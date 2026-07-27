# Databricks notebook source
# MAGIC %md
# MAGIC # Numeric Overflow and Date-Timestamp Parsing
# MAGIC
# MAGIC **Learning objectives.** After this notebook, you will be able to:
# MAGIC - Handle integer and decimal **cast overflow** under Spark 4 / ANSI mode
# MAGIC - Use **`try_add`** and **`try_sum`** / **`try_avg`** when arithmetic or
# MAGIC   aggregation overflow should return **`NULL`** instead of raising
# MAGIC - Parse text into **`date`** and **`timestamp`** values with
# MAGIC   **`to_date`** / **`to_timestamp`** and format patterns
# MAGIC - Use **`try_to_date`** / **`try_to_timestamp`** (and related **`try_*`**
# MAGIC   helpers) for invalid source values
# MAGIC - Distinguish an **invalid source value** (data problem) from an
# MAGIC   **invalid format pattern** (code problem)
# MAGIC - Chain safe parsing into a small operations-style output
# MAGIC
# MAGIC **Prerequisites.** `03 - Safe Type Casting` in this module — you should
# MAGIC already know **`cast`**, **`try_cast`**, ANSI mode, and the rejected-row
# MAGIC pattern **`source.isNotNull() & casted.isNull()`**.
# MAGIC
# MAGIC **Setup.** Attach any compute with PySpark available. This notebook uses
# MAGIC small, hand-built rideshare-style DataFrames aligned with **`trip`**,
# MAGIC **`trip_time`**, and **`payment`** column names from the course dataset.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup context for overflow and parsing examples
# MAGIC
# MAGIC Notebook 03 handled malformed **casts** with **`try_cast`**. Overflow can
# MAGIC still appear during **casts**, **arithmetic**, and **aggregations** under
# MAGIC ANSI mode. Date and timestamp columns often arrive as **text** before
# MAGIC analytics can use them.
# MAGIC
# MAGIC Each section below builds a tiny DataFrame for one failure mode. Column
# MAGIC names align with **`docs/data/dataset-overview.md`**.

# COMMAND ----------

from decimal import Decimal

from pyspark.sql import functions as F

# COMMAND ----------

# MAGIC %md
# MAGIC ## Handle integer cast overflow
# MAGIC
# MAGIC The course stores **`trip_id`** as **`bigint`**. The largest value an
# MAGIC **`int`** can hold is **`2147483647`**. Casting a larger trip ID to
# MAGIC **`int`** raises **`[CAST_OVERFLOW]`** under ANSI mode.
# MAGIC
# MAGIC The first operation shows the error. The second uses **`try_cast`** to
# MAGIC return **`NULL`** instead.

# COMMAND ----------

big_trip_id = spark.createDataFrame(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    [(2147483648,)],
    "trip_id bigint",
)

try:
    big_trip_id.select(F.col("trip_id").cast("int")).show()
except Exception as e:
    print(f"{type(e).__name__}: {str(e).splitlines()[0]}")

# COMMAND ----------

big_trip_id.select(F.col("trip_id").try_cast("int").alias("trip_id_int")).show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Choose a decimal type that fits
# MAGIC
# MAGIC In **`decimal(p, s)`**, **`p`** is the total number of digits and **`s`** is
# MAGIC digits after the decimal point. **`decimal(4, 2)`** max is **`99.99`**.
# MAGIC
# MAGIC The sample fare does not fit that narrow type, so the first cast raises an
# MAGIC error. The course payment schema uses **`decimal(10, 2)`** for
# MAGIC **`base_fare_amount`** — the second cast succeeds.

# COMMAND ----------

fares = spark.createDataFrame(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    [(12345.67,)],
    "base_fare_amount double",
)

try:
    fares.select(F.col("base_fare_amount").cast("decimal(4,2)")).show()
except Exception as e:
    print(f"{type(e).__name__}: {str(e).splitlines()[0]}")

# COMMAND ----------

fares.select(F.col("base_fare_amount").cast("decimal(10,2)").alias("base_fare_amount")).show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Return `NULL` for arithmetic overflow
# MAGIC
# MAGIC Overflow can occur during a calculation, not only in a cast. Set
# MAGIC **`ride_duration_mins`** to the largest **`int`** value — adding it to
# MAGIC itself exceeds the **`int`** range.
# MAGIC
# MAGIC **`try_add`** returns **`NULL`** instead of raising. Related helpers include
# MAGIC **`try_subtract`**, **`try_multiply`**, and **`try_divide`** (**`try_divide`**
# MAGIC also returns **`NULL`** for division by zero).

