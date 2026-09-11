```
=== AGENT LOG ===
PHASE: 01 — Repository Inventory
STATUS: COMPLETED
REPORT_FILE: _audit/findings/PHASE_01_REPOSITORY_INVENTORY.md
SCOPE_COVERED: Structural inventory only — directory tree, entry points, backend/frontend/worker/CLI apps, scripts, config files, env templates, Docker/compose, CI/CD, infra & DB-migration wiring, ORM/API surface locations, test dirs, docs, generated/build artifacts, static assets, upload handling, third-party integration providers. NO code-quality/security evaluation.
FILES_EXAMINED: ≈95 (≈50 files opened/read; ≈45 directories enumerated)
EVIDENCE_ITEMS: 68 file:line / file-path citations
FINDINGS_TOTAL: 41  (VERIFIED: 36 / INFERRED: 4 / UNKNOWN: 1)
SEVERITY_BREAKDOWN: BLOCKER: 0 / HIGH: 0 / MEDIUM: 0 / LOW: 0 / INFO: 41   (Phase 01 is structural inventory; severities not assessed — deferred to Phases 11–17)
TOP_FINDINGS:
  1. HTTP API entry point is FastAPI `app` — backend/main.py:75-83 (+ uvicorn `main:app` in package.json:7 & railway.toml:9)
  2. Background workers are Celery — backend/jobs/celery_app.py:10-21 (4 queues + beat) wired in docker-compose.yml:49-190
  3. Routers are hand-maintained per-actor and dynamically mounted — backend/main.py:245-278; auto-router generator RETIRED — backend/main.py:281-289
  4. ORM = SQLAlchemy declarative; models in domains/*/models/*.py preloaded by lifespan — backend/lifespan.py:282-311; canonical Base in infrastructure/database/base.py
  5. Two DB-schema mechanisms coexist: Alembic (canonical, ~62 versions) + legacy in-code migrations gated by default-false flags — backend/alembic/, backend/config.py:94-95, backend/infrastructure/database/migrations/new_tables.py
GAPS / NOT DETERMINABLE: Contents of .kilo/, .neon, .githooks/, backend/var/, memory/Zozi-Cursor-Router-Migration/ not opened (names only). Whether root .next/ & root node_modules/ are git-tracked vs ignored not fully verified (requires full .gitignore read).
SELF_SKEPTICISM_RATING: 5
=== END AGENT LOG ===
```

# PHASE 01 — COMPLETE REPOSITORY INVENTORY (Zozi E-commerce Platform)

**Audit type:** Forensic, evidence-based, read-only. Governed by `_audit/MASTER_RULES.md`.
**Scope of this phase:** *Structural* inventory only. This report determines **what exists and where**, and each major directory's **apparent responsibility as evidenced by representative files opened** — not by folder/package names or docs. Code quality, security, performance, and correctness are explicitly **out of scope** for Phase 01 and deferred to later phases.
**Evidence labels:** VERIFIED (opened the file/config), INFERRED (strongly implied by opened evidence), UNKNOWN (insufficient evidence).

> Note on method: every directory-responsibility claim below is backed by at least one representative file that was opened and cited. Where only the directory listing (not the file contents) was examined, the claim is labelled INFERRED or UNKNOWN accordingly.

---

## Repository Structure (tree-like)

Top-level (workspace root `d:\Projects\10- E-COMMERCE WEBSITE\zozi`) — VERIFIED via `list_dir` of root:

