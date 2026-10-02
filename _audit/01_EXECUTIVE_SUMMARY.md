# ZOZI Forensic Audit — Executive Summary

**Compiled:** 2026-10-01  
**Scope:** all artifacts under `_audit/**`  
**Mode:** READ-ONLY audit — no source files were modified  

---

## 1. VERDICT

**NOT PRODUCTION READY.**

The platform is **feature-rich and structurally sound at the file level, but functionally incomplete at the runtime level.** Every dimension auditor returned confirmation: FAIL. All 14 dimensions completed with zero remediation applied. Zero of seven critical business chains reached COMPLETE.

| Readiness dimension | Verdict | Primary evidence |
|---|---|---|
| Build & boot | FAIL | Boot smoke: 3 PASS / 2 FAIL; 2 routers silently skipped; import path broken |
| Functional correctness (business chains) | FAIL | 0 of 7 chains COMPLETE; 7 PARTIAL; 1 with broken rollback |
| Security | FAIL | 5 P0 (plaintext payment credentials, SQL injection, SSRF) |
| Money correctness | FAIL | Float-for-money systemic in 14+ files; vat_rate/commission_rate typed float |
| Data integrity / schema | FAIL | 5 Alembic heads; 293 relationships default lazy="select"; 42 tables missing country_code |
| Error handling | FAIL | 100+ silent except blocks; finance tax/FX/AML failures swallowed |
| Lazy loading / N+1 | FAIL | 293 relationships without lazy=; keyset pagination absent on hot lists |
| Operational / CI-CD | FAIL | No CI/CD pipeline; /health/deps never fails closed; no deploy/rollback runbook |
| Dependency & supply chain | FAIL | uv.lock empty; 6 forbidden packages; 53 version findings; no SBOM |
| Frontend web | PARTIAL | Build passes (151 pages) but 60+ TS errors; zod on major version 3 vs 4 |
| Mobile | FAIL | OTA updates disabled; social sign-in stubs; 0 Detox specs |
| Observability | FAIL | OpenTelemetry disabled; RLS install skipped; R2 not health-checked |
| Test suite integrity | FAIL | 4657 collected / 6 collection errors; 8335 ruff errors; 9 domains lack feature tests |

---

## 2. FINDINGS ROLL-UP BY DIMENSION

| Dimension | Files inspected | Findings | P0 | P1 | P2 | P3 | Blockers (yes) | Partial |
|---|---|---|---|---|---|---|---|---|
| 01 Architectural | 240+ | 14 | 4 | 6 | 3 | 1 | 4 | 0 |
| 02 Technological | 12 | 53 | 15 | 35 | 3 | 0 | 15 | 0 |
| 03 Logical | 47 | 18 | 4 | 6 | 5 | 3 | 4 | 2 |
| 04 Operational | 18 | 10 | 2 | 3 | 3 | 2 | 2 | 0 |
| 05 Wiring | 18 | 8 | 2 | 2 | 2 | 2 | 2 | 2 |
| 06 Database | 12 | 8 | 3 | 2 | 2 | 1 | 4 | 0 |
| 07 Tables & Fields | 343 tables | 272 | 1 | 77 | 194 | 0 | 78 | 0 |
| 08 Providers | ~55 modules | 8 (cross-cutting) | — | — | — | — | 0 | 0 |
| 09 Laws | 325 laws | 23 violations | — | — | — | — | 5 | — |
| 15 Frontend / Mobile | 18 | 9 | 0 | 2 | 4 | 3 | 1 | 0 |
| 16 Features | 42 | 42 | 8 | 14 | 12 | 8 | 8 | 6 |
| 18 Security | 47 | 12 | 5 | 4 | 2 | 1 | 5 | 1 |
| 19 Performance | 30 | 9 | 2 | 3 | 3 | 1 | 2 | 0 |
| 27 Completion Blockers | 14 | 9 | 9 | 0 | 0 | 0 | 9 | 0 |
| **Subtotal — 12 tabular dimensions** | | **464** | **55** | **154** | **233** | **22** | **134** | **11** |
| **Subtotal — non-tabular (08, 09)** | | **31** | — | — | — | — | **5** | — |
| **GRAND TOTAL** | | **495** | **55** | **154** | **233** | **22** | **139** | **11** |

