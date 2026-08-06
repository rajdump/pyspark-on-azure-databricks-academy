# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC
# MAGIC # 01 - GroupBy and Basic Aggregations
# MAGIC
# MAGIC ## Two traps every data engineer faces in aggregations
# MAGIC
# MAGIC ### Trap 1: Spark skips NULLs silently
# MAGIC Your stakeholder asks for the **average tip per trip** across 106 trips:
# MAGIC
# MAGIC ```python
# MAGIC trip_enriched.agg(F.avg("tip_amount")).show()
# MAGIC ```
# MAGIC
# MAGIC - **Spark calculates:** `2.955673` ($307.39 total ÷ **104** known tips)
# MAGIC - **Business asks for:** `2.899906` ($307.39 total ÷ **106** total trips)
# MAGIC
# MAGIC Because 2 trips have `NULL` tips, `F.avg` skips them. Spark gives no error,
# MAGIC but calculated *"average tip on tipped rides"* instead of *"average tip per
# MAGIC trip"*. A wrong aggregate still returns a plausible number.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Trap 2: `groupBy` reduces your data grain
# MAGIC
# MAGIC Module 7 taught you to preserve data grain during joins (1 row per trip).
# MAGIC A `groupBy` deliberately **reduces** that grain. Example:
# MAGIC `groupBy("service_type")` — `service_type` has 5 distinct values
# MAGIC (`STANDARD`, `SHARED`, `PREMIUM`, `XL`, `UNKNOWN`). Module 6 normalized
# MAGIC blanks into `"UNKNOWN"`.
# MAGIC
# MAGIC - **Input grain:** 106 rows (1 row per trip)
# MAGIC - **Output grain:** 5 rows (1 row per `service_type`)
# MAGIC
# MAGIC **Core habit:** State the output grain before you write the aggregate.
# MAGIC Verify with `count()` after — especially on a new dataset or a new key.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## What this notebook teaches
# MAGIC
# MAGIC | Section | Concept | Why it matters |
# MAGIC |---|---|---|
# MAGIC | 1. Output grain | One row per group | Predict summary row count before running |
# MAGIC | 2. `groupBy().agg()` | Syntax and aliasing | Name aggregate columns explicitly |
# MAGIC | 3. Counting | 3 counts, 3 answers | Match count function to business question |
# MAGIC | 4. NULL skipping | `sum` / `avg` ignore NULLs | Control denominator with `F.coalesce` |
# MAGIC | Exercise | Per-`payment_method` summary | Apply all four habits on a new key |
# MAGIC
# MAGIC **Core habit:** Name output grain → run → verify with `count()`.
# MAGIC
# MAGIC **Reads:** `rideshare_dev.processed.trip_enriched` (106 rows). **No writes.**
# MAGIC
# MAGIC **Prerequisites:** Module 7 notebooks 01–07 (`trip_enriched`);
# MAGIC Module 3 NULLs & `F.coalesce`; Module 4 wide/shuffle stages.

# COMMAND ----------

# DBTITLE 1,Setup
# MAGIC %md
# MAGIC ## Setup — load `trip_enriched`
# MAGIC
# MAGIC Module 7 Notebook **`07`** wrote this managed table: one row per `trip_id`,
# MAGIC **106** rows, 16 columns.
# MAGIC
# MAGIC | Role | Columns |
# MAGIC |---|---|
# MAGIC | Key | `trip_id` |
# MAGIC | Join keys (retained) | `pickup_location_id`, `dropoff_location_id` |
# MAGIC | Group keys | `service_type`, `payment_method`, `trip_date`, `hour_of_day` |
# MAGIC | Group keys (zone) | `pickup_borough`, `pickup_zone`, `dropoff_borough`, `dropoff_zone` |
# MAGIC | Measures | `trip_distance_miles`, `ride_duration_mins` |
# MAGIC | Measures (money) | `base_fare_amount`, `tip_amount`, `driver_payout_amount` |
# MAGIC
# MAGIC Money and distance columns are `decimal`; `ride_duration_mins` and
# MAGIC `hour_of_day` are `int`; `trip_date` is a `date`.

