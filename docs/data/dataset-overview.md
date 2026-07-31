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
**Modules 5+:** learners use Unity Catalog Volume paths for reads and writes.
Setup and teardown notebooks (Module 5 Notebooks 01 and 99) may use a
config-built `abfss://` root for external-location / managed-location DDL
and ADLS teardown only. Format and transform notebooks use `/Volumes/...`
paths only — not hardcoded `abfss://` URLs.

Each student uses their own Azure storage and Databricks workspace. Course
object names below are fixed; Azure account/container/credential values are
set in the Notebook 01 / 99 config cell.

| Platform piece | Value |
|---|---|
| Catalog | `rideshare_dev` |
| Schemas | `landing`, `processed` |
| Volumes | `landing.source_files`, `processed.output_files` |
| External location | `el_rideshare_dev` (created in Module 5 Notebook 01) |
| Storage credential | Student-provided name in the config cell (creation how-to is outside this repo) |

### Glossary (avoid shorthand)

| Term | Meaning |
|---|---|
| Schema `landing` / `processed` | Unity Catalog schemas under `rideshare_dev` |
| Volume `source_files` / `output_files` | External volumes under those schemas |
| Folder `practice/` / `curated/` | Directories inside `output_files` (created on first write) |

Do not write “processed/” alone in notebooks — say the full Volume path or
`practice/` / `curated/` tier. Schema names `landing` / `processed` are
**not** medallion Bronze/Silver/Gold (Module 12).

### Path patterns

```text
/Volumes/rideshare_dev/landing/source_files/{dataset}/
/Volumes/rideshare_dev/processed/output_files/practice/{output_name}/
/Volumes/rideshare_dev/processed/output_files/curated/{output_name}/
```

**Write rules:**

- Module 5 practice writes → `…/processed/output_files/practice/{output_name}/`
- Module 6+ pipeline outputs → `…/processed/output_files/curated/{output_name}/`
  (cleaned datasets, enrichments, KPIs — descriptive snake_case folder names)
- Do not read `practice/` after Module 5; later modules read landing and/or
  prior `curated/` outputs

### Datasets at a glance

Dataset folder names: `trip`, `trip_time`, `zone_lookup`, `payment`,
`drivers`.

| Dataset | Module 5 format | Repo source (Git) | Volume destination |
|---|---|---|---|
| `trip` | CSV | `data/raw/csv/trip.csv` | `landing/source_files/trip/` |
| `trip_time` | Parquet | `data/raw/parquet/trip_time.parquet` | `landing/source_files/trip_time/` |
| `zone_lookup` | JSON Lines | `data/raw/json/zone_lookup.json` | `landing/source_files/zone_lookup/` |
| `drivers` | XML | `data/raw/xml/drivers.xml` | `landing/source_files/drivers/` |
| `payment` | Avro | `data/raw/avro/payment.avro` | `landing/source_files/payment/` |

Module 5 Notebook 01 also lands two supplementary bad-data learning files:

| Purpose | Repo source (Git) | Volume destination |
|---|---|---|
| Trip cleaning | `data/raw/csv/bad_trip_data.csv` | `landing/source_files/trip/bad_trip_data.csv` |
| Payment cleaning | `data/raw/csv/bad_payment_data.csv` | `landing/source_files/payment/bad_payment_data.csv` |

These small CSV files exist only to make rejection and repair behavior
visible in Module 6 **`03 - Cleaning and Curated Outputs`**. They are not
additional logical datasets and are never written directly to `curated/`.
Canonical `trip.csv` and `payment.avro` remain the sources for curated
pipeline outputs.

JSON is newline-delimited; Parquet preserves decimals. Other payment formats
may exist under `data/raw/` for authoring flexibility; Module 5’s primary
`payment` read format is Avro.
