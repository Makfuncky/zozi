# Repository Structure Specification (00_REPO_STRUCTURE.md)

This document describes the target folder layout for the ZOZI platform. It is
the canonical reference for the architecture audit's `repo_structure` rules.

## Top-level layout

```
zozi/
├── backend/                 # FastAPI service (Python)
│   ├── main.py              # LAYER 0: app creation, middleware, router mounting
│   ├── middleware/          # LAYER 1: request preprocessing, auth, RLS context
│   ├── dependencies/        # LAYER 1: shared FastAPI dependencies
│   ├── routers/             # LAYER 2: {surface}_{domain}_{operation}.py (flat)
│   ├── controllers/         # LAYER 3: grouped by DOMAIN (finance/, orders/, ...)
│   ├── services/            # LAYER 4: grouped by DOMAIN (business rules, DB ops)
│   ├── providers/           # LAYER 5: external adapters (ai/, media/, ...)
│   ├── models/              # LAYER 6: SQLAlchemy ORM grouped by DOMAIN
│   ├── data/                # db engine, session factory, base classes (LAYER 7)
│   ├── alembic/             # migrations
│   ├── utils/               # pure helpers (no state, no DB)
│   ├── events/              # domain events grouped by domain
│   ├── jobs/                # background tasks grouped by domain
│   └── tests/               # test files (exempt from most rules)
├── frontend/
│   ├── web_app/             # Next.js 15 web frontend
│   ├── mobile_app/          # React Native / Expo
│   └── shared/              # shared frontend libraries
├── documents/               # project documentation
│   ├── scope/               # scope binding + structure specs
│   └── archive/             # historical/reference docs
├── scripts/                 # ops/maintenance scripts (exempt)
└── _extra_files/            # local scratch/experiments (gitignored)
```

## Backend layering rules

Imports flow **downward only**:

```
main → middleware/dependencies → routers → controllers → services → providers → models → db
```

- Routers must not perform `session.add/commit/delete` or business logic.
- Controllers orchestrate services; they must not write to the session directly.
- Services contain business rules and DB operations; they must not import routers/controllers.
- Providers adapt external APIs; they must not import services/controllers.
- Models define ORM only and must not import any other layer.

## Cross-cutting packages

`utils/`, `events/`, `jobs/`, `tests/`, `scripts/` are exempt from the strict
layer ordering but must remain free of business logic in `utils/` and free of
DB state in `utils/events/jobs`.
