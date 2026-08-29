# Databricks notebook source
# MAGIC %md
# MAGIC # 04 - ACID and Optimistic Concurrency
# MAGIC
# MAGIC Two jobs might correct fares in `fare_maint_lab` at the same time — a
# MAGIC card-trip tip and a wallet-trip tip. Production pipelines need those
# MAGIC writes to stay **transactionally correct**: one commit must not mix
# MAGIC partial work from two writers.
# MAGIC
# MAGIC This notebook shows how Delta uses **ACID** transactions and
# MAGIC **optimistic concurrency**. A reader sees a snapshot. A writer checks
# MAGIC that snapshot at commit time. Overlapping writers on the same files
# MAGIC conflict; the losing writer retries.
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC - Create `fare_maint_lab` with extract columns and insert trips **1001–1004**
# MAGIC - `UPDATE` trip **1003** tip **6.00 → 10.00** and inspect `DESCRIBE HISTORY`
# MAGIC - Explain optimistic concurrency: snapshot reads, version checks, and
# MAGIC   overlapping-write conflicts
# MAGIC - Show one overlapping-write conflict, a retry, and **4** remaining rows
# MAGIC
# MAGIC **Reads:** none of the 100-row source files or teaching tables
# MAGIC (`trip_enriched`, KPIs, `curated/`)
# MAGIC
# MAGIC **Writes:**
# MAGIC - `rideshare_dev.processed.fare_maint_lab` at `{url}/external-tables/fare_maint_lab`
# MAGIC
# MAGIC **Prerequisites:** Module 10 notebooks `01`–`04`. Module 5
# MAGIC `01 - Unity Catalog Volumes and Data Landing.py` (catalog,
# MAGIC `el_rideshare_dev`, `processed`).
# MAGIC
# MAGIC This notebook does **not** teach isolation levels, checkpoints, protocol
# MAGIC versions, or `OPTIMIZE`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup
# MAGIC
# MAGIC Drop `rideshare_dev.processed.fare_maint_lab` and delete leftover files at
# MAGIC `{url}/external-tables/fare_maint_lab`. `DROP TABLE` does not delete those
# MAGIC files.

# COMMAND ----------

import threading

from delta.exceptions import DeltaConcurrentModificationException

lab_table = "rideshare_dev.processed.fare_maint_lab"

external_location_url = (
    spark.sql("DESCRIBE EXTERNAL LOCATION el_rideshare_dev")
    .select("url")
    .first()["url"]
    .rstrip("/")
)
lab_path = f"{external_location_url}/external-tables/fare_maint_lab"

spark.sql(f"DROP TABLE IF EXISTS {lab_table}")
dbutils.fs.rm(lab_path, True)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 0 — Create the table and insert four rows
# MAGIC
# MAGIC Create the Delta table with **deletion vectors disabled** and insert the
# MAGIC four extract rows.

# COMMAND ----------