# COMMAND ----------

from pyspark.sql import functions as F

trip_enriched_table = "rideshare_dev.processed.trip_enriched"

trip_enriched = spark.table(trip_enriched_table)  # noqa: F821

print("trip_enriched rows:", trip_enriched.count())
trip_enriched.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ### The NULLs you inherited — read this before Section 3
# MAGIC
# MAGIC In `trip_enriched`, these columns are NULL on these `trip_id` values.
# MAGIC Both causes are deliberate (Module 7 left joins + Module 6 value rejection):
# MAGIC
# MAGIC | Column(s) | NULL on `trip_id` | Rows | Cause |
# MAGIC |---|---|---|---|
# MAGIC | `trip_date`, `hour_of_day` | 101–106 | 6 | `trip_time` had 100 rows (Module 7 left join) |
# MAGIC | `payment_method`, `driver_payout_amount` | 106 | 1 | `payment` had 105 rows (left join) |
# MAGIC | `base_fare_amount` | 104, 106 | 2 | Left join; Module 6: trip 104 (negative fare) |
# MAGIC | `tip_amount` | 103, 106 | 2 | Left join; Module 6 rejected trip 103's `not_a_number` tip |
# MAGIC | `trip_distance_miles` | 103, 105, 106 | 3 | Module 6: `-1.00`, `not_a_number`, blank |
# MAGIC
# MAGIC The next cell proves the counts — not the individual `trip_id`s.

# COMMAND ----------

trip_enriched.select(
    F.count("*").alias("rows"), ## Counts all rows (NULLs don’t matter)
    F.count("trip_date").alias("trip_date"), ## Exclude NULL rows
    F.count("payment_method").alias("payment_method"),
    F.count("base_fare_amount").alias("base_fare"),
    F.count("tip_amount").alias("tip"),
    F.count("trip_distance_miles").alias("distance"),
    F.count("ride_duration_mins").alias("duration"),
).show()

# Expected: rows=106, trip_date=100, payment_method=105, base_fare=104,
# tip=104, distance=103, duration=106

# COMMAND ----------

# DBTITLE 1,Section 1 - Output grain
# MAGIC %md
# MAGIC ## 1. Output grain — one row per group
# MAGIC
# MAGIC **Output grain** refers to what each row of your *result* represents.
# MAGIC
# MAGIC Module 7 processed *input* grain with one row per `trip_id`. A `groupBy`
# MAGIC operation replaces it with a new structure:
# MAGIC
# MAGIC | | Grain | Rows |
# MAGIC |---|---|---|
# MAGIC | Input `trip_enriched` | One completed trip | 106 |
# MAGIC | `groupBy("service_type")` | One service type | ? |
# MAGIC
# MAGIC You can fill in that `?` **before running the aggregate**, because the output
# MAGIC row count of a `groupBy` is just the number of distinct group-key values:
# MAGIC
# MAGIC ```
# MAGIC output rows == countDistinct(group key)
# MAGIC ```
# MAGIC
# MAGIC The prediction step is straightforward and only requires a single inexpensive
# MAGIC query. If the actual result returns a different row count, then your mental
# MAGIC model of the data is incorrect, and any calculations derived from it will
# MAGIC also be flawed.
# MAGIC
# MAGIC Notebook `02` covers this caveat: `countDistinct` **excludes NULLs**, while
# MAGIC `groupBy` **includes them as a separate group**. `service_type` has no NULLs,
# MAGIC so both methods agree here.
# MAGIC
# MAGIC **Performance Note:** The `groupBy` operation is considered a **wide**
# MAGIC transformation, which involves an `Exchange` (shuffle) as outlined in
# MAGIC Module 4. This means that rows with the same key need to be processed by the
# MAGIC same executor. Tuning the shuffle process will be covered in Module 16.

# COMMAND ----------

# How many groups will groupBy("service_type") produce?
trip_enriched.select("service_type").distinct().count()  # 5 groups expected

# COMMAND ----------

trip_enriched.select("service_type").distinct().show() 

