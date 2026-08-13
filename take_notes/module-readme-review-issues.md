# Module `README.md` Review Issues (Modules 01–09)

Author-only. Issues-only audit of module `README.md` files against
`COURSE_MODULES.md`, on-disk notebooks, `docs/data/dataset-overview.md`,
`docs/standards/naming-conventions.md`,
`docs/standards/permissions-and-governance.md`, and the `/review-module`
checklist applied across all nine modules.

Do **not** treat this file as a learner doc. Status stays in
`COURSE_MODULES.md`. Runtime evidence stays in `docs/validation/`.

Each item: location, problem, suggested fix, **Blocking** or **Optional**.

---

## Module 01 — Azure Databricks and Spark Foundations

No module-specific issues. Cross-module items C4 and C5 apply.

## Module 02 — DataFrame Fundamentals

No module-specific issues. Cross-module items C4 and C5 apply.

## Module 03 — Data Cleaning, NULL Semantics, and Type Handling

No module-specific issues. Cross-module items C4 and C5 apply.

## Module 04 — Transformations, Actions, and Lazy Evaluation

No module-specific issues. Cross-module items C4 and C5 apply.

## Module 05 — Reading, Writing, and Schemas

1. **Runtime section leaks validation evidence** — **Blocking**
   - **README:** §Runtime and scope ~L81–82
   - States notebooks are “runtime-validated” and links
     `docs/validation/05 - Reading, Writing, and Schemas.md`.
   - Drop the validation claim and the `docs/validation/` link; keep
     in-scope / out-of-scope only.

2. **Runtime section omits Spark / DBR** — **Blocking**
   - **README:** §Runtime and scope ~L79–89
   - Modules 7–9 state Spark **4.0.0** / DBR **17.3 LTS**; this section
     does not.
   - Add the same runtime line. (Also cross-module C3.)

3. **Out-of-scope module numbers are wrong** — **Blocking**
   - **README:** §Runtime and scope ~L87–89
   - Parenthetical “(Modules 6 and 10+)” does not match the exclusions:
     `explode` → Module 6; UC grants → Module 11; medallion → Modules
     12–13; Delta ACID / `MERGE` → Module 10.
   - Tag each exclusion with the correct module number.

Purpose length and Volume-path shorthand for this module are C1 and C2.

## Module 06 — Built-in Functions, Complex Types, and UDF Alternatives

4. **Runtime section omits Spark / DBR** — **Blocking**
   - **README:** §Runtime and scope ~L75–87
   - Same gap as Module 5. Add Spark **4.0.0** / DBR **17.3 LTS**.
     (Also C3.)

5. **Volume destinations use ellipsis** — **Blocking**
   - **README:** §Paths and outputs ~L60–62; §Notebooks ~L96–98
   - Paths such as `…/curated/drivers_flat/` and
     `…/trip_time/trip_time.parquet` are not full Volume paths.
   - Use `/Volumes/rideshare_dev/{schema}/{volume}/{path}/`. (Also C2.)

6. **Controlled-bad inputs are not Volume paths** — **Blocking**
   - **README:** §Prerequisites ~L38
   - Listed as `trip/bad_trip_data.csv` and `payment/bad_payment_data.csv`.
   - Use
     `/Volumes/rideshare_dev/landing/source_files/trip/bad_trip_data.csv`
     and
     `/Volumes/rideshare_dev/landing/source_files/payment/bad_payment_data.csv`.

7. **`drivers_flat` grain omits trips 1–100** — **Optional**
   - **README:** §Paths and outputs ~L60
   - `dataset-overview.md` states one row per (`driver_id`, `trip_id`);
     trips **1–100**.
   - Add that bound so it matches Module 7 and the dataset doc.

## Module 07 — Joins and Set Operations

8. **Prerequisites recommend Level 2 cleanup** — **Blocking**
   - **README:** §Prerequisites ~L61–62
   - “Clean rerun: Module 5 Notebook **99**, Level 2” would delete
     `curated/` — this module’s inputs. §Cleanup already says Level 2
     only clears curated Parquet.
   - Remove the Level 2 “clean rerun” from Prerequisites. Point at
     Cleanup: Level 1 for `practice/` hygiene; Level 4 to drop managed
     tables.

9. **Expected-NULL list is incomplete** — **Blocking**
   - **README:** §Paths and outputs ~L77–81
   - Lists trip **106** as the payment gap only. `dataset-overview.md`
     teaching NULLs for Modules 7–8 also include `base_fare_amount` on
     **104**; `tip_amount` on **103**; `trip_distance_miles` on **103,
     105, 106**; `trip_date` / `hour_of_day` on **101–106**.
   - Mirror that contract (or link to it) instead of a partial list.

Purpose length and `curated/` shorthand are C1 and C2.

## Module 08 — Aggregations and Window Functions

10. **Notebooks table title does not match the file** — **Blocking**
    - **README:** §Notebooks ~L153
    - Table says `Running Totals and lag/lead`; file is
      `06 - Running Totals and Lag and Lead.py`.
    - Use the on-disk title.

