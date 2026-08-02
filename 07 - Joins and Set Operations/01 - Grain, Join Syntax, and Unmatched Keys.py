# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # 01 - Grain, Join Syntax, and Unmatched Keys
# MAGIC
# MAGIC Before production joins, clarify **grain**, **cardinality**, and **join-condition
# MAGIC syntax**. Constructed examples show how join types change row counts when keys
# MAGIC do not align or when a single key matches too broadly.
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
# MAGIC **Grain** is what one row represents. For **`trip`**, the grain is **one row per
# MAGIC `trip_id`**. A join may **preserve** that grain (1:1), **widen** it (1:M), or
# MAGIC **multiply** it (M:M) depending on key uniqueness on each side.
# MAGIC
# MAGIC Compare total row count to **`countDistinct("trip_id")`**. When they match, the
# MAGIC table is unique on that key.

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
# MAGIC Landing **`trip`** ↔ **`trip_time`** on **`trip_id`** is **1:1**. **1:M** and **M:1**
# MAGIC appear below on **`trip_summary`** ↔ **`trip_charges`**. **M:M** fanout is in
# MAGIC Notebook **`02`**.

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
# MAGIC | Form | Syntax | When to use |
# MAGIC |---|---|---|
# MAGIC | **String** | `"trip_id"` | Same join column name on both sides |
# MAGIC | **List** | `["trip_id", "charge_type"]` | Composite key; same column names both sides |
# MAGIC | **Boolean** | `F.col("l.key") == F.col("r.key")` | Different key names or full control |
# MAGIC
# MAGIC Notebook **`03`** uses **Boolean** for zone lookup:
# MAGIC **`pickup_location_id`** / **`dropoff_location_id`** ↔ **`zone_lookup.location_id`**.

# COMMAND ----------

# MAGIC %md
# MAGIC ### String: same join column name on both sides
# MAGIC
# MAGIC Spark coalesces duplicate key columns into **one** **`trip_id`** in the result.

# COMMAND ----------

