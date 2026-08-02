# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # 04 - Built-ins First: When (Not) to Use UDFs
# MAGIC
# MAGIC A **UDF** (user-defined function) lets you write a column rule in plain Python
# MAGIC instead of Spark's built-in `F.*` expressions. UDFs feel familiar, so it is
# MAGIC tempting to reach for one by default. In production, **use Spark built-in
# MAGIC functions first**.
# MAGIC
# MAGIC PySpark code builds Spark expressions and an execution plan. Built-in
# MAGIC expressions are executed by Spark's **JVM-based engine**. The **Catalyst**
# MAGIC optimizer can inspect those built-in expressions and optimize them together
# MAGIC with the surrounding query plan. A UDF wraps opaque Python logic — Catalyst
# MAGIC cannot inspect or optimize code inside the function, so Spark can only call it
# MAGIC as a black box.
# MAGIC
# MAGIC This notebook implements the same small rule twice — built-in and Python UDF —
# MAGIC so you can compare execution behavior and decide when a UDF is genuinely
# MAGIC justified.
# MAGIC
# MAGIC You will:
# MAGIC
# MAGIC 1. Express a column rule with Spark built-in `F.*` functions on curated data
# MAGIC    from Notebook 03
# MAGIC 2. Implement the same rule as a Python UDF and contrast it with the built-in
# MAGIC    version
# MAGIC 3. Use a decision table to choose an approach on a new column rule
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
# MAGIC `F.when` expresses this rule entirely with built-in expressions. Catalyst can
# MAGIC inspect those expressions and optimize them together with the surrounding query
# MAGIC plan.

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
# MAGIC Built-in Spark expressions run in Spark's JVM-based engine. A regular Python
# MAGIC UDF cannot run there — Spark must run your Python function in a separate
# MAGIC **Python worker** on the cluster.
# MAGIC
# MAGIC Spark transfers **batches** of values from the JVM executor to that worker. Your
# MAGIC Python function still processes **one value at a time** inside the worker. That
# MAGIC JVM–Python boundary adds serialization overhead that built-in expressions avoid.
# MAGIC Catalyst cannot inspect or optimize the Python logic inside the UDF.
# MAGIC
# MAGIC The demo below produces the same `tip_band` values as the built-in version; the
# MAGIC difference is where and how Spark executes the logic.

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
# MAGIC ## 3. Which approach to reach for
# MAGIC
# MAGIC Both implementations above agree on `tip_band` because this rule is simple enough
# MAGIC for built-ins — that is the common case in production.
# MAGIC
# MAGIC | Approach | Execution | Use when |
# MAGIC |---|---|---|
# MAGIC | Built-in `F.*` | Spark JVM engine; visible to Catalyst | Default choice |
# MAGIC | Python UDF | Python worker; logic opaque to Catalyst | Only when Spark built-ins cannot express the rule |
# MAGIC | Pandas/Arrow UDF | Python worker with Arrow batches | Advanced fallback when vectorized Python logic is required |
# MAGIC
# MAGIC A common mistake is reaching for a UDF out of familiarity with plain Python
# MAGIC before checking whether `pyspark.sql.functions` already covers the rule — most
# MAGIC of the transforms in Module 6 **`01 - Column Transforms with Built-in
# MAGIC Functions`** and **`03 - Cleaning and Curated Outputs`** did not need one.
# MAGIC
# MAGIC **Advanced note.** Pandas UDFs use Apache Arrow to transfer data between Spark
# MAGIC and Python in columnar batches and support vectorized Pandas operations. They can
# MAGIC be useful when Python, Pandas, or NumPy logic is genuinely required, but they
# MAGIC remain secondary to Spark built-in functions. This course does not cover them
# MAGIC further.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Exercise
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
# MAGIC 1. Build `trip_distance_band` with built-in `F.when`.
# MAGIC 2. In a markdown cell or short comment, explain why a Python UDF is unnecessary
# MAGIC    for this rule.
# MAGIC 3. Name one situation where a UDF could be justified (you do not need to
# MAGIC    implement it).
# MAGIC
# MAGIC Do not write any result — this notebook only reads `curated/trip/` and
# MAGIC `curated/payment/`, never overwrites them.

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - Built-ins are the default.
# MAGIC - Built-ins execute through Spark's JVM-based engine.
# MAGIC - Python UDF logic runs in Python workers.
# MAGIC - Python UDFs add serialization and process-boundary overhead.
# MAGIC - Catalyst cannot inspect the Python logic inside a UDF.
# MAGIC - Pandas/Arrow UDFs are only an advanced fallback and are not covered further.
# MAGIC
# MAGIC **Next:** Module 7 — Joins and Set Operations.
