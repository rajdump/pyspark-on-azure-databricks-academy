# Notebook Writing Standards

This file is the canonical owner of Databricks notebook source format,
notebook structure, cell boundaries, and output-display conventions.

Direct consumers are `docs/standards/notebook-authoring-checklist.md` and
`/new-lesson`. `/write-lesson`, `/validate-notebook`, `/review-module`, and
`.cursor/rules/learner-notebooks.mdc` receive these rules through the
checklist. Do not duplicate the notebook-format rules in those consumers.

## Format

All learner notebooks are **Databricks source-format `.py` files** — never
`.ipynb`. This is fixed (see `README.md` for the technical baseline); this
document covers how to write within that format.

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

### Markdown conventions

- Use `###` only for distinct subtopics within an H2; do not use H4 or deeper.
- Use `> **Note:**` for important asides and `> **Warning:**` for common
  pitfalls, with at most one callout per section.
- Use bold for UI elements and key terms on first introduction, italics for
  variable references in prose, and never underline.
- Use triple backticks plus `python`, `sql`, or `text`; use inline backticks
  for column names, function names, and short expressions.

## Notebook-level structure

Every learner notebook follows this shape:

1. **Title + objectives cell** — what the learner will be able to do after
   this notebook, and which prior notebooks it assumes.
2. **Setup cell(s)** — imports, and reads of the shared dataset where
   relevant (see @docs/data/dataset-overview.md).
3. **Planned concept sections** — section order follows the module README's
   Notebooks table Focus cell. Split unrelated concept paths into separate
   planned notebooks.
4. **Examples and exercises** — their teaching order follows the
   **Structure patterns** section in
   @docs/standards/teaching-guidelines.md.
5. **Summary cell** — brief recap of what was covered and a pointer to the
   next notebook.

### Notebook dependencies and execution state

- Each notebook must run after executing only its own top setup/config cell.
- Document persistent prerequisites such as tables or Volume files in the
  objectives cell.
- Never depend on variables, imports, or temporary views from another
  notebook; re-establish all in-memory state locally.
- Prior-notebook dependencies must use persistent tables or files, never
  hidden session state.

## Code cell conventions

- Follow the import conventions in
  @docs/standards/coding-standards.md.
- Select DataFrame, SQL, and comparison cells using the **DataFrame and SQL
  teaching policy** in @docs/standards/teaching-guidelines.md.
- Keep cells focused — one idea per cell — so a learner can run cells
  incrementally and see each step's effect with `display()`/`.show()`.
- **Together (acceptable):** a short setup line, the transformation it
  enables, and `display()` may share a cell when they serve one learning
  point and total fewer than about 10 lines.
- **Split (required):** separate reusable setup (imports/config), a lesson
  transformation that needs an explanation cell above, or output that needs
  its own discussion below. Borderline cases are reviewer judgment, not a
  hard validation failure.
- Comments explain *why*, not *what* the code already says.

### Output display convention

- Prefer `display()` for DataFrames when visual table or chart output helps.
- Use `.show()` to demonstrate truncation or when `display()` is unavailable.
- Use `.printSchema()` when schema inspection is the learning objective.
- Use `print()` only for scalars, strings, or other non-DataFrame output.

## What must never appear in a notebook

Apply the **Security and portability** and **Permitted author defaults**
sections in @docs/standards/coding-standards.md. That standard owns all
path, parameterization, secret, and learner-specific-value restrictions.

## Minimum privileges

If a notebook's examples require specific Unity Catalog privileges beyond
what a default learner might have, the module's `README.md` documents them
(see the **Minimum-privilege documentation pattern** in
`docs/standards/permissions-and-governance.md`). Do not repeat the privilege
list inside the notebook.

## Does not cover

- Code syntax and security — see `docs/standards/coding-standards.md`.
- Pedagogy and exercise design — see
  `docs/standards/teaching-guidelines.md`.
- Minimum-privilege documentation — see
  `docs/standards/permissions-and-governance.md`.
- Compute selection and runtime evidence — see
  `docs/standards/compute-validation-policy.md`.
