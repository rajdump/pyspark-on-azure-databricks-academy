# How Cursor Rules Decide When to Apply

Cursor project rules live in:

```text
.cursor/rules/*.mdc
```

A repository can have many rules, but Cursor does not need every rule for every Agent request.

The key question is:

> **When should this rule be available to the agent?**

Cursor decides mainly from the rule's frontmatter.

---

## 1. The four Cursor project-rule modes

Three frontmatter fields control how a project rule applies:

```yaml
alwaysApply:
description:
globs:
```

Their combination determines the rule mode.

| Cursor mode                 | `alwaysApply` | `description` | `globs` | When it applies                             |
| --------------------------- | ------------: | ------------- | ------- | ------------------------------------------- |
| **Always Apply**            |        `true` | ignored       | ignored | Every Cursor Agent request                  |
| **Apply to Specific Files** |       `false` | optional      | set     | A matching file is in Agent context         |
| **Apply Intelligently**     |       `false` | set           | omitted | Cursor decides whether the description fits |
| **Apply Manually**          |       `false` | omitted       | omitted | Only when explicitly `@`-referenced         |

These four modes apply to **project `.mdc` rules**.

`AGENTS.md` is separate.

---

## 2. Apply to Specific Files

This is the main mode used in this repository.

Use it when a rule clearly belongs to a certain kind of file.

For example, `learner-notebooks.mdc` uses a pattern like:

```yaml
---
description: Rules for learner notebooks
globs:
  - "[0-9][0-9] - */*.py"
alwaysApply: false
---
```

Because `globs` is present, this is:

> **Apply to Specific Files**

The `description` does not turn it into an Apply Intelligently rule.

The glob controls when it attaches.

---

## Example

Suppose this notebook is part of the Agent request:

```text
08 - Aggregations and Window Functions/
06 - Running Totals and Lag and Lead.py
```

It matches:

```text
[0-9][0-9] - */*.py
```

So Cursor attaches:

```text
learner-notebooks.mdc
```

The flow is:

```text
Learner notebook is in Agent context
        ↓
Path matches the glob
        ↓
learner-notebooks.mdc attaches
```

The glob is specific.

It does not mean:

```text
any .py file anywhere in the repository
```

It means:

> a `.py` file one level inside a numbered module folder.

---

## 3. Agent context matters

A matching file must be part of the **Agent request/context**.

Simply having a file open in an editor tab is not the right mental model.

Think of it as:

```text
Matching file enters Agent context
        ↓
Cursor checks its path
        ↓
Matching rule attaches
```

For example, if you only ask:

> Write the aggregations lesson.

but no numbered learner notebook is included in the Agent context, the notebook glob may not fire.

This is one reason slash commands can explicitly load the files they need.

---

## 4. `course-authoring.mdc` uses the same mode

`course-authoring.mdc` is also an **Apply to Specific Files** rule.

It targets:

```text
README.md
COURSE_MODULES.md
[0-9][0-9] - */README.md
```

So:

```text
Root README.md
    ↓
course-authoring.mdc
```

```text
COURSE_MODULES.md
    ↓
course-authoring.mdc
```

```text
08 - Aggregations and Window Functions/README.md
    ↓
course-authoring.mdc
```

One useful detail:

```text
README.md
```

targets the root README.

A module README needs the separate pattern:

```text
[0-9][0-9] - */README.md
```

So a file such as:

```text
vault/README.md
```

does not match either of those module/root patterns.

---

## 5. More than one file rule can attach

Rules are not mutually exclusive.

If the same Agent request contains both:

```text
06 - Running Totals and Lag and Lead.py
```

and:

```text
08 - Aggregations and Window Functions/README.md
```

then both paths match.

Cursor may therefore attach:

```text
learner-notebooks.mdc
+
course-authoring.mdc
```

The rules are selected from the files present in the Agent context.

---

## 6. Always Apply

An always-on rule looks like:

```yaml
---
alwaysApply: true
---
```

