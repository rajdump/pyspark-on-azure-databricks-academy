# Module 3 — Data Cleaning, NULL Semantics, and Type Handling

## Purpose

Fix imperfect values and write NULL-aware predicates on hand-built rideshare
DataFrames — before file-based ingestion. Module 2 introduced the DataFrame
API and filter traps; this module goes deeper on three-valued logic, messy
values, safe casting, and parsing.

## Learning objectives

By the end of this module, you'll be able to:

- Explain three-valued logic and why filters keep only `TRUE` rows
- Build NULL-safe predicates (`isNull` / `isNotNull`, `isin` + NULL trap,
  `eqNullSafe`) without repeating Module 2 intro traps
- Identify missing data disguised as `NULL`, blank strings, sentinels, and
  `NaN`; normalize to real `NULL` before drop/fill decisions
- Use `na.drop`, `na.fill`, and `na.replace`; distinguish `F.coalesce` from
  partition `coalesce`
- Cast columns with `cast` and `try_cast`; detect rows rejected by a cast
- Handle numeric overflow and unparseable dates/timestamps with Spark 4 /
  ANSI `try_*` helpers
- Chain cleaning and predicate logic on small hand-built DataFrames

## Prerequisites

Module 2 — DataFrame Fundamentals. You should already know `select`,
`withColumn`, `filter` / `where`, `F.col`, `F.when`, intro NULL checks, and
empty string vs `NULL`.

## Notebook navigation

Four notebooks, in this order:

1. **NULL Semantics and Predicate Correctness**
   - Three-valued logic (`TRUE`, `FALSE`, `NULL`) shown as columns
   - Why filters keep only `TRUE`; extend Module 2 intro — do not re-teach
     `== None` or empty-string basics
   - `isin` + Python `None` trap; `eqNullSafe` / `<=>`
   - Reusable eligibility / quality predicate chain
2. **Missing, Blank, and Sentinel Values**
   - `NULL`, blank strings, sentinels (`"N/A"`, `-1`), and `NaN`
   - Normalize-first convention before `na.drop` / `na.fill`
   - `na.drop` (`how="any"` / `"all"`, `subset`), `na.fill`, `na.replace`
   - `F.coalesce` vs `DataFrame.coalesce(n)` gotcha
   - Bridge to notebook 3 — safe casting when strings must become typed columns
3. **Safe Type Casting**
   - `cast` vs `try_cast` under Spark 4 / ANSI mode
   - Rejected-row pattern: `source.isNotNull() & casted.isNull()`
   - Unsupported type pairs (when `try_cast` cannot help)
4. **Numeric Overflow and Date-Timestamp Parsing**
   - Cast and arithmetic overflow; `try_sum` / `try_avg`
   - `to_date` / `to_timestamp` with format patterns
   - `try_to_date` / `try_to_timestamp`; invalid format demos

Authoring approach: redesign from scratch to Academy standards; cover the
topic surface of the prior reference module without porting it verbatim.

## In scope / out of scope

**In scope:** hand-built messy rideshare DataFrames (`trip`, `payment`,
`trip_time` columns as needed); in-memory cleaning and NULL-aware predicates.

**Out of scope (defer to later modules):**

- File reads/writes, JDBC, bronze/silver paths → Module 5
- Raw-to-clean ingestion pipelines → Modules 5 and 13
- Full NULL behavior in joins → Module 7
- Quarantine / dead-letter patterns → Module 13

## Dataset used

Small, **ad-hoc** rideshare-flavored DataFrames built in code, aligned with
column names and types from
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).
File-based reading begins in Module 5.

## Exercises

Each notebook ends with a short hands-on task on a slightly different messy
DataFrame — for example, writing a NULL-safe filter, normalizing sentinels,
detecting rejected casts, or parsing date strings safely.

## Minimum privileges required

- Databricks workspace: ability to attach to or start compute
  (`CAN ATTACH TO` or `CAN RESTART` on the cluster/policy your workspace
  provides for this course)
- Unity Catalog: none — this module uses hand-built DataFrames only
