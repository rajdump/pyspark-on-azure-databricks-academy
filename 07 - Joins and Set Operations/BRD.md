# BRD — Module 07 Notebook 07: Build Unified Curated Tables

**Status:** Approved  
**Derived from:** runtime cross-check results (verified Aug 2026). No prior notebook
code was used as input.

---

## Purpose

Produce two Unity Catalog managed Delta tables from curated and landing inputs.
These tables are the primary read surfaces for Module 8 (aggregations and window
functions) and Module 9 (Spark SQL).

| Output table | Grain | Primary consumer |
|---|---|---|
| `rideshare_dev.processed.trip_enriched` | One row per `trip_id` | Module 8 + Module 9 |
| `rideshare_dev.processed.trip_driver_assignment` | One row per (`driver_id`, `trip_id`) | Module 8 + Module 9 |

---

## Inputs

### 1. `curated_trip`

- **Path:** `/Volumes/rideshare_dev/processed/output_files/curated/trip/` (Parquet)
- **Grain:** one row per `trip_id`
- **Rows:** 106
- **Key:** `trip_id` — `bigint`, unique, no NULLs

| Column | Type | Notes |
|---|---|---|
| `trip_id` | bigint | PK |
| `service_type` | string | **Uppercase** — "STANDARD", "PREMIUM", "SHARED", "UNKNOWN" |
| `service_label` | string | "SERVICE-{service_type}" — Module 6 enrichment |
| `pickup_location_id` | int | Join key to `zone_lookup` |
| `dropoff_location_id` | int | Join key to `zone_lookup` |
| `trip_distance_miles` | decimal(8,2) | Positive only; NULL for invalid source values |
| `trip_distance_km` | double | `trip_distance_miles × 1.60934` — Module 6 enrichment |
| `request_to_pickup_mins` | int | Total wait: request → boarding; ≥ 0 |
| `driver_arrival_to_pickup_mins` | int | Boarding time after driver arrives; ≥ 0 |
| `request_to_driver_arrival_mins` | int | `request_to_pickup_mins − driver_arrival_to_pickup_mins` — Module 6 enrichment |
| `ride_duration_mins` | int | Actual ride time; ≥ 0 |
| `diff_ride_duration_wait_mins` | int | `ride_duration_mins − request_to_pickup_mins` — Module 6 enrichment |
| `ride_duration_band` | string | "short" / "medium" / "long" / NULL — Module 6 enrichment |

### 2. `curated_payment`

- **Path:** `/Volumes/rideshare_dev/processed/output_files/curated/payment/` (Parquet)
- **Grain:** one row per `trip_id`
- **Rows:** 105 (`trip_id` 106 absent — intentional gap from Module 6 cleaning)
- **Key:** `trip_id` — `bigint`, unique, no NULLs

| Column | Type | Notes |
|---|---|---|
| `trip_id` | bigint | FK → `curated_trip` |
| `payment_method` | string | Lowercase — "card", "cash", "wallet", "unknown" |
| `base_fare_amount` | decimal(10,2) | ≥ 0 |
| `surge_amount` | decimal(10,2) | ≥ 0 |
| `tax_amount` | decimal(10,2) | ≥ 0 |
| `tip_amount` | decimal(10,2) | ≥ 0 |
| `discount_amount` | decimal(10,2) | ≥ 0 |
| `driver_payout_amount` | decimal(10,2) | ≥ 0 |
| `charge_before_tip` | decimal(16,2) | `base + coalesce(surge,0) + coalesce(tax,0) − coalesce(discount,0)` — Module 6 enrichment |
| `tip_percent_of_base` | decimal(16,1) | `(tip / base) × 100`; NULL if base ≤ 0 or tip is NULL — Module 6 enrichment |

### 3. `drivers_flat`

- **Path:** `/Volumes/rideshare_dev/processed/output_files/curated/drivers_flat/` (Parquet)
- **Grain:** one row per (`driver_id`, `trip_id`)
- **Rows:** 100 (trips 1–100 only; trips 101–106 have no driver assignment)
- **Keys:** `driver_id` (string) + `trip_id` (bigint) — composite unique key; `trip_id` alone is also unique

| Column | Type | Notes |
|---|---|---|
| `driver_id` | string | e.g., "D001" |
| `driver_name` | string | |
| `license_number` | string | |
| `vehicle_make` | string | |
| `vehicle_model` | string | |
| `vehicle_year` | long | XML numeric element — inferred as `LongType` by Spark XML reader |
| `vehicle_body_type` | string | |
| `trip_id` | bigint | FK → `curated_trip` |

### 4. `trip_time` (landing)

