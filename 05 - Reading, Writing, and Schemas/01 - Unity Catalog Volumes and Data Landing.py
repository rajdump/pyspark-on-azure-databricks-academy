# Databricks notebook source
# MAGIC %md
# MAGIC # Unity Catalog Volumes and Data Landing
# MAGIC
# MAGIC Module 5 begins file-based work on the shared rideshare dataset. Before
# MAGIC reading CSV, JSON, Parquet, XML, or Avro in later notebooks, land the course
# MAGIC data on Unity Catalog Volumes under **`academy.rideshare`**.
# MAGIC
# MAGIC **Learning objectives.** After this notebook, you will be able to:
# MAGIC - Explain how catalog, schema, and volume fit together for governed file
# MAGIC   storage in this course lab
# MAGIC - Create **`raw`**, **`processed`**, and **`source`** volumes when they do
# MAGIC   not already exist (under the existing **`el_lab`** external location)
# MAGIC - Create dataset folders with **`dbutils.fs.mkdirs`**
# MAGIC - Copy repo source files into Volume paths and verify they landed
# MAGIC
# MAGIC **Prerequisites.** Module 4 — Transformations, Actions, and Lazy Evaluation.
# MAGIC
# MAGIC **Setup.** Attach classic all-purpose compute with PySpark and Unity Catalog
# MAGIC access. Learner paths use Volume URLs only — not long **`abfss://`** strings.
# MAGIC
# MAGIC Shared lab constants and repo → Volume paths:
# MAGIC **`docs/data/dataset-overview.md`** (Physical layout — **`academy`** /
# MAGIC **`rideshare`**, volumes **`raw`** / **`processed`** / **`source`**, datasets
# MAGIC **`trip`**, **`trip_time`**, **`zone_lookup`**, **`payment`**, **`drivers`**).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Unity Catalog awareness
# MAGIC
# MAGIC Brief orientation: catalog **`academy`**, schema **`rideshare`**, and the
# MAGIC three volume roles (**`raw`**, **`processed`**, **`source`**).
# MAGIC
# MAGIC Prerequisite callout: external location **`el_lab`** already exists in this
# MAGIC lab. Storage credentials, external-location design, and grants are Module 11.

# COMMAND ----------

# TODO: Show current catalog/schema context (e.g. USE statements or spark.catalog).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create volumes
# MAGIC
# MAGIC Create **`raw`**, **`processed`**, and **`source`** volumes with
# MAGIC **`CREATE VOLUME IF NOT EXISTS`** when missing, using **`LOCATION`** under
# MAGIC the existing **`el_lab`** subpath for Academy.

# COMMAND ----------

# TODO: CREATE VOLUME IF NOT EXISTS for raw, processed, and source.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prepare folder structure
# MAGIC
# MAGIC Create dataset subfolders under each volume with **`dbutils.fs.mkdirs`**.

# COMMAND ----------

# TODO: mkdirs for raw/{trip,trip_time,zone_lookup,drivers,payment} and source/payment.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Upload course data from the repo
# MAGIC
# MAGIC Copy Git repo files into the Volume paths from the dataset-overview Physical
# MAGIC layout table. The Git folder path in Databricks depends on how this repo is
# MAGIC attached — use the course repo root, not a local laptop path.

# COMMAND ----------

# TODO: Copy repo files into Volume destinations (dbutils.fs.cp or equivalent).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify landed files
# MAGIC
# MAGIC List each target folder and confirm expected files are present before the
# MAGIC format-read notebooks.

# COMMAND ----------

# TODO: dbutils.fs.ls (or equivalent) on each raw/ and source/payment path.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC TODO: Short hands-on task — e.g. list one Volume path, confirm file count or
# MAGIC name, or add one mkdir + verify step on a practice subfolder.

# COMMAND ----------

# TODO: Exercise starter / solution placeholder.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC TODO: Recap catalog/schema/volume setup, mkdirs, repo copy, and verify.
# MAGIC
# MAGIC **Next up:** **Azure SQL Load and Extract** — **`payment`** seed from
# MAGIC **`source/payment/`**, JDBC to **`el_lab.payments`**, Avro to **`raw/payment/`**.
