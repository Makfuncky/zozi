# 11 — PRODUCTION READINESS COMPILATION

**Compiled:** 2026-10-01
**Sources:** `_audit/**` only (5 top-level reports, 15 dimension reports, 17 raw JSONL logs)
**Mode:** READ-ONLY compilation. No source file was modified.
**Status of all findings:** NEW (nothing resolved, nothing compiled, nothing deferred)

> ### ⚠ Provenance warning — this file overwrote a committed predecessor
>
> A 40-line version of this file was committed at HEAD (`6666d435`, "Generated: 2026-09-30T04:40:00Z, Run number: 1") and contained the project's **18-condition launch gate** — the canonical go/no-go mechanism. It had been deleted in the working tree, and this compilation run wrote over its tracked path.
>
> The 18-condition gate has been **recovered and preserved in full at §3.4**, with HEAD's own statuses retained alongside the 2026-10-01 audit evidence. Nothing of substance was lost, but the original file's formatting and provenance metadata were not.
>
> Recover at any time with `git show HEAD:_audit/11_PRODUCTION_READINESS.md`.
>
> **Note:** `_audit/DIMENSION_INDEX.md` and a rewritten `_audit/00_README.md` appeared in the working tree at 23:58 during this compilation — i.e. a concurrent process is also writing into `_audit/`. Row-count totals in §2 are reconciled against `DIMENSION_INDEX.md` §2, which is treated as authoritative where the two overlap.

---

## 1. VERDICT

**NOT PRODUCTION READY.**

The platform is **feature-rich and structurally sound at the file level, but functionally incomplete at the runtime level.** Every dimension auditor returned confirmation ❌. Zero of seven critical business chains reached COMPLETE. The application boots to 82 routes, but two entire routers (`logistics`, `orders`) silently fail to register, RLS policy installation is skipped, OpenTelemetry is disabled, and Valkey is unreachable — meaning cache, sessions, rate limiting and the event bus are non-functional in the audited environment.

The dominant risk is **not** cosmetic. It is that the cross-domain event layer is entirely non-functional: every `subscribers.py` is a stub, no service publishes its declared events, and consequently no inventory reservation, no supplier notification, no commission accrual, no settlement posting and no order confirmation notification ever fires. The order-to-cash chain is wired only as direct synchronous function calls, not as the architecture specifies.

| Readiness dimension | Verdict | Primary evidence |
|---|---|---|
| Build & boot | ❌ FAIL | Boot smoke: 3 PASS / 2 FAIL of 5 checks; 2 routers skipped; import path broken |
| Functional correctness (business chains) | ❌ FAIL | 0 of 7 chains COMPLETE; 7 PARTIAL; 1 with broken rollback |
| Security | ❌ FAIL | 5 P0 (plaintext payment credentials, 3× SQL injection via f-string, SSRF) |
| Money correctness | ❌ FAIL | Float-for-money systemic in 14+ files; `vat_rate`/`commission_rate` typed `float` |
| Data integrity / schema | ❌ FAIL | 5 Alembic heads; 293 relationships default `lazy="select"`; 42 tables missing `country_code` |
| Error handling | ❌ FAIL | 100+ silent `except Exception:` blocks; finance tax/FX/AML failures swallowed |
| Lazy loading / N+1 | ❌ FAIL | 293 relationships without `lazy=`; keyset pagination absent on hot lists |
| Operational / CI-CD | ❌ FAIL | No CI/CD pipeline; `/health/deps` never fails closed; no deploy/rollback runbook |
| Dependency & supply chain | ❌ FAIL | `uv.lock` empty; 6 forbidden packages; 53 version findings; no SBOM; no dep scanning |
| Frontend web | ⚠️ PARTIAL | Build passes (151 pages) but 60+ TS errors; `zod` on major version 3 vs 4 |
| Mobile | ❌ FAIL | OTA updates disabled; social sign-in stubs; zero Detox specs |
| Observability | ❌ FAIL | OpenTelemetry disabled; RLS install skipped; R2 not health-checked |
| Test suite integrity | ❌ FAIL | 4657 collected / 6 collection errors; 8335 ruff errors; 9 domains lack feature tests |

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
| **Subtotal — 12 tabular dimensions** | — | **464** | **55** | **154** | **233** | **22** | **134** | **11** |
| **Subtotal — non-tabular (08, 09)** | — | **31** | — | — | — | — | **5** | — |
| **GRAND TOTAL** | — | **495** | **55** | **154** | **233** | **22** | **139** | **11** |

Reconciliation: tabular 464 = 55 + 154 + 233 + 22 (priority) = 134 + 11 + 319 (blocker split). Non-tabular 31 = 8 (`08_providers`) + 23 (`09_laws`), which carry no P0–P3 split. Grand total 495 = 464 + 31. These tabular subtotals match `_audit/DIMENSION_INDEX.md` §2 exactly; where this table and that index disagree, that index is authoritative for row counts.

> **Counting caveat.** `09_laws.md` has no priority breakdown, so its 5 blockers appear only in the blocker column. `08_providers.md` and `09_laws.md` are excluded from priority totals by design. Do not read "55 P0" as the complete P0 population if law violations are later prioritised.

Additional cross-cutting artefacts (not counted above, overlapping in scope):

| Artefact | Volume | Blockers (yes) | Partial |
|---|---|---|---|
| Anti-patterns (`09_ANTI_PATTERNS.md`) | 20 categories, **1,847 occurrences** | 8 | 3 |
| Contradictions (`07_CONTRADICTIONS.md`) | 37 | 9 | 16 |
| Chains (`10_CHAINS.md`) | 7 chains | 0 COMPLETE / 7 PARTIAL | — |
| Feature stack (`03_FEATURE_STACK_DRAFT.md`) | 231 feature atoms, 68 orphans | 20 launch-critical | — |
| Phase 0 boot/preflight (`logs/phase0_results.md`) | 14 checks, 3 PASS / 9 FAIL | 9 | — |

---

## 3. BOOT & PREFLIGHT GATE (Phase 0 / 0.5)

This is the hardest gate, and it fails.

### 3.1 What actually works

| Check | Result | Evidence |
|---|---|---|
| Architecture test collection | ✅ PASS | 356 tests collected in 4.09s |
| Frontend install | ✅ PASS | `pnpm install --frozen-lockfile` clean, 14.3s |
| Frontend build | ✅ PASS | Next.js 16.3.4 compiled, 13.9s, 151 static pages |
| Docker Compose config | ✅ PASS | Valid YAML, 10 services: backend, celery-beat, celery-worker-{emails,ml,payouts,periodic}, db, frontend, pgbouncer, valkey |

### 3.2 Boot degradations that were NOT counted as failures

The adapted boot check (`cd backend; python -c "from main import app"`) returned **82 routes**, but emitted six warnings that materially change what is running in production:

| Boot warning | Production consequence |
|---|---|
| `Skipping router orders: cannot import name 'bulk_archive_entities' from 'domains.governance.ports'` | **The entire orders router is not mounted.** Order placement, order history, returns and refunds are unreachable. |
| `Skipping router logistics: cannot import name 'bulk_archive_entities'` | **The entire logistics router is not mounted.** Shipment creation, pickup scanning and tracking are unreachable. |
| `RLS policy install skipped` (Neon unsupported `statement_timeout`) | Row-level security is **not** installed in the database. Country data isolation is unenforced at the DB layer. |
| `OpenTelemetry disabled: No module named 'infrastructure.utils.tracing'` | Distributed tracing is off. |
| `Valkey connection timeouts (3 retries exhausted)` | Cache, session store, rate limiter and event bus are all down. |
| `readiness_require_valkey AttributeError` | Readiness probe itself is broken. |

