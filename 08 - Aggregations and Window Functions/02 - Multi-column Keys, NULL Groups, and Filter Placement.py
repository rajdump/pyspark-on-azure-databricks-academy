# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC
# MAGIC # 02 - Multi-column Keys, NULL Groups, and Filter Placement
# MAGIC
# MAGIC Notebook 01 always grouped on a single column with no NULLs. Real summaries
# MAGIC rarely stay that clean. This notebook covers the two concepts that break
# MAGIC most real-world aggregations:
# MAGIC
# MAGIC ### Part 1: Grouping on several columns — and NULL as a group key
# MAGIC
# MAGIC Notebook 01's exercise left you with a group nobody asked for: a
# MAGIC `payment_method` row whose key is `NULL`. In the output it looks exactly
# MAGIC like a valid data row. Section 1 explains where it comes from, what it does
# MAGIC to your row-count prediction, and how it behaves once you group on more
# MAGIC than one column.
# MAGIC
# MAGIC ### Part 2: `WHERE` vs `HAVING`
# MAGIC
# MAGIC Filtering *before* the aggregate and filtering *after* are different SQL
# MAGIC clauses (`WHERE` / `HAVING`). In the DataFrame API they are both called
# MAGIC `.filter()` — only line order distinguishes them. Putting `.filter()` on the
# MAGIC wrong side silently changes every number in your result.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## What this notebook teaches
# MAGIC
# MAGIC | Section | Concept | Why it matters |
# MAGIC |---|---|---|
# MAGIC | 1. Multi-column keys | Composite grain & NULLs | Grain is defined by the full key list |
# MAGIC | 2. Filter placement | `WHERE` vs `HAVING` | Filter early without breaking group logic |
# MAGIC | Exercise | Per-borough summary | Composite grain + HAVING on a new key |
# MAGIC
# MAGIC **Reads:** `rideshare_dev.processed.trip_enriched` (106 rows). **No writes.**
# MAGIC
# MAGIC **Prerequisites:** Notebook 01 (`groupBy`, aliasing, NULL skipping);
# MAGIC Module 7 (join NULL semantics).

# COMMAND ----------

# DBTITLE 1,Setup
# MAGIC %md
# MAGIC ## Setup — load `trip_enriched`
# MAGIC
# MAGIC The same managed table Notebook 01 used: one row per `trip_id`, **106**
# MAGIC rows, 16 columns. Column roles, types, and the inherited-NULL map are in
# MAGIC Notebook 01's setup and in `docs/data/dataset-overview.md`.
# MAGIC
# MAGIC This notebook groups on `service_type`, `payment_method`, and
# MAGIC `pickup_borough`, and aggregates `base_fare_amount`, `tip_amount`, and
# MAGIC `trip_distance_miles`.

# COMMAND ----------

from pyspark.sql import functions as F

trip_enriched_table = "rideshare_dev.processed.trip_enriched"

trip_enriched = spark.table(trip_enriched_table)  # noqa: F821

print("trip_enriched rows:", trip_enriched.count())

# COMMAND ----------

