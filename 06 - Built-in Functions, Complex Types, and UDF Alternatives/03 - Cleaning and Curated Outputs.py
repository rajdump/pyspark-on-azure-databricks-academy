# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # 03 - Cleaning and Curated Outputs
# MAGIC
# MAGIC A clear cleaning pipeline should start with the source data that needs cleaning and
# MAGIC carry that same data through to the curated output. The two CSV files in this
# MAGIC notebook contain the original 100 course records plus a small set of controlled bad
# MAGIC records. This gives each dataset one complete path from source to curated files.
# MAGIC
# MAGIC You will:
# MAGIC
# MAGIC 1. Read every CSV field as text so malformed values do not stop the read.
# MAGIC 2. Safely cast fields while retaining the raw values needed for diagnosis.
# MAGIC 3. Reject records without a usable key, normalize labels, and convert invalid
# MAGIC    numeric values to NULL.
# MAGIC 4. Add the existing Module 6 enrichment columns to the cleaned DataFrames.
# MAGIC 5. Write and validate the curated `trip` and `payment` outputs.
# MAGIC
# MAGIC **Prerequisites.** Complete Module 6 **`01 - Column Transforms with Built-in
# MAGIC Functions`** and **`02 - Complex Types: Structs, Arrays, and explode`**. Run Module
# MAGIC 5 **`01 - Unity Catalog Volumes and Data Landing`** so both controlled-bad CSV files
# MAGIC exist in the landing Volume.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup
# MAGIC
# MAGIC Both source files use the canonical column names, but every field is read as a
# MAGIC string. `try_cast` can then return NULL for malformed text without stopping the
# MAGIC notebook under ANSI mode.
# MAGIC
# MAGIC The source files contain:
# MAGIC
# MAGIC - `bad_trip_data.csv`: 100 original trip records and 7 controlled bad records
# MAGIC - `bad_payment_data.csv`: 100 original payment records and 6 controlled bad records
# MAGIC
# MAGIC One record in each file has no `trip_id` and will be rejected. The other controlled
# MAGIC records remain after their values are cleaned.

# COMMAND ----------

from pyspark.sql import functions as F

landing_root = "/Volumes/rideshare_dev/landing/source_files"
curated_root = "/Volumes/rideshare_dev/processed/output_files/curated"

trip_source_path = f"{landing_root}/trip/bad_trip_data.csv"
payment_source_path = f"{landing_root}/payment/bad_payment_data.csv"

curated_trip_path = f"{curated_root}/trip"
curated_payment_path = f"{curated_root}/payment"

print(f"trip_source_path = {trip_source_path}")
print(f"payment_source_path = {payment_source_path}")
print(f"curated_trip_path = {curated_trip_path}")
print(f"curated_payment_path = {curated_payment_path}")

# COMMAND ----------

trip_string_schema_ddl = """
trip_id string,
service_type string,
pickup_location_id string,
dropoff_location_id string,
trip_distance_miles string,
request_to_pickup_mins string,
ride_duration_mins string,
driver_arrival_to_pickup_mins string
"""

payment_string_schema_ddl = """
trip_id string,
payment_method string,
base_fare_amount string,
surge_amount string,
tax_amount string,
tip_amount string,
discount_amount string,
driver_payout_amount string
"""

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Clean and enrich trip data
# MAGIC
# MAGIC The trip source contains controlled examples of casing and whitespace, sentinel and
# MAGIC blank labels, malformed numeric text, a negative distance, a blank distance, and a
# MAGIC missing key.
# MAGIC
# MAGIC The pipeline will:
# MAGIC
# MAGIC - cast each typed field with `try_cast`
# MAGIC - retain the raw key and distance text for diagnosis
# MAGIC - isolate and reject the record whose `trip_id` becomes NULL
# MAGIC - trim and lowercase `service_type`; map blanks and `n/a` to `unknown`
# MAGIC - convert malformed or non-positive distance values to NULL
# MAGIC - convert negative duration and wait values to NULL while keeping zero as valid

# COMMAND ----------

trip_source = (
    spark.read.format(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
        "csv"
    )
    .option("header", "true")
    .schema(trip_string_schema_ddl)
    .load(trip_source_path)
)

