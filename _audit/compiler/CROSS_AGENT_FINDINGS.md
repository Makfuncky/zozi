# CROSS-AGENT FINDINGS BRIEF — compiler run 8

> Established by batch 1 and batch 2 verification agents, each independently
> verified against live source. **Treat these as leads to corroborate, not as
> settled fact.** If your dimension contradicts one of these, verify it yourself
> and report the conflict loudly — do not defer to this document.
>
> Sibling output: `_audit/compiler/verdicts/*.json`. Do not edit those files.

---

## T1 · The "providers/metrics.py Gauge import failure" P0 is FALSE
Two agents independently refuted it. `backend/providers/metrics.py` **does not
exist**; `backend/providers/` holds only `__init__.py _base.py _helpers.py
async_workers.py config.py http.py observability.py`. The real module is
`backend/infrastructure/observability/metrics.py`; line 2 imports `Gauge` from
`prometheus_fastapi_instrumentator.middleware`, which does export it, and
`import providers` succeeds. The `pytest tests/providers` failures come from
leaked `sk_test_dummy` credentials and a `ModuleNotFoundError` for `boto3` at
`infrastructure/storage/storage.py:27`. `prometheus-client==0.26.0` **is**
present standalone (`requirements.txt:62`, `pyproject.toml:35`), which
TECHNOLOGY_STACK §9 forbids and which is redundant via the instrumentator.
`tests/providers` collects 1312 tests with no collection error.

## T2 · Migration chain: 1 head, merge-shaped, NOT linear, NOT divergent
75 migration files, 75 distinct revision ids, 0 duplicates, **1 head
`20261001_0001`**. Law 49 is PARTIAL: 4 branch points resolved by 3 merge
migrations, every parent ancestry-walked. The audit's "5 divergent heads" and
"62 heads" claims are **stale/false**. Separately, `backend/alembic/check_migration_naming.py`
is itself buggy (truncates revision at the first `_`, 34 false errors), so the
"64/66 = 97%" figure counts tool output rather than the rule.

## T3 · `_validate_production` DOES enforce required secrets
`backend/config.py:598-776` is a `mode="after"` validator, early-returning
unless `app_env == "production"`, with ~40 explicit `raise ValueError`. 21
variables were blanked one at a time; all 21 raised. Law 82 (empty default) and
Law 83 (validate at startup) are BOTH satisfied. Residual defect is message
quality, not enforcement: `env_ignore_empty=True` (`:97`) often surfaces a
generic pydantic message instead of the named assertion, and `AUDIT_CHAIN_KEY`'s
effective floor is 16 chars, not the intended 32. A second validator at
`:384-452` requires ~51 settings outside production.

## T4 · No committed secrets; `health_test_*.py` are empty
`.env` and `backend/.env` are **not tracked** (only `.env.example`,
`.env.wrangler`, `backend/.env.example` are). `.gitignore:15-16` covers them.
Real dev values exist on disk (`backend/.env:4` is a 19-char `sqlite://` URL —
a local dev profile, sanctioned by Law 204). All 75 `health_test_*.py` contain
a `SECRET_KEY` line and all 75 assign `""` — the claimed leak is **refuted**.
Two real Law 32 violations do remain, both in `monitoring/` (not gitignored):
a Grafana admin password at `:72` and a sentry-db superuser password at `:127`.

## T5 · `backend/modules/employee/routers/hr.py` is DEAD CODE
The `hr/` package shadows the same-named `hr.py` module. `hr.py` is 55921
bytes / 97 declared routes and is **unreachable**. The live routes are in
`hr/*.py` (e.g. `hr/ess.py:45` leave balance, `:76` attendance, `:69` payslip;
`hr/employees.py:107` kill-switch). Any finding citing `hr.py` lines is citing
a file that never loads. Verified: employee router IS mounted via
`backend/main.py:360-380`; live app exposes 738 paths, 85 under
`/api/v1/employee/hr`. `/hr/tasks/stats` and `/hr/workspace` have **zero**
backend occurrences anywhere.

## T6 · `permissions.ts` is badly drifted — regenerate, never edit
Backend `rbac/catalog.py` holds **367 atoms / 19 namespaces** (the audit's
"231" is stale). `frontend/shared/src/permissions.ts` has **177**. That is 78
frontend-only atoms that do not exist, and 268 backend atoms missing.
Worse: `generate-permissions.mjs` emits `BUILD_TIME_FEATURES`, `_NAMESPACES`
and `_FEATURE_LIST`, identifiers **absent from the committed file** — so
running the generator would break every importer of `FEATURE_CATALOG` /
`FEATURE_SET` / `isKnownFeature`. The generator contract must be reconciled
before regeneration.

## T7 · Role vocabulary is four-way divergent
The admin roles `sub_admin / moderator / finance_officer / country_manager /
auditor` **are** present in `_ROLE_FEATURES` and `_ROLE_MODULES`
(`backend/rbac/dependencies.py:90-180`) — that part of the audit is stale. But
`VALID_USER_ROLES` (`catalog.py:14`) was **not** updated, so
`update_user_role` (`user_management_service.py:386`) still 400s on
`finance_officer`, `country_manager` and `auditor`. The roles exist but are
unreachable.

## T8 · Gates that exist but can never pass — worse than missing gates
AST scan of 1007 endpoints: 58 lack any gate, 49 have no auth dependency. But
the higher-severity class is **unreachable gates**: 47 of 51 customer-module
gates 403 for `role="customer"` (effective set is 6 atoms), so cart,
`orders.create`, `orders.cancel`, returns, tracking, coupons, password change
and MFA are all broken. Logistics 31/31, employee 51/54, supplier 22/43.
**22 live gate literals are absent from the catalog** and so 403 even for
`super_admin`: `support.read/reply/update` (`admin/routers/tickets.py:43,67,82,109`),
`moderation.suppliers` (`disputes.py:35,64,77`),
`promotions.flash_sales.read/write` (`promotions.py:134,160,193,226`). Admin
tickets and supplier disputes are 100% broken. Also 9 router files are
unregistered (Law 135).

