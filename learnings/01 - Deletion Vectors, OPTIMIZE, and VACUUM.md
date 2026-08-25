# Learnings: Deletion Vectors, OPTIMIZE, and VACUUM

**Notebook:** `01 - Deletion Vectors, OPTIMIZE, and VACUUM` (Module 11)

**Table:** `rideshare_dev.processed.fare_maint_lab`

---

## Version 0 — CREATE TABLE

Creates empty table with `delta.enableDeletionVectors = false`.

**Files on disk:** None (just `_delta_log/`)

---

## Version 1 — INSERT 4 rows

| Metric | Value |
| --- | --- |
| numFiles | 1 |
| numOutputRows | 4 |
| numOutputBytes | 2,186 |

**Files on disk:** 1 parquet (2,186 B) — ACTIVE, all 4 rows

---

## Version 2 — UPDATE trip_id=1003 (DV OFF)

| Metric | Value |
| --- | --- |
| numRemovedFiles | 1 |
| numAddedFiles | 1 |
| numAddedBytes | 2,186 |
| numCopiedRows | **3** |
| numUpdatedRows | 1 |

**Files on disk:**

| File | Size | Status |
| --- | --- | --- |
| Original parquet | 2,186 B | OBSOLETE |
| New parquet (full rewrite) | 2,186 B | ACTIVE (4 rows) |

**Explanation:** Without DVs, Spark must rewrite the whole file. It read 4 rows, changed 1, and wrote all 4 into a new file. `numCopiedRows=3` is the wasted work.

---

## Version 3 — SET TBLPROPERTIES

Enables deletion vectors. No file changes.

---

## Version 4 — UPDATE trip_id=1003 (DV ON)

| Metric | Value |
| --- | --- |
| numRemovedFiles | **0** |
| numAddedFiles | 1 |
| numAddedBytes | 2,086 |
| numCopiedRows | **0** |
| numUpdatedRows | 1 |
| numDeletionVectorsAdded | **1** |
| numDeletionVectorsRemoved | 0 |
| numDeletionVectorsUpdated | 0 |

**Files on disk (LIST captured before auto-compact):**

| File | Size | Status |
| --- | --- | --- |
| V1 parquet | 2,186 B | Obsolete (since V2) |
| V2 parquet | 2,186 B | ACTIVE — 3 live rows, DV masks trip_id=1003 |
| DV `.bin` | 43 B | ACTIVE — marks 1 row in V2 parquet |
| V4 parquet | 2,086 B | ACTIVE — updated trip_id=1003 value |

**Explanation:** No file was removed or rewritten. The 43-byte DV tells Spark "skip the trip_id=1003 row in the base file." The updated value lives in the small new parquet. `numCopiedRows=0` — zero wasted work.

**Comparison — Step 1 vs Step 2:**

| Metric | Step 1 (DV off) | Step 2 (DV on) |
| --- | --- | --- |
| numCopiedRows | 3 | **0** |
| numRemovedFiles | 1 | **0** |
| numAddedBytes | 2,186 (full) | **2,086** (partial) |
| Base file rewritten? | Yes | **No** |

---

## Version 5 — OPTIMIZE (auto-compaction)

Fires automatically after V4.

| Metric | Value |
| --- | --- |
| numRemovedFiles | 2 |
| numRemovedBytes | 4,272 (= 2,186 + 2,086) |
| numDeletionVectorsRemoved | 1 |
| numAddedFiles | 1 |
| numAddedBytes | 2,186 |

**What it did:** Compacted the DV'd base file + the V4 fragment into one clean file (all 4 rows, no DV).

**Active after V5:** 1 single clean file (2,186 B)

---

## Version 6 — UPDATE trip_id=1001 (DV ON)

| Metric | Value |
| --- | --- |
| numRemovedFiles | 0 |
| numAddedFiles | 1 |
| numAddedBytes | 2,093 |
| numCopiedRows | **0** |
| numUpdatedRows | 1 |
| numDeletionVectorsAdded | 1 |
| numDeletionVectorsUpdated | **0** |

**Explanation:** V5 auto-compact already resolved V4's DV. The V5 output file has no prior DV — V6 adds a fresh one. That's why `numDeletionVectorsUpdated = 0`.

**Active after V6:** V5 output (with DV, 3 live rows) + V6 parquet (1 row: trip_id=1001)

---

## Version 7 — OPTIMIZE (auto-compaction)

Fires automatically after V6.

| Metric | Value |
| --- | --- |
| numRemovedFiles | 2 |
| numRemovedBytes | 4,279 (= 2,186 + 2,093) |
| numDeletionVectorsRemoved | 1 |
| numAddedFiles | 1 |
| numAddedBytes | 2,185 |

**Active after V7:** 1 single clean file (2,185 B)

---

## Version 8 — UPDATE trip_id=1004 (DV ON)

| Metric | Value |
| --- | --- |
| numRemovedFiles | 0 |
| numAddedFiles | 1 |
| numAddedBytes | 2,106 |
| numCopiedRows | **0** |
| numUpdatedRows | 1 |
| numDeletionVectorsAdded | 1 |
| numDeletionVectorsUpdated | 0 |

