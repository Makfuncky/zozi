# ZOZI Backend Controllers Audit Report

**Scope:** Every `.py` file under `backend/controllers/**` (including all subfolders: `admin/`, `analytics/`, `audit/`, `catalog/`, `commerce/`, `comms/`, `configuration/`, `core/`, `customer/`, `finance/`, `geography/`, `governance/`, `hr/`, `identity/`, `orders/`, `products/`, `security/`, `supplier/`, `treasury/`, and `delegators/`).

**Total controller files examined:** ~70 non-`__init__` `.py` files across all subfolders, plus 4 root-level controllers.

---

## 1. NEW_4_CONTROLLERS_ASSESSMENT

**YES — all 4 are thin delegators.** No inline business logic, no inline models, no provider calls.

| File | Lines | Assessment | Evidence |
|------|-------|------------|----------|
| `backend/controllers/search_controller.py` | 43 | Clean delegator | Delegates `smart_search` and `get_recommendations` to `services.core.search_service` — each function is a single `return _fn(...)` call (lines 31, 41-43). |
| `backend/controllers/orders_controller.py` | 87 | Clean delegator | 10 functions, each a single `return _fn(...)` delegating to `services.orders.orders_service`. |
| `backend/controllers/hr_controller.py` | 91 | Clean delegator | 9 functions, each a single `return _fn(...)` delegating to `services.hr.hr_service`. |
| `backend/controllers/payments_controller.py` | 194 | Clean re-exporter | Imports request models + handler functions from `services.gateways.payments` and re-exports them via `__all__`. No logic. |

---

## 2. INLINE_MODELS_IN_CONTROLLERS

**2 cases** — Pydantic `BaseModel` classes defined inside controller files.

| File:Line | Class Name |
|-----------|-----------|
| `backend/controllers/commerce/wishlist_controller.py:38` | `class WishlistItemOut(BaseModel)` |
| `backend/controllers/finance/accounting_controller.py:30` | `class JournalEntryBody(BaseModel)` |

---

## 3. PROVIDER_CALLS_IN_CONTROLLERS

**ZERO matches.** No direct imports from or usages of `providers.*` anywhere in the controllers tree.

- `grep -r "from providers" backend/controllers/` → No files found
- `grep -r "import providers" backend/controllers/` → No files found
- `grep -r "providers\." backend/controllers/` → No files found

All controller-facing external-service calls go through `services.**` or `utils.**` (though some controllers call raw DB helpers like `first()`/`all_rows()` from `services.common.db_read` — see INLINE_LOGIC below).

---

## 4. CONTROLLER_INLINE_LOGIC

### Tier 1 — Critical violations (massive business logic in controllers)

**`backend/controllers/core/ai_controller.py`** (378 lines)
- **Lines 27-87** — `_collect_upload_sources()`: Inline file-path security validation (resolving URLs against upload root, `..` traversal checks, `Path.resolve()` containment checks), file reading, 5MB size enforcement, filename/dedup tracking. This is security-critical path-resolution and I/O orchestration.
- **Lines 90-251** — `_generate_ai_suggestions()`: The entire AI suggestion pipeline orchestrated inline: `ai_service.infer_visual_product_hint`, `extract_image_caption`, `merge_image_captions`, `infer_product_name`, `is_generic_product_name`, `suggest_category`, `detect_palette`, `infer_color_from_filenames`, `refine_color_palette`, `suggest_tags`, `suggest_material_candidates`, `suggest_variant_template`, `suggest_variant_options`, `generate_product_description` — with inline fallback chains (e.g., lines 146: `if filename_color and (not color or color.strip().lower() in neutral_color_fallbacks)`), inline category/color resolution heuristics (lines 152-158), and inline result dict construction (lines 238-251, including `"tags_string": ", ".join(tags)` on line 244).
- **Lines 254-276** — `_generate_product_angles()`: Inline product-angle generation orchestration with try/except fallback.
- **Line 189** — Inline `". ".join(part for part in (description.strip(), merged_caption) if part).strip()` tag-context building.
- **Line 244** — Inline `", ".join(tags)` for response.

