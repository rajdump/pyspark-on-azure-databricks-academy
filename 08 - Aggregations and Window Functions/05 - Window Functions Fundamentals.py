# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC
# MAGIC # 05 - Window Functions Fundamentals
# MAGIC
# MAGIC A **window function** lets you add group-level information to each row while
# MAGIC keeping the row-level details.
# MAGIC
# MAGIC For example, each driver-trip row can keep its own trip distance while also
# MAGIC showing the driver's total trip count.
# MAGIC
# MAGIC **Qualified rule:** a window function adds group-level values to each detail
# MAGIC row without collapsing the rows. A later `filter()` can still remove rows and
# MAGIC change the result grain.
# MAGIC
# MAGIC ## What this notebook teaches
# MAGIC
# MAGIC | Section | Concept | Why it matters |
# MAGIC |---|---|---|
# MAGIC | 1 | `groupBy` vs window | Add group-level values without collapsing detail rows |
# MAGIC | 2 | Window aggregates | Add counts, totals, and averages to each detail row |
# MAGIC | 3 | Ranking functions | Rank rows within each group |
# MAGIC | 4 | Ranking ties | Control how equal values receive ranks |
# MAGIC | 5 | Deduplication | Keep one winning record per business key |
# MAGIC | Exercise | Combined windows | Combine group metrics and ranking in one result |
# MAGIC
# MAGIC **Reads:** `rideshare_dev.processed.trip_enriched` (106 rows) and
# MAGIC `rideshare_dev.processed.trip_driver_assignment` (100 rows). **No writes.**
# MAGIC
# MAGIC **Prerequisites:** Module 8 Notebooks **01–04**; Module 7 Notebooks
# MAGIC **01–07**, especially **`02 - Silent Join Failures and Validation`** and
# MAGIC **`07 - Build Unified Curated Tables`**.

# COMMAND ----------

# DBTITLE 1,Setup and baseline grain
# MAGIC %md
# MAGIC ## Setup — load both managed tables
# MAGIC
# MAGIC Shared schemas and inherited NULL details remain in Module 8
# MAGIC **`01 - GroupBy and Basic Aggregations`** and `docs/data/dataset-overview.md`.
# MAGIC
# MAGIC | DataFrame | Grain | Used for |
# MAGIC |---|---|---|
# MAGIC | `trip_enriched` | One row per `trip_id` (106) | Section 1, exercise |
# MAGIC | `trip_driver_assignment` | One (`driver_id`, `trip_id`) row (100) | Sections 2–4 |
# MAGIC
# MAGIC `trip_driver_assignment` already contains `trip_distance_miles` and
# MAGIC `ride_duration_mins` on every row, so Sections 2–4 do not need a join to
# MAGIC `trip_enriched`.
# MAGIC
# MAGIC Both columns are non-NULL across the dataset. This lets the ranking examples
# MAGIC focus on **ties**—what happens when two rows have the same value—without
# MAGIC introducing NULL ordering rules.

# COMMAND ----------

# DBTITLE 1,Load and verify the managed tables
from pyspark.sql import functions as F
from pyspark.sql.window import Window

trip_enriched_table = "rideshare_dev.processed.trip_enriched"
trip_driver_assignment_table = "rideshare_dev.processed.trip_driver_assignment"

trip_enriched = spark.table(trip_enriched_table)  # noqa: F821
trip_driver_assignment = spark.table(trip_driver_assignment_table)  # noqa: F821

trip_enriched_rows = trip_enriched.count()
trip_driver_assignment_rows = trip_driver_assignment.count()

print(f"trip_enriched: observed={trip_enriched_rows}, expected=106")
print(f"trip_driver_assignment: observed={trip_driver_assignment_rows}, expected=100")

# COMMAND ----------

