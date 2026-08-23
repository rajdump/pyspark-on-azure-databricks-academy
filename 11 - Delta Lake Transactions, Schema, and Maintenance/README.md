# Module 11 — Delta Lake Transactions, Schema, and Maintenance

## Purpose

Apply transactional Delta behavior, schema change, table maintenance, and
introductory `MERGE` after the foundations module.

This README currently specifies **notebook 01** only. Notebooks **02–04**
are not designed yet.

## Learning objectives

By the end of notebook **01**, you'll be able to:

- Compare how an `UPDATE` behaves with and without **deletion vectors**
- Show that `VACUUM` removes only files that are no longer used by the table
- Compact active files with `OPTIMIZE`, then remove eligible old files with
  `VACUUM`

This notebook does not teach ACID, schema evolution, `MERGE`, liquid
clustering, Change Data Feed, or a table-properties tour. Grants are
Module 12.

## Prerequisites

Complete Module 10 notebooks **`01`–`04`**. You need the Module 5 platform
(not the teaching pipeline tables):

| Asset | Notes | Source |
|---|---|---|
| Catalog `rideshare_dev`; schema `processed` | Course catalog | Module 5 `01 - Unity Catalog Volumes and Data Landing.py` |
| Volume `rideshare_dev.processed.output_files` | 01 practice folder | Module 5 `01 - Unity Catalog Volumes and Data Landing.py` |

Recall Module 10: `UPDATE` can leave extra files on disk; history is kept
about **30** days; data files become eligible for `VACUUM` after **7** days;
do not run `VACUUM` in Module 10. This notebook is the first run of
`OPTIMIZE` and `VACUUM`.

Does **not** read or mutate `trip_enriched`, `trip_driver_assignment`, KPI
tables, or `curated/`.

## Dataset

Same four-row handmade extract as Module 10 (`trip_id` **1001–1004**), not
the 100-row source files. Columns from `trip.service_type` and `payment`
(no `driver_payout_amount`). `service_type` uppercase; `payment_method`
lowercase.

```text
trip_id bigint
service_type string
payment_method string
base_fare_amount decimal(10,2)
tip_amount decimal(10,2)
```

| trip_id | service_type | payment_method | base_fare_amount | tip_amount | Lab use in 01 |
|---|---|---|---:|---:|---|
| 1001 | STANDARD | card | 20.00 | 3.00 | Step 3: tip → **4.00** |
| 1002 | SHARED | cash | 15.00 | 0.00 | Unchanged |
| 1003 | PREMIUM | card | 40.00 | 6.00 | Step 1: **6.00 → 10.00** (DV off); step 2: **12.00** (DV on) |
| 1004 | STANDARD | wallet | 25.00 | 2.50 | Step 3: tip → **3.50** |

First write: deletion vectors **off**. Ignore `.crc` files in listings.

## Paths and outputs

Object location:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md)
(Module 11 — Delta Lake Transactions, Schema, and Maintenance).

| Notebook | Object |
|---|---|
| 01 | `fare_maint_lab/` at `/Volumes/rideshare_dev/processed/output_files/practice/fare_maint_lab/` |

No `saveAsTable`. Path DML on `` delta.`<path>` ``. Bound paths use
`spark.sql`; `%sql` only for fixed names.

**Cleanup:** Notebook 01 setup `rm`s `fare_maint_lab/`. Module 5
`99 - Rideshare Project Cleanup and Reset.py` Level 1 clears `practice/`
(including this folder).

## Notebooks

One specified notebook so far. **No exercise.**

| # | Notebook | Focus |
|---|---|---|
| 01 | Deletion Vectors, OPTIMIZE, and VACUUM | Volume folder `fare_maint_lab/`. **0** baseline: DV off, four rows, one file, `ls`. **1** `UPDATE` 1003 **6.00 → 10.00** without DV, `ls` (rewrite). **2** enable DV; `UPDATE` 1003 **→ 12.00**, `ls` (small new file; existing file stays). **3** `UPDATE` 1001 **→ 4.00** and 1004 **→ 3.50**, `ls` (multiple **live** files). **4** `VACUUM RETAIN 0`, `ls` (live files stay — not compaction). **5** `OPTIMIZE`, `ls` (fewer live files). **6** `VACUUM RETAIN 0` (session check off; lab only), `ls` (obsolete files gone; time travel that needed them stops). Fence: no helper, no HISTORY/`VERSION AS OF` demo, no `MERGE`. **No exercise** |

## Minimum privileges required

- Unity Catalog (no catalog / external-location / volume **CREATE** /
  **DROP** here — Module 5 already created those objects):
  - **`USE CATALOG`** on **`rideshare_dev`**
  - **`USE SCHEMA`** on **`rideshare_dev.processed`**
  - **`READ VOLUME`** / **`WRITE VOLUME`** on
    **`rideshare_dev.processed.output_files`**
- Workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the compute used here
