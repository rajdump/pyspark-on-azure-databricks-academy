# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC
# MAGIC # 03 - Collections, Percentiles, and Approximate Counts
# MAGIC
# MAGIC ## Build driver profiles, distance bands, and route counts
# MAGIC
# MAGIC A driver profile needs the services that driver has handled. An operations
# MAGIC report needs both a typical trip distance and an upper-range threshold. A
# MAGIC route audit needs the number of pickup-to-drop-off combinations.
# MAGIC
# MAGIC You will build those outputs in three steps:
# MAGIC
# MAGIC 1. Collect service types into driver-level arrays.
# MAGIC 2. Calculate p50 and p90 trip-distance thresholds.
# MAGIC 3. Compare exact and approximate route counts.
# MAGIC
# MAGIC **Reads:** `rideshare_dev.processed.trip_enriched` (106 rows) and
# MAGIC `rideshare_dev.processed.trip_driver_assignment` (100 rows). **No writes.**
# MAGIC
# MAGIC **Prerequisites:** Notebook 01 (`groupBy`, aliases, counts, NULL exclusion);
# MAGIC Notebook 02 (composite keys and output grain); Module 6 (`struct`).

# COMMAND ----------

# DBTITLE 1,Setup
# MAGIC %md
# MAGIC ## Setup — use the table that matches the question
# MAGIC
# MAGIC Driver arrays need repeated trips per driver, so they use
# MAGIC `trip_driver_assignment`. Distance and route summaries use
# MAGIC `trip_enriched`.
# MAGIC
# MAGIC | DataFrame | Input grain | Used for |
# MAGIC |---|---|---|
# MAGIC | `trip_driver_assignment` | One driver-trip assignment | Driver service arrays |
# MAGIC | `trip_enriched` | One trip | Distance, payment, and route summaries |
# MAGIC
# MAGIC Notebook 01 owns the detailed schema and inherited NULL map.

# COMMAND ----------

from pyspark.sql import functions as F

trip_enriched_table = "rideshare_dev.processed.trip_enriched"
trip_driver_assignment_table = "rideshare_dev.processed.trip_driver_assignment"

trip_enriched = spark.table(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    trip_enriched_table
)
trip_driver_assignment = spark.table(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    trip_driver_assignment_table
)

print("trip_enriched rows:", trip_enriched.count())
print("trip_driver_assignment rows:", trip_driver_assignment.count())

# COMMAND ----------

# DBTITLE 1,Which service types did each driver handle?
# MAGIC %md
# MAGIC ## 1. Collect grouped values
# MAGIC
# MAGIC The 100 assignment rows belong to 12 drivers, with 8 or 9 trips per driver.
# MAGIC
# MAGIC ### Which service types did each driver handle?
# MAGIC
# MAGIC A driver can complete the same service type many times. `collect_list` keeps
# MAGIC one service value from every assignment, so repeated services remain.
# MAGIC
# MAGIC **Output grain:** one row per `driver_id` — 12 expected rows.

# COMMAND ----------

driver_service_lists = trip_driver_assignment.groupBy("driver_id").agg(
    F.sort_array(F.collect_list(F.col("service_type"))).alias("service_type_list"),
)

driver_service_lists.orderBy("driver_id").show(12, truncate=False)

# COMMAND ----------

# DBTITLE 1,Which unique service types did each driver handle?
# MAGIC %md
# MAGIC ### Which unique service types did each driver handle?
# MAGIC
# MAGIC A capability list needs each service only once. `collect_set` removes repeated
# MAGIC values. The next result places the full list and unique set side by side.

# COMMAND ----------

driver_service_collections = trip_driver_assignment.groupBy("driver_id").agg(
    F.sort_array(F.collect_list(F.col("service_type"))).alias("all_service_types"),
    F.sort_array(F.collect_set(F.col("service_type"))).alias("unique_service_types"),
)

driver_service_collections.orderBy("driver_id").show(12, truncate=False)

# COMMAND ----------

# DBTITLE 1,Why are the arrays different lengths?
# MAGIC %md
# MAGIC ### Why are the arrays different lengths?
# MAGIC
# MAGIC `all_service_types` has 8 or 9 entries because it keeps one value per trip.
# MAGIC `unique_service_types` has 3 or 4 entries because it removes repeats.
# MAGIC
# MAGIC Do not treat either array as trip order. `sort_array` gives the display a
# MAGIC predictable order. Also keep collected groups bounded: a large group creates
# MAGIC a large array.
# MAGIC
# MAGIC ### Does the `STANDARD` array keep its NULL payment method?
# MAGIC
# MAGIC `STANDARD` has 55 trips, but trip 106 has no `payment_method`. Compare the
# MAGIC row count with the number of values collected.

