# Databricks notebook source
# MAGIC %md
# MAGIC # Selecting and Transforming Columns
# MAGIC
# MAGIC **Learning objectives.** After this notebook, you will be able to:
# MAGIC - Project and reorder columns with `select`, and explain DataFrame
# MAGIC   immutability
# MAGIC - Choose column-name strings vs `F.col` when you need an expression
# MAGIC - Build Column expressions with `alias`, light `cast`, `F.lit`, and
# MAGIC   `F.when` / `otherwise`
# MAGIC - Add or replace columns with `withColumn` / `withColumns`
# MAGIC - Rename and drop columns with `withColumnRenamed` /
# MAGIC   `withColumnsRenamed` and `drop`
# MAGIC - Choose `select` vs `withColumn` when adding vs recalculating a column
# MAGIC - Chain transforms into a small operations-style output
# MAGIC
# MAGIC **Prerequisites.** `02 - Inspecting DataFrames` in this module — you
# MAGIC should already know how to create and inspect a small DataFrame.
# MAGIC
# MAGIC **Setup.** Attach any compute with PySpark available. This notebook uses
# MAGIC a small, hand-built rideshare-style DataFrame (aligned with the `trip`
# MAGIC table column names).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup DataFrame for column transforms
# MAGIC
# MAGIC Create one small DataFrame to reuse across every example so each
# MAGIC transform starts from the same trips data.
# MAGIC
# MAGIC Production framing: ops and analytics often need a narrower, renamed,
# MAGIC derived view of trip columns — without mutating the source DataFrame.

# COMMAND ----------

from pyspark.sql import functions as F

# TODO: small hand-built trip rows + explicit schema
# (trip_id, service_type, pickup_location_id, trip_distance_miles,
#  ride_duration_mins — names/types from docs/data/dataset-overview.md)

df = None  # replace with spark.createDataFrame(...)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Project and reorder with `select`
# MAGIC
# MAGIC Motivate: keep only the columns a downstream consumer needs, in a clear
# MAGIC order.
# MAGIC
# MAGIC Demonstrate:
# MAGIC - `select` with column-name strings
# MAGIC - reordering via the order of arguments
# MAGIC - immutability: original `df` columns unchanged after `select`

# COMMAND ----------

# TODO: df.select(...).show() — project a few columns

# COMMAND ----------

# TODO: reorder columns with select; print selected.columns vs df.columns

# COMMAND ----------

# MAGIC %md
# MAGIC ## Column-name strings vs `F.col`
# MAGIC
# MAGIC Use a string when you only need the column as-is. Use `F.col("name")`
# MAGIC when you need a **Column expression** (alias, arithmetic, cast, etc.).

# COMMAND ----------

# TODO: select with F.col(...).alias(...)

# COMMAND ----------

# TODO: arithmetic expression stored in a variable, then aliased in select

# COMMAND ----------

# MAGIC %md
# MAGIC ## Light `cast` and constants with `F.lit`
# MAGIC
# MAGIC - `.cast("type")` — intentional type change (deeper casting / ANSI
# MAGIC   behavior comes in a later module)
# MAGIC - `F.lit(value)` — a fixed value as a column on every row

# COMMAND ----------

# TODO: cast example (e.g. trip_id to string) + printSchema

# COMMAND ----------

# TODO: lit example (e.g. source_system tag)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Conditional columns: `F.when` / `otherwise`
# MAGIC
# MAGIC Build a derived label column (for example a distance band) with chained
# MAGIC `F.when(...).when(...).otherwise(...)`.

# COMMAND ----------

# TODO: when / otherwise expression aliased in select

# COMMAND ----------

# MAGIC %md
# MAGIC ## Add or replace columns: `withColumn` / `withColumns`
# MAGIC
# MAGIC - New name → adds a derived column
# MAGIC - Existing name → recalculates that column
# MAGIC - Several columns at once → `withColumns({...})`
# MAGIC
# MAGIC Call out: `select("*", expr.alias("existing_name"))` can duplicate a
# MAGIC column name; `withColumn` replaces by name.

# COMMAND ----------

# TODO: withColumn to add a derived column

# COMMAND ----------

# TODO: withColumn to recalculate an existing column

# COMMAND ----------

# TODO: withColumns for several derived columns

# COMMAND ----------

# MAGIC %md
# MAGIC ## Rename and drop columns
# MAGIC
# MAGIC - One rename: `withColumnRenamed`
# MAGIC - Several renames: `withColumnsRenamed`
# MAGIC - Remove columns: `drop` (missing names do not error)
# MAGIC
# MAGIC Note: `withColumnRenamed` is a silent no-op if the old name is wrong —
# MAGIC check `printSchema()` when a rename seems ignored.

# COMMAND ----------

# TODO: withColumnRenamed / withColumnsRenamed examples

# COMMAND ----------

# TODO: drop example

# COMMAND ----------

# MAGIC %md
# MAGIC ## Chain transforms into an operations-style output
# MAGIC
# MAGIC Worked example: start from `df`, project / derive / rename / drop into a
# MAGIC small dashboard-ready DataFrame. Prefer readable chaining or clear
# MAGIC intermediate names.

# COMMAND ----------

# TODO: chained select / withColumns / withColumn / rename / drop
# TODO: show() + printSchema() on the result

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Use a second small rideshare-style DataFrame named `my_df` and complete:
# MAGIC
# MAGIC 1. Project and reorder a few columns with `select`.
# MAGIC 2. Add one derived column with `withColumn` (or `withColumns`) using
# MAGIC    `F.col` (and `F.when` or `F.lit` if useful).
# MAGIC 3. Rename one column and drop one column you no longer need.
# MAGIC 4. Confirm the original `my_df` columns are unchanged after your chain.
# MAGIC
# MAGIC Keep the DataFrame tiny (a handful of rows).

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC Recap this notebook's reshape path:
# MAGIC
# MAGIC - `select` for projection, reorder, and immutability
# MAGIC - strings vs `F.col` for expressions (`alias`, light `cast`, `F.lit`,
# MAGIC   `F.when`)
# MAGIC - `withColumn` / `withColumns` to add or recalculate
# MAGIC - rename helpers and `drop`
# MAGIC - chaining into a clear output shape
# MAGIC
# MAGIC Next up: `04 - SQL Expressions in DataFrame Code` — the same kind of
# MAGIC column logic written as SQL expression strings (`F.expr`, `selectExpr`).
