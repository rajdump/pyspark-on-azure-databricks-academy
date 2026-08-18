# Rule Authoring Standard

This file is the canonical owner of the structure of Cursor project rules in
`.cursor/rules/*.mdc`. A rule detects a context and routes the agent to the
canonical owner of the work. It never owns domain rules itself, except for the
one scoped policy a Type 3 rule is explicitly delegated.

Direct readers: agents creating or auditing a rule file. The rules themselves —
`.cursor/rules/command-authoring.mdc`, `.cursor/rules/learner-notebooks.mdc`,
`.cursor/rules/course-authoring.mdc`, and
`.cursor/rules/notebook-command-output.mdc` — are the artifacts this standard
governs rather than its readers. It has no indirect consumers in lesson or
module-authoring workflows.

Terms used below:

- **Attachment** is Cursor deciding a rule applies to the current request,
  either because a `globs` pattern matches a path in Agent context or because
  the `description` matches the situation. Attachment is Cursor-only; standalone
  Codex reads `AGENTS.md` and ignores `.mdc`.
- An **active command** is a slash command the author invoked for this turn.
- An **ad-hoc edit** is work on a matching artifact with no active command.

## Choosing a rule type

Confirm first that the instruction belongs in `.cursor/rules/` at all:

- It must hold for agents that never read `.mdc` → `AGENTS.md`.
- It is a detailed domain rule → `docs/standards/`.
- It is a user-invoked workflow → `.cursor/commands/`, structured by
  `docs/standards/command-authoring.md`.

What remains is a rule. Every rule performs exactly one of three jobs, and a
rule that wants two jobs is two rules.

| Type | Job | Frontmatter | Example |
|---|---|---|---|
| 1 — Attachment router | Attach one canonical standard when a matching artifact is edited | `description` and `globs` | `.cursor/rules/command-authoring.mdc` |
| 2 — Context router | Select which instructions apply, based on whether a command is active | `description` and `globs` | `.cursor/rules/learner-notebooks.mdc` |
| 3 — Policy rule | Own one scoped policy that consumers load explicitly | `description` only | `.cursor/rules/notebook-command-output.mdc` |

Choose Type 1 over Type 2 whenever behavior does not change between an active
command and an ad-hoc edit. A short Type 1 rule is complete, not deficient.

## Type 1 — attachment router

Two blocks and nothing else: a one-sentence scope, then one read instruction
naming the owning standard and the sections to apply.

A Type 1 rule must not add a precedence statement, an ownership reminder, or a
boundaries pointer. Those exist to resolve conflicts a Type 1 rule cannot have,
because it routes to exactly one owner.

```markdown
---
description: <artifact class> authoring structure
globs: ["<pattern>"]
alwaysApply: false
---

You are editing <artifact> in `<location>`.

Read `docs/standards/<owner>.md` and follow its [[<Required section>]].
```

## Type 2 — context router

Use this type only when instructions differ between an active command and an
ad-hoc edit. Blocks in this order:

1. **Scope** — one sentence naming the artifact in context.
2. **Command-active path** — defer to the active command's declared reads.
   Expand only within that command's canonical sources when a scoped read does
   not establish an answer. Never load another command's manifest, and never
   load the ad-hoc path as well.
3. **Ad-hoc path** — for each target state, a backticked canonical path plus the
   exact sections to apply, and the condition that selects that branch.
4. **Workflow** — the slash command the author should prefer, and the review
   step that follows it. Include only at a real workflow transition.
5. **Precedence** — which source wins when the artifact conflicts with it.
6. **Boundaries** — the `AGENTS.md` [[Author-only writes]] pointer. Include only
   when the governed artifact class can trigger an author-only write.

The two read paths are mutually exclusive. A rule must never let an ad-hoc list
run alongside a command manifest, in either direction.

```markdown
---
description: <domain> authoring rules
globs: ["<pattern>", "<pattern>"]
alwaysApply: false
---

You are editing <artifact/context>.

When `<command>` is active, follow its declared reads. Expand within those
reads and <its canonical sources> when a scoped read is insufficient; do not
load the ad-hoc list below or a different command's manifest.

For ad-hoc edits with no active command:

- **<target state>** — read `docs/standards/<owner>.md` and apply
  [[<Section>]] and [[<Section>]].
- **<other target state>** — apply [[<Other section>]]. Read
  `docs/standards/<conditional owner>.md` only when <condition>.

For <operation>, the author should use `<command>` (not ad-hoc chat) so reads
and stop conditions load consistently.

<Owner> is canonical. If the artifact conflicts with it, follow that source.

Automatic-write restrictions are owned by the [[Author-only writes]] section in
`AGENTS.md`.
```

## Type 3 — policy rule

Use this type when consumers load the rule explicitly rather than through file
attachment. A policy rule owns one scoped policy — an output contract, for
example — and nothing about workflow or domain detail.

A Type 3 rule carries no `globs`. Discoverability comes from the `@` reference
in its consumers, so adding a pattern only to make the file findable creates a
second, unintended attachment path.

Headings are expected here, unlike Types 1 and 2: a policy rule states shared
rules once, then the requirements specific to each consumer.

