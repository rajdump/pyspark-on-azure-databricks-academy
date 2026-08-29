# Databricks notebook source
# MAGIC %md
# MAGIC # 01 - Deletion Vectors, REORG TABLE, and VACUUM
# MAGIC
# MAGIC Module 10 showed how a one-row fare `UPDATE` can leave old data files behind.
# MAGIC
# MAGIC This notebook introduces **deletion vectors**, then uses
# MAGIC **`REORG TABLE ... APPLY (PURGE)`** to rewrite current files that still hold
# MAGIC deleted or updated rows, and **`VACUUM`** to remove the old files.
# MAGIC
# MAGIC A deletion vector marks **deleted or updated rows** in an existing Parquet
# MAGIC file, so Delta can avoid rewriting the entire file immediately.
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC - Compare how an `UPDATE` behaves with and without **deletion vectors**
# MAGIC - Show that `VACUUM` removes only files that are no longer used by the
# MAGIC   table — it does not purge deletion-vector rows from live files
# MAGIC - Purge those rows from current files with
# MAGIC   `REORG TABLE ... APPLY (PURGE)`, then remove the old files with `VACUUM`
# MAGIC
# MAGIC **Reads:** none of the 100-row source files or teaching tables
# MAGIC (`trip_enriched`, KPIs, `curated/`)
# MAGIC
# MAGIC **Writes:**
# MAGIC - `rideshare_dev.processed.fare_maint_lab` at `{url}/external-tables/fare_maint_lab`
# MAGIC
# MAGIC **Prerequisites:** Module 10 notebooks `01`–`04`. Module 5
# MAGIC `01 - Unity Catalog Volumes and Data Landing.py` (catalog,
# MAGIC `el_rideshare_dev`, `processed`).
# MAGIC
# MAGIC This notebook does **not** teach ACID, schema evolution, `MERGE`,
# MAGIC `OPTIMIZE`, liquid clustering, Change Data Feed, or a table-properties
# MAGIC tour.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 0 — Start with one data file
# MAGIC
# MAGIC Create the Delta table with **deletion vectors disabled** and insert four
# MAGIC rows. Auto-compaction is off so later deletion vectors stay visible for
# MAGIC the purge demo.
# MAGIC
# MAGIC At this point, the current table data is stored in **one Parquet file**.

# COMMAND ----------

spark.conf.set("spark.databricks.delta.autoCompact.enabled", "false")

lab_table = "rideshare_dev.processed.fare_maint_lab"

external_location_url = (
    spark.sql("DESCRIBE EXTERNAL LOCATION el_rideshare_dev")
    .select("url")
    .first()["url"]
    .rstrip("/")
)
lab_path = f"{external_location_url}/external-tables/fare_maint_lab"

