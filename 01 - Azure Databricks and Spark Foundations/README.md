# Module 1 — Azure Databricks and Spark Foundations

## Purpose

Orient in the Azure Databricks workspace and build a mental model of how
Apache Spark runs code — before real data-engineering logic.

## Learning objectives

By the end of this module, you'll be able to:

- Explain what Spark is and why it exists (unified engine, distributed
  processing) at a data-engineer level — not a distributed-systems deep dive
- Describe the driver/executor model and how a job breaks into stages and tasks
- Navigate the workspace: compute types and access modes, attach a notebook,
  Databricks Runtime / LTS versioning
- Work in a notebook: cells, magic commands, `dbutils`
- Use the provided `SparkSession` (`spark`) and build a first DataFrame

## Prerequisites

None — first module. Assumes the audience baseline in
[`README.md`](../README.md#who-this-is-for): basic Python, basic SQL.

## Dataset

Small **ad-hoc** rideshare-flavored DataFrames built in code (a few rows), not
`data/raw/`. Volume file reading starts in Module 5. Full course dataset:
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).

## Notebooks

Four notebooks, in order. Each ends with a short hands-on task on the compute
you just attached (e.g. Spark UI job/stage/task, or a tiny DataFrame inspect).

| # | Notebook | Focus |
|---|---|---|
| 1 | Introduction to Azure Databricks and the Workspace | Workspace browser, notebook editor, compute attach; DBR / LTS (classic vs serverless gotcha) |
| 2 | Apache Spark Architecture and PySpark | Why Spark distributes work; PySpark ↔ Spark; `SparkSession`; driver/executors (Diagram A); jobs → stages → tasks (Diagram B); `spark.range(...).count()` stand-in; Spark UI on classic all-purpose Standard |
| 3 | Working with Notebooks | Cell run order and shared Python state; languages keep separate state; magics (`%md`, `%sql`, `%fs`, `%sh`); `%fs` vs `dbutils.fs` |
| 4 | Your First DataFrame | Small rideshare DataFrame from Python rows (no explicit schema); `show` / `display` / `printSchema`; inferred schema fine for demos, not for production |

## Minimum privileges required

- Workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the compute used here
- Unity Catalog: none — this module does not read or write governed data
