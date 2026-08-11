# Databricks notebook source
# DBTITLE 1,Introduction
# MAGIC %md
# MAGIC
# MAGIC # 07 - Top-N per Group and Sampling
# MAGIC
# MAGIC Keeping the "top N" rows sounds simple, but two decisions matter:
# MAGIC
# MAGIC 1. **How should ties at the cutoff be handled?**
# MAGIC 2. **Where should NULL values appear in the sort order?**
# MAGIC
# MAGIC This notebook extends the ranking pattern from Notebook **05**, then
# MAGIC introduces reproducible sampling with `sample`, `sampleBy`, and
# MAGIC `randomSplit`.
# MAGIC
# MAGIC ## What this notebook teaches
# MAGIC
# MAGIC | Section | Concept | Why it matters |
# MAGIC |---|---|---|
# MAGIC | 1 | Top-N + output grain | Rank, filter, then verify what one row represents |
# MAGIC | 2 | Ties at the cutoff | Choose `row_number` vs `rank`; add a secondary sort when needed |
# MAGIC | 3 | NULL sort placement | Control where NULLs appear in window `orderBy` |
# MAGIC | 4 | Sampling | Draw reproducible subsets with a seed |
# MAGIC | Exercise | Top tips per borough | Combine Top-N with explicit tip NULL placement |
# MAGIC
# MAGIC **Reads:** `rideshare_dev.processed.trip_enriched` (106 rows) and
# MAGIC `rideshare_dev.processed.trip_driver_assignment` (100 rows). **No writes.**
# MAGIC
# MAGIC **Prerequisites:** Module 8 Notebooks **01–06**, especially
# MAGIC **`05 - Window Functions Fundamentals`** and
# MAGIC **`06 - Running Totals and Lag and Lead`**.

# COMMAND ----------

# DBTITLE 1,Setup — load both managed tables
# MAGIC %md
# MAGIC ## Setup — load both managed tables
# MAGIC
# MAGIC Shared schemas and inherited NULL details remain in Module 8
# MAGIC **`01 - GroupBy and Basic Aggregations`** and `docs/data/dataset-overview.md`.
# MAGIC
# MAGIC | DataFrame | Rows | Used for |
# MAGIC |---|---:|---|
# MAGIC | `trip_driver_assignment` | 100 | Sections 1–2 (Top-N); Section 4c |
# MAGIC | `trip_enriched` | 106 | Section 3 (NULL sort); Section 4a–4b; exercise |
# MAGIC
# MAGIC Notebook **05** introduced Top-2 per driver. Here we extend the same pattern
# MAGIC to Top-3 and verify how filtering changes the output grain.

# COMMAND ----------

# DBTITLE 1,Load and verify the managed tables
from pyspark.sql import functions as F
from pyspark.sql.window import Window

trip_enriched_table = "rideshare_dev.processed.trip_enriched"
trip_driver_assignment_table = "rideshare_dev.processed.trip_driver_assignment"

trip_enriched = spark.table(trip_enriched_table)  # noqa: F821
trip_driver_assignment = spark.table(trip_driver_assignment_table)  # noqa: F821

trip_enriched_rows = trip_enriched.count()
trip_driver_assignment_rows = trip_driver_assignment.count()

print(f"trip_enriched: {trip_enriched_rows} rows")
print(f"trip_driver_assignment: {trip_driver_assignment_rows} rows")

# COMMAND ----------

# DBTITLE 1,How does Top-N change the output grain?
# MAGIC %md
# MAGIC ## 1. How does Top-N change the output grain?
# MAGIC
# MAGIC A mileage review needs each driver's longest trips.
# MAGIC
# MAGIC Before applying the Top-N filter, compare what one row represents before and
# MAGIC after the filter:
# MAGIC
# MAGIC | Stage | Grain |
# MAGIC |---|---|
# MAGIC | Input | **100** rows — one per (`driver_id`, `trip_id`) |
# MAGIC | After Top-3 filter | **36** rows — three trips per driver in this dataset |
# MAGIC
# MAGIC In Notebook **05**, Top-2 used `distance_row_number <= 2` (100 → **24**).
# MAGIC Here the same `row_number` + `filter` pattern keeps the **top 3** longest
# MAGIC trips per driver. Ranking keeps every row until `filter()` changes the
# MAGIC grain.