spark.sql(f"DROP TABLE IF EXISTS {lab_table}")
dbutils.fs.rm(lab_path, True)

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
    LOCATION '{lab_path}'
    TBLPROPERTIES (
      'delta.enableDeletionVectors' = 'false',
      'delta.autoOptimize.autoCompact' = 'false'
    )
    """
)
spark.sql(
    f"""
    INSERT INTO {lab_table} VALUES
      (1001, 'STANDARD', 'card', 20.00, 3.00),
      (1002, 'SHARED', 'cash', 15.00, 0.00),
      (1003, 'PREMIUM', 'card', 40.00, 6.00),
      (1004, 'STANDARD', 'wallet', 25.00, 2.50)
    """
)
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 — Update one row without deletion vectors
# MAGIC
# MAGIC Without deletion vectors, updating a single row requires Spark to rewrite
# MAGIC the **entire Parquet file that contains that row**.
# MAGIC
# MAGIC The original file remains on disk for Delta history.

# COMMAND ----------

spark.sql(
    f"""
    UPDATE {lab_table}
    SET tip_amount = 10.00
    WHERE trip_id = 1003
    """
)
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 — Enable deletion vectors
# MAGIC
# MAGIC Enable deletion vectors and update the **same row again**.
# MAGIC
# MAGIC Now Delta can avoid rewriting the entire Parquet file. The old row is
# MAGIC marked as no longer part of the current table state, and the updated row
# MAGIC is written to a new data file.
# MAGIC
# MAGIC Compare the new file size with Step 1. The new data file should be much
# MAGIC smaller, and you should also see a deletion-vector `.bin` file.

# COMMAND ----------

spark.sql(
    f"""
    ALTER TABLE {lab_table}
    SET TBLPROPERTIES ('delta.enableDeletionVectors' = 'true')
    """
)

# COMMAND ----------

spark.sql(
    f"""
    UPDATE {lab_table}
    SET tip_amount = 12.00
    WHERE trip_id = 1003
    """
)
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 — Keep updating
# MAGIC
# MAGIC Run two more updates with deletion vectors enabled, then list the folder
# MAGIC after each.
# MAGIC
# MAGIC Each update may create a **small Parquet file** and a **deletion-vector
# MAGIC `.bin` file**. Older Parquet and `.bin` files can remain in `LIST` until
# MAGIC `VACUUM`.

# COMMAND ----------

spark.sql(
    f"""
    UPDATE {lab_table}
    SET tip_amount = 4.00
    WHERE trip_id = 1001
    """
)
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

spark.sql(
    f"""
    UPDATE {lab_table}
    SET tip_amount = 3.50
    WHERE trip_id = 1004
    """
)
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4 — Delete a row with deletion vectors
# MAGIC
# MAGIC Delete trip **1002**. The query result drops the row. The live Parquet
# MAGIC file can still hold that trip's bytes, with a deletion vector marking it
# MAGIC as removed.

# COMMAND ----------

spark.sql(
    f"""
    DELETE FROM {lab_table}
    WHERE trip_id = 1002
    """
)
display(spark.sql(f"SELECT * FROM {lab_table} ORDER BY trip_id"))
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5 — Run VACUUM
# MAGIC
# MAGIC Disable the retention safety check for the current Spark session, then run
# MAGIC `VACUUM RETAIN 0 HOURS` and list the folder again.
# MAGIC
# MAGIC `VACUUM` does **not** purge deletion-vector rows from live files. It only
# MAGIC removes obsolete files that are no longer used by the table and are
# MAGIC outside the retention period.
# MAGIC
# MAGIC The leftover file from the Step 1 rewrite can go. Live files that still
# MAGIC carry deletion vectors remain.
# MAGIC
# MAGIC > **Warning:** `RETAIN 0 HOURS` can immediately remove historical files
# MAGIC > required for time travel. Do not use it on production tables.

# COMMAND ----------

spark.conf.set(
    "spark.databricks.delta.retentionDurationCheck.enabled", "false"
)
spark.sql(f"VACUUM {lab_table} RETAIN 0 HOURS")
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6 — Purge with REORG TABLE
# MAGIC
# MAGIC `REORG TABLE ... APPLY (PURGE)` rewrites **current** files that still
# MAGIC carry deletion-vector changes. After this command, the deleted and
# MAGIC updated rows are gone from the live data files.
# MAGIC
# MAGIC The old files can remain in `LIST` until `VACUUM`.

# COMMAND ----------

spark.sql(f"REORG TABLE {lab_table} APPLY (PURGE)")
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC `DESCRIBE HISTORY` records the `REORG`.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT version, operation, operationParameters
# MAGIC FROM (DESCRIBE HISTORY rideshare_dev.processed.fare_maint_lab)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 7 — Remove the obsolete files
# MAGIC
# MAGIC The default `VACUUM` retention period is **7 days**, so files created
# MAGIC during this lab are normally too new to remove.
# MAGIC
# MAGIC For this lab, the retention safety check is already disabled. Run
# MAGIC `VACUUM ... RETAIN 0 HOURS` again. This removes files that `REORG`
# MAGIC replaced.

# COMMAND ----------

spark.sql(f"VACUUM {lab_table} RETAIN 0 HOURS")
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 8 — Run REORG again
# MAGIC
# MAGIC `REORG TABLE ... APPLY (PURGE)` is idempotent. A second run has no further
# MAGIC rewrite to do when current files no longer carry deletion-vector changes.

# COMMAND ----------

spark.sql(f"REORG TABLE {lab_table} APPLY (PURGE)")
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC | Step | What happened |
# MAGIC | ---- | ------------- |
# MAGIC | 1 | DV off → updating one row rewrites the Parquet file containing that row |
# MAGIC | 2 | DV on → the update can avoid rewriting the entire Parquet file |
# MAGIC | 3 | More DV updates add small Parquet files and `.bin` files |
# MAGIC | 4 | `DELETE` 1002 → `SELECT` has 3 rows; live files can still hold the row |
# MAGIC | 5 | `VACUUM` removes unused files; it does **not** purge live DV data |
# MAGIC | 6 | `REORG TABLE ... APPLY (PURGE)` rewrites current files that carry DVs |
# MAGIC | 7 | `VACUUM` removes the files `REORG` replaced |
# MAGIC | 8 | A second `REORG` is a no-op |
# MAGIC
# MAGIC **Deletion vectors avoid a full file rewrite. `REORG TABLE ... APPLY
# MAGIC (PURGE)` removes the old row bytes from current files. `VACUUM` then
# MAGIC deletes the files `REORG` replaced.**
# MAGIC
# MAGIC **Next:** Module 11 continues with transactions, schema changes, and
# MAGIC introductory `MERGE`.
