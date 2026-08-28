# ZOZI — Agent Quick Reference

## What This Is

GCC-focused e-commerce marketplace. Modular monolith backend (FastAPI), Next.js 16 web frontend, Expo mobile app.

## Stack (verified)

| Layer | Stack |
|---|---|
| Backend | FastAPI 0.115, Python 3.11, SQLAlchemy 2.0 async, Alembic, SQLite (dev) / PostgreSQL 15 (prod) |
| Frontend | Next.js 16.3.1 (App Router, RSC), React 18.3.1, TypeScript 5.8 strict, Tailwind 3.4 |
| Mobile | Expo React Native |
| Auth | JWT (HS256) + `jti` blacklist + refresh rotation |
| Cache | Redis 8 (sessions, catalog, rate-limit) |
| Jobs | APScheduler 3.11 |
| Payments | Stripe + Tap + PayPal + PayTabs + Thawani |

## Three-Axis Architecture (critical — read ARCHITECTURE_DIAGRAM.md first)

```
modules/{who}/  →  domains/{what}/  →  infrastructure/  ←  providers/
     ↑                    ↑
   rbac/              kernel/
```

| Axis | Path | Role |
|---|---|---|
| **Module** (who) | `modules/{admin,customer,employee,logistics,supplier}/` | Auth + thin routers + serializers |
| **Domain** (what) | `domains/{16 domains}/` | Services, models, schemas, policies, events |
| **Feature** (may) | `rbac/` + `domains/*/features.py` | Permission atoms, gated by `require_feature()` |

### The Laws (325 total, enforced by CI + `tests/architecture/test_import_laws.py`)

1. **Arrows point down only** — `modules → domains → infrastructure`. Domains never import modules. `infrastructure`/`kernel` import nothing above them.
2. **Module routers stay thin** — auth context + `require_feature(...)` + one service call. No DB writes, no business rules.
3. **Cross-domain writes only via events** (`events.py`/`subscribers.py`); cross-domain reads only via `ports.py`/`read_models/`.
4. **Features single-sourced** in `domains/*/features.py`; aggregated by `rbac/catalog.py`. CI fails on `require_feature("…")` literals not in catalog.
5. **Country is the orthogonal scope axis** — RLS session context + `country_staff_assignments`.
6. **Schema discipline** — one Postgres schema per domain; Alembic is the only schema source; `snake_case`, plural tables, `<thing>_id` FKs.
7. **Allowlist rule** — `DOMAIN_ALLOWLIST.yaml` tracks temporary cross-domain imports; may only shrink.

## Provider Rules

- Providers (`backend/providers/`) wrap external SDKs only — **no business logic, no domain imports**.
- Each provider exposes `HAS_<SDK>` boolean flags (e.g., `HAS_STRIPE`, `HAS_REMBG`). Domains must gracefully degrade when absent.
- Domain services call providers via function calls — providers never import from domains.

## Key Structural Facts

- **16 domains**: accounts, analytics, audit, catalog, comms, country, customers, finance, governance, hr, logistics, orders, promotions, security, suppliers
- **5 modules**: admin, customer, employee, logistics, supplier
- **~22 provider packages**: ai, auth, payments, geography, comms, image, storage, shipping, etc.
- **kernel/** — pure business primitives (money/Decimal, currency, numbering, country, period). Must not import domains/modules/rbac/providers.
- **rbac/** — catalog, roles, resolution (actor×role×country→features, Redis-cached), dependencies (`require_feature`, `require_module`).
- **@zozi/shared** (`frontend/shared`) — cross-platform TS. `permissions.ts` is **generated** from `GET /rbac/catalog`.

## Commands

```bash
# Backend
cd backend
python -m pytest -x -q --timeout=30          # run tests (transaction-rollback isolation)
python -m pytest tests/architecture/         # architecture law checks
ruff check .                                  # lint

# Frontend
cd frontend/web_app
npm run dev                                   # dev server (proxies /api/*, /admin/*, /auth/* → backend)
npm run lint                                  # ESLint
npx tsc --noEmit --skipLibCheck               # typecheck
npx jest --runInBand                          # unit tests
npx playwright test                           # e2e

# From root
make test-backend && make test-frontend && make lint-backend && make typecheck
```

## Test Fixtures (backend/tests/conftest.py)

- `db_session` — transaction-rolled-back session (no data leaks between tests)
- `client` / `admin_client` / `supplier_client` / `customer_client` — pre-authenticated TestClients
- `admin_token` / `supplier_token` / `customer_token` — JWT strings for demo users
- Demo users seeded: `admin@zozi.com`, `supplier@zozi.com`, `customer@zozi.com` (passwords match `admin123`/`supplier123`/`customer123`)
- `APP_ENV=test` auto-set; CSRF disabled; rate limiting disabled

## Environment Files

| File | Purpose |
|---|---|
| `.env.example` | Source of truth for required vars |
| `.env` | Docker Compose only |
| `backend/.env` | FastAPI runtime |
| `frontend/web_app/.env.local` | Next.js (client + server) |

## Known Gotchas

- **Two DeclarativeBase classes** — `infrastructure.database.base.Base` (real, 318 tables) vs `db.base.Base` (empty). Canonical is `infrastructure.database.base.Base`. Several files still import the empty one.
- **RLS is a runtime no-op** — `instrument_rls` is never called (`rls_interceptor.py:359`). Country scoping exists in code paths but isn't enforced at the DB layer.
- **Webhook middleware unexported** — `WebhookVerificationMiddleware`/`WebhookIPWhitelistMiddleware` exist but aren't wired in `orchestrator.py`.
- **No root `package-lock.json`** — lockfiles are per-package only (`frontend/web_app/package-lock.json`, etc.).
- **Frontend API proxy** — Next.js rewrites `/api/*`, `/admin/*`, `/auth/*`, `/hr/*`, `/__api/*`, `/uploads/*` to `NEXT_PUBLIC_API_URL` (default `http://127.0.0.1:8000`).
- **Shared package not built** — `@zozi/shared` is consumed via `file:` protocol; no pre-build step needed for dev.
- **Alembic migrations** — `scripts/deploy.sh` and CI run `alembic upgrade head` automatically. For manual deploy, run migrations before serving.

## File Placement Rules

- New backend business logic → `domains/{domain}/services/`
- New API endpoints → `modules/{module}/routers/{domain}.py` (one file per domain per module)
- New external SDK wrappers → `providers/{category}/`
- Cross-domain communication → `events.py` (writes) or `ports.py` (reads) only
- Root-level `utils/`, `routers/`, `controllers/`, `services/`, `db/` are **forbidden** — they live inside modules/domains/infrastructure

## Before Committing

1. `ruff check .` passes
2. `python -m pytest tests/architecture/` passes (import laws intact)
3. `npx tsc --noEmit --skipLibCheck` passes (frontend)
