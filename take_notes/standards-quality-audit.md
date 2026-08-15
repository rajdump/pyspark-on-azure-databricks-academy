# Standards Quality Audit

Read-only audit of six standards against the checklist, root guidance,
dataset contract, Cursor rules, Cursor commands, and representative
early/middle/late notebooks.

Findings are deduplicated by root ID. A root may appear in multiple sections
but is counted once in the final total.

Sampling boundary:

- Early: `02 - DataFrame Fundamentals/03 - Selecting and Transforming Columns.py`
- Middle: `05 - Reading, Writing, and Schemas/02 - Reading CSV.py`
- Late: `08 - Aggregations and Window Functions/01 - GroupBy and Basic Aggregations.py`
- Supporting: Module 2's SQL notebook and Module 5's setup/config notebook

## 1. Duplicated content

**Findings**: 3

### AQ-01 — Notebook-writing restates the functions import convention

**Details**:

- `notebook-writing.md:63–64` says `pyspark.sql.functions` is imported as
  `F`; `coding-standards.md:21–23` already owns and defines the exact import
  form.

**Severity**: LOW

**Recommended fix**: Keep the DataFrame-versus-SQL structural guidance in
`notebook-writing.md`, but point to `coding-standards.md` for import syntax.

### AQ-02 — Python naming is defined in two canonical domains

**Details**:

- `coding-standards.md:16–17` and `naming-conventions.md:61–65` both prescribe
  `snake_case` and `PascalCase`; `naming-conventions.md` also says it owns
  naming.

**Severity**: LOW

**Recommended fix**: Make `naming-conventions.md` the sole normative owner and
leave a pointer in `coding-standards.md`.

### AQ-03 — The security pointer broadens the hardcoded-path prohibition

**Details**:

- `notebook-writing.md:73–74` says no hardcoded paths.
- `coding-standards.md:55–58` bans hardcoded local-machine paths and requires
  environment-varying paths to be parameterized.
- Fixed course-controlled Volume paths are valid elsewhere.

**Severity**: MEDIUM

**Recommended fix**: Make `notebook-writing.md` a pure pointer, or say “no
hardcoded local-machine or learner-specific paths” so course paths remain
permitted.

No issue was found with worked-example ordering or the checklist's
security/exercise bullets; those are concise acceptance criteria rather than
competing canonical definitions.

## 2. Contradictions and inconsistencies

**Findings**: 6

### AQ-04 — DataFrame-default and side-by-side SQL guidance lack precedence

**Details**:

- `notebook-writing.md:63–64` prefers DataFrames unless the notebook teaches
  SQL and parenthetically names Module 9.
- `teaching-guidelines.md:43–44` prefers DataFrame and SQL side by side
  wherever both are idiomatic.
- Module 2 Notebook 06 already uses both.

**Severity**: MEDIUM

**Recommended fix**: State one policy: DataFrame-first by default;
side-by-side only when comparison is a planned learning objective; Module 9
formalizes systematic dual-API treatment.

### AQ-05 — `/write-lesson` claims validation parity but loads fewer standards

**Details**:

- `.cursor/commands/write-lesson.md:5–10` says it loads the same standards as
  `/validate-notebook` but follows Required reads only.
- `.cursor/commands/validate-notebook.md:8–10` also applies conditional
  Additional reads from `notebook-authoring-checklist.md:24–32`.

**Severity**: MEDIUM

**Recommended fix**: Either apply compute and permissions reads during
relevant lesson writing, or replace “same standards” with the exact
Required-reads/Full-lesson scope.

### AQ-06 — A module spot-check is called equivalent to full validation

**Details**:

- `.cursor/commands/review-module.md:22–25` says “spot-check each notebook” is
  equivalent to running `/validate-notebook` on each one.
- `/validate-notebook` checks the complete notebook, compute assumptions,
  security, and README privileges.
- Uninspected defects can therefore pass the module gate and leave incorrect
  notebooks approved.

**Severity**: HIGH

**Recommended fix**: Require a complete per-notebook authoring review, or
retain spot-checking and explicitly state that it is not equivalent to
`/validate-notebook`.

### AQ-07 — Learner rule applies the Full-lesson bar to scaffolding

**Details**:

- `.cursor/rules/learner-notebooks.mdc:10–12` requires Required reads and the
  Full-lesson bar before editing any cell.
- The Scaffold bar and `.cursor/commands/new-lesson.md:33–36` intentionally
  allow TODOs and prohibit full lesson content.

**Severity**: MEDIUM

