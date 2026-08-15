# How This Repository Uses Rules and Standards

[Agents and Cursor Rules](01-Agents-and-Cursor-Rules.md) defines agents,
`AGENTS.md`, `.mdc` rules, and the four modes. This file applies that
mechanism here.

## Architecture

This repository keeps a small always-on contract, attaches Cursor rules only
for matching work, and keeps detailed standards in one place. Slash commands
run the lesson workflows.

```text
USER REQUEST
      │
      ▼
 AGENTS.md                 always on (every agent)
      │
      ├─ numbered learner .py in Agent context
      │         → learner-notebooks.mdc
      │
      ├─ root README, COURSE_MODULES.md, or module README in Agent context
      │         → course-authoring.mdc
      │
      └─ slash command
                → /new-lesson, /write-lesson,
                  /validate-notebook, /review-module
```

The three `.cursor/rules/` files are in Rule cards. The four commands are in
Command workflows.

## `AGENTS.md` in this repository

The root `AGENTS.md` is the global contract. This is a batch-only PySpark
course, authored as Databricks source `.py` notebooks, never `.ipynb`. No
Structured Streaming, Auto Loader, streaming tables, or ML content. It
points at `COURSE_MODULES.md`, the current module `README.md`,
`docs/data/dataset-overview.md`, and `docs/standards/` instead of copying
them.

Two actions stay author-owned: status in `COURSE_MODULES.md`, and runtime
evidence under `docs/validation/`. Agents must not fill those in as a side
effect of lesson work.

## Standards

Canonical detail lives in `docs/standards/` and
`docs/data/dataset-overview.md`.

| File | Owns |
| --- | --- |
| `notebook-authoring-checklist.md` | Shared read list for notebook work |
| `notebook-writing.md` | Notebook structure and formatting |
| `teaching-guidelines.md` | Pedagogy and explanation style |
| `coding-standards.md` | Python / PySpark conventions |
| `naming-conventions.md` | Folder, file, and notebook names |
| `compute-validation-policy.md` | Compute selection and validation order |
| `permissions-and-governance.md` | Azure RBAC vs workspace permissions vs Unity Catalog; minimum-privilege pattern |
| `dataset-overview.md` | Schemas, join keys, and physical layout |

`compute-validation-policy.md` and `permissions-and-governance.md` are extra
reads for `/validate-notebook` and `/review-module` when relevant. They are
not in `learner-notebooks.mdc`'s `@` list.

## Rule cards

The subsections below are cards. A card states what a rule matches and what
it references. It is not a sequence of steps. End-to-end after the cards is
the sequence; those sections cite the cards instead of repeating globs and
`@` lists.

### `learner-notebooks.mdc`

**Mode:** Apply to Specific Files (`alwaysApply: false`, glob set).

**Matches:** `[0-9][0-9] - */*.py` — a `.py` file one level inside a
numbered module folder, not any `.py` in the repository.

**`@`-references:** `notebook-authoring-checklist.md`,
`notebook-writing.md`, `teaching-guidelines.md`, `coding-standards.md`,
`naming-conventions.md`, `dataset-overview.md`.

**Opened, not `@`-referenced:** the `README.md` in the same numbered module
folder.

### `course-authoring.mdc`

**Mode:** Apply to Specific Files.

**Matches:**

- `README.md` — repository root only
- `COURSE_MODULES.md`
- `[0-9][0-9] - */README.md` — a numbered module README

`vault/README.md` matches none of those.

**`@`-references:** `teaching-guidelines.md` and `naming-conventions.md`.

**Points at:** `permissions-and-governance.md` for the minimum-privilege
pattern in a module README.

### `notebook-command-output.mdc`

**Mode:** Apply Intelligently — a description, no glob, `alwaysApply: false`.
Not Apply Manually.

**Description:** minimal response format for `/new-lesson`, `/write-lesson`,
`/validate-notebook`, `/review-module`.

All four commands also `@`-reference it. That `@` is the reliable path.

### When both glob rules attach

If the same request has a numbered learner `.py` and a module `README.md` in
the Agent context, both globs match. Cursor may attach
`learner-notebooks.mdc` and `course-authoring.mdc` together.

## End-to-end

### Editing a learner notebook

You ask Cursor to edit a numbered notebook that is in the Agent context:

```text
08 - Aggregations and Window Functions/06 - Running Totals and Lag and Lead.py
```

`AGENTS.md` applies (see `AGENTS.md` in this repository). Because that `.py`
is in the Agent context, `learner-notebooks.mdc` attaches. See the
`learner-notebooks.mdc` card for what it `@`-references and what it tells
the agent to open.

If the request names a lesson but no numbered `.py` is in the Agent context,
the notebook glob does not attach. `AGENTS.md` still applies.

### Editing a course README

You ask Cursor to edit the root `README.md`, `COURSE_MODULES.md`, or a
numbered module `README.md`.

`AGENTS.md` applies. Because that path is in the Agent context,
`course-authoring.mdc` attaches. See the `course-authoring.mdc` card for
what it `@`-references.

## Command workflows

A rule attaching is not a command running.

Each of `/new-lesson`, `/write-lesson`, `/validate-notebook`, and
`/review-module` `@`-references `notebook-command-output.mdc` and
`docs/standards/notebook-authoring-checklist.md`. `/validate-notebook` and
`/review-module` also pull `compute-validation-policy.md` and
`permissions-and-governance.md` when relevant.

| Command | Difference |
| --- | --- |
| `/new-lesson` | Scaffolds a skeleton notebook; does not write the full lesson |
| `/write-lesson` | Needs an existing skeleton and a sibling notebook for voice; writes the full runnable lesson |
| `/validate-notebook` | Reports authoring issues only; does not write files |
| `/review-module` | Covers the whole module folder, not one notebook |

## Decision guide for this repository

When this repository must choose a home for an instruction, use the modes
in Frontmatter and the four modes in
[Agents and Cursor Rules](01-Agents-and-Cursor-Rules.md). The choices
already made here:

- Hard stops go in `AGENTS.md`.
- There is no `alwaysApply: true` project rule.
- There is no Apply Manually rule.
- Response format for the four commands is Apply Intelligently
  (`notebook-command-output.mdc`) plus each command `@`-referencing that
  rule.
- Glob rules split learner notebooks (`learner-notebooks.mdc`) from READMEs
  and the roadmap (`course-authoring.mdc`).

Codex receives `AGENTS.md` but not `.mdc` rules or Cursor commands. See
Cursor rules are contextual and Commands start workflows in
[Agents and Cursor Rules](01-Agents-and-Cursor-Rules.md).
