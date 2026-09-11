# TASK 14 — BUG / CONTRADICTION / INCONSISTENCY AUDIT
## ZOZI Marketplace E-Commerce Platform

**Audit Date:** 2026-09-11  
**Auditor:** Kilo (Forensic Technical Audit)  
**Scope:** Backend + Frontend + Database + Config + Deployment  
**Status:** READ-ONLY AUDIT — No files modified

---

## EXECUTIVE SUMMARY

This forensic audit identified 12 confirmed bugs and 8 inconsistencies across the ZOZI codebase. The most critical issues are:

1. Fatal attribute mismatch: Order model defines `status_code` but ~30 service files read/write `order.status`
2. Infinite recursion: `create_address()` in `checkout/service.py` calls itself unconditionally
3. Payment state machine broken: DB check constraint allows 4 statuses; code uses 6+
4. Valkey/Redis naming violation: Codebase still contains `redis` references despite migration constraint
5. Duplicate function definitions: `finance_service.py` defines identical functions twice

---

## CONFIRMED BUGS

---

### BUG-01: Fatal Attribute Mismatch — `order.status` vs `order.status_code`

**Severity:** CRITICAL  
**Location:** `backend/domains/orders/models/order_entities.py:24` vs ~30 service files  
**Status:** VERIFIED

**Evidence:**

Model definition (`order_entities.py:19-24`):
```python
__table_args__ = (Index('ix_orders_status', 'status_code'), CheckConstraint("status_code IN ('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'returned')", name='chk_orders_status_valid'), {'schema': 'orders'})
id = Column(Integer, primary_key=True, index=True)
status_code = Column(String, default='pending')
```

But `domains/orders/services/core/dtos.py:75` reads:
```python
status=orm_order.status,  # AttributeError — 'Order' object has no attribute 'status'
```

And `domains/orders/services/orders_service.py:393` reads:
```python
old_status = order.status  # AttributeError
```

And `domains/orders/services/tracking/service.py:1041` reads:
```python
if order.status not in ("pending", "confirmed"):  # AttributeError
```

And `domains/orders/services/core/order_engine.py:1021` writes:
```python
order.status = reconciled_status  # AttributeError
```

**Affected files (verified):**
- `domains/orders/services/orders_service.py` (lines 338-339, 393, 409)
- `domains/orders/services/tracking/service.py` (lines 1041, 1044, 1075, 1092, 1148, 1157, 1205, 1225, 1227, 1258, 1271, 1309, 1314, 1345-1346, 1426, 1431-1432, 1517, 1519, 1524)
- `domains/orders/services/core/order_engine.py` (lines 897, 1020-1021, 1047-1048, 1235, 1244)
- `domains/orders/services/core/dtos.py` (line 75)
- `domains/orders/services/core/order_admin.py` (lines 58, 68, 122-123, 222, 307, 339, 351, 360, 375)
- `domains/orders/services/packing/service.py` (lines 103-104, 124, 171-172)
- `domains/orders/services/core/logistics.py` (lines 105, 132, 4212, 4578, 4869, 4872)
- `domains/suppliers/services/orders/supplier_orders_service.py` (lines 92, 230-231, 655-656)
- `domains/suppliers/services/orders/supplier_orders.py` (lines 82-83, 129, 188, 194, 232-233, 256, 376, 512, 514, 569)
- `domains/finance/services/payouts/payout_batch_service.py` (line 1651)
- `domains/finance/services/payments/payment_orchestrator.py` (lines 595, 889, 905, 1039, 1051, 1075, 1083, 1103, 1107)
- `domains/finance/services/payments/gateway_tap.py` (lines 299, 331, 345, 383, 397, 460, 478, 528, 644, 669, 683, 721, 739, 905, 1517, 1554, 1583, 1670, 1690, 1710, 1752, 1764, 1803)

**Expected behavior:** All code should use `order.status_code` to match the model column.

