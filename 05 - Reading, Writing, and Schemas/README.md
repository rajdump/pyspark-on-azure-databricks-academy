# Module 5 — Reading, Writing, and Schemas

## Purpose

Land the shared rideshare dataset on Unity Catalog Volumes and read/write
production file formats with explicit schemas. This module is **hybrid I/O**:
schemas, readers/writers, and minimal reshape (rename, select, basic cast).
Systematic transforms and `explode()` belong in Module 6.

## Learning objectives

By the end of this module, you'll be able to:

- Work with catalog **`academy`**, schema **`rideshare`**, and Volumes
  **`raw`**, **`processed`**, and **`source`** using learner-facing Volume paths
- Create volumes and folder structure, copy repo source files into Volumes, and
  verify landed data
- Extract **`payment`** via JDBC (Azure SQL Database) and write Avro to
  **`raw/payment/`**
- Read one production format per dataset — CSV, JSON Lines, Parquet, XML, Avro
  — with explicit schemas and informed use of **`inferSchema`**
- Apply light reshape after read; compare format trade-offs
- Write files with save modes; introduce brief partitioned writes
- Preview Delta as a file format and one **`saveAsTable`** table write (deep
  Delta → Module 10; UC grants and external-location design → Module 11)

## Prerequisites

Module 4 — Transformations, Actions, and Lazy Evaluation. You should understand
transformations vs actions, lazy evaluation, and that **`write`** is an action.

## Approach and boundaries

**In scope:** Volume setup, JDBC load/extract, format reads, explicit schemas,
minimal reshape, write patterns, Delta/`saveAsTable` preview.

**Out of scope:** Deep transforms, **`explode()`**, UC grants, medallion
layering, Delta ACID/`MERGE` (Modules 6 and 10+).

Module 5 may write practice outputs. Schemas, column names, Volume path rules,
write ownership, repo → Volume upload map, format-to-dataset map, and JDBC
flow:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md) (Physical
layout and **`payment` JDBC exercise** sections). All five datasets under
Volume **`raw/`** (and **`source/payment/`** for JDBC seed).

## Notebook navigation

Eight notebooks, in this order:

1. **Unity Catalog Volumes and Data Landing**
   - Catalog / schema / volume awareness
   - **`CREATE VOLUME IF NOT EXISTS`** for **`raw`**, **`processed`**, **`source`**
     under existing **`el_lab`**
   - **`dbutils.fs.mkdirs`** for dataset folders
   - Copy repo files into Volume paths (see dataset-overview upload map); verify with **`ls`**
2. **Azure SQL Load and Extract**
   - Read seed from **`source/payment/`**
   - JDBC write → **`el_lab.payments`**; JDBC read back
   - Write Avro → **`raw/payment/`**
   - Call out: SQL table **`el_lab.payments`** ≠ Volume folder **`payment`**
   - **All-purpose cluster required** (JDBC write); do not claim serverless
3. **Reading CSV with Schemas**
   - Read **`trip`** from **`raw/trip/`**
   - Explicit schema vs **`inferSchema`**; format trade-offs; light reshape
4. **Reading JSON with Schemas**
   - Read **`zone_lookup`** (JSON Lines) from **`raw/zone_lookup/`**
5. **Reading Parquet with Schemas**
   - Read **`trip_time`** from **`raw/trip_time/`**
6. **Reading XML with Schemas**
   - Read **`drivers`** with **`rowTag`** only — no **`explode`** (Module 6)
7. **Reading Avro with Schemas**
   - Read **`payment`** from **`raw/payment/`**
8. **Write Patterns and Table Preview**
   - Save modes; brief partitioned write
   - Delta as output-format preview and/or one **`saveAsTable`** preview
   - One note: files vs tables; deep Delta → Module 10

## JDBC connection (author workspace only)

Configure in the Databricks workspace — **never commit** server names, passwords,
or connection strings to this repository. Pattern:

- Secret scope: **`el-lab`**, key: **`sql-password`**
- Target table: **`el_lab.payments`**
- Use **`dbutils.secrets.get`** in the notebook; document the variable names
  here, not the secret values

## Exercises

Each notebook ends with a short hands-on task — for example, verifying a Volume
path, reading with an explicit schema, or writing with a chosen save mode.

## Minimum privileges required

- Databricks workspace: **`CAN ATTACH TO`** or **`CAN RESTART`** on all-purpose
  compute (JDBC write notebook)
- Unity Catalog: **`USE CATALOG`** on **`academy`**, **`USE SCHEMA`** on
  **`rideshare`**, **`CREATE VOLUME`** / write access on course volumes as
  configured in the lab
- Azure RBAC: none beyond standard workspace access
