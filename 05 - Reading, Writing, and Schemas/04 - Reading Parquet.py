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
# MAGIC in the file. Spark reads column names and types without **`inferSchema`**. An
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
# MAGIC | Round-trip test | Re-read written Parquet and confirm types are preserved |
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

from pyspark.sql import functions as F
from pyspark.sql.types import DateType, IntegerType, LongType, StructField, StructType

landing_root = "/Volumes/rideshare_dev/landing/source_files"
trip_time_parquet_path = f"{landing_root}/trip_time/trip_time.parquet"
practice_root = "/Volumes/rideshare_dev/processed/output_files/practice"
practice_output_path = f"{practice_root}/trip_time_parquet_roundtrip/"

print(f"trip_time_parquet_path = {trip_time_parquet_path}")
print(f"practice_output_path = {practice_output_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Source path
# MAGIC
# MAGIC **`trip_time/trip_time.parquet`** was copied into the landing volume in
# MAGIC Notebook 01. Format notebooks in this module read through **`/Volumes/...`**
# MAGIC paths only.

# COMMAND ----------

display(dbutils.fs.ls(f"{landing_root}/trip_time"))

# COMMAND ----------

# MAGIC %md
# MAGIC You should see **`trip_time.parquet`** in that folder. The path variable
# MAGIC **`trip_time_parquet_path`** points to the full file for the reads below.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Parquet format
# MAGIC
# MAGIC Parquet stores data **column-by-column** with **embedded schema metadata**.
# MAGIC Contrast with:
# MAGIC
# MAGIC | Format | How types arrive |
# MAGIC |--------|------------------|
# MAGIC | CSV | Text only — default **`string`**, or **`inferSchema`** / explicit schema |
# MAGIC | JSON | Infers names and types from values (or use explicit schema) |
# MAGIC | Parquet | Types already stored in the file footer — no **`inferSchema`** needed |
# MAGIC
# MAGIC The landing file is **binary** — do not treat it like a text peek with
# MAGIC **`dbutils.fs.head`**. Inspect schema after you read it into a DataFrame.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Read syntax — shorthand vs generic
# MAGIC
# MAGIC Spark exposes two equivalent ways to read Parquet:

# COMMAND ----------

trip_time_shorthand = spark.read.parquet(trip_time_parquet_path)

trip_time_embedded = spark.read.format("parquet").load(trip_time_parquet_path)

print("Shorthand — .parquet(path):")
trip_time_shorthand.printSchema()

print("Generic — .format('parquet').load(path):")
trip_time_embedded.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC Both approaches give the same result. The difference is just syntax:
# MAGIC
# MAGIC | Syntax | When to use |
# MAGIC |--------|-------------|
# MAGIC | `.parquet(path)` | Quick exploration — short and convenient |
# MAGIC | `.format("parquet").load(path)` | Recommended — same pattern as CSV, JSON, Avro, and XML |
# MAGIC
# MAGIC This notebook uses **`format("parquet")`** from here onward. The variable
# MAGIC **`trip_time_embedded`** carries forward until section 5, where we apply an
# MAGIC explicit schema.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Read and inspect
# MAGIC
# MAGIC Without **`inferSchema`**, Parquet already returns typed columns from file
# MAGIC metadata. Confirm schema, a sample row, and row count.

# COMMAND ----------

print("Schema from Parquet metadata (no inferSchema):")
trip_time_embedded.printSchema()

print("\nSample row:")
trip_time_embedded.show(1, vertical=True)

row_count = trip_time_embedded.count()
print(f"\nRow count: {row_count} (expect 100 for the course trip_time file)")

# COMMAND ----------

# MAGIC %md
# MAGIC Expect **`trip_id`** as **`bigint`**, **`trip_date`** as **`date`**, and
# MAGIC **`hour_of_day`** as **`int`**. **`printSchema()`** inspects metadata on the
# MAGIC driver — it does not modify data. **`count()`** is an action that executes
# MAGIC the read plan.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Explicit schema
# MAGIC
# MAGIC Even though Parquet carries types, production pipelines still declare the
# MAGIC contract up front. Module 2 introduced DDL strings and **`StructType`**;
# MAGIC file reads accept either via **`.schema(...)`**.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 5a. DDL schema string

# COMMAND ----------

trip_time_schema_ddl = """
trip_id bigint,
trip_date date,
hour_of_day int
"""

trip_time = (
    spark.read.format("parquet").schema(trip_time_schema_ddl).load(trip_time_parquet_path)
)

print("Read with DDL schema:")
trip_time.printSchema()
trip_time.show(1, vertical=True)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 5b. `StructType` schema

# COMMAND ----------

trip_time_schema = StructType(
    [
        StructField("trip_id", LongType(), False),
        StructField("trip_date", DateType(), False),
        StructField("hour_of_day", IntegerType(), False),
    ]
)

trip_time_via_struct = (
    spark.read.format("parquet").schema(trip_time_schema).load(trip_time_parquet_path)
)

print("Same file read with StructType (schemas should match):")
trip_time_via_struct.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC Use **`trip_time`** (DDL read) for the rest of this notebook.
# MAGIC
# MAGIC > **Note:** If the explicit schema disagrees with Parquet metadata (wrong
# MAGIC > type or missing columns), Spark may cast, null out values, or fail the
# MAGIC > read depending on the mismatch. Keep the declared schema aligned with
# MAGIC > the course contract.

# COMMAND ----------

# DBTITLE 1,Schema mismatch scenarios
# What happens when your explicit schema disagrees with the Parquet file?
# The file has: trip_id (bigint), trip_date (date), hour_of_day (int)

# Scenario 1: Compatible type widening (int → bigint) — Spark casts silently
schema_1 = "trip_id bigint, trip_date date, hour_of_day bigint"
df1 = spark.read.format("parquet").schema(schema_1).load(trip_time_parquet_path)
print("Scenario 1 — int declared as bigint (compatible cast):")
df1.select("hour_of_day").show(2)

# Scenario 2: Incompatible type (date column declared as int) — returns NULLs
schema_2 = "trip_id bigint, trip_date int, hour_of_day int"
df2 = spark.read.format("parquet").schema(schema_2).load(trip_time_parquet_path)
print("Scenario 2 — date declared as int (incompatible) → NULLs:")
df2.select("trip_date").show(2)

# Scenario 3: Extra column in schema that doesn't exist in file → NULLs
schema_3 = "trip_id bigint, trip_date date, hour_of_day int, city string"
df3 = spark.read.format("parquet").schema(schema_3).load(trip_time_parquet_path)
print("Scenario 3 — 'city' not in file → NULLs:")
df3.select("city").show(2)

# Scenario 4: Schema omits a file column → column is dropped (not in DataFrame)
schema_4 = "trip_id bigint, trip_date date"
df4 = spark.read.format("parquet").schema(schema_4).load(trip_time_parquet_path)
print("Scenario 4 — 'hour_of_day' omitted from schema → dropped:")
df4.printSchema()
df4.show(2)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Light reshape
# MAGIC
# MAGIC **`select`** and **`withColumnRenamed`** prepare a small extract for later
# MAGIC joins to **`trip`** on **`trip_id`**. Deeper transforms belong in Module 6.

# COMMAND ----------

trip_time_subset = trip_time.select(
    F.col("trip_id"),
    F.col("trip_date"),
    F.col("hour_of_day"),
).withColumnRenamed("hour_of_day", "pickup_hour")

trip_time_subset.show(3)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Parquet round trip
# MAGIC
# MAGIC Write the subset to **`practice/trip_time_parquet_roundtrip/`**, then read it
# MAGIC back. Spark writes **`part-*.parquet`** files under that directory. Unlike
# MAGIC CSV (and more reliably than JSON), Parquet **preserves types** across the
# MAGIC write — still re-apply an explicit schema on read when you want a clear
# MAGIC contract.
# MAGIC
# MAGIC The write below uses **`format("parquet").save(...)`** (recommended). The
# MAGIC shorthand **`.parquet(...)`** equivalent is shown as a comment only.

# COMMAND ----------

trip_time_subset.write.format("parquet").mode("overwrite").save(practice_output_path)

# Shorthand equivalent:
# trip_time_subset.write.mode("overwrite").parquet(practice_output_path)

print(f"Wrote Parquet folder to {practice_output_path}")
display(dbutils.fs.ls(practice_output_path))

# COMMAND ----------

roundtrip_embedded = spark.read.format("parquet").load(practice_output_path)

print("Re-read without explicit schema (types come from Parquet metadata):")
roundtrip_embedded.printSchema()
roundtrip_embedded.show(1, vertical=True)

# COMMAND ----------

trip_time_subset_schema_ddl = (
    "trip_id bigint, trip_date date, pickup_hour int"
)

roundtrip_typed = (
    spark.read.format("parquet")
    .schema(trip_time_subset_schema_ddl)
    .load(practice_output_path)
)

print("Re-read with explicit schema (production pattern):")
roundtrip_typed.printSchema()
roundtrip_typed.show(1, vertical=True)

# COMMAND ----------

# MAGIC %md
# MAGIC Parquet kept **`trip_date`** as **`date`** and **`pickup_hour`** as **`int`**
# MAGIC without **`inferSchema`**. We used **`.mode("overwrite")`** so re-runs
# MAGIC replace the prior folder. Save modes in depth are in **07 - Write Patterns
# MAGIC and Table Preview**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Build a small practice extract without reusing **`trip_time_subset`**:
# MAGIC
# MAGIC 1. Read **`trip_time.parquet`** again with the full **`trip_time_schema_ddl`**
# MAGIC    (or **`trip_time_schema`**) into a new DataFrame (do not reuse
# MAGIC    **`trip_time`** or **`trip_time_subset`**).
# MAGIC 2. **`select`** exactly these two columns: **`trip_id`**, **`trip_date`**.
# MAGIC 3. Write the result to
# MAGIC    **`/Volumes/rideshare_dev/processed/output_files/practice/trip_time_exercise/`**
# MAGIC    with **`.mode("overwrite")`** (use either **`format("parquet").save(...)`**
# MAGIC    or **`.parquet(...)`** — same as section 7).
# MAGIC 4. Re-read the written folder with an explicit schema for those two columns
# MAGIC    and print the schema. Confirm **`trip_id`** is **`bigint`** and
# MAGIC    **`trip_date`** is **`date`**.

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - **Parquet syntax** — **`.parquet(path)`** shorthand and
# MAGIC   **`format("parquet").load(...)`** / **`format("parquet").save(...)`** are
# MAGIC   equivalent; prefer **`format("parquet")`** in this module
# MAGIC - **Embedded schema** — types come from file metadata; no **`inferSchema`**
# MAGIC - **Explicit schema (DDL or `StructType`)** — still recommended for production
# MAGIC   contracts and validation
# MAGIC - **Light reshape** — **`select`** / rename before a practice write
# MAGIC - **Parquet round trip** — writes a directory of part files; types are
# MAGIC   preserved on re-read (unlike CSV)
# MAGIC
# MAGIC **Next:** **05 - Reading XML** — read **`drivers`** from the landing volume
# MAGIC with **`rowTag`** only (no **`explode`** — Module 6).
