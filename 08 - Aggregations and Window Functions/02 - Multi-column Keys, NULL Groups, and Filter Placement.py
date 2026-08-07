# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC
# MAGIC # 02 - Multi-column Keys, NULL Groups, and Filter Placement
# MAGIC
# MAGIC Few common mistakes can significantly impact aggregate results:
# MAGIC
# MAGIC 1. **NULL Behavior**: In `groupBy`, `NULL` values create a separate group, while in `sum` or `avg`, they are ignored in calculations.
# MAGIC
# MAGIC 2. **Filter Position**: Filtering **before** `groupBy` removes rows that don’t meet conditions, while filtering **after** `agg` removes groups based on accumulated values.
# MAGIC
# MAGIC | Scenario                                           | What happens                                                                                          |
# MAGIC | -------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
# MAGIC | Group by `payment_method`                          | Spark returns **6 groups**: five payment methods plus one `NULL` group                                |
# MAGIC | Apply `sum` or `avg` to a column containing `NULL` | Spark ignores the `NULL` values and calculates the aggregate using the remaining values               |
# MAGIC | Filter `tip_amount > 5` before `groupBy`           | Spark removes rows that do not meet the condition before aggregation |
# MAGIC | Filter `total_tip > 90` after `agg()`              | Spark removes groups whose aggregated `total_tip` does not meet the condition                         |
# MAGIC
# MAGIC
# MAGIC
# MAGIC This notebook addresses both topics in the following order:
# MAGIC
# MAGIC 1. Composite keys and the NULL group — key versus value
# MAGIC 2. `WHERE` vs `HAVING` — the same `.filter()`, different implications
# MAGIC
# MAGIC **Reads:** `rideshare_dev.processed.trip_enriched` (106 rows). **No writes.**
# MAGIC
# MAGIC **Prerequisites:** Notebook 01 (covering `groupBy`, aliasing, and NULL
# MAGIC skipping); Module 7 (join NULL semantics).

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

# DBTITLE 1,Section 1 - Multi-column grouping
# MAGIC %md
# MAGIC ## 1. Composite keys and the NULL group
# MAGIC
# MAGIC Start with the result you should predict **before** running:
# MAGIC
# MAGIC | Aggregate | Predicted groups |
# MAGIC |---|---|
# MAGIC | `groupBy("service_type")` | 5 |
# MAGIC | `groupBy("payment_method")` | 6 (`card`, `wallet`, `cash`, `corporate`, `unknown`, `NULL`) |  # noqa: E501
# MAGIC | `groupBy("service_type", "payment_method")` | at most `5 * 6 = 30` |
# MAGIC
# MAGIC The actual composite output is **18** rows, not 30, because Spark returns
# MAGIC only combinations that exist in data.
# MAGIC
# MAGIC **Rule:** a `groupBy` grain is the **full key list**. Adding keys splits
# MAGIC existing groups, so row count can only stay same or increase.
# MAGIC
# MAGIC ### Why 6 groups for `payment_method` if `countDistinct` is 5?
# MAGIC
# MAGIC | Operation | NULL behavior |
# MAGIC |---|---|
# MAGIC | `join` | NULL keys do not match (`NULL = NULL` is not true) |
# MAGIC | `countDistinct` | NULL is ignored |
# MAGIC | `groupBy` | NULL keys collapse into one output group |
# MAGIC
# MAGIC So `countDistinct("payment_method")` returns 5, while
# MAGIC `groupBy("payment_method")` returns 6.
# MAGIC
# MAGIC `unknown` and `NULL` are different:
# MAGIC - `unknown`: normalized sentinel for a blank method (trip 105)
# MAGIC - `NULL`: no payment row at all (trip 106)

# COMMAND ----------

# DBTITLE 1,How many payment methods — countDistinct vs groupBy("payment_method")?
trip_enriched.select(
    F.countDistinct("service_type").alias("distinct_service_type"),
    F.countDistinct("payment_method").alias("distinct_payment_method"),
).show()

print("groupBy(payment_method) groups:", trip_enriched.groupBy("payment_method").count().count())

# COMMAND ----------

# DBTITLE 1,How many trips used each payment method?
trip_enriched.groupBy("payment_method").agg(
    F.count("*").alias("trip_count"),
).orderBy(F.col("trip_count").desc()).show()

# Expected 6 rows: card 59, wallet 20, cash 17, corporate 8, unknown 1, NULL 1

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
# MAGIC | Concept | What to remember |
# MAGIC |---|---|
# MAGIC | Composite key grain | Output row = one observed key combination |
# MAGIC | NULL group behavior | `groupBy` keeps one NULL group; `countDistinct` ignores NULL |
# MAGIC | `unknown` vs NULL | Sentinel string and missing join row are different issues |
# MAGIC | Filter placement | `WHERE` changes values; `HAVING` changes which groups survive |
# MAGIC
# MAGIC Next notebook: **`03 - Aggregate Functions Beyond Count and Sum`**.