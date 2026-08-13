---
aliases:
  - Course Progress
tags:
  - course/progress
  - status/started
updated: 2026-08-13
---

# Course progress

> [!important] Status authority
> [COURSE_MODULES](../COURSE_MODULES.md) is the author-owned source of truth.
> This note summarizes the repository as inspected on **2026-08-13** and does
> not change roadmap or runtime-validation status.

## At a glance

- **20 planned modules**
- **9 complete** — Modules 01–09
- **11 not started** — Modules 10–20
- **51 Databricks source notebooks on disk**
- **51 notebook entries with recorded runtime evidence**
- **Current work:** Module 10 — Delta Lake for Managed Tables

## Phase summary

| Phase | Modules | Current state |
|---|---:|---|
| I — Language and Engine Foundations | 01–04 | Complete |
| II — Core Data Engineering Skills | 05–09 | Complete |
| III — Lakehouse Design and Implementation | 10–13 | Not started (working design; next: Module 10) |
| IV — Reliable Batch Pipelines | 14–15 | Not started |
| V — Quality, Delivery, and Operations | 16–20 | Not started |

## Module tracker

| Module | Roadmap | Files on disk | Runtime evidence |
|---|---|---:|---|
| [01 — Foundations](../01%20-%20Azure%20Databricks%20and%20Spark%20Foundations/README.md) | Complete | 4 of 4 | 4 of 4 |
| [02 — DataFrames](../02%20-%20DataFrame%20Fundamentals/README.md) | Complete | 6 of 6 | 6 of 6 |
| [03 — Cleaning and NULLs](../03%20-%20Data%20Cleaning,%20NULL%20Semantics,%20and%20Type%20Handling/README.md) | Complete | 4 of 4 | 4 of 4 |
| [04 — Execution model](../04%20-%20Transformations,%20Actions,%20and%20Lazy%20Evaluation/README.md) | Complete | 4 of 4 | 4 of 4 |
| [05 — I/O and schemas](../05%20-%20Reading,%20Writing,%20and%20Schemas/README.md) | Complete | 8 of 8 | 8 of 8 |
| [06 — Built-ins and complex types](../06%20-%20Built-in%20Functions,%20Complex%20Types,%20and%20UDF%20Alternatives/README.md) | Complete | 4 of 4 | 4 of 4 |
| [07 — Joins and set operations](../07%20-%20Joins%20and%20Set%20Operations/README.md) | Complete | 7 of 7 | 7 of 7 |
| [08 — Aggregations and windows](../08%20-%20Aggregations%20and%20Window%20Functions/README.md) | Complete | 8 of 8 | 8 of 8 |
| [09 — Spark SQL and DataFrame Interoperability](../09%20-%20Spark%20SQL%20and%20DataFrame%20Interoperability/README.md) | Complete | 6 of 6 | 6 of 6 |
| 10–20 | Not started | 0 | 0 |

`05 - Reading, Writing, and Schemas/99 - Rideshare Project Cleanup and
Reset.py` is included in Module 05's eight files.

## Completed modules

### Modules 01–04 — Foundations

- Core platform, DataFrame, cleaning, NULL, type-safety, lazy-execution, and
  action concepts are fully authored.
- Standard all-purpose compute passed for all recorded entries.
- Serverless limitations are documented where applicable:
  - Module 01: DBR metadata and `spark.app.id`
  - Module 02 Notebook 06: global temporary views
- Module 04 Notebook 03 uses Dedicated all-purpose compute for the clearest
  partition and shuffle demonstration.

### Modules 05–06 — Landing and curated data

- All twelve notebooks, including cleanup utility 99, have Standard and
  serverless runtime evidence.
- Module 05 lands canonical formats into Unity Catalog Volumes and separates
  `practice/` from `curated/`.
- Module 06 produces cleaned curated Parquet under the Volume `curated/`
  paths.

### Module 07 — Joins and set operations

- All seven notebooks validated on classic all-purpose Standard (2026-08-05).
- Managed analytical tables written by Notebook 07:
  - `trip_enriched` — 106 rows, 16 columns
  - `trip_driver_assignment` — 100 rows, 13 columns

Requirements:

- [Business requirements](../07%20-%20Joins%20and%20Set%20Operations/requirements/BRD.md)
- [Trip enriched mapping](../07%20-%20Joins%20and%20Set%20Operations/requirements/trip_enriched_mapping.md)
- [Driver assignment mapping](../07%20-%20Joins%20and%20Set%20Operations/requirements/trip_driver_assignment_mapping.md)

### Module 08 — Aggregations and window functions

- All eight notebooks authored and validated on classic all-purpose Standard
  access mode (Notebooks **01–03** on 2026-08-08; **04–08** on 2026-08-12).
- Evidence:
  [Module 08 validation](../docs/validation/08%20-%20Aggregations%20and%20Window%20Functions.md)
- Serverless not tested (policy: Standard baseline first; serverless is a
  later compatibility check).
- Managed KPI tables written by Notebook **08**:

| Output | Grain |
|---|---|
| `rideshare_dev.processed.kpi_daily_trip_summary` | One row per non-NULL `trip_date` — 14 rows |
| `rideshare_dev.processed.kpi_zone_performance` | One row per pickup borough and pickup zone — 20 rows |
| `rideshare_dev.processed.kpi_driver_productivity` | One row per `driver_id` — 12 rows |

Column contracts:
[Module 8 README](../08%20-%20Aggregations%20and%20Window%20Functions/README.md#paths-and-outputs).

### Module 09 — Spark SQL and DataFrame Interoperability

- All six notebooks authored and validated on classic all-purpose Standard
  and serverless (2026-08-13).
- Evidence:
  [Module 09 validation](../docs/validation/09%20-%20Spark%20SQL%20and%20DataFrame%20Interoperability.md)
- Dedicated not required (Standard passed). No writes; notebooks **01–05**
  have SQL exercises; **06** (`06 - End-to-End SQL Pipeline`) rebuilds the
  Module 8 KPI contracts in Spark SQL (read-only).

## Current focus — Module 10

**Next:** Module 10 — Delta Lake for Managed Tables.

**Roadmap status** for Module 10 in [COURSE_MODULES](../COURSE_MODULES.md)
is **Not Started**. Deepen Delta on existing managed tables; introductory
`MERGE` syntax only. Production incremental `MERGE` is Module 14.

## Next sequence

1. Author Module 10 — Delta Lake for Managed Tables.
2. Optionally run Module 07 and Module 08 serverless compatibility checks
   and record results in those modules' validation files.

## Documentation and consistency backlog

### High priority

- [ ] Reconcile [[NB07_personal_notes|NB07 personal notes]] with approved
  mappings. The personal note currently shows `surge_amount` in
  `trip_enriched` and time/payment fields in `trip_driver_assignment`; neither
  belongs to the signed-off targets.

### Lower priority

- [ ] Decide whether Module 07 and Module 08 require serverless compatibility
  runs; current policy treats serverless as a compatibility check, not the
  baseline.
- [ ] Clarify that `data/raw/parquet/zone_lookup.parquet` is an authoring
  alternate with 20 rows, while canonical JSON has 22 and includes teaching
  rows 21–22.
- [ ] Remove repeated `.databricks` entries from `.gitignore` when doing
  configuration housekeeping.
- [ ] Place the open file-format and lakehouse teaching ideas from
  `take_notes/M5.txt` into an appropriate future module.

## Deferred roadmap work

Phase III is a working design. Canonical rows:
[COURSE_MODULES](../COURSE_MODULES.md). Ownership addendum: [[decisions#D-021 — 20-module advanced roadmap]].

- Module 10: Delta Lake for Managed Tables (`MERGE` syntax only)
- Module 11: govern existing `landing` / `processed` assets
- Module 12: paper-design medallion (no objects created)
- Module 13: full-refresh `bronze` / `silver` / `gold` plus `src/`
- Module 14: production incremental `MERGE`
- Module 15: required batch Lakeflow Pipelines
- Module 16: testing, data quality, and code quality
- Module 17: performance and Spark internals
- Module 18: Lakeflow Jobs; create `databricks.yml` from scratch
- Module 19: observability and production operations
- Module 20: deployable capstone

## Related

- [[home|Vault home]]
- [[decisions|Course decisions]]
- [COURSE_MODULES](../COURSE_MODULES.md)
- [Validation policy](../docs/standards/compute-validation-policy.md)
