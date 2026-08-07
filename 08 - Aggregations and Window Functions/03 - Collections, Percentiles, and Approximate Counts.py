# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC
# MAGIC # 03 - Collections, Percentiles, and Approximate Counts
# MAGIC
# MAGIC ## Three aggregate patterns used in data projects
# MAGIC
# MAGIC This notebook answers three practical questions:
# MAGIC
# MAGIC 1. Which values belong to each group?
# MAGIC 2. What do typical and upper-end values look like?
# MAGIC 3. When is an estimated distinct count useful?
# MAGIC
# MAGIC **Reads:** `rideshare_dev.processed.trip_enriched` (106 rows) and
# MAGIC `rideshare_dev.processed.trip_driver_assignment` (100 rows). **No writes.**
# MAGIC
# MAGIC **Prerequisites:** Notebook 01 (`groupBy`, aliases, counts, NULL exclusion);
# MAGIC Notebook 02 (composite keys and output grain); Module 6 (`struct`).

# COMMAND ----------

# DBTITLE 1,Setup
# MAGIC %md
# MAGIC ## Setup — load both managed tables
# MAGIC
# MAGIC Setup details and the inherited NULL map stay in Notebook 01.
# MAGIC
# MAGIC | DataFrame | Input grain | Columns used here |
# MAGIC |---|---|---|
# MAGIC | `trip_enriched` | One row per trip | service, distance, locations, payment |
# MAGIC | `trip_driver_assignment` | One row per driver-trip assignment | driver, service |

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

# DBTITLE 1,Section 1 - collect_list
# MAGIC %md
# MAGIC ## 1. Collect grouped values
# MAGIC
# MAGIC The 100 assignment rows belong to 12 drivers, with 8 or 9 trips per driver.
# MAGIC
# MAGIC ### Which service types did each driver handle?
# MAGIC
# MAGIC `collect_list` keeps every value, including duplicates.
# MAGIC
# MAGIC **Output grain:** one row per `driver_id` — 12 expected rows.

# COMMAND ----------

driver_service_lists = trip_driver_assignment.groupBy("driver_id").agg(
    F.sort_array(F.collect_list(F.col("service_type"))).alias("service_type_list"),
)

driver_service_lists.orderBy("driver_id").show(12, truncate=False)

# COMMAND ----------

# DBTITLE 1,Section 1a - collect_set
# MAGIC %md
# MAGIC ### Which unique service types did each driver handle?
# MAGIC
# MAGIC A repeated service type is useful in a trip history but not in a list of
# MAGIC services the driver has handled. `collect_set` removes those duplicates.

# COMMAND ----------

driver_service_collections = trip_driver_assignment.groupBy("driver_id").agg(
    F.sort_array(F.collect_list(F.col("service_type"))).alias("all_service_types"),
    F.sort_array(F.collect_set(F.col("service_type"))).alias("unique_service_types"),
)

driver_service_collections.orderBy("driver_id").show(12, truncate=False)

# COMMAND ----------

# DBTITLE 1,Collection behavior
# MAGIC %md
# MAGIC Each list has 8 or 9 entries; each set has 3 or 4 unique services.
# MAGIC
# MAGIC Do not rely on the order returned by either collection function.
# MAGIC `sort_array` makes presentation order explicit.
# MAGIC
# MAGIC **Production note:** use collection aggregates when each group is reasonably
# MAGIC bounded. Large groups create large arrays.
# MAGIC
# MAGIC One `STANDARD` trip has a NULL `payment_method`. Is that NULL collected?

# COMMAND ----------

standard_payment_collections = trip_enriched.filter(F.col("service_type") == "STANDARD").agg(
    F.count("*").alias("standard_trip_count"),
    F.count(F.col("payment_method")).alias("known_payment_method_count"),
    F.size(F.collect_list(F.col("payment_method"))).alias("collected_list_size"),
    F.sort_array(F.collect_set(F.col("payment_method"))).alias("unique_payment_methods"),
)

standard_payment_collections.show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Collection NULL conclusion
# MAGIC %md
# MAGIC `STANDARD` has 55 trips but only 54 collected payment methods.
# MAGIC `collect_list` and `collect_set` exclude top-level NULLs, just like
# MAGIC `count("payment_method")`.

# COMMAND ----------

# DBTITLE 1,Section 2 - Percentiles
# MAGIC %md
# MAGIC ## 2. Calculate percentiles
# MAGIC
# MAGIC `trip_enriched` has 103 known trip distances from 1.18 to 17.96 miles.
# MAGIC
# MAGIC ### What is a typical trip distance, and how far are trips near the upper end?
# MAGIC
# MAGIC Compare the familiar average with:
# MAGIC
# MAGIC - **p50** — an approximate median: about half the values are at or below it
# MAGIC - **p90** — an upper-tail threshold: about 90% are at or below it

