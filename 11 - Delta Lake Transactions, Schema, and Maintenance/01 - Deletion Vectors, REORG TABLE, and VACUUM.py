# Databricks notebook source
# MAGIC %md
# MAGIC # 01 - Deletion Vectors, REORG TABLE, and VACUUM
# MAGIC
# MAGIC Without deletion vectors, an `UPDATE` or `DELETE` rewrites the Parquet
# MAGIC file that holds the row. With deletion vectors, Delta **marks** the row
# MAGIC instead. `VACUUM` removes unused files. `REORG TABLE ... APPLY (PURGE)`
# MAGIC rewrites live files so those marks become a physical rewrite, then
# MAGIC `VACUUM` deletes the files `REORG` replaced.
# MAGIC
# MAGIC This notebook uses one ~300 MB file so those marks stay visible. Inspect
# MAGIC only four `row_id`s — do not `SELECT *` the table.
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC - Compare one `UPDATE` with and without **deletion vectors**
# MAGIC - `DELETE` a row that stays in the live file until purge
# MAGIC - Use `VACUUM` then `REORG ... APPLY (PURGE)` then `VACUUM` again
# MAGIC
# MAGIC **Reads:** Parquet folder from `00 - Copy Fare DV Lab File`
# MAGIC
# MAGIC **Writes:** `rideshare_dev.processed.fare_dv_lab` at
# MAGIC `{url}/external-tables/fare_dv_lab`
# MAGIC
# MAGIC **Prerequisites:** Module 10 `01`–`04`. Module 11 `00`. Module 5 `01`
# MAGIC (catalog, `el_rideshare_dev`, `processed`).
# MAGIC
# MAGIC This notebook does **not** teach ACID, schema evolution, `MERGE`,
# MAGIC `OPTIMIZE`, or time travel.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 0 — Delta table on the Parquet folder
# MAGIC
# MAGIC Notebook **00** already placed `fare_dv_lab.parquet` in this folder
# MAGIC (**11,060,030** rows). Convert that folder to Delta and register the
# MAGIC external table. Deletion vectors start **off**.
# MAGIC
# MAGIC Auto-compaction is off so later `.bin` files stay visible.

# COMMAND ----------

spark.conf.set("spark.databricks.delta.autoCompact.enabled", "false")

lab_table = "rideshare_dev.processed.fare_dv_lab"
inspect_ids = (
    210049714452023,
    210049714452029,
    210049714452046,
    210049714452050,
)
inspect_sql = f"""
SELECT row_id, pickup_location, dropoff_location, passenger_fare,
       driver_total_pay, trip_length, business
FROM {lab_table}
WHERE row_id IN {inspect_ids}
ORDER BY row_id
"""

lab_path = (
    spark.sql("DESCRIBE EXTERNAL LOCATION el_rideshare_dev")
    .select("url")
    .first()["url"]
    .rstrip("/")
    + "/external-tables/fare_dv_lab"
)

spark.sql(f"DROP TABLE IF EXISTS {lab_table}")
spark.sql(f"CONVERT TO DELTA parquet.`{lab_path}`")
spark.sql(
    f"""
    CREATE TABLE {lab_table}
    USING DELTA
    LOCATION '{lab_path}'
    """
)
spark.sql(
    f"""
    ALTER TABLE {lab_table}
    SET TBLPROPERTIES (
      'delta.enableDeletionVectors' = 'false',
      'delta.autoOptimize.autoCompact' = 'false'
    )
    """
)

display(spark.sql(inspect_sql))
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 — `UPDATE` without deletion vectors
# MAGIC
# MAGIC Set `passenger_fare` **51.57 → 55.00** on `row_id` **210049714452023**.
# MAGIC Spark rewrites the **whole** ~300 MB file. `LIST` can show the leftover
# MAGIC old file.

# COMMAND ----------

spark.sql(
    f"""
    UPDATE {lab_table}
    SET passenger_fare = 55.00
    WHERE row_id = 210049714452023
    """
)
display(spark.sql(inspect_sql))
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 — Same `UPDATE` with deletion vectors
# MAGIC
# MAGIC Enable deletion vectors, then set that row **55.00 → 60.00**. The large
# MAGIC file should stay. Expect a small new file and a `.bin` deletion vector.

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
    SET passenger_fare = 60.00
    WHERE row_id = 210049714452023
    """
)
display(spark.sql(inspect_sql))
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 — `DELETE` with deletion vectors
# MAGIC
# MAGIC Delete `row_id` **210049714452046**. The inspection query shows **3**
# MAGIC rows. The live Parquet file can still hold that row's bytes.

# COMMAND ----------

spark.sql(
    f"""
    DELETE FROM {lab_table}
    WHERE row_id = 210049714452046
    """
)
display(spark.sql(inspect_sql))
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4 — `VACUUM`
# MAGIC
# MAGIC `VACUUM` deletes files the table no longer uses. It does **not** remove
# MAGIC deletion-vector rows from live files. The leftover rewrite from Step 1
# MAGIC can go; files that still carry `.bin` marks remain.
# MAGIC
# MAGIC > **Warning:** `RETAIN 0 HOURS` can remove time-travel files immediately.
# MAGIC > Do not use it on production tables.

# COMMAND ----------

spark.conf.set(
    "spark.databricks.delta.retentionDurationCheck.enabled", "false"
)
spark.sql(f"VACUUM {lab_table} RETAIN 0 HOURS")
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5 — `REORG TABLE ... APPLY (PURGE)`
# MAGIC
# MAGIC This rewrites **current** files that still carry deletion vectors. After
# MAGIC it runs, the updated and deleted rows are gone from live data files.
# MAGIC Old files can remain until `VACUUM`.

# COMMAND ----------

spark.sql(f"REORG TABLE {lab_table} APPLY (PURGE)")
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT version, operation, operationParameters
# MAGIC FROM (DESCRIBE HISTORY rideshare_dev.processed.fare_dv_lab)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6 — `VACUUM` again
# MAGIC
# MAGIC Remove the files `REORG` replaced.

# COMMAND ----------

spark.sql(f"VACUUM {lab_table} RETAIN 0 HOURS")
display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC | Step | What happened |
# MAGIC | ---- | ------------- |
# MAGIC | 0 | Delta table on the existing ~300 MB Parquet folder |
# MAGIC | 1 | DV off → one-row `UPDATE` rewrites the whole file |
# MAGIC | 2 | DV on → large file stays; small file + `.bin` |
# MAGIC | 3 | `DELETE` **210049714452046** → **3** inspection rows; bytes can remain |
# MAGIC | 4 | `VACUUM` removes unused files, not live DV data |
# MAGIC | 5 | `REORG ... APPLY (PURGE)` rewrites current files that carry DVs |
# MAGIC | 6 | `VACUUM` removes the files `REORG` replaced |
# MAGIC
# MAGIC **Next:** `02 - Schema Enforcement and Evolution`.
