# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC
# MAGIC # 01 - Grain, Join Syntax, and Unmatched Keys
# MAGIC
# MAGIC ## The problem: wrong joins cost more than syntax errors
# MAGIC
# MAGIC A syntax error stops your code immediately — you fix it and move on. A wrong
# MAGIC join decision **silently produces wrong data** that passes all downstream code
# MAGIC without a single error. You only discover it when a report is wrong or a
# MAGIC stakeholder notices impossible numbers.
# MAGIC
# MAGIC Consider two tables joined on **`trip_id`**:
# MAGIC
# MAGIC | trip_id | service_type |       | trip_id | charge_type | amount |
# MAGIC |---|---|---|---|---|---|
# MAGIC | 1 | Standard |  | 1 | base_fare | 8.00 |
# MAGIC | 2 | Premium |  | 1 | surge | 3.00 |
# MAGIC |  |  |  | 1 | tip | 1.50 |
# MAGIC |  |  |  | 2 | base_fare | 18.00 |
# MAGIC |  |  |  | 2 | surge | 5.00 |
# MAGIC |  |  |  | 2 | tip | 2.00 |
# MAGIC
# MAGIC Join on `trip_id` → **6 rows** (not 2). No error. No warning. Your
# MAGIC `sum(amount)` is now **3x too high** and nothing in your pipeline will tell you.
# MAGIC
# MAGIC Why? The left table has **1 row per trip**, the right has **3 rows per trip**.
# MAGIC Spark doesn't care — it matched every left row to every right row with the same
# MAGIC key. That's a **1:M fanout**, and it's the most expensive mistake in data
# MAGIC engineering because it's invisible until the damage is done.
# MAGIC
# MAGIC ## What this notebook teaches
# MAGIC
# MAGIC | Section | Concept | Why it matters |
# MAGIC |---|---|---|
# MAGIC | 1. Grain | What one row represents | Detect duplicates before joining |
# MAGIC | 2. Cardinality | 1:1, 1:M, M:1, M:M labels | Predict output row count |
# MAGIC | 3. Join syntax | String, List, Boolean forms | Write correct PySpark join conditions |
# MAGIC | 4. Unmatched keys | inner/left/right/full behavior | Control which rows survive |
# MAGIC
# MAGIC **Core habit:** predict row count → run the join → verify with `count()`.
# MAGIC
# MAGIC **Reads:** landing `trip` and `trip_time` (100 rows each). **No writes.**
# MAGIC
# MAGIC **Prerequisites:** Module 6 notebooks 01–04; landing Volume with `trip` (CSV)
# MAGIC and `trip_time` (Parquet).

# COMMAND ----------

# DBTITLE 1,Setup
# MAGIC %md
# MAGIC ## Setup — load landing `trip` and `trip_time`
# MAGIC
# MAGIC | Table | Format | Grain | Key column | Rows |
# MAGIC |---|---|---|---|---|
# MAGIC | **`trip`** | CSV | One rideshare trip | `trip_id` (bigint) | 100 |
# MAGIC | **`trip_time`** | Parquet | Date/hour per trip | `trip_id` (bigint) | 100 |
# MAGIC
# MAGIC **Why explicit schemas?** CSV has no type metadata. Without a schema, Spark
# MAGIC infers `trip_id` as a *string*. Later joins against Parquet (where `trip_id` is
# MAGIC `bigint`) would silently return 0 rows — types don't match, so nothing joins.
# MAGIC The DDL schemas below force correct types from the start.

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

# DBTITLE 1,Section 1 - Grain
# MAGIC %md
# MAGIC ## 1. Grain — know your data before you join it
# MAGIC
# MAGIC If you don't know what one row represents, you can't predict what a join will
# MAGIC do. **Grain** answers the only question that matters before joining:
# MAGIC *"What real-world thing does one row describe?"*
# MAGIC
# MAGIC | Table | Grain statement | Key |
# MAGIC |---|---|---|
# MAGIC | `trip` | One completed rideshare trip | `trip_id` |
# MAGIC | `trip_time` | One time record per trip | `trip_id` |
# MAGIC
# MAGIC **The one check that prevents most join bugs:**
# MAGIC
# MAGIC ```
# MAGIC row_count = total rows in the table
# MAGIC distinct_key = number of unique trip_id values
# MAGIC
# MAGIC row_count == distinct_key → safe to join (one row per key)
# MAGIC row_count >  distinct_key → STOP. Duplicates will multiply your rows.
# MAGIC ```
# MAGIC
# MAGIC This takes 5 seconds to run and saves hours of debugging wrong aggregations.
# MAGIC The next cell demonstrates it.

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