# COMMAND ----------

# MAGIC %md
# MAGIC `UNKNOWN` is Module 6's normalized sentinel for a blank or `n/a`
# MAGIC service type; it is a real string, **not** a NULL.

# COMMAND ----------

# Note the uppercase values: Module 6 normalized service_type with F.upper
trip_enriched.groupBy("service_type").count().orderBy(F.col("count").desc()).show()

# Expected: STANDARD 55, SHARED 21, PREMIUM 16, XL 12, UNKNOWN 2  (sum = 106)

# COMMAND ----------

# DBTITLE 1,Section 2 - groupBy and agg
# MAGIC %md
# MAGIC ## 2. `groupBy().agg()` — multiple aggregates in one pass
# MAGIC Two rules:
# MAGIC
# MAGIC
# MAGIC **1. Multiple Aggregates, One Scan:** You can include as many aggregate
# MAGIC expressions as needed inside the `.agg(...)` function. Spark processes all
# MAGIC of these expressions in a single pass, eliminating the need for separate
# MAGIC queries for operations like count, sum, and average.
# MAGIC
# MAGIC **2. Always Use Aliases:** If you don't use `.alias(...)`, Spark will
# MAGIC automatically generate column names such as `count(1)`, `sum(tip_amount)`,
# MAGIC and `avg(CAST(...))`. These generated names can be difficult to read and
# MAGIC cumbersome to use later on, often requiring backtick escaping like
# MAGIC ``F.col("`sum(tip_amount)`")``. To avoid confusion, always assign each
# MAGIC aggregate a clear, descriptive name.
# MAGIC
# MAGIC The first cell below illustrates the default names that can be hard to
# MAGIC interpret, while the second cell shows a more readable version with aliases.

# COMMAND ----------

# Aggregates without alias — legal, but look at the column names
trip_enriched.groupBy("service_type").agg(
    F.count("*"),
    F.sum("tip_amount"),
    F.avg("trip_distance_miles"),
).show(truncate=False)

# COMMAND ----------

service_summary = trip_enriched.groupBy("service_type").agg(
    F.count("*").alias("trip_count"),
    F.sum("tip_amount").alias("total_tip"),
    F.round(F.avg("trip_distance_miles"), 2).alias("avg_distance_miles"),
    F.min("ride_duration_mins").alias("shortest_ride_mins"),
    F.max("ride_duration_mins").alias("longest_ride_mins"),
)

service_summary.orderBy(F.col("trip_count").desc()).show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## UNKNOWN has 2 trips — which ones? Let's try adding trip_id to the result.

# COMMAND ----------

try:
    service_summary = trip_enriched.groupBy("service_type").agg(
    F.count("*").alias("trip_count"),
    F.sum("tip_amount").alias("total_tip"),
    F.round(F.avg("trip_distance_miles"), 2).alias("avg_distance_miles"),
    F.min("ride_duration_mins").alias("shortest_ride_mins"),
    F.max("ride_duration_mins").alias("longest_ride_mins"),
    F.col("trip_id"),  # This is not allowed
).filter(F.col("service_type") == "UNKNOWN")

    service_summary.show()
except Exception as e:
    print("groupBy collapsed multiple rows into one row per group — there is no single trip_id to display.")
    print("To keep individual rows with group-level summaries, use a window function (Notebook 05).")


# COMMAND ----------

# DBTITLE 1,Section 3 - Counting correctly
# MAGIC %md
# MAGIC ## 3. Counting correctly — three counts, three answers
# MAGIC
# MAGIC | Expression | Question it answers | On `trip_date` |
# MAGIC |---|---|---|
# MAGIC | `F.count("*")` | How many **rows**? | **106** |
# MAGIC | `F.count("trip_date")` | How many rows **have a value**? | **100** |
# MAGIC | `F.countDistinct("trip_date")` | How many **different values**? | **14** |
# MAGIC
# MAGIC These are three different business questions:
# MAGIC
# MAGIC - **How many trips did we operate?** — count all trips.
# MAGIC - **How many trips have a valid trip date?** — count only trips where the date is available.
# MAGIC - **How many days does the dataset cover?** — count the distinct trip dates.
# MAGIC
# MAGIC All three questions are valid, but the appropriate question depends on the **business metric you are trying to measure**
# MAGIC
# MAGIC **Cost note:** `countDistinct` is expensive at scale — Notebook `03` covers a faster approximate alternative.