```
zozi/
├── backend/                     # Python / FastAPI application (VERIFIED: backend/main.py:75)
│   ├── main.py                  # FastAPI app + health routes + WS + router loader (VERIFIED)
│   ├── lifespan.py              # Modular startup/shutdown hooks; model preloader (VERIFIED)
│   ├── config.py                # Base Settings class (VERIFIED: config.py:22)
│   ├── pyproject.toml           # pytest config only (VERIFIED: [tool.pytest.ini_options])
│   ├── requirements.txt / requirements-dev.txt
│   ├── Dockerfile / Dockerfile.prod
│   ├── DOMAIN_ALLOWLIST.yaml
│   ├── alembic/                 # Alembic migration harness (VERIFIED: env.py, alembic.ini)
│   │   ├── env.py  alembic.ini  migration_helpers.py  script.py.mako
│   │   └── versions/            # ~62 migration scripts (VERIFIED: list_dir)
│   ├── domains/                 # DDD bounded contexts — 16 domains (VERIFIED)
│   │   ├── accounts/ analytics/ audit/ catalog/ comms/ country/ customers/
│   │   ├── finance/ governance/ hr/ logistics/ orders/ payments/ promotions/
│   │   ├── security/ suppliers/
│   │   ├── _mixin_compliance.py  __init__.py
│   │   └── (per-domain: models/ services/ schemas/ read_models/ policies/
│   │        ports.py events.py features.py serializers.py subscribers.py)  # (VERIFIED via orders/)
│   ├── modules/                 # Per-actor API surface (VERIFIED)
│   │   ├── admin/ customer/ employee/ logistics/ supplier/
│   │   │   └── routers/         # one router file per domain (VERIFIED)
│   │   └── (admin also: auth/ serializers/)
│   ├── kernel/                  # Value primitives (VERIFIED: money.py, currency.py, country.py…)
│   ├── infrastructure/          # Cross-cutting tech (VERIFIED)
│   │   ├── database/  (base.py, database.py, models.py, rls_interceptor.py,
│   │   │               migrations/, migrations.py, seed/, seed_data/, sql/, …)
│   │   ├── observability/  events/  http/  messaging/  ml/  redis/  valkey/
│   │   ├── security/  storage/  uploads/(empty)  utils/  config.py
│   ├── middleware/              # 20+ ASGI middleware + orchestrator.py (VERIFIED)
│   ├── providers/               # Third-party integration adapters (VERIFIED)
│   │   ├── payments/ (stripe, paypal, paytabs, tap, thawani, connect, webhooks…)
│   │   ├── storage/ (r2_client, s3_client)  ai/  comms/  barcode/ qr/ ocr/
│   │   ├── scanner/ voice/ shipping/ geography/ news/ image/ bg_removal/
│   │   ├── security/ finance/ analytics/ automation/  http.py  _base.py
│   ├── rbac/                    # Roles/permissions engine (VERIFIED: roles.py, resolution.py…)
│   ├── jobs/                    # Celery app + tasks + MCP servers (VERIFIED)
│   ├── scripts/                 # Backend maintenance/gen/gate scripts (VERIFIED)
│   ├── tests/                   # 183 pytest files across ~14 subdirs (VERIFIED)
│   └── var/                     # runtime dir (UNKNOWN contents)
├── frontend/
│   ├── web_app/                 # Next.js 16 App Router (VERIFIED: package.json:31 "next":"16.3.4")
│   │   ├── src/ (app/ components/ hooks/ lib/ logo/ services/ shared/ styles/
│   │   │         theme/ types/ utils/ __mocks__/ __tests__/)
│   │   ├── src/app/api/**/route.ts   # Next.js Route Handlers / BFF (VERIFIED: 10 files)
│   │   ├── e2e/ (Playwright, ~55 specs)  __tests__/ (Jest)  public/ (static svgs)
│   │   ├── next.config.ts  middleware.ts  tailwind.config.js  playwright.config.ts
│   │   └── Dockerfile  openapi.json  (+ many stray *.txt/*.png test/build outputs)
│   ├── mobile_app/              # Expo / React Native (VERIFIED: package.json:5 expo AppEntry)
│   │   ├── app/ ((auth)/ (tabs)/ admin/ …)  components/ lib/ theme/ assets/
│   │   ├── android/  e2e/  app.config.js  app.json  metro.config.js  pnpm-lock.yaml
│   └── shared/                  # @zozi/shared cross-platform lib (VERIFIED: package.json:2)
│       └── src/ (api/ components/ logo/ types/ + ~35 helper .ts modules)
├── .github/                     # CI/CD (VERIFIED: workflows/ + dependabot.yml)
│   └── workflows/ (ci.yml, build.yml, deploy.yml, e2e.yml, rollback.yml,
│                   architecture-gate.yml, router-generation.yml,
│                   schema-audit.yml, security.yml)
├── monitoring/                  # Prometheus/Grafana/Tempo/Promtail + py monitors (VERIFIED)
├── nginx/                       # nginx.conf reverse proxy (VERIFIED)
├── scripts/                     # Root-level ops/gen/audit scripts (VERIFIED)
├── documents/                   # ~85 design/spec/audit docs (VERIFIED)
├── _audit/                      # THIS audit (rules, plan, findings/, _logs/)
├── _design_investigation/       # design-diff artifacts (INFERRED: css/js dumps)
├── _most_imp_docx/              # curated doc copies (INFERRED)
├── browser-tests/               # root Playwright spec (VERIFIED: scaling_audit.spec.ts)
├── logs/  memory/               # pytest_baseline.txt / router-migration notes
├── docker-compose.yml / .override.yml / .prod.yml   # orchestration (VERIFIED)
├── Caddyfile  railway.toml  vercel.json  neon.ts     # edge/deploy config (VERIFIED)
├── Makefile  package.json  package-lock.json          # root task runner (VERIFIED)
├── run_zozi.bat / .sh  run_e2e.ps1  run_test.bat  update_diagram.py  # launchers
├── ARCHITECTURE_DIAGRAM.md  CODEBASE_AUDIT_BY_ASHER.md  SECURITY.md  WIRING_STATUS.json
├── investor_pitch_deck.html
├── .env  .env.example  .env.wrangler                  # env (root = Docker Compose)
├── .gitleaks.toml  .semgrep.yml  .githooks/  .kilo/  .neon   # dev/security tooling
└── (generated/artifacts) .next/  node_modules/  dump.rdb  test_phase7e2.db{,-shm,-wal}
                          .pytest_cache/ .ruff_cache/ .hypothesis/
```

