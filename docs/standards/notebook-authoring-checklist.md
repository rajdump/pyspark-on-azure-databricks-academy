# Notebook Authoring Checklist

This file tells Cursor which sources to read for learner-notebook work and
what must be true at two content stages:

- The **Scaffold bar** defines a valid notebook scaffold.
- The **Full-lesson bar** defines a runnable lesson ready for
  authoring-quality review with `/validate-notebook`.

A **bar** is a set of pass criteria. This file is the canonical owner of both
bars and the command-specific read manifests. Direct readers are
`/new-lesson`, `/write-lesson`, `/validate-notebook`, `/review-module`,
`.cursor/rules/learner-notebooks.mdc`, and `AGENTS.md`.

## At a glance

| Command | Purpose | Apply from this checklist |
|---|---|---|
| `/new-lesson` | Create a scaffold only | Scaffold manifest and Scaffold bar |
| `/write-lesson` | Turn a scaffold into a full runnable lesson | Full-lesson manifest, applicable Conditional reads, Full-lesson bar, and Validation gate checks |
| `/validate-notebook` | Review one full lesson without editing it | Validation manifest, applicable Conditional reads, Full-lesson bar, and Validation gate checks |
| `/review-module` | Review module-wide consistency without editing files | Module-review manifest, applicable Conditional reads, and Module-review bar |

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

### Artifact and content-state terminology

- **Learner notebook:** the Databricks source `.py` artifact in a numbered
  module folder.
- **Scaffold:** a learner notebook in a structure-only state; it contains
  placeholders and no runnable teaching demonstrations. Teaching cells are
  empty or contain `# TODO`.
- **Full lesson:** a learner notebook with runnable teaching demonstrations
  for its planned concepts. Exercise `# TODO` markers are allowed.
- **`Focus` entry:** the entry in a module README's Notebooks table that owns
  the notebook's topics, subtopics, comparisons, gotchas, and exercise
  expectation. This is not a Databricks notebook cell.

Use **scaffold**, not *skeleton*. Use **authoring-quality review** for Cursor
review and **runtime validation** for execution in Azure Databricks.

### Command target selection

- Resolve a module from an existing module path, its module number, or its
  exact roadmap title. Do not use fuzzy or substring title matching. Stop and
  ask when the input has no unique match.
- An explicitly named notebook must map to exactly one Notebooks table row
  by number, title, or full path. Stop on an unplanned or ambiguous target.
- `/new-lesson` selects the first table row whose planned file is missing. An
  explicit later row is allowed only when every prior row has a file.
- `/write-lesson` selects the first table row whose file exists and is still
  a scaffold. For an explicit target, the file must exist. Every prior
  in-module row must have a file, and the immediately prior notebook must be
  a full lesson.
- `/validate-notebook` selects the last table row whose file exists and is a
  full lesson. For an explicit target, the file must exist; the Validation
  guards determine its content state. Every prior in-module row must have a
  file, and the immediately prior notebook must be a full lesson.
- `/review-module` resolves the module only; it does not select an individual
  notebook.

For Notebook 01, the Full-lesson and Validation manifests use the last
numbered notebook of the previous module when it exists and is a full lesson.
If that notebook is still a scaffold, stop and report the gap.

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

1. The target module README's full **Notebooks** table (including the target row,
   the next row when present, and per-row **Reads** when that column exists),
   plus **Prerequisites**, **Dataset**, and **Paths and outputs** when
   present, and **Minimum privileges required** when present.
2. The target module row in `COURSE_MODULES.md` for **Production Relevance**
   when applying production framing.
3. The full `docs/standards/notebook-writing.md`.
4. The full `docs/standards/teaching-guidelines.md`.
5. The full `docs/standards/coding-standards.md`.
6. The **Python identifiers** section in
   `docs/standards/naming-conventions.md`, plus **Unity Catalog objects**
   when the lesson names course objects.
7. The sections selected by **Dataset scope**.
8. One completed sibling notebook for voice and cell structure: use the
   immediately prior in-module notebook after **Command target selection**
   confirms that it exists and is a full lesson. For Notebook 01, read the
   last numbered notebook of the previous module when one exists.

Also apply **Conditional reads** below.

### Validation manifest (`/validate-notebook`)

Resolve the target through **Command target selection**, then read the
Full-lesson manifest, including the completed sibling for voice comparison.

**Validation guards** (stop before reviewing):

- The target `.py` file exists; if not, tell the author to run `/new-lesson`.
- The target is a **full lesson** per **Artifact and content-state
  terminology**. If it is still a scaffold, tell the author to run
  `/write-lesson`. Exercise `# TODO` markers in an otherwise complete lesson
  are expected.
- Command target selection confirmed that every prior in-module file exists
  and that the immediately prior notebook is a full lesson.

Then review the target notebook against the **Full-lesson bar** and
**Validation gate checks**. Validation is read-only and does not produce
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

Then apply the **Module-review bar** below. Module review is read-only
and does not produce runtime evidence.

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
create the notebook or change the module status. A missing or incomplete
module design routes to `/write-module-readme`; the author still owns the
roadmap status change. When roadmap status is not `Started`, also check the
module folder for existing `.py` files and report a
**roadmap/filesystem inconsistency** when present.

