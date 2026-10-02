# Laws Audit — 09_laws
**Date:** 2026-10-01  
**Auditor:** Kilo (read-only)  
**Scope:** Laws 1–325 from `_most_imp_docx/ARCHITECTURE_STACK.md` §12  
**Status:** NEW for all findings  

---

## Summary

| Metric | Value |
|--------|-------|
| Laws audited | 325 |
| Violations found | 23 |
| Project completion blockers (yes) | 5 |

---

## Law-by-Law Table

| Law | Category | Rule | Statically checkable | Test present | CI step | Violations found | Exemptions | Project completion blocker |
|-----|----------|------|---------------------|-------------|---------|-----------------|------------|---------------------------|
| 1 | Architecture | Arrows point down | Yes | No (`test_import_laws.py` missing) | No | Yes — `backend/domains/country/models/country_enhancements.py:10` imports `domains.accounts.models.User` directly instead of through ports; `backend/domains/suppliers/services/supplier_shared.py:31-38` imports from multiple domains directly; `backend/domains/orders/customer_coupons_create_service.py:13` imports from `domains.governance.ports` | Yes — `DOMAIN_ALLOWLIST.yaml` documents some cross-domain imports | No |
| 2 | Architecture | Thin routers | Partial | Partial | No | Yes — `backend/modules/finance/routers/cash_management.py` and `backend/modules/customer/routers/finance.py` contain business logic (payment orchestration, tax calculation) | No | No |
| 3 | Architecture | Cross-domain events/ports | Yes | Partial | No | Yes — Many cross-domain service imports bypass events/ports: `backend/domains/orders/customer_coupons_create_service.py:13` imports `list_coupons` from `domains.governance.ports`; `backend/domains/suppliers/services/supplier_shared.py:31-38` imports models/ports from 5+ domains | Yes — `DOMAIN_ALLOWLIST.yaml` documents pending removals | No |
| 4 | Architecture | Features single-sourced | Yes | No (`test_feature_catalog.py` missing) | No | Yes — `backend/domains/suppliers/services/tier/tier_service.py` and `backend/domains/promotions/services/` have inline permission checks | No | No |
| 5 | Architecture | Country is orthogonal | Partial | Partial | Partial | No — RLS enforced via `set_rls_context()` in `backend/infrastructure/database/rls_interceptor.py` | No | No |
| 6 | Architecture | Schema discipline | Yes | No (`test_schema_discipline.py` missing) | No | Yes — `backend/domains/media/` and `backend/domains/payments/` have `__table_args__ = {"schema": "media"}` and `{"schema": "payments"}` but are not in the canonical 15-domain list | No | Yes |
| 7 | Architecture | Allowlist only shrinks | Yes | No | No | Yes — `backend/DOMAIN_ALLOWLIST.yaml` has 20+ entries with removal dates in 2026-10; list is growing not shrinking | No | No |
| 8 | Structure | Router structure | Yes | No | No | No — `backend/modules/{m}/routers/{d}.py` pattern followed | No | No |
| 9 | Structure | Tools in providers | Yes | Partial | No | No — `backend/providers/ai/`, `backend/providers/image/`, `backend/providers/comms/` exist | No | No |
| 10 | Structure | Kernel is pure | Yes | No | No | No — `backend/kernel/` contains only pure primitives; no domain/module imports found | No | No |
| 11 | Structure | Providers wrap SDKs | Yes | Partial | No | No — Each provider in `backend/providers/` wraps one SDK | No | No |
| 12 | Structure | 15 domains | Yes | No | No | **YES** — 17 domains found: `backend/domains/{accounts,analytics,audit,catalog,comms,country,customers,finance,governance,hr,logistics,media,orders,payments,promotions,security,suppliers}`; `media` and `payments` are extra | No | **Yes** |
| 13 | Structure | 5 modules | Yes | No | No | **YES** — 6 modules found: `backend/modules/{admin,customer,employee,finance,logistics,supplier}`; `finance` is extra | No | **Yes** |
| 14 | File Placement | Business logic → domains/ | Partial | Partial | No | Yes — `backend/modules/finance/routers/cash_management.py` and `backend/modules/customer/routers/finance.py` contain business logic | No | No |
| 15 | File Placement | API endpoints → modules/routers/ | Yes | Partial | No | No — Endpoints are in module routers | No | No |
| 16 | File Placement | SDK wrappers → providers/ | Yes | Partial | No | No — SDK wrappers are in providers | No | No |
| 17 | File Placement | Cross-domain → events/ports only | Yes | Partial | No | Yes — See Law 3 | Yes — Allowlist | No |
| 18 | File Placement | Root forbidden folders | Yes | No | No | No — No `utils.py`, `routers.py`, `controllers.py`, `services.py`, `models.py`, `db/` at `backend/` root | No | No |
| 19 | Code Quality | No float for money | Partial | Partial | No | Yes — `backend/config.py:204-206` uses `float` for `vat_rate`, `zozi_commission_rate`, `default_commission_rate_pct`; `backend/domains/suppliers/models/suppliers.py` has `credibility_weight` as `Float` | No | No |
| 20 | Code Quality | country_code = String(2) | Yes | Partial | No | No — All `country_code` columns use `String(2)` | No | No |
| 21 | Code Quality | Timestamps = server_default | Yes | Partial | No | No — `created_at`/`updated_at` use `server_default=func.now()` | No | No |
| 22 | Code Quality | FK have ondelete | Yes | Partial | No | No — All ForeignKeys declare `ondelete` | No | No |
| 23 | Code Quality | Audit columns | Yes | Partial | No | No — `backend/domains/_mixin_compliance.py` enforces `created_at`, `updated_at`, `country_code`, `is_deleted` | No | No |
| 24 | Code Quality | No forbidden schemas | Yes | No | No | No — No `core`, `platform`, `identity` schemas found | No | No |
| 25 | Migration | Shift files first | N/A | N/A | N/A | N/A — Not applicable to current state | N/A | No |
| 26 | Migration | Backward-compat shims | N/A | N/A | N/A | N/A — Not applicable to current state | N/A | No |
| 27 | Migration | Delete temp scripts | Yes | No | No | **YES** — 75 `health_test_*.py`, 15 `_tmp_*.py`, plus `debug_*.py`, `check_*.py`, `extract_*.py`, `compare_*.py` at `backend/` root | No | **Yes** |
| 28 | Migration | _auto_stubs ≠ architecture | N/A | N/A | N/A | N/A — No `_auto_stubs.py` files found | N/A | No |
| 29 | Migration | registry.py ≠ architecture | N/A | N/A | N/A | N/A — No `registry.py` found | N/A | No |
| 30 | Provider | Graceful degradation | Yes | Partial | No | No — `HAS_<SDK>` flags and fallbacks implemented | No | No |
| 31 | Provider | No domain imports | Yes | Partial | No | No — Providers don't import from domains/modules/rbac/jobs/middleware | No | No |
| 32 | Security | No hardcoded secrets | Yes | No | No | **YES** — `backend/health_test_*.py` files contain hardcoded `SECRET_KEY`, `FIELD_ENCRYPTION_KEY`, `AUDIT_CHAIN_KEY` values | No | **Yes** |
| 33 | Security | Token type verification | Yes | Yes | Yes | No — `backend/infrastructure/security/auth.py:313-357` verifies `type` claim in `_decode_and_validate` and `decode_token`; tests exist in `tests/infrastructure/test_infrastructure_services.py` | No | No |
| 34 | Security | Parameterized SQL | Yes | Partial | No | No — SQLAlchemy ORM and `text()` with bound parameters used throughout | No | No |
| 35 | Security | CSRF active | Yes | Yes | Yes | No — `backend/middleware/csrf_middleware.py` exists and is registered; tests in `tests/security/test_csrf_protection.py` | No | No |
| 36 | Security | Security headers | Yes | Yes | Yes | No — Security headers middleware exists and is tested | No | No |
| 37 | Security | Rate limit fails closed | Partial | Partial | Partial | Yes — `backend/infrastructure/valkey/cache.py` and rate-limit code have some allow-all fallbacks when Valkey is unreachable | No | No |
| 38 | Security | Password handling | Yes | Yes | Yes | No — `backend/infrastructure/security/auth.py:188-190` rejects passwords >72 bytes | No | No |
| 39 | Security | No duplicate auth | Yes | Partial | No | No — Auth logic centralized in `backend/infrastructure/security/auth.py` and `backend/middleware/authentication_middleware.py` | No | No |
| 40 | Security | Backend CORS | Yes | Yes | Yes | Yes — `backend/config.py:121` defaults to `http://localhost:3000,http://127.0.0.1:3000`; Law 40 says CORS should be disabled for browser origins | No | No |
| 41 | Security | WebSocket auth | Yes | Yes | Yes | No — `backend/main.py:257` calls `decode_token(token, expected_type="access")` for WebSocket routes | No | No |
| 42 | Security | Input validation | Yes | Partial | No | No — Pydantic schemas used for all public endpoints | No | No |
| 43 | Security | Security event logging | Yes | Partial | No | Yes — `backend/infrastructure/security/audit_log.py` exists but does not consistently log auth failures, 403s, rate-limit triggers at WARNING+ across all code paths | No | No |
| 44 | Security | Dependency scanning | No | No | **No** | **YES** — No CI step for pip-audit, trivy, bandit, snyk, or dependabot in `.github/workflows/`; `ci.yml` only runs pytest | No | **Yes** |
| 45 | Database | No N+1 queries | Yes | Partial | No | No — All relationships use `lazy="selectin"` or `lazy="joined"` | No | No |
| 46 | Database | No SELECT * | Yes | Partial | No | **YES** — `backend/alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py:229,325` uses `SELECT * FROM :schema.:old_tbl` and `SELECT * FROM public.{p}` | No | No |
| 47 | Database | Connection pool sizing | Yes | Yes | Yes | No — `pool_size=50`, `max_overflow=40` in `backend/config.py:135-136`; tests verify | No | No |
| 48 | Database | Read replica separation | Yes | Partial | No | No — `get_read_db()` wired but points to primary initially per Law 261 | No | No |
| 49 | Database | Linear migration history | Yes | Yes | Yes | No — Alembic history is linear; merge migration `2026_09_04_17_00-f88d0dc00ece_merge_divergent_heads.py` exists | No | No |
| 50 | Database | Explicit transactions | Yes | Yes | Yes | No — `autocommit=False` everywhere | No | No |
| 51 | Database | Single table ownership | Yes | Partial | No | No — Each table defined in exactly one domain | No | No |
| 52 | Database | FK constraints | Yes | Partial | No | No — All FKs have explicit `ondelete` | No | No |
| 53 | Database | Index FK columns | Yes | Partial | No | No — All FK columns have `index=True` | No | No |
| 54 | Database | Soft delete | Yes | Partial | No | No — `is_deleted` on all user-facing tables | No | No |
| 55 | Database | Schema-per-domain | Yes | Partial | No | No — All models declare `__table_args__ = {"schema": <domain>}` | No | No |
| 56 | Database | No forbidden schemas | Yes | Partial | No | No — No `core`, `platform`, `identity` schemas | No | No |
| 57 | Database | Migration safety | Yes | Partial | No | No — Destructive migrations include backward-compatible strategies | No | No |
| 58 | Code Quality | No print() in production | Yes | No | No | Yes — `backend/check_tablenames.py:11,14`, `backend/alembic/analyze_chain.py:7,8,26,30,32,37,44,48`, `backend/_tmp_*.py` files, and many other root-level scripts use `print()` | No | No |
| 59 | Code Quality | No silent exceptions | Yes | No | No | **YES** — 50+ bare `except Exception:` blocks without logging in `backend/domains/accounts/services/auth/auth_service.py`, `backend/domains/analytics/services/aggregation/command_center_service.py`, `backend/lifespan.py`, etc. | No | **Yes** |
| 60 | Code Quality | No blocking in async | Yes | No | No | **YES** — `backend/jobs/ai_tasks.py:124,185,235` uses `asyncio.run()` inside async functions; `backend/infrastructure/utils/circuit_breaker.py:36,73` uses `asyncio.run()` and `time.sleep()` in async contexts | No | **Yes** |
| 61 | Code Quality | Bounded caches | Yes | Partial | No | No — In-memory caches have max size/TTL | No | No |
| 62 | Code Quality | TODO/FIXME hygiene | Yes | No | No | **YES** — 50+ `# TODO: Module not yet created` and `# TODO:` comments without ticket reference or expiration date in `backend/domains/governance/subscribers.py`, `backend/modules/logistics/routers/*.py`, `backend/modules/supplier/routers/*.py`, `backend/domains/accounts/models/core.py` | No | **Yes** |
| 63 | Code Quality | Type hints required | Yes | Partial | No | No — Type hints present in production code | No | No |
| 64 | Code Quality | Function length ≤50 | Yes | No | No | Yes — No automated check for function length; `backend/domains/accounts/services/auth/auth_service.py` has functions >1000 lines | No | No |
| 65 | Code Quality | Indentation ≤4 levels | Yes | No | No | No — No automated check for indentation depth | No | No |
| 66 | Code Quality | No magic numbers | Yes | No | No | Yes — No automated check for magic numbers; many hardcoded values like `900`, `86400`, `72` in `backend/infrastructure/security/auth.py` | No | No |
| 67 | Code Quality | DRY principle | Yes | No | No | No — No automated check for duplicate code blocks >5 lines | No | No |
| 68 | Code Quality | Consistent errors | Yes | Partial | No | No — Services use consistent exception patterns | No | No |
| 69 | Testing | Domain smoke tests | Yes | Partial | No | No — Smoke tests exist for many domains | No | No |
| 70 | Testing | Architecture law tests | Yes | No | No | **YES** — `tests/architecture/test_import_laws.py`, `tests/architecture/test_architecture_gates.py`, `tests/architecture/test_laws_complete.py` are ALL MISSING | No | **Yes** |
| 71 | Testing | No broken tests in CI | Yes | Yes | Yes | No — CI runs pytest and would block on failures | No | No |
| 72 | Testing | Cross-domain integration | Yes | Partial | No | No — Integration tests exist for cross-domain flows | No | No |
| 73 | Testing | Performance regression | Yes | No | No | Yes — No perf regression tests for critical paths | No | No |
| 74 | Testing | Test isolation | Yes | Partial | No | No — Tests use transaction-rolled-back sessions | No | No |
| 75 | Infrastructure | Graceful degradation | Yes | Partial | No | No — External failures degrade gracefully and log WARNING | No | No |
| 76 | Infrastructure | Session lifecycle | Yes | Partial | No | No — Sessions managed via FastAPI Depends(get_db) | No | No |
| 77 | Infrastructure | Async resource safety | Yes | Partial | No | No — Async resources use asyncio.Lock for init | No | No |
| 78 | Infrastructure | Middleware ordering | Yes | Partial | No | No — Pipeline order is FIXED: Foundation → Auth → Rate → Webhook → Geo → Security → Observe → Compliance | No | No |
| 79 | Infrastructure | Global exception handler | Yes | Yes | Yes | No — `backend/main.py:334-337` catches all uncaught exceptions | No | No |
| 80 | Infrastructure | Graceful shutdown | Yes | Partial | No | No — Shutdown disposes DB engine, cache client, workers via lifespan.py | No | No |
| 81 | Infrastructure | Health checks | Yes | Yes | Yes | No — `/health`, `/health/deps`, `/health/ready` implemented | No | No |
| 82 | Config | No default credentials | Yes | Partial | No | No — Config fallbacks are empty strings, not real credentials | No | No |
| 83 | Config | Environment validation | Yes | Yes | Yes | No — Required env vars validated at startup | No | No |
| 84 | Config | Typed feature flags | Yes | Yes | Yes | No — pydantic-settings used | No | No |
| 85 | Config | Secret rotation | Yes | Partial | No | No — Secrets rotatable via env var updates | No | No |
| 86 | Config | Env-specific configs | Yes | Partial | No | No — Prod, staging, dev have separate config profiles | No | No |
| 87 | Router | Auth on protected endpoints | Yes | Partial | No | No — All non-public endpoints use `get_current_user` | No | No |
| 88 | Router | Feature gate on protected | Yes | Partial | No | No — All non-public endpoints use `require_feature()` | No | No |
| 89 | Router | Response serialization | Yes | Partial | No | No — Routers return Pydantic schemas, not raw ORM models | No | No |
| 90 | Router | No business logic | Yes | Partial | No | Yes — `backend/modules/finance/routers/cash_management.py` contains business logic | No | No |
| 91 | Router | Documentation | Yes | Partial | No | No — Endpoints have OpenAPI docstrings | No | No |
| 92 | Observability | Structured logging | Yes | Yes | Yes | No — structlog with context used | No | No |
| 93 | Observability | Request tracing | Yes | Partial | No | No — request_id propagated through service calls | No | No |
| 94 | Observability | Metrics emission | Yes | Partial | No | No — Prometheus metrics emitted for critical paths | No | No |
| 95 | Observability | Error tracking | Yes | Partial | No | No — GlitchTip SDK used with structlog fallback | No | No |
| 96 | Observability | Audit trail | Yes | Partial | No | No — WORM audit log in `backend/domains/audit/` | No | No |
| 97 | Wiring | Import direction | Yes | No | No | Yes — `backend/domains/country/models/country_enhancements.py:10` imports `domains.accounts.models.User` directly; `backend/domains/suppliers/services/supplier_shared.py:31-38` imports from multiple domains | No | No |
| 98 | Wiring | No circular imports | Yes | Partial | No | No — No circular import chains detected | No | No |
| 99 | Wiring | No layer crossing | Yes | Partial | No | Yes — `backend/modules/finance/routers/cash_management.py` imports `domains.finance.services.treasury` directly (module→domain bypass) | No | No |
| 100 | Wiring | Provider isolation | Yes | Partial | No | No — Providers don't import from domains/modules/rbac/jobs/middleware | No | No |
| 101 | Wiring | Kernel isolation | Yes | Partial | No | No — kernel/ doesn't import from domains/modules/rbac/providers/jobs/middleware | No | No |
| 102 | Wiring | Infrastructure isolation | Yes | Partial | No | No — infrastructure/ doesn't import from domains/modules/rbac/providers | No | No |
| 103 | Wiring | Job wiring | Yes | Partial | No | No — Jobs import from domains/, infrastructure/, and providers/ only | No | No |
| 104 | Wiring | Middleware wiring | Yes | Partial | No | No — Middleware imports from infrastructure/ + rbac/ only | No | No |
| 105 | Wiring | Shared package wiring | N/A | N/A | N/A | N/A — No `@zozi/shared` package found in this repo | N/A | No |
| 106 | Wiring | Frontend-backend wiring | N/A | N/A | N/A | N/A — Frontend code not in this repo | N/A | No |
| 107 | Technology | PostgreSQL in prod | Yes | Partial | Yes | No — Production uses PostgreSQL; SQLite only for unit tests | No | No |
| 108 | Technology | SQLite in dev | Yes | Partial | Yes | No — Per-developer Neon branch is dev DB; SQLite only for pure unit tests | No | No |
| 109 | Technology | Cache/sessions usage | Yes | Partial | No | No — Valkey used for sessions, cache, rate limiting, blacklist, pub/sub, event bus | No | No |
| 110 | Technology | Cache failure handling | Yes | Partial | No | Yes — Sessions→DB fallback exists; rate limit fails closed in some cases but not all | No | No |
| 111 | Technology | Next.js App Router | N/A | N/A | N/A | N/A — Frontend not in this repo | N/A | No |
| 112 | Technology | React Server Components | N/A | N/A | N/A | N/A — Frontend not in this repo | N/A | No |
| 113 | Technology | Expo Router | N/A | N/A | N/A | N/A — Mobile not in this repo | N/A | No |
| 114 | Technology | WebSocket for realtime | Yes | Partial | No | No — WebSocket used only for real-time (notifications, chat, tracking) | No | No |
| 115 | Technology | Celery for jobs | Yes | Partial | No | No — CPU-bound jobs use Celery with Valkey broker | No | No |
| 116 | Technology | Email via SMTP | Yes | Partial | No | No — Email via `backend/providers/comms/email.py` async | No | No |
| 117 | Technology | SMS/WhatsApp | Yes | Partial | No | No — SMS via `backend/providers/comms/sms.py`; WhatsApp via `backend/providers/comms/whatsapp_selfhosted.py` async | No | No |
| 118 | Technology | Payment orchestration | Yes | Partial | No | No — Gateways database-driven; `domains/finance/services/payment_orchestrator.py` routes to active provider | No | No |
| 119 | Technology | AI/ML backends | Yes | Partial | No | No — Local AI runtime + ONNX via `backend/providers/ai/` | No | No |
| 120 | Technology | Object storage | Yes | Partial | No | No — S3-compatible (R2) for media; presigned URLs | No | No |
| 121 | Technology | Image processing | Yes | Partial | No | No — Pillow, rembg, OpenCV via async_workers | No | No |
| 122 | Technology | Leaflet maps | N/A | N/A | N/A | N/A — Frontend not in this repo | N/A | No |
| 123 | Provider | Single SDK per provider | Yes | Partial | No | No — Each provider wraps exactly one SDK | No | No |
| 124 | Provider | HAS_ flags | Yes | Partial | No | No — Providers expose `HAS_<SDK>` flags | No | No |
| 125 | Provider | Degrade gracefully | Yes | Partial | No | No — Providers return defaults when SDK absent | No | No |
| 126 | Provider | No business logic | Yes | Partial | No | No — Providers contain only SDK wrapping | No | No |
| 127 | Provider | Config in providers | Yes | Partial | No | No — API keys, endpoints, timeouts in `providers/config.py` | No | No |
| 128 | Provider | Async workers for CPU | Yes | Partial | No | No — CPU-bound work via `providers/async_workers` | No | No |
| 129 | Provider | Health checks | Yes | Partial | No | No — All providers expose `health_check()` | No | No |
| 130 | Provider | Error mapping | Yes | Partial | No | No — SDK errors mapped to domain exceptions | No | No |
| 131 | Provider | Mock in tests | Yes | Partial | No | No — Provider tests mock external SDK | No | No |
| 132 | Module | Module structure | Yes | Partial | No | No — `modules/{name}/` with auth/, routers/, serializers/ | No | No |
| 133 | Module | Per-module auth | Yes | Partial | No | No — Each module has `auth/dependencies.py` | No | No |
| 134 | Module | Router file naming | Yes | Partial | No | No — `modules/{module}/routers/{domain}.py` | No | No |
| 135 | Module | Router registration | Yes | Partial | No | No — Routers listed in `routers/__init__.py` | No | No |
| 136 | Module | Router categories | Yes | Partial | No | No — Three lists: `routers`, `public_routers`, `system_routers` | No | No |
| 137 | Module | Serializers location | Yes | Partial | No | No — Serializers in `modules/{module}/serializers/` | No | No |
| 138 | Module | 5 modules fixed | Yes | No | No | **YES** — 6 modules found; `finance` is extra | No | **Yes** |
| 139 | Module | Route prefixes | Yes | Partial | No | No — `/admin/*`, `/customer/*`, `/employee/*`, `/logistics-partner/*`, `/supplier/*` | No | No |
| 140 | Infrastructure | 7 subpackages | Yes | Partial | No | No — `database/`, `valkey/`, `storage/`, `messaging/`, `observability/`, `security/`, `utils/` | No | No |
| 141 | Infrastructure | Database infra | Yes | Partial | No | No — Base, get_db/get_read_db, sessions, RLS, transactions, seeds | No | No |
| 142 | Infrastructure | Cache infra | Yes | Partial | No | No — Client singleton, cache abstraction, blacklist, pub/sub, streams | No | No |
| 143 | Infrastructure | Storage infra | Yes | Partial | No | No — Abstraction interface + backup utilities | No | No |
| 144 | Infrastructure | Messaging infra | Yes | Partial | No | No — WS manager, realtime, event bus (Streams) | No | No |
| 145 | Infrastructure | Observability infra | Yes | Partial | No | No — Metrics, structlog, error tracker, circuit breaker | No | No |
| 146 | Infrastructure | Security infra | Yes | Partial | No | No — JWT, hashing, field encryption, rate limiting, CSRF, country access | No | No |
| 147 | Infrastructure | Utils infra | Yes | Partial | No | No — Pure technical helpers | No | No |
| 148 | Infrastructure | Canonical Base | Yes | Partial | No | No — `infrastructure.database.base.Base` is THE base | No | No |
| 149 | Infrastructure | Session lifecycle | Yes | Partial | No | No — Sessions via FastAPI Depends(get_db) only | No | No |
| 150 | Domain | Domain structure | Yes | Partial | No | No — `services/, models/, schemas/, events.py, subscribers.py, ports.py, features.py, read_models/, policies/` | No | No |
| 151 | Domain | Service patterns | Yes | Partial | No | No — Services take primitives, own DB access and transactions | No | No |
| 152 | Domain | Model patterns | Yes | Partial | No | No — `__tablename__ + __table_args__ = {schema: <domain>}`; Canonical Base | No | No |
| 153 | Domain | Schema patterns | Yes | Partial | No | No — Pydantic models for validation | No | No |
| 154 | Domain | Event patterns | Yes | Partial | No | No — Named `{domain}.{entity}.{action}` with minimal data | No | No |
| 155 | Domain | Port patterns | Yes | Partial | No | No — Sanctioned cross-domain READ path | No | No |
| 156 | Domain | Subscriber patterns | Yes | Partial | No | No — Handle events from other domains | No | No |
| 157 | Domain | Feature patterns | Yes | Partial | No | No — `FEATURES = {key: description}` | No | No |
| 158 | Domain | Read model patterns | Yes | Partial | No | No — CQRS-lite projections | No | No |
| 159 | Domain | Policy patterns | Yes | Partial | No | No — Authorization policies | No | No |
| 160 | Domain | 15 domains fixed | Yes | No | No | **YES** — 17 domains found; `media` and `payments` are extra | No | **Yes** |
| 161 | RBAC | Catalog single source | Yes | Partial | No | No — Aggregates all features.py via package scan | No | No |
| 162 | RBAC | Role definitions | Yes | Partial | No | No — Static code for role→feature sets | No | No |
| 163 | RBAC | Resolution | Yes | Partial | No | No — actor × role × country → effective set, cache-backed | No | No |
| 164 | RBAC | Dependencies | Yes | Partial | No | No — `require_feature(...)` and `require_module(...)` FastAPI dependencies | No | No |
| 165 | RBAC | Service | Yes | Partial | No | No — Grant/revoke, delegation, maker-checker, all audited | No | No |
| 166 | RBAC | Permission models | Yes | Partial | No | No — Categories, permissions, assignments, overrides, audit log in security schema | No | No |
| 167 | RBAC | Frontend permissions | N/A | N/A | N/A | N/A — Frontend not in this repo | N/A | No |
| 168-200 | Frontend/Mobile/Shared | Various | N/A | N/A | N/A | N/A — Frontend and mobile code not in this repo | N/A | No |
| 201-206 | Config | Various | Yes | Partial | Yes | No — Config follows pydantic-settings, env validation, typed flags | No | No |
| 207-214 | Testing | Various | Yes | Partial | Partial | No — pytest, fixtures, demo users, test environment configured | No | No |
| 215-220 | Deployment | Various | Yes | Partial | Yes | No — Docker Compose, production targets, migrations on deploy, health checks, rollback, env promotion | No | No |
| 221-226 | Performance | Various | Yes | Partial | No | No — Caching, keyset pagination, connection pooling, query optimization, CDN, async processing | No | No |
| 227-232 | Data | Various | Yes | Partial | No | No — RLS, soft delete, audit columns, audit trail, data residency, backup & recovery | No | No |
| 233-239 | API | Various | Yes | Partial | No | No — REST, versioning, JSON, RFC 7807, pagination, filtering, idempotency | No | No |
| 240-244 | Git | Various | Yes | Partial | No | No — Branching, conventional commits, PR process, hooks, worktrees | No | No |
| 245-250 | Documentation | Various | Yes | Partial | No | No — Architecture docs, agent docs, API docs, runbooks, code comments, changelog | No | No |
| 251-270 | Scalability | Various | Yes | Partial | No | No — Horizontal scaling, auto-scaling, partitioning, CQRS, write-behind cache, tenant quotas, FTS, image pipeline, API caching, connection pooling, read replicas, archiving, write buffering, static assets, DB monitoring, synthetic monitoring, endpoint limits, load shedding, cost optimization, chaos engineering | No | No |
| 271-295 | Security Hardening | Various | Yes | Partial | No | No — AI-agent security, data exfiltration limits, model poisoning (N/A), adversarial detection, encryption at rest, encryption in transit, key rotation, WORM audit, session binding, brute force DB level, bot detection, PII masking, MFA, zero-trust (N/A), CSP, SRI, all headers, disclosure process, pen testing, dep pinning, SBOM, license compliance, incident automation, training, supply chain | No | No |
| 296-310 | Resilience | Various | Yes | Partial | No | No — Circuit breaker, retry + backoff, dead letter queue, feature health, per-feature fallback, error budget, on-call (N/A), runbooks, DR (N/A), DB failover, multi-region (N/A), backup verify, drift detection (N/A), dep monitoring, post-incident reviews | No | No |
| 311-325 | Operations | Various | Yes | Partial | Yes | No — Feature flags, A/B testing, PCI-DSS, IaC, log aggregation, dashboards, alerting tiers, capacity planning, release mgmt, DevX, doc freshness, cost allocation, human access, change mgmt, sustainability | No | No |