**`backend/controllers/customer/users.py`** (826 lines — the worst file in the codebase)
- **Lines 15-77** — Imports ~60 SQLAlchemy models directly into the controller.
- **Line 78** — Imports raw DB read helpers `first`, `all_rows`, `count`, `aggregate_rows` from `services.common.db_read` — these are NOT service-layer business functions; they are thin DB-access wrappers.
- **Line 80** — Imports `get_password_hash` from `utils.auth` and uses it inline at **line 480**.
- **Lines 96-103** — `_build_list_page_payload()`: Inline pagination computation (`(total + page_size - 1) // page_size`).
- **Lines 106-110** — `_effective_staff_permissions()`: Inline permission-resolution logic (checks `staff_permissions`, falls back to `default_permissions_for_role`).
- **Lines 113-134** — `_serialize_staff_user()`: Inline dict serialization mapping 20+ fields from a `User` model.
- **Lines 251-310** — `_DELETE_BLOCKING_SUPPLIER_MODELS` (11 entries) and `_NULLABLE_USER_REFERENCE_UPDATES` (59 entries): Inline configuration data structures defining cascade-delete and null-update rules — business policy living in the controller.
- **Lines 137-145** — `list_staff_accounts()`: Calls `all_rows(db, User, ...)` (raw query) then does inline list-comp serialization.
- **Lines 148-198** — `get_all_users()`: Calls `count(db, User)` and `all_rows(db, User, ...)` and `all_rows(db, SupplierProfile, ...)` — three raw DB queries; inline verification-status inference logic (lines 170-177); inline field-by-field dict construction (lines 179-196).
- **Lines 201-226** — `update_user_role()`: `first(db, User, [...])` raw query; role validation; inline audit logging (lines 215-225).
- **Lines 229-246** — `toggle_user_active()`: `first(db, User, [...])` raw query; inline audit logging.
- **Lines 335-407** — `bulk_update_users_role()`: `first(db, User, ...)` raw queries per-iteration; validation; inline `updated`/`skipped` tracking; inline audit logging.
- **Lines 410-459** — `bulk_toggle_users_active()`: `first(db, User, ...)` raw queries; `_PROTECTED_EMAILS` check; inline audit logging.
- **Lines 462-518** — `create_staff_account()`: `first(db, User, ...)` for email/username existence checks; `get_password_hash(payload.password)` inline; `create_staff_user(...)` call; inline audit logging with 15-field details dict; inline serialization via `_serialize_staff_user`.
- **Lines 521-558** — `update_staff_account()`: `first(db, User, ...)` raw query; `payload.model_dump(exclude_unset=True)` inline; email collision check via `first()`; inline audit logging; inline serialization.
- **Line 562** — `from controllers.security.admin_users import delete_user_admin` — **controller calling another controller**.
- **Lines 561-582** — `delete_staff_account()`: `first(db, User, ...)` raw query; calls `delete_user_admin` from the security controller; inline audit logging.
- **Lines 585-647** — `bulk_update_staff_accounts()`: `all_rows(db, User, ...)` raw query; inline validation; `payload.model_dump(exclude_unset=True)`; inline audit logging.
- **Lines 650-723** — `list_pending_bank_accounts()`: `aggregate_rows(db, [SupplierBankAccount, User.username, SupplierProfile.business_name], ...)` with raw `joins`/`outerjoins`; inline field-by-field dict construction with 18 fields per row × 2 branches.
- **Lines 726-775** — `verify_bank_account()`: `first(db, SupplierBankAccount/LogisticsPartnerBankAccount, ...)` raw queries; inline `action.upper()`; inline audit logging; inline response dict.
- **Lines 778-810** — `delete_bank_account_record()`: `first(...)` raw query; inline `getattr(...)` serialization; inline audit logging; inline response dict.
- **Lines 811-826** — Deferred bottom-import from `services.users.users_write_service` to work around a circular import (the service re-exports handlers defined *in this controller module* — see DUPLICATED_LOGIC).

