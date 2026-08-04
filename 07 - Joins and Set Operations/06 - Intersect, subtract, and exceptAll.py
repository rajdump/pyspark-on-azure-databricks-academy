# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC # 06 - Intersect, subtract, and exceptAll
# MAGIC
# MAGIC Notebook **05** stacked DataFrames with `union` / `unionByName`. This
# MAGIC notebook covers the other whole-row set operations: keep rows on **both**
# MAGIC sides, or keep rows on **one** side only.
# MAGIC
# MAGIC These APIs compare **entire rows**, not a join key. Notebook **04**
# MAGIC previewed `subtract()` next to `left_anti` — here you get the full family,
# MAGIC including `*All` variants that preserve duplicate counts.
# MAGIC
# MAGIC | Section | Focus |
# MAGIC |---|---|
# MAGIC | 1 | `intersect` vs `intersectAll` |
# MAGIC | 2 | `subtract` vs `exceptAll` |
# MAGIC | 3 | SQL `EXCEPT` naming vs DataFrame API |
# MAGIC | Practice | Predict multiset set-op counts |
# MAGIC
# MAGIC **Prerequisites.** Module 7 **`01`–`05`**. **No write.**

# COMMAND ----------

# DBTITLE 1,Set-op rules
# MAGIC %md
# MAGIC ## Set-op rules
# MAGIC
# MAGIC 1. Set ops compare **whole rows** (every selected column), not a join key.
# MAGIC 2. `intersect` / `subtract` return **distinct** results.
# MAGIC 3. `intersectAll` / `exceptAll` preserve duplicate **counts**.
# MAGIC 4. Columns align by **position** (same idea as `union`), not by name.
# MAGIC 5. SQL `EXCEPT` / `EXCEPT DISTINCT` ↔ DataFrame `subtract()` — there is no
# MAGIC    method named `except()`.

# COMMAND ----------

# DBTITLE 1,Setup
# MAGIC %md
# MAGIC ## Setup — constructed frames
# MAGIC
# MAGIC Tiny handmade DataFrames — same pattern as Notebook **05**. No landing or
# MAGIC curated read.
# MAGIC
# MAGIC | Frame | `trip_id` values |
# MAGIC |---|---|
# MAGIC | `left_ids` | 1, 2, 3 |
# MAGIC | `right_ids` | 2, 3, 4 |
# MAGIC
# MAGIC Overlap: `2`, `3`. Left-only: `1`. Right-only: `4`.

# COMMAND ----------

# DBTITLE 1,Create left_ids and right_ids
left_ids = spark.createDataFrame(  # noqa: F821
    [(1,), (2,), (3,)],
    ["trip_id"],
)
right_ids = spark.createDataFrame(  # noqa: F821
    [(2,), (3,), (4,)],
    ["trip_id"],
)

print("left_ids:")
left_ids.show()
print("right_ids:")
right_ids.show()

# COMMAND ----------

# DBTITLE 1,1. intersect vs intersectAll
# MAGIC %md
# MAGIC ## 1. `intersect` vs `intersectAll`
# MAGIC
# MAGIC `intersect()` returns rows that appear in **both** DataFrames and removes
# MAGIC duplicates. It matches SQL `INTERSECT`.
# MAGIC
# MAGIC `intersectAll()` also keeps only shared rows, but preserves how many times a
# MAGIC row can appear — limited by the **smaller** count on either side. It matches
# MAGIC SQL `INTERSECT ALL`.

# COMMAND ----------

# DBTITLE 1,1. intersect — shared trip_ids
shared = left_ids.intersect(right_ids)

print("intersect rows:", shared.count())  # 2 and 3 → 2
shared.orderBy("trip_id").show()

# COMMAND ----------

# DBTITLE 1,1b. intersect vs intersectAll with duplicates
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
# MAGIC `subtract()` returns rows in the **left** DataFrame that do not appear on the
# MAGIC right, and removes duplicates. It matches SQL `EXCEPT` / `EXCEPT DISTINCT`.
# MAGIC
# MAGIC `exceptAll()` is the same idea but preserves leftover duplicate counts on the
# MAGIC left. It matches SQL `EXCEPT ALL`.
# MAGIC
# MAGIC Notebook **04** contrasted `left_anti` (join key; keeps left duplicates) with
# MAGIC `subtract()` (whole selected row; distinct result). This section is the full
# MAGIC treatment.

# COMMAND ----------

# DBTITLE 1,2. subtract — direction matters
only_left = left_ids.subtract(right_ids)  # 1
only_right = right_ids.subtract(left_ids)  # 4

print("left_ids.subtract(right_ids):")
only_left.show()
print("right_ids.subtract(left_ids):")
only_right.show()
print("→ Which DataFrame is left decides which leftover you get")

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
print("left_ids.subtract(right_ids) count:", left_ids.subtract(right_ids).count())
print("→ In SQL docs this is EXCEPT / EXCEPT DISTINCT, not except()")

# COMMAND ----------

# DBTITLE 1,Practice
# MAGIC %md
# MAGIC ## Practice — predict and verify
# MAGIC
# MAGIC Create a new multiset pair and apply all four APIs:
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
# MAGIC 1. **`intersect`** — rows on both sides; distinct result (`INTERSECT`).
# MAGIC
# MAGIC 2. **`intersectAll`** — rows on both sides; keeps overlapping duplicate
# MAGIC    counts (`INTERSECT ALL`).
# MAGIC
# MAGIC 3. **`subtract`** — left-only rows; distinct result (`EXCEPT` /
# MAGIC    `EXCEPT DISTINCT`). No DataFrame method named `except`.
# MAGIC
# MAGIC 4. **`exceptAll`** — left-only rows; multiset difference (`EXCEPT ALL`).
# MAGIC
# MAGIC 5. Set ops compare **whole rows**. For key-only gaps, prefer semi/anti joins
# MAGIC    (Notebook **04**) or `select` the comparison columns first.
# MAGIC
# MAGIC **Next:** **`07 - Build Unified Curated Tables`**
