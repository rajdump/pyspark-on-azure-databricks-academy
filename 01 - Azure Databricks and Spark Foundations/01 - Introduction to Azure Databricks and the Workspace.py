# Databricks notebook source
# MAGIC %md
# MAGIC # Introduction to Azure Databricks and the Workspace
# MAGIC
# MAGIC **Learning objectives.** After this notebook, you will be able to:
# MAGIC - Navigate the main areas of the Azure Databricks workspace
# MAGIC - Attach a notebook to compute and run a cell
# MAGIC - Explain, at a high level, what Databricks Runtime (and LTS) means for this course
# MAGIC
# MAGIC **Prerequisites.** None — this is the first notebook in the course.
# MAGIC
# MAGIC **Dataset note.** This module uses small, hand-built examples when needed.
# MAGIC File-based reads of the shared rideshare dataset begin later. This notebook
# MAGIC focuses on the workspace and compute — no dataset files are required.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup
# MAGIC
# MAGIC Before you run any code cells:
# MAGIC
# MAGIC 1. Open this notebook in your Azure Databricks workspace (via the Git folder
# MAGIC    that tracks this course repository).
# MAGIC 2. In the notebook toolbar, open the **Connect** (compute) dropdown.
# MAGIC 3. Select compute that your workspace provides for this course, or start it
# MAGIC    if it is stopped.
# MAGIC 4. Wait until the notebook shows that it is attached (connected).
# MAGIC
# MAGIC If a cell fails with a message about no cluster or compute, attach compute
# MAGIC and try again. You do not need any data files for this notebook.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Concept: the Azure Databricks workspace
# MAGIC
# MAGIC An Azure Databricks **workspace** is the web environment where you organize
# MAGIC notebooks, attach compute, and run batch data engineering work. Think of it
# MAGIC as the home base for this course — not a place you install Spark yourself.
# MAGIC
# MAGIC Three areas matter most right now:
# MAGIC
# MAGIC | Area | What it is | Why you care |
# MAGIC |---|---|---|
# MAGIC | **Workspace browser** | Folders and notebooks (including this Git-backed course) | Where you find and open lessons |
# MAGIC | **Notebook editor** | Cells you read, edit, and run | Where you write and execute PySpark |
# MAGIC | **Compute** | The machines that actually run your code | Notebooks do nothing useful until attached |
# MAGIC
# MAGIC In production, the same idea holds: your logic lives in notebooks or jobs,
# MAGIC and **compute** is what executes it. Choosing and attaching the right
# MAGIC compute is platform literacy every later module depends on.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Concept: attaching compute
# MAGIC
# MAGIC **Compute** is the cluster (or serverless environment) that runs notebook
# MAGIC cells. **Attaching** (connecting) a notebook to compute links this editor
# MAGIC to that runtime so `spark` and Python cells can execute.
# MAGIC
# MAGIC Common gotcha: you open a notebook and click Run before anything is
# MAGIC attached. The cell cannot run until compute is connected and ready.
# MAGIC
# MAGIC For this course, start with **classic all-purpose** compute in **Standard**
# MAGIC access mode when your workspace offers it. Other compute types appear in
# MAGIC later modules when a topic needs them — you do not need every option yet.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Concept: Databricks Runtime and LTS
# MAGIC
# MAGIC **Databricks Runtime (DBR)** is the software stack on your compute: Apache
# MAGIC Spark, Python, and supporting libraries, packaged as one versioned
# MAGIC environment.
# MAGIC
# MAGIC **LTS** means **Long Term Support** — a Runtime line that receives fixes
# MAGIC for a longer window than non-LTS releases. Teams pin an LTS version so
# MAGIC jobs stay predictable instead of silently changing underneath them.
# MAGIC
# MAGIC This course targets **Databricks Runtime 17.3 LTS** (Spark 4.0, Python
# MAGIC 3.12). When you create or pick compute for these notebooks, prefer that
# MAGIC Runtime (or the LTS version your workspace admin has standardized for the
# MAGIC course).
# MAGIC
# MAGIC You do not need to memorize every library on the Runtime. Remember the
# MAGIC idea: **the Runtime version defines what your code runs on.**

# COMMAND ----------

# MAGIC %md
# MAGIC ## Worked example: confirm compute is ready
# MAGIC
# MAGIC With this notebook attached to compute, run the next cell. Azure Databricks
# MAGIC already provides a `spark` session in the notebook — you do not create one
# MAGIC yourself here.
# MAGIC
# MAGIC The cell prints the Spark version and the Databricks Runtime version from
# MAGIC your attached compute. That is a simple proof that the workspace, notebook,
# MAGIC and compute are connected.

# COMMAND ----------

import os

# A notebook on Databricks already has `spark`. These prints confirm that this
# notebook is attached to compute and show which Runtime you are on.
spark_version = spark.version
dbr_version = os.environ.get(
    "DATABRICKS_RUNTIME_VERSION",
    spark.conf.get("spark.databricks.clusterUsageTags.sparkVersion", "unknown"),
)

print(f"Spark version on this compute: {spark_version}")
print(f"Databricks Runtime version: {dbr_version}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### What you should see
# MAGIC
# MAGIC - A Spark version string (for DBR 17.3 LTS this is in the Spark 4.0 line).
# MAGIC - A Databricks Runtime version string (for this course, look for **17.3** LTS).
# MAGIC - If the cell errors because compute is missing, use **Connect**, attach
# MAGIC   compute, wait until it is ready, and run the cell again.
# MAGIC
# MAGIC You can also confirm Runtime in the UI: open the compute details for the
# MAGIC cluster you attached and check the Databricks Runtime version shown there.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Practice the attach-and-run loop yourself:
# MAGIC
# MAGIC 1. If compute is connected, disconnect it from the notebook toolbar, then
# MAGIC    attach (connect) again and wait until it is ready.
# MAGIC 2. Run the cell below and note the printed **Databricks Runtime** version.
# MAGIC 3. In the compute UI for the cluster you attached, confirm the same Runtime
# MAGIC    version appears there.
# MAGIC
# MAGIC You are not grading yourself on a perfect match of every suffix — the goal
# MAGIC is to practice connecting compute and knowing where Runtime is shown.

# COMMAND ----------

# After re-attaching compute, run this cell.
import os

spark_version = spark.version
dbr_version = os.environ.get(
    "DATABRICKS_RUNTIME_VERSION",
    spark.conf.get("spark.databricks.clusterUsageTags.sparkVersion", "unknown"),
)

print(f"Spark version on this compute: {spark_version}")
print(f"Databricks Runtime version: {dbr_version}")

# Optional: compare the printed Runtime with the value shown in the compute UI.
# Example shape: 17.3 — use whatever your workspace shows.
# dbr_version_from_ui = "REPLACE_ME"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - The **workspace** is where you browse notebooks and do your work.
# MAGIC - **Compute** runs your cells; attach (connect) before you expect output.
# MAGIC - **Databricks Runtime** is the versioned Spark/Python stack on that compute;
# MAGIC   **LTS** is the supported line this course pins (**17.3 LTS**).
# MAGIC
# MAGIC Next up: `02 - Apache Spark Architecture and PySpark` — how Spark executes
# MAGIC work once compute is attached (driver, executors, jobs, stages, and tasks).
