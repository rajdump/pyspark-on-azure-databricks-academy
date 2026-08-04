# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC # 07 - Build Unified Curated Tables
# MAGIC
# MAGIC Notebooks 01–06 developed skills in joining and set operations without storing data. This notebook serves as the capstone: it combines those skills to build and write the two managed tables required for Modules 8 and 9.
# MAGIC
# MAGIC | Section | Focus |
# MAGIC |---|---|
# MAGIC | Setup | Grain contracts for every input; `trip_id` type check |
# MAGIC | 1 | Stepwise left joins — time, then payment |
# MAGIC | 2 | Zone lookup + `F.broadcast` |
# MAGIC | 3 | Validate before write (write gate) |
# MAGIC | 4 | Write `trip_enriched` |
# MAGIC | Practice | Build, validate, and write `trip_driver_assignment` |
# MAGIC
# MAGIC **Reads:**
# MAGIC
# MAGIC | Input | Source | Format |
# MAGIC |---|---|---|
# MAGIC | `trip` | curated (Module 6 **03**) | Parquet |
# MAGIC | `payment` | curated (Module 6 **03**) | Parquet |
# MAGIC | `drivers_flat` | curated (Module 6 **02**) | Parquet |
# MAGIC | `trip_time` | landing | Parquet |
# MAGIC | `zone_lookup` | landing | JSON |
# MAGIC
# MAGIC **Writes:**
# MAGIC
# MAGIC | Output table | Grain |
# MAGIC |---|---|
# MAGIC | `rideshare_dev.processed.trip_enriched` | one row per `trip_id` (106) |
# MAGIC | `rideshare_dev.processed.trip_driver_assignment` | one row per (`driver_id`, `trip_id`) (100) |
# MAGIC
# MAGIC **Prerequisites:** Module 7 **`01`–`06`**; complete Module 6, with curated
# MAGIC inputs specifically from Module 6 **`02`** (`drivers_flat`) and **`03`**
# MAGIC (`trip` / `payment`).

# COMMAND ----------

# DBTITLE 1,Setup — grain contracts
# MAGIC %md
# MAGIC ## Setup — grain contracts
# MAGIC
# MAGIC | Table | Format | Grain (one row =) | Key | Rows |
# MAGIC |---|---|---|---|---|
# MAGIC | `curated/trip` | Parquet | one trip | `trip_id` | 106 |
# MAGIC | `curated/payment` | Parquet | one trip's payment | `trip_id` | 105 |
# MAGIC | `curated/drivers_flat` | Parquet | one driver–trip assignment | (`driver_id`, `trip_id`) | 100 |
# MAGIC | Landing `trip_time` | Parquet | one trip's date/hour | `trip_id` | 100 |
# MAGIC | Landing `zone_lookup` | JSON Lines | one taxi zone | `location_id` | 22 |
# MAGIC
# MAGIC **Target grains for this notebook's two writes:**
# MAGIC - `trip_enriched` — one row per `curated/trip.trip_id` → **106**
# MAGIC - `trip_driver_assignment` — one row per (`driver_id`, `trip_id`) from
# MAGIC   `drivers_flat` → **100**
# MAGIC
# MAGIC **Expected NULLs after left joins (intentional — predict before Section 1):**
# MAGIC
# MAGIC | Join | Left rows | Right rows | Unmatched rows | Columns that become NULL |
# MAGIC |---|---:|---:|---:|---|
# MAGIC | `trip` ⟕ `trip_time` | 106 | 100 | 6 | `trip_date`, `hour_of_day` |
# MAGIC | result ⟕ `payment` | 106 | 105 | 1 | all payment columns |
# MAGIC
# MAGIC Trips **101–106** have no time record; trip **106** also has no payment
# MAGIC record. Both gaps trace back to Module 6's cleaning outputs — the numbers
# MAGIC are already visible in the grain table above.
# MAGIC
# MAGIC Same habit as Notebooks 01–06: **predict → run → verify** — one join at a
# MAGIC time.

# COMMAND ----------

# DBTITLE 1,Setup — load inputs
from pyspark.sql import functions as F

landing_root = "/Volumes/rideshare_dev/landing/source_files"
curated_root = "/Volumes/rideshare_dev/processed/output_files/curated"

