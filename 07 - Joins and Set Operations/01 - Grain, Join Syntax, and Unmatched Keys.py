# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # 01 - Grain, Join Syntax, and Unmatched Keys
# MAGIC
# MAGIC Imagine joining a rideshare trip table to a billing table that stores one row
# MAGIC per charge type — base fare, surge, and tip as three separate rows. A join on
# MAGIC `trip_id` alone turns each trip into three output rows. No error. No warning.
# MAGIC Just three times as many rows and every downstream aggregate quietly wrong.
# MAGIC
# MAGIC That kind of **silent row multiplication** is the most common source of join
# MAGIC bugs in production pipelines. It does not come from syntax mistakes — it comes
# MAGIC from not knowing the **grain** and **cardinality** of the inputs before the join
# MAGIC runs.
# MAGIC
# MAGIC This notebook gives you the vocabulary and the habit to catch it early:
# MAGIC
# MAGIC - **Grain** — what one row represents in a table
# MAGIC - **Cardinality** — how rows on the left relate to rows on the right on the join
# MAGIC   key (1:1, 1:M, M:1, M:M)
# MAGIC - **Three join-condition forms** — string, list of columns, Boolean expression
# MAGIC - **Four join types on unmatched keys** — inner, left, right, full outer
# MAGIC
# MAGIC You will not write any output tables yet. The goal is the **predict → run →
# MAGIC verify** habit: state an expected row count before running the join, then
# MAGIC confirm it with `count()`.
# MAGIC
# MAGIC **After this notebook, you will be able to:**
# MAGIC
# MAGIC - Confirm that a table is unique on a join key before joining it
# MAGIC - Use 1:1, 1:M, M:1, and M:M to predict output row counts
# MAGIC - Write a join condition as a shared column name, a list of column names, or a
# MAGIC   Boolean column expression — and choose the right form for each situation
# MAGIC - Explain why inner, left, right, and full outer joins return different row
# MAGIC   counts when the key sets do not fully overlap
# MAGIC
# MAGIC **Prerequisites.** Module 6, notebooks **`01`** through **`04`**. The landing
# MAGIC Volume must contain **`trip`** (CSV, 100 rows) and **`trip_time`** (Parquet, 100
# MAGIC rows) at the paths used below.
# MAGIC
# MAGIC **Reads:** landing **`trip`** and **`trip_time`** only. **No writes.**

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup — load landing `trip` and `trip_time`
# MAGIC
# MAGIC **`trip`** is the central fact table for the rideshare dataset; **`trip_time`**
# MAGIC extends it with the calendar date and hour of each ride. Both are joined on
# MAGIC **`trip_id`**.
# MAGIC
# MAGIC One important detail: CSV files do not carry type metadata. Without an explicit
# MAGIC schema, Spark infers **`trip_id`** as a string from the header row. That causes
# MAGIC a silent type mismatch when you later join to a table where **`trip_id`** is a
# MAGIC **`bigint`**. The DDL schemas below follow the dataset contract established in
# MAGIC Module 5 to make sure column types are correct from the start.
# MAGIC
# MAGIC Run this cell once — **`trip`** and **`trip_time`** are reused throughout the
# MAGIC notebook. You should see **100 rows** for each table.

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
# MAGIC ## 1. Grain — what one row represents
# MAGIC
# MAGIC Every table has a **grain**: the real-world entity that a single row describes.
# MAGIC For landing **`trip`**, the grain is **one completed rideshare trip**, identified
# MAGIC by **`trip_id`**. Each trip happens once and gets exactly one row.
# MAGIC
# MAGIC This matters for joins because Spark joins on key *values*, not on real-world
# MAGIC uniqueness. If the table you are joining has two rows for the same **`trip_id`**,
# MAGIC the join produces two output rows for that trip — without an error or a warning.
# MAGIC The output schema looks exactly right; only the row count reveals the problem.
# MAGIC
# MAGIC > **Production habit:** before every join, confirm that each input is unique on
# MAGIC > the join key. The check is straightforward — compare total row count to
# MAGIC > `countDistinct` on the key column. When the two numbers match, there is one row
# MAGIC > per key value and the table is safe to join without risk of silent duplication.

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
# MAGIC ## 2. Cardinality — how the two sides of a join relate
# MAGIC
# MAGIC Once you know each table's grain, **cardinality** describes the relationship
# MAGIC between them on the join key. There are four patterns, and each predicts a
# MAGIC different output row count:
# MAGIC
# MAGIC | Label | What it means | Row count effect |
# MAGIC |---|---|---|
# MAGIC | **1:1** | Each left key matches at most one right key | Same count as either input |
# MAGIC | **1:M** | One left key matches multiple right rows | Grows — each left row fans out |
# MAGIC | **M:1** | Multiple left rows match the same right row | Follows left count |
# MAGIC | **M:M** | Duplicate keys on both sides | Can multiply sharply — Notebook **`02`** |
# MAGIC
# MAGIC Landing **`trip`** ↔ **`trip_time`** on **`trip_id`** is **1:1**: every trip has
# MAGIC exactly one date-and-hour record. The two sections below first confirm that
# MAGIC on real data, then demonstrate 1:M and M:1 on small constructed frames so
# MAGIC the mechanics are visible.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Profile both tables before joining
# MAGIC
# MAGIC Run the same uniqueness check from Section 1 on both tables. When both show
# MAGIC equal row counts and distinct key counts, you have a confirmed 1:1 pair and
# MAGIC can join without fear of row multiplication.

