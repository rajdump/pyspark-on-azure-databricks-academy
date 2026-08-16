Scaffold a new learner-facing notebook for a specified target module.

Response format: @.cursor/rules/notebook-command-output.mdc

Before writing anything, read @docs/standards/notebook-authoring-checklist.md
and follow its **Scaffold manifest** and **Scaffold bar**.

Steps:

1. Determine the target module folder. If it's not obvious from the current
   context (open files, recent conversation), ask which module this
   notebook belongs to.
2. Determine the next notebook number within that module folder by
   inspecting existing `NN - Title.py` files there (start at `01` if none
   exist).
3. Apply the checklist's **Readiness precondition**. Use the module README's
   matching Notebooks row as the source of truth for the title and planned
   structure. Stop and report any design or roadmap-status gap.
4. If a `Not Started` module already contains a notebook, report the
   roadmap/filesystem inconsistency. Never change roadmap status as part of
   this command.
5. Create the correctly named Databricks source `.py` file and populate a
   **skeleton only** — objectives, section headings, setup
   placeholder, exercise placeholder, summary placeholder. Use `# TODO` or
   empty cells where code will go. **Do not write the full lesson**; the
   author runs `/write-lesson` next.
6. For shared data, put only manifest-verified tables, schemas, or paths in
   setup comments; do not invent columns.
