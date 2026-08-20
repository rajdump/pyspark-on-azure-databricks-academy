# Databricks notebook source
# MAGIC %md
# MAGIC # 02 - Understanding the Delta Transaction Log
# MAGIC
# MAGIC Notebook 01 introduced the basic structure of a Delta table: Parquet data files together with a `_delta_log` directory.
# MAGIC
# MAGIC In this notebook, we create `fare_log_delta/` and examine how `_delta_log`
# MAGIC changes over time.
# MAGIC
# MAGIC Each successful table change creates a new commit in `_delta_log`, represented by a JSON file and identified by a new table version.
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC - Walk `_delta_log` commit by commit (`protocol` / `metaData` /
# MAGIC   `commitInfo` / `add` / `remove`)
# MAGIC - Reconstruct the current snapshot from `add` / `remove`
# MAGIC - Read `DESCRIBE HISTORY` on the Delta path
# MAGIC
# MAGIC **Reads:** none of the 100-row source files or teaching tables
# MAGIC (`trip_enriched`, KPIs, `curated/`). Do **not** touch
# MAGIC `fare_correction_parquet/` or `fare_correction_delta/`.
# MAGIC
# MAGIC **Writes:**
# MAGIC - `/Volumes/rideshare_dev/processed/output_files/practice/fare_log_delta/`
# MAGIC
# MAGIC No `saveAsTable`. Path `UPDATE` / `DELETE` on `` delta.`<path>` ``.
# MAGIC
# MAGIC **Prerequisites:** Module 9 notebooks `01`–`06`. Module 5
# MAGIC `01 - Unity Catalog Volumes and Data Landing.py` (catalog,
# MAGIC `processed.output_files`). Module 10 `01 - Why Delta Lake Exists.py`
# MAGIC (conceptual).
# MAGIC
# MAGIC This notebook does **not** teach `VERSION AS OF`, `TIMESTAMP AS OF`,
# MAGIC `RESTORE`, `OPTIMIZE`, `VACUUM`, checkpoints, or deletion vectors.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup
# MAGIC
# MAGIC Handmade dataset, reset `fare_log_delta/` so the notebook can re-run.
# MAGIC Deletion vectors **off**.

# COMMAND ----------

import json
from decimal import Decimal

from delta.tables import DeltaTable
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DecimalType,
    LongType,
    StringType,
    StructField,
    StructType,
)

delta_path = (
    "/Volumes/rideshare_dev/processed/output_files/practice/"
    "fare_log_delta/"
)
log_path = f"{delta_path}_delta_log"

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

dbutils.fs.rm(delta_path, True)