# DBTITLE 1,Section 1 - Multi-column grouping
# MAGIC %md
# MAGIC ## 1. Grouping on several columns — and NULL as a group key
# MAGIC
# MAGIC Pass more than one column and the **output grain becomes the whole key
# MAGIC list**: one row per *combination* that actually occurs.
# MAGIC
# MAGIC | Group key | Output grain |
# MAGIC |---|---|
# MAGIC | `service_type` | One row per service type (5) |
# MAGIC | `service_type`, `payment_method` | One row per service type **and** method |
# MAGIC
# MAGIC Adding a key can only **add** rows, never remove them — you are subdividing
# MAGIC existing groups. Predicting the count is now a range, not a number:
# MAGIC
# MAGIC ```
# MAGIC at most  groups(key1) * groups(key2)              = 5 * 6 = 30
# MAGIC actual   only combinations present in the data    = 18
# MAGIC ```
# MAGIC
# MAGIC Read `groups(key)` as the number of groups a `groupBy` on that key alone
# MAGIC would produce — **not** `countDistinct`. `payment_method` contributes **6**
# MAGIC here, not 5. The subsection below explains the gap.
# MAGIC
# MAGIC The 12 missing combinations are information in themselves: no `XL` trip was
# MAGIC ever paid in cash, for instance. A `groupBy` reports what exists, not every
# MAGIC combination that could.
# MAGIC
# MAGIC ### The NULL group-key rule
# MAGIC
# MAGIC Three operations, three different answers on the same NULL key:
# MAGIC
# MAGIC | Operation | NULL keys |
# MAGIC |---|---|
# MAGIC | `join` (Module 7) | Never match — `NULL = NULL` is not true; need `eqNullSafe` |
# MAGIC | `groupBy` | Collapse into a single group, displayed as `NULL` |
# MAGIC | `countDistinct` | Ignored entirely |
# MAGIC
# MAGIC The middle row is the one that catches people: `groupBy` treats every NULL
# MAGIC as the same key, which is why `payment_method` yields **6** groups where
# MAGIC `countDistinct` reports **5**.
# MAGIC
# MAGIC Watch for `unknown` **and** NULL appearing as separate rows below. The
# MAGIC `unknown` sentinel from Notebook 01 covers a blank method on trip 105; the
# MAGIC NULL is trip 106, which has no payment row at all. Two different data
# MAGIC problems that a careless summary would merge.
# MAGIC
# MAGIC Notebook `04` shows how this NULL group becomes genuinely ambiguous once
# MAGIC `rollup` starts adding subtotal rows that *also* show NULL.

# COMMAND ----------

# The 5-vs-6 gap, proven
trip_enriched.select(
    F.countDistinct("service_type").alias("distinct_service_type"),
    F.countDistinct("payment_method").alias("distinct_payment_method"),
).show()

print("groupBy(payment_method) groups:", trip_enriched.groupBy("payment_method").count().count())

# COMMAND ----------

trip_enriched.groupBy("payment_method").agg(
    F.count("*").alias("trip_count"),
).orderBy(F.col("trip_count").desc()).show()

# Expected 6 rows: card 59, wallet 20, cash 17, corporate 8, unknown 1, NULL 1

# COMMAND ----------

method_by_service = trip_enriched.groupBy("service_type", "payment_method").agg(
    F.count("*").alias("trip_count"),
    F.round(F.sum("base_fare_amount"), 2).alias("total_base_fare"),
)

print("output rows:", method_by_service.count(), "(at most 5 groups * 6 groups = 30)")
method_by_service.orderBy("service_type", "payment_method").show(30)
# Expected: 18 rows (not all 30 possible service_type × payment_method combinations exist)

# COMMAND ----------

# DBTITLE 1,Section 2 - Filter placement
# MAGIC %md
# MAGIC ## 2. Filtering before vs after aggregating
# MAGIC
# MAGIC The same `filter` call means completely different things depending on which
# MAGIC side of `.agg()` it sits on. In SQL these have separate keywords, which is
# MAGIC why the distinction is easy to miss in the DataFrame API — here it is just
# MAGIC line order.
# MAGIC
# MAGIC | Placement | SQL | What it does |
# MAGIC |---|---|---|
# MAGIC | `filter` **before** `groupBy` | `WHERE` | Drops input rows; **aggregate values change** |
# MAGIC | `filter` **after** `agg` | `HAVING` | Drops whole groups; **values stay identical** |
# MAGIC
# MAGIC There is no `.having()` method — a `HAVING` is just a `filter` further down
# MAGIC the chain, applied to the **alias** you created in `.agg()`. That is reason
# MAGIC number two for Notebook 01's aliasing rule.
# MAGIC
# MAGIC Watch all three results below on the same per-borough tip totals:
# MAGIC
# MAGIC | Query | Groups | Manhattan total |
# MAGIC |---|---|---|
# MAGIC | No filter | 5 | 134.45 |
# MAGIC | `WHERE tip_amount > 5` first | 4 | **91.00** — value changed |
# MAGIC | `HAVING total_tip > 90` after | 2 | **134.45** — value preserved |
# MAGIC
# MAGIC `WHERE` did two things at once: it shrank every total *and* eliminated
# MAGIC Staten Island entirely, because its single trip tipped 2.41 and no rows
# MAGIC survived to form a group. `HAVING` dropped three groups but changed no
# MAGIC number. Neither is more correct — but "boroughs whose total tips exceed 90"
# MAGIC and "total of tips over 5, by borough" are different reports.
# MAGIC
# MAGIC **Habit:** filter as early as the question allows. Fewer rows enter the
# MAGIC shuffle, which is the cheapest performance win in Spark (Module 4).

