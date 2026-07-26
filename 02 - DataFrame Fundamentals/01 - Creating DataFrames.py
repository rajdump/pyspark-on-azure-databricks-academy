# Databricks notebook source
# MAGIC %md
# MAGIC # Creating DataFrames
# MAGIC
# MAGIC **Learning objectives.** After this notebook, you will be able to:
# MAGIC - Explain what a Spark DataFrame represents in technical terms
# MAGIC - Create a small DataFrame four ways from Python rows:
# MAGIC   - without columns and without schema
# MAGIC   - with columns and without schema
# MAGIC   - with columns and an explicit DDL schema
# MAGIC   - with columns and an explicit `StructType` schema
# MAGIC - Inspect each DataFrame with `printSchema()` and row output
# MAGIC - Explain why inferred schemas are convenient for demos but risky for
# MAGIC   production data models
# MAGIC
# MAGIC **Prerequisites.** `04 - Your First DataFrame` in Module 1 — you should
# MAGIC already be comfortable with `spark.createDataFrame(...)`, `show()`, and
# MAGIC `printSchema()`.
# MAGIC
# MAGIC **Setup.** Attach any compute with PySpark available. This notebook uses
# MAGIC tiny hand-built rideshare rows (2-3 rows per example) so the focus stays
# MAGIC on DataFrame creation patterns.

# COMMAND ----------

# MAGIC %md
# MAGIC ## What a Spark DataFrame represents
# MAGIC
# MAGIC A Spark DataFrame is a distributed table-like dataset with:
# MAGIC
# MAGIC - **rows** (records)
# MAGIC - **named columns**
# MAGIC - a **schema** (column types and nullability metadata)
# MAGIC
# MAGIC Spark uses the schema to plan and optimize execution. In demos, Spark can
# MAGIC infer the schema from sample Python values. In production, you usually
# MAGIC define the schema intentionally so data types and nullability match the
# MAGIC business model you expect.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1) Without columns and without schema
# MAGIC
# MAGIC This is the most basic creation path. Spark infers types and assigns
# MAGIC default column names like `_1`, `_2`, `_3`.

# COMMAND ----------

rows_basic = [
    (1001, "Standard", 12.4),
    (1002, "Shared", 3.1),
    (1003, "Premium", 22.7),
]

df_unnamed = spark.createDataFrame(rows_basic)

df_unnamed.printSchema()
df_unnamed.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC Default names (`_1`, `_2`, ...) are useful for quick experiments, but they
# MAGIC are hard to maintain in real pipelines.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2) With columns and without schema
# MAGIC
# MAGIC Here you provide column names, but Spark still infers data types from the
# MAGIC Python values.

# COMMAND ----------

rows_named = [
    (1001, "Standard", 138, 12.4, 18),
    (1002, "Shared", 74, 3.1, 9),
    (1003, "Premium", 231, 22.7, 35),
]

columns_named = [
    "trip_id",
    "service_type",
    "pickup_location_id",
    "trip_distance_miles",
    "ride_duration_mins",
]

df_inferred = spark.createDataFrame(rows_named, columns_named)

df_inferred.printSchema()
df_inferred.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC This is convenient and readable. The risk is that inferred types follow the
# MAGIC supplied values, not necessarily your intended production model.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3) With columns and an explicit DDL schema
# MAGIC
# MAGIC A DDL schema string gives explicit names, types, and nullability. For this
# MAGIC course, we align the core fields to the rideshare model (`bigint`, `int`,
# MAGIC `decimal(8,2)`).

# COMMAND ----------

from decimal import Decimal

rows_typed = [
    (1001, "Standard", 138, Decimal("12.40"), 18),
    (1002, "Shared", 74, Decimal("3.10"), 9),
    (1003, "Premium", 231, Decimal("22.70"), 35),
]

schema_ddl = (
    "trip_id bigint NOT NULL, service_type string, pickup_location_id int, "
    "trip_distance_miles decimal(8,2), ride_duration_mins int"
)

df_ddl = spark.createDataFrame(rows_typed, schema_ddl)

df_ddl.printSchema()
df_ddl.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC The explicit DDL schema controls types and nullability metadata up front.
# MAGIC That makes behavior more predictable than inference.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4) With columns and an explicit `StructType` schema
# MAGIC
# MAGIC `StructType` is the same idea as DDL schema, expressed as Python objects.

# COMMAND ----------

from pyspark.sql.types import DecimalType, IntegerType, LongType, StringType, StructField, StructType

schema_struct = StructType(
    [
        StructField("trip_id", LongType(), nullable=False),
        StructField("service_type", StringType(), nullable=True),
        StructField("pickup_location_id", IntegerType(), nullable=True),
        StructField("trip_distance_miles", DecimalType(8, 2), nullable=True),
        StructField("ride_duration_mins", IntegerType(), nullable=True),
    ]
)

df_struct = spark.createDataFrame(rows_typed, schema_struct)

df_struct.printSchema()
df_struct.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC `StructType` is especially useful when schema objects need to be assembled
# MAGIC or reused in code. In this notebook, focus on seeing that it produces an
# MAGIC explicit schema outcome similar to DDL.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Why inference is convenient, but risky in production
# MAGIC
# MAGIC Inferred schema is fast to start with because Spark decides types for you.
# MAGIC For production batch pipelines, that can be risky:
# MAGIC
# MAGIC - whole-number fields can become `long` when your model expects `int`
# MAGIC - decimal-like fields can become `double` when financial logic expects
# MAGIC   exact decimal types
# MAGIC - nullability may not reflect business rules
# MAGIC
# MAGIC Explicit schemas reduce ambiguity and make pipeline behavior more reliable.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Build one small rideshare DataFrame in two ways, then compare:
# MAGIC
# MAGIC 1. Create `my_df_inferred` from 3 rows + column names (no explicit schema).
# MAGIC 2. Create `my_df_typed` from the same rows using an explicit DDL schema:
# MAGIC    - `trip_id bigint`
# MAGIC    - `service_type string`
# MAGIC    - `pickup_location_id int`
# MAGIC    - `trip_distance_miles decimal(8,2)`
# MAGIC    - `ride_duration_mins int`
# MAGIC 3. Run `printSchema()` on both DataFrames.
# MAGIC 4. Show either DataFrame rows with `show(truncate=False)`.
# MAGIC 5. In a short comment, note one schema difference you observe.

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC You created DataFrames four ways and inspected each schema:
# MAGIC
# MAGIC - unnamed + inferred
# MAGIC - named + inferred
# MAGIC - named + explicit DDL schema
# MAGIC - named + explicit `StructType` schema
# MAGIC
# MAGIC The key production takeaway: inferred schemas are convenient for demos, but
# MAGIC explicit schemas are safer when type precision and nullability matter.
# MAGIC
# MAGIC Next up: `02 - Inspecting DataFrames` — deeper inspection with `columns`,
# MAGIC `dtypes`, `count`, and summary statistics.
