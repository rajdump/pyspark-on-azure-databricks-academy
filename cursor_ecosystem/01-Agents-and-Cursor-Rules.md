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
- **Context** — gives the model the information available for the current task.
- **Tools** — let the agent read, search, edit, and run commands.

The important point is that **instructions** is a broad category.

Instructions can come from several places:

- your prompt
- `AGENTS.md`
- Cursor `.mdc` rules
- commands or other instructions supplied by the agent environment

A **rule** is one source of instructions. For example, a Cursor `.mdc` rule can contain instructions about what the agent should do for a particular kind of work.

A standards document is different in role. It is where detailed project rules, definitions, or conventions may live.

For example:

```text
coding-standards.md
    → detailed coding rules

naming-conventions.md
    → detailed naming rules
```

Those documents can still contain instructions. The difference is **how the model receives them**.

A prompt, `AGENTS.md`, a rule, or a command may tell the agent to read or use a standards document. Once that document is read or supplied, its content becomes part of the **context** available to the model.

So:

```text
Instructions
    → tell the model what to follow

Rules
    → one way to supply instructions

Standards / project docs
    → store detailed rules and knowledge

Context
    → what the model has available for the current task
```

The overall picture is:

```text
                     AI agent
        ┌─────────────────────────────┐
        │ instructions                │
        │   ← your prompt             │
        │   ← AGENTS.md               │
        │   ← attached .mdc rules     │
        │   ← commands                │
        │                             │
        │ context                     │
        │   ← files / docs / schemas  │
        │                             │
        │ tools                       │
        │   ← read / search / edit    │
        │                             │
        │        LLM model            │
        └─────────────────────────────┘
```

Together, these let the model work with a repository.

But the agent still needs to know **what this particular project expects**.

---

## Why project instructions need different layers

A project may have many instructions the agent needs to follow.

But those instructions do not all need to reach the model in the same way.

Some instructions should be available broadly across the repository.

Some are needed only for particular files or tasks.

Detailed rules and definitions may already live in canonical project documents and should stay there as the source of truth.

That gives each part a different role:

| Need | Where it belongs |
| --- | --- |
| Instructions that should apply broadly across the repository | `AGENTS.md` |
| Additional instructions needed for particular work | Cursor `.mdc` rules |
| Detailed project rules, definitions, and reference information | Canonical docs / standards |

`AGENTS.md` and `.mdc` rules are **instruction sources**.

Canonical docs and standards are where detailed project information lives. When the agent reads or receives them, that content becomes part of the model's context.

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

`AGENTS.md` should stay focused.

> **Navigate, don't duplicate.**

If a detailed rule already exists in another document, `AGENTS.md` should point the agent to that document instead of copying the same content.

For example, if detailed naming conventions already live in a naming-standard document, `AGENTS.md` can tell the agent to use that document rather than repeating all of its rules.

This keeps one source of truth for the detailed information and reduces the chance that multiple copies drift apart.

So `AGENTS.md` does two important things:

1. supplies repository-level instructions
2. tells the agent where deeper project information lives

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

The next file, [How This Repository Uses Rules and Standards](02-How-This-Repository-Uses-Rules-and-Standards.md), shows how this repository combines `AGENTS.md`, `.mdc` rules, project documents, and commands in real workflows.
