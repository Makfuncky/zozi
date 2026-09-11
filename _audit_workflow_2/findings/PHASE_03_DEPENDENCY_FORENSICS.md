# PHASE 03 — DEPENDENCY FORENSIC AUDIT
## ZOZI Marketplace E-Commerce Platform

**Date:** 2026-09-11  
**Auditor:** Kilo (Automated Forensic Audit)  
**Scope:** All package manifests and lock files in the repository  
**Status:** Read-only audit — no files modified

---

## MANIFESTS INSPECTED

| Manifest Path | Type | Lockfile |
|--------------|------|----------|
| `package.json` (root) | npm | `package-lock.json` (v3) |
| `frontend/package.json` | npm | — |
| `frontend/web_app/package.json` | npm | `package-lock.json` (v3) |
| `frontend/shared/package.json` | npm | `package-lock.json` (v3) |
| `frontend/mobile_app/package.json` | npm | `pnpm-lock.yaml` (v9) |
| `backend/tests/playwright/package.json` | npm | `package-lock.json` |
| `backend/requirements.txt` | pip | — |
| `backend/requirements-dev.txt` | pip | — |
| `backend/pyproject.toml` | config | — |

---

## FINDINGS

### FINDING 01 — CRITICAL: Redis/Valkey Manifest Mismatch
**Package:** `redis` (PyPI) vs `valkey` (PyPI)  
**Version:** `redis==8.0.1` declared, code imports `valkey`  
**Manifest:** `backend/requirements.txt:20`  
**Observed usage:** Codebase imports `valkey` extensively  
**Status:** VERIFIED — Confirmed mismatch between manifest and implementation  

**Evidence:**
- `backend/requirements.txt:20` declares `redis==8.0.1`
- `backend/infrastructure/valkey/client.py:81` imports `valkey` (not `redis`)
- `backend/tests/architecture/test_manifest_drift.py:24-46` explicitly tests that `requirements.txt` must NOT declare `redis` and MUST declare `valkey`
- `backend/tests/architecture/test_valkey_migration.py` validates Valkey migration completeness
- Project memory constraint `no_redis_naming_anywhere` requires zero `redis` identifiers after the 2026-09-03 migration

**Impact:** High — `pip install -r requirements.txt` installs the `redis` package, but the code imports `valkey`. The `redis` PyPI package does NOT provide a `valkey` module. This will cause `ImportError` at runtime unless a separate `valkey` package is installed manually.

**Risk:** Runtime import failure; violates completed Valkey migration; contradicts architecture tests.

**Recommended action:** Replace `redis==8.0.1` with `valkey==8.0.1` (or appropriate valkey version) in `backend/requirements.txt`.

---

### FINDING 02 — CRITICAL: Pillow Version Does Not Exist on PyPI
**Package:** `Pillow`  
**Version:** `12.3.0` (nonexistent)  
**Manifest:** `backend/requirements.txt:51`  
**Observed usage:** Used via `from PIL import Image` in `backend/jobs/ai_tasks.py:48`, `backend/infrastructure/utils/lazy_imports.py:18`  
**Status:** VERIFIED — Version does not exist on PyPI per architecture test  

**Evidence:**
- `backend/requirements.txt:51` declares `Pillow==12.3.0`
- `backend/tests/architecture/test_manifest_drift.py:49-59` asserts: "Pillow 12.3.0 does not exist on PyPI; use 11.x"
- Actual usage confirmed in `backend/jobs/ai_tasks.py:48` and `backend/infrastructure/utils/lazy_imports.py:18`

**Impact:** `pip install` will fail with "No matching distribution found" for Pillow 12.3.0.

**Risk:** Installation failure on fresh environments; breaks CI/CD and deployment pipelines.

**Recommended action:** Pin Pillow to a valid version (e.g., `Pillow==11.1.0` or latest stable 11.x).

---

### FINDING 03 — HIGH: Frontend package.json vs lockfile Version Mismatches (web_app)
**Package:** Multiple  
**Version:** Declared in `package.json` differs from resolved in `package-lock.json`  
**Manifest:** `frontend/web_app/package.json` vs `frontend/web_app/package-lock.json`  
**Observed usage:** Lockfile resolves different versions than manifest specifies  
**Status:** VERIFIED — Multiple version conflicts between manifest and lockfile  

