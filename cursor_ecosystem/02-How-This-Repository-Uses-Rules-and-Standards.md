# How This Repository Uses Rules and Standards

[Agents and Cursor Rules](01-Agents-and-Cursor-Rules.md) explains the general mechanism behind `AGENTS.md`, Cursor rules, canonical documents, and commands.

This file is the living routing model for **this repository**. Declared line-count measurements and test logs live in [Markdown Context Routing Optimization](04-Markdown-Context-Routing-Optimization.md).

---

## How the repository is organized

The repository gives each layer one job:

| Layer | Role in this repository |
| --- | --- |
| `AGENTS.md` | Repository-wide constraints and boundaries |
| `.cursor/rules/*.mdc` | Extra instructions for matching work |
| `docs/standards/` and `docs/data/` | Detailed rules and reference information |
| `.cursor/commands/` | Explicit lesson and README workflows |

After `AGENTS.md`, three overlays may apply. They are siblings, not a fixed sequence:

```text
USER REQUEST
    ↓
AGENTS.md
    ├── matching glob .mdc rule, when a matching path is in Agent context
    ├── slash command, when the user invokes it (@-includes + tool-reads)
    └── required standards and project documents (eager @ or tool-read)
    ↓
agent performs the work
```

A slash command can run with no glob rule attached. `/new-lesson` often does that when no numbered `.py` file is in Agent context yet.

---

## Three routing paths

| Path | Trigger | Routing authority |
| --- | --- | --- |
| A — Notebook commands | `/new-lesson`, `/write-lesson`, `/validate-notebook`, `/review-module` | Checklist manifests |
| B — README command | `/write-module-readme` | Its own read list (independent of the checklist) |
| C — Ad-hoc edit | No command; matching path in Agent context | `.mdc` glob rules → checklist or standalone list |

---

## `AGENTS.md` is the repository-wide contract

The root `AGENTS.md` contains the constraints that should remain available across repository work. Cursor and Codex agents use it. Databricks chat does not auto-load it.

It has five sections, ordered by what an agent needs first:

| Section | Role |
| --- | --- |
| **Hard constraints** | Batch-only scope, Databricks source `.py` notebooks and never `.ipynb`, no local Spark execution, and no invented facts |
| **Author-only writes** | The three writes an agent must not perform unsolicited |
| **Read for facts** | The numbered source-precedence chain |
| **Authoring workflows** | The five slash commands, plus the rules to load standards on demand and to never let prior chat replace a required read |
| **Local checks** | `uv`, `ruff`, and `mypy` commands, and which pre-existing findings to leave alone |

`AGENTS.md` states each constraint once and points to the documents that own deeper information:

| Need | Source of truth |
| --- | --- |
| Course roadmap and status | `COURSE_MODULES.md` |
| Module-specific design | the module's `README.md` |
| Schemas, join keys, and physical layout | `docs/data/dataset-overview.md` |
| Detailed authoring and engineering rules | `docs/standards/` |
| Learner overview and technical baseline | root `README.md` |

Deeper facts are not copied into `AGENTS.md`. It names the dataset document rather than listing tables, and names the root `README.md` rather than restating the runtime baseline or the Git-to-Databricks workflow.

**Read for facts** is the canonical home of source precedence. `vault/decisions.md` points to it instead of keeping a second copy, since `vault/` is itself context-only in that chain.

Two restrictions remain author-owned:

- updating status in `COURSE_MODULES.md`
- scaffolding learner notebooks only when the **Readiness precondition** in
  `docs/standards/notebook-authoring-checklist.md` is met

Agents must not perform either as a side effect of lesson work.

### Cross-file section references

The `.mdc` rules, the five commands, and `AGENTS.md` name another document's section explicitly:

| Form | Use |
| --- | --- |
| `[[Author-only writes]]` | the usual case |
| `[[readme-authoring#Learning objectives]]` | when a bare name would match two documents |
| `[[#Read for facts]]` | a heading in the same file |
| `[[file#Name\|label]]` | alias form, when the prose needs its own wording |

A bare name resolves only against the documents that file already names with `@path` or a backticked path, so a reference cannot point somewhere the reader was never told to read. It resolves to a heading whenever one exists anywhere; a bold label in the target counts only for names that are headings nowhere.

Ordinary `**bold**` is emphasis and is never a reference. Because references are matched by name, renaming a heading breaks every file pointing at it — `Author-only writes` alone is referenced by `learner-notebooks.mdc`, `course-authoring.mdc`, and all five commands. `scripts/check_doc_references.py` fails until those are updated, and also verifies every file path written in those files.

---

## Standards own the detail

Detailed project rules live in `docs/standards/` and `docs/data/`.

