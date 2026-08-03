# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC
# MAGIC # 03 - Lookup Joins, Columns, and Broadcast
# MAGIC
# MAGIC ## The problem: location IDs aren't names — and a tiny lookup table shouldn't cost a big shuffle
# MAGIC
# MAGIC Every trip in `curated/trip` includes a `pickup_location_id` and a
# MAGIC `dropoff_location_id`, both of which are numeric codes rather than easily
# MAGIC recognizable place names. To present the trip information in a more
# MAGIC understandable format, you need to join the `zone_lookup` table on
# MAGIC `location_id`. This requires using the same 22-row lookup table twice: once
# MAGIC for the pickup location and once for the dropoff location.
# MAGIC
# MAGIC The size difference between tables is important. In our small example, the `zone_lookup` table has 22 rows, while the `trip` table contains 106 rows. However, in a production environment, the fact table may have millions of rows compared to a dimension table with only a few hundred. Joining these tables using the standard method could lead Spark to shuffle the larger `trip` table across the cluster to connect it with the smaller table that can fit in memory on each executor.
# MAGIC
# MAGIC A **broadcast join** addresses this issue by sending the entire smaller table to every executor, keeping only the large table in its original location. This notebook is designed to develop toward implementing a broadcast join once the repeated lookup pattern is firmly established.
# MAGIC
# MAGIC This notebook covers the following topics:
# MAGIC
# MAGIC 1. **Repeated Lookup Join** - This refers to joining the same dimension table twice using different aliases for distinct roles, such as pickup role and drop-off role.
# MAGIC    
# MAGIC 2. **Column Cleanup** - This involves resolving issues related to duplicate or ambiguous names that arise from the repeated lookup.
# MAGIC
# MAGIC 3. **Unmatched Dimension Rows** - In the `zone_lookup`, there are two zones (location_id 21–22) that no trip references. The behavior of left joins versus right or full outer joins reveals these discrepancies differently.
# MAGIC
# MAGIC 4. **Broadcasting** - This is about providing a hint to Spark to bypass the shuffle operation and verifying this decision in the physical plan.
# MAGIC
# MAGIC **Reads:** landing `zone_lookup` (JSON Lines, 22 rows); processed
# MAGIC `curated/trip` (Parquet, 106 rows). **No write.**
# MAGIC
# MAGIC **Prerequisites.** Module 7 **`01 - Grain, Join Syntax, and Unmatched Keys`**
# MAGIC and **`02 - Silent Join Failures and Validation`**; Module 6 (**`01`** through
# MAGIC **`04`**) so **`curated/trip`** exists. Boolean join syntax, `.alias`, key
# MAGIC profiling, and left/right/full unmatched-key behavior are applied here, not
# MAGIC re-taught. Landing Volume must contain **`zone_lookup`**.

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
# MAGIC Three signals decide which table plays which role:
# MAGIC
# MAGIC 1. **Grain and content** - This refers to what one row represents.
# MAGIC    `curated/trip`'s grain is one completed trip, a business event carrying
# MAGIC    measures you aggregate, such as `trip_distance_miles` and the duration
# MAGIC    columns. `zone_lookup`'s grain is one taxi zone, a descriptive entity
# MAGIC    with attributes you filter or group by, such as `borough_name` and
# MAGIC    `zone_name`, and it has no measures at all.
# MAGIC 2. **Foreign key direction** - This is about which table points at the
# MAGIC    other. `curated/trip` holds `pickup_location_id` and
# MAGIC    `dropoff_location_id`, both of which point at `zone_lookup.location_id`.
# MAGIC    Fact tables hold foreign keys into dimension tables, never the reverse.
# MAGIC 3. **Growth pattern** - This is about how each table changes over time.
# MAGIC    `curated/trip` grows with every new trip, while `zone_lookup` is static
# MAGIC    reference data, since the set of taxi zones doesn't change trip by trip.
# MAGIC
# MAGIC Based on these signals, `curated/trip` is the **fact** table because it
# MAGIC references zones by ID, and `zone_lookup` is the **dimension** because it
# MAGIC holds one row per zone, the thing being looked up.
# MAGIC
# MAGIC This follows the same habit as Notebook 02: profile the lookup key before
# MAGIC joining. If `rows == distinct` and `nulls == 0`, `location_id` is a safe
# MAGIC join key, with no fanout risk from the dimension side. 
# MAGIC
# MAGIC Only the dimension
# MAGIC key needs this check. Duplicates in `trip`'s foreign key columns
# MAGIC (`pickup_location_id`, `dropoff_location_id`) are normal, since many trips
# MAGIC share the same pickup or dropoff zone, so profiling the fact side would
# MAGIC flag expected behavior as if it were a problem.

