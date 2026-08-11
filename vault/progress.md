---
aliases:
  - Course Progress
tags:
  - course/progress
  - status/started
updated: 2026-08-12
---

# Course progress

> [!important] Status authority
> [COURSE_MODULES](../COURSE_MODULES.md) is the author-owned source of truth.
> This note summarizes the repository as inspected on **2026-08-12** and does
> not change roadmap or runtime-validation status.

## At a glance

- **19 planned modules**
- **7 complete** — Modules 01–07
- **1 started** — Module 08
- **11 not started** — Modules 09–19
- **44 Databricks source notebooks on disk**
- **39 notebook entries with recorded runtime evidence**
- **Current work:** Module 08 Notebook 08 — Build KPI Tables (docs/contracts
  locked; author `.py` from approved md replica)

## Phase summary

| Phase | Modules | Current state |
|---|---:|---|
| I — Language and Engine Foundations | 01–04 | Complete |
| II — Core Data Engineering Skills | 05–07 | Complete |
| II — Current authoring | 08 | Started |
| II — Next module | 09 | Not started |
| III — Lakehouse and Governance | 10–12 | Not started |
| IV — Production Batch Engineering | 13–15 | Not started |
| V — Excellence and Delivery | 16–19 | Not started |

## Module tracker

| Module | Roadmap | Files on disk | Runtime evidence |
|---|---|---:|---|
| [01 — Foundations](../01%20-%20Azure%20Databricks%20and%20Spark%20Foundations/README.md) | Complete | 4 of 4 | 4 of 4 |
| [02 — DataFrames](../02%20-%20DataFrame%20Fundamentals/README.md) | Complete | 6 of 6 | 5 of 6 |
| [03 — Cleaning and NULLs](../03%20-%20Data%20Cleaning,%20NULL%20Semantics,%20and%20Type%20Handling/README.md) | Complete | 4 of 4 | 4 of 4 |
| [04 — Execution model](../04%20-%20Transformations,%20Actions,%20and%20Lazy%20Evaluation/README.md) | Complete | 4 of 4 | 4 of 4 |
| [05 — I/O and schemas](../05%20-%20Reading,%20Writing,%20and%20Schemas/README.md) | Complete | 8 of 8 | 8 of 8 |
| [06 — Built-ins and complex types](../06%20-%20Built-in%20Functions,%20Complex%20Types,%20and%20UDF%20Alternatives/README.md) | Complete | 4 of 4 | 4 of 4 |
| [07 — Joins and set operations](../07%20-%20Joins%20and%20Set%20Operations/README.md) | Complete | 7 of 7 | 7 of 7 |
| [08 — Aggregations and windows](../08%20-%20Aggregations%20and%20Window%20Functions/README.md) | Started | 7 of 8 | 3 of 8 |
| 09 — Spark SQL and DataFrame Interoperability | Not started | 0 | 0 |
| 10–19 | Not started | 0 | 0 |

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
- **Evidence gap:** Module 02 Notebook 05 exists and is fully authored, but
  [Module 02 validation](../docs/validation/02%20-%20DataFrame%20Fundamentals.md)
  has no matching runtime entry.

### Modules 05–06 — Landing and curated data

- All twelve notebooks, including cleanup utility 99, have Standard and
  serverless runtime evidence.
- Module 05 lands canonical formats into Unity Catalog Volumes and separates
  `practice/` from `curated/`.
- Module 06 produces:
  - `curated/drivers_flat/`
  - `curated/trip/` — 106 rows
  - `curated/payment/` — 105 rows
- Built-in Spark functions remain the default; Python UDFs are a last-resort
  contrast.

### Module 07 — Unified managed tables

- All seven notebooks passed on classic all-purpose Standard compute on
  2026-08-05.
- Serverless compatibility has not been tested.
- The BRD and both mappings are approved and signed off.
- Outputs:
  - `trip_enriched` — 106 rows, 16 columns
  - `trip_driver_assignment` — 100 rows, 13 columns

