# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC
# MAGIC # 04 - Semi Joins and Anti Joins
# MAGIC
# MAGIC ### The problem: you need to filter rows by whether a match exists — without adding columns
# MAGIC
# MAGIC Inner and left joins answer "what does the combined record look like?" They
# MAGIC append columns from both sides. But sometimes the question is simpler:
# MAGIC
# MAGIC - **Which trips already have a payment?** (keep those rows, nothing else)
# MAGIC - **Which trips are missing a payment?** (find the gaps)
# MAGIC
# MAGIC A regular join would add all payment columns just to answer a yes/no
# MAGIC question. Semi and anti joins answer it directly — returning **only left-side
# MAGIC columns**, with zero schema expansion.
# MAGIC
# MAGIC PySpark exposes these as join-type strings:
# MAGIC
# MAGIC | Join type | Question answered | Result schema |
# MAGIC |---|---|---|
# MAGIC | `"left_semi"` | Left rows where a match **exists** in the right | Left columns only |
# MAGIC | `"left_anti"` | Left rows where **no match** exists in the right | Left columns only |
# MAGIC
# MAGIC | Section | Focus |
# MAGIC |---|---|
# MAGIC | 1 | `left_semi` — keep trips that have a payment |
# MAGIC | 2 | `left_anti` — find trips without a payment; verify; reverse anti |
# MAGIC | 3 | Practice — apply semi/anti to a second gap (trip_time) |
# MAGIC | 4 | Bridge to `subtract()` — conceptual preview for Notebook 06 |
# MAGIC
# MAGIC **Reads:** `curated/trip` (Parquet, 106 rows); `curated/payment` (Parquet,
# MAGIC 105 rows); landing `trip_time` (Parquet, 100 rows — practice only). **No
# MAGIC write.**
# MAGIC
# MAGIC **Prerequisites.** Module 7 **`01`–`03`**; Module 6 (**`01`–`04`**) so
# MAGIC `curated/trip` and `curated/payment` exist. Join syntax, key profiling, and
# MAGIC outer-join behavior are applied here, not re-taught.

# COMMAND ----------

# DBTITLE 1,Setup
# MAGIC %md
# MAGIC ## Setup — load curated trip and payment
# MAGIC
# MAGIC | Table | Format | Grain | Key | Rows | Used in |
# MAGIC |---|---|---|---|---|---|
# MAGIC | `curated/trip` | Parquet | one completed trip | `trip_id` | 106 | Sections 1–4 |
# MAGIC | `curated/payment` | Parquet | one fare record per trip | `trip_id` | 105 | Sections 1–2 |
# MAGIC | Landing `trip_time` | Parquet | one time record per trip | `trip_id` | 100 | Practice (Section 3 only) |
# MAGIC
# MAGIC `curated/payment` has 105 rows — one fewer than `curated/trip`. Trip 106
# MAGIC exists in trip but has no payment record. This intentional gap drives the
# MAGIC anti-join demo in Section 2.
# MAGIC
# MAGIC Trips 101–106 have no record in `trip_time` (which covers only the original
# MAGIC 100 trips). That 6-row gap drives the Section 3 practice.

# COMMAND ----------

# DBTITLE 1,Load curated trip, payment, and landing trip_time
from pyspark.sql import functions as F

curated_root = "/Volumes/rideshare_dev/processed/output_files/curated"
landing_root = "/Volumes/rideshare_dev/landing/source_files"

trip = spark.read.format("parquet").load(f"{curated_root}/trip")  # noqa: F821
payment = spark.read.format("parquet").load(f"{curated_root}/payment")  # noqa: F821
trip_time = spark.read.format("parquet").load(  # noqa: F821
    f"{landing_root}/trip_time/trip_time.parquet"
)

print("trip rows:", trip.count())
print("payment rows:", payment.count())
print("trip_time rows:", trip_time.count())

# COMMAND ----------

# DBTITLE 1,Profile trip_id on trip and payment
# Quick key profile — applying the NB02 habit, not re-teaching it
for name, df in [("trip", trip), ("payment", payment)]:
    stats = df.select(
        F.count(F.lit(1)).alias("rows"),
        F.countDistinct("trip_id").alias("distinct"),
        F.sum(F.when(F.col("trip_id").isNull(), 1).otherwise(0)).alias("nulls"),
    ).collect()[0]
    print(
        f"{name}: rows={stats['rows']}, "
        f"distinct={stats['distinct']}, nulls={stats['nulls']}"
    )

