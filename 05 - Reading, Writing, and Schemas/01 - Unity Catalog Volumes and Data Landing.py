# Databricks notebook source
# MAGIC %md
# MAGIC # Unity Catalog Volumes and Data Landing
# MAGIC
# MAGIC Module 5 begins file-based work on the shared rideshare dataset. Before
# MAGIC reading CSV, JSON, Parquet, XML, or Avro in later notebooks, land the course
# MAGIC data on Unity Catalog Volumes under **`academy.rideshare`**.
# MAGIC
# MAGIC **Learning objectives.** After this notebook, you will be able to:
# MAGIC - Explain how catalog, schema, and volume fit together for governed file
# MAGIC   storage in this course lab
# MAGIC - Create **`raw`**, **`processed`**, and **`source`** volumes when they do
# MAGIC   not already exist (under the existing **`el_lab`** external location)
# MAGIC - Create dataset folders with **`dbutils.fs.mkdirs`**
# MAGIC - Copy repo source files into Volume paths and verify they landed
# MAGIC
# MAGIC **Prerequisites.** Module 4 — Transformations, Actions, and Lazy Evaluation.
# MAGIC
# MAGIC **Setup.** Attach classic all-purpose compute with PySpark and Unity Catalog
# MAGIC access. Learner paths use Volume URLs only — not long **`abfss://`** strings.
# MAGIC
# MAGIC Shared lab constants and repo → Volume paths:
# MAGIC **`docs/data/dataset-overview.md`** (Physical layout — **`academy`** /
# MAGIC **`rideshare`**, volumes **`raw`** / **`processed`** / **`source`**, datasets
# MAGIC **`trip`**, **`trip_time`**, **`zone_lookup`**, **`payment`**, **`drivers`**).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup — locate the course repo
# MAGIC
# MAGIC This notebook copies files from the Databricks **Git folder** checkout of
# MAGIC this course into Volumes. Set **`repo_root`** to the folder that contains
# MAGIC **`data/raw/`** (the course repository root in this workspace — not a path
# MAGIC on your laptop).

# COMMAND ----------

