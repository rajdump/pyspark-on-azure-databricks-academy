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

# COMMAND ----------

# DBTITLE 1,Setup
# MAGIC %md
# MAGIC ## 2. Setup — load and verify the clean 1:1 baseline
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
# MAGIC All should return 100. This is a baseline signal — not proof of 1:1 grain
# MAGIC (Section 4 establishes that), but a quick sanity check that nothing is
# MAGIC obviously wrong.

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

predicted = 100
pairs = [("trip", "trip_time", trip, trip_time), ("trip", "payment", trip, payment)]

for left_name, right_name, left_df, right_df in pairs:
    print(f"{left_name} ↔ {right_name}:")
    for how in ["inner", "left", "right", "full"]:
        actual = left_df.join(right_df, "trip_id", how).count()
        mark = "✓" if actual == predicted else "✗"
        print(f"  {mark} {how:6} → predicted={predicted}, actual={actual}")
    print()

# COMMAND ----------

# DBTITLE 1,2. M:M fanout
# MAGIC %md
# MAGIC ## 3. M:M — when both sides have duplicates
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

# DBTITLE 1,3. Pre-join profiling
# MAGIC %md
# MAGIC ## 4. Key profiling — detect duplicates before joining
# MAGIC
# MAGIC Before any join, profile the key on both sides:
# MAGIC
# MAGIC 1. **Row count** — total rows in the table
# MAGIC 2. **Distinct non-NULL keys** — `countDistinct(key)` (this ignores NULLs)
# MAGIC 3. **NULL key count** — rows where the key is NULL
# MAGIC
# MAGIC If rows == distinct and nulls == 0 → the key is unique and complete.
# MAGIC If not → fix before joining (next section).

# COMMAND ----------

for name, df in [("trip", trip), ("trip_time", trip_time), ("payment", payment)]:
    stats = df.select(
        F.count(F.lit(1)).alias("rows"),
        F.countDistinct("trip_id").alias("distinct_keys"),
        F.sum(F.when(F.col("trip_id").isNull(), 1).otherwise(0)).alias("null_keys"),
    ).collect()[0]
    print(
        f"{name:10} rows={stats['rows']}, "
        f"distinct={stats['distinct_keys']}, "
        f"nulls={stats['null_keys']}"
    )

# COMMAND ----------

# DBTITLE 1,3b. Duplicate resolution
# MAGIC %md
# MAGIC ## 5. Duplicate resolution — don't let Spark decide
# MAGIC
# MAGIC You profiled and found duplicates. Two approaches:
# MAGIC
# MAGIC | Method | Behavior |
# MAGIC |---|---|
# MAGIC | `dropDuplicates(["trip_id"])` | Keeps one row per key — survivor is non-deterministic (different plans may keep different rows) |
# MAGIC | `groupBy("trip_id").agg(...)` | Keeps one row using YOUR rule — deterministic, same input always gives same output |
# MAGIC
# MAGIC `dropDuplicates` is fine when all rows for a key are truly identical. When
# MAGIC they differ (different payloads, timestamps, amounts), use `groupBy` with an
# MAGIC explicit rule: `max`, `min`, `F.first`, or whatever your business logic requires.

# COMMAND ----------

dup_payload = spark.createDataFrame(  # noqa: F821
    [(1, "version-a"), (1, "version-b"), (2, "only-one")],
    ["trip_id", "payload"],
)

print("Before — trip_id=1 has two different payloads:")
dup_payload.show()

print("After dropDuplicates — which survived? Non-deterministic:")
dup_payload.dropDuplicates(["trip_id"]).orderBy("trip_id").show()

print("After groupBy + max — always picks 'version-b' (alphabetical max):")
resolved = dup_payload.groupBy("trip_id").agg(F.max("payload").alias("payload"))
resolved.orderBy("trip_id").show()

# Verify grain after resolution
stats = resolved.select(
    F.count(F.lit(1)).alias("rows"),
    F.countDistinct("trip_id").alias("distinct"),
).collect()[0]
print(f"Resolved: rows={stats['rows']}, distinct={stats['distinct']} → grain is clean")

# COMMAND ----------

# DBTITLE 1,4. NULL-key loss
# MAGIC %md
# MAGIC ## 6. NULL keys — silent data loss
# MAGIC
# MAGIC In SQL and Spark, `NULL = NULL` evaluates to `NULL` (not TRUE). Standard
# MAGIC equality never matches NULL to NULL. Result: NULL-key rows vanish from inner
# MAGIC joins without warning.
# MAGIC
# MAGIC When you hit this: missing `trip_id` from upstream ETL, optional foreign keys,
# MAGIC or NULLs introduced by a prior outer join.
# MAGIC
# MAGIC ```
# MAGIC Left trip_id:  [1, 2, NULL]
# MAGIC Right trip_id: [2, 3, NULL]
# MAGIC ```
# MAGIC
# MAGIC Predict each join type — replace `None` in the cell below:
# MAGIC * inner: only key 2 matches (NULL ≠ NULL)
# MAGIC * left: all 3 left rows kept; right fills NULLs where no match
# MAGIC * right: all 3 right rows kept; left fills NULLs where no match
# MAGIC * full: all unique entities from both sides

# COMMAND ----------

nullable_schema = StructType([StructField("trip_id", LongType(), True)])

