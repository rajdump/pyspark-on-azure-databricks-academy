# Databricks notebook source
# MAGIC %md
# MAGIC # 01 - Deletion Vectors, OPTIMIZE, and VACUUM
# MAGIC
# MAGIC Module 10 showed how a one-row fare `UPDATE` can leave old data files behind.
# MAGIC
# MAGIC This notebook introduces **deletion vectors**, then uses **`OPTIMIZE`** to
# MAGIC improve the active file layout and **`VACUUM`** to remove old files that are
# MAGIC no longer needed.
# MAGIC
# MAGIC A deletion vector marks a replaced row so Spark can skip rewriting the
# MAGIC whole Parquet file.
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC - Compare how an `UPDATE` behaves with and without **deletion vectors**
# MAGIC - Show that `VACUUM` removes only files that are no longer used by the table
# MAGIC - Compact active files with `OPTIMIZE`, then remove eligible old files with
# MAGIC   `VACUUM`
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
# MAGIC This notebook does **not** teach ACID, schema evolution, `MERGE`, liquid
# MAGIC clustering, Change Data Feed, or a table-properties tour.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 0 — Start with one data file
# MAGIC
# MAGIC Create the Delta table with **deletion vectors disabled** and insert four rows.
# MAGIC
# MAGIC Then list the table folder and note the Parquet file size.
# MAGIC
# MAGIC At this point, the current table data is stored in **one Parquet file**.

# COMMAND ----------

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
    TBLPROPERTIES ('delta.enableDeletionVectors' = 'false')
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
# MAGIC Update one row, then list the table folder again.
# MAGIC
# MAGIC Without deletion vectors, changing one row requires Spark to rewrite the **Parquet file containing that row**.
# MAGIC
# MAGIC Because this lab has only one data file, all four rows are written into a new file. The original file remains on disk for Delta history.

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
# MAGIC Now Spark can avoid rewriting the entire Parquet file. The old row is marked as logically replaced, while the updated value is written separately.
# MAGIC
# MAGIC Compare the new file size with Step 1. The new write should be much smaller.

# COMMAND ----------

spark.sql(
    f"""
    ALTER TABLE {lab_table}
    SET TBLPROPERTIES ('delta.enableDeletionVectors' = 'true')
    """
)
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
# MAGIC Run a few more updates with deletion vectors enabled, then list the folder again.
# MAGIC
# MAGIC The original data file still holds unchanged rows, while the updates create additional small files.
# MAGIC
# MAGIC Repeated row-level changes can therefore leave the table reading from **many small files**.

# COMMAND ----------

spark.sql(
    f"""
    UPDATE {lab_table}
    SET tip_amount = 4.00
    WHERE trip_id = 1001
    """
)
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
# MAGIC ## Step 4 — Run VACUUM
# MAGIC
# MAGIC Run `VACUUM RETAIN 0 HOURS`, then list the folder again.
# MAGIC
# MAGIC `VACUUM` does **not** combine small files. It removes old files only when they are no longer needed and have passed the retention period.
# MAGIC
# MAGIC The live small files remain because the current table still uses them.

# COMMAND ----------

spark.conf.set(
    "spark.databricks.delta.retentionDurationCheck.enabled", "false"
)
spark.sql(f"VACUUM {lab_table} RETAIN 0 HOURS")
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5 — Run OPTIMIZE
# MAGIC
# MAGIC Run `OPTIMIZE`, then list the folder again.
# MAGIC
# MAGIC `OPTIMIZE` reorganizes the table's live data into **fewer, larger files**.
# MAGIC
# MAGIC On this tiny table, you may see the current rows compacted into a single data file.
# MAGIC
# MAGIC The previous files can remain on disk because Delta may still need them for historical versions.

# COMMAND ----------

spark.sql(f"OPTIMIZE {lab_table}")
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6 — Remove the obsolete files
# MAGIC
# MAGIC The default `VACUUM` retention period is **7 days**, so the files created during this lab are normally too new to delete.
# MAGIC
# MAGIC For this lab only, disable the retention safety check and run:
# MAGIC
# MAGIC `VACUUM ... RETAIN 0 HOURS`
# MAGIC
# MAGIC Now the obsolete files created by the earlier updates and `OPTIMIZE` can be physically removed.
# MAGIC
# MAGIC > **Warning:** `RETAIN 0 HOURS` removes historical data files immediately. Do not use it on production tables.

# COMMAND ----------

spark.sql(f"VACUUM {lab_table} RETAIN 0 HOURS")
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC | Step | What happened |
# MAGIC |---|---|
# MAGIC | 1 | DV off → updating one row rewrites its Parquet file |
# MAGIC | 2 | DV on → the update can avoid the full-file rewrite |
# MAGIC | 3 | Repeated updates can create many small live files |
# MAGIC | 4 | `VACUUM` does not compact live files |
# MAGIC | 5 | `OPTIMIZE` compacts live data into fewer files |
# MAGIC | 6 | `VACUUM` removes obsolete files after compaction |
# MAGIC
# MAGIC **Deletion vectors reduce rewrite work. `OPTIMIZE` improves file layout. `VACUUM` removes files that are no longer needed.**
# MAGIC
# MAGIC **Next:** remaining Module 11 notebooks are not in this notebook.
