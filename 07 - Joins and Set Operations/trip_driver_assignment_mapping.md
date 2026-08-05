## 1. Target mapping overview

| Field | Value |
|---|---|
| Target table | `rideshare_dev.processed.trip_driver_assignment` |
| Business grain | One row per available driver–trip assignment |
| Primary source | `drivers_flat` |
| Business key | (`driver_id`, `trip_id`) |
| Related BRD | `BRD.md` |
| Mapping status | Draft |

---

## 2. Source datasets

| Source table or file | Source category | Grain | Business key | Role in target |
|---|---|---|---|---|
| `drivers_flat` | Primary | One row per (`driver_id`, `trip_id`) | (`driver_id`, `trip_id`) | Defines the target assignment record set and supplies driver and vehicle attributes |
| `curated_trip` | Supporting | One row per `trip_id` | `trip_id` | Supplies selected trip descriptors for each assignment |

---

## 3. Join mapping

The primary source defines the target grain and record set. Supporting and lookup
sources add attributes without removing or unexpectedly multiplying primary-source
records.

| Join order | Left source | Right source | Left join column(s) | Right join column(s) | Join type | Expected relationship | Unmatched-row handling |
|---:|---|---|---|---|---|---|---|
| 1 | `drivers_flat` | `curated_trip` | `trip_id` | `trip_id` | Left | Many-to-one | Preserve the driver–trip assignment; trip columns become `NULL` when the referenced trip does not resolve |

---

## 4. Column mapping

| # | Source table or file | Source column(s) | Source data type | Source nullable | Mapping type | Transformation rule | Target table | Target column | Target data type | Target nullable | Key / constraint | Default value | NULL handling | Business rule / notes |
|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `drivers_flat` | `driver_id` | string | No | Direct | Copy without transformation | `rideshare_dev.processed.trip_driver_assignment` | `driver_id` | string | No | Part of composite business key; not null | None | Source value is required | Defines the target grain with trip_id |
| 2 | `drivers_flat` | `driver_name` | string | Yes | Direct | Copy without transformation | `rideshare_dev.processed.trip_driver_assignment` | `driver_name` | string | Yes | None | None | Retain source NULL | — |
| 3 | `drivers_flat` | `license_number` | string | Yes | Direct | Copy without transformation | `rideshare_dev.processed.trip_driver_assignment` | `license_number` | string | Yes | None | None | Retain source NULL | — |
| 4 | `drivers_flat` | `vehicle_make` | string | Yes | Direct | Copy without transformation | `rideshare_dev.processed.trip_driver_assignment` | `vehicle_make` | string | Yes | None | None | Retain source NULL | — |
| 5 | `drivers_flat` | `vehicle_model` | string | Yes | Direct | Copy without transformation | `rideshare_dev.processed.trip_driver_assignment` | `vehicle_model` | string | Yes | None | None | Retain source NULL | — |
| 6 | `drivers_flat` | `vehicle_year` | long | Yes | Direct | Copy without transformation | `rideshare_dev.processed.trip_driver_assignment` | `vehicle_year` | long | Yes | None | None | Retain source NULL | — |
| 7 | `drivers_flat` | `vehicle_body_type` | string | Yes | Direct | Copy without transformation | `rideshare_dev.processed.trip_driver_assignment` | `vehicle_body_type` | string | Yes | None | None | Retain source NULL | — |
| 8 | `drivers_flat` | `trip_id` | bigint | No | Direct | Copy without transformation | `rideshare_dev.processed.trip_driver_assignment` | `trip_id` | bigint | No | Part of composite business key; not null | None | Source value is required | Defines the target grain with driver_id |
| 9 | `curated_trip` | `service_type` | string | No | Direct | Copy from the matched supporting record | `rideshare_dev.processed.trip_driver_assignment` | `service_type` | string | Yes | None | None | NULL when the referenced trip does not resolve | Expected to resolve for all valid assignments |
| 10 | `curated_trip` | `trip_distance_miles` | decimal(8,2) | Yes | Direct | Copy from the matched supporting record | `rideshare_dev.processed.trip_driver_assignment` | `trip_distance_miles` | decimal(8,2) | Yes | None | None | NULL when the referenced trip does not resolve | Expected to resolve for all valid assignments |
| 11 | `curated_trip` | `ride_duration_mins` | int | Yes | Direct | Copy from the matched supporting record | `rideshare_dev.processed.trip_driver_assignment` | `ride_duration_mins` | int | Yes | None | None | NULL when the referenced trip does not resolve | Expected to resolve for all valid assignments |
| 12 | `curated_trip` | `pickup_location_id` | int | Yes | Direct | Copy from the matched supporting record | `rideshare_dev.processed.trip_driver_assignment` | `pickup_location_id` | int | Yes | None | None | NULL when the referenced trip does not resolve | Expected to resolve for all valid assignments |
| 13 | `curated_trip` | `dropoff_location_id` | int | Yes | Direct | Copy from the matched supporting record | `rideshare_dev.processed.trip_driver_assignment` | `dropoff_location_id` | int | Yes | None | None | NULL when the referenced trip does not resolve | Expected to resolve for all valid assignments |

