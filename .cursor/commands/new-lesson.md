Scaffold a new learner-facing notebook for a specified target module.

Response format: @.cursor/rules/notebook-command-output.mdc

Reads:
- `docs/standards/notebook-authoring-checklist.md`
  - [[Scaffold manifest]], [[Command target selection]]
  - [[Scaffold bar]], including [[Readiness precondition]] and
    [[Scaffold contents]]

Target: the module to scaffold into, resolved through
[[Command target selection]]. If open files or recent conversation do not
establish one unique match, ask once.

Guards — stop before proceeding when:
- either [[Readiness precondition]] check fails → report its prescribed
  remediation and create no file; when roadmap status is not `Started`, also
  report any numbered `.py` files in the module folder as a
  [[roadmap/filesystem inconsistency]]
- a target-selection guard in [[Scaffold contents]] trips → stop without
  creating a file

Steps:
1. Select and name the notebook through [[Command target selection]] and
   [[Scaffold contents]].
2. Apply the [[Filesystem cross-check]] — report mismatches, do not block on
   them.
3. Create the correctly named Databricks source `.py` file and populate a
   scaffold, including [[Dataset setup]] and [[Module 5 setup or cleanup]]
   when applicable. Use `# TODO` or empty cells where code will go, and take
   facts only from the [[Scaffold manifest]] canonical sources — never invent
   columns or learner-specific values.

Verify: the scaffold satisfies [[Scaffold contents]] and the [[Scaffold bar]].

Boundaries:
- Automatic-write restrictions: `AGENTS.md`, [[Author-only writes]].
- This command does not write the full lesson.

Next: `/write-lesson`.
