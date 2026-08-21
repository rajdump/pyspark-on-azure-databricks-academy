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
# MAGIC You will also run one PySpark `versionAsOf` read, and contrast time travel
# MAGIC **reads** with `RESTORE` (a new Delta commit).
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

from pyspark.sql.types import (
    DecimalType,
    LongType,
    StringType,
    StructField,
    StructType,
)

lab_table = "rideshare_dev.processed.fare_timetravel_lab"

extract_schema = StructType(
    [
        StructField("trip_id", LongType(), False),
        StructField("service_type", StringType(), False),
        StructField("payment_method", StringType(), False),
        StructField("base_fare_amount", DecimalType(10, 2), False),
        StructField("tip_amount", DecimalType(10, 2), False),
    ]
)

trips_extract = spark.createDataFrame(
    [
        (1001, "STANDARD", "card", Decimal("20.00"), Decimal("3.00")),
        (1002, "SHARED", "cash", Decimal("15.00"), Decimal("0.00")),
        (1003, "PREMIUM", "card", Decimal("40.00"), Decimal("6.00")),
        (1004, "STANDARD", "wallet", Decimal("25.00"), Decimal("2.50")),
    ],
    schema=extract_schema,
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
print(f"rows = {spark.table(lab_table).count()} (expect 0)")
display(trips_extract.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Build table history
# MAGIC We will create a short, known history. This is the **expected history in
# MAGIC a clean run** — not integers to paste into SQL:
# MAGIC
# MAGIC ```text
# MAGIC v0 CREATE TABLE           0 rows
# MAGIC v1 WRITE (first INSERT)   1001-1003   3 rows   1003 tip 6.00
# MAGIC v2 WRITE (second INSERT)  +1004       4 rows   1003 tip 6.00
# MAGIC v3 UPDATE                 1003 tip 10 4 rows   1002 present
# MAGIC v4 DELETE                 1002        3 rows
# MAGIC ```
# MAGIC
# MAGIC Code captures named versions after the commits we will query. One
# MAGIC `sleep(2)` after the second insert, before the update, so the timestamp
# MAGIC we capture is not the update's timestamp.
# MAGIC
# MAGIC > **Note:** The pause is only for this lab. Delta does not require waiting
# MAGIC > between writes.

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
after_second = spark.table(lab_table)
print(f"rows = {after_second.count()} (expect 4)")
display(after_second.orderBy("trip_id"))
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
after_update = spark.table(lab_table)
print(f"rows = {after_update.count()} (expect 4)")
display(after_update.orderBy("trip_id"))

# COMMAND ----------

spark.sql(
    f"""
    DELETE FROM {lab_table}
    WHERE trip_id = 1002
    """
)
delete_version, _ = latest_history(lab_table)
after_delete = spark.table(lab_table)
print(f"rows = {after_delete.count()} (expect 3)")
display(after_delete.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Explore history with `DESCRIBE HISTORY`
# MAGIC `DESCRIBE HISTORY` is the easiest way to see the versions that have been
# MAGIC created. Look at **`version`**, **`timestamp`**, and **`operation`**.
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
# MAGIC current table. Use `VERSION AS OF` when `DESCRIBE HISTORY` already gave
# MAGIC you the exact commit.
# MAGIC
# MAGIC Read the snapshot from before the tip correction
# MAGIC (`before_update_version`), then read current (the delete snapshot).

# COMMAND ----------

before_update = spark.sql(
    f"""
    SELECT *
    FROM {lab_table}
    VERSION AS OF {before_update_version}
    """
)
print(f"rows = {before_update.count()} (expect 4)")
display(before_update.orderBy("trip_id"))

current = spark.table(lab_table)
print(f"rows = {current.count()} (expect 3)")
display(current.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Compare snapshots
# MAGIC
# MAGIC ```text
# MAGIC before update     4 rows   tip 6.00    1002 present   (already queried)
# MAGIC restore target    4 rows   tip 10.00   1002 present   (query next)
# MAGIC after delete      3 rows   tip 10.00   1002 missing   (already current)
# MAGIC ```

# COMMAND ----------

restore_target = spark.sql(
    f"""
    SELECT *
    FROM {lab_table}
    VERSION AS OF {restore_version}
    """
)
print(f"rows = {restore_target.count()} (expect 4)")
display(restore_target.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Time travel by timestamp
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
# MAGIC that timestamp. Use the timestamp captured after the second insert.

# COMMAND ----------

by_timestamp = spark.sql(
    f"""
    SELECT *
    FROM {lab_table}
    TIMESTAMP AS OF '{before_update_timestamp}'
    """
)
print(f"rows = {by_timestamp.count()} (expect 4)")
display(by_timestamp.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Time travel with PySpark
# MAGIC The same before-update snapshot as a DataFrame reader option.
# MAGIC `timestampAsOf` exists in Databricks; this lesson omits it on purpose.

# COMMAND ----------

historical_df = spark.read.option("versionAsOf", before_update_version).table(
    lab_table
)
print(f"rows = {historical_df.count()} (expect 4)")
display(historical_df.orderBy("trip_id"))

current = spark.table(lab_table)
print(f"rows = {current.count()} (expect 3)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Restore an earlier state
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
restored = spark.table(lab_table)
print(f"rows = {restored.count()} (expect 4)")
print(f"after_version_restore = {after_version_restore}")
display(restored.orderBy("trip_id"))
display(spark.sql(f"DESCRIBE HISTORY {lab_table}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ```text
# MAGIC Before  UPDATE snapshot   DELETE ← current
# MAGIC After   UPDATE snapshot   DELETE   RESTORE ← current
# MAGIC ```
# MAGIC
# MAGIC `RESTORE` does not erase the delete commit or move the version number
# MAGIC backward. It writes **another** commit whose table state matches the
# MAGIC chosen snapshot. If that restore were wrong, you could restore a later
# MAGIC version still listed in history.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Restore by timestamp
# MAGIC `RESTORE` can also identify the target by timestamp. Do **not** run this;
# MAGIC the version restore already recovered the UPDATE snapshot.
# MAGIC
# MAGIC ```sql
# MAGIC RESTORE TABLE … TO TIMESTAMP AS OF '<timestamp>'
# MAGIC ```
# MAGIC
# MAGIC A timestamp that resolves to the same snapshot as `restore_version` would
# MAGIC restore the same table state. Running it would add another `RESTORE`
# MAGIC commit with those same rows. Timestamp targeting was already executed as
# MAGIC a **read**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Retention: how far back can you go?
# MAGIC Time travel is not a permanent backup. A historical read or restore needs
# MAGIC transaction history **and** the data files for that version.
# MAGIC
# MAGIC ```text
# MAGIC Historical version
# MAGIC        │
# MAGIC        ├── transaction history
# MAGIC        │      default: 30 days
# MAGIC        │
# MAGIC        └── historical data files
# MAGIC               7-day VACUUM eligibility threshold
# MAGIC ```
# MAGIC
# MAGIC - Delta table history is retained for **30 days** by default.
# MAGIC - Obsolete data files have a default **7-day retention threshold** before
# MAGIC   they are eligible for removal by `VACUUM`.
# MAGIC - For reliable time travel beyond 7 days, both transaction history and
# MAGIC   historical data files must be retained long enough.
# MAGIC - `DESCRIBE HISTORY` can still list a version whose required data files
# MAGIC   are no longer available.
# MAGIC - The 7-day threshold does **not** mean files are automatically deleted
# MAGIC   every 7 days. `VACUUM` removes eligible obsolete files.
# MAGIC
# MAGIC This lab's commits are minutes old, so the queries here still work.
# MAGIC
# MAGIC > **Warning:** Do not run `VACUUM` in this notebook. Maintenance is
# MAGIC > Module 11.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC Query the table as it looked **immediately after** trip **1002** was
# MAGIC deleted (`delete_version`).
# MAGIC
# MAGIC - Use `VERSION AS OF`
# MAGIC - Do not `RESTORE`
# MAGIC
# MAGIC **Expected:** historical read is **3** rows (1002 gone). Current without
# MAGIC `AS OF` is still **4** rows (1002 is back from restore).

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC **Hint:** Use `VERSION AS OF` with `delete_version` (or find the `DELETE`
# MAGIC row in `DESCRIBE HISTORY`). Then read the table with no `AS OF` and
# MAGIC confirm `.count()` is **4**.

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
# MAGIC Time travel lets me READ an earlier state without changing the current table.
# MAGIC RESTORE makes an earlier state current again by creating a NEW Delta version.
# MAGIC Historical versions are not retained forever.
# MAGIC ```
# MAGIC
# MAGIC **Next:** Module 11 (transactions, schema, `OPTIMIZE` / `VACUUM`, intro
# MAGIC `MERGE`). This module ends here.
