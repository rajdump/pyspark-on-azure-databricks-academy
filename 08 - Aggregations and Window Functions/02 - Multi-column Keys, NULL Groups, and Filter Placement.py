# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC
# MAGIC # 02 - Multi-column Keys, NULL Groups, and Filter Placement
# MAGIC
# MAGIC ## Two traps in the key list and filter
# MAGIC
# MAGIC ### Trap 1: An unexpected group
# MAGIC
# MAGIC Your stakeholder wants trips broken down by payment method (e.g., `card`, `wallet`, `cash`, `corporate`, `unknown`); you might encounter a `NULL` group as well. This group contains real trips without any payment record, and while `countDistinct` ignores `NULL`, `groupBy` includes it.
# MAGIC
# MAGIC ### Trap 2: Position of the filter answers different questions
# MAGIC
# MAGIC The questions “Which boroughs earned more than $90 in tips?” and “What are borough totals
# MAGIC from tips over $5?” both use `.filter()`, but they differ in context. A filter before `groupBy` excludes input rows, while a filter after `agg()` excludes aggregated groups, but placing the filter incorrectly will go unnoticed by Spark.
# MAGIC
# MAGIC ## What this notebook teaches
# MAGIC
# MAGIC | Section          | Concept                                | Why it matters                                                     |
# MAGIC | ---------------- | -------------------------------------- | ------------------------------------------------------------------ |
# MAGIC | 1. One key       | `countDistinct` vs `groupBy`           | Predict the number of output groups before running the aggregation |
# MAGIC | 1. Composite key | Two keys in one `groupBy`              | Output grain is defined by the full key list                       |
# MAGIC | 2. Filter first  | `.filter()` before `groupBy`           | Removes input trips, so aggregate values can change                |
# MAGIC | 2. Filter last   | `.filter()` after `.agg()`             | Removes groups after aggregate values are calculated               |
# MAGIC | Exercise         | Per-borough summary, then a second key | Apply both ideas to a new grouping key                             |
# MAGIC
# MAGIC **Reads:** `rideshare_dev.processed.trip_enriched` (106 rows). **No writes.**
# MAGIC
# MAGIC **Prerequisites:** Notebook 01 (`groupBy`, aliasing, NULL exclusion);
# MAGIC Module 7 (join NULL semantics).

# COMMAND ----------

# DBTITLE 1,Setup
# MAGIC %md
# MAGIC ## Setup — load `trip_enriched`
# MAGIC
# MAGIC Same managed table as Notebook 01: one row per `trip_id` (106 rows).
# MAGIC Shared setup details (column roles, types, inherited NULL map) stay in
# MAGIC Notebook 01 and `docs/data/dataset-overview.md`.
# MAGIC
# MAGIC This notebook uses:
# MAGIC - Group keys: `service_type`, `payment_method`, `pickup_borough`
# MAGIC - Measures: `base_fare_amount`, `tip_amount`, `trip_distance_miles`

# COMMAND ----------

from pyspark.sql import functions as F

trip_enriched_table = "rideshare_dev.processed.trip_enriched"

trip_enriched = spark.table(trip_enriched_table)  # noqa: F821

print("trip_enriched rows:", trip_enriched.count())

# COMMAND ----------

# DBTITLE 1,Section 1 - Composite keys and the NULL group
# MAGIC %md
# MAGIC ## 1. Composite keys and the NULL group
# MAGIC
# MAGIC ### Prediction prompt
# MAGIC
# MAGIC Before running anything, predict:
# MAGIC
# MAGIC - `countDistinct("payment_method")` returns how many values?
# MAGIC - `groupBy("payment_method").count()` returns how many rows?
# MAGIC
# MAGIC Will these two numbers agree? If not, what could cause the difference?

# COMMAND ----------

# DBTITLE 1,How many payment methods — countDistinct vs groupBy?
# Prove the gap: countDistinct vs groupBy group count
trip_enriched.select(
    F.countDistinct("service_type").alias("distinct_service_type"),
    F.countDistinct("payment_method").alias("distinct_payment_method"),
).show()

print("groupBy(payment_method) groups:", trip_enriched.groupBy("payment_method").count().count())

# Display all 6 groups
trip_enriched.groupBy("payment_method").agg(
    F.count("*").alias("trip_count"),
).orderBy(F.col("trip_count").desc()).show()

# COMMAND ----------

# DBTITLE 1,What makes trip 106 different from trips 104 and 105?
# Inspect the three edge-case trips: NULL key, NULL value, and sentinel
trip_enriched.filter(F.col("trip_id").isin(104, 105, 106)).select(
    "trip_id", "payment_method", "base_fare_amount",
).orderBy("trip_id").show()

# COMMAND ----------

# DBTITLE 1,Interpret: key NULL vs value NULL vs sentinel
# MAGIC %md
# MAGIC ### Interpretation
# MAGIC
# MAGIC | Trip | `payment_method` | `base_fare_amount` | What it shows |
# MAGIC |---|---|---|---|
# MAGIC | 104 | `card` (valid key) | NULL (missing value) | Row stays in the **card** group; NULL fare is excluded from aggregates (Notebook 01) |
# MAGIC | 105 | `unknown` (sentinel) | 12.00 | A real string — not NULL. Lowercase equivalent of Notebook 01’s `UNKNOWN` service type |
# MAGIC | 106 | NULL (missing key) | NULL | No payment row exists — this is the extra group that `countDistinct` missed |
# MAGIC
# MAGIC `countDistinct` excludes NULL → reports 5.  
# MAGIC `groupBy` keeps NULL as one group → returns 6.
# MAGIC
# MAGIC ### Composite key — predict before running
# MAGIC
# MAGIC - `service_type`: 5 groups (no NULLs in this column)
# MAGIC - `payment_method`: 6 groups
# MAGIC - Upper bound: `5 × 6 = 30` possible pairs
# MAGIC
# MAGIC How many pairs actually exist in the data?