- **Path:** `/Volumes/rideshare_dev/landing/source_files/trip_time/trip_time.parquet` (Parquet)
- **Grain:** one row per `trip_id`
- **Rows:** 100 (trips 1–100 only; trips 101–106 absent)
- **Key:** `trip_id` — `bigint`, unique, no NULLs

| Column | Type |
|---|---|
| `trip_id` | bigint |
| `trip_date` | date |
| `hour_of_day` | int |

### 5. `zone_lookup` (landing)

- **Path:** `/Volumes/rideshare_dev/landing/source_files/zone_lookup/zone_lookup.json` (JSON Lines)
- **Grain:** one row per `location_id`
- **Rows:** 22
- **Key:** `location_id` — `int` (explicit schema DDL applied on read; Spark would infer `LongType` without it)

| Column | Type |
|---|---|
| `location_id` | int |
| `borough_name` | string |
| `zone_name` | string |
| `service_zone` | string |

**Zone coverage note:** all trip `pickup_location_id` and `dropoff_location_id` values are
1–20. `zone_lookup` covers 1–22. Location IDs 21 and 22 are never referenced by any trip.
Zero unresolved zones — no NULLs expected after the lookup joins.

**Type compatibility:** `curated_trip.pickup_location_id` and `.dropoff_location_id` are
`int` (IntegerType). `zone_lookup.location_id` is `int` (IntegerType) when the explicit
schema DDL is applied. Both sides are exact-match IntegerType — no implicit widening occurs.

---

## Column selection rationale

### trip_enriched — 17 columns

The table is a denormalized analytical surface for trip-level aggregations and SQL joins.
Exclusion rule: **trip_enriched carries source columns and what the joins add — not what
Module 6 computed.** Module 6 enrichments (derived columns) stay in `curated/trip/`;
Module 8 will re-derive categorical groupings (e.g., duration bands) as an exercise.

**Included from `curated_trip` (7 columns):**

| Column | Reason |
|---|---|
| `trip_id` | Key — preserves grain |
| `service_type` | Grouping dimension — aggregations by service class |
| `pickup_location_id` | Join key — kept for direct zone ID lookups in Module 9 |
| `dropoff_location_id` | Join key — same |
| `trip_distance_miles` | Aggregation measure — avg/sum distance |
| `ride_duration_mins` | Aggregation measure — avg/sum duration |
| `request_to_pickup_mins` | Aggregation measure — avg wait time by zone or service type; source column, not a Module 6 enrichment |

**Excluded from `curated_trip` (6 columns):**

| Column | Reason for exclusion |
|---|---|
| `ride_duration_band` | Module 6 enrichment (derived from `ride_duration_mins`); Module 8 re-derives this with CASE/when as a teaching exercise |
| `service_label` | Module 6 enrichment; redundant display string, not an analytical dimension |
| `trip_distance_km` | Module 6 enrichment; redundant dual-unit metric |
| `request_to_driver_arrival_mins` | Module 6 enrichment; derivable in-query from source columns |
| `diff_ride_duration_wait_mins` | Module 6 enrichment; derivable in-query from source columns |
| `driver_arrival_to_pickup_mins` | Source column but a sub-component metric; not a direct aggregation target and not needed to derive any included column |

**Included from `trip_time` (2 columns):** `trip_date`, `hour_of_day` — time dimensions for date-based aggregations and time-of-day analysis.

**Included from `curated_payment` (4 columns):** `payment_method`, `base_fare_amount`, `tip_amount`, `driver_payout_amount` — core payment facts for fare aggregations. Full breakdown (surge, tax, discount, derived metrics) stays in `curated/payment/`.

**Included from `zone_lookup` via pickup alias (2 columns):** `pickup_borough`, `pickup_zone` — geographic grouping dimensions.

**Included from `zone_lookup` via dropoff alias (2 columns):** `dropoff_borough`, `dropoff_zone` — geographic grouping dimensions.

### trip_driver_assignment — 13 columns

The table is a driver-assignment view. Its grain is the assignment, not the trip.
Zone names are excluded — a driver assignment has no analytical relationship to borough
that isn't better expressed by joining `trip_enriched` in Module 9. `ride_duration_mins`
is included as the one metric that meaningfully characterises a driver's assignment.

**All 8 columns from `drivers_flat`:** `driver_id`, `driver_name`, `license_number`,
`vehicle_make`, `vehicle_model`, `vehicle_year`, `vehicle_body_type`, `trip_id`

**5 columns from `curated_trip`:** `service_type`, `trip_distance_miles`,
`ride_duration_mins`, `pickup_location_id`, `dropoff_location_id`

---

## Output contracts

