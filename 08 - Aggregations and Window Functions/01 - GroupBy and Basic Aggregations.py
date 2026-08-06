# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC
# MAGIC # 01 - GroupBy and Basic Aggregations
# MAGIC
# MAGIC ## The problem: an aggregate answers a question you didn't ask
# MAGIC
# MAGIC Your manager asks for the **average tip per trip**. You write one line:
# MAGIC
# MAGIC ```python
# MAGIC trip_enriched.agg(F.avg("tip_amount")).show()
# MAGIC ```
# MAGIC
# MAGIC It prints **2.955673**. The table has **106** trips and the tips total
# MAGIC **307.39**, so anyone checking your work by hand gets
# MAGIC `307.39 / 106` = **2.8999**. Two different "average tips", neither flagged
# MAGIC by an error.
# MAGIC
# MAGIC Spark divided by **104**, not 106, because two trips have a NULL
# MAGIC `tip_amount` and `F.avg` **skips** them. Spark answered "average of the tips
# MAGIC we know about" while you asked "average tip per trip". Both are defensible
# MAGIC numbers — but only one is the one you were asked for, and nothing in the
# MAGIC code says which you meant.
# MAGIC
# MAGIC That is the theme of this notebook. Aggregating is easy to write and easy to
# MAGIC get subtly wrong, because a wrong aggregate is still a number.
# MAGIC
# MAGIC **The second idea:** `groupBy` **changes the grain**. Module 7 taught you to
# MAGIC protect the grain through a join; this is the first time you deliberately
# MAGIC collapse it. One row per trip goes in, one row per *group* comes out — so
# MAGIC say what a group is before you write the aggregate.
# MAGIC
# MAGIC ## What this notebook teaches
# MAGIC
# MAGIC | Section | Concept | Why it matters |
# MAGIC |---|---|---|
# MAGIC | 1. Output grain | One row per group | Predict a summary's row count |
# MAGIC | 2. `groupBy().agg()` | Syntax and aliasing | Named, usable summary columns |
# MAGIC | 3. Counting | 3 counts, 3 answers | Know which question you asked |
# MAGIC | 4. NULL skipping | `sum` / `avg` ignore NULLs | Control your denominator |
# MAGIC | 5. Multi-column keys | Composite grain; NULL groups | Grain is the whole key list |
# MAGIC | 6. Filter placement | `WHERE` vs `HAVING` | One line moved, different numbers |
# MAGIC | Exercise | Per-borough summary | Repeat it on a new key |
# MAGIC
# MAGIC **Core habit:** name the output grain → predict the row count → run →
# MAGIC verify with `count()`.
# MAGIC
# MAGIC **Reads:** `rideshare_dev.processed.trip_enriched` (106 rows). **No writes.**
# MAGIC
# MAGIC **Prerequisites:** Module 7 notebooks 01–07, so `trip_enriched` exists;
# MAGIC Module 3 NULL semantics and `F.coalesce`; Module 4 wide/shuffle stages.

# COMMAND ----------

# DBTITLE 1,Setup
# MAGIC %md
# MAGIC ## Setup — load `trip_enriched`
# MAGIC
# MAGIC Module 7 Notebook **`07`** wrote this managed table: one row per `trip_id`,
# MAGIC **106** rows, 16 columns.
# MAGIC
# MAGIC | Role | Columns |
# MAGIC |---|---|
# MAGIC | Key | `trip_id` |
# MAGIC | Join keys (retained) | `pickup_location_id`, `dropoff_location_id` |
# MAGIC | Group keys | `service_type`, `payment_method`, `trip_date`, `hour_of_day` |
# MAGIC | Group keys (zone) | `pickup_borough`, `pickup_zone`, `dropoff_borough`, `dropoff_zone` |
# MAGIC | Measures | `trip_distance_miles`, `ride_duration_mins` |
# MAGIC | Measures (money) | `base_fare_amount`, `tip_amount`, `driver_payout_amount` |
# MAGIC
# MAGIC Money and distance columns are `decimal`; `ride_duration_mins` and
# MAGIC `hour_of_day` are `int`; `trip_date` is a `date`.

# COMMAND ----------

from pyspark.sql import functions as F

trip_enriched_table = "rideshare_dev.processed.trip_enriched"