This means:

> Attach this project rule to every Cursor Agent request.

When `alwaysApply: true`, `description` and `globs` no longer control when the rule applies.

You could create an always-on rule for things such as:

```text
Use .py notebooks.
Do not introduce streaming.
```

But this repository already has:

```text
AGENTS.md
```

for repository-wide guidance.

Duplicating the same rule would give Cursor two copies:

```text
AGENTS.md
    ↓
global instruction

alwaysApply .mdc
    ↓
same global instruction again
```

For this repository:

> **Use `AGENTS.md` for global rules instead of creating a second always-on `.mdc`.**

Use `alwaysApply: true` only when you have a truly Cursor-specific instruction that must appear in every Cursor Agent request.

This repo currently does not need one.

---

## 7. Apply Intelligently

A rule can have a description but no glob:

```yaml
---
description: Guidance for Lakeflow Jobs development
alwaysApply: false
---
```

This is:

> **Apply Intelligently**

Cursor uses the description to decide whether the rule is relevant.

This is useful when the trigger is a **topic**, not a predictable file path.

Examples might include:

```text
Lakeflow Jobs
SQL performance
deployment guidance
```

These topics could appear across many different files.

---

## Do not use it for critical rules

Apply Intelligently depends on Cursor deciding that the description is relevant.

So avoid putting hard repository restrictions only here.

For example:

```text
Do not scaffold modules marked Not Started.
```

should not depend on model judgment.

That kind of instruction belongs in:

```text
AGENTS.md
```

A simple rule is:

> **Use Apply Intelligently when missing the rule would be inconvenient, not harmful.**

---

## 8. `notebook-command-output.mdc` is Apply Intelligently

This repository's third rule has a different setup.

Its frontmatter is similar to:

```yaml
---
description: Minimal response format for /new-lesson,
             /write-lesson,
             /validate-notebook,
             /review-module
alwaysApply: false
---
```

It has:

```text
description = yes
globs       = no
alwaysApply = false
```

Therefore its mode is:

> **Apply Intelligently**

It is not a pure Manual rule.

Cursor may attach it if the description looks relevant.

But the four commands also explicitly `@`-reference it:

```text
/new-lesson ───────┐
/write-lesson ─────┤
/validate-notebook ├──→ @notebook-command-output.mdc
/review-module ────┘
```

So it has two possible loading paths:

```text
Description looks relevant
        ↓
Cursor may attach it
```

and:

```text
Slash command
        ↓
Explicit @ reference
        ↓
Rule is predictably included
```

For these workflows, the command `@` is the reliable path.

---

## 9. What does Apply Manually mean?

A pure Manual rule has:

```yaml
---
alwaysApply: false
---
```

with:

```text
no globs
no description
```

Cursor has no automatic reason to attach it.

It must be explicitly referenced.

For example:

```text
@my-special-rule
```

The flow is:

```text
No glob
No description
alwaysApply: false
        ↓
No automatic attachment
        ↓
Explicit @ required
```

This repository currently does not use a Manual rule.

---

## 10. `@` is not a rule mode

This distinction is important.

`@` means:

> **Explicitly include this rule or file in the current context/workflow.**

For example, a command can reference:

```text
@notebook-authoring-checklist.md
@notebook-writing.md
@coding-standards.md
@notebook-command-output.mdc
```

Those files do not have to be Manual rules.

So:

```text
@ ≠ Manual mode
```

Instead:

```text
Rule mode
    = controls automatic attachment

@
    = explicit inclusion
```

---

## 11. Slash commands are a separate decision

Suppose a slash command always needs a particular rule or standards file.

Do not rely only on automatic rule selection.

Explicitly reference it from the command.

For example:

```text
/validate-notebook
        ↓
@notebook-command-output.mdc
```

This is independent of the rule mode.

In this repository:

```text
notebook-command-output.mdc
        ↓
Apply Intelligently
```

and also:

```text
command
    ↓
@notebook-command-output.mdc
```