print("\n\u2192 Both unique, no NULLs \u2014 safe to join on trip_id")

# COMMAND ----------

# DBTITLE 1,1. left_semi
# MAGIC %md
# MAGIC ## 1. `left_semi` — keep trips that have a payment
# MAGIC
# MAGIC **Question:** which of the 106 trips already have a payment record?
# MAGIC
# MAGIC **Prediction:** `curated/payment` has trip_ids 1–105. A `left_semi` join
# MAGIC keeps every trip row whose `trip_id` exists in `payment` — that's 105 rows.
# MAGIC Trip 106 has no match, so it drops.
# MAGIC
# MAGIC The key difference from an inner join: **semi returns only left-side
# MAGIC columns**. No payment columns appear in the result.

# COMMAND ----------

# DBTITLE 1,1. Run left_semi and verify
trips_with_payment = trip.join(payment, "trip_id", "left_semi")

print("left_semi row count:", trips_with_payment.count())
print("\nResult columns (left side only):")
print(trips_with_payment.columns)

# COMMAND ----------

# DBTITLE 1,1. Contrast with inner join column count
# Inner join on the same key returns the same 105 qualifying rows,
# but appends all payment columns — semi gives the filter without the payload.
inner_result = trip.join(payment, "trip_id", "inner")

print(f"inner join: {inner_result.count()} rows, {len(inner_result.columns)} columns")
print(f"left_semi:  {trips_with_payment.count()} rows, {len(trips_with_payment.columns)} columns")
print(f"\n\u2192 Same qualifying rows, but semi keeps only the {len(trip.columns)} trip columns")

# COMMAND ----------

# DBTITLE 1,2. left_anti
# MAGIC %md
# MAGIC ## 2. `left_anti` — find trips without a payment
# MAGIC
# MAGIC **Question:** which trips have no payment record at all?
# MAGIC
# MAGIC **Prediction:** only trip 106 has no match in `curated/payment` — expect
# MAGIC **1 row**.
# MAGIC
# MAGIC `left_anti` is the complement of `left_semi`: it keeps left rows where
# MAGIC **no key match** exists on the right. Same rule — only left-side columns in
# MAGIC the result.
# MAGIC
# MAGIC **Production use cases:**
# MAGIC - **Completeness audits** — find orders without shipments, users without logins
# MAGIC - **Incremental loads** — identify new records that haven't been processed yet
# MAGIC - **Orphan detection** — fact rows referencing deleted dimension keys

# COMMAND ----------

# DBTITLE 1,2. Run left_anti and verify
trips_without_payment = trip.join(payment, "trip_id", "left_anti")

print("left_anti row count:", trips_without_payment.count())
print("\nThe missing trip:")
trips_without_payment.select("trip_id", "service_type").show()

# Verify: semi + anti must account for every row in the driving table
semi_count = trips_with_payment.count()
anti_count = trips_without_payment.count()
print(f"Verify: semi({semi_count}) + anti({anti_count}) = {semi_count + anti_count} == trip.count({trip.count()})")

# COMMAND ----------

# DBTITLE 1,2b. Verify: semi + anti = total
# MAGIC %md
# MAGIC When the join key is unique and NULL-free on both sides, `left_semi` count +
# MAGIC `left_anti` count always equals the driving table’s row count. This is your
# MAGIC exhaustive-split check for filtering joins.

# COMMAND ----------

# DBTITLE 1,2c. Reverse anti
# MAGIC %md
# MAGIC ### 2c. Reverse anti — flip the driving side
# MAGIC
# MAGIC Same two tables, different question: are there any payments that have **no
# MAGIC matching trip**?
# MAGIC
# MAGIC **Prediction:** every payment (trip_ids 1–105) has a corresponding trip row.
# MAGIC Expect **0 rows**.
# MAGIC
# MAGIC The direction of a filtering join changes which side’s gaps you detect.

# COMMAND ----------

# DBTITLE 1,2c. Reverse anti — payments without a trip
payments_without_trip = payment.join(trip, "trip_id", "left_anti")
print("Payments without a matching trip:", payments_without_trip.count(), "rows")
print("\n\u2192 Same tables, different driver \u2014 different answer")

