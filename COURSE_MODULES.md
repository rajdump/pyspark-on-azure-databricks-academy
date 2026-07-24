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

## Phase I — Language and Engine Foundations (Modules 1–5)

| # | Module | Purpose | Major Topics | Prerequisites | Production Relevance | Final-Project Contribution | Status |
|---|---|---|---|---|---|---|---|
| 1 | Azure Databricks and Spark Foundations | Get oriented in the Azure Databricks workspace and understand how Spark executes work | Spark architecture (driver/executor), compute types and access modes, notebooks, `SparkSession` | — | Compute and platform literacy every later module depends on | Establishes the environment the final project runs in | Current |
| 2 | DataFrame Fundamentals | Build and inspect DataFrames | Creating DataFrames, schemas, `select`/`withColumn`, inspecting structure | Module 1 | Core API fluency used in every notebook | Forms the DataFrame layer reused throughout | Not Started |
| 3 | Transformations, Actions, and Lazy Evaluation | Understand Spark's lazy execution model | Transformations vs. actions, the query plan, narrow vs. wide operations | Module 2 | Builds performance-aware coding habits early | Shapes how pipeline logic is written efficiently | Not Started |
| 4 | Column Expressions, Filtering, and NULL Semantics | Filter and reason about data correctly, including NULLs | Column expressions, `filter`/`where`, NULL semantics, SQL expressions in DataFrame code | Modules 2–3 | Correctness in data-quality-sensitive logic | Provides the filtering/cleaning logic used downstream | Not Started |
| 5 | Data Cleaning and Type Handling | Handle messy, real-world data | Missing/blank/sentinel values, type casting, numeric overflow, date/timestamp parsing | Module 4 | Robust ingestion preparation | Produces the raw-to-clean transforms the project depends on | Not Started |

## Phase II — Core Data Engineering Skills (Modules 6–10)

| # | Module | Purpose | Major Topics | Prerequisites | Production Relevance | Final-Project Contribution | Status |
|---|---|---|---|---|---|---|---|
| 6 | Reading, Writing, and Schemas | Read and write the file formats used in production ingestion | CSV/JSON/Avro/XML/Parquet readers and writers, explicit schemas vs. `inferSchema` | Module 5 | File-based I/O patterns used in real ingestion jobs | Builds the ingestion layer for the final project | Not Started |
| 7 | Built-in Functions, Complex Types, and UDF Alternatives | Write performant transformations without reaching for UDFs first | `pyspark.sql.functions`, structs/arrays/maps, when (not) to use UDFs | Module 6 | Performant, idiomatic transformation logic | Implements business-logic transforms | Not Started |
| 8 | Joins and Set Operations | Combine the rideshare tables correctly | Join types, broadcast joins, union/intersect, join key pitfalls | Module 7 | Multi-table integration, a core production pattern | Combines `trip`/`payment`/`zone_lookup` into unified views | Not Started |
| 9 | Aggregations and Window Functions | Produce analytics-ready summaries | `groupBy`, window specifications, ranking, running totals | Module 8 | Analytics and reporting layers | Produces KPI/metric tables for the project | Not Started |
| 10 | Spark SQL and DataFrame Interoperability | Move fluently between SQL and the DataFrame API | Temporary views, `spark.sql()`, when to prefer SQL vs. DataFrame code | Module 9 | Supports SQL-first team collaboration | Enables SQL-based transforms and tests | Not Started |

## Phase III — Lakehouse and Governance (Modules 11–13)

| # | Module | Purpose | Major Topics | Prerequisites | Production Relevance | Final-Project Contribution | Status |
|---|---|---|---|---|---|---|---|
| 11 | Delta Lake | Adopt Delta Lake as the storage foundation | ACID tables, time travel, `MERGE`, schema evolution basics | Module 10 | Lakehouse storage foundation for all later modules | Backs the project's tables with Delta | Not Started |
| 12 | Unity Catalog and Governed Data | Work within a governed data platform | Catalogs, schemas, managed/external tables, volumes, grants, minimum-privilege documentation | Module 11 | Governance compliance — required in any real Databricks environment | Produces UC-governed data assets | Not Started |
| 13 | Lakehouse and Medallion Architecture | Structure a pipeline using the medallion pattern | Bronze/silver/gold layering, layered pipeline design | Module 12 | The standard lakehouse architecture pattern | Establishes the project's medallion structure | Not Started |

## Phase IV — Production Batch Engineering (Modules 14–16)

| # | Module | Purpose | Major Topics | Prerequisites | Production Relevance | Final-Project Contribution | Status |
|---|---|---|---|---|---|---|---|
| 14 | Reliable Batch Ingestion and Incremental Processing | Make batch ingestion idempotent and resilient | Idempotency, `MERGE`-based upserts, deduplication, late-arriving data, backfills, quarantine patterns | Module 13 | Ingestion reliability — a core production concern | Implements the project's incremental load logic | Not Started |
| 15 | Lakeflow Pipelines for Batch Processing | Explore declarative batch pipelines | Lakeflow Pipelines concepts, materialized views (batch only) | Module 14 | A managed orchestration option for batch workloads | Offers an optional pipeline-based variant of the project | Not Started |
| 16 | Lakeflow Jobs, Packaging, and Deployment | Package and deploy batch workloads | Lakeflow Jobs, job tasks, Databricks Asset Bundles (`databricks.yml`) | Module 14 (Module 15 optional) | Deployment and CI/CD foundation | Produces the project's deployable job definition | Not Started |

## Phase V — Excellence and Delivery (Modules 17–20)

| # | Module | Purpose | Major Topics | Prerequisites | Production Relevance | Final-Project Contribution | Status |
|---|---|---|---|---|---|---|---|
| 17 | Performance and Spark Internals | Understand and tune Spark performance | Partitioning, shuffles, adaptive query execution, caching, Photon awareness | Module 16 | Cost and performance tuning | Applies an optimization pass to the project | Not Started |
| 18 | Testing, Data Quality, and Code Quality | Build confidence in pipeline correctness | `pytest` for PySpark logic, data-quality checks, linting/typing gates | Module 17 | Reliability and maintainability | Adds the project's test suite and quality gates | Not Started |
| 19 | Observability and Production Operations | Operate batch pipelines in production | Logging, job monitoring and alerts, run history, troubleshooting | Module 18 | Operational readiness | Adds monitoring/alerting to the project | Not Started |
| 20 | End-to-End Deployable Batch Project | Integrate everything into one deployable pipeline | Capstone integration of all prior modules | Modules 1–19 | This module *is* the production capstone | The final project itself | Not Started |
