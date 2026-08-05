## 1. Target mapping overview

| Field | Value |
|---|---|
| Target table | `rideshare_dev.processed.trip_enriched` |
| Business grain | One row per `trip_id` |
| Primary source | `curated_trip` |
| Business key | `trip_id` |
| Related BRD | `BRD.md` |
| Mapping status | Draft |

---

## 2. Source datasets

| Source table or file | Source category | Grain | Business key | Role in target |
|---|---|---|---|---|
| `curated_trip` | Primary | One row per `trip_id` | `trip_id` | Defines the target trip record set and supplies selected trip attributes |
| `trip_time` | Supporting | One row per `trip_id` | `trip_id` | Supplies trip date and hour information |
| `curated_payment` | Supporting | One row per `trip_id` | `trip_id` | Supplies selected payment attributes |
| `zone_lookup` | Lookup | One row per `location_id` | `location_id` | Supplies borough and zone names for pickup and drop-off locations |

---

## 3. Join mapping

The primary source defines the target grain and record set. Supporting and lookup
sources add attributes without removing or unexpectedly multiplying primary-source
records.

| Join order | Left source | Right source | Left join column(s) | Right join column(s) | Join type | Expected relationship | Unmatched-row handling |
|---:|---|---|---|---|---|---|---|
| 1 | `curated_trip` | `trip_time` | `trip_id` | `trip_id` | Left | One-to-zero-or-one | Preserve the trip; time columns become `NULL` when no time record exists |
| 2 | Result after time join | `curated_payment` | `trip_id` | `trip_id` | Left | One-to-zero-or-one | Preserve the trip; payment columns become `NULL` when no payment record exists |
| 3 | Result after payment join | `zone_lookup` — pickup role | `pickup_location_id` | `location_id` | Left | Many-to-one | Preserve the trip; pickup-zone columns become `NULL` when the lookup does not resolve |
| 4 | Result after pickup-zone join | `zone_lookup` — drop-off role | `dropoff_location_id` | `location_id` | Left | Many-to-one | Preserve the trip; drop-off-zone columns become `NULL` when the lookup does not resolve |

`zone_lookup` is used twice because pickup and drop-off locations represent two
different relationships to the same reference dataset.

---

## 4. Column mapping

