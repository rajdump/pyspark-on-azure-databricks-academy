# Notebook 02 Revision Plan

Target:
[`02 - Multi-column Keys, NULL Groups, and Filter Placement.py`](02%20-%20Multi-column%20Keys,%20NULL%20Groups,%20and%20Filter%20Placement.py)

## Goal

Make the notebook follow one clear learning sequence:

1. Ask whether distinct values and grouped keys produce the same count.
2. Prove and interpret the NULL-key difference.
3. Apply the established key counts to a composite `groupBy`.
4. Compare filtering rows before aggregation with filtering groups afterward.
5. Practise both patterns in the exercise.

The introduction, worked examples, exercise, and summary must present these
ideas in the same order.

## Teaching boundaries

- Notebook 01 owns aggregate-value behavior: `sum` and `avg` skip NULL values,
  and an all-NULL measure produces a NULL aggregate.
- Notebook 02 owns group-key behavior: a NULL key is retained as one output
  group, even though `countDistinct` ignores NULL.
- Trip 104 provides the valid-key/NULL-value contrast: `payment_method="card"`
  and `base_fare_amount=NULL`.
- Trip 105 demonstrates a sentinel string: `payment_method="unknown"`.
- Trip 106 demonstrates the NULL group key: both `payment_method` and
  `base_fare_amount` are NULL because no payment row exists.
- Notebook 02 will reference Notebook 01's value-NULL lesson rather than
  re-teaching its handmade all-NULL-group example.
- Catalyst optimizer behavior stays out of this introductory notebook.

## Cell-by-cell implementation

### Cell 1 — Introduction

- Replace “Few” with a direct motivation based on two choices: grouping keys
  and filter placement.
- Remove the duplicated numbered explanation above the existing table.
- Make the preview table an exact content contract:
  - profile single keys and compare distinct values with grouped keys;
  - build the composite `service_type`/`payment_method` key and observe 18
    combinations;
  - filter rows before aggregation;
  - filter aggregated groups afterward.
- Do not reveal the 5-versus-6 result here; the learner will establish it in
  Section 1.
- Remove the `sum`/`avg` NULL-skipping row because that belongs to Notebook 01.
- Use “aggregated values,” not “accumulated values.”
- Keep the reads, prerequisites, and no-write statement.

### Cell 2 — Setup explanation

- Keep the short reference to Notebook 01 and
  `docs/data/dataset-overview.md`.
- Keep only the keys and measures used in this notebook.
- Do not repeat the schema or inherited NULL map.

### Cell 3 — Load `trip_enriched`

- Keep the `F` import, managed-table read, and 106-row check unchanged.

### Cell 4 — Section 1 prediction prompt

- Keep one numbered section: `## 1. Composite keys and the NULL group`.
- Add a `###` subsection prompt asking whether:
  - `countDistinct("payment_method")`, and
  - the number of rows from `groupBy("payment_method")`
  will agree.
- Ask the learner to predict before running.
- Do not answer or explain the difference in this cell.

### Cell 5 — Prove 5 distinct values versus 6 groups

- Combine the directly related evidence in one focused code cell:
  - show `countDistinct("service_type")` and
    `countDistinct("payment_method")`;
  - count the output rows from `groupBy("payment_method")`;
  - display all payment groups with `trip_count`.
- Expected evidence:
  - five non-NULL payment values;
  - six payment groups;
  - `card` 59, `wallet` 20, `cash` 17, `corporate` 8, `unknown` 1,
    and NULL 1.

### Cell 6 — Inspect trips 104–106

- Add one small code cell:

```python
trip_enriched.filter(F.col("trip_id").isin(104, 105, 106)).select(
    "trip_id",
    "payment_method",
    "base_fare_amount",
).orderBy("trip_id").show()
```

- This cell supplies row-level evidence for NULL value, sentinel string, and
  NULL key without creating a separate conceptual sidebar.

### Cell 7 — Interpret, then establish the composite bound

- Interpret the preceding outputs only after the evidence:
  - `countDistinct` ignores the NULL payment key;
  - `groupBy` keeps that key as one group;
  - trip 104 remains in the `card` group despite its NULL fare;
  - trip 105's `unknown` is the lowercase payment equivalent of Notebook 01's
    uppercase `UNKNOWN` sentinel;
  - trip 106 has no payment row and therefore has a NULL payment key.