curated_trip_path = f"{curated_root}/trip"
curated_payment_path = f"{curated_root}/payment"
curated_drivers_path = f"{curated_root}/drivers_flat"

trip_time_path = f"{landing_root}/trip_time/trip_time.parquet"
zone_json_path = f"{landing_root}/zone_lookup/zone_lookup.json"

# Same zone_lookup DDL as Notebook 03 — reused verbatim, not reinferred.
zone_lookup_schema_ddl = """
location_id int,
borough_name string,
zone_name string,
service_zone string
"""

curated_trip = spark.read.format("parquet").load(curated_trip_path)  # noqa: F821

curated_payment = spark.read.format("parquet").load(curated_payment_path)  # noqa: F821

drivers_flat = spark.read.format("parquet").load(curated_drivers_path)  # noqa: F821

trip_time = spark.read.format("parquet").load(trip_time_path)  # noqa: F821

zone_lookup = (
    spark.read.format("json")  # noqa: F821
    .schema(zone_lookup_schema_ddl)
    .load(zone_json_path)
)

print("curated_trip rows:    ", curated_trip.count())
print("curated_payment rows: ", curated_payment.count())
print("drivers_flat rows:    ", drivers_flat.count())
print("trip_time rows:       ", trip_time.count())
print("zone_lookup rows:     ", zone_lookup.count())

# Type check — confirm trip_id aligns before the practice join relies on it.
print("\ndrivers_flat.trip_id type:", drivers_flat.schema["trip_id"].dataType)
print("curated_trip.trip_id type:", curated_trip.schema["trip_id"].dataType)

# COMMAND ----------

# DBTITLE 1,1. Stepwise left joins
# MAGIC %md
# MAGIC ## 1. Stepwise left joins — time, then payment
# MAGIC
# MAGIC Two left joins from curated trip, one at a time, so each join's row-count
# MAGIC and NULL effect is visible on its own instead of hidden inside one big
# MAGIC chain.
# MAGIC
# MAGIC Predict before running:
# MAGIC
# MAGIC | Step | Driving side | Join | Predicted rows | Predicted NULLs |
# MAGIC |---|---|---|---:|---:|
# MAGIC | 1a | `curated_trip` (106) | `trip_time` (100) | 106 | 6 NULL `trip_date` |
# MAGIC | 1b | result of 1a (106) | `curated_payment` (105) | 106 | 1 NULL `payment_method` |
# MAGIC
# MAGIC Left preserves the curated trip grain (106 rows) at every step — `trip_id`
# MAGIC is the driving key throughout, so no left join here can add or remove trip
# MAGIC rows, only add NULLs where the right side has no match.

# COMMAND ----------

# DBTITLE 1,1a. trip ⟕ trip_time
# Boolean join — trip_id names match, but the explicit Boolean form here
# keeps both stepwise joins in this section consistent with each other.
t = curated_trip.alias("t")
tt = trip_time.alias("tt")

# Boolean join on a shared name produces two columns, both displayed as
# "trip_id" (Notebook 03's ambiguous-column trap). Passing a Column object
# to drop() — not a string — resolves it by lineage, not by name, so only
# tt's copy is removed; t's trip_id survives, now unqualified.
trip_with_time = t.join(
    tt,
    F.col("t.trip_id") == F.col("tt.trip_id"),
    "left",
).drop(F.col("tt.trip_id"))

print("trip_with_time rows:", trip_with_time.count())
print(
    "NULL trip_date rows:",
    trip_with_time.filter(F.col("trip_date").isNull()).count(),
)

print("\nTrips with no time record:")
trip_with_time.filter(F.col("trip_date").isNull()).select("trip_id").orderBy("trip_id").show()

# COMMAND ----------

# DBTITLE 1,1b. + payment
# Boolean join to payment, same form as 1a — same Column-based drop() to
# remove only p's duplicate trip_id (see the comment in cell 1a).
twt = trip_with_time.alias("twt")
p = curated_payment.alias("p")

trip_with_time_pay = twt.join(
    p,
    F.col("twt.trip_id") == F.col("p.trip_id"),
    "left",
).drop(F.col("p.trip_id"))