# COMMAND ----------

for name, df in [("trip", trip), ("trip_time", trip_time)]:
    stats = df.agg(
        F.count(F.lit(1)).alias("rows"),
        F.countDistinct("trip_id").alias("distinct_trip_id"),
    ).collect()[0]
    print(f"{name}: rows={stats.rows}, distinct trip_id={stats.distinct_trip_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1:1 in action — join `trip` and `trip_time`
# MAGIC
# MAGIC When both tables use the **same column name** for the join key, the idiomatic
# MAGIC PySpark form is to pass the name as a **string** — for example, `"trip_id"`.
# MAGIC Spark performs an equi-join and **coalesces** the two key columns into one in
# MAGIC the output. You get a single **`trip_id`** column, not two side-by-side copies.
# MAGIC That coalescing behavior is unique to the string (and list) form; Section 3
# MAGIC shows what happens when you use the Boolean form instead.
# MAGIC
# MAGIC On 1:1 data with 100 rows on each side, an inner join on a fully matching key
# MAGIC should return **100 rows** — the same count as either input. Verify that,
# MAGIC then inspect the columns to confirm the single coalesced **`trip_id`**.

# COMMAND ----------

join_string = trip.join(trip_time, "trip_id", "inner")
print("Columns after string join on trip_id:", join_string.columns)
print("Row count:", join_string.count())
join_string.select("trip_id", "trip_date", "hour_of_day").show(3, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1:M — one key matches multiple rows on the other side
# MAGIC
# MAGIC Real billing systems often store charges in long format — one row per charge
# MAGIC type (base fare, surge, tip) rather than one row per trip. **`trip_summary`**
# MAGIC below represents the trip-level view (one row per **`trip_id`**) and
# MAGIC **`trip_charges`** represents the charge-level view (up to three rows per
# MAGIC **`trip_id`**). This mirrors how a production payment pipeline might separate
# MAGIC aggregated totals from itemised charge records.
# MAGIC
# MAGIC Joining **`trip_summary`** to **`trip_charges`** on **`trip_id` only** is a
# MAGIC **1:M** join from the summary side. Each summary row fans out to match every
# MAGIC charge row that shares its key. With 2 trips × 3 charges each, predict **6**
# MAGIC output rows.

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

predicted_trip_id_only = 6
single_key = trip_summary.join(trip_charges, "trip_id", "inner")
actual_trip_id_only = single_key.count()
print(
    f"1:M — trip_id only: predicted={predicted_trip_id_only}, "
    f"actual={actual_trip_id_only}"
)
single_key.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Composite key — join on a list of column names
# MAGIC
# MAGIC The 1:M join above returns 6 rows because it only matches on **`trip_id`**,
# MAGIC ignoring **`charge_type`**. If you want to join **`trip_charges`** to a
# MAGIC **`rate_card`** table that stores the expected amount for each
# MAGIC **(trip, charge_type) pair**, you need to match on **both columns**.
# MAGIC
# MAGIC Pass a **Python list** as the join condition to join on multiple columns at once.
# MAGIC Spark requires every column in the list to match — it is the same as writing
# MAGIC `trip_id = trip_id AND charge_type = charge_type` in SQL. The **`rate_card`**
# MAGIC below covers only 4 of the 6 charge rows (base fare and surge, no tip), so
# MAGIC predict **4** output rows.

# COMMAND ----------

rate_card = spark.createDataFrame(  # noqa: F821
    [
        (1, "base_fare", 8.00),
        (1, "surge", 3.00),
        (2, "base_fare", 18.00),
        (2, "surge", 5.00),
    ],
    ["trip_id", "charge_type", "expected_amount"],
)

predicted_composite = 4
composite_key = trip_charges.join(rate_card, ["trip_id", "charge_type"], "inner")
actual_composite = composite_key.count()
print(
    f"Composite [trip_id, charge_type]: predicted={predicted_composite}, "
    f"actual={actual_composite}"
)
composite_key.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ### M:1 — many left rows match the same right row
# MAGIC
# MAGIC **M:1** is the mirror of **1:M** — the same join logic, but with the tables
# MAGIC swapped. Put **`trip_charges`** on the left and **`trip_summary`** on the right,
# MAGIC still joining on **`trip_id` only**. Each charge row matches exactly one summary
# MAGIC row, so the output has one row per charge. The row count follows the **left**
# MAGIC side — predict **6** again, one per charge line.
# MAGIC
# MAGIC The labels 1:M and M:1 do not change the row count arithmetic here; they change
# MAGIC *which side is the "many"*. In practice, the label you use depends on which table
# MAGIC is the driving table in your pipeline.

# COMMAND ----------

predicted_m1 = 6
m1_join = trip_charges.join(trip_summary, "trip_id", "inner")
actual_m1 = m1_join.count()
print(
    f"M:1 — charges → summary on trip_id: predicted={predicted_m1}, "
    f"actual={actual_m1}"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Join conditions — three syntactic forms
# MAGIC
# MAGIC You have already used two of the three forms above. Here is the full picture:
# MAGIC
# MAGIC | Form | Example | When to use |
# MAGIC |---|---|---|
# MAGIC | **String** | `"trip_id"` | Same name on both sides; key coalesces |
# MAGIC | **List** | `["trip_id", "charge_type"]` | Composite key; same names both sides |
# MAGIC | **Boolean** | `F.col("l.id") == F.col("r.loc_id")` | Names differ, or aliases needed |
# MAGIC
# MAGIC The **Boolean** form is introduced below. Notebook **`03`** uses it for the
# MAGIC zone lookup, where **`trip.pickup_location_id`** and
# MAGIC **`trip.dropoff_location_id`** join to **`zone_lookup.location_id`** — the
# MAGIC column names are different on each side, so string and list forms are not an
# MAGIC option.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Boolean condition — when column names differ
# MAGIC
# MAGIC The string and list forms work only when the join key has the **same name** on
# MAGIC both sides. When names differ — as they do in many dimension-table lookups — you
# MAGIC need to express the join as an explicit Boolean Column expression:
# MAGIC
# MAGIC ```
# MAGIC left.alias("l").join(right.alias("r"), F.col("l.key") == F.col("r.other_key"), "inner")
# MAGIC ```
# MAGIC
# MAGIC Two things to note:
# MAGIC
# MAGIC 1. **Alias each DataFrame** before the join. Once both sides share a column
# MAGIC    called, say, `trip_id`, Spark cannot resolve `F.col("trip_id")` unambiguously
# MAGIC    without an alias prefix.
# MAGIC 2. **Both key columns appear in the output.** Unlike the string form, a Boolean
# MAGIC    join does not coalesce the key columns — you get `trip_id` from the left *and*
# MAGIC    `trip_no` from the right. Use `select` or `drop` to tidy the result.
# MAGIC
# MAGIC The small frame below uses `trip_id` on the left and `trip_no` on the right to
# MAGIC show the mechanics. Only key `1` matches — key `2` has no partner on the right,
# MAGIC and key `3` has no partner on the left — so predict **1** output row from an
# MAGIC inner join.

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
print("Inner join on trip_id = trip_no:")
join_diff_names.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Boolean condition on same-named columns — both copies kept
# MAGIC
# MAGIC You can write a Boolean condition even when both sides use the same column name.
# MAGIC Spark allows it, but the behavior is different from the string form: **both key
# MAGIC columns appear in the output**. The code below joins **`trip`** and
# MAGIC **`trip_time`** using a Boolean expression and selects `t.trip_id` and
# MAGIC `tt.trip_id` separately to make that visible.
# MAGIC
# MAGIC This is important context for Notebook **`03`** (zone lookup with aliases), but
# MAGIC the practical rule is: use the **string form** when column names match. It
# MAGIC produces cleaner output with one less column to manage.

# COMMAND ----------

join_bool_raw = trip.alias("t").join(
    trip_time.alias("tt"),
    F.col("t.trip_id") == F.col("tt.trip_id"),
    "inner",
)
print("Column names after Boolean join (note two trip_id columns):")
print(join_bool_raw.columns)
join_bool_raw.select(
    F.col("t.trip_id"),
    F.col("tt.trip_id"),
    F.col("tt.trip_date"),
).show(3, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. What happens when keys do not fully overlap
# MAGIC
# MAGIC So far, both sides of each join shared the same key values. In production,
# MAGIC that rarely happens — there are often rows on one side with no partner on the
# MAGIC other. The join **type** determines what happens to those unmatched rows.
# MAGIC
# MAGIC The four join types and what they do with unmatched rows:
# MAGIC
# MAGIC | Join type | Keeps unmatched left rows? | Keeps unmatched right rows? |
# MAGIC |---|:---:|:---:|
# MAGIC | **inner** | No | No |
# MAGIC | **left** | Yes (NULLs for right columns) | No |
# MAGIC | **right** | No | Yes (NULLs for left columns) |
# MAGIC | **full outer** | Yes (NULLs for right columns) | Yes (NULLs for left columns) |
# MAGIC
# MAGIC The frame below has:
# MAGIC
# MAGIC - Left **`trip_id`**: `[1, 2, 3, 4, 5]`
# MAGIC - Right **`trip_id`**: `[3, 4, 5, 6, 7]`
# MAGIC - Overlap: `{3, 4, 5}` — three keys present on both sides
# MAGIC - Left-only: `{1, 2}` — two keys with no right partner
# MAGIC - Right-only: `{6, 7}` — two keys with no left partner
# MAGIC
# MAGIC Apply the table above to predict each join's row count before running the cell:
# MAGIC
# MAGIC | Join type | Predicted rows | Reasoning |
# MAGIC |---|---:|---|
# MAGIC | inner | 3 | Only the 3 overlapping keys survive |
# MAGIC | left | 5 | All 5 left rows kept; `{1, 2}` get NULLs for right columns |
# MAGIC | right | 5 | All 5 right rows kept; `{6, 7}` get NULLs for left columns |
# MAGIC | full outer | 7 | Both sides kept; 3 overlap rows merge — 2 + 3 + 2 = 7 |
# MAGIC
# MAGIC Spark accepts both **`"full"`** and **`"full_outer"`** as aliases for the same
# MAGIC full-outer-join behavior.

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
# MAGIC Apply the same reasoning to a slightly different key setup. The mini-frames
# MAGIC below use:
# MAGIC
# MAGIC - Left **`trip_id`**: `[1, 2, 3, 4]`
# MAGIC - Right **`trip_id`**: `[2, 3, 4, 5]`
# MAGIC - Overlap: `{2, 3, 4}`
# MAGIC
# MAGIC Before running the cell:
# MAGIC
# MAGIC 1. Use the join-type table from Section 4 to reason through the expected counts
# MAGIC    for an **inner** join and a **right** join on **`trip_id`**.
# MAGIC 2. Set **`predicted_inner_exercise`** and **`predicted_right_exercise`** to your
# MAGIC    answers.
# MAGIC 3. Run the cell. If your predictions are off, re-read the join-type table and
# MAGIC    check which side's unmatched rows survive each type.
# MAGIC
# MAGIC This notebook is skill-building only — no table writes in this cell.

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
# MAGIC **Grain** is what one row represents. Confirm it with a `count` vs
# MAGIC `countDistinct` check before every join — a mismatch means the join will
# MAGIC silently multiply rows without raising an error.
# MAGIC
# MAGIC **Cardinality** (1:1, 1:M, M:1, M:M) tells you what to expect from the output
# MAGIC row count. Landing `trip` ↔ `trip_time` is 1:1: safe to inner-join with no
# MAGIC fanout. The constructed `trip_summary` ↔ `trip_charges` example showed 1:M
# MAGIC and M:1 in action. M:M — where both sides have duplicate keys — is in
# MAGIC Notebook **`02`**.
# MAGIC
# MAGIC **Join condition syntax:** use a **string** when the key column has the same
# MAGIC name on both sides (Spark coalesces the key into one output column); use a
# MAGIC **list** for composite keys with matching names; use a **Boolean** expression
# MAGIC when the column names differ (as in the zone lookup in Notebook **`03`**) or
# MAGIC when you need explicit aliases.
# MAGIC
# MAGIC **Unmatched keys** produce different results depending on join type. Inner keeps
# MAGIC only matched rows; left and right keep all rows from the driving side and fill
# MAGIC the other with NULLs; full outer keeps everything. Predict the count before
# MAGIC running — if the actual count surprises you, the grain or cardinality
# MAGIC assumption was wrong.
# MAGIC
# MAGIC **Next:** **`02 - Join Types, NULL Keys, and Validation`** — apply the same
# MAGIC habits to the full 100-row landing tables, explore NULL join-key behaviour, and
# MAGIC practice key profiling before joining.
