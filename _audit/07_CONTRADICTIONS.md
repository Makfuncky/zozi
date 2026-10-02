# CONTRADICTIONS — ZOZI E-Commerce Platform

Harvested from canonical docs (`_most_imp_docx/ARCHITECTURE_STACK.md`, `_most_imp_docx/TECHNOLOGY_STACK.md`) vs actual code/config/lockfiles at HEAD.

---

## CONTRAD-001

- **Category:** target_vs_code
- **Source A (L3):** `_most_imp_docx/ARCHITECTURE_STACK.md:539` — "Fixed set: admin, customer, employee, logistics, supplier. The `admin` module serves multiple roles."
- **Source B (L0):** `backend/modules/finance/__init__.py:1` — "Finance module — actor-agnostic finance router surface."
- **Conflict:** Canonical defines exactly 5 modules; a 6th `modules/finance` module exists with its own router (`cash_management.py`), violating the fixed module set.
- **Impact:** Breaks Law 13 (fixed 5 modules); route prefix `/finance/*` is mounted outside the canonical module boundary, creating an unauthorized actor surface.
- **Project completion blocker:** yes
- **Recommendation:** `modules/finance` is non-canonical. Finance endpoints must live under the `admin` module router (which already exposes `finance.py`) or another canonical module; remove `modules/finance`.
- **User decision required:** yes

---

## CONTRAD-002

- **Category:** target_vs_code
- **Source A (L3):** `_most_imp_docx/ARCHITECTURE_STACK.md:88-103` — "providers/payments — 1:1 payment gateway adapters (Stripe, PayPal, regional gateways)"
- **Source B (L0):** `backend/domains/payments/__init__.py:1` — "payments domain package."
- **Conflict:** Payments is defined as a provider-only concern in canonical docs, but `domains/payments/` exists as a full domain (models, services, schemas, events.py, features.py, ports.py, subscribers.py).
- **Impact:** Violates Law 12 (fixed 15 domains); creates a 16th domain and duplicates payment logic already in `domains/finance/services/payments/`.
- **Project completion blocker:** yes
- **Recommendation:** `domains/payments/` is non-canonical. Remove the domain package and keep payment orchestration exclusively in `domains/finance/services/payments/`; keep only `providers/payments/` for SDK adapters.
- **User decision required:** yes

---

## CONTRAD-003

- **Category:** target_vs_code
- **Source A (L3):** `_most_imp_docx/ARCHITECTURE_STACK.md:354` — "Approved non-canonical schemas: media (media assets / upload sessions — no dedicated domain yet)"
- **Source B (L0):** `backend/domains/media/__init__.py` (directory exists with models, schemas, services, events.py, features.py, ports.py, subscribers.py)
- **Conflict:** Canonical explicitly states `media` has no dedicated domain, yet `domains/media/` is structured as a full domain package.
- **Impact:** Violates Law 12 (fixed 15 domains); blurs the boundary between a Postgres schema and a domain, making future migration to canonical domain harder.
- **Project completion blocker:** partial
- **Recommendation:** Either add `media` as the 16th canonical domain (requires ARCHITECTURE_STACK.md update) or demote `domains/media/` to a schema-level package outside `domains/`.
- **User decision required:** yes

---

## CONTRAD-004

- **Category:** target_vs_code
- **Source A (L3):** `_most_imp_docx/ARCHITECTURE_STACK.md:88-103` — Canonical providers list: ai, barcode, bg_removal, comms, finance, geography, image, ocr, payments, qr, security, shipping, storage, async_workers, _base.py.
- **Source B (L0):** `backend/providers/news/`, `backend/providers/automation/`, `backend/providers/scanner/`, `backend/providers/voice/`, `backend/providers/analytics/` — directories exist.
- **Conflict:** Five provider packages exist that are not in the canonical provider tree.
- **Impact:** Violates Law 9/16 (tools in providers); undocumented providers may import forbidden SDKs or bypass circuit-breaker/retry conventions.
- **Project completion blocker:** no
- **Recommendation:** Either document the five extra providers in ARCHITECTURE_STACK.md or remove them if they are unused scaffolding.
- **User decision required:** yes

