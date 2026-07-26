# Teaching Guidelines

Canonical owner of all pedagogical and explanation standards. Referenced by
`.cursor/rules/learner-notebooks.mdc`, `.cursor/rules/course-authoring.mdc`,
`/new-lesson`, `/write-lesson`, `/validate-notebook`, and `/review-module`
— do not duplicate this content elsewhere. Shared read list:
@docs/standards/notebook-authoring-checklist.md.

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
- Call out common mistakes and gotchas explicitly (e.g. NULL-handling
  surprises, lazy-evaluation timing) rather than letting learners discover
  them by accident.
- Use the shared rideshare dataset (`docs/data/dataset-overview.md`) for
  examples by default; only switch datasets when a topic genuinely requires
  it, and explain why.
- Prefer DataFrame API and Spark SQL side by side where both are idiomatic,
  so learners recognize both forms in the wild (Module 10 formalizes this).

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
  @docs/standards/notebook-authoring-checklist.md; full lessons use
  `/write-lesson` and the **Full-lesson bar** there.
