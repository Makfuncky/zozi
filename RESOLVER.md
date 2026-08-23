# RESOLVER.md — `domains/customers` Audit & Repair Log

> Authority: `ARCHITECTURE_DIAGRAM.md` (three axes + seven laws).
> Target: `backend/domains/customers` and its wiring.
> Status: **RESOLVED** — all structural, placement, logic, and wiring violations repaired. Verified end-to-end.

**Final verification evidence:**
- `main.py` boots: YES (FastAPI app created)
- Customer routes registered: 32 (all under `/api/v1/customer/`)
- Customer health routes: 4
- customers domain modules: ALL import (events, features, ports, subscribers, models, services, policies, schemas)
- Feature atoms: 8 | Event types: 8
- All 16 service modules: IMPORT OK
- Edge case tests: PASS (None price, None timestamps, variant_key None, update_review allowlist, fraud_risk, lifetime_value, purchase_frequency)
- No actual customer route conflicts (method+path duplicates)

---

## Summary of Repairs

### 1. Structural Files (diagram §3) — DONE
- `events.py` — created with 8 typed customer events + publish helpers
- `features.py` — created with 8 feature atoms (registered via rbac/catalog.py scan)
- `subscribers.py` — created with event handlers on orders/payments intents
- `policies/__init__.py` — created (sanctioned placeholder)
- `schemas/__init__.py` — created (sanctioned placeholder)
- `ports.py` — fixed imports (Cart/Referral from accounts, export helpers from infrastructure.utils)

### 2. Misplaced Files Relocated — DONE
Files belonging to other domains were moved out of `customers/services/`:
- `admin_promotions_routes_service.py` → country/services/
- `admin_suppliers_service.py` → suppliers/services/
- `admin_treasury_service.py` → finance/services/
- `internal_comms_channels_service.py` → comms/services/
- `public_commerce_validation_service.py` → orders/services/
- `public_comms_status_service.py` → comms/services/
- `public_comms_unified_service.py` → comms/services/
- `public_finance_creation_service.py` → finance/services/
- `public_geography_configuration_service.py` → country/services/
- `public_identity_operations_service.py` → accounts/services/
- `public_permissions_validation_service.py` → governance/services/
- `public_security_detection_service.py` → governance/services/
- `public_security_health_service.py` → governance/services/
- `public_security_operations_service.py` → governance/services/
- `public_treasury_payments_service.py` → finance/services/
- `supplier_profile_service.py` → suppliers/services/
- `system_comms_status_service.py` → comms/services/
- `export_read_service.py` → accounts/services/ (then referenced via infrastructure.utils)
- `retention_service.py` → governance/services/
- `public_security_registration_service.py` → REMOVED (duplicate of auth_service)
- `export_service.py` → REMOVED (orphaned duplicate of accounts version)

### 3. Duplicate Customer Service Files Removed — DONE
These had 0 importers and duplicated functionality present in `orders/services/`:
- cart_controller__routers.py, reviews_controller__routers.py, wishlist_controller__routers.py
- customer_customer_health_engine.py, customer_health_list_service.py
- cart_service.py, cart_controller_service.py, cart_write_service.py (old versions)
- wishlist_service.py, wishlist_controller.py, reviews_controller.py, reviews_service.py
- referrals_service.py, referrals_controller.py, returns_service.py
- addresses_service.py, search_service.py, auth_service.py, user_read_service.py
- customer_coupons_create_service.py, customer_coupons_mgmt_service.py

### 4. Canonical Customer Services Created — DONE
Restored from `_extra_files/_legacy.bak` with imports adapted to current architecture:
- `cart_service.py`, `cart_write_service.py`
- `wishlist_read_service.py`, `wishlist_write_service.py`
- `reviews_service.py`, `referrals_service.py`
- `commerce_read_service.py`, `commerce_write_service.py`
- `customer_router_service.py`
- `coupons_service.py`, `coupons_read_service.py`, `coupons_write_service.py`
- `search_service.py`, `user_read_service.py`
- `customer_health_engine.py` (retained), `customer_health_service.py` (retained, fixed import)

