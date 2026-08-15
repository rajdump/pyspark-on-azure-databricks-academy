# Agents and Cursor Rules

A capable language model already knows Python, SQL, Spark, and many other technologies. It still does not know how a particular repository expects those technologies to be used.

Until those project decisions reach the model, it can produce work that is valid in general and wrong here.

The rest of this file answers one question:

> **How does the right project guidance reach an AI coding agent at the right time?**

The next file, [How This Repository Uses Rules and Standards](02-How-This-Repository-Uses-Rules-and-Standards.md), shows how this repository implements the same idea.

## What an AI coding agent needs

Getting those decisions to the model is the job of an **AI coding agent**, not of the model alone.

The agent is the model plus the environment around it. That environment feeds the model instructions, gives it context, and lets it use tools.

The model reasons about the task and generates the response. Instructions constrain how it should behave. Context supplies the files and project information for this request. Tools let it read, search, edit, and run commands.

The agent environment decides what the model sees. The missing piece is **project guidance**.

## Why project guidance needs different layers

Every repository makes decisions a general model cannot know in advance: which file format to use, which features are in or out of scope, which names are canonical, which schemas or interfaces are authoritative, and which actions are prohibited.

Not every instruction belongs in every request.

Some guidance should be present throughout the repository. Some matters only for a certain kind of file or task. Detailed standards already live in dedicated documents. Copying them into every instruction file wastes context.

Those are three different jobs: repository-wide guidance, extra guidance only for particular work, and detailed knowledge that already has an owner.

`AGENTS.md` holds the first. Cursor `.mdc` rules hold the second. Canonical docs and standards own the third.

## `AGENTS.md` provides repository-level guidance

`AGENTS.md` is the repository-level channel for guidance that must be available no matter which file the agent is touching. It holds important constraints, project-wide working rules, boundaries the agent must respect, and pointers to canonical documentation. Keep it small.

> **Navigate, don't duplicate.**

If the same detailed rule is copied into several instruction files, those copies can disagree. `AGENTS.md` should send the agent to the document that owns the detail.

## Cursor rules add context-specific guidance

Repository-level guidance is the wrong shape for advice that only matters for certain files or tasks. Instructions that belong with configuration files do not help a test review.

Cursor can **attach** extra guidance only when it is relevant.

That extra guidance lives in `.mdc` files under `.cursor/rules/`. An `.mdc` rule routes the right additional context for the current work. It does not own the detailed standards.

```text
Repository-wide guidance  →  AGENTS.md
Context-specific guidance →  .mdc rules
Detailed knowledge        →  canonical docs / standards
```

`AGENTS.md` is a repository convention that Cursor and standalone Codex both read. `.mdc` rules are Cursor-specific. Standalone Codex does not interpret `.cursor/rules/*.mdc`.

A constraint that must not depend on Cursor matching must not live **only** in an `.mdc` rule.

Once several `.mdc` rules exist, Cursor still has to decide when each one attaches.

## How Cursor decides when a rule applies

Each `.mdc` file declares when it should attach.

The declaration sits in a short header at the top of the file, called frontmatter. The fields `alwaysApply`, `description`, and `globs` combine into four modes.

Sometimes the extra guidance must be present on every Cursor Agent request, and it is Cursor-specific rather than a recopy of `AGENTS.md`. That is **Always Apply**.

Sometimes the guidance has a reliable file-path boundary. That is **Apply to Specific Files**.

Sometimes relevance depends on the meaning of the task, not on a path. That is **Apply Intelligently**.

Sometimes there is no automatic trigger. The rule attaches only when it is explicitly referenced. That is **Apply Manually**.

These four modes belong to project `.mdc` rules. `AGENTS.md` is a separate always-on channel, not a fifth mode.

| Cursor mode                 | `alwaysApply` | `description` | `globs` | When it attaches                                   |
| --------------------------- | ------------: | ------------- | ------- | -------------------------------------------------- |
| **Always Apply**            |        `true` | ignored       | ignored | Every Cursor Agent request                         |
| **Apply to Specific Files** |       `false` | optional      | set     | A matching path is in the Agent context            |
| **Apply Intelligently**     |       `false` | set           | omitted | Cursor decides whether the description is relevant |
| **Apply Manually**          |       `false` | omitted       | omitted | The rule is explicitly referenced                  |

If `globs` is set, the mode is **Apply to Specific Files**, even when `description` is also present. A glob matches a path in the **Agent context**, not merely a file that is open in an editor tab. More than one matching rule can attach at once.

Apply Intelligently must not be the sole home for a hard constraint. If missing the rule could let the agent do something unsafe or prohibited, that constraint belongs in a more reliable layer.

`@` is not a fifth mode. It is an explicit reference mechanism. A rule's mode controls automatic attachment. An `@` reference explicitly includes something in the current request, including a rule that would not otherwise attach.

Telling the agent to open or read a file is different. An `@` reference supplies the item as context for the request. An instruction to open a file tells the agent to go read that file as part of its work.

## Commands start workflows

Attaching the right guidance still does not start a named procedure.

Rules answer what guidance should be available for this work. Commands answer what workflow the agent should perform.

A Cursor command is an explicitly **invoked** Markdown workflow under `.cursor/commands/`. A rule attaching does not invoke a command.

[How This Repository Uses Rules and Standards](02-How-This-Repository-Uses-Rules-and-Standards.md) shows how this repository puts these layers to work.
