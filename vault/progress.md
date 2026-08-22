---
aliases:
  - Course Progress
tags:
  - course/progress
  - status/started
updated: 2026-08-23
---

# Course progress

> [!important] Status authority
> [COURSE_MODULES](../COURSE_MODULES.md) owns roadmap status. This note
> summarizes repository state as of **2026-08-23** and does not override it.

## At a glance

| | |
|---|---|
| Planned modules | 21 |
| Complete | 01–10 |
| Not started | 11–21 |
| Notebooks on disk | 55 |
| Current work | Module 11 — Delta Lake Transactions, Schema, and Maintenance |

Module 05 includes
`99 - Rideshare Project Cleanup and Reset.py` in its eight on-disk notebooks.

## Phase summary

| Phase | Modules | State |
|---|---:|---|
| I — Language and Engine Foundations | 01–04 | Complete |
| II — Core Data Engineering Skills | 05–09 | Complete |
| III — Lakehouse Design and Implementation | 10–14 | 10 complete; next 11 |
| IV — Reliable Batch Pipelines | 15–16 | Not started |
| V — Quality, Delivery, and Operations | 17–21 | Not started |

## Module tracker

| Module | Roadmap | On disk |
|---|---|---:|
| [01](../01%20-%20Azure%20Databricks%20and%20Spark%20Foundations/README.md) | Complete | 4 |
| [02](../02%20-%20DataFrame%20Fundamentals/README.md) | Complete | 6 |
| [03](../03%20-%20Data%20Cleaning,%20NULL%20Semantics,%20and%20Type%20Handling/README.md) | Complete | 4 |
| [04](../04%20-%20Transformations,%20Actions,%20and%20Lazy%20Evaluation/README.md) | Complete | 4 |
| [05](../05%20-%20Reading,%20Writing,%20and%20Schemas/README.md) | Complete | 8 |
| [06](../06%20-%20Built-in%20Functions,%20Complex%20Types,%20and%20UDF%20Alternatives/README.md) | Complete | 4 |
| [07](../07%20-%20Joins%20and%20Set%20Operations/README.md) | Complete | 7 |
| [08](../08%20-%20Aggregations%20and%20Window%20Functions/README.md) | Complete | 8 |
| [09](../09%20-%20Spark%20SQL%20and%20DataFrame%20Interoperability/README.md) | Complete | 6 |
| [10](../10%20-%20Delta%20Lake%20Foundations/README.md) | Complete | 4 |
| 11–21 | Not started | — |

For row counts, output tables, and column contracts, use
[dataset overview](../docs/data/dataset-overview.md) and each module README —
not this note.

## Current focus

**Module 11 — Delta Lake Transactions, Schema, and Maintenance**

Roadmap status in [COURSE_MODULES](../COURSE_MODULES.md): **Not Started**.

Scope (from roadmap): ACID semantics, optimistic concurrency, schema
enforcement and evolution, `OPTIMIZE`, `VACUUM`, deletion vectors, introductory
`MERGE` syntax. Production incremental `MERGE` is Module 15.

**Suggested sequence**

1. Complete Module 11 README design (`/write-module-readme` when ready).
2. Scaffold and author notebooks (`/new-lesson`, `/write-lesson`).
3. Run in Azure Databricks, then mark Complete in
   [COURSE_MODULES](../COURSE_MODULES.md) when asked.

## Backlog

### High priority

- [ ] Reconcile [`take_notes/NB07_personal_notes.md`](../take_notes/NB07_personal_notes.md)
  with approved Module 07 mappings (`surge_amount` and time/payment fields in
  personal notes are not in signed-off targets).

### Lower priority

- [ ] Serverless compatibility for Modules 07 and 08 (optional follow-on;
  policy treats serverless as a check after Standard).
- [ ] Document `data/raw/parquet/zone_lookup.parquet` (20 rows) vs canonical
  JSON (22 rows, teaching zones 21–22) in dataset docs.
- [ ] Place file-format and lakehouse teaching ideas from `take_notes/M5.txt`
  in a future module.
- [ ] Remove duplicate `.databricks` entries in `.gitignore` during config
  housekeeping.

## Related

- [[home|Vault home]]
- [[decisions|Course decisions]]
- [COURSE_MODULES](../COURSE_MODULES.md)
- [Compute validation policy](../docs/standards/compute-validation-policy.md)
