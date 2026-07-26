# Module 1 — Azure Databricks and Spark Foundations

## Purpose

Get oriented in the Azure Databricks workspace and build a working mental
model of how Apache Spark executes code, before writing any real data
engineering logic.

## Learning objectives

By the end of this module, you'll be able to:

- Explain what Spark is and why it exists (unified engine, distributed
  processing), at a level useful for a data engineer — not a distributed
  systems deep dive
- Describe the driver/executor model and how a job breaks down into stages
  and tasks
- Navigate the Azure Databricks workspace: compute types and access modes,
  attaching a notebook to compute, and how Databricks Runtime/LTS
  versioning works
- Work inside a Databricks notebook: cells, magic commands, and `dbutils`
- Use the notebook's provided `SparkSession` (`spark`) and build your first
  DataFrame

## Prerequisites

None — this is the first module. Assumes the general audience baseline in
the root [`README.md`](../README.md#who-this-is-for): basic Python syntax,
basic SQL.

## Notebook navigation

Notebooks in this module, in order:

1. **Introduction to Azure Databricks and the Workspace**
   - Workspace browser, notebook editor, compute attach
   - Databricks Runtime / LTS (classic vs serverless DBR gotcha)
2. **Apache Spark Architecture and PySpark**
   - Why Spark distributes work; PySpark as Python talking to Spark
   - SparkSession (`spark`) as the entry point / connection
   - Driver, executors, cluster manager (Diagram A)
   - Jobs → stages → tasks (Diagram B)
   - Running story: count-trips stand-in via `spark.range(...).count()`
   - Spark UI on classic all-purpose Standard (no DataFrame labs yet)
3. **Working with Notebooks**
   - Cell run order and shared Python state
   - Each language keeps its own state (expected-fail `%sql` on a Python local)
   - Magic commands (`%md`, `%sql`, `%fs`, `%sh`)
   - `%fs` vs `dbutils.fs` (quick look vs Python result)
4. **Your First DataFrame**
   - Build a small rideshare DataFrame from Python rows (no explicit schema)
   - Inspect with `show` / `display` / `printSchema`
   - Note that `printSchema` shows Spark's default inferred schema — fine for
     demos, not recommended for production

## Dataset used

This module uses small, **ad-hoc** rideshare-flavored DataFrames (built by
hand in code, a few rows), not the file-based dataset in `data/raw/`.
File-based reading begins in Module 6. See
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md) for the
full dataset this course builds toward using.

## Exercises

Each notebook ends with a short hands-on task using the compute you've just
attached to — for example, running a provided cell and identifying its
job/stage/task breakdown in the Spark UI, or creating a small DataFrame of
your own and inspecting it with `.show()`/`display()`.

## Minimum privileges required

- Databricks workspace: ability to attach to or start compute
  (`CAN ATTACH TO` or `CAN RESTART` on the cluster/policy your workspace
  provides for this course)
- Unity Catalog: none — this module doesn't read or write governed data