# COMMAND ----------

trip_enriched.select(
    F.count("*").alias("all_trips"),
    F.count("trip_date").alias("trips_with_a_date"),
    F.countDistinct("trip_date").alias("distinct_dates"),
).show()

# Expected: all_trips=106, trips_with_a_date=100 (6 NULLs), distinct_dates=14

# COMMAND ----------

# MAGIC %md
# MAGIC Now apply the same three counts **per service type** — this is where the difference becomes visible.

# COMMAND ----------

trip_enriched.groupBy("service_type").agg(
    F.count("*").alias("trip_count"),
    F.count("trip_date").alias("dated_trip_count"),
    F.countDistinct("trip_date").alias("distinct_dates"),
).orderBy(F.col("trip_count").desc()).show()

# COMMAND ----------

# MAGIC %md
# MAGIC | `service_type` | `trip_count` | `dated_trip_count` | Gap | `distinct_dates` |
# MAGIC |---|---|---|---|---|
# MAGIC | STANDARD | 55 | 52 | 3 | 14 |
# MAGIC | SHARED | 21 | 21 | 0 | 13 |
# MAGIC | PREMIUM | 16 | 15 | 1 | 9 |
# MAGIC | XL | 12 | 12 | 0 | 8 |
# MAGIC | UNKNOWN | 2 | **0** | 2 | **0** |
# MAGIC
# MAGIC Observe the difference between `trip_count` and `dated_trip_count` — this is where the NULL values are hidden. The STANDARD category is short by 3 trips, yet every row still appears convincing. By displaying both counts side by side, the gap becomes noticeable.
# MAGIC
# MAGIC In the case of UNKNOWN, the situation is even more noticeable: there are 2 trips, but **0** are dated — indicating that this entire group lacks any date information.

# COMMAND ----------

# DBTITLE 1,Section 4 - NULL skipping
# MAGIC %md
# MAGIC ## 4. `sum` / `avg` / `min` / `max` skip NULLs
# MAGIC
# MAGIC Module 3 taught that NULL **propagates** through arithmetic: if `tip_amount`
# MAGIC is NULL then `base_fare_amount + tip_amount` is NULL. Aggregates do the
# MAGIC **opposite** — they quietly **skip** NULL inputs:
# MAGIC
# MAGIC | Context | NULL behavior |
# MAGIC |---|---|
# MAGIC | Row arithmetic (`a + b`) | NULL **propagates** — result is NULL |
# MAGIC | Aggregate (`F.sum`, `F.avg`) | NULL is **skipped** — result ignores it |
# MAGIC
# MAGIC This is the notebook's opening puzzle. `tip_amount` is NULL on 2 of 106
# MAGIC trips, so:
# MAGIC
# MAGIC | Expression | Divides by | Result | Means |
# MAGIC |---|---|---|---|
# MAGIC | `F.avg("tip_amount")` | 104 | ≈ **2.955673** | Average of *known* tips |
# MAGIC | `F.sum(...) / F.count("*")` | 106 | ≈ **2.899906** | Average tip *per trip* |
# MAGIC
# MAGIC Neither is a bug. `F.avg` is `sum / count(col)`, never `sum / count(all rows)`.
# MAGIC The question is which denominator your stakeholder meant, and the code
# MAGIC should make that obvious.
# MAGIC
# MAGIC **Deciding:** if a missing tip means *we don't know*, `F.avg` is right. If it
# MAGIC means *no tip was given* — worth 0.00 — then `F.coalesce(col, F.lit(0))`
# MAGIC before aggregating is right (Module 3). Choose deliberately; don't inherit
# MAGIC the default.
# MAGIC
# MAGIC `F.min` / `F.max` skip NULLs too, so a max is the largest *known* value.
# MAGIC
# MAGIC And one edge worth seeing directly: when **every** value in a group is NULL,
# MAGIC `F.sum` and `F.max` return **NULL**, not `0`. A "total" column that is NULL
# MAGIC rather than zero breaks downstream arithmetic in exactly the way Module 3
# MAGIC warned about.
# MAGIC
# MAGIC Two real examples follow. First at `trip_id` grain, where trips **103** and
# MAGIC **106** each form a single-row group with no known tip, and trip **105** is
# MAGIC the control with a real tip of `2.50`. Then a genuine multi-row case: both
# MAGIC `UNKNOWN` service-type trips are undated, so that group's
# MAGIC `latest_trip_date` is NULL even though the group has 2 rows.

