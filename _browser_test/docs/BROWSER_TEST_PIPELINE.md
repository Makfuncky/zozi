# BROWSER_TEST_PIPELINE.md

> **Authority.** `_most_imp_docx/ARCHITECTURE_STACK.md` (structure, modules, domains, laws 1–325) and `_most_imp_docx/TECHNOLOGY_STACK.md` (versions, SDKs, infra).
>
> **Folder structure.** `_browser_test/tests/` uses 5 top-level items: 2 root spec files (`preflight.spec.ts`, `database.spec.ts`) + 3 folders (`auth/`, `modules/`, `cross-cutting/`). The `modules/` folder contains 5 sub-folders (`admin/`, `customer/`, `supplier/`, `logistics/`, `employee/`).

---

## 1 · Prerequisites

| Requirement | Command / Check | Status |
|---|---|---|
| Node.js 22.x | `node --version` | Must be 22.x |
| pnpm 10.x | `pnpm --version` | Must be 10.x |
| Python 3.13 | `python --version` | Must be 3.13.x |
| Playwright browsers | `cd _browser_test && npx playwright install chromium` | One-time |
| `config/stack.env.ps1` | `copy config\stack.env.ps1.example config\stack.env.ps1` then edit secrets | **Required** |
| Backend running | `curl http://127.0.0.1:8000/health` → `{"status":"healthy"}` | Must pass |
| Frontend running | `curl http://127.0.0.1:3100` → 200 HTML | Must pass |
| Valkey running | `redis-cli ping` → `PONG` | Non-fatal warnings ok |
| Postgres running | `psql $DATABASE_URL -c "SELECT 1"` | Non-fatal warnings ok |

---

## 2 · Quick Start

```powershell
# 1. Install Playwright browsers (once)
cd _browser_test
npx playwright install chromium

# 2. Configure environment
copy config\stack.env.ps1.example config\stack.env.ps1
# Edit config/stack.env.ps1 with real secrets (SECRET_KEY, DATABASE_URL, etc.)

# 3. Start backend (terminal 1)
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 4. Start frontend (terminal 2)
cd frontend/web_app
pnpm dev --port 3100

# 5. Run pipeline (terminal 3)
cd _browser_test
.\scripts\run-pipeline.ps1
```

---

## 3 · Folder Structure

```
_browser_test/
├── config/
│   └── stack.env.ps1          ← environment secrets (created from .example)
├── docs/
│   ├── BROWSER_TEST_PIPELINE.md  ← this file
│   ├── PROMPT_BROWSER_TEST.md    ← full prompt for porting/writing specs
│   └── README.md                 ← suite overview
├── scripts/
│   └── run-pipeline.ps1       ← CI-ready pipeline runner
├── src/
│   ├── auth.ts                ← ported from frontend/web_app/e2e/helpers/auth.ts
│   ├── api.ts                 ← ported from frontend/web_app/e2e/helpers/api.ts
│   └── ui.ts                  ← ZOZI-specific selectors and utilities
├── global-setup.ts            ← pre-flight verification (backend + frontend health)
├── global-teardown.ts         ← artifact consolidation (results.json → last-run.json)
├── playwright.config.ts       ← reporter, output, env-var-driven URLs
├── tests/
│   ├── preflight.spec.ts      ← environment readiness (no deps)
│   ├── database.spec.ts       ← migrations, seed, constraints, RLS
│   ├── auth/                  ← login, registration, session, RBAC gates
│   ├── modules/               ← all 5 module-specific test suites
│   │   ├── admin/             ← admin panel + security tests
│   │   ├── customer/          ← browse, cart, checkout, tracking
│   │   ├── supplier/          ← registration, upload, KYC, bulk, voice
│   │   ├── logistics/         ← pricing, switching, scan/delivery, COD
│   │   └── employee/          ← HR dashboard, orders, customers
│   └── cross-cutting/         ← design system, panels, country, visual
└── reports/                   ← screenshots, traces, JSON results
```

---

## 4 · Pipeline Execution Order

```
preflight.spec.ts          ← env readiness, no deps
    ↓
database.spec.ts           ← migrations, seed data, constraints
    ↓
auth/                      ← login, session, RBAC gates (depends on preflight + database)
    ↓
modules/admin/             ← all admin + employee + security (depends on auth + seed)
modules/customer/          ← browse, cart, checkout (depends on auth + seed)
modules/supplier/          ← registration, upload, KYC (depends on auth + seed)
modules/logistics/         ← pricing, switching, scan/delivery (depends on auth + seed)
modules/employee/          ← HR dashboard, orders (depends on auth + seed)
    ↓
cross-cutting/             ← panels, design system, visual (depends on all roles)
```

