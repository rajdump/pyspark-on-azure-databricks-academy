Scaffold a new learner-facing notebook for a specified target module.

Response format: @.cursor/rules/notebook-command-output.mdc

Before writing anything, read @docs/standards/notebook-authoring-checklist.md
and follow its **Scaffold manifest** and **Scaffold bar**. Do not use prior
chat as a substitute for the manifest reads.

Steps:

1. Resolve the target module through **Command target selection**. If open
   files or recent conversation do not establish one unique match, ask once.
2. Apply the checklist's **Readiness precondition**. If either check fails,
   stop and report its prescribed remediation; do not create a file. Report
   any `.py` files found when status is not `Started` as a
   **roadmap/filesystem inconsistency**. Never change `COURSE_MODULES.md`
   status as part of this command.
3. Select and name the notebook through **Command target selection** and
   **Scaffold contents**. Stop on any target-selection guard.
4. Apply the **Filesystem cross-check** in **Scaffold contents** — report;
   do not block on mismatches.
5. Create the correctly named Databricks source `.py` file and populate a
   **scaffold only** that satisfies **Scaffold contents** in the checklist
   (including **Dataset setup** and **Module 5 setup or cleanup** when
   applicable). Use facts from the Scaffold manifest's canonical sources
   only — do not invent columns or learner-specific values. Use `# TODO` or
   empty cells where code will go. **Do not write the full lesson**; the
   author runs `/write-lesson` next.