print(f"delta_path = {delta_path}")
print("rows in extract =", trips_extract.count())
display(trips_extract.orderBy("trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Version 0 — Create an empty Delta folder
# MAGIC
# MAGIC Write an empty Delta **folder** at the Volume path — no `saveAsTable` and no `catalog.schema.table` name, not a table registered in Unity Catalog.
# MAGIC
# MAGIC The first commit creates **Version 0** and records the initial information in `_delta_log`, including:
# MAGIC
# MAGIC * `protocol` — the Delta reader and writer requirements
# MAGIC * `metaData` — the table schema, configuration, and unique table ID
# MAGIC * `commitInfo` — information about the operation that created the table
# MAGIC
# MAGIC Because no rows have been written yet, there are normally **no Parquet data files**.
# MAGIC
# MAGIC **Table state at Version 0: 0 rows.**
# MAGIC

# COMMAND ----------

(
    DeltaTable.create(spark)
    .location(delta_path)
    .addColumn("trip_id", "BIGINT", nullable=False)
    .addColumn("service_type", "STRING", nullable=False)
    .addColumn("payment_method", "STRING", nullable=False)
    .addColumn("base_fare_amount", "DECIMAL(10,2)", nullable=False)
    .addColumn("tip_amount", "DECIMAL(10,2)", nullable=False)
    .property("delta.enableDeletionVectors", "false")
    .execute()
)

print("Delta folder after empty create:")
display(dbutils.fs.ls(delta_path))

print("_delta_log after empty create:")
display(dbutils.fs.ls(log_path))

delta_now = spark.read.format("delta").load(delta_path)
print(f"delta rows = {delta_now.count()} (expect 0)")

# COMMAND ----------

# MAGIC %md
# MAGIC You should see `_delta_log/` and typically **no** data `.parquet`. The
# MAGIC first commit file is `00000000000000000000.json` (version **0**).

# COMMAND ----------

v0_log = spark.read.json(f"{log_path}/00000000000000000000.json")
print("v0 columns:", v0_log.columns)
display(v0_log)

# COMMAND ----------

# MAGIC %md
# MAGIC Scan the column names: `protocol`, `metaData`, `commitInfo`. Each JSON
# MAGIC line is one action; most columns on a row are empty.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Version 1 — `add` trips 1001–1003
# MAGIC
# MAGIC Append **1001–1003** (1003 tip still **6.00**). Leave **1004** for the
# MAGIC next commit. The new JSON should include `add`. Delta read: **3** rows.

# COMMAND ----------

trips_1001_to_1003 = trips_extract.filter(
    F.col("trip_id").isin(1001, 1002, 1003)
)

(
    trips_1001_to_1003.write.format("delta")
    .mode("append")
    .save(delta_path)
)

delta_now = spark.read.format("delta").load(delta_path)
print(f"delta rows = {delta_now.count()} (expect 3)")
display(delta_now.orderBy("trip_id"))

print("_delta_log after v1:")
display(dbutils.fs.ls(log_path))

# COMMAND ----------

v1_log = spark.read.json(f"{log_path}/00000000000000000001.json")
print("v1 columns:", v1_log.columns)
display(v1_log)

# COMMAND ----------

# MAGIC %md
# MAGIC Look for `add` (the new Parquet file) and `commitInfo`. Trip **1003** is
# MAGIC still **6.00**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Version 2 — `add` trip 1004
# MAGIC
# MAGIC Second write adds **1004** only. Another `add`. Delta read: **4** rows.

# COMMAND ----------

trip_1004 = trips_extract.filter(F.col("trip_id") == 1004)

(
    trip_1004.write.format("delta")
    .mode("append")
    .save(delta_path)
)

delta_now = spark.read.format("delta").load(delta_path)
print(f"delta rows = {delta_now.count()} (expect 4)")
display(delta_now.orderBy("trip_id"))

print("_delta_log after v2:")
display(dbutils.fs.ls(log_path))

# COMMAND ----------

v2_log = spark.read.json(f"{log_path}/00000000000000000002.json")
print("v2 columns:", v2_log.columns)
display(v2_log)

# COMMAND ----------

# MAGIC %md
# MAGIC Four trips, two data writes. The snapshot now names every `add` from
# MAGIC versions **1** and **2**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Version 3 — `UPDATE` trip 1003 (`remove` + `add`)
# MAGIC
# MAGIC Operations needs trip **1003**'s tip changed from **6.00** to **10.00**.
# MAGIC Keep all **4** rows. Path `UPDATE` does not edit bytes inside the old
# MAGIC Parquet file: it `remove`s that file from the snapshot and `add`s a new
# MAGIC one. A leftover file may remain on disk.

# COMMAND ----------

spark.sql(
    f"""
    UPDATE delta.`{delta_path}`
    SET tip_amount = 10.00
    WHERE trip_id = 1003
    """
)

delta_now = spark.read.format("delta").load(delta_path)
print(f"delta rows = {delta_now.count()} (expect 4)")
display(delta_now.orderBy("trip_id"))

print("Delta data files after UPDATE (leftover files may remain):")
display(dbutils.fs.ls(delta_path))

print("_delta_log after v3:")
display(dbutils.fs.ls(log_path))

# COMMAND ----------

v3_log = spark.read.json(f"{log_path}/00000000000000000003.json")
print("v3 columns:", v3_log.columns)
display(v3_log)

# COMMAND ----------

# MAGIC %md
# MAGIC **4** rows; **1003** is **10.00**. The v3 JSON has both `remove` and
# MAGIC `add`. Extra `.parquet` files in `ls` are leftover, not extra rows.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Version 4 — `DELETE` trip 1002 (`remove` + `add`)
# MAGIC
# MAGIC Remove trip **1002** the same way: path `DELETE`, then `remove` + `add`
# MAGIC in the log. Delta read: **3** rows.

# COMMAND ----------

spark.sql(
    f"""
    DELETE FROM delta.`{delta_path}`
    WHERE trip_id = 1002
    """
)

delta_now = spark.read.format("delta").load(delta_path)
print(f"delta rows = {delta_now.count()} (expect 3)")
display(delta_now.orderBy("trip_id"))

print("Delta data files after DELETE (leftover files may remain):")
display(dbutils.fs.ls(delta_path))

print("_delta_log after v4:")
display(dbutils.fs.ls(log_path))

# COMMAND ----------

v4_log = spark.read.json(f"{log_path}/00000000000000000004.json")
print("v4 columns:", v4_log.columns)
display(v4_log)

# COMMAND ----------

# MAGIC %md
# MAGIC **3** rows: **1001**, **1003** (tip **10.00**), **1004**. Trip **1002**
# MAGIC is gone from the snapshot. v4 is again `remove` + `add`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Replay add/remove vs `ls`
# MAGIC
# MAGIC Walk every commit JSON. `add` puts a file in the snapshot; `remove`
# MAGIC takes it out. That set is the current table. `ls` still lists leftover
# MAGIC files.
# MAGIC
# MAGIC > **Warning:** Treating the folder like a Parquet dump (reading every
# MAGIC > leftover file) is not the same as a Delta read of the snapshot.

# COMMAND ----------

snapshot_files = set()
commit_files = sorted(
    file_info.path
    for file_info in dbutils.fs.ls(log_path)
    if file_info.path.endswith(".json")
)

for commit_file in commit_files:
    file_name = commit_file.rsplit("/", 1)[-1]
    version = int(file_name.replace(".json", ""))
    actions = []
    for line in dbutils.fs.head(commit_file).splitlines():
        if not line.strip():
            continue
        action = json.loads(line)
        if "add" in action:
            snapshot_files.add(action["add"]["path"])
            actions.append("add")
        elif "remove" in action:
            snapshot_files.discard(action["remove"]["path"])
            actions.append("remove")
        elif "protocol" in action:
            actions.append("protocol")
        elif "metaData" in action:
            actions.append("metaData")
        elif "commitInfo" in action:
            actions.append("commitInfo")
    print(f"v{version} actions: {actions}")

print("current snapshot files from add/remove:")
for name in sorted(snapshot_files):
    print(f"  {name}")
print(f"snapshot file count = {len(snapshot_files)}")

parquet_on_disk = [
    file_info.name
    for file_info in dbutils.fs.ls(delta_path)
    if file_info.name.endswith(".parquet")
]
print(f"parquet files on disk = {len(parquet_on_disk)}")
print("ls of the folder (ignore .crc and _delta_log):")
display(dbutils.fs.ls(delta_path))

# COMMAND ----------

# MAGIC %md
# MAGIC The snapshot file count can be **smaller** than the `.parquet` count on
# MAGIC disk. A Delta read still returns **3** rows — leftover files are not
# MAGIC extra trips.

# COMMAND ----------

# MAGIC %md
# MAGIC ## `DESCRIBE HISTORY`
# MAGIC
# MAGIC `DESCRIBE HISTORY` is the readable index of the same commits. Use
# MAGIC `spark.sql` because the name is a bound path. Stop here — do not query
# MAGIC a past version.

# COMMAND ----------

history = spark.sql(f"DESCRIBE HISTORY delta.`{delta_path}`")
display(history)

# COMMAND ----------

# MAGIC %md
# MAGIC You should see versions **0**–**4**. Reading `VERSION AS OF` /
# MAGIC `TIMESTAMP AS OF` and `RESTORE` is notebook 04.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - Version **0** is an empty Delta folder: `protocol` / `metaData` /
# MAGIC   `commitInfo`, typically no data `.parquet`, **0** rows
# MAGIC - Writes `add` files; `UPDATE` and `DELETE` record `remove` + `add`.
# MAGIC   Leftover Parquet files may stay on disk
# MAGIC - Replay `add` / `remove` to get the current snapshot; `ls` is not the
# MAGIC   snapshot
# MAGIC - `DESCRIBE HISTORY` lists those commits; time travel is next
# MAGIC
# MAGIC **Next:** `03 - Managed vs External Delta Tables` compares managed and
# MAGIC external Unity Catalog tables on a self-contained extract.