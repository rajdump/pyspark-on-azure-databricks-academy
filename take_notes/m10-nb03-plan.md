# Module 10 notebook 03 — full authoring plan

**File to write:** `10 - Delta Lake Foundations/03 - Managed vs External Delta Tables.py`  
**Voice:** `01 - Why Delta Lake Exists.py`  
**Cells:** 32  
**Exercise:** none  
**Do not author the `.py` until the author says yes.**

Do not edit `COURSE_MODULES.md` or `docs/validation/` unless asked.

---

## Commands on execute

1. Patch [10 - Delta Lake Foundations/README.md](../10%20-%20Delta%20Lake%20Foundations/README.md):
   - Row 03 **Focus** = the sequence below; **No exercise**
   - “Notebooks **01**, **03**, and **04** each end with a short exercise” → 03 like 02 (no exercise)
   - LO bullet: contrast location, `DROP` / `UNDROP`, external re-register (drop PO / ordinary DML from 03)
   - Row 04 Focus: remove “do not re-interpret 03's DRY RUN”
2. `/new-lesson` then `/write-lesson` from this replica
3. Next: `/validate-notebook`

---

## Story

```text
CREATE both empty (0 rows)
        ↓
INSERT the same 4 rows → verify 4 each
        ↓
DESCRIBE DETAIL → information_schema → LIST
        ↓
DROP → SHOW TABLES DROPPED → external files remain
        ↓
UNDROP both (4 rows)
        ↓
DROP external → re-register LOCATION (4 rows)
        ↓
Cell 31 decide → Cell 32 close
```

---

## Locked facts

- Both are Unity Catalog tables. Difference = who controls the **storage path** and **what happens to the files on `DROP`**, not who owns the cloud data.
- **File lifecycle** = who decides the storage path, and what happens to the table files when you `DROP TABLE`. Not `OPTIMIZE` / `VACUUM`.
- Managed: `rideshare_dev.processed.fare_managed_lab` (no `LOCATION`)
- External: `rideshare_dev.processed.fare_external_lab` at `external_table_path`
- `external_location_url` = `url` from `DESCRIBE EXTERNAL LOCATION el_rideshare_dev`, strip trailing slash
- `external_table_path` = `{external_location_url}/external-tables/fare_external_lab`
- Never `CREATE` at the external-location root
- Extract: same four rows as 01–02; 1003 tip stays **6.00**; 1001 stays **3.00**
- First `CREATE` only: `TBLPROPERTIES ('delta.enableDeletionVectors' = 'false')`
- Bound `LOCATION` / `LIST` use `spark.sql`. `%sql` for single fixed-name demos
- `DROP TABLE` removes the **active Unity Catalog table registration** (still recoverable for 7 days)
- External files do **not** remain because of the 7-day window; they remain because you control that path
- Managed `UNDROP` = relation + files UC retained. External `UNDROP` = relation over files that **never left**. Never “external recovers files.”
- Managed `LIST`: uncaught `# Expected: AnalysisException`
- `SHOW TABLES DROPPED`
- No `UPDATE`, `DESCRIBE HISTORY`, `OPTIMIZE`, `VACUUM`, PO demo, exercise, `GRANT`, Volume `LOCATION`, `CREATE EXTERNAL TABLE` syntax, 8-day / 48-hour cleanup
- End state: managed undropped; external re-registered; **4** rows each
- Cell 31 = decision. Cell 32 = close only (no second architecture table)
- Callout: UC still governs external tables; automatic optimizations more limited; **Predictive Optimization is not supported**. Do not mention “disaster recovery.”
- Always write **Unity Catalog (UC)**. Never “Universal Catalog.”

---

## Markdown tables in the notebook

1. After `DESCRIBE DETAIL` (cell 11) — identity / who chooses location
2. After `LIST` (cell 16) — `table_type` / `storage_path` / `LIST` works?
3. After external `DROP` (cell 24) — active registration vs files
4. After re-register (cell 30) — `UNDROP` vs new registration
5. Cell 31 — architecture defaults (landing Volume / B-S-G managed / fixed-path external)

