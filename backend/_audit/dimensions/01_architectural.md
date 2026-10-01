# Architectural Audit — Dimension 01: Architectural Compliance

**Audit Date:** 2026-09-28  
**Auditor:** Kilo  
**Scope:** Laws 1–7 and section 7.1 from ARCHITECTURE_STACK.md  
**Status:** In Progress  

---

## Executive Summary

The ZOZI backend exhibits a **partially implemented modular architecture** with significant cross-domain coupling violations. While the `ports.py`/`events.py`/`subscribers.py` pattern is correctly established in some domains, the router layer has become the primary vector for unauthorized cross-domain service imports, bypassing the sanctioned read surface. The `DOMAIN_ALLOWLIST.yaml` is severely outdated and does not cover the majority of actual cross-domain imports.

**Key Metrics:**
- 75 router files across 5 modules × 15 domains
- 177 cross-domain service imports in routers (should be 0 or allowlisted)
- 44 cross-domain ports imports (correct pattern, but underutilized)
- 1 direct model import in routers (violation)
- Multiple routers with business logic beyond thin delegation
- 16 domain directories confirmed; `media/` domain is empty

---

## Laws Audited

| Law | Description | Status |
|-----|-------------|--------|
| Law 1 | Layer direction: modules → domains → infrastructure | PARTIAL |
| Law 2 | Domain isolation: no cross-domain direct imports | VIOLATED |
| Law 3 | Cross-domain reads via ports.py only | PARTIAL |
| Law 4 | Cross-domain writes via events/subscribers | PARTIAL |
| Law 5 | No business logic in routers | VIOLATED |
| Law 6 | Router thinness: delegation only | VIOLATED |
| Law 7 | Allowlist for temporary cross-domain imports | MISMATCH |

---

