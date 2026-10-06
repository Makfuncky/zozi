# ZOZI Browser Test Suite

Playwright E2E suite for the ZOZI multi-module commerce platform — **64 spec files, 302 tests** covering customer, supplier, logistics, admin, and employee modules plus cross-cutting concerns.

Spec-of-record: [`docs/PROMPT_BROWSER_TEST.md`](docs/PROMPT_BROWSER_TEST.md)

---

## Quick start

```powershell
cd _browser_test

npm install                       # once
npx playwright install chromium   # once
copy config\stack.env.ps1.example config\stack.env.ps1   # then edit the secrets
```

Start the services in separate terminals:

```powershell
cd ..\backend          ; python -m uvicorn main:app --host 0.0.0.0 --port 8000
cd ..\frontend\web_app ; npx next dev --port 3100
```

Then:

```powershell
npm run preflight   # environment only — fails loudly naming the service that is down
npm test            # full suite
npm run report      # open the HTML report
```

## Static gates (no servers required)

```powershell
node scripts\preTestScan.mjs   # resolves every import; fails on broken/out-of-scope ones
npm run typecheck              # tsc --noEmit
npm run test:list              # confirms all 302 tests load
```

Run these before pushing. `preTestScan` is what catches an unresolvable relative import — the failure mode that silently killed six specs.

## Scoped runs

```powershell
npm run test:auth           npm run test:admin        npm run test:customer
npm run test:supplier       npm run test:logistics    npm run test:employee
npm run test:cross-cutting
npm test -- -Grep "sidebar"
```

## Pipeline

```powershell
.\scripts\run-pipeline.ps1     # env → static scan → Playwright → reports/run/last-run.json
.\scripts\run-pipeline.ps1 -PlaywrightArgs @('--grep','admin')
```

## Layout

```
tests/
├── preflight.spec.ts     environment gates — halts the run if a service is down
├── database.spec.ts      schemas, migrations, seed data, constraints, RLS
├── auth/                 login, registration, session refresh, RBAC gates
├── modules/admin/        admin workspaces + the six security specs
├── modules/customer/     browse, cart, checkout, search, wishlist
├── modules/supplier/     registration, catalog, KYC, bulk, voice-to-catalog
├── modules/logistics/    quotes, scanning, fulfillment, parcel verification
├── modules/employee/     login, dashboard, orders, customers, HR
└── cross-cutting/        design system, mobile overflow, country RLS, scaling audit
```

Helpers live in `src/`: `api.ts` (REST, with `*Loud` variants that throw instead of
swallowing a 404), `auth.ts` (session bootstrap and form helpers), `ui.ts` (ZOZI
selectors and the overflow audit).

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `API_BASE_URL` | `http://127.0.0.1:8000` | Backend origin |
| `WEB_BASE_URL` | `http://127.0.0.1:3100` | SPA origin |
| `PW_WORKERS` | `1` | Keep at 1 — specs share seed state |
| `PW_TIMEOUT` | `120000` | Per-test ms; accepts `30_000` too |
| `PW_RETRIES` | `1` | Retries |
| `SEED_*_PASSWORD` | `E2e<Role>#2026` | Seeded account passwords |

## Security

`config/stack.env.ps1` holds real credentials and is **gitignored — never commit it**.
`config/stack.env.ps1.example` is the committed template. Generated output
(`reports/`, `test-results/`) is gitignored too.

## Before adding a spec

- Import from `src/`, never from `frontend/web_app/e2e/**` (that tree is read-only source of truth).
- Get the relative depth right: `../src/` from `tests/`, `../../src/` from `tests/auth/` and
  `tests/cross-cutting/`, `../../../src/` from `tests/modules/*/`. No `.ts` extension.
- Use `page.request` option `data`, never `body`.
- **Every test must assert.** A spec with no `expect()` is a green signal and will be flagged.
- Prefer the `*Loud` API helpers so a 404 or timeout cannot pass silently.