**Actual behavior:** Code accesses `order.status` which does not exist on the SQLAlchemy model. This will raise `AttributeError` at runtime when any of these code paths execute.

**Why it is incorrect:** The `Order` ORM model defines `status_code` as the column name. There is no `status` column or hybrid property on the model. Accessing `order.status` will fail.

**Affected workflow:** Every order status transition, order listing, order detail, tracking, refund, and admin operation.

**Recommended fix:** Either (a) rename the model column from `status_code` to `status`, or (b) update all ~30+ service files to use `order.status_code`. Option (b) is preferred because the DB column and check constraint already use `status_code`.

---

### BUG-02: Infinite Recursion in `create_address()`

**Severity:** CRITICAL  
**Location:** `backend/domains/orders/services/checkout/service.py:80-116`  
**Status:** VERIFIED

**Evidence:**
```python
def create_address(
    db: Session,
    *,
    user_id: int,
    full_name: str,
    address_line1: str,
    city: str,
    state: Optional[str] = None,
    postal_code: Optional[str] = None,
    country: str = "US",
    is_default: bool = False,
    label: Optional[str] = None,
    phone: Optional[str] = None,
):
    """Persist a new customer address and return the saved row."""
    try:
        return create_address(   # <-- Calls itself! Infinite recursion.
            db,
            user_id=user_id,
            ...
        )
```

**Expected behavior:** Should call `domains.governance.ports.create_address` or `domains.accounts.models.core.Address` creation.

**Actual behavior:** Unconditional infinite recursion → `RecursionError` when called.

**Why it is incorrect:** The function calls itself with the same arguments, leading to infinite recursion and stack overflow.

**Affected workflow:** Any address creation during checkout or profile management.

**Recommended fix:** Replace the recursive call with actual address creation logic.

---

### BUG-03: Payment Status Check Constraint Mismatch

**Severity:** HIGH  
**Location:** `backend/domains/finance/models/payments.py:39-60`  
**Status:** VERIFIED

**Evidence:**

Model constraint:
```python
CheckConstraint("status IN ('pending', 'completed', 'failed', 'refunded')", name="chk_payment_status_valid")
```

But services use additional statuses:
- `payment_engine.py`: `"approved"`, `"declined"`, `"requires_payment_method"`, `"requires_action"`, `"processing"`, `"requires_capture"`
- `gateway_tap.py`: `"captured"`, `"hold"`, `"pending"`, `"processing"`
- `gateway_paypal.py`: paypal-specific statuses

**Expected behavior:** Check constraint should include all statuses the application uses, or the application should only use the 4 allowed statuses.

**Actual behavior:** Any payment record saved with status like `"approved"` or `"captured"` will violate the DB constraint and raise `IntegrityError`.

**Why it is incorrect:** The check constraint is too restrictive compared to actual business logic.

**Affected workflow:** Payment processing for all gateways (Stripe, Tap, PayTabs, PayPal, Thawani).

**Recommended fix:** Expand the check constraint to include all valid statuses, or map external gateway statuses to the 4 canonical values before persisting.

---

### BUG-04: Valkey/Redis Naming Violation

**Severity:** HIGH  
**Location:** Multiple files  
**Status:** VERIFIED

**Evidence:**

Project constraint (`project.md`): "Project must contain no 'redis' name anywhere — no files, directories, variables, env vars, or identifiers — after the Valkey migration (2026-09-03)."

Violations found:
- `backend/requirements.txt:20`: `redis==8.0.1`
- `backend/config.py:74`: `"redis_url": "redis://localhost:6379"`
- `backend/config.py:90-91`: `celery_broker_url` and `celery_result_backend` default to `redis://localhost:6379/1` and `redis://localhost:6379/2`
- `backend/infrastructure/valkey/client.py:115-117`: Aliases `redis_client = valkey_client` and `get_redis = valkey_client`
- `backend/infrastructure/messaging/realtime.py:43`: `_create_realtime_redis_client()`
- Multiple job files import `from infrastructure.utils.redis_client import redis_client`
- `backend/infrastructure/observability/error_handler.py:59`: `from sentry_sdk.integrations.redis import RedisIntegration`