# COMMAND ----------

borough_tips = trip_enriched.groupBy("pickup_borough").agg(
    F.count("*").alias("trip_count"),
    F.sum("tip_amount").alias("total_tip"),
)

print("No filter — 5 groups, all 106 trips:")
borough_tips.orderBy(F.col("total_tip").desc()).show()

# COMMAND ----------

# WHERE — filter runs first, so only generous tips reach the aggregate
print("WHERE tip_amount > 5 (applied before groupBy):")
(
    trip_enriched.filter(F.col("tip_amount") > 5)
    .groupBy("pickup_borough")
    .agg(
        F.count("*").alias("trip_count"),
        F.sum("tip_amount").alias("total_tip"),
    )
    .orderBy(F.col("total_tip").desc())
    .show()
)

# COMMAND ----------

# HAVING — filter runs after, on the alias, so totals match the unfiltered run
print("HAVING total_tip > 90 (applied after agg):")
borough_tips.filter(F.col("total_tip") > 90).orderBy(F.col("total_tip").desc()).show()

# COMMAND ----------

# DBTITLE 1,Exercise
# MAGIC %md
# MAGIC ## Exercise — a per-borough trip summary
# MAGIC
# MAGIC Steps 1–3 apply Section 2's filter placement to the single key
# MAGIC **`pickup_borough`**. Step 4 then adds Section 1's composite key.
# MAGIC
# MAGIC **1. Predict.** Set `predicted_borough_groups` to the number of output rows
# MAGIC you expect. Get it from `countDistinct("pickup_borough")` — the zone
# MAGIC columns carry **no** NULLs, so unlike `payment_method` there is no extra
# MAGIC NULL group to add here.
# MAGIC
# MAGIC **2. Aggregate.** One row per `pickup_borough`, with these aliased columns:
# MAGIC
# MAGIC | Alias | Aggregate |
# MAGIC |---|---|
# MAGIC | `trip_count` | All trips in the borough |
# MAGIC | `dated_trip_count` | Trips with a non-NULL `trip_date` |
# MAGIC | `total_base_fare` | Sum of `base_fare_amount`, rounded to 2 |
# MAGIC | `avg_distance_miles` | Average `trip_distance_miles`, rounded to 2 |
# MAGIC
# MAGIC **3. Apply a `HAVING`.** Keep only boroughs with **more than 10** trips,
# MAGIC then answer this: *why is `total_base_fare` for Manhattan identical before
# MAGIC and after that filter?*
# MAGIC
# MAGIC Expected results to check yourself against:
# MAGIC
# MAGIC | pickup_borough | trip_count | dated_trip_count | total_base_fare | avg_distance_miles |
# MAGIC |---|---|---|---|---|
# MAGIC | Manhattan | 44 | 41 | 1389.04 | 7.60 |
# MAGIC | Brooklyn | 29 | 27 | 927.91 | 8.01 |
# MAGIC | Queens | 22 | 21 | 632.40 | 7.89 |
# MAGIC | Bronx | 10 | 10 | 341.54 | 8.61 |
# MAGIC | Staten Island | 1 | 1 | 16.94 | 6.10 |
# MAGIC
# MAGIC `avg_distance_miles` divides by non-NULL distances only, so the three trips
# MAGIC with a rejected distance (103, 105, 106) are excluded from their borough's
# MAGIC average — Notebook 01's denominator lesson, applied.
# MAGIC
# MAGIC The `HAVING` should leave **3** rows — Bronx has exactly 10 trips, and
# MAGIC `> 10` excludes it. Off-by-one traps are real; check the boundary.
# MAGIC
# MAGIC **4. Now the composite key.** Group on **`pickup_borough` *and*
# MAGIC `payment_method`** with a single `trip_count`, and predict the row count
# MAGIC *before* you run it.
# MAGIC
# MAGIC Two rules from Section 1 decide your answer: the upper bound is
# MAGIC `groups(pickup_borough) * groups(payment_method)`, and `payment_method`
# MAGIC contributes **6**, not 5. Expect the actual number to land well below that
# MAGIC bound — no borough saw every payment method. If the check prints `✗`, work
# MAGIC out which of the two rules you missed before looking at the result.