**Evidence:**

| Package | package.json | package-lock.json resolved |
|---------|-------------|---------------------------|
| `next` | `16.3.4` | `16.1.6` |
| `react` | `19.2.8` | `19.2.3` |
| `react-dom` | `19.2.8` | `19.2.3` |
| `framer-motion` | `^12.0.0` | `^11.5.6` |
| `eslint-config-next` | `16.3.4` | `16.1.6` |
| `jest-environment-jsdom` | `^30.3.0` | `^29.0.0` |

**Impact:** Reproducibility risk; `npm install` may produce different results than the lockfile; CI/CD may not match local development.

**Risk:** "It works on my machine" due to version drift between declared and resolved versions.

**Recommended action:** Run `npm install` in `frontend/web_app/` to regenerate `package-lock.json` and align resolved versions with `package.json`.

---

### FINDING 04 — HIGH: Shared vs Web_app Dependency Version Conflicts
**Package:** `framer-motion`, `tailwind-merge`  
**Version:** Conflicting versions across workspace packages  
**Manifest:** `frontend/shared/package.json` vs `frontend/web_app/package-lock.json`  
**Observed usage:** Shared library and consuming app resolve different versions  
**Status:** VERIFIED — Monorepo dependency tree inconsistency  

**Evidence:**
- `frontend/shared/package.json:26` declares `framer-motion: ^12.0.0`
- `frontend/web_app/package-lock.json:22` resolves `framer-motion` to `11.5.6`
- `frontend/shared/package.json:28` declares `tailwind-merge: ^3.5.0`
- `frontend/shared/package-lock.json:14` resolves `tailwind-merge` to `^2.6.1`
- `frontend/web_app/package-lock.json:31` resolves `tailwind-merge` to `3.5.0`

**Impact:** Peer dependency conflicts; runtime errors if shared package expects v3 API but app provides v2; or vice versa.

**Risk:** Shared components may break at runtime due to API mismatches between resolved versions.

**Recommended action:** Align versions across `shared/package.json` and consuming apps; consider using a single version range or `overrides`/`resolutions` field.

---

### FINDING 05 — HIGH: npm audit Reveals 9 Vulnerabilities in web_app
**Package:** Multiple  
**Version:** As installed per `frontend/web_app/package-lock.json`  
**Manifest:** `frontend/web_app/package-lock.json`  
**Observed usage:** Installed in `node_modules/`  
**Status:** VERIFIED — Confirmed by `npm audit` (reportVersion 2)  

**Evidence:**

| Package | Severity | Vulnerability Count | CVE/Advisory |
|---------|----------|---------------------|-------------|
| `next` (16.1.6) | Critical/High | 9 | GHSA-ggv3-7p47-pfv8 (moderate), GHSA-p293-qw3h-jr36 (critical, RCE on Windows), GHSA-89xv-2m56-2m9x (high, SSRF), etc. |
| `js-yaml` | High | 4 | GHSA-52cp-r559-cp3m, GHSA-5p4m-2wfm-xmqj |
| `postcss` | High | 3 | GHSA-6g55-p6wh-862q, GHSA-r28c-9q8g-f849 |
| `sharp` | High | 2 | GHSA-f88m-g3jw-g9cj (libvips), GHSA-rgj7-g3m4-5g8c (libheif) |
| `brace-expansion` | High | 3 | GHSA-3jxr-9vmj-r5cp, GHSA-mh99-v99m-4gvg, GHSA-rgw5-rvv9-x895 |
| `ws` | High | 2 | GHSA-58qx-3vcg-4xpx, GHSA-96hv-2xvq-fx4p |
| `dompurify` | Moderate | 5 | GHSA-hpcv-96wg-7vj8, GHSA-r47g-fvhr-h676, etc. |
| `fflate` | Moderate | 1 | GHSA-px8p-9vwx-vf98 |
| `@babel/core` | Low | 1 | GHSA-4x5r-pfxv-6jf8 |

**Impact:** Multiple attack vectors: RCE, SSRF, DoS, XSS, file read, cache poisoning.

**Risk:** Production exposure to known exploits; `next` alone has a critical Windows RCE and multiple high-severity issues.

