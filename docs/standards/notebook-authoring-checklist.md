# Notebook Authoring Checklist

This file tells Cursor which sources to read for notebook work and what must
be true at two stages:

- The **Scaffold bar** defines a valid notebook scaffold.
- The **Full-lesson bar** defines a complete lesson ready for authoring
  validation.

A **bar** is a set of pass criteria. This file is the canonical owner of both
bars and the command-specific read manifests. Direct readers are
`/new-lesson`, `/write-lesson`, `/validate-notebook`, `/review-module`,
`.cursor/rules/learner-notebooks.mdc`, and `AGENTS.md`.

## At a glance

| Command | Purpose | Apply from this checklist |
|---|---|---|
| `/new-lesson` | Create a scaffold only | Scaffold manifest and Scaffold bar |
| `/write-lesson` | Turn a scaffold into a full runnable lesson | Full-lesson manifest, Full-lesson bar, and Validation gate checks |
| `/validate-notebook` | Review one full lesson without editing it | Validation manifest, Full-lesson bar, and Validation gate checks |
| `/review-module` | Review module-wide consistency without editing files | Module-review manifest and Full-lesson spot checks |

## How to read a manifest

- An `@path` means read the whole file.
- A backticked path followed by named headings is a scoped read. Locate those
  headings with search/read tools and read only those sections. Cursor has no
  section-level `@path` syntax. Do not preflight the whole file.
- Read the target notebook when writing or validating it. Read the relevant
  notebooks in the target module when reviewing a module.
- Never infer a missing schema, path, join key, course object name, or README
  design decision from a scoped read. Expand within the selected manifest's
  canonical sources or ask the author when the named sections do not
  establish the answer. Expand only as far as the missing fact requires, and
  do not switch to a different command's manifest.

### Dataset scope

Use `docs/data/dataset-overview.md` as one canonical file, but read only the
sections needed by the target:

- Modules 1–4: **Core data model**.
- A lesson that uses nested driver data: **Supplementary: `drivers` (nested
  XML)** in addition to the relevant core or pipeline section.
- Modules 5–8: **Core data model** and the matching subsection under
  **Module pipeline**.
- Modules 9+: **Core data model**, relevant subsections under **Module
  pipeline** for consumed outputs, and **Unity Catalog platform reference**
  when the lesson uses governed objects or Volume paths.
- Any lesson that creates, names, grants access to, or reads a Unity Catalog
  object or Volume path: **Unity Catalog platform reference**.

Expand to adjacent pipeline subsections when the target consumes an earlier
module's derived output and its contract is not repeated in the matching
subsection.

## Command read manifests

### Scaffold manifest (`/new-lesson`)

Read:

1. The target module's full `README.md`.
2. The target module row and its table headings in `COURSE_MODULES.md`.
3. The full `docs/standards/readme-authoring.md`.
4. The **Format** and **Notebook-level structure** sections in
   `docs/standards/notebook-writing.md`.
5. The **Audience assumptions** and **Explanation style** sections in
   `docs/standards/teaching-guidelines.md`.
6. The **Notebook files** section in
   `docs/standards/naming-conventions.md`.
7. The sections selected by **Dataset scope** when the notebook uses course
   data or persistent course objects.
8. For Module 5 setup or cleanup notebooks that configure learner-specific
   storage, the **Module 5 parameterization** section in
   `docs/standards/permissions-and-governance.md` and **Permitted author
   defaults** in `docs/standards/coding-standards.md`.

Coding standards are not part of this manifest because a scaffold contains
no runnable lesson code; item 8 is a scoped exception for safe setup
placeholders.

### Full-lesson manifest (`/write-lesson`)

Read:

1. The target module README's **Notebooks** row for the target and its
   **Prerequisites**, **Dataset**, and **Paths and outputs** sections when
   present, plus **Minimum privileges required** when present.
2. The full `docs/standards/notebook-writing.md`.
3. The full `docs/standards/teaching-guidelines.md`.
4. The full `docs/standards/coding-standards.md`.
5. The **Python identifiers** section in
   `docs/standards/naming-conventions.md`, plus **Unity Catalog objects**
   when the lesson names course objects.
6. The sections selected by **Dataset scope**.
7. One completed sibling notebook for voice and cell structure: prefer the
   prior numbered notebook in the same module. For Notebook 01 with no prior
   sibling, read the last numbered notebook of the previous module.

Also apply **Conditional reads** below.

### Validation manifest (`/validate-notebook`)

Read the Full-lesson manifest, including a completed sibling for voice
comparison, then review the target notebook against the **Full-lesson bar**
and **Validation gate checks**. Validation is read-only and does not produce
runtime evidence.

### Module-review manifest (`/review-module`)

Read:

1. The target module's full `README.md`.
2. The target module row and its table headings in `COURSE_MODULES.md`.
3. The full `docs/standards/readme-authoring.md`.
4. The **Module folders** and **Notebook files** sections in
   `docs/standards/naming-conventions.md`.
5. The **Format**, **Notebook-level structure**, **Notebook dependencies and
   execution state**, **Code cell conventions**, **Output display
   convention**, and **What must never appear in a notebook** sections in
   `docs/standards/notebook-writing.md`.
6. The **Explanation style**, **Structure patterns**, and **Production
   framing** sections in `docs/standards/teaching-guidelines.md`.
7. The **Style baseline**, **PySpark-specific conventions**, **Error handling
   in teaching notebooks**, **Security and portability**, and **Permitted
   author defaults** sections in `docs/standards/coding-standards.md`.
8. The **Python identifiers** section in
   `docs/standards/naming-conventions.md`.
9. The sections selected by **Dataset scope**.

