# Module 8 — Aggregations and Window Functions

## Purpose

Turn the unified tables built in Module 7 into analytics-ready summaries and KPI
tables — without losing rows to NULL-skipping aggregates, double-counting a
grain, or mistaking a window function for a `groupBy`.

Two habits run through Notebooks **01–07**:

1. State the **output grain** before you aggregate — one row per *what*?
2. **Predict row count → run → verify** with `count()`, exactly as in Module 7

The dividing question of this module: do you want **fewer rows** (`groupBy`
collapses) or **the same rows plus a summary column** (a window does not
collapse)? Notebooks **01–04** cover the first, **05–07** the second.

Notebooks **01–07** build skills only (**no write**). Notebook **08** is a
**write-only business notebook** — read the Module 7 managed tables, build the
three KPI outputs for Module 9, write. No profiling or validation scripts
(those belong in **01–07**).

Schemas and physical layout:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md). Module 7
target-column scope:
[`07 - Joins and Set Operations/requirements/trip_enriched_mapping.md`](../07%20-%20Joins%20and%20Set%20Operations/requirements/trip_enriched_mapping.md).

## Learning objectives

By the end of this module, you'll be able to:

- Name the **output grain** of an aggregate and predict its row count before
  running
- Write **`groupBy().agg()`** with aliased aggregate columns, and group by one
  or several columns
- Explain why **`F.count("*")`**, **`F.count("col")`**, and
  **`F.countDistinct("col")`** disagree, and why **`F.avg`** / **`F.sum`** skip
  NULLs instead of returning NULL
- Filter **before** aggregating (`WHERE`) versus **after** (`HAVING`) and say
  which one changes the numbers
- Reach past `count` / `sum` to **`F.collect_set`**, **`F.median`**,
  **`F.mode`**, **`F.percentile_approx`**, and **`F.approx_count_distinct`**
- Produce subtotals with **`rollup`** / **`cube`** / **`grouping_sets`** and
  identify subtotal rows with **`F.grouping_id`**
- Reshape a summary with **`pivot`** (always with an explicit value list) and
  reverse it with **`stack`**
- Build a **`Window`** spec (`partitionBy` / `orderBy`), rank with
  **`row_number`** / **`rank`** / **`dense_rank`** / **`ntile`**, and add
  window aggregates that keep every input row
- Control window **frames** (`rowsBetween` vs `rangeBetween`) for running
  totals and moving averages, and use **`lag`** / **`lead`**
- Select **Top-N per group** deterministically and handle ties, and draw
  reproducible samples with **`sample`** / **`sampleBy`** / **`randomSplit`**
- Apply those patterns in Notebook **08** to write the three `curated/` KPI
  outputs

## Prerequisites

Complete Module 7 notebooks **`01`–`07`**. You need:

| Asset | Rows / notes | Source |
|---|---|---|
| `rideshare_dev.processed.trip_enriched` | 106 — one per `trip_id`; 16 columns | Module 7 **`07`** |
| `rideshare_dev.processed.trip_driver_assignment` | One per (`driver_id`, `trip_id`); 12 drivers, trips 1–100; 13 columns | Module 7 **`07`** |

`trip_enriched` is the primary source for Notebooks **01–06**.
`trip_driver_assignment` appears where a **1:M** grain (many trips per driver)
makes a point that trip grain cannot.

**Inherited NULLs — this module's teaching material, not a defect.** Two
different causes, which is why **each column has its own non-NULL count**:
Module 7's intentional left joins (see that module's *Expected NULLs*), and
Module 6's value-rejection rules, which turned bad source values into NULL.

| Column(s) | NULL on `trip_id` | Rows | Cause |
|---|---|---|---|
| `trip_date`, `hour_of_day` | 101–106 | 6 | `trip_time` has only 100 rows — left join |
| `payment_method`, `driver_payout_amount` | 106 | 1 | `curated/payment` has 105 rows — left join |
| `base_fare_amount` | 104, 106 | 2 | Left join **plus** trip 104's negative fare rejected in Module 6 |
| `tip_amount` | 103, 106 | 2 | Left join **plus** trip 103's `not_a_number` tip rejected in Module 6 |
| `trip_distance_miles` | 103, 105, 106 | 3 | Module 6 positive-value rule |