trip_enriched = spark.table(trip_enriched_table)  # noqa: F821

print("trip_enriched rows:", trip_enriched.count())
trip_enriched.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ### The NULLs you inherited — read this before Section 3
# MAGIC
# MAGIC Every number in this notebook depends on knowing where the NULLs are. They
# MAGIC come from two places, both deliberate:
# MAGIC
# MAGIC | Column(s) | NULL on `trip_id` | Rows | Cause |
# MAGIC |---|---|---|---|
# MAGIC | `trip_date`, `hour_of_day` | 101–106 | 6 | `trip_time` had 100 rows (Module 7 left join) |
# MAGIC | `payment_method`, `driver_payout_amount` | 106 | 1 | `payment` had 105 rows (left join) |
# MAGIC | `base_fare_amount` | 104, 106 | 2 | Left join; Module 6: trip 104 (negative fare) |
# MAGIC | `tip_amount` | 103, 106 | 2 | Left join; Module 6 rejected trip 103's `not_a_number` tip |
# MAGIC | `trip_distance_miles` | 103, 105, 106 | 3 | Module 6: `-1.00`, `not_a_number`, blank |
# MAGIC
# MAGIC `ride_duration_mins`, `service_type`, and the four zone columns have **no**
# MAGIC NULLs. So there is no single "non-NULL row count" for this table — **each
# MAGIC column has its own**, which is exactly why Section 3 exists.
# MAGIC
# MAGIC The next cell proves the table above rather than asking you to trust it.

# COMMAND ----------

trip_enriched.select(
    F.count("*").alias("rows"),
    F.count("trip_date").alias("trip_date"),
    F.count("payment_method").alias("payment_method"),
    F.count("base_fare_amount").alias("base_fare"),
    F.count("tip_amount").alias("tip"),
    F.count("trip_distance_miles").alias("distance"),
    F.count("ride_duration_mins").alias("duration"),
).show()

# Expected: rows=106, trip_date=100, payment_method=105, base_fare=104,
# tip=104, distance=103, duration=106

# COMMAND ----------

# DBTITLE 1,Section 1 - Output grain
# MAGIC %md
# MAGIC ## 1. Output grain — one row per group
# MAGIC
# MAGIC **Output grain** = what one row of your *result* represents.
# MAGIC
# MAGIC Module 7 drilled *input* grain: one row per `trip_id`. A `groupBy` replaces
# MAGIC it with a new one:
# MAGIC
# MAGIC | | Grain | Rows |
# MAGIC |---|---|---|
# MAGIC | Input `trip_enriched` | One completed trip | 106 |
# MAGIC | `groupBy("service_type")` | One service type | ? |
# MAGIC
# MAGIC You can fill in that `?` **before running the aggregate**, because the output
# MAGIC row count of a `groupBy` is just the number of distinct group-key values:
# MAGIC
# MAGIC ```
# MAGIC output rows == countDistinct(group key)
# MAGIC ```
# MAGIC
# MAGIC That is your prediction step, and it costs one cheap query. If the real
# MAGIC result has a different row count, stop — your mental model of the data is
# MAGIC wrong, and every number built on top of it will be too.
# MAGIC
# MAGIC One caveat that Section 5 returns to: `countDistinct` **ignores NULLs** but
# MAGIC `groupBy` **keeps them as a group**. `service_type` has no NULLs, so the two
# MAGIC agree here.
# MAGIC
# MAGIC **Performance note:** `groupBy` is a **wide** transformation — the `Exchange`
# MAGIC (shuffle) from Module 4. Rows for the same key must meet on one executor.
# MAGIC Tuning that shuffle is Module 16.

# COMMAND ----------

predicted_groups = trip_enriched.select(
    F.countDistinct("service_type").alias("distinct_service_type"),
).collect()[0]["distinct_service_type"]

actual_groups = trip_enriched.groupBy("service_type").count().count()

print(f"predicted output rows = {predicted_groups}")
print(f"actual output rows    = {actual_groups}")
print("match:", predicted_groups == actual_groups)

# COMMAND ----------

# MAGIC %md
# MAGIC Five groups, and the per-group counts sum back to 106 — a `groupBy` on a
# MAGIC column with no NULLs never loses or invents rows, it only redistributes
# MAGIC them. `UNKNOWN` is Module 6's normalized sentinel for a blank or `n/a`
# MAGIC service type; it is a real string, **not** a NULL.