# COMMAND ----------

max_duration = spark.createDataFrame(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    [(2147483647,)],
    "ride_duration_mins int",
)

max_duration.select(
    F.try_add(
        F.col("ride_duration_mins"),
        F.col("ride_duration_mins"),
    ).alias("doubled_duration_mins")
).show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Handle aggregation overflow
# MAGIC
# MAGIC **`sum`** / **`avg`** can overflow when the result exceeds the column type.
# MAGIC Here, **`base_fare_amount`** uses maximum decimal precision — summing two
# MAGIC max values raises **`[ARITHMETIC_OVERFLOW]`**.
# MAGIC
# MAGIC **`try_sum`** and **`try_avg`** return **`NULL`** for an overflowing result.

# COMMAND ----------

huge_fares = spark.createDataFrame(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    [
        (Decimal("9" * 38),),
        (Decimal("9" * 38),),
    ],
    "base_fare_amount decimal(38,0)",
)

try:
    huge_fares.select(F.expr("sum(base_fare_amount)")).show()
except Exception as e:
    print(f"{type(e).__name__}: {str(e).splitlines()[0]}")

# COMMAND ----------

huge_fares.select(
    F.expr("try_sum(base_fare_amount)").alias("safe_sum"),
    F.expr("try_avg(base_fare_amount)").alias("safe_avg"),
).show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Convert text to dates and timestamps
# MAGIC
# MAGIC **`trip_time`** stores **`trip_date`** and **`hour_of_day`**. Build timestamp
# MAGIC text from both, then parse with format patterns:
# MAGIC
# MAGIC - **`yyyy`** — year; **`MM`** — month; **`dd`** — day
# MAGIC - **`HH`** — hour (24-hour); **`mm`** — minute; **`ss`** — second
# MAGIC
# MAGIC **`to_date`** converts date text. **`to_timestamp`** parses the combined date
# MAGIC and hour string.

# COMMAND ----------

events = spark.createDataFrame(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    [(1001, "2026-07-16", 14)],
    "trip_id bigint, trip_date string, hour_of_day int",
)

timestamp_text = F.expr(
    "concat(trip_date, ' ', lpad(cast(hour_of_day AS string), 2, '0'), ':00:00')"
)

parsed = events.select(
    "trip_id",
    F.to_date(F.col("trip_date"), "yyyy-MM-dd").alias("trip_date"),
    "hour_of_day",
    F.to_timestamp(timestamp_text, "yyyy-MM-dd HH:mm:ss").alias("trip_timestamp"),
)

parsed.printSchema()
parsed.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Return `NULL` for invalid timestamps
# MAGIC
# MAGIC Malformed **`trip_date`** or invalid **`hour_of_day`** produces text that
# MAGIC **`to_timestamp`** cannot parse — it raises under ANSI mode.
# MAGIC
# MAGIC **`try_to_timestamp`** returns **`NULL`** instead. Keep source columns beside
# MAGIC the result so rejected values stay visible.

# COMMAND ----------

messy = spark.createDataFrame(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    [
        (1001, "2026-07-16", 9),
        (1002, "not-a-date", 14),
        (1003, "2026-13-40", 99),
    ],
    "trip_id bigint, trip_date string, hour_of_day int",
)

try:
    messy.select(
        F.to_timestamp(timestamp_text, "yyyy-MM-dd HH:mm:ss").alias("trip_timestamp")
    ).show()
except Exception as e:
    print(f"{type(e).__name__}: {str(e).splitlines()[0]}")

# COMMAND ----------

parsed_messy = messy.select(
    "trip_id",
    "trip_date",
    "hour_of_day",
    F.try_to_timestamp(timestamp_text, F.lit("yyyy-MM-dd HH:mm:ss")).alias("trip_timestamp"),
)

parsed_messy.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Return `NULL` for invalid dates
# MAGIC
# MAGIC For ISO-shaped text such as **`yyyy-MM-dd`**, **`try_cast(... AS DATE)`** or
# MAGIC **`try_to_date`** returns **`NULL`** instead of raising for invalid source
# MAGIC strings.

# COMMAND ----------

dates = spark.createDataFrame(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    [("2026-07-16",), ("not-a-date",), ("2026-02-30",)],
    "trip_date string",
)