print("Controlled trip source records:")
trip_source.filter(
    F.col("trip_id").isin("101", "102", "103", "104", "105", "106")
    | F.col("trip_id").isNull()
    | (F.trim(F.col("trip_id")) == "")
).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Safely cast typed fields
# MAGIC
# MAGIC `trip_distance_miles_src` keeps the original text beside the cast result. A
# MAGIC nonblank raw value followed by a NULL cast result identifies malformed numeric
# MAGIC text. A blank CSV field is read as NULL, so it remains distinguishable from a
# MAGIC failed conversion.

# COMMAND ----------

trip_cast = (
    trip_source.withColumn("trip_id_src", F.col("trip_id"))
    .withColumn("trip_id", F.col("trip_id").try_cast("bigint"))
    .withColumn(
        "pickup_location_id",
        F.col("pickup_location_id").try_cast("int"),
    )
    .withColumn(
        "dropoff_location_id",
        F.col("dropoff_location_id").try_cast("int"),
    )
    .withColumn("trip_distance_miles_src", F.col("trip_distance_miles"))
    .withColumn(
        "trip_distance_miles",
        F.col("trip_distance_miles").try_cast("decimal(8,2)"),
    )
    .withColumn(
        "request_to_pickup_mins",
        F.col("request_to_pickup_mins").try_cast("int"),
    )
    .withColumn(
        "ride_duration_mins",
        F.col("ride_duration_mins").try_cast("int"),
    )
    .withColumn(
        "driver_arrival_to_pickup_mins",
        F.col("driver_arrival_to_pickup_mins").try_cast("int"),
    )
)

print("Trip records where distance text was present but try_cast returned NULL:")
trip_cast.filter(
    F.col("trip_distance_miles_src").isNotNull()
    & (F.trim(F.col("trip_distance_miles_src")) != "")
    & F.col("trip_distance_miles").isNull(),
).select(
    F.col("trip_id"),
    F.col("trip_distance_miles_src"),
    F.col("trip_distance_miles"),
).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Reject records without a usable key
# MAGIC
# MAGIC A required key controls the row grain and later joins. Keep the rejected record
# MAGIC visible for diagnosis, then carry only non-NULL keys into the next stage.

# COMMAND ----------

trip_rejected = trip_cast.filter(F.col("trip_id").isNull())

print("Rejected trip records:")
trip_rejected.select(
    F.col("trip_id_src"),
    F.col("service_type"),
    F.col("pickup_location_id"),
).show(truncate=False)

trip_key_filtered = trip_cast.filter(F.col("trip_id").isNotNull())

# COMMAND ----------

# MAGIC %md
# MAGIC ### Normalize service labels
# MAGIC
# MAGIC Normalize before checking for sentinels so values such as `" n/a "` become
# MAGIC `"n/a"` first. Blank, NULL, and `n/a` labels then become `unknown`.

# COMMAND ----------

trip_labels_normalized = trip_key_filtered.withColumn(
    "service_type",
    F.lower(F.trim(F.col("service_type"))),
).withColumn(
    "service_type",
    F.coalesce(
        F.when(
            ~F.col("service_type").isin("", "n/a"),
            F.col("service_type"),
        ),
        F.lit("unknown"),
    ),
)

print("Controlled trip labels after normalization:")
trip_labels_normalized.filter(F.col("trip_id").between(101, 106)).select(
    F.col("trip_id"),
    F.col("service_type"),
).orderBy(F.col("trip_id")).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Convert invalid numeric values to NULL
# MAGIC
# MAGIC `try_cast` has already converted malformed numeric text to NULL. The conditions
# MAGIC below also convert values outside the course rules to NULL: distance must be
# MAGIC positive, while duration and wait values may be zero but not negative.

# COMMAND ----------

