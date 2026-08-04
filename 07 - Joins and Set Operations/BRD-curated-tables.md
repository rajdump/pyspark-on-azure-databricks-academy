# BRD — Unified Curated Tables

## 1. Business objective

Modules 8 (Aggregations and Windows) and 9 (SQL and CTEs) require two
analytics-ready managed tables that combine trip, time, payment, zone, and
driver data into query-friendly grains. Today, those attributes live in
separate curated Parquet files and landing sources with no single
query-ready view.

This document defines the two deliverables, their target contracts, source
mappings, and acceptance criteria.

---

## 2. Deliverables

| # | Table | Business purpose |
|---:|---|---|
| 1 | `rideshare_dev.processed.trip_enriched` | One analytics-ready record per curated trip — combines trip attributes, time, core payment facts, and zone names |
| 2 | `rideshare_dev.processed.trip_driver_assignment` | Connects every driver assignment to the basic details of the assigned trip |

---

## 3. Target contracts

### 3a. `trip_enriched`

| Attribute | Requirement |
|---|---|
| Grain | One row per `trip_id` |
| Driving source | `curated/trip` |
| Row rule | Every driving row preserved — target count = driving count |
| Expected rows (this dataset) | 106 |
| Storage | Unity Catalog managed Delta table |
| Write mode | DROP + overwrite (idempotent rerun) |

### 3b. `trip_driver_assignment`

| Attribute | Requirement |
|---|---|
| Grain | One row per (`driver_id`, `trip_id`) |
| Driving source | `curated/drivers_flat` |
| Row rule | Every driving row preserved — target count = driving count |
| Expected rows (this dataset) | 100 |
| Storage | Unity Catalog managed Delta table |
| Write mode | DROP + overwrite (idempotent rerun) |

---

## 4. Source inventory

| Source | Format | Grain | Key | Rows |
|---|---|---|---|---:|
| `curated/trip` | Parquet | one trip | `trip_id` | 106 |
| `curated/payment` | Parquet | one trip's payment | `trip_id` | 105 |
| `curated/drivers_flat` | Parquet | one driver–trip assignment | (`driver_id`, `trip_id`) | 100 |
| Landing `trip_time` | Parquet | one trip's date/hour | `trip_id` | 100 |
| Landing `zone_lookup` | JSON | one taxi zone | `location_id` | 22 |

---

## 5. Join plan — `trip_enriched`

All joins are **left joins** — every curated trip must remain in the output
even when a right-side record is missing.

| Source | Join condition | Type | Expected relationship |
|---|---|---|---|
| `trip_time` | `trip_id = trip_id` | Left | One-to-zero-or-one |
| `curated_payment` | `trip_id = trip_id` | Left | One-to-zero-or-one |
| `zone_lookup` (pickup) | `pickup_location_id = location_id` | Left | Many-to-one |
| `zone_lookup` (dropoff) | `dropoff_location_id = location_id` | Left | Many-to-one |

### Join plan — `trip_driver_assignment`

| Source | Join condition | Type | Expected relationship |
|---|---|---|---|
| `curated_trip` | `trip_id = trip_id` | Left | Many-to-one |

---

## 6. Source-to-target column mapping

### 6a. `trip_enriched`

**Direct-copy columns** (no transformation):

| # | Target column | Source |
|---:|---|---|
| 1 | `trip_id` | `curated/trip` |
| 2 | `service_type` | `curated/trip` |
| 3 | `pickup_location_id` | `curated/trip` |
| 4 | `dropoff_location_id` | `curated/trip` |
| 5 | `trip_distance_miles` | `curated/trip` |
| 6 | `ride_duration_mins` | `curated/trip` |

**Columns with mapping rules:**

