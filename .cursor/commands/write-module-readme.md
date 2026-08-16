Create a numbered module folder along with a design-complete `README.md`.

Response format: @.cursor/rules/notebook-command-output.mdc

Before creating the module folder or README, read:

- The column headings and the row for the named phase and module in `COURSE_MODULES.md`
- @docs/standards/readme-authoring.md
- **Audience assumptions** and **Production framing** in
  `docs/standards/teaching-guidelines.md`
- **Module folders** and **Notebook files** in
  `docs/standards/naming-conventions.md`
- `docs/data/dataset-overview.md` — use only the headings that apply
  to this module
- The full `docs/standards/permissions-and-governance.md` when the design
  requires privileges beyond basic workspace access

Do not use prior chat as a substitute for these reads.

Steps:

1. **Target.** The user must name `Phase ?, Module ?` as digits
   (roman numerals are not practical to type). If either is missing
   or not digits, stop and reply exactly
   `Name the phase and module (Phase ?, Module ?).`
   Do not guess from open files.
2. **Roadmap row.** Map the phase digit to the matching `Phase`
   heading in `COURSE_MODULES.md` (`1` → `Phase I`, and so on) and
   use that module's row. If that heading has no such row, stop and
   report the gap. Take number, title, and the other row fields from
   that row only.
3. **Folder name.** Build the module folder name from that row's
   title, using **Module folders** in
   `docs/standards/naming-conventions.md`.
4. **Existing README.** Look at that path without creating it. If
   `README.md` is already there, stop. Do not overwrite it. An empty
   folder is fine.
5. **Missing design.** Every concrete fact in the README (table names,
   columns, paths, object names, privileges) must come from the files
   listed above. If the README needs one of those facts and it is not
   in those files, stop and ask the author for that fact. Do not
   guess, leave `TODO`, or write a partial README.
6. **Write.** Create the folder if needed and write a design-complete
   `README.md` per `docs/standards/readme-authoring.md`.

Do not create learner notebooks, change `COURSE_MODULES.md` status,
or write runtime validation evidence.
