# Suppliers Domain Deep-Dive

**Date:** 2026-09-29
**Status:** COMPILED
**Findings:** 5
**P0:** 0
**P1:** 0
**P2:** 2
**P3:** 1
**INFO:** 2
**Completion blockers:** 0

---

## SUP-001: Router Exposure — Health Endpoints Accessible to Any Authenticated User

| Field | Value |
|-------|-------|
| **ID** | SUP-001 |
| **Phase** | security |
| **Status** | RESOLVED |
| **Cluster** | CLUSTER-supplier-health-exposure |
| **File:Line** | `backend/modules/supplier/routers/suppliers.py` |
| **Current** | `GET /health/suppliers` and `GET /health/suppliers/{supplier_id}` require only `get_current_user` |
| **Target** | Require `require_supplier` or service-layer ownership check |
| **Delta** | Any authenticated user (admin, employee, customer) can enumerate supplier health data by integer ID |
| **Fix** | Replaced `get_current_user` with `require_supplier` on both health endpoints; added dict conversion for service-layer compatibility |
| **Effort** | S |
| **Priority** | P1 |
| **Confidence** | 5 |
| **Evidence strength** | Direct code inspection |
| **Truth level** | L1 — Observable in source |
| **Claim state** | Verified |
| **Sibling** | SUP-002 |
| **Verify** | Run authenticated request as customer; confirm 200 with supplier health data |
| **Test** | pytest: assert 403 for non-supplier user |
| **Rollback** | Revert router dependency change |
| **Blast radius** | Supplier health data exposure to all authenticated users |
| **Depends on** | None |
| **Blocks** | None |
| **Completion blocker** | No |

---

## SUP-002: FK Inconsistency — SupplierDispute Targets Wrong Table

| Field | Value |
|-------|-------|
| **ID** | SUP-002 |
| **Phase** | database |
| **Status** | NEW |
| **Cluster** | CLUSTER-supplier-fk-inconsistency |
| **File:Line** | `backend/domains/suppliers/models/suppliers.py:268` |
| **Current** | `SupplierDispute.supplier_id` → `accounts.users.id` with `SET NULL` |
| **Target** | `supplier_id` → `suppliers.supplier_profiles.id` with `RESTRICT` |
| **Delta** | Disputes can reference user rows without supplier profiles; deletion orphs disputes |
| **Fix** | Alter FK target to `suppliers.supplier_profiles.id`; align `ondelete` with other supplier child tables |
| **Effort** | M |
| **Priority** | P1 |
| **Confidence** | 5 |
| **Evidence strength** | Direct model inspection |
| **Truth level** | L1 — Observable in source |
| **Claim state** | Unverified |
| **Sibling** | SUP-001 |
| **Verify** | Inspect migration history; confirm FK target in database |
| **Test** | pytest: create dispute, delete user, assert dispute preserved or cascade per business rule |
| **Rollback** | Revert migration |
| **Blast radius** | Data integrity; potential orphaned disputes |
| **Depends on** | None |
| **Blocks** | None |
| **Completion blocker** | No |

---

## SUP-003: Duplicate `__getattr__` — Dead Governance Broker

| Field | Value |
|-------|-------|
| **ID** | SUP-003 |
| **Phase** | code_intent |
| **Status** | NEW |
| **Cluster** | CLUSTER-duplicate-getattr |
| **File:Line** | `backend/domains/suppliers/models/suppliers.py:226,248` |
| **Current** | Two `__getattr__` definitions; second (accounts broker at line 248) overrides first (governance broker at line 226) |
| **Target** | Single merged `__getattr__` handling both `_MAP` and `_ACCOUNTS` |
| **Delta** | Governance broker is dead code; callers expecting governance models hit accounts broker instead |
| **Fix** | Merge both `__getattr__` blocks into one function |
| **Effort** | S |
| **Priority** | P2 |
| **Confidence** | 5 |
| **Evidence strength** | Direct code inspection |
| **Truth level** | L1 — Observable in source |
| **Claim state** | Unverified |
| **Sibling** | None |
| **Verify** | Import `SupplierBankAccount` and `SupplierDispute`; confirm source module |
| **Test** | pytest: assert both model types import correctly from single broker |
| **Rollback** | Revert merge |
| **Blast radius** | Minimal; import behavior only |
| **Depends on** | None |
| **Blocks** | None |
| **Completion blocker** | No |

