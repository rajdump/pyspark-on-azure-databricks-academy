# Workspace files and usage

Author-only reference. This is **not** a learner notebook.

This repo is a **course authoring workspace**, not a Spark application.
Learner notebooks live in numbered module folders (`01`–`09` so far).
Everything else supports authoring, the shared rideshare dataset, local
tooling, and Databricks Git sync.

There is no `src/` package and no `tests/` folder yet. Those are planned
for later modules (13 and 16).

## How the pieces fit together

```text
Author in Cursor
  README.md + COURSE_MODULES.md     → what the course is
  docs/standards + .cursor/         → how to write notebooks
  docs/data + data/raw              → what data notebooks use
  NN - Module/README.md             → that module's lesson plan
        ↓
  GitHub (source of truth)
        ↓
  Azure Databricks Git folder runs notebooks

  cursor_ecosystem/                 → author notes on Cursor routing
  vault/ + take_notes/              → private tracking
```

**If you are a learner:** start at root `README.md` → `COURSE_MODULES.md`
→ a module `README.md` → its notebooks. You only need `data/raw` once you
hit Module 5.

**If you are authoring:** `AGENTS.md` → [02-How-This-Repository-Uses-Rules-and-Standards.md](02-How-This-Repository-Uses-Rules-and-Standards.md)
for routing → `docs/standards/` → module `README.md` → slash commands.
Use `vault/` for personal tracking, not as the public course spec.

Author reading order: root `README.md` → `COURSE_MODULES.md` → target
module `README.md` → this catalog as needed → `02` before notebook
commands. Do not use a `docs/` file-role duplicate; this file is the
workspace catalog.

## 1. Course source of truth (root)

These are the canonical course docs. Status and roadmap live here, not in
notebooks.

| File | Usage |
|---|---|
| `README.md` | Learner-facing overview: who the course is for, DBR 17.3 LTS baseline, Git → Databricks workflow, where to start |
| `COURSE_MODULES.md` | **Author-owned** 20-module roadmap: purpose, topics, prerequisites, production relevance, Complete / Started / Not Started. Agents must not update status here unless asked |
| `AGENTS.md` | Pointer file for Cursor/agents: what the project is, where standards live, what not to auto-write |

## 2. Shared dataset

The same small rideshare dataset (`trip`, `trip_time`, `payment`,
`zone_lookup`, plus nested `drivers`) threads through every module.

### Schema and pipeline contracts

| File | Usage |
|---|---|
| `docs/data/dataset-overview.md` | Canonical schemas, join keys, row counts, Volume paths, and how Modules 5–8 transform landing → curated → managed tables → KPIs. Notebooks should follow this, not invent schemas |
| `docs/data/dataset-guide.md` | Human-facing explanation of the same model: keys-only ER diagram, stage-level pipeline flow, a per-module diagram of what Modules 5–9 read and create, and why row counts and NULLs change. Explanatory only — owns no facts and appears in no read manifest |

### Physical files (`data/raw/`)

Copied onto a Unity Catalog Volume in Module 5. Intentionally small
(~100 rows) for fast iteration.

| Path | Usage |
|---|---|
| `data/raw/csv/` | `trip.csv`, `trip_time.csv`, `payment.csv`, `zone_lookup.csv` plus **controlled-bad** files (`bad_trip_data.csv`, `bad_payment_data.csv`) for schema/quality teaching |
| `data/raw/json/` | Same four tables as JSON (Module 5 JSON reads) |
| `data/raw/parquet/` | Same four tables as Parquet (binary; Cursor ignores them via `.cursorignore`) |
| `data/raw/avro/` | `payment.avro` (+ `.crc`) for Avro reads |
| `data/raw/xml/` | `drivers.xml` — nested supplementary dataset used from Module 5/6 onward |

## 3. Authoring standards (`docs/standards/`)

These are the writing rules. Slash commands and Cursor rules **point
here**; they do not duplicate the content.

| File | Usage |
|---|---|
| `notebook-authoring-checklist.md` | Per-command reads and acceptance bars for notebook authoring and review |
| `notebook-writing.md` | Databricks source `.py` format: header, `# COMMAND ----------`, cell structure |
| `teaching-guidelines.md` | Pedagogy: how to explain, what to show, what not to skip |
| `coding-standards.md` | Python / PySpark conventions in notebooks |
| `naming-conventions.md` | `NN - Descriptive Title` folders and notebooks |
| `readme-authoring.md` | Module README structure and design-complete definition |
| `compute-validation-policy.md` | Which compute to use and the Standard → serverless validation order |
| `permissions-and-governance.md` | Azure RBAC vs workspace permissions vs Unity Catalog privileges; “minimum privileges” pattern for module READMEs |
| `standards-authoring.md` | Structure, language, and cross-reference conventions for standards; no lesson consumers |

## 4. Module design (not the `.py` notebooks)

Each numbered folder has a `README.md` that owns **that module’s**
objectives, notebook order, exercises, dataset notes, and privileges. It
must not copy the full roadmap.

| Path | Usage |
|---|---|
| `01` … `09 - …/README.md` | Detailed design + notebook navigation for each complete module |

Module 7 also has approved build specs (not lesson text):

| Path | Usage |
|---|---|
| `07 …/requirements/BRD.md` | Business requirements for `trip_enriched` and `trip_driver_assignment` |
| `07 …/requirements/trip_enriched_mapping.md` | Column-level source-to-target mapping |
| `07 …/requirements/trip_driver_assignment_mapping.md` | Same for the driver-assignment table |

## 5. Cursor authoring automation (`.cursor/`)

