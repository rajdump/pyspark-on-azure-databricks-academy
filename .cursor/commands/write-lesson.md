Write the full runnable content for a specified target notebook.

Response format: @.cursor/rules/notebook-command-output.mdc

Reads:
- `docs/standards/notebook-authoring-checklist.md`
  - [[Full-lesson manifest]], [[Command target selection]],
    [[Full-lesson bar]], [[Validation gate checks]]
  - [[Command boundaries]], which this command must follow
  - [[Conditional reads]], only those that apply to the target
- `docs/standards/readme-authoring.md`
  - [[Notebooks table]]
- `docs/standards/naming-conventions.md`
  - [[Notebook files]]

Target: the module and notebook, resolved through
[[Command target selection]]. If no scaffold exists, report: all planned files
are full lessons → `/validate-notebook`; no planned files exist →
`/new-lesson`.

Guards — stop before proceeding when:
- the target file is missing, the prior planned file is missing, or the prior
  notebook is unfinished → report which one
- the target is already a full lesson → stop unless the author explicitly
  asked to replace it; exercise `# TODO` markers in an otherwise complete
  lesson do not make it unfinished

Steps:
1. Match the filename to its row in the module README's [[Notebooks table]],
   per [[Notebook files]]. That row's `Focus` entry is the topic source of
   truth.
2. Read the sources selected by the [[Full-lesson manifest]] and any
   applicable [[Conditional reads]], including the completed sibling from
   manifest item 8.
3. Replace the scaffold content with a full lesson, using only the schema,
   path, and object details found in the manifest's canonical sources.

Verify: the lesson satisfies the [[Full-lesson bar]] and
[[Validation gate checks]].

Boundaries:
- Automatic-write restrictions: `AGENTS.md`, [[Author-only writes]].
- This command does not perform the authoring-quality review or runtime
  validation.

Next: `/validate-notebook`.