Two of the five business domains have no HTTP surface at all. This is the single most consequential fact in the audit and it is recorded only as an "Observed but not changed" note in `logs/phase0_results.md`, not as a finding ID.

### 3.3 Pre-flight failures (all 9 are completion blockers)

| # | Check | Failure |
|---|---|---|
| 1 | Route count | `ModuleNotFoundError: No module named 'infrastructure'` — `backend/` lacks `__init__.py` |
| 6 | `DATABASE_URL` | `AttributeError: Settings has no attribute 'DATABASE_URL'`; actual attribute is lowercase `database_url` |
| 7 | Valkey | `ValueError` on `valkey://` scheme, then `ConnectionRefusedError 10061` on `localhost:6379` |
| 8 | Test collection | 4657 collected, **6 collection errors** |
| 9 | Frontend types | **60+ TypeScript errors** |
| 10 | Lint | **8335 ruff errors** (2954 auto-fixable) |
| 11-12 | Alembic | **5 divergent heads**; `alembic heads` crashes with `ModuleNotFoundError: migration_helpers` |
| 13 | Python lockfile | `uv.lock` has 1 package (not a lockfile); 6 forbidden packages; 7 version mismatches |
| 14 | Frontend lockfile | 9 version mismatches incl. `zod` major-version drift (3 → 4) |

### 3.4 The 18-condition launch gate (recovered from git HEAD `6666d435`)

This gate existed in a committed 40-line version of this file (`git show HEAD:_audit/11_PRODUCTION_READINESS.md`, generated 2026-09-30T04:40:00Z, run 1). That version was deleted in the working tree and the compilation run overwrote it. It is reproduced here because it is the project's canonical go/no-go mechanism and was not restated anywhere else in `_audit/**`.

The **Status** column is HEAD's own verdict from run 1. The **Audit evidence** column is what the 2026-10-01 dimension audits add.

| # | Condition | Status @ HEAD | Audit evidence 2026-10-01 |
|---|---|---|---|
| 1 | All `yes` completion-blocker findings RESOLVED or waived | fail (6 open) | **Worse**: 139 blocker-yes findings now recorded |
| 2 | All P1 findings RESOLVED or date-scheduled | fail (PF-006 open) | 154 P1 open, none scheduled |
| 3 | `pytest test/architecture/` green | fail (dir missing) | Still not evidenced anywhere in `_audit/**` |
| 4 | `pytest test/commerce/` green | unverifiable | Still unverifiable — 6 collection errors |
| 5 | `pytest test/security/` green | unverifiable | **Now answered FAIL** — SEC-001…012 (5 P0) |
| 6 | `uvicorn backend.main:app` boots zero stubs | fail (router skips) | **Worse**: `orders` + `logistics` also skipped; 82 routes |
| 7 | `next build` passes zero errors | fail (install timeout) | **Now FAIL on types**: 60+ TS errors (151 pages build) |
| 8 | Mobile `eas build` succeeds or explicitly deferred | unverifiable | **Now answered FAIL**: OTA disabled, social sign-in stubbed, 0 Detox specs |
| 9 | Browser: all money-path features pass | unverifiable | **Now answered FAIL**: order/settlement chains PARTIAL, no e2e chain tests |
| 10 | Browser: all security-path features pass | unverifiable | **Now answered FAIL**: SSRF, 3× SQLi, plaintext payment credentials |
| 11 | Load test p95 < 500 ms at 2× peak | unverifiable | **Now answered FAIL**: N+1 across 293 relationships, no keyset pagination |
| 12 | Zero KEEP/HARDEN violations | pass | Still pass — no KEEP/HARDEN constraints exist yet |
| 13 | Zero open contradictions blocking P0/P1 | fail (6) | **Worse**: 15 internal corpus conflicts + canonical-doc contradictions |
| 14 | Verifier: 3 consecutive GREEN cycles | unverifiable | Still unverifiable — no CI/CD pipeline exists |
| 15 | All required env vars set in production config | fail (DATABASE_URL, VALKEY_URL) | Confirmed and wider — `DATABASE_URL` is not even a Settings attribute |
| 16 | Migrations linear and tested | fail (`alembic current` failed) | Confirmed; head count disputed (5 vs 62 — see §13) |
| 17 | Payment credentials stored encrypted | unverifiable | **Now answered FAIL**: credentials in plaintext (`backend/.env`) |
| 18 | PCI-DSS compliance verified | unverifiable | Still unverifiable — not assessed in any dimension |

**Gate result at HEAD: 1 pass, 8 fail, 9 unverifiable. Gate result after this audit: 1 pass, 14 fail, 3 unverifiable.**

Of the 9 unverifiable conditions, **6 have now been resolved to FAIL** (5, 8, 9, 10, 11, 17) — the audits converted open questions into confirmed blockers. The 3 still-unverifiable are **4, 14, 18**:

- **4 (`pytest test/commerce/`)** — blocked by the 6 test-collection errors; cannot be collected until boot is fixed.
- **14 (verifier: 3 consecutive GREEN cycles)** — no CI/CD pipeline exists to run a verifier.
- **18 (PCI-DSS compliance)** — not assessed by any dimension; genuinely out of scope of the current audit corpus.

Condition **3** (`pytest test/architecture/`, fail: directory missing) remains an unresolved *fail*, not an open question, and is a fast, cheap fix — the test directory does not exist.

**Waivers on record at HEAD: none. Known issues at launch at HEAD: "None yet — awaiting Pass 1 and Pass 2."** Both are now superseded by the register in §4; no waiver has been granted for any blocker in the 139-item blocker population.

---

## 4. BLOCKING ISSUE REGISTER (P0)

### 4.1 Structural / boot blockers

| ID | Issue | Evidence | Blocking |
|---|---|---|---|
| BLOCKER-001 | Backend not importable as a package from project root | `ModuleNotFoundError: No module named 'infrastructure'` | All boot, test, CI commands |
| ARCH-001 | 6th top-level module `modules/finance/` violates Law 13 (fixed 5 modules) | `backend/modules/finance/__init__.py:1` | Law 13; route boundary |
| ARCH-002 | `domains/payments/` is a 16th/17th domain; violates Law 12 (fixed 15 domains) | `backend/domains/payments/events.py:1` | Law 12; duplicates `domains/finance/services/payments/` |
| ARCH-011 | `modules/finance/routers/cash_management.py` has 49 plain functions + an `APIRouter` with **no decorators**, and is not loaded by `main.py:_load_routers()` | `backend/main.py:303` | Dead code masquerading as a router |
| ARCH-014 / LOGIC-006 | `domains/finance/subscribers.py` handlers only `logger.info` with `# Future:` comments | `backend/domains/finance/subscribers.py:20` | Commission accrual + settlement posting never occur |
| LOGIC-018 | `domains/orders/subscribers.py` — all five lifecycle subscribers are stubs; no consumers registered | `backend/domains/orders/subscribers.py:1-129` | Audit trail, notifications, settlements never auto-trigger |
| AP-018 | 25 un-wired governance event handlers registered but never implemented | `backend/domains/governance/subscribers.py:63` | Silent event drops |
| AP-009 | 11 orphan router files (supplier/security, supplier/promotions, supplier/hr, logistics/catalog, employee/promotions, …) | `backend/modules/supplier/routers/security.py:12` | Guaranteed 404s |

### 4.2 Data / migration blockers

