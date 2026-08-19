# Module 10 — Delta Lake Foundations

## Purpose

Understand what a Delta table is, how it tracks versions, how managed and
external tables differ, and how historical states can be queried and restored.

## Learning objectives

By the end of this module, you'll be able to:

- Show why a one-row fare correction is a full Parquet rewrite, and apply the
  same correction as a Delta `UPDATE` that records the change in `_delta_log`
- Walk `_delta_log` commit by commit (`protocol` / `metaData` / `commitInfo` /
  `add` / `remove`), reconstruct the current snapshot, and read
  `DESCRIBE HISTORY`
- Prove managed and external Unity Catalog tables are both Delta, then
  contrast storage location, `DROP` / `UNDROP` / external re-registration, and
  **manual capability vs managed-table automation**
- Query a past snapshot (`VERSION AS OF`, `TIMESTAMP AS OF`, one PySpark
  `versionAsOf` read) and `RESTORE` it; explain why `VACUUM` can cut how far
  back those files still exist

This module does not teach ACID internals, concurrency, schema evolution,
deletion vectors, `MERGE`, or `OPTIMIZE` / `VACUUM` behavior — those are
Module 11. Grants are Module 12.

## Prerequisites

Complete Module 9 notebooks **`01`–`06`**. You need the Module 5 platform
(not the teaching pipeline tables):

| Asset | Notes | Source |
|---|---|---|
| Catalog `rideshare_dev`; schema `processed` | Course catalog | Module 5 `01 - Unity Catalog Volumes and Data Landing.py` |
| External location `el_rideshare_dev` | `url` used for the 03 external `LOCATION` | Module 5 `01 - Unity Catalog Volumes and Data Landing.py` |
| Volume `rideshare_dev.processed.output_files` | 01–02 practice folders | Module 5 `01 - Unity Catalog Volumes and Data Landing.py` |

Recall Module 5 `07 - Write Patterns and Table Preview.py`: Parquet and a
Delta **folder** under `practice/`, plus managed `saveAsTable`. This module
is the first **row change**.

Does **not** read or mutate `trip_enriched`, `trip_driver_assignment`, KPI
tables, or `curated/`. Notebooks **03** and **04** are self-contained (they
do not require 01–02 folders or each other's tables).

## Dataset

Four-row handmade extract (`trip_id` **1001–1004**), not the 100-row source
files. Lab object names:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md)
(Module 10 lab objects). Columns from `trip.service_type` and `payment`
(no `driver_payout_amount`). `service_type` uppercase; `payment_method`
lowercase.

```text
trip_id bigint
service_type string
payment_method string
base_fare_amount decimal(10,2)
tip_amount decimal(10,2)
```

| trip_id | service_type | payment_method | base_fare_amount | tip_amount | Lab use |
|---|---|---|---:|---:|---|
| 1001 | STANDARD | card | 20.00 | 3.00 | 01 and 03 exercise: tip → **4.00** |
| 1002 | SHARED | cash | 15.00 | 0.00 | 02 and 04: deleted |
| 1003 | PREMIUM | card | 40.00 | 6.00 | Worked `UPDATE` in 01–04: tip → **10.00** |
| 1004 | STANDARD | wallet | 25.00 | 2.50 | 02 and 04: second write |

First Delta writes: deletion vectors **off**. Ignore `.crc` files in
listings.

## Paths and outputs

| Notebook | Object | Location |
|---|---|---|
| 01 | Parquet folder | `/Volumes/rideshare_dev/processed/output_files/practice/fare_correction_parquet/` |
| 01 | Delta folder | `/Volumes/rideshare_dev/processed/output_files/practice/fare_correction_delta/` |
| 02 | Delta folder | `/Volumes/rideshare_dev/processed/output_files/practice/fare_log_delta/` |
| 03 | Managed table | `rideshare_dev.processed.fare_managed_lab` (no `LOCATION`; files under `{abfss_root}/uc-managed`) |
| 03 | External table | `rideshare_dev.processed.fare_external_lab` at `{url from DESCRIBE EXTERNAL LOCATION el_rideshare_dev}/external-tables/fare_external_lab` (**not** a Volume path) |
| 04 | Managed table | `rideshare_dev.processed.fare_timetravel_lab` (no `LOCATION`) |

No `saveAsTable` in **01–02**. 01–02 use `UPDATE` / `DELETE` on
`` delta.`<path>` ``. 03–04 use fully qualified `catalog.schema.table`. Bound
versions and `LOCATION` use `spark.sql`; `%sql` only for fixed names.

**Cleanup:** Module 5 `99 - Rideshare Project Cleanup and Reset.py` Level 1
clears all of `practice/` (including 01–02 folders). Notebook 03 setup
`DROP`s both 03 tables and `rm`s `external-tables/fare_external_lab`.
Notebook 04 setup `DROP TABLE IF EXISTS fare_timetravel_lab`. Level 4
`DROP CATALOG CASCADE` drops lab **names**; it does **not** by itself delete
03's ADLS files.

## Notebooks

Four notebooks, in order. This module **ends after 04**. Notebooks **01**,
**03**, and **04** each end with a short exercise. **02** has **no exercise**.

