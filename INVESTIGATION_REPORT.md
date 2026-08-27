# ZOZI Complete Investigation Report

> Generated: 2026-08-26  
> Scope: Backend + Frontend  
> Total issues found: **350+**

---

## Executive Summary

| Category | Issues |
|----------|--------|
| Architecture Violations | 112 |
| Database & Model | 108 |
| Security | 34 |
| Frontend | 20 |
| Error Handling & Concurrency | 25 |
| Duplication & Logic | 50+ |
| RBAC & Providers | 25 |
| Backend-Frontend Wiring | 27 |
| **TOTAL** | **350+** |

---

## 1. ARCHITECTURE VIOLATIONS (112 issues)

### 1.1 Law 1: Arrows Point Down (CRITICAL)

#### Domains Importing Modules

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 1 | `domains/orders/services/core/admin.py` | 15 | `from modules.admin.routers.admin_controller import ...` | Move `archive_entity` to domain service |
| 2 | `domains/orders/services/core/admin_extra.py` | 13 | Same pattern | Same fix |

#### Infrastructure Importing Domains

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 3 | `infrastructure/utils/export_read.py` | 15-19 | Imports 5 domain models | Move to `domains/governance/services/` |
| 4 | `infrastructure/utils/misc_write.py` | 31-38 | Imports domain models + services | Move to `domains/governance/services/` |
| 5 | `infrastructure/utils/user_context.py` | 5 | Imports `governance.models.user.User` | Keep — TYPE_CHECKING only |
| 6 | `infrastructure/services/utils/workflow_engine.py` | 10 | Imports `governance.models.admin.SystemSetting` | Move to `domains/governance/services/` |
| 7 | `infrastructure/services/utils/translate_controller.py` | 6 | Imports `governance.services.translation_service` | Move to `domains/governance/services/` |
| 8 | `infrastructure/search/routers/search_controller.py` | 19,22 | Imports `catalog.services.search.search_service` | Move to `modules/` or `domains/catalog/` |

#### Kernel Importing Providers

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 9 | `kernel/currency.py` | 7 | `from providers.geography.rates import ...` | Move rate logic to `infrastructure/` or `domains/finance/` |

### 1.2 Law 4: Features Single-Sourced (CRITICAL)

#### Feature Naming Mismatch (dots vs colons)

| Domain | Router Uses | Features.py Defines |
|--------|-------------|---------------------|
| catalog | `catalog:list`, `catalog:read` | `catalog.product.create`, `catalog.category.manage` |
| finance | `finance:commission:read` | `finance.commission.read` |
| orders | `orders:list`, `orders:read` | `orders.read`, `orders.create` |
| suppliers | `suppliers:onboarding:write` | `suppliers.registration.manage` |
| analytics | `analytics:read` | `{}` (empty) |
| hr | Various | `{}` (empty) |
| audit | Various | `{}` (empty) |
| security | Various | `{}` (empty) |

**Fix:** Standardize on dot notation. Update all `require_feature()` calls to match `domains/*/features.py`.

