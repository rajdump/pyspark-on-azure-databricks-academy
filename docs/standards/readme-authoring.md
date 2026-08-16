# Module README Authoring Standard

This file is the canonical owner of module `README.md` structure and the
design-complete definition. A module README owns detailed module design; it
does not own the course roadmap, global standards, or Cursor workflows.

Direct consumers are `AGENTS.md`, `.cursor/rules/course-authoring.mdc`,
`.cursor/commands/write-module-readme.md`,
`.cursor/commands/review-module.md`, and
`docs/standards/notebook-authoring-checklist.md`. `/new-lesson` receives the
design-complete gate through the checklist. Do not duplicate the README
structure or gate in those consumers.

## Required structure

A module README uses the module number and title from @COURSE_MODULES.md as
its H1 and includes:

1. **Purpose** — the module's concise role in the course.
2. **Learning objectives** — observable learner outcomes.
3. **Prerequisites** — prior modules, concepts, tables, or setup required.
4. **Dataset notes** — inputs, outputs, paths, schemas, and relevant data
   dependencies. Use `## Dataset` when data inputs or contracts need
   explanation. Use `## Paths and outputs` when the module reads or creates
   persistent locations or objects. Use both when both concerns apply.
5. **Notebooks** — an ordered table defining each notebook's title and
   planned topics/subtopics.
6. **Exercises** — the practice expected in each notebook, recorded in the
   Notebooks table's Focus cell or in a dedicated section when module-level
   detail is needed.
7. **Minimum privileges required** — include when the module requires
   specific privileges beyond basic workspace access, using the pattern in
   @docs/standards/permissions-and-governance.md.

## Notebooks table

The table is ordered by zero-padded notebook number and uses these required
columns:

```markdown
| # | Notebook | Focus |
|---|---|---|
| 01 | Descriptive Title | Planned topics/subtopics; exercise |
```

Add a `Reads` column when input dependencies need to be explicit. Each row
maps to one planned `NN - Descriptive Title.py` file. The Focus cell is the
source of truth for the notebook's topics, subtopics, comparisons, gotchas,
and exercise scope.

## Design-complete definition

A module README is design-complete only when all checks below pass:

- Every applicable item in **Required structure** is present.
- Every planned notebook has a numbered row with a final title, Focus scope,
  and exercise expectation.
- Inputs, dependencies, persistent paths, and outputs are specific enough
  for scaffolding without invention.
- Required privileges are documented when the module goes beyond basic
  workspace access.
- No `TODO` placeholder or unresolved material design decision remains.

Before a module moves to `Started`—including when reopening a `Complete`
module—report missing design elements rather than changing status.

## Does not cover

- Course-wide purpose, sequence, production relevance, or module status —
  see `COURSE_MODULES.md`.
- Notebook source format and cell structure — see
  `docs/standards/notebook-writing.md`.
- Pedagogy and exercise design rules — see
  `docs/standards/teaching-guidelines.md`.
- Code, security, and naming rules — see
  `docs/standards/coding-standards.md` and
  `docs/standards/naming-conventions.md`.
- Runtime validation and evidence — see
  `docs/standards/compute-validation-policy.md`.