spark.sql(
    f"""
    CREATE TABLE {lab_table} (
      trip_id BIGINT,
      service_type STRING,
      payment_method STRING,
      base_fare_amount DECIMAL(10, 2),
      tip_amount DECIMAL(10, 2)
    )
    USING DELTA
    LOCATION '{lab_path}'
    TBLPROPERTIES (
      'delta.enableDeletionVectors' = 'false'
    )
    """
)
spark.sql(
    f"""
    INSERT INTO {lab_table} VALUES
      (1001, 'STANDARD', 'card', 20.00, 3.00),
      (1002, 'SHARED', 'cash', 15.00, 0.00),
      (1003, 'PREMIUM', 'card', 40.00, 6.00),
      (1004, 'STANDARD', 'wallet', 25.00, 2.50)
    """
)
display(spark.sql(f"SELECT * FROM {lab_table} ORDER BY trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 — UPDATE and DESCRIBE HISTORY
# MAGIC
# MAGIC Correct the PREMIUM trip's tip from **6.00** to **10.00**. That write is
# MAGIC one **atomic** commit: either the new tip is the current table state, or
# MAGIC the table is unchanged.
# MAGIC
# MAGIC `DESCRIBE HISTORY` lists each commit as a new version. Module 10 used
# MAGIC this command; here it shows the fare correction as its own transaction.

# COMMAND ----------

spark.sql(
    f"""
    UPDATE {lab_table}
    SET tip_amount = 10.00
    WHERE trip_id = 1003
    """
)
display(spark.sql(f"SELECT * FROM {lab_table} ORDER BY trip_id"))

# COMMAND ----------

display(spark.sql(f"DESCRIBE HISTORY {lab_table}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 — Optimistic concurrency
# MAGIC
# MAGIC Delta transactions are **ACID**:
# MAGIC
# MAGIC - **Atomic** — a write commits completely or not at all
# MAGIC - **Consistent** — the table moves from one valid snapshot to the next
# MAGIC - **Isolated** — a reader sees a snapshot, not another writer's in-flight
# MAGIC   work
# MAGIC - **Durable** — a committed version stays in the transaction log
# MAGIC
# MAGIC **Optimistic concurrency** is how Delta isolates overlapping writers:
# MAGIC
# MAGIC 1. A reader or writer sees a **snapshot** at a table version.
# MAGIC 2. A writer prepares new data files for its change.
# MAGIC 3. At commit, Delta **validates** that the files this writer used have
# MAGIC    not changed since that snapshot.
# MAGIC 4. If another writer already rewrote those files, the commit fails with
# MAGIC    a **concurrent-modification** error. The failed write did not commit,
# MAGIC    so the writer **retries** against the latest snapshot.
# MAGIC
# MAGIC Two writers that touch the **same files** conflict, even when they
# MAGIC update different rows. Deletion vectors are **off** in this notebook, so
# MAGIC an `UPDATE` rewrites the Parquet file that holds the row.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 — Overlapping-write conflict and retry
# MAGIC
# MAGIC Start two Python threads so two `UPDATE`s overlap: trip **1001**
# MAGIC **3.00 → 4.00** and trip **1004** **2.50 → 3.50**. They change different
# MAGIC rows, but both rewrite the same files, so one writer loses with a
# MAGIC concurrent-modification error (`DeltaConcurrentModificationException`,
# MAGIC often `ConcurrentAppendException` or `ConcurrentDeleteReadException`).
# MAGIC
# MAGIC The losing write does **not** commit. The next cell retries it. Expect
# MAGIC **4** rows when both writes have committed.
# MAGIC
# MAGIC > **Note:** If both writes commit (timing), re-run this cell so the
# MAGIC > updates overlap.

# COMMAND ----------

conflict_errors = []
results_lock = threading.Lock()
start_together = threading.Barrier(2)


def update_tip(trip_id, tip_amount):
    start_together.wait()
    try:
        spark.sql(
            f"""
            UPDATE {lab_table}
            SET tip_amount = {tip_amount}
            WHERE trip_id = {trip_id}
            """
        )  # Expected: DeltaConcurrentModificationException
    except DeltaConcurrentModificationException as exc:
        with results_lock:
            conflict_errors.append((trip_id, tip_amount, type(exc).__name__))
        print(f"trip_id {trip_id} did not commit: {type(exc).__name__}")
    else:
        print(f"trip_id {trip_id} committed tip_amount = {tip_amount}")


writers = [
    threading.Thread(target=update_tip, args=(1001, "4.00")),
    threading.Thread(target=update_tip, args=(1004, "3.50")),
]
for writer in writers:
    writer.start()
for writer in writers:
    writer.join()

print("conflict_errors =", conflict_errors)
display(spark.sql(f"SELECT * FROM {lab_table} ORDER BY trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC Retry any write that lost the conflict. After the retry, the table still
# MAGIC has **4** rows: **1001** tip **4.00**, **1003** tip **10.00**, **1004**
# MAGIC tip **3.50**.

# COMMAND ----------

if not conflict_errors:
    print("No conflict to retry — both writers committed.")
else:
    for trip_id, tip_amount, error_name in conflict_errors:
        print(f"Retrying trip_id {trip_id} after {error_name}")
        spark.sql(
            f"""
            UPDATE {lab_table}
            SET tip_amount = {tip_amount}
            WHERE trip_id = {trip_id}
            """
        )

display(spark.sql(f"SELECT * FROM {lab_table} ORDER BY trip_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4 — Table properties glance
# MAGIC
# MAGIC `SHOW TBLPROPERTIES` confirms `delta.enableDeletionVectors` is **false**.
# MAGIC
# MAGIC > **Note:** Deletion vectors can allow **row-level** concurrency when two
# MAGIC > writers update different rows in the same file. This notebook does not
# MAGIC > lab that behavior.

# COMMAND ----------

display(
    spark.sql(
        f"SHOW TBLPROPERTIES {lab_table} ('delta.enableDeletionVectors')"
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - A Delta `UPDATE` is an ACID commit and a new row in `DESCRIBE HISTORY`.
# MAGIC - Optimistic concurrency: readers see a snapshot; a writer validates
# MAGIC   against that version; overlapping writers on the same files conflict.
# MAGIC - The losing writer gets a concurrent-modification error and retries.
# MAGIC   The failed write does not commit, so the table stays consistent.
# MAGIC - Deletion vectors are off here. They can allow row-level concurrency
# MAGIC   for non-overlapping rows — that is not part of this lab.
# MAGIC
# MAGIC **Next:** Module 12 — Unity Catalog and Data Governance.
