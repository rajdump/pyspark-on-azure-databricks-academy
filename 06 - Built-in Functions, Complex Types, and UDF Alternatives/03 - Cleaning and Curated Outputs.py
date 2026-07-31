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
# MAGIC predicates, normalize-before-drop, `F.coalesce`, and `try_cast` — on messy demo
# MAGIC data. You will then apply the relevant guards to landing CSV and Avro data and
# MAGIC persist the results as curated Parquet.
# MAGIC
# MAGIC You will:
# MAGIC
# MAGIC 1. Re-read landing `trip` and `payment` with explicit schemas
# MAGIC 2. Work through a small messy demo slice to preview each cleaning rule
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
# MAGIC | Dataset | Source | Curated output (under `curated/`) |
# MAGIC |---|---|---|
# MAGIC | `trip` | Landing CSV | `trip/` |
# MAGIC | `payment` | Landing Avro | `payment/` |
# MAGIC
# MAGIC Enrichment and cleaning columns (normalized labels, guards) are added only here —
# MAGIC not in Module 6, `01 - Column Transforms with Built-in Functions`.

# COMMAND ----------

from decimal import Decimal

from pyspark.sql import functions as F

landing_root = "/Volumes/rideshare_dev/landing/source_files"
trip_csv_path = f"{landing_root}/trip/trip.csv"
payment_avro_path = f"{landing_root}/payment/payment.avro"

curated_root = "/Volumes/rideshare_dev/processed/output_files/curated"
curated_trip_path = f"{curated_root}/trip"
curated_payment_path = f"{curated_root}/payment"

print(f"trip_csv_path       = {trip_csv_path}")
print(f"payment_avro_path   = {payment_avro_path}")
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
# MAGIC ## 2. Cleaning patterns on a messy demo slice
# MAGIC
# MAGIC Before touching the real landing data, work through each cleaning rule on a
# MAGIC small hand-built DataFrame. This makes the effect of each guard easy to see
# MAGIC in isolation.
# MAGIC
# MAGIC The slice mimics `trip` column names and types, but contains deliberate
# MAGIC problems: a missing `trip_id`, a missing or sentinel `service_type`, and a
# MAGIC negative distance.

# COMMAND ----------

messy_rows = [
    (1, "Premium", 5, 9, Decimal("4.20"), 4, 24, 1),
    (2, " n/a ", 18, 14, Decimal("5.14"), 11, 17, 1),
    (3, "standard", 12, 20, Decimal("-1.00"), 2, 19, 1),
    (None, "premium", 10, 3, Decimal("12.12"), 3, 43, 2),
    (4, None, 7, 16, Decimal("6.75"), 5, 22, 2),
]

messy_trip = spark.createDataFrame(  # noqa: F821
    messy_rows,
    schema=trip_schema_ddl,
)

print("Messy demo slice:")
messy_trip.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2a. NULL-safe predicate — drop rows with no `trip_id`
# MAGIC
# MAGIC A missing `trip_id` makes a row unjoinable. `isNotNull()` gives a definite
# MAGIC answer even when the column value is `NULL`.

# COMMAND ----------

print("Rows missing trip_id (should see one):")
messy_trip.filter(F.col("trip_id").isNull()).show(truncate=False)

print("Rows with valid trip_id:")
messy_trip.filter(F.col("trip_id").isNotNull()).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2b. Normalize-before-drop — clean `service_type` before handling sentinels
# MAGIC
# MAGIC Normalize the label first (`F.trim` + `F.upper`) so `"standard"`, `"Standard"`,
# MAGIC and `" STANDARD "` all become `"STANDARD"` before any comparison. Then filter
# MAGIC or replace known sentinels. This example converts the padded, lowercase sentinel
# MAGIC `" n/a "` to `NULL` and preserves its row for the `F.coalesce` decision in
# MAGIC section 2d.

# COMMAND ----------

messy_normalized = messy_trip.withColumn(
    "service_type_clean",
    F.upper(F.trim(F.col("service_type"))),
)

print("After normalization:")
messy_normalized.select("trip_id", "service_type", "service_type_clean").show(truncate=False)

messy_with_sentinel_null = messy_normalized.withColumn(
    "service_type_clean",
    F.when(F.col("service_type_clean") == "N/A", F.lit(None)).otherwise(
        F.col("service_type_clean")
    ),
)