# DBTITLE 1,Section 2 - Cardinality vocabulary
# MAGIC %md
# MAGIC ## 2. Cardinality — predict the damage before it happens
# MAGIC
# MAGIC Grain tells you what one row is. **Cardinality** tells you what will happen
# MAGIC when two tables meet on a join key:
# MAGIC
# MAGIC | Label | What it means | Row-count prediction |
# MAGIC |---|---|---|
# MAGIC | **1:1** | Each left key matches at most one right key | Output ≈ input count |
# MAGIC | **1:M** | One left key matches multiple right rows | Output grows (fanout) |
# MAGIC | **M:1** | Multiple left rows match one right row | Output follows left count |
# MAGIC | **M:M** | Duplicates on both sides | Output can multiply sharply |
# MAGIC
# MAGIC Landing **`trip`** ↔ **`trip_time`** on **`trip_id`** is **1:1** (confirmed by
# MAGIC the grain check above). The 1:M pattern is demonstrated in Section 3 as
# MAGIC motivation for composite keys. M:M is covered in Notebook **`02`**.
# MAGIC
# MAGIC You don't need to memorize this table. The point is simple: **if you know the
# MAGIC grain of both sides, you already know what the join will do.** No surprises.

# COMMAND ----------

# DBTITLE 1,Profile both tables
# MAGIC %md
# MAGIC ### Verify both sides — not just one
# MAGIC
# MAGIC Cell 6 confirmed `trip` is unique. That's half the story. If `trip_time` has
# MAGIC duplicates, the join still multiplies rows. **Both sides must pass the grain
# MAGIC check.** One clean table joined to one dirty table = dirty output.

# COMMAND ----------

for name, df in [("trip", trip), ("trip_time", trip_time)]:
    stats = df.agg(
        F.count(F.lit(1)).alias("rows"),
        F.countDistinct("trip_id").alias("distinct_trip_id"),
    ).collect()[0]
    print(f"{name}: rows={stats.rows}, distinct trip_id={stats.distinct_trip_id}")

# COMMAND ----------

# DBTITLE 1,Section 3 - Join syntax
# MAGIC %md
# MAGIC ## 3. Join-condition syntax — three ways to say "match these keys"
# MAGIC
# MAGIC Grain and cardinality tell you *whether* to join. Now: *how* to write it.
# MAGIC
# MAGIC PySpark gives you three syntactic forms for equi-joins (key on left = key on
# MAGIC right):
# MAGIC
# MAGIC | # | Form | Syntax | Output key columns | Use when |
# MAGIC |---|---|---|---|---|
# MAGIC | 1 | **String** | `"trip_id"` | **1 column** (merged) | Same name, single key |
# MAGIC | 2 | **List** | `["trip_id", "charge_type"]` | **1 per key** (merged) | Same names, multiple keys |
# MAGIC | 3 | **Boolean** | `F.col("l.key") == F.col("r.other")` | **2 columns** (both kept) | Names differ |
# MAGIC
# MAGIC **The difference that bites you:** String/List automatically merge the key
# MAGIC columns into one clean output column. Boolean keeps both copies — which gives
# MAGIC you duplicate column names and ambiguous references that break downstream code.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 3.1 String form — single shared column name
# MAGIC
# MAGIC ```python
# MAGIC left.join(right, "trip_id", "inner")
# MAGIC ```
# MAGIC
# MAGIC **What happens:**
# MAGIC - Spark finds `trip_id` on both sides, matches equal values
# MAGIC - **Merges** the two `trip_id` columns into one in the output (called "coalescing")
# MAGIC - Result has cleaner schema — no duplicate columns
# MAGIC
# MAGIC **Predict:** `trip` (100 rows) joined to `trip_time` (100 rows), both unique on
# MAGIC `trip_id`, all keys match → expect **100** output rows.

# COMMAND ----------

