Review an entire module folder for completeness and consistency.

Response format: @.cursor/rules/notebook-command-output.mdc

Reads:
- `docs/standards/notebook-authoring-checklist.md`
  - [[Module-review manifest]], [[Module-review bar]],
    [[Command target selection]]
  - [[Command boundaries]], which this command must follow
  - [[Conditional reads]], only those that apply to the target

Target: the module to review, resolved through [[Command target selection]].
If open files or recent context do not establish one unique match, ask once.

Guards: none after target resolution.

Steps:
1. Load the [[Module-review manifest]] and any applicable
   [[Conditional reads]].
2. Apply the [[Module-review bar]] to the module.

Verify: the reply is issues only, and every issue cites `[file]` or
`[file ~lines]`.

Boundaries:
- Automatic-write restrictions: `AGENTS.md`, [[Author-only writes]].
- This is an authoring-quality review in Cursor. Never edit files.
- This command does not perform runtime validation, which belongs in Azure
  Databricks per `docs/standards/compute-validation-policy.md`.
- Its notebook spot checks are intentionally lighter and do not replace
  per-notebook authoring-quality review.

Next: runtime validation in Azure Databricks.