# COMMAND ----------

# DBTITLE 1,3. Practice
# MAGIC %md
# MAGIC ## 3. Practice — a second intentional gap (trip_time)
# MAGIC
# MAGIC Landing `trip_time` has 100 rows covering trip_ids 1–100. The curated trip
# MAGIC table has 106 rows (trip_ids 1–106). Trips 101–106 were added during Module 6
# MAGIC cleaning and have **no time record**.
# MAGIC
# MAGIC **Your task:** apply semi and anti joins to this second pair using Boolean
# MAGIC form with aliases (Notebook 01 Section 3.3).
# MAGIC
# MAGIC | Join | Driving side | Right side | Predicted rows |
# MAGIC |---|---|---|---|
# MAGIC | `left_semi` | `trip` (106) | `trip_time` (100) | ? |
# MAGIC | `left_anti` | `trip` (106) | `trip_time` (100) | ? |

# COMMAND ----------

# DBTITLE 1,3. Practice - left_semi on trip_time
# TODO (practice): Write a left_semi join from `trip` to `trip_time`
# using Boolean form with aliases.
#
# Steps:
#   1. Alias trip as "t" and trip_time as "tt"
#   2. Join: t.join(tt, <Boolean condition>, "left_semi")
#   3. Print the count — does it match your prediction?


# COMMAND ----------

# DBTITLE 1,3b. Now find what's missing
# MAGIC %md
# MAGIC ### Now find what’s missing
# MAGIC
# MAGIC Predict before running: how many trips have **no** time record? Which
# MAGIC trip_ids are they?

# COMMAND ----------

# DBTITLE 1,3. Practice - left_anti on trip_time
# TODO (practice): Write a left_anti join from `trip` to `trip_time`
# using Boolean form with aliases.
#
# Steps:
#   1. Alias trip as "t" and trip_time as "tt"
#   2. Join: t.join(tt, <Boolean condition>, "left_anti")
#   3. Print the count and display the trip_ids
#   4. Also confirm: semi count + anti count = 106


# COMMAND ----------

# DBTITLE 1,4. Bridge to subtract()
# MAGIC %md
# MAGIC ## 4. Bridge to `subtract()` — conceptual preview
# MAGIC
# MAGIC The anti-join above found trip_id 106 — the one trip key not in `payment`.
# MAGIC You can get the same single key using `subtract()` on the key column alone.
# MAGIC
# MAGIC **Key difference:** `left_anti` matches on a specified join key and returns
# MAGIC all left columns. `subtract()` compares **entire rows** — every selected
# MAGIC column must match. Selecting just the key column makes the comparison
# MAGIC equivalent to anti-join on that key.
# MAGIC
# MAGIC **Gotcha:** `trip.subtract(payment)` would fail or return nonsense because
# MAGIC the two DataFrames have different schemas. You must select the same
# MAGIC column(s) from both sides first.
# MAGIC
# MAGIC Full set-operation coverage → Notebook 06.

# COMMAND ----------

# DBTITLE 1,4. subtract on trip_id — same result as anti-join
# Key-only subtract: equivalent to the anti-join result for this column
subtract_result = trip.select("trip_id").subtract(payment.select("trip_id"))

print("subtract on trip_id:", subtract_result.count(), "row(s)")
subtract_result.show()

# COMMAND ----------

# DBTITLE 1,Summary
# MAGIC %md
# MAGIC ## Summary — filtering joins in one page
# MAGIC
# MAGIC 1. **`left_semi`** keeps left rows where a match exists on the right — no
# MAGIC    right-side columns appear.
# MAGIC
# MAGIC 2. **`left_anti`** keeps left rows where **no match** exists — same
# MAGIC    left-only schema.
# MAGIC
# MAGIC 3. **Direction matters** — swapping which table drives the join changes
# MAGIC    which side’s gaps you detect.
# MAGIC
# MAGIC 4. **Exhaustive-split check** — semi count + anti count = driving table’s
# MAGIC    row count (when the key is unique and NULL-free).
# MAGIC
# MAGIC 5. **Anti on a key ≈ `subtract()` on that key column** — but `subtract()`
# MAGIC    requires whole-row equality on the selected columns. Full set-operation
# MAGIC    coverage in Notebook 06.
# MAGIC
# MAGIC **Next:** **`05 - Union and unionByName`**