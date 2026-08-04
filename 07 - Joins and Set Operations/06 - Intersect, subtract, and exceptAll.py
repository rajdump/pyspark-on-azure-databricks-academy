# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC # 06 - Intersect, subtract, and exceptAll
# MAGIC
# MAGIC Notebook **05** stacked DataFrames with `union` / `unionByName`. This
# MAGIC notebook covers the other whole-row set operations: keep rows that appear
# MAGIC on **both** sides, or keep rows that appear on **one** side only.
# MAGIC
# MAGIC These APIs compare **entire rows** (all selected columns), not a join key.
# MAGIC Notebook **04** previewed `subtract()` next to `left_anti` — here you get
# MAGIC the full set-op family, including the `*All` variants that preserve
# MAGIC duplicate counts.
# MAGIC
# MAGIC | Section | Focus |
# MAGIC |---|---|
# MAGIC | 1 | `intersect` vs `intersectAll` |
# MAGIC | 2 | `subtract` vs `exceptAll` |
# MAGIC | 3 | SQL `EXCEPT` naming vs DataFrame API |
# MAGIC | Practice | Predict multiset set-op counts on a new handmade pair |
# MAGIC
# MAGIC **Prerequisites.** Module 7 **`01`–`05`**. **No write.**

# COMMAND ----------

# DBTITLE 1,Set-op rules
# MAGIC %md
# MAGIC ## Set-op rules
# MAGIC
# MAGIC 1. Set ops compare **whole rows** (every selected column), not a join key.
# MAGIC 2. `intersect` / `subtract` remove duplicate results (**distinct** set semantics).
# MAGIC 3. `intersectAll` / `exceptAll` preserve duplicate **counts** (multiset semantics).
# MAGIC 4. Column alignment follows **position** (same idea as `union`), not name.
# MAGIC 5. SQL names: `INTERSECT` ↔ `intersect`; `INTERSECT ALL` ↔ `intersectAll`;
# MAGIC    `EXCEPT` / `EXCEPT DISTINCT` ↔ `subtract`; `EXCEPT ALL` ↔ `exceptAll`.

# COMMAND ----------

# DBTITLE 1,Setup
# MAGIC %md
# MAGIC ## Setup — overlapping trip_id filters on landing trip
# MAGIC
# MAGIC | Frame | Filter | Rows |
# MAGIC |---|---|---:|
# MAGIC | Landing `trip` | full table | 100 |
# MAGIC | `le_60` | `trip_id <= 60` | 60 |
# MAGIC | `ge_41` | `trip_id >= 41` | 60 |
# MAGIC | Overlap | `trip_id` 41–60 | 20 |
# MAGIC
# MAGIC Because each `trip_id` appears once, `le_60` and `ge_41` have no duplicate
# MAGIC rows. Sections 1–2 use them for clear overlap / difference counts, then use
# MAGIC tiny handmade frames to show where `*All` behaves differently.

# COMMAND ----------

# DBTITLE 1,Load landing trip and build filters
from pyspark.sql import functions as F

landing_root = "/Volumes/rideshare_dev/landing/source_files"

trip = (
    spark.read.format("csv")  # noqa: F821
    .option("header", True)
    .schema(
        "trip_id bigint, service_type string, pickup_location_id int, "
        "dropoff_location_id int, trip_distance_miles decimal(8,2), "
        "request_to_pickup_mins int, ride_duration_mins int, "
        "driver_arrival_to_pickup_mins int"
    )
    .load(f"{landing_root}/trip/trip.csv")
)

le_60 = trip.filter(F.col("trip_id") <= 60)
ge_41 = trip.filter(F.col("trip_id") >= 41)

print("trip:", trip.count())
print("le_60:", le_60.count())
print("ge_41:", ge_41.count())

# COMMAND ----------

# DBTITLE 1,1. intersect vs intersectAll
# MAGIC %md
# MAGIC ## 1. `intersect` vs `intersectAll`
# MAGIC
# MAGIC `intersect()` returns rows that appear in **both** DataFrames and removes
# MAGIC duplicates from the result. It matches SQL `INTERSECT`.
# MAGIC
# MAGIC `intersectAll()` also keeps only rows present on both sides, but preserves
# MAGIC how many times a row can appear — limited by the **smaller** duplicate count
# MAGIC on either side. It matches SQL `INTERSECT ALL`.

# COMMAND ----------

# DBTITLE 1,1. intersect on landing overlap
shared = le_60.intersect(ge_41)

print("intersect rows:", shared.count())  # trip_ids 41–60 → 20
shared.select("trip_id").orderBy("trip_id").show(5)

# COMMAND ----------

# DBTITLE 1,1b. intersect vs intersectAll with duplicates
# Handmade frames — same trip_id can appear more than once
left_dup = spark.createDataFrame(  # noqa: F821
    [(1,), (1,), (2,), (3,)],
    ["trip_id"],
)
right_dup = spark.createDataFrame(  # noqa: F821
    [(1,), (1,), (2,)],
    ["trip_id"],
)

print("intersect (deduped):")
left_dup.intersect(right_dup).orderBy("trip_id").show()

print("intersectAll (keeps overlapping copies):")
left_dup.intersectAll(right_dup).orderBy("trip_id").show()
print("→ trip_id 1 appears twice on both sides → intersectAll keeps 2 copies")

# COMMAND ----------