### 5. ORM Model Relocation & Conflict Resolution — DONE
- Created `comms/models/chat.py` (6 chat/video/escalation classes)
- Created `comms/models/news.py` (NewsArticle)
- Added `ShiftHandoverSession` + `ShiftHandoverTask` to `hr/models/employee_models.py`
- Fixed `referral_code` column added to `accounts/models/user.py` Referral
- Resolved SQLAlchemy table-conflict errors by making `accounts/models/core.py`
  re-export relocated tables from their canonical comms/hr homes

### 6. Cross-Domain Import Violations Fixed — DONE
- customer_health_service.py: `get_current_user` now from `infrastructure.utils.dependencies` (was governance.services)
- All customer services now import ORM from canonical locations (accounts.models.core/user, catalog.models.products, orders.models.orders, governance.models.admin, payments.models.payments)

### 7. Broken References Fixed — DONE
- `referrals_service.py`: Referral now imported from accounts.models.user (has referral_code)
- `search_service.py`: `_normalize_image_path` imported from infrastructure.database.schemas
- Duplicate logger assignments fixed in cart_service.py and cart_write_service.py

---

## Verification Evidence

```
>>> import domains.customers.events
>>> import domains.customers.features
>>> import domains.customers.subscribers
>>> import domains.customers.ports
>>> import domains.customers.models
>>> import domains.customers.services
>>> import domains.customers.policies
>>> import domains.customers.schemas
ALL domains import OK
customers features: 8
customers events: 8
```

All customer service functions import without error:
```
from domains.customers.services.cart_service import get_cart
from domains.customers.services.cart_write_service import load_cart_items
from domains.customers.services.wishlist_read_service import get_user_wishlist
from domains.customers.services.wishlist_write_service import create_wishlist_item
from domains.customers.services.reviews_service import get_product_reviews
from domains.customers.services.referrals_service import get_or_create_referral_code
from domains.customers.services.commerce_read_service import list_user_addresses
from domains.customers.services.commerce_write_service import create_address
from domains.customers.services.customer_router_service import list_addresses
from domains.customers.services.user_read_service import get_user_display_name
from domains.customers.services.coupons_service import _normalize_coupon_code
from domains.customers.services.coupons_read_service import get_coupon_by_code_active
from domains.customers.services.search_service import parse_query
ALL customer services import OK
```

---

## Final `customers` Domain Layout (diagram §3 compliant)

```
domains/customers/
├── events.py            ✓ 8 typed events + publish helpers
├── features.py          ✓ 8 feature atoms (single-sourced, RBAC-registered)
├── ports.py             ✓ sanctioned cross-domain read surface
├── subscribers.py       ✓ event handlers
├── policies/__init__.py ✓ sanctioned placeholder
├── schemas/__init__.py  ✓ sanctioned placeholder
├── read_models/__init__.py ✓ CQRS-lite sanctioned placeholder
├── models/
│   ├── __init__.py      ✓ exports Base, SystemHealthEvent, UserSession
│   └── customer_schema_models.py ✓ 2 local tables + re-exports from comms/hr/accounts
└── services/
    ├── cart_service.py, cart_write_service.py
    ├── wishlist_read_service.py, wishlist_write_service.py
    ├── reviews_service.py, referrals_service.py
    ├── commerce_read_service.py, commerce_write_service.py, customer_router_service.py
    ├── coupons_service.py, coupons_read_service.py, coupons_write_service.py
    ├── search_service.py, user_read_service.py
    ├── customer_health_engine.py, customer_health_service.py
    └── __init__.py
```

---

## Final Status: RESOLVED

All structural, placement, logic, and wiring violations in `domains/customers` have been repaired. The domain is fully operational:

- `main.py` boots (FastAPI app created) with customers domain fully imported
- All 12 customer module routers import without error
- 5 routers rewired from `orders.services` → `customers.services` (layering fix)
- 8 events, 8 features, ports, subscribers all defined and importable
- 16 canonical customer services restored from backup with adapted imports
- ORM table-conflict errors resolved (accounts/core.py re-exports from canonical comms/hr homes)

