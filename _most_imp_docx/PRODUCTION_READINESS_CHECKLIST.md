# ZOZI -- Production Readiness Checklist

> **Purpose.** This is the single authoritative checklist for declaring ZOZI production-ready.
> After each forensic audit pass, update the `Status` and `Last verified` columns in the tables below,
> then refresh the **Summary Dashboard** and **Production Readiness Gate**. The result is a live
> view of what is resolved, what remains, and what still blocks production.
>
> **How to use after audit completion.**
> 1. For each check below, set `Status` to PASS / FAIL / DEFERRED / UNVERIFIABLE based on audit evidence.
> 2. Record the evidence path/command in the `Evidence` column.
> 3. Update the **Summary Dashboard** counts.
> 4. Update the **Completion Blockers** table with remaining `project_completion_blocker = yes` findings.
> 5. Update **Production Ready:** YES / NO and the assessment date.
> 6. Do not mark PASS without evidence; failures must cite the exact finding ID or file:line.

---

## Run History

| Run | Date | Status | Key Changes |
|-----|------|--------|-------------|
| 1 | 2026-10-01 | `phase_incomplete_timeout` | Initial audit: 728 findings, 72 P0, 241 completion blockers |
| 2 | 2026-10-01 | `re_verification_complete` | Re-verified 28 dimensions, 100+ sub-agents launched, logging system implemented, 19 out-of-scope files cleaned up |
| 3 | 2026-10-01 | `live_verification_complete` | Live project verification: backend fails to boot (ImportError get_user_by_id), frontend build fails (missing Timer export), pytest 4509 collected / 17 errors, architecture tests 31/32 pass, python-jose absent, requests absent, redis absent, pytz/tzlocal absent, pnpm-lock.yaml present, tests/architecture/ present, .github/workflows/ present, POSTGRES_PASSWORD set, alembic.ini missing |
| 4 | 2026-10-01 | `features_dimension_complete` | Features dimension audit: 42 findings (8 P0, 14 P1, 12 P2, 8 P3), 10 new completion blockers (FEAT-001, FEAT-002, FEAT-003, FEAT-004, FEAT-005, FEAT-009, FEAT-010, FEAT-022, FEAT-025, FEAT-040), float money math, missing inventory claim/release, plaintext payment credentials, archived promotion modules |
| 5 | 2026-10-01 | `forensic_audit_complete` | Forensic audit complete: 495 findings (55 P0, 154 P1, 233 P2, 22 P3), 139 completion blockers, 14 dimensions FAIL, launch gate 1 pass / 14 fail / 3 unverifiable, 1,847 anti-pattern occurrences, 37 contradictions, 0 of 7 business chains COMPLETE |
| 6 | 2026-10-02 | `machine_audit_complete_verification_pass` | Rebuilt audit suite `_zozi_audit/` and ran it end-to-end in `--full` mode at commit `6666d435`. 1,764 findings (96 P0 / 764 P1 / 691 P2 / 213 P3), 90 `completion_blocker=yes`, 0 crashed checks. 98 P0/yes-blocker claims independently re-verified by 10 sub-agents: 49 confirmed, 10 partial, 39 false-positive/inflated, 9 wrong-location or wrong-number. |
| 7 | 2026-10-02 | `audit_extended_compiler_added` | Added 5 extension scanner modules (design/colour, interaction robustness, feature & taxonomy, workflow/QA/automation, data management) — registered checks 59 → 79 — plus a `Recommendation` stream (19 items) and Phase B `zozi_compile.py`, which emits an ordered 6-wave, work-package remediation plan. 1,777 findings, 89 blockers, 0 crashed checks. All new detection rules re-verified by 3 independent sub-agents; 10 false-positive rules found and fixed. |
| 8 | 2026-10-02 | `wave0_sample_remediation_and_reverification` | Fixed 3 real defects (1 line each) and re-verified with a reverted-state baseline. Pre-flight gates 4 FAIL → 2 FAIL: **test collection PASS** (4,728 tests, 0 errors) and **alembic heads PASS** (single head `20261001_0001`). Architecture suite now *executes* (was aborted at collection) exposing **50 failing law tests across 25 files** that were previously invisible. 0 crashed checks; 1,660 findings. |
| 9 | 2026-10-02 | `http_layer_and_settings_contract_added` | Closed two coverage gaps the audit could not see: **no HTTP dimension existed** (nothing ever inspected a real response) and **no settings-contract check** (undefined `settings.*` reads only fail when that path executes). Registered checks 79 → 82. Live probe boots the app (378 s) and issues 12 real HTTP exchanges. 1,695 findings, 92 blockers. |
| 10 | 2026-10-02 | `falsification_gate_added` | Added `zozi_verify.py`: every finding is adjudicated CONFIRMED / FALSE_POSITIVE / ALREADY_FIXED / WRONG_LOCATION / UNVERIFIABLE, and `zozi_compile.py` now gates on it — 63 findings dropped, only 235 independently-confirmed findings become fix steps, 1,390 demoted to verification tasks. Measured FP+wrong = 6.1%, P0 noise = 6.3%. `PLAN.md` §11 records the outstanding gate: `confirmed_pct` 13.9% must reach 60% before waves 2–3 are safe for autonomous execution. |

---

## Run 10 — the falsification gate (`zozi_verify.py`) (2026-10-02)

### The gap this closes

`zozi_compile.py` could **sequence** findings but never tried to prove them
wrong. The project's own prior run had already measured that cost: its
`verify_verdicts.py` adjudicated 1,359 findings and returned **910 REAL, 160
FALSE_POSITIVE, 265 ALREADY_FIXED, 23 BLOCKED** — **31% not actionable as
stated**. The v3 audit inherited no equivalent gate, so its plan inherited
unmeasured noise.

### Measured result — 1,695 findings adjudicated

| Verdict | Count | Share |
|---|---|---|
| CONFIRMED (independently re-derived) | 235 | **13.9%** |
| UNVERIFIABLE (consistent, not proven) | 1,310 | 77.3% |
| WRONG_LOCATION | 79 | 4.7% |
| FALSE_POSITIVE | 25 | 1.5% |
| ALREADY_FIXED | 46 | 2.7% |

- **False-positive rate (FP + wrong location): 6.1%**
- **Not actionable as stated: 8.8%**
- **P0 set: 111 findings, 26 confirmed, 6.3% noise** — so **85 P0 claims are
  unproven**, which is materially better than the prior run's 31% noise but is
  still not a green light.

### What the gate enforces in the plan

| Rule | Effect |
|---|---|
| `FALSE_POSITIVE` / `ALREADY_FIXED` | **dropped from every wave**, listed in a Rejected appendix with counter-evidence so the exclusion is auditable — 63 findings removed |
| Not `CONFIRMED` | demoted to a **verification task in wave 4**, regardless of the priority the audit assigned |
| `CONFIRMED` only | eligible to become a `fix` step — **235 steps** |
| No `verdicts.jsonl` | compiler warns twice and emits **zero** fix instructions (verified) |

Result: 1,695 findings → 63 rejected, 235 confirmed fix steps, 1,390 verification
tasks. `PLAN.md` §11 records the one outstanding gate: raise `confirmed_pct`
above 60% before waves 2–3 are released for autonomous execution.

### Answer to "can an AI follow this plan?"

**Wave 0 and the 235 confirmed steps: yes.** Everything else: no — and the plan
says so on its first page rather than burying it. The prior run's own verdict
distribution shows why caution is correct: its `28_supply_chain_security` agent
returned 3 REAL against 14 FALSE_POSITIVE, and its `16_features` agent 28 against
16. A dimension average hides that; only per-finding adjudication does not.

### Three defects in the gate itself, found and fixed

1. **340 spurious `WRONG_LOCATION`** — 311 findings cite a *directory*
   (`backend/modules/finance`), which the gate treated as a missing file.
2. **A line drift was claimed as a refutation.** Tokens elsewhere in a file do
   not disprove a finding, so those 261 cases are now `UNVERIFIABLE` with the
   drift flagged, not `WRONG_LOCATION`.
3. **`Compiler.__init__` crashed on the no-gate path** because `self.warnings`
   was assigned after the loader that writes to it. The intended failure mode
   (warn loudly, emit no fixes) is now what actually happens.

**Verdict unchanged: NOT PRODUCTION READY — 92 blockers.** What changed is that
the number is now measured rather than assumed, and the plan knows which 13.9% of
it may be acted on.

---

## Run 9 — HTTP layer + settings contract (2026-10-02)

### The reported CSP/h11 bug does not exist

The claim under review was *"h11 refuses a semicolon inside a header value"*,
with a proposal to emit multiple `Content-Security-Policy` fields instead.
**Tested and refuted.** A real uvicorn server returned:

```
HTTP/1.1 200 OK
content-security-policy: default-src 'self'; script-src 'self' https://js.stripe.com;
  style-src 'self'; ... base-uri 'self'; form-action 'self'; report-uri /csp-report
```

Semicolons are legal in an HTTP field value (RFC 9110) and h11 serialises them
correctly. The proposed "fix" would have made the policy *less* portable: a
single field is what every CSP consumer reads first. **No change was made to the
CSP emission** — the correct outcome of this investigation was to change nothing.

### What the audit genuinely could not see, and now does

| Gap | Added | Coverage |
|---|---|---|
| No HTTP dimension at all | `zz_integrations/http_probe.py` + `http_response_contract` | Boots the app under a real server, issues **12 real HTTP/1.1 exchanges**, asserts on the bytes returned |
| Header policy hidden behind a down stack | `security_header_policy` (static) | Runs with no server, so header defects are never masked by a dead stack |
| Undefined `settings.*` reads invisible | `settings_contract` | Resolves every `settings.<attr>` read against the fields `Settings` declares |

### New findings (all live-verified, not inferred)

| Finding | Severity | Evidence |
|---|---|---|
| **CORS preflight returns 405** | P0 | `OPTIONS /api/v1/auth/login` and `OPTIONS /health` both answer `405 Method Not Allowed`. Root cause pinned at `backend/middleware/security_headers.py:78` — the OPTIONS branch calls `call_next()` and then decorates the result, so the router has already rejected the verb. **Every cross-origin write from the web app fails in a browser while curl and the in-process ASGI client both pass.** |
| **31 undefined `Settings` attributes** | 12× P0 | `backup_verify_on_create`, `backup_s3_*` (7 more), `smtp_*` (4), `free_shipping_threshold`, `qr_secret_key`, `max_image_dim` and 15 more are read in production code but declared nowhere in `config.py`. `backup_verify_on_create` is the confirmed cause of the startup `AttributeError`. Six were independently re-grepped; all six genuinely absent and genuinely read. |
| `csrf_token` set without `Secure`/`HttpOnly` | P1 | live `Set-Cookie` |
| CSP names `localhost` origins on every route | P1 | live header, all 4 probed routes |
| CSP uses deprecated `report-uri` | P2 | static + live |
| `X-XSS-Protection` still emitted | P2 | removed from all current browsers |
| 4 startup errors logged as "non-critical" | P0 | live server log |
| A single **298-second** query during startup | observation | live server log |

### Three of my own new checks were wrong first time — corrected before shipping

1. `missing_from_middleware` reported 4 headers as absent; the live probe had just **proved** they were sent. Cause: they are applied from a module-level dict in a loop, which literal matching cannot see. Now correctly `[]`.
2. `SEC-csp-missing-directive` claimed `object-src`/`base-uri` were absent. They are present. The finding was spurious and is **gone**.
3. The CORS finding was attributed to `webhook_verification.py` — a stale duplicate assignment overwrote the correct value. Now correctly `security_headers.py:78`.

### Verdict

**NOT PRODUCTION READY — 92 blockers** (was 89). The count rose because two
blind spots became measurable; one P0 CORS defect that breaks all cross-origin
writes in a browser is more consequential than most of what it outranks.

**Next assessment due:** fix `SEC-cors-preflight-static` first — it is a ~5-line
change and it unblocks the browser E2E suite.

---

## Run 8 — sample remediation + before/after verification (2026-10-02)

**Three defects were fixed, each proven with a reverted-state baseline.** A
baseline was produced by inverting the three edits, running the identical
commands, then restoring them — so every number below is measured, not inferred.

| # | Defect | Root cause | Fix | Files/lines |
|---|---|---|---|---|
| 1 | `alembic heads` / `upgrade` cannot run | 8 migrations do `from migration_helpers import …`, but Alembic puts `versions/` on `sys.path`, not the `alembic/` package that holds the module | `prepend_sys_path = %(here)s` in `alembic.ini` (imports rewritten to `alembic.migration_helpers` would be unsafe — `backend/alembic/` shadows the alembic library) | 1 file, +9 |
| 2 | 2 collection errors; whole architecture + security suites aborted | `conftest.py` set `SECRET_KEY` to a 28-char value; `config.py:315` enforces `min_length=32`, so `Settings()` raised at import | test-only secret lengthened to 57 chars | 1 file, +8/−1 |
| 3 | Country scope leaks across pooled connections | `SET` (session-level) instead of `SET LOCAL` (transaction-local), violating Law 5 | `SET LOCAL` + docstring explaining the pooling hazard | 1 file, 1 line |

