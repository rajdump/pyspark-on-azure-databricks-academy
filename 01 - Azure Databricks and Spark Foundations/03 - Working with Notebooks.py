# Databricks notebook source
# MAGIC %md
# MAGIC # Working with Notebooks
# MAGIC
# MAGIC **Learning objectives.** After this notebook, you will be able to:
# MAGIC - Identify the different cell types in a Databricks notebook and run them
# MAGIC - Use common magic commands (`%md`, `%sql`, `%sh`, `%run`)
# MAGIC - Use `dbutils` for common notebook tasks (widgets, file system access,
# MAGIC   notebook utilities)
# MAGIC - Explain why cell execution order matters in a live Spark session
# MAGIC
# MAGIC **Prerequisites.** `02 - Apache Spark Architecture and PySpark` — you
# MAGIC should already know what a SparkSession is and how to attach compute.
# MAGIC
# MAGIC **Setup.** Any compute type works for this notebook. Classic all-purpose
# MAGIC Standard is fine; serverless also works for most cells (see gotcha notes
# MAGIC where relevant).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cells and magic commands
# MAGIC
# MAGIC A Databricks notebook is a sequence of **cells**. Each cell has a type
# MAGIC that tells the runtime how to interpret its content. You set most types
# MAGIC with a **magic command** — a line starting with `%` that must be the
# MAGIC **first line** of the cell.
# MAGIC
# MAGIC | Cell type | Magic (first line) | What it does |
# MAGIC |---|---|---|
# MAGIC | **Python** | *(none — default)* | Runs Python / PySpark on the driver |
# MAGIC | **Markdown** | `%md` | Renders formatted text, headings, tables |
# MAGIC | **SQL** | `%sql` | Runs a Spark SQL statement; shows a result table |
# MAGIC | **Shell** | `%sh` | Runs a bash command on the driver node |
# MAGIC
# MAGIC Two other magics are useful but are **not** cell languages:
# MAGIC
# MAGIC | Magic | Purpose |
# MAGIC |---|---|
# MAGIC | `%run` | Run another notebook and import its variables into this session |
# MAGIC | `%pip` | Install a Python package for this notebook session |
# MAGIC
# MAGIC You will see `%md` in every notebook in this course. `%sql` and `%run`
# MAGIC appear in later modules. `%pip` is covered in Module 14.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Worked example: `%sql`
# MAGIC
# MAGIC The cell below uses `%sql` to run a simple Spark SQL statement. The result
# MAGIC renders as a table directly in the notebook output — no `display()` needed
# MAGIC for SQL cells.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 'Working with Notebooks' AS lesson, current_timestamp() AS run_at

# COMMAND ----------

# MAGIC %md
# MAGIC ### Worked example: `%sh`
# MAGIC
# MAGIC `%sh` runs a bash command on the **driver node** — not on executors.
# MAGIC Useful for quick checks like confirming Python version or reading a small
# MAGIC local file. Not a substitute for Spark file operations on large data.
# MAGIC
# MAGIC **Gotcha — serverless.** `%sh` may be restricted or unavailable on
# MAGIC serverless compute. Prefer classic all-purpose Standard if you need it.

# COMMAND ----------

# MAGIC %sh
# MAGIC python3 --version

# COMMAND ----------

# MAGIC %sh
# MAGIC pwd

# COMMAND ----------

# MAGIC %sh
# MAGIC echo "hello from the driver"

# COMMAND ----------

# MAGIC %sh
# MAGIC ls -l /dbfs

# COMMAND ----------

# MAGIC %md
# MAGIC Other common commands you may see in `%sh` cells: `ls`, `pwd`, `cat`,
# MAGIC `echo`, `head`, `mkdir`. You do not need to memorize a shell catalog here.
# MAGIC
# MAGIC **Tip — Web Terminal.** For interactive work (for example `vim`, `htop`,
# MAGIC or multi-step command-line sessions), prefer the Databricks **Web
# MAGIC Terminal** over stacking many `%sh` cells in a notebook.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell execution order
# MAGIC
# MAGIC A Databricks notebook shares one live Python process (the driver) across
# MAGIC all cells. Variables, imports, and DataFrames created in one cell are
# MAGIC available in every cell run **after** it in the same session.
# MAGIC
# MAGIC This means **order matters**:
# MAGIC - If you run cell 5 before cell 3, and cell 5 depends on a variable
# MAGIC   defined in cell 3, cell 5 will fail.
# MAGIC - If you redefine a variable in cell 2 and re-run cell 5, cell 5 sees
# MAGIC   the new value — even if you ran cell 5 earlier with the old value.
# MAGIC
# MAGIC The safest habit: use **Run All** (`Shift+F10` or the toolbar button) to
# MAGIC run the notebook top-to-bottom before sharing it or recording results.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Worked example: execution order
# MAGIC
# MAGIC Run the two cells below in order, then try running the second cell first
# MAGIC (after restarting the session with **Detach & Re-attach**) to see the
# MAGIC `NameError` that results.