# COMMAND ----------

# DBTITLE 1,Rank distance within each driver
distance_rank_window = Window.partitionBy("driver_id").orderBy(
    F.col("trip_distance_miles").desc(),
)

driver_ranked = trip_driver_assignment.withColumn(
    "distance_row_number",
    F.row_number().over(distance_rank_window),
)

# COMMAND ----------

# DBTITLE 1,Keep top 3 trips per driver
top3_trips_per_driver = driver_ranked.filter(
    F.col("distance_row_number") <= 3,
)

# COMMAND ----------

# DBTITLE 1,Inspect top 3 trips and confirm grain
top3_trips_per_driver.select(
    "driver_id",
    "driver_name",
    "trip_id",
    "trip_distance_miles",
    "distance_row_number",  # derived column
).orderBy(
    "driver_id",
    "distance_row_number",
).show(40, truncate=False)

top3_trips_per_driver_rows = top3_trips_per_driver.count()
print(f"Top-3 result: {top3_trips_per_driver_rows} rows (12 drivers × 3 trips)")

# COMMAND ----------

# DBTITLE 1,Summarize miles among each driver's top 3 trips
# MAGIC %md
# MAGIC After Top-N keeps the rows you need, a later aggregate can summarize them.
# MAGIC Here: total miles among each driver's three longest trips — still no write.

# COMMAND ----------

# DBTITLE 1,Total miles in the Top-3 set per driver
top3_trips_per_driver.groupBy("driver_id").agg(
    F.sum("trip_distance_miles").alias("top3_total_miles"),
).orderBy("driver_id").show(truncate=False)

# COMMAND ----------

# DBTITLE 1,What happens when rows tie at the Top-N cutoff?
# MAGIC %md
# MAGIC ## 2. What happens when rows tie at the Top-N cutoff?
# MAGIC
# MAGIC Exact-N eligibility and "keep every trip tied at the cutoff" are different
# MAGIC policies — for driver **D010**, trips **22** and **79** both have
# MAGIC **8.81 miles**.
# MAGIC
# MAGIC Both trips are tied at the Top-4 cutoff. Because `row_number` assigns a
# MAGIC unique position to every row, only one can receive position 4. If the
# MAGIC requirement is to keep all rows tied at the cutoff, use a different ranking
# MAGIC rule.
# MAGIC
# MAGIC | Cutoff | What it keeps |
# MAGIC |---|---|
# MAGIC | `row_number <= N` | **At most N** rows per group; ties do not increase the row count |
# MAGIC | `rank <= N` | All rows with rank **N or lower**; a tie at the cutoff can keep **more than N** rows |  # noqa: E501
# MAGIC
# MAGIC Add a secondary sort key when an exact-N result must be
# MAGIC **deterministic for the same input**.

# COMMAND ----------

# DBTITLE 1,Add row_number and rank on distance only
policy_distance_window = Window.partitionBy("driver_id").orderBy(
    F.col("trip_distance_miles").desc(),
)

driver_policy_ranked = trip_driver_assignment.withColumn(
    "distance_row_number",
    F.row_number().over(policy_distance_window),
).withColumn(
    "distance_rank",
    F.rank().over(policy_distance_window),
)

# COMMAND ----------

# DBTITLE 1,Inspect D010 before the cutoff
driver_policy_ranked.filter(
    F.col("driver_id") == "D010",
).select(
    "driver_id",
    "trip_id",
    "trip_distance_miles",
    "distance_row_number",  # derived column
    "distance_rank",  # derived column
).orderBy(
    "distance_row_number",
).show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Compare row_number <= 4 vs rank <= 4 on D010
d010_row_number_top4 = driver_policy_ranked.filter(
    (F.col("driver_id") == "D010")
    & (F.col("distance_row_number") <= 4),
)
d010_rank_top4 = driver_policy_ranked.filter(
    (F.col("driver_id") == "D010")
    & (F.col("distance_rank") <= 4),
)