# COMMAND ----------

# Note the uppercase values: Module 6 normalized service_type with F.upper
trip_enriched.groupBy("service_type").count().orderBy(F.col("count").desc()).show()

# Expected: STANDARD 55, SHARED 21, PREMIUM 16, XL 12, UNKNOWN 2  (sum = 106)

# COMMAND ----------

# DBTITLE 1,Section 2 - groupBy and agg
# MAGIC %md
# MAGIC ## 2. `groupBy().agg()` and why aliasing is not optional
# MAGIC
# MAGIC `.count()` is a shorthand for one specific aggregate. The general form takes
# MAGIC any number of aggregates in a single pass:
# MAGIC
# MAGIC ```python
# MAGIC trip_enriched.groupBy("service_type").agg(
# MAGIC     F.count("*").alias("trip_count"),
# MAGIC     F.sum("tip_amount").alias("total_tip"),
# MAGIC )
# MAGIC ```
# MAGIC
# MAGIC Two rules worth internalizing now:
# MAGIC
# MAGIC **1. Alias every aggregate.** Without `.alias(...)`, Spark names the column
# MAGIC after the expression — `count(1)`, `sum(tip_amount)`, `avg(CAST(...))`. Those
# MAGIC are legal but painful to reference: the parentheses have to be escaped with
# MAGIC backticks, as in ``F.col("`sum(tip_amount)`")``, or Spark reads the name as a
# MAGIC function call. Section 6 has to *filter* on an aggregate by name, so an alias
# MAGIC is not cosmetic.
# MAGIC
# MAGIC **2. Output columns are group keys and aggregates — nothing else.** Referring
# MAGIC to a bare `trip_id` in the result is an error, because 55 `STANDARD` trips
# MAGIC have 55 different `trip_id` values and Spark will not pick one for you. If
# MAGIC you genuinely want a per-row column *and* a group summary side by side, you
# MAGIC want a **window function** — Notebook `04`.
# MAGIC
# MAGIC The first cell shows the unaliased mess, the second the readable version.

# COMMAND ----------

# Aggregates without alias — legal, but look at the column names
trip_enriched.groupBy("service_type").agg(
    F.count("*"),
    F.sum("tip_amount"),
    F.avg("trip_distance_miles"),
).show(truncate=False)

# COMMAND ----------

service_summary = trip_enriched.groupBy("service_type").agg(
    F.count("*").alias("trip_count"),
    F.sum("tip_amount").alias("total_tip"),
    F.round(F.avg("trip_distance_miles"), 2).alias("avg_distance_miles"),
    F.min("ride_duration_mins").alias("shortest_ride_mins"),
    F.max("ride_duration_mins").alias("longest_ride_mins"),
)

service_summary.orderBy(F.col("trip_count").desc()).show()

# COMMAND ----------

# DBTITLE 1,Section 3 - Counting correctly
# MAGIC %md
# MAGIC ## 3. Counting correctly — three counts, three answers
# MAGIC
# MAGIC "How many?" is the most common question asked of a dataset and the easiest
# MAGIC one to answer wrongly. Three expressions look interchangeable and are not:
# MAGIC
# MAGIC | Expression | Question it answers | On `trip_date` |
# MAGIC |---|---|---|
# MAGIC | `F.count("*")` | How many **rows**? | **106** |
# MAGIC | `F.count("trip_date")` | How many rows **have a value**? | **100** |
# MAGIC | `F.countDistinct("trip_date")` | How many **different values**? | **14** |
# MAGIC
# MAGIC Read those as three different business questions: *how many trips did we
# MAGIC run*, *how many trips do we know the date of*, and *how many days does this
# MAGIC data cover*. All three are reasonable; only one is what you were asked.
# MAGIC
# MAGIC - `106 - 100 = 6` **is** the six undated trips (101–106) from the setup table.
# MAGIC - **14** is small because 100 trips are spread over just 14 calendar dates.
# MAGIC
# MAGIC **Gotcha — say what you mean.** `F.count("*")`, `F.count(F.lit(1))`, and
# MAGIC `F.count(F.col("*"))` all count rows. They are equivalent, but a reader
# MAGIC cannot tell whether you *meant* "all rows" or fat-fingered a column name.
# MAGIC Prefer `F.count("*")` with an alias that states the intent. (Module 7
# MAGIC used `F.count(F.lit(1))` for the same purpose — either form is fine, but
# MAGIC pick one and stay consistent within a notebook.)
# MAGIC
# MAGIC **Cost warning.** `F.countDistinct` must deduplicate across the whole
# MAGIC cluster, which is far more expensive than counting. On 106 rows you will
# MAGIC never notice; on a billion you will. Notebook `02` covers
# MAGIC `F.approx_count_distinct` for when an estimate is good enough.

