# Databricks notebook source
# MAGIC %md
# MAGIC # 04 - SQL Windows and QUALIFY
# MAGIC
# MAGIC Two arcs on Module 8 KPI tables: rank zones within a borough, then track
# MAGIC daily distance over time.
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC - Rank within partitions with `ROW_NUMBER() OVER (...)` and filter with
# MAGIC   `QUALIFY`
# MAGIC - Write the equivalent subquery / CTE form for engines without `QUALIFY`
# MAGIC - Compute running totals and day-over-day change with `SUM` / `LAG`
# MAGIC
# MAGIC **Callbacks:** Module 8 `05 - Window Functions Fundamentals` and
# MAGIC `06 - Running Totals and Lag and Lead` — this notebook is the SQL spelling.
# MAGIC `RANK` / `DENSE_RANK` tie behavior stays in Module 8; we use `ROW_NUMBER`
# MAGIC here.
# MAGIC
# MAGIC **Reads:** `kpi_zone_performance` (20), `kpi_daily_trip_summary` (14).
# MAGIC **No writes.**
# MAGIC
# MAGIC **Prerequisites:** Module 9 `03 - SQL Pivot, Unpivot, and Sampling`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup — load zone + daily KPI tables
# MAGIC
# MAGIC Zone KPI: `pickup_borough`, `pickup_zone`, `total_tip`, `trip_count`.
# MAGIC Daily KPI: `trip_date`, `total_distance_miles`.

# COMMAND ----------

kpi_zone = spark.table(  # noqa: F821
    "rideshare_dev.processed.kpi_zone_performance"
)
kpi_daily = spark.table(  # noqa: F821
    "rideshare_dev.processed.kpi_daily_trip_summary"
)

print(f"kpi_zone_performance: {kpi_zone.count()} rows")  # expect 20
print(f"kpi_daily_trip_summary: {kpi_daily.count()} rows")  # expect 14

# COMMAND ----------

# MAGIC %md
# MAGIC ## Arc A — Ranking on `kpi_zone_performance`
# MAGIC
# MAGIC ### A1 — Window anatomy
# MAGIC
# MAGIC ```text
# MAGIC <window_fn> OVER (PARTITION BY ... ORDER BY ...)
# MAGIC ```
# MAGIC
# MAGIC Same idea as Module 8 `Window.partitionBy(...).orderBy(...)`.
# MAGIC
# MAGIC **`ORDER BY` inside `OVER` ranks within the window — it is not the final
# MAGIC result sort.** Add a separate `ORDER BY` if you want display order.
# MAGIC
# MAGIC Goal: rank zones by `total_tip` within each `pickup_borough`.
# MAGIC
# MAGIC **Expected:** **20** rows; Manhattan `rn` 1–8; Staten Island `rn` = 1 only.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   pickup_borough,
# MAGIC   pickup_zone,
# MAGIC   total_tip,
# MAGIC   ROW_NUMBER() OVER (
# MAGIC     PARTITION BY pickup_borough
# MAGIC     ORDER BY total_tip DESC
# MAGIC   ) AS rn
# MAGIC FROM rideshare_dev.processed.kpi_zone_performance
# MAGIC ORDER BY pickup_borough, rn

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2 — QUALIFY
# MAGIC
# MAGIC `QUALIFY` filters on a window expression **without** wrapping the query in
# MAGIC a subquery. Keep Top-2 zones per borough by tip.
# MAGIC
# MAGIC **Expected:** **9** rows (Staten Island has only one zone, so 4×2 + 1).

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   pickup_borough,
# MAGIC   pickup_zone,
# MAGIC   total_tip,
# MAGIC   ROW_NUMBER() OVER (
# MAGIC     PARTITION BY pickup_borough
# MAGIC     ORDER BY total_tip DESC
# MAGIC   ) AS rn
# MAGIC FROM rideshare_dev.processed.kpi_zone_performance
# MAGIC QUALIFY ROW_NUMBER() OVER (
# MAGIC   PARTITION BY pickup_borough
# MAGIC   ORDER BY total_tip DESC
# MAGIC ) <= 2
# MAGIC ORDER BY pickup_borough, rn

# COMMAND ----------

# MAGIC %md
# MAGIC ### A3 — Equivalent subquery form
# MAGIC
# MAGIC Same filter as a subquery / CTE with `WHERE rn <= 2`.
# MAGIC
# MAGIC Portability: Spark, Snowflake, and BigQuery support `QUALIFY`. Postgres
# MAGIC does not — use this wrapper form there.
# MAGIC
# MAGIC **Expected:** same **9** rows.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT pickup_borough, pickup_zone, total_tip, rn
# MAGIC FROM (
# MAGIC   SELECT
# MAGIC     pickup_borough,
# MAGIC     pickup_zone,
# MAGIC     total_tip,
# MAGIC     ROW_NUMBER() OVER (
# MAGIC       PARTITION BY pickup_borough
# MAGIC       ORDER BY total_tip DESC
# MAGIC     ) AS rn
# MAGIC   FROM rideshare_dev.processed.kpi_zone_performance
# MAGIC ) ranked
# MAGIC WHERE rn <= 2
# MAGIC ORDER BY pickup_borough, rn

