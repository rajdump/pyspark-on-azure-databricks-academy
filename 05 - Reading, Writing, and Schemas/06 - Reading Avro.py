# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # 06 - Reading Avro
# MAGIC
# MAGIC ## What is Avro?
# MAGIC
# MAGIC Avro is a **row-oriented binary format** commonly used to exchange
# MAGIC structured records between systems.
# MAGIC
# MAGIC ## Row-oriented storage
# MAGIC
# MAGIC In a row-oriented format, all values for one record are stored together.
# MAGIC
# MAGIC For example, a payment record may contain **`trip_id`**,
# MAGIC **`payment_method`**, **`base_fare_amount`**, and **`tip_amount`**.
# MAGIC This makes Avro suitable for Kafka events, application messages, and
# MAGIC ingestion pipelines that usually produce or consume complete records.
# MAGIC
# MAGIC The diagram below uses three small payments to show how Avro lays those
# MAGIC fields out on disk.

# COMMAND ----------

# MAGIC %md
# MAGIC Same three payments (logical table):
# MAGIC
# MAGIC | trip_id | tip_amount | payment_method |
# MAGIC |--------:|-----------:|:---------------|
# MAGIC | 1 | 2.50 | card |
# MAGIC | 2 | 1.00 | cash |
# MAGIC | 3 | 3.25 | card |

# COMMAND ----------

# MAGIC %md
# MAGIC ### Avro — row-oriented (on disk)
# MAGIC
# MAGIC Storage follows each payment **across** (→), then the next payment.
# MAGIC One record stays together on disk.
# MAGIC
# MAGIC ```text
# MAGIC Logical rows (read →):
# MAGIC
# MAGIC   trip_id   tip_amount   payment_method
# MAGIC   -------   ----------   --------------
# MAGIC      1         2.50           card      ← payment 1
# MAGIC      2         1.00           cash      ← payment 2
# MAGIC      3         3.25           card      ← payment 3
# MAGIC
# MAGIC On disk (payment after payment):
# MAGIC
# MAGIC   [ 1 | 2.50 | card ]  [ 2 | 1.00 | cash ]  [ 3 | 3.25 | card ]
# MAGIC    <-- payment 1 -->    <-- payment 2 -->    <-- payment 3 -->
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## How is Parquet different?
# MAGIC
# MAGIC Parquet is **column-oriented**, meaning values from the same column are
# MAGIC stored together.
# MAGIC
# MAGIC If a dataset has ten columns but a query needs only **`tip_amount`**,
# MAGIC Parquet can read mainly the data for that column. Avro returns only the
# MAGIC selected column, but it must process the records containing the other
# MAGIC fields.
# MAGIC
# MAGIC Therefore, Parquet is better suited for analytical queries that read a
# MAGIC small number of columns from large datasets.
# MAGIC
# MAGIC The same three payments, stored the Parquet way:

# COMMAND ----------

# MAGIC %md
# MAGIC ### Parquet — column-oriented (on disk)
# MAGIC
# MAGIC Storage follows each column **down** (↓), then the next column.
# MAGIC Values from the same field sit together on disk.
# MAGIC
# MAGIC ```text
# MAGIC Same table, regrouped by column (read ↓):
# MAGIC
# MAGIC   trip_id values:         1      2      3
# MAGIC   tip_amount values:      2.50   1.00   3.25
# MAGIC   payment_method values:  card   cash   card
# MAGIC
# MAGIC On disk (column after column):
# MAGIC
# MAGIC   [ 1 | 2 | 3 ]  [ 2.50 | 1.00 | 3.25 ]  [ card | cash | card ]
# MAGIC    <-- trip_id -->  <---- tip_amount ---->  <- payment_method ->
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## When to use each format
# MAGIC
# MAGIC Use **Avro** for ingestion and record-based data exchange.
# MAGIC
# MAGIC Use **Parquet** for analytical file storage and column-based queries.
# MAGIC
# MAGIC ## Dataset used in this notebook
# MAGIC
# MAGIC In this notebook, we read the **`payment`** Avro dataset copied to the
# MAGIC landing volume in Notebook 01.
# MAGIC
# MAGIC ## Schema handling
# MAGIC
# MAGIC Avro files store schema information in the file header. Parquet files
# MAGIC also store schema metadata.
# MAGIC
# MAGIC Spark can therefore read typed columns from both formats without using
# MAGIC **`inferSchema`**.
# MAGIC
# MAGIC In production pipelines, the discovered schema should still be validated
# MAGIC against the expected data contract.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### What you will learn
# MAGIC
# MAGIC | Topic | What you will do |
# MAGIC |-------|------------------|
# MAGIC | When to use Avro | Contrast Avro with Parquet for ingestion vs analytics |
# MAGIC | Read Avro | Load **`payment`** from a Volume path |
# MAGIC | DataSource syntax | Use `format("avro").load(...)` / `.save(...)` |
# MAGIC | Embedded schema | Inspect with `printSchema()`, a sample row, and row count |
# MAGIC | Explicit schemas | Apply DDL string and `StructType` schemas for validation |
# MAGIC | Schema mismatch | Contrast `.schema(...)` drift vs compatible `avroSchema` evolution |
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
avro_evolution_demo_path = f"{practice_root}/avro_schema_evolution_demo/"