trip_values_checked = (
    trip_labels_normalized.withColumn(
        "trip_distance_miles",
        F.when(
            F.col("trip_distance_miles") > 0,
            F.col("trip_distance_miles"),
        ).otherwise(F.lit(None).cast("decimal(8,2)")),
    )
    .withColumn(
        "request_to_pickup_mins",
        F.when(
            F.col("request_to_pickup_mins") >= 0,
            F.col("request_to_pickup_mins"),
        ),
    )
    .withColumn(
        "ride_duration_mins",
        F.when(
            F.col("ride_duration_mins") >= 0,
            F.col("ride_duration_mins"),
        ),
    )
    .withColumn(
        "driver_arrival_to_pickup_mins",
        F.when(
            F.col("driver_arrival_to_pickup_mins") >= 0,
            F.col("driver_arrival_to_pickup_mins"),
        ),
    )
)

print("Controlled trip distances after cleaning:")
trip_values_checked.filter(F.col("trip_id").between(101, 106)).select(
    F.col("trip_id"),
    F.col("trip_distance_miles_src"),
    F.col("trip_distance_miles"),
).orderBy(F.col("trip_id")).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Validate controlled trip outcomes
# MAGIC
# MAGIC These assertions check the expected row counts and representative outcomes before
# MAGIC enrichment or writing.

# COMMAND ----------

trip_source_count = trip_source.count()
trip_rejected_count = trip_rejected.count()
trip_retained_count = trip_values_checked.count()

print(
    "Trip rows: "
    f"source={trip_source_count}, "
    f"rejected={trip_rejected_count}, "
    f"retained={trip_retained_count}"
)

assert trip_source_count == 107
assert trip_rejected_count == 1
assert trip_retained_count == 106

