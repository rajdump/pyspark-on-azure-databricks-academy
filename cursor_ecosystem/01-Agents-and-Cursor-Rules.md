# Agents and Cursor Rules

An AI coding agent is more than a language model. The practical question is
how the right guidance reaches that agent at the right time.

This file explains that mechanism. How this repository wires it is in
[How This Repository Uses Rules and Standards](02-How-This-Repository-Uses-Rules-and-Standards.md).

## What an AI coding agent is

A language model can write code. Working in a repository also needs
instructions, context, and tools.

```text
AI coding agent
    = model
    + instructions
    + context
    + tools
```

The model reasons. Instructions and context tell it what this project
requires. Tools let it read files, search the repository, edit, and run
commands.

Cursor and Codex are environments around the model. They decide what the
model sees and what it is allowed to do.

The model is the brain. Cursor or Codex is the workplace around that brain.

## Why a capable model still needs project instructions

A strong model already knows common languages and libraries. It does not
know the decisions this repository already made: which file format to use,
which features are in scope, which names and schemas are canonical.

Without those decisions written down, the agent can produce work that is
technically valid and still wrong for the project.

The next question is where those instructions live, and which of them belong
on every request.

## `AGENTS.md` protects and navigates

Not all project guidance has the same scope. Constraints that must hold on
every request belong in a small, always-on file. Detailed standards belong
in the documents that own them.

A human-facing `README.md` answers what the project is and how to use it.
`AGENTS.md` answers how an agent should behave while working here.

The open `AGENTS.md` specification treats the file as a README for coding
agents: plain Markdown at a predictable path. Cursor and Codex both read it.

Keep `AGENTS.md` small. Navigate, don't duplicate. A second copy will drift.

## Cursor rules are contextual

Most guidance should enter context only when the request needs it.

Cursor project rules live in `.cursor/rules/` as `.mdc` files. They add
Cursor-specific guidance when the relevant context requires it.

Rules are not a second copy of the standards. They route.

```text
AGENTS.md                          .mdc rule
(always on, every agent)           (Cursor only, when the work matches)
        \                              /
         \                            /
          ▼                          ▼
          canonical standards / data docs
```

`AGENTS.md` holds repository-wide guidance and navigation. `.mdc` rules add
context-specific routing in Cursor. Canonical docs and standards own the
details.

Codex reads `AGENTS.md`. Standalone Codex does not interpret
`.cursor/rules/*.mdc`. `.mdc` is a Cursor-specific context mechanism.

## Frontmatter and the four modes

Cursor needs a way to decide when a project rule should enter the Agent's
context. The rule's frontmatter provides that loading behavior.

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

**Apply to Specific Files.** When guidance belongs to a certain kind of
file, a **glob** (a path pattern) is the reliable signal. If `globs` is
set, that is the mode, even when a `description` is also present.

The glob matches a path in the **Agent context** (the Agent request), not a
file sitting in an editor tab.

For example, `crates/*/src/**/*.rs` means Rust sources under a crate, not
every `.rs` file in the repository.

Several glob rules can attach in one request when several matching paths are
in the Agent context.

**Apply Intelligently.** When there is no reliable path, a description with
no glob lets Cursor decide whether the topic fits. Missing the rule should
be inconvenient, not harmful: the model may skip it.

**Apply Manually.** No glob, no description, `alwaysApply: false`. Cursor
has no automatic reason to attach it.

**`@` is not a mode.** `@`-referencing a rule or file explicitly includes it
in this request. That works for any mode. Apply Manually has no automatic
path, so `@` is the only way it attaches.

Telling the agent to **open** a file is different: the agent is instructed
to go read it; the file is not already in the request.

## Commands start workflows

Once the right guidance can attach, you still need a way to start a
repeatable task.

A rule supplies context. A command is a Markdown workflow under
`.cursor/commands/` that you invoke explicitly. Attaching a rule does not
run a command. Commands are Cursor-specific. How this repository uses them
is in Command workflows in
[How This Repository Uses Rules and Standards](02-How-This-Repository-Uses-Rules-and-Standards.md).