| ID | Issue | Evidence | Blocking |
|---|---|---|---|
| BLOCKER-007 / DB-001 / TF P0 | **5 divergent Alembic heads** — Law 49 violation | `alembic heads` → `20260930_0002, 20260930_0003, 20260930_0006, 20260930_0007, 20261001_0001` | All DB migrations, all deploys |
| DB-002 | `alembic heads` crashes: `ModuleNotFoundError: No module named 'migration_helpers'` | `alembic/versions/2026_08_06_0001_add_analytics_audit_columns.py:31` | Cannot even enumerate heads |
| DB-005 | RLS policy uses `current_setting('app.current_country_code')` but middleware sets `app.country_scope` — **names do not match** | `infrastructure/database/sql/pg_rls_policies.sql:23-26` vs `middleware/country_context.py:272` | Cross-country data isolation |
| WIRE-002 | Canonical `set_rls_context()` sets ContextVars only; never executes `SET LOCAL` | `infrastructure/database/rls_interceptor.py:128` | Law 5 unenforced |
| DB-006 | Two competing RLS implementations (SQLAlchemy interceptor vs raw `.sql`) | `rls_interceptor.py:223-270` | Undeterminable enforcement |
| TF-001 | **42 user-facing tables missing `country_code`** (37 in `comms`, plus `customers.cross_country_customer_sessions`, `orders.order_notifications`, `suppliers.supplier_documents`, `suppliers.supplier_notification_preferences`) | `dimensions/07_tables_fields.md` | RLS scoping (Laws 5, 20) |
| TF-002 | **14 DB tables have no ORM model** (`security.permission_audit_log`, `comms.notification_*`, `hr.onboarding_*`, `logistics.*_projections`, …) | `dimensions/07_tables_fields.md` | Schema drift, untraceable data |
| TF-003 | `media.media_assets` and `media.upload_sessions` models exist but DB tables do not | `domains/media/models/media_asset.py:11` | Media domain non-functional |
| TF-006 | `payroll_records` and `employee_trainings` models lack `__table_args__` schema declaration | `dimensions/07_tables_fields.md` | Would create tables in `public` |

### 4.3 Security blockers

| ID | Severity | Issue | Evidence |
|---|---|---|---|
| SEC-001 / FEAT-005 / FEAT-022 | **CRITICAL** | Payment gateway `secret_key`, `webhook_secret`, `public_key`, `credentials` JSON stored **in plaintext** in `finance.payment_gateway_connections` | `domains/finance/services/payments/payment_engine.py:3200-3206`; `domains/finance/models/payments.py:88` |
| SEC-002 | **HIGH** | SQL injection via f-string in migration (`f"SELECT * FROM public.{p}"`, `f"INSERT INTO :schema.:flat_name"`) | `alembic/versions/2026_07_29_20_30-...py:325-330` |
| SEC-003 | **HIGH** | SQL injection via f-string column list in key rotation | `infrastructure/security/key_rotation.py:115` |
| SEC-004 | **HIGH** | SQL injection via f-string table + WHERE in analytics aggregation | `domains/analytics/services/aggregation/command_center_query_service.py:80,83` |
| SEC-005 | **HIGH** | **SSRF** — `urlopen()`/`httpx` with caller-influenced URLs, no `is_safe_url()` guard, in 4 providers | `providers/security/watchlist.py:65`, `threat_intel.py:30`, `voice/voice_to_text.py:60`, `payment_engine.py:3330,3399` |
| WIRE-001 | **HIGH** | `websocket_user` accepts connections **without JWT verification** → unauthenticated broadcast to all users | `modules/admin/routers/comms.py:138` |
| AP-004 | HIGH | 100+ `except Exception:` blocks with no logging — **finance tax calc, FX revaluation, AML screening** all swallow errors | `general_ledger.py:8560`, `order_engine.py:698-703`, `supplier_service.py:164` |
| LOGIC-008 | HIGH | `screen_supplier` catches all exceptions and returns `{"cleared": True}` — **a failed AML check passes the supplier** | `domains/suppliers/services/supplier_service.py:164` |
| FIND-09-004 | HIGH | Hardcoded `SECRET_KEY`, `FIELD_ENCRYPTION_KEY`, `AUDIT_CHAIN_KEY` in the 75 `health_test_*.py` files at backend root | Law 32 |
| FIND-09-011 | HIGH | **No dependency-scanning CI step** (no pip-audit / trivy / bandit / snyk / dependabot) | Law 44 |
| TECH-030 | MEDIUM | `starlette` unpinned → may resolve below CVE thresholds (CVE-2025-54121, CVE-2025-62727, CVE-2026-48817) | `requirements.txt` |
| SEC-007 / AP-017 | MEDIUM | CAPTCHA silently skipped when `TURNSTILE_SECRET_KEY` unset → bot protection off on all public auth endpoints. Payment idempotency key optional on 3 paths. | `infrastructure/security/dependencies.py:37-39` |

### 4.4 Money-correctness blockers

| ID | Issue | Evidence |
|---|---|---|
| LOGIC-001 / 002 / 004 / 010 / 011 / 012 / 013 | `CodRemittanceRequest.amount: float`; `reconcile_in_multi_currency` uses `round(amount * fx, 2)` float arithmetic; float filters on `Order.total_amount`; float payout amounts; float PO/SO line totals | `finance_service.py:66,576-593`; `orders_service.py:213`; `payout_batch_service.py:3387`; `trading_service.py:134,310` |
| FEAT-001/002/003/009/010 | Float arithmetic in **cart totals**, order serialization, product price serialization, tax calculation entry point | `orders_service.py:142,309`; `products_service.py:132`; `modules/customer/routers/orders.py:142,175` |
| CONTRAD-020 | `vat_rate: float` and `zozi_commission_rate: float` in typed settings, explicitly whitelisted in `_FLOAT_KEYS` | `backend/config.py:204-206`, `_FLOAT_KEYS` at `:79` |
| AP-005 | 150+ `float()` casts near money terms in non-test backend source | across suppliers, logistics, finance, hr, payments |
| FEAT-004 / FEAT-025 | `INVENTORY_HELD_STATUSES` is defined but **no `claim_inventory`/`release_inventory` is wired** into order creation or cancellation → **oversell risk** | `payment_engine.py:259`; `orders_service.py:259` |
| FEAT-011 | Refund auto-issued when a return reaches `completed`, with no explicit refund intent and no `finance.ledger.write` gate | `domains/orders/services/returns/service.py:388` |
| LOGIC-015 | `idempotency_key: Optional[str] = None` on `PaymentIntentRequest` → duplicate payment intents on retry | `payment_engine.py:361-371` |
| LOGIC-016 | `refund_order` allows refund on `cancelled` orders but `allowed_transitions` has no `cancelled → refunded` | `returns/service.py:441`; `orders_service.py:447` |
| LOGIC-007 / WIRE-004 | `asyncio.get_event_loop()` + `loop.run_until_complete()` inside async refund handler; `time.sleep()` in async event-bus retry | `returns/service.py:435-438`; `event_bus.py:331` |
| LOGIC-014 | Failed FX revaluation logs a warning and continues **without rolling back** → books do not match inventory | `finance/services/data_import_service.py:571-572` |
| AP-010 | WORM audit performs `UPDATE audit_logs SET details = jsonb_set(...)` after INSERT → audit trail is mutable | `domains/audit/services/worm_audit.py:60-67` |
| CHAIN-003 | **Refund rollback is BROKEN** — once a refund is issued to Stripe/Tap there is no compensating mechanism | `10_CHAINS.md` |

### 4.5 Operational blockers

