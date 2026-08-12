# Databricks notebook source
# MAGIC %md
# MAGIC # 05 - CTEs and Parameterized SQL
# MAGIC
# MAGIC Build an auditable tip-share pipeline with named SQL steps, then bind
# MAGIC values safely with `:params` instead of string-building SQL.
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC - Name multi-step SQL with CTEs instead of nested subqueries
# MAGIC - Parameterize safely with named `:params` (not f-string SQL)
# MAGIC - Combine CTEs and parameters for a filtered daily tip-share query
# MAGIC
# MAGIC **Reads:** `rideshare_dev.processed.trip_enriched` (106). **No writes.**
# MAGIC
# MAGIC **Prerequisites:** Module 9 `04 - SQL Windows and QUALIFY`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup — load `trip_enriched`
# MAGIC
# MAGIC Columns used here: `pickup_borough`, `tip_amount`, `trip_date`.

# COMMAND ----------

trip_enriched = spark.table("rideshare_dev.processed.trip_enriched")  # noqa: F821

print(f"trip_enriched: {trip_enriched.count()} rows")  # expect 106

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Single CTE
# MAGIC
# MAGIC A CTE (`WITH name AS (...)`) is a **named intermediate** you can select from.
# MAGIC Prefer it when the next reader should see the steps, not a nested blob.
# MAGIC
# MAGIC **Expected:** **5** borough rows.

# COMMAND ----------

# MAGIC %sql
# MAGIC WITH borough_tips AS (
# MAGIC   SELECT
# MAGIC     pickup_borough,
# MAGIC     SUM(tip_amount) AS total_tip
# MAGIC   FROM rideshare_dev.processed.trip_enriched
# MAGIC   GROUP BY pickup_borough
# MAGIC )
# MAGIC SELECT *
# MAGIC FROM borough_tips
# MAGIC ORDER BY pickup_borough

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Multi-CTE composition
# MAGIC
# MAGIC Add a fleet-wide total CTE, then join the intermediates for each borough's
# MAGIC tip share percent.
# MAGIC
# MAGIC **Expected:** **5** rows with `tip_share_pct`.

# COMMAND ----------

# MAGIC %sql
# MAGIC WITH borough_tips AS (
# MAGIC   SELECT
# MAGIC     pickup_borough,
# MAGIC     SUM(tip_amount) AS total_tip
# MAGIC   FROM rideshare_dev.processed.trip_enriched
# MAGIC   GROUP BY pickup_borough
# MAGIC ),
# MAGIC fleet_total AS (
# MAGIC   SELECT SUM(tip_amount) AS fleet_tip
# MAGIC   FROM rideshare_dev.processed.trip_enriched
# MAGIC )
# MAGIC SELECT
# MAGIC   b.pickup_borough,
# MAGIC   b.total_tip,
# MAGIC   f.fleet_tip,
# MAGIC   ROUND(100 * b.total_tip / NULLIF(f.fleet_tip, 0), 1) AS tip_share_pct
# MAGIC FROM borough_tips AS b
# MAGIC CROSS JOIN fleet_total AS f
# MAGIC ORDER BY b.pickup_borough

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Nested subquery contrast
# MAGIC
# MAGIC Same share logic as nested subqueries — intentionally harder to read.
# MAGIC Same **5** rows. CTEs win on auditability, not on a different answer.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   b.pickup_borough,
# MAGIC   b.total_tip,
# MAGIC   f.fleet_tip,
# MAGIC   ROUND(100 * b.total_tip / NULLIF(f.fleet_tip, 0), 1) AS tip_share_pct
# MAGIC FROM (
# MAGIC   SELECT
# MAGIC     pickup_borough,
# MAGIC     SUM(tip_amount) AS total_tip
# MAGIC   FROM rideshare_dev.processed.trip_enriched
# MAGIC   GROUP BY pickup_borough
# MAGIC ) AS b
# MAGIC CROSS JOIN (
# MAGIC   SELECT SUM(tip_amount) AS fleet_tip
# MAGIC   FROM rideshare_dev.processed.trip_enriched
# MAGIC ) AS f
# MAGIC ORDER BY b.pickup_borough

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Named parameters
# MAGIC
# MAGIC Bind literals with `:borough` and `spark.sql(..., args={...})`. The SQL text
# MAGIC stays fixed; only the args dict changes.
# MAGIC
# MAGIC **Anti-pattern:** building SQL with an f-string
# MAGIC (`f"... WHERE pickup_borough = '{borough}'"`) — that invites injection and
# MAGIC makes every borough a different query string. Prefer `:params`.