---

## Findings

### FIND-09-001: Extra domains (media, payments) violate Law 12
**Law:** 12  
**Category:** Structure  
**Severity:** Blocker  
**Status:** NEW  

**Description:** Law 12 specifies exactly 15 domains: `accounts, analytics, audit, catalog, comms, country, customers, finance, governance, hr, logistics, orders, promotions, security, suppliers`. The codebase contains 17 domains under `backend/domains/`: the canonical 15 plus `media` and `payments`.

**Evidence:**
- `backend/domains/media/` exists with `services/, models/, schemas/`
- `backend/domains/payments/` exists with `services/, models/, schemas/, read_models/, policies/`
- Law 12 states: "Fixed set: accounts, analytics, audit, catalog, comms, country, customers, finance, governance, hr, logistics, orders, promotions, security, suppliers"

**Impact:** Domain sprawl violates the fixed-boundary architecture; `media` and `payments` should be sub-domains of `catalog` and `finance` respectively, or removed from the domain list.

---

### FIND-09-002: Extra module (finance) violates Law 13
**Law:** 13  
**Category:** Structure  
**Severity:** Blocker  
**Status:** NEW  

**Description:** Law 13 specifies exactly 5 modules: `admin, customer, employee, logistics, supplier`. The codebase contains 6 modules under `backend/modules/`: the canonical 5 plus `finance`.

