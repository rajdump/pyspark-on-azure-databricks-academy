# Agents and Cursor Rules

A capable language model may already know Python, SQL, Spark, and many other technologies.

But it does not automatically know the decisions made by a specific project:

- which formats to use
- which features are in or out of scope
- which names and schemas are authoritative
- where the source of truth lives

Without that project knowledge, the model can produce code that is technically correct but still wrong for the repository.

That leads to the main question:

> **How does the right project guidance reach an AI coding agent at the right time?**

This file explains that mechanism. The next file, [How This Repository Uses Rules and Standards](02-How-This-Repository-Uses-Rules-and-Standards.md), shows how this repository implements it.

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
- **Instructions** — tell the model how it should behave.
- **Context** — provides the files and project information needed for the current request.
- **Tools** — let the agent read, search, edit, and run commands.

Together, these let the model work inside a repository.

But the agent still needs one more thing: the project's own guidance.

## Why project guidance needs different layers

Project guidance includes decisions a general model cannot know on its own: project scope, naming rules, approved formats, authoritative schemas, and actions that are not allowed.

But **not every instruction belongs in every request**.

Some guidance should be available across the repository.

Some guidance is needed only for certain files or tasks.

And detailed standards should remain in the documents that own them rather than being copied into instruction files.

That gives us three different responsibilities:

| Layer | Responsibility |
| --- | --- |
| `AGENTS.md` | Repository-level guidance and navigation |
| Cursor `.mdc` rules | Add guidance when the current work needs it |
| Canonical docs / standards | Own the detailed source of truth |

The goal is not to give the agent every document on every request.

The goal is to give it **the right guidance for the current work**.

```text
AGENTS.md → broad guidance
.mdc       → relevant extra guidance
standards  → detailed truth
```

## `AGENTS.md` provides repository-level guidance

Some guidance should remain available regardless of which file or task the agent is working on.

That is the role of `AGENTS.md`.

It can hold:

- important repository constraints
- project-wide working rules
- boundaries the agent must respect
- pointers to authoritative documentation

But `AGENTS.md` should stay small.

> **Navigate, don't duplicate.**

If a detailed standard already has a source of truth, point the agent to that document instead of copying the same content into `AGENTS.md`.

Otherwise, the copies can drift and eventually disagree.

## Cursor rules add context-specific guidance

`AGENTS.md` handles guidance that should remain broadly available across the repository.

But some guidance is needed only for certain files or tasks. Including that guidance in every request would add unnecessary context.

Cursor handles this with **Project Rules** stored as `.mdc` files under:

```text
.cursor/rules/
```

A Cursor rule can **attach** additional guidance when the current work needs it.

This gives each layer a clear responsibility:

```text
Repository-level guidance  →  AGENTS.md
Context-specific guidance  →  .mdc rules
Detailed source of truth   →  canonical docs / standards
```

An `.mdc` rule can bring relevant instructions into the Agent context and point the agent to the documents it needs.

It should not become another copy of those documents.

There is also an important portability difference:

* `AGENTS.md` can guide both Cursor and standalone Codex.
* `.mdc` rules are specific to Cursor.
* Standalone Codex does not interpret `.cursor/rules/*.mdc`.

Therefore, a hard project constraint that must apply outside Cursor should not live **only** in an `.mdc` rule.

Once a repository has several `.mdc` rules, Cursor needs to answer the next question:

> **When should each rule attach?**

## How Cursor decides when a rule applies

Attaching every `.mdc` rule to every request would defeat the purpose of
context-specific guidance. Each rule therefore declares when it should
attach.

That declaration appears in **frontmatter**, a short YAML header at the top of
the `.mdc` file. Three fields determine the rule's mode:

- `alwaysApply` says whether the rule should attach to every Cursor Agent
  request.
- `globs` identifies file-path patterns associated with the rule.
- `description` explains the kind of work for which the rule is relevant.

Their combinations produce four modes:

| Cursor mode                 | `alwaysApply` | `description` | `globs` | When it attaches                                   |
| --------------------------- | ------------: | ------------- | ------- | -------------------------------------------------- |
| **Always Apply**            |        `true` | ignored       | ignored | Every Cursor Agent request                         |
| **Apply to Specific Files** |       `false` | optional      | set     | A matching path is in the Agent context            |
| **Apply Intelligently**     |       `false` | set           | omitted | Cursor decides whether the description is relevant |
| **Apply Manually**          |       `false` | omitted       | omitted | The rule is explicitly referenced                  |

`AGENTS.md` is separate from these four Cursor `.mdc` modes. Use **Always
Apply** for Cursor-specific guidance needed on every request, not to copy
`AGENTS.md`.

When `globs` is set, the rule uses **Apply to Specific Files**, even if
`description` is also present. A glob matches a path in **Agent context**, not
merely a file open in an editor tab. If paths in the Agent context match
several rules, all of those rules can attach.

**Apply Intelligently** depends on Cursor deciding that a description is
relevant to the request. It must not be the sole home of a hard constraint. A
constraint that cannot safely be missed belongs in a more reliable guidance
layer.

`@` is not a fifth mode. It explicitly supplies a referenced rule or file as
context for the current request. A mode controls when a rule attaches
automatically.

Telling the agent to open or read a file is different. The `@` reference
provides the item as context for the request. An instruction to open or read
the file asks the agent to retrieve it as part of its work.

## Commands start workflows

Guidance and workflows solve different problems. Rules supply guidance.
Commands start workflows.

A Cursor command is a Markdown workflow stored under `.cursor/commands/`.
The user explicitly **invokes** it when that workflow should run. A rule
attaching does not invoke a command.

[How This Repository Uses Rules and Standards](02-How-This-Repository-Uses-Rules-and-Standards.md)
shows how this repository combines these mechanisms.
