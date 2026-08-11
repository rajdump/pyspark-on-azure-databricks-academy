# Databricks notebook source
# MAGIC %md
# MAGIC # 08 - Build KPI Tables
# MAGIC
# MAGIC Build three analytics KPI tables from Module 7's managed sources and write
# MAGIC them as Unity Catalog managed Delta tables. Module 9 reads these tables and
# MAGIC re-expresses the same logic in Spark SQL (dual-API check).
# MAGIC
# MAGIC This notebook applies patterns from Notebooks **01–07** (`groupBy` / `agg`,
# MAGIC NULL-aware filters, `collect_set`, aggregate-then-`dense_rank`). It does not
# MAGIC introduce new APIs.
# MAGIC
# MAGIC | Table | Grain | Rows |
# MAGIC |---|---|---:|
# MAGIC | `rideshare_dev.processed.kpi_daily_trip_summary` | one per `trip_date` | 14 |
# MAGIC | `rideshare_dev.processed.kpi_zone_performance` | one per (`pickup_borough`, `pickup_zone`) | 20 |
# MAGIC | `rideshare_dev.processed.kpi_driver_productivity` | one per `driver_id` | 12 |
# MAGIC
# MAGIC Column contracts: this module's README — Paths and outputs.
# MAGIC Write-only — no exercise (same pattern as Module 7 Notebook **07**).

# COMMAND ----------

# MAGIC %md
# MAGIC ##### LOAD: `trip_enriched` and `trip_driver_assignment`

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

trip_enriched = spark.table("rideshare_dev.processed.trip_enriched")  # noqa: F821
trip_driver_assignment = spark.table(  # noqa: F821
    "rideshare_dev.processed.trip_driver_assignment"
)

print(f"trip_enriched: {trip_enriched.count()} rows")  # expect 106
print(
    f"trip_driver_assignment: {trip_driver_assignment.count()} rows"
)  # expect 100

# COMMAND ----------

# MAGIC %md
# MAGIC ### What does daily trip volume look like across the fleet's 14 active days?
# MAGIC
# MAGIC Finance wants one summary row per calendar day — trip counts, fares, tips,
# MAGIC payouts, distance, and average duration — so Module 9 can chart trends and
# MAGIC running totals.
# MAGIC
# MAGIC **Grain:** one row per `trip_date` → **14** rows (2026-03-01 – 2026-03-14).
# MAGIC
# MAGIC **Filter first:** drop NULL `trip_date` (trips **101–106**). Those six undated
# MAGIC trips are also the only rows with measure NULLs. After the filter, the
# MAGIC remaining **100** trips are fully populated on fare, tip, payout, and
# MAGIC distance — the explicit filter **is** the NULL-handling for this KPI.
# MAGIC
# MAGIC `total_distance_miles` is included so Module 9 can build running totals /
# MAGIC `lag` over dates without re-aggregating trips.

# COMMAND ----------

# MAGIC %md
# MAGIC ##### `1a: Filter dated trips and aggregate`

# COMMAND ----------

# explicit NULL-date removal — measures below are fully populated
dated_trip = trip_enriched.filter(F.col("trip_date").isNotNull())

kpi_daily_trip_summary = dated_trip.groupBy("trip_date").agg(
    F.count("*").alias("trip_count"),
    F.sum("base_fare_amount").alias("total_base_fare"),
    F.sum("tip_amount").alias("total_tip"),
    F.sum("driver_payout_amount").alias("total_driver_payout"),
    F.sum("trip_distance_miles").alias("total_distance_miles"),
    F.round(F.avg("trip_distance_miles"), 2).alias("avg_distance_miles"),
    F.round(F.avg("ride_duration_mins"), 2).alias("avg_ride_duration_mins"),
)

# COMMAND ----------

# MAGIC %md
# MAGIC ##### `1b: Preview daily KPI`

# COMMAND ----------

