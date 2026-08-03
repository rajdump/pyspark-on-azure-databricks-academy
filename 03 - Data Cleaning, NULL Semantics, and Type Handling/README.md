# Module 3 — Data Cleaning, NULL Semantics, and Type Handling

## Purpose

Fix imperfect values and write NULL-aware predicates on hand-built rideshare
DataFrames — before file-based ingestion. Module 2 introduced the DataFrame
API and filter traps; this module goes deeper on three-valued logic, messy
values, safe casting, and parsing under Spark 4 / ANSI mode (prefer `try_*`
helpers over disabling ANSI globally).

## Learning objectives

By the end of this module, you'll be able to:

- Explain three-valued logic and why filters keep only `TRUE` rows
- Build NULL-safe predicates with `isNull` / `isNotNull`, the `isin` + NULL
  trap, and `eqNullSafe` / `<=>`
- Identify missing data as `NULL`, blanks, sentinels, and `NaN`; normalize to
  real `NULL` before drop/fill
- Use `na.drop`, `na.fill`, and `na.replace`; use `F.coalesce` for column
  fallbacks (not partition `DataFrame.coalesce(n)`)
- Cast with `cast` and `try_cast`; detect rows rejected by a cast
- Handle numeric overflow and unparseable dates/timestamps with Spark 4 /
  ANSI `try_*` helpers
- Chain cleaning and predicate logic on small hand-built DataFrames

## Prerequisites

Module 2 — DataFrame Fundamentals. You should already know `select`,
`withColumn`, `filter` / `where`, `F.col`, `F.when`, intro NULL checks, and
empty string vs `NULL`.

## Dataset

Small **ad-hoc** rideshare-flavored DataFrames built in code, aligned with
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md). Volume
file reading starts in Module 5.

## Notebooks

Four notebooks, in order. Each ends with a short hands-on task on a slightly
different messy DataFrame (NULL-safe filter, sentinel normalize, rejected
casts, safe date parse, etc.).

| # | Notebook | Focus |
|---|---|---|
| 1 | NULL Semantics and Predicate Correctness | Three-valued logic as columns; filters keep only `TRUE`; `isNull` / `isNotNull`; `isin` + `None` trap; `eqNullSafe` / `<=>`; reusable eligibility / quality predicate chain |
| 2 | Missing, Blank, and Sentinel Values | `NULL`, blanks, sentinels (`"N/A"`, `-1`), `NaN`; normalize before `na.drop` / `na.fill`; `na.drop` / `na.fill` / `na.replace`; `F.coalesce` (not partition coalesce) |
| 3 | Safe Type Casting | `cast` vs `try_cast` under Spark 4 / ANSI; rejected-row pattern (`source.isNotNull() & casted.isNull()`); unsupported type pairs |
| 4 | Numeric Overflow and Date-Timestamp Parsing | Cast / arithmetic overflow; `try_sum` / `try_avg`; `to_date` / `to_timestamp` with formats; `try_to_date` / `try_to_timestamp`; invalid source vs invalid format |

## Minimum privileges required

- Workspace: **`CAN ATTACH TO`** or **`CAN RESTART`** on the compute/policy for
  this course
- Unity Catalog: none — hand-built DataFrames only
