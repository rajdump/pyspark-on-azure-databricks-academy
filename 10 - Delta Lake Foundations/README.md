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
- Contrast managed and external Unity Catalog tables on storage location,
  `DROP` / `UNDROP` (including the managed dropped-table recovery window),
  and external re-registration, and choose managed vs external
  (Databricks-managed storage and optimizations vs path control)
- Query a past snapshot (`VERSION AS OF`, `TIMESTAMP AS OF`, one PySpark
  `versionAsOf` read) and `RESTORE` it; explain that historical access is
  bounded by retention and that `VACUUM` removes eligible files

This module does not teach ACID internals, concurrency, schema evolution,
deletion vectors, `MERGE`, or `OPTIMIZE` / `VACUUM` behavior — those are
Module 11. Grants are Module 12.

## Prerequisites

Complete Module 9 notebooks **`01`–`06`**. You need the Module 5 platform
(not the teaching pipeline tables):

| Asset | Notes | Source |
|---|---|---|
| Catalog `rideshare_dev`; schema `processed` | Course catalog | Module 5 `01 - Unity Catalog Volumes and Data Landing.py` |
| External location `el_rideshare_dev` | 03 table `LOCATION` only | Module 5 `01 - Unity Catalog Volumes and Data Landing.py` |
| Volume `rideshare_dev.processed.output_files` | 01–02 practice files | Module 5 `01 - Unity Catalog Volumes and Data Landing.py` |

Recall Module 5 `07 - Write Patterns and Table Preview.py`: Parquet and a
Delta **folder** under `practice/`, plus managed `saveAsTable`. This module
is the first **row change**.

Does **not** read or mutate `trip_enriched`, `trip_driver_assignment`, KPI
tables, or `curated/`. Notebooks **03** and **04** are self-contained (they
do not require 01 folders, `fare_log_delta/`, or each other's tables).

## Dataset

Four-row handmade extract (`trip_id` **1001–1004**), not the 100-row source
files. Columns from `trip.service_type` and `payment` (no
`driver_payout_amount`). `service_type` uppercase; `payment_method`
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
| 1001 | STANDARD | card | 20.00 | 3.00 | 01 exercise: tip → **4.00** |
| 1002 | SHARED | cash | 15.00 | 0.00 | 02 and 04: deleted |
| 1003 | PREMIUM | card | 40.00 | 6.00 | Worked `UPDATE` in 01, 02, and 04: tip → **10.00** |
| 1004 | STANDARD | wallet | 25.00 | 2.50 | 02 and 04: second write |

First Delta writes: deletion vectors **off**. Ignore `.crc` files in
listings.

## Paths and outputs

Object locations:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md)
(Module 10 — Delta Lake Foundations). `{url}` is the `url` column from
`DESCRIBE EXTERNAL LOCATION el_rideshare_dev` (strip a trailing slash).

| Notebook | Object |
|---|---|
| 01 | `fare_correction_parquet/`, `fare_correction_delta/` |
| 02 | `fare_log_delta/` |
| 03 | `rideshare_dev.processed.fare_managed_lab`; `rideshare_dev.processed.fare_external_lab` at `{url}/external-tables/fare_external_lab` |
| 04 | `rideshare_dev.processed.fare_timetravel_lab` |

No `saveAsTable` in **01–02**. 01 and 02 use path DML on `` delta.`<path>` ``.
02 starts with an empty DataFrameWriter `.save` at the Volume path. 03–04
use SQL `CREATE` and fully qualified names. Bound paths and `LOCATION` use
`spark.sql`; `%sql` only for fixed names.

**Cleanup:** Module 5 `99 - Rideshare Project Cleanup and Reset.py` Level 1
clears `practice/` files (01 folders and `fare_log_delta/`). Notebook 02
setup `rm`s `fare_log_delta/`. Notebook 03 setup `DROP`s both 03 tables and
`rm`s `external-tables/fare_external_lab`. Notebook 04 setup `DROP TABLE IF
EXISTS fare_timetravel_lab`. Level 4 `DROP CATALOG CASCADE` drops lab
**names**; it does **not** by itself delete 03's ADLS files.

## Notebooks

Four notebooks, in order. This module **ends after 04**. Notebooks **01**
and **04** each end with a short exercise. **02** and **03** have **no
exercise**.

