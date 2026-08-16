# Naming Conventions

This file is the canonical owner of folder, file, identifier, and Unity
Catalog object naming rules for this repository.

Direct readers: `docs/standards/notebook-authoring-checklist.md`,
`docs/standards/coding-standards.md`, `.cursor/rules/course-authoring.mdc`,
and `/write-module-readme`. Notebook commands other than
`/write-module-readme`, plus `.cursor/rules/learner-notebooks.mdc`, receive
these rules through the checklist.

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
└── 02 - Apache Spark Architecture and PySpark.py
```

Always identify a notebook by **both** its module and its own title in
prose, references, and validation records — never "Notebook 02" alone.
Example: "`02 - Apache Spark Architecture and PySpark.py` in
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
non-naming coding rules live in `docs/standards/coding-standards.md`. This
file remains the sole owner of identifier naming.

## Unity Catalog objects

For objects not defined by the course, prefer clear, environment-aware names
that distinguish learning or development objects from production objects.
Do not embed personal identifiers.

The rideshare course's fixed catalog, schema, table, and volume names are
defined in `docs/data/dataset-overview.md`. Learner notebooks must use those
names rather than inventing alternatives. Azure storage accounts,
containers, and storage credentials vary per learner;
`01 - Unity Catalog Volumes and Data Landing.py` in
`05 - Reading, Writing, and Schemas` owns those inputs, not this naming
standard.

## Does not cover

- Code style, security, or committed-value rules — see
  `docs/standards/coding-standards.md`.
- The rideshare dataset's fixed object names and paths — see
  `docs/data/dataset-overview.md`.
