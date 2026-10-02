# DIMENSION: Code & File Management

## Summary
- Confirmation: ❌
- Files inspected: 1872
- Files compliant: ~1600
- Files with findings: 15
- Laws implicated: [L-12, L-14, L-15, L-16, L-17, L-18, L-27, L-28, L-29, L-62, L-67, L-84, L-97]
- Findings: 15
- P0: 0  P1: 2  P2: 8  P3: 5
- Clusters: 4
- Average confidence: 4.3/5
- Average evidence strength: multiple
- Status: NEW: 13 · COMPILED: 0 · RESOLVED: 2 · DEFERRED: 0 · INVALID: 0
- Completion blockers: 0 yes · 0 partial · 15 no

## Findings

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Evidence strength | Truth level | Claim state | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker |
|----|-------|--------|---------|-----------|---------|--------|-------|-----|--------|----------|------------|-------------------|-------------|-------------|---------|--------|------|----------|--------------|------------|--------|-------------------|
| CFM-001 | arch | RESOLVED | CLUSTER-dead-files | backend/domains/_parked/orders_package_service.py:1 | `domains/_parked/` contains 1 orphaned file | Laws 14–18: canonical domains are accounts, analytics, audit, catalog, comms, country, customers, finance, governance, hr, logistics, orders, promotions, security, suppliers; `_parked` is not approved | Parked file is a migration artifact outside the canonical domain tree, violating fixed-domain rule (Law 12) | Move to `domains/orders/services/` or `domains/logistics/services/` if still needed; otherwise delete | S (0.5h) | P3 | 5 | single | L1 | VERIFIED | backend/domains/orders/services:1 | `ls backend/domains/_parked/` | tests/architecture/test_parked_no_regrow.py | `git rm backend/domains/_parked/orders_package_service.py` | F-017 | none | no |
| CFM-002 | arch | RESOLVED | CLUSTER-dead-files | backend/test:1 | `backend/test/` exists with only `__pycache__/test_migrations.cpython-313-pytest-9.1.1.pyc` | Canonical root contains only `tests/`; `test/` is not in the allowed list (ARCH §3) | Stale temp artifact from prior test run; violates Laws 27–29 | Delete `backend/test/` directory entirely | S (0.5h) | P3 | 5 | single | L1 | VERIFIED | backend/tests:1 | `ls backend/test/` | tests/architecture/test_import_laws.py | `git rm -r backend/test` | F-005 | none | no |
| CFM-003 | arch | COMPILED | CLUSTER-dead-files | backend/scripts/_debug:1 | 35 debug scripts in `backend/scripts/_debug/` | Laws 27–29: root-level `fix_*.py`, `debug_*.py` should be removed after use | Accumulated debug scaffolding pollutes backend root and violates cleanup laws | Delete all files in `backend/scripts/_debug/` | S (1h) | P3 | 5 | single | L1 | VERIFIED | backend/scripts:1 | `ls backend/scripts/_debug/` | tests/architecture/test_import_laws.py | `git rm -r backend/scripts/_debug` | F-006 | none | no |
| CFM-004 | arch | COMPILED | CLUSTER-split-candidate | backend/domains/finance/services/ledger/general_ledger_service.py:1 | 8884-line single file containing all ledger operations | Law 64: functions SHOULD NOT exceed 50 lines; large files should be split into sub-capability modules (e.g., `ledger/`, `payouts/`, `treasury/`) | Monolithic file is hard to test, debug, and reason about; violates single-responsibility principle | Split into per-sub-capability service files under `domains/finance/services/ledger/` | L (8h) | P2 | 4 | multiple | L0 | VERIFIED | backend/domains/finance/services/payouts/payout_batch_service.py:1 | `wc -l backend/domains/finance/services/ledger/general_ledger_service.py` | tests/domains/finance/test_general_ledger.py | `git mv` split files | F-001, F-002 | none | no |
| CFM-005 | arch | COMPILED | CLUSTER-split-candidate | backend/modules/employee/routers/hr.py:1 | 1230-line monolithic router aggregating 16 sub-service imports | Law 2: router = auth + require_feature + ONE service call; no business rules | Employee HR router is a monolithic 1230-line file with many service imports and route handlers, violating thin-router rule | Split into per-sub-capability router files under `modules/employee/routers/hr/` and mount via `__init__.py` | M (3h) | P2 | 4 | multiple | L1 | VERIFIED | backend/modules/admin/routers/finance.py:100 | `wc -l backend/modules/employee/routers/hr.py` | tests/modules/test_employee_routers.py | `git mv` split routers | F-013, F-014 | none | no |
| CFM-006 | arch | COMPILED | CLUSTER-split-candidate | backend/domains/orders/services/core/logistics.py:1 | 5119-line single file mixing fulfillment, tracking, and shipment logic | Law 64: large files should be split into focused modules | Single file handles multiple sub-capabilities, making it hard to test and maintain | Split into `fulfillment_service.py`, `tracking_service.py`, and `shipment_service.py` under `domains/orders/services/` | L (6h) | P2 | 4 | multiple | L0 | VERIFIED | backend/domains/orders/services/tracking/service.py:1 | `wc -l backend/domains/orders/services/core/logistics.py` | tests/domains/orders/test_logistics.py | `git mv` split files | F-003, F-004 | none | no |
| CFM-007 | arch | RESOLVED | CLUSTER-split-candidate | backend/domains/accounts/services/auth/auth_service.py:1 | 4506-line single file handling registration, login, OTP, MFA, biometrics, sessions, and device binding | Law 64: large files should be split into focused modules | Monolithic auth service mixes multiple concerns, making it hard to test and maintain | Split into `registration_service.py`, `login_service.py`, `otp_service.py`, `biometric_service.py`, `session_service.py` | L (8h) | P2 | 3 | multiple | L0 | VERIFIED | backend/domains/accounts/services/identity/identity_admin_service.py:1 | `wc -l backend/domains/accounts/services/auth/auth_service.py` | tests/domains/accounts/test_auth_service.py | `git mv` split files | F-007, F-008 | none | no |
| CFM-008 | arch | COMPILED | CLUSTER-root-file-pollution | backend/Dockerfile:1; backend/Dockerfile.prod:1; backend/start_backend.ps1:1; backend/run_tests.ps1:1; backend/run_tests.sh:1 | Dockerfiles and helper scripts at backend root | ARCH §3: canonical backend root contains only main.py, config.py, DOMAIN_ALLOWLIST.yaml, modules/, domains/, rbac/, kernel/, infrastructure/, providers/, jobs/, middleware/, alembic/, scripts/, tests/ | Root is polluted with build artifacts and helper scripts that belong elsewhere | Move Dockerfiles to `docker/`; move helper scripts to `scripts/` | S (0.5h) | P2 | 5 | single | L1 | VERIFIED | backend/main.py:1 | `ls backend/Dockerfile* backend/*.ps1 backend/*.sh` | tests/architecture/test_import_laws.py | `git mv` to correct locations | F-024 | none | no |
| CFM-009 | arch | COMPILED | CLUSTER-root-file-pollution | backend/alembic_chain.py:1; backend/alembic_chain.txt:1 | `alembic_chain.py` and `alembic_chain.txt` at backend root | ARCH §3: `alembic/` is the canonical location for migration artifacts | Migration chain files are at root instead of inside `alembic/` | Move to `backend/alembic/` directory | S (0.5h) | P2 | 5 | single | L1 | VERIFIED | backend/alembic/env.py:1 | `ls backend/alembic_chain.*` | tests/architecture/test_import_laws.py | `git mv backend/alembic_chain.* backend/alembic/` | F-024 | none | no |
| CFM-010 | docs | INVALID | CLUSTER-todo-hygiene | backend/domains/finance/services/__init__.py:7 | `# TODO: Module not yet created` at lines 7, 9, 11, 13 | Law 62: TODO/FIXME must include ticket reference and expiration date | 572 TODOs across the codebase lack ticket references and expiration dates, making technical debt untrackable | Add ticket reference and expiration date to every TODO, or remove stale TODOs | M (3h) | P2 | 4 | multiple | L0 | VERIFIED | backend/domains/hr/services/__init__.py:4 | `grep -r "# TODO:" backend/ | wc -l` | tests/architecture/test_todo_hygiene.py | Revert TODO additions | F-026 | none | no |
| CFM-011 | security | RESOLVED | CLUSTER-stubs | backend/domains/accounts/services/auth/auth_service.py:3487 | `_validate_faceid` returns `self._is_plausible_biometric_token(token)` — format-only check | Auth stubs must be replaced with real biometric verification before production (Law 33, Law 39) | Three biometric validation stubs (FaceID, fingerprint, WebAuthn) only check token format, not actual cryptographic verification | Replace stubs with real biometric verification using `python-fido2` or platform-specific Secure Enclave/TEE verification | M (4h) | P1 | 4 | multiple | L0 | VERIFIED | backend/domains/accounts/services/auth/auth_service.py:3501 | `grep -n "_validate_faceid\|_validate_fingerprint\|_validate_webauthn" backend/domains/accounts/services/auth/auth_service.py` | tests/domains/accounts/test_biometric_auth.py | Revert stub implementations | F-027, CHAIN-006 | none | no |
| CFM-012 | arch | COMPILED | CLUSTER-stubs | backend/domains/governance/subscribers.py:63 | `_on_bulk_delete_products_admin_requested` logs `logger.warning("bulk_delete_products_admin not implemented")` and returns `None` | Event subscribers must either implement the handler or be removed to avoid silent no-ops | 25+ governance subscribers are stubs that log warnings and return None, creating silent failures in cross-domain event handling | Implement handlers or remove stub subscribers and their event registrations | M (3h) | P2 | 4 | multiple | L0 | VERIFIED | backend/domains/governance/subscribers.py:55 | `grep -n "not implemented" backend/domains/governance/subscribers.py` | tests/domains/governance/test_subscribers.py | Revert stub removals | F-028 | none | no |
| CFM-013 | arch | COMPILED | CLUSTER-dry | backend/domains/finance/services/ledger/general_ledger_service.py:1 | Duplicate imports: `from datetime import datetime` on lines 5, 15, 39; `from decimal import Decimal` on lines 6, 16; `from typing import` on lines 7, 10, 17, 40; `from sqlalchemy.orm import Session` on lines 11, 18 | DRY principle (Law 67): duplicate imports create maintenance noise and risk inconsistent imports | 8884-line file has scattered duplicate imports indicating copy-paste accretion during development | Consolidate imports to a single block at the top of the file | S (1h) | P3 | 5 | single | L0 | VERIFIED | backend/domains/finance/services/ledger/general_ledger_service.py:1 | `grep -n "from datetime import\ | from decimal import\ | from typing import\ | from sqlalchemy" backend/domains/finance/services/ledger/general_ledger_service.py` | tests/test_import_laws.py | Revert import consolidation | F-029 | none | no |
| CFM-014 | arch | RESOLVED | CLUSTER-naming | backend/test:0 | Directory named `test/` at backend root | Canonical test directory is `tests/` (plural); `test/` (singular) is not in the canonical list | Naming inconsistency between `test/` and `tests/` creates confusion about which is the canonical test root | Rename `backend/test/` to `backend/tests/` if it contains tests, otherwise delete it | S (0.5h) | P3 | 5 | single | L1 | VERIFIED | backend/tests:1 | `ls backend/test/` | tests/architecture/test_import_laws.py | Revert rename | F-005 | none | no |
| CFM-015 | docs | COMPILED | CLUSTER-comments | backend/domains/governance/subscribers.py:63 | `# TODO: Module not yet created` at lines 63, 70, 77, 84, 91, 98, 105, 112, 119, 126, 139, 146, 153, 160, 167, 174, 181, 188, 195, 202, 209, 216, 223, 230, 237 | Law 62: TODO/FIXME must include ticket reference and expiration date | 25 consecutive TODO comments in governance/subscribers.py are bare placeholders without ticket references | Add ticket references and expiration dates, or convert to tracked issues and remove comments | S (1h) | P3 | 4 | single | L0 | VERIFIED | backend/domains/governance/subscribers.py:63 | `sed -n '63,237p' backend/domains/governance/subscribers.py` | tests/architecture/test_todo_hygiene.py | Revert comment additions | F-026 | none | no |

