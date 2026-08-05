# Databricks notebook source
# MAGIC %md
# MAGIC #####LOAD:`curated_trip, curated_payment, drivers, trip_time & zone_lookup`

# COMMAND ----------

from pyspark.sql import functions as F

landing_root = "/Volumes/rideshare_dev/landing/source_files"
curated_root = "/Volumes/rideshare_dev/processed/output_files/curated"

# Load curated sources
curated_trip = spark.read.format("parquet").load(f"{curated_root}/trip")  # noqa: F821
curated_payment = spark.read.format("parquet").load(f"{curated_root}/payment")  # noqa: F821
drivers_flat = spark.read.format("parquet").load(f"{curated_root}/drivers_flat")  # noqa: F821

# Load landing sources
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

# COMMAND ----------

# MAGIC %md
# MAGIC #####`Verify row counts and trip_id type consistency`

# COMMAND ----------

# Row counts — must match grain contracts
print("curated_trip:", curated_trip.count())   
print("curated_payment:", curated_payment.count())  
print("drivers_flat:", drivers_flat.count())   
print("trip_time:", trip_time.count())         
print("zone_lookup:", zone_lookup.count())     

# Type consistency — trip_id must be the same type across all sources.
# A type mismatch would silently return 0 join matches (NB 01 lesson).
for name, df in [("curated_trip", curated_trip), ("curated_payment", curated_payment),
                 ("drivers_flat", drivers_flat), ("trip_time", trip_time)]:
    tid_type = dict(df.dtypes)["trip_id"]
    print(f"  {name}.trip_id → {tid_type}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### trip_enriched implementation

# COMMAND ----------

# DBTITLE 1,trip_enriched
# MAGIC %md
# MAGIC ##### `1a:Left join trip_time and curated_payment`

# COMMAND ----------

# Aliases keep column references unambiguous across multiple joins.
t = curated_trip.alias("t")
tt = trip_time.alias("tt")
pay = curated_payment.alias("pay")

# Step 1: trip + trip_time (6 trips will have NULL date/hour)
trip_with_time = t.join(
    tt,
    F.col("t.trip_id") == F.col("tt.trip_id"),
    "left",
)

# Step 2: + curated_payment (trip 106 will have NULL payment cols)
trip_with_time_pay = trip_with_time.join(
    pay,
    F.col("t.trip_id") == F.col("pay.trip_id"),
    "left",
)

# COMMAND ----------

# MAGIC %md
# MAGIC ##### `1b:broadcast zone_lookup`

# COMMAND ----------

# zone_lookup is 22 rows — broadcast avoids shuffling the fact side.
# Same pattern as NB 03 Section 4: alias + F.broadcast + Boolean condition.
pz = F.broadcast(zone_lookup.alias("pz"))
dz = F.broadcast(zone_lookup.alias("dz"))

trip_full = (
    trip_with_time_pay
    .join(pz, F.col("t.pickup_location_id") == F.col("pz.location_id"), "left")
    .join(dz, F.col("t.dropoff_location_id") == F.col("dz.location_id"), "left")
)

# COMMAND ----------

# MAGIC %md
# MAGIC #####  `1c. Select and rename — 16 target columns`

# COMMAND ----------

# Select exactly the 16 target columns per the mapping contract.
# Alias-qualified references avoid ambiguous-column errors from the joins.
trip_enriched = trip_full.select(
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

# COMMAND ----------

# MAGIC %md
# MAGIC #####  `1d.Write trip_enriched to Unity Catalog`

# COMMAND ----------

trip_enriched.write.mode("overwrite").saveAsTable(
    "rideshare_dev.processed.trip_enriched"
)

# COMMAND ----------

# DBTITLE 1,trip_driver_assignment
# MAGIC %md
# MAGIC ## `trip_driver_assignment`

# COMMAND ----------

# MAGIC %md
# MAGIC #####  `2a: Build — drivers_flat LEFT JOIN curated_trip`

# COMMAND ----------

drv = drivers_flat.alias("drv")
tr = curated_trip.alias("tr")

driver_trip = drv.join(
    tr,
    F.col("drv.trip_id") == F.col("tr.trip_id"),
    "left",
)

# Select the 13 target columns per the mapping contract.
trip_driver_assignment = driver_trip.select(
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

# COMMAND ----------

# MAGIC %md
# MAGIC #####  `2b: Write trip_driver_assignment to Unity Catalog`

# COMMAND ----------

trip_driver_assignment.write.mode("overwrite").saveAsTable(
    "rideshare_dev.processed.trip_driver_assignment"
)

# COMMAND ----------

# DBTITLE 1,AQE — what happened behind the scenes
# MAGIC %md
# MAGIC ## Note — Adaptive Query Execution (AQE)
# MAGIC
# MAGIC You did not tune anything in this notebook, yet Spark silently optimized the
# MAGIC joins at runtime. That’s **Adaptive Query Execution (AQE)** — enabled by
# MAGIC default since Spark 3.2.
# MAGIC
# MAGIC AQE re-optimizes the physical plan *during* execution based on actual
# MAGIC statistics collected after each shuffle stage:
# MAGIC
# MAGIC | AQE capability | What it does | Relevance here |
# MAGIC |---|---|---|
# MAGIC | **Auto-broadcast** | Converts a shuffle join to a broadcast join when the materialized side turns out to be small | `trip_time` (100 rows) and `curated_payment` (105 rows) are candidates even without `F.broadcast()` |
# MAGIC | **Partition coalescing** | Merges small post-shuffle partitions into fewer, larger ones | Reduces task overhead on our 100–106 row tables |
# MAGIC | **Skew join handling** | Splits a skewed partition into smaller sub-partitions | Not triggered here (data is uniform), but matters on production fact tables |
# MAGIC
# MAGIC **Why we still used `F.broadcast()` explicitly for `zone_lookup`:**
# MAGIC
# MAGIC - `F.broadcast()` is a *hint* — Spark honors it unconditionally, even before
# MAGIC   AQE collects statistics. This guarantees no shuffle on the zone lookup
# MAGIC   regardless of the planner’s cost model.
# MAGIC - AQE’s auto-broadcast kicks in *after* a shuffle exchange has already been
# MAGIC   planned and data has been partially materialized. The explicit hint avoids
# MAGIC   that wasted work.
# MAGIC
# MAGIC **Key takeaway:** AQE is not a replacement for understanding join mechanics
# MAGIC — it’s a safety net. It cannot fix a wrong join type (inner vs left), a
# MAGIC missing key column, or an M:M fanout. Those problems still require the grain
# MAGIC and cardinality thinking from Notebooks 01–02.
# MAGIC
# MAGIC Module 16 dives deeper into physical plans, AQE configuration, and
# MAGIC join-strategy control.

# COMMAND ----------

# DBTITLE 1,Summary
# MAGIC %md
# MAGIC ## Output
# MAGIC
# MAGIC | Table | Rows | Grain |
# MAGIC |---|---|---|
# MAGIC | `rideshare_dev.processed.trip_enriched` | 106 | one per `trip_id` |
# MAGIC | `rideshare_dev.processed.trip_driver_assignment` | 100 | one per (`driver_id`, `trip_id`) |
# MAGIC
# MAGIC **Next:** **Module 8 — Aggregations and Window Functions** reads these tables
# MAGIC directly with `spark.table()`.