# COMMAND ----------

standard_payment_collections = trip_enriched.filter(F.col("service_type") == "STANDARD").agg(
    F.count("*").alias("standard_trip_count"),
    F.count(F.col("payment_method")).alias("known_payment_method_count"),
    F.size(F.collect_list(F.col("payment_method"))).alias("collected_list_size"),
    F.sort_array(F.collect_set(F.col("payment_method"))).alias("unique_payment_methods"),
)

standard_payment_collections.show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Why are only 54 payment methods collected?
# MAGIC %md
# MAGIC ### Why are only 54 payment methods collected?
# MAGIC
# MAGIC `collect_list` and `collect_set` skip the NULL input from trip 106. The list
# MAGIC size therefore matches `count("payment_method")`: both return 54.

# COMMAND ----------

# DBTITLE 1,What is typical, and where does the upper range begin?
# MAGIC %md
# MAGIC ## 2. Calculate percentiles
# MAGIC
# MAGIC `trip_enriched` has 103 known trip distances from 1.18 to 17.96 miles.
# MAGIC
# MAGIC ### What is a typical trip distance, and where does the upper range begin?
# MAGIC
# MAGIC An average gives one center, but it does not show where longer trips begin.
# MAGIC Compare it with approximate p50 and p90 thresholds.

# COMMAND ----------

trip_enriched.agg(
    F.round(F.avg(F.col("trip_distance_miles")), 2).alias("avg_distance_miles"),
    F.percentile_approx(F.col("trip_distance_miles"), 0.50).alias("p50_distance_miles"),
    F.percentile_approx(F.col("trip_distance_miles"), 0.90).alias("p90_distance_miles"),
).show()

# COMMAND ----------

# DBTITLE 1,p50 marks the middle; p90 marks the upper range
# MAGIC %md
# MAGIC ### p50 marks the middle; p90 marks the upper range
# MAGIC
# MAGIC About half of the 103 observed distances are at or below p50. About 90% are
# MAGIC at or below p90, leaving roughly 10% above that threshold.
# MAGIC
# MAGIC The three missing distance values are not part of these calculations.

# COMMAND ----------

# DBTITLE 1,How do trip-distance patterns differ by service type?
# MAGIC %md
# MAGIC ### How do trip-distance patterns differ by service type?
# MAGIC
# MAGIC The overall p50 and p90 can hide differences between `STANDARD`, `PREMIUM`,
# MAGIC `SHARED`, `XL`, and `UNKNOWN`. Calculate the same measures inside each group.
# MAGIC
# MAGIC **Output grain:** one row per `service_type` — 5 expected rows.

# COMMAND ----------

service_distance_percentiles = trip_enriched.groupBy("service_type").agg(
    F.count(F.col("trip_distance_miles")).alias("known_distance_count"),
    F.round(F.avg(F.col("trip_distance_miles")), 2).alias("avg_distance_miles"),
    F.percentile_approx(F.col("trip_distance_miles"), 0.50).alias("p50_distance_miles"),
    F.percentile_approx(F.col("trip_distance_miles"), 0.90).alias("p90_distance_miles"),
)

service_distance_percentiles.orderBy("service_type").show(truncate=False)

# COMMAND ----------

# DBTITLE 1,The UNKNOWN group has only two known distances
# MAGIC %md
# MAGIC ### The `UNKNOWN` group has only two known distances
# MAGIC
# MAGIC Read `known_distance_count` before comparing the percentile columns.
# MAGIC `UNKNOWN` has only 2 known distances, so its p50 and p90 describe those two
# MAGIC trips—not a broad service pattern.

# COMMAND ----------

# DBTITLE 1,How many distinct pickup-to-drop-off routes appear?
# MAGIC %md
# MAGIC ## 3. Count distinct values at scale
# MAGIC
# MAGIC The 106 trips use 20 pickup and 20 drop-off locations. That permits up to
# MAGIC 400 location pairs, but only observed pairs are routes in this dataset.
# MAGIC
# MAGIC ### How many distinct pickup-to-drop-off routes appear?
# MAGIC
# MAGIC `countDistinct` treats each pickup and drop-off pair as one route and returns
# MAGIC the exact number observed.
# MAGIC
# MAGIC **Output grain:** one row for the complete dataset.

# COMMAND ----------

