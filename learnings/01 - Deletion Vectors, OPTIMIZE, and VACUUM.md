# Learnings: Deletion Vectors, OPTIMIZE, and VACUUM

**Notebook:** [01 - Deletion Vectors, OPTIMIZE, and VACUUM.py](../11%20-%20Delta%20Lake%20Transactions,%20Schema,%20and%20Maintenance/01%20-%20Deletion%20Vectors,%20OPTIMIZE,%20and%20VACUUM.py)

**Module folder:** [11 - Delta Lake Transactions, Schema, and Maintenance](../11%20-%20Delta%20Lake%20Transactions,%20Schema,%20and%20Maintenance/)

**Runtime:** Azure Databricks DBR 17.3, auto-compaction **enabled by default**.

**Lab table:** `rideshare_dev.processed.fare_maint_lab`

This note is author-only. It records why the first Databricks run did not match the lesson `LIST` story. It does not change the learner notebook.

---

## Two things to keep straight

- **`LIST` is the folder.** It shows live files, obsolete files, `.bin` deletion vectors, `_delta_log`, and `.crc`. Ignore `.crc` and the log folder when counting data files.
- **Live** = what the **current** table version reads. **Obsolete** = still on disk, not used by the current version, waiting for `VACUUM`.

Auto-compaction runs **right after** a successful write. `DESCRIBE HISTORY` showed auto-`OPTIMIZE` at **versions 5, 7, and 9** after each DV `UPDATE`. Each of those commits **removed 2 data files + 1 deletion vector** and **added 1 clean Parquet**. `OPTIMIZE` does **not** delete files from disk; it only changes the current snapshot.

`VACUUM` does **not** purge deletion vectors and does **not** compact live files. It only deletes unused files that have passed the retain window.

---

## The version map for this notebook

| Version | What committed |
|---|---|
| 0 | `CREATE TABLE` |
| 1 | Step 0 `INSERT` |
| 2 | Step 1 `UPDATE` (DV **off**) |
| 3 | Step 2 `ALTER` (enable DVs) |
| 4 | Step 2 `UPDATE` (DV **on**) |
| **5** | **auto-`OPTIMIZE`** (`{"auto":"true"}`) — after Step 2 `UPDATE` |
| 6 | Step 3 first `UPDATE` (`trip_id` 1001) |
| **7** | **auto-`OPTIMIZE`** (`{"auto":"true"}`) — after Step 3 first `UPDATE` |
| 8 | Step 3 second `UPDATE` (`trip_id` 1004) |
| **9** | **auto-`OPTIMIZE`** (`{"auto":"true"}`) — after Step 3 second `UPDATE` |
| 10–11 | Step 4 `VACUUM` |

No auto-`OPTIMIZE` after Step 0 or Step 1. Deletion vectors were still off.

Labels below (`P0`, `P1`, …) are the Parquet files in commit order, not hashes from a specific run.

---

## Step 0 — `INSERT` four rows (DV off)

What happens: one Parquet write. Auto-compaction does not fire.

| | Parquet | `.bin` (DV) |
|---|---|---|
| **Live** | **1** (`P0`) | **0** |
| **Obsolete** | **0** | **0** |
| **On disk / `LIST`** | **1** | **0** |

Matches the lesson.

---

## Step 1 — `UPDATE` `1003` → `10.00` (DV still off)

What happens: full-file rewrite. `P0` is replaced in the snapshot by `P1` (all four current rows). `P0` stays on disk. No DV, so no `.bin`. Auto-compaction does not fire.

| | Parquet | `.bin` |
|---|---|---|
| **Live** | **1** (`P1`) | **0** |
| **Obsolete** | **1** (`P0`) | **0** |
| **On disk / `LIST`** | **2** | **0** |

Still matches the lesson. `P0` is obsolete for current reads, but **not** deleted yet (default 7-day retention). A plain `VACUUM` would leave it. It becomes removable only with `VACUUM … RETAIN 0 HOURS` after the retention check is disabled (lab only).

---

## Step 2 — enable DVs, then `UPDATE` `1003` → `12.00`

This step is two commits, then `LIST`. `LIST` runs **after** auto-compaction, so you never see the DV layout as a stable result.

### Commit v4 — the DV `UPDATE` (what the markdown describes)

- `P1` stays; a **deletion vector** marks the old `1003` row.
- A **small** Parquet `P2` holds the new `1003` row.

| | Parquet | `.bin` |
|---|---|---|
| **Live** | **2** (`P1` + `P2`) | **1** (marks rows in `P1`) |
| **Obsolete** | **1** (`P0`) | **0** |
| **On disk** | **3** | **1** |

The DV is usually a **sidecar** `.bin`, not a rewrite of `P1`. If `LIST` did not show a `.bin`, the DV may have been stored **inside `_delta_log`**. History still counted “1 deletion vector” removed.

### Commit v5 — auto-`OPTIMIZE` (before `LIST`)

Rewrites `P1` + `P2` + the DV into **one clean file** `P3` (four current rows, no DV). Those three objects become obsolete. They stay on disk.

| | Parquet | `.bin` |
|---|---|---|
| **Live** | **1** (`P3`) | **0** |
| **Obsolete** | **3** (`P0`, `P1`, `P2`) | **1** |
| **On disk / `LIST`** | **4** | **1** |

**What the lesson expected:** small new file, existing file still live, DV visible.

**What `LIST` showed:** extra files on disk, but **one live Parquet and no live `.bin`**. The DV story was already compacted away.

---

## Step 3 — two more DV `UPDATE`s, then one `LIST`

