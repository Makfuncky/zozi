# ZOZI Platform — AI Agent Instructions

## Project Overview

ZOZI is an e-commerce marketplace platform with:
- **Backend**: FastAPI/Python with SQLite (dev) / PostgreSQL (prod)
- **Frontend**: Next.js 15 with React 19, TypeScript, Tailwind CSS
- **Mobile**: React Native / Expo
- **Infrastructure**: Docker Compose, Railway, Vercel

## Key Conventions

- Backend code lives in `backend/`, web frontend in `frontend/web_app/`
- `.env.example` is the source of truth for required env vars
- Root `.env` is for Docker Compose; `backend/.env` is for FastAPI
- `frontend/web_app/.env.local` is for the Next.js frontend
- No root `package-lock.json` — lockfiles are per-package only
- The backend uses `requirements.txt` (no lockfile yet)

## Architecture Notes

- `backend/main.py` is large (599 lines) — router registration and lifespan hooks are monolithic
- Router modules are loaded dynamically via `importlib` in `_load_routers()`
- Middleware pipeline is managed by `backend/middleware/orchestrator.py`
- CORS origins are configured via `CORS_ORIGINS` env var (comma-separated)
- JWT tokens include `jti` for blacklisting support

## Security Considerations

- SECRET_KEY must be set in production (app won't start without it)
- CSRF middleware is active for production; bypassed in dev/test
- Rate limiting is configured per-path in `rate_limit_middleware.py`
- All passwords are bcrypt-hashed (72-char truncation caveat)
- File uploads are limited to 10MB by default