trip_enriched.agg(
    F.countDistinct(
        F.col("pickup_location_id"),
        F.col("dropoff_location_id"),
    ).alias("exact_route_count"),
).show()

# COMMAND ----------

# DBTITLE 1,What changes when an estimate is acceptable?
# MAGIC %md
# MAGIC ### What changes when an estimate is acceptable?
# MAGIC
# MAGIC The exact result is 93 routes. On a much larger trip table, an estimated count
# MAGIC may be enough for profiling or monitoring.
# MAGIC
# MAGIC `approx_count_distinct` counts one expression, so `struct` packages the pickup
# MAGIC and drop-off IDs as one route value. The next cell compares that estimate with
# MAGIC the exact count.

# COMMAND ----------

route = F.struct(
    F.col("pickup_location_id"),
    F.col("dropoff_location_id"),
)

trip_enriched.agg(
    F.countDistinct(
        F.col("pickup_location_id"),
        F.col("dropoff_location_id"),
    ).alias("exact_route_count"),
    F.approx_count_distinct(route).alias("approx_route_count"),
).show()

# COMMAND ----------

# DBTITLE 1,Matching counts do not make the estimate exact
# MAGIC %md
# MAGIC ### Matching counts do not make the estimate exact
# MAGIC
# MAGIC The approximate result may also show 93 on these 106 trips. That match belongs
# MAGIC to this input; `approx_count_distinct` still returns an estimate.
# MAGIC
# MAGIC Use `countDistinct` when the precise value matters. Use
# MAGIC `approx_count_distinct` when cardinality is large and an estimate is
# MAGIC acceptable.

# COMMAND ----------

# DBTITLE 1,Exercise
# MAGIC %md
# MAGIC ## Exercise — pickup-borough summaries
# MAGIC
# MAGIC Operations now wants the same three patterns at borough level.
# MAGIC
# MAGIC **Shared output grain:** one row per `pickup_borough`. Predict the number of
# MAGIC borough groups before running the TODO cells.
# MAGIC
# MAGIC 1. Collect the sorted, unique service types in each borough.
# MAGIC 2. Calculate approximate p50 and p90 ride duration in each borough.
# MAGIC 3. Compare exact and approximate distinct drop-off locations in each borough.
# MAGIC
# MAGIC Set `predicted_borough_groups`, complete each TODO, then verify that all three
# MAGIC summaries have the expected row count.

# COMMAND ----------

# DBTITLE 1,Exercise step 1 - Collections
predicted_borough_groups = None  # TODO: replace with your prediction

borough_services = trip_enriched.groupBy("pickup_borough").agg(
    F.count("*").alias("trip_count"),
    # TODO: add sorted unique service types as unique_service_types
)

borough_services.orderBy("pickup_borough").show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Exercise step 2 - Percentiles
borough_duration_percentiles = trip_enriched.groupBy("pickup_borough").agg(
    F.count(F.col("ride_duration_mins")).alias("known_duration_count"),
    # TODO: add approximate p50 as p50_duration_mins
    # TODO: add approximate p90 as p90_duration_mins
)

borough_duration_percentiles.orderBy("pickup_borough").show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Exercise step 3 - Distinct counts
borough_dropoff_counts = trip_enriched.groupBy("pickup_borough").agg(
    F.count("*").alias("trip_count"),
    # TODO: add exact distinct drop-off locations as exact_dropoff_location_count
    # TODO: add approximate distinct locations as approx_dropoff_location_count
)

borough_dropoff_counts.orderBy("pickup_borough").show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Exercise check - Verify grain
summary_group_counts = {
    "borough_services": borough_services.count(),
    "borough_duration_percentiles": borough_duration_percentiles.count(),
    "borough_dropoff_counts": borough_dropoff_counts.count(),
}

for summary_name, actual_groups in summary_group_counts.items():
    matches = "✓" if predicted_borough_groups == actual_groups else "✗"
    print(f"{matches} {summary_name}: predicted={predicted_borough_groups}, actual={actual_groups}")

# COMMAND ----------

# DBTITLE 1,Summary
# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC | Pattern | What it is used for |
# MAGIC |---|---|
# MAGIC | `collect_list` / `collect_set` | Build bounded arrays with repeated or unique values |
# MAGIC | `percentile_approx` | Estimate p50 and p90 thresholds |
# MAGIC | `countDistinct` | Return the exact number of unique values |
# MAGIC | `approx_count_distinct` | Estimate high-cardinality distinct counts |
# MAGIC
# MAGIC **Next:** **`04 - Multi-Level Grouping and Pivot`** — add subtotals and reshape
# MAGIC grouped results.
