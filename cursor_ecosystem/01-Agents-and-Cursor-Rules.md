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

An **AI coding agent** adds the working environment around that model:

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
- **Context** — provides the files and project information available for the current request.
- **Tools** — let the agent read, search, edit, and run commands.

Together, these let the model work with a repository.

But knowing how to work with files and tools is not enough.

The agent still needs to know **what this particular project expects**.

Think of a skilled developer joining a new team. They already know how to code, but they still need the team's conventions, repo layout, and boundaries — including what not to change. An AI agent needs the same kind of project-specific guidance.

Project instructions and rules do not replace the model's general knowledge. They direct that knowledge toward what this repository expects.

---

## Why project instructions need different layers

A project may have many instructions the agent needs to follow.

But those instructions do not all need to reach the agent in the same way.

Some instructions should be available broadly across the repository.

Some are needed only for particular files or tasks.

Detailed rules and definitions may already live in dedicated documents and should remain the source of truth instead of being copied into every instruction file.

That gives each layer a different job:

| Need | Where it belongs |
| --- | --- |
| Instructions that should apply broadly across the repository | `AGENTS.md` |
| Additional instructions needed for particular work | Cursor `.mdc` rules |
| Detailed rules, definitions, and project information | Canonical docs / standards |

The goal is not to give the agent every instruction and document on every request.

The goal is to give it **what it needs for the current work**.

---

## `AGENTS.md` provides repository-level instructions

A root `AGENTS.md` is a good place for project instructions that should remain broadly available while the agent works in the repository.

It can contain:

- important project constraints
- project-wide working rules
- boundaries the agent must respect
- pointers to authoritative project documents

`AGENTS.md` should stay focused.

> **Navigate, don't duplicate.**

If a detailed rule already exists in another document, `AGENTS.md` should point the agent to that document instead of copying the same rule.

For example, if detailed naming rules already live in a naming-standard document, `AGENTS.md` can tell the agent to use that document rather than repeating all of its contents.

This keeps one source of truth for the detailed rule and reduces the chance that multiple copies drift apart.

---

## Cursor rules add instructions for specific work

Some project instructions are needed only for certain files or tasks.

Those instructions do not need to be included in every request.

Cursor handles this with **Project Rules** stored as `.mdc` files under:

```text
.cursor/rules/
```

When a rule is relevant to the current work, Cursor can **attach** it to the agent's context.

The attached rule can then:

- provide instructions needed for that work
- point the agent to additional documents it should use

An `.mdc` rule should not become another copy of a detailed project document. The detailed information should remain in its source of truth; the rule helps the agent reach it when needed.

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

A hard constraint belongs in a more reliable instruction layer.

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
    → explicitly includes context
```

Telling the agent to **open or read** a file is different.

An `@` reference provides the referenced item as context for the request.

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

The next file, [How This Repository Uses Rules and Standards](02-How-This-Repository-Uses-Rules-and-Standards.md), shows how this repository combines `AGENTS.md`, `.mdc` rules, canonical documents, and commands in real workflows.