# DBTITLE 1,How is a window different from groupBy?
# MAGIC %md
# MAGIC ## 1. How is a window different from `groupBy`?
# MAGIC
# MAGIC A borough report needs the average base fare for each `pickup_borough`.
# MAGIC A grouped result should contain **5 rows**—one per borough.
# MAGIC
# MAGIC The same borough average can also be placed beside every trip. That result
# MAGIC should still contain **106 rows** because each `trip_id` remains present.
# MAGIC
# MAGIC (`F.avg` skips the NULL `base_fare_amount` values on trips 104 and 106. Both
# MAGIC approaches below therefore average the same known fares.)

# COMMAND ----------

# DBTITLE 1,Calculate one average per borough
borough_avg_fare = trip_enriched.groupBy("pickup_borough").agg(
    F.round(
        F.avg(F.col("base_fare_amount")),
        2,
    ).alias("borough_avg_base_fare"),
)

borough_avg_fare.orderBy("pickup_borough").show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Window specification anatomy
# MAGIC %md
# MAGIC ### Window specification anatomy
# MAGIC
# MAGIC A **window specification** identifies which related rows participate in a
# MAGIC calculation.
# MAGIC
# MAGIC - `Window.partitionBy("pickup_borough")` places trips from the same borough in
# MAGIC   the same calculation group.
# MAGIC - `.over(borough_aggregate_window)` applies a function to that group for each
# MAGIC   input row.
# MAGIC
# MAGIC Unlike `groupBy`, `partitionBy` only defines which rows contribute to the
# MAGIC calculation. It does not collapse the output. The borough average repeats
# MAGIC while each trip row remains available.
# MAGIC
# MAGIC Spark may shuffle rows to bring equal partition keys together. Module 16
# MAGIC covers shuffle and window tuning; this notebook stays focused on correctness.

# COMMAND ----------

# DBTITLE 1,Add the borough average to every trip
borough_aggregate_window = Window.partitionBy("pickup_borough")

trip_with_borough_avg = trip_enriched.withColumn(
    "borough_avg_base_fare",
    F.round(
        F.avg(F.col("base_fare_amount")).over(borough_aggregate_window),
        2,
    ),
)

trip_with_borough_avg.select(
    "trip_id",
    "pickup_borough",
    "base_fare_amount",
    "borough_avg_base_fare",
).orderBy(
    "pickup_borough",
    "trip_id",
).show(30, truncate=False)

# COMMAND ----------

# DBTITLE 1,Verify grouped and windowed grain
borough_group_rows = borough_avg_fare.count()
trip_with_borough_avg_rows = trip_with_borough_avg.count()

print(f"groupBy output: observed={borough_group_rows}, expected=5")
print(f"window input: observed={trip_enriched_rows}, expected=106")
print(f"window output: observed={trip_with_borough_avg_rows}, expected=106")
print("window preserved trip rows:", trip_with_borough_avg_rows == trip_enriched_rows)

# COMMAND ----------

# DBTITLE 1,What driver-level metrics can we add to every driver-trip row?
# MAGIC %md
# MAGIC ## 2. What driver-level metrics can we add to every driver-trip row?
# MAGIC
# MAGIC The borough result kept all 106 trip rows. Driver assignments extend that
# MAGIC idea by adding three driver-level metrics to each of their 100 rows.
# MAGIC
# MAGIC Driver D001 gives us a concrete check:
# MAGIC
# MAGIC - **9** assigned `trip_id` values
# MAGIC - **78.50** total `trip_distance_miles`
# MAGIC - **33.67** average `ride_duration_mins`
# MAGIC
# MAGIC Those values should repeat on all nine D001 rows while each trip's own
# MAGIC distance and duration remain unchanged.

# COMMAND ----------

# DBTITLE 1,Add partition-level driver metrics
driver_aggregate_window = Window.partitionBy("driver_id")

driver_with_metrics = (
    trip_driver_assignment.withColumn(
        "driver_trip_count",
        F.count(F.col("trip_id")).over(driver_aggregate_window),
    )
    .withColumn(
        "driver_total_distance_miles",
        F.round(
            F.sum(F.col("trip_distance_miles")).over(driver_aggregate_window),
            2,
        ),
    )
    .withColumn(
        "driver_avg_ride_duration_mins",
        F.round(
            F.avg(F.col("ride_duration_mins")).over(driver_aggregate_window),
            2,
        ),
    )
)