**`backend/controllers/security/admin_users.py`** (197 lines)
- **Line 18** — Imports `selectinload` from SQLAlchemy.
- **Line 20** — Imports raw DB helpers `all_rows, first` from `services.common.db_read`.
- **Line 22** — Imports models `Order, OrderItem, User` directly.
- **Lines 24-33** — Imports from `controllers.customer.users` (another controller): `audit_log`, `AuditAction`, `get_password_hash`, `force_reset_password_service` (a "service" function), and private helpers `_build_user_delete_blocker`, `_delete_order_records`, `_hard_delete_user_record`. **Controller-to-controller dependency including audit utilities and a service function.**
- **Lines 41, 123, 177** — `first(db, User, [User.id == user_id])` raw DB queries.
- **Lines 45-54** — `all_rows(db, Order, [Order.user_id == user_id], options=[selectinload(Order.items).selectinload(OrderItem.product), selectinload(Order.shipments)], order_by=[...])` — raw query with eager loading.
- **Lines 86-101, 147-157, 186-196** — Inline `audit_log()` calls.
- **Lines 74-84** — Inline error handling with a 17-type exception catch clause.
- **Lines 38, 107, 171** — Inline authorization checks (`if current_user.get("role") != "admin"`).
- **Line 184** — `get_password_hash(new_password)` — direct crypto usage in controller.

### Tier 2 — Controllers with orchestration/coordination logic that should be in services

**`backend/controllers/commerce/reviews_controller.py`** (156 lines)
- **Lines 37-45** — `_to_user_map()`: Inline user object-to-dict mapping with isinstance branching.
- **Lines 48-65** — `_serialize()`: Inline dict serialization of 13 fields.
- **Line 55** — `limit = max(1, min(200, limit))` inline clamping.
- **Lines 103-124** — `create_review()`: Orchestration logic: `product_exists` check → `find_existing_review` duplicate check → `has_verified_purchase` check → `service_create_review` → `recompute_product_rating` → `_serialize`. Also `int(review.rating)` conversion (line 116).
- **Lines 128-144** — `update_review()`: Inline authorization check (`existing.user_id != user["id"]`); inline `updates = {"rating": int(review.rating), ...}` dict construction.
- **Lines 148-156** — `delete_review()`: Inline authorization check + serialization.

**`backend/controllers/commerce/wishlist_controller.py`** (81 lines) — also an INLINE_MODEL offender
- **Lines 47-50** — `_user_id()`: Inline user-ID extraction with isinstance/type-branching.
- **Line 55** — `limit = max(1, min(200, limit))` inline clamping.
- **Lines 60-66** — `add_to_wishlist()`: Orchestration: `service_product_exists` check → `service_get_item_by_product` duplicate check → `service_create_item`.

**`backend/controllers/finance/accounting_controller.py`** (156 lines) — also an INLINE_MODEL offender
- **Lines 81-90** — `create_journal_entry()`: Inline `JournalEntryCreate(...)` construction from body fields (10 field mappings).
- **Lines 92-94** — Inline user field extraction with complex `getattr(...) or current_user.get(...) if isinstance(current_user, dict) else getattr(...)` ternary expressions for `user_id`, `username`, `user_role`.
- **Lines 95-110** — Inline `audit_log()` call with 6-field details dict.
- **Lines 48-58** — `seed_chart_of_accounts()`: Inline `count = len(gl.list_accounts(db))` extra query + conditional audit logging.
- **Line 144** — Inline `Decimal("0.00")` in response dict.

**`backend/controllers/finance/sub_ledger_controller.py`** (157 lines)
- **Lines 65, 128** — Inline `import datetime as dt` inside function bodies (violates import conventions).
- **Lines 66, 129** — Inline `dt.datetime.fromisoformat(due_date)` date parsing.
- **Lines 68, 98, 131, 152** — Inline `Decimal(str(amount))` conversion.
- **Lines 73-80, 103-110** — Inline `audit_log()` calls.
- **Lines 81, 111, 136, 157** — Inline response dict construction (`{"id": entry.id, "status": entry.status, "balance_after": float(entry.balance_after or 0)}`).

