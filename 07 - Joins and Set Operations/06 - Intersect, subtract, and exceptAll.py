# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC # 06 - Intersect, subtract, and exceptAll
# MAGIC
# MAGIC Notebook **05** stacked DataFrames with `union` / `unionByName`. This
# MAGIC notebook covers the remaining set operations: keep rows on **both** sides,
# MAGIC or keep rows on **one** side only.
# MAGIC
# MAGIC | Section | Focus |
# MAGIC |---|---|
# MAGIC | 1 | `intersect` vs `intersectAll` |
# MAGIC | 2 | `subtract` vs `exceptAll` |
# MAGIC | Practice | Predict multiset counts on a new pair |
# MAGIC
# MAGIC **Prerequisites.** Module 7 **`01`–`05`**. **No write.**

# COMMAND ----------

# DBTITLE 1,Set-op rules
# MAGIC %md
# MAGIC ## Set-op rules
# MAGIC
# MAGIC 1. Set ops compare **whole rows** (every selected column), not a join key.
# MAGIC 2. `intersect` / `subtract` remove duplicates from the result (distinct semantics).
# MAGIC 3. `intersectAll` / `exceptAll` preserve duplicate **counts** (multiset semantics).
# MAGIC 4. Columns align by **position** (same as `union`), not by name.
# MAGIC
# MAGIC **SQL name mapping:**
# MAGIC
# MAGIC | SQL | DataFrame API |
# MAGIC |---|---|
# MAGIC | `INTERSECT` | `intersect()` |
# MAGIC | `INTERSECT ALL` | `intersectAll()` |
# MAGIC | `EXCEPT` / `EXCEPT DISTINCT` | `subtract()` |
# MAGIC | `EXCEPT ALL` | `exceptAll()` |
# MAGIC
# MAGIC There is no DataFrame method named `except`. Use `subtract()`.

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

print("intersect (distinct):")
left_dup.intersect(right_dup).orderBy("trip_id").show()

print("intersectAll (keeps overlapping copies):")
left_dup.intersectAll(right_dup).orderBy("trip_id").show()
print("→ trip_id 1 appears twice on both sides → intersectAll keeps 2 copies")

# COMMAND ----------

# DBTITLE 1,2. subtract vs exceptAll
# MAGIC %md
# MAGIC ## 2. `subtract` vs `exceptAll`
# MAGIC
# MAGIC `subtract()` returns rows in the **left** DataFrame that do not appear in
# MAGIC the right. Duplicates are removed from the result.
# MAGIC
# MAGIC `exceptAll()` is the multiset version — it subtracts matching copies from
# MAGIC the right, one for one, and keeps any remaining left-side copies.

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
# MAGIC 1. **`intersect`** — rows in both sides; distinct result.
# MAGIC
# MAGIC 2. **`intersectAll`** — rows in both sides; preserves duplicate counts.
# MAGIC
# MAGIC 3. **`subtract`** — left-only rows; distinct result.
# MAGIC
# MAGIC 4. **`exceptAll`** — left-only rows; preserves duplicate counts.
# MAGIC
# MAGIC Set ops compare **whole rows**. For key-only gaps, `select` the key column
# MAGIC before calling `subtract`, or use semi/anti joins (Notebook **04**).
# MAGIC
# MAGIC **Next:** **`07 - Build Unified Curated Tables`**