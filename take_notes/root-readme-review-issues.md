# Root `README.md` Review Issues

## Course Status and Scope

1. **The introduction implies that the full course already exists**
   - **Root README lines:** 3–8
   - The statement that the course “ends with a deployable batch data
     engineering project” can make the planned Modules 10–19 sound complete.
   - Clarify that the course is under active development and link to
     `COURSE_MODULES.md` for current availability.

2. **The streaming exclusion is ambiguous**
   - **Root README lines:** 10–12
   - “Streaming tables/pipelines” could be interpreted as excluding every
     kind of pipeline, including the planned batch Lakeflow Pipelines module.
   - Use “streaming tables and streaming pipelines” to distinguish them from
     batch pipelines.

3. **The required learner environment is not stated clearly**
   - **Related root README lines:** 14–25 (`Who this is for`); the environment
     requirement is currently absent.
   - Learners need access to an Azure Databricks workspace and usable compute
     from Module 1.
   - State this separately from the additional personal Azure and ADLS
     requirements introduced in Module 5.

## Technical Baseline

4. **The platform row conflates separate permission systems**
   - **Root README line:** 32
   - “Unity Catalog + RBAC enabled” mixes Azure RBAC, Databricks workspace
     permissions, and Unity Catalog privileges.
   - Use “Azure Databricks, Premium tier” for the platform row and retain the
     separate “Governance | Unity Catalog” row.

5. **The SQL description is broader than the course content**
   - **Root README line:** 38
   - “Databricks SQL / Spark SQL” suggests that Databricks SQL warehouses are
     taught.
   - The course currently teaches Spark SQL through `%sql` and `spark.sql()`
     in Databricks notebooks.

## Roadmap and Navigation

6. **Current module status is duplicated**
   - **Root README line:** 68
   - “Modules 1–9 are complete; next is Module 10” duplicates
     `COURSE_MODULES.md` and becomes stale whenever authoring progresses.
   - Keep status exclusively in `COURSE_MODULES.md` and link to it.

7. **The roadmap size is hardcoded**
   - **Root README line:** 66
   - “All 19 modules” duplicates the current roadmap size.
   - Use “the full roadmap” so the README remains accurate if the roadmap
     changes.

8. **The Module 5 prerequisite bullet contains too much detail**
   - **Root README line:** 69
   - Azure setup, ADLS, storage credentials, Unity Catalog privileges,
     Databricks Git folder access, and the PDF disclaimer are already covered
     by the Module 5 README.
   - Keep only a short warning and link to the module-specific prerequisites.

## Local Authoring Setup

9. **The `Setup` heading is misleading**
    - **Root README lines:** 79–82
    - `uv sync` installs local authoring tools; it is not required for learners
      who only run the course notebooks in Azure Databricks.
    - Rename the section to “Local authoring setup” and mark it as optional for
      notebook-only learners.

10. **“Pinned dev dependencies” is inaccurate**
    - **Root README lines:** 88–89
    - `pyproject.toml` declares minimum versions using `>=`.
    - `uv.lock`, not `pyproject.toml`, pins the resolved dependency versions.
    - Replace “pinned dev dependencies” with “declared dev dependencies.”