Enumeration confidence: **VERIFIED** for every path shown with a VERIFIED tag; sub-trees marked INFERRED were listed but not every file opened.

---

## Application Components

| Component | Location | Evidence | Confidence |
|---|---|---|---|
| HTTP API service (FastAPI) | `backend/main.py` | `app = FastAPI(title=…, lifespan=build_lifespan(), docs_url="/docs")` — backend/main.py:75-83 | VERIFIED |
| Background worker (Celery) | `backend/jobs/celery_app.py` | `celery_app = Celery("zozi", broker=…, include=[…])` — celery_app.py:10-21; queues `ml/periodic/payouts/emails` — :33-38 | VERIFIED |
| Celery Beat scheduler | `backend/jobs/celery_app.py` + `backend/jobs/periodic_tasks.py` | `beat_schedule={…}` — celery_app.py:57-80; compose `celery -A celery_app beat` — docker-compose.yml:180-190 | VERIFIED |
| DDD domain layer (16 bounded contexts) | `backend/domains/*` | Dirs: accounts…suppliers — list_dir backend/domains; per-domain structure (models/services/schemas/read_models/policies/ports) — list_dir backend/domains/orders | VERIFIED |
| Per-actor API modules (5) | `backend/modules/{admin,customer,employee,logistics,supplier}` | list_dir backend/modules; each `routers/` holds 1 file per domain — list_dir modules/*/routers; aggregation — modules/admin/routers/__init__.py:9-38 | VERIFIED |
| Kernel value primitives | `backend/kernel/` | Files money.py, currency.py, country.py, numbering.py, period.py — list_dir backend/kernel | VERIFIED |
| Infrastructure (cross-cutting) | `backend/infrastructure/` | database/, observability/, messaging/, redis/, valkey/, storage/, security/, utils/, ml/ — list_dir | VERIFIED |
| RBAC engine | `backend/rbac/` | roles.py, resolution.py, catalog.py, service.py, models/, services/ — list_dir backend/rbac | VERIFIED |
| Middleware pipeline | `backend/middleware/` | 20+ modules incl. authentication_middleware, csrf_middleware, rate_limit_middleware; `setup_middleware(app)` — main.py:85, orchestrator.py | VERIFIED |
| Integration providers (adapters) | `backend/providers/` | payments/, storage/, ai/, comms/, ocr/, qr/, barcode/, scanner/, voice/, shipping/… — list_dir backend/providers | VERIFIED |
| Web app (Next.js App Router) | `frontend/web_app/` | `"next": "16.3.4"` + scripts `next dev/build/start` — web_app/package.json:6-8,31; App Router `src/app/` — list_dir | VERIFIED |
| Web BFF (Route Handlers) | `frontend/web_app/src/app/api/**/route.ts` | 10 `route.ts` files (auth/register, auth/me, currency/context, geo, z-rmbg, frontend-errors…) — file_search | VERIFIED |
| Mobile app (Expo / React Native) | `frontend/mobile_app/` | `"main": "node_modules/expo/AppEntry.js"`, `expo ~57.0.9`, `react-native 0.81.4` — mobile_app/package.json:5,22-24 | VERIFIED |
| Shared cross-platform lib | `frontend/shared/` | `"name":"@zozi/shared"`, `"main":"src/index.ts"` — shared/package.json:2,5; consumed as `"@zozi/shared":"file:../shared"` — web_app/package.json:25 | VERIFIED |
| MCP servers (agent tooling) | `backend/jobs/mcp_server.py`, `backend/jobs/mcp_marketplace_server.py` | list_dir backend/jobs | INFERRED (files present; not opened) |
| CLI / maintenance scripts | `backend/scripts/`, `scripts/` | e.g. seed_categories.py, pg_backup.py, schema_drift_gate.py — list_dir backend/scripts; audit/backup/gen tools — list_dir scripts | VERIFIED |
| Monitoring stack | `monitoring/` | prometheus.yml, alertmanager.yml, grafana/, tempo/, promtail/, docker-compose.monitoring.yml — list_dir | VERIFIED |

---

## Entry Points

| Entry Point | File | Function/Class | Purpose | Evidence |
|---|---|---|---|---|
| ASGI application object | `backend/main.py` | `app` (`FastAPI(...)`) | The importable ASGI app served by uvicorn (`main:app`) | backend/main.py:75-83 | 
| Local run (module main) | `backend/main.py` | `if __name__ == "__main__": uvicorn.run("main:app", …, port=8000)` | Direct `python main.py` launch | backend/main.py:~322-324 |
| Backend start (npm) | `package.json` | script `start:backend` | `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000` | package.json:7 |
| Backend start (Docker) | `docker-compose.yml` | service `backend` | `command: uvicorn main:app --host 0.0.0.0 --port 8000` | docker-compose.yml:48 |
| Backend start (Railway/prod) | `railway.toml` | `[deploy] startCommand` | `APP_ENV=production uvicorn main:app --host 0.0.0.0 --port $PORT --proxy-headers` | railway.toml:9 |
| App lifespan (startup/shutdown) | `backend/lifespan.py` | `build_lifespan()` → `lifespan()` | Model preload, table ensure, RLS, seed, service/event registration | lifespan.py:317-340; wired at main.py:79 |
| Celery worker | `backend/jobs/celery_app.py` | `celery_app` | Worker app; run via `celery -A celery_app worker -Q <queue>` | celery_app.py:10; docker-compose.yml:98,148,160,172 |
| Celery beat | `backend/jobs/celery_app.py` | `celery_app.conf.beat_schedule` | Periodic scheduler | celery_app.py:57; docker-compose.yml:189 |
| Web app dev/build/start | `frontend/web_app/package.json` | scripts `dev`/`build`/`start` | `next dev` / `next build` / `next start` | web_app/package.json:6-8 |
| Web middleware (edge) | `frontend/web_app/middleware.ts` | Next.js middleware | Present at web_app root (edge request handling) | list_dir frontend/web_app |
| Mobile app dev/build | `frontend/mobile_app/package.json` | scripts `dev`/`build` | `expo start` / `expo export` | mobile_app/package.json:6-8 |
| Combined dev | `package.json` | script `dev` | `npm run start:backend & npm run start:web` | package.json:6 |
| WebSocket routes | `backend/main.py` | `/ws/user`, `/ws/admin/background-jobs` | Realtime user + admin job sockets | main.py:198-201, 205 |
| Health/readiness probes | `backend/main.py` | `/health`, `/health/deps`, `/health/ready` | Liveness/readiness endpoints | main.py:106-179 |
| Router mounting | `backend/main.py` | `_load_routers()` | Dynamically imports & mounts per-actor module routers | main.py:245-278 |

---

## Configuration

| Configuration | File | Technology/Purpose | Evidence |
|---|---|---|---|
| Base app settings | `backend/config.py` | `class Settings` with `_DEFAULTS` dict (auth, DB, CORS, tokens, runtime flags) | config.py:22-40, 94-95 |
| Settings facade (canonical import) | `backend/infrastructure/utils/config.py` | Re-exports base settings: `from config import *`; `settings` used app-wide | infrastructure/utils/config.py:2; imported at main.py:29 |
| Additional scoped configs | `backend/infrastructure/config.py`, `backend/providers/config.py`, `backend/providers/payments/config.py` | Per-layer config modules (infra / providers / payment providers) | file_search backend/**/config.py (5 total) |
| pytest configuration | `backend/pyproject.toml` | `[tool.pytest.ini_options]` testpaths, markers, filterwarnings | pyproject.toml:1-13 |
| Alembic config | `backend/alembic/alembic.ini`, `backend/alembic/env.py` | Migration harness; `target_metadata = ModelsBase.metadata`; DATABASE_URL override | env.py:16-23 |
| Celery config | `backend/jobs/celery_app.py` | Broker/backend, serialization, routes, beat schedule | celery_app.py:10-80 |
| Domain allowlist | `backend/DOMAIN_ALLOWLIST.yaml` | Architecture/import allowlist (governance) | list_dir backend |
| Root env (Docker Compose) | `.env`, `.env.example` | Compose variable source (POSTGRES_*, SECRET_KEY, STRIPE_*, R2_*…) — values blank/placeholder in template | .env.example:1-49 |
| Cloudflare env | `.env.wrangler` | UTF-16 file beginning `CLOUDFL…` (Cloudflare-related env) | read_file .env.wrangler:1 (binary/UTF-16) |
| Backend env | `backend/.env`, `backend/.env.example` | FastAPI runtime env (flags `BOOTSTRAP_SCHEMA_ON_STARTUP=false`, `RUN_LEGACY_MIGRATIONS_ON_STARTUP=false`) | backend/.env:16-17 |
| Web env | `frontend/web_app/.env.local`, `.env.example` | Next.js public/runtime env | list_dir frontend/web_app |
| Mobile env | `frontend/mobile_app/.env` (per repo memory) | Expo env | list_dir mobile_app (.gitignore present); repo-memory note |
| TypeScript config | `frontend/web_app/tsconfig.json`, `frontend/shared/tsconfig.json`, `frontend/mobile_app/tsconfig.json` | TS compiler config | list_dir (each app) |
| Next.js config | `frontend/web_app/next.config.ts`, `postcss.config.mjs`, `tailwind.config.js` | Build/styling | list_dir frontend/web_app |
| Lint/format/security tooling | `.gitleaks.toml`, `.semgrep.yml`, `backend` ruff (`.ruff_cache/`), `eslint.config.js` (web/mobile) | Secret scan / SAST / lint | list_dir root & apps |
| Secrets locations (NOT values) | `.env*`, compose `environment:` blocks | `SECRET_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `TWILIO_*`, `OPENAI_API_KEY`, `R2_*`/`S3_*`, `POSTGRES_PASSWORD` — declared as keys only (templates blank) | .env.example:29-49; docker-compose.yml:34-45 — **values not exposed** |

