# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # 02 - Join Types, NULL Keys, and Validation
# MAGIC
# MAGIC Apply the four join types to **clean landing data**, then use constructed frames
# MAGIC for **many-to-many** fanout, **NULL** keys, **key profiling**, and the Module 7
# MAGIC **predict → run → verify** habit.
# MAGIC
# MAGIC You will:
# MAGIC
# MAGIC 1. Predict and verify inner, left, right, and full outer joins on 1:1 landing tables
# MAGIC 2. See row multiplication and NULL join-key behavior on small teaching frames
# MAGIC 3. Profile keys, apply a deterministic duplicate rule, and avoid accidental Cartesian products
# MAGIC
# MAGIC **Prerequisites.** Module 7 **`01 - Grain, Join Syntax, and Unmatched Keys`**
# MAGIC and Module 6 (**`01`** through **`04`**). Landing Volume must contain **`trip`**,
# MAGIC **`trip_time`**, and **`payment`** (100 rows each). Recall Module 3
# MAGIC **`eqNullSafe`** when NULL keys must match.
# MAGIC
# MAGIC **Reads:** landing **`trip`**, **`trip_time`**, **`payment`**. Skill-building — **no write**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup
# MAGIC
# MAGIC Reload the three core landing tables (explicit schemas — Module 5 contracts).

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

# MAGIC %md
# MAGIC ## Four join types on rideshare data
# MAGIC
# MAGIC On **`trip_id`**, landing **`trip`** ↔ **`trip_time`** and **`trip`** ↔
# MAGIC **`payment`** are **1:1**. Predict **100** rows for each join type, then verify.

# COMMAND ----------

predicted_landing = 100

print("trip join trip_time — predicted row count for each join type:", predicted_landing)
for how in ["inner", "left", "right", "full", "full_outer"]:
    actual = trip.join(trip_time, "trip_id", how).count()
    print(f"  {how:11} predicted={predicted_landing}, actual={actual}")