# COMMAND ----------

# 1. YOUR PREDICTION — replace None with the row count you expect
predicted_borough_groups = None

# 2. YOUR CODE — build the per-borough summary described above
borough_summary = trip_enriched.groupBy("pickup_borough").agg(
    F.count("*").alias("trip_count"),
    # TODO: dated_trip_count, total_base_fare, avg_distance_miles
)

actual = borough_summary.count()
match = "✓" if predicted_borough_groups == actual else "✗"
print(f"{match} predicted={predicted_borough_groups}, actual={actual}")

borough_summary.orderBy(F.col("trip_count").desc()).show()

# COMMAND ----------

# 3. YOUR CODE — keep only boroughs with more than 10 trips (HAVING)
# Then compare Manhattan's total_base_fare against the unfiltered run above.

# COMMAND ----------

# 4. YOUR PREDICTION — replace None with the row count you expect
predicted_pair_groups = None

# 4. YOUR CODE — add the second key so the grain is one row per
# (pickup_borough, payment_method)
borough_method = trip_enriched.groupBy("pickup_borough").agg(  # TODO: add payment_method
    F.count("*").alias("trip_count"),
)

actual_pairs = borough_method.count()
pair_match = "✓" if predicted_pair_groups == actual_pairs else "✗"
print(f"{pair_match} predicted={predicted_pair_groups}, actual={actual_pairs}")

borough_method.orderBy(F.col("trip_count").desc()).show(40)

# COMMAND ----------

# DBTITLE 1,Summary
# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC | Concept | Key takeaway |
# MAGIC |---|---|
# MAGIC | **Composite keys** | Grain is the whole key list; ≤ product of per-key group counts |
# MAGIC | **NULL group key** | One NULL group in output; ignored by `countDistinct`; never matches |
# MAGIC | **`unknown` ≠ NULL** | String sentinel and missing row are separate groups — don't merge |
# MAGIC | **Filter placement** | `WHERE` changes aggregate values; `HAVING` only drops groups |
# MAGIC | **Aliasing for HAVING** | `HAVING` filters on the alias — another reason to always alias |
# MAGIC | **Filter early** | Push `WHERE` as far left as possible; fewer rows = cheaper shuffle |
# MAGIC
# MAGIC **The two habits from this notebook:** (1) when grouping on a nullable
# MAGIC column, add 1 to your `countDistinct` estimate for the NULL group; (2)
# MAGIC ask "does this filter change what's *in* the groups or *which* groups
# MAGIC survive?" — that tells you whether it is a `WHERE` or a `HAVING`.
# MAGIC
# MAGIC **Next:** **`03 - Aggregate Functions Beyond Count and Sum`** — where `avg`
# MAGIC misleads and `F.median` / `F.percentile_approx` don't, collecting group
# MAGIC values into arrays with `F.collect_set`, exact versus approximate distinct
# MAGIC counts, and what `decimal` precision does under `sum` and `avg`.
