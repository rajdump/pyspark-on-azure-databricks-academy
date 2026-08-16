Review an entire module folder for completeness and consistency. This is an
authoring-quality check in Cursor, not runtime validation, and it never
writes roadmap status or validation evidence.

Response format: @.cursor/rules/notebook-command-output.mdc

Before reviewing, read @docs/standards/notebook-authoring-checklist.md and
apply its **Module-review manifest**, applicable **Conditional reads**, and
Full-lesson spot checks.

Given a module folder (ask which one if not obvious from context), check:

1. **README completeness** — the module's `README.md` meets the
   manifest's design-complete definition. It must not duplicate the full
   course roadmap, global standards, or Cursor instructions.
2. **Naming** — folder and notebook names use exact zero-padding and Title
   Case.
3. **Notebook sequence** — notebooks are numbered contiguously starting at
   `01`, and the README's Notebooks table matches the actual files present.
4. **Standards compliance across all notebooks** — spot-check each notebook
   using the manifest. This lighter gate does not substitute for running
   `/validate-notebook` on every notebook.
5. **Dataset consistency** — every DataFrame/file-read example matches
   the manifest's scoped dataset contract.
6. **No leaked evidence** — validation results, tokens, workspace URLs, or
   personal identifiers do not appear anywhere in the module folder.
