# FALSE POSITIVE AUDIT — ZOZI Forensic Report

## 1. Claim-by-Claim Verification

| # | Claim | Audit Value | Your Value | Verdict |
|---|-------|-------------|------------|---------|
| 1 | 340 SQLAlchemy models | 340 | 340 | AGREE |
| 2 | only 2 tables without explicit `__table_args__` schema | 2 | 2 (`payroll_records`, `employee_trainings` in `domains/hr/models/employee_models.py`) | AGREE |
| 3 | 376 `relationship()` calls, 294 omit `lazy=` (78%) | 376 / 294 | 376 / 294 | AGREE |
| 4 | 871 unindexed hot columns | 871 | 871 reported; **647 false positives** (have `index=True`); real unindexed = **224** | DISAGREE |
| 5 | 0 monetary columns typed `Float` | 0 | 0 | AGREE |
| 6a | 22 tables missing `created_at`+`updated_at` | 22 | 22 | AGREE |
| 6b | 4 missing soft delete (`is_deleted`) | 4 | 4 | AGREE |
| 6c | 178 missing `version` | 178 | 178 | NOISE — see §2 |
| 6d | 57 missing `country_code` | 57 | 57 | AGREE |
| 7 | migrations reference `commerce` (1 ref) and `customer` (5 refs) | 1 / 5 | 1 / 5 | AGREE (but see §3) |

---

## 2. Detailed Findings

### Claim 1 — Model count (340)
**Verdict: AGREE.**  
All 340 classes with `__tablename__` inherit from SQLAlchemy `Base`/`Model`/`Mixin`. The 3 non-model classes in `models/` dirs (`MfaFactorType(str)`, two `GUID(TypeDecorator)`) lack `__tablename__` and are excluded. Delta: **0**. Biggest false-positive class: **none**.

### Claim 3 — `lazy=` on relationships (294/376)
**Verdict: AGREE.**  
`backend/infrastructure/database/base.py` is:
```python
class Base(DeclarativeBase):
    pass
```
No default `lazy` is set. SQLAlchemy's implicit default is `lazy="select"`, which Law 45 forbids. The 78% figure is accurate, and the severity is correctly stated. If the base had set `lazy="raise"`, the severity would drop; it does not.

### Claim 4 — 871 unindexed hot columns
**Verdict: DISAGREE — massive false positive.**  
The scanner in `zz_scanners/s20_db_advisor.py` extracts index names from `__table_args__` using:
```python
re.findall(r'["\']([a-z_]+_idx|[a-z_]+_pkey|ix_[a-z0-9_]+|idx_[a-z0-9_]+)', src)
```
It then checks if the hot column name appears in that list. **A column declared `Column(..., index=True)` IS indexed by SQLAlchemy**, but it produces no literal `Index(...)` object in `__table_args__`, so the regex never sees its auto-generated `ix_<col>` name.

Of the 871 reported unindexed hot-column pairs:
- **647 have `index=True`** on the column → FALSE POSITIVES
- **224 are truly unindexed** → real defect

False positive rate: **74%**.

**Biggest false-positive tables:** `accounts.supplier_bank_accounts` (country_code, supplier_id, is_deleted), `accounts.addresses` (country_code, user_id), `accounts.carts` (country_code, user_id).

### Claim 6c — 178 missing `version`
**Verdict: NOISE — not a defect per architecture rules.**  
`ARCHITECTURE_STACK.md` Law 23 states:
> "Every model MUST include `created_at`, `updated_at`, `country_code`, `is_deleted`."

There is **no law requiring `version` on every table**. The `version` column was introduced by migration `2026_08_31_0003_add_version_columns.py` as an optimization for high-contention tables, not as a universal schema law. The 178 count is mechanically correct but architecturally meaningless and should not appear as a defect.

### Claim 7 — Migration schema drift (`commerce`, `customer`)
**Verdict: AGREE (scanner counts are correct), but these are legacy artifacts.**  
The scanner counts references inside specific list variables (`COMPOSITE_INDEXES`, `SINGLE_COUNTRY_INDEXES`) in migration files:
- `commerce`: 1 ref in `2026_08_31_0004_add_composite_indexes.py` line 24 — `("commerce", "products", ...)`
- `customer`: 5 refs in `2026_09_03_0006_add_performance_indexes.py` lines 46–50 — `("customer", "addresses")`, `("customer", "wishlist_items")`, etc.

The ORM declares these tables under `catalog` and `customers` (plural) respectively. The split was performed by migration `20260821_split_commerce_schema` (Aug 21) and `20260821_customer_comm_logistics_media` (Aug 21). The referencing migrations are dated Aug 31 and Sep 03 — **after** the split. These are **legacy artifacts that would fail on a fresh DB** because `commerce.products` and `customer.addresses` no longer exist post-split. They are not live tables; they are stale references in already-applied migration code.

---

## FALSE POSITIVES TO FIX

1. **Hot-column index detector** — Rule: "a column is unindexed if its name does not appear as a literal index-name string in `__table_args__`."  
   **Corrected rule:** A column is unindexed only if it lacks both `Column(..., index=True)` AND an explicit `Index(...)` declaration in `__table_args__`. The current detector ignores `index=True` entirely, causing a 74% false-positive rate.

2. **Missing-version detector** — Rule: "every table must have `version`."  
   **Corrected rule:** `version` is not mandated by `ARCHITECTURE_STACK.md` Law 23. Remove `version` from the universal defect list; report it only as a recommendation for high-contention tables, not a blocker.

---

## RECOMMENDED ACTION

Fix the hot-column detector in `zz_scanners/s20_db_advisor.py` to treat `index=True` on the column definition as a valid index declaration, and downgrade `version` from a P1 blocker to a recommendation because no architecture law requires it on every table.