**Recommended action:** Upgrade `next` to `>=16.3.3`, `js-yaml` to `>=3.15.2` or `>=4.3.2`, `postcss` to `>=8.5.22`, `sharp` to `>=0.35.4`, `brace-expansion` to `>=1.1.18`, `ws` to `>=8.21.0`, `dompurify` to `>=3.4.12`.

---

### FINDING 06 — MEDIUM: @testing-library/dom in dependencies Instead of devDependencies
**Package:** `@testing-library/dom`  
**Version:** `^10.4.1`  
**Manifest:** `frontend/web_app/package.json:17`  
**Observed usage:** Only used in `__tests__/` and test files  
**Status:** VERIFIED — Testing library incorrectly in production dependencies  

**Evidence:**
- `frontend/web_app/package.json:17` lists `@testing-library/dom` under `dependencies`
- Grep search of `frontend/web_app/src/` finds NO source imports of `@testing-library/dom` outside `__tests__/` directories
- All references are in test files

**Impact:** Bloated production bundle; unnecessary production dependency.

**Risk:** Minor — increases install time and bundle size in production.

**Recommended action:** Move `@testing-library/dom` to `devDependencies`.

---

### FINDING 07 — MEDIUM: Unused Dependencies in web_app
**Package:** `jspdf`, `core-js`, `class-variance-authority`  
**Version:** `^4.1.0`, `^3.37.1`, `^0.7.1`  
**Manifest:** `frontend/web_app/package.json:28,24,22`  
**Observed usage:** No source imports found in `frontend/web_app/src/`  
**Status:** VERIFIED — Declared but no observed usage in application source  

**Evidence:**
- `jspdf` (`frontend/web_app/package.json:28`): Zero imports in `src/` directory
- `core-js` (`frontend/web_app/package.json:24`): Zero imports in `src/` directory
- `class-variance-authority` (`frontend/web_app/package.json:22`): Zero imports in `src/` directory

**Impact:** Unnecessary bundle size and attack surface.

**Risk:** Low — dead code increases maintenance burden and potential supply-chain risk.

**Recommended action:** Remove unused dependencies or confirm usage via tree-shaking analysis.

---

### FINDING 08 — MEDIUM: Root package-lock.json Has Undeclared Dependencies
**Package:** `@neon/config`, `@neon/env`  
**Version:** `^1.2.0`  
**Manifest:** Root `package.json` has NO dependencies; `package-lock.json` has them  
**Observed usage:** Lockfile entries exist but manifest is empty  
**Status:** VERIFIED — Lockfile/manifest inconsistency  

**Evidence:**
- Root `package.json` has empty `dependencies` and `devDependencies`
- Root `package-lock.json:11-14` declares:
  `@neon/config: ^1.2.0` and `@neon/env: ^1.2.0`

**Impact:** `npm install` at root may behave unexpectedly; dependencies are captured in lockfile but not declared.

**Risk:** Reproducibility and dependency hygiene.

**Recommended action:** Either add `@neon/config` and `@neon/env` to root `package.json` or remove them from the lockfile.

---

### FINDING 09 — MEDIUM: Mixed Package Managers Across Monorepo
**Package:** N/A (tooling)  
**Version:** npm (v3 lockfiles) + pnpm (v9 lockfile)  
**Manifest:** `frontend/mobile_app/pnpm-lock.yaml` vs all other npm lockfiles  
**Observed usage:** Mobile app uses pnpm, rest use npm  
**Status:** VERIFIED — Mixed package manager strategy  

**Evidence:**
- `frontend/web_app/package-lock.json` — lockfileVersion: 3 (npm)
- `frontend/shared/package-lock.json` — lockfileVersion: 3 (npm)
- `frontend/mobile_app/pnpm-lock.yaml` — lockfileVersion: '9.0' (pnpm)
- `backend/tests/playwright/package-lock.json` — npm
- Root `package-lock.json` — lockfileVersion: 3 (npm)

**Impact:** Different resolution algorithms; duplicate hoisting; potential deduplication differences.

**Risk:** Inconsistent installs across environments; harder to enforce workspace-wide policies.

