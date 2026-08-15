# How Cursor Loads Rules and Standards in This Repository

Cursor does not load every project instruction for every task.

Instead, this repository uses different layers:

```text
AGENTS.md
    = global project guidance

.cursor/rules/*.mdc
    = task/file-specific Cursor guidance

docs/standards/*
    = detailed source of truth

.cursor/commands/*
    = repeatable workflows
```

The key question is:

> **What instructions does the agent need for this task, and how do those instructions reach it?**

---

## 1. `AGENTS.md` — global guidance

`AGENTS.md` contains the important repository-wide instructions.

In this project, it establishes things such as:

* this is a batch-focused PySpark course,
* learner notebooks use Databricks source `.py` files,
* do not create `.ipynb` notebooks,
* use the existing project documentation as the source of truth,
* use `docs/data/dataset-overview.md` for datasets, schemas, and physical locations,
* do not invent validation evidence or create validation artifacts unless the task explicitly requires it.

Think of it as:

```text
AGENTS.md
    ↓
Rules that should not depend on
which course file is being edited
```

It also points the agent to more detailed documentation.

So its role is:

> **Protect the repository and tell the agent where to look next.**

---

# 2. Cursor rules — guidance for specific work

Cursor-specific rules live here:

```text
.cursor/rules/
```

This repository currently has:

```text
learner-notebooks.mdc
course-authoring.mdc
notebook-command-output.mdc
```

These rules do not all need to load for every task.

Cursor can attach a rule based on:

* a matching file path,
* an explicit `@` reference,
* or, for some rules, the rule description.

---

# 3. File-pattern rules

Two rules in this repository are mainly path-based:

```text
learner-notebooks.mdc
course-authoring.mdc
```

The flow is:

```text
File is part of the Agent request
        ↓
Cursor checks its path
        ↓
Path matches a glob
        ↓
Matching .mdc rule attaches
```

The important point is:

> A file simply being open in an editor tab is not enough as a mental model.
> The file must be part of the Agent request/context.

---

# 4. Learner notebook example

Suppose the Agent is working with:

```text
08 - Aggregations and Window Functions/
06 - Running Totals and Lag and Lead.py
```

`learner-notebooks.mdc` uses a pattern such as:

```yaml
globs:
  - "[0-9][0-9] - */*.py"
```

The notebook path matches.

So Cursor attaches:

```text
learner-notebooks.mdc
```

The flow becomes:

```text
Learner notebook .py
        ↓
Path matches notebook glob
        ↓
learner-notebooks.mdc
```

---

# 5. What the notebook rule brings in

`learner-notebooks.mdc` directly `@`-references several files:

```text
@docs/standards/notebook-authoring-checklist.md
@docs/standards/notebook-writing.md
@docs/standards/teaching-guidelines.md
@docs/standards/coding-standards.md
@docs/standards/naming-conventions.md
@docs/data/dataset-overview.md
```

So the rule can bring those documents into the Agent context.

Conceptually:

```text
Notebook .py
    ↓
learner-notebooks.mdc
    ↓
@ notebook-authoring-checklist.md
@ notebook-writing.md
@ teaching-guidelines.md
@ coding-standards.md
@ naming-conventions.md
@ dataset-overview.md
```

These files answer different questions:

| File                              | What it tells the agent                              |
| --------------------------------- | ---------------------------------------------------- |
| `notebook-authoring-checklist.md` | What must be checked before notebook work            |
| `notebook-writing.md`             | How notebook content should be structured            |
| `teaching-guidelines.md`          | How concepts should be explained                     |
| `coding-standards.md`             | How code should be written                           |
| `naming-conventions.md`           | What naming patterns to follow                       |
| `dataset-overview.md`             | What datasets, schemas, columns, and locations exist |

---

# 6. The module README is different

The notebook rule also tells the agent to use the README from the same module.

For example:

```text
08 - Aggregations and Window Functions/README.md
```

