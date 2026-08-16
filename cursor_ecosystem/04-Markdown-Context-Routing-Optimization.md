# Markdown Context Routing Optimization

Author-only architecture report. This is not a learner notebook or a
normative standard.

## Status

- Structural routing implementation: complete
- Static requirement-coverage review: complete
- Behavioral scenario testing: pending
- Date: 2026-08-16

The baseline is commit `48975a3`. The optimized state described here is the
current uncommitted working tree based on that commit; record the resulting
commit ID here after the changes are committed.

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

Each declared file is counted once. Scoped reads count only the named
sections. Conditional compute and permissions files produce ranges because
they do not apply to every target.

These are line-based context estimates, not exact Cursor token counts.
Cursor does not expose its internal context construction, tokenization, or
deduplication behavior.

## Estimated results

| Command | Before | After | Estimated reduction |
| --- | ---: | ---: | ---: |
| `/new-lesson` | ~1,145 lines | ~630–740 lines | ~35–45% |
| `/write-lesson` | ~1,060 lines | ~770–870 lines | ~18–27% |
| `/validate-notebook` | ~1,050 lines | ~770–870 lines | ~17–27% |
| `/review-module` | ~1,160 lines | ~810–900 lines | ~22–30% |
| `/write-module-readme` | ~890 lines | ~430–630 lines | ~29–52% |

Ranges vary by module, dataset sections, and whether compute or permission
rules apply.

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
lesson content. Compute and permissions remain conditional.

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

`/write-module-readme` remains independent of the notebook checklist. Its
roadmap, teaching, naming, dataset, and permissions reads are now scoped to
the module design being authored.

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
- Module notebook sequence and leaked-evidence checks
- Separation between Cursor authoring review and Databricks runtime evidence

This is static coverage evidence. It does not yet prove runtime command
behavior in deliberate edge cases.

## Static verification completed

- `git diff --check`
- IDE lint checks
- File and section reference review
- Canonical-owner and requirement-coverage review
- Confirmation that dataset, notebooks, roadmap, and validation evidence
  were not edited

## Scenario testing still required

Run the commands against deliberate cases before calling the behavioral
validation complete:

1. `/new-lesson` with an incomplete module README.
2. `/new-lesson` for a `Not Started` module containing a stray notebook.
3. `/write-lesson` with a missing scaffold and with no in-module sibling.
4. `/validate-notebook` on a skeleton, a missing worked example, and a
   personal-value leak.
5. `/validate-notebook` on compute-specific and privilege-specific lessons.
6. `/review-module` with a numbering gap, README/file mismatch, or leaked
   validation evidence.
7. `/write-module-readme` with a missing roadmap row and an unresolved
   material design decision.

Record scenario outcomes separately from Azure Databricks runtime evidence.
