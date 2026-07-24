# Compute Selection and Validation Policy

Canonical owner of compute-selection and validation-order rules for every
module. Referenced by `/validate-notebook`, `/review-module`, and the
`docs/validation/NN - Module Title.md` template — do not duplicate this
content elsewhere.

## Available compute

Classic all-purpose (Standard and Dedicated access modes), jobs compute, and
serverless compute. **There is no single course-wide compute type** —
compute is selected per module based on its APIs, workload, and learning
objectives.

## Notebook validation baseline

1. Test on **classic all-purpose Standard access mode** first.
2. If it passes, Standard is the confirmed baseline for that notebook — do
   not also repeat the same test on Dedicated.
3. Switch to **Dedicated** only when a verified API, library, isolation, or
   access-mode requirement makes Standard unsuitable. Document the exact
   reason in the module's validation record.
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
- Record compatibility as one of: `complete`, `partial`, `unsupported`, or
  `not applicable`.
- Document verified limitations — never claim compatibility without having
  actually tested it.
- If a lesson fails on serverless but passes on Standard, and it has clear
  learning value, keep it and record the serverless gap. Do not invent an
  alternative just to make serverless "pass."

## Jobs and pipeline compute

- Add **jobs-compute validation** only when a module includes Lakeflow
  Jobs, job tasks, production automation, retries, or deployment behavior.
- Add **pipeline-managed validation** only when a module includes Lakeflow
  Pipelines.

## Recording results

For every compute environment relevant to a module, the module's
`docs/validation/NN - Module Title.md` file records whether it was
**selected, excluded, unsupported, or not applicable — and why**. See that
file's template for the exact fields.

## What this policy does not cover

- Runtime validation *evidence itself* — that's the module's
  `docs/validation/` file, filled in by the author after running notebooks
  in Azure Databricks. Cursor's `/validate-notebook` and `/review-module`
  are authoring-quality checks in Cursor, not a substitute for this runtime
  validation.
- Unity Catalog privilege requirements — see
  `permissions-and-governance.md`.
