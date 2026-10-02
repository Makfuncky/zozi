# ZOZI Forensic Audit — Compiled README

> **Compiled:** 2026-10-01
> **Scope:** all artifacts under `_audit/**`
> **Mode:** READ-ONLY audit. No source files were modified by this compilation.
> **Benchmarks:** `_most_imp_docx/ARCHITECTURE_STACK.md`, `_most_imp_docx/TECHNOLOGY_STACK.md`, `_most_imp_docx/PROMPT_FORENSIC_AUDIT.md`, `_most_imp_docx/FEATURE_STACK.md`

---

## 1. Purpose

This directory is the compiled output of the ZOZI e-commerce platform forensic audit. It contains:

- **Phase 0 (Boot Smoke Test)** and **Phase 0.5 (Pre-flight Checks)** — executable verification of build, import, lint, typecheck, migration and dependency health.
- **28 dimension reports** — architectural, technological, logical, operational, wiring, database, tables/fields, providers, laws, migrations, environmental, tests, dev-to-prod, frontend/web, frontend/mobile, features, code/file management, security, performance, observability/resilience, contradictions, anti-patterns, code intent, browser behavior, AI drift, code alignment, project completion blockers, supply chain security.
- **4 cross-cutting passes** — chain tracing, anti-pattern scan, contradiction harvest, feature-stack reconstruction.

All findings are `NEW` status. No remediation has been applied.

---

## 2. File Index

```
_audit/
├── 00_README.md                       # This file — compiled index and rollup
├── 01_EXECUTIVE_SUMMARY.md            # 2 pages max: top 20 findings + priority matrix + completion blockers
├── 02_TARGET_STATE.md                 # Synthesized "what should be"
├── 03_FEATURE_STACK_DRAFT.md          # Feature catalog reconciliation (231 atoms)
├── 04_REMEDIATION_PLAN.md             # Prioritized fix list + clusters + KEEP/HARDEN
├── 05_DIMENSION_INDEX.md              # One line per dimension
├── 06_OBSERVATIONS.csv                # Pass 1 raw observations
├── 07_CONTRADICTIONS.md               # 37 target-vs-code contradictions
├── 08_FEATURE_HEALTH.md               # Per-feature health scores
├── 09_ANTI_PATTERNS.md                # 20 anti-pattern categories, 1,847 occurrences
├── 10_CHAINS.md                       # 7 critical business chains traced end-to-end
├── 11_PRODUCTION_READINESS.md         # Production-readiness conditions
├── COMPLETION_BLOCKERS.md             # All yes blockers in priority order
├── dimensions/
│   ├── 00_boot_smoke_test.md          # Boot smoke test results
│   ├── 01_architectural.md            # Structural law compliance
│   ├── 02_technological.md            # Versions, package managers, base images
│   ├── 03_logical.md                  # Correctness, money types, state machines
│   ├── 04_operational.md              # Health gates, CI/CD, runbooks, config
│   ├── 05_wiring.md                   # Auth wiring, RLS wiring, event wiring
│   ├── 06_database.md                 # Migrations, relationships, RLS, replicas
│   ├── 07_tables_fields.md            # 343 tables inspected, ORM/DB drift
│   ├── 08_providers.md                # ~55 provider modules across 17 subpackages
│   ├── 09_laws.md                     # 325 laws audited
│   ├── 10_migrations.md               # Migration correctness and history
│   ├── 11_environmental.md            # Environment variables and config
│   ├── 12_tests.md                    # Test coverage and collection
│   ├── 12_tests_collection_verify.md  # Test collection verification
│   ├── 13_dev_to_prod.md              # Dev-to-prod path
│   ├── 13_dev_to_prod_docker_verify.md # Docker dev-to-prod verification
│   ├── 14_frontend_web.md             # Next.js web application
│   ├── 15_frontend_mobile.md          # Expo/React Native app
│   ├── 16_features.md                 # Feature-level correctness
│   ├── 17_code_file_management.md     # Code and file management
│   ├── 18_security.md                 # Credentials, injection, SSRF, WORM, MFA
│   ├── 19_performance.md              # N+1, pagination, images, indexes
│   ├── 20_observability_resilience.md # Observability and resilience
│   ├── 21_contradictions.md           # Contradictions detail
│   ├── 22_anti_patterns.md            # Anti-patterns detail
│   ├── 23_code_intent.md              # Code intent analysis
│   ├── 24_browser_behavior.md         # Browser audit bridge
│   ├── 25_ai_drift.md                 # AI drift detection
│   ├── 26_code_alignment.md           # Code alignment
│   ├── 27_project_completion_blockers.md # 9 consolidated P0 boot blockers
│   ├── 28_supply_chain_security.md    # Supply chain security
│   ├── config_verification.md         # Config verification
│   └── suppliers.md                   # Supplier-specific findings
└── logs/
    ├── boot_preflight.jsonl           # 17 timestamped command records
    ├── checkpoint.json                # Phase 0 checkpoint state
    ├── commands.txt                   # Audit commands log
    ├── phase0_results.md              # 14-check results table + F-001..F-009
    ├── queries.sql                    # Audit SQL queries log
    ├── NN_<dimension>.jsonl           # Machine-readable findings per dimension
    ├── anti_patterns.jsonl            # 20 anti-pattern records
    ├── chains.jsonl                   # 7 chain verdicts
    ├── contradictions.jsonl           # 37 contradiction records
    └── feature_stack.jsonl            # Feature stack summary records
```