**`backend/controllers/treasury/cash_management_write_controller.py`** (215 lines)
- **Lines 16-19** — Imports `_serialize_finance_bank_settings` and `admin_queue_dispatch_transfer_batch` from `controllers.treasury.cash_management_controller` (another controller).
- **Line 53** — `return _serialize_finance_bank_settings(record)` — inline serialization via another controller's private function.

### Tier 3 — Thin controllers with minor inline helpers / repeated patterns

**`backend/controllers/core/ai_upload_controller.py`** (77 lines)
- **Lines 32-37** — `_resolve_user_id()`: Inline identity extraction (checks `current_user.get("id")`, `.get("user_id")`, `.get("user").get("id")`). Minor but should be in a service.

**`backend/controllers/treasury/payout_approval_controller.py`** (70 lines)
- **Lines 18-20** — `_notes()`: Inline payload attribute extraction.
- **Lines 23-25** — `_actor()`: Inline identity extraction returning a `(id, username)` tuple.

---

## 5. DUPLICATED_LOGIC

### 5a. `_actor(current_user)` helper — copied identically in 9 controllers

Same 12-line identity-mapping function duplicated across:

| File:Line | Notes |
|-----------|-------|
| `admin/orders_controller.py:42` | |
| `admin/products_controller.py:41` | |
| `admin/suppliers_controller.py:30` | |
| `admin/tickets_controller.py:27` | |
| `admin/coupons_controller.py:27` | |
| `admin/payouts_controller.py:22` | |
| `admin/permissions_controller.py:26` | |
| `admin/bank_accounts_controller.py:26` | |
| `admin/users_admin_controller.py:38` | |
| `catalog/category_admin_controller.py:39` | |

(`customer/users.py` and `commerce/reviews_controller.py` and `commerce/wishlist_controller.py` have their own variants: `_user_id`, `_to_user_map`, `_user_id`.)

### 5b. `_with_rls()` + `try/finally: clear_rls_context()` — copied in 12 controllers

The same RLS-context setup + try/finally teardown block:

| File:Line | |
|-----------|-------|
| `admin/analytics_controller.py:29` | |
| `admin/audit_controller.py:22` | |
| `admin/bank_accounts_controller.py:40` | |
| `admin/coupons_controller.py:41` | |
| `admin/misc_controller.py:20` | |
| `admin/orders_controller.py:56` | |
| `admin/permissions_controller.py:40` | |
| `admin/payouts_controller.py:36` | |
| `admin/products_controller.py:55` | |
| `admin/suppliers_controller.py:44` | |
| `admin/tickets_controller.py:41` | |
| `admin/users_admin_controller.py:52` | |
| `catalog/category_admin_controller.py:53` | |

### 5c. `offset = max(0, (page - 1) * page_size)` — inline pagination in 8 controllers

| File:Line | |
|-----------|-------|
| `admin/orders_controller.py:82` | |
| `admin/products_controller.py:77, 104` | |
| `admin/suppliers_controller.py:65, 86, 188` | |
| `admin/tickets_controller.py:62` | |
| `admin/coupons_controller.py:62` | |
| `admin/payouts_controller.py:56` | |
| `admin/bank_accounts_controller.py:61` | |
| `admin/users_admin_controller.py:78` | |

### 5d. Inline audit-logging pattern — `audit_log(db=..., action=..., user_id=..., username=..., user_role=..., resource_type=..., ...)`

Repe across:
- `customer/users.py`: ~12 occurrences (lines 215, 235, 389, 442, 499, 543, 571, 627)
- `security/admin_users.py`: 3 occurrences (lines 86, 147, 186)
- `finance/accounting_controller.py`: 2 occurrences (lines 49, 95)
- `finance/sub_ledger_controller.py`: 2 occurrences (lines 73, 103)

### 5e. Inline user field extraction — `getattr(current_user, "id", None) or current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", None)`

- `finance/accounting_controller.py:92-94` (3 fields: `user_id`, `username`, `user_role`)

### 5f. Controller-to-controller dependencies