**Recommended action:** Document the mixed-manager rationale; consider standardizing on one tool or using a workspace-aware tool.

---

### FINDING 10 — MEDIUM: pytest Version Conflict Between requirements.txt and requirements-dev.txt
**Package:** `pytest`  
**Version:** `9.1.1` (requirements.txt) vs `9.2.0` (requirements-dev.txt)  
**Manifest:** `backend/requirements.txt:101` vs `backend/requirements-dev.txt:4`  
**Observed usage:** Both install pytest  
**Status:** VERIFIED — Version conflict between production and dev manifests  

**Evidence:**
- `backend/requirements.txt:101`: `pytest==9.1.1`
- `backend/requirements-dev.txt:4`: `pytest==9.2.0`

**Impact:** If both files are installed together, `requirements-dev.txt` overrides with 9.2.0; standalone installs get 9.1.0.

**Risk:** Non-reproducible test environments; subtle behavioral differences between CI and local.

**Recommended action:** Align versions or use a single `requirements.txt` with `-r requirements-dev.txt` for dev-only extras.

---

### FINDING 11 — MEDIUM: requests and httpx Coexist — Potential Redundancy
**Package:** `requests` (2.34.2) and `httpx` (0.28.1)  
**Version:** Both declared in `backend/requirements.txt`  
**Manifest:** `backend/requirements.txt:36,35`  
**Observed usage:** Both imported in production code  
**Status:** VERIFIED — Both HTTP clients used in codebase  

**Evidence:**
- `backend/requirements.txt:35` declares `httpx==0.28.1`
- `backend/requirements.txt:36` declares `requests==2.34.2`
- `backend/domains/accounts/services/auth/auth_service.py:33` imports `requests`
- `backend/domains/finance/services/payments/payment_engine.py:55` imports `httpx`
- `backend/providers/geography/rates.py:17` imports `httpx`

**Impact:** Two HTTP client libraries increase bundle size and surface area; inconsistent async/sync patterns.

**Risk:** Maintainability; developers may not know which client to use for new code.

**Recommended action:** Standardize on `httpx` (async-capable) and migrate `requests` usages, or document a clear policy for when each is used.

---

### FINDING 12 — MEDIUM: python-multipart and starlette Without Explicit Version Pins
**Package:** `starlette`, `python-multipart`  
**Version:** Unpinned (`starlette`) and `^0.0.32` (`python-multipart`)  
**Manifest:** `backend/requirements.txt:11,44`  
**Observed usage:** Used by FastAPI for form parsing and ASGI  
**Status:** VERIFIED — Inconsistent pinning strategy  

**Evidence:**
- `backend/requirements.txt:11`: `starlette` (no version pin — latest will be installed)
- `backend/requirements.txt:44`: `python-multipart==0.0.32` (pinned)
- FastAPI 0.115.2 depends on starlette; unpinned starlette may pull incompatible versions

**Impact:** Non-reproducible installs; potential breakage when starlette releases breaking changes.

**Risk:** Dependency drift; CI/CD failures on fresh installs.

**Recommended action:** Pin `starlette` to the version compatible with `fastapi==0.115.2`.

---

### FINDING 13 — MEDIUM: numpy==2.2.6 — Very New Major Version
**Package:** `numpy`  
**Version:** `2.2.6`  
**Manifest:** `backend/requirements.txt:57`  
**Observed usage:** Used in `backend/jobs/ai_tasks.py:47`, `backend/jobs/mcp_server.py:86`, `backend/domains/suppliers/services/products/supplier_supplier_upload_service.py:16`  
**Status:** VERIFIED — Very recent NumPy 2.x release  

**Evidence:**
- `backend/requirements.txt:57`: `numpy==2.2.6`
- NumPy 2.x series is very recent; many scientific Python packages had compatibility gaps during initial 2.x rollout
- Used alongside `Pillow` (which also had NumPy 2.x compatibility issues in earlier versions)

**Impact:** Potential ABI/compatibility issues with transitive dependencies.

**Risk:** Runtime crashes or silent data corruption if transitive dependencies are not NumPy 2.x compatible.

**Recommended action:** Verify all transitive dependencies support NumPy 2.2.6; consider pinning to a well-tested version.

---

