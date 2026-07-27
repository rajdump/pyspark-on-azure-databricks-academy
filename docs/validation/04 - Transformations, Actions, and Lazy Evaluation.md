# Validation — 04 - Transformations, Actions, and Lazy Evaluation

Author-recorded runtime validation evidence for this module. Results below
were observed by running the notebooks in Azure Databricks (see
`docs/standards/compute-validation-policy.md` for the validation order).

## `01 - Transformations vs Actions.py`

Validated on: 2026-07-28

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — transformation vs action distinction, chain-then-action examples, and exercise path all ran as expected |
| Serverless | Passed | Same teachable path as Standard — all cells run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `02 - Lazy Evaluation and the Query Plan.py`

Validated on: 2026-07-28

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — lazy evaluation, `explain(mode="extended")`, optimizer filter pushdown demo, and Spark UI check all ran as expected |
| Serverless | Passed | Same teachable path as Standard — plan inspection and action cells all run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `03 - Narrow vs Wide Transformations.py`

Validated on: 2026-07-28

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Dedicated access mode | Passed | **Preferred teaching compute.** Multi-partition layout is visible; narrow `filter` (no `Exchange`) vs wide `groupBy` (`Exchange` / multi-stage) and Spark UI checks match the lesson |
| Classic all-purpose, Standard access mode | Passed | Notebook runs, but this hand-built sample may land in a **single partition**, which weakens the narrow vs wide / partition-inspection experience. Prefer Dedicated for the intended demo |
| Serverless | Passed | Notebook runs end-to-end; for the clearest partition / stage / `Exchange` teaching experience, prefer classic all-purpose **Dedicated** |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete** (functional); **Dedicated all-purpose recommended** for learner experience on partition and shuffle demos

## `04 - Common DataFrame Actions.py`

Validated on: 2026-07-28

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — `first` / `head` / `take` / `tail` / `isEmpty` / `toPandas` and driver-memory caution path all ran as expected |
| Serverless | Passed | Same teachable path as Standard — pull/check action cells all run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**
