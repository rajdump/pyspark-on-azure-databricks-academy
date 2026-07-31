# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # 03 - Cleaning and Curated Outputs
# MAGIC
# MAGIC Landing data is loaded as-is from source files. Values may be missing,
# MAGIC inconsistently formatted, or out of range. Downstream joins and aggregations
# MAGIC in later modules depend on a clean, reliable `trip` and `payment` dataset.
# MAGIC
# MAGIC In this notebook you will review the Module 3 cleaning patterns — NULL-safe
# MAGIC predicates, normalize-before-drop, `F.coalesce`, and `try_cast` — on two
# MAGIC deliberately bad CSV files. You will then apply the relevant guards to
# MAGIC canonical landing CSV and Avro data and persist the results as curated Parquet.
# MAGIC
# MAGIC You will:
# MAGIC
# MAGIC 1. Re-read landing `trip` and `payment` with explicit schemas
# MAGIC 2. Clean landed bad-data `trip` and `payment` CSV files step by step
# MAGIC 3. Apply production-style guards to landing `trip` and write `curated/trip/`
# MAGIC 4. Apply production-style guards to landing `payment` and write `curated/payment/`
# MAGIC
# MAGIC **Prerequisites.** Complete Module 3 (NULL semantics, missing values, safe casts)
# MAGIC and Module 5 landing-data notebooks. The landing Volume must be populated.
# MAGIC This notebook reads landing data only — it does not read `practice/`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup
# MAGIC
# MAGIC | Dataset | Canonical source | Bad-data learning file | Curated output |
# MAGIC |---|---|---|---|
# MAGIC | `trip` | `trip/trip.csv` | `trip/bad_trip_data.csv` | `curated/trip/` |
# MAGIC | `payment` | `payment/payment.avro` | `payment/bad_payment_data.csv` | `curated/payment/` |
# MAGIC
# MAGIC Enrichment and cleaning columns (normalized labels, guards) are added only here —
# MAGIC not in Module 6, `01 - Column Transforms with Built-in Functions`.

# COMMAND ----------

from pyspark.sql import functions as F

landing_root = "/Volumes/rideshare_dev/landing/source_files"
trip_csv_path = f"{landing_root}/trip/trip.csv"
bad_trip_csv_path = f"{landing_root}/trip/bad_trip_data.csv"
payment_avro_path = f"{landing_root}/payment/payment.avro"
bad_payment_csv_path = f"{landing_root}/payment/bad_payment_data.csv"

curated_root = "/Volumes/rideshare_dev/processed/output_files/curated"
curated_trip_path = f"{curated_root}/trip"
curated_payment_path = f"{curated_root}/payment"