### 1.3 Law 6: Schema Discipline

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 10 | `domains/accounts/models/onboarding.py` | 17 | Schema `hr` for accounts model | Move to `accounts` schema |
| 11 | `domains/accounts/models/onboarding.py` | 46 | Schema `media` (doesn't exist) | Move to `security` or `catalog` schema |
| 12 | `domains/hr/models/employee_models.py` | 25 | Schema `logistics` for HR model | Move to `hr` schema |
| 13 | `domains/suppliers/models/suppliers.py` | 30 | Schema `supplier` (singular) | Change to `suppliers` |
| 14 | `domains/customers/models/customer_schema_models.py` | 28 | Schema `customer` (singular) | Change to `customers` |

### 1.4 Law 7: DOMAIN_ALLOWLIST Issues

| # | File | Line | Issue |
|---|------|------|-------|
| 15 | `DOMAIN_ALLOWLIST.yaml` | 9-11 | References forbidden `core.users` |
| 16 | `DOMAIN_ALLOWLIST.yaml` | 20-21 | References non-existent `domains.payments` |

---

## 2. DATABASE & MODEL ISSUES (108 issues)

### 2.1 Duplicate Table Names (CRITICAL)

| Tables | File A | File B |
|--------|--------|--------|
| `permission_categories`, `permissions`, `role_permission_assignments`, `user_permission_overrides`, `permission_audit_log` | `rbac/models.py` | `rbac/models/permission_entities.py` |

**Fix:** Delete `rbac/models.py`, keep `permission_entities.py`.

### 2.2 Missing ondelete (HIGH)

100+ FK columns missing `ondelete`. Examples:

| File | Column | FK Target |
|------|--------|-----------|
| `rbac/models.py` | `category_id` | `accounts.permission_categories.id` |
| `governance/models/user.py` | `referred_by_user_id` | `governance.users.id` |
| `finance/models/payments.py` | `order_id` | `commerce.orders.id` |

**Fix:** Add `ondelete='SET NULL'`, `ondelete='CASCADE'`, or `ondelete='RESTRICT'` to all FKs.

### 2.3 country_code Width (MEDIUM)

19 columns use `String(10)` instead of `String(2)`:

| File | Models |
|------|--------|
| `accounts/models/core.py` | `Address`, `CartItem` |
| `governance/models/core.py` | `UserSession` |
| `hr/models/employee_models.py` | `PhysicalIDCard`, etc. |

### 2.4 Missing updated_at (MEDIUM)

16 models have `created_at` but no `updated_at`:

| File | Models |
|------|--------|
| `governance/models/user.py` | `PasswordResetToken`, `EmailVerificationToken`, `RevokedToken` |
| `finance/models/payments.py` | `PaymentReconciliationRun`, `PaymentGatewayConnection` |
| `catalog/models/ai_upload.py` | `AIUploadJob`, `AIStagingProduct`, `AIUploadError` |

### 2.5 Inconsistent Timestamps (HIGH)

Mixing `default=_utcnow` (Python-side) vs `server_default=func.now()` (DB-side) across 50+ models.

**Fix:** Standardize on `server_default=func.now()`.

### 2.6 Duplicate Classes (CRITICAL)

| Class | Files |
|-------|-------|
| `StorageBackend` | `infrastructure/storage/storage.py` + `providers/storage/storage_backend.py` |
| `CircuitBreaker` | `infrastructure/utils/circuit_breaker.py` + `infrastructure/observability/circuit_breaker.py` |
| `UserCreate`, `UserUpdate` | Multiple schema files |

---

## 3. SECURITY ISSUES (34 issues)

### 3.1 Hardcoded Secrets (CRITICAL)

| # | File | Issue |
|---|------|-------|
| 1 | `backend/.env` | `SECRET_KEY=change-this-to-a-strong-random-key` |
| 2 | `tests/conftest.py` | Demo passwords: `admin123`, `supplier123`, `customer123` |

### 3.2 SQL Injection (HIGH)

| # | File | Line | Issue |
|---|------|------|-------|
| 3 | `domains/hr/services/hr_employee_service.py` | 56,108,141 | f-string SQL interpolation |
| 4 | `domains/hr/services/ess_service.py` | 48 | f-string SQL |
| 5 | `infrastructure/security/vault.py` | 155 | Dynamic SQL without allowlist |
| 6 | `infrastructure/database/database_service.py` | 42 | String concatenation SQL |
| 7 | `jobs/seed_all.py` | 301 | String concatenation SQL |

### 3.3 Missing Authentication (HIGH)

| # | File | Endpoint | Issue |
|---|------|----------|-------|
| 8 | `main.py` | `/ws/admin/background-jobs` | No auth |
| 9 | `domains/security/services/detection/public_security_detection_service.py` | Threat feed status | No auth |
| 10 | `domains/logistics/services/core/service.py` | `/api/health`, `/api/geo/*` | No auth |

### 3.4 Missing Input Validation (HIGH)

20+ endpoints accept `body: dict = Body(...)` without Pydantic validation.

| File | Endpoints |
|------|-----------|
| `modules/admin/routers/security.py` | Fraud score, blacklist |
| `modules/admin/routers/hr.py` | HR operations |
| `modules/supplier/routers/finance.py` | Financial operations |
| `modules/employee/routers/comms.py` | Tickets |

### 3.5 Bare Except / Swallowed Exceptions (MEDIUM)

30+ locations with `except:` or `except Exception: pass`.

### 3.6 Insecure Defaults (HIGH)

| File | Issue |
|------|-------|
| `infrastructure/utils/config.py` | `secret_key` regenerates on restart (invalidates JWTs) |
| `domains/logistics/services/core/service.py` | CORS `allow_origins` defaults to `["*"]` |

---

## 4. FRONTEND ISSUES (20 issues)

### 4.1 Security (CRITICAL)

| # | File | Issue | Fix |
|---|------|-------|-----|
| 1 | `app/auth/callback/SocialAuthCallbackClient.tsx` | Access token in URL query param | Use server-set httpOnly cookie |
| 2 | `shared/src/adminPermissions.ts` | Admin permissions in localStorage | Fetch from server |
| 3 | `shared/src/adminPermissions.ts` | Permission overrides in localStorage | Validate server-side |

### 4.2 Missing Error Boundaries (MEDIUM)

Most routes lack error boundaries. Only `/products` has one.

**Fix:** Wrap all `/admin/*`, `/supplier/*`, `/checkout`, `/orders`, `/cart` routes with `ErrorBoundary`.

### 4.3 Performance (MEDIUM)

| File | Issue |
|------|-------|
| `app/products/page.tsx` | Large product grid without virtualization |
| `components/Header.tsx` | Not memoized, subscribes to 7+ stores |

### 4.4 Missing Routes (MEDIUM)

Employee portal is a stub. Backend has full EMS/payroll/HR but frontend only has bare `/employee` page.

---

## 5. ERROR HANDLING & CONCURRENCY (25 issues)

| # | Category | Issues |
|---|----------|--------|
| 1 | Missing pagination | List endpoints without limit/offset (will OOM at 100K users) |
| 2 | Missing timeouts | Payment provider API calls (Stripe, PayPal, etc.) |
| 3 | Missing rollback | DB helper functions without rollback |
| 4 | N+1 queries | Supplier health + reconciliation services |
| 5 | Missing retry | Payment providers without retry logic |
| 6 | Missing error handling | Endpoints without try/except |

---

## 6. DUPLICATION & LOGIC (50+ issues)

### 6.1 Duplicate Functions

| Function | Files |
|----------|-------|
| `get_user_by_id` | 5+ files |
| `get_order_by_id` | 4+ files |
| `health_check` | 4 job files |
| `cleanup_expired_tokens` | 2 files |

### 6.2 Dead Code

| Pattern | Count |
|---------|-------|
| `if False else` dead code | 2 locations |
| Stub functions returning `{}` | 50+ locations |
| `import *` usage | 100+ files |

### 6.3 Logic Errors

| File | Issue |
|------|-------|
| `domains/finance/services/ledger/general_ledger_service.py` | `== None` instead of `is None` |
| `domains/security/services/fraud/fraud_detection_service.py` | `== None` instead of `is None` |

---

## 7. RBAC & PROVIDERS (25 issues)

### 7.1 Feature Atom Mismatch (CRITICAL)

ALL `require_feature()` calls in routers don't match `domains/*/features.py` definitions. RBAC gates will fail.

### 7.2 Empty Feature Files (HIGH)

4 domains have empty `features.py`: `hr`, `analytics`, `audit`, `security`.

### 7.3 Missing Provider HAS Flags (MEDIUM)

10+ providers missing `HAS_<SDK>` flags: `auth`, `automation`, `bg_removal`, `finance`, `geography`, etc.

### 7.4 Dual Role System (HIGH)

Two role assignment systems: `rbac/roles.py` (old) and `rbac/dependencies.py` (new).

---

## 8. BACKEND-FRONTEND WIRING (27 issues)

### 8.1 API Proxy Misconfiguration (CRITICAL)

| # | Issue |
|---|-------|
| 1 | `/api/:path*` rewrite strips `/api` prefix but backend routes are `/api/v1/...` |
| 2 | `/admin/:path*` forwarded to `/admin/...` but backend has no such routes |
| 3 | Frontend `/admin` calls bypass `/__api` proxy |

### 8.2 Missing Backend Endpoints (CRITICAL)

| Endpoint | Frontend Uses | Backend Has |
|----------|---------------|-------------|
| `GET /rbac/catalog` | Permission sync | **NO** |
| `/auth/login` | Login | **NO** |
| `/auth/refresh` | Token refresh | **NO** |
| `/auth/me` | Current user | **NO** |
| `/auth/logout` | Logout | **NO** |
| `websocket_user` | WebSocket | **NO** (import crashes) |

### 8.3 Permission Sync (CRITICAL)

Frontend `adminPermissions.ts` is hardcoded, not generated from backend `/rbac/catalog`.

### 8.4 Naming Mismatch (HIGH)

Backend uses colon-separated features (`analytics:read`), frontend uses dot-separated (`analytics.view`).

---

## Priority Action Plan

### Phase 1: CRITICAL (Fix Immediately)

| # | Action | Impact |
|---|--------|--------|
| 1 | Add `GET /rbac/catalog` endpoint | Permission sync works |
| 2 | Fix API proxy rewrites | Admin API calls work |
| 3 | Create `/auth/login`, `/auth/refresh`, `/auth/me`, `/auth/logout` | Login flow works |
| 4 | Create `websocket_user` handler | Backend starts |
| 5 | Replace placeholder `SECRET_KEY` | Security |
| 6 | Delete `rbac/models.py` (duplicate) | Prevents runtime crash |

### Phase 2: HIGH (Fix This Week)

| # | Action | Impact |
|---|--------|--------|
| 7 | Standardize feature naming (dots vs colons) | RBAC gates work |
| 8 | Fix SQL injection vulnerabilities | Security |
| 9 | Add missing auth to endpoints | Security |
| 10 | Fix `country_code` width to String(2) | Data integrity |
| 11 | Add `ondelete` to all FK columns | Data integrity |
| 12 | Add Pydantic validation to endpoints | Security |

### Phase 3: MEDIUM (Fix This Month)

| # | Action | Impact |
|---|--------|--------|
| 13 | Add `updated_at` to all models | Audit trail |
| 14 | Standardize timestamps to `server_default` | Consistency |
| 15 | Add error boundaries to frontend routes | UX |
| 16 | Build employee portal frontend | Feature parity |
| 17 | Add missing `features.py` atoms | RBAC coverage |
| 18 | Add provider `HAS_<SDK>` flags | Graceful degradation |

### Phase 4: LOW (Technical Debt)

| # | Action | Impact |
|---|--------|--------|
| 19 | Delete duplicate functions/classes | Maintainability |
| 20 | Remove dead code (`if False else`) | Code clarity |
| 21 | Replace `== None` with `is None` | PEP 8 compliance |
| 22 | Remove `import *` usage | Namespace clarity |
| 23 | Add missing pagination | 100K user scalability |
| 24 | Add virtualization to product grids | Performance |

---

## Statistics

| Severity | Count |
|----------|-------|
| CRITICAL | 15 |
| HIGH | 45 |
| MEDIUM | 120+ |
| LOW | 50+ |
| **TOTAL** | **350+** |
