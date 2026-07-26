# Databricks notebook source
# MAGIC %md
# MAGIC # Inspecting DataFrames
# MAGIC
# MAGIC **Learning objectives.** After this notebook, you will be able to:
# MAGIC - Inspect DataFrame contents with `show()` options and `display()`
# MAGIC - Inspect DataFrame structure with `printSchema()`, `schema`, `columns`,
# MAGIC   and `dtypes`
# MAGIC - Check DataFrame size and emptiness with `count()` and `isEmpty()`
# MAGIC - Review first-pass statistics with `describe()` and `summary()`
# MAGIC - Explain which inspection methods are metadata lookups vs methods that
# MAGIC   execute Spark work
# MAGIC
# MAGIC **Prerequisites.** `01 - Creating DataFrames` in this module — you should
# MAGIC already know how to create small DataFrames with inferred and explicit
# MAGIC schemas.
# MAGIC
# MAGIC **Setup.** Attach any compute with PySpark available. Use a small,
# MAGIC hand-built rideshare-style DataFrame for examples in this notebook.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup DataFrame for inspection
# MAGIC
# MAGIC Create one small DataFrame (for example 3-8 rows) to use throughout the
# MAGIC notebook so every inspection method runs against the same data.

# COMMAND ----------

# TODO (worked example):
# 1) Define small rideshare-style rows.
# 2) Define a schema or column names appropriate for this lesson.
# 3) Create `df` with `spark.createDataFrame(...)`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Inspect contents: `show()` and `display()`
# MAGIC
# MAGIC Demonstrate row output options:
# MAGIC
# MAGIC - `show()` default
# MAGIC - `show(n, truncate=...)`
# MAGIC - `show(..., vertical=True)` (if useful for readability)
# MAGIC - `display(df)` for interactive exploration in Databricks

# COMMAND ----------

# TODO (worked example): run `df.show()` with default options.

# COMMAND ----------

# TODO (worked example): run `df.show(...)` with explicit `n`/`truncate` settings.

# COMMAND ----------

# TODO (worked example): run `display(df)`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Inspect structure: `printSchema()`, `schema`, `columns`, `dtypes`
# MAGIC
# MAGIC Use both human-readable and programmatic schema views.

# COMMAND ----------

# TODO (worked example): run `df.printSchema()`.

# COMMAND ----------

# TODO (worked example): inspect programmatic schema with `df.schema`.

# COMMAND ----------

# TODO (worked example): print or inspect `df.columns` and `df.dtypes`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Inspect size and emptiness: `count()` and `isEmpty()`
# MAGIC
# MAGIC Compare total-row checks and empty-data checks.

# COMMAND ----------

# TODO (worked example): run `df.count()`.

# COMMAND ----------

# TODO (worked example): run `df.isEmpty()`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## First-pass statistics: `describe()` and `summary()`
# MAGIC
# MAGIC Add a quick profile pass for numeric and string columns.

# COMMAND ----------

# TODO (worked example): run `df.describe().show()`.

# COMMAND ----------

# TODO (worked example): run `df.summary(...).show()` with selected stats.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Performance note: metadata checks vs Spark execution
# MAGIC
# MAGIC Add a short note showing which methods typically do lightweight metadata
# MAGIC inspection (`schema`, `columns`, `dtypes`, `printSchema`) and which methods
# MAGIC trigger Spark work (`show`, `count`, `isEmpty`, `describe`, `summary`).
# MAGIC
# MAGIC Keep this note brief and practical for day-to-day notebook use.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Use a second small rideshare-style DataFrame named `my_df` and complete:
# MAGIC
# MAGIC 1. Show rows with one `show(...)` call and `display(my_df)`.
# MAGIC 2. Inspect structure with `printSchema()`, `schema`, and `dtypes`.
# MAGIC 3. Run `count()` and `isEmpty()`.
# MAGIC 4. Run one stats method (`describe()` or `summary()`).
# MAGIC 5. Write one short note: which method you used that triggers Spark work
# MAGIC    and which method you used that is metadata-oriented.

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC Recap this notebook's inspection path:
# MAGIC
# MAGIC - row content inspection (`show`, `display`)
# MAGIC - structure inspection (`printSchema`, `schema`, `columns`, `dtypes`)
# MAGIC - size/emptiness checks (`count`, `isEmpty`)
# MAGIC - quick statistical review (`describe`, `summary`)
# MAGIC - practical performance awareness (metadata lookups vs Spark execution)
# MAGIC
# MAGIC Next up: `03 - Selecting and Transforming Columns`.
