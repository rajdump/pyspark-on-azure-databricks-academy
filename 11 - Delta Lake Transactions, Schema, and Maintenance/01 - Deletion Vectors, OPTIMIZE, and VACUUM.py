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
# MAGIC - `/Volumes/rideshare_dev/processed/output_files/practice/fare_maint_lab/`
# MAGIC
# MAGIC **Prerequisites:** Module 10 notebooks `01`–`04`. Module 5
# MAGIC `01 - Unity Catalog Volumes and Data Landing.py` (catalog,
# MAGIC `processed.output_files`).
# MAGIC
# MAGIC This notebook does **not** teach ACID, schema evolution, `MERGE`, liquid
# MAGIC clustering, Change Data Feed, or a table-properties tour.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 0) Baseline
# MAGIC Same four-row extract as Module 10. Deletion vectors **off**. One data file.

# COMMAND ----------

from decimal import Decimal

maint_path = (
    "/Volumes/rideshare_dev/processed/output_files/practice/"
    "fare_maint_lab/"
)

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

dbutils.fs.rm(maint_path, True)
(
    trips_extract.write.format("delta")
    .mode("overwrite")
    .option("delta.enableDeletionVectors", "false")
    .save(maint_path)
)

print(f"maint_path = {maint_path}")
display(dbutils.fs.ls(maint_path))
display(spark.read.format("delta").load(maint_path).orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1) Without deletion vectors
# MAGIC One row `UPDATE` rewrites the whole file.

# COMMAND ----------

spark.sql(
    f"""
    UPDATE delta.`{maint_path}`
    SET tip_amount = 10.00
    WHERE trip_id = 1003
    """
)
display(dbutils.fs.ls(maint_path))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2) With deletion vectors
# MAGIC Turn them on and `UPDATE` the same trip. The existing data file stays. A
# MAGIC small new file holds the change.

# COMMAND ----------

spark.sql(
    f"""
    ALTER TABLE delta.`{maint_path}`
    SET TBLPROPERTIES ('delta.enableDeletionVectors' = 'true')
    """
)
spark.sql(
    f"""
    UPDATE delta.`{maint_path}`
    SET tip_amount = 12.00
    WHERE trip_id = 1003
    """
)
display(dbutils.fs.ls(maint_path))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3) Repeated changes leave live files
# MAGIC Two more `UPDATE`s. The table still needs every file you see.

# COMMAND ----------

spark.sql(
    f"""
    UPDATE delta.`{maint_path}`
    SET tip_amount = 4.00
    WHERE trip_id = 1001
    """
)
spark.sql(
    f"""
    UPDATE delta.`{maint_path}`
    SET tip_amount = 3.50
    WHERE trip_id = 1004
    """
)
display(dbutils.fs.ls(maint_path))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4) `VACUUM` is not compaction
# MAGIC If there are many small files, `VACUUM` is not the fix. It cannot remove
# MAGIC files the current table still uses.

# COMMAND ----------

spark.conf.set(
    "spark.databricks.delta.retentionDurationCheck.enabled", "false"
)
spark.sql(f"VACUUM delta.`{maint_path}` RETAIN 0 HOURS")
display(dbutils.fs.ls(maint_path))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5) `OPTIMIZE` fixes the live layout
# MAGIC `OPTIMIZE` rewrites the current files into fewer files.

# COMMAND ----------

spark.sql(f"OPTIMIZE delta.`{maint_path}`")
display(dbutils.fs.ls(maint_path))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6) `VACUUM` removes obsolete files
# MAGIC Those replaced files are no longer the current table, so `VACUUM` can
# MAGIC delete them. This lab uses `RETAIN 0 HOURS` so you see it now. Do not do
# MAGIC that on a real table — versions that needed those files stop working.

# COMMAND ----------

spark.sql(f"VACUUM delta.`{maint_path}` RETAIN 0 HOURS")
display(dbutils.fs.ls(maint_path))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - **Deletion vectors** → cheaper row-level changes
# MAGIC - **`OPTIMIZE`** → improve current file layout
# MAGIC - **`VACUUM`** → remove obsolete files
# MAGIC
# MAGIC **Next:** the rest of Module 11 (not in this notebook).