---

## 5. Excluded columns

| Source table or file | Excluded source column | Source data type | Reason for exclusion | Available from |
|---|---|---|---|---|
| `curated_trip` | `request_to_pickup_mins` | int | Outside the agreed driver-assignment target scope | `curated_trip` |
| `curated_trip` | `driver_arrival_to_pickup_mins` | int | Outside the agreed driver-assignment target scope | `curated_trip` |
| `curated_trip` | `request_to_driver_arrival_mins` | int | Outside the agreed driver-assignment target scope | `curated_trip` |
| `curated_trip` | `diff_ride_duration_wait_mins` | int | Outside the agreed driver-assignment target scope | `curated_trip` |
| `curated_trip` | `ride_duration_band` | string | Outside the agreed driver-assignment target scope | `curated_trip` |
| `curated_trip` | `service_label` | string | Outside the agreed driver-assignment target scope | `curated_trip` |
| `curated_trip` | `trip_distance_km` | decimal(8,2) | Outside the agreed driver-assignment target scope | `curated_trip` |

### Sources not mapped to this target

| Source dataset | Reason |
|---|---|
| `trip_time` | Time attributes are outside the driver-assignment target scope |
| `curated_payment` | Payment attributes are outside the driver-assignment target scope |
| `zone_lookup` | Zone names remain available through `trip_enriched` |

---

## 6. Mapping rules and constraints

### 6.1 Target grain and key rules

- Target grain is one row per available driver–trip assignment.
- (`driver_id`, `trip_id`) is the composite business key; together they must uniquely identify one target row.
- `drivers_flat` defines the target record set.
- Trips without an assignment must not create target rows.
- Business-key columns must not contain `NULL`.
- Supporting-source joins must not unexpectedly duplicate primary-source records.
- The target must not include records outside the `drivers_flat` record set.

### 6.2 Join and cardinality rules

- Join conditions are defined once in Section 3 and must not be repeated in column-level specifications.
- Left joins preserve the primary-source record set.
- `curated_trip` must contain no more than one row per `trip_id` (many-to-one from the driver-assignment perspective).
- Unexpected duplicate matches are a source-data or mapping issue and must not be silently accepted.
- Unmatched `curated_trip` references retain the left-side row and produce `NULL` for the related target columns.
- Join implementation details such as aliases, broadcast hints, and duplicate-column removal belong in the notebook technical plan, not in this mapping document.

### 6.3 Data type and transformation rules

- Direct mappings retain the source value and data type unless Section 4 explicitly defines otherwise.
- Decimal precision and scale must be preserved unless an approved transformation requires a different target type.
- No implicit default value, cast, or data-format conversion may be added outside the documented mapping.
- `service_type` is carried through without transformation.

### 6.4 NULL-handling rules

- Source NULLs are retained unless Section 4 defines a different rule.
- Unresolved `curated_trip` references technically produce `NULL` in mapped trip columns.
- The BRD requires every assignment `trip_id` to resolve to an existing curated trip.
- No default value may replace missing trip values unless explicitly approved.
- Required business-key columns must not be `NULL`.
- Target nullable status must distinguish NULLs already present in the source from NULLs introduced by an unmatched left join.
- Dataset-specific NULL counts are not part of the permanent mapping contract.

### 6.5 Mapping completeness rules

- Every approved target column must appear exactly once in Section 4.
- Every Section 4 source column must exist in a source dataset listed in Section 2.
- Every supporting source used in Section 4 must have a relationship defined in Section 3.
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
| Mapping document | `trip_driver_assignment_mapping.md` |
| Target table | `rideshare_dev.processed.trip_driver_assignment` |
| Current status | Draft |
| Related BRD | `BRD.md` |
| Open decisions remaining | None |

| Review role | Reviewer | Status | Review date |
|---|---|---|---|
| Business or requirements reviewer |  | Pending |  |
| Data engineering reviewer |  | Pending |  |
| Course-content reviewer |  | Pending |  |