**Measured before → after**

| Measurement | Before (edits reverted) | After |
|---|---|---|
| `pytest --collect-only` | 4,703 collected, **2 errors**, exit 2 | **4,728 collected, 0 errors**, exit 0 |
| `tests/architecture` | **interrupted at collection, 0 tests ran** | 313 passed, 50 failed, 5 errors (368 ran) |
| `tests/security` | **interrupted at collection, 0 tests ran** | 137 passed, 131 failed, 70 errors (318 ran) |
| `alembic heads` | `ModuleNotFoundError`, exit 1 | 1 head `20261001_0001`, exit 0 |
| App boot (repo root and `backend/`) | 84 routes | 84 routes (unchanged) |

**The 50 architecture and 131 security failures are pre-existing, not
regressions** — they could not have been observed before, because both suites
were aborted at collection. Their causes are circular imports
(`middleware.webhook_verification`, `middleware.orchestrator`, …) and undefined
names (`ShippingRule`), which is why fix #2 was a prerequisite for measuring
anything at all.

**Four measurement bugs in the audit itself were found and fixed during this
pass** — all of the same class as the earlier false-positive work:

1. `pnpm exec tsc` triggered the repo's supply-chain install hook instead of
   running tsc, so the audit reported **"FAIL: 0 TypeScript errors"**. The probe
   now calls `node_modules/.bin/tsc` directly: **119 errors in 29 files**,
   matching independent measurement.
2. Counts were parsed from `stdout_tail`, which elides the middle of long output.
   tsc reported 25 of 119. `ToolResult.full_stdout` is now retained and all count
   parsers read it.
3. The architecture row pasted `Press Ctrl-Break to quit` as the "test result"
   because the run is killed before pytest prints a summary. That state is now
   reported as **INCOMPLETE** (50 failed, 5 errored observed, remainder
   unproven) rather than a misleading FAIL, and the 25 worst law-test files are
   named individually.

**Net effect on the verdict.** Blockers 89 → 86 at the point the gates turned
green; the count then moved again as previously-invisible failures became
visible. Readiness did **not** improve in the way the pass count suggests: two
gates are now honestly green, and 50 law violations that were hidden are now
measurable. `NOT PRODUCTION READY` stands on 89 blockers.

**Next assessment due:** after the architecture suite runs to completion (it
currently hangs — no summary after ~700 s) and the 50 named law tests are fixed.

**Production Readiness Percentage: unchanged at 2.8% — Production Ready: NO**
(three one-line defects out of a 1,660-finding backlog does not move readiness;
it restores the ability to measure it.)

---

## Summary Dashboard

Update this section after each forensic audit pass. The goal is to make remaining work visible at a glance.

| Section | Total | PASS | FAIL | DEFERRED | UNVERIFIABLE | Remaining |
|---------|-------|------|------|----------|--------------|-----------|
| Canonical Document Alignment | 6 | 3 | 2 | 0 | 1 | 0 |
|Technology Stack| 27 | 17 | 4 | 0 | 6 | 0 |
|Architecture| 24 | 5 | 14 | 0 | 5 | 0 |
| Feature Completeness| 10 | 0 | 5 | 0 | 5 | 0 |
|Backend Runtime| 13 | 0 | 7 | 0 | 6 | 0 |
|Frontend Build & Runtime| 9 | 2 | 3 | 0 | 4 | 0 |
|Mobile Build| 7 | 0 | 0 | 0 | 7 | 0 |
|Tests -- Backend| 15 | 2 | 6 | 0 | 7 | 0 |
|Security| 38 | 7 | 16 | 0 | 15 | 0 |
|Database| 27 | 0 | 9 | 0 | 18 | 0 |
|Frontend UI| 18 | 0 | 0 | 0 | 18 | 0 |
|Frontend Workflows| 20 | 0 | 0 | 0 | 20 | 0 |
|Browser Behavioral Tests| 5 | 0 | 4 | 0 | 1 | 0 |
|Performance & Fast Loading| 15 | 1 | 5 | 0 | 9 | 0 |
|Observability & Health| 17 | 0 | 6 | 0 | 11 | 0 |
|Provider Resilience| 15 | 0 | 0 | 0 | 15 | 0 |
|Operations| 19 | 0 | 1 | 0 | 18 | 0 |
|Country Management| 15 | 0 | 1 | 0 | 14 | 0 |
|Tax & Calculations| 14 | 0 | 2 | 0 | 12 | 0 |
|Location / Geography| 8 | 0 | 0 | 0 | 8 | 0 |
|Catalog Management| 18 | 0 | 0 | 0 | 18 | 0 |
|Photo / Video / Media Management| 13 | 0 | 0 | 0 | 13 | 0 |
|Supply Chain Security| 10 | 0 | 2 | 0 | 8 | 0 |
| **Total** | **1764** | **96** | **764** | **691** | **213** | **90** |

> **Run 6 note on this table.** The per-section PASS/FAIL/UNVERIFIABLE split above is still
> carried from Run 5 and was **not** recomputed in Run 6; only the **Total** row was
> refreshed from `_zozi_audit/zozi_forensic_audit.md`. The four columns map to
> P0 / P1 / P2 / P3, and `Remaining` is `completion_blocker = yes`. Recomputing the
> per-section split is outstanding work for the next pass.

**Production Ready:** NO

**Date of last full assessment:** 2026-10-02

**Run 6 forensic audit (machine, evidence-based).** The audit suite at `_zozi_audit/` was
rebuilt to the point where it runs end-to-end in `--full` mode (0 crashed checks across 59
registered checks + 10 pre-flight checks, 604 s, 10 workers) and pinned to commit
`6666d435a947e61ce63cf238439514a248891063`. Totals: 1,764 findings, 96 P0, 764 P1, 691 P2,
213 P3, 90 hard completion blockers, 113 clusters, 6 contradictions, 7 chains audited.

**Pre-flight gate (independently re-run, all 10 rows have real evidence).**

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1 | Boot smoke test | **FAIL** | `backend/infrastructure/observability/metrics.py:1` — `ImportError: cannot import name 'Gauge' from 'prometheus_fastapi_instrumentator.metrics'` (installed 8.1.0 exports only `Counter, Histogram, Info, Summary`). Second, earlier failure: `backend/config.py:315` pydantic `ValidationError` when `SECRET_KEY` < 32 chars or `FIELD_ENCRYPTION_KEY` < 64 chars. **The backend does not start.** |
| 2 | Required env vars | PASS | `.env.example` declares 193; typed settings fields 188 |
| 3 | Database connectivity | PASS | Neon reachable (host/port probed; credentials never logged) |
| 4 | Valkey connectivity | FAIL | `valkey://localhost:6379` — `ConnectionRefusedError` (not running) |
| 5 | Test collection | FAIL | 4,460 tests collected, **20 collection errors** (all from the `config.py:315` `Settings` validation error) |
| 6 | Frontend type check | FAIL | **106** TypeScript errors (`tsc --noEmit`) |
| 7 | Backend lint | FAIL | **7,849** ruff violations (E402=2065, F401=1986, F821=1435, F811=1112, F405=397, E712=305, F403=176, E701=93, F841=89, F822=76, E702=44, E741=24, E401=22, F601=12, E711=6, F541=6, E731=1) |
| 8 | Alembic heads | FAIL | `alembic heads` cannot run — `versions/2026_08_06_0001_add_analytics_audit_columns.py:31` raises `ModuleNotFoundError: No module named 'migration_helpers'`. **The module exists at `backend/alembic/migration_helpers.py`**; the failure is a `sys.path` resolution issue (Alembic puts `versions/` on the path, not `alembic/`). Affects 8 migration files. |
| 9 | Lockfile sync | PASS | `backend/uv.lock` (107 packages) and `frontend/web_app/pnpm-lock.yaml` (5,183 entries) both present |
| 10 | Architecture law tests | FAIL (timeout) | `tests/architecture` suite did not finish in 240 s → the law gates are **UNVERIFIED**, not passing. `test_schema_discipline.py` and `test_model_relocation.py` do not exist. |

**Verification pass (10 sub-agents, 98 P0/yes-blocker claims re-checked against source).**

| Outcome | Count | Representative examples |
|---------|-------|------------------------|
| Confirmed | 49 | 24 float-for-money sites (e.g. `finance/schemas/finance_schemas.py:11`, `orders/.../order_engine.py`), `domains/finance/models/payments.py:97-99` payment credentials stored as bare `String(1000)` with zero uses of the existing `EncryptedString` TypeDecorator, `middleware/comms.py:138-140` `websocket.accept()` before any JWT check, RLS variable mismatch (`middleware/country_context.py:272` sets `app.country_scope`; `pg_rls_policies.sql:25` reads `app.current_country_code`), `domains/accounts/services/auth/auth_service.py:252` session-level `SET` (forbidden by Law 5), 17 log-only event subscribers, `backend/modules/finance/` as a 6th module, 5 architecture/frontend contradictions |
| Partial | 10 | idempotency enforced in the service body but `Optional` at the schema; SSRF at `payment_engine.py:3383-3399` (report cited the wrong line); CHAIN-005 has posting + reconciliation but never publishes `JournalEntryPosted` |
| **False positive / inflated** | **39** | all 9 `migration_helpers` "missing module" claims; all 10 idempotency claims (0 confirmed); 5 rate/percentage floats (`VAT_RATES`, `commission_rate`, `CATEGORY_TAX_PROFILES`); 3 webhook-signature claims (verification exists in `WebhookVerificationMiddleware` and per-gateway handlers); `health_check` "0/N providers" (inherited from `providers/_base.py`); circuit-breaker "missing" (`infrastructure/observability/circuit_breaker.py` + 5 live breakers in `payment_engine.py:163-167`); Law 7 / 37 / 275 FAILs |
| Wrong location / wrong number | 9 | `LOGIC-385` cites a line with no `float()`; 2 idempotency claims cite docstring prose; ruff reported 6,598 (true 7,849); tsc reported 24 (true 106); browser "332 failed tests" (true 0 — the run collected 0 suites) |

**Therefore: the P0 population is ~40% noise.** The verified P0 set is approximately
**49 findings, not 90 blockers**, and several confirmed items are lower severity than P0
(a missing architecture-test file is P2, a TODO count is not a blocker). The
**NOT PRODUCTION READY** verdict stands, but on 49 verified hard blockers rather than 90.

**Two defects are newly confirmed and outrank everything else in Run 5:**
1. The application cannot start (`metrics.py:1` + `config.py:315`).
2. CI cannot even enumerate migrations (`alembic heads` fails), so no migration gate runs.

**Production Readiness Percentage: 2.8% (49 verified P0 of 1,764 findings) — Production Ready: NO**

---

## Run 7 — audit extension + compilation (2026-10-02)

**Two capabilities were added, because the audit could not answer the questions
the business was actually asking.**

1. **Audit extension** — 5 new scanner modules bring registered checks from 59 to
   79, mapped onto the existing 28 dimensions: design tokens and colour drift,
   interaction robustness (buttons, modals, forms, toasts, per-page loading/
   empty/error states), feature-gate integrity and the route × test matrix,
   category-hierarchy depth, workflow runtime and the event spine, handover/
   takeover assurance, QA mechanisms, automation candidates, the finance
   automation surface, and table/migration management.
2. **Compilation** — `zozi_compile.py` turns the audit into
   `_zozi_audit/zozi_remediation_plan.md`: 1,802 steps organised into 6 waves and
   work packages, with a `fix`, a `verify` command and a `rollback` for every
   step, plus `logs/plan_status.json` progress round-trip. Untrusted claims
   (`claim_state ∈ {UNKNOWN, INFERRED}`) are emitted as **verification tasks, not
   code changes** — 282 of them, in wave 4.

**Measurements added this run (all measured from source during the run).**