```markdown
---
description: <policy> for <consumers>
alwaysApply: false
---

# <Policy title>

<One sentence stating the shared policy.>

## <Shared section>

- <rule>

## `<consumer A>`

- <requirement>

## `<consumer B>`

- <requirement>
```

## Attachment modes

`alwaysApply: true` is prohibited. Standalone Codex reads `AGENTS.md` but does
not interpret `.mdc`, so a repository-wide constraint placed in an
always-applied rule silently stops applying outside Cursor. Put that constraint
in `AGENTS.md`, which is where [[Read for facts]] and [[Hard constraints]]
already live.

A manual rule — no `description` and no `globs` — is permitted only for
author-invoked scratch work. None exists. Adding one requires a stated reason
inside the rule.

## Frontmatter

Three fields, and no others. Do not invent frontmatter keys.

- `description` — always required. For Types 1 and 2 it labels the artifact
  class, because `globs` does the attaching. For Type 3 it *is* the attachment
  trigger and must name the situations that should pull the rule in.
- `globs` — required for Types 1 and 2, forbidden for Type 3. Always the
  bracketed list form, `["<pattern>"]`, with every pattern quoted, even when
  there is only one. That is the form whose attachment behavior this repository
  has exercised; do not switch a working rule to another YAML spelling, since
  attachment cannot be verified locally.
- `alwaysApply` — always written explicitly, and always `false`.

Write a pattern that matches the intended artifact class and nothing wider.
`[0-9][0-9] - */README.md` matches numbered module READMEs and correctly misses
`vault/README.md`; a bare `README.md` pattern would not.

## Reads and references

- Reference form is owned by [[References]] in
  `docs/standards/standards-authoring.md`. This standard adds only the
  restrictions below.
- Never use `@path` in a rule. A rule that needs a whole file is routing to the
  wrong place, and the cost is paid on every attachment. Commands may use
  `@path` with a stated reason; rules may not.
- Prefer a scoped read: a backticked path followed by the exact section names.
  Cursor has no section-level `@path` syntax, so the agent locates and reads
  those sections with search and read tools.
- Never reload a standard the active command already declared.
- A rule defines no guard, bar, or acceptance gate of its own. When a rule must
  mention a stop, it names the source that owns it.

## Size and cost

A rule is loaded whenever it attaches, so its length is a recurring cost paid
before any useful work begins.

- Type 1: about ten lines. If it grows, the extra content belongs in the
  standard it points to.
- Type 2: under roughly forty lines. Branch conditions and section names belong
  in the rule; the instructions behind them do not.
- Type 3: justified by its consumers. A policy `@`-included by five commands is
  paid five times, so every line must earn a place.

These are budgets, not hard limits. Exceeding one is a signal that content has
drifted out of its owner, so state the reason or move the content.

## Ownership boundaries

| Layer | Owns |
|---|---|
| `AGENTS.md` | Repository-wide constraints that must also apply outside Cursor, source precedence, and author-only writes |
| `docs/standards/` and `docs/data/` | Detailed domain rules and canonical facts |
| `.cursor/commands/` | User-invoked workflows, with targets, guards, steps, and verification |
| `.cursor/rules/` | Attachment, context routing, and explicitly delegated scoped policy |

Every line in a rule must help answer one question: when this context applies,
which canonical instructions should the agent use? A rule that begins answering
the instruction itself has become a second source of truth.

When a rule and a canonical owner overlap, keep the rule's pointer and delete
the local copy, following [[Ownership and duplication]] in
`docs/standards/standards-authoring.md`.

## Rule acceptance criteria

Confirm all eight before accepting a rule.

1. **Type** — the rule matches exactly one type, and the match is evident from
   its frontmatter and body shape.
2. **Frontmatter** — `description` present; `globs` a quoted list for Types 1
   and 2 and absent for Type 3; `alwaysApply: false` present and explicit; no
   other field.
3. **Attachment** — the patterns match the intended artifact class and nothing
   wider. For Type 3, every consumer that needs the policy loads it explicitly.
4. **Stop behavior** — the rule defines no guard, bar, or acceptance gate of its
   own, and any stop it mentions names the owner that defines it.
5. **Size** — within the budget for its type, or the excess is explained.
6. **Reference conformity** — no `@path`; forms follow [[References]]; every
   path and section reference resolves under
   `scripts/check_doc_references.py`.
7. **Ownership** — the [[Author-only writes]] pointer appears exactly when the
   governed artifact class can trigger an author-only write, and no other
   ownership statement is restated locally.
8. **No duplicated canonical rules** — no sentence restates a rule owned by
   `AGENTS.md`, a command, or a standard. Each is a pointer to its owner.

## Does not cover

- Which rules this repository has and how they interact at runtime — see
  `cursor_ecosystem/02-How-This-Repository-Uses-Rules-and-Standards.md`, which
  is descriptive and owns no rules.
- Slash-command structure — see `docs/standards/command-authoring.md`.
- Standards structure and reference-form conventions — see
  `docs/standards/standards-authoring.md`.
- Repository-wide constraints and automatic-write restrictions — see
  `AGENTS.md`.
- Command read manifests and notebook acceptance bars — see
  `docs/standards/notebook-authoring-checklist.md`.
