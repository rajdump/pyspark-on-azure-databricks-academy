# Permissions and Governance

Canonical owner of the distinction between Azure RBAC, Databricks workspace
permissions, and Unity Catalog privileges, plus the minimum-privilege
documentation pattern used in module `README.md` files. Referenced by
`.cursor/rules/course-authoring.mdc`, `/review-module`, and `/validate-notebook` — do not duplicate
this content elsewhere.

## Three distinct permission systems

This course touches three separate, non-overlapping permission systems.
Confusing them is a common source of "why can't I do this" errors — always
be explicit about which one applies.

| System | Controls | Example |
|---|---|---|
| **Azure RBAC** | Access to Azure resources themselves (the Databricks workspace resource, the metastore's underlying storage account, networking) | "Contributor" role on the Azure resource group hosting the workspace |
| **Databricks workspace permissions** | Access to objects inside the Databricks workspace UI/API (compute, jobs, notebooks, workspace folders) | `CAN ATTACH TO` on a cluster, `CAN MANAGE` on a job (`CAN USE` applies to cluster policies, not clusters) |
| **Unity Catalog privileges** | Access to governed data objects (catalogs, schemas, tables, volumes) | `USE CATALOG`, `USE SCHEMA`, `SELECT` on a table |

A learner can have full Databricks workspace access and still be unable to
query a table because Unity Catalog privileges are missing — and vice
versa. Azure RBAC is often invisible when storage is already provisioned,
but **Module 5** expects each learner to use **their own** Azure storage
and storage credential — so Azure RBAC on that storage is learner-visible
for external-location setup and File Events troubleshooting.

## Unity Catalog privilege chaining

Unity Catalog privileges are hierarchical — reading a table requires **all**
of the following, not just a grant on the table itself:

```
USE CATALOG <catalog>  -->  USE SCHEMA <schema>  -->  SELECT (or other object-level privilege) on the object
```

Missing any link in this chain produces an access error even if the final
object-level grant looks correct.

## Module 5 vs Module 11

- **Module 5** creates the rideshare catalog, external location, schemas,
  and volumes in each learner’s own account (see that module’s README for
  privileges and the config cell). Creating the storage credential itself
  is documented outside this repository (course PDF).
- **Module 11** governs those **existing** objects (managed vs external,
  grants, ownership, credentials, least privilege) — it does not recreate
  the Module 5 setup.

## The course author's role

The course author can create and manage all Unity Catalog objects
(catalogs, schemas, managed tables, external tables, volumes, external
locations, storage credentials, grants) and is not blocked by any of this.
Module 5’s supported path assumes learners can create catalogs and
external locations in **their own** metastore. Learners without those
privileges cannot complete Module 5 setup as written.

## Minimum-privilege documentation pattern

Every module `README.md` that requires specific privileges beyond basic
workspace access documents them in a short "Minimum privileges required"
section, using this shape:

```markdown
## Minimum privileges required

- Unity Catalog: `USE CATALOG` on `<catalog>`, `USE SCHEMA` on `<schema>`,
  `SELECT` on `<table(s)>`
- Databricks workspace: `CAN ATTACH TO` (or `CAN RESTART`) on the compute
  used in this module
- Azure RBAC: none beyond standard workspace access (only note this if a
  module genuinely requires an Azure-level role)
```

Only list what that specific module's examples actually require — do not
restate the full catalog/schema hierarchy at every level unless it's
genuinely necessary context. Module 5 lists CREATE privileges and Azure
RBAC on the learner’s storage because Notebook 01 creates platform
objects.

## What this file does not cover

- Compute selection/validation rules — see `compute-validation-policy.md`.
- Actual catalog/schema/volume names — defined in
  `docs/data/dataset-overview.md` for the rideshare course objects.
- Module 5 Notebooks 01 and 99 use a Python **config cell** for Azure
  storage account, container, storage credential, and ADLS folder
  (author defaults; learners overwrite). That config cell, rather than
  widgets, is the Module 5 parameterization mechanism. Author defaults must
  follow the **Permitted author defaults** boundary in
  @docs/standards/coding-standards.md. Course UC object names
  (`rideshare_dev`, etc.) stay fixed per dataset-overview.