d010_row_number_top4_rows = d010_row_number_top4.count()
d010_rank_top4_rows = d010_rank_top4.count()

print(
    f"D010: row_number keeps {d010_row_number_top4_rows} rows, "
    f"rank keeps {d010_rank_top4_rows} — the tie adds an extra row"
)

d010_rank_top4.select(
    "driver_id",
    "trip_id",
    "trip_distance_miles",
    "distance_row_number",  # derived column
    "distance_rank",  # derived column
).orderBy(
    "distance_row_number",
).show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Compare both cutoffs across all 12 drivers
fleet_row_number_top4 = driver_policy_ranked.filter(
    F.col("distance_row_number") <= 4,
)
fleet_rank_top4 = driver_policy_ranked.filter(
    F.col("distance_rank") <= 4,
)

fleet_row_number_top4_rows = fleet_row_number_top4.count()
fleet_rank_top4_rows = fleet_rank_top4.count()

print(
    f"fleet totals — row_number <= 4: {fleet_row_number_top4_rows}; "
    f"rank <= 4: {fleet_rank_top4_rows}"
)

print("rows kept per driver — row_number <= 4:")
fleet_row_number_top4.groupBy("driver_id").count().orderBy("driver_id").show(
    truncate=False,
)

print("rows kept per driver — rank <= 4:")
fleet_rank_top4.groupBy("driver_id").count().orderBy("driver_id").show(
    truncate=False,
)

# COMMAND ----------

# DBTITLE 1,Make the Top-N cut deterministic with a secondary sort
stable_distance_window = Window.partitionBy("driver_id").orderBy(
    F.col("trip_distance_miles").desc(),
    F.col("trip_id").asc(),
)

driver_stable_ranked = trip_driver_assignment.withColumn(
    "distance_row_number",
    F.row_number().over(stable_distance_window),
)

driver_stable_ranked.filter(
    F.col("driver_id") == "D010",
).select(
    "driver_id",
    "trip_id",
    "trip_distance_miles",
    "distance_row_number",  # derived column
).orderBy(
    "distance_row_number",
).show(truncate=False)

# COMMAND ----------

# DBTITLE 1,What to remember when trips tie at Top-N
# MAGIC %md
# MAGIC ### What to remember when trips tie at Top-N
# MAGIC
# MAGIC First decide how many rows to keep. For D010 at Top-4 (trips 22 and 79 both
# MAGIC 8.81 miles):
# MAGIC
# MAGIC - `row_number <= 4` keeps exactly **4** rows. Only one of the tied trips
# MAGIC   receives the final slot.
# MAGIC - `rank <= 4` keeps every row ranked **4**. Because both trips share rank
# MAGIC   **4**, both are kept so that the result can contain more than **4** rows.
# MAGIC
# MAGIC Across the full fleet, `row_number <= 4` always returns **48** rows
# MAGIC (12 drivers × 4 trips). With `rank <= 4`, the row count increases whenever
# MAGIC multiple trips are tied at the cutoff rank.
# MAGIC
# MAGIC If the requirement is exactly N rows per driver, add a secondary sort such
# MAGIC as `trip_id.asc()`. This gives Spark an explicit and repeatable way to
# MAGIC choose between tied rows for the same input.
# MAGIC
# MAGIC The secondary sort does not preserve both tied trips. It only decides which
# MAGIC one gets the final slot.

# COMMAND ----------

# DBTITLE 1,How does NULL placement affect window ordering?
# MAGIC %md
# MAGIC ## 3. How does NULL placement affect window ordering?
# MAGIC
# MAGIC Undated trips and missing tips change who appears first in an ordered
# MAGIC borough report.
# MAGIC
# MAGIC Adding `row_number` changes the order position, not the number of rows:
# MAGIC the result still has **106 trips**.
# MAGIC
# MAGIC Spark's default NULL placement depends on sort direction. Column helpers
# MAGIC make the intended placement explicit:
# MAGIC
# MAGIC | Method | Non-NULL order | NULLs |
# MAGIC |---|---|---|
# MAGIC | `asc()` | smallest → largest | **first** (default) |
# MAGIC | `asc_nulls_last()` | smallest → largest | **last** |
# MAGIC | `desc()` | largest → smallest | **last** (default) |
# MAGIC | `desc_nulls_first()` | largest → smallest | **first** |
# MAGIC | `desc_nulls_last()` | largest → smallest | **last** (same as `desc()`) |
# MAGIC
# MAGIC Prefer the helper when NULL placement matters so the order is visible in
# MAGIC the code.

