# ZOZI Architecture Rules — Developer Onboarding

> **Purpose**: This document is the single source of truth for every architectural rule enforced
> by the automated gate tests (`tests/test_architecture_gates.py`) and the CI scanner
> (`scripts/system_trackers/system_architecture_audit.py`). Every new file, import, and
> refactor MUST comply with these rules. Violations will be caught by the gate tests and
> blocked from merge.

---

## Table of Contents

1. [Grid-Line Architecture (W3)](#1-grid-line-architecture-w3)
2. [Domain Folder Naming (DOM7)](#2-domain-folder-naming-dom7)
3. [File Placement Rules (DOM2/MV1)](#3-file-placement-rules-dom2mv1)
4. [Exception Handling (HL301/HL302/HL303)](#4-exception-handling-hl301hl302hl303)
5. [Query Limits (PERF4)](#5-query-limits-perf4)
6. [Router Registration](#6-router-registration)
7. [Controller-to-Controller Imports (W4)](#7-controller-to-controller-imports-w4)
8. [Naming Conventions](#8-naming-conventions)
9. [Backward-Compat Shims](#9-backward-compat-shims)
10. [Forbidden Patterns](#10-forbidden-patterns)
11. [Quick Reference Cheat Sheet](#11-quick-reference-cheat-sheet)

---

## 1. Grid-Line Architecture (W3)

The backend follows a strict **layered architecture** with unidirectional imports.
Think of it as grid-lines on a page: data flows **downward** only.

```
┌─────────────────────────────────────────────────────┐
│  ROUTERS  (HTTP layer — parse requests, return responses)
│  routers/{surface}_{domain}_{operation}.py          │
├─────────────────────────────────────────────────────┤
│  CONTROLLERS  (validation, auth, orchestration)     │
│  controllers/{domain}/{entity}_controller.py        │
├─────────────────────────────────────────────────────┤
│  SERVICES  (business logic, transactions)           │
│  services/{domain}/{entity}_service.py              │
├─────────────────────────────────────────────────────┤
│  PROVIDERS  (external integrations, AI, 3rd-party)  │
│  providers/{category}/{provider_name}.py            │
├─────────────────────────────────────────────────────┤
│  MODELS  (SQLAlchemy ORM, Pydantic schemas)         │
│  models/{domain}/{entity}.py                        │
└─────────────────────────────────────────────────────┘
```

### Import Direction Rules

| From ↓ → To → | Routers | Controllers | Services | Providers | Models |
|---|---|---|---|---|---|
| **Routers** | ❌ | ⚠️ Deprecated | ✅ **Preferred** | ❌ | ❌ |
| **Controllers** | ❌ | ❌ | ✅ | ❌ | ✅ (models only) |
| **Services** | ❌ | ❌ | ✅ (intra-domain) | ✅ | ✅ |
| **Providers** | ❌ | ❌ | ❌ | ✅ (intra-category) | ✅ |
| **Models** | ❌ | ❌ | ❌ | ❌ | ✅ (intra-domain) |

### Key Rules

**W3 — Routers MUST import from services, NOT controllers.**

```python
# ✅ CORRECT
from services.commerce.promotion_engine_service import get_active_tiers
from services.finance.treasury_query_service import get_treasury_summary

# ❌ WRONG — routers must not import from controllers
from controllers.promotion_controller import get_active_tiers
from controllers.treasury_controller import get_treasury_summary
```

**Why?** Controllers handle request validation and auth. Routers should delegate
business logic to services directly. Importing from controllers creates circular
dependency chains and makes the code untestable.

### Allowed Exceptions

Some legacy imports from controllers remain during active migration. They are
documented in `documents/ARCHITECTURE_LAYER_RULES.md` and have active TODO items.

### Cross-Domain Service Imports

Services MAY import from other domains when there is a documented business justification.
See `documents/ARCHITECTURE_LAYER_RULES.md` for the full list of allowed cross-domain
imports (e.g., `cash_management_service` → `logistics_partner_pricing` for COD calculations).

---

## 2. Domain Folder Naming (DOM7)

Every domain has a **canonical folder name**. Using non-canonical names triggers
DOM7 violations in the audit scanner.

### Canonical Domain Names

| Domain | Canonical Name | ❌ Non-Canonical (DO NOT USE) |
|---|---|---|
| Communication | `comms` | `communication`, `comms_2`, `messaging` |
| Geography | `geography` | `country`, `geo`, `geography_2` |
| Commerce | `commerce` | `shopping`, `ecommerce` |
| Finance | `finance` | `financial`, `payments`, `treasury` |
| Logistics | `logistics` | `shipping`, `delivery` |
| Catalog | `catalog` | `products`, `inventory` |
| Security | `security` | `auth`, `permissions`, `iam` |
| HR | `hr` | `human_resources`, `people` |
| Media | `media` | `uploads`, `files`, `images` |
| AI | `ai` | `ml`, `intelligence` |
| Analytics | `analytics` | `reports`, `insights` |
| Core | `core` | `common`, `shared`, `base` |

### Folder Structure Per Domain

Each layer follows the same pattern:

```
controllers/{domain}/          # Request handling, validation
models/{domain}/               # SQLAlchemy ORM classes
services/{domain}/             # Business logic
providers/{category}/          # External integrations
```

### Gate Test Validation

The gate tests verify:
- `controllers/comms/` exists with ≥2 files (not `controllers/communication/`)
- `models/comms/` exists with ≥4 files (not `models/communication/`)
- `services/comms/` exists with ≥20 files (not `services/communication/`)
- `controllers/geography/` exists (not `controllers/country/`)
- `models/geography/` exists with ≥6 files (not `models/country/`)
- `services/geography/` exists with ≥10 files (not `services/country/`)
- `providers/geography/` exists (not `providers/country/`)

---

## 3. File Placement Rules (DOM2/MV1)

Every file MUST live in its correct domain folder. The audit scanner flags
files that are in the wrong location.

### Provider Placement

| Provider Type | Correct Location | Examples |
|---|---|---|
| AI/ML providers | `providers/ai/` | `vision.py`, `chatbot.py`, `voice_to_text.py`, `ocr.py` |
| Geography providers | `providers/geography/` | `country.py`, `maps.py` |
| Media providers | `providers/media/` | `bg_remover.py` |
| HR providers | `providers/hr/` | `bg_remover.py` (legacy implementations) |
| Text/NLP providers | `providers/text/` | `embedding.py` |

### Service Placement

| Service Type | Correct Location | Examples |
|---|---|---|
| Domain services | `services/{domain}/` | `services/commerce/order_service.py` |
| Core utilities | `services/core/` | `services/core/admin_operations_service.py` |
| Write helpers | `services/core/` | `services/core/write_helpers.py` |

### Forbidden Folders

These folders MUST NOT exist in the codebase:

| Forbidden Folder | Reason | Canonical Location |
|---|---|---|
| `services/admin/` | Admin is a cross-domain concern, not a domain | `services/core/` |
| `controllers/admin/` | Admin is a cross-domain concern, not a domain | `controllers/{domain}/` |
| `models/misc/` | Models must be organized by domain | `models/{domain}/` |

---

## 4. Exception Handling (HL301/HL302/HL303)

Every exception handler MUST follow these rules. The gate tests validate
critical files for compliance.

### Rule HL301: No Bare `except:`

```python
# ❌ WRONG — catches SystemExit, KeyboardInterrupt, GeneratorExit
try:
    do_something()
except:
    pass

# ✅ CORRECT — catch specific exceptions
try:
    do_something()
except ValueError as e:
    logger.warning("Invalid value: %s", e)
except ConnectionError as e:
    logger.exception("Connection failed")
```

### Rule HL302: No Swallowed Exceptions

Every `except` block MUST either log the exception or re-raise it.
Silent `pass` inside `except` blocks is forbidden.

```python
# ❌ WRONG — exception silently swallowed
try:
    process_payment(order)
except Exception:
    pass

# ✅ CORRECT — exception is logged
try:
    process_payment(order)
except Exception:
    logger.exception("Payment processing failed for order %s", order.id)

# ✅ ALSO CORRECT — exception is re-raised
try:
    process_payment(order)
except PaymentError:
    raise
except Exception:
    logger.exception("Unexpected payment error")
    raise
```

### Rule HL303: Broad `except Exception` Must Log

When catching the broad `Exception` type, you MUST include logging.
The `logger.exception()` call is preferred because it captures the traceback.

```python
# ❌ WRONG — broad catch without logging
try:
    external_api_call()
except Exception:
    return default_value

# ✅ CORRECT — broad catch with logging
try:
    external_api_call()
except Exception:
    logger.exception("External API call failed")
    return default_value
```

### Critical Files Enforced by Gate Tests

The following files are validated in every gate test run:

```
backend/main.py
backend/utils/auth.py
backend/utils/cache.py
backend/utils/config.py
backend/utils/realtime.py
backend/utils/background_jobs.py
backend/services/finance/payments_gateway_service.py
backend/controllers/supplier/supplier_controller.py
backend/controllers/security/auth_controller.py
```

### Pattern Summary

| Pattern | Status | Fix |
|---|---|---|
| `except:` | ❌ Forbidden | Replace with `except Exception:` + logging |
| `except Exception: pass` | ❌ Forbidden | Add `logger.exception(...)` |
| `except Exception: return X` | ⚠️ Warning | Add `logger.exception(...)` before return |
| `except SpecificError as e:` | ✅ OK | Log or re-raise |
| `except Exception:` + `logger.exception()` | ✅ OK | Best practice |

---

## 5. Query Limits (PERF4)

Every database query on potentially large tables MUST include a `.limit()` clause
or use `.count()` when only counting rows.

### Rules

```python
# ❌ WRONG — unbounded query on large table
users = db.query(User).all()

# ❌ WRONG — len(.all()) loads entire table into memory
count = len(db.query(User).all())

# ✅ CORRECT — use .count() for counting
count = db.query(User).count()

# ✅ CORRECT — use .limit() for listing
users = db.query(User).limit(100).all()

# ✅ CORRECT — paginated query
users = db.query(User).offset(page * size).limit(size).all()
```

### Large Tables Requiring `.limit()`

These tables can grow unbounded and MUST use `.limit()` or `.count()`:

| Table | Reason |
|---|---|
| `User` | All platform users |
| `Order` | All orders across all time |
| `PurchaseOrder` | All supplier POs |
| `Notification` | High-volume notifications |
| `CommunicationAuditTrail` | Audit log grows indefinitely |
| `Allocation` | Inventory allocations |
| `Connection` | Network connections |

### Gate Test Validation

The gate test verifies that `command_center_service.py` uses `.count()` instead of
`len(.all())` for the active user query. Add similar checks for any new high-volume
query you introduce.

---

## 6. Router Registration

### File Naming

Router files MUST follow the flat naming convention:

```
routers/{surface}_{domain}_{operation}.py
```

| Component | Description | Examples |
|---|---|---|
| `surface` | API surface | `api`, `admin`, `supplier`, `logistics`, `public` |
| `domain` | Business domain | `catalog`, `orders`, `finance`, `comms` |
| `operation` | Specific area | `routes`, `routes_2`, `query`, `tracking` |

**Examples:**
```
api_catalog_routes.py        # Public catalog API
api_catalog_routes_2.py      # Product moderation
admin_commerce_routes.py     # Admin promotions
supplier_products.py         # Supplier product management
logistics_orders.py          # Logistics order handling
```

### Registration in `main.py`

Routers are registered dynamically in `main.py` via the `_load_routers()` function.
The registration list is:

```python
router_names = [
    ("module_name", "/api/v1/url-prefix"),
    ...
]
```

**NEVER add new router entries to `main.py` until the router module is fully wired
and tested.** Registering a broken router will prevent the app from booting.

### Prefix Conventions

| Surface | Prefix Pattern | Example |
|---|---|---|
| Public API | `/api/v1/{domain}` | `/api/v1/products` |
| Admin API | `/api/v1/admin/{domain}` | `/api/v1/admin/promotions` |
| Supplier API | `/api/v1/supplier[-domain]` | `/api/v1/supplier-products` |
| Logistics | `/api/v1/logistics[-domain]` | `/api/v1/logistics-orders` |

---

## 7. Controller-to-Controller Imports (W4)

Controllers MUST NOT import from other controllers. All shared logic between
controllers MUST live in a service module.

```python
# ❌ WRONG — controller importing from another controller
from controllers.coupon_controller import validate_coupon

# ✅ CORRECT — import from service
from services.commerce.coupon_service import validate_coupon
```

### Refactoring Pattern

When you find a controller-to-controller import:

1. Identify the shared function
2. Create a new service module (or add to an existing one)
3. Move the logic to the service
4. Update both controllers to import from the service
5. Verify both endpoints still work

---

## 8. Naming Conventions

### Module Naming

| Layer | Pattern | Example |
|---|---|---|
| Router | `{surface}_{domain}_{operation}.py` | `api_catalog_routes.py` |
| Controller | `{entity}_controller.py` | `products_controller.py` |
| Service | `{entity}_service.py` | `order_service.py` |
| Provider | `{provider_name}.py` | `vision.py`, `chatbot.py` |
| Model | `{entity}.py` | `product.py`, `order.py` |

### Function Naming

| Pattern | Usage | Example |
|---|---|---|
| `get_*` | Read operations | `get_user_by_id`, `get_all_orders` |
| `create_*` | Create operations | `create_order`, `create_user` |
| `update_*` | Update operations | `update_product`, `update_status` |
| `delete_*` | Delete operations | `delete_order`, `delete_user` |
| `validate_*` | Validation | `validate_coupon`, `validate_payment` |
| `process_*` | Business logic | `process_payment`, `process_return` |
| `require_*` | Auth dependency | `require_admin`, `require_roles` |

### Internal/Private Functions

Functions that are NOT part of the module's public API MUST be prefixed with `_`:

```python
# Public — imported by other modules
def get_user_by_id(user_id: int) -> User:
    ...

# Private — only used within this file
def _validate_user_data(data: dict) -> bool:
    ...
```

---

## 9. Backward-Compat Shims

When you move a file to a new canonical location, you MUST create a backward-compat
shim at the old location. This prevents import breakage in code that hasn't been
updated yet.

### Shim Pattern

```python
# services/communication/email_gateway.py (OLD location — shim)
"""Backward-compat shim: canonical location is services/comms/email_gateway.py"""
from services.comms.email_gateway import *  # noqa: F401,F403
from services.comms.email_gateway import (
    EmailGateway,
    send_email,
    # ... list every public name explicitly for IDE support
)
```

### Shim Requirements

1. **Re-export ALL public names** from the canonical module
2. **Add a docstring** explaining this is a shim and where the canonical location is
3. **Use explicit imports** (not just `*`) for IDE autocompletion
4. **Test both import paths** work: `from old.path import X` and `from new.path import X`

### Shim Inventory

| Old Path | Canonical Path | Domain |
|---|---|---|
| `services/communication/` | `services/comms/` | Communication |
| `models/communication/` | `models/comms/` | Communication |
| `controllers/communication/` | `controllers/comms/` | Communication |
| `services/country/` | `services/geography/` | Geography |
| `models/country/` | `models/geography/` | Geography |
| `controllers/country/` | `controllers/geography/` | Geography |
| `providers/country/` | `providers/geography/` | Geography |

---

## 10. Forbidden Patterns

### SQL Injection (SEC101)

Never construct SQL queries with string concatenation or f-strings:

```python
# ❌ WRONG — SQL injection vulnerability
table = request.query_params["table"]
db.execute(text(f"SELECT * FROM {table}"))

# ✅ CORRECT — use ORM or parameterized queries
db.query(User).filter(User.id == user_id).all()

# ✅ CORRECT — if dynamic table access is required, whitelist tables
ALLOWED_TABLES = {"users", "orders", "products"}
if table_name not in ALLOWED_TABLES:
    raise ValueError(f"Invalid table: {table_name}")
table = Table(table_name, Base.metadata, autoload_with=engine)
db.query(table).all()
```

### Raw DB Writes in Controllers

Controllers MUST NOT call `db.add()`, `db.commit()`, or `db.flush()` directly.
All database writes MUST go through service modules:

```python
# ❌ WRONG — raw DB write in controller
@router.post("/orders")
async def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    order = Order(**order_data.dict())
    db.add(order)
    db.commit()
    return order

# ✅ CORRECT — delegate to service
@router.post("/orders")
async def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    return order_service.create_order(db, order_data)
```

### Hardcoded Values

Never hardcode configuration values, URLs, secrets, or environment-specific settings:

```python
# ❌ WRONG
SECRET_KEY = "my-secret-key"
DATABASE_URL = "sqlite:///./zozi.db"
REDIS_HOST = "localhost"

# ✅ CORRECT — use settings from environment
from utils.config import settings
SECRET_KEY = settings.secret_key
DATABASE_URL = settings.database_url
REDIS_HOST = settings.redis_host
```

### Edit/Write Tools on `.py` Files

**AI agents**: Do NOT use `str_replace` or `write_file` tools directly on Python files
in the backend. Instead, use bash scripts or terminal commands to make changes.
This is a session constraint — follow it for all backend modifications.

---

## 11. Quick Reference Cheat Sheet

### Before Creating Any File

1. ✅ Check `.governance/scaffolding_contract.json` for allowed folder locations
2. ✅ Check `documents/ARCHITECTURE_LAYER_RULES.md` for import exceptions
3. ✅ Use the canonical domain folder name (see Section 2)
4. ✅ Follow the naming pattern for your layer (see Section 8)
5. ✅ Run the architecture audit: `python scripts/system_trackers/system_architecture_audit.py`

### Before Merging

1. ✅ App boots: `python -c "from backend.main import app; print('OK')"`
2. ✅ Gate tests pass: `pytest tests/test_architecture_gates.py -v`
3. ✅ No new bare `except:` blocks
4. ✅ No new unbounded queries without `.limit()`
5. ✅ Routers import from services, not controllers
6. ✅ No new files in forbidden folders (`services/admin/`, `controllers/admin/`, `models/misc/`)

### Architecture Audit Commands

```bash
# Full architecture audit
python scripts/system_trackers/system_architecture_audit.py

# Database audit
python scripts/system_trackers/database_audit.py

# Design audit
python scripts/system_trackers/design_audit.py

# Health audit
python scripts/system_trackers/health_audit.py

# Gate tests only
pytest tests/test_architecture_gates.py -v
```

### Common Mistakes & Fixes

| Mistake | Fix |
|---|---|
| Created file in `services/admin/` | Move to `services/core/` |
| Router imports from controller | Change to import from service |
| `except: pass` | Change to `except Exception: logger.exception("...")` |
| `db.query(BigTable).all()` | Add `.limit(N)` or use `.count()` |
| Used `communication/` folder | Rename to `comms/` |
| Used `country/` folder | Rename to `geography/` |
| Controller calls `db.add()` | Extract logic to service module |
| Hardcoded secret/config | Move to `utils/config.py` settings |

---

## Appendix: Gate Test Details

The gate test suite (`tests/test_architecture_gates.py`) validates the following
rules on every run:

| Test Class | What It Validates | Rule |
|---|---|---|
| `TestDOM7CommsMigration` | `comms/` folders exist, stale `communication/` imports are gone | DOM7 |
| `TestDOM7GeographyMigration` | `geography/` folders exist, shims are wired | DOM7 |
| `TestExceptionHandling` | No bare `except:`, critical files have logging | HL301/HL302 |
| `TestUnboundedQueries` | Critical queries use `.count()` or `.limit()` | PERF4 |
| `TestRouterImports` | Key routers import from services, not controllers | W3 |
| `TestAppBoot` | FastAPI app loads with ≥1400 routes | Boot |

### Running Gate Tests

```bash
# From project root
cd backend && python -m pytest ../tests/test_architecture_gates.py -v

# With verbose output
cd backend && python -m pytest ../tests/test_architecture_gates.py -v --tb=short
```

---

*Last updated: 2026-08-06 — after DOM7 communication→comms and country→geography migrations.*
*Source of truth for new violations: `scripts/system_trackers/system_architecture_audit.py`.*
