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
  - **`…/landing/source_files/trip_time/`** — 100 rows, Parquet
  - **`…/landing/source_files/zone_lookup/`** — 22 rows, JSON Lines
    (`location_id` 21–22 are not referenced by any trip — see
    [`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md))

The core 100-row landing tables (`trip`, `trip_time`, `payment`) are also used
directly in Notebook 1 where a perfectly 1:1 grain is required for teaching
join types without interference from extended IDs.

**Data source by notebook:**

| Notebook | Landing reads | Processed curated/ reads | Why |
|---|---|---|---|
| 1 | `trip`, `trip_time`, `payment` (100 rows each) + 3 constructed frames | — | Landing tables confirm predictions on clean 1:1 data; constructed frames teach row-count differences, NULL keys, and many-to-many — none of which the clean landing data can show |
| 2 | `zone_lookup` (22 rows) | `curated/trip` (106 rows) | `zone_lookup` has no curated version; rows 21–22 are the only real unmatched-dimension rows in the dataset |
| 3 | — | `curated/trip` (106), `curated/payment` (105) | The 106 vs 105 mismatch is the teaching point |
| 4 | Named filters on landing `trip` | — | See Notebook 4 below for the exact subsets — not an unspecified sample |
| 5 | `trip_time`, `zone_lookup` | `curated/trip`, `curated/payment`, `curated/drivers_flat` | `trip_time` and `zone_lookup` have no curated version |

Recall Module 3 — Data Cleaning, NULL Semantics, and Type Handling for
NULL-aware predicates and **`eqNullSafe`** when join keys may be NULL.

Join keys, table roles, and the `zone_lookup` unmatched-row design:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).

This module does **not** read **`practice/`**.

Rerunning from a clean state: use Module 5
**`99 - Rideshare Project Cleanup and Reset`** Level 2, which wipes Module 6
Parquet curated outputs and drops the two Module 7 managed tables
(`rideshare_dev.processed.trip_enriched` and
`rideshare_dev.processed.trip_driver_assignment`). Notebook 99 must be updated
to include those `DROP TABLE IF EXISTS` statements before Level 2 is used to
reset this module.

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
- `groupBy`, pivots, and window functions (Module 8)
- CTEs and parameterized SQL pipelines (Module 9)
- Delta ACID, time travel, `MERGE` DML, and schema evolution (Module 10)
- Unity Catalog grants (Module 11)
- All join-plan tuning beyond the `F.broadcast` hint — other join hints
  (`merge`, `shuffle_hash`, `shuffle_replicate_nl`), configuring or tuning
  AQE, and skew/salting remedies (Module 16). Notebook 5's high-level AQE
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

Module 7 writes managed Delta tables using `saveAsTable(..., mode="overwrite")`.
Unity Catalog managed tables use Delta format by default on Databricks.
Delta Lake internals — ACID guarantees, transaction log, time travel, schema
evolution, and `MERGE` — are taught in Module 10.

**Cleanup:** Module 5 **`99 - Rideshare Project Cleanup and Reset`** Level 2
clears Module 6 Parquet curated outputs and drops the two Module 7 managed
tables. This module has no dedicated cleanup notebook. Notebook 99 must be
updated to include the `DROP TABLE IF EXISTS` statements for
`rideshare_dev.processed.trip_enriched` and
`rideshare_dev.processed.trip_driver_assignment` before Level 2 is used.

## Notebook navigation

Five notebooks, in this order:

1. **Join Types and Row-Count Correctness**

   *Reads:* landing `trip`, `trip_time`, `payment` — 100 rows each, clean 1:1
   grain — plus 3 constructed frames (below). No curated tables in this
   notebook.

   - **Grain orientation** — one row represents one business entity at a
     defined level of detail; a join may preserve, widen, or multiply the
     grain depending on cardinality
   - **Cardinality vocabulary** — 1:1, 1:M, M:1, M:M; how each predicts the
     output row count before running a single cell
   - **Join-condition syntax** — three forms, taught before the first join
     runs:
     - Single shared column name as a string: no duplicate column in the
       result; both sides must have a column of that name
     - List of shared column names: composite equi-join, brief syntax
       example only — no course dataset requires a composite key
     - Boolean column condition: explicit `df_left.col == df_right.col`;
       when the key columns have different names, Spark retains both in the
       result; Notebook 2 relies on this form for the repeated zone lookup
   - **Constructed frame 1 — unmatched keys**: left `trip_id`
     `[1, 2, 3, 4, 5]`, right `trip_id` `[3, 4, 5, 6, 7]`; predict, then
     verify inner=3, left=5, right=5, full outer=7 — this is the demo that
     makes the four join types' row-count differences visible
   - **Four join types on rideshare data** — inner, left, right, full outer
     on `trip_id` using landing `trip`, `trip_time`, and `payment`; predict
     counts, run each join, verify with `count()`; **all four** join types
     return 100 rows here — the landing tables are a perfect 1:1 match, so
     this step confirms the prediction rather than revealing a difference
   - **Constructed frame 2 — many-to-many**: left `trip_id` `[1, 1, 2]`,
     right `trip_id` `[1, 1, 3]` (not production keys); predict, then verify
     inner=4 — the 2×2 fanout on key 1 shows row multiplication when neither
     side has a unique key
   - **Key profiling before joining** — count total rows and distinct key
     values; if they differ, investigate before joining; apply a deterministic
     resolution rule; validate uniqueness; `dropDuplicates()` alone is not
     sufficient when duplicate rows carry different payload values
   - **Constructed frame 3 — NULL keys**: left `trip_id` `[1, 2, NULL]`,
     right `trip_id` `[2, 3, NULL]`; predict, then verify inner=1 (only key 2
     matches — standard equality never matches NULL, so inner join excludes
     both sides' NULL-key rows; left preserves left with NULL right-side
     columns; right preserves right; full outer preserves both); callback to
     Module 3 for `eqNullSafe` when NULL equality is genuinely intended
   - **Pre-join and post-join validation habit** — check grain and count
     inputs, predict output count, verify after join; use this pattern in
     every notebook and especially in Notebook 5
   - Gotcha: a missing or always-true join condition produces an accidental
     Cartesian product; use `crossJoin()` only when a full cross product is
     intentional
   - Skill-building only — **no write**

2. **Lookup Joins, Aliases, and Column Selection**

   *Reads:* landing `zone_lookup` (22 rows, dimension); `curated/trip`
   (106 rows). `zone_lookup` has no curated version.

   - **Repeated lookup join, and why it needs a Boolean condition** —
     `zone_lookup` is joined twice to `curated/trip`: once on
     `pickup_location_id = location_id` and once on
     `dropoff_location_id = location_id` — a role-playing dimension pattern,
     not a self-join. Pickup and dropoff use different key column names on
     the left side, so the string-shorthand form from Notebook 1 cannot
     express this; the Boolean form is required, and it produces duplicate
     `location_id`, `borough_name`, `zone_name`, `service_zone` columns
   - **Lookup-key uniqueness check** — verify `zone_lookup.location_id` is
     unique before joining; a non-unique dimension key would silently multiply
     trip rows
   - **Real unmatched-dimension rows** — `zone_lookup` rows 21–22
     (`Newark Airport`, `Hoboken Terminal`) are never referenced by any trip.
     A **left** join from `curated/trip` never surfaces them (every trip's
     location IDs are in 1–20, so the lookup always matches). Reverse the
     join — `zone_lookup` **right** joined to `curated/trip`, or a **full
     outer** — and rows 21–22 appear with NULL trip columns. This is the
     only pair in the dataset with a real unmatched dimension row; use it
     to confirm the Notebook 1 prediction rules on production-shaped data
   - **Aliases and qualified references** — `alias()` on each `zone_lookup`
     instance; resolve duplicate columns with `df.alias.col` or
     `F.col("alias.col")`
   - **Explicit `select`** — choose and rename output columns (e.g.,
     `pickup_borough`, `dropoff_zone`) rather than carrying all columns
     forward
   - **`F.broadcast`** on `zone_lookup`; read the `BroadcastHashJoin` node in
     **`.explain("formatted")`** — inspection only, no physical-plan tuning
   - Skill-building only — **no write** (Notebook 5 reuses this lookup,
     alias, `select`, and broadcast pattern to produce the curated output)

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
     compares entire rows and requires identical schemas. Notebook 5 reuses
     both techniques together as a validation gate before its enrichment
     writes
   - Skill-building only — **no write**

4. **Set Operations**

   *Reads:* named filters on landing `trip` (100 rows) — no curated tables.

   - **`union()` vs `unionByName()` — column-order bug**: `premium_trips =
     trip.filter(service_type == "Premium").select("trip_id",
     "service_type", "trip_distance_miles")` (15 rows) and `xl_trips =
     trip.filter(service_type == "XL").select("service_type", "trip_id",
     "trip_distance_miles")` (12 rows, same three columns in a different
     order). `union()` matches by **position**, so `xl_trips.trip_id` values
     land in the `service_type` column of the result — silently wrong.
     `unionByName()` matches by name and returns the correct 27-row result
   - **`unionByName(allowMissingColumns=True)`** — reuse `premium_trips`
     with a fourth column, `ride_duration_mins` (15 rows, 4 columns), against
     an `xl_trips` variant with that column dropped (12 rows, 3 columns);
     `allowMissingColumns=True` fills NULL for the 12 XL rows; use only when
     the schema difference is known and intentional, not as a catch-all that
     hides unexpected schema contract changes
   - **Duplicate rows after `union`** — `union()` preserves duplicates;
     `distinct()` after `union` is justified only when duplicate rows are
     genuinely equivalent and should be collapsed, not as a routine cleanup
   - **Whole-row comparison semantics** — `intersect()`, `intersectAll()`,
     `subtract()`, and `exceptAll()` compare **entire rows**, not just keys;
     a learner expecting key-based matching will get unexpected results
   - **`intersect()` vs `intersectAll()`, and `subtract()` vs
     `exceptAll()`**: `early_trips = trip.filter(trip_id <= 60)` (60 rows)
     and `late_trips = trip.filter(trip_id >= 41)` (60 rows) overlap on
     `trip_id` 41–60. `intersect()` returns those 20 rows distinct;
     `intersectAll()` would preserve duplicates if either subset had them.
     `subtract(early_trips, late_trips)` returns the 40 rows unique to
     `early_trips` (`trip_id` 1–40); `exceptAll()` preserves duplicates from
     the left side instead of de-duplicating
   - Note: `EXCEPT` is SQL clause syntax; `subtract()` is the PySpark
     DataFrame method for distinct row difference
   - Skill-building only — **no write**

5. **Build Unified Curated Tables**

   *Reads:* `curated/trip` (106 rows), `curated/payment` (105 rows),
   `curated/drivers_flat`, landing `trip_time` (100 rows), landing
   `zone_lookup` (22 rows). `trip_time` and `zone_lookup` have no curated
   version.

   - **State input grain contracts** before any join — one row per `trip_id`
     in `curated/trip`; one row per `trip_id` in `curated/payment`; one row
     per (`driver_id`, `trip_id`) in `curated/drivers_flat`; one row per
     `location_id` in `zone_lookup`
   - **Key uniqueness profiling** on each join key before the first join
   - **Stepwise enrichment** — add one dimension or extension at a time;
     after each left join, count rows and count NULLs on the
     **business-significant joined columns** (e.g., `trip_date` after the
     `trip_time` join; `base_fare_amount` after the payment join); confirm
     against the expected NULL documentation above
   - **Apply lookup-join, alias, `select`, and broadcast patterns from
     Notebook 2** for the zone-lookup step (pickup and dropoff roles);
     `zone_lookup` stays small enough to broadcast here too
   - **Validation gate using Notebook 3 and 4 techniques** — before trusting
     the expected-NULL counts, confirm the exact unmatched key sets
     directly with `subtract()` (trip vs. `trip_time` keys) and `left_anti`
     (trip vs. `payment`) — the results must match the Expected NULLs
     documentation above; this reuses the anti-join and `subtract()`
     contrast from Notebook 3's bridge instead of relying on NULL counts
     alone
   - **Explicit final column selection** — choose the output schema
     intentionally; do not carry forward every intermediate column
   - **Write only after all validation steps pass** — predicted and verified
     row counts match; expected NULLs confirmed; output schema correct
   - Write `rideshare_dev.processed.trip_enriched` and
     `rideshare_dev.processed.trip_driver_assignment` as managed Delta tables
     using `saveAsTable` with overwrite mode; exact write pattern is finalized
     during notebook authoring
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
  - **`CREATE TABLE`** on **`rideshare_dev.processed`**
    (for `saveAsTable` in Notebook 5)