| # | Source table or file | Source column(s) | Source data type | Source nullable | Mapping type | Transformation rule | Target table | Target column | Target data type | Target nullable | Key / constraint | Default value | NULL handling | Business rule / notes |
|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `curated_trip` | `trip_id` | bigint | No | Direct | Copy without transformation | `rideshare_dev.processed.trip_enriched` | `trip_id` | bigint | No | Business key; unique; not null | None | Source value is required | Defines the target grain |
| 2 | `curated_trip` | `service_type` | string | No | Direct | Copy without transformation | `rideshare_dev.processed.trip_enriched` | `service_type` | string | No | Not null | None | Source value is required | Carried through without transformation |
| 3 | `curated_trip` | `pickup_location_id` | int | Yes | Direct | Copy without transformation | `rideshare_dev.processed.trip_enriched` | `pickup_location_id` | int | Yes | None | None | Retain source NULL | Used as join key to resolve pickup zone |
| 4 | `curated_trip` | `dropoff_location_id` | int | Yes | Direct | Copy without transformation | `rideshare_dev.processed.trip_enriched` | `dropoff_location_id` | int | Yes | None | None | Retain source NULL | Used as join key to resolve drop-off zone |
| 5 | `curated_trip` | `trip_distance_miles` | decimal(8,2) | Yes | Direct | Copy without transformation | `rideshare_dev.processed.trip_enriched` | `trip_distance_miles` | decimal(8,2) | Yes | None | None | Retain source NULL | — |
| 6 | `curated_trip` | `ride_duration_mins` | int | Yes | Direct | Copy without transformation | `rideshare_dev.processed.trip_enriched` | `ride_duration_mins` | int | Yes | None | None | Retain source NULL | — |
| 7 | `trip_time` | `trip_date` | date | No | Direct | Copy from the matched supporting record | `rideshare_dev.processed.trip_enriched` | `trip_date` | date | Yes | None | None | NULL when no matching time record exists | Optional supporting attribute |
| 8 | `trip_time` | `hour_of_day` | int | No | Direct | Copy from the matched supporting record | `rideshare_dev.processed.trip_enriched` | `hour_of_day` | int | Yes | None | None | NULL when no matching time record exists | Optional supporting attribute |
| 9 | `curated_payment` | `payment_method` | string | Yes | Direct | Copy from the matched supporting record | `rideshare_dev.processed.trip_enriched` | `payment_method` | string | Yes | None | None | NULL when no matching payment record exists | Optional supporting attribute |
| 10 | `curated_payment` | `base_fare_amount` | decimal(10,2) | Yes | Direct | Copy from the matched supporting record | `rideshare_dev.processed.trip_enriched` | `base_fare_amount` | decimal(10,2) | Yes | None | None | NULL when no matching payment record exists | Optional supporting attribute |
| 11 | `curated_payment` | `tip_amount` | decimal(10,2) | Yes | Direct | Copy from the matched supporting record | `rideshare_dev.processed.trip_enriched` | `tip_amount` | decimal(10,2) | Yes | None | None | NULL when no matching payment record exists | Optional supporting attribute |
| 12 | `curated_payment` | `driver_payout_amount` | decimal(10,2) | Yes | Direct | Copy from the matched supporting record | `rideshare_dev.processed.trip_enriched` | `driver_payout_amount` | decimal(10,2) | Yes | None | None | NULL when no matching payment record exists | Optional supporting attribute |
| 13 | `zone_lookup` — pickup role | `borough_name` | string | Yes | Lookup + Rename | Copy from the pickup lookup and rename | `rideshare_dev.processed.trip_enriched` | `pickup_borough` | string | Yes | None | None | NULL when the lookup does not resolve | Expected to resolve for all valid location IDs |
| 14 | `zone_lookup` — pickup role | `zone_name` | string | Yes | Lookup + Rename | Copy from the pickup lookup and rename | `rideshare_dev.processed.trip_enriched` | `pickup_zone` | string | Yes | None | None | NULL when the lookup does not resolve | Expected to resolve for all valid location IDs |
| 15 | `zone_lookup` — drop-off role | `borough_name` | string | Yes | Lookup + Rename | Copy from the drop-off lookup and rename | `rideshare_dev.processed.trip_enriched` | `dropoff_borough` | string | Yes | None | None | NULL when the lookup does not resolve | Expected to resolve for all valid location IDs |
| 16 | `zone_lookup` — drop-off role | `zone_name` | string | Yes | Lookup + Rename | Copy from the drop-off lookup and rename | `rideshare_dev.processed.trip_enriched` | `dropoff_zone` | string | Yes | None | None | NULL when the lookup does not resolve | Expected to resolve for all valid location IDs |

---

## 5. Excluded columns

| Source table or file | Excluded source column | Source data type | Reason for exclusion | Available from |
|---|---|---|---|---|
| `curated_trip` | `service_label` | string | Derived upstream and redundant with `service_type` | `curated_trip` |
| `curated_trip` | `trip_distance_km` | decimal(8,2) | Derived upstream; the target retains `trip_distance_miles` | `curated_trip` |
| `curated_trip` | `request_to_driver_arrival_mins` | int | Derived upstream and outside the agreed target scope | `curated_trip` |
| `curated_trip` | `diff_ride_duration_wait_mins` | int | Derived upstream and outside the agreed target scope | `curated_trip` |
| `curated_trip` | `ride_duration_band` | string | Derived upstream and not promoted into this target | `curated_trip` |
| `curated_trip` | `driver_arrival_to_pickup_mins` | int | Source-level subcomponent metric outside the agreed target scope | `curated_trip` |
| `curated_trip` | `request_to_pickup_mins` | int | Source-level subcomponent metric outside the agreed target scope | `curated_trip` |
| `curated_payment` | `surge_amount` | decimal(10,2) | Full payment breakdown remains in `curated_payment` | `curated_payment` |
| `curated_payment` | `tax_amount` | decimal(10,2) | Full payment breakdown remains in `curated_payment` | `curated_payment` |
| `curated_payment` | `discount_amount` | decimal(10,2) | Full payment breakdown remains in `curated_payment` | `curated_payment` |
| `curated_payment` | `charge_before_tip` | decimal(10,2) | Derived payment metric retained in `curated_payment` | `curated_payment` |
| `curated_payment` | `tip_percent_of_base` | decimal(10,2) | Derived payment metric retained in `curated_payment` | `curated_payment` |
| `zone_lookup` | `service_zone` | string | Reference attribute outside the target contract | `zone_lookup` |

