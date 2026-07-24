# Notebook Writing Standards

Canonical owner of all notebook structure and formatting rules. Referenced
by `.cursor/rules/learner-notebooks.mdc` and the `/new-lesson` and
`/validate-notebook` commands — do not duplicate this content elsewhere.

## Format

All learner notebooks are **Databricks source-format `.py` files** — never
`.ipynb`. This is fixed (see `README.md` for why); this document covers how
to write within that format.

Required structure markers:

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Notebook Title
# MAGIC
# MAGIC Learning objectives, context, prerequisites.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section heading

# COMMAND ----------

# Python / PySpark code for this section

# COMMAND ----------
```

- The first line must be exactly `# Databricks notebook source`.
- `# COMMAND ----------` separates cells.
- `# MAGIC %md` prefixes a Markdown cell's lines; `# MAGIC %sql` prefixes a
  SQL cell's lines.
- Never hand-edit cell boundaries in a way that breaks Databricks' ability
  to parse the file back into cells — always keep the exact marker syntax.

## Notebook-level structure

Every learner notebook follows this shape:

1. **Title + objectives cell** — what the learner will be able to do after
   this notebook, and which prior notebooks it assumes.
2. **Setup cell(s)** — imports, and reads of the shared dataset where
   relevant (see `docs/data/dataset-overview.md`).
3. **One concept path per notebook** — introduce a concept, show it, let the
   learner practice it, before moving to the next. Avoid cramming unrelated
   concepts into one notebook — split into another numbered notebook
   instead.
4. **Worked examples before exercises** — demonstrate the pattern with the
   rideshare dataset, then give the learner a similar but not identical
   task.
5. **Summary cell** — brief recap of what was covered and a pointer to the
   next notebook.

## Code cell conventions

- Prefer the DataFrame API and `pyspark.sql.functions` (imported as `F`)
  unless the notebook's explicit purpose is to teach Spark SQL (Module 10).
- Show, don't just tell: every new API introduced gets a runnable example
  against the rideshare dataset before being used in an exercise.
- Keep cells focused — one idea per cell — so a learner can run cells
  incrementally and see each step's effect with `display()`/`.show()`.
- Comments explain *why*, not *what* the code already says.

## What must never appear in a notebook

- Access tokens, passwords, client secrets
- Personal workspace URLs or cluster IDs
- Personal catalog/schema names that reveal account-specific details
- Hardcoded local machine paths

These rules exist because this repository is authored as if already public.

## Minimum privileges

If a notebook's examples require specific Unity Catalog privileges beyond
what a default learner might have, the module's `README.md` documents them
(see `permissions-and-governance.md` for the pattern) — this is not
repeated inside the notebook itself.
