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
# MAGIC but calculated *"average tip on tipped rides"* instead of *"average tip per trip"*.
# MAGIC A wrong aggregate still returns a plausible number.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Trap 2: `groupBy` collapses your data grain
# MAGIC Module 7 taught you to preserve data grain during joins (1 row per trip).
# MAGIC A `groupBy` deliberately **collapses** that grain:
# MAGIC
# MAGIC - **Input grain:** 106 rows (1 row per trip)
# MAGIC - **Output grain:** 5 rows (1 row per `service_type`)
# MAGIC
# MAGIC > **Why 5 rows?** `service_type` has 5 distinct values (`STANDARD`, `SHARED`,
# MAGIC > `PREMIUM`, `XL`, `UNKNOWN`). Module 6 normalized blanks into `"UNKNOWN"`.
# MAGIC > *(By contrast, grouping by `payment_method` gives 6 rows because Spark keeps
# MAGIC > `NULL` as a 6th group).*
# MAGIC
# MAGIC **Core rule:** Always name the output grain and predict the row count *before*
# MAGIC running the aggregate.
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
# MAGIC **Core habit:** Name output grain → predict row count → run → verify with `count()`.
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
# MAGIC Every number in this notebook depends on knowing where the NULLs are. They
# MAGIC come from two places, both deliberate:
# MAGIC
# MAGIC | Column(s) | NULL on `trip_id` | Rows | Cause |
# MAGIC |---|---|---|---|
# MAGIC | `trip_date`, `hour_of_day` | 101–106 | 6 | `trip_time` had 100 rows (Module 7 left join) |
# MAGIC | `payment_method`, `driver_payout_amount` | 106 | 1 | `payment` had 105 rows (left join) |
# MAGIC | `base_fare_amount` | 104, 106 | 2 | Left join; Module 6: trip 104 (negative fare) |
# MAGIC | `tip_amount` | 103, 106 | 2 | Left join; Module 6 rejected trip 103's `not_a_number` tip |
# MAGIC | `trip_distance_miles` | 103, 105, 106 | 3 | Module 6: `-1.00`, `not_a_number`, blank |
# MAGIC
# MAGIC `ride_duration_mins`, `service_type`, and the four zone columns have **no**
# MAGIC NULLs. So there is no single "non-NULL row count" for this table — **each
# MAGIC column has its own**, which is exactly why Section 3 exists.
# MAGIC
# MAGIC The next cell proves the table above rather than asking you to trust it.

# COMMAND ----------

