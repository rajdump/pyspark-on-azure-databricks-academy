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

# DBTITLE 1,Cell 5
# MAGIC %md
# MAGIC ## Grain orientation
# MAGIC
# MAGIC
# MAGIC **Grain** refers to what one row represents. For **`trip`**, each row stands for **one `trip_id`**. If the number of rows matches the number of unique **`trip_id`** entries, then the data is unique for that key.
# MAGIC
# MAGIC **To check this programmatically:**
# MAGIC
# MAGIC 1. Count the total number of rows using `F.count(F.lit(1))`.
# MAGIC 2. Count the unique **`trip_id`** values with `F.countDistinct("trip_id")`.
# MAGIC 3. Compare the two counts: if they are equal, the key is unique (no duplicates).
# MAGIC
# MAGIC The next step runs this check on **`trip`**. If the counts match, we can confidently say: **one row per trip — grain confirmed.**

# COMMAND ----------

trip_grain = trip.agg(
    F.count(F.lit(1)).alias("row_count"),
    F.countDistinct("trip_id").alias("distinct_trip_id"),
).collect()[0] ##return first element from the list 
##Row(row_count=100, distinct_trip_id=100)]

print(
    f"Total: {trip_grain.row_count} rows in Trip Dataset, "
    f"{trip_grain.distinct_trip_id} distinct trip_id values"
)
print(
    "Grain check:",
    "one row per trip_id"
    if trip_grain.row_count == trip_grain.distinct_trip_id
    else "NOT unique on trip_id",
)

# COMMAND ----------

# DBTITLE 1,Cell 7
# MAGIC %md
# MAGIC ## Cardinality vocabulary
# MAGIC
# MAGIC **Cardinality** describes how many rows on the left match how many rows on the
# MAGIC right for a given join key. Once you know the grain of each table, you can
# MAGIC label the join relationship:
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
# MAGIC
# MAGIC The next cell verifies **both** tables in a loop, confirming the 1:1 label
# MAGIC is safe before any join.

# COMMAND ----------

for name, df in [("trip", trip), ("trip_time", trip_time)]:
    stats = df.agg(
        F.count(F.lit(1)).alias("rows"),
        F.countDistinct("trip_id").alias("distinct_trip_id"),
    ).collect()[0]
    print(f"{name}: rows={stats.rows}, distinct trip_id={stats.distinct_trip_id}")

# COMMAND ----------

# DBTITLE 1,Cell 9
# MAGIC %md
# MAGIC ## Understand Join-condition syntax
# MAGIC
# MAGIC PySpark provides three ways to express that equality condition:
# MAGIC
# MAGIC | Form | Syntax | When to use |
# MAGIC |---|---|---|
# MAGIC | **String** | `"trip_id"` | Same join column name on both sides |
# MAGIC | **List** | `["trip_id", "leg_id"]` | Multiple join column names (composite key) |
# MAGIC | **Boolean** | `F.col("l.key") == F.col("r.key")` | join column names differ, or you need full control |
# MAGIC
# MAGIC Notebook **`03`** needs the **Boolean** form because the zone lookup table uses
# MAGIC a different column name than the trip table (`location_id` vs `zone_id`).
# MAGIC
# MAGIC The following subsections demonstrate each form with working examples.

# COMMAND ----------

# DBTITLE 1,Cell 10
# MAGIC %md
# MAGIC ### Same join column name on both sides
# MAGIC
# MAGIC
# MAGIC
# MAGIC ```python
# MAGIC df_left.join(df_right, "trip_id", "inner")
# MAGIC ```
# MAGIC
# MAGIC **Key behavior:** because both tables have a column named `trip_id`, Spark
# MAGIC automatically matches them and keeps only **one** copy of the key column in
# MAGIC the output. This is the simplest and cleanest join syntax when column names
# MAGIC already align.
# MAGIC
# MAGIC The next cell joins **`trip`** ↔ **`trip_time`** this way and prints the
# MAGIC resulting columns and row count.

# COMMAND ----------

join_string = trip.join(trip_time, "trip_id", "inner")
print("Columns after string join on trip_id:", join_string.columns)
print("Row count:", join_string.count())
join_string.select("*").show(1, truncate=False,vertical=True)

# COMMAND ----------

# DBTITLE 1,Cell 12
# MAGIC %md
# MAGIC ###  Multiple join column names (composite key)
# MAGIC
# MAGIC Pass a **list of column names** when the relationship requires more than one key.
# MAGIC
# MAGIC ```python
# MAGIC df_left.join(df_right, ["trip_id", "leg_id"], "inner")
# MAGIC ```
# MAGIC
# MAGIC **Why composite keys matter:** sometimes a single column is not enough to
# MAGIC uniquely identify a match. For example, a trip with multiple legs needs both
# MAGIC `trip_id` AND `leg_id` to pinpoint the exact row.
# MAGIC
# MAGIC The next cell demonstrates the difference:
# MAGIC - Joining on `trip_id` alone → more rows (matches across different legs)
# MAGIC - Joining on `[trip_id, leg_id]` → fewer, precise rows (exact leg match)

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

