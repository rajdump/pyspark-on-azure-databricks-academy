# Databricks notebook source
# MAGIC %md
# MAGIC # NULL Semantics and Predicate Correctness
# MAGIC
# MAGIC **Learning objectives.** After this notebook, you will be able to:
# MAGIC - Explain three-valued logic and show `TRUE`, `FALSE`, and `NULL` as
# MAGIC   intermediate condition columns
# MAGIC - Explain why `filter` / `where` keep only rows whose condition is `TRUE`
# MAGIC - Use `isNull` / `isNotNull` for definite answers when a column value may
# MAGIC   be missing
# MAGIC - Build NULL-safe predicates with `isNull` / `isNotNull`, the `isin` +
# MAGIC   Python `None` trap, and `eqNullSafe` / `<=>`
# MAGIC - Chain reward and blocklist rules into a reusable eligibility output
# MAGIC
# MAGIC **Prerequisites.** Module 2 — especially `05 - Filtering Rows` and
# MAGIC `06 - Querying DataFrames with SQL`. You should already know `F.col`,
# MAGIC `filter` / `where`, Column `&` / `|` / `~`, intro `isNull` /
# MAGIC `isNotNull`, and why `== None` does not find NULLs.
# MAGIC
# MAGIC **Setup.** Attach any compute with PySpark available. This notebook uses
# MAGIC a small, hand-built rideshare-style DataFrame aligned with `trip` and
# MAGIC `payment` column names from the course dataset.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup DataFrame for NULL semantics examples
# MAGIC
# MAGIC Module 2 introduced intro NULL checks in **`05 - Filtering Rows`**. This
# MAGIC notebook goes deeper: how **`NULL`** behaves in comparisons, why filters
# MAGIC silently drop **`NULL`** results, and how to write predicates that stay
# MAGIC correct when values are missing.
# MAGIC
# MAGIC Create one small DataFrame with deliberate missing values in
# MAGIC **`payment_method`**, **`tip_amount`**, and **`pickup_location_id`**:

# COMMAND ----------

from pyspark.sql import functions as F

rows = [
    (1001, "Card", 3.50, 138),
    (1002, "Cash", None, 74),
    (1003, None, 2.00, 231),
    (1004, "Card", 1.00, None),
]

schema_ddl = "trip_id bigint, payment_method string, tip_amount double, pickup_location_id int"

df = spark.createDataFrame(rows, schema_ddl)  # pyright: ignore[reportUndefinedVariable]  # noqa: F821

# COMMAND ----------

# MAGIC %md
# MAGIC Confirm the sample rows before building conditions — the same habit as
# MAGIC inspection in Module 2.

# COMMAND ----------

df.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Understand three-valued logic
# MAGIC
# MAGIC **Business question:** Operations needs trips that qualify for a card-tip
# MAGIC reward.
# MAGIC
# MAGIC Qualifying rule: payment method is **`"Card"`** and tip is at least
# MAGIC **`$2.00`**. The next result shows each comparison **before** combining them
# MAGIC with **`&`**.

# COMMAND ----------

is_card = F.col("payment_method") == "Card"
tip_at_least_2 = F.col("tip_amount") >= 2.00
qualifies_for_reward = is_card & tip_at_least_2

df.select(
    "trip_id",
    "payment_method",
    "tip_amount",
    is_card.alias("is_card"),
    tip_at_least_2.alias("tip_at_least_2"),
    qualifies_for_reward.alias("qualifies_for_reward"),
).show()

# COMMAND ----------

