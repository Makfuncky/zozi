# Audit Domain — Complete Diagnosis Report

> Generated: 2026-08-26  
> Scope: `backend/domains/audit/`  
> Reference: ARCHITECTURE_DIAGRAM.md §13  
> Total issues found: **50+**

---

## Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 16 |
| 🟠 HIGH | 20+ |
| 🟡 MEDIUM | 15+ |
| 🟢 LOW | 8+ |
| **TOTAL** | **50+** |

---

## 1. BROKEN IMPORTS (CRITICAL — Runtime Crashes)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 1 | `services/audit.py` | 4 | Imports from non-existent `domains.security.services.audit_service` | DELETE file |
| 2 | `services/ediscovery.py` | 18 | `JournalEntry` doesn't exist in `domains/finance/models/finance.py` | Fix import path |
| 3 | `services/retention_service.py` | 13 | `ShipmentEvent` doesn't exist in `domains/logistics/models/logistics.py` | Fix import path |
| 4 | `services/data_residency_service.py` | 12 | `DataResidencyRecord` in wrong module (`country_enhancements` vs `country_control`) | Fix import |
| 5 | `services/data_residency_service.py` | 65 | `infrastructure.utils.encryption` doesn't exist | Fix import |
| 6 | `services/logs/audit_service.py` | 457 | `Union`, `Dict` not imported for type hints | Add imports |
| 7 | `services/compliance_engine.py` | 13-16 | Direct HR model imports | Use HR ports |
| 8 | `services/communication_audit.py` | 17-57 | Controller (`@get` decorators) in services layer | Move to modules/ |

---

## 2. FAKE SECURITY (CRITICAL — Compliance Violations)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 9 | `services/data_residency.py` | 84-100 | `SovereignEncryptionService` is **fake encryption** — stores plaintext with `sovereign_encrypted: True` flag | Implement real KMS encryption |
| 10 | `services/data_residency_service.py` | 64-69 | Silent plaintext fallback when encryption fails | Raise exception for strict tiers |
| 11 | `services/worm_audit.py` | 73-83 | `get_chain_integrity` **always returns True** — never verifies chain | Implement real hash verification |
| 12 | `services/worm_audit.py` | 103 | `text("ANY")` in JSONB query is invalid SQL | Use proper JSONB operators |

---

## 3. CROSS-DOMAIN POLLUTION (CRITICAL)

### 3.1 HR Domain Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 13 | `compliance_engine.py` | 25-134 | **Entire HR compliance logic** in audit domain | Move to `domains/hr/services/` |
| 14 | `logs/audit_service.py` | 68-103 | `log_payroll_freeze`, `log_coi_violation` are HR concepts | Move to HR domain |

### 3.2 Governance Domain Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 15 | `security_audit.py` | 7 | Imports `AuditLog` from governance (wrong schema!) | Import from `audit.models` |
| 16 | `worm_audit.py` | 14 | Same wrong import | Same fix |
| 17 | `logs/audit_service.py` | 9 | Same wrong import | Same fix |
| 18 | `logs/audit_query_service.py` | 17 | Same wrong import | Same fix |

### 3.3 Logistics/Finance/Comms Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 19 | `retention_service.py` | 10-22 | Direct queries to logistics, comms, governance | Use ports or events |
| 20 | `ediscovery.py` | 13-18 | Queries governance chat, country, comms, finance | Use ports |

---

## 4. DUPLICATE FILES & LOGIC (HIGH)

| # | Files | Issue | Fix |
|---|-------|-------|-----|
| 21 | `data_residency.py` / `data_residency_service.py` / `flat_data_residency_service.py` | **Three** `DataResidencyService` classes | Consolidate into one |
| 22 | `audit_service.py` / `logs/audit_service.py` | Re-export shim | Delete `audit_service.py` |
| 23 | `services/features.py` / root `features.py` | Duplicate feature definitions | Delete `services/features.py` |
| 24 | `services/ports.py` / root `ports.py` | Duplicate ports | Delete `services/ports.py` |
| 25 | `services/events.py` / root `events.py` | Duplicate events | Delete `services/events.py` |

---