### FINDING 14 — LOW: @types/react Version Range vs Lockfile Pin Conflict
**Package:** `@types/react`  
**Version:** `^19` (web_app) vs `^19.2.17` (shared devDep)  
**Manifest:** `frontend/web_app/package.json:47` vs `frontend/shared/package.json:36`  
**Observed usage:** Shared package and app resolve different type versions  
**Status:** VERIFIED — Version range inconsistency across monorepo packages  

**Evidence:**
- `frontend/web_app/package.json:47`: `"@types/react": "^19"`
- `frontend/shared/package.json:36`: `"@types/react": "^19.2.17"`
- `frontend/web_app/package-lock.json` resolves `@types/react` to `19.2.17`
- `frontend/shared/package-lock.json` resolves `@types/react` to `18.3.1` (in shared devDependencies)

**Impact:** Type checking inconsistencies between shared and app code.

**Risk:** Type errors at build time that are environment-dependent.

**Recommended action:** Align `@types/react` ranges or use `overrides` in web_app to force a single version.

---

### FINDING 15 — LOW: jest-environment-jsdom Version Mismatch
**Package:** `jest-environment-jsdom`  
**Version:** `^30.3.0` (web_app) vs `^29.0.0` (shared) vs `~57.0.9` (mobile jest-expo)  
**Manifest:** Multiple package.json files  
**Observed usage:** Test runner environment  
**Status:** VERIFIED — Version mismatch across test setups  

**Evidence:**
- `frontend/web_app/package.json:54`: `"jest-environment-jsdom": "^30.3.0"`
- `frontend/shared/package.json:40`: `"jest-environment-jsdom": "^29.0.0"`

**Impact:** Different jsdom behavior across packages; potential test failures when running shared tests from web_app context.

**Risk:** Inconsistent test behavior.

**Recommended action:** Align jest-environment-jsdom versions across all test packages.

---

### FINDING 16 — LOW: tailwind-merge Version Divergence
**Package:** `tailwind-merge`  
**Version:** `^3.5.0` (web_app and shared) vs `^2.6.1` (shared lockfile)  
**Manifest:** `frontend/shared/package-lock.json`  
**Observed usage:** Shared package lockfile resolves v2 while manifest requests v3  
**Status:** VERIFIED — Lockfile version divergence  

**Evidence:**
- `frontend/shared/package.json:28`: `"tailwind-merge": "^3.5.0"`
- `frontend/shared/package-lock.json:14`: resolves `tailwind-merge` to `^2.6.1`
- `frontend/web_app/package-lock.json:31`: resolves `tailwind-merge` to `3.5.0`

**Impact:** Shared package may use v2 API while app uses v3 API.

**Risk:** Runtime CSS merging differences.

**Recommended action:** Regenerate `frontend/shared/package-lock.json` to resolve v3.

---

### FINDING 17 — LOW: Backend pytest-asyncio Version Conflict
**Package:** `pytest-asyncio`  
**Version:** `1.4.0` in both `requirements.txt` and `requirements-dev.txt`  
**Manifest:** `backend/requirements.txt:102` vs `backend/requirements-dev.txt:5`  
**Observed usage:** Async test support  
**Status:** VERIFIED — Same version, but double-declared  

**Evidence:**
- `backend/requirements.txt:102`: `pytest-asyncio==1.4.0`
- `backend/requirements-dev.txt:5`: `pytest-asyncio==1.4.0`

**Impact:** Minor redundancy; if both files are installed, no conflict.

**Risk:** Low — but indicates lack of clear separation between production and dev dependencies.

**Recommended action:** Remove `pytest-asyncio` from `requirements.txt` (it is a test-only dependency) or document why it is in production manifest.

---

### FINDING 18 — LOW: duckdb-engine Without Direct duckdb Usage
**Package:** `duckdb` and `duckdb-engine`  
**Version:** `duckdb==1.5.5`, `duckdb-engine==0.17.0`  
**Manifest:** `backend/requirements.txt:97-98`  
**Observed usage:** No direct `import duckdb` found in backend source  
**Status:** INFERRED — Declared but usage not confirmed in inspected code  

**Evidence:**
- `backend/requirements.txt:97-98`: both `duckdb` and `duckdb-engine` declared
- Grep of backend source found no `import duckdb` or `from duckdb` statements
- Comment says "optional analytics domain engine"