print("After converting sentinel 'N/A' to NULL:")
messy_with_sentinel_null.select(
    "trip_id",
    "service_type",
    "service_type_clean",
).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2c. Guard against out-of-range values — NULL negative distances
# MAGIC
# MAGIC A negative trip distance cannot be correct. Replace it with `NULL` using
# MAGIC `F.when` rather than dropping the whole row — the other columns may still be
# MAGIC useful for the curated output.

# COMMAND ----------

messy_distance = messy_trip.withColumn(
    "trip_distance_miles",
    F.when(F.col("trip_distance_miles") >= 0, F.col("trip_distance_miles")).otherwise(F.lit(None)),
)

print("trip_distance_miles after nulling negatives:")
messy_distance.select("trip_id", "trip_distance_miles").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2d. Fill a missing label with `F.coalesce`
# MAGIC
# MAGIC `F.coalesce` returns the first non-NULL expression. Use a fallback such as
# MAGIC `"UNKNOWN"` when the row is still useful but a descriptive label is missing.
# MAGIC Drop the row instead when a required key such as `trip_id` is NULL.

# COMMAND ----------

messy_with_service_fallback = messy_with_sentinel_null.withColumn(
    "service_type_clean",
    F.coalesce(F.col("service_type_clean"), F.lit("UNKNOWN")),
)

print("Missing and sentinel service_type values filled with 'UNKNOWN':")
messy_with_service_fallback.select(
    "trip_id",
    "service_type",
    "service_type_clean",
).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2e. Safe cast — `try_cast` when string inputs could be malformed
# MAGIC
# MAGIC When a column arrives as string but must be numeric, `try_cast` returns `NULL`
# MAGIC for unparseable values instead of raising an error under Spark 4 / ANSI mode.
# MAGIC
# MAGIC Detect rejected rows with `source.isNotNull() & casted.isNull()`.

# COMMAND ----------

# Build a small slice where distance arrives as string (simulating a file
# without a declared schema).
string_rows = [(1, "4.20"), (2, "not_a_number"), (3, None)]
string_df = spark.createDataFrame(  # noqa: F821
    string_rows,
    schema="trip_id bigint, distance_raw string",
)

string_df = string_df.withColumn(
    "trip_distance_miles",
    F.col("distance_raw").try_cast("decimal(8,2)"),
)

print("After try_cast:")
string_df.show(truncate=False)

print("Rows rejected by the cast (raw not null but casted is null):")
string_df.filter(F.col("distance_raw").isNotNull() & F.col("trip_distance_miles").isNull()).show(
    truncate=False
)

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
# MAGIC ## 4. Clean landing `payment` data
# MAGIC
# MAGIC Apply guards to the full landing `payment` dataset:
# MAGIC
# MAGIC - Drop rows where `trip_id` is NULL.
# MAGIC - Normalize `payment_method`: trim and uppercase.
# MAGIC - NULL out negative `base_fare_amount`. For this course, treat a negative
# MAGIC   base fare as a data quality problem rather than a valid value.
# MAGIC - Preserve `trip_id` and all fare columns at the same row grain as landing.
# MAGIC
# MAGIC The landing `payment` data has no NULL `trip_id` or negative
# MAGIC `base_fare_amount` values, so the row counts below are expected to match
# MAGIC for the same reason.

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
# MAGIC The real landing `payment` data has no missing `tip_amount` values and no
# MAGIC negative `surge_amount` values, so these guards would have no visible effect
# MAGIC on `payment_landing` directly. Build a small messy `payment` slice instead
# MAGIC (same approach as section 2), then apply two guards:
# MAGIC
# MAGIC 1. Keep only rows where `tip_amount` is NOT NULL.
# MAGIC 2. NULL out any `surge_amount` that is negative (use `F.when`).
# MAGIC
# MAGIC Display the result. Do not write it.

# COMMAND ----------

exercise_payment_rows = [
    (
        101,
        "CARD",
        Decimal("18.50"),
        Decimal("2.00"),
        Decimal("1.50"),
        Decimal("3.00"),
        Decimal("0.00"),
        Decimal("15.00"),
    ),
    (
        102,
        "CASH",
        Decimal("22.00"),
        Decimal("-1.50"),
        Decimal("1.80"),
        Decimal("4.50"),
        Decimal("0.00"),
        Decimal("18.00"),
    ),
    (
        103,
        "WALLET",
        Decimal("9.75"),
        Decimal("0.75"),
        Decimal("0.80"),
        None,
        Decimal("0.00"),
        Decimal("8.00"),
    ),
]
payment_exercise_raw = spark.createDataFrame(  # noqa: F821
    exercise_payment_rows,
    schema=payment_schema_ddl,
)

payment_exercise = payment_exercise_raw.filter(
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
