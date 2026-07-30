# Reference Data Reorganization Plan

## Goal
Move all code out of `backend/reference_data/` into the canonical top-level directories `backend/controllers/`, `backend/services/`, `backend/routers/`, merge duplicate cross-domain modules (`accounts/`, `finance/`, `payments/`), and update every affected import across the repo.

## Current State
```
backend/
├── controllers/        ← empty
├── routers/            ← empty
├── reference_data/
│   ├── controllers/    ← country, export, logistics, marketing, products, search, suppliers
│   ├── services/       ← ai, chat, country, escalation, logistics, marketing, media, search, suppliers, workflows
│   ├── routers/        ← contact, country, currency, export, logistics, marketing, media, products, search, shift_handover, succession, suppliers, upload, workflows
│   ├── accounts/       ← domain package (to be dissolved)
│   ├── finance/        ← domain package (to be dissolved)
│   ├── payments/       ← domain package (to be dissolved)
│   ├── vat_rates.py
│   ├── category_tax_profiles.py
│   ├── country_curated.py
│   ├── country_profile_enums.py
│   ├── curated_cities.py
│   ├── research/
│   └── zozi_variant_config.json
```

## Target State
```
backend/
├── controllers/
│   ├── accounts/       ← from reference_data/accounts/controllers/
│   ├── finance/        ← from reference_data/finance/controllers/
│   ├── payments/       ← from reference_data/payments/controllers/
│   ├── country/        ← from reference_data/controllers/country/
│   ├── export/         ← from reference_data/controllers/export/
│   ├── logistics/
│   ├── marketing/
│   ├── products/
│   ├── search/
│   └── suppliers/
├── services/
│   ├── accounts/       ← from reference_data/accounts/services/ + domain-level modules
│   ├── finance/        ← from reference_data/finance/services/ + domain-level modules
│   ├── payments/       ← from reference_data/payments/services/
│   ├── ai/
│   ├── chat/
│   ├── country/
│   ├── escalation/
│   ├── logistics/
│   ├── marketing/
│   ├── media/
│   ├── search/
│   ├── suppliers/
│   └── workflows/
├── routers/
│   ├── accounts/       ← from reference_data/accounts/routers/
│   ├── finance/        ← from reference_data/finance/routers/
│   ├── payments/       ← from reference_data/payments/routers/
│   ├── contact/
│   ├── country/
│   ├── currency/
│   ├── export/
│   ├── logistics/
│   ├── marketing/
│   ├── media/
│   ├── products/
│   ├── search/
│   ├── shift_handover/
│   ├── succession/
│   ├── suppliers/
│   ├── upload/
│   └── workflows/
├── dependencies.py     ← merged from accounts/, finance/, payments/
├── exceptions.py       ← merged from accounts/, finance/, payments/
├── schemas.py          ← merged from accounts/, finance/, payments/
├── vat_rates.py        → services/finance/vat_rates.py
├── category_tax_profiles.py → services/finance/category_tax_profiles.py
├── country_curated.py  → services/country/country_curated.py
├── country_profile_enums.py → services/country/country_profile_enums.py
├── curated_cities.py   → services/country/curated_cities.py
├── reference_data/
│   ├── research/
│   └── zozi_variant_config.json
└── ...
```

## Steps

### 1. Create missing top-level directories
- Create `backend/services/` (does not currently exist)
- `backend/controllers/` and `backend/routers/` already exist but are empty

### 2. Move reference_data/controllers/* to backend/controllers/
Move all subdirectories and files:
- `reference_data/controllers/accounts/` → `backend/controllers/accounts/` (if exists after merging)
- `reference_data/controllers/country/` → `backend/controllers/country/`
- `reference_data/controllers/export/` → `backend/controllers/export/`
- `reference_data/controllers/logistics/` → `backend/controllers/logistics/`
- `reference_data/controllers/marketing/` → `backend/controllers/marketing/`
- `reference_data/controllers/products/` → `backend/controllers/products/`
- `reference_data/controllers/search/` → `backend/controllers/search/`
- `reference_data/controllers/suppliers/` → `backend/controllers/suppliers/`

