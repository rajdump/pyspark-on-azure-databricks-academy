# Databricks notebook source
# MAGIC %md
# MAGIC # 02 - SQL Joins, Aggregations, and Filtering
# MAGIC
# MAGIC In this notebook, we'll build one SQL query step by step — starting with
# MAGIC trip-level columns and ending with a **driven-trip** tier summary filtered
# MAGIC by `HAVING`.
# MAGIC
# MAGIC Along the way, we'll also handle a common JOIN problem: two tables containing
# MAGIC the same column name.
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC - Add row-level categories with `CASE WHEN`
# MAGIC - Replace NULL values with `COALESCE`
# MAGIC - Join tables using clear SQL aliases
# MAGIC - Resolve ambiguous column references after a JOIN
# MAGIC - Aggregate joined data with `GROUP BY`
# MAGIC - Filter aggregated results with `HAVING`
# MAGIC - Find rows with no matching record using `NOT EXISTS`
# MAGIC
# MAGIC **Callbacks:** Module 7 join notebooks; Module 8 `01 - GroupBy and Basic
# MAGIC Aggregations` and `02 - Multi-column Keys, NULL Groups, and Filter
# MAGIC Placement`. This notebook is the Spark SQL spelling — not a re-teach.
# MAGIC
# MAGIC **Reads:**
# MAGIC - `rideshare_dev.processed.trip_enriched` — **106 rows**
# MAGIC - `rideshare_dev.processed.trip_driver_assignment` — **100 rows**
# MAGIC
# MAGIC **Writes:** None.
# MAGIC
# MAGIC **Prerequisites:** Module 9 `01 - Dual API Foundations and When to Choose`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup — load both tables
# MAGIC
# MAGIC We'll join two managed tables:
# MAGIC
# MAGIC - `trip_enriched` — **106 trips**
# MAGIC - `trip_driver_assignment` — driver assignments for **100 trips**
# MAGIC
# MAGIC Trips **101–106** have no driver assignment.
# MAGIC
# MAGIC Both tables also contain `service_type`. That shared name matters at the
# MAGIC JOIN.

# COMMAND ----------

trip_enriched = spark.table("rideshare_dev.processed.trip_enriched")  # noqa: F821
trip_driver_assignment = spark.table(  # noqa: F821
    "rideshare_dev.processed.trip_driver_assignment"
)

print(f"trip_enriched: {trip_enriched.count()} rows")  # expect 106
print(f"trip_driver_assignment: {trip_driver_assignment.count()} rows")  # expect 100

# COMMAND ----------

