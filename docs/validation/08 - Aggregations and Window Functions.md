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

## `04 - Pivot.py`

Validated on: 2026-08-12

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — `trip_enriched` read, long `groupBy` service-type counts, explicit-value `pivot` to wide layout, high-cardinality caution, and payment-method pivot exercise all ran as expected |
| Serverless | Not tested | Standard baseline confirmed; serverless not yet run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **not tested**

## `05 - Window Functions Fundamentals.py`

Validated on: 2026-08-12

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — `trip_enriched` and `trip_driver_assignment` reads, `groupBy` vs window comparison, window aggregates, ranking tie APIs, filter-after-rank Top-2 preview, and service-window exercise all ran as expected |
| Serverless | Not tested | Standard baseline confirmed; serverless not yet run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **not tested**

## `06 - Running Totals and Lag and Lead.py`

Validated on: 2026-08-12

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — `trip_enriched` read with NULL-date filter to 100 rows, default `RANGE` running-total trap, `ROWS` frame fix, `lag` / `lead`, and exercise all ran as expected |
| Serverless | Not tested | Standard baseline confirmed; serverless not yet run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **not tested**

## `07 - Top-N per Group and Sampling.py`

Validated on: 2026-08-12

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — `trip_enriched` and `trip_driver_assignment` reads, Top-N grain checks, tie-selection (`row_number` vs `rank`), NULL sort placement, `sample` / `sampleBy` / `randomSplit`, and Top-tips exercise all ran as expected |
| Serverless | Not tested | Standard baseline confirmed; serverless not yet run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **not tested**

## `08 - Build KPI Tables.py`

Validated on: 2026-08-12

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — `trip_enriched` and `trip_driver_assignment` reads; wrote `kpi_daily_trip_summary` (14), `kpi_zone_performance` (20), and `kpi_driver_productivity` (12) via `saveAsTable` overwrite; row-count verifies matched expected grains |
| Serverless | Not tested | Standard baseline confirmed; serverless not yet run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **not tested**