# COMMAND ----------

# DBTITLE 1,Inspect D001 driver metrics
driver_with_metrics.filter(
    F.col("driver_id") == "D001",
).select(
    "driver_id",
    "trip_id",
    "trip_distance_miles",
    "ride_duration_mins",
    "driver_trip_count",
    "driver_total_distance_miles",
    "driver_avg_ride_duration_mins",
).orderBy(
    "trip_id",
).show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Verify driver-trip grain
driver_with_metrics_rows = driver_with_metrics.count()

print(f"driver input: observed={trip_driver_assignment_rows}, expected=100")
print(f"driver output: observed={driver_with_metrics_rows}, expected=100")
print(
    "window preserved driver-trip rows:",
    driver_with_metrics_rows == trip_driver_assignment_rows,
)

# COMMAND ----------

# DBTITLE 1,How do we rank trips within each driver?
# MAGIC %md
# MAGIC ## 3. How do we rank trips within each driver?
# MAGIC
# MAGIC Partitioning decides which driver's rows belong together. Ranking also needs
# MAGIC an order inside each driver. For D001, trip 8 is longest at **12.75 miles**,
# MAGIC so it should appear first.
# MAGIC
# MAGIC | Function | Result when values tie |
# MAGIC |---|---|
# MAGIC | `row_number` | Gives every row a unique sequence number |
# MAGIC | `rank` | Shares the rank, then leaves a gap |
# MAGIC | `dense_rank` | Shares the rank, then continues without a gap |
# MAGIC
# MAGIC We need two ordering rules: one that preserves equal distances for `rank` and
# MAGIC `dense_rank`, and one that gives `row_number` a repeatable tie-breaker.
# MAGIC Section 4 shows why the difference matters.

# COMMAND ----------

# DBTITLE 1,Add three distance rankings
distance_rank_window = Window.partitionBy("driver_id").orderBy(
    F.col("trip_distance_miles").desc(),
)

distance_row_number_window = Window.partitionBy("driver_id").orderBy(
    F.col("trip_distance_miles").desc(),
    F.col("trip_id").asc(),
)

driver_ranked = (
    driver_with_metrics.withColumn(
        "distance_row_number",
        F.row_number().over(distance_row_number_window),
    )
    .withColumn(
        "distance_rank",
        F.rank().over(distance_rank_window),
    )
    .withColumn(
        "distance_dense_rank",
        F.dense_rank().over(distance_rank_window),
    )
)

# COMMAND ----------

# DBTITLE 1,Inspect D001 distance rankings
driver_ranked.filter(
    F.col("driver_id") == "D001",
).select(
    "driver_id",
    "trip_id",
    "trip_distance_miles",
    "distance_row_number",
    "distance_rank",
    "distance_dense_rank",
).orderBy(
    "distance_row_number",
).show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Why D001 rankings agree
# MAGIC %md
# MAGIC All three columns agree for D001 because its nine trip distances are unique.
# MAGIC Equal values are where their behavior separates.
# MAGIC
# MAGIC Keep the partition-only `driver_aggregate_window` separate from these ordered
# MAGIC ranking specifications. Reusing an ordered specification for a total `sum` or
# MAGIC `avg` can change its meaning. Module 8
# MAGIC **`06 - Running Totals and lag/lead`** explains ordered aggregates and frames.

# COMMAND ----------

# DBTITLE 1,What happens when ranking values tie?
# MAGIC %md
# MAGIC ## 4. What happens when ranking values tie?
# MAGIC
# MAGIC D001's unique distances made the functions look identical. D010 contains the
# MAGIC real tie that exposes their differences:
# MAGIC
# MAGIC - Trips 22 and 79 are both **8.81 miles**.
# MAGIC - Deterministic `row_number` should assign **4** and **5** by `trip_id`.
# MAGIC - Both rows should receive `rank` **4** and `dense_rank` **4**.
# MAGIC - The following 7.65-mile trip should receive `rank` **6** but `dense_rank`
# MAGIC   **5**.
# MAGIC
# MAGIC Showing the complete D010 partition makes both the tie and the later gap
# MAGIC visible.