| ID | Issue | Evidence |
|---|---|---|
| OPS-001 | `/health/deps` **always returns HTTP 200** even with DB / Valkey / email / payments down — load-balancer and orchestrator health gates are defeated | `backend/main.py:149-182` |
| OPS-002 | **No CI/CD pipeline at all** (`.github/workflows/` has `ci.yml` only; no deploy workflow) — migrations, rollback and health gating are 100% manual | `04_operational.md` |
| BLOCKER-003 | Valkey unreachable → rate limiting, token blacklist, cache and event bus all fail | `config.py` (`valkey_url`) |
| BLOCKER-004 | 6 test files cannot be imported → full suite cannot execute | see §6 |
| BLOCKER-005 | 60+ TypeScript errors in production frontend source | `tsc --noEmit` |
| BLOCKER-006 | 8335 ruff errors in `backend/` (2954 auto-fixable) | `ruff check .` |
| MOB-001 / MOB-002 | **OTA updates disabled** (`expo.modules.updates.ENABLED=false`) and `expo-updates` absent from `package.json` → no hotfix path without full store review | `android/app/src/main/AndroidManifest.xml:17` |
| TECH-001/002/003 | `uv.lock` empty, `pyproject.toml` has no `[project.dependencies]`, Dockerfile + CI use pip not uv | `backend/uv.lock`, `backend/pyproject.toml` |
| TECH-006 | Docker base image `python:3.11-slim` vs required `3.13-slim` | `backend/Dockerfile:1` |

---

## 5. CHAIN READINESS (the seven critical business journeys)

No chain is COMPLETE. Every chain has a working happy path implemented as **direct synchronous calls**, but the canonical event-driven spine is absent.

| Chain | Name | Happy path | Failure paths | Rollback | Verdict |
|---|---|---|---|---|---|
| CHAIN-001 | Customer order placement | partial | 4/4 | verified | **PARTIAL** |
| CHAIN-002 | Supplier payout | partial | 3/3 | partial | **PARTIAL** |
| CHAIN-003 | Return and refund | partial | 5/5 | **broken** | **PARTIAL** |
| CHAIN-004 | Logistics pickup and delivery | partial | 3/3 | partial | **PARTIAL** |
| CHAIN-005 | Admin ledger posting and reconciliation | partial | 4/4 | partial | **PARTIAL** |
| CHAIN-006 | Customer registration and KYC | partial | 3/3 | partial | **PARTIAL** |
| CHAIN-007 | Supplier onboarding and first product listing | partial | 4/4 | partial | **PARTIAL** |

**Failure-path coverage is genuinely good** (26 of 26 required failure paths are covered with cited evidence). **Rollback coverage is not** — only CHAIN-001 has a verified compensating action (`_rollback_order_creation`).

### 5.1 The systemic defect: Law 3 is not implemented anywhere

> "All seven chains have event classes defined in their respective `domains/*/events.py` files, but **NONE** of the service functions actually publish events via the canonical event bus. **All subscribers are stubs** containing only `logger.info` calls and `# Future:` comments. This is a systematic violation of Law 3."
> — `10_CHAINS.md`, cross-cutting finding 1

Concretely missing:
- `create_order` never calls `publish_order_created` → **no inventory reservation, no supplier notification, no fraud evaluation, no confirmation email**
- `generate_supplier_payout_batches` never emits `PayoutCreated`
- `update_return_request` issues Stripe/Tap refunds directly, never emits `RefundPosted`
- `create_shipment` never emits `ShipmentCreated`
- `create_journal_entry` never emits `JournalEntryPosted`; no event-driven reconciliation flow exists
- `register_user` never emits `CustomerRegistered`; **the accounts domain has no `events.py` or `subscribers.py` at all**
- `register_user` never emits `SupplierRegistered`; product creation never emits `ProductCreated`
- WIRE-003: even where `publish()` *is* called, it is **synchronous inside the service transaction**, so a mid-transaction failure can leave cross-domain state inconsistent

### 5.2 The missing multi-supplier split

CHAIN-001 finding: a single `Order` row is created with `OrderItem` rows referencing multiple `supplier_id` values, but **no per-supplier `Shipment` rows are created** and `selected_partner_id` is set at order level. This directly contradicts `ARCHITECTURE_STACK.md §2` ("A single customer order may span multiple suppliers… fulfillment splits per supplier into `shipments`"). The multi-supplier market model is therefore not implemented.

### 5.3 No end-to-end chain tests

`test_cross_domain_flows.py` and `test_e2e_flows.py` only verify that modules and event *classes* exist — not that anything is published or consumed. Zero Playwright specs exist for any of the seven chains.

---

## 6. TEST SUITE INTEGRITY

| Metric | Value |
|---|---|
| Tests collected | 4657 |
| Collection errors | 6 |
| Architecture tests collected | 356 |
| Ruff errors (backend) | 8335 (2954 auto-fixable) |
| TypeScript errors (frontend web) | 60+ |
| Domains with dedicated feature tests | 8 of 17 |
| Playwright coverage of money paths | Present but **never executed** in audit scope (FEAT-042, marked INFERRED) |
| Detox E2E specs (mobile) | **0** (`.detoxrc.js` present, no specs) |

The 6 collection errors:

| File | Error |
|---|---|
| `tests/domains/catalog/test_category_deletion.py` | `ImportError: _CATEGORY_DELETED_MESSAGE` |
| `tests/domains/catalog/test_file_54_resolution.py` | `ImportError: MODERATION_APPROVE_MESSAGE` |
| `tests/domains/customers/test_cross_country_session.py` | `ModuleNotFoundError: No module named 'backend'` |
| `tests/domains/customers/test_customer_router_service.py` | `ImportError: _delete_response` |
| `tests/domains/orders/test_core_admin.py` | `ImportError: bulk_archive_entities` |
| `tests/domains/test_circuit_breaker.py` | `ImportError: CircuitBreakerRegistry` |

Note: `test_core_admin.py` fails on the same missing symbol (`bulk_archive_entities`) that causes the **orders router to be skipped at boot**. A broken import in a test and a missing runtime import in production share a root cause.

---

## 7. SECURITY POSTURE

### Confirmed protections (working)

| Control | Evidence |
|---|---|
| JWT type-claim verification | `infrastructure/security/auth.py:313-357` verifies `type` in `_decode_and_validate` and `decode_token`; tests exist |
| WebSocket JWT (declared route) | `backend/main.py:257` calls `decode_token(token, expected_type="access")` — **contradicted by WIRE-001 for the admin `comms` router** |
| CSRF middleware | `middleware/csrf_middleware.py` registered and tested |
| Security headers middleware | Present and tested |
| Password length cap (>72 bytes rejected) | `infrastructure/security/auth.py:188-190` |
| Login rate limit, fail-closed | 5 attempts / 60s against Valkey — `auth_service.py:97` |
| Provider import isolation (Law 31) | **PASS** — zero providers import `domains`, `services`, `middleware`, `rbac`, `jobs`, `modules` |
| AI graceful degradation | `HAS_OPENAI` / `HAS_HUGGINGFACE` / `HAS_NUMPY` / `HAS_PIL` / `HAS_VADER` flags with offline fallbacks |
| No hardcoded secrets in provider code | All provider secrets read from env vars |

### Confirmed gaps