---

## Section 0 — Title

### Cell 1 (`%md`)

```markdown
# 03 - Managed vs External Delta Tables

Both are Unity Catalog (UC) tables. The difference is who controls the
storage location and what happens to the table files when you `DROP TABLE`.
You still own the data in your cloud account.

**File lifecycle** here means who decides the storage path, and what
happens to the table files when you `DROP TABLE`. It does not mean
`OPTIMIZE` or `VACUUM` (Module 11).

```text
Managed table
UC table ──► UC chooses storage location
             UC manages files on DROP

External table
UC table ──► You choose storage location
             You manage files on DROP
```

## Learning objectives

- Create the same empty Delta table as managed and as external, then load
  the same four rows
- Compare table type and storage location (`DESCRIBE DETAIL`,
  `information_schema`, `LIST`)
- `DROP` both, `UNDROP` both, and re-register the external folder

**Reads:** none of the 100-row source files or teaching tables
(`trip_enriched`, KPIs, `curated/`)

**Writes:**
- `rideshare_dev.processed.fare_managed_lab`
- `rideshare_dev.processed.fare_external_lab` at
  `{url}/external-tables/fare_external_lab`

**Prerequisites:** Module 9 notebooks `01`–`06`. Module 5
`01 - Unity Catalog Volumes and Data Landing.py` (catalog,
`el_rideshare_dev`, `processed`).

This notebook does **not** teach `UPDATE`, `DESCRIBE HISTORY`,
`OPTIMIZE`, `VACUUM`, time travel, `RESTORE`, grants (Module 12), or
`CREATE TABLE` at a Volume path.
```

---

## Section 1 — Setup

### Cell 2 (`%md`)

```markdown
## Setup
Handmade extract. Drop both lab names. Delete the external folder.
Do not insert yet.
```

### Cell 3 (Python)

```python
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
```

---

## Section 2 — Empty CREATE

### Cell 4 (`%md`)

```markdown
## Empty managed and external tables
Managed: no `LOCATION`. Unity Catalog chooses the path.
External: you choose an `abfss://` path, not `/Volumes/`.
**0** rows until the next section.
```

### Cell 5 (`%sql`)

```sql
CREATE TABLE rideshare_dev.processed.fare_managed_lab (
  trip_id BIGINT,
  service_type STRING,
  payment_method STRING,
  base_fare_amount DECIMAL(10, 2),
  tip_amount DECIMAL(10, 2)
)
USING DELTA
TBLPROPERTIES ('delta.enableDeletionVectors' = 'false')
```

### Cell 6 (Python)

```python
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
```

---

## Section 3 — One INSERT

### Cell 7 (`%md`)

```markdown
## Insert the extract
Same four rows into both tables. Trip **1003** tip stays **6.00**.
This load is so `DROP` / `UNDROP` / re-register can prove **data**
survived — not a DML lesson.
```

### Cell 8 (Python)

```python
spark.sql(f"INSERT INTO {managed_table} SELECT * FROM trips_extract")
spark.sql(f"INSERT INTO {external_table} SELECT * FROM trips_extract")

managed_df = spark.table(managed_table)
external_df = spark.table(external_table)
print(f"managed rows = {managed_df.count()} (expect 4)")
print(f"external rows = {external_df.count()} (expect 4)")
display(managed_df.orderBy("trip_id"))
display(external_df.orderBy("trip_id"))
```

---

## Section 4 — Where do they live?

### Cell 9 (`%md`)

```markdown
## Where do the files live?
`LIST` on the external path should succeed. `LIST` on the managed
table's cloud URI is expected to fail. Knowing a managed location
does not make it a supported file interface.
```

### Cell 10 (Python)

```python
display(spark.sql(f"DESCRIBE DETAIL {managed_table}"))
display(spark.sql(f"DESCRIBE DETAIL {external_table}"))
```

### Cell 11 (`%md`) — Table 1

```markdown
Look at `format` and `location`.

