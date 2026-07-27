# Validation — 03 - Data Cleaning, NULL Semantics, and Type Handling

Author-recorded runtime validation evidence for this module. Results below
were observed by running the notebooks in Azure Databricks (see
`docs/standards/compute-validation-policy.md` for the validation order).

## `01 - NULL Semantics and Predicate Correctness.py`

Validated on: 2026-07-27

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — three-valued logic demos, filter keep-TRUE behavior, `isNull` / `isNotNull`, `isin` + `None` trap, `eqNullSafe` / `<=>`, and reward/pickup-zone predicate chain all ran as expected |
| Serverless | Passed | Same teachable path as Standard — NULL semantics, predicate correctness, and chain cells all run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not repeated per validation baseline |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `02 - Missing, Blank, and Sentinel Values.py`

Validated on: 2026-07-27

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — blank/sentinel/`NaN` normalization to `NULL`, `na.drop` / `na.fill` / `na.replace`, and `F.coalesce` fallback cells all ran as expected |
| Serverless | Passed | Same teachable path as Standard — missing-value normalization and `na.*` / coalesce cells all run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not repeated per validation baseline |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `03 - Safe Type Casting.py`

Validated on: 2026-07-27

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — `cast` vs `try_cast`, rejected-row detection (`source.isNotNull() & casted.isNull()`), and unsupported type-pair demos all ran as expected |
| Serverless | Passed | Same teachable path as Standard — safe casting and rejected-row pattern cells all run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not repeated per validation baseline |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `04 - Numeric Overflow and Date-Timestamp Parsing.py`

Validated on: 2026-07-27

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — cast/arithmetic overflow, `try_sum` / `try_avg`, `to_date` / `to_timestamp`, and `try_to_date` / `try_to_timestamp` cells all ran as expected |
| Serverless | Passed | Same teachable path as Standard — overflow and date/timestamp parsing cells all run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not repeated per validation baseline |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**
