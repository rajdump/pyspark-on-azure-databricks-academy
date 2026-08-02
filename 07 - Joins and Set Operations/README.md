# Module 7 — Joins and Set Operations

## Purpose

Combine rideshare tables with explicit join types and set logic so row counts
and keys stay predictable — no silent duplication from many-to-many joins,
no lost rows from the wrong outer join, and no ambiguous column names after a
dimension lookup.

The module introduces two core production habits: **know the grain of every
input before you join** and **predict row count, run the join, then verify**.
Both habits carry through every notebook and culminate in the capstone write.

Module 7 reads Module 6 **curated** Parquet outputs and **landing** datasets
where no curated version exists, then writes two **Unity Catalog managed Delta
tables** consumed by Module 8 aggregations and Module 9 SQL synthesis.

## Learning objectives

By the end of this module, you'll be able to:

- Define **DataFrame grain** and use **cardinality** (1:1, 1:M, M:1, M:M)
  as the vocabulary for predicting join row counts before running any query
- Write join conditions in all three syntactic forms: single shared column
  name, list of shared column names, and Boolean column condition
- Choose **inner**, **left**, **right**, and **full outer** joins and predict
  exactly how each affects row count when input grains differ
- Understand NULL join-key behaviour by join type: standard equality never
  matches NULL, so inner joins exclude NULL-key rows; left, right, and full
  outer joins preserve unmatched rows with NULL on the non-driving side
- Profile join keys before joining — count total rows and distinct key values
  — and apply a deterministic resolution rule when duplicates are found
- Join `trip` to `zone_lookup` twice in pickup and dropoff roles using table
  aliases — a **repeated lookup join** (role-playing dimension pattern)
- Resolve duplicate column names after joins using **`alias`**, qualified
  column references, and explicit **`select`**
- Use **`left_semi`** and **`left_anti`** joins to answer set-membership
  questions without widening row count
- Contrast **`left_anti`** with **`subtract()`**: anti-join is key-based
  (schemas may differ); `subtract()` compares full rows (identical schema
  required)
- Combine DataFrames with **`union`**, **`unionByName`**, **`intersect`**,
  **`intersectAll`**, **`subtract`**, and **`exceptAll`**, with awareness
  that `union()` matches columns by **position** and `subtract()`/`intersect()`
  compare **whole rows**
- Apply **`F.broadcast`** on a small dimension table and read the broadcast
  node in **`.explain("formatted")`**
- Validate grain and row counts at each join step, confirm expected NULLs,
  and write two managed Delta tables only after validation passes

## Prerequisites

Module 6 — Built-in Functions, Complex Types, and UDF Alternatives (notebooks
**`01 - Column Transforms with Built-in Functions`** through
**`04 - Built-ins First, When (Not) to Use UDFs`**). You should have:

- **Module 6 curated outputs** (processed layer — these are Parquet):
  - **`…/curated/trip/`** — 106 rows, one per `trip_id`, cleaned from
    `bad_trip_data.csv`; preserves `pickup_location_id` and
    `dropoff_location_id` for zone lookup joins
  - **`…/curated/payment/`** — 105 rows, one per `trip_id`, cleaned from
    `bad_payment_data.csv`
  - **`…/curated/drivers_flat/`** — one row per (`driver_id`, `trip_id`)
    after `explode` on `trips_assigned`; all 100 trips in the range 1–100
    are each assigned to exactly one driver — zero gaps (verified from
    `drivers.xml`)