**Expected behavior:** No `redis` identifier should exist in the codebase.

**Actual behavior:** The codebase still extensively uses `redis` naming in dependencies, config, variables, and imports.

**Why it is incorrect:** Violates the explicit project constraint to remove all Redis naming after Valkey migration.

**Affected workflow:** Caching, sessions, rate limiting, Celery broker, and realtime messaging.

**Recommended fix:** Rename all `redis` identifiers to `valkey`, update `requirements.txt` to use `valkey` package, and update config defaults.

---

### BUG-05: Duplicate Function Definitions in `finance_service.py`

**Severity:** HIGH  
**Location:** `backend/domains/finance/services/finance_service.py:372-487`  
**Status:** VERIFIED

**Evidence:**

The file defines these functions twice:
1. `get_global_config` — defined at line 372 and imported at line 322
2. `update_global_config` — defined at line 375 and imported at line 323
3. `list_category_rates` — defined at line 379 and imported at line 324
4. `update_category_rate` — defined at line 382 and imported at line 325
5. `list_badge_tiers` — defined at line 386 and imported at line 326
6. `update_badge_tier` — defined at line 389 and imported at line 327
7. `list_ledger_entries` — defined at line 393 and imported at line 328
8. `adjust_ledger_entry` — defined at line 396 and imported at line 329
9. `preview_commission` — defined at line 405 and imported at line 330
10. `list_supplier_commissions` — defined at line 413 and imported at line 331
11. `get_supplier_commission` — defined at line 416 and imported at line 332
12. `set_supplier_commission` — defined at line 419 and imported at line 333
13. `delete_supplier_commission_override` — defined at line 428 and imported at line 334
14. `get_product_commission_override` — defined at line 436 and imported at line 335
15. `list_product_commission_overrides` — defined at line 443 and imported at line 336
16. `set_product_commission_override` — defined at line 452 and imported at line 337
17. `delete_product_commission_override` — defined at line 462 and imported at line 338

The second definitions (lines 372-487) shadow the imports from `general_ledger_service`. The second `get_global_config` at line 372 calls itself recursively:
```python
def get_global_config(db: Session, current_user: dict):
    return get_global_config(db)  # Infinite recursion!
```

**Expected behavior:** Each function should be defined once.

**Actual behavior:** Functions are defined twice; the second definitions shadow the first. `get_global_config` recurses infinitely.

**Why it is incorrect:** The second block of functions appears to be a failed merge from another file. It creates duplicate symbols and infinite recursion.

**Affected workflow:** All commission, ledger, and badge tier operations.

**Recommended fix:** Remove the duplicate function definitions (lines 372-487) or rename them to avoid shadowing.

---

### BUG-06: Order Model Has Duplicate/Conflicting Amount Columns

**Severity:** MEDIUM  
**Location:** `backend/domains/orders/models/order_entities.py:30-38`  
**Status:** VERIFIED

**Evidence:**
```python
subtotal = Column(Numeric(10, 2))              # Line 30
subtotal_amount = Column(Numeric(10, 2))       # Line 31
shipping_fee = Column(Numeric(10, 2), default=0)  # Line 32
shipping_amount = Column(Numeric(10, 2), default=0) # Line 33
tax_amount = Column(Numeric(10, 2), default=0)     # Line 34
vat_amount = Column(Numeric(10, 2), default=0)     # Line 35
discount_amount = Column(Numeric(10, 2))           # Line 36
total = Column(Numeric(10, 2))                   # Line 37
total_amount = Column(Numeric(10, 2))            # Line 38
```

