# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC
# MAGIC # 04 - Delta Time Travel and Restore
# MAGIC
# MAGIC A Delta table can change over time, creating multiple versions of the
# MAGIC same table. This raises two important questions:
# MAGIC
# MAGIC - How can you inspect what the table looked like at an earlier point?
# MAGIC - How can you make a previous table state the current state again?
# MAGIC
# MAGIC In `02 - Understanding the Delta Transaction Log`, you learned how Delta
# MAGIC records table changes and creates new versions. This notebook builds on
# MAGIC that foundation to explore how those versions can be queried and restored.
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC By the end of this notebook, you will be able to:
# MAGIC
# MAGIC - Inspect Delta table history
# MAGIC - Query an earlier table state by version
# MAGIC - Query an earlier table state by timestamp
# MAGIC - Read a historical version using PySpark
# MAGIC - Restore an earlier table state
# MAGIC - Understand how retention limits access to historical versions
# MAGIC
# MAGIC **Reads:** None of the 100-row source files or teaching tables
# MAGIC (`trip_enriched`, KPIs, or `curated/`)
# MAGIC
# MAGIC **Writes:**
# MAGIC
# MAGIC - `rideshare_dev.processed.fare_timetravel_lab`
# MAGIC
# MAGIC **Prerequisites:**
# MAGIC
# MAGIC - Module 9 notebooks `01`–`06`
# MAGIC - Module 5 `01 - Unity Catalog Volumes and Data Landing.py`
# MAGIC   (catalog and `processed` schema)
# MAGIC
# MAGIC **Scope note:** This notebook focuses on table history, time travel,
# MAGIC `RESTORE`, and retention. It does not run `VACUUM`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup — create the lab table
# MAGIC We use a managed Delta table to keep the lesson focused on table versions, time travel, and `RESTORE`.

# COMMAND ----------

from decimal import Decimal

lab_table = "rideshare_dev.processed.fare_timetravel_lab"

# Small source dataset used to create a controlled Delta history
trips_extract = spark.createDataFrame(
    [
        (1001, "STANDARD", "card", Decimal("20.00"), Decimal("3.00")),
        (1002, "SHARED", "cash", Decimal("15.00"), Decimal("0.00")),
        (1003, "PREMIUM", "card", Decimal("40.00"), Decimal("6.00")),
        (1004, "STANDARD", "wallet", Decimal("25.00"), Decimal("2.50")),
    ],
    "trip_id LONG, service_type STRING, payment_method STRING, "
    "base_fare_amount DECIMAL(10, 2), tip_amount DECIMAL(10, 2)",
)
# SQL statements below read from this temporary view
trips_extract.createOrReplaceTempView("trips_extract")