So:

> **The rule mode controls automatic attachment.
> The command `@` gives the workflow a predictable explicit dependency.**

---

## 12. Rule loaded does not mean command executed

A notebook path may cause:

```text
learner-notebooks.mdc
```

to attach.

That does not mean:

```text
/write-lesson
```

has run.

These are different mechanisms:

```text
Glob matches
    ↓
Load guidance
```

versus:

```text
Slash command
    ↓
Run a workflow
```

So remember:

> **Rule loaded ≠ command executed.**

For the detailed loading chain, see:

```text
05-How Cursor Loads Rules and Standards in This Repository.md
```

---

## 13. How to choose the right mode

Start with:

> **When must the agent receive this instruction?**

### Must apply everywhere in the repository

Example:

```text
Course is batch-only.
Learner notebooks use .py files.
```

Use:

```text
AGENTS.md
```

For this repo, do not duplicate the same guidance in an `alwaysApply: true` `.mdc`.

---

### Applies to predictable file paths

Example:

```text
When working with learner notebooks,
follow the notebook-authoring standards.
```

Use:

```text
Apply to Specific Files
        ↓
globs
```

This is how:

```text
learner-notebooks.mdc
course-authoring.mdc
```

work.

---

### Applies to a topic with no reliable path

Example:

```text
Use this guidance for Lakeflow Jobs work.
```

Use:

```text
Apply Intelligently
        ↓
description
```

Use this for helpful guidance, not hard stops.

---

### Should never attach automatically

Use:

```text
Apply Manually
```

with:

```text
alwaysApply: false
no globs
no description
```

Then explicitly `@` the rule when needed.

---

### Needed by a slash command

This is a **separate workflow decision**.

Use:

```text
Slash command
        ↓
@ required rule or standards file
```

The referenced rule can still be:

```text
Apply Intelligently
Apply to Specific Files
Apply Manually
```

Its automatic mode is independent of the command's explicit `@`.

---

## 14. How this repository uses the modes

The current setup is:

```text
Must always apply
        ↓
AGENTS.md
```

```text
.py file one level inside
a numbered module folder
        ↓
learner-notebooks.mdc
        ↓
Apply to Specific Files
```

```text
Root README
COURSE_MODULES.md
numbered module README
        ↓
course-authoring.mdc
        ↓
Apply to Specific Files
```

```text
Slash-command response format
        ↓
notebook-command-output.mdc
        ↓
Apply Intelligently
        +
commands explicitly @ it
```

This repository currently has no strong need for:

```text
alwaysApply: true
```

or a pure:

```text
Apply Manually
```

project rule.

---

## Final Mental Model

When creating a Cursor project rule, ask:

```text
When must the agent receive this?
              │
              ├── Everywhere in the repo
              │       ↓
              │   AGENTS.md
              │
              ├── Certain file paths
              │       ↓
              │   globs
              │   Apply to Specific Files
              │
              ├── Topic with no reliable path
              │       ↓
              │   description
              │   Apply Intelligently
              │
              └── Never automatically
                      ↓
                  Apply Manually
                  explicit @ only
```

Then ask a separate workflow question:

```text
Does a slash command always need
this rule or standards file?
        │
       YES
        ↓
Put an explicit @ reference
inside the command
```

For this repository, the practical pattern is:

```text
Global guidance
    → AGENTS.md

File-specific guidance
    → glob-scoped .mdc

Topic-based optional guidance
    → Apply Intelligently

No automatic attachment
    → Apply Manually

Workflow dependencies
    → command @ references
```

The key distinctions are:

> **Rule mode decides when Cursor automatically attaches a project rule.**

> **`@` explicitly includes a rule or file when a request or workflow needs it.**

> **Loading a rule is not the same as running a command.**

One final tool boundary:

> Cursor `.mdc` modes and `.cursor/commands` are Cursor-specific. Codex does not automatically use these mechanisms; `AGENTS.md` is the shared repository-guidance layer.
