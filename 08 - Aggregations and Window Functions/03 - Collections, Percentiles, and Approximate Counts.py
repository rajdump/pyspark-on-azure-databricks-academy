# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC
# MAGIC # 03 - Collections, Percentiles, and Approximate Counts
# MAGIC
# MAGIC `groupBy` with `count`, `sum`, and `avg` covers many common aggregation needs.
# MAGIC This notebook adds `collect_list` / `collect_set`, `percentile_approx`, and
# MAGIC `countDistinct` / `approx_count_distinct`.
# MAGIC
# MAGIC ## What this notebook teaches
# MAGIC
# MAGIC | Section | Concept | Why it matters |
# MAGIC |---|---|---|
# MAGIC | 1 | `collect_list` / `collect_set` | Build a driver profile showing all service types handled, or only the unique service types. |
# MAGIC | 2 | `avg` vs `percentile_approx` (p50 / p90) | Compare average trip distance with median and upper-range distance thresholds. |
# MAGIC | 3 | `countDistinct` vs `approx_count_distinct` | Count how many unique pickup-to-drop-off routes appear, exactly or approximately. |
# MAGIC | Exercise | Same three patterns by `pickup_borough` | Apply the same aggregation patterns to borough-level questions. |
# MAGIC
# MAGIC **Reads:** `rideshare_dev.processed.trip_enriched` (106 rows) and
# MAGIC `rideshare_dev.processed.trip_driver_assignment` (100 rows). **No writes.**
# MAGIC
# MAGIC **Prerequisites:** Notebook 01; Notebook 02; Module 6 Notebook 02 (structs).

# COMMAND ----------

# DBTITLE 1,Setup
# MAGIC %md
# MAGIC ## Setup
# MAGIC
# MAGIC | DataFrame | Grain | Used for |
# MAGIC |---|---|---|
# MAGIC | `trip_driver_assignment` | One driver-trip assignment | Section 1 (collections) |
# MAGIC | `trip_enriched` | One trip | Sections 2–3 and exercise |

# COMMAND ----------

from pyspark.sql import functions as F

trip_enriched_table = "rideshare_dev.processed.trip_enriched"
trip_driver_assignment_table = "rideshare_dev.processed.trip_driver_assignment"

trip_enriched = spark.table(trip_enriched_table)  # noqa: F821
trip_driver_assignment = spark.table(trip_driver_assignment_table)  # noqa: F821

# COMMAND ----------

# DBTITLE 1,Which services did each driver handle?
# MAGIC %md
# MAGIC ## 1. Collect grouped values
# MAGIC
# MAGIC ### Which service types did each driver handle — all, or only unique?
# MAGIC
# MAGIC `collect_list` keeps repeats. `collect_set` keeps unique values only.
# MAGIC `sort_array` is for readable display, not trip order.

# COMMAND ----------

driver_service_collections = trip_driver_assignment.groupBy("driver_id").agg(
    F.sort_array(F.collect_list(F.col("service_type"))).alias("all_service_types"),
    F.sort_array(F.collect_set(F.col("service_type"))).alias("unique_service_types"),
)

driver_service_collections.orderBy("driver_id").show(12, truncate=False)

# COMMAND ----------

# DBTITLE 1,Which payment methods appear on STANDARD trips?
# MAGIC %md
# MAGIC ### Which payment methods appear on STANDARD trips?
# MAGIC
# MAGIC Build the payment-method list and unique set for `STANDARD`. Trip count can
# MAGIC be higher than the collected list size when a trip has no payment method —
# MAGIC `collect_list` and `collect_set` skip NULLs.

# COMMAND ----------

standard_payment_collections = trip_enriched.filter(F.col("service_type") == "STANDARD").agg(
    F.count("*").alias("standard_trip_count"),
    F.count(F.col("payment_method")).alias("known_payment_method_count"),
    F.size(F.collect_list(F.col("payment_method"))).alias("collected_list_size"),
    F.sort_array(F.collect_set(F.col("payment_method"))).alias("unique_payment_methods"),
)

standard_payment_collections.show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Typical distance and upper-range threshold
# MAGIC %md
# MAGIC ## 2. Calculate percentiles
# MAGIC
# MAGIC ### What is a typical trip distance, and where does the upper range begin?
# MAGIC
# MAGIC Compare `avg` with approximate p50 (typical) and p90 (upper-range threshold).

# COMMAND ----------

trip_enriched.agg(
    F.round(F.avg(F.col("trip_distance_miles")), 2).alias("avg_distance_miles"),
    F.percentile_approx(F.col("trip_distance_miles"), 0.50).alias("p50_distance_miles"),
    F.percentile_approx(F.col("trip_distance_miles"), 0.90).alias("p90_distance_miles"),
).show()

# COMMAND ----------

# DBTITLE 1,Distance patterns by service type
# MAGIC %md
# MAGIC ### How do trip-distance patterns differ by service type?
# MAGIC
# MAGIC Read `known_distance_count` before trusting a group's p50 / p90 — a tiny
# MAGIC group (for example `UNKNOWN`) is not a broad pattern.

# COMMAND ----------

service_distance_percentiles = trip_enriched.groupBy("service_type").agg(
    F.count(F.col("trip_distance_miles")).alias("known_distance_count"),
    F.round(F.avg(F.col("trip_distance_miles")), 2).alias("avg_distance_miles"),
    F.percentile_approx(F.col("trip_distance_miles"), 0.50).alias("p50_distance_miles"),
    F.percentile_approx(F.col("trip_distance_miles"), 0.90).alias("p90_distance_miles"),
)

service_distance_percentiles.orderBy("service_type").show(truncate=False)

# COMMAND ----------

# DBTITLE 1,How many unique routes appear?
# MAGIC %md
# MAGIC ## 3. Count distinct values at scale
# MAGIC
# MAGIC ### How many unique pickup-to-drop-off routes appear?
# MAGIC
# MAGIC `countDistinct` on pickup and drop-off IDs returns the exact route count.

# COMMAND ----------

trip_enriched.agg(
    F.countDistinct(
        F.col("pickup_location_id"),
        F.col("dropoff_location_id"),
    ).alias("exact_route_count"),
).show()

# COMMAND ----------

# DBTITLE 1,Exact vs approximate route count
# MAGIC %md
# MAGIC ### What if an estimate is enough?
# MAGIC
# MAGIC `approx_count_distinct` takes one expression, so wrap the two IDs with
# MAGIC `struct`. A matching count on this small table does not make the estimate exact.

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

# DBTITLE 1,Exercise
# MAGIC %md
# MAGIC ## Exercise — pickup-borough summaries
# MAGIC
# MAGIC Same three patterns, one row per `pickup_borough`.
# MAGIC
# MAGIC 1. Unique service types per borough
# MAGIC 2. p50 and p90 of `ride_duration_mins` per borough
# MAGIC 3. Exact vs approximate distinct `dropoff_location_id` per borough
# MAGIC
# MAGIC Predict the borough group count, complete the TODOs, then verify.

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
# MAGIC | `collect_list` / `collect_set` | Per-group arrays — repeats vs unique values (NULLs skipped) |
# MAGIC | `percentile_approx` | p50 / p90 thresholds alongside `avg` |
# MAGIC | `countDistinct` | Exact distinct counts |
# MAGIC | `approx_count_distinct` | Approximate distinct counts at scale |
# MAGIC
# MAGIC **Next:** **`04 - Multi-Level Grouping and Pivot`** — add subtotals and reshape
# MAGIC grouped results.
