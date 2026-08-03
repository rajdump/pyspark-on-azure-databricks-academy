# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC # 05 - Union and unionByName
# MAGIC
# MAGIC Joins add columns — they combine fields from two DataFrames side by side.
# MAGIC Union operations add rows — they stack DataFrames vertically into one.
# MAGIC
# MAGIC Spark provides two union methods:
# MAGIC
# MAGIC - **`union()`** — matches columns by position. Fast, but silently produces
# MAGIC   wrong results if column order differs between the two sides.
# MAGIC - **`unionByName()`** — matches columns by name. Safer when column order may
# MAGIC   vary, and supports an `allowMissingColumns` flag for schema differences.
# MAGIC
# MAGIC | Section | Focus |
# MAGIC |---|---|
# MAGIC | 1 | `union` — stack by position and the column-order trap |
# MAGIC | 2 | `unionByName` — match by name, not position |
# MAGIC | 3 | `allowMissingColumns` — handle different schemas |
# MAGIC | 4 | `distinct()` after union — removing extra copies |
# MAGIC | Practice | Predict and verify counts on overlapping filters |
# MAGIC
# MAGIC **Prerequisites.** Module 7 **`01`–`04`**; Module 5 so landing volumes
# MAGIC exist. **No write.**

# COMMAND ----------

# DBTITLE 1,Setup
# MAGIC %md
# MAGIC ## Setup — load landing trip and create named filters
# MAGIC
# MAGIC | Table | Format | Grain | Key | Rows | Used in |
# MAGIC |---|---|---|---|---|---|
# MAGIC | Landing `trip` | CSV | one completed trip | `trip_id` | 100 | All sections |
# MAGIC
# MAGIC This notebook works entirely from named subsets of the landing trip table.
# MAGIC No second table is needed — we split, stack, and compare.

# COMMAND ----------

# DBTITLE 1,Load landing trip and create named filters
from pyspark.sql import functions as F

landing_root = "/Volumes/rideshare_dev/landing/source_files"

trip = (
    spark.read.format("csv")
    .option("header", True)
    .schema(
        "trip_id bigint, service_type string, pickup_location_id int, "
        "dropoff_location_id int, trip_distance_miles decimal(8,2), "
        "request_to_pickup_mins int, ride_duration_mins int, "
        "driver_arrival_to_pickup_mins int"
    )
    .load(f"{landing_root}/trip/trip.csv")
)

# Named filters for Sections 1–4
le_50 = trip.filter(F.col("trip_id") <= 50)   # first half
gt_50 = trip.filter(F.col("trip_id") > 50)    # second half
premium = trip.filter(F.col("service_type") == "Premium")

print(f"trip:    {trip.count()} rows")
print(f"le_50:   {le_50.count()} rows")
print(f"gt_50:   {gt_50.count()} rows")
print(f"premium: {premium.count()} rows")

# COMMAND ----------

# DBTITLE 1,1. union
# MAGIC %md
# MAGIC ## 1. `union` — stack by position
# MAGIC
# MAGIC `union()` appends rows from the second DataFrame below the first. Columns
# MAGIC are matched by **position** — column 1 of the right aligns with column 1 of
# MAGIC the left, regardless of name.
# MAGIC
# MAGIC When both sides share the same schema and column order, this works
# MAGIC correctly.

# COMMAND ----------

# DBTITLE 1,1. Basic union — reconstruct the full table
# Two disjoint halves → full table
reconstructed = le_50.union(gt_50)

print("le_50 + gt_50:", reconstructed.count(), "rows")
print("Columns:", reconstructed.columns)

# COMMAND ----------

# DBTITLE 1,1b. The column-order trap
# MAGIC %md
# MAGIC ### The column-order trap
# MAGIC
# MAGIC If one side has columns in a different order, `union()` silently puts values
# MAGIC into the wrong columns. No error, no warning — just corrupted data.

# COMMAND ----------

# DBTITLE 1,1b. Column-order trap demo
# Swap pickup and dropoff positions on the right side
gt_50_swapped = gt_50.select(
    "trip_id", "pickup_location_id", "dropoff_location_id"
)
le_50_normal = le_50.select(
    "trip_id", "pickup_location_id", "dropoff_location_id"
)

# Swap column order on one side
gt_50_bad = gt_50.select(
    "trip_id", "dropoff_location_id", "pickup_location_id"
)

bad_union = le_50_normal.union(gt_50_bad)

print("Original gt_50 row (trip_id 51):")
gt_50_swapped.filter(F.col("trip_id") == 51).show()

print("Same row after union — pickup and dropoff are SWAPPED:")
bad_union.filter(F.col("trip_id") == 51).show()

# COMMAND ----------

# DBTITLE 1,2. unionByName
# MAGIC %md
# MAGIC ## 2. `unionByName` — match by name, not position
# MAGIC
# MAGIC `unionByName()` aligns columns by **name**. Column order no longer matters.
# MAGIC This is the safer choice whenever column order might differ between sides.