### `rideshare_dev.processed.trip_enriched`

- **Format:** Delta managed table
- **Write mode:** `saveAsTable` overwrite (DROP TABLE IF EXISTS first)
- **Grain:** one row per `trip_id`
- **Row count:** 106

| # | Column | Source | Type | Nullable | NULL meaning |
|---|---|---|---|---|---|
| 1 | `trip_id` | `curated_trip` | bigint | No | — |
| 2 | `service_type` | `curated_trip` | string | No | — |
| 3 | `pickup_location_id` | `curated_trip` | int | Yes | invalid source value |
| 4 | `dropoff_location_id` | `curated_trip` | int | Yes | invalid source value |
| 5 | `trip_distance_miles` | `curated_trip` | decimal(8,2) | Yes | invalid source value |
| 6 | `ride_duration_mins` | `curated_trip` | int | Yes | invalid source value |
| 7 | `request_to_pickup_mins` | `curated_trip` | int | Yes | invalid source value |
| 8 | `trip_date` | `trip_time` | date | Yes | **trips 101–106** — no time record |
| 9 | `hour_of_day` | `trip_time` | int | Yes | **trips 101–106** — no time record |
| 10 | `payment_method` | `curated_payment` | string | Yes | **trip 106** — no payment record |
| 11 | `base_fare_amount` | `curated_payment` | decimal(10,2) | Yes | **trip 106** |
| 12 | `tip_amount` | `curated_payment` | decimal(10,2) | Yes | **trip 106** |
| 13 | `driver_payout_amount` | `curated_payment` | decimal(10,2) | Yes | **trip 106** |
| 14 | `pickup_borough` | `zone_lookup` (pickup) | string | Yes | expected 0 NULLs |
| 15 | `pickup_zone` | `zone_lookup` (pickup) | string | Yes | expected 0 NULLs |
| 16 | `dropoff_borough` | `zone_lookup` (dropoff) | string | Yes | expected 0 NULLs |
| 17 | `dropoff_zone` | `zone_lookup` (dropoff) | string | Yes | expected 0 NULLs |

### `rideshare_dev.processed.trip_driver_assignment`

- **Format:** Delta managed table
- **Write mode:** `saveAsTable` overwrite (DROP TABLE IF EXISTS first)
- **Grain:** one row per (`driver_id`, `trip_id`)
- **Row count:** 100

| # | Column | Source | Type | Nullable | Notes |
|---|---|---|---|---|---|
| 1 | `driver_id` | `drivers_flat` | string | No | |
| 2 | `driver_name` | `drivers_flat` | string | Yes | |
| 3 | `license_number` | `drivers_flat` | string | Yes | |
| 4 | `vehicle_make` | `drivers_flat` | string | Yes | |
| 5 | `vehicle_model` | `drivers_flat` | string | Yes | |
| 6 | `vehicle_year` | `drivers_flat` | long | Yes | Inferred LongType from XML |
| 7 | `vehicle_body_type` | `drivers_flat` | string | Yes | |
| 8 | `trip_id` | `drivers_flat` | bigint | No | |
| 9 | `service_type` | `curated_trip` | string | Yes | Expected 0 NULLs — trips 1–100 all exist in curated_trip |
| 10 | `trip_distance_miles` | `curated_trip` | decimal(8,2) | Yes | Expected 0 NULLs |
| 11 | `ride_duration_mins` | `curated_trip` | int | Yes | Expected 0 NULLs |
| 12 | `pickup_location_id` | `curated_trip` | int | Yes | Expected 0 NULLs |
| 13 | `dropoff_location_id` | `curated_trip` | int | Yes | Expected 0 NULLs |

---

## Join logic

### trip_enriched — 4 joins in sequence

All joins use Boolean form with explicit DataFrame aliases. `Column`-object `.drop()`
(not string `.drop()`) resolves duplicate `trip_id` columns by lineage.

| Step | Left | Right | Type | Key | Predicted rows | Predicted NULLs |
|---|---|---|---|---|---:|---|
| 1 | `curated_trip` (106) | `trip_time` (100) | left | `trip_id` | 106 | 6 NULL `trip_date`, `hour_of_day` |
| 2 | result of 1 (106) | `curated_payment` (105) | left | `trip_id` | 106 | 1 NULL payment block |
| 3 | result of 2 (106) | `zone_lookup` aliased as pickup | left + `F.broadcast` | `pickup_location_id = location_id` | 106 | 0 |
| 4 | result of 3 (106) | `zone_lookup` aliased as dropoff | left + `F.broadcast` | `dropoff_location_id = location_id` | 106 | 0 |

### trip_driver_assignment — 1 join (practice section)

