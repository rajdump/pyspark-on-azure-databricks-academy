# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC
# MAGIC # 03 - Lookup Joins, Columns, and Broadcast
# MAGIC
# MAGIC ## The problem: location IDs aren't names
# MAGIC
# MAGIC Every trip in `curated/trip` carries `pickup_location_id` and
# MAGIC `dropoff_location_id` — numeric codes, not human-readable places. To report
# MAGIC "trips from Manhattan to Brooklyn" you need to attach `zone_lookup`
# MAGIC attributes (`borough_name`, `zone_name`, `service_zone`) to **both** roles,
# MAGIC without duplicating the 22-row dimension table for each side.
# MAGIC
# MAGIC This notebook covers:
# MAGIC
# MAGIC * **Repeated lookup join** — joining the same dimension table twice with
# MAGIC   different aliases (pickup role, dropoff role)
# MAGIC * **Column cleanup** — resolving the duplicate/ambiguous names a repeated
# MAGIC   lookup produces
# MAGIC * **Unmatched dimension rows** — `zone_lookup` has two zones
# MAGIC   (`location_id` 21–22) no trip ever references; left vs right/full outer
# MAGIC   joins surface this differently
# MAGIC * **Broadcast** — hinting Spark to skip shuffling the large fact table
# MAGIC
# MAGIC **Reads:** landing `zone_lookup` (JSON Lines, 22 rows); processed
# MAGIC `curated/trip` (Parquet, 106 rows). **No write.**
# MAGIC
# MAGIC **Prerequisites.** Module 7 **`01 - Grain, Join Syntax, and Unmatched Keys`**
# MAGIC and **`02 - Silent Join Failures and Validation`** — Boolean join syntax,
# MAGIC `.alias`, key profiling, and left/right/full unmatched-key behavior are
# MAGIC applied here, not re-taught.

# COMMAND ----------

# DBTITLE 1,Setup
# MAGIC %md
# MAGIC ## Setup — fact vs dimension
# MAGIC
# MAGIC | Table | Format | Grain | Key | Rows |
# MAGIC |---|---|---|---|---|
# MAGIC | `curated/trip` | Parquet | one completed trip | `trip_id` | 106 |
# MAGIC | `zone_lookup` | JSON Lines | one taxi zone | `location_id` | 22 |
# MAGIC
# MAGIC `curated/trip` is the **fact** table — it references zones by ID.
# MAGIC `zone_lookup` is the **dimension** — one row per zone, the thing being
# MAGIC looked up.
# MAGIC
# MAGIC Same habit as Notebook 02: profile the lookup key before joining. If
# MAGIC `rows == distinct` and `nulls == 0`, `location_id` is a safe join key — no
# MAGIC fanout risk from the dimension side.

# COMMAND ----------

# DBTITLE 1,Load trip and zone_lookup, profile the lookup key
from pyspark.sql import functions as F

landing_root = "/Volumes/rideshare_dev/landing/source_files"
curated_root = "/Volumes/rideshare_dev/processed/output_files/curated"

zone_json_path = f"{landing_root}/zone_lookup/zone_lookup.json"
curated_trip_path = f"{curated_root}/trip"

zone_lookup_schema_ddl = """
location_id int,
borough_name string,
zone_name string,
service_zone string
"""

zone_lookup = (
    spark.read.format("json")  # noqa: F821
    .schema(zone_lookup_schema_ddl)
    .load(zone_json_path)
)

trip = spark.read.format("parquet").load(curated_trip_path)  # noqa: F821

print("trip rows:", trip.count())
print("zone_lookup rows:", zone_lookup.count())

zone_stats = zone_lookup.select(
    F.count(F.lit(1)).alias("rows"),
    F.countDistinct("location_id").alias("distinct"),
    F.sum(F.when(F.col("location_id").isNull(), 1).otherwise(0)).alias("nulls"),
).collect()[0]
print(
    f"zone_lookup profile: rows={zone_stats['rows']}, "
    f"distinct={zone_stats['distinct']}, nulls={zone_stats['nulls']}"
)
print("\u2192 unique, no NULLs \u2014 safe lookup key")

