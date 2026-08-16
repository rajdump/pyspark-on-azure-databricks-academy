Review an entire module folder for completeness and consistency. This is an
authoring-quality check in Cursor, not runtime validation. Never edit files,
change `COURSE_MODULES.md` status, or produce or edit runtime validation
evidence in `docs/validation/`.

Response format: @.cursor/rules/notebook-command-output.mdc

Before reviewing, read @docs/standards/notebook-authoring-checklist.md and
apply its **Module-review manifest**, applicable **Conditional reads**, and
**Module-review bar**. Do not use prior chat as a substitute for the manifest
reads.

Steps:

1. Determine the target module folder (path, module number, or title). Prefer
   the open module folder or a notebook path when obvious. If not obvious
   from open files or recent context, ask once — do not guess from unrelated
   context.
2. Load the **Module-review manifest** and applicable **Conditional reads**.
3. Apply the **Module-review bar** in the checklist. Cite `[file]` or
   `[file ~lines]` for every issue.
4. Reply **issues only** per the output rule. Do not edit files.

**Boundary.** Per-notebook **Full-lesson bar** and **Validation gate checks**
belong to `/validate-notebook`, not this command. Runtime validation belongs
in Azure Databricks per `docs/standards/compute-validation-policy.md`.

**Workflow note.** Run after each notebook in the module passes
`/validate-notebook`; this command does not replace per-notebook validation.
