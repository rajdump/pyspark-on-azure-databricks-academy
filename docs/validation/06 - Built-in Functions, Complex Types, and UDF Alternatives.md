# Validation — 06 - Built-in Functions, Complex Types, and UDF Alternatives

Author-recorded runtime validation evidence for this module. Results below
were observed by running the notebooks in Azure Databricks (see
`docs/standards/compute-validation-policy.md` for the validation order).

## `01 - Column Transforms with Built-in Functions.py`

Validated on: 2026-08-02

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — landing Volume vs managed `trip_time_preview` loads, built-in transforms on `trip`, `trip_time`, and light `payment` examples, and exercise path all ran as expected |
| Serverless | Passed | Same teachable path as Standard — all cells run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `02 - Complex Types, Structs, Arrays, and explode.py`

Validated on: 2026-08-02

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — landing `drivers` XML read, struct/array access, `explode` / `explode_outer`, curated write to `…/curated/drivers_flat/`, and exercise path all ran as expected |
| Serverless | Passed | Same teachable path as Standard — all cells run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `03 - Cleaning and Curated Outputs.py`

Validated on: 2026-08-02

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — full-size controlled-bad CSV reads, cleaning chains, enrichment columns (`trip_distance_km`, `tip_percent_of_base`, etc.), curated writes to `…/curated/trip/` and `…/curated/payment/`, and exercise path all ran as expected |
| Serverless | Passed | Same teachable path as Standard — all cells run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `04 - Built-ins First, When (Not) to Use UDFs.py`

Validated on: 2026-08-02

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — curated `trip` / `payment` Parquet reads, built-in `F.when` vs Python UDF contrast on `tip_percent_of_base`, decision guidance, and read-only exercise framing all ran as expected |
| Serverless | Passed | Same teachable path as Standard — all cells run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**
