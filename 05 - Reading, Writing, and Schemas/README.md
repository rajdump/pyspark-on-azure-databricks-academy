# Module 5 — Reading, Writing, and Schemas

## Purpose

Land the shared rideshare dataset on Unity Catalog Volumes and read/write
production file formats with explicit schemas. This module is **hybrid I/O**:
schemas, readers/writers, and minimal reshape (rename, select, basic cast).
Systematic transforms and `explode()` belong in Module 6.

Each student uses **their own** Azure storage account and Databricks
workspace. **`01 - Unity Catalog Volumes and Data Landing`** creates the
course catalog, external location, schemas, and volumes in that account.

Schemas, column names, Volume path rules, and the repo → Volume upload map:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).

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
  format under `practice/` and create managed table
  **`rideshare_dev.processed.trip_time_preview`** with **`saveAsTable`**
  (files vs managed tables; Module 6 reuses this table for path-vs-table API
  parity; deep Delta → Module 10; UC grants → Module 11)

## Prerequisites

Module 4 — Transformations, Actions, and Lazy Evaluation. Understand
transformations vs actions, lazy evaluation, and that **`DataFrame.write`**
returns a writer; execution happens on terminal methods such as **`.save()`**,
**`.parquet()`**, or **`.saveAsTable()`**.

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

| Role | Path |
|---|---|
| Reads | `/Volumes/rideshare_dev/landing/source_files/{dataset}/` |
| Module 5 writes | `/Volumes/rideshare_dev/processed/output_files/practice/{output_name}/` |
| Module 6+ writes | `/Volumes/rideshare_dev/processed/output_files/curated/{output_name}/` |

Do **not** use shorthand `processed/` alone. `practice/` and `curated/` are
created on first write — Notebook **01** does not pre-create them. Schema
names `landing` / `processed` are not medallion layers (Module 12).

Notebook **01** creates platform objects; **Module 11** explains governance
(grants, ownership, credentials, least privilege) on those existing objects.

## Runtime and scope

All notebooks **01–07** and **99** are on disk and runtime-validated (see
`docs/validation/05 - Reading, Writing, and Schemas.md`).

**In scope:** Volume setup, format reads, explicit schemas, minimal reshape,
write patterns, Delta file write + managed `saveAsTable` preview.

**Out of scope:** Deep transforms, **`explode()`**, UC grants, medallion
layering, Delta ACID / `MERGE` (Modules 6 and 10+). Creating storage
credentials (course PDF).

## Notebooks

Seven content notebooks plus cleanup, in order. Each content notebook
(**01–07**) ends with a short hands-on task. **`99`** is a utility notebook
with no exercise.

| # | Notebook | Focus |
|---|---|---|
| 1 | Unity Catalog Volumes and Data Landing | Config cell (your Azure values); ADLS project folder; external location `el_rideshare_dev`, catalog `rideshare_dev`, schemas, volumes; `mkdirs`; copy canonical + controlled-bad sources into landing; verify |
| 2 | Reading CSV | Read **`trip`** from landing; explicit schema vs **`inferSchema`**; light reshape; practice write |
| 3 | Reading JSON | Read **`zone_lookup`** (JSON Lines) from landing |
| 4 | Reading Parquet | Read **`trip_time`** from landing |
| 5 | Reading XML | Read **`drivers`** with **`rowTag`** only — no **`explode`** (Module 6) |
| 6 | Reading Avro | Read **`payment`** from landing (Avro copied in Notebook **01**) |
| 7 | Write Patterns and Table Preview | Save modes; brief partitioned write; Delta **file** under `practice/` + managed **`saveAsTable`** to **`rideshare_dev.processed.trip_time_preview`** (managed location ≠ external volume); files vs tables; Module 6 **`01`** reads this table alongside landing **`trip_time`** Parquet; deep Delta → Module 10 |
| 99 | Rideshare Project Cleanup and Reset | Level 1 clear `practice/`; Level 2 clear `curated/` (blast radius); Level 3 clear landing; Level 4 full teardown |

## Minimum privileges required

- Workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the compute used here
- Unity Catalog: **`CREATE CATALOG`** and **`CREATE EXTERNAL LOCATION`** on the
  metastore; **`CREATE EXTERNAL LOCATION`** on the storage credential in the
  config cell; **`CREATE SCHEMA`**, **`CREATE VOLUME`**, and read/write course
  volumes under `rideshare_dev` after creation
- Azure RBAC: roles on **your** storage account for the access connector behind
  your storage credential (including File Events–related roles when testing
  the external location — see Notebook **01** troubleshooting)
- Storage credential: must already exist; this module does not create it