Reconciliation: tabular 464 = 55 + 154 + 233 + 22 (priority) = 134 + 11 + 319 (blocker split). Non-tabular 31 = 8 (08_providers) + 23 (09_laws), which carry no P0-P3 split. Grand total 495 = 464 + 31.

### Cross-cutting artefacts (not counted above, overlapping in scope)

| Artefact | Volume | Blockers (yes) | Partial |
|---|---|---|---|
| Anti-patterns | 20 categories, 1,847 occurrences | 8 | 3 |
| Contradictions | 37 | 9 | 16 |
| Chains | 7 chains — 0 COMPLETE / 7 PARTIAL | all project-completion-critical | — |
| Feature stack | 231 feature atoms, 68 orphans | 20 launch-critical | — |
| Phase 0 boot/preflight | 14 checks, 3 PASS / 9 FAIL | 9 | — |

---

## 3. BOOT & PREFLIGHT GATE (Phase 0 / 0.5)

### What actually works

| Check | Result | Evidence |
|---|---|---|
| Architecture test collection | PASS | 356 tests collected in 4.09s |
| Frontend install | PASS | pnpm install --frozen-lockfile clean, 14.3s |
| Frontend build | PASS | Next.js 16.3.4 compiled, 13.9s, 151 static pages |
| Docker Compose config | PASS | Valid YAML, 10 services |

### Pre-flight failures (all 9 are completion blockers)

| # | Check | Failure |
|---|---|---|
| 1 | Route count | ModuleNotFoundError: No module named 'infrastructure' |
| 6 | DATABASE_URL | AttributeError: Settings has no attribute 'DATABASE_URL' |
| 7 | Valkey | ValueError on valkey:// scheme; ConnectionRefusedError on localhost:6379 |
| 8 | Test collection | 4657 collected, 6 collection errors |
| 9 | Frontend types | 60+ TypeScript errors |
| 10 | Lint | 8335 ruff errors (2954 auto-fixable) |
| 11-12 | Alembic | 5 divergent heads; alembic heads crashes with ModuleNotFoundError: migration_helpers |
| 13 | Python lockfile | uv.lock has 1 package; 6 forbidden packages; 7 version mismatches |
| 14 | Frontend lockfile | 9 version mismatches incl. zod major-version drift (3 → 4) |

### Boot degradations (not counted as failures but consequential)

| Boot warning | Production consequence |
|---|---|
| Skipping router orders | Entire orders router not mounted — order placement/history/returns unreachable |
| Skipping router logistics | Entire logistics router not mounted — shipment tracking/pickup unreachable |
| RLS policy install skipped | Row-level security not installed; country isolation unenforced |
| OpenTelemetry disabled | Distributed tracing off |
| Valkey connection timeouts | Cache, sessions, rate limiter and event bus all down |
| readiness_require_valkey AttributeError | Readiness probe itself broken |

### The 18-condition launch gate (recovered from git HEAD 6666d435)

Recovered from a deleted committed version of this file. Status column is HEAD's verdict from run 1; Audit evidence column is what the 2026-10-01 dimension audits add.