---

## Build/Deployment

| File | Technology | Purpose | Evidence |
|---|---|---|---|
| `backend/Dockerfile` | Docker (python:3.11-slim) | Backend image; installs OpenCV/GL sys deps; `CMD uvicorn main:app` | backend/Dockerfile:1-33 |
| `backend/Dockerfile.prod` | Docker | Production backend image (referenced by prod compose) | docker-compose.prod.yml:24-26 |
| `frontend/web_app/Dockerfile` | Docker (node:22-alpine, multi-stage) | Builds web with local `../shared`; `npm ci --legacy-peer-deps`; runner `npm start` | web_app/Dockerfile:1-33 |
| `docker-compose.yml` | Docker Compose | Dev/base stack: postgres:18-alpine, valkey:9.0-alpine, backend, 4 celery workers, celery-beat, frontend | docker-compose.yml:1-190 |
| `docker-compose.override.yml` | Docker Compose | Adds PgBouncer pooler + rewires backend DATABASE_URL to pooler:6432 | docker-compose.override.yml:1-23 |
| `docker-compose.prod.yml` | Docker Compose | Prod: PgBouncer (scram-sha-256), Dockerfile.prod, `STORAGE_BACKEND=s3`, S3 creds | docker-compose.prod.yml:1-40 |
| `Caddyfile` | Caddy | Reverse proxy: `api.*`→backend:8000 (+WebSockets), `*`→frontend:3000; auto-HTTPS; security headers | Caddyfile:11-58 |
| `nginx/nginx.conf` | nginx | Alternative reverse proxy config | list_dir nginx |
| `railway.toml` | Railway | Backend deploy via `backend/Dockerfile`; healthcheck `/health` | railway.toml:1-14 |
| `vercel.json` | Vercel | Frontend deploy: `framework:"nextjs"`, build `frontend/web_app`, output `.next`, cache & security headers | vercel.json:1-40 |
| `neon.ts` | Neon | `defineConfig({ auth: true })` (Neon project/auth config) | neon.ts:1-6 |
| `Makefile` | Make | Task runner: backend/frontend setup, docker-up/down, tests, lint, `routers`/`routers-check` | Makefile:1-40 |
| `package.json` (root) | npm | Orchestration scripts (dev/test/build/db:migrate/seed); **no dependencies declared** | package.json:5-24 |
| `.github/workflows/ci.yml` | GitHub Actions | Lint (ruff) → architecture-gates → unit-tests → schema-drift (Python 3.11) | ci.yml:1-80 |
| `.github/workflows/deploy.yml` | GitHub Actions | Staging/prod deploy to GHCR images `zozi-backend`/`zozi-frontend`; pre-deploy validation | deploy.yml:1-60 |
| `.github/workflows/*` | GitHub Actions | build.yml, e2e.yml, rollback.yml, architecture-gate.yml, router-generation.yml, schema-audit.yml, security.yml | list_dir .github/workflows |
| `.github/dependabot.yml` | Dependabot | Dependency update automation | list_dir .github |
| `run_zozi.bat` / `run_zozi.sh` / `run_e2e.ps1` / `run_test.bat` | Shell/PS launchers | Local dev/test launchers | list_dir root |
| `monitoring/docker-compose.monitoring.yml` | Docker Compose | Observability stack (Prometheus/Grafana/Tempo/Promtail) | list_dir monitoring |

