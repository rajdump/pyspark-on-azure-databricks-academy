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
    after `explode` on `trips_assigned`; all `trip_id` values fall within
    1–100
- **Landing datasets** (no curated version exists for these):
  - **`…/landing/source_files/trip_time/`** — 100 rows, Parquet
  - **`…/landing/source_files/zone_lookup/`** — 20 rows, JSON Lines

The core 100-row landing tables (`trip`, `trip_time`, `payment`) are also used
directly in Notebook 1 where a perfectly 1:1 grain is required for teaching
join types without interference from extended IDs.

**Data source by notebook:**

| Notebook | Landing reads | Processed curated/ reads | Why |
|---|---|---|---|
| 1 | `trip`, `trip_time`, `payment` (100 rows each) | — | Clean 1:1 grain; no surprises from extended IDs |
| 2 | `zone_lookup` (20 rows) | `curated/trip` (106 rows) | `zone_lookup` has no curated version |
| 3 | — | `curated/trip` (106), `curated/payment` (105) | The 106 vs 105 mismatch is the teaching point |
| 4 | Small in-notebook subsets | Small in-notebook subsets | Controlled data for set-op examples |
| 5 | `trip_time`, `zone_lookup` | `curated/trip`, `curated/payment`, `curated/drivers_flat` | `trip_time` and `zone_lookup` have no curated version |

Recall Module 3 — Data Cleaning, NULL Semantics, and Type Handling for
NULL-aware predicates and **`eqNullSafe`** when join keys may be NULL.

Join keys and table roles:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).

This module does **not** read **`practice/`**.

Rerunning from a clean state: use Module 5
**`99 - Rideshare Project Cleanup and Reset`** Level 2 to wipe Module 6
Parquet curated outputs, then drop the two Module 7 managed tables manually:

```
DROP TABLE IF EXISTS rideshare_dev.processed.trip_enriched;
DROP TABLE IF EXISTS rideshare_dev.processed.trip_driver_assignment;
```

## Approach and boundaries

**Runtime baseline:** Apache Spark **4.0.0** on Databricks Runtime **17.3 LTS**.
Join APIs and set-operation methods below match the Spark 4.0.0 documentation.

**API used:** PySpark **DataFrame** `join`, set-operation methods, and
`F.broadcast`. `spark.sql` may appear only for brief plan inspection —
dual-API pipeline work belongs in Module 9.

**In scope:** DataFrame grain and cardinality; join types and row-count
correctness; key profiling and pre-join validation; lookup joins and column
naming; semi/anti joins; `union` / `unionByName` / `intersect` /
`intersectAll` / `subtract` / `exceptAll`; broadcast hint and high-level AQE
awareness; capstone write to managed Delta tables.

**Out of scope:** `groupBy`, pivots, and window functions (Module 8); CTEs
and parameterized SQL pipelines (Module 9); Delta ACID, time travel, `MERGE`
DML, and schema evolution (Module 10); Unity Catalog grants (Module 11).
`F.broadcast` is the only join strategy taught here — AQE and all other join
tuning belong to Module 16.

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
- `trip_driver_assignment`: `curated/drivers_flat` trip IDs fall within 1–100
  (verified from `drivers.xml`); no unexpected key NULLs from driver
  assignment

Module 7 writes managed Delta tables using `saveAsTable(..., mode="overwrite")`.
Unity Catalog managed tables use Delta format by default on Databricks.
Delta Lake internals — ACID guarantees, transaction log, time travel, schema
evolution, and `MERGE` — are taught in Module 10.

**Cleanup:** Module 5 **`99 - Rideshare Project Cleanup and Reset`** Level 2
clears Module 6 Parquet curated outputs. Drop Module 7 managed tables manually
(see cleanup commands in Prerequisites above). This module has no dedicated
cleanup notebook.

## Notebook navigation

Five notebooks, in this order:

1. **Join Types and Row-Count Correctness**

   *Reads:* landing `trip`, `trip_time`, `payment` — 100 rows each, clean 1:1
   grain. No curated tables in this notebook.

   - **Grain orientation** — one row represents one business entity at a
     defined level of detail; every join changes or preserves the grain
   - **Cardinality vocabulary** — 1:1, 1:M, M:1, M:M; how each predicts the
     output row count before running a single cell
   - **Join-condition syntax** — three forms:
     - Single shared column name as a string: no duplicate column in the
       result
     - List of shared column names: composite equi-join, no duplicates
     - Boolean column condition: explicit `df_left.col == df_right.col`;
       produces duplicate columns requiring qualified references
   - **Four join types** — inner, left, right, full outer on `trip_id`; predict
     counts from the 1:1 landing grain, run each join, verify with `count()`
   - **Many-to-many** — deliberate small in-notebook example (not production
     keys) to show row multiplication when neither side has a unique key
   - **Key profiling before joining** — count total rows and distinct key
     values; if they differ, investigate before joining; apply a deterministic
     resolution rule; validate uniqueness; `dropDuplicates()` alone is not
     sufficient when duplicate rows carry different payload values
   - **NULL join-key behaviour** — standard equality never matches NULL:
     inner join excludes both sides' NULL-key rows; left preserves left with
     NULL right-side columns; right preserves right; full outer preserves
     both; callback to Module 3 for `eqNullSafe` when NULL equality is
     genuinely intended
   - **Pre-join and post-join validation habit** — check grain and count
     inputs, predict output count, verify after join; use this pattern in
     every notebook and especially in Notebook 5
   - Gotcha: a missing or always-true join condition produces an accidental
     Cartesian product; use `crossJoin()` only when a full cross product is
     intentional
   - Skill-building only — **no write**