# docs/data/dataset-overview.md documents 22 zone_lookup rows (location_id
# 21-22 intentionally unreferenced by any trip). If the landed file has
# fewer rows, Section 3's unmatched-dimension-row demo has nothing to find.
expected_zone_rows = 22
if zone_stats["rows"] != expected_zone_rows:
    print(
        f"\n\u26a0 Expected {expected_zone_rows} zone_lookup rows per "
        f"docs/data/dataset-overview.md, found {zone_stats['rows']}. "
        "Section 3 below reports what the landed file actually contains."
    )

# COMMAND ----------

# DBTITLE 1,1. Repeated lookup join
# MAGIC %md
# MAGIC ## 1. Repeated lookup join — same table, two roles
# MAGIC
# MAGIC `zone_lookup` needs to join to `trip` **twice**: once to resolve
# MAGIC `pickup_location_id`, once for `dropoff_location_id`. Same table, same key
# MAGIC column (`location_id`), two different roles in the output.
# MAGIC
# MAGIC Both sides need `.alias()` (Notebook 01 Section 3.3) — Spark can't tell which
# MAGIC `zone_lookup` instance a column belongs to otherwise. Since `location_id`
# MAGIC (`zone_lookup`) and `pickup_location_id` / `dropoff_location_id` (`trip`)
# MAGIC have different names, this is a Boolean-form join.
# MAGIC
# MAGIC Predict: joining twice doesn't change the row count (still 106 — every trip
# MAGIC has exactly one pickup and one dropoff zone), but it does produce duplicate
# MAGIC column names (`borough_name`, `zone_name`, `service_zone` — twice each).

# COMMAND ----------

# DBTITLE 1,Join zone_lookup twice for pickup and dropoff
trip_a = trip.alias("t")
pickup_zone = zone_lookup.alias("pz")
dropoff_zone = zone_lookup.alias("dz")

trip_with_zones_raw = trip_a.join(
    pickup_zone,
    F.col("t.pickup_location_id") == F.col("pz.location_id"),
    "left",
).join(
    dropoff_zone,
    F.col("t.dropoff_location_id") == F.col("dz.location_id"),
    "left",
)

print(f"Row count: {trip_with_zones_raw.count()} (predicted 106 \u2014 unchanged)")
print("\nColumns after double join \u2014 duplicate names from both zone_lookup instances:")
print(trip_with_zones_raw.columns)

print("\nSame borough_name column, two different values per row (pickup vs dropoff):")
trip_with_zones_raw.select(
    F.col("t.trip_id"),
    F.col("pz.borough_name"),
    F.col("dz.borough_name"),
).show(5, truncate=False)

# COMMAND ----------

# DBTITLE 1,2. Explicit select and rename
# MAGIC %md
# MAGIC ## 2. Explicit select and rename — clean up before downstream use
# MAGIC
# MAGIC The double join works, but the column names are unusable: two
# MAGIC `borough_name` columns, two `zone_name` columns, two `service_zone` columns.
# MAGIC Any downstream `.select("borough_name")` throws an ambiguous column error.
# MAGIC
# MAGIC Fix: `.select()` with alias-qualified references, renaming each attribute to
# MAGIC its role — `pickup_borough`, `pickup_zone`, `dropoff_borough`,
# MAGIC `dropoff_zone`. This produces one clean, unambiguous schema ready for
# MAGIC aggregation or export.

# COMMAND ----------

# DBTITLE 1,Select and rename pickup/dropoff zone attributes
trip_with_zones = trip_with_zones_raw.select(
    F.col("t.trip_id"),
    F.col("t.service_type"),
    F.col("t.pickup_location_id"),
    F.col("pz.borough_name").alias("pickup_borough"),
    F.col("pz.zone_name").alias("pickup_zone"),
    F.col("t.dropoff_location_id"),
    F.col("dz.borough_name").alias("dropoff_borough"),
    F.col("dz.zone_name").alias("dropoff_zone"),
    F.col("t.trip_distance_miles"),
)