# COMMAND ----------

trip_enriched.select(
    F.count("*").alias("all_trips"),
    F.count("trip_date").alias("trips_with_a_date"),
    F.countDistinct("trip_date").alias("distinct_dates"),
    # Same 106 as all_trips — proof that these row-counting forms are equivalent
    F.count(F.lit(1)).alias("count_lit_1"),
    F.count(F.col("*")).alias("count_col_star"),
).show()

# COMMAND ----------

# MAGIC %md
# MAGIC Now the same three counts **per group**, which is where this gets practical.
# MAGIC The six undated trips do not sit in one tidy place — they scatter across
# MAGIC three service types:
# MAGIC
# MAGIC | `service_type` | `trip_count` | `dated_trip_count` | Gap | `distinct_dates` |
# MAGIC |---|---|---|---|---|
# MAGIC | STANDARD | 55 | 52 | 3 | 14 |
# MAGIC | SHARED | 21 | 21 | 0 | 13 |
# MAGIC | PREMIUM | 16 | 15 | 1 | 9 |
# MAGIC | XL | 12 | 12 | 0 | 8 |
# MAGIC | UNKNOWN | 2 | **0** | 2 | **0** |
# MAGIC
# MAGIC This is how a NULL problem hides in a summary. `SHARED` and `XL` are
# MAGIC perfectly clean, `STANDARD` is short by 3, and every row still *looks*
# MAGIC plausible. Only by putting `count("*")` and `count(col)` side by side does
# MAGIC the gap become visible at all — a report showing just one of them would
# MAGIC never reveal it.
# MAGIC
# MAGIC `UNKNOWN` is the extreme case: 2 trips, **0** of them dated. Both a count of
# MAGIC non-NULL values and a distinct count of an all-NULL group are `0`.

# COMMAND ----------

trip_enriched.groupBy("service_type").agg(
    F.count("*").alias("trip_count"),
    F.count("trip_date").alias("dated_trip_count"),
    F.countDistinct("trip_date").alias("distinct_dates"),
).orderBy(F.col("trip_count").desc()).show()

# COMMAND ----------

# DBTITLE 1,Section 4 - NULL skipping
# MAGIC %md
# MAGIC ## 4. `sum` / `avg` / `min` / `max` skip NULLs
# MAGIC
# MAGIC Module 3 taught that NULL **propagates** through arithmetic: if `tip_amount`
# MAGIC is NULL then `base_fare_amount + tip_amount` is NULL. Aggregates do the
# MAGIC **opposite** — they quietly **skip** NULL inputs:
# MAGIC
# MAGIC | Context | NULL behavior |
# MAGIC |---|---|
# MAGIC | Row arithmetic (`a + b`) | NULL **propagates** — result is NULL |
# MAGIC | Aggregate (`F.sum`, `F.avg`) | NULL is **skipped** — result ignores it |
# MAGIC
# MAGIC This is the notebook's opening puzzle. `tip_amount` is NULL on 2 of 106
# MAGIC trips, so:
# MAGIC
# MAGIC | Expression | Divides by | Result | Means |
# MAGIC |---|---|---|---|
# MAGIC | `F.avg("tip_amount")` | 104 | ≈ **2.955673** | Average of *known* tips |
# MAGIC | `F.sum(...) / F.count("*")` | 106 | ≈ **2.899906** | Average tip *per trip* |
# MAGIC
# MAGIC Neither is a bug. `F.avg` is `sum / count(col)`, never `sum / count(all rows)`.
# MAGIC The question is which denominator your stakeholder meant, and the code
# MAGIC should make that obvious.
# MAGIC
# MAGIC **Deciding:** if a missing tip means *we don't know*, `F.avg` is right. If it
# MAGIC means *no tip was given* — worth 0.00 — then `F.coalesce(col, F.lit(0))`
# MAGIC before aggregating is right (Module 3). Choose deliberately; don't inherit
# MAGIC the default.
# MAGIC
# MAGIC `F.min` / `F.max` skip NULLs too, so a max is the largest *known* value.
# MAGIC
# MAGIC And one edge worth seeing directly: when **every** value in a group is NULL,
# MAGIC `F.sum` and `F.max` return **NULL**, not `0`. A "total" column that is NULL
# MAGIC rather than zero breaks downstream arithmetic in exactly the way Module 3
# MAGIC warned about.
# MAGIC
# MAGIC Two real examples follow. First at `trip_id` grain, where trips **103** and
# MAGIC **106** each form a single-row group with no known tip, and trip **105** is
# MAGIC the control with a real tip of `2.50`. Then a genuine multi-row case: both
# MAGIC `UNKNOWN` service-type trips are undated, so that group's
# MAGIC `latest_trip_date` is NULL even though the group has 2 rows.

