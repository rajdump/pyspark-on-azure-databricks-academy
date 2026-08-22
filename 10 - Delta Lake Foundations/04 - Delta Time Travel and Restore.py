# Databricks notebook source
# MAGIC %md
# MAGIC # 04 - Delta Time Travel and Restore
# MAGIC
# MAGIC The fares table will change several times. How do you inspect an earlier
# MAGIC state, and how do you make an older state current again?
# MAGIC
# MAGIC Notebook 02 showed how Delta versions are created. This notebook uses
# MAGIC version history to read and restore earlier table states.
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC - Inspect Delta table history
# MAGIC - Query an earlier state by version and by timestamp
# MAGIC - Restore an earlier state
# MAGIC - Understand how retention limits access to historical versions
# MAGIC
# MAGIC **Reads:** none of the 100-row source files or teaching tables
# MAGIC (`trip_enriched`, KPIs, `curated/`)
# MAGIC
# MAGIC **Writes:**
# MAGIC - `rideshare_dev.processed.fare_timetravel_lab`
# MAGIC
# MAGIC **Prerequisites:** Module 9 notebooks `01`–`06`. Module 5
# MAGIC `01 - Unity Catalog Volumes and Data Landing.py` (catalog, `processed`).
# MAGIC
# MAGIC This notebook does not cover Delta maintenance or advanced change-tracking
# MAGIC features.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup — create the lab table
# MAGIC We use a managed Delta table so the lesson can focus on versions, time
# MAGIC travel, and restore.

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
    TBLPROPERTIES ('delta.enableDeletionVectors' = 'false')
    """
)

print(f"lab_table = {lab_table}")
print(f"rows = {spark.table(lab_table).count()} (expect 0)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Build table history
# MAGIC We will intentionally create five table states so we have history to
# MAGIC explore. After a full run from the top, `DESCRIBE HISTORY` matches this
# MAGIC timeline:
# MAGIC
# MAGIC ```text
# MAGIC version 0  CREATE TABLE           0 rows
# MAGIC version 1  WRITE (first INSERT)   1001-1003   3 rows   1003 tip 6.00
# MAGIC version 2  WRITE (second INSERT)  +1004       4 rows   1003 tip 6.00
# MAGIC version 3  UPDATE                 1003 tip 10 4 rows   1002 present
# MAGIC version 4  DELETE                 1002        3 rows
# MAGIC ```
# MAGIC
# MAGIC Later cells use these version numbers. If you re-run only some cells,
# MAGIC use the numbers `DESCRIBE HISTORY` shows in **this** run.

# COMMAND ----------

# First data version: trips 1001–1003
spark.sql(
    f"""
    INSERT INTO {lab_table}
    SELECT * FROM trips_extract
    WHERE trip_id <= 1003
    """
)
print(f"rows = {spark.table(lab_table).count()} (expect 3)")

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
# MAGIC `DESCRIBE HISTORY` is how you identify versions. It returns one row per
# MAGIC recorded table version. For this lesson, look at:
# MAGIC
# MAGIC - **`version`** — identifies the table state
# MAGIC - **`timestamp`** — when that version was created
# MAGIC - **`operation`** — the type of change
# MAGIC
# MAGIC Ignore the other columns for now.
# MAGIC
# MAGIC We ran `INSERT` for the first two data commits. `DESCRIBE HISTORY`
# MAGIC typically records those appends as **`WRITE`**.
# MAGIC
# MAGIC Find version **2** (before the tip update), version **3** (after the
# MAGIC update, 1002 still present), and version **4** (after the delete). Later
# MAGIC queries use those numbers.

# COMMAND ----------

display(spark.sql(f"DESCRIBE HISTORY {lab_table}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Time travel by version
# MAGIC Time travel lets you **read** an earlier version without changing the
# MAGIC current table.
# MAGIC
# MAGIC `DESCRIBE HISTORY` gave you the version numbers. `VERSION AS OF` reads
# MAGIC the table as it looked at that commit. The query is read-only.
# MAGIC
# MAGIC Read version **2** (before the tip correction), then read current (after
# MAGIC the delete).

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
# MAGIC ### Compare versions
# MAGIC
# MAGIC ```text
# MAGIC Version 2  before update    4 rows   tip 6.00    1002 present
# MAGIC Version 3  after update     4 rows   tip 10.00   1002 present
# MAGIC Version 4  after delete     3 rows   tip 10.00   1002 missing
# MAGIC ```
# MAGIC
# MAGIC Version 2 shows the original tip. Version 4 is the current table. Next,
# MAGIC read version 3: corrected tip, trip **1002** still present. That is the
# MAGIC version we will restore to later.

# COMMAND ----------

# Table as it looked at version 3 (after the tip correction)
after_update = spark.sql(
    f"""
    SELECT *
    FROM {lab_table}
    VERSION AS OF 3
    """
)
display(after_update.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Time travel by timestamp
# MAGIC A historical table state can be identified by version number or by time.
# MAGIC
# MAGIC ```text
# MAGIC I know the exact Delta version
# MAGIC → VERSION AS OF
# MAGIC
# MAGIC I know the time when the table was correct
# MAGIC → TIMESTAMP AS OF
# MAGIC ```
# MAGIC
# MAGIC `TIMESTAMP AS OF` resolves to the latest table version **at or before**
# MAGIC that timestamp. Use the **timestamp** column HISTORY showed for version
# MAGIC **2** — the same table state as `VERSION AS OF 2`.

# COMMAND ----------

# Timestamp HISTORY recorded for version 2
v2 = spark.sql(f"DESCRIBE HISTORY {lab_table}").where("version = 2").first()
ts_v2 = v2["timestamp"].isoformat(sep=" ", timespec="milliseconds")

by_timestamp = spark.sql(
    f"""
    SELECT *
    FROM {lab_table}
    TIMESTAMP AS OF '{ts_v2}'
    """
)
display(by_timestamp.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Time travel with PySpark
# MAGIC Delta time travel is also available on the DataFrame reader. Use the
# MAGIC `versionAsOf` option to load a historical version of the table.

# COMMAND ----------

# Same version 2, through the DataFrame reader
historical_df = spark.read.option("versionAsOf", 2).table(lab_table)
display(historical_df.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Restore an earlier state
# MAGIC Time travel and `RESTORE` both use Delta history, but they do different
# MAGIC jobs.
# MAGIC
# MAGIC ```text
# MAGIC TIME TRAVEL   read an earlier version     current table unchanged
# MAGIC RESTORE       make an earlier version     the new current state
# MAGIC               current                     (a new Delta version)
# MAGIC ```
# MAGIC
# MAGIC Suppose deleting trip **1002** was a mistake. Version **3** is the UPDATE:
# MAGIC trip **1003** is already **10.00**, and **1002** is still there.

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
# MAGIC `RESTORE` adds a new commit to the Delta transaction log. The new commit can point to the same data files used by the older version.
# MAGIC
# MAGIC The original versions remain in history, and the version number continues to increase.
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### Restore by timestamp
# MAGIC `RESTORE` can also use a timestamp instead of a version number.
# MAGIC
# MAGIC
# MAGIC ```sql
# MAGIC RESTORE TABLE … TO TIMESTAMP AS OF '<timestamp>'
# MAGIC ```
# MAGIC
# MAGIC Databricks finds the table state at that time and adds a new commit to the Delta transaction log that makes that historical state current again.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Retention: how far back can you go?
# MAGIC Time travel and `RESTORE` work only while Delta still has:
# MAGIC
# MAGIC - the transaction history for that version
# MAGIC - the data files referenced by that version
# MAGIC
# MAGIC ```text
# MAGIC Historical version
# MAGIC        │
# MAGIC        ├── Transaction history      default: 30 days
# MAGIC        └── Required data files      VACUUM retention: 7 days
# MAGIC ```
# MAGIC
# MAGIC Delta keeps table history for 30 days by default.
# MAGIC Data files that are no longer part of the current table become eligible
# MAGIC for removal by `VACUUM` after 7 days by default.
# MAGIC So a version may still appear in `DESCRIBE HISTORY`, but time travel or
# MAGIC `RESTORE` can fail if the required old data files have already been
# MAGIC removed.
# MAGIC
# MAGIC **Note:** The 7-day retention period does not mean files are automatically
# MAGIC deleted after 7 days. `VACUUM` must remove them.
# MAGIC
# MAGIC > **Warning:** Do not run `VACUUM` in this notebook. Maintenance is
# MAGIC > Module 11.

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
# MAGIC - Time travel and restore work only while the required transaction
# MAGIC   history and data files are still available.
# MAGIC
# MAGIC **Next:** Module 11 — transactions, schema, `OPTIMIZE`, `VACUUM`, and an
# MAGIC introduction to `MERGE`.