## T9 · Frontend: Tailwind v4 confirmed, config dead, types unchecked
- `tailwindcss` 4.3.3 + `@tailwindcss/postcss`; `globals.css:3` is
  `@import "tailwindcss"`. **No `@config` directive anywhere**, so the
  235-line `tailwind.config.js` never loads. ~174 usages of custom classes
  (`text-3xs` 128x/42 files, `text-4xs` 30x/11, `text-5xs` 15x/5,
  `max-w-11xl` 7x/7) emit **no CSS at all**. Confirmed against a fresh build.
- `@tanstack/react-query` present in 3 files (`providers.tsx:3`,
  `QueryErrorBoundary.tsx:16`, `queryStates.ts:14`) — Law 171 violation, not in
  `pnpm-lock.yaml`, `MODULE_NOT_FOUND`. `swr`: 0.
- **Both lockfiles present** (`pnpm-lock.yaml` and `package-lock.json`);
  `vercel.json` deploys via `npm install --legacy-peer-deps`.
- `next.config.ts:6-8` sets `ignoreBuildErrors: true`. `next build` exits 0
  while `tsc --noEmit` reports **119 errors across 29 files**. That
  suppression is what keeps Law 186 looking satisfied.
- No Cloudflare Pages config (`wrangler.toml`/`_headers`) anywhere.

## T10 · CI security scanning is entirely absent
Grep for `pip-audit|gitleaks|trivy|npm audit|dependabot|cosign|syft` across all
five workflows returns **zero hits**. `.github/dependabot.yml` does not exist.
gitleaks exists only as a pre-commit hook (`.pre-commit-config.yaml:31-34`).
A prior audit row asserted these scanners were COMPLIANT — that assertion is
false. `pip-audit 2.10.1` was run read-only and found **52 vulnerabilities in 3
packages**: pillow 12.2.0 (25), starlette 0.40.0 (14), pyjwt 2.13.0 (13).
`uv.lock` is committed with exact pins + 502 sha256 hashes and is used with
`--frozen` at all 4 install sites, but a **shadowing committed
`requirements.txt`** diverges from it (fastapi 0.141.0 there vs 0.115.2 in
`uv.lock`; `starlette` unpinned at line 11) and both Dockerfiles install from
it, so containers follow the ungoverned manifest.

## T11 · Confirmed benchmark-vs-benchmark contradictions (user must resolve)
- **TT-01 dev database.** `ARCHITECTURE_STACK.md:634` (Law 108) "Per-developer
  Neon branch is the dev database"; `:741` (Law 215) "No local Postgres
  container". `TECHNOLOGY_STACK.md:42` "Never point dev at Neon"; `:45` "use
  the local Postgres DSN"; `:279` "Includes a local Postgres 16 container".
  TECH also self-conflicts at `:291` and `:305`. The repo encodes both sides.
- **TT-02 `DEFAULT_COUNTRY`.** `TECHNOLOGY_STACK.md:392` says `US`;
  `:564` says `AE`. `config.py:289` is `"US"` — satisfies one, violates the
  other.
- Record these as `BLOCKED_BY_CONTRADICTION` with both citations. **Never
  resolve a contradiction yourself** (resolver §0.14, §20).

## T12 · Three contradiction registers disagree
`_audit/07_CONTRADICTIONS.md` = 38 · `_audit/dimensions/21_contradictions.md` =
22 · `_audit/04_REMEDIATION_PLAN.md` = 0 (still "No contradictions yet").
Resolver §14 step 13 requires all three to match. It fails. Note it.

## T13 · `auth_service.py:2058` prints PII on every login
Confirmed verbatim. Law 58 (print, plus a function-local `import sys`) **and**
Law 282 (user id + email). It writes to stderr directly, so the `_scrub_pii`
structlog processor never runs — the email is **not** redacted. No packet record
covers this line. It is the highest-value new finding so far.

## T14 · Boot smoke baseline
`$env:PYTHONPATH="backend"; python -c "from backend.main import app; print(len(app.routes))"`
→ **84 routes** (85 with `PROMETHEUS_ENABLED` truthy). Valkey is unreachable in
this environment and degradation is graceful per Law 110: 3 jittered retries
then `valkey_fallback` WARNING, import continues. Boot also logs
`No module named 'infrastructure.utils.tracing'` — the module is actually at
`infrastructure/observability/tracing.py`, so OpenTelemetry is silently dead.

## T15 · Repository hygiene facts that keep recurring
- 75 `health_test_*.py` + 15 `_tmp_*.py` + ~5 `debug_*.py` at `backend/` root
  (Law 27). All `health_test_*` contribute ~300 raw env writes.
- No `_auto_stubs.py` exists anywhere — Law 28 is a no-op.
- All 6 forbidden root folders are absent — Law 18 is clean.
- ~20 `ARCHIVED MODULE … _parked` files still inside `domains/` (Law 27/28).
- Tests live in `backend/tests/` and a root `tests/`. The benchmark's
  `test/architecture/` path does **not** exist; that is why 24/55, 19/20 and
  41/42 named test paths were missing. **Most packet records are
  `FIX_UNTESTABLE` because their Test paths reference a `test/` tree that does
  not exist.** Flag this once per dimension rather than per record.
- `.kilo/worktrees/buttercup-rainbow/` holds a full unscanned repo duplicate.