print(f"payment_avro_path = {payment_avro_path}")
print(f"practice_output_path = {practice_output_path}")
print(f"avro_evolution_demo_path = {avro_evolution_demo_path}")

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
# MAGIC ## 2. Read syntax
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
# MAGIC forward until section 4, where we apply an explicit schema.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Read and inspect
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
# MAGIC ## 4. Explicit schema
# MAGIC
# MAGIC Even though Avro carries types, production pipelines still declare the
# MAGIC contract up front. Module 2 introduced DDL strings and **`StructType`**;
# MAGIC file reads accept either via **`.schema(...)`**.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4a. DDL schema string

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
# MAGIC ### 4b. `StructType` schema

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
# MAGIC Use **`payment`** (DDL read) for the rest of this notebook after the
# MAGIC mismatch demos below.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4c. Schema mismatch (ingestion drift)
# MAGIC
# MAGIC Avro is common at **ingestion**. Official Spark docs describe **two**
# MAGIC different schema knobs — do not mix them up:
# MAGIC
# MAGIC | API | What it is | Typical use |
# MAGIC |-----|------------|-------------|
# MAGIC | **`.schema(...)`** | Spark SQL (Catalyst) contract | Everyday pipeline contract |
# MAGIC | **`.option("avroSchema", ...)`** | Avro JSON **reader** schema | Compatible evolution (writer vs reader) |
# MAGIC
# MAGIC With **`.schema(...)`**, Spark is intentionally **strict** about wrong
# MAGIC types (Spark 3.5+ can raise incompatible-read errors rather than return
# MAGIC corrupt values). Column add/drop via Catalyst still often "succeeds"
# MAGIC with nulls or omitted columns.
# MAGIC
# MAGIC Compatible evolution (for example a **new field with a default**) is
# MAGIC documented on **`avroSchema`**, not on Catalyst type casts.
# MAGIC
# MAGIC After these demos, keep using **`payment`** from section 4a.

# COMMAND ----------

# MAGIC %md
# MAGIC #### `.schema(...)` — landing dropped a column
# MAGIC
# MAGIC The contract still expects **`promo_code`**, but **`payment.avro`** does
# MAGIC not have it.

# COMMAND ----------

mismatch_dropped = (
    spark.read.format("avro")
    .schema(
        """
        trip_id bigint,
        payment_method string,
        base_fare_amount decimal(10,2),
        surge_amount decimal(10,2),
        tax_amount decimal(10,2),
        tip_amount decimal(10,2),
        discount_amount decimal(10,2),
        driver_payout_amount decimal(10,2),
        promo_code string
        """
    )
    .load(payment_avro_path)
)

print("Contract field missing from file → nulls:")
mismatch_dropped.select("trip_id", "promo_code").show(3)

# COMMAND ----------

# MAGIC %md
# MAGIC **`promo_code`** is all **`null`**. The job can still succeed — easy to
# MAGIC miss until a downstream check fails.

# COMMAND ----------

# MAGIC %md
# MAGIC #### `.schema(...)` — wrong type (strict fail)
# MAGIC
# MAGIC Declaring **`tip_amount`** as **`string`** when the file stores a decimal
# MAGIC is an incompatible Catalyst type. Modern Spark Avro refuses this rather
# MAGIC than inventing a quiet wrong value (see Spark's Avro incompatible-read
# MAGIC behavior / migration notes since 3.5). Contrast Parquet Notebook **04**,
# MAGIC where some wrong types still return rows.

# COMMAND ----------

try:
    (
        spark.read.format("avro")
        .schema(
            """
            trip_id bigint,
            payment_method string,
            base_fare_amount decimal(10,2),
            surge_amount decimal(10,2),
            tax_amount decimal(10,2),
            tip_amount string,
            discount_amount decimal(10,2),
            driver_payout_amount decimal(10,2)
            """
        )
        .load(payment_avro_path)
        .select("tip_amount")
        .show(3)
    )
except Exception as exc:
    print(f"Wrong Catalyst type stopped the read: {type(exc).__name__}")
    print(str(exc)[:500])

# COMMAND ----------

