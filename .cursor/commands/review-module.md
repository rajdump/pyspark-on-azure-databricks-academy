Review an entire module folder for completeness and consistency. This is an
authoring-quality check in Cursor, not runtime validation, and it never
writes roadmap status or validation evidence.

Given a module folder (ask which one if not obvious from context), check:

1. **README completeness** — the module's `README.md` has clear learning
   objectives, prerequisites, ordered notebook navigation, exercises,
   relevant datasets, and a "Minimum privileges required" section if
   applicable (@docs/standards/permissions-and-governance.md). It must not
   duplicate the full course roadmap, global standards, or Cursor
   instructions.
2. **Naming** — folder and notebook names follow
   @docs/standards/naming-conventions.md exactly, including zero-padding
   and Title Case.
3. **Notebook sequence** — notebooks are numbered contiguously starting at
   `01`, and the README's navigation list matches the actual files present.
4. **Standards compliance across all notebooks** — spot-check each notebook
   against @docs/standards/notebook-writing.md,
   @docs/standards/coding-standards.md, and
   @docs/standards/teaching-guidelines.md (equivalent to running
   `/validate-notebook` on each one).
5. **Dataset consistency** — every DataFrame/file-read example matches
   @docs/data/dataset-overview.md.
6. **No leaked evidence** — validation results, tokens, workspace URLs, or
   personal identifiers do not appear anywhere in the module folder.

Output a single findings summary grouped by check, with specific file/cell
references for anything that needs fixing.

Do not update `COURSE_MODULES.md` status or create/edit anything under
`docs/validation/` — those remain author-owned, filled in only after real
Azure Databricks runtime validation.
