# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # 03 - Cleaning and Curated Outputs
# MAGIC
# MAGIC Reliable curated datasets need explicit rules for rejecting invalid rows, repairing
# MAGIC recoverable values, and preserving the keys used by downstream pipelines. This
# MAGIC notebook first makes those decisions visible on two small bad-data files, then
# MAGIC applies the same guards to the canonical landing data.
# MAGIC
# MAGIC You will:
# MAGIC
# MAGIC 1. Review NULL-safe predicates, normalization, and safe casts on landed bad data
# MAGIC 2. Build one forward-moving transformation chain for each bad-data file
# MAGIC 3. Apply production-style guards to canonical `trip` and `payment` data
# MAGIC 4. Persist cleaning and enrichment columns in curated outputs
# MAGIC 5. Write and verify curated `trip` and `payment` datasets
# MAGIC
# MAGIC **Prerequisites.** Complete Module 6 **`01 - Column Transforms with Built-in
# MAGIC Functions`** and **`02 - Complex Types: Structs, Arrays, and explode`**. Run Module
# MAGIC 5 **`01 - Unity Catalog Volumes and Data Landing`** so the canonical files and both
# MAGIC supplementary bad-data CSV files exist in the landing Volume.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup
# MAGIC
# MAGIC The supplementary CSV files deliberately store every field as text. Reading them
# MAGIC with string schemas lets `try_cast` expose malformed values without stopping the
# MAGIC notebook under ANSI mode.
# MAGIC
# MAGIC The canonical contracts are:
# MAGIC
# MAGIC - `trip`: `trip_id` plus service type, location keys, distance, and duration fields
# MAGIC - `payment`: `trip_id` plus payment method and decimal fare-breakdown fields
# MAGIC
# MAGIC Only canonical data is written to the full curated Volume paths. The bad-data
# MAGIC samples are inspected in memory and are never written.

# COMMAND ----------

from pyspark.sql import functions as F

landing_root = "/Volumes/rideshare_dev/landing/source_files"
curated_root = "/Volumes/rideshare_dev/processed/output_files/curated"

trip_csv_path = f"{landing_root}/trip/trip.csv"
bad_trip_csv_path = f"{landing_root}/trip/bad_trip_data.csv"
payment_avro_path = f"{landing_root}/payment/payment.avro"
bad_payment_csv_path = f"{landing_root}/payment/bad_payment_data.csv"

curated_trip_path = f"{curated_root}/trip"
curated_payment_path = f"{curated_root}/payment"

print(f"bad_trip_csv_path = {bad_trip_csv_path}")
print(f"bad_payment_csv_path = {bad_payment_csv_path}")
print(f"curated_trip_path = {curated_trip_path}")
print(f"curated_payment_path = {curated_payment_path}")

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

bad_trip_schema_ddl = """
trip_id string,
service_type string,
pickup_location_id string,
dropoff_location_id string,
trip_distance_miles string,
request_to_pickup_mins string,
ride_duration_mins string,
driver_arrival_to_pickup_mins string
"""