# MAGIC %md
# MAGIC The result depends on what Spark knows about each trip:
# MAGIC
# MAGIC - Trip **`1001`**: `TRUE AND TRUE` produces **`TRUE`**.
# MAGIC - Trip **`1002`**: `FALSE AND NULL` produces **`FALSE`**. Its payment
# MAGIC   method already disqualifies it.
# MAGIC - Trip **`1003`**: `NULL AND TRUE` produces **`NULL`**. Its payment
# MAGIC   method is **`NULL`**, so Spark cannot produce a definite answer.
# MAGIC - Trip **`1004`**: `TRUE AND FALSE` produces **`FALSE`**.
# MAGIC
# MAGIC Spark follows SQL's **three-valued logic**. A condition can produce
# MAGIC **`TRUE`**, **`FALSE`**, or **`NULL`**. In a condition result, **`NULL`**
# MAGIC means Spark cannot determine whether the answer is true or false.
# MAGIC
# MAGIC The same rule applies to other boolean operators. **`TRUE OR NULL`**
# MAGIC becomes **`TRUE`**, while **`FALSE OR NULL`** remains **`NULL`**.
# MAGIC **`NOT NULL`** also remains **`NULL`**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## See what a filter keeps
# MAGIC
# MAGIC **Business question:** Operations needs only the qualifying trips from that
# MAGIC rule.
# MAGIC
# MAGIC A filter keeps only rows whose condition is **`TRUE`** — not **`FALSE`**
# MAGIC or **`NULL`**.

# COMMAND ----------

df.filter(qualifies_for_reward).show()

# COMMAND ----------

# MAGIC %md
# MAGIC Only trip **`1001`** remains. Trips **`1002`** and **`1004`** produced
# MAGIC **`FALSE`**, while trip **`1003`** produced **`NULL`**. The filter removes
# MAGIC all three because it keeps only **`TRUE`**.
# MAGIC
# MAGIC When rows containing **`NULL`** require separate handling, test for
# MAGIC **`NULL`** explicitly instead of relying on a normal comparison alone.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Use `isNull` and `isNotNull` for definite answers
# MAGIC
# MAGIC Module 2 showed that comparing a column with Python **`None`** does not find
# MAGIC **`NULL`** values — use **`isNull()`** / **`isNotNull()`** when the
# MAGIC requirement mentions missing values. Here, apply that pattern after seeing
# MAGIC why comparisons can produce **`NULL`** in the first place.
# MAGIC
# MAGIC **Business question:** A payment audit needs trips with a recorded payment
# MAGIC method.

# COMMAND ----------

df.filter(F.col("payment_method").isNotNull()).show()

# COMMAND ----------

# MAGIC %md
# MAGIC **Business question:** A payment audit needs trips with no payment method on
# MAGIC file.

# COMMAND ----------

df.filter(F.col("payment_method").isNull()).show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Handle `None` in an `isin` list
# MAGIC
# MAGIC **`isNull()`** and **`isNotNull()`** check whether a **column value** is
# MAGIC **`NULL`**. A **`NULL`** can also enter a condition through a Python list
# MAGIC passed to **`isin(...)`**.
# MAGIC
# MAGIC **Business question:** Compliance needs trips not picked up in blocked zones
# MAGIC **74** or **231**.
# MAGIC
# MAGIC Blocklist filter: **`~F.col("pickup_location_id").isin(blocked)`** — **`~`**
# MAGIC applies **`NOT`** to the **`isin(...)`** condition result. Inspect
# MAGIC **`pickup_location_id`** before you filter.

# COMMAND ----------

df.show()

# COMMAND ----------

# MAGIC %md
# MAGIC **`isin(blocked)`** is **`TRUE`** when **`pickup_location_id`** is on the
# MAGIC blocklist. **`~isin(...)`** keeps rows where that result is **`FALSE`**
# MAGIC (zones **74** and **231** drop out).

# COMMAND ----------

blocked = [74, 231]
df.filter(~F.col("pickup_location_id").isin(blocked)).show()

# COMMAND ----------

# MAGIC %md
# MAGIC **Business question:** Compliance needs trips not picked up in blocked zones
# MAGIC **74** or **231**.
# MAGIC
# MAGIC The upstream blocklist includes Python **`None`**. Run the same filter — why
# MAGIC no rows? PySpark treats Python **`None`** as **`NULL`** in the
# MAGIC **`isin(...)`** condition.

