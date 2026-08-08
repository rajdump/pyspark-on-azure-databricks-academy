# Validation — 08 - Aggregations and Window Functions

Author-recorded runtime validation evidence for this module. Results below
were observed by running the notebooks in Azure Databricks (see
`docs/standards/compute-validation-policy.md` for the validation order).

## `01 - GroupBy and Basic Aggregations.py`

Validated on: 2026-08-08

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — `trip_enriched` read, output-grain checks, `groupBy().agg()` with aliases, three-count semantics, NULL-skipping `sum`/`avg` with `F.coalesce`, and payment-method exercise all ran as expected |
| Serverless | Not tested | Standard baseline confirmed; serverless not yet run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **not tested**

## `02 - Multi-column Keys, NULL Groups, and Filter Placement.py`

Validated on: 2026-08-08

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — `trip_enriched` read, `countDistinct` vs `groupBy` NULL-group behavior, composite-key grain, progressive WHERE vs HAVING filter placement, and borough / borough+payment exercise all ran as expected |
| Serverless | Not tested | Standard baseline confirmed; serverless not yet run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **not tested**

## `03 - Collections, Percentiles, and Distinct Counts.py`

Validated on: 2026-08-08

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — `trip_enriched` and `trip_driver_assignment` reads, `collect_list` / `collect_set`, `percentile_approx` p50/p90, `countDistinct` routes, and pickup-borough exercise all ran as expected |
| Serverless | Not tested | Standard baseline confirmed; serverless not yet run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **not tested**
