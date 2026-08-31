# Notebook Content Standard

This file is the canonical owner of Databricks notebook source format,
notebook structure, cell boundaries, output-display conventions, pedagogy,
explanation style, and exercise-design rules for learner-facing course
content.

Direct reader: `docs/standards/notebook-authoring-checklist.md`. Notebook
commands and `.cursor/rules/learner-notebooks.mdc` receive these rules
through the checklist. `.cursor/rules/course-authoring.mdc` receives
[[#Audience assumptions]] and [[#Production framing]] when editing module
README learning objectives.

## Format

All learner notebooks are **Databricks source-format `.py` files** — never
`.ipynb`. This is fixed (see `README.md` for the technical baseline); this
document covers how to write within that format.

Required structure markers. The first markdown cell follows [[#Opening
cell]] — not a prerequisites block:

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # NN - Descriptive Title
# MAGIC
# MAGIC Short business or lesson context.
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC - Observable outcome 1
# MAGIC - Observable outcome 2

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

## Opening cell

The first `%md` cell is the opening. It contains only:

1. An H1 that exactly matches the notebook filename stem:
   `# NN - Descriptive Title` (ASCII hyphen, zero-padded number, no
   `Notebook ` prefix).
2. A short business or lesson-context introduction.
3. One Markdown H2 whose heading text is Learning objectives, then 3–6
   observable bullets for teaching notebooks. Utility, setup, and cleanup
   notebooks may have fewer bullets when the README contract has fewer
   real outcomes. Never pad.

Forbidden in the opening (and do not put `# DBTITLE 1,Introduction` on any
cell):

- `Reads`, `Writes`, `Prerequisites`, `Callback` / `Callbacks` labels
- Dataset note, `Source file`, `Compute`, `Setup` (as opening metadata)
- Scope note / “this notebook does not teach”
- Next-in-opening
- Topic tables / a “What you will learn” table
- no-exercise / no-write labels

One concise unlabeled sentence may name required run order or prior
persistent outputs when omitting it would cause failure. Unique callbacks
fold into that context or into the first later teaching `%md` cell; delete
a callback only when the same pointer already exists later.

Compute, access-mode, source-path, cleanup-level, output-grain, and catalog
notes belong on a post-opening setup or before-you-run `%md` cell, even
when they only weaken a demonstration rather than hard-fail it.

README Expected state never authorizes generated `.count()`, assertion,
read-back, or verification cells. That rule is owned by
`docs/standards/readme-authoring.md`.

## Notebook-level structure

Every learner notebook follows this shape:

1. **Opening cell** — [[#Opening cell]] only. Not prior-notebook
   assumptions as a Prerequisites block.
2. **Setup cell(s)** — imports, and reads of the shared dataset where
   relevant (see `docs/data/dataset-overview.md`).
3. **Planned concept sections** — section order follows the module README
   Lesson flow. Split unrelated concept paths into separate planned
   notebooks.
4. **Examples and exercises** — their teaching order follows
   [[#Structure patterns]].
5. **Summary cell** — brief recap of what was covered and a pointer to the
   next notebook.

### Notebook dependencies and execution state

- Each notebook must run after executing only its own top setup/config cell.
- Persistent prerequisites such as tables or Volume files belong in the
  unlabeled opening run-order sentence or on a later setup `%md` cell —
  not in the opening as a Prerequisites block.
- Never depend on variables, imports, or temporary views from another
  notebook; re-establish all in-memory state locally.
- Prior-notebook dependencies must use persistent tables or files, never
  hidden session state.

## Code cell conventions

- Follow the import conventions in `docs/standards/coding-standards.md`.
- Select DataFrame, SQL, and comparison cells using the
  [[#DataFrame and SQL teaching policy]].
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

Apply the [[Security and portability]] and [[Permitted author defaults]]
sections in `docs/standards/coding-standards.md`. That standard owns all
path, parameterization, secret, and learner-specific-value restrictions.

## Minimum privileges

If a notebook's examples require specific Unity Catalog privileges beyond
what a default learner might have, the module's `README.md` documents them
(see the [[Minimum-privilege documentation pattern]] in
`docs/standards/permissions-and-governance.md`). Do not repeat the privilege
list inside the notebook.

## Audience assumptions

Write for a learner who:
- Knows basic Python syntax
- Knows basic SQL, not advanced SQL
- Has little or no Apache Spark or Azure Databricks experience
- Has little or no production data engineering experience
- Is unfamiliar with local-authoring / Git / Databricks deployment workflows

**Explain unfamiliar concepts before using them.** If a notebook needs a
term or idea that hasn't been introduced yet, define it briefly in place
rather than assuming prior exposure.

## Explanation style

- Practical and code-focused over theory-heavy. Motivate *why* a concept
  matters with a concrete rideshare scenario before showing *how*.
- Beginner-friendly language — avoid unexplained jargon; when a technical
  term is introduced for the first time, define it in one sentence.
- Progressive complexity: within a notebook, and across the module, start
  simple and layer in complexity once the basics are demonstrated.
- Don't try to teach every PySpark API. Focus on what's needed to build
  reliable batch data engineering solutions — depth over breadth.

## Structure patterns

- Worked example first, exercise second — never ask a learner to attempt a
  pattern that hasn't been demonstrated.
- Give every newly introduced API a runnable example against the shared
  rideshare dataset before using it in an exercise.
- Call out common mistakes and gotchas explicitly (e.g. NULL-handling
  surprises, lazy-evaluation timing) rather than letting learners discover
  them by accident.
- Use the shared rideshare dataset (`docs/data/dataset-overview.md`) for
  examples by default; only switch datasets when a topic genuinely requires
  it, and explain why.

### DataFrame and SQL teaching policy

Teach DataFrame-first by default. Show SQL only when SQL is a planned
learning objective for that cell or section; the fact that both APIs are
idiomatic is not enough to require both.

Use side-by-side DataFrame and SQL examples only when comparing the two APIs
is itself the learning objective, as in
`06 - Querying DataFrames with SQL.py` in `02 - DataFrame Fundamentals`.
**Module 9 — Spark SQL and DataFrame Interoperability** formalizes
systematic dual-API treatment as its core purpose. See [[#Code cell
conventions]] for the structural code-cell rules that implement this
policy.

### Exercise design conventions

- Put optional hints after the exercise cell, progressing from general to
  specific.
- Put solutions in a clearly marked cell after the exercise; collapse or
  comment them out where the platform supports it.
- State the expected output shape or row count in the prompt for self-checks.
- Optional assertion cells after exercises are encouraged, not required.

## Production framing

Every module should connect its concept back to why it matters in a real
batch data engineering job — this is a job-focused course, not an academic
Spark tour. Where relevant, name the production concern a topic addresses
(reliability, idempotency, governance, performance, etc.) using the
"Production Relevance" language already established for that module in
`COURSE_MODULES.md`.

## Where this applies

- Module `README.md` learning-objective **tone and production framing**
  only; structure and concrete facts — see
  `docs/standards/readme-authoring.md`
- Learner notebooks (markdown cells, comments, exercise framing)

Which command applies which manifest and bar is owned by [[At a glance]] and
the command read manifests in
`docs/standards/notebook-authoring-checklist.md`.

## Does not cover

- Code syntax and security — see `docs/standards/coding-standards.md`.
- Module README structure and design-complete — see
  `docs/standards/readme-authoring.md`.
- Minimum-privilege documentation — see
  `docs/standards/permissions-and-governance.md`.
- Compute selection — see `docs/standards/compute-validation-policy.md`.
- Identifier naming — see `docs/standards/naming-conventions.md`.
