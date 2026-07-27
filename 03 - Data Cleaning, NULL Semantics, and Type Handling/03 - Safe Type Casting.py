# Databricks notebook source
# MAGIC %md
# MAGIC # Safe Type Casting
# MAGIC
# MAGIC **Learning objectives.** After this notebook, you will be able to:
# MAGIC - Explain how Spark 4 / ANSI mode changes invalid **`cast`** behavior
# MAGIC - Cast string columns to typed values with **`cast`**
# MAGIC - Use **`try_cast`** when malformed or overflowing values should become
# MAGIC   **`NULL`** instead of raising an error
# MAGIC - Detect rows rejected by a cast with
# MAGIC   **`source.isNotNull() & casted.isNull()`**
# MAGIC - Recognize unsupported type pairs where **`try_cast`** cannot help
# MAGIC - Inspect rejected casts in a small operations-style output
# MAGIC
# MAGIC **Prerequisites.** `02 - Missing, Blank, and Sentinel Values` in this
# MAGIC module — you should already know normalize-first cleaning and intro
# MAGIC **`cast`** from Module 2 **`03 - Selecting and Transforming Columns`**.
# MAGIC Module 2 deferred deeper casting rules here.
# MAGIC
# MAGIC **Setup.** Attach any compute with PySpark available. This notebook uses
# MAGIC small, hand-built rideshare-style DataFrames aligned with **`payment`**
# MAGIC and **`trip`** column names from the course dataset.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup DataFrame for casting examples
# MAGIC
# MAGIC Notebook 02 normalized missing-value disguises to real **`NULL`** values.
# MAGIC The next problem is **wrong types** — numbers stored as text before
# MAGIC calculations can run.
# MAGIC
# MAGIC Create one small DataFrame where fare and duration values are **`string`**
# MAGIC columns:

# COMMAND ----------

from pyspark.sql import functions as F

rows = [
    (1001, "12.50", "18"),
    (1002, "8.00", "24"),
    (1003, "22.75", "35"),
]

schema_ddl = "trip_id bigint, base_fare_amount string, ride_duration_mins string"

df = spark.createDataFrame(rows, schema_ddl)  # pyright: ignore[reportUndefinedVariable]  # noqa: F821

# COMMAND ----------

# MAGIC %md
# MAGIC Confirm the sample rows and schema before casting — check that numeric
# MAGIC values are stored as text.

# COMMAND ----------

df.show()
df.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cast columns with `cast`
# MAGIC
# MAGIC **`F.col("x").cast("type")`** converts a column to a new type when the
# MAGIC source values are valid. Pass a type name such as **`"decimal(10,2)"`** or
# MAGIC **`"int"`**.
# MAGIC
# MAGIC **Business question:** Finance needs **`base_fare_amount`** as
# MAGIC **`decimal(10,2)`** and **`ride_duration_mins`** as **`int`** for
# MAGIC calculations.

# COMMAND ----------

typed = df.select(
    "trip_id",
    F.col("base_fare_amount").cast("decimal(10,2)").alias("base_fare_amount"),
    F.col("ride_duration_mins").cast("int").alias("ride_duration_mins"),
)

typed.printSchema()
typed.show()

# COMMAND ----------

# MAGIC %md
# MAGIC Casting a decimal to an integer **truncates toward zero** — it does not
# MAGIC round. **`2.9`** becomes **`2`**.

# COMMAND ----------

typed.select(F.lit(2.9).cast("int").alias("truncated")).show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Spark 4 / ANSI mode and invalid casts
# MAGIC
# MAGIC On Databricks Runtime 17.3, **ANSI mode** is enabled by default. An invalid
# MAGIC **`cast`** raises an error instead of silently returning **`NULL`** (legacy
# MAGIC non-ANSI behavior).
# MAGIC
# MAGIC **Business question:** What happens when **`base_fare_amount`** contains
# MAGIC text that is not a number, such as **`"N/A"`**?

# COMMAND ----------

print("ANSI mode enabled:", spark.conf.get("spark.sql.ansi.enabled"))  # noqa: F821

# COMMAND ----------

bad = spark.createDataFrame(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    [
        (1001, "12.50"),
        (1002, "N/A"),
        (1003, "8.00"),
        (1004, "999999999.99"),
    ],
    "trip_id bigint, base_fare_amount string",
)

try:
    bad.select(F.col("base_fare_amount").cast("double")).show()
except Exception as e:
    print(f"{type(e).__name__}: {str(e).splitlines()[0]}")

# COMMAND ----------

