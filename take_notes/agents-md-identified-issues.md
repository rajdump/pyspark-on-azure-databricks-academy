# AGENTS.md — Issues and Reviewed Solutions

## Purpose

This beginner-friendly document explains the issues found in the original
repository-root `AGENTS.md`, why each issue mattered, and the solution that was
reviewed and implemented.

It is an **author-private review record**. It is not:

- a replacement for `AGENTS.md`,
- course content,
- or a source of truth for project rules.

Canonical guidance remains in:

- `README.md`
- `COURSE_MODULES.md`
- module `README.md` files
- `docs/standards/`
- `docs/data/dataset-overview.md`
- `.cursor/`

The core design principle is:

> Keep `AGENTS.md` small, always-on, and navigational. Put maintainable detail
> in canonical documents.

### How to read this document

Each issue uses the same structure:

1. **Pre-fix wording or state** — what existed before the cleanup.
2. **Problem** — what was incorrect, unclear, or duplicated.
3. **Why this matters** — the practical risk.
4. **Reviewed solution** — the final safe decision.
5. **Result** — what agents should now understand or do.

All pre-fix quotations are historical. They do not describe the current
`AGENTS.md`.

---

## Overall assessment

The original `AGENTS.md` had a good foundation:

- It was concise.
- Its paths resolved.
- It described the course and dataset.
- It protected author-owned status and validation evidence.
- It routed agents toward repository standards.

The main problems were:

1. wording that could produce incorrect behavior,
2. duplicated information that could drift,
3. missing lifecycle and routing safeguards,
4. Cursor-specific behavior mixed with general guidance,
5. unnecessary always-on context.

The correct approach was to **refine the file**, not replace it with a large
instruction manual.

---

# Priority summary

## P1 — Correctness and agent behavior

| # | Issue | Main risk |
|---|---|---|
| 1 | Databricks SQL named alongside Spark SQL | Agent teaches the wrong SQL product |
| 2 | Undefined “current module” | Agent selects or invents the wrong module |
| 3 | Cursor rule loading overstated | Agent skips required standards |
| 4 | Standards catalog duplicated | Lists drift and required-read order is bypassed |
| 5 | Absolute status-edit ban | Agent refuses an explicit author request |
| 6 | Absolute validation-edit ban | Agent refuses real author-supplied results |
| 7 | Module lifecycle not enforced | Notebook scaffolding makes roadmap status false |

## P2 — Structure, duplication, and context

| # | Issue | Main risk |
|---|---|---|
| 8 | Technical baseline duplicated | Version details drift or useful UC context is removed |
| 9 | Slash-command workflow duplicated | Workflow copies diverge |
| 10 | Command-role guard duplicated | Same rule is maintained in several places |
| 11 | Root README not linked | Agent misses the full platform overview |
| 12 | Cursor details mixed into general guidance | Non-Cursor agents receive confusing instructions |
| 13 | Optional rule filename catalog | Always-on context gains a fragile Cursor-only list |
| 14 | Context budget not applied consistently | Duplicated detail consumes context and drifts |

---

# P1 — Correctness and agent behavior

## Issue 1 — SQL product was named incorrectly

### Pre-fix wording

```markdown
- Primary language: PySpark; SQL via Databricks SQL / Spark SQL where relevant
```

### Problem

The sentence treated **Databricks SQL** and **Spark SQL** as though they were
the same course technology.

This course teaches Spark SQL inside Databricks notebooks through:

- `%sql`
- `spark.sql()`

It does not teach SQL warehouses, the Databricks SQL editor, or DBSQL
endpoints.

### Why this matters

An agent asked to create a SQL lesson could introduce a different product and
produce content outside the course scope.

### Reviewed solution

```markdown
- Primary language: PySpark; SQL via Spark SQL (`%sql` / `spark.sql()`)
```

### Result

The boundary is explicit:

