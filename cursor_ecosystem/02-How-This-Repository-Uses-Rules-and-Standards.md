# How This Repository Uses Rules and Standards

[Agents and Cursor Rules](01-Agents-and-Cursor-Rules.md) explains the general mechanism behind `AGENTS.md`, Cursor rules, canonical documents, and commands.

This file shows how this repository uses that mechanism.

---

## How the repository is organized

The repository gives each layer one job:

| Layer | Role in this repository |
| --- | --- |
| `AGENTS.md` | Repository-wide constraints and boundaries |
| `.cursor/rules/*.mdc` | Extra instructions for matching work |
| `docs/standards/` and `docs/data/` | Detailed rules and reference information |
| `.cursor/commands/` | Explicit lesson workflows |

The flow is:

```text
USER REQUEST
    ↓
AGENTS.md
    ↓
matching Cursor rule, when applicable
    ↓
required standards and project documents
    ↓
agent performs the work
```

A slash command adds another layer only when the user explicitly invokes that workflow.

---

## `AGENTS.md` is the repository-wide contract

The root `AGENTS.md` contains the constraints that should remain available across repository work.

For this course, those include:

- batch-only PySpark data engineering
- Databricks source `.py` notebooks, never `.ipynb`
- no Structured Streaming, Auto Loader, streaming tables, or ML content

`AGENTS.md` also points to the documents that own deeper information:

| Need | Source of truth |
| --- | --- |
| Course roadmap and status | `COURSE_MODULES.md` |
| Module-specific design | the module's `README.md` |
| Schemas, join keys, and physical layout | `docs/data/dataset-overview.md` |
| Detailed authoring and engineering rules | `docs/standards/` |

Two actions remain author-owned:

- updating status in `COURSE_MODULES.md`
- writing runtime validation evidence under `docs/validation/`

Agents must not perform either action as a side effect of lesson work.

---

## Standards own the detail

Detailed project rules live in `docs/standards/` and `docs/data/`.

| File | Owns |
| --- | --- |
| `notebook-authoring-checklist.md` | Command-specific read manifests and notebook acceptance bars |
| `notebook-writing.md` | Notebook structure and formatting |
| `teaching-guidelines.md` | Pedagogy and explanation style |
| `coding-standards.md` | Python and PySpark conventions |
| `naming-conventions.md` | Folder, file, and notebook names |
| `compute-validation-policy.md` | Compute selection and validation order |
| `permissions-and-governance.md` | Azure RBAC, workspace permissions, Unity Catalog privileges, and minimum-privilege guidance |
| `dataset-overview.md` | Schemas, join keys, and physical layout |

The Cursor rules and commands point to these documents instead of copying their detailed content.

The checklist loads `compute-validation-policy.md` and
`permissions-and-governance.md` only for workflows where their conditions
apply.

---

## Cursor rules used by this repository

The repository has three `.mdc` rules:

| Rule | Mode | Used for |
| --- | --- | --- |
| `learner-notebooks.mdc` | Apply to Specific Files | Numbered learner `.py` notebooks |
| `course-authoring.mdc` | Apply to Specific Files | Root README, roadmap, and numbered module READMEs |
| `notebook-command-output.mdc` | Apply Intelligently | Response format for the five authoring commands |

### `learner-notebooks.mdc`

This rule matches:

```text
[0-9][0-9] - */*.py
```

For example:

```text
08 - Aggregations and Window Functions/06 - Running Totals and Lag and Lead.py
```

When the rule attaches during a slash command, it defers to that command's
manifest in `notebook-authoring-checklist.md`. For an ad-hoc edit, it tells
the agent to read the applicable scaffold or full-lesson manifest with read
tools. This avoids eagerly loading every canonical standard for every
notebook task.

The selected manifest also routes the agent to the target module README and
the relevant canonical standards.

### `course-authoring.mdc`

This rule matches:

```text
README.md
COURSE_MODULES.md
[0-9][0-9] - */README.md
```

So it covers the repository root `README.md`, the roadmap, and numbered module READMEs.

For example, `08 - Aggregations and Window Functions/README.md` matches. `vault/README.md` does not.

For ad-hoc work, the rule routes the agent to `teaching-guidelines.md`,
`naming-conventions.md`, and—when editing a module README—
`readme-authoring.md`. During `/write-module-readme`, it defers to the
command's scoped reads.

### `notebook-command-output.mdc`

This rule has a description and no glob, so its mode is **Apply Intelligently**.

Its description covers the response format for:

```text
/write-module-readme
/new-lesson
/write-lesson
/validate-notebook
/review-module
```

Cursor may attach the rule when that description is relevant.

All five commands also explicitly `@`-reference it. The `@` reference is
explicit inclusion; it is not another rule mode.

### When two glob rules match

If the Agent context contains both a numbered learner `.py` file and a numbered module `README.md`, both file patterns match.

Cursor may therefore attach both `learner-notebooks.mdc` and `course-authoring.mdc` to the same request.

---

## What happens when editing a learner notebook

Suppose this notebook is in the Agent context:

```text
08 - Aggregations and Window Functions/06 - Running Totals and Lag and Lead.py
```

The flow is:

```text
AGENTS.md
    ↓
learner-notebooks.mdc attaches
    ↓
agent reads the applicable command or ad-hoc manifest
    ↓
module README and scoped standards are opened
    ↓
agent performs the notebook work
```

If no matching numbered `.py` file is in the Agent context, the notebook glob does not attach. `AGENTS.md` still applies.

---

## What happens when editing course documentation

For the root `README.md`, `COURSE_MODULES.md`, or a numbered module `README.md`:

```text
AGENTS.md
    ↓
course-authoring.mdc attaches
    ↓
agent follows the command's scoped reads, or the ad-hoc list
    ↓
agent performs the documentation work
```

This keeps notebook instructions separate from README and roadmap instructions.

---

## Commands start lesson workflows

A rule attaching does not run a command.

The user must explicitly invoke the workflow.

| Command | Purpose |
| --- | --- |
| `/write-module-readme` | Create a design-complete module README without inventing unresolved design decisions |
| `/new-lesson` | Scaffold a skeleton notebook; do not write the full lesson |
| `/write-lesson` | Use an existing skeleton and a sibling notebook for voice; write the full runnable lesson |
| `/validate-notebook` | Report authoring issues only; do not write files |
| `/review-module` | Review the whole module folder rather than one notebook |

All five commands `@`-reference `notebook-command-output.mdc`. The four
notebook commands also `@`-reference
`docs/standards/notebook-authoring-checklist.md`;
`/write-module-readme` declares its own scoped reads.

The checklist's **Conditional reads** route `/write-lesson`,
`/validate-notebook`, and `/review-module` to
`compute-validation-policy.md` and `permissions-and-governance.md` when
their triggers apply.

---

## The repository model

```text
Broad repository constraints
    → AGENTS.md

Learner notebook instructions
    → learner-notebooks.mdc

README and roadmap instructions
    → course-authoring.mdc

Detailed rules and reference information
    → docs/standards/ and docs/data/

Lesson workflows
    → .cursor/commands/
```

This repository has no `alwaysApply: true` project rule and no Apply Manually project rule.

It uses two Apply to Specific Files rules and one Apply Intelligently rule.

Standalone Codex can use `AGENTS.md`, but it does not interpret Cursor `.mdc` rules or Cursor commands. A repository-wide constraint that must also apply outside Cursor should therefore live in `AGENTS.md`, not only in a Cursor-specific rule.