assert (
    trip_values_checked.filter(
        (F.col("trip_id") == 101) & (F.col("service_type") == "premium")
    ).count()
    == 1
)
assert (
    trip_values_checked.filter(
        (F.col("trip_id") == 102) & (F.col("service_type") == "unknown")
    ).count()
    == 1
)
assert (
    trip_values_checked.filter(
        (F.col("trip_id") == 104) & (F.col("service_type") == "unknown")
    ).count()
    == 1
)
assert (
    trip_values_checked.filter(
        (F.col("trip_id").isin(103, 105, 106)) & F.col("trip_distance_miles").isNull()
    ).count()
    == 3
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Add trip enrichments and select the curated contract
# MAGIC
# MAGIC The enrichment columns come from Module 6 **`01 - Column Transforms with Built-in
# MAGIC Functions`**. The explicit NULL branch in `ride_duration_band` prevents a missing
# MAGIC duration from being mislabeled as a long ride.

# COMMAND ----------

trip_clean = (
    trip_values_checked.withColumn(
        "service_type_standardized",
        F.upper(F.col("service_type")),
    )
    .withColumn(
        "service_label",
        F.concat_ws(
            "-",
            F.lit("SERVICE"),
            F.upper(F.col("service_type")),
        ),
    )
    .withColumn(
        "trip_distance_km",
        F.round(F.col("trip_distance_miles") * F.lit(1.60934), 2),
    )
    .withColumn(
        "request_to_driver_arrival_mins",
        F.col("request_to_pickup_mins") - F.col("driver_arrival_to_pickup_mins"),
    )
    .withColumn(
        "ride_minus_wait_to_pickup_mins",
        F.col("ride_duration_mins") - F.col("request_to_pickup_mins"),
    )
    .withColumn(
        "ride_wait_to_pickup_gap_mins",
        F.abs(F.col("ride_duration_mins") - F.col("request_to_pickup_mins")),
    )
    .withColumn(
        "ride_duration_band",
        F.when(F.col("ride_duration_mins").isNull(), F.lit(None).cast("string"))
        .when(F.col("ride_duration_mins") < 15, "short")
        .when(F.col("ride_duration_mins") < 30, "medium")
        .otherwise("long"),
    )
    .select(
        F.col("trip_id"),
        F.col("service_type"),
        F.col("service_type_standardized"),
        F.col("service_label"),
        F.col("pickup_location_id"),
        F.col("dropoff_location_id"),
        F.col("trip_distance_miles"),
        F.col("trip_distance_km"),
        F.col("request_to_pickup_mins"),
        F.col("ride_duration_mins"),
        F.col("driver_arrival_to_pickup_mins"),
        F.col("request_to_driver_arrival_mins"),
        F.col("ride_minus_wait_to_pickup_mins"),
        F.col("ride_wait_to_pickup_gap_mins"),
        F.col("ride_duration_band"),
    )
)

trip_clean_count = trip_clean.count()
assert trip_clean_count == 106

trip_clean.orderBy(F.col("trip_id")).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Clean and enrich payment data
# MAGIC
# MAGIC The payment source contains controlled examples of casing and whitespace, a blank
# MAGIC label, malformed optional numeric text, negative amounts, and a missing key.
# MAGIC
# MAGIC The pipeline will:
# MAGIC
# MAGIC - cast the key and each amount with `try_cast`
# MAGIC - retain the raw key and selected amount text for diagnosis
# MAGIC - isolate and reject the record whose `trip_id` becomes NULL
# MAGIC - trim and lowercase `payment_method`; map blanks to `unknown`
# MAGIC - convert malformed or negative amounts to NULL

# COMMAND ----------

payment_source = (
    spark.read.format(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
        "csv"
    )
    .option("header", "true")
    .schema(payment_string_schema_ddl)
    .load(payment_source_path)
)

print("Controlled payment source records:")
payment_source.filter(
    F.col("trip_id").isin("101", "102", "103", "104", "105")
    | F.col("trip_id").isNull()
    | (F.trim(F.col("trip_id")) == "")
).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Safely cast typed fields
# MAGIC
# MAGIC The raw base fare, surge, and tip values stay beside their cast results because the
# MAGIC controlled records use those fields to demonstrate different invalid inputs.

# COMMAND ----------

payment_cast = (
    payment_source.withColumn("trip_id_src", F.col("trip_id"))
    .withColumn("trip_id", F.col("trip_id").try_cast("bigint"))
    .withColumn("base_fare_amount_src", F.col("base_fare_amount"))
    .withColumn(
        "base_fare_amount",
        F.col("base_fare_amount").try_cast("decimal(10,2)"),
    )
    .withColumn("surge_amount_src", F.col("surge_amount"))
    .withColumn(
        "surge_amount",
        F.col("surge_amount").try_cast("decimal(10,2)"),
    )
    .withColumn(
        "tax_amount",
        F.col("tax_amount").try_cast("decimal(10,2)"),
    )
    .withColumn("tip_amount_src", F.col("tip_amount"))
    .withColumn(
        "tip_amount",
        F.col("tip_amount").try_cast("decimal(10,2)"),
    )
    .withColumn(
        "discount_amount",
        F.col("discount_amount").try_cast("decimal(10,2)"),
    )
    .withColumn(
        "driver_payout_amount",
        F.col("driver_payout_amount").try_cast("decimal(10,2)"),
    )
)

print("Payment records where tip text was present but try_cast returned NULL:")
payment_cast.filter(
    F.col("tip_amount_src").isNotNull()
    & (F.trim(F.col("tip_amount_src")) != "")
    & F.col("tip_amount").isNull(),
).select(
    F.col("trip_id"),
    F.col("tip_amount_src"),
    F.col("tip_amount"),
).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Reject records without a usable key

# COMMAND ----------

payment_rejected = payment_cast.filter(F.col("trip_id").isNull())

print("Rejected payment records:")
payment_rejected.select(
    F.col("trip_id_src"),
    F.col("payment_method"),
    F.col("base_fare_amount_src"),
).show(truncate=False)

payment_key_filtered = payment_cast.filter(F.col("trip_id").isNotNull())

# COMMAND ----------

# MAGIC %md
# MAGIC ### Normalize payment labels

# COMMAND ----------

payment_labels_normalized = payment_key_filtered.withColumn(
    "payment_method",
    F.lower(F.trim(F.col("payment_method"))),
).withColumn(
    "payment_method",
    F.coalesce(
        F.when(
            F.col("payment_method") != "",
            F.col("payment_method"),
        ),
        F.lit("unknown"),
    ),
)

print("Controlled payment labels after normalization:")
payment_labels_normalized.filter(F.col("trip_id").between(101, 105)).select(
    F.col("trip_id"),
    F.col("payment_method"),
).orderBy(F.col("trip_id")).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Convert invalid numeric values to NULL
# MAGIC
# MAGIC `try_cast` has already converted malformed numeric text to NULL. The conditions
# MAGIC below keep zero and positive amounts and convert negative amounts to NULL.

# COMMAND ----------

payment_values_checked = (
    payment_labels_normalized.withColumn(
        "base_fare_amount",
        F.when(
            F.col("base_fare_amount") >= 0,
            F.col("base_fare_amount"),
        ).otherwise(F.lit(None).cast("decimal(10,2)")),
    )
    .withColumn(
        "surge_amount",
        F.when(
            F.col("surge_amount") >= 0,
            F.col("surge_amount"),
        ).otherwise(F.lit(None).cast("decimal(10,2)")),
    )
    .withColumn(
        "tax_amount",
        F.when(
            F.col("tax_amount") >= 0,
            F.col("tax_amount"),
        ).otherwise(F.lit(None).cast("decimal(10,2)")),
    )
    .withColumn(
        "tip_amount",
        F.when(
            F.col("tip_amount") >= 0,
            F.col("tip_amount"),
        ).otherwise(F.lit(None).cast("decimal(10,2)")),
    )
    .withColumn(
        "discount_amount",
        F.when(
            F.col("discount_amount") >= 0,
            F.col("discount_amount"),
        ).otherwise(F.lit(None).cast("decimal(10,2)")),
    )
    .withColumn(
        "driver_payout_amount",
        F.when(
            F.col("driver_payout_amount") >= 0,
            F.col("driver_payout_amount"),
        ).otherwise(F.lit(None).cast("decimal(10,2)")),
    )
)

print("Controlled payment amounts after cleaning:")
payment_values_checked.filter(F.col("trip_id").between(101, 105)).select(
    F.col("trip_id"),
    F.col("base_fare_amount_src"),
    F.col("base_fare_amount"),
    F.col("surge_amount_src"),
    F.col("surge_amount"),
    F.col("tip_amount_src"),
    F.col("tip_amount"),
).orderBy(F.col("trip_id")).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Validate controlled payment outcomes

# COMMAND ----------

payment_source_count = payment_source.count()
payment_rejected_count = payment_rejected.count()
payment_retained_count = payment_values_checked.count()

print(
    "Payment rows: "
    f"source={payment_source_count}, "
    f"rejected={payment_rejected_count}, "
    f"retained={payment_retained_count}"
)

assert payment_source_count == 106
assert payment_rejected_count == 1
assert payment_retained_count == 105

assert (
    payment_values_checked.filter(
        (F.col("trip_id") == 101) & (F.col("payment_method") == "card")
    ).count()
    == 1
)
assert (
    payment_values_checked.filter(
        (F.col("trip_id") == 105) & (F.col("payment_method") == "unknown")
    ).count()
    == 1
)
assert (
    payment_values_checked.filter(
        (F.col("trip_id") == 102) & F.col("surge_amount").isNull()
    ).count()
    == 1
)
assert (
    payment_values_checked.filter((F.col("trip_id") == 103) & F.col("tip_amount").isNull()).count()
    == 1
)
assert (
    payment_values_checked.filter(
        (F.col("trip_id") == 104) & F.col("base_fare_amount").isNull()
    ).count()
    == 1
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Add payment enrichments and select the curated contract
# MAGIC
# MAGIC `charge_before_tip` uses zero only as a calculation fallback for optional amounts;
# MAGIC it does not overwrite a source NULL. `tip_percent_of_base` remains NULL when its
# MAGIC denominator is missing or zero.

# COMMAND ----------

payment_clean = (
    payment_values_checked.withColumn(
        "charge_before_tip",
        F.round(
            F.col("base_fare_amount")
            + F.coalesce(F.col("surge_amount"), F.lit(0))
            + F.coalesce(F.col("tax_amount"), F.lit(0))
            - F.coalesce(F.col("discount_amount"), F.lit(0)),
            2,
        ),
    )
    .withColumn(
        "tip_percent_of_base",
        F.when(
            (F.col("base_fare_amount") > 0) & F.col("tip_amount").isNotNull(),
            F.round(
                F.col("tip_amount") / F.col("base_fare_amount") * 100,
                1,
            ),
        ).otherwise(F.lit(None)),
    )
    .select(
        F.col("trip_id"),
        F.col("payment_method"),
        F.col("base_fare_amount"),
        F.col("surge_amount"),
        F.col("tax_amount"),
        F.col("tip_amount"),
        F.col("discount_amount"),
        F.col("driver_payout_amount"),
        F.col("charge_before_tip"),
        F.col("tip_percent_of_base"),
    )
)

payment_clean_count = payment_clean.count()
assert payment_clean_count == 105

payment_clean.orderBy(F.col("trip_id")).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Write and verify curated outputs
# MAGIC
# MAGIC `.mode("overwrite")` makes this course workflow idempotent: rerunning the notebook
# MAGIC replaces the previous output instead of appending duplicate records. The same
# MAGIC `trip_clean` and `payment_clean` DataFrames validated above are written here.

# COMMAND ----------

trip_clean.write.mode("overwrite").parquet(curated_trip_path)
payment_clean.write.mode("overwrite").parquet(curated_payment_path)

print(f"Wrote curated trip data to {curated_trip_path}")
print(f"Wrote curated payment data to {curated_payment_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC Read both folders back to check the actual files that downstream notebooks will
# MAGIC consume.

# COMMAND ----------

trip_curated = spark.read.parquet(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    curated_trip_path
)
payment_curated = spark.read.parquet(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    curated_payment_path
)

trip_curated_count = trip_curated.count()
payment_curated_count = payment_curated.count()

print(f"Curated trip readback: {trip_curated_count} records")
print(f"Curated payment readback: {payment_curated_count} records")

assert trip_curated_count == trip_clean_count == 106
assert payment_curated_count == payment_clean_count == 105

trip_curated.printSchema()
payment_curated.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Exercise
# MAGIC
# MAGIC New payment records arrive with the same categories of problems demonstrated
# MAGIC above, but different values. Build `payment_exercise` from
# MAGIC `payment_exercise_source`:
# MAGIC
# MAGIC 1. Safely cast `trip_id` and `base_fare_amount` with `try_cast` to their
# MAGIC    canonical types.
# MAGIC 2. Reject the record whose `trip_id` becomes NULL after casting.
# MAGIC 3. Trim and lowercase `payment_method`; replace a blank or NULL method with
# MAGIC    `unknown`.
# MAGIC 4. Convert a negative `base_fare_amount` to NULL.
# MAGIC 5. Select `trip_id`, `payment_method`, and `base_fare_amount`, then order by
# MAGIC    `trip_id` and show the result.
# MAGIC
# MAGIC Keep this as one forward-moving chain and do not write it. Your result should
# MAGIC have four records. Trip `202` should show `payment_method = "unknown"`
# MAGIC (blank source value). Trip `203` should show `base_fare_amount = NULL`
# MAGIC (negative source value).

# COMMAND ----------

payment_exercise_source = spark.createDataFrame(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    [
        ("201", " Card ", "45.00", "5.00", "3.50", "6.00", "0.00", "38.00"),
        ("202", "", "30.00", "0.00", "2.40", "3.00", "0.00", "25.00"),
        ("203", "Cash", "-12.00", "0.00", "0.96", "1.50", "0.00", "10.00"),
        ("204", "wallet", "27.50", "2.00", "2.20", "3.00", "0.00", "22.00"),
        (None, "Card", "18.00", "0.00", "1.44", "2.00", "0.00", "15.00"),
    ],
    payment_string_schema_ddl,
)

print("New payment records for the exercise:")
payment_exercise_source.show(truncate=False)

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - Read each full-size controlled-bad CSV with a string schema so `try_cast` could
# MAGIC   expose malformed values safely under ANSI mode.
# MAGIC - Used one staged chain per dataset to cast fields, diagnose failed conversions,
# MAGIC   reject missing keys, normalize labels, and convert invalid numeric values to
# MAGIC   NULL.
# MAGIC - Added the existing Module 6 enrichments to those same cleaned DataFrames.
# MAGIC - Wrote `trip_clean` and `payment_clean` to `curated/trip/` and
# MAGIC   `curated/payment/`, then verified 106 trip records and 105 payment records.
# MAGIC
# MAGIC **Next:** Module 6 **`04 - Built-ins First: When (Not) to Use UDFs`** compares
# MAGIC built-in expressions with Python and Pandas UDF alternatives.
