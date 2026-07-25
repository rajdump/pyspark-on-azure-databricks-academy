Review the currently open (or specified) notebook for authoring-quality
issues. This is a Cursor-side quality check, not a substitute for running
the notebook in Azure Databricks — it never produces or edits runtime
validation evidence.

Check the notebook against all of the following, and cite specific cells
where it deviates:

- @docs/standards/notebook-writing.md — structure, cell markers, format
- @docs/standards/coding-standards.md — Python/PySpark code conventions
- @docs/standards/naming-conventions.md — file/notebook naming
- @docs/standards/teaching-guidelines.md — pedagogy and explanation style
- @docs/data/dataset-overview.md — schema/column-name correctness for any
  DataFrame or file-read example; flag any column name, type, or join key
  that doesn't match this reference

Also check for:

- Hardcoded tokens, workspace URLs, cluster IDs, or personal catalog/schema
  names (must never appear — this repo is authored as if already public)
- Compute-specific assumptions that should instead be documented per
  @docs/standards/compute-validation-policy.md
- Missing "Minimum privileges required" section if the notebook uses
  Unity Catalog objects beyond default access (see
  @docs/standards/permissions-and-governance.md)

Output format (issues only):
- If nothing deviates: one short line — e.g. "No authoring issues found."
- If something deviates: list only issues, grouped by standard — cell reference
  and specific fix for each. No pass tables, no "OK" rows, no long summaries.

Do not modify `COURSE_MODULES.md` or any file under
`docs/validation/`, and do not mark anything as runtime-validated — only
Azure Databricks execution can confirm that.