null_left = spark.createDataFrame([(1,), (2,), (None,)], schema=nullable_schema)  # noqa: F821
null_right = spark.createDataFrame([(2,), (3,), (None,)], schema=nullable_schema)

# YOUR PREDICTIONS — replace None with expected row count
predictions = {
    "inner": None,
    "left": None,
    "right": None,
    "full": None,
}

for join_type, predicted in predictions.items():
    actual = null_left.join(null_right, "trip_id", join_type).count()
    mark = "✓" if predicted == actual else "✗"
    print(f"{mark} {join_type:6} → predicted={predicted}, actual={actual}")

# COMMAND ----------

# DBTITLE 1,4b. eqNullSafe
# MAGIC %md
# MAGIC ### 6b. When you WANT NULL to match NULL
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

null_left_a = null_left.alias("l")
null_right_a = null_right.alias("r")

eq_safe = null_left_a.join(
    null_right_a,
    F.col("l.trip_id").eqNullSafe(F.col("r.trip_id")),
    "inner",
)

print(f"inner (eqNullSafe): predicted=2, actual={eq_safe.count()}")
eq_safe.show()

# COMMAND ----------

# DBTITLE 1,5. Cartesian explosion
# MAGIC %md
# MAGIC ## 7. Cartesian products — intentional versus accidental
# MAGIC
# MAGIC | Code | Intent | Result (2 × 3) |
# MAGIC |---|---|---|
# MAGIC | `a.crossJoin(b)` | Intentional — all combinations | 6 |
# MAGIC | `a.join(b, F.lit(True), "inner")` | Anti-pattern — always-true condition | 6 |
# MAGIC
# MAGIC `crossJoin` is legitimate when you need every combination (e.g., generating a
# MAGIC calendar × product grid). `F.lit(True)` as a join condition is an explicit
# MAGIC always-true anti-pattern that demonstrates Cartesian risk — not a realistic
# MAGIC example of merely "forgetting" a key, but it shows what the failure looks like.
# MAGIC
# MAGIC On production tables: 100K × 100K = 10 billion rows. Your cluster crashes or
# MAGIC runs for hours. If you see an always-true condition in a join, treat it as a
# MAGIC bug.

# COMMAND ----------

tiny_a = spark.createDataFrame([(1,), (2,)], ["k"])  # noqa: F821
tiny_b = spark.createDataFrame([("x",), ("y",), ("z",)], ["tag"])

intentional = tiny_a.crossJoin(tiny_b)
print(f"Intentional crossJoin: 2 × 3 = {intentional.count()} rows")
intentional.show()

anti_pattern = tiny_a.join(tiny_b, F.lit(True), "inner")
print(f"Anti-pattern F.lit(True): 2 × 3 = {anti_pattern.count()} rows")
print("→ Same result. On large tables, this is a silent disaster.")

# COMMAND ----------

# DBTITLE 1,6. Validation exercise and summary
# MAGIC %md
# MAGIC ## 8. Exercise — full pre-join and post-join validation
# MAGIC
# MAGIC Apply the complete workflow on `trip` ↔ `payment`:
# MAGIC
# MAGIC 1. Profile key uniqueness (rows vs distinct)
# MAGIC 2. Count NULL keys
# MAGIC 3. Predict inner and left join counts
# MAGIC 4. Run and verify
# MAGIC
# MAGIC Replace `None` below with your predictions, then run.

# COMMAND ----------

# Profile
for name, df in [("trip", trip), ("payment", payment)]:
    stats = df.select(
        F.count(F.lit(1)).alias("rows"),
        F.countDistinct("trip_id").alias("distinct"),
        F.sum(F.when(F.col("trip_id").isNull(), 1).otherwise(0)).alias("nulls"),
    ).collect()[0]
    print(f"{name:8} rows={stats['rows']}, distinct={stats['distinct']}, nulls={stats['nulls']}")

print()

# YOUR PREDICTIONS — replace None
predicted_inner = None
predicted_left = None

# Verify
actual_inner = trip.join(payment, "trip_id", "inner").count()
actual_left = trip.join(payment, "trip_id", "left").count()

mark_i = "✓" if predicted_inner == actual_inner else "✗"
mark_l = "✓" if predicted_left == actual_left else "✗"
print(f"{mark_i} inner → predicted={predicted_inner}, actual={actual_inner}")
print(f"{mark_l} left  → predicted={predicted_left}, actual={actual_left}")

# COMMAND ----------

# DBTITLE 1,9. Summary
# MAGIC %md
# MAGIC ## 9. Summary — `profile → predict → run → verify`
# MAGIC
# MAGIC | Failure mode | What happens | How to prevent |
# MAGIC |---|---|---|
# MAGIC | M:M duplicates | Rows multiply per key | Profile: rows == distinct? |
# MAGIC | NULL keys | Inner joins drop NULL-key rows | Profile NULL count; eqNullSafe if needed |
# MAGIC | Accidental Cartesian | Every row × every row | Never join on always-true condition |
# MAGIC | Non-deterministic dedup | Different plans may keep different rows | groupBy + explicit rule |
# MAGIC
# MAGIC This habit catches row-count failures. It does not prove every joined value
# MAGIC is correct — that requires checking output columns against business
# MAGIC expectations (Notebook 08).
# MAGIC
# MAGIC **Next:** `03 - Lookup Joins and Unmatched Dimensions`