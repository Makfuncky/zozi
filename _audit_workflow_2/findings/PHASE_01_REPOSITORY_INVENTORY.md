# PHASE 01 — REPOSITORY INVENTORY
## ZOZI Marketplace E-Commerce Platform
**Audit Date:** 2026-09-11  
**Auditor:** Kilo (Forensic Technical Audit)  
**Repository Root:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi`  
**Methodology:** Source-code verification only. No assumptions from folder names, READMEs, or documentation.

---

## 1. Repository Structure

```
zozi/
├── .git/                          # Git repository data
├── .githooks/                     # Git hook scripts
├── .github/                       # CI/CD workflows
│   └── workflows/
│       ├── architecture-gate.yml
│       ├── build.yml
│       ├── ci.yml
│       ├── deploy.yml
│       ├── e2e.yml
│       ├── rollback.yml
│       ├── router-generation.yml
│       ├── schema-audit.yml
│       └── security.yml
├── .hypothesis/                   # Hypothesis testing config
├── .kilo/                         # Kilo agent config
├── .next/                         # Next.js build output (GENERATED)
├── .pytest_cache/                 # Pytest cache (GENERATED)
├── .ruff_cache/                   # Ruff linter cache (GENERATED)
├── .vscode/                       # VS Code settings
├── backend/                       # Python FastAPI backend application
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Settings class
│   ├── lifespan.py                # Startup/shutdown hooks
│   ├── Dockerfile                 # Dev container image
│   ├── Dockerfile.prod            # Production container image
│   ├── requirements.txt           # Python dependencies
│   ├── pyproject.toml             # Pytest configuration
│   ├── .env / .env.example        # Environment files
│   ├── DOMAIN_ALLOWLIST.yaml      # Cross-domain import allowlist
│   ├── start_backend.ps1          # Windows dev startup script
│   ├── run_tests.ps1 / .sh        # Test runner scripts
│   ├── modules/                   # Thin HTTP routers (per actor)
│   │   ├── admin/
│   │   ├── customer/
│   │   ├── supplier/
│   │   ├── logistics/
│   │   └── employee/
│   ├── domains/                   # Domain-driven design aggregates
│   │   ├── accounts/
│   │   ├── analytics/
│   │   ├── audit/
│   │   ├── catalog/
│   │   ├── comms/
│   │   ├── country/
│   │   ├── customers/
│   │   ├── finance/
│   │   ├── governance/
│   │   ├── hr/
│   │   ├── logistics/
│   │   ├── orders/
│   │   ├── payments/
│   │   ├── promotions/
│   │   ├── security/
│   │   └── suppliers/
│   ├── infrastructure/            # Technical cross-cutting concerns
│   │   ├── database/              # SQLAlchemy ORM, Alembic, RLS, seed
│   │   ├── events/                # Domain event subscriber
│   │   ├── http/                  # HTTP client utilities
│   │   ├── messaging/             # Email, realtime, WebSocket manager
│   │   ├── ml/                    # ML worker entry point
│   │   ├── observability/         # Logging, Prometheus, tracing, error handling
│   │   ├── redis/                 # Redis client/cache
│   │   ├── security/              # Auth, encryption, CSRF, rate limiting, vault
│   │   ├── storage/               # S3, R2, backup storage backends
│   │   ├── uploads/               # Empty directory
│   │   ├── utils/                 # Config, auth, pagination, media, etc.
│   │   └── valkey/                # Valkey client/cache
│   ├── jobs/                      # Celery task definitions
│   │   ├── celery_app.py          # Celery app + beat schedule
│   │   ├── ai_tasks.py
│   │   ├── periodic_tasks.py
│   │   ├── payout_tasks.py
│   │   ├── email_tasks.py
│   │   ├── ml_worker.py
│   │   └── ...
│   ├── middleware/                 # FastAPI middleware pipeline
│   │   ├── orchestrator.py        # Central middleware registration
│   │   ├── authentication_middleware.py
│   │   ├── rate_limit_middleware.py
│   │   ├── country_context.py
│   │   ├── security_headers.py
│   │   └── ...
│   ├── providers/                 # Third-party integration adapters
│   │   ├── ai/                    # OpenAI, HuggingFace, image AI, search
│   │   ├── analytics/
│   │   ├── auth/
│   │   ├── automation/
│   │   ├── barcode/
│   │   ├── bg_removal/
│   │   ├── comms/                 # Email, SMS, Twilio, WhatsApp
│   │   ├── finance/               # Stripe, Tap, PayPal, Thawani, PayTabs
│   │   ├── geography/
│   │   ├── image/
│   │   ├── news/
│   │   ├── ocr/
│   │   ├── qr/
│   │   ├── scanner/
│   │   ├── security/              # Vault, KMS, secrets manager
│   │   ├── shipping/
│   │   ├── storage/               # S3, R2
│   │   └── voice/                 # Empty directory
│   ├── rbac/                      # Role-based access control
│   │   ├── roles.py
│   │   ├── service.py
│   │   ├── catalog.py
│   │   ├── resolution.py
│   │   └── dependencies.py
│   ├── kernel/                    # Shared kernel (DDD)
│   │   ├── country.py
│   │   ├── currency.py
│   │   ├── money.py
│   │   ├── mixins.py
│   │   └── ...
│   ├── scripts/                   # Backend maintenance/debug scripts
│   ├── tests/                     # Backend test suite
│   │   ├── architecture/          # Architecture law compliance tests
│   │   ├── domains/               # Per-domain unit/integration tests
│   │   ├── playwright/            # Backend e2e (Playwright)
│   │   ├── admin/, integration/, kernel/, middleware/, modules/, observability/, providers/, rbac/, security/, system/, workflows/
│   │   ├── conftest.py
│   │   └── test_*.py               # ~40+ test files
│   ├── alembic/                   # Database migrations
│   │   ├── alembic.ini
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   ├── migration_helpers.py
│   │   └── versions/              # 60+ migration files (2026-07-26 to 2026-09-04)
│   └── var/
│       ├── artifacts/             # Contains schema_mapping.json
│       ├── static/                # Empty directory
│       └── uvicorn.err / .out     # Uvicorn log files
├── frontend/                      # Frontend applications
│   ├── package.json               # Root devDependencies (testing-library)
│   ├── .env.local
│   ├── .npmrc
│   ├── README.md
│   ├── web_app/                   # Next.js web application
│   │   ├── package.json           # Next 16.3.4, React 19.2.8
│   │   ├── next.config.ts         # Next.js config (rewrites, redirects)
│   │   ├── middleware.ts          # Next.js middleware (auth guards)
│   │   ├── tsconfig.json
│   │   ├── tailwind.config.js
│   │   ├── postcss.config.mjs
│   │   ├── Dockerfile
│   │   ├── .env.example / .env.local
│   │   ├── src/
│   │   │   ├── app/               # Next.js App Router pages
│   │   │   │   ├── page.tsx       # Root page (redirects to /products)
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── providers.tsx
│   │   │   │   ├── admin/
│   │   │   │   ├── api/
│   │   │   │   ├── auth/
│   │   │   │   ├── cart/
│   │   │   │   ├── checkout/
│   │   │   │   ├── customer/
│   │   │   │   ├── employee/
│   │   │   │   ├── login/
│   │   │   │   ├── logistics-partner/
│   │   │   │   ├── orders/
│   │   │   │   ├── products/
│   │   │   │   ├── profile/
│   │   │   │   ├── register/
│   │   │   │   ├── reset-password/
│   │   │   │   ├── returns/
│   │   │   │   ├── supplier/
│   │   │   │   ├── suppliers/
│   │   │   │   ├── tracking/
│   │   │   │   ├── verify-email/
│   │   │   │   ├── wishlist/
│   │   │   │   └── ... (30+ route dirs)
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── lib/
│   │   │   ├── services/
│   │   │   ├── shared/
│   │   │   ├── styles/
│   │   │   ├── theme/
│   │   │   ├── types/
│   │   │   └── utils/
│   │   ├── public/                # Static assets (SVG icons)
│   │   ├── e2e/                   # Playwright e2e specs
│   │   ├── __tests__/             # Jest unit tests
│   │   ├── openapi.json           # Frontend-captured OpenAPI spec
│   │   ├── jest.config.js
│   │   ├── playwright.config.ts
│   │   └── ...
│   ├── mobile_app/                # Expo React Native application
│   │   ├── package.json           # Expo ~57.0.9, React Native 0.81.4
│   │   ├── app.json               # Expo config (bundle IDs, plugins)
│   │   ├── app.config.js
│   │   ├── tsconfig.json
│   │   ├── babel.config.js
│   │   ├── metro.config.js
│   │   ├── sentry.config.ts
│   │   ├── app/                   # Expo Router screens
│   │   ├── components/
│   │   ├── lib/
│   │   ├── theme/
│   │   ├── e2e/                   # Playwright mobile e2e
│   │   ├── web-dist/              # Built web output
│   │   └── assets/                # Icons, splash images
│   └── shared/                    # @zozi/shared TypeScript package
│       ├── package.json
│       ├── tsconfig.json
│       ├── tsconfig.build.json
│       └── src/
├── browser-tests/                 # Standalone Playwright scaling audit
│   └── scaling_audit.spec.ts
├── documents/                     # Project documentation (many .md/.txt files)
│   ├── ARCHITECTURE_DIAGRAM.md
│   ├── SECURITY_*.md
│   ├── TECHNOLOGY_USED.md
│   ├── PROJECT-ROADMAP.md
│   ├── WORKFLOW_STATUS_SUMMARY.md
│   └── ... (50+ documentation files)
├── logs/                          # Log artifacts
├── memory/                        # Kilo memory / notes
├── monitoring/                    # Observability stack
│   ├── docker-compose.monitoring.yml
│   ├── prometheus.yml / prometheus/
│   ├── alertmanager.yml
│   ├── alerts.yml
│   ├── grafana/
│   │   └── provisioning/dashboards/zozi-system-health.json
│   ├── tempo/tempo.yaml
│   ├── promtail/promtail-config.yml
│   ├── fraud_monitoring.py
│   ├── ghost_order_detector.py
│   └── threat_feed_updater.py
├── nginx/                         # Nginx reverse proxy config
│   └── nginx.conf
├── node_modules/                  # Root-level JS dependencies (tracked/large)
├── scripts/                       # Utility, audit, and maintenance scripts
│   ├── audit/
│   │   └── full_system_audit.py
│   ├── frontend/
│   │   ├── fix-theme-module-styles.js
│   │   ├── replace-hardcoded-mobile-sizes.js
│   │   └── ...
│   ├── maintenance/
│   │   ├── cleanup-bak.sh
│   │   ├── fix_createStyles.py
│   │   └── ...
│   ├── system_trackers/
│   │   ├── feature_definitions.yaml
│   │   ├── architecture_flow.yaml
│   │   └── ...
│   ├── testing/
│   │   ├── loadtests/
│   │   ├── ai_image_group_smoke.py
│   │   └── full_stack_health_check.py
│   ├── tools/
│   │   ├── generate_codebase.py
│   │   ├── generate_data_dictionary.py
│   │   ├── check_db.py
│   │   ├── check_hash.py
│   │   └── ...
│   ├── agent_v07_audit.py
│   ├── design_audit.py
│   ├── run_all_tests.py
│   ├── start_backend.ps1
│   ├── start_frontend.ps1
│   └── ...
├── _audit/                        # Audit workspace
├── _audit_workflow_2/             # Current audit workspace
│   └── findings/                  # Audit output directory
├── _design_investigation/         # Design investigation workspace
├── _most_imp_docx/                # Document generation workspace
│   └── _audit/
├── .env                           # Root env (gitignored)
├── .env.example
├── .env.wrangler
├── .gitignore
├── .gitleaks.toml                  # Secret scanning config
├── .neon                           # Neon PostgreSQL config
├── .semgrep.yml                    # SAST config
├── ARCHITECTURE_DIAGRAM.md         # Architecture specification
├── Caddyfile                       # Caddy reverse proxy config
├── CODEBASE_AUDIT_BY_ASHER.md      # Prior audit document
├── Makefile                        # Dev/build/test shortcuts
├── neon.ts                         # Neon TypeScript config
├── package.json / package-lock.json # Root JS workspace config
├── railway.toml                    # Railway deployment config
├── run_e2e.ps1                     # E2E runner (PowerShell)
├── run_test.bat                    # Test runner (Windows)
├── run_zozi.bat / .sh              # Dev startup scripts
├── SECURITY.md                     # Security policy
├── test_phase7e2.db*               # SQLite test database files
├── update_diagram.py               # Diagram update script
├── vercel.json                     # Vercel deployment config
├── WIRING_STATUS.json              # Wiring status tracker
├── dump.rdb                        # Redis dump file (root)
├── investor_pitch_deck.html        # Pitch deck artifact
└── _temp_delete_kilo.py            # Temp Kilo script
```

---

## 2. Application Components

| Component | Location | Evidence | Confidence |
|-----------|----------|----------|------------|
| **Backend API** | `backend/` | `main.py` creates `FastAPI(...)` app; `requirements.txt` lists `fastapi==0.115.2`, `uvicorn==0.51.0`; `docker-compose.yml` service `backend` runs `uvicorn main:app` | **VERIFIED** |
| **Frontend Web (Next.js)** | `frontend/web_app/` | `package.json` lists `next: 16.3.4`, `react: 19.2.8`; `next.config.ts` exists; `src/app/page.tsx` is root page; `vercel.json` configures Next.js deployment | **VERIFIED** |
| **Frontend Mobile (Expo)** | `frontend/mobile_app/` | `package.json` lists `expo: ~57.0.9`, `react-native: 0.81.4`; `app.json` defines Expo config with bundle ID `com.zozi.marketplace` | **VERIFIED** |
| **Shared UI Package** | `frontend/shared/` | `package.json` name `@zozi/shared`; peer dependencies on `react`, `react-native`, `react-native-web`; imported by `frontend/web_app/package.json` as `@zozi/shared` | **VERIFIED** |
| **Celery Workers (ML)** | `backend/` + `docker-compose.yml` | `jobs/celery_app.py` defines Celery app; `docker-compose.yml` service `celery-worker-ml` runs `celery -A celery_app worker -Q ml` | **VERIFIED** |
| **Celery Workers (Periodic)** | `backend/` + `docker-compose.yml` | `docker-compose.yml` service `celery-worker-periodic`; `celery_app.py` beat schedule defines periodic tasks | **VERIFIED** |
| **Celery Workers (Payouts)** | `backend/` + `docker-compose.yml` | `docker-compose.yml` service `celery-worker-payouts`; `jobs/payout_tasks.py` exists | **VERIFIED** |
| **Celery Workers (Emails)** | `backend/` + `docker-compose.yml` | `docker-compose.yml` service `celery-worker-emails`; `jobs/email_tasks.py` exists | **VERIFIED** |
| **Celery Beat Scheduler** | `backend/` + `docker-compose.yml` | `docker-compose.yml` service `celery-beat`; `celery_app.py` beat_schedule dict defines 7 scheduled tasks | **VERIFIED** |
| **ML Worker (standalone)** | `backend/` + `docker-compose.prod.yml` | `docker-compose.prod.yml` service `ml_worker` runs `python -m utils.ml_worker`; `backend/infrastructure/ml/worker.py` exists | **VERIFIED (command path mismatch noted in Suspicious Areas)** |
| **Reverse Proxy (Nginx)** | `nginx/` | `nginx.conf` defines upstream `backend:8000`, `frontend:3000`, location blocks for `/api/`, `/ws/`, `/_next/static/`, `/uploads/` | **VERIFIED** |
| **Reverse Proxy (Caddy)** | Root | `Caddyfile` defines `api.yourdomain.com` and `yourdomain.com` reverse proxies | **VERIFIED** |
| **Monitoring Stack** | `monitoring/` | `docker-compose.monitoring.yml`, `prometheus.yml`, `alertmanager.yml`, `grafana/provisioning/`, `tempo/tempo.yaml`, `promtail/` configs | **VERIFIED** |
| **Browser Tests** | `browser-tests/` | `scaling_audit.spec.ts` exists | **VERIFIED** |

---

## 3. Entry Points

| Entry Point | File | Function/Class | Purpose | Evidence |
|-------------|------|----------------|---------|----------|
| **Backend API (dev)** | `backend/main.py` | `app = FastAPI(...)` | Main FastAPI application instance | Line 72: `app = FastAPI(...)`; Line 299: `uvicorn.run("main:app", ...)` |
| **Backend API (prod)** | `backend/Dockerfile.prod` | CMD | Gunicorn + Uvicorn workers serving `main:app` | Line 26: `CMD ["gunicorn", "main:app", ...]` |
| **Backend startup/lifespan** | `backend/lifespan.py` | `build_lifespan()` | Modular startup/shutdown hooks (tables, migrations, seed, RLS, services) | Line 315: `def build_lifespan():` |
| **Health checks** | `backend/main.py` | `health_check()`, `health_deps()`, `health_ready()` | Runtime and dependency health endpoints | Lines 104-181: `@app.get("/health")`, `/health/deps`, `/health/ready` |
| **WebSocket (user)** | `backend/main.py` | `websocket_user` (imported), `app.add_api_websocket_route("/ws/user", ...)` | Customer/supplier real-time socket | Line 194-196 |
| **WebSocket (admin jobs)** | `backend/main.py` | `websocket_background_jobs()` | Admin background jobs real-time updates | Lines 204-240 |
| **Router loader** | `backend/main.py` | `_load_routers()` | Discovers and mounts routers from `modules/{customer,supplier,logistics,admin,employee}/routers/` | Lines 243-278 |
| **Celery app** | `backend/jobs/celery_app.py` | `celery_app = Celery("zozi", ...)` | Distributed task processing (ML, periodic, payouts, emails) | Line 11-21 |
| **ML Worker** | `backend/infrastructure/ml/worker.py` | (worker entry) | Background ML/AI image processing | File exists; referenced in `docker-compose.prod.yml` line 71 |
| **Next.js web app** | `frontend/web_app/src/app/page.tsx` | (default export) | Root web page | File exists; `next.config.ts` rewrites `/` to `/products` |
| **Next.js middleware** | `frontend/web_app/middleware.ts` | `middleware(request)` | Auth guards for `/admin`, `/supplier`, `/logistics-partner` | Lines 34-78 |
| **Expo mobile app** | `frontend/mobile_app/AppEntry.js` | (Expo entry) | React Native application entry | `package.json` main: `node_modules/expo/AppEntry.js` |
| **Frontend dev server** | `frontend/web_app/package.json` | `npm run dev` → `next dev` | Next.js development server | Scripts section |
| **Backend dev server** | Root `package.json` | `npm run start:backend` → `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000` | Uvicorn dev server | Line 8 |
| **Database migrations** | `backend/alembic/` | `alembic upgrade head` | Schema versioning and migration | `Makefile` line 19: `db:migrate`; CI workflows run `alembic upgrade head` |
| **Database seeding** | `backend/infrastructure/database/seed/` | `seed_data()` | Demo/catalog data seeding | `lifespan.py` line 218 calls `seed_data(SessionLocal)`; `main.py` line 21: `python -m infrastructure.database.init_db --seed` |
| **Audit script** | `scripts/audit/full_system_audit.py` | (entry point) | Full system audit runner | File exists |

---

## 4. Configuration

| Configuration | File | Technology/Purpose | Evidence |
|---------------|------|-------------------|----------|
| **Root env vars** | `.env`, `.env.example`, `.env.wrangler` | Root-level environment (gitignored) | `.gitignore` line 15: `.env`; files exist |
| **Backend settings** | `backend/config.py` | `Settings` class with 100+ settings (DB, auth, payments, storage, AI, etc.) | Lines 23-509: class `Settings` with `_DEFAULTS` dict |
| **Backend env** | `backend/.env`, `backend/.env.example` | Backend-specific env vars | Files exist |
| **Frontend env** | `frontend/web_app/.env.local`, `frontend/web_app/.env.example` | Next.js public/private env vars | Files exist |
| **Frontend root env** | `frontend/.env.local` | Root frontend env | File exists |
| **Docker Compose (dev)** | `docker-compose.yml` | Dev stack: Postgres 18, Valkey 9.0, backend, 4 Celery workers, Celery Beat, frontend | Lines 1-173: service definitions |
| **Docker Compose (prod)** | `docker-compose.prod.yml` | Prod stack: PgBouncer, backend (3 replicas), ML worker, Redis 7 | Lines 1-112: service definitions |
| **Docker Compose (override)** | `docker-compose.override.yml` | Dev overrides: PgBouncer, DB pool tuning | Lines 1-25 |
| **Monitoring Compose** | `monitoring/docker-compose.monitoring.yml` | Prometheus, Grafana, Tempo, Alertmanager, Promtail stack | File exists |
| **Vercel config** | `vercel.json` | Next.js deployment: build command, headers, security headers, env mapping | Lines 1-55 |
| **Railway config** | `railway.toml` | Railway backend deployment: Dockerfile, start command, healthcheck | Lines 1-13 |
| **Caddy reverse proxy** | `Caddyfile` | HTTPS reverse proxy for API and frontend, WebSocket support, security headers | Lines 1-66 |
| **Nginx reverse proxy** | `nginx/nginx.conf` | Reverse proxy: API, WebSocket, static, uploads, CDN | Lines 1-135 |
| **Makefile** | `Makefile` | Dev shortcuts: setup, dev, docker, test, lint, router generation | Lines 1-45 |
| **Pytest config** | `backend/pyproject.toml` | Test paths, warnings, markers | Lines 1-13 |
| **Semgrep** | `.semgrep.yml` | Static analysis rules | File exists |
| **Gitleaks** | `.gitleaks.toml` | Secret scanning configuration | File exists |
| **Neon config** | `.neon`, `neon.ts` | Neon PostgreSQL integration config | Files exist |
| **Domain allowlist** | `backend/DOMAIN_ALLOWLIST.yaml` | Cross-domain import debt tracker | Lines 1-53 |
| **Frontend Next.js config** | `frontend/web_app/next.config.ts` | Rewrites to backend API, redirects, image remote patterns | Lines 1-75 |
| **Frontend middleware** | `frontend/web_app/middleware.ts` | Route protection: `/admin`, `/supplier`, `/logistics-partner` | Lines 1-82 |
| **Frontend TS config** | `frontend/web_app/tsconfig.json` | TypeScript compiler options, path aliases (`@/*`, `@shared/*`) | Lines 1-48 |
| **Mobile app config** | `frontend/mobile_app/app.json` | Expo config: name, slug, bundle ID, plugins, scheme | Lines 1-45 |
| **Mobile TS config** | `frontend/mobile_app/tsconfig.json` | TypeScript config | File exists |
| **Prometheus alerts** | `monitoring/alerts.yml` | Alerting rules | File exists |
| **Alertmanager** | `monitoring/alertmanager.yml` | Alert routing/config | File exists |
| **Grafana dashboard** | `monitoring/grafana/provisioning/dashboards/zozi-system-health.json` | System health dashboard JSON | File exists |
| **Tempo config** | `monitoring/tempo/tempo.yaml` | Distributed tracing backend config | File exists |
| **Promtail config** | `monitoring/promtail/promtail-config.yml` | Log collection agent config | File exists |
| **Frontend Jest config** | `frontend/web_app/jest.config.js` | Jest test runner config | File exists |
| **Frontend Playwright config** | `frontend/web_app/playwright.config.ts` | E2E test runner config | File exists |
| **Mobile Playwright config** | `frontend/mobile_app/playwright.config.ts` | Mobile e2e config | File exists |
| **Shared package config** | `frontend/shared/tsconfig.json`, `tsconfig.build.json` | Shared TS package build config | Files exist |

---

## 5. Build/Deployment

| File | Technology | Purpose | Evidence |
|------|-----------|---------|----------|
| **Backend Dockerfile** | Docker (python:3.11-slim) | Dev image: install deps, copy code, run uvicorn | Lines 1-30: `FROM python:3.11-slim`, `CMD ["uvicorn", ...]` |
| **Backend Dockerfile.prod** | Docker (python:3.11-slim) | Prod image: install deps, run gunicorn + uvicorn workers | Lines 1-26: `CMD ["gunicorn", "main:app", ...]` |
| **Frontend Dockerfile** | Docker (node base implied) | Frontend container image | `docker-compose.yml` line 161: `dockerfile: web_app/Dockerfile`; file exists |
| **Root package.json** | npm | Workspace scripts: dev, test, build, lint, db migrate | Lines 6-22 |
| **Makefile** | Make | Docker up/down, backend/frontend setup, test, lint, router generation | Lines 1-45 |
| **GitHub Actions (build)** | GitHub Actions | Build & push Docker images to `ghcr.io` | `.github/workflows/build.yml` lines 1-134 |
| **GitHub Actions (deploy)** | GitHub Actions | Deploy backend to Railway, frontend to Vercel, smoke tests | `.github/workflows/deploy.yml` lines 1-304 |
| **GitHub Actions (CI)** | GitHub Actions | Lint (ruff), architecture gates, unit tests, schema drift | `.github/workflows/ci.yml` lines 1-85 |
| **GitHub Actions (E2E)** | GitHub Actions | Playwright e2e (local stack + staging), mobile e2e | `.github/workflows/e2e.yml` lines 1-246 |
| **GitHub Actions (security)** | GitHub Actions | Security scanning | `.github/workflows/security.yml` |
| **GitHub Actions (schema-audit)** | GitHub Actions | Schema drift/audit checks | `.github/workflows/schema-audit.yml` |
| **GitHub Actions (rollback)** | GitHub Actions | Deployment rollback | `.github/workflows/rollback.yml` |
| **GitHub Actions (router-generation)** | GitHub Actions | Auto-router generation/verification | `.github/workflows/router-generation.yml` |
| **GitHub Actions (architecture-gate)** | GitHub Actions | Architecture law enforcement | `.github/workflows/architecture-gate.yml` |
| **Vercel deployment** | Vercel | Frontend production/preview deployments | `vercel.json`; `deploy.yml` uses `vercel deploy` |
| **Railway deployment** | Railway | Backend production/staging deployments | `railway.toml`; `deploy.yml` uses `railway up` |
| **Alembic migrations** | Alembic | Database schema versioning | `backend/alembic/versions/` contains 60+ migrations |
| **CI migration step** | GitHub Actions + Alembic | `alembic upgrade head` runs in deploy workflows | `deploy.yml` lines 116, 199; `e2e.yml` line 99 |
| **CI lint step** | ruff | Backend linting in CI | `ci.yml` lines 22-25 |
| **Frontend build** | Next.js | `next build` for production | `package.json` script `build:web`; `vercel.json` buildCommand |

---

## 6. Unknown Areas

| Area | Description | Reason |
|------|-------------|--------|
| **Voice provider implementation** | `backend/providers/voice/` directory exists but is empty | Cannot determine if placeholder or deprecated |
| **Uploads infrastructure** | `backend/infrastructure/uploads/` directory exists but is empty | Cannot determine intended purpose |
| **OpenSearch integration** | Session memory references OpenSearch as finalized search tech, but `requirements.txt` contains no OpenSearch client and `grep` found no code references | Cannot verify if implemented or only planned |
| **Pybreaker circuit breaker** | Session memory references `pybreaker` as finalized, but `requirements.txt` contains no pybreaker and `grep` found no code references | Cannot verify if implemented or only planned |
| **Route group `(authenticated)`** | Next.js App Router commonly uses route groups, but no parenthesized directories exist under `frontend/web_app/src/app/` | Cannot determine if route groups are used elsewhere or not used |
| **Scripts utilization** | `scripts/` contains 30+ Python/JS scripts; unclear which are actively maintained vs legacy one-offs | No metadata or documentation definitively classifies them |
| **.env runtime values** | `.env`, `backend/.env`, `frontend/.env.local` exist but were not read (to avoid exposing secrets) | Exact runtime configuration values are not determinable |
| **Provider completeness** | `backend/providers/` contains 18 subdirectories; some (e.g., `voice/`) are empty, but others' completeness is not fully verified | Partial verification only |
| **Mobile app screens** | `frontend/mobile_app/app/` exists but screen inventory was not enumerated | Partial verification |
| **Frontend API routes completeness** | `frontend/web_app/src/app/api/` contains `auth/`, `currency/`, `frontend-errors/`, `geo/`, `z-rmbg/` but full route coverage was not enumerated | Partial verification |
| **Backend services registry** | `lifespan.py` attempts to import `services._registry`, `services.registry`, `services.unknown._registry` but none were found in the listed directories | Cannot determine if registry exists elsewhere or is absent |
| **`utils.ml_worker` module path** | `docker-compose.prod.yml` references `python -m utils.ml_worker` but no top-level `utils` module exists under `backend/` | Actual import path is not determinable from container command alone |

---

## 7. Suspicious Areas (Structural Anomalies Only)

| Area | Anomaly | Evidence | Impact |
|------|---------|----------|--------|
| **Redis vs Valkey naming inconsistency** | `docker-compose.prod.yml` uses `REDIS_URL` and deploys `redis:7-alpine`; `docker-compose.yml` uses `VALKEY_URL` and `valkey:9.0-alpine`; `backend/config.py` defaults to `redis://localhost:6379`; both `backend/infrastructure/redis/` and `backend/infrastructure/valkey/` directories exist | `docker-compose.prod.yml` lines 29, 96-104; `docker-compose.yml` lines 20-25, 34, 39-40; `backend/config.py` lines 74, 90-91; directory listings | High — contradicts stated Valkey-only migration; risk of mixed Redis/Valkey dependencies in production |
| **ML worker command path mismatch** | `docker-compose.prod.yml` line 71: `python -m utils.ml_worker` does not match any top-level `utils` package under `backend/` | `docker-compose.prod.yml` line 71; `backend/` directory listing shows no `utils/` directory | Medium — container will fail to start if command is literal |
| **Loose test artifacts in web_app root** | `frontend/web_app/` root contains `test_logistics.txt`, `staff_test.txt`, `staff_test2.txt`, `output.txt`, `build_output.txt`, `bulk_test_output.txt`, `logistics_test.txt`, `playwright-results.txt`, etc. | `frontend/web_app/` directory listing | Low — pollutes repo root; suggests ad-hoc testing outside proper test directories |
| **Database files at repo root** | `test_phase7e2.db`, `test_phase7e2.db-shm`, `test_phase7e2.db-wal`, `dump.rdb` exist at repository root | Root directory listing | Low — local database artifacts should not be committed; `dump.rdb` suggests Redis dump file |
| **Multiple overlapping reverse proxy configs** | `Caddyfile`, `nginx/nginx.conf`, `vercel.json` all define reverse proxy/security headers without clear environment-specific activation | Files exist at root | Medium — operational risk if multiple proxies are activated simultaneously |
| **Empty provider directories** | `backend/providers/voice/` and `backend/infrastructure/uploads/` are empty | Directory listings | Low — may be placeholders or incomplete implementations |
| **Beta dependency versions** | `opentelemetry-instrumentation==0.65b0` is a beta prerelease version | `backend/requirements.txt` line 66 | Low — potential instability in observability stack |
| **Session digest vs code mismatch** | Prior session digest states technology decisions are finalized for OpenSearch, HashiCorp Vault, pybreaker; codebase does not contain these dependencies or clear implementations | Session memory record vs `requirements.txt` grep | High — audit trail and actual codebase are misaligned; indicates either incomplete implementation or outdated session summary |

---

## 8. Additional Verified Findings

### 8.1 ORM / Database Architecture
- **Status:** VERIFIED
- **Evidence:** `backend/requirements.txt` lines 14-17 (`sqlalchemy==2.0.51`, `alembic==1.18.5`, `asyncpg==0.31.0`, `psycopg2-binary==2.9.12`); `backend/infrastructure/database/base.py` (Base declarative); `backend/infrastructure/database/database.py` (engine/session); `backend/alembic/versions/` contains 60+ migration files
- **Schema strategy:** Multi-schema PostgreSQL (`accounts`, `catalog`, `country`, etc.) verified via `__table_args__ = ({"schema": "catalog"},)` in `backend/domains/catalog/models/products.py` line 15
- **RLS:** Row Level Security implemented via `backend/infrastructure/database/rls_interceptor.py` and `install_rls_policies()` called in `backend/main.py` lines 28, 49-53
- **Migrations:** Alembic with custom `migration_helpers.py`, `env.py`; CI runs `alembic check` for drift detection

### 8.2 API Layer Architecture
- **Status:** VERIFIED
- **Evidence:** `backend/modules/*/routers/*.py` files; `backend/main.py` lines 243-278 `_load_routers()` dynamically imports routers from `modules.{customer,supplier,logistics,admin,employee}.routers`
- **Verified prefixes:**
  - `/api/v1/admin/*` — `backend/modules/admin/routers/*.py` (e.g., `catalog.py` line 39: `APIRouter(prefix="/api/v1/admin/catalog", ...)`)
  - `/api/v1/customer/*` — `backend/modules/customer/routers/*.py` (e.g., `catalog.py` line 23)
  - `/api/v1/supplier/*` — `backend/modules/supplier/routers/*.py` (e.g., `catalog.py` line 21)
  - `/api/v1/logistics/*` — `backend/modules/logistics/routers/*.py`
  - `/api/v1/employee/*` — `backend/modules/employee/routers/*.py` (has extra `hr/` subdir)
  - `/api/v1/auth/*` — `backend/modules/*/routers/auth.py` in each module
- **Next.js rewrites** proxy `/api/*`, `/admin/*`, `/hr/*`, `/__api/*` to backend (`frontend/web_app/next.config.ts` lines 32-71)

### 8.3 Authentication & Authorization
- **Status:** VERIFIED
- **Evidence:** `backend/requirements.txt` lines 22-28 (`python-jose`, `pyjwt`, `bcrypt`, `pyotp`, `passlib`); `backend/infrastructure/security/auth.py`, `dependencies.py`; `backend/middleware/authentication_middleware.py`; `backend/rbac/` directory
- **JWT:** Access tokens (15 min), refresh tokens (7 days), cookie-based refresh
- **MFA:** `pyotp` listed; `backend/domains/accounts/models/mfa_factor.py`, `otp.py` exist
- **Social auth:** Google and Facebook OAuth configured in `backend/config.py` lines 78-81
- **Device binding:** `middleware/device_binding_middleware.py`, `zero_trust_auth.py`
- **RBAC:** `backend/rbac/roles.py`, `service.py`, `catalog.py`, `resolution.py`

### 8.4 Payment Providers
- **Status:** VERIFIED
- **Evidence:** `backend/providers/finance/` contains `stripe.py`, `stripe_sdk.py`, `tap.py`, `paypal.py`, `paytabs.py`, `thawani.py`, `webhooks.py`, `registry.py`
- **Config:** Stripe, Tap keys in `backend/config.py` lines 49-55, 72-73

### 8.5 Communication Providers
- **Status:** VERIFIED
- **Evidence:** `backend/providers/comms/` contains `email.py`, `sms.py`, `twilio.py`, `whatsapp.py`, `whatsapp_selfhosted.py`
- **Config:** SMTP, Twilio, Resend keys in `backend/config.py` lines 57-61, 72-76

### 8.6 Storage Providers
- **Status:** VERIFIED
- **Evidence:** `backend/providers/storage/` contains `s3_client.py`, `r2_client.py`, `storage_backend.py`, `base.py`, `config.py`, `connect.py`, `generic.py`; `backend/infrastructure/storage/storage.py`, `backup.py`
- **Config:** S3/R2 bucket, region, endpoint, CDN, access keys in `backend/config.py` lines 113-122

### 8.7 Observability
- **Status:** VERIFIED
- **Evidence:** `backend/requirements.txt` lines 59-70 (`structlog`, `sentry-sdk`, `prometheus-client`, `prometheus-fastapi-instrumentator`, `opentelemetry-*`); `backend/infrastructure/observability/` contains `logging_config.py`, `prometheus_setup.py`, `error_handler.py`; `backend/main.py` lines 35, 85-86, 96-101 initialize structlog, Prometheus, OpenTelemetry

### 8.8 Testing Infrastructure
- **Status:** VERIFIED
- **Evidence:**
  - Backend unit/integration: `backend/tests/` contains ~40+ `test_*.py` files plus `conftest.py`
  - Architecture tests: `backend/tests/architecture/` contains 36 test files enforcing architecture laws
  - Playwright e2e (web): `frontend/web_app/e2e/` and `backend/tests/playwright/`
  - Playwright e2e (mobile): `frontend/mobile_app/e2e/`
  - Jest unit tests: `frontend/web_app/__tests__/`
  - CI runs all test suites: `ci.yml`, `e2e.yml`

### 8.9 CI/CD Pipelines
- **Status:** VERIFIED
- **Evidence:** `.github/workflows/` contains 9 workflow files:
  - `ci.yml`: lint + architecture gates + unit tests + schema drift
  - `build.yml`: Docker build & push to GHCR
  - `deploy.yml`: Railway (backend) + Vercel (frontend) with pre-deploy validation and smoke tests
  - `e2e.yml`: Playwright against local stack and staging
  - `security.yml`: Security scanning
  - `schema-audit.yml`: Schema drift checks
  - `rollback.yml`: Deployment rollback
  - `router-generation.yml`: Auto-router CI gate
  - `architecture-gate.yml`: Architecture law enforcement

### 8.10 Static Assets & Upload Handling
- **Status:** VERIFIED
- **Evidence:**
  - Frontend static: `frontend/web_app/public/` contains SVG icons (`file.svg`, `globe.svg`, `next.svg`, `placeholder.svg`, `vercel.svg`, `window.svg`)
  - Backend local uploads: `backend/main.py` lines 90-93 mounts `/uploads` from `backend/uploads/` directory (dev only)
  - Production uploads: S3/R2 via `backend/providers/storage/` and `backend/infrastructure/storage/storage.py`; `backend/config.py` lines 113-122 configure S3/R2
  - Nginx serves `/uploads/` and `/media/` in dev (`nginx/nginx.conf` lines 121-133)

---

## 9. Confidence Summary

| Category | Confidence |
|----------|------------|
| Backend framework, entry points, and runtime | **High** |
| Frontend web framework, routing, and build | **High** |
| Mobile app framework and config | **High** |
| Database ORM, migrations, and multi-schema strategy | **High** |
| CI/CD pipelines and deployment targets | **High** |
| Background job architecture (Celery) | **High** |
| Third-party provider adapters (payments, comms, storage, AI) | **High** |
| Middleware pipeline composition | **High** |
| Authentication/authorization mechanisms | **High** |
| Observability stack (logging, metrics, tracing, error tracking) | **High** |
| OpenSearch and pybreaker implementation status | **Low** — planned per session memory but absent from code |
| Provider directory completeness (e.g., `voice/`) | **Low** — empty directories present |
| Scripts maintenance status | **Medium** — many files exist but utilization is unclear |
| Exact `.env` runtime values | **Unknown** — intentionally not inspected |

---

*End of Phase 01 Repository Inventory. No modifications were made to the repository during this audit.*
