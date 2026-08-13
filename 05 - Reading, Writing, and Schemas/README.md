# Module 5 — Reading, Writing, and Schemas

## Purpose

Land the shared rideshare dataset on UC Volumes and read/write production
formats with explicit schemas.

## Learning objectives

By the end of this module, you'll be able to:

- Set Tier 1 lab config (storage account, container, storage credential,
  ADLS folder) and create `rideshare_dev` landing/processed volumes
- Copy repo source files into
  `/Volumes/rideshare_dev/landing/source_files/{dataset}/` and verify
- Land full-size controlled-bad `bad_trip_data.csv` and `bad_payment_data.csv`
  variants for the Module 6 cleaning walkthrough
- Read one production format per dataset — CSV, JSON Lines, Parquet, XML,
  Avro — with explicit schemas and informed use of **`inferSchema`**
- Apply light reshape after read; compare format trade-offs
- Write practice outputs under
  `/Volumes/rideshare_dev/processed/output_files/practice/{output_name}/`
- Use save modes and a brief partitioned write; preview Delta as a **file**
  format under
  `/Volumes/rideshare_dev/processed/output_files/practice/` and create
  managed table **`rideshare_dev.processed.trip_time_preview`** with
  **`saveAsTable`** (files vs managed tables)

## Prerequisites

Module 4 — Transformations, Actions, and Lazy Evaluation. Understand
transformations vs actions, lazy evaluation, and that **`DataFrame.write`**
returns a writer; execution happens on terminal methods such as **`.save()`**,
**`.parquet()`**, or **`.saveAsTable()`**.

Each student uses **their own** Azure storage account and Databricks
workspace. `01 - Unity Catalog Volumes and Data Landing.py` creates the
course catalog, external location, schemas, and volumes in that account.

### Before Notebook 01

Complete these before running **`01 - Unity Catalog Volumes and Data Landing`**:

1. Own Azure Databricks workspace with Unity Catalog (Premium-capable)
2. Ability to **`CREATE CATALOG`** and **`CREATE EXTERNAL LOCATION`** on the
   metastore, plus **`CREATE EXTERNAL LOCATION`** on the storage credential
   named in the config cell
3. Azure Data Lake Storage Gen2 account + container, and a Unity Catalog
   **storage credential** that already exists and can access that storage
   (Access Connector / credential setup is in the course PDF — not this repo)
4. This course repo as a Databricks **Git folder** (open Notebook **01** from
   that folder so the copy cell can find `data/raw`)
5. Notebook attached to compute
6. In **`01 - Unity Catalog Volumes and Data Landing`** and
   **`99 - Rideshare Project Cleanup and Reset`**, overwrite the config cell
   with **your** storage account, container, storage credential, and ADLS
   folder

## Paths and outputs

Schemas, column names, Volume path rules, and the repo → Volume upload map:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).

| Role | Path |
|---|---|
| Reads | `/Volumes/rideshare_dev/landing/source_files/{dataset}/` |
| Module 5 writes | `/Volumes/rideshare_dev/processed/output_files/practice/{output_name}/` |

Do **not** use shorthand `processed/` alone. The `practice/` and `curated/`
tiers under `/Volumes/rideshare_dev/processed/output_files/` are created on
first write — `01 - Unity Catalog Volumes and Data Landing.py` does not
pre-create them. Schema names `landing` / `processed` are not medallion
layers (Modules 12–13).

`01 - Unity Catalog Volumes and Data Landing.py` creates platform objects;
**Module 11** explains governance (grants, ownership, credentials, least
privilege) on those existing objects.

## Notebooks

Seven content notebooks plus cleanup, in order. Each content notebook
(**01–07**) ends with a short hands-on task. **`99`** is a utility notebook
with no exercise.

| # | Notebook | Focus |
|---|---|---|
| 01 | Unity Catalog Volumes and Data Landing | Config cell (your Azure values); create ADLS project folder in Azure Portal; external location `el_rideshare_dev`, catalog `rideshare_dev`, schemas, volumes; `mkdirs`; copy canonical + controlled-bad sources into landing; verify |
| 02 | Reading CSV | Read **`trip`** from landing; explicit schema vs **`inferSchema`**; light reshape; practice write |
| 03 | Reading JSON | Read **`zone_lookup`** (JSON Lines) from landing |
| 04 | Reading Parquet | Read **`trip_time`** from landing |
| 05 | Reading XML | Read **`drivers`** with **`rowTag`** only — no **`explode`** (Module 6) |
| 06 | Reading Avro | Read **`payment`** from landing (Avro copied in `01 - Unity Catalog Volumes and Data Landing.py`) |
| 07 | Write Patterns and Table Preview | Save modes; brief partitioned write; Delta **file** under `/Volumes/rideshare_dev/processed/output_files/practice/` + managed **`saveAsTable`** to **`rideshare_dev.processed.trip_time_preview`** (managed location ≠ external volume); files vs tables; Module 6 `01 - Column Transforms with Built-in Functions.py` reads this table alongside landing **`trip_time`** Parquet; deep Delta → Module 10 |
| 99 | Rideshare Project Cleanup and Reset | Level 1 clear `/Volumes/rideshare_dev/processed/output_files/practice/`; Level 2 clear `/Volumes/rideshare_dev/processed/output_files/curated/` (Module 6 Parquet); Level 3 clear landing; Level 4 full teardown (drops managed tables including Module 7/8 `saveAsTable` outputs) |

## Minimum privileges required

- Unity Catalog: **`CREATE CATALOG`** and **`CREATE EXTERNAL LOCATION`** on the
  metastore; **`CREATE EXTERNAL LOCATION`** on the storage credential in the
  config cell; **`CREATE SCHEMA`**, **`CREATE VOLUME`**, and read/write course
  volumes under `rideshare_dev` after creation
- Workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the compute used here
- Azure RBAC: roles on **your** storage account for the access connector behind
  your storage credential (including File Events–related roles when testing
  the external location — see `01 - Unity Catalog Volumes and Data Landing.py`
  troubleshooting)
- Storage credential: must already exist; this module does not create it