# COMMAND ----------

blocked_with_null = [74, 231, None]
df.filter(~F.col("pickup_location_id").isin(blocked_with_null)).show()

# COMMAND ----------

# MAGIC %md
# MAGIC Zone **`138`** is not on the blocklist, but the filter returns **no rows**.
# MAGIC
# MAGIC **`isin(...)`** compares the column to **each** list value and **`OR`s** the
# MAGIC results. For zone **`138`**: **`138 == 74`** is **`FALSE`**, **`138 == 231`**
# MAGIC is **`FALSE`**, and **`138 == NULL`** is **`NULL`** — Python **`None`** in
# MAGIC the list becomes **`NULL`**. So **`isin(...)`** is **`FALSE OR FALSE OR
# MAGIC NULL`**, which is **`NULL`**.
# MAGIC
# MAGIC **`~`** applies **`NOT`**. **`NOT NULL`** is still **`NULL`**, not **`TRUE`**,
# MAGIC so the filter drops the row. Blocked zones get **`FALSE`** as intended; every
# MAGIC other row gets **`NULL`**, not **`TRUE`**.

# COMMAND ----------

# MAGIC %md
# MAGIC **Business question:** Compliance needs trips not picked up in zones **74**
# MAGIC or **231**, and trips whose pickup zone is unknown.
# MAGIC
# MAGIC Strip **`None`** from the blocklist first. The filter below keeps:
# MAGIC
# MAGIC - trips whose **`pickup_location_id`** is **`NULL`**
# MAGIC - trips whose **`pickup_location_id`** is known and not **74** or **231**

# COMMAND ----------

safe_blocked = [zone_id for zone_id in blocked_with_null if zone_id is not None]

location_allowed = F.col("pickup_location_id").isNull() | (
    ~F.col("pickup_location_id").isin(safe_blocked)
)

df.filter(location_allowed).select("trip_id", "pickup_location_id").show()

# COMMAND ----------

# MAGIC %md
# MAGIC The **`isNull()`** branch covers unknown pickup zones. For known zones,
# MAGIC **`~isin(safe_blocked)`** excludes **74** and **231**.
# MAGIC
# MAGIC To **drop** trips with unknown pickup zones instead, remove the
# MAGIC **`isNull()`** branch.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Compare values that may be `NULL`: `eqNullSafe`
# MAGIC
# MAGIC **`isNull()`** tests whether a value is missing. **`eqNullSafe(...)`**
# MAGIC (SQL **`<=>`**) **compares** two values and always returns **`TRUE`** or
# MAGIC **`FALSE`** — even when either side is **`NULL`**.
# MAGIC
# MAGIC **Business question:** A matching report needs payment-method comparisons
# MAGIC that never return **`NULL`**.
# MAGIC
# MAGIC Normal **`==`** returns **`NULL`** when either side is **`NULL`**.
# MAGIC **`eqNullSafe(...)`** rules:
# MAGIC
# MAGIC - two **`NULL`** values → **`TRUE`**
# MAGIC - **`NULL`** vs a known value → **`FALSE`**
# MAGIC - two known values → same as **`==`**

# COMMAND ----------

df.select(
    "trip_id",
    "payment_method",
    (F.col("payment_method") == "Card").alias("plain_eq"),
    F.col("payment_method").eqNullSafe("Card").alias("null_safe_vs_card"),
    F.col("payment_method").eqNullSafe(None).alias("null_safe_vs_null"),
).show()

# COMMAND ----------

