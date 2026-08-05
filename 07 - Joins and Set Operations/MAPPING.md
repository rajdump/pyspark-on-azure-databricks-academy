# Mapping — Module 07 Notebook 07: Build Unified Curated Tables

**Status:** Draft — awaiting author approval  
**Derived from:** BRD (approved, 17 + 13 columns)

---

## How to read this document

- **DataFrame alias** — the alias assigned to the DataFrame in the join chain at that step.
- **Source expression** — the exact `F.col(...)` reference or `.alias(...)` call to use in `select()`.
- **Transform** — any rename, cast, or computation applied. "Pass-through" means the column is taken as-is.
- **Nullable** — whether NULLs can appear in the output and why.

---

## Table 1 — `rideshare_dev.processed.trip_enriched`

### Join chain (in order)

| Step | Operation | Left alias | Right alias | Join type | Condition | After-join rows |
|---|---|---|---|---|---|---:|
| Load | Read `curated_trip` | `t` | — | — | — | 106 |
| Load | Read `trip_time` | — | `tt` | — | — | 100 |
| Load | Read `curated_payment` | — | `p` | — | — | 105 |
| Load | Read `zone_lookup` | — | `pz` (pickup), `dz` (dropoff) | — | — | 22 |
| 1 | `t` LEFT JOIN `tt` | `t` | `tt` | left | `t.trip_id == tt.trip_id` | 106 |
| — | Drop duplicate key | — | — | — | `.drop(F.col("tt.trip_id"))` | 106 |
| 2 | result LEFT JOIN `p` | `twt` | `p` | left | `twt.trip_id == p.trip_id` | 106 |
| — | Drop duplicate key | — | — | — | `.drop(F.col("p.trip_id"))` | 106 |
| 3 | result LEFT JOIN `pz` | `t` | `F.broadcast(pz)` | left | `t.pickup_location_id == pz.location_id` | 106 |
| 4 | result LEFT JOIN `dz` | — | `F.broadcast(dz)` | left | `t.dropoff_location_id == dz.location_id` | 106 |

**Alias note after step 2:** the chained result is re-aliased as `"t"` before steps 3–4
so that `F.col("t.pickup_location_id")` and `F.col("t.dropoff_location_id")` resolve
unambiguously. At that point `"t"` refers to the full trip + time + payment result.

### Column lineage

| # | Target column | Source dataset | DataFrame alias | Source expression | Transform | Output type | Nullable | NULL condition |
|---|---|---|---|---|---|---|---|---|
| 1 | `trip_id` | `curated_trip` | `t` | `F.col("t.trip_id")` | Pass-through | bigint | No | — |
| 2 | `service_type` | `curated_trip` | `t` | `F.col("t.service_type")` | Pass-through | string | No | — |
| 3 | `pickup_location_id` | `curated_trip` | `t` | `F.col("t.pickup_location_id")` | Pass-through | int | Yes | Invalid source value (already NULL in curated_trip) |
| 4 | `dropoff_location_id` | `curated_trip` | `t` | `F.col("t.dropoff_location_id")` | Pass-through | int | Yes | Invalid source value |
| 5 | `trip_distance_miles` | `curated_trip` | `t` | `F.col("t.trip_distance_miles")` | Pass-through | decimal(8,2) | Yes | Invalid source value |
| 6 | `ride_duration_mins` | `curated_trip` | `t` | `F.col("t.ride_duration_mins")` | Pass-through | int | Yes | Invalid source value |
| 7 | `request_to_pickup_mins` | `curated_trip` | `t` | `F.col("t.request_to_pickup_mins")` | Pass-through | int | Yes | Invalid source value |
| 8 | `trip_date` | `trip_time` | `tt` | `F.col("t.trip_date")` ¹ | Pass-through | date | Yes | trips 101–106 — no `trip_time` record |
| 9 | `hour_of_day` | `trip_time` | `tt` | `F.col("t.hour_of_day")` ¹ | Pass-through | int | Yes | trips 101–106 — no `trip_time` record |
| 10 | `payment_method` | `curated_payment` | `p` | `F.col("t.payment_method")` ¹ | Pass-through | string | Yes | trip 106 — no payment record |
| 11 | `base_fare_amount` | `curated_payment` | `p` | `F.col("t.base_fare_amount")` ¹ | Pass-through | decimal(10,2) | Yes | trip 106 |
| 12 | `tip_amount` | `curated_payment` | `p` | `F.col("t.tip_amount")` ¹ | Pass-through | decimal(10,2) | Yes | trip 106 |
| 13 | `driver_payout_amount` | `curated_payment` | `p` | `F.col("t.driver_payout_amount")` ¹ | Pass-through | decimal(10,2) | Yes | trip 106 |
| 14 | `pickup_borough` | `zone_lookup` | `pz` | `F.col("pz.borough_name").alias("pickup_borough")` | Rename | string | Yes | Expected 0 NULLs |
| 15 | `pickup_zone` | `zone_lookup` | `pz` | `F.col("pz.zone_name").alias("pickup_zone")` | Rename | string | Yes | Expected 0 NULLs |
| 16 | `dropoff_borough` | `zone_lookup` | `dz` | `F.col("dz.borough_name").alias("dropoff_borough")` | Rename | string | Yes | Expected 0 NULLs |
| 17 | `dropoff_zone` | `zone_lookup` | `dz` | `F.col("dz.zone_name").alias("dropoff_zone")` | Rename | string | Yes | Expected 0 NULLs |