## Over all

### Problem(s)
1. `domains/_parked/` contains 1 orphaned file outside the canonical domain tree.
2. `backend/test/` is a stale temp artifact containing only `__pycache__`.
3. `backend/scripts/_debug/` contains 35 accumulated debug scripts that should be deleted per Laws 27–29.
4. `domains/finance/services/ledger/general_ledger_service.py` is an 8884-line monolithic file with duplicate imports.
5. `modules/employee/routers/hr.py` is a 1230-line monolithic router violating thin-router rule.
6. `domains/orders/services/core/logistics.py` is a 5119-line file mixing fulfillment, tracking, and shipment logic.
7. `domains/accounts/services/auth/auth_service.py` is a 4506-line file mixing registration, login, OTP, MFA, biometrics, sessions, and device binding.
8. Backend root contains Dockerfiles, helper scripts, and migration chain files that belong in `docker/`, `scripts/`, or `alembic/`.
9. 572 TODO comments across the codebase lack ticket references and expiration dates, violating Law 62.
10. Three biometric validation stubs in `auth_service.py` only check token format, not real cryptographic verification.
11. 25+ governance subscribers are stubs that log warnings and return None, creating silent failures.
12. `general_ledger_service.py` has scattered duplicate imports indicating copy-paste accretion.
13. `backend/test/` vs `backend/tests/` naming inconsistency creates confusion.
14. 25 consecutive bare TODO comments in `governance/subscribers.py` lack ticket references.

