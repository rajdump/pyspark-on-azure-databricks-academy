# Validation — 02 - DataFrame Fundamentals

Author-recorded runtime validation evidence for this module. Results below
were observed by running the notebooks in Azure Databricks (see
`docs/standards/compute-validation-policy.md` for the validation order).

## `01 - Creating DataFrames.py`

Validated on: 2026-07-26

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — all four creation patterns and schema inspection cells ran as expected |
| Serverless | Passed | Same teachable path as Standard — create patterns, `printSchema()`, and row output all run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not repeated per validation baseline |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**