**Recommended fix**: Branch the rule by task: Scaffold bar for
`/new-lesson`; Full-lesson bar for full lesson writing and validation.

### AQ-08 — Module 5 author-default safety criteria are undefined

**Details**:

- `coding-standards.md:52–60` bans secrets and account-revealing
  catalog/schema names.
- `notebook-writing.md:73–74` broadly bans personal identifiers.
- Both point toward a “Tier 1” config-cell exception, and
  `permissions-and-governance.md:87–90` permits author defaults.
- Neither Tier 1 nor acceptable non-secret defaults are defined.

**Severity**: MEDIUM

**Recommended fix**: State which non-secret sample identifiers may be
committed, retain the ban on real sensitive/account-revealing values, and
define Tier 1 or remove the term.

AQ-03 is also a scope inconsistency but is counted under duplicated content.

## 3. Stale or outdated information

**Findings**: 6

### AQ-09 — Validation template claim and vocabulary have drifted

**Details**:

- `compute-validation-policy.md:5,52–55` refers to a
  `docs/validation/NN - Module Title.md` template and
  selected/excluded/unsupported/not-applicable states.
- No template file exists.
- Existing records use Passed/Partial/Not tested/Not applicable.
- Modules 07–08 use `not tested` as serverless compatibility despite
  `compute-validation-policy.md:35–36` allowing only `complete`, `partial`,
  `unsupported`, or `not applicable`.

**Severity**: MEDIUM

**Recommended fix**: Create a canonical template or define its exact fields
in the policy, including separate environment disposition, test result, and
serverless compatibility vocabularies.

### AQ-10 — Cluster permission example uses the wrong privilege

**Details**:

- `permissions-and-governance.md:18` gives `CAN USE` on a cluster.
- The same file at lines 70–71 and all module READMEs use cluster permissions
  `CAN ATTACH TO` or `CAN RESTART`.
- `CAN USE` applies to resources such as cluster policies.

**Severity**: MEDIUM

**Recommended fix**: Replace the cluster example with `CAN ATTACH TO`;
mention `CAN USE` only for an object that exposes it.

### AQ-11 — Notebook filename example no longer matches Module 1

**Details**:

- `naming-conventions.md:31–41` uses
  `02 - Apache Spark and PySpark.py`.
- The current file and Module 1 README use
  `02 - Apache Spark Architecture and PySpark.py`.

**Severity**: LOW

**Recommended fix**: Update both occurrences in the naming example to the
current filename.

### AQ-12 — Scaffold bar still refers to README navigation bullets

**Details**:

- `notebook-authoring-checklist.md:83–84` says headings align to “README
  navigation bullets.”
- The canonical structure is the `## Notebooks` table, and other consumers
  now use that name.

**Severity**: MEDIUM

**Recommended fix**: Say headings align to topics/subtopics in the target
`Notebooks` table entry.

### AQ-13 — Standards headers blur direct and transitive consumers

**Details**:

- The six “Referenced by” lists name commands/rules that now load standards
  through the checklist.
- They omit some direct cross-standard consumers and therefore no longer
  describe the dependency graph precisely.

**Severity**: LOW

**Recommended fix**: Use “Loaded directly or through the checklist by…” or
list only direct references and let the checklist own the consumer inventory.

### AQ-14 — README does not provide the promised notebook-format rationale

**Details**:

- `notebook-writing.md:11–13` says “see README.md for why” source `.py` is
  fixed.
- `README.md:31–45` lists `.py` in the technical baseline but does not
  explain why it was selected.

**Severity**: LOW

**Recommended fix**: Add a brief rationale to README or change the standard
to “see README.md for the technical baseline.”

Not stale: DBR 17.3 LTS, Spark 4.0.0, Python 3.12, Modules
5/6/9/11/13/16, and the planned absence of `src/`, `tests/`, Modules 10–20
assets, and `python-modules.mdc` all align with the roadmap.

## 4. Broken cross-references

**Findings**: 2

No literal `@path` is broken. The named **Security and portability**,
**Structure patterns**, **Scaffold bar**, and **Full-lesson bar** sections
resolve.

### AQ-09 — Validation-template reference has no target artifact

**Details**:

- The filename pattern resolves to nine instance records.
- No template contains the “exact fields” promised by
  `compute-validation-policy.md:55`.

**Severity**: MEDIUM

**Recommended fix**: Create a template or make the policy itself the explicit
schema owner.

### AQ-14 — README rationale reference resolves only syntactically

**Details**:

- README exists, but the referenced explanation does not.