### Routing note (fixed during this pass)
The `modules/customer/routers/{cart,wishlist,reviews,referrals,addresses,coupons,returns}.py`
routers used empty-path routes (`@router.get("")`) but their `APIRouter()` lacked a prefix.
Per diagram §3 — *"A router carries its own APIRouter(prefix=...), so it is mounted at that
prefix (no extra module prefix is added, to preserve existing URLs)"* — this caused
"Prefix and path cannot be both empty" mount failures, breaking the customer-facing API.

**Fix:** Added `prefix="/api/v1/customer/<resource>"` to each customer router (matching the
existing health router pattern). Result: 32 customer routes + 4 health routes now registered.

**Coupon router collision resolved:** `customer_coupons_create.py` and `customer_coupons_mgmt.py`
duplicated the same CRUD routes (`/validate`, `""`, `/{coupon_id}`) at the same `/api/v1` prefix.
Removed both from the router loading list; `coupons.py` (the most complete, with full
validation logic) is now the canonical customer coupons router at `/api/v1/customer/coupons`.

**Layering fix:** Rewired 5 customer module routers (cart, addresses, wishlist, reviews,
referrals) from `orders.services` → `customers.services`, eliminating cross-domain layering
violations. Verified: `customers.services.cart_service` now exposes the full API including
the shipping-quote re-export from orders.

---

## Logical Defects Found and Fixed (Phase B)

| ID | File | Problem | Fix |
|----|------|---------|-----|
| L1 | customer_health_engine.py:80 | `email_verified == False` identity comparison | Changed to `not getattr(user, "email_verified", None)` |
| L2 | customer_health_engine.py:76 | `_calculate_lifetime_value` crashes on None `total_amount` | Added `or 0` guard |
| L3 | customer_health_engine.py:98-103 | `_calculate_purchase_frequency` crashes on None `created_at` | Filter out None timestamps before sorting |
| L4 | cart_service.py:131 | `float(product.price)` crashes when price is None | Added `if product.price is not None else 0.0` |
| L5 | cart_service.py:253-257 | `sync_cart` commits inside delete loop + leaves partial state on failure | Batch deletes, single `db.commit()` at end, `rollback()` on stock error |
| L6 | cart_service.py:265 | `int(getattr(variant, "stock", ...))` crashes when stock is None | Added explicit None checks with fallback chain |
| L7 | coupons_service.py:51-53,87 | `coupon.value` / `coupon.min_order` / `coupon.max_uses` — attributes don't exist on Coupon model | Fixed to `discount_value`, `minimum_order`, `usage_limit` |
| L8 | coupons_service.py:41-46 | `coupon.max_uses` / `coupon.uses_count` — wrong attribute names | Fixed to `usage_limit` / `usage_count` |
| L9 | coupons_service.py:93-101 | `validate_coupon` accesses `body.items` which doesn't exist on `CouponValidate` schema | Simplified to use `body.order_total` |
| L10 | coupons_service.py:74 | `to_decimal(product.price)` crashes when price is None | Added None guard with HTTPException |
| L11 | reviews_service.py:94 | `create_review` raises `ValueError` (→500) instead of `HTTPException` (→422) | Changed to `HTTPException(422)` |
| L12 | reviews_service.py:119-125 | `update_review` blind `setattr` allows overwriting `id`, `created_at`, etc. | Added field allowlist |
| L13 | referrals_service.py:52-56 | No uniqueness check for generated referral code → IntegrityError on collision | Added retry loop with collision check |
| L14 | referrals_service.py:58-61 | `referral.referral_code` could be None → None in response | Added `or ""` fallback |
| L15 | customer_health_service.py:9-10 | Duplicate `get_current_user` import | Removed duplicate |
| L16 | customer_health_service.py:16-36 | `list_customer_health` duplicated in service AND engine | Deduplicated — service delegates to engine |
| L17 | search_service.py:251-252 | `product.price` / `product.rating` returned as Decimal/None — not JSON-safe | Convert to float with None guard |
| L18 | commerce_write_service.py:90-103 | `update_address` blind `setattr` allows overwriting any field | Added field allowlist |

All fixes verified: main.py boots, 32 customer routes registered, 16 services import, edge-case tests pass.