> PySpark is primary. “SQL” means Spark SQL inside Databricks notebooks.

---

## Issue 2 — “Current module” was undefined

### Pre-fix wording

```markdown
See `COURSE_MODULES.md` for the full roadmap and
the current module's own `README.md` for detailed, in-progress design.
```

### Problem

The phrase **current module** assumed that one module was always being
authored. At the time of review, Modules 1–9 were Complete, Modules 10–20 were
Not Started, and no module was Started.

### Why this matters

An agent could interpret “current module” as:

- the latest completed module,
- the next module,
- a module inferred from an open file,
- or a module that did not exist.

### Reviewed solution

Use task-based wording:

```markdown
See `COURSE_MODULES.md` for the roadmap and use the target module's
`README.md` for its detailed design.
```

Do not copy live module counts or status summaries into `AGENTS.md`.

### Result

The user’s requested target determines the module. The agent does not guess
which module is “current.”

---

## Issue 3 — Cursor rule loading was overstated

### Pre-fix wording

```markdown
Scoped `.cursor/rules/*.mdc` files load these automatically for matching
files.
```

### Problem

The repository does not have one attachment mode for every `.mdc` rule:

- `learner-notebooks.mdc` is file-scoped.
- `course-authoring.mdc` is file-scoped.
- `notebook-command-output.mdc` is relevance-scoped because it has a
  description and no glob.
- Commands also include `notebook-command-output.mdc` explicitly with `@`.
- Standalone Codex does not interpret Cursor `.mdc` rules.

The downloaded draft incorrectly described all rules as glob-scoped. That
would repeat the original problem in a different form.

### Why this matters

An agent might assume:

> The rule attached, so every referenced standard must already be available.

It could then skip notebook structure, naming, dataset, or teaching standards.

### Reviewed solution

```markdown
Each `.cursor/rules/*.mdc` file declares its own attachment behavior in
frontmatter. Do not assume a rule or the standards it references are already
in context; open the required canonical files.
```

Do not copy rule globs into `AGENTS.md`.

### Result

Rules are treated as scoped routing instructions, not proof that all
standards are already loaded.

---

## Issue 4 — The standards catalog was duplicated

### Pre-fix state

`AGENTS.md` listed each standards file separately:

- coding standards,
- notebook writing,
- naming conventions,
- teaching guidelines,
- compute validation,
- permissions and governance,
- notebook authoring checklist.

### Problem

`docs/standards/notebook-authoring-checklist.md` already owns the shared read
list for notebook work.

Maintaining another catalog in `AGENTS.md` creates two lists that can drift.

### Why this matters

An agent may treat the shorter `AGENTS.md` list as complete and skip:

- the checklist’s required-read order,
- the target module README,
- conditional compute or permission guidance.

### Reviewed solution

Remove the individual catalog and keep one pointer:

```markdown
- Shared read list for notebook work:
  `docs/standards/notebook-authoring-checklist.md`
```

Broad routing pointers to the roadmap, module README, dataset contract, and
standards directory remain useful.

### Result

The checklist owns the shared read list. `AGENTS.md` only routes agents to it.

---

## Issue 5 — The roadmap status rule was too absolute

### Pre-fix wording

```markdown
- Never update `COURSE_MODULES.md` status — that is author-owned.
```

### Problem

The intended restriction was:

> Do not change status automatically as a side effect of another task.

The word **never** also blocked direct requests from the author.

### Why this matters

An agent could refuse a legitimate request such as:

> Mark Module 10 as Started.

### Reviewed solution

```markdown
- Do not update `COURSE_MODULES.md` status as a side effect; change it only
  when the author explicitly asks.
```

The scopes remain different:

- A separate explicit author request may change status.
- Lesson commands never change status.
- Notebook edits never change status.

### Result

Silent status changes remain prohibited, while explicit author-directed
changes are allowed.

---

## Issue 6 — The validation rule was too absolute

### Pre-fix wording

```markdown
- Never write runtime validation evidence in `docs/validation/` — that is
  filled in by the author after running notebooks in Azure Databricks.
```

### Problem

The real safety boundary is not:

> An agent can never edit a validation file.

It is:

> An agent must never infer or fabricate runtime evidence.

The downloaded draft’s phrase “do not invent or auto-generate” was still
ambiguous about when a legitimate edit was allowed.

### Why this matters

The author may run a notebook in Azure Databricks, provide the actual output,
and ask the agent to format or record those facts.

Without precise wording, an agent could either:

1. refuse the valid request, or
2. invent a Pass/Fail result.

### Reviewed solution

```markdown
- Do not infer, fabricate, or independently mark runtime outcomes. Edit
  `docs/validation/` only when the author explicitly asks using Azure
  Databricks results or output they supplied.
```

Lesson commands retain their stricter rule: they never edit runtime evidence.

### Result

The agent can help record author-supplied facts but cannot create or infer
runtime outcomes.

---

## Issue 7 — The module-start lifecycle was not enforced

### Pre-fix state

The roadmap defined Not Started, Started, and Complete, but the repository did
not fully define or enforce the transition into notebook authoring.

The downloaded draft proposed allowing a Not Started module’s notebook when
the author explicitly asked and a README existed. That still left the roadmap
saying **Not Started** while a notebook existed.

### Problem

The roadmap status would become false:

- **Not Started** means no learner notebooks.
- **Started** means README design is complete and notebook authoring is active.
- **Complete** means notebooks have passed authoring and runtime validation.

### Why this matters

An agent could:

- create Module 10 from roadmap topics alone,
- create a notebook before the README design was complete,
- add a notebook while status remained Not Started,
- add an unvalidated notebook to a Complete module.

### Reviewed solution

Use this lifecycle:

```text
Complete module README design
    ↓
Author explicitly changes status to Started
    ↓
Run /new-lesson
    ↓
Write, review, and validate notebooks
    ↓
Author explicitly changes status to Complete
```

The policy is enforced across the correct owners:

- `COURSE_MODULES.md` defines status meaning.
- `notebook-authoring-checklist.md` owns scaffold prerequisites.
- `course-authoring.mdc` checks README completeness before a requested
  transition to Started.
- `/new-lesson` requires Started status, the README design, and a matching
  Notebook navigation entry.
- `AGENTS.md` keeps only the short repository-wide guard.

Adding a notebook to a Complete module requires a separate author-directed
change back to Started first.

### Result

Notebook files, README design, and roadmap status cannot silently contradict
one another.

---

# P2 — Structure, duplication, and context

## Issue 8 — The technical baseline duplicated the root README

### Pre-fix state

The original `AGENTS.md` repeated:

- Premium tier,
- Unity Catalog,
- DBR, Spark, Python, and Scala versions,
- language and SQL mode,
- notebook format,
- batch-only scope.

### Problem

Most of this already exists in the root `README.md`.

However, the downloaded draft removed Unity Catalog from `AGENTS.md`. That
was unsafe because Unity Catalog changes generated code and guidance.

Unity Catalog affects:

- `/Volumes/...` paths,
- three-part object names,
- managed tables,
- catalog and schema operations,
- privileges.

### Reviewed solution

Keep constraints that materially affect generated content:

```markdown
- Databricks Runtime 17.3 LTS — Spark 4.0.0, Python 3.12
- Unity Catalog governs course tables, Volumes, object names, and privileges
- Primary language: PySpark; SQL via Spark SQL (`%sql` / `spark.sql()`)
- Notebook format: Databricks source `.py` (`# Databricks notebook source`
  header required) — never `.ipynb`
- Batch data engineering only — no Structured Streaming, Auto Loader,
  streaming tables, or ML content
```

Keep Premium tier and Scala 2.13 in the root README. Remove the separate
`Technical baseline` heading and merge retained constraints into
`What this is`.

### Result

`AGENTS.md` stays compact without losing Unity Catalog behavior that affects
course code.

---

## Issue 9 — The slash-command workflow was duplicated

### Pre-fix state

`AGENTS.md` repeated the full lesson sequence:

```text
/new-lesson → /write-lesson → /validate-notebook → Azure validation
```

### Problem

The notebook checklist already owns command roles and workflow order.

The downloaded draft removed the workflow and then inserted almost the same
sequence in a Cursor section. That did not actually remove the duplication.

### Why this matters

If the workflow changes, multiple copies can disagree.

### Reviewed solution

Keep only the workflow location:

```markdown
Lesson workflows live in `.cursor/commands/`.
```

### Result

`AGENTS.md` provides discovery. The checklist and command files own details.

---

## Issue 10 — The command-role guard was duplicated

### Pre-fix wording

```markdown
- `/new-lesson`, `/write-lesson`, `/validate-notebook`, and `/review-module`
  never write roadmap status or runtime validation evidence ...
```

### Problem

The same behavior already existed in:

- global side-effect guards,
- the notebook checklist,
- individual command files,
- the learner-notebook rule.

### Why this matters

Repeated rules can slowly acquire different wording and meaning.

### Reviewed solution

Remove the command-role bullet from `AGENTS.md`.

Keep:

- global policy in `AGENTS.md`,
- strict command behavior in command files,
- command roles in the checklist,
- notebook-edit restrictions in `learner-notebooks.mdc`.

### Result

Each layer owns the rule appropriate to its scope.

---

## Issue 11 — The root README was missing from routing

### Pre-fix state

`AGENTS.md` pointed to the roadmap, module READMEs, dataset documentation, and
standards, but not the repository root `README.md`.

### Problem

The root README owns:

- learner overview,
- audience and prerequisites,
- full platform/version table,
- development workflow,
- where-to-start guidance.

### Reviewed solution

Add this under `Where to read`:

```markdown
- Learner overview and full technical baseline: `README.md`
```

### Result

`AGENTS.md` can omit secondary platform details without hiding their canonical
location.

---

## Issue 12 — General guidance and Cursor details were mixed

### Pre-fix state

The opening called `AGENTS.md` tool-agnostic, but later sections included:

- Cursor rules,
- slash commands,
- Cursor workflow.

### Problem

Non-Cursor agents could interpret Cursor mechanics as general project
workflow.

### Reviewed solution

Use a neutral opening:

```markdown
Always-on agent context. Canonical project guidance lives in `README.md`,
`COURSE_MODULES.md`, `docs/standards/`, and `docs/data/` — this file routes
to those sources instead of duplicating them.
```

Move the minimal Cursor pointers into a final section:

```markdown
## Cursor

Lesson workflows live in `.cursor/commands/`.

Each `.cursor/rules/*.mdc` file declares its own attachment behavior in
frontmatter. Do not assume a rule or the standards it references are already
in context; open the required canonical files.
```

### Result

Repository-wide guidance remains clear for every agent, while Cursor-specific
mechanics are isolated.

---

## Issue 13 — The optional rule filename catalog was rejected

### Proposed addition in the downloaded draft

```markdown
Rule files: `learner-notebooks.mdc`, `course-authoring.mdc`,
`notebook-command-output.mdc`.
```

### Problem

This was presented as a discoverability improvement, but it would create
another Cursor-specific catalog in always-on context.

The list could drift when a rule is added, removed, or renamed.

### Reviewed solution

Do not add the filename list.

Point to:

```text
.cursor/rules/
```

Let each rule’s frontmatter remain authoritative.

### Result

No required behavior is lost. Agents can inspect the directory when rule
details are relevant.

---

## Issue 14 — Always-on context was not consistently optimized

### Pre-fix state

`AGENTS.md` said “navigate, don’t duplicate,” but still repeated:

- a standards catalog,
- command workflow,
- command roles,
- platform details.

### Problem

`AGENTS.md` is supplied on every request.

Duplication creates:

1. **maintenance cost** — copied guidance becomes stale,
2. **context cost** — task-specific code and instructions receive less room.

### Reviewed solution

Apply these rules:

1. Prefer **pointer + canonical document**.
2. Keep `AGENTS.md` at 80 lines or fewer.
3. Do not duplicate the checklist’s standards catalog.
4. Do not duplicate the README’s full platform table.
5. Do not duplicate command responsibilities or workflow.
6. Do not store live module-status summaries.
7. Do not copy `.mdc` globs or filename catalogs.
8. Keep short repository-wide constraints that must remain always available.

### Result

`AGENTS.md` becomes a compact routing and safety layer rather than a second
documentation system.

---

# Implemented final structure

The revised `AGENTS.md` uses six sections:

| # | Section | Purpose |
|---|---|---|
| 1 | `What this is` | Identity and code-generation constraints |
| 2 | `Dataset` | Dataset names and canonical dataset pointer |
| 3 | `Workflow` | GitHub/Databricks workflow and local Spark boundary |
| 4 | `Where to read` | Lightweight routing to canonical documents |
| 5 | `Do not write automatically` | Global side-effect and lifecycle guards |
| 6 | `Cursor` | Minimal command and rule-attachment pointers |

The final file is 63 lines, below the 80-line practical limit.

---

# Files aligned by this cleanup

The review found that Issue 7 could not be fixed safely in `AGENTS.md` alone.
The implemented cleanup therefore aligned seven files:

| File | Reason |
|---|---|
| `AGENTS.md` | Repository-wide routing and safeguards |
| `COURSE_MODULES.md` | Canonical lifecycle definitions |
| `docs/standards/notebook-authoring-checklist.md` | Canonical scaffold prerequisites |
| `.cursor/rules/course-authoring.mdc` | Checks README design before Started status |
| `.cursor/commands/new-lesson.md` | Enforces README and Started requirements |
| `.cursor/commands/write-lesson.md` | Replaces ambiguous “current module” wording |
| `take_notes/agents-md-identified-issues.md` | Beginner-friendly reviewed record |

No module status value and no runtime validation evidence was changed during
the cleanup.

---

# Final verification checklist

- [x] `AGENTS.md` is at or below 80 lines.
- [x] Spark SQL is used instead of Databricks SQL for course SQL scope.
- [x] Undefined “current module” wording was removed from active guidance.
- [x] Unity Catalog behavior remains in always-on context.
- [x] The root README is linked.
- [x] The notebook checklist owns the shared standards read list.
- [x] Explicit author-directed status changes remain possible.
- [x] Lesson commands cannot change roadmap status.
- [x] Runtime evidence cannot be inferred or fabricated.
- [x] Author-supplied Azure results can be recorded when explicitly requested.
- [x] Every scaffold requires Started status and complete README design.
- [x] Complete modules must return to Started before receiving a new notebook.
- [x] Cursor rule attachment is described through frontmatter, not as all-glob.
- [x] The command workflow is not duplicated in `AGENTS.md`.
- [x] Cursor rule filenames and glob patterns are not duplicated.

---

# Expected outcome

`AGENTS.md` now acts as a compact entry point:

```text
AGENTS.md
    ↓
understand repository-wide constraints
    ↓
identify the correct canonical document
    ↓
open task-specific guidance
    ↓
perform the requested work
```

It does not become:

- a second README,
- a second standards catalog,
- a second roadmap,
- a second command manual,
- or a second validation record.

The intended beginner mental model is:

1. `AGENTS.md` gives short rules and directions.
2. Canonical documents own detailed information.
3. Cursor rules help route task-specific work.
4. Commands perform explicit workflows.
5. The author controls roadmap status and supplies runtime evidence.
