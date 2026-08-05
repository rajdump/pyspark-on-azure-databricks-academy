# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC # 07 - Build Unified Curated Tables
# MAGIC
# MAGIC Write-only capstone: apply Notebooks **01–06** join patterns to produce the
# MAGIC two managed tables Modules 8–9 read. Business logic and BRD acceptance
# MAGIC checks only — no teaching exercises.
# MAGIC
# MAGIC **Contracts:** `requirements/BRD.md`,
# MAGIC `requirements/trip_enriched_mapping.md`,
# MAGIC `requirements/trip_driver_assignment_mapping.md`.
# MAGIC
# MAGIC **Prerequisites:** Module 7 **`01`–`06`**; Module 6 curated
# MAGIC `trip` / `payment` / `drivers_flat` and landing `trip_time` /
# MAGIC `zone_lookup`.

# COMMAND ----------

# DBTITLE 1,Load sources
from pyspark.sql import functions as F

landing_root = "/Volumes/rideshare_dev/landing/source_files"
curated_root = "/Volumes/rideshare_dev/processed/output_files/curated"

curated_trip = spark.read.format("parquet").load(f"{curated_root}/trip")  # noqa: F821
curated_payment = spark.read.format("parquet").load(f"{curated_root}/payment")  # noqa: F821
drivers_flat = spark.read.format("parquet").load(f"{curated_root}/drivers_flat")  # noqa: F821
trip_time = spark.read.format("parquet").load(  # noqa: F821
    f"{landing_root}/trip_time/trip_time.parquet"
)

zone_lookup_schema_ddl = """
location_id int,
borough_name string,
zone_name string,
service_zone string
"""

zone_lookup = (
    spark.read.format("json")  # noqa: F821
    .schema(zone_lookup_schema_ddl)
    .load(f"{landing_root}/zone_lookup/zone_lookup.json")
)

print("curated_trip:", curated_trip.count(), "(expect 106)")
print("curated_payment:", curated_payment.count(), "(expect 105)")
print("drivers_flat:", drivers_flat.count(), "(expect 100)")
print("trip_time:", trip_time.count(), "(expect 100)")
print("zone_lookup:", zone_lookup.count(), "(expect 22)")

for name, df in [
    ("curated_trip", curated_trip),
    ("curated_payment", curated_payment),
    ("drivers_flat", drivers_flat),
    ("trip_time", trip_time),
]:
    print(f"  {name}.trip_id → {dict(df.dtypes)['trip_id']}")

# COMMAND ----------

# DBTITLE 1,Build trip_enriched
t = curated_trip.alias("t")
tt = trip_time.alias("tt")
pay = curated_payment.alias("pay")
pz = F.broadcast(zone_lookup.alias("pz"))
dz = F.broadcast(zone_lookup.alias("dz"))

trip_enriched = (
    t.join(tt, F.col("t.trip_id") == F.col("tt.trip_id"), "left")
    .join(pay, F.col("t.trip_id") == F.col("pay.trip_id"), "left")
    .join(pz, F.col("t.pickup_location_id") == F.col("pz.location_id"), "left")
    .join(dz, F.col("t.dropoff_location_id") == F.col("dz.location_id"), "left")
    .select(
        F.col("t.trip_id"),
        F.col("t.service_type"),
        F.col("t.pickup_location_id"),
        F.col("t.dropoff_location_id"),
        F.col("t.trip_distance_miles"),
        F.col("t.ride_duration_mins"),
        F.col("tt.trip_date"),
        F.col("tt.hour_of_day"),
        F.col("pay.payment_method"),
        F.col("pay.base_fare_amount"),
        F.col("pay.tip_amount"),
        F.col("pay.driver_payout_amount"),
        F.col("pz.borough_name").alias("pickup_borough"),
        F.col("pz.zone_name").alias("pickup_zone"),
        F.col("dz.borough_name").alias("dropoff_borough"),
        F.col("dz.zone_name").alias("dropoff_zone"),
    )
)

# COMMAND ----------

# DBTITLE 1,Validate and write trip_enriched
assert trip_enriched.count() == 106, "BR-02: trip_enriched must have 106 rows"
assert (
    trip_enriched.filter(F.col("trip_date").isNull()).count() == 6
), "BR-02: expect 6 NULL trip_date rows"
assert (
    trip_enriched.filter(F.col("payment_method").isNull()).count() == 1
), "BR-02: expect 1 NULL payment_method row"
assert (
    trip_enriched.filter(
        F.col("pickup_borough").isNull() | F.col("dropoff_borough").isNull()
    ).count()
    == 0
), "BR-04: every trip zone must resolve"

trip_enriched.write.mode("overwrite").saveAsTable(
    "rideshare_dev.processed.trip_enriched"
)
print("trip_enriched written:", spark.table("rideshare_dev.processed.trip_enriched").count())  # noqa: F821

# COMMAND ----------

# DBTITLE 1,Build trip_driver_assignment
drv = drivers_flat.alias("drv")
tr = curated_trip.alias("tr")

trip_driver_assignment = (
    drv.join(tr, F.col("drv.trip_id") == F.col("tr.trip_id"), "left")
    .select(
        F.col("drv.driver_id"),
        F.col("drv.driver_name"),
        F.col("drv.license_number"),
        F.col("drv.vehicle_make"),
        F.col("drv.vehicle_model"),
        F.col("drv.vehicle_year"),
        F.col("drv.vehicle_body_type"),
        F.col("drv.trip_id"),
        F.col("tr.service_type"),
        F.col("tr.trip_distance_miles"),
        F.col("tr.ride_duration_mins"),
        F.col("tr.pickup_location_id"),
        F.col("tr.dropoff_location_id"),
    )
)

# COMMAND ----------

# DBTITLE 1,Validate and write trip_driver_assignment
assert trip_driver_assignment.count() == 100, "BR-03: expect 100 assignment rows"
assert (
    drivers_flat.join(curated_trip, "trip_id", "left_anti").count() == 0
), "BR-05: no orphan trip_id in drivers_flat"

trip_driver_assignment.write.mode("overwrite").saveAsTable(
    "rideshare_dev.processed.trip_driver_assignment"
)
print(
    "trip_driver_assignment written:",
    spark.table("rideshare_dev.processed.trip_driver_assignment").count(),  # noqa: F821
)

# COMMAND ----------

# DBTITLE 1,AQE note
# MAGIC %md
# MAGIC ## AQE note
# MAGIC
# MAGIC Adaptive Query Execution (AQE) can change join strategy at runtime from
# MAGIC actual sizes. Explicit `F.broadcast()` on `zone_lookup` is still honored —
# MAGIC it is a hint, not overridden by AQE. Deeper plan tuning is Module 16.

# COMMAND ----------

# DBTITLE 1,Output
# MAGIC %md
# MAGIC ## Output
# MAGIC
# MAGIC | Table | Rows | Grain |
# MAGIC |---|---|---|
# MAGIC | `rideshare_dev.processed.trip_enriched` | 106 | one per `trip_id` |
# MAGIC | `rideshare_dev.processed.trip_driver_assignment` | 100 | one per (`driver_id`, `trip_id`) |
# MAGIC
# MAGIC **Next:** Module **8** reads these tables with `spark.table()`.
