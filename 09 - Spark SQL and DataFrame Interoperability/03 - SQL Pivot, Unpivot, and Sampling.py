# Databricks notebook source
# MAGIC %md
# MAGIC # 03 - SQL Pivot, Unpivot, and Sampling
# MAGIC
# MAGIC In this notebook, we'll reshape trip counts between **long** and **wide**
# MAGIC formats with Spark SQL.
# MAGIC
# MAGIC We'll start with one row per borough and service type, pivot service types
# MAGIC into columns, then unpivot those columns back into rows.
# MAGIC
# MAGIC We'll finish with a short look at SQL `TABLESAMPLE`.
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC - Reshape long-form data to wide form with `PIVOT`
# MAGIC - Convert wide-form data back to long form with `UNPIVOT`
# MAGIC - Replace missing pivot combinations with `COALESCE`
# MAGIC - Store an intermediate result in a SQL temp view
# MAGIC - Compare SQL `TABLESAMPLE` with seeded DataFrame sampling
# MAGIC
# MAGIC **Callbacks:** Module 8 `04 - Pivot` introduced the DataFrame `pivot`
# MAGIC operation; Module 8 `07 - Top-N per Group and Sampling` used seeded
# MAGIC `.sample()`. Here we use the SQL forms, including `UNPIVOT`.
# MAGIC
# MAGIC **Reads:** `rideshare_dev.processed.trip_enriched` — **106 rows**
# MAGIC
# MAGIC **Writes:** None.
# MAGIC
# MAGIC **Prerequisites:** Module 9 `02 - SQL Joins, Aggregations, and Filtering`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup — load `trip_enriched`
# MAGIC
# MAGIC We'll use `trip_enriched` throughout the notebook.
# MAGIC
# MAGIC The main columns are:
# MAGIC
# MAGIC - `pickup_borough` — the row grouping
# MAGIC - `service_type` — the values we'll pivot into columns
# MAGIC - `trip_id` — used to count trips
# MAGIC - `payment_method` — used later in the exercise
# MAGIC
# MAGIC The table contains **106 trips**.

# COMMAND ----------

trip_enriched = spark.table("rideshare_dev.processed.trip_enriched")  # noqa: F821

