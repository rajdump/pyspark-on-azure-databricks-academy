Review an entire module folder for completeness and consistency. This is an
authoring-quality review in Cursor, not runtime validation. Never edit files.
Automatic-write restrictions are owned by the **Author-only writes** section
in `AGENTS.md`.

Response format: @.cursor/rules/notebook-command-output.mdc

Before reviewing, read @docs/standards/notebook-authoring-checklist.md and
apply its **Module-review manifest**, applicable **Conditional reads**, and
**Module-review bar**.

Steps:

1. Resolve the target module through **Command target selection**. If open
   files or recent context do not establish one unique match, ask once.
2. Load the **Module-review manifest** and applicable **Conditional reads**.
3. Apply the **Module-review bar** in the checklist. Cite `[file]` or
   `[file ~lines]` for every issue.
4. Reply **issues only** per the output rule. Do not edit files.

Follow the checklist's **Command boundaries**. Runtime validation belongs in
Azure Databricks per `docs/standards/compute-validation-policy.md`.

**Workflow note.** Run once after every planned notebook in the module passes
`/validate-notebook`. Its notebook spot checks are intentionally lighter and
do not replace per-notebook authoring-quality review.