| Importing controller | Imports from controller | Lines |
|---|---|---|
| `catalog/category_admin_controller.py` | `controllers.admin.admin_controller` (archive_entity, bulk_archive_entities, restore_entity) | 24-29 |
| `security/admin_users.py` | `controllers.customer.users` (audit_log, AuditAction, get_password_hash, force_reset_password_service, _build_user_delete_blocker, _delete_order_records, _hard_delete_user_record) | 24-33 |
| `customer/users.py` | `controllers.security.admin_users` (delete_user_admin) | 562 |
| `treasury/cash_management_write_controller.py` | `controllers.treasury.cash_management_controller` (_serialize_finance_bank_settings, admin_queue_dispatch_transfer_batch) | 16-19 |
| `admin/auth.py` | `controllers.security.auth_controller` (get_current_user) | 12-14 |

### 5g. Business logic duplicated between controller and service layers

- `services/admin/users_service.py` (992 lines, **docstring says "Admin users controller"**) contains a **verbatim duplicate** of the business logic from `controllers/customer/users.py` (826 lines): same model imports (line 10), same `get_password_hash`/`require_permission` imports (line 11), same `audit_log`/`AuditAction` imports (line 12), same `_build_list_page_payload` (lines 19-26), same `_effective_staff_permissions` (line 28), same `_serialize_staff_user`, same `_DELETE_BLOCKING_SUPPLIER_MODELS`/`_NULLABLE_USER_REFERENCE_UPDATES` constants, same `first()`/`all_rows()`/`count()`/`aggregate_rows()` raw DB calls, same inline audit logging.
- `services.admin.users_service` is imported BY controllers (e.g., `admin/users_admin_controller.py:21`), and `services/admin/admin_logistics_operations_service.py` (line 14) imports back from `controllers.admin.admin_controller`.
- Result: `controllers.admin.admin_controller` (line 23: `from services.admin.users_service import get_all_users`, line 45: `create_staff_account`, etc.) re-exports functions that are duplicated in the service file, which in turn re-exports/contains the same logic that lives in `controllers/customer/users.py`.

### 5h. `_require_super()` / inline "Super admin only" check — duplicated in 2 controllers

| File:Line | Code |
|-----------|------|
| `admin/orders_controller.py:219-221` | `actor = _actor(current_user); if actor.get("role") not in ("admin", "super_admin"): raise HTTPException(status_code=403, detail="Super admin only")` |
| `admin/users_admin_controller.py:57-59, 189-190, 210-211, 230-231, 253-254, 274-275, 295-296` | `_require_super()` helper (lines 57-59) then called inline at each route |

---

## 6. TOP_OFFENDERS (controllers most needing refactor)

| Rank | File | Lines | Primary violation |
|------|------|-------|-------------------|
| 1 | `controllers/customer/users.py` | 826 | **Worst.** Raw `first()`/`all_rows()`/`count()`/`aggregate_rows()` DB queries; 60 inline model imports; `get_password_hash` used inline; 4 different inline serialization blocks; inline audit logging (12×); inline validation/authorization; controller-to-controller call (`delete_user_admin`); circular-import workaround via deferred import. Logic duplicated in `services/admin/users_service.py`. |
| 2 | `controllers/core/ai_controller.py` | 378 | Entire AI pipeline (`_collect_upload_sources`, `_generate_ai_suggestions`, `_generate_product_angles`) — 250+ lines of orchestration, security-path validation, fallback chains, and inline string manipulation. |
| 3 | `controllers/security/admin_users.py` | 197 | Raw `first()`/`all_rows()` + `selectinload` queries; imports from another controller (`controllers.customer.users`) including `get_password_hash`, `audit_log`, private helpers, and a service function; inline audit logging (3×); 17-type except clause. |
| 4 | `admin/orders_controller.py` | 281 | Duplicated `_actor`/`_with_rls`/try-finally/offset/role-check pattern across all routes. |
| 5 | `admin/users_admin_controller.py` | 321 | Duplicated `_actor`/`_with_rls`/`_require_super`/try-finally/offset pattern. |
| 6 | `admin/products_controller.py` | 293 | Duplicated `_actor`/`_with_rls`/try-finally/offset pattern. |
| 7 | `admin/suppliers_controller.py` | 191 | Duplicated `_actor`/`_with_rls`/try-finally/offset pattern. |
| 8 | `finance/accounting_controller.py` | 156 | Inline `JournalEntryBody` model; inline `JournalEntryCreate` construction; inline complex user-field extraction; inline audit logging (2×); inline `Decimal("0.00")`. |
| 9 | `commerce/reviews_controller.py` | 156 | Inline `_to_user_map`/`_serialize` helpers; `create_review` orchestration (6-step flow: product-exists → dup-check → verified-purchase → create → recompute → serialize). |
| 10 | `finance/sub_ledger_controller.py` | 157 | Inline `import datetime as dt`; inline `Decimal(str(amount))` conversions; inline `float(entry.balance_after or 0)`; inline audit logging (2×); inline response dicts. |