| # | Target column | Source | Rule | Nullable |
|---:|---|---|---|---|
| 7 | `trip_date` | `trip_time` | Direct after join on `trip_id` | Yes — no time record for trips 101–106 |
| 8 | `hour_of_day` | `trip_time` | Direct after join on `trip_id` | Yes — no time record for trips 101–106 |
| 9 | `payment_method` | `curated/payment` | Direct after join on `trip_id` | Yes — no payment for trip 106 |
| 10 | `base_fare_amount` | `curated/payment` | Direct after join on `trip_id` | Yes — no payment for trip 106 |
| 11 | `tip_amount` | `curated/payment` | Direct after join on `trip_id` | Yes — no payment for trip 106 |
| 12 | `driver_payout_amount` | `curated/payment` | Direct after join on `trip_id` | Yes — no payment for trip 106 |
| 13 | `pickup_borough` | `zone_lookup` | Rename `borough_name` after join on `pickup_location_id` | No — all locations 1–20 resolve |
| 14 | `pickup_zone` | `zone_lookup` | Rename `zone_name` after join on `pickup_location_id` | No — all locations 1–20 resolve |
| 15 | `dropoff_borough` | `zone_lookup` | Rename `borough_name` after join on `dropoff_location_id` | No — all locations 1–20 resolve |
| 16 | `dropoff_zone` | `zone_lookup` | Rename `zone_name` after join on `dropoff_location_id` | No — all locations 1–20 resolve |

**Excluded from target** (core payment facts only; full breakdown stays in
`curated/payment/`):

`surge_amount`, `tax_amount`, `discount_amount`, `charge_before_tip`,
`tip_percent_of_base`, `service_zone`.

---

### 6b. `trip_driver_assignment`

**Direct-copy columns** (from `drivers_flat`):

| # | Target column | Source |
|---:|---|---|
| 1 | `driver_id` | `drivers_flat` |
| 2 | `driver_name` | `drivers_flat` |
| 3 | `license_number` | `drivers_flat` |
| 4 | `vehicle_make` | `drivers_flat` |
| 5 | `vehicle_model` | `drivers_flat` |
| 6 | `vehicle_year` | `drivers_flat` |
| 7 | `vehicle_body_type` | `drivers_flat` |
| 8 | `trip_id` | `drivers_flat` |

**Columns from joined source:**

| # | Target column | Source | Rule | Nullable |
|---:|---|---|---|---|
| 9 | `service_type` | `curated/trip` | Direct after join on `trip_id` | No — all trips 1–100 exist |
| 10 | `trip_distance_miles` | `curated/trip` | Direct after join on `trip_id` | No — all trips 1–100 exist |
| 11 | `pickup_location_id` | `curated/trip` | Direct after join on `trip_id` | No — all trips 1–100 exist |
| 12 | `dropoff_location_id` | `curated/trip` | Direct after join on `trip_id` | No — all trips 1–100 exist |

**Excluded from target** (assignment-relevant only; time, payment, zone
columns do not belong to this grain):

`trip_date`, `hour_of_day`, `payment_method`, all payment amounts, zone
names.

---

## 7. Acceptance criteria

### 7a. `trip_enriched`

| Check | Expected result |
|---|---|
| Row count = driving count | 106 |
| Distinct `trip_id` = row count | 106 (grain preserved) |
| NULL `trip_date` count | 6 (trips 101–106) |
| NULL `payment_method` count | 1 (trip 106) |
| NULL `pickup_borough` count | 0 (all locations resolve) |
| NULL `dropoff_borough` count | 0 (all locations resolve) |
| `left_anti` curated_trip vs curated_payment | 1 row — trip 106 |

### 7b. `trip_driver_assignment`

| Check | Expected result |
|---|---|
| Row count = driving count | 100 |
| Distinct (`driver_id`, `trip_id`) = row count | 100 (grain preserved) |
| `left_anti` drivers_flat vs curated_trip on `trip_id` | 0 (no orphan assignments) |
| `left_anti` curated_trip vs drivers_flat on `trip_id` | 6 (trips 101–106 unassigned) |

---

## 8. Out of scope

* Delta internals (ACID, MERGE, time travel) — Module 10
* Aggregations and window functions — Module 8
* SQL / CTEs — Module 9
* AQE tuning beyond a brief awareness note — Module 16
* Updating Module 5 Notebook 99 Level 2 cleanup — tracked separately
* Volume Parquet writes — this notebook writes managed tables only
