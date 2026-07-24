# Databricks notebook source
# MAGIC %md
# MAGIC # Apache Spark Architecture and PySpark
# MAGIC
# MAGIC **Learning objectives.** After this notebook, you will be able to:
# MAGIC - Explain what Apache Spark is and why data engineers use it
# MAGIC - Describe the driver/executor model at a practical level
# MAGIC - Relate a notebook cell run to jobs, stages, and tasks in the Spark UI
# MAGIC - Recognize PySpark as the Python API for Spark on Databricks
# MAGIC
# MAGIC **Prerequisites.** `01 - Introduction to Azure Databricks and the Workspace`
# MAGIC in this module — you should already know how to attach compute and run a cell.
# MAGIC
# MAGIC **Dataset note.** This module uses small, hand-built rideshare-flavored
# MAGIC examples when needed. File-based reads of the shared rideshare dataset
# MAGIC begin later.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup
# MAGIC
# MAGIC Attach this notebook to **classic all-purpose** compute (**Standard** access
# MAGIC mode when available) before running code cells. Prefer classic compute for
# MAGIC this lesson so you can open the **Spark UI** clearly after a cell runs.
# MAGIC
# MAGIC No dataset files are required — examples below build a few rows in code.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Concept: Apache Spark and PySpark
# MAGIC
# MAGIC **Apache Spark** is a distributed data processing engine. Instead of one
# MAGIC machine doing all the work, Spark can split a large batch job across many
# MAGIC workers and combine the results. Data engineers use it for reliable,
# MAGIC repeatable batch pipelines — clean, transform, join, and write tables at
# MAGIC scale.
# MAGIC
# MAGIC On Azure Databricks you do not install Spark yourself. Compute already
# MAGIC includes Spark as part of the **Databricks Runtime**.
# MAGIC
# MAGIC **PySpark** is the Python API for Spark. When you write Python in a
# MAGIC Databricks notebook and use `spark` (and later DataFrame methods), you are
# MAGIC using PySpark. Spark also has APIs for Scala and SQL; this course focuses
# MAGIC on PySpark for batch data engineering.
# MAGIC
# MAGIC You do not need a distributed-systems deep dive here. Remember the job
# MAGIC framing: **your notebook code describes the work; Spark schedules that
# MAGIC work across the cluster.**

# COMMAND ----------

# MAGIC %md
# MAGIC ## Concept: driver, executors, jobs, stages, and tasks
# MAGIC
# MAGIC When your notebook is attached to compute, Spark runs with two main roles:
# MAGIC
# MAGIC | Role | What it does |
# MAGIC |---|---|
# MAGIC | **Driver** | Coordinates the job — plans the work and collects final results |
# MAGIC | **Executors** | Worker processes that run pieces of the work in parallel |
# MAGIC
# MAGIC When you run a cell that actually **executes** Spark work (an *action*, such
# MAGIC as showing rows or counting them), Spark organizes that work like this:
# MAGIC
# MAGIC 1. **Job** — one unit of work triggered by an action
# MAGIC 2. **Stage** — a phase within a job (Spark may split a job into stages when
# MAGIC    data must be reshuffled between workers)
# MAGIC 3. **Task** — the smallest unit; each task runs on one executor on a slice
# MAGIC    of the data
# MAGIC
# MAGIC So one notebook cell that calls an action can create **one or more jobs**,
# MAGIC each with **stages**, each with **tasks**.
# MAGIC
# MAGIC Later modules cover *lazy evaluation* (why some lines do not run work yet).
# MAGIC For now: if you only build a DataFrame and never call something like
# MAGIC `.show()` or `.count()`, you may see little or no new work in the Spark UI.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Where to find the Spark UI
# MAGIC
# MAGIC After you run an action on classic compute:
# MAGIC
# MAGIC 1. Open the compute attached to this notebook (or use the notebook's Spark
# MAGIC    UI / jobs entry point your workspace shows for the run).
# MAGIC 2. Open the **Spark UI**.
# MAGIC 3. Look at the **Jobs** page for a new job tied to your cell run.
# MAGIC 4. Open that job to see **stages**, then open a stage to see **tasks**.
# MAGIC
# MAGIC Exact menu labels can vary slightly by UI version. The goal is the same:
# MAGIC connect **your cell** → **job** → **stage** → **task**.
# MAGIC
# MAGIC **Gotcha.** On serverless, Spark UI visibility can differ from classic
# MAGIC clusters. Prefer classic all-purpose **Standard** for this notebook's
# MAGIC Spark UI exercise.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Worked example: run an action and inspect the Spark UI
# MAGIC
# MAGIC The next cell builds a tiny rideshare-flavored DataFrame by hand (a few
# MAGIC `trip` rows — not a file read). Then it calls `.show()`, which is an
# MAGIC **action** and should create Spark work you can find in the Spark UI.
# MAGIC
# MAGIC After the cell finishes:
# MAGIC
# MAGIC 1. Open the Spark UI for this compute.
# MAGIC 2. Find the newest job.
# MAGIC 3. Note how many stages and tasks that job shows (even a tiny DataFrame
# MAGIC    usually still shows at least one stage with one or more tasks).