# COMMAND ----------

trip_enriched.select(
    F.count("*").alias("all_trips"),
    F.count("tip_amount").alias("trips_with_tip"),
    F.sum("tip_amount").alias("total_tip"),
    F.avg("tip_amount").alias("avg_skips_nulls"),
    # Round to 6 d.p. to match F.avg's decimal(14,6) output — raw division
    # widens to decimal(38,20) and prints 20 digits without the round.
    F.round(F.sum("tip_amount") / F.count("*"), 6).alias("avg_per_trip"),
).show(truncate=False)

# COMMAND ----------

# Trips 103 and 106 have no known tip, so their totals are NULL — not 0
trip_enriched.filter(F.col("trip_id").isin(103, 105, 106)).groupBy("trip_id").agg(
    F.count("*").alias("rows"),
    F.count("tip_amount").alias("known_tips"),
    F.sum("tip_amount").alias("total_tip"),
    F.max("tip_amount").alias("max_tip"),
    F.coalesce(F.sum("tip_amount"), F.lit(0)).alias("total_or_zero"),
).orderBy("trip_id").show()

# COMMAND ----------

# A multi-row all-NULL group: both UNKNOWN trips are undated, so max is NULL
trip_enriched.groupBy("service_type").agg(
    F.count("*").alias("trip_count"),
    F.count("trip_date").alias("dated_trips"),
    F.max("trip_date").alias("latest_trip_date"),
).orderBy("service_type").show()

# COMMAND ----------

# MAGIC %md
# MAGIC Same question, treating a missing tip as 0.00. `F.coalesce` runs **before**
# MAGIC the aggregate, so the NULLs become real zeros and are no longer skipped —
# MAGIC `avg_with_zeros` now matches `avg_per_trip` above. Note that the **total is
# MAGIC unchanged**: adding zeros cannot move a sum, only the count it is divided by.

# COMMAND ----------

tip_or_zero = F.coalesce(F.col("tip_amount"), F.lit(0).cast("decimal(10,2)"))

trip_enriched.select(
    F.sum(tip_or_zero).alias("total_tip_unchanged"),
    F.count(tip_or_zero).alias("now_counts_all_106"),
    F.avg(tip_or_zero).alias("avg_with_zeros"),
).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC **A note on types, since the output looks odd.** `tip_amount` is
# MAGIC `decimal(10,2)`. Spark widens decimal types when aggregating:
# MAGIC `F.avg` → `decimal(14,6)` (six decimals); `F.sum` → `decimal(20,2)` (keeps
# MAGIC two); raw division (`sum / count`) → `decimal(38,20)` (twenty decimals —
# MAGIC that is why `avg_per_trip` is wrapped in `F.round(..., 6)` above).
# MAGIC Wrap any aggregate in `F.round(..., 2)` when the output is going into a
# MAGIC report. Notebook `03` looks at decimal growth properly.

# COMMAND ----------

