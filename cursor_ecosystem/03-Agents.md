# AI Coding Agents: `AGENTS.md`, Rules, Commands, and Project Context

## 1. What is an AI coding agent?

An AI coding agent is more than the language model that generates an answer.

A useful mental model is:

```
AI Agent
   =
Model
+ Instructions
+ Context
+ Tools
+ Workflow
```

For example, when using Cursor or Codex, the agent may be able to:

- read repository files,
- search the codebase,
- edit files,
- run terminal commands,
- inspect Git changes,
- and follow project-specific instructions.

The **model** provides the reasoning capability.

The **agent system** decides what context the model receives, what tools it can use, and what project instructions apply.

That distinction is important:

> **GPT, Claude, or another model is the brain. Cursor or Codex is the working environment around that brain.**

---

## 2. Why does an agent need project instructions?

Imagine opening this repository and asking:

> Create a new lesson about data ingestion.

A capable model knows PySpark, but it does not automatically know the decisions made specifically for this course.

For example, this project requires:

```
Azure Databricks
DBR 17.3 LTS
Spark 4.0
PySpark
Databricks source .py notebooks
batch processing only
shared rideshare dataset
specific Unity Catalog objects
specific teaching standards
```

Without project instructions, an agent could reasonably create:

- an `.ipynb` notebook,
- a Structured Streaming example,
- an invented dataset,
- different catalog names,
- or a lesson that does not match the course roadmap.

Those answers could be technically valid PySpark, but **wrong for this repository**.

This is the problem that project guidance solves.

---

# 3. Why `AGENTS.md` was created

`AGENTS.md` is a predictable place where a repository can tell coding agents:

> **“Before you work here, these are the important things you need to know.”**

The open `AGENTS.md` specification describes it as essentially a **README for coding agents**. It is plain Markdown and can contain project overview, development commands, testing instructions, conventions, security guidance, and other repository-specific expectations.

This separates two audiences:

```
README.md
    ↓
Humans:
What is this project?
How do I use it?

AGENTS.md
    ↓
AI coding agents:
How should you behave while working in this project?
What must you respect?
Where should you look for detailed rules?
```

That is the main reason `AGENTS.md` exists.

---

# 4. What `AGENTS.md` does in this workspace

Your root `AGENTS.md` is correctly acting as a **global contract and router**.

It tells an agent important facts such as:

```
This is a batch-only PySpark course.

Use Databricks source .py notebooks.
Never create .ipynb notebooks.

Do not introduce:
- Structured Streaming
- Auto Loader
- streaming tables
- ML content
```

It also tells the agent where the detailed information lives:

```
COURSE_MODULES.md
    → course roadmap

docs/data/dataset-overview.md
    → data model and physical layout

module README.md
    → module-specific lesson design

docs/standards/*
    → authoring and engineering standards
```

This is good architecture because `AGENTS.md` does **not** try to contain every detailed rule.

A good way to describe its responsibility is:

> **`AGENTS.md` protects the repository and routes the agent to the right source of truth.**

OpenAI similarly recommends keeping `AGENTS.md` small and using it for durable project guidance and routing information.

---

# 5. Why not put everything inside `AGENTS.md`?

Suppose you copied all of these files into `AGENTS.md`:

```
coding-standards.md
teaching-guidelines.md
notebook-writing.md
naming-conventions.md
dataset-overview.md
permissions-and-governance.md
```

The file would become very large.

More importantly, the same rule could then exist in several places:

```
AGENTS.md
learner-notebooks.mdc
teaching-guidelines.md
```

Eventually one copy changes while another does not.

Now the agent has conflicting instructions.

Your workspace instead follows a better principle:

> **Navigate, don't duplicate.**

For example, **ownership** (where the detailed rule lives) looks like this:

```
AGENTS.md
     │
     │ points to
     ▼
docs/standards/notebook-authoring-checklist.md
     │
     ├── notebook-writing.md
     ├── teaching-guidelines.md
     ├── coding-standards.md
     ├── naming-conventions.md
     └── dataset-overview.md
```

`.mdc` files are **not** in that fan-out. They do not own teaching-guidelines or column names. Putting them there would imply a third copy of the standards.

They are a **Cursor-only router** to the same checklist. In Cursor, two paths can reach one source of truth:

```
AGENTS.md                          learner-notebooks.mdc
(always-on, all tools)             (glob: numbered *.py, Cursor only)
     │                                         │
     └────────────────┬────────────────────────┘
                      ▼
     docs/standards/notebook-authoring-checklist.md
                      │
                      ▼
              the standards files above
```

So:

- **Required for the detailed rules?** No. The checklist and `docs/standards/` are enough.
- **Required for Cursor to load those rules at the right moment?** Yes — that is section 6. Codex never sees the `.mdc` file; it has to follow `AGENTS.md` and open the checklist itself.