**Honorable mentions (also need refactor):**
- `admin/coupons_controller.py` (170) — `_actor`/`_with_rls`/offset + inline `data = {...}` dict construction
- `admin/payouts_controller.py` (85) — `_actor`/`_with_rls`/offset + inline `data = {...}` dict construction
- `admin/tickets_controller.py` (121) — `_actor`/`_with_rls`/offset
- `admin/bank_accounts_controller.py` (104) — `_actor`/`_with_rls`/offset
- `admin/permissions_controller.py` (95) — `_actor`/`_with_rls`
- `admin/audit_controller.py` (76) — `_with_rls`/try-finally
- `admin/misc_controller.py` (39) — `_with_rls`/try-finally
- `catalog/category_admin_controller.py` (245) — `_actor`/`_with_rls`/`_with_rls`/try-finally + imports from `controllers.admin.admin_controller`
- `admin/auth.py` (137) — inline authorization/2FA logic; 15 `raise HTTPException` calls; imports `get_current_user` from another controller
- `commerce/wishlist_controller.py` (81) — inline model, `_user_id`, limit clamping, `add_to_wishlist` orchestration

---

## 7. SYSTEMIC ARCHITECTURAL ISSUES

1. **Controller-to-controller imports** exist in 5 places (see 5f above). Services and controllers are cross-importing each other, creating circular dependency paths.

2. **Services import from controllers** — `services/admin/admin_logistics_operations_service.py` (line 3: "All business logic lives in controllers/admin_controller.py") imports a 40+ function list from `controllers.admin.admin_controller`, plus functions from `controllers.catalog.banner_controller`, `controllers.core.export_controller`, `controllers.commerce.promotion_controller`, `controllers.commerce.flash_sale_controller`, and `controllers.orders.disputes_controller`. This is a **full architectural inversion**: the service layer depends upward on the controller layer.

3. **Pure re-export / "delegator" controllers** expose private `_`-prefixed internals through the controller boundary in: `orders/orders_controller.py`, `orders/disputes_controller.py`, `orders/returns_controller.py`, `orders/logistics_controller.py`, `orders/logistics_partner_controller.py`, `security/auth_controller.py`, `supplier/supplier_controller.py`, `supplier/supplier_document_controller.py`, `commerce/cart_controller.py`, `commerce/coupons_controller.py`, `commerce/promotion_controller.py`, `commerce/flash_sale_controller.py`, `commerce/reviews_controller.py`, `geography/country_controller.py`, `products/products_controller.py` (also uses dynamic `vars()` + `globals()` re-export), `catalog/banner_controller.py`, `finance/commission_controller.py`, `finance/invoice_controller.py`, `identity/iam_controller.py`, and all `controllers/delegators/*.py` files (auto-generated).

4. **Two identically-named "orders controllers"** exist: `controllers/orders_controller.py` (root, 87 lines, clean) and `controllers/orders/orders_controller.py` (21 lines, re-export). The subfolder version re-exports private service functions (`_calculate_order_amounts`, `_generate_order_number`, etc.) through the controller namespace.

5. **`admin/admin_controller.py`** is a 82-line barrel re-export file that imports from ~15 different `services.admin.*` modules and re-exports 82 names — it serves as the indirection hub that `services.admin.admin_logistics_operations_service` then imports back from, completing the circular loop.
