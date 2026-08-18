# Cursor Ecosystem — Future Topics

## Purpose

Author-private backlog of Cursor ecosystem topics intentionally **not** in File 01. They would add noise to the beginner mental model in [01-Agents-and-Cursor-Rules.md](01-Agents-and-Cursor-Rules.md).

> These topics are intentionally deferred. Their omission from File 01 is not a content gap. File 01 teaches the minimum mental model needed to understand agents, `AGENTS.md`, Project Rules, rule attachment modes, and commands.

> Do not add a future topic to File 01 unless its absence makes File 01 technically incorrect or causes the learner to form a materially wrong mental model.

---

## Nested `AGENTS.md`

- [ ] Nested `AGENTS.md`
  - root vs nested `AGENTS.md`
  - instruction scope by directory
  - precedence and inheritance behavior
  - `AGENTS.override.md`
  - when nested instructions are useful

Worth covering later when learners need directory-scoped or monorepo instruction patterns beyond a single root file.

---

## Cursor User Rules

- [ ] Cursor User Rules
  - what User Rules are
  - how they differ from Project Rules
  - when personal or global rules are useful

Worth covering later when authors need to separate repo-wide team guidance from individual Cursor preferences.

---

## Cursor Team Rules

- [ ] Cursor Team Rules
  - organization- or team-level rules
  - relationship with Project Rules and User Rules
  - loading and precedence considerations

Worth covering later for team or enterprise setups where dashboard-managed rules affect every project.

---

## Cursor Skills

- [ ] Cursor Skills
  - what Agent Skills are
  - `.cursor/skills/<skill>/SKILL.md`
  - Skills vs Rules
  - Skills vs Commands
  - when to choose each mechanism

Worth covering later when the course addresses reusable agent workflows beyond Project Rules and slash commands.

---

## Advanced rule attachment

- [ ] Advanced rule attachment
  - how matching files enter the agent's context
  - explicit `@` references
  - files read or edited by the agent
  - multiple matching rules
  - practical glob behavior

Worth covering later after learners understand the four attachment modes and need operational detail on when globs actually fire.

This repository’s operational `@` / glob / backtick model lives in
[02-How-This-Repository-Uses-Rules-and-Standards.md](02-How-This-Repository-Uses-Rules-and-Standards.md).
Do not add a fifth routing architecture file.

---

## Rule reliability and troubleshooting

- [ ] Rule reliability and troubleshooting
  - how to debug a rule that did not attach
  - validating glob patterns
  - common rule-loading problems
  - version-specific behavior when relevant

Worth covering later as a troubleshooting reference, not as part of the first-pass mental model.

### Rule attachment smoke test (operational)

Filesystem check (automated): `python3 scripts/verify_rule_globs.py` — confirms each
`.mdc` glob matches the paths it should on disk. Does **not** prove Cursor Agent
attaches the rule.

IDE check (manual, ~2 minutes):

1. **Customize → Rules** — confirm `command-authoring.mdc` is **Apply to Specific
   Files** with `.cursor/commands/*.md`.
2. New Agent chat → run `/new-lesson` (or edit `.cursor/commands/new-lesson.md`).
3. In the chat context / attached-rules list, look for `command-authoring` or
   *Structure for Cursor slash-command files*.
4. **Negative control:** new chat, edit only `README.md` — rule should not attach.
5. **Positive control:** `@`-reference a numbered learner `.py` — `learner-notebooks`
   should attach.

If the IDE check fails but `verify_rule_globs.py` passes, try `globs` as a plain
string (`globs: .cursor/commands/*.md`) per Cursor docs, then
`globs: **/.cursor/commands/*.md`.

---

## Complete Cursor instruction hierarchy

- [ ] Complete Cursor instruction hierarchy
  - `AGENTS.md`
  - Team Rules
  - Project Rules
  - User Rules
  - Skills
  - Commands
  - how these mechanisms relate without duplicating responsibility

Worth covering later as a capstone map once learners already know the File 01 core; avoids cataloging every Cursor surface in the beginner lesson.