| # | Condition | Status @ HEAD | Audit evidence 2026-10-01 |
|---|---|---|---|
| 1 | All blocker findings RESOLVED or waived | fail (6 open) | Worse: 139 blocker-yes findings now recorded |
| 2 | All P1 findings RESOLVED or date-scheduled | fail (PF-006 open) | 154 P1 open, none scheduled |
| 3 | pytest test/architecture/ green | fail (dir missing) | Still not evidenced anywhere in _audit |
| 4 | pytest test/commerce/ green | unverifiable | Now answered FAIL — 6 collection errors |
| 5 | pytest test/security/ green | unverifiable | Now answered FAIL — SEC-001…012 (5 P0) |
| 6 | uvicorn backend.main:app boots zero stubs | fail (router skips) | Worse: orders + logistics also skipped; 82 routes |
| 7 | next build passes zero errors | fail (install timeout) | Now FAIL on types: 60+ TS errors |
| 8 | Mobile eas build succeeds or deferred | unverifiable | Now answered FAIL: OTA disabled, social sign-in stubbed |
| 9 | Browser: all money-path features pass | unverifiable | Now answered FAIL: chains PARTIAL, no e2e tests |
| 10 | Browser: all security-path features pass | unverifiable | Now answered FAIL: SSRF, SQLi, plaintext credentials |
| 11 | Load test p95 < 500ms at 2x peak | unverifiable | Now answered FAIL: N+1 across 293 relationships |
| 12 | Zero KEEP/HARDEN violations | pass | Still pass |
| 13 | Zero open contradictions blocking P0/P1 | fail (6) | Worse: 15 internal conflicts + canonical contradictions |
| 14 | Verifier: 3 consecutive GREEN cycles | unverifiable | Still unverifiable — no CI/CD pipeline |
| 15 | All required env vars set in production config | fail | Confirmed and wider — DATABASE_URL not even a Settings attribute |
| 16 | Migrations linear and tested | fail | Confirmed; head count disputed (5 vs 62) |
| 17 | Payment credentials stored encrypted | unverifiable | Now answered FAIL: credentials in plaintext |
| 18 | PCI-DSS compliance verified | unverifiable | Still unverifiable — not assessed |

**Gate result at HEAD: 1 pass, 8 fail, 9 unverifiable. Gate result after this audit: 1 pass, 14 fail, 3 unverifiable.**

---

## 4. CHAIN READINESS (seven critical business journeys)

No chain is COMPLETE. All 7 are PARTIAL. Failure-path coverage is good (26 of 26), but the canonical event-driven spine is entirely absent.

| Chain | Name | Happy path | Failure paths | Rollback | Verdict |
|---|---|---|---|---|---|
| CHAIN-001 | Customer order placement | partial | 4/4 covered | verified | PARTIAL |
| CHAIN-002 | Supplier payout | partial | 3/3 covered | partial | PARTIAL |
| CHAIN-003 | Return and refund | partial | 5/5 covered | broken | PARTIAL |
| CHAIN-004 | Logistics pickup and delivery | partial | 3/3 covered | partial | PARTIAL |
| CHAIN-005 | Admin ledger posting and reconciliation | partial | 4/4 covered | partial | PARTIAL |
| CHAIN-006 | Customer registration and KYC | partial | 3/3 covered | partial | PARTIAL |
| CHAIN-007 | Supplier onboarding and first product listing | partial | 4/4 covered | partial | PARTIAL |

**Systemic defect:** All seven chains define event classes in their `domains/*/events.py` files, but NONE of the service functions publish events via the canonical event bus. All subscribers are stubs containing only `logger.info` calls and `# Future:` comments. This is a systematic violation of Law 3 that breaks the order-to-cash chain at the accounting step.

Additionally, no chain has end-to-end integration tests that verify cross-domain event propagation. Multi-supplier fulfillment splitting is not implemented in `create_order`.

---

## 5. SECURITY POSTURE

### Confirmed protections (working)

| Control | Evidence |
|---|---|
| JWT type-claim verification | infrastructure/security/auth.py:313-357 |
| WebSocket JWT (declared route, not admin comms) | backend/main.py:257 |
| CSRF middleware | middleware/csrf_middleware.py registered and tested |
| Security headers middleware | Present and tested |
| Password length cap (>72 bytes rejected) | infrastructure/security/auth.py:188-190 |
| Login rate limit, fail-closed | auth_service.py:97 — 5 attempts / 60s |
| Provider import isolation (Law 31) | PASS — zero forbidden imports across ~55 providers |
| AI graceful degradation | HAS_OPENAI / HAS_HUGGINGFACE / HAS_NUMPY / HAS_PIL / HAS_VADER flags |
| No hardcoded secrets in provider code | All provider secrets read from env vars |

### Confirmed gaps

