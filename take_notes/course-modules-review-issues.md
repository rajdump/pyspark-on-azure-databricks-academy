# `COURSE_MODULES.md` Review Issues

Roadmap status values are author-owned. This file records review decisions
after the 20-module Phases III–V rewrite. Phase III is a **working design**
for the roadmap, not a notebook-authoring lock.

## Resolved Issues

- **Issues 2–6 — Module 9 and Phase II:** Aligned the purpose with the
  SQL-first design, corrected KPI source wording, added `PIVOT` / `UNPIVOT` /
  `TABLESAMPLE`, replaced “tests” with cross-API validation, and changed
  “query bilingually” to “query in Spark SQL.”
- **Issue 7 — Module 10 Delta framing:** Deepens Delta knowledge on existing
  managed tables (`MERGE` syntax only).
- **Issue 8 — `MERGE` ownership:** Module 10 teaches introductory `MERGE`
  syntax; Module 14 applies production incremental `MERGE` to the medallion
  pipeline.
- **Issue 9 — Module 11 contribution:** Applies least-privilege governance to
  existing Unity Catalog assets.
- **Issue 10 — Medallion transition:** Module 12 is paper design only. Module
  13 creates new `bronze` / `silver` / `gold` schemas and a new landing
  volume, copies repo `data/raw` there, and does **not** reuse Module 5
  `landing` / `processed` objects, curated folders, or teaching tables.
- **Issue 11 — Required path:** All modules are required. Direct
  prerequisites run `9 → 10 → … → 20`. Module 15 is the required batch
  Lakeflow Pipeline. Module 20’s prerequisite cell is Module 19.
- **Issue 12 — Testing boundary:** Local `pytest` is pure Python helpers
  only; Spark data-quality checks run in Databricks. Owner is Module 16.
- **Issue 13 — `src/` ownership:** Module 13 introduces the reusable `src/`
  package.
- **Issue 14 — Deployment bundle:** Deleted the premature `databricks.yml`
  stub (hardcoded host). Learners create `databricks.yml` from scratch in
  Module 18.
- **Issue 15 — AQE depth:** Module 17 owns AQE tuning and plan analysis
  beyond Module 7’s high-level awareness.
- **Issue 16 — Phase introductions:** Every phase heading now has one stable
  summary sentence.
- **Issue 17 — Prerequisite convention:** The roadmap states that
  prerequisite cells list direct dependencies and the learning path is
  cumulative unless stated otherwise.
- **Issue 19 — Module 5 prerequisite:** Removed the extra Module 5 paragraph.
  The Module 5 prerequisite cell links to additional environment and
  privilege requirements in the Module 5 README.
- **Issue 20 — Status-ownership note:** Removed from the learner-facing
  roadmap. Workflow enforcement stays in `AGENTS.md`.
- **Issue 21 — Module 11 topics cell:** Removed “do not recreate Module 5”
  from the roadmap table. Learner instruction belongs in the future Module
  11 README.
- **Issue 23 — Phase jump list:** Added a phase-level jump list after the
  status legend.
- **Phase II contributions:** Module 5 lands files for the Phase II learning
  pipeline (medallion lands its own copy in 13); Module 6 teaches cleaning
  patterns later reused in Silver; Module 7 builds teaching managed tables
  rebuilt in Gold; Module 8 produces teaching KPIs rebuilt as Gold; Module 9
  unchanged.
- **Phase III ownership:** Module 11 governs existing `landing` /
  `processed` only; Module 12 designs `bronze` / `silver` / `gold` and a new
  landing location without creating them; Module 13 creates those objects
  and the full-refresh tables.
- **Vault dashboard:** `vault/home.md` and `vault/progress.md` now follow
  the 20-module map. Historical `vault/decisions.md` entries stay as
  written; **D-021** records the new ownership.

The former Module 2 validation-evidence item was removed after the author
recorded successful all-purpose and serverless validation for Notebook 05.

## Deferred / no change

### 18. Running-use-case description

The short dataset paragraph also appears in the root README. Kept so the
roadmap stays self-contained and still links to
[`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).

### 22. Wide roadmap tables (deferred)

Eight-column tables remain. Revisit cell length after this rewrite only if
scanning is still a problem. Do not redesign the table in this pass.

### 24. Unused `Started` status (no change)

Keep `Started` in the legend as forward-looking workflow vocabulary.

### 25. Effort estimates (do not add)

Do not add module duration or effort estimates.

## Explicitly still deferred (not roadmap issues)

- Phase III refinement before notebooks are authored
- Medallion-create rules in `docs/standards/permissions-and-governance.md`
- Bronze / Silver / Gold column contracts
- Module 10–20 folders, READMEs, notebooks, `src/`, and tests
- Historical scratch notes (`NB07_personal_notes.md`,
  `root-readme-review-issues.md`)
