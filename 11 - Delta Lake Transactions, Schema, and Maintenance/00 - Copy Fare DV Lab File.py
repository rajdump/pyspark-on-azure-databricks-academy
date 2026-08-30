# Databricks notebook source
# MAGIC %md
# MAGIC # 00 - Copy Fare DV Lab File
# MAGIC
# MAGIC Copy the large lab Parquet from the course repo to the external location
# MAGIC so later deletion-vector demos can use a file that is already around
# MAGIC **290 MB**.
# MAGIC
# MAGIC This notebook only **copies a file**. It does not create a table and does
# MAGIC not teach deletion vectors, `UPDATE`, `VACUUM`, or `OPTIMIZE`.
# MAGIC
# MAGIC ## Learning objectives
# MAGIC
# MAGIC - Copy `data/lab/fare_dv_lab.parquet` to the course external-tables folder
# MAGIC
# MAGIC **Reads:** `data/lab/fare_dv_lab.parquet` (not the 100-row source files or
# MAGIC teaching tables)
# MAGIC
# MAGIC **Writes:**
# MAGIC - `{url}/external-tables/fare_dv_lab/fare_dv_lab.parquet`
# MAGIC
# MAGIC **Prerequisites:** Module 10 notebooks `01`–`04`. Module 5
# MAGIC `01 - Unity Catalog Volumes and Data Landing.py` (catalog,
# MAGIC `el_rideshare_dev`, `processed`). Open this notebook from the course
# MAGIC **Git folder** so the copy cell can find `data/lab`.
# MAGIC
# MAGIC Module 5 landing does **not** copy `data/lab/`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup
# MAGIC Resolve the external location URL. Drop the lab table name if it exists.
# MAGIC Delete the destination folder so this notebook can re-run.

# COMMAND ----------

lab_table = "rideshare_dev.processed.fare_dv_lab"

external_location_url = (
    spark.sql("DESCRIBE EXTERNAL LOCATION el_rideshare_dev")
    .select("url")
    .first()["url"]
    .rstrip("/")
)
lab_path = f"{external_location_url}/external-tables/fare_dv_lab"
dest_file = f"{lab_path}/fare_dv_lab.parquet"

spark.sql(f"DROP TABLE IF EXISTS {lab_table}")
dbutils.fs.rm(lab_path, True)

print(f"lab_path = {lab_path}")
print(f"dest_file = {dest_file}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Copy the lab Parquet
# MAGIC Open this notebook from the course **Git folder**. The cell walks up from
# MAGIC the working directory until it finds `data/raw`, then copies
# MAGIC `data/lab/fare_dv_lab.parquet`.
# MAGIC
# MAGIC > **Note:** The destination is an `abfss://` folder, not a `/Volumes/`
# MAGIC > path. Do not `CREATE TABLE` here.

# COMMAND ----------

from pathlib import Path

def find_repo_root(start: Path) -> Path:
    for path in [start, *start.parents]:
        if (path / "data" / "raw").is_dir():
            return path
    raise FileNotFoundError(
        "Could not find a folder containing data/raw. "
        "Open this notebook from the course Git folder and try again."
    )

repo_root = find_repo_root(Path.cwd())
src = repo_root / "data" / "lab" / "fare_dv_lab.parquet"
if not src.is_file():
    raise FileNotFoundError(
        f"Missing {src}. Add data/lab/fare_dv_lab.parquet to the repo "
        "(about 290 MB or larger) and pull the Git folder again."
    )

print(f"src = {src}")
print(f"src size bytes = {src.stat().st_size}")

dbutils.fs.mkdirs(lab_path)
dbutils.fs.cp(f"file:{src.resolve()}", dest_file)
print(f"copied → {dest_file}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify
# MAGIC `LIST` the destination folder. You should see `fare_dv_lab.parquet`.

# COMMAND ----------

display(spark.sql(f"LIST '{lab_path}'"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - The lab Parquet lives in the repo under `data/lab/`, not `data/raw/`
# MAGIC - This notebook copies it to `{url}/external-tables/fare_dv_lab/`
# MAGIC - No Unity Catalog table is created here
# MAGIC
# MAGIC **Next:** `01 - Deletion Vectors, REORG TABLE, and VACUUM` still uses
# MAGIC four-row `fare_maint_lab`. Use the copied file when you need a ~290 MB
# MAGIC base file so deletion-vector files stay visible.