print("trip_with_time_pay rows:", trip_with_time_pay.count())
print(
    "NULL payment_method rows:",
    trip_with_time_pay.filter(F.col("payment_method").isNull()).count(),
)

print("\nTrip with no payment record:")
trip_with_time_pay.filter(F.col("payment_method").isNull()).select(
    "trip_id", "service_type", "trip_date"
).show()

# COMMAND ----------

# DBTITLE 1,2. Zone lookup + broadcast
# MAGIC %md
# MAGIC ## 2. Zone lookup + broadcast
# MAGIC
# MAGIC Same repeated-lookup pattern as Notebook **03**: alias `zone_lookup` twice
# MAGIC — once for pickup, once for dropoff — and use `F.broadcast()` on both
# MAGIC sides, since `zone_lookup` is only 22 rows. No threshold reconfiguration
# MAGIC needed here; that demo already lives in **03**.
# MAGIC
# MAGIC **Predict zone coverage before joining:** `curated/trip`'s
# MAGIC `pickup_location_id` and `dropoff_location_id` only ever use `location_id`
# MAGIC **1–20** (`docs/data/dataset-overview.md`); `zone_lookup` covers **1–22**.
# MAGIC Location IDs 21–22 (`Newark Airport`, `Hoboken Terminal`) are simply never
# MAGIC referenced by any trip. Predict: **zero** NULL `pickup_borough` /
# MAGIC `dropoff_borough` after this lookup — every trip's zones will resolve.
# MAGIC (Validated in Section 3.)
# MAGIC
# MAGIC `service_zone` is deliberately excluded from the final `select` below — it
# MAGIC isn't needed downstream in this notebook.

# COMMAND ----------

# DBTITLE 1,2. Build trip_enriched
t = trip_with_time_pay.alias("t")
pz = F.broadcast(zone_lookup.alias("pz"))
dz = F.broadcast(zone_lookup.alias("dz"))

trip_with_zones = t.join(
    pz,
    F.col("t.pickup_location_id") == F.col("pz.location_id"),
    "left",
).join(
    dz,
    F.col("t.dropoff_location_id") == F.col("dz.location_id"),
    "left",
)

trip_enriched = trip_with_zones.select(
    F.col("t.trip_id"),
    F.col("t.service_type"),
    F.col("t.pickup_location_id"),
    F.col("t.dropoff_location_id"),
    F.col("t.trip_distance_miles"),
    F.col("t.ride_duration_mins"),
    F.col("t.trip_date"),
    F.col("t.hour_of_day"),
    # Core payment facts only — full breakdown (surge_amount, tax_amount,
    # discount_amount) and Module 6 derived metrics (charge_before_tip,
    # tip_percent_of_base) remain in curated/payment/, not here.
    F.col("t.payment_method"),
    F.col("t.base_fare_amount"),
    F.col("t.tip_amount"),
    F.col("t.driver_payout_amount"),
    F.col("pz.borough_name").alias("pickup_borough"),
    F.col("pz.zone_name").alias("pickup_zone"),
    F.col("dz.borough_name").alias("dropoff_borough"),
    F.col("dz.zone_name").alias("dropoff_zone"),
)

print("trip_enriched rows:", trip_enriched.count())
trip_enriched.printSchema()

# COMMAND ----------

# DBTITLE 1,3. Validate before write
# MAGIC %md
# MAGIC ## 3. Validate before write
# MAGIC
# MAGIC Two different checks, for two different purposes:
# MAGIC
# MAGIC **Write gate (re-confirming a known gap):** run `left_anti` between the
# MAGIC **original curated `trip` and `payment` frames** (not `trip_enriched`) on
# MAGIC `trip_id`. This isn't a new discovery — Notebook **04** already
# MAGIC established `curated/trip` has one payment gap (trip 106). Re-running it
# MAGIC here, right before the write, confirms nothing changed since Setup.
# MAGIC
# MAGIC A key-only `subtract()` (Notebook **06**) would give the same answer —
# MAGIC `curated_trip.select("trip_id").subtract(curated_payment.select("trip_id"))`
# MAGIC — shown here only as a one-line equivalent, not run twice as a peer check.
# MAGIC
# MAGIC **Output validation (what actually confirms `trip_enriched` is correct):**
# MAGIC the two NULL asserts predicted in Sections 1–2:
# MAGIC - NULL `trip_date` count on `trip_enriched` must equal **6** (the
# MAGIC   `trip_time` gap)
# MAGIC - NULL `pickup_borough` / `dropoff_borough` count on `trip_enriched` must
# MAGIC   equal **0** (Section 2's zone-coverage prediction)
# MAGIC
# MAGIC Write only after every check passes.

