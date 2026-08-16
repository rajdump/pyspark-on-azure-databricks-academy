Scaffold a new learner-facing notebook for a specified target module.

Response format: @.cursor/rules/notebook-command-output.mdc

Before writing anything, read @docs/standards/notebook-authoring-checklist.md
and follow its **Scaffold manifest** and **Scaffold bar**. Do not use prior
chat as a substitute for the manifest reads.

Steps:

1. Determine the target module folder (path, module number, or title). If
   it's not obvious from open files or recent conversation, ask once — do
   not guess from unrelated context.
2. Apply the checklist's **Readiness precondition**. When status is not
   `Started`, also report any stray `.py` files on disk as a
   roadmap/filesystem inconsistency. Never change `COURSE_MODULES.md`
   status as part of this command.
3. Select the notebook from the README **Notebooks table**: the first row in
   table order whose `NN - Title.py` file is missing. Build the filename
   from that row's `#` and `Notebook` columns. Stop if every planned row
   already has a file or if the target file already exists.
4. **Filesystem cross-check** — report (do not block on) any numbered `.py`
   files on disk that are not listed in the README Notebooks table.
5. Create the correctly named Databricks source `.py` file and populate a
   **scaffold only** that satisfies **Scaffold contents** in the checklist.
   Use `# TODO` or empty cells where code will go. **Do not write the full
   lesson**; the author runs `/write-lesson` next.
6. For shared data and Module 5 setup/cleanup targets, put only
   manifest-verified tables, schemas, paths, or config placeholders in setup
   comments; do not invent columns or learner-specific values.
