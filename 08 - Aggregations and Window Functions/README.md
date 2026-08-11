# Module 8 — Aggregations and Window Functions

## Purpose

Turn the Module 7 managed tables into analytics-ready summaries and KPI
tables — without losing rows to NULL-skipping aggregates, mistaking output
grain, or treating a window like a `groupBy`.

Two habits run through the skill-building notebooks:

1. **Name the output grain** before you write the aggregate — one row per *what*?
2. **Verify with `count()`** after — especially on a new dataset or a new key

Notebooks **01–04** use `groupBy` (fewer rows). **05–07** focus on windows,
which preserve the rows of the DataFrame they receive. Notebook **06** may
first aggregate to daily grain, then window over that. **01–07** do not write.
Notebook **08** writes three managed Delta KPI tables for Module 9.

Schemas, inherited NULLs, and group-key values:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).
KPI column contracts live in this README (Paths and outputs).

## Learning objectives

By the end of this module, you'll be able to:

- Name and verify the **output grain** of grouped and windowed calculations
- Build aliased aggregates with single or composite keys, and reason about
  NULL keys, NULL values, and count semantics
- Choose whether to filter input rows (`WHERE`) or aggregated groups (`HAVING`)
- Use advanced aggregates and pivoting to summarize and reshape data
- Build windows for ranking, running calculations, and row-to-row comparisons
- Control NULL sort placement with **`nullsFirst` / `nullsLast`**
- Select **Top-N per group** (including tie-selection policy) and draw
  reproducible samples with **`sample`** / **`sampleBy`** / **`randomSplit`**
- Apply the module patterns in Notebook **08** to write three managed `kpi_*`
  tables for Module 9

## Prerequisites

Complete Module 7 notebooks **`01`–`07`**. You need:

| Asset | Rows / notes | Source |
|---|---|---|
| `rideshare_dev.processed.trip_enriched` | 106 — one per `trip_id`; 16 columns | Module 7 **`07`** |
| `rideshare_dev.processed.trip_driver_assignment` | 100 — one per (`driver_id`, `trip_id`); 12 drivers, trips 1–100; 13 columns | Module 7 **`07`** |

`trip_enriched` is the primary source for Notebooks **01–07**.
`trip_driver_assignment` appears where a **1:M** grain (many trips per driver)
makes a point that trip grain cannot. Notebook **01** owns the shared setup
description; later notebooks load without re-describing it.

Also recall: Module 3 NULL / `F.coalesce`; Module 4 wide/`Exchange` stages;
Module 7 Notebook **02** (`Window` + `row_number` dedup — revisited in **05**;
Top-N reuses the pattern in **07**).

Does **not** read `practice/` or Module 6 `curated/` — the managed tables
already carry what this module needs.

## Paths and outputs

Notebook **08** writes Unity Catalog managed Delta tables with
`.mode("overwrite").saveAsTable(...)`. Module 9 reads them with
`spark.table(...)` / SQL `FROM` and re-expresses the same logic.

| Table | Grain / rows | Source |
|---|---|---|
| `rideshare_dev.processed.kpi_daily_trip_summary` | One row per **`trip_date`** — **14**. Explicitly drops NULL-`trip_date` trips **101–106** (that filter also removes all measure-NULL rows; remaining trips 1–100 are fully populated) | `trip_enriched` |
| `rideshare_dev.processed.kpi_zone_performance` | One row per (**`pickup_borough`**, **`pickup_zone`**) — **20**. All 106 rows; primary NULL-aggregate surface | `trip_enriched` |
| `rideshare_dev.processed.kpi_driver_productivity` | One row per **`driver_id`** — **12**. Includes fleet-wide `distance_dense_rank` after aggregate | `trip_driver_assignment` |

### `kpi_daily_trip_summary` columns

| Column | Formula |
|---|---|
| `trip_date` | key |
| `trip_count` | `count("*")` |
| `total_base_fare` | `sum(base_fare_amount)` |
| `total_tip` | `sum(tip_amount)` |
| `total_driver_payout` | `sum(driver_payout_amount)` |
| `total_distance_miles` | `sum(trip_distance_miles)` — Module 9 running-total candidate |
| `avg_distance_miles` | `round(avg(trip_distance_miles), 2)` |
| `avg_ride_duration_mins` | `round(avg(ride_duration_mins), 2)` |

### `kpi_zone_performance` columns

