# SHARED CONTEXT FOR ALL SUB-AGENTS

## Benchmark Documents (read top to bottom)
- `_most_imp_docx/ARCHITECTURE_STACK.md` — 325 laws, 15 domains, 5 modules, package layout
- `_most_imp_docx/TECHNOLOGY_STACK.md` — All technology versions, SDKs, infra

## Project Structure
- Backend: `backend/` — FastAPI, Python 3.13, SQLAlchemy 2.0, asyncpg
- Frontend Web: `frontend/web_app/` — Next.js 16, React 19, TypeScript
- Frontend Mobile: `frontend/mobile_app/` — Expo SDK 57, React Native 0.86
- Shared: `frontend/shared/` — Cross-platform TypeScript

## Key Laws (from ARCHITECTURE_STACK.md)
- Law 1: Arrows point down only (modules → rbac → domains → kernel → infrastructure)
- Law 3: Cross-domain writes only via events.py/subscribers.py; reads via ports.py
- Law 5: Country is orthogonal scope axis (RLS)
- Law 6: Schema discipline (every table in domain schema)
- Law 19: No float for money (Decimal only)
- Law 21: Timestamps = server_default=func.now()
- Law 23: Audit columns (created_at, updated_at, country_code, is_deleted)
- Law 32: No hardcoded secrets
- Law 45: No N+1 (lazy=selectin or joined)
- Law 49: Linear migration history
- Law 50: Explicit transactions
- Law 82: No default credentials
- Law 86: Env-specific configs (no inheritance)

## Key Tech (from TECHNOLOGY_STACK.md)
- Python 3.13.x, FastAPI 0.141.x, SQLAlchemy 2.0.52
- uv 0.12.12 (package manager, NOT pip)
- Valkey 9.0.6+ (cache/sessions/broker)
- Celery 5.5+ (background tasks)
- Neon PostgreSQL 18 (prod), PostgreSQL 16 (dev)
- Cloudflare R2 (object storage)
- pydantic-settings 2.9.1+ (typed env vars)
- structlog (logging)
- prometheus-fastapi-instrumentator 8.1.0+ (metrics)

## Forbidden
- pip (use uv)
- requests (use httpx)
- psycopg2 (use asyncpg)
- python-magic (use puremagic)
- pytz/tzlocal (use zoneinfo)
- prometheus-client standalone (use prometheus-fastapi-instrumentator)
- slowapi/limits (use fastapi-limiter-valkey)
- paypalrestsdk/paypalcheckoutsdk (use direct REST via httpx)
- float for money (use Decimal)
- print() in production (use structlog)

## Working Directory
All paths are relative to `D:\Projects\10- E-COMMERCE WEBSITE\zozi`

## Logging
Every sub-agent MUST log all actions to `_audit/resolver/logs/<file_slug>.log`
Format: `<ISO-8601> <ACTION> <DETAIL>`
