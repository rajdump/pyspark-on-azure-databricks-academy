# Databricks notebook source
# MAGIC %md
# MAGIC # 06 - End-to-End SQL Pipeline and Parity Inspection
# MAGIC
# MAGIC Phase II synthesis: rebuild the three Module 8 KPI contracts in Spark SQL
# MAGIC and **inspect** whether they match the managed tables.
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC - Rebuild daily, zone, and driver KPI contracts with `spark.sql(...)`
# MAGIC - Inspect parity with counts and bidirectional `exceptAll` diffs
# MAGIC - Treat dual-API habit as same logic, different API — automate asserts in
# MAGIC   Module 17 (no Python `assert` here)
# MAGIC
# MAGIC **No exercise** — the three parity inspections are the synthesis.
# MAGIC
# MAGIC **Callbacks:** Module 8 `08 - Build KPI Tables` (+ Module 8 README
# MAGIC contracts); `04 - SQL Windows and QUALIFY` (`DENSE_RANK`);
# MAGIC `05 - CTEs and Parameterized SQL` (CTE agg).
# MAGIC
# MAGIC **Reads:** `trip_enriched` (106), `trip_driver_assignment` (100),
# MAGIC `kpi_daily_trip_summary` (14), `kpi_zone_performance` (20),
# MAGIC `kpi_driver_productivity` (12). **No writes.**
# MAGIC
# MAGIC **Cell-type lock:** KPI rebuilds use **Python** cells with `spark.sql(...)`
# MAGIC so results are assignable DataFrames (`%sql` cannot bind to a variable).
# MAGIC
# MAGIC **Prerequisites:** Module 9 notebooks 01–05; Module 8 KPI writes.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup — load sources + KPI tables
# MAGIC
# MAGIC Parity inspection = print row counts, then `display` rows that appear in
# MAGIC only one side via `exceptAll`. Empty diffs mean the SQL rebuild matches.
# MAGIC Automated asserts → Module 17.

# COMMAND ----------

trip_enriched = spark.table("rideshare_dev.processed.trip_enriched")  # noqa: F821
trip_driver_assignment = spark.table(  # noqa: F821
    "rideshare_dev.processed.trip_driver_assignment"
)
kpi_daily = spark.table(  # noqa: F821
    "rideshare_dev.processed.kpi_daily_trip_summary"
)
kpi_zone = spark.table(  # noqa: F821
    "rideshare_dev.processed.kpi_zone_performance"
)
kpi_driver = spark.table(  # noqa: F821
    "rideshare_dev.processed.kpi_driver_productivity"
)

print(f"trip_enriched: {trip_enriched.count()} rows")  # expect 106
print(
    f"trip_driver_assignment: {trip_driver_assignment.count()} rows"
)  # expect 100
print(f"kpi_daily_trip_summary: {kpi_daily.count()} rows")  # expect 14
print(f"kpi_zone_performance: {kpi_zone.count()} rows")  # expect 20
print(f"kpi_driver_productivity: {kpi_driver.count()} rows")  # expect 12

# COMMAND ----------

def show_parity(sql_df, table_df, cols, label):
    """Print counts and display bidirectional exceptAll diffs — no assert."""
    a = sql_df.select(cols)
    b = table_df.select(cols)
    only_in_sql = a.exceptAll(b)
    only_in_kpi = b.exceptAll(a)
    print(f"{label}: sql_rows={a.count()} kpi_rows={b.count()}")
    print(
        f"{label}: only_in_sql={only_in_sql.count()} "
        f"only_in_kpi={only_in_kpi.count()}"
    )
    display(only_in_sql.limit(20))  # noqa: F821
    display(only_in_kpi.limit(20))  # noqa: F821


print("show_parity helper ready")

# COMMAND ----------

# MAGIC %md
# MAGIC ## KPI 1 — Daily (layered)
# MAGIC
# MAGIC **Contract:** one row per `trip_date`; drop NULL dates (trips **101–106**).
# MAGIC Callback: Module 8 `08 - Build KPI Tables`.
# MAGIC
# MAGIC Aggregates: `trip_count`, `total_base_fare`, `total_tip`,
# MAGIC `total_driver_payout`, `total_distance_miles`, `avg_distance_miles`,
# MAGIC `avg_ride_duration_mins`.

