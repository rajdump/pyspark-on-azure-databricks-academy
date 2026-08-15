# Naming Conventions

Canonical owner of all folder, file, and object naming rules for this
repository. Referenced by `.cursor/rules/course-authoring.mdc`, `/new-lesson`,
`/write-lesson`, `/validate-notebook`, and `/review-module` — do not duplicate
this content elsewhere. Shared read list:
@docs/standards/notebook-authoring-checklist.md.

## Module folders

Format: `NN - Descriptive Title` — zero-padded two-digit number, space,
hyphen, space, Title Case words separated by spaces.

```
01 - Azure Databricks and Spark Foundations/
02 - DataFrame Fundamentals/
```

- Zero-pad to two digits (`01`, not `1`) so folders sort correctly.
- Preserve product/technology capitalization: **PySpark**, **SQL**,
  **UDFs**, **Delta Lake**, **Unity Catalog**.
- No kebab-case or snake_case for learner-facing folder names.
- Quote paths containing spaces in terminal commands, e.g.
  `cd "01 - Azure Databricks and Spark Foundations"`.

## Notebook files

Format: `NN - Descriptive Title.py` — numbered per module, same casing
rules as folders.

```
01 - Azure Databricks and Spark Foundations/
├── README.md
├── 01 - Introduction to Azure Databricks.py
└── 02 - Apache Spark and PySpark.py
```

Always identify a notebook by **both** its module and its own title in
prose, references, and validation records — never "Notebook 02" alone.
Example: "`02 - Apache Spark and PySpark.py` in
`01 - Azure Databricks and Spark Foundations`".

## Internal documentation files

Files under `docs/standards/`, `docs/data/`, and `docs/validation/` use
kebab-case, lowercase, `.md`: e.g. `coding-standards.md`,
`dataset-overview.md`. These are author-facing, not learner-facing, so they
follow ordinary developer-documentation convention rather than the
Title Case rule above. `docs/validation/` files are the one exception —
they use the same `NN - Module Title.md` pattern as module folders, because
they must identify a specific module unambiguously.

## Cursor configuration files

- Rule files: `.cursor/rules/<scope>.mdc`, lowercase kebab-case
  (`learner-notebooks.mdc`, `course-authoring.mdc`).
- Command files: `.cursor/commands/<command-name>.md` — the filename **is**
  the slash command name (e.g. `new-lesson.md` → `/new-lesson`,
  `write-lesson.md` → `/write-lesson`).

## Python identifiers

Standard PEP 8 conventions: `snake_case` for modules, functions, and
variables; `PascalCase` for classes; `UPPER_SNAKE_CASE` for constants. Full
non-naming coding rules live in `coding-standards.md` — this file is the
sole normative owner of identifier naming.

## Unity Catalog objects

Catalogs, schemas, tables, and volumes are created and named by the course
author as each module needs them — no fixed names are prescribed here. When
naming them, prefer clear, environment-aware patterns (e.g. separating a
learning/dev catalog from anything resembling production) and avoid
embedding personal identifiers. Do not commit real catalog or schema names
to public-facing files if they reveal personal workspace details.

Course catalog, schema, and volume names for the rideshare dataset are
defined in `docs/data/dataset-overview.md` — use those for learner
notebooks rather than inventing alternate names. Azure storage account,
container, and storage credential names vary per learner and belong in the
Module 5 config cell (not as alternate UC object names).