Also move merged accounts/finance/payments controllers:
- `reference_data/accounts/controllers/` → `backend/controllers/accounts/`
- `reference_data/finance/controllers/` → `backend/controllers/finance/`
- `reference_data/payments/controllers/` → `backend/controllers/payments/`

### 3. Move reference_data/services/* to backend/services/
Move all subdirectories and files:
- `reference_data/services/ai/` → `backend/services/ai/`
- `reference_data/services/chat/` → `backend/services/chat/`
- `reference_data/services/country/` → `backend/services/country/`
- `reference_data/services/escalation/` → `backend/services/escalation/`
- `reference_data/services/logistics/` → `backend/services/logistics/`
- `reference_data/services/marketing/` → `backend/services/marketing/`
- `reference_data/services/media/` → `backend/services/media/`
- `reference_data/services/search/` → `backend/services/search/`
- `reference_data/services/suppliers/` → `backend/services/suppliers/`
- `reference_data/services/workflows/` → `backend/services/workflows/`

Also move merged accounts/finance/payments services:
- `reference_data/accounts/services/` → `backend/services/accounts/`
- `reference_data/finance/services/` → `backend/services/finance/`
- `reference_data/payments/services/` → `backend/services/payments/`

### 4. Move reference_data/routers/* to backend/routers/
Move all subdirectories and files:
- `reference_data/routers/contact/` → `backend/routers/contact/`
- `reference_data/routers/country/` → `backend/routers/country/`
- `reference_data/routers/currency/` → `backend/routers/currency/`
- `reference_data/routers/export/` → `backend/routers/export/`
- `reference_data/routers/logistics/` → `backend/routers/logistics/`
- `reference_data/routers/marketing/` → `backend/routers/marketing/`
- `reference_data/routers/media/` → `backend/routers/media/`
- `reference_data/routers/products/` → `backend/routers/products/`
- `reference_data/routers/search/` → `backend/routers/search/`
- `reference_data/routers/shift_handover/` → `backend/routers/shift_handover/`
- `reference_data/routers/succession/` → `backend/routers/succession/`
- `reference_data/routers/suppliers/` → `backend/routers/suppliers/`
- `reference_data/routers/upload/` → `backend/routers/upload/`
- `reference_data/routers/workflows/` → `backend/routers/workflows/`

Also move merged accounts/finance/payments routers:
- `reference_data/accounts/routers/` → `backend/routers/accounts/`
- `reference_data/finance/routers/` → `backend/routers/finance/`
- `reference_data/payments/routers/` → `backend/routers/payments/`

### 5. Move domain-level modules to services/
- `reference_data/accounts/engine.py`, `coa.py`, `journal.py`, `fx.py`, `multi_book.py`, `periods.py`, `subledgers.py`, `controls.py` → `backend/services/accounts/`
- `reference_data/finance/assets.py`, `async_jobs.py`, `automated_reporting.py`, `automation.py`, `budgets.py`, `cash.py`, `cod_reconciliation.py`, `consolidation.py`, `deferred_revenue.py`, `distribution.py`, `dunning.py`, `expenses.py`, `gateway_reconciliation.py`, `import_duty.py`, `intercompany.py`, `inventory_reconciliation.py`, `landed_cost.py`, `multi_currency.py`, `orphan_detector.py`, `payout_batches.py`, `period_close.py`, `po_grn_match.py`, `price_change.py`, `reconciliation.py`, `refund.py`, `refund_automation.py`, `reports.py`, `revenue_recognition.py`, `subscription_billing.py`, `trading.py`, `treasury.py` → `backend/services/finance/`
- `reference_data/finance/models/trading.py` → `backend/services/finance/`
- `reference_data/finance/models/__init__.py` → delete (empty)

