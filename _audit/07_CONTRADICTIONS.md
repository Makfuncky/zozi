# Contradictions

Generated: 2026-09-30T04:40:00Z
Run number: 1

## CONTR-001

- **Category:** code_vs_config
- **Source A (L0):** `backend/config.py:340` — config class raises AttributeError for DATABASE_URL
- **Source B (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:303` — DATABASE_URL is listed as required env var
- **Conflict:** Code does not define DATABASE_URL setting, but TECHNOLOGY_STACK.md declares it required.
- **Impact:** App cannot start without DATABASE_URL; missing setting causes AttributeError on import.
- **Project completion blocker:** yes
- **Recommendation:** Add DATABASE_URL to backend/config.py as pydantic-settings field.
- **User decision required:** no

## CONTR-002

- **Category:** code_vs_config
- **Source A (L0):** `backend/config.py:340` — config class raises AttributeError for VALKEY_URL
- **Source B (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:402` — VALKEY_URL is listed as required env var
- **Conflict:** Code does not define VALKEY_URL setting, but TECHNOLOGY_STACK.md declares it required.
- **Impact:** Valkey-dependent features (sessions, cache, rate-limit, event bus, Celery broker) cannot function.
- **Project completion blocker:** yes
- **Recommendation:** Add VALKEY_URL to backend/config.py as pydantic-settings field.
- **User decision required:** no

## CONTR-003

- **Category:** preflight_failure
- **Source A (L0):** `alembic.ini` — missing script_location key
- **Source B (L3):** `_most_imp_docx/ARCHITECTURE_STACK.md:114` — alembic is the single schema source of truth
- **Conflict:** Alembic cannot run due to missing script_location; contradicts the architecture law that migrations must be runnable.
- **Impact:** Database migrations cannot be executed; schema changes cannot be deployed.
- **Project completion blocker:** yes
- **Recommendation:** Add script_location = backend/alembic/versions to alembic.ini.
- **User decision required:** no

## CONTR-004

- **Category:** preflight_failure
- **Source A (L0):** `docker-compose` — requires POSTGRES_PASSWORD
- **Source B (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:277` — Docker Compose is the local dev orchestration
- **Conflict:** docker-compose config fails because POSTGRES_PASSWORD is not set in root .env; local dev environment is broken.
- **Impact:** Developers cannot start local dev environment with Docker Compose.
- **Project completion blocker:** yes
- **Recommendation:** Add POSTGRES_PASSWORD to root .env or .env.example.
- **User decision required:** no

## CONTR-005

- **Category:** preflight_failure
- **Source A (L0):** `frontend/web_app` — pnpm-lock.yaml absent
- **Source B (L3):** `_most_imp_docx/TECHNOLOGY_STACK.md:182` — pnpm is the canonical package manager
- **Conflict:** pnpm install --frozen-lockfile fails because lockfile is absent; contradicts the technology stack rule.
- **Impact:** Frontend build and CI cannot run with frozen lockfile; dependency drift possible.
- **Project completion blocker:** yes
- **Recommendation:** Generate pnpm-lock.yaml via pnpm install and commit it.
- **User decision required:** no

## CONTR-006

- **Category:** preflight_failure
- **Source A (L0):** `tests/` — tests/architecture/ directory missing
- **Source B (L3):** `_most_imp_docx/ARCHITECTURE_STACK.md:117` — tests/architecture/ must contain test_import_laws.py, test_feature_catalog.py, test_schema_discipline.py, test_model_relocation.py
- **Conflict:** Required architecture test directory does not exist; contradicts the architecture law that architecture tests must be present.
- **Impact:** CI cannot enforce architectural laws; import violations may go undetected.
- **Project completion blocker:** yes
- **Recommendation:** Create tests/architecture/ with the four required test files.
- **User decision required:** no