# COMMAND ----------

# DBTITLE 1,Inspect the complete D010 ranking
driver_ranked.filter(
    F.col("driver_id") == "D010",
).select(
    "driver_id",
    "trip_id",
    "trip_distance_miles",
    "distance_row_number",
    "distance_rank",
    "distance_dense_rank",
).orderBy(
    "distance_row_number",
).show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Interpret the D010 tie
# MAGIC %md
# MAGIC The output separates three different requirements:
# MAGIC
# MAGIC - `row_number` gives the tied trips different positions: 4 and 5.
# MAGIC - `rank` keeps both trips at 4, then skips position 5.
# MAGIC - `dense_rank` keeps both trips at 4, then continues at position 5.
# MAGIC
# MAGIC `trip_id` belongs in the `row_number` specification because that sequence must
# MAGIC be repeatable. It stays out of the other specification so equal distances
# MAGIC remain equal ranks.

# COMMAND ----------

# DBTITLE 1,Why did the Module 7 dedup window work?
# MAGIC %md
# MAGIC ## 5. Why did Module 7's dedup window work?
# MAGIC
# MAGIC Deterministic numbering can do more than label rows—it can select one
# MAGIC surviving record.
# MAGIC
# MAGIC Module 7 **`02 - Silent Join Failures and Validation`** used this pattern with
# MAGIC a recency column. Both managed tables in this notebook are already
# MAGIC deduplicated, so this section constructs a tiny update history instead:
# MAGIC **4 update rows**, **2 duplicated `trip_id` values**, and an expected
# MAGIC **2 surviving rows**.
# MAGIC
# MAGIC Here, the largest `update_version` represents the latest record:
# MAGIC
# MAGIC 1. Partition rows by the business key, `trip_id`.
# MAGIC 2. Order each key by `update_version` descending.
# MAGIC 3. Assign `row_number`.
# MAGIC 4. Keep row number 1.
# MAGIC
# MAGIC This deliberate deduplication is the notebook's only row-reducing example.

# COMMAND ----------

# DBTITLE 1,Construct duplicate trip updates
trip_updates = spark.createDataFrame(  # noqa: F821
    [
        (501, "requested", 1),
        (501, "completed", 2),
        (502, "requested", 1),
        (502, "cancelled", 2),
    ],
    schema="trip_id bigint, trip_status string, update_version int",
)

trip_updates.orderBy("trip_id", "update_version").show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Rank every update within its trip
trip_update_window = Window.partitionBy("trip_id").orderBy(
    F.col("update_version").desc(),
)

ranked_trip_updates = trip_updates.withColumn(
    "update_row_number",
    F.row_number().over(trip_update_window),
)

ranked_trip_updates.orderBy(
    "trip_id",
    "update_row_number",
).show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Keep the latest update per trip
latest_trip_updates = (
    ranked_trip_updates.filter(F.col("update_row_number") == 1)
    .drop("update_row_number")
    .orderBy("trip_id")
)

latest_trip_updates.show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Verify the deduplicated grain
trip_updates_rows = trip_updates.count()
latest_trip_updates_rows = latest_trip_updates.count()
latest_trip_ids = latest_trip_updates.select("trip_id").distinct().count()

print(f"input updates: observed={trip_updates_rows}, expected=4")
print(f"latest updates: observed={latest_trip_updates_rows}, expected=2")
print(f"surviving trip_ids: observed={latest_trip_ids}, expected=2")

# COMMAND ----------

