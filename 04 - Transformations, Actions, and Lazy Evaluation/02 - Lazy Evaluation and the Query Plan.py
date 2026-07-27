# Databricks notebook source
# MAGIC %md
# MAGIC # Lazy Evaluation and the Query Plan
# MAGIC
# MAGIC Notebook 01 showed that transformations build a plan and actions execute
# MAGIC it. This notebook looks at **lazy evaluation** — why Spark waits for an
# MAGIC action — and at the **query plan** you inspect with **`.explain()`**,
# MAGIC including how the optimizer can reorder your steps before anything runs.
# MAGIC
# MAGIC **Learning objectives.** After this notebook, you will be able to:
# MAGIC - Explain why Spark waits for an action before executing a DataFrame's
# MAGIC   logical plan
# MAGIC - Inspect query plans with **`.explain()`**
# MAGIC - Recognize how the Spark optimizer can reorder transformations
# MAGIC
# MAGIC **Prerequisites.** `01 - Transformations vs Actions` in this module —
# MAGIC you should already know transformations, actions, and chaining before a
# MAGIC single action.
# MAGIC
# MAGIC **Setup.** Prefer **classic all-purpose** compute (Standard access mode).
# MAGIC Spark UI job and stage navigation is clearer there than on serverless —
# MAGIC useful when you compare actions in this notebook. This notebook uses
# MAGIC small, hand-built rideshare-style DataFrames aligned with the course
# MAGIC **`trip`** schema.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Set up the rideshare example
# MAGIC
# MAGIC Build a small DataFrame with four columns from the course **`trip`** schema:
# MAGIC **`trip_id`**, **`service_type`**, **`trip_distance_miles`**, and
# MAGIC **`ride_duration_mins`**.

# COMMAND ----------

from decimal import Decimal

from pyspark.sql import functions as F

trips = spark.createDataFrame(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    [
        (1001, "standard", Decimal("2.40"), 12),
        (1002, "premium", Decimal("8.75"), 26),
        (1003, "standard", Decimal("6.20"), 21),
        (1004, "shared", Decimal("3.10"), 18),
        (1005, "standard", Decimal("11.50"), 34),
        (1006, "premium", Decimal("4.80"), 16),
    ],
    """
    trip_id bigint,
    service_type string,
    trip_distance_miles decimal(8,2),
    ride_duration_mins int
    """,
)

trips.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Why Spark waits for an action
# MAGIC
# MAGIC **Lazy evaluation** means Spark records each transformation in a logical
# MAGIC plan and does not process rows until an action asks for a result.
# MAGIC
# MAGIC **Business question:** Operations needs standard-service trips of at least
# MAGIC five miles, with distance also in kilometers. What happens when you define
# MAGIC that chain — and when does Spark actually run it?

# COMMAND ----------