# COMMAND ----------

trip_enriched.agg(
    F.round(F.avg(F.col("trip_distance_miles")), 2).alias("avg_distance_miles"),
    F.percentile_approx(F.col("trip_distance_miles"), 0.50).alias("p50_distance_miles"),
    F.percentile_approx(F.col("trip_distance_miles"), 0.90).alias("p90_distance_miles"),
).show()

# COMMAND ----------

# DBTITLE 1,Percentile interpretation
# MAGIC %md
# MAGIC The average uses all 103 known distances. Approximate p50 identifies the
# MAGIC middle of the distribution, while p90 shows where the longest 10% begins.
# MAGIC
# MAGIC As in Notebook 01, NULL measures are excluded from these calculations.

# COMMAND ----------

# DBTITLE 1,Section 2a - Percentiles by service
# MAGIC %md
# MAGIC ### How do distance distributions differ by service type?
# MAGIC
# MAGIC Calculate average, p50, and p90 inside each service group.
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

# DBTITLE 1,Grouped percentile interpretation
# MAGIC %md
# MAGIC The average gives one overall center, while p50 and p90 separate the middle
# MAGIC from the upper tail. That makes service-level distance patterns easier to
# MAGIC compare.
# MAGIC
# MAGIC Check `known_distance_count` before trusting a percentile. `UNKNOWN` has only
# MAGIC 2 known distances, so its p50 and p90 describe very little data.

# COMMAND ----------

# DBTITLE 1,Section 3 - Exact distinct routes
# MAGIC %md
# MAGIC ## 3. Count distinct values at scale
# MAGIC
# MAGIC The 106 trips use 20 pickup and 20 drop-off locations. That permits up to
# MAGIC 400 location pairs, but only observed pairs are routes in this dataset.
# MAGIC
# MAGIC ### How many distinct pickup-to-drop-off routes appear?
# MAGIC
# MAGIC This is one overall aggregate, so the result has one row.

# COMMAND ----------

trip_enriched.agg(
    F.countDistinct(
        F.col("pickup_location_id"),
        F.col("dropoff_location_id"),
    ).alias("exact_route_count"),
).show()

# COMMAND ----------

# DBTITLE 1,Section 3a - Approximate distinct routes
# MAGIC %md
# MAGIC ### What changes when an estimate is acceptable?
# MAGIC
# MAGIC `approx_count_distinct` estimates cardinality with bounded state instead of
# MAGIC producing an exact answer. Its default relative standard deviation setting
# MAGIC is `0.05`.
# MAGIC
# MAGIC The approximate function accepts one expression, so `struct` represents the
# MAGIC pickup and drop-off IDs as one route value.

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

# DBTITLE 1,Exact vs approximate interpretation
# MAGIC %md
# MAGIC The exact answer is 93 observed routes. The approximate result may match on
# MAGIC this small dataset, but that does not make the function exact.
# MAGIC
# MAGIC Use exact counting when correctness requires the precise value. Consider the
# MAGIC approximate version when cardinality is very large and an estimate is
# MAGIC acceptable. This 106-row dataset demonstrates the API, not a performance gain.

# COMMAND ----------

# DBTITLE 1,Exercise
# MAGIC %md
# MAGIC ## Exercise — pickup-borough summaries
# MAGIC
# MAGIC Build three independent summaries from `trip_enriched`.
# MAGIC
# MAGIC **Shared output grain:** one row per `pickup_borough`.
# MAGIC
# MAGIC Before running the TODO cells, set `predicted_borough_groups` to the expected
# MAGIC number of groups.
# MAGIC
# MAGIC 1. Sorted unique service types
# MAGIC 2. Approximate p50 and p90 ride duration
# MAGIC 3. Exact and approximate distinct drop-off locations
# MAGIC
# MAGIC The final cell verifies that all three outputs preserve the predicted grain.

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
# MAGIC | Pattern | Use it when |
# MAGIC |---|---|
# MAGIC | `collect_list` / `collect_set` | A bounded group needs all or unique values |
# MAGIC | `percentile_approx` | p50 / p90 describe the middle and upper tail |
# MAGIC | `countDistinct` | The result must be exact |
# MAGIC | `approx_count_distinct` | Cardinality is large and an estimate is acceptable |
# MAGIC
# MAGIC **Next:** **`04 - Multi-Level Grouping and Pivot`** — produce subtotals,
# MAGIC multi-dimensional summaries, and pivoted output.