Same pattern **twice**. `LIST` is only at the end, so you see the state after **both** auto-`OPTIMIZE`s (v7 and v9).

### First `UPDATE` (`1001` → `4.00`) — v6, then auto-`OPTIMIZE` v7

1. DV write: live = `P3` + DV + small `P4`.
2. Auto-compact: live = one clean `P5`. `P3`, `P4`, and that `.bin` become obsolete.

### Second `UPDATE` (`1004` → `3.50`) — v8, then auto-`OPTIMIZE` v9

1. DV write: live = `P5` + DV + small `P6`.
2. Auto-compact: live = one clean `P7`. `P5`, `P6`, and that `.bin` become obsolete.

### After the Step 3 cell (`LIST`)

| | Parquet | `.bin` |
|---|---|---|
| **Live** | **1** (`P7`, all four current tips) | **0** |
| **Obsolete** | **7** (`P0`…`P6`) | **3** (one per DV `UPDATE`) |
| **On disk / `LIST`** | **8** | **3** |

**What the lesson expected:** many **live** small files (original + DV patches).

**What `LIST` showed:** a **pile of files on disk**, but only **one live** Parquet. Auto-compaction had already done Step 5’s job three times.

---

## Step 4 — `VACUUM RETAIN 0 HOURS`

`VACUUM` does **not** compact and does **not** purge live DVs. It **deletes unused files** that are older than the retain window. With `RETAIN 0` and the check disabled, that is **everything not in the current snapshot**.

Current snapshot is already **one clean file** (`P7`). So `VACUUM` physically removes `P0`–`P6` and the obsolete `.bin`s.

| | Parquet | `.bin` |
|---|---|---|
| **Live** | **1** (`P7`) | **0** |
| **Obsolete** | **0** | **0** |
| **On disk / `LIST`** | **1** | **0** |

**What the lesson expected:** live small files still there (`VACUUM` ≠ compact).

**What `LIST` showed:** one file. It looks like `VACUUM` compacted. It only **swept** files auto-compaction had already made obsolete. A newer file seen after this cell (for example `c602deac` on the first run) is `P7` from version 9, not a `VACUUM` rewrite.

The Databricks command that physically rewrites files to remove DV soft-deletes is `REORG TABLE … APPLY (PURGE)`, not `VACUUM`. That command is not in this notebook.

---

## Step 5 — learner `OPTIMIZE`

Live layout is **already one file**. Manual `OPTIMIZE` has nothing useful to merge.

It may **no-op** (still 1 file) or **rewrite** into a new `P8` and leave `P7` obsolete (2 Parquets on disk). Either way this step cannot show “many live files → fewer live files,” because auto-compaction already collapsed them at Steps 2–3.

---

## Step 6 — `VACUUM RETAIN 0` again

If Step 5 rewrote: delete `P7`, leave `P8` → **1** Parquet.

If Step 5 no-op’d: still **1** Parquet.

**`.bin`:** still **0**.

---

## Why the notebook `LIST` results did not match the lesson

| Step | Lesson wanted after `LIST` | With auto-compaction on, `LIST` actually reflects |
|---|---|---|
| 2 | Live file **with DV** + **small** new file | **1 live** clean file; DV already rewritten |
| 3 | **Many live** files | **1 live** file; lots of **obsolete** leftovers |
| 4 | `VACUUM` leaves live small files | `VACUUM` deletes leftovers → **1** file |
| 5 | `OPTIMIZE` reduces live files | Already **1** live file |

The DVs **did** exist, for a moment, after each DV `UPDATE`. Auto-compaction **immediately** rewrote them away. Steps 2–4 are not visible in `LIST` unless that auto-`OPTIMIZE` is turned off before the first write.

`VACUUM` was **not** the culprit. History versions **5, 7, and 9** with `OPTIMIZE` and `{"auto":"true"}` are system-triggered compaction, not the learner `OPTIMIZE` in Step 5.

---

## Intended lesson layout (auto-compaction **off**)

This is what Steps 2–4 are designed to show. It is **not** what the first DBR 17.3 run showed.

| After | Live Parquet | Obsolete Parquet | Live `.bin` |
|---|---|---|---|
| Step 0 | 1 | 0 | 0 |
| Step 1 | 1 (rewrite) | 1 (Step 0 file) | 0 |
| Step 2 | 2 (Step 1 file + small DV write) | 1 | 1 |
| Step 3 | several live files | Step 0 file still obsolete | DVs on the files that were updated |
| Step 4 `VACUUM RETAIN 0` | those live small files **remain** | eligible obsolete files **gone** | live DVs remain |
| Step 5 `OPTIMIZE` | fewer live files (often 1) | previous live files now obsolete | DVs resolved as a side effect of rewrite |
| Step 6 `VACUUM RETAIN 0` | compacted live file(s) | previous files gone | 0 |

---

## Agreed authoring fix (not applied in this note)

Keep Steps 4–6. Do not add `DESCRIBE HISTORY` as a lesson cell (still fenced). Use history in Databricks when validating.

Disable auto-compaction **before the first DML** in the Step 0 code cell:

```python
spark.conf.set("spark.databricks.delta.autoCompact.enabled", "false")
```

Optional on `CREATE` (this table only):

```sql
TBLPROPERTIES (
  'delta.enableDeletionVectors' = 'false',
  'delta.autoOptimize.autoCompact' = 'false'
)
```

One markdown sentence in Step 0: this lab turns auto compaction off so each `LIST` is from the cell just run. Do not teach auto compaction.

If small files still vanish on write, also consider `'delta.autoOptimize.optimizeWrite' = 'false'`.