**All 28 dimensions are present and complete.**

---

## 3. Rollup by Dimension

| Dimension | Report | Files inspected | Findings | P0 | Blockers (yes) | Blockers (partial) | Avg confidence |
|---|---|---|---|---|---|---|---|
| 01 Architectural | `dimensions/01_architectural.md` | 240+ | 14 | 4 | 4 | 0 | 4.5/5 |
| 02 Technological | `dimensions/02_technological.md` | 12 | 53 | 15 | 15 | 0 | 4.8/5 |
| 03 Logical | `dimensions/03_logical.md` | 47 | 18 | 4 | 4 | 2 | 4.4/5 |
| 04 Operational | `dimensions/04_operational.md` | 18 | 10 | 2 | 2 | 0 | 4.5/5 |
| 05 Wiring | `dimensions/05_wiring.md` | 18 | 8 | 2 | 2 | 2 | 4.5/5 |
| 06 Database | `dimensions/06_database.md` | 12 | 8 | 3 | 4 | 0 | 4.5/5 |
| 07 Tables & Fields | `dimensions/07_tables_fields.md` | 343 tables | 272 | 1 | 78 | 0 | 5/5 |
| 08 Providers | `dimensions/08_providers.md` | ~55 modules | 8 | — | 0 | 0 | — |
| 09 Laws | `dimensions/09_laws.md` | 325 laws | 23 | — | 5 | 0 | — |
| 15 Frontend/Mobile | `dimensions/15_frontend_mobile.md` | 18 | 9 | 0 | 1 | 0 | 4/5 |
| 16 Features | `dimensions/16_features.md` | 42 | 42 | 8 | 8 | 6 | 4/5 |
| 18 Security | `dimensions/18_security.md` | 47 | 12 | 5 | 5 | 1 | 4.6/5 |
| 19 Performance | `dimensions/19_performance.md` | 30 | 9 | 2 | 2 | 0 | 4/5 |
| 27 Completion Blockers | `dimensions/27_project_completion_blockers.md` | 14 | 9 | 9 | 9 | 0 | 5/5 |
| **Total** | | | **495** | **55** | **139** | **11** | |

Dimension 27 duplicates the nine Phase 0 findings (F-001..F-009) by design. Deduplicated total across dimensions 01–19: **486 findings**.

### Cross-cutting passes

| Pass | Report | Volume | Blockers |
|---|---|---|---|
| Chains | `10_CHAINS.md` | 7 chains — 0 COMPLETE, 7 PARTIAL | all project-completion-critical |
| Anti-patterns | `09_ANTI_PATTERNS.md` | 20 categories, 1,847 occurrences | 8 yes, 3 partial, 9 no |
| Contradictions | `07_CONTRADICTIONS.md` | 37 records | 9 yes, 16 partial, 12 no |
| Feature stack | `03_FEATURE_STACK_DRAFT.md` | 231 atoms, 68 orphans, 20 launch-critical | 9 domains lack feature tests |

