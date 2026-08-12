# Databricks notebook source
# MAGIC %md
# MAGIC # 04 - SQL Windows and QUALIFY
# MAGIC
# MAGIC A window function adds group-level information to each row while keeping
# MAGIC the row-level details (Module 8 `05 - Window Functions Fundamentals`).
# MAGIC
# MAGIC In this notebook, we'll answer two questions with Spark SQL:
# MAGIC
# MAGIC 1. Within each borough, which zones rank highest by total tip?
# MAGIC 2. How does total trip distance change from one day to the next?
# MAGIC
# MAGIC We'll also use `QUALIFY` to filter window results in the same query.
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC - Rank rows within a group with `ROW_NUMBER() OVER (...)`
# MAGIC - Filter window results with `QUALIFY`
# MAGIC - Write the same Top-N logic with a subquery
# MAGIC - Calculate a running total with windowed `SUM`
# MAGIC - Access the previous row with `LAG`
# MAGIC - Derive a day-over-day change from the current and previous values
# MAGIC
# MAGIC **Callbacks:** Module 8 `05 - Window Functions Fundamentals` introduced
# MAGIC ranking windows, and `06 - Running Totals and Lag and Lead` covered running
# MAGIC totals and `LAG`. Here we apply those patterns with Spark SQL.
# MAGIC
# MAGIC **Reads:**
# MAGIC
# MAGIC - `rideshare_dev.processed.kpi_zone_performance` — **20 rows**
# MAGIC - `rideshare_dev.processed.kpi_daily_trip_summary` — **14 rows**
# MAGIC
# MAGIC **Writes:** None.
# MAGIC
# MAGIC **Prerequisites:** Module 9 `03 - SQL Pivot, Unpivot, and Sampling`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup — load the KPI tables
# MAGIC
# MAGIC This notebook uses two KPI tables created in Module 8.
# MAGIC
# MAGIC The `kpi_zone_performance` table contains one row for each combination of
# MAGIC `pickup_borough` and `pickup_zone` (**20** rows). Each row includes
# MAGIC aggregated zone metrics such as `total_tip` and `trip_count`. We will
# MAGIC compare zones within the same borough and rank them from highest to
# MAGIC lowest based on these metrics.
# MAGIC
# MAGIC Example shape (toy):
# MAGIC
# MAGIC | pickup_borough | pickup_zone | total_tip | trip_count |
# MAGIC |---|---|---:|---:|
# MAGIC | Bronx | Zone A | 50 | 8 |
# MAGIC | Bronx | Zone B | 30 | 5 |
# MAGIC
# MAGIC The `kpi_daily_trip_summary` table contains one row for each `trip_date`
# MAGIC (**14** rows). Each row includes `total_distance_miles` for that day. We
# MAGIC will order these daily records by date to calculate the running distance,
# MAGIC bring in the previous day's distance with `LAG`, and measure the
# MAGIC day-over-day change.
# MAGIC
# MAGIC Example shape (toy):
# MAGIC
# MAGIC | trip_date | total_distance_miles |
# MAGIC |---|---:|
# MAGIC | day 1 | 20 |
# MAGIC | day 2 | 10 |
# MAGIC | day 3 | 15 |

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
# MAGIC ## Part 1 — Rank zones within each borough
# MAGIC
# MAGIC ### 1. Assign a row number within each borough
# MAGIC
# MAGIC Within each borough, `ROW_NUMBER()` ranks zones by `total_tip` DESC.
# MAGIC
# MAGIC Example shape (toy — not the full result):
# MAGIC
# MAGIC | pickup_borough | pickup_zone | total_tip | rn |
# MAGIC |---|---|---:|---:|
# MAGIC | Bronx | Zone A | 50 | 1 |
# MAGIC | Bronx | Zone B | 30 | 2 |
# MAGIC | Bronx | Zone C | 10 | 3 |
# MAGIC
# MAGIC `PARTITION BY pickup_borough` restarts `rn` per borough. The `ORDER BY`
# MAGIC inside `OVER(...)` drives the ranking — not the final display sort.
# MAGIC
# MAGIC **Expected:** **20 rows**.

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
# MAGIC ### 2. Keep the Top 2 zones with `QUALIFY`
# MAGIC
# MAGIC `QUALIFY ... <= 2` keeps only `rn` 1 and 2 within each borough.
# MAGIC
# MAGIC Example shape (toy — after `QUALIFY`):
# MAGIC
# MAGIC | pickup_borough | pickup_zone | total_tip | rn |
# MAGIC |---|---|---:|---:|
# MAGIC | Bronx | Zone A | 50 | 1 |
# MAGIC | Bronx | Zone B | 30 | 2 |
# MAGIC
# MAGIC Zone C (`rn` 3) is gone — no outer subquery needed.
# MAGIC
# MAGIC **Expected:** **9 rows** (Staten Island has only one zone).

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
# MAGIC ### 3. Write the same Top-N logic with a subquery
# MAGIC
# MAGIC Same Top-N: inner query builds `rn`, outer query uses `WHERE rn <= 2`.
# MAGIC
# MAGIC | form | filter |
# MAGIC |---|---|
# MAGIC | `QUALIFY` | in the same query |
# MAGIC | subquery | `WHERE rn <= 2` outside |
# MAGIC
# MAGIC Use the subquery form when `QUALIFY` is unavailable or you need to reuse
# MAGIC the ranked rows in more logic.
# MAGIC
# MAGIC **Expected:** same **9 rows**.

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
# MAGIC ## Part 2 — Track distance across days
# MAGIC
# MAGIC ### 4. Calculate a running distance total
# MAGIC
# MAGIC Order by `trip_date` and accumulate `total_distance_miles`.
# MAGIC
# MAGIC Example shape (toy):
# MAGIC
# MAGIC | trip_date | total_distance_miles | running_distance |
# MAGIC |---|---:|---:|
# MAGIC | day 1 | 20 | 20 |
# MAGIC | day 2 | 10 | 30 |
# MAGIC | day 3 | 5 | 35 |
# MAGIC
# MAGIC Frame: `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`.
# MAGIC
# MAGIC **Expected:** **14 rows**; running distance
# MAGIC **21.35 → 113.34 → … → 793.20**.

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
# MAGIC ### 5. Compare each day with the previous day
# MAGIC
# MAGIC `LAG` pulls the previous day's miles; `delta = current − previous`.
# MAGIC
# MAGIC Example shape (toy):
# MAGIC
# MAGIC | trip_date | total_distance_miles | prev_day | delta |
# MAGIC |---|---:|---:|---:|
# MAGIC | day 1 | 20 | NULL | NULL |
# MAGIC | day 2 | 10 | 20 | −10 |
# MAGIC | day 3 | 15 | 10 | +5 |
# MAGIC
# MAGIC Day 1 has no previous row, so `prev_day` and `delta` are NULL.
# MAGIC
# MAGIC **Expected:** `delta` begins with NULL, then
# MAGIC **+70.64, −61.99, +25.52, ...**

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
# MAGIC ### 6. Turn the daily change into a direction
# MAGIC
# MAGIC Map `delta` to a label:
# MAGIC
# MAGIC | `delta` | `direction` |
# MAGIC |---|---|
# MAGIC | NULL | `n/a` |
# MAGIC | greater than 0 | `up` |
# MAGIC | less than 0 | `down` |
# MAGIC | equal to 0 | `flat` |
# MAGIC
# MAGIC Check NULL first so day 1 is `n/a`, not `flat`. The inner query builds
# MAGIC `delta`; the outer query applies `CASE`.

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
# MAGIC Top 2 zones per borough by **`trip_count`**, only zones with
# MAGIC `trip_count >= 3`.
# MAGIC
# MAGIC | clause | job |
# MAGIC |---|---|
# MAGIC | `WHERE` | drop zones with `trip_count < 3` |
# MAGIC | `QUALIFY` | keep `rn` 1 and 2 within each borough |
# MAGIC
# MAGIC Rank with:
# MAGIC
# MAGIC `ROW_NUMBER() OVER (PARTITION BY pickup_borough ORDER BY trip_count DESC)`
# MAGIC
# MAGIC **Expected:** **8 rows** (Staten Island removed by `WHERE`).

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
# MAGIC | topic | pattern |
# MAGIC |---|---|
# MAGIC | Rank within borough | `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)` |
# MAGIC | Top-N in place | `QUALIFY ... <= N` |
# MAGIC | Top-N portable | subquery + `WHERE rn <= N` |
# MAGIC | Running total | windowed `SUM` + `ROWS` frame |
# MAGIC | Day-over-day | `LAG` → `delta` → `CASE` direction |
# MAGIC
# MAGIC **Next:** `05 - CTEs and Parameterized SQL` — named query steps and safe
# MAGIC SQL parameters.
