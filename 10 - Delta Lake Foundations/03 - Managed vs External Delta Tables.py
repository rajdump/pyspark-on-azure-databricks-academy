# Databricks notebook source
# MAGIC %md
# MAGIC # 03 - Managed vs External Delta Tables
# MAGIC
# MAGIC Both managed and external tables are governed by Unity Catalog (UC).
# MAGIC The key differences are who controls the table’s physical storage and
# MAGIC which capabilities Databricks manages automatically.
# MAGIC
# MAGIC
# MAGIC ```text
# MAGIC Managed table
# MAGIC UC table ──► UC chooses the storage location
# MAGIC              Databricks manages the table storage and
# MAGIC              supported automatic optimizations
# MAGIC
# MAGIC External table
# MAGIC UC table ──► You choose the storage location
# MAGIC              You manage the storage path and files
# MAGIC ```
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC - Create the same empty Delta table as managed and as external, then load
# MAGIC   the same four rows
# MAGIC - Compare table type and storage location (`DESCRIBE DETAIL`,
# MAGIC   `information_schema`, `LIST`)
# MAGIC - `DROP` both, `UNDROP` both, and re-register the external folder
# MAGIC
# MAGIC **Reads:** none of the 100-row source files or teaching tables
# MAGIC (`trip_enriched`, KPIs, `curated/`)
# MAGIC
# MAGIC **Writes:**
# MAGIC - `rideshare_dev.processed.fare_managed_lab`
# MAGIC - `rideshare_dev.processed.fare_external_lab` at
# MAGIC   `{url}/external-tables/fare_external_lab`
# MAGIC
# MAGIC **Prerequisites:** Module 9 notebooks `01`–`06`. Module 5
# MAGIC `01 - Unity Catalog Volumes and Data Landing.py` (catalog,
# MAGIC `el_rideshare_dev`, `processed`).
# MAGIC
# MAGIC This notebook does **not** teach `UPDATE`, `DESCRIBE HISTORY`,
# MAGIC `OPTIMIZE`, `VACUUM`, time travel, `RESTORE`, grants (Module 12), or
# MAGIC `CREATE TABLE` at a Volume path.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup
# MAGIC Handmade extract. Drop both lab names. Delete the external folder.
# MAGIC Do not insert yet.

# COMMAND ----------

from decimal import Decimal

from pyspark.sql.types import (
    DecimalType,
    LongType,
    StringType,
    StructField,
    StructType,
)

managed_table = "rideshare_dev.processed.fare_managed_lab"
external_table = "rideshare_dev.processed.fare_external_lab"

external_location_url = (
    spark.sql("DESCRIBE EXTERNAL LOCATION el_rideshare_dev")
    .select("url")
    .first()["url"]
    .rstrip("/")
)
external_table_path = (
    f"{external_location_url}/external-tables/fare_external_lab"
)

extract_schema = StructType(
    [
        StructField("trip_id", LongType(), False),
        StructField("service_type", StringType(), False),
        StructField("payment_method", StringType(), False),
        StructField("base_fare_amount", DecimalType(10, 2), False),
        StructField("tip_amount", DecimalType(10, 2), False),
    ]
)

trips_extract = spark.createDataFrame(
    [
        (1001, "STANDARD", "card", Decimal("20.00"), Decimal("3.00")),
        (1002, "SHARED", "cash", Decimal("15.00"), Decimal("0.00")),
        (1003, "PREMIUM", "card", Decimal("40.00"), Decimal("6.00")),
        (1004, "STANDARD", "wallet", Decimal("25.00"), Decimal("2.50")),
    ],
    schema=extract_schema,
)
trips_extract.createOrReplaceTempView("trips_extract")

spark.sql(f"DROP TABLE IF EXISTS {managed_table}")
spark.sql(f"DROP TABLE IF EXISTS {external_table}")
dbutils.fs.rm(external_table_path, True)