11. **Authoring quality gate breaks canonical section order** — **Blocking**
    - **README:** §Markdown Quality Gate ~L157–166
    - Author guidance sits between Notebooks and Minimum privileges.
    - Delete it from the learner README.

12. **Runtime has no In scope** — **Optional**
    - **README:** §Runtime and scope ~L118–129
    - Modules 5–7 and 9 have **In scope**; this module does not.
    - Add a short in-scope line (`groupBy`/`agg`, `pivot`, windows, KPI
      `saveAsTable`).

13. **“Verified” reads like run evidence** — **Optional**
    - **README:** §Paths and outputs ~L98–100
    - “NULL-affected pickup zones **(verified)**”.
    - Keep the zone list as the contract; drop “verified”.

Purpose length is C1.

## Module 09 — Spark SQL and DataFrame Interoperability

14. **Purpose lead does not match `COURSE_MODULES.md`** — **Blocking**
    - **README:** §Purpose ~L5–6
    - Roadmap Purpose is “Re-express DataFrame-based rideshare analytics
      in Spark SQL and choose deliberate SQL–DataFrame interoperability
      patterns.” Interop is buried in later Purpose paragraphs.
    - Open with the roadmap Purpose (2–4 lines); move SQL-first rules
      and habits out of Purpose. (Also C1.)

15. **Uses `M9` instead of `Module 9`** — **Blocking**
    - **README:** §PySpark callback map ~L190
    - Change **`M9`** to **Module 9**.

16. **Authoring quality gate breaks canonical section order** — **Blocking**
    - **README:** §Drafting quality gate ~L201–214
    - Same problem as Module 8 item 11.
    - Delete it from the learner README.

17. **Callback map sits before Minimum privileges** — **Optional**
    - **README:** §PySpark callback map ~L183–197
    - Extra `##` before privileges. Useful for learners.
    - Move it after Minimum privileges (or fold callbacks into the
      Notebooks table).

18. **“Phase II synthesis → Module 10” is easy to misread** — **Optional**
    - **README:** §Notebooks ~L123
    - Can be read as Module 10 still being Phase II.
    - Use “Phase II synthesis; next is Module 10 (Phase III)”.

---

## Cross-module

C1. **Purpose exceeds 2–4 lines (Modules 5, 7, 8, 9)** — **Blocking**
    - Extra paragraphs mix in lab setup, notebook architecture, and
      teaching habits. Modules 1–4 and the first two lines of Module 6
      already match the roadmap.
    - Keep the `COURSE_MODULES.md` Purpose (2–4 lines). Move the rest
      to Prerequisites, Runtime and scope, or Notebooks.
    - Module 5: hybrid I/O / `explode` → Runtime; student storage +
      Notebook 01 creates objects → Prerequisites / Before Notebook 01;
      dataset-overview link stays in Paths.
    - Module 7: 01–06 habits and write-vs-skill split → Notebooks intro.
    - Module 8: grain/`count()` habits → Notebooks intro.
    - Module 9: SQL-first / Python-allowed rules → Runtime; two habits
      → Notebooks intro; no-writes stays in Paths / Runtime.

C2. **Volume path shorthand (Modules 5–9)** — **Blocking**
    - Destinations appear as `practice/`, `curated/trip/`,
      `…/curated/drivers_flat/`, etc. Required form:
      `/Volumes/rideshare_dev/{schema}/{volume}/{path}/`.
    - Worst in Module 6 (§Paths and outputs, §Notebooks). Module 7
      §Prerequisites uses `curated/trip/` as the asset path.
    - Folder *names* (`practice/`, `curated/`) may remain as tier labels
      after a full-path table; they are not a substitute for Volume
      paths.

C3. **`## Runtime and scope` Spark line (Modules 5–6 vs 7–9)** — **Blocking**
    - 7–9 include Spark **4.0.0** / DBR **17.3 LTS**; 5–6 have the
      section without it.
    - Same runtime line in every module that has this section.

C4. **Notebook table `#` is unpadded (all 01–09)** — **Optional**
    - Files are `01`, `02`, …; tables use `1`, `2`, ….
    - Zero-pad the `#` column (`01`, `02`, …, `99`) to match files.

C5. **Minimum-privileges bullet order (all 01–09)** — **Optional**
    - READMEs list Workspace then Unity Catalog.
      `docs/standards/permissions-and-governance.md` shows UC, then
      workspace, then Azure RBAC.
    - Match that order.

C6. **Cross-module notebook pointers omit titles (Modules 5–9 prose)** — **Optional**
    - Pointers like “Module 5 **`01`**” or “Notebook **07**” omit the
      notebook title. `docs/standards/naming-conventions.md` wants
      module + title.
    - Intra-module tables can keep `#` + short name. Cross-module prose
      should use both (e.g. `` `01 - Unity Catalog Volumes and Data
      Landing.py` in Module 5 ``).