### 6. Move loose root-level reference_data files
- `reference_data/vat_rates.py` → `backend/services/finance/vat_rates.py`
- `reference_data/category_tax_profiles.py` → `backend/services/finance/category_tax_profiles.py`
- `reference_data/country_curated.py` → `backend/services/country/country_curated.py`
- `reference_data/country_profile_enums.py` → `backend/services/country/country_profile_enums.py`
- `reference_data/curated_cities.py` → `backend/services/country/curated_cities.py`

### 7. Merge duplicate files (concatenate with comment headers)
Create at `backend/` top level:
- `backend/dependencies.py` ← `accounts/dependencies.py` + `finance/dependencies.py` + `payments/dependencies.py`
- `backend/exceptions.py` ← `accounts/exceptions.py` + `finance/exceptions.py` + `payments/exceptions.py`
- `backend/schemas.py` ← `accounts/schemas.py` + `finance/schemas.py` + `payments/schemas.py`

Format each merged file with clear comment headers preserving domain attribution.

Delete source files after merging.

### 8. Create missing __init__.py files
Create empty `__init__.py` in:
- `backend/controllers/__init__.py`
- `backend/services/__init__.py`
- `backend/routers/__init__.py`
- `backend/controllers/accounts/__init__.py`
- `backend/controllers/finance/__init__.py`
- `backend/controllers/payments/__init__.py`
- `backend/services/accounts/__init__.py`
- `backend/services/finance/__init__.py`
- `backend/services/payments/__init__.py`
- `backend/routers/accounts/__init__.py`
- `backend/routers/finance/__init__.py`
- `backend/routers/payments/__init__.py`

### 9. Update all imports across the entire repo
Replace `reference_data.*` imports with new paths in EVERY `.py` file under `backend/`:

| Old import | New import |
|---|---|
| `from reference_data.controllers.xxx` | `from controllers.xxx` |
| `from reference_data.services.xxx` | `from services.xxx` |
| `from reference_data.routers.xxx` | `from routers.xxx` |
| `from reference_data.accounts.controllers.xxx` | `from controllers.accounts.xxx` |
| `from reference_data.accounts.services.xxx` | `from services.accounts.xxx` |
| `from reference_data.accounts.routers.xxx` | `from routers.accounts.xxx` |
| `from reference_data.finance.controllers.xxx` | `from controllers.finance.xxx` |
| `from reference_data.finance.services.xxx` | `from services.finance.xxx` |
| `from reference_data.finance.routers.xxx` | `from routers.finance.xxx` |
| `from reference_data.payments.controllers.xxx` | `from controllers.payments.xxx` |
| `from reference_data.payments.services.xxx` | `from services.payments.xxx` |
| `from reference_data.payments.routers.xxx` | `from routers.payments.xxx` |
| `from reference_data.accounts.dependencies` | `from dependencies` |
| `from reference_data.finance.dependencies` | `from dependencies` |
| `from reference_data.payments.dependencies` | `from dependencies` |
| `from reference_data.accounts.exceptions` | `from exceptions` |
| `from reference_data.finance.exceptions` | `from exceptions` |
| `from reference_data.payments.exceptions` | `from exceptions` |
| `from reference_data.accounts.schemas` | `from schemas` |
| `from reference_data.finance.schemas` | `from schemas` |
| `from reference_data.payments.schemas` | `from schemas` |
| `from reference_data.vat_rates` | `from services.finance.vat_rates` |
| `from reference_data.category_tax_profiles` | `from services.finance.category_tax_profiles` |
| `from reference_data.country_curated` | `from services.country.country_curated` |
| `from reference_data.country_profile_enums` | `from services.country.country_profile_enums` |
| `from reference_data.curated_cities` | `from services.country.curated_cities` |
| `import reference_data.controllers.xxx` | `import controllers.xxx` |
| `import reference_data.services.xxx` | `import services.xxx` |
| `import reference_data.routers.xxx` | `import routers.xxx` |