---

## 5 · What Each Category Covers

### `preflight.spec.ts`

Single root file. Verifies:
- Playwright chromium is installed and launchable
- `GET /health` returns 200
- `GET /health/deps` reports Valkey + Postgres connected
- Frontend serves on configured port
- `GET /rbac/catalog` returns 200 with feature array

**Failure behavior:** Halts pipeline immediately. Reports exact service that is down.

### `database.spec.ts`

Single root file. Write new:
- `test("Alembic heads are linear")` — assert single head
- `test("all 15 domain schemas exist")` — query `information_schema.schemata`
- `test("no tables in forbidden schemas")` — assert zero tables in `core`, `platform`, `identity`
- `test("seed countries are loaded")` — `GET /countries` returns AE, SA, OM, BH, KW, QA
- `test("seed admin user can authenticate")` — `POST /api/v1/auth/login` with `admin@zozi.com`
- `test("seed products have variants and stock")` — `GET /products?limit=50`
- `test("FK constraints prevent orphan order_lines")` — delete product with order_lines
- `test("unique constraints prevent duplicate emails")` — register same email twice
- `test("RLS blocks cross-country reads")` — login as AE admin, attempt `GET /orders?country=SA`

### `auth/`

Port from `frontend/web_app/e2e/`:
- `auth-role-login.spec.ts` — UI login smoke for admin, customer, supplier, logistics, employee
- `auth-registration-login.spec.ts` — registration page renders and submission flows

Write new:
- `auth-session-refresh.spec.ts` — silent refresh, token rotation, device binding, logout
- `auth-rbac-gates.spec.ts` — 403 on unauthorized features, cross-tenant isolation

### `modules/admin/`

Port from `frontend/web_app/e2e/` (14 files):
- `admin-commission.spec.ts`
- `admin-audit-fixes.spec.ts`
- `admin-country-control-plane.spec.ts`
- `admin-country-enhanced.spec.ts`
- `admin-communication-hub.spec.ts`
- `admin-data-ops.spec.ts`
- `admin-logistics-workspace.spec.ts`
- `admin-hr-permissions.spec.ts`
- `admin-modules-reconciliation.spec.ts`
- `admin-payment-gateways.spec.ts`
- `admin-supplier-logistics-sanity.spec.ts`
- `admin-treasury-payout.spec.ts`
- `finance-e2e.spec.ts`
- `finance-cod-proof-live.spec.ts`

Write new (security):
- `rbac-enforcement.spec.ts` — 403 on unauthorized access, cross-tenant isolation
- `csrf-protection.spec.ts` — POST without CSRF token returns 403
- `xss-protection.spec.ts` — UGC sanitized, CSP header present
- `rate-limiting.spec.ts` — 15 rapid logins return 429
- `rls-cross-tenant.spec.ts` — country_code blocks cross-country reads
- `input-validation.spec.ts` — oversized passwords, SQL injection, XSS in address fields

### `modules/employee/`

Write new:
- `employee-login.spec.ts` — UI + API bootstrap
- `employee-dashboard.spec.ts` — assigned orders, support tickets
- `employee-orders.spec.ts` — order detail, internal notes
- `employee-customers.spec.ts` — search, order history
- `employee-hr.spec.ts` — onboarding pipeline, HSE tab

### `modules/customer/`

Port from `frontend/web_app/e2e/`:
- `customer-core-flow.spec.ts` — browse → product detail → add to cart → checkout → order tracking
- `cross-border-checkout.spec.ts` — admin tax/gateway/logistics config → customer checkout

Write new:
- `customer-search.spec.ts` — category, price, rating, voice, image search
- `customer-cart.spec.ts` — cart persistence, quantity updates, empty cart, cross-border tax
- `customer-wishlist.spec.ts` — add to wishlist, persistence across sessions

### `modules/supplier/`