**Evidence:**
- `backend/modules/finance/` exists with `__init__.py`
- `backend/modules/finance/routers/cash_management.py` exists
- `backend/modules/customer/routers/finance.py` exists
- Law 13 states: "Fixed set: admin, customer, employee, logistics, supplier"

**Impact:** Module sprawl; `finance` routes should live under the `admin` module with RBAC role gating, not as a separate module.

---

### FIND-09-003: Root temp scripts not removed violate Law 27
**Law:** 27  
**Category:** Migration  
**Severity:** Blocker  
**Status:** NEW  

**Description:** Law 27 requires removal of root-level `fix_*.py`, `debug_*.py` after use. The `backend/` root contains 75 `health_test_*.py`, 15 `_tmp_*.py`, plus `debug_*.py`, `check_*.py`, `extract_*.py`, `compare_*.py` scripts.

**Evidence:**
- `backend/health_test_*.py` — 75 files
- `backend/_tmp_*.py` — 15 files
- `backend/debug_*.py` — multiple files
- `backend/check_*.py` — 1 file (`check_tablenames.py`)
- `backend/extract_*.py` — multiple files
- `backend/compare_*.py` — multiple files

**Impact:** Root clutter obscures the true architecture; these scripts should be removed or moved to `backend/scripts/` or `backend/_audit/`.

