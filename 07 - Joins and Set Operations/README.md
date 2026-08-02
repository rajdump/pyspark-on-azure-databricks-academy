# Module 7 — Joins and Set Operations

## Purpose

Combine rideshare tables with explicit join types and set logic so row counts
and keys stay understandable — no silent duplication from many-to-many joins,
no accidental Cartesian products, no lost rows from the wrong outer join, and
no ambiguous duplicate column names after a dimension lookup.

The module reads Module 6 **curated** outputs and **landing** datasets where
join keys or grain require them, then writes new **curated** unified views for
Module 8 aggregations and Module 9 SQL synthesis. Throughout, the habit is
**predict row count, run the join, verify** — especially in the capstone
notebook.

## Learning objectives

By the end of this module, you'll be able to:

- Choose **inner**, **left**, **right**, and **full outer** joins and predict
  how each affects row count when keys are one-to-one vs many-to-one
- Recognize an accidental **cross join** from a missing or wrong join
  condition, and use **`crossJoin()`** / **`how="cross"`** only when a true
  Cartesian product is intended
- Recall that **NULL join keys do not match** in an equi-join (rows drop
  silently) and tie that behavior to Module 3 NULL-safe patterns where shown
- Join **`trip`** to **`zone_lookup`** twice (pickup and dropoff) as a
  **self-join** pattern — same logical table, different aliases and join keys
- Resolve duplicate column names after joins using **`alias`**, **`select`**,
  and rename patterns
- Use **semi** and **anti** joins (and equivalent membership patterns where
  shown) to answer set-membership questions without widening row count
- Contrast **left anti** with **`except`**: both ask “in A but not B,” but
  anti-join is key-based with flexible schemas; **`except`** requires
  identical schemas and compares full rows
- Apply **`F.broadcast`** on small dimension tables and skim join-related
  nodes in **`.explain()`**; recognize that **AQE** may change join strategy,
  coalesce shuffle partitions, or mitigate skew at runtime (deep tuning →
  Module 16)
- Combine DataFrames with **set operations** — **`union`**, **`unionByName`**,
  **`intersect`**, **`intersectAll`**, **`except`** / **`subtract`**, and
  **`exceptAll`** — including when **`union()`** misaligns columns by position
- Read prior **`curated/`** folders and landing paths, then write new curated
  **Parquet** outputs under descriptive folder names

## Prerequisites

Module 6 — Built-in Functions, Complex Types, and UDF Alternatives (notebooks
**`01 - Column Transforms with Built-in Functions`** through
**`04 - Built-ins First, When (Not) to Use UDFs`**). You should have:

- **Curated** outputs from Module 6:
  - **`…/curated/trip/`** (cleaned from **`bad_trip_data.csv`**, 106 rows)
  - **`…/curated/payment/`** (cleaned from **`bad_payment_data.csv`**, 105 rows)
  - **`…/curated/drivers_flat/`** (one row per **`driver_id`** +
    **`trip_id`** after **`explode`**)
- Landing datasets used for joins:
  - **`…/landing/source_files/trip/`**, **`trip_time/`**, **`payment/`** (core
    100-row logical tables where 1:1 join teaching needs them)
  - **`…/landing/source_files/zone_lookup/`** (JSON Lines dimension, 20 rows)
- Comfort with transformations vs actions and terminal writes (Modules 4–5)

Recall Module 3 — Data Cleaning, NULL Semantics, and Type Handling for
NULL-aware filters and **`eqNullSafe`** when join keys can be NULL.

Join keys and table roles:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).

This module does **not** read **`practice/`**.

Use Module 5 **`99 - Rideshare Project Cleanup and Reset`**, Level 2, to wipe
**`curated/`** when rerunning Modules 6–9 from a clean pipeline state.

## Approach and boundaries

**Runtime baseline:** Apache Spark **4.0.0** on Databricks Runtime **17.3 LTS**
(course default). Join APIs and hints below match Spark 4.0.0 documentation.

**API used:** PySpark **DataFrame** **`join`**, set-operation methods, and
**`F.broadcast`**. **`spark.sql`** may appear only for brief plan inspection —
dual-API pipeline work belongs in Module 9.

**In scope:** join types and row-count correctness; self-joins and column
naming; semi/anti; **`union`** / **`unionByName`** / **`intersect`** /
**`intersectAll`** / **`except`** / **`exceptAll`**; broadcast hints and
high-level **AQE** awareness; curated read/write for unified views.

**Join strategy hints:** teach **`F.broadcast`** (and what to look for in
**`.explain()`**). SQL join hints **`MERGE`**, **`SHUFFLE_HASH`**, and
**`SHUFFLE_REPLICATE_NL`** may be named in passing only (same treatment as
Pandas UDFs in Module 6 — not demonstrated here). Do not confuse the join hint
**`MERGE`** (shuffle sort-merge join) with **Delta Lake `MERGE`** (upsert DML,
Module 10).

**Out of scope:** **`groupBy`**, pivots, and window functions (Module 8); CTEs
and parameterized SQL pipelines (Module 9); Delta ACID, time travel, and
**Delta `MERGE`** DML (Module 10); Unity Catalog grants (Module 11); reading
**`practice/`**; **`lateralJoin`**; streaming or stream-static joins;
UDF-based join-key logic; skew tuning and advanced join-hint workflows
(Module 16).

Schemas, column names, join keys, and Volume path rules:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).

**Paths (do not use shorthand `processed/` alone):**

| Role | Path |
|---|---|
| Reads (landing) | `/Volumes/rideshare_dev/landing/source_files/{dataset}/` |
| Reads (prior outputs) | `/Volumes/rideshare_dev/processed/output_files/curated/{output_name}/` |
| Module 7 writes | `/Volumes/rideshare_dev/processed/output_files/curated/{output_name}/` |

