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
  result or write data)
- Explain **lazy evaluation**: why Spark waits for an action before executing
  a DataFrame's logical plan
- Inspect a DataFrame's logical and physical plans with **`.explain()`** and
  identify optimizer changes
- Differentiate **narrow transformations** (no data movement between
  partitions) from **wide transformations** (which require a **shuffle**)
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
   - Classify common APIs as transformations or actions
   - Chain transformations before a single action
2. **Lazy Evaluation and the Query Plan**
   - Explain why Spark waits for an action (`show`, `count`, `write`)
   - Inspect query plans with `.explain()`
   - Understand how the Spark optimizer reorders transformations
3. **Narrow vs Wide Transformations**
   - Compare narrow transformations (local to partition) and wide transformations
     (require a shuffle)
   - Identify `Exchange` in the physical plan as a shuffle boundary
   - Recognize common shuffle triggers and their performance implications
4. **Common DataFrame Actions**
   - Use `first()`, `head()`, `take()`, `tail()`, `isEmpty()`, and `toPandas()`
   - Understand the driver-side memory risks of actions that return many rows

## Dataset used

Small, **ad-hoc** rideshare-flavored DataFrames built in code, aligned with
column names and types from
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).
File-based reading begins in Module 5.

## Exercises

Each notebook ends with a short hands-on task to reinforce the concepts —
for example, building and explaining a transformation chain, inspecting an
optimized plan, or predicting shuffle behavior.

## Minimum privileges required

- Databricks workspace: ability to attach to or start compute
  (`CAN ATTACH TO` or `CAN RESTART` on the cluster/policy your workspace
  provides for this course)
- Unity Catalog: none — this module uses hand-built DataFrames only