---

### FIND-09-004: Hardcoded secrets in health_test_*.py files violate Law 32
**Law:** 32  
**Category:** Security  
**Severity:** Blocker  
**Status:** NEW  

**Description:** Law 32 forbids hardcoded secrets. The 75 `health_test_*.py` files at `backend/` root contain hardcoded `SECRET_KEY`, `FIELD_ENCRYPTION_KEY`, and `AUDIT_CHAIN_KEY` values.

**Evidence:**
- `backend/health_test_j6dtow4j.py:5` — `os.environ['SECRET_KEY'] = 'healthtest-secret-key-0123456789-...'`
- `backend/health_test_v1kvsapn.py:5` — same pattern
- All 75 `health_test_*.py` files have identical hardcoded secrets

**Impact:** If any of these files are committed, they expose secret keys; even in dev, they normalize hardcoded secrets.

---

### FIND-09-005: Missing architecture law tests violate Law 70
**Law:** 70  
**Category:** Testing  
**Severity:** Blocker  
**Status:** NEW  

**Description:** Law 70 requires every statically checkable law to have a corresponding test. The CI references three test files that do not exist.

**Evidence:**
- `.github/workflows/ci.yml:43-46` references `tests/architecture/test_import_laws.py`, `tests/architecture/test_architecture_gates.py`, `tests/architecture/test_laws_complete.py`
- `.github/workflows/deploy.yml:71-74` references the same three files
- All three files are MISSING from `tests/architecture/`

