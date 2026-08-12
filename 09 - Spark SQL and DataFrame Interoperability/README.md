# Module 9 — Spark SQL and DataFrame Interoperability

## Purpose

Express the same rideshare analytics in Spark SQL that Modules 7–8 already
built in the DataFrame API — and prove the two APIs agree by inspection.

**SQL-first.** No SQL→PySpark homework. Python `spark.table` setup appears in
every notebook. DataFrame **transforms** appear only in Notebook **01**
(SQL↔DF bridges). Notebook **05** uses Python solely to bind `:params` via
`spark.sql(..., args=...)`. Notebook **06** adds the parity inspection
helper. All other lesson cells are `%sql` or SQL text.

Two habits run through the module:

1. **Pick the entry point deliberately** — `%sql`, `spark.table`,
   `spark.sql`→DF, or DF→temp view — then stay consistent in that cell
2. **Layer the full statement** after Step 1 of a main arc; call out only
   what is new in each cell

**No managed-table writes.** Read-only consumers of Module 7 and Module 8
tables. Notebook **03** may create session temp views. Automated `assert` /
pytest-style checks → Module 17; Notebook **06** displays diffs only.

Schemas, join keys, and KPI contracts:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md) and
Module 8 [`README.md`](../08%20-%20Aggregations%20and%20Window%20Functions/README.md)
(Paths and outputs).

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
- Rebuild Module 8 KPI contracts in SQL and **inspect** parity vs managed
  tables (`exceptAll` diffs — no Python `assert`)

## Prerequisites

Complete Module 8 notebooks **`01`–`08`**. You need:

| Asset | Rows / notes | Source |
|---|---|---|
| `rideshare_dev.processed.trip_enriched` | 106 — one per `trip_id`; 16 columns | Module 7 **`07`** |
| `rideshare_dev.processed.trip_driver_assignment` | 100 — one per (`driver_id`, `trip_id`); trips 1–100; trips **101–106** have no driver | Module 7 **`07`** |
| `rideshare_dev.processed.kpi_daily_trip_summary` | 14 — one per `trip_date` | Module 8 **`08`** |
| `rideshare_dev.processed.kpi_zone_performance` | 20 — one per (`pickup_borough`, `pickup_zone`) | Module 8 **`08`** |
| `rideshare_dev.processed.kpi_driver_productivity` | 12 — one per `driver_id` + `distance_dense_rank` | Module 8 **`08`** |

Also recall: Module 2 `06 - Querying DataFrames with SQL` (temp views /
`%sql` / `spark.sql`); Module 7 join patterns; Module 8 aggregates, pivot,
windows, and KPI formulas — this module **re-expresses**, it does not
re-teach.

Does **not** write managed tables or touch `practice/` / `curated/`.

## Paths and outputs

| Role | Location |
|---|---|
| Reads | Unity Catalog managed tables listed above |
| Writes | **None** to managed tables — session temp views only (Notebook **03**) |

Notebook **06** rebuilds the three KPI contracts in SQL and compares to the
managed tables with a display-only `show_parity` helper. Expected result
when formulas match: matching row counts and empty bidirectional
`exceptAll` diffs.

**Cleanup:** Module 5 **`99`** Level 4 drops these managed tables with the
rest of `rideshare_dev`. This module creates nothing durable to tear down.

## Runtime and scope

**Runtime:** Spark **4.0.0** / DBR **17.3 LTS**.

**API:** Spark SQL first (`%sql` and `spark.sql`). See Purpose for where
Python is allowed.

**In scope:** dual-API entry points; SQL joins / aggs / `HAVING`;
`PIVOT` / `UNPIVOT` / brief `TABLESAMPLE`; windows + `QUALIFY`; CTEs and
named params; KPI parity **inspection**.

**Out of scope:**

- SQL→PySpark homework rewrites
- Python `assert` / automated tests (Module 17)
- Delta ACID / `MERGE` / time travel (Module 10)
- Unity Catalog grant administration (Module 11)
- Re-teaching Module 7/8 theory — one short **callback** to the matching
  PySpark notebook is enough

## Notebooks

