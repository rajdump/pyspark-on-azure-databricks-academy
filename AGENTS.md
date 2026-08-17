# AGENTS.md

Always-on agent context for this repository. States constraints, where
authoritative documents live, and what requires explicit author approval.

## Repository constraints

Non-negotiable scope and format rules for all work in this repo.

A batch-only PySpark data engineering course on Azure Databricks, organized
into numbered modules (`NN - Descriptive Title`). See `COURSE_MODULES.md` for
the roadmap and the target module's `README.md` for its detailed design.

- Notebook format: Databricks source `.py` (`# Databricks notebook source`
  header required) — never `.ipynb`
- Batch data engineering only — no Structured Streaming, Auto Loader,
  streaming tables, or ML content
- Shared rideshare dataset (`trip`, `trip_time`, `payment`, `zone_lookup`,
  plus supplementary nested `drivers`) threads through every module — schemas,
  join keys, and physical layout: `docs/data/dataset-overview.md`
- Full technical baseline (runtime, Spark/Python versions, governance,
  languages): `README.md`

## Authoring and validation workflow

How content is authored locally and validated in Azure Databricks.

Local authoring in Cursor -> push to GitHub (source of truth) -> Azure
Databricks Git folder pulls and runs. Local tooling (`uv`, `ruff`, `mypy`,
`pytest`) never executes Spark; all Spark/Delta/Unity Catalog behavior is
validated in Azure Databricks.

## Authoritative documents and precedence

Where to read facts; use the numbered order when sources disagree (details:
`vault/decisions.md` — Source precedence):

1. `COURSE_MODULES.md` — roadmap and status
2. Target module `README.md` — lesson design
   (`docs/standards/readme-authoring.md` for structure and
   **Design-complete definition**)
3. Approved BRDs/mappings under a module's `requirements/` (when present)
4. `docs/data/dataset-overview.md` — schemas, paths, contracts
5. `docs/standards/` — authoring policy and pedagogy; command read manifests
   and acceptance bars: `docs/standards/notebook-authoring-checklist.md`
6. `docs/validation/` — author-supplied runtime evidence only
7. `vault/`, `take_notes/`, and personal notes — context only, not
   authoritative

`README.md` — learner overview and technical baseline (outside the conflict
chain above).

## Author-only writes

Do not perform these updates unless the author explicitly requests them.

- Do not update `COURSE_MODULES.md` status as a side effect; change it only
  when the author explicitly asks.
- Do not infer, fabricate, or independently mark runtime outcomes. Edit
  `docs/validation/` only when the author explicitly asks using Azure
  Databricks results or output they supplied.
- Do not guess or invent table names, columns, paths, grants, or row counts
  in module READMEs or notebooks; derive them from canonical sources or ask
  the author.
- Scaffold learner notebooks only when the **Readiness precondition** in
  `docs/standards/notebook-authoring-checklist.md` is met.

## Cursor authoring tools

Prefer slash commands; load standards on demand — do not assume they are in
context.

Module-design and lesson workflows live in `.cursor/commands/`. For module
README and learner-notebook work, prefer the slash commands there
(`/write-module-readme`, `/new-lesson`, `/write-lesson`, `/validate-notebook`,
`/review-module`) so read manifests and stop conditions load consistently.

Each `.cursor/rules/*.mdc` file declares its own attachment behavior in
frontmatter. Do not assume a rule or the standards it references are already
in context; open the required canonical files.