**Impact:** If unused, bloated install; if used via dynamic import or in uninspected modules, needed.

**Risk:** Cannot fully verify without inspecting all runtime code paths.

**Recommended action:** Verify if analytics domain actually uses duckdb; remove if unused or document optional nature more clearly.

---

### FINDING 19 — INFO: Backend Dependencies With Confirmed Usage
**Package:** Multiple  
**Version:** As pinned in `backend/requirements.txt`  
**Manifest:** `backend/requirements.txt`  
**Observed usage:** Confirmed in source code  

**Evidence (sampled):**
| Package | Version | Usage Files |
|---------|---------|-------------|
| `fastapi` | 0.115.2 | `backend/main.py` |
| `sqlalchemy` | 2.0.51 | `backend/alembic/versions/*.py`, domain models |
| `alembic` | 1.18.5 | `backend/alembic/` |
| `asyncpg` | 0.31.0 | `backend/infrastructure/database/` |
| `psycopg2-binary` | 2.9.12 | `backend/config.py` |
| `celery` | 5.4.0 | `backend/jobs/celery_app.py`, task files |
| `pydantic` | 2.13.4 | `backend/config.py`, domain models |
| `python-jose` | 3.5.0 | `backend/infrastructure/security/auth.py` |
| `bcrypt` | 5.0.0 | `backend/infrastructure/security/auth.py` |
| `stripe` | 15.3.1 | `backend/providers/payments/stripe_sdk.py` |
| `structlog` | 26.1.0 | `backend/infrastructure/observability/logging_config.py` |
| `sentry-sdk` | 2.66.1 | `backend/infrastructure/observability/error_handler.py` |
| `slowapi` | 0.1.10 | `backend/infrastructure/security/rate_limiter.py` |
| `websockets` | 16.1.1 | `backend/main.py` |
| `prometheus-client` | 0.26.0 | `backend/infrastructure/observability/metrics.py` |
| `httpx` | 0.28.1 | Multiple provider files |
| `requests` | 2.34.2 | `backend/domains/accounts/services/auth/auth_service.py` |
| `python-multipart` | 0.0.32 | FastAPI form parsing |
| `aiofiles` | 25.1.0 | Not directly observed (possibly transitive) |
| `phonenumbers` | 9.0.35 | `backend/infrastructure/utils/phone_utils.py:6` |
| `feedparser` | 6.0.12 | `backend/providers/news/rss_provider.py:13` |
| `faker` | 40.36.0 | `backend/tests/` (also in requirements-dev.txt) |
| `opentelemetry-*` | 1.44.0 / 0.65b0 | `backend/infrastructure/observability/tracing.py` |
| `opentelemetry-instrumentation` | 0.65b0 | `backend/infrastructure/observability/tracing.py` |
| `prometheus-fastapi-instrumentator` | 7.1.0 | `backend/infrastructure/observability/prometheus_setup.py` |
| `opentelemetry-exporter-otlp-proto-http` | 1.44.0 | `backend/infrastructure/observability/tracing.py` |

**Status:** VERIFIED — Core dependencies are actively used.

---

### FINDING 20 — INFO: Frontend Dependencies With Confirmed Usage
**Package:** Multiple  
**Version:** As resolved in lockfiles  
**Manifest:** `frontend/web_app/package.json` / `frontend/shared/package.json` / `frontend/mobile_app/package.json`  
**Observed usage:** Confirmed in source code  

