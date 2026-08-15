# Agents and Cursor Rules

An AI coding agent can already understand Python, SQL, Spark, and many other technologies. But that is not enough to work correctly inside a specific repository.

The real question is:

> **How does the right project guidance reach the agent at the right time?**

This file builds that mental model. The next file, [How This Repository Uses Rules and Standards](02-How-This-Repository-Uses-Rules-and-Standards.md), shows how this repository implements it.

---

## What an AI coding agent needs

A language model can reason about code and generate changes. An **AI coding agent** adds the environment needed to work inside a repository.

```text
AI coding agent
    = model
    + instructions
    + context
    + tools
```

Each part has a different job:

* **Model** — reasons about the task and generates the response or code.
* **Instructions** — tell the model how it should behave.
* **Context** — gives the model the files and project information needed for the current task.
* **Tools** — let the agent read, search, edit, and run commands.

Cursor and Codex are agent environments around the model. They help decide what instructions and repository context the model receives and what actions it can perform.

The model may already know the technology. It still needs to learn **how this particular repository expects that technology to be used**.

---

## Why project guidance needs different layers

Every repository makes decisions that a general model cannot know in advance.

For example:

* which file format the project uses
* which features are in or out of scope
* which naming conventions are canonical
* which datasets, schemas, or interfaces are authoritative
* which actions are prohibited

Without that guidance, an agent can produce code that is technically valid but still wrong for the project.

But there is another problem:

> **Not every instruction belongs in every request.**

Some guidance should apply throughout the repository.

Some guidance matters only when a certain kind of file or task is involved.

Detailed standards may already live in dedicated documents and should not be copied into every instruction file.

That leads to three different responsibilities:

| Layer                      | Responsibility                                  |
| -------------------------- | ----------------------------------------------- |
| `AGENTS.md`                | Repository-level guidance and navigation        |
| Cursor `.mdc` rules        | Add guidance when a particular context needs it |
| Canonical docs / standards | Own the detailed knowledge                      |

The goal is not to load every document all the time.

The goal is to give the agent **the right guidance for the current work**.

---

## `AGENTS.md` provides repository-level guidance

`AGENTS.md` gives coding agents instructions about how to work inside a repository.

It is the right place for guidance that should remain broadly applicable, such as:

* important repository constraints
* project-wide working rules
* boundaries the agent must respect
* pointers to canonical documentation

A useful `AGENTS.md` should stay small.

Instead of copying an entire coding standard or data contract into it, point the agent to the document that owns that information.

The principle is:

> **Navigate, don't duplicate.**

If the same detailed rule is copied into several instruction files, those copies can eventually disagree.

`AGENTS.md` should guide the agent toward the source of truth rather than become another copy of it.

---

## Cursor rules add context-specific guidance

Repository-level guidance is not enough for every situation.

Imagine that one set of instructions matters only when working on configuration files, while another matters only when reviewing tests.

Loading both sets for every task would add unnecessary context.

Cursor solves this with **Project Rules** stored as `.mdc` files under:

```text
.cursor/rules/
```

A Cursor rule can provide additional guidance only when that guidance is relevant.

Conceptually:

```text
Repository-wide guidance
        │
        ▼
    AGENTS.md

Context-specific guidance
        │
        ▼
    .mdc rules

Detailed knowledge
        │
        ▼
canonical docs / standards
```

An `.mdc` rule is therefore not another place to copy the standards.

Its main job is to help Cursor provide the **right additional context for the current work**.

There is also a portability boundary:

> `AGENTS.md` is supported by agent environments such as Cursor and Codex. Cursor `.mdc` rules are a Cursor-specific mechanism.

Standalone Codex does not interpret `.cursor/rules/*.mdc`.

So an important project constraint that must not depend on Cursor-specific rule matching should not exist **only** inside an `.mdc` rule.

---

## How Cursor decides when a rule applies

Once a repository has several `.mdc` rules, Cursor needs to answer another question:

> **When should each rule enter the Agent's context?**

Project-rule frontmatter provides that loading behavior.

The three important fields are:

```yaml
alwaysApply:
description:
globs:
```

Their combination produces four rule modes. These four modes apply to project `.mdc` rules. `AGENTS.md` is a separate always-on channel, not a fifth mode.

| Cursor mode                 | `alwaysApply` | `description` | `globs` | When it attaches                                   |
| --------------------------- | ------------: | ------------- | ------- | -------------------------------------------------- |
| **Always Apply**            |        `true` | ignored       | ignored | Every Cursor Agent request                         |
| **Apply to Specific Files** |       `false` | optional      | set     | A matching path is in the Agent context            |
| **Apply Intelligently**     |       `false` | set           | omitted | Cursor decides whether the description is relevant |
| **Apply Manually**          |       `false` | omitted       | omitted | The rule is explicitly referenced                  |

### Always Apply

Use this for Cursor-specific guidance that must be present on every Cursor Agent request.

Do not use an always-on `.mdc` rule merely to duplicate `AGENTS.md`.

### Apply to Specific Files

Use this when the guidance has a reliable file-path boundary.

The `globs` field contains path patterns that tell Cursor which files the rule belongs with.

If `globs` is set, that is the mode even when a `description` is also present.

The important point is:

> A glob matches a path in the **Agent context**, not simply a file that happens to be open in an editor tab.

For example:

```text
services/*/tests/**/*.ts
```

targets matching TypeScript test paths under service folders.

More than one glob-based rule can apply when the Agent context contains paths matching more than one rule.

### Apply Intelligently

Use this when relevance depends on the **meaning of the task** rather than a reliable file path.

The rule's `description` helps Cursor decide whether the rule should be included.

Because that decision is contextual, this mode should not be the only home for a hard constraint.

If missing a rule could make the agent perform an unsafe or prohibited action, that constraint belongs in a more reliable instruction layer.

### Apply Manually

A Manual rule has no automatic trigger.

It is included when explicitly referenced.

### `@` is not a fifth mode

`@` is an explicit reference mechanism.

You can explicitly reference a rule or another file even when that rule normally uses a different mode.

So these are different ideas:

```text
rule mode
    → controls automatic loading behavior

@ reference
    → explicitly includes something in the current request
```

Telling the agent to **open or read** a file is different again.

An `@` reference supplies the referenced item as context for the request. An instruction to open a file tells the agent to go and read that file as part of its work.

---

## Commands start workflows

Rules answer:

> **What guidance should be available for this work?**

Commands answer a different question:

> **What workflow should the agent perform?**

A Cursor command is an explicitly invoked Markdown workflow under:

```text
.cursor/commands/
```

A rule being loaded does **not** execute a command.

The next file shows how this repository combines `AGENTS.md`, `.mdc` rules, standards, and commands in real authoring and review workflows:

[How This Repository Uses Rules and Standards](02-How-This-Repository-Uses-Rules-and-Standards.md)