| Gap | Severity |
|---|---|
| Payment credentials in plaintext at rest | CRITICAL |
| 3× f-string SQL injection (migration, key rotation, analytics) | HIGH |
| SSRF in 4 providers (no require_safe_url()) | HIGH |
| Unauthenticated websocket_user broadcast endpoint | HIGH |
| 100+ silent excepts, including AML screening, tax calc, FX revaluation | HIGH |
| Hardcoded encryption/audit keys in 75 root-level health_test_*.py files | HIGH |
| MFA not enforced for admin/employee roles | HIGH |
| CAPTCHA silently disabled without TURNSTILE_SECRET_KEY | MEDIUM |
| cors_origins defaults to localhost | MEDIUM |
| Rate limiting RATE_LIMIT_ENABLED=false by default | MEDIUM |
| Payment idempotency key optional on 3 paths | MEDIUM |
| Permission audit log has WORM intent but no DB-level append-only enforcement | MEDIUM |
| PCI-DSS middleware logs full request details at INFO | MEDIUM |
| No dependency-scanning CI step | HIGH |
| 16 _tmp_*.py / _audit_boot_check.py debug scripts with direct DB access | MEDIUM |
| No circuit breaker or retry policy in any of ~55 providers | HIGH |
| No explicit HTTP timeout in any provider wrapper | MEDIUM |
| No health_check() on ~50 of ~55 providers | MEDIUM |

---

## 6. KEY FINDING CLUSTERS

### 6.1 Structural / architectural

- **6th module and 17th domain exist.** `backend/modules/finance/` violates Law 13 (fixed 5 modules). `backend/domains/payments/` and `backend/domains/media/` violate Law 12 (fixed 15 domains).
- **91 temp/debug files at backend root** plus outdated run_tests.ps1/run_tests.sh runners, violating Law 27.
- **Ports anti-patterns.** `domains/finance/ports.py` uses wildcard imports and a ~70-entry `_LAZY_SERVICE_EXPORTS` service locator.
- **Five undocumented providers** exist outside the canonical tree: news/, automation/, scanner/, voice/, analytics/.

### 6.2 Money correctness (systemic)

- **Float-for-money is systemic** — 14+ files across finance, orders, payouts, trading, catalog, and suppliers. 150+ float casts near money terms. `vat_rate` and `zozi_commission_rate` in config.py are explicitly typed as `float` and whitelisted in `_FLOAT_KEYS`.
- **Return-type leak** — internal `Decimal` values are serialized as `float` in API responses, violating Law 89.

### 6.3 Data integrity

- **Divergent Alembic history.** Phase 0 counted 5 heads via the CLI; dimension 06 counted 62 by parsing down_revision tuples. `alembic heads` crashes with ModuleNotFoundError: migration_helpers.
- **293 relationships lack lazy=** — defaulting to lazy="select" and causing N+1 on every collection endpoint.
- **42 user-facing tables lack country_code** (37 in comms domain alone).
- **RLS variable name mismatch.** Policies read `current_setting('app.current_country_code')` while middleware sets `app.country_scope`. Two competing RLS implementations exist.

### 6.4 Dependency & supply chain

- **`uv.lock` is effectively empty** (1 entry); `pyproject.toml` has no `[project.dependencies]`. Dockerfile and CI use pip/requirements.txt.
- **Base image drift.** Backend Dockerfile uses `python:3.11-slim` against canonical `python:3.13-slim`.
- **6 forbidden packages present:** psycopg2-binary, python-magic, pytz, tzlocal, requests, prometheus-client.
- **Missing declared dependency.** `fastapi-limiter-valkey` is imported in production but absent from requirements.txt.
- **No SBOM generation** anywhere in CI or the repo.
- **53 version mismatch findings** across backend, web, and mobile.

### 6.5 Event spine (the dominant risk)

All 7 chains define events but none publish them. All subscribers.py files are stubs. The order-to-cash chain is wired only as direct synchronous function calls, not as the architecture specifies. This breaks inventory reservation, supplier notification, commission accrual, settlement posting, and order confirmation at the event level.

### 6.6 Operational