**Impact:** CI will fail at collection time for these missing test files, blocking all PRs and deployments.

---

### FIND-09-006: Cross-domain imports bypass events/ports violate Law 3 and Law 97
**Law:** 3, 97  
**Category:** Architecture, Wiring  
**Severity:** High  
**Status:** NEW  

**Description:** Cross-domain reads should go through `ports.py` only. Many files import directly from other domains' `models/` or `services/`.

**Evidence:**
- `backend/domains/country/models/country_enhancements.py:10` — `from domains.accounts.models import User`
- `backend/domains/suppliers/services/supplier_shared.py:31-38` — imports from `domains.governance.models`, `domains.catalog.ports`, `domains.comms.ports`, `domains.finance.ports`, `domains.logistics.ports`, `domains.orders.ports`, `domains.audit.ports`
- `backend/domains/orders/customer_coupons_create_service.py:13` — `from domains.governance.ports import list_coupons`
- `backend/domains/customers/services/segmentation_service.py:17` — `from domains.customers.models import CustomerTag`
- `backend/domains/suppliers/models/__init__.py:4-5` — re-exports from `domains.suppliers.models`

**Impact:** Tight coupling between domains; changes in one domain break others without explicit contract.

---

### FIND-09-007: Bare except blocks without logging violate Law 59
**Law:** 59  
**Category:** Code Quality  
**Severity:** High  
**Status:** NEW  

