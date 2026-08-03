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
# MAGIC | Practice | Predict and verify counts on overlapping frames |
# MAGIC
# MAGIC **Prerequisites.** Module 7 **`01`–`04`**. **No write.**

# COMMAND ----------

# DBTITLE 1,Setup
# MAGIC %md
# MAGIC ## Setup — constructed frames
# MAGIC
# MAGIC This notebook uses tiny handmade DataFrames — the same pattern as Notebook 01
# MAGIC and the official PySpark `union` / `unionByName` examples. No landing or
# MAGIC curated read is required.
# MAGIC
# MAGIC | Frame | Rows | Columns |
# MAGIC |---|---:|---|
# MAGIC | `morning` | 2 | `trip_id`, `pickup_location_id`, `dropoff_location_id` |
# MAGIC | `afternoon` | 2 | same as `morning` |

# COMMAND ----------

# DBTITLE 1,Create morning and afternoon
from pyspark.sql import functions as F

morning = spark.createDataFrame(  # noqa: F821
    [(1, 10, 20), (2, 11, 21)],
    ["trip_id", "pickup_location_id", "dropoff_location_id"],
)
afternoon = spark.createDataFrame(  # noqa: F821
    [(3, 12, 22), (4, 13, 23)],
    ["trip_id", "pickup_location_id", "dropoff_location_id"],
)

print("morning:")
morning.show()
print("afternoon:")
afternoon.show()

# COMMAND ----------

# DBTITLE 1,1. union
# MAGIC %md
# MAGIC ## 1. `union` — stack by position
# MAGIC
# MAGIC `union()` appends rows from the second DataFrame below the first. Columns are
# MAGIC matched by **position** — column 1 of the right aligns with column 1 of the
# MAGIC left, regardless of name. The result keeps the left DataFrame's column names.
# MAGIC
# MAGIC `union()` does **not** remove duplicates. Compatible types by position are
# MAGIC required; incompatible types raise an error.
# MAGIC
# MAGIC **The column-order trap.** If one side has columns in a different order,
# MAGIC `union()` silently puts values into the wrong columns. No error, no warning —
# MAGIC just corrupted data.

# COMMAND ----------

# DBTITLE 1,1. Basic union — same schema and order
combined = morning.union(afternoon)

print("rows:", combined.count())
combined.show()

# COMMAND ----------

# DBTITLE 1,1b. Column-order trap demo
# Same rows as afternoon; pickup and dropoff columns swapped in position
afternoon_reordered = afternoon.select(
    "trip_id", "dropoff_location_id", "pickup_location_id"
)

print("afternoon_reordered (names still correct; column order differs):")
afternoon_reordered.show()

bad_union = morning.union(afternoon_reordered)
print("After union — afternoon pickup/dropoff values are corrupted:")
bad_union.show()

# COMMAND ----------

# DBTITLE 1,2. unionByName
# MAGIC %md
# MAGIC ## 2. `unionByName` — match by name, not position
# MAGIC
# MAGIC `unionByName()` aligns columns by **name**. Column order no longer matters.
# MAGIC This is the safer choice whenever order might differ between sides.
# MAGIC
# MAGIC By default both sides must share the same column names. Missing names raise
# MAGIC an error — Section 3 shows how to handle that.

# COMMAND ----------

# DBTITLE 1,2. unionByName fixes the reorder
good_union = morning.unionByName(afternoon_reordered)

print("unionByName on the same reordered frame:")
good_union.show()
print("→ Pickup and dropoff are correct because columns matched by name")

# COMMAND ----------

# DBTITLE 1,2b. Column mismatch error
# Same morning grain — drop dropoff, add tip_amount (missing on the other side)
full_cols = morning  # trip_id, pickup_location_id, dropoff_location_id
partial_cols = morning.select("trip_id", "pickup_location_id").withColumn(
    "tip_amount", F.lit(5.0)
)

# Default unionByName requires matching column names on both sides
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
# MAGIC When combining DataFrames from different sources or schema versions, one side
# MAGIC may have columns the other does not. Setting `allowMissingColumns=True` fills
# MAGIC the missing columns with NULL instead of raising an error.

# COMMAND ----------

# DBTITLE 1,3. allowMissingColumns demo
result = full_cols.unionByName(partial_cols, allowMissingColumns=True)

print("allowMissingColumns=True — NULLs fill columns each side is missing:")
result.show()

# COMMAND ----------

# DBTITLE 1,4. distinct after union
# MAGIC %md
# MAGIC ## 4. `distinct()` after union — removing extra copies
# MAGIC
# MAGIC `union()` keeps every row from both sides, including exact duplicates. It does
# MAGIC not deduplicate.
# MAGIC
# MAGIC Apply `distinct()` only when extra copies are **unintended** — for example,
# MAGIC overlapping source files or retry reprocessing. Do not apply it by default;
# MAGIC some workflows produce legitimate repeated rows.
# MAGIC
# MAGIC `distinct()` removes whole-row duplicates — same effect as `dropDuplicates()`
# MAGIC without arguments. Notebook 02 used `dropDuplicates` for **key-level** dedup
# MAGIC before joins — different context.

# COMMAND ----------

# DBTITLE 1,4. distinct demo — double-union morning
doubled = morning.union(morning)

print("morning rows:", morning.count())
print("After union with itself:", doubled.count())
print("After distinct():", doubled.distinct().count())
print("\n→ distinct() removed the extra copies")

# COMMAND ----------

# DBTITLE 1,Practice
# MAGIC %md
# MAGIC ## Practice — predict and verify
# MAGIC
# MAGIC Create two overlapping frames (`trip_id` only) and stack them:
# MAGIC
# MAGIC | Frame | trip_ids |
# MAGIC |---|---|
# MAGIC | `group_a` | 1, 2, 3 |
# MAGIC | `group_b` | 3, 4, 5 |
# MAGIC
# MAGIC Predict **union** count and **distinct** count before you run.
# MAGIC
# MAGIC | Step | Your prediction |
# MAGIC |---|---:|
# MAGIC | unionByName count | ? |
# MAGIC | distinct count | ? |

# COMMAND ----------

# DBTITLE 1,Practice — overlapping frames
# TODO (practice):
# 1. Create group_a: trip_ids 1, 2, 3 (column: trip_id only)
# 2. Create group_b: trip_ids 3, 4, 5 (column: trip_id only)
# 3. unionByName the two frames — does the count match your prediction?
# 4. Apply distinct() — does the count match your prediction?
#
# Hint: trip_id 3 appears in both groups.


# COMMAND ----------

# DBTITLE 1,Summary
# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC 1. **`union`** matches columns by position — fast, but silently corrupts data
# MAGIC    if column order differs between sides.
# MAGIC
# MAGIC 2. **`unionByName`** matches columns by name — safer when column order may
# MAGIC    vary.
# MAGIC
# MAGIC 3. **`allowMissingColumns=True`** fills missing columns with NULL when schemas
# MAGIC    differ between sides.
# MAGIC
# MAGIC 4. **`distinct()` after union** removes exact whole-row duplicates. Use it
# MAGIC    intentionally when extra copies are unintended, not as a default.
# MAGIC
# MAGIC **Next:** **`06 - Intersect, subtract, and exceptAll`**