# COMMAND ----------

dated_trips = spark.sql(  # noqa: F821
    """
    SELECT *
    FROM rideshare_dev.processed.trip_enriched
    WHERE trip_date IS NOT NULL
    """
)
print(f"dated_trips: {dated_trips.count()} rows")  # expect 100

# COMMAND ----------

sql_daily = spark.sql(  # noqa: F821
    """
    SELECT
      trip_date,
      COUNT(*) AS trip_count,
      SUM(base_fare_amount) AS total_base_fare,
      SUM(tip_amount) AS total_tip,
      SUM(driver_payout_amount) AS total_driver_payout,
      SUM(trip_distance_miles) AS total_distance_miles,
      ROUND(AVG(trip_distance_miles), 2) AS avg_distance_miles,
      ROUND(AVG(ride_duration_mins), 2) AS avg_ride_duration_mins
    FROM rideshare_dev.processed.trip_enriched
    WHERE trip_date IS NOT NULL
    GROUP BY trip_date
    """
)
print(f"sql_daily: {sql_daily.count()} rows")  # expect 14
sql_daily.orderBy("trip_date").show(14, truncate=False)

# COMMAND ----------

daily_cols = [
    "trip_date",
    "trip_count",
    "total_base_fare",
    "total_tip",
    "total_driver_payout",
    "total_distance_miles",
    "avg_distance_miles",
    "avg_ride_duration_mins",
]
show_parity(sql_daily, kpi_daily, daily_cols, "daily")

# COMMAND ----------

# MAGIC %md
# MAGIC ## KPI 2 — Zone (layered)
# MAGIC
# MAGIC **Contract:** one row per (`pickup_borough`, `pickup_zone`); all **106**
# MAGIC trips. `tip_percent_of_base` is a ratio of **sums**, only when
# MAGIC `SUM(base_fare_amount) > 0` — else NULL.

# COMMAND ----------

zone_grain = spark.sql(  # noqa: F821
    """
    SELECT
      pickup_borough,
      pickup_zone,
      MAX(pickup_location_id) AS pickup_location_id,
      COUNT(*) AS trip_count,
      SUM(base_fare_amount) AS total_base_fare,
      SUM(tip_amount) AS total_tip
    FROM rideshare_dev.processed.trip_enriched
    GROUP BY pickup_borough, pickup_zone
    ORDER BY pickup_borough, pickup_zone
    """
)
print(f"zone_grain: {zone_grain.count()} rows")  # expect 20
zone_grain.show(20, truncate=False)

# COMMAND ----------

sql_zone = spark.sql(  # noqa: F821
    """
    SELECT
      pickup_borough,
      pickup_zone,
      MAX(pickup_location_id) AS pickup_location_id,
      COUNT(*) AS trip_count,
      SUM(base_fare_amount) AS total_base_fare,
      SUM(tip_amount) AS total_tip,
      CASE
        WHEN SUM(base_fare_amount) > 0
        THEN ROUND(100 * SUM(tip_amount) / SUM(base_fare_amount), 1)
      END AS tip_percent_of_base,
      ROUND(AVG(trip_distance_miles), 2) AS avg_distance_miles,
      ROUND(AVG(ride_duration_mins), 2) AS avg_ride_duration_mins
    FROM rideshare_dev.processed.trip_enriched
    GROUP BY pickup_borough, pickup_zone
    """
)
print(f"sql_zone: {sql_zone.count()} rows")  # expect 20
sql_zone.orderBy("pickup_borough", "pickup_zone").show(20, truncate=False)

# COMMAND ----------

zone_cols = [
    "pickup_borough",
    "pickup_zone",
    "pickup_location_id",
    "trip_count",
    "total_base_fare",
    "total_tip",
    "tip_percent_of_base",
    "avg_distance_miles",
    "avg_ride_duration_mins",
]
show_parity(sql_zone, kpi_zone, zone_cols, "zone")

