# Compute Selection and Validation Policy

This file is the canonical owner of compute selection and the order in which
notebooks are runtime-tested in Azure Databricks.

Direct readers: `docs/standards/notebook-authoring-checklist.md` and
`README.md`. Notebook commands receive this policy through the checklist when
compute guidance is relevant.

This repository does not keep per-module runtime evidence files. Running the
notebooks in Azure Databricks is the validation.

## Available compute

The course may use classic all-purpose compute (Standard or Dedicated access
mode), jobs compute, and serverless compute. **There is no single
course-wide compute type**. Select compute per module based on its APIs,
workload, and learning objectives.

## Notebook validation baseline

1. Test on **classic all-purpose Standard access mode** first.
2. If it passes, Standard is the confirmed baseline for that notebook — do
   not also repeat the same test on Dedicated.
3. Switch to **Dedicated** only when a verified API, library, isolation, or
   access-mode requirement makes Standard unsuitable. Document the exact
   reason in the module `README.md`.
4. **Never** switch to Dedicated to bypass a code defect. Before switching,
   always determine whether a failure comes from code, runtime, access
   mode, permissions, or a platform limitation.

## Serverless compatibility

- Establish the all-purpose Standard baseline *before* testing serverless.
- Treat serverless as a **compatibility check**, not the course-wide
  default.
- Serverless uses independently versioned environment versions, not
  Databricks Runtime version pins — do not claim a DBR version (e.g.
  17.3 LTS) applies to the serverless environment.
- Never claim compatibility without having actually tested it.
- If a lesson fails on serverless but passes on Standard, and it has clear
  learning value, keep it. Note a learner-facing gap in the module
  `README.md`. Do not invent an alternative just to make serverless "pass."

## Jobs and pipeline compute

- Add **jobs-compute validation** only when a module includes Lakeflow
  Jobs, job tasks, production automation, retries, or deployment behavior.
- Add **pipeline-managed validation** only when a module includes Lakeflow
  Pipelines.

## Does not cover

- Cursor's `/write-lesson`, `/validate-notebook`, and `/review-module` —
  those are authoring-quality checks, not a substitute for running notebooks
  in Azure Databricks.
- Unity Catalog privilege requirements — see
  `docs/standards/permissions-and-governance.md`.
