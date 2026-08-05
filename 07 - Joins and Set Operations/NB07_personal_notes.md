# NB07 — Build Unified Curated Tables: Personal Notes

> How 5 scattered sources become 2 query-ready tables — explained with one sample trip.

---

## The Problem: 5 Separate Sources

Today, trip data lives in **5 independent files** with different row counts and grains.
No single place shows the full picture or surfaces the gaps.

---

## Source Inventory (what we start with)

| # | Source | Location | Grain (1 row =) | Key | Rows |
|---|--------|----------|-----------------|-----|------|
| 1 | `curated_trip` | `curated/trip` (Parquet) | one trip | `trip_id` | **106** |
| 2 | `curated_payment` | `curated/payment` (Parquet) | one trip's payment | `trip_id` | **105** |
| 3 | `trip_time` | `landing/trip_time` (Parquet) | one trip's date/hour | `trip_id` | **100** |
| 4 | `zone_lookup` | `landing/zone_lookup` (JSON) | one taxi zone | `location_id` | **22** |
| 5 | `drivers_flat` | `curated/drivers_flat` (Parquet) | one driver–trip pair | (`driver_id`, `trip_id`) | **100** |

---

## Sample Record: Trip 8 Across All 5 Sources

### Source 1 — `curated_trip`

| trip_id | service_type | pickup_location_id | dropoff_location_id | trip_distance_miles | ride_duration_mins |
|---------|--------------|-------------------|--------------------|--------------------|-------------------|
| 8 | PREMIUM | 1 | 5 | 12.75 | 55 |

### Source 2 — `curated_payment`

| trip_id | payment_method | base_fare_amount | surge_amount | tip_amount | driver_payout_amount |
|---------|---------------|-----------------|-------------|-----------|---------------------|
| 8 | card | 74.78 | 3.74 | 6.78 | 66.14 |

### Source 3 — `trip_time`

| trip_id | trip_date | hour_of_day |
|---------|-----------|-------------|
| 8 | 2026-03-06 | 3 |

### Source 4 — `zone_lookup` (two lookups needed)

| location_id | borough_name | zone_name |
|-------------|-------------|----------|
| 1 | Manhattan | Midtown East | ← pickup_location_id = 1
| 5 | Manhattan | Upper West Side | ← dropoff_location_id = 5

### Source 5 — `drivers_flat`

| driver_id | driver_name | license_number | vehicle_make | vehicle_model | vehicle_year | trip_id |
|-----------|-------------|---------------|-------------|--------------|-------------|--------|
| D001 | Ravi Kumar | DL-2024-0001 | Toyota | Camry | 2022 | 8 |

---

## Target 1: `trip_enriched` — What Trip 8 Looks Like After Unification

**Grain:** 1 row = 1 trip (`trip_id`) → **106 rows total**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        trip_enriched  (trip 8)                               │
├───────────────────────┬─────────────────────────────────────────────────────┤
│  FROM curated_trip    │  trip_id = 8                                        │
│                       │  service_type = PREMIUM                             │
│                       │  trip_distance_miles = 12.75                        │
│                       │  ride_duration_mins = 55                            │
├───────────────────────┼─────────────────────────────────────────────────────┤
│  FROM trip_time       │  trip_date = 2026-03-06                             │
│                       │  hour_of_day = 3                                    │
├───────────────────────┼─────────────────────────────────────────────────────┤
│  FROM zone_lookup     │  pickup_borough = Manhattan                         │
│  (×2 lookups)         │  pickup_zone = Midtown East                         │
│                       │  dropoff_borough = Manhattan                        │
│                       │  dropoff_zone = Upper West Side                     │
├───────────────────────┼─────────────────────────────────────────────────────┤
│  FROM curated_payment │  payment_method = card                              │
│                       │  base_fare_amount = 74.78                           │
│                       │  surge_amount = 3.74                                │
│                       │  tip_amount = 6.78                                  │
│                       │  driver_payout_amount = 66.14                       │
└───────────────────────┴─────────────────────────────────────────────────────┘
```

**Result row in table format:**

| trip_id | service_type | distance | duration | trip_date | hour | pickup_borough | pickup_zone | dropoff_borough | dropoff_zone | payment | fare | surge | tip | payout |
|---------|-------------|----------|----------|-----------|------|----------------|-------------|-----------------|--------------|---------|------|-------|-----|--------|
| 8 | PREMIUM | 12.75 | 55 | 2026-03-06 | 3 | Manhattan | Midtown East | Manhattan | Upper West Side | card | 74.78 | 3.74 | 6.78 | 66.14 |

---

## Target 2: `trip_driver_assignment` — What Trip 8 Looks Like

**Grain:** 1 row = 1 driver–trip pair (`driver_id`, `trip_id`) → **100 rows total**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  trip_driver_assignment  (trip 8)                            │
├───────────────────────┬─────────────────────────────────────────────────────┤
│  FROM drivers_flat    │  driver_id = D001                                   │
│                       │  driver_name = Ravi Kumar                           │
│                       │  license_number = DL-2024-0001                      │
│                       │  vehicle_make = Toyota                              │
│                       │  vehicle_model = Camry                              │
│                       │  vehicle_year = 2022                                │
│                       │  vehicle_body_type = Sedan                          │
├───────────────────────┼─────────────────────────────────────────────────────┤
│  FROM curated_trip    │  trip_id = 8                                        │
│                       │  service_type = PREMIUM                             │
│                       │  trip_distance_miles = 12.75                        │
│                       │  ride_duration_mins = 55                            │
├───────────────────────┼─────────────────────────────────────────────────────┤
│  FROM trip_time       │  trip_date = 2026-03-06                             │
│                       │  hour_of_day = 3                                    │
├───────────────────────┼─────────────────────────────────────────────────────┤
│  FROM curated_payment │  base_fare_amount = 74.78                           │
│                       │  driver_payout_amount = 66.14                       │
└───────────────────────┴─────────────────────────────────────────────────────┘
```