# Recreate the lab table so every run starts with a clean history
spark.sql(f"DROP TABLE IF EXISTS {lab_table}")
spark.sql(
    f"""
    CREATE TABLE {lab_table} (
      trip_id BIGINT,
      service_type STRING,
      payment_method STRING,
      base_fare_amount DECIMAL(10, 2),
      tip_amount DECIMAL(10, 2)
    )
    USING DELTA
    """
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Build table history
# MAGIC We will intentionally create five table versions to build a history that we can explore.

# COMMAND ----------

# First data version: trips 1001–1003
spark.sql(
    f"""
    INSERT INTO {lab_table}
    SELECT * FROM trips_extract
    WHERE trip_id <= 1003
    """
)
display(spark.table(lab_table).orderBy("trip_id"))

# COMMAND ----------

# Add trip 1004 — table state immediately before the update
spark.sql(
    f"""
    INSERT INTO {lab_table}
    SELECT * FROM trips_extract
    WHERE trip_id = 1004
    """
)
display(spark.table(lab_table).orderBy("trip_id"))

# COMMAND ----------

# Correct the tip for trip 1003
spark.sql(
    f"""
    UPDATE {lab_table}
    SET tip_amount = 10.00
    WHERE trip_id = 1003
    """
)
display(spark.table(lab_table).orderBy("trip_id"))

# COMMAND ----------

# Simulate an accidental delete of trip 1002
spark.sql(
    f"""
    DELETE FROM {lab_table}
    WHERE trip_id = 1002
    """
)
display(spark.table(lab_table).orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Explore history with `DESCRIBE HISTORY`
# MAGIC
# MAGIC `DESCRIBE HISTORY` lets you inspect the versions recorded for a Delta table.
# MAGIC
# MAGIC For this lesson, focus on:
# MAGIC
# MAGIC * **`version`** — identifies the table version
# MAGIC * **`timestamp`** — when the version was created
# MAGIC * **`operation`** — the type of operation that created the version
# MAGIC
# MAGIC Ignore the other columns for now.
# MAGIC
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT version, timestamp, operation FROM (DESCRIBE HISTORY rideshare_dev.processed.fare_timetravel_lab)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Time travel by version
# MAGIC
# MAGIC Time travel lets you **read** an earlier version of a Delta table without changing its current state.
# MAGIC

# COMMAND ----------

# Table as it looked at version 2 (before the tip update)
before_update = spark.sql(
    f"""
    SELECT *
    FROM {lab_table}
    VERSION AS OF 2
    """
)
display(before_update.orderBy("trip_id"))

# Current table — time travel does not change it
current = spark.table(lab_table)
display(current.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Time travel by timestamp
# MAGIC Sometimes you don't know the Delta version number. Instead, you know approximately when the table was last correct, such as before a bad load.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM rideshare_dev.processed.fare_timetravel_lab
# MAGIC TIMESTAMP AS OF '2026-08-29T18:45:22.000+00:00'

# COMMAND ----------

# MAGIC %md
# MAGIC ## Time travel with PySpark
# MAGIC
# MAGIC Delta time travel is also available through the DataFrame reader. Use the `versionAsOf` option to load a specific historical version of the table.
# MAGIC

# COMMAND ----------

# Same version 2, through the DataFrame reader
historical_df = spark.read.option("versionAsOf", 2).table(lab_table)
display(historical_df.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Restore an earlier state
# MAGIC Time travel and `RESTORE` both use Delta history, but they do different
# MAGIC jobs.

# COMMAND ----------

# Recover version 3: after the UPDATE, before the DELETE
spark.sql(
    f"""
    RESTORE TABLE {lab_table}
    TO VERSION AS OF 3
    """
)
# 1002 is back; the corrected tip remains
display(spark.table(lab_table).orderBy("trip_id"))

# HISTORY lists RESTORE as a new version after DELETE
display(spark.sql(f"DESCRIBE HISTORY {lab_table}"))

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC > `RESTORE` creates a new table version that matches the version you choose. The older versions remain in the table history.
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### Restore by timestamp
# MAGIC
# MAGIC `RESTORE` can also use a timestamp instead of a version number.
# MAGIC
# MAGIC ```sql
# MAGIC RESTORE TABLE ... TO TIMESTAMP AS OF '<timestamp>'
# MAGIC ```
# MAGIC
# MAGIC Databricks finds the table state at that time and creates a new version with that state as the current table.
# MAGIC

# COMMAND ----------

# MAGIC
# MAGIC %md
# MAGIC
# MAGIC ## Retention: how far back can you go?
# MAGIC
# MAGIC Time travel and `RESTORE` work only while Delta retains the information needed to access an earlier version:
# MAGIC
# MAGIC - **Transaction history** — identifies the table version.
# MAGIC - **Data files** — contain the data needed to read that version.
# MAGIC
# MAGIC ```text
# MAGIC Historical version
# MAGIC        │
# MAGIC        ├── Transaction history      default: 30 days
# MAGIC        │
# MAGIC        └── Required data files      VACUUM retention: 7 days
# MAGIC ````
# MAGIC
# MAGIC Delta keeps table history for 30 days by default.
# MAGIC
# MAGIC Data files that are no longer needed by the current table become eligible for removal after 7 days by default. They remain in storage until VACUUM runs and deletes them.
# MAGIC
# MAGIC After the required data files are removed, `VERSION AS OF` may no longer be able to read that historical version, even if `DESCRIBE HISTORY` still lists it.
# MAGIC
# MAGIC > **Warning:** Do not run `VACUUM` in this notebook

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC The table has already been restored, so trip **1002** is present again
# MAGIC in the current state.
# MAGIC
# MAGIC Use PySpark `versionAsOf` to read version **4** (the `DELETE` in HISTORY),
# MAGIC then compare it with the current table. Time travel still reads that old
# MAGIC state even after `RESTORE` changed current.
# MAGIC
# MAGIC **Expected:**
# MAGIC - version **4** → **3** rows
# MAGIC - current table → **4** rows

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC **Hint:** Read version **4** with the same `versionAsOf` option used
# MAGIC earlier, then compare its row count with the current table.

# COMMAND ----------

# MAGIC %md
# MAGIC **Solution** (commented out — un-comment if you want to compare)

# COMMAND ----------

# historical = (
#     spark.read
#     .option("versionAsOf", 4)
#     .table(lab_table)
# )
# print(f"historical rows = {historical.count()} (expect 3)")
# display(historical.orderBy("trip_id"))
# current = spark.table(lab_table)
# print(f"current rows = {current.count()} (expect 4)")
# display(current.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - Delta creates a new table version for each committed change.
# MAGIC - `DESCRIBE HISTORY` shows the recorded version history.
# MAGIC - Time travel reads an earlier table state by version or timestamp
# MAGIC   without changing the current table.
# MAGIC - `RESTORE` adds a new commit that makes an earlier table state current
# MAGIC   again.
# MAGIC - Time travel and restore work only while the required history and data
# MAGIC   files are still available.
# MAGIC
# MAGIC **Next:** Time travel and `RESTORE` depend on historical versions
# MAGIC remaining available. Module 11
# MAGIC `01 - Deletion Vectors, REORG TABLE, and VACUUM` introduces cleanup of
# MAGIC obsolete data and its effect on historical access.