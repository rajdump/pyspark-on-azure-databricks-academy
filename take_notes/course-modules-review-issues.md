# `COURSE_MODULES.md` Review Issues

This review separates unresolved roadmap problems from optional editorial
improvements. Roadmap status values are author-owned.

## Resolved Issues

- **Issues 2–6 — Module 9 and Phase II:** Aligned the purpose with the
  SQL-first design, corrected KPI source wording, added `PIVOT` / `UNPIVOT` /
  `TABLESAMPLE`, replaced “tests” with cross-API validation, and changed
  “query bilingually” to “query in Spark SQL.”
- **Issue 7 — Module 10 Delta framing:** Reframed the module as deepening
  Delta knowledge on existing managed tables.
- **Issue 9 — Module 11 contribution:** Clarified that the module applies
  least-privilege governance to existing Unity Catalog assets.
- **Issue 12 — Module 17 testing boundary:** Limited local `pytest` to pure
  Python helpers and assigned Spark data-quality checks to Databricks.
- **Issue 15 — Module 16 AQE depth:** Distinguished AQE tuning and plan
  analysis from Module 7's high-level awareness.

The former Module 2 validation-evidence item was removed after the author
recorded successful all-purpose and serverless validation for Notebook 05.

## Open Confirmed Issues

### 8. Module 10 and Module 13 have unclear `MERGE` ownership

- **Roadmap locations:** lines 61 and 69
- Module 10 lists `MERGE`; Module 13 lists `MERGE`-based upserts.
- The distinction between feature instruction and production application is
  not stated.
- **Suggested correction:** Assign basic `MERGE` syntax and semantics to
  Module 10, and idempotent incremental pipeline patterns to Module 13.

### 10. Module 12 does not explain the medallion transition

- **Roadmap location:** line 63
- The existing project uses `landing`, `processed`, and `curated` locations and
  objects.
- The roadmap introduces Bronze/Silver/Gold without explaining whether those
  layers map to or replace the existing structure.
- **Suggested correction:** Describe Module 12 as restructuring or mapping the
  existing pipeline into a medallion design.

### 11. Module 14 is optional but Module 19 requires it

- **Roadmap locations:** lines 70–71 and 80
- Module 14 is described as an optional variant, and Module 15 allows learners
  to proceed directly from Module 13.
- Module 19 requires Modules 1–18, which includes Module 14.
- **Suggested correction:** Either make Module 14 required, exclude it from the
  capstone prerequisites, or define separate capstone paths.

### 13. No module clearly owns the reusable `src/` structure

- **Roadmap locations:** lines 69–78
- Coding standards expect reusable `src/` code from Module 13 onward.
- Neither Module 13 nor Module 15 explicitly introduces that structure, even
  though Module 17 depends on testable non-Spark helpers.
- **Suggested correction:** Assign reusable package structure to Module 13 or
  Module 15.

### 14. Module 15 sounds like the deployment bundle starts there

- **Roadmap location:** line 71
- The roadmap says Module 15 produces the deployable job definition.
- A `databricks.yml` development stub already exists.
- **Suggested correction:** Say that Module 15 expands and productionizes the
  existing bundle stub.

## Editorial and Design Trade-offs

### 16. Phase introductions are uneven

- **Roadmap locations:** lines 31, 40–43, 57, 65, and 73
- Only Phase II has a descriptive flow summary.
- **Possible improvement:** Add one concise purpose or flow sentence to every
  phase, or remove the Phase II sentence.

### 17. The prerequisite convention is not explicit

- **Roadmap location:** line 38
- Module 4 lists Modules 2–3 but not Module 1, even though Module 1 establishes
  the platform environment.
- This is not necessarily wrong if the table lists only direct prerequisites.
- **Possible improvement:** State whether prerequisites are direct or
  cumulative instead of repeating every earlier module.

### 18. The running-use-case description duplicates the root README

- **Roadmap location:** lines 21–27
- The dataset list also appears in the root README.
- This creates a small maintenance point, but it makes the roadmap
  self-contained and links to the canonical dataset document.
- **Possible improvement:** Keep the short description or reduce it to a link
  if minimizing duplication is more important than self-contained context.

### 19. Module 5 prerequisite navigation appears in three places

- **Roadmap locations:** lines 45–47 and line 51
- Related links or requirements also appear in the root README and Module 5
  README.
- The roadmap note does not repeat all setup details; it adds requirements
  omitted from the table row and points to the canonical module guidance.
- **Possible improvement:** Keep one short warning and link, avoiding detailed
  setup duplication.

### 20. The status-ownership note is internal process guidance

- **Roadmap location:** lines 10–11
- The explanation of manual or chat-assisted updates and Cursor slash-command
  behavior is primarily useful to authors.
- **Possible improvement:** Move automation-specific guidance to `AGENTS.md`
  while retaining a short statement that this file owns roadmap status.

### 21. Module 11 includes authoring guidance

- **Roadmap location:** line 62
- “Inspect existing `rideshare_dev` — do not recreate Module 5 setup” is more
  detailed than most roadmap topics.
- It currently protects an important module boundary because no Module 11
  README exists yet.
- **Possible improvement:** Move the instruction into Module 11's README when
  that design file is created, leaving a short governance summary here.

### 22. The roadmap tables are difficult to scan

- **Roadmap locations:** lines 33–38, 49–55, 59–63, 67–71, and 75–80
- Eight wide columns contain substantial prose and require horizontal
  scrolling in many Markdown renderers.
- **Possible improvement:** Shorten major-topic and contribution cells, with
  detailed design deferred to module READMEs.

### 23. There is no table of contents

- The phase headings provide structure, but there are no quick links at the
  top.
- **Possible improvement:** Add a compact phase-level contents list if the
  roadmap grows significantly.

### 24. The `Started` status is currently unused

- **Roadmap location:** line 18
- No current module has this status.
- This is valid forward-looking workflow vocabulary rather than stale content.
- **Possible improvement:** None required.

### 25. The roadmap has no effort estimates

- No module duration or expected effort is provided.
- Estimates could help learners plan, but they also become stale and can imply
  an inappropriate pace.
- **Possible improvement:** Add estimates only if learner scheduling becomes a
  stated course requirement.

## Verified Non-Issues

- No broken links were found in `COURSE_MODULES.md`.
- Existing module folder names match the roadmap titles for Modules 1–9.
- The roadmap consistently excludes streaming and machine-learning content.
- The Module 5 versus Module 11 Unity Catalog responsibility split is broadly
  correct.
- No obviously stale module count is duplicated in the root README.

## Open Design Decisions

1. Clarify the Module 10 versus Module 13 Delta and `MERGE` boundary.
2. Define how Module 12 maps the current pipeline into medallion layers.
3. Resolve whether Module 14 is optional for the Module 19 capstone.
4. Assign ownership of the reusable `src/` structure.
5. Define how Module 15 evolves the existing deployment-bundle stub.