- **No CI/CD pipeline exists.** No deploy workflow; migrations, rollback, and health gating are 100% manual.
- **`/health/deps` always returns HTTP 200** even with DB / Valkey / email / payments down.
- **No deployment, rollback, or migration-on-deploy runbooks** — only 5 operational runbooks exist.
- **OpenTelemetry disabled.** `infrastructure/utils/tracing` module is missing.
- **Valkey unreachable** — cache, sessions, rate limiting and event bus all fail.

---

## 7. ANTI-PATTERNS

20 categories, 1,847 occurrences across the backend codebase.

| Category | Occurrences | Blocker |
|---|---|---|
| Magic string | 300+ | no |
| Wildcard / unused import | 200+ | no |
| Empty handler (pass) | 191 | no |
| **TODO-only implementation** | 185 (120 in admin_service.py alone) | **yes** |
| **Wrong type for money (float)** | 150+ | **yes** |
| **Silent except** | 100+ | **yes** |
| Commented code | 120+ | partial |
| Orphan route | 11 | **yes** |
| Not-wired event handler | 25 | **yes** |
| Missing idempotency | 3 payment paths | **yes** |
| Default masks failure | 6 critical defaults | **yes** |
| Stub function (NotImplementedError) | 7 | partial |
| Orphan service | 1 confirmed, more likely | partial |
| Phantom reference | 10 | partial |
| Not-wired feature gate | 5 | partial |
| Dead branch | 3 | no |
| Unused import | 12+ files | no |
| Duplicate business logic | 4 blocks | no |

---

## 8. CONTRADICTIONS

37 contradictions harvested from canonical docs vs actual code/config/lockfiles. 9 are completion blockers, 16 partial, 12 non-blocking.

**Notable blockers:**
- CONTRAD-001: 6th module `modules/finance` (canonical: 5 modules)
- CONTRAD-002: `domains/payments/` exists as a full domain (canonical: payments is provider-only)
- CONTRAD-005: FastAPI 0.115.2 vs 0.141.x (25+ releases behind)
- CONTRAD-016/036: `fastapi-limiter-valkey` imported but absent from requirements; `slowapi`+`limits` declared instead
- CONTRAD-020: `vat_rate: float`, `zozi_commission_rate: float` (canonical: no float for money)
- CONTRAD-024: Zod 3.25.76 vs 4.3.6 (major-version drift)
- CONTRAD-029: `/hr/*` rewrite exists but standalone hr module is non-canonical
- CONTRAD-034: `modules/employee/routers/hr.py` shadowed by `hr/` package
- CONTRAD-003: `domains/media/` exists as full domain (canonical: media has no dedicated domain)

---

## 9. COMPLETION BLOCKERS

`_audit/dimensions/27_project_completion_blockers.md` consolidates the 9 Phase 0 P0 blockers.

| ID | Area | Blocker | Effort |
|---|---|---|---|
| BLOCKER-001 | boot | `backend/` lacks `__init__.py`; `from backend.main import app` fails | S |
| BLOCKER-002 | boot | `settings.DATABASE_URL` AttributeError; actual attribute is `database_url` | S |
| BLOCKER-003 | infra | No local Valkey on localhost:6379; cache, rate limiting, sessions and event bus all fail | S |
| BLOCKER-004 | testing | 6 test files cannot be imported → full suite cannot execute | M |
| BLOCKER-005 | frontend | 60+ TypeScript compilation errors | L |
| BLOCKER-006 | backend lint | 8335 ruff errors (2954 auto-fixable) | L |
| BLOCKER-007 | database | 5 divergent Alembic heads; Law 49 violation | L |
| BLOCKER-008 | dependencies | Backend version mismatches and 6 forbidden packages | M |
| BLOCKER-009 | dependencies | Frontend version mismatches vs TECHNOLOGY_STACK.md | M |

---

## 10. REMEDIATION PRIORITY (high-level waves)

**Wave 0 — Make the application boot completely and truthfully**

1. Fix backend package import (BLOCKER-001)
2. Restore orders and logistics routers (resolve bulk_archive_entities in domains.governance.ports)
3. Merge 5 Alembic heads into single linear chain (BLOCKER-007)
4. Fix migration_helpers import so alembic heads runs
5. Align settings.database_url ↔ DATABASE_URL and valkey_url ↔ VALKEY_URL
6. Bring up Valkey and confirm RLS policy installation on Neon
7. Fix 6 broken test imports (BLOCKER-004)
8. Re-enable OpenTelemetry
9. Delete modules/finance/routers/cash_management.py or properly register it
10. Delete 91 root-level temp/debug files and run_tests.ps1/.sh