---

## 6. Mapping rules and constraints

### 6.1 Target grain and key rules

- Target grain is one row per `trip_id`.
- `trip_id` is the business key; it must uniquely identify one target row.
- `curated_trip` defines the target record set.
- Every `curated_trip` row must remain in the target regardless of whether supporting records exist.
- Business-key columns must not contain `NULL`.
- Supporting-source joins must not unexpectedly duplicate primary-source records.
- The target must not include records outside the `curated_trip` record set.

### 6.2 Join and cardinality rules

- Join conditions are defined once in Section 3 and must not be repeated in column-level specifications.
- Left joins preserve the primary-source record set.
- `trip_time` and `curated_payment` must contain no more than one matching row per `trip_id` (one-to-zero-or-one).
- `zone_lookup` must contain no more than one row per `location_id` (many-to-one from the trip perspective).
- Unexpected duplicate matches are a source-data or mapping issue and must not be silently accepted.
- Unmatched optional supporting records retain the left-side row and produce `NULL` for the related target columns.
- Join implementation details such as aliases, broadcast hints, and duplicate-column removal belong in the notebook technical plan, not in this mapping document.

### 6.3 Data type and transformation rules

- Direct mappings retain the source value and data type unless Section 4 explicitly defines otherwise.
- Rename mappings change only the target column name; the source value and data type are preserved.
- Lookup mappings use the reference relationship defined in Section 3.
- Derived and constant mappings may be used only when explicitly approved in Section 4.
- Decimal precision and scale must be preserved unless an approved transformation requires a different target type.
- No implicit default value, cast, or data-format conversion may be added outside the documented mapping.
- `service_type` is carried through without transformation.

### 6.4 NULL-handling rules

- Source NULLs are retained unless Section 4 defines a different rule.
- Missing `trip_time` records produce `NULL` in `trip_date` and `hour_of_day`.
- Missing `curated_payment` records produce `NULL` in mapped payment columns.
- Unresolved zone lookups technically produce `NULL`, although the BRD requires every valid trip location to resolve.
- No default value may replace missing time, payment, or lookup values unless explicitly approved.
- Required business-key columns must not be `NULL`.
- Target nullable status must distinguish NULLs already present in the source from NULLs introduced by an unmatched left join.
- Dataset-specific NULL counts are not part of the permanent mapping contract.

### 6.5 Mapping completeness rules

- Every approved target column must appear exactly once in Section 4.
- Every Section 4 source column must exist in a source dataset listed in Section 2.
- Every supporting or lookup source used in Section 4 must have a relationship defined in Section 3.
- Columns intentionally omitted from relevant source scope must be documented in Section 5.
- Included and excluded columns must not overlap.
- Target column order must match the approved target contract.
- Source fields must remain on the left side of the column-mapping table and target fields on the right.
- Fixed row counts, fixed NULL counts, Spark code, write logic, and performance hints must not appear in this document.

---

## 7. Open decisions and approval

### 7.1 Open mapping decisions

No open mapping decisions remain. Target grain, source relationships, column
mappings, exclusions, data types, and NULL-handling rules have been agreed.

### 7.2 Document approval

| Field | Value |
|---|---|
| Mapping document | `trip_enriched_mapping.md` |
| Target table | `rideshare_dev.processed.trip_enriched` |
| Current status | Draft |
| Related BRD | `BRD.md` |
| Open decisions remaining | None |

| Review role | Reviewer | Status | Review date |
|---|---|---|---|
| Business or requirements reviewer |  | Pending |  |
| Data engineering reviewer |  | Pending |  |
| Course-content reviewer |  | Pending |  |
