# Coding Standards

Canonical owner of all Python coding rules for this repository — notebook
code today, `src/` code once it's introduced (Module 13+). Referenced by
`.cursor/rules/learner-notebooks.mdc`, `/write-lesson`, `/validate-notebook`,
and `/review-module` (and later `.cursor/rules/python-modules.mdc`) — do not
duplicate this content elsewhere. Shared read list:
@docs/standards/notebook-authoring-checklist.md.

## Style baseline

- Follow PEP 8. `ruff` (configured in `pyproject.toml`) is the enforced
  linter/formatter for anything checkable locally; run `ruff format .` and
  `ruff check .` before pushing.
- Line length: 100 characters (matches the `ruff` config).
- `snake_case` for variables and functions, `PascalCase` for classes —
  see `naming-conventions.md` for file/folder naming.

## PySpark-specific conventions

- Import functions as `from pyspark.sql import functions as F` and
  reference them as `F.col(...)`, `F.when(...)`, etc. — avoid
  `from pyspark.sql.functions import *`.
- Prefer `F.col("name")` over bare string column references in
  transformation chains once a notebook has introduced `col()` — bare
  strings are fine in the earliest DataFrame-fundamentals material before
  `col()` is taught.
- Avoid UDFs when a built-in function achieves the same result — see
  Module 6 for the built-in-functions-first philosophy. When a UDF truly is
  necessary, explain why in a comment.
- Avoid `.collect()` / `.toPandas()` on data that isn't already known to be
  small; when used for teaching purposes on the small rideshare dataset,
  note that this pattern doesn't scale.
- Prefer chained, readable transformations over deeply nested expressions;
  break long chains across multiple `.withColumn()` calls or intermediate
  variables when it improves readability.

## Reusable code (`src/`, once introduced)

- Type hints on public function signatures.
- Docstrings on any function whose purpose isn't obvious from its name and
  signature.
- No Spark session creation inside reusable functions — accept a
  `SparkSession`/`DataFrame` as a parameter instead, so functions stay
  testable without a live cluster.
- Pure, non-Spark-dependent logic is preferred where feasible, specifically
  so it can be covered by local `pytest` tests (Module 17) without needing
  Databricks Connect or a running cluster.

## Security and portability

- No hardcoded access tokens, passwords, client secrets, workspace URLs,
  cluster IDs, or personal catalog/schema names — anywhere in code, comments,
  or docstrings. This repository is authored as if already public.
- No hardcoded local machine paths.
- Configuration (catalog names, paths, etc.) that legitimately varies by
  environment is parameterized (widgets, job parameters, or bundle
  variables — introduced progressively as those mechanisms are taught).
  Module 5 Notebooks 01/99 use a Python config cell for Azure storage
  account, container, storage credential, and ADLS folder (author defaults;
  learners overwrite). Course UC object names stay fixed per
  `docs/data/dataset-overview.md`.

## Local tooling boundaries

`ruff`, `mypy`, and `pytest` run locally and check Python syntax, style, and
non-Spark logic only. They do not execute Spark, Delta Lake, or Unity
Catalog operations — that validation only happens in Azure Databricks (see
`compute-validation-policy.md`).
