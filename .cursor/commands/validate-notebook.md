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

1. Determine the target notebook. If not obvious from open files or recent
   context, ask which module and notebook number (or file path).
2. **Scaffold guard.** If the file is still a scaffold from `/new-lesson`
   (placeholder structure with no runnable teaching demonstrations, or only
   empty/`# TODO` teaching cells), stop and tell the author to run
   `/write-lesson` first. Exercise `# TODO` markers in an otherwise complete
   lesson are expected — do not reject those.
3. Match the filename to the module README's **Notebooks table row**; the
   **Focus cell** is the topic source of truth.
4. Load the Validation manifest and applicable **Conditional reads**;
   compare voice and structure to the manifest's completed sibling (prior
   in-module notebook, or the previous module's last numbered notebook when
   the target is `01`).
5. Review the notebook against the **Full-lesson bar** and **Validation gate
   checks**. Cite specific cells — `[file ~lines]` — for every issue.
6. Reply **issues only** per the output rule. Do not edit files.

**Boundary.** Module-level sequence, naming, README design-complete, and
folder-wide evidence checks belong to `/review-module`, not this command.

**After a clean pass.** The author runs the notebook in Azure Databricks and
records evidence per `docs/standards/compute-validation-policy.md`. This
command does not perform runtime validation.
