# File Shift Map — Infrastructure ↔ Domain

> Generated: 2026-08-25  
> After infrastructure/utils/ cleanup (34 files moved)

---

## PART 1: Infrastructure Files That Should Move to Domains

These files live in `infrastructure/` but import from `domains/`, violating Law 1 (arrows point down).

### 1A. Infrastructure Files Importing from Domains (24 files)

| # | Current Location | Imports From | Suggested Target |
|---|-----------------|--------------|------------------|
| 1 | `infrastructure/database/seed.py` | 21 imports: governance, catalog, comms, country, logistics, orders, hr | `domains/governance/services/seed.py` |
| 2 | `infrastructure/database/treasury_seeder.py` | finance models | `domains/finance/services/treasury_seeder.py` |
| 3 | `infrastructure/database/permission_service.py` | governance services | `domains/governance/services/permission_service.py` |
| 4 | `infrastructure/lifespan.py` | governance, finance, logistics | Split: move domain imports to `domains/governance/services/startup.py` |
| 5 | `infrastructure/messaging/downstream_hooks.py` | country models | `domains/country/services/downstream_hooks.py` |
| 6 | `infrastructure/messaging/downstream_wiring.py` | catalog, country, orders, finance | `domains/finance/services/downstream_wiring.py` |
| 7 | `infrastructure/messaging/email_service.py` | governance models, comms services | `domains/comms/services/email_service.py` |
| 8 | `infrastructure/middleware/country_detection.py` | country services | Use port: keep in middleware but import via `domains/country/ports.py` |
| 9 | `infrastructure/middleware/rls.py` | country models | Use port: keep in middleware but import via `domains/country/ports.py` |
| 10 | `infrastructure/ml/worker.py` | finance services | `providers/ml/worker.py` (replace domain import with provider) |
| 11 | `infrastructure/observability/audit.py` | governance ports | `domains/governance/services/observability_audit.py` |
| 12 | `infrastructure/search/routers/search_controller.py` | governance services | `domains/governance/services/search.py` |
| 13 | `infrastructure/security/dependencies.py` | governance models, governance services | `domains/governance/services/security_dependencies.py` |
| 14 | `infrastructure/security/key_rotation.py` | governance, comms, logistics, orders models | `domains/security/services/key_rotation.py` |
| 15 | `infrastructure/security/qr_service.py` | hr ports, governance ports | `domains/security/services/qr_service.py` |
| 16 | `infrastructure/security/security_audit.py` | governance ports | `domains/governance/services/security_audit.py` |
| 17 | `infrastructure/security/vault.py` | finance models | `domains/finance/services/vault.py` |
| 18 | `infrastructure/services/utils/translate_controller.py` | governance services | `domains/governance/services/translate.py` |
| 19 | `infrastructure/services/utils/workflow_engine.py` | governance models | `domains/governance/services/workflow_engine.py` |
| 20 | `infrastructure/utils/user_context.py` | governance models (TYPE_CHECKING only) | Keep — TYPE_CHECKING only, acceptable |
| 21 | `infrastructure/media/free_image_tools.py` | finance services | Replace with `providers/image/bg_remover` call |

### 1B. High-Priority Moves (files with 5+ domain imports)

| # | File | Domain Import Count | Target |
|---|------|-------------------|--------|
| 1 | `infrastructure/database/seed.py` | 21 | `domains/governance/services/seed.py` |
| 2 | `infrastructure/security/key_rotation.py` | 6 | `domains/security/services/key_rotation.py` |
| 3 | `infrastructure/database/seed.py` | 21 | `domains/governance/services/seed.py` |
| 4 | `infrastructure/lifespan.py` | 5 | `domains/governance/services/startup.py` |
| 5 | `infrastructure/messaging/downstream_wiring.py` | 5 | `domains/finance/services/downstream_wiring.py` |

---

## PART 2: Domain Files That Need Import Updates

These domain files import from `infrastructure/utils/` but the imported files have been moved to kernel/. Import paths need updating.

### 2A. Import Path Updates Required (kernel/ files)

| Old Import Path | New Import Path | Files Affected |
|----------------|-----------------|----------------|
| `infrastructure.utils.money` | `kernel.money` | All files using `to_decimal`, `round_money`, `to_cents` |
| `infrastructure.utils.currency` | `kernel.currency` | All files using `convert_from_aed`, `KNOWN_CURRENCY_META`, `COUNTRY_TO_CURRENCY` |
| `infrastructure.utils.constants` | `kernel.constants` | All files using `STAFF_ROLES`, `TREASURY_ROLES`, `DEFAULT_COUNTRY`, etc. |

