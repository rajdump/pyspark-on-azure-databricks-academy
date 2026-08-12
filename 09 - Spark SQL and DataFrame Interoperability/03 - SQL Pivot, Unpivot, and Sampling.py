# Databricks notebook source
# MAGIC %md
# MAGIC # 03 - SQL Pivot, Unpivot, and Sampling
# MAGIC
# MAGIC Reshape borough × service counts long → wide → long, then a brief sampling
# MAGIC coda.
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC - Reshape long → wide with SQL `PIVOT` and back with `UNPIVOT`
# MAGIC - Fill sparse pivot NULLs with `COALESCE` and register a SQL temp view
# MAGIC - Contrast SQL `TABLESAMPLE` (non-deterministic here) with seeded DataFrame
# MAGIC   sampling
# MAGIC
# MAGIC **Callbacks:** Module 8 `04 - Pivot` (DataFrame `pivot`); Module 8
# MAGIC `07 - Top-N per Group and Sampling` (seeded `.sample()`). SQL wins on
# MAGIC `UNPIVOT` versus an awkward DataFrame `stack()`.
# MAGIC
# MAGIC **Reads:** `rideshare_dev.processed.trip_enriched` (106). **No writes.**
# MAGIC
# MAGIC **Prerequisites:** Module 9 `02 - SQL Joins, Aggregations, and Filtering`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup — load `trip_enriched`
# MAGIC
# MAGIC Columns used here: `pickup_borough`, `service_type`, `payment_method`,
# MAGIC `trip_id`.

# COMMAND ----------

trip_enriched = spark.table("rideshare_dev.processed.trip_enriched")  # noqa: F821

print(f"trip_enriched: {trip_enriched.count()} rows")  # expect 106

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Long-form baseline
# MAGIC
# MAGIC Establish the long data `PIVOT` will reshape: one row per
# MAGIC (`pickup_borough`, `service_type`) with a trip count.
# MAGIC
# MAGIC **Expected:** **18** rows (not 17) — some borough × service combos are
# MAGIC missing and will become NULLs after the pivot.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   pickup_borough,
# MAGIC   service_type,
# MAGIC   COUNT(*) AS trip_count
# MAGIC FROM rideshare_dev.processed.trip_enriched
# MAGIC GROUP BY pickup_borough, service_type
# MAGIC ORDER BY 1, 2

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. PIVOT to wide
# MAGIC
# MAGIC `PIVOT` turns `service_type` values into columns. A NULL cell means zero
# MAGIC matching rows for that borough × service (watch Bronx / Staten Island).
# MAGIC
# MAGIC **Expected:** **5** borough rows × the five service columns.

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
# MAGIC Optional zeros via `COALESCE(col, 0)` — same idea as
# MAGIC `02 - SQL Joins, Aggregations, and Filtering`, now on pivot columns.
# MAGIC
# MAGIC Register with pure SQL `CREATE OR REPLACE TEMP VIEW` (not Python
# MAGIC `createOrReplaceTempView` from `01 - Dual API Foundations and When to
# MAGIC Choose`). A CTE can replace this temp view later in
# MAGIC `05 - CTEs and Parameterized SQL`.

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
# MAGIC `UNPIVOT` proves the reshape. Rows with `0` are now **explicit** — Step 1's
# MAGIC long form omitted missing combos entirely.

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
# MAGIC ## 5. TABLESAMPLE coda
# MAGIC
# MAGIC Brief coda. Module 8 `07 - Top-N per Group and Sampling` used seeded
# MAGIC `.sample()` for reproducible draws. SQL `TABLESAMPLE (25 PERCENT)` here is
# MAGIC **non-deterministic** — re-run and the row set can change.
# MAGIC
# MAGIC **Expected:** roughly ~25 rows (not exact).

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM rideshare_dev.processed.trip_enriched TABLESAMPLE (25 PERCENT)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Full reshape round-trip on **`payment_method`** by `pickup_borough` —
# MAGIC `PIVOT` then `UNPIVOT` (not `UNPIVOT` alone).
# MAGIC
# MAGIC Use these payment values as columns: `card`, `cash`, `wallet`, `corporate`,
# MAGIC `unknown`. Coalesce NULLs to 0 before unpivoting. Note Staten Island
# MAGIC sparsity (and that a NULL `payment_method` on trip 106 does not become its
# MAGIC own column when the `IN` list is explicit).
# MAGIC
# MAGIC **Expected:** 5×5 wide matrix, then long form back from the coalesced wide
# MAGIC table.

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
# MAGIC -- Prefer one statement: UNPIVOT a subquery that applies COALESCE
# MAGIC -- (or: CREATE TEMP VIEW in one cell, UNPIVOT in the next — not both in one %sql cell)
# MAGIC SELECT pickup_borough
# MAGIC FROM rideshare_dev.processed.trip_enriched
# MAGIC WHERE 1 = 0

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - `PIVOT` reshapes long → wide; NULL cells mark missing combos
# MAGIC - `COALESCE` makes zeros explicit; SQL temp views hold the wide table
# MAGIC - `UNPIVOT` round-trips — including the zero rows Step 1 never showed
# MAGIC - Prefer seeded DataFrame `.sample()` when you need a reproducible draw
# MAGIC
# MAGIC **Next:** `04 - SQL Windows and QUALIFY` — ranking, running totals, and `LAG`.