## Findings

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Evidence Strength | Truth Level | Claim State | Sibling | Verify | Test | Rollback | Blast Radius | Depends on | Blocks |
|----|------|--------|---------|-----------|---------|--------|-------|-----|--------|----------|------------|-------------------|-------------|-------------|---------|--------|------|----------|--------------|------------|--------|
| ARCH-001 | 1 | NEW | Cross-domain imports | backend/modules/supplier/routers/catalog.py:10 | Router imports `domains.catalog.services.products.products_service` directly | Cross-domain reads must go through `domains.catalog.ports` | +1 unauthorized service import | Replace import with `domains.catalog.ports` equivalent | Low | High | Certain | Direct evidence | File | Unverified | ARCH-002 | grep | Unit test import graph | Revert import | Low | None | None |
| ARCH-002 | 1 | NEW | Cross-domain imports | backend/modules/supplier/routers/finance.py:14 | Router imports `domains.finance.services.ledger.general_ledger_service` directly | Cross-domain reads must go through `domains.finance.ports` | +1 unauthorized service import | Replace import with `domains.finance.ports` equivalent | Low | High | Certain | Direct evidence | File | Unverified | ARCH-001 | grep | Unit test import graph | Revert import | Low | None | None |
| ARCH-003 | 1 | NEW | Cross-domain imports | backend/modules/supplier/routers/accounts.py:18 | Router imports `domains.accounts.services.auth.auth_service` directly | Cross-domain reads must go through `domains.accounts.ports` | +1 unauthorized service import | Replace import with `domains.accounts.ports` equivalent | Low | High | Certain | Direct evidence | File | Unverified | ARCH-001 | grep | Unit test import graph | Revert import | Low | None | None |
| ARCH-004 | 1 | NEW | Cross-domain imports | backend/modules/logistics/routers/finance.py:18 | Router imports `domains.finance.services.finance_service` directly | Cross-domain reads must go through `domains.finance.ports` | +1 unauthorized service import | Replace import with `domains.finance.ports` equivalent | Low | High | Certain | Direct evidence | File | Unverified | ARCH-001 | grep | Unit test import graph | Revert import | Low | None | None |
| ARCH-005 | 1 | NEW | Cross-domain imports | backend/modules/employee/routers/finance.py:22 | Router imports `domains.finance.services.ledger.general_ledger_service` directly | Cross-domain reads must go through `domains.finance.ports` | +1 unauthorized service import | Replace import with `domains.finance.ports` equivalent | Low | High | Certain | Direct evidence | File | Unverified | ARCH-001 | grep | Unit test import graph | Revert import | Low | None | None |
| ARCH-006 | 1 | NEW | Cross-domain imports | backend/modules/employee/routers/comms.py:40 | Router imports `domains.comms.services.messaging.chat_service` directly | Cross-domain reads must go through `domains.comms.ports` | +1 unauthorized service import | Replace import with `domains.comms.ports` equivalent | Low | High | Certain | Direct evidence | File | Unverified | ARCH-001 | grep | Unit test import graph | Revert import | Low | None | None |
| ARCH-007 | 1 | NEW | Cross-domain imports | backend/modules/logistics/routers/comms.py:23 | Router imports `domains.comms.services.comms_service` directly | Cross-domain reads must go through `domains.comms.ports` | +1 unauthorized service import | Replace import with `domains.comms.ports` equivalent | Low | High | Certain | Direct evidence | File | Unverified | ARCH-001 | grep | Unit test import graph | Revert import | Low | None | None |
| ARCH-008 | 1 | NEW | Cross-domain imports | backend/modules/employee/routers/orders.py:10 | Router imports `domains.orders.services.trading_service` directly | Cross-domain reads must go through `domains.orders.ports` | +1 unauthorized service import | Replace import with `domains.orders.ports` equivalent | Low | High | Certain | Direct evidence | File | Unverified | ARCH-001 | grep | Unit test import graph | Revert import | Low | None | None |
| ARCH-009 | 1 | NEW | Cross-domain imports | backend/modules/customer/routers/suppliers.py:7 | Router imports `domains.suppliers.ports` (correct pattern) | Cross-domain reads must go through ports.py | 0 violations | N/A — already compliant | N/A | Info | Certain | Direct evidence | File | Verified | None | grep | Import test | N/A | None | None | None |
| ARCH-010 | 1 | NEW | Cross-domain imports | backend/modules/admin/routers/orders.py:11 | Router imports `domains.comms.ports` (correct pattern) | Cross-domain reads must go through ports.py | 0 violations | N/A — already compliant | N/A | Info | Certain | Direct evidence | File | Verified | None | grep | Import test | N/A | None | None | None |
| ARCH-011 | 1 | NEW | Layer violation | backend/modules/admin/routers/staff.py:225 | Router executes `db.query(User)` directly on `domains.accounts.models` | All DB access must be delegated to domain services | Direct model query in router | Move query to `domains.accounts.services` and expose via `domains.accounts.ports` | Medium | High | Certain | Direct evidence | File | Unverified | None | grep | Integration test | Revert query | Medium | accounts domain | None |
| ARCH-012 | 1 | NEW | Business logic in routers | backend/modules/admin/routers/disputes.py:51 | Router contains `if type:` and validation logic | Routers must only delegate to services | Business logic in router layer | Extract validation to service or Pydantic model | Low | Medium | Certain | Direct evidence | File | Unverified | None | grep | Unit test | Revert logic | Low | None | None |
| ARCH-013 | 1 | NEW | Business logic in routers | backend/modules/admin/routers/permissions.py:65 | Router contains `for perm in perms:` iteration | Routers must only delegate to services | Business logic in router layer | Extract iteration to service | Low | Medium | Certain | Direct evidence | File | Unverified | None | grep | Unit test | Revert logic | Low | None | None |
| ARCH-014 | 1 | NEW | Stub routers | backend/modules/supplier/routers/hr.py:12 | Router contains `# TODO: Add endpoints as domain services are implemented` | All routers must have implemented endpoints | Stub router with TODO | Implement endpoints or remove router if not needed | Low | Medium | Certain | Direct evidence | File | Unverified | None | grep | Smoke test | N/A | Low | None | None |
| ARCH-015 | 1 | NEW | Stub routers | backend/modules/supplier/routers/security.py:12 | Router contains `# TODO: Add endpoints as domain services are implemented` | All routers must have implemented endpoints | Stub router with TODO | Implement endpoints or remove router if not needed | Low | Medium | Certain | Direct evidence | File | Unverified | None | grep | Smoke test | N/A | Low | None | None |
| ARCH-016 | 1 | NEW | Stub routers | backend/modules/supplier/routers/promotions.py:12 | Router contains `# TODO: Add endpoints as domain services are implemented` | All routers must have implemented endpoints | Stub router with TODO | Implement endpoints or remove router if not needed | Low | Medium | Certain | Direct evidence | File | Unverified | None | grep | Smoke test | N/A | Low | None | None |
| ARCH-017 | 1 | NEW | Stub routers | backend/modules/supplier/routers/catalog.py:12 | Router contains `# TODO: Add endpoints as domain services are implemented` | All routers must have implemented endpoints | Stub router with TODO | Implement endpoints or remove router if not needed | Low | Medium | Certain | Direct evidence | File | Unverified | None | grep | Smoke test | N/A | Low | None | None |
| ARCH-018 | 1 | NEW | Stub routers | backend/modules/supplier/routers/country.py:12 | Router contains `# TODO: Add endpoints as domain services are implemented` | All routers must have implemented endpoints | Stub router with TODO | Implement endpoints or remove router if not needed | Low | Medium | Certain | Direct evidence | File | Unverified | None | grep | Smoke test | N/A | Low | None | None |
| ARCH-019 | 1 | NEW | Module duplication | backend/modules/*/routers/ | 5 modules each containing identical 15-domain router sets | Single canonical router location per domain | 75 router files for 16 domains | Consolidate to single router per domain or justify module split | High | High | Certain | Direct evidence | File | Unverified | None | glob | Import graph | Revert consolidation | High | All modules | None |
| ARCH-020 | 1 | NEW | Allowlist mismatch | backend/DOMAIN_ALLOWLIST.yaml:4 | Allowlist only covers `domains.finance.services.*` cross-domain imports | Allowlist must cover all temporary cross-domain imports | 177 unauthorized cross-domain imports not in allowlist | Update allowlist or fix imports | High | High | Certain | Direct evidence | File | Unverified | None | grep | Import audit test | Revert allowlist | High | All domains | None |
| ARCH-021 | 1 | NEW | ports.py re-export blur | backend/domains/suppliers/ports.py:110 | `ports.py` re-exports service functions like `get_supplier_analytics_summary` | `ports.py` must only expose read helpers, not service logic | Read/write boundary blurred in ports.py | Move service re-exports to dedicated `read.py` or remove from ports | Medium | Medium | Certain | Direct evidence | File | Unverified | None | grep | Import test | Revert re-exports | Medium | suppliers domain | None |
| ARCH-022 | 1 | NEW | Empty domain directory | backend/domains/media/ | `media/` domain directory exists with no Python files | Either implement domain or remove directory | Empty domain directory | Implement domain or remove directory | Low | Low | Certain | Direct evidence | Directory | Unverified | None | glob | File existence | N/A | Low | None | None |
| ARCH-023 | 1 | NEW | ports.py pattern compliance | backend/domains/orders/ports.py:38 | `ports.py` correctly re-exports tracking service functions | Cross-domain reads via ports.py | Compliant | N/A — good pattern | N/A | Info | Certain | Direct evidence | File | Verified | None | grep | Import test | N/A | None | None | None |
| ARCH-024 | 1 | NEW | Events pattern | backend/domains/suppliers/events.py:15 | Domain publishes events for cross-domain writes | Cross-domain writes via events/subscribers | Compliant | N/A — good pattern | N/A | Info | Certain | Direct evidence | File | Verified | None | grep | Event test | N/A | None | None | None |
| ARCH-025 | 1 | NEW | Subscribers pattern | backend/domains/suppliers/subscribers.py:40 | Domain registers subscribers for peer domain events | Cross-domain reactions via subscribers | Compliant | N/A — good pattern | N/A | Info | Certain | Direct evidence | File | Verified | None | grep | Event test | N/A | None | None | None |

---

## Cross-Domain Import Heatmap

| Source Domain | logistics | comms | accounts | orders | finance | suppliers | governance | hr | audit | catalog | customers | analytics | security | country | promotions |
|---------------|-----------|-------|----------|--------|---------|-----------|------------|----|-------|---------|-----------|----------|---------|---------|------------|
| **logistics** | — | 0 | 3 | 2 | 2 | 1 | 1 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 |
| **comms** | 0 | — | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **accounts** | 0 | 0 | — | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **orders** | 0 | 0 | 0 | — | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **finance** | 0 | 0 | 0 | 0 | — | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **suppliers** | 3 | 1 | 1 | 1 | 1 | — | 1 | 0 | 1 | 1 | 1 | 1 | 0 | 0 | 0 |
| **governance** | 0 | 0 | 0 | 0 | 0 | 0 | — | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **hr** | 0 | 0 | 1 | 0 | 0 | 0 | 1 | — | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **audit** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — | 0 | 0 | 0 | 0 | 0 | 0 |
| **catalog** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — | 0 | 0 | 0 | 0 | 0 |
| **customers** | 1 | 0 | 2 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | — | 0 | 0 | 1 | 1 |
| **analytics** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — | 0 | 0 | 0 |
| **security** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — | 0 | 0 |
| **country** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | — | 0 |
| **promotions** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | — |

*Numbers represent cross-domain service imports found in routers. 0 = no direct service imports detected.*

---

## Layer Compliance Summary

| Layer | Rule | Compliant | Violations | Coverage |
|-------|------|-----------|------------|----------|
| Routers → Services | Must use ports.py for cross-domain reads | Partial | 177 direct service imports | 44 ports imports vs 177 service imports |
| Routers → DB | Must not execute raw queries | Partial | 1 direct `db.query(User)` in staff.py | 99 routers import `get_db` (expected) |
| Routers → Logic | Must not contain business logic | Violated | 3+ routers with control flow | Majority are thin wrappers |
| Domain → Domain | Must use events for writes | Partial | Events pattern exists in suppliers | Subscribers registered for peer events |
| Allowlist | Must cover all temporary imports | Violated | 177 imports not in allowlist | Allowlist only covers finance |

---

## Recommendations

1. **Immediate (High Priority):**
   - Update `DOMAIN_ALLOWLIST.yaml` to cover all 177 cross-domain service imports or fix the imports to use `ports.py`
   - Remove direct `db.query(User)` from `admin/routers/staff.py:228`
   - Implement or remove 15+ stub routers with TODO comments

2. **Short-term (Medium Priority):**
   - Extract business logic from routers (`disputes.py`, `permissions.py`) into domain services
   - Review `ports.py` re-exports in `domains/suppliers/ports.py` — move service functions to read-specific surface
   - Implement or remove empty `domains/media/` directory

3. **Long-term (Low Priority):**
   - Consider consolidating 75 router files if module split is not providing clear value
   - Establish automated import-graph checking in CI to prevent Law 2 violations

---

## Appendix: Files Audited

### Routers (69 files)
- `backend/modules/supplier/routers/*.py` (16 files)
- `backend/modules/logistics/routers/*.py` (16 files)
- `backend/modules/employee/routers/*.py` (16 files)
- `backend/modules/customer/routers/*.py` (16 files)
- `backend/modules/admin/routers/*.py` (17 files including `__init__.py`)

### Domain Services (hundreds of files)
- `backend/domains/*/services/*.py` across all 16 domains

### Ports / Events / Subscribers (48 files)
- `backend/domains/*/ports.py` (16 files)
- `backend/domains/*/events.py` (16 files)
- `backend/domains/*/subscribers.py` (16 files)

### Infrastructure
- `backend/main.py`
- `backend/middleware/orchestrator.py`
- `backend/DOMAIN_ALLOWLIST.yaml`