# COMMAND ----------

trip_enriched.select(
    F.count("*").alias("all_trips"),
    F.count("tip_amount").alias("trips_with_tip"),
    F.sum("tip_amount").alias("total_tip"),
    F.avg("tip_amount").alias("avg_skips_nulls"),
    # Round to 6 d.p. to match F.avg's decimal(14,6) output — raw division
    # widens to decimal(38,20) and prints 20 digits without the round.
    F.round(F.sum("tip_amount") / F.count("*"), 6).alias("avg_per_trip"),
).show(truncate=False)

# COMMAND ----------

# Trips 103 and 106 have no known tip, so their totals are NULL — not 0
trip_enriched.filter(F.col("trip_id").isin(103, 105, 106)).groupBy("trip_id").agg(
    F.count("*").alias("rows"),
    F.count("tip_amount").alias("known_tips"),
    F.sum("tip_amount").alias("total_tip"),
    F.max("tip_amount").alias("max_tip"),
    F.coalesce(F.sum("tip_amount"), F.lit(0)).alias("total_or_zero"),
).orderBy("trip_id").show()

# COMMAND ----------

# A multi-row all-NULL group: both UNKNOWN trips are undated, so max is NULL
trip_enriched.groupBy("service_type").agg(
    F.count("*").alias("trip_count"),
    F.count("trip_date").alias("dated_trips"),
    F.max("trip_date").alias("latest_trip_date"),
).orderBy("service_type").show()

# COMMAND ----------

# MAGIC %md
# MAGIC Same question, treating a missing tip as 0.00. `F.coalesce` runs **before**
# MAGIC the aggregate, so the NULLs become real zeros and are no longer skipped —
# MAGIC `avg_with_zeros` now matches `avg_per_trip` above. Note that the **total is
# MAGIC unchanged**: adding zeros cannot move a sum, only the count it is divided by.

# COMMAND ----------

tip_or_zero = F.coalesce(F.col("tip_amount"), F.lit(0).cast("decimal(10,2)"))

trip_enriched.select(
    F.sum(tip_or_zero).alias("total_tip_unchanged"),
    F.count(tip_or_zero).alias("now_counts_all_106"),
    F.avg(tip_or_zero).alias("avg_with_zeros"),
).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC **A note on types, since the output looks odd.** `tip_amount` is
# MAGIC `decimal(10,2)`. Spark widens decimal types when aggregating:
# MAGIC `F.avg` → `decimal(14,6)` (six decimals); `F.sum` → `decimal(20,2)` (keeps
# MAGIC two); raw division (`sum / count`) → `decimal(38,20)` (twenty decimals —
# MAGIC that is why `avg_per_trip` is wrapped in `F.round(..., 6)` above).
# MAGIC Wrap any aggregate in `F.round(..., 2)` when the output is going into a
# MAGIC report. Notebook `02` looks at decimal growth properly.

# COMMAND ----------