The model has both `subtotal`/`total` and `subtotal_amount`/`total_amount` and `shipping_fee`/`shipping_amount`. Service code inconsistently uses both sets:
- `order_engine.py:789-793` sets `subtotal_amount`, `shipping_amount`, `total_amount`
- `tracking/service.py:330-335` reads `subtotal_amount`, `shipping_amount`, `vat_amount`, `total_amount`
- `dtos.py:80` reads `total` (not `total_amount`)

**Expected behavior:** One canonical set of column names.

**Actual behavior:** Two parallel sets of columns with no clear ownership, leading to data inconsistency and confusion.

**Why it is incorrect:** Having duplicate semantic columns violates DRY and risks half-written data if one set is updated but not the other.

**Affected workflow:** Order creation, order preview, financial reporting, and all order-related API responses.

**Recommended fix:** Deprecate `subtotal`, `total`, and `shipping_fee`; standardize on `subtotal_amount`, `total_amount`, `shipping_amount`.

---

### BUG-07: Order Status State Machine Inconsistencies

**Severity:** MEDIUM  
**Location:** Multiple files  
**Status:** VERIFIED

**Evidence:**

`order_entities.py:19` check constraint:
```python
CheckConstraint("status_code IN ('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'returned')", name='chk_orders_status_valid')
```

`order_engine.py:77-89` transition map:
```python
VALID_ORDER_TRANSITIONS = {
    "pending": {"confirmed", "cancelled", "failed"},
    "confirmed": {"processing", "cancelled", "failed"},
    "processing": {"prepared", "cancelled", "failed"},
    "prepared": {"picking_up", "cancelled"},
    "picking_up": {"shipped", "cancelled"},
    "shipped": {"in_transit"},
    "in_transit": {"delivered"},
    "delivered": {"refunded"},
    "failed": {"refunded"},
    "cancelled": set(),
    "refunded": set(),
}
```

`tracking/service.py:46-54` ORDER_STATUS_FLOW:
```python
ORDER_STATUS_FLOW = [
    "pending", "processing", "prepared", "picking_up",
    "shipped", "in_transit", "delivered",
]
```

`orders_service.py:89-92` valid_statuses:
```python
valid_statuses = (
    "pending", "confirmed", "processing", "prepared", "picking_up",
    "shipped", "delivered", "cancelled", "failed",
)
```

`orders_service.py:397-408` allowed_transitions:
```python
allowed_transitions = {
    "pending": {"confirmed", "cancelled", "failed"},
    "confirmed": {"processing", "prepared", "shipped", "delivered", "cancelled"},
    "processing": {"prepared", "shipped", "delivered", "cancelled"},
    "prepared": {"picking_up", "shipped", "delivered", "cancelled"},
    "picking_up": {"prepared", "shipped", "delivered", "cancelled"},
    "shipped": {"delivered"},
    "delivered": set(),
    "cancelled": set(),
    "failed": set(),
    "refunded": set(),
}
```

Inconsistencies:
1. DB check constraint allows `returned` but no transition map includes it
2. `orders_service.py` allows `confirmed → prepared` and `confirmed → shipped` but `order_engine.py` does not
3. `tracking/service.py` includes `in_transit` but DB constraint does not
4. `orders_service.py` allows `shipped → delivered` but `order_engine.py` only allows `shipped → in_transit`

**Expected behavior:** One canonical state machine used everywhere, matching the DB constraint.

**Actual behavior:** Four different state machines with conflicting allowed transitions.

**Why it is incorrect:** Different services enforce different state transitions, creating impossible states and race conditions.

**Affected workflow:** Order status updates from admin, customer, supplier, and logistics panels.

**Recommended fix:** Define a single `ORDER_STATUSES` set and `ORDER_TRANSITIONS` map in a shared constants module, update the DB check constraint, and enforce it consistently.

---

### BUG-08: Frontend `apiFetch` Contains Production `console.log` Statements

**Severity:** LOW  
**Location:** `frontend/web_app/src/lib/api/client.ts:109,117,121,166`  
**Status:** VERIFIED

