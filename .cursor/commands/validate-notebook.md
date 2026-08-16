Review the currently open (or specified) notebook for authoring-quality
issues. This is a Cursor-side, **read-only** check — not a substitute for
running the notebook in Azure Databricks. Never edit the notebook, change
`COURSE_MODULES.md` status, or produce or edit runtime validation evidence
in `docs/validation/`.

Response format: @.cursor/rules/notebook-command-output.mdc

Before reviewing, read @docs/standards/notebook-authoring-checklist.md and
apply its **Validation manifest**, applicable **Conditional reads**,
**Full-lesson bar**, and **Validation gate checks**. Do not use prior chat
as a substitute for the manifest reads.

Steps:

1. Determine the target notebook. Prefer the open module notebook when
   obvious. If only the module is named, select the **last** **Notebooks
   table** row whose `.py` file exists and is a **full lesson** per
   **Scaffold vs full lesson** in the checklist. If the author names a
   specific notebook, use that row. If no full lesson exists, stop and
   report: only scaffolds → `/write-lesson`; no files → `/new-lesson`. If
   not obvious from open files or recent context, ask once which module
   and notebook number (or file path).
2. Apply **Validation guards** in the **Validation manifest** — stop when a
   guard fails. Then load the **Validation manifest** and applicable
   **Conditional reads**; compare voice and structure per Full-lesson
   manifest item 8.
3. Match the filename to the module README's **Notebooks table** row per
   `docs/standards/naming-conventions.md`; the **Focus cell** is the topic
   source of truth.
4. Review the notebook against the **Full-lesson bar** and **Validation gate
   checks**. Cite specific cells — `[file ~lines]` — for every issue.
5. Reply **issues only** per the output rule. Do not edit files.

**Boundary.** Module-level sequence, naming, **Design-complete definition**,
and folder-wide evidence checks belong to `/review-module`, not this command.

**After a clean pass.** The author runs the notebook in Azure Databricks and
records evidence per `docs/standards/compute-validation-policy.md`. This
command does not perform runtime validation.