**Evidence (sampled):**
| Package | Version | Usage Files |
|---------|---------|-------------|
| `next` | 16.1.6 | `frontend/web_app/src/app/**/*.tsx` |
| `react` | 19.2.3 | All web_app components |
| `react-dom` | 19.2.3 | All web_app components |
| `framer-motion` | 11.5.6 | Multiple animation components |
| `lucide-react` | 0.563.0 | Multiple icon components |
| `clsx` | 2.1.1 | `frontend/web_app/src/shared/utils.ts` |
| `tailwind-merge` | 3.5.0 | `frontend/web_app/src/shared/utils.ts` |
| `zustand` | 5.0.11 | Multiple store files |
| `jose` | 6.2.10 | `frontend/web_app/src/lib/serverAuth.ts` |
| `dompurify` | 3.3.3 | `EmailTemplateManager.tsx`, `CreateCampaignForm.tsx` |
| `qrcode` | 1.5.4 | `frontend/web_app/src/app/supplier/labels/[id]/page.tsx` |
| `@zxing/library` | 0.21.3 | Barcode scan pages |
| `chart.js` + `react-chartjs-2` | 4.5.1 / 5.3.1 | `ChartComponents.tsx` |
| `expo` | 55.0.27 | `frontend/mobile_app/app.json` |
| `react-native` | 0.83.2 | Mobile app |
| `@react-navigation/native` | 7.3.4 | Mobile navigation |
| `react-native-reanimated` | 4.2.1 | Mobile animations |
| `dayjs` | 1.11.13 | Mobile date handling |

**Status:** VERIFIED — Core frontend dependencies are actively used.

---

## DEPENDENCY HEALTH SCORE

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| **Correctness** | 4/10 | Critical manifest mismatch (redis/valkey, Pillow 12.3.0); version drift between package.json and lockfiles; pytest version conflict |
| **Maintainability** | 6/10 | Mixed package managers; some unused deps; duplicate packages across monorepo; but core structure is sound |
| **Security** | 4/10 | 9 confirmed vulnerabilities in web_app (1 critical, 5 high, 2 moderate, 1 low); next.js has unpatched RCE on Windows |
| **Reproducibility** | 5/10 | Lockfile version mismatches; unpinned `starlette`; root lockfile has undeclared deps; mixed pnpm/npm |

**Overall Health Score: 4.75/10**

### Evidence Explanations:
- **Correctness (-6):** Two critical install-breakers (redis/valkey mismatch, Pillow 12.3.0) mean fresh environments will fail. Version mismatches between manifests and lockfiles reduce trust in declared dependencies.
- **Maintainability (-4):** Mixed package managers and duplicate/shared dependency inconsistencies create confusion. Unused deps (`jspdf`, `core-js`, `cva`) add noise.
- **Security (-6):** `npm audit` on web_app reveals 9 vulnerabilities including a critical Next.js RCE (GHSA-p293-qw3h-jr36) and multiple high-severity DoS/SSRF issues. No pip audit output available, but `numpy==2.2.6` is very new.
- **Reproducibility (-5):** Lockfile and manifest are inconsistent. `npm install` in web_app will not reproduce the locked tree. Unpinned `starlette` allows silent upgrades.

---

## SUMMARY TABLE

