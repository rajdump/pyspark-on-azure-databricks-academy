# Validation — 09 - Spark SQL and DataFrame Interoperability

Author-recorded runtime validation evidence for this module. Results below
were observed by running the notebooks in Azure Databricks (see
`docs/standards/compute-validation-policy.md` for the validation order).

## `01 - Dual API Foundations and When to Choose.py`

Validated on: 2026-08-13

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — `trip_enriched` (106) via `%sql` and `spark.table`; `spark.sql`→DF; absolute `tip_amount_band` (zero 26 / low 40 / medium 20 / high 18 / no_data 2); DF→temp view; Manhattan known-tip exercise path (**43** rows) |
| Serverless | Passed | Same teachable path as Standard — all cells run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `02 - SQL Joins, Aggregations, and Filtering.py`

Validated on: 2026-08-13

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — `trip_enriched` (106) and `trip_driver_assignment` (100); layered CASE / `COALESCE` / JOIN (ambiguous column then fix); `GROUP BY` / `HAVING`; `NOT EXISTS` undriven (**6**); after JOIN high 15 / standard 64 / other 21; exercise path (compound `HAVING` **2** rows; undriven ids **6**) |
| Serverless | Passed | Same teachable path as Standard — all cells run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `03 - SQL Pivot, Unpivot, and Sampling.py`

Validated on: 2026-08-13

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — `trip_enriched` (106); borough×service counts (**18**); SQL `PIVOT` / `COALESCE` zeros / `TEMP VIEW` / `UNPIVOT`; brief `TABLESAMPLE`; payment-method reshape exercise path |
| Serverless | Passed | Same teachable path as Standard — all cells run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `04 - SQL Windows and QUALIFY.py`

Validated on: 2026-08-13

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — `kpi_zone_performance` (20) and `kpi_daily_trip_summary` (14); `ROW_NUMBER` + `QUALIFY` Top-2 by tip (**9** rows) and subquery equivalent; running `SUM` / `LAG` / direction `CASE`; Top-2 by `trip_count` exercise (**8** rows) |
| Serverless | Passed | Same teachable path as Standard — all cells run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `05 - CTEs and Parameterized SQL.py`

Validated on: 2026-08-13

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — `trip_enriched` (106); single CTE; multi-CTE tip-share; nested-subquery contrast; named `:borough` / `:min_tip` via `spark.sql(..., args=...)`; Manhattan daily share (**14** rows); borough-daily tip-share exercise path |
| Serverless | Passed | Same teachable path as Standard — all cells run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `06 - End-to-End SQL Pipeline.py`

Validated on: 2026-08-13

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — `trip_enriched` (106) and `trip_driver_assignment` (100); SQL rebuild of daily (14), zone (20), and driver (12) KPI contracts; read-only, no writes |
| Serverless | Passed | Same teachable path as Standard — all cells run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not required for this notebook |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**
