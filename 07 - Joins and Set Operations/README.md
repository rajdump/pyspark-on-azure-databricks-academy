# Module 7 — Joins and Set Operations

## Purpose

Combine rideshare tables with explicit join types and set logic so row counts
and keys stay understandable — no silent duplication from many-to-many joins,
no lost rows from the wrong outer join, and no ambiguous duplicate column
names after a dimension lookup.

The module reads Module 6 **curated** outputs and **landing** datasets where
join keys or grain require them, then writes new **curated** unified views for
Module 8 aggregations and Module 9 SQL synthesis.

## Learning objectives

By the end of this module, you'll be able to:

- Choose **inner**, **left**, **right**, and **full outer** joins and predict
  how each affects row count when keys are one-to-one vs many-to-one
- Join **`zone_lookup`** twice on **`trip`** (pickup and dropoff) using clear
  **aliases** and **`select`** / **`drop`** patterns for duplicate names
- Use **semi** and **anti** joins (and equivalent **`filter` + `exists`**
  patterns where shown) to answer membership questions without widening rows
- Apply **broadcast** hints on small dimension tables and read **AQE**-related
  join behavior at a high level in **`.explain()`** (deep tuning → Module 16)
- Combine DataFrames with **set operations** — **`union`**, **`unionByName`**,
  **`intersect`**, **`except`** / **`subtract`** — with column-order and
  duplicate-row awareness
- Read prior **`curated/`** folders and landing paths, then write new curated
  Parquet outputs under descriptive folder names

## Prerequisites

Module 6 — Built-in Functions, Complex Types, and UDF Alternatives (notebooks
**`01 - Column Transforms with Built-in Functions`** through
**`04 - Built-ins First, When (Not) to Use UDFs`**). You should have:

- **Curated** outputs from Module 6:
  - **`…/curated/trip/`** (cleaned from **`bad_trip_data.csv`**, 106 rows)
  - **`…/curated/payment/`** (cleaned from **`bad_payment_data.csv`**, 105 rows)
  - **`…/curated/drivers_flat/`** (one row per **`driver_id`** +
    **`trip_id`** after **`explode`**)
- Landing datasets still used for joins at the core 100-row grain or as
  dimensions:
  - **`…/landing/source_files/trip_time/`** (Parquet)
  - **`…/landing/source_files/zone_lookup/`** (JSON Lines)
- Optional reference reads of the original 100-row **`trip`**, **`payment`**
  landing files when contrasting **1:1** join behavior with curated row-count
  differences (106 vs 105)
- Comfort with transformations vs actions and terminal writes (Modules 4–5)

Join keys and table roles:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).

Clearing **`curated/`** before a full rerun: Module 5
**`99 - Rideshare Project Cleanup and Reset`**, Level 2 (also clears Module
8–9 curated outputs once those modules exist).

## Approach and boundaries

**API used:** PySpark **DataFrame** **`join`** and set-operation methods.
**`F.broadcast`** for explicit broadcast hints. **`spark.sql`** may appear
only for brief plan inspection or a single illustrative join — dual-API
pipeline work belongs in Module 9.

**In scope:** join types, cardinality and key correctness, semi/anti, broadcast
hints and AQE awareness, set operations, curated read/write for unified views.

**Out of scope:** **`groupBy`**, pivots, and window functions (Module 8); CTE /
parameterized SQL pipelines (Module 9); Delta **`MERGE`** (Module 10); UC
grants (Module 11); reading **`practice/`**; skew and advanced shuffle tuning
(Module 16).

Schemas, column names, join keys, and Volume path rules:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).

**Paths (do not use shorthand `processed/` alone):**

| Role | Path |
|---|---|
| Reads (landing) | `/Volumes/rideshare_dev/landing/source_files/{dataset}/` |
| Reads (prior module outputs) | `/Volumes/rideshare_dev/processed/output_files/curated/{output_name}/` |
| Module 7 writes | `/Volumes/rideshare_dev/processed/output_files/curated/{output_name}/` |

**Curated outputs this module creates** (names may be refined during
authoring; keep grain contracts stable for Module 8):

| Output | Path | Grain / contract |
|---|---|---|
| Trip enriched | `…/curated/trip_enriched/` | One row per **`trip_id`** from **`curated/trip`**, left-joined to **`trip_time`**, **`curated/payment`**, and pickup/dropoff **`zone_lookup`** attributes |
| Trip driver assignment | `…/curated/trip_driver_assignment/` | One row per (**`driver_id`**, **`trip_id`**) from **`curated/drivers_flat`**, joined to trip attributes needed for downstream KPIs |

Write curated outputs as **Parquet** with **`.mode("overwrite")`** unless a
notebook states otherwise. Module 8 reads these (and may read other **`curated/`**
folders) for aggregations and windows.

**Cleanup:** reuse Module 5 **`99 - Rideshare Project Cleanup and Reset`**
(Level 2). This module has no dedicated cleanup notebook.

## Notebook navigation

Five notebooks, in this order (titles may be adjusted during authoring):

1. **Join Types and Row-Count Correctness**
   - Inner and outer joins on **`trip_id`** using landing **`trip`**, **`trip_time`**, and **`payment`** where the logical model is **1:1**
   - Predict and verify row counts; contrast with a deliberate many-to-many
     example on a small in-notebook frame (not production keys)
   - **`dropDuplicates`** on keys before join when the business rule requires
     unique keys (callback to Module 6 cleaning)
2. **Dimension Joins and Column Naming**
   - Join **`curated/trip`** (or landing **`trip`**) to **`zone_lookup`**
     twice — pickup and dropoff — with table aliases
   - Resolve **`location_id`**, **`borough_name`**, and **`zone_name`**
     collisions via **`select`** / rename patterns
   - Introduce **`F.broadcast`** on **`zone_lookup`** and skim join nodes in
     **`.explain()`**
3. **Semi Joins and Anti Joins**
   - Membership questions on curated row counts (106 trips vs 105 payments):
     trips with payment, trips without payment, payments without matching trip
   - **`left_semi`**, **`left_anti`**, and when **`inner`** + **`distinct`**
     would over-count
4. **Set Operations**
   - **`union`** vs **`unionByName`** on aligned schemas
   - **`intersect`**, **`except`** / **`subtract`** on small rideshare subsets
   - Duplicate rows and **`distinct`** after **`union`**
5. **Unified Curated Views**
   - Read **`curated/trip`**, **`curated/payment`**, **`curated/drivers_flat`**, plus landing **`trip_time`** and **`zone_lookup`**
   - Build **`trip_enriched`** and **`trip_driver_assignment`**; write Parquet
     under **`curated/`**
   - Optional: note where **AQE** may change join strategy between runs —
     inspection only, not tuning

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
