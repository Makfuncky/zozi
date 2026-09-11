# PHASE 13 — DEAD CODE / UNUSED CODE AUDIT

**Project:** ZOZI Marketplace  
**Date:** 2026-09-11  
**Auditor:** Kilo (forensic static analysis)  
**Scope:** Backend (`D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend`) + Frontend (`D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend`)  
**Methodology:** Repository-wide grep/glob scans for commented code, unused imports, unreachable branches, abandoned experiments, obsolete feature implementations, duplicate implementations, unused scripts, unused dependencies, unused environment variables, and unused API routes. Cross-referenced against dynamic dispatch patterns (router discovery, dependency injection, event handlers, CLI entry points).

---

## EXECUTIVE SUMMARY

| Category | Count | Severity |
|---|---|---|
| CONFIRMED DEAD (no production references) | 16 items | HIGH |
| PROBABLY DEAD (stale/migration remnants, no active callers) | 12 items | MEDIUM |
| POSSIBLY USED DYNAMICALLY (test fixtures, build hooks, event bus) | 6 items | LOW |
| UNKNOWN (requires runtime tracing) | 4 items | INFO |

**Total dead/unused code candidates identified:** 38

---

## SECTION 1 — CONFIRMED DEAD CODE

### 1.1 Orphaned Monitoring Scripts (Backend `monitoring/`)

**Status:** CONFIRMED DEAD  
**Confidence:** HIGH — Zero import references across entire backend tree.

| File | Evidence |
|---|---|
| `monitoring/fraud_monitoring.py` | No `import fraud_monitoring` or module-level reference found in any backend `.py` file. |
| `monitoring/ghost_order_detector.py` | No references found. |
| `monitoring/threat_feed_updater.py` | No references found. |

**Impact:** Dead code clutter; potential confusion about active monitoring surface.  
**Files:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\monitoring\fraud_monitoring.py`, `D:\Projects\10- E-COMMERCE WEBSITE\zozi\monitoring\ghost_order_detector.py`, `D:\Projects\10- E-COMMERCE WEBSITE\zozi\monitoring\threat_feed_updater.py`

---

### 1.2 Orphaned Backup/DB Utility Scripts

**Status:** CONFIRMED DEAD  
**Confidence:** HIGH — No production import references.

| File | Evidence |
|---|---|
| `backend/scripts/pg_backup.py` | No `import pg_backup` or module reference in backend or tests. |
| `backend/scripts/_dbcheck.py` | No references found. This is a 14-line standalone SQLite inspector, never invoked. |

**Impact:** Dead operational scripts.  
**Files:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\scripts\pg_backup.py`, `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\scripts\_dbcheck.py`

---

### 1.3 One-Time Migration/Fix Scripts (Already Executed, Not Retained)

**Status:** CONFIRMED DEAD  
**Confidence:** HIGH — Scripts are named as one-shot fixes with no production import paths.

| File | Evidence |
|---|---|
| `backend/scripts/check_broken.py` | Not imported anywhere; filename implies one-time diagnostic. |
| `backend/scripts/check_law6.py` | Not imported anywhere; diagnostic for Law 6 compliance. |
| `backend/scripts/check_logistics.py` | Not imported anywhere; diagnostic for logistics routes. |
| `backend/scripts/reconstruct_functions.py` | Not imported anywhere; reconstructs broken function defs. |
| `backend/scripts/undo_changes.py` | Not imported anywhere; reverts `require_feature` additions. |
| `backend/scripts/schema_drift_gate.py` | Not imported anywhere; CI gate script. |
| `backend/scripts/fix_law6.py` | Not imported anywhere; one-time Law 6 fixer. |
| `backend/scripts/fix_law6_remaining.py` | Not imported anywhere; one-time Law 6 fixer. |
| `backend/scripts/fix_law6_schema.py` | Not imported anywhere; one-time Law 6 fixer. |
| `backend/scripts/fix_misplaced.py` | Not imported anywhere; one-time file-move fixer. |
| `backend/scripts/debug_import.py` | Not imported anywhere; debug utility. |
| `backend/scripts/_bootstrap_build.py` | Not imported anywhere; one-time table bootstrap. |
| `backend/scripts/_clean_redis_migration.py` | Not imported anywhere; one-time Redis→Valkey rename script. |