¹ After `.drop(F.col("tt.trip_id"))` and `.drop(F.col("p.trip_id"))` collapse the join
chain into a single unambiguous `"t"` alias, all columns from `trip_time` and
`curated_payment` are accessible as `F.col("t.<column>")` without their original alias.

### Validation checks (run before write)

| # | Expression | Expected | Fail action |
|---|---|---|---|
| 1 | `trip_enriched.count()` | 106 | Do not write — row count changed |
| 2 | `trip_enriched.filter(F.col("trip_date").isNull()).count()` | 6 | Do not write — trip_time gap changed |
| 3 | `trip_enriched.filter(F.col("payment_method").isNull()).count()` | 1 | Do not write — payment gap changed |
| 4 | `trip_enriched.filter(F.col("pickup_borough").isNull()).count()` | 0 | Do not write — zone lookup failed |
| 5 | `trip_enriched.filter(F.col("dropoff_borough").isNull()).count()` | 0 | Do not write — zone lookup failed |
| 6 | `curated_trip.join(curated_payment, "trip_id", "left_anti").count()` | 1 | Do not write — source data changed |

### Write

```python
spark.sql("DROP TABLE IF EXISTS rideshare_dev.processed.trip_enriched")
trip_enriched.write.mode("overwrite").saveAsTable("rideshare_dev.processed.trip_enriched")
```

---

## Table 2 — `rideshare_dev.processed.trip_driver_assignment`

### Join (practice section)

| Step | Operation | Left alias | Right alias | Join type | Condition | After-join rows |
|---|---|---|---|---|---|---:|
| Load | Read `drivers_flat` | `d` | — | — | — | 100 |
| Load | Read `curated_trip` | — | `t` | — | — | 106 |
| 1 | `d` LEFT JOIN `t` | `d` | `t` | left | `d.trip_id == t.trip_id` | 100 |
| — | Drop duplicate key | — | — | — | `.drop(F.col("t.trip_id"))` | 100 |

**Driving table is `drivers_flat`, not `curated_trip`.** Driving from `curated_trip`
(106 rows) would produce 6 rows with NULL driver columns for trips 101–106.
The grain of this table is the assignment — unassigned trips are a reveal (anti-join),
not a row in this output.

### Column lineage