# MAGIC %md
# MAGIC For trip **`1003`**, **`payment_method`** is **`NULL`**:
# MAGIC
# MAGIC - normal equality with **`"Card"`** returns **`NULL`**
# MAGIC - **`eqNullSafe("Card")`** returns **`FALSE`**
# MAGIC - **`eqNullSafe(None)`** returns **`TRUE`**
# MAGIC
# MAGIC Use **`isNull()`** to check whether a column value is **`NULL`**. Use
# MAGIC **`eqNullSafe(...)`** to compare values that may be **`NULL`** when the
# MAGIC result must always be **`TRUE`** or **`FALSE`**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Chain reward and pickup-zone rules
# MAGIC
# MAGIC **Business question:** Operations needs a per-trip report with three columns:
# MAGIC reward rule pass/fail, blocklist rule pass/fail, and final pass/fail.
# MAGIC
# MAGIC Reward rule: **`"Card"`** and tip ≥ **`$2.00`**. Blocklist rule: not zones
# MAGIC **74** or **231**, or unknown pickup zone (same as **`location_allowed`**
# MAGIC above).

# COMMAND ----------

reward_decisions = df.select(
    "trip_id",
    "payment_method",
    "tip_amount",
    "pickup_location_id",
    qualifies_for_reward.alias("qualifies_for_reward"),
    location_allowed.alias("location_allowed"),
    (qualifies_for_reward & location_allowed).alias("eligible_for_reward"),
)
reward_decisions.show()

# COMMAND ----------

# MAGIC %md
# MAGIC Only trip **`1001`** has **`eligible_for_reward`** **`TRUE`**. Trip **`1003`**
# MAGIC shows the trap: **`qualifies_for_reward`** is **`NULL`**, so
# MAGIC **`qualifies_for_reward & location_allowed`** is not **`TRUE`** even though
# MAGIC **`location_allowed`** is **`TRUE`**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercise
# MAGIC
# MAGIC Use a second small rideshare-style DataFrame named **`exercise_df`** and
# MAGIC complete:
# MAGIC
# MAGIC 1. Create **`exercise_df`** with **`trip_id`**, **`service_type`**, and
# MAGIC    **`dropoff_location_id`** (aligned with the `trip` table). Include at
# MAGIC    least one **`NULL`** **`service_type`** and one **`NULL`**
# MAGIC    **`dropoff_location_id`**.
# MAGIC 2. Define a reusable condition **`is_premium`** — **`service_type`** equals
# MAGIC    **`"Premium"`** (observe **`NULL`** in the intermediate column for missing
# MAGIC    service types).
# MAGIC 3. Build a blocklist **`restricted_zones`** that accidentally includes Python
# MAGIC    **`None`**, then derive **`safe_restricted`** without **`None`**.
# MAGIC 4. Define **`zone_ok`** — keep rows whose **`dropoff_location_id`** is
# MAGIC    **`NULL`** **or** not in **`safe_restricted`** (same pattern as
# MAGIC    **`location_allowed`** above).
# MAGIC 5. Filter to rows where **`is_premium & zone_ok`** is **`TRUE`** and show
# MAGIC    the result.
# MAGIC
# MAGIC Keep the DataFrame tiny (four or five rows).

# COMMAND ----------

# Your code here.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC Recap this notebook's NULL predicate path:
# MAGIC
# MAGIC - **Three-valued logic** — conditions can produce **`TRUE`**, **`FALSE`**,
# MAGIC   or **`NULL`**; show intermediate columns before filtering
# MAGIC - **Filters keep only `TRUE`** — **`FALSE`** and **`NULL`** rows drop out
# MAGIC - **`isNull()` / `isNotNull()`** — definite answers when a column value may
# MAGIC   be missing (Module 2 intro; applied here after 3VL)
# MAGIC - **`isin` + Python `None`** — strip **`None`** from lists; decide separately
# MAGIC   how to treat **`NULL`** column values
# MAGIC - **`eqNullSafe` / `<=>`** — comparisons that must always return
# MAGIC   **`TRUE`** or **`FALSE`**
# MAGIC - **Eligibility chain** — name intermediate predicates; combine with **`&`**
# MAGIC   for a final pass/fail column
# MAGIC
# MAGIC Next up: **`02 - Missing, Blank, and Sentinel Values`** — how missing data
# MAGIC hides as blanks, sentinels, and **`NaN`**, and how to normalize before
# MAGIC **`na.drop`** / **`na.fill`**.