# COMMAND ----------

# MAGIC %md
# MAGIC ## KPI 3 — Driver (layered)
# MAGIC
# MAGIC **Contract:** one row per `driver_id` from `trip_driver_assignment`, then
# MAGIC fleet-wide `DENSE_RANK` by `total_distance_miles` desc.
# MAGIC Reuse CTE habit from `05 - CTEs and Parameterized SQL` and ranking from
# MAGIC `04 - SQL Windows and QUALIFY`.

# COMMAND ----------

driver_agg_sql = spark.sql(  # noqa: F821
    """
    WITH driver_agg AS (
      SELECT
        driver_id,
        MAX(driver_name) AS driver_name,
        COUNT(*) AS trip_count,
        SUM(trip_distance_miles) AS total_distance_miles,
        ROUND(AVG(ride_duration_mins), 2) AS avg_ride_duration_mins,
        SORT_ARRAY(COLLECT_SET(service_type)) AS unique_service_types
      FROM rideshare_dev.processed.trip_driver_assignment
      GROUP BY driver_id
    )
    SELECT *
    FROM driver_agg
    ORDER BY driver_id
    """
)
print(f"driver_agg: {driver_agg_sql.count()} rows")  # expect 12
driver_agg_sql.show(12, truncate=False)

# COMMAND ----------

sql_driver = spark.sql(  # noqa: F821
    """
    WITH driver_agg AS (
      SELECT
        driver_id,
        MAX(driver_name) AS driver_name,
        COUNT(*) AS trip_count,
        SUM(trip_distance_miles) AS total_distance_miles,
        ROUND(AVG(ride_duration_mins), 2) AS avg_ride_duration_mins,
        SORT_ARRAY(COLLECT_SET(service_type)) AS unique_service_types
      FROM rideshare_dev.processed.trip_driver_assignment
      GROUP BY driver_id
    )
    SELECT
      driver_id,
      driver_name,
      trip_count,
      total_distance_miles,
      avg_ride_duration_mins,
      unique_service_types,
      DENSE_RANK() OVER (
        ORDER BY total_distance_miles DESC
      ) AS distance_dense_rank
    FROM driver_agg
    """
)
print(f"sql_driver: {sql_driver.count()} rows")  # expect 12
sql_driver.orderBy("distance_dense_rank", "driver_id").show(
    12, truncate=False
)

# COMMAND ----------

driver_cols = [
    "driver_id",
    "driver_name",
    "trip_count",
    "total_distance_miles",
    "avg_ride_duration_mins",
    "unique_service_types",
    "distance_dense_rank",
]
show_parity(sql_driver, kpi_driver, driver_cols, "driver")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Takeaway
# MAGIC
# MAGIC When all three inspections show matching counts and empty diffs, the SQL
# MAGIC rebuild matches the DataFrame KPIs — **same logic, different API**.
# MAGIC
# MAGIC Inspect in notebooks and jobs; **automate asserts in Module 17**.
# MAGIC
# MAGIC Phase II is complete → Module 10 Delta Lake.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary — Module 9
# MAGIC
# MAGIC | Notebook | Focus |
# MAGIC |---|---|
# MAGIC | `01 - Dual API Foundations and When to Choose` | Bridges + row-level `CASE` |
# MAGIC | `02 - SQL Joins, Aggregations, and Filtering` | JOIN, `GROUP BY`, `HAVING` |
# MAGIC | `03 - SQL Pivot, Unpivot, and Sampling` | Reshape + `TABLESAMPLE` |
# MAGIC | `04 - SQL Windows and QUALIFY` | Ranking, running totals, `LAG` |
# MAGIC | `05 - CTEs and Parameterized SQL` | Named steps + `:params` |
# MAGIC | `06 - End-to-End SQL Pipeline and Parity Inspection` | KPI rebuild + inspect |
# MAGIC
# MAGIC **Next:** Module 10 — Delta Lake.
