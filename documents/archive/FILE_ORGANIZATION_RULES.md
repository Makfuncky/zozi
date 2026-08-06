# File Organization Rules

This document defines the file and folder rules for the ZOZI repository. Use it together with `documents/RUNTIME_FILE_MAP.md`.

## Goals

- Keep one clear owner for every file.
- Keep runtime files separate from templates and generated output.
- Keep deployable code close to the app or service that owns it.
- Keep cleanup decisions low risk by avoiding duplicate sources of truth.

## Canonical Directory Ownership

| Path | Purpose | Do Keep Here | Do Not Keep Here |
|---|---|---|---|
| `/` | Repo orchestration | compose files, README, root scripts, repo-level config | app source files, random runtime caches, extra lockfiles |
| `backend/` | FastAPI service | backend code, backend tests, backend env template/runtime config | frontend code, duplicate DB files outside the canonical path |
| `frontend/web_app/` | Next.js web app | web source, web tests, web env template/runtime config, web Dockerfile | mobile code, shared package source, root-level caches |
| `frontend/mobile_app/` | Expo mobile app | mobile source, mobile env file, mobile lockfile | web-only files, ad-hoc backend helpers |
| `frontend/shared/` | shared frontend package | shared utilities, shared components, shared lockfile | app-specific runtime config |
| `documents/` | docs and planning | specs, audits, architecture docs, file maps | generated runtime output, active source code |
| `artifacts/` | generated exports and reports | CSV exports, smoke outputs, generated artefacts | hand-maintained docs or source files |
| `scripts/` | automation | setup, deploy, validation, maintenance scripts | one-off applied migrations/fixes that are no longer needed |

## Environment File Rules

Active runtime env files in this repo are:

- `.env` for Docker Compose only
- `backend/.env` for the FastAPI backend
- `frontend/web_app/.env.local` for the Next.js web app
- `frontend/mobile_app/.env` for the Expo mobile app

Templates and examples stay in git:

- `.env.example`
- `.env.production`
- `backend/.env.example`
- `frontend/web_app/.env.example`

Rules:

- Do not add new env files unless a distinct runtime actually needs one.
- Keep secrets in runtime env files, not in docs or source files.
- Keep examples sanitized and safe to commit.

## Dependency and Lockfile Rules

- Keep exactly one lockfile next to each real `package.json`.
- Do not create a root `package-lock.json` unless the repo also has a real root `package.json`.
- Do not commit `node_modules`, package caches, or build caches.
- For this repo, install `frontend/shared` before or alongside `frontend/web_app` on clean setups.

## Shared Package Boundary Rules

- `frontend/shared` is for cross-app code only.
- Shared modules must not import app-local aliases such as `@/lib/*`, `@/types`, or other files owned by `frontend/web_app` or `frontend/mobile_app`.
- If a component needs app-local stores, routers, platform setup hooks, or app-only types, keep that component in the owning app and only share the pure helper logic underneath it.
- Keep shared exports prop-driven and platform-agnostic where possible; use app-local wrappers in web or mobile for wiring.

## Docker Rules

- Keep compose files at repo root.
- Keep one Dockerfile per deployable service.
- The web frontend must build with `frontend` as the Docker build context and `frontend/web_app/Dockerfile` as the Dockerfile path.
- Do not create alternate Dockerfiles for the same service unless there is a real environment-specific need.

## Database and Generated Data Rules

- The canonical local SQLite database is `backend/zozi.db`.
- Do not create duplicate root-level DB files.
- Treat CSV exports, smoke outputs, logs, caches, and test results as generated output, not source.
- Generated files belong under dedicated output folders such as `artifacts/`, not mixed into app source trees.

## Documentation Rules

- Keep long-form workstream prompts in `documents/PROMPT.md`.
- Keep the shorter operational checklist in `documents/TO_DO.md`.
- Keep runtime ownership and active file mapping in `documents/RUNTIME_FILE_MAP.md`.
- Update an existing document when the subject already has a canonical home; do not create overlapping docs with near-duplicate names.

## Test Placement Rules

- Backend tests belong under `backend/tests/`.
- Web tests belong under `frontend/web_app/src/__tests__/` or the framework-standard test location already used by that app.
- Mobile tests belong under `frontend/mobile_app/`.
- Shared package tests belong under `frontend/shared/`.
- Do not leave loose test files at repo root or duplicate old test directories after migrations.

## Before Adding a New File

1. Does an existing folder already own this concern?
2. Is the file source code, runtime config, a template, or generated output?
3. Will CI, Docker, scripts, and docs still point to the same canonical path?
4. Does this create a second source of truth for an existing feature?

If the answer to the last question is yes, update the existing file instead of adding a new one.