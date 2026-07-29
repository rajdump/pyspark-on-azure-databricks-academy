# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # 06 - Reading Avro
# MAGIC
# MAGIC Avro is a row-oriented binary format with an embedded schema, common in
# MAGIC Kafka and event-pipeline exports. In this notebook, we read the
# MAGIC **`payment`** dataset — Avro landed in the volume in Notebook 01.
# MAGIC
# MAGIC **Key difference from CSV / JSON:** like Parquet, Avro carries schema
# MAGIC metadata in the file. Spark reads typed columns without
# MAGIC **`inferSchema`**. An explicit schema remains useful for production
# MAGIC contracts.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### What you will learn
# MAGIC
# MAGIC | Topic | What you will do |
# MAGIC |-------|------------------|
# MAGIC | Read Avro | Load **`payment`** from a Volume path |
# MAGIC | DataSource syntax | Use `format("avro").load(...)` / `.save(...)` |
# MAGIC | Embedded schema | Inspect with `printSchema()`, a sample row, and row count |
# MAGIC | Explicit schemas | Apply DDL string and `StructType` schemas for validation |
# MAGIC | Light reshape | Select fare columns for a practice write |
# MAGIC | Write Avro | Save a practice output under `practice/` |
# MAGIC | Round-trip test | Re-read written Avro and confirm types are preserved |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Prerequisites.** Module 4, **01 - Unity Catalog Volumes and Data
# MAGIC Landing**, and prior Module 5 format notebooks — landing volume populated
# MAGIC with **`payment/payment.avro`**.
# MAGIC
# MAGIC **Source file:** `/Volumes/rideshare_dev/landing/source_files/payment/payment.avro`
# MAGIC
# MAGIC **Compute:** Any cluster with PySpark. This notebook uses Volume paths only.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup
# MAGIC
# MAGIC Import PySpark helpers and set paths for the **`payment`** dataset.
# MAGIC
# MAGIC Course **`payment`** columns (from `docs/data/dataset-overview.md`):
# MAGIC **`trip_id`** (bigint), **`payment_method`** (string),
# MAGIC **`base_fare_amount`** (decimal(10,2)), **`surge_amount`** (decimal(10,2)),
# MAGIC **`tax_amount`** (decimal(10,2)), **`tip_amount`** (decimal(10,2)),
# MAGIC **`discount_amount`** (decimal(10,2)), **`driver_payout_amount`**
# MAGIC (decimal(10,2)).

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import (
    DecimalType,
    LongType,
    StringType,
    StructField,
    StructType,
)

landing_root = "/Volumes/rideshare_dev/landing/source_files"
payment_avro_path = f"{landing_root}/payment/payment.avro"
practice_root = "/Volumes/rideshare_dev/processed/output_files/practice"
practice_output_path = f"{practice_root}/payment_avro_roundtrip/"