| Area | Measurement | Value |
|---|---|---|
| Design | hardcoded hex in web-app components (SVG/chart/palette excluded) | 165 across 33 files |
| Design | raw Tailwind palette classes bypassing the token scale | 375 across 52 files |
| Design | inline `style={{…}}` in the web app | 302 |
| Design | UI primitives / using `cva` | 72 / **0** |
| Interaction | buttons / missing `type` / missing pending state | 1466 / 949 / 1189 |
| Interaction | modals missing focus management | 26 of 27 |
| Interaction | destructive calls without a confirmation | 28 |
| Interaction | unlabelled text inputs (wrapping `<label>` and `title` excluded) | 465 of 743 |
| Interaction | success / error toasts | 187 / 780 |
| Pages | routes / loading.tsx / error.tsx / no error handling | 155 / 13 / 15 / 44 |
| Features | declared / gated / undefined gates / dead | 371 / 155 / **7** / 152 |
| Coverage | routes covered by a browser or e2e spec | 100 of 155 (**64.5 %**) |
| Taxonomy | model found / self-reference / depth column / path / seeded depth | yes / yes / yes / yes / **2 of 5** |
| Workflow | Celery app location / tasks / beat schedules | `backend/jobs/celery_app.py` / 38 / 10 |
| Workflow | event handlers / log-only stubs | 79 / 44 (56 %) |
| Workflow | status assignment sites / central state machine | 134 / partial (one domain only) |
| Handover | handover/takeover functions fully guarded | **0 of 10** |
| QA | quality mechanisms absent | product inspection, proof of delivery, supplier scorecard, SLA breach |
| Automation | human-waiting statuses found / serial network loops | 7 status values / 15 |
| Finance | capabilities automated / not | 9 / 1 (bad-debt provisioning) |
| Data | models / relationships missing `lazy=` | 340 / **294 of 376** |
| Data | unindexed hot columns | 224 |
| Data | migration ↔ ORM schema drift | `commerce` (1), `customer` (5) |
| Recommendations | emitted | **19**, tracked separately from blockers |

**Verification of the new checks.** Three independent sub-agents re-derived every
new measurement. They found **ten wrong detection rules**, all now fixed in code
and documented in `_zozi_audit/PLAN.md` §0.2 — including counting React Native
inline styles as web drift (1953 vs 302), ignoring `Column(…, index=True)` (871
vs 224), matching `require_feature` inside comments (15 vs 7), and looking for
the Celery app only at `backend/` root (it is under `backend/jobs/`). Corrected
figures now agree with independent derivation.

**This does not change the verdict.** It sharpens what "not production ready"
means: the blockers are now grouped into a sequence whose first wave (restore
boot, migrations, test collection) is small, and the improvement track is
explicit rather than implied.

**Next assessment due:** after wave 0 of `zozi_remediation_plan.md` is green —
nothing downstream can be trusted while boot, migration enumeration or test
collection is broken.

---

## Completion Blockers

These are findings marked `project_completion_blocker = yes` in dimension files.
They MUST be resolved before production exposure.

**Total completion blockers: 139** (134 yes + 5 partial blockers from law/provider dimensions)

Detailed blocker registers are maintained in:
- `_audit/dimensions/27_project_completion_blockers.md`
- `_audit/11_PRODUCTION_READINESS.md` §4
- `_audit/DIMENSION_INDEX.md`

Top-level blocker categories:
1. **Boot / import blockers** (8): missing `get_current_user`, 15 routers fail to import, `alembic.ini` missing, `ModuleNotFoundError` in migrations
2. **Security blockers** (13): plaintext payment credentials, SQL injection, SSRF, TOTP secrets plaintext, webhook fail-open, missing encryption
3. **Database / migration blockers** (4): 62 divergent Alembic heads, RLS policy/middleware mismatch, 42 tables missing `country_code`, 14 tables without ORM models
4. **Money / float blockers** (20+): systemic float-for-money in 14+ files, tax/commission/FX rounding drift
5. **Architecture blockers** (4): extra `modules/finance/`, duplicate `domains/payments/`, dead cash_management router, cross-domain import violations
6. **Event spine blockers** (2): finance subscribers stubs, orders subscribers stubs — 0 of 7 business chains COMPLETE
7. **Frontend / build blockers** (2): 60+ TypeScript errors, missing icon exports
8. **Test / lint blockers** (2): 6 collection errors, 8,335 ruff errors
9. **Observability / cache blockers** (2): Valkey unreachable, OpenTelemetry disabled

> **Note:** This table must be updated after each audit pass. Remove rows only when the finding is resolved and verified.

---

## Canonical Document Alignment

These three documents must be present, current, and internally consistent. If any check fails, the audit should stop until the canonical docs are corrected.

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| CAN-01 | _most_imp_docx/TECHNOLOGY_STACK.md exists | 01_EXECUTIVE_SUMMARY.md | File present | _most_imp_docx/TECHNOLOGY_STACK.md exists | PASS | 2026-09-29 |
| CAN-02 | _most_imp_docx/ARCHITECTURE_STACK.md exists | 01_EXECUTIVE_SUMMARY.md | File present | _most_imp_docx/ARCHITECTURE_STACK.md exists | PASS | 2026-09-29 |
| CAN-03 | _most_imp_docx/FEATURE_STACK_LIST.md exists | 01_EXECUTIVE_SUMMARY.md | File present | _most_imp_docx/FEATURE_STACK_LIST.md exists | PASS | 2026-09-29 |
| CAN-04 | Technology versions in code match TECHNOLOGY_STACK.md | 18_security.md / 21_contradictions | Lockfile / package.json matches canonical versions | Live check: Python 3.13.15, FastAPI 0.141.0, Uvicorn 0.35.0, SQLAlchemy 2.0.52, Alembic 1.19.1, Pydantic 2.13.4, httpx 0.28.1, Next.js 16.3.4, React 19.2.8, Node v22.15.0 | FAIL | 2026-10-01 |
| CAN-05 | Architecture laws in code match ARCHITECTURE_STACK.md | 21_contradictions.md / architecture tests | No runtime contradictions in live verification | Live check: 31/32 architecture tests pass; 1 CORS foundation test fails; backend boot fails with ImportError get_user_by_id from domains.accounts.ports | FAIL | 2026-10-01 |
| CAN-06 | Feature IDs in code match FEATURE_STACK_LIST.md | 08_FEATURE_HEALTH.md | Catalog test passes; no orphan features | Feature health audit not compiled | UNVERIFIABLE | 2026-09-29 |
| CAN-07 | No .env files exist in backend/, frontend/, or mobile_app/ | 01_executive_summary.md preconditions | find / grep returns zero matches | | UNVERIFIABLE | |

---

## 1 · Technology Stack

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| T-01 | Python version matches TECHNOLOGY_STACK.md | 18_security.md / CI | python --version = 3.13.x | Live: python --version = 3.13.15; pyproject.toml requires-python >=3.13,<3.14 | PASS | 2026-10-01 |
| T-02 | FastAPI version matches | 18_security.md / CI | pip show fastapi = 0.141.x | Live: pip show fastapi = 0.141.0 | PASS | 2026-10-01 |
| T-03 | Uvicorn version matches | 18_security.md / CI | pip show uvicorn = 0.35.0+ | Live: pip show uvicorn = 0.35.0 | PASS | 2026-10-01 |
| T-04 | SQLAlchemy version matches | 18_security.md / CI | pip show sqlalchemy = 2.0.52 | Live: pip show sqlalchemy = 2.0.52 | PASS | 2026-10-01 |
| T-05 | Alembic version matches | 18_security.md / CI | pip show alembic = 1.19.1+ | Live: pip show alembic = 1.19.1 | PASS | 2026-10-01 |
| T-06 | Pydantic version matches | 18_security.md / CI | pip show pydantic = 2.13.4 | Live: pip show pydantic = 2.13.4 | PASS | 2026-10-01 |
| T-07 | httpx version matches | 18_security.md / CI | pip show httpx = 0.28.1 | Live: pip show httpx = 0.28.1 | PASS | 2026-10-01 |
| T-08 | PyJWT is used; python-jose is absent from runtime deps | 18_security.md / 21_contradictions | grep -r "python-jose" backend/ returns zero matches | Live grep: no python-jose / from jose / import jose in backend runtime .py files | PASS | 2026-10-01 |
| T-09 | Valkey client is used; redis PyPI package is absent from runtime deps | 18_security.md / 21_contradictions.md | grep -r "import redis" backend/ returns zero matches | Live grep: no import redis / from redis in backend runtime .py files | PASS | 2026-10-01 |
| T-10 | pytz / tzlocal are absent from runtime deps | 18_security.md | grep -r "pytz tzlocal" backend/ returns zero matches | Live grep: no pytz / tzlocal imports in backend runtime .py files | PASS | 2026-10-01 |
| T-11 | python-magic is absent; puremagic is used | 18_security.md | grep -r "python-magic" backend/ returns zero matches | Live grep: no python-magic package import in backend runtime .py files; puremagic used | PASS | 2026-10-01 |
| T-12 | requests is absent from async code paths | 18_security.md / 21_contradictions | grep -r "import requests" backend/ returns zero matches | Live grep: no import requests / from requests in backend runtime .py files | PASS | 2026-10-01 |
| T-13 | psycopg / psycopg2 are absent from application code | 18_security.md | grep -r "psycopg" backend/ returns zero matches | Live grep: no psycopg imports in backend runtime .py files | PASS | 2026-10-01 |
| T-14 | Next.js version matches TECHNOLOGY_STACK.md | 21_contradictions.md | npm ls next = 16.3.5 | Live: package.json has next 16.3.4; target 16.3.5; drift 0.1 | FAIL | 2026-10-01 |
| T-15 | React version matches | 21_contradictions.md | npm ls react = 19.2.8 | | UNVERIFIABLE | |
| T-16 | TypeScript version matches | 21_contradictions.md | npx tsc --version = 5.9.3 | | UNVERIFIABLE | |
| T-17 | pnpm is the package manager; no npm/yarn lockfiles in frontend | 21_contradictions.md | ls package-lock.json yarn.lock returns no files | Live: pnpm-lock.yaml EXISTS; no package-lock.json or yarn.lock | PASS | 2026-10-01 |
| T-18 | sharp version matches | 21_contradictions.md | npm ls sharp = 0.35.4 | | UNVERIFIABLE | |
| T-19 | Tailwind CSS version matches | 21_contradictions.md | npm ls tailwindcss = 4.3.3 | | UNVERIFIABLE | |
| T-20 | Zustand version matches | 21_contradictions.md | npm ls zustand = 5.0.14 | | UNVERIFIABLE | |
| T-21 | framer-motion / motion version matches | 21_contradictions.md | npm ls motion = 13.2.0+ | CONTRADICTION-008: framer-motion ^12.0.0 vs motion 13.2.0+ target | FAIL | 2026-10-01 |
| T-22 | No forbidden frontend packages | 18_security.md / 21_contradictions.md | grep in package.json | CONTRADICTION-010: jest-environment-jsdom ^30.3.0 incompatible with jest ^29.0.0 | FAIL | 2026-10-01 |
| T-23 | Node.js version matches Dockerfile | 18_security.md / CI | node --version = 22.12.0 | Live: node --version = v22.15.0; Dockerfile uses node:22-alpine (minor unpinned) | FAIL | 2026-10-01 |
| T-24 | uv.lock is present and committed | 18_security.md | File present | Live: uv.lock EXISTS; pyproject.toml requires-python >=3.13,<3.14 | PASS | 2026-10-01 |
| T-25 | pnpm-lock.yaml is present and committed | 18_security.md / PF-005 | File present | Live: pnpm-lock.yaml EXISTS in frontend/web_app | PASS | 2026-10-01 |
| T-26 | DATABASE_URL_UNPOOLED is not used anywhere | 21_contradictions.md | grep -r "DATABASE_URL_UNPOOLED" returns zero matches | Live grep: no DATABASE_URL_UNPOOLED in backend runtime code | PASS | 2026-10-01 |
| T-27 | Deprecated aliases are not used in new code | 21_contradictions.md | grep for deprecated vars in changed files | | UNVERIFIABLE | |

---

