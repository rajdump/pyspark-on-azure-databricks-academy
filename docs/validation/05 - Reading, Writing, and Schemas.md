# Validation — 05 - Reading, Writing, and Schemas

Author-recorded runtime validation evidence for this module. Results below
were observed by running the notebooks in Azure Databricks (see
`docs/standards/compute-validation-policy.md` for the validation order).

## `01 - Unity Catalog Volumes and Data Landing.py`

Validated on: 2026-07-30

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — config cell, external location, catalog/schemas/volumes, landing copy, and verify path all ran as expected |
| Serverless | Passed | Same teachable path as Standard — all cells run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `02 - Reading CSV.py`

Validated on: 2026-07-30

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — CSV read options, explicit schema vs `inferSchema`, light reshape, practice write, and exercise path all ran as expected |
| Serverless | Passed | Same teachable path as Standard — all cells run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `03 - Reading JSON.py`

Validated on: 2026-07-30

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — JSON Lines read, explicit schema, light reshape, practice write, and exercise path all ran as expected |
| Serverless | Passed | Same teachable path as Standard — all cells run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `04 - Reading Parquet.py`

Validated on: 2026-07-30

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — Parquet read, embedded vs explicit schema, light reshape, practice write, and exercise path all ran as expected |
| Serverless | Passed | Same teachable path as Standard — all cells run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `05 - Reading XML.py`

Validated on: 2026-07-30

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — XML `rowTag` read, nested inspect without `explode`, practice write, and exercise path all ran as expected |
| Serverless | Passed | Same teachable path as Standard — all cells run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `06 - Reading Avro.py`

Validated on: 2026-07-30

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — Avro read, explicit schema, light reshape, practice write, and exercise path all ran as expected |
| Serverless | Passed | Same teachable path as Standard — all cells run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `07 - Write Patterns and Table Preview.py`

Validated on: 2026-07-30

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — save modes, partitioned write, Delta file write under `practice/`, managed `saveAsTable`, files vs tables, and exercise path all ran as expected |
| Serverless | Passed | Same teachable path as Standard — all cells run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `99 - Rideshare Project Cleanup and Reset.py`

Validated on: 2026-07-30

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — cleanup levels against course volumes/catalog ran as expected |
| Serverless | Passed | Same teachable path as Standard — all cells run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**