| # | Notebook | Focus |
|---|---|---|
| 01 | Why Delta Lake Exists | Isolated `fare_correction_parquet/` vs `fare_correction_delta/` (do not touch `fare_log_delta/`). Write 4 Parquet rows (1003 tip **6.00**, no `_delta_log`) → business need (1003 → **10.00**, keep **4** rows) → Parquet read/`when`/overwrite → Parquet limits (no transactional `UPDATE`; failed writes can leave a bad folder) → same original rows as Delta (DV off) → path `UPDATE` → verify → `ls` leftover files + `_delta_log` (do **not** open JSON; do **not** name `add`/`remove`). Note: Volume folders so `ls` works; managed tables such as `trip_enriched` are also Delta under `abfss://`. Fence: no ACID, time travel, `DESCRIBE HISTORY`, `DELETE`, `MERGE`, `VACUUM`, DV teaching. Exercise: `UPDATE` **1001** **3.00 → 4.00**; still **4** rows |
| 02 | Understanding the Delta Transaction Log | Recreate `fare_log_delta/` only. Walk commits: v0 empty (`protocol`/`metaData`/`commitInfo`, typically no data `.parquet`, Delta read **0**) → v1 `add` **1001–1003** (**3**) → v2 `add` **1004** (**4**) → v3 `UPDATE` 1003 `remove`+`add` (**4**, leftover file may remain) → v4 `DELETE` **1002** `remove`+`add` (**3**). Replay add/remove vs `ls` (snapshot ≠ leftover files). `DESCRIBE HISTORY` on the path. Stop before time travel. Fence: no `VERSION AS OF` / `TIMESTAMP AS OF` / `RESTORE` / `OPTIMIZE` / `VACUUM` / checkpoints / DV teaching. **No exercise** |
| 03 | Managed vs External Delta Tables | Self-contained original four rows (1003 = **6.00**). Empty managed `CREATE` (no `LOCATION`) + empty external `CREATE … LOCATION` → type/location proof (`DESCRIBE DETAIL` format+location; `rideshare_dev.information_schema.tables` `table_type`/`storage_path`; `DESCRIBE TABLE EXTENDED` Type; `LIST` external succeeds, `LIST` managed URI expected failure) → `INSERT` both (**4**) → `UPDATE` both (1003 → **10.00**) + `DESCRIBE HISTORY` on names → `OPTIMIZE` + `VACUUM DRY RUN` on **both** as **feature-support proof only** (tiny data may rewrite/list nothing; no Z-ORDER, retention, or real `VACUUM`) → `DESCRIBE TABLE EXTENDED` Predictive Optimization if present (do **not** `ALTER`): the DRY RUN proof is **manual capability** on both types; PO is **managed-table automation** only → external `DROP`/`LIST` files remain/`SHOW TABLES DROPPED`/`UNDROP`/`DROP`/re-register without column list → managed `DROP`/`UNDROP` (do **not** `CREATE` between; classroom `LIST` does not show managed files) → short decision guide. Leave managed undropped and external re-registered. Fence: no `VERSION AS OF`/`RESTORE`; no `GRANT` (Module 12); no Volume `LOCATION`. Exercise: `UPDATE` **1001** **3.00 → 4.00** on `fare_managed_lab` (still **4** rows); which `information_schema` row is `EXTERNAL`, and which `storage_path` kept files during `DROP`? |
| 04 | Delta Time Travel and Restore | Self-contained managed `fare_timetravel_lab`. Generate `CREATE` (**0**) → `INSERT` 1001–1003 (**3**, 1003 = **6.00**) → `INSERT` 1004 (**4**) → `UPDATE` 1003 → **10.00** (**4**, 1002 present) → `DELETE` 1002 (**3**); `time.sleep(2)` after each data commit; capture versions/timestamps (`yyyy-MM-dd HH:mm:ss`). `DESCRIBE HISTORY` is the index (read `operation` from the grid). `VERSION AS OF` / `TIMESTAMP AS OF` on the pre-update commit (both **4** rows, 1003 = **6.00**). Compare current (after delete) vs `VERSION AS OF` before-update / after-update (= before-delete) / after-delete. One PySpark `versionAsOf` read (no `timestampAsOf` option, no PySpark restore API). Historical reads leave current unchanged. `RESTORE TABLE … TO VERSION AS OF` the update version (new HISTORY row; **4** rows, 1002 back); brief `RESTORE … TO TIMESTAMP AS OF` the **UPDATE** timestamp (rows look unchanged; proof is the new version). Retention warning: `VACUUM` can remove files a snapshot still names — do **not** run `VACUUM` or re-interpret 03's DRY RUN. Fence: no `UNDROP`, `CLONE`, CDF, JSON, `@v` syntax, time travel on teaching tables. Exercise: `VERSION AS OF` the delete version (**3** rows, 1002 gone); current without `AS OF` still **4** rows; do **not** `RESTORE`. Module 10 ends here; next is Module 11 |

## Minimum privileges required

- Unity Catalog (no catalog / external-location / volume **DDL** here — Module
  5 already created those objects):
  - **`USE CATALOG`** on **`rideshare_dev`**
  - **`USE SCHEMA`** on **`rideshare_dev.processed`**
  - **`READ VOLUME`** / **`WRITE VOLUME`** on
    **`rideshare_dev.processed.output_files`** (01–02 practice folders)
  - **`CREATE TABLE`** on **`rideshare_dev.processed`** (03–04 lab tables)
  - **`CREATE EXTERNAL TABLE`**, **`READ FILES`**, and **`WRITE FILES`** on
    **`el_rideshare_dev`** (`03 - Managed vs External Delta Tables.py`)
  - Table owner **`SELECT`** / **`MODIFY`** on the lab tables this module
    creates (`RESTORE` needs **`MODIFY`**)
  - **`UNDROP`** is not a grantable privilege; table owner (or **`MANAGE`**)
    plus catalog/schema use is enough
  - Session temp views for 03 inserts are allowed; that is not schema DDL
- Workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the compute used here