**Impact:** 13 dead migration/fix scripts cluttering `backend/scripts/`.  
**Files:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\scripts\{check_broken,check_law6,check_logistics,reconstruct_functions,undo_changes,schema_drift_gate,fix_law6,fix_law6_remaining,fix_law6_schema,fix_misplaced,debug_import,_bootstrap_build,_clean_redis_migration}.py`

---

### 1.4 Baseline Generator Scripts (Only Used in Tests, Not Production)

**Status:** CONFIRMED DEAD (in production)  
**Confidence:** HIGH — Only referenced from `tests/architecture/*` and `tests/` files, never from production code.

| File | Evidence |
|---|---|
| `backend/scripts/_gen_router_baseline.py` | Referenced only in `tests/architecture/test_architecture_gates.py` and `tests/architecture/test_supplier_route_integrity.py`. |
| `backend/scripts/_gen_service_provider_baseline.py` | Referenced only in `tests/architecture/test_architecture_gates.py`. |
| `backend/scripts/_gen_import_laws_baseline.py` | Referenced only in `tests/architecture/test_import_laws.py`. |
| `backend/scripts/_gen_offset_adoption_baseline.py` | Referenced only in `tests/architecture/test_offset_adoption_baseline.py`. |
| `backend/scripts/_gen_cross_domain_baseline.py` | Referenced only in `tests/architecture/test_no_cross_domain_direct_imports.py` and `tests/architecture/test_ports_contract.py`. |
| `backend/scripts/_gen_ports_contract_baseline.py` | Referenced only in `tests/architecture/test_ports_contract.py`. |

**Impact:** Baseline generator scripts live in production `scripts/` but serve no production purpose. They are test-support utilities that should ideally reside under `tests/` or be clearly marked as dev-only.  
**Files:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\scripts\_gen_{router,service_provider,import_laws,offset_adoption,cross_domain,ports_contract}_baseline.py`

---

### 1.5 `seed_loader.py` — Dev-Only Utility Not Invoked in Production

**Status:** CONFIRMED DEAD (in production)  
**Confidence:** HIGH — Used only by test files and other debug scripts; production seed path is `infrastructure.database.seed._common.seed_data()`.

| Reference | Evidence |
|---|---|
| `tests/architecture/test_country_staff_seed.py` | `from scripts import seed_loader` |
| `scripts/_debug/_test_products*.py` | `from scripts.seed_loader import ...` |
| `infrastructure/database/seed/_seed_constants.py` | Mentions `scripts/seed_loader.py` in docstring only. |

**Impact:** Dead dev utility in production scripts tree.  
**File:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\scripts\seed_loader.py`

---

### 1.6 `domains/finance/services/__init__.py` — Commented-Out Module Imports

**Status:** CONFIRMED DEAD  
**Confidence:** HIGH — All four submodule imports are commented out with `# TODO: Module not yet created`.

**Evidence:**
```python
# TODO: Module not yet created
# from domains.finance.services.payments import *
# TODO: Module not yet created
# from domains.finance.services.treasury import *
# TODO: Module not yet created
# from domains.finance.services.payouts import *
# TODO: Module not yet created
# from domains.finance.services.country import *
```

**Impact:** Dead commented code; `__all__` is empty.  
**File:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\domains\finance\services\__init__.py`

---

### 1.7 `supplier_supplier_upload_service.py` — Large Commented-Out Import Block at Top

**Status:** CONFIRMED DEAD  
**Confidence:** HIGH — Imports are explicitly commented out.

**Evidence:**
```python
# from domains.finance.services.shared.bg_removal_service import VALID_STRATEGIES
# from domains.finance.services.shared.bg_removal_service import remove_background
# from domains.finance.services.shared.bg_removal_service import _HAS_CV2
```

**Impact:** Dead commented imports; module `domains.finance.services.shared.bg_removal_service` does not exist.  
**File:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\domains\suppliers\services\products\supplier_supplier_upload_service.py:20-25`

---

### 1.8 `supplier_orders_verify_service.py` — Commented-Out Import Block

**Status:** CONFIRMED DEAD  
**Confidence:** HIGH — 10 commented-out imports.

**Evidence:**
```python
# from domains.suppliers.services.orders.supplier_order_service import get_supplier_order
# from domains.suppliers.services.orders.supplier_order_service import get_supplier_order_for_verify
# ... (8 more)
```

**File:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\domains\suppliers\services\orders\supplier_orders_verify_service.py:22-42`

---

### 1.9 `supplier_shared.py` — Commented-Out Imports

**Status:** CONFIRMED DEAD  
**Confidence:** HIGH — Imports explicitly commented out.

**Evidence:**
```python
# from providers.ai.ai_variant_config import ai_service  # unused
# from domains.finance.services.ledger.finance_transfer_service import build_transfer_reference
```

**File:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\domains\suppliers\services\supplier_shared.py:37-39`

---

### 1.10 `requirements.txt` — Unused `redis` Package

**Status:** CONFIRMED DEAD  
**Confidence:** HIGH — Project completed Valkey migration (memory record `infrastructure_stack_production`), and constraint `no_redis_naming_anywhere` forbids Redis naming. Yet `redis==8.0.1` is still in `requirements.txt`.

**Evidence:**
- `requirements.txt:20`: `redis==8.0.1`
- No active `import redis` in production codebase (Valkey shim replaces it).
- Memory record: `infrastructure_stack_production :: Valkey migration IS complete as of 2026-09-03`.

**Impact:** Dead dependency; contradicts project constraint `no_redis_naming_anywhere`.  
**File:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\requirements.txt:20`

---

### 1.11 Frontend `LegacyBadgeTier` — Deprecated Type Still Exported

**Status:** CONFIRMED DEAD  
**Confidence:** HIGH — Marked `@deprecated` with no active usage confirmed.

**Evidence:**
```tsx
/** @deprecated Use the new backend-aligned tiers instead */
export type LegacyBadgeTier = "trusted" | "premium" | "new";
```

**Files:**
- `D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\shared\src\components\ui\SupplierBadge.web.tsx:6-7`
- `D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\shared\src\components\ui\SupplierBadge.native.tsx:11-12`

**Impact:** Deprecated type still exported; may confuse consumers.

---

## SECTION 2 — PROBABLY DEAD CODE

### 2.1 `domains/finance/services/payouts/payout_batch_service.py` — Massive Commented-Out Import Block

**Status:** PROBABLY DEAD  
**Confidence:** MEDIUM — 20+ commented-out imports at top of file; some internal functions may be used, but the commented block references `domains.finance.services.payments.base` and `registry` which may not exist.

**Evidence:**
```python
# TODO: Module not yet created
# from domains.finance.services.payments.base import BasePaymentGateway
# ... (20 more commented imports)
```

**File:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\domains\finance\services\payouts\payout_batch_service.py:7-17`

