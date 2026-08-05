# `trip_driver_assignment` — Source-to-Target Mapping

## Column Mapping

| # | Source Table / File | Source Column | Source Type | Source Constraints | Join Condition | Transformation | Target Column | Target Type | Target Constraints |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `drivers_flat` | `driver_id` | string | PK (composite), not null | — (primary source) | Direct | `driver_id` | string | PK (composite), not null |
| 2 | `drivers_flat` | `driver_name` | string | nullable | — | Direct | `driver_name` | string | nullable |
| 3 | `drivers_flat` | `license_number` | string | nullable | — | Direct | `license_number` | string | nullable |
| 4 | `drivers_flat` | `vehicle_make` | string | nullable | — | Direct | `vehicle_make` | string | nullable |
| 5 | `drivers_flat` | `vehicle_model` | string | nullable | — | Direct | `vehicle_model` | string | nullable |
| 6 | `drivers_flat` | `vehicle_year` | long | nullable | — | Direct | `vehicle_year` | long | nullable |
| 7 | `drivers_flat` | `vehicle_body_type` | string | nullable | — | Direct | `vehicle_body_type` | string | nullable |
| 8 | `drivers_flat` | `trip_id` | bigint | PK (composite), not null | — | Direct | `trip_id` | bigint | PK (composite), not null |
| 9 | `curated_trip` | `service_type` | string | not null | left join on drivers.trip_id = trip.trip_id | Direct | `service_type` | string | nullable |
| 10 | `curated_trip` | `trip_distance_miles` | decimal(8,2) | nullable | left join on drivers.trip_id = trip.trip_id | Direct | `trip_distance_miles` | decimal(8,2) | nullable |
| 11 | `curated_trip` | `ride_duration_mins` | int | nullable | left join on drivers.trip_id = trip.trip_id | Direct | `ride_duration_mins` | int | nullable |
| 12 | `curated_trip` | `pickup_location_id` | int | nullable | left join on drivers.trip_id = trip.trip_id | Direct | `pickup_location_id` | int | nullable |
| 13 | `curated_trip` | `dropoff_location_id` | int | nullable | left join on drivers.trip_id = trip.trip_id | Direct | `dropoff_location_id` | int | nullable |

---

## Open Decisions and Approval

No open mapping decisions remain.

| Field | Value |
|---|---|
| Target table | `rideshare_dev.processed.trip_driver_assignment` |
| Business grain | One row per (`driver_id`, `trip_id`) |
| Status | Approved |
| Related BRD | `BRD.md` |