| File | Owns |
| --- | --- |
| `docs/standards/notebook-authoring-checklist.md` | Command-specific read manifests and notebook acceptance bars |
| `docs/standards/notebook-writing.md` | Notebook structure and formatting |
| `docs/standards/teaching-guidelines.md` | Pedagogy and explanation style |
| `docs/standards/coding-standards.md` | Python and PySpark conventions |
| `docs/standards/naming-conventions.md` | Folder, file, and notebook names |
| `docs/standards/readme-authoring.md` | Module README structure and design-complete definition |
| `docs/standards/compute-validation-policy.md` | Compute selection and validation order |
| `docs/standards/permissions-and-governance.md` | Azure RBAC, workspace permissions, Unity Catalog privileges, and minimum-privilege guidance |
| `docs/standards/standards-authoring.md` | Meta-rules for writing standards; no lesson consumers |
| `docs/data/dataset-overview.md` | Schemas, join keys, and physical layout |

The Cursor rules and commands point to these documents instead of copying their detailed content.

Dataset routing for notebook commands is **Dataset scope** in the checklist.
`/write-module-readme` selects the applicable dataset headings from its own
read list. Agents tool-read named headings in `docs/data/dataset-overview.md`;
they do not `@`-include that file whole.

`docs/data/dataset-guide.md` is the human-facing companion to that contract.
It explains the model, the pipeline story, and why row counts and NULLs
change, but it owns no facts and belongs in no read manifest. Learner-facing
links such as the root `README.md` intro point there; every agent, rule,
command, standard, module README, and notebook reference stays on
`dataset-overview.md`.

**Conditional reads** in the checklist load `compute-validation-policy.md` and `permissions-and-governance.md` for `/write-lesson`, `/validate-notebook`, and `/review-module` when those triggers apply. `/new-lesson` does not use that section. Module 5 setup/cleanup is Scaffold manifest item 8 (parameterization plus **Permitted author defaults**). `/write-module-readme` loads `permissions-and-governance.md` from its own list when the design needs privileges beyond basic workspace access.

---

## Cursor rules used by this repository

The repository has four `.mdc` rules:

| Rule | Mode | Used for |
| --- | --- | --- |
| `command-authoring.mdc` | Apply to Specific Files | `.cursor/commands/*.md` — routes to `docs/standards/command-authoring.md` |
| `learner-notebooks.mdc` | Apply to Specific Files | Numbered learner `.py` notebooks |
| `course-authoring.mdc` | Apply to Specific Files | Root README, roadmap, and numbered module READMEs |
| `notebook-command-output.mdc` | Apply Intelligently | Response format for the five authoring commands |

### `command-authoring.mdc`

This rule matches:

```text
.cursor/commands/*.md
```

When a command file is in Agent context, the rule tells the agent to read
`docs/standards/command-authoring.md` and follow its required block order.
It does not apply to manual edits with no AI.

### `learner-notebooks.mdc`

This rule matches:

```text
[0-9][0-9] - */*.py
```

For example:

```text
08 - Aggregations and Window Functions/06 - Running Totals and Lag and Lead.py
```

The glob attaches when a matching path is in Agent context, not only when that file is the active editor tab.

When the rule attaches during a slash command, it defers to that command's
manifest in `notebook-authoring-checklist.md`. For an ad-hoc edit, it tells
the agent to read the applicable Full-lesson manifest and bar, or the
Scaffold manifest and **Scaffold contents** if the file is still a
scaffold. Apply the **Readiness precondition** only when creating a new
notebook.

The selected manifest also routes the agent to the target module README and
the relevant canonical standards. Full-lesson work reads some standards as
whole files (`notebook-writing.md`, `teaching-guidelines.md`,
`coding-standards.md`); other sources stay heading-scoped.

### `course-authoring.mdc`

This rule matches:

```text
README.md
COURSE_MODULES.md
[0-9][0-9] - */README.md
```

So it covers the repository root `README.md`, the roadmap, and numbered module READMEs.

For example, `08 - Aggregations and Window Functions/README.md` matches. `vault/README.md` does not.

For ad-hoc work (Path C), the rule routes numbered module READMEs to
`readme-authoring.md` and its canonical sources. It loads the **Module
folders** and **Notebook files** naming sections when needed, and the
**Audience assumptions** and **Production framing** teaching sections when
editing Learning objectives. Root `README.md` and `COURSE_MODULES.md` do not
load `readme-authoring.md`.

During `/write-module-readme` (Path B), it defers to the command's scoped
reads and must not add the ad-hoc list a second time. Root `README.md` in
context can attach this rule during that command; the rule still defers.
Path B reads named teaching and naming sections, not those whole files.

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

## How text gets into agent context

