# Teaching Guidelines

This file is the canonical owner of pedagogy, explanation style, and
exercise-design rules for learner-facing course content.

Direct readers: `docs/standards/notebook-authoring-checklist.md`,
`docs/standards/notebook-writing.md`, `.cursor/rules/course-authoring.mdc`,
and `/write-module-readme`. Notebook commands and
`.cursor/rules/learner-notebooks.mdc` receive these rules through the
checklist.

## Audience assumptions

Write for a learner who:
- Knows basic Python syntax
- Knows basic SQL, not advanced SQL
- Has little or no Apache Spark or Azure Databricks experience
- Has little or no production data engineering experience
- Is unfamiliar with local-authoring / Git / Databricks deployment workflows

**Explain unfamiliar concepts before using them.** If a notebook needs a
term or idea that hasn't been introduced yet, define it briefly in place
rather than assuming prior exposure.

## Explanation style

- Practical and code-focused over theory-heavy. Motivate *why* a concept
  matters with a concrete rideshare scenario before showing *how*.
- Beginner-friendly language — avoid unexplained jargon; when a technical
  term is introduced for the first time, define it in one sentence.
- Progressive complexity: within a notebook, and across the module, start
  simple and layer in complexity once the basics are demonstrated.
- Don't try to teach every PySpark API. Focus on what's needed to build
  reliable batch data engineering solutions — depth over breadth.

## Structure patterns

- Worked example first, exercise second — never ask a learner to attempt a
  pattern that hasn't been demonstrated.
- Give every newly introduced API a runnable example against the shared
  rideshare dataset before using it in an exercise.
- Call out common mistakes and gotchas explicitly (e.g. NULL-handling
  surprises, lazy-evaluation timing) rather than letting learners discover
  them by accident.
- Use the shared rideshare dataset (`docs/data/dataset-overview.md`) for
  examples by default; only switch datasets when a topic genuinely requires
  it, and explain why.

### DataFrame and SQL teaching policy

Teach DataFrame-first by default. Show SQL only when SQL is a planned
learning objective for that cell or section; the fact that both APIs are
idiomatic is not enough to require both.

Use side-by-side DataFrame and SQL examples only when comparing the two APIs
is itself the learning objective, as in
`06 - Querying DataFrames with SQL.py` in `02 - DataFrame Fundamentals`.
**Module 9 — Spark SQL and DataFrame Interoperability** formalizes
systematic dual-API treatment as its core purpose. See
`docs/standards/notebook-writing.md` for the structural code-cell rules that
implement this policy.

### Exercise design conventions

- Put optional hints after the exercise cell, progressing from general to
  specific.
- Put solutions in a clearly marked cell after the exercise; collapse or
  comment them out where the platform supports it.
- State the expected output shape or row count in the prompt for self-checks.
- Optional assertion cells after exercises are encouraged, not required.

## Production framing

Every module should connect its concept back to why it matters in a real
batch data engineering job — this is a job-focused course, not an academic
Spark tour. Where relevant, name the production concern a topic addresses
(reliability, idempotency, governance, performance, etc.) using the
"Production Relevance" language already established for that module in
`COURSE_MODULES.md`.

## Where this applies

- Module `README.md` files (learning objectives, prerequisites, guidance)
- Learner notebooks (markdown cells, comments, exercise framing)
- `/new-lesson`-scaffolded content follows the **Scaffold bar** in
  `docs/standards/notebook-authoring-checklist.md`; full lessons use
  `/write-lesson` and the **Full-lesson bar** there.

## Does not cover

- Code formatting and security — see
  `docs/standards/coding-standards.md`.
- Notebook structure, source format, and cell boundaries — see
  `docs/standards/notebook-writing.md`.
