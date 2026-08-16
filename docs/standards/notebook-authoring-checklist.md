# Notebook Authoring Checklist

This file tells Cursor which sources to read for notebook work and what must
be true at two stages:

- The **Scaffold bar** defines a valid notebook skeleton.
- The **Full-lesson bar** defines a complete lesson ready for authoring
  validation.

A **bar** is a set of pass criteria. This file is the canonical owner of both
bars and the shared read list. The notebook commands,
`.cursor/rules/learner-notebooks.mdc`, and `AGENTS.md` point here instead of
copying these rules.

## At a glance

| Command | Purpose | Apply from this checklist |
|---|---|---|
| `/new-lesson` | Create a skeleton only | Required reads, scoped additions, Scaffold bar |
| `/write-lesson` | Turn a skeleton into a full runnable lesson | Required reads, relevant Additional reads, Full-lesson bar |
| `/validate-notebook` | Review one full lesson without editing it | Required reads, relevant Additional reads, Full-lesson bar |
| `/review-module` | Review module-wide consistency without editing files | Required reads, scoped additions, relevant Additional reads, Full-lesson bar |

## Required reads (every notebook command)

Read every source below before scaffolding, writing, or checking a learner
notebook, or reviewing a module:

1. The module's own `README.md` (e.g. `02 - …/README.md`) — use its
   **Notebooks** table Focus cell for the target notebook number as the
   source of truth for planned topics, subtopics, comparisons, gotchas, and
   exercise scope.
2. @docs/standards/notebook-writing.md — structure, cell markers, format
3. @docs/standards/teaching-guidelines.md — pedagogy and explanation style
4. @docs/standards/coding-standards.md — Python/PySpark conventions
5. @docs/standards/naming-conventions.md — folder and notebook naming
6. @docs/data/dataset-overview.md — schemas, column names, join keys, physical layout

### Scoped additions to Required reads

For `/new-lesson` and `/review-module`, also read:

- @COURSE_MODULES.md — roadmap status and module-level scope
- @docs/standards/readme-authoring.md — module README structure and the
  design-complete definition

## Additional reads (when relevant)

These do not apply to a structure-only scaffold. Read them when writing or
checking a full lesson, or reviewing a module, under these conditions:

- @docs/standards/compute-validation-policy.md — when examples assume a
  specific compute type or access mode
- @docs/standards/permissions-and-governance.md — when examples use Unity
  Catalog objects beyond default learner access

## Scaffold bar (`/new-lesson`)

### Readiness precondition

Before creating a notebook, check both conditions:

- **Roadmap status:** The target module is `Started` in `COURSE_MODULES.md`.
- **README design:** The module `README.md` meets the design-complete
  definition in
  @docs/standards/readme-authoring.md.

If either check fails, `/new-lesson` stops and reports the gap. It does not
create the notebook or change the module status.

### Scaffold contents

When readiness passes, the scaffold is valid only when all checks below pass:

- **Format:** It uses the required Databricks source format.
- **Planned structure:** Its section headings match the topics and subtopics
  in the module README's Notebooks table Focus cell.
- **Placeholders:** It includes objectives, prerequisites, setup, exercise,
  and summary placeholders.
- **Dataset setup:** If the notebook will use the shared dataset, setup
  comments name the correct tables and schema or path from
  @docs/data/dataset-overview.md without inventing columns.
- **No lesson content yet:** `# TODO` or empty code cells are acceptable.
  Runnable lesson content is not required until `/write-lesson`.

## Full-lesson bar (`/write-lesson`)

This bar summarizes the final checks; the linked standards still apply. A
lesson is ready for `/validate-notebook` only when every applicable Required
and Additional read is followed and all checks below pass:

- **Planned coverage:** The module README's Notebooks table Focus cell is
  fully implemented. Planned topics, subtopics, comparisons, and gotchas
  have runnable demonstrations where behavior can be shown. The exercise
  matches its planned scope.
- **Teaching order:** Worked examples come before the exercise. The exercise
  applies the demonstrated pattern to slightly different data.
- **Course consistency:** The notebook follows the course voice and sibling
  structure: objectives, setup, incremental teaching cells, summary, and a
  next-notebook pointer.
- **Code and safe values:** Notebook code and authored content follow
  @docs/standards/coding-standards.md, including its **Security and
  portability** and **Permitted author defaults** sections.

If a check fails, the notebook is not ready. Fix the gap and run
`/validate-notebook` again.

## Workflow and validation boundary

```text
/new-lesson → /write-lesson → /validate-notebook → fix and re-run if needed
→ commit and push to GitHub → pull into the Databricks Git folder
→ author validates the notebook in Azure Databricks
```

After every notebook passes `/validate-notebook`, run `/review-module` as a
separate, lighter check for cross-notebook consistency. It does not replace
validating each notebook.

The Scaffold and Full-lesson bars cover authoring quality only. Runtime
validation is separate and follows
@docs/standards/compute-validation-policy.md. Notebook commands do not
commit, push, pull, run Databricks, or record runtime results.
