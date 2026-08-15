# Notebook Authoring Checklist

Canonical owner of the **shared read list** for learner-notebook slash
commands. Referenced by `.cursor/commands/new-lesson.md`,
`.cursor/commands/write-lesson.md`, `.cursor/commands/validate-notebook.md`,
`.cursor/rules/learner-notebooks.mdc`, and `AGENTS.md` — do not duplicate
this list elsewhere; point to this file instead.

## Required reads (every notebook command)

Before scaffolding, writing, or validating a learner notebook, read **all**
of the following:

1. The module's own `README.md` (e.g. `02 - …/README.md`) — use the
   **Notebook navigation** entry for the target notebook number as the
   source of truth for topics and subtopics.
2. @docs/standards/notebook-writing.md — structure, cell markers, format
3. @docs/standards/teaching-guidelines.md — pedagogy and explanation style
4. @docs/standards/coding-standards.md — Python/PySpark conventions
5. @docs/standards/naming-conventions.md — folder and notebook naming
6. @docs/data/dataset-overview.md — schemas, column names, join keys, physical layout

## Additional reads (validate and review only)

Read these when checking a notebook (or an entire module), not when
scaffolding structure alone:

- @docs/standards/compute-validation-policy.md — when examples assume a
  specific compute type or access mode
- @docs/standards/permissions-and-governance.md — when examples use Unity
  Catalog objects beyond default learner access

## Command roles

| Command | Writes files? | Output depth |
|---|---|---|
| `/new-lesson` | Yes — creates `NN - Title.py` | **Skeleton only** (sections, objectives, exercise placeholder). No full lesson. |
| `/write-lesson` | Yes — fills the target notebook | **Full runnable lesson** — all README bullets demonstrated, worked examples before exercise. |
| `/validate-notebook` | No — review only | Issues list; fix gaps, then re-run. |

Recommended workflow:

```
/new-lesson  →  /write-lesson  →  /validate-notebook  →  (fix if needed)  →  Azure Databricks runtime validation by author
```

Do not use normal chat (“write the full lesson”) as a substitute for
`/write-lesson` — chat may not load every required standard; the slash
command must.

## Full-lesson bar (`/write-lesson`)

A notebook is ready for `/validate-notebook` when it meets all of the
following:

- Every bullet under that notebook's **Notebook navigation** entry in the
  module README has a **runnable** demonstration (not prose-only for
  gotchas or API comparisons).
- Worked examples appear **before** the exercise; the exercise repeats
  the demonstrated pattern on slightly different data.
- Voice and structure match sibling notebooks in the same module (objectives
  cell, setup, incremental cells, summary, next-notebook pointer).
- PySpark code follows `coding-standards.md` (including `F` imports and
  `# noqa: F821` on Databricks-provided `spark` where needed).
- No secrets, workspace URLs, cluster IDs, or personal catalog/schema names.
  Use course object names from `docs/data/dataset-overview.md`. Module 5
  Notebooks 01/99 may keep author Azure defaults in the Tier 1 config cell
  for learners to overwrite — that is intentional, not a personal UC rename.
- Do not update `COURSE_MODULES.md` or anything under `docs/validation/`.

## Scaffold bar (`/new-lesson`)

- Before scaffolding, verify the target module is `Started` in
  `COURSE_MODULES.md`. If it is `Not Started` or `Complete`, stop; `/new-lesson`
  never changes roadmap status.
- The module `README.md` must include objectives, prerequisites, ordered
  **Notebook navigation** with an entry for the target notebook, exercises,
  dataset notes, and minimum privileges when applicable.
- Correct Databricks source format and section headings aligned to the
  README navigation bullets.
- Objectives, prerequisites, setup placeholder, exercise placeholder,
  summary placeholder.
- `# TODO` or empty code cells are acceptable; runnable lesson content is
  **not** required until `/write-lesson`.