| Mechanism | What it does |
| --- | --- |
| `AGENTS.md` | Always-on agent pointer (Cursor + Codex; not Databricks auto-load) |
| Glob `.mdc` | Attaches when a matching path is in Agent context |
| Apply Intelligently `.mdc` | May self-attach when the description matches; commands also `@`-include the output rule |
| `@path` | Eager whole-file include (automatic, no agent choice) |
| Backtick + read verb | Agent must tool-read the whole file or named headings |
| Backtick, no read verb | Informational mention only (owner, consumer, or related file) |

The surrounding sentence determines backtick meaning, not the location of the path. A backticked path with a read verb in a checklist manifest, command file, rule, or ad-hoc list is a read instruction. A backticked path that only names an owner is informational.

Scoped reads are agent instructions, not mechanical enforcement. Cursor can still open a whole file.

---

## What happens when editing a learner notebook

Suppose this notebook is in the Agent context:

```text
08 - Aggregations and Window Functions/06 - Running Totals and Lag and Lead.py
```

If a notebook command is active, `learner-notebooks.mdc` defers to that
command's manifest. If no command is active, it uses the ad-hoc Full-lesson
or Scaffold path.

```text
AGENTS.md
    ↓
learner-notebooks.mdc attaches (if a matching .py is in context)
    ↓
agent follows the active command manifest, or the ad-hoc checklist path
    ↓
module README and the manifest's standards are opened
    ↓
agent performs the notebook work
```

If no matching numbered `.py` file is in the Agent context, the notebook glob does not attach. `AGENTS.md` still applies. Creating the first notebook in an empty module can therefore run `/new-lesson` from the command and checklist alone.

---

## What happens when editing course documentation

For the root `README.md`, `COURSE_MODULES.md`, or a numbered module `README.md`:

```text
AGENTS.md
    ↓
course-authoring.mdc attaches
    ↓
agent follows /write-module-readme's scoped reads, or the ad-hoc whole-file list
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
| `/new-lesson` | Create a notebook scaffold; do not write the full lesson |
| `/write-lesson` | Use an existing scaffold and a sibling notebook for voice; write the full runnable lesson |
| `/validate-notebook` | Report authoring issues only; do not write files |
| `/review-module` | Review the whole module folder rather than one notebook |

All five commands `@`-reference `notebook-command-output.mdc`. Command
structure is owned by `docs/standards/command-authoring.md`; when editing
a command file with Cursor AI, `command-authoring.mdc` routes the agent
there.

The four notebook commands declare scoped reads from
`docs/standards/notebook-authoring-checklist.md` (named manifest, bar, and
guard sections), not a whole-file `@`. `/write-module-readme`
`@`-references `docs/standards/readme-authoring.md` because every section
governs its output, and declares its own scoped reads for roadmap, dataset,
naming, and teaching sources.

### Path A — notebook commands (via the checklist)

| Command | Apply |
| --- | --- |
| `/new-lesson` | Scaffold manifest + Scaffold bar. Does **not** use Conditional reads. |
| `/write-lesson` | Full-lesson manifest + applicable Conditional reads + Full-lesson bar + Validation gate checks |
| `/validate-notebook` | Validation manifest + applicable Conditional reads + Full-lesson bar + Validation gate checks |
| `/review-module` | Module-review manifest + applicable Conditional reads + Module-review bar |

Manifest item lists stay in the checklist. Do not copy them here.

Checklist consumers: those four commands, `learner-notebooks.mdc` (ad-hoc Path C), and `AGENTS.md` (pointer only).

### Path B — `/write-module-readme` (independent of the checklist)

| Source | Sections |
| --- | --- |
| `COURSE_MODULES.md` | `Phase N` heading, column headings, target module row |
| `docs/standards/teaching-guidelines.md` | Audience assumptions, Production framing |
| `docs/standards/naming-conventions.md` | Module folders, Notebook files |
| `docs/data/dataset-overview.md` | Applicable headings only |
| `docs/standards/permissions-and-governance.md` | Whole file — only when privileges go beyond basic workspace access |
| `@docs/standards/readme-authoring.md` | Whole file — every section governs the README this command writes |

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

Notebook commands (Path A)
    → .cursor/commands/ plus the checklist

README command (Path B)
    → /write-module-readme (own read list; not the checklist)
```

This repository has no `alwaysApply: true` project rule and no Apply Manually project rule.

It uses two Apply to Specific Files rules and one Apply Intelligently rule.

Standalone Codex can use `AGENTS.md`, but it does not interpret Cursor `.mdc` rules or Cursor commands. A repository-wide constraint that must also apply outside Cursor should therefore live in `AGENTS.md`, not only in a Cursor-specific rule.
