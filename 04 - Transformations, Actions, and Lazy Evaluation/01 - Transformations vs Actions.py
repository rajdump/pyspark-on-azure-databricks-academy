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
# MAGIC This notebook answers a question that Modules 2 and 3 left open: when does
# MAGIC Spark actually process your data?
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
# MAGIC Modules 2 and 3 built chains of **`select`**, **`filter`**, and
# MAGIC **`withColumn`** without asking when Spark ran them. One scenario runs
# MAGIC through this notebook: a nightly operations review of standard-service trips
# MAGIC that covered at least five miles.
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
# MAGIC The **`show()`** call is what displayed those rows — it is an action, and the
# MAGIC sections below explain why that distinction matters.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Building a chain produces no output
# MAGIC
# MAGIC **Business question:** The nightly review needs standard-service trips of at
# MAGIC least five miles, with each distance also expressed in kilometers. What
# MAGIC happens when you write those steps and run the cell?

# COMMAND ----------

review_trips = (
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
# MAGIC The cell finished without printing a single row. Spark recorded the three
# MAGIC steps in the DataFrame's **logical plan** — its internal description of the
# MAGIC requested result — and processed no data.
# MAGIC
# MAGIC That is the behavior this notebook explains: **`filter`**, **`withColumn`**,
# MAGIC and **`select`** are transformations, and transformations on their own never
# MAGIC produce output.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Transformations return new DataFrames
# MAGIC
# MAGIC A **transformation** defines a processing step and returns a new DataFrame.
# MAGIC Run the first two steps of the review separately to see what each call hands
# MAGIC back.
# MAGIC
# MAGIC **Business question:** The review adds a kilometer column. Does that change
# MAGIC the shared **`trips`** DataFrame that other reports read?

# COMMAND ----------

filtered_trips = trips.filter(
    (F.col("service_type") == "standard") & (F.col("trip_distance_miles") >= 5)
)

trips_with_km = filtered_trips.withColumn(
    "trip_distance_km",
    F.round(F.col("trip_distance_miles") * F.lit(1.60934), 2),
)

print("filter returned:    ", type(filtered_trips).__name__)
print("withColumn returned:", type(trips_with_km).__name__)

# COMMAND ----------

print("Source columns:     ", trips.columns)
print("Transformed columns:", trips_with_km.columns)

# COMMAND ----------

# MAGIC %md
# MAGIC Both calls returned a **`DataFrame`**, and neither printed rows. The source
# MAGIC **`trips`** still has its original four columns — **`trip_distance_km`**
# MAGIC exists only in the plan held by **`trips_with_km`**.
# MAGIC
# MAGIC A transformation never modifies the DataFrame it was called on, so other
# MAGIC reports reading **`trips`** are unaffected by this review.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Actions run the plan and produce output
# MAGIC
# MAGIC An **action** asks Spark to execute a DataFrame's plan. Depending on the
# MAGIC API, an action displays rows, returns a Python value, or writes data to
# MAGIC storage.
# MAGIC
# MAGIC **Business question:** The nightly review has to list its trips and report
# MAGIC how many it found. Which calls make that happen?

# COMMAND ----------

show_result = review_trips.show(truncate=False)

print("show() returned:", type(show_result).__name__)

# COMMAND ----------

review_count = review_trips.count()

print("count() returned:", type(review_count).__name__)
print("Number of records:", review_count)

# COMMAND ----------

# MAGIC %md
# MAGIC Trips **`1003`** and **`1005`** are the only standard-service trips of at
# MAGIC least five miles. **`show()`** displayed them and returned **`None`**;
# MAGIC **`count()`** returned the row count as a Python **`int`**. Both executed the
# MAGIC plan that produced no output when it was built.
# MAGIC
# MAGIC > **Good to know:** Each action executes the plan again. The two cells above
# MAGIC > ran the same filter, kilometer conversion, and column selection twice —
# MAGIC > once for **`show()`** and once for **`count()`**. The next notebook looks at
# MAGIC > the plan itself and at why Spark waits for an action.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Classify an unfamiliar API
# MAGIC
# MAGIC **Business question:** You inherit a pipeline that calls **`limit`**,
# MAGIC **`orderBy`**, and **`printSchema`**. Which of them process data?

# COMMAND ----------

limited_trips = trips.limit(2)
sorted_trips = trips.orderBy(F.col("trip_distance_miles").desc())

print("limit(2) returned: ", type(limited_trips).__name__)
print("orderBy() returned:", type(sorted_trips).__name__)

# COMMAND ----------

# MAGIC %md
# MAGIC Both returned a **`DataFrame`** and printed nothing, so both are
# MAGIC transformations. **`limit(2)`** reads as if it fetches two rows and
# MAGIC **`orderBy`** reads as if it sorts them, but neither touches data until an
# MAGIC action runs. Add the action, and the rows appear.

# COMMAND ----------

limited_trips.show()

# COMMAND ----------

# MAGIC %md
# MAGIC A method's return type on its own is not a reliable test either.
# MAGIC **`printSchema()`** returns **`None`**, exactly like **`show()`**, and
# MAGIC **`columns`** returns a Python list — yet neither processes rows. Both read
# MAGIC only the schema Spark already holds.

# COMMAND ----------

schema_result = trips.printSchema()

print("printSchema() returned:", type(schema_result).__name__)
print("columns returned:      ", type(trips.columns).__name__, trips.columns)

# COMMAND ----------

# MAGIC %md
# MAGIC Classify by what a call does, not by what it returns:
# MAGIC
# MAGIC - **Transformation** — returns a new DataFrame and extends its logical plan
# MAGIC   without processing rows: **`select`**, **`filter`** / **`where`**,
# MAGIC   **`withColumn`**, **`limit`**, **`orderBy`**
# MAGIC - **Action** — triggers execution and returns a result, displays output, or
# MAGIC   writes data to storage: **`show`**, **`count`**
# MAGIC - **Neither** — reads metadata Spark already holds: **`printSchema`**,
# MAGIC   **`columns`**

# COMMAND ----------

# MAGIC %md
# MAGIC ## Chain transformations before one action
# MAGIC
# MAGIC In a batch job, build the required result through transformations, then call
# MAGIC the single action the job needs. Extra actions in the middle of a pipeline
# MAGIC re-execute every step before them.
# MAGIC
# MAGIC **Business question:** The nightly review should list its trips longest
# MAGIC first. How do you add that step and still execute the plan once?

# COMMAND ----------

nightly_review = review_trips.orderBy(F.col("trip_distance_miles").desc())

nightly_review.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC **`orderBy`** extended the existing plan instead of starting a new one, and
# MAGIC a single **`show()`** executed the filter, kilometer conversion, column
# MAGIC selection, and sort together. Trip **`1005`** now appears first at
# MAGIC **`11.50`** miles.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Build a similar review with columns from the course **`payment`** schema:
# MAGIC
# MAGIC 1. Create **`exercise_df`** with **`trip_id`** (`bigint`),
# MAGIC    **`payment_method`** (`string`), **`base_fare_amount`**
# MAGIC    (`decimal(10,2)`), and **`tip_amount`** (`decimal(10,2)`). Use three or
# MAGIC    four small rows.
# MAGIC 2. Filter to rows where **`payment_method`** is **`"card"`**.
# MAGIC 3. Add **`fare_and_tip_amount`** as **`base_fare_amount + tip_amount`**.
# MAGIC 4. Select **`trip_id`**, **`payment_method`**, and
# MAGIC    **`fare_and_tip_amount`**.
# MAGIC 5. Before you run the chain, write down whether each of steps 2, 3, and 4 is
# MAGIC    a transformation or an action, and do the same for **`printSchema()`**.
# MAGIC 6. Call **`show()`** once, after the chain is complete, and check your
# MAGIC    answers against what the cells printed.

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC Recap this notebook's path:
# MAGIC
# MAGIC - **Transformations** return a new DataFrame and extend its logical plan
# MAGIC   without processing rows — **`select`**, **`filter`** / **`where`**,
# MAGIC   **`withColumn`**, **`limit`**, **`orderBy`**
# MAGIC - **Actions** trigger execution and return a result, display output, or
# MAGIC   write data — **`show`**, **`count`**
# MAGIC - **Return type is not the test** — **`printSchema()`** returns **`None`**
# MAGIC   just like **`show()`**, but processes no rows
# MAGIC - **Source DataFrames are never modified** — each transformation builds a new
# MAGIC   plan, so a shared source stays usable by other reports
# MAGIC - **One action per result** — every action re-executes the plan behind it
# MAGIC
# MAGIC Next up: **Lazy Evaluation and the Query Plan** — why Spark waits for an
# MAGIC action and how to inspect the plan it builds.
