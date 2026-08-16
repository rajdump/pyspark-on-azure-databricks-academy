# Standards Authoring

This file is the canonical owner of the structure, language, and
cross-reference conventions for files under `docs/standards/`.

Its direct consumers are agents creating or auditing standards. It has no
indirect consumers in normal lesson or module-authoring workflows.

## Document types

Use the structure that matches the file's job:

- **Normative standard:** Owns rules for one domain, such as coding,
  pedagogy, naming, or permissions.
- **Orchestration hub:** Coordinates workflows, required reads, or acceptance
  bars while delegating detailed rules to normative standards.

Do not force an orchestration hub into the exact section order of a normative
standard.

## Required opening

Every standard starts with:

1. One H1 title.
2. A plain-English statement of what the file owns.
3. Its consumers, distinguishing direct readers from consumers that receive
   the standard through an orchestration hub.

Define specialized terms before using them. If a file coordinates several
workflows, add an **At a glance** section near the top.

## Rules and headings

- Use H2 headings for major domains and H3 headings for subdivisions.
- Keep sections short and use parallel wording for related checks.
- Write requirements so an author or reviewer can observe whether they pass.
- Use direct imperative wording, `must`, or `never` for requirements. Use
  `should` or `prefer` for defaults that need judgment, and `may` for
  permitted choices.
- Label judgment-based guidance so it is not reported as a blocking failure.
- Keep examples current, minimal, and consistent with the repository's
  canonical course, roadmap, and dataset documents.
- Isolate module-specific exceptions and explain why the shared rule does not
  apply.

## References

- Use `@path` when the current prompt or rule must eagerly include another
  whole file.
- For conditional routing, use a backticked path and explicitly say whether
  to read the whole file or named sections. The agent must locate and read
  the selected content with search/read tools; do not use `@path` for every
  branch of a manifest.
- Use a backticked path when identifying a consumer, owner, or related file
  for information only.
- For a scoped read, name the exact headings. Cursor has no section-level
  `@path` syntax.
- Confirm referenced files and section headings exist.

## Ownership and duplication

Each rule has one canonical owner. Other standards may summarize that rule
only when a workflow gate needs it; otherwise they point to the owner.

When an overlap is found:

1. Keep the full rule in its owning standard.
2. Replace copies in non-owners with a precise reference.
3. Verify that no requirement is lost.

## Boundaries

A normative standard ends with **Does not cover**, listing adjacent domains
and their owners. An orchestration hub may instead use a clear workflow or
validation-boundary section when that communicates its exclusions better.

## Review checklist

Before accepting a standard, confirm:

- Its purpose, owned domain, consumers, and exclusions are clear.
- Requirements and judgment-based guidance are distinguishable.
- Technical examples match `README.md`, `COURSE_MODULES.md`, and
  `docs/data/dataset-overview.md` where applicable.
- References resolve and use the correct reference form.
- Detailed rules are not duplicated across owners.
- The wording is concise enough to understand on a first read.

## Does not cover

- The domain rules inside each standard; those remain owned by that file.
- Cursor command or `.mdc` structure; audit those under their own owners.
