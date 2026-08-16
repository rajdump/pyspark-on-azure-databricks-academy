# AGENTS.md

Always-on agent context. Canonical project guidance lives in `README.md`,
`COURSE_MODULES.md`, `docs/standards/`, and `docs/data/` — this file routes
to those sources instead of duplicating them.

## What this is

A batch-only PySpark data engineering course on Azure Databricks, authored as
Databricks source `.py` notebooks, organized into numbered modules
(`NN - Descriptive Title`). See `COURSE_MODULES.md` for the roadmap and use
the target module's `README.md` for its detailed design.

- Notebook format: Databricks source `.py` (`# Databricks notebook source`
  header required) — never `.ipynb`
- Batch data engineering only — no Structured Streaming, Auto Loader,
  streaming tables, or ML content
- Full technical baseline (runtime, Spark/Python versions, governance,
  languages): `README.md`

## Dataset

A shared rideshare dataset (`trip`, `trip_time`, `payment`, `zone_lookup`,
plus a supplementary nested `drivers` dataset) threads through every module.
Full schema, join keys, and physical layout: `docs/data/dataset-overview.md`.

## Workflow

Local authoring in Cursor -> push to GitHub (source of truth) -> Azure
Databricks Git folder pulls and runs. Local tooling (`uv`, `ruff`, `mypy`,
`pytest`) never executes Spark; all Spark/Delta/Unity Catalog behavior is
validated in Azure Databricks.

## Where to read

- Learner overview and full technical baseline: `README.md`
- Roadmap and status: `COURSE_MODULES.md`
- Module design: the target module's `README.md`
- Module README structure and **Design-complete definition**:
  `docs/standards/readme-authoring.md`
- Command-specific read manifests and acceptance bars for notebook work:
  `docs/standards/notebook-authoring-checklist.md`
- Dataset contract: `docs/data/dataset-overview.md`
- Process and pedagogy: `docs/standards/`

## Do not write automatically

- Do not update `COURSE_MODULES.md` status as a side effect; change it only
  when the author explicitly asks.
- Do not infer, fabricate, or independently mark runtime outcomes. Edit
  `docs/validation/` only when the author explicitly asks using Azure
  Databricks results or output they supplied.
- Scaffold learner notebooks only when the **Readiness precondition** in
  `docs/standards/notebook-authoring-checklist.md` is met.

## Cursor

Module-design and lesson workflows live in `.cursor/commands/`.

Each `.cursor/rules/*.mdc` file declares its own attachment behavior in
frontmatter. Do not assume a rule or the standards it references are already
in context; open the required canonical files.
