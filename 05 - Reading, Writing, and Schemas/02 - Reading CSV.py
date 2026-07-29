# Databricks notebook source
# MAGIC %md
# MAGIC # 02 - Reading CSV
# MAGIC
# MAGIC CSV is still one of the most common file formats in batch ingestion — exports
# MAGIC from legacy systems, ad hoc uploads, and partner feeds often arrive as
# MAGIC `.csv` files. The catch: CSV stores text only. Spark does not know your column
# MAGIC types until you tell it (or ask it to guess).
# MAGIC
# MAGIC This notebook reads the course **`trip`** dataset from the landing volume,
# MAGIC compares three read approaches, validates the result, handles a controlled
# MAGIC parsing failure, and writes a small practice output.
# MAGIC
# MAGIC **Learning objectives.** After this notebook, you will be able to:
# MAGIC - Read a CSV file from a Volume path under
# MAGIC   `/Volumes/rideshare_dev/landing/source_files/`
# MAGIC - Compare a default CSV read, **`inferSchema=True`**, and an explicit
# MAGIC   **`StructType`**
# MAGIC - Validate that the read schema matches the expected file layout
# MAGIC - Apply a light **`select`** reshape and write a practice CSV output
# MAGIC - Re-read a written CSV and see that Spark types are not preserved
# MAGIC
# MAGIC **Prerequisites.** Module 4 and **01 - Unity Catalog Volumes and Data
# MAGIC Landing** — landing volume populated with **`trip/trip.csv`**.
# MAGIC
# MAGIC **Setup.** Attach any compute with PySpark available. This notebook reads
# MAGIC from Volume paths only (not **`abfss://`** URLs).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup
# MAGIC
# MAGIC Import PySpark helpers and set paths for the **`trip`** dataset.
# MAGIC
# MAGIC Course **`trip`** columns (from `docs/data/dataset-overview.md`):
# MAGIC **`trip_id`** (bigint), **`service_type`** (string),
# MAGIC **`pickup_location_id`** (int), **`dropoff_location_id`** (int),
# MAGIC **`trip_distance_miles`** (decimal(8,2)), **`request_to_pickup_mins`**
# MAGIC (int), **`ride_duration_mins`** (int),
# MAGIC **`driver_arrival_to_pickup_mins`** (int).

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import (
    DecimalType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
)

landing_root = "/Volumes/rideshare_dev/landing/source_files"
trip_csv_path = f"{landing_root}/trip/trip.csv"
practice_root = "/Volumes/rideshare_dev/processed/output_files/practice"
practice_output_path = f"{practice_root}/trip_csv_roundtrip/"
malformed_demo_path = f"{practice_root}/malformed_csv_demo/"

trip_schema = StructType(
    [
        StructField("trip_id", LongType(), False),
        StructField("service_type", StringType(), False),
        StructField("pickup_location_id", IntegerType(), False),
        StructField("dropoff_location_id", IntegerType(), False),
        StructField("trip_distance_miles", DecimalType(8, 2), False),
        StructField("request_to_pickup_mins", IntegerType(), False),
        StructField("ride_duration_mins", IntegerType(), False),
        StructField("driver_arrival_to_pickup_mins", IntegerType(), False),
    ]
)

print(f"trip_csv_path = {trip_csv_path}")
print(f"practice_output_path = {practice_output_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Source path
# MAGIC
# MAGIC **`trip/trip.csv`** was copied into the landing volume in Notebook 01.
# MAGIC Format notebooks in this module read through **`/Volumes/...`** paths — Unity
# MAGIC Catalog resolves those paths to your external storage without hardcoding
# MAGIC **`abfss://`** URLs in every cell.

# COMMAND ----------

display(dbutils.fs.ls(f"{landing_root}/trip"))

# COMMAND ----------

# MAGIC %md
# MAGIC You should see **`trip.csv`** in that folder. The path variable
# MAGIC **`trip_csv_path`** points to the full file location for the reads below.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Default CSV read
# MAGIC
# MAGIC Start with the smallest option set: tell Spark the first row is a header.
# MAGIC Do **not** enable schema inference yet.

# COMMAND ----------

trip_strings = spark.read.option("header", True).csv(trip_csv_path)

print("Default read dtypes (expect all string):")
for name, dtype in trip_strings.dtypes:
    print(f"  {name}: {dtype}")

trip_strings.show(5)

# COMMAND ----------

# MAGIC %md
# MAGIC Every column arrived as **`string`**. That is Spark's safe default for CSV —
# MAGIC text files do not embed type metadata. If you leave types as strings, numeric
# MAGIC columns behave like text in filters and aggregations (Module 3 showed why
# MAGIC typing matters).

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Schema inference
# MAGIC
# MAGIC **`inferSchema=True`** asks Spark to scan the file and guess column types.
# MAGIC Convenient for exploration; less predictable in production.

# COMMAND ----------

trip_inferred = (
    spark.read.option("header", True).option("inferSchema", True).csv(trip_csv_path)
)

print("Inferred dtypes:")
for name, dtype in trip_inferred.dtypes:
    print(f"  {name}: {dtype}")

trip_inferred.show(5)

# COMMAND ----------

# MAGIC %md
# MAGIC Inference usually produces reasonable types on clean data, but it requires an
# MAGIC **extra pass over the file** to sample values. On large or messy feeds, guesses
# MAGIC can be wrong (for example, ID columns inferred as numbers when they should
# MAGIC stay strings). Module 4 also reminded you that anything that forces Spark to
# MAGIC inspect data — like **`count()`** — is an **action**. Treat inference as a
# MAGIC trade-off: less upfront work, less control.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Explicit schema
# MAGIC
# MAGIC The production pattern: define a **`StructType`** that matches the contract
# MAGIC you expect, then pass it to **`.schema(...)`**. Types are applied at read
# MAGIC time — no separate cast step needed when the file matches the contract.

# COMMAND ----------

trip = spark.read.option("header", True).schema(trip_schema).csv(trip_csv_path)

trip.printSchema()
trip.show(5)

# COMMAND ----------

# MAGIC %md
# MAGIC Use **`trip`** (explicit schema) for the rest of this notebook. When the
# MAGIC source layout is stable, explicit schemas make pipelines repeatable and
# MAGIC reviewable.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Schema validation
# MAGIC
# MAGIC After any read, confirm three things before downstream steps: Spark's schema,
# MAGIC column names, and a quick row sample. On small landing files, a row count is
# MAGIC cheap sanity check too.

# COMMAND ----------

print("Spark schema:")
trip.printSchema()

print(f"\nColumn names ({len(trip.columns)} columns):")
print(trip.columns)

print("\nSample rows:")
trip.show(5)

row_count = trip.count()
print(f"\nRow count: {row_count} (expect 100 for the course trip file)")

# COMMAND ----------

# MAGIC %md
# MAGIC **`printSchema()`** and **`.columns`** are transformations (they inspect
# MAGIC metadata). **`count()`** is an action — it executes the read plan and scans
# MAGIC the file. In production jobs, row-count checks often catch empty files or
# MAGIC partial loads early.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Malformed records
# MAGIC
# MAGIC Real feeds arrive with bad rows — missing fields, extra commas, truncated
# MAGIC lines. Do **not** edit the landed **`trip.csv`** to simulate this. Instead,
# MAGIC write a tiny demo file under **`practice/`** and read it with
# MAGIC **`FAILFAST`** vs **`PERMISSIVE`**.

# COMMAND ----------

malformed_csv_path = f"{malformed_demo_path}bad_trips.csv"

dbutils.fs.mkdirs(malformed_demo_path)
dbutils.fs.put(
    malformed_csv_path,
    """trip_id,service_type,trip_distance_miles
1,Standard,5.54
2,Premium
3,Standard,4.44
""",
    True,
)

print(f"Wrote demo file to {malformed_csv_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC Row 2 is missing the distance field. **`FAILFAST`** stops the read at the
# MAGIC first bad row — useful when bad data should halt the pipeline.

# COMMAND ----------

try:
    (
        spark.read.option("header", True)
        .option("mode", "FAILFAST")
        .csv(malformed_csv_path)
        .show()
    )
except Exception as exc:
    print(f"FAILFAST stopped the read: {type(exc).__name__}")
    print(str(exc)[:400])

# COMMAND ----------

# MAGIC %md
# MAGIC **`PERMISSIVE`** keeps good rows and parks corrupt lines in a
# MAGIC **`_corrupt_record`** column so you can inspect or quarantine them later.

# COMMAND ----------

(
    spark.read.option("header", True)
    .option("mode", "PERMISSIVE")
    .option("columnNameOfCorruptRecord", "_corrupt_record")
    .csv(malformed_csv_path)
    .show(truncate=False)
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Light reshape
# MAGIC
# MAGIC Before writing, **`select`** a small column set for a downstream preview.
# MAGIC This module stops at light reshape — deeper transforms belong in Module 6.

# COMMAND ----------

trip_subset = trip.select(
    F.col("trip_id"),
    F.col("service_type"),
    F.col("pickup_location_id"),
    F.col("trip_distance_miles"),
)

trip_subset.show(5)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. CSV round trip
# MAGIC
# MAGIC Write the subset to **`practice/trip_csv_roundtrip/`**, then read it back.
# MAGIC CSV is still text on disk — Spark does **not** remember that
# MAGIC **`trip_distance_miles`** was a decimal.

# COMMAND ----------

trip_subset.write.mode("overwrite").option("header", True).csv(practice_output_path)

print(f"Wrote CSV folder to {practice_output_path}")
display(dbutils.fs.ls(practice_output_path))

# COMMAND ----------

roundtrip_strings = spark.read.option("header", True).csv(practice_output_path)

print("Re-read without a schema (types revert to string):")
roundtrip_strings.printSchema()
roundtrip_strings.show(5)

# COMMAND ----------

trip_subset_schema = StructType(
    [
        StructField("trip_id", LongType(), False),
        StructField("service_type", StringType(), False),
        StructField("pickup_location_id", IntegerType(), False),
        StructField("trip_distance_miles", DecimalType(8, 2), False),
    ]
)

roundtrip_typed = (
    spark.read.option("header", True)
    .schema(trip_subset_schema)
    .csv(practice_output_path)
)

print("Re-read with explicit schema (types restored):")
roundtrip_typed.printSchema()
roundtrip_typed.show(5)

# COMMAND ----------

# MAGIC %md
# MAGIC We used **`.mode("overwrite")`** so re-running this cell replaces the prior
# MAGIC folder. Save modes in depth — append, error, ignore — are covered in
# MAGIC **07 - Write Patterns and Table Preview**. Parquet (next formats in this
# MAGIC module) preserves types without this round-trip loss.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Build a small practice extract without reusing **`trip_subset`**:
# MAGIC
# MAGIC 1. Read **`trip.csv`** again with the full **`trip_schema`** into a new
# MAGIC    DataFrame (do not reuse **`trip`** or **`trip_subset`**).
# MAGIC 2. **`select`** exactly these three columns: **`trip_id`**,
# MAGIC    **`dropoff_location_id`**, **`ride_duration_mins`**.
# MAGIC 3. Write the result to
# MAGIC    **`/Volumes/rideshare_dev/processed/output_files/practice/trip_exercise/`**
# MAGIC    with **`header=True`** and **`.mode("overwrite")`**.
# MAGIC 4. Re-read the written folder **with an explicit schema** for those three
# MAGIC    columns and print the schema. Confirm **`trip_id`** is **`bigint`** and
# MAGIC    the two integer columns are **`int`**, not **`string`**.

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - **Volume paths** — format reads use
# MAGIC   **`/Volumes/rideshare_dev/landing/source_files/...`**, not raw
# MAGIC   **`abfss://`** URLs
# MAGIC - **Default CSV read** — with **`header=True`** only, every column is
# MAGIC   **`string`**
# MAGIC - **`inferSchema=True`** — Spark guesses types after an extra data pass;
# MAGIC   fine for exploration, risky for production contracts
# MAGIC - **Explicit `StructType`** — recommended production pattern; types apply
# MAGIC   at read time
# MAGIC - **Validation** — check **`printSchema()`**, column names, samples, and
# MAGIC   row counts before trusting a landing file
# MAGIC - **Malformed rows** — **`FAILFAST`** halts early; **`PERMISSIVE`** +
# MAGIC   **`_corrupt_record`** quarantines bad lines for inspection
# MAGIC - **CSV round trip** — writing CSV loses Spark types; re-apply a schema on
# MAGIC   read (Parquet avoids this — coming up next)
# MAGIC
# MAGIC **Next:** **03 - Reading JSON** — read **`zone_lookup`** (JSON Lines) from
# MAGIC the landing volume.