dbutils.widgets.text(  # noqa: F821
    "repo_root",
    "",
    "Course repo root under /Workspace/Repos/...",
)
repo_root = dbutils.widgets.get("repo_root").rstrip("/")  # noqa: F821
if not repo_root:
    raise ValueError(
        "Set the repo_root widget to your Databricks Git folder path "
        "(the folder that contains data/raw/)."
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Unity Catalog awareness
# MAGIC
# MAGIC Unity Catalog organizes governed objects in layers:
# MAGIC
# MAGIC | Layer | This lab | Role |
# MAGIC |---|---|---|
# MAGIC | **Catalog** | **`academy`** | Top-level container |
# MAGIC | **Schema** | **`rideshare`** | Groups related tables and volumes |
# MAGIC | **Volume** | **`raw`**, **`processed`**, **`source`** | Governed file storage |
# MAGIC
# MAGIC Learners read and write with Volume paths such as
# MAGIC **`/Volumes/academy/rideshare/raw/trip/`** — not raw storage URLs.
# MAGIC
# MAGIC Prerequisite: external location **`el_lab`** already exists in this lab.
# MAGIC Storage credentials, external-location design, and grants are Module 11.
# MAGIC Catalog **`academy`** and schema **`rideshare`** must exist before volumes
# MAGIC can be created (ask your lab admin if **`USE CATALOG`** / **`USE SCHEMA`**
# MAGIC fail).

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG academy;
# MAGIC USE SCHEMA rideshare;
# MAGIC SELECT current_catalog() AS catalog_name, current_schema() AS schema_name;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create volumes
# MAGIC
# MAGIC An **external volume** points at a folder under an existing external
# MAGIC location. Discover the **`el_lab`** URL, then create **`raw`**,
# MAGIC **`processed`**, and **`source`** with **`CREATE VOLUME IF NOT EXISTS`**
# MAGIC when they are missing.
# MAGIC
# MAGIC After creation, day-to-day work uses **`/Volumes/academy/rideshare/...`**
# MAGIC only.

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE EXTERNAL LOCATION el_lab

# COMMAND ----------

el_url = (
    spark.sql("DESCRIBE EXTERNAL LOCATION el_lab")  # noqa: F821
    .select("url")
    .collect()[0]["url"]
    .rstrip("/")
)
print(f"el_lab URL: {el_url}")

volume_locations = {
    "raw": f"{el_url}/academy/raw",
    "processed": f"{el_url}/academy/processed",
    "source": f"{el_url}/academy/source",
}

for volume_name, location in volume_locations.items():
    spark.sql(  # noqa: F821
        f"""
        CREATE VOLUME IF NOT EXISTS academy.rideshare.{volume_name}
        LOCATION '{location}'
        """
    )
    print(f"Ensured volume academy.rideshare.{volume_name} -> {location}")

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW VOLUMES IN academy.rideshare

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prepare folder structure
# MAGIC
# MAGIC Volumes are the containers. Dataset folders inside them keep each rideshare
# MAGIC table's files separate. Create the folders under **`raw/`** and the JDBC
# MAGIC seed folder under **`source/payment/`**.

# COMMAND ----------

VOL_RAW = "/Volumes/academy/rideshare/raw"
VOL_PROCESSED = "/Volumes/academy/rideshare/processed"
VOL_SOURCE = "/Volumes/academy/rideshare/source"

raw_datasets = ["trip", "trip_time", "zone_lookup", "drivers", "payment"]
for dataset in raw_datasets:
    dbutils.fs.mkdirs(f"{VOL_RAW}/{dataset}/")  # noqa: F821

dbutils.fs.mkdirs(f"{VOL_SOURCE}/payment/")  # noqa: F821

print("Created folders:")
for dataset in raw_datasets:
    print(f"  {VOL_RAW}/{dataset}/")
print(f"  {VOL_SOURCE}/payment/")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Upload course data from the repo
# MAGIC
# MAGIC Copy each primary Module 5 source file into its Volume destination. The
# MAGIC **`payment`** seed for the next notebook lands under **`source/payment/`**;
# MAGIC Avro under **`raw/payment/`** is written later via JDBC.

# COMMAND ----------

# Repo relative path -> Volume destination (file name preserved).
copy_jobs = [
    ("data/raw/csv/trip.csv", f"{VOL_RAW}/trip/trip.csv"),
    ("data/raw/parquet/trip_time.parquet", f"{VOL_RAW}/trip_time/trip_time.parquet"),
    ("data/raw/json/zone_lookup.json", f"{VOL_RAW}/zone_lookup/zone_lookup.json"),
    ("data/raw/xml/drivers.xml", f"{VOL_RAW}/drivers/drivers.xml"),
    ("data/raw/csv/payment.csv", f"{VOL_SOURCE}/payment/payment.csv"),
]

for relative_src, dest in copy_jobs:
    src = f"file:{repo_root}/{relative_src}"
    dbutils.fs.cp(src, dest, True)  # noqa: F821
    print(f"Copied {relative_src} -> {dest}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify landed files
# MAGIC
# MAGIC List each target folder and confirm the expected files are present before
# MAGIC the format-read notebooks.

# COMMAND ----------

verify_paths = [
    f"{VOL_RAW}/trip/",
    f"{VOL_RAW}/trip_time/",
    f"{VOL_RAW}/zone_lookup/",
    f"{VOL_RAW}/drivers/",
    f"{VOL_RAW}/payment/",
    f"{VOL_SOURCE}/payment/",
]

for path in verify_paths:
    entries = dbutils.fs.ls(path)  # noqa: F821
    names = [e.name for e in entries]
    print(f"{path} -> {names}")

# COMMAND ----------

# MAGIC %md
# MAGIC **Gotcha — empty `raw/payment/`.** That folder is intentional right now. The
# MAGIC next notebook loads **`payment`** from Azure SQL and writes Avro into
# MAGIC **`raw/payment/`**. The CSV seed lives under **`source/payment/`**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Practice the same folder + list pattern on a **different** path — not one
# MAGIC of the **`raw/`** dataset folders already verified above.
# MAGIC
# MAGIC 1. Create **`/Volumes/academy/rideshare/processed/practice/`** with
# MAGIC    **`dbutils.fs.mkdirs`**.
# MAGIC 2. List that path with **`dbutils.fs.ls`** and print how many entries it
# MAGIC    has (a brand-new folder may show **`0`**).
# MAGIC 3. Confirm the path string you used starts with
# MAGIC    **`/Volumes/academy/rideshare/processed/`**.

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - **`academy`** / **`rideshare`** hold the course volumes; **`el_lab`** is
# MAGIC   the existing external location underneath them
# MAGIC - **`CREATE VOLUME IF NOT EXISTS`** registers **`raw`**, **`processed`**,
# MAGIC   and **`source`** under **`el_lab`**
# MAGIC - **`dbutils.fs.mkdirs`** builds dataset folders; **`dbutils.fs.cp`** lands
# MAGIC   repo files onto Volume paths
# MAGIC - Day-to-day paths look like **`/Volumes/academy/rideshare/raw/trip/`**
# MAGIC
# MAGIC **Next up:** **Azure SQL Load and Extract** — **`payment`** seed from
# MAGIC **`source/payment/`**, JDBC to **`el_lab.payments`**, Avro to
# MAGIC **`raw/payment/`**.