Read each notebook far enough to check sequence, README coverage, consistent
voice and structure, security, and dataset use. This is a module-level spot
check, not a substitute for the Validation manifest on every notebook.

### Conditional reads

Except for the scoped Module 5 setup or cleanup exception in the Scaffold
manifest, these do not apply to a structure-only scaffold:

- Read the full `docs/standards/compute-validation-policy.md` when a full
  lesson or review assumes a compute type, access mode, cluster
  configuration, job, or pipeline.
- Read the full `docs/standards/permissions-and-governance.md` when a full
  lesson or review uses Unity Catalog objects beyond default learner access
  or must verify a module README's minimum-privilege section.

## Scaffold bar (`/new-lesson`)

### Readiness precondition

Before creating a notebook, check both conditions:

- **Roadmap status:** The target module is `Started` in `COURSE_MODULES.md`.
  `Complete` blocks scaffolding until the author sets `Started` again.
- **README design:** The module `README.md` meets the **Design-complete
  definition** in `docs/standards/readme-authoring.md`.

If either check fails, `/new-lesson` stops and reports the gap. It does not
create the notebook or change the module status. When readiness fails because
roadmap status is not `Started`, also check the module folder for existing
`.py` files and report a `Not Started` plus stray-notebook inconsistency when
present.

### Scaffold contents

Determine the target notebook from the module README's **Notebooks table** in
row order: select the **first row** whose `NN - Title.py` file does not yet
exist (including non-contiguous numbers such as `99` when planned). If the
author names a specific notebook, use that row only when every prior row
already has a file. Build the filename from that row's `#` and `Notebook`
columns per `docs/standards/naming-conventions.md`. Stop without creating a
file if every planned row already has a matching file, or if the named or
selected target file already exists.

- **Filesystem cross-check:** Report (do not block on) any numbered `.py`
  files on disk that are not listed in the README Notebooks table.

When readiness passes and a target row is selected, the scaffold is valid only
when all checks below pass:

- **Format:** It uses the required Databricks source format.
- **Planned structure:** Its section headings match the topics and subtopics
  in that row's **Focus cell**.
- **Placeholders:** It includes objectives, prerequisites, setup, summary,
  and a next-notebook pointer placeholder. Include an exercise placeholder
  only when the Focus cell plans an exercise or hands-on task; for
  write-only, utility, or no-exercise notebooks, use ordered concept-section
  placeholders per the Focus cell instead.
- **Dataset setup:** If the notebook will use the shared dataset, setup
  comments name the correct tables and schema or path from
  `docs/data/dataset-overview.md` without inventing columns.
- **Module 5 setup or cleanup:** When the target row is setup or cleanup,
  include config placeholders per Scaffold manifest item 8 — do not invent
  learner-specific values.
- **No lesson content yet:** `# TODO` or empty code cells are acceptable.
  Runnable lesson content is not required until `/write-lesson`.

## Full-lesson bar (`/write-lesson`, `/validate-notebook`)

This bar summarizes the final checks; the linked standards still apply. A
lesson is ready for `/validate-notebook` only when its manifest and
conditional reads are followed and all checks below pass:

- **Planned coverage:** The module README's **Notebooks table Focus cell**
  for the target row is fully implemented. Planned topics, subtopics,
  comparisons, and gotchas have runnable demonstrations where behavior can
  be shown. When the Focus cell plans an exercise or hands-on task, the
  exercise matches that scope. Write-only, utility, or no-exercise notebooks
  implement the Focus cell through ordered concept sections and writes
  instead of a learner exercise.
- **Teaching order:** Worked examples come before any exercise section. When
  an exercise is planned, it applies the demonstrated pattern to slightly
  different data. Write-only and utility notebooks follow ordered concept
  sections per the Focus cell.
- **Required course structure:** The notebook includes objectives, setup,
  incremental teaching cells, a summary, and a next-notebook pointer.
- **Voice consistency (reviewer judgment):** The explanation style and
  progression are consistent with the teaching standard and completed
  sibling notebooks. Borderline style differences are not blocking issues.
- **Code and safe values:** Notebook code and authored content follow
  `docs/standards/coding-standards.md`, including its **Security and
  portability** and **Permitted author defaults** sections.

`/write-lesson` self-check and `/validate-notebook` both apply this bar plus
**Validation gate checks**.

If a check fails, the notebook is not ready. Fix the gap and run
`/validate-notebook` again.

## Validation gate checks (`/write-lesson` self-check, `/validate-notebook`)

Apply after the **Full-lesson bar**. These are per-notebook authoring checks
in Cursor — not runtime validation and not module-level review.

- **Security and personal values:** No hardcoded tokens, workspace URLs,
  cluster IDs, or personal catalog/schema names anywhere in the notebook.
- **Compute assumptions:** Compute-type or access-mode claims are documented
  by the applicable conditional standard when the lesson assumes them.
- **README minimum privileges:** When the notebook uses Unity Catalog objects
  beyond default learner access, the module `README.md` documents them under
  **Minimum privileges required**.
- **Hidden session state:** The notebook runs after its own setup only — no
  dependency on variables, imports, or temp views from another notebook's
  session (see **Notebook dependencies and execution state** in
  `docs/standards/notebook-writing.md`).
- **Intentional failures:** Demonstrated failures use Markdown explanation
  and `# Expected: <ErrorType>` on the failing line (see **Error handling
  in teaching notebooks** in `docs/standards/coding-standards.md`).
- **No leaked evidence:** Runtime validation results, tokens, workspace
  URLs, or personal identifiers do not appear in notebook cells or comments.

Module-level sequence, naming, README design-complete, and folder-wide
evidence checks belong to `/review-module`, not this list.

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
`docs/standards/compute-validation-policy.md`. Notebook commands do not
commit, push, pull, run Databricks, or record runtime results.
