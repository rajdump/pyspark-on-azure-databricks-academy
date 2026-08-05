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

## Data Layers: Landing vs Bronze vs Silver vs Gold

### Landing Zone ≠ Bronze (common confusion)

| Aspect | Landing Zone | Bronze Layer |
|--------|-------------|-------------|
| What it is | Files on disk (CSV, JSON, Parquet, XML) | Managed Delta **table** |
| Format | Native source format | Unified (Delta) |
| Queryable via SQL? | No — need Spark reader | Yes — `SELECT * FROM bronze.trip` |
| ACID guarantees? | No — just files | Yes — transactions, time travel |
| Schema enforced? | No — discover at read time | Yes — defined at creation |
| Data changed? | No | No (still raw, no cleaning) |
| Lifespan | Often ephemeral | Permanent — system of record |

> **Key insight:** Same raw data — difference is Bronze **registers** it as a
> proper table with schema, versioning, and SQL access.

### Where our data sits today

```
 Landing (raw files)              Silver (cleaned)              Gold (query-ready)
 ———————————————————              ————————————————              ——————————————————
 bad_trip_data.csv (108 rows)     curated/trip (106 rows)       trip_enriched (106)
 bad_payment_data.csv (106 rows)  curated/payment (105 rows)    trip_driver_assignment (100)
 trip_time.parquet (100 rows)     drivers_flat (100 rows)
 zone_lookup.json (22 rows)       trip_time (100 rows)
 drivers.xml (12 records)         zone_lookup (22 rows)
```

**This course skips formal Bronze** — Module 6 reads directly from landing and
writes cleaned Silver. Module 12 will add the Bronze table layer.

### Medallion layer test

> "Can this data have bad rows, duplicates, or wrong types?"
> * Yes → Bronze
> * No, it's cleaned → Silver
> * No, and it's joined/aggregated for a specific use case → Gold

---

## Why Medallion + Delta Later? (Course Progression)

### Problems we CAN'T solve today (no Delta yet)

| Pain Point | What happens today | Delta + Medallion solves it |
|-----------|-------------------|----------------------------|
| Overwrote curated/trip | Old version is gone forever | Time travel: `VERSION AS OF` |
| Cleaning job failed halfway | Data is half-written, corrupt state | ACID: all-or-nothing transactions |
| New records arrived | Must reprocess everything | `MERGE` / incremental upserts |
| Landing files deleted | No raw backup exists | Bronze table: permanent raw record |
| Schema changed upstream | Pipeline breaks silently | Schema enforcement + evolution |
| "Who wrote what and when?" | No audit trail | Audit columns: `ingested_at`, `source_file` |

### Module progression (building blocks)

```
  Module 5-6  →  Module 7 (HERE)  →  Module 8-9  →  Module 10  →  Module 12  →  Module 13
  ——————————     ——————————————       ——————————     ——————————     ——————————     ——————————
  Files:         Files → Unified:     Managed tbls:  Delta Lake:    Medallion:     Incremental:
  read/write/    joins, left joins,   aggregation,   ACID, time     formalize      MERGE upserts,
  clean          zone lookups,        window fns,    travel,        Bronze/Silver/ idempotency,
                 gap visibility       pivot, KPIs    MERGE, schema  Gold w/ Delta  late-arriving
                                                     evolution                     data
```

### What each module adds to the architecture

| Module | You learn | Architecture contribution |
|--------|----------|---------------------------|
| 5 | Read/write files on Volumes | Establishes landing zone |
| 6 | Clean, type, deduplicate | Builds Silver (curated) outputs |
| **7** | **Join + unify** | **Builds Gold (consumption) tables** |
| 8 | Aggregate + window | Produces KPI/metric tables from Gold |
| 9 | SQL + DataFrame interop | Validates pipeline in both APIs |
| 10 | Delta Lake | Adds ACID, versioning, MERGE to all layers |
| 12 | Medallion architecture | Formalizes Bronze/Silver/Gold with Delta |
| 13 | Incremental processing | Makes pipeline idempotent + resilient |

> **You are here (Module 7):** Learning the "what and why" of unified tables.
> Module 12 adds the "how to make it production-grade" with Delta.

---

## Column Selection Rationale

### Why trip_enriched drops some columns from curated_trip

| Column | Included? | Reason |
|--------|-----------|--------|
| trip_id | Yes | Primary key |
| service_type | Yes | Core business dimension |
| service_label | No | Redundant — derived from service_type |
| pickup_location_id | Yes | FK retained (zone names added alongside) |
| dropoff_location_id | Yes | FK retained (zone names added alongside) |
| trip_distance_miles | Yes | Core metric |
| trip_distance_km | No | Redundant — miles x 1.609 |
| request_to_pickup_mins | No | Operational detail |
| driver_arrival_to_pickup_mins | No | Operational detail |
| request_to_driver_arrival_mins | No | Operational detail |
| ride_duration_mins | Yes | Core metric |
| diff_ride_duration_wait_mins | No | Derived (duration - wait) |
| ride_duration_band | No | Derived bucket |

### Metrics LOST by dropping those columns

| Lost Metric | Column Needed | Use Case |
|------------|--------------|----------|
| Wait time by zone/hour | request_to_pickup_mins | "Bronx has worst wait times" |
| Driver response ranking | driver_arrival_to_pickup_mins | "Amit Patel is fastest (2.0 min avg)" |
| SLA violation detection | wait / ride ratio | "Trip 46: 200% wait-to-ride ratio" |
| Journey time breakdown | All timing columns | "Delay is in dispatch, not pickup" |
| Revenue by duration band | ride_duration_band | "Long trips = 60% of revenue" |

### Design tradeoff