Six notebooks, in order. Notebooks **01–05** each end with a short SQL
exercise. Notebook **06** has **no exercise** (parity inspection is the
synthesis).

**Ownership handoffs (do not re-teach across notebooks):**

| Topic | Owner |
|---|---|
| Dual entry + SQL↔DF bridges + when-to-choose | **01** |
| Row-level `CASE WHEN` (`tip_amount_band`, absolute bands) | **01** (reuse in **02** tier / **04** delta / **06** tip %) |
| First Module 9 `GROUP BY` / JOIN aliases / `HAVING` / `NOT EXISTS` | **02** |
| `COALESCE` visible on raw 106; one-line honesty after JOIN (NULL tips undriven) | **02** |
| `PIVOT` / `UNPIVOT` / `TABLESAMPLE` | **03** |
| Window `OVER` / `QUALIFY` / running `SUM` / `LAG` | **04** |
| CTEs + named `:params` | **05** |
| KPI rebuild + parity inspection (no asserts) | **06** |

| # | Notebook | Reads | Focus |
|---|---|---|---|
| 1 | Dual API Foundations and When to Choose | `trip_enriched` | UC `%sql` + `spark.table`; `spark.sql`→DF; row-level `CASE` → `tip_amount_band` (≠ Module 6 percent `tip_band`); DF→temp view; when-to-choose table. **No `GROUP BY`.** Locked bands: zero 26 / low 40 / medium 20 / high 18 / no_data 2. Exercise → **43** Manhattan known-tip rows |
| 2 | SQL Joins, Aggregations, and Filtering | `trip_enriched`, `trip_driver_assignment` | Layered arc: projection → service `tier` CASE → `COALESCE` → JOIN (deliberate `AMBIGUOUS_REFERENCE` then fix) → first `GROUP BY` → `HAVING`. Side path: `NOT EXISTS` undriven (**6**). After JOIN: high 15 / standard 64 / other 21. Exercise: compound `HAVING` + undriven ids |
| 3 | SQL Pivot, Unpivot, and Sampling | `trip_enriched` | Borough×service counts (**18**) → `PIVOT` service columns → `COALESCE` zeros + SQL `TEMP VIEW` → `UNPIVOT` back to rows; brief non-deterministic `TABLESAMPLE`. Exercise: `payment_method` reshape by borough |
| 4 | SQL Windows and QUALIFY | `kpi_zone_performance`, `kpi_daily_trip_summary` | Part 1: `ROW_NUMBER` + `QUALIFY` Top-2 by tip (**9** rows) + subquery equivalent. Part 2: running distance + `LAG` + direction `CASE`. Exercise: Top-2 by `trip_count` with `WHERE` + `QUALIFY` → **8** rows |
| 5 | CTEs and Parameterized SQL | `trip_enriched` | Single CTE → multi-CTE tip-share → nested-subquery contrast → `:borough` params (anti f-string) → CTE + params. Exercise: borough daily tip as share of fleet daily |
| 6 | End-to-End SQL Pipeline and Parity Inspection | all five tables | Rebuild daily / zone / driver KPIs via `spark.sql(...)`; `show_parity` displays counts + `exceptAll` (no assert). No exercise. Phase II synthesis → Module 10 |

### Notebook section navigation

Do not invent alternate arcs. Section titles below match the authored
notebooks.

**01 — Dual API Foundations and When to Choose**

1. Direct SQL on a UC table (`LIMIT` / `SHOW TABLES` / `DESCRIBE TABLE`)
2. Same projection via DataFrame API
3. SQL → DataFrame bridge (`spark.sql` + light `IS NOT NULL`; no agg)
4. Row-level `CASE WHEN` (`tip_amount_band`)
5. DataFrame → SQL bridge (`F.when` + temp view)
6. When to choose (decision table)

**02 — SQL Joins, Aggregations, and Filtering**

Main arc (one evolving query):

1. Base projection (NULLs visible on 106)
2. CASE → `tier`
3. `COALESCE` while NULLs remain
4. JOIN + ambiguous column (one intentional error, then fix → 100; one-line COALESCE honesty)
5. First `GROUP BY` (`GROUP BY tier` alias; repeating `CASE` also works)
6. `HAVING`