**Severity**: LOW

**Recommended fix**: Correct the semantic target as described in Section 3.

## 5. Scope gaps

**Findings**: 6

### AQ-15 — Module README structure has no canonical standards owner

**Details**:

- The design-complete definition lives in
  `.cursor/rules/course-authoring.mdc:21–29`.
- No `docs/standards` file owns README structure.
- Non-Cursor agents receive only indirect routing through `AGENTS.md`.

**Severity**: MEDIUM

**Recommended fix**: Create a canonical README-authoring standard and make
the Cursor rule a concise loader, or explicitly declare the rule as owner.

### AQ-16 — Exercise hints, solutions, and self-checks are unowned

**Details**:

- `teaching-guidelines.md:28–29` owns progressive complexity.
- Lines 35–36 plus the checklist own example-before-exercise ordering.
- No standard defines hint policy, solution visibility, expected-output
  guidance, or learner self-check conventions.

**Severity**: LOW

**Recommended fix**: Add a concise Exercise design subsection to
`teaching-guidelines.md` for hints, solutions, expected outcomes, and
self-checks.

### AQ-17 — Display-method selection is not standardized

**Details**:

- `notebook-writing.md:67–68` allows `display()`/`.show()` but gives no rule
  for when to use `display`, `show`, `printSchema`, or `print`.

**Severity**: LOW

**Recommended fix**: Add a short output-display convention to
`notebook-writing.md`, or explicitly leave the choice module-local.

### AQ-18 — Notebook dependency and execution-state policy is missing

**Details**:

- Notebook-writing asks objectives to name prior assumptions and summaries
  to point forward.
- No standard says whether notebooks must run independently, require prior
  notebooks, depend only on persistent tables, or declare run-order state.

**Severity**: MEDIUM

**Recommended fix**: Add a notebook-dependencies section defining allowed
persistent dependencies, forbidden hidden session state, and where
prerequisites must be documented.

### AQ-19 — Notebook error-handling patterns are unowned

**Details**:

- No standard distinguishes intentional expected failures, teaching
  `try`/`except` cells, operational error handling, and errors that should
  fail fast.

**Severity**: LOW

**Recommended fix**: Add a concise expected-error convention to
`notebook-writing.md` or `coding-standards.md`.

### AQ-20 — Markdown presentation conventions are incomplete

**Details**:

- `notebook-writing.md:17–27` establishes H1 notebook titles and H2 sections.
- It does not define deeper-heading use, callout/blockquote patterns, table
  conventions, emphasis, or code-fence style.

**Severity**: LOW

**Recommended fix**: Add only the remaining Markdown conventions needed for
consistent learner notebooks.

Validation-record format is also a scope gap, represented by AQ-09 and not
counted again.

## 6. Ownership conflicts

**Findings**: 3

### AQ-02 — Python identifier naming

**Details**:

- Python identifier naming is normative in both `coding-standards.md` and
  `naming-conventions.md`.

**Severity**: LOW

**Recommended fix**: Use the ownership correction described in Section 1.

### AQ-09 — Validation record shape

**Details**:

- `compute-validation-policy.md` claims a validation template owns exact
  fields, but no such owner artifact exists.

**Severity**: MEDIUM

**Recommended fix**: Establish one canonical owner as described in Sections
3–5.

### AQ-15 — Module README design

**Details**:

- Module README design is effectively owned by a Cursor rule rather than a
  canonical standards document.

**Severity**: MEDIUM

**Recommended fix**: Move or formally declare ownership as described in
Section 5.

No conflict was found for security ownership, permissions versus compute, or
naming versus dataset object names.

## 7. Alignment with AGENTS.md guardrails

**Findings**: 2

### AQ-21 — Lesson workflow omits GitHub and Databricks Git-folder transfer

**Details**:

- `AGENTS.md:27–32` and `README.md:52–65` require Cursor → GitHub →
  Databricks Git folder → runtime validation.
- `notebook-authoring-checklist.md:43–47` and command output jump from
  `/validate-notebook` directly to runtime validation.

**Severity**: MEDIUM

**Recommended fix**: Include commit/push/pull as an explicit handoff before
Azure runtime validation, without making commands perform those actions
automatically.

### AQ-07 — Full-lesson bar conflicts with scaffolding

**Details**:

- The learner rule's unconditional Full-lesson bar conflicts with AGENTS'
  instruction to scaffold only under the checklist's Readiness precondition
  and Scaffold bar.

**Severity**: MEDIUM

