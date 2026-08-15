# Agents and Cursor Rules

The model that writes code is only part of an AI coding agent. The rest is
instructions, context, and tools. This file explains that mechanism. How
this repository wires it is in
[How This Repository Uses Rules and Standards](02-How-This-Repository-Uses-Rules-and-Standards.md).

## What an AI coding agent is

```text
AI coding agent
    = model
    + instructions
    + context
    + tools
```

Cursor and Codex are environments around the model. They can read and search
the repository, edit files, run terminal commands, and apply project
guidance. The environment decides what the model sees and what it is allowed
to do.

The model is the brain. Cursor or Codex is the workplace around that brain.

## Why a capable model still needs project instructions

A strong model already knows common languages and libraries. It does not
know the decisions this repository already made: which file format to use,
which features are in scope, which names and schemas are canonical.

Without those decisions written down, the agent can produce work that is
technically valid and still wrong for the project.

## `AGENTS.md` protects and navigates

A human-facing `README.md` answers what the project is and how to use it.
`AGENTS.md` answers how an agent should behave while working here.

The open `AGENTS.md` specification treats the file as a README for coding
agents: plain Markdown at a predictable path. Cursor and Codex both read it.

Keep `AGENTS.md` small. Put durable guardrails there — the constraints that
must hold on every request — and point to the documents that own the
details. A second copy will drift.

## Cursor rules are contextual

Cursor project rules live in `.cursor/rules/` as `.mdc` files. They solve a
different problem from `AGENTS.md`: this instruction matters only when this
kind of work is happening.

Rules are not a second copy of the standards. They route.

```text
AGENTS.md                          .mdc rule
(always on, every agent)           (Cursor only, when the work matches)
        \                              /
         \                            /
          ▼                          ▼
          canonical standards / data docs
```

Codex reads `AGENTS.md` and does not interpret `.cursor/rules/*.mdc`.

## Frontmatter and the four modes

Three frontmatter fields control when a project rule attaches:

```yaml
alwaysApply:
description:
globs:
```

Their combination is the rule mode. These four modes apply to project `.mdc`
rules. `AGENTS.md` is a separate always-on channel, not a fifth mode.

| Cursor mode | `alwaysApply` | `description` | `globs` | When it attaches |
| --- | ---: | --- | --- | --- |
| **Always Apply** | `true` | ignored | ignored | Every Cursor Agent request |
| **Apply to Specific Files** | `false` | optional | set | A matching file is in the Agent context |
| **Apply Intelligently** | `false` | set | omitted | Cursor decides whether the description fits |
| **Apply Manually** | `false` | omitted | omitted | Only when explicitly `@`-referenced |

**Always Apply.** Use this only for Cursor-specific guidance that must
appear on every Cursor request. Do not duplicate `AGENTS.md` in an
always-on `.mdc`.

**Apply to Specific Files.** If `globs` is set, that is the mode, even when
a `description` is also present.

The glob matches a path in the **Agent context** (the Agent request), not a
file sitting in an editor tab.

A glob is a path pattern. For example, `crates/*/src/**/*.rs` means Rust
sources under a crate, not every `.rs` file in the repository.

Several glob rules can attach in one request when several matching paths are
in the Agent context.

**Apply Intelligently.** A description with no glob lets Cursor decide
whether the topic fits. Missing the rule should be inconvenient, not
harmful: the model may skip it.

**Apply Manually.** No glob, no description, `alwaysApply: false`. Cursor
has no automatic reason to attach it.

**`@` is not a mode.** `@`-referencing a rule or file explicitly includes it
in this request. That works for any mode. Apply Manually has no automatic
path, so `@` is the only way it attaches.

Telling the agent to **open** a file is different: the agent is instructed
to go read it; the file is not already in the request.

## Commands start workflows

A rule supplies context. A command is a Markdown workflow under
`.cursor/commands/` that you invoke explicitly. Attaching a rule does not
run a command. Commands are Cursor-specific. How this repository uses them
is in Command workflows in
[How This Repository Uses Rules and Standards](02-How-This-Repository-Uses-Rules-and-Standards.md).