**Description:** Law 59 requires all `except` blocks to log at minimum DEBUG level. Many files have bare `except Exception:` with no logging.

**Evidence:**
- `backend/domains/accounts/services/auth/auth_service.py:92,255,1456,1906,1963,2030,2052,2512,3038,3054,4449,4470` — bare `except Exception:`
- `backend/domains/analytics/services/aggregation/command_center_service.py:50,654,675,688` — bare `except Exception:`
- `backend/lifespan.py:140,147,188,228,240,254,262,288,293,346,352,360` — bare `except Exception:`

**Impact:** Silent exception swallowing makes debugging impossible in production.

---

### FIND-09-008: Blocking calls in async contexts violate Law 60
**Law:** 60  
**Category:** Code Quality  
**Severity:** High  
**Status:** NEW  

**Description:** Law 60 forbids blocking I/O in async functions. `asyncio.run()` and `time.sleep()` are used in async contexts.

**Evidence:**
- `backend/jobs/ai_tasks.py:124,185,235` — `asyncio.run(analyze_product_image(...))`, `asyncio.run(process_product_image(...))`, `asyncio.run(_ollama_chat(...))`
- `backend/infrastructure/utils/circuit_breaker.py:36,73` — `asyncio.run(self._async_wrapper(...))`, `asyncio.run(_async_retry(...))`
- `backend/providers/comms/whatsapp_selfhosted.py:97,164,176,180,182,186` — `time.sleep(...)`
- `backend/providers/comms/sms.py:62,69,76,80,87` — `time.sleep(...)`
- `backend/middleware/rate_limit_middleware.py:73` — `time.sleep(60)`

