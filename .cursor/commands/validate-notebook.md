Review the currently open (or specified) notebook for authoring-quality issues.

Response format: @.cursor/rules/notebook-command-output.mdc

Reads:
- `docs/standards/notebook-authoring-checklist.md`
  - [[Validation manifest]], [[Validation guards]], [[Command target selection]]
  - [[Full-lesson manifest]], [[Full-lesson bar]], [[Validation gate checks]]
  - [[Command boundaries]], which this command must follow
  - [[Conditional reads]], only those that apply to the target
- `docs/standards/readme-authoring.md`
  - [[Notebook contracts]]
- `docs/standards/naming-conventions.md`
  - [[Notebook files]]

Target: the module and notebook, resolved through
[[Command target selection]]. If no full lesson exists, report: only scaffolds
→ `/write-lesson`; no planned files → `/new-lesson`.

Guards — stop before proceeding when:
- a [[Validation guards]] check fails → report which one

Steps:
1. Read the [[Validation manifest]], including the completed sibling selected
   by [[Full-lesson manifest]] item 7, then load any applicable
   [[Conditional reads]].
2. Match the filename to `## Notebook NN — Title` ([[Notebook contracts]]).
   Take number and title, then apply [[Notebook files]]. Lesson flow is the
   topic source of truth.
3. Review the notebook against the [[Full-lesson bar]], including
   [[Voice consistency]], and the [[Validation gate checks]].

Verify: the reply is issues only, and every issue cites `[file ~lines]`.

Boundaries:
- Automatic-write restrictions: `AGENTS.md`, [[Author-only writes]].
- This is a Cursor-side, read-only check. Never edit the notebook.
- This command does not perform runtime validation in Azure Databricks.

Next: the next planned notebook. After the final one passes, `/review-module`,
then runtime validation in Azure Databricks.
