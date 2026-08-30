# Module 11 — Delta Lake Transactions, Schema, and Maintenance

## Purpose

Apply deletion-vector maintenance, schema change, introductory `MERGE`, and
ACID / optimistic concurrency after the foundations module.

## Learning objectives

By the end of this module, you'll be able to:

- Compare `UPDATE` with and without **deletion vectors**, then physically
  remove old row bytes with `REORG TABLE ... APPLY (PURGE)` and `VACUUM`
- Enforce a table schema, add a column, and apply `NOT NULL` / `CHECK`
- Apply an introductory `MERGE` (matched update and not-matched insert)
- Explain ACID and optimistic concurrency, including a write conflict and
  retry

This module does not teach `OPTIMIZE` or file layout (Module 18), production
incremental `MERGE` (Module 15), or grants (Module 12).

## Prerequisites

Complete Module 10 notebooks **`01`–`04`**. You need the Module 5 platform
(not the teaching pipeline tables):

| Asset | Notes | Source |
|---|---|---|
| Catalog `rideshare_dev`; schema `processed` | Course catalog | Module 5 `01 - Unity Catalog Volumes and Data Landing.py` |
| External location `el_rideshare_dev` | Table `LOCATION` | Module 5 `01 - Unity Catalog Volumes and Data Landing.py` |

Module 10 `04 - Delta Time Travel and Restore` warned that `VACUUM` removes
files time travel needs. This module's notebook **01** is the first cleanup
(deletion vectors, `REORG`, `VACUUM`) on an external table so `LIST` works.

Does **not** read or mutate `trip_enriched`, `trip_driver_assignment`, KPI
tables, or `curated/`.

## Dataset

Notebooks **02–04** use the same handmade extract as Module 10 (`trip_id`
**1001–1004**), not the 100-row source files. Columns from
`trip.service_type` and `payment` (no `driver_payout_amount` on first
write). `service_type` uppercase; `payment_method` lowercase.

```text
trip_id bigint
service_type string
payment_method string
base_fare_amount decimal(10,2)
tip_amount decimal(10,2)
```

Notebook **02** adds `driver_payout_amount decimal(10,2)` from
[`payment`](../docs/data/dataset-overview.md#payment). Leave that column
**NULL** on the four lab rows — do not invent payout amounts.

| trip_id | service_type | payment_method | base_fare_amount | tip_amount | Lab use |
|---|---|---|---:|---:|---|
| 1001 | STANDARD | card | 20.00 | 3.00 | 03 exercise: `MERGE` tip → **4.00**; 04 OCC |
| 1002 | SHARED | cash | 15.00 | 0.00 | 02 / 04 extract row |
| 1003 | PREMIUM | card | 40.00 | 6.00 | 03 `MERGE` → **10.00**; 04 OCC |
| 1004 | STANDARD | wallet | 25.00 | 2.50 | 03 `MERGE` insert; 04 OCC |

Notebook **01** uses `fare_dv_lab` (**11,060,030** rows, ~300 MB, all
`Lyft`). Schema, inspection `row_id`s, and baseline values:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md)
(Module 11). Inspect only those four rows — do not `SELECT *` the table.

| row_id | Baseline `passenger_fare` | Lab use |
|---:|---:|---|
| 210049714452023 | 51.57 | 01: **55.00** (DV off), **60.00** (DV on) |
| 210049714452029 | 41.76 | 01: inspect only |
| 210049714452046 | 38.65 | 01: `DELETE` |
| 210049714452050 | 40.13 | 01: inspect only |

First write in each of **01–04**: deletion vectors **off**. Notebook **01**
also sets auto-compaction **off** (lab control, not taught). Ignore `.crc`
files in listings.

Notebook **00** copies the lab Parquet from the Git folder working copy
(gitignored; not on GitHub). **00** does not `CREATE TABLE`.

## Paths and outputs

Object locations:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md)
(Module 11 — Delta Lake Transactions, Schema, and Maintenance). `{url}` is
the `url` column from `DESCRIBE EXTERNAL LOCATION el_rideshare_dev` (strip
a trailing slash).

| Notebook | Object |
|---|---|
| 00 | `data/lab/fare_dv_lab.parquet` → `{url}/external-tables/fare_dv_lab/fare_dv_lab.parquet` |
| 01 | `rideshare_dev.processed.fare_dv_lab` at `{url}/external-tables/fare_dv_lab` |
| 02–04 | `rideshare_dev.processed.fare_maint_lab` at `{url}/external-tables/fare_maint_lab` |

External table (not a Volume path). Table DML on the catalog name. Bound
`LOCATION` uses `spark.sql`; `%sql` only for fixed names. Do not `CREATE
TABLE` at a Volume path.

**Cleanup:** Each of **02–04** setup `DROP`s `fare_maint_lab` and `rm`s its
`LOCATION` folder. Notebook **00** `DROP`s leftover `fare_dv_lab` if present,
`rm`s the folder, then copies the Parquet. Notebook **01** `CONVERT TO DELTA`
on that folder and `CREATE`s `fare_dv_lab`. `DROP TABLE` does not delete
those files. Module 5 `99` Level 1 does not clear `external-tables/` (same
as Module 10 notebook 03).