## 2 · Architecture

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| A-01 | backend/main.py boots with zero stubs / TODOs / NotImplementedError | 09_ANTI_PATTERNS.md / 11_PRODUCTION_READINESS.md | uvicorn backend.main:app --log-level warning logs show zero stubs | Live: 15 module routers fail to import with ImportError: cannot import name 'get_current_user' from 'infrastructure.utils.dependencies'; 0 routes mounted | FAIL | 2026-10-01 |
| A-02 | All routes mount successfully | 11_PRODUCTION_READINESS.md | GET /openapi.json returns full schema | Live: 15 module routers fail to import; 0 routes mounted; /openapi.json unreachable | FAIL | 2026-10-01 |
| A-03 | 5 modules exist: admin, customer, employee, logistics, supplier | ARCHITECTURE_STACK.md | Directory listing | 5 module directories exist | PASS | 2026-09-29 |
| A-04 | 15 domains exist | ARCHITECTURE_STACK.md | Directory listing under backend/domains/ | Live: 18 entries including __pycache__; 17 domain dirs: accounts, analytics, audit, catalog, comms, country, customers, finance, governance, hr, logistics, media, orders, payments, promotions, security, suppliers | FAIL | 2026-10-01 |
| A-05 | No root-level forbidden folders | ARCHITECTURE_STACK.md | ls backend/ | No root-level forbidden folders | PASS | 2026-09-29 |
| A-06 | kernel/ imports nothing from modules, domains, rbac, providers, jobs, middleware | 21_contradictions.md / architecture tests | Architecture test test_import_laws.py | Live: 31/32 arch tests pass; test_supplier_routes_are_registered FAILS (0 supplier routes); test_cors_in_foundation_layer FAILS | FAIL | 2026-10-01 |
| A-07 | infrastructure/ imports nothing from domains, rbac, providers | 21_contradictions.md / architecture tests | Architecture test | CONTRADICTION-ARCH: infrastructure imports domains/providers (ARCH-010..014) | FAIL | 2026-09-29 |
| A-08 | providers/ imports nothing from domains, modules, rbac, jobs, middleware | 21_contradictions.md / architecture tests | Architecture test test_provider_isolation.py | CONTRADICTION-002: providers import requests (forbidden); providers import infrastructure (ARCH-029..031) | FAIL | 2026-10-01 |
| A-09 | jobs/ imports only from domains, infrastructure, providers | 21_contradictions.md / architecture tests | Architecture test | jobs/ imports only sanctioned layers | PASS | 2026-09-29 |
| A-10 | middleware/ imports only from infrastructure + rbac | 21_contradictions.md / architecture tests | Architecture test | PB-01, PB-05: middleware imports providers/domains; SEC-AUTH-001: 4 duplicate require_admin implementations | FAIL | 2026-10-01 |
| A-11 | @zozi/shared does not import from web_app or mobile_app | 21_contradictions.md / architecture tests | Architecture test | shared/ no app imports | PASS | 2026-09-29 |
| A-12 | No circular imports across any two packages | 21_contradictions.md / architecture tests | Architecture test test_no_cross_domain_direct_imports.py | Live: app boot fails with ImportError due to missing get_user_by_id in ports.py | FAIL | 2026-10-01 |
| A-13 | DOMAIN_ALLOWLIST.yaml exists and only shrinks | 21_contradictions.md | File diff vs baseline | DOMAIN_ALLOWLIST.yaml bloat (22 entries) | FAIL | 2026-09-29 |
| A-14 | All router files are registered in routers/__init__.py | 21_contradictions.md | Unregistered router test | | UNVERIFIABLE | |
| A-15 | Module routers are thin (auth + require_feature + 1 service call) | 09_ANTI_PATTERNS.md | Architecture test test_law2_router_no_db_writes.py | 09_ANTI_PATTERNS: 50 findings including raw DB queries in routers | FAIL | 2026-10-01 |
| A-16 | Cross-domain writes go only through events.py / subscribers.py | 21_contradictions.md | Architecture test test_law3_cross_domain.py | Cross-domain writes bypass events | FAIL | 2026-09-29 |
| A-17 | Cross-domain reads go only through ports.py | 21_contradictions.md | Architecture test test_ports_contract.py | Cross-domain reads bypass ports.py | FAIL | 2026-09-29 |
| A-18 | Every table is in a domain Postgres schema (no public tables) | 21_contradictions.md | Architecture test test_law6_schema_discipline.py | | UNVERIFIABLE | |
| A-19 | No forbidden schemas: core, platform, identity | 21_contradictions.md | Architecture test | | UNVERIFIABLE | |
| A-20 | Every model has __table_args__ = {"schema": "<domain>"} | 21_contradictions.md | Schema test | | UNVERIFIABLE | |
| A-21 | Alembic history is linear (no divergent heads) | 11_PRODUCTION_READINESS.md | alembic heads returns one head | Live: alembic.ini MISSING at backend root; env.py uses context.config but no ini file present | FAIL | 2026-10-01 |
| A-22 | create_all is dev-only and not used in production migrations | 09_ANTI_PATTERNS.md | Code review | | UNVERIFIABLE | |
| A-23 | infrastructure/database/base.py is the single canonical Base | 21_contradictions.md | Architecture test | infrastructure/database/base.py is canonical Base | PASS | 2026-09-29 |
| A-24 | All 325 laws from ARCHITECTURE_STACK.md have corresponding tests | 11_PRODUCTION_READINESS.md | Architecture test test_laws_complete.py | Live: 356 architecture tests collected; test_laws_complete.py exists and passes allowlist tests | FAIL | 2026-10-01 |

---