| | Managed | External |
|---|---|---|
| Registered in Unity Catalog | yes | yes |
| Format | Delta | Delta |
| Who chooses the location | Unity Catalog | you specify |
| Explicit `LOCATION` | no | yes |

This lab uses Delta for both so path and `DROP` behavior are the only
variables. External tables can use other file formats; that is not
this lab.
```

### Cell 12 (`%sql`)

```sql
SELECT table_name, table_type, storage_path
FROM rideshare_dev.information_schema.tables
WHERE table_schema = 'processed'
  AND table_name IN ('fare_managed_lab', 'fare_external_lab')
ORDER BY table_name
```

### Cell 13 (`%md`)

```markdown
`table_type` is `MANAGED` or `EXTERNAL`. Next: `LIST` the external
folder, then try the managed URI.
```

### Cell 14 (Python)

```python
display(spark.sql(f"LIST '{external_table_path}'"))
```

### Cell 15 (Python)

```python
managed_uri = (
    spark.sql(f"DESCRIBE DETAIL {managed_table}")
    .select("location")
    .first()["location"]
)
print(f"managed_uri = {managed_uri}")
spark.sql(f"LIST '{managed_uri}'")  # Expected: AnalysisException
```

### Cell 16 (`%md`) — Table 2

```markdown
Classroom `LIST` is not a managed-file browser. The failure does
**not** mean the files are gone.

| | Managed | External |
|---|---|---|
| `table_type` | `MANAGED` | `EXTERNAL` |
| `storage_path` | UC-chosen path | `external_table_path` |
| `LIST` of that path | expected to fail | succeeds |
```

---

## Section 5 — DROP

### Cell 17 (`%md`)

```markdown
## DROP TABLE
Does `DROP` delete the files? Do not wait 7 days. Do not `PURGE`.

`DROP TABLE` removes the **active Unity Catalog table registration**.
The table is no longer queryable. For **7 days**, `UNDROP` can recover
**either** type — that is catalog recovery, not “the table is gone
forever.”

That 7-day window is **not** why external files remain.
```

### Cell 18 (`%sql`)

```sql
DROP TABLE rideshare_dev.processed.fare_managed_lab;
SHOW TABLES DROPPED IN rideshare_dev.processed
```

### Cell 19 (`%md`)

```markdown
Do not `CREATE` this managed name again before `UNDROP`.
```

### Cell 20 (Python)

```python
print("External folder before DROP:")
display(spark.sql(f"LIST '{external_table_path}'"))
```

### Cell 21 (`%sql`)

```sql
DROP TABLE rideshare_dev.processed.fare_external_lab
```

### Cell 22 (Python)

```python
print("External folder after DROP:")
display(spark.sql(f"LIST '{external_table_path}'"))
```

### Cell 23 (`%sql`)

```sql
SHOW TABLES DROPPED IN rideshare_dev.processed
```

### Cell 24 (`%md`) — Table 3

```markdown
The **active UC registration** is gone; the ADLS folder is still there
(data files plus `_delta_log/`).

Managed: DROP → active registration removed → UC retains files →
UNDROP for 7 days → then UC deletes those files

External: DROP → active registration removed → UNDROP for 7 days
+ files remain at the ADLS path independently

The external files do **not** remain because of the 7-day `UNDROP`
window. They remain because the external table does not give Unity
Catalog control of deleting those files.

| | Managed | External |
|---|---|---|
| Active UC registration after `DROP` | removed | removed |
| Files after `DROP` | UC retains them for recovery (not a `LIST` browser) | remain at `external_table_path` |
| Why files remain | 7-day recovery, then UC deletes them | you control those files |
```

---

## Section 6 — UNDROP

### Cell 25 (`%md`)

```markdown
## UNDROP
Works for both types. For external, the location and credential must
still exist. `UNDROP TABLE name` restores the most recently dropped
matching relation. Expect **4** rows each.

- **Managed:** restores the UC relation **and** the data UC retained
  for recovery.