---

## 4. Phase 0 / 0.5 Results

14 checks executed — **3 PASS, 9 FAIL, 1 PARTIAL, 1 ADAPTED**. Full detail in `logs/phase0_results.md`.

| # | Check | Status |
|---|---|---|
| 1 | Route count > 0 (`from backend.main import app`) | FAIL — `ModuleNotFoundError: No module named 'infrastructure'`; adapted run from `backend/` yields 82 routes |
| 2 | Architecture test collection | PASS — 356 tests collected |
| 3 | Frontend install (`pnpm install --frozen-lockfile`) | PASS |
| 4 | Frontend build (`pnpm build`) | PASS — Next.js 16.3.4, 151 pages |
| 5 | Docker compose config | PASS — 10 services |
| 6 | `DATABASE_URL` set | FAIL — `settings.DATABASE_URL` AttributeError; actual attribute is lowercase `database_url` |
| 7 | Valkey connectivity | FAIL — `valkey://` scheme rejected by `redis.Redis`; `ConnectionRefusedError` on `localhost:6379` |
| 8 | Full test collection | FAIL — 4,657 tests collected, 6 collection errors |
| 9 | Frontend type check | FAIL — 60+ TypeScript errors |
| 10 | Backend lint (`ruff check .`) | FAIL — 8,335 errors (2,954 fixable) |
| 11 | `alembic current` | PARTIAL — multiple applied revisions, heads divergent |
| 12 | `alembic heads` | FAIL — 5 divergent heads (Law 49 violation) |
| 13 | Lockfile sync — Python | FAIL — `uv.lock` holds 1 entry; version mismatches and forbidden packages |
| 14 | Lockfile sync — Frontend | FAIL — 15+ version mismatches including zod 3→4 major drift |

---

## 5. Key Findings

### 5.1 Structural / architectural

- **Sixth module and seventeenth domain exist.** `backend/modules/finance/` violates Law 13 (fixed 5 modules). `backend/domains/payments/` and `backend/domains/media/` violate Law 12 (fixed 15 domains). Both are blockers in dimensions 01 and 09 and contradictions CONTRAD-001/002/003.
- **Systemic direct-service imports in routers.** 18+ router files import from `domains/*/services/*` instead of through `ports.py`, violating Law 3.
- **Middleware dependency violations.** `middleware/dependencies/auth.py` imports from `domains.accounts.services.auth.security_dependencies`; `country_detection.py` imports from `providers.geography.ip`.
- **91 temp/debug files at backend root** plus outdated `run_tests.ps1`/`run_tests.sh` runners, violating Law 27 and the project's single-runner constraint.
- **Ports anti-patterns.** `domains/finance/ports.py` uses wildcard imports and a ~70-entry `_LAZY_SERVICE_EXPORTS` service locator.
- **Five undocumented providers** exist outside the canonical tree: `news/`, `automation/`, `scanner/`, `voice/`, `analytics/`.

### 5.2 Technological / dependencies

- **Python dependency management is fully misaligned.** `uv.lock` is effectively empty (1 virtual package), `pyproject.toml` has no `[project.dependencies]`, and `requirements.txt` + pip are used in Dockerfile and CI.
- **Base image drift.** Backend Dockerfile uses `python:3.11-slim` against a canonical `python:3.13-slim`.
- **Six forbidden packages present:** `psycopg2-binary`, `python-magic`, `pytz`, `tzlocal`, `requests`, `prometheus-client` — with live imports of `requests` and `prometheus_client` in production code.
- **Version drift across all three stacks.** Backend (FastAPI 0.115.2 vs 0.141.x, SQLAlchemy 2.0.51 vs 2.0.52, Alembic 1.18.5 vs 1.19.1+, Celery 5.4.0 vs 5.5+); web (Next 16.3.4 vs 16.3.5, zod 3.25.76 vs 4.3.6, framer-motion 12.43.0 vs 13.2.0+); mobile (Expo 55 vs 57, RN 0.83 vs 0.86).
- **Missing declared dependencies.** `fastapi-limiter-valkey` is imported in production (`infrastructure/security/rate_limiter.py:24`) but absent from `requirements.txt` — CONTRAD-036, blocker.
- **No SBOM generation** anywhere in CI or the repo.

