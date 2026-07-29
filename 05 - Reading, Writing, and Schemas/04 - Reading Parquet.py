# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # 04 - Reading Parquet
# MAGIC
# MAGIC Parquet is a columnar file format widely used in data lakes and lakehouses.
# MAGIC In this notebook, we read the **`trip_time`** dataset — stored as Parquet in
# MAGIC the landing volume.
# MAGIC
# MAGIC **Key difference from CSV and JSON:** Parquet embeds schema and type metadata
# MAGIC in the file. Spark reads column names and types without inference, but an
# MAGIC explicit schema is still useful for validation and production contracts.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### What you will learn
# MAGIC
# MAGIC | Topic | What you will do |
# MAGIC |-------|------------------|
# MAGIC | Read Parquet | Load **`trip_time`** from a Volume path |
# MAGIC | Two read syntaxes | `.parquet(path)` shorthand vs `format("parquet").load(path)` |
# MAGIC | Embedded schema | Inspect with `printSchema()`, a sample row, and row count |
# MAGIC | Explicit schemas | Apply DDL string and `StructType` schemas for validation |
# MAGIC | Light reshape | Select and rename columns after read |
# MAGIC | Write Parquet | Save a practice output under `practice/` |
# MAGIC | Round-trip test | Re-read written Parquet and confirm schema |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Prerequisites.** Module 4, **01 - Unity Catalog Volumes and Data
# MAGIC Landing**, and **02 - Reading CSV** / **03 - Reading JSON** — landing
# MAGIC volume populated with **`trip_time/trip_time.parquet`**.
# MAGIC
# MAGIC **Source file:** `/Volumes/rideshare_dev/landing/source_files/trip_time/trip_time.parquet`
# MAGIC
# MAGIC **Compute:** Any cluster with PySpark. This notebook uses Volume paths only.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup
# MAGIC
# MAGIC Import PySpark helpers and set paths for the **`trip_time`** dataset.
# MAGIC
# MAGIC Course **`trip_time`** columns (from `docs/data/dataset-overview.md`):
# MAGIC **`trip_id`** (bigint), **`trip_date`** (date), **`hour_of_day`** (int).

# COMMAND ----------

# TODO: imports, landing_root, trip_time_parquet_path, practice paths

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Source path
# MAGIC
# MAGIC **`trip_time/trip_time.parquet`** was copied into the landing volume in
# MAGIC Notebook 01. Format notebooks in this module read through **`/Volumes/...`**
# MAGIC paths only.

# COMMAND ----------

# TODO: list landing/source_files/trip_time and confirm trip_time.parquet

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Parquet format
# MAGIC
# MAGIC Parquet stores data **column-by-column** with embedded schema metadata.
# MAGIC Contrast with row-oriented CSV and line-delimited JSON from earlier notebooks.

# COMMAND ----------

# TODO: brief note or peek at file metadata if useful for teaching

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Read syntax — shorthand vs generic
# MAGIC
# MAGIC Spark exposes two equivalent ways to read Parquet:

# COMMAND ----------

# TODO: spark.read.parquet(...) vs spark.read.format("parquet").load(...)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Read and inspect
# MAGIC
# MAGIC Load **`trip_time`** and verify schema, sample rows, and row count.

# COMMAND ----------

# TODO: read, printSchema(), display/show, count()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Explicit schema
# MAGIC
# MAGIC Even though Parquet carries schema metadata, apply an explicit schema
# MAGIC (DDL string or **`StructType`**) for production validation.

# COMMAND ----------

# TODO: trip_time_schema_ddl, trip_time_schema StructType, read with schema

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Light reshape
# MAGIC
# MAGIC Select and rename columns — minimal reshape before a practice write.

# COMMAND ----------

# TODO: select/rename example on trip_time

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Parquet round trip
# MAGIC
# MAGIC Write reshaped output to **`/Volumes/rideshare_dev/processed/output_files/practice/`**
# MAGIC and re-read to confirm the written schema.

# COMMAND ----------

# TODO: write with format("parquet").save(...) or .parquet(...), re-read

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC TODO: hands-on task — read **`trip_time`**, reshape, write to a new
# MAGIC **`practice/`** path, re-read with explicit schema.

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC TODO: recap Parquet read/write patterns and pointer to **05 - Reading XML**.
