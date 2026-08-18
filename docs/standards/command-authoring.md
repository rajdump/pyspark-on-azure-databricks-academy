# Command Authoring Standard

This file is the canonical owner of the structure of slash-command files in
`.cursor/commands/`. A command orchestrates one authoring workflow. It never
restates a rule that `AGENTS.md` or a normative standard already owns.

Direct readers: agents creating or auditing a command file. The commands
themselves — `/write-module-readme`, `/new-lesson`, `/write-lesson`,
`/validate-notebook`, and `/review-module` — are the artifacts this standard
governs rather than its readers.

## Required blocks

Every command uses these blocks, in this order:

| Block | Answers | Required |
|---|---|---|
| Purpose | what this command produces or checks | yes |
| Response format | which output rule applies | yes |
| Reads | what context must be loaded | yes |
| Target | what this acts on, and what to do when it cannot be identified | yes |
| Guards | what prevents proceeding once the target is known | yes |
| Steps | the command-specific work | yes |
| Verify | what the result is checked against | yes |
| Boundaries | what this command never does | yes |
| Next | the successor command or workflow | only when one exists |

Never drop a required block because it is short, and never move one out of
order. Fixed positions are what keep the commands comparable as different
agents edit them.

## Template

```markdown
<One-sentence purpose.>

Response format: @.cursor/rules/notebook-command-output.mdc

Reads:
- `docs/standards/<file>.md`
  - <required section>, <required section>
  - <conditional section>, only when <condition>
- @<path> — whole file, because <reason it cannot be scoped>

Target: <what this acts on>. If missing or ambiguous, <stop and report | ask once>.

Guards — stop before proceeding when:
- <condition> → report <what>

Steps:
1. <Action.>
2. <Action.>

Verify: <named bar or gate, or the output contract for a review command>.

Boundaries:
- Automatic-write restrictions: `AGENTS.md`, <Author-only writes>.
- This command does not <excluded scope>.

Next: <successor command.>
```

## Reads

- Prefer a scoped read: a backticked path followed by the exact section names.
- Use `@path` only when the whole file is genuinely required, and state the
  reason inline. Naming a section does not load only that section, so an
  unnecessary `@` costs the whole file on every run.
- Group sections beneath their file. Never repeat a path.
- Give every conditional read the condition that triggers it.
- Reference form is owned by [[References]] in
  `docs/standards/standards-authoring.md`.

## Target and Guards

**Target** owns identification only: can this command uniquely determine what
to act on? Its failure mode is a missing or ambiguous target, and it must say
which response applies — stop and report, or ask once.

**Guards** own every condition after the target is known, such as readiness
and content state. Write each guard as a condition and the report it produces.

A command with no post-target stop condition must write
`Guards: none after target resolution` rather than omitting the block.

## Verify

- A command that writes an artifact verifies that artifact against a named
  bar, gate, or acceptance definition.
- A command that reviews verifies its own output against the response
  contract, such as citing every issue and never listing passed checks.

## Boundaries

- `Reads` lists dependencies that require opening another file.
- `Boundaries` lists policy already in context through `AGENTS.md`, plus what
  this command specifically does not do.
- Never list the same dependency in both blocks.
- A read-only command states that here, not in **Purpose**.

## Does not cover

- Command read manifests, acceptance bars, and command boundaries — see
  `docs/standards/notebook-authoring-checklist.md`.
- Automatic-write restrictions — see `AGENTS.md`.
- Response formatting detail — see
  `.cursor/rules/notebook-command-output.mdc`.
- The structure of `.cursor/rules/*.mdc` files — see
  `docs/standards/rule-authoring.md`.
- Standards structure and cross-reference conventions — see
  `docs/standards/standards-authoring.md`.
