# Learnings: Deletion Vectors, OPTIMIZE, and VACUUM

**Notebook:** [01 - Deletion Vectors, OPTIMIZE, and VACUUM.py](../11%20-%20Delta%20Lake%20Transactions,%20Schema,%20and%20Maintenance/01%20-%20Deletion%20Vectors,%20OPTIMIZE,%20and%20VACUUM.py)

**Runtime:** DBR 17.3. **Table:** `rideshare_dev.processed.fare_maint_lab`

Author-only. Auto-compaction **enabled**. Ignore `_delta_log/` and `.crc`.

From `DESCRIBE HISTORY` on this runtime:

| Version | Operation | Auto-`OPTIMIZE`? |
|---|---|---|
| 0 | `CREATE TABLE` | No |
| 1 | `INSERT` (four rows) | No |
| 2 | `UPDATE` 1003, DV **off** | No |
| 3 | Enable deletion vectors | No |
| **4** | `UPDATE` 1003, DV **on** | **No** |
| 5 | `UPDATE` 1001, DV on | Then **v6** `OPTIMIZE` `"auto":"true"` (~1s) — 2 files + 1 DV removed from the snapshot |
| 7 | `UPDATE` 1004, DV on | Then **v8** `OPTIMIZE` `"auto":"true"` (~4s) — 3 files + 1 DV removed from the snapshot |

After each auto-`OPTIMIZE`, **live** data is **one Parquet file** and **no live `.bin`**. Obsolete files can stay in `LIST` until `VACUUM`. What you **read** is that one clean file.

`D0`, `D1`, … = data files. `B1`, `B2`, … = `.bin` files. Labels, not hashes.

---

## Step 0 — `INSERT` (DV off)

| | Data | `.bin` |
|---|---|---|
| **Write** | `D0` (four rows) | none |
| **Live** | `D0` | none |
| **On disk / `LIST`** | **1** | **0** |

Auto-compaction does not run.

---

## Step 1 — `UPDATE` 1003, DV off

Full-file rewrite. No `.bin`. Auto-compaction does not run.

| | Data | `.bin` |
|---|---|---|
| **Write** | New `D1` (four current rows). `D0` obsolete | none |
| **Live** | `D1` | none |
| **On disk / `LIST`** | **2** (`D0`, `D1`) | **0** |

---

## Step 2 — enable DV, `UPDATE` 1003 again

`ALTER` adds no files.

**First DV `UPDATE` (history v4). No auto-`OPTIMIZE` after this version.**

| | Data | `.bin` |
|---|---|---|
| **Write** | `D1` stays. Small `D2` = new `1003` | `B1` on `D1` (old `1003` skipped) |
| **Live** | `D1` + `D2` | `B1` |
| **Obsolete** | `D0` | none |
| **On disk / `LIST`** | **3** | **1** |

This is the only DV step where `LIST` can still show the DV layout (base + small file + `.bin`).

---

## Step 3 — two more DV `UPDATE`s

### `UPDATE` 1001 (history v5)

Hits the **same** live base `D1` (already has a DV).

| | Data | `.bin` |
|---|---|---|
| **Write** | Small new file for `1001`. New `.bin` on `D1` | Extra small Parquet + `.bin` |

**Then auto-`OPTIMIZE` (v6), ~1 second later.** Snapshot: **one** clean Parquet (`D3`). No live `.bin`. Old data files and `.bin`s are obsolete but may still appear in `LIST`.

**Live after v6: 1 data file. 0 `.bin`.**

### `UPDATE` 1004 (history v7)

Hits that new clean base. Writes a small file + `.bin` again.

**Then auto-`OPTIMIZE` (v8), ~4 seconds later.** Again: **one** clean Parquet. No live `.bin`.

**Live after Step 3: 1 data file. 0 `.bin`.**

`LIST` may show more names (obsolete leftovers). The table you query is **one** file. That is what “we saw only one file after DV enabled” means after Step 3 — not after the first DV `UPDATE` at v4.

---

## Step 4 — `VACUUM RETAIN 0`

Deletes obsolete files only. Live is already one file, so `LIST` goes to **1** data file and **0** `.bin`. Looks like `VACUUM` compacted. It only removed leftovers from the auto-`OPTIMIZE`s.

---

## Step 5 — `OPTIMIZE`

Live is already one file. Your `OPTIMIZE` has nothing to merge. `LIST` stays **1** file, or **2** if it rewrites into a new Parquet and leaves the old one.

---

## Step 6 — `VACUUM RETAIN 0` again

**1** data file. **0** `.bin`.