# COMMAND ----------

# DBTITLE 1,Setup - load trip and zone_lookup
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

# COMMAND ----------

# DBTITLE 1,Setup - profile zone_lookup key
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

# COMMAND ----------

# DBTITLE 1,1. Repeated lookup join
# MAGIC %md
# MAGIC ## 1. Repeating a lookup join results in multiple shuffles
# MAGIC
# MAGIC `zone_lookup` joins to `trip` twice: once for `pickup_location_id`, once
# MAGIC for `dropoff_location_id`. Each join is a separate operation in the plan,
# MAGIC and by default each one triggers its own shuffle: Spark redistributes
# MAGIC rows across partitions so that matching keys land in the same partition
# MAGIC before it can align them.
# MAGIC
# MAGIC Shuffles are the most costly operations in Spark. During a shuffle, records are physically moved from their original partition to a new one based on the join key. This process requires writing intermediate data to disk and reading it back, resulting in significant disk I/O and serialization costs that occur regardless of the cluster size. Additionally, when executors span multiple nodes, there is a network transfer cost, but this is not the primary expense associated with a shuffle itself.
# MAGIC
# MAGIC Check the physical plan in the `explain()` output below. Spark will
# MAGIC default to a `SortMergeJoin` for each join, since that's the default
# MAGIC equi-join strategy when neither side qualifies for a broadcast — and
# MAGIC `SortMergeJoin` shuffles **both sides** of a join to co-partition matching
# MAGIC keys. With two joins, that's `Exchange` appearing four times, not two: one
# MAGIC for each side of each join.
# MAGIC
# MAGIC To fix this, use a broadcast join instead of a plain join — Section 4
# MAGIC covers it in detail.
# MAGIC
# MAGIC First, disable automatic broadcast so the plan below shows a shuffle join.
# MAGIC Section 4 forces broadcast with `F.broadcast()` while this setting stays
# MAGIC at `-1` (a hint still works when auto-broadcast is off).

# COMMAND ----------

# DBTITLE 1,1. Disable auto-broadcast for the shuffle demo
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)  # noqa: F821

# COMMAND ----------

# DBTITLE 1,1. Double lookup join without broadcast
t = trip.alias("t")
pz = zone_lookup.alias("pz")
dz = zone_lookup.alias("dz")

trip_with_zones = (
    t.join(
        pz,
        F.col("t.pickup_location_id") == F.col("pz.location_id"),
        "left",
    )
    .join(
        dz,
        F.col("t.dropoff_location_id") == F.col("dz.location_id"),
        "left",
    )
)

trip_with_zones.explain()

# COMMAND ----------

# DBTITLE 1,1. Show messy duplicate columns
trip_with_zones.show(1, truncate=False, vertical=True)

# COMMAND ----------

# DBTITLE 1,1b. Duplicate columns after the double join
# MAGIC %md
# MAGIC ## Duplicate columns after the double join
# MAGIC
# MAGIC Take a look at the row printed above: `location_id`, `borough_name`, `zone_name`, and `service_zone` each appear twice—once from the pickup join and once from the dropoff join. As a result, joining `zone_lookup` twice causes every column to appear twice in the output, which means we need to explicitly differentiate the pickup value from the dropoff value.
# MAGIC
# MAGIC This is expected behavior and not an error, but the data is not yet usable. The columns need to be selected and renamed to accurately reflect their business meaning. 
# MAGIC
# MAGIC For example, we should rename the columns to `pickup_borough` and `dropoff_borough` instead of having two identically named `borough_name` columns. Section 2 below will address this cleanup.

