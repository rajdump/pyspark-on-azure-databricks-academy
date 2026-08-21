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
# MAGIC `OPTIMIZE`, `VACUUM`, Predictive Optimization, time travel, `RESTORE`,
# MAGIC grants (Module 12), or `CREATE TABLE` at a Volume path.

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

# Course external location — not a Volume path.
external_location_url = (
    spark.sql("DESCRIBE EXTERNAL LOCATION el_rideshare_dev")
    .select("url")
    .first()["url"]
    .rstrip("/")
)
# Subfolder only. Never CREATE at the external-location root.
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

# Reset: drop UC names, then delete leftover external files.
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
# MAGIC -- No LOCATION: Unity Catalog chooses the path. DV off on first CREATE.
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

# LOCATION makes this external. Same schema as managed. DV off.
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

# Same four rows in both, so later DROP / UNDROP / re-register can check data.
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
# MAGIC Look at `format` and `location` in `DESCRIBE DETAIL`. Both tables have
# MAGIC an `abfss://` path. For managed, Unity Catalog chose it. For external,
# MAGIC you chose it.

# COMMAND ----------

# Compare format and location.
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
# MAGIC This lab uses Delta for both tables. External tables can use other file formats; that is not
# MAGIC this lab.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Catalog metadata: MANAGED vs EXTERNAL, and storage_path.
# MAGIC SELECT table_name, table_type, storage_path
# MAGIC FROM rideshare_dev.information_schema.tables
# MAGIC WHERE table_schema = 'processed'
# MAGIC   AND table_name IN ('fare_managed_lab', 'fare_external_lab')
# MAGIC ORDER BY table_name

# COMMAND ----------

# MAGIC %md
# MAGIC `table_type` is `MANAGED` or `EXTERNAL`.
# MAGIC
# MAGIC You cannot list a managed table’s storage path in the same way that you can with an external table’s storage path. 
# MAGIC
# MAGIC The next cell succeeds because the external table uses a path that you explicitly provided through a Unity Catalog external location. However, the cell after that fails because Unity Catalog does not support path-based access to managed table storage, even if you are aware of the underlying URI. The error message about the path overlapping managed storage indicates that Unity Catalog is enforcing that boundary.
# MAGIC
# MAGIC This behaviour is by design. For managed tables, Unity Catalog controls the location of managed storage, so you interact with the data by referencing the table name using SQL or DataFrame APIs. In contrast, for external tables, although Unity Catalog still governs them, users with sufficient privileges can access the same data via their cloud storage URIs.

# COMMAND ----------

# Should succeed — you control this path.
display(spark.sql(f"LIST '{external_table_path}'"))

# COMMAND ----------

# Knowing the managed URI does not make LIST a supported file interface.
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
# MAGIC -- Removes the active UC name. Do not CREATE this name again before UNDROP.
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

# Folder while the external table still exists.
print("External folder before DROP:")
display(spark.sql(f"LIST '{external_table_path}'"))

# COMMAND ----------

# MAGIC %sql
# MAGIC -- UC name only. Files at LOCATION stay.
# MAGIC DROP TABLE rideshare_dev.processed.fare_external_lab

# COMMAND ----------

# Same folder should still be here — DROP did not delete the files.
print("External folder after DROP:")
display(spark.sql(f"LIST '{external_table_path}'"))

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Public Preview. Use the most recently dropped fare_external_lab row.
# MAGIC SHOW TABLES DROPPED IN rideshare_dev.processed

# COMMAND ----------

# MAGIC %md
# MAGIC Find the **most recently dropped** `fare_external_lab` row.
# MAGIC
# MAGIC | | Managed | External |
# MAGIC |---|---|---|
# MAGIC | UC metadata after `DROP` | recoverable for 7 days | recoverable for 7 days |
# MAGIC | Files after `DROP` | retained by UC for recovery | remain at `external_table_path` |
# MAGIC | After recovery window | UC deletes the files | files remain until you delete them |
# MAGIC
# MAGIC `UNDROP TABLE` can recover either table type during the 7-day recovery window.