long_standard = (
    trips.filter((F.col("service_type") == "standard") & (F.col("trip_distance_miles") >= 5))
    .withColumn(
        "trip_distance_km",
        F.round(F.col("trip_distance_miles") * F.lit(1.60934), 2),
    )
    .select(
        "trip_id",
        "service_type",
        "trip_distance_miles",
        "trip_distance_km",
        "ride_duration_mins",
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC The cell finished with no printed rows. Spark has a plan for
# MAGIC **`long_standard`**, not a computed table in memory. An action is what
# MAGIC forces execution. Three common actions are **`show()`**, **`count()`**,
# MAGIC and writing the DataFrame to storage.

# COMMAND ----------

long_standard.show(truncate=False)

# COMMAND ----------

row_count = long_standard.count()

print("count() returned:", row_count)

# COMMAND ----------

# MAGIC %md
# MAGIC **`show()`** and **`count()`** each executed the same plan. Writing is also
# MAGIC an action: building a **`DataFrameWriter`** does nothing until you call a
# MAGIC save method. The cell below uses Spark's **`noop`** sink so the write
# MAGIC executes the plan without keeping files for later modules.

# COMMAND ----------

writer = long_standard.write.mode("overwrite").format("noop")

print("DataFrameWriter type:", type(writer).__name__)

writer.save()

print("noop write finished — the plan ran as part of the save")

# COMMAND ----------

# MAGIC %md
# MAGIC Spark waits so it can see the full chain before choosing how to run it.
# MAGIC That is the production reason for lazy evaluation: the optimizer works on
# MAGIC the complete plan, not on each line as you type it.
# MAGIC
# MAGIC > **Good to know:** After **`show()`**, **`count()`**, or the write, open
# MAGIC > **Spark UI → Jobs** on classic all-purpose compute. Each action should
# MAGIC > appear as its own job for the same logical plan.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Inspect the query plan with `.explain()`
# MAGIC
# MAGIC **`.explain()`** prints how Spark understands a DataFrame. It does not
# MAGIC return rows to your notebook the way **`show()`** does — it prints the
# MAGIC plan text.
# MAGIC
# MAGIC **Business question:** What plan did Spark build for the operations
# MAGIC review before any action ran?

# COMMAND ----------

long_standard.explain()

# COMMAND ----------

# MAGIC %md
# MAGIC The default **`.explain()`** print is the physical plan Spark would run.
# MAGIC Use **`mode="extended"`** when you also want the unresolved, analyzed,
# MAGIC and optimized logical plans in one printout.

# COMMAND ----------

long_standard.explain(mode="extended")

# COMMAND ----------

# MAGIC %md
# MAGIC Read the extended output from the bottom up for the logical stages, then
# MAGIC the physical plan. You do not need every operator name yet — look for the
# MAGIC filter, the projected columns, and the local relation that holds these
# MAGIC hand-built rows.

# COMMAND ----------

# MAGIC %md
# MAGIC ## How the optimizer reorders transformations
# MAGIC
# MAGIC You write transformations in one order. The **Catalyst optimizer** may
# MAGIC rearrange them into a cheaper order before execution — for example by
# MAGIC applying a filter earlier so fewer rows flow through later steps.
# MAGIC
# MAGIC **Business question:** The review selects columns first, then filters to
# MAGIC long standard trips. Does the optimized plan keep that written order?

# COMMAND ----------

written_order = trips.select(
    "trip_id",
    "service_type",
    "trip_distance_miles",
    "ride_duration_mins",
).filter((F.col("service_type") == "standard") & (F.col("trip_distance_miles") >= 5))

# COMMAND ----------

# MAGIC %md
# MAGIC Written order: **`select`**, then **`filter`**. Inspect the optimized
# MAGIC logical plan and the physical plan.

# COMMAND ----------

written_order.explain(mode="extended")

# COMMAND ----------

# MAGIC %md
# MAGIC Compare that to the same business result written with the filter first.

# COMMAND ----------

filter_first = trips.filter(
    (F.col("service_type") == "standard") & (F.col("trip_distance_miles") >= 5)
).select(
    "trip_id",
    "service_type",
    "trip_distance_miles",
    "ride_duration_mins",
)

filter_first.explain(mode="extended")

# COMMAND ----------

# MAGIC %md
# MAGIC Both chains answer the same question. In the optimized / physical plans,
# MAGIC look for the filter relative to the projection: Spark often pushes the
# MAGIC filter toward the data source so it does not carry unused rows through
# MAGIC every step. Your notebook order is a request; the optimized plan is what
# MAGIC Spark intends to run.
# MAGIC
# MAGIC > **Good to know:** **`.explain()`** prints a plan. It is not a substitute
# MAGIC > for an action when you need rows, counts, or written output.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Build an isolated chain (do not reuse DataFrames from earlier sections):
# MAGIC
# MAGIC 1. Create **`exercise_df`** with **`trip_id`** (`bigint`),
# MAGIC    **`service_type`** (`string`), **`trip_distance_miles`**
# MAGIC    (`decimal(8,2)`), and **`ride_duration_mins`** (`int`). Use three or
# MAGIC    four small rows.
# MAGIC 2. Build a chain that **`select`s** those columns first, then **`filter`s**
# MAGIC    to premium trips with **`ride_duration_mins >= 20`**.
# MAGIC 3. Call **`.explain(mode="extended")`** on the chain.
# MAGIC 4. In a short note under the plan, name one place where the optimized or
# MAGIC    physical plan differs from your written **`select`-then-`filter`**
# MAGIC    order — or state that the filter still appears next to the scan.
# MAGIC 5. Call **`show()`** once after you finish reading the plan.

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC Recap this notebook's path:
# MAGIC
# MAGIC - **Lazy evaluation** — transformations accumulate in a logical plan;
# MAGIC   Spark processes rows when an action runs
# MAGIC - **Actions that trigger execution** — **`show`**, **`count`**, and write
# MAGIC   / save operations (building a writer alone is not enough)
# MAGIC - **`.explain()`** — prints the plan; **`mode="extended"`** includes
# MAGIC   logical and physical stages
# MAGIC - **Optimizer reordering** — Catalyst may change step order (for example
# MAGIC   filter pushdown) while preserving the same result
# MAGIC
# MAGIC Next up: **Narrow vs Wide Transformations** — local work versus shuffles
# MAGIC and **`Exchange`** in the physical plan.
