# AGENTS.md — Identified Issues and Resolutions

## Purpose of this document

Author-private audit and implementation record for the `AGENTS.md` cleanup.
It is not course content and not a second `AGENTS.md`. Quotes labeled
**Current state** and their line numbers capture the pre-fix, 72-line
`AGENTS.md` snapshot; they are historical after the cleanup is applied.

Use it to understand the original issue, failure mode, reviewed resolution,
and affected canonical files. The [Target structure](#target-structure-after-fixes)
table is the composition model for `AGENTS.md`; lifecycle policy also requires
the roadmap, checklist, and command/rule changes recorded under Issue 7.

Do not treat this file as a source of truth for the course. Canonical
rules stay in `README.md`, `COURSE_MODULES.md`, `docs/standards/`,
`docs/data/dataset-overview.md`, and `.cursor/`.

## What AGENTS.md does in this project

`AGENTS.md` is always-on agent context (Cursor injects it; Codex reads it
before work). Each `.cursor/rules/*.mdc` file declares its own attachment
behavior in frontmatter; this repository has two file-scoped rules and one
relevance-scoped rule. Codex does not load `.mdc` files.

Design principle: **navigate, don't duplicate.** Point at canonical docs.
Keep only hard stops that must apply even when no glob matches.

**Token / context optimization:** `AGENTS.md` is always-on — every line
counts toward the model's context budget. Keep broad constraints short;
put maintainable detail in canonical docs and route with pointers. Scoped
`.mdc` rules and slash commands load additional standards only for
matching work, not on every request. See
`cursor_ecosystem/01-Agents-and-Cursor-Rules.md` (layers + decision tree).
When a rule is broad but not short enough for `AGENTS.md`, keep a brief
constraint or pointer in `AGENTS.md` and own the full detail in
`docs/standards/` or `docs/data/` — do not copy long text into always-on
context.

When this file is wrong, agents fail in five ways:

1. **Wrong product content** — teach Databricks SQL warehouses instead of
   Spark SQL in notebooks.
2. **Nonexistent targets** — chase a "current in-progress module" that
   does not exist.
3. **Skipped standards** — assume `.mdc` rules already loaded
   `docs/standards/` and never open them.
4. **Refused legitimate requests** — treat "never" as a ban even when the
   author explicitly asks.
5. **Premature scaffolding** — create Module 10+ notebooks with no folder
   and no README.

## Pre-fix snapshot

- **File:** `AGENTS.md` (repo root), **72 lines**
- **Verdict:** Good foundation — targeted changes needed
- **Already works:** size is in the "keep it small" range; every path
  resolves; DBR 17.3 LTS / Spark 4.0.0 / Python 3.12 match `README.md` and
  validation records; `/new-lesson`, `/write-lesson`, `/validate-notebook`,
  `/review-module` exist; author-owned guards for status and
  `docs/validation/` are present (wording is too absolute)
- **Editing rule:** scalpel, not rewrite; stay **≤ 80 lines** after edits

## Target structure after fixes

| # | New heading | Absorbs from current | Purpose |
|---|---|---|---|
| 1 | **What this is** | "What this project is" + "Technical baseline" | Identity plus codegen constraints: DBR/Spark/Python, Unity Catalog, `.py` not `.ipynb`, batch-only, Spark SQL |
| 2 | **Dataset** | Dataset (unchanged role) | Table names + pointer to `docs/data/dataset-overview.md` |
| 3 | **Workflow** | Workflow (unchanged role) | GitHub is remote SoT; local tools do not run Spark |
| 4 | **Where to read** | "Where the real rules live" minus Cursor workflow and the seven-file catalog | Routing only: README, COURSE_MODULES, module README when it exists, checklist, dataset-overview |
| 5 | **Do not write automatically** | "What Cursor should not do automatically" | Global side-effect guards: status, supplied runtime evidence, module lifecycle |
| 6 | **Cursor** | Cursor bits from "Where the real rules live" | Short last section: command pointer and frontmatter-defined rule attachment |

---

## Issues

P1 — Fix first (items 1–3 produce wrong files; items 4–7 are
consistency/gaps). P2 — Cleanup after P1 (includes token/context
optimization — Issue 14).

### Issue 1 — Wrong product: "Databricks SQL" instead of Spark SQL in notebooks

**Category:** Inconsistency
**Priority:** P1 — an agent can author SQL-warehouse / DBSQL lessons this course does not teach
**Location:** `AGENTS.md` L18

**Current state:**

> `- Primary language: PySpark; SQL via Databricks SQL / Spark SQL where relevant`

**Description:**

The line names two products as if both were in scope. This course uses
Spark SQL inside Databricks notebooks (`%sql` and `spark.sql()`).
Databricks SQL is the warehouse product (DBSQL). The rest of the repo
never uses the warehouse name.

**Project impact:**

An agent asked to "add a SQL lesson" can introduce SQL warehouses, DBSQL
endpoints, or Databricks SQL editor workflows. That contradicts Module 9
(`Spark SQL and DataFrame Interoperability`) and the README SQL row.

**Resolution:**

```
- Primary language: PySpark; SQL via Spark SQL (`%sql` / `spark.sql()`)
```

**Source of truth:** `README.md:42`

---

### Issue 2 — Undefined target: "current module" in-progress design

**Category:** Stale
**Priority:** P1 — the pointer names a state that does not exist; the agent may invent a module
**Location:** `AGENTS.md` L11–12

**Current state:**

> `See `COURSE_MODULES.md` for the full roadmap and`
> `the current module's own `README.md` for detailed, in-progress design.`

**Description:**

The text assumes there is always a current in-progress module with a
README. `COURSE_MODULES.md` defines Started as "actively authoring — see
its README." Modules 1–9 are Complete; 10–20 are Not Started; there is no
Started row and no `10 - *` folder. "Current" is undefined.

**Project impact:**

An agent looking for "the current module" may pick Module 9 (last
Complete), Module 10 (next Not Started, no folder), or hallucinate an
in-progress README, then scaffold or edit the wrong tree.

**Resolution:**

Replace L11–12 with:

```
See `COURSE_MODULES.md` for the full roadmap. Use the target module's
`README.md` when it exists.
```

Do **not** write live Complete/Not Started counts into `AGENTS.md`.

**Source of truth:** `COURSE_MODULES.md:10-16`

---

### Issue 3 — Overstated auto-loading of `.cursor/rules/`

**Category:** Inconsistency
**Priority:** P1 — agents skip opening `docs/standards/` because they think rules already injected them
**Location:** `AGENTS.md` L56–57

**Current state:**

> `Scoped `.cursor/rules/*.mdc` files load these automatically for matching`
> `files.`

**Description:**

Two rules auto-attach on globs: `learner-notebooks.mdc` (numbered `*.py`)
and `course-authoring.mdc` (READMEs / `COURSE_MODULES.md`).
`notebook-command-output.mdc` has `alwaysApply: false`, a description, and
no globs, so Cursor can attach it by relevance; slash commands also include
it explicitly with `@`. Codex does not read `.mdc` at all. "Load these
automatically" overstates both Cursor and Codex.

**Project impact:**

A Codex session, or a Cursor chat with no matching file in context, treats
standards as already loaded and writes notebooks that skip the checklist
(wrong cell markers, invented columns, no `F` import).

**Resolution:**

Delete L56–57 from "Where the real rules live." Put this under **Cursor**
(Issue 12):

```
Each `.cursor/rules/*.mdc` file declares its attachment behavior in
frontmatter. Do not assume a rule or the standards it references are already
in context; open the required canonical files.
```

Do **not** copy glob patterns from `.mdc` frontmatter.

**Source of truth:** `.cursor/rules/notebook-command-output.mdc:1-4` (no
`globs`; `alwaysApply: false`). Compare
`.cursor/rules/learner-notebooks.mdc:3-4` and
`.cursor/rules/course-authoring.mdc:3-4`.

---

### Issue 4 — Seven-file standards list duplicates the checklist catalog

**Category:** Duplicates
**Priority:** P1 — violates the checklist's own "do not duplicate this list"; two catalogs will drift
**Location:** `AGENTS.md` L46–54

**Current state:**

> `- Coding standards: `docs/standards/coding-standards.md``
> `- Notebook structure and formatting: `docs/standards/notebook-writing.md``
> `- Naming conventions: `docs/standards/naming-conventions.md``
> `- Teaching/pedagogy standards: `docs/standards/teaching-guidelines.md``
> `- Compute selection and validation order: `docs/standards/compute-validation-policy.md``
> `- Permissions and governance (Azure RBAC vs. workspace permissions vs. Unity`
> `  Catalog privileges): `docs/standards/permissions-and-governance.md``
> `- Notebook authoring checklist (shared read list for slash commands):`
> `  `docs/standards/notebook-authoring-checklist.md``

**Description:**

The checklist is the canonical shared read list and names `AGENTS.md` as a
pointer site: do not duplicate the list; point here instead. `AGENTS.md`
then reprints all seven files. Adding a future standard (for example
`python-modules`) requires two edits or the lists diverge.

**Project impact:**

An agent uses the AGENTS list as complete, skips the checklist's
**Required reads** order (module README first), and invents notebook
sections that are not in that module's Notebook navigation.

**Resolution:**

Remove L46–54 entirely. Under **Where to read**, keep a single standards
pointer:

```
- Shared read list for notebook work: `docs/standards/notebook-authoring-checklist.md`
```

Keep the earlier layer bullets that are not the seven-file catalog
(`COURSE_MODULES.md`, dataset-overview, module README, `docs/standards/`
as a directory). Do not re-list the seven files.

**Source of truth:** `docs/standards/notebook-authoring-checklist.md:1-7`

---

### Issue 5 — Absolute "never" on `COURSE_MODULES.md` status vs "only when asked"

**Category:** Inconsistency
**Priority:** P1 — wording conflict; failure mode is over-refusal, not a bad write
**Location:** `AGENTS.md` L66

**Current state:**

> `- Never update `COURSE_MODULES.md` status — that is author-owned.`

**Description:**

Slash commands correctly forbid status updates as a side effect of lesson
work. `course-authoring.mdc` allows a status draft when the author
**explicitly asks**. "Never" blocks that path. The current wording is
safer than permissive, but it disagrees with the file that owns edits to
`COURSE_MODULES.md`.

**Project impact:**

The author says "mark Module 10 as Started" and the agent refuses, or
edits a private note instead of `COURSE_MODULES.md`. It will not silently
flip status during `/write-lesson`.

**Resolution:**

Replace L66 with:

```
- Do not update `COURSE_MODULES.md` status as a side effect — only when the
  author explicitly asks.
```

**Source of truth:** `.cursor/rules/course-authoring.mdc:25-26`

---

### Issue 6 — Absolute "never write" on `docs/validation/` blocks author-directed recording

**Category:** Inconsistency
**Priority:** P1 — wording conflict; failure mode is over-refusal, not invented evidence
**Location:** `AGENTS.md` L67–68

**Current state:**

> `- Never write runtime validation evidence in `docs/validation/` — that is`
> `  filled in by the author after running notebooks in Azure Databricks.`

**Description:**

The real rule is: do not invent runtime evidence, and do not write it as a
side effect of authoring commands. `compute-validation-policy.md` says the
author fills `docs/validation/` after Azure runs. If the author pastes
real results and asks to format the record, "never write" forbids a
legitimate edit.

**Project impact:**

After a Databricks run, the author pastes compute notes and asks the agent
to update `docs/validation/09 - ….md`. The agent refuses. Conversely,
without a "don't invent" line, `/write-lesson` might fabricate Pass rows.
The replacement must block invention and allow author-directed recording.

**Resolution:**

Replace L67–68 with wording that permits faithful recording but never agent
inference:

```
- Do not infer, fabricate, or independently mark runtime outcomes. Edit
  `docs/validation/` only when the author explicitly asks using Azure
  Databricks results or output they supplied.
```

**Source of truth:** `docs/standards/compute-validation-policy.md:57-63`

---

### Issue 7 — Define and enforce the module-start lifecycle

**Category:** New policy decision (identified from a gap)
**Priority:** P1 — scaffolding must not make roadmap status false
**Location:** No line — missing

**Current state:**

> *(no corresponding sentence in `AGENTS.md`)*

**Description:**

The status legend says Not Started has no learner notebooks and Started is
actively authoring, but it did not define the transition. The reviewed policy
is: complete the module README design, change status to Started through a
separate explicit author request, then scaffold. Every `/new-lesson` requires
Started; adding a notebook to a Complete module requires returning it to
Started first.

**Project impact:**

An agent creates `10 - Delta Lake for Managed Tables/01 - ….py` from
`COURSE_MODULES.md` topics alone, with no Notebook navigation, no
privileges section, and no module README. That violates "module README
owns detailed design."

**Resolution:**

This is a coordinated policy, not an `AGENTS.md`-only sentence:

```
- `COURSE_MODULES.md` defines the Not Started / Started / Complete lifecycle.
- `notebook-authoring-checklist.md` owns scaffold prerequisites.
- `course-authoring.mdc` validates README design before a requested Started
  transition.
- `/new-lesson` requires Started status, the module README, and the matching
  Notebook navigation entry; it never changes status.
- `AGENTS.md` keeps the short repository-wide lifecycle guard.
```

**Source of truth:** `COURSE_MODULES.md` status legend and
`docs/standards/notebook-authoring-checklist.md` Scaffold bar

---

### Issue 8 — Full technical baseline recopied from README

**Category:** Duplicates
**Priority:** P2 — non-codegen pins add drift risk in always-on context
**Location:** `AGENTS.md` L14–22 (heading **Technical baseline** plus bullets)

**Current state:**

> `## Technical baseline`
>
> `- Azure Databricks, Premium tier, Unity Catalog enabled`
> `- Databricks Runtime 17.3 LTS — Spark 4.0.0, Python 3.12, Scala 2.13`
> `- Primary language: PySpark; SQL via Databricks SQL / Spark SQL where relevant`
> `- Notebook format: Databricks source `.py` (`# Databricks notebook source``
> `  header required) — never `.ipynb``
> `- Batch data engineering only — no Structured Streaming, Auto Loader,`
> `  streaming tables, or ML content`

**Description:**

This is the README version table in prose. DBR / Spark / Python, `.py` vs
`.ipynb`, batch-only scope, and Unity Catalog change what code an agent
generates. Unity Catalog affects Volume paths, three-part names, managed
tables, and privileges. Premium tier and Scala 2.13 can remain in the root
README. SQL wording is Issue 1; apply that fix inside this shortened list.
Fold the retained bullets into **What this is** and drop the separate
**Technical baseline** heading.

**Project impact:**

README later moves to a new LTS and AGENTS.md still says 17.3 — two
sources. Premium and Scala in always-on context add tokens without changing
notebook code. Retain Unity Catalog because it affects generated code, and
point at README for the full table (Issue 11).

**Resolution:**

Delete the heading `## Technical baseline`. Merge into **What this is**
(after the identity sentence from Issue 2):

```
- Databricks Runtime 17.3 LTS — Spark 4.0.0, Python 3.12
- Unity Catalog governs course tables, Volumes, object names, and privileges
- Primary language: PySpark; SQL via Spark SQL (`%sql` / `spark.sql()`)
- Notebook format: Databricks source `.py` (`# Databricks notebook source`
  header required) — never `.ipynb`
- Batch data engineering only — no Structured Streaming, Auto Loader,
  streaming tables, or ML content
```

Drop Premium and Scala 2.13. Retain behavior-oriented Unity Catalog context.
The full table remains in `README.md`.

**Source of truth:** `README.md:31-45`

---

### Issue 9 — Slash-command workflow repeats the checklist

**Category:** Duplicates
**Priority:** P2 — same pipeline in three places; AGENTS.md is the wrong owner
**Location:** `AGENTS.md` L57–62

**Current state:**

> `Slash commands (`/new-lesson`, `/write-lesson`, `/validate-notebook`,`
> `/review-module`) reference the checklist and standards directly.`
>
> `Recommended notebook workflow: `/new-lesson` (skeleton) → `/write-lesson``
> `(full content) → `/validate-notebook` (authoring check) → Azure Databricks`
> `runtime validation by the author.`

**Description:**

The checklist already owns command roles and the recommended workflow.
Each `.cursor/commands/*.md` file restates "do not update COURSE_MODULES /
docs/validation." AGENTS.md should point, not replay the pipeline.
`/review-module` stays in `.cursor/commands/`; it does not need to be in
the always-on one-liner.

**Project impact:**

Checklist workflow changes and AGENTS.md still describes an old sequence.
Non-Cursor agents also try to invoke `/new-lesson`, which they do not
have, instead of reading the checklist.

**Resolution:**

Remove L57–62 from **Where the real rules live**. Under **Cursor**, keep only
the workflow location:

```
Lesson workflows live in `.cursor/commands/`.
```

**Source of truth:** `docs/standards/notebook-authoring-checklist.md:41-45`

---

### Issue 10 — Command-roles bullet restates Issues 5–6 and each command file

**Category:** Removable
**Priority:** P2 — third copy of the same guard
**Location:** `AGENTS.md` L69–71

**Current state:**

> `- `/new-lesson`, `/write-lesson`, `/validate-notebook`, and `/review-module``
> `  never write roadmap status or runtime validation evidence (`/write-lesson``
> `  fills lesson content; `/new-lesson` scaffolds only).`

**Description:**

After Issues 5–6, **Do not write automatically** already covers status and
validation. Each slash command already says not to touch those files.
Command roles (scaffold vs full lesson vs review) live in the checklist
table. This bullet is leftover Cursor-specific duplication.

**Project impact:**

None if left in (redundant safety). Cost is tokens and a third wording to
keep in sync with Issues 5–6.

**Resolution:**

Remove entirely.

**Source of truth:** `docs/standards/notebook-authoring-checklist.md:33-39`;
also `.cursor/commands/new-lesson.md:34`,
`.cursor/commands/write-lesson.md:38`,
`.cursor/commands/validate-notebook.md:34-36`,
`.cursor/commands/review-module.md:29-31`

---

### Issue 11 — Root `README.md` never linked

**Category:** Gap
**Priority:** P2 — agents duplicate the version table instead of opening README
**Location:** No line — missing (add under **Where to read**)

**Current state:**

> *(AGENTS.md never mentions `README.md`. Closest routing is L41: `COURSE_MODULES.md`.)*

**Description:**

Official AGENTS.md guidance: this file complements README; it does not
replace it. The human version table, audience, and "where to start" live
in `README.md`. After Issue 8 drops Premium/Scala/UC from AGENTS.md,
agents need a pointer to that table.

**Project impact:**

An agent asked for "platform details" keeps using the shortened AGENTS
pins or invents Community-edition / no-UC setups instead of reading
README.

**Resolution:**

First bullet under **Where to read**:

```
- Learner overview and version table: `README.md`
```

**Source of truth:** `README.md:1-13` (overview) and `README.md:31-45`
(version table)

---

### Issue 12 — Opening claims tool-agnostic; L56–62 is Cursor-only

**Category:** Removable
**Priority:** P2 — Codex and other tools get Cursor slash-command procedure in always-on context
**Location:** `AGENTS.md` L1–4 and L56–62

**Current state:**

> `Concise, tool-agnostic project summary. Full standards live in`
> ``docs/standards/*.md`` `and` ``docs/data/*.md`` `— this file points to them, it`
> `does not duplicate them.`

(Cursor workflow at L56–62 is quoted in Issues 3 and 9.)

**Description:**

The header says tool-agnostic, then the same file embeds `/new-lesson` →
`/write-lesson` as recommended workflow. Hard stops (format, batch-only,
don't invent validation) belong in the main body. Cursor commands and the
pointer to frontmatter-scoped rules belong in a last **Cursor** section.

**Project impact:**

A non-Cursor agent tries to run `/new-lesson` or assumes `.cursor/rules`
already loaded standards (Issue 3). Cursor authors still need a short
pointer.

**Resolution:**

Replace L1–4 with:

```
Always-on agent context. Canonical rules live in `docs/standards/`,
`docs/data/`, `README.md`, and `COURSE_MODULES.md` — this file points to
them; it does not duplicate them.
```

Add a final section after applying Issues 3 and 9:

```
## Cursor

Lesson workflows live in `.cursor/commands/`.

Each `.cursor/rules/*.mdc` file declares its own attachment behavior in
frontmatter. Do not assume a rule or the standards it references are already
in context; open the required canonical files.
```

**Source of truth:** Design principle in current `AGENTS.md:1-5`; Cursor vs
`.mdc` attachment: https://cursor.com/docs/rules

---

### Issue 13 — Optional `.mdc` filename catalog (rejected)

**Category:** Rejected optional optimization
**Priority:** None — omission keeps always-on context smaller
**Location:** Not applicable

**Current state:**

> `Scoped `.cursor/rules/*.mdc` files` *(L56 — glob only, no filenames)*

**Description:**

Listing `learner-notebooks.mdc`, `course-authoring.mdc`, and
`notebook-command-output.mdc` could improve discovery, but it would add a
Cursor-specific catalog to always-on context. The `.cursor/rules/` pointer
is sufficient; interested agents can inspect that directory.

**Project impact:**

No required behavior depends on the filename list. `AGENTS.md` routes
notebook work directly to the canonical checklist.

**Resolution:**

Do not add the filename catalog. It adds always-on detail for Cursor-specific
files and can drift as rules are added or renamed. Point to `.cursor/rules/`
and let each rule's frontmatter remain authoritative.

**Source of truth:** `.cursor/rules/` frontmatter and
`docs/standards/notebook-authoring-checklist.md`

---

### Issue 14 — Token / context budget: short always-on text, canonical detail elsewhere

**Category:** Cross-cutting cleanup
**Priority:** P2 — apply while resolving Issues 4, 8, 9, and 11; not a
separate line patch
**Location:** Cross-cutting — `AGENTS.md` size, routing in **Where to
read**, and alignment with `cursor_ecosystem/01-Agents-and-Cursor-Rules.md`

**Current state:**

> Navigate, don't duplicate is stated (L1–5 area) but token optimization
> is not explicit. Several P2 issues remove duplication (Issues 4, 8, 9,
> 10, 11) without naming the shared reason: always-on context is expensive.

**Description:**

Layered guidance is not only about correctness and single source of truth.
It also limits what reaches the model on every request:

- **`AGENTS.md`** — small always-on instruction surface; short constraints
  or pointers, not full standards catalogs
- **`.mdc` rules** — attach for particular files or tasks; `@`-reference or
  route to standards when detail is needed
- **Canonical docs** — own maintainable detail; contents become context
  when read or `@`-referenced, not by default on every chat

If a repository-wide rule needs more than a few lines, **do not expand
`AGENTS.md`** — add or update the canonical document and keep a pointer
in `AGENTS.md` (same pattern as naming conventions in File 01).

**Project impact:**

Duplicated standards in always-on context waste tokens and crowd out
notebook code and task-specific context. Agents may follow stale copies
instead of opening the canonical file. Fixes that only shorten prose
without routing leave detail orphaned or repeated in `.mdc` rules.

**Resolution:**

While applying P2 edits:

1. Prefer **pointer + canonical doc** over pasting detail into `AGENTS.md`.
2. Keep **≤ 80 lines** (existing constraint) as a practical token guard.
3. Do not duplicate checklist catalogs (Issue 4) or README version tables
   (Issue 11) — both are token and drift risks.
4. When adding a new broad rule, ask: *short enough for `AGENTS.md`?* If
   not, canonical doc + one-line pointer.

No new `AGENTS.md` section required unless a single sentence under
**Where to read** helps authors (optional): e.g. keep this file small;
detailed rules live in `docs/standards/` and `docs/data/`.

**Source of truth:** `cursor_ecosystem/01-Agents-and-Cursor-Rules.md`
(Why layers, `AGENTS.md` section, decision tree); OpenAI Codex AGENTS.md
guide (keep small; default size cap).

---

## Constraints for editing

- Do not duplicate the checklist's file catalog (Issue 4). Point at
  `docs/standards/notebook-authoring-checklist.md`.
- Do not cache module status (Complete / Started / Not Started counts)
  into `AGENTS.md`. Status lives in `COURSE_MODULES.md`.
- After edits, every path in `AGENTS.md` must resolve (`README.md`,
  `COURSE_MODULES.md`, `docs/data/dataset-overview.md`,
  `docs/standards/notebook-authoring-checklist.md`, `docs/validation/`,
  `.cursor/commands/`, and `.cursor/rules/`).
- Stay **≤ 80 lines** (always-on token budget as well as readability).
- When a broad rule is not short enough for `AGENTS.md`, point to the
  canonical document; do not paste the full rule (Issue 14).
- Do not copy `.mdc` glob patterns or filename catalogs; they will drift.
- Compose P1 and P2 changes rather than applying overlapping line patches.
  Issues 1 and 8 both touch the
  SQL bullet — use Issue 8's shortened list, which already includes the
  Issue 1 Spark SQL wording.
- Issues 3, 9, 10, and 12 all touch L56–71 — compose them via the
  **Cursor** and **Do not write automatically** headings in the target
  structure, do not apply those four as independent overlapping patches.
- Do not change any module status value or runtime validation evidence as a
  side effect of this cleanup. The reviewed scope also aligns
  `COURSE_MODULES.md`, the notebook checklist, `course-authoring.mdc`,
  `/new-lesson`, and the opening terminology in `/write-lesson`.

## References

| URL | What it supports |
|---|---|
| https://agents.md/ | AAIF / Linux Foundation format: Markdown, no required schema. Complements README. Nested files merge; closest wins; user prompt overrides. |
| https://developers.openai.com/codex/guides/agents-md | Codex loads `AGENTS.md` before work; keep small; 32 KiB default cap; nested merge. |
| https://developers.openai.com/codex/concepts/customization | Keep it small. Use AGENTS.md for every-time rules and routing. Repeatable workflows belong in skills/commands, not a large AGENTS.md. |
| https://cursor.com/docs/rules | `AGENTS.md` is a Cursor rule type (plain Markdown, no globs). `.mdc` attachment is controlled by `alwaysApply`, `description`, and `globs`. Reference files instead of copying. |
