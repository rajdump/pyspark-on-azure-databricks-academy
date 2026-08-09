# Module 8 — Aggregations and Window Functions

## Purpose

Turn the Module 7 managed tables into analytics-ready summaries and KPI
tables — without losing rows to NULL-skipping aggregates, mistaking output
grain, or treating a window like a `groupBy`.

Two habits run through the skill-building notebooks:

1. **Name the output grain** before you write the aggregate — one row per *what*?
2. **Verify with `count()`** after — especially on a new dataset or a new key

Notebooks **01–04** use `groupBy` to produce fewer rows; **05–07** use windows
to keep the input rows while adding summary columns. These notebooks do not
write data. Notebook **08** applies the patterns to build three Parquet KPI
outputs for Module 9, without re-teaching them.

**Dataset reference:**
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md)
(schemas, inherited NULLs, group-key values). Module 7 mappings:
[`trip_enriched_mapping.md`](../07%20-%20Joins%20and%20Set%20Operations/requirements/trip_enriched_mapping.md),
[`trip_driver_assignment_mapping.md`](../07%20-%20Joins%20and%20Set%20Operations/requirements/trip_driver_assignment_mapping.md).

## Learning objectives

By the end of this module, you'll be able to:

- Name and verify the **output grain** of grouped and windowed calculations
- Build aliased aggregates with single or composite keys, and reason about
  NULL keys, NULL values, and count semantics
- Choose whether to filter input rows (`WHERE`) or aggregated groups (`HAVING`)
- Use advanced aggregates and pivoting to summarize and reshape data
- Build windows for ranking, running calculations, and row-to-row
  comparisons
- Select **Top-N per group** and draw reproducible samples with **`sample`** /
  **`sampleBy`** / **`randomSplit`**
- Apply the module patterns in Notebook **08** to write three `curated/` KPI
  outputs for Module 9

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
Module 7 Notebook **02**'s `Window` + `row_number` dedup (revisited later as its
own topic; Notebook **05** previews filter-after-rank with Top-2).

Does **not** read `practice/` or Module 6 `curated/` — the managed tables
already carry what this module needs.

## Paths and outputs

Notebooks read the two managed tables listed under **Prerequisites**. Notebook
**08** writes to
`/Volumes/rideshare_dev/processed/output_files/curated/{kpi_name}/`.

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

**API:** DataFrame `groupBy` / `agg`, `pivot`, and
`pyspark.sql.window.Window` with `F.*` window functions.

**Out of scope:** Spark SQL / `QUALIFY` (Module 9); Delta ACID / `MERGE` /
incremental KPI refresh (Modules 10 and 13); Unity Catalog grant administration
(Module 11); shuffle tuning beyond a one-line `partitionBy` note in Notebook
**05** (Module 16); UDAFs — built-ins cover this module.

## Notebooks

Each skill-building notebook ends with a short exercise.
Notebook **01** owns the `trip_enriched` setup description and the inherited-NULL
map. Notebooks **02–07** load the table without re-describing it, and point back
to the notebook that taught a concept instead of re-teaching it.

**NULLs in windows:** Notebook **05** keeps ranking columns non-NULL (ties
only) and points to **`nullsFirst` / `nullsLast`**. Notebook **07** demos NULL
sort placement once on Top-N. No separate notebook — Module 3 and Notebooks
**01–02** already own general NULL semantics.

| # | Notebook | Reads | Focus |
|---|---|---|---|
| 1 | GroupBy and Basic Aggregations | `trip_enriched` | Output grain; `groupBy().agg()` + aliasing; bare non-key column in `.agg()` fails (window → **05**); three counts (`*` / col / distinct); `sum`/`avg` skip NULLs + `F.coalesce`; exercise — per-`payment_method` summary (observe row count; NULL-group *why* → **02**) |
| 2 | Multi-column Keys, NULL Groups, and Filter Placement | `trip_enriched` | NULL key group vs `countDistinct`; composite grain (`service_type`, `payment_method` → 18 of 30); progressive `WHERE` vs `HAVING` comparison; exercise — per-`pickup_borough` + HAVING, then composite (`pickup_borough`, `payment_method`) |
| 3 | Collections, Percentiles, and Distinct Counts | `trip_enriched`, `trip_driver_assignment` | `collect_list` / `collect_set` (duplicates, unique values, NULL exclusion, bounded groups); `avg` vs approximate p50 / p90; `countDistinct` route counts |
| 4 | Pivot | `trip_enriched` | `pivot` + explicit values |
| 5 | Window Functions Fundamentals | `trip_enriched`, `trip_driver_assignment` | `groupBy` vs `Window`; ranking + ties; window aggregates; Top-2 filter-after-rank preview (non-NULL ranking measures) |
| 6 | Running Totals and lag/lead | `trip_enriched` | Ordered `first_value` / `last_value`; running totals; `lag` / `lead` |
| 7 | Top-N per Group and Sampling | `trip_enriched`, `trip_driver_assignment` | Top-N via `row_number`; ties; one short nullable-order example (`nullsFirst` / `nullsLast`); `sample` / `sampleBy` / `randomSplit` |
| 8 | Build KPI Tables | both managed tables | Write-only: three `kpi_*` Parquet outputs |

## Markdown Quality Gate (Module 8)

Module-local quality gate for this module. It supplements
`docs/standards/*.md` and does not replace global standards.

- Begin each section with a concrete example from this dataset — a number,
  expected result, or small table — before the theory.
- Keep introductory content to two roles: motivation and a short roadmap.
- In notebooks 02 and later, reference Notebook 01 or
  `docs/data/dataset-overview.md` for shared setup; do not repeat full schema
  tables.
- Before push, remove repeated statements across the introduction, sections,
  and summary.

## Minimum privileges required

- Workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the compute used here
- Unity Catalog (no catalog / external-location / volume DDL; no `CREATE TABLE`):
  - **`USE CATALOG`** on **`rideshare_dev`**
  - **`USE SCHEMA`** on **`rideshare_dev.processed`**
  - **`SELECT`** on **`rideshare_dev.processed.trip_enriched`** and
    **`rideshare_dev.processed.trip_driver_assignment`**
  - **`WRITE VOLUME`** on **`rideshare_dev.processed.output_files`**
    (Notebook **08** only)