`ride_duration_mins`, `service_type`, and the four zone columns have **no**
NULLs — every trip matched a zone (`location_id` 1–20). So `F.count("*")` is
106 while `F.count(col)` returns 100 / 104 / 105 / 106 depending on the column,
and `F.avg` silently divides by that per-column count. Notebooks **01** and
**02** are built on this.

Group-key values after Module 6 normalization, since the casing surprises
people: `service_type` is **uppercase** (`STANDARD` 55, `SHARED` 21,
`PREMIUM` 16, `XL` 12, `UNKNOWN` 2) while `payment_method` is **lowercase**
(`card` 59, `wallet` 20, `cash` 17, `corporate` 8, `unknown` 1, plus 1 NULL).
`UNKNOWN` / `unknown` are normalized sentinels, **not** NULL — a `groupBy`
shows them as ordinary groups.

Also recall: Module 2 `F.when` / `F.lit` for KPI ratio columns, Module 3
NULL semantics and `F.coalesce`, Module 4 wide (shuffle) stages — every
`groupBy` and every `partitionBy` is an `Exchange`, and Module 7 Notebook
**02**'s narrow `Window` + `row_number` dedup, which Notebook **05** here
generalizes.

Does **not** read `practice/` or the Module 6 `curated/` folders — Module 7's
managed tables already carry what this module needs.

## Paths and outputs

| Role | Location |
|---|---|
| Reads | Unity Catalog managed tables `rideshare_dev.processed.{trip_enriched, trip_driver_assignment}` |
| Module writes | `/Volumes/rideshare_dev/processed/output_files/curated/{kpi_name}/` |

| Output | Path | Grain / contract |
|---|---|---|
| Daily trip summary | `…/curated/kpi_daily_trip_summary/` | One row per **`trip_date`**. Trip count, total distance, avg ride duration, total base fare, total tip, total driver payout. Drops the 6 NULL-`trip_date` rows (trips 101–106) **explicitly**, and says so |
| Zone performance | `…/curated/kpi_zone_performance/` | One row per (**`pickup_borough`**, **`pickup_zone`**). Trip count, avg distance, avg base fare, tip rate (total tip / total base fare) |
| Driver productivity | `…/curated/kpi_driver_productivity/` | One row per **`driver_id`** from `trip_driver_assignment` (12 rows). Trips assigned, total distance, avg ride duration, distance rank across drivers (`dense_rank`) |

Write KPI outputs as **Parquet** with **`.mode("overwrite")`**. Every KPI folder
name is prefixed **`kpi_`** so `curated/` stays readable next to the Module 6
cleaned datasets. Module 9 reads these folders and reproduces them in SQL.

**Cleanup:** reuse Module 5 **`99`** Level 2, which clears all Module 6–9
`curated/` outputs. This module has no dedicated cleanup notebook and creates
no managed tables, so Level 4 is not needed here.

## Runtime and scope

**Runtime:** Spark **4.0.0** / DBR **17.3 LTS**.

**API:** DataFrame `groupBy` / `agg`, `rollup` / `cube` / `groupingSets`,
`pivot`, and `pyspark.sql.window.Window` with `F.*` window functions. No Spark
SQL dual-API and no `QUALIFY` — those are Module 9, which re-expresses this
module's outputs in SQL.

**In scope:** output grain and row-count prediction; aggregate functions and
their NULL behavior; `WHERE` vs `HAVING` placement; multi-level grouping and
pivot; window specs, ranking, frames, `lag` / `lead`; Top-N per group;
sampling; the three KPI writes in **07**.

**Out of scope:** SQL syntax for the same operations and `QUALIFY` (Module 9);
Delta ACID / `MERGE` / incremental KPI refresh (Module 10 and 13 — Notebook
**07** fully overwrites each run); UC grants (Module 11); skew, spill, and
shuffle-partition tuning behind these aggregates (Module 16 — Notebook **04**
adds only a one-line note that `partitionBy` shuffles); approximate-algorithm
internals beyond *when to reach for `approx_count_distinct`*; UDAFs (custom
aggregate functions) — built-ins cover every case in this module, consistent
with Module 6.

## Notebooks

Eight notebooks, in order. Notebooks **01–07** are skill-building only and each
ends with a short hands-on task that repeats the demonstrated pattern on
slightly different columns. Notebook **08** is write-only (no practice, no
validation cells): read, build the three KPI outputs, write Parquet.