The detailed rule still has one canonical owner.

---

# 6. What are `.cursor/rules/*.mdc` files?

`AGENTS.md` gives broad project guidance.

Cursor rules solve a different problem:

> **“This instruction matters only when I am doing this kind of work.”**

Cursor project rules live under:

```
.cursor/rules/
```

and can be automatically attached based on file patterns, always applied, selected by the agent based on relevance, or manually included.

Your workspace has three:

```
.cursor/rules/
├── learner-notebooks.mdc
├── course-authoring.mdc
└── notebook-command-output.mdc
```

They have different jobs.

---

## 7. `learner-notebooks.mdc`

Your rule contains:

```yaml
globs: ["[0-9][0-9] - */*.py"]
alwaysApply: false
```

A **glob** is simply a file-path pattern.

It roughly means:

> When Cursor is working with `.py` files inside numbered course-module folders, this rule is relevant.

For example:

```
08 - Aggregations and Window Functions/
06 - Running Totals and Lag and Lead.py
```

matches the pattern.

Therefore Cursor can attach `learner-notebooks.mdc`.

That rule then says:

```
Read the notebook-authoring checklist.

Read the module README.

Read:
- notebook-writing.md
- teaching-guidelines.md
- coding-standards.md
- naming-conventions.md
- dataset-overview.md
```

Notice what the rule is doing.

It does **not** duplicate those documents.

It tells Cursor:

> “Because you are editing a learner notebook, these documents now matter.”

That is exactly what scoped rules are good for.

---

# 8. `course-authoring.mdc`

This rule targets files such as:

```
README.md
COURSE_MODULES.md
NN - Module Name/README.md
```

Its responsibility is different.

When editing a module README, the agent needs rules about:

- learning objectives,
- course-roadmap ownership,
- module navigation,
- pedagogy,
- naming,
- permissions.

It does not necessarily need all the detailed notebook-editing instructions.

So Cursor can load different guidance depending on the type of file being changed.

That keeps the context focused.

---

# 9. `notebook-command-output.mdc`

This rule has a different purpose again.

It defines how responses from commands such as:

```
/new-lesson
/write-lesson
/validate-notebook
/review-module
```

should look.

For example:

```
/validate-notebook
```

should return **issues only**, rather than a large table containing dozens of passing checks.

This rule does not need to affect normal notebook editing.

Therefore your commands explicitly reference it.

This demonstrates an important idea:

> **Not every rule needs to be active all the time.**

---

# 10. What are `.cursor/commands/*`?

Rules describe **how the agent should behave**.

Commands describe **a repeatable task you want the agent to perform**.

Cursor supports project commands as Markdown files under `.cursor/commands`; they provide reusable workflows invoked with `/`.

Your workspace contains:

```
/new-lesson
/write-lesson
/validate-notebook
/review-module
```

Each command has a clear responsibility.

```
/new-lesson
    ↓
Create notebook skeleton

/write-lesson
    ↓
Write complete runnable lesson

/validate-notebook
    ↓
Review one notebook

/review-module
    ↓
Review the complete module
```

This is different from a rule.

For example:

```
Rule:
"Use beginner-friendly explanations."

Command:
"Review this notebook against all authoring standards."
```

A **rule constrains behavior**.

A **command starts a workflow**.

---

# 11. Standards and data documents are another layer

Files such as:

```
docs/standards/teaching-guidelines.md
docs/standards/coding-standards.md
docs/standards/notebook-writing.md
docs/data/dataset-overview.md
```

are not simply “more agent rules.”

They are the **authoritative project documentation**.

For example:

`dataset-overview.md` owns:

```
table schemas
column names
join keys
NULL rules
Unity Catalog locations
module data flow
```

So if an agent needs to know whether:

```python
pickup_borough
```

or:

```python
borough_name
```

exists in a particular dataset, it should consult the data contract instead of guessing.

Similarly:

```
teaching-guidelines.md
```

owns the pedagogical standards.

That separation gives the repository a clean hierarchy:

```
Instruction
    ↓
Find the authoritative document
    ↓
Use its facts
```

---

# 12. Module README files have another responsibility

Consider:

```
08 - Aggregations and Window Functions/README.md
```

It defines what Module 8 actually teaches.

For example, it says Notebook 06 covers:

```
Default RANGE vs explicit ROWS
ordered first_value / last_value
daily running totals
lag / lead
```

That is not a global authoring rule.

It is the **lesson contract for Module 8**.

Therefore the workflow becomes:

```
Global project rules
        ↓
Notebook-specific rules
        ↓
Module README
        ↓
Exact topics for this lesson
```

This prevents the agent from inventing additional sections just because they are related to Spark windows.

---

