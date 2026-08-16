# Markdown Context Routing Optimization

Author-only architecture report. This is not a learner notebook or a
normative standard.

## Status

- Living routing model: [02-How-This-Repository-Uses-Rules-and-Standards.md](02-How-This-Repository-Uses-Rules-and-Standards.md)
- Structural routing implementation: complete in `f919c7e`
- Safeguard follow-up: complete in the current working tree
- Static routing assertions: 32 passed
- Behavioral specification scenarios: 25 passed
- Authenticated Cursor attachment/read-trace test: pending
- Date: 2026-08-16

The canonical baseline is `48975a3`, the parent of optimization commit
`f919c7e`. The current measurements include the working-tree safeguard
follow-up applied after that commit.

## Purpose

Notebook commands previously shared one broad read list. That made
scaffold-only and module-review workflows read standards they did not always
need. The refactor introduces command-specific manifests and scoped reads
while preserving canonical ownership and authoring safeguards.

This work optimizes declared context routing. It does not change course
content, dataset contracts, notebook content, roadmap status, or runtime
validation evidence.

## Measurement method

The estimates trace each command through:

1. Its command file.
2. Applicable Cursor rules.
3. The notebook checklist or the command's independent routing.
4. Required standards and canonical data documents.

Each declared file is counted once. Scoped reads count the named heading and
its child headings, with overlapping ranges deduplicated. Dynamic module
README rows, target notebooks, sibling notebooks, and roadmap rows are
excluded because their size varies by target.

The reproducible measures are source lines and characters. They are not
Cursor token counts: Cursor does not expose its internal context
construction, tokenization, deduplication, or pruning behavior.

## Estimated results

| Command | Baseline lines | Core-profile lines | Baseline chars | Core-profile chars | Character change |
| --- | ---: | ---: | ---: | ---: | ---: |
| `/new-lesson` | 1,198 | 696 | 47,809 | 27,288 | -42.9% |
| `/write-lesson` | 1,116 | 837 | 44,210 | 34,044 | -23.0% |
| `/validate-notebook` | 1,105 | 835 | 43,551 | 33,925 | -22.1% |
| `/review-module` | 1,213 | 879 | 48,259 | 35,817 | -25.8% |
| `/write-module-readme` | 941 | 489 | 36,587 | 18,276 | -50.0% |

The core profile uses the **Core data model** and excludes conditional
compute and permissions reads. A Module 5 + Unity Catalog profile adds about
91–105 scoped lines. Full conditional files add:

| Conditional read | Lines | Characters |
| --- | ---: | ---: |
| `compute-validation-policy.md` | 80 | 3,726 |
| `permissions-and-governance.md` | 105 | 5,012 |

These results correct earlier comparisons that used a broader historical
baseline. Against the canonical pre-optimization commit, every command's
declared core profile is smaller, including `/review-module`.

## Changes made

### Command-specific manifests

`docs/standards/notebook-authoring-checklist.md` now owns four manifests:

- **Scaffold manifest** for `/new-lesson`
- **Full-lesson manifest** for `/write-lesson`
- **Validation manifest** for `/validate-notebook`
- **Module-review manifest** for `/review-module`

The Scaffold manifest keeps notebook structure, pedagogy needed for
objectives, naming, roadmap, README design, and dataset setup. It excludes
coding standards because a scaffold contains no runnable lesson code.

The Full-lesson and Validation manifests remain comprehensive for runnable
lesson content. Their module README scope includes **Minimum privileges
required** when present. Compute and permissions remain conditional.

The Module-review manifest uses targeted sections for module-level
consistency checks and remains lighter than validating every notebook.

### Scoped canonical reads

`docs/data/dataset-overview.md` remains one canonical file. Manifests name
the exact sections required by the target:

- **Core data model** for Modules 1–4
- **Supplementary: `drivers` (nested XML)** when nested driver data is used
- The matching **Module pipeline** subsection for Modules 5–8
- **Unity Catalog platform reference** when a lesson uses governed objects
  or Volume paths

Scoped reads use a backticked path plus exact headings. Cursor has no
section-level `@path` syntax.

### Command and rule routing

Lesson commands now point to the applicable manifest instead of repeating
the checklist's read lists and acceptance criteria. Command-specific
safeguards remain local to their commands.

`learner-notebooks.mdc` defers to the active command manifest and still
supports ad-hoc notebook edits. `course-authoring.mdc` keeps standalone
README routing for edits performed without a slash command.

Expansion is allowed within the selected manifest's canonical sources when
a scoped read is insufficient. It does not authorize loading another
command's manifest.

`/write-module-readme` remains independent of the notebook checklist. Its
roadmap, teaching, naming, dataset, and permissions reads are scoped to the
module design being authored. Dataset reads follow the same section rules as
the checklist's **Dataset scope**: Modules 1–4 stay on **Core data model**;
pipeline subsections apply only to Modules 5–8.

## Safeguards retained

Static coverage confirms that the routing still reaches:

- Module `Started` status and design-complete README checks
- Roadmap/filesystem inconsistency reporting
- Skeleton-only and full-lesson boundaries
- Worked-example and exercise ordering
- Sibling-notebook voice and idiom comparison
- Dataset schema, path, join-key, and object-name contracts
- Security and personal-value restrictions
- Conditional compute and minimum-privilege rules
- Module 5 setup/cleanup parameterization and safe author defaults
- Module notebook sequence and leaked-evidence checks
- Unfinished-scaffold, hidden-state, and intentional-error spot checks
- Separation between Cursor authoring review and Databricks runtime evidence

These safeguards passed static assertions and isolated specification
scenarios. They do not prove Cursor's internal attachment behavior.

## Static verification completed

- 32 ephemeral path, heading, manifest, inventory, boundary, and
  forbidden-write assertions
- `git diff --check`
- IDE lint checks
- File and section reference review
- Canonical-owner and requirement-coverage review
- Confirmation that dataset, notebooks, roadmap, and validation evidence
  were not edited

## Behavioral specification testing completed

Twenty-five isolated scenarios passed:

- Scaffold/README routing: incomplete README, `Not Started` plus stray
  notebook, Module 5 Notebook 99 parameterization, missing roadmap row, and
  unresolved design.
- Lesson writing/validation: missing scaffold and sibling fallback, skeleton
  rejection, missing runnable demonstration, personal-value leak,
  compute/privilege routing, teaching order, and runtime boundary.
- Module review: numbering and README/file mismatches, leaked evidence,
  unfinished scaffold, hidden state, intentional-error handling, dataset
  mismatch, clean control, issues-only output, and lighter spot-check
  boundary.

Tests ran in a disposable worktree. Fixtures were removed, no commits were
created, and course roadmap, dataset, validation evidence, and real learner
notebooks remained unchanged.

## Observed read behavior and remaining limitation

The deterministic harness confirmed the intended decisions, but an
authenticated headless Cursor CLI was unavailable. Two harness passes read
some scoped standards in full during preflight; one respected the scoped
reads. This does not establish how a real slash-command turn constructs
context.

Final empirical validation therefore requires fresh authenticated Cursor
chats with controlled open files. Record which files and sections are read,
whether glob rules attach, and whether scoped sources are systematically
opened in full. Treat systematic whole-file expansion as an efficiency
regression, not a correctness failure. Keep these results separate from
Azure Databricks runtime evidence.