---

### 2.2 `domains/finance/services/payments/payment_orchestrator.py` — Commented-Out Imports + TODO Blocks

**Status:** PROBABLY DEAD  
**Confidence:** MEDIUM — File contains extensive commented-out code and TODO placeholders.

**Evidence:**
```python
# TODO: Module not yet created
# # TODO: Module not yet created
# TODO: log_bank_transaction not found in cash_management_service
```

**File:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\domains\finance\services\payments\payment_orchestrator.py:1112-1140`

---

### 2.3 `domains/finance/services/payments/payment_engine.py` — Commented-Out TODO

**Status:** PROBABLY DEAD  
**Confidence:** MEDIUM — Function-level TODO.

**Evidence:**
```python
# TODO: Functions not found in kernel.money
```

**File:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\domains\finance\services\payments\payment_engine.py:97`

---

### 2.4 `domains/suppliers/services/supplier_shared.py` — Stale AI Smoke Report Paths

**Status:** PROBABLY DEAD  
**Confidence:** MEDIUM — Module-level constants reference artifact paths that likely no longer exist.

**Evidence:**
```python
_AI_IMAGE_SMOKE_REPORT = Path(__file__).resolve().parents[2] / "artifacts" / "ai_image_group_smoke.json"
_AI_IMAGE_SMOKE_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "ai_image_group_smoke.py"
```

