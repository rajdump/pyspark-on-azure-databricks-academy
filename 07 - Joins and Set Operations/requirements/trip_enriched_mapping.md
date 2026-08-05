# `trip_enriched` — Source-to-Target Mapping

## Column Mapping

| # | Source Table / File | Source Column | Source Type | Source Constraints | Join Condition | Transformation | Target Column | Target Type | Target Constraints |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `curated_trip` | `trip_id` | bigint | PK, not null | — (primary source) | Direct | `trip_id` | bigint | PK, not null |
| 2 | `curated_trip` | `service_type` | string | not null | — | Direct | `service_type` | string | not null |
| 3 | `curated_trip` | `pickup_location_id` | int | nullable | — | Direct | `pickup_location_id` | int | nullable |
| 4 | `curated_trip` | `dropoff_location_id` | int | nullable | — | Direct | `dropoff_location_id` | int | nullable |
| 5 | `curated_trip` | `trip_distance_miles` | decimal(8,2) | nullable | — | Direct | `trip_distance_miles` | decimal(8,2) | nullable |
| 6 | `curated_trip` | `ride_duration_mins` | int | nullable | — | Direct | `ride_duration_mins` | int | nullable |
| 7 | `trip_time` | `trip_date` | date | not null | left join on trip.trip_id = time.trip_id | Direct | `trip_date` | date | nullable |
| 8 | `trip_time` | `hour_of_day` | int | not null | left join on trip.trip_id = time.trip_id | Direct | `hour_of_day` | int | nullable |
| 9 | `curated_payment` | `payment_method` | string | nullable | left join on trip.trip_id = payment.trip_id | Direct | `payment_method` | string | nullable |
| 10 | `curated_payment` | `base_fare_amount` | decimal(10,2) | nullable | left join on trip.trip_id = payment.trip_id | Direct | `base_fare_amount` | decimal(10,2) | nullable |
| 11 | `curated_payment` | `tip_amount` | decimal(10,2) | nullable | left join on trip.trip_id = payment.trip_id | Direct | `tip_amount` | decimal(10,2) | nullable |
| 12 | `curated_payment` | `driver_payout_amount` | decimal(10,2) | nullable | left join on trip.trip_id = payment.trip_id | Direct | `driver_payout_amount` | decimal(10,2) | nullable |
| 13 | `zone_lookup` | `borough_name` | string | nullable | left broadcast on trip.pickup_location_id = zone.location_id | Rename | `pickup_borough` | string | nullable |
| 14 | `zone_lookup` | `zone_name` | string | nullable | left broadcast on trip.pickup_location_id = zone.location_id | Rename | `pickup_zone` | string | nullable |
| 15 | `zone_lookup` | `borough_name` | string | nullable | left broadcast on trip.dropoff_location_id = zone.location_id | Rename | `dropoff_borough` | string | nullable |
| 16 | `zone_lookup` | `zone_name` | string | nullable | left broadcast on trip.dropoff_location_id = zone.location_id | Rename | `dropoff_zone` | string | nullable |

---

## Open Decisions and Approval

No open mapping decisions remain.

| Field | Value |
|---|---|
| Target table | `rideshare_dev.processed.trip_enriched` |
| Business grain | One row per `trip_id` |
| Status | Draft |
| Related BRD | `BRD.md` |
