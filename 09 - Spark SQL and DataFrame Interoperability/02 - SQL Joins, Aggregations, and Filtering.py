# Databricks notebook source
# MAGIC %md
# MAGIC # 02 - SQL Joins, Aggregations, and Filtering
# MAGIC
# MAGIC Build one evolving SQL query that an analyst would hand to a reporting
# MAGIC layer — then a short side path for existence checks.
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC - Layer projection → `CASE` → `COALESCE` → JOIN → `GROUP BY` → `HAVING`
# MAGIC - Qualify ambiguous columns with table aliases (one intentional error)
# MAGIC - Filter groups with `HAVING`; find missing keys with `NOT EXISTS`
# MAGIC
# MAGIC **Main arc:** one query that grows cell by cell (full statement each step
# MAGIC after the base projection). **Side path:** `NOT EXISTS` for undriven trips.
# MAGIC
# MAGIC **Callbacks:** Module 7 join notebooks; Module 8 `01 - GroupBy and Basic
# MAGIC Aggregations` and `02 - Multi-column Keys, NULL Groups, and Filter
# MAGIC Placement`. Do not re-teach those APIs — this notebook is the SQL spelling.
# MAGIC
# MAGIC **Reads:** `trip_enriched` (106), `trip_driver_assignment` (100). **No writes.**
# MAGIC
# MAGIC **Prerequisites:** Module 9 `01 - Dual API Foundations and When to Choose`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup — load both tables
# MAGIC
# MAGIC Trips **101–106** have no row in `trip_driver_assignment`.
# MAGIC Both tables include `service_type` — that collision matters at the JOIN.

# COMMAND ----------

trip_enriched = spark.table("rideshare_dev.processed.trip_enriched")  # noqa: F821
trip_driver_assignment = spark.table(  # noqa: F821
    "rideshare_dev.processed.trip_driver_assignment"
)

print(f"trip_enriched: {trip_enriched.count()} rows")  # expect 106
print(
    f"trip_driver_assignment: {trip_driver_assignment.count()} rows"
)  # expect 100

# COMMAND ----------