# DBTITLE 1,Section 5 - Multi-column grouping
# MAGIC %md
# MAGIC ## 5. Grouping on several columns — and NULL as a group key
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
# MAGIC here (5 values plus a NULL group) even though `countDistinct` reports 5.
# MAGIC The subsection below explains why those two numbers differ.
# MAGIC
# MAGIC The 12 missing combinations are information in themselves: no `XL` trip was
# MAGIC ever paid in cash, for instance. A `groupBy` reports what exists, not every
# MAGIC combination that could.
# MAGIC
# MAGIC ### The NULL group-key rule
# MAGIC
# MAGIC Module 7 hammered that `NULL = NULL` is **not true**, so NULL keys never
# MAGIC match in a join. `groupBy` works the other way: **all NULLs collapse into
# MAGIC one group**, displayed as `NULL`.
# MAGIC
# MAGIC | Operation | NULL keys |
# MAGIC |---|---|
# MAGIC | `join` (Module 7) | Never match — need `eqNullSafe` |
# MAGIC | `groupBy` | Collapse into a single NULL group |
# MAGIC | `countDistinct` | Ignored entirely |
# MAGIC
# MAGIC So `payment_method` produces **6** groups (5 real values + NULL) while
# MAGIC `countDistinct` reports **5**. Watch for `unknown` **and** NULL appearing as
# MAGIC separate rows below: `unknown` is Module 6's sentinel for a blank method on
# MAGIC trip 105, whereas the NULL is trip 106, which has no payment row at all.
# MAGIC Two different data problems that a careless summary would merge.
# MAGIC
# MAGIC Notebook `03` shows how this NULL group becomes genuinely ambiguous once
# MAGIC `rollup` starts adding subtotal rows that *also* show NULL.

# COMMAND ----------

# countDistinct ignores NULL; groupBy does not — hence 5 vs 6
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

# DBTITLE 1,Section 6 - Filter placement
# MAGIC %md
# MAGIC ## 6. Filtering before vs after aggregating
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
# MAGIC number two for Section 2's aliasing rule.
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
# MAGIC Sections 1–6 grouped mostly on `service_type`. Build the same shape of
# MAGIC summary on **`pickup_borough`**, using every habit from this notebook.
# MAGIC
# MAGIC **1. Predict.** Set `predicted_borough_groups` to the number of output rows
# MAGIC you expect. Get it from `countDistinct("pickup_borough")` — and remember
# MAGIC from the setup table that the zone columns have **no** NULLs, so there is no
# MAGIC extra NULL group here.
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
# MAGIC average — Section 4's denominator lesson, applied.
# MAGIC
# MAGIC The `HAVING` should leave **3** rows — Bronx has exactly 10 trips, and
# MAGIC `> 10` excludes it. Off-by-one traps are real; check the boundary.

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

# DBTITLE 1,Summary
# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC | Concept | Key takeaway |
# MAGIC |---|---|
# MAGIC | **Output grain** | One row per group; `countDistinct` predicts it when key has no NULLs |
# MAGIC | **Aliasing** | Alias every aggregate — `HAVING` filters need the name |
# MAGIC | **Only keys and aggregates** | Want a per-row column too? That's a window (`04`) |
# MAGIC | **Three counts** | `count("*")`=106, `count("trip_date")`=100, `countDistinct`=14 |
# MAGIC | **NULL skipping** | `avg` divides by non-NULL count (104), not by rows (106) |
# MAGIC | **`F.coalesce` first** | Use it when missing means 0, not *unknown* |
# MAGIC | **Composite keys** | Grain is the whole key list; ≤ product of per-key group counts |
# MAGIC | **NULL group key** | One NULL group; ignored by `countDistinct`; never matches in a join |
# MAGIC | **Filter placement** | `WHERE` changes aggregate values; `HAVING` only drops groups |
# MAGIC
# MAGIC **The habit that prevents most aggregation bugs:** say the output grain out
# MAGIC loud, predict the row count, then verify. A wrong join at least gives you a
# MAGIC suspicious row count to notice — a wrong aggregate just gives you a number
# MAGIC that looks fine.
# MAGIC
# MAGIC **Next:** **`02 - Aggregate Functions Beyond Count and Sum`** — where `avg`
# MAGIC misleads and `F.median` / `F.percentile_approx` don't, collecting group
# MAGIC values into arrays with `F.collect_set`, exact versus approximate distinct
# MAGIC counts, and what `decimal` precision does under `sum` and `avg`.
