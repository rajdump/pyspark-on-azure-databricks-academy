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

from decimal import Decimal

rows = [
    (1001, "Standard", 138, Decimal("12.40"), 18),
    (1002, "Shared", 74, Decimal("3.10"), 9),
    (1003, "Premium", 231, Decimal("22.70"), 35),
    (1004, "Standard", 100, Decimal("5.60"), 14),
    (1005, "Shared", 74, Decimal("2.20"), 7),
]

schema_ddl = (
    "trip_id bigint, service_type string, pickup_location_id int, "
    "trip_distance_miles decimal(8,2), ride_duration_mins int"
)

df = spark.createDataFrame(rows, schema_ddl)  # pyright: ignore[reportUndefinedVariable]

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

df.show()

# COMMAND ----------

df.show(3, truncate=False)

# COMMAND ----------

df.show(2, vertical=True)

# COMMAND ----------

display(df)  # pyright: ignore[reportUndefinedVariable]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Inspect structure: `printSchema()`, `schema`, `columns`, `dtypes`
# MAGIC
# MAGIC Use both human-readable and programmatic schema views.

# COMMAND ----------

df.printSchema()

# COMMAND ----------

print(df.schema)

# COMMAND ----------

print("columns:", df.columns)
print("dtypes: ", df.dtypes)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Inspect size and emptiness: `count()` and `isEmpty()`
# MAGIC
# MAGIC Compare total-row checks and empty-data checks.

# COMMAND ----------

print(f"Row count: {df.count()}")

# COMMAND ----------

print(f"Is DataFrame empty? {df.isEmpty()}")

# COMMAND ----------

# A quick emptiness check on a filtered DataFrame.
empty_df = df.filter("trip_distance_miles > 1000")
print(f"Is filtered DataFrame empty? {empty_df.isEmpty()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## First-pass statistics: `describe()` and `summary()`
# MAGIC
# MAGIC Add a quick profile pass for numeric and string columns.

# COMMAND ----------

df.describe().show()

# COMMAND ----------

df.summary("count", "min", "25%", "50%", "75%", "max").show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Performance note: metadata checks vs Spark execution
# MAGIC
# MAGIC For day-to-day inspection, separate lightweight schema lookups from methods
# MAGIC that execute Spark work:
# MAGIC
# MAGIC - **Metadata-oriented:** `schema`, `columns`, `dtypes`, `printSchema()`
# MAGIC - **Execute Spark work:** `show()`, `count()`, `isEmpty()`, `describe()`,
# MAGIC   `summary()`
# MAGIC
# MAGIC Practical tip: if you only need to know whether data exists, `isEmpty()`
# MAGIC is often a better emptiness check than `count() == 0`.

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
