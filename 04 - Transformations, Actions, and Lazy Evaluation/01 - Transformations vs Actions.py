# Databricks notebook source
# MAGIC %md
# MAGIC # Transformations vs Actions
# MAGIC
# MAGIC Transformations such as **`select()`**, **`filter()`**, and
# MAGIC **`withColumn()`** define processing steps and return new DataFrames without
# MAGIC immediately processing the data. Actions such as **`show()`**, **`count()`**,
# MAGIC or writing a DataFrame to storage trigger Spark to execute the accumulated
# MAGIC plan and produce output.
# MAGIC
# MAGIC **Learning objectives.** After this notebook, you will be able to:
# MAGIC - Distinguish transformations, which return DataFrames and extend logical
# MAGIC   plans, from actions, which execute those plans
# MAGIC - Classify common DataFrame APIs as transformations or actions
# MAGIC - Chain several transformations before a single action
# MAGIC
# MAGIC **Prerequisites.** Modules 2 and 3 — you should already be comfortable
# MAGIC using **`select`**, **`filter`**, **`withColumn`**, and **`F.col`**.
# MAGIC
# MAGIC **Setup.** Attach any compute with PySpark available. This notebook uses a
# MAGIC small, hand-built rideshare-style DataFrame aligned with the course
# MAGIC **`trip`** schema.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Set up the rideshare example
# MAGIC
# MAGIC Operations wants to review longer rides by service type. Build a small
# MAGIC DataFrame with four columns from the course **`trip`** schema:
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
# MAGIC ## Transformations return new DataFrames
# MAGIC
# MAGIC A **transformation** defines a processing step and returns a new DataFrame.
# MAGIC Methods such as **`select()`**, **`filter()`**, and **`withColumn()`** are
# MAGIC transformations.
# MAGIC
# MAGIC Spark does not process the underlying rows immediately. Instead, each
# MAGIC transformation adds an instruction to the DataFrame's **logical plan**,
# MAGIC which describes what Spark should do when an action triggers execution.
# MAGIC
# MAGIC The original **`trips`** DataFrame remains unchanged. In the example below,
# MAGIC each new variable refers to a DataFrame with a logical plan derived from
# MAGIC **`trips`**.

# COMMAND ----------

selected_trips = trips.select(
    "trip_id",
    "service_type",
    "trip_distance_miles",
    "ride_duration_mins",
)

long_trips = selected_trips.filter(F.col("trip_distance_miles") >= F.lit(5))

labeled_trips = long_trips.withColumn(
    "duration_band",
    F.when(F.col("ride_duration_mins") >= 30, F.lit("30+ mins")).otherwise(
        F.lit("under 30 mins")
    ),
)

print("select returned:", type(selected_trips).__name__)
print("filter returned:", type(long_trips).__name__)
print("withColumn returned:", type(labeled_trips).__name__)

# COMMAND ----------

# MAGIC %md
# MAGIC All three calls returned **`DataFrame`**. The original **`trips`**
# MAGIC DataFrame still has four columns; **`duration_band`** belongs only to the
# MAGIC new plan represented by **`labeled_trips`**.

# COMMAND ----------

print("Source columns:", trips.columns)
print("Transformed columns:", labeled_trips.columns)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Actions execute a DataFrame plan
# MAGIC
# MAGIC An **action** asks Spark to execute a DataFrame's plan. Depending on the
# MAGIC API, an action can return a Python value, display rows, or write data.
# MAGIC
# MAGIC **`show()`** executes the plan and prints rows; its Python return value is
# MAGIC **`None`**. **`count()`** executes the plan and returns the number of rows
# MAGIC as a Python **`int`**.

# COMMAND ----------

show_result = labeled_trips.show(truncate=False)
print("show() returned:", type(show_result).__name__)

# COMMAND ----------

row_count = labeled_trips.count()
print("count() returned:", type(row_count).__name__)
print("Rows in labeled_trips:", row_count)

# COMMAND ----------