| # | Target column | Source dataset | DataFrame alias | Source expression | Transform | Output type | Nullable | NULL condition |
|---|---|---|---|---|---|---|---|---|
| 1 | `driver_id` | `drivers_flat` | `d` | `F.col("d.driver_id")` | Pass-through | string | No | — |
| 2 | `driver_name` | `drivers_flat` | `d` | `F.col("d.driver_name")` | Pass-through | string | Yes | Source may be NULL |
| 3 | `license_number` | `drivers_flat` | `d` | `F.col("d.license_number")` | Pass-through | string | Yes | Source may be NULL |
| 4 | `vehicle_make` | `drivers_flat` | `d` | `F.col("d.vehicle_make")` | Pass-through | string | Yes | Source may be NULL |
| 5 | `vehicle_model` | `drivers_flat` | `d` | `F.col("d.vehicle_model")` | Pass-through | string | Yes | Source may be NULL |
| 6 | `vehicle_year` | `drivers_flat` | `d` | `F.col("d.vehicle_year")` | Pass-through | long | Yes | Source may be NULL |
| 7 | `vehicle_body_type` | `drivers_flat` | `d` | `F.col("d.vehicle_body_type")` | Pass-through | string | Yes | Source may be NULL |
| 8 | `trip_id` | `drivers_flat` | `d` | `F.col("d.trip_id")` | Pass-through | bigint | No | — |
| 9 | `service_type` | `curated_trip` | `t` | `F.col("t.service_type")` | Pass-through | string | Yes | Expected 0 NULLs — all drivers_flat trip_ids (1–100) exist in curated_trip |
| 10 | `trip_distance_miles` | `curated_trip` | `t` | `F.col("t.trip_distance_miles")` | Pass-through | decimal(8,2) | Yes | Expected 0 NULLs |
| 11 | `ride_duration_mins` | `curated_trip` | `t` | `F.col("t.ride_duration_mins")` | Pass-through | int | Yes | Expected 0 NULLs |
| 12 | `pickup_location_id` | `curated_trip` | `t` | `F.col("t.pickup_location_id")` | Pass-through | int | Yes | Expected 0 NULLs |
| 13 | `dropoff_location_id` | `curated_trip` | `t` | `F.col("t.dropoff_location_id")` | Pass-through | int | Yes | Expected 0 NULLs |

### Validation checks (run before write)

| # | Expression | Expected | Fail action |
|---|---|---|---|
| 1 | `trip_driver_assignment.count()` | 100 | Do not write — row count changed |
| 2 | `drivers_flat.join(curated_trip, "trip_id", "left_anti").count()` | 0 | Do not write — orphan trip_id in drivers_flat |

### Anti-join reveal (run after validation — separate from the write gate)

```python
# Which trips have no driver assignment at all?
# Expect 6 rows: trips 101–106 (same gap as trip_time).
curated_trip.join(drivers_flat, "trip_id", "left_anti") \
    .select("trip_id") \
    .orderBy("trip_id") \
    .show()
```

This is a teaching reveal — it shows that the Module 6 extension trips (101–106) have
no time record, no driver assignment, and (for trip 106) no payment record. The pattern
is consistent and deliberate.

### Write

```python
spark.sql("DROP TABLE IF EXISTS rideshare_dev.processed.trip_driver_assignment")
trip_driver_assignment.write.mode("overwrite").saveAsTable("rideshare_dev.processed.trip_driver_assignment")
```

---

## Columns excluded from both output tables

All excluded columns remain available in their source curated paths for any notebook
that needs them.

| Column | Source | Available at |
|---|---|---|
| `ride_duration_band` | `curated_trip` | `curated/trip/` |
| `service_label` | `curated_trip` | `curated/trip/` |
| `trip_distance_km` | `curated_trip` | `curated/trip/` |
| `request_to_driver_arrival_mins` | `curated_trip` | `curated/trip/` |
| `diff_ride_duration_wait_mins` | `curated_trip` | `curated/trip/` |
| `driver_arrival_to_pickup_mins` | `curated_trip` | `curated/trip/` |
| `surge_amount` | `curated_payment` | `curated/payment/` |
| `tax_amount` | `curated_payment` | `curated/payment/` |
| `discount_amount` | `curated_payment` | `curated/payment/` |
| `charge_before_tip` | `curated_payment` | `curated/payment/` |
| `tip_percent_of_base` | `curated_payment` | `curated/payment/` |
| `service_zone` | `zone_lookup` | Landing `zone_lookup` |