# MAGIC %md
# MAGIC ## Main arc — build the query step by step
# MAGIC
# MAGIC We'll start with all trips and add one SQL concept at a time until we have
# MAGIC a driven-trip tier aggregate — then filter those groups with `HAVING`.
# MAGIC
# MAGIC Each step keeps the previous logic and introduces one new piece.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 1 — Start with the base columns
# MAGIC
# MAGIC Begin with the trip-level columns needed for the rest of the query.
# MAGIC
# MAGIC We intentionally keep NULL values visible for now:
# MAGIC
# MAGIC - `tip_amount` is NULL for trips **103** and **106**
# MAGIC - `base_fare_amount` is NULL for trips **104** and **106**
# MAGIC
# MAGIC No filtering or grouping yet — result stays at **106 rows**.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT trip_id, service_type, tip_amount, base_fare_amount
# MAGIC FROM rideshare_dev.processed.trip_enriched

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2 — Classify `service_type` into a tier
# MAGIC
# MAGIC Add a row-level `CASE WHEN` (same idea as
# MAGIC `01 - Dual API Foundations and When to Choose`, new labels).
# MAGIC
# MAGIC | `service_type` | `tier` |
# MAGIC |---|---|
# MAGIC | `PREMIUM` | `high` |
# MAGIC | `STANDARD`, `XL` | `standard` |
# MAGIC | Anything else | `other` |
# MAGIC
# MAGIC Each trip gets a `tier` label — the result is still **106 rows**.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   trip_id,
# MAGIC   service_type,
# MAGIC   tip_amount,
# MAGIC   base_fare_amount,
# MAGIC   CASE
# MAGIC     WHEN service_type = 'PREMIUM' THEN 'high'
# MAGIC     WHEN service_type IN ('STANDARD', 'XL') THEN 'standard'
# MAGIC     ELSE 'other'
# MAGIC   END AS tier
# MAGIC FROM rideshare_dev.processed.trip_enriched

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 3 — Replace NULL tips with `COALESCE`
# MAGIC
# MAGIC Add `COALESCE(tip_amount, 0) AS safe_tip`.
# MAGIC
# MAGIC `COALESCE` does **not** remove rows. It keeps every trip and substitutes
# MAGIC `0` when `tip_amount` is NULL.
# MAGIC
# MAGIC Look at trips **103** and **106** in the result:
# MAGIC
# MAGIC - `tip_amount` stays NULL (raw value)
# MAGIC - `safe_tip` shows `0` (substituted value)
# MAGIC
# MAGIC Row count is still **106**. We add `COALESCE` here — before the JOIN —
# MAGIC while those NULL tips are still visible.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   trip_id,
# MAGIC   service_type,
# MAGIC   tip_amount,
# MAGIC   base_fare_amount,
# MAGIC   CASE
# MAGIC     WHEN service_type = 'PREMIUM' THEN 'high'
# MAGIC     WHEN service_type IN ('STANDARD', 'XL') THEN 'standard'
# MAGIC     ELSE 'other'
# MAGIC   END AS tier,
# MAGIC   COALESCE(tip_amount, 0) AS safe_tip
# MAGIC FROM rideshare_dev.processed.trip_enriched

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 4 — Join the driver assignment table
# MAGIC
# MAGIC Restrict the report to **driven trips** — trips that have a row in
# MAGIC `trip_driver_assignment` — with an `INNER JOIN` on `trip_id`.
# MAGIC
# MAGIC Alias `d` is used only in the `ON` clause (an existence filter). We do not
# MAGIC select columns from the assignment table.
# MAGIC
# MAGIC Both tables contain `service_type`, so after the JOIN a bare
# MAGIC `service_type` is no longer specific enough.
# MAGIC
# MAGIC The next query is **intentionally incorrect**: JOIN aliases are defined,
# MAGIC but the `CASE WHEN` still uses bare `service_type`. Expect an ambiguous
# MAGIC column reference error (`AMBIGUOUS_REFERENCE` or the Spark 4 equivalent).

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   t.trip_id,
# MAGIC   tip_amount,
# MAGIC   base_fare_amount,
# MAGIC   CASE
# MAGIC     WHEN service_type = 'PREMIUM' THEN 'high'
# MAGIC     WHEN service_type IN ('STANDARD', 'XL') THEN 'standard'
# MAGIC     ELSE 'other'
# MAGIC   END AS tier,
# MAGIC   COALESCE(tip_amount, 0) AS safe_tip
# MAGIC FROM rideshare_dev.processed.trip_enriched AS t
# MAGIC INNER JOIN rideshare_dev.processed.trip_driver_assignment AS d
# MAGIC   ON t.trip_id = d.trip_id

# COMMAND ----------