**Wave 1 — Stop the bleeding: security and money**

11. Encrypt payment gateway credentials with AES-256-GCM
12. Add JWT verification to websocket_user
13. Replace all f-string SQL with sa.text() + bound parameters
14. Wrap outbound HTTP calls in require_safe_url()
15. Fix screen_supplier to return cleared=False on exception
16. Add logging to all 100+ silent excepts in financial paths
17. Convert vat_rate, commission_rate and all monetary Pydantic fields to Decimal
18. Wire claim_inventory / release_inventory into order flows
19. Make idempotency_key required on PaymentIntentRequest and payment webhooks
20. Gate refunds behind explicit intent with finance.ledger.write
21. Compute WORM chain hash before INSERT; remove post-INSERT UPDATE
22. Pin starlette; add dependency scanning to CI

**Wave 2 — Make the event spine real**

23. Implement finance subscribers (commission accrual, reversal, settlement)
24. Implement order lifecycle subscribers and register them
25. Emit post-commit events for all 7 chains
26. Convert event publication to after_commit hooks
27. Implement or un-register 25 governance stub handlers
28. Replace time.sleep() and run_until_complete() with asyncio primitives
29. Implement multi-supplier Shipment splitting in create_order
30. Implement or remove 11 orphan routers and 7 NotImplementedError stubs

**Wave 3 — Data integrity and RLS**

31. Align RLS policy variable name; pick one implementation
32. Add country_code to 42 user-facing tables
33. Create ORM models for 14 unmapped tables
34. Apply media schema migration
35. Add lazy="selectin" to all 293 relationships
36. Add __table_args__ schema to payroll_records and employee_trainings
37. Sync 13 orphan columns and apply 17 pending column migrations

**Wave 4 — Engineering gate and supply chain**

38. Populate uv.lock and pyproject.toml [project.dependencies]
39. Remove 6 forbidden packages; add fastapi-limiter-valkey, uvloop, httptools, pybreaker
40. Reconcile all backend, web and mobile versions with TECHNOLOGY_STACK.md
41. Fix Docker base image to python:3.13-slim
42. Generate SBOM via Syft/CycloneDX in CI

**Wave 5 — Operational readiness**

43. Make /health/deps return 503 when any critical dependency is down
44. Build .github/workflows/deploy.yml with pre-deploy migrations and health gate
45. Write deployment, rollback, and migration-on-deploy runbooks
46. Add circuit breaker + retry + timeout to all ~55 providers
47. Replace os.getenv() with typed settings in provider config
48. Add per-task concurrency_limit for payout and reconciliation

**Wave 6 — Frontend, mobile, performance**

49. Fix 60+ TypeScript errors and 8335 ruff errors
50. Keyset pagination on product listing and order history
51. Add pg_trgm GIN index on catalog.products.name
52. Add AVIF + blurDataURL image pipeline
53. Re-enable OTA updates
54. Resolve mobile payment strategy contradiction
55. Implement native social sign-in
56. Write Detox specs for critical flows
57. Add offline detection + mutation queue

**Wave 7 — Authorization and test depth**

58. Gate or retire 68 orphan feature atoms
59. Enforce MFA for admin/employee roles
60. Add feature tests for 9 uncovered domains
61. Add architecture tests for import laws and Law 70 gates
62. Add CI gates: single Alembic head, no lazy="select", no forbidden imports, no float-for-money

---

## 11. WHAT IS GENUINELY STRONG

Not everything is broken. These are real assets:

| Asset | Evidence |
|---|---|
| Frontend builds cleanly and fast | Next.js 16.3.4 compiled in 13.9s, 151 static pages generated |
| Docker Compose topology is complete and valid | 10 services incl. 4 specialized Celery workers, pgbouncer |
| Failure-path coverage across all 7 chains | 26 of 26 required failure paths have cited code evidence |
| CHAIN-001 rollback is verified | _rollback_order_creation exists and is called on exception |
| Provider import isolation (Law 31) | PASS — zero forbidden imports across ~55 providers |