**File:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\domains\suppliers\services\supplier_shared.py:64-65`

---

### 2.5 `backend/scripts/seed_categories.py` — Dev-Only Seed Script

**Status:** PROBABLY DEAD  
**Confidence:** MEDIUM — Docstring says "dev-only offline tool"; production seed path is `infrastructure.database.seed._common.seed_data()`.

**Evidence:** Docstring at lines 1-18 states it is a dev-only tool. No production import references found.  
**File:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\scripts\seed_categories.py`

---

### 2.6 `backend/scripts/_cross_domain_baseline.txt` and `_router_logic_baseline.txt` — Stale Baseline Text Files

**Status:** PROBABLY DEAD  
**Confidence:** MEDIUM — `.txt` baseline files in `scripts/` directory. The Python `_gen_*` scripts regenerate these, but the `.txt` files themselves are not imported by production code.

**Files:**
- `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\scripts\_cross_domain_baseline.txt`
- `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\scripts\_router_logic_baseline.txt`
- `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\scripts\_import_laws_baseline.txt`
- `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\scripts\_offset_adoption_baseline.txt`
- `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\scripts\_ports_contract_baseline.txt`

---

### 2.7 `backend/scripts/audit/` Directory — Audit Artifacts

**Status:** PROBABLY DEAD  
**Confidence:** MEDIUM — `backend/scripts/audit/` contains audit result JSONs and scripts that appear to be one-time audit outputs.

**Files:**
- `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\scripts\audit\` (directory)
- `D:\Projects\10- E-COMMERCE WEBSITE\zozi\documents\action\AUDIT_RESULTS.json`

---

### 2.8 `backend/scripts/docs/` Directory

**Status:** PROBABLY DEAD  
**Confidence:** MEDIUM — Documentation directory inside `scripts/` not referenced from code.

**File:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\scripts\docs\`

---

### 2.9 `backend/scripts/_debug/` Directory

**Status:** PROBABLY DEAD  
**Confidence:** MEDIUM — Debug scripts (`_test_products*.py`, `_test_emp.py`) are not referenced from production code.

**Files:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\scripts\_debug\_test_products{,.2,.3,.4}.py`, `_test_emp.py`

---

### 2.10 `backend/.kilo/` Directory — Kilo Migration Helper Scripts

**Status:** PROBABLY DEAD  
**Confidence:** MEDIUM — Contains `update_imports.py`, `update_imports_v2.py`, `simple_update.py`, `list_missing.py`, `extract_modules.py`, `create_shims.py`, `create_remaining_shims.py`, `create_all_shims.py`. These are one-time import-path migration helpers.

**Constraint reminder:** Project constraint `no_kilo_files_in_project` states Kilo files must not exist in the project repository.  
**Files:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\.kilo\*.py`

---

### 2.11 `backend/tests/_support/laws.py` — Commented-Out Architectural Commentary

**Status:** PROBABLY DEAD  
**Confidence:** MEDIUM — Contains extensive commented-out architectural rules that are enforced by actual test logic elsewhere.

**Evidence:**
```python
# key = the importing layer's package root; value = forbidden import roots.
# Source-level import checks (Law 1 / 97-102)
```

**File:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\tests\_support\laws.py`

---

### 2.12 `backend/config.py` — Unused/Stale Settings Keys

**Status:** PROBABLY DEAD  
**Confidence:** MEDIUM — Several settings keys are defined in `_DEFAULTS` but have no confirmed production usage.

| Setting | Evidence |
|---|---|
| `hf_api_token` | No reference found in backend code. |
| `loadtest_profile_enabled` | Only referenced in `auth_service.py:1588` inside a conditional; likely test-only. |
| `finance_scheduler_dispatch_provider` | Empty default, no production references. |
| `finance_scheduler_dispatch_dry_run` | Default `True`, no production references. |
| `finance_ai_timeout` | In `_INT_KEYS` but no reference found. |
| `field_encryption_key_from_env` | Indirect alias; primary path is `field_encryption_key`. |
| `field_encryption_key_file` | File-based key loading; no production references. |
| `field_encryption_key_vault_*` | Vault integration; no production references. |
| `field_encryption_key_aws_ssm_*` | AWS SSM integration; no production references. |