But the module README is **not directly `@`-included** by `learner-notebooks.mdc`.

Instead:

```text
learner-notebooks.mdc
        ↓
"Tells the agent to use the module README"
        ↓
Agent should locate and read it
```

This distinction is useful:

```text
@file
    = directly referenced for context

"Read/use this file"
    = agent should locate and open it
```

The module README answers:

> **What should this notebook teach?**

The standards answer:

> **How should the notebook teach it?**

---

# 7. README and course-roadmap work

Now suppose the Agent is working with:

```text
README.md
```

or:

```text
COURSE_MODULES.md
```

or:

```text
08 - Aggregations and Window Functions/README.md
```

These match `course-authoring.mdc`.

The mappings are:

| File                | Matching glob              |
| ------------------- | -------------------------- |
| Root `README.md`    | `README.md`                |
| `COURSE_MODULES.md` | `COURSE_MODULES.md`        |
| Module README       | `[0-9][0-9] - */README.md` |

So Cursor attaches:

```text
course-authoring.mdc
```

---

# 8. What `course-authoring.mdc` brings in

This rule directly references:

```text
@docs/standards/teaching-guidelines.md
@docs/standards/naming-conventions.md
@docs/standards/permissions-and-governance.md
```

So the flow is:

```text
README / COURSE_MODULES.md
        ↓
course-authoring.mdc
        ↓
@ teaching-guidelines.md
@ naming-conventions.md
@ permissions-and-governance.md
```

Notice what is **not** automatically pulled by this rule:

```text
notebook-authoring-checklist.md
notebook-writing.md
coding-standards.md
dataset-overview.md
```

Those mainly belong to learner-notebook work.

---

# 9. Why notebook and README rules are separate

A notebook usually needs guidance about:

```text
code
Markdown cells
teaching flow
dataset usage
notebook structure
```

A README usually needs guidance about:

```text
module scope
learning objectives
course structure
navigation
naming
governance
```

So the normal pattern is:

```text
Notebook .py
    ↓
learner-notebooks.mdc
```

and:

```text
README / COURSE_MODULES.md
    ↓
course-authoring.mdc
```

This keeps the context focused.

---

# 10. Can both rules attach?

Yes.

Rules are not mutually exclusive.

If the same Agent request contains both:

```text
06 - Running Totals and Lag and Lead.py
```

and:

```text
08 - Aggregations and Window Functions/README.md
```

then both paths can match:

```text
Notebook .py
    ↓
learner-notebooks.mdc

Module README
    ↓
course-authoring.mdc
```

So both rules may be available in the same Agent conversation.

---

# 11. What if the file matches no glob?

Suppose the Agent is working with:

```text
take_notes/ideas.md
```

or:

```text
docs/standards/teaching-guidelines.md
```

These paths do not match the notebook or course-authoring globs.

So:

```text
No matching file glob
        ↓
No notebook/course-authoring .mdc
attaches because of that path
```

`AGENTS.md` still provides the repository-wide guidance.

---

# 12. `notebook-command-output.mdc` works differently

`notebook-command-output.mdc` has:

* `alwaysApply: false`,
* a description,
* no file glob.

So it is not primarily attached by notebook or README paths.

Its main purpose is to control the response format used by these commands:

```text
/new-lesson
/write-lesson
/validate-notebook
/review-module
```

All four commands explicitly reference:

```text
@.cursor/rules/notebook-command-output.mdc
```

So the reliable path is:

```text
Slash command
      ↓
Command file
      ↓
@notebook-command-output.mdc
```

Because the rule has a description, Cursor may also select it when it considers the description relevant.

But the commands explicitly loading it is the predictable path.

---

# 13. Rules and commands are different

This is one of the most important distinctions.

## Rule

A rule answers:

> **How should the agent behave?**

Example:

```text
learner-notebooks.mdc
    ↓
Follow notebook-writing,
teaching, coding, and dataset standards
```

