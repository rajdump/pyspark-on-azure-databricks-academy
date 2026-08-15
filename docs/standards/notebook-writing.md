# Notebook Writing Standards

Canonical owner of all notebook structure and formatting rules.

Referenced by (directly or through the checklist):
@docs/standards/notebook-authoring-checklist.md,
`.cursor/rules/learner-notebooks.mdc`,
@docs/standards/teaching-guidelines.md, and the `/new-lesson`,
`/write-lesson`, `/validate-notebook`, and `/review-module` commands — do
not duplicate this content elsewhere.

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
- Use `> **Note:**` for important asides and `> Warning:` for common
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
   relevant (see `docs/data/dataset-overview.md`).
3. **One concept path per notebook** — introduce a concept, show it, let the
   learner practice it, before moving to the next. Avoid cramming unrelated
   concepts into one notebook — split into another numbered notebook
   instead.
4. **Worked examples before exercises** — per
   @docs/standards/teaching-guidelines.md's Structure patterns: demonstrate
   the pattern with the rideshare dataset before the learner attempts it.
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
- Implement the DataFrame and SQL teaching policy in
  @docs/standards/teaching-guidelines.md: include DataFrame code cells by
  default, and include SQL cells only when SQL is a planned learning
  objective for that cell or section. Include side-by-side DataFrame and SQL
  cells only when API comparison is the learning objective. Module 9
  formalizes systematic dual-API treatment.
- Show, don't just tell: every new API introduced gets a runnable example
  against the rideshare dataset before being used in an exercise.
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

No hardcoded local-machine or learner-specific paths. Fixed
course-controlled Volume paths are permitted. For full path,
parameterization, and banned-value rules, see
@docs/standards/coding-standards.md's **Security and portability** and
**Permitted author defaults** sections.

## Minimum privileges

If a notebook's examples require specific Unity Catalog privileges beyond
what a default learner might have, the module's `README.md` documents them
(see `permissions-and-governance.md` for the pattern) — this is not
repeated inside the notebook itself.

## Does not cover

Code syntax standards (see `coding-standards.md`) or pedagogical approach
(see `teaching-guidelines.md`).
