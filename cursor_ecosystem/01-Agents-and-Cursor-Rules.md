# Agents and Cursor Rules

A language model may already know Python, SQL, Spark, and many other technologies.

But it does not automatically know the decisions made by a specific project:

- which formats to use
- which features are in or out of scope
- which names and schemas are authoritative
- which actions are not allowed
- where the source of truth lives

Without that project information, the model can produce code that is technically correct but still wrong for the project.

So the important question is:

> **How does the right project information reach an AI coding agent at the right time?**

This file explains that mechanism.

The next file, [How This Repository Uses Rules and Standards](02-How-This-Repository-Uses-Rules-and-Standards.md), shows how this repository implements it.

---

## What an AI coding agent needs

A language model can reason about a task and generate code or text.

An **AI coding agent** adds the environment needed to work with a repository:

```text
AI coding agent
    = model
    + instructions
    + context
    + tools
```

Each part has a different job:

- **Model** — reasons about the task and generates the result.
- **Instructions** — tell the model what it should or should not do.
- **Context** — gives the model the information it can use for the current task.
- **Tools** — let the agent read, search, edit, and run commands.

The important point is:

> **Instructions and context describe different roles. They are not specific file types.**

### Instructions tell the model what to follow

Instructions can come from different places:

```text
Your prompt
    → "Review this notebook and report issues only."

AGENTS.md
    → "Use .py files for learner notebooks."

.mdc rule
    → "Follow the notebook content standard for this lesson."
```

These come from different sources, but they all tell the model **what it should follow**.

A Cursor `.mdc` rule is therefore one source of instructions.

```text
.mdc rule
    ↓
contains instructions
    ↓
Cursor attaches the rule
    ↓
model receives those instructions
```

### Context gives the model information to work with

Context is the information available to the model for the current task.

It can include:

- source code
- README files
- schemas
- configuration files
- standards documents
- other project documentation

For example, an `.mdc` rule may contain this instruction:

```text
Use coding-standards.md.
```

That instruction tells the agent **which document to use**.

The agent then reads or receives `coding-standards.md`.

```text
.mdc rule
    ↓
"Use coding-standards.md"
    ↓
agent reads the document
    ↓
model can now see its contents
```

The standard itself may contain detailed rules such as:

```text
Use F.col(...) for column references.
Avoid wildcard imports.
```

So there are two separate ideas:

- `coding-standards.md` **stores the detailed rules**
- once that file is read or supplied, the model can **use those rules as part of its context**

In other words:

> **Instructions tell the model what to follow. Context gives the model the information it needs to follow those instructions.**

A rule can connect the two:

```text
Rule
    ↓
tells the agent what to do
or which document to use
    ↓
required document is read
    ↓
document becomes available to the model
    ↓
model performs the task
```

So the simplest mental model is:

```text
Instructions
    → what the model should follow

Rules
    → one source of instructions

Standards / project docs
    → where detailed project rules and information live

Context
    → the information available to the model for the current task

Tools
    → what the agent can use to read, edit, search, and run
```

Together, these allow the model to work with the repository **and follow the project's expectations**.

---

## Why project instructions need different layers

A project may have many instructions the agent needs to follow.

But those instructions do not all need to reach the model in the same way.

Some constraints must apply broadly across the repository. Some instructions matter only for particular files or tasks. Detailed rules, definitions, and reference information may need a canonical document that can be maintained as the source of truth.

That gives each layer a different role:

| Need | Where it belongs |
| --- | --- |
| Short constraints and working rules that should apply broadly across the repository | `AGENTS.md` |
| Additional instructions needed for particular files or kinds of work | Cursor `.mdc` rules |
| Detailed rules, definitions, and reference information that need a canonical home | Project docs / standards |

`AGENTS.md` and `.mdc` rules are **instruction sources**.

They may contain instructions directly, or they may tell the agent which canonical document to use.

Canonical docs and standards hold detailed project knowledge that should have one maintained source of truth. When the agent reads or receives those documents, their contents become part of the model's context.

A useful way to decide where a new instruction belongs is:

```text
New instruction
    ↓
Must it apply broadly across the repository?
    ├─ yes → AGENTS.md
    │        Keep it short.
    │        Point to a canonical document if more detail is needed.
    │
    └─ no
        ↓
Is it needed only for particular files or work?
    ├─ yes → .mdc rule
    │        Keep the scoped instruction there.
    │        Point to a canonical document if the detail already lives elsewhere.
    │
    └─ no
        ↓
Is it detailed project knowledge that needs to be maintained?
        └─ yes → canonical project document
```

The important distinction is between **owning the detail** and **routing the agent to it**.

A canonical document should own detailed information that needs one maintained source of truth. `AGENTS.md` and `.mdc` rules should contain the instructions needed at their scope and point to that canonical information instead of copying it.

The goal is not to send every instruction and every document with every request.

The goal is to give the model **the instructions and context needed for the current work**.

---

## `AGENTS.md` provides repository-level instructions

Some project instructions should remain broadly available while the agent works in the repository.

`AGENTS.md` is a good place for those repository-level instructions.

It can contain:

- important project constraints
- project-wide working rules
- boundaries the agent must respect
- pointers to authoritative project documents

