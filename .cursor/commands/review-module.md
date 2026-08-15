Review an entire module folder for completeness and consistency. This is an
authoring-quality check in Cursor, not runtime validation, and it never
writes roadmap status or validation evidence.

Response format: @.cursor/rules/notebook-command-output.mdc

Before reviewing, read @docs/standards/notebook-authoring-checklist.md and
apply its **Required reads**, **Additional reads** (when relevant), and
**Full-lesson bar** as the review standard.

Given a module folder (ask which one if not obvious from context), check:

1. **README completeness** — the module's `README.md` meets the
   design-complete definition in @.cursor/rules/course-authoring.mdc. It must
   not duplicate the full course roadmap, global standards, or Cursor
   instructions.
2. **Naming** — folder and notebook names follow
   @docs/standards/naming-conventions.md exactly, including zero-padding
   and Title Case.
3. **Notebook sequence** — notebooks are numbered contiguously starting at
   `01`, and the README's Notebooks table matches the actual files present.
4. **Standards compliance across all notebooks** — spot-check each notebook
   against @docs/standards/notebook-authoring-checklist.md, including
   @docs/standards/compute-validation-policy.md when relevant. This is a
   lighter module-review gate for speed; it does not substitute for running
   `/validate-notebook` on every notebook.
5. **Dataset consistency** — every DataFrame/file-read example matches
   @docs/data/dataset-overview.md.
6. **No leaked evidence** — validation results, tokens, workspace URLs, or
   personal identifiers do not appear anywhere in the module folder.