Requirements:

- [Business requirements](../07%20-%20Joins%20and%20Set%20Operations/requirements/BRD.md)
- [Trip enriched mapping](../07%20-%20Joins%20and%20Set%20Operations/requirements/trip_enriched_mapping.md)
- [Driver assignment mapping](../07%20-%20Joins%20and%20Set%20Operations/requirements/trip_driver_assignment_mapping.md)

## Current focus — Module 08

### Authored

- Notebook 01 — GroupBy and Basic Aggregations — validated
- Notebook 02 — Multi-column Keys, NULL Groups, and Filter Placement —
  validated
- Notebook 03 — Collections, Percentiles, and Distinct Counts — validated
- Notebook 04 — Pivot — authored, runtime evidence pending
- Notebook 05 — Window Functions Fundamentals — authored, runtime evidence
  pending
- Notebook 06 — Running Totals and Lag and Lead — authored, runtime evidence
  pending
- Notebook 07 — Top-N per Group and Sampling — authored with active,
  uncommitted local polish; runtime evidence pending

The `TODO` markers inside these notebooks are learner exercise scaffolding,
not unfinished author content.

### Missing

- `08 - Build KPI Tables.py` (md replica approved; contracts in Module 8 README)
- Runtime evidence for Notebooks 04–08
- Author-owned roadmap transition from Started to Complete after authoring and
  Azure validation

### Planned KPI outputs

| Output | Intended grain |
|---|---|
| `rideshare_dev.processed.kpi_daily_trip_summary` | One row per non-NULL `trip_date` — 14 rows |
| `rideshare_dev.processed.kpi_zone_performance` | One row per pickup borough and pickup zone — 20 rows |
| `rideshare_dev.processed.kpi_driver_productivity` | One row per `driver_id` — 12 rows |

All three are overwrite-mode managed Delta tables via `saveAsTable`. Column
contracts: [Module 8 README](../08%20-%20Aggregations%20and%20Window%20Functions/README.md#paths-and-outputs).

## Next sequence

1. Author Module 08 Notebook 08 (`08 - Build KPI Tables.py`) from the approved
   md replica and Module 8 README contract.
2. Run Module 08 Notebooks 04–08 in Azure Databricks using Standard
   all-purpose compute first.
3. Record runtime evidence in
   [Module 08 validation](../docs/validation/08%20-%20Aggregations%20and%20Window%20Functions.md).
4. Let the author update [COURSE_MODULES](../COURSE_MODULES.md) after the
   module meets the Complete definition.
5. Begin Module 09 — Spark SQL and DataFrame Interoperability.

## Documentation and consistency backlog

### High priority

- [ ] Confirm or add the missing Module 02 Notebook 05 runtime record.
- [ ] Reconcile [[NB07_personal_notes|NB07 personal notes]] with approved
  mappings. The personal note currently shows `surge_amount` in
  `trip_enriched` and time/payment fields in `trip_driver_assignment`; neither
  belongs to the signed-off targets.
- [ ] Review `databricks.yml`: its committed workspace host conflicts with the
  repository rule against committed workspace URLs.

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

- Module 09: dual DataFrame/SQL API patterns and KPI reads
- Module 10: Delta Lake
- Module 11: govern existing Unity Catalog objects
- Module 12: formal medallion architecture and fuller purpose-built tables
- Module 13: reliable incremental batch processing
- Module 14: Lakeflow Pipelines for batch
- Module 15: Lakeflow Jobs and deployment
- Module 16: performance and Spark internals
- Module 17: tests and data quality
- Module 18: observability and operations
- Module 19: deployable capstone

## Related

- [[home|Vault home]]
- [[decisions|Course decisions]]
- [COURSE_MODULES](../COURSE_MODULES.md) — canonical roadmap
- [Validation policy](../docs/standards/compute-validation-policy.md)