# COMMAND ----------

# Cell A — defines a variable
city = "New York"

# COMMAND ----------

# Cell B — uses the variable defined in Cell A
# If you run this before Cell A, Python raises NameError: name 'city' is not defined.
print(f"Rideshare city: {city}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## `dbutils`
# MAGIC
# MAGIC `dbutils` is a Databricks-provided utility object, available in every
# MAGIC notebook automatically (no import needed). It covers three areas you will
# MAGIC use throughout this course:
# MAGIC
# MAGIC | Utility | Access | What it does |
# MAGIC |---|---|---|
# MAGIC | **File system** | `dbutils.fs` | List, read, copy, move, delete files in DBFS or cloud storage |
# MAGIC | **Widgets** | `dbutils.widgets` | Create notebook parameters (dropdowns, text inputs) |
# MAGIC | **Notebook** | `dbutils.notebook` | Run or exit a notebook programmatically |
# MAGIC | **Secrets** | `dbutils.secrets` | Read secrets from a Databricks secret scope |
# MAGIC
# MAGIC You can explore any utility with `dbutils.fs.help()`, `dbutils.widgets.help()`,
# MAGIC and so on.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Worked example: `dbutils.fs`
# MAGIC
# MAGIC List the top-level entries in the Databricks File System (DBFS).
# MAGIC This is the managed file system attached to your workspace — not Unity
# MAGIC Catalog volumes, which come in a later module.

# COMMAND ----------

# List the root of DBFS.
for entry in dbutils.fs.ls("/"):
    print(entry.path)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Worked example: `dbutils.widgets`
# MAGIC
# MAGIC Widgets turn notebook parameters into interactive UI controls. In a
# MAGIC production job, widget values are supplied by the job run configuration
# MAGIC instead. Here, create a simple text widget and read its value.

# COMMAND ----------

# Create a text widget with a default value.
dbutils.widgets.text("city_filter", "New York", "City")

# Read the current value — default until the learner changes it in the UI.
city_filter = dbutils.widgets.get("city_filter")
print(f"city_filter = {city_filter!r}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Clean up the widget
# MAGIC
# MAGIC Widgets persist for the notebook session. Remove them when done so they
# MAGIC don't accumulate across repeated runs.

# COMMAND ----------

dbutils.widgets.remove("city_filter")

# COMMAND ----------

# MAGIC %md
# MAGIC ## `%run` — sharing code between notebooks
# MAGIC
# MAGIC `%run` executes another notebook and pulls all its variables and functions
# MAGIC into the current session. It is the simplest way to share a setup cell
# MAGIC (imports, dataset reads) across multiple notebooks in a module.
# MAGIC
# MAGIC ```python
# MAGIC # Example — not executed here because there is no target notebook yet.
# MAGIC # %run ./00 - Setup
# MAGIC ```
# MAGIC
# MAGIC You will use `%run` in later modules to load a shared setup notebook
# MAGIC before the lesson's main content. The path is relative to the current
# MAGIC notebook's folder.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC 1. In the cell below, add a `dbutils.widgets.dropdown` widget named
# MAGIC    `"service_type"` with options `["Yellow", "Green", "FHV"]` and default
# MAGIC    `"Yellow"`.
# MAGIC 2. Read its value with `dbutils.widgets.get("service_type")` and print it.
# MAGIC 3. Change the dropdown value in the notebook UI and re-run only that cell
# MAGIC    — confirm the printed value updates.
# MAGIC 4. Remove the widget with `dbutils.widgets.remove("service_type")`.

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC - A notebook is a sequence of **cells**; each cell runs in the shared
# MAGIC   driver process, so **execution order matters**.
# MAGIC - **Magic commands** (`%md`, `%sql`, `%sh`, `%run`, `%pip`) change how a
# MAGIC   cell is interpreted — the magic must be the first line of the cell.
# MAGIC - **`dbutils`** provides file system access (`dbutils.fs`), notebook
# MAGIC   parameters (`dbutils.widgets`), cross-notebook execution
# MAGIC   (`dbutils.notebook`), and secret access (`dbutils.secrets`).
# MAGIC
# MAGIC Next up: `04 - Your First DataFrame` — building and inspecting a small
# MAGIC rideshare DataFrame with `show()`, `display()`, and `printSchema()`.