### 10. Update main.py
Make these specific replacements:
- **Lifespan imports**:
  - `from controllers.admin.admin_controller import load_role_permission_settings` → `from controllers.accounts.admin.admin_controller import load_role_permission_settings`
  - `from services.admin.command_center_background import start_background_jobs` → `from services.accounts.admin.command_center_background import start_background_jobs`
  - `from services.jobs.scheduler import start_finance_scheduler` → `from services.finance.jobs.scheduler import start_finance_scheduler`
  - `from controllers import payments_controller` → `from controllers.payments.payments_controller import payments_controller`

- **Router candidates** (line 520):
  Replace `("reference_data.accounts", "reference_data", "reference_data.finance", "reference_data.payments")` with `("controllers.accounts", "controllers", "controllers.finance", "controllers.payments", "routers.accounts", "routers", "routers.finance", "routers.payments", "services.accounts", "services.finance", "services.payments")`

- **Hardcoded import** (line 542):
  `from reference_data.accounts.routers.admin.admin_promotions import country_router as promotions_country_router` → `from routers.accounts.admin.admin_promotions import country_router as promotions_country_router`

- **Other hardcoded imports**:
  - `importlib.import_module("reference_data.routers.logistics.logistics_partner")` → `importlib.import_module("routers.logistics.logistics_partner")`
  - `importlib.import_module("reference_data.routers.country.countries")` → `importlib.import_module("routers.country.countries")`
  - `from reference_data.routers.chat.ws_chat import websocket_user as _ws_user` → `from routers.chat.ws_chat import websocket_user as _ws_user`

### 11. Update reference_data/__init__.py
Replace contents with:
```python
"""Data package: curated reference datasets for country onboarding."""

from __future__ import annotations

__all__ = []
```
(Or leave as a minimal stub since reference_data will only contain research/ and config.)

### 12. Remove empty domain directories and __pycache__
After all files are moved and imports updated, remove:
- `reference_data/accounts/`
- `reference_data/finance/`
- `reference_data/payments/`
- All `__pycache__/` directories under `reference_data/`
- Any empty directories left behind

### 13. Verification
Run these checks:
```python
import sys
sys.path.insert(0, r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend')

import controllers
import services
import routers
import controllers.accounts
import services.finance
import routers.payments
import dependencies
import exceptions
import schemas

import py_compile
py_compile.compile(r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\main.py', doraise=True)
```

Also verify no remaining `reference_data.controllers`, `reference_data.services`, `reference_data.routers` imports exist outside of `reference_data/` itself.

## Risks
1. **Massive import surface**: Imports to `reference_data.*` exist in `main.py`, `db/seed_finance_demo.py`, `tests/test_finance_e2e.py`, `alembic/`, and throughout `reference_data/`. Missing any will break runtime or migrations. Mitigation: use regex replacement across all `.py` files, then verify with grep.
2. **Circular imports**: `accounts/__init__.py` and `finance/__init__.py` re-export cross-domain symbols. Removing them may break code importing from these facades. Mitigation: update all imports before removing directories.
3. **Name collisions in merged files**: `dependencies.py`, `exceptions.py`, `schemas.py` from all three domains will be concatenated. If class/function names collide, the merge breaks. Mitigation: verify no name collisions before merging; if collisions exist, namespace-qualify them.
4. **main.py router candidate list**: Changing the candidate tuple may affect router import order. Mitigation: test that all routers still mount correctly after the change.
5. **Missing `backend/services/`**: This directory does not exist yet and must be created before moving files.

## Open Questions
1. **Resolved**: Top-level directories use plural names (`controllers`, `services`, `routers`) matching existing repo convention.
2. **Resolved**: `backend/services/` must be created since it does not exist.
3. **Resolved**: Merged cross-domain files (`dependencies.py`, `exceptions.py`, `schemas.py`) go at `backend/` top level as shared utilities.