For example, a short rule such as:

```text
Use Databricks source .py notebooks.
Do not use .ipynb files.
```

can belong directly in `AGENTS.md` when that constraint should apply across the repository.

But `AGENTS.md` should stay focused.

> **Navigate, don't duplicate.**

If a rule needs a longer explanation, detailed conventions, or several examples, that detail should usually have one canonical home. `AGENTS.md` can keep the short repository-level instruction and point the agent to the document that owns the full detail.

For example:

```text
Follow docs/standards/naming-conventions.md
for project naming rules.
```

The naming standard owns the detailed conventions. `AGENTS.md` makes sure the agent knows that those conventions govern repository work.

This avoids maintaining the same detailed rule in several places and reduces the chance that those copies drift apart.

So `AGENTS.md` has two related responsibilities:

1. supply concise repository-level constraints and working instructions
2. route the agent to deeper project information when more detail is required

In short:

> **Keep broad constraints in `AGENTS.md`; keep detailed maintainable knowledge in its canonical document.**

---

## Cursor rules add instructions for specific work

Not every project instruction needs to be available all the time.

Some instructions matter only for certain files or tasks.

Cursor handles this with **Project Rules** stored as `.mdc` files under:

```text
.cursor/rules/
```

A rule contains instructions for a particular kind of work.

When that rule is relevant, Cursor can **attach** it so those instructions are supplied to the model for the current task.

A rule can also tell the agent to read or use another project document.

For example, a rule may tell the agent to follow a coding standard or read a module-specific document before making changes.

The rule is not the owner of that detailed information. The source document still owns the detail; the rule helps the agent reach it when needed.

There is also an important portability difference:

- Cursor and standalone Codex can both use `AGENTS.md`.
- `.mdc` rules are a Cursor-specific mechanism.
- Standalone Codex does not interpret `.cursor/rules/*.mdc`.

So a project constraint that must also apply outside Cursor should not exist **only** inside an `.mdc` rule.

Once a repository contains several `.mdc` rules, Cursor needs to answer another question:

> **When should each rule attach?**

---

## How Cursor decides when a rule attaches

Cursor does not need every `.mdc` rule on every request.

Each rule therefore declares **when it should attach**.

That configuration is stored in **frontmatter** — a short YAML header at the top of the `.mdc` file.

Three fields are used:

- `alwaysApply`
- `description`
- `globs`

Their combination produces four rule modes:

| Cursor mode | `alwaysApply` | `description` | `globs` | When it attaches |
| --- | ---: | --- | --- | --- |
| **Always Apply** | `true` | ignored | ignored | Every Cursor Agent request |
| **Apply to Specific Files** | `false` | optional | set | A matching path is in the agent's context |
| **Apply Intelligently** | `false` | set | omitted | Cursor decides whether the description is relevant |
| **Apply Manually** | `false` | omitted | omitted | The rule is explicitly referenced |

**Always Apply** is for Cursor-specific instructions that must be available on every request. It should not be used to duplicate `AGENTS.md`.

These four modes belong to Cursor `.mdc` rules.

`AGENTS.md` is separate from them — it is **not a fifth rule mode**.

### Apply to Specific Files

When `globs` is set, the rule uses **Apply to Specific Files**, even if a `description` is also present.

A glob is a file-path pattern.

A glob can attach a rule when a matching file is in the agent's context — not simply because the file is open in an editor tab.

If the agent's context contains paths that match several rules, more than one rule can attach.

### Apply Intelligently

When there is no reliable file-path boundary, Cursor can use the rule's `description` to decide whether the rule is relevant to the current request.

Because Cursor makes that decision, **Apply Intelligently should not be the only place for an instruction that must never be missed**.

A hard constraint belongs in a more reliable instruction source.

### Apply Manually

A Manual rule has no automatic trigger.

It attaches when it is explicitly referenced.

### `@` is not a fifth mode

`@` is an explicit reference mechanism.

A rule mode controls **automatic attachment**.

An `@` reference explicitly includes a rule or file in the current request.

```text
rule mode
    → controls automatic attachment

@ reference
    → explicitly includes something in the request
```

Telling the agent to **open or read** a file is different.

An `@` reference supplies the referenced item as part of the request context.

An instruction to open or read a file tells the agent to retrieve that file as part of its work.

---

## Commands start workflows

Rules and commands solve different problems.

> **Rules answer:** What instructions should be available for this work?

> **Commands answer:** What workflow should the agent perform?

A Cursor command is a Markdown workflow stored under:

```text
.cursor/commands/
```

The user explicitly **invokes** a command when that workflow should run.

A rule attaching does not invoke a command.

Commands can also tell the agent which files, standards, or rules to use while performing the workflow.

So:

```text
rule
    → supplies instructions for relevant work

command
    → starts a workflow and may tell the agent what to use
```

The next files in this repository:

- [How This Repository Uses Rules and Standards](02-How-This-Repository-Uses-Rules-and-Standards.md) — this repo’s routing model
- [Workspace files and usage](03-Workspace%20Files%20and%20Usage.md) — workspace catalog
- [Markdown Context Routing Optimization](04-Markdown-Context-Routing-Optimization.md) — dated optimization report

