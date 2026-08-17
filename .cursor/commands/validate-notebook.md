Review the currently open (or specified) notebook for authoring-quality
issues. This is a Cursor-side, **read-only** check — not a substitute for
running the notebook in Azure Databricks. Never edit the notebook.
Automatic-write restrictions are owned by the **Author-only writes** section
in `AGENTS.md`.

Response format: @.cursor/rules/notebook-command-output.mdc

Before reviewing, read @docs/standards/notebook-authoring-checklist.md and
apply its **Validation manifest**, applicable **Conditional reads**,
**Full-lesson bar**, and **Validation gate checks**.

Steps:

1. Resolve the module and notebook through **Command target selection**. If
   no full lesson exists, report: only scaffolds → `/write-lesson`; no
   planned files → `/new-lesson`.
2. Read the **Validation manifest**, including the completed sibling selected
   by Full-lesson manifest item 8, and then apply **Validation guards**. Stop
   when a guard fails. If they pass, load applicable **Conditional reads**.
   Compare voice and structure under **Voice consistency** in the
   **Full-lesson bar**.
3. Match the filename to the module README's **Notebooks table** row per
   `docs/standards/naming-conventions.md`; the **`Focus` entry** is the topic
   source of truth.
4. Review the notebook against the **Full-lesson bar** and **Validation gate
   checks**. Cite specific cells — `[file ~lines]` — for every issue.
5. Reply **issues only** per the output rule. Do not edit files.

Follow the checklist's **Command boundaries**.

**After a clean pass.** Continue with the next planned notebook. After the
final planned notebook passes, run `/review-module`, then perform runtime
validation in Azure Databricks and record evidence per
`docs/standards/compute-validation-policy.md`. This command does not perform
runtime validation.