- **External:** restores the UC relation over files that **already
  remained** at the path. The files were never removed. Do not say
  that external `UNDROP` “recovers the files.”
```

### Cell 26 (Python)

```python
spark.sql(f"UNDROP TABLE {managed_table}")
spark.sql(f"UNDROP TABLE {external_table}")

managed_df = spark.table(managed_table)
external_df = spark.table(external_table)
print(f"managed rows = {managed_df.count()} (expect 4)")
print(f"external rows = {external_df.count()} (expect 4)")
display(managed_df.orderBy("trip_id"))
display(external_df.orderBy("trip_id"))
```

---

## Section 7 — Re-register

### Cell 27 (`%md`)

```markdown
## Re-register the external folder
Leave the managed table undropped. This is **not** `UNDROP`. Drop the
external name again, then register a new UC table over the folder
that is still on ADLS.
```

### Cell 28 (`%sql`)

```sql
DROP TABLE rideshare_dev.processed.fare_external_lab
```

### Cell 29 (Python)

```python
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
```

### Cell 30 (`%md`) — Table 4

```markdown
**4** rows. External files were never removed from the path.

| | Managed | External |
|---|---|---|
| `UNDROP` | 4 rows: relation + files UC retained | 4 rows: relation over files that stayed |
| 7-day window | catalog recovery; then UC deletes managed files | catalog recovery only; files stay because you control them |
| Re-register | do not `CREATE` the name before `UNDROP` | **new** UC registration over the surviving folder; 4 rows |

`UNDROP` restores the previously dropped UC relation. Re-registering
creates a **new** UC registration over the existing external Delta
folder.
```

---

## Section 8 — When to use which (decision)

### Cell 31 (`%md`) — Table 5

```markdown
## When to use which

### Use an external table when

Choose an **external table** when the storage path must stay under your
control.

Typical cases:

- data already exists at a specific ADLS path and should stay there
- another system needs direct access to the same files
- the table uses a file format that is not supported as a managed table
- `DROP TABLE` must leave the underlying files untouched

You provide the `LOCATION`. Unity Catalog still governs the table, but
the files remain at the storage path you manage.

### Use a managed table when

Choose a **managed table** for most new tables created in Databricks.

Unity Catalog chooses the storage location and Databricks manages the
table's storage lifecycle and platform optimizations.

For a typical lakehouse architecture:

| Area | Recommended default |
|---|---|
| Landing / raw source files | External Volume |
| New Bronze, Silver, and Gold tables | Managed table |
| Existing or shared data that must stay at a specific path | External table |

Bronze, Silver, and Gold describe **data layers**, not managed or
external table types.

**Bronze does not mean external.**

> **Note:** What do you give up with an external table?
>
> External tables remain governed by Unity Catalog, but some capabilities
> available to managed tables are reduced or unavailable:
>
> - automatic Databricks optimizations are more limited
> - Predictive Optimization is not supported
>
> Use external tables because you need control of the storage path,
> not simply because the data belongs to a particular medallion layer.

Module 5 `landing` and `processed` are course storage areas; they are not
medallion layers.
```

Learner rule: need control of the physical storage path → **external**. Otherwise, for a new Databricks lakehouse table → **managed**.

---

## Section 9 — Summary (close only)

### Cell 32 (`%md`)

Do not repeat Cell 31’s table, examples, or callout.

```markdown
## Summary

- Both managed and external tables are governed by Unity Catalog
- Managed is the default for most new Databricks tables
- External is for cases where you must control or preserve a specific
  storage path
- `DROP TABLE` removes the active UC registration; external files remain,
  while managed files follow the UC-managed recovery and deletion lifecycle
- `UNDROP` can recover either table type during the 7-day recovery window

**Next:** `04 - Delta Time Travel and Restore`
```

---

## Out of scope until yes

- Writing `03 - Managed vs External Delta Tables.py`
- Notebook 04
- Editing `COURSE_MODULES.md`
- Runtime validation / `docs/validation/`
