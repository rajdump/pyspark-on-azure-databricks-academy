# Validation — 01 - Azure Databricks and Spark Foundations

Author-recorded runtime validation evidence for this module. Results below
were observed by running the notebooks in Azure Databricks (see
`docs/standards/compute-validation-policy.md` for the validation order).

## `01 - Introduction to Azure Databricks and the Workspace.py`

Validated on: 2026-07-25

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — Spark version and Databricks Runtime version (17.3 LTS) both printed as expected |
| Serverless | Partial | `spark.version` works; the DBR version lookup does not — serverless uses independently versioned environments, not DBR pins. Lesson kept as-is per policy (learning value on Standard baseline). |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not repeated per validation baseline |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **partial** (DBR-version lookup unavailable; all other cells run)

## `02 - Apache Spark Architecture and PySpark.py`

Validated on: 2026-07-25

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — `spark.version`, `spark.app.id`, and stand-in count cells ran; Spark UI path is available on classic |
| Serverless | Partial | `spark.version` and count cells work; `spark.app.id` is unavailable (Spark Connect / `CONFIG_NOT_AVAILABLE`). Spark UI gotcha also applies. Lesson kept as-is per policy (learning value on Standard baseline). |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not repeated per validation baseline |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **partial** (`spark.app.id` unavailable; count path runs)
