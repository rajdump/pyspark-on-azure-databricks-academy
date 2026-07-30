# Module 4 — Transformations, Actions, and Lazy Evaluation

## Purpose

Understand Spark's lazy execution model: how DataFrames build logical plans
that execute only when an action is called, how the Spark optimizer can reorder
your steps, and how different transformations may or may not require shuffling
data between worker nodes.

## Learning objectives

By the end of this module, you'll be able to:

- Distinguish between **transformations** (which return a new DataFrame and
  build a logical plan) and **actions** (which execute that plan and return a
  result or trigger terminal writes such as **`.save()`** /
  **`.saveAsTable()`** via `DataFrameWriter`)
- Explain **lazy evaluation**: why Spark waits for an action before executing
  a DataFrame's logical plan
- Inspect a DataFrame's logical and physical plans with **`.explain()`** and
  identify optimizer changes
- Differentiate **narrow transformations** (no data movement between
  partitions) from **wide transformations** (which require a **shuffle**)
- Identify **`Exchange`** in the physical plan as a shuffle / stage boundary
- Recognize common **shuffle triggers** such as `groupBy` and `orderBy`
- Choose common DataFrame **actions** (`first`, `head`, `take`, `tail`,
  `isEmpty`, `toPandas`) and be aware of their driver-side memory risks

## Prerequisites

Module 2 — DataFrame Fundamentals and Module 3 — Data Cleaning, NULL Semantics,
and Type Handling. You should already be comfortable creating, inspecting,
reshaping, expressing, and filtering DataFrames using various methods (e.g.,
`select`, `withColumn`, `filter`/`where`, `F.col`, `F.when`, `F.expr`).

## Notebook navigation

Four notebooks, in this order:

1. **Transformations vs Actions**
   - Distinguish transformations (new DataFrame, logical plan) from actions
     (executes plan, returns result)
   - Chain transformations before a single action — example 1
     (`filter`, `withColumn`, `select`)
   - Chain transformations before a single action — example 2
     (`filter`, `orderBy`, `limit`, `select`)
2. **Lazy Evaluation and the Query Plan**
   - Why Spark waits for an action before processing rows
   - Inspect the plan with `.explain(mode="extended")`
   - See how the optimizer can apply a late filter earlier on one narrow chain
3. **Narrow vs Wide Transformations**
   - Prefer classic all-purpose compute (**Dedicated** access mode) for the
     best partition / shuffle teaching experience — Standard and serverless
     run the notebook, but may collapse this hand-built sample into one
     partition
   - Inspect how rows are distributed across partitions
   - Run a narrow transformation (`filter`) and confirm it does not shuffle
     (no `Exchange`, one stage; rows stay in place)
   - Run a wide transformation (`groupBy`) and identify `Exchange` as the
     shuffle / stage boundary; confirm in Spark UI
   - Review common shuffle triggers (deep tuning deferred to Module 16)
4. **Common DataFrame Actions**
   - Review return types and driver-side size risk for common actions
     (`show` / `count` / `collect` already known; deepen the rest here)
   - Sort for predictable order, then compare `first()`, `head()`, `head(n)`,
     and `take(n)`
   - Retrieve the last rows with `tail(n)` (order is not guaranteed unless
     you sort)
   - Check emptiness with `isEmpty()` (prefer over `count() == 0` for a
     yes/no check)
   - Convert a small result with `toPandas()` and note the same driver-memory
     risk as `collect()`; writing with `DataFrame.write` waits for Module 5

## Dataset used

Small, **ad-hoc** rideshare-flavored DataFrames built in code, aligned with
column names and types from
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).
Volume-based file reading begins in Module 5.

## Exercises

Each notebook ends with a short hands-on task to reinforce the concepts —
for example, building and explaining a transformation chain, inspecting an
optimized plan, predicting shuffle behavior, or practicing pull/check
actions on a small sorted DataFrame.

## Minimum privileges required

- Databricks workspace: ability to attach to or start compute
  (`CAN ATTACH TO` or `CAN RESTART` on the cluster/policy your workspace
  provides for this course)
- Unity Catalog: none — this module uses hand-built DataFrames only