Side path: `NOT EXISTS` undriven trips (+ one-line `LEFT ANTI JOIN` awareness).

**03 — SQL Pivot, Unpivot, and Sampling**

1. Borough × service counts
2. `PIVOT` service types into columns
3. `COALESCE` zeros + SQL temp view
4. `UNPIVOT` columns back to rows
5. `TABLESAMPLE`

**04 — SQL Windows and QUALIFY**

- Part 1 (zone KPI): rank → `QUALIFY` → subquery equivalent
- Part 2 (daily KPI): running `SUM` → `LAG` → direction `CASE`

**05 — CTEs and Parameterized SQL**

1. Single CTE
2. Multi-CTE composition
3. Nested subquery contrast
4. Named parameters (`:borough`)
5. CTE + params combined

**06 — End-to-End SQL Pipeline and Parity Inspection**

- Setup + `show_parity` helper
- KPI 1 daily (layered `spark.sql`)
- KPI 2 zone (layered `spark.sql`)
- KPI 3 driver (CTE + `DENSE_RANK`)
- Takeaway (inspect here; automate in Module 17)

Cell-type lock for **06:** KPI rebuild steps that feed `show_parity` use
**Python** cells with `spark.sql(...)` so results are assignable DataFrames.

## PySpark callback map

When a SQL pattern is a re-expression, point back once — do not re-teach:

| Module 9 topic | Point back to |
|---|---|
| Temp views / `%sql` / `spark.sql` | Module 2 `06 - Querying DataFrames with SQL` |
| `F.when` / CASE-style columns | Module 2 `06 - Querying DataFrames with SQL` / Module 6 tip-band work (M9 uses **absolute** `tip_amount_band`) |
| Joins | Module 7 managed-table consumers (esp. `07 - Build Unified Curated Tables`) |
| `GROUP BY` / aggs / WHERE vs HAVING | Module 8 `01 - GroupBy and Basic Aggregations`, `02 - Multi-column Keys, NULL Groups, and Filter Placement` |
| Pivot | Module 8 `04 - Pivot` |
| Windows / Top-N / ranking | Module 8 `05 - Window Functions Fundamentals`–`07 - Top-N per Group and Sampling` |
| Running totals / lag | Module 8 `06 - Running Totals and Lag and Lead` |
| Sampling | Module 8 `07 - Top-N per Group and Sampling` |
| KPI formulas / grains | Module 8 `08 - Build KPI Tables` + Module 8 README contracts |

Refer by **real notebook titles** (never “Notebook 02” alone).

## Drafting quality gate (Module 9)

Module-local authoring gate (supplements `docs/standards/*.md`):

- **Minimal MD by default.** Business question + what’s new + expected
  result/trap. Runnable SQL carries the lesson
- **Do not re-teach** Module 7/8 theory. One short callback is enough
- **More MD only for net-new SQL:** dual-API when-to-choose; ambiguous
  column → aliases; `QUALIFY`; CTEs vs nested SQL; `:params` vs f-strings;
  `UNPIVOT` vs DF `stack()`; parity inspection vs Module 17 asserts
- **Quality over volume:** tight prose, precise names, locked expected
  counts; no essay cells; no duplicate explanations across intro /
  section / summary
- **No Python `assert`.** Diffs are displayed; automated tests → Module 17

## Minimum privileges required

- Workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the compute used here
- Unity Catalog (no catalog/schema/table DDL, no managed-table writes):
  - **`USE CATALOG`** on **`rideshare_dev`**
  - **`USE SCHEMA`** on **`rideshare_dev.processed`**
  - **`SELECT`** on:
    - `rideshare_dev.processed.trip_enriched`
    - `rideshare_dev.processed.trip_driver_assignment`
    - `rideshare_dev.processed.kpi_daily_trip_summary`
    - `rideshare_dev.processed.kpi_zone_performance`
    - `rideshare_dev.processed.kpi_driver_productivity`
  - Session **`CREATE OR REPLACE TEMP VIEW`** is allowed (Notebook **03**);
    that is not schema/table DDL on `rideshare_dev.processed`
