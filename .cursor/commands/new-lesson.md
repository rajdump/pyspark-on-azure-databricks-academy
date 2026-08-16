Scaffold a new learner-facing notebook for a specified target module.

Response format: @.cursor/rules/notebook-command-output.mdc

Before writing anything, read @docs/standards/notebook-authoring-checklist.md
and follow its **Scaffold manifest** and **Scaffold bar**. Do not use prior
chat as a substitute for the manifest reads.

Steps:

1. Determine the target module folder (path, module number, or title). If
   it's not obvious from open files or recent conversation, ask once — do
   not guess from unrelated context.
2. Apply the checklist's **Readiness precondition**. If either check fails,
   stop and report the gap; do not create a file. When status is not
   `Started`, also report any stray `.py` files on disk as a
   roadmap/filesystem inconsistency. Never change `COURSE_MODULES.md`
   status as part of this command.
3. Select the notebook from the README **Notebooks table**: by default, the
   first row in table order whose `NN - Title.py` file is missing. If the
   author names a specific notebook, use that row only when every prior row
   already has a file; otherwise stop and report the gap. Build the filename
   from that row's `#` and `Notebook` columns per
   `docs/standards/naming-conventions.md`. Stop if every planned row already
   has a file, or if the named or selected target file already exists.
4. Apply the **Filesystem cross-check** in **Scaffold contents** — report;
   do not block on mismatches.
5. Create the correctly named Databricks source `.py` file and populate a
   **scaffold only** that satisfies **Scaffold contents** in the checklist
   (including **Dataset setup** and **Module 5 setup or cleanup** when
   applicable). Use facts from the Scaffold manifest's canonical sources
   only — do not invent columns or learner-specific values. Use `# TODO` or
   empty cells where code will go. **Do not write the full lesson**; the
   author runs `/write-lesson` next.