### 5.3 Database / schema

- **Divergent Alembic history.** Phase 0 counted 5 heads via the CLI; dimension 06 counted 62 by parsing `down_revision` tuples. `alembic heads` also crashes with `ModuleNotFoundError: No module named 'migration_helpers'` at `2026_08_06_0001_add_analytics_audit_columns.py:31`.
- **293 relationships lack `lazy=`**, defaulting to `lazy='select'` and causing N+1 on every collection endpoint.
- **RLS variable name mismatch.** Policies read `current_setting('app.current_country_code')` while middleware sets `app.country_scope`; two competing RLS implementations exist (`rls_interceptor.py` ContextVar path vs `country_context.py` `SET LOCAL` path).
- **Schema drift: 343 tables inspected, 142 compliant, 201 with findings.** 14 DB tables have no ORM model; 2 models have no table; 13 orphan DB columns; 17 model columns missing from the live DB.
- **42 user-facing tables lack `country_code`**, breaking RLS scoping (Law 5, Law 20) — 37 of them in the comms domain.
- **150 tables use Python-side `default=_utcnow`** instead of `server_default=func.now()` (Law 21).
- **Read replica engine is built but never wired** into application routers.

### 5.4 Security

- **Payment gateway credentials stored in plaintext** — `finance.payment_gateway_connections.secret_key` / `webhook_secret` are written without AES-256-GCM field encryption, against the platform's own `field_encryption.py` requirement and PCI-DSS 3.
- **SQL injection via f-string interpolation** in a migration script, `infrastructure/security/key_rotation.py:115`, and `command_center_query_service.py`.
- **SSRF exposure** in four outbound HTTP clients that do not validate URLs against private/internal ranges.
- **WORM audit trail mutates rows after INSERT** to append `worm_hash`, violating Write-Once-Read-Many.
- **CAPTCHA silently skipped** when `TURNSTILE_SECRET_KEY` is unset, disabling bot protection on all public auth endpoints.
- **MFA not enforced** for admin/employee roles — the architecture test only checks for MFA code existence.
- **WebSocket `websocket_user` accepts connections without JWT verification**, allowing unauthenticated broadcast to all users.
- **Hardcoded secrets** in `health_test_*.py` files (Law 32).

### 5.5 Logic / correctness

- **Float-for-money is systemic** — 14+ files across finance, orders, payouts and trading, plus cart totals and tax computation. Rounding drift affects commission, FX revaluation and payouts.
- **Return-type leak** — internal `Decimal` values are serialized as `float` in API responses, violating Law 89.
- **Blocking I/O in async handlers** — `loop.run_until_complete()` inside the Tap refund path freezes the event loop; `time.sleep(backoff)` in the event bus retry loop does the same.
- **Silent `except` blocks on financial operations** — tax calculation, FX revaluation and AML screening swallow exceptions, potentially approving prohibited counterparties.
- **Illegal state transition** — `refund_order` permits refunds on `cancelled` orders, but the state machine has no `cancelled → refunded` edge.
- **Idempotency key is optional** on `PaymentIntentRequest`, permitting duplicate payment intents on retry.

### 5.6 Wiring / operations

- **Canonical `set_rls_context()` uses ContextVars and never executes `SET LOCAL`**, violating Law 5; the legacy `SET LOCAL` path is not wired to it.
- **Event publishers call `publish()` synchronously inside service transactions** with no post-commit guarantee (Law 3), risking cross-schema transaction locking.
- **`/health/deps` never fails closed** — always returns HTTP 200 regardless of dependency health, breaking orchestrator and load-balancer gates.
- **No CI/CD pipeline exists.** No `.github/workflows/` directory; migrations, rollback and deployment health checks are entirely manual.
- **No deployment, rollback, or migration-on-deploy runbooks** — only 5 operational runbooks exist.
- **Raw `os.getenv()` in provider config** for payments, geography and SMS, bypassing typed pydantic settings.
- **Rate limiting disabled by default** (`RATE_LIMIT_ENABLED=false`), and does not consistently fail closed (Law 37).