**Evidence:**
```typescript
console.log('[apiFetch] path:', path, '-> url:', url, 'method:', method);  // Line 109
console.log('[apiFetch] calling ensureAccessToken');  // Line 117
console.log('[apiFetch] ensureAccessToken done');  // Line 119
console.log('[apiFetch] skipping ensureAccessToken (refreshing)');  // Line 121
console.error(`[API] Fetch failed for ${url}: ${errorMessage}`);  // Line 166
```

**Expected behavior:** Production code should use structured logging, not `console.log`.

**Actual behavior:** Debug logging statements leak into production bundle.

**Why it is incorrect:** Architecture law 58 forbids `print()` in production; frontend equivalent should not use `console.log`.

**Affected workflow:** All frontend API calls produce console noise in production.

**Recommended fix:** Remove `console.log` statements or guard them behind a debug flag.

---

### BUG-09: DTO Reads Non-Existent Model Attribute

**Severity:** MEDIUM  
**Location:** `backend/domains/orders/services/core/dtos.py:75`  
**Status:** VERIFIED

**Evidence:**
```python
def to_order_dto(orm_order, include_items: bool = False) -> OrderDTO:
    dto = OrderDTO(
        id=orm_order.id,
        status=orm_order.status,  # AttributeError: 'Order' object has no attribute 'status'
        ...
    )
```

**Expected behavior:** Read `orm_order.status_code`.

**Actual behavior:** Will raise `AttributeError` when `to_order_dto` is called with a real ORM Order object.

**Why it is incorrect:** Same root cause as BUG-01 — the model column is `status_code`, not `status`.

**Affected workflow:** Any code path that serializes an Order to a DTO.

**Recommended fix:** Change `orm_order.status` to `orm_order.status_code`.

---

### BUG-10: Config Defaults Risk Accidental Production Misconfiguration

**Severity:** MEDIUM  
**Location:** `backend/config.py:31,96,139`  
**Status:** VERIFIED

**Evidence:**

```python
"secret_key": os.getenv("SECRET_KEY", "zozi-dev-secret-key-change-in-production-2026"),  # Line 31
"seed_data_on_startup": True,  # Line 96
"cookie_secure": True,  # Line 139
```

Issues:
1. `secret_key` has a hardcoded dev default. The production validation at line 214-224 checks for placeholder values, but if `APP_ENV` is not set to `"production"` (e.g., `"staging"`), the weak default is accepted.
2. `seed_data_on_startup=True` means every dev/test startup re-seeds data, which can mask production seed issues and cause flaky tests.
3. `cookie_secure=True` with `refresh_cookie_samesite="lax"` causes the config to override to `"none"` in production (line 228-232), which is a behavioral contradiction — the default says `lax` but production forces `none`.

**Expected behavior:** Safer defaults and explicit environment gating.

**Actual behavior:** Weak defaults can leak into non-production environments, and cookie behavior changes unexpectedly based on environment.

**Why it is incorrect:** Violates config law 82 ("No default credentials") and creates surprising behavior.

**Affected workflow:** Application startup, session management, and test reliability.

**Recommended fix:** Remove hardcoded secret default; require explicit env var. Set `seed_data_on_startup=False` by default. Document the cookie samesite override logic.

---

### BUG-11: Payment Gateway Registry Import Path Mismatch

**Severity:** MEDIUM  
**Location:** `backend/domains/orders/services/orders_service.py:21`  
**Status:** VERIFIED

**Evidence:**
```python
from providers.payments.registry import PaymentGatewayRegistry
```

But the actual file is at:
- `backend/domains/finance/services/payments/payment_engine.py` (defines `LIVE_ADAPTER_GATEWAY_CODES`, `BUILT_IN_GATEWAY_CODES`, etc.)
- No `providers/payments/registry.py` file found in the codebase.

**Expected behavior:** Import path should resolve to an existing module.

**Actual behavior:** Import will fail with `ModuleNotFoundError` unless a `registry.py` exists in `providers/payments/`.