## Command

A command answers:

> **What workflow should the agent perform?**

Example:

```text
/write-lesson
    ↓
Run the full lesson-writing workflow
```

So:

```text
Rule
    = guidance

Command
    = workflow
```

---

# 14. Glob loading does not run `/write-lesson`

Suppose a learner notebook is in the Agent context.

The notebook path matches, so:

```text
learner-notebooks.mdc
```

attaches.

That means Cursor has the relevant notebook guidance.

It does **not** mean:

```text
/write-lesson
```

has been executed.

These are different:

```text
Notebook matches glob
        ↓
Load notebook guidance
```

versus:

```text
/write-lesson
        ↓
Run the complete lesson-writing workflow
```

Your repository uses `/write-lesson` for full lesson creation.

That workflow can include additional steps such as:

* checking that a valid skeleton exists,
* reading a sibling notebook for tone and style,
* applying the full-lesson requirements,
* covering the required README topics.

So remember:

> **Rule loaded ≠ workflow executed.**

---

# 15. `/new-lesson` vs `/write-lesson`

These commands also have different responsibilities:

```text
/new-lesson
    = create the lesson skeleton

/write-lesson
    = turn the skeleton into the full lesson
```

This keeps lesson creation controlled instead of trying to do everything in one generic Agent request.

---

# 16. Commands can load standards directly

A command does not have to wait for a notebook glob to attach first.

For example:

```text
/write-lesson
```

or:

```text
/validate-notebook
```

can directly `@`-reference the checklist and other files required by that workflow.

So there are two possible paths:

```text
Notebook in Agent context
        ↓
glob
        ↓
learner-notebooks.mdc
        ↓
standards
```

or:

```text
Slash command
        ↓
command file
        ↓
@ required standards directly
```

This is why commands remain useful even though glob-based rules already exist.

`/validate-notebook` and `/review-module` can also require additional documents when relevant — for example `compute-validation-policy.md` and extra permissions checks. A glob-based notebook edit does not automatically pull those.

---

# 17. Simple picture

```text
                        USER REQUEST
                             │
                             ▼
                         AGENTS.md
                             │
                    Global project guidance
                             │
             ┌───────────────┴───────────────┐
             │                               │
             ▼                               ▼
      Learner notebook                 README / roadmap
             │                               │
       path matches                      path matches
             │                               │
             ▼                               ▼
 learner-notebooks.mdc             course-authoring.mdc
             │                               │
             ▼                               ▼
    @ notebook standards             @ authoring standards
             │
             ▼
      module README
   agent reads when needed
```

A separate workflow path exists:

```text
/new-lesson
/write-lesson
/validate-notebook
/review-module
        │
        ▼
Command workflow
        │
        ├── @ required standards
        └── @ notebook-command-output.mdc
```

---

# 18. Cursor vs Codex

The `.cursor/rules/*.mdc` globs and `.cursor/commands/*` workflows are **Cursor-specific**.

Codex does not automatically use these Cursor mechanisms.

For Codex, the shared starting point is:

```text
AGENTS.md
```

and any additional files that `AGENTS.md` or the task instructs Codex to read.

---

# Final Mental Model

The repository has four main instruction paths:

```text
AGENTS.md
    = global repository guidance

Glob-scoped .mdc
    = file-specific Cursor guidance

@file
    = directly reference a file for context

Slash command
    = run a controlled workflow
```

For this repository:

```text
Must always be respected
        ↓
AGENTS.md

Learner notebook in Agent context
        ↓
learner-notebooks.mdc

README / COURSE_MODULES in Agent context
        ↓
course-authoring.mdc

Need a controlled lesson/review workflow
        ↓
/new-lesson
/write-lesson
/validate-notebook
/review-module
```

The two most important ideas are:

> **Rules decide what guidance the agent receives.**

> **Commands decide what workflow the agent performs.**

And therefore:

> **Loading a rule is not the same as running a command.**