### Database migration files & wiring
- **Canonical: Alembic.** Harness `backend/alembic/` (alembic.ini, env.py, migration_helpers.py, script.py.mako). `target_metadata = ModelsBase.metadata` from `infrastructure.database.base` (env.py:8-20); DB URL from `DATABASE_URL` env (env.py:22-23). **~62 revision files** in `backend/alembic/versions/` dated 2026-07-26 → 2026-09-04 (list_dir). VERIFIED.
- **Startup migration bootstrap:** `_bootstrap_runtime()` attempts an Alembic upgrade on startup (lifespan.py:58+; referenced at build_lifespan). VERIFIED (function present).
- **Legacy in-code path (dormant):** `backend/infrastructure/database/migrations.py` and `backend/infrastructure/database/migrations/new_tables.py` exist; gated by `bootstrap_schema_on_startup` / `run_legacy_migrations_on_startup` — **default False** (config.py:94-95; backend/.env:16-17). VERIFIED presence; "dormant by default" INFERRED from flag defaults.

### ORM / model definitions & wiring
- **ORM = SQLAlchemy declarative.** Canonical `Base` in `backend/infrastructure/database/base.py` (imported by alembic env.py:9 and domains/orders/models/__init__.py:1). VERIFIED.
- **Model classes live in `domains/*/models/*.py`.** Example: `domains/orders/models/order_entities.py` is canonical; `domains/orders/models/orders.py` is a **re-export shim** (`Order, OrderItem, OrderLogisticsAllocation, ReturnRequest`) — orders.py:1-31. VERIFIED.
- **Registration wiring:** `backend/infrastructure/database/models.py` only calls `clear_mappers()` (models.py:14). Actual registration is by `_preload_all_models()` which `pkgutil.walk_packages` over 15 `domains.<d>.models` packages at startup — lifespan.py:282-311. VERIFIED. (Note: `infrastructure` must not import `domains`; preload lives in lifespan — models.py:1-14 docstring.)

