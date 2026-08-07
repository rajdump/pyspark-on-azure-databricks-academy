# Module 8 — Aggregations and Window Functions

## Purpose

Turn the Module 7 managed tables into analytics-ready summaries and KPI
tables — without losing rows to NULL-skipping aggregates, mistaking output
grain, or treating a window like a `groupBy`.

Two habits run through Notebooks **01–07**:

1. **Name the output grain** before you write the aggregate — one row per *what*?
2. **Verify with `count()`** after — especially on a new dataset or a new key

The dividing question: do you want **fewer rows** (`groupBy` collapses) or
**the same rows plus a summary column** (a window does not collapse)?
Notebooks **01–04** cover the first; **05–07** the second.

Notebooks **01–07** are skill-building only (**no write**). Notebook **08** is
write-only: read the Module 7 tables, build three KPI outputs for Module 9,
write Parquet. No pedagogy re-teach in **08**.

**Dataset reference:**
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md)
(schemas, inherited NULLs, group-key values). Module 7 mappings:
[`trip_enriched_mapping.md`](../07%20-%20Joins%20and%20Set%20Operations/requirements/trip_enriched_mapping.md),
[`trip_driver_assignment_mapping.md`](../07%20-%20Joins%20and%20Set%20Operations/requirements/trip_driver_assignment_mapping.md).

## Learning objectives

By the end of this module, you'll be able to:

- Name the **output grain** of an aggregate and verify its row count
- Write **`groupBy().agg()`** with aliased columns; group by one or several keys
- Explain why **`F.count("*")`**, **`F.count("col")`**, and
  **`F.countDistinct("col")`** disagree, and why **`F.avg`** / **`F.sum`** skip
  NULLs
- Explain why **`groupBy` keeps a NULL group** while **`countDistinct` ignores
  NULL**, and why `unknown` ≠ NULL
- Filter **before** aggregating (`WHERE`) vs **after** (`HAVING`) and say which
  changes the numbers
- Use **`F.collect_set`**, **`F.median`**, **`F.mode`**,
  **`F.percentile_approx`**, and **`F.approx_count_distinct`**
- Produce subtotals with **`rollup`** / **`cube`** / **`groupingSets`** and
  identify them with **`F.grouping_id`**
- Reshape with **`pivot`** (explicit value list) and reverse with **`stack`**
- Build a **`Window`** (`partitionBy` / `orderBy`), rank with **`row_number`** /
  **`rank`** / **`dense_rank`** / **`ntile`**, and add window aggregates that
  keep every input row
- Control window **frames** (`rowsBetween` vs `rangeBetween`), and use
  **`lag`** / **`lead`**
- Select **Top-N per group** and draw reproducible samples with **`sample`** /
  **`sampleBy`** / **`randomSplit`**
- Apply those patterns in Notebook **08** to write the three `curated/` KPI
  outputs

## Prerequisites

Complete Module 7 notebooks **`01`–`07`**. You need:

| Asset | Rows / notes | Source |
|---|---|---|
| `rideshare_dev.processed.trip_enriched` | 106 — one per `trip_id`; 16 columns | Module 7 **`07`** |
| `rideshare_dev.processed.trip_driver_assignment` | 100 — one per (`driver_id`, `trip_id`); 12 drivers, trips 1–100; 13 columns | Module 7 **`07`** |

`trip_enriched` is the primary source for Notebooks **01–07**.
`trip_driver_assignment` appears where a **1:M** grain (many trips per driver)
makes a point that trip grain cannot.

**Inherited NULLs** on `trip_enriched` (join gaps + Module 6 value rejection)
are teaching material — column × `trip_id` NULL map and normalized group-key
values (`service_type`, `payment_method`) live in
[`dataset-overview.md`](../docs/data/dataset-overview.md).

Also recall: Module 3 NULL / `F.coalesce`; Module 4 wide/`Exchange` stages;
Module 7 Notebook **02**'s `Window` + `row_number` dedup (generalized here in
Notebook **05**).

Does **not** read `practice/` or Module 6 `curated/` — the managed tables
already carry what this module needs.

## Paths and outputs

| Role | Location |
|---|---|
| Reads | `rideshare_dev.processed.{trip_enriched, trip_driver_assignment}` |
| Module writes | `/Volumes/rideshare_dev/processed/output_files/curated/{kpi_name}/` |

