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
# MAGIC Auto-compaction: After a DML operation completes, automatic compaction may
# MAGIC run on the cluster. It can combine eligible small files and rewrite files
# MAGIC containing deletion vectors without requiring you to execute the `OPTIMIZE`
# MAGIC command explicitly. After deletion-vector writes, that compact can still
# MAGIC run even when the table auto-compact property is false.
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
# MAGIC Then list the table folder and note the Parquet file size.
# MAGIC
# MAGIC At this point, the current table data is stored in **one Parquet file**.
# MAGIC
# MAGIC The `CREATE` sets the table auto-compact property to false. That does not
# MAGIC stop every automatic compact after deletion-vector writes. Later `LIST`
# MAGIC results can include leftover files from that compact, not only the files
# MAGIC the cell you just ran wrote.

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
# MAGIC Run two more updates with deletion vectors enabled, then list the folder
# MAGIC again.
# MAGIC
# MAGIC Each update can add a small file and a deletion-vector file, the same
# MAGIC pattern as Step 2.
# MAGIC
# MAGIC After these writes, automatic compaction can rewrite the live files
# MAGIC without you running `OPTIMIZE`. The current table is then **one data
# MAGIC file**, with **no live deletion-vector file**.
# MAGIC
# MAGIC `LIST` can still show leftover Parquet names and `.bin` files (the
# MAGIC deletion-vector files) from that compact. Those extra names are not extra
# MAGIC live files.

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

# MAGIC %sql
# MAGIC
# MAGIC select version, operation, operationParameters from (
# MAGIC DESCRIBE HISTORY rideshare_dev.processed.fare_maint_lab) 

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4 — Run VACUUM
# MAGIC
# MAGIC Disable the retention safety check for this Spark session so Delta allows
# MAGIC a `VACUUM` retention period shorter than the default safety threshold.
# MAGIC
# MAGIC Run `VACUUM RETAIN 0 HOURS`, then list the folder again.
# MAGIC
# MAGIC `VACUUM` does **not** combine files. It removes only files the current
# MAGIC table no longer uses, once they have passed the retention period.
# MAGIC
# MAGIC If automatic compaction already rewrote the live data into one file,
# MAGIC `VACUUM` deletes the leftover files. `LIST` can then show **one** data
# MAGIC file. That can look as if `VACUUM` compacted the table. It did not.
# MAGIC Compaction already happened; `VACUUM` only removed the leftovers.

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
# MAGIC `OPTIMIZE` reorganizes the table's **live** data into fewer, larger files.
# MAGIC
# MAGIC If automatic compaction already left one live file, this `OPTIMIZE` may
# MAGIC rewrite nothing. `LIST` then stays at one data file. Or it may write a
# MAGIC new Parquet file and leave the previous one on disk for history, so
# MAGIC `LIST` shows two.
# MAGIC
# MAGIC Either result matches a table that is already compacted.

# COMMAND ----------

spark.sql(f"OPTIMIZE {lab_table}")
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6 — Remove the obsolete files
# MAGIC
# MAGIC The default `VACUUM` retention period is **7 days**, so the files created
# MAGIC during this lab are normally too new to delete.
# MAGIC
# MAGIC For this lab only, the session already has the retention safety check
# MAGIC disabled. Run:
# MAGIC
# MAGIC `VACUUM ... RETAIN 0 HOURS`
# MAGIC
# MAGIC If Step 5 wrote a new file and left the old one, `VACUUM` can now remove
# MAGIC that leftover. If `OPTIMIZE` rewrote nothing, `LIST` already shows one
# MAGIC file and stays that way.
# MAGIC
# MAGIC > **Warning:** `RETAIN 0 HOURS` removes historical data files immediately.
# MAGIC > Do not use it on production tables.

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
# MAGIC | 3 | Further DV updates can trigger automatic compaction → one live file; `LIST` may still show leftovers |
# MAGIC | 4 | `VACUUM` does not compact; it can delete leftovers so `LIST` looks compacted |
# MAGIC | 5 | `OPTIMIZE` compacts live files if any remain; it may already be a no-op |
# MAGIC | 6 | `VACUUM` removes obsolete files left after `OPTIMIZE` |
# MAGIC
# MAGIC **Deletion vectors reduce rewrite work. Automatic compaction or
# MAGIC `OPTIMIZE` improves file layout. `VACUUM` removes files that are no
# MAGIC longer needed.**
# MAGIC
# MAGIC **Next:** remaining Module 11 notebooks are not in this notebook.