# MAGIC %md
# MAGIC ## Main arc — layered aggregate query
# MAGIC
# MAGIC After Step 1, each SQL cell shows the **full** statement. Call out only
# MAGIC what is new.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 1 — Base projection (NULLs visible)
# MAGIC
# MAGIC Start from raw columns — **no tip filter yet**, so NULL tips and fares stay
# MAGIC visible. Tip NULL on trips **103** and **106**; base fare NULL on **104**
# MAGIC and **106**. **106** rows.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT trip_id, service_type, tip_amount, base_fare_amount
# MAGIC FROM rideshare_dev.processed.trip_enriched

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2 — CASE → tier (still row grain)
# MAGIC
# MAGIC Reuse the `01 - Dual API Foundations and When to Choose` `CASE` idea in a
# MAGIC new context: map `service_type` to `tier`. Still **106** rows — labeling,
# MAGIC not grouping.
# MAGIC
# MAGIC | `service_type` | `tier` |
# MAGIC |---|---|
# MAGIC | `PREMIUM` | `high` |
# MAGIC | `STANDARD`, `XL` | `standard` |
# MAGIC | else | `other` |

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
# MAGIC ### Step 3 — COALESCE while NULLs remain
# MAGIC
# MAGIC **What's new:** `COALESCE(tip_amount, 0) AS safe_tip`. Former NULL tips
# MAGIC show as `0` because we have not filtered them yet.

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
# MAGIC ### Step 4 — JOIN + ambiguous column lesson
# MAGIC
# MAGIC Add driver assignment with an INNER JOIN. Both tables have `service_type`.
# MAGIC
# MAGIC The next cell is **intentionally broken**: the JOIN and aliases are
# MAGIC correct, but the `CASE` still uses bare `service_type`. Expect
# MAGIC `AMBIGUOUS_REFERENCE` (or the Spark 4 equivalent). Run it to see the error.

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
# MAGIC **Fix:** qualify as `t.service_type` (and qualify tip/fare columns from `t`).
# MAGIC One deliberate break only — do not invent a second error.
# MAGIC
# MAGIC **Expected after the fix:** **100** rows (trips **101–106** drop).

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
# MAGIC ### Step 5 — First GROUP BY
# MAGIC
# MAGIC **What's new:** collapse to tier grain and alias aggregates.
# MAGIC
# MAGIC Spark SQL also accepts the select alias in `GROUP BY` (`GROUP BY tier`).
# MAGIC This notebook repeats the explicit `CASE` in `GROUP BY` for clarity —
# MAGIC both work.
# MAGIC
# MAGIC **Expected:** `high` 15 / `standard` 64 / `other` 21;
# MAGIC `total_base_fare` **966.75 / 1970.15 / 308.68**.

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
# MAGIC GROUP BY
# MAGIC   CASE
# MAGIC     WHEN t.service_type = 'PREMIUM' THEN 'high'
# MAGIC     WHEN t.service_type IN ('STANDARD', 'XL') THEN 'standard'
# MAGIC     ELSE 'other'
# MAGIC   END

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 6 — COALESCE vs WHERE (honest data note)
# MAGIC
# MAGIC In **this** dataset, the INNER JOIN already removed every NULL-tip row
# MAGIC (trips **103** and **106** are undriven). After the JOIN, `COALESCE` on tip
# MAGIC has no effect and `WHERE tip_amount IS NOT NULL` removes nothing — both
# MAGIC would still show **15 / 64 / 21**.
# MAGIC
# MAGIC **In production** with LEFT JOINs or incomplete tip data, you choose:
# MAGIC
# MAGIC | Approach | Effect |
# MAGIC |---|---|
# MAGIC | `COALESCE(tip, 0)` | Keep the row; substitute a value |
# MAGIC | `WHERE tip IS NOT NULL` | Drop the row |
# MAGIC
# MAGIC We showed `COALESCE` where it was visible — Step 3 on the raw **106** rows.
# MAGIC No second SQL cell here; do not fake a Strategy B that changes nothing.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 7 — HAVING
# MAGIC
# MAGIC **What's new:** `HAVING` filters **groups** after aggregation (`WHERE`
# MAGIC filters rows before). Callback: Module 8 `02 - Multi-column Keys, NULL
# MAGIC Groups, and Filter Placement`.
# MAGIC
# MAGIC **Expected:** **2** rows (`other` with base **308.68** drops).

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
# MAGIC GROUP BY
# MAGIC   CASE
# MAGIC     WHEN t.service_type = 'PREMIUM' THEN 'high'
# MAGIC     WHEN t.service_type IN ('STANDARD', 'XL') THEN 'standard'
# MAGIC     ELSE 'other'
# MAGIC   END
# MAGIC HAVING SUM(t.base_fare_amount) > 500

# COMMAND ----------

# MAGIC %md
# MAGIC ## Side path — existence (`NOT EXISTS`)
# MAGIC
# MAGIC Existence checks do not fold into the aggregate arc — separate query shape.
# MAGIC
# MAGIC **Expected:** **6** undriven `trip_id`s (**101–106**).

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
# MAGIC One-line awareness: Spark `LEFT ANTI JOIN` is an alternate spelling of the
# MAGIC same “rows with no match” idea.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC **Q1.** On **driven** trips only, which tiers have **more than 20 trips AND
# MAGIC total base fare greater than 300**?
# MAGIC Use `JOIN` + aliases + `CASE` + `GROUP BY` + a compound `HAVING`.
# MAGIC
# MAGIC **Expected:** **2** rows — `standard` (64, ~1970) and `other` (21, ~308).
# MAGIC
# MAGIC **Q2.** List undriven `trip_id`s with `NOT EXISTS`.
# MAGIC
# MAGIC **Expected:** **6** ids.

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
# MAGIC GROUP BY
# MAGIC   CASE
# MAGIC     WHEN t.service_type = 'PREMIUM' THEN 'high'
# MAGIC     WHEN t.service_type IN ('STANDARD', 'XL') THEN 'standard'
# MAGIC     ELSE 'other'
# MAGIC   END
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
# MAGIC - Qualify shared column names after a JOIN (`t.service_type`)
# MAGIC - `COALESCE` was visible on the raw 106 rows; no-op after this INNER JOIN
# MAGIC - First Module 9 `GROUP BY` (+ note: alias-in-`GROUP BY` also works)
# MAGIC - `HAVING` filters groups; `NOT EXISTS` finds undriven trips
# MAGIC
# MAGIC **Next:** `03 - SQL Pivot, Unpivot, and Sampling` — reshape long ↔ wide.
