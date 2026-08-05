# Business Requirements Document
## Build Unified Curated Tables

---

## 1. Document status

| Field | Value |
|---|---|
| Status | Draft |
| Module | 07 — Joins and Set Operations |
| Notebook | 07 — Build Unified Curated Tables |
| Version | 1.0 |
| Date | Aug 2026 |

---

## 2. Background

Modules 8 (Aggregations and Window Functions) and 9 (Spark SQL and CTEs) require
analytics-ready data surfaces that combine trip, time, payment, zone, and driver
information into a form that can be queried directly. At the point Notebook 07 runs,
those attributes exist across five separate sources — three curated Parquet datasets
and two landing files — with no consolidated view available to downstream modules.

Notebook 07 is the capstone of Module 7. Its sole purpose is to produce the two managed
tables that Modules 8 and 9 depend on. It does not perform cleaning or enrichment; those
are the responsibility of Module 6. It joins, selects, validates, and writes.

---

## 3. Business problem

**Problem 1 — Fragmented trip data.** A complete picture of any trip requires joining
five separate sources. Performing that join ad hoc at the start of every Module 8 and 9
exercise would be repetitive, error-prone, and would distract from the learning
objectives of those modules.

**Problem 2 — Disconnected driver assignments.** Driver assignment data in `drivers_flat`
has no direct link to the trip attributes (service type, distance, duration) that give
an assignment business meaning. Module 8 and 9 exercises on driver performance require
those attributes to be co-located with the assignment record.

---

## 4. Objective

Produce two Unity Catalog managed Delta tables that consolidate the required source data
into grain-correct, analytics-ready views, and make them available for Modules 8 and 9
to query without further source joins.

---

## 5. Business deliverables

### `rideshare_dev.processed.trip_enriched`

A single analytics-ready record per curated trip. It combines every trip's core
attributes with the trip's date and time, core payment facts, and the names of its
pickup and drop-off zones.

| Attribute | Value |
|---|---|
| Grain | One row per `trip_id` |
| Driving source | `curated_trip` |
| Row rule | Every curated trip must appear in the output |
| Expected rows (course dataset) | 106 |
| Storage | Unity Catalog managed Delta table |
| Write behaviour | Idempotent — prior version dropped before each write |

### `rideshare_dev.processed.trip_driver_assignment`

A single record per driver–trip assignment. It combines every assignment with the basic
attributes of the assigned trip to support driver-level analysis.

| Attribute | Value |
|---|---|
| Grain | One row per (`driver_id`, `trip_id`) |
| Driving source | `drivers_flat` |
| Row rule | Every driver assignment must appear in the output |
| Expected rows (course dataset) | 100 |
| Storage | Unity Catalog managed Delta table |
| Write behaviour | Idempotent — prior version dropped before each write |

---

## 6. Downstream consumers

| Consumer | Role |
|---|---|
| Module 8 — Aggregations and Window Functions | Reads both tables as its primary input for group-by, aggregation, and window-function exercises |
| Module 9 — Spark SQL and CTEs | Reads both tables for SQL query, CTE, and join exercises |

No other modules depend on these two tables within the current course design.

---

## 7. Business requirements

### BR-01 — Create `trip_enriched` as a managed Delta table

The solution must create `rideshare_dev.processed.trip_enriched` as a managed table in
the Unity Catalog `rideshare_dev.processed` schema, stored in Delta format.

### BR-02 — Create `trip_driver_assignment` as a managed Delta table

The solution must create `rideshare_dev.processed.trip_driver_assignment` as a managed
table in the Unity Catalog `rideshare_dev.processed` schema, stored in Delta format.

### BR-03 — Preserve every curated trip in `trip_enriched`

`trip_enriched` must contain one row for every row in `curated_trip`. Missing records
from optional supporting sources (`trip_time`, `curated_payment`) must not remove a trip
from the output. Those missing values must appear as `NULL`.

**Expected for the course dataset:** 106 rows.

### BR-04 — Preserve every driver assignment in `trip_driver_assignment`

