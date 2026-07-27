# Course Modules

Canonical owner of the full course roadmap: module numbers and titles, purpose,
major topics, prerequisites, production relevance, contribution to the final
project, and planning status.

This file does **not** contain notebook sequences, exercises, or code. Detailed
design for the current module lives in that module's own `README.md`. Future
modules stay at the roadmap level shown here until they become current.

Status updates in this file are author-owned (manual edit or chat-assisted
draft). No Cursor slash command writes to this file automatically.

## Status legend

| Status | Meaning |
|---|---|
| Not Started | Roadmap entry only — no folder, no notebooks yet |
| Current | Actively being authored — see its `README.md` for detailed design |
| Complete | Notebooks written, authoring-quality checked, and runtime-validated in Azure Databricks (see `docs/validation/`) |

## The running use case

Every module threads through the same small rideshare dataset — `trip`,
`trip_time`, `payment`, and `zone_lookup` — so each topic builds on the same
data instead of switching examples. Full schema, join keys, and file layout:
[`docs/data/dataset-overview.md`](docs/data/dataset-overview.md).

---

## Phase I — Language and Engine Foundations (Modules 1–4)

| # | Module | Purpose | Major Topics | Prerequisites | Production Relevance | Final-Project Contribution | Status |
|---|---|---|---|---|---|---|---|
| 1 | Azure Databricks and Spark Foundations | Get oriented in the Azure Databricks workspace and understand how Spark executes work | Spark architecture (driver/executor), compute types and access modes, notebooks, `SparkSession` | — | Compute and platform literacy every later module depends on | Establishes the environment the final project runs in | Complete |
| 2 | DataFrame Fundamentals | Build core DataFrame fluency: create, inspect, reshape, express, filter, and query | Creating/inspecting DataFrames, `select`/`withColumn`/`withColumns`, `F.col`/`F.when`/`F.lit`, `F.expr`/`selectExpr`, `filter`/`where`, intro NULL/blank traps, session and global temp views, `%sql`/`spark.sql` | Module 1 | Core API fluency used in every notebook | Forms the DataFrame layer reused throughout | Complete |
| 3 | Data Cleaning, NULL Semantics, and Type Handling | Fix imperfect values and write NULL-aware predicates on hand-built rideshare DataFrames — before file-based ingestion | Missing/blank/sentinel/`NaN` and normalize-first; `na.drop`/`fill`/`replace` and `F.coalesce`; three-valued logic and NULL-safe predicates (`isin` trap, `eqNullSafe`); `cast`/`try_cast` and rejected-row detection; numeric overflow; date/timestamp parsing (Spark 4 / ANSI `try_*`) | Module 2 | Correctness in filters, comparisons, and in-memory cleaning transforms | Reusable NULL-safe predicates and cleaning patterns for later joins and aggregations | Complete |
| 4 | Transformations, Actions, and Lazy Evaluation | Understand Spark's lazy execution model on chains learners already write | Transformations vs. actions, the query plan, narrow vs. wide operations | Modules 2–3 | Builds performance-aware coding habits early | Shapes how pipeline logic is written efficiently | Current |

## Phase II — Core Data Engineering Skills (Modules 5–9)

| # | Module | Purpose | Major Topics | Prerequisites | Production Relevance | Final-Project Contribution | Status |
|---|---|---|---|---|---|---|---|
| 5 | Reading, Writing, and Schemas | Read and write the file formats used in production ingestion | CSV/JSON/Avro/XML/Parquet readers and writers, explicit schemas vs. `inferSchema` | Module 4 | File-based I/O patterns used in real ingestion jobs | Builds the ingestion layer for the final project | Not Started |
| 6 | Built-in Functions, Complex Types, and UDF Alternatives | Write performant transformations without reaching for UDFs first | `pyspark.sql.functions`, structs/arrays/maps, when (not) to use UDFs | Module 5 | Performant, idiomatic transformation logic | Implements business-logic transforms | Not Started |
| 7 | Joins and Set Operations | Combine the rideshare tables correctly | Join types, broadcast joins, union/intersect, join key pitfalls | Module 6 | Multi-table integration, a core production pattern | Combines `trip`/`payment`/`zone_lookup` into unified views | Not Started |
| 8 | Aggregations and Window Functions | Produce analytics-ready summaries | `groupBy`, window specifications, ranking, running totals | Module 7 | Analytics and reporting layers | Produces KPI/metric tables for the project | Not Started |
| 9 | Spark SQL and DataFrame Interoperability | Deepen SQL ↔ DataFrame fluency for team and pipeline workflows | When to prefer SQL vs. DataFrame code, richer SQL/DataFrame interop (builds on Module 2 temp views / `spark.sql`) | Module 8 | Supports SQL-first team collaboration | Enables SQL-based transforms and tests | Not Started |

