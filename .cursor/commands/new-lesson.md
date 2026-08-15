Scaffold a new learner-facing notebook for a specified target module.

Response format: @.cursor/rules/notebook-command-output.mdc

Before writing anything, read @docs/standards/notebook-authoring-checklist.md
and follow its **Required reads** and **Scaffold bar** sections.

Steps:

1. Determine the target module folder. If it's not obvious from the current
   context (open files, recent conversation), ask which module this
   notebook belongs to.
2. Determine the next notebook number within that module folder by
   inspecting existing `NN - Title.py` files there (start at `01` if none
   exist).
3. Read that module's `README.md` and apply the README-design condition in
   the checklist's **Readiness precondition**. Use the **Notebooks** table
   entry for the next notebook number as the source of truth for its title,
   topics, and subtopics. If the condition or matching entry is not met, stop
   and report the design gap.
4. Read `COURSE_MODULES.md` and apply the roadmap-status condition in the
   checklist's **Readiness precondition**. If a `Not Started` module already
   contains a notebook, report the roadmap/filesystem inconsistency. If the
   condition is not met, stop and report it; any status change is a separate
   author-directed action and must not be made by this command.
5. Confirm the target notebook title follows
   @docs/standards/naming-conventions.md.
6. Create the file as `NN - Title.py` inside the module folder, using the
   exact Databricks source-notebook structure from
   @docs/standards/notebook-writing.md: header line, `# COMMAND ----------`
   cell markers, a title/objectives markdown cell, and section structure
   aligned to README bullets.
7. Populate a **skeleton only** — objectives, section headings, setup
   placeholder, exercise placeholder, summary placeholder. Use `# TODO` or
   empty cells where code will go. **Do not write the full lesson**; the
   author runs `/write-lesson` next.
8. If the notebook will use the shared dataset, note the correct table(s)
   and schema from @docs/data/dataset-overview.md in setup comments — do
   not invent column names.

After scaffolding, tell the author: **Next step — `/write-lesson` on this
notebook, then `/validate-notebook`.**
