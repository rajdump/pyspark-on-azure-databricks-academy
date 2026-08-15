Create a numbered module folder and its design-complete `README.md`.

Response format: @.cursor/rules/notebook-command-output.mdc

Before writing anything, read `COURSE_MODULES.md` and
@docs/standards/readme-authoring.md. Also read:

- @docs/standards/teaching-guidelines.md
- @docs/standards/naming-conventions.md
- @docs/data/dataset-overview.md
- @docs/standards/permissions-and-governance.md

Steps:

1. Determine the target module number. If it is not explicit, ask the
   author.
2. Find that module's row in `COURSE_MODULES.md`. Use it as the sole source
   for the module number, title, purpose, major topics, prerequisites,
   production relevance, final-project contribution, and current status.
   If no matching row exists, stop and report the gap.
3. Derive the exact zero-padded folder name as `NN - Module Title` and
   validate it against @docs/standards/naming-conventions.md.
4. Inspect the target path without changing it. If `README.md` already
   exists, stop rather than overwriting it. An existing empty folder is
   acceptable.
5. Resolve the detailed notebook sequence, dataset dependencies, exercise
   scope, outputs, and minimum privileges needed for a design-complete
   README. If the roadmap and canonical docs do not establish a material
   design decision, ask the author before creating anything; do not invent
   details or leave `TODO` placeholders.
6. Once the design is complete, create the module folder if needed and write
   its `README.md` following @docs/standards/readme-authoring.md. Keep
   roadmap-level facts aligned with `COURSE_MODULES.md` without copying the
   full roadmap entry.
7. Do not create learner notebooks, change `COURSE_MODULES.md` status, or
   write runtime validation evidence. Those are separate author-directed
   actions.

After creation, tell the author to review the README, explicitly change the
module status to `Started`, and then run `/new-lesson`.