# MAGIC %md
# MAGIC The error is typically **`[CAST_INVALID_INPUT]`** — **`"N/A"`** cannot become
# MAGIC a **`double`**. Spark points to the fix: **`try_cast`**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Return `NULL` for invalid values with `try_cast`
# MAGIC
# MAGIC When Spark supports the source-to-target conversion, **`try_cast`** returns
# MAGIC **`NULL`** for malformed or overflowing values instead of raising an error.
# MAGIC Unsupported type pairs still raise an error, as shown later.

# COMMAND ----------

cleaned = bad.select(
    "trip_id",
    "base_fare_amount",
    F.col("base_fare_amount").try_cast("decimal(10,2)").alias("base_fare_amount_clean"),
)

cleaned.show()

# COMMAND ----------

# MAGIC %md
# MAGIC **`"12.50"`** and **`"8.00"`** fit **`decimal(10,2)`**.
# MAGIC
# MAGIC - **`"N/A"`** is invalid text → **`NULL`**
# MAGIC - **`"999999999.99"`** is too large for **`decimal(10,2)`** → **`NULL`**

# COMMAND ----------

# MAGIC %md
# MAGIC ## Find rows that `try_cast` rejected
# MAGIC
# MAGIC A rejected row has a source value that is not **`NULL`**, but a cast result
# MAGIC that is **`NULL`**:
# MAGIC
# MAGIC **`source.isNotNull() & casted.isNull()`**
# MAGIC
# MAGIC **Business question:** Which trips have fare text that could not be parsed
# MAGIC to the target type?

# COMMAND ----------

rejected = cleaned.filter(
    F.col("base_fare_amount").isNotNull() & F.col("base_fare_amount_clean").isNull()
)

rejected.show()

# COMMAND ----------

# MAGIC %md
# MAGIC > **Good to know:** Apply **`try_cast`** to the affected column expressions.
# MAGIC > Do not turn off ANSI for the whole session — that hides bad casts and
# MAGIC > overflows across the job.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Unsupported type conversions
# MAGIC
# MAGIC **`try_cast`** handles invalid **values** only when Spark supports the
# MAGIC conversion. For example, Spark supports string → integer even when some
# MAGIC strings are not valid numbers.
# MAGIC
# MAGIC Some type combinations cannot be converted. An **array**, for example, cannot
# MAGIC be cast directly to an **integer**. Spark rejects the operation before
# MAGIC processing rows, and **`try_cast`** cannot prevent that error. Choose a
# MAGIC compatible target type or transform the source first.

# COMMAND ----------

try:
    spark.range(1).select(F.array(F.lit(1)).try_cast("int")).show()  # noqa: F821
except Exception as e:
    print(f"{type(e).__name__}: {str(e).splitlines()[0]}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Chain cast validation into an operations-style output
# MAGIC
# MAGIC **Business question:** Which fare values are ready for calculation, and
# MAGIC which records need data-quality review because conversion failed?
# MAGIC
# MAGIC A non-**`NULL`** value in **`base_fare_amount_clean`** is ready. A source
# MAGIC value that is not **`NULL`** with a **`NULL`** cast result requires review.

# COMMAND ----------

valid_fares = cleaned.filter(F.col("base_fare_amount_clean").isNotNull())

print("Ready for calculations")
valid_fares.show()

print("Requires data-quality review")
rejected.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Use a second small rideshare-style DataFrame named **`exercise_df`** and
# MAGIC complete:
# MAGIC
# MAGIC 1. Create **`exercise_df`** with **`trip_id`** and **`trip_distance_miles`**
# MAGIC    as **`string`** (`trip` table column). Include at least one valid decimal
# MAGIC    string and one invalid value (for example **`"unknown"`**).
# MAGIC 2. Add **`trip_distance_miles_clean`** with **`try_cast`** to
# MAGIC    **`decimal(8,2)`**.
# MAGIC 3. Filter to rows where the source was not **`NULL`** but the cast result
# MAGIC    is **`NULL`** (rejected casts).
# MAGIC 4. Show the rejected rows.
# MAGIC
# MAGIC Keep the DataFrame tiny (four or five rows).

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC Recap this notebook's casting path:
# MAGIC
# MAGIC - **`cast`** — converts when values are valid; invalid input raises under
# MAGIC   ANSI mode
# MAGIC - **`try_cast`** — returns **`NULL`** for bad values when the conversion
# MAGIC   is supported
# MAGIC - **Rejected rows** — **`source.isNotNull() & casted.isNull()`**
# MAGIC - **Unsupported pairs** — schema/operation error; fix the target type or
# MAGIC   transform the source first
# MAGIC - **Do not disable ANSI globally** — use **`try_*`** on affected
# MAGIC   expressions
# MAGIC
# MAGIC Next up: **`04 - Numeric Overflow and Date-Timestamp Parsing`** —
# MAGIC **`try_add`**, **`try_sum`**, **`try_to_date`**, and invalid source vs
# MAGIC invalid format patterns.