# 13. Practical example: editing a Module 8 notebook

Suppose you ask Cursor:

> Improve `06 - Running Totals and Lag and Lead.py`.

The intended flow is:

```
1. AGENTS.md
   ↓
Understands:
- batch-only
- PySpark
- .py Databricks notebook
- project sources of truth

2. learner-notebooks.mdc
   ↓
The path matches the notebook glob.

3. notebook-authoring-checklist.md
   ↓
Tells Cursor what must be read.

4. Module 8 README.md
   ↓
Defines exactly what Notebook 06 must teach.

5. teaching-guidelines.md
   ↓
Defines how to explain it.

6. coding-standards.md
   ↓
Defines how the code should look.

7. dataset-overview.md
   ↓
Defines which columns/tables actually exist.

8. Agent edits the notebook.
```

This is a good example of the complete ecosystem working together.

---

# 14. Why global rules still matter

Now consider another request:

> Add Structured Streaming to Module 2.

Perhaps you currently have only this file open:

```
take_notes/lernings.md
```

A learner-notebook-specific Cursor rule might not be relevant yet because no numbered notebook is involved in the current context.

But the root `AGENTS.md` already says:

```
Batch data engineering only.
No Structured Streaming.
No Auto Loader.
```

That restriction should apply regardless of which file happens to be open.

This illustrates the correct design principle:

> **If a rule must protect the repository everywhere, keep it in `AGENTS.md`.**

---

# 15. Cursor and Codex are not identical

This distinction is especially important in your repository.

Cursor understands:

```
.cursor/rules/*.mdc
.cursor/commands/*.md
```

as Cursor-specific mechanisms. Cursor rules can be scoped and automatically attached when matching files are referenced.

Codex has its own project-guidance mechanism centered around `AGENTS.md`.

Codex reads `AGENTS.md` before doing work and can combine global, root, and nested project guidance according to directory scope.

Therefore:

```
AGENTS.md
    → shared repository guidance

.cursor/rules/*.mdc
    → Cursor-specific contextual guidance

.cursor/commands/*
    → Cursor-specific workflows
```

Do **not** assume Codex automatically interprets Cursor `.mdc` rules.

That is why your root `AGENTS.md` matters even though Cursor rules already exist.

---

# 16. The complete architecture of this workspace

The cleanest mental model for your repository is:

```
                     USER REQUEST
                          │
                          ▼
                    AI CODING AGENT
                          │
                          ▼
┌────────────────────────────────────────┐
│ AGENTS.md                              │
│                                        │
│ Global project contract                │
│ Hard guardrails                        │
│ Navigation to sources of truth         │
└──────────────────┬─────────────────────┘
                   │
           Cursor  │
                   ▼
┌────────────────────────────────────────┐
│ .cursor/rules/*.mdc                    │
│                                        │
│ Context-specific instructions          │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│ Project sources of truth               │
│                                        │
│ COURSE_MODULES.md                      │
│ Module README.md                       │
│ docs/standards/*                       │
│ docs/data/dataset-overview.md          │
└────────────────────────────────────────┘

Separate workflow layer:

.cursor/commands/*
        ↓
new → write → validate → review

Separate evidence layer:

docs/validation/*
        ↓
Actual Azure Databricks runtime evidence
```

---

# 17. One correction I would make in the current `AGENTS.md`

The current file says:

> “Scoped `.cursor/rules/*.mdc` files load these automatically for matching files.”

The idea is correct for Cursor, but the sentence appears inside a file described as **tool-agnostic**.

I would make the tool boundary explicit:

> **In Cursor**, scoped `.cursor/rules/*.mdc` files attach the relevant standards for matching work. Other agents such as Codex should use the navigation in this `AGENTS.md` to locate the same canonical standards.

That removes any suggestion that Codex automatically understands Cursor's `.mdc` mechanism.

---

# Final mental model

You do not need to think of all these files as competing instruction files.

Each layer has a different responsibility:

| Layer | Responsibility |
| --- | --- |
| `AGENTS.md` | **Protect and navigate** |
| `.cursor/rules/*.mdc` | **Apply contextual Cursor guidance** |
| `.cursor/commands/*` | **Run repeatable Cursor workflows** |
| `docs/standards/*` | **Define detailed reusable standards** |
| `docs/data/dataset-overview.md` | **Define the data contract** |
| Module `README.md` | **Define what that module/notebook teaches** |
| `COURSE_MODULES.md` | **Define the overall roadmap and status** |
| `docs/validation/*` | **Store author-confirmed runtime evidence** |

The most important design principle is:

> **Keep global guardrails small, keep detailed knowledge in one authoritative place, and load or read that knowledge only when the task needs it.**

That is the role `AGENTS.md` and its surrounding ecosystem play in this workspace.