print("Clean schema \u2014 one column per attribute, no ambiguity:")
print(trip_with_zones.columns)
print(f"\nRow count: {trip_with_zones.count()}")
trip_with_zones.show(5, truncate=False)

# COMMAND ----------

# DBTITLE 1,3. Unmatched dimension rows
# MAGIC %md
# MAGIC ## 3. Unmatched dimension rows — 21–22 never appear... unless you look from the other side
# MAGIC
# MAGIC By design, `zone_lookup` has 22 rows but `trip.pickup_location_id` and
# MAGIC `trip.dropoff_location_id` only ever use values **1–20** across all 106
# MAGIC curated rows — `location_id` 21 (`Newark Airport`) and 22
# MAGIC (`Hoboken Terminal`) are intentionally unreferenced (see
# MAGIC [`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md)).
# MAGIC The code below computes the unreferenced set directly from the data
# MAGIC rather than hardcoding it, so it self-corrects if the landed file differs.
# MAGIC
# MAGIC Recall Notebook 01: the join type decides which unmatched rows survive.
# MAGIC
# MAGIC * **Left from `trip`** — `trip` drives, `zone_lookup` is looked up. Zones
# MAGIC   21–22 have no trip to attach to, so they simply never appear. No NULLs,
# MAGIC   no error — just absence.
# MAGIC * **Right or full from `zone_lookup`'s side** — zones 21–22 now survive
# MAGIC   with NULL trip columns, because the dimension rows are preserved even
# MAGIC   without a match.
# MAGIC
# MAGIC **Predict:** does a `trip`-driven left join ever produce a row for
# MAGIC `location_id` 21 or 22? Confirm, then flip the join to see them surface.

# COMMAND ----------

# DBTITLE 1,Confirm left join never surfaces unused zones
# Left join from trip's perspective — zones 21-22 should never appear
dropoff_left = trip.alias("t").join(
    zone_lookup.alias("dz"),
    F.col("t.dropoff_location_id") == F.col("dz.location_id"),
    "left",
)

referenced_dropoff_ids = [r[0] for r in trip.select("dropoff_location_id").distinct().collect()]
unreferenced_zones = zone_lookup.filter(~F.col("location_id").isin(referenced_dropoff_ids))
unreferenced_ids = [r[0] for r in unreferenced_zones.select("location_id").collect()]
print(f"zone_lookup location_id values no trip's dropoff ever uses: {unreferenced_ids}")

unused_zones_in_left = dropoff_left.filter(F.col("dz.location_id").isin(unreferenced_ids))
print(f"Rows matching those unreferenced zones in the left join: {unused_zones_in_left.count()}")
print("\u2192 Confirms: a trip-driven left join can never surface a zone no trip references.")

# COMMAND ----------

# DBTITLE 1,Right/full surfaces unused zones
# MAGIC %md
# MAGIC ### Right or full from the dimension side surfaces unused zones
# MAGIC
# MAGIC Flip the driving side (apply Notebook 01's left/right/full behavior): a
# MAGIC right or full outer join from `zone_lookup` keeps every dimension row,
# MAGIC matched or not. Any unreferenced zone now appears — with NULL for every
# MAGIC trip column, because no trip references it.

# COMMAND ----------

# DBTITLE 1,Right join surfaces zones 21 and 22 with NULL trip columns
# Right join from zone_lookup's side — unused zones survive with NULL trip columns
dropoff_right = trip.alias("t").join(
    zone_lookup.alias("dz"),
    F.col("t.dropoff_location_id") == F.col("dz.location_id"),
    "right",
)

