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
# MAGIC - Chain reward and location rules into a reusable eligibility output
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
# MAGIC **Business question:** Operations wants to identify trips that qualify for
# MAGIC a card-tip reward. A trip qualifies when its payment method is **`"Card"`**
# MAGIC and its tip is at least **`$2.00`**. Some rows do not contain enough
# MAGIC information to evaluate both parts of the rule.
# MAGIC
# MAGIC The next result shows each comparison **before** combining them with **`&`**.

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
# MAGIC The previous result displayed all three possible outcomes. A filter treats
# MAGIC them differently: it keeps only rows whose condition is **`TRUE`**.

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
# MAGIC **Business question:** Which trips have a known payment method recorded?

# COMMAND ----------

df.filter(F.col("payment_method").isNotNull()).show()

# COMMAND ----------

# MAGIC %md
# MAGIC **Business question:** Which trips are missing a payment method?

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
# MAGIC Operations maintains a list of pickup zone IDs where trips are not
# MAGIC allowed. Filter with **`isin(...)`** and negate with **`~`** to keep
# MAGIC allowed trips.
# MAGIC
# MAGIC **Business question:** Which trips did **not** pick up in zones **74** or
# MAGIC **231**?
# MAGIC
# MAGIC Inspect **`pickup_location_id`** in the sample data before you filter.

# COMMAND ----------

df.show()

# COMMAND ----------

# MAGIC %md
# MAGIC **`isin(blocked)`** returns **`TRUE`** for a blocked location. The **`~`**
# MAGIC operator reverses the result, so the filter keeps locations that are not
# MAGIC blocked.

# COMMAND ----------

blocked = [74, 231]
df.filter(~F.col("pickup_location_id").isin(blocked)).show()

# COMMAND ----------

# MAGIC %md
# MAGIC **Business question:** Same rule — exclude zones **74** and **231** — but
# MAGIC the upstream blocklist accidentally includes a missing value (**`None`**).
# MAGIC Run the filter again. Why do you get no rows?
# MAGIC
# MAGIC PySpark treats Python **`None`** as **`NULL`** when it builds the
# MAGIC **`isin(...)`** condition.

# COMMAND ----------

blocked_with_null = [74, 231, None]
df.filter(~F.col("pickup_location_id").isin(blocked_with_null)).show()

# COMMAND ----------

# MAGIC %md
# MAGIC You expected trip **`1001`** (zone **`138`**) to pass, as it is not blocked.
# MAGIC However, the filter returns **no rows**. Walk through each trip using the
# MAGIC same three-valued logic as the reward example above.
# MAGIC
# MAGIC - Trip **`1002`** (zone **`74`**) and trip **`1003`** (zone **`231`**):
# MAGIC   **`isin(...)`** is **`TRUE`**, so **`~`** reverses it to **`FALSE`**. The
# MAGIC   filter drops them — as intended.
# MAGIC - Trip **`1001`** (zone **`138`**): **`138`** is not blocked, but
# MAGIC   **`isin(...)`** also compares **`138 == NULL`** because Python **`None`**
# MAGIC   in the list becomes **`NULL`**. That third comparison is **`NULL`**, not
# MAGIC   **`FALSE`**. **`FALSE OR FALSE OR NULL`** is **`NULL`**, and **`NOT NULL`**
# MAGIC   stays **`NULL`**. The filter drops trip **`1001`** even though zone
# MAGIC   **`138`** is allowed.
# MAGIC - Trip **`1004`** (missing **`pickup_location_id`**): comparisons against
# MAGIC   the list also produce **`NULL`**, so **`~`** still yields **`NULL`**.
# MAGIC
# MAGIC **Takeaway:** One **`NULL`** inside an **`isin`** list can break the negated
# MAGIC condition for every row that is not explicitly blocked. The filter keeps
# MAGIC only **`TRUE`**, so **`FALSE`** and **`NULL`** both disappear — and here,
# MAGIC no row reaches **`TRUE`**.

# COMMAND ----------

# MAGIC %md
# MAGIC **Business question:** Rebuild the blocklist without **`None`**, then decide
# MAGIC separately whether trips with a missing **`pickup_location_id`** should be
# MAGIC kept or dropped.
# MAGIC
# MAGIC The next filter keeps:
# MAGIC
# MAGIC - rows whose pickup location is **`NULL`**
# MAGIC - rows whose known pickup location is not blocked

# COMMAND ----------

safe_blocked = [zone_id for zone_id in blocked_with_null if zone_id is not None]

location_allowed = F.col("pickup_location_id").isNull() | (
    ~F.col("pickup_location_id").isin(safe_blocked)
)

df.filter(location_allowed).select("trip_id", "pickup_location_id").show()

# COMMAND ----------

# MAGIC %md
# MAGIC The **`isNull()`** condition keeps rows with an unknown pickup location.
# MAGIC For known locations, the negated **`isin(...)`** condition keeps only
# MAGIC locations that are not blocked.
# MAGIC
# MAGIC This pipeline chooses to **keep** unknown locations. If the pipeline
# MAGIC should **reject** them, leave out the **`isNull()`** condition.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Compare values that may be `NULL`: `eqNullSafe`
# MAGIC
# MAGIC The previous examples asked whether a value was **`NULL`** or appeared in a
# MAGIC list. Sometimes a pipeline must **compare** a value that may be **`NULL`**
# MAGIC and still receive a definite **`TRUE`** or **`FALSE`**.
# MAGIC
# MAGIC Normal equality returns **`NULL`** when either side is **`NULL`**.
# MAGIC **`eqNullSafe(...)`** (SQL **`<=>`**) handles **`NULL`** explicitly:
# MAGIC
# MAGIC - two **`NULL`** values are equal
# MAGIC - a **`NULL`** and a known value are not equal
# MAGIC - two known values use normal equality

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
# MAGIC ## Chain reward and pickup-location rules
# MAGIC
# MAGIC **Business question:** Which trips qualify for a card-tip reward **and** pass
# MAGIC the pickup-location rules when payment methods or locations may be
# MAGIC **`NULL`**?
# MAGIC
# MAGIC A trip must satisfy the reward condition **and** the location rule. Show
# MAGIC both intermediate decisions and the final eligibility for every trip.

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
# MAGIC Only trip **`1001`** is eligible: it is the sole row where both intermediate
# MAGIC conditions are **`TRUE`**. Trip **`1003`** shows why **`NULL`** results
# MAGIC matter — the reward condition is unknown, so the combined rule is not
# MAGIC **`TRUE`** even when the location is allowed.

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
# MAGIC   for downstream output
# MAGIC
# MAGIC Next up: **`02 - Missing, Blank, and Sentinel Values`** — how missing data
# MAGIC hides as blanks, sentinels, and **`NaN`**, and how to normalize before
# MAGIC **`na.drop`** / **`na.fill`**.