# COMMAND ----------

# DBTITLE 1,2. Explicit select and rename
# MAGIC %md
# MAGIC ## 2. Explicit select and rename — clean up before downstream use
# MAGIC
# MAGIC Any downstream `.select("borough_name")` throws an
# MAGIC ambiguous column error, because Spark cannot tell which one you mean.
# MAGIC
# MAGIC The fix is to use `.select()` with alias-qualified references, renaming
# MAGIC each attribute to reflect its role: `pickup_borough`, `pickup_zone`,
# MAGIC `dropoff_borough`, and `dropoff_zone`. This produces one clean, unambiguous
# MAGIC schema that is ready for aggregation or export.

# COMMAND ----------

# DBTITLE 1,2. Select and rename
trip_with_zones.select(
    F.col("t.trip_id"),
    F.col("t.service_type"),
    F.col("t.pickup_location_id"),
    F.col("pz.borough_name").alias("pickup_borough"),
    F.col("pz.zone_name").alias("pickup_zone"),
    F.col("t.dropoff_location_id"),
    F.col("dz.borough_name").alias("dropoff_borough"),
    F.col("dz.zone_name").alias("dropoff_zone"),
    F.col("t.trip_distance_miles"),
).show(1, truncate=False, vertical=True)

# COMMAND ----------

# DBTITLE 1,3. Unmatched dimension rows
# MAGIC %md
# MAGIC ## 3. Unmatched dimension rows — practice
# MAGIC
# MAGIC Work through a small concrete example before writing any code.
# MAGIC
# MAGIC **A few `trip` rows:**
# MAGIC
# MAGIC | trip_id | pickup_location_id | dropoff_location_id |
# MAGIC |---|---|---|
# MAGIC | 1 | 1 | 9 |
# MAGIC | 2 | 18 | 14 |
# MAGIC | 3 | 12 | 20 |
# MAGIC
# MAGIC **A few `zone_lookup` rows:**
# MAGIC
# MAGIC | location_id | borough_name | zone_name |
# MAGIC |---|---|---|
# MAGIC | 1 | Manhattan | Midtown East |
# MAGIC | 9 | Brooklyn | Downtown Brooklyn |
# MAGIC | 21 | New Jersey | Newark Airport |
# MAGIC | 22 | New Jersey | Hoboken Terminal |
# MAGIC
# MAGIC Notice `location_id` 21 and 22 never show up as anyone's
# MAGIC `pickup_location_id` or `dropoff_location_id` above. This holds across the
# MAGIC full dataset too: `zone_lookup` has 22 rows, but no trip among all 106
# MAGIC curated rows ever references `location_id` 21 (`Newark Airport`) or 22
# MAGIC (`Hoboken Terminal`) — see
# MAGIC [`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md).
# MAGIC
# MAGIC **Practice, using Notebook 01's left/right/full join behavior:**
# MAGIC
# MAGIC 1. Write a `trip`-driven **left join** to `zone_lookup` on `location_id`.
# MAGIC    Predict first: will `location_id` 21 or 22 ever appear in the result?
# MAGIC    Then run it and check.
# MAGIC 2. Flip it to a **right or full outer join** from `zone_lookup`'s side.
# MAGIC    Predict first: what changes? Then run it and inspect what the trip
# MAGIC    columns look like for `location_id` 21 and 22.

# COMMAND ----------

# DBTITLE 1,3. Practice - left join
# TODO (practice): write a trip-driven LEFT JOIN from `trip` to
# `zone_lookup`, matching `dropoff_location_id` to `location_id`.
# Use .alias() on both sides (Notebook 01 Section 3.3).
#
# Then check: does location_id 21 or 22 ever appear in the result?
# Filter your joined DataFrame down to just those two location_id values
# and count the rows — does the count match your prediction?