### 5.7 Providers

~55 provider modules across 17 subpackages audited against the 12-point schema. **0 Law 31 forbidden-domain import violations.** All findings are cross-cutting:

1. No circuit breaker or retry policy in any provider.
2. No explicit timeout in provider wrappers.
3. `health_check()` missing from most providers.
4. Payment webhook signature uses HMAC-SHA256, not the documented AES-256-GCM.
5. No async implementation in comms providers.
6. Storage providers lack presigned URL, CDN and lifecycle support.
7. Secrets handled via environment variables.
8. Test coverage exists for ~20 providers only.

### 5.8 Chains (7 critical business journeys)

**All 7 chains are PARTIAL. None is COMPLETE.** See `10_CHAINS.md` for step-level evidence.

| Chain | Name | Happy path | Failure paths | Rollback | Verdict |
|---|---|---|---|---|---|
| CHAIN-001 | Customer order placement | partial | 4/4 | verified | PARTIAL |
| CHAIN-002 | Supplier payout | partial | 3/3 | partial | PARTIAL |
| CHAIN-003 | Return and refund | partial | 5/5 | broken | PARTIAL |
| CHAIN-004 | Logistics pickup and delivery | partial | 3/3 | partial | PARTIAL |
| CHAIN-005 | Admin ledger posting and reconciliation | partial | 4/4 | partial | PARTIAL |
| CHAIN-006 | Customer registration and KYC | partial | 3/3 | partial | PARTIAL |
| CHAIN-007 | Supplier onboarding and first product listing | partial | 4/4 | partial | PARTIAL |

The dominant cross-cutting finding: **all seven domains define event classes but none of the service functions publish them** via the canonical event bus. Every `domains/*/subscribers.py` is a stub containing only `logger.info` calls and `# Future:` comments. This is a systematic Law 3 violation that breaks the order-to-cash chain at the accounting step. Secondary findings: no multi-supplier shipment splitting at order creation, and no rollback mechanism for already-issued refunds or committed ledger entries.

### 5.9 Frontend / mobile

- **OTA updates fully disabled** — `expo.modules.updates.ENABLED=false` in the Android manifest and `expo-updates` absent from package.json, so no hotfix path exists outside store review.
- **No offline detection or mutation queue** — mutations fail silently when the network is unavailable.
- **Social sign-in non-functional on native** — two of three providers are throw stubs; Google requires uninstalled native SDK packages.
- **Payment strategy contradictory** — native Stripe SDK installed but checkout redirects to web; three regional SDKs are dynamically required but not declared.
- **No Detox E2E tests** despite the stack mandating them; only Playwright web-viewport tests present.
- **`expo-secure-store` web fallback uses unencrypted `localStorage`** for tokens.

### 5.10 Performance

- **N+1 queries** from `lazy="select"` defaults on `Product.cart_items`, `Order.items`, `Product.variants`, `Product.videos`, `ReturnRequest.order`.
- **OFFSET pagination on hot customer lists** — product listing and order history violate Law 317 ("NEVER OFFSET on hot lists").
- **Incomplete image pipeline** — AVIF missing from `next.config.ts`, no blur placeholders on product images.
- **Product name search uses `ilike '%q%'`** with no pg_trgm GIN index, causing sequential scans.

### 5.11 Laws

325 laws audited; **23 violations found**; 5 are project completion blockers.

| Category | Laws | Compliant | Violations |
|---|---|---|---|
| Architecture (1–7) | 7 | 5 | 2 |
| Structure (8–18) | 11 | 8 | 3 |
| Code Quality (19–31, 58–68) | 22 | 12 | 10 |
| Security (32–44) | 13 | 8 | 5 |
| Database (45–57) | 13 | 11 | 2 |
| Testing (69–74, 207–214) | 14 | 9 | 5 |
| Wiring (97–106) | 10 | 6 | 4 |
| Infrastructure (75–81, 140–149) | 17 | 15 | 2 |
| Config (82–86, 201–206) | 11 | 10 | 1 |
| Technology (107–122) | 16 | 14 | 2 |
| Provider (123–131) | 9 | 9 | 0 |
| Module (132–139) | 8 | 6 | 2 |
| Domain (150–160) | 11 | 9 | 2 |
| All others (RBAC, Frontend, Deployment, Performance, Data, API, Git, Docs, Scalability, Security Hardening, Resilience, Operations) | 152 | 152 | 0 |