# COMMAND ----------

# DBTITLE 1,3. Validation checks
# Write gate — re-confirm the known payment gap on the ORIGINAL curated
# frames. Equivalent one-liner (not run):
#   curated_trip.select("trip_id").subtract(curated_payment.select("trip_id"))
payment_gap = curated_trip.join(curated_payment, "trip_id", "left_anti")
payment_gap_count = payment_gap.count()
payment_gap_ok = payment_gap_count == 1
gap_trip_id = payment_gap.collect()[0]["trip_id"] if payment_gap_count else "none"

time_null_count = trip_enriched.filter(F.col("trip_date").isNull()).count()
time_ok = time_null_count == 6

zone_null_count = trip_enriched.filter(
    F.col("pickup_borough").isNull() | F.col("dropoff_borough").isNull()
).count()
zone_ok = zone_null_count == 0

print(
    f"Write gate — payment gap trip_id: {gap_trip_id} \u2192 {'PASS' if payment_gap_ok else 'FAIL'}"
)
print(
    f"NULL check — trip_date nulls = {time_null_count} (expect 6) "
    f"\u2192 {'PASS' if time_ok else 'FAIL'}"
)
print(
    f"NULL check — zone borough nulls = {zone_null_count} (expect 0) "
    f"\u2192 {'PASS' if zone_ok else 'FAIL'}"
)

all_checks_passed = payment_gap_ok and time_ok and zone_ok
if all_checks_passed:
    print("\n\u2713 All checks passed \u2014 safe to write.")
else:
    print("\n\u2717 Checks failed \u2014 do not write.")

# COMMAND ----------

# DBTITLE 1,4. Write trip_enriched
# MAGIC %md
# MAGIC ## 4. Write `trip_enriched`
# MAGIC
# MAGIC Unity Catalog managed table `rideshare_dev.processed.trip_enriched`.
# MAGIC `DROP TABLE IF EXISTS` first, then `saveAsTable(..., mode="overwrite")` —
# MAGIC Delta by default (Module 10 covers Delta internals: ACID, `MERGE`, time
# MAGIC travel). This is a managed table, not a Volume Parquet write like
# MAGIC Modules 5–6.

# COMMAND ----------

# DBTITLE 1,4. Write + read-back
assert all_checks_passed, "Fix validation failures before writing trip_enriched."

spark.sql("DROP TABLE IF EXISTS rideshare_dev.processed.trip_enriched")  # noqa: F821
trip_enriched.write.mode("overwrite").saveAsTable("rideshare_dev.processed.trip_enriched")

trip_enriched_readback = spark.table(  # noqa: F821
    "rideshare_dev.processed.trip_enriched"
)
print("trip_enriched read-back rows:", trip_enriched_readback.count())

# COMMAND ----------

# DBTITLE 1,Practice — trip_driver_assignment
# MAGIC %md
# MAGIC ## Practice — `trip_driver_assignment`
# MAGIC
# MAGIC Grain: one row per (`driver_id`, `trip_id`) from `drivers_flat` — **100**
# MAGIC rows (12 drivers, 100 assignments, trips 1–100 only).
# MAGIC
# MAGIC Left join `drivers_flat` to **`curated/trip`** — not `trip_enriched`.
# MAGIC Joining `trip_enriched` would drag `trip_date`, `hour_of_day`,
# MAGIC `payment_method`, and the zone columns — and their NULLs — into a table
# MAGIC where those columns have no business meaning; `trip_driver_assignment` is
# MAGIC a different grain, and those columns belong to the trip-time / payment /
# MAGIC zone story, not the driver-assignment story.
# MAGIC
# MAGIC Predict: assignment rows = **100** (every `drivers_flat` row has a
# MAGIC matching `curated/trip` row — Setup's type check confirmed the join key
# MAGIC types align).
# MAGIC
# MAGIC Two distinct checks below, run separately:
# MAGIC 1. **Validate your output** — count equals 100;
# MAGIC    `drivers_flat.left_anti(curated_trip)` on `trip_id` is empty (no
# MAGIC    orphan `trip_id` in your result).
# MAGIC 2. **Reveal** — a different question:
# MAGIC    `curated_trip.left_anti(drivers_flat)` on `trip_id` → which trips have
# MAGIC    **no** driver assignment? Predict **6** rows (trips 101–106 —
# MAGIC    `drivers_flat` only covers 1–100).