print(f"Rows for unreferenced zones {unreferenced_ids} \u2014 trip columns are NULL:")
unmatched_zone_rows = dropoff_right.filter(F.col("dz.location_id").isin(unreferenced_ids))
unmatched_zone_rows.select(
    F.col("t.trip_id"),
    F.col("dz.location_id"),
    F.col("dz.zone_name"),
).show(truncate=False)

right_total = dropoff_right.count()
print(
    f"Right join total rows: {right_total} "
    f"({right_total - unmatched_zone_rows.count()} matched + "
    f"{unmatched_zone_rows.count()} unmatched zones)"
)

# COMMAND ----------

# DBTITLE 1,4. Broadcast
# MAGIC %md
# MAGIC ## 4. Broadcast — avoid shuffling the fact table for a 22-row dimension
# MAGIC
# MAGIC `zone_lookup` is tiny (22 rows). `trip` is comparatively large. Without a
# MAGIC hint, Spark may still shuffle both sides across the cluster to align
# MAGIC partitions for the join — wasted work when one side already fits entirely in
# MAGIC each executor's memory.
# MAGIC
# MAGIC `F.broadcast()` tells Spark to send the whole small table to every executor
# MAGIC instead, skipping the shuffle on the large side. This module's high-level AQE
# MAGIC awareness (README) means Spark may already do this automatically at this
# MAGIC tiny scale — the hint makes the intent explicit and guarantees the plan
# MAGIC regardless of size.
# MAGIC
# MAGIC **Note on Serverless compute:** Photon (Databricks' native vectorized engine)
# MAGIC is always on for Serverless compute and SQL warehouses — there's no toggle to
# MAGIC disable it, unlike classic clusters. Photon renames plan operators with a
# MAGIC `Photon` prefix, so the join below shows up as `PhotonBroadcastHashJoin`
# MAGIC rather than plain `BroadcastHashJoin`. Same broadcast optimization — just
# MAGIC Photon's vectorized implementation of it.

# COMMAND ----------

# DBTITLE 1,Join with a broadcast hint on zone_lookup
pickup_zone_broadcast = F.broadcast(zone_lookup.alias("pz"))

trip_broadcast_join = trip.alias("t").join(
    pickup_zone_broadcast,
    F.col("t.pickup_location_id") == F.col("pz.location_id"),
    "left",
)

print(f"Row count: {trip_broadcast_join.count()} (unchanged \u2014 broadcast only affects the plan)")

# COMMAND ----------

# DBTITLE 1,Inspect the plan for BroadcastHashJoin
print(
    "Look for a broadcast hash join below \u2014 on Serverless/Photon compute it's "
    "named PhotonBroadcastHashJoin; on classic non-Photon compute it's plain "
    "BroadcastHashJoin:\n"
)
trip_broadcast_join.explain("formatted")

# COMMAND ----------

# DBTITLE 1,Summary
# MAGIC %md
# MAGIC ## Summary — lookup joins, in one workflow
# MAGIC
# MAGIC 1. **Profile** the dimension key (`location_id`) — unique, no NULLs → safe
# MAGIC 2. **Join twice** with aliases when the same dimension plays two roles
# MAGIC    (pickup / dropoff) — Boolean form, since names differ
# MAGIC 3. **Select and rename** immediately after — don't leave ambiguous duplicate
# MAGIC    column names for downstream code to trip over
# MAGIC 4. **Choose the join direction deliberately** — left from the fact hides
# MAGIC    unreferenced dimension rows; right/full from the dimension surfaces them
# MAGIC 5. **Broadcast** small dimension tables explicitly with `F.broadcast()` and
# MAGIC    confirm `BroadcastHashJoin` in `.explain("formatted")`
# MAGIC
# MAGIC This repeated-lookup + explicit-select pattern is exactly what Notebook 07's
# MAGIC capstone reuses to build `trip_enriched` from multiple joins.
# MAGIC
# MAGIC **Next:** **`04 - Semi Joins and Anti Joins`**