- Explicitly distinguish trip 104's NULL measure from trip 106's NULL key.
- Transition to the composite business question:
  - 5 service groups;
  - 6 payment groups;
  - at most `5 * 6 = 30` possible pairs.
- Ask how many pairs are actually present before running the next cell.
- Remove the current redundant standalone “Rule” paragraph.

### Cell 8 — Apply the composite key

- Run the existing:

```python
groupBy("service_type", "payment_method")
```

- Keep `trip_count` and rounded `total_base_fare`.
- Report 18 observed groups out of the upper bound of 30.
- Keep the conclusion inside this code cell through a concise comment or output
  label: Spark returns only key combinations present in the data.
- Do not add a standalone Markdown cell for that one-sentence explanation.

### Cell 9 — Section 2 explanation

- Keep `## 2. WHERE vs HAVING with the same .filter()`.
- Preserve the concrete comparison:
  - no filter: 5 groups, Manhattan total 134.45;
  - row filter before aggregation: 4 groups, Manhattan total 91.00;
  - group filter after aggregation: 2 groups, Manhattan total 134.45.
- Keep the mechanism:
  - before `groupBy` removes input rows and changes aggregate values;
  - after `agg` removes complete groups while retained totals remain unchanged.
- Keep the DataFrame API note that there is no `.having()` method.
- Keep the beginner-safe performance habit: filter as early as the business
  question allows.
- Do not mention Catalyst or physical-plan filter movement.

### Cells 10–12 — Filter-placement demonstrations

- Cell 10: build and display the unfiltered `borough_tips` baseline.
- Cell 11: apply `tip_amount > 5` before `groupBy` and display changed totals.
- Cell 12: apply `total_tip > 90` after `agg` and display surviving groups.
- Keep these as three separate query shapes so the learner can compare them
  incrementally.

### Cell 13 — Exercise instructions

- Preserve the four existing tasks:
  1. predict the number of borough groups;
  2. build the per-borough summary;
  3. apply `HAVING` with `trip_count > 10`;
  4. add `payment_method` as a second key.
- Keep the published per-borough answer values.
- Ensure the wording points back to the matching worked example:
  group-count verification, aggregate construction, post-aggregate filtering,
  and composite grain.

### Cells 14–16 — Exercise code

- Cell 14: prediction plus per-borough aggregate.
- Cell 15: post-aggregate filter for boroughs with more than 10 trips.
- Cell 16: composite `pickup_borough`/`payment_method` prediction and aggregate.
- Do not fill learner TODOs.

### Cell 17 — Summary

- Recap in notebook order:
  1. NULL keys affect grouped row counts;
  2. sentinel strings are not NULL;
  3. composite groups represent observed key combinations;
  4. filtering before aggregation removes rows and changes values;
  5. filtering after aggregation removes groups.
- Keep the pointer to Notebook 03.

## Cross-file findings

- [`README.md`](README.md) already assigns the correct topics to Notebook 02:
  composite grain, NULL group versus `countDistinct`, sentinel versus NULL,
  filter placement, and the existing exercise.
- [`docs/data/dataset-overview.md`](../docs/data/dataset-overview.md) already
  agrees with the notebook facts and requires no edit.
- No changes are planned for Notebook 01, `COURSE_MODULES.md`, or
  `docs/validation/`.

## Verified facts

The repository source data confirms:

- `trip_enriched`: 106 rows.
- `service_type`: 5 grouped values.
- `payment_method`: 5 non-NULL distinct values and 6 grouped keys.
- Composite (`service_type`, `payment_method`): 18 observed groups.
- Composite (`pickup_borough`, `payment_method`): 18 observed groups.
- Trip 104: `card` with NULL `base_fare_amount`.
- Trip 105: `unknown` with `base_fare_amount=12.00`.
- Trip 106: NULL `payment_method` and NULL `base_fare_amount`.
- Existing borough totals and exercise answer values are consistent with the
  source data.

## Verification after implementation

1. Confirm all Databricks source cell markers remain valid.
2. Confirm Cell 1 previews every topic demonstrated later and no extra topic.
3. Confirm Section 1 follows ask → prove → inspect → interpret → apply.
4. Confirm Section 2 retains the three verified query shapes.
5. Confirm the exercise uses only patterns demonstrated earlier.
6. Run `ruff format` and `ruff check` on the target notebook.
7. Check editor diagnostics for the edited file.
8. Leave Spark and Unity Catalog runtime validation for Azure Databricks.