print(f"payment_avro_path = {payment_avro_path}")
print(f"practice_output_path = {practice_output_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Source path
# MAGIC
# MAGIC **`payment/payment.avro`** was copied into the landing volume in Notebook 01.
# MAGIC Format notebooks in this module read through **`/Volumes/...`** paths only.

# COMMAND ----------

display(dbutils.fs.ls(f"{landing_root}/payment"))

# COMMAND ----------

# MAGIC %md
# MAGIC You should see **`payment.avro`** in that folder. The path variable
# MAGIC **`payment_avro_path`** points to the full file for the reads below.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Avro format
# MAGIC
# MAGIC Avro stores rows in a **binary** container with an **embedded schema**.
# MAGIC Contrast with formats you already read:
# MAGIC
# MAGIC | Format | How types arrive |
# MAGIC |--------|------------------|
# MAGIC | CSV | Text only — default **`string`**, or **`inferSchema`** / explicit schema |
# MAGIC | JSON | Infers names and types from values (or use explicit schema) |
# MAGIC | Parquet | Columnar binary — types in file metadata |
# MAGIC | Avro | Row-oriented binary — types in file metadata (no **`inferSchema`**) |
# MAGIC
# MAGIC Do not peek with **`dbutils.fs.head`** — inspect schema after you read the
# MAGIC DataFrame.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Read syntax
# MAGIC
# MAGIC Use the generic DataSource API — the same **`format(...).load(...)`**
# MAGIC pattern as CSV, JSON, Parquet, and XML in this module. Avro does not have
# MAGIC a compact **`.avro(path)`** reader shorthand like **`.parquet(path)`**.

# COMMAND ----------

payment_embedded = spark.read.format("avro").load(payment_avro_path)

print("format('avro').load(path):")
payment_embedded.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC Prefer **`format("avro")`** for both reads and writes so pipelines stay
# MAGIC consistent across formats. The variable **`payment_embedded`** carries
# MAGIC forward until section 5, where we apply an explicit schema.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Read and inspect
# MAGIC
# MAGIC Without **`inferSchema`**, Avro already returns typed columns from file
# MAGIC metadata. Confirm schema, a sample row, and row count.

# COMMAND ----------

print("Schema from Avro metadata (no inferSchema):")
payment_embedded.printSchema()

print("\nSample row:")
payment_embedded.show(1, vertical=True)

row_count = payment_embedded.count()
print(f"\nRow count: {row_count} (expect 100 for the course payment file)")

# COMMAND ----------

# MAGIC %md
# MAGIC Expect **`trip_id`** as **`bigint`**, **`payment_method`** as **`string`**,
# MAGIC and the fare columns as **`decimal(10,2)`** (or a compatible numeric type
# MAGIC from the file). **`printSchema()`** inspects metadata on the driver.
# MAGIC **`count()`** is an action that executes the read plan.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Explicit schema
# MAGIC
# MAGIC Even though Avro carries types, production pipelines still declare the
# MAGIC contract up front. Module 2 introduced DDL strings and **`StructType`**;
# MAGIC file reads accept either via **`.schema(...)`**.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 5a. DDL schema string

# COMMAND ----------

payment_schema_ddl = """
trip_id bigint,
payment_method string,
base_fare_amount decimal(10,2),
surge_amount decimal(10,2),
tax_amount decimal(10,2),
tip_amount decimal(10,2),
discount_amount decimal(10,2),
driver_payout_amount decimal(10,2)
"""

payment = (
    spark.read.format("avro").schema(payment_schema_ddl).load(payment_avro_path)
)

print("Read with DDL schema:")
payment.printSchema()
payment.show(1, vertical=True)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 5b. `StructType` schema

# COMMAND ----------

payment_schema = StructType(
    [
        StructField("trip_id", LongType(), False),
        StructField("payment_method", StringType(), False),
        StructField("base_fare_amount", DecimalType(10, 2), False),
        StructField("surge_amount", DecimalType(10, 2), False),
        StructField("tax_amount", DecimalType(10, 2), False),
        StructField("tip_amount", DecimalType(10, 2), False),
        StructField("discount_amount", DecimalType(10, 2), False),
        StructField("driver_payout_amount", DecimalType(10, 2), False),
    ]
)

payment_via_struct = (
    spark.read.format("avro").schema(payment_schema).load(payment_avro_path)
)

print("Same file read with StructType (schemas should match):")
payment_via_struct.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC Use **`payment`** (DDL read) for the rest of this notebook.
# MAGIC
# MAGIC > **Note:** If the explicit schema disagrees with Avro metadata (wrong type
# MAGIC > or missing columns), Spark may cast, null out values, or fail the read.
# MAGIC > Keep the declared schema aligned with the course contract.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Light reshape
# MAGIC
# MAGIC **`select`** a small fare extract for later joins to **`trip`** on
# MAGIC **`trip_id`**. Deeper transforms belong in Module 6.

# COMMAND ----------

payment_subset = payment.select(
    F.col("trip_id"),
    F.col("payment_method"),
    F.col("base_fare_amount"),
    F.col("tip_amount"),
    F.col("driver_payout_amount"),
)

payment_subset.show(3)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Avro round trip
# MAGIC
# MAGIC Write the subset to **`practice/payment_avro_roundtrip/`**, then read it
# MAGIC back. Spark writes **`part-*.avro`** files under that directory. Like
# MAGIC Parquet, Avro **preserves types** across the write — still re-apply an
# MAGIC explicit schema on read when you want a clear contract.
# MAGIC
# MAGIC Use **`format("avro").save(...)`** (recommended module pattern).

# COMMAND ----------

payment_subset.write.format("avro").mode("overwrite").save(practice_output_path)

print(f"Wrote Avro folder to {practice_output_path}")
display(dbutils.fs.ls(practice_output_path))

# COMMAND ----------

roundtrip_embedded = spark.read.format("avro").load(practice_output_path)

print("Re-read without explicit schema (types come from Avro metadata):")
roundtrip_embedded.printSchema()
roundtrip_embedded.show(1, vertical=True)

# COMMAND ----------

payment_subset_schema_ddl = """
trip_id bigint,
payment_method string,
base_fare_amount decimal(10,2),
tip_amount decimal(10,2),
driver_payout_amount decimal(10,2)
"""

roundtrip_typed = (
    spark.read.format("avro").schema(payment_subset_schema_ddl).load(practice_output_path)
)

print("Re-read with explicit schema (production pattern):")
roundtrip_typed.printSchema()
roundtrip_typed.show(1, vertical=True)

# COMMAND ----------

# MAGIC %md
# MAGIC Avro kept decimal fare columns typed without **`inferSchema`**. We used
# MAGIC **`.mode("overwrite")`** so re-runs replace the prior folder. Save modes
# MAGIC in depth are in **07 - Write Patterns and Table Preview**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Build a small practice extract without reusing **`payment_subset`**:
# MAGIC
# MAGIC 1. Read **`payment.avro`** again with the full **`payment_schema_ddl`**
# MAGIC    (or **`payment_schema`**) into a new DataFrame (do not reuse
# MAGIC    **`payment`** or **`payment_subset`**).
# MAGIC 2. **`select`** exactly these three columns: **`trip_id`**,
# MAGIC    **`surge_amount`**, **`tax_amount`**.
# MAGIC 3. Write the result to
# MAGIC    **`/Volumes/rideshare_dev/processed/output_files/practice/payment_exercise/`**
# MAGIC    with **`.mode("overwrite")`** using **`format("avro").save(...)`**.
# MAGIC 4. Re-read the written folder with an explicit schema for those three
# MAGIC    columns and print the schema. Confirm **`trip_id`** is **`bigint`** and
# MAGIC    the amount columns are **`decimal(10,2)`**.

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - **Avro syntax** — use **`format("avro").load(...)`** /
# MAGIC   **`format("avro").save(...)`** (no compact **`.avro(path)`** reader like
# MAGIC   Parquet)
# MAGIC - **Embedded schema** — types come from file metadata; no **`inferSchema`**
# MAGIC - **Explicit schema (DDL or `StructType`)** — still recommended for production
# MAGIC   contracts and validation
# MAGIC - **Light reshape** — **`select`** fare columns before a practice write
# MAGIC - **Avro round trip** — writes a directory of part files; types are
# MAGIC   preserved on re-read (unlike CSV)
# MAGIC
# MAGIC **Next:** **07 - Write Patterns and Table Preview** — save modes, a brief
# MAGIC partitioned write, Delta file write under **`practice/`**, and managed
# MAGIC **`saveAsTable`** into **`rideshare_dev.processed`**.