| Column | Formula |
|---|---|
| `pickup_borough`, `pickup_zone` | composite key |
| `pickup_location_id` | `max(pickup_location_id)` — deterministic per zone |
| `trip_count` | `count("*")` |
| `total_base_fare`, `total_tip` | sums (NULL-skipping) |
| `tip_percent_of_base` | `when(sum(base_fare_amount) > 0, round(100 * sum(tip) / sum(base), 1)).otherwise(NULL)` — not avg of row percents |
| `avg_distance_miles`, `avg_ride_duration_mins` | rounded avgs |

NULL-affected pickup zones (verified): Financial District (104 base), Harlem
(106 base/tip/distance — densest), Astoria (103 tip/distance), Williamsburg
(105 distance only).

### `kpi_driver_productivity` columns

| Column | Formula |
|---|---|
| `driver_id` | key |
| `driver_name` | `max(driver_name)` |
| `trip_count` | `count("*")` |
| `total_distance_miles` | `sum(trip_distance_miles)` |
| `avg_ride_duration_mins` | `round(avg(ride_duration_mins), 2)` |
| `unique_service_types` | `sort_array(collect_set(service_type))` |
| `distance_dense_rank` | after agg: `dense_rank` over fleet by `total_distance_miles` desc |

**Cleanup:** Module 5 **`99`** Level 4 (catalog teardown) drops these managed
tables with the rest of `rideshare_dev` — same as Module 7. Level 2 clears
Module 6 `curated/` Parquet only and does **not** remove KPI tables.

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

**Ownership handoffs (do not re-teach across notebooks):**

| Topic | Owner |
|---|---|
| Ranking-API ties (`row_number` vs `rank` vs `dense_rank`) | **05** |
| Top-2 filter-after-rank preview | **05** (full Top-N → **07**) |
| Frames, running totals, `first_value` / `last_value`, `lag` / `lead` | **06** |
| Top-N per group; Top-N selection policy; sampling | **07** |
| `nullsFirst` / `nullsLast` (ordered-window sort placement) | **07** (standalone; not only on Top-N) |
| General NULL semantics | Module 3 and Notebooks **01–02** |

| # | Notebook | Reads | Focus |
|---|---|---|---|
| 1 | GroupBy and Basic Aggregations | `trip_enriched` | Output grain; `groupBy().agg()` + aliasing; bare non-key column fails (window → **05**); three counts; `sum`/`avg` skip NULLs + `F.coalesce`; exercise — per-`payment_method` |
| 2 | Multi-column Keys, NULL Groups, and Filter Placement | `trip_enriched` | NULL key group vs `countDistinct`; composite grain; `WHERE` vs `HAVING`; exercise — borough + HAVING, then composite key |
| 3 | Collections, Percentiles, and Distinct Counts | `trip_enriched`, `trip_driver_assignment` | `collect_list` / `collect_set`; `avg` vs approximate p50 / p90; `countDistinct` |
| 4 | Pivot | `trip_enriched` | `pivot` + explicit values |
| 5 | Window Functions Fundamentals | `trip_enriched`, `trip_driver_assignment` | `groupBy` vs `Window`; partition-only aggregates; ranking-API ties; Top-2 filter-after-rank preview → **07** |
| 6 | Running Totals and lag/lead | `trip_enriched` | Default `RANGE` vs explicit `ROWS`; ordered `first_value` / `last_value`; daily running totals; `lag` / `lead` |
| 7 | Top-N per Group and Sampling | `trip_enriched`, `trip_driver_assignment` | Top-N per group (`row_number` + filter; extends **05** Top-2); Top-N selection policy (`row_number <= N` vs `rank <= N`, secondary sort); `nullsFirst` / `nullsLast` (standalone sort placement); `sample` / `sampleBy` / `randomSplit` |
| 8 | Build KPI Tables | both managed tables | Write-only: three managed `kpi_*` Delta tables (`saveAsTable`) |

## Markdown Quality Gate (Module 8)

Module-local authoring gate (supplements `docs/standards/*.md`):

- Begin each section with a concrete dataset example before theory
- Keep introductions to motivation + a short roadmap
- Notebooks **02+**: point to Notebook **01** or `dataset-overview.md` for shared
  setup — do not repeat full schema tables
- Before push, remove repeated statements across introduction, sections, and
  summary

## Minimum privileges required

- Workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the compute used here
- Unity Catalog (no catalog / external-location / volume DDL):
  - **`USE CATALOG`** on **`rideshare_dev`**
  - **`USE SCHEMA`** on **`rideshare_dev.processed`**
  - **`SELECT`** on **`rideshare_dev.processed.trip_enriched`** and
    **`rideshare_dev.processed.trip_driver_assignment`**
  - **`CREATE TABLE`** on **`rideshare_dev.processed`** (Notebook **08** only)