join_string = trip.join(trip_time, "trip_id", "inner")
print("Columns after string join on trip_id:", join_string.columns)
print("Row count:", join_string.count())
join_string.select("trip_id", "trip_date", "hour_of_day").show(3, truncate=False)

# COMMAND ----------

# DBTITLE 1,3.2 List form
# MAGIC %md
# MAGIC ### 3.2 List form — composite equi-join
# MAGIC
# MAGIC ```python
# MAGIC left.join(right, ["trip_id", "charge_type"], "inner")
# MAGIC ```
# MAGIC
# MAGIC **What happens:**
# MAGIC - Spark requires **ALL** columns in the list to match (like SQL `AND`)
# MAGIC - Still merges key columns (same as string form, just multiple columns)
# MAGIC
# MAGIC **Why this exists:** joining on too few columns is one of the most common
# MAGIC join mistakes. You think you're matching precisely, but you're matching too
# MAGIC broadly.
# MAGIC
# MAGIC Example: `trip_summary` (2 rows) joined to `trip_charges` (6 rows) on
# MAGIC `trip_id` alone:
# MAGIC - Trip 1 matches **all 3** charge rows → 3 output rows for 1 input row
# MAGIC - Trip 2 matches **all 3** charge rows → 3 output rows for 1 input row
# MAGIC - Result: **6 rows** — you just tripled your data without realizing it
# MAGIC
# MAGIC Fix: add `charge_type` to the key. Now each row matches **exactly one** row
# MAGIC on the other side. `rate_card` has no tip entries (4 rows), so predict **4**.
# MAGIC
# MAGIC The next two cells demonstrate: first the mistake, then the fix.

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

# DBTITLE 1,Composite key fix
# MAGIC %md
# MAGIC **Now fix it — add `charge_type` to the key.**
# MAGIC
# MAGIC `rate_card` stores expected amounts for base_fare and surge only (no tip):
# MAGIC
# MAGIC - `trip_charges`: 6 rows (3 charge types × 2 trips)
# MAGIC - `rate_card`: 4 rows (2 charge types × 2 trips — tip doesn't exist here)
# MAGIC - Composite join: match only where BOTH columns align
# MAGIC - Tip rows? No match in `rate_card` → inner join drops them
# MAGIC - **Predict: 4 rows** (not 6 — the composite key eliminated the fanout)

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

# DBTITLE 1,3.3 Boolean form
# MAGIC %md
# MAGIC ### 3.3 Boolean form — when column names differ
# MAGIC
# MAGIC ```python
# MAGIC left.alias("l").join(
# MAGIC     right.alias("r"),
# MAGIC     F.col("l.trip_id") == F.col("r.trip_no"),
# MAGIC     "inner",
# MAGIC )
# MAGIC ```
# MAGIC
# MAGIC **When you're forced to use this:** the key column has a **different name** on
# MAGIC each side. Your fact table says `trip_id`, the staging file says `trip_no`.
# MAGIC String/list forms won't work — they need the exact same name on both sides.
# MAGIC Boolean is your only option.
# MAGIC
# MAGIC **Two critical behaviors:**
# MAGIC
# MAGIC | Behavior | Why | What to do |
# MAGIC |---|---|---|
# MAGIC | Must **alias** both DataFrames | Otherwise `F.col("trip_id")` is ambiguous | Use `.alias("l")` / `.alias("r")` |
# MAGIC | **Both** key columns appear in output | Boolean form never merges columns | Use `.select()` or `.drop()` to clean up |
# MAGIC
# MAGIC **Example below:** left has `trip_id` = [1, 2], right has `trip_no` = [1, 3].
# MAGIC Only key `1` exists on both sides → **predict 1 output row**.

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

# DBTITLE 1,Boolean same names
# MAGIC %md
# MAGIC ### Common mistake: Boolean form when names already match
# MAGIC
# MAGIC You *can* do it — but you're creating a problem for yourself:
# MAGIC
# MAGIC ```python
# MAGIC # String form result: ['trip_id', 'trip_date', ...]      ← clean, one trip_id
# MAGIC # Boolean form result: ['trip_id', 'trip_date', ..., 'trip_id']  ← broken, two trip_id
# MAGIC ```
# MAGIC
# MAGIC Now every `.select("trip_id")` downstream throws an **ambiguous column error**.
# MAGIC You're forced to prefix everything with aliases: `F.col("t.trip_id")`.
# MAGIC
# MAGIC **Don't make extra work for yourself.** Use string form when names match.
# MAGIC Boolean is for when you have no choice (names differ). The cell below shows
# MAGIC exactly what the duplicate-column problem looks like.

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