# MAGIC %md
# MAGIC Both actions evaluated the plan represented by **`labeled_trips`**.
# MAGIC Calling an action does not consume or replace that DataFrame; the same
# MAGIC DataFrame can be used again.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Classify common DataFrame APIs
# MAGIC
# MAGIC A practical classification test is to ask what the call gives back:
# MAGIC
# MAGIC - **Transformation:** returns another DataFrame — **`select`**,
# MAGIC   **`filter`** / **`where`**, **`withColumn`**, and **`limit`**
# MAGIC - **Action:** executes a plan and produces output or a non-DataFrame result
# MAGIC   — **`show`** and **`count`**
# MAGIC
# MAGIC Run a few familiar transformations and inspect their Python return types.

# COMMAND ----------

select_result = trips.select("trip_id", "service_type")
where_result = trips.where(F.col("service_type") == "standard")
limit_result = trips.limit(2)

print("select(...) ->", type(select_result).__name__, "(transformation)")
print("where(...)  ->", type(where_result).__name__, "(transformation)")
print("limit(...)  ->", type(limit_result).__name__, "(transformation)")

# COMMAND ----------

# MAGIC %md
# MAGIC Run a few familiar actions and inspect their return types.

# COMMAND ----------

print("show()  ->", type(select_result.show()).__name__, "(action)")


# COMMAND ----------

count_result = where_result.count()

print("count() ->", type(count_result).__name__, "(action)")
print("Number of records:", count_result)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Chain transformations before one action
# MAGIC
# MAGIC In a batch pipeline, build the required result through transformations,
# MAGIC then call the action needed by the job. This keeps the data-processing
# MAGIC steps together and gives Spark the complete plan before execution.
# MAGIC
# MAGIC **Business question:** Which standard-service trips covered at least five
# MAGIC miles, and what was each trip's distance in kilometers?

# COMMAND ----------

standard_long_trips = (
    trips.filter(
        (F.col("service_type") == "standard")
        & (F.col("trip_distance_miles") >= F.lit(5))
    )
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
# MAGIC The variable now represents a chain of **`filter`**, **`withColumn`**, and
# MAGIC **`select`** transformations. Call one action to produce the requested
# MAGIC output.

# COMMAND ----------

standard_long_trips.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC Trips **`1003`** and **`1005`** meet both conditions. The action produces
# MAGIC only the rows and columns described by the full transformation chain.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Build a similar pipeline with columns from the course **`payment`** schema:
# MAGIC
# MAGIC 1. Create **`exercise_df`** with **`trip_id`** (`bigint`),
# MAGIC    **`payment_method`** (`string`), **`base_fare_amount`**
# MAGIC    (`decimal(10,2)`), and **`tip_amount`** (`decimal(10,2)`). Use three or
# MAGIC    four small rows.
# MAGIC 2. Filter to rows where **`payment_method`** is **`"card"`**.
# MAGIC 3. Add **`fare_and_tip_amount`** as **`base_fare_amount + tip_amount`**.
# MAGIC 4. Select **`trip_id`**, **`payment_method`**, and
# MAGIC    **`fare_and_tip_amount`**.
# MAGIC 5. Call **`show()`** once, after the transformation chain is complete.
# MAGIC
# MAGIC Before running the action, identify each operation in your chain as a
# MAGIC transformation or an action.

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC Recap the two operation types:
# MAGIC
# MAGIC - **Transformations** return new DataFrames and extend logical plans;
# MAGIC   familiar examples include **`select`**, **`filter`**,
# MAGIC   **`withColumn`**, and **`limit`**
# MAGIC - **Actions** execute DataFrame plans and produce results or output;
# MAGIC   **`show`** displays rows and **`count`** returns a Python integer
# MAGIC - A transformation chain describes the complete result before one action
# MAGIC   asks Spark to produce it
# MAGIC
# MAGIC Next up: **Lazy Evaluation and the Query Plan** — why Spark waits for an
# MAGIC action and how to inspect the plan it builds.
