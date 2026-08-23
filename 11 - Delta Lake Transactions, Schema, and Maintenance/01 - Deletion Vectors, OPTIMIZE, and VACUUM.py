# Databricks notebook source
# MAGIC %md
# MAGIC # 01 - Deletion Vectors, OPTIMIZE, and VACUUM
# MAGIC
# MAGIC Module 10 showed a one-row fare `UPDATE` and leftover files on disk. This
# MAGIC notebook names **deletion vectors**, then uses **`OPTIMIZE`** and
# MAGIC **`VACUUM`** so frequent fare corrections stay cheap without leaving a
# MAGIC pile of tiny files.
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC - Show that one `UPDATE` without deletion vectors rewrites the whole data
# MAGIC   file, and that the same kind of `UPDATE` with deletion vectors on writes
# MAGIC   a small new file instead
# MAGIC - Show that `VACUUM` cannot remove files the current table still uses
# MAGIC - Compact live small files with `OPTIMIZE`, then `VACUUM` unused files
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
# MAGIC ## Setup
# MAGIC Same four-row extract as Module 10. Reset the folder. Deletion vectors
# MAGIC **off**. Ignore `.crc` files in listings.

# COMMAND ----------

from decimal import Decimal

from pyspark.sql.types import (
    DecimalType,
    LongType,
    StringType,
    StructField,
    StructType,
)

maint_path = (
    "/Volumes/rideshare_dev/processed/output_files/practice/"
    "fare_maint_lab/"
)

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


def show_data_files(folder: str) -> None:
    listing = dbutils.fs.ls(folder)
    data_files = [
        item
        for item in listing
        if not item.name.endswith(".crc") and not item.name.startswith("_")
    ]
    print(f"data file count = {len(data_files)}")
    for item in data_files:
        print(f"{item.name}  {item.size} bytes")
    display(listing)


dbutils.fs.rm(maint_path, True)
(
    trips_extract.write.format("delta")
    .mode("overwrite")
    .option("delta.enableDeletionVectors", "false")
    .save(maint_path)
)

print(f"maint_path = {maint_path}")
print("rows in extract =", trips_extract.count())
display(trips_extract.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Baseline — one data file
# MAGIC Note the file **size**. You should see **one** data file and **4** rows.
# MAGIC Trip **1003** tip is **6.00**.

# COMMAND ----------

print("After setup (deletion vectors off):")
show_data_files(maint_path)
baseline = spark.read.format("delta").load(maint_path)
print(f"rows = {baseline.count()} (expect 4)")
display(baseline.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1) `UPDATE` without deletion vectors
# MAGIC You already did this kind of `UPDATE` in Module 10. One change **rewrites
# MAGIC the whole file**. The leftover old file on disk is expected. Here, look at
# MAGIC the **size** of the new file.

# COMMAND ----------

spark.sql(
    f"""
    UPDATE delta.`{maint_path}`
    SET tip_amount = 10.00
    WHERE trip_id = 1003
    """
)

# COMMAND ----------

print("After UPDATE 1003 → 10.00 (deletion vectors off):")
show_data_files(maint_path)
after_full_rewrite = spark.read.format("delta").load(maint_path)
print(f"rows = {after_full_rewrite.count()} (expect 4)")
display(after_full_rewrite.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2) Same kind of `UPDATE` with deletion vectors on
# MAGIC Turn deletion vectors **on**. Change trip **1003** again. Spark leaves the
# MAGIC existing file in place, marks the old row, and writes a **small** new
# MAGIC file for the new tip. Compare that size to step 1.

# COMMAND ----------

spark.sql(
    f"""
    ALTER TABLE delta.`{maint_path}`
    SET TBLPROPERTIES ('delta.enableDeletionVectors' = 'true')
    """
)

# COMMAND ----------

spark.sql(
    f"""
    UPDATE delta.`{maint_path}`
    SET tip_amount = 12.00
    WHERE trip_id = 1003
    """
)

# COMMAND ----------

print("After UPDATE 1003 → 12.00 (deletion vectors on):")
show_data_files(maint_path)
after_dv = spark.read.format("delta").load(maint_path)
print(f"rows = {after_dv.count()} (expect 4)")
display(after_dv.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3) Keep updating — more live files
# MAGIC Two more fare corrections. Each `UPDATE` can add another small file. The
# MAGIC table **still needs all of them**. Count the files — this is the small-file
# MAGIC problem.

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

# COMMAND ----------

print("After UPDATE 1001 → 4.00 and 1004 → 3.50:")
show_data_files(maint_path)
after_more = spark.read.format("delta").load(maint_path)
print(f"rows = {after_more.count()} (expect 4)")
display(after_more.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4) `VACUUM` cannot delete files the table still uses
# MAGIC Those small files are the current table. `VACUUM` will not remove them —
# MAGIC even with `RETAIN 0`.

# COMMAND ----------

spark.conf.set(
    "spark.databricks.delta.retentionDurationCheck.enabled", "false"
)
spark.sql(f"VACUUM delta.`{maint_path}` RETAIN 0 HOURS")

# COMMAND ----------

print("After VACUUM (before OPTIMIZE):")
show_data_files(maint_path)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5) `OPTIMIZE` merges live small files
# MAGIC `OPTIMIZE` reads the live small files and writes fewer larger files (on
# MAGIC this extract, often **one**). The table now points at that new file. The
# MAGIC old small files are no longer the current table, but they may still sit
# MAGIC on disk.

# COMMAND ----------

# One-row history lookup for the proof cell after VACUUM; this does not scale.
pre_optimize_version = (
    spark.sql(f"DESCRIBE HISTORY delta.`{maint_path}`")
    .selectExpr("max(version) AS v")
    .collect()[0]["v"]
)
print(f"version before OPTIMIZE = {pre_optimize_version}")
spark.sql(f"OPTIMIZE delta.`{maint_path}`")

# COMMAND ----------

print("After OPTIMIZE:")
show_data_files(maint_path)
after_optimize = spark.read.format("delta").load(maint_path)
print(f"rows = {after_optimize.count()} (expect 4)")
display(after_optimize.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6) `VACUUM` after `OPTIMIZE`
# MAGIC Module 10 used **7** days. This lab uses **`RETAIN 0 HOURS`** so you see
# MAGIC leftover files disappear in this notebook. Time travel to those versions
# MAGIC is lost **on purpose**. Never use `RETAIN 0` on a real table.

# COMMAND ----------

spark.sql(f"VACUUM delta.`{maint_path}` RETAIN 0 HOURS")

# COMMAND ----------

print("After VACUUM (after OPTIMIZE):")
show_data_files(maint_path)

# COMMAND ----------

# MAGIC %md
# MAGIC You used `VERSION AS OF` in Module 10. The next cell reads the version
# MAGIC from **before** `OPTIMIZE`. It is expected to **fail** — those files are
# MAGIC gone.
# MAGIC
# MAGIC > **Warning:** `RETAIN 0 HOURS` is for this lab only.

# COMMAND ----------

spark.sql(
    f"""
    SELECT * FROM delta.`{maint_path}`
    VERSION AS OF {pre_optimize_version}
    """
)  # Expected: SparkException

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - Without deletion vectors, one `UPDATE` **rewrites the whole file**. With
# MAGIC   them on, the same kind of change writes a **small** new file
# MAGIC - `VACUUM` cannot delete files the **current** table still uses
# MAGIC - `OPTIMIZE` merges live small files; `VACUUM` then deletes the leftovers
# MAGIC
# MAGIC **Next:** the rest of Module 11 (not in this notebook).