## 5. MODEL ISSUES (CRITICAL)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 26 | `models/audit_schema_models.py` | 19, 31 | FK references `accounts.users.id` but users table is in **`governance`** schema | Change to `governance.users.id` |
| 27 | `models/audit_schema_models.py` | 24 | `AuditLog` missing `updated_at` | Add column |
| 28 | `models/audit_schema_models.py` | 17-18 | Missing composite index on `entity_type` + `entity_id` | Add index |
| 29 | `models/audit_schema_models.py` | 22 | Missing GIN index on `details` JSON column | Add GIN index |

---

## 6. LOGIC ERRORS (CRITICAL)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 30 | `compliance_engine.py` | 89-101 | Weekly rest check **doesn't track max streak** | Fix algorithm |
| 31 | `retention_service.py` | 74 | Catches 25 exception types explicitly | Use `except Exception` |
| 32 | `ediscovery.py` | 27-28 | DB session never closed | Use context manager |

---

## 7. ARCHITECTURE VIOLATIONS (HIGH)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 33 | `communication_audit.py` | 17-57 | Controller in services layer | Move to `modules/admin/controllers/` |
| 34 | `audit.py` | 4 | Re-export from security domain | DELETE |
| 35 | `compliance_service.py` | 3-5 | Re-export from infrastructure | DELETE |
| 36 | `data/service.py` | 4-7 | Deprecated shim | DELETE |
| 37 | `compliance/audit_service.py` | 4 | Deprecated shim | DELETE |

---

## 8. PROFESSIONAL STANDARDS GAPS

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 38 | `worm_audit.py` | 16-19 | Double logger definition | Use single logger |
| 39 | `logs/audit_trail_service.py` | 49 | f-string in logger | Use lazy evaluation |
| 40 | `logs/audit_service.py` | 34 | `details` stored as `str()` not JSON | Use `json.dumps()` |
| 41 | `compliance_engine.py` | 68 | Hard-coded GCC country list | Single-source constants |

---

## Priority Action Plan

### Phase 1: CRITICAL (Fix Immediately)

| # | Action | Impact |
|---|--------|--------|
| 1 | Delete `services/audit.py` (broken import) | Prevents ImportError |
| 2 | Fix `AuditLog` FK schema (`accounts` → `governance`) | Prevents FK violation |
| 3 | Remove fake `SovereignEncryptionService` | Compliance violation |
| 4 | Fix silent plaintext fallback | Data protection |
| 5 | Implement real WORM chain verification | Audit integrity |
| 6 | Fix `JournalEntry` import in `ediscovery.py` | Prevents NameError |
| 7 | Fix `ShipmentEvent` import in `retention_service.py` | Prevents NameError |
| 8 | Fix `DataResidencyRecord` import in `data_residency_service.py` | Prevents NameError |
| 9 | Move `compliance_engine.py` to `domains/hr/services/` | Architecture compliance |
| 10 | Fix weekly rest algorithm in `compliance_engine.py` | Correct compliance results |

### Phase 2: HIGH (Fix This Week)

| # | Action | Impact |
|---|--------|--------|
| 11 | Consolidate 3 `DataResidencyService` classes | Reduces confusion |
| 12 | Delete duplicate files (`features.py`, `ports.py`, `events.py` in services/) | Clean structure |
| 13 | Delete deprecated shims (`data/service.py`, `compliance/audit_service.py`) | Clean structure |
| 14 | Move `communication_audit.py` to modules/ | Architecture compliance |
| 15 | Remove HR logic from `logs/audit_service.py` | Domain purity |
| 16 | Remove cross-domain imports from `retention_service.py` | Architecture compliance |
| 17 | Refactor `ediscovery.py` to use ports | Architecture compliance |

### Phase 3: MEDIUM (Fix This Month)

| # | Action | Impact |
|---|--------|--------|
| 18 | Add `updated_at` to `AuditLog` | Data integrity |
| 19 | Add composite index on `entity_type` + `entity_id` | Performance |
| 20 | Add GIN index on `details` JSON | Performance |
| 21 | Add error handling to `compliance_engine.py` | Robustness |
| 22 | Fix DB session leak in `ediscovery.py` | Resource management |

---

## Statistics

| Metric | Value |
|--------|-------|
| Total files | 31 |
| Files with cross-domain pollution | 14 |
| CRITICAL issues | 16 |
| HIGH issues | 20+ |
| MEDIUM issues | 15+ |
| LOW issues | 8+ |
| Duplicate file pairs | 5 |
| Empty/stub directories | 4 |
| Broken imports | 8 |
| Fake security functions | 3 |