# COMMAND ----------

# DBTITLE 1,For each service type and payment method: trip count and total base fare?
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
# MAGIC ## 2. `WHERE` vs `HAVING` with the same `.filter()`
# MAGIC
# MAGIC Concrete check first (same borough metric, three query shapes):
# MAGIC
# MAGIC | Query | Groups | Manhattan total |
# MAGIC |---|---|---|
# MAGIC | No filter | 5 | 134.45 |
# MAGIC | `WHERE tip_amount > 5` (before `groupBy`) | 4 | **91.00** |
# MAGIC | `HAVING total_tip > 90` (after `agg`) | 2 | **134.45** |
# MAGIC
# MAGIC **Rule:** placement changes meaning.
# MAGIC
# MAGIC - `.filter()` before `groupBy(...).agg(...)` is a `WHERE`
# MAGIC   - drops input rows
# MAGIC   - aggregate values change
# MAGIC - `.filter()` after `.agg(...)` is a `HAVING`
# MAGIC   - drops whole groups
# MAGIC   - aggregate values stay the same as unfiltered aggregate
# MAGIC
# MAGIC There is no `.having()` method in the DataFrame API; you filter on the
# MAGIC alias created in `.agg()`.
# MAGIC
# MAGIC **Performance habit:** filter as early as the question allows to reduce
# MAGIC shuffle input.

# COMMAND ----------

# DBTITLE 1,What is the total tip for each pickup borough?
borough_tips = trip_enriched.groupBy("pickup_borough").agg(
    F.count("*").alias("trip_count"),
    F.sum("tip_amount").alias("total_tip"),
)

print("No filter — 5 groups, all 106 trips:")
borough_tips.orderBy(F.col("total_tip").desc()).show()

# COMMAND ----------

# DBTITLE 1,What is the total tip for each borough if we only count tips over $5?
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

# DBTITLE 1,Which boroughs received more than $90 in total tips?
# HAVING — filter runs after, on the alias, so totals match the unfiltered run
print("HAVING total_tip > 90 (applied after agg):")
borough_tips.filter(F.col("total_tip") > 90).orderBy(F.col("total_tip").desc()).show()

# COMMAND ----------

# DBTITLE 1,Exercise
# MAGIC %md
# MAGIC ## Exercise — per-borough summary, then composite check
# MAGIC
# MAGIC **Steps 1–3:** apply `HAVING` logic on single key `pickup_borough`.
# MAGIC **Step 4:** add the second key (`payment_method`) to practice composite grain.
# MAGIC
# MAGIC **1. Predict.** Set `predicted_borough_groups` from
# MAGIC `countDistinct("pickup_borough")`. Zone columns have no NULLs, so no extra
# MAGIC NULL group here.
# MAGIC
# MAGIC **2. Aggregate.** One row per `pickup_borough`, with:
# MAGIC - `trip_count` = all trips
# MAGIC - `dated_trip_count` = non-NULL `trip_date`
# MAGIC - `total_base_fare` = sum(`base_fare_amount`) rounded to 2
# MAGIC - `avg_distance_miles` = avg(`trip_distance_miles`) rounded to 2
# MAGIC
# MAGIC **3. Apply `HAVING`.** Keep boroughs with `trip_count > 10`.
# MAGIC Then explain: why Manhattan `total_base_fare` is unchanged before/after.
# MAGIC
# MAGIC **Expected results for step 2:**
# MAGIC
# MAGIC | pickup_borough | trip_count | dated_trip_count | total_base_fare | avg_distance_miles |
# MAGIC |---|---|---|---|---|
# MAGIC | Manhattan | 44 | 41 | 1389.04 | 7.60 |
# MAGIC | Brooklyn | 29 | 27 | 927.91 | 8.01 |
# MAGIC | Queens | 22 | 21 | 632.40 | 7.89 |
# MAGIC | Bronx | 10 | 10 | 341.54 | 8.61 |
# MAGIC | Staten Island | 1 | 1 | 16.94 | 6.10 |
# MAGIC
# MAGIC **4. Composite key check.** Build one row per
# MAGIC (`pickup_borough`, `payment_method`) with `trip_count`.
# MAGIC Predict first; verify after running.
# MAGIC
# MAGIC Use both rules:
# MAGIC - upper bound: `groups(pickup_borough) * groups(payment_method)`
# MAGIC - `payment_method` contributes **6** groups (not 5)

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
# MAGIC | # | Concept | Rule |
# MAGIC |---|---|---|
# MAGIC | 1 | NULL group key | `groupBy` keeps NULL as one group; `countDistinct` excludes it |
# MAGIC | 2 | Sentinel vs NULL | `"unknown"` is a real string; NULL means no row exists |
# MAGIC | 3 | Composite grain | Output rows = observed key combinations only |
# MAGIC | 4 | Filter before aggregation | Removes rows — aggregate values change |
# MAGIC | 5 | Filter after aggregation | Removes groups — aggregate values stay unchanged |
# MAGIC
# MAGIC Next notebook: **`03 - Aggregate Functions Beyond Count and Sum`**.