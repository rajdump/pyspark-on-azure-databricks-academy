# AGENTS.md

Concise, tool-agnostic project summary. Full standards live in
`docs/standards/*.md` and `docs/data/*.md` — this file points to them, it
does not duplicate them.

## What this project is

A batch-only PySpark data engineering course on Azure Databricks, authored as
Databricks source `.py` notebooks, organized into numbered modules
(`NN - Descriptive Title`). See `COURSE_MODULES.md` for the full roadmap and
the current module's own `README.md` for detailed, in-progress design.

## Technical baseline

- Azure Databricks, Premium tier, Unity Catalog enabled
- Databricks Runtime 17.3 LTS — Spark 4.0.0, Python 3.12, Scala 2.13
- Primary language: PySpark; SQL via Databricks SQL / Spark SQL where relevant
- Notebook format: Databricks source `.py` (`# Databricks notebook source`
  header required) — never `.ipynb`
- Batch data engineering only — no Structured Streaming, Auto Loader,
  streaming tables, or ML content

## Dataset

A shared rideshare dataset (`trip`, `trip_time`, `payment`, `zone_lookup`,
plus a supplementary nested `drivers` dataset) threads through every module.
Full schema, join keys, and physical layout: `docs/data/dataset-overview.md`.

## Workflow

Local authoring in Cursor -> push to GitHub (source of truth) -> Azure
Databricks Git folder pulls and runs. Local tooling (`uv`, `ruff`, `mypy`,
`pytest`) never executes Spark; all Spark/Delta/Unity Catalog behavior is
validated in Azure Databricks.

## Where the real rules live

Documentation layers (link down; do not duplicate content across tiers):

- Roadmap and status: `COURSE_MODULES.md`
- Dataset schemas, join keys, and physical layout: `docs/data/dataset-overview.md`
- Module design when authoring (notebook navigation, privileges): that module's `README.md`
- Process and pedagogy: `docs/standards/`

- Coding standards: `docs/standards/coding-standards.md`
- Notebook structure and formatting: `docs/standards/notebook-writing.md`
- Naming conventions: `docs/standards/naming-conventions.md`
- Teaching/pedagogy standards: `docs/standards/teaching-guidelines.md`
- Compute selection and validation order: `docs/standards/compute-validation-policy.md`
- Permissions and governance (Azure RBAC vs. workspace permissions vs. Unity
  Catalog privileges): `docs/standards/permissions-and-governance.md`
- Notebook authoring checklist (shared read list for slash commands):
  `docs/standards/notebook-authoring-checklist.md`

Scoped `.cursor/rules/*.mdc` files load these automatically for matching
files. Slash commands (`/new-lesson`, `/write-lesson`, `/validate-notebook`,
`/review-module`) reference the checklist and standards directly.

Recommended notebook workflow: `/new-lesson` (skeleton) → `/write-lesson`
(full content) → `/validate-notebook` (authoring check) → Azure Databricks
runtime validation by the author.

## What Cursor should not do automatically

- Never update `COURSE_MODULES.md` status — that is author-owned.
- Never write runtime validation evidence in `docs/validation/` — that is
  filled in by the author after running notebooks in Azure Databricks.
- `/new-lesson`, `/write-lesson`, `/validate-notebook`, and `/review-module`
  never write roadmap status or runtime validation evidence (`/write-lesson`
  fills lesson content; `/new-lesson` scaffolds only).