### 2B. Domain Files Importing Kernel-Primitives via infrastructure/utils/

| # | Domain File | Imports | Update To |
|---|-------------|---------|-----------|
| 1 | `domains/accounts/services/auth/auth_controller_service.py` | `infrastructure.utils.currency` | `kernel.currency` |
| 2 | `domains/accounts/services/auth/auth_controller_service.py` | `infrastructure.utils.constants` | `kernel.constants` |
| 3 | `domains/accounts/services/users/users_admin_service.py` | `infrastructure.utils.constants` | `kernel.constants` |
| 4 | `domains/accounts/services/admin/admin_suppliers_service.py` | `infrastructure.utils.constants` | `kernel.constants` |
| 5 | `domains/accounts/services/security/security_dependencies.py` | `infrastructure.utils.constants` | `kernel.constants` |
| 6 | `domains/accounts/services/admin/admin_service.py` | `infrastructure.utils.constants` | `kernel.constants` |
| 7 | `domains/accounts/services/auth/auth_service.py` | `infrastructure.utils.config` | `infrastructure.config` |
| 8 | `domains/accounts/services/auth/auth_service.py` | `infrastructure.utils.currency` | `kernel.currency` |
| 9 | `domains/analytics/services/*.py` | `infrastructure.utils.*` | Varies |
| 10 | `domains/catalog/services/*.py` | `infrastructure.utils.*` | Varies |
| 11 | `domains/comms/services/*.py` | `infrastructure.utils.*` | Varies |
| 12 | `domains/customers/services/*.py` | `infrastructure.utils.*` | Varies |
| 13 | `domains/finance/services/*.py` | `infrastructure.utils.*` | Varies |
| 14 | `domains/governance/services/*.py` | `infrastructure.utils.*` | Varies |
| 15 | `domains/hr/services/*.py` | `infrastructure.utils.*` | Varies |
| 16 | `domains/logistics/services/*.py` | `infrastructure.utils.*` | Varies |
| 17 | `domains/orders/services/*.py` | `infrastructure.utils.*` | Varies |
| 18 | `domains/suppliers/services/*.py` | `infrastructure.utils.*` | Varies |

---

## PART 3: Domain Files Importing from infrastructure/utils/ (Full List)

### By Domain — Import Count

| Domain | Files Importing infrastructure/utils/ |
|--------|--------------------------------------|
| accounts | ~45 files |
| analytics | ~15 files |
| catalog | ~25 files |
| comms | ~20 files |
| country | ~10 files |
| customers | ~20 files |
| finance | ~35 files |
| governance | ~50 files |
| hr | ~20 files |
| logistics | ~30 files |
| orders | ~25 files |
| promotions | ~10 files |
| suppliers | ~15 files |
| security | ~10 files |
| **TOTAL** | **~310 files** |

---

## PART 4: Recommended Shift Order

### Immediate (low risk, high impact)
1. **Update kernel.primitive imports** — Global search/replace:
   - `from infrastructure.utils.money` → `from kernel.money`
   - `from infrastructure.utils.currency` → `from kernel.currency`
   - `from infrastructure.utils.constants` → `from kernel.constants`

2. **Move `infrastructure/database/seed.py`** — 21 domain imports, should be in `domains/governance/services/seed.py`

3. **Move `infrastructure/security/key_rotation.py`** — 6 domain imports, should be in `domains/security/services/key_rotation.py`

### Medium (requires port abstraction)
4. **Move `infrastructure/messaging/downstream_wiring.py`** — 5 domain imports
5. **Move `infrastructure/messaging/email_service.py`** — 2 domain imports
6. **Move `infrastructure/security/dependencies.py`** — 2 domain imports
7. **Move `infrastructure/security/vault.py`** — 1 domain import

### Lower Priority (TYPE_CHECKING or single import)
8. `infrastructure/utils/user_context.py` — TYPE_CHECKING only, acceptable
9. `infrastructure/middleware/rls.py` — Use port abstraction
10. `infrastructure/middleware/country_detection.py` — Use port abstraction

---

## Summary

| Category | Count |
|----------|-------|
| Infrastructure files to move to domains | 21 (excl. TYPE_CHECKING) |
| Domain files needing import updates | ~310 |
| Kernel.primitive imports to update | ~50+ files |