Port from `frontend/web_app/e2e/`:
- `supplier-smoke.spec.ts` — registration multi-step, retired route redirects
- `supplier-search.spec.ts` — supplier query URL redirect, storefront suggestions
- `supplier-product-upload-complete.spec.ts` — image upload, AI auto-fill, background removal, variants
- `supplier-kyc-form.spec.ts` — KYC checklist, toggle requirements, change KYC level
- `supplier-bulk-upload.spec.ts` — AI assist, manual upload, JSON import, draft duplication
- `voice-to-catalog.spec.ts` — voice pipeline, mic denial, batch limits

Write new:
- `supplier-orders-payouts.spec.ts` — orders list, parcel sheet, payouts, support tickets

### `modules/logistics/`

Port from `frontend/web_app/e2e/`:
- `shipping-quote-checkout.spec.ts` — logistics partner pricing end-to-end
- `logistics-country-switching.spec.ts` — country switching updates discovery segregation
- `fulfillment-role-flow.spec.ts` — supplier → logistics → customer → admin aligned
- `parcel-verification.spec.ts` — parcel proof upload + AI verification

Write new:
- `logistics-dashboard.spec.ts` — active shipments, scan page, status updates

### `cross-cutting/`

Port from `frontend/web_app/e2e/` (16 files):
- `panel-slider-audit.spec.ts`
- `mobile-panel-audit.spec.ts`
- `verify-all-panels.spec.ts`
- `products-visual-shell.spec.ts`
- `design-system-tokens.spec.ts`
- `design-system-comprehensive.spec.ts`
- `collapse-poll.spec.ts`
- `bg-comparison-visual.spec.ts`
- `chatbot-shopping-assistant.spec.ts`
- `command-center.spec.ts`
- `amendment-verify.spec.ts`
- `country-research-all-modules.spec.ts`
- `country-integration-rls.spec.ts`
- `country-auto-populate.spec.ts`
- `countries-search.spec.ts`
- `scaling_audit.spec.ts`

---

## 6 · Helper Files (must be completed before porting)

### `src/auth.ts`

Ported from `frontend/web_app/e2e/helpers/auth.ts`:
- `bootstrapAdminSessionViaApi(page)`
- `bootstrapSupplierSession(page)`
- `bootstrapLogisticsSession(page)`
- `bootstrapCustomerSession(page)`
- `bootstrapEmployeeSession(page)`
- `submitCredentialForm(page, username, password)`
- `waitForSessionFlag(page, timeoutMs?)`
- `openProtectedRoute(page, path, expectedUrl, timeoutMs?)`
- `ensurePanelSession(page, opts)`
- `expectNavigation(page, expectedUrl, timeoutMs?)`

### `src/api.ts`

Ported from `frontend/web_app/e2e/helpers/api.ts`:
- `API_BASE` / `WEB_BASE` from env (`API_BASE_URL` defaults to `http://127.0.0.1:8000`, `WEB_BASE_URL` defaults to `http://127.0.0.1:3100`)
- `apiGet<T>`, `apiPost<T>`, `apiPatch<T>`, `apiDelete<T>`
- `uniqueEmail(role)`, `uniqueUsername(role)`
- `registerUser(page, opts)`, `loginUser(page, email, password?)`, `verifyUser(page, token)`
- Response types: `ApiResponse<T>`, `RegisterResponse`, `LoginResponse`, `MeResponse`

### `src/ui.ts`

Write:
- `waitForPageLoad(page)`
- `glassPanel(locator)` — asserts `backdrop-filter: blur()`
- `sidebarShell(page)` — returns `aside.theme-sidebar-shell`
- `mobileDrawer(page)` — returns mobile drawer element
- `themeToggle(page)` — returns theme toggle button
- `countrySelector(page)` — returns country dropdown
- `collectOverflowReport(page)` — returns `{ viewportWidth, scrollWidth, offendingElements }`

### `playwright.config.ts`

Current config is minimal. Must include:
```typescript
reporter: [
  ["html", { outputFolder: "reports/html", open: "never" }],
  ["json", { outputFile: "reports/run/results.json" }],
  ["junit", { outputFile: "reports/run/junit.xml" }],
  ["list"],
],
outputDir: "test-results/",
globalTeardown: "./global-teardown.ts",
```

### `scripts/run-pipeline.ps1`

Current script runs `npx playwright test`. Must:
1. Verify `config/stack.env.ps1` exists
2. Source `config/stack.env.ps1`
3. Run `npx playwright test` from `_browser_test/`
4. Copy `reports/run/results.json` to `reports/run/last-run.json`
5. Exit with Playwright's exit code

---

## 7 · Acceptance Criteria

The browser test suite is **functional** when:

