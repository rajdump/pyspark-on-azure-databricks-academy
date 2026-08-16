Create a numbered module folder and its design-complete `README.md`.

Response format: @.cursor/rules/notebook-command-output.mdc

Before writing, read:

- The target module row and its table headings in `COURSE_MODULES.md`
- @docs/standards/readme-authoring.md
- **Audience assumptions**, **Explanation style**, **Structure patterns**,
  **Exercise design conventions**, and **Production framing** in
  `docs/standards/teaching-guidelines.md`
- **Module folders** and **Notebook files** in
  `docs/standards/naming-conventions.md`
- `docs/data/dataset-overview.md`: **Core data model**; **Supplementary:
  `drivers` (nested XML)** when the module uses nested driver data; the
  matching **Module pipeline** subsection for Modules 5–8; **Unity Catalog
  platform reference** when the design creates, names, grants access to, or
  reads a Unity Catalog object or Volume path. Expand to an earlier pipeline
  subsection only when that contract is required and not repeated.
- The full `docs/standards/permissions-and-governance.md` when the design
  requires privileges beyond basic workspace access

Steps:

1. Determine the target module number. If it is not explicit, ask the
   author.
2. Use the matching roadmap row as the sole source
   for the module number, title, purpose, major topics, prerequisites,
   production relevance, final-project contribution, and current status.
   If no matching row exists, stop and report the gap.
3. Derive the exact zero-padded folder name as `NN - Module Title` and
   validate it against the naming section.
4. Inspect the target path without changing it. If `README.md` already
   exists, stop rather than overwriting it. An existing empty folder is
   acceptable.
5. Resolve the detailed notebook sequence, dataset dependencies, exercise
   scope, outputs, and minimum privileges needed for a design-complete
   README. If the roadmap and canonical docs do not establish a material
   design decision, ask the author before creating anything; do not invent
   details or leave `TODO` placeholders.
6. Once the design is complete, create the module folder if needed and write
   its `README.md` following the README standard. Keep
   roadmap-level facts aligned with `COURSE_MODULES.md` without copying the
   full roadmap entry.
7. Do not create learner notebooks, change `COURSE_MODULES.md` status, or
   write runtime validation evidence. Those are separate author-directed
   actions.