## Notebooks

Five notebooks, in order. **00** is a copy utility (**no exercise**).
Notebook **01** uses `fare_dv_lab`. Notebooks **02–04** use `fare_maint_lab`.
Notebook **03** ends with a short exercise. Notebooks **01**, **02**, and
**04** have **no exercise**.

| # | Notebook | Focus |
|---|---|---|
| 00 | Copy Fare DV Lab File | Utility. Open from the course Git folder. `DROP TABLE IF EXISTS fare_dv_lab`; `rm` the destination folder; copy `fare_dv_lab.parquet` into it; `LIST`. Do not `CREATE TABLE`. Fence: no DV teaching, `UPDATE`, `VACUUM`, `OPTIMIZE`. **No exercise**. **Next:** `01 - Deletion Vectors, REORG TABLE, and VACUUM` |
| 01 | Deletion Vectors, REORG TABLE, and VACUUM | After Module 10 `04` retention/`VACUUM` warning. Run **00** first. `CONVERT TO DELTA` the Parquet folder, `CREATE TABLE` `fare_dv_lab` `LOCATION` `{url}/external-tables/fare_dv_lab` (DV off; auto-compact **off**, lab control, not taught). Inspect only `row_id`s **210049714452023**, **210049714452029**, **210049714452046**, **210049714452050** (never `SELECT *`). **1** `UPDATE` **210049714452023** **51.57 → 55.00** without DV, `LIST` (full-file rewrite). **2** enable DV; `UPDATE` same row **→ 60.00**, `LIST` (large file stays; small file + `.bin`). **3** `DELETE` **210049714452046**; inspect **3** rows; `LIST`. **4** `VACUUM RETAIN 0 HOURS`, `LIST`. **5** `REORG TABLE ... APPLY (PURGE)`, `LIST`, `DESCRIBE HISTORY`. **6** `VACUUM RETAIN 0 HOURS`, `LIST`. Fence: no `OPTIMIZE`, auto-compact teaching, `VERSION AS OF` / `RESTORE`, `MERGE`, extra `UPDATE`s, second `REORG`, other `REORG` `APPLY` clauses, or partition `WHERE`. **No exercise** |
| 02 | Schema Enforcement and Evolution | **0** `CREATE` extract columns only (no `driver_payout_amount`), `INSERT` **1001–1004**, **4** rows. **1** enforcement: write/append a DataFrame that includes `driver_payout_amount` → expected fail. **2** `ALTER TABLE ADD COLUMN driver_payout_amount DECIMAL(10,2)`; `mergeSchema` write succeeds; `SELECT` still **4** rows; payout is **NULL**. **3** `NOT NULL` on `trip_id`; `CHECK (tip_amount >= 0)`; one insert that violates `CHECK` → expected fail. Fence: no column mapping, `DROP COLUMN`, identity/generated columns, `MERGE`, DV, or `OPTIMIZE`. **No exercise** |
| 03 | Introductory MERGE | DV off. **0** `CREATE` + `INSERT` **1001–1003** only (**3** rows; 1003 tip **6.00**; **1004** absent). **1** `MERGE` from a source with 1003 tip **10.00** and extract row **1004**: `WHEN MATCHED` update tip; `WHEN NOT MATCHED` insert. **2** `SELECT` **4** rows; 1003 is **10.00**; 1004 present. Fence: no production incremental `MERGE` (Module 15), CDF, or `REPLACE WHERE`. Exercise: `MERGE` **1001** **3.00 → 4.00**; still **4** rows; 1003 stays **10.00** |
| 04 | ACID and Optimistic Concurrency | DV off. **0** `CREATE` + `INSERT` **1001–1004**. **1** `UPDATE` 1003 tip **6.00 → 10.00**; `DESCRIBE HISTORY`. **2** Explain OCC: readers see a snapshot; a writer validates against that version; overlapping writers on the same files conflict. **3** One overlapping-write demo (second writer loses with a concurrent-modification error, then retries); **4** rows remain. **4** `SHOW TBLPROPERTIES` glance (`delta.enableDeletionVectors`). Mention: deletion vectors can allow row-level concurrency for non-overlapping rows — no lab. Fence: no isolation-level tour, checkpoints, protocol versions, or `OPTIMIZE`. **No exercise** |

## Minimum privileges required

- Unity Catalog (no catalog / external-location / volume **CREATE** /
  **DROP** here — Module 5 already created those objects):
  - **`USE CATALOG`** on **`rideshare_dev`**
  - **`USE SCHEMA`** on **`rideshare_dev.processed`**
  - **`CREATE TABLE`** on **`rideshare_dev.processed`**
  - **`CREATE EXTERNAL TABLE`**, **`READ FILES`**, and **`WRITE FILES`**
    on **`el_rideshare_dev`**
  - Table owner **`SELECT`** / **`MODIFY`** on
    **`rideshare_dev.processed.fare_maint_lab`** and
    **`rideshare_dev.processed.fare_dv_lab`**
- Workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the compute used here
