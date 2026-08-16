# Notebook Authoring Checklist

Canonical owner of the **shared read list**, **Scaffold bar**, and
**Full-lesson bar** for learner-notebook slash commands. Referenced by
`.cursor/commands/new-lesson.md`,
`.cursor/commands/write-lesson.md`, `.cursor/commands/validate-notebook.md`,
`.cursor/commands/review-module.md`, `.cursor/rules/learner-notebooks.mdc`,
and `AGENTS.md` — do not duplicate this list elsewhere; point to this file
instead.

## Required reads (every notebook command)

Before scaffolding, writing, or validating a learner notebook—or reviewing
an entire module—read **all** of the following:

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

For `/new-lesson` and `/review-module` only, also read:

- @COURSE_MODULES.md — roadmap status and module-level scope
- @docs/standards/readme-authoring.md — module README structure and the
  design-complete definition

## Additional reads (when relevant)

Read these when writing or checking a full lesson (or reviewing an entire
module), not when scaffolding structure alone:

- @docs/standards/compute-validation-policy.md — when examples assume a
  specific compute type or access mode
- @docs/standards/permissions-and-governance.md — when examples use Unity
  Catalog objects beyond default learner access

## Command roles

| Command | Writes files? | Output depth |
|---|---|---|
| `/new-lesson` | Yes — creates `NN - Title.py` | **Skeleton only** (sections, objectives, exercise placeholder). No full lesson. |
| `/write-lesson` | Yes — fills the target notebook | **Full runnable lesson** — meets the Full-lesson bar. |
| `/validate-notebook` | No — review only | Issues list; fix gaps, then re-run. |
| `/review-module` | No — review only | Module-wide issues list; fix gaps, then re-run. |

Recommended workflow:

```
/new-lesson  →  /write-lesson  →  /validate-notebook  →  (fix if needed)
→  commit and push to GitHub  →  pull into Databricks Git folder
→  Azure runtime validation by author
```

After `/validate-notebook` passes, the author manually commits and pushes to
GitHub, then pulls into the Databricks Git folder before running Azure
runtime validation. Notebook commands do not perform this repository
handoff automatically.

For a whole-module authoring check, run `/review-module` separately after
its notebooks pass `/validate-notebook`. Module review is a supplementary,
lighter gate for cross-notebook consistency; it does not replace validating
each notebook.

## Scaffold bar (`/new-lesson`)

### Readiness precondition

Both conditions must be true:

- The target module is `Started` in `COURSE_MODULES.md`.
- Its `README.md` meets the design-complete definition in
  @docs/standards/readme-authoring.md.

### Scaffold contents

- Correct Databricks source format and section headings aligned to the
  topics/subtopics in the target module README's **Notebooks** table entry.
- Objectives, prerequisites, setup placeholder, exercise placeholder,
  summary placeholder.
- When the planned notebook uses the shared dataset, setup comments identify
  the correct tables and schema or path from @docs/data/dataset-overview.md
  without inventing columns.
- `# TODO` or empty code cells are acceptable; runnable lesson content is
  **not** required until `/write-lesson`.

## Full-lesson bar (`/write-lesson`)

This bar is a summary acceptance gate, not a complete restatement of the
linked standards. A notebook is ready for `/validate-notebook` only when it
satisfies every applicable requirement in the Required and Additional reads
and all of the following:

- The module README's **Notebooks** table Focus cell is fully implemented:
  planned topics, subtopics, comparisons, and gotchas have **runnable**
  demonstrations rather than prose alone where behavior can be shown, and
  the exercise matches its planned scope.
- Worked examples appear **before** the exercise; the exercise repeats
  the demonstrated pattern on slightly different data.
- Voice and structure match sibling notebooks in the same module (objectives
  cell, setup, incremental cells, summary, next-notebook pointer).
- Notebook code and authored content follow
  @docs/standards/coding-standards.md, including its **Security and
  portability** and **Permitted author defaults** sections.

The Scaffold and Full-lesson bars cover authoring quality only; runtime
validation is separate (see
@docs/standards/compute-validation-policy.md).