# COMMAND ----------

# DBTITLE 1,Practice TODO — build
# TODO (practice): left join drivers_flat to curated_trip on trip_id, using
# Boolean form with aliases (same pattern as Section 1's stepwise joins).
#
# Steps:
#   1. Alias drivers_flat as "d" and curated_trip as "t"
#   2. Join: d.join(t, <Boolean condition on trip_id>, "left")
#   3. Select: driver_id, driver_name, license_number, vehicle_make,
#      vehicle_model, vehicle_year, vehicle_body_type, trip_id (from d),
#      plus service_type, trip_distance_miles, pickup_location_id,
#      dropoff_location_id (from t)
#   4. Name the result trip_driver_assignment
#   5. Print the row count — does it match your prediction (100)?

# COMMAND ----------

# DBTITLE 1,Practice TODO — validate
# TODO (practice), both required — validate a different thing each:
#
# (a) Validate YOUR OUTPUT — no orphan trip_id in trip_driver_assignment:
#     - Print trip_driver_assignment.count() — expect 100
#     - drivers_flat.join(curated_trip, "trip_id", "left_anti").count()
#       — expect 0 (every drivers_flat trip_id exists in curated_trip)
#
# (b) Reveal — which trips have NO driver assignment at all:
#     - curated_trip.join(drivers_flat, "trip_id", "left_anti")
#       — expect 6 rows
#     - Show the trip_ids — do they match trips 101-106 (the same trips
#       that had no trip_time record in Section 1)?

# COMMAND ----------

# DBTITLE 1,Practice TODO — write
# TODO (practice): write trip_driver_assignment as a managed table, same
# pattern as Section 4.
#
# Steps:
#   1. DROP TABLE IF EXISTS rideshare_dev.processed.trip_driver_assignment
#   2. trip_driver_assignment.write.mode("overwrite").saveAsTable(
#        "rideshare_dev.processed.trip_driver_assignment")
#   3. Read it back with spark.table(...) and print the row count
#      — expect 100

# COMMAND ----------

# DBTITLE 1,AQE note
# MAGIC %md
# MAGIC ## AQE note
# MAGIC
# MAGIC Adaptive Query Execution (AQE) can change a join's physical strategy at
# MAGIC runtime based on actual data sizes, not just the plan Spark chose upfront.
# MAGIC The explicit `F.broadcast()` hint used in Section 2 still applies — it's a
# MAGIC direct instruction, not something AQE overrides. Deeper join-plan tuning
# MAGIC (AQE thresholds, skew handling) is Module 16.

# COMMAND ----------

# DBTITLE 1,Summary
# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - **Grain first:** every table's row count and key were confirmed before
# MAGIC   any join ran.
# MAGIC - **Stepwise left joins:** `curated/trip` → `trip_time` → `curated/payment`,
# MAGIC   one join at a time, each with its own NULL-count check (Section 1).
# MAGIC - **Reused, not re-taught:** the repeated zone lookup + `F.broadcast()`
# MAGIC   pattern from Notebook **03** (Section 2).
# MAGIC - **Validated before writing:** a write-gate `left_anti` re-confirming a
# MAGIC   known gap, plus NULL asserts that actually validate `trip_enriched`'s
# MAGIC   shape (Section 3).
# MAGIC - **Wrote two Unity Catalog managed tables** — `trip_enriched` (106 rows)
# MAGIC   and, in the practice, `trip_driver_assignment` (100 rows) — for
# MAGIC   Modules 8–9 to build on.
# MAGIC
# MAGIC **Next:** Module **8**.