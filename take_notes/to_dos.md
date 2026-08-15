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