2. **Lookup Joins, Aliases, and Column Selection**

   *Reads:* landing `zone_lookup` (20 rows, dimension); `curated/trip`
   (106 rows). `zone_lookup` has no curated version.

   - **Repeated lookup join** — `zone_lookup` is joined twice to `curated/trip`:
     once on `pickup_location_id = location_id` and once on
     `dropoff_location_id = location_id`; this is a role-playing dimension
     pattern, not a self-join
   - **Lookup-key uniqueness check** — verify `zone_lookup.location_id` is
     unique before joining; a non-unique dimension key would silently multiply
     trip rows
   - **Why Boolean column condition** — pickup and dropoff use different key
     column names on the left side (`pickup_location_id` vs
     `dropoff_location_id`) so a string shorthand cannot be used; Boolean
     condition is required; this produces duplicate `location_id`,
     `borough_name`, `zone_name`, `service_zone` columns
   - **Aliases and qualified references** — `alias()` on each `zone_lookup`
     instance; resolve duplicate columns with `df.alias.col` or
     `F.col("alias.col")`
   - **Explicit `select`** — choose and rename output columns (e.g.,
     `pickup_borough`, `dropoff_zone`) rather than carrying all columns
     forward
   - **`F.broadcast`** on `zone_lookup`; read the `BroadcastHashJoin` node in
     **`.explain("formatted")`** — inspection only, no physical-plan tuning
   - Skill-building only — **no write** (Notebook 5 applies this pattern to
     produce the curated output)

3. **Semi Joins and Anti Joins**

   *Reads:* `curated/trip` (106 rows), `curated/payment` (105 rows). The
   one-row difference between these tables is the teaching data.

   - **`left_semi`** — returns only left-side rows that have a match; does not
     widen the DataFrame; trips that have a payment record
   - **`left_anti`** — returns only left-side rows without a match; trips that
     have no payment record (`trip_id` 106 is the expected result)
   - **Reverse anti join** — payments without a matching trip record; expected
     result is zero rows, which confirms key integrity between the two cleaned
     datasets — zero unmatched rows is informative, not a failure
   - **Why `left_semi` / `left_anti` instead of inner + distinct** — inner
     join followed by `distinct` may collapse genuine duplicate rows in the
     payload and still widens the intermediate result before deduplication;
     semi/anti never produce a wider DataFrame and express membership intent
     directly
   - Bridge to Notebook 4: `left_anti` and `subtract()` both answer "rows in
     A not in B" — anti-join is key-based and works across schemas; `subtract()`
     compares entire rows and requires identical schemas
   - Skill-building only — **no write**

4. **Set Operations**

   *Reads:* small in-notebook subsets built from rideshare data.

   - **`union()` vs `unionByName()`** — `union()` matches columns by
     **position**, not name; columns in different orders silently produce
     wrong results; `unionByName()` matches by name and is safer for most
     production scenarios
   - **`unionByName(allowMissingColumns=True)`** — fills missing columns with
     NULL; use only when schema differences are known and intentional;
     do not use as a catch-all that hides unexpected schema contract changes
   - **Duplicate rows after `union`** — `union()` preserves duplicates;
     `distinct()` after `union` is justified only when duplicate rows are
     genuinely equivalent and should be collapsed, not as a routine cleanup
   - **Whole-row comparison semantics** — `intersect()`, `intersectAll()`,
     `subtract()`, and `exceptAll()` compare **entire rows**, not just keys;
     a learner expecting key-based matching will get unexpected results
   - **`intersect()` vs `intersectAll()`** — `intersect()` returns distinct
     matching rows; `intersectAll()` preserves duplicates
   - **`subtract()` vs `exceptAll()`** — `subtract()` returns distinct rows
     in left not in right; `exceptAll()` preserves duplicates from the left
   - Note: `EXCEPT` is SQL clause syntax; `subtract()` is the PySpark
     DataFrame method for distinct row difference
   - Skill-building only — **no write**

5. **Build Unified Curated Tables**

   *Reads:* `curated/trip` (106 rows), `curated/payment` (105 rows),
   `curated/drivers_flat`, landing `trip_time` (100 rows), landing
   `zone_lookup` (20 rows). `trip_time` and `zone_lookup` have no curated
   version.

   - **State input grain contracts** before any join — one row per `trip_id`
     in `curated/trip`; one row per `trip_id` in `curated/payment`; one row
     per (`driver_id`, `trip_id`) in `curated/drivers_flat`; one row per
     `location_id` in `zone_lookup`
   - **Key uniqueness profiling** on each join key before the first join
   - **Stepwise enrichment** — add one dimension or extension at a time;
     after each left join, count rows and count NULLs on the newly joined
     columns; confirm against the expected NULL documentation above
   - **Apply lookup-join and alias patterns from Notebook 2** for the
     zone-lookup step (pickup and dropoff roles)
   - **Explicit final column selection** — choose the output schema
     intentionally; do not carry forward every intermediate column
   - **Write only after all validation steps pass** — predicted and verified
     row counts match; expected NULLs confirmed; output schema correct
   - Write `rideshare_dev.processed.trip_enriched` and
     `rideshare_dev.processed.trip_driver_assignment` using
     `saveAsTable(..., mode="overwrite")`
   - **AQE note:** Databricks may adapt the physical join strategy at runtime.
     AQE and advanced join tuning are covered in Module 16.

## Exercises

Each notebook listed in **Notebook navigation** ends with a short hands-on
task that repeats the demonstrated pattern on slightly different keys, columns,
or membership questions.

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
    (to read Module 6 curated Parquet outputs in Notebooks 2–5)
  - **`WRITE VOLUME`** on **`rideshare_dev.processed.output_files`**
    (retained for consistency with Module 6; Notebook 5 writes managed tables,
    not Volume files)
  - **`CREATE TABLE`** on **`rideshare_dev.processed`**
    (for `saveAsTable` in Notebook 5)