# MAGIC %md
# MAGIC #### Fix the ambiguous reference
# MAGIC
# MAGIC Qualify which `service_type` Spark should read: `t.service_type`.
# MAGIC Qualify the other trip columns with `t.` for consistency — the SELECT list
# MAGIC is still trip columns only.
# MAGIC
# MAGIC The `INNER JOIN` keeps only driven trips.
# MAGIC
# MAGIC **Expected:** **100 rows** — undriven trips **101–106** are removed.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   t.trip_id,
# MAGIC   t.tip_amount,
# MAGIC   t.base_fare_amount,
# MAGIC   CASE
# MAGIC     WHEN t.service_type = 'PREMIUM' THEN 'high'
# MAGIC     WHEN t.service_type IN ('STANDARD', 'XL') THEN 'standard'
# MAGIC     ELSE 'other'
# MAGIC   END AS tier,
# MAGIC   COALESCE(t.tip_amount, 0) AS safe_tip
# MAGIC FROM rideshare_dev.processed.trip_enriched AS t
# MAGIC INNER JOIN rideshare_dev.processed.trip_driver_assignment AS d
# MAGIC   ON t.trip_id = d.trip_id

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 5 — Aggregate by tier
# MAGIC
# MAGIC Until now, the query returned one row per driven trip. `GROUP BY` changes
# MAGIC the result to one row per `tier`.
# MAGIC
# MAGIC For each tier we calculate trip count, average tip, and total base fare.
# MAGIC
# MAGIC Group with `GROUP BY tier` (Spark allows the select alias). Repeating the
# MAGIC full `CASE` in `GROUP BY` also works in dialects that disallow aliases.
# MAGIC
# MAGIC **Expected:**
# MAGIC
# MAGIC | `tier` | `trip_count` | `total_base_fare` |
# MAGIC |---|---:|---:|
# MAGIC | `high` | 15 | 966.75 |
# MAGIC | `standard` | 64 | 1970.15 |
# MAGIC | `other` | 21 | 308.68 |

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   CASE
# MAGIC     WHEN t.service_type = 'PREMIUM' THEN 'high'
# MAGIC     WHEN t.service_type IN ('STANDARD', 'XL') THEN 'standard'
# MAGIC     ELSE 'other'
# MAGIC   END AS tier,
# MAGIC   COUNT(*) AS trip_count,
# MAGIC   ROUND(AVG(COALESCE(t.tip_amount, 0)), 2) AS avg_tip,
# MAGIC   SUM(t.base_fare_amount) AS total_base_fare
# MAGIC FROM rideshare_dev.processed.trip_enriched AS t
# MAGIC INNER JOIN rideshare_dev.processed.trip_driver_assignment AS d
# MAGIC   ON t.trip_id = d.trip_id
# MAGIC GROUP BY tier

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 6 — `COALESCE` vs `WHERE`
# MAGIC
# MAGIC `COALESCE` and `WHERE ... IS NOT NULL` solve different problems:
# MAGIC
# MAGIC | Approach | What happens |
# MAGIC |---|---|
# MAGIC | `COALESCE(tip_amount, 0)` | Keep the row; substitute `0` for a NULL tip |
# MAGIC | `WHERE tip_amount IS NOT NULL` | Remove rows whose tip is NULL |
# MAGIC
# MAGIC In this dataset, both NULL-tip trips (**103** and **106**) have no driver
# MAGIC assignment. The `INNER JOIN` already removed them, so after the JOIN:
# MAGIC
# MAGIC - `COALESCE` no longer changes any tip values
# MAGIC - `WHERE tip_amount IS NOT NULL` would remove no additional rows
# MAGIC
# MAGIC Tier counts stay **15 / 64 / 21**. That is why we showed `COALESCE` in
# MAGIC Step 3 on the raw **106-row** table — while the NULLs were still visible.
# MAGIC
# MAGIC We don't rerun SQL here — the result would match Step 5. The semantics
# MAGIC still differ even when this JOIN makes the outputs match.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 7 — Filter aggregated groups with `HAVING`
# MAGIC
# MAGIC `WHERE` filters rows **before** aggregation. `HAVING` filters groups
# MAGIC **after** aggregation.
# MAGIC
# MAGIC Keep tiers whose total base fare is greater than `500`.
# MAGIC
# MAGIC Callback: Module 8 `02 - Multi-column Keys, NULL Groups, and Filter
# MAGIC Placement`.
# MAGIC
# MAGIC **Expected:** **2 rows** — `other` drops (total base fare **308.68**).

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   CASE
# MAGIC     WHEN t.service_type = 'PREMIUM' THEN 'high'
# MAGIC     WHEN t.service_type IN ('STANDARD', 'XL') THEN 'standard'
# MAGIC     ELSE 'other'
# MAGIC   END AS tier,
# MAGIC   COUNT(*) AS trip_count,
# MAGIC   ROUND(AVG(COALESCE(t.tip_amount, 0)), 2) AS avg_tip,
# MAGIC   SUM(t.base_fare_amount) AS total_base_fare
# MAGIC FROM rideshare_dev.processed.trip_enriched AS t
# MAGIC INNER JOIN rideshare_dev.processed.trip_driver_assignment AS d
# MAGIC   ON t.trip_id = d.trip_id
# MAGIC GROUP BY tier
# MAGIC HAVING SUM(t.base_fare_amount) > 500

