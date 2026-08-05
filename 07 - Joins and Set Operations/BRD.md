# Business Requirements Document
## Build Unified Curated Tables

## 1. Background and objective

Curated trip, payment, and driver data currently live in separate curated outputs
(`curated_trip`, `curated_payment`, `drivers_flat`) and landing sources (`trip_time`,
`zone_lookup`). There are no query-ready tables that consolidate trip-level
information and driver-assignment information at their appropriate business grains,
so anyone analyzing trips or driver assignments has to work across multiple sources
and reconcile them manually — with known gaps (missing time and payment records for
some trips) not visible in any single place today.

The objective is to produce two Unity Catalog managed Delta tables that combine the
curated and landing sources into two clear, consistent grains — preserving every
driving record and keeping known data gaps visible as `NULL` rather than hidden or
dropped.

---

## 2. Business deliverables

### `rideshare_dev.processed.trip_enriched`

One row per `trip_id`, driven by `curated_trip`. Combines trip attributes with time,
core payment facts, and pickup/drop-off zone details.

### `rideshare_dev.processed.trip_driver_assignment`

One row per (`driver_id`, `trip_id`), driven by `drivers_flat`. Combines driver
details with the agreed trip descriptors.

**Downstream consumers:** Module 8 (aggregations and window functions) and Module 9
(Spark SQL) read both tables as their primary analytical source.

---

## 3. Business requirements

### BR-01 — Create both target tables

The solution must produce `trip_enriched` and `trip_driver_assignment` from the
approved curated and landing sources.

### BR-02 — Preserve curated trips

`trip_enriched` must contain one row for every curated trip. Missing time or
payment records must remain visible as `NULL` rather than removing the trip. For
the fixed course dataset, the expected output is 106 rows.

### BR-03 — Preserve available driver assignments

`trip_driver_assignment` must contain one row for every available driver assignment.
Trips without a driver assignment must not appear in this table. For the fixed
course dataset, the expected output is 100 rows.

### BR-04 — Resolve zone details for every trip

Every trip's pickup and drop-off location in `trip_enriched` must resolve to a
borough and zone name; zero unresolved zones are expected for the course dataset.

### BR-05 — Guarantee driver-assignment integrity

Every `trip_id` present in `trip_driver_assignment` must correspond to an existing
row in `curated_trip`; zero orphaned assignments are expected for the course dataset.

### BR-06 — Deliver as managed Delta tables

Both outputs must be delivered as Unity Catalog managed Delta tables. Each
successful run must replace the previous contents so downstream modules read only
the latest complete output.

---

## 4. Business rules

* `trip_enriched` carries selected trip attributes together with supporting time,
  payment, and pickup/drop-off zone information. Previously derived enrichment
  columns are not promoted into `trip_enriched`; they remain available in their
  curated source.
* `trip_enriched` carries core payment facts only (payment method, base fare, tip,
  driver payout). The full payment breakdown remains available at its source.
* `trip_enriched` includes borough and zone name for both pickup and drop-off
  locations.
* `trip_driver_assignment` contains driver details and the agreed trip descriptors:
  service type, distance, duration, and pickup and drop-off location IDs. Time,
  payment, and zone-name attributes are outside this target's scope and remain
  available through `trip_enriched`.
* `trip_driver_assignment` must be built from the driver-assignment source as the
  driving record set, not from the trip source, so that trips without a driver
  assignment do not appear as assignment records.
* `service_type` is carried through from `curated_trip` without transformation.

---

## 5. Known data gaps

* **Time data:** unavailable for 6 trips in the course dataset. `trip_enriched`
  shows `NULL` for time-related columns on those trips.
* **Payment data:** unavailable for 1 trip in the course dataset. `trip_enriched`
  shows `NULL` for payment-related columns on that trip.
* **Zone data:** every trip's pickup and drop-off location is covered by the
  geographic reference data, so no unresolved zone lookups are expected.
* **Driver assignments:** no assignment records exist for 6 trips in the course
  dataset. These trips are excluded from `trip_driver_assignment` because its grain
  is one row per available driver–trip assignment, not one row per trip.

---

## 6. Acceptance criteria

### `trip_enriched`

* Meets BR-02 (grain, row count, and NULL visibility for missing time or payment
  data).
* Meets BR-04 (no unresolved pickup or drop-off zone details).

### `trip_driver_assignment`

* Meets BR-03 (grain and row count).
* Meets BR-05 (no assignment references a missing curated trip).

### Both outputs

* Meet BR-06 (delivered as managed Delta tables).

---

## 7. Scope and dependencies

**Out of scope:**

* Enrichment values already computed upstream of the curated trip and payment data
  (for example, derived duration categories, dual-unit distance, and derived payment
  metrics) are not promoted into either output table; they remain available at
  their source.
* The full payment cost breakdown and the zone service-zone attribute are not
  promoted into either output table.
* Aggregation, window-function, and SQL-based analysis of the output tables — that
  work belongs to Module 8 and Module 9, not to this deliverable.

**Assumptions and dependencies:**

* Assumes the curated sources (`curated_trip`, `curated_payment`, `drivers_flat`)
  and landing sources (`trip_time`, `zone_lookup`) are already produced and stable
  for the fixed course dataset described in the Business requirements section.
* Depends on `curated_trip` as the single source of truth for trip identity and
  grain.
* Depends on the geographic reference data continuing to cover every pickup and
  drop-off location referenced by trips.

---

## 8. Status

* **Status:** Draft — not yet approved. Pending business sign-off.
* **Module:** Module 07, Notebook 07 — Build Unified Curated Tables
* **Basis:** verified runtime cross-check results against the current curated and landing sources (Aug 2026)
* **Open decisions:** None identified. All column-selection and grain decisions
  currently in scope have been agreed (see Business rules).
