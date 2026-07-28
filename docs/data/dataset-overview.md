# Dataset Overview — Rideshare

Canonical owner of the rideshare dataset's logical tables, columns/types,
join keys, and physical layout (Git source files + Unity Catalog Volume
paths from Module 5). Referenced by `.cursor/rules/learner-notebooks.mdc`,
`/new-lesson`, `/write-lesson`, `/validate-notebook`, `/review-module`, and
Cmd+K sessions via `@docs/data/dataset-overview.md` — do not duplicate this
content elsewhere. Module notebook sequences and privileges live in that
module's `README.md`. Shared read list: @docs/standards/notebook-authoring-checklist.md.

Intentionally small (100/100/100/20 rows) for fast iteration — not for
demonstrating shuffle, spill, or skew at volume (Module 16 uses it for
plan-reading only).

## Core logical tables

| Table | Rows | Role |
|---|---:|---|
| `trip` | 100 | Central fact table |
| `trip_time` | 100 | 1:1 extension of `trip` — date and time |
| `payment` | 100 | 1:1 extension of `trip` — fare breakdown |
| `zone_lookup` | 20 | Dimension — pickup and dropoff locations |

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

## Supplementary: `drivers` (nested XML)

12 `<driver>` records — not a fifth core table.

| Field | Type |
|---|---|
| `driver_id` | string, e.g. `D001` |
| `name` | string |
| `license_number` | string |
| `vehicle` | struct — `make`, `model`, `year`, `body_type` |
| `trips_assigned` | repeated `trip_id` list |

Joinable to `trip` after `explode()` on `trips_assigned`.

## Physical layout

**Modules 1–4:** hand-built DataFrames in code (column names/types above).
**Modules 5+:** learner notebooks use Unity Catalog Volume paths only — not
`abfss://` URLs.

| Platform piece | Value |
|---|---|
| Catalog / schema | `academy` / `rideshare` |
| Volumes | `raw`, `processed`, `source` |
| External location | `el_lab` (already exists; grants/credentials → Module 11) |
| Secrets | `el-lab` / `sql-password` |

Volume path pattern: `/Volumes/academy/rideshare/{volume}/{dataset}/`

**Write rule:** Module 6 owns cleaned `processed/{dataset}/`; Modules 7–9
use new output names (`trip_enriched`, KPI tables, etc.) to avoid overwrites.

### Datasets at a glance

Academy folder names: `trip`, `trip_time`, `zone_lookup`, `payment`,
`drivers`.

| Dataset | Module 5 format | Repo source (Git) | Volume destination |
|---|---|---|---|
| `trip` | CSV | `data/raw/csv/trip.csv` | `raw/trip/` |
| `trip_time` | Parquet | `data/raw/parquet/trip_time.parquet` | `raw/trip_time/` |
| `zone_lookup` | JSON Lines | `data/raw/json/zone_lookup.json` | `raw/zone_lookup/` |
| `drivers` | XML | `data/raw/xml/drivers.xml` | `raw/drivers/` |
| `payment` | Avro | `data/raw/{csv,json,parquet}/payment.*` also in repo | `raw/payment/` |

Module 5 copies repo files into Volume `raw/{dataset}/`. JSON is
newline-delimited; Parquet preserves decimals. Other formats exist in the
repo for authoring flexibility but each dataset has one primary read format
in Module 5.

### `payment` JDBC exercise (Module 5)

`payment` also has a live **Azure SQL Database** source. Run on an
all-purpose cluster (not serverless):

1. Seed from `source/payment/`
2. JDBC write → `el_lab.payments`
3. JDBC read ← `el_lab.payments`
4. Write Avro → `raw/payment/`

SQL table `el_lab.payments` ≠ Volume folder `payment`. Connection details
live in the Module 5 README — never committed here. Repo `data/raw/avro/` stays
empty; Avro lands on the Volume only.
