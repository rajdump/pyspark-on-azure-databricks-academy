Scaffold a new learner-facing notebook for the current module.

Before writing anything, read the standards files listed in step 3 below.

Steps:

1. Determine the target module folder. If it's not obvious from the current
   context (open files, recent conversation), ask which module this
   notebook belongs to.
2. Read that module's `README.md` (e.g. `01 - …/README.md`). Use the
   **Notebook navigation** entry for the next notebook number as the source
   of truth for topics and subtopics in the scaffold.
3. Read:
   - @docs/standards/notebook-writing.md
   - @docs/standards/teaching-guidelines.md
   - @docs/standards/naming-conventions.md
   - @docs/data/dataset-overview.md
4. Determine the next notebook number within that module folder by
   inspecting existing `NN - Title.py` files there (start at `01` if none
   exist).
5. Ask for (or infer from context) a short, descriptive Title Case name for
   the notebook, following the naming rules in `naming-conventions.md`.
6. Create the file as `NN - Title.py` inside the module folder, using the
   exact Databricks source-notebook structure from `notebook-writing.md`:
   header line, `# COMMAND ----------` cell markers, a title/objectives
   markdown cell, and section structure.
7. Populate it with a skeleton that follows `teaching-guidelines.md` and the
   matching README notebook bullets (objectives first, worked example before
   exercise placeholder) — not full lesson content unless explicitly asked
   to write it now.
8. If the notebook will use the shared dataset, reference the correct
   table(s) and schema from `dataset-overview.md` rather than inventing
   column names.

Do not update `COURSE_MODULES.md` or any file under `docs/validation/` as
part of this command — scaffolding only.