bad_payment_schema_ddl = """
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
# MAGIC ## 1. Clean the landed bad trip sample
# MAGIC
# MAGIC The trip sample contains mixed text casing, surrounding spaces, a sentinel
# MAGIC (`n/a`), a missing key, a negative distance, malformed numeric text, and blanks.
# MAGIC
# MAGIC The cleaning policy is:
# MAGIC
# MAGIC - reject rows whose `trip_id` cannot become a non-NULL `bigint`
# MAGIC - trim and lowercase `service_type`; map blanks and `n/a` to `unknown`
# MAGIC - use `try_cast` for every typed field; keep raw text beside cast results when you
# MAGIC   need to detect rejected conversions with
# MAGIC   **`raw.isNotNull() & casted.isNull()`**
# MAGIC - turn non-positive distances into `NULL` so an invalid measurement is not treated
# MAGIC   as a real distance (distinct from a cast rejection)
# MAGIC
# MAGIC Each stage below derives from the previous DataFrame in one forward-moving pipeline
# MAGIC so you can inspect normalization, casting, range repair, and key rejection.

# COMMAND ----------

bad_trip_raw = (
    spark.read.format(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
        "csv"
    )
    .option("header", "true")
    .schema(bad_trip_schema_ddl)
    .load(bad_trip_csv_path)
)

print("Bad trip source:")
bad_trip_raw.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Normalize text labels

# COMMAND ----------

bad_trip_normalized = bad_trip_raw.withColumn(
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

print("After service_type normalization:")
bad_trip_normalized.select("trip_id", "service_type").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Cast typed fields and detect rejected conversions
# MAGIC
# MAGIC Keep **`trip_distance_miles_src`** so a failed `try_cast` is not confused with a
# MAGIC blank source value.

# COMMAND ----------

bad_trip_cast = (
    bad_trip_normalized.withColumn("trip_id", F.col("trip_id").try_cast("bigint"))
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

print("Rows where distance text was present but try_cast returned NULL:")
bad_trip_cast.filter(
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
# MAGIC ### Repair invalid measurements and reject missing keys
# MAGIC
# MAGIC Non-positive distances become `NULL` after a successful cast. That is range repair,
# MAGIC not a cast rejection.

# COMMAND ----------

bad_trip_repaired = bad_trip_cast.withColumn(
    "trip_distance_miles",
    F.when(
        F.col("trip_distance_miles") > 0,
        F.col("trip_distance_miles"),
    ).otherwise(F.lit(None).cast("decimal(8,2)")),
)

print("After non-positive distance repair (trip_id 3):")
bad_trip_repaired.filter(F.col("trip_id") == 3).select(
    F.col("trip_id"),
    F.col("trip_distance_miles_src"),
    F.col("trip_distance_miles"),
).show(truncate=False)

bad_trip_clean = bad_trip_repaired.filter(F.col("trip_id").isNotNull()).select(
    F.col("trip_id"),
    F.col("service_type"),
    F.col("pickup_location_id"),
    F.col("dropoff_location_id"),
    F.col("trip_distance_miles"),
    F.col("request_to_pickup_mins"),
    F.col("ride_duration_mins"),
    F.col("driver_arrival_to_pickup_mins"),
)

bad_trip_source_count = bad_trip_raw.count()
bad_trip_clean_count = bad_trip_clean.count()

print(f"Bad trip rows: {bad_trip_source_count} -> {bad_trip_clean_count}")
assert bad_trip_source_count == 7
assert bad_trip_clean_count == 6

bad_trip_clean.orderBy(F.col("trip_id")).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC Rejected **`trip_id`** values (missing key) — compare to cast rejections above.

# COMMAND ----------

bad_trip_cast.filter(F.col("trip_id").isNull()).select(
    F.col("trip_id"),
    F.col("service_type"),
    F.col("pickup_location_id"),
).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Clean the landed bad payment sample
# MAGIC
# MAGIC The payment sample adds another important distinction: a required row key can
# MAGIC justify rejection, while an invalid optional amount can often remain as `NULL` for
# MAGIC later review.
# MAGIC
# MAGIC This chain:
# MAGIC
# MAGIC - rejects only a missing or malformed `trip_id`
# MAGIC - trims and lowercases `payment_method`; fills a blank with `unknown`
# MAGIC - safely casts every amount to `decimal(10,2)`
# MAGIC - converts negative amounts to `NULL` instead of inventing a replacement amount
# MAGIC
# MAGIC Work through normalization, casting (with rejected-conversion detection), range
# MAGIC repair, and key rejection in separate cells within one forward-moving pipeline.

# COMMAND ----------

bad_payment_raw = (
    spark.read.format(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
        "csv"
    )
    .option("header", "true")
    .schema(bad_payment_schema_ddl)
    .load(bad_payment_csv_path)
)

print("Bad payment source:")
bad_payment_raw.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Normalize payment method

# COMMAND ----------

bad_payment_normalized = bad_payment_raw.withColumn(
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

print("After payment_method normalization:")
bad_payment_normalized.select("trip_id", "payment_method").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Cast amounts and detect rejected conversions
# MAGIC
# MAGIC No rows are expected from the base-fare rejection filter below: every non-empty
# MAGIC base-fare value in this file is valid numeric text. Range problems (negative
# MAGIC amounts) appear in the repair step, not as cast rejections.

# COMMAND ----------

bad_payment_cast = (
    bad_payment_normalized.withColumn("trip_id", F.col("trip_id").try_cast("bigint"))
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

print("Rows where base fare text was present but try_cast returned NULL:")
bad_payment_cast.filter(
    F.col("base_fare_amount_src").isNotNull()
    & (F.trim(F.col("base_fare_amount_src")) != "")
    & F.col("base_fare_amount").isNull(),
).select(
    F.col("trip_id"),
    F.col("base_fare_amount_src"),
    F.col("base_fare_amount"),
).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Repair invalid amounts and reject missing keys
# MAGIC
# MAGIC Negative amounts become `NULL` after a successful cast. Trip `102` keeps its row
# MAGIC but loses the invalid surge value. Trip `104` keeps its row but loses a negative
# MAGIC base fare for the same reason — that is range repair, not a cast rejection.

# COMMAND ----------

bad_payment_repaired = (
    bad_payment_cast.withColumn(
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

print("After negative surge repair (trip_id 102):")
bad_payment_repaired.filter(F.col("trip_id") == 102).select(
    F.col("trip_id"),
    F.col("surge_amount_src"),
    F.col("surge_amount"),
).show(truncate=False)

bad_payment_clean = bad_payment_repaired.filter(F.col("trip_id").isNotNull()).select(
    F.col("trip_id"),
    F.col("payment_method"),
    F.col("base_fare_amount"),
    F.col("surge_amount"),
    F.col("tax_amount"),
    F.col("tip_amount"),
    F.col("discount_amount"),
    F.col("driver_payout_amount"),
)

bad_payment_source_count = bad_payment_raw.count()
bad_payment_clean_count = bad_payment_clean.count()

print(f"Bad payment rows: {bad_payment_source_count} -> {bad_payment_clean_count}")
assert bad_payment_source_count == 6
assert bad_payment_clean_count == 5

bad_payment_clean.orderBy(F.col("trip_id")).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC Rejected **`trip_id`** values (missing key):

# COMMAND ----------

bad_payment_cast.filter(F.col("trip_id").isNull()).select(
    F.col("trip_id"),
    F.col("payment_method"),
    F.col("base_fare_amount_src"),
).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Apply production-style guards to canonical landing data
# MAGIC
# MAGIC The small samples proved the rules. Production code now re-reads the canonical
# MAGIC landing files rather than carrying sample data forward.
# MAGIC
# MAGIC The curated contract keeps the same row grain as each canonical source. Apply the
# MAGIC **relevant sample guards** plus **canonical domain checks** on the full landing
# MAGIC files: reject rows without `trip_id`, normalize labels, repair invalid
# MAGIC measurements, and for trip only require non-negative duration and wait columns
# MAGIC (zero minutes is valid). The current canonical files contain 100 valid keys each,
# MAGIC so both cleaned outputs should preserve all 100 rows.

# COMMAND ----------

trip = (
    spark.read.format(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
        "csv"
    )
    .option("header", "true")
    .schema(trip_schema_ddl)
    .load(trip_csv_path)
)

payment = (
    spark.read.format(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
        "avro"
    )
    .schema(payment_schema_ddl)
    .load(payment_avro_path)
)

print("Canonical trip schema:")
trip.printSchema()
print("Canonical payment schema:")
payment.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Clean and enrich canonical trip data
# MAGIC
# MAGIC This chain applies the bad-trip sample guards (key, labels, distance) plus canonical
# MAGIC domain checks on `request_to_pickup_mins`, `ride_duration_mins`, and
# MAGIC `driver_arrival_to_pickup_mins`: keep values when they are **greater than or equal
# MAGIC to zero** so zero-minute waits and rides remain valid. It preserves `trip_id` and
# MAGIC both location join keys, and persists the string, numeric, and conditional
# MAGIC enrichments demonstrated in Module 6
# MAGIC **`01 - Column Transforms with Built-in Functions`**.
# MAGIC
# MAGIC Notice the explicit NULL branch in `ride_duration_band`. Without it, a NULL
# MAGIC duration would reach `.otherwise("long")` and be mislabeled as a long ride.

# COMMAND ----------

trip_clean = (
    trip.filter(F.col("trip_id").isNotNull())
    .withColumn(
        "service_type",
        F.lower(F.trim(F.col("service_type"))),
    )
    .withColumn(
        "service_type",
        F.coalesce(
            F.when(
                ~F.col("service_type").isin("", "n/a"),
                F.col("service_type"),
            ),
            F.lit("unknown"),
        ),
    )
    .withColumn(
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
    .withColumn(
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

trip_source_count = trip.count()
trip_clean_count = trip_clean.count()

print(f"Canonical trip rows: {trip_source_count} -> {trip_clean_count}")
assert trip_source_count == 100
assert trip_clean_count == 100

trip_clean.show(10, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Clean and enrich canonical payment data
# MAGIC
# MAGIC Payment uses the same normalize-and-guard sequence as the sample. The derived
# MAGIC `charge_before_tip` uses zero only as a calculation fallback for optional amounts;
# MAGIC it does not overwrite a source NULL. `tip_percent_of_base` remains NULL when its
# MAGIC denominator is missing or zero.

# COMMAND ----------

payment_clean = (
    payment.filter(F.col("trip_id").isNotNull())
    .withColumn(
        "payment_method",
        F.lower(F.trim(F.col("payment_method"))),
    )
    .withColumn(
        "payment_method",
        F.coalesce(
            F.when(
                F.col("payment_method") != "",
                F.col("payment_method"),
            ),
            F.lit("unknown"),
        ),
    )
    .withColumn(
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
    .withColumn(
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

payment_source_count = payment.count()
payment_clean_count = payment_clean.count()

print(f"Canonical payment rows: {payment_source_count} -> {payment_clean_count}")
assert payment_source_count == 100
assert payment_clean_count == 100

payment_clean.show(10, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Write and verify curated outputs
# MAGIC
# MAGIC `.mode("overwrite")` makes the result idempotent for this course workflow: rerunning
# MAGIC the notebook replaces its previous output instead of appending duplicate rows.
# MAGIC
# MAGIC Only `trip_clean` and `payment_clean`, both derived from canonical sources, are
# MAGIC written. The supplementary samples never enter either write path.

# COMMAND ----------

trip_clean.write.mode("overwrite").parquet(curated_trip_path)
payment_clean.write.mode("overwrite").parquet(curated_payment_path)

print(f"Wrote curated trip data to {curated_trip_path}")
print(f"Wrote curated payment data to {curated_payment_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC Read both folders back instead of validating only the in-memory DataFrames. This
# MAGIC checks the actual files that downstream notebooks will consume.

# COMMAND ----------

trip_curated = spark.read.parquet(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    curated_trip_path
)
payment_curated = spark.read.parquet(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    curated_payment_path
)

trip_curated_count = trip_curated.count()
payment_curated_count = payment_curated.count()

print(f"Curated trip readback: {trip_curated_count} rows")
print(f"Curated payment readback: {payment_curated_count} rows")

assert trip_curated_count == 100
assert payment_curated_count == 100

trip_curated.printSchema()
payment_curated.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Build `payment_exercise` from the already loaded `bad_payment_raw` DataFrame:
# MAGIC
# MAGIC 1. Safely cast `trip_id`, `base_fare_amount`, and `surge_amount` to their canonical
# MAGIC    types.
# MAGIC 2. Normalize `payment_method` with `trim` and `lower`; replace a blank or NULL
# MAGIC    method with `unknown`.
# MAGIC 3. Convert a negative `surge_amount` to NULL.
# MAGIC 4. Reject rows where `trip_id` is NULL after casting.
# MAGIC 5. Reject rows where `base_fare_amount` is NULL or not greater than zero.
# MAGIC 6. Select `trip_id`, `payment_method`, `base_fare_amount`, and `surge_amount`, then
# MAGIC    order by `trip_id` and show the result.
# MAGIC
# MAGIC Keep this as one forward-moving chain and do not write it. Your result should have
# MAGIC four rows. Trip `102` should remain with `surge_amount = NULL`.

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - Read supplementary CSV fields as strings so `try_cast` could expose malformed
# MAGIC   values safely under ANSI mode.
# MAGIC - Used staged forward-moving chains to normalize text, cast types, surface rejected
# MAGIC   conversions with **`raw.isNotNull() & casted.isNull()`**, repair invalid ranges,
# MAGIC   and reject rows without required keys.
# MAGIC - Applied the demonstrated guards to canonical `trip` and `payment` landing data.
# MAGIC - Persisted the string, numeric, and conditional enrichments from Module 6
# MAGIC   **`01 - Column Transforms with Built-in Functions`** only after cleaning.
# MAGIC - Wrote canonical data—not bad-data samples—to `curated/trip/` and
# MAGIC   `curated/payment/`, then verified exactly 100 rows in each readback.
# MAGIC
# MAGIC **Next:** Module 6 **`04 - Built-ins First: When (Not) to Use UDFs`** compares
# MAGIC built-in expressions with Python and Pandas UDF alternatives.
