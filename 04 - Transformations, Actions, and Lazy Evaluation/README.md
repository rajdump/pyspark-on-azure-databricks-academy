# Module 4 — Transformations, Actions, and Lazy Evaluation

## Purpose

Understand Spark's lazy execution model on chains learners already write:
DataFrames build logical plans that run only when an action is called; the
optimizer can rewrite that plan (for example, applying a filter earlier); and
some transformations shuffle data between worker nodes while others do not.

## Learning objectives

By the end of this module, you'll be able to:

- Distinguish **transformations** (new DataFrame, build logical plan) from
  **actions** (execute the plan; return a result or trigger terminal writes
  such as **`.save()`** / **`.saveAsTable()`** via `DataFrameWriter`)
- Explain **lazy evaluation**: why Spark waits for an action
- Inspect logical and physical plans with **`.explain()`** and spot optimizer
  changes
- Differentiate **narrow** (no cross-partition move) from **wide**
  (requires a **shuffle**) transformations
- Identify **`Exchange`** in the physical plan as a shuffle / stage boundary
- Recognize common **shuffle triggers** such as `groupBy` and `orderBy`
- Choose common actions (`first`, `head`, `take`, `tail`, `isEmpty`,
  `toPandas`) and know their driver-side memory risks

## Prerequisites

Module 2 — DataFrame Fundamentals and Module 3 — Data Cleaning, NULL Semantics,
and Type Handling. Comfortable creating, inspecting, reshaping, expressing,
and filtering DataFrames (`select`, `withColumn`, `filter` / `where`, `F.col`,
`F.when`, `F.expr`, etc.).

## Dataset

Small **ad-hoc** rideshare-flavored DataFrames built in code, aligned with
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md). Volume
file reading starts in Module 5.

## Notebooks

Four notebooks, in order. Each ends with a short hands-on task (explain a
chain, inspect an optimized plan, predict shuffle, practice pull/check
actions).

| # | Notebook | Focus |
|---|---|---|
| 1 | Transformations vs Actions | Transformations vs actions; chain before one action — example 1 (`filter`, `withColumn`, `select`); example 2 (`filter`, `orderBy`, `limit`, `select`) |
| 2 | Lazy Evaluation and the Query Plan | Why Spark waits for an action; `.explain(mode="extended")`; optimizer can push a late filter earlier on one narrow chain |
| 3 | Narrow vs Wide Transformations | Prefer classic all-purpose (**Dedicated**) for partition/shuffle teaching — Standard/serverless may collapse this sample to one partition; inspect partition distribution; narrow `filter` (no `Exchange`, one stage); wide `groupBy` + `Exchange` + Spark UI; common shuffle triggers (deep tuning → Module 17) |
| 4 | Common DataFrame Actions | Return types and driver size risk (`show` / `count` / `collect` already known); sort then compare `first()` / `head()` / `head(n)` / `take(n)`; `tail(n)` (order not guaranteed unless sorted); `isEmpty()` vs `count() == 0`; `toPandas()` same driver risk as `collect()`; `DataFrame.write` → Module 5 |

## Minimum privileges required

- Workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the compute used here
- Unity Catalog: none — hand-built DataFrames only