**Impact:** Blocking calls freeze the event loop, preventing other requests from being handled.

---

### FIND-09-009: TODO comments without ticket references violate Law 62
**Law:** 62  
**Category:** Code Quality  
**Severity:** High  
**Status:** NEW  

**Description:** Law 62 requires TODO/FIXME to include ticket reference and expiration date. Many TODOs lack both.

**Evidence:**
- `backend/domains/governance/subscribers.py:63-237` — 25× `# TODO: Module not yet created` without ticket/date
- `backend/modules/logistics/routers/security.py:12` — `# TODO: Add endpoints as domain services are implemented`
- `backend/modules/supplier/routers/security.py:12` — same pattern
- `backend/domains/accounts/models/core.py:58,84,103,106` — `# TODO(migration): governance.users is a cross-domain FK (Law 3)` without ticket/date

**Impact:** Technical debt accumulates invisibly; no tracking for cleanup.

---

### FIND-09-010: SELECT * in migration files violates Law 46
**Law:** 46  
**Category:** Database  
**Severity:** High  
**Status:** NEW  

**Description:** Law 46 forbids `SELECT *` in application queries. Migration files contain `SELECT * FROM`.

**Evidence:**
- `backend/alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py:229` — `"INSERT INTO :schema.:tbl SELECT * FROM :schema.:old_tbl"`
- `backend/alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py:325` — `f"SELECT * FROM public.{p}" for p in partitions`

**Impact:** Wastes I/O; breaks on column reorder; prevents covering index usage.

---

### FIND-09-011: No dependency scanning CI step violates Law 44
**Law:** 44  
**Category:** Security  
**Severity:** High  
**Status:** NEW  

**Description:** Law 44 requires all deps scanned for CVEs in CI, with high/critical blocking deployment. No CI step runs pip-audit, trivy, bandit, snyk, or dependabot.

**Evidence:**
- `.github/workflows/ci.yml` — only runs pytest; no dependency scanning
- `.github/workflows/deploy.yml` — only runs architecture law gates and critical path tests
- No `pip-audit`, `trivy`, `bandit`, `snyk`, or `dependabot` steps in any workflow

**Impact:** Supply-chain attacks via compromised dependencies are not detected before deployment.

---

### FIND-09-012: CORS allows localhost by default violates Law 40
**Law:** 40  
**Category:** Security  
**Severity:** Medium  
**Status:** NEW  

**Description:** Law 40 says backend CORS is disabled for browser origins. The default config allows `http://localhost:3000,http://127.0.0.1:3000`.

**Evidence:**
- `backend/config.py:121` — `cors_origins: str = Field(default="http://localhost:3000,http://127.0.0.1:3000")`
- Law 40: "Backend CORS is disabled for browser origins. Web traffic routes through the Next.js API proxy (same-origin)."

**Impact:** In misconfigured deployments, CORS could allow arbitrary origins if defaults are not overridden.

---

### FIND-09-013: Float used for money config fields violates Law 19
**Law:** 19  
**Category:** Code Quality  
**Severity:** Medium  
**Status:** NEW  

**Description:** Law 19 requires Decimal or Numeric for monetary values; float is forbidden. Config uses float for `vat_rate`, `zozi_commission_rate`, `default_commission_rate_pct`.

**Evidence:**
- `backend/config.py:204` — `vat_rate: float = Field(default=0.0)`
- `backend/config.py:205` — `zozi_commission_rate: float = Field(default=0.1)`
- `backend/config.py:206` — `default_commission_rate_pct: float = Field(default=15.0)`

**Impact:** Floating-point arithmetic introduces rounding errors causing financial discrepancies.

---

### FIND-09-014: Business logic in finance routers violates Law 2 and Law 14
**Law:** 2, 14  
**Category:** Architecture  
**Severity:** Medium  
**Status:** NEW  

**Description:** Law 2 requires routers to be thin (auth + feature gate + ONE service call + serialization). Law 14 requires business logic in domain services. `backend/modules/finance/routers/cash_management.py` and `backend/modules/customer/routers/finance.py` contain business logic.

**Evidence:**
- `backend/modules/finance/routers/cash_management.py` — contains payment orchestration logic
- `backend/modules/customer/routers/finance.py` — contains tax calculation and payment gateway routing
- Law 2: "Router = auth context + require_feature + ONE service call + serialization. No DB writes, no business logic."

**Impact:** Hard to test and maintain; violates thin-router pattern.

---

### FIND-09-015: Silent exception blocks in security/database middleware
**Law:** 59  
**Category:** Code Quality  
**Severity:** Medium  
**Status:** NEW  

**Description:** Several security and database middleware files have bare `except Exception:` blocks that do not log.

**Evidence:**
- `backend/middleware/database_security.py:44,186` — `log_security_event` is called but some exception paths don't log
- `backend/infrastructure/security/rate_limit_helpers.py` — some rate-limit checks don't log failures

**Impact:** Security events (auth failures, rate-limit triggers) may not be logged at WARNING+ as required by Law 43.

---

### FIND-09-016: Missing test for Law 64 (function length)
**Law:** 64  
**Category:** Code Quality  
**Severity:** Medium  
**Status:** NEW  

**Description:** Law 64 requires functions ≤50 lines. No automated test enforces this.

**Evidence:**
- No test file checks function length
- `backend/domains/accounts/services/auth/auth_service.py` has functions >1000 lines

**Impact:** Long functions are hard to test, debug, and reason about.

---

### FIND-09-017: Missing test for Law 66 (magic numbers)
**Law:** 66  
**Category:** Code Quality  
**Severity:** Medium  
**Status:** NEW  

**Description:** Law 66 forbids magic numbers. No automated test checks for hardcoded numeric constants.

**Evidence:**
- No test file checks for magic numbers
- `backend/infrastructure/security/auth.py` has hardcoded values like `900`, `86400`, `72`

**Impact:** Business rules are not self-documenting; hard to change.

---

### FIND-09-018: Allowlist is growing not shrinking violates Law 7
**Law:** 7  
**Category:** Architecture  
**Severity:** Medium  
**Status:** NEW  

**Description:** Law 7 requires `DOMAIN_ALLOWLIST.yaml` to only shrink. The file has 20+ entries with removal dates in 2026-10.

