# Module 5 — Reading, Writing, and Schemas

## Purpose

Land the shared rideshare dataset on Unity Catalog Volumes and read/write
production file formats with explicit schemas. This module is **hybrid I/O**:
schemas, readers/writers, and minimal reshape (rename, select, basic cast).
Systematic transforms and `explode()` belong in Module 6.

Each student uses **their own** Azure storage account and Databricks
workspace. Notebook 01 creates the course catalog, external location,
schemas, and volumes in that account.

## Learning objectives

By the end of this module, you'll be able to:

- Set Tier 1 lab config (storage account, container, storage credential,
  ADLS folder) and create `rideshare_dev` landing/processed volumes
- Copy repo source files into
  `/Volumes/rideshare_dev/landing/source_files/{dataset}/` and verify
- Read one production format per dataset — CSV, JSON Lines, Parquet, XML,
  Avro — with explicit schemas and informed use of **`inferSchema`**
- Apply light reshape after read; compare format trade-offs
- Write practice outputs under
  `/Volumes/rideshare_dev/processed/output_files/practice/{output_name}/`
- Use save modes and a brief partitioned write; preview Delta as a **file**
  format under `practice/` and a managed **`saveAsTable`** into
  `rideshare_dev.processed` (files vs managed tables contrast; deep Delta →
  Module 10; UC grants → Module 11)

## Prerequisites

Module 4 — Transformations, Actions, and Lazy Evaluation. You should understand
transformations vs actions, lazy evaluation, and that **`write`** is an action.

### Before Notebook 01

1. Own Azure Databricks workspace with Unity Catalog (Premium-capable)
2. Ability to **`CREATE CATALOG`**, **`CREATE EXTERNAL LOCATION`**, and
   **`CREATE VOLUME`** in your metastore
3. Azure Data Lake Storage Gen2 account + container, and a Unity Catalog
   **storage credential** that already exists and can access that storage
   (how to create the Access Connector and credential is covered in the
   course PDF materials — not in this repository)
4. This course repo available as a Databricks **Git folder**
5. Notebook attached to compute
6. In Notebooks 01 and 99, overwrite the config cell with **your** storage
   account, container, storage credential, and ADLS folder (optional
   `repo_root` if auto-find of `data/raw` fails)

## Approach and boundaries

**In scope:** Volume setup, format reads, explicit schemas, minimal reshape,
write patterns, Delta file write + managed `saveAsTable` preview.

**Out of scope:** Deep transforms, **`explode()`**, UC grants, medallion
layering, Delta ACID/`MERGE` (Modules 6 and 10+). Creating storage
credentials (course PDF).

Schemas, column names, Volume path rules, and the repo → Volume upload map:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).

**Paths (do not use shorthand `processed/` alone):**

| Role | Path |
|---|---|
| Reads | `/Volumes/rideshare_dev/landing/source_files/{dataset}/` |
| Module 5 writes | `/Volumes/rideshare_dev/processed/output_files/practice/{output_name}/` |
| Module 6+ writes | `/Volumes/rideshare_dev/processed/output_files/curated/{output_name}/` |

`practice/` and `curated/` are created on first write — Notebook 01 does not
pre-create them. Schema names `landing` / `processed` are not medallion
layers (Module 12).

Notebook 01 creates platform objects; **Module 11** explains governance
(grants, ownership, credentials, least privilege) on those existing objects.

## Notebook navigation

Seven content notebooks plus cleanup, in this order. **Only Notebooks 01 and
99 exist on disk today**; 02–07 are planned next. When authoring, the next
content notebook number is **02** (ignore **99** for numbering).

1. **Unity Catalog Volumes and Data Landing** *(exists)*
   - Config cell (your Azure values); create ADLS project folder in Portal
   - Create external location `el_rideshare_dev`, catalog `rideshare_dev`,
     schemas, and volumes
   - `mkdirs` for dataset folders; copy repo files into landing; verify
2. **Reading CSV with Schemas**
   - Read **`trip`** from landing; explicit schema vs **`inferSchema`**;
     light reshape; practice write
3. **Reading JSON with Schemas**
   - Read **`zone_lookup`** (JSON Lines) from landing
4. **Reading Parquet with Schemas**
   - Read **`trip_time`** from landing
5. **Reading XML with Schemas**
   - Read **`drivers`** with **`rowTag`** only — no **`explode`** (Module 6)
6. **Reading Avro with Schemas**
   - Read **`payment`** from landing (Avro landed in Notebook 01)
7. **Write Patterns and Table Preview**
   - Save modes; brief partitioned write
   - Delta **file** write under `practice/` and managed **`saveAsTable`**
     into `rideshare_dev.processed` (managed location ≠ external volume)
   - Files vs tables; deep Delta → Module 10
99. **Rideshare Project Cleanup and Reset** *(exists)*
   - Level 1 clear `practice/`; Level 2 clear `curated/` (blast radius);
     Level 3 clear landing; Level 4 full teardown

## Exercises

Each notebook ends with a short hands-on task — for example, verifying a
Volume path, reading with an explicit schema, or writing with a chosen save
mode.

## Minimum privileges required

- Databricks workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the
  compute used in this module
- Unity Catalog: ability to **`CREATE CATALOG`**, **`CREATE EXTERNAL
  LOCATION`**, **`CREATE SCHEMA`**, **`CREATE VOLUME`**, and read/write the
  course volumes under `rideshare_dev` after creation
- Azure RBAC: roles on **your** storage account for the access connector
  behind your storage credential (including File Events–related roles when
  testing the external location — see Notebook 01 troubleshooting)
- Storage credential: must already exist; this module does not create it
