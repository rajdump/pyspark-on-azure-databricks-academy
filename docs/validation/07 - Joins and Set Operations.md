# Validation — 07 - Joins and Set Operations

Author-recorded runtime validation evidence for this module. Results below
were observed by running the notebooks in Azure Databricks (see
`docs/standards/compute-validation-policy.md` for the validation order).

## `01 - Grain, Join Syntax, and Unmatched Keys.py`

Validated on: 2026-08-05

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — landing `trip` / `trip_time` reads, grain and cardinality checks, string/list/Boolean join forms, composite-key fix, and unmatched-keys exercise all ran as expected |
| Serverless | Not tested | Standard baseline confirmed; serverless not yet run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **not tested**

## `02 - Silent Join Failures and Validation.py`

Validated on: 2026-08-05

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — landing `trip` / `trip_time` / `payment` reads, M:M fanout, key profiling, window-based duplicate resolution, NULL-key and `eqNullSafe` behavior, Cartesian demo, and exercise all ran as expected |
| Serverless | Not tested | Standard baseline confirmed; serverless not yet run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **not tested**

## `03 - Lookup Joins, Columns, and Broadcast.py`

Validated on: 2026-08-05

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — landing `zone_lookup` and curated `trip` reads, repeated pickup/dropoff lookup join, duplicate-column cleanup, unmatched dimension-row practice, and `F.broadcast` + `.explain()` all ran as expected |
| Serverless | Not tested | Standard baseline confirmed; serverless not yet run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **not tested**

## `04 - Semi Joins and Anti Joins.py`

Validated on: 2026-08-05

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — curated `trip` / `payment` and landing `trip_time` reads, `left_semi` / `left_anti`, reverse anti, semi+anti exhaustive-split check, `subtract()` bridge, and exercise all ran as expected |
| Serverless | Not tested | Standard baseline confirmed; serverless not yet run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **not tested**

## `05 - Union and unionByName.py`

Validated on: 2026-08-05

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — constructed frames only; `union` column-order trap, `unionByName`, `allowMissingColumns`, `distinct()` after union, and exercise all ran as expected |
| Serverless | Not tested | Standard baseline confirmed; serverless not yet run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **not tested**

## `06 - Intersect, subtract, and exceptAll.py`

Validated on: 2026-08-05

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — constructed frames only; `intersect` vs `intersectAll`, `subtract` vs `exceptAll` on duplicate-bearing multisets, and exercise all ran as expected |
| Serverless | Not tested | Standard baseline confirmed; serverless not yet run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **not tested**

## `07 - Build Unified Curated Tables.py`

Validated on: 2026-08-05

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — curated `trip` / `payment` / `drivers_flat` and landing `trip_time` / `zone_lookup` reads, stepwise left joins, broadcast zone lookup, 16/13-column mapping selects, and `saveAsTable` overwrite writes to `rideshare_dev.processed.trip_enriched` and `rideshare_dev.processed.trip_driver_assignment` all ran as expected |
| Serverless | Not tested | Standard baseline confirmed; serverless not yet run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **not tested**
