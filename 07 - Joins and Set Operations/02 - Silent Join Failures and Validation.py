# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC # 02 - Silent Join Failures and Validation
# MAGIC
# MAGIC Joins can succeed and still be wrong. No error, no warning — just silently
# MAGIC corrupted row counts and broken aggregations downstream.
# MAGIC
# MAGIC This notebook covers three silent failures and the habits that prevent them:
# MAGIC
# MAGIC * **M:M duplicate keys** — rows multiply (2×2 = 4 per key)
# MAGIC * **NULL keys** — rows vanish from inner joins
# MAGIC * **Accidental Cartesian** — every row × every row
# MAGIC
# MAGIC Between those: how to detect duplicates before joining (key profiling) and
# MAGIC how to resolve them deterministically (groupBy, not dropDuplicates).
# MAGIC
# MAGIC **Reads:** landing `trip`, `trip_time`, `payment` (100 rows each) +
# MAGIC constructed mini-frames. **No write.**
# MAGIC
# MAGIC **Prerequisites.** Module 7 **`01 - Grain, Join Syntax, and Unmatched Keys`**
# MAGIC and Module 6 (**`01`** through **`04`**). Landing Volume must contain **`trip`**,
# MAGIC **`trip_time`**, and **`payment`** (100 rows each). Recall Module 3
# MAGIC **`eqNullSafe`** when NULL keys must match.

# COMMAND ----------

# DBTITLE 1,Setup
# MAGIC %md
# MAGIC ## Setup — load and verify the clean 1:1 baseline
# MAGIC
# MAGIC | Table | Format | Grain | Key | Rows |
# MAGIC |---|---|---|---|---|
# MAGIC | `trip` | CSV | one completed trip | `trip_id` | 100 |
# MAGIC | `trip_time` | Parquet | one time record per trip | `trip_id` | 100 |
# MAGIC | `payment` | Avro | one fare record per trip | `trip_id` | 100 |
# MAGIC
# MAGIC All three are 1:1 on `trip_id`. `payment` is new (not used in Notebook 01);
# MAGIC it adds fare columns per trip.
# MAGIC
# MAGIC After loading, the second code cell runs all four join types on both pairs.
# MAGIC All should return 100 — that's the clean baseline.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import LongType, StructField, StructType

landing_root = "/Volumes/rideshare_dev/landing/source_files"
trip_csv_path = f"{landing_root}/trip/trip.csv"
trip_time_parquet_path = f"{landing_root}/trip_time/trip_time.parquet"
payment_avro_path = f"{landing_root}/payment/payment.avro"

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