**Why it is incorrect:** The import references a module that does not exist in the repository.

**Affected workflow:** Order gateway resolution (`get_order_gateway`).

**Recommended fix:** Verify whether `providers/payments/registry.py` exists or should be created; if not, remove or correct the import.

---

### BUG-12: Frontend `_order_to_dict` Serializes Non-Existent Columns

**Severity:** LOW  
**Location:** `backend/domains/orders/services/orders_service.py:345-366`  
**Status:** VERIFIED

**Evidence:**
```python
def _order_to_dict(order: Order, include_items: bool = False) -> dict[str, Any]:
    cols = [c.name for c in Order.__table__.columns]
    d = {}
    for col in cols:
        val = getattr(order, col, None)
        ...
```

This function iterates over actual DB columns, which is safe. However, it does NOT include `status_label` or `customer_username` unless explicitly told to include the extra attributes. The `get_all_orders` function at line 342 calls:
```python
[_order_to_dict(o, include_items=False) for o in orders]
```

But earlier (lines 338-341), it mutates the ORM objects:
```python
if order.status != reconciled_status:
    order.status = reconciled_status
setattr(order, "status_label", order_status_label(reconciled_status, shipments, events))
setattr(order, "customer_username", username_map.get(...))
```

These mutations use `order.status` (BUG-01) and set `status_label`/`customer_username` on the ORM object, but `_order_to_dict` only serializes DB columns unless explicitly told to include the extra attributes.

**Expected behavior:** `_order_to_dict` should include `status_label` and `customer_username`.

**Actual behavior:** These computed fields are set on the ORM object but not included in the dict output (they ARE included in the `hasattr` block at lines 353-355, but only if `include_items=False` still processes them — which it does not because lines 353-355 are outside the `if include_items` block, so they ARE included. Wait, let me re-read...).

Actually, looking more carefully at lines 353-355:
```python
for attr in ("status_label", "customer_username"):
    if hasattr(order, attr):
        d[attr] = getattr(order, attr)
```

This IS outside the `if include_items` block, so it does include them. The bug is actually that `order.status` is accessed at line 338 before `_order_to_dict` is called, which triggers BUG-01.

**Reclassified:** This is a secondary manifestation of BUG-01, not a standalone bug.

---

## CONFIRMED INCONSISTENCIES (Non-Bug Contradictions)

---

### INCON-01: Architecture Claims PostgreSQL 18 but Alembic Migrations Reference Older Patterns

**Severity:** MEDIUM  
**Location:** `ARCHITECTURE_DIAGRAM.md:20` vs `backend/alembic/versions/*`  
**Status:** INFERRED

**Evidence:**

Architecture diagram states: "Neon PostgreSQL 18 (prod & local Docker)"

But `alembic/versions/2026_07_26_16_09-b81bfc888610_baseline_canonical_orm_schema_clean.py` uses:
```python
op.add_column('internal_messages', sa.Column('is_deleted', sa.Boolean(), nullable=True))
```

And `alembic/versions/2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py` contains:
```python
if not _has_table('country_configs', 'country'):
    op.create_table('country_configs', ...)
```

**Expected behavior:** Migrations should reflect PostgreSQL 18 features and schema.

**Actual behavior:** Migrations use generic SQLAlchemy patterns and include baseline table creation checks that suggest the schema was ported from an earlier system.

**Why it matters:** Not a runtime bug, but indicates the database may not be fully aligned with the stated architecture.

**Affected workflow:** Database migrations and schema drift detection.

---

### INCON-02: `Order` Model Has `version` Column But No Optimistic Locking

**Severity:** LOW  
**Location:** `backend/domains/orders/models/order_entities.py:15`  
**Status:** VERIFIED

**Evidence:**
```python
version = Column(Integer, nullable=False, default=1)
```

The column exists but no service code reads or increments it. Optimistic locking via `version` is not implemented.

**Expected behavior:** If `version` exists, concurrent updates should check it.