| Gap | Severity |
|---|---|
| Payment credentials in plaintext at rest | CRITICAL |
| 3× f-string SQL injection (migration, key rotation, analytics) | HIGH |
| SSRF in 4 providers (no `require_safe_url()`) | HIGH |
| Unauthenticated `websocket_user` broadcast endpoint | HIGH |
| 100+ silent excepts, including AML screening, tax calc, FX revaluation | HIGH |
| Hardcoded encryption/audit keys in 75 root-level `health_test_*.py` files | HIGH |
| MFA **not enforced** for admin/employee roles — the architecture test only checks that MFA code exists | HIGH |
| CAPTCHA silently disabled without `TURNSTILE_SECRET_KEY` | MEDIUM |
| `cors_origins` defaults to `http://localhost:3000,http://127.0.0.1:3000` | MEDIUM |
| Rate limiting `RATE_LIMIT_ENABLED=false` by default and bypassed in test mode | MEDIUM |
| Payment idempotency key optional on 3 paths | MEDIUM |
| Permission audit log has WORM intent but **no DB-level append-only enforcement** | MEDIUM |
| PCI-DSS middleware logs full request details at INFO | MEDIUM |
| No dependency-scanning CI step | HIGH |
| 16 `_tmp_*.py` / `_audit_boot_check.py` debug scripts with direct DB access remain in `backend/` root | MEDIUM |
| No circuit breaker or retry policy in **any** of ~55 providers; `retry_call` in `_helpers.py` is unused | HIGH |
| No explicit HTTP timeout in any provider wrapper | MEDIUM |
| No `health_check()` on ~50 of ~55 providers | MEDIUM |

---

## 8. PERFORMANCE & SCALABILITY

| Finding | Priority | Evidence |
|---|---|---|
| **293 SQLAlchemy relationships omit `lazy=`** → N+1 on every collection endpoint | P1 (4 specific P0s) | `domains/*/models/*.py` |
| `Product.cart_items` uses default `lazy="select"` | P0 | `domains/catalog/models/products.py:107` |
| `Order.items` uses default `lazy="select"` | P0 | `domains/orders/models/order_entities.py:67` |
| `Product.variants`, `Product.videos` default lazy | P1 | `products.py:108-112` |
| `ReturnRequest.order` default lazy | P3 | `order_entities.py:176` |
| **OFFSET pagination on the hottest customer path** (product listing) — cursor path already exists but the router does not use it | P1 | `products_service.py:305` vs `:287-303` |
| OFFSET pagination on customer order history | P2 | `order_engine.py:1009` |
| Product search `ilike '%q%'` with no `pg_trgm` GIN index → sequential scan | P2 | `products_service.py:248` |
| `image/avif` absent from Next.js formats (WebP only) | P1 | `next.config.ts:19` |
| No `blurDataURL` on product images → CLS | P1 | `ProductCard.tsx:141-151` |
| Read replica engine built but **never wired** into any router | P2 | `infrastructure/database/database.py:360` |
| `asyncpg` `statement_cache_size=0` not set | P3 | `database.py:200-217` |
| Celery `retry_backoff_max=300s` vs 8s target | P2 | `jobs/celery_app.py:87` |
| Payout/reconciliation tasks have no `rate_limit`/`concurrency_limit` → concurrent payout sweeps | P3 | `celery_app.py:86-189` |
| `log_retention_days` (default 30) defined but never enforced — size-based rotation only | P2 | `logging_config.py:138-142` |

---

## 9. DEPENDENCY & SUPPLY CHAIN

### Forbidden packages present in `backend/requirements.txt`

| Package | Present | Canonical replacement |
|---|---|---|
| `psycopg2-binary==2.9.12` | yes (with real imports) | `asyncpg==0.31.0` |
| `requests==2.34.2` | yes (imported in `scripts/_debug/_smoke.py`) | `httpx==0.28.1` |
| `prometheus-client==0.26.0` | yes (imported in `infrastructure/valkey/client.py:22`, `infrastructure/observability/metrics.py:1`) | `prometheus-fastapi-instrumentator` |
| `python-magic==0.4.27` | yes (declared, no imports) | `puremagic==2.2.0` |
| `pytz==2026.3.post1` | yes | `zoneinfo` + `tzdata 2025b` |
| `tzlocal==5.4.4` | yes | `zoneinfo` |
| `paypalrestsdk`, `paypalcheckoutsdk` | yes (imported in `providers/payments/paypal.py:33,37`) | direct REST via `httpx` |

### Version mismatches

**Backend:** `fastapi` 0.115.2 vs 0.141.x · `sqlalchemy` 2.0.51 vs 2.0.52 · `alembic` 1.18.5 vs 1.19.1+ · `pydantic-settings` 2.7.1 vs 2.9.1+ · `celery` 5.4.0 vs 5.5+ · `stripe` 15.3.1 vs 15.5.1 · `prometheus-fastapi-instrumentator` 7.1.0 vs 8.1.0+ · `sentry-sdk` 2.66.1 vs 2.68.1 (missing `[fastapi]` extra) · `uvicorn` 0.51.0 vs 0.35.0+ · `starlette` **unpinned**

**Web:** `next` 16.3.4 vs 16.3.5 · `zod` **3.25.76 vs 4.3.6 (major drift)** · `framer-motion` 12.43.0 vs 13.2.0+ · `@stripe/react-stripe-js` 5.6.1 vs 6.9.0 · `@hookform/resolvers` 5.9.1 vs 5.2.2 · `react-hook-form` 7.89.0 vs 7.84.0 · `zustand` 5.0.15 vs 5.0.14 · `tailwind-merge` 3.7.0 vs 3.5.0 · `dompurify` 3.4.16 vs 3.4.0 · `jose` 6.2.12 vs 6.2.10
**Missing web packages:** `next-intl@4.14.2`, `@sentry/nextjs@9.x`, `sharp@0.35.4`, `motion@13.2.0+`

**Mobile:** `expo` ~57.0.9 (lockfile 55.0.27) vs 57.0.20+ · `react-native` 0.81.4 (lockfile 0.83.2) vs 0.86.3 · `react` 19.1.0 vs 19.2.8
**Missing mobile packages:** `lucide-react-native@0.563.0`, `expo-secure-storage@14.2.3`, `react-native-maps@1.29.0`

**Infrastructure drift:** `python:3.11-slim` vs required `3.13-slim` · dev `postgres:18-alpine` vs documented `16-alpine` · frontend Dockerfile uses `npm ci --legacy-peer-deps` instead of `pnpm install --frozen-lockfile` · root `package.json` scripts invoke `npm run` despite "Do NOT use npm or yarn" · **no SBOM** (Syft/CycloneDX) anywhere.

**Declared-vs-imported mismatch (build-breaking):** production imports `from fastapi_limiter_valkey import RateLimiter` (`infrastructure/security/rate_limiter.py:24`) but `fastapi-limiter-valkey` is **absent from `requirements.txt`** while the forbidden `slowapi==0.1.10` and `limits==5.8.0` are declared. Likewise `uvloop` and `httptools` (documented Uvicorn deps) are absent, and `pybreaker==1.4.1` (documented circuit breaker) is absent — which explains the "no circuit breaker anywhere" provider finding.

---

## 10. FEATURE STACK

| Metric | Count |
|---|---|
| Feature atoms catalogued | 231 |
| Tier 1 (brief) / Tier 2 (deep) | 211 / 20 |
| **Orphan features** (in catalog, never gated by any `require_feature()`) | **68** |
| Launch-critical features | 20 |
| Domains without dedicated feature tests | 9 of 17 (`accounts`, `suppliers`, `customers`, `hr`, `analytics`, `country`, `governance`, `payments`, `media`) |
| `_FEATURE_STACK.md` claims | ~495 (doc counts routes, catalog counts permission atoms) |

Orphan concentration: `accounts` 24, `governance` 14, `finance` 14, `comms` 13, `security` 7, `hr` 7, `country` 3, `customers` 2, `media` 2.

An RBAC atom that exists but is never enforced on any route is a permission that exists only on paper. Combined with `accounts.user.delete` being documented LIVE while having no router gate, and `coins.manage` documented as a customer feature while `_ROLE_FEATURES` assigns it to admin, the feature-gate layer is not yet trustworthy as an authorization control.

---

## 11. ANTI-PATTERN FOOTPRINT