---

## CONTRAD-005

- **Category:** tech_target_vs_lockfile
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:23` — "FastAPI 0.141.x"
- **Source B (L0):** `backend/requirements.txt:8` — "fastapi==0.115.2"
- **Conflict:** 25+ minor-version gap between canonical target and locked dependency.
- **Impact:** Missing features, security fixes, and behavioral changes from 26+ releases; may break middleware/routing contracts the code was written against.
- **Project completion blocker:** yes
- **Recommendation:** `requirements.txt` is authoritative for what is installed; bump FastAPI to 0.141.x or update TECHNOLOGY_STACK.md to match the installed version.
- **User decision required:** yes

---

## CONTRAD-006

- **Category:** tech_target_vs_lockfile
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:25` — "Uvicorn 0.35.0+"
- **Source B (L0):** `backend/requirements.txt:9` — "uvicorn[standard]==0.51.0"
- **Conflict:** Locked version (0.51.0) is newer than the canonical floor (0.35.0+), but the range is not documented.
- **Impact:** Behavior drift in HTTP/WebSocket handling; may invalidate assumptions in middleware and lifespan code.
- **Project completion blocker:** partial
- **Recommendation:** Pin Uvicorn in TECHNOLOGY_STACK.md to the installed version or validate 0.51.0 against the middleware contract.
- **User decision required:** yes

---

## CONTRAD-007

- **Category:** tech_target_vs_lockfile
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:45` — "Alembic 1.19.1+"
- **Source B (L0):** `backend/requirements.txt:15` — "alembic==1.18.5"
- **Conflict:** Locked Alembic is one minor version below the canonical floor.
- **Impact:** May lack migration autogenerate fixes or env-prefix support needed by the 77-migration codebase.
- **Project completion blocker:** partial
- **Recommendation:** Bump Alembic to 1.19.1+.
- **User decision required:** no

---

## CONTRAD-008

- **Category:** tech_target_vs_lockfile
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:31` — "pydantic-settings 2.9.1+"
- **Source B (L0):** `backend/requirements.txt:40` — "pydantic-settings==2.7.1"
- **Conflict:** Two minor versions below canonical floor.
- **Impact:** May lack env-prefix or `env_nested_delimiter` fixes relied on by `config.py`'s `SettingsConfigDict`.
- **Project completion blocker:** partial
- **Recommendation:** Bump pydantic-settings to 2.9.1+.
- **User decision required:** no

---

## CONTRAD-009

- **Category:** tech_target_vs_lockfile
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:136` — "prometheus-fastapi-instrumentator 8.1.0+"
- **Source B (L0):** `backend/requirements.txt:63` — "prometheus-fastapi-instrumentator==7.1.0"
- **Conflict:** One major version below canonical floor.
- **Impact:** Missing metrics buckets, route-labeling fixes, or FastAPI compatibility patches required by the observability stack.
- **Project completion blocker:** partial
- **Recommendation:** Bump to 8.1.0+ or update TECHNOLOGY_STACK.md.
- **User decision required:** yes

---

## CONTRAD-010

- **Category:** tech_target_vs_lockfile
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:134` — "sentry-sdk[fastapi] 2.68.1"
- **Source B (L0):** `backend/requirements.txt:61` — "sentry-sdk==2.66.1"
- **Conflict:** Two patch versions below canonical; missing `[fastapi]` extra.
- **Impact:** May lack FastAPI-specific integration (request-id breadcrumbs, route error handling).
- **Project completion blocker:** partial
- **Recommendation:** Install `sentry-sdk[fastapi]==2.68.1`.
- **User decision required:** no

---

## CONTRAD-011

