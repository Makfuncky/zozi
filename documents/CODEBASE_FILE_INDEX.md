# Zozi Codebase File Index (Canonical)

## Purpose

This is the canonical high-signal file index for the Zozi workspace.

It is intentionally concise and points to source-of-truth folders and files.

## Snapshot (2026-05-08)

Current maintained file counts from workspace scan:

- Backend Python source files: 326
- Web app source files: 311
- Mobile app source files: 186
- Shared source files: 101
- Documentation markdown files: 98

## Top-Level Ownership

| Area | Root | Primary technology | Notes |
| --- | --- | --- | --- |
| Backend API | `backend/` | FastAPI + SQLAlchemy + Alembic | Core business logic and data layer |
| Web App | `frontend/web_app/` | Next.js + React + Tailwind | Admin, supplier, customer, logistics web UX |
| Mobile App | `frontend/mobile_app/` | Expo + React Native | Mobile customer/supplier/logistics UX |
| Shared Frontend | `frontend/shared/` | TypeScript shared package | Shared contracts, theme, utility logic |
| Documentation | `documents/` | Markdown | Product, architecture, operations, audits |
| Scripts and Ops | `scripts/`, root files | Python + shell + batch | Tooling, startup, audit, maintenance |

## Backend Index

### Entry and configuration

- `backend/main.py`
- `backend/config.py`
- `backend/database.py`
- `backend/auth.py`

### Key code domains

- `backend/controllers/`
- `backend/routers/`
- `backend/services/`
- `backend/utils/`
- `backend/db/`
- `backend/alembic/`

### Key tests

- `backend/tests/`

## Web App Index

### App and layout

- `frontend/web_app/src/app/`
- `frontend/web_app/src/app/layout.tsx`

### Shared UI and state

- `frontend/web_app/src/components/`
- `frontend/web_app/src/lib/`
- `frontend/web_app/src/styles/globals.css`
- `frontend/web_app/tailwind.config.js`

### Web tests

- `frontend/web_app/src/__tests__/`
- `frontend/web_app/e2e/`

## Mobile App Index

### App and navigation

- `frontend/mobile_app/app/`

### Shared mobile modules

- `frontend/mobile_app/components/`
- `frontend/mobile_app/lib/`

### Mobile tests

- `frontend/mobile_app/lib/__tests__/`
- `frontend/mobile_app/e2e/`

## Shared Frontend Index

- `frontend/shared/src/types/`
- `frontend/shared/src/theme.ts`
- `frontend/shared/src/adminPermissions.ts`
- `frontend/shared/src/localization.ts`
- `frontend/shared/src/statusColors.ts`

## Documentation Index (High Priority)

- `documents/DOCUMENTATION_INDEX.md`

### Staff

- `documents/STAFF_MANAGEMENT_GUIDE.md`
- `documents/STAFF_MANAGEMENT_OPERATIONAL_GUIDE.md`
- `documents/STAFF_MANAGEMENT_IMPLEMENTATION_SUMMARY.md`
- `documents/STAFF_MANAGEMENT_TESTING_CHECKLIST.md`

### Logistics

- `documents/LOGISTIC_MANAGEMENT.md`
- `documents/LOGISTIC_CHRGES.md` (compatibility alias)
- `documents/LOGISTICS_AUDIT_GAPS.md` (compatibility alias)
- `documents/LOGISTICS_CHARGE_FILE_INVENTORY.md` (compatibility alias)

### UI and migration

- `documents/WEB_APP_UI_UX_INVENTORY.md`
- `documents/UI-MIGRATION-NOTES.md`
- `documents/UI-MIGRATION-REPORT.md`
- `documents/UIUX.md`

## Compatibility Files

- `documents/CODE_FILE_INDEX.md` exists as a compatibility pointer to this document.

## Maintenance Rules

1. Keep this file as a canonical map, not a running change log.
2. Put historical execution logs and ad-hoc validation notes in dedicated audit/run reports.
3. When major structure changes occur, update this index and compatibility pointer together.