# COMMAND ----------

# DBTITLE 1,2. unionByName fixes the swap
# Same frames that broke with union — unionByName handles them correctly
good_union = le_50_normal.unionByName(gt_50_bad)

print("unionByName on the same swapped frames — trip_id 51:")
good_union.filter(F.col("trip_id") == 51).show()
print("→ Pickup and dropoff are correct because columns matched by name")

# COMMAND ----------

# DBTITLE 1,2b. When column sets differ
# MAGIC %md
# MAGIC ### When column sets differ
# MAGIC
# MAGIC `unionByName` requires both DataFrames to have the **same column names** by
# MAGIC default. If one side has a column the other doesn’t, Spark raises an error.

# COMMAND ----------

# DBTITLE 1,2b. Column mismatch error
# full_cols has 3 columns; partial_cols has only 2
full_cols = le_50.select("trip_id", "service_type", "trip_distance_miles")
partial_cols = le_50.select("trip_id", "service_type")

try:
    full_cols.unionByName(partial_cols).show()
except Exception as e:
    print("unionByName fails when column sets differ:")
    print(f"  {str(e).splitlines()[0]}")

# COMMAND ----------

# DBTITLE 1,3. allowMissingColumns
# MAGIC %md
# MAGIC ## 3. `allowMissingColumns` — handle different schemas
# MAGIC
# MAGIC When combining DataFrames from different sources or schema versions, one
# MAGIC side may have columns the other does not. Setting `allowMissingColumns=True`
# MAGIC fills the missing columns with NULL instead of raising an error.

# COMMAND ----------

# DBTITLE 1,3. allowMissingColumns demo
# Use 3 rows from each side so NULLs are visible in the output
full_3 = full_cols.limit(3)
partial_3 = partial_cols.limit(3)

result = full_3.unionByName(partial_3, allowMissingColumns=True)

print("allowMissingColumns=True — NULLs fill the gap:")
result.show()

# COMMAND ----------

# DBTITLE 1,4. distinct after union
# MAGIC %md
# MAGIC ## 4. `distinct()` after union — removing extra copies
# MAGIC
# MAGIC `union()` keeps every row from both sides, including exact duplicates. It
# MAGIC does not deduplicate.
# MAGIC
# MAGIC Apply `distinct()` only when extra copies are **unintended** — for example,
# MAGIC overlapping source files or retry reprocessing. Do not apply it by default;
# MAGIC some workflows produce legitimate repeated rows.

# COMMAND ----------

# DBTITLE 1,4. distinct demo — double-union same subset
# Union premium with itself — every row appears twice
doubled = premium.union(premium)

print("premium rows:", premium.count())
print("After union with itself:", doubled.count())
print("After distinct():", doubled.distinct().count())
print("\n→ distinct() removed the extra copies")

# COMMAND ----------

# DBTITLE 1,4b. distinct vs dropDuplicates
# MAGIC %md
# MAGIC `distinct()` removes whole-row duplicates — same effect as
# MAGIC `dropDuplicates()` without arguments. Notebook 02 used `dropDuplicates` for
# MAGIC **key-level** dedup before joins — different context.

# COMMAND ----------

# DBTITLE 1,Practice
# MAGIC %md
# MAGIC ## Practice — predict and verify
# MAGIC
# MAGIC The `service_type` distribution in landing trip:
# MAGIC
# MAGIC | service_type | count |
# MAGIC |---|---:|
# MAGIC | Standard | 52 |
# MAGIC | Shared | 21 |
# MAGIC | Premium | 15 |
# MAGIC | XL | 12 |
# MAGIC
# MAGIC Create two overlapping groups and predict the counts before running.

# COMMAND ----------

# DBTITLE 1,Practice — overlapping service_type union
# TODO (practice):
# 1. Create group_a: service_type IN ("Premium", "Standard")  → predict: ?
# 2. Create group_b: service_type IN ("Standard", "Shared")   → predict: ?
# 3. unionByName group_a and group_b                          → predict: ?
# 4. Apply distinct()                                         → predict: ?
# 5. How many extra copies were removed?                      → predict: ?
#
# Hint: Standard appears in both groups.


# COMMAND ----------

# DBTITLE 1,Summary
# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC 1. **`union`** matches columns by position — fast, but silently corrupts
# MAGIC    data if column order differs between sides.
# MAGIC
# MAGIC 2. **`unionByName`** matches columns by name — safer when column order may
# MAGIC    vary.
# MAGIC
# MAGIC 3. **`allowMissingColumns=True`** fills missing columns with NULL when
# MAGIC    schemas differ between sides.
# MAGIC
# MAGIC 4. **`distinct()` after union** removes exact whole-row duplicates. Use it
# MAGIC    intentionally when extra copies are unintended, not as a default.
# MAGIC
# MAGIC **Next:** **`06 - Intersect, subtract, and exceptAll`**