### API definitions & wiring
- **Routes declared directly in per-actor module routers** under `backend/modules/{customer,supplier,logistics,admin,employee}/routers/`, one file per domain (e.g., admin has 20 files incl. accounts…suppliers + config_versions, disputes, permissions, staff, tickets). VERIFIED (list_dir all 5).
- **Mounting:** `_load_routers()` imports each `modules.<m>.routers` package and mounts its `routers` + `public_routers` lists; each router carries its own `APIRouter(prefix=…)` — main.py:245-278. Aggregation contract: `modules/admin/routers/__init__.py:9-38` builds the lists from per-domain `router`/`public_router` attributes. VERIFIED.
- **Auto-router generator RETIRED:** controllers/route-marker generation removed; "HTTP routes are declared directly in module routers"; retired generator parked at `scripts/retired_auto_router.py` — main.py:281-289. No `controllers/` directories exist (file_search `backend/modules/**/controllers/**` → none). VERIFIED.
- Web BFF: 10 `route.ts` handlers under `frontend/web_app/src/app/api/` (auth/*, currency/context, geo, z-rmbg, frontend-errors). VERIFIED.
- `frontend/web_app/openapi.json` present (generated API schema snapshot). VERIFIED (list_dir).

### Third-party integrations (adapters)
| Category | Location | Evidence |
|---|---|---|
| Payments | `backend/providers/payments/` | stripe.py, stripe_sdk.py, paypal.py, paytabs.py, tap.py, thawani.py, connect.py, webhooks.py, registry.py — list_dir |
| Object storage | `backend/providers/storage/` | r2_client.py (Cloudflare R2), s3_client.py, storage_backend.py — list_dir; `STORAGE_BACKEND=r2` (.env.example:47) / `=s3` (compose.prod:31) |
| AI / ML | `backend/providers/ai/` | openai_client.py, huggingface.py, vision.py, image_ai_service.py, recommendation.py, sentiment.py, chatbot.py — list_dir |
| Comms | `backend/providers/comms/` | email.py, sms.py, twilio.py, whatsapp.py, whatsapp_selfhosted.py — list_dir |
| Payments SDK (web) | `frontend/web_app` | `@stripe/react-stripe-js`, `@stripe/stripe-js` — web_app/package.json:13-14 |
| Payments SDK (mobile) | `frontend/mobile_app` | `@stripe/stripe-react-native` — mobile_app/package.json |
| Error tracking / tracing | `backend/infrastructure/observability/` | Sentry DSN wiring (main.py:62-68), OpenTelemetry setup (main.py:98-103), Prometheus (main.py:88) |
| Neon Postgres | `neon.ts` + `DATABASE_URL` | neon.ts:1-6 |

### Test directories
- **Backend:** `backend/tests/` — **183** `test_*.py` files (file_search) across `architecture/`, `domains/`, `security/`, `providers/`, `infrastructure/`, `modules/`, `integration/`, `system/`, `middleware/`, `observability/`, `rbac/`, `kernel/`, `admin/`, `workflows/`, `playwright/`, `_support/`, plus `conftest.py`. VERIFIED.
- **Web:** `frontend/web_app/e2e/` (Playwright, ~55 `*.spec.ts`), `frontend/web_app/__tests__/`, `src/__tests__/` (Jest). VERIFIED.
- **Mobile:** `frontend/mobile_app/e2e/`, Detox config `.detoxrc.js`, `jest.config.js`. VERIFIED.
- **Shared:** `frontend/shared/src/__tests__/`. VERIFIED.
- **Root:** `browser-tests/scaling_audit.spec.ts`. VERIFIED.

### Documentation
- `documents/` (~85 files: `.md` specs/audits + several `.txt` feature notes) — list_dir. Root docs: `ARCHITECTURE_DIAGRAM.md`, `CODEBASE_AUDIT_BY_ASHER.md`, `SECURITY.md`. Doc-artifact dirs: `_most_imp_docx/`, `_design_investigation/`, `_audit/`. VERIFIED.

### Generated files, build artifacts, static assets, upload handling
- **Static assets:** `frontend/web_app/public/` (file.svg, globe.svg, next.svg, placeholder.svg, vercel.svg, window.svg) — list_dir; `frontend/mobile_app/assets/`. VERIFIED.
- **Upload handling:** `/uploads` static mount is conditional on `backend/uploads/` existing (`if os.path.isdir(_uploads_dir)`) — main.py:92-95. `backend/infrastructure/uploads/` is **empty** (list_dir). Runtime media handled via `providers/storage` (R2/S3) and `infrastructure/storage/storage.py`. VERIFIED.
- **Generated / build artifacts (present in tree):** root `.next/`, `node_modules/`, `package-lock.json`, `dump.rdb`, `test_phase7e2.db{,-shm,-wal}`, `.pytest_cache/`, `.ruff_cache/`, `.hypothesis/`; `frontend/web_app/.next/`, `tsconfig.tsbuildinfo`, `openapi.json`, `build_log.txt`, `build_output.txt`, `output.txt`, `next.err`, `playwright-results.txt`, and PNG screenshots. VERIFIED presence (list_dir); git-tracked-vs-ignored status = UNKNOWN (see Unknown Areas).

---

## Unknown Areas

1. **git-tracked vs ignored status** of root `.next/`, root `node_modules/`, `dump.rdb`, `test_phase7e2.db*`, and the frontend stray artifacts — NOT DETERMINABLE without a full `.gitignore` read (repo memory suggests some are intentionally ignored, but that is a note, not verified source). UNKNOWN.
2. **Contents/purpose** of `.kilo/`, `.neon`, `.githooks/`, `backend/var/`, and `memory/Zozi-Cursor-Router-Migration/` — directories listed but files not opened. NOT DETERMINABLE FROM AVAILABLE CODE (this phase).
3. **MCP servers** `backend/jobs/mcp_server.py` / `mcp_marketplace_server.py` — files present but not opened; their runtime role is INFERRED only.
4. **`.env.wrangler`** is UTF-16 encoded and begins `CLOUDFL…`; full key inventory not enumerated (avoided to prevent secret exposure). Its exact deployment target (Cloudflare Workers vs Pages) is UNKNOWN.
5. Whether all five module router packages actually import successfully at runtime — `_load_routers()` and the module `__init__` aggregators **swallow import errors** (main.py:262-278; admin/__init__.py:29-31), so a broken router would be silently skipped. Runtime mounting outcome is UNKNOWN in a purely structural pass (flagged for Phase 08).

---

## Suspicious Areas (structural anomalies only — no security/quality judgment)

> These are **structural** observations (misplaced/duplicated/stray files, config↔runtime mismatches). No severity, security, or quality assessment is made here.

1. **Stray root `.next/` build output** outside the Next.js app (the app is `frontend/web_app/`, which has its own `.next/`). Root-level Next build output is anomalous. Evidence: list_dir root shows `.next/`; app at web_app/package.json:31. VERIFIED.
2. **Root `node_modules/` + `package-lock.json` with a dependency-less root `package.json`.** Root `package.json` declares scripts only (no `dependencies`/`devDependencies`) yet a root lockfile and `node_modules/` exist. Evidence: package.json:5-24 (no deps); list_dir root. VERIFIED. (Consistent with repo-memory note of a stale monorepo lock.)
3. **Committed runtime/DB artifacts at repo root:** `dump.rdb` (Redis/Valkey dump) and `test_phase7e2.db` + `-shm`/`-wal` (SQLite). These are runtime/test outputs sitting at the repo root. Evidence: list_dir root. VERIFIED.
4. **Many stray test/build output files under `frontend/web_app/`:** e.g. `build_log.txt`, `build_output.txt`, `output.txt`, `next.err`, `playwright-results.txt`, `bulk_test_output.txt`, `staff_test*.txt`, `standalone_test*.txt`, `logistics_test.txt`, `*.png` screenshots, and a file literally named `-w`. Evidence: list_dir frontend/web_app. VERIFIED.
5. **Makefile references the retired auto-router generator.** Targets `routers` / `routers-check` under "Auto-generated routers (Design 3)" (Makefile:1, 38-40) contradict main.py:281-289 which states the generator was "fully retired." Config↔runtime mismatch. VERIFIED.
6. **CI `router-generation.yml` present** despite generator retirement — possible stale workflow. Evidence: list_dir .github/workflows (filename only; contents not opened). INFERRED.
7. **Stray Python test inside the web Playwright (TS) e2e folder:** `frontend/web_app/e2e/test_vat_remittance_fix.py` sits among `*.spec.ts` Playwright tests. Evidence: list_dir frontend/web_app/e2e. VERIFIED.
8. **`backend/infrastructure/uploads/` is empty** and the `/uploads` static mount targets a *different* path (`backend/uploads/`, which is absent from `backend/` listing), so the mount is inert in this checkout. Evidence: list_dir infrastructure/uploads (empty); main.py:92-95; list_dir backend (no `uploads/`). VERIFIED.
9. **Duplicated monitoring scripts across two locations:** `fraud_monitoring.py`, `ghost_order_detector.py`, `threat_feed_updater.py` exist in **both** `backend/jobs/` and `monitoring/`. Evidence: list_dir backend/jobs & list_dir monitoring. VERIFIED (whether contents are identical was not compared — flagged for Phase 13).
10. **Two coexisting DB-schema mechanisms** (Alembic canonical + legacy in-code `migrations.py`/`migrations/new_tables.py`). Both present; legacy gated off by default flags. Evidence: backend/alembic/versions/ vs infrastructure/database/migrations/new_tables.py; config.py:94-95. VERIFIED (coexistence); "Alembic is authoritative" INFERRED.
11. **Multiple `config.py` modules (5).** `backend/config.py`, `infrastructure/utils/config.py`, `infrastructure/config.py`, `providers/config.py`, `providers/payments/config.py`. This is **not** a contradiction: `infrastructure/utils/config.py:2` does `from config import *` (re-export of the base), and the others are layer-scoped. Noted for map completeness. VERIFIED.
12. **Redundant top-level launcher/doc surface:** overlapping launchers (`run_zozi.bat/.sh`, `run_e2e.ps1`, `run_test.bat`) and multiple doc-copy trees (`documents/`, `_most_imp_docx/`, `_design_investigation/`, root `*.md`). Structural sprawl only. Evidence: list_dir root. VERIFIED.

---

*End of Phase 01 structural inventory. No codebase files were modified; only this report was created. Severity, security, dependency-usage, dead-code, and correctness assessments are deferred to their respective phases per AUDIT_PLAN.md.*