# COMMAND ----------

# MAGIC %md
# MAGIC ## UNDROP
# MAGIC
# MAGIC `UNDROP TABLE` can restore both managed and external tables within the
# MAGIC 7-day recovery window.
# MAGIC
# MAGIC - **Managed:** restores the UC table and retained data.
# MAGIC - **External:** restores the UC table over files that already remain at
# MAGIC   the external path.

# COMMAND ----------

# Managed: relation + files UC kept. External: relation over files that stayed.
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
# MAGIC
# MAGIC Drop the external table again, then create a new UC table over the
# MAGIC existing ADLS folder.
# MAGIC
# MAGIC This is **re-registration**, not `UNDROP`.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Drop the name only. Next cell re-registers the surviving folder.
# MAGIC DROP TABLE rideshare_dev.processed.fare_external_lab

# COMMAND ----------

# New UC name over the existing folder. Not UNDROP. No column list.
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
# MAGIC **4 rows** are available again in both tables.
# MAGIC
# MAGIC | | Managed | External |
# MAGIC |---|---|---|
# MAGIC | `UNDROP` | Restores the dropped table and retained data | Restores the dropped table over existing files |
# MAGIC | Re-register | Not applicable here | Creates a new UC registration over the existing Delta folder |
# MAGIC
# MAGIC `UNDROP` restores the dropped UC table. Re-registering creates a **new**
# MAGIC UC table over the existing external files.

# COMMAND ----------

# MAGIC %md
# MAGIC ## When to use which
# MAGIC
# MAGIC ### Use an external table when
# MAGIC
# MAGIC Choose an **external table** when you need control of the storage path.
# MAGIC
# MAGIC Typical cases:
# MAGIC
# MAGIC * data already exists at a specific ADLS path
# MAGIC * another system needs direct access to the same files
# MAGIC * the data format is not supported as a managed table
# MAGIC * `DROP TABLE` must leave the underlying files untouched
# MAGIC
# MAGIC You provide the `LOCATION`. Unity Catalog governs the table, while the
# MAGIC files remain at the storage path you control.
# MAGIC
# MAGIC ### Use a managed table when
# MAGIC
# MAGIC Choose a **managed table** for most new tables created in Databricks.
# MAGIC
# MAGIC Unity Catalog chooses the storage location and Databricks manages the
# MAGIC table storage for you.
# MAGIC
# MAGIC | Architecture area                       | Recommended default |
# MAGIC | --------------------------------------- | ------------------- |
# MAGIC | Landing / raw source files              | External Volume     |
# MAGIC | Bronze, Silver, and Gold tables         | Managed table       |
# MAGIC | Existing or shared data at a fixed path | External table      |
# MAGIC
# MAGIC Bronze, Silver, and Gold are **data layers**, not table types.
# MAGIC **Bronze does not mean external.**
# MAGIC
# MAGIC > **External table trade-off:** You keep control of the storage path, but
# MAGIC > managed-only capabilities such as **Predictive Optimization** are not
# MAGIC > available.
# MAGIC
# MAGIC Module 5 `landing` and `processed` are course storage areas, not
# MAGIC medallion layers.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC * Both managed and external tables are governed by Unity Catalog.
# MAGIC * Use **managed tables** by default for most new Databricks tables.
# MAGIC * Use **external tables** when you need to control or preserve a
# MAGIC   specific storage path.
# MAGIC * `DROP TABLE` removes the active UC registration. Managed files follow
# MAGIC   the UC-managed recovery lifecycle; external files remain at their
# MAGIC   storage path.
# MAGIC * `UNDROP` can restore either table type during the 7-day recovery
# MAGIC   window.
# MAGIC * Re-registering an external folder creates a **new UC registration**
# MAGIC   over the existing files.
# MAGIC
# MAGIC **Next:** `04 - Delta Time Travel and Restore`