**Recommended fix**: Apply the task-specific bar described in Section 2.

Aligned:

- Batch-only scope
- No automatic roadmap-status edits
- No fabricated validation evidence
- Readiness requires Started status plus a design-complete README
- Local tools do not run Spark

## 8. Alignment with notebook-authoring-checklist.md

**Findings**: 5

### AQ-05 — `/write-lesson` load set

**Details**:

- `/write-lesson` claims the validation load set but omits Additional reads.

**Severity**: MEDIUM

**Recommended fix**: Align the claim and load behavior.

### AQ-06 — `/review-module` depth

**Details**:

- `/review-module` weakens full notebook validation into spot-checking while
  calling it equivalent.

**Severity**: HIGH

**Recommended fix**: Make the review exhaustive or remove the equivalence
claim.

### AQ-07 — Scaffold versus full-lesson bar

**Details**:

- `learner-notebooks.mdc` ignores the Scaffold/Full-lesson distinction.

**Severity**: MEDIUM

**Recommended fix**: Select the correct bar based on the task.

### AQ-12 — Retired navigation wording

**Details**:

- The Scaffold bar still uses the retired “navigation bullets” name.

**Severity**: MEDIUM

**Recommended fix**: Refer to the target `Notebooks` table entry.

### AQ-21 — Incomplete workflow

**Details**:

- The recommended workflow omits the repository transfer step before runtime
  validation.

**Severity**: MEDIUM

**Recommended fix**: Add the GitHub/Git-folder handoff.

Otherwise aligned:

- Command write/review roles
- Skeleton versus full-lesson depth
- Readiness checks
- Required reads
- Authoring-versus-runtime boundary
- Issues-only command output

## 9. Format and structure consistency across the six files

**Findings**: 2

### AQ-13 — Consumer-list semantics

**Details**:

- All six use a “Referenced by” preamble, but the lists do not share one
  direct/transitive dependency meaning.

**Severity**: LOW

**Recommended fix**: Standardize the consumer-list semantics.

### AQ-22 — Closing scope pattern is inconsistent

**Details**:

- Only `compute-validation-policy.md` and
  `permissions-and-governance.md` have an explicit “What this file does not
  cover” section.
- The other four rely on their opening owner declaration.

**Severity**: LOW

**Recommended fix**: Either adopt a small “Does not cover” footer where
adjacent domains exist or document that the footer is optional.

All six have canonical-owner declarations, consumer statements, and
anti-duplication language. The four always-read standards point to the shared
checklist; the two conditional standards appropriately omit that boilerplate.

## 10. Actionability and clarity

**Findings**: 7

### AQ-23 — `F.col` preference does not define aggregate/grouping APIs

**Details**:

- `coding-standards.md:24–27` limits bare strings in transformation chains
  after `col()` is taught.
- Module 8 uses idiomatic `groupBy("service_type")`,
  `F.sum("tip_amount")`, and `F.avg(...)`.
- The standard does not say whether these are permitted.

**Severity**: MEDIUM

**Recommended fix**: Define the boundary by API: require `F.col` for Column
expressions and disambiguation; permit documented string-accepting APIs such
as `groupBy` and aggregate functions if that is the intended style.

### AQ-24 — “One idea per cell” has no review criterion

**Details**:

- `notebook-writing.md:67–68` requires one idea per cell but gives no example
  of when closely related setup, transform, and display work should remain
  together.

**Severity**: LOW

**Recommended fix**: Add one positive and one negative example, or label the
rule explicitly as reviewer judgment rather than a hard validation criterion.

Also relevant:

- AQ-03: “hardcoded paths” is broader than the owner's actual rule.
- AQ-04: “where both are idiomatic” does not resolve when SQL comparison is
  required.
- AQ-08: Tier 1 and safe author defaults are undefined.
- AQ-09: validation status/result/compatibility vocabularies are not
  separated.
- AQ-12: “navigation bullets” no longer names an actual README structure.

## Summary

- Total unique issues: **24**
- HIGH: **1**
- MEDIUM: **12**
- LOW: **11**

Top three priorities:

1. **AQ-06** — Make `/review-module` exhaustive or stop calling a spot-check
   equivalent to `/validate-notebook`.
2. **AQ-05** — Align `/write-lesson` with conditional compute and permissions
   reads, or narrow its “same standards” claim.
3. **AQ-09** — Create or define the validation-record template and reconcile
   its vocabulary with the compute policy.

No repository standards, rules, commands, roadmap, validation evidence, or
notebooks were modified as part of this audit.