Used when writing course content in Cursor. Learners running notebooks
in Databricks do not need these.

### Slash commands (`.cursor/commands/`)

| Command file | What it does |
|---|---|
| `write-module-readme.md` | Create a design-complete module README; own scoped reads, not the checklist |
| `new-lesson.md` | Create a notebook scaffold from the module README (Scaffold manifest) |
| `write-lesson.md` | Turn a scaffold into a full lesson (Full-lesson manifest) |
| `validate-notebook.md` | Authoring-quality review of one notebook (not Databricks runtime) |
| `review-module.md` | Whole-module completeness/consistency check (lighter than per-notebook validation) |

Every command file follows `docs/standards/command-authoring.md` (fixed block
order, scoped reads, guards, verify, boundaries). When you edit a command
with Cursor AI, `.cursor/rules/command-authoring.mdc` should attach and
route the agent to that standard. For manual edits, read the standard first,
then run `python3 scripts/check_doc_references.py`.

### Rules (`.cursor/rules/`)

| File | When it applies |
|---|---|
| `command-authoring.mdc` | Glob `.cursor/commands/*.md` — read `docs/standards/command-authoring.md` |
| `learner-notebooks.mdc` | Glob `[0-9][0-9] - */*.py` — defer to the active command manifest, or route ad-hoc edits |
| `course-authoring.mdc` | Glob on root `README.md`, `COURSE_MODULES.md`, and numbered module READMEs |
| `notebook-command-output.mdc` | No glob (Apply Intelligently); `@`-included by all five commands to keep replies short |

`.cursorignore` keeps binary Parquet/Avro, `uv.lock`, and `.venv/` out of
AI context.

## 6. Local Python tooling (does **not** run Spark)

Spark, Delta, and Unity Catalog run only in Azure Databricks.

| File | Usage |
|---|---|
| `pyproject.toml` | Declares `uv` + `ruff` / `mypy` / `pytest` for local format/lint/type/non-Spark tests. Empty runtime `dependencies` |
| `uv.lock` | Pinned versions from `uv sync` (generated; gitignored from AI context) |
| `scripts/check_doc_references.py` | After editing `.cursor/commands/`, `.cursor/rules/`, or `AGENTS.md`, run `python3 scripts/check_doc_references.py`. It fails when a `[[Section name]]` pointer or a `` `path` `` / `@path` no longer resolves — for example, after renaming a heading in `docs/standards/` or moving a referenced file. Scans those sources only; does not check command block structure (`docs/standards/command-authoring.md` owns that). Standard library only; `0 unresolved` means pass. |
| `.editorconfig` | Indent, charset, newlines for editors |
| `.cursorignore` | Paths Cursor should keep out of AI context (binary Parquet/Avro, `uv.lock`, `.venv/`) |
| `.gitignore` | Ignores `.venv`, caches, `.env`, `.databricks/`, editor junk |
| `.env.example` | Template for optional `DATABRICKS_HOST` / `DATABRICKS_TOKEN` for CLI/Connect. Copy to gitignored `.env`; never put real secrets in the template |

`pytest` is configured with `testpaths = ["tests"]`, but **`tests/` does
not exist yet**.

## 7. Author notes (not learner-facing)

These folders are author-only. They are not learner notebooks and not
normative standards.

### Cursor ecosystem (`cursor_ecosystem/`)

| File | Usage |
|---|---|
| [01-Agents-and-Cursor-Rules.md](01-Agents-and-Cursor-Rules.md) | General Cursor mechanism: agents, `AGENTS.md`, rule modes, commands |
| [02-How-This-Repository-Uses-Rules-and-Standards.md](02-How-This-Repository-Uses-Rules-and-Standards.md) | Living routing model for this repo (paths A/B/C, `@` vs backtick) |
| [03-Workspace Files and Usage.md](03-Workspace%20Files%20and%20Usage.md) | This catalog — what each workspace path is for |
| [04-Markdown-Context-Routing-Optimization.md](04-Markdown-Context-Routing-Optimization.md) | Dated routing-optimization report (measurements, test log) |
| [FUTURE-TOPICS.md](FUTURE-TOPICS.md) | Backlog of Cursor topics intentionally kept out of File 01 |

### Obsidian vault (`vault/`)

Open **this folder** as the Obsidian vault, not the repo root. Course
source of truth stays outside so Git/Databricks/Cursor paths stay stable.

| File | Usage |
|---|---|
| `vault/README.md` | How to open the vault and what belongs there |
| `vault/home.md` | Dashboard: current module, links into the repo |
| `vault/progress.md` | Personal progress tracker (does not override `COURSE_MODULES.md`) |
| `vault/decisions.md` | Decision log with links back to canonical docs |
| `vault/.obsidian/` | Obsidian app settings for this vault |

### Scratch notes (`take_notes/`)

| File | Usage |
|---|---|
| `to_dos.md` | Personal author to-dos and notes |

## 8. Generated / local / accidental (usually ignore)

| Path | Usage |
|---|---|
| `.venv/`, `.ruff_cache/`, `.mypy_cache/`, `.pytest_cache/` | Local tool caches (gitignored) |
| `.databricks/` | Databricks CLI / Asset Bundle local state (gitignored) |
| `.vscode/` | Editor settings (gitignored) |
| `.obsidian/` at **repo root** | Extra Obsidian config; the intended vault is `vault/` |
| `Untitled.canvas` | Empty leftover canvas file |
| `Workspace/Users/…/.assistant_instructions.md` | Databricks workspace / Git-folder artifact, not course content |