# DBTITLE 1,2. subtract vs exceptAll
# MAGIC %md
# MAGIC ## 2. `subtract` vs `exceptAll`
# MAGIC
# MAGIC `subtract()` returns rows in the **left** DataFrame that do not appear in the
# MAGIC right DataFrame, and removes duplicates from the result. It matches SQL
# MAGIC `EXCEPT` / `EXCEPT DISTINCT`.
# MAGIC
# MAGIC `exceptAll()` is the same idea but preserves duplicate counts on the left
# MAGIC after subtracting matching copies on the right. It matches SQL `EXCEPT ALL`.
# MAGIC
# MAGIC Notebook **04** contrasted `left_anti` (join key; keeps left duplicates) with
# MAGIC `subtract()` (whole selected row; distinct result). This section is the full
# MAGIC `subtract` / `exceptAll` treatment.

# COMMAND ----------

# DBTITLE 1,2. subtract on landing filters
only_early = le_60.subtract(ge_41)  # trip_ids 1–40
only_late = ge_41.subtract(le_60)  # trip_ids 61–100

print("le_60.subtract(ge_41):", only_early.count())  # 40
print("ge_41.subtract(le_60):", only_late.count())  # 40
print("→ Direction matters: which side is left decides which leftover you get")

# COMMAND ----------

# DBTITLE 1,2b. subtract vs exceptAll with duplicates
batch_a = spark.createDataFrame(  # noqa: F821
    [(1,), (1,), (1,), (2,), (3,), (4,)],
    ["trip_id"],
)
batch_b = spark.createDataFrame(  # noqa: F821
    [(1,), (3,)],
    ["trip_id"],
)

print("subtract (distinct difference):")
batch_a.subtract(batch_b).orderBy("trip_id").show()

print("exceptAll (multiset difference):")
batch_a.exceptAll(batch_b).orderBy("trip_id").show()
print("→ three copies of trip_id 1 minus one copy → two remain under exceptAll")

# COMMAND ----------

# DBTITLE 1,3. SQL EXCEPT naming
# MAGIC %md
# MAGIC ## 3. SQL `EXCEPT` naming vs DataFrame API
# MAGIC
# MAGIC Module 7 stays on the DataFrame API (Module **09** covers SQL side by side).
# MAGIC Learn the name mapping so SQL docs and teammates make sense:
# MAGIC
# MAGIC | SQL | DataFrame API | Duplicate behavior |
# MAGIC |---|---|---|
# MAGIC | `INTERSECT` | `intersect()` | Distinct |
# MAGIC | `INTERSECT ALL` | `intersectAll()` | Preserve counts |
# MAGIC | `EXCEPT` / `EXCEPT DISTINCT` | `subtract()` | Distinct |
# MAGIC | `EXCEPT ALL` | `exceptAll()` | Preserve counts |
# MAGIC
# MAGIC There is **no** DataFrame method named `except`. Use `subtract()` for SQL
# MAGIC `EXCEPT`.

# COMMAND ----------

# DBTITLE 1,3. Naming check — subtract is EXCEPT DISTINCT
# Same landing difference as Section 2 — naming reminder only
print("subtract count:", le_60.subtract(ge_41).count())
print("→ In SQL docs this is EXCEPT / EXCEPT DISTINCT, not a method called except()")

# COMMAND ----------

# DBTITLE 1,Practice
# MAGIC %md
# MAGIC ## Practice — predict and verify
# MAGIC
# MAGIC Sections 1–2 used landing filters for distinct set ops and separate handmade
# MAGIC frames for `*All`. Now apply **both** ideas on one new multiset pair:
# MAGIC
# MAGIC | Frame | `trip_id` values |
# MAGIC |---|---|
# MAGIC | `left_ms` | 5, 5, 5, 6, 7 |
# MAGIC | `right_ms` | 5, 5, 7, 8 |
# MAGIC
# MAGIC Predict before you run:
# MAGIC
# MAGIC | Step | Your prediction |
# MAGIC |---|---:|
# MAGIC | `intersect` count | ? |
# MAGIC | `intersectAll` count | ? |
# MAGIC | `subtract` count | ? |
# MAGIC | `exceptAll` count | ? |
# MAGIC
# MAGIC Hint: shared values are `5` and `7`. Count how many copies survive under
# MAGIC distinct vs multiset rules.

# COMMAND ----------

# DBTITLE 1,Practice — multiset set ops
# TODO (practice):
# 1. Create left_ms: trip_ids 5, 5, 5, 6, 7 (column: trip_id only)
# 2. Create right_ms: trip_ids 5, 5, 7, 8 (column: trip_id only)
# 3. Print counts for intersect, intersectAll, subtract, exceptAll
# 4. Do the four counts match your predictions?


# COMMAND ----------

# DBTITLE 1,Summary
# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC 1. **`intersect`** — rows in both sides; distinct result (`INTERSECT`).
# MAGIC
# MAGIC 2. **`intersectAll`** — rows in both sides; keeps overlapping duplicate
# MAGIC    counts (`INTERSECT ALL`).
# MAGIC
# MAGIC 3. **`subtract`** — left-only rows; distinct result (`EXCEPT` /
# MAGIC    `EXCEPT DISTINCT`). No DataFrame method named `except`.
# MAGIC
# MAGIC 4. **`exceptAll`** — left-only rows; multiset difference (`EXCEPT ALL`).
# MAGIC
# MAGIC 5. Set ops compare **whole rows**. For key-only gaps, prefer semi/anti joins
# MAGIC    (Notebook **04**) or `select` the key columns before `subtract`.
# MAGIC
# MAGIC **Next:** **`07 - Build Unified Curated Tables`**
