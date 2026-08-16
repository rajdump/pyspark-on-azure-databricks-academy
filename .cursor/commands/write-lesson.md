Write the full runnable content for a specified target notebook.

Response format: @.cursor/rules/notebook-command-output.mdc

Before writing anything, read @docs/standards/notebook-authoring-checklist.md
and follow its **Full-lesson manifest**, applicable **Conditional reads**,
**Full-lesson bar**, and **Validation gate checks**. Do not use prior chat
as a substitute for the manifest reads.

Steps:

1. Determine the target notebook. If not obvious from open files or recent
   context, ask which module and notebook number (or file path).
2. If the file does not exist, stop and tell the author to run `/new-lesson`
   first.
3. If the file is already a full lesson (runnable teaching demonstrations,
   not a scaffold), stop unless the author explicitly asked to replace
   content.
4. Match the filename to the module README's **Notebooks table row**; the
   **Focus cell** is the topic source of truth.
5. Load the Full-lesson manifest and applicable **Conditional reads**; use
   the manifest's completed sibling for voice and idiom drift (`F.count`
   form, aliasing style, comment patterns). When the target is `01`, use the
   previous module's last numbered notebook.
6. Replace scaffold content with a **full lesson**:
   - Implement every Focus cell topic, including runnable demonstrations
     for gotchas and API comparisons where behavior can be shown.
   - Remove scaffold placeholders and satisfy the **Full-lesson bar**.
   - Use only schema, path, and object details established by the manifest.
7. Self-check against the **Full-lesson bar** and **Validation gate checks**.