# COMMAND ----------

# MAGIC %md
# MAGIC ## Side path — find trips with no driver assignment
# MAGIC
# MAGIC Not every question needs aggregation. To find trips with **no** matching
# MAGIC row in `trip_driver_assignment`, use `NOT EXISTS`.
# MAGIC
# MAGIC For each trip, Spark checks whether a matching `trip_id` exists in the
# MAGIC assignment table and keeps the trip only when no match is found.
# MAGIC
# MAGIC **Expected:** **6 trips** — `101` through `106`.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT t.trip_id
# MAGIC FROM rideshare_dev.processed.trip_enriched AS t
# MAGIC WHERE NOT EXISTS (
# MAGIC   SELECT 1
# MAGIC   FROM rideshare_dev.processed.trip_driver_assignment AS d
# MAGIC   WHERE d.trip_id = t.trip_id
# MAGIC )
# MAGIC ORDER BY t.trip_id

# COMMAND ----------

# MAGIC %md
# MAGIC `LEFT ANTI JOIN` asks the same high-level question: keep left-side rows with
# MAGIC no match on the right. Module 7 used that pattern in the DataFrame API;
# MAGIC here `NOT EXISTS` is the SQL form.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC ### Q1 — Filter aggregated tiers
# MAGIC
# MAGIC Using **driven trips only**, return tiers that satisfy both:
# MAGIC
# MAGIC - more than **20 trips**
# MAGIC - total base fare greater than **300**
# MAGIC
# MAGIC Use table aliases, `JOIN`, `CASE WHEN`, `GROUP BY`, and compound `HAVING`.
# MAGIC
# MAGIC **Expected:** **2 rows**
# MAGIC
# MAGIC - `standard` — 64 trips
# MAGIC - `other` — 21 trips
# MAGIC
# MAGIC ### Q2 — Find undriven trips
# MAGIC
# MAGIC Use `NOT EXISTS` to return trips with no driver assignment.
# MAGIC
# MAGIC **Expected:** **6 `trip_id`s** — `101–106`.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Q1: compound HAVING on driven trips (expect 2 rows: standard, other)
# MAGIC SELECT
# MAGIC   CASE
# MAGIC     WHEN t.service_type = 'PREMIUM' THEN 'high'
# MAGIC     WHEN t.service_type IN ('STANDARD', 'XL') THEN 'standard'
# MAGIC     ELSE 'other'
# MAGIC   END AS tier,
# MAGIC   COUNT(*) AS trip_count,
# MAGIC   SUM(t.base_fare_amount) AS total_base_fare
# MAGIC FROM rideshare_dev.processed.trip_enriched AS t
# MAGIC INNER JOIN rideshare_dev.processed.trip_driver_assignment AS d
# MAGIC   ON t.trip_id = d.trip_id
# MAGIC GROUP BY tier
# MAGIC HAVING 1 = 0  -- TODO: compound HAVING (trip count and total base fare)

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Q2: undriven trip_ids via NOT EXISTS (expect 6 rows: 101–106)
# MAGIC SELECT t.trip_id
# MAGIC FROM rideshare_dev.processed.trip_enriched AS t
# MAGIC WHERE 1 = 0  -- TODO: NOT EXISTS (... trip_driver_assignment ...)
# MAGIC ORDER BY t.trip_id

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC One SQL query grew into a driven-trip tier summary:
# MAGIC
# MAGIC `SELECT` → `CASE WHEN` → `COALESCE` → `JOIN` → `GROUP BY` → `HAVING`
# MAGIC
# MAGIC Key takeaways:
# MAGIC
# MAGIC - `INNER JOIN` to assignment restricts to driven trips (`d` in `ON` only)
# MAGIC - Qualify shared column names after a JOIN (`t.service_type`)
# MAGIC - `COALESCE` keeps a row and substitutes; `WHERE` can remove the row
# MAGIC - `GROUP BY tier` changes driven-trip grain to tier grain
# MAGIC - `HAVING` filters aggregated groups
# MAGIC - `NOT EXISTS` finds undriven trips
# MAGIC
# MAGIC **Next:** `03 - SQL Pivot, Unpivot, and Sampling` reshapes aggregated data
# MAGIC between long and wide forms.
