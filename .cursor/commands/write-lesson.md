Write the full runnable content for a specified target notebook.

Response format: @.cursor/rules/notebook-command-output.mdc

This command loads the **Required reads** from the
notebook-authoring-checklist. Do not use normal chat as a substitute — read
every required file before writing.

Before writing anything, read @docs/standards/notebook-authoring-checklist.md
and follow its **Required reads** and **Full-lesson bar** sections in full.
Also load @docs/standards/compute-validation-policy.md when the lesson
involves cluster configuration, and
@docs/standards/permissions-and-governance.md when it involves catalog or
schema privileges.

Steps:

1. Determine the target notebook. If not obvious from open files or recent
   context, ask which module and notebook number (or file path).
2. If the file does not exist, stop and tell the author to run `/new-lesson`
   first.
3. Read the module's `README.md` — its **Notebooks** table entry for that
   notebook is the topic source of truth.
4. Read one completed sibling notebook for voice and cell structure
   (e.g. the prior numbered notebook in the same module). If the target is
   Notebook `01` and no prior sibling exists yet, read the **last numbered
   notebook of the previous module** instead — this catches idiom drift
   across modules (e.g. `F.count` form, aliasing style, comment patterns).
5. Replace skeleton/`TODO` content with a **full lesson**:
   - Runnable PySpark for every README bullet (including gotchas and API
     comparisons — not prose-only).
   - Worked examples before the exercise; exercise uses a similar but not
     identical pattern.
   - Summary recap and pointer to the next notebook.
6. PySpark code follows @docs/standards/coding-standards.md.
7. Use column names and types from @docs/data/dataset-overview.md for any
   hand-built DataFrame.
8. After writing, mentally self-check against the **Full-lesson bar** in
   the checklist — the author should run `/validate-notebook` next.