```
  LEAN TABLE (current)                    FAT TABLE (alternative)
  ---------------------                   ------------------------
  * Focused on its purpose                * Self-contained for ALL metrics
  * Fewer columns = easier to read        * More columns = wider schema
  * Module 8 may need re-joins            * Module 8 never needs re-joins
  * Teaches: "pick what you need"         * Teaches: "include everything"
```

> **The data is NOT lost** — source files remain at curated/trip.
> Module 8 can always join back by trip_id if it needs wait-time metrics.

---


## Silver vs Gold: Where Do Joins Belong?

### The rule of thumb

| Join Type | Where it belongs | Why |
|-----------|-----------------|-----|
| Reuniting fragments of the SAME entity | Silver | "Cleaning up a source system quirk" |
| Combining MULTIPLE business entities | Gold | "Purpose-built for a specific consumer" |

### Example with our data

```
  trip + trip_time  →  Could be Silver
                       (both keyed on trip_id, 1:1, same entity split by source design)

  trip + payment + zone + drivers  →  Definitely Gold
                       (multiple entities, shaped for trip analytics use case)
```

### Why NOT join everything in Silver?

Different teams need different combinations:

```
  Team A (Operations):  trip + time + zone          (no payment needed)
  Team B (Finance):     trip + payment              (no zone, no driver)
  Team C (Fleet):       trip + driver + payment     (no zone)
```

If you pre-join in Silver → one massive wide table that:
  * Has columns some teams don't need
  * Forces everyone to read data they don't care about
  * Breaks for ALL teams if any one source schema changes

### The architecture purist approach

```
  SILVER (one clean entity per table — reusable building blocks):
  ┌─────────────────────────────────────────────────────────┐
  │  silver.trip      ← trip + trip_time merged (same entity)│
  │  silver.payment   ← cleaned payment                      │
  │  silver.driver    ← cleaned, flattened driver             │
  │  silver.zone      ← clean dimension                      │
  └─────────────────────────────────────────────────────────┘
           │                │               │
           │    Different Gold tables pick what THEY need
           ▼                ▼               ▼
  GOLD (purpose-built for specific consumers):
  ┌─────────────────────────────────────────────────────────┐
  │  gold.trip_enriched            ← trip + payment + zone   │
  │  gold.trip_driver_assignment   ← driver + trip + payment │
  │  gold.finance_summary          ← trip + payment only     │
  │  gold.fleet_dashboard          ← driver + trip only      │
  └─────────────────────────────────────────────────────────┘
```

### Key properties comparison

| Property | Silver | Gold |
|----------|--------|------|
| Scope | One entity per table | Multiple entities combined |
| Purpose | "Clean source of truth" | "Ready for THIS use case" |
| Reusability | High — many Gold tables read from it | Lower — built for specific consumers |
| Coupling | Independent — changing one doesn't break others | Coupled — source changes may break the join |
| Who uses it | Data engineers (to build Gold) | Analysts, BI tools, ML models |
| Row count changes? | Only from cleaning (rejects) | Can change from joins (fan-out or NULLs) |

### Summary

> Silver = WHAT the data IS (clean, single-subject, trustworthy)
> Gold = HOW the data is USED (joined, aggregated, purpose-built)


## Design Decision: Lean Now, Full Pipeline in Module 12

### The three options considered

| Option | Approach | Verdict |
|--------|----------|---------|
| 1 | Fat table now — pull ALL columns, calculate metrics in Module 8 | Rejected |
| 2 | Lean table now — only core columns, ignore extras | Accepted (Module 7-8) |
| 3 | Full end-to-end pipeline with all columns + all metrics | Accepted (Module 12) |

### Final strategy: Option 2 (now) + Option 3 (later)

### Why lean tables in Module 7-8

* Module 7's job = teach JOIN mechanics, not column management
* 38 columns in one table drowns students while learning join types
* Focus stays on "how does LEFT JOIN work?" not "which columns to select?"
* Teaches design discipline: not every column belongs in every table
* Keeps Module 8 aggregation queries simple and readable

### Why full pipeline in Module 12

* Shows contrast between "learning exercise" and "production pipeline"
* Students see same data processed two ways — reinforces understanding
* Delivers the "surprise — you already know 50% of medallion" moment
* Full pipeline includes:
  - Bronze: ALL files → Delta (1:1, all columns, warts included)
  - Silver: Clean all columns (nothing dropped except bad rows)
  - Gold: Multiple purpose-built tables with ALL possible metrics
    - trip_enriched_full (all trip + payment + time + zone columns)
    - driver_performance (all driver + wait-time + SLA metrics)
    - kpi_hourly_zone (all aggregations Module 8 style)

### The teaching arc

```
  Module 7 (lean):   "Here's HOW to join — we pick only what we need"
                      → Focus: join types, grain, NULLs, left-join preservation

  Module 8 (lean):   "Here's HOW to aggregate — GROUP BY, windows, KPIs"
                      → Focus: aggregation mechanics on focused columns

  Module 12 (full):  "Now build the REAL production pipeline end-to-end"
                      → Focus: architecture, Delta, all columns, all metrics
                      → Reveals: "You already learned Silver + Gold — now
                        we add Bronze and do it all properly with Delta"
```

### The "aha" moment planned for Module 12

> "In Module 7, we deliberately excluded request_to_pickup_mins and
> driver_arrival_to_pickup_mins. That was a DESIGN CHOICE, not a
> limitation. In production, your Gold layer serves multiple consumers —
> so you build multiple Gold tables, each with the columns ITS consumer
> needs. Here's the full pipeline that includes everything."

---

*Notes created from BRD discussion — NB07 Build Unified Curated Tables*
