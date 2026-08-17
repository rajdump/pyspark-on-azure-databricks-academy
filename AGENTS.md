# AGENTS.md

A batch-only PySpark data engineering course on Azure Databricks, organized
into numbered module folders (`NN - Descriptive Title`). Authored locally in
Cursor, pushed to GitHub, then pulled into an Azure Databricks Git folder to
run.

## Hard constraints

- Learner notebooks are Databricks source `.py` files whose first line is
  `# Databricks notebook source`. Never `.ipynb`.
- Batch data engineering only. Never add Structured Streaming, Auto Loader,
  streaming tables, or ML content.
- Never execute Spark, Delta, or Unity Catalog locally. All runtime behavior
  is validated in Azure Databricks.
- Never invent a table name, column, path, grant, or row count. Take it from
  a **Read for facts** source, or ask the author.

## Author-only writes

Do not perform these unless the author explicitly asks:

- Changing module status in `COURSE_MODULES.md`, including as a side effect
  of lesson work.
- Editing `docs/validation/`, which records only Azure Databricks output the
  author supplied. Never infer or mark a runtime outcome.
- Scaffolding a new learner notebook before the **Readiness precondition** in
  `docs/standards/notebook-authoring-checklist.md` is met.

## Read for facts

Read these for course facts. When they disagree, the earlier source wins.

1. `COURSE_MODULES.md` — roadmap and module status
2. `NN - Descriptive Title/README.md` — that module's lesson design; read
   `docs/standards/readme-authoring.md` for its required structure and the
   **Design-complete definition**
3. `NN - Descriptive Title/requirements/` — approved BRDs and mappings, when
   present
4. `docs/data/dataset-overview.md` — dataset schemas, join keys, paths, and
   pipeline contracts
5. `docs/standards/` — authoring policy and pedagogy; read
   `docs/standards/notebook-authoring-checklist.md` for command read
   manifests and acceptance bars
6. `docs/validation/` — recorded runtime evidence
7. `vault/`, `take_notes/`, and dated root notes — context only

Outside that chain, the root `README.md` owns the learner overview and the
technical baseline (runtime, Spark and Python versions, governance,
languages).

## Authoring workflows

Prefer these slash commands in `.cursor/commands/` over ad-hoc chat so read
manifests and stop conditions load consistently:

| Task | Command |
|---|---|
| Design a module | `/write-module-readme` |
| Create a notebook scaffold | `/new-lesson` |
| Write a full lesson | `/write-lesson` |
| Gate authoring quality | `/validate-notebook` |
| Review a whole module | `/review-module` |

Load standards on demand. Never assume a standard or a `.cursor/rules/*.mdc`
rule is already in context. Prior chat is never a substitute for a required
read: when a command or rule names a manifest or canonical source, read it
in the current session even if it appeared earlier in conversation.

## Local checks

```bash
uv sync
uv run ruff check .
uv run mypy .
```

Both report expected pre-existing findings in learner notebooks:
Databricks-injected `spark`, `dbutils`, and `display` read as undefined,
`# MAGIC` prose exceeds the line length, and per-cell imports trip
import-position rules. Never "fix" those, and never add a `SparkSession` to a
learner notebook. Act only on findings in lines you added. `pytest` is
configured but no `tests/` directory exists.
