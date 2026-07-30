# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # 07 - Write Patterns and Table Preview
# MAGIC
# MAGIC Earlier notebooks wrote practice outputs with **`.mode("overwrite")`**.
# MAGIC This notebook goes deeper: save modes, a brief partitioned write, a
# MAGIC Delta **file** write under **`practice/`**, and a managed
# MAGIC **`saveAsTable`** into **`rideshare_dev.processed`**.
# MAGIC
# MAGIC **Files vs tables:** Volume paths under
# MAGIC **`/Volumes/rideshare_dev/processed/output_files/practice/`** are files
# MAGIC on the external volume. A managed table in **`rideshare_dev.processed`**
# MAGIC lives in the catalog's managed location — not the same as the external
# MAGIC volume. Deep Delta Lake → Module 10; UC grants → Module 11.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### What you will learn
# MAGIC
# MAGIC | Topic | What you will do |
# MAGIC |-------|------------------|
# MAGIC | Save modes | Compare `overwrite`, `append`, `ignore`, and `errorifexists` |
# MAGIC | Partitioned write | Write a small extract partitioned by a column |
# MAGIC | Delta file write | Write Delta under `practice/` on the external volume |
# MAGIC | Managed `saveAsTable` | Save into `rideshare_dev.processed` |
# MAGIC | Files vs tables | Contrast volume paths with managed table location |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Prerequisites.** Module 4 and Module 5 Notebooks **01–06** — landing
# MAGIC volume populated with **`trip_time/trip_time.parquet`**. Prior format
# MAGIC notebooks already used **`.mode("overwrite")`** on practice writes.
# MAGIC
# MAGIC **Source file:** `/Volumes/rideshare_dev/landing/source_files/trip_time/trip_time.parquet`
# MAGIC
# MAGIC **Write root:** `/Volumes/rideshare_dev/processed/output_files/practice/`
# MAGIC
# MAGIC **Compute:** Any cluster with PySpark. This notebook uses Volume paths
# MAGIC and Unity Catalog managed tables under **`rideshare_dev.processed`**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup
# MAGIC
# MAGIC Import PySpark helpers and set paths for the **`trip_time`** write demos.
# MAGIC
# MAGIC Course **`trip_time`** columns (from `docs/data/dataset-overview.md`):
# MAGIC **`trip_id`** (bigint), **`trip_date`** (date), **`hour_of_day`** (int).
# MAGIC
# MAGIC Practice outputs for this notebook:
# MAGIC **`write_modes_demo/`**, **`trip_time_partitioned/`**,
# MAGIC **`trip_time_delta_file/`**, plus managed table
# MAGIC **`rideshare_dev.processed.trip_time_preview`**.

# COMMAND ----------

from pyspark.sql import functions as F

landing_root = "/Volumes/rideshare_dev/landing/source_files"
trip_time_parquet_path = f"{landing_root}/trip_time/trip_time.parquet"
practice_root = "/Volumes/rideshare_dev/processed/output_files/practice"

save_modes_path = f"{practice_root}/write_modes_demo/"
partitioned_path = f"{practice_root}/trip_time_partitioned/"
delta_file_path = f"{practice_root}/trip_time_delta_file/"
managed_table = "rideshare_dev.processed.trip_time_preview"

