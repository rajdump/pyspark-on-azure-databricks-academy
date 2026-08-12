# Databricks notebook source
# MAGIC %md
# MAGIC # 04 - SQL Windows and QUALIFY
# MAGIC
# MAGIC Window functions let us calculate across related rows while keeping each
# MAGIC row in the result.
# MAGIC
# MAGIC In this notebook, we'll use them for two practical questions:
# MAGIC
# MAGIC 1. Which zones rank highest within each borough?
# MAGIC 2. How does total trip distance change from one day to the next?
# MAGIC
# MAGIC We'll also use `QUALIFY` to filter window results directly in SQL.
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
# MAGIC We'll use two KPI tables from Module 8.
# MAGIC
# MAGIC `kpi_zone_performance` contains zone-level metrics such as:
# MAGIC
# MAGIC - `pickup_borough`
# MAGIC - `pickup_zone`
# MAGIC - `total_tip`
# MAGIC - `trip_count`
# MAGIC
# MAGIC `kpi_daily_trip_summary` contains one row per day, including
# MAGIC `total_distance_miles`.
# MAGIC
# MAGIC The first table supports **ranking within each borough**. The second supports
# MAGIC **calculations across dates**.

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
# MAGIC Our first question is:
# MAGIC
# MAGIC **Which zones generate the most tip within each borough?**
# MAGIC
# MAGIC Use `ROW_NUMBER()` with a window:
# MAGIC
# MAGIC ```text
# MAGIC ROW_NUMBER() OVER (
# MAGIC   PARTITION BY ...
# MAGIC   ORDER BY ...
# MAGIC )
# MAGIC ```
# MAGIC
# MAGIC For this query:
# MAGIC
# MAGIC - `PARTITION BY pickup_borough` restarts the numbering for each borough
# MAGIC - `ORDER BY total_tip DESC` gives the highest-tip zone row number `1`
# MAGIC
# MAGIC The `ORDER BY` inside `OVER(...)` controls the **window calculation**.
# MAGIC It does not guarantee the final display order, so the query uses a separate
# MAGIC `ORDER BY` at the end.
# MAGIC
# MAGIC **Expected:** **20 rows**. Each borough gets its own sequence of row numbers.

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
# MAGIC The previous query calculates a row number for every zone.
# MAGIC
# MAGIC Now we only want the **Top 2 zones in each borough**.
# MAGIC
# MAGIC `QUALIFY` filters rows using the result of a window function, so we can apply
# MAGIC the Top-N condition in the same query without adding an outer subquery.
# MAGIC
# MAGIC Here:
# MAGIC
# MAGIC `ROW_NUMBER() ... <= 2`
# MAGIC
# MAGIC keeps row numbers `1` and `2` within each borough.
# MAGIC
# MAGIC **Expected:** **9 rows**.
# MAGIC
# MAGIC Four boroughs contribute two zones each, while Staten Island has only one
# MAGIC zone.

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
# MAGIC `QUALIFY` gives us a concise way to filter a window result, but the same
# MAGIC logic can be written with a subquery.
# MAGIC
# MAGIC The inner query calculates:
# MAGIC
# MAGIC `ROW_NUMBER() ... AS rn`
# MAGIC
# MAGIC The outer query can then use:
# MAGIC
# MAGIC `WHERE rn <= 2`
# MAGIC
# MAGIC Both queries answer the same question and should return the same **9 rows**.
# MAGIC
# MAGIC The subquery pattern is useful when `QUALIFY` is unavailable or when the
# MAGIC window result needs to be reused by additional logic.

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
# MAGIC The zone example partitioned rows by borough.
# MAGIC
# MAGIC For the next calculations, we'll work across the daily KPI table in
# MAGIC `trip_date` order.
# MAGIC
# MAGIC ### 4. Calculate a running distance total
# MAGIC
# MAGIC A running total answers:
# MAGIC
# MAGIC **How much distance have we accumulated up to each day?**
# MAGIC
# MAGIC Order the rows by `trip_date` and calculate:
# MAGIC
# MAGIC ```text
# MAGIC SUM(total_distance_miles) OVER (...)
# MAGIC ```
# MAGIC
# MAGIC The explicit frame:
# MAGIC
# MAGIC ```text
# MAGIC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
# MAGIC ```
# MAGIC
# MAGIC means: start from the first ordered row and include every row through the
# MAGIC current day.
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
# MAGIC A running total tells us how distance accumulates.
# MAGIC
# MAGIC Now ask a different question:
# MAGIC
# MAGIC **Did total distance increase or decrease compared with the previous day?**
# MAGIC
# MAGIC `LAG(total_distance_miles, 1)` returns the value from the previous row in
# MAGIC `trip_date` order.
# MAGIC
# MAGIC We can then calculate:
# MAGIC
# MAGIC `current distance - previous distance`
# MAGIC
# MAGIC as `delta`.
# MAGIC
# MAGIC The first day has no previous row, so both `prev_day` and `delta` are NULL.
# MAGIC
# MAGIC **Expected:** `delta` begins with NULL, followed by values such as
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
# MAGIC The numeric `delta` tells us how much the distance changed.
# MAGIC
# MAGIC Now convert that value into a simple label:
# MAGIC
# MAGIC | `delta` | `direction` |
# MAGIC |---|---|
# MAGIC | NULL | `n/a` |
# MAGIC | greater than 0 | `up` |
# MAGIC | less than 0 | `down` |
# MAGIC | equal to 0 | `flat` |
# MAGIC
# MAGIC Check NULL first because the first date has no previous day. Calling that
# MAGIC row `flat` would incorrectly imply that a comparison was available.
# MAGIC
# MAGIC The inner query calculates `delta`; the outer query then uses that result
# MAGIC inside `CASE`.

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
# MAGIC Return the **Top 2 zones in each borough by `trip_count`**, but only consider
# MAGIC zones with at least **3 trips**.
# MAGIC
# MAGIC Use both filters in the correct place:
# MAGIC
# MAGIC - `WHERE` to remove zones with `trip_count < 3`
# MAGIC - `QUALIFY` to keep row numbers `1` and `2` within each borough
# MAGIC
# MAGIC Rank with:
# MAGIC
# MAGIC `ROW_NUMBER() OVER (PARTITION BY pickup_borough ORDER BY trip_count DESC)`
# MAGIC
# MAGIC **Expected:** **8 rows**.
# MAGIC
# MAGIC Staten Island is removed by the `WHERE` condition before the ranking is
# MAGIC filtered.

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
# MAGIC This notebook used SQL window functions for two different types of analysis.
# MAGIC
# MAGIC ### Ranking within groups
# MAGIC
# MAGIC - `PARTITION BY` creates a separate window for each borough
# MAGIC - `ORDER BY` inside `OVER(...)` determines the ranking order
# MAGIC - `ROW_NUMBER()` assigns a position within each borough
# MAGIC - `QUALIFY` filters those window results directly
# MAGIC - A subquery with `WHERE` can express the same Top-N pattern
# MAGIC
# MAGIC ### Calculations across time
# MAGIC
# MAGIC - Windowed `SUM` builds a running distance total
# MAGIC - `LAG` brings the previous day's value onto the current row
# MAGIC - Subtracting the previous value produces the day-over-day `delta`
# MAGIC - `CASE` converts that numeric change into `up`, `down`, `flat`, or `n/a`
# MAGIC
# MAGIC **Next:** `05 - CTEs and Parameterized SQL` introduces named query steps
# MAGIC and safe SQL parameters.