# DBTITLE 1,Exercise
# MAGIC %md
# MAGIC ## Exercise — a per-`payment_method` summary
# MAGIC
# MAGIC Sections 1–4 grouped mostly on `service_type`. Apply the same habits on
# MAGIC **`payment_method`**.
# MAGIC
# MAGIC **1. Aggregate.** One row per `payment_method`, with these aliased columns:
# MAGIC
# MAGIC | Alias | Aggregate |
# MAGIC |---|---|
# MAGIC | `trip_count` | All trips (`count("*")`) |
# MAGIC | `trips_with_fare` | Trips with a non-NULL `base_fare_amount` |
# MAGIC | `total_base_fare` | Sum of `base_fare_amount`, rounded to 2 |
# MAGIC | `avg_fare_skips_null` | `F.avg("base_fare_amount")`, rounded to 2 |
# MAGIC | `avg_fare_per_trip` | `F.sum / F.count("*")`, rounded to 2 |
# MAGIC
# MAGIC **2. Check the row count.** After you run, set `predicted_method_groups` to
# MAGIC the number of rows you got and confirm it matches `method_summary.count()`.
# MAGIC (You may see more groups than `countDistinct("payment_method")` — Notebook
# MAGIC `02` explains why.)
# MAGIC
# MAGIC **3. Explain (Section 4).** For the row where `payment_method` is NULL, why
# MAGIC are `total_base_fare` and `avg_fare_skips_null` both NULL, while
# MAGIC `trip_count` is 1?
# MAGIC
# MAGIC Expected results:
# MAGIC
# MAGIC | payment_method | trip_count | trips_with_fare | total_base_fare |
# MAGIC |---|---|---|---|
# MAGIC | card | 59 | 59 | 1785.85 |
# MAGIC | wallet | 20 | 20 | 661.33 |
# MAGIC | cash | 17 | 17 | 536.17 |
# MAGIC | corporate | 8 | 8 | 269.75 |
# MAGIC | unknown | 1 | 0 | null |
# MAGIC | null | 1 | 0 | null |
# MAGIC
# MAGIC | payment_method | avg_fare_skips_null | avg_fare_per_trip |
# MAGIC |---|---|---|
# MAGIC | card | 30.27 | 30.27 |
# MAGIC | wallet | 33.07 | 33.07 |
# MAGIC | cash | 31.54 | 31.54 |
# MAGIC | corporate | 33.72 | 33.72 |
# MAGIC | unknown | null | null |
# MAGIC | null | null | null |
# MAGIC
# MAGIC Notice `unknown` and `null` both appear — Notebook `02` explains that
# MAGIC difference.

# COMMAND ----------

# 1. YOUR CODE — build the per-payment_method summary described above
method_summary = trip_enriched.groupBy("payment_method").agg(
    F.count("*").alias("trip_count"),
    # TODO: trips_with_fare, total_base_fare, avg_fare_skips_null, avg_fare_per_trip
)

# 2. YOUR CHECK — set this to the row count you observed
predicted_method_groups = None

actual = method_summary.count()
match = "✓" if predicted_method_groups == actual else "✗"
print(f"{match} predicted={predicted_method_groups}, actual={actual}")

method_summary.orderBy(F.col("trip_count").desc()).show()

# COMMAND ----------

# DBTITLE 1,Summary
# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC | Concept | Key takeaway |
# MAGIC |---|---|
# MAGIC | **Output grain** | One row per group; predict with `countDistinct` when no NULLs |
# MAGIC | **Aliasing** | Alias every aggregate — names are needed to chain `.filter()` |
# MAGIC | **Only keys and aggregates** | Want a per-row column too? That's a window (`05`) |
# MAGIC | **Three counts** | `count("*")`=106, `count("trip_date")`=100, `countDistinct`=14 |
# MAGIC | **NULL skipping** | `avg` divides by non-NULL count (104), not by rows (106) |
# MAGIC | **`F.coalesce` first** | Use it when missing means 0, not *unknown* |
# MAGIC
# MAGIC **The habit that prevents most aggregation bugs:** name the output grain,
# MAGIC then verify with `count()` after — especially on a new key. A wrong
# MAGIC aggregate just gives you a plausible number — no error to notice.
# MAGIC
# MAGIC **Next:** **`02 - Multi-column Keys, NULL Groups, and Filter Placement`** —
# MAGIC grouping on composite keys, why NULL becomes its own group, and how
# MAGIC `WHERE` vs `HAVING` produce different numbers from the same aggregation.