# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # 04 - Built-ins First: When (Not) to Use UDFs
# MAGIC
# MAGIC A **UDF** (user-defined function) lets you write a column rule in plain Python
# MAGIC instead of Spark's built-in `F.*` expressions. UDFs feel familiar, so it is
# MAGIC tempting to reach for one by default. In production this usually hurts
# MAGIC performance: Spark's built-in expressions run entirely inside the JVM, where the
# MAGIC **Catalyst optimizer** can push down predicates and generate optimized code for
# MAGIC the whole query. A UDF is opaque to Catalyst — Spark can only call it, not
# MAGIC optimize through it. This notebook implements the same small rule three ways so
# MAGIC you can see the difference and decide when a UDF is genuinely justified.
# MAGIC
# MAGIC You will:
# MAGIC
# MAGIC 1. Express a column rule with Spark built-in `F.*` functions on curated data
# MAGIC    from Notebook 03
# MAGIC 2. Implement the same rule as a Python UDF and see why it is slower and less
# MAGIC    optimizable than the built-in version
# MAGIC 3. Implement the same rule as a Pandas UDF and see how vectorized execution
# MAGIC    narrows — but does not close — that gap
# MAGIC 4. Decide which approach to reach for on a new column rule
# MAGIC
# MAGIC **Prerequisites.** Complete Module 6 **`01 - Column Transforms with Built-in
# MAGIC Functions`**, **`02 - Complex Types: Structs, Arrays, and explode`**, and
# MAGIC **`03 - Cleaning and Curated Outputs`**. The curated Parquet outputs under
# MAGIC `…/curated/trip/` (106 rows) and `…/curated/payment/` (105 rows) must exist.
# MAGIC This notebook reads those outputs and does **not** overwrite them.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup
# MAGIC
# MAGIC Read the curated `trip` and `payment` outputs written in Module 6
# MAGIC **`03 - Cleaning and Curated Outputs`**. Use `format("parquet").load(...)` — the
# MAGIC same recommended read pattern as Notebook 03 — rather than the `.parquet(path)`
# MAGIC shorthand.
# MAGIC
# MAGIC | Dataset | Source | Grain |
# MAGIC |---|---|---|
# MAGIC | `trip` | `…/curated/trip/` | 106 rows; one row per `trip_id` |
# MAGIC | `payment` | `…/curated/payment/` | 105 rows; one row per `trip_id` |
# MAGIC
# MAGIC This notebook's demo rule uses `payment`'s `tip_percent_of_base`; the exercise
# MAGIC uses `trip`'s `trip_distance_km`. Both columns were created in Notebook 03.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import StringType
import numpy as np
import pandas as pd

curated_root = "/Volumes/rideshare_dev/processed/output_files/curated"
curated_trip_path = f"{curated_root}/trip"
curated_payment_path = f"{curated_root}/payment"

print(f"curated_trip_path = {curated_trip_path}")
print(f"curated_payment_path = {curated_payment_path}")

# COMMAND ----------

trip_curated = spark.read.format(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    "parquet"
).load(curated_trip_path)
payment_curated = spark.read.format(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    "parquet"
).load(curated_payment_path)

print(f"Curated trip rows: {trip_curated.count()}")
print(f"Curated payment rows: {payment_curated.count()}")