---

## 12. INTERNAL CONFLICTS INSIDE THE AUDIT CORPUS

The audit does not fully agree with itself. These must be resolved before remediation sequencing:

| # | Conflict | Sources |
|---|---|---|
| C1 | Alembic head count: "5 heads" vs "62 divergent migration heads" | phase0_results.md + 07_tables_fields.md + 27_project_completion_blockers.md say 5; 06_database.md DB-001 says 62 |
| C2 | Law 49: laws audit says "No violation — Alembic history is linear" | 09_laws.md:71 contradicts 06_database.md, 07_tables_fields.md, logs/phase0_results.md, 27_project_completion_blockers.md |
| C3 | Law 45 (N+1): laws audit says "No violation — all relationships use lazy=selectin or joined" | 09_laws.md:67 contradicts 06_database.md (293 relationships) and 19_performance.md |
| C4 | Law 21 (timestamps): laws audit says "No violation" | 09_laws.md:43 contradicts 07_tables_fields.md (150 tables use Python-side default) |
| C5 | Law 34 (parameterized SQL): laws audit says "No violation" | 09_laws.md:56 contradicts 18_security.md SEC-002/003/004 (3 P0 f-string injections) |
| C6 | Law 41 (WebSocket auth): laws audit says "No violation" | 09_laws.md:63 contradicts 05_wiring.md WIRE-001 |
| C7 | Domain count: "17 domains, extra = media + payments" vs "payments is a 17th domain" | 09_laws.md:34 vs 01_architectural.md ARCH-002 |
| C8 | Feature stack P0/P1 count = "0 (all resolved)" | 03_FEATURE_STACK_DRAFT.md:887-889 contradicts 46 P0 findings and 9 Phase-0 blockers |
| C9 | Log volume mismatch | logs/*.jsonl has 1 record while dimension reports 10 findings (operational); 1 record vs 9 findings (performance) |
| C10 | Money-float cluster membership | 03_logical.md:90 lists LOGIC-016 (state machine) as cluster member |
| C11 | 00_README.md file index is stale | Lists only 3 files; claims "3 PASS / 2 FAIL" for Phase 0.5 |
| C12 | CI/CD: "No .github/workflows/ directory" vs ".github/workflows/ci.yml exists" | 04_operational.md OPS-002 vs 02_technological.md |
| C13 | modules/finance load status | CONTRAD-001 calls it a 6th module with router; ARCH-011 proves router has no decorators and is not registered |
| C14 | Mobile Stripe strategy | Native SDK installed but web redirect used; Tap/PayTabs/Thawani wrappers dynamically required but not in package.json |
| C15 | country_code count | 07_tables_fields.md: 42 tables lack country_code; 09_laws.md:42 says all country_code columns use String(2) — different things, laws audit never surfaces the 42-table gap |

---

## 13. RECOMMENDATIONS

1. **Resolve all 15 internal audit conflicts (C1–C15)** before sequencing remediation — several would let a remediation plan declare work "already done" that is not.
2. **Wave 0 items are absolute prerequisites** — no remediation in other waves can proceed until the application boots with all routers mounted, RLS installed, Valkey reachable, and migrations on a single head.
3. **The event spine (Wave 2) is the largest structural risk** — no chain can reach COMPLETE until events are published and subscribers are implemented; this is not optional middleware.
4. **Security Wave 1 items are independent and parallel-izable** — they do not depend on Wave 0 but must be complete before any payment or auth path is exposed.
5. **The 18-condition launch gate is the authoritative go/no-go** — the audit converted 6 previously-unverifiable conditions to confirmed FAIL. Condition 1 alone requires reducing 139 blocker-yes findings to RESOLVED or waived.

---

*This summary was compiled from `_audit/**` files only. No source files were read or modified. The full audit corpus consists of 14 dimension reports, 4 cross-cutting reports, 17 JSONL logs, and the 18-condition launch gate recovered from git HEAD.*