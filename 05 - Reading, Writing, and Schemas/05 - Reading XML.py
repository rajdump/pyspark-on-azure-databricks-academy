# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # 05 - Reading XML
# MAGIC
# MAGIC XML still appears in vendor feeds and legacy system exports. In this
# MAGIC notebook, we read the supplementary **`drivers`** dataset — nested XML
# MAGIC landed in the volume in Notebook 01.
# MAGIC
# MAGIC **Key difference from CSV / JSON / Parquet:** the XML reader needs
# MAGIC **`rowTag`** to know which element is one row. Nested fields
# MAGIC (**`vehicle`**, **`trips_assigned`**) stay nested here — **`explode()`**
# MAGIC is Module 6.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### What you will learn
# MAGIC
# MAGIC | Topic | What you will do |
# MAGIC |-------|------------------|
# MAGIC | Read XML | Load **`drivers`** from a Volume path with **`rowTag`** |
# MAGIC | `rowTag` | See why the option is required |
# MAGIC | Inspect nested schema | `printSchema()`, sample rows, row count |
# MAGIC | Nested columns | Inspect **`vehicle`** and **`trips_assigned`** without **`explode`** |
# MAGIC | Light reshape | Select top-level fields for a practice write |
# MAGIC | Write practice output | Save under `practice/` and re-read |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Prerequisites.** Module 4, **01 - Unity Catalog Volumes and Data
# MAGIC Landing**, and prior Module 5 format notebooks — landing volume populated
# MAGIC with **`drivers/drivers.xml`**.
# MAGIC
# MAGIC **Source file:** `/Volumes/rideshare_dev/landing/source_files/drivers/drivers.xml`
# MAGIC
# MAGIC **Compute:** Any cluster with PySpark. This notebook uses Volume paths only.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup
# MAGIC
# MAGIC Import PySpark helpers and set paths for the **`drivers`** dataset.
# MAGIC
# MAGIC Course **`drivers`** fields (from `docs/data/dataset-overview.md`):
# MAGIC **`driver_id`** (string), **`name`** (string), **`license_number`**
# MAGIC (string), **`vehicle`** (struct: make, model, year, body_type),
# MAGIC **`trips_assigned`** (repeated **`trip_id`** list).

# COMMAND ----------

# TODO: imports, landing_root, drivers_xml_path, practice paths

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Source path
# MAGIC
# MAGIC **`drivers/drivers.xml`** was copied into the landing volume in Notebook 01.
# MAGIC Format notebooks in this module read through **`/Volumes/...`** paths only.

# COMMAND ----------

# TODO: list landing/source_files/drivers and confirm drivers.xml

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. XML layout and `rowTag`
# MAGIC
# MAGIC Peek at the file structure. Each **`<driver>`** element is one record;
# MAGIC **`rowTag`** tells Spark that root wrapping element is not the row.

# COMMAND ----------

# TODO: dbutils.fs.head peek; explain rowTag = "driver"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Read with `rowTag`
# MAGIC
# MAGIC Read **`drivers.xml`** using **`format("xml")`** and **`.option("rowTag", ...)`**.
# MAGIC README boundary: **`rowTag` only — no `explode`**.

# COMMAND ----------

# TODO: spark.read.format("xml").option("rowTag", "driver").load(...)
# TODO: optional contrast — read without rowTag (expect failure / unusable result)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Inspect schema and nested columns
# MAGIC
# MAGIC Confirm row count (expect 12), and inspect nested **`vehicle`** /
# MAGIC **`trips_assigned`** with **`printSchema()`** and **`show`** — do not
# MAGIC flatten with **`explode`**.

# COMMAND ----------

# TODO: printSchema(), show, count(); inspect nested fields only

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Light reshape
# MAGIC
# MAGIC Select top-level columns (and optionally nested field access with
# MAGIC **`vehicle.make`**-style paths) — no **`explode`** on **`trips_assigned`**.

# COMMAND ----------

# TODO: select / nested field access example

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Practice write
# MAGIC
# MAGIC Write a reshaped extract under
# MAGIC **`/Volumes/rideshare_dev/processed/output_files/practice/`** and re-read
# MAGIC (JSON or Parquet practice output is fine — XML write is optional).

# COMMAND ----------

# TODO: write practice output; re-read to confirm

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC TODO: hands-on task — read **`drivers`** with **`rowTag`**, select a small
# MAGIC top-level subset (no **`explode`**), write to a new **`practice/`** path,
# MAGIC re-read and print schema.

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC TODO: recap XML **`rowTag`** read, nested columns without **`explode`**,
# MAGIC pointer to **06 - Reading Avro**.
