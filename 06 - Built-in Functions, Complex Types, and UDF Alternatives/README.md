# Module 6 — Built-in Functions, Complex Types, and UDF Alternatives

## Purpose

Transform landing data with Spark built-ins, work with nested types, and write
curated outputs — prefer built-ins over UDFs.

Python UDFs appear only in the final notebook as a contrast for logic that
cannot be expressed with built-ins. Pandas/Arrow UDFs are mentioned briefly as
an advanced fallback; this course does not teach them further.

Schemas, column names, join keys, and Volume path rules:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).

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

Complete Module 5 content notebooks **`01`–`07`**. You need:

| Asset | Notes |
|---|---|
| Landing volume | `/Volumes/rideshare_dev/landing/source_files/{dataset}/` populated |
| Controlled-bad CSVs | Full-size `trip/bad_trip_data.csv` and `payment/bad_payment_data.csv` from Module 5 **`01`** |
| Managed table | **`rideshare_dev.processed.trip_time_preview`** from Module 5 **`07`** |
| Write model | Comfort with transformations vs actions; **`DataFrame.write`** executes on **`.save()`** / **`.parquet()`** / **`.saveAsTable()`** (Module 4) |

Recall Module 3 (**`01`–`03`**): NULL-aware filters, normalize-before-drop,
`F.coalesce`, `try_cast`.

This module reads the **landing volume** and (Notebook **01** only) one
**managed table**. It does **not** read `practice/`.

Optional hygiene: Module 5 **`99`** Level 1 clears `practice/` before start.
Use Level 2 to wipe `curated/` only when rerunning from a clean curated state.

## Paths and outputs

| Role | Path |
|---|---|
| Reads | `/Volumes/rideshare_dev/landing/source_files/{dataset}/` |
| Module 6 writes | `/Volumes/rideshare_dev/processed/output_files/curated/{output_name}/` |

| Output | Path | Grain / contract |
|---|---|---|
| Flattened drivers | `…/curated/drivers_flat/` | One row per **`driver_id`** + **`trip_id`** after **`explode`** on **`trips_assigned`** |
| Cleaned trip | `…/curated/trip/` | One row per **`trip_id`** from **`bad_trip_data.csv`** after missing-key rejection and **`dropDuplicates`**; 106 rows; preserve location join keys |
| Cleaned payment | `…/curated/payment/` | One row per **`trip_id`** from **`bad_payment_data.csv`** after missing-key rejection; 105 rows |

Write curated outputs as **Parquet** under each folder with
**`.mode("overwrite")`** unless a notebook states otherwise. Module 7 reads
these curated folders plus **landing** datasets such as **`trip_time`** and
**`zone_lookup`** where joins require them.

`curated/` is created on first write. Schema names `landing` / `processed` are
not medallion Bronze/Silver/Gold (Module 12).

**Cleanup:** reuse Module 5 **`99`** (Level 2 clears Module 6 curated
outputs). This module has no dedicated cleanup notebook.

## Runtime and scope

**API:** Notebooks **01–03** use DataFrame methods and **`F.*`**. **`04`**
contrasts built-ins with a Python UDF and briefly notes Pandas/Arrow UDFs.
`F.expr` / `selectExpr` were taught in Module 2 and are not used here. Pure
SQL and dual-API patterns belong in Module 9.

**In scope:** built-in transforms, struct/array/`explode`, curated writes
(above), built-in vs UDF decision guidance.

**Out of scope:** joins / set ops (Module 7); aggregations / windows (Module 8);
pure SQL / dual-API (Module 9); Delta ACID / `MERGE` (Module 10); UC grants
(Module 11); reading `practice/`.

## Notebooks

Four notebooks, in order. Each ends with a short hands-on task that repeats the
demonstrated pattern on slightly different columns or values.

| # | Notebook | Focus |
|---|---|---|
| 1 | Column Transforms with Built-in Functions | Volume vs managed table on **`trip_time`**: landing **`…/trip_time/trip_time.parquet`** vs **`rideshare_dev.processed.trip_time_preview`** — same transforms after load; built-ins by dataset (**`trip`**: string, numeric/decimal, conditional — no date cols; **`trip_time`**: **`trip_date`**, **`hour_of_day`**; optional light **`payment`** decimals); no curated write — **`03`** re-reads landing |
| 2 | Complex Types, Structs, Arrays, and explode | Landing **`drivers`** XML with **`rowTag`** (same as Module 5 **`05`** — do not read `practice/`); struct fields (**`vehicle.*`**); arrays; **`explode`** / **`explode_outer`** on **`trips_assigned`**; write **`…/curated/drivers_flat/`** |
| 3 | Cleaning and Curated Outputs | Full-size **`bad_trip_data.csv`** (108 source rows) and **`bad_payment_data.csv`** (106 source rows); one forward chain per file (missing-key rejection, **`dropDuplicates`** on trip **`trip_id`**, normalization, failed-conversion handling, invalid-value rules); persist enrichment/cleaning columns only here; write **`…/curated/trip/`** and **`…/curated/payment/`** |
| 4 | Built-ins First, When (Not) to Use UDFs | Built-ins as default; Python UDF contrast; short Pandas/Arrow note (not taught further); demo on a small column rule — **do not overwrite** curated outputs |

## Minimum privileges required

- Workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the compute used here
- Unity Catalog (objects from Module 5 — no **`CREATE CATALOG`**, external
  location, or volume DDL here):
  - **`USE CATALOG`** on **`rideshare_dev`**
  - **`USE SCHEMA`** on **`rideshare_dev.landing`** and
    **`rideshare_dev.processed`**
  - **`READ VOLUME`** on **`rideshare_dev.landing.source_files`**
  - **`WRITE VOLUME`** on **`rideshare_dev.processed.output_files`**
  - **`SELECT`** on **`rideshare_dev.processed.trip_time_preview`**
    (Notebook **01** only)