# COMMAND ----------

# MAGIC %md
# MAGIC ## Arc B — Time-series on `kpi_daily_trip_summary`
# MAGIC
# MAGIC ### B1 — Running total
# MAGIC
# MAGIC Running sum of `total_distance_miles` ordered by `trip_date`, with an
# MAGIC explicit `ROWS` frame (same caution Module 8 taught for default `RANGE`).
# MAGIC
# MAGIC **Expected:** **14** rows; running distance **21.35 → 113.34 → … → 793.20**.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   trip_date,
# MAGIC   total_distance_miles,
# MAGIC   SUM(total_distance_miles) OVER (
# MAGIC     ORDER BY trip_date
# MAGIC     ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
# MAGIC   ) AS running_distance
# MAGIC FROM rideshare_dev.processed.kpi_daily_trip_summary
# MAGIC ORDER BY trip_date

# COMMAND ----------

# MAGIC %md
# MAGIC ### B2 — Day-over-day with LAG
# MAGIC
# MAGIC **What's new:** `LAG` pulls the prior day's distance. The first row's
# MAGIC previous value is naturally NULL.
# MAGIC
# MAGIC **Expected:** `delta` starts NULL, then **+70.64, −61.99, +25.52…**

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   trip_date,
# MAGIC   total_distance_miles,
# MAGIC   SUM(total_distance_miles) OVER (
# MAGIC     ORDER BY trip_date
# MAGIC     ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
# MAGIC   ) AS running_distance,
# MAGIC   LAG(total_distance_miles, 1) OVER (ORDER BY trip_date) AS prev_day,
# MAGIC   total_distance_miles
# MAGIC     - LAG(total_distance_miles, 1) OVER (ORDER BY trip_date) AS delta
# MAGIC FROM rideshare_dev.processed.kpi_daily_trip_summary
# MAGIC ORDER BY trip_date

# COMMAND ----------

# MAGIC %md
# MAGIC ### B3 — Direction label (CASE)
# MAGIC
# MAGIC Reuse the `CASE` habit from `01 - Dual API Foundations and When to Choose`
# MAGIC and `02 - SQL Joins, Aggregations, and Filtering` — direction label only.
# MAGIC
# MAGIC Check **NULL first**: day 1 has no prior day; labeling it `flat` would be
# MAGIC misleading. The outer query wraps B2 so `CASE` can reference `delta` by
# MAGIC name (Spark does not reuse select-list aliases in the same `SELECT`).

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   trip_date,
# MAGIC   total_distance_miles,
# MAGIC   running_distance,
# MAGIC   prev_day,
# MAGIC   delta,
# MAGIC   CASE
# MAGIC     WHEN delta IS NULL THEN 'n/a'
# MAGIC     WHEN delta > 0 THEN 'up'
# MAGIC     WHEN delta < 0 THEN 'down'
# MAGIC     ELSE 'flat'
# MAGIC   END AS direction
# MAGIC FROM (
# MAGIC   SELECT
# MAGIC     trip_date,
# MAGIC     total_distance_miles,
# MAGIC     SUM(total_distance_miles) OVER (
# MAGIC       ORDER BY trip_date
# MAGIC       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
# MAGIC     ) AS running_distance,
# MAGIC     LAG(total_distance_miles, 1) OVER (ORDER BY trip_date) AS prev_day,
# MAGIC     total_distance_miles
# MAGIC       - LAG(total_distance_miles, 1) OVER (ORDER BY trip_date) AS delta
# MAGIC   FROM rideshare_dev.processed.kpi_daily_trip_summary
# MAGIC ) daily_delta
# MAGIC ORDER BY trip_date

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Top-2 zones per borough by **`trip_count`** (not tip), and only keep zones
# MAGIC with `trip_count >= 3`. You need **`WHERE` and `QUALIFY` together**.
# MAGIC
# MAGIC **Expected:** **8** rows (Staten Island drops out).

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Top-2 by trip_count per borough, only zones with trip_count >= 3 (expect 8)
# MAGIC SELECT
# MAGIC   pickup_borough,
# MAGIC   pickup_zone,
# MAGIC   trip_count
# MAGIC   -- TODO: ROW_NUMBER() ... AS rn
# MAGIC FROM rideshare_dev.processed.kpi_zone_performance
# MAGIC WHERE 1 = 0  -- TODO: trip_count >= 3
# MAGIC -- TODO: QUALIFY ... <= 2
# MAGIC ORDER BY pickup_borough, trip_count DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - `OVER (PARTITION BY … ORDER BY …)` ranks within a group; final `ORDER BY`
# MAGIC   is separate
# MAGIC - `QUALIFY` filters window results in place; subquery/`WHERE rn` is the
# MAGIC   portable spelling
# MAGIC - Explicit `ROWS` running `SUM` and `LAG` build day-over-day change
# MAGIC - Direction `CASE` must test NULL before up/down/flat
# MAGIC
# MAGIC **Next:** `05 - CTEs and Parameterized SQL` — named intermediates and
# MAGIC `:params`.