# DBTITLE 1,Section 4 - Unmatched keys
# MAGIC %md
# MAGIC ## 4. Unmatched keys — the other join mistake
# MAGIC
# MAGIC The first mistake is joining on the wrong grain (Section 1). The second is
# MAGIC choosing the wrong join type when keys don't fully overlap — you either lose
# MAGIC rows you needed or keep rows you shouldn't have.
# MAGIC
# MAGIC Production data almost never has perfect key overlap. The **join type** is your
# MAGIC decision about what to do with the mismatches:
# MAGIC
# MAGIC - **inner** → "I only want rows that exist on BOTH sides. Drop the rest."
# MAGIC - **left** → "I need every left row. If right has no match, fill with NULLs."
# MAGIC - **right** → "I need every right row. If left has no match, fill with NULLs."
# MAGIC - **full outer** → "Give me everything. NULLs wherever there's no partner."
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Test data:**
# MAGIC
# MAGIC ```
# MAGIC Left  trip_id: [1, 2, 3, 4, 5]
# MAGIC Right trip_id: [3, 4, 5, 6, 7]
# MAGIC
# MAGIC Left-only:  {1, 2}     ← no right partner
# MAGIC Overlap:    {3, 4, 5}  ← present on BOTH sides
# MAGIC Right-only: {6, 7}     ← no left partner
# MAGIC ```
# MAGIC
# MAGIC **Now predict — this is the habit that saves you:**
# MAGIC
# MAGIC | Join type | What survives | Count |
# MAGIC |---|---|---:|
# MAGIC | inner | Only the 3 overlapping keys | 3 |
# MAGIC | left | All 5 left rows (2 get NULLs for right columns) | 5 |
# MAGIC | right | All 5 right rows (2 get NULLs for left columns) | 5 |
# MAGIC | full outer | Everything: 2 + 3 + 2 | 7 |
# MAGIC
# MAGIC If you can't predict the count before running, you don't understand the join
# MAGIC well enough to trust its output. The next cell verifies all four.

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

# DBTITLE 1,Section 5 - Exercise
# MAGIC %md
# MAGIC ## 5. Exercise — prove you understand it
# MAGIC
# MAGIC **Your data:**
# MAGIC
# MAGIC ```
# MAGIC Left  trip_id: [1, 2, 3, 4]
# MAGIC Right trip_id: [2, 3, 4, 5]
# MAGIC ```
# MAGIC
# MAGIC **Before you run:** work out the overlap yourself, then predict:
# MAGIC
# MAGIC 1. How many rows does an **inner** join produce?
# MAGIC 2. How many rows does a **right** join produce?
# MAGIC
# MAGIC Replace `None` in the next cell with your answers, then run. If you get it
# MAGIC wrong, you didn't internalize Section 4 — go back and re-read the mental model.

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

# DBTITLE 1,Summary
# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC | Concept | Key takeaway |
# MAGIC |---|---|
# MAGIC | **Grain** | `count(*)` == `countDistinct(key)` → safe to join. Mismatch = silent row multiplication. |
# MAGIC | **Cardinality** | 1:1, 1:M, M:1, M:M — grain determines cardinality, cardinality predicts row count. |
# MAGIC | **String join** | `"trip_id"` — same name both sides, key column merged into one. |
# MAGIC | **List join** | `["trip_id", "charge_type"]` — composite key, all columns must match. |
# MAGIC | **Boolean join** | `F.col("l.key") == F.col("r.other")` — names differ, both key columns kept. |
# MAGIC | **Unmatched keys** | inner = overlap only; left/right = one side fully kept; full = everything. |
# MAGIC
# MAGIC **The habit that prevents 90% of join bugs:** predict the row count BEFORE
# MAGIC you run. If actual ≠ predicted, something is wrong with your understanding
# MAGIC of the data — fix that before you build anything on top of it.
# MAGIC
# MAGIC **Next:** **`02 - Join Types, NULL Keys, and Validation`** — four join types
# MAGIC on real landing data, NULL key behavior, and key profiling before production
# MAGIC joins.