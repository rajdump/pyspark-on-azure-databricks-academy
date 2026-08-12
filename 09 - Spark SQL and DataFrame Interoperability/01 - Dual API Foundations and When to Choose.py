# Databricks notebook source
# MAGIC %md
# MAGIC # 01 - Dual API Foundations and When to Choose
# MAGIC
# MAGIC Module 9 re-expresses analytics you already built in PySpark — this time in
# MAGIC Spark SQL — and shows when each API entry point fits.
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC - Query a Unity Catalog table with `%sql` and with `spark.table`
# MAGIC - Bridge SQL → DataFrame (`spark.sql`) and DataFrame → SQL (temp view)
# MAGIC - Apply row-level `CASE WHEN` for absolute `tip_amount_band`
# MAGIC - Choose among `%sql`, `spark.table`, `spark.sql`→DF, and DF→temp view
# MAGIC
# MAGIC **Callback:** Module 2 `06 - Querying DataFrames with SQL` already covered
# MAGIC temp views, `%sql`, and `spark.sql`. This notebook adds UC table paths and
# MAGIC a when-to-choose habit.
# MAGIC
# MAGIC **Reads:** `rideshare_dev.processed.trip_enriched` (106). **No writes.**
# MAGIC Aggregations start in `02 - SQL Joins, Aggregations, and Filtering`.
# MAGIC
# MAGIC **Prerequisites:** Module 7–8 managed tables; Module 2 SQL intro.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup — load `trip_enriched`
# MAGIC
# MAGIC Module 7 managed table: one row per `trip_id`, **106** rows.

# COMMAND ----------

from pyspark.sql import functions as F

trip_enriched = spark.table("rideshare_dev.processed.trip_enriched")  # noqa: F821

print(f"trip_enriched: {trip_enriched.count()} rows")  # expect 106

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Direct SQL on a UC table
# MAGIC
# MAGIC Glance at tip and borough for a few trips. `%sql` can name
# MAGIC `rideshare_dev.processed.trip_enriched` directly — no temp view.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT trip_id, service_type, tip_amount, pickup_borough
# MAGIC FROM rideshare_dev.processed.trip_enriched
# MAGIC LIMIT 5

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW TABLES IN rideshare_dev.processed

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE TABLE rideshare_dev.processed.trip_enriched

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Same projection via DataFrame API
# MAGIC
# MAGIC Same table via the Setup DataFrame: `.select` → `.limit`.

# COMMAND ----------

trip_enriched.select(
    "trip_id",
    "service_type",
    "tip_amount",
    "pickup_borough",
).limit(5).show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. SQL → DataFrame bridge
# MAGIC
# MAGIC `spark.sql(...)` returns a DataFrame.
# MAGIC
# MAGIC `WHERE tip_amount IS NOT NULL` → **104** rows.

# COMMAND ----------

known_tips = spark.sql(  # noqa: F821
    """
    SELECT trip_id, tip_amount, pickup_borough
    FROM rideshare_dev.processed.trip_enriched
    WHERE tip_amount IS NOT NULL
    """
)

print(f"known_tips: {known_tips.count()} rows")  # expect 104
known_tips.limit(5).show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Row-level `CASE WHEN` (absolute tip bands)
# MAGIC
# MAGIC Add `tip_amount_band` with `CASE WHEN` — still **106** rows. Absolute
# MAGIC dollar bands (≠ Module 6 percent `tip_band`):
# MAGIC
# MAGIC | Condition | Band |
# MAGIC |---|---|
# MAGIC | `tip_amount` IS NULL | `no_data` |
# MAGIC | `= 0` | `zero` |
# MAGIC | `<= 3` | `low` |
# MAGIC | `<= 6` | `medium` |
# MAGIC | else | `high` |
# MAGIC
# MAGIC Expected: **zero 26 / low 40 / medium 20 / high 18 / no_data 2**.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   trip_id,
# MAGIC   tip_amount,
# MAGIC   CASE
# MAGIC     WHEN tip_amount IS NULL THEN 'no_data'
# MAGIC     WHEN tip_amount = 0 THEN 'zero'
# MAGIC     WHEN tip_amount <= 3 THEN 'low'
# MAGIC     WHEN tip_amount <= 6 THEN 'medium'
# MAGIC     ELSE 'high'
# MAGIC   END AS tip_amount_band
# MAGIC FROM rideshare_dev.processed.trip_enriched
# MAGIC ORDER BY tip_amount_band, trip_id

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. DataFrame → SQL bridge
# MAGIC
# MAGIC Register a computed DataFrame with `createOrReplaceTempView` so `%sql` can
# MAGIC use a name (Module 2 — `%sql` resolves names, not Python variables).

# COMMAND ----------

trip_tip_band = trip_enriched.withColumn(
    "tip_amount_band",
    F.when(F.col("tip_amount").isNull(), "no_data")
    .when(F.col("tip_amount") == 0, "zero")
    .when(F.col("tip_amount") <= 3, "low")
    .when(F.col("tip_amount") <= 6, "medium")
    .otherwise("high"),
)

trip_tip_band.createOrReplaceTempView("trip_tip_band")
print("Temp view registered: trip_tip_band")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT trip_id, tip_amount, tip_amount_band
# MAGIC FROM trip_tip_band
# MAGIC LIMIT 20

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. When to choose
# MAGIC
# MAGIC | Entry point | Use when |
# MAGIC |---|---|
# MAGIC | Direct `%sql` on a UC table | Whole cell is SQL; table already has a catalog name |
# MAGIC | `spark.table` → DataFrame API | PySpark transforms / reuse a loaded DF |
# MAGIC | `spark.sql(...)` → DataFrame | Filter or project in SQL, then continue in Python |
# MAGIC | DF → `createOrReplaceTempView` | Computed columns in PySpark need a SQL name |
# MAGIC
# MAGIC Pick one entry point per cell and stay consistent inside that cell.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Return Manhattan trips with a known tip, labeled with `tip_amount_band`.
# MAGIC
# MAGIC Requirements:
# MAGIC
# MAGIC - `WHERE pickup_borough = 'Manhattan'` and `tip_amount IS NOT NULL`
# MAGIC - Same absolute `CASE` bands as Section 4
# MAGIC - SQL only — no PySpark rewrite
# MAGIC - One SQL comment: which entry point you would choose and why
# MAGIC
# MAGIC **Expected:** **43** rows.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- I chose ... because ...
# MAGIC SELECT
# MAGIC   trip_id,
# MAGIC   tip_amount,
# MAGIC   CASE
# MAGIC     WHEN tip_amount IS NULL THEN 'no_data'
# MAGIC     -- TODO: finish absolute tip_amount_band CASE (same bands as Section 4)
# MAGIC     ELSE 'TODO'
# MAGIC   END AS tip_amount_band
# MAGIC FROM rideshare_dev.processed.trip_enriched
# MAGIC WHERE 1 = 0  -- TODO: replace with Manhattan + tip_amount IS NOT NULL
# MAGIC -- Expected: 43 rows

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - Four entry points: `%sql`, `spark.table`, `spark.sql`→DF, DF→temp view
# MAGIC - Row-level `CASE WHEN` → `tip_amount_band` (106 rows; absolute ≠ Module 6 `tip_band`)
# MAGIC
# MAGIC **Next:** `02 - SQL Joins, Aggregations, and Filtering` — JOIN aliases,
# MAGIC first Module 9 `GROUP BY`, `HAVING`.