# COMMAND ----------

# DBTITLE 1,Default asc — NULLs first on trip_date
default_date_window = Window.partitionBy("pickup_borough").orderBy(
    F.col("trip_date").asc(),
)

trip_date_default_ordered = trip_enriched.withColumn(
    "date_row_number",
    F.row_number().over(default_date_window),
)

trip_date_default_ordered.filter(
    F.col("pickup_borough") == "Manhattan",
).select(
    "pickup_borough",
    "trip_id",
    "trip_date",
    "date_row_number",  # derived column
).orderBy(
    "date_row_number",
).show(15, truncate=False)

# COMMAND ----------

# DBTITLE 1,asc_nulls_last — dated trips first
nulls_last_date_window = Window.partitionBy("pickup_borough").orderBy(
    F.col("trip_date").asc_nulls_last(),
)

trip_date_nulls_last = trip_enriched.withColumn(
    "date_row_number",
    F.row_number().over(nulls_last_date_window),
)

trip_date_nulls_last.filter(
    F.col("pickup_borough") == "Manhattan",
).select(
    "pickup_borough",
    "trip_id",
    "trip_date",
    "date_row_number",  # derived column
).orderBy(
    "date_row_number",
).show(15, truncate=False)

# COMMAND ----------

# DBTITLE 1,Interpret the ascending NULL fix
# MAGIC %md
# MAGIC Manhattan undated trips are **101**, **104**, and **106**.
# MAGIC
# MAGIC - Default `asc()`: those trips appear among the **earliest**
# MAGIC   `date_row_number` values.
# MAGIC - `asc_nulls_last()`: the same trips appear at the **end** of the borough
# MAGIC   ordering.

# COMMAND ----------

# DBTITLE 1,What changes with desc_nulls_first?
# MAGIC %md
# MAGIC ### What changes with `desc_nulls_first()`?
# MAGIC
# MAGIC Trip **106** has NULL `tip_amount` in Manhattan (trip **103**'s NULL tip
# MAGIC is in Queens).
# MAGIC
# MAGIC The next cell compares two descending tip orders:
# MAGIC
# MAGIC - Default `desc()`: NULL tips stay **last**.
# MAGIC - `desc_nulls_first()`: NULL tips move **first**, ahead of known tip values.
# MAGIC
# MAGIC For a "highest known tip" ranking, prefer `desc_nulls_last()` so NULL tips
# MAGIC do not win early ranks. That matches Spark's descending default — write
# MAGIC `desc_nulls_last()` explicitly when the placement matters.

# COMMAND ----------

# DBTITLE 1,Compare tip desc default vs desc_nulls_first — Manhattan
default_tip_window = Window.partitionBy("pickup_borough").orderBy(
    F.col("tip_amount").desc(),
)
nulls_first_tip_window = Window.partitionBy("pickup_borough").orderBy(
    F.col("tip_amount").desc_nulls_first(),
)

tip_desc_default = trip_enriched.withColumn(
    "tip_row_number",
    F.row_number().over(default_tip_window),
)
tip_desc_nulls_first = trip_enriched.withColumn(
    "tip_row_number",
    F.row_number().over(nulls_first_tip_window),
)

print("default tip desc (NULLs last) — Manhattan:")
tip_desc_default.filter(
    F.col("pickup_borough") == "Manhattan",
).select(
    "pickup_borough",
    "trip_id",
    "tip_amount",
    "tip_row_number",  # derived column
).orderBy(
    "tip_row_number",
).show(10, truncate=False)