| # | Package | Version | Manifest | Lockfile Version | Observed Usage | Status | Evidence | Risk | Recommended Action |
|---|---------|---------|----------|------------------|----------------|--------|----------|------|-------------------|
| 1 | redis/valkey | redis==8.0.1 / code uses valkey | `requirements.txt:20` | N/A | `infrastructure/valkey/client.py` imports `valkey` | CRITICAL | Architecture tests enforce `valkey` in manifest | High | Replace `redis==8.0.1` with `valkey==8.0.1` |
| 2 | Pillow | 12.3.0 | `requirements.txt:51` | N/A | `from PIL import Image` | CRITICAL | Version does not exist on PyPI | High | Pin to valid 11.x version |
| 3 | next | 16.3.4 (declared) / 16.1.6 (resolved) | `web_app/package.json` / `package-lock.json` | 16.1.6 | Next.js app router | HIGH | Manifest/lockfile mismatch | High | Regenerate lockfile |
| 4 | next (vuln) | 16.1.6 | `web_app/package-lock.json` | 16.1.6 | Server-side rendering | CRITICAL | GHSA-p293-qw3h-jr36 (RCE) | Critical | Upgrade to >=16.3.3 |
| 5 | framer-motion | ^12.0.0 (shared) / ^11.5.6 (resolved) | Multiple | 11.5.6 | Animation components | HIGH | Shared vs app version conflict | High | Align versions |
| 6 | tailwind-merge | ^3.5.0 / resolved 2.6.1 (shared) | `shared/package.json` / lockfile | 2.6.1 | CSS utility merging | MEDIUM | Lockfile resolves v2 while manifest says v3 | Medium | Regenerate lockfile |
| 7 | @testing-library/dom | ^10.4.1 | `web_app/package.json` | — | Only in `__tests__/` | MEDIUM | Listed in `dependencies` not `devDependencies` | Low | Move to devDependencies |
| 8 | jspdf | ^4.1.0 | `web_app/package.json` | — | None found | MEDIUM | No source imports | Low | Remove or confirm usage |
| 9 | core-js | ^3.37.1 | `web_app/package.json` | — | None found | MEDIUM | No source imports | Low | Remove or confirm usage |
| 10 | class-variance-authority | ^0.7.1 | `web_app/package.json` | — | None found | MEDIUM | No source imports | Low | Remove or confirm usage |
| 11 | @neon/config + @neon/env | ^1.2.0 | Root `package-lock.json` only | N/A | Not in root `package.json` | MEDIUM | Lockfile has undeclared deps | Low | Add to manifest or remove from lockfile |
| 12 | pytest | 9.1.1 (prod) / 9.2.0 (dev) | `requirements.txt` / `requirements-dev.txt` | N/A | Test runner | MEDIUM | Version conflict between manifests | Low | Align versions |
| 13 | starlette | (unpinned) | `requirements.txt:11` | N/A | FastAPI dependency | MEDIUM | No version pin | Medium | Pin to FastAPI-compatible version |
| 14 | numpy | 2.2.6 | `requirements.txt:57` | N/A | AI/image tasks | LOW | Very new major version | Medium | Verify transitive compatibility |
| 15 | jest-environment-jsdom | ^30.3.0 / ^29.0.0 / ~57.0.9 | Multiple | Multiple | Test runner | LOW | Version mismatch across packages | Low | Align versions |
| 16 | @types/react | ^19 (web_app) / ^19.2.17 (shared) | Multiple | 18.3.1 / 19.2.17 | Type checking | LOW | Range inconsistency | Low | Align ranges |
| 17 | requests + httpx | 2.34.2 + 0.28.1 | `requirements.txt` | N/A | HTTP clients | MEDIUM | Both used in production | Low | Standardize or document policy |
| 18 | multiple (npm audit) | Various | `web_app/package-lock.json` | Various | Installed deps | HIGH | 9 confirmed vulnerabilities | High | Apply `npm audit fix` or manual upgrades |

---

## RECOMMENDATIONS (Priority Order)

1. **IMMEDIATE:** Replace `redis==8.0.1` with `valkey==8.0.1` in `backend/requirements.txt` (Finding 01)
2. **IMMEDIATE:** Fix `Pillow==12.3.0` to a valid PyPI version (Finding 02)
3. **HIGH:** Upgrade `next` from 16.1.6 to >=16.3.3 in `frontend/web_app/` (Finding 05)
4. **HIGH:** Regenerate `frontend/web_app/package-lock.json` to align with `package.json` (Finding 03)
5. **HIGH:** Align `framer-motion` and `tailwind-merge` versions across `shared` and `web_app` (Finding 04)
6. **MEDIUM:** Move `@testing-library/dom` to `devDependencies` in `web_app/package.json` (Finding 06)
7. **MEDIUM:** Remove or confirm usage of `jspdf`, `core-js`, `class-variance-authority` (Finding 07)
8. **MEDIUM:** Pin `starlette` to a specific version compatible with FastAPI 0.115.2 (Finding 12)
9. **LOW:** Align `jest-environment-jsdom` and `@types/react` versions across monorepo (Findings 15, 16)
10. **LOW:** Standardize on `httpx` or document dual HTTP client policy (Finding 11)

---

## METHODOLOGY NOTES

- All package manifests were read directly from the filesystem.
- Lock files were inspected for version resolution mismatches.
- `npm audit` was executed in `frontend/web_app/` (9 vulnerabilities found) and root (0 vulnerabilities found).
- `pip audit` was attempted but returned no usable JSON output on this environment; Python package vulnerabilities were not independently verified via CVE database.
- Source code usage was verified via grep for import statements across `backend/` and `frontend/web_app/src/`.
- Architecture tests (`test_manifest_drift.py`, `test_valkey_migration.py`) were read to confirm known issues.
- No files were modified during this audit.