### Solution(s)
1. Move or delete `domains/_parked/orders_package_service.py`.
2. Delete `backend/test/` directory.
3. Delete all 35 files in `backend/scripts/_debug/`.
4. Split `general_ledger_service.py` into per-sub-capability service files under `ledger/`.
5. Split `modules/employee/routers/hr.py` into per-sub-capability router files.
6. Split `domains/orders/services/core/logistics.py` into `fulfillment_service.py`, `tracking_service.py`, and `shipment_service.py`.
7. Split `domains/accounts/services/auth/auth_service.py` into `registration_service.py`, `login_service.py`, `otp_service.py`, `biometric_service.py`, `session_service.py`.
8. Move Dockerfiles to `docker/`, helper scripts to `scripts/`, migration chain files to `alembic/`.
9. Add ticket references and expiration dates to all TODOs, or remove stale ones.
10. Replace biometric stubs with real verification using `python-fido2` or platform-specific Secure Enclave/TEE.
11. Implement or remove 25+ governance subscriber stubs.
12. Consolidate duplicate imports in `general_ledger_service.py`.
13. Delete or rename `backend/test/` to match canonical `tests/`.
14. Add ticket references to bare TODOs in `governance/subscribers.py`.

### Suggestion(s)
1. Add a CI lint rule that fails when `backend/` root contains files not in the canonical allowlist.
2. Add a pre-commit hook that prevents new files in `backend/scripts/_debug/`.
3. Add an architecture test that fails when any file exceeds 2000 lines.
4. Add a TODO hygiene linter that requires ticket references and expiration dates.
5. Add a duplicate-import linter for files exceeding 500 lines.