print("trip join payment — predicted row count for each join type:", predicted_landing)
for how in ["inner", "left", "right", "full", "full_outer"]:
    actual = trip.join(payment, "trip_id", how).count()
    print(f"  {how:11} predicted={predicted_landing}, actual={actual}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Constructed frame — many-to-many
# MAGIC
# MAGIC Left **`trip_id`** `[1, 1, 2]`, right `[1, 1, 3]`. Key **1** twice per side → inner **4**.

# COMMAND ----------

left_mm = spark.createDataFrame([(1,), (1,), (2,)], ["trip_id"])  # noqa: F821
right_mm = spark.createDataFrame([(1,), (1,), (3,)], ["trip_id"])

predicted_mm = 4
actual_mm = left_mm.join(right_mm, "trip_id", "inner").count()
print(f"inner many-to-many: predicted={predicted_mm}, actual={actual_mm}")
left_mm.join(right_mm, "trip_id", "inner").show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Key profiling before joining
# MAGIC
# MAGIC Compare row count vs **`countDistinct`** on the join key. **`dropDuplicates`**
# MAGIC alone is unsafe when duplicate keys carry different payloads.

# COMMAND ----------

dup_payload = spark.createDataFrame(  # noqa: F821
    [(1, "version-a"), (1, "version-b"), (2, "only-one")],
    ["trip_id", "payload"],
)

print("Before dropDuplicates:")
dup_payload.show()

print("After dropDuplicates on trip_id only:")
dup_payload.dropDuplicates(["trip_id"]).show()

# COMMAND ----------

# MAGIC %md
# MAGIC **Deterministic resolution:** **`groupBy` + `max(payload)`** per **`trip_id`**, then
# MAGIC confirm one row per key.

# COMMAND ----------

dup_resolved = dup_payload.groupBy("trip_id").agg(
    F.max("payload").alias("payload"),
)

print("After deterministic groupBy + max(payload):")
dup_resolved.orderBy("trip_id").show()

dup_resolved.select(
    F.count(F.lit(1)).alias("rows"),
    F.countDistinct("trip_id").alias("distinct_trip_id"),
).show()

# COMMAND ----------

trip.select(
    F.count(F.lit(1)).alias("rows"),
    F.countDistinct("trip_id").alias("distinct_trip_id"),
).show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Constructed frame — NULL keys
# MAGIC
# MAGIC Left **`[1, 2, NULL]`**, right **`[2, 3, NULL]`**. Standard equality never matches
# MAGIC **`NULL`**; predict inner **1**, left **3**, right **3**, full outer **5**.

# COMMAND ----------

nullable_trip_id = StructType([StructField("trip_id", LongType(), True)])

null_left = spark.createDataFrame(  # noqa: F821
    [(1,), (2,), (None,)],
    schema=nullable_trip_id,
)
null_right = spark.createDataFrame(
    [(2,), (3,), (None,)],
    schema=nullable_trip_id,
)

predictions_null = {
    "inner": 1,
    "left": 3,
    "right": 3,
    "full": 5,
    "full_outer": 5,
}

for how in ["inner", "left", "right", "full", "full_outer"]:
    predicted = predictions_null[how]
    actual = null_left.join(null_right, "trip_id", how).count()
    print(f"{how:11} predicted={predicted}, actual={actual}")

# COMMAND ----------

# MAGIC %md
# MAGIC **`eqNullSafe`** in the join condition (Module 3) matches **`NULL`** to **`NULL`**
# MAGIC — inner count **2** here.

# COMMAND ----------

null_left_a = null_left.alias("l")
null_right_a = null_right.alias("r")

eq_null_safe_inner = null_left_a.join(
    null_right_a,
    F.col("l.trip_id").eqNullSafe(F.col("r.trip_id")),
    "inner",
)

print("inner (eqNullSafe):", eq_null_safe_inner.count())
eq_null_safe_inner.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pre-join and post-join validation habit
# MAGIC
# MAGIC **Predict → run → verify** on every join in Module 7 (especially Notebook **`08`**).

# COMMAND ----------

left_rows = trip.count()
right_rows = trip_time.count()
left_distinct = trip.select(F.countDistinct("trip_id")).collect()[0][0]
right_distinct = trip_time.select(F.countDistinct("trip_id")).collect()[0][0]

predicted_inner = min(left_distinct, right_distinct)
print(f"Input: trip rows={left_rows}, distinct trip_id={left_distinct}")
print(f"Input: trip_time rows={right_rows}, distinct trip_id={right_distinct}")
print(f"Predicted inner join rows (1:1 keys): {predicted_inner}")

actual_inner = trip.join(trip_time, "trip_id", "inner").count()
print(f"Actual inner join rows: {actual_inner}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Accidental Cartesian product
# MAGIC
# MAGIC Use **`crossJoin()`** only when a full cross product is **intentional**.

# COMMAND ----------

tiny_a = spark.createDataFrame([(1,), (2,)], ["k"])  # noqa: F821
tiny_b = spark.createDataFrame([("x",), ("y",), ("z",)], ["tag"])

intentional = tiny_a.crossJoin(tiny_b)
print("Intentional crossJoin rows (2 × 3):", intentional.count())
intentional.show()

# COMMAND ----------

accidental = tiny_a.join(tiny_b, F.lit(True), "inner")
print("Accidental always-true join rows:", accidental.count())

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC On landing **`trip`** and **`payment`**:
# MAGIC
# MAGIC 1. Profile **`trip_id`** (row count and distinct count) on each side.
# MAGIC 2. Predict **inner** and **left** join row counts.
# MAGIC 3. Run both joins and verify with **`count()`**.

# COMMAND ----------

print("trip profile:")
trip.agg(
    F.count(F.lit(1)).alias("rows"),
    F.countDistinct("trip_id").alias("distinct_trip_id"),
).show()

print("payment profile:")
payment.agg(
    F.count(F.lit(1)).alias("rows"),
    F.countDistinct("trip_id").alias("distinct_trip_id"),
).show()

predicted_inner_exercise = None
predicted_left_exercise = None

print(f"Predicted inner rows: {predicted_inner_exercise}")
print(f"Predicted left rows: {predicted_left_exercise}")

print("Actual inner rows:", trip.join(payment, "trip_id", "inner").count())
print("Actual left rows:", trip.join(payment, "trip_id", "left").count())

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - **1:1 landing joins** can return the same row count for all four join types.
# MAGIC - **M:M** and **NULL** frames show fanout and equality semantics.
# MAGIC - **Profile keys**, resolve duplicates with a **deterministic rule**, and
# MAGIC   **predict → run → verify** before trusting joins.
# MAGIC
# MAGIC **Next:** Module 7 **`03 - Lookup Joins and Unmatched Dimensions`** — repeated
# MAGIC **`zone_lookup`** joins on **`curated/trip`**.