kpi_daily_trip_summary.orderBy("trip_date").show(14, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ##### `1c: Write daily KPI`

# COMMAND ----------

kpi_daily_trip_summary.write.mode("overwrite").saveAsTable(
    "rideshare_dev.processed.kpi_daily_trip_summary"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ##### `1d: Verify daily KPI`

# COMMAND ----------

daily_out = spark.table(  # noqa: F821
    "rideshare_dev.processed.kpi_daily_trip_summary"
)
print(f"kpi_daily_trip_summary: {daily_out.count()} rows")  # expect 14

# COMMAND ----------

# MAGIC %md
# MAGIC ### Which pickup zones generate the most revenue, and how do tip rates compare?
# MAGIC
# MAGIC Ops wants pickup-zone performance — trip volume, fare and tip totals, and an
# MAGIC aggregate tip percent — across every trip in `trip_enriched`.
# MAGIC
# MAGIC **Grain:** one row per (`pickup_borough`, `pickup_zone`) → **20** rows.
# MAGIC
# MAGIC Uses **all 106** rows (no date filter). This is the module's **primary
# MAGIC NULL-aggregate surface** — `sum` / `avg` skip NULLs inside affected zones.
# MAGIC
# MAGIC | Pickup zone | NULL measures | Source trip(s) |
# MAGIC |---|---|---|
# MAGIC | Manhattan / Financial District | `base_fare_amount` | 104 |
# MAGIC | Manhattan / Harlem | `base_fare`, `tip`, `distance` (densest) | 106 |
# MAGIC | Queens / Astoria | `tip_amount`, `trip_distance_miles` | 103 |
# MAGIC | Brooklyn / Williamsburg | `trip_distance_miles` only | 105 |
# MAGIC
# MAGIC For Williamsburg, NULL distance lowers the denominator of
# MAGIC `avg_distance_miles` (avg skips that row) while `trip_count` still includes
# MAGIC the trip.
# MAGIC
# MAGIC **`tip_percent_of_base`:** `100 * sum(tip) / sum(base)` when
# MAGIC `sum(base) > 0`, else NULL — aggregate ratio, not the average of row-level
# MAGIC percents. The guard is defensive (no zone has a zero base sum here).

# COMMAND ----------

# MAGIC %md
# MAGIC ##### `2a: Aggregate by pickup zone`

# COMMAND ----------

kpi_zone_performance = trip_enriched.groupBy(
    "pickup_borough",
    "pickup_zone",
).agg(
    # one location_id per zone — max is deterministic
    F.max("pickup_location_id").alias("pickup_location_id"),
    F.count("*").alias("trip_count"),
    F.sum("base_fare_amount").alias("total_base_fare"),
    F.sum("tip_amount").alias("total_tip"),
    # tip percent only when base fare sum is positive; else NULL
    F.when(
        F.sum("base_fare_amount") > 0,
        F.round(
            F.lit(100) * F.sum("tip_amount") / F.sum("base_fare_amount"),
            1,
        ),
    )
    .otherwise(F.lit(None))
    .alias("tip_percent_of_base"),
    F.round(F.avg("trip_distance_miles"), 2).alias("avg_distance_miles"),
    F.round(F.avg("ride_duration_mins"), 2).alias("avg_ride_duration_mins"),
)

# COMMAND ----------

# MAGIC %md
# MAGIC ##### `2b: Preview zone KPI`

# COMMAND ----------

kpi_zone_performance.orderBy(
    "pickup_borough",
    "pickup_zone",
).show(20, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ##### `2c: Write zone KPI`

# COMMAND ----------

kpi_zone_performance.write.mode("overwrite").saveAsTable(
    "rideshare_dev.processed.kpi_zone_performance"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ##### `2d: Verify zone KPI`

# COMMAND ----------

zone_out = spark.table(  # noqa: F821
    "rideshare_dev.processed.kpi_zone_performance"
)
print(f"kpi_zone_performance: {zone_out.count()} rows")  # expect 20

# COMMAND ----------

# MAGIC %md
# MAGIC ### Which drivers cover the most distance across the fleet?
# MAGIC
# MAGIC Fleet ops wants one productivity row per driver — trip count, total
# MAGIC distance, average ride duration, service mix — then a fleet-wide distance
# MAGIC rank.
# MAGIC
# MAGIC **Grain:** one row per `driver_id` → **12** rows.
# MAGIC
# MAGIC **Source:** `trip_driver_assignment` (trips 1–100 only; **no NULLs**).
# MAGIC
# MAGIC **Two-step pattern:** aggregate first, then `dense_rank` the aggregated
# MAGIC result (do not rank trip-level rows and collapse afterward).

# COMMAND ----------

# MAGIC %md
# MAGIC ##### `3a: Aggregate per driver`

# COMMAND ----------

driver_agg = trip_driver_assignment.groupBy("driver_id").agg(
    # max(driver_name) is deterministic — one name per driver_id
    F.max("driver_name").alias("driver_name"),
    F.count("*").alias("trip_count"),
    F.sum("trip_distance_miles").alias("total_distance_miles"),
    F.round(F.avg("ride_duration_mins"), 2).alias("avg_ride_duration_mins"),
    F.sort_array(F.collect_set("service_type")).alias("unique_service_types"),
)

# COMMAND ----------

# MAGIC %md
# MAGIC ##### `3b: Rank by total distance (fleet-wide)`

# COMMAND ----------

distance_rank_window = Window.orderBy(F.col("total_distance_miles").desc())

kpi_driver_productivity = driver_agg.withColumn(
    "distance_dense_rank",
    F.dense_rank().over(distance_rank_window),
)

# COMMAND ----------

# MAGIC %md
# MAGIC ##### `3c: Preview driver KPI`

# COMMAND ----------

kpi_driver_productivity.orderBy(
    "distance_dense_rank",
    "driver_id",
).show(12, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ##### `3d: Write driver KPI`

# COMMAND ----------

kpi_driver_productivity.write.mode("overwrite").saveAsTable(
    "rideshare_dev.processed.kpi_driver_productivity"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ##### `3e: Verify driver KPI`

# COMMAND ----------

driver_out = spark.table(  # noqa: F821
    "rideshare_dev.processed.kpi_driver_productivity"
)
print(f"kpi_driver_productivity: {driver_out.count()} rows")  # expect 12

# COMMAND ----------

# MAGIC %md
# MAGIC ## Output
# MAGIC
# MAGIC | Table | Rows | Grain |
# MAGIC |---|---:|---|
# MAGIC | `rideshare_dev.processed.kpi_daily_trip_summary` | 14 | one per `trip_date` |
# MAGIC | `rideshare_dev.processed.kpi_zone_performance` | 20 | one per (`pickup_borough`, `pickup_zone`) |
# MAGIC | `rideshare_dev.processed.kpi_driver_productivity` | 12 | one per `driver_id` |
# MAGIC
# MAGIC **Pattern:** filter (when needed) → aggregate → preview → write → count.
# MAGIC
# MAGIC Written with `.mode("overwrite").saveAsTable(...)`. Cleared by Module 5
# MAGIC Notebook **99** Level 4 (catalog teardown), same as Module 7 managed tables.
# MAGIC
# MAGIC **Next:** Module 9 re-expresses these KPIs in Spark SQL and validates both
# MAGIC APIs produce matching results.