# MAGIC %md
# MAGIC #### `.schema(...)` — contract omits a file column
# MAGIC
# MAGIC The file has **`discount_amount`**, but this contract does not list it.
# MAGIC Undeclared columns do not appear in the DataFrame.

# COMMAND ----------

mismatch_omit = (
    spark.read.format("avro")
    .schema(
        """
        trip_id bigint,
        payment_method string,
        base_fare_amount decimal(10,2),
        surge_amount decimal(10,2),
        tax_amount decimal(10,2),
        tip_amount decimal(10,2),
        driver_payout_amount decimal(10,2)
        """
    )
    .load(payment_avro_path)
)

print("File column omitted from contract → dropped from DataFrame:")
mismatch_omit.printSchema()
mismatch_omit.show(2)

# COMMAND ----------

# MAGIC %md
# MAGIC **`discount_amount`** is gone from the result.
# MAGIC
# MAGIC #### `avroSchema` — compatible evolution (official pattern)
# MAGIC
# MAGIC [Spark Avro docs](https://spark.apache.org/docs/latest/sql-data-sources-avro.html):
# MAGIC set **`avroSchema`** to an evolved Avro JSON schema that is **compatible
# MAGIC but different** from the file (for example one **additional field with a
# MAGIC default**). Deserialization follows the reader schema.
# MAGIC
# MAGIC We write a tiny practice Avro with a **known** writer schema, then read it
# MAGIC with a reader schema that adds **`region`**.

# COMMAND ----------

payment_avro_writer_schema = """
{
  "type": "record",
  "name": "PaymentEvent",
  "fields": [
    {"name": "trip_id", "type": "long"},
    {"name": "payment_method", "type": "string"}
  ]
}
"""

payment_avro_reader_schema = """
{
  "type": "record",
  "name": "PaymentEvent",
  "fields": [
    {"name": "trip_id", "type": "long"},
    {"name": "payment_method", "type": "string"},
    {"name": "region", "type": "string", "default": "unknown"}
  ]
}
"""

evolution_rows = spark.createDataFrame(
    [(1, "card"), (2, "cash")],
    "trip_id long, payment_method string",
)

(
    evolution_rows.write.format("avro")
    .option("avroSchema", payment_avro_writer_schema)
    .mode("overwrite")
    .save(avro_evolution_demo_path)
)

print(f"Wrote writer-schema Avro to {avro_evolution_demo_path}")

# COMMAND ----------

evolution_read = (
    spark.read.format("avro")
    .option("avroSchema", payment_avro_reader_schema)
    .load(avro_evolution_demo_path)
)

print("Reader schema adds region with default 'unknown':")
evolution_read.printSchema()
evolution_read.show()

# COMMAND ----------

# MAGIC %md
# MAGIC **`region`** appears with the default **`unknown`** even though the written
# MAGIC file never stored that field — that is Avro writer/reader resolution via
# MAGIC **`avroSchema`**, not a Catalyst **`.schema(...)`** cast.
# MAGIC
# MAGIC **Takeaway for ingestion:** keep a clear **`.schema(...)`** contract for
# MAGIC everyday reads; use **`avroSchema`** when you deliberately accept a
# MAGIC compatible Avro evolution. Do not expect **`.schema(...)`** to quietly
# MAGIC remap **`decimal` → `double`** or **`bigint` → `double`**.
# MAGIC
# MAGIC Continue with **`payment`** from section 4a.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Light reshape
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
# MAGIC ## 6. Avro round trip
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
# MAGIC - **When to use** — Avro for ingestion and record exchange; Parquet for
# MAGIC   analytical file storage and column-based queries
# MAGIC - **Avro syntax** — use **`format("avro").load(...)`** /
# MAGIC   **`format("avro").save(...)`** (no compact **`.avro(path)`** reader like
# MAGIC   Parquet)
# MAGIC - **Embedded schema** — types come from file metadata; no **`inferSchema`**
# MAGIC - **Explicit schema (DDL or `StructType`)** — still recommended for production
# MAGIC   contracts and validation
# MAGIC - **Schema mismatch** — **`.schema(...)`**: drop→nulls, omit→missing col,
# MAGIC   wrong type→usually **fails**; **`avroSchema`**: compatible Avro evolution
# MAGIC   (new field + default). Not the same as Parquet's quiet wrong-type reads
# MAGIC   (Notebook **04**)
# MAGIC - **Light reshape** — **`select`** fare columns before a practice write
# MAGIC - **Avro round trip** — writes a directory of part files; types are
# MAGIC   preserved on re-read (unlike CSV)
# MAGIC
# MAGIC **Next:** **07 - Write Patterns and Table Preview** — save modes, a brief
# MAGIC partitioned write, Delta file write under **`practice/`**, and managed
# MAGIC **`saveAsTable`** into **`rideshare_dev.processed`**.