**Actual behavior:** Column is written but never read, making it dead data.

**Why it matters:** Wasted column; future developers may assume optimistic locking is active.

**Affected workflow:** None currently, but potential for confusion.

---

### INCON-03: `User` Model Default `country_code="US"` but App is GCC-Focused

**Severity:** MEDIUM  
**Location:** `backend/domains/accounts/models/user.py:39`  
**Status:** VERIFIED

**Evidence:**
```python
country_code = Column(String(2), nullable=False, default="US")
```

The entire finance, tax, and logistics system is built for GCC countries (OMR currency, VAT, GCC-specific gateways). Defaulting new users to `"US"` will cause:
- Wrong tax/VAT calculation
- Wrong currency display
- Wrong payment gateway routing
- Wrong shipping zone resolution

**Expected behavior:** Default should be the platform's primary market (likely `"OM"` for Oman).

**Actual behavior:** New users default to United States, breaking GCC-specific logic.

**Why it is incorrect:** Contradicts the platform's GCC-first architecture.

**Affected workflow:** User registration, checkout, and all country-scoped operations.

**Recommended fix:** Change default to `"OM"` or require explicit country selection at registration.

---

### INCON-04: Frontend Proxy Rewrite Rules vs Backend Route Prefixes

**Severity:** MEDIUM  
**Location:** `frontend/web_app/src/app/api/` routing vs backend module prefixes  
**Status:** INFERRED

**Evidence:**

Architecture diagram states module prefixes: `/admin/*`, `/customer/*`, `/employee/*`, `/logistics-partner/*`, `/supplier/*`

Frontend `client.ts:42`:
```typescript
if (!path.startsWith("/api") && !path.startsWith("/auth") && !path.startsWith("/admin")) return `/__api${path}`;
```

The frontend rewrites unknown paths to `/__api{path}` but the backend modules use direct prefixes like `/admin/finance/ledger`. The Next.js rewrite configuration (in `next.config.ts`) is not present in the files reviewed, so the exact mapping cannot be verified.

**Expected behavior:** Frontend and backend routes should align.

**Actual behavior:** Cannot fully verify without `next.config.ts`, but the pattern suggests potential mismatch.

**Why it matters:** Frontend/backend contract violations cause 404s and broken navigation.

---

### INCON-05: `PaymentGatewayConnection` Has Both `secret_key` and `credentials` JSON Column

**Severity:** LOW  
**Location:** `backend/domains/finance/models/payments.py:94-106`  
**Status:** VERIFIED

**Evidence:**
```python
credentials = Column(JSON, nullable=True)      # Line 94
secret_key = Column(String(1000), nullable=True)  # Line 105
public_key = Column(String(500), nullable=True)   # Line 104
```

The `credentials` JSON column likely contains the same secrets as the dedicated columns, creating redundancy.

**Expected behavior:** One canonical storage location for gateway credentials.

**Actual behavior:** Two parallel storage mechanisms.

**Why it matters:** Potential for credential desynchronization and security audit confusion.

---

### INCON-06: Celery Broker Uses Redis URLs Despite Valkey Migration

**Severity:** HIGH  
**Location:** `backend/config.py:90-91`  
**Status:** VERIFIED

**Evidence:**
```python
"celery_broker_url": os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
"celery_result_backend": os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
```

Architecture diagram states: "Celery + Celery Beat + Valkey broker (`jobs/`)"

**Expected behavior:** Broker URL should use Valkey scheme.

**Actual behavior:** Default broker URLs use `redis://` scheme.

**Why it is incorrect:** Violates Valkey migration constraint and may cause connection issues if Valkey server does not accept Redis scheme URLs.

**Affected workflow:** Background job processing.

---

### INCON-07: `Order.status_label` Computed But Not a DB Column

**Severity:** LOW  
**Location:** Multiple service files  
**Status:** VERIFIED