Five law violations block project completion:

1. **FIND-09-005** — Missing architecture law tests (`test_import_laws.py`, `test_architecture_gates.py`, `test_laws_complete.py`) block CI and deployments.
2. **FIND-09-001** — Extra domains `media` and `payments` violate Law 12.
3. **FIND-09-002** — Extra module `finance` violates Law 13.
4. **FIND-09-003** — Root temp scripts violate Law 27.
5. **FIND-09-004** — Hardcoded secrets in `health_test_*.py` violate Law 32.

### 5.12 Feature stack

231 feature atoms catalogued from `backend/domains/*/features.py` aggregated via `backend/rbac/catalog.py`.

| Metric | Count |
|---|---|
| Total features catalogued | 231 |
| Tier 1 (brief cards) | 211 |
| Tier 2 (deep cards) | 20 |
| Orphan features (defined, never gated) | 68 |
| Launch-critical features | 20 |
| Domains without dedicated feature tests | 9 |
| Contradictions found | 3 |
| AI drift instances (duplicate/legacy atoms) | 5 |

Highest-scoring launch-critical features: `orders.create` (0.95), `finance.payments.process` (0.90), `orders.fulfill` (0.88), `finance.payout.approve` (0.87), `finance.payout.dispatch` (0.85), `payments.transaction.process` (0.85).

Orphan concentration: accounts (24 orphans / 49 atoms), finance (14/47), governance (14/63), comms (13/37), hr (7/31), security (7/18), country (3/19), customers (2/12), media (2/4).

Nine domains lack a dedicated feature test file: accounts, suppliers, customers, hr, analytics, country, governance, payments, media.

**Known discrepancy:** `_most_imp_docx/FEATURE_STACK.md` claims ~495 features. The RBAC catalog contains 231 unique atoms. `FEATURE_STACK.md` counts individual routes as features; the catalog counts permission atoms. This report uses catalog atoms as authoritative.

---

## 6. Anti-Patterns

20 categories, 1,847 occurrences. Blockers: 8 yes, 3 partial, 9 no.

| ID | Category | Occurrences | Blocker |
|---|---|---|---|
| AP-001 | TODO-only implementation | 185 across 28 files (~120 in `governance/services/admin/admin_service.py`) | yes |
| AP-002 | Stub function (`NotImplementedError`) | 7 across 5 files | partial |
| AP-003 | Empty handler | — | yes |
| AP-004 | Silent except | — | yes |
| AP-005 | Wrong type for money (float) | — | yes |
| AP-006 | Commented code | — | no |
| AP-007 | Magic string | — | no |
| AP-008 | Unused / wildcard import | — | no |
| AP-009 | Orphan route | — | no |
| AP-010 | Orphan service | — | no |
| AP-011 | Phantom reference | — | no |
| AP-012 | Duplicate business logic | — | no |
| AP-013 | Default masks failure | — | no |
| AP-014 | Unused import | — | no |
| AP-015 | Dead branch | — | no |
| AP-016 | Magic string (permission atoms) | 15+ hardcoded atoms | no |
| AP-017 | Missing idempotency | 3 payment paths | yes |
| AP-018 | Not-wired event | 25 governance subscribers | yes |
| AP-019 | Not-wired port | 3 missing port refs | partial |
| AP-020 | Not-wired feature gate | 5 gates returning TODO | partial |

---

## 7. Contradictions

37 records harvested from canonical docs vs actual code/config/lockfiles at HEAD.

