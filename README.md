# PySpark on Azure Databricks Academy

A job-focused PySpark data engineering course on Azure Databricks, currently
under active development. The course is designed to progress from beginner
Spark fundamentals to production batch data engineering, using a single
connected rideshare dataset (`trip`, `trip_time`, `payment`, `zone_lookup`,
plus supplementary `drivers`) as the running example throughout, and to
culminate in a deployable batch data engineering project.

This course covers **batch data engineering only**. Structured Streaming,
Auto Loader, streaming tables, machine learning, and general Azure
infrastructure administration are out of scope.

## Who this is for

You should already know:
- Basic Python syntax
- Basic SQL (not advanced SQL)

You do **not** need prior experience with:
- Apache Spark or Azure Databricks
- Production data engineering
- Local Databricks development/deployment workflows

To complete the hands-on exercises, you need access to an Azure Databricks
workspace and permission to use suitable compute. Module-specific environment
and privilege requirements are documented in each module's `README.md`.

Unfamiliar concepts are explained before they're used.

## Technical baseline

| Component | Version / Detail |
|---|---|
| Cloud platform | Microsoft Azure |
| Platform | Azure Databricks, Premium tier |
| Databricks Runtime | 17.3 LTS |
| Apache Spark | 4.0.0 |
| Python | 3.12 |
| Scala runtime | 2.13 |
| Primary language | Python with PySpark |
| SQL | Spark SQL in Databricks notebooks (`%sql` and `spark.sql()`) |
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

- **Full roadmap and current status:** [`COURSE_MODULES.md`](COURSE_MODULES.md) — module purposes, topics, prerequisites, and planned progression
- **Start here (learners):** [`01 - Azure Databricks and Spark Foundations`](01%20-%20Azure%20Databricks%20and%20Spark%20Foundations/)
- **Before Module 5:** Review the [module-specific environment and privilege requirements](05%20-%20Reading%2C%20Writing%2C%20and%20Schemas/README.md#before-notebook-01).

## Repository conventions

- Module folders and notebooks: `NN - Descriptive Title` — see
  `docs/standards/naming-conventions.md`
- Coding and notebook-writing standards: `docs/standards/`
- Dataset reference (schemas, join keys, physical layout): `docs/data/dataset-overview.md`
- Author-facing runtime validation evidence: `docs/validation/`

## Optional local authoring setup

Learners who run notebooks only in Azure Databricks do not need local Python
tooling. For local authoring and non-Spark checks, this repository uses
[`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
```

See `pyproject.toml` for the declared development tools (`ruff`, `mypy`,
`pytest`); `uv.lock` records the resolved versions.