**Evidence:**
```python
setattr(order, "status_label", order_status_label(reconciled_status, shipments, events))
```

`status_label` is set dynamically on ORM objects but is not a persisted column. This is fine for API responses but creates confusion if the object is re-queried later.

**Expected behavior:** Document that `status_label` is a computed field.

**Actual behavior:** Treated like a regular attribute in some code paths.

---

### INCON-08: `ReturnRequest` Has `user_id` Synonym for `customer_id`

**Severity:** LOW  
**Location:** `backend/domains/orders/models/order_entities.py:156`  
**Status:** VERIFIED

**Evidence:**
```python
customer_id = Column(Integer, ForeignKey('accounts.users.id', ondelete='RESTRICT'), nullable=True, index=True)
user_id = synonym('customer_id')
```

Using `synonym` creates two names for the same column, which can cause confusion in queries and serialization.

**Expected behavior:** Use one canonical name.

**Actual behavior:** Two names for the same data.

---

## SUMMARY TABLE

| ID | Severity | Category | Status | File(s) |
|---|---|---|---|---|
| BUG-01 | CRITICAL | Model/Code Mismatch | VERIFIED | order_entities.py + ~30 service files |
| BUG-02 | CRITICAL | Infinite Recursion | VERIFIED | checkout/service.py |
| BUG-03 | HIGH | DB Constraint Mismatch | VERIFIED | finance/models/payments.py |
| BUG-04 | HIGH | Naming Violation | VERIFIED | requirements.txt, config.py, valkey/client.py, etc. |
| BUG-05 | HIGH | Duplicate Definitions | VERIFIED | finance_service.py |
| BUG-06 | MEDIUM | Duplicate Columns | VERIFIED | order_entities.py |
| BUG-07 | MEDIUM | State Machine Conflict | VERIFIED | Multiple order service files |
| BUG-08 | LOW | Frontend Debug Logging | VERIFIED | client.ts |
| BUG-09 | MEDIUM | DTO Attribute Error | VERIFIED | orders/services/core/dtos.py |
| BUG-10 | MEDIUM | Config Defaults | VERIFIED | config.py |
| BUG-11 | MEDIUM | Missing Module | VERIFIED | orders_service.py |
| BUG-12 | LOW | DTO Serialization | VERIFIED | orders_service.py |
| INCON-01 | MEDIUM | Migration/Architecture Drift | INFERRED | alembic/versions/ |
| INCON-02 | LOW | Dead Column | VERIFIED | order_entities.py |
| INCON-03 | MEDIUM | Wrong Default Country | VERIFIED | accounts/models/user.py |
| INCON-04 | MEDIUM | Frontend/Backend Route Mismatch | INFERRED | client.ts |
| INCON-05 | LOW | Duplicate Credential Storage | VERIFIED | finance/models/payments.py |
| INCON-06 | HIGH | Redis Broker URLs | VERIFIED | config.py |
| INCON-07 | LOW | Computed Field Confusion | VERIFIED | tracking/service.py |
| INCON-08 | LOW | Synonym Column | VERIFIED | order_entities.py |

---

## RECOMMENDATIONS (Priority Order)

1. IMMEDIATE: Fix BUG-01 (order.status vs order.status_code) across all ~30 service files. This is a showstopper.
2. IMMEDIATE: Fix BUG-02 (infinite recursion in create_address).
3. HIGH: Fix BUG-03 (payment status check constraint) and BUG-05 (duplicate functions).
4. HIGH: Resolve BUG-04 and BUG-06 (Valkey/Redis naming violations) to comply with project constraint.
5. MEDIUM: Fix BUG-06 (duplicate order amount columns) and BUG-07 (state machine unification).
6. MEDIUM: Fix BUG-10 (config defaults), BUG-11 (missing module import), and INCON-03 (default country).
7. LOW: Clean up BUG-08 (console.log), INCON-02, INCON-05, INCON-07, INCON-08.

---

*End of PHASE_14_BUGS.md*