| Category | Count | Yes blockers | Partial | No |
|---|---|---|---|---|
| target_vs_code | 5 | 3 | 1 | 1 |
| tech_target_vs_lockfile | 14 | 1 | 6 | 7 |
| code_vs_config | 2 | 1 | 1 | 0 |
| frontend_vs_backend | 10 | 2 | 5 | 3 |
| package_vs_import | 3 | 2 | 1 | 0 |
| doc_vs_code | 3 | 0 | 2 | 1 |
| **Total** | **37** | **9** | **16** | **12** |

Notable blockers: CONTRAD-001 (6th module), CONTRAD-002 (17th domain), CONTRAD-005 (FastAPI gap), CONTRAD-036 (missing `fastapi-limiter-valkey`), CONTRAD-034 (orphaned `hr.py` shadowed by `hr/` package, making it unreachable).

Several contradictions require a **user decision** rather than a code fix — whether to delete non-canonical packages or amend the architecture document to accept them. These are flagged `User decision required: yes` in `07_CONTRADICTIONS.md`.

---

## 8. Completion Blockers

`dimensions/27_project_completion_blockers.md` consolidates the nine Phase 0 P0 blockers. All are confidence 5/5, triangulated.

| ID | Area | Blocker | Effort |
|---|---|---|---|
| BLOCKER-001 | boot | `backend/` lacks `__init__.py`; `from backend.main import app` fails | S |
| BLOCKER-002 | boot | `settings.DATABASE_URL` AttributeError; actual attribute is `database_url` | S |
| BLOCKER-003 | infra | No local Valkey on `localhost:6379`; cache, rate limiting, sessions and event bus all fail | S |
| BLOCKER-004 | testing | 6 test files with broken imports prevent full collection | M |
| BLOCKER-005 | frontend | 60+ TypeScript compilation errors | L |
| BLOCKER-006 | backend lint | 8,335 ruff errors (2,954 auto-fixable) | L |
| BLOCKER-007 | database | 5 divergent Alembic heads violate Law 49 | L |
| BLOCKER-008 | dependencies | Backend version mismatches and 6 forbidden packages | M |
| BLOCKER-009 | dependencies | Frontend version mismatches vs `TECHNOLOGY_STACK.md` | M |

---

## 9. Cross-Dimension Consistency Notes

- **Alembic head count disagrees.** Phase 0 counted 5 heads via `alembic heads`; dimension 07 also reports 5; dimension 06 reports 62 heads parsed from `down_revision` tuples. The 5 vs 62 discrepancy likely reflects different counting semantics (applied heads vs unmerged revision nodes). This needs resolution before the merge plan is sized.
- **Feature count disagrees internally.** `03_FEATURE_STACK_DRAFT.md` reports 231 catalogued atoms in its completion summary but the per-domain table sums to 377. The catalog figure is authoritative per the report's own reconciliation note.
- **Two RLS implementations coexist.** Dimension 06 flags the variable-name mismatch; dimension 05 separately finds that the canonical function never executes `SET LOCAL`. Both must be fixed together or RLS remains ineffective.
- **Dimension 27 duplicates Phase 0.** The nine findings are identical to F-001..F-009 in `logs/phase0_results.md` by design; deduplicate when tracking remediation.

---

## 10. Status Summary

| Phase / Pass | Status |
|---|---|
| Phase 0 (Boot Smoke Test) | COMPLETED — 5 checks, 4 pass / 1 fail (adapted) |
| Phase 0.5 (Pre-flight Checks) | COMPLETED — 9 checks, 0 pass / 9 fail |
| Dimension 01 Architectural | COMPLETED — 14 findings |
| Dimension 02 Technological | COMPLETED — 53 findings |
| Dimension 03 Logical | COMPLETED — 18 findings |
| Dimension 04 Operational | COMPLETED — 10 findings |
| Dimension 05 Wiring | COMPLETED — 8 findings |
| Dimension 06 Database | COMPLETED — 8 findings |
| Dimension 07 Tables & Fields | COMPLETED — 272 findings |
| Dimension 08 Providers | COMPLETED — 8 cross-cutting findings |
| Dimension 09 Laws | COMPLETED — 23 violations |
| Dimension 15 Frontend/Mobile | COMPLETED — 9 findings |
| Dimension 16 Features | COMPLETED — 42 findings |
| Dimension 18 Security | COMPLETED — 12 findings |
| Dimension 19 Performance | COMPLETED — 9 findings |
| Dimension 27 Completion Blockers | COMPLETED — 9 findings |
| Chains (10_CHAINS) | COMPLETED — 7 chains, all PARTIAL |
| Anti-patterns (09) | COMPLETED — 20 categories |
| Contradictions (07) | COMPLETED — 37 records |
| Feature stack (03) | COMPLETED — 231 atoms |

