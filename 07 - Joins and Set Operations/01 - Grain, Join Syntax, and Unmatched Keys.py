# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # 01 - Grain, Join Syntax, and Unmatched Keys
# MAGIC
# MAGIC Before production joins, clarify **grain**, **cardinality**, and **join-condition
# MAGIC syntax**. A small constructed example then shows how **inner**, **left**,
# MAGIC **right**, and **full outer** joins change row counts when keys do not align.
# MAGIC
# MAGIC You will:
# MAGIC
# MAGIC 1. Relate table grain and 1:1 / 1:M / M:1 / M:M cardinality to join row counts
# MAGIC 2. Write equi-joins as a shared column name, a column list, or a Boolean expression
# MAGIC 3. Predict and verify row counts for four join types on unmatched keys
# MAGIC
# MAGIC **Prerequisites.** Complete Module 6 (**`01`** through **`04`**). Landing Volume
# MAGIC must contain **`trip`** and **`trip_time`** (100 rows each on the core files).
# MAGIC
# MAGIC **Reads:** landing **`trip`**, **`trip_time`** only. Skill-building — **no write**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup
# MAGIC
# MAGIC Import **`F`**, define landing paths, and load **`trip`** and **`trip_time`**
# MAGIC with explicit schemas (Module 5 contracts). Join key: **`trip_id`**.

# COMMAND ----------

from pyspark.sql import functions as F

landing_root = "/Volumes/rideshare_dev/landing/source_files"
trip_csv_path = f"{landing_root}/trip/trip.csv"
trip_time_parquet_path = f"{landing_root}/trip_time/trip_time.parquet"

print(f"trip_csv_path = {trip_csv_path}")
print(f"trip_time_parquet_path = {trip_time_parquet_path}")

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

