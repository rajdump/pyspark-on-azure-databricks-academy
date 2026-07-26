# Databricks notebook source
# MAGIC %md
# MAGIC # Your First DataFrame
# MAGIC
# MAGIC **Learning objectives.** After this notebook, you will be able to:
# MAGIC - Explain what a Spark **DataFrame** is at a practical level
# MAGIC - Build a small rideshare-flavored DataFrame with `spark.createDataFrame`
# MAGIC - Inspect rows with `.show()` and `display()`
# MAGIC - Inspect column names and types with `.printSchema()`
# MAGIC
# MAGIC **Prerequisites.** `03 - Working with Notebooks` — you should already know
# MAGIC how to attach compute, run cells in order, and use `spark`.
# MAGIC
# MAGIC **Setup.** Attach compute before running code cells. Any compute type
# MAGIC that provides a `spark` session works for this notebook.
# MAGIC
# MAGIC **Dataset note.** This module builds a **few rows in code** — not a file
# MAGIC read from `data/raw/`. File-based reads of the shared rideshare dataset
# MAGIC begin in a later module. Column names here match the `trip` table shape
# MAGIC from the course dataset (see `docs/data/dataset-overview.md`).
# MAGIC
# MAGIC You know how notebooks and `spark` work. Next you create and inspect
# MAGIC your first DataFrame.

# COMMAND ----------

# MAGIC %md
# MAGIC ## What is a DataFrame?
# MAGIC
# MAGIC A **DataFrame** is Spark's tabular data structure — rows and named columns,
# MAGIC like a spreadsheet or SQL table, but distributed when the data grows large.
# MAGIC
# MAGIC In this notebook the data is tiny (hand-built). The point is the **API**:
# MAGIC create a DataFrame, then inspect it before you transform it in later
# MAGIC modules.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Worked example: build a small `trip` DataFrame
# MAGIC
# MAGIC The shared rideshare dataset centers on a `trip` table. Below, three rows
# MAGIC use the same column names you will see later (`trip_id`, `service_type`,
# MAGIC `pickup_location_id`, `dropoff_location_id`, `trip_distance_miles`).
# MAGIC
# MAGIC Run the next cell to create the DataFrame.

# COMMAND ----------

# TODO: worked example — spark.createDataFrame from a list of rows or dicts
# using trip column names from dataset-overview.md

# COMMAND ----------

# MAGIC %md
# MAGIC ### Inspect rows with `.show()`
# MAGIC
# MAGIC `.show()` prints a text table to the cell output — quick and common in
# MAGIC logs and tutorials.

# COMMAND ----------

# TODO: trips.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Inspect schema with `.printSchema()`
# MAGIC
# MAGIC `.printSchema()` prints column names and Spark data types. Use it to
# MAGIC confirm types before joins or aggregations in later lessons.

# COMMAND ----------

# TODO: trips.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Inspect rows with `display()`
# MAGIC
# MAGIC `display()` renders an interactive table in the notebook UI — sortable and
# MAGIC easier to browse than `.show()` for exploration.

# COMMAND ----------

# TODO: display(trips)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC 1. Add one more row to the worked example data (your choice of values).
# MAGIC 2. Re-create the DataFrame and run `.show()` and `.printSchema()` again.
# MAGIC 3. Confirm the new row appears and the schema is unchanged.
# MAGIC
# MAGIC *(Full exercise cells to be authored.)*

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - A **DataFrame** is Spark's tabular structure for batch data engineering.
# MAGIC - Use **`spark.createDataFrame`** to build small examples in code before
# MAGIC   file reads.
# MAGIC - **`.show()`** and **`display()`** inspect rows; **`.printSchema()`**
# MAGIC   inspects column names and types.
# MAGIC
# MAGIC Next up: Module 2 — DataFrame fundamentals build on this pattern with
# MAGIC the full shared rideshare dataset.