1,847 occurrences across 20 categories. The largest by volume and severity:

| Category | Occurrences | Blocker | Note |
|---|---|---|---|
| Magic string | 300+ | no | `"Module not yet created"` alone appears ~100+ times |
| Wildcard / unused import | 200+ `__init__.py` files | no | ruff F403 not enforced |
| Empty handler (`pass`) | 191 | no | should fail closed |
| **TODO-only implementation** | 185 across 28 files | **yes** | `governance/services/admin/admin_service.py` alone has ~120 |
| **Wrong type for money (float)** | 150+ | **yes** | Law 19 |
| **Silent except** | 100+ | **yes** | no logging, no re-raise |
| Commented code | 120+ | partial | `admin_service.py` has ~100 commented import lines |
| Orphan route | 11 files | **yes** | guaranteed 404s |
| Not-wired event handler | 25 | **yes** | governance subscribers |
| Missing idempotency | 3 payment paths | **yes** | webhook ingress + payout sweep |
| Default masks failure | 6 critical defaults | **yes** | `APP_ENV`, `VALKEY_URL`, `CELERY_BROKER_URL`, `FRONTEND_URL` all default rather than fail |
| Stub function (`NotImplementedError`) | 7 across 5 files | partial | `_validate_faceid` raises unconditionally |
| Phantom reference | 10 | partial | cross-domain FKs with no port |
| Not-wired feature gate | 5 | partial | endpoints return `"TODO: ... not yet wired"` |
| Not-wired port | 3 | partial | `CountryStaffAssignment` missing from `country.ports` |
| TODO without ticket | — | partial | Law 62 |
| Dead branch | 3 | no | |

Root-level hygiene: **75 `health_test_*.py` + 15 `_tmp_*.py` + `_audit_boot_check.py` + `run_tests.ps1` + `run_tests.sh`** at `backend/` root — Law 27 violation and a standing project constraint (use `scripts/run-pipeline.ps1` only).

---

## 12. CONTRADICTIONS BETWEEN CANONICAL DOCS AND CODE

37 contradictions harvested; **9 are completion blockers, 16 partial**. Highest impact:

| # | Canonical says | Code says | Blocker |
|---|---|---|---|
| CONTRAD-001 | 5 modules | 6 (`modules/finance`) | yes |
| CONTRAD-002 | payments = provider concern only | `domains/payments/` is a full domain | yes |
| CONTRAD-005 | FastAPI 0.141.x | 0.115.2 (25+ releases behind) | yes |
| CONTRAD-016/036 | `fastapi-limiter-valkey` | declared as `slowapi`+`limits`; canonical package absent from requirements | yes |
| CONTRAD-020 | No float for money | `vat_rate: float`, `zozi_commission_rate: float` | yes |
| CONTRAD-024 | Zod 4.3.6 | `zod ^3.25.76` (major-version drift — different validation semantics and error shapes) | yes |
| CONTRAD-029 | 5 modules, no standalone `hr` | `next.config.ts:51-53` rewrites `/hr/*` → non-existent backend route | yes |
| CONTRAD-034 | one router per module | `modules/employee/routers/hr.py` (file) is shadowed by `hr/` (package) | yes |
| CONTRAD-003 | `media` has no dedicated domain | `domains/media/` is a full domain package | partial |
| CONTRAD-019 | `DEFAULT_COUNTRY` = US | `default_country = "AE"` — needs a user decision | partial |
| CONTRAD-030/031 | Python 3.13, Postgres 16 | `python:3.11-slim`, `postgres:18-alpine` | partial |

---

## 13. INTERNAL CONFLICTS INSIDE THE AUDIT CORPUS

The audit does not fully agree with itself. These must be resolved before any remediation plan is executed, or work will be done against the wrong premise.