## Phase III — Lakehouse and Governance (Modules 10–12)

| # | Module | Purpose | Major Topics | Prerequisites | Production Relevance | Final-Project Contribution | Status |
|---|---|---|---|---|---|---|---|
| 10 | Delta Lake | Adopt Delta Lake as the storage foundation | ACID tables, time travel, `MERGE`, schema evolution basics | Module 9 | Lakehouse storage foundation for all later modules | Backs the project's tables with Delta | Not Started |
| 11 | Unity Catalog and Governed Data | Work within a governed data platform | Catalogs, schemas, managed/external tables, volumes, grants, minimum-privilege documentation | Module 10 | Governance compliance — required in any real Databricks environment | Produces UC-governed data assets | Not Started |
| 12 | Lakehouse and Medallion Architecture | Structure a pipeline using the medallion pattern | Bronze/silver/gold layering, layered pipeline design | Module 11 | The standard lakehouse architecture pattern | Establishes the project's medallion structure | Not Started |

## Phase IV — Production Batch Engineering (Modules 13–15)

| # | Module | Purpose | Major Topics | Prerequisites | Production Relevance | Final-Project Contribution | Status |
|---|---|---|---|---|---|---|---|
| 13 | Reliable Batch Ingestion and Incremental Processing | Make batch ingestion idempotent and resilient | Idempotency, `MERGE`-based upserts, deduplication, late-arriving data, backfills, quarantine patterns | Module 12 | Ingestion reliability — a core production concern | Implements the project's incremental load logic | Not Started |
| 14 | Lakeflow Pipelines for Batch Processing | Explore declarative batch pipelines | Lakeflow Pipelines concepts, materialized views (batch only) | Module 13 | A managed orchestration option for batch workloads | Offers an optional pipeline-based variant of the project | Not Started |
| 15 | Lakeflow Jobs, Packaging, and Deployment | Package and deploy batch workloads | Lakeflow Jobs, job tasks, Databricks Asset Bundles (`databricks.yml`) | Module 13 (Module 14 optional) | Deployment and CI/CD foundation | Produces the project's deployable job definition | Not Started |

## Phase V — Excellence and Delivery (Modules 16–19)

| # | Module | Purpose | Major Topics | Prerequisites | Production Relevance | Final-Project Contribution | Status |
|---|---|---|---|---|---|---|---|
| 16 | Performance and Spark Internals | Understand and tune Spark performance | Partitioning, shuffles, adaptive query execution, caching, Photon awareness | Module 15 | Cost and performance tuning | Applies an optimization pass to the project | Not Started |
| 17 | Testing, Data Quality, and Code Quality | Build confidence in pipeline correctness | `pytest` for PySpark logic, data-quality checks, linting/typing gates | Module 16 | Reliability and maintainability | Adds the project's test suite and quality gates | Not Started |
| 18 | Observability and Production Operations | Operate batch pipelines in production | Logging, job monitoring and alerts, run history, troubleshooting | Module 17 | Operational readiness | Adds monitoring/alerting to the project | Not Started |
| 19 | End-to-End Deployable Batch Project | Integrate everything into one deployable pipeline | Capstone integration of all prior modules | Modules 1–18 | This module *is* the production capstone | The final project itself | Not Started |
