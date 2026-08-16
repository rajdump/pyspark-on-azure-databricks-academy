# Module README Authoring Standard

This file is the canonical owner of module `README.md` structure and the
design-complete definition. A module README owns that module's detailed
design.

Direct readers: `AGENTS.md`, `.cursor/rules/course-authoring.mdc`,
`/write-module-readme`, and
`docs/standards/notebook-authoring-checklist.md`. `/new-lesson` and
`/review-module` receive the **Design-complete definition** through the
checklist.

## Canonical sources

Concrete facts in a module README — table names, columns, paths, object
names, and privileges — must come from:

- That module's row in `COURSE_MODULES.md`
- Applicable headings in `docs/data/dataset-overview.md`
- `docs/standards/permissions-and-governance.md` when the module
  requires privileges beyond basic workspace access

Do not guess or invent them. Derive learning objectives and the
Notebooks table from that row's Purpose and Major Topics.

## Required structure

Use the roadmap number and title as the H1 in this form:
`# Module N — Title` (not zero-padded).

Align **Purpose** and **Prerequisites** with that `COURSE_MODULES.md` row.
Do not copy **Production Relevance**, **Final-Project Contribution**, or
**Status**. **Major Topics** inform the Notebooks table; do not paste them
as a section.

A module README must include:

1. **Purpose** — the module's concise role in the course.
2. **Learning objectives** — observable learner outcomes written for the
   audience and production framing in
   `docs/standards/teaching-guidelines.md`.
3. **Prerequisites** — prior modules, concepts, tables, or setup required.
4. **Dataset** — inputs, outputs, paths, schemas, and dependencies.
   Every concrete fact must come from the canonical sources above.
   Do not guess or invent them. Use `## Dataset` when data inputs or
   contracts need explanation. Use `## Paths and outputs` when the
   module reads or creates persistent locations or objects. Use both
   when both apply.
5. **Notebooks** — the ordered table below. Record each notebook's exercise
   expectation in the `Focus` entry, or in a dedicated section when the
   module needs extra detail.
6. **Minimum privileges required** — follow **Minimum-privilege
   documentation pattern** in
   `docs/standards/permissions-and-governance.md`. List only what
   that module's examples require. Do not guess or invent object names
   or grants.

## Notebooks table

Order rows by zero-padded notebook number. Required columns:

```markdown
| # | Notebook | Focus |
|---|---|---|
| 01 | Descriptive Title | Planned topics/subtopics; exercise |
```

Add a `Reads` column when input dependencies need to be explicit. Each
row maps to one planned `NN - Descriptive Title.py` file. The `Focus` entry
is the source of truth for topics, subtopics, comparisons, gotchas, and
exercise scope.

## Design-complete definition

A module README is design-complete only when all of these pass:

- Every applicable item in **Required structure** is present.
- Every planned notebook has a numbered row with a final title, `Focus`
  scope, and exercise expectation. State explicitly when an exercise does
  not apply to a setup, cleanup, utility, or write-only notebook.
- Every concrete fact in the README comes from the canonical sources
  above. Do not guess or invent them.
- No `TODO` placeholder remains.

## Does not cover

- Roadmap sequence, production relevance, final-project contribution, or
  module status — see `COURSE_MODULES.md`.
- How to create the module folder and README — see `/write-module-readme`.
- Notebook source format and cell structure — see
  `docs/standards/notebook-writing.md`.
- Pedagogy and how to write exercises in notebooks — see
  `docs/standards/teaching-guidelines.md`.
- Code, security, and naming rules — see
  `docs/standards/coding-standards.md` and
  `docs/standards/naming-conventions.md`.
- Runtime validation and evidence — see
  `docs/standards/compute-validation-policy.md`.
