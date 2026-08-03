# Module 2 — DataFrame Fundamentals

## Purpose

Build core DataFrame fluency: create, inspect, reshape, express, filter, and
query through temp views and Spark SQL. Reshape uses the DataFrame API and SQL
expression strings; filtering includes intro NULL and blank traps. This is the
API layer every later notebook reuses.

## Learning objectives

By the end of this module, you'll be able to:

- Explain what a Spark DataFrame is: distributed rows plus named, typed
  columns and schema metadata
- Create DataFrames from Python rows four ways: unnamed/inferred,
  named/inferred, named with DDL, named with `StructType`
- Explain why inferred schemas are convenient for demos but risky in production
- Inspect beyond a first look (`show`, `display`, `printSchema`, `columns`,
  `dtypes`, `count`, summary stats)
- Select, add, rename, recalculate, and drop columns (`select`, `withColumn` /
  `withColumns`, `withColumnRenamed` / `withColumnsRenamed`, `drop`)
- Build Column expressions with `F.col`, `alias`, light `cast`, `F.lit`, and
  `F.when` / `otherwise`
- Express the same logic as SQL strings with `F.expr` and `selectExpr`
  (including `CASE WHEN`) and choose the clearer form
- Filter with `filter` / `where` (Column ops and SQL strings); intro NULL
  checks (`isNull` / `isNotNull`); empty string ≠ NULL
- Register a session temporary view with `createOrReplaceTempView`; query with
  `%sql` and `spark.sql`; recognize global temporary views on classic compute
- Prefer clear chained transforms that leave the original frame unchanged
  until you assign a new one

## Prerequisites

Module 1 — Azure Databricks and Spark Foundations. You should already attach
compute, use notebook cells, and create a small DataFrame with
`spark.createDataFrame(rows, columns)` plus basic `show` / `display` /
`printSchema`.

## Dataset

Small **ad-hoc** rideshare-flavored DataFrames built in code, aligned with
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md). Volume
file reading starts in Module 5.

## Notebooks

Six notebooks, in order. Each ends with a short hands-on task on a slightly
different rideshare DataFrame. **`01 - Creating DataFrames`** includes one
medium exercise on inferred vs explicit schema inspection.

| # | Notebook | Focus |
|---|---|---|
| 1 | Creating DataFrames | What a DataFrame is; create without columns/schema (`_1`, `_2`, …); named + inferred; DDL; `StructType`; inspect each path; inferred vs production risk; keep examples tiny (2–3 rows) |
| 2 | Inspecting DataFrames | Contents: `show` options (`n`, `truncate`, `vertical`) / `display`; structure: `printSchema`, `schema`, `columns`, `dtypes`; size: `count`, `isEmpty`; `describe` / `summary`; metadata checks vs methods that run Spark work |
| 3 | Selecting and Transforming Columns | `select` / immutability; name strings vs `F.col`; `alias`, arithmetic, light `cast`, `F.lit`; `F.when` / `otherwise`; `withColumn` / `withColumns`; `withColumnRenamed` / `withColumnsRenamed` / `drop`; when to use `select` vs `withColumn`; chain into a small ops-style output |
| 4 | SQL Expressions in DataFrame Code | `F.expr`; `selectExpr`; SQL `CASE WHEN`; misspelled columns (`AnalysisException`) across styles; Python `SyntaxError` vs Spark SQL parse errors; choose and reuse related rules consistently |
| 5 | Filtering Rows | `filter` / `where`; combine with SQL `AND` vs Column `&` (parens); why Python `and` fails; `\|`, `~`, `isin`, `between`, `like`; intro NULL (`isNull` / `isNotNull`; `== None` fails); empty string ≠ NULL; deeper NULL → Module 3 |
| 6 | Querying DataFrames with SQL | Same calculated column via `F.when`, `F.expr`, `selectExpr`; why `%sql` cannot see a Python variable; session temp views (`createOrReplaceTempView`); `%sql` and `spark.sql`; global temp views (`global_temp`) — classic only / not serverless; session vs global vs persisted table |

## Minimum privileges required

- Workspace: **`CAN ATTACH TO`** (or **`CAN RESTART`**) on the compute used here
- Unity Catalog: none — this module does not read or write governed data
- Global temporary view demo (**`06 - Querying DataFrames with SQL`**): classic
  all-purpose compute; not available on serverless