### Scaffold contents

Select the target through **Command target selection** (including
non-contiguous numbers such as `99` when planned). Build the filename from
that row's `#` and `Notebook` columns per
`docs/standards/naming-conventions.md`. Stop without creating a file if every
planned row already has a matching file, or if the named or selected target
file already exists.

- **Filesystem cross-check:** Report (do not block on) any numbered `.py`
  files on disk that are not listed in the README Notebooks table.

When readiness passes and a target row is selected, the scaffold is valid only
when all checks below pass:

- **Format:** It uses the required Databricks source format.
- **Planned structure:** Its section headings match the topics and subtopics
  in that row's **`Focus` entry**.
- **Placeholders:** It includes objectives, prerequisites, setup, summary,
  and a next-notebook pointer placeholder. Include an exercise placeholder
  only when the `Focus` entry plans an exercise or hands-on task; for
  write-only, utility, or no-exercise notebooks, use ordered concept-section
  placeholders per the `Focus` entry instead.
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

- **Planned coverage:** The module README's **Notebooks table `Focus` entry**
  for the target row is fully implemented. Planned topics, subtopics,
  comparisons, and gotchas have runnable demonstrations where behavior can
  be shown. When the `Focus` entry plans an exercise or hands-on task, the
  exercise matches that scope. Write-only, utility, or no-exercise notebooks
  implement the `Focus` entry through ordered concept sections and writes
  instead of a learner exercise.
- **Teaching order:** Worked examples come before any exercise section. When
  an exercise is planned, it applies the demonstrated pattern to slightly
  different data. Write-only and utility notebooks follow ordered concept
  sections per the `Focus` entry.
- **Required course structure:** The notebook includes objectives, setup,
  incremental teaching cells, a summary, and a next-notebook pointer.
- **Voice consistency (reviewer judgment):** The explanation style and
  progression are consistent with the teaching standard and completed
  sibling notebooks. Match idiom drift where the sibling establishes a
  pattern — for example `F.count` form, column aliasing style, and comment
  patterns. Borderline style differences are not blocking issues.
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

Module-level sequence, naming, **Design-complete definition**, and folder-wide
evidence checks belong to `/review-module`, not this list.

## Module-review bar (`/review-module`)

Apply after the **Module-review manifest** and applicable **Conditional
reads**. This bar summarizes module-level checks; the linked standards still
apply. A module passes `/review-module` only when all checks below pass:

- **README design:** The module `README.md` meets the **Design-complete
  definition** in `docs/standards/readme-authoring.md` and aligns with the
  target module row in `COURSE_MODULES.md`. It must not duplicate the full
  course roadmap, global standards, or Cursor instructions.
- **Naming:** Folder and notebook names follow **Module folders** and
  **Notebook files** in `docs/standards/naming-conventions.md`.
- **Notebook sequence:** Every **Notebooks table** row has a matching
  `NN - Title.py` file (including non-contiguous numbers such as `99` when
  planned). No unplanned numbered `.py` files on disk (inverse of the
  **Filesystem cross-check** in **Scaffold contents**).
- **Notebook spot checks:** Read each notebook far enough to check voice,
  structure, security, and dataset use per the manifest reads. This lighter
  gate does not substitute for running `/validate-notebook` on every notebook.
- **Dataset consistency:** Every DataFrame and file-read example matches the
  **Dataset scope** contract.
- **No leaked evidence:** Validation results, tokens, workspace URLs, or
  personal identifiers do not appear anywhere in the module folder.
- **No unfinished scaffolds:** No notebook is still a scaffold per
  **Artifact and content-state terminology**; report that `/write-lesson`
  must run first.
- **README minimum privileges:** When any notebook in the module uses Unity
  Catalog objects beyond default learner access, the module `README.md`
  documents them under **Minimum privileges required**.

## Command boundaries

- `/new-lesson` creates a scaffold only.
- `/write-lesson` writes one full lesson and self-checks it; it does not
  replace the independent `/validate-notebook` authoring-quality review.
- `/validate-notebook` applies per-notebook authoring checks without editing.
- `/review-module` applies the Module-review bar after all planned notebooks
  pass `/validate-notebook`; it does not repeat each Full-lesson review.
- Runtime validation and author-recorded evidence remain outside all four
  commands.

## Workflow and validation boundary

```text
/new-lesson → /write-lesson → /validate-notebook → fix and re-run if needed
→ repeat for every planned notebook → /review-module
→ commit and push to GitHub → pull into the Databricks Git folder
→ author validates the notebooks in Azure Databricks
```

Once every planned notebook passes `/validate-notebook`, run `/review-module`
once as a separate, lighter check for cross-notebook consistency. It does not
replace validating each notebook.

The Scaffold and Full-lesson bars cover authoring quality only. Runtime
validation is separate and follows
`docs/standards/compute-validation-policy.md`. Notebook commands do not
commit, push, pull, run Databricks, or record runtime results.