- **Category:** tech_target_vs_lockfile
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:99` — "stripe (SDK) 15.5.1"
- **Source B (L0):** `backend/requirements.txt:91` — "stripe==15.3.1"
- **Conflict:** Two patch versions below canonical.
- **Impact:** May miss payment-method or webhook signature fixes required for the payment orchestration layer.
- **Project completion blocker:** partial
- **Recommendation:** Bump stripe to 15.5.1.
- **User decision required:** no

---

## CONTRAD-012

- **Category:** tech_target_vs_lockfile
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:72` — "puremagic 2.2.0" and "`python-magic` is forbidden"
- **Source B (L0):** `backend/requirements.txt:48` — "python-magic==0.4.27"
- **Conflict:** Forbidden package `python-magic` is locked instead of canonical `puremagic`; `puremagic` is absent from requirements entirely.
- **Impact:** Introduces libmagic CVE surface; violates the approved MIME-type detection stack.
- **Project completion blocker:** no
- **Recommendation:** Replace `python-magic==0.4.27` with `puremagic==2.2.0` in requirements.txt.
- **User decision required:** no

---

## CONTRAD-013

- **Category:** tech_target_vs_lockfile
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:43` — "`psycopg`/`psycopg2` are forbidden in production code"
- **Source B (L0):** `backend/requirements.txt:17` — "psycopg2-binary==2.9.12"
- **Conflict:** Forbidden package `psycopg2-binary` is present in the dependency manifest.
- **Impact:** Adds a forbidden driver to the image; violates the asyncpg-only database policy.
- **Project completion blocker:** no
- **Recommendation:** Remove `psycopg2-binary==2.9.12` from requirements.txt.
- **User decision required:** no

---

## CONTRAD-014

- **Category:** tech_target_vs_lockfile
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:123` — "`pytz`/`tzlocal` are forbidden"
- **Source B (L0):** `backend/requirements.txt:79` — "pytz==2026.3.post1" and `backend/requirements.txt:80` — "tzlocal==5.4.4"
- **Conflict:** Two forbidden timezone libraries are locked.
- **Impact:** Violates the zoneinfo-stdlib policy; adds unnecessary dependencies that may shadow stdlib behavior.
- **Project completion blocker:** no
- **Recommendation:** Remove `pytz` and `tzlocal` from requirements.txt.
- **User decision required:** no

---

## CONTRAD-015

- **Category:** tech_target_vs_lockfile
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:98` — "`requests` is forbidden"
- **Source B (L0):** `backend/requirements.txt:36` — "requests==2.34.2"
- **Conflict:** Forbidden sync HTTP client is present in the dependency manifest.
- **Impact:** Pulls a forbidden package into the image; risk of blocking the event loop if imported in async code.
- **Project completion blocker:** no
- **Recommendation:** Remove `requests==2.34.2` from requirements.txt.
- **User decision required:** no

---

## CONTRAD-016

- **Category:** package_vs_import
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:89` — "fastapi-limiter-valkey latest stable"
- **Source B (L0):** `backend/requirements.txt:73` — "slowapi==0.1.10" and `backend/requirements.txt:74` — "limits==5.8.0"
- **Source C (L0):** `backend/infrastructure/security/rate_limiter.py:24` — "from fastapi_limiter_valkey import RateLimiter as _RateLimiter"
- **Conflict:** Canonical rate limiter is `fastapi-limiter-valkey` (imported in production), but `requirements.txt` declares `slowapi`/`limits` and omits `fastapi-limiter-valkey`.
- **Impact:** The declared dependency set does not match the imported production set; builds may fail if `fastapi-limiter-valkey` is not transitively available.
- **Project completion blocker:** yes
- **Recommendation:** Replace `slowapi==0.1.10` and `limits==5.8.0` with `fastapi-limiter-valkey` in requirements.txt.
- **User decision required:** yes

---

## CONTRAD-017

