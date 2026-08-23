# To-dos

## July 30th 2026

- As part of this module, note the important terms: column-oriented vs. row-oriented
  files, data warehouse vs. data lake vs. lakehouse. We need to cover these topics in
  the course.
- Do we need to clarify when to use Avro and Parquet? In this era of Delta files,
  learners should understand that Delta does not replace every file format.
- I need to understand different files in this workspace
  `pyspark-on-azure-databricks-academy` and its usage, apart from notebooks — list and
  categorize the files across the workspace.
- Azure Databricks account creation
- Databricks free edition creation

## August 14th 2026

- Need to tune `dataset-overview.md` file to reduce the token cost

## August 15th 2026

### Cursor vs Databricks — what loads into agent context

Nothing from the repo auto-loads into Databricks chat/Genie. Databricks only sees what
you open, paste, or explicitly reference.

| File / folder | In Git repo? | Cursor auto-load? | Databricks auto-load? | Notes |
| --- | --- | --- | --- | --- |
| `AGENTS.md` | Yes | Yes (always) | No | Cursor project map only |
| `.cursor/rules/*.mdc` | Yes | Yes (globs / command @-ref) | No | Cursor-only; harmless in Databricks |
| `.cursor/commands/` | Yes | Yes (when you invoke `/command`) | No | Cursor-only workflows |
| `docs/standards/*.md` | Yes | No (read on demand) | No | Portable source of truth — manual ref only |
| `docs/data/*.md` | Yes | No (read on demand) | No | Same as above |
| Module `README.md` | Yes | No (read on demand) | No | Same as above |
| Notebook `.py` files | Yes | Yes (glob rule when editing) | No | Run in Databricks; not agent context |

**Solution:**

- Author in Cursor → use `.mdc` + slash commands to find/follow standards.
- Run/validate in Databricks → notebooks execute; agents don't inherit Cursor rules.
- In Databricks chat → paste or reference `docs/standards/` manually.
- Keep one source of truth in `docs/standards/`; `.mdc`/commands only point there.

**Workflow:** Cursor (author) → GitHub → Databricks Git folder (run/validate)

## August 16th 2026

### Understand `docs/standards/`

Read the standards in this order:

1. `notebook-authoring-checklist.md` — master workflow and loading map
2. `readme-authoring.md` — module design before notebooks
3. `teaching-guidelines.md` — how lessons should teach
4. `notebook-writing.md` — notebook structure and cells
5. `coding-standards.md` — Python/PySpark implementation rules
6. `naming-conventions.md` — names for folders, files, and identifiers
7. `permissions-and-governance.md` — access and privilege requirements
8. `compute-validation-policy.md` — runtime testing and compute selection

For each file, answer:

- What does it own?
- When is it loaded?
- Which commands or rules consume it?
- What does it explicitly not cover?
- What practical behavior does it change?

## August 23rd 2026

### Companion site for theory (launch)

Databricks notebooks stay labs: code plus short cell-level explanation. Longer
theory (data-lake drawbacks, warehouse vs lake vs lakehouse, ACID overview,
governance ideas) does not belong as encyclopedia markdown in the notebooks.

When launching, put that theory on a companion site and link it from the
matching notebook (one “read this first” link at the top — not a URL on every
cell).

Prefer a site **built from this repo** (GitHub Pages, MkDocs, or Docusaurus)
so the page version ships with the notebook version, PRs can review both, and
links do not rot on a disconnected Notion or marketing site. Notion/PPT stay
fine for drafting or a live talk.

Split by topic (not one mega article). Map pages to modules (e.g. lake
limitations → Module 10 / 01; ACID → 11; governance → 12; medallion → 13).
Do not put streaming / Auto Loader on the site while the course is
batch-only. Dataset contracts (tables, paths, row counts) stay in
`docs/data/dataset-overview.md` and the notebooks — the site explains ideas,
not those facts.

### Cover limitations: warehouse, data lake, and Parquet → Delta Lake

Theory track should explain **why** teams move to Delta, not only how `UPDATE`
works in a notebook:

- **Data warehouse** limitations (cost, rigidity, weak fit for raw /
  semi-structured files)
- **Data lake** limitations (files without a table log: no reliable row
  change, snapshot, versioning, or fine-grained governance)
- **Parquet** as lake storage: columnar and useful, but a Parquet *folder*
  is still not a table (rewrite-to-change-a-row, no `_delta_log`)
- **Delta Lake** as the transformation: same Parquet data files plus a
  transaction log — lakehouse table behavior on lake storage

Keep this on the companion site (and/or a short lecture). Module 10 notebook
01 stays the lab proof of one gap (Parquet overwrite vs Delta `UPDATE`).
Later modules still own ACID, governance, and medallion — do not dump those
into notebook 01.