`trip_driver_assignment` must contain one row for every row in `drivers_flat`. The
driving table is `drivers_flat`, not `curated_trip`. Trips that have no driver assignment
are excluded from this table by design; they are not a data quality issue.

**Expected for the course dataset:** 100 rows.

### BR-05 — `trip_enriched` must include trip attributes, time, core payment facts, and zone names

The content of `trip_enriched` is restricted to:

- Core trip attributes from `curated_trip`: identifier, service type, location IDs,
  distance, ride duration, and wait time from request to pickup
- Date and time of the trip from `trip_time`
- Core payment facts from `curated_payment`: payment method, base fare, tip, and driver
  payout
- Pickup and drop-off zone names from `zone_lookup`

Module 6 computed enrichments (derived columns added by Module 6's cleaning pipeline)
are excluded. They remain available in the curated trip and payment sources for any
notebook that needs them.

### BR-06 — `trip_driver_assignment` must include driver details and core trip attributes

The content of `trip_driver_assignment` is restricted to:

- All driver and vehicle fields from `drivers_flat`
- Core trip attributes from `curated_trip` relevant to an assignment: service type,
  distance, duration, and location IDs

Zone names, time, and payment columns are excluded from this table. Those belong to
the trip-level story, not the assignment story.

### BR-07 — Known missing time data must appear as NULL, not cause row removal

Six trips (IDs 101–106) have no corresponding record in `trip_time`. Their date and
time fields in `trip_enriched` must be `NULL`. These rows must remain in the output.

### BR-08 — Known missing payment data must appear as NULL, not cause row removal

One trip (ID 106) has no corresponding record in `curated_payment`. Its payment fields
in `trip_enriched` must be `NULL`. This row must remain in the output.

### BR-09 — Every trip location must resolve to a zone name

All trip pickup and drop-off location identifiers fall within the range covered by
`zone_lookup`. Every trip must resolve to a named pickup zone and a named drop-off zone.
No `NULL` zone names are acceptable in `trip_enriched`.

### BR-10 — No driver assignment may reference a non-existent trip

Every `trip_id` in `drivers_flat` must correspond to a record in `curated_trip`. If any
assignment cannot be matched to a curated trip, the write must not proceed.

**Expected for the course dataset:** zero unmatched assignments.

### BR-11 — Both tables must be available before Modules 8 and 9 begin

Both tables must be written and readable from the `rideshare_dev.processed` schema
before any Module 8 or Module 9 notebook runs.

### BR-12 — Writes must be idempotent

Re-running Notebook 07 must produce identical output. The existing table must be
replaced, not appended to.

---

## 8. Business rules

**BRule-01 — service_type values are uppercase.**
`service_type` values in `curated_trip` — and therefore in both output tables — are
uppercase: `STANDARD`, `PREMIUM`, `SHARED`, `UNKNOWN`. Any downstream filter or
comparison must use uppercase values.

**BRule-02 — Core payment facts only in `trip_enriched`.**
The full payment breakdown (surge, tax, discount, and derived amounts) is not promoted
to `trip_enriched`. Only the four values directly relevant to trip-level analysis are
included: `payment_method`, `base_fare_amount`, `tip_amount`, `driver_payout_amount`.
The full breakdown remains accessible in `curated/payment/`.

**BRule-03 — Module 6 enrichments are excluded from both output tables.**
Columns computed by Module 6's cleaning pipeline — such as bucketed duration categories
and distance unit conversions — are not carried forward. Module 8 exercises re-derive
these from the source columns included in the output tables.

**BRule-04 — `trip_driver_assignment` is driven by the assignment, not the trip.**
The row count of `trip_driver_assignment` is determined by `drivers_flat`, not by
`curated_trip`. Trips without a driver assignment (IDs 101–106) do not appear in this
table. Their absence is expected and correct.

**BRule-05 — Zone lookup references two location fields independently.**
Each trip has a pickup location and a drop-off location. Both must be resolved to zone
names independently. The same lookup source is used for both lookups.

---

## 9. Data availability and known gaps

The following gaps exist in the source data. They are known, verified, and intentional
outcomes of Module 6's cleaning pipeline. They do not represent data quality problems
in this notebook.

| Gap | Affected trips | Effect on output |
|---|---|---|
| No time record | Trips 101–106 (6 trips) | `trip_enriched`: `trip_date` and `hour_of_day` are NULL for these rows |
| No payment record | Trip 106 (1 trip) | `trip_enriched`: all payment fields are NULL for this row |
| No driver assignment | Trips 101–106 (6 trips) | These trips do not appear in `trip_driver_assignment` — the table is driven by assignments, not trips |
| Unused zone IDs | Location IDs 21–22 | These two zones exist in `zone_lookup` but are never referenced by any trip; they produce no NULLs |

No other gaps have been identified. All trip location IDs resolve to zone names. All
driver assignment trip IDs match a curated trip record.

---

## 10. Acceptance criteria

The following criteria must be met before either table is considered complete. No
implementation expressions or technical checks are required here; the MAPPING document
defines the corresponding validation logic.

### `trip_enriched`

| # | Criterion |
|---|---|
| AC-01 | `trip_enriched` contains exactly one row per `trip_id` |
| AC-02 | The row count equals the `curated_trip` row count — expected 106 for the course dataset |
| AC-03 | Exactly 6 rows have a NULL date and time — corresponding to trips 101–106 |
| AC-04 | Exactly 1 row has NULL payment information — corresponding to trip 106 |
| AC-05 | Zero rows have a NULL pickup zone name |
| AC-06 | Zero rows have a NULL drop-off zone name |
| AC-07 | The table is readable from `rideshare_dev.processed.trip_enriched` as a Delta table |

### `trip_driver_assignment`

| # | Criterion |
|---|---|
| AC-08 | `trip_driver_assignment` contains exactly one row per (`driver_id`, `trip_id`) pair |
| AC-09 | The row count equals the `drivers_flat` row count — expected 100 for the course dataset |
| AC-10 | Every assignment `trip_id` matches a record in `curated_trip` — zero unmatched assignments |
| AC-11 | The table is readable from `rideshare_dev.processed.trip_driver_assignment` as a Delta table |

---

## 11. In scope

- Joining curated and landing source data into the two output tables defined in
  Section 5
- Validating row counts and known NULL conditions before writing
- Writing both tables as Unity Catalog managed Delta tables in `rideshare_dev.processed`
- Making both tables available for Modules 8 and 9

---

## 12. Out of scope

- Data cleaning or enrichment — completed in Module 6
- Aggregations or window functions — Module 8
- SQL queries or CTEs on the output tables — Module 9
- Delta table internals (ACID guarantees, MERGE, time travel) — Module 10
- Unity Catalog privilege grants on the output tables — Module 11
- Join plan tuning beyond a high-level awareness note — Module 16
- Updating `dataset-overview.md` to reflect curated schemas — tracked separately, outside this notebook's scope
- Updating Module 5 Notebook 99 cleanup levels — tracked separately

---

## 13. Assumptions and dependencies

| # | Assumption or dependency |
|---|---|
| A-01 | Module 6 Notebooks 02 and 03 have run successfully and their curated outputs are available in the processed Volume |
| A-02 | Module 5 Notebook 01 has run and the `trip_time` and `zone_lookup` landing files are present in the landing Volume |
| A-03 | The learner has `CREATE TABLE` privilege on `rideshare_dev.processed` and read access to both the landing and processed Volumes |
| A-04 | The course dataset is fixed — the row counts stated in this document (106 trips, 105 payments, 100 assignments, 100 time records, 22 zones) are not expected to change |
| A-05 | The two output tables are written once per module run; concurrent writes are not a concern in this single-learner course environment |

---

## 14. Open decisions

No open decisions remain. All column-selection choices have been resolved and are
recorded in the approved MAPPING document.

---

## 15. Approval status

| Role | Name | Status |
|---|---|---|
| Author | — | Draft — pending review |
