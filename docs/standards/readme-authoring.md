# Module README Authoring Standard

This file is the canonical owner of module `README.md` structure and the
design-complete definition. A module README owns that module's detailed
design.

Direct readers: `AGENTS.md`, `.cursor/rules/course-authoring.mdc`,
`/write-module-readme`, and
`docs/standards/notebook-authoring-checklist.md`. `/new-lesson` and
`/review-module` receive the [[#Design-complete definition]] through the
checklist.

## Canonical sources

Concrete facts in a module README — table names, columns, paths, object
names, and privileges — must come from:

- That module's row in `COURSE_MODULES.md`
- Applicable headings in `docs/data/dataset-overview.md`
- `docs/standards/permissions-and-governance.md` when the module
  requires privileges beyond basic workspace access

Do not guess or invent them. Derive **Learning objectives** and the
notebook contracts (H2 `## Notebook NN — Title` sections) from that row's
Purpose and Major Topics.

## Required structure

Use the roadmap number and title as the H1 in this form:
`# Module N — Title` (not zero-padded).

Align **Purpose** and **Prerequisites** with that `COURSE_MODULES.md` row.
Do not copy **Production Relevance**, **Final-Project Contribution**, or
**Status**. **Major Topics** inform the notebook contracts; do not paste
them as a section.

A module README must include:

1. **Purpose** — the module's concise role in the course.
2. **Learning objectives** — observable learner outcomes written for the
   audience and production framing in
   `docs/standards/notebook-content-standard.md`.
3. **Prerequisites** — prior modules, concepts, tables, or setup required.
   Extra module-specific subsections remain legal (for example Module 5
   `### Before Notebook 01`). Never rename that heading.
4. **Dataset** — shared schemas and semantic contracts. Promote existing
   facts from Dataset, Prerequisite asset tables, and/or Paths and
   outputs. Do not invent schemas, row counts, or paths. Omit the heading
   only when the README has no data facts.
5. **Notebooks** — [[#Notebook contracts]] H2 sections. `/write-module-readme`
   writes only [[#Notebook contracts]].
6. **Minimum privileges required** — follow [[Minimum-privilege
   documentation pattern]] in
   `docs/standards/permissions-and-governance.md`. List only what
   that module's examples require. Do not guess or invent object names
   or grants.

`## Shared paths and assets` is omit-when-empty. It holds only module-wide
reused operational assets (for example Module 8 KPI formulas). Notebook-
specific objects belong in that notebook's Expected state. Expected state
may point at Dataset or Shared paths instead of copying them.

Cross-document links target unique H2 anchors (`#shared-paths-and-assets`,
`#before-notebook-01`, `## Notebook NN — Title`), never repeated
`### Expected state`.

New READMEs (`/write-module-readme`) and already-converted modules use this
skeleton. Fence the example so the H2 names are not live headings in this
standard:

```markdown
# Module N — Module Title
## Purpose
## Learning objectives
## Prerequisites
## Dataset
## Shared paths and assets
## Notebook 01 — Descriptive Title
### Context
### Learning objectives
### Lesson flow
### Expected state
### Exercise
### Boundaries
### Next
## Minimum privileges required
```

Omit `## Shared paths and assets` and `### Boundaries` when empty. Do not
create a learner file named `Notebook 01 — Title.py`. The README H2 uses an
em dash and a `Notebook NN` prefix; the `.py` filename uses
`docs/standards/naming-conventions.md`: `NN - Descriptive Title.py`
(ASCII hyphen, no `Notebook ` prefix). Take number and title from the H2,
then apply that naming rule.

## Notebook contracts

Each planned notebook is an H2 `## Notebook NN — Title` (zero-padded `NN`,
em dash). Required subsections:

- **Context** — why this notebook exists in the module.
- **Learning objectives** — observable outcomes for this notebook.
- **Lesson flow** — ordered topics, subtopics, comparisons, and gotchas.
- **Expected state** — only applicable labels: Input, Output, Expected
  rows, Important values, Expected failure. Use
  `Not applicable — no persistent data state` when true. May point at
  Dataset or Shared paths.
- **Exercise** — the planned task, or an explicit sentence that an
  exercise does not apply (setup, cleanup, utility, write-only).
- **Next** — intended learner progression, not table order. Cleanup/reset
  notebooks point back at the workflow that invokes them.

**Boundaries** is omit-when-empty except when named APIs must stay out of
scope (map those into Boundaries), or when there is unsafe-write risk,
object-damage risk, or a realistic scope overlap.

`Expected state` guides authors and reviewers. It does not automatically
create `.count()`, assertion, read-back, or verification cells.

## Design-complete definition

A module README is design-complete when it is **H2-only** and all of these
pass:

- Every planned notebook has [[#Notebook contracts]] subsections Context,
  Learning objectives, Lesson flow, Expected state, Exercise, and Next.
  Boundaries only when its trigger applies. Shared paths only when it has
  content.
- Every concrete fact in the README comes from the canonical sources
  above. Do not guess or invent them.
- No `TODO` placeholder remains.

`/write-module-readme` writes only the H2 shape.

## Does not cover

- Roadmap sequence, production relevance, final-project contribution, or
  module status — see `COURSE_MODULES.md`.
- How to create the module folder and README — see `/write-module-readme`.
- Notebook source format, cell structure, pedagogy, and exercises — see
  `docs/standards/notebook-content-standard.md`.
- Code, security, and naming rules — see
  `docs/standards/coding-standards.md` and
  `docs/standards/naming-conventions.md`.
- Runtime compute selection and Azure Databricks testing — see
  `docs/standards/compute-validation-policy.md`.
