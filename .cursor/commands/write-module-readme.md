Create a numbered module folder along with a design-complete `README.md`.

Response format: @.cursor/rules/notebook-command-output.mdc

Reads:
- `COURSE_MODULES.md`
  - the `Phase N` heading for the named phase, its column headings, and that
    module's row
- `docs/standards/notebook-content-standard.md`
  - [[Audience assumptions]], [[Production framing]]
- `docs/standards/naming-conventions.md`
  - [[Module folders]], [[Notebook files]]
- `docs/data/dataset-overview.md`
  - only the headings that apply to this module
- `docs/standards/permissions-and-governance.md`
  - whole file, only when the design requires privileges beyond basic
    workspace access
- @docs/standards/readme-authoring.md — whole file, because every section
  governs the README this command writes

Target: the phase and module the author names as digits, `Phase ?, Module ?`
(roman numerals are not practical to type). If either is missing or not
digits, stop and reply exactly
`Name the phase and module (Phase ?, Module ?).` Do not guess from open files.

Guards — stop before proceeding when:
- the mapped `Phase` heading has no row for that module → report the gap
- a `README.md` already exists at the target path → report it and never
  overwrite it; an empty folder is fine
- a fact required by [[Canonical sources]] is absent from the reads above →
  ask the author for it; never guess, leave `TODO`, or write a partial README

Steps:
1. Map the phase digit to the matching `Phase` heading in `COURSE_MODULES.md`
   (`1` → `Phase I`, and so on) and use that module's row. Take the number,
   title, and other row fields from that row only.
2. Build the module folder name from that row's title, per [[Module folders]].
3. Create the folder if needed and write the `README.md` using only
   [[Notebook contracts]] (H2 `## Notebook NN — Title`).

Verify: the README meets [[Required structure]] and the
[[Design-complete definition]] in `docs/standards/readme-authoring.md`.

Boundaries:
- Automatic-write restrictions: `AGENTS.md`, [[Author-only writes]].
- This command does not create learner notebooks.

Next: `/new-lesson`.