trip_time_schema_ddl = """
trip_id bigint,
trip_date date,
hour_of_day int
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

print("trip rows:", trip.count())
print("trip_time rows:", trip_time.count())

# COMMAND ----------

# MAGIC %md
# MAGIC ## Grain orientation
# MAGIC
# MAGIC **Grain** is what one row represents. For **`trip`**, the grain is **one row
# MAGIC per `trip_id`**. When row count equals distinct **`trip_id`**, the table is unique
# MAGIC on that key.

# COMMAND ----------

trip_grain = trip.agg(
    F.count(F.lit(1)).alias("row_count"),
    F.countDistinct("trip_id").alias("distinct_trip_id"),
).collect()[0]

print(
    f"trip: {trip_grain.row_count} rows, "
    f"{trip_grain.distinct_trip_id} distinct trip_id values"
)
print(
    "Grain check:",
    "one row per trip_id"
    if trip_grain.row_count == trip_grain.distinct_trip_id
    else "NOT unique on trip_id",
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cardinality vocabulary
# MAGIC
# MAGIC | Label | Meaning | Row-count intuition (equi-join) |
# MAGIC |---|---|---|
# MAGIC | **1:1** | Each left key matches at most one right key | Often same count when keys align |
# MAGIC | **1:M** | One left key matches many right rows | Output can **multiply** |
# MAGIC | **M:1** | Many left rows match one right row | Output follows left row count |
# MAGIC | **M:M** | Duplicates on **both** sides | Output can **multiply sharply** |
# MAGIC
# MAGIC Landing **`trip`** ↔ **`trip_time`** on **`trip_id`** is **1:1** (100 rows and
# MAGIC 100 distinct keys on each side). Notebook **`02`** applies the four join types on
# MAGIC that landing pair.

# COMMAND ----------

for name, df in [("trip", trip), ("trip_time", trip_time)]:
    stats = df.agg(
        F.count(F.lit(1)).alias("rows"),
        F.countDistinct("trip_id").alias("distinct_trip_id"),
    ).collect()[0]
    print(f"{name}: rows={stats.rows}, distinct trip_id={stats.distinct_trip_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Join-condition syntax
# MAGIC
# MAGIC Three equi-join forms — Notebook **`03`** needs the **Boolean** form for zone lookup.

# COMMAND ----------

# MAGIC %md
# MAGIC ### String: single shared column name
# MAGIC
# MAGIC Pass the shared key name as a **string**. Spark coalesces duplicate key columns
# MAGIC into one **`trip_id`**.

# COMMAND ----------

join_string = trip.join(trip_time, "trip_id", "inner")
print("Columns after string join on trip_id:", join_string.columns)
print("Row count:", join_string.count())
join_string.select("trip_id", "trip_date", "hour_of_day").show(3, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### List: composite equi-join
# MAGIC
# MAGIC Pass a **list of column names** when the relationship requires more than one key.

# COMMAND ----------

left_composite = spark.createDataFrame(  # noqa: F821
    [(1, 10, "left-a"), (2, 20, "left-b")],
    ["trip_id", "leg_id", "left_note"],
)
right_composite = spark.createDataFrame(
    [(1, 10, "match"), (1, 11, "other-leg"), (2, 20, "match")],
    ["trip_id", "leg_id", "right_flag"],
)

print(
    "Join on trip_id only (ignores leg_id):",
    left_composite.join(right_composite, "trip_id", "inner").count(),
)
print(
    "Join on [trip_id, leg_id] (composite):",
    left_composite.join(right_composite, ["trip_id", "leg_id"], "inner").count(),
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Boolean: explicit column condition
# MAGIC
# MAGIC Use when key **names differ** or you need an explicit expression. Spark **keeps
# MAGIC both sides' key columns** when names match — resolve them with aliases in
# MAGIC Notebook **`04`**.

# COMMAND ----------

join_bool_raw = trip.alias("t").join(
    trip_time.alias("tt"),
    F.col("t.trip_id") == F.col("tt.trip_id"),
    "inner",
)

print("Boolean join columns (both trip_id sides retained):", join_bool_raw.columns)
join_bool_raw.select(
    F.col("t.trip_id"),
    F.col("tt.trip_id"),
    F.col("tt.trip_date"),
).show(3, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Constructed frame — unmatched keys
# MAGIC
# MAGIC Left **`trip_id`** `[1, 2, 3, 4, 5]`, right `[3, 4, 5, 6, 7]`.
# MAGIC
# MAGIC | Join type | Predicted rows |
# MAGIC |---|---:|
# MAGIC | inner | 3 |
# MAGIC | left | 5 |
# MAGIC | right | 5 |
# MAGIC | full outer | 7 |

# COMMAND ----------

left_unmatched = spark.createDataFrame(  # noqa: F821
    [(1,), (2,), (3,), (4,), (5,)],
    ["trip_id"],
)
right_unmatched = spark.createDataFrame(
    [(3,), (4,), (5,), (6,), (7,)],
    ["trip_id"],
)

predictions_unmatched = {"inner": 3, "left": 5, "right": 5, "full": 7, "full_outer": 7}

for how in ["inner", "left", "right", "full", "full_outer"]:
    predicted = predictions_unmatched[how]
    actual = left_unmatched.join(right_unmatched, "trip_id", how).count()
    print(f"{how:11} predicted={predicted}, actual={actual}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Using **`left_composite`** and **`right_composite`** from above:
# MAGIC
# MAGIC 1. Predict the **inner** join row count on **`[trip_id, leg_id]`** only.
# MAGIC 2. Run that join and verify with **`count()`**.
# MAGIC
# MAGIC Do not write any output.

# COMMAND ----------

predicted_composite_inner = None  # replace with your prediction
actual_composite_inner = left_composite.join(
    right_composite,
    ["trip_id", "leg_id"],
    "inner",
).count()

print(f"Predicted composite inner rows: {predicted_composite_inner}")
print(f"Actual composite inner rows: {actual_composite_inner}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - **Grain** and **cardinality** vocabulary predict join behavior before you run code.
# MAGIC - **String**, **list**, and **Boolean** join forms differ in how key columns appear.
# MAGIC - **Unmatched keys** make inner / left / right / full outer row counts diverge.
# MAGIC
# MAGIC **Next:** Module 7 **`02 - Join Types, NULL Keys, and Validation`** — landing
# MAGIC 1:1 joins, many-to-many and NULL-key frames, key profiling, and the predict habit.