dates.select(
    "trip_date",
    F.expr("try_cast(trip_date AS DATE)").alias("parsed_trip_date"),
    F.try_to_date(F.col("trip_date"), F.lit("yyyy-MM-dd")).alias("parsed_with_try_to_date"),
).show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Distinguish invalid source from invalid format pattern
# MAGIC
# MAGIC An invalid **source value** is a data problem — tolerant parsing can return
# MAGIC **`NULL`**. An invalid **format pattern** is a code problem — fix the pattern
# MAGIC in code; **`try_*`** cannot make an unsupported pattern valid.
# MAGIC
# MAGIC Spark datetime patterns use lowercase **`yyyy`** for a calendar year. The
# MAGIC pattern **`YYYY-QQ-DD`** is invalid — Spark rejects it before parsing rows.

# COMMAND ----------

try:
    dates.select(F.to_date(F.col("trip_date"), "YYYY-QQ-DD")).show()
except Exception as e:
    print(f"{type(e).__name__}: {str(e).splitlines()[0]}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Chain safe parsing into an operations-style output
# MAGIC
# MAGIC **Business question:** Which trip timestamps parsed successfully, and which
# MAGIC rows need review because parsing returned **`NULL`** while source text was
# MAGIC present?

# COMMAND ----------

accepted_timestamps = parsed_messy.filter(F.col("trip_timestamp").isNotNull())

rejected_timestamps = parsed_messy.filter(
    F.col("trip_date").isNotNull() & F.col("trip_timestamp").isNull()
)

print("Parsed successfully")
accepted_timestamps.show(truncate=False)

print("Requires data-quality review")
rejected_timestamps.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC **Business question:** How can operations combine safe arithmetic and
# MAGIC timestamp parsing in one review table without stopping the pipeline when
# MAGIC overflow or invalid source values occur?

# COMMAND ----------

operations_input = spark.createDataFrame(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    [
        (1001, "2026-07-16", 9, 30),
        (1002, "not-a-date", 14, 2147483647),
        (1003, "2026-13-40", 99, 45),
    ],
    "trip_id bigint, trip_date string, hour_of_day int, ride_duration_mins int",
)

operations_review = operations_input.select(
    "trip_id",
    "trip_date",
    "hour_of_day",
    "ride_duration_mins",
    F.try_add(
        F.col("ride_duration_mins"),
        F.col("ride_duration_mins"),
    ).alias("doubled_duration_mins"),
    F.try_to_timestamp(timestamp_text, F.lit("yyyy-MM-dd HH:mm:ss")).alias("trip_timestamp"),
)

operations_review.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC A **`NULL`** in **`doubled_duration_mins`** or **`trip_timestamp`** marks a
# MAGIC value that requires review; non-**`NULL`** results remain usable in the same
# MAGIC batch.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Use a second small rideshare-style DataFrame named **`exercise_df`** and
# MAGIC complete:
# MAGIC
# MAGIC 1. Create **`exercise_df`** with **`trip_id`** and **`trip_date`** as
# MAGIC    **`string`** (`trip_time` table). Include at least one valid ISO-shaped
# MAGIC    date and one invalid date string.
# MAGIC 2. Add **`trip_date_parsed`** with **`try_to_date`** (or
# MAGIC    **`try_cast(... AS DATE)`**) and a matching format pattern.
# MAGIC 3. Filter to rows where source **`trip_date`** is not **`NULL`** but
# MAGIC    **`trip_date_parsed`** is **`NULL`**.
# MAGIC 4. Show the rejected rows.
# MAGIC
# MAGIC Keep the DataFrame tiny (three or four rows).

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC Recap this notebook's overflow and parsing path:
# MAGIC
# MAGIC - **Cast overflow** — use **`try_cast`** when a too-large value should
# MAGIC   become **`NULL`**
# MAGIC - **Arithmetic overflow** — **`try_add`** and related **`try_*`** operators
# MAGIC - **Aggregation overflow** — **`try_sum`** / **`try_avg`**
# MAGIC - **Date/timestamp parsing** — **`to_date`** / **`to_timestamp`** with
# MAGIC   explicit patterns; **`try_to_*`** for bad source text
# MAGIC - **Bad data vs bad pattern** — fix patterns in code; use **`try_*`** for
# MAGIC   bad source values
# MAGIC - **Review output** — keep source columns beside safe results; split
# MAGIC   accepted vs rejected rows
# MAGIC
# MAGIC Next up: **Module 4 — Transformations, Actions, and Lazy Evaluation** —
# MAGIC how Spark builds and executes the transformation chains you already write.
