Scaffold a new learner-facing notebook for the current module.

Response format: @.cursor/rules/notebook-command-output.mdc

Before writing anything, read @docs/standards/notebook-authoring-checklist.md
and follow its **Required reads** and **Scaffold bar** sections.

Steps:

1. Determine the target module folder. If it's not obvious from the current
   context (open files, recent conversation), ask which module this
   notebook belongs to.
2. Read that module's `README.md`. Use the **Notebook navigation** entry
   for the next notebook number as the source of truth for topics and
   subtopics in the scaffold.
3. Determine the next notebook number within that module folder by
   inspecting existing `NN - Title.py` files there (start at `01` if none
   exist).
4. Ask for (or infer from context) a short, descriptive Title Case name for
   the notebook, following @docs/standards/naming-conventions.md.
5. Create the file as `NN - Title.py` inside the module folder, using the
   exact Databricks source-notebook structure from
   @docs/standards/notebook-writing.md: header line, `# COMMAND ----------`
   cell markers, a title/objectives markdown cell, and section structure
   aligned to README bullets.
6. Populate a **skeleton only** — objectives, section headings, setup
   placeholder, exercise placeholder, summary placeholder. Use `# TODO` or
   empty cells where code will go. **Do not write the full lesson**; the
   author runs `/write-lesson` next.
7. If the notebook will use the shared dataset, note the correct table(s)
   and schema from @docs/data/dataset-overview.md in setup comments — do
   not invent column names.

Do not update `COURSE_MODULES.md` or any file under `docs/validation/`.

After scaffolding, tell the author: **Next step — `/write-lesson` on this
notebook, then `/validate-notebook`.**