# DBTITLE 1,Cell 14
# MAGIC %md
# MAGIC ### Boolean: explicit column condition
# MAGIC
# MAGIC Join keys **do not** have to share a column name. The string and list forms
# MAGIC only work when **both sides use the same name(s)**. When names differ — e.g.
# MAGIC **`trip_id`** on the fact table and **`trip_no`** on a staging file — use a
# MAGIC **Boolean** expression:
# MAGIC
# MAGIC ```python
# MAGIC left.alias("l").join(
# MAGIC     right.alias("r"),
# MAGIC     F.col("l.trip_id") == F.col("r.trip_no"),
# MAGIC     "inner",
# MAGIC )
# MAGIC ```
# MAGIC
# MAGIC **Key differences from string/list form:**
# MAGIC - You **must** alias both DataFrames (`alias("l")`, `alias("r")`) to
# MAGIC   disambiguate columns
# MAGIC - Spark keeps **both** key columns in the output (no auto-coalescing)
# MAGIC - This is the **only** syntax that works when column names differ across tables
# MAGIC
# MAGIC When names **match**, Boolean joins still keep **both** key columns unless you
# MAGIC **`select`** away one; Notebook **`04`** uses aliases for pickup/dropoff zone lookup.
# MAGIC
# MAGIC The next cell joins `trip_id` (left) to `trip_no` (right) — impossible with
# MAGIC the string form.

# COMMAND ----------

left_id = spark.createDataFrame(  # noqa: F821
    [(1, "a"), (2, "b")],
    ["trip_id", "note"],
)
right_no = spark.createDataFrame(
    [(1, 10.0), (3, 30.0)],
    ["trip_no", "score"],
)

join_diff_names = left_id.alias("l").join(
    right_no.alias("r"),
    F.col("l.trip_id") == F.col("r.trip_no"),
    "inner",
)

print("Different key names — Boolean join only (string 'trip_id' would not apply):")
join_diff_names.show()

# COMMAND ----------

# DBTITLE 1,Cell 16
# MAGIC %md
# MAGIC **Same name on both sides — the duplicate-column trap:**
# MAGIC
# MAGIC When both tables have `trip_id` and you use the Boolean form
# MAGIC (`t.trip_id == tt.trip_id`), Spark does **not** merge the key columns. You get
# MAGIC **two** `trip_id` columns in the result. You must use the alias prefix
# MAGIC (`t.trip_id` or `tt.trip_id`) in any subsequent `select` to avoid ambiguity.
# MAGIC
# MAGIC The next cell demonstrates this behavior with **`trip`** ↔ **`trip_time`**:

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

# DBTITLE 1,Cell 18
# MAGIC %md
# MAGIC ## Constructed frame — unmatched keys
# MAGIC
# MAGIC When keys do **not** fully overlap, different join types produce different row
# MAGIC counts. This section builds two small DataFrames with **partial key overlap**
# MAGIC to make the effect visible.
# MAGIC
# MAGIC Left **`trip_id`** `[1, 2, 3, 4, 5]`, right `[3, 4, 5, 6, 7]`.
# MAGIC
# MAGIC Overlap: `{3, 4, 5}` (3 keys match). Left-only: `{1, 2}`. Right-only: `{6, 7}`.
# MAGIC
# MAGIC | Join type | Logic | Predicted rows |
# MAGIC |---|---|---:|
# MAGIC | **inner** | Only matching keys | 3 |
# MAGIC | **left** | All left rows + matches from right (NULLs for 1, 2) | 5 |
# MAGIC | **right** | All right rows + matches from left (NULLs for 6, 7) | 5 |
# MAGIC | **full outer** | All rows from both sides (NULLs where no match) | 7 |
# MAGIC
# MAGIC The next cell creates the frames, predicts the counts, runs each join, and
# MAGIC verifies predictions match actuals. This is the **predict-then-verify** habit
# MAGIC that prevents silent row count errors in production joins.

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
# MAGIC - **Boolean** joins express **`trip_id` = `trip_no`** and other mismatched key names;
# MAGIC   string/list forms require the same name on both sides.
# MAGIC - **Unmatched keys** make inner / left / right / full outer row counts diverge.
# MAGIC
# MAGIC **Next:** Module 7 **`02 - Join Types, NULL Keys, and Validation`** — landing
# MAGIC 1:1 joins, many-to-many and NULL-key frames, key profiling, and the predict habit.