| # | Conflict | Sources |
|---|---|---|
| C1 | **Alembic head count**: "5 heads" vs "62 divergent migration heads" | `logs/phase0_results.md` + `07_tables_fields.md` + `27_project_completion_blockers.md` say **5**; `06_database.md` DB-001 says **62** |
| C2 | **Law 49**: laws audit reports "No violation — Alembic history is linear; merge migration exists" | `09_laws.md:71` contradicts `06_database.md`, `07_tables_fields.md`, `logs/phase0_results.md` and `27_project_completion_blockers.md`, all of which report 5 heads |
| C3 | **Law 45 (N+1)**: laws audit reports "No violation — all relationships use `lazy=selectin` or `joined`" | `09_laws.md:67` contradicts `06_database.md` (293 relationships without `lazy=`) and `19_performance.md` |
| C4 | **Law 21 (timestamps)**: laws audit reports "No violation — `created_at`/`updated_at` use `server_default=func.now()`" | `09_laws.md:43` contradicts `07_tables_fields.md` (150 tables use Python-side `default=_utcnow`) |
| C5 | **Law 34 (parameterized SQL)**: laws audit reports "No violation" | `09_laws.md:56` contradicts `18_security.md` SEC-002/003/004 (3 P0 f-string SQL injections) |
| C6 | **Law 41 (WebSocket auth)**: laws audit reports "No violation — `main.py:257` verifies `expected_type='access'`" | `09_laws.md:63` contradicts `05_wiring.md` WIRE-001 (`comms.py:138` accepts without JWT) — both can be true if only some WS routes are covered, but the laws audit does not distinguish them |
| C7 | **Domain count**: "17 domains, extra = media + payments" vs "payments is a 17th domain" | `09_laws.md:34` vs `01_architectural.md` ARCH-002 |
| C8 | **Feature stack P0/P1 count = "0 (all resolved or in-progress)"** | `03_FEATURE_STACK_DRAFT.md:887-889` directly contradicts 46 P0 findings and 9 Phase-0 blockers elsewhere in `_audit`. This statement is sourced from a prior session digest and appears stale. **Do not rely on it.** |
| C9 | **Log volume mismatch**: `04_operational.jsonl` has 1 record while `04_operational.md` reports 10 findings; `19_performance.jsonl` has 1 record while the dimension reports 9 findings | `logs/` vs `dimensions/` — some JSONL logs are incomplete |
| C10 | **Money-float cluster membership**: `03_logical.md` lists LOGIC-016 (state machine) as a member of `CLUSTER-float-money` | `03_logical.md:90` — LOGIC-016 is about a `cancelled → refunded` transition, not float |
| C11 | **`_audit/00_README.md` file index is stale** — it lists only 3 files and claims "Phase 0 COMPLETED, 0 PASS / 9 FAIL" for Phase 0.5, omitting the 12 dimension reports that now exist | `00_README.md:9-18` |
| C12 | **CI/CD**: `04_operational.md` OPS-002 says "No `.github/workflows/` directory; no CI/CD pipeline exists", but `02_technological.md` cites `.github/workflows/ci.yml` as an existing file | Both cannot be accurate; the truthful reading is "a CI test workflow exists, a deploy/CD pipeline does not" |
| C13 | **`modules/finance` load status**: CONTRAD-001 calls it "a 6th module … with its own router (`cash_management.py`)", while ARCH-011 proves that router has no decorators and is **not registered** by `main.py:_load_routers()` | `07_CONTRADICTIONS.md` vs `01_architectural.md` |
| C14 | **Mobile Stripe strategy**: `@stripe/stripe-react-native ^0.50.0` installed but `checkout.tsx:94` uses a web redirect; simultaneously `@tap-as/sdk-react-native`, `@paytabs/react-native-paytabs`, `@thawani/rn-sdk` are dynamically `require()`d but **not in `package.json`** | `15_frontend_mobile.md` MOB-007/008 — these three will crash with "module not found" at runtime |
| C15 | **`country_code` count**: `07_tables_fields.md` states 42 user-facing tables lack `country_code`; `09_laws.md:42` states "All `country_code` columns use `String(2)`" and marks Law 20 compliant | The two are about different things (existing columns' type vs missing columns) but the laws audit never surfaces the 42-table gap |

**Recommended action:** reconcile C1–C15 before sequencing remediation. C2, C3, C4, C5 and C8 in particular would let a remediation plan declare work "already done" that is not.

---

## 14. REMEDIATION SEQUENCING

Ordered by dependency, not by severity alone. Each wave is a prerequisite for the next.

### Wave 0 — Make the application boot completely and truthfully
*Unblocks every other wave. Small, well-understood, mostly S-effort items.*

1. Fix `backend/__init__.py` package import (BLOCKER-001).
2. **Restore the `orders` and `logistics` routers** — resolve `bulk_archive_entities` in `domains.governance.ports`. Two domains currently have no HTTP surface.
3. Merge the 5 Alembic heads into one linear chain (BLOCKER-007 / DB-001 / TF P0).
4. Fix `migration_helpers` import so `alembic heads` runs (DB-002).
5. Align `settings.database_url` ↔ `DATABASE_URL` and `valkey_url` ↔ `VALKEY_URL`, or correct `TECHNOLOGY_STACK.md` (BLOCKER-002).
6. Bring up Valkey (`docker compose up valkey`) and confirm RLS policy installation succeeds on Neon instead of being skipped (BLOCKER-003).
7. Fix the 6 broken test imports (BLOCKER-004).
8. Re-enable OpenTelemetry (`infrastructure/utils/tracing` missing).
9. Delete `modules/finance/routers/cash_management.py` or convert it into a properly decorated, registered router (ARCH-011).
10. Delete the 91 root-level temp/debug files and `run_tests.ps1`/`run_tests.sh` (ARCH-003/004, SEC-009, Law 27) — this also removes the hardcoded `SECRET_KEY`/`FIELD_ENCRYPTION_KEY`/`AUDIT_CHAIN_KEY` exposure.

### Wave 1 — Stop the bleeding: security and money
*Highest business risk. Nothing here should wait for Wave 2.*

11. Encrypt `secret_key`, `webhook_secret`, `public_key`, `credentials` with AES-256-GCM (`infrastructure/security/field_encryption.py`); migrate existing rows. **(SEC-001, FEAT-005, FEAT-022)**
12. Add JWT verification with `expected_type="access"` to `websocket_user`. **(WIRE-001)**
13. Replace all f-string SQL with `sa.text()` + bound parameters. **(SEC-002, SEC-003, SEC-004)**
14. Wrap every outbound HTTP call in `require_safe_url()`. **(SEC-005)**
15. Make `screen_supplier` return `cleared=False` on exception — never `True`. **(LOGIC-008)**
16. Add `logger.warning(..., exc_info=True)` to all 100+ silent excepts in financial paths; roll back on FX journal failure. **(AP-004, LOGIC-009, LOGIC-014)**
17. Convert `vat_rate`, `zozi_commission_rate` and all monetary Pydantic fields to `Decimal`; add a ruff rule that fails CI on float-for-money. **(CONTRAD-020, AP-005, LOGIC-001..013, FEAT-001..003, FEAT-009, FEAT-010)**
18. Wire `claim_inventory` / `release_inventory` into order confirm/cancel/refund. **(FEAT-004, FEAT-025)**
19. Make `idempotency_key` required on `PaymentIntentRequest` and on webhook ingress + payout sweep. **(LOGIC-015, AP-017)**
20. Gate refunds behind an explicit `refund` intent with `finance.ledger.write`. **(FEAT-011)**
21. Compute the WORM chain hash before INSERT; remove the post-INSERT UPDATE. **(SEC-006, AP-010)**
22. Pin `starlette`; add dependency scanning to CI. **(TECH-030, FIND-09-011)**

### Wave 2 — Make the event spine real
*The single largest structural change. Prerequisite for automatic commerce.*

23. Implement the finance subscribers: commission accrual on `payment.confirmed`, reversal on `payment.refunded`, settlement journal on `order.completed`. **(ARCH-014, LOGIC-006)**
24. Implement the order lifecycle subscribers and **register them** in `lifespan.py`. **(LOGIC-018)**
25. Emit post-commit: `publish_order_created`, `PayoutCreated`, `RefundPosted`, `ShipmentCreated`, `JournalEntryPosted`, `CustomerRegistered`, `SupplierRegistered`, `ProductCreated`. **(CHAIN-001..007)**
26. Convert event publication to `after_commit` hooks. **(WIRE-003)**
27. Implement or un-register the 25 governance stub handlers. **(AP-018)**
28. Replace `time.sleep()` and `run_until_complete()` with `asyncio` primitives. **(WIRE-004, LOGIC-007)**
29. Implement multi-supplier `Shipment` splitting in `create_order`. **(CHAIN-001)**
30. Implement or remove the 11 orphan routers and the 7 `NotImplementedError` stubs. **(AP-009, AP-002)**

### Wave 3 — Data integrity and RLS

31. Align the RLS policy variable name (`app.current_country_code` vs `app.country_scope`) and pick one implementation. **(DB-005, DB-006, WIRE-002)**
32. Add `country_code` to the 42 user-facing tables. **(TF-001)**
33. Create ORM models for the 14 unmapped tables. **(TF-002)**
34. Apply the `media` schema migration. **(TF-003)**
35. Add `lazy="selectin"` to all 293 relationships. **(DB-003, PERF-001..009)**
36. Add `__table_args__` schema to `payroll_records` and `employee_trainings`. **(TF-006)**
37. Sync the 13 orphan columns and apply the 17 pending column migrations. **(TF-007/008)**

### Wave 4 — Engineering gate and supply chain

38. Populate `uv.lock` and `pyproject.toml [project.dependencies]`; migrate Dockerfile + CI from pip to `uv`. **(TECH-001..005)**
39. Remove the 6 forbidden packages and the 2 PayPal SDKs; add the missing canonical packages (`fastapi-limiter-valkey`, `uvloop`, `httptools`, `pybreaker`). **(TECH-008..019, CONTRAD-016/018/036)**
40. Reconcile all backend, web and mobile versions with `TECHNOLOGY_STACK.md` — 53 findings total. **(TECH-020..049)**
41. Base image `python:3.13-slim`; frontend Dockerfile on pnpm; add `packageManager` field. **(TECH-006, TECH-050/051)**
42. Generate SBOM via Syft/CycloneDX in CI. **(TECH-052/053)**

### Wave 5 — Operational readiness

43. `/health/deps` must return **503** when any critical dependency is down; add R2 to the health checks. **(OPS-001, OPS-008)**
44. Build `.github/workflows/deploy.yml`: pre-deploy `alembic upgrade head`, `/health/ready` gate, automatic rollback. **(OPS-002)**
45. Write `docs/runbooks/deployment.md`, `rollback.md`, `migration_on_deploy.md`. **(OPS-003)**
46. Add circuit breaker + retry + explicit timeout to all ~55 providers. **(08_providers F1/F2)**
47. Replace raw `os.getenv()` with typed `settings.*` in payment / geography / SMS providers. **(OPS-004..006)**
48. Explicit `--workers` for gunicorn; per-task `concurrency_limit` for payout and reconciliation. **(OPS-007, OPS-010)**

### Wave 6 — Frontend, mobile, performance

49. Fix the 60+ TypeScript errors; fix 8335 ruff errors (`ruff check . --fix` clears 2954 immediately). **(BLOCKER-005/006)**
50. Keyset pagination as default on product listing and order history. **(PERF-006/007)**
51. `pg_trgm` GIN index on `catalog.products.name`. **(PERF-008)**
52. `image/avif` + `blurDataURL` pipeline. **(PERF-004/005)**
53. Re-enable OTA updates; install `expo-updates`. **(MOB-001/002)**
54. Resolve the mobile payment strategy contradiction; install or remove the Tap/PayTabs/Thawani wrappers. **(MOB-007/008)**
55. Implement native social sign-in (Google, Facebook, Apple). **(MOB-005/006)**
56. Write Detox specs for login, browse-to-cart, checkout. **(MOB-009)**
57. Add offline detection + mutation queue via NetInfo. **(MOB-003/004)**

### Wave 7 — Authorization and test depth

58. Gate or retire the 68 orphan feature atoms. **(feature stack)**
59. Enforce MFA for admin and employee roles at the authentication layer. **(SEC-018 correction)**
60. Add feature tests for the 9 uncovered domains; execute the Playwright money-path specs. **(feature stack, FEAT-042)**
61. Add architecture tests for import laws, ports coverage, Law 70 gates. **(FIND-09-005)**
62. Add CI gates: `alembic heads` == 1, no `relationship()` without `lazy=`, no forbidden imports, no float-for-money, `country_code` presence.

---

## 15. WHAT IS GENUINELY STRONG

Not everything is broken. The following are real assets that should not be lost in remediation:

| Asset | Evidence |
|---|---|
| Frontend builds cleanly and fast | Next.js 16.3.4 compiled in 13.9s, **151 static pages** generated |
| Docker Compose topology is complete and valid | 10 services incl. 4 specialised Celery workers, pgbouncer |
| Failure-path coverage across all 7 chains | **26 of 26** required failure paths have cited code evidence |
| CHAIN-001 rollback is verified | `_rollback_order_creation` exists and is called on exception |
| Provider import isolation (Law 31) | **PASS** — zero forbidden imports across ~55 providers |
| JWT type-claim verification | Implemented and tested (`infrastructure/security/auth.py`) |
| CSRF, security headers, password-length cap | All present and tested |
| Login rate limiting fails closed | 5 attempts / 60s against Valkey |
| AI graceful degradation | `HAS_*` flags with working offline fallbacks |
| No hardcoded secrets in provider code | All provider secrets come from env vars |
| Event classes and subscriber skeletons exist | The structure is in place — only the bodies are missing |
| Database schema breadth | 343 tables with per-domain schemas, soft delete, audit columns |
| Feature catalog is centralised | 231 atoms single-sourced in `rbac/catalog.py`, validated by 3 architecture tests |
| Architecture test suite exists and collects | 356 tests, 4.09s |

---

## 16. LIMITS OF THIS COMPILATION

- **Scope:** compiled exclusively from `_audit/**`. No source file, canonical doc (`_most_imp_docx/**`), or configuration file was read or modified during this compilation. Statements about canonical intent are therefore reported *as the audit reports them*, not independently verified.
- **Point-in-time:** all evidence is from 2026-10-01. Any fix already merged after the audit is invisible here.
- **Unverified claims (INFERRED, confidence ≤ 4):** FEAT-018, FEAT-020, FEAT-026, FEAT-030, FEAT-033, FEAT-034, FEAT-035, FEAT-038, FEAT-041, FEAT-042; TECH-030. These are explicitly marked `Truth level = L1 / INFERRED` in their source tables and must not be treated as confirmed.
- **Not assessed at all:** no load testing, no browser-level visual or functional verification of the 151 generated pages, no accessibility audit, no Lighthouse/CWV measurement, no penetration test, no staging-environment verification, no disaster-recovery drill, no backup/restore verification.
- **Lost working-tree evidence:** 19 dimension reports (`00_boot_smoke_test.md`, `10_migrations.md`, `11_environmental.md`, `12_tests*.md`, `13_dev_to_prod*.md`, `14_frontend_web.md`, `17_code_file_management.md`, `20_observability_resilience.md`, `21_contradictions.md`, `22_anti_patterns.md`, `23_code_intent.md`, `24_browser_behavior.md`, `25_ai_drift.md`, `26_code_alignment.md`, `28_supply_chain_security.md`, `config_verification.md`, `suppliers.md`) plus 11 root artefacts and `_audit/resolver/` are tracked at HEAD but **absent from disk**. Their content was recoverable but was not consulted for this compilation. Dimensions 10–14, 17 and 20–26 are therefore **unrepresented here** — not because they were never audited, but because their reports are missing. Recover with `git restore`. **This materially caps confidence: migrations, environmental config, frontend web, browser behaviour and supply-chain dimensions are under-covered in this document.**
- **Concurrent writer:** another process wrote `_audit/DIMENSION_INDEX.md` and rewrote `_audit/00_README.md` at 23:58 on 2026-10-01, during this compilation. `_audit/**` is a shared, moving target; figures here may already be stale relative to those artifacts.
- **This file overwrote a committed predecessor:** see the provenance warning in the header and §3.4. The pre-existing 18-condition gate was recovered, but the original 40-line artifact was replaced rather than superseded in place.
- **Possible stale claim — "no CI/CD pipeline":** §1 and Wave 4 assert that no CI/CD pipeline exists, on the strength of the dimension audits. However, the working tree contains **untracked** `.github/workflows/ci.yml`, `rollback.yml`, `router-generation.yml` and `schema-audit.yml`. These were *not read* (read-only `_audit/**` constraint) and are untracked, so they may be uncommitted in-progress work rather than a functioning pipeline — but the assertion should be re-verified against those files before it is relied upon. Treat "no CI/CD pipeline" as **audit-sourced and unconfirmed**, not established fact.
- **Uncommitted remediation is landing concurrently:** the working tree holds ~490 modified/deleted files outside `_audit/**` (including `backend/main.py`, `backend/lifespan.py`, `backend/config.py`, every `subscribers.py`, and new migrations `2026_09_30_0007` and `2026_10_01_0001`). Some audit blockers may already be fixed in uncommitted work. `backend/.env` also appears present, which is consistent with the plaintext-credential finding. This report describes the **audited state**, not necessarily the current state of the working tree.
- **Log completeness:** several `logs/*.jsonl` files contain fewer records than their corresponding dimension reports (see §13 C9), so the JSONL stream cannot be used as a complete evidence index.
- **Contradictions:** 15 internal conflicts in the audit corpus are documented in §13 and unresolved. This document reports both sides rather than silently choosing one.

---

## 17. BOTTOM LINE

The platform should **not** go to production.

The two facts that decide this are not the 46 P0 findings or the 8335 lint errors — those are expensive but tractable. They are:

1. **Two of the five business modules do not register at boot.** `orders` and `logistics` fail to import because `bulk_archive_entities` is missing from `domains.governance.ports`. Order placement, order history, returns, refunds, shipment creation and tracking are unreachable in the audited environment. This is recorded as an "Observed but not changed" note, not as a finding.

2. **The event layer is entirely non-functional.** Every subscriber in the codebase is a stub; no service publishes its declared events; inventory is never claimed or released; commissions are never accrued; settlements are never posted; refunds have no rollback. All seven critical business chains are PARTIAL, and the audit's own cross-cutting finding is that this is *systematic*, not incidental.

Compounding both: **RLS policy installation is skipped on Neon** — so cross-country data isolation, which is the platform's central multi-market premise, is not enforced in the database at all. Combined with **payment gateway credentials stored in plaintext** and **country-scoping broken on 42 user-facing tables**, a single authorization flaw has the potential to expose or corrupt financial data across every market simultaneously.

Start at Wave 0. Nothing else can be validated until the application boots completely and the router set is provably whole.