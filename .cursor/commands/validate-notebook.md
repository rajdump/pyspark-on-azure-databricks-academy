Review the currently open (or specified) notebook for authoring-quality
issues. This is a Cursor-side quality check, not a substitute for running
the notebook in Azure Databricks — it never produces or edits runtime
validation evidence.

Response format: @.cursor/rules/notebook-command-output.mdc

Before reviewing, read @docs/standards/notebook-authoring-checklist.md and
apply its **Validation manifest**, applicable **Conditional reads**, and
**Full-lesson bar**. Cite specific cells where the notebook deviates.

Also check for:

- Hardcoded tokens, workspace URLs, cluster IDs, or personal catalog/schema
  names (must never appear — this repo is authored as if already public)
- Compute-specific assumptions that are not documented by the applicable
  conditional standard
- Missing "Minimum privileges required" section in the module README if the
  notebook uses Unity Catalog objects beyond default access

If the notebook is still a skeleton (`TODO` placeholders, no runnable
examples), report that the author should run `/write-lesson` first — do not
review skeletons as full lessons.
