Write the full runnable content for a specified target notebook.

Response format: @.cursor/rules/notebook-command-output.mdc

Before writing anything, read @docs/standards/notebook-authoring-checklist.md
and follow its **Full-lesson manifest**, applicable **Conditional reads**,
and **Full-lesson bar**. Do not use prior chat as a substitute for the
manifest reads.

Steps:

1. Determine the target notebook. If not obvious from open files or recent
   context, ask which module and notebook number (or file path).
2. If the file does not exist, stop and tell the author to run `/new-lesson`
   first.
3. Use the module README's matching Notebooks row as the topic source of
   truth.
4. Use the manifest's completed sibling to catch voice and idiom drift
   (`F.count` form, aliasing style, comment patterns).
5. Replace skeleton/`TODO` content with a **full lesson**:
   - Implement every README bullet, including runnable demonstrations for
     gotchas and API comparisons where behavior can be shown.
   - Remove scaffold placeholders and satisfy the Full-lesson bar.
   - Use only schema, path, and object details established by the manifest.
6. Self-check the completed notebook against the Full-lesson bar.
