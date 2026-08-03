# Module 7 — Joins and Set Operations

## Purpose

Join and combine rideshare tables with predictable row counts and clear keys —
no silent cardinality or key traps (M:M fanout, wrong outer join, ambiguous
columns after a dimension lookup).

Two habits run through every notebook and the capstone write:

1. Know the **grain** of each input before you join
2. **Profile → predict → run → verify** on every join

**Reads:** Module 6 curated Parquet plus landing tables that have no curated
version. **Writes (Notebook 07 only):** two Unity Catalog managed Delta tables
for Modules 8–9.

Schemas, join keys, and the `zone_lookup` 21–22 design:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).

## Learning objectives

By the end of this module, you'll be able to:

- Define **grain** and **cardinality** (1:1, 1:M, M:1, M:M) and predict join
  row counts before running
- Write equi-joins in **string**, **list**, and **Boolean** form
- Choose **inner / left / right / full** and explain NULL-key behavior
  (`NULL = NULL` is not true; use **`eqNullSafe`** when NULLs must match)
- Profile keys (`rows`, `countDistinct`, nulls) and resolve duplicates with
  **`Window` + `row_number`** (not `dropDuplicates`) when payloads differ
- Run a **repeated lookup join** (`zone_lookup` for pickup and dropoff),
  clean columns with **`select` / rename**, and **`F.broadcast`** a small
  dimension (confirm in **`.explain()`**)
- Use **`left_semi` / `left_anti`**, and contrast anti-join with **`subtract()`**
- Combine frames with **`union` / `unionByName` / `intersect` /
  `intersectAll` / `subtract` / `exceptAll`**
- Validate stepwise, then write **`trip_enriched`** and
  **`trip_driver_assignment`**

## Prerequisites

Complete Module 6 notebooks **`01`–`04`**. You need:

| Asset | Rows / notes |
|---|---|
| `curated/trip/` | 106 — one per `trip_id`; has pickup/dropoff location IDs |
| `curated/payment/` | 105 — one per `trip_id` (no row for trip 106) |
| `curated/drivers_flat/` | one row per (`driver_id`, `trip_id`); trips 1–100 covered |
| Landing `trip`, `trip_time`, `payment` | 100 each; **1:1** on `trip_id` |
| Landing `zone_lookup` | 22; location_id **21–22** never used by any trip |

Also recall Module 3 **`eqNullSafe`** for NULL-aware join keys.

Does **not** read **`practice/`**. Clean rerun: Module 5 Notebook **99**, Level 2
(see **Cleanup** below).

## Paths and outputs

| Role | Location |
|---|---|
| Landing reads | `/Volumes/rideshare_dev/landing/source_files/{dataset}/` |
| Curated reads (Module 6) | `/Volumes/rideshare_dev/processed/output_files/curated/{name}/` |
| Module writes | Unity Catalog managed tables (below) |

| Output table | Contract |
|---|---|
| `rideshare_dev.processed.trip_enriched` | One row per `curated/trip` `trip_id` (106), left-joined to `trip_time`, `curated/payment`, pickup/dropoff zones |
| `rideshare_dev.processed.trip_driver_assignment` | One row per (`driver_id`, `trip_id`) from `curated/drivers_flat` plus trip attributes |

**Expected NULLs after left joins (intentional):**

- Trips **101–106**: NULL `trip_date` / `hour_of_day` (`trip_time` is only 100 rows)
- Trip **106**: NULL payment columns (`curated/payment` has 105 rows)
- Driver assignment: no unexpected key gaps on trips 1–100

Writes use `saveAsTable` overwrite (Delta by default). Delta internals → Module 10.

**Cleanup:** Module 5 **`99`** Level 2 drops the two Module 7 tables and clears
Module 6 curated Parquet. Confirm **99** has the matching `DROP TABLE IF EXISTS`
statements.

## Runtime and scope

- **Runtime:** Spark **4.0.0** / DBR **17.3 LTS**
- **API:** DataFrame `join`, set ops, `F.broadcast`, `.explain()` — no Spark SQL
  dual-API (Module 9)