1. All 54 spec files from `frontend/web_app/e2e/` are ported to `_browser_test/tests/`
2. All new spec files (preflight, database, employee, security) are written and passing
3. All helper files (`auth.ts`, `api.ts`, `ui.ts`, `global-setup.ts`) are fully implemented
4. `playwright.config.ts` includes reporter config, output paths, and env-var-driven URLs
5. `scripts/run-pipeline.ps1` runs the full suite end-to-end without manual intervention
6. Preflight tests pass — backend health, Valkey, Postgres, frontend, `/rbac/catalog`
7. Database tests pass — seed data present, schemas correct, constraints enforced
8. Auth tests pass for all 5 modules with both API bootstrap and UI form login
9. Customer core flow passes — browse → cart → checkout → tracking
10. Supplier smoke passes — registration multi-step, retired route redirects
11. Logistics fulfillment passes — parcel sheet → scan → delivery → admin confirmation
12. Security tests pass — RBAC 403, CSRF, XSS sanitization, rate limit 429, RLS isolation
13. Design system tests pass — CSS tokens, glass panels, theme switching
14. Zero `page.route()` failures due to missing mock endpoints
15. All screenshots and traces on failure written to `_browser_test/reports/`

---

## 8 · Troubleshooting

| Symptom | Fix |
|---|---|
| `APP_ENV=production` triggers `AUDIT_CHAIN_KEY` error | Set `APP_ENV=development` in `config/stack.env.ps1` |
| TypeScript build fails | Run `pnpm build` in `frontend/web_app`; fix errors or keep `typescript.ignoreBuildErrors: true` |
| Playwright browsers not found | Run `npx playwright install chromium` in `_browser_test/` |
| Backend `import main` fails | Check `backend/.env` has `POSTGRES_PASSWORD`; check Valkey is running |
| Frontend returns 502 | Run `pnpm dev --port 3100` in `frontend/web_app` |
| Alembic divergent heads | Run `alembic merge heads -m "merge heads"` then `alembic upgrade head` |
| `python-jose` CVE in audit | Removed from `requirements.txt`; use `PyJWT` (canonical per TECH_STACK) |
| `requests` sync HTTP in audit | Not used in production code (only in tests); audit finding is stale |
| Webhook fail-open in audit | Webhook verification returns 401 on exception (fail-closed per Law 37); audit finding is stale |

---

## 9 · Benchmark Compliance

| Benchmark Doc | Section | Browser Test Requirement |
|---|---|---|
| `ARCHITECTURE_STACK.md` | §2 — Three Orthogonal Axes | Tests verify module router prefixes, domain data boundaries, feature gates |
| `ARCHITECTURE_STACK.md` | §3.1 — Frontend layout | Tests validate route groups per module, Zustand stores, `/rbac/catalog` fetch |
| `ARCHITECTURE_STACK.md` | §6 — Backend circuit | Tests verify middleware layers via 401/403/429 responses |
| `ARCHITECTURE_STACK.md` | §7 — RBAC / Feature axis | Tests verify `/rbac/catalog` gating, 403 on unauthorized features |
| `ARCHITECTURE_STACK.md` | §8 — Schema discipline | Database tests verify 15 schemas, no forbidden schemas |
| `ARCHITECTURE_STACK.md` | §10 — Security architecture | Security tests verify JWT type claim, CSRF, headers, rate limit fails-closed |
| `ARCHITECTURE_STACK.md` | §10.1 — Payment orchestration | Finance tests verify `/api/v1/finance/checkout/options`, webhook ingress |
| `TECHNOLOGY_STACK.md` | §12 — Frontend framework | Tests run against Next.js 16.3.5, React 19.2.8, TypeScript 5.9.3 |
| `TECHNOLOGY_STACK.md` | §15 — Frontend testing | Playwright 1.62.1+, Jest 29.7.0, React Testing Library 16.3.0 |
| `TECHNOLOGY_STACK.md` | §5 — Auth/Crypto | Tests verify PyJWT HS256, bcrypt 5.0.0, pyotp 2.10.0, AES-256-GCM field encryption |
| `TECHNOLOGY_STACK.md` | §3 — Cache/Sessions | Tests verify Valkey sessions, rate-limit counters, WebSocket fan-out |
| `TECHNOLOGY_STACK.md` | §9 — Observability | Tests verify structlog JSON, Prometheus `/metrics`, GlitchTip DSN configured |
