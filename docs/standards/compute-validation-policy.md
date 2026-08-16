# Compute Selection and Validation Policy

This file is the canonical owner of compute selection, validation order, and
the validation-record schema for every module.

Direct consumers are `docs/standards/notebook-authoring-checklist.md`,
`README.md`, `/write-lesson`, `/validate-notebook`, `/review-module`, and
module validation records. Other notebook workflows receive these rules
through the checklist when compute guidance is relevant. Do not duplicate
the compute or validation-record rules in those consumers.

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

Each module validation record uses these distinct fields and canonical
values:

- **Environment disposition** — the course's support decision for that
  compute environment: `supported`, `unsupported`, or `not applicable`.
  Explain the verified constraint or applicability decision behind it.
- **Test result** — what the author actually exercised: `passed`, `partial`,
  or `not tested`. The value `not tested` belongs only in this field.
- **Serverless compatibility** — `complete`, `partial`, `unsupported`, or
  `not applicable`. Record this summary only from serverless test evidence,
  or use `not applicable` when serverless genuinely does not apply. If
  serverless has not been tested, record `not tested` as its test result and
  leave compatibility unassigned until evidence exists.

These fields are the canonical validation-record schema; validation records
must not invent substitute fields or values. Never infer a result or
compatibility value from authoring review alone.

## Does not cover

- Runtime validation *evidence itself* — that's the module's
  `docs/validation/` file, filled in by the author after running notebooks
  in Azure Databricks. Cursor's `/write-lesson`, `/validate-notebook`, and
  `/review-module` are authoring-quality checks in Cursor, not a substitute
  for this runtime validation.
- Unity Catalog privilege requirements — see
  `docs/standards/permissions-and-governance.md`.
