# Module 11 — Delta Lake Transactions, Schema, and Maintenance

## Purpose

Apply transactional Delta behavior, schema change, table maintenance, and
introductory `MERGE` after the foundations module.

This README currently specifies **notebook 01** only. Notebooks **02–04**
are not designed yet.

## Learning objectives

By the end of notebook **01**, you'll be able to:

- Compare how an `UPDATE` behaves with and without **deletion vectors**
- Show that `VACUUM` removes only files that are no longer used by the
  table — it does not purge deletion-vector rows from live files
- Purge those rows from current files with
  `REORG TABLE ... APPLY (PURGE)`, then remove the old files with `VACUUM`

This notebook does not teach ACID, schema evolution, `MERGE`, `OPTIMIZE`,
liquid clustering, Change Data Feed, or a table-properties tour. Grants are
Module 12.

## Prerequisites

Complete Module 10 notebooks **`01`–`04`**. You need the Module 5 platform
(not the teaching pipeline tables):

| Asset | Notes | Source |
|---|---|---|
| Catalog `rideshare_dev`; schema `processed` | Course catalog | Module 5 `01 - Unity Catalog Volumes and Data Landing.py` |
| External location `el_rideshare_dev` | 01 table `LOCATION` | Module 5 `01 - Unity Catalog Volumes and Data Landing.py` |

Recall Module 10: `UPDATE` can leave extra files on disk; history is kept
about **30** days; data files become eligible for `VACUUM` after **7** days;
do not run `VACUUM` in Module 10. This notebook is the first run of
`REORG` and `VACUUM`.

Does **not** read or mutate `trip_enriched`, `trip_driver_assignment`, KPI
tables, or `curated/`.

## Dataset

Same handmade extract as Module 10 (`trip_id` **1001–1004**), not the
100-row source files. Columns from `trip.service_type` and `payment`
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
| 1001 | STANDARD | card | 20.00 | 3.00 | Unchanged |
| 1002 | SHARED | cash | 15.00 | 0.00 | Step 3: `DELETE` |
| 1003 | PREMIUM | card | 40.00 | 6.00 | Step 1: **6.00 → 10.00** (DV off); step 2: **12.00** (DV on) |
| 1004 | STANDARD | wallet | 25.00 | 2.50 | Unchanged |

First write: deletion vectors **off**; auto-compaction **off** (lab control,
not taught). Ignore `.crc` files in listings.

## Paths and outputs

Object location:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md)
(Module 11 — Delta Lake Transactions, Schema, and Maintenance). `{url}` is
the `url` column from `DESCRIBE EXTERNAL LOCATION el_rideshare_dev` (strip
a trailing slash).

| Notebook | Object |
|---|---|
| 01 | `rideshare_dev.processed.fare_maint_lab` at `{url}/external-tables/fare_maint_lab` |

External table (not a Volume path). Table DML on the catalog name. Bound
`LOCATION` uses `spark.sql`; `%sql` only for fixed names. Do not `CREATE
TABLE` at a Volume path.

**Cleanup:** Notebook 01 setup `DROP`s the table and `rm`s the `LOCATION`
folder. `DROP TABLE` does not delete those files. Module 5 `99` Level 1
does not clear `external-tables/` (same as Module 10 notebook 03).

## Notebooks

One specified notebook so far. **No exercise.**

| # | Notebook | Focus |
|---|---|---|
| 01 | Deletion Vectors, REORG TABLE, and VACUUM | External table `fare_maint_lab`. Auto-compact **off** (lab control, not taught). **0** baseline: DV off, four rows, one file, `LIST`. **1** `UPDATE` 1003 **6.00 → 10.00** without DV, `LIST` (rewrite). **2** enable DV; `UPDATE` 1003 **→ 12.00**, `LIST` (small new file; existing file stays; `.bin`). **3** `DELETE` 1002; `SELECT` **3** rows; `LIST` (live Parquet + `.bin`). **4** `VACUUM RETAIN 0 HOURS`, `LIST` (obsolete files can go; live DV files remain). **5** `REORG TABLE ... APPLY (PURGE)`, `LIST`, `DESCRIBE HISTORY`. **6** `VACUUM RETAIN 0 HOURS`, `LIST`. **7** second `REORG` (idempotent). Choice rule in prose only: `OPTIMIZE` is layout (not run). Fence: no `OPTIMIZE`, no auto-compact teaching, no helper, no `VERSION AS OF` / `RESTORE`, no `MERGE`, no other `REORG` `APPLY` clauses, no partition `WHERE`. **No exercise** |

## Minimum privileges required

- Unity Catalog (no catalog / external-location / volume **CREATE** /
  **DROP** here — Module 5 already created those objects):
  - **`USE CATALOG`** on **`rideshare_dev`**
  - **`USE SCHEMA`** on **`rideshare_dev.processed`**
  - **`CREATE TABLE`** on **`rideshare_dev.processed`**
  - **`CREATE EXTERNAL TABLE`**, **`READ FILES`**, and **`WRITE FILES`**
    on **`el_rideshare_dev`**
  - Table owner **`SELECT`** / **`MODIFY`** on
    **`rideshare_dev.processed.fare_maint_lab`**
- Workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the compute used here