| # | Notebook | Reads | Focus |
|---|---|---|---|
| 1 | GroupBy and Basic Aggregations | `trip_enriched` (106) | Output grain vs input grain; `countDistinct` predicts the output row count (`service_type` → 5); `groupBy().agg()` + aliasing; `F.count("*")` (106) vs `F.count("trip_date")` (100) vs `F.countDistinct("trip_date")` (14); `F.sum` / `F.avg` skip NULLs — `avg("tip_amount")` divides by 104, and `F.coalesce` changes the answer; exercise — per-`payment_method` summary (6 groups: 5 values + 1 NULL) |
| 2 | Multi-column Keys, NULL Groups, and Filter Placement | `trip_enriched` (106) | Composite grain: grouping on (`service_type`, `payment_method`) → 18 of a possible 30 rows; NULL as its own group — `countDistinct` ignores it, `groupBy` keeps it, joins never match it; `WHERE` vs `HAVING` on per-borough tip totals; exercise — per-`pickup_borough` summary with HAVING (5 groups) |
| 3 | Aggregate Functions Beyond Count and Sum | `trip_enriched` (106), `trip_driver_assignment` | `F.collect_list` / `F.collect_set` back to arrays (Module 6 complex types); `F.median` / `F.mode` / `F.percentile_approx` vs `F.avg` on skewed fares; `F.countDistinct` vs `F.approx_count_distinct` (exact cost vs estimate); `decimal` precision growth in `F.sum` / `F.avg`; `F.first` / `F.last` and why they need `orderBy` to mean anything |
| 4 | Multi-Level Grouping and Pivot | `trip_enriched` (106) | `rollup` vs `cube` vs `groupingSets` on (`pickup_borough`, `service_type`); telling a subtotal row from a NULL data row with `F.grouping_id`; `pivot` `service_type` by `hour_of_day`; explicit pivot value list vs inferred (extra scan); multiple aggregates in one pivot; reversing with `F.expr("stack(...)")` |
| 5 | Window Functions Fundamentals | `trip_enriched` (106), `trip_driver_assignment` | Same summary, no collapse: `groupBy` (fewer rows) vs `Window` (same rows + column); `Window.partitionBy` / `orderBy`; `row_number` / `rank` / `dense_rank` / `ntile` and how each treats ties; window aggregate (`F.avg().over(w)`) for per-row share-of-group; generalizes Module 7 **02**'s dedup; one-line note that `partitionBy` is an `Exchange` (Module 16) |
| 6 | Window Frames, Running Totals, and lag/lead | `trip_enriched` (106) | The implicit frame: `orderBy` alone means *unbounded preceding → current row* — the module's biggest gotcha; `rowsBetween` vs `rangeBetween` (ties change `range` results); running total and moving average of daily fare; `lag` / `lead` for day-over-day change with `default`; unordered window = whole-partition frame |
| 7 | Top-N per Group and Sampling | `trip_enriched` (106), `trip_driver_assignment` | Two ways to keep a subset of rows — deterministic and probabilistic. `row_number` + `filter` for Top-3 zones per borough; `rank` / `dense_rank` when ties must all survive; why `orderBy().limit()` is not per-group; `sample(fraction, seed)`, `sampleBy` stratified on `service_type`, `randomSplit`; seed reproducibility and why a sampled aggregate is for development speed, not reporting |
| 8 | Build KPI Tables | `trip_enriched`, `trip_driver_assignment` | Write-only business flow: read both managed tables → explicit NULL-`trip_date` exclusion → build `kpi_daily_trip_summary`, `kpi_zone_performance` (tip rate), `kpi_driver_productivity` (`dense_rank`) → Parquet `overwrite` to the three `curated/` folders; no pedagogy re-teach, no practice |

## Minimum privileges required

- Workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the compute used here
- Unity Catalog (objects from Modules 5 and 7 — no catalog, external-location,
  or volume DDL here, and no `CREATE TABLE`):
  - **`USE CATALOG`** on **`rideshare_dev`**
  - **`USE SCHEMA`** on **`rideshare_dev.processed`**
  - **`SELECT`** on **`rideshare_dev.processed.trip_enriched`** and
    **`rideshare_dev.processed.trip_driver_assignment`**
  - **`WRITE VOLUME`** on **`rideshare_dev.processed.output_files`**
    (KPI writes — Notebook **08**)
