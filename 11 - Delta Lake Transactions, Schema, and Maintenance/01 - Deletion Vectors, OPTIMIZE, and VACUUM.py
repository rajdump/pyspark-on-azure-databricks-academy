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
# MAGIC A deletion vector marks **deleted or updated rows** in an existing Parquet file, allowing Delta to avoid rewriting the entire file immediately.
# MAGIC
# MAGIC **Auto-compaction:** After an `UPDATE`, `DELETE`, or `MERGE`, Databricks may automatically compact eligible small files into larger files. You do not need to run `OPTIMIZE` explicitly, but auto-compaction does **not** guarantee that every small file will be compacted.
# MAGIC
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC - Compare how an `UPDATE` behaves with and without **deletion vectors**
# MAGIC - Show that `VACUUM` removes only files that are no longer used by the
# MAGIC   table — it does not compact
# MAGIC - Compact live files with `OPTIMIZE` when they have not already been
# MAGIC   compacted automatically, then remove eligible old files with `VACUUM`
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
    TBLPROPERTIES (
      'delta.enableDeletionVectors' = 'false'
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
# MAGIC Without deletion vectors, updating a single row requires Spark to rewrite the **entire Parquet file that contains that row**.
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
# MAGIC Now Delta can avoid rewriting the entire Parquet file. The old row is marked as no longer part of the current table state, and the updated row is written to a new data file.
# MAGIC
# MAGIC Compare the new file size with Step 1. The new data file should be much smaller.
# MAGIC

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
# MAGIC Run two more updates with deletion vectors enabled, then list the folder again.
# MAGIC
# MAGIC Each update may create a **small Parquet file** and a **deletion-vector `.bin` file**. Automatic compaction may also rewrite eligible live files without running `OPTIMIZE`.
# MAGIC
# MAGIC `LIST` may still show older Parquet and `.bin` files that are no longer part of the current table state.
# MAGIC

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
# MAGIC `DESCRIBE HISTORY` may show an `OPTIMIZE` operation with `"auto":"true"` after the updates. This indicates **automatic compaction**; you have not run `OPTIMIZE` manually yet.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT version, operation, operationParameters
# MAGIC FROM (DESCRIBE HISTORY rideshare_dev.processed.fare_maint_lab) 

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4 — Run VACUUM
# MAGIC
# MAGIC Disable the retention safety check for the current Spark session, then run `VACUUM RETAIN 0 HOURS` and list the folder again.
# MAGIC
# MAGIC `VACUUM` does **not** compact files. It only removes obsolete files that are no longer used by the table and are outside the retention period.
# MAGIC
# MAGIC If auto-compaction already combined the live data, `VACUUM` simply removes the leftover files.
# MAGIC

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
# MAGIC `OPTIMIZE` reorganizes the table’s **live data** into fewer, larger files.
# MAGIC
# MAGIC If auto-compaction has already compacted the table, `OPTIMIZE` may have little or no additional work to do. `LIST` may still show older files because they can remain in storage until `VACUUM` removes them.

# COMMAND ----------

spark.sql(f"OPTIMIZE {lab_table}")
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6 — Remove the obsolete files
# MAGIC
# MAGIC The default `VACUUM` retention period is **7 days**, so files created during this lab are normally too new to remove.
# MAGIC
# MAGIC For this lab, the retention safety check is already disabled. Run:
# MAGIC
# MAGIC ```sql
# MAGIC VACUUM ... RETAIN 0 HOURS
# MAGIC ```
# MAGIC
# MAGIC This removes obsolete files left by previous writes or `OPTIMIZE`.
# MAGIC
# MAGIC > **Warning:** `RETAIN 0 HOURS` can immediately remove historical files required for time travel. Do not use it on production tables.

# COMMAND ----------

spark.sql(f"VACUUM {lab_table} RETAIN 0 HOURS")
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC | Step | What happened                                                                                                     |
# MAGIC | ---- | ----------------------------------------------------------------------------------------------------------------- |
# MAGIC | 1    | DV off → updating one row rewrites the Parquet file containing that row                                           |
# MAGIC | 2    | DV on → the update can avoid rewriting the entire Parquet file                                                    |
# MAGIC | 3    | More DV updates may trigger auto-compaction; `LIST` can still show obsolete Parquet and `.bin` files              |
# MAGIC | 4    | `VACUUM` removes obsolete files; it does **not** compact data                                                     |
# MAGIC | 5    | `OPTIMIZE` compacts live files into fewer, larger files; it may do little if auto-compaction already handled them |
# MAGIC | 6    | `VACUUM` removes obsolete files left after `OPTIMIZE`                                                             |
# MAGIC
# MAGIC **Deletion vectors reduce rewrite work. Auto-compaction and `OPTIMIZE` improve file layout. `VACUUM` removes obsolete files.**
# MAGIC
# MAGIC **Next:** Module 11 continues with transactions, schema changes, and introductory `MERGE`.