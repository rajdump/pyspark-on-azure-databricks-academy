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
# MAGIC ## Module 9 preview
# MAGIC
# MAGIC | # | Notebook | Focus |
# MAGIC |---|---|---|
# MAGIC | 01 | Dual API Foundations and When to Choose | Bridges + row-level `CASE` |
# MAGIC | 02 | SQL Joins, Aggregations, and Filtering | JOIN, `GROUP BY`, `HAVING` |
# MAGIC | 03 | SQL Pivot, Unpivot, and Sampling | Reshape + `TABLESAMPLE` |
# MAGIC | 04 | SQL Windows and QUALIFY | Ranking, running totals, `LAG` |
# MAGIC | 05 | CTEs and Parameterized SQL | Named steps + `:params` |
# MAGIC | 06 | End-to-End SQL Pipeline and Parity Inspection | Rebuild KPIs; inspect diffs |
# MAGIC
# MAGIC **Callback:** Module 2 `06 - Querying DataFrames with SQL` already covered
# MAGIC temp views, `%sql`, and `spark.sql`. This notebook adds UC table paths and
# MAGIC a when-to-choose habit.
# MAGIC
# MAGIC **Reads:** `rideshare_dev.processed.trip_enriched` (106). **No writes.**
# MAGIC **No `GROUP BY` / `.groupBy()`** — first Module 9 aggregation is
# MAGIC `02 - SQL Joins, Aggregations, and Filtering`.
# MAGIC
# MAGIC **Prerequisites:** Module 7–8 managed tables; Module 2 SQL intro.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup — load `trip_enriched`
# MAGIC
# MAGIC Module 7 wrote this managed table: **one row per `trip_id`**, **106** rows.
# MAGIC Confirm the count before querying.

# COMMAND ----------

from pyspark.sql import functions as F

trip_enriched = spark.table("rideshare_dev.processed.trip_enriched")  # noqa: F821

print(f"trip_enriched: {trip_enriched.count()} rows")  # expect 106

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Direct SQL on a UC table
# MAGIC
# MAGIC Business question: glance at tip and borough for a few trips — without
# MAGIC registering a temp view first.
# MAGIC
# MAGIC SQL can name the Unity Catalog table directly:
# MAGIC `rideshare_dev.processed.trip_enriched`.

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
# MAGIC Same physical table, second entry point: the DataFrame already loaded in
# MAGIC Setup → `.select` → `.limit`. Two APIs, one source.

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
# MAGIC `spark.sql(...)` runs SQL and returns a **DataFrame** — continue in Python
# MAGIC without rewriting the filter.
# MAGIC
# MAGIC `WHERE tip_amount IS NOT NULL` keeps rows that have a tip value (**104** of
# MAGIC 106 if you count). Still row grain — **no aggregation**.

# COMMAND ----------

known_tips = spark.sql(  # noqa: F821
    """
    SELECT trip_id, tip_amount, pickup_borough
    FROM rideshare_dev.processed.trip_enriched
    WHERE tip_amount IS NOT NULL
    """
)

print(f"known_tips: {known_tips.count()} rows")  # expect 104
known_tips.select("trip_id", "tip_amount", "pickup_borough").limit(5).show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Row-level `CASE WHEN` (absolute tip bands)
# MAGIC
# MAGIC `CASE WHEN` here is a **row transform** — each trip gets a label; the row
# MAGIC count stays **106**. This is not grouping.
# MAGIC
# MAGIC Column: `tip_amount_band`. These are **absolute dollar bands**, not the
# MAGIC Module 6 percent-of-base `tip_band`.
# MAGIC
# MAGIC | Condition | Band |
# MAGIC |---|---|
# MAGIC | `tip_amount` IS NULL | `no_data` |
# MAGIC | `= 0` | `zero` |
# MAGIC | `<= 3` | `low` |
# MAGIC | `<= 6` | `medium` |
# MAGIC | else | `high` |
# MAGIC
# MAGIC Validated distribution (stated here so we do not need `GROUP BY` yet):
# MAGIC **zero 26 / low 40 / medium 20 / high 18 / no_data 2**.

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
# MAGIC When a computed DataFrame needs a SQL name, register it with
# MAGIC `createOrReplaceTempView` (Module 2 callback — `%sql` resolves names, not
# MAGIC Python variables).

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
# MAGIC The cells above already proved each path. Use this table when you start a
# MAGIC new cell:
# MAGIC
# MAGIC | Entry point | Use when |
# MAGIC |---|---|
# MAGIC | Direct `%sql` on a UC table | Whole cell is SQL; table already has a catalog name |
# MAGIC | `spark.table` → DataFrame API | You want PySpark transforms / reuse a loaded DF |
# MAGIC | `spark.sql(...)` → DataFrame | Filter or project in SQL, then continue in Python |
# MAGIC | DF → `createOrReplaceTempView` | You computed columns in PySpark and need a SQL name |
# MAGIC
# MAGIC Pick one entry point per cell and stay consistent inside that cell.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Return Manhattan trips that have a known tip, labeled with
# MAGIC `tip_amount_band`.
# MAGIC
# MAGIC Requirements:
# MAGIC
# MAGIC - `WHERE pickup_borough = 'Manhattan'` and `tip_amount IS NOT NULL`
# MAGIC - Same absolute `CASE` bands as Section 4
# MAGIC - SQL only — no PySpark rewrite
# MAGIC
# MAGIC Also add a one-line SQL comment stating which entry point you would choose
# MAGIC for this query and why (1–2 sentences).
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
# MAGIC - `CASE WHEN` at row grain labels every trip (`tip_amount_band`); count stays 106
# MAGIC - Absolute dollar bands ≠ Module 6 percent `tip_band`
# MAGIC
# MAGIC **Next:** `02 - SQL Joins, Aggregations, and Filtering` — first Module 9
# MAGIC `GROUP BY`, JOIN with aliases, and `HAVING`.