print(f"trip_time_parquet_path = {trip_time_parquet_path}")
print(f"practice_root = {practice_root}")
print(f"managed_table = {managed_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Source path
# MAGIC
# MAGIC **`trip_time/trip_time.parquet`** was copied into the landing volume in
# MAGIC Notebook 01 and read in **04 - Reading Parquet**. Format notebooks in
# MAGIC this module read through **`/Volumes/...`** paths only.

# COMMAND ----------

display(dbutils.fs.ls(f"{landing_root}/trip_time"))

# COMMAND ----------

# MAGIC %md
# MAGIC You should see **`trip_time.parquet`** in that folder. Load it with an
# MAGIC explicit schema into **`write_source`** for the write demos below —
# MAGIC same production pattern as Notebook 04.

# COMMAND ----------

trip_time_schema_ddl = """
trip_id bigint,
trip_date date,
hour_of_day int
"""

trip_time = (
    spark.read.format("parquet")
    .schema(trip_time_schema_ddl)
    .load(trip_time_parquet_path)
)

write_source = trip_time.select(
    F.col("trip_id"),
    F.col("trip_date"),
    F.col("hour_of_day"),
)

print(f"write_source rows = {write_source.count()} (expect 100)")
write_source.printSchema()
write_source.show(3)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Save modes
# MAGIC
# MAGIC **`.mode(...)`** controls what happens when the output path already
# MAGIC exists. **`write`** is an **action** (Module 4) — each cell below
# MAGIC executes immediately.
# MAGIC
# MAGIC Prior notebooks defaulted to **`overwrite`** so re-runs replaced the
# MAGIC practice folder. Here you compare all four common modes on one path.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2a. `overwrite`
# MAGIC
# MAGIC Replace any existing files at the path.

# COMMAND ----------

(
    write_source.limit(5)
    .write.format("parquet")
    .mode("overwrite")
    .save(save_modes_path)
)

print("After overwrite (expect 5 rows):")
print(spark.read.format("parquet").load(save_modes_path).count())
display(dbutils.fs.ls(save_modes_path))

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2b. `append`
# MAGIC
# MAGIC Add another batch of files alongside what is already there. Row count
# MAGIC grows — useful for incremental loads, risky if you re-run the same
# MAGIC batch by accident.

# COMMAND ----------

(
    write_source.limit(5)
    .write.format("parquet")
    .mode("append")
    .save(save_modes_path)
)

print("After append (expect 10 rows if you ran overwrite once, then append once):")
print(spark.read.format("parquet").load(save_modes_path).count())

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2c. `ignore`
# MAGIC
# MAGIC If the path already has data, **do nothing** — no error, no update.

# COMMAND ----------

count_before_ignore = spark.read.format("parquet").load(save_modes_path).count()

(
    write_source.limit(3)
    .write.format("parquet")
    .mode("ignore")
    .save(save_modes_path)
)

count_after_ignore = spark.read.format("parquet").load(save_modes_path).count()
print(f"Before ignore: {count_before_ignore}")
print(f"After ignore:  {count_after_ignore} (unchanged when path already exists)")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2d. `errorifexists`
# MAGIC
# MAGIC Fail if the path already exists. Use this when a re-run should be loud
# MAGIC instead of silently appending or overwriting. Spark also accepts
# MAGIC **`"error"`** as an alias.

# COMMAND ----------

print("errorifexists when path exists (expect failure):")
try:
    (
        write_source.limit(1)
        .write.format("parquet")
        .mode("errorifexists")
        .save(save_modes_path)
    )
except Exception as exc:
    print(f"{type(exc).__name__}: {str(exc)[:400]}")

# COMMAND ----------

# MAGIC %md
# MAGIC | Mode | If path exists |
# MAGIC |------|----------------|
# MAGIC | **`overwrite`** | Replace contents |
# MAGIC | **`append`** | Add more files / rows |
# MAGIC | **`ignore`** | Leave existing data alone |
# MAGIC | **`errorifexists`** / **`error`** | Raise an error |
# MAGIC
# MAGIC Production tip: prefer an intentional mode every time — never rely on the
# MAGIC default if you care about idempotent re-runs.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Brief partitioned write
# MAGIC
# MAGIC **`.partitionBy("hour_of_day")`** lays out folders like
# MAGIC **`hour_of_day=8/`** under the output path. Partitioning is a layout
# MAGIC choice for selective reads later — this module only shows the write.

# COMMAND ----------

(
    write_source.write.format("parquet")
    .mode("overwrite")
    .partitionBy("hour_of_day")
    .save(partitioned_path)
)

print(f"Wrote partitioned Parquet to {partitioned_path}")
display(dbutils.fs.ls(partitioned_path))

# COMMAND ----------

# MAGIC %md
# MAGIC You should see directories named **`hour_of_day=<value>`**. Reading the
# MAGIC parent folder still returns all rows; Spark discovers partitions from
# MAGIC the directory names.

# COMMAND ----------

partitioned_read = spark.read.format("parquet").load(partitioned_path)

print("Schema after partitioned read:")
partitioned_read.printSchema()
print(f"Row count: {partitioned_read.count()} (expect 100)")
partitioned_read.groupBy("hour_of_day").count().orderBy("hour_of_day").show(10)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Delta file write under `practice/`
# MAGIC
# MAGIC Write Delta as a **file format** to the external volume — same
# MAGIC **`/Volumes/.../practice/`** pattern as Parquet/JSON, but with
# MAGIC **`format("delta")`**. This is a preview only: ACID, **`MERGE`**, and
# MAGIC time travel belong in Module 10.
# MAGIC
# MAGIC Delta does not replace every file format — Module 5 still uses CSV,
# MAGIC JSON, Parquet, XML, and Avro for landing and practice writes.

# COMMAND ----------

(
    write_source.write.format("delta")
    .mode("overwrite")
    .save(delta_file_path)
)

print(f"Wrote Delta files to {delta_file_path}")
display(dbutils.fs.ls(delta_file_path))

# COMMAND ----------

delta_from_path = spark.read.format("delta").load(delta_file_path)

print("Re-read Delta from Volume path:")
delta_from_path.printSchema()
print(f"Row count: {delta_from_path.count()}")
delta_from_path.show(3)

# COMMAND ----------

# MAGIC %md
# MAGIC Notice **`_delta_log/`** in the directory listing — that is Delta's
# MAGIC transaction log on the volume. The data still lives as files under
# MAGIC **`practice/`**, not as a catalog table yet.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Managed `saveAsTable` into `rideshare_dev.processed`
# MAGIC
# MAGIC **`saveAsTable`** registers a **managed** table in Unity Catalog. The
# MAGIC files go to the catalog's **managed location** (created in Notebook 01),
# MAGIC which is **not** the external **`output_files`** volume.

# COMMAND ----------

spark.sql(f"DROP TABLE IF EXISTS {managed_table}")

(
    write_source.write.format("delta")
    .mode("overwrite")
    .saveAsTable(managed_table)
)

print(f"Created managed table {managed_table}")

# COMMAND ----------

display(spark.sql(f"DESCRIBE EXTENDED {managed_table}"))

# COMMAND ----------

# MAGIC %md
# MAGIC In the **`DESCRIBE EXTENDED`** output, find **`Type`** / **`Location`**
# MAGIC (wording can vary slightly by runtime). The location should point at
# MAGIC managed storage under the catalog — not
# MAGIC **`/Volumes/rideshare_dev/processed/output_files/...`**.
# MAGIC
# MAGIC Re-runs: **`DROP TABLE IF EXISTS`** above keeps this notebook idempotent.
# MAGIC Notebook **99** Level 4 drops the whole **`rideshare_dev`** catalog
# MAGIC (including managed tables). Level 1 only clears **`practice/`** files.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Files vs tables
# MAGIC
# MAGIC Same logical rows, two homes: a Delta **path** on the external volume,
# MAGIC and a managed **table** in **`rideshare_dev.processed`**.

# COMMAND ----------

print("Delta FILE on external volume:")
print(f"  path = {delta_file_path}")
print(f"  rows = {spark.read.format('delta').load(delta_file_path).count()}")

print("\nManaged TABLE in Unity Catalog:")
print(f"  name = {managed_table}")
print(f"  rows = {spark.table(managed_table).count()}")

print("\nQuery the table with the DataFrame API:")
spark.table(managed_table).show(3)

# COMMAND ----------

# MAGIC %md
# MAGIC | | Delta file under `practice/` | Managed `saveAsTable` |
# MAGIC |---|------------------------------|------------------------|
# MAGIC | How you address it | Volume path string | Catalog.schema.table |
# MAGIC | Storage | External volume (`output_files`) | Catalog managed location |
# MAGIC | Governance | Path permissions on the volume | UC table privileges (Module 11) |
# MAGIC | Deep Delta features | Module 10 | Module 10 |
# MAGIC
# MAGIC Both can use the Delta format. The important Module 5 takeaway is
# MAGIC **where** the data lives and **how** you name it.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Build a second write preview without reusing the worked-output paths
# MAGIC above:
# MAGIC
# MAGIC 1. From **`write_source`** (or a fresh read of **`trip_time.parquet`**),
# MAGIC    **`select`** **`trip_id`** and **`trip_date`** only.
# MAGIC 2. Write that extract as Parquet to
# MAGIC    **`/Volumes/rideshare_dev/processed/output_files/practice/trip_date_exercise/`**
# MAGIC    with **`.mode("overwrite")`** and **`.partitionBy("trip_date")`**.
# MAGIC 3. List the partition folders with **`dbutils.fs.ls`**.
# MAGIC 4. Write the same two-column extract as a managed Delta table named
# MAGIC    **`rideshare_dev.processed.trip_date_preview`** (drop it first if it
# MAGIC    exists), then **`show(3)`** via **`spark.table(...)`**.

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - **Save modes** — **`overwrite`**, **`append`**, **`ignore`**,
# MAGIC   **`errorifexists`** control re-run behavior; **`write`** is an action
# MAGIC - **Partitioned write** — **`.partitionBy(...)`** creates
# MAGIC   **`column=value/`** folders under **`practice/`**
# MAGIC - **Delta file write** — **`format("delta").save(volume_path)`** stores
# MAGIC   Delta on the external volume (preview only; deep Delta → Module 10).
# MAGIC   Delta does not replace CSV/JSON/Parquet/Avro for every use case
# MAGIC - **Managed `saveAsTable`** — registers a table in
# MAGIC   **`rideshare_dev.processed`**; managed location ≠ external volume
# MAGIC - **Files vs tables** — path-based files vs catalog-governed tables
# MAGIC   (UC grants → Module 11)
# MAGIC
# MAGIC **Next:** Module 6 — systematic transforms (including **`explode`** on
# MAGIC **`drivers`**). Use **99 - Rideshare Project Cleanup and Reset** when you
# MAGIC need to clear **`practice/`** or tear down the project.