# COMMAND ----------

# DBTITLE 1,3b. Flip the driving side
# MAGIC %md
# MAGIC ### Now flip the driving side
# MAGIC
# MAGIC Before writing the next join, predict: which side needs to drive for an
# MAGIC unreferenced zone to have any chance of showing up at all?

# COMMAND ----------

# DBTITLE 1,3. Practice - right or full join
# TODO (practice): write a RIGHT (or FULL) outer join from `zone_lookup`'s
# side to `trip`, matching `dropoff_location_id` to `location_id`.
#
# Then check: filter the result down to location_id 21 and 22 — what do
# the trip columns (e.g. trip_id) look like for those rows? Compare the
# total row count to the left join from the cell above.

# COMMAND ----------

# DBTITLE 1,4. Broadcast
# MAGIC %md
# MAGIC ## 4. Broadcast — avoid shuffling the fact table for a 22-row dimension
# MAGIC
# MAGIC **Without a hint (Section 1):** With `autoBroadcastJoinThreshold = -1`,
# MAGIC Spark does not auto-broadcast. The double join used a shuffle strategy
# MAGIC (`SortMergeJoin` / `Exchange`s).
# MAGIC
# MAGIC **With a hint (below):** `F.broadcast()` forces a broadcast join even while
# MAGIC the threshold is still `-1`. Auto-broadcast stays off so the difference you
# MAGIC see in `.explain()` comes from the hint, not from the 10 MB default.
# MAGIC
# MAGIC **Note on Serverless compute:** Photon renames plan operators with a
# MAGIC `Photon` prefix, so you may see `PhotonBroadcastHashJoin` instead of
# MAGIC `BroadcastHashJoin`. Same optimization — Photon's vectorized form.

# COMMAND ----------

# DBTITLE 1,4. Double lookup join with F.broadcast
# Same double join as Section 1, but both zone_lookup sides use F.broadcast().
# Threshold is still -1 — the hint alone forces the broadcast plan.
t = trip.alias("t")
pz = F.broadcast(zone_lookup.alias("pz"))
dz = F.broadcast(zone_lookup.alias("dz"))

trip_broadcast_join = t.join(
    pz,
    F.col("t.pickup_location_id") == F.col("pz.location_id"),
    "left",
).join(
    dz,
    F.col("t.dropoff_location_id") == F.col("dz.location_id"),
    "left",
)

trip_broadcast_join.explain()

# COMMAND ----------

# DBTITLE 1,4. Restore auto-broadcast default
# Lesson complete — restore the usual 10 MB auto-broadcast threshold.
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "10485760")  # noqa: F821

# COMMAND ----------

# DBTITLE 1,Summary
# MAGIC %md
# MAGIC ## Summary — lookup joins, in one workflow
# MAGIC
# MAGIC 1. **Profile the Dimension Key** - Ensure that `location_id` is unique and has no NULL values before performing the join. This confirms that it is safe to use.
# MAGIC
# MAGIC 2. **Join Twice with Aliases** - When the same dimension serves two purposes, such as pickup and dropoff, use aliases to differentiate between them. The Boolean form is useful here since the column names will be different.
# MAGIC
# MAGIC 3. **Select and Rename Immediately** - This practice helps avoid ambiguous duplicate column names that might cause issues in downstream code.
# MAGIC
# MAGIC 4. **Choose Join Direction Deliberately** - A left join from the fact table will hide any unreferenced dimension rows, while a right or full join from the dimension will reveal them.
# MAGIC
# MAGIC 5. **Broadcast Small Dimension Tables Explicitly** - Use `F.broadcast()` to optimize performance with smaller dimension tables, and confirm this by checking for `BroadcastHashJoin` in `.explain()`.
# MAGIC
# MAGIC This pattern of repeated lookups and explicit selections is what Notebook 07's capstone uses to build `trip_enriched` through multiple joins.
# MAGIC
# MAGIC **Next:** **`04 - Semi Joins and Anti Joins`**