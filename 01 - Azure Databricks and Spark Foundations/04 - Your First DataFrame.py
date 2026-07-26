# Databricks notebook source
# MAGIC %md
# MAGIC # Your First DataFrame
# MAGIC
# MAGIC **Learning objectives.** After this notebook, you will be able to:
# MAGIC - Build a small rideshare DataFrame from in-notebook Python data
# MAGIC - Inspect DataFrame rows with `show()` and `display()`
# MAGIC - Inspect DataFrame structure with `printSchema()`
# MAGIC - Explain why checking both data values and schema is useful before transformations
# MAGIC
# MAGIC **Prerequisites.** `03 - Working with Notebooks` in this module — you should be comfortable with notebook cells, magics, and shared Python state.
# MAGIC
# MAGIC **Setup.** Use any attached compute with PySpark available. This notebook uses a hand-built, small rideshare example (not file reads from `data/raw/` yet).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Build a small rideshare DataFrame
# MAGIC
# MAGIC In production pipelines, DataFrames usually come from files or tables. For a first step, we create one directly in code so you can focus on the DataFrame shape and inspection workflow.
# MAGIC
# MAGIC The columns below use the same naming pattern as the course rideshare dataset (for example `trip_id`, `service_type`, `trip_distance_miles`) so later modules feel familiar.

# COMMAND ----------

from decimal import Decimal

from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType, IntegerType, LongType, StringType, StructField, StructType

# COMMAND ----------

trip_schema = StructType(
    [
        StructField("trip_id", LongType(), nullable=False),
        StructField("service_type", StringType(), nullable=False),
        StructField("pickup_location_id", IntegerType(), nullable=False),
        StructField("dropoff_location_id", IntegerType(), nullable=False),
        StructField("trip_distance_miles", DecimalType(8, 2), nullable=False),
    ]
)

trip_rows = [
    (1001, "standard", 7, 12, Decimal("3.40")),
    (1002, "premium", 15, 3, Decimal("8.75")),
    (1003, "shared", 22, 22, Decimal("1.10")),
    (1004, "standard", 4, 19, Decimal("5.25")),
]

trips_df = spark.createDataFrame(trip_rows, schema=trip_schema)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Inspect DataFrame rows
# MAGIC
# MAGIC Start by looking at the actual values. `show()` is quick in code output, while `display()` gives Databricks table exploration controls.

# COMMAND ----------

trips_df.show(truncate=False)

# COMMAND ----------

display(trips_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Inspect DataFrame structure
# MAGIC
# MAGIC `printSchema()` shows column names, types, and nullability. In real jobs, this check helps catch type mismatches early (for example decimal vs. string distance fields).

# COMMAND ----------

trips_df.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Worked example: quick quality checks
# MAGIC
# MAGIC Before any transformation, run one or two simple checks so you know the DataFrame is usable.

# COMMAND ----------

print(f"Row count: {trips_df.count()}")

distance_summary_df = trips_df.select(
    F.min("trip_distance_miles").alias("min_distance_miles"),
    F.max("trip_distance_miles").alias("max_distance_miles"),
)
display(distance_summary_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Create a second small DataFrame named `my_trips_df` with the same schema:
# MAGIC
# MAGIC 1. Add at least 3 rows of your own rideshare-style values.
# MAGIC 2. Run `my_trips_df.show(truncate=False)`.
# MAGIC 3. Run `my_trips_df.printSchema()`.
# MAGIC 4. Add one quick check of your choice (for example row count or min/max distance).

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC You created and inspected your first DataFrame by:
# MAGIC
# MAGIC - Defining a schema and building rows in Python
# MAGIC - Viewing values with `show()` and `display()`
# MAGIC - Validating structure with `printSchema()`
# MAGIC - Running a simple quality check before transformation work
# MAGIC
# MAGIC This inspection habit carries into the rest of the course whenever you read from files or tables.
