# Author vault (`vault/`)

Obsidian vault for **author notes only**. Course source-of-truth files stay
outside this folder so Cursor, slash commands, and Databricks Git paths keep
working.

## How to open

1. In Obsidian: **Open folder as vault**
2. Select this folder:
   `PySpark on Azure Databricks Academy/vault`
3. Do **not** open the repo root as the vault

Start from `home.md`.

## What belongs here

| Path | Purpose |
|---|---|
| `home.md` | Vault dashboard |
| `progress.md` | Course progress tracker |
| `decisions.md` | Decision log |
| `.obsidian/` | Obsidian app settings for this vault |

Author-only Module 7 notes live outside this vault at
[`take_notes/NB07_personal_notes.md`](../take_notes/NB07_personal_notes.md)
(linked from progress/decisions; not a vault-local file).

## What does **not** belong here

Do not move these into `vault/`:

- `COURSE_MODULES.md`, `README.md`, `AGENTS.md`
- `docs/` (standards, dataset, validation)
- Module `README.md` files and learner notebooks
- Approved Module 7 requirements (`BRD.md`, mapping docs)
- `.cursor/` rules and slash commands

Link to those files with relative markdown links such as
`[COURSE_MODULES](../COURSE_MODULES.md)`.

## Intra-vault links

Use short wikilinks between author notes:

- `[[home]]`
- `[[progress]]`
- `[[decisions]]`
- `[[NB07_personal_notes]]`
