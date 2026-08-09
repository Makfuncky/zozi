# Orders Module — Audit Remediation Note

**Date:** 2026-08-06
**Module:** `orders` (chosen from the audit's "All Findings by Domain")
**Approach:** "Safe + clear REDs" (consistent with the media-module rescue)
**Source of truth:** `SYSTEM_AUDIT_REPORT.md` §8 (Damage Hotlist) + §9 (read-only; audit scripts in `scripts/` not modified)

---

## 1. RED findings cleared (DBA06 — cross-schema FK)

The orders domain carried **12 RED `DBA06`** findings, every one a `ForeignKey` in
`backend/models/orders/orders.py` whose target lives in a *different* schema than the
declaring `commerce` table. Removed all 12 `ForeignKey(...)` constraints (integer ID
columns retained, indexed), keeping the ORM relationships alive via explicit
`primaryjoin=` so joins still work application-side:

- `Order.customer_id`  -> `core.users.id`
- `Order.user_id`      -> `core.users.id`
- `Order.invoice_id`   -> `finance.ar_invoices.id`
- `Order.country_code` -> `country.country_configs.code`
- `OrderLogisticsAllocation.supplier_id`   -> `core.users.id`
- `OrderLogisticsAllocation.shipment_id`  -> `logistics.shipments.id`
- `OrderLogisticsAllocation.partner_id`   -> `logistics.logistics_partners.id`
- `OrderLogisticsAllocation.service_area_id` -> `logistics.logistics_partner_service_areas.id`
- `OrderLogisticsAllocation.country_code` -> `country.country_configs.code`
- `ReturnRequest.customer_id` -> `core.users.id`
- `ReturnRequest.country_code` -> `country.country_configs.code`
- `OrderNotification.user_id` -> `core.users.id`

**Kept (same-schema, NOT cross-schema):** `order_id -> commerce.orders.id`,
`product_id -> commerce.products.id` (both inside the `commerce` schema).

**Relationship fix (required):** Because the FK columns are no longer DB FKs, each
cross-context `relationship(...)` (`Order.user`, `Order.customer`, `Order.country`,
`Order.invoice`, `OrderLogisticsAllocation.country`, `ReturnRequest.country`,
`OrderNotification.user`) now declares `primaryjoin=` so SQLAlchemy can resolve the join
without a DB constraint. The same latent issue existed in the **media** models
(non-FK columns referenced by `relationship(foreign_keys=...)`); those got the matching
`primaryjoin=` fix as well so the whole mapper registry configures cleanly.

**Verification:** `tests/test_orders_dba06_rescue.py` asserts (a) the orders models
configure, (b) zero cross-schema FKs remain in the orders tables, (c) the integer ID
columns are retained. `import main` now reports `cross_ecosystem: 0 FKs`
(`out/cross_schema_fk_analysis.json`).

---

## 2. Findings verified as FALSE POSITIVES (reported in detail, NOT changed)

The orders-domain yellow findings are the same classes as the media pass and were
sampled against current source:

### HL302 (swallowed exceptions)
- `services/orders/orders_router_service.py:82` — inside `_as_float()`: `except (TypeError, ValueError): return value`. This is a benign type-coercion fallback that returns the original value, not an error swallow. **False positive.**

### HL303 (broad `except Exception`)
- `controllers/orders/admin_orders_controller.py:388,446,462,477` and others — broad
  `except` blocks; sampled ones log with `logger.exception/warning` + context. Narrowing
  risks dropping legitimate errors; acceptable as-is.

### PERF4 (unbounded query)
- `services/orders/import_service.py:32,33` — `db.query(Account).all()` / `db.query(AccountGroup).all()` inside `_ensure_import_accounts`, a one-time seed that builds the *complete* chart-of-accounts set. Adding `.limit()` would truncate the set and be wrong. **False positive.**
- `services/orders/trading_service.py:489,578,608` — same `.all()` seeding/bootstrap
  pattern; bounded reference data.

---

## 3. Systemic / by-design / deferred findings (documented, NOT restructured under "Safe" scope)

- **CA2 / CIR2 / API101 / MV1 / DOM7** (`backref`-style router→service calls, missing
  `response_model`, empty `services/orders/` forwarders): platform-wide architectural
  patterns shared with the media module; restructuring risks breaking call sites.
- **DBA03 / DBA32** (missing `AuditMixin`/`SoftDeleteMixin`/`TenantMixin` columns such as
  `uuid`, `version`, `created_by`/`updated_by`): the orders models already define
  `created_at`/`updated_at`/`is_deleted`/`deleted_at` explicitly, so naively adding
  `AuditMixin`/`SoftDeleteMixin` would create **duplicate columns**. Consistent with the
  media precedent (mixin columns are a broader migration deliverable), this is deferred to
  the cleanup process.
- **HL601 / HL602** (missing timeouts / hardcoded values in controllers): enhancement
  opportunity; codebase-wide, deferred.
- **W4 / SYM1 / A2 / QUAL3 / FE3 / FEH*** etc.: cosmetic / naming / frontend-contract
  items, out of scope for the code-safe "clear REDs" pass.

---

## 4. Validation performed

- `models/orders/orders.py` imports and the SQLAlchemy mapper configures (relationships
  resolve via `primaryjoin`).
- `models/media/media_models.py` + `models/media/upload_job.py` re-validated (added
  `primaryjoin=` to keep the full registry configuring).
- `tests/test_orders.py` — **10 passed** (full app + DB integration).
- `tests/test_orders_dba06_rescue.py` — **3 passed** (no cross-schema FKs; columns kept;
  registry configures).
- `import main` builds the FastAPI app (1421 routes); `cross_ecosystem: 0 FKs`.

**Note:** As with media, a full Alembic-migration pass for the removed FK constraints is
the broader cleanup process's deliverable. In DEV SQLite (`create_all`, used by the test
suite and dev) the model-driven schema is internally consistent.