# DBTITLE 1,Exercise - Compare trips within service type
# MAGIC %md
# MAGIC ## Exercise — How does each trip compare within its service type?
# MAGIC
# MAGIC Reuse the partition-only pattern from Section 2 and the ordered `dense_rank`
# MAGIC pattern from Section 3. Build the result from `trip_enriched` with:
# MAGIC
# MAGIC 1. `service_trip_count` — count `trip_id` over a partition-only
# MAGIC    `service_type` specification
# MAGIC 2. `service_avg_ride_duration_mins` — average `ride_duration_mins` over the
# MAGIC    same partition-only specification, rounded to two decimals
# MAGIC 3. `ride_duration_dense_rank` — rank `ride_duration_mins` from longest to
# MAGIC    shortest using a separate ordered specification
# MAGIC
# MAGIC `ride_duration_mins` has no NULLs. Leave `trip_id` out of the dense-rank order
# MAGIC so equal durations remain tied. Do not filter the result.
# MAGIC
# MAGIC Predict the output row count before completing the TODOs. Your checks:
# MAGIC
# MAGIC - output rows: **106**
# MAGIC - distinct `trip_id` values: **106**
# MAGIC - every `STANDARD` row repeats `service_trip_count` **55**

# COMMAND ----------

# DBTITLE 1,Exercise step 1 - Define window specifications
predicted_output_rows = None  # TODO: replace with your prediction

# TODO: partition by service_type only; do not add orderBy
service_aggregate_window = None

# TODO: partition by service_type and order by ride_duration_mins descending
service_duration_rank_window = None

# COMMAND ----------

# DBTITLE 1,Exercise step 2 - Build the windowed result
# TODO: replace None with a transformation built from trip_enriched.
# Add:
# - service_trip_count using service_aggregate_window
# - service_avg_ride_duration_mins using service_aggregate_window
# - ride_duration_dense_rank using service_duration_rank_window
service_window_summary = None

# COMMAND ----------

# DBTITLE 1,Exercise step 3 - Verify grain
if service_window_summary is None:
    raise NotImplementedError(
        "Complete service_window_summary before verification.",
    )

exercise_output_rows = service_window_summary.count()
exercise_distinct_trip_ids = service_window_summary.select("trip_id").distinct().count()

prediction_match = "✓" if predicted_output_rows == exercise_output_rows else "✗"
row_grain_match = "✓" if exercise_output_rows == trip_enriched_rows else "✗"
key_grain_match = "✓" if exercise_distinct_trip_ids == trip_enriched_rows else "✗"

print(f"{prediction_match} predicted={predicted_output_rows}, actual={exercise_output_rows}")
print(f"{row_grain_match} input rows={trip_enriched_rows}, output rows={exercise_output_rows}")
print(
    f"{key_grain_match} distinct trip_ids={exercise_distinct_trip_ids},"
    f" expected={trip_enriched_rows}"
)

# COMMAND ----------

# DBTITLE 1,Exercise step 4 - Inspect STANDARD trips
service_window_summary.filter(
    F.col("service_type") == "STANDARD",
).select(
    "service_type",
    "trip_id",
    "ride_duration_mins",
    "service_trip_count",
    "service_avg_ride_duration_mins",
    "ride_duration_dense_rank",
).orderBy(
    "ride_duration_dense_rank",
    "trip_id",
).show(30, truncate=False)

# COMMAND ----------

# DBTITLE 1,Summary
# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - **`groupBy` versus window:** `groupBy` returns one row per group; a window
# MAGIC   can repeat the group metric while keeping detailed rows.
# MAGIC - **Partition-only aggregates:** use them for totals, counts, and averages over
# MAGIC   every row in a partition.
# MAGIC - **Ordered rankings:** choose `row_number`, `rank`, or `dense_rank` based on
# MAGIC   how the business rule should handle ties.
# MAGIC - **Deterministic selection:** use an ordering rule that breaks every tie, then
# MAGIC   keep `row_number == 1` when one record must survive per key.
# MAGIC
# MAGIC **Next:** Module 8 **`06 - Running Totals and lag/lead`** adds ordered frames,
# MAGIC running calculations, `first_value`, `last_value`, `lag`, and `lead`.
# MAGIC Module 8 **`07 - Top-N per Group and Sampling`** then applies ranking to
# MAGIC Top-N questions and introduces sampling.
