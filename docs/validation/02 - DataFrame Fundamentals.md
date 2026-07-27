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

## `02 - Inspecting DataFrames.py`

Validated on: 2026-07-27

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — `show()` variants, `display()`, schema inspection (`printSchema()`, `schema`, `columns`, `dtypes`), size checks (`count()`, `isEmpty()`), and stats (`describe()`, `summary()`) all ran as expected |
| Serverless | Passed | Same teachable path as Standard — content, structure, size, and stats inspection cells all run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not repeated per validation baseline |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `03 - Selecting and Transforming Columns.py`

Validated on: 2026-07-27

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — `select`, `F.col`, `cast`/`F.lit`, `F.when`/`otherwise`, `withColumn`, `withColumns`, rename, `drop`, and chained transform cells all ran as expected |
| Serverless | Passed | Same teachable path as Standard — column projection, derived columns, and multi-step transform chain all run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not repeated per validation baseline |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `04 - SQL Expressions in DataFrame Code.py`

Validated on: 2026-07-27

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — `F.expr`, `selectExpr`, SQL `CASE WHEN`, misspelled-column `AnalysisException` demos, Python vs Spark SQL parse-error demos, and reusable expression chain all ran as expected |
| Serverless | Passed | Same teachable path as Standard — SQL-in-DataFrame expressions and error-handling demos all run |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not repeated per validation baseline |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **complete**

## `06 - Querying DataFrames with SQL.py`

Validated on: 2026-07-27

| Compute | Result | Notes |
|---|---|---|
| Classic all-purpose, Standard access mode | Passed | Baseline confirmed — three-way derived-column compare, SQL catalog resolution demo, session temp view (`createOrReplaceTempView`), `%sql`, `spark.sql` with chained `.filter`, and global temp view (`global_temp`) all ran as expected |
| Serverless | Partial | Session temp views, `%sql`, and `spark.sql` run. Global temp view cell raises `AnalysisException: [NOT_SUPPORTED_WITH_SERVERLESS] GLOBAL TEMPORARY VIEW is not supported on serverless compute` — caught by `try` / `except` as documented; remainder of notebook runs. Lesson kept as-is per policy (learning value on Standard baseline). |
| Classic all-purpose, Dedicated access mode | Not tested | Standard passed, so Dedicated not repeated per validation baseline |
| Jobs compute | Not applicable | No jobs content in this module |
| Pipeline-managed compute | Not applicable | No Lakeflow Pipelines content in this module |

- Databricks Runtime observed: **17.3 LTS**
- Serverless compatibility: **partial** (global temp views unsupported; session views and SQL query path run)