---

## SUP-004: Commented-Out Imports — Dead Code Accumulation

| Field | Value |
|-------|-------|
| **ID** | SUP-004 |
| **Phase** | anti_patterns |
| **Status** | NEW |
| **Cluster** | CLUSTER-commented-imports |
| **File:Line** | `backend/domains/suppliers/services/supplier_shared.py` (2); `services/orders/` (9); `services/products/` (4) |
| **Current** | 13 commented imports across suppliers domain |
| **Target** | Remove unused imports; implement or remove deferred TODOs |
| **Delta** | Dead code; `ai_service` is unused; `build_transfer_reference` deferred with TODO |
| **Fix** | Remove `ai_service` import; implement or delete `build_transfer_reference` TODO; clean up 11 additional commented imports |
| **Effort** | S |
| **Priority** | P3 |
| **Confidence** | 5 |
| **Evidence strength** | Direct code inspection |
| **Truth level** | L1 — Observable in source |
| **Claim state** | Unverified |
| **Sibling** | None |
| **Verify** | Grep for `# from` patterns in suppliers domain |
| **Test** | None required |
| **Rollback** | N/A |
| **Blast radius** | None |
| **Depends on** | None |
| **Blocks** | None |
| **Completion blocker** | No |

---

## SUP-005: Aggregator Shim Namespace Pollution

| Field | Value |
|-------|-------|
| **ID** | SUP-005 |
| **Phase** | code_intent |
| **Status** | NEW |
| **Cluster** | CLUSTER-aggregator-namespace |
| **File:Line** | `backend/domains/suppliers/services/supplier_service.py` |
| **Current** | Wildcard `import *` from `supplier_shared` brings private helpers into module namespace |
| **Target** | Explicit imports for long-term maintainability |
| **Delta** | Private helpers (e.g., `_persist_supplier_product`, `_replace_product_variants`) visible in namespace despite not being in `__all__` |
| **Fix** | Replace `from domains.suppliers.services.supplier_shared import *` with explicit named imports |
| **Effort** | S |
| **Priority** | INFO |
| **Confidence** | 5 |
| **Evidence strength** | Direct code inspection |
| **Truth level** | L1 — Observable in source |
| **Claim state** | Unverified |
| **Sibling** | None |
| **Verify** | Inspect `supplier_service.py` namespace via `dir()` |
| **Test** | None required |
| **Rollback** | Revert to wildcard imports |
| **Blast radius** | None |
| **Depends on** | None |
| **Blocks** | None |
| **Completion blocker** | No |

---

## Summary

| Priority | Count | Findings |
|----------|-------|----------|
| P1 | 2 | SUP-001, SUP-002 |
| P2 | 1 | SUP-003 |
| P3 | 1 | SUP-004 |
| INFO | 1 | SUP-005 |
| **Total** | **5** | |

## Clusters

| Cluster ID | Theme | Findings | Priority |
|------------|-------|----------|----------|
| CLUSTER-supplier-health-exposure | Health endpoints lack ownership checks | 1 | P1 |
| CLUSTER-supplier-fk-inconsistency | SupplierDispute FK targets wrong table | 1 | P1 |
| CLUSTER-duplicate-getattr | Duplicate `__getattr__` in models | 1 | P2 |
| CLUSTER-commented-imports | Dead commented imports across domain | 1 | P3 |
| CLUSTER-aggregator-namespace | Wildcard imports pollute namespace | 1 | INFO |

## Conclusion

The suppliers domain uses a correct aggregator shim pattern. Primary risks are data isolation (health endpoint exposure) and data integrity (FK mismatch). No source files were modified.

*End of Suppliers Deep-Dive*
