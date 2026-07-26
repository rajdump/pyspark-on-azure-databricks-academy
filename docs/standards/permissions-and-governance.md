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
| **Databricks workspace permissions** | Access to objects inside the Databricks workspace UI/API (compute, jobs, notebooks, workspace folders) | `CAN USE` on a cluster, `CAN MANAGE` on a job |
| **Unity Catalog privileges** | Access to governed data objects (catalogs, schemas, tables, volumes) | `USE CATALOG`, `USE SCHEMA`, `SELECT` on a table |

A learner can have full Databricks workspace access and still be unable to
query a table because Unity Catalog privileges are missing — and vice
versa. Azure RBAC is effectively invisible to most learners day-to-day,
since the course author manages it, but it's worth naming so learners
understand it's a separate layer if they ever administer their own
workspace.

## Unity Catalog privilege chaining

Unity Catalog privileges are hierarchical — reading a table requires **all**
of the following, not just a grant on the table itself:

```
USE CATALOG <catalog>  -->  USE SCHEMA <schema>  -->  SELECT (or other object-level privilege) on the object
```

Missing any link in this chain produces an access error even if the final
object-level grant looks correct.

## The course author's role

The course author can create and manage all Unity Catalog objects
(catalogs, schemas, managed tables, external tables, volumes, external
locations, storage credentials, grants) and is not blocked by any of this.
**Do not assume every learner has the same permissions as the course
author** — a learner following along in their own workspace may have a
more restricted role.

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
genuinely necessary context.

## What this file does not cover

- Compute selection/validation rules — see `compute-validation-policy.md`.
- Actual catalog/schema names — those are hardcoded by the author,
  introduced progressively per module, and are not part of this policy
  document.