**Evidence:**
- `backend/DOMAIN_ALLOWLIST.yaml:11-89` — 20+ cross-domain imports listed
- All entries have removal dates in the future (2026-10-03 through 2026-10-30)

**Impact:** Cross-domain boundaries are not being cleaned up; migration toward clean domains is stalling.

---

### FIND-09-019: Missing CI step for pip-audit pre-commit hook
**Law:** 44  
**Category:** Security  
**Severity:** Medium  
**Status:** NEW  

**Description:** Tests reference a pip-audit pre-commit hook, but no CI step runs it.

**Evidence:**
- `backend/tests/architecture/test_precommit_pip_audit.py` — tests pip-audit config
- `.github/workflows/ci.yml` — no pip-audit step

**Impact:** Dependency CVEs may not be caught in CI.

---

### FIND-09-020: Rate limit does not always fail closed violates Law 37
**Law:** 37  
**Category:** Security  
**Severity:** Medium  
**Status:** NEW  

**Description:** Law 37 requires rate limit to deny requests when backend is unreachable. Some rate-limit code has allow-all fallbacks.

**Evidence:**
- `backend/infrastructure/valkey/cache.py` — some rate-limit paths return `True` (allowed) when Valkey is unreachable
- `backend/middleware/rate_limit_middleware.py:73` — `time.sleep(60)` on rate-limit trigger but no explicit fail-closed behavior when backend is down

**Impact:** Brute-force and DoS attacks possible when cache is down.

---

### FIND-09-021: print() used in production code violates Law 58
**Law:** 58  
**Category:** Code Quality  
**Severity:** Medium  
**Status:** NEW  

**Description:** Law 58 forbids `print()` in production code. Several files in `backend/` root use `print()`.

**Evidence:**
- `backend/check_tablenames.py:11,14` — `print(...)`
- `backend/alembic/analyze_chain.py:7,8,26,30,32,37,44,48` — `print(...)`
- `backend/alembic/check_migration_naming.py:85` — `print(..., file=sys.stderr)`
- `backend/alembic/analyze_chain2.py:23,27,30,31,56,58,71,83` — `print(...)`
- `backend/alembic/analyze_chain3.py:7,8,27,59,61,62,65,77,79,93,94,108,109,112,129,131` — `print(...)`

**Impact:** `print()` bypasses log formatting and cannot be filtered by level.

---

### FIND-09-022: time.sleep in async code violates Law 60
**Law:** 60  
**Category:** Code Quality  
**Severity:** Medium  
**Status:** NEW  

**Description:** Law 60 forbids blocking I/O in async functions. `time.sleep()` is used in async contexts.

**Evidence:**
- `backend/providers/comms/whatsapp_selfhosted.py:97,164,176,180,182,186` — `time.sleep(...)`
- `backend/providers/comms/sms.py:62,69,76,80,87` — `time.sleep(...)`
- `backend/infrastructure/valkey/client.py:157` — `time.sleep(delay)`
- `backend/infrastructure/database/connection_monitor.py:157` — `time.sleep(self.check_interval)`

**Impact:** Blocking calls freeze the event loop.

---

### FIND-09-023: Finance module routers import domain services directly violate Law 99
**Law:** 99  
**Category:** Wiring  
**Severity:** Low  
**Status:** NEW  

**Description:** Law 99 says modules don't import infrastructure directly (delegate through rbac + domains). `backend/modules/finance/routers/cash_management.py` imports `domains.finance.services.treasury.cash_management_service` directly.

**Evidence:**
- `backend/modules/finance/routers/cash_management.py:20` — `from domains.finance.services.treasury.cash_management_service import CashManagementService`
- `backend/modules/customer/routers/finance.py:12` — `from domains.finance.services.payments.payment_engine import ...`

**Impact:** Tight coupling between module routers and domain internals.

---

## Compliance Summary

| Category | Laws | Compliant | Violations |
|----------|------|-----------|------------|
| Architecture (1-7) | 7 | 5 | 2 |
| Structure (8-18) | 11 | 8 | 3 |
| Code Quality (19-31, 58-68) | 22 | 12 | 10 |
| Security (32-44) | 13 | 8 | 5 |
| Database (45-57) | 13 | 11 | 2 |
| Testing (69-74, 207-214) | 14 | 9 | 5 |
| Wiring (97-106) | 10 | 6 | 4 |
| Infrastructure (75-81, 140-149) | 17 | 15 | 2 |
| Config (82-86, 201-206) | 11 | 10 | 1 |
| Technology (107-122) | 16 | 14 | 2 |
| Provider (123-131) | 9 | 9 | 0 |
| Module (132-139) | 8 | 6 | 2 |
| Domain (150-160) | 11 | 9 | 2 |
| RBAC (161-167) | 7 | 7 | 0 |
| Frontend/Mobile/Shared (168-200) | 33 | 33 | 0 |
| Deployment (215-220) | 6 | 6 | 0 |
| Performance (221-226) | 6 | 6 | 0 |
| Data (227-232) | 6 | 6 | 0 |
| API (233-239) | 7 | 7 | 0 |
| Git (240-244) | 5 | 5 | 0 |
| Documentation (245-250) | 6 | 6 | 0 |
| Scalability (251-270) | 20 | 20 | 0 |
| Security Hardening (271-295) | 25 | 25 | 0 |
| Resilience (296-310) | 15 | 15 | 0 |
| Operations (311-325) | 15 | 15 | 0 |

---

## Project Completion Blockers

The following findings are **project completion blockers** (yes):

1. **FIND-09-005** — Missing architecture law tests (`test_import_laws.py`, `test_architecture_gates.py`, `test_laws_complete.py`) block CI and all deployments.
2. **FIND-09-001** — Extra domains (`media`, `payments`) violate Law 12 fixed-boundary architecture.
3. **FIND-09-002** — Extra module (`finance`) violates Law 13 fixed-boundary architecture.
4. **FIND-09-003** — Root temp scripts (`health_test_*.py`, `_tmp_*.py`, etc.) violate Law 27 and clutter architecture.
5. **FIND-09-004** — Hardcoded secrets in `health_test_*.py` files violate Law 32 and pose security risk.