print(f"trip_enriched: {trip_enriched.count()} rows")  # expect 106

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Long-form baseline
# MAGIC
# MAGIC Before pivoting, look at the data in its current shape.
# MAGIC
# MAGIC Each row is one `pickup_borough` + `service_type` combination with a trip
# MAGIC count. Not every borough × service combination exists in the source data —
# MAGIC those missing combinations become visible after we pivot.
# MAGIC
# MAGIC **Expected:** **18 rows**.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   pickup_borough,
# MAGIC   service_type,
# MAGIC   COUNT(*) AS trip_count
# MAGIC FROM rideshare_dev.processed.trip_enriched
# MAGIC GROUP BY pickup_borough, service_type
# MAGIC ORDER BY pickup_borough, service_type

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. PIVOT to wide
# MAGIC
# MAGIC `PIVOT` turns values from `service_type` into separate columns.
# MAGIC
# MAGIC The grain changes from one row per `pickup_borough` + `service_type` to one
# MAGIC row per `pickup_borough`. The listed service types become columns such as
# MAGIC `STANDARD`, `PREMIUM`, and `XL`.
# MAGIC
# MAGIC If a borough has no trips for one of the listed service types, that pivot
# MAGIC cell appears as NULL — a missing combination, not yet a zero.
# MAGIC
# MAGIC **Expected:** **5 borough rows** with **5 service-type columns**.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM (
# MAGIC   SELECT pickup_borough, service_type, trip_id
# MAGIC   FROM rideshare_dev.processed.trip_enriched
# MAGIC )
# MAGIC PIVOT (
# MAGIC   COUNT(trip_id)
# MAGIC   FOR service_type IN (
# MAGIC     'STANDARD',
# MAGIC     'PREMIUM',
# MAGIC     'XL',
# MAGIC     'SHARED',
# MAGIC     'UNKNOWN'
# MAGIC   )
# MAGIC )
# MAGIC ORDER BY pickup_borough

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. COALESCE zeros + SQL temp view
# MAGIC
# MAGIC The pivot result contains NULLs where a borough has no trips for a listed
# MAGIC service type. Use `COALESCE(column, 0)` to make those missing combinations
# MAGIC explicit as zero counts — the same idea as in
# MAGIC `02 - SQL Joins, Aggregations, and Filtering`, now on pivot columns.
# MAGIC
# MAGIC Store the wide result in a session temp view named `borough_service_wide`
# MAGIC with SQL `CREATE OR REPLACE TEMP VIEW`. Later SQL cells can query it
# MAGIC directly by name.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TEMP VIEW borough_service_wide AS
# MAGIC SELECT
# MAGIC   pickup_borough,
# MAGIC   COALESCE(STANDARD, 0) AS STANDARD,
# MAGIC   COALESCE(PREMIUM, 0) AS PREMIUM,
# MAGIC   COALESCE(XL, 0) AS XL,
# MAGIC   COALESCE(SHARED, 0) AS SHARED,
# MAGIC   COALESCE(UNKNOWN, 0) AS UNKNOWN
# MAGIC FROM (
# MAGIC   SELECT *
# MAGIC   FROM (
# MAGIC     SELECT pickup_borough, service_type, trip_id
# MAGIC     FROM rideshare_dev.processed.trip_enriched
# MAGIC   )
# MAGIC   PIVOT (
# MAGIC     COUNT(trip_id)
# MAGIC     FOR service_type IN (
# MAGIC       'STANDARD',
# MAGIC       'PREMIUM',
# MAGIC       'XL',
# MAGIC       'SHARED',
# MAGIC       'UNKNOWN'
# MAGIC     )
# MAGIC   )
# MAGIC )

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM borough_service_wide
# MAGIC ORDER BY pickup_borough

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. UNPIVOT round-trip
# MAGIC
# MAGIC `UNPIVOT` performs the reverse reshape. The five service-type columns become
# MAGIC values in a single `service_type` column, and their counts move into
# MAGIC `trip_count`.
# MAGIC
# MAGIC Because we replaced pivot NULLs with `0`, the unpivoted result includes
# MAGIC those zero-count combinations explicitly. That differs from Step 1, where
# MAGIC combinations with no source rows did not appear at all.
# MAGIC
# MAGIC **Expected:** **25 rows** (5 boroughs × 5 service types).

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM borough_service_wide
# MAGIC UNPIVOT (
# MAGIC   trip_count FOR service_type IN (
# MAGIC     STANDARD,
# MAGIC     PREMIUM,
# MAGIC     XL,
# MAGIC     SHARED,
# MAGIC     UNKNOWN
# MAGIC   )
# MAGIC )
# MAGIC ORDER BY pickup_borough, service_type

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. TABLESAMPLE
# MAGIC
# MAGIC Spark SQL can sample rows directly from a table. Here we request
# MAGIC approximately **25%** of `trip_enriched` with `TABLESAMPLE (25 PERCENT)`.
# MAGIC
# MAGIC This sample is not seeded, so repeated runs can return a different set of
# MAGIC rows. The percentage is approximate, not an exact row-count guarantee.
# MAGIC
# MAGIC Module 8 `07 - Top-N per Group and Sampling` used seeded `.sample()` for
# MAGIC reproducible draws — prefer that when you need the same sample again.
# MAGIC
# MAGIC **Expected:** roughly **25–30 rows** from this 106-row table.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM rideshare_dev.processed.trip_enriched TABLESAMPLE (25 PERCENT)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Repeat the same reshape pattern using `payment_method`.
# MAGIC
# MAGIC ### Q1 — Pivot payment methods to columns
# MAGIC
# MAGIC Create one row per `pickup_borough` and pivot these payment methods into
# MAGIC columns:
# MAGIC
# MAGIC - `card`
# MAGIC - `cash`
# MAGIC - `wallet`
# MAGIC - `corporate`
# MAGIC - `unknown`
# MAGIC
# MAGIC Count trips with `trip_id`.
# MAGIC
# MAGIC **Expected:** **5 borough rows × 5 payment-method columns**.
# MAGIC
# MAGIC ### Q2 — Replace NULLs and unpivot
# MAGIC
# MAGIC Replace missing pivot values with `0`, then `UNPIVOT` the wide result back
# MAGIC to long form. The final result should include explicit zero-count rows for
# MAGIC missing borough and payment-method combinations.
# MAGIC
# MAGIC One source row has a NULL `payment_method`. Because NULL is not in the
# MAGIC explicit `PIVOT ... IN (...)` list, it does not become a separate pivot
# MAGIC column.
# MAGIC
# MAGIC **Expected:** long form from the coalesced wide table (explicit zeros
# MAGIC included).

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Q1: PIVOT payment_method by pickup_borough (expect 5 borough rows × 5 methods)
# MAGIC -- TODO: wrap a subquery in PIVOT (COUNT(trip_id) FOR payment_method IN (...))
# MAGIC SELECT pickup_borough
# MAGIC FROM rideshare_dev.processed.trip_enriched
# MAGIC WHERE 1 = 0

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Q2: COALESCE zeros, then UNPIVOT back to long (expect explicit 0 rows)
# MAGIC -- Hint: UNPIVOT a subquery that applies COALESCE, or create a temp view
# MAGIC -- then UNPIVOT in the next cell (not both in one %sql cell)
# MAGIC SELECT pickup_borough
# MAGIC FROM rideshare_dev.processed.trip_enriched
# MAGIC WHERE 1 = 0

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC In this notebook, we reshaped the same aggregated data in both directions:
# MAGIC
# MAGIC `long → PIVOT → wide → UNPIVOT → long`
# MAGIC
# MAGIC Key takeaways:
# MAGIC
# MAGIC - `PIVOT` turns values from one column into multiple columns
# MAGIC - Missing pivot combinations appear as NULL
# MAGIC - `COALESCE` can make those missing combinations explicit as zero
# MAGIC - `UNPIVOT` turns wide columns back into row values
# MAGIC - A SQL temp view can hold an intermediate result for later SQL cells
# MAGIC - `TABLESAMPLE` provides approximate sampling; use a seeded DataFrame
# MAGIC   sample when reproducibility matters
# MAGIC
# MAGIC **Next:** `04 - SQL Windows and QUALIFY` covers ranking, running totals,
# MAGIC and `LAG`.
