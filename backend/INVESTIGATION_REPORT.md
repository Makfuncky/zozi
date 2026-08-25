# ZOZI Backend — Detailed Investigation Report

> Generated: 2026-08-25
> Scope: Complete backend codebase audit — architecture, broken imports, structural issues

---

## 1 · Executive Summary

| Metric | Value |
|--------|-------|
| **Total broken import statements** | ~2,253 |
| **Critical blockers (app won't start)** | 7 |
| **Router files (current)** | 476 across 5 modules |
| **Router files (target — Phase 19)** | 75 (15 per module) |
| **Unregistered router files** | 149 (exist on disk, never imported) |
| **Domain service files** | 517 across 15 domains |
| **Missing third-party packages** | ~20 |
| **Domains with broken service imports** | 12 of 15 |

**The app currently cannot start** due to a single cascade failure in `middleware/country_context.py:39`.

---

## 2 · Architecture Overview

### 2.1 Three Orthogonal Axes (as designed)

| Axis | What | Where | Count |
|------|------|-------|-------|
| **Module** (who) | admin, customer, employee, logistics, supplier | `modules/{m}/` | 5 |
| **Domain** (what) | accounts, analytics, audit, catalog, comms, country, customers, finance, governance, hr, logistics, orders, promotions, security, suppliers | `domains/{d}/` | 15 |
| **Feature** (may) | Permission atoms | `rbac/` + `domains/*/features.py` | 1 |

> **Note:** `media` is a **provider** (already in `providers/media/`), not a domain. `infrastructure` is a **platform layer** (top-level `infrastructure/`), not a domain. Neither appears in the domain count.

### 2.2 Current Router Structure (Problematic)

| Module | Router Files | Registered | Unregistered | Status |
|--------|-------------|------------|--------------|--------|
| admin | 270 | 228 | 42 | Bloated — should be 15 |
| customer | 44 | 12 | 32 | Scattered |
| employee | 80 | 50 | 30 | Scattered |
| logistics | 32 | 12 | 20 | Scattered |
| supplier | 50 | 25 | 25 | Scattered |
| **TOTAL** | **476** | **327** | **149** | **Target: 75** |

### 2.3 Target Router Structure (Phase 19)

Each module gets exactly 15 domain router files:
```
modules/{m}/routers/
├── accounts.py      analytics.py     audit.py
├── catalog.py       comms.py         country.py
├── customers.py     finance.py       governance.py
├── hr.py            logistics.py     orders.py
├── promotions.py    security.py      suppliers.py
└── __init__.py
```

---

## 3 · Critical Blockers (App Won't Start)

These 7 broken imports prevent the entire application from booting:

### 3.1 `middleware/country_context.py:39`
```python
from domains.hr.services.coi_service import check_approval_blocked
```
- **Error:** `ModuleNotFoundError: No module named 'domains.hr.services.coi_service'`
- **Actual location:** `domains/hr/services/employees/coi_service.py` (function at line 98)
- **Fix:** Change to `from domains.hr.services.employees.coi_service import check_approval_blocked`

### 3.2 `middleware/coi_middleware.py:10`
```python
from domains.hr.services.coi_service import COIService
```
- **Error:** Same wrong path
- **Fix:** Change to `from domains.hr.services.employees.coi_service import COIService`

### 3.3 `middleware/dependencies/coi_dependency.py:10`
```python
from domains.hr.services.coi_service import COIService
```
- **Error:** Same wrong path
- **Fix:** Change to `from domains.hr.services.employees.coi_service import COIService`

### 3.4 `middleware/impossible_travel_middleware.py:156`
```python
from domains.governance.services.security.impossible_travel_write_service import log_impossible_travel_lock
```
- **Error:** Module doesn't exist AND function doesn't exist anywhere in codebase
- **Fix:** Implement the function or remove the import and runtime call

### 3.5 `middleware/impossible_travel_middleware.py:349`
```python
from domains.governance.services.fraud.fraud_detection_service import FraudScoringEngine
```
- **Error:** `ModuleNotFoundError` — wrong domain
- **Actual location:** `domains/security/services/fraud_detection_service.py` (class at line 432)
- **Fix:** Change to `from domains.security.services.fraud_detection_service import FraudScoringEngine`

### 3.6 `middleware/device_binding_middleware.py:69-70`
```python
self.mesh = ServiceMeshSecurity()
self.policy = NetworkPolicy()
```
- **Error:** Both classes are never imported and never defined anywhere
- **Fix:** Implement these classes or remove the calls

### 3.7 `middleware/dependencies/fraud_events.py:21`
```python
from infrastructure.database.models import FraudEvent
```
- **Error:** `FraudEvent` not in `infrastructure.database.models`
- **Actual location:** `domains/governance/models/fraud.py`
- **Fix:** Change to `from domains.governance.models.fraud import FraudEvent`

---

## 4 · Router Import Errors (~1,789 occurrences)

### 4.1 Root Cause Patterns

| Pattern | Occurrences | Root Cause |
|---------|-------------|-----------|
| `domains.governance.services.{domain}.{service}` | ~800 | Governance was meant to be an "admin aggregator" but most sub-services were never created |
| `domains.hr.services.{subdomain}.{service}` | ~200 | HR was restructured into subpackages (employees, payroll, etc.) but imports never updated |
| `domains.comms.services.{subdomain}.{service}` | ~150 | Comms restructured into subpackages — imports stale |
| `domains.finance.services.{subdomain}.{service}` | ~200 | Finance restructured — imports stale |
| `domains.country.services.{subdomain}.{service}` | ~100 | Country restructured — imports stale |
| Flat files that never existed | ~300 | Referenced in imports but never created on disk |

### 4.2 Modules Most Affected

| Module | Unique Broken Modules | Total Broken Occurrences |
|--------|----------------------|-------------------------|
| admin | 64 | ~1,400 |
| employee | 25 | ~168 |
| logistics | 2 | ~145 |
| supplier | 4 | ~13 |
| customer | 2 | ~3 |

---

## 5 · Domain Service Import Errors (~283 occurrences)

### 5.1 By Domain

| Domain | Broken Imports | Primary Issue |
|--------|---------------|---------------|
| finance | 110 | Cross-domain imports to governance, comms |
| logistics | 60 | Cross-domain imports to governance |
| security | 44 | Self-referential imports to fraud_detection |
| hr | 37 | Subpackage restructuring left stale imports |
| governance | 31 | Subpackage restructuring left stale imports |
| comms | 30 | Subpackage restructuring left stale imports |
| orders | 13 | Cross-domain imports |
| suppliers | 6 | Cross-domain imports |
| country | 4 | Subpackage restructuring |
| promotions | 2 | Minor cross-domain |
| infrastructure | 1 | Not a real domain — leftover in `domains/` |

### 5.2 Key Structural Issues

1. **HR domain restructured but imports not updated**
2. **Comms domain restructured** — imports stale
3. **Finance domain restructured** — imports stale
4. **Governance domain never fully implemented** — many sub-services referenced but don't exist
5. **`domains/media/` no longer exists** — already moved to `providers/media/` (correct)
6. **`domains/infrastructure/` exists** — but it's not a real domain (should be removed)

---

## 6 · Provider/Infrastructure Import Errors (174 occurrences)

### 6.1 Missing Third-Party Packages (~20)

| Package | Files Affected | Category |
|---------|---------------|----------|
| `cv2` (OpenCV) | 10 | Media/AI |
| `rembg` | 8 | Media/AI |
| `psutil` | 4 | System monitoring |
| `geoip2` | 2 | Geography |
| `onnxruntime` | 1 | AI models |
| `pytesseract` | 1 | OCR |
| `skimage` | 3 | Image processing |
| `scipy` | 1 | Scientific computing |
| `imageio` | 2 | Image I/O |
| `gradio_client` | 1 | AI/ML |
| `speech_recognition` | 1 | Voice |
| `bcrypt` | 2 | Security |
| `dotenv` | 1 | Config |
| `email_validator` | 1 | Validation |
| `reportlab` | 1 | PDF generation |

### 6.2 Self-Imports in `providers/media/`

Files that import themselves (likely copy-paste errors or circular imports):
- `free_image_tools.py:3` → `from free_image_tools import *`
- `image_ai_service.py:3` → `from image_ai_service import *`
- `import_service.py:3` → `from import_service import *`
- `media_storage.py:3` → `from media_storage import *`
- `qr_service.py:3` → `from qr_service import *`
- `storage.py:3` → `from storage import *`
- `upload_job_service.py:3` → `from upload_job_service import *`

---

## 7 · Structural Problems Summary

### 7.1 Router Layer
- **476 router files** across 5 modules — should be 75 (15 per module)
- **149 router files** exist on disk but are never registered
- Naming inconsistencies: `admin_*`, `*_controller`, `*_router`, `*_routes` all mixed
- Many router files contain business logic (violates thin-router pattern)

### 7.2 Domain Layer
- **517 service files** across 15 domains
- Cross-domain imports violate Law 3 (should go through ports.py/events.py)
- Many domains restructured into subpackages but imports never updated
- `domains/infrastructure/` should NOT exist (infrastructure is a top-level platform layer)

### 7.3 Governance Domain
- Acts as a "god domain" — 100+ router files import from it
- Most referenced sub-services don't exist on disk
- Should either be fully implemented or decomposed into actual domains

---

## 8 · Recommended Fix Order

| Priority | Phase | Description | Impact |
|----------|-------|-------------|--------|
| P0 | 20.1 | Fix 7 critical middleware blockers | App can start |
| P1 | 20.5.3 | Update HR/comms/finance/country import paths | ~700 router imports fixed |
| P1 | 20.5.4 | Install missing 3rd-party packages | ~20 broken imports fixed |
| P2 | 19 | Router restructuring (15 files/module) | 476 → 75 files |
| P2 | 20.5.2 | Create missing governance service stubs | ~800 router imports fixed |
| P3 | 20.5.5 | Remove dead imports | ~300 broken imports fixed |
| P4 | 15 | Distribute _parked/ files | Dead code removal |
| P5 | 17 | Update all imports after restructuring | Final cleanup |

---

## 9 · Architecture Changes Made

### 9.1 `ARCHITECTURE_DIAGRAM.md` Updates
- Updated domain list: removed `media` (provider), removed `infrastructure` (platform)
- Corrected domain count: 15 (not 13 or 19)
- Updated router pattern: `modules/{m}/routers/{d}.py` — 15 files per module
- Updated database schema diagram: 15 domain schemas

### 9.2 `DOMAIN_WORK.md` Updates
- Added **Phase 19: Router Restructuring** — `modules/{m}/routers/{d}.py` (15 files per module)
- Added **Phase 20: Fix All Broken Imports** — detailed fix table for all 7 critical blockers
- Updated Migration Order table with Phases 19 and 20

### 9.3 `ROUTER_CORRECTION_PLAN.md` Created
- Detailed module-by-module mapping of 476 → 75 files
- Exact source-to-target file mapping for all 5 modules
- Execution order, risk mitigation, success criteria

---

## 10 · Conclusion

The ZOZI backend has a **well-designed architecture on paper** but suffers from **incomplete implementation**:

1. **The three-axes design (Module × Domain × Feature) is sound** — but the codebase hasn't fully migrated to it
2. **15 actual domains** (not 19) — `media` is a provider, `infrastructure` is platform
3. **~2,253 broken import statements** indicate the migration is ~40% complete
4. **7 critical blockers** prevent the app from starting at all
5. **Router layer is 6.3x larger than needed** (476 vs 75 files)

**Immediate next step:** Fix the 7 critical middleware blockers (Phase 20.1) so the app can start, then proceed with router restructuring (Phase 19).