print("tip desc_nulls_first — Manhattan:")
tip_desc_nulls_first.filter(
    F.col("pickup_borough") == "Manhattan",
).select(
    "pickup_borough",
    "trip_id",
    "tip_amount",
    "tip_row_number",  # derived column
).orderBy(
    "tip_row_number",
).show(10, truncate=False)

# COMMAND ----------

# DBTITLE 1,Section 3 rule of thumb
# MAGIC %md
# MAGIC **Rule of thumb:** if an ordered column can contain NULLs, name the NULL
# MAGIC placement in `orderBy` (`asc_nulls_last()`, `desc_nulls_last()`, and so
# MAGIC on) so the intended ordering is visible in the code.

# COMMAND ----------

# DBTITLE 1,How do we draw a reproducible subset of rows?
# MAGIC %md
# MAGIC ## 4. How do we draw a reproducible subset of rows?
# MAGIC
# MAGIC Before running a fare audit across all trips, you may need a smaller
# MAGIC reproducible subset to spot-check. Spark provides three useful patterns:
# MAGIC
# MAGIC | API | Use it when |
# MAGIC |---|---|
# MAGIC | `sample` | Draw an approximate fraction of the DataFrame |
# MAGIC | `sampleBy` | Draw different fractions for different key values |
# MAGIC | `randomSplit` | Divide the DataFrame into reproducible subsets |
# MAGIC
# MAGIC Pass a `seed` when you need the sampling operation to be reproducible for
# MAGIC the same input.
# MAGIC
# MAGIC ### 4a. `sample` — approximate fraction and seed reproducibility

# COMMAND ----------

# DBTITLE 1,sample with seed 42
trip_sample_a = trip_enriched.sample(
    withReplacement=False,
    fraction=0.2,
    seed=42,
)

trip_sample_a_rows = trip_sample_a.count()

print(f"sample (~0.2, seed=42): {trip_sample_a_rows} rows from {trip_enriched_rows}")

trip_sample_a.select(
    "trip_id",
    "service_type",
    "pickup_borough",
    "trip_distance_miles",
).show(5, truncate=False)

# COMMAND ----------

# DBTITLE 1,Verify the same seed reproduces the sample
trip_sample_b = trip_enriched.sample(
    withReplacement=False,
    fraction=0.2,
    seed=42,
)

trip_sample_b_rows = trip_sample_b.count()

print(f"Sample B: {trip_sample_b_rows} rows (same as A)")

only_in_a = (
    trip_sample_a.select("trip_id")
    .subtract(trip_sample_b.select("trip_id"))
    .count()
)
only_in_b = (
    trip_sample_b.select("trip_id")
    .subtract(trip_sample_a.select("trip_id"))
    .count()
)
print(
    f"Trips only in A: {only_in_a}, only in B: {only_in_b} — "
    "same seed produces identical subsets"
)

# COMMAND ----------

# DBTITLE 1,Which service types get sampled?
# MAGIC %md
# MAGIC ### 4b. Which service types get sampled?
# MAGIC
# MAGIC `sampleBy` draws within each key using the fractions you supply. Keys
# MAGIC **omitted** from the map are not sampled (fraction 0).
# MAGIC
# MAGIC The map below includes four service types and **omits** `UNKNOWN`, so the
# MAGIC sample should contain **0** UNKNOWN rows even though the full table has 2.

# COMMAND ----------

# DBTITLE 1,Draw stratified sample without UNKNOWN
service_type_fractions = {
    "STANDARD": 0.2,
    "SHARED": 0.2,
    "PREMIUM": 0.2,
    "XL": 0.2,
}

trip_sample_by_service = trip_enriched.sampleBy(
    "service_type",
    fractions=service_type_fractions,
    seed=42,
)

print("full counts by service_type:")
trip_enriched.groupBy("service_type").count().orderBy("service_type").show(
    truncate=False,
)

print("sampleBy counts by service_type (UNKNOWN omitted from fractions):")
trip_sample_by_service.groupBy("service_type").count().orderBy("service_type").show(
    truncate=False,
)

# COMMAND ----------

