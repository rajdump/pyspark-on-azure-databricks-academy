# Course Modules

Canonical owner of the full course roadmap: module numbers and titles, purpose,
major topics, prerequisites, production relevance, contribution to the final
project, and planning status.

This file does **not** contain notebook sequences, exercises, or code. Detailed
design lives in a module's `README.md` when present; see the status legend.

## Status legend

| Status | Meaning |
|---|---|
| Not Started | Roadmap entry — no learner notebooks yet (module `README.md` optional) |
| Started | Actively authoring notebooks — see its `README.md` for detailed design |
| Complete | Notebooks written, authoring-quality checked, and runtime-validated in Azure Databricks (see `docs/validation/`) |

Prerequisites list direct dependencies. The course learning path is
cumulative unless stated otherwise.

## Phases

- [Phase I — Language and Engine Foundations](#phase-i--language-and-engine-foundations-modules-14)
- [Phase II — Core Data Engineering Skills](#phase-ii--core-data-engineering-skills-modules-59)
- [Phase III — Lakehouse Design and Implementation](#phase-iii--lakehouse-design-and-implementation-modules-1013)
- [Phase IV — Reliable Batch Pipelines](#phase-iv--reliable-batch-pipelines-modules-1415)
- [Phase V — Quality, Delivery, and Operations](#phase-v--quality-delivery-and-operations-modules-1620)

## The running use case

Every module threads through the same small rideshare dataset — `trip`,
`trip_time`, `payment`, and `zone_lookup`, plus a supplementary nested
`drivers` dataset — so each topic builds on the same data instead of
switching examples. Full schema, join keys, and physical layout:
[`docs/data/dataset-overview.md`](docs/data/dataset-overview.md).

---

## Phase I — Language and Engine Foundations (Modules 1–4)

Learn the Databricks environment, build DataFrame fluency, handle imperfect
data, and understand Spark execution.

| # | Module | Purpose | Major Topics | Prerequisites | Production Relevance | Final-Project Contribution | Status |
|---|---|---|---|---|---|---|---|
| 1 | Azure Databricks and Spark Foundations | Orient in the Azure Databricks workspace and build a mental model of how Spark executes code — before real data-engineering logic | Spark architecture (driver/executor, jobs/stages/tasks); compute types and access modes; notebooks, magics, `dbutils`; `SparkSession` and first DataFrame | None — assumes root [README.md](README.md#who-this-is-for) baseline (basic Python, basic SQL) | Compute and platform literacy every later module depends on | Establishes the environment the final project runs in | Complete |
| 2 | DataFrame Fundamentals | Build core DataFrame fluency: create, inspect, reshape, express, filter, and query through temp views and Spark SQL | Creating/inspecting DataFrames; `select`/`withColumn`/`withColumns`/rename/`drop`; `F.col`/`F.when`/`F.lit`; `F.expr`/`selectExpr`; `filter`/`where`; intro NULL/blank traps; session and global temp views; `%sql`/`spark.sql` | Module 1 | Core API fluency used in every notebook | Forms the DataFrame layer reused throughout | Complete |
| 3 | Data Cleaning, NULL Semantics, and Type Handling | Fix imperfect values and write NULL-aware predicates on hand-built rideshare DataFrames — before file-based ingestion | Three-valued logic and NULL-safe predicates (`isin` trap, `eqNullSafe`); missing/blank/sentinel/`NaN` and normalize-first; `na.drop`/`fill`/`replace` and `F.coalesce`; `cast`/`try_cast` and rejected-row detection; numeric overflow; date/timestamp parsing (Spark 4 / ANSI `try_*`) | Module 2 | Correctness in filters, comparisons, and in-memory cleaning transforms | Reusable NULL-safe predicates and cleaning patterns for later joins and aggregations | Complete |
| 4 | Transformations, Actions, and Lazy Evaluation | Understand Spark's lazy execution model on chains learners already write — plans run on actions; the optimizer can rewrite; narrow vs wide (shuffle) | Transformations vs actions; lazy evaluation and the query plan; narrow vs wide / `Exchange`; common actions and driver-memory risk | Modules 2–3 | Builds performance-aware coding habits early | Shapes how pipeline logic is written efficiently | Complete |

## Phase II — Core Data Engineering Skills (Modules 5–9)

Land files, transform data, build analytical tables and KPIs, and re-express
the pipeline in Spark SQL.

| # | Module | Purpose | Major Topics | Prerequisites | Production Relevance | Final-Project Contribution | Status |
|---|---|---|---|---|---|---|---|
| 5 | Reading, Writing, and Schemas | Land the shared rideshare dataset on UC Volumes and read/write production formats with explicit schemas | UC Volumes and data landing (including controlled-bad sources); CSV/JSON/Parquet/XML/Avro reads; explicit schemas vs inference; write modes; Delta file write and managed `saveAsTable` preview | Module 4; [additional environment and privilege requirements](05%20-%20Reading%2C%20Writing%2C%20and%20Schemas/README.md#before-notebook-01) | Volume-based file I/O patterns used in real ingestion jobs | Lands raw files for the Phase II learning pipeline. The production medallion lands its own copy in Module 13. | Complete |
| 6 | Built-in Functions, Complex Types, and UDF Alternatives | Transform landing data with Spark built-ins, work with nested types, and write curated outputs — prefer built-ins over UDFs | Built-in `F.*` transforms; Volume path vs managed table; structs/arrays/`explode`; cleaned `curated/` outputs; built-in vs Python UDF (Pandas/Arrow note only) | Module 5 | Performant, idiomatic transformation logic | Teaches cleaning and enrichment patterns later reused in Silver. | Complete |
| 7 | Joins and Set Operations | Join and combine rideshare tables with predictable row counts and clear keys — no silent cardinality or key traps | Grain and cardinality; join types and silent failures; lookup joins, column cleanup, broadcast; semi/anti; set operations; read Module 6 `curated/` / write managed tables (`trip_enriched`, `trip_driver_assignment`); high-level AQE awareness | Module 6 | Multi-table integration — a core production pattern | Builds teaching managed tables. Production tables are rebuilt in Gold. | Complete |
| 8 | Aggregations and Window Functions | Produce analytics-ready summaries and KPI tables | `groupBy` and aggregates (collections, percentiles, distinct counts); pivot; window functions (ranking, running totals, lag/lead); Top-N per group; sampling; managed Delta `kpi_*` tables (`saveAsTable`) | Module 7 | Analytics and reporting layers | Produces teaching KPI tables later rebuilt as Gold. | Complete |
| 9 | Spark SQL and DataFrame Interoperability | Re-express DataFrame-based rideshare analytics in Spark SQL and choose deliberate SQL–DataFrame interoperability patterns | Dual-API entry points; SQL joins and aggregations; `PIVOT`, `UNPIVOT`, and `TABLESAMPLE`; windows and `QUALIFY`; CTEs and named parameters; rebuilds Module 8 KPI outputs in Spark SQL from Module 7 managed tables | Module 8 | Supports SQL-first collaboration and dual-API validation | Enables SQL-based transforms and cross-API validation | Complete |

## Phase III — Lakehouse Design and Implementation (Modules 10–13)

Deepen Delta and governance knowledge, design the medallion architecture, and
build its full-refresh implementation.

| # | Module | Purpose | Major Topics | Prerequisites | Production Relevance | Final-Project Contribution | Status |
|---|---|---|---|---|---|---|---|
| 10 | Delta Lake for Managed Tables | Deepen Delta Lake knowledge on managed tables learners already use | Delta transaction log and ACID semantics; history and time travel; schema evolution; maintenance basics; introductory `MERGE` syntax | Module 9 | Lakehouse storage foundation for all later modules | Applies Delta operations to existing project tables | Not Started |
| 11 | Unity Catalog and Data Governance | Govern existing Module 5–9 `landing` / `processed` assets with least privilege | Managed vs external objects; grants and privileges; ownership; storage credentials; minimum-privilege design; future medallion schemas will need their own roles | Module 10 | Governance compliance — required in any real Databricks environment | Applies least-privilege governance to existing Unity Catalog assets | Not Started |
| 12 | Medallion Architecture and Layer Design | Paper-design the medallion architecture without creating lakehouse objects | Layer rules and quality boundaries; schema names; new medallion landing location; source-to-target mapping; no `CREATE SCHEMA` and no tables; Module 5 `landing` / `processed` objects are not medallion layers | Module 11 | The standard lakehouse architecture pattern | Documents the project's medallion design | Not Started |
| 13 | Build the Full-Refresh Medallion Pipeline | Create `rideshare_dev.bronze`, `.silver`, and `.gold` and land a fresh copy of the raw files | New medallion landing volume; copy repo `data/raw` there; first grants on the new schemas; full-refresh managed Delta tables; introduce `src/`; do not use Module 5 `landing` / `processed` objects, curated folders, or teaching tables | Module 12 | First production-shaped lakehouse implementation | Creates the production medallion and reusable package | Not Started |

## Phase IV — Reliable Batch Pipelines (Modules 14–15)

Make the medallion pipeline incremental and reliable, then express it as a
required batch Lakeflow Pipeline.

| # | Module | Purpose | Major Topics | Prerequisites | Production Relevance | Final-Project Contribution | Status |
|---|---|---|---|---|---|---|---|
| 14 | Reliable Batch Ingestion and Incremental Processing | Make the Module 13 pipeline incremental and resilient | Production `MERGE` upserts; idempotency; deduplication; late-arriving data; backfills; batch state; quarantine | Module 13 | Ingestion reliability — a core production concern | Implements the project's incremental load logic | Not Started |
| 15 | Lakeflow Declarative Pipelines for Batch | Re-express the required Bronze→Silver→Gold flow as a batch Lakeflow Pipeline | Lakeflow Pipelines on pipeline-managed compute; materialized views (batch only); no streaming or Auto Loader | Module 14 | A managed orchestration option for batch workloads | Required declarative pipeline variant of the project | Not Started |

## Phase V — Quality, Delivery, and Operations (Modules 16–20)

Test, tune, deploy, operate, and integrate the complete production pipeline.

| # | Module | Purpose | Major Topics | Prerequisites | Production Relevance | Final-Project Contribution | Status |
|---|---|---|---|---|---|---|---|
| 16 | Testing, Data Quality, and Code Quality | Build confidence in pipeline correctness | `pytest` for pure Python helpers; Databricks-based data-quality checks; linting/typing gates | Module 15 | Reliability and maintainability | Adds the project's test suite and quality gates | Not Started |
| 17 | Performance and Spark Internals | Tune the tested pipeline through plan analysis and Spark internals | Partitioning; shuffles; AQE tuning and plan analysis beyond Module 7 awareness; caching; Photon awareness | Module 16 | Cost and performance tuning | Applies an optimization pass to the project | Not Started |
| 18 | Lakeflow Jobs, Packaging, and Deployment | Package `src/` and deploy the required pipeline plus quality tasks | Lakeflow Jobs; job tasks; create `databricks.yml` from scratch; package `src/` | Module 17 | Deployment and CI/CD foundation | Produces the project's deployable job definition | Not Started |
| 19 | Observability and Production Operations | Operate batch pipelines in production | Structured logging; monitoring; alerts; run-history triage; operational runbooks | Module 18 | Operational readiness | Adds monitoring/alerting to the project | Not Started |
| 20 | End-to-End Deployable Batch Project | Integrate Modules 1–19 into one deployable batch project — no new major APIs | Capstone integration of all prior modules | Module 19 | This module *is* the production capstone | The final project itself | Not Started |
