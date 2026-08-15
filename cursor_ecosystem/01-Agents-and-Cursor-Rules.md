# Agents and Cursor Rules

A capable language model can write Python, SQL, Spark, and many other
technologies. But it cannot know the decisions made inside a repository it has
never seen.

It does not know which file format the project requires, which features are
out of scope, or where the source of truth lives. Without that knowledge, it
can produce code that works in general but is wrong for the project.

That leads to the central question:

> **How does the right project guidance reach an AI coding agent at the right time?**

## What an AI coding agent needs

A language model can reason about a task and generate a response. An **AI
coding agent** surrounds that model with instructions, context, and tools.

The model does the reasoning. Instructions tell it how to behave. Context
supplies the files and information needed for the current request. Tools let
the agent read, search, edit, and run commands.

The agent environment brings these parts together. To work correctly in a
repository, it must also give the model the project's own guidance.

## Why project guidance needs different layers

Project guidance covers decisions a general model cannot know. These include
the project's scope, naming conventions, approved formats, authoritative
schemas or interfaces, and prohibited actions.

Sending all of that guidance with every request would create a new problem.
Some instructions matter throughout the repository, while others matter only
for a particular file or task. Detailed standards may also be too long to
repeat in instruction files.

The guidance therefore has three different jobs:

- provide directions that apply across the repository
- add directions needed only for the current work
- preserve detailed knowledge in a single source of truth

## `AGENTS.md` provides repository-level guidance

Some instructions should be available wherever the agent works in the
repository. `AGENTS.md` provides that repository-level guidance.

It is a good place for broad constraints, working rules, important boundaries,
and directions to authoritative documents. It should remain small enough to
guide the agent without repeating those documents.

The principle is:

> **Navigate, don't duplicate.**

If a detailed standard is copied into several instruction files, the copies
can drift apart. `AGENTS.md` should point to the document that owns the detail
instead of becoming another version of it.

## Cursor rules add context-specific guidance

Some guidance is useful only for certain work. For example, test instructions
help when the agent is editing tests. They are unnecessary when the agent is
editing a configuration file.

Cursor can attach this extra guidance when it is relevant. The guidance lives
in `.mdc` files under `.cursor/rules/`.

An `.mdc` rule routes context to the agent. It does not become the owner of the
detailed standard that it points to.

```text
Repository-level guidance → AGENTS.md
Context-specific guidance → .mdc rules
Detailed source of truth  → canonical docs / standards
```

Cursor and standalone Codex do not use these files in the same way. Both read
`AGENTS.md`, but standalone Codex does not interpret Cursor `.mdc` rules.

A hard constraint that must reach both environments must therefore not live
only in an `.mdc` rule.

Once a repository has several `.mdc` rules, Cursor needs a way to decide when
each rule should attach.

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