## 3 · Feature Completeness

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| F-01 | Every feature in FEATURE_STACK_LIST.md has a backend service | 08_FEATURE_HEALTH.md | Service file exists per feature | FEAT-016: promotions_write_service.py marked ARCHIVED MODULE but still imported; some features lack live service implementation | FAIL | 2026-10-01 |
| F-02 | Every feature has at least one smoke test | 08_FEATURE_HEALTH.md | Test file exists | FEAT-023: test_orders.py has 122 lines — mostly smoke tests; no refund/return workflow tests | FAIL | 2026-10-01 |
| F-03 | Every feature has a happy-path test | 08_FEATURE_HEALTH.md | Workflow test exists | FEAT-023: missing return/refund integration tests; only smoke tests present | FAIL | 2026-10-01 |
| F-04 | Every feature has a failure-path test | 08_FEATURE_HEALTH.md | Error-path test exists | FEAT-023: no failure-path tests for return/refund workflow | FAIL | 2026-10-01 |
| F-05 | Every feature has an idempotency/rollback test where applicable | 08_FEATURE_HEALTH.md | Idempotency test exists | FEAT-011: refund auto-issue lacks idempotency test; inventory claim/release lacks rollback test | FAIL | 2026-10-01 |
| F-06 | backend/catalog.py aggregates all domains/*/features.py | 08_FEATURE_HEALTH.md | GET /rbac/catalog returns full set | | UNVERIFIABLE | |
| F-07 | Frontend permissions.ts is generated from /rbac/catalog | 08_FEATURE_HEALTH.md | Generated file present and current | | UNVERIFIABLE | |
| F-08 | All require_feature() literals exist in catalog | 08_FEATURE_HEALTH.md / architecture tests | Architecture test test_feature_catalog.py | FEAT-008: get_cart uses require_feature("customers.cart.manage") — compliant; full catalog not verified | UNVERIFIABLE | |
| F-09 | No duplicate feature definitions across domains | 08_FEATURE_HEALTH.md | Feature catalog test | | UNVERIFIABLE | |
| F-10 | MISSING features are either implemented or deferred with time-box | 08_FEATURE_HEALTH.md | Deferral log exists | | UNVERIFIABLE | |

---

## 4 · Backend Runtime

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| B-01 | uvicorn backend.main:app boots to ready state | 11_PRODUCTION_READINESS.md | Process exits 0; logs show startup complete | Live: ImportError: cannot import name 'get_user_by_id' from 'domains.accounts.ports'; 15 routers skipped; app does not boot | FAIL | 2026-10-01 |
| B-02 | /health returns 200 | 11_PRODUCTION_READINESS.md | curl /health = 200 | Live: app cannot boot; /health unreachable | FAIL | 2026-10-01 |
| B-03 | /health/deps returns 200 with dependency status JSON | 11_PRODUCTION_READINESS.md | curl /health/deps = 200 + JSON | Live: app cannot boot; /health/deps unreachable | FAIL | 2026-10-01 |
| B-04 | /health/ready returns 200 when all deps healthy | 11_PRODUCTION_READINESS.md | curl /health/ready = 200 | Live: app cannot boot; /health/ready unreachable | FAIL | 2026-10-01 |
| B-05 | /health/ready fails closed when Valkey is down | 11_PRODUCTION_READINESS.md | Disconnect Valkey; /health/ready != 200 | | UNVERIFIABLE | |
| B-06 | /health/ready fails closed when DB is down | 11_PRODUCTION_READINESS.md | Disconnect DB; /health/ready != 200 | | UNVERIFIABLE | |
| B-07 | Zero print() calls in production code | 09_ANTI_PATTERNS.md | grep -r "print(" backend/ in non-test code | Live: print() found in backend/domains/_mixin_compliance.py:159-160 (production code) | FAIL | 2026-10-01 |
| B-08 | All logs use structlog with context fields | 09_ANTI_PATTERNS.md | Code review + log samples | 09_ANTI_PATTERNS: Not all logs use structlog | FAIL | 2026-09-29 |
| B-09 | Global exception handler returns RFC 7807 / structured errors | 11_PRODUCTION_READINESS.md | Integration test test_error_handling.py | | UNVERIFIABLE | |
| B-10 | No stack traces leak in production error responses | 11_PRODUCTION_READINESS.md | Response review | | UNVERIFIABLE | |
| B-11 | All background jobs (Celery / Beat) boot and process | 11_PRODUCTION_READINESS.md | Worker starts; Beat schedules fire | Live: app cannot boot; Celery boot not verified | FAIL | 2026-10-01 |
| B-12 | Celery broker is Valkey, not SQLite | 11_PRODUCTION_READINESS.md | CELERY_BROKER_URL uses valkey:// | | UNVERIFIABLE | |
| B-13 | Graceful shutdown disposes DB engine, cache client, workers | 09_ANTI_PATTERNS.md | Shutdown test / code review | | UNVERIFIABLE | |
| B-14 | Request ID propagates through all service calls | 09_ANTI_PATTERNS.md | Log samples show request_id | | UNVERIFIABLE | |

---

## 5 · Frontend Build & Runtime

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| FE-01 | next build exits 0 with zero errors | 11_PRODUCTION_READINESS.md / 19_performance | Build log exit 0 | Live: pnpm build fails with exit code 1; error: The export Timer was not found in module src/lib/icons.ts | FAIL | 2026-10-01 |
| FE-02 | No Module not found errors in build | 11_PRODUCTION_READINESS.md / 19_performance | Build log | Live: build fails with module-not-found for Timer export from src/lib/icons.ts | FAIL | 2026-10-01 |
| FE-03 | Turbopack root-directory is correctly configured | 11_PRODUCTION_READINESS.md | No root-directory error | Live: build fails at src/app/employee/attendance/page.tsx importing Timer from src/lib/icons.ts | FAIL | 2026-10-01 |
| FE-04 | next/image optimization is active (sharp installed) | 21_contradictions.md | npm ls sharp = 0.35.4 | | UNVERIFIABLE | |
| FE-05 | Bundle chunks are <200 KB per chunk | 19_performance.md | Build analyzer output | PERF-007: build fails; no .next artifact exists for analysis | UNVERIFIABLE | |
| FE-06 | No console.log() in production client code | 09_ANTI_PATTERNS.md | grep -r "console.log" frontend/web_app/src/ in non-test code | Live grep: no console.log in frontend/web_app/src/ | PASS | 2026-10-01 |
| FE-07 | All routes return 200 / expected status | 11_PRODUCTION_READINESS.md | Smoke test against built app | PERF-007: build fails; no built app to test | UNVERIFIABLE | |
| FE-08 | API proxy rewrites /api/* to backend correctly | 21_contradictions.md | Proxy test | API proxy rewrites configured | PASS | 2026-09-29 |
| FE-09 | next.config.ts has correct rewrites for backend proxy | 21_contradictions.md | Config review | | UNVERIFIABLE | |

---

## 6 · Mobile Build

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| M-01 | eas build succeeds for at least one platform | 11_PRODUCTION_READINESS.md | EAS build artifact | 15_frontend_mobile: missing deps (expo-notifications, expo-camera); no eas.json; build not attempted | UNVERIFIABLE | |
| M-02 | expo-secure-store is in package.json | 15_frontend_mobile.md | npm ls expo-secure-store | | UNVERIFIABLE | |
| M-03 | expo-notifications is in package.json | 15_frontend_mobile.md | npm ls expo-notifications | | UNVERIFIABLE | |
| M-04 | No localStorage for tokens; uses expo-secure-store | 15_frontend_mobile.md | Code review | | UNVERIFIABLE | |
| M-05 | expo-location used instead of navigator.geolocation | 15_frontend_mobile.md | Code review | | UNVERIFIABLE | |
| M-06 | Social login stubs are implemented or deferred | 15_frontend_mobile.md | Implementation or deferral record | | UNVERIFIABLE | |
| M-07 | Checkout UX is functional end-to-end | 15_frontend_mobile.md | E2E test or manual sign-off | | UNVERIFIABLE | |

---

## 7 · Tests -- Backend

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| T-01 | pytest backend/tests/architecture/ exits 0 with zero skips/xfails | 11_PRODUCTION_READINESS.md | CI artifact or local run | Live: tests/architecture/ EXISTS; 356 tests collected; 31/32 pass with keyword filter; 1 CORS foundation test fails | FAIL | 2026-10-01 |
| T-02 | pytest backend/tests/security/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | BOOT-011: collection errors prevent execution | UNVERIFIABLE | |
| T-03 | pytest backend/tests/domains/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | BOOT-011: collection errors prevent execution | UNVERIFIABLE | |
| T-04 | pytest backend/tests/integration/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | BOOT-011: collection errors prevent execution | UNVERIFIABLE | |
| T-05 | pytest backend/tests/providers/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | BOOT-011: collection errors prevent execution | UNVERIFIABLE | |
| T-06 | pytest backend/tests/rbac/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | BOOT-011: collection errors prevent execution | UNVERIFIABLE | |
| T-07 | pytest backend/tests/workflows/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | BOOT-011: collection errors prevent execution | UNVERIFIABLE | |
| T-08 | pytest backend/tests/middleware/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | python-jose present (SEC-JWT-001, CONTRADICTION-001) | FAIL | 2026-10-01 |
| T-09 | pytest backend/tests/kernel/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | redis package used in infrastructure/valkey/ (CONTRADICTION-002 shows requests in 8 files) | FAIL | 2026-10-01 |
| T-10 | pytest backend/tests/observability/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | No pytz/tzlocal in runtime deps | PASS | 2026-09-29 |
| T-11 | pytest backend/tests/modules/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | python-magic absent; puremagic used | PASS | 2026-09-29 |
| T-12 | pytest backend/tests/finance/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | requests used in auth_service.py:33 (CONTRADICTION-002); collection errors | FAIL | 2026-10-01 |
| T-13 | pytest backend/tests/performance/ has at least one passing perf regression test | 12_tests.md / 19_performance.md | Perf test artifact | psycopg2-binary in schema-audit CI | FAIL | 2026-09-29 |
| T-14 | No collection-time errors (duplicate table, missing imports) | 11_PRODUCTION_READINESS.md | Test collection log | Live: 4509 tests collected, 17 collection errors (ImportError get_user_by_id, ModuleNotFoundError domains.finance.services.payments, fastapi_limiter_valkey Limiter) | FAIL | 2026-10-01 |
| T-15 | Test coverage meets minimum threshold (per-domain smoke + law tests) | 12_tests.md | Coverage report | | UNVERIFIABLE | |

---

## 8 · Security

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| S-01 | Zero open CRITICAL security findings | 18_security.md / TO_BE_RESOLVE.md | Resolver tracker | 18_security: P0: 9 findings (SEC-AUTH-001, SEC-ENC-001, SEC-ENC-002, SEC-DEVBIND-001, SEC-WEB-002..006); all are completion blockers | FAIL | 2026-10-01 |
| S-02 | Zero open HIGH security findings | 18_security.md / TO_BE_RESOLVE.md | Resolver tracker | 18_security: P1: 4 findings (SEC-KEY-001, SEC-IDEM-001, SEC-ROUTE-001, SEC-3DS-001) | FAIL | 2026-10-01 |
| S-03 | python-jose is absent from runtime code | 18_security.md / 21_contradictions | grep -r "python-jose" backend/ | Live grep: no python-jose / from jose / import jose in backend runtime .py files | PASS | 2026-10-01 |
| S-04 | JWT signing uses PyJWT with HS256 | 18_security.md | Code review providers/auth/jwt.py | PyJWT used for signing | PASS | 2026-09-29 |
| S-05 | typ claim is verified on every JWT decode | 18_security.md | Code review | typ claim verified | PASS | 2026-09-29 |
| S-06 | Token blacklist is implemented and cached in Valkey | 18_security.md | Code review infrastructure/valkey/ | Token blacklist in Valkey | PASS | 2026-09-29 |
| S-07 | Refresh token rotation is implemented | 18_security.md | Code review | | UNVERIFIABLE | |
| S-08 | MFA backup codes are encrypted (AES-256-GCM), not bcrypt-hashed | 18_security.md | Code review | Live: backend/domains/accounts/models/mfa_factor.py still present; field_encryptor exists at infrastructure/security/field_encryption.py | FAIL | 2026-10-01 |
| S-09 | Passwords >72 bytes are rejected, never truncated | 18_security.md | Code review auth_service.py | | UNVERIFIABLE | |
| S-10 | bcrypt cost is configurable and >= recommended | 18_security.md | Code review | | UNVERIFIABLE | |
| S-11 | All public endpoints use Pydantic schemas | 18_security.md | Code review + architecture test | Live: app does not boot; cannot verify router signatures; anti-patterns report indicates raw dict usage | FAIL | 2026-10-01 |
| S-12 | CSRF middleware is active in all environments | 18_security.md | Code review middleware/orchestrator.py | SEC-CSRF-001: CSRF can be disabled via CSRF_DISABLED env var in test/development | FAIL | 2026-10-01 |
| S-13 | Security headers are emitted (CSP, HSTS, X-Frame-Options, etc.) | 18_security.md | Header inspection | Security headers present | PASS | 2026-09-29 |
| S-14 | Rate limiting fails closed when Valkey is down | 18_security.md | Chaos test | | UNVERIFIABLE | |
| S-15 | Field-level encryption uses AES-256-GCM with FIELD_ENCRYPTION_KEY | 18_security.md | Code review infrastructure/security/field_encryption.py | SEC-ENC-003 resolved; FieldEncryptor uses AES-256-GCM | PASS | 2026-10-01 |
| S-16 | Payment gateway credentials are encrypted at rest | 18_security.md | DB schema review | Live: backend/domains/finance/models/payments.py still present; plaintext credential columns reported | FAIL | 2026-10-01 |
| S-17 | Webhook signatures are verified before processing | 18_security.md | Code review webhook_verification.py | SEC-WEB-002..006: 5 webhook handlers fail-open when secret unconfigured | FAIL | 2026-10-01 |
| S-18 | Webhook IP whitelist is active | 18_security.md | Code review webhook_ip_whitelist.py | | UNVERIFIABLE | |
| S-19 | SQL injection is prevented (no f-string SQL, parameterized queries only) | 18_security.md | Architecture test + code review | No raw SQL injection | PASS | 2026-09-29 |
| S-20 | PII is masked in logs, errors, and non-admin responses | 18_security.md | Code review + log samples | PII leaks in responses | FAIL | 2026-10-01 |
| S-21 | gitleaks passes in CI (zero secrets found) | 18_security.md | CI artifact | | UNVERIFIABLE | |
| S-22 | pip-audit passes (zero high/critical CVEs) | 18_security.md | CI artifact | | UNVERIFIABLE | |
| S-23 | Trivy passes on container image | 18_security.md | CI artifact | | UNVERIFIABLE | |
| S-24 | Dependabot is enabled and high/critical alerts are addressed | 18_security.md | GitHub settings | | UNVERIFIABLE | |
| S-25 | No hardcoded secrets in code | 18_security.md | gitleaks + code review | | UNVERIFIABLE | |
| S-26 | SECRET_KEY is >=32 chars and rotated on 90-day schedule | 18_security.md | Config review + rotation log | Live: AUDIT_CHAIN_KEY validation enforces >=32 chars at config.py:305; SECRET_KEY validation present | FAIL | 2026-10-01 |
| S-27 | FIELD_ENCRYPTION_KEY is rotated on 90-day schedule | 18_security.md | Config review + rotation log | Live: FIELD_ENCRYPTION_KEY validation present in config.py | FAIL | 2026-10-01 |
| S-28 | AUDIT_CHAIN_KEY is rotated on schedule | 18_security.md | Config review + rotation log | Live: AUDIT_CHAIN_KEY validation enforces >=32 chars at config.py:305 | FAIL | 2026-10-01 |
| S-29 | All auth failures, 403s, rate-limit triggers logged at WARNING+ | 18_security.md | Log samples | SEC-AUTH-002: rate-limit triggers not logged | FAIL | 2026-10-01 |
| S-30 | Auth logic exists in exactly one canonical location | 18_security.md | Code review | SEC-AUTH-001: 4 duplicate require_admin implementations | FAIL | 2026-10-01 |
| S-31 | WebSocket auth verifies JWT type claim = access | 18_security.md | Code review | | UNVERIFIABLE | |
| S-32 | Device binding is enforced for sensitive actions | 18_security.md | Code review | SEC-DEVBIND-001: DeviceBindingMiddleware stores fp but never verifies against JWT dfp claim | FAIL | 2026-10-01 |
| S-33 | Brute-force protection: 5 fails = lock, 10 = admin alert | 18_security.md | Code review | | UNVERIFIABLE | |
| S-34 | Bot detection / CAPTCHA is active on public auth endpoints | 18_security.md | Code review | No CAPTCHA on public auth endpoints | FAIL | 2026-10-01 |
| S-35 | Session concurrent limit is enforced | 18_security.md | Code review | | UNVERIFIABLE | |
| S-36 | Session binding uses device fingerprint | 18_security.md | Code review | SEC-DEVBIND-001: device binding data-carrying only, not verified | FAIL | 2026-10-01 |
| S-37 | All non-public endpoints use get_current_user or equivalent | 18_security.md / architecture tests | Architecture test | | UNVERIFIABLE | |
| S-38 | All non-public endpoints use require_feature() or require_module() | 18_security.md / architecture tests | Architecture test | | UNVERIFIABLE | |
| S-39 | PCI-DSS scope is minimized | 18_security.md | Architecture review | SEC-WEB-001: PCI-DSS bypass for test/development environments | FAIL | 2026-10-01 |
| S-40 | Payment credentials are stored encrypted (AES-256-GCM) | 18_security.md | DB schema + code review | SEC-ENC-002: Payment credentials plaintext in PaymentGatewayConnection model | FAIL | 2026-10-01 |

---

## 9 · Database

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| D-01 | All 15 domain schemas exist and contain expected tables | 21_contradictions.md | \dn in psql | | UNVERIFIABLE | |
| D-02 | No tables exist in public schema (except allowed extensions) | 21_contradictions.md | \dt public.* | | UNVERIFIABLE | |
| D-03 | No duplicate __tablename__ across models | 21_contradictions.md | Architecture test test_schema_discipline.py | | UNVERIFIABLE | |
| D-04 | All FK columns have explicit ForeignKey with ondelete | 21_contradictions.md | Schema review | D-04: Missing ForeignKey on country_code | FAIL | 2026-09-29 |
| D-05 | All FK columns have explicit indexes | 21_contradictions.md | Schema review | D-05: Missing indexes on FK columns | FAIL | 2026-09-29 |
| D-06 | All user-facing tables have is_deleted boolean default false | 21_contradictions.md | Schema review | | UNVERIFIABLE | |
| D-07 | All tables have created_at, updated_at, country_code | 21_contradictions.md | Schema review | | UNVERIFIABLE | |
| D-08 | country_code is String(2) following ISO 3166-1 alpha-2 | 21_contradictions.md | Schema review | | UNVERIFIABLE | |
| D-09 | created_at / updated_at use server_default=func.now() | 21_contradictions.md | Schema review | | UNVERIFIABLE | |
| D-10 | No SELECT * in application queries | 21_contradictions.md / 19_performance | Code review + grep | PERF-002: SELECT * in 3 unified inbox queries | FAIL | 2026-10-01 |
| D-11 | No N+1 queries (all relationships use lazy="selectin" or "joined") | 19_performance.md | Architecture test + code review | PERF-001: N+1 query patterns in 6 model files | FAIL | 2026-10-01 |
| D-12 | OFFSET pagination is not used on hot lists | 19_performance.md | Architecture test test_keyset_pagination.py | PERF-004: 25 OFFSET pagination instances in hot list endpoints | FAIL | 2026-10-01 |
| D-13 | Connection pool pool_size >= 10, max_overflow >= 20 | 11_PRODUCTION_READINESS.md | Config review | | UNVERIFIABLE | |
| D-14 | DATABASE_URL uses pooled Neon endpoint (-pooler in host) | 11_PRODUCTION_READINESS.md | Config review | D-14: DATABASE_URL pooling issues | FAIL | 2026-10-01 |
| D-15 | DATABASE_URL_DIRECT uses non-pooled Neon endpoint | 11_PRODUCTION_READINESS.md | Config review | D-15: DATABASE_URL_DIRECT not configured | FAIL | 2026-10-01 |
| D-16 | Alembic uses DATABASE_URL_DIRECT, not pooled endpoint | 11_PRODUCTION_READINESS.md | Code review alembic/env.py | | UNVERIFIABLE | |
| D-17 | Alembic rejects SQLite with RuntimeError | 11_PRODUCTION_READINESS.md | Code review alembic/env.py | | UNVERIFIABLE | |
| D-18 | Migrations are linear; alembic heads returns one head | 11_PRODUCTION_READINESS.md / 10_migrations | CLI command | 10_migrations: 14 divergent heads; 2 duplicate revision IDs; backend/alembic.ini MISSING | FAIL | 2026-10-01 |
| D-19 | No auto-migrate on web replica boot | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| D-20 | RLS is active on all 15 domain schemas | 21_contradictions.md | \dp in psql + architecture test | | UNVERIFIABLE | |
| D-21 | set_rls_context() uses SET LOCAL inside active transaction | 21_contradictions.md | Code review | D-21: RLS SET LOCAL mismatch | FAIL | 2026-10-01 |
| D-22 | Session-level SET is forbidden under Neon pooler | 21_contradictions.md | Code review | D-22: Session-level SET under Neon pooler | FAIL | 2026-10-01 |
| D-23 | All queries filter by country_code via RLS | 21_contradictions.md | Architecture test test_law5_country_isolation.py | | UNVERIFIABLE | |
| D-24 | Soft delete (is_deleted) is applied to all user-facing tables | 21_contradictions.md | Schema review | | UNVERIFIABLE | |
| D-25 | Float is not used for monetary values in DB models | 18_security.md / 21_contradictions.md | Schema review (Numeric / Decimal used) | | UNVERIFIABLE | |
| D-26 | All migrations have backward-compatible strategy (expand-contract) | 11_PRODUCTION_READINESS.md | Migration review | | UNVERIFIABLE | |
| D-27 | Daily backups exist and restore has been tested | 11_PRODUCTION_READINESS.md | Backup artifact + restore log | | UNVERIFIABLE | |
| D-28 | Read replicas use get_read_db() with independent pool settings | 19_performance.md | Code review (if replicas provisioned) | | UNVERIFIABLE | |

---

## 10 · Frontend UI

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| UI-01 | Buttons have disabled/loading/error states | 24_browser_behavior.md | Component review | | UNVERIFIABLE | |
| UI-02 | Buttons are keyboard accessible (Enter/Space activation) | 24_browser_behavior.md | Accessibility test | | UNVERIFIABLE | |
| UI-03 | Buttons have visible focus indicator | 24_browser_behavior.md | Accessibility test | | UNVERIFIABLE | |
| UI-04 | Popups/modals implement focus trap | 24_browser_behavior.md | Code review + Playwright | | UNVERIFIABLE | |
| UI-05 | Popups/modals close on Escape key | 24_browser_behavior.md | Code review + Playwright | | UNVERIFIABLE | |
| UI-06 | Popups/modals have aria-modal="true" and role="dialog" | 24_browser_behavior.md | Code review | | UNVERIFIABLE | |
| UI-07 | Popups/modals have backdrop click-to-close (where appropriate) | 24_browser_behavior.md | Code review | | UNVERIFIABLE | |
| UI-08 | Popups/modals have scroll lock when open | 24_browser_behavior.md | Code review | | UNVERIFIABLE | |
| UI-09 | Forms validate on submit and show user-facing errors | 24_browser_behavior.md | Component review | | UNVERIFIABLE | |
| UI-10 | Form validation matches backend Pydantic schemas | 24_browser_behavior.md | Integration test | | UNVERIFIABLE | |
| UI-11 | Error boundaries catch and display errors gracefully | 24_browser_behavior.md | Component review | | UNVERIFIABLE | |
| UI-12 | Loading skeletons / spinners are shown for async states | 24_browser_behavior.md | Component review | | UNVERIFIABLE | |
| UI-13 | Empty states are designed for all list views | 24_browser_behavior.md | Component review | | UNVERIFIABLE | |
| UI-14 | WCAG 2.1 AA contrast ratios are met | 24_browser_behavior.md | jest-axe + manual review | | UNVERIFIABLE | |
| UI-15 | Responsive behavior verified at 320px, 768px, 1024px, 1440px | 24_browser_behavior.md | Playwright viewport tests | | UNVERIFIABLE | |
| UI-16 | next/image is used for all product/media images | 24_browser_behavior.md | Code review | | UNVERIFIABLE | |
| UI-17 | Images have width, height, and alt attributes | 24_browser_behavior.md | Code review | | UNVERIFIABLE | |
| UI-18 | No layout shift (CLS < 0.1) on critical pages | 19_performance.md | Lighthouse / Playwright | | UNVERIFIABLE | |

---

## 11 · Frontend Workflows

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| W-01 | Browse -> cart -> checkout -> order -> confirmation (customer) | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-02 | Registration -> email verify -> login -> profile (customer) | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-03 | Supplier registration -> KYC -> product upload -> order received | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-04 | Logistics partner registration -> service areas -> shipment pickup -> delivery | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-05 | Admin login -> product moderation -> category management -> order management | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-06 | Payment -- card (Stripe/Tap/PayTabs) end-to-end | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-07 | Payment -- Cash on Delivery order flow | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-08 | Return request -> admin review -> refund flow | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-09 | Wishlist -> move to cart -> checkout | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-10 | Search -> filter -> sort -> product detail -> add to cart | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-11 | Chatbot opens, queries, receives response | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-12 | Employee login -> leave request -> manager approval | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-13 | Admin RBAC: sub-admin sees bounded feature set only | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-14 | Country switch updates currency, tax, payment methods | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-15 | Session revocation forces re-login | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-16 | Password reset flow end-to-end | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-17 | TOTP setup -> login with MFA -> backup codes issued | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-18 | Error path: network failure shows retry UI | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-19 | Error path: 404/500 shows friendly error page | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-20 | Rollback path: cancel order restores inventory and queues refund | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |

---

## 12 · Browser Behavioral Tests

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| B-01 | _browser_test/ directory exists | 24_browser_behavior.md | Directory present | Live: _browser_test/ EXISTS with config, docs, fixtures, src, tests; 23 failed tests in last run | FAIL | 2026-10-01 |
| B-02 | Money-path Playwright specs exist and pass: checkout, payment, order creation | 24_browser_behavior.md | Spec files + green CI run | Live: 23 failed tests in last run | FAIL | 2026-10-01 |
| B-03 | Security-path Playwright specs exist and pass: login, MFA, RBAC, session revocation | 24_browser_behavior.md | Spec files + green CI run | Live: 23 failed tests in last run | FAIL | 2026-10-01 |
| B-04 | Browser tests run in CI on every PR | 24_browser_behavior.md | CI workflow present | Live: _browser_test/reports/artifacts/.last-run.json shows status: failed; 23 tests failed | FAIL | 2026-10-01 |
| B-05 | Browser tests run against production-like environment (staging) | 24_browser_behavior.md | Staging test run artifact | | UNVERIFIABLE | |

---

## 13 · Performance & Fast Loading

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| P-01 | LCP < 2.5s on 4G for critical pages | 19_performance.md | Lighthouse / Playwright | | UNVERIFIABLE | |
| P-02 | CLS < 0.1 on critical pages | 19_performance.md | Lighthouse / Playwright | | UNVERIFIABLE | |
| P-03 | INP < 200ms on critical pages | 19_performance.md | Lighthouse / Playwright | | UNVERIFIABLE | |
| P-04 | TTFB < 600ms at p50 | 19_performance.md | Load test / RUM | | UNVERIFIABLE | |
| P-05 | Bundle chunks are <200 KB (gzipped) | 19_performance.md | Build analyzer | Live: frontend build fails; no .next artifact exists for analysis | FAIL | 2026-10-01 |
| P-06 | Images are optimized (WebP/AVIF) | 19_performance.md | Image audit / build output | Live: next.config.ts only enables WebP, not AVIF | FAIL | 2026-10-01 |
| P-07 | CDN is configured for static assets and images | 19_performance.md | Response headers | | UNVERIFIABLE | |
| P-08 | API p95 < 500ms at 2x expected peak traffic | 11_PRODUCTION_READINESS.md | Load test report | | UNVERIFIABLE | |
| P-09 | API p99 < 1s at 2x expected peak traffic | 11_PRODUCTION_READINESS.md | Load test report | | UNVERIFIABLE | |
| P-10 | Zero N+1 queries on hot paths | 19_performance.md | Architecture test + query log review | PERF-001: N+1 query patterns in 6 model files | FAIL | 2026-10-01 |
| P-11 | Connection pool does not exhaust under peak load | 19_performance.md | Load test + pool metrics | | UNVERIFIABLE | |
| P-12 | Cache hit rate > 80% for catalog and session data | 19_performance.md | Valkey metrics | PERF-005: infrastructure/utils/cache.py is no-op shim; no Valkey hit/miss metrics | FAIL | 2026-10-01 |
| P-13 | Graceful degradation when Valkey is down (sessions -> DB fallback) | 19_performance.md | Chaos test | | UNVERIFIABLE | |
| P-14 | CPU-bound work runs in Celery / async_workers, not request handlers | 19_performance.md | Code review | PERF-009: CPU-bound work correctly routed through async_workers; already compliant | PASS | 2026-10-01 |
| P-15 | Keyset pagination is used on all hot list endpoints | 19_performance.md | Architecture test test_keyset_pagination.py | PERF-004: 25 OFFSET pagination instances in hot list endpoints | FAIL | 2026-10-01 |

---

## 14 · Observability & Health

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| O-01 | /health returns 200 | 11_PRODUCTION_READINESS.md | Smoke test | Live: app cannot boot due to ImportError get_user_by_id | FAIL | 2026-10-01 |
| O-02 | /health/deps returns 200 with dependency health JSON | 11_PRODUCTION_READINESS.md | Smoke test | Live: app cannot boot | FAIL | 2026-10-01 |
| O-03 | /health/ready returns 200 when all deps healthy | 11_PRODUCTION_READINESS.md | Smoke test | Live: app cannot boot | FAIL | 2026-10-01 |
| O-04 | /health/ready fails closed when Valkey is down | 11_PRODUCTION_READINESS.md | Chaos test | | UNVERIFIABLE | |
| O-05 | /health/ready fails closed when DB is down | 11_PRODUCTION_READINESS.md | Chaos test | | UNVERIFIABLE | |
| O-06 | /metrics exposes Prometheus metrics | 11_PRODUCTION_READINESS.md | curl /metrics returns metrics | CONTRADICTION-003: prometheus_client used directly in metrics.py and valkey/client.py | FAIL | 2026-10-01 |
| O-07 | All logs use structlog with user_id, request_id, domain, action | 11_PRODUCTION_READINESS.md | Log samples | | UNVERIFIABLE | |
| O-08 | Auth failures, 403s, rate-limit triggers logged at WARNING+ | 11_PRODUCTION_READINESS.md | Log samples | SEC-AUTH-002: rate-limit triggers not logged via log_security_event | FAIL | 2026-10-01 |
| O-09 | Unhandled exceptions reported to GlitchTip | 11_PRODUCTION_READINESS.md | GlitchTip dashboard | | UNVERIFIABLE | |
| O-10 | Frontend errors reported to GlitchTip | 11_PRODUCTION_READINESS.md | GlitchTip dashboard | | UNVERIFIABLE | |
| O-11 | Circuit breakers wrap all external provider calls | 11_PRODUCTION_READINESS.md | Code review infrastructure/observability/circuit_breaker.py | SEC-CB-001: circuit breakers missing for oauth.py, apple.py, bank_api.py, ip.py, huggingface.py | FAIL | 2026-10-01 |
| O-12 | Circuit breakers fail open/closed correctly | 11_PRODUCTION_READINESS.md | Provider test | | UNVERIFIABLE | |
| O-13 | Dead-letter queue exists and is monitored for failed events/jobs | 11_PRODUCTION_READINESS.md | Infrastructure review | | UNVERIFIABLE | |
| O-14 | Request tracing carries request_id through all service calls | 11_PRODUCTION_READINESS.md | Log samples | | UNVERIFIABLE | |
| O-15 | Prometheus alerts are configured for critical paths | 11_PRODUCTION_READINESS.md | Alertmanager config | | UNVERIFIABLE | |
| O-16 | Grafana dashboards exist for latency, error rate, throughput | 11_PRODUCTION_READINESS.md | Dashboard URLs | | UNVERIFIABLE | |
| O-17 | Uptime monitor is configured from external vantage point | 11_PRODUCTION_READINESS.md | Monitor config | | UNVERIFIABLE | |

---

## 15 · Provider Resilience

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| PR-01 | All providers expose HAS_<SDK> boolean flags | 11_PRODUCTION_READINESS.md | Code review _base.py | | UNVERIFIABLE | |
| PR-02 | Domains handle missing SDKs via HAS_<SDK> flags (never crash) | 11_PRODUCTION_READINESS.md | Provider test test_provider_isolation.py | | UNVERIFIABLE | |
| PR-03 | Payment providers have circuit breaker | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| PR-04 | Payment providers have retry with backoff (1-2-4-8s, jitter, max 5) | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| PR-05 | Payment gateway health degrades gracefully (smart routing fallback) | 11_PRODUCTION_READINESS.md | Code review payment_orchestrator.py | | UNVERIFIABLE | |
| PR-06 | SMS provider has retry + fallback | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| PR-07 | Email provider has retry + fallback | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| PR-08 | WhatsApp provider has retry + fallback | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| PR-09 | AI providers (ollama, embeddings) have fallback when unavailable | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| PR-10 | Storage provider (R2) has presigned URL fallback | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| PR-11 | Geography / IP provider has fallback when unavailable | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| PR-12 | All provider errors are mapped to domain exceptions (no raw SDK errors leak) | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| PR-13 | All providers expose health_check() | 11_PRODUCTION_READINESS.md | Code review _base.py | | UNVERIFIABLE | |
| PR-14 | /health/deps reports provider health | 11_PRODUCTION_READINESS.md | /health/deps JSON | | UNVERIFIABLE | |
| PR-15 | Provider timeouts are configured and enforced | 11_PRODUCTION_READINESS.md | Config review | | UNVERIFIABLE | |

---

## 16 · Operations

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| OPS-01 | Migrations run in CI before deploy | 11_PRODUCTION_READINESS.md | CI workflow deploy.yml | | UNVERIFIABLE | |
| OPS-02 | Migrations are backward-compatible (expand-contract) | 11_PRODUCTION_READINESS.md | Migration review | | UNVERIFIABLE | |
| OPS-03 | Web replicas never auto-migrate on boot | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| OPS-04 | Celery Beat scheduler boots and fires scheduled jobs | 11_PRODUCTION_READINESS.md | Logs / scheduler status | | UNVERIFIABLE | |
| OPS-05 | Celery workers process tasks from Valkey broker | 11_PRODUCTION_READINESS.md | Worker logs | | UNVERIFIABLE | |
| OPS-06 | DLQ exists and is monitored for failed jobs | 11_PRODUCTION_READINESS.md | DLQ review | | UNVERIFIABLE | |
| OPS-07 | Finance scheduler jobs (payout, reconciliation, accruals) are tested | 11_PRODUCTION_READINESS.md | Job test artifact | | UNVERIFIABLE | |
| OPS-08 | Fraud monitoring runs on schedule | 11_PRODUCTION_READINESS.md | Job log | | UNVERIFIABLE | |
| OPS-09 | Ghost order detector runs daily | 11_PRODUCTION_READINESS.md | Job log | | UNVERIFIABLE | |
| OPS-10 | Data retention job runs weekly | 11_PRODUCTION_READINESS.md | Job log | | UNVERIFIABLE | |
| OPS-11 | Threat feed updater runs hourly | 11_PRODUCTION_READINESS.md | Job log | | UNVERIFIABLE | |
| OPS-12 | News ingester runs on schedule | 11_PRODUCTION_READINESS.md | Job log | | UNVERIFIABLE | |
| OPS-13 | AI embeddings sync runs nightly | 11_PRODUCTION_READINESS.md | Job log | | UNVERIFIABLE | |
| OPS-14 | KPI watchdog runs hourly | 11_PRODUCTION_READINESS.md | Job log | | UNVERIFIABLE | |
| OPS-15 | Event outbox relay is functional | 11_PRODUCTION_READINESS.md | Integration test | | UNVERIFIABLE | |
| OPS-16 | Rollback procedure is documented and tested | 11_PRODUCTION_READINESS.md | RUNBOOKS.md + drill record | | UNVERIFIABLE | |
| OPS-17 | Backup restore has been tested within last 30 days | 11_PRODUCTION_READINESS.md | Restore log | | UNVERIFIABLE | |
| OPS-18 | Coolify zero-downtime rolling deploy works | 11_PRODUCTION_READINESS.md | Deploy log | | UNVERIFIABLE | |
| OPS-19 | Environment promotion: dev -> staging -> production is documented | 11_PRODUCTION_READINESS.md | SETUP.md or runbook | OPS-19: SETUP.md missing at repo root | FAIL | 2026-10-01 |

---

## 17 · Country Management

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| C-01 | Country CRUD is functional (admin) | 14_country_management.md | Admin E2E test | | UNVERIFIABLE | |
| C-02 | Country config versioning works (draft -> approve -> publish -> rollback) | 14_country_management.md | Admin E2E test | | UNVERIFIABLE | |
| C-03 | Country-specific tax rates are configurable and applied at checkout | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| C-04 | Country-specific commission rates are configurable | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| C-05 | Country-specific payment gateways are configurable | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| C-06 | Country-specific logistics settings are configurable | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| C-07 | Country-specific legal docs (ToS, Privacy, Supplier Agreement) are generated | 14_country_management.md | Code review + test | | UNVERIFIABLE | |
| C-08 | Country staff assignments sync RLS + permissions | 14_country_management.md | Architecture test test_law5_country_isolation.py | | UNVERIFIABLE | |
| C-09 | RLS enforces country_code session context on all queries | 14_country_management.md | Architecture test test_rls_runtime.py | | UNVERIFIABLE | |
| C-10 | Feature flags can be rolled out per country | 14_country_management.md | Admin E2E test | | UNVERIFIABLE | |
| C-11 | Currency conversion uses exact arithmetic (Decimal) | 14_country_management.md | Code review + test | C-11: Float-for-money in currency paths | FAIL | 2026-10-01 |
| C-12 | FX revaluation job runs at month-end | 14_country_management.md | Job log | | UNVERIFIABLE | |
| C-13 | Country AI assistant is functional and cached | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| C-14 | Cross-border logistics rules are enforced | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| C-15 | Country-specific compliance rules (GCC labor law, etc.) are enforced | 14_country_management.md | Integration test | | UNVERIFIABLE | |

---

## 18 · Tax & Calculations

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| TX-01 | Tax calculation engine handles all applicable jurisdictions | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| TX-02 | Tax values are rounded and stored in smallest currency unit | 14_country_management.md | Schema review + test | | UNVERIFIABLE | |
| TX-03 | Tax is inclusive/exclusive per country config | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| TX-04 | Commission waterfall: global -> category -> badge -> supplier override | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| TX-05 | Commission is calculated on order delivery event | 14_country_management.md | Subscriber test | | UNVERIFIABLE | |
| TX-06 | Discount/coupon validation checks expiry, usage limit, min-order | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| TX-07 | Discount stacking rules are enforced | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| TX-08 | Order total calculation uses exact arithmetic (Decimal, never float) | 14_country_management.md / 18_security.md | Code review + test | TX-08: Float for order total calc | FAIL | 2026-10-01 |
| TX-09 | Currency conversion uses cached rates + Decimal arithmetic | 14_country_management.md | Integration test | TX-09: Float in currency conversion | FAIL | 2026-10-01 |
| TX-10 | FX revaluation auto-posts at month-end | 14_country_management.md | Job test | | UNVERIFIABLE | |
| TX-11 | Promotion ledger is immutable and audited | 14_country_management.md | Code review | | UNVERIFIABLE | |
| TX-12 | Refund calculations reconcile to original payment | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| TX-13 | VAT/tax remittance aggregation is correct | 14_country_management.md | Finance test | | UNVERIFIABLE | |
| TX-14 | Commission values reconcile to finance ledger | 14_country_management.md | Reconciliation test | | UNVERIFIABLE | |

---

## 19 · Location / Geography

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| G-01 | IP geolocation resolves country correctly | 14_country_management.md | Provider test | | UNVERIFIABLE | |
| G-02 | Country detection falls back: JWT -> staff assignment -> IP -> header | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| G-03 | Geo-fence validation works for check-in / attendance | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| G-04 | Distance calculation is accurate for logistics routing | 14_country_management.md | Provider test | | UNVERIFIABLE | |
| G-05 | Maps render correctly (Leaflet web / react-native-maps mobile) | 14_country_management.md | Component test | | UNVERIFIABLE | |
| G-06 | Address validation / formatting works per country | 14_country_management.md | Service test | | UNVERIFIABLE | |
| G-07 | Region restrictions (shipping eligibility) are enforced | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| G-08 | GPS tracking attaches to shipment events | 14_country_management.md | Integration test | | UNVERIFIABLE | |

---

## 20 · Catalog Management

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| CAT-01 | Product CRUD (create, read, update, soft-delete) is functional | 08_FEATURE_HEALTH.md | Integration test | | UNVERIFIABLE | |
| CAT-02 | Category hierarchy (parent/child) is functional | 08_FEATURE_HEALTH.md | Integration test | | UNVERIFIABLE | |
| CAT-03 | Category reordering works | 08_FEATURE_HEALTH.md | Admin E2E test | | UNVERIFIABLE | |
| CAT-04 | Category bulk archive/restore works | 08_FEATURE_HEALTH.md | Admin E2E test | | UNVERIFIABLE | |
| CAT-05 | Inventory management tracks stock per variant | 08_FEATURE_HEALTH.md | Integration test | | UNVERIFIABLE | |
| CAT-06 | Low-stock alert triggers at <=5 units | 08_FEATURE_HEALTH.md | Integration test | | UNVERIFIABLE | |
| CAT-07 | Product search uses hybrid FTS + pg_trgm + optional pgvector | 08_FEATURE_HEALTH.md | Search test | | UNVERIFIABLE | |
| CAT-08 | Autocomplete works for search queries | 08_FEATURE_HEALTH.md | Search test | | UNVERIFIABLE | |
| CAT-09 | Filter/sort works on catalog listing | 08_FEATURE_HEALTH.md | Integration test | | UNVERIFIABLE | |
| CAT-10 | Product variants (color, size) are manageable | 08_FEATURE_HEALTH.md | Integration test | | UNVERIFIABLE | |
| CAT-11 | Bulk CSV import validates and processes rows | 08_FEATURE_HEALTH.md | Integration test | | UNVERIFIABLE | |
| CAT-12 | Bulk CSV export produces valid file | 08_FEATURE_HEALTH.md | Integration test | | UNVERIFIABLE | |
| CAT-13 | Product moderation queue is functional | 08_FEATURE_HEALTH.md | Admin E2E test | | UNVERIFIABLE | |
| CAT-14 | Product verification queue is functional | 08_FEATURE_HEALTH.md | Admin E2E test | | UNVERIFIABLE | |
| CAT-15 | Credibility badge is computed and displayed | 08_FEATURE_HEALTH.md | Integration test | | UNVERIFIABLE | |
| CAT-16 | Discount / compare_price window is enforced | 08_FEATURE_HEALTH.md | Integration test | | UNVERIFIABLE | |
| CAT-17 | Product image gallery supports multiple images + video | 08_FEATURE_HEALTH.md | Component test | | UNVERIFIABLE | |
| CAT-18 | Facet counts refresh on schedule | 08_FEATURE_HEALTH.md | Job log | | UNVERIFIABLE | |

---

## 21 · Photo / Video / Media Management

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| MED-01 | Image upload uses presigned URLs (direct client -> R2) | 17_photo_video_media_management.md | Code review + network trace | | UNVERIFIABLE | |
| MED-02 | Uploaded files are validated via magic bytes (puremagic) | 17_photo_video_media_management.md | Code review | | UNVERIFIABLE | |
| MED-03 | Images are optimized to WebP/AVIF | 17_photo_video_media_management.md | Build output / image audit | | UNVERIFIABLE | |
| MED-04 | EXIF metadata is stripped from uploaded images | 17_photo_video_media_management.md | Code review Pillow usage | | UNVERIFIABLE | |
| MED-05 | Background removal (rembg) runs in async_workers | 17_photo_video_media_management.md | Code review | | UNVERIFIABLE | |
| MED-06 | Background removal respects BG_MAX_CONCURRENT, BG_MAX_IMAGE_DIM, memory limits | 17_photo_video_media_management.md | Config review + test | | UNVERIFIABLE | |
| MED-07 | Video processing (transcode, captions) is functional | 17_photo_video_media_management.md | Integration test | | UNVERIFIABLE | |
| MED-08 | Media CDN base URL (R2_CDN_BASE) is configured and reachable | 17_photo_video_media_management.md | curl CDN URL | | UNVERIFIABLE | |
| MED-09 | Presigned URL TTL is configured (R2_PRESIGN_TTL_SECONDS) | 17_photo_video_media_management.md | Config review | | UNVERIFIABLE | |
| MED-10 | Media permissions are enforced (owner/admin only) | 17_photo_video_media_management.md | Security test | | UNVERIFIABLE | |
| MED-11 | Large file uploads are chunked or timed out appropriately | 17_photo_video_media_management.md | Code review | | UNVERIFIABLE | |
| MED-12 | Image similarity / duplicate detection works (CLIP/ONNX) | 17_photo_video_media_management.md | Integration test | | UNVERIFIABLE | |
| MED-13 | Barcode / QR generation and scanning work | 17_photo_video_media_management.md | Integration test | | UNVERIFIABLE | |
| MED-14 | OCR document parsing works for invoices/IDs | 17_photo_video_media_management.md | Integration test | | UNVERIFIABLE | |


---

## 22 · Supply Chain Security

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| SC-01 | SBOM (Software Bill of Materials) is generated and stored | 28_supply_chain_security.md | SBOM artifact in CI | | UNVERIFIABLE | |
| SC-02 | All dependencies are scanned for known vulnerabilities (pip-audit / npm audit) | 28_supply_chain_security.md | CI artifact; zero high/critical | SEC-DEP-001: No CVE scanning tool in CI/CD | FAIL | 2026-10-01 |
| SC-03 | Container image is signed (Docker Content Trust / Sigstore) | 28_supply_chain_security.md | docker trust inspect | | UNVERIFIABLE | |
| SC-04 | Git commits are signed (GPG/SSH signature verified in CI) | 28_supply_chain_security.md | CI log shows verified signatures | | UNVERIFIABLE | |
| SC-05 | CI pipeline verifies integrity of build artifacts | 28_supply_chain_security.md | CI artifact hash check | | UNVERIFIABLE | |
| SC-06 | No unknown binaries or scripts in production container image | 28_supply_chain_security.md | Trivy / docker scout | | UNVERIFIABLE | |
| SC-07 | Dependency versions are pinned (no floating ranges in lockfiles) | 28_supply_chain_security.md | Lockfile review | Live: uv.lock and pnpm-lock.yaml present; requirements.txt may have floating versions | FAIL | 2026-10-01 |
| SC-08 | License compliance is checked (no GPL in proprietary product) | 28_supply_chain_security.md | License scanner artifact | | UNVERIFIABLE | |
| SC-09 | Third-party components are inventoried and reviewed | 28_supply_chain_security.md | Third-party audit log | | UNVERIFIABLE | |
| SC-10 | Build is reproducible from source + lockfile + SBOM | 28_supply_chain_security.md | Reproducibility test | | UNVERIFIABLE | |

---

## 23 · Production Readiness Gate

> **Rule:** Production is declared ready only when every check above is PASS or DEFERRED (with documented acceptance).
> A single FAIL blocks production exposure until resolved or formally accepted via waiver.

| Gate | Requirement | Result |
|------|-------------|--------|
| All P0 security findings resolved | Zero open CRITICAL findings | FAIL — SEC-AUTH-001, SEC-ENC-001, SEC-ENC-002, SEC-DEVBIND-001, SEC-WEB-002, SEC-WEB-003, SEC-WEB-004, SEC-WEB-005, SEC-WEB-006 |
| Frontend builds clean | next build exits 0 | FAIL — PERF-007: missing Timer export from src/lib/icons.ts |
| Backend boots with full route set | App boots to ready state | FAIL — 15 module routers fail to import with ImportError get_current_user from infrastructure.utils.dependencies; 0 routes mounted |
| Browser behavioral tests pass | All Playwright specs green | FAIL — BROWSER-001: 23 failed tests in last run |
| Test suite collection clean | pytest exits 0 with zero collection errors | FAIL — 4509 collected, 17 collection errors (ImportError get_current_user, ModuleNotFoundError domains.finance.services.payments, fastapi_limiter_valkey Limiter) |
| All 28 dimensions audited | Dimension files present and current | PASS |
| Single indicator file updated | This checklist is current | PASS |
| Waivers documented | Any DEFERRED item has signed waiver | UNVERIFIABLE |
| Float money math eliminated | No float used for monetary values in cart, orders, tax | FAIL — FEAT-001, FEAT-002, FEAT-003, FEAT-009, FEAT-010 |
| Payment credentials encrypted | All payment gateway credentials encrypted at rest | FAIL — FEAT-005, FEAT-022 |
| Inventory claim/release wired | Inventory claimed on confirm, released on cancel/refund | FAIL — FEAT-004, FEAT-025 |

**Production Ready:** NO

**Overall Production Readiness: 10.1% (37 PASS / 366 total checks)**

**Assessment Date:** 2026-10-01

**Next Review Date:** After all FAIL / UNVERIFIABLE items are retested

---

## 24 · Completion Blockers

> These are findings marked `project_completion_blocker = yes` in dimension files.
> They MUST be resolved before production exposure.

| ID | Finding | Dimension | File:Line | Status |
|----|---------|-----------|-----------|--------|
| PB-01 | python-jose in auth code (CVE-2025-61152, CVE-2026-85394) | 21_contradictions / 18_security | backend/infrastructure/security/auth.py:14; backend/providers/auth/jwt.py:9; backend/middleware/authentication_middleware.py:18 | FAIL |
| PB-02 | requests (sync HTTP) used in 8 production files | 21_contradictions | backend/domains/accounts/services/auth/auth_service.py:33,958; backend/providers/auth/oauth.py:17; backend/providers/auth/apple.py:21 | FAIL |
| PB-03 | TOTP secrets stored in plaintext (SEC-ENC-001) | 18_security | backend/domains/accounts/models/mfa_factor.py:45 | FAIL |
| PB-04 | Payment gateway credentials plaintext (SEC-ENC-002) | 18_security | backend/domains/finance/models/payments.py:94-126; backend/domains/finance/services/payments/payment_engine.py:3188-3196 | FAIL |
| PB-05 | Device binding not verified (SEC-DEVBIND-001) | 18_security | backend/middleware/device_binding_middleware.py:13-28 | FAIL |
| PB-06 | Tap webhook fail-open (SEC-WEB-002) | 18_security | backend/domains/finance/services/payments/gateway_tap.py:971-1003 | FAIL |
| PB-07 | PayPal webhook fail-open (SEC-WEB-003) | 18_security | backend/domains/finance/services/payments/gateway_paypal.py:388-490 | FAIL |
| PB-08 | PayTabs callback fail-open (SEC-WEB-004) | 18_security | backend/domains/finance/services/payments/gateway_tap.py:1083-1193 | FAIL |
| PB-09 | Thawani webhook fail-open (SEC-WEB-005) | 18_security | backend/domains/finance/services/payments/gateway_tap.py:1367-1423 | FAIL |
| PB-10 | Generic gateway webhook fail-open (SEC-WEB-006) | 18_security | backend/domains/finance/services/payments/payment_orchestrator.py:793-833 | FAIL |
| PB-11 | Prometheus metrics duplicate on import (BOOT-009) | 00_boot_smoke_test | backend/middleware/logging_middleware.py:17 | FAIL |
| PB-12 | Frontend build broken (BOOT-003, BOOT-007, PERF-007) | 00_boot_smoke_test / 19_performance | frontend/web_app/src/app/admin/analytics/page.tsx:12 | FAIL |
| PB-13 | Alembic script_location missing (BOOT-005, PF-003) | 00_boot_smoke_test / 27_project_completion_blockers | backend/alembic.ini:1 | FAIL |
| PB-14 | POSTGRES_PASSWORD empty / missing (BOOT-010, PF-004) | 00_boot_smoke_test / 27_project_completion_blockers | .env:1 | FAIL |
| PB-15 | pnpm-lock.yaml absent (PF-005) | 27_project_completion_blockers | frontend/web_app | FAIL |
| PB-16 | tests/architecture/ directory missing (PF-006) | 27_project_completion_blockers | tests/architecture/ | FAIL |
| PB-17 | Production cache is no-op shim (PERF-005) | 19_performance | backend/infrastructure/utils/cache.py:19-70 | FAIL |
| PB-18 | Browser tests last run failed (BROWSER-001) | 24_browser_behavior | _browser_test/reports/artifacts/.last-run.json:2 | FAIL |
| PB-19 | Float arithmetic in cart totals (FEAT-001) | 16_features | backend/domains/orders/services/orders_service.py:142 | FAIL |
| PB-20 | Float rounding in order serialization (FEAT-002) | 16_features | backend/domains/orders/services/orders_service.py:309 | FAIL |
| PB-21 | Float serialization of product prices (FEAT-003) | 16_features | backend/domains/catalog/services/products/products_service.py:132 | FAIL |
| PB-22 | Missing inventory claim/release on order transitions (FEAT-004) | 16_features | backend/domains/orders/services/core/order_engine.py | FAIL |
| PB-23 | Payment gateway credentials plaintext (FEAT-005) | 16_features | backend/domains/finance/models/payments.py:34 | FAIL |
| PB-24 | Float math in cart totals endpoint (FEAT-009) | 16_features | backend/modules/customer/routers/orders.py:142 | FAIL |
| PB-25 | Float input to tax calculation (FEAT-010) | 16_features | backend/modules/customer/routers/orders.py:175 | FAIL |
| PB-26 | Plaintext payment gateway credentials JSON (FEAT-022) | 16_features | backend/domains/finance/models/payments.py:88 | FAIL |
| PB-27 | Missing inventory claim/release in order engine (FEAT-025) | 16_features | backend/domains/orders/services/orders_service.py:259 | FAIL |
| PB-28 | Float in tax calculation via ledger (FEAT-040) | 16_features | backend/domains/finance/services/ledger/general_ledger.py | FAIL |

> **Note:** This table must be updated after each audit pass. Remove rows only when the finding is resolved and verified.

---

## 25 · Sign-Off

| Role | Name | Signature | Date | Status |
|------|------|-----------|------|--------|
| Lead Auditor | | | | Pending |
| Security Reviewer | | | | Pending |
| Backend Lead | | | | Pending |
| Frontend Lead | | | | Pending |
| DevOps / SRE | | | | Pending |
| Product Owner | | | | Pending |

**Assessment Conducted By:** Kilo (Automated Forensic Auditor) + Live Verification Run 3 + Forensic Audit Run 5
**Assessment Date:** 2026-10-01
**Production Readiness: NOT PRODUCTION READY — 495 findings (55 P0, 154 P1, 233 P2, 22 P3), 139 completion blockers, 14 dimensions FAIL, launch gate 1 pass / 14 fail / 3 unverifiable**
**Next Review Date:** After all FAIL / UNVERIFIABLE items are retested

---

## Appendices

### Appendix A · Dimension-to-Check Mapping

| Section | Dimension File | Dimension Name |
|---------|----------------|----------------|
| Canonical Document Alignment | 01_EXECUTIVE_SUMMARY.md | Executive Summary |
| Technology Stack | 18_security.md, 21_contradictions.md | Security, Contradictions |
| Architecture | 21_contradictions.md, 09_ANTI_PATTERNS.md | Contradictions, Anti-Patterns |
| Feature Completeness | 08_FEATURE_HEALTH.md | Feature Health |
| Backend Runtime | 11_PRODUCTION_READINESS.md | Production Readiness |
| Frontend Build & Runtime | 11_PRODUCTION_READINESS.md, 21_contradictions.md | Production Readiness, Contradictions |
| Mobile Build | 15_frontend_mobile.md | Frontend Mobile |
| Tests -- Backend | 12_tests.md, 11_PRODUCTION_READINESS.md | Tests, Production Readiness |
| Security | 18_security.md | Security |
| Database | 21_contradictions.md, 11_PRODUCTION_READINESS.md | Contradictions, Production Readiness |
| Frontend UI | 24_browser_behavior.md | Browser Behavior |
| Frontend Workflows | 24_browser_behavior.md | Browser Behavior |
| Browser Behavioral Tests | 24_browser_behavior.md | Browser Behavior |
| Performance & Fast Loading | 19_performance.md, 11_PRODUCTION_READINESS.md | Performance, Production Readiness |
| Observability & Health | 11_PRODUCTION_READINESS.md, 20_observability_resilience.md | Production Readiness, Observability |
| Provider Resilience | 11_PRODUCTION_READINESS.md, 08_providers.md | Production Readiness, Providers |
| Operations | 11_PRODUCTION_READINESS.md, 10_migrations.md | Production Readiness, Migrations |
| Country Management | 14_country_management.md | Country Management |
| Tax & Calculations | 14_country_management.md | Country Management |
| Location / Geography | 14_country_management.md | Country Management |
| Catalog Management | 08_FEATURE_HEALTH.md | Feature Health |
| Photo / Video / Media Management | 17_photo_video_media_management.md | Photo/Video/Media Management |
| Supply Chain Security | 28_supply_chain_security.md | Supply Chain Security |

### Appendix B · How to Update This Document After Each Audit Pass

1. Open this file in an editor.
2. For each check, update Status to PASS / FAIL / DEFERRED / UNVERIFIABLE.
3. Fill in the Evidence column with the exact file path, command output, or test artifact.
4. Update the Last verified column with the date (YYYY-MM-DD).
5. Refresh the **Summary Dashboard** counts.
6. Update **Production Ready:** YES / NO.
7. Update the **Completion Blockers** table: remove resolved blockers, add new ones.
8. Commit the updated checklist with message: docs: update production readiness checklist — <date>.

### Appendix C · Abbreviations

| Abbreviation | Meaning |
|--------------|---------|
| CVE | Common Vulnerabilities and Exposures |
| RLS | Row-Level Security |
| SBOM | Software Bill of Materials |
| CLS | Cumulative Layout Shift |
| LCP | Largest Contentful Paint |
| INP | Interaction to Next Paint |
| TTFB | Time to First Byte |
| RBAC | Role-Based Access Control |
| MFA | Multi-Factor Authentication |
| DLQ | Dead-Letter Queue |
| FX | Foreign Exchange |
| PII | Personally Identifiable Information |
| WCAG | Web Content Accessibility Guidelines |
| EAS | Expo Application Services |
| CI/CD | Continuous Integration / Continuous Deployment |
| SBOM | Software Bill of Materials |

