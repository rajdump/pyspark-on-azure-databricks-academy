Write the full runnable content for a specified target notebook.

Response format: @.cursor/rules/notebook-command-output.mdc

Before writing anything, read @docs/standards/notebook-authoring-checklist.md
and follow its **Full-lesson manifest**, applicable **Conditional reads**,
**Full-lesson bar**, and **Validation gate checks**. Do not use prior chat
as a substitute for the manifest reads.

Steps:

1. Resolve the module and notebook through **Command target selection**. If
   no scaffold exists, report: all planned files are full lessons →
   `/validate-notebook`; no planned files exist → `/new-lesson`.
2. Apply the target-selection and content-state guards. Stop on a missing
   file, missing prior file, unfinished prior notebook, or already-full
   target unless the author explicitly asked to replace that target.
   Exercise `# TODO` markers in an otherwise complete lesson are expected.
3. Match the filename to the module README's Notebooks table row per
   `docs/standards/naming-conventions.md`; its **`Focus` entry** is the topic
   source of truth.
4. Read the sources selected by the **Full-lesson manifest** and applicable
   **Conditional reads**, including the completed sibling from manifest
   item 8.
5. Replace scaffold content with a **full lesson** that satisfies the
   **Full-lesson bar**. Use only schema, path, and object details from the
   manifest's canonical sources. Never change `COURSE_MODULES.md` status or
   edit `docs/validation/` as part of this command.
6. Self-check against the **Full-lesson bar** and **Validation gate checks**.

Follow the checklist's **Command boundaries**.