join_string = trip.join(trip_time, "trip_id", "inner")
print("Columns after string join on trip_id:", join_string.columns)
print("Row count:", join_string.count())
join_string.select("trip_id", "trip_date", "hour_of_day").show(3, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### List: multiple join column names (composite key)
# MAGIC
# MAGIC **`trip_charges`** is one row per **`trip_id` + `charge_type`** (base fare, surge,
# MAGIC tip — same ideas as landing **`payment`**, in long form for join practice).
# MAGIC
# MAGIC - **`trip_summary`** join **`trip_charges`** on **`trip_id` only** → **1:M** (predict **6**)
# MAGIC - **`trip_charges`** join **`rate_card`** on **`[trip_id, charge_type]`** → predict **4**

# COMMAND ----------

trip_summary = spark.createDataFrame(  # noqa: F821
    [(1, "standard", 12.50), (2, "premium", 25.00)],
    ["trip_id", "service_type", "total_fare"],
)

trip_charges = spark.createDataFrame(  # noqa: F821
    [
        (1, "base_fare", 8.00),
        (1, "surge", 3.00),
        (1, "tip", 1.50),
        (2, "base_fare", 18.00),
        (2, "surge", 5.00),
        (2, "tip", 2.00),
    ],
    ["trip_id", "charge_type", "amount"],
)

rate_card = spark.createDataFrame(  # noqa: F821
    [
        (1, "base_fare", 8.00),
        (1, "surge", 3.00),
        (2, "base_fare", 18.00),
        (2, "surge", 5.00),
    ],
    ["trip_id", "charge_type", "expected_amount"],
)

predicted_trip_id_only = 6
single_key = trip_summary.join(trip_charges, "trip_id", "inner")
actual_trip_id_only = single_key.count()
print(
    f"trip_id only: predicted={predicted_trip_id_only}, actual={actual_trip_id_only}"
)

predicted_composite = 4
composite_key = trip_charges.join(rate_card, ["trip_id", "charge_type"], "inner")
actual_composite = composite_key.count()
print(
    f"[trip_id, charge_type]: predicted={predicted_composite}, "
    f"actual={actual_composite}"
)
composite_key.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### M:1 — many left rows per right key
# MAGIC
# MAGIC Flip the **1:M** join: put **`trip_charges`** on the left and **`trip_summary`**
# MAGIC on the right (still **`trip_id` only**). Each charge row matches one summary row,
# MAGIC so the output row count follows the **left** side — predict **6**, same as **1:M**
# MAGIC fanout but with **M:1** vocabulary.

# COMMAND ----------

predicted_m1 = 6
m1_join = trip_charges.join(trip_summary, "trip_id", "inner")
actual_m1 = m1_join.count()
print(f"M:1 (charges → summary on trip_id): predicted={predicted_m1}, actual={actual_m1}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Boolean: explicit column condition
# MAGIC
# MAGIC String and list forms require the **same column name(s)** on both sides. When names
# MAGIC differ — **`trip_id`** vs **`trip_no`** — use a Boolean expression. That is also
# MAGIC how Notebook **`03`** joins trip location columns to **`location_id`**.
# MAGIC
# MAGIC Boolean joins keep **both** key columns unless you **`select`** or alias them away.

# COMMAND ----------

left_id = spark.createDataFrame(  # noqa: F821
    [(1, "a"), (2, "b")],
    ["trip_id", "note"],
)
right_no = spark.createDataFrame(  # noqa: F821
    [(1, 10.0), (3, 30.0)],
    ["trip_no", "score"],
)

join_diff_names = left_id.alias("l").join(
    right_no.alias("r"),
    F.col("l.trip_id") == F.col("r.trip_no"),
    "inner",
)
print("trip_id = trip_no (Boolean only):")
join_diff_names.show()

join_bool_raw = trip.alias("t").join(
    trip_time.alias("tt"),
    F.col("t.trip_id") == F.col("tt.trip_id"),
    "inner",
)
print("Same name, Boolean form — columns:", join_bool_raw.columns)
join_bool_raw.select(
    F.col("t.trip_id"),
    F.col("tt.trip_id"),
    F.col("tt.trip_date"),
).show(3, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Constructed frame — unmatched keys
# MAGIC
# MAGIC Left **`trip_id`** `[1…5]`, right **`[3…7]`**. Overlap **`{3, 4, 5}`**.
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
right_unmatched = spark.createDataFrame(  # noqa: F821
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
# MAGIC On mini-frames with left **`trip_id`** **`[1, 2, 3, 4]`** and right **`[2, 3, 4, 5]`**
# MAGIC (overlap **`{2, 3, 4}`** — different keys than the **`[1…5]`** / **`[3…7]`** demo):
# MAGIC
# MAGIC 1. Predict row counts for **inner** and **right** joins on **`trip_id`**.
# MAGIC 2. Run both joins and verify with **`count()`**.
# MAGIC
# MAGIC Do not write any output.

# COMMAND ----------

left_exercise = spark.createDataFrame(  # noqa: F821
    [(1,), (2,), (3,), (4,)],
    ["trip_id"],
)
right_exercise = spark.createDataFrame(  # noqa: F821
    [(2,), (3,), (4,), (5,)],
    ["trip_id"],
)

predicted_inner_exercise = None  # replace with your prediction
predicted_right_exercise = None  # replace with your prediction

actual_inner_exercise = left_exercise.join(
    right_exercise, "trip_id", "inner"
).count()
actual_right_exercise = left_exercise.join(
    right_exercise, "trip_id", "right"
).count()

print(f"Predicted inner rows: {predicted_inner_exercise}")
print(f"Actual inner rows: {actual_inner_exercise}")
print(f"Predicted right rows: {predicted_right_exercise}")
print(f"Actual right rows: {actual_right_exercise}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - **Grain** and **cardinality** predict join row counts; joins can preserve, widen,
# MAGIC   or multiply grain.
# MAGIC - **String**, **list**, and **Boolean** join forms — list demo on **`trip_charges`**
# MAGIC   / **`rate_card`**; Boolean for mismatched names and zone lookup in **`03`**.
# MAGIC - **Unmatched keys** change inner / left / right / full outer counts — always
# MAGIC   **predict → run → verify**.
# MAGIC
# MAGIC **Next:** Module 7 **`02 - Join Types, NULL Keys, and Validation`**.
