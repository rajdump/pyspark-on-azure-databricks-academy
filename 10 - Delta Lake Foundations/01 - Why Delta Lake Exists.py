# Databricks notebook source
# MAGIC %md
# MAGIC # 01 - Why Delta Lake Exists
# MAGIC
# MAGIC Module 5 wrote Parquet and a Delta **folder**. This notebook is the first
# MAGIC **row change**: a one-row tip correction on a four-row handmade extract.
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC - Show why correcting one row in Parquet means rewriting the files
# MAGIC - Apply the same correction as a Delta `UPDATE`
# MAGIC - Confirm Delta still stores Parquet plus a `_delta_log` folder (do not
# MAGIC   open the JSON)
# MAGIC
# MAGIC **Reads:** none of the 100-row source files or teaching tables
# MAGIC (`trip_enriched`, KPIs, `curated/`)
# MAGIC
# MAGIC **Writes:**
# MAGIC - `/Volumes/rideshare_dev/processed/output_files/practice/fare_correction_parquet/`
# MAGIC - `/Volumes/rideshare_dev/processed/output_files/practice/fare_correction_delta/`
# MAGIC
# MAGIC Do **not** touch `fare_log_delta/` (notebook 02). No `saveAsTable`.
# MAGIC
# MAGIC **Prerequisites:** Module 5 `01 - Unity Catalog Volumes and Data Landing.py`
# MAGIC (catalog, `processed.output_files`) and
# MAGIC `07 - Write Patterns and Table Preview.py` (Parquet vs Delta folder).
# MAGIC
# MAGIC This notebook does **not** teach ACID, time travel, `DESCRIBE HISTORY`,
# MAGIC JSON action names, `DELETE`, `MERGE`, `VACUUM`, or deletion vectors.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup
# MAGIC
# MAGIC Isolated practice folders. Schema and four rows come from the Module 10
# MAGIC README extract (`trip_id` **1001–1004**). Do not write Delta yet.

# COMMAND ----------

# TODO: paths, schema, F — parquet and delta folders only; not fare_log_delta/

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write four rows as Parquet
# MAGIC
# MAGIC Original extract: **1003** tip is **6.00**. After write: **4** rows, part
# MAGIC files, **no** `_delta_log`.

# COMMAND ----------

# TODO: write 4 rows as Parquet; ls; confirm count 4 and tip 6.00 on 1003

# COMMAND ----------

# MAGIC %md
# MAGIC ## Business requirement — correct trip 1003
# MAGIC
# MAGIC Set **1003** tip to **10.00**. Keep **4** rows.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parquet update — read, modify, overwrite
# MAGIC
# MAGIC Read → `when` / `otherwise` → overwrite the same path.

# COMMAND ----------

# TODO: Parquet read / when / overwrite; confirm 4 rows, 1003 is 10.00, still no _delta_log

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parquet limitations
# MAGIC
# MAGIC No transactional `UPDATE`. No log. No separate table state. Failed or
# MAGIC overlapping writes can leave a bad folder.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Same data as Delta
# MAGIC
# MAGIC Write the **original** four rows (tip **6.00**) with `format("delta")`
# MAGIC overwrite. Deletion vectors **off**. `ls`: data files plus `_delta_log/`.
# MAGIC Do **not** name `add` / `remove`.

# COMMAND ----------

# TODO: write original 4 rows as Delta (DV off); ls data files and _delta_log

# COMMAND ----------

# MAGIC %md
# MAGIC ## Delta `UPDATE`
# MAGIC
# MAGIC `UPDATE ... SET tip_amount = 10.00 WHERE trip_id = 1003` on
# MAGIC `` delta.`<path>` ``. Delta did not edit a row inside a Parquet file.

# COMMAND ----------

# TODO: path UPDATE for trip 1003

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify
# MAGIC
# MAGIC **4** rows; **1003** is **10.00**.

# COMMAND ----------

# TODO: read Delta path; confirm count and tip

# COMMAND ----------

# MAGIC %md
# MAGIC ## Glance at files
# MAGIC
# MAGIC `ls` data files and `_delta_log` (more than one JSON after `UPDATE`).
# MAGIC Data is still Parquet; leftover files may remain. Do **not** open JSON.
# MAGIC JSON → notebook 02.

# COMMAND ----------

# TODO: ls data files and _delta_log

# COMMAND ----------

# MAGIC %md
# MAGIC ## Volume folders vs managed tables
# MAGIC
# MAGIC This lab uses Volume folders so `ls` works. Managed tables such as
# MAGIC `trip_enriched` are also Delta; files live in the catalog managed
# MAGIC location (`abfss://`). Do not change teaching tables.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC `UPDATE` **1001** tip **3.00 → 4.00**. Still **4** rows.

# COMMAND ----------

# TODO: learner UPDATE on trip 1001

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC # TODO: Parquet rewrite vs Delta UPDATE; _delta_log records the change.

# COMMAND ----------

# MAGIC %md
# MAGIC **Next:** `02 - Understanding the Delta Transaction Log` walks `_delta_log`
# MAGIC commit by commit.