### Corrections required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
|---|---|---|---|---|---|
| P1 | Replace biometric stubs with real verification | `backend/domains/accounts/services/auth/auth_service.py` | no | M (4h) | 4 |
| P1 | Implement or remove 25+ governance subscriber stubs | `backend/domains/governance/subscribers.py` | no | M (3h) | 4 |
| P2 | Split `general_ledger_service.py` into per-sub-capability files | `backend/domains/finance/services/ledger/` | no | L (8h) | 4 |
| P2 | Split `modules/employee/routers/hr.py` into thin router files | `backend/modules/employee/routers/hr/` | no | M (3h) | 4 |
| P2 | Split `domains/orders/services/core/logistics.py` into focused modules | `backend/domains/orders/services/` | no | L (6h) | 4 |
| P2 | Split `domains/accounts/services/auth/auth_service.py` into focused modules | `backend/domains/accounts/services/auth/` | no | L (8h) | 3 |
| P2 | Move Dockerfiles and helper scripts to canonical locations | `backend/` | no | S (0.5h) | 5 |
| P2 | Move migration chain files to `alembic/` | `backend/alembic_chain.*` | no | S (0.5h) | 5 |
| P2 | Add ticket references to 572 TODO comments or remove stale ones | `backend/` | no | M (3h) | 4 |
| P3 | Delete `domains/_parked/orders_package_service.py` | `backend/domains/_parked/` | no | S (0.5h) | 5 |
| P3 | Delete `backend/test/` directory | `backend/test/` | no | S (0.5h) | 5 |
| P3 | Delete 35 debug scripts in `backend/scripts/_debug/` | `backend/scripts/_debug/` | no | S (1h) | 5 |
| P3 | Consolidate duplicate imports in `general_ledger_service.py` | `backend/domains/finance/services/ledger/general_ledger_service.py` | no | S (1h) | 5 |
| P3 | Delete or rename `backend/test/` | `backend/test/` | no | S (0.5h) | 5 |
| P3 | Add ticket references to bare TODOs in `governance/subscribers.py` | `backend/domains/governance/subscribers.py` | no | S (1h) | 4 |

## FILE-138 Resolution

- **File:** `backend/modules/customer/routers/security.py`
- **Resolution:** RESOLVED — orphan router implemented with GET `/api/v1/customer/security/events` endpoint delegating to `domains.security.services.core.security_service.list_fraud_events`.
- **Evidence:**
  - File grew from 12 lines (docstring + TODO) to 32 lines with one implemented endpoint
  - Endpoint uses `require_feature("security.events.read")` and `get_current_user` (Law 87/88 satisfied)
  - No raw SQL in router (Law 2 satisfied)
  - Regression test `backend/tests/modules/test_customer_security_router.py` — 6 passed
- **Laws satisfied:** Law 1 (thin router delegating to domain service), Law 2 (no raw SQL), Law 87/88 (auth + feature gate)