- **Landing datasets** (no curated version exists for these):
  - **`…/landing/source_files/trip/`** — 100 rows, CSV (`trip.csv`)
  - **`…/landing/source_files/trip_time/`** — 100 rows, Parquet
  - **`…/landing/source_files/payment/`** — 100 rows, Avro
  - **`…/landing/source_files/zone_lookup/`** — 22 rows, JSON Lines
    (`location_id` 21–22 are not referenced by any trip — see
    [`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md))

The core 100-row landing tables (`trip`, `trip_time`, `payment`) are **1:1** on
`trip_id`. Per-notebook reads (including constructed frames) are listed under
**Notebook navigation**.

**Data source by notebook:**

| Notebook | Landing reads | Processed curated/ reads | Why |
|---|---|---|---|
| 1 | `trip`, `trip_time` (+ constructed frames) | — | Grain, join syntax, unmatched-keys exercise (no `payment`) |
| 2 | `trip`, `trip_time`, `payment` (100 rows each) + constructed frames | — | Silent join failures: M:M, NULL keys, Cartesians; validation habit |
| 3–4 | `zone_lookup` (22 rows) | `curated/trip` (106 rows) | Rows 21–22 are unmatched dimension rows; lookup pattern split across two notebooks |
| 5 | — | `curated/trip` (106), `curated/payment` (105) | The 106 vs 105 mismatch is the teaching point |
| 6–7 | Named filters on landing `trip` | — | Set operations split: union paths vs intersect/subtract paths |
| 8 | `trip_time`, `zone_lookup` | `curated/trip`, `curated/payment`, `curated/drivers_flat` | Capstone enrichment and managed-table writes |

Recall Module 3 — Data Cleaning, NULL Semantics, and Type Handling for
NULL-aware predicates and **`eqNullSafe`** when join keys may be NULL.

Join keys, table roles, and the `zone_lookup` unmatched-row design:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).

This module does **not** read **`practice/`**.

Rerunning from a clean state: Module 5 **`99 - Rideshare Project Cleanup and Reset`**
Level 2 — see **Cleanup** under Approach and boundaries below.

## Approach and boundaries

**Runtime baseline:** Apache Spark **4.0.0** on Databricks Runtime **17.3 LTS**.
Join APIs and set-operation methods below match the Spark 4.0.0 documentation.

**API used:** PySpark **DataFrame** `join`, set-operation methods, and
`F.broadcast`. This module uses the DataFrame API only. Use
`DataFrame.explain("formatted")` for plan inspection — `spark.sql` and
dual-API patterns belong in Module 9.

**In scope:** DataFrame grain and cardinality; join types and row-count
correctness; key profiling and pre-join validation; lookup joins and column
naming; semi/anti joins; `union` / `unionByName` / `intersect` /
`intersectAll` / `subtract` / `exceptAll`; broadcast hint and high-level AQE
awareness; capstone write to managed Delta tables.

**Out of scope:**
- `groupBy`, pivots, and window functions (Module 8) — except the narrow
  pre-join duplicate-resolution pattern in Notebook **02** (`groupBy` +
  `agg` to keep one deterministic row per key). Aggregation pedagogy stays
  in Module 8
- CTEs and parameterized SQL pipelines (Module 9)
- Delta ACID, time travel, `MERGE` DML, and schema evolution (Module 10)
- Unity Catalog grants (Module 11)
- All join-plan tuning beyond the `F.broadcast` hint — other join hints
  (`merge`, `shuffle_hash`, `shuffle_replicate_nl`), configuring or tuning
  AQE, and skew/salting remedies (Module 16). Notebook **08**'s high-level AQE
  *awareness* — knowing the runtime may adapt the plan — stays in scope

Schemas, column names, join keys, and Volume path rules:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).

**Paths and tables:**

| Role | Location |
|---|---|
| Reads — landing | `/Volumes/rideshare_dev/landing/source_files/{dataset}/` |
| Reads — curated Parquet (Module 6 outputs) | `/Volumes/rideshare_dev/processed/output_files/curated/{output_name}/` |
| Module 7 writes | Unity Catalog managed tables — see table below |

**Module 7 output tables:**

| Table | Grain / contract |
|---|---|
| `rideshare_dev.processed.trip_enriched` | One row per `trip_id` from `curated/trip` (106 rows), left-joined to landing `trip_time`, `curated/payment`, and pickup/dropoff `zone_lookup` attributes |
| `rideshare_dev.processed.trip_driver_assignment` | One row per (`driver_id`, `trip_id`) from `curated/drivers_flat`, joined to trip attributes for downstream KPIs |

**Expected NULLs after left joins — intentional, not data bugs:**

- `trip_enriched`: `trip_id` 101–106 have NULL `trip_date` / `hour_of_day`
  because landing `trip_time` covers only the core 100 rows; `curated/trip`
  was extended to 106 by Module 6 cleaning
- `trip_enriched`: `trip_id` 106 has NULL payment columns because
  `curated/payment` has 105 rows (no payment record for `trip_id` 106)
- `trip_driver_assignment`: `curated/drivers_flat` covers all 100 trips in
  1–100 with zero gaps (verified from `drivers.xml`); no unexpected key
  NULLs from driver assignment

Module 7 writes managed Delta tables using `saveAsTable` with overwrite mode.
Unity Catalog managed tables use Delta format by default on Databricks.
Delta Lake internals — ACID guarantees, transaction log, time travel, schema
evolution, and `MERGE` — are taught in Module 10.

**Cleanup:** Module 5 **`99 - Rideshare Project Cleanup and Reset`** Level 2
clears Module 6 Parquet curated outputs and drops
`rideshare_dev.processed.trip_enriched` and
`rideshare_dev.processed.trip_driver_assignment`. Ensure Notebook **99** includes
those `DROP TABLE IF EXISTS` statements before using Level 2.

## Notebook navigation

Eight notebooks, in this order:

1. **Grain, Join Syntax, and Unmatched Keys**

   *Reads:* landing `trip` (CSV) and `trip_time` (Parquet), 100 rows each.
   Constructed frames: `trip_charges`, `rate_card`, unmatched-key mini-frames.
   Does **not** read landing **`payment`** (wide, one row per `trip_id` —
   Notebook **02**).

   - **Grain** — what one row represents; `count` vs `countDistinct` on
     `trip_id` (check both sides before joining)
   - **Cardinality** — labels 1:1 / 1:M / M:1 / M:M; landing `trip` ↔
     `trip_time` is **1:1**; intro sketch is **1:M**; §3.2
     `trip_charges` ↔ `rate_card` on `trip_id` alone is **M:M** (12 rows);
     fuller M:M construct in **02**
   - **Join syntax**
     - **String** — `trip` ↔ `trip_time` on `"trip_id"` (coalesced key;
       predict **100**)
     - **List** — `trip_charges` ↔ `rate_card`: `"trip_id"` only → **12**
       (wrong) vs `["trip_id", "charge_type"]` → **4** (correct)
     - **Boolean** — different names (`trip_id` = `trip_no`); same-name
       duplicate-column gotcha
   - **Exercise — unmatched keys** — left `[1…5]`, right `[3…7]`;
     predict/verify inner / left / right / full (expect 3 / 5 / 5 / 7);
     applies SQL join-type knowledge to PySpark row counts
   - Skill-building only — **no write**

2. **Silent Join Failures and Validation**

   *Reads:* landing `trip`, `trip_time`, `payment` (100 rows each) plus
   constructed mini-frames. No curated tables.

   - **Clean 1:1 baseline** — all four join types return 100 on landing data;
     baseline signal (not proof) that grain and overlap are correct
   - **M:M fanout** — constructed frame `[1, 1, 2]` ↔ `[1, 1, 3]`; predict
     inner=4; formula: count(left) × count(right) per key
   - **Key profiling** — rows vs `countDistinct(key)` vs NULL-key count;
     `countDistinct` ignores NULLs so uniqueness requires zero NULLs confirmed
   - **Duplicate resolution** — `dropDuplicates()` survivor is non-deterministic;
     `groupBy` + `agg` is deterministic; verify grain after resolution
   - **NULL keys** — `[1, 2, NULL]` ↔ `[2, 3, NULL]`; predict/verify inner,
     left, right, full outer; `eqNullSafe` when NULL must match NULL (can
     itself fan out with multiple NULLs per side)
   - **Cartesian products** — intentional `crossJoin()` vs always-true
     anti-pattern (`F.lit(True)`); demonstrates row explosion risk
   - **Validation exercise** — full workflow: profile → predict → run → verify
     (catches row-count failures; does not prove value correctness)
   - Skill-building only — **no write**

3. **Lookup Joins and Unmatched Dimensions**

   *Reads:* landing `zone_lookup` (22 rows); `curated/trip` (106 rows).

   - **Repeated lookup join (Boolean condition)** — join `zone_lookup` twice to
     `curated/trip`: `pickup_location_id = location_id` and
     `dropoff_location_id = location_id` (role-playing dimension, not a self-join)
   - **Lookup-key uniqueness check** on `zone_lookup.location_id`
   - **Real unmatched-dimension rows** — `location_id` 21–22 never referenced by
     trips; left join from trips never surfaces them; **right** or **full outer**
     from `zone_lookup` shows NULL trip columns on 21–22
   - Skill-building only — **no write** (Notebook **08** reuses this lookup step)

4. **Aliases, Column Selection, and Broadcast**

   *Reads:* same as Notebook **03** (continue the lookup join from pickup/dropoff
   Boolean joins).

   - **Aliases and qualified references** — `alias()` on each `zone_lookup`
     instance; `F.col("alias.col")`
   - **Explicit `select`** — rename to `pickup_borough`, `dropoff_zone`, etc.
   - **`F.broadcast`** on `zone_lookup`; read **`BroadcastHashJoin`** in
     **`.explain("formatted")`** — inspection only
   - Skill-building only — **no write**

5. **Semi Joins and Anti Joins**

   *Reads:* `curated/trip` (106), `curated/payment` (105).

   - **`left_semi`** and **`left_anti`** on `trip_id`; `trip_id` **106** on anti
   - **Reverse anti join** — payments without trips (expect zero rows)
   - **Why semi/anti vs inner + distinct**
   - Bridge to Notebook **07**: anti-join vs **`subtract()`** (key-based vs whole-row)
   - Skill-building only — **no write**

6. **Union and unionByName**

   *Reads:* named filters on landing `trip`.

   - **`union()` vs `unionByName()`** — `premium_trips =
     trip.filter(service_type == "Premium").select("trip_id", "service_type",
     "trip_distance_miles")` (15 rows) vs `xl_trips =
     trip.filter(service_type == "XL").select("service_type", "trip_id",
     "trip_distance_miles")` (12 rows, column-order trap)
   - **`unionByName(allowMissingColumns=True)`** — fourth column on Premium only;
     use only for known schema differences
   - **Duplicate rows after `union`** — when **`distinct()`** is justified
   - Skill-building only — **no write**

7. **Intersect, subtract, and exceptAll**

   *Reads:* `early_trips = trip.filter(trip_id <= 60)` (60 rows);
   `late_trips = trip.filter(trip_id >= 41)` (60 rows); overlap on 41–60.

   - **Whole-row comparison semantics** for `intersect`, `intersectAll`,
     `subtract`, `exceptAll`
   - **`intersect()` vs `intersectAll()`**; **`subtract()` vs `exceptAll()`**
   - Note: SQL **`EXCEPT`** vs PySpark **`subtract()`**
   - Skill-building only — **no write**

8. **Build Unified Curated Tables**

   *Reads:* `curated/trip`, `curated/payment`, `curated/drivers_flat`, landing
   `trip_time`, landing `zone_lookup`.

   - **State input grain contracts** and key profiling before joins
   - **Stepwise enrichment** with NULL checks on business columns after each left join
   - **Reuse Notebook 03–04** lookup, alias, `select`, broadcast for zones
   - **Validation gate** — **`left_anti`** and **`subtract()`** from Notebooks **05**
     and **07** before trusting expected NULLs
   - **Explicit final column selection**; write only after validation passes
   - Write `rideshare_dev.processed.trip_enriched` and
     `rideshare_dev.processed.trip_driver_assignment` via **`saveAsTable`**
     overwrite mode
   - **AQE note** — high-level awareness only (Module 16 for tuning)

## Exercises

Each notebook in **Notebook navigation** ends with a short hands-on task
(predict/verify, transform, or membership check) using that notebook's
patterns.

## Minimum privileges required

- Databricks workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the
  compute used in this module
- Unity Catalog (objects created in Module 5 — no **`CREATE CATALOG`**,
  external location, or volume DDL in this module):
  - **`USE CATALOG`** on **`rideshare_dev`**
  - **`USE SCHEMA`** on **`rideshare_dev.landing`** and
    **`rideshare_dev.processed`**
  - **`READ VOLUME`** on **`rideshare_dev.landing.source_files`**
  - **`READ VOLUME`** on **`rideshare_dev.processed.output_files`**
    (Module 6 curated Parquet — Notebooks **03–08**)
  - **`CREATE TABLE`** on **`rideshare_dev.processed`**
    (for `saveAsTable` in Notebook **08**)
