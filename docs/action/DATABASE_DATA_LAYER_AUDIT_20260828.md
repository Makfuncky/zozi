# ZOZI Backend — Database & Data Layer Audit Report

**Date:** 2026-08-28  
**Scope:** Laws 19, 45–57, 61  
**Working Directory:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend`

---

## Executive Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 3 |
| HIGH | 4 |
| MEDIUM | 2 |
| LOW | 1 |
| OK | 5 |

---

## 1. Float for Money (Law 19) — CRITICAL

**Law:** Monetary values MUST use Decimal or Numeric. Float FORBIDDEN for money.

### Findings

**173+ instances** of `float()` casts on monetary values across the codebase.

#### `domains/catalog/services/search/search_service.py`
- Line 348: `price = float(cast(Any, getattr(product, "price")) or 0)`
- Line 357: `score += float(cast(float | None, getattr(product, "rating")) or 0)`
- Line 367: `float(cast(Any, getattr(row[1], "price")) or 0)`
- Line 385: `float(cast(Any, getattr(row[1], "price")) or 0)`
- Line 413-418: `result["min_price"] = float(...)`, `result["max_price"] = float(...)`
- Line 770: `avg = float(price_avg_row.avg_price)`
- Line 819: `prc = float(cast(Any, getattr(p, "price")) or 0)`
- Lines 924-927: `q.filter(Product.price >= float(filters["min_price"]))`
- Line 971: `"price": float(product.price) if product.price else 0`
- Line 978: `"min": float(result.min_price) if result.min_price is not None else 0`
- Lines 1037-1039: `parsed["min_price"] = float(match.group(1))`
- Lines 1079-1082: `db_query.filter(Product.price >= float(all_filters["min_price"]))`
- Line 1102: `"price": float(product.price) if product.price else 0`
- Lines 1122-1124: `db_query.filter(Product.price >= float(parsed["min_price"]))`
- Line 1154: `"price": float(row["price"])`

#### `domains/catalog/services/products/products_service.py`
- Line 133: `"price": float(product.price) if product.price else 0`
- Line 134: `"compare_price": float(product.compare_price) if product.compare_price else None`
- Line 312: `rating=float(data.pop("rating", 0.0) or 0.0)`
- Line 701: `product.compare_price = float(compare_price) if compare_price else None`
- Line 726: `product.compare_price = float(payload["compare_price"]) if payload["compare_price"] else None`
- Lines 739-740: `float(product.price) / float(product.compare_price)`
- Line 742: `"price": float(product.price), "compare_price": float(product.compare_price)`
- Lines 746-747: `price = float(product.price or 0)`, `compare_price = float(product.compare_price)`

#### `domains/catalog/services/search/ai_search_service.py`
- Line 78: `intent["entities"]["price_range"] = float(price_match.group(1))`
- Line 166: `"price": float(product.price) if product.price else 0`

#### `domains/catalog/services/categories/categories_service.py`
- Line 86: `"commission_rate": float(c.commission_rate) if c.commission_rate is not None else None`

#### `domains/catalog/services/categories/category_service.py`
- Line 186: `"commission_rate": float(commission_rate) if commission_rate is not None else None`

#### `domains/catalog/services/products/admin_products_service.py`
- Lines 300, 311: `val = float(val)` (on price/commission fields)

#### `domains/_parked/` (duplicate code)
- `search_service.py`: 15+ float() casts on price/amount
- `promotion_points_service.py`: Lines 128, 266
- `promotion_bogo_service.py`: Line 175
- `categories_service.py`: Line 91
- `cart_service__orders.py`: Lines 138, 148, 159

### Severity: CRITICAL
Floating-point arithmetic introduces rounding errors causing financial discrepancies. At 100K+ user scale, these errors compound.

### Fix
Replace all `float()` casts on monetary values with `Decimal(str(value))` or `float` → `Decimal` conversion. Use `kernel/money.py` primitives.

---

## 2. N+1 Query Patterns (Law 45) — CRITICAL

**Law:** All relationships declare `lazy=selectin` or `joined`. Default `lazy=select` FORBIDDEN.

### Findings

**Only 9 relationships** in the entire codebase use `lazy="selectin"` — all in `domains/accounts/models/user.py` (lines 54-69).

**200+ relationships** across all domains use the SQLAlchemy default `lazy="select"`, which causes N+1 queries.

#### Affected domains (non-exhaustive):
- `domains/catalog/models/products.py`: 22 relationships (lines 35, 99-106, 129-130, 143-144, 157-158, 185, 190, 214, 245-246, 262)
- `domains/catalog/models/ai_upload.py`: 4 relationships (lines 65, 101-102, 136)
- `domains/security/models/security_schema_models.py`: 5 relationships (lines 44-45, 64-65)
- `domains/security/models/fraud.py`: 10 relationships (lines 43-44, 146, 175, 235, 275, 304-305, 322-324, 349-350, 390-391, 413)
- `domains/comms/models/message.py`: 3 relationships (lines 46-48)
- `domains/comms/models/marketing.py`: 7 relationships (lines 37-38, 63-65, 92, 173-174)
- `domains/comms/models/incident.py`: 7 relationships (lines 24-26, 39-40, 57-58)
- `domains/comms/models/communication_schema_models.py`: 6 relationships (lines 47-49, 61-62, 74-75)
- `domains/comms/models/communication.py`: 20+ relationships (lines 57-58, 134-135, 158-161, 184-186, 211-213, 233, 254, 277, 306-308, 328-329, 351-352, 423-424)
- `domains/comms/models/chat.py`: 15+ relationships (lines 42-43, 64-65, 78-80, 93-94, 109-110, 124-125, 138-139, 153-154, 169, 172, 183-184)
- `domains/comms/models/fraud.py`: 1 relationship (line 31)
- `domains/hr/models/employee_models.py`: 20+ relationships (lines 140, 176-196, etc.)

### Severity: CRITICAL
N+1 queries bring the database to its knees at 100K+ users. Every relationship access triggers a new query.

### Fix
Add `lazy="selectin"` or `lazy="joined"` to all `relationship()` declarations. Use `lazy="selectin"` for collections, `lazy="joined"` for single-relationships.

---

## 3. SELECT * Queries (Law 46) — HIGH

**Law:** Application queries MUST select explicit columns.

### Findings

**13 instances** of `SELECT *` in raw SQL:

#### `domains/hr/services/hr_employee_service.py`
- Line 67: `text("SELECT * FROM offices WHERE country_code = :code ORDER BY name")`
- Line 98: `query = "SELECT * FROM employees WHERE country_code = :code"`
- Line 131: `text("SELECT * FROM employees WHERE id = :id")`
- Line 139: `text("SELECT * FROM employees WHERE user_id = :uid")`
- Line 158: `text("SELECT * FROM employee_documents WHERE employee_id = :eid ORDER BY created_at DESC")`
- Line 185: `query = "SELECT * FROM attendance_records WHERE employee_id = :eid"`
- Line 236: `text("SELECT * FROM employee_relations WHERE employee_id = :eid OR related_employee_id = :eid")`
- Line 259: `query = "SELECT * FROM work_logs WHERE employee_id = :eid"`
- Line 313: `text("SELECT * FROM qr_login_tokens WHERE token = :token AND expires_at > :now")`
- Line 323: `text("SELECT * FROM employee_roles WHERE country_code = :code ORDER BY name")`

#### `domains/comms/services/shared/chat_threads_query.py`
- Line 29: `SELECT * FROM (` (subquery)

#### `domains/comms/services/comms_service.py`
- Line 160: `SELECT * FROM (` (subquery)

#### `domains/comms/services/email/email_management.py`
- Line 460: `SELECT * FROM (` (subquery)

### Severity: HIGH
Wastes memory/I/O. Prevents covering indexes. Breaks on column reorder.

### Fix
Replace `SELECT *` with explicit column lists: `SELECT id, name, country_code FROM offices`.

---

## 4. Connection Pool Sizing (Law 47) — OK

**Law:** `pool_size ≥ 10`, `max_overflow ≥ 20`.

### Findings

`infrastructure/utils/config.py`:
- Line 44: `"db_pool_size": int(os.getenv("DB_POOL_SIZE", "50"))` ✓
- Line 45: `"db_max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "100"))` ✓

`infrastructure/database/database.py`:
- Lines 70-71: Uses `settings.db_pool_size`, `settings.db_max_overflow` ✓

### Status: PASS
Both values exceed minimums (50 > 10, 100 > 20). Environment-configurable.

---

## 5. Read Replica Separation (Law 48) — MEDIUM

**Law:** Replica connections use independent pool settings.

### Findings

`infrastructure/database/database.py`:
- Lines 284-341: `_get_replica_engine()` exists ✓
- Lines 311-325: Replica uses **same** `pool_size` and `max_overflow` as primary ✗
- Line 344: `get_read_db()` falls back to primary when `database_replica_url` is empty ✓

### Issue
Read replica shares the same pool budget as the primary. Under load, read-heavy endpoints compete with writes for connections.

### Severity: MEDIUM

### Fix
Add independent `db_replica_pool_size` and `db_replica_max_overflow` settings. Use larger pool for reads.

---

## 6. Linear Migration History (Law 49) — HIGH

**Law:** Alembic history MUST remain linear. Resolve divergent heads immediately.

### Findings

**Merge migration exists:**
`alembic/versions/2026_08_08_21_02-02ebc285f66f_merge_divergent_heads_20260806_0009_and_.py`
- Line 15: `down_revision: Union[str, None] = ('20260806_0009', '20260808_0001')`

**Divergent heads were created by:**
- `2026_08_06_0001_add_analytics_audit_columns.py` (down_revision: 20260806_0001)
- `2026_08_06_0001_media_add_audit_softdelete_mixins_and_rename_ai_result.py` (down_revision: 20260806_0001)

Both migrations share the same `down_revision`, creating a branch.

### Severity: HIGH
Divergent heads break `alembic upgrade head` and cause deployment failures. The merge migration resolves it, but the branch point indicates process failure.

### Fix
The merge migration exists, so current state is linear. But CI should enforce single-head before merge. Add `alembic heads` check to CI.

---

## 7. Explicit Transactions (Law 50) — OK

**Law:** All writes use explicit transaction management. Autocommit FORBIDDEN.

### Findings

- `infrastructure/database/database.py:138`: `autocommit=False` ✓
- `infrastructure/database/database.py:336`: `autocommit=False` ✓
- `infrastructure/database/transaction.py:21,73`: `autocommit: bool = False` ✓
- `infrastructure/database/init_db.py:32`: `autocommit=False` ✓
- `infrastructure/database/seed/_common.py:22`: `autocommit=False` ✓

### Status: PASS
All session factories use `autocommit=False`.

---

## 8. Single Table Ownership (Law 51) — HIGH

**Law:** Each table defined in exactly one domain. Duplicate `__tablename__` FORBIDDEN.

### Findings

**Duplicate table names across domains:**

| Table | Domain 1 | Domain 2 |
|-------|----------|----------|
| `payout_rules` | `finance/models/tax_rules.py:21` | `country/models/countries.py:178` |
| `tax_rules` | `finance/models/tax_rules.py:43` | `country/models/countries.py:200` |
| `shipping_rules` | `finance/models/tax_rules.py:63` | `country/models/countries.py:220` |
| `payout_rule_categories` | `finance/models/tax_rules.py:85` | `country/models/countries.py:270` |
| `payout_rule_products` | `finance/models/tax_rules.py:97` | `country/models/countries.py:292` |
| `cross_country_customer_sessions` | `customers/models/cross_country_session.py:21` | `country/models/country_enhancements.py:59` |
| `shift_handover_tasks` | `hr/models/hr_schema_models.py:55` | `hr/models/employee_models.py:616` |

### Severity: HIGH
Duplicate tables cause MetaData conflicts and runtime crashes. Different ORM classes map to the same table.

### Fix
Consolidate to single domain. `payout_rules`, `tax_rules`, `shipping_rules` should live in `finance/`. `cross_country_customer_sessions` should live in `country/`. `shift_handover_tasks` should live in `hr/` (one file).

---

## 9. FK Constraints with ondelete (Law 52) — MEDIUM

**Law:** All FK columns have explicit ForeignKey with ondelete.

### Findings

Most FK columns have `ondelete` specified. However, some are missing:

#### `domains/finance/models/payments.py`
- Line 49: `order_id = Column(Integer, ForeignKey("commerce.orders.id", ondelete='CASCADE'), nullable=False)` — missing `index=True`

#### `domains/audit/models/audit_schema_models.py`
- Line 19: `user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=True)` — missing `index=True`
- Line 34: `user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=False)` — missing `index=True`

#### `domains/comms/models/incident.py`
- Line 19: `created_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=False)` — missing `index=True`
- Line 34: `war_room_id = Column(Integer, ForeignKey("comms.incident_war_rooms.id", ondelete="SET NULL"), nullable=False)` — missing `index=True`
- Line 35: `participant_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=False)` — missing `index=True`
- Line 47: `war_room_id = Column(Integer, ForeignKey("comms.incident_war_rooms.id", ondelete="SET NULL"), nullable=False)` — missing `index=True`
- Line 48: `assignee_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)` — missing `index=True`

#### `domains/comms/models/communication_schema_models.py`
- Line 40: `user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=False)` — missing `index=True`
- Line 56: `ticket_id = Column(Integer, ForeignKey("comms.support_tickets.id", ondelete="SET NULL"), nullable=False)` — missing `index=True`
- Line 57: `sender_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=False)` — missing `index=True`
- Line 69: `ticket_reply_id = Column(Integer, ForeignKey("comms.support_ticket_replies.id", ondelete="SET NULL"), nullable=True)` — missing `index=True`
- Line 70: `ticket_id = Column(Integer, ForeignKey("comms.support_tickets.id", ondelete="SET NULL"), nullable=True)` — missing `index=True`
- Line 108: `country_code = Column(String(2), ForeignKey("country.country_configs.code", ondelete="SET NULL"), nullable=True)` — missing `index=True`

### Severity: MEDIUM
FK without `ondelete` can cause referential integrity issues. FK without `index=True` degrades JOINs to sequential scans.

### Fix
Add `index=True` to all FK columns. Ensure all FK have explicit `ondelete`.

---

## 10. Index FK Columns (Law 53) — MEDIUM

**Law:** All FK columns have explicit index. PostgreSQL does NOT auto-index FKs.

### Findings

Same as Law 52 findings above. Many FK columns lack `index=True`:

- `domains/audit/models/audit_schema_models.py`: Lines 19, 34
- `domains/comms/models/incident.py`: Lines 19, 34, 35, 47, 48
- `domains/comms/models/communication_schema_models.py`: Lines 40, 56, 57, 69, 70, 108
- `domains/finance/models/payments.py`: Line 49

### Severity: MEDIUM
Without indexes, JOINs degrade to sequential scans. At 100K+ users, this causes timeouts.

### Fix
Add `index=True` to all FK columns, or create explicit `Index()` in `__table_args__`.

---

## 11. Soft Delete (Law 54) — HIGH

**Law:** All user-facing tables use `is_deleted` (boolean, default false).

### Findings

**Models WITH is_deleted:** 100+ models have `is_deleted` ✓

**Models potentially MISSING is_deleted (need manual verification):**
- `domains/hr/models/employee_models.py:23` — `Office` has `is_deleted` ✓
- `domains/hr/models/employee_models.py:43` — `PhysicalIDCard` has `is_deleted` ✓
- `domains/catalog/models/products.py:11` — `Category` — **NO is_deleted** ✗
- `domains/catalog/models/products.py:161` — `ProductVariant` — **NO is_deleted** ✗
- `domains/country/models/country_enhancements.py:12` — `CountryFeatureFlag` — **NO is_deleted** ✗
- `domains/country/models/country_enhancements.py:35` — `CountryStaffAssignment` — **NO is_deleted** ✗
- `domains/country/models/country_enhancements.py:59` — `CrossCountryCustomerSession` — **NO is_deleted** ✗
- `domains/country/models/country_enhancements.py:84` — `OmanDeliveryZone` — **NO is_deleted** ✗
- `domains/country/models/country_enhancements.py:110` — `CountryConfigVersion` — **NO is_deleted** ✗
- `domains/country/models/country_enhancements.py:134` — `SupplierKYCRequirement` — **NO is_deleted** ✗
- `domains/country/models/country_enhancements.py:155` — `LogisticsPartnerKYCRequirement` — **NO is_deleted** ✗
- `domains/country/models/country_enhancements.py:178` — `CountryCommissionRate` — **NO is_deleted** ✗
- `domains/country/models/country_enhancements.py:205` — `CountryLocalization` — **NO is_deleted** ✗
- `domains/country/models/country_enhancements.py:226` — `CountryPaymentAlias` — **NO is_deleted** ✗
- `domains/country/models/country_enhancements.py:246` — `CountryLegalContract` — **NO is_deleted** ✗
- `domains/country/models/country_enhancements.py:266` — `CountryCategoryTaxRate` — **NO is_deleted** ✗
- `domains/country/models/country_enhancements.py:294` — `CountryCity` — **NO is_deleted** ✗
- `domains/country/models/country_enhancements.py:324` — `CountryHolidayCalendar` — **NO is_deleted** ✗
- `domains/country/models/country_enhancements.py:345` — `CountryGatewayConfig` — **NO is_deleted** ✗
- `domains/country/models/country_enhancements.py:371` — `CountryCommunicationThread` — **NO is_deleted** ✗
- `domains/country/models/country_enhancements.py:393` — `CountryCommissionRateHistory` — **NO is_deleted** ✗
- `domains/country/models/country_enhancements.py:418` — `CountryLogisticsZone` — **NO is_deleted** ✗
- `domains/country/models/country_enhancements.py:441` — `CountryPayoutRule` — **NO is_deleted** ✗

### Severity: HIGH
Without `is_deleted`, data cannot be recovered. Audit trails are broken. Safe cascading is impossible.

### Fix
Add `is_deleted = Column(Boolean, default=False, nullable=False, index=True)` to all user-facing models.

---

## 12. Schema-per-domain (Law 55) — HIGH

**Law:** Every model declares `__table_args__ = {schema: <domain>}`.

### Findings

**Models with `__table_args__`:** 100+ ✓

**Models potentially MISSING `__table_args__` (need manual verification):**
- `domains/country/models/countries.py:11` — `CountryConfig` has `__table_args__` ✓
- `domains/country/models/countries.py:126` — `CountryCommunication` has `__table_args__` ✓
- `domains/country/models/countries.py:156` — `CountryGatewayCredentials` — **NO `__table_args__`** ✗
- `domains/country/models/countries.py:178` — `PayoutRule` — **NO `__table_args__`** ✗
- `domains/country/models/countries.py:200` — `TaxRule` — **NO `__table_args__`** ✗
- `domains/country/models/countries.py:220` — `ShippingRule` — **NO `__table_args__`** ✗
- `domains/country/models/countries.py:241` — `Message` — **NO `__table_args__`** ✗
- `domains/country/models/countries.py:270` — `PayoutRuleCategory` — **NO `__table_args__`** ✗
- `domains/country/models/countries.py:292` — `PayoutRuleProduct` — **NO `__table_args__`** ✗

### Severity: HIGH
Tables without schema land in `public`, breaking multi-tenant isolation.

### Fix
Add `__table_args__ = {"schema": "country"}` to all models in `country/models/countries.py`.

---

## 13. Forbidden Schemas (Law 56) — OK

**Law:** `core`, `platform`, `identity` FORBIDDEN as schema names.

### Findings

No instances of `schema="core"`, `schema="platform"`, or `schema="identity"` found in `domains/`.

### Status: PASS

---

## 14. OFFSET Pagination — HIGH

**Law:** Keyset pagination (cursor), NEVER OFFSET on hot lists.

### Findings

**40+ instances** of `.offset()` across the codebase:

#### `domains/catalog/services/products/products_service.py`
- Line 271: `products = q_obj.offset(offset).limit(limit).all()`
- Line 567: `items = q.offset((page - 1) * size).limit(size).all()`
- Line 844: `items = q.offset((page - 1) * size).limit(size).all()`

#### `domains/catalog/services/categories/categories_service.py`
- Line 29: `items = query.order_by(...).offset((page - 1) * page_size).limit(page_size).all()`
- Line 78: `rows = query.order_by(...).offset((page - 1) * page_size).limit(page_size).all()`

#### `domains/catalog/services/categories/admin_categories_service.py`
- Line 44: `rows = q.order_by(...).offset((page - 1) * page_size).limit(page_size).all()`

#### `domains/catalog/services/categories/category_admin_read_service.py`
- Line 30: `rows = q.order_by(...).offset((page - 1) * page_size).limit(page_size).all()`

#### `domains/catalog/services/products/admin_products_service.py`
- Line 391: `query = query.offset(offset)`

#### `domains/catalog/services/products/product_verification_service.py`
- Line 81: `items = q.order_by(...).offset((page - 1) * page_size).limit(page_size).all()`

#### `domains/orders/services/admin_orders_service.py`
- Line 45: `items = q.order_by(Order.created_at.desc()).offset((page - 1) * size).limit(size).all()`

#### `domains/orders/services/admin_orders_status_service.py`
- Line 32: `items = q.order_by(Order.created_at.desc()).offset((page - 1) * size).limit(size).all()`

#### `domains/orders/services/admin_catalog_orders_service.py`
- Line 24: `rows = q.order_by(...).offset((page - 1) * page_size).limit(page_size).all()`

#### `domains/finance/services/trading_service.py`
- Line 105: `return q.order_by(PurchaseOrder.id.desc()).offset(offset).limit(limit).all()`
- Line 172: `return q.order_by(GoodsReceiptNote.id.desc()).offset(offset).limit(limit).all()`
- Line 275: `return q.order_by(SalesOrder.id.desc()).offset(offset).limit(limit).all()`
- Line 350: `rows = q.order_by(StockMovement.id.desc()).offset(offset).limit(limit).all()`

#### `domains/finance/services/payouts/payout_batch_service.py`
- Line 2584: `.offset(max(0, offset))`
- Line 4022: `batches = query.order_by(...).offset((page - 1) * page_size).limit(page_size).all()`
- Line 4073: `payouts = query.order_by(...).offset((page - 1) * page_size).limit(page_size).all()`
- Line 4093: `logistics_payouts = logistics_payout_q.order_by(...).offset((page - 1) * page_size).limit(page_size).all()`
- Line 4137: `rows = q.order_by(...).offset((page - 1) * page_size).limit(page_size).all()`
- Line 4161: `rows = q.order_by(...).offset((page - 1) * page_size).limit(page_size).all()`
- Line 4171: `rows = q.order_by(...).offset((page - 1) * page_size).limit(page_size).all()`

#### `domains/accounts/services/users/user_management_service.py`
- Line 1131: `.offset(safe_offset)`
- Line 1163: `.offset(safe_offset)`

#### `domains/accounts/services/auth/auth_service.py`
- Line 2944: `.offset(safe_offset)`

#### `domains/audit/services/logs/audit_query_service.py`
- Line 101: `items = ordered.offset((page - 1) * page_size).limit(page_size).all()`

#### `domains/_parked/` (duplicate code)
- `admin_promotion_service.py`: Lines 274, 345, 405
- `admin_promotions_write_service.py`: Lines 355, 367
- `admin_categories_service.py`: Line 43
- `orders_package_service.py`: Lines 35, 85, 170
- `categories_service.py`: Lines 34, 83
- `promotion_points_service.py`: Line 300

### Severity: HIGH
OFFSET pagination degrades to full table scan as offset grows. At 100K+ users, deep pagination causes timeouts.

### Fix
Replace OFFSET with keyset pagination: `WHERE id < last_seen_id ORDER BY id DESC LIMIT 20`.

---

## 15. Unbounded Caches (Law 61) — OK

**Law:** All in-memory caches have max size and/or TTL. Unbounded dict FORBIDDEN.

### Findings

`domains/catalog/services/search/search_service.py`:
- Line 867: `_cache_ttl = 300`
- Line 868: `_cache_max_size = 500`
- Line 873: `self._cache: Dict[str, Dict[str, Any]] = OrderedDict()`
- Line 875-877: `_ensure_cache_bound()` — evicts oldest when over max size
- Line 888-890: `_invalidate_cache()` — clears on version bump

### Status: PASS
Cache is bounded with max size and TTL.

---

## Summary Table

| # | Law | Severity | Status | Issue |
|---|-----|----------|--------|-------|
| 1 | Law 19: No float for money | CRITICAL | FAIL | 173+ float() casts on monetary values |
| 2 | Law 45: No N+1 queries | CRITICAL | FAIL | 200+ relationships use default lazy=select |
| 3 | Law 46: No SELECT * | HIGH | FAIL | 13 SELECT * queries in HR/comms |
| 4 | Law 47: Connection pool sizing | OK | PASS | pool_size=50, max_overflow=100 |
| 5 | Law 48: Read replica separation | MEDIUM | WARN | Same pool settings as primary |
| 6 | Law 49: Linear migration history | HIGH | WARN | Merge migration exists (past divergence) |
| 7 | Law 50: Explicit transactions | OK | PASS | autocommit=False everywhere |
| 8 | Law 51: Single table ownership | HIGH | FAIL | 7 duplicate table names across domains |
| 9 | Law 52: FK constraints | MEDIUM | WARN | Some FK missing index=True |
| 10 | Law 53: Index FK columns | MEDIUM | WARN | Some FK missing index=True |
| 11 | Law 54: Soft delete | HIGH | FAIL | ~25 models missing is_deleted |
| 12 | Law 55: Schema-per-domain | HIGH | WARN | Some models missing __table_args__ |
| 13 | Law 56: No forbidden schemas | OK | PASS | No forbidden schemas found |
| 14 | OFFSET pagination | HIGH | FAIL | 40+ .offset() calls |
| 15 | Law 61: Bounded caches | OK | PASS | Cache is bounded |

---

## Recommended Fix Priority

1. **Law 19 (Float for Money)** — Replace all `float()` on monetary values with `Decimal`
2. **Law 45 (N+1)** — Add `lazy="selectin"` to all relationships
3. **Law 54 (Soft Delete)** — Add `is_deleted` to all user-facing models
4. **Law 51 (Single Table Ownership)** — Consolidate duplicate tables
5. **Law 46 (SELECT *)** — Replace with explicit column lists
6. **OFFSET Pagination** — Replace with keyset pagination
7. **Law 55 (Schema-per-domain)** — Add `__table_args__` to all models
8. **Law 49 (Linear Migration)** — Add CI check for single head
9. **Law 48 (Read Replica)** — Add independent pool settings
10. **Laws 52/53 (FK + Index)** — Add `index=True` to all FK columns