payment_curated.select(
    F.col("trip_id"),
    F.col("tip_percent_of_base"),
).orderBy(F.col("trip_id")).show(10, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Built-ins as the default
# MAGIC
# MAGIC The demo rule buckets `tip_percent_of_base` into a `tip_band` label:
# MAGIC
# MAGIC | `tip_percent_of_base` | `tip_band` |
# MAGIC |---|---|
# MAGIC | NULL | `no_tip` |
# MAGIC | `< 10` | `low` |
# MAGIC | `10` – `< 20` | `medium` |
# MAGIC | `>= 20` | `high` |
# MAGIC
# MAGIC `F.when` expresses this rule entirely with built-in expressions, so Catalyst can
# MAGIC optimize it like any other column transform.

# COMMAND ----------

payment_tip_band_builtin = payment_curated.withColumn(
    "tip_band",
    F.when(F.col("tip_percent_of_base").isNull(), F.lit("no_tip"))
    .when(F.col("tip_percent_of_base") < 10, F.lit("low"))
    .when(F.col("tip_percent_of_base") < 20, F.lit("medium"))
    .otherwise(F.lit("high")),
).select(
    F.col("trip_id"),
    F.col("tip_percent_of_base"),
    F.col("tip_band"),
)

print("tip_band from built-in F.when:")
payment_tip_band_builtin.orderBy(F.col("trip_id")).show(10, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. The same rule as a Python UDF
# MAGIC
# MAGIC A Python UDF runs **row-at-a-time**: for every row, Spark serializes the input
# MAGIC value, sends it to a separate Python worker process, runs the plain Python
# MAGIC function, and serializes the result back. That round trip — and the fact that
# MAGIC Catalyst cannot see inside the function to optimize it — is why UDFs are slower
# MAGIC than the equivalent built-in expression, even though the logic is identical.

# COMMAND ----------


def tip_band_python(tip_percent):
    if tip_percent is None:
        return "no_tip"
    if tip_percent < 10:
        return "low"
    if tip_percent < 20:
        return "medium"
    return "high"


tip_band_udf = F.udf(tip_band_python, StringType())

payment_tip_band_udf = payment_curated.withColumn(
    "tip_band_udf",
    tip_band_udf(F.col("tip_percent_of_base")),
).select(
    F.col("trip_id"),
    F.col("tip_percent_of_base"),
    F.col("tip_band_udf"),
)

print("tip_band from a Python UDF (same values as the built-in version):")
payment_tip_band_udf.orderBy(F.col("trip_id")).show(10, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. The same rule as a Pandas UDF
# MAGIC
# MAGIC A **Pandas UDF** uses Apache Arrow to send a whole **batch** of rows to the
# MAGIC Python worker as a `pandas.Series`, run one **vectorized** NumPy/pandas
# MAGIC operation over the batch, and return a `pandas.Series` of results. This removes
# MAGIC the row-at-a-time round trip a plain Python UDF pays for, so Pandas UDFs are
# MAGIC usually much faster than Python UDFs. They are still slower than built-ins for
# MAGIC logic Spark can already express natively — reach for a Pandas UDF only when the
# MAGIC rule genuinely needs a NumPy/pandas operation with no built-in equivalent.

# COMMAND ----------


@F.pandas_udf(StringType())
def tip_band_pandas(tip_percent: pd.Series) -> pd.Series:
    conditions = [
        tip_percent.isna(),
        tip_percent < 10,
        tip_percent < 20,
    ]
    choices = ["no_tip", "low", "medium"]
    return pd.Series(
        np.select(conditions, choices, default="high"),
        index=tip_percent.index,
    )


payment_tip_band_pandas = payment_curated.withColumn(
    "tip_band_pandas",
    tip_band_pandas(F.col("tip_percent_of_base")),
).select(
    F.col("trip_id"),
    F.col("tip_percent_of_base"),
    F.col("tip_band_pandas"),
)

print("tip_band from a Pandas UDF (same values as the built-in version):")
payment_tip_band_pandas.orderBy(F.col("trip_id")).show(10, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Which approach to reach for
# MAGIC
# MAGIC All three cells above produce the same `tip_band` values because this rule is
# MAGIC simple enough for built-ins to express directly — that is the common case.
# MAGIC
# MAGIC | Approach | Execution | Use when |
# MAGIC |---|---|---|
# MAGIC | Built-in `F.*` | Inside the JVM; Catalyst-optimized | Default choice — almost always |
# MAGIC | Python UDF | Row-at-a-time in a Python worker | Rare; prefer a Pandas UDF instead |
# MAGIC | Pandas UDF | Vectorized, batched via Arrow | Only for NumPy/pandas rules, no built-in |
# MAGIC
# MAGIC A common mistake is reaching for a UDF out of familiarity with plain Python
# MAGIC before checking whether `pyspark.sql.functions` already covers the rule — most
# MAGIC of the transforms in Module 6 **`01 - Column Transforms with Built-in
# MAGIC Functions`** and **`03 - Cleaning and Curated Outputs`** did not need one.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Exercise
# MAGIC
# MAGIC New requirement: bucket curated `trip` rows into a `trip_distance_band` from
# MAGIC `trip_distance_km`:
# MAGIC
# MAGIC | `trip_distance_km` | `trip_distance_band` |
# MAGIC |---|---|
# MAGIC | NULL | `unknown` |
# MAGIC | `< 5` | `short` |
# MAGIC | `5` – `< 15` | `medium` |
# MAGIC | `>= 15` | `long` |
# MAGIC
# MAGIC Using `trip_curated`:
# MAGIC
# MAGIC 1. Build `trip_distance_band_builtin` with `F.when` (built-in).
# MAGIC 2. Build `trip_distance_band_udf` with a Python UDF that implements the same
# MAGIC    rule.
# MAGIC 3. Build `trip_distance_band_pandas` with a Pandas UDF that implements the same
# MAGIC    rule.
# MAGIC 4. Select `trip_id`, `trip_distance_km`, and the band column from each result,
# MAGIC    order by `trip_id`, and show them side by side to confirm the three
# MAGIC    approaches agree.
# MAGIC
# MAGIC Do not write any result — this notebook only reads `curated/trip/` and
# MAGIC `curated/payment/`, never overwrites them.

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - Implemented one column rule three ways: a built-in `F.when` expression, a
# MAGIC   row-at-a-time Python UDF, and a vectorized Pandas UDF — all three produced
# MAGIC   identical `tip_band` values.
# MAGIC - Built-ins run inside the JVM under Catalyst optimization; Python UDFs pay a
# MAGIC   row-at-a-time serialization cost the built-in version never incurs; Pandas
# MAGIC   UDFs close part of that gap with Arrow-based batching but still trail
# MAGIC   built-ins for logic Spark can already express.
# MAGIC - Confirmed the decision rule: prefer built-ins by default; use a Pandas UDF
# MAGIC   only when the logic truly requires NumPy/pandas; treat a plain Python UDF as
# MAGIC   a last resort.
# MAGIC - Read curated `trip` and `payment` outputs from Notebook 03 without
# MAGIC   overwriting either.
# MAGIC
# MAGIC **Next:** Module 7 — Joins and Set Operations.
