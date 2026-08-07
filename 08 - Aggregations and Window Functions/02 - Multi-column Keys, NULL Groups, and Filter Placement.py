# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC
# MAGIC # 02 - Multi-column Keys, NULL Groups, and Filter Placement
# MAGIC
# MAGIC ## Two traps: the NULL group and the filter's position
# MAGIC
# MAGIC ### Trap 1: An unexpected group
# MAGIC
# MAGIC Your stakeholder wants trips broken down by payment method. You check the
# MAGIC distinct values first — `card`, `wallet`, `cash`, `corporate`, `unknown` —
# MAGIC and build the report for exactly those five.
# MAGIC
# MAGIC The `groupBy` returns one more group, keyed `NULL`: trips with no payment
# MAGIC method. Nothing failed, and that group contains real trips.
# MAGIC
# MAGIC ### Trap 2: The filter's position changes the question
# MAGIC
# MAGIC "Which boroughs earned more than $90 in tips?" and "What are borough totals
# MAGIC from tips over $5?" are different questions, yet both are written with
# MAGIC `.filter()`.
# MAGIC
# MAGIC A filter before `groupBy` excludes input rows; a filter after
# MAGIC `agg()` excludes aggregated groups.
# MAGIC
# MAGIC ## What this notebook teaches
# MAGIC
# MAGIC | Section | Concept | Why it matters |
# MAGIC |---|---|---|
# MAGIC | 1 | `countDistinct` vs `groupBy` | Predict the group count before running |
# MAGIC | 1a | Composite key | Only pairs that exist in the data become rows |
# MAGIC | 2a–2d | Filter placement | Compare filtering input rows with filtering groups |
# MAGIC | Exercise | Per-borough summary, then a second key | Apply both ideas to a new key |
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

# DBTITLE 1,Section 1 - countDistinct vs groupBy
# MAGIC %md
# MAGIC ## 1. `countDistinct` vs `groupBy`
# MAGIC
# MAGIC Before writing the business logic, predict whether these two values should match.
# MAGIC
# MAGIC If they do not match, determine which result matches the business
# MAGIC requirement and explain why.
# MAGIC
# MAGIC
# MAGIC ### How many payment methods — `countDistinct` vs `groupBy`?

# COMMAND ----------

# 1. Display every payment_method group (watch for a NULL row)
trip_enriched.groupBy("payment_method").agg(
    F.count("*").alias("trip_count"),
).orderBy(F.col("trip_count").desc()).show()

# COMMAND ----------

# 2. Count groups — includes the NULL group
print(
    "groupBy(payment_method) groups:",
    trip_enriched.groupBy("payment_method").count().count(),
)

# COMMAND ----------

# 3. Distinct values — countDistinct skips NULL
trip_enriched.select(
    F.countDistinct("payment_method").alias("distinct_payment_method"),
).show()

# COMMAND ----------

# DBTITLE 1,Section 1a - Composite key
# MAGIC %md
# MAGIC ## 1a. Composite key
# MAGIC
# MAGIC - `service_type`: 5 groups (no NULLs in this column)
# MAGIC - `payment_method`: 6 groups
# MAGIC - Upper bound: `5 × 6 = 30` possible pairs
# MAGIC
# MAGIC How many pairs actually exist in the data?
# MAGIC
# MAGIC ### For each service type and payment method: trip count and total base fare?

# COMMAND ----------

# 1. One row per observed (service_type, payment_method) pair
method_by_service = trip_enriched.groupBy("service_type", "payment_method").agg(
    F.count("*").alias("trip_count"),
    F.round(F.sum("base_fare_amount"), 2).alias("total_base_fare"),
)

method_by_service.orderBy("service_type", "payment_method").show(30)

# COMMAND ----------

# 2. Count pairs — at most 5 * 6 = 30; only combinations in the data appear
print("output rows:", method_by_service.count(), "(at most 5 * 6 = 30)")
# Expected: 18

# COMMAND ----------

# DBTITLE 1,Section 2 - Filter placement
# MAGIC %md
# MAGIC ## 2. Filter placement
# MAGIC
# MAGIC | Query | Groups | Manhattan total |
# MAGIC |---|---|---|
# MAGIC | No filter | 5 | 134.45 |
# MAGIC | `WHERE tip_amount > 5` (before `groupBy`) | 4 | **91.00** |
# MAGIC | `HAVING total_tip > 90` (after `agg`) | 2 | **134.45** |
# MAGIC
# MAGIC There is no `.having()` method in the DataFrame API; you filter on the
# MAGIC alias created in `.agg()`.
# MAGIC
# MAGIC **Performance habit:** filter as early as the question allows to reduce
# MAGIC shuffle input.

# COMMAND ----------

# DBTITLE 1,2a - Inspect combinations
# MAGIC %md
# MAGIC ### 2a. Which pickup borough and tip combinations exist?

# COMMAND ----------

# Inspection only — do not use this deduplicated view to calculate totals
pickup_borough_tip_combinations = (
    trip_enriched.select("pickup_borough", "tip_amount")
    .distinct()
    .orderBy("pickup_borough", "tip_amount")
)

pickup_borough_tip_combinations.show(106, truncate=False)

# COMMAND ----------

# DBTITLE 1,2b - Filter input rows
# MAGIC %md
# MAGIC ### 2b. Which trip rows remain when `tip_amount > 5`?

# COMMAND ----------

# Keep original rows so repeated borough-tip pairs still contribute to totals
tips_over_5 = trip_enriched.filter(F.col("tip_amount") > 5).select(
    "pickup_borough",
    "tip_amount",
)

tips_over_5.orderBy("pickup_borough", "tip_amount").show(106, truncate=False)

# COMMAND ----------

# DBTITLE 1,2c - Aggregate filtered rows
# MAGIC %md
# MAGIC ### 2c. What are the borough totals after filtering the input trips?

# COMMAND ----------

# Only tip rows over $5 reach the shuffle and aggregate
borough_tips_over_5 = tips_over_5.groupBy("pickup_borough").agg(
    F.round(F.sum("tip_amount"), 2).alias("total_tip"),
)

borough_tips_over_5.orderBy(F.col("total_tip").desc()).show()

# COMMAND ----------

# DBTITLE 1,2d - Aggregate all rows
# MAGIC %md
# MAGIC ### 2d. Which unfiltered borough totals exceed $90?

# COMMAND ----------

# Calculate each borough total before deciding which groups to keep
borough_tips = trip_enriched.groupBy("pickup_borough").agg(
    F.round(F.sum("tip_amount"), 2).alias("total_tip"),
)

borough_tips.orderBy(F.col("total_tip").desc()).show()

# COMMAND ----------

# DBTITLE 1,2d - Filter aggregate result

# Keep groups by filtering the alias created in agg()
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
# MAGIC | 1 | `countDistinct` vs `groupBy` | `groupBy` keeps a NULL group; distinct skips it |
# MAGIC | 1a | Composite key | Only key pairs present in the data become rows |
# MAGIC | 2 | Filter placement | Before grouping removes rows; after aggregation removes groups |
# MAGIC
# MAGIC Next notebook: **`03 - Aggregate Functions Beyond Count and Sum`**.
