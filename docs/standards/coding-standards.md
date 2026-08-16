# Coding Standards

This file is the canonical owner of Python and PySpark coding rules other
than identifier naming. It applies to learner notebooks now and to reusable
`src/` code after Module 13 introduces it.

Direct consumers are `docs/standards/notebook-authoring-checklist.md`,
`docs/standards/notebook-writing.md`,
`docs/standards/permissions-and-governance.md`, and `/write-lesson`. Other
notebook commands and `.cursor/rules/learner-notebooks.mdc` receive these
rules through the checklist. Do not duplicate the coding rules in those
consumers.

## Style baseline

- Follow PEP 8. `ruff` (configured in `pyproject.toml`) is the enforced
  linter/formatter for anything checkable locally; run `ruff format .` and
  `ruff check .` before pushing.
- Line length: 100 characters (matches the `ruff` config).
- For Python identifier naming (`snake_case`, `PascalCase`, constants), see
  @docs/standards/naming-conventions.md.

## PySpark-specific conventions

- Import functions as `from pyspark.sql import functions as F` and
  reference them as `F.col(...)`, `F.when(...)`, etc. — avoid
  `from pyspark.sql.functions import *`.
- Use `F.col()` for column expressions, transformations, disambiguation, and
  chained `Column` operations after the course introduces it. Earlier
  DataFrame-fundamentals lessons may use bare strings before `col()` is
  taught.
- Bare strings remain permitted as the sole column argument to a documented
  string-accepting API, including `groupBy()`, `orderBy()`, `partitionBy()`,
  `F.sum()`, `F.avg()`, `F.count()`, `F.min()`, and `F.max()`. When one
  chain uses both a string-accepting API and a `Column` expression, prefer
  one consistent reference style where the APIs allow it.
- Avoid UDFs when a built-in function achieves the same result — see
  **Module 6 — Built-in Functions, Complex Types, and UDF Alternatives** for
  the built-in-functions-first philosophy. When a UDF truly is necessary,
  explain why in a comment.
- Avoid `.collect()` / `.toPandas()` on data that isn't already known to be
  small; when used for teaching purposes on the small rideshare dataset,
  note that this pattern doesn't scale.
- Prefer chained, readable transformations over deeply nested expressions;
  break long chains across multiple `.withColumn()` calls or intermediate
  variables when it improves readability.

### Error handling in teaching notebooks

- Before an intentional failure, explain it in Markdown and add
  `# Expected: <ErrorType>` on the failing line.
- Treat a teaching `try`/`except` as a normal lesson whose objective is that
  pattern.
- Setup/config errors fail fast with a clear message; never silently swallow
  them.
- Never catch broad `Exception` unless that is the explicit lesson topic.

## Reusable code (`src/`, after Module 13)

- Type hints on public function signatures.
- Docstrings on any function whose purpose isn't obvious from its name and
  signature.
- No Spark session creation inside reusable functions — accept a
  `SparkSession`/`DataFrame` as a parameter instead, so functions stay
  testable without a live cluster.
- Pure, non-Spark-dependent logic is preferred where feasible, specifically
  so it can be covered by local `pytest` tests in **Module 16 — Testing,
  Data Quality, and Code Quality** without Databricks Connect or a running
  cluster.

## Security and portability

- No hardcoded access tokens, passwords, client secrets, workspace URLs,
  cluster IDs, or personal catalog/schema names — anywhere in code, comments,
  or docstrings. This repository is authored as if already public.
- No hardcoded local machine paths.
- Configuration that legitimately varies by environment must use the
  mechanism planned for that module, such as a setup/config cell, widgets,
  job parameters, or bundle variables. Do not introduce a mechanism before
  the course teaches it.

### Permitted author defaults

Safe committed defaults are generic sample catalog/schema names (for
example, `catalog_name = "my_catalog"`), placeholder usernames, and
non-secret course-controlled Volume paths. These values must be obviously
generic or defined by the course and must not identify a real learner,
customer, account, or workspace.

Never commit real workspace IDs, account or workspace URLs, tokens,
passwords, client secrets, personal email addresses, or
organization-specific catalog/schema names that reveal customer identity.

## Local tooling boundaries

`ruff`, `mypy`, and `pytest` run locally and check Python syntax, style, and
non-Spark logic only. They do not execute Spark, Delta Lake, or Unity
Catalog operations — that validation only happens in Azure Databricks (see
`docs/standards/compute-validation-policy.md`).

## Does not cover

- Identifier naming — see `docs/standards/naming-conventions.md`.
- Notebook structure and cell formatting — see
  `docs/standards/notebook-writing.md`.
- Compute selection and runtime evidence — see
  `docs/standards/compute-validation-policy.md`.
