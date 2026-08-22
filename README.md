# PySpark on Azure Databricks Academy

A job-focused PySpark data engineering course on Azure Databricks, currently
under active development. The course is designed to progress from beginner
Spark fundamentals to production batch data engineering, using a single
connected [rideshare dataset](docs/data/dataset-guide.md) as the running
example throughout, and to culminate in a deployable batch data engineering
project.

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
compute, or serverless) based on that module's APIs and learning objectives.
Each module's `README.md` states what that module needs.

## Where to start

The course runs in five phases, from Spark and Databricks foundations to a
deployable batch capstone — see the [phase list](COURSE_MODULES.md#phases).

- **Full roadmap and current status:** [`COURSE_MODULES.md`](COURSE_MODULES.md) — module purposes, topics, prerequisites, and planned progression
- **Start here (learners):** [`01 - Azure Databricks and Spark Foundations`](01%20-%20Azure%20Databricks%20and%20Spark%20Foundations/)
- **Before Module 5:** Review the [module-specific environment and privilege requirements](05%20-%20Reading%2C%20Writing%2C%20and%20Schemas/README.md#before-notebook-01).

## For course authors

Everything below is for authoring and maintaining this course — learners can
stop here. Agent-facing constraints, author-only writes, and source
precedence live in [`AGENTS.md`](AGENTS.md).

### Development workflow

```
Local laptop (Cursor)  -->  GitHub  -->  Azure Databricks Git folder
```

1. Author and review notebooks, Markdown, and code locally in Cursor.
2. Commit and push to GitHub — the canonical remote source of truth.
3. Azure Databricks pulls the approved version via a Git folder.
4. Run and validate in Azure Databricks.

Local tooling handles formatting, linting, and non-Spark checks only. Spark,
Delta Lake, and Unity Catalog execution happens exclusively in Azure
Databricks; [`AGENTS.md`](AGENTS.md) states that as a hard constraint for
agents.

### Repository conventions

- Module folders and notebooks: `NN - Descriptive Title` — see
  `docs/standards/naming-conventions.md`
- Slash commands (`.cursor/commands/`): `docs/standards/command-authoring.md`
- Coding and notebook-writing standards: `docs/standards/`
- Compute selection and validation order:
  `docs/standards/compute-validation-policy.md`
- Dataset reference (schemas, join keys, physical layout): `docs/data/dataset-overview.md`

### Local authoring setup

Learners who run notebooks only in Azure Databricks do not need local Python
tooling. For local authoring and non-Spark checks, this repository uses
[`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
```

`pyproject.toml` declares `ruff` and `mypy`, which are usable now, plus
`pytest` for the test suite Module 16 introduces — no `tests/` directory
exists yet. `uv.lock` records the resolved versions.

```bash
uv run ruff check .
uv run mypy .
python3 scripts/check_doc_references.py
```

`ruff` and `mypy` cover Python code. Run
`scripts/check_doc_references.py` after editing any file in
`.cursor/commands/`, `.cursor/rules/`, or `AGENTS.md`. It verifies that
every `[[Section name]]` pointer and every `` `path` `` or `@path` written
in those files still resolves — so renaming a heading in a standard or
moving a file breaks the build instead of failing silently at runtime. It
does not check command block structure; see
`docs/standards/command-authoring.md` for that. `0 unresolved` means pass.
The script uses only the Python standard library.