| Output | Path | Grain / contract |
|---|---|---|
| Daily trip summary | `…/curated/kpi_daily_trip_summary/` | One row per **`trip_date`**. Drops the 6 NULL-`trip_date` rows (trips 101–106) **explicitly** |
| Zone performance | `…/curated/kpi_zone_performance/` | One row per (**`pickup_borough`**, **`pickup_zone`**). Includes tip rate |
| Driver productivity | `…/curated/kpi_driver_productivity/` | One row per **`driver_id`** (12). Includes `dense_rank` on distance |

Write as **Parquet** with **`.mode("overwrite")`**. KPI folders use the
**`kpi_`** prefix. Module 9 reads these folders and re-expresses them in SQL.

**Cleanup:** Module 5 **`99`** Level 2 clears Module 6–9 `curated/` outputs.
This module creates no managed tables — Level 4 is not required here.

## Runtime and scope

**Runtime:** Spark **4.0.0** / DBR **17.3 LTS**.

**API:** DataFrame `groupBy` / `agg`, `rollup` / `cube` / `groupingSets`,
`pivot`, and `pyspark.sql.window.Window` with `F.*` window functions. No Spark
SQL dual-API and no `QUALIFY` (Module 9).

**In scope:** output grain; aggregate NULL behavior; NULL group keys; `WHERE` vs
`HAVING`; multi-level grouping and pivot; windows, frames, `lag` / `lead`;
Top-N and sampling; three KPI writes in Notebook **08**.

**Out of scope:** SQL / `QUALIFY` (Module 9); Delta ACID / `MERGE` / incremental
KPI refresh (Modules 10 and 13 — Notebook **08** fully overwrites each run); UC
grants (Module 11); shuffle tuning beyond a one-line `partitionBy` note in
Notebook **05** (Module 16); UDAFs — built-ins cover this module.

## Notebooks

Eight notebooks, in order. **01–07** skill-building (each ends with a short
exercise). **08** write-only.

| # | Notebook | Reads | Focus |
|---|---|---|---|
| 1 | GroupBy and Basic Aggregations | `trip_enriched` | Output grain; `groupBy().agg()` + aliasing; three counts (`*` / col / distinct); `sum`/`avg` skip NULLs + `F.coalesce`; bare non-key column in `.agg()` fails (window → **05**); exercise — per-`payment_method` summary (observe row count; NULL-group *why* → **02**) |
| 2 | Multi-column Keys, NULL Groups, and Filter Placement | `trip_enriched` | Composite grain (`service_type`, `payment_method` → 18 of 30); NULL group vs `countDistinct`; `unknown` ≠ NULL; `WHERE` vs `HAVING`; exercise — per-`pickup_borough` + HAVING |
| 3 | Aggregate Functions Beyond Count and Sum | `trip_enriched`, `trip_driver_assignment` | `collect_list` / `collect_set`; `median` / `mode` / `percentile_approx` vs `avg`; exact vs `approx_count_distinct`; decimal growth; `first` / `last` need order |
| 4 | Multi-Level Grouping and Pivot | `trip_enriched` | `rollup` / `cube` / `groupingSets`; `grouping_id`; `pivot` + explicit values; `stack` |
| 5 | Window Functions Fundamentals | `trip_enriched`, `trip_driver_assignment` | `groupBy` vs `Window`; ranking; window aggregates; generalizes Module 7 **02** dedup |
| 6 | Window Frames, Running Totals, and lag/lead | `trip_enriched` | Implicit frame gotcha; `rowsBetween` vs `rangeBetween`; running totals; `lag` / `lead` |
| 7 | Top-N per Group and Sampling | `trip_enriched`, `trip_driver_assignment` | Top-N via `row_number`; ties; `sample` / `sampleBy` / `randomSplit` |
| 8 | Build KPI Tables | both managed tables | Write-only: three `kpi_*` Parquet outputs |

## Minimum privileges required

- Workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the compute used here
- Unity Catalog (no catalog / external-location / volume DDL; no `CREATE TABLE`):
  - **`USE CATALOG`** on **`rideshare_dev`**
  - **`USE SCHEMA`** on **`rideshare_dev.processed`**
  - **`SELECT`** on **`rideshare_dev.processed.trip_enriched`** and
    **`rideshare_dev.processed.trip_driver_assignment`**
  - **`WRITE VOLUME`** on **`rideshare_dev.processed.output_files`**
    (KPI writes — Notebook **08**)
