# Module 2 — DataFrame Fundamentals

## Purpose

Build core DataFrame fluency: create DataFrames with intentional schemas,
inspect contents and structure, and reshape columns with `select` /
`withColumn`. This is the API layer every later notebook reuses.

## Learning objectives

By the end of this module, you'll be able to:

- Explain what a Spark DataFrame represents: distributed rows plus named,
  typed columns and schema metadata
- Create DataFrames from Python rows in four ways: unnamed/inferred, named/
  inferred, named with DDL schema, and named with `StructType`
- Explain why inferred schemas are convenient for demos but risky for
  production data models
- Inspect DataFrame contents and structure beyond a first look (`show`,
  `display`, `printSchema`, `columns`, `dtypes`, `count`, and summary stats)
- Select, add, rename, and drop columns with the DataFrame API
- Prefer clear, column-focused transforms that keep the original DataFrame
  unchanged until you assign a new one

## Prerequisites

Module 1 — Azure Databricks and Spark Foundations. You should already be
able to attach compute, use notebook cells, and create a small DataFrame
with `spark.createDataFrame(rows, columns)` plus basic `show` / `display` /
`printSchema`.

## Notebook navigation

Notebooks are added to this module using `/new-lesson` as they're authored,
in this planned order:

1. **Creating DataFrames**
   - What a Spark DataFrame represents (technical foundation)
   - Create from rows without columns and without schema (`_1`, `_2`, ...)
   - Create from rows with column names and inferred types
   - Create from rows with an explicit DDL schema
   - Create from rows with an explicit `StructType` schema
   - For each path: inspect with `printSchema()` and row output
   - Inferred schema convenience vs production risk (types and nullability)
   - Keep examples intentionally tiny (2-3 rows) for concept focus
2. **Inspecting DataFrames**
   - Contents: `show` options (`n`, `truncate`, `vertical`) and `display`
   - Structure: `printSchema`, `columns`, `dtypes`
   - Size: `count`
   - Summary stats: `describe` and `summary` for a first-pass review
3. **Selecting and Transforming Columns**
   - `select` to project and reorder columns
   - Column expressions with `F.col` (and simple `alias` / `cast` / `lit`
     as needed for demos)
   - Add or replace columns with `withColumn`
   - Rename and drop columns
   - Chain transforms; remember each call returns a new DataFrame

This list will be updated as notebooks are actually created — it reflects
current planning, not a promise of final content.

## Dataset used

This module uses small, **ad-hoc** rideshare-flavored DataFrames (built by
hand in code), aligned with column names and types from
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).
File-based reading begins in Module 6.

## Exercises

Each notebook ends with a short hands-on task that repeats the notebook's
pattern on a slightly different rideshare DataFrame — for example, defining
an explicit schema, inspecting with `columns`/`dtypes`, or projecting and
adding a derived column. Notebook 1 includes one medium-difficulty exercise
on inferred vs explicit schema inspection.

## Minimum privileges required

- Databricks workspace: ability to attach to or start compute
  (`CAN ATTACH TO` or `CAN RESTART` on the cluster/policy your workspace
  provides for this course)
- Unity Catalog: none — this module doesn't read or write governed data
