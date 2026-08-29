# Permissions and Governance

This file is the canonical owner of the distinction between Azure RBAC,
Databricks workspace permissions, and Unity Catalog privileges. It also owns
the minimum-privilege documentation pattern for module `README.md` files.

Direct readers: `docs/standards/notebook-authoring-checklist.md`,
`docs/standards/readme-authoring.md`, and `/write-module-readme`. Notebook
commands receive these rules through the checklist when permission guidance
is relevant.

## Three distinct permission systems

This course touches three distinct, independently evaluated permission
systems.
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

## Module 5 and Module 12 responsibilities

- **Module 5 — Reading, Writing, and Schemas** creates the rideshare catalog,
  external location, schemas, and volumes in each learner's own account.
  Its README owns the required privileges and setup inputs. Creating the
  storage credential itself is documented outside this repository.
- **Module 12 — Unity Catalog and Data Governance** governs those existing
  objects through grants, ownership, credentials, and least privilege. It
  does not recreate the Module 5 setup.

### Module 5 parameterization

`01 - Unity Catalog Volumes and Data Landing.py` and
`99 - Rideshare Project Cleanup and Reset.py` in
`05 - Reading, Writing, and Schemas` use a Python setup/config cell for the
learner's Azure storage account, container, storage credential, and ADLS
folder. They do not use widgets for those values. Committed defaults must
follow the [[Permitted author defaults]] section in
`docs/standards/coding-standards.md`. Fixed course Unity Catalog names, such
as `rideshare_dev`, remain defined by `docs/data/dataset-overview.md`.

## Author and learner privilege assumptions

The authoring baseline assumes the course author can create and manage the
Unity Catalog objects used by the lessons. Module 5's supported learner path
assumes learners can create catalogs and external locations in their own
metastore. Learners without those privileges cannot complete Module 5 setup
as written.

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
RBAC on the learner's storage because
`01 - Unity Catalog Volumes and Data Landing.py` in
`05 - Reading, Writing, and Schemas` creates platform objects.

## Does not cover

- Compute selection and validation rules — see
  `docs/standards/compute-validation-policy.md`.
- Actual catalog/schema/volume names — defined in
  `docs/data/dataset-overview.md` for the rideshare course objects.
- Security and safe committed defaults — see the [[Security and
  portability]] and [[Permitted author defaults]] sections in
  `docs/standards/coding-standards.md`.
