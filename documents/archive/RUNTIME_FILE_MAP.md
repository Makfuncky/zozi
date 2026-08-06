# Runtime File Map

This document is the canonical map for runtime configuration, lockfiles, Docker files, and local database files in this repository.

## Environment Files

| File | Used By | Purpose | Auto-loaded |
|---|---|---|---|
| `.env` | Root Docker Compose files | Compose variables such as `POSTGRES_*`, `SECRET_KEY`, `NEXT_PUBLIC_API_URL` | Yes, by `docker compose` from repo root |
| `.env.example` | Humans | Template for the root Docker Compose `.env` | No |
| `.env.production` | Humans only | Optional production template; not auto-read by backend, web app, or scripts | No |
| `backend/.env` | FastAPI backend | Backend runtime settings loaded by `backend/utils/config.py` | Yes |
| `backend/.env.example` | Humans | Template for `backend/.env` | No |
| `frontend/web_app/.env.example` | Humans | Template for `frontend/web_app/.env.local` | No |
| `frontend/web_app/.env.local` | Next.js web app | Web-only runtime variables such as `NEXT_PUBLIC_API_URL` | Yes |
| `frontend/mobile_app/.env` | Expo mobile app | Mobile-only Expo public variables such as `EXPO_PUBLIC_API_URL` | Yes |

## Lockfiles

| File | Status | Notes |
|---|---|---|
| `frontend/web_app/package-lock.json` | Keep | Canonical lockfile for the Next.js web app |
| `frontend/mobile_app/package-lock.json` | Keep | Canonical lockfile for the Expo mobile app |
| `frontend/shared/package-lock.json` | Keep | Canonical lockfile for the shared package |
| `documents/snap/Logo/zozi-logo-app/package-lock.json` | Keep, isolated | Belongs only to the archived logo sandbox under `documents/snap` |
| `package-lock.json` | Removed | Stale root lockfile from an old monorepo layout; no matching root `package.json` exists |

## Docker Files

| File | Status | Notes |
|---|---|---|
| `docker-compose.yml` | Keep | Base stack definition |
| `docker-compose.override.yml` | Keep | Local development override |
| `docker-compose.prod.yml` | Keep | Production stack definition |
| `backend/Dockerfile` | Keep | Backend image |
| `frontend/web_app/Dockerfile` | Keep | Web frontend image; Compose and CI now point to this file explicitly |

## Database Files

| File | Status | Notes |
|---|---|---|
| `backend/zozi.db` | Keep | Canonical local SQLite database |
| `backend/zozi.db-wal` | Keep while backend is in use | SQLite write-ahead log file |
| `backend/zozi.db-shm` | Keep while backend is in use | SQLite shared-memory sidecar file |
| `zozi.db` | Removed | Stale root-level SQLite file left over from older relative-path behavior |

## Orphaned Generated Paths

These are not canonical app roots and should not be recreated manually:

- `frontend/.next`
- `frontend/node_modules`

The real web build cache and dependencies live under `frontend/web_app/`.

## Canonical Paths Summary

- Web app: `frontend/web_app`
- Mobile app: `frontend/mobile_app`
- Shared package: `frontend/shared`
- Backend runtime config: `backend/.env`
- Web runtime config: `frontend/web_app/.env.local`
- Mobile runtime config: `frontend/mobile_app/.env`
- Compose runtime config: `.env`
- Local SQLite DB: `backend/zozi.db`