**Curated outputs this module creates:**

| Output | Path | Grain / contract |
|---|---|---|
| Trip enriched | `…/curated/trip_enriched/` | One row per **`trip_id`** from **`curated/trip`**, left-joined to landing **`trip_time`**, **`curated/payment`**, and pickup/dropoff **`zone_lookup`** attributes |
| Trip driver assignment | `…/curated/trip_driver_assignment/` | One row per (**`driver_id`**, **`trip_id`**) from **`curated/drivers_flat`**, joined to trip attributes needed for downstream KPIs |

**Expected NULLs after left joins (intentional, not data bugs):**

- **`trip_enriched`:** **`trip_id`** 101–106 have NULL **`trip_date`** /
  **`hour_of_day`** because landing **`trip_time`** remains the core 100-row
  table while **`curated/trip`** has 106 rows after Module 6 cleaning.
- **`trip_enriched`:** **`trip_id`** 106 has NULL payment columns because
  **`curated/payment`** has 105 rows (no payment row for 106).
- **`trip_driver_assignment`:** **`drivers_flat`** trip ids fall within 1–100;
  joins to trip attributes should not introduce unexpected key NULLs from
  driver assignment alone.

Write curated outputs as **Parquet** with **`.mode("overwrite")`** unless a
notebook states otherwise. Module 8 reads these folders (and may read other
**`curated/`** outputs) for aggregations and windows. Primary storage stays
Parquet here; full Delta Lake treatment remains Module 10 (Module 5 already
previewed Delta in **`07 - Write Patterns and Table Preview`**).

**Cleanup:** reuse Module 5 **`99 - Rideshare Project Cleanup and Reset`**
(Level 2). This module has no dedicated cleanup notebook.

## Notebook navigation

Five notebooks, in this order:

1. **Join Types and Row-Count Correctness**
   - **Inner**, **left**, **right**, and **full outer** joins on **`trip_id`**
     using landing **`trip`**, **`trip_time`**, and **`payment`** where the
     logical model is **1:1** — predict counts, then verify with **`count()`**
   - Deliberate **many-to-many** example on a small in-notebook frame (not
     production keys) to show row multiplication
   - **`dropDuplicates`** on keys before join when the business rule requires
     unique keys (callback to Module 6)
   - Gotcha: missing or wrong join condition → accidental **cross join**;
     contrast with deliberate **`crossJoin()`** / **`how="cross"`**
   - Gotcha: NULL **`trip_id`** (or other key) does not equi-join — callback
     to Module 3 NULL semantics
   - Skill-building only — **no curated write**
2. **Dimension Joins, Self-Joins, and Column Naming**
   - **Self-join** pattern: join **`trip`** (landing or **`curated/trip`**) to
     **`zone_lookup`** twice — pickup and dropoff — with table aliases
   - Resolve **`location_id`**, **`borough_name`**, and **`zone_name`**
     collisions via **`select`** / rename patterns
   - **`F.broadcast`** on **`zone_lookup`**; skim join nodes in **`.explain()`**
   - Skill-building only — **no curated write** (capstone reuses the pattern)
3. **Semi Joins and Anti Joins**
   - Membership on curated grains: 106 trips vs 105 payments — trips with
     payment, trips without payment, payments without a matching trip
   - **`left_semi`**, **`left_anti`**, and why **`inner`** + **`distinct`**
     is not a substitute for semi when you must not widen rows
   - Bridge to Notebook 4: anti-join vs **`except`** (keys vs full-row diff,
     schema requirements)
4. **Set Operations**
   - **`union()`** vs **`unionByName`** — **`union()`** matches columns by
     **position**, not name (common production mistake)
   - **`intersect`** / **`except`** vs **`intersectAll`** / **`exceptAll`**
     (deduplicating vs duplicate-preserving semantics)
   - Duplicate rows after **`union`** and when **`distinct`** is appropriate
   - Brief cross-reference: **`crossJoin()`** vs set **`union`** — different
     operations (Cartesian product vs stack rows)
5. **Unified Curated Views**
   - Read **`curated/trip`**, **`curated/payment`**, **`curated/drivers_flat`**, plus landing **`trip_time`** and **`zone_lookup`**
   - Apply join patterns from Notebooks 1–3; reuse dimension/self-join naming
     from Notebook 2
   - **Predict and verify row counts** on **`trip_enriched`** and
     **`trip_driver_assignment`** before write; confirm expected NULLs
     documented above
   - Write **`…/curated/trip_enriched/`** and
     **`…/curated/trip_driver_assignment/`** as Parquet
   - **AQE:** at a high level, runtime may switch join strategy, coalesce
     shuffle partitions, or handle skew — inspect plans only; tuning → Module 16
   - Name-only note: join hints **`MERGE`**, **`SHUFFLE_HASH`**, and
     **`SHUFFLE_REPLICATE_NL`** exist in SQL; not taught in this module

## Exercises

Each notebook listed in **Notebook navigation** ends with a short hands-on
task that repeats the demonstrated join or set pattern on slightly different
keys, columns, or membership questions.

## Minimum privileges required

- Databricks workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the
  compute used in this module
- Unity Catalog (objects created in Module 5 — no **`CREATE CATALOG`**,
  external location, or volume DDL in this module):
  - **`USE CATALOG`** on **`rideshare_dev`**
  - **`USE SCHEMA`** on **`rideshare_dev.landing`** and
    **`rideshare_dev.processed`**
  - **`READ VOLUME`** on **`rideshare_dev.landing.source_files`**
  - **`READ VOLUME`** and **`WRITE VOLUME`** on
    **`rideshare_dev.processed.output_files`**
