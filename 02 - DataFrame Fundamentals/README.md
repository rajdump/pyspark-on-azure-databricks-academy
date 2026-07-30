# Module 2 — DataFrame Fundamentals

## Purpose

Build core DataFrame fluency: create and inspect DataFrames, reshape
columns with the DataFrame API and SQL expression strings, filter rows
(including intro NULL and blank traps), and query the same data through
temporary views and Spark SQL. This is the API layer every later notebook
reuses.

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
- Select, add, rename, recalculate, and drop columns with the DataFrame API
  (`select`, `withColumn` / `withColumns`, rename helpers, `drop`)
- Build Column expressions with `F.col`, `alias`, light `cast`, `F.lit`, and
  `F.when` / `otherwise`
- Express the same column logic as SQL strings with `F.expr` and `selectExpr`
  (including `CASE WHEN`), and choose the clearer form for related rules
- Filter rows with `filter` / `where` using Column operators and SQL
  predicate strings; use intro NULL checks (`isNull` / `isNotNull`) and
  treat empty strings as distinct from NULL
- Give a DataFrame a SQL name with a session temporary view; query it with
  `%sql` and `spark.sql`; recognize global temporary views on classic compute
- Prefer clear, chained transforms that keep the original DataFrame
  unchanged until you assign a new one

## Prerequisites

Module 1 — Azure Databricks and Spark Foundations. You should already be
able to attach compute, use notebook cells, and create a small DataFrame
with `spark.createDataFrame(rows, columns)` plus basic `show` / `display` /
`printSchema`.

## Notebook navigation

Six notebooks, in this order:

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
   - Structure: `printSchema`, `schema`, `columns`, `dtypes`
   - Size / emptiness: `count`, `isEmpty`
   - Summary stats: `describe` and `summary` for a first-pass review
   - Performance note: metadata checks vs methods that execute Spark work
3. **Selecting and Transforming Columns**
   - `select` to project and reorder columns; DataFrame immutability
   - Column-name strings vs `F.col` when you need an expression
   - `alias`, simple arithmetic, light `cast`, `F.lit`
   - Conditional columns with `F.when` / `otherwise`
   - Add or replace columns with `withColumn`; several at once with
     `withColumns`
   - Rename with `withColumnRenamed` / `withColumnsRenamed`; remove with
     `drop`
   - Choose `select` vs `withColumn` when adding vs recalculating a column
   - Chain transforms into a small operations-style output
4. **SQL Expressions in DataFrame Code**
   - Build a Column from a SQL string with `F.expr`
   - Apply several SQL strings with `selectExpr`
   - Conditional logic with SQL `CASE WHEN` (same idea as `F.when`)
   - Compare misspelled column names (`AnalysisException`) across styles
   - Python `SyntaxError` vs Spark SQL parse errors on bad expression strings
   - Choose the clearer form; store and reuse related rules consistently
5. **Filtering Rows**
   - `filter` / `where` (alias); one-condition filters
   - Combine conditions: SQL `AND` in strings vs Column `&` (with
     parentheses); why Python `and` fails
   - `|`, `~`, `isin`, `between`, `like`
   - Intro NULL: `isNull` / `isNotNull`; why `== None` does not find NULLs
   - Empty string is not NULL (check separately)
   - Deeper NULL semantics and quality pipelines stay for Module 3
6. **Querying DataFrames with SQL**
   - Short compare: same calculated column via `F.when`, `F.expr`, and
     `selectExpr`
   - Why a `%sql` cell cannot see a Python DataFrame variable
   - Session temporary views (`createOrReplaceTempView`)
   - Query with `%sql` and with `spark.sql(...)`; continue from the
     DataFrame `spark.sql` returns
   - Global temporary views (`global_temp`) — recognize in existing code;
     classic compute only / not on serverless
   - Session view vs global view vs a persisted table (tables come later)

## Dataset used

This module uses small, **ad-hoc** rideshare-flavored DataFrames (built by
hand in code), aligned with column names and types from
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).
Volume-based file reading begins in Module 5.

## Exercises

Each notebook ends with a short hands-on task that repeats the notebook's
pattern on a slightly different rideshare DataFrame — for example, defining
an explicit schema, inspecting with `columns`/`dtypes`, projecting and
adding a derived column, filtering with a reusable condition, or querying a
temp view. Module 2 **`01 - Creating DataFrames`** includes one
medium-difficulty exercise on inferred vs explicit schema inspection.

## Minimum privileges required

- Databricks workspace: ability to attach to or start compute
  (`CAN ATTACH TO` or `CAN RESTART` on the cluster/policy your workspace
  provides for this course)
- Unity Catalog: none — this module doesn't read or write governed data
- Global temporary view demo in Module 2 **`06 - Querying DataFrames with
  SQL`**: classic all-purpose compute; not available on serverless
