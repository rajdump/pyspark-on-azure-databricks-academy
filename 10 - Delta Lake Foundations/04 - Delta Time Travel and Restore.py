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
# MAGIC ## Create the lab table
# MAGIC We use a managed Delta table so the lesson can focus on versions, time
# MAGIC travel, and restore.

# COMMAND ----------

import time
from decimal import Decimal

lab_table = "rideshare_dev.processed.fare_timetravel_lab"

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
trips_extract.createOrReplaceTempView("trips_extract")


def latest_history(table):
    row = spark.sql(f"DESCRIBE HISTORY {table} LIMIT 1").first()
    ts_str = row["timestamp"].isoformat(sep=" ", timespec="milliseconds")
    return int(row["version"]), ts_str


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
display(trips_extract.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Build table history
# MAGIC We will intentionally create five table states so we have history to
# MAGIC explore. This is the expected history in a clean run:
# MAGIC
# MAGIC ```text
# MAGIC v0 CREATE TABLE           0 rows
# MAGIC v1 WRITE (first INSERT)   1001-1003   3 rows   1003 tip 6.00
# MAGIC v2 WRITE (second INSERT)  +1004       4 rows   1003 tip 6.00
# MAGIC v3 UPDATE                 1003 tip 10 4 rows   1002 present
# MAGIC v4 DELETE                 1002        3 rows
# MAGIC ```
# MAGIC
# MAGIC The notebook captures the actual versions from Delta history and uses
# MAGIC those captured values in later queries, not these `v0`–`v4` labels.
# MAGIC
# MAGIC > **Note:** After the second insert we pause two seconds so the captured
# MAGIC > timestamp is clearly before the update. Delta does not require this wait.

# COMMAND ----------

spark.sql(
    f"""
    INSERT INTO {lab_table}
    SELECT * FROM trips_extract
    WHERE trip_id <= 1003
    """
)
print(f"rows = {spark.table(lab_table).count()} (expect 3)")

# COMMAND ----------

spark.sql(
    f"""
    INSERT INTO {lab_table}
    SELECT * FROM trips_extract
    WHERE trip_id = 1004
    """
)
before_update_version, before_update_timestamp = latest_history(lab_table)
display(spark.table(lab_table).orderBy("trip_id"))
time.sleep(2)

# COMMAND ----------

spark.sql(
    f"""
    UPDATE {lab_table}
    SET tip_amount = 10.00
    WHERE trip_id = 1003
    """
)
restore_version, _ = latest_history(lab_table)
display(spark.table(lab_table).orderBy("trip_id"))

# COMMAND ----------

spark.sql(
    f"""
    DELETE FROM {lab_table}
    WHERE trip_id = 1002
    """
)
delete_version, _ = latest_history(lab_table)
display(spark.table(lab_table).orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Explore history with `DESCRIBE HISTORY`
# MAGIC `DESCRIBE HISTORY` returns one row per recorded table version. For this
# MAGIC lesson, look at:
# MAGIC
# MAGIC - **`version`** — identifies the table state
# MAGIC - **`timestamp`** — when that version was created
# MAGIC - **`operation`** — the type of change
# MAGIC
# MAGIC Ignore the other columns for now.
# MAGIC
# MAGIC We ran `INSERT` for the first two data commits. `DESCRIBE HISTORY`
# MAGIC typically records those appends as **`WRITE`**.

# COMMAND ----------

display(spark.sql(f"DESCRIBE HISTORY {lab_table}"))
print(f"before_update_version = {before_update_version}")
print(f"restore_version = {restore_version}")
print(f"delete_version = {delete_version}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Time travel by version
# MAGIC Time travel lets you **read** an earlier version without changing the
# MAGIC current table.
# MAGIC
# MAGIC `DESCRIBE HISTORY` gave you the version numbers. `VERSION AS OF` reads
# MAGIC the table as it looked at that commit. The query is read-only.
# MAGIC
# MAGIC Read the snapshot from before the tip correction
# MAGIC (`before_update_version`), then read current (after the delete).

# COMMAND ----------

before_update = spark.sql(
    f"""
    SELECT *
    FROM {lab_table}
    VERSION AS OF {before_update_version}
    """
)
display(before_update.orderBy("trip_id"))

current = spark.table(lab_table)
display(current.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Compare snapshots
# MAGIC
# MAGIC ```text
# MAGIC Before update    4 rows   tip 6.00    1002 present
# MAGIC After update     4 rows   tip 10.00   1002 present
# MAGIC After delete     3 rows   tip 10.00   1002 missing
# MAGIC ```
# MAGIC
# MAGIC The before-update state shows the original tip. The after-delete state is
# MAGIC the current table. Next, read the state immediately after the update:
# MAGIC corrected tip, trip **1002** still present — later the restore target.

# COMMAND ----------

restore_target = spark.sql(
    f"""
    SELECT *
    FROM {lab_table}
    VERSION AS OF {restore_version}
    """
)
display(restore_target.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Time travel by timestamp
# MAGIC A historical state can be identified by version number or by time.
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
# MAGIC that timestamp. This timestamp points to the same before-update snapshot
# MAGIC used in the previous section.

# COMMAND ----------

by_timestamp = spark.sql(
    f"""
    SELECT *
    FROM {lab_table}
    TIMESTAMP AS OF '{before_update_timestamp}'
    """
)
display(by_timestamp.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Time travel with PySpark
# MAGIC Delta time travel is also available on the DataFrame reader. Use the
# MAGIC `versionAsOf` option to load a historical version of the table.

# COMMAND ----------

historical_df = spark.read.option("versionAsOf", before_update_version).table(
    lab_table
)
display(historical_df.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Restore an earlier state
# MAGIC Time travel and `RESTORE` both use Delta history, but they do different
# MAGIC jobs.
# MAGIC
# MAGIC ```text
# MAGIC TIME TRAVEL  read old state     current unchanged
# MAGIC RESTORE      make old state current    new Delta version
# MAGIC ```
# MAGIC
# MAGIC Suppose deleting trip **1002** was a mistake. `restore_version` is the
# MAGIC UPDATE snapshot: trip **1003** is already **10.00**, and **1002** is still
# MAGIC there.

# COMMAND ----------

spark.sql(
    f"""
    RESTORE TABLE {lab_table}
    TO VERSION AS OF {restore_version}
    """
)
after_version_restore, _ = latest_history(lab_table)
print(f"after_version_restore = {after_version_restore}")
display(spark.table(lab_table).orderBy("trip_id"))
display(spark.sql(f"DESCRIBE HISTORY {lab_table}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ```text
# MAGIC Before RESTORE   UPDATE snapshot   DELETE ← current
# MAGIC After RESTORE    UPDATE snapshot   DELETE   RESTORE ← current
# MAGIC ```
# MAGIC
# MAGIC `RESTORE` does not rewind or erase Delta history. It writes **another**
# MAGIC commit whose table state matches the chosen snapshot. The delete commit
# MAGIC stays in history, and the version number keeps moving forward. You can
# MAGIC restore another available version if the required history and data files
# MAGIC are still retained.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Restore by timestamp
# MAGIC `RESTORE` can target a version or a timestamp. Do not run this; the table
# MAGIC is already restored.
# MAGIC
# MAGIC ```sql
# MAGIC RESTORE TABLE … TO TIMESTAMP AS OF '<timestamp>'
# MAGIC ```
# MAGIC
# MAGIC Both forms select a historical state and create a new Delta version.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Retention: how far back can you go?
# MAGIC Time travel is not a permanent backup. A historical read or restore needs
# MAGIC transaction history **and** the data files for that version.
# MAGIC
# MAGIC ```text
# MAGIC Historical version
# MAGIC        │
# MAGIC        ├── transaction history     default: 30 days
# MAGIC        └── historical data files   7-day VACUUM eligibility
# MAGIC ```
# MAGIC
# MAGIC Delta keeps table history for **30 days** by default. Obsolete files
# MAGIC become eligible for `VACUUM` after **7 days**. Reliable time travel beyond
# MAGIC 7 days needs both the transaction history and the required data files.
# MAGIC
# MAGIC `DESCRIBE HISTORY` can still list a version whose files are gone. The
# MAGIC 7-day threshold is not an automatic delete timer.
# MAGIC
# MAGIC This lab's commits are minutes old, so the queries here still work.
# MAGIC
# MAGIC > **Warning:** Do not run `VACUUM` in this notebook. Maintenance is
# MAGIC > Module 11.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC The table is already restored, so trip **1002** is present again.
# MAGIC
# MAGIC Query the table as it looked **immediately after** trip **1002** was
# MAGIC deleted (`delete_version`).
# MAGIC
# MAGIC - Use `VERSION AS OF`
# MAGIC - Do not `RESTORE`
# MAGIC
# MAGIC **Expected:** historical read is **3** rows (1002 gone). Current without
# MAGIC `AS OF` is still **4** rows.

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC **Hint:** Use `delete_version` with `VERSION AS OF`, then compare that
# MAGIC result with the current table.

# COMMAND ----------

# MAGIC %md
# MAGIC **Solution** (commented out — un-comment if you want to compare)

# COMMAND ----------

# historical = spark.sql(
#     f"""
#     SELECT *
#     FROM {lab_table}
#     VERSION AS OF {delete_version}
#     """
# )
# print(f"rows = {historical.count()} (expect 3)")
# display(historical.orderBy("trip_id"))
# current = spark.table(lab_table)
# print(f"rows = {current.count()} (expect 4)")
# display(current.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC ```text
# MAGIC A Delta table creates versions as it changes.
# MAGIC DESCRIBE HISTORY shows the table's recorded version history.
# MAGIC Time travel lets me read an earlier state by version or timestamp
# MAGIC without changing the current table.
# MAGIC RESTORE makes an earlier state current again by creating a NEW Delta version.
# MAGIC Historical access depends on the required transaction history and data
# MAGIC files still being available.
# MAGIC ```
# MAGIC
# MAGIC **Next:** Module 11 (transactions, schema, `OPTIMIZE` / `VACUUM`, intro
# MAGIC `MERGE`). This module ends here.