| # | Notebook | Focus |
|---|---|---|
| 01 | Parquet Rewrite vs Delta UPDATE | Isolated `fare_correction_parquet/` vs `fare_correction_delta/` (do not touch `fare_log_delta/`). Write 4 Parquet rows (1003 tip **6.00**, no `_delta_log`) → business need (1003 → **10.00**, keep **4** rows) → Parquet read/`when`/overwrite → Parquet limits (no transactional `UPDATE`; failed writes can leave a bad folder) → same original rows as Delta (DV off) → path `UPDATE` → verify → `ls` leftover files + `_delta_log` (do **not** open JSON; do **not** name `add`/`remove`). Note: Volume folders so `ls` works; managed tables such as `trip_enriched` are also Delta under `abfss://`. Fence: no ACID, time travel, `DESCRIBE HISTORY`, `DELETE`, `MERGE`, `VACUUM`, DV teaching. Exercise: `UPDATE` **1001** **3.00 → 4.00**; still **4** rows |
| 02 | Understanding the Delta Transaction Log | Create Volume folder `fare_log_delta/` (empty DataFrameWriter `.save`, empty v0). Walk commits: v0 empty (`protocol`/`metaData`/`commitInfo`, typically no data `.parquet`, Delta read **0**) → v1 `add` **1001–1003** from `trips_extract` (**3**) → v2 `add` **1004** (**4**) → v3 `UPDATE` 1003 `remove`+`add` (**4**, leftover file may remain) → v4 `DELETE` **1002** `remove`+`add` (**3**). Replay add/remove vs `ls` (snapshot ≠ leftover files). `DESCRIBE HISTORY` on the path. Stop before time travel. Fence: no `VERSION AS OF` / `TIMESTAMP AS OF` / `RESTORE` / `OPTIMIZE` / `VACUUM` / checkpoints / DV teaching; no managed-vs-external proof; **no catalog table**. **No exercise** |
| 03 | Managed vs External Delta Tables | Self-contained original four rows (1003 stays **6.00**; 1001 stays **3.00**). Empty managed `CREATE` (no `LOCATION`, DV off) + empty external `CREATE … LOCATION` at `{url}/external-tables/fare_external_lab` (**0** rows) → `INSERT` both (**4**) → type/location proof (`DESCRIBE DETAIL` format+location; `rideshare_dev.information_schema.tables` `table_type`/`storage_path`; `LIST` external succeeds, `LIST` managed URI expected failure) → `DROP` both / `SHOW TABLES DROPPED` / external files remain → `UNDROP` both (**4**; managed = relation + files UC retained; external = relation over files that never left) → leave managed undropped; external `DROP` + re-register `CREATE … LOCATION` without column list (**4**) → decision guide (landing Volume / Bronze-Silver-Gold managed / fixed-path external; managed default = Databricks-managed storage and optimizations) → dropped-table recovery period for managed tables (default **7** days; catalog or schema, not per table; **0** hours disables `UNDROP`; **7–30** days; schema overrides catalog; `ALTER CATALOG` / `ALTER SCHEMA RETAIN DROPPED` **syntax only — do not run**). Fence: no `UPDATE`, `DESCRIBE HISTORY`, `OPTIMIZE`, `VACUUM`, `VERSION AS OF`/`RESTORE`; no `GRANT` (Module 12); no Volume `LOCATION`; no Predictive Optimization demo. **No exercise** |
| 04 | Delta Time Travel and Restore | Self-contained managed `fare_timetravel_lab` (no `LOCATION`, DV off). Build history then identify versions from `DESCRIBE HISTORY` (no Python version captures): CREATE (0) → INSERT 1001–1003 (1, 3 rows, 1003 tip **6.00**) → INSERT 1004 (2, 4 rows) → UPDATE 1003 → **10.00** (3, 4 rows, 1002 present) → DELETE 1002 (4, 3 rows). HISTORY (`version`, `timestamp`, `operation`; SQL `INSERT`s typically `WRITE`). Time travel: `VERSION AS OF 2` vs current unchanged, then `VERSION AS OF 3`; `TIMESTAMP AS OF` version 2's HISTORY timestamp (at-or-before; same as version 2); one PySpark `versionAsOf` **2**. Time travel (read) vs `RESTORE` (new commit). One executable `RESTORE TO VERSION AS OF 3` (1002 back, 1003 = **10.00**, HISTORY version 5); timestamp `RESTORE` syntax only. If cells are re-run, use HISTORY numbers from that run. Retention: 30-day history vs 7-day `VACUUM` eligibility; do not run `VACUUM`. Fence: no `CLONE`, CDF, JSON, `@v`, teaching-table time travel, retention `ALTER`, PySpark `timestampAsOf` / `restoreToVersion`, `exceptAll`, `latest_history` helper. Exercise: PySpark `versionAsOf` **4** after restore (**3** rows); current still **4**. Module ends here; next is Module 11 |

## Minimum privileges required

- Unity Catalog (no catalog / external-location / volume **CREATE** /
  **DROP** here — Module 5 already created those objects). Notebook 03
  shows `ALTER CATALOG` / `ALTER SCHEMA RETAIN DROPPED` as **syntax only**
  — do not run it; **`MANAGE`** on the catalog or schema is not required:
  - **`USE CATALOG`** on **`rideshare_dev`**
  - **`USE SCHEMA`** on **`rideshare_dev.processed`**
  - **`READ VOLUME`** / **`WRITE VOLUME`** on
    **`rideshare_dev.processed.output_files`**
  - **`CREATE TABLE`** on **`rideshare_dev.processed`** (03–04)
  - **`CREATE EXTERNAL TABLE`**, **`READ FILES`**, and **`WRITE FILES`** on
    **`el_rideshare_dev`** (03 only)
  - Table owner **`SELECT`** / **`MODIFY`** on the lab tables this module
    creates (`RESTORE` needs **`MODIFY`**)
  - **`UNDROP`** is not a grantable privilege; table owner (or **`MANAGE`**)
    plus catalog/schema use is enough
  - Session temp views for 03 inserts are allowed; that is not schema DDL
- Workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the compute used here