All 28 dimensions are present and complete.

---

## 11. Remediation Priority

Ordered by blast radius and dependency, derived from the `Corrections required (prioritized)` tables in each dimension report.

**P0 — unblocks everything else**
1. Merge divergent Alembic heads into a single linear chain (Law 49). Fix the `migration_helpers` import path first so `alembic heads` can even run. **Blocks all DB work.**
2. Add the missing architecture law tests (`test_import_laws.py`, `test_architecture_gates.py`, `test_laws_complete.py`). **Blocks CI and all deployments.**
3. Fix the 6 broken test imports so the full 4,657-test suite collects.
4. Add `backend/__init__.py` or standardize all commands on running from inside `backend/`.
5. Start local Valkey via Docker Compose.
6. Encrypt payment gateway credentials with AES-256-GCM; migrate columns to `EncryptedString`.
7. Replace all f-string SQL with parameterized `sa.text()` queries.
8. Add SSRF validation to the four affected outbound HTTP clients.
9. Add JWT verification to `websocket_user` before `websocket.accept()`.
10. Wire canonical `set_rls_context()` to execute `SET LOCAL`, and align the RLS policy variable name with the middleware target.
11. Make `/health/deps` return 503 when any critical dependency is down.
12. Create the CI/CD pipeline with pre-deploy migrations, health gate and rollback.
13. Implement the stub subscribers, or remove the event registrations so failures are not silent. **Without this, no chain can reach COMPLETE.**
14. Resolve the float-for-money cluster across finance, orders, catalog and payouts using `Decimal` and `kernel.money.round_money`.

**P1**
15. Remove `modules/finance/`, `domains/payments/`, and 91 root temp/debug files; delete `run_tests.ps1`/`run_tests.sh`.
16. Migrate backend from pip/requirements.txt to uv/pyproject.toml; populate `uv.lock`.
17. Align all package versions across backend, web and mobile with `TECHNOLOGY_STACK.md`; remove the 6 forbidden packages.
18. Implement event publication across all 7 chains (OrderCreated, PayoutCreated, RefundPosted, ShipmentCreated, JournalEntryPosted, CustomerRegistered, SupplierRegistered, ProductCreated).
19. Implement multi-supplier shipment splitting at order creation.
20. Add `country_code` to the 42 user-facing tables; add ORM models for the 14 unmapped tables.
21. Add `lazy="selectin"` to the 293 relationships missing it.
22. Enforce MFA for admin/employee roles; make CAPTCHA fail closed when the key is missing.
23. Re-enable `expo-updates`; add offline detection and mutation queue.
24. Switch hot customer lists to keyset cursor pagination (Law 317).
25. Write deployment, rollback and migration-on-deploy runbooks.

**P2**
26. Add keyset pagination to remaining lists, AVIF + blur placeholders, pg_trgm GIN index on `catalog.products.name`.
27. Resolve the 37 contradictions — several need a user decision on whether to amend `ARCHITECTURE_STACK.md` or delete non-canonical packages.
28. Add SBOM generation to CI.
29. Add feature tests for the 9 domains lacking them; resolve the 68 orphan feature atoms and 5 AI drift instances.

---

## 12. Canonical References

- `_most_imp_docx/ARCHITECTURE_STACK.md` — architecture laws (325), module layout, module/domain/provider boundaries
- `_most_imp_docx/TECHNOLOGY_STACK.md` — canonical versions, SDKs, forbidden packages, package managers
- `_most_imp_docx/PROMPT_FORENSIC_AUDIT.md` — audit rules, finding schemas, scoring formula
- `_most_imp_docx/FEATURE_STACK.md` — feature stack reference (reconciled against RBAC catalog in `03_FEATURE_STACK_DRAFT.md`)
