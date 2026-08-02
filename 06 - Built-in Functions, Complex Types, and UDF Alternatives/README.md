# Module 6 — Built-in Functions, Complex Types, and UDF Alternatives

## Purpose

Use PySpark built-in functions to transform landing data, work with nested
columns and arrays, and produce curated datasets for later modules.

The module establishes one production rule: **use Spark built-ins first**.
Python UDFs appear only in the final notebook as a contrast for logic that
cannot be expressed with built-in functions. Pandas/Arrow UDFs are mentioned
briefly as an advanced fallback; this course does not teach them further.

## Learning objectives

By the end of this module, you'll be able to:

- Apply string, numeric, date/time, and conditional transforms with
  **`pyspark.sql.functions`** (`F.*`) on DataFrames loaded from Volume paths
- Load the same logical dataset from a **Volume path** and a **managed Unity
  Catalog table**, then apply identical transform chains after load
- Access **struct** fields, work with **array** columns, and flatten nested
  data with **`explode`** / **`explode_outer`**
- Review Module 3 cleaning patterns (NULL-safe predicates, normalization,
  safe casts) on full-size controlled-bad CSV variants and carry those same
  cleaned DataFrames into **curated** outputs
- Explain when to prefer built-ins over **Python UDFs** (and when Pandas/Arrow
  UDFs exist as an advanced fallback outside this course)

## Prerequisites

Module 5 — Reading, Writing, and Schemas (complete content notebooks
**`01 - Unity Catalog Volumes and Data Landing`** through
**`07 - Write Patterns and Table Preview`**). You should have:

- Landing volume populated under
  `/Volumes/rideshare_dev/landing/source_files/{dataset}/`
- Full-size controlled-bad `trip/bad_trip_data.csv` and
  `payment/bad_payment_data.csv` source variants landed by Module 5
  **`01 - Unity Catalog Volumes and Data Landing`**
- Managed table **`rideshare_dev.processed.trip_time_preview`** created in
  Module 5 **`07 - Write Patterns and Table Preview`**
- Comfort with transformations vs actions, and that **`DataFrame.write`**
  returns a writer interface; execution occurs when you call terminal write
  methods such as **`.save()`**, **`.parquet()`**, or **`.saveAsTable()`**
  (Module 4)

Recall Module 3 — Data Cleaning, NULL Semantics, and Type Handling:
**`01 - NULL Semantics and Predicate Correctness`**,
**`02 - Missing, Blank, and Sentinel Values`**, and
**`03 - Safe Type Casting`** cover NULL-aware filters,
normalize-before-drop, `F.coalesce`, and `try_cast`.

This module reads from the **landing volume** and (in
**`01 - Column Transforms with Built-in Functions`** only) one **managed
table**. It does **not** read `practice/`.

Clearing `practice/` before starting (Module 5
**`99 - Rideshare Project Cleanup and Reset`**, Level 1) is optional hygiene.
Use Level 2 to wipe `curated/` only when rerunning this module from a clean
curated state.

## Approach and boundaries

**API used:** Notebooks **01–03** use PySpark **DataFrame** methods and
built-in **`F.*`** Column expressions. **`04 - Built-ins First: When (Not) to
Use UDFs`** contrasts built-ins with a Python UDF and briefly notes
Pandas/Arrow UDFs as an advanced fallback not taught here. `F.expr` and `selectExpr` were
taught in Module 2 and are not used here. Pure SQL and dual-API patterns
belong in Module 9.

**In scope:** built-in transforms, struct/array/`explode`, curated writes
(below), built-in vs UDF decision guidance.

**Out of scope:** joins and set operations (Module 7); aggregations and
window functions (Module 8); pure SQL / dual-API deep dive (Module 9);
Delta ACID / `MERGE` (Module 10); Unity Catalog grants (Module 11); reading
`practice/`.

Schemas, column names, join keys, and Volume path rules:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).

**Paths (do not use shorthand `processed/` alone):**

| Role | Path |
|---|---|
| Reads | `/Volumes/rideshare_dev/landing/source_files/{dataset}/` |
| Module 6 writes | `/Volumes/rideshare_dev/processed/output_files/curated/{output_name}/` |

