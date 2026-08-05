# Business Requirements Document
## Build Unified Curated Tables

## 1. Document status

* **Status:** Draft
* **Module:** Module 07, Notebook 07 — Build Unified Curated Tables
* **Basis:** verified runtime cross-check results against the current curated and landing sources (Aug 2026)

---

## 2. Background

Curated trip, payment, and driver data currently live in separate curated outputs
(`curated_trip`, `curated_payment`, `drivers_flat`) and landing sources (`trip_time`,
`zone_lookup`). There is no single, query-ready view that combines trip, time,
payment, zone, and driver information at a consistent grain.

---

## 3. Business problem

Without a unified view, anyone analyzing trips or driver assignments has to work
across multiple curated and landing sources and reconcile them manually. Known gaps
in the supporting sources (missing time and payment records for some trips) are not
visible in any single place today.

---

## 4. Objective

Produce two Unity Catalog managed Delta tables that combine the curated and landing
sources into two clear, consistent grains — preserving every driving record and
keeping known data gaps visible as `NULL` rather than hidden or dropped.

---

## 5. Business deliverables

### `rideshare_dev.processed.trip_enriched`

* One row per `trip_id`
* Preserve every curated trip
* Expected result: target count equals the driving `curated_trip` count
* For the fixed course dataset: 106 rows
* Missing time or payment data must remain visible as `NULL`
* Geographic lookup details must resolve for all valid trip location IDs

### `rideshare_dev.processed.trip_driver_assignment`

* One row per (`driver_id`, `trip_id`)
* Preserve every available driver assignment
* Expected result: target count equals the driving `drivers_flat` count
* For the fixed course dataset: 100 rows
* All assignment trip IDs must resolve to an existing curated trip

---

## 6. Downstream consumers

* **Module 8** (aggregations and window functions) — reads both tables as its
  primary analytical source.
* **Module 9** (Spark SQL) — reads both tables as its primary analytical source.

Both tables are the primary read surfaces for these two modules.

---

## 7. Business requirements

### BR-01 — Create both target tables

The solution must produce `trip_enriched` and `trip_driver_assignment` as new,
refreshable outputs built from the current curated and landing sources.

### BR-02 — Define target grain

`trip_enriched` must contain one row per `trip_id`. `trip_driver_assignment` must
contain one row per (`driver_id`, `trip_id`).

### BR-03 — Preserve every curated trip

The solution must produce one `trip_enriched` row for every row in `curated_trip`.
Missing records from supporting sources (time, payment, zone) must not remove the
trip from the output.

**Expected for the course dataset:** 106 rows.

### BR-04 — Preserve every available driver assignment

The solution must produce one `trip_driver_assignment` row for every row in
`drivers_flat`. Trips without a driver assignment must not appear in this table.

**Expected for the course dataset:** 100 rows.

### BR-05 — Keep known gaps visible as NULL

Where a trip has no matching time record or no matching payment record, the
corresponding `trip_enriched` columns must be `NULL` rather than dropping the trip
or substituting a default value.

**Expected for the course dataset:** 6 trips with missing time information; 1 trip
with missing payment information.

### BR-06 — Resolve zone details for every trip

Every trip's pickup and drop-off location must resolve to a borough and zone name in
`trip_enriched`.

**Expected for the course dataset:** zero trips with unresolved pickup or drop-off
zone details.

### BR-07 — Guarantee driver-assignment integrity

Every `trip_id` present in `trip_driver_assignment` must correspond to an existing
row in `curated_trip`. No assignment may reference a trip that does not exist.

**Expected for the course dataset:** zero assignments referencing a missing trip.

### BR-08 — Make outputs available to downstream modules

Both tables must be available for Module 8 and Module 9 to use as their primary
read surfaces.

### BR-09 — Deliver as managed Delta tables

Both outputs must be delivered as Unity Catalog managed Delta tables, fully
refreshed on each run so downstream modules always read current output.

---

## 8. Business rules

* `trip_enriched` carries source-level trip attributes and what the joins add — not
  enrichment values already computed upstream. Those enrichment values remain
  available at their source so Module 8 can re-derive some of them as an exercise.
* `trip_enriched` carries core payment facts only (payment method, base fare, tip,
  driver payout). The full payment breakdown remains available at its source.
* `trip_enriched` includes borough and zone name for both pickup and drop-off
  locations.
* `trip_driver_assignment` is scoped to the assignment: it carries driver details
  plus a small set of trip descriptors (service type, distance, duration, pickup and
  drop-off location IDs). Time, payment, and zone-name attributes are not included,
  as they do not belong to the assignment grain.
* `trip_driver_assignment` must be built from the driver-assignment source as the
  driving record set, not from the trip source, so that trips without a driver
  assignment do not appear as assignment records.
* Final business scope: `trip_enriched` carries 17 columns; `trip_driver_assignment`
  carries 13 columns.

---

## 9. Data availability and known gaps

* **Time data:** unavailable for 6 trips in the course dataset. `trip_enriched`
  shows `NULL` for time-related columns on those trips.
* **Payment data:** unavailable for 1 trip in the course dataset. `trip_enriched`
  shows `NULL` for payment-related columns on that trip.
* **Zone data:** every trip's pickup and drop-off location is covered by the
  geographic reference data, so no unresolved zone lookups are expected.
* **Driver-assignment data:** unavailable for 6 trips in the course dataset. Those
  trips simply do not appear in `trip_driver_assignment`, since its grain is the
  assignment, not the trip.

---

## 10. Acceptance criteria

### `trip_enriched`

* Has one row per `trip_id`.
* Row count equals the `curated_trip` count; expected 106.
* Six trips have missing time information.
* One trip has missing payment information.
* No trip has unresolved pickup or drop-off zone details.

### `trip_driver_assignment`

* Has one row per (`driver_id`, `trip_id`).
* Row count equals the `drivers_flat` count; expected 100.
* No driver assignment references a missing curated trip.

### Both outputs

* Available as Unity Catalog managed Delta tables.

---

## 11. In scope

* Building `trip_enriched` by combining curated trip data with time, payment, and
  zone information.
* Building `trip_driver_assignment` by combining driver-assignment data with a
  small set of trip descriptors.
* Delivering both as Unity Catalog managed Delta tables for consumption by Module 8
  and Module 9.

---

## 12. Out of scope

* Enrichment values already computed upstream of the curated trip and payment data
  (for example, derived duration categories, dual-unit distance, and derived payment
  metrics) are not promoted into either output table; they remain available at
  their source.
* The full payment cost breakdown and the zone service-zone attribute are not
  promoted into either output table.
* Aggregation, window-function, and SQL-based analysis of the output tables — that
  work belongs to Module 8 and Module 9, not to this deliverable.

---

## 13. Assumptions and dependencies

* Assumes the curated sources (`curated_trip`, `curated_payment`, `drivers_flat`)
  and landing sources (`trip_time`, `zone_lookup`) are already produced and stable
  for the course dataset (106 trips, 105 payment records, 100 driver assignments,
  100 time records, 22 zones).
* Depends on `curated_trip` as the single source of truth for trip identity and
  grain.
* Depends on the geographic reference data continuing to cover every pickup and
  drop-off location referenced by trips.

---

## 14. Open decisions

None identified. All column-selection and grain decisions currently in scope have
been agreed (see Section 8, Business rules).

---

## 15. Approval status

**Draft — not yet approved.** Pending business sign-off.