**In scope:**

- Grain / cardinality
- Join types and row-count correctness
- Key profiling
- Lookup joins and column naming
- Semi / anti joins
- Set ops
- Broadcast hint
- High-level AQE awareness in the capstone
- Managed-table writes after validation

**Out of scope:**

- Aggregations / windows pedagogy (Module 8) — except Notebook **02**'s narrow
  pre-join dedup (`Window` + `row_number`)
- CTEs / parameterized SQL (Module 9)
- Delta ACID / `MERGE` / time travel (Module 10)
- UC grants (Module 11)
- Join-plan tuning beyond `F.broadcast` (Module 16)

## Notebooks

Seven notebooks, in order. Each includes a short hands-on task (final cell or
integrated practice). Notebooks **01–06** build skills only (**no write**);
**07** writes the managed tables.

| # | Notebook | Reads | Focus |
|---|---|---|---|
| 1 | Grain, Join Syntax, and Unmatched Keys | Landing `trip`, `trip_time` (+ constructed frames). No `payment`. | Grain; 1:1 / 1:M / M:M; string / list / Boolean join; unmatched-keys exercise (expect 3 / 5 / 5 / 7) |
| 2 | Silent Join Failures and Validation | Landing `trip`, `trip_time`, `payment` (+ frames) | M:M fanout; key profiling; `dropDuplicates` vs window dedup; NULL keys + `eqNullSafe`; accidental Cartesian; profile → predict → run → verify |
| 3 | Lookup Joins, Columns, and Broadcast | `zone_lookup` (22); `curated/trip` (106) | Fact vs dim; repeated pickup/dropoff lookup; `select`/rename; unmatched 21–22 **practice**; `-1` threshold then `F.broadcast` + `.explain()` (reused in **07**) |
| 4 | Semi Joins and Anti Joins | `curated/trip` (106), `curated/payment` (105) | `left_semi` / `left_anti` (trip 106 on anti); reverse anti; bridge to **`subtract()`** in **06** |
| 5 | Union and unionByName | Named filters on landing `trip` | `union` vs `unionByName`; column-order trap; `allowMissingColumns`; when `distinct()` after union |
| 6 | Intersect, subtract, and exceptAll | `trip_id <= 60` vs `>= 41` filters | Whole-row set ops; `intersect` vs `intersectAll`; `subtract` vs `exceptAll`; SQL `EXCEPT` naming |
| 7 | Build Unified Curated Tables | Curated trip/payment/drivers_flat; landing `trip_time`, `zone_lookup` | Grain contracts; stepwise left joins + NULL checks; reuse **03** lookup/broadcast; validate with **04**/**06** patterns; write both managed tables; AQE note only |

**Notebook 1 detail — join syntax demos:**

- String: `trip` ↔ `trip_time` on `"trip_id"` → 100
- List: `trip_charges` ↔ `rate_card` — `"trip_id"` alone → 12 (wrong);
  `["trip_id", "charge_type"]` → 4 (correct)
- Boolean: different names (`trip_id` = `trip_no`); same-name duplicate-column trap

**Notebook 3 — apply, don't re-teach:** Boolean form, aliases, profiling, and
left/right/full from **01–02**. New: fact/dim framing, double role-play lookup,
column cleanup, broadcast with/without auto-threshold.

## Minimum privileges required

- Workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the compute used here
- Unity Catalog (objects from Module 5 — no catalog/external-location DDL here):
  - **`USE CATALOG`** on **`rideshare_dev`**
  - **`USE SCHEMA`** on **`rideshare_dev.landing`** and **`rideshare_dev.processed`**
  - **`READ VOLUME`** on **`rideshare_dev.landing.source_files`**
  - **`READ VOLUME`** on **`rideshare_dev.processed.output_files`**
    (curated Parquet — Notebooks **03**, **04**, **07**)
  - **`CREATE TABLE`** on **`rideshare_dev.processed`** (Notebook **07** writes)