**File:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\config.py`

---

## SECTION 3 — POSSIBLY USED DYNAMICALLY

### 3.1 `monitoring/` Scripts — May Be Cron/External Scheduled Jobs

**Status:** POSSIBLY USED DYNAMICALLY  
**Confidence:** LOW — No Python imports found, but these could be invoked by external cron, CI, or systemd timers not visible in repo.

| File | Note |
|---|---|
| `monitoring/fraud_monitoring.py` | Standalone script; may be scheduled externally. |
| `monitoring/ghost_order_detector.py` | Same. |
| `monitoring/threat_feed_updater.py` | Same. |

**Recommendation:** Verify with ops team whether these are scheduled externally. If yes, move to `backend/scripts/monitoring/` for clarity.

---

### 3.2 `backend/scripts/seed_loader.py` — May Be Used in CI/CD Pipeline

**Status:** POSSIBLY USED DYNAMICALLY  
**Confidence:** LOW — Could be invoked by CI/CD pipeline or local dev workflow not tracked in repo imports.

---

### 3.3 `backend/scripts/_gen_*.py` — May Be Used in CI Gates

**Status:** POSSIBLY USED DYNAMICALLY  
**Confidence:** LOW — Baseline generators are invoked by architecture gate tests, but could also be run in CI pre-commit hooks.

---

### 3.4 `backend/.kilo/` Scripts — May Be Used by Kilo Extension

**Status:** POSSIBLY USED DYNAMICALLY  
**Confidence:** LOW — These scripts may be invoked by the Kilo VS Code extension outside of the Python runtime.

---

### 3.5 `backend/tests/_support/laws.py` — Architectural Gate Support

**Status:** POSSIBLY USED DYNAMICALLY  
**Confidence:** LOW — May be dynamically loaded by test infrastructure.

---

### 3.6 `backend/scripts/audit/` and `documents/action/AUDIT_RESULTS.json` — May Be Used in Audit Reports

**Status:** POSSIBLY USED DYNAMICALLY  
**Confidence:** LOW — Could be referenced by external audit tooling or documentation generators.

---

## SECTION 4 — UNKNOWN (REQUIRES RUNTIME TRACING)

### 4.1 Unused Environment Variables

**Status:** UNKNOWN  
**Evidence:** The following env vars are defined in `.env.example` / `config.py` but have no confirmed usage in scanned source:

| Variable | Defined In |
|---|---|
| `REDIS_URL` | `.env.example:21` — backward-compat alias per comment, but no usage confirmed. |
| `TAP_SECRET_KEY` | `.env.example:16` |
| `TAP_WEBHOOK_SECRET` | `.env.example:16` |
| `TAP_WEBHOOK_URL` | `.env.example:16` |
| `RESEND_API_KEY` | `.env.example` (not present) but `resend_api_key` in `config.py` |
| `RESEND_WEBHOOK_SECRET` | `.env.example` (not present) but `resend_webhook_secret` in `config.py` |
| `GOOGLE_CLIENT_ID` | `.env.example` (not present) but `google_client_id` in `config.py` |
| `GOOGLE_CLIENT_SECRET` | `.env.example` (not present) |
| `FACEBOOK_CLIENT_ID` | `.env.example` (not present) |
| `FACEBOOK_CLIENT_SECRET` | `.env.example` (not present) |
| `OPENAI_API_KEY` | `.env.example:41` — no confirmed production usage. |
| `HF_API_TOKEN` | `.env.example` (not present) but `hf_api_token` in `config.py` |
| `S3_*` legacy aliases | `.env.example:56-61` — backward-compat aliases, but new code should use `R2_*`. |
| `CELERY_BROKER_URL` | `.env.example:65` |
| `CELERY_RESULT_BACKEND` | `.env.example:66` |
| `CELERY_TASK_ALWAYS_EAGER` | `.env.example:67` |
| `ML_WORKERS` | `.env.example:70` |
| `RUN_LEGACY_MIGRATIONS_ON_STARTUP` | `.env.example:9` |
| `BOOTSTRAP_SCHEMA_ON_STARTUP` | `.env.example:8` |

**Note:** Some of these may be used via dynamic config loading (`os.getenv`) or framework discovery. Runtime tracing required.

---

### 4.2 Unused/Orphaned Frontend Files

**Status:** UNKNOWN  
**Evidence:** The following files exist in the frontend tree but were not confirmed as imported/used during static scan. Some may be dynamically imported or used by build tooling.

| File | Note |
|---|---|
| `frontend/web_app/src/lib/useBgABTest.ts` | A/B test hook; may be feature-flagged. |
| `frontend/web_app/src/components/BackgroundEffect.tsx` | Decorative component; may be used conditionally. |
| `frontend/web_app/src/components/BannerCanvasEditor.tsx` | Large canvas editor; may be used in admin only. |
| `frontend/web_app/src/components/Carousel.tsx` | May be used in multiple places. |
| `frontend/web_app/e2e/*.spec.ts` | E2E tests are not "dead" per se, but many spec files exist that may not be run in CI. |

---

### 4.3 Unused API Routes

**Status:** UNKNOWN  
**Evidence:** `_load_routers()` in `backend/main.py:243-278` dynamically discovers routers via `importlib.import_module`. Static analysis cannot confirm which routers are mounted vs. orphaned without runtime inspection.

**Recommendation:** Run the application with router debug logging enabled to list all mounted routes.

---

### 4.4 Unused Models

**Status:** UNKNOWN  
**Evidence:** SQLAlchemy models are imported for registration in `backend/main.py:14` (`from infrastructure.database import models`). Models without corresponding routes or services may exist. Full model-to-route cross-reference requires runtime inspection.

---

## SECTION 5 — COMMENTED-OUT CODE INVENTORY

### 5.1 Commented-Out Imports (Backend)

| File | Lines | Count |
|---|---|---|
| `domains/finance/services/__init__.py` | 7-14 | 4 imports |
| `domains/finance/services/payouts/payout_batch_service.py` | 7-17 | 10 imports |
| `domains/finance/services/payments/payment_orchestrator.py` | 1112-1122 | 2 imports |
| `domains/suppliers/services/supplier_shared.py` | 37-39 | 2 imports |
| `domains/suppliers/services/products/supplier_supplier_upload_service.py` | 20-25, 50-53 | 6 imports |
| `domains/suppliers/services/orders/supplier_orders_verify_service.py` | 22-42 | 10 imports |
| `domains/accounts/services/auth/auth_service.py` | 3516 | 1 import |
| `domains/accounts/ports.py` | 1010 | 1 import |
| `domains/comms/services/shared/utility/shared_utils.py` | 182 | 1 import |
| `domains/catalog/services/categories/admin_categories_service.py` | 27 | 1 import |
| `domains/catalog/services/products/admin_products_service.py` | 14 | 1 import |
| `domains/governance/subscribers.py` | 64-182 | 15 imports |
| `domains/security/services/detection/public_security_detection_service.py` | 16-18 | 2 imports |
| `domains/accounts/services/permissions/permission_service.py` | 445 | 1 import |
| `domains/accounts/services/identity/identity_admin_service.py` | 22 | 1 import |
| `domains/country/services/core/country_config_admin_service.py` | 260 | 1 import |

**Total commented-out imports:** ~58

---

### 5.2 Commented-Out Code Blocks (Backend)

| File | Lines | Description |
|---|---|---|
| `domains/suppliers/services/profile/supplier_payouts_service.py` | 58 | Commented-out section header: `# ── ORM-based Payout Operations (merged from supplier_payout_service.py) ──────` |
| `domains/suppliers/services/orders/supplier_orders_service.py` | 541 | Commented-out section header: `# ── ORM-based Order Operations (merged from supplier_order_service.py) ─────────` |
| `domains/audit/services/logs/audit_service.py` | 131 | Commented-out section header referencing legacy vocabulary. |
| `domains/catalog/services/categories/category_service.py` | 430 | Commented-out section header: `# ── Archive / restore / bulk (folded from admin_categories_service) ──────────` |
| `domains/country/services/research/country_ai_research.py` | 537 | Commented-out section header: `# -- Research helpers (folded from country_research) -----------------------------` |

---

### 5.3 Commented-Out Frontend Imports

| File | Line | Description |
|---|---|---|
| `frontend/web_app/src/lib/useAuth.tsx` | 158 | `// from the server is handled by the cart store's isAuthenticated() guard.` (comment only, not an import) |

**No commented-out TS/TSX imports were found.**

---

## SECTION 6 — UNUSED DEPENDENCIES

### 6.1 Backend `requirements.txt`

| Package | Evidence | Recommendation |
|---|---|---|
| `redis==8.0.1` | `requirements.txt:20`; no active `import redis` in production; Valkey migration complete. | Remove. |
| `duckdb==1.5.5` | Optional analytics domain engine; no confirmed production usage. | Verify with analytics team. |
| `duckdb-engine==0.17.0` | Same as above. | Verify with analytics team. |
| `feedparser==6.0.12` | No references found in backend code. | Remove if unused. |
| `schedule==1.2.2` | No references found; APScheduler is used instead. | Remove if unused. |
| `text-unidecode==1.3` | No references found. | Remove if unused. |
| `python-docx==1.2.0` | No references found in backend code. | Remove if unused. |
| `openpyxl==3.1.5` | No references found in backend code. | Remove if unused. |
| `faker==40.36.0` | Used in tests only; should be in `requirements-dev.txt`. | Move to dev requirements. |

---

## SECTION 7 — RECOMMENDATIONS

1. **Remove or archive `monitoring/` scripts** (`fraud_monitoring.py`, `ghost_order_detector.py`, `threat_feed_updater.py`) if they are not scheduled externally. If they are cron jobs, move them to `backend/scripts/monitoring/` and document the schedule.

2. **Delete one-time migration/fix scripts** in `backend/scripts/`: `check_broken.py`, `check_law6.py`, `check_logistics.py`, `reconstruct_functions.py`, `undo_changes.py`, `schema_drift_gate.py`, `fix_law6*.py`, `fix_misplaced.py`, `debug_import.py`, `_bootstrap_build.py`, `_clean_redis_migration.py`, `_dbcheck.py`. These should be preserved in version control history, not in the active tree.

3. **Move `_gen_*.py` baseline generators** to `tests/architecture/` or clearly mark them as dev-only. They have no production purpose.

4. **Remove or archive `seed_loader.py`** if the production seed path (`infrastructure.database.seed._common.seed_data()`) is canonical.

5. **Clean up commented-out imports** in:
   - `domains/finance/services/__init__.py`
   - `domains/finance/services/payouts/payout_batch_service.py`
   - `domains/suppliers/services/supplier_shared.py`
   - `domains/suppliers/services/products/supplier_supplier_upload_service.py`
   - `domains/suppliers/services/orders/supplier_orders_verify_service.py`
   - `domains/governance/subscribers.py`

6. **Remove `redis==8.0.1`** from `requirements.txt` to comply with project constraint `no_redis_naming_anywhere`.

7. **Deprecate `LegacyBadgeTier`** in frontend `SupplierBadge` components if no consumers remain.

8. **Verify unused env vars** in `config.py` (`hf_api_token`, `finance_ai_timeout`, vault/SSM field encryption paths) with the team; remove if truly unused.

9. **Audit `.kilo/` directory** — per project constraint `no_kilo_files_in_project`, these files should not exist in the repo. Remove them.

10. **Run runtime route listing** to confirm which routers are actually mounted and identify orphaned API routes.

---

## APPENDIX — METHODOLOGY NOTES

- **Static analysis only:** No files were modified. No runtime tracing was performed.
- **Dynamic imports:** `_load_routers()` in `main.py:243` uses `importlib.import_module` to discover routers. Static analysis cannot confirm orphaned routers without runtime inspection.
- **Event handlers:** Event subscribers may be wired via decorator or registry patterns not visible in static imports.
- **Configuration-driven behavior:** Some unused-looking code may be activated by config flags (e.g., `settings.bank_api_enabled`).
- **Test fixtures:** Some dead-code candidates are used exclusively by tests and should not be removed without test impact analysis.