**Active after V8:** V7 output (with DV, 3 live rows) + V8 parquet (1 row: trip_id=1004)

---

## Version 9 — OPTIMIZE (auto-compaction)

Fires automatically after V8.

| Metric | Value |
| --- | --- |
| numRemovedFiles | 2 |
| numRemovedBytes | 4,291 (= 2,185 + 2,106) |
| numDeletionVectorsRemoved | 1 |
| numAddedFiles | 1 |
| numAddedBytes | 2,193 |

**Active after V9:** 1 single clean file (2,193 B) — all 4 rows, no DV

---

## Versions 10–11 — VACUUM (Step 4)

`VACUUM RETAIN 0 HOURS`

| Metric | Value |
| --- | --- |
| numFilesToDelete | **10** |
| sizeOfDataToDelete | **15,157 B** |
| numDeletedFiles | 10 |

**After:** Only 1 parquet remains (2,193 B). VACUUM removed 10 obsolete files (7 parquets + 3 DV bins).

**Key lesson:** VACUUM does NOT compact. It only garbage-collects files no longer referenced by the current table version.

---

## Version 12 — INSERT trip_id=1005 (Step 5)

| Metric | Value |
| --- | --- |
| numFiles | 1 |
| numOutputRows | 1 |
| numOutputBytes | 2,093 |

**After:** 2 active files on disk (V9 output + new insert)

---

## Version 13 — INSERT trip_id=1006 (Step 5)

| Metric | Value |
| --- | --- |
| numFiles | 1 |
| numOutputRows | 1 |
| numOutputBytes | 2,079 |

**After:** 3 active files on disk

| File | Size | Rows |
| --- | --- | --- |
| V9 compacted parquet | 2,193 B | 4 rows (1001-1004) |
| V12 insert parquet | 2,093 B | 1 row (trip_id=1005) |
| V13 insert parquet | 2,079 B | 1 row (trip_id=1006) |

**No DV involved** — INSERTs just create new files.

---

## Version 14 — OPTIMIZE (manual, Step 6)

| Metric | Value |
| --- | --- |
| numRemovedFiles | **3** |
| numRemovedBytes | **6,365** (= 2,193 + 2,093 + 2,079) |
| numDeletionVectorsRemoved | 0 |
| numAddedFiles | 1 |
| numAddedBytes | **2,254** |

**After:** 4 files on disk (3 obsolete + 1 new active)

| File | Size | Status |
| --- | --- | --- |
| V9 parquet | 2,193 B | OBSOLETE |
| V12 parquet | 2,093 B | OBSOLETE |
| V13 parquet | 2,079 B | OBSOLETE |
| V14 OPTIMIZE output | **2,254 B** | ACTIVE (all 6 rows) |

**Key lesson:** OPTIMIZE compacts live files into one — but the old files remain on disk until VACUUM.

---

## Versions 15–16 — VACUUM (Step 7)

`VACUUM RETAIN 0 HOURS`

| Metric | Value |
| --- | --- |
| numFilesToDelete | **3** |
| sizeOfDataToDelete | **6,365 B** |
| numDeletedFiles | 3 |

**After:** Only 1 parquet remains (2,254 B, all 6 rows). Clean final state.

---

## Why Two VACUUMs?

| VACUUM | What it removes |
| --- | --- |
| First (Step 4) | Debris from DV writes + auto-compaction (10 files) |
| Second (Step 7) | Debris from OPTIMIZE (3 files) |

Each VACUUM has **different files to remove**. The INSERTs (Step 5) create new small files that give OPTIMIZE real work to do, and OPTIMIZE leaves behind the files it replaced.

---

## Auto-Compaction Behavior

Auto-compaction after DV writes:
- Targets the file with the deletion vector + its associated fragments
- Does NOT guarantee all small files will be compacted
- Is non-deterministic — same code may produce different numbers of auto-compacts across runs
- Documentation states: "File compaction events don't have strict guarantees for resolving changes recorded in deletion vectors"

For guaranteed full compaction, use manual `OPTIMIZE`.

---

## Summary

| Step | Versions | What it proves |
| --- | --- | --- |
| 0 | V0–V1 | Baseline: 1 file, 4 rows |
| 1 | V2 | DV off: full rewrite, numCopiedRows=3 |
| 2 | V3–V4 (+V5 auto) | DV on: no rewrite, numCopiedRows=0 |
| 3 | V6–V8 (+V7,V9 auto) | Pattern repeats; auto-compact resolves each DV |
| 4 | V10–V11 | VACUUM removes 10 dead files, leaves 1 active |
| 5 | V12–V13 | INSERTs create small files (gives OPTIMIZE work) |
| 6 | V14 | OPTIMIZE merges 3 files into 1 — creates new dead files |
| 7 | V15–V16 | VACUUM removes OPTIMIZE's 3 dead files |

**Core takeaway:** Deletion vectors reduce rewrite work (numCopiedRows=0). Auto-compaction or OPTIMIZE consolidates file layout. VACUUM removes files no longer needed.