**Curated outputs this module creates:**

| Output | Path | Grain / contract |
|---|---|---|
| Flattened drivers | `…/curated/drivers_flat/` | One row per **`driver_id`** + **`trip_id`** after **`explode`** on **`trips_assigned`** |
| Cleaned trip | `…/curated/trip/` | One row per **`trip_id`** from **`bad_trip_data.csv`** after missing-key rejection and **`dropDuplicates`**; 106 rows; preserve location join keys |
| Cleaned payment | `…/curated/payment/` | One row per **`trip_id`** from **`bad_payment_data.csv`** after missing-key rejection; 105 rows |

Write curated outputs as **Parquet** under each folder with
**`.mode("overwrite")`** unless a notebook states otherwise. Module 7 reads
these curated folders plus **landing** datasets such as **`trip_time`** and
**`zone_lookup`** where joins require them.

`curated/` is created on first write. Schema names `landing` / `processed`
are not medallion Bronze/Silver/Gold (Module 12).

**Cleanup:** reuse Module 5 **`99 - Rideshare Project Cleanup and Reset`**
(Level 2 clears all Module 6–9 curated outputs). This module has no
dedicated cleanup notebook.

## Notebook navigation

Four notebooks, in this order:

1. **Column Transforms with Built-in Functions**
   - Volume vs managed table on **`trip_time`**: landing
     **`…/trip_time/trip_time.parquet`** vs
     **`rideshare_dev.processed.trip_time_preview`** — same transforms after
     load, different source reference
   - Built-ins by dataset: **`trip`** — string, numeric/decimal, conditional
     (no date columns on **`trip`**); **`trip_time`** — **`trip_date`**,
     **`hour_of_day`**; optional light **`payment`** decimal examples
   - Skill-building only — **no curated write**;
     **`03 - Cleaning and Curated Outputs`** re-reads landing
2. **Complex Types: Structs, Arrays, and explode**
   - Read landing **`drivers`** XML with **`rowTag`** (same source pattern as
     Module 5 **`05 - Reading XML`** — do not read `practice/`)
   - Struct field access (**`vehicle.*`**); arrays; **`explode`** /
     **`explode_outer`** on **`trips_assigned`**
   - Write **`…/curated/drivers_flat/`**
3. **Cleaning and Curated Outputs**
   - Full-size **`bad_trip_data.csv`** (108 source rows) and
     **`bad_payment_data.csv`** (106 source rows); layout in
     [`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md)
   - One forward-moving DataFrame chain per file: missing-key rejection,
     **`dropDuplicates`** on trip **`trip_id`**, normalization,
     failed-conversion handling, and invalid-value rules
   - Persist enrichment/cleaning columns only here — not in
     **`01 - Column Transforms with Built-in Functions`**
   - Write **`…/curated/trip/`** and **`…/curated/payment/`**
4. **Built-ins First: When (Not) to Use UDFs**
   - Built-ins as default; Python UDF as a contrast when custom Python might be considered
   - Short advanced note on Pandas/Arrow UDFs (not taught further in this course)
   - Demo on a small column rule — **do not overwrite** curated outputs

## Exercises

Each notebook listed in **Notebook navigation** ends with a short hands-on
task that repeats the demonstrated pattern on slightly different columns or
values.

## Minimum privileges required

- Databricks workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the
  compute used in this module
- Unity Catalog (objects created in Module 5 — no **`CREATE CATALOG`**,
  external location, or volume DDL in this module):
  - **`USE CATALOG`** on **`rideshare_dev`**
  - **`USE SCHEMA`** on **`rideshare_dev.landing`** and
    **`rideshare_dev.processed`**
  - **`READ VOLUME`** on **`rideshare_dev.landing.source_files`**
  - **`WRITE VOLUME`** on **`rideshare_dev.processed.output_files`**
  - **`SELECT`** on **`rideshare_dev.processed.trip_time_preview`**
    (**01 - Column Transforms with Built-in Functions** only)