- **Category:** tech_target_vs_lockfile
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:26` — "uvloop 0.21.0" and `_most_imp_docx/TECHNOLOGY_STACK.md:27` — "httptools 0.7.0"
- **Source B (L0):** `backend/requirements.txt:1-102` — neither `uvloop` nor `httptools` listed.
- **Conflict:** Canonical Uvicorn dependencies are absent from the pinned manifest.
- **Impact:** Uvicorn may fall back to stdlib asyncio and pure-Python HTTP parsing, losing the documented 2–4× throughput benefit.
- **Project completion blocker:** no
- **Recommendation:** Add `uvloop==0.21.0` and `httptools==0.7.0` to requirements.txt.
- **User decision required:** no

---

## CONTRAD-018

- **Category:** tech_target_vs_lockfile
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:90` — "pybreaker 1.4.1"
- **Source B (L0):** `backend/requirements.txt:1-102` — `pybreaker` not listed.
- **Conflict:** Canonical circuit-breaker library is absent from the pinned manifest.
- **Impact:** Provider calls lack the documented circuit-breaker wrapper; cascade failures are unguarded.
- **Project completion blocker:** partial
- **Recommendation:** Add `pybreaker==1.4.1` to requirements.txt.
- **User decision required:** no

---

## CONTRAD-019

- **Category:** code_vs_config
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:392` — "DEFAULT_COUNTRY default US"
- **Source B (L0):** `backend/config.py:279` — "default_country: str = Field(default="AE")"
- **Conflict:** Canonical default country is `US`; code defaults to `AE` (UAE).
- **Impact:** RLS session context, localization, and tax rules default to the wrong country for non-UAE deployments.
- **Project completion blocker:** partial
- **Recommendation:** Align `config.py` default to `US` or update TECHNOLOGY_STACK.md to reflect the `AE` market focus.
- **User decision required:** yes

---

## CONTRAD-020

- **Category:** code_vs_config
- **Source A (L3):** `_most_imp_docx/ARCHITECTURE_STACK.md:546` — "No float for money — Monetary values MUST use Decimal or Numeric. Float FORBIDDEN for money."
- **Source B (L0):** `backend/config.py:204` — "vat_rate: float = Field(default=0.0)" and `backend/config.py:205` — "zozi_commission_rate: float = Field(default=0.1)"
- **Source C (L0):** `backend/config.py:79` — '_FLOAT_KEYS = {"vat_rate", "zozi_commission_rate", "whatsapp_min_delay"}'
- **Conflict:** Money-related config values are typed as `float` in the typed settings, violating Law 19.
- **Impact:** Rounding errors in VAT and commission calculations; financial discrepancies in orders and payouts.
- **Project completion blocker:** yes
- **Recommendation:** Change `vat_rate` and `zozi_commission_rate` to `Decimal` in `config.py` and `_FLOAT_KEYS`.
- **User decision required:** no

---

## CONTRAD-021

- **Category:** frontend_vs_backend
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:180` — "Next.js 16.3.5"
- **Source B (L0):** `frontend/web_app/package.json:34` — '"next": "16.3.4"'
- **Conflict:** One patch version behind canonical.
- **Impact:** May miss SSR/ISR fixes or build-tooling patches affecting the App Router.
- **Project completion blocker:** no
- **Recommendation:** Bump Next.js to 16.3.5.
- **User decision required:** no

---

## CONTRAD-022

- **Category:** frontend_vs_backend
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:199` — "motion (framer-motion) 13.2.0+"
- **Source B (L0):** `frontend/web_app/package.json:29` — '"framer-motion": "^12.0.0"' and `frontend/shared/package.json:26` — '"framer-motion": "^12.0.0"'
- **Conflict:** Both web and shared packages pin framer-motion 12.x while canonical requires 13.2.0+.
- **Impact:** Missing animation features, gesture improvements, and potential RSC compatibility fixes.
- **Project completion blocker:** no
- **Recommendation:** Bump framer-motion to 13.2.0+ in web_app and shared.
- **User decision required:** no

---

## CONTRAD-023

- **Category:** frontend_vs_backend
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:214` — "Zustand 5.0.14"
- **Source B (L0):** `frontend/web_app/package.json:44` — '"zustand": "^5.0.11"'
- **Conflict:** Zustand in web_app is 5.0.11 while canonical and shared both pin 5.0.14.
- **Impact:** May lack middleware or persist fixes present in 5.0.14.
- **Project completion blocker:** no
- **Recommendation:** Align web_app Zustand to 5.0.14.
- **User decision required:** no