| Step | Left | Right | Type | Key | Predicted rows | Predicted NULLs |
|---|---|---|---|---|---:|---|
| 1 | `drivers_flat` (100) | `curated_trip` (106) | left | `trip_id` | 100 | 0 |

Left drives from `drivers_flat` — not from `curated_trip`. Driving from `curated_trip`
would produce 106 rows and create NULLs for driver columns on trips 101–106. The
assignment table's grain is the assignment; unassigned trips belong in a separate
anti-join reveal, not in the table itself.

---

## Known gaps and intentional NULLs

| Table | Column(s) | Affected rows | Root cause |
|---|---|---|---|
| `trip_enriched` | `trip_date`, `hour_of_day` | trips 101–106 (6 rows) | `trip_time` only covers trips 1–100 |
| `trip_enriched` | `payment_method`, `base_fare_amount`, `tip_amount`, `driver_payout_amount` | trip 106 (1 row) | `curated_payment` has no record for trip 106 |
| `trip_enriched` | `pickup_borough`, `pickup_zone`, `dropoff_borough`, `dropoff_zone` | 0 rows | All trip location IDs are 1–20; zone_lookup covers 1–22 |
| `trip_driver_assignment` | any column from `curated_trip` | 0 rows | All 100 `drivers_flat` `trip_id` values (1–100) exist in `curated_trip` |

**Reveal (not a gap in the output table):** `curated_trip` left anti `drivers_flat` on
`trip_id` returns 6 rows (trips 101–106) — the same trips missing from `trip_time`.
This is a deliberate teaching moment in the practice section, not a write-time issue.

---

## Validation rules (write gate)

All checks run on the fully assembled DataFrame, before any write call. Write is gated
on all checks passing.

### trip_enriched

| # | Check | Expected | Failure means |
|---|---|---|---|
| 1 | `trip_enriched.count()` | 106 | Join added or removed rows |
| 2 | `trip_enriched.filter(trip_date.isNull()).count()` | 6 | trip_time gap changed |
| 3 | `trip_enriched.filter(payment_method.isNull()).count()` | 1 | payment gap changed |
| 4 | `trip_enriched.filter(pickup_borough.isNull()).count()` | 0 | Zone lookup failed |
| 5 | `trip_enriched.filter(dropoff_borough.isNull()).count()` | 0 | Zone lookup failed |
| 6 | `curated_trip.join(curated_payment, trip_id, left_anti).count()` | 1 | Source data changed |

### trip_driver_assignment

| # | Check | Expected | Failure means |
|---|---|---|---|
| 1 | `trip_driver_assignment.count()` | 100 | Join added or removed rows |
| 2 | `drivers_flat.join(curated_trip, trip_id, left_anti).count()` | 0 | Orphan trip_id in drivers_flat |

---

## Out of scope (not promoted to either output table)

| Column | Source table | Reason |
|---|---|---|
| `ride_duration_band` | `curated_trip` | Module 6 enrichment; Module 8 re-derives this as a CASE/when exercise |
| `service_label` | `curated_trip` | Module 6 enrichment; redundant display string |
| `trip_distance_km` | `curated_trip` | Module 6 enrichment; redundant dual-unit metric |
| `request_to_driver_arrival_mins` | `curated_trip` | Module 6 enrichment; derivable in-query |
| `diff_ride_duration_wait_mins` | `curated_trip` | Module 6 enrichment; derivable in-query |
| `driver_arrival_to_pickup_mins` | `curated_trip` | Sub-component metric; not a direct aggregation target |
| `surge_amount` | `curated_payment` | Full breakdown stays in `curated/payment/` |
| `tax_amount` | `curated_payment` | Full breakdown stays in `curated/payment/` |
| `discount_amount` | `curated_payment` | Full breakdown stays in `curated/payment/` |
| `charge_before_tip` | `curated_payment` | Derived metric; stays in `curated/payment/` |
| `tip_percent_of_base` | `curated_payment` | Derived metric; stays in `curated/payment/` |
| `service_zone` | `zone_lookup` | Not needed downstream |

---

## Design decisions — resolved

| Decision | Choice |
|---|---|
| `request_to_pickup_mins` in `trip_enriched` | **Included** — source column, not a Module 6 enrichment; useful for Module 8 wait-time aggregations |
| `ride_duration_band` in `trip_enriched` | **Excluded** — Module 6 enrichment; Module 8 re-derives it as a CASE/when exercise |
| `ride_duration_mins` in `trip_driver_assignment` | **Included** — enables driver-level duration aggregations in Module 8 |
| Final column counts | `trip_enriched` = **17 columns**, `trip_driver_assignment` = **13 columns** |