# COMMAND ----------

borough_sql = """
SELECT
  pickup_borough,
  COUNT(*) AS trip_count,
  ROUND(SUM(tip_amount), 2) AS total_tip
FROM rideshare_dev.processed.trip_enriched
WHERE pickup_borough = :borough
GROUP BY pickup_borough
"""

manhattan = spark.sql(borough_sql, args={"borough": "Manhattan"})  # noqa: F821
manhattan.show()

# COMMAND ----------

queens = spark.sql(borough_sql, args={"borough": "Queens"})  # noqa: F821
queens.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. CTE + params combined
# MAGIC
# MAGIC Daily grain: for a borough, each dated day's tip as a share of **that day's
# MAGIC fleet tip**. Parameters: `:borough`, `:min_tip`. Drop NULL dates
# MAGIC (`WHERE trip_date IS NOT NULL`) — trips **101–106**.
# MAGIC
# MAGIC **Expected:** **14** dated rows for Manhattan with `:min_tip = 0`. Share can
# MAGIC hit **100%** when every tip that day is in the borough.

# COMMAND ----------

daily_share_sql = """
WITH borough_daily AS (
  SELECT
    trip_date,
    SUM(tip_amount) AS borough_tip
  FROM rideshare_dev.processed.trip_enriched
  WHERE pickup_borough = :borough
    AND trip_date IS NOT NULL
    AND COALESCE(tip_amount, 0) >= :min_tip
  GROUP BY trip_date
),
fleet_daily AS (
  SELECT
    trip_date,
    SUM(tip_amount) AS fleet_tip
  FROM rideshare_dev.processed.trip_enriched
  WHERE trip_date IS NOT NULL
    AND COALESCE(tip_amount, 0) >= :min_tip
  GROUP BY trip_date
)
SELECT
  f.trip_date,
  b.borough_tip,
  f.fleet_tip,
  ROUND(100 * b.borough_tip / NULLIF(f.fleet_tip, 0), 1) AS tip_share_pct
FROM fleet_daily AS f
LEFT JOIN borough_daily AS b
  ON f.trip_date = b.trip_date
ORDER BY f.trip_date
"""

manhattan_daily = spark.sql(  # noqa: F821
    daily_share_sql,
    args={"borough": "Manhattan", "min_tip": 0},
)
print(f"manhattan_daily: {manhattan_daily.count()} rows")  # expect 14
manhattan_daily.show(14, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC For a `:borough` you choose, return that borough's **daily tip as a share of
# MAGIC fleet daily tip** (dated days only). Use CTEs + `spark.sql` + `args`.
# MAGIC
# MAGIC Some dates may show **100%** (for example Manhattan on **2026-03-01**) —
# MAGIC correct when all fleet tips that day are in the borough.
# MAGIC
# MAGIC **Expected:** **14** dated rows for the borough you pick.

# COMMAND ----------

# Write a parameterized CTE query: borough daily tip / fleet daily tip.
# Use spark.sql(..., args={"borough": "<your borough>", "min_tip": 0})
# TODO: result = spark.sql("""...""", args={...})  # noqa: F821
# TODO: print count (expect 14) and result.show(14, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - CTEs name intermediates; nested subqueries compute the same thing less
# MAGIC   clearly
# MAGIC - `:params` + `args={...}` keep SQL text stable and avoid f-string SQL
# MAGIC - Combine both for reusable, filterable multi-step pipelines
# MAGIC
# MAGIC **Next:** `06 - End-to-End SQL Pipeline and Parity Inspection` — rebuild
# MAGIC Module 8 KPIs in SQL and inspect parity (no asserts).