# COMMAND ----------

# Small ad-hoc sample — column names match the course trip table shape.
trips = spark.createDataFrame(
    [
        (1001, "standard", 1, 5, 2.40, 3, 12, 1),
        (1002, "premium", 2, 8, 5.10, 5, 18, 2),
        (1003, "standard", 3, 1, 1.20, 2, 8, 1),
    ],
    schema=[
        "trip_id",
        "service_type",
        "pickup_location_id",
        "dropoff_location_id",
        "trip_distance_miles",
        "request_to_pickup_mins",
        "ride_duration_mins",
        "driver_arrival_to_pickup_mins",
    ],
)

# .show() is an action — it triggers a Spark job you can inspect in the Spark UI.
trips.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ### What you should see
# MAGIC
# MAGIC - A three-row table printed in the notebook output.
# MAGIC - In the Spark UI, at least one recent **job** created by the `.show()`
# MAGIC   action, with stage and task detail underneath.
# MAGIC
# MAGIC You are not expected to tune performance here. The goal is a mental model:
# MAGIC **notebook action → Spark job → stages → tasks on executors.**

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Practice the same loop with a different action:
# MAGIC
# MAGIC 1. Keep classic all-purpose compute attached.
# MAGIC 2. Run the cell below (it uses `.count()` instead of `.show()`).
# MAGIC 3. Open the Spark UI and find the new job for this run.
# MAGIC 4. Write down (in a comment in that cell, or on paper) how many **stages**
# MAGIC    and roughly how many **tasks** that job shows.
# MAGIC
# MAGIC The exact counts can vary by Runtime and cluster size — what matters is
# MAGIC that you can find the job and read its stage/task breakdown.

# COMMAND ----------

# Same tiny trip sample, different action — look for a new job in the Spark UI.
trips = spark.createDataFrame(
    [
        (2001, "standard", 4, 6, 3.50, 4, 15, 2),
        (2002, "premium", 7, 2, 6.80, 6, 22, 3),
    ],
    schema=[
        "trip_id",
        "service_type",
        "pickup_location_id",
        "dropoff_location_id",
        "trip_distance_miles",
        "request_to_pickup_mins",
        "ride_duration_mins",
        "driver_arrival_to_pickup_mins",
    ],
)

trip_count = trips.count()
print(f"Trip count: {trip_count}")

# After checking the Spark UI, note what you saw, for example:
# stages_seen = ?
# tasks_seen = ?

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - **Spark** is the distributed engine; **PySpark** is how you drive it from
# MAGIC   Python on Databricks.
# MAGIC - The **driver** plans; **executors** run the work.
# MAGIC - An **action** (like `.show()` or `.count()`) creates a **job**, which
# MAGIC   breaks into **stages** and **tasks** — visible in the Spark UI.
# MAGIC - Prefer classic all-purpose compute when you need a clear Spark UI view.
# MAGIC
# MAGIC Next up: `03 - Working with Notebooks` — cells, magic commands, and
# MAGIC `dbutils` inside the Databricks notebook editor.