print(f"managed_table = {managed_table}")
print(f"external_table = {external_table}")
print(f"external_table_path = {external_table_path}")
print("rows in extract =", trips_extract.count())
display(trips_extract.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Empty managed and external tables
# MAGIC Managed: no `LOCATION`. Unity Catalog chooses the path.
# MAGIC External: you choose an `abfss://` path, not `/Volumes/`.
# MAGIC **0** rows until the next section.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE rideshare_dev.processed.fare_managed_lab (
# MAGIC   trip_id BIGINT,
# MAGIC   service_type STRING,
# MAGIC   payment_method STRING,
# MAGIC   base_fare_amount DECIMAL(10, 2),
# MAGIC   tip_amount DECIMAL(10, 2)
# MAGIC )
# MAGIC USING DELTA
# MAGIC TBLPROPERTIES ('delta.enableDeletionVectors' = 'false')

# COMMAND ----------

spark.sql(
    f"""
    CREATE TABLE {external_table} (
      trip_id BIGINT,
      service_type STRING,
      payment_method STRING,
      base_fare_amount DECIMAL(10, 2),
      tip_amount DECIMAL(10, 2)
    )
    USING DELTA
    LOCATION '{external_table_path}'
    TBLPROPERTIES ('delta.enableDeletionVectors' = 'false')
    """
)

print(f"managed rows = {spark.table(managed_table).count()} (expect 0)")
print(f"external rows = {spark.table(external_table).count()} (expect 0)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Insert the extract
# MAGIC Same four rows into both tables. Trip **1003** tip stays **6.00**.
# MAGIC This load is so `DROP` / `UNDROP` / re-register can prove **data**
# MAGIC survived — not a DML lesson.

# COMMAND ----------

spark.sql(f"INSERT INTO {managed_table} SELECT * FROM trips_extract")
spark.sql(f"INSERT INTO {external_table} SELECT * FROM trips_extract")

managed_df = spark.table(managed_table)
external_df = spark.table(external_table)
print(f"managed rows = {managed_df.count()} (expect 4)")
print(f"external rows = {external_df.count()} (expect 4)")
display(managed_df.orderBy("trip_id"))
display(external_df.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Where do the files live?
# MAGIC `LIST` on the external path should succeed. `LIST` on the managed
# MAGIC table's cloud URI is expected to fail. Knowing a managed location
# MAGIC does not make it a supported file interface.

# COMMAND ----------

display(spark.sql(f"DESCRIBE DETAIL {managed_table}"))
display(spark.sql(f"DESCRIBE DETAIL {external_table}"))

# COMMAND ----------

# MAGIC %md
# MAGIC Look at `format` and `location`.
# MAGIC
# MAGIC | | Managed | External |
# MAGIC |---|---|---|
# MAGIC | Registered in Unity Catalog | yes | yes |
# MAGIC | Format | Delta | Delta |
# MAGIC | Who chooses the location | Unity Catalog | you specify |
# MAGIC | Explicit `LOCATION` | no | yes |
# MAGIC
# MAGIC This lab uses Delta for both so path and `DROP` behavior are the only
# MAGIC variables. External tables can use other file formats; that is not
# MAGIC this lab.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT table_name, table_type, storage_path
# MAGIC FROM rideshare_dev.information_schema.tables
# MAGIC WHERE table_schema = 'processed'
# MAGIC   AND table_name IN ('fare_managed_lab', 'fare_external_lab')
# MAGIC ORDER BY table_name

# COMMAND ----------

# MAGIC %md
# MAGIC `table_type` is `MANAGED` or `EXTERNAL`. Next: `LIST` the external
# MAGIC folder, then try the managed URI.

# COMMAND ----------

display(spark.sql(f"LIST '{external_table_path}'"))

# COMMAND ----------

managed_uri = (
    spark.sql(f"DESCRIBE DETAIL {managed_table}")
    .select("location")
    .first()["location"]
)
print(f"managed_uri = {managed_uri}")
spark.sql(f"LIST '{managed_uri}'")  # Expected: AnalysisException

# COMMAND ----------

# MAGIC %md
# MAGIC Classroom `LIST` is not a managed-file browser. The failure does
# MAGIC **not** mean the files are gone.
# MAGIC
# MAGIC | | Managed | External |
# MAGIC |---|---|---|
# MAGIC | `table_type` | `MANAGED` | `EXTERNAL` |
# MAGIC | `storage_path` | UC-chosen path | `external_table_path` |
# MAGIC | `LIST` of that path | expected to fail | succeeds |

# COMMAND ----------

# MAGIC %md
# MAGIC ## DROP TABLE
# MAGIC Does `DROP` delete the files? Do not wait 7 days. Do not `PURGE`.
# MAGIC
# MAGIC `DROP TABLE` removes the **active Unity Catalog table registration**.
# MAGIC The table is no longer queryable. For **7 days**, `UNDROP` can recover
# MAGIC **either** type — that is catalog recovery, not "the table is gone
# MAGIC forever."
# MAGIC
# MAGIC That 7-day window is **not** why external files remain.

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP TABLE rideshare_dev.processed.fare_managed_lab;
# MAGIC SHOW TABLES DROPPED IN rideshare_dev.processed

# COMMAND ----------

# MAGIC %md
# MAGIC Find the **most recently dropped** `fare_managed_lab` row
# MAGIC (`deletedAt`). If this notebook has been run before, older rows with
# MAGIC the same name can appear.
# MAGIC
# MAGIC > **Note:** `SHOW TABLES DROPPED` is Public Preview.
# MAGIC
# MAGIC Do not `CREATE` this managed name again before `UNDROP`.

# COMMAND ----------

print("External folder before DROP:")
display(spark.sql(f"LIST '{external_table_path}'"))

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP TABLE rideshare_dev.processed.fare_external_lab

# COMMAND ----------

print("External folder after DROP:")
display(spark.sql(f"LIST '{external_table_path}'"))

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW TABLES DROPPED IN rideshare_dev.processed

# COMMAND ----------

# MAGIC %md
# MAGIC Find the **most recently dropped** `fare_external_lab` row. The
# MAGIC **active UC registration** is gone; the ADLS folder is still there
# MAGIC (data files plus `_delta_log/`).
# MAGIC
# MAGIC Managed: DROP → active registration removed → UC retains files →
# MAGIC UNDROP for 7 days → then UC deletes those files
# MAGIC
# MAGIC External: DROP → active registration removed → UNDROP for 7 days
# MAGIC + files remain at the ADLS path independently
# MAGIC
# MAGIC The external files do **not** remain because of the 7-day `UNDROP`
# MAGIC window. They remain because the external table does not give Unity
# MAGIC Catalog control of deleting those files.
# MAGIC
# MAGIC | | Managed | External |
# MAGIC |---|---|---|
# MAGIC | Active UC registration after `DROP` | removed | removed |
# MAGIC | Files after `DROP` | UC retains them for recovery (not a `LIST` browser) | remain at `external_table_path` |
# MAGIC | Why files remain | 7-day recovery, then UC deletes them | you control those files |

# COMMAND ----------

# MAGIC %md
# MAGIC ## UNDROP
# MAGIC Works for both types. For external, the location and credential must
# MAGIC still exist. `UNDROP TABLE name` restores the most recently dropped
# MAGIC matching relation. Expect **4** rows each.
# MAGIC
# MAGIC - **Managed:** restores the UC relation **and** the data UC retained
# MAGIC   for recovery.
# MAGIC - **External:** restores the UC relation over files that **already
# MAGIC   remained** at the path. The files were never removed. Do not say
# MAGIC   that external `UNDROP` "recovers the files."

# COMMAND ----------

spark.sql(f"UNDROP TABLE {managed_table}")
spark.sql(f"UNDROP TABLE {external_table}")

managed_df = spark.table(managed_table)
external_df = spark.table(external_table)
print(f"managed rows = {managed_df.count()} (expect 4)")
print(f"external rows = {external_df.count()} (expect 4)")
display(managed_df.orderBy("trip_id"))
display(external_df.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Re-register the external folder
# MAGIC Leave the managed table undropped. This is **not** `UNDROP`. Drop the
# MAGIC external name again, then register a new UC table over the folder
# MAGIC that is still on ADLS.

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP TABLE rideshare_dev.processed.fare_external_lab

# COMMAND ----------

spark.sql(
    f"""
    CREATE TABLE {external_table}
    USING DELTA
    LOCATION '{external_table_path}'
    """
)

external_df = spark.table(external_table)
print(f"external rows = {external_df.count()} (expect 4)")
display(external_df.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC **4** rows. External files were never removed from the path.
# MAGIC
# MAGIC | | Managed | External |
# MAGIC |---|---|---|
# MAGIC | `UNDROP` | 4 rows: relation + files UC retained | 4 rows: relation over files that stayed |
# MAGIC | 7-day window | catalog recovery; then UC deletes managed files | catalog recovery only; files stay because you control them |
# MAGIC | Re-register | do not `CREATE` the name before `UNDROP` | **new** UC registration over the surviving folder; 4 rows |
# MAGIC
# MAGIC `UNDROP` restores the previously dropped UC relation. Re-registering
# MAGIC creates a **new** UC registration over the existing external Delta
# MAGIC folder.

# COMMAND ----------

# MAGIC %md
# MAGIC ## When to use which
# MAGIC
# MAGIC ### Use an external table when
# MAGIC
# MAGIC Choose an **external table** when the storage path must stay under your
# MAGIC control.
# MAGIC
# MAGIC Typical cases:
# MAGIC
# MAGIC - data already exists at a specific ADLS path and should stay there
# MAGIC - another system needs direct access to the same files
# MAGIC - the table uses a file format that is not supported as a managed table
# MAGIC - `DROP TABLE` must leave the underlying files untouched
# MAGIC
# MAGIC You provide the `LOCATION`. Unity Catalog still governs the table, but
# MAGIC the files remain at the storage path you manage.
# MAGIC
# MAGIC ### Use a managed table when
# MAGIC
# MAGIC Choose a **managed table** for most new tables created in Databricks.
# MAGIC
# MAGIC Unity Catalog chooses the storage location and Databricks manages the
# MAGIC table's storage lifecycle and platform optimizations.
# MAGIC
# MAGIC For a typical lakehouse architecture:
# MAGIC
# MAGIC | Area | Recommended default |
# MAGIC |---|---|
# MAGIC | Landing / raw source files | External Volume |
# MAGIC | New Bronze, Silver, and Gold tables | Managed table |
# MAGIC | Existing or shared data that must stay at a specific path | External table |
# MAGIC
# MAGIC Bronze, Silver, and Gold describe **data layers**, not managed or
# MAGIC external table types.
# MAGIC
# MAGIC **Bronze does not mean external.**
# MAGIC
# MAGIC > **Note:** What do you give up with an external table?
# MAGIC >
# MAGIC > External tables remain governed by Unity Catalog, but some capabilities
# MAGIC > available to managed tables are reduced or unavailable:
# MAGIC >
# MAGIC > - automatic Databricks optimizations are more limited
# MAGIC > - Predictive Optimization is not supported
# MAGIC >
# MAGIC > Use external tables because you need control of the storage path,
# MAGIC > not simply because the data belongs to a particular medallion layer.
# MAGIC
# MAGIC Module 5 `landing` and `processed` are course storage areas; they are not
# MAGIC medallion layers.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - Both managed and external tables are governed by Unity Catalog
# MAGIC - Managed is the default for most new Databricks tables
# MAGIC - External is for cases where you must control or preserve a specific
# MAGIC   storage path
# MAGIC - `DROP TABLE` removes the active UC registration; external files remain,
# MAGIC   while managed files follow the UC-managed recovery and deletion lifecycle
# MAGIC - `UNDROP` can recover either table type during the 7-day recovery window
# MAGIC
# MAGIC **Next:** `04 - Delta Time Travel and Restore`