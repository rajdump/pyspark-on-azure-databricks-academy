# Module 9 — Spark SQL and DataFrame Interoperability

## Purpose

Re-express DataFrame-based rideshare analytics in Spark SQL and choose
deliberate SQL–DataFrame interoperability patterns.

## Learning objectives

By the end of this module, you'll be able to:

- Choose among direct `%sql`, `spark.table`, `spark.sql`→DataFrame, and
  DF→`createOrReplaceTempView` for a given task
- Write SQL joins with qualified aliases, `CASE WHEN`, `COALESCE`,
  `GROUP BY`, and `HAVING` (including compound predicates)
- Reshape with SQL `PIVOT` / `UNPIVOT` and contrast SQL `TABLESAMPLE` with
  seeded DataFrame sampling
- Rank and filter with window `OVER` + `QUALIFY`, and compute running
  totals / `LAG` on daily KPI grain
- Compose multi-step logic with CTEs and safe named `:params` (not
  f-string SQL)
- Rebuild Module 8 KPI contracts in Spark SQL (read-only; no writes)

## Prerequisites

Complete Module 8 notebooks **`01`–`08`**. You need:

| Asset | Rows / notes | Source |
|---|---|---|
| `rideshare_dev.processed.trip_enriched` | 106 — one per `trip_id`; 16 columns | Module 7 `07 - Build Unified Curated Tables.py` |
| `rideshare_dev.processed.trip_driver_assignment` | 100 — one per (`driver_id`, `trip_id`); trips 1–100; trips **101–106** have no driver | Module 7 `07 - Build Unified Curated Tables.py` |
| `rideshare_dev.processed.kpi_daily_trip_summary` | 14 — one per `trip_date` | Module 8 `08 - Build KPI Tables.py` |
| `rideshare_dev.processed.kpi_zone_performance` | 20 — one per (`pickup_borough`, `pickup_zone`) | Module 8 `08 - Build KPI Tables.py` |

Also recall: Module 2 `06 - Querying DataFrames with SQL.py` (temp views /
`%sql` / `spark.sql`); Module 7 join patterns; Module 8 aggregates, pivot,
windows, and KPI formulas — this module **re-expresses**, it does not
re-teach.

Does **not** write managed tables or touch
`/Volumes/rideshare_dev/processed/output_files/practice/` /
`/Volumes/rideshare_dev/processed/output_files/curated/`.

## Paths and outputs

Schemas, join keys, and KPI contracts:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md) and
Module 8 [`README.md`](../08%20-%20Aggregations%20and%20Window%20Functions/README.md)
(Paths and outputs).

| Role | Location |
|---|---|
| Reads | Unity Catalog managed tables listed above |
| Writes | **None** to managed tables — session temp views only (`03 - SQL Pivot, Unpivot, and Sampling.py`) |

`06 - End-to-End SQL Pipeline.py` rebuilds the three KPI contracts in Spark
SQL from `trip_enriched` and `trip_driver_assignment`. Read-only — no writes.

**Cleanup:** Module 5 `99 - Rideshare Project Cleanup and Reset.py` Level 4
drops these managed tables with the rest of `rideshare_dev`. This module
creates nothing durable to tear down.

## Notebooks

Six notebooks, in order. Notebooks **01–05** each end with a short SQL
exercise. `06 - End-to-End SQL Pipeline.py` has **no exercise** (the three
KPI rebuilds are the synthesis).

| # | Notebook | Reads | Focus |
|---|---|---|---|
| 01 | Dual API Foundations and When to Choose | `trip_enriched` | UC `%sql` + `spark.table`; `spark.sql`→DF; row-level `CASE` → `tip_amount_band` (≠ Module 6 percent `tip_band`); DF→temp view; when-to-choose table. **No `GROUP BY`.** Locked bands: zero 26 / low 40 / medium 20 / high 18 / no_data 2. Exercise → **43** Manhattan known-tip rows |
| 02 | SQL Joins, Aggregations, and Filtering | `trip_enriched`, `trip_driver_assignment` | Layered arc: projection → service `tier` CASE → `COALESCE` → JOIN (deliberate `AMBIGUOUS_REFERENCE` then fix) → first `GROUP BY` → `HAVING`. Side path: `NOT EXISTS` undriven (**6**). After JOIN: high 15 / standard 64 / other 21. Exercise: compound `HAVING` + undriven ids |
| 03 | SQL Pivot, Unpivot, and Sampling | `trip_enriched` | Borough×service counts (**18**) → `PIVOT` service columns → `COALESCE` zeros + SQL `TEMP VIEW` → `UNPIVOT` back to rows; brief non-deterministic `TABLESAMPLE`. Exercise: `payment_method` reshape by borough |
| 04 | SQL Windows and QUALIFY | `kpi_zone_performance`, `kpi_daily_trip_summary` | Part 1: `ROW_NUMBER` + `QUALIFY` Top-2 by tip (**9** rows) + subquery equivalent. Part 2: running distance + `LAG` + direction `CASE`. Exercise: Top-2 by `trip_count` with `WHERE` + `QUALIFY` → **8** rows |
| 05 | CTEs and Parameterized SQL | `trip_enriched` | Single CTE → multi-CTE tip-share → nested-subquery contrast → `:borough` params (anti f-string) → CTE + params. Exercise: borough daily tip as share of fleet daily |
| 06 | End-to-End SQL Pipeline | `trip_enriched`, `trip_driver_assignment` | Rebuild daily / zone / driver KPIs in `%sql` (layered steps). No writes. No exercise. Phase II synthesis; next is Module 10 (Phase III) |

## Minimum privileges required

- Unity Catalog (no catalog/schema/table DDL, no managed-table writes):
  - **`USE CATALOG`** on **`rideshare_dev`**
  - **`USE SCHEMA`** on **`rideshare_dev.processed`**
  - **`SELECT`** on:
    - `rideshare_dev.processed.trip_enriched`
    - `rideshare_dev.processed.trip_driver_assignment`
    - `rideshare_dev.processed.kpi_daily_trip_summary`
    - `rideshare_dev.processed.kpi_zone_performance`
  - Session **`CREATE OR REPLACE TEMP VIEW`** is allowed
    (`03 - SQL Pivot, Unpivot, and Sampling.py`); that is not schema/table
    DDL on `rideshare_dev.processed`
- Workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the compute used here
