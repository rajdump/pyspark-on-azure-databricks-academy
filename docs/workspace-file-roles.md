# Workspace File Roles and Responsibilities

A reference map of every file and folder in the
**pyspark-on-azure-databricks-academy** repository, grouped by function.

---

## Top-Level Governance & Navigation

| File | Role |
|------|------|
| `README.md` | Learner-facing overview: audience, technical baseline (DBR 17.3 LTS, Spark 4.0, Python 3.12), development workflow, and entry points |
| `COURSE_MODULES.md` | Canonical roadmap: module numbers, purposes, prerequisites, status (Not Started / Started / Complete). Phases I–V, Modules 1–20 |
| `AGENTS.md` | Always-on agent routing context; points to canonical docs rather than duplicating them; enforces guardrails (no auto-updates, no fabricated results) |

---

## Standards & Process (`docs/standards/`)

| File | Role |
|------|------|
| `notebook-authoring-checklist.md` | Readiness preconditions and authoring workflow for scaffolding learner notebooks |
| `notebook-writing.md` | Narrative and pedagogical structure inside each notebook |
| `coding-standards.md` | PySpark/Python style rules |
| `naming-conventions.md` | `NN - Descriptive Title` module/notebook naming |
| `compute-validation-policy.md` | How to select and validate compute per module |
| `permissions-and-governance.md` | Unity Catalog privilege requirements |
| `teaching-guidelines.md` | Pedagogical principles and tone |

---

## Dataset Contract (`docs/data/`)

| File | Role |
|------|------|
| `dataset-overview.md` | Full schema, join keys, physical layout for the rideshare dataset (`trip`, `trip_time`, `payment`, `zone_lookup`, `drivers`) |

---

## Validation Evidence (`docs/validation/`)

One file per completed module (Modules 1–9 present). Records Azure Databricks
runtime results; edited only when the author supplies actual output.

---

## Source Data (`data/raw/`)

Raw rideshare files used in Module 5+ for file-landing exercises:

- `avro/`
- `csv/`
- `json/`
- `parquet/`
- `xml/`

---

## Module Folders (`01 - ...` through `09 - ...`)

Each module folder contains:

- Learner `.py` notebooks (Databricks source format)
- A `README.md` with detailed module design, notebook sequence, and prerequisites

---

## Cursor Tooling (`.cursor/`)

### Rules (`.cursor/rules/`)

| File | Role |
|------|------|
| `course-authoring.mdc` | Rule for general course authoring context |
| `learner-notebooks.mdc` | Rule for learner notebook scaffolding |
| `notebook-command-output.mdc` | Rule for handling notebook command output |

Each `.mdc` file declares its own attachment behavior in frontmatter.

### Commands (`.cursor/commands/`)

| File | Role |
|------|------|
| `new-lesson.md` | Slash command to scaffold a new lesson |
| `write-lesson.md` | Slash command to author lesson content |
| `validate-notebook.md` | Slash command to validate a notebook |
| `review-module.md` | Slash command to review an entire module |

---

## Project Configuration

| File | Role |
|------|------|
| `pyproject.toml` | Declares dev dependencies (`ruff`, `mypy`, `pytest`) managed by `uv` |
| `uv.lock` | Resolved/pinned dependency versions |
| `.editorconfig` | Cross-editor formatting rules |
| `.cursorignore` | Paths Cursor should ignore |
| `.gitignore` | Paths Git should ignore |
| `.env.example` | Template for environment variables |

---

## Other Folders

| Folder | Role |
|--------|------|
| `Workspace/Users/` | Mirrors a Databricks workspace path (Git folder alignment) |
| `cursor_ecosystem/` | Supplementary Cursor tooling/notes |
| `vault/` | Personal reference vault |
| `take_notes/` | Personal note-taking space |

---

## Reading Order (Recommended)

1. `README.md` — orientation and technical baseline
2. `COURSE_MODULES.md` — roadmap and module status
3. Target module's `README.md` — detailed design for the module you're working on
4. `docs/data/dataset-overview.md` — dataset contract
5. `docs/standards/notebook-authoring-checklist.md` — before writing any notebook
6. `docs/standards/coding-standards.md` — code style
7. `docs/standards/notebook-writing.md` — narrative structure
8. `AGENTS.md` — agent guardrails and routing
