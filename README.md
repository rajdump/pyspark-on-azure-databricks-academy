# PySpark on Azure Databricks Academy

A job-focused PySpark data engineering course on Azure Databricks. It
progresses from beginner Spark fundamentals to production batch data
engineering, using a single connected rideshare dataset as the running
example throughout, and ends with a deployable batch data engineering
project.

This course covers **batch data engineering only**. Streaming (Structured
Streaming, Auto Loader, streaming tables/pipelines), machine learning, and
general Azure infrastructure administration are out of scope.

## Who this is for

You should already know:
- Basic Python syntax
- Basic SQL (not advanced SQL)

You do **not** need prior experience with:
- Apache Spark or Azure Databricks
- Production data engineering
- Local Databricks development/deployment workflows

Unfamiliar concepts are explained before they're used.

## Technical baseline

| Component | Version / Detail |
|---|---|
| Cloud platform | Microsoft Azure |
| Platform | Azure Databricks, Premium tier (Unity Catalog + RBAC enabled) |
| Databricks Runtime | 17.3 LTS |
| Apache Spark | 4.0.0 |
| Python | 3.12 |
| Scala runtime | 2.13 |
| Primary language | Python with PySpark |
| SQL | Databricks SQL / Spark SQL, where it serves the learning objective |
| Governance | Unity Catalog |
| Version control | GitHub |
| Notebook format | Databricks source `.py` notebooks |

Compute is selected per module (classic all-purpose Standard/Dedicated, jobs
compute, or serverless) based on that module's APIs and learning objectives —
see `docs/standards/compute-validation-policy.md` for the selection and
validation-order rules.

## Development workflow

```
Local laptop (Cursor)  -->  GitHub  -->  Azure Databricks Git folder
```

1. Author and review notebooks, Markdown, and code locally in Cursor.
2. Commit and push to GitHub — the canonical remote source of truth.
3. Azure Databricks pulls the approved version via a Git folder.
4. Run and validate in Azure Databricks; record results in `docs/validation/`.

Local tooling (`uv`, `ruff`, `mypy`, `pytest`) handles formatting, linting,
and non-Spark checks. Spark, Delta Lake, and Unity Catalog execution only
happens in Azure Databricks — local Spark execution is not part of this
workflow.

## Where to start

- **Full roadmap:** [`COURSE_MODULES.md`](COURSE_MODULES.md) — all 19 modules, their purpose, and status
- **Start here (learners):** [`01 - Azure Databricks and Spark Foundations`](01%20-%20Azure%20Databricks%20and%20Spark%20Foundations/)
- **Phase I complete** through Module 4 — next to author: **Module 5 — Reading, Writing, and Schemas** (Volume-based file I/O, JDBC, and schemas — see [`COURSE_MODULES.md`](COURSE_MODULES.md))

## Repository conventions

- Module folders and notebooks: `NN - Descriptive Title` — see
  `docs/standards/naming-conventions.md`
- Coding and notebook-writing standards: `docs/standards/`
- Dataset reference (schemas, join keys, file layout): `docs/data/dataset-overview.md`
- Author-facing runtime validation evidence: `docs/validation/`

## Setup

This repository uses [`uv`](https://docs.astral.sh/uv/) for local Python
tooling (not for the Databricks runtime itself).

```bash
uv sync
```

See `pyproject.toml` for the pinned dev dependencies (`ruff`, `mypy`,
`pytest`).