# DBTITLE 1,How do we split rows into seeded subsets?
# MAGIC %md
# MAGIC ### 4c. How do we split rows into seeded subsets?
# MAGIC
# MAGIC Use `trip_driver_assignment` here (100 rows, no undated-trip NULLs) so an
# MAGIC approximately 70/30 split is easy to read. Sections 4a–4b used
# MAGIC `trip_enriched` because stratification keyed on `service_type` there.
# MAGIC
# MAGIC `[0.7, 0.3]` requests an approximately 70/30 split. The exact row counts
# MAGIC can vary. With the same input and seed, the split is reproducible.

# COMMAND ----------

# DBTITLE 1,Split assignment rows ~70/30 with seed 42
subset_a, subset_b = trip_driver_assignment.randomSplit(
    [0.7, 0.3],
    seed=42,
)

subset_a_rows = subset_a.count()
subset_b_rows = subset_b.count()

print(f"\nsubset A ({subset_a_rows} rows):")
subset_a.select(
    "driver_id",
    "trip_id",
    "trip_distance_miles",
).show(5, truncate=False)

print(f"subset B ({subset_b_rows} rows):")
subset_b.select(
    "driver_id",
    "trip_id",
    "trip_distance_miles",
).show(5, truncate=False)

# COMMAND ----------

# DBTITLE 1,Exercise — Top tips per borough with explicit NULL placement
# MAGIC %md
# MAGIC ## Exercise — Top tips per borough with explicit NULL placement
# MAGIC
# MAGIC Which 2 trips per `pickup_borough` had the highest known tips?
# MAGIC
# MAGIC Repeat the Top-N pattern on `trip_enriched`, partitioned by
# MAGIC `pickup_borough`.
# MAGIC
# MAGIC Trips **103** and **106** have NULL `tip_amount`. Order tips with
# MAGIC `desc_nulls_last()` so known tip values are ranked before NULLs.
# MAGIC For descending order, NULLs last is already Spark's default. Use
# MAGIC `desc_nulls_last()` explicitly here so the intended NULL placement is
# MAGIC visible in the code.
# MAGIC
# MAGIC | Column | Pattern |
# MAGIC |---|---|
# MAGIC | `tip_row_number` | `row_number` within `pickup_borough`, tip descending, NULLs last |
# MAGIC | filter | keep `tip_row_number <= 2` |
# MAGIC
# MAGIC Predict the output row count, then build, verify, and inspect.

# COMMAND ----------

# DBTITLE 1,Exercise — Build, verify, and inspect
predicted_top_tip_rows = None  # TODO: replace with your prediction

# TODO: Window.partitionBy("pickup_borough").orderBy(
#     F.col("tip_amount").desc_nulls_last(),
# )
tip_rank_window = None

trip_tip_ranked = trip_enriched.withColumn(
    "tip_row_number",
    F.row_number().over(tip_rank_window),
)

top2_tips_per_borough = trip_tip_ranked.filter(
    F.col("tip_row_number") <= 2,
)

actual_top_tip_rows = top2_tips_per_borough.count()
top_tip_match = "✓" if predicted_top_tip_rows == actual_top_tip_rows else "✗"
print(
    f"{top_tip_match} top-2 tip rows:",
    f"predicted={predicted_top_tip_rows},",
    f"actual={actual_top_tip_rows}",
)

top2_tips_per_borough.select(
    "pickup_borough",
    "trip_id",
    "tip_amount",
    "tip_row_number",  # derived column
).orderBy(
    "pickup_borough",
    "tip_row_number",
).show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Summary
# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC | Idea | Takeaway |
# MAGIC |---|---|
# MAGIC | Top-N | Rank first, then filter |
# MAGIC | Ties | `row_number` limits rows; `rank` can keep extra tied rows |
# MAGIC | Deterministic order | Add a secondary sort key when ties must be resolved |
# MAGIC | NULL ordering | Specify NULL placement when the sort column can be NULL |
# MAGIC | Sampling | Use a seed when reproducibility matters |
# MAGIC
# MAGIC **Next:** Module 8 **`08 - Build KPI Tables`** — write three `kpi_*`
# MAGIC Parquet outputs for Module 9.
