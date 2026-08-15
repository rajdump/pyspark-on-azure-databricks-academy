# Module README Authoring Standard

Canonical owner of module `README.md` structure and the design-complete
definition. Module READMEs own detailed module design; they must not
duplicate the full course roadmap, global standards, or Cursor instructions.

## Referenced by

- `AGENTS.md`
- `.cursor/rules/course-authoring.mdc`
- `.cursor/commands/write-module-readme.md`
- `.cursor/commands/review-module.md`
- `docs/standards/notebook-authoring-checklist.md`

## Required structure

A module README uses the module number and title as its H1 and includes:

1. **Purpose** — the module's concise role in the course.
2. **Learning objectives** — observable learner outcomes.
3. **Prerequisites** — prior modules, concepts, tables, or setup required.
4. **Dataset notes** — inputs, outputs, paths, schemas, and relevant data
   dependencies. Use `## Dataset`, `## Paths and outputs`, or both, according
   to the module's needs.
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

A module README is design-complete only when all applicable required
structure above is specific enough to scaffold every planned notebook
without inventing content. Before a module moves to `Started`—including when
reopening a `Complete` module—report missing design elements rather than
changing status.