trip_enriched.select(
    F.count("*").alias("rows"),
    F.count("trip_date").alias("trip_date"),
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
# MAGIC **Output grain** = what one row of your *result* represents.
# MAGIC
# MAGIC Module 7 drilled *input* grain: one row per `trip_id`. A `groupBy` replaces
# MAGIC it with a new one:
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
# MAGIC That is your prediction step, and it costs one cheap query. If the real
# MAGIC result has a different row count, stop — your mental model of the data is
# MAGIC wrong, and every number built on top of it will be too.
# MAGIC
# MAGIC One caveat that Section 5 returns to: `countDistinct` **ignores NULLs** but
# MAGIC `groupBy` **keeps them as a group**. `service_type` has no NULLs, so the two
# MAGIC agree here.
# MAGIC
# MAGIC **Performance note:** `groupBy` is a **wide** transformation — the `Exchange`
# MAGIC (shuffle) from Module 4. Rows for the same key must meet on one executor.
# MAGIC Tuning that shuffle is Module 16.

# COMMAND ----------

predicted_groups = trip_enriched.select(
    F.countDistinct("service_type").alias("distinct_service_type"),
).collect()[0]["distinct_service_type"]

actual_groups = trip_enriched.groupBy("service_type").count().count()

print(f"predicted output rows = {predicted_groups}")
print(f"actual output rows    = {actual_groups}")
print("match:", predicted_groups == actual_groups)

# COMMAND ----------

# MAGIC %md
# MAGIC Five groups, and the per-group counts sum back to 106 — a `groupBy` on a
# MAGIC column with no NULLs never loses or invents rows, it only redistributes
# MAGIC them. `UNKNOWN` is Module 6's normalized sentinel for a blank or `n/a`
# MAGIC service type; it is a real string, **not** a NULL.

# COMMAND ----------

# Note the uppercase values: Module 6 normalized service_type with F.upper
trip_enriched.groupBy("service_type").count().orderBy(F.col("count").desc()).show()

# Expected: STANDARD 55, SHARED 21, PREMIUM 16, XL 12, UNKNOWN 2  (sum = 106)

# COMMAND ----------

# DBTITLE 1,Section 2 - groupBy and agg
# MAGIC %md
# MAGIC ## 2. `groupBy().agg()` and why aliasing is not optional
# MAGIC
# MAGIC `.count()` is a shorthand for one specific aggregate. The general form takes
# MAGIC any number of aggregates in a single pass:
# MAGIC
# MAGIC ```python
# MAGIC trip_enriched.groupBy("service_type").agg(
# MAGIC     F.count("*").alias("trip_count"),
# MAGIC     F.sum("tip_amount").alias("total_tip"),
# MAGIC )
# MAGIC ```
# MAGIC
# MAGIC Two rules worth internalizing now:
# MAGIC
# MAGIC **1. Alias every aggregate.** Without `.alias(...)`, Spark names the column
# MAGIC after the expression — `count(1)`, `sum(tip_amount)`, `avg(CAST(...))`. Those
# MAGIC are legal but painful to reference: the parentheses have to be escaped with
# MAGIC backticks, as in ``F.col("`sum(tip_amount)`")``, or Spark reads the name as a
# MAGIC function call. Section 6 has to *filter* on an aggregate by name, so an alias
# MAGIC is not cosmetic.
# MAGIC
# MAGIC **2. Output columns are group keys and aggregates — nothing else.** Referring
# MAGIC to a bare `trip_id` in the result is an error, because 55 `STANDARD` trips
# MAGIC have 55 different `trip_id` values and Spark will not pick one for you. If
# MAGIC you genuinely want a per-row column *and* a group summary side by side, you
# MAGIC want a **window function** — Notebook `05`.
# MAGIC
# MAGIC The first cell shows the unaliased mess, the second the readable version.

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

# DBTITLE 1,Section 3 - Counting correctly
# MAGIC %md
# MAGIC ## 3. Counting correctly — three counts, three answers
# MAGIC
# MAGIC "How many?" is the most common question asked of a dataset and the easiest
# MAGIC one to answer wrongly. Three expressions look interchangeable and are not:
# MAGIC
# MAGIC | Expression | Question it answers | On `trip_date` |
# MAGIC |---|---|---|
# MAGIC | `F.count("*")` | How many **rows**? | **106** |
# MAGIC | `F.count("trip_date")` | How many rows **have a value**? | **100** |
# MAGIC | `F.countDistinct("trip_date")` | How many **different values**? | **14** |
# MAGIC
# MAGIC Read those as three different business questions: *how many trips did we
# MAGIC run*, *how many trips do we know the date of*, and *how many days does this
# MAGIC data cover*. All three are reasonable; only one is what you were asked.
# MAGIC
# MAGIC - `106 - 100 = 6` **is** the six undated trips (101–106) from the setup table.
# MAGIC - **14** is small because 100 trips are spread over just 14 calendar dates.
# MAGIC
# MAGIC **Gotcha — say what you mean.** `F.count("*")`, `F.count(F.lit(1))`, and
# MAGIC `F.count(F.col("*"))` all count rows. They are equivalent, but a reader
# MAGIC cannot tell whether you *meant* "all rows" or fat-fingered a column name.
# MAGIC Prefer `F.count("*")` with an alias that states the intent. This module
# MAGIC and Module 7 now use the same form for consistency.
# MAGIC
# MAGIC **Cost warning.** `F.countDistinct` must deduplicate across the whole
# MAGIC cluster, which is far more expensive than counting. On 106 rows you will
# MAGIC never notice; on a billion you will. Notebook `03` covers
# MAGIC `F.approx_count_distinct` for when an estimate is good enough.

# COMMAND ----------

trip_enriched.select(
    F.count("*").alias("all_trips"),
    F.count("trip_date").alias("trips_with_a_date"),
    F.countDistinct("trip_date").alias("distinct_dates"),
    # Same 106 as all_trips — proof that these row-counting forms are equivalent
    F.count(F.lit(1)).alias("count_lit_1"),
    F.count(F.col("*")).alias("count_col_star"),
).show()

# COMMAND ----------

# MAGIC %md
# MAGIC Now the same three counts **per group**, which is where this gets practical.
# MAGIC The six undated trips do not sit in one tidy place — they scatter across
# MAGIC three service types:
# MAGIC
# MAGIC | `service_type` | `trip_count` | `dated_trip_count` | Gap | `distinct_dates` |
# MAGIC |---|---|---|---|---|
# MAGIC | STANDARD | 55 | 52 | 3 | 14 |
# MAGIC | SHARED | 21 | 21 | 0 | 13 |
# MAGIC | PREMIUM | 16 | 15 | 1 | 9 |
# MAGIC | XL | 12 | 12 | 0 | 8 |
# MAGIC | UNKNOWN | 2 | **0** | 2 | **0** |
# MAGIC
# MAGIC This is how a NULL problem hides in a summary. `SHARED` and `XL` are
# MAGIC perfectly clean, `STANDARD` is short by 3, and every row still *looks*
# MAGIC plausible. Only by putting `count("*")` and `count(col)` side by side does
# MAGIC the gap become visible at all — a report showing just one of them would
# MAGIC never reveal it.
# MAGIC
# MAGIC `UNKNOWN` is the extreme case: 2 trips, **0** of them dated. Both a count of
# MAGIC non-NULL values and a distinct count of an all-NULL group are `0`.

# COMMAND ----------

trip_enriched.groupBy("service_type").agg(
    F.count("*").alias("trip_count"),
    F.count("trip_date").alias("dated_trip_count"),
    F.countDistinct("trip_date").alias("distinct_dates"),
).orderBy(F.col("trip_count").desc()).show()

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
# MAGIC Sections 1–4 grouped mostly on `service_type`. Now apply the same four
# MAGIC habits on **`payment_method`** — a column that has a NULL group.
# MAGIC
# MAGIC **1. Predict.** Set `predicted_method_groups` to the number of output rows
# MAGIC you expect. Hint: `payment_method` has 5 distinct string values *plus*
# MAGIC 1 NULL group (trip 106 has no payment row). `countDistinct` reports 5
# MAGIC but `groupBy` will produce **6** — that is the distinction from Section 4.
# MAGIC
# MAGIC **2. Aggregate.** One row per `payment_method`, with these aliased columns:
# MAGIC
# MAGIC | Alias | Aggregate |
# MAGIC |---|---|
# MAGIC | `trip_count` | All trips (`count("*")`) |
# MAGIC | `trips_with_fare` | Trips with a non-NULL `base_fare_amount` |
# MAGIC | `total_base_fare` | Sum of `base_fare_amount`, rounded to 2 |
# MAGIC | `avg_fare_skips_null` | `F.avg("base_fare_amount")`, rounded to 2 |
# MAGIC | `avg_fare_per_trip` | `F.sum / F.count("*")`, rounded to 2 |
# MAGIC
# MAGIC **3. Explain.** For the NULL group, why are `total_base_fare` and
# MAGIC `avg_fare_skips_null` both NULL, while `trip_count` is 1?
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
# MAGIC Notice `unknown` and `null` are two different rows — different data
# MAGIC problems that a careless summary would merge. Notebook `02` explains why.

# COMMAND ----------

# 1. YOUR PREDICTION — replace None with the expected row count
predicted_method_groups = None

# 2. YOUR CODE — build the per-payment_method summary described above
method_summary = trip_enriched.groupBy("payment_method").agg(
    F.count("*").alias("trip_count"),
    # TODO: trips_with_fare, total_base_fare, avg_fare_skips_null, avg_fare_per_trip
)

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
# MAGIC predict the row count, then verify. A wrong aggregate just gives you a
# MAGIC plausible number — no error to notice.
# MAGIC
# MAGIC **Next:** **`02 - Multi-column Keys, NULL Groups, and Filter Placement`** —
# MAGIC grouping on composite keys, why NULL becomes its own group, and how
# MAGIC `WHERE` vs `HAVING` produce different numbers from the same aggregation.
