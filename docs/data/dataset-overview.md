# Dataset Overview — Rideshare

Canonical owner of the rideshare dataset's logical tables, columns/types,
join keys, physical formats, and `data/raw/` layout. Referenced by
`.cursor/rules/learner-notebooks.mdc`, `/new-lesson`, `/validate-notebook`,
`/review-module`, and Cmd+K inline-edit sessions (via explicit `@docs/data/dataset-overview.md`) — do
not duplicate this content elsewhere.

This is the single running example threaded through every module. It is
intentionally small and transformation-friendly, so the same data supports
everything from hand-built DataFrames in Module 1 through Delta/Unity
Catalog work in Modules 11–13.

## Core logical tables

| Table | Rows | Role |
|---|---:|---|
| `trip` | 100 | Central fact table |
| `trip_time` | 100 | 1:1 extension of `trip` — date and time of the trip |
| `payment` | 100 | 1:1 extension of `trip` — fare breakdown |
| `zone_lookup` | 20 | Dimension table, referenced for both pickup and dropoff |

Later modules may use larger generated variants of this same shape — not
part of this initial setup.

### `trip`

| Column | Type |
|---|---|
| `trip_id` | bigint |
| `service_type` | string |
| `pickup_location_id` | int |
| `dropoff_location_id` | int |
| `trip_distance_miles` | decimal(8,2) |
| `request_to_pickup_mins` | int |
| `ride_duration_mins` | int |
| `driver_arrival_to_pickup_mins` | int |

### `trip_time`

| Column | Type |
|---|---|
| `trip_id` | bigint |
| `trip_date` | date |
| `hour_of_day` | int |

### `payment`

| Column | Type |
|---|---|
| `trip_id` | bigint |
| `payment_method` | string |
| `base_fare_amount` | decimal(10,2) |
| `surge_amount` | decimal(10,2) |
| `tax_amount` | decimal(10,2) |
| `tip_amount` | decimal(10,2) |
| `discount_amount` | decimal(10,2) |
| `driver_payout_amount` | decimal(10,2) |

### `zone_lookup`

| Column | Type |
|---|---|
| `location_id` | int |
| `borough_name` | string |
| `zone_name` | string |
| `service_zone` | string |

## Join keys

- `trip.trip_id = trip_time.trip_id`
- `trip.trip_id = payment.trip_id`
- `trip.pickup_location_id = zone_lookup.location_id`
- `trip.dropoff_location_id = zone_lookup.location_id`

`zone_lookup` is referenced twice (pickup and dropoff), which makes it
useful for teaching multiple joins to the same lookup table (Module 8).

## Supplementary dataset: `drivers` (nested XML)

`drivers.xml` is a nested, non-flat dataset — 12 `<driver>` records — kept
separately from the 4 core logical tables above. It exists specifically to
teach nested-structure reading and `explode()` (Module 6 for the read, Module 7
for complex-type handling), not as a fifth core table.

| Field | Type |
|---|---|
| `driver_id` | string, e.g. `D001` |
| `name` | string |
| `license_number` | string |
| `vehicle` | nested struct — `make`, `model`, `year`, `body_type` |
| `trips_assigned` | nested repeated element — a list of `trip_id` values assigned to that driver |

Joinable back to the core tables after flattening:
`trip.trip_id = drivers.trips_assigned[].trip_id` (after `explode()`).

## Secondary live source: `payment` in Azure SQL Database

In addition to the static bulk files below, the `payment` table also has a
live source in an **Azure SQL Database**. This is used specifically for
Module 6's reader/writer exercise: connect via JDBC from Azure Databricks
(not locally), read `payment` from Azure SQL Database, and write the result
to `data/raw/avro/` as an Avro file. This is why `data/raw/avro/` starts
empty in this initial setup — it is populated as Module 6 content, not as a
repository-setup data-prep step. Connection details (server name, auth
method, secret scope) are Module 6 design, documented there, and are never
committed to this repository.

## File layout

```
data/raw/
├── csv/        trip.csv, trip_time.csv, payment.csv, zone_lookup.csv
├── json/       trip.json, trip_time.json, payment.json, zone_lookup.json
├── parquet/    trip.parquet, trip_time.parquet, payment.parquet, zone_lookup.parquet
├── avro/       (empty at setup — populated by Module 6's Azure SQL Database exercise)
└── xml/
    └── drivers.xml
```

- JSON files are newline-delimited (JSON Lines) — reads cleanly in Spark.
- Parquet files preserve intended types, including decimals.
- CSV and JSON drive the ingestion-format lessons, where explicit schemas
  are taught alongside `inferSchema` (Module 6).

## Note on scale

This dataset is intentionally tiny (100/100/100/20 rows). It's sized for
fast iteration while learning syntax and patterns — it is not meant to
demonstrate shuffle, spill, or skew behavior at volume. Module 17
(Performance and Spark Internals) uses this same data for syntax and
plan-reading; real performance-at-scale behavior is out of scope for this
course.
