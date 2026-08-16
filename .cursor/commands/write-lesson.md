Write the full runnable content for a specified target notebook.

Response format: @.cursor/rules/notebook-command-output.mdc

Before writing anything, read @docs/standards/notebook-authoring-checklist.md
and follow its **Full-lesson manifest**, applicable **Conditional reads**,
**Full-lesson bar**, and **Validation gate checks**. Do not use prior chat
as a substitute for the manifest reads.

Steps:

1. Determine the target notebook. If only the module is named, select the
   first **Notebooks table** row whose `.py` file exists but is still a
   scaffold per **Scaffold vs full lesson** in the checklist. If the author
   names a specific notebook, use that row. If no scaffold exists, stop and
   report: all full → run `/validate-notebook`; none exist → run
   `/new-lesson`. If not obvious from open files or recent context, ask once
   which module and notebook number (or file path).
2. If the file does not exist, stop and tell the author to run `/new-lesson`
   first.
3. **Scaffold guard.** If the file is still a scaffold (per **Scaffold vs
   full lesson**), continue. If it is already a full lesson, stop unless the
   author explicitly asked to replace content. Exercise `# TODO` markers in
   an otherwise complete lesson are expected — do not treat those as a
   scaffold.
4. Match the filename to the module README's **Notebooks table** row per
   `docs/standards/naming-conventions.md`; the **Focus cell** is the topic
   source of truth.
5. Load the **Full-lesson manifest** and applicable **Conditional reads**;
   apply the completed-sibling rule from manifest item 8.
6. Replace scaffold content with a **full lesson** that satisfies the
   **Full-lesson bar**. Use only schema, path, and object details from the
   manifest's canonical sources. Never change `COURSE_MODULES.md` status or
   edit `docs/validation/` as part of this command.
7. Self-check against the **Full-lesson bar** and **Validation gate checks**.

**Boundary.** Module-level sequence, naming, **Design-complete definition**,
and folder-wide evidence checks belong to `/review-module`, not this command.