trip_time_schema_ddl = """
trip_id bigint,
trip_date date,
hour_of_day int
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

trip = (
    spark.read.format("csv")  # noqa: F821
    .option("header", True)
    .schema(trip_schema_ddl)
    .load(trip_csv_path)
)

trip_time = (
    spark.read.format("parquet")  # noqa: F821
    .schema(trip_time_schema_ddl)
    .load(trip_time_parquet_path)
)

payment = (
    spark.read.format("avro")  # noqa: F821
    .schema(payment_schema_ddl)
    .load(payment_avro_path)
)

print("trip rows:", trip.count())
print("trip_time rows:", trip_time.count())
print("payment rows:", payment.count())

# COMMAND ----------

# trip ↔ trip_time — all four types should return 100
print("trip ↔ trip_time:")
print("  inner:", trip.join(trip_time, "trip_id", "inner").count())
print("  left: ", trip.join(trip_time, "trip_id", "left").count())
print("  right:", trip.join(trip_time, "trip_id", "right").count())
print("  full: ", trip.join(trip_time, "trip_id", "full").count())

print()

# trip ↔ payment — same expectation
print("trip ↔ payment:")
print("  inner:", trip.join(payment, "trip_id", "inner").count())
print("  left: ", trip.join(payment, "trip_id", "left").count())
print("  right:", trip.join(payment, "trip_id", "right").count())
print("  full: ", trip.join(payment, "trip_id", "full").count())

print("\n→ All same. No duplicates, no unmatched keys, no NULLs.")
print("  The rest of this notebook shows what happens when that breaks.")

# COMMAND ----------

# DBTITLE 1,1. M:M fanout
# MAGIC %md
# MAGIC ## 1. M:M — when both sides have duplicates
# MAGIC
# MAGIC Notebook 01 Section 3.2 showed what happens when you join on too few columns
# MAGIC — one side had extra rows per key. M:M is worse: BOTH sides have duplicates.
# MAGIC
# MAGIC When you hit this: ETL ran twice, source sent retries, or two fact tables
# MAGIC joined without aggregating first.
# MAGIC
# MAGIC ```
# MAGIC Left trip_id:  [1, 1, 2]   — key 1 appears 2×
# MAGIC Right trip_id: [1, 1, 3]   — key 1 appears 2×
# MAGIC
# MAGIC Key 1: 2 left × 2 right = 4 output rows
# MAGIC Key 2: 1 left × 0 right = 0 (no match)
# MAGIC Key 3: 0 left × 1 right = 0 (no match)
# MAGIC Inner total: 4
# MAGIC ```
# MAGIC
# MAGIC The formula: for each key, count(left) × count(right).

# COMMAND ----------

left_mm = spark.createDataFrame([(1,), (1,), (2,)], ["trip_id"])  # noqa: F821
right_mm = spark.createDataFrame([(1,), (1,), (3,)], ["trip_id"])

predicted_mm = 4
actual_mm = left_mm.join(right_mm, "trip_id", "inner").count()
print(f"Inner M:M: predicted={predicted_mm}, actual={actual_mm}")
print("Each row below came from key 1 matching 2×2:")
left_mm.join(right_mm, "trip_id", "inner").show()

# COMMAND ----------

# DBTITLE 1,2. Key profiling
# MAGIC %md
# MAGIC ## 2. Key profiling — detect duplicates before joining
# MAGIC
# MAGIC Before any join, profile the key on both sides:
# MAGIC
# MAGIC 1. **Row count** — total rows in the table
# MAGIC 2. **Distinct non-NULL keys** — `countDistinct(key)` (this ignores NULLs)
# MAGIC 3. **NULL key count** — rows where the key is NULL
# MAGIC
# MAGIC If rows == distinct and nulls == 0 → the key is unique and complete.
# MAGIC If not:
# MAGIC * rows ≠ distinct, but data is correct → the table's grain is finer than
# MAGIC   your key → find the composite key (Notebook 01 Section 3.2: `[trip_id,
# MAGIC   charge_type]` instead of just `trip_id`)
# MAGIC * rows ≠ distinct, data has true duplicates → resolve before joining
# MAGIC   (Section 3 below)
# MAGIC * nulls > 0 → inner joins will silently drop those rows (Section 4)

# COMMAND ----------

# Profile trip
trip_stats = trip.select(
    F.count(F.lit(1)).alias("rows"),
    F.countDistinct("trip_id").alias("distinct"),
    F.sum(F.when(F.col("trip_id").isNull(), 1).otherwise(0)).alias("nulls"),
).collect()[0]
print(f"trip       rows={trip_stats['rows']}, distinct={trip_stats['distinct']}, nulls={trip_stats['nulls']}")

# Profile trip_time
tt_stats = trip_time.select(
    F.count(F.lit(1)).alias("rows"),
    F.countDistinct("trip_id").alias("distinct"),
    F.sum(F.when(F.col("trip_id").isNull(), 1).otherwise(0)).alias("nulls"),
).collect()[0]
print(f"trip_time  rows={tt_stats['rows']}, distinct={tt_stats['distinct']}, nulls={tt_stats['nulls']}")

# Profile payment
pay_stats = payment.select(
    F.count(F.lit(1)).alias("rows"),
    F.countDistinct("trip_id").alias("distinct"),
    F.sum(F.when(F.col("trip_id").isNull(), 1).otherwise(0)).alias("nulls"),
).collect()[0]
print(f"payment    rows={pay_stats['rows']}, distinct={pay_stats['distinct']}, nulls={pay_stats['nulls']}")

# COMMAND ----------

# DBTITLE 1,3. Duplicate resolution
# MAGIC %md
# MAGIC ## 3. Duplicate resolution — don't let Spark decide
# MAGIC
# MAGIC You profiled and found duplicates. Two approaches:
# MAGIC
# MAGIC | Method | Behavior |
# MAGIC |---|---|
# MAGIC | `dropDuplicates(["trip_id"])` | Keeps one row per key — survivor is non-deterministic (different plans may keep different rows) |
# MAGIC | `groupBy("trip_id").agg(...)` | Keeps one row using YOUR rule — deterministic, same input always gives same output |
# MAGIC
# MAGIC `dropDuplicates` is fine when all rows for a key are truly identical. When
# MAGIC they differ (different timestamps, amounts, statuses), use `groupBy` with an
# MAGIC explicit rule.
# MAGIC
# MAGIC Most common real-world pattern: same trip appears twice because ETL ran twice
# MAGIC or the source sent a retry. The rows are identical except for an `updated_at`
# MAGIC timestamp. Resolution: keep the row with the latest timestamp.

# COMMAND ----------

# ETL ran twice — same trip, different updated_at timestamps
dup_trips = spark.createDataFrame(  # noqa: F821
    [
        (1, "Premium", 25.00, "2024-01-15 10:00:00"),
        (1, "Premium", 25.00, "2024-01-15 14:30:00"),  # later retry
        (2, "Standard", 12.50, "2024-01-15 09:00:00"),
    ],
    ["trip_id", "service_type", "fare", "updated_at"],
)

print("Before — trip_id=1 appears twice (ETL retry):")
dup_trips.show(truncate=False)

print("dropDuplicates — which row survived? Non-deterministic:")
dup_trips.dropDuplicates(["trip_id"]).orderBy("trip_id").show(truncate=False)

print("groupBy + max(updated_at) — always keeps the latest:")
resolved = dup_trips.groupBy("trip_id").agg(
    F.first("service_type").alias("service_type"),
    F.first("fare").alias("fare"),
    F.max("updated_at").alias("updated_at"),
)
resolved.orderBy("trip_id").show(truncate=False)

# Verify grain after resolution
stats = resolved.select(
    F.count(F.lit(1)).alias("rows"),
    F.countDistinct("trip_id").alias("distinct"),
).collect()[0]
print(f"Resolved: rows={stats['rows']}, distinct={stats['distinct']} → grain is clean")

# COMMAND ----------

# DBTITLE 1,4. NULL keys
# MAGIC %md
# MAGIC ## 4. NULL keys — silent data loss
# MAGIC
# MAGIC In SQL and Spark, `NULL = NULL` evaluates to `NULL` (not TRUE). Standard
# MAGIC equality never matches NULL to NULL.
# MAGIC
# MAGIC **Scenario:** A batch of trip records arrived with a corrupt `trip_id` (NULL)
# MAGIC — the system failed to assign an ID. Separately, a payment record came in
# MAGIC that couldn't be linked to any trip (also NULL `trip_id`).
# MAGIC
# MAGIC You try to join trips with payments on `trip_id`:
# MAGIC
# MAGIC ```
# MAGIC trips   trip_id: [1, 2, NULL]   ← trip 3 has corrupt/missing ID
# MAGIC payments trip_id: [2, 3, NULL]   ← payment with no linked trip
# MAGIC ```
# MAGIC
# MAGIC The NULL trip and the NULL payment look like they should match — but they
# MAGIC don't. `NULL = NULL` is not TRUE in Spark. Both rows silently disappear
# MAGIC from an inner join.
# MAGIC
# MAGIC Predict each join type, replace `None` below, then run:
# MAGIC * **inner:** which trip_ids can actually match? (hint: NULL can't)
# MAGIC * **left:** all left rows stay — how many?
# MAGIC * **right:** all right rows stay — how many?
# MAGIC * **full:** everything from both sides — how many unique entities?

# COMMAND ----------

# Trips — one record has corrupt/missing trip_id (NULL)
trips_with_null = spark.createDataFrame(  # noqa: F821
    [(1, "Premium"), (2, "Standard"), (None, "XL")],
    ["trip_id", "service_type"],
)

# Payments — one payment couldn't be linked to a trip (NULL)
payments_with_null = spark.createDataFrame(
    [(2, 15.00), (3, 22.50), (None, 8.00)],
    ["trip_id", "fare"],
)

print("Trips:")
trips_with_null.show()
print("Payments:")
payments_with_null.show()

# YOUR PREDICTIONS — replace None with expected row count
predictions = {
    "inner": None,
    "left": None,
    "right": None,
    "full": None,
}

for join_type, predicted in predictions.items():
    actual = trips_with_null.join(payments_with_null, "trip_id", join_type).count()
    mark = "✓" if predicted == actual else "✗"
    print(f"{mark} {join_type:6} → predicted={predicted}, actual={actual}")

# COMMAND ----------

# DBTITLE 1,4b. eqNullSafe
# MAGIC %md
# MAGIC ### When you WANT NULL to match NULL
# MAGIC
# MAGIC Sometimes NULL represents a known category ("unassigned trips") and you need
# MAGIC them to group together. Use `.eqNullSafe()` in a Boolean join condition —
# MAGIC it treats NULL = NULL as TRUE.
# MAGIC
# MAGIC This requires Boolean form (Notebook 01 Section 3.3) and produces both key
# MAGIC columns in the output.
# MAGIC
# MAGIC **Warning:** `eqNullSafe` can itself fan out when both sides contain multiple
# MAGIC NULL-key rows. Two NULLs left × three NULLs right = six rows. Profile NULL
# MAGIC counts on both sides before using this.
# MAGIC
# MAGIC Predict: inner with eqNullSafe on the data above → key 2 matches + NULL
# MAGIC matches = **2 rows**.

# COMMAND ----------

# Standard inner join — NULL rows lost
standard = trips_with_null.join(payments_with_null, "trip_id", "inner")
print(f"Standard inner: {standard.count()} row (NULL didn't match)")
standard.show()

# eqNullSafe inner join — NULL rows matched
trips_a = trips_with_null.alias("t")
payments_a = payments_with_null.alias("p")

eq_safe = trips_a.join(
    payments_a,
    F.col("t.trip_id").eqNullSafe(F.col("p.trip_id")),
    "inner",
)
print(f"eqNullSafe inner: {eq_safe.count()} rows (NULL matched NULL)")
eq_safe.show()

# COMMAND ----------

# DBTITLE 1,5. Cartesian products
# MAGIC %md
# MAGIC ## 5. Cartesian products — intentional versus accidental
# MAGIC
# MAGIC A Cartesian product is every row on the left paired with every row on the
# MAGIC right. Think of it as M:M taken to the extreme — every key "matches" every
# MAGIC key.
# MAGIC
# MAGIC **Why it happens:** the join condition evaluates to TRUE for every
# MAGIC combination. No filtering, no key comparison — just "pair everything."
# MAGIC
# MAGIC **Intentional use case:** You're building a pricing grid. You have 3 service
# MAGIC types and 3 zones. You need a row for every combination so you can assign
# MAGIC a base rate to each. That's `crossJoin` — explicit, readable, intentional.
# MAGIC After the crossJoin, you add a rate column based on service type.
# MAGIC
# MAGIC **Accidental anti-pattern:** You write a Boolean join condition but use
# MAGIC `F.lit(True)` instead of an actual column comparison. The condition is always
# MAGIC true, so every left row matches every right row. Same 9 rows, but it's a bug.
# MAGIC
# MAGIC The danger isn't on small data (3 × 3 = 9). It's on production:
# MAGIC 100K trips × 100K payments = **10 billion rows**. No error message — your
# MAGIC cluster just runs out of memory or hangs for hours.
# MAGIC
# MAGIC **How to spot it:** if your join output is dramatically larger than either
# MAGIC input and you didn't expect it, check the join condition. An always-true
# MAGIC condition or a missing key is usually the cause.

# COMMAND ----------

# Intentional: generate a pricing grid (all service × zone combinations)
service_types = spark.createDataFrame(  # noqa: F821
    [("Premium",), ("Standard",), ("XL",)], ["service_type"]
)
zones = spark.createDataFrame(
    [("Manhattan",), ("Brooklyn",), ("Queens",)], ["zone"]
)

pricing_grid = service_types.crossJoin(zones).withColumn(
    "base_rate",
    F.when(F.col("service_type") == "Premium", 25.00)
    .when(F.col("service_type") == "XL", 20.00)
    .otherwise(12.00),
)
print(f"Intentional crossJoin: 3 service types × 3 zones = {pricing_grid.count()} rows")
print("Every combination gets a base rate:")
pricing_grid.show()

# Accidental: forgot the join key, used always-true condition
print("Accidental — F.lit(True) instead of 'trip_id':")
accidental = service_types.join(zones, F.lit(True), "inner")
print(f"Same result: {accidental.count()} rows")
print("→ On production (100K × 100K) this would be 10 billion rows.")

# COMMAND ----------

# DBTITLE 1,6. Exercise
# MAGIC %md
# MAGIC ## 6. Exercise — full pre-join and post-join validation
# MAGIC
# MAGIC **Scenario:** A `driver_payouts` table arrived from the finance system. It
# MAGIC should have one payout per trip, but the extract has issues you need to
# MAGIC detect.
# MAGIC
# MAGIC Your task:
# MAGIC 1. Profile `driver_payouts` on `trip_id` (rows, distinct, nulls)
# MAGIC 2. Look at the profile result — is it safe to inner join with `trip`?
# MAGIC 3. Predict: if you inner join `trip` (100 rows, unique) with
# MAGIC    `driver_payouts` as-is, how many rows will you get?
# MAGIC 4. Replace `None` with your prediction, run, and verify
# MAGIC
# MAGIC **Think about:** Does the profile show duplicates? NULLs? What failure mode
# MAGIC from this notebook would you hit?

# COMMAND ----------

# Finance extract — has issues you need to detect
driver_payouts = spark.createDataFrame(  # noqa: F821
    [
        (1, 18.50),
        (2, 10.00),
        (2, 10.00),   # duplicate — payout processed twice
        (3, 30.00),
        (None, 5.00), # NULL — couldn't link to a trip
    ],
    ["trip_id", "payout_amount"],
)

# Step 1: Profile driver_payouts
print("driver_payouts:")
driver_payouts.show()

payout_stats = driver_payouts.select(
    F.count(F.lit(1)).alias("rows"),
    F.countDistinct("trip_id").alias("distinct"),
    F.sum(F.when(F.col("trip_id").isNull(), 1).otherwise(0)).alias("nulls"),
).collect()[0]
print(f"Profile: rows={payout_stats['rows']}, distinct={payout_stats['distinct']}, nulls={payout_stats['nulls']}")
print("  → rows ≠ distinct: duplicates exist!")
print("  → nulls > 0: inner join will drop that row!")

print()

# Step 2: YOUR PREDICTION — inner join trip (100 unique) with driver_payouts (as-is)
# Think: trip has keys [1..100]. driver_payouts has keys [1, 2, 2, 3, NULL].
# Which keys overlap? What about the duplicate? What about the NULL?
predicted_inner = None

# Step 3: Verify
actual_inner = trip.join(driver_payouts, "trip_id", "inner").count()
mark = "✓" if predicted_inner == actual_inner else "✗"
print(f"{mark} inner → predicted={predicted_inner}, actual={actual_inner}")

# COMMAND ----------

# DBTITLE 1,Summary
# MAGIC %md
# MAGIC ## Summary — what to do before every join
# MAGIC
# MAGIC **The workflow:**
# MAGIC
# MAGIC 1. **Profile** both sides on the join key (rows, distinct, nulls)
# MAGIC 2. **Decide** — is it safe to join as-is?
# MAGIC    * rows ≠ distinct → resolve duplicates (groupBy, not dropDuplicates)
# MAGIC    * nulls > 0 → handle before inner join (or use eqNullSafe)
# MAGIC 3. **Predict** the output row count based on what you know
# MAGIC 4. **Run** the join
# MAGIC 5. **Verify** — actual == predicted? If not, investigate.
# MAGIC
# MAGIC **What this catches:**
# MAGIC * M:M fanout (rows multiply because duplicates exist on both sides)
# MAGIC * NULL-key loss (rows vanish from inner joins)
# MAGIC * Accidental Cartesian (output explodes because join condition is wrong)
# MAGIC
# MAGIC **What this does NOT catch:** value-level errors. Your row count can be
# MAGIC correct but the joined values can still be wrong (e.g., matching to the
# MAGIC wrong record). That requires checking output columns against business
# MAGIC expectations (Notebook 08).
# MAGIC
# MAGIC **Next:** `03 - Lookup Joins and Unmatched Dimensions`