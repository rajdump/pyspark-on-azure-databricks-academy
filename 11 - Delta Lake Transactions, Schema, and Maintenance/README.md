# Module 11 — Delta Lake Transactions, Schema, and Maintenance

## Purpose

Apply transactional Delta behavior, schema change, table maintenance, and
introductory `MERGE` after the foundations module.

This README currently specifies **notebook 01** only. Notebooks **02–04**
are not designed yet.

## Learning objectives

By the end of notebook **01**, you'll be able to:

- Show that one `UPDATE` without deletion vectors rewrites the whole data
  file, and that the same kind of `UPDATE` with deletion vectors on writes a
  small new file instead
- Show that `VACUUM` cannot remove files the current table still uses
- Compact live small files with `OPTIMIZE`, then `VACUUM` unused files
  (`RETAIN 0 HOURS` in this lab only — that drops time travel to those
  versions on purpose)

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
| 1003 | PREMIUM | card | 40.00 | 6.00 | Step 1: tip → **10.00**; step 2: tip → **12.00** |
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
| 01 | Deletion Vectors, OPTIMIZE, and VACUUM | Volume folder `fare_maint_lab/` (do not use Module 10 folders). Setup: DV **off**, four rows, **one** data file, note size. Step 1: `UPDATE` **1003** **6.00 → 10.00** without DV — new file is a full rewrite; show size (Module 10 recap; leftover file is expected). Step 2: enable DV; `UPDATE` **1003** **10.00 → 12.00** — existing file stays; new file is small; show size. Step 3: `UPDATE` **1001** **3.00 → 4.00** and **1004** **2.50 → 3.50** — many live small files the table still needs. Step 4: `VACUUM RETAIN 0` — those files stay (`VACUUM` cannot delete files the table still uses). Step 5: `OPTIMIZE` — fewer larger files (often **one**); old small files off the current table but may still sit on disk. Step 6: `VACUUM RETAIN 0 HOURS` (session retention check off, set once before step 4) — leftovers gone; time travel to those versions is lost **on purpose**; never `RETAIN 0` on a real table. Proof: `VERSION AS OF` a version from before `OPTIMIZE` should fail (callback to Module 10, not a new lesson). Ignore `.crc`. Fence: no `MERGE`, liquid clustering, TBLPROPERTIES tour, CDF, Predictive Optimization demo, HISTORY walk, log JSON, 30-day/7-day diagram (one sentence: Module 10 used 7 days; this lab uses 0 so you see it now). **No exercise** |

## Minimum privileges required

- Unity Catalog (no catalog / external-location / volume **CREATE** /
  **DROP** here — Module 5 already created those objects):
  - **`USE CATALOG`** on **`rideshare_dev`**
  - **`USE SCHEMA`** on **`rideshare_dev.processed`**
  - **`READ VOLUME`** / **`WRITE VOLUME`** on
    **`rideshare_dev.processed.output_files`**
- Workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the compute used here