**Result row in table format:**

| driver_id | driver_name | license | vehicle | trip_id | service_type | distance | duration | trip_date | hour | fare | payout |
|-----------|-------------|---------|---------|---------|-------------|----------|----------|-----------|------|------|--------|
| D001 | Ravi Kumar | DL-2024-0001 | Toyota Camry 2022 | 8 | PREMIUM | 12.75 | 55 | 2026-03-06 | 3 | 74.78 | 66.14 |

---

## The Gap Scenario: Trip 106 (Worst Case)

Trip 106 exists in `curated_trip` but is **missing from all other sources**.

```
        curated_trip          curated_payment         trip_time            drivers_flat
       ┌───────────┐          ┌─────────────┐       ┌──────────┐         ┌─────────────┐
trip 8 │  ✅ EXISTS │          │  ✅ EXISTS   │       │ ✅ EXISTS │         │  ✅ EXISTS   │
       ├───────────┤          ├─────────────┤       ├──────────┤         ├─────────────┤
  ...  │    ...    │          │    ...      │       │   ...    │         │    ...      │
       ├───────────┤          ├─────────────┤       ├──────────┤         ├─────────────┤
trip106│  ✅ EXISTS │          │  ❌ MISSING  │       │ ❌ MISSING│         │  ❌ MISSING  │
       └───────────┘          └─────────────┘       └──────────┘         └─────────────┘
          106 rows                105 rows             100 rows              100 rows
```

**What trip 106 looks like in `trip_enriched` (NULLs reveal the gaps):**

| trip_id | service_type | distance | duration | trip_date | hour | pickup_borough | pickup_zone | payment | fare | surge | tip | payout |
|---------|-------------|----------|----------|-----------|------|----------------|-------------|---------|------|-------|-----|--------|
| 106 | STANDARD | NULL | 14 | **NULL** | **NULL** | Manhattan | Harlem | **NULL** | **NULL** | **NULL** | **NULL** | **NULL** |

> Without the unified table, trip 106 silently disappears — the analyst never
> knows it exists because each source looks "complete" on its own.

---

## Exact Gap Map (Trips 101–106)

| trip_id | in curated_trip? | in curated_payment? | in trip_time? | in drivers_flat? |
|---------|-----------------|--------------------|--------------|-----------------|
| 101 | ✅ | ✅ | ❌ | ❌ |
| 102 | ✅ | ✅ | ❌ | ❌ |
| 103 | ✅ | ✅ | ❌ | ❌ |
| 104 | ✅ | ✅ | ❌ | ❌ |
| 105 | ✅ | ✅ | ❌ | ❌ |
| 106 | ✅ | ❌ | ❌ | ❌ |

**Takeaway:** Gaps are staggered, not uniform. Only a unified left-join
surfaces all of them as visible NULLs.

---

## Join Strategy (Stepwise Left Joins)

```
                          trip_enriched build path
                          ════════════════════════

  curated_trip (106)  ──LEFT JOIN──▶  trip_time (100)     = 106 rows (6 NULL dates)
                                          │
                                     ──LEFT JOIN──▶  curated_payment (105)  = 106 rows (1 NULL payment)
                                                         │
                                                    ──LEFT JOIN──▶  zone_lookup (×2)  = 106 rows
                                                                        │
                                                                   trip_enriched ✅


                     trip_driver_assignment build path
                     ════════════════════════════════

  drivers_flat (100)  ──LEFT JOIN──▶  curated_trip (106)   = 100 rows
                                          │
                                     ──LEFT JOIN──▶  trip_time (100)  = 100 rows
                                                         │
                                                    ──LEFT JOIN──▶  curated_payment (105)  = 100 rows
                                                                        │
                                                                trip_driver_assignment ✅
```

**Key rule:** The LEFT side drives the row count. It never gains or loses
rows — only acquires NULLs where the right side has no match.

---

## Two Tables, Two Questions

| Aspect | `trip_enriched` | `trip_driver_assignment` |
|--------|----------------|-------------------------|
| Grain | 1 row = 1 trip | 1 row = 1 driver–trip pair |
| Rows | 106 (all trips, even unassigned) | 100 (only assigned trips) |
| Primary key | `trip_id` | (`driver_id`, `trip_id`) |
| Has zone info? | ✅ (borough + zone names) | ❌ |
| Has driver info? | ❌ | ✅ (name, license, vehicle) |
| Answers | Revenue, geography, timing, data quality | Driver earnings, workload, fleet |
| Feeds into | Module 8: KPI aggregations | Module 8: Driver performance metrics |

---

## What Module 8 Will Do With These Tables

| From `trip_enriched` | From `trip_driver_assignment` |
|---------------------|------------------------------|
| Avg fare by borough | Top earners ranking |
| Surge patterns by hour | Earning per trip efficiency |
| Revenue by payment × zone | Vehicle type comparison |
| Trip distance distributions | Driver daily schedule |
| Data completeness metrics | Fleet composition |

> **No more 5-way joins** — Module 8 just does simple GROUP BYs on these
> pre-built tables.

---

*Notes created from BRD discussion — NB07 Build Unified Curated Tables*