print(f"trip_csv_path       = {trip_csv_path}")
print(f"bad_trip_csv_path   = {bad_trip_csv_path}")
print(f"payment_avro_path   = {payment_avro_path}")
print(f"bad_payment_csv_path= {bad_payment_csv_path}")
print(f"curated_trip_path   = {curated_trip_path}")
print(f"curated_payment_path= {curated_payment_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Read landing `trip` and `payment` data
# MAGIC
# MAGIC Landing CSV does not carry type metadata; the explicit schema applies the
# MAGIC expected types at read time. Landing Avro already carries its schema, but
# MAGIC declaring it in code keeps the expected contract visible.

# COMMAND ----------

trip_schema_ddl = """
trip_id bigint,
service_type string,
pickup_location_id int,
dropoff_location_id int,
trip_distance_miles decimal(8,2),
request_to_pickup_mins int,
ride_duration_mins int,
driver_arrival_to_pickup_mins int
"""

trip_landing = (
    spark.read.format("csv")  # noqa: F821
    .option("header", "true")
    .schema(trip_schema_ddl)
    .load(trip_csv_path)
)

print("trip schema:")
trip_landing.printSchema()
trip_landing.show(3, truncate=False)

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

payment_landing = (
    spark.read.format("avro")  # noqa: F821
    .schema(payment_schema_ddl)
    .load(payment_avro_path)
)

print("payment schema:")
payment_landing.printSchema()
payment_landing.show(3, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Clean bad `trip` data step by step
# MAGIC
# MAGIC Before touching the canonical landing data, read `bad_trip_data.csv` and move
# MAGIC it through one forward-only cleaning chain. Every stage uses the DataFrame
# MAGIC produced by the preceding stage and displays proof of that change.
# MAGIC
# MAGIC Distance is intentionally read as a string so the same file can demonstrate
# MAGIC valid, malformed, negative, and missing numeric input.

# COMMAND ----------

bad_trip_schema_ddl = """
trip_id bigint,
service_type string,
pickup_location_id int,
dropoff_location_id int,
trip_distance_miles string,
request_to_pickup_mins int,
ride_duration_mins int,
driver_arrival_to_pickup_mins int
"""

bad_trip_raw = (
    spark.read.format("csv")  # noqa: F821
    .option("header", "true")
    .schema(bad_trip_schema_ddl)
    .load(bad_trip_csv_path)
    .withColumnRenamed("trip_distance_miles", "trip_distance_raw")
)

print("Bad trip source:")
bad_trip_raw.printSchema()
bad_trip_raw.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2a. Filter rows with no `trip_id`
# MAGIC
# MAGIC A missing `trip_id` makes a row unjoinable. `isNotNull()` gives a definite
# MAGIC answer even when the column value is `NULL`. Store the retained complete rows
# MAGIC in a new DataFrame before continuing.

# COMMAND ----------

trip_key_filtered = bad_trip_raw.filter(F.col("trip_id").isNotNull())

print("Rejected rows with no trip_id (should see one):")
bad_trip_raw.filter(F.col("trip_id").isNull()).show(truncate=False)

print(f"Before key filter: {bad_trip_raw.count()}")
print(f"After key filter : {trip_key_filtered.count()}")
trip_key_filtered.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2b. Normalize `service_type`, then replace sentinels
# MAGIC
# MAGIC Normalize the label first (`F.trim` + `F.upper`) so `"standard"`, `"Standard"`,
# MAGIC and `" STANDARD "` all become `"STANDARD"` before any comparison. Then filter
# MAGIC or replace known sentinels. This example converts the padded, lowercase sentinel
# MAGIC `" n/a "` to `NULL` and preserves its row for the `F.coalesce` decision in
# MAGIC section 2e.

# COMMAND ----------

trip_service_normalized = trip_key_filtered.withColumn(
    "service_type_clean",
    F.upper(F.trim(F.col("service_type"))),
)

print("After normalization:")
trip_service_normalized.select(
    "trip_id",
    "service_type",
    "service_type_clean",
).show(truncate=False)

# COMMAND ----------

trip_sentinels_replaced = trip_service_normalized.withColumn(
    "service_type_clean",
    F.when(F.col("service_type_clean") == "N/A", F.lit(None)).otherwise(
        F.col("service_type_clean")
    ),
)

print("After converting sentinel 'N/A' to NULL:")
trip_sentinels_replaced.select(
    "trip_id",
    "service_type",
    "service_type_clean",
).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2c. Safely cast string distances
# MAGIC
# MAGIC `try_cast` converts valid numeric strings to decimal and returns `NULL` for
# MAGIC malformed input instead of raising an error under Spark 4 / ANSI mode. Detect
# MAGIC rejected input when the raw value is not NULL but the cast result is NULL.

# COMMAND ----------

trip_distance_casted = trip_sentinels_replaced.withColumn(
    "trip_distance_miles",
    F.col("trip_distance_raw").try_cast("decimal(8,2)"),
)

print("After try_cast:")
trip_distance_casted.select(
    "trip_id",
    "trip_distance_raw",
    "trip_distance_miles",
).show(truncate=False)

print("Rows rejected by the cast:")
trip_distance_casted.filter(
    F.col("trip_distance_raw").isNotNull() & F.col("trip_distance_miles").isNull()
).select("trip_id", "trip_distance_raw", "trip_distance_miles").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2d. Guard against out-of-range distances
# MAGIC
# MAGIC A negative trip distance cannot be correct. Replace it with `NULL` using
# MAGIC `F.when` rather than dropping the whole row — the other columns may still be
# MAGIC useful.

# COMMAND ----------

trip_distance_checked = trip_distance_casted.withColumn(
    "trip_distance_miles",
    F.when(F.col("trip_distance_miles") >= 0, F.col("trip_distance_miles")).otherwise(F.lit(None)),
)

print("After nulling negative distances:")
trip_distance_checked.select(
    "trip_id",
    "trip_distance_raw",
    "trip_distance_miles",
).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2e. Fill missing labels with `F.coalesce`
# MAGIC
# MAGIC `F.coalesce` returns the first non-NULL expression. Use `"UNKNOWN"` when the
# MAGIC row is still useful but a descriptive label is missing. The required-key
# MAGIC decision already happened in section 2a.

# COMMAND ----------

trip_sample_cleaned = trip_distance_checked.withColumn(
    "service_type_clean",
    F.coalesce(F.col("service_type_clean"), F.lit("UNKNOWN")),
)

print("Final cleaned trip learning sample:")
trip_sample_cleaned.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Clean landing `trip` data
# MAGIC
# MAGIC Apply the relevant guards to the full landing `trip` dataset:
# MAGIC
# MAGIC - Drop rows where `trip_id` is NULL — they cannot be matched in an equality
# MAGIC   join.
# MAGIC - Normalize `service_type`: trim whitespace and standardize to uppercase.
# MAGIC   The real landing CSV does not contain sentinel values such as `"N/A"`, so
# MAGIC   normalization alone is sufficient here — no sentinel filter is needed.
# MAGIC - NULL out negative `trip_distance_miles` and non-positive `ride_duration_mins`.
# MAGIC   For this course, treat these values as invalid — the dataset contract in
# MAGIC   `dataset-overview.md` defines their types only, not this domain rule.
# MAGIC - Preserve all join keys (`trip_id`, `pickup_location_id`,
# MAGIC   `dropoff_location_id`) and all source columns at the same row grain.
# MAGIC
# MAGIC The landing `trip` data has no NULL `trip_id`, sentinel `service_type`
# MAGIC values, or out-of-range distances/durations, so the row counts below are
# MAGIC expected to match — these guards protect the pipeline if a future load
# MAGIC introduces one of these problems.

# COMMAND ----------

trip_clean = (
    trip_landing.filter(F.col("trip_id").isNotNull())
    .withColumn(
        "service_type",
        F.upper(F.trim(F.col("service_type"))),
    )
    .withColumn(
        "trip_distance_miles",
        F.when(F.col("trip_distance_miles") >= 0, F.col("trip_distance_miles")).otherwise(
            F.lit(None)
        ),
    )
    .withColumn(
        "ride_duration_mins",
        F.when(F.col("ride_duration_mins") > 0, F.col("ride_duration_mins")).otherwise(F.lit(None)),
    )
)

print(f"Landing trip row count : {trip_landing.count()}")
print(f"Cleaned trip row count : {trip_clean.count()}")
trip_clean.show(5, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Clean `payment` data
# MAGIC
# MAGIC First prove the payment guards on `bad_payment_data.csv`, then apply the same
# MAGIC rules to the canonical landing Avro data.
# MAGIC
# MAGIC - Drop rows where `trip_id` is NULL.
# MAGIC - Normalize `payment_method`: trim and uppercase.
# MAGIC - NULL out negative `base_fare_amount`. For this course, treat a negative
# MAGIC   base fare as a data quality problem rather than a valid value.
# MAGIC - Preserve `trip_id` and all fare columns at the same row grain.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4a. Prove the guards on bad payment data

# COMMAND ----------

bad_payment_raw = (
    spark.read.format("csv")  # noqa: F821
    .option("header", "true")
    .schema(payment_schema_ddl)
    .load(bad_payment_csv_path)
)

print("Bad payment source:")
bad_payment_raw.show(truncate=False)

# COMMAND ----------

payment_sample_key_filtered = bad_payment_raw.filter(F.col("trip_id").isNotNull())

print("Rejected payment rows with no trip_id (should see one):")
bad_payment_raw.filter(F.col("trip_id").isNull()).show(truncate=False)

print(f"Before key filter: {bad_payment_raw.count()}")
print(f"After key filter : {payment_sample_key_filtered.count()}")
payment_sample_key_filtered.show(truncate=False)

# COMMAND ----------

payment_sample_method_normalized = payment_sample_key_filtered.withColumn(
    "payment_method",
    F.upper(F.trim(F.col("payment_method"))),
)

print("After payment_method normalization:")
payment_sample_method_normalized.select("trip_id", "payment_method").show(truncate=False)

# COMMAND ----------

payment_sample_base_fare_checked = payment_sample_method_normalized.withColumn(
    "base_fare_amount",
    F.when(F.col("base_fare_amount") >= 0, F.col("base_fare_amount")).otherwise(F.lit(None)),
)

print("After nulling negative base fares:")
payment_sample_base_fare_checked.select(
    "trip_id",
    "payment_method",
    "base_fare_amount",
).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4b. Apply the guards to canonical landing payment
# MAGIC
# MAGIC The canonical landing data has no NULL `trip_id` or negative
# MAGIC `base_fare_amount` values, so the row counts below are expected to match.

# COMMAND ----------

payment_clean = (
    payment_landing.filter(F.col("trip_id").isNotNull())
    .withColumn(
        "payment_method",
        F.upper(F.trim(F.col("payment_method"))),
    )
    .withColumn(
        "base_fare_amount",
        F.when(F.col("base_fare_amount") >= 0, F.col("base_fare_amount")).otherwise(F.lit(None)),
    )
)

print(f"Landing payment row count : {payment_landing.count()}")
print(f"Cleaned payment row count : {payment_clean.count()}")
payment_clean.show(5, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Write curated outputs
# MAGIC
# MAGIC Write both cleaned DataFrames as Parquet with `.mode("overwrite")`. Module 7
# MAGIC reads these curated folders when it joins `trip`, `payment`, and `zone_lookup`.

# COMMAND ----------

trip_clean.write.mode("overwrite").parquet(curated_trip_path)
print(f"Wrote curated trip to {curated_trip_path}")

# COMMAND ----------

payment_clean.write.mode("overwrite").parquet(curated_payment_path)
print(f"Wrote curated payment to {curated_payment_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC Read back a sample from each curated folder to confirm the writes succeeded.

# COMMAND ----------

print("Curated trip sample:")
spark.read.parquet(curated_trip_path).show(5, truncate=False)  # noqa: F821

print("Curated payment sample:")
spark.read.parquet(curated_payment_path).show(5, truncate=False)  # noqa: F821

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC `bad_payment_data.csv` also contains a missing `tip_amount` and a negative
# MAGIC `surge_amount`. Start with `payment_sample_base_fare_checked` from section 4,
# MAGIC then apply two more guards:
# MAGIC
# MAGIC 1. Keep only rows where `tip_amount` is NOT NULL.
# MAGIC 2. NULL out any `surge_amount` that is negative (use `F.when`).
# MAGIC
# MAGIC Display the result. Do not write it.

# COMMAND ----------

payment_exercise = payment_sample_base_fare_checked.filter(
    F.lit(True)  # TODO: replace with an isNotNull predicate for tip_amount
)
# TODO: add a withColumn on surge_amount that uses F.when to NULL out negative
# values and otherwise keeps the original surge_amount.

payment_exercise.select("trip_id", "tip_amount", "surge_amount").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - **NULL-safe predicates** — use `isNotNull()` to remove rows missing a
# MAGIC   required key such as `trip_id` before an ordinary equality join.
# MAGIC - **Normalize before drop** — apply `F.trim` and `F.upper` before comparing,
# MAGIC   replacing, or dropping sentinel values.
# MAGIC - **`F.coalesce`** — supply a fallback when a descriptive value is missing but
# MAGIC   the row should remain.
# MAGIC - **Out-of-range guards** — use `F.when` to NULL unphysical values rather than
# MAGIC   dropping the whole row.
# MAGIC - **`try_cast`** — converts string inputs to typed values safely; use
# MAGIC   `source.isNotNull() & casted.isNull()` to surface rows the cast rejected.
# MAGIC - Wrote curated Parquet outputs to `curated/trip/` and `curated/payment/`.
# MAGIC
# MAGIC **Next:** Module 6 **`04 - Built-ins First: When (Not) to Use UDFs`** — compare
# MAGIC built-in functions to Python UDFs and Pandas UDFs.
