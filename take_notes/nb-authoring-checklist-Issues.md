# Notebook Authoring Checklist — Identified Issues and Solutions

Tracks duplication/ownership/clarity issues found across
docs/standards/notebook-authoring-checklist.md and its dependents, and the
agreed fix per issue. Update the Status column as each group below is
applied; do not delete resolved rows — mark them Verified instead.

## Group 1 — Single-source "no automatic roadmap/validation writes"
| ID | Category | Priority | Location | Problem | Fix | Status |
|---|---|---|---|---|---|---|
| I1 | Duplicate | P1 | checklist.md, new-lesson.md, write-lesson.md, validate-notebook.md, review-module.md | Same prohibition restated in 5 files | Delete restated lines; keep only in AGENTS.md "Do not write automatically" | Verified |
| I2 | Duplicate | P1 | learner-notebooks.mdc lines 34–36 | Restates the same prohibition, missed by the original Group 1 scope | Delete; point to AGENTS.md instead | Verified |
| I3 | Duplicate | P2 | course-authoring.mdc lines 25–26 | Separately restates "status changes are author-owned" | Delete or replace with a pointer to AGENTS.md | Verified |
| I4 | Decision | — | validate-notebook.md lines 1–4, review-module.md lines 1–3 | Opening-paragraph framing partially echoes the policy | Keep as-is — intentional framing, not duplication to remove | Verified |

## Group 2 — De-duplicate Required-reads list
| ID | Category | Priority | Location | Problem | Fix | Status |
|---|---|---|---|---|---|---|
| I5 | Duplicate | P1 | validate-notebook.md lines 15–22 | Re-enumerates the six Required-reads sources; also carries the Full-lesson bar's runnable-coverage test | Point to checklist's Required reads AND Full-lesson bar (preserve the coverage-test nuance) | Verified |
| I6 | Duplicate | P1 | learner-notebooks.mdc lines 13–24 | Direct six-item re-enumeration | Point to checklist's Required reads only | Verified |

## Group 3 — Canonicalize the Started/README-completeness gate
| ID | Category | Priority | Location | Problem | Fix | Status |
|---|---|---|---|---|---|---|
| I7 | Duplicate/Ownership | P1 | COURSE_MODULES.md lines 18–21, course-authoring.mdc lines 27–31, checklist.md lines 73–78, new-lesson.md steps 3–4 | Same gate restated 4 ways | course-authoring.mdc becomes the sole detailed definition; others point to it or to checklist's new Readiness precondition | Verified |
| I8 | Duplicate | P1 | AGENTS.md lines 52–54 | 5th independent restatement of the gate | Replace with a pointer to checklist's Readiness precondition | Verified |
| I9 | Duplicate | P1 | review-module.md lines 9–14 | Repeats README-completeness criteria | Point to course-authoring.mdc's design-complete definition | Verified |
| I10 | Ownership/Clarity | P2 | checklist.md Scaffold bar bullets 1–2 vs 3–5 | Mixes readiness preconditions with scaffold-content requirements | Split into "Readiness precondition" and "Scaffold contents" subsections | Verified |
| I11 | Clarity | P2 | checklist.md Scaffold bar bullet 1 | Procedural "verify...stop" language duplicates new-lesson.md step 4 | Reword as a stated condition; leave stop/report behavior to new-lesson.md | Verified |

## Group 4 — Remove the Module 5 exception from shared/peer docs
| ID | Category | Priority | Location | Problem | Fix | Status |
|---|---|---|---|---|---|---|
| I12 | Ownership/Stale | P1 | checklist.md lines 65–68 | Module-specific exception embedded in the shared Full-lesson bar | Delete; already covered by Module 5 README + permissions-and-governance.md | Verified |
| I13 | Duplicate | P2 | coding-standards.md lines 59–62 vs permissions-and-governance.md lines 87–92 | Same Module 5 exception documented in two peer "detailed-rule" standards | Have coding-standards.md reference permissions-and-governance.md instead of restating specifics | Verified |

## Group 5 — Trim restated coding-standards.md detail
| ID | Category | Priority | Location | Problem | Fix | Status |
|---|---|---|---|---|---|---|
| I14 | Duplicate/Ownership | P2 | checklist.md lines 63–64, write-lesson.md lines 31–32 | Restate F-imports/noqa/line-length/.collect() detail owned by coding-standards.md | Replace both with a plain pointer | Verified |

## Group 6 — Checklist metadata and scope cleanups
| ID | Category | Priority | Location | Problem | Fix | Status |
|---|---|---|---|---|---|---|
| I15 | Gap | P2 | checklist.md lines 4–6, Command roles table | /review-module missing from referrer list and roles table | Add a row/reference for /review-module | Verified |
| I16 | Gap | P2 | checklist.md lines 11–12, Recommended workflow | Required-reads trigger sentence and workflow diagram omit module review | Add /review-module, or explicitly note it's a separate optional workflow | Verified |
| I17 | Gap | P2 | checklist.md (no scope note) | Bars could be read as implying runtime validation | Add one line: authoring quality only, see compute-validation-policy.md | Verified |
| I18 | Duplicate/Removable | P2 | checklist.md lines 47–49 | "Don't use chat instead of /write-lesson" duplicated from write-lesson.md | Delete from checklist; keep only in write-lesson.md | Verified |

## Group 7 — Close review-module.md's checklist-consumption gap
| ID | Category | Priority | Location | Problem | Fix | Status |
|---|---|---|---|---|---|---|
| I19 | Gap | P2 | review-module.md | Unlike the other three commands, has no explicit "before reviewing, read the checklist's Required/Additional reads" instruction | Add that instruction alongside its existing checklist reference | Verified |