---

## CONTRAD-024

- **Category:** frontend_vs_backend
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:217` — "Zod 4.3.6"
- **Source B (L0):** `frontend/web_app/package.json:43` — '"zod": "^3.25.76"'
- **Conflict:** Zod is on major version 3 while canonical requires Zod 4.
- **Impact:** Different validation semantics, error shapes, and type inference; forms and API payloads may fail validation unexpectedly.
- **Project completion blocker:** yes
- **Recommendation:** Upgrade web_app Zod to 4.3.6 or update TECHNOLOGY_STACK.md to Zod 3.x.
- **User decision required:** yes

---

## CONTRAD-025

- **Category:** frontend_vs_backend
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:218` — "@hookform/resolvers 5.2.2"
- **Source B (L0):** `frontend/web_app/package.json:15` — '"@hookform/resolvers": "^5.9.1"'
- **Conflict:** @hookform/resolvers is 5.9.1 while canonical pins 5.2.2.
- **Impact:** Zod 4 integration may require resolvers 5.2.x specifically; 5.9.x may have breaking changes in the resolver API.
- **Project completion blocker:** partial
- **Recommendation:** Pin @hookform/resolvers to 5.2.2 or validate 5.9.x against the Zod 4 migration.
- **User decision required:** yes

---

## CONTRAD-026

- **Category:** frontend_vs_backend
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:245` — "Expo SDK 57.0.20+"
- **Source B (L0):** `frontend/mobile_app/package.json:22` — '"expo": "~57.0.9"'
- **Conflict:** Expo SDK is 57.0.9 while canonical requires 57.0.20+.
- **Impact:** Missing OTA updates, EAS build fixes, and native module patches.
- **Project completion blocker:** partial
- **Recommendation:** Bump Expo SDK to 57.0.20+.
- **User decision required:** no

---

## CONTRAD-027

- **Category:** frontend_vs_backend
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:246` — "React Native 0.86.3"
- **Source B (L0):** `frontend/mobile_app/package.json:28` — '"react-native": "0.81.4"'
- **Conflict:** React Native is 0.81.4 while canonical requires 0.86.3.
- **Impact:** Missing New Architecture features, performance patches, and native module fixes.
- **Project completion blocker:** partial
- **Recommendation:** Bump React Native to 0.86.3 or update TECHNOLOGY_STACK.md.
- **User decision required:** yes

---

## CONTRAD-028

- **Category:** frontend_vs_backend
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:181` — "React 19.2.8"
- **Source B (L0):** `frontend/mobile_app/package.json:26` — '"react": "19.1.0"'
- **Conflict:** Mobile React is 19.1.0 while canonical requires 19.2.8.
- **Impact:** Missing RSC and concurrent feature fixes; may cause hydration mismatches with shared code.
- **Project completion blocker:** partial
- **Recommendation:** Bump mobile React to 19.2.8.
- **User decision required:** no

---

## CONTRAD-029

- **Category:** frontend_vs_backend
- **Source A (L3):** `_most_imp_docx/ARCHITECTURE_STACK.md:539` — "5 modules: admin, customer, employee, logistics, supplier"
- **Source B (L0):** `frontend/web_app/next.config.ts:51-53` — rewrites `source: '/hr/:path*'` → `destination: '/hr/:path*'`
- **Conflict:** Next.js rewrites expose a standalone `/hr` prefix, but no canonical `hr` module exists; the `hr` domain is accessed through the `employee` module (`/api/v1/employee/hr/*`).
- **Impact:** Frontend navigation to `/hr/*` will 404 or proxy to a non-existent backend route.
- **Project completion blocker:** yes
- **Recommendation:** Remove the `/hr/:path*` rewrite and replace with `/employee/hr/:path*` → `/api/v1/employee/hr/:path*`, or remove the standalone `hr` route group from the frontend.
- **User decision required:** yes

---

## CONTRAD-030

- **Category:** doc_vs_code
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:22` — "Python 3.13.x"
- **Source B (L0):** `backend/Dockerfile:1` — "FROM python:3.11-slim"
- **Conflict:** Dev Dockerfile uses Python 3.11 while canonical requires 3.13.x.
- **Impact:** Local dev environment runs a different Python minor version than prod; async behavior, dependency resolution, and type-checking may diverge.
- **Project completion blocker:** partial
- **Recommendation:** Update `backend/Dockerfile` base image to `python:3.13-slim`.
- **User decision required:** no

---

## CONTRAD-031

- **Category:** doc_vs_code
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:42` — "PostgreSQL (local) 16 | Dev — Always in local development. Run via Docker Compose (`postgres:16-alpine`)."
- **Source B (L0):** `docker-compose.yml:4` — "image: postgres:18-alpine"
- **Conflict:** Dev Docker Compose uses Postgres 18 while canonical specifies Postgres 16 for local development.
- **Impact:** Local dev DB may have schema defaults or planner behavior differences from the documented target.
- **Project completion blocker:** partial
- **Recommendation:** Change `docker-compose.yml` to `postgres:16-alpine` for the dev `db` service.
- **User decision required:** no

---

## CONTRAD-032

- **Category:** package_vs_import
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:183` — "Always. Do NOT use npm or yarn — they break workspace resolution."
- **Source B (L0):** `package.json:7` — '"dev": "npm run start:backend & npm run start:web"'
- **Source C (L0):** `package.json:8` — '"start:backend": "cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000"'
- **Conflict:** Root package.json scripts invoke `npm run` directly, bypassing the mandated pnpm workspace.
- **Impact:** Monorepo workspace resolution may break; shared package symlinks may not be created.
- **Project completion blocker:** partial
- **Recommendation:** Replace root `package.json` scripts with pnpm equivalents or remove the root orchestrator in favor of pnpm workspace scripts.
- **User decision required:** yes

---

## CONTRAD-033

- **Category:** frontend_vs_backend
- **Source A (L3):** `_most_imp_docx/ARCHITECTURE_STACK.md:186` — "frontend/web_app/src/app/ ... (customer), auth/, admin/*, supplier/*, logistics-partner/*, employee/*, wishlist/, profile/, chatbot/, tracking/; app/api/ = Next server routes"
- **Source B (L0):** `frontend/web_app/src/app:logistics-partner` (directory) and `frontend/web_app/src/app:logistics-partners` (directory)
- **Conflict:** Two sibling directories exist for the logistics-partner module group, violating the one-route-tree-per-actor rule.
- **Impact:** Duplicate route groups cause ambiguous navigation, SEO duplicate-content risk, and potential route shadowing.
- **Project completion blocker:** no
- **Recommendation:** Delete or merge the duplicate `logistics-partners` directory into `logistics-partner`.
- **User decision required:** no

---

## CONTRAD-034

- **Category:** target_vs_code
- **Source A (L3):** `_most_imp_docx/ARCHITECTURE_STACK.md:539` — "5 modules: admin, customer, employee, logistics, supplier"
- **Source B (L0):** `backend/modules/employee/routers/hr.py:1` — file exists at same level as `backend/modules/employee/routers/hr/` package directory
- **Conflict:** Both `hr.py` (file) and `hr/` (package directory) exist in `modules/employee/routers/`. Python's import system resolves `import modules.employee.routers.hr` to the package, shadowing the `.py` file.
- **Impact:** The `hr.py` file is unreachable; any code expecting the module file will import the package instead, causing attribute errors or silent misbehavior.
- **Project completion blocker:** yes
- **Recommendation:** Remove the orphaned `hr.py` file; consolidate all HR router code into the `hr/` package.
- **User decision required:** no

---

## CONTRAD-035

- **Category:** tech_target_vs_lockfile
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:44` — "SQLAlchemy 2.0.52"
- **Source B (L0):** `backend/requirements.txt:14` — "sqlalchemy==2.0.51"
- **Conflict:** One patch version below canonical.
- **Impact:** May lack ORM query-planning or async-session fixes.
- **Project completion blocker:** no
- **Recommendation:** Bump SQLAlchemy to 2.0.52.
- **User decision required:** no

---

## CONTRAD-036

- **Category:** tech_target_vs_lockfile
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:89` — "fastapi-limiter-valkey latest stable"
- **Source B (L0):** `backend/requirements.txt:1-102` — `fastapi-limiter-valkey` not listed.
- **Conflict:** Canonical rate-limiter package is imported in production (`backend/infrastructure/security/rate_limiter.py:24`) but absent from the pinned requirements.
- **Impact:** Docker builds and `pip install -r requirements.txt` will not install the rate-limiter, causing `ImportError` at startup when Valkey is available.
- **Project completion blocker:** yes
- **Recommendation:** Add `fastapi-limiter-valkey` to `requirements.txt`.
- **User decision required:** no

---

## CONTRAD-037

- **Category:** doc_vs_code
- **Source A (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:280` — "Docker Compose 2.40.0+ | Dev | Local service orchestration (PostgreSQL 16, Valkey, backend, frontend, Celery, Beat)."
- **Source B (L0):** `backend/Dockerfile:19` — "COPY requirements.txt ." and `backend/Dockerfile:30` — 'CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]'
- **Conflict:** Dev `Dockerfile` runs `uvicorn` directly (no Gunicorn) while canonical production command uses Gunicorn with Uvicorn workers; dev Dockerfile also uses Python 3.11 (see CONTRAD-030).
- **Impact:** Dev container may not mirror production process management; Gunicorn graceful-restart and pre-fork behavior is absent locally.
- **Project completion blocker:** no
- **Recommendation:** Add a Gunicorn-based dev CMD or document that the dev Dockerfile intentionally uses Uvicorn directly.
- **User decision required:** no

---

## CONTRAD-038

- **Category:** cross_dimension_count
- **Source A (L0):** `_audit/dimensions/06_database.md` DB-001 — "62 divergent migration heads (parsed from down_revision tuples)"
- **Source B (L0):** `_audit/logs/phase0_results.md` + `_audit/dimensions/07_tables_fields.md` + `_audit/dimensions/27_project_completion_blockers.md` — "5 divergent heads: `20260930_0002`, `20260930_0003`, `20260930_0006`, `20260930_0007`, `20261001_0001`"
- **Conflict:** `06_database.md` reports 62 divergent heads; Phase 0 CLI output and `07_tables_fields.jsonl` report 5 heads. Structural analysis of `backend/alembic/versions/*.py` (75 files, mixed old/new revision format) confirms exactly 5 heads. The "62" figure was a miscount from a script that parsed all files with no children in the down_revision graph rather than true divergent heads.
- **Impact:** P0 remediation plan sized for 62-head merge is incorrect; actual merge scope is 5 heads. `10_migrations.md` (dated 2026-09-30) reported 0 heads because the state was linear at that time; 4 new files were added on 2026-09-30 and `20261001_0001` on 2026-10-01 without wiring into the chain.
- **Project completion blocker:** yes
- **Recommendation:** Correct `06_database.md` DB-001 to "5 divergent heads". Merge the 5 heads into a single linear chain after fixing the `migration_helpers` import error in `env.py` that prevents `alembic heads` from executing.
- **User decision required:** no

---

## Summary

| Category | Count | Yes blockers | Partial | No |
|---|---|---|---|---|
| target_vs_code | 5 | 3 | 1 | 1 |
| tech_target_vs_lockfile | 14 | 1 | 6 | 7 |
| code_vs_config | 2 | 1 | 1 | 0 |
| frontend_vs_backend | 10 | 2 | 5 | 3 |
| package_vs_import | 3 | 2 | 1 | 0 |
| doc_vs_code | 3 | 0 | 2 | 1 |
| cross_dimension_count | 1 | 1 | 0 | 0 |
| **Total** | **38** | **10** | **16** | **12** |
