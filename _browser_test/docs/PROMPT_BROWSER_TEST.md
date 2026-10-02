# Browser Test Prompt — ZOZI E-Commerce Platform

> **Benchmark authority.** This prompt is governed by `_most_imp_docx/ARCHITECTURE_STACK.md` (structure, modules, domains, laws 1–325) and `_most_imp_docx/TECHNOLOGY_STACK.md` (versions, SDKs, infra). Any browser-test implementation must respect the module/domain/feature axes, the 5-module / 15-domain layout, and the RBAC permission model defined there.

---

## 1 · Objective

Port, complete, and make fully functional the ZOZI Playwright E2E browser test suite under `_browser_test/tests/`. The source-of-truth spec files already exist in `frontend/web_app/e2e/` (54 spec files). None have been migrated to `_browser_test/tests/` yet. This prompt defines exactly what must be built, fixed, and verified.

---

## 2 · Current State (2026-10-02)

| Component | Status |
|---|---|
| `_browser_test/` skeleton | Created — config, docs, scripts, src helpers |
| `_browser_test/tests/**/*.spec.ts` | **64 spec files present** — rearranged to match benchmark module layout |
| `_browser_test/tests/` | **8 top-level items** — `preflight.spec.ts`, `database.spec.ts`, `fixtures.ts`, `auth/`, `modules/`, `cross-cutting/` |
| `frontend/web_app/e2e/**/*.spec.ts` | **52 spec files exist** — source of truth |
| `frontend/web_app/e2e/helpers/auth.ts` | Complete — bootstrapAdminSessionViaApi, bootstrapSupplierSession, bootstrapLogisticsSession, bootstrapCustomerSession |
| `frontend/web_app/e2e/helpers/api.ts` | Complete — apiPost, apiGet, apiPatch, apiDelete, registerUser, loginUser |
| `_browser_test/playwright.config.ts` | Complete — baseURL, workers, timeout, reporters, trace/video/screenshot config |
| `_browser_test/scripts/run-pipeline.ps1` | Created — sources `config/stack.env.ps1`, runs `npx playwright test` |
| `_browser_test/src/auth.ts` | Complete — 159 lines, all bootstrap helpers, form helpers, panel session |
| `_browser_test/src/api.ts` | Complete — 355 lines, all CRUD helpers, loud wrappers, domain helpers, response types |
| `_browser_test/src/ui.ts` | Complete — 65 lines, ZOZI selectors, overflow audit |
| `_browser_test/global-setup.ts` | Exists |
| `_browser_test/global-teardown.ts` | Exists |
| `config/stack.env.ps1` | Exists |
| Frontend build | **Passes** — 151/151 static pages generated |
| Backend boot | **Passes** — `import main` succeeds with non-fatal warnings |

### What is broken / missing

1. **6 spec files are stubs** — `auth-session-refresh.spec.ts`, `auth-rbac-gates.spec.ts`, `customer-cart.spec.ts`, `customer-wishlist.spec.ts`, `supplier-orders-payouts.spec.ts`, `logistics-dashboard.spec.ts` contain only placeholder comments.
2. **~40 ported spec files** need import updates — replace `frontend/web_app/e2e/helpers/` imports with `_browser_test/src/`.
3. **`_browser_test/src/monitor.ts`** and **`_browser_test/src/workflows.ts`** exist but are not referenced in PROMPT_BROWSER_TEST.md; verify if needed.
4. **Browser dependencies not installed** — `playwright install` must be run before first execution.
5. **Frontend `next.config.ts` has `typescript.ignoreBuildErrors: true`** — type errors in e2e imports or test utilities may be masked; must be validated when running tests.

---

## 3 · Architecture Constraints (from benchmark docs)

### 3.1 Module / Domain / Feature Axes

The browser tests must exercise endpoints and UI flows that respect the three orthogonal axes:

| Axis | Definition | Test implication |
|---|---|---|
| **Module** (who) | customer, supplier, logistics, admin, employee | Each test targets a specific module's router prefix and auth flow |
| **Domain** (what) | accounts, analytics, audit, catalog, comms, country, customers, finance, governance, hr, logistics, orders, promotions, security, suppliers | Tests validate domain-specific data and business rules |
| **Feature** (may) | `finance.ledger.post`, `catalog.product.create`, etc. from `domains/*/features.py` | UI gating and API gating share `/rbac/catalog`; tests must verify unauthorized access returns 403 |

### 3.2 Middleware Pipeline (Law 78)

All backend requests traverse 8 middleware layers before reaching a module router:

```
Foundation → Auth/Zero-Trust → Rate Limit → Webhook Verification → Geo/Country → Security → Observability → Compliance
```

Tests must verify:
- Unauthenticated requests to protected routes return 401.
- Requests with expired/invalid JWTs return 401.
- Rate-limited requests return 429 after threshold.
- Country context (`x-country-code` header) is set on every request.

### 3.3 Frontend Layout (ARCHITECTURE_STACK.md §3.1)

```
frontend/web_app/
├── src/app/          # route tree per module: (customer), auth/, admin/*, supplier/*, logistics-partner/*, employee/*
├── src/components/   # ui/ (design system), admin/, auth/, chat/, comms/, country/, map/, supplier/
├── src/hooks/        # useApi, useAuth, WebSocket hooks
├── src/lib/          # api/ (client.ts, auth.ts, country.ts, errors.ts), rbac.ts
├── src/services/     # localizationService, crossBorderService, addressFormatService
└── shared/           # cross-platform TS: api-core.ts, money.ts, permissions.ts (GENERATED from /rbac/catalog)
```

Tests must validate:
- Route guards redirect unauthenticated users to the correct module login page.
- `/rbac/catalog` is fetched on boot and `permissions.ts` gates UI elements.
- Zustand stores (`cart`, `currency`, `wishlist`) persist across navigations within a session.

### 3.4 Security Architecture (ARCHITECTURE_STACK.md §10)

| Law | Rule | Test requirement |
|---|---|---|
| Law 33 | Token type verification | Access tokens only; refresh tokens rejected by API and WebSocket endpoints |
| Law 35 | CSRF active | State-changing POST/PATCH/DELETE require CSRF token or same-origin enforcement |
| Law 36 | Security headers | CSP, HSTS, X-Frame-Options, X-Content-Type-Options present in production responses |
| Law 37 | Rate limit fails closed | Valkey down → deny, not allow-all |
| Law 40 | Backend CORS disabled for browsers | CORS only allowed for Next.js API proxy origin; native mobile bypasses CORS |
| Law 42 | Input validation | All public endpoints use Pydantic schemas; no raw dicts in router signatures |
| Law 43 | Security event logging | Auth failures, 403s, rate-limit triggers logged at WARNING+ |

---

## 4 · Test Scope & Categories

The `_browser_test/tests/` directory uses 5 top-level items (2 root spec files + 3 folders). Each folder maps to existing `frontend/web_app/e2e/` spec files. The table below defines what must be ported, what must be written from scratch, and what must be fixed.

| Category | Path | Source spec files | Action required |
|---|---|---|---|
| Preflight | `tests/preflight.spec.ts` | None | **Write new** — env readiness, server health, DB connectivity |
| Database | `tests/database.spec.ts` | None | **Write new** — migration correctness, seed data, constraints, RLS |
| Auth | `tests/auth/` | `auth-role-login.spec.ts`, `auth-registration-login.spec.ts` | **Port** — login, logout, session, token refresh, CSRF, 401/403 |
| Modules — Admin | `tests/modules/admin/` | 14 admin spec files | **Port** — all admin modules, finance lifecycle, treasury, payment gateways |
| Modules — Customer | `tests/modules/customer/` | `customer-core-flow.spec.ts`, `cross-border-checkout.spec.ts` | **Port** — browse, cart, checkout, tracking, tax preview |
| Modules — Supplier | `tests/modules/supplier/` | 6 supplier spec files | **Port** — registration, product upload, KYC, bulk, voice-to-catalog |
| Modules — Logistics | `tests/modules/logistics/` | 4 logistics spec files | **Port** — pricing, country switching, scan/delivery, COD proof |
| Modules — Employee | `tests/modules/employee/` | None | **Write new** — HR dashboard, onboarding, disciplinary, HSE, alumni |
| Cross-cutting | `tests/cross-cutting/` | 16 cross-cutting spec files | **Port** — panel collapse, mobile overflow, design tokens, visual shell, WebSocket, scaling |

---

## 5 · Detailed Prompts per Category

### 5.1 `_browser_test/tests/preflight.spec.ts`

**Purpose:** Verify environment readiness before any functional test runs. This runs first in the pipeline.

**What to build:**

1. `preflight.spec.ts` — single spec file with the following tests:
   - `test("Playwright browsers are installed")` — asserts `chromium` is available via `chromium.launch()`.
   - `test("Backend health endpoint returns 200")` — `GET http://127.0.0.1:8000/health` returns `{ status: "healthy" }`.
   - `test("Backend /health/deps reports Valkey and DB as connected")` — `GET http://127.0.0.1:8000/health/deps` returns `{ valkey: "connected", postgres: "connected" }`.
   - `test("Frontend is serving on configured port")` — `GET http://127.0.0.1:3100` returns 200 with `text/html`.
   - `test("Rbac catalog endpoint is reachable")` — `GET http://127.0.0.1:8000/rbac/catalog` returns 200 with feature array.
   - `test("Database responds to a simple query")` — backend `GET /health` includes `database: "connected"`.
   - `test("Valkey is reachable")` — backend `GET /health/deps` includes `valkey: "connected"`.

**Failure behavior:** If any preflight test fails, the pipeline must halt and report the exact service that is down. Do not attempt to run functional tests.

---

### 5.2 `_browser_test/tests/auth/`

**Purpose:** Cover login, logout, session management, and token refresh flows for all 5 modules.

**Source files:** `frontend/web_app/e2e/auth-role-login.spec.ts`, `frontend/web_app/e2e/auth-registration-login.spec.ts`, `frontend/web_app/e2e/helpers/auth.ts`

**What to build:**

1. `auth-role-login.spec.ts` — port from `frontend/web_app/e2e/auth-role-login.spec.ts`:
   - `test("admin login via UI")` — navigate to `/admin/login`, fill form, assert redirect to `/admin/dashboard`.
   - `test("customer login via UI")` — navigate to `/login`, fill form, assert redirect to `/`.
   - `test("supplier login via UI")` — navigate to `/supplier/login`, fill form, assert redirect to `/supplier/dashboard`.
   - `test("logistics partner login via UI")` — navigate to `/logistics-partner/login`, fill form, assert redirect to `/logistics-partner/dashboard`.
   - `test("employee login via UI")` — navigate to `/employee/login`, fill form, assert redirect to `/employee/dashboard`.
   - `test("token type is access — refresh token rejected by API")` — send refresh token to `/api/v1/auth/login` (access-only endpoint), assert 401.

2. `auth-registration-login.spec.ts` — port from `frontend/web_app/e2e/auth-registration-login.spec.ts`:
   - `test("customer registration page renders form")` — navigate to `/register`, assert password input, email input, submit button visible.
   - `test("supplier registration page loads")` — navigate to `/supplier/register`, assert form fields visible.
   - `test("logistics-partner registration page loads")` — navigate to `/logistics-partner/register`, assert form fields visible.
   - `test("admin registration is blocked for non-super-admin")` — attempt to register admin via API, assert 403.

3. `auth-session-refresh.spec.ts` — **write new**:
   - `test("access token expires — silent refresh via httpOnly cookie succeeds")` — expire access token, call protected endpoint, assert no 401 (silent refresh via `zozi_refresh` cookie).
   - `test("refresh token rotation — old token invalidated after refresh")` — use refresh token to get new access, assert old refresh token returns 401.
   - `test("device binding — session invalidated on new device")` — bootstrap session, change device fingerprint, assert 401 on subsequent request.
   - `test("logout clears session state")` — bootstrap session, call `/api/v1/auth/logout`, assert `zozi_refresh` cookie deleted, localStorage flag cleared.

4. `auth-rbac-gates.spec.ts` — **write new**:
   - `test("unauthorized feature access returns 403")` — login as customer, call `POST /admin/finance/ledger`, assert 403.
   - `test("authorized feature access returns 200")` — login as admin, call `POST /admin/finance/ledger`, assert 200.
   - `test("cross-tenant data isolation — country A cannot see country B data")` — login as AE admin, call `GET /orders?country=SA`, assert empty or 403.

**Required helpers in `_browser_test/src/auth.ts`:**
```typescript
// Port from frontend/web_app/e2e/helpers/auth.ts:
export async function bootstrapAdminSessionViaApi(page: Page): Promise<boolean>;
export async function bootstrapSupplierSession(page: Page): Promise<boolean>;
export async function bootstrapLogisticsSession(page: Page): Promise<boolean>;
export async function bootstrapCustomerSession(page: Page): Promise<boolean>;
export async function bootstrapEmployeeSession(page: Page): Promise<boolean>;
export async function submitCredentialForm(page: Page, username: string, password: string): Promise<void>;
export async function waitForSessionFlag(page: Page, timeoutMs?: number): Promise<void>;
export async function openProtectedRoute(page: Page, path: string, expectedUrl: RegExp, timeoutMs?: number): Promise<void>;
export async function ensurePanelSession(page: Page, opts: { user: string; pass: string; loginPath: string; landing: string; landingRegex: RegExp }): Promise<void>;
export async function expectNavigation(page: Page, expectedUrl: RegExp, timeoutMs?: number): Promise<void>;
```

---

### 5.3 `_browser_test/tests/modules/customer/`

**Purpose:** End-to-end flows for customer-facing features: browse, product detail, cart, checkout, order tracking, cross-border tax.

**Source files:** `frontend/web_app/e2e/customer-core-flow.spec.ts`, `frontend/web_app/e2e/cross-border-checkout.spec.ts`, `frontend/web_app/e2e/country-auto-populate.spec.ts`

**What to build:**

1. `customer-core-flow.spec.ts` — port from `frontend/web_app/e2e/customer-core-flow.spec.ts`:
   - `test("product page to order tracking flow")` — browse → product detail → add to cart → checkout → order tracking.
   - Assertions: `/products` shows results count, product detail shows name heading, cart shows "Cart" heading, checkout shows delivery form, order redirects to `/orders/{id}`, tracking shows `tracking-live-status`.

2. `cross-border-checkout.spec.ts` — port from `frontend/web_app/e2e/cross-border-checkout.spec.ts`:
   - `test("customer can view tax preview for different countries")` — admin configures tax rules, customer previews VAT.
   - `test("can configure multiple payment gateways for cross-border")` — admin adds gateway, customer sees it in checkout.
   - `test("can configure logistics providers for delivery")` — admin adds partner, customer sees shipping options.

3. `customer-search.spec.ts` — port from `frontend/web_app/e2e/search-bar-header.spec.ts` (customer subset):
   - `test("category selection filters products")` — select category, assert `category=` in request URL.
   - `test("price filter min_price param is passed")` — assert `min_price=` in request URL.
   - `test("rating filter min_rating param is passed")` — assert `min_rating=` in request URL.
   - `test("voice search mic button is visible")` — assert `button[title='Voice search']` visible.
   - `test("image search camera button is visible and enabled")` — assert `button[title='Search by image']` visible and enabled.

4. `customer-cart.spec.ts` — **write new**:
   - `test("cart persists across page reloads")` — add item, reload, assert item still in cart.
   - `test("cart total updates with quantity change")` — increment quantity, assert total recalculates.
   - `test("empty cart shows checkout CTA")` — clear cart, assert "Proceed to Checkout" not visible, "Continue Shopping" visible.
   - `test("cross-border tax shown in cart for AE destination")` — set country AE, add item, assert tax line visible.

5. `customer-wishlist.spec.ts` — **write new**:
   - `test("add to wishlist from product page")` — click wishlist button, assert item in wishlist store.
   - `test("wishlist persists across sessions")` — add item, reload, assert item still in wishlist.

**Required helpers in `_browser_test/src/api.ts`:**
```typescript
export const API_BASE: string; // from env API_BASE_URL or http://127.0.0.1:8000
export const WEB_BASE: string; // from env WEB_BASE_URL or http://127.0.0.1:3100
export async function apiGet<T>(page: Page, path: string, opts?: { headers?: Record<string,string>; timeout?: number }): Promise<ApiResponse<T>>;
export async function apiPost<T>(page: Page, path: string, data?: unknown, opts?: ...): Promise<ApiResponse<T>>;
export async function apiPatch<T>(...): Promise<ApiResponse<T>>;
export async function apiDelete<T>(...): Promise<ApiResponse<T>>;
export function uniqueEmail(role: string): string;
export function uniqueUsername(role: string): string;
export async function registerUser(page: Page, opts: { email, username, password, role, business_name?, phone? }): Promise<ApiResponse<RegisterResponse>>;
export async function loginUser(page: Page, email: string, password?: string): Promise<ApiResponse<LoginResponse>>;
export async function verifyUser(page: Page, token: string): Promise<ApiResponse<MeResponse>>;
```

---

### 5.4 `_browser_test/tests/modules/supplier/`

**Purpose:** Cover supplier onboarding, catalog management, order fulfillment, payout flows.

**Source files:** `frontend/web_app/e2e/supplier-smoke.spec.ts`, `supplier-search.spec.ts`, `supplier-product-upload-complete.spec.ts`, `supplier-kyc-form.spec.ts`, `supplier-bulk-upload.spec.ts`, `voice-to-catalog.spec.ts`

**What to build:**

1. `supplier-smoke.spec.ts` — port from `frontend/web_app/e2e/supplier-smoke.spec.ts`:
   - `test("supplier register completes the multi-step flow")` — fill 3-step registration, assert redirect to `/supplier/login?registered=1`.
   - `test("retired supplier routes land on merged workspaces")` — verify redirects:
     - `/supplier/invoices` → `/supplier/payouts?view=invoices`
     - `/supplier/disputes` → `/supplier/support?section=disputes`
     - `/supplier/returns` → `/supplier/orders?section=returns`
     - `/supplier/logistics` → `/supplier/orders`
     - `/supplier/documents` → `/supplier/profile?tab=documents`
     - `/supplier/guide` → `/supplier/profile?tab=guide`
   - `test("merged supplier profile action strip stays accessible on narrow screens")` — viewport 390x844, assert all 9 tab buttons visible.

2. `supplier-search.spec.ts` — port from `frontend/web_app/e2e/supplier-search.spec.ts`:
   - `test("redirects a direct supplier query URL to the storefront")` — `/products?supplier=Dream Mart` → `/supplier=dream-mart`.
   - `test("opens the supplier storefront from suggestions")` — type "Dream Mart", click suggestion, assert heading "Dream Mart".

3. `supplier-product-upload.spec.ts` — port from `frontend/web_app/e2e/supplier-product-upload-complete.spec.ts`:
   - `test("Upload image → canvas renders → AI auto-fills")` — upload image, assert canvas, AI analyze button.
   - `test("AI mock fill + background removal")` — mock `/supplier/upload/ai-analyze`, assert name auto-filled.
   - `test("Image processing tools + canvas controls")` — mock `/supplier/upload/process-tools`, test magic erase, smart crop, auto light, W/B/T, denoise, sharpen.
   - `test("Complete product submission with variants")` — fill form, enable variants, click Publish Product.
   - `test("Multiple image formats accepted")` — JPEG, WebP, JPEG-alt.
   - `test("Fast bg quality toggle and remove image")` — toggle fast/quality, remove, assert "Choose Photo" visible.

4. `supplier-kyc.spec.ts` — port from `frontend/web_app/e2e/supplier-kyc-form.spec.ts`:
   - `test("supplier KYC tab loads with document checklist")` — admin views KYC tab, asserts document checklist.
   - `test("can toggle document requirements")` — toggle Commercial Registration, VAT Certificate.
   - `test("can change KYC level")` — select "enhanced", save draft.

5. `supplier-bulk-upload.spec.ts` — port from `frontend/web_app/e2e/supplier-bulk-upload.spec.ts`:
   - `test("AI assist normalizes workspace image into draft card")` — upload, click "Use AI from Photo", assert draft populated.
   - `test("manual upload uses currency-aware payloads and variant table rows")` — fill advanced form, assert payload shape.
   - `test("JSON import and draft duplication")` — import JSON, duplicate draft, upload 2 products.
   - `test("invalid fashion upload focuses first blocking field")` — select Fashion, upload without material, assert error focus.

6. `supplier-voice-to-catalog.spec.ts` — port from `frontend/web_app/e2e/voice-to-catalog.spec.ts`:
   - `test("complete pipeline finishes in under 30 seconds")` — upload, trigger voice, assert "Pipeline Complete" < 30s.
   - `test("pipeline handles microphone denial gracefully")` — deny mic, assert "Pipeline Failed" or graceful fallback.
   - `test("batch upload limits returned correctly")` — call `GET /supplier/products/batch-limits`, assert `max_batch_size >= 10`.

7. `supplier-orders-payouts.spec.ts` — **write new**:
   - `test("supplier orders list shows pending and fulfilled orders")` — navigate to `/supplier/orders`, assert order rows visible.
   - `test("supplier can print parcel sheet")` — click "Print Packing Sheet", assert print dialog or PDF download.
   - `test("supplier payouts tab shows balance and transaction history")` — navigate to `/supplier/payouts`, assert balance, transactions.
   - `test("supplier support tickets list and create")` — navigate to `/supplier/support`, create ticket, assert visible.

---

### 5.5 `_browser_test/tests/modules/logistics/`

**Purpose:** Cover delivery partner management, shipment tracking, route optimization, manifest generation.

**Source files:** `frontend/web_app/e2e/shipping-quote-checkout.spec.ts`, `logistics-country-switching.spec.ts`, `fulfillment-role-flow.spec.ts`, `parcel-verification.spec.ts`

**What to build:**

1. `shipping-quote.spec.ts` — port from `frontend/web_app/e2e/shipping-quote-checkout.spec.ts`:
   - `test("logistics partner pricing verified end-to-end")` — supplier login, create partner service area, customer add to cart, `POST /cart/shipping-quote` for AE/Dubai, assert `shipping_amount > 0`, `source: "approved_logistics_partner"`.

2. `logistics-country-switching.spec.ts` — port from `frontend/web_app/e2e/logistics-country-switching.spec.ts`:
   - `test("manual country switching updates logistics discovery segregation and x-country-code header")` — create PK and OM partners, switch to PK, assert PK partner visible, OM hidden, header `x-country-code: PK`.

3. `fulfillment-role-flow.spec.ts` — port from `frontend/web_app/e2e/fulfillment-role-flow.spec.ts`:
   - `test("supplier, partner, customer, and admin views stay aligned across one shipment")` — supplier creates parcel, partner scans, customer tracks, admin views shipment row.
   - `test("supplier parcel sheet flows into logistics scan and marks picked from supplier")` — two browser contexts, partner clicks "Picked From Supplier", supplier accepts confirmation.
   - `test("web scan delivery captures signature and marks order delivered")` — logistics clicks "Delivered", sends confirmation request with signature pad, customer accepts, admin asserts "delivered".

4. `parcel-verification.spec.ts` — port from `frontend/web_app/e2e/parcel-verification.spec.ts`:
   - `test("parcel proof upload + verification returns valid match_score > 0 and engines_used >= 2")` — supplier uploads photo, calls verify endpoint, asserts response shape.

5. `logistics-dashboard.spec.ts` — **write new**:
   - `test("logistics dashboard shows active shipments count")` — navigate to `/logistics-partner/dashboard`, assert stats row.
   - `test("logistics scan page loads with scanner input")` — navigate to `/logistics-partner/scan`, assert scan input visible.
   - `test("logistics can update shipment status to Distribution Checkpoint")` — scan code, click status, assert update.

---

### 5.6 `_browser_test/tests/modules/employee/`

**Purpose:** Cover employee workflows and admin security tests.

**Source files:** No direct employee e2e specs exist; security tests sourced from `frontend/web_app/e2e/verify-8-fixes.spec.ts` (security subset) and backend `tests/security/*.py`.

**What to build:** Write employee tests and security tests from scratch. Key tests:

1. `employee-login.spec.ts` — **write new**:
   - `test("employee login via UI")` — navigate to `/employee/login`, fill credentials, assert redirect to `/employee/dashboard`.
   - `test("employee login via API bootstrap")` — `bootstrapEmployeeSession`, assert `/api/v1/auth/me` returns employee role.

2. `employee-dashboard.spec.ts` — **write new**:
   - `test("employee dashboard shows assigned orders and support tickets")` — assert orders count, tickets count visible.

3. `employee-orders.spec.ts` — **write new**:
   - `test("employee can view order detail")` — navigate to `/employee/orders/{id}`, assert order info, customer details, shipment status.
   - `test("employee can add internal note to order")` — fill note, submit, assert note visible in timeline.

4. `employee-customers.spec.ts` — **write new**:
   - `test("employee can search customers by email or phone")` — search, assert results.
   - `test("employee can view customer order history")` — click customer, assert order list.

5. `employee-hr.spec.ts` — **write new**:
   - `test("employee can view onboarding pipeline")` — navigate to `/admin/employees?tab=onboarding`, assert pipeline stages.
   - `test("HSE tab renders without crashing")` — navigate to `/admin/employees?tab=hse`, assert "Health, Safety & Environment" heading.

---

### 5.7 `_browser_test/tests/modules/admin/` (admin specs)

**Purpose:** Cover administrative functions: user management, configuration, monitoring, billing, finance, commissions, countries, logistics, HR.

**Source files:** 14 spec files in `frontend/web_app/e2e/` (see §4 table)

**What to build:** Port all 14 admin spec files. Key tests:

| Spec file | Key tests |
|---|---|
| `admin-commission.spec.ts` | Overview tab, category rates add, badge tiers add |
| `admin-audit-fixes.spec.ts` | Audit logs chrome, command center WebSocket, promotions prefix |
| `admin-country-control-plane.spec.ts` | Ledger table, create country, 12-tab workspace, version history |
| `admin-country-enhanced.spec.ts` | Inline form, auto-populate, ledger columns, bulk commission, country selector |
| `admin-communication-hub.spec.ts` | Video rooms, email campaigns, chat threads |
| `admin-data-ops.spec.ts` | DB health, backup, restore, user export |
| `admin-logistics-workspace.spec.ts` | Logistics config, carriers, service areas |
| `admin-hr-permissions.spec.ts` | Employee management, permissions matrix |
| `admin-modules-reconciliation.spec.ts` | Module route inventory vs actual routes |
| `admin-payment-gateways.spec.ts` | Gateway attach, config, country assignment |
| `admin-supplier-logistics-sanity.spec.ts` | Supplier and logistics sanity checks |
| `admin-treasury-payout.spec.ts` | Treasury overview, payout sweep |
| `finance-e2e.spec.ts` | All 12 finance tabs: COA, FX, Deferred Revenue, Email-to-Ledger, Bank Mapping, AR/AP, Journal, Budgets, Audit Log |
| `finance-cod-proof-live.spec.ts` | Logistics COD proof upload, admin verify |

**Porting rules:**
- Use `_browser_test/src/auth.ts` `bootstrapAdminSessionViaApi` instead of importing from `frontend/web_app/e2e/helpers/auth.ts`.
- Use `_browser_test/src/api.ts` `apiGet`/`apiPost` instead of `page.route()` interceptors where possible; keep `page.route()` for complex mock payloads.
- Maintain all existing `test.describe` blocks and test names exactly for traceability.
- Take screenshots on failure (handled by `playwright.config.ts`).

---

### 5.8 `_browser_test/tests/modules/admin/` (security specs)

**Purpose:** Cover RBAC, input validation, XSS/CSRF protections, privilege escalation prevention, rate limiting, RLS.

**Source files:** `frontend/web_app/e2e/verify-8-fixes.spec.ts` (security subset), `backend/tests/security/*.py`

**What to build:**

1. `rbac-enforcement.spec.ts` — **write new**:
   - `test("customer cannot access admin routes")` — 403 on `GET /admin/finance`.
   - `test("supplier cannot access other supplier's data")` — cross-tenant 403 on `/supplier/orders?supplier_id=X` where X ≠ self.
   - `test("logistics cannot access admin finance")` — 403 on `/admin/finance`.
   - `test("feature gate blocks unassigned feature")` — role without `finance.ledger.post` gets 403.

2. `csrf-protection.spec.ts` — **write new**:
   - `test("POST without CSRF token returns 403 in production mode")` — set `APP_ENV=production`, send POST without CSRF header, assert 403.
   - `test("POST with valid CSRF token returns 200")` — fetch CSRF token, send with request, assert 200.

3. `xss-protection.spec.ts` — **write new**:
   - `test("user-generated content in product name is sanitized")` — create product with `<script>alert(1)</script>` in name, assert raw script not in DOM.
   - `test("CSP header blocks inline script execution")` — assert `Content-Security-Policy` header present.

4. `rate-limiting.spec.ts` — **write new**:
   - `test("15 rapid failed logins return 429")` — 15x `POST /api/v1/auth/login` with bad password, assert at least one 429.
   - `test("rate limit resets after window")` — wait 60s, assert login succeeds again.

5. `rls-cross-tenant.spec.ts` — **write new**:
   - `test("admin with country_code=AE cannot read SA supplier data via API")` — set `x-country-code: AE`, call `GET /suppliers?country=SA`, assert empty or 403.
   - `test("customer with country_code=AE sees only AE-priced products")` — browse products, assert prices in AED not OMR.

6. `input-validation.spec.ts` — **write new**:
   - `test("oversized password rejected with error")` — register with 100-char password, assert 422 or specific error.
   - `test("SQL injection in search param returns 422 or empty results")` — `GET /products?search='; DROP TABLE products; --`, assert no crash.
   - `test("XSS in checkout address field is sanitized")` — submit `<script>` in street field, assert sanitized in response.

---

### 5.9 `_browser_test/tests/cross-cutting/`

**Purpose:** Tests spanning multiple roles and requiring coordinated user actions.

**Source files:** 16 spec files in `frontend/web_app/e2e/` (see §4 table)

**What to build:** Port all 16 spec files. Key tests:

| Spec file | Key tests |
|---|---|
| `panel-slider-audit.spec.ts` | Admin/supplier/logistics mobile drawer + desktop sidebar collapse |
| `mobile-panel-audit.spec.ts` | iPhone 13 viewport overflow across 18 routes |
| `verify-all-panels.spec.ts` | No global header, sidebar collapses for all 3 roles |
| `products-visual-shell.spec.ts` | Background effects, glass cards, no opaque white shell |
| `design-system-tokens.spec.ts` | CSS custom properties wired correctly |
| `design-system-comprehensive.spec.ts` | Token wiring, glass system, z-index scale, theme switching |
| `collapse-poll.spec.ts` | Sidebar collapse does not trigger infinite re-render |
| `bg-comparison-visual.spec.ts` | Background removal visual quality |
| `chatbot-shopping-assistant.spec.ts` | Chatbot flow: intent → product suggestion → add to cart |
| `command-center.spec.ts` | WebSocket real-time telemetry, SYNC/INITIALISING states |
| `amendment-verify.spec.ts` | Order amendment request + admin verify flow |
| `country-research-all-modules.spec.ts` | Country AI research across all modules |
| `country-integration-rls.spec.ts` | Country RLS integration across domains |
| `country-auto-populate.spec.ts` | Auto-populate "Saudi Arabia" returns SA/SAR/Asia-Riyadh |
| `countries-search.spec.ts` | Countries search and selection |
| `scaling_audit.spec.ts` | API health, auth, product search, pagination, storage, Dockerfiles, Alembic |

---

### 5.10 `_browser_test/tests/database.spec.ts`

**Purpose:** Cover data integrity, migration correctness, seed data loading, constraint validation.

**Source files:** `backend/tests/system/test_database_alignment.py`, `backend/tests/architecture/test_schema_discipline.py`

**What to build:**

1. `migration-correctness.spec.ts` — **write new** (Playwright cannot run Alembic directly; use API/backend tests):
   - `test("Alembic heads are linear — no divergent branches")` — call backend endpoint or read `alembic/versions/` via API, assert single head.
   - `test("all 15 domain schemas exist in database")` — query `information_schema.schemata`, assert all 15 canonical schemas present.
   - `test("no tables exist in forbidden schemas (core, platform, identity)")` — assert zero tables in those schemas.

2. `seed-data.spec.ts` — **write new**:
   - `test("seed countries are loaded")` — `GET /countries`, assert AE, SA, OM, BH, KW, QA present.
   - `test("seed admin user exists and can authenticate")` — `POST /api/v1/auth/login` with `admin@zozi.com` / `E2eAdmin#2026`, assert 200 + tokens.
   - `test("seed products have variants and stock")` — `GET /products?limit=50`, assert at least one product with `variants` array and `stock > 0`.

3. `constraint-validation.spec.ts` — **write new**:
   - `test("foreign key constraints prevent orphan order_lines")` — delete product with order_lines, assert FK prevents or cascades per `ondelete`.
   - `test("unique constraints prevent duplicate emails")` — register same email twice, assert second returns 409.
   - `test("check constraints enforce valid enum values")` — insert invalid `status` into orders, assert 422.

4. `rls-enforcement.spec.ts` — **write new**:
   - `test("country_code session context is set on every query")` — login as AE admin, call `GET /orders`, assert `app.country_code = 'AE'` in DB session (via audit log or explain).
   - `test("RLS blocks cross-country reads")` — login as AE admin, attempt `GET /orders?country=SA`, assert empty or 403.

---

## 6 · Shared Test Infrastructure Requirements

### 6.1 `_browser_test/src/auth.ts` — Complete Implementation

Must be a full port of `frontend/web_app/e2e/helpers/auth.ts` with the following additions:
- `API_BASE` / `WEB_BASE` URL resolution from `process.env`.
- Session bootstrap functions for all 5 modules: `bootstrapAdminSessionViaApi`, `bootstrapSupplierSession`, `bootstrapLogisticsSession`, `bootstrapCustomerSession`, `bootstrapEmployeeSession`.
- `submitCredentialForm` — fills any login form generically.
- `waitForSessionFlag` — waits for `zozi_has_session=1` in localStorage or `zozi_refresh` cookie.
- `openProtectedRoute` — navigates and waits for expected URL pattern.
- `ensurePanelSession` — tries API bootstrap first, falls back to UI form.
- `expectNavigation` — polls `page.url()` until regex matches or timeout.

### 6.2 `_browser_test/src/api.ts` — Complete Implementation

Must be a full port of `frontend/web_app/e2e/helpers/api.ts` plus:
- Env-var-driven `API_BASE` (`API_BASE_URL` or `http://127.0.0.1:8000`) and `WEB_BASE` (`WEB_BASE_URL` or `http://127.0.0.1:3100`).
- Type-safe response wrappers: `ApiResponse<T>`, `RegisterResponse`, `LoginResponse`, `MeResponse`.
- Domain helpers: `uniqueEmail(role)`, `uniqueUsername(role)`.
- All CRUD helpers: `apiPost`, `apiGet`, `apiPatch`, `apiDelete`.

### 6.3 `_browser_test/src/ui.ts` — Complete Implementation

Must include:
- `waitForPageLoad(page)` — existing.
- ZOZI-specific selectors:
  - `glassPanel(locator)` — asserts `backdrop-filter: blur()`.
  - `sidebarShell(page)` — returns `aside.theme-sidebar-shell`.
  - `mobileDrawer(page)` — returns mobile drawer element.
  - `themeToggle(page)` — returns theme toggle button.
  - `countrySelector(page)` — returns country dropdown.
- Overflow detection utility:
  - `collectOverflowReport(page)` — returns `{ viewportWidth, scrollWidth, offendingElements }`.

### 6.4 `_browser_test/global-setup.ts` — Complete Implementation

Must perform lightweight verification (no server startup — servers managed externally):
```typescript
export default async (): Promise<void> => {
  const apiBase = process.env.API_BASE_URL || "http://127.0.0.1:8000";
  const webBase = process.env.WEB_BASE_URL || "http://127.0.0.1:3100";

  // Verify backend is reachable
  const health = await fetch(`${apiBase}/health`);
  if (!health.ok) {
    console.error(`[global-setup] Backend health check failed: ${health.status}`);
    process.exit(1);
  }

  // Verify frontend is reachable
  const frontend = await fetch(webBase);
  if (!frontend.ok) {
    console.error(`[global-setup] Frontend health check failed: ${frontend.status}`);
    process.exit(1);
  }

  console.log(`[global-setup] Preflight OK — backend=${apiBase}, frontend=${webBase}`);
};
```

### 6.5 `_browser_test/playwright.config.ts` — Complete Configuration

Must extend the existing minimal config with:
```typescript
export default defineConfig({
  testDir: "./tests",
  testMatch: ["**/*.spec.ts"],
  fullyParallel: false,
  workers: parseInt(process.env.PW_WORKERS || "1"),
  timeout: parseInt(process.env.PW_TIMEOUT || "30000"),
  globalSetup: "./global-setup.ts",
  globalTeardown: "./global-teardown.ts",   // write new
  use: {
    baseURL: process.env.WEB_BASE_URL || "http://127.0.0.1:3100",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  reporter: [
    ["html", { outputFolder: "reports/html", open: "never" }],
    ["json", { outputFile: "reports/run/results.json" }],
    ["junit", { outputFile: "reports/run/junit.xml" }],
    ["list"],
  ],
  outputDir: "test-results/",
});
```

### 6.6 `_browser_test/scripts/run-pipeline.ps1` — Update

Current script just runs `npx playwright test`. Must be updated to:
1. Verify `config/stack.env.ps1` exists (already does).
2. Source `config/stack.env.ps1`.
3. Run `npx playwright test --config=../playwright.config.ts` from `_browser_test/`.
4. After test run, copy `reports/run/results.json` to `reports/run/last-run.json` for CI consumption.
5. Exit with Playwright's exit code (non-zero on failure).

---

## 7 · Environment Setup Checklist

Before running the pipeline, the following must be verified:

| Step | Command / Action | Status |
|---|---|---|
| 1. Install Playwright browsers | `npx playwright install chromium` | Must be done once |
| 2. Copy env file | `copy config\stack.env.ps1.example config\stack.env.ps1` | **Pending** — `.ps1` file not created |
| 3. Configure secrets in `config/stack.env.ps1` | Replace `replace-me-*` with real values | **Pending** |
| 4. Start backend | `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000` | Backend boots with `import main` |
| 5. Start frontend | `cd frontend/web_app && npx next dev --port 3100` | Frontend builds (151 pages) |
| 6. Verify Valkey running | `redis-cli ping` → `PONG` (Valkey is Redis-compatible) | Non-fatal warnings present |
| 7. Verify Postgres running | `psql $DATABASE_URL -c "SELECT 1"` | Non-fatal warnings present |
| 8. Run pipeline | `.\scripts\run-pipeline.ps1` | **Pending** — no specs exist |

---

## 8 · Known Issues & Blockers

| Issue | Severity | Mitigation |
|---|---|---|
| `APP_ENV=production` in root `.env` triggers `AUDIT_CHAIN_KEY` validation error | **Blocker** | Set `APP_ENV=development` for local testing |
| TypeScript build errors suppressed via `typescript.ignoreBuildErrors: true` | Medium | Fix pre-existing type issues in `frontend/web_app/src/` |
| Divergent Alembic heads (14 heads, 2 duplicate revision IDs) | High | Fix before production; does not block local testing |
| `python-jose` CVEs (replaced by `PyJWT` per TECH_STACK but still in lockfile) | High | Update `uv.lock` |
| 5 webhook fail-open handlers (allow on exception) | High | Fix to fail-closed per Law 37 |
| `requests` sync HTTP used in 8 backend files (forbidden, must use `httpx`) | Medium | Migrate to `httpx` |
| `Limiter` import from `fastapi_limiter_valkey` missing | Low | Add import or install package |
| `BankTransaction` model not found | Low | Add model or fix import |
| `supplier_bank_account_query` syntax error in `country_ai_research.py` | Low | Fix syntax error |

---

## 9 · Execution Order & Dependencies

```
preflight.spec.ts (no deps)
    ↓
database.spec.ts (depends on: backend booted, Alembic configured)
    ↓
auth/ (depends on: preflight + database passing, backend booted)
    ↓
modules/admin/ (depends on: auth passing, seed data loaded)
modules/customer/ (depends on: auth passing, seed data loaded)
modules/supplier/ (depends on: auth passing, seed data loaded)
modules/logistics/ (depends on: auth passing, seed data loaded)
modules/employee/ (depends on: auth passing, seed data loaded)
    ↓
cross-cutting/ (depends on: all module tests passing)
```

---

## 10 · Prompt Templates for Sub-Agents

When delegating work to sub-agents, use these exact prompts:

### Prompt A — Port a single spec file

```
Port the Playwright E2E spec file `frontend/web_app/e2e/{SOURCE_SPEC}.spec.ts` to `_browser_test/tests/{CATEGORY}/{TARGET_SPEC}.spec.ts`.

Rules:
1. Do NOT import from `frontend/web_app/e2e/helpers/auth.ts` or `frontend/web_app/e2e/helpers/api.ts`.
2. Import auth helpers from `_browser_test/src/auth.ts` and API helpers from `_browser_test/src/api.ts`.
3. Preserve all test names and test.describe blocks exactly.
4. Use `_browser_test/playwright.config.ts` baseURL (`http://127.0.0.1:3100`).
5. Keep all `page.route()` mock interceptors.
6. Take screenshots on failure (already configured).
7. Return the full file content.

Reference architecture:
- `_most_imp_docx/ARCHITECTURE_STACK.md` — modules, domains, laws 1–325
- `_most_imp_docx/TECHNOLOGY_STACK.md` — versions, SDKs
- `_browser_test/src/auth.ts` — auth helpers
- `_browser_test/src/api.ts` — API helpers
```

### Prompt B — Write a new spec file from scratch

```
Write a new Playwright E2E spec file at `_browser_test/tests/{CATEGORY}/{SPEC_NAME}.spec.ts` that covers:

{COPY TESTS FROM SECTION 5.X ABOVE}

Rules:
1. Use `_browser_test/src/auth.ts` for session bootstrap.
2. Use `_browser_test/src/api.ts` for direct API calls.
3. Use `_browser_test/src/ui.ts` for ZOZI-specific selectors.
4. Base URL is `http://127.0.0.1:3100` (from `_browser_test/playwright.config.ts`).
5. Each test must be independently runnable (use `test.beforeEach` for setup).
6. Assertions must use Playwright's `expect` with explicit timeouts (min 30s).
7. Mock external providers via `page.route()` — never call real Stripe, PayPal, or SMS APIs.
8. Return the full file content.

Reference:
- `_most_imp_docx/ARCHITECTURE_STACK.md` §10 — security architecture
- `_most_imp_docx/TECHNOLOGY_STACK.md` §5 — auth/crypto/rate-limiting
- `frontend/web_app/e2e/helpers/auth.ts` — bootstrap pattern reference
```

### Prompt C — Fix a helper file

```
Complete the implementation of `_browser_test/src/{HELPER}.ts` by porting the full implementation from `frontend/web_app/e2e/helpers/{HELPER}.ts`.

Additional requirements for `_browser_test/`:
- Support `process.env.API_BASE_URL` and `process.env.WEB_BASE_URL` for URL resolution.
- Do NOT import from `frontend/web_app/e2e/helpers/` — all code must be self-contained.
- Add TypeScript type exports for all public functions.
- Return the full file content.

Reference: `_browser_test/playwright.config.ts` for baseURL configuration.
```

---

## 11 · Acceptance Criteria

The browser test suite is considered **functional** when:

1. **All 54 spec files** from `frontend/web_app/e2e/` are ported to `_browser_test/tests/` in the correct category directories.
2. **All new spec files** listed in §5 (preflight, employee, security, database) are written and passing.
3. **All helper files** (`auth.ts`, `api.ts`, `ui.ts`, `global-setup.ts`) are fully implemented.
4. **`playwright.config.ts`** includes reporter config, output paths, and env-var-driven URLs.
5. **`scripts/run-pipeline.ps1`** runs the full suite end-to-end without manual intervention.
6. **Preflight tests pass** — backend health, Valkey, Postgres, frontend, `/rbac/catalog`.
7. **Auth tests pass** for all 5 modules with both API bootstrap and UI form login.
8. **Customer core flow passes** — browse → cart → checkout → tracking.
9. **Supplier smoke passes** — registration multi-step, retired route redirects.
10. **Logistics fulfillment passes** — parcel sheet → scan → delivery → admin confirmation.
11. **Security tests pass** — RBAC 403, CSRF, XSS sanitization, rate limit 429, RLS isolation.
12. **Design system tests pass** — CSS tokens, glass panels, theme switching.
13. **Database tests pass** — seed data present, schemas correct, constraints enforced.
14. **Zero `page.route()` failures due to missing mock endpoints** — all intercepted routes must fulfill with valid JSON.
15. **All screenshots and traces on failure** — reports written to `_browser_test/reports/`.

---

## 12 · Non-Functional Requirements

| Requirement | Rule |
|---|---|
| No secrets in test files | Use `process.env` or `config/stack.env.ps1`; never hardcode passwords |
| No real external API calls | Mock Stripe, PayPal, SMS, WhatsApp, email via `page.route()` |
| Deterministic tests | Do not depend on real-time data; seed all required data via API before test |
| Independent tests | Each `test()` must be runnable in isolation; use `test.beforeEach` for setup |
| Explicit waits | Never use `page.waitForTimeout` as the sole wait; use `expect(locator).toBeVisible()` |
| Timeouts | Minimum 30s per test; 90s for navigation-heavy flows; 240s for multi-step flows |
| Viewport | Desktop: 1440x900; Mobile: 390x844; set explicitly per test |
| Trace on failure | Already configured in `playwright.config.ts` — do not disable |
| Screenshot on failure | Already configured — do not disable |

---

## 13 · Quick Reference — File Inventory

### Spec files present (64 total, 2026-10-02)

```
_browser_test/tests/
├── preflight.spec.ts
├── database.spec.ts
├── fixtures.ts
├── auth/
│   ├── auth-role-login.spec.ts
│   ├── auth-registration-login.spec.ts
│   ├── auth-session-refresh.spec.ts          ← stub, needs implementation
│   └── auth-rbac-gates.spec.ts               ← stub, needs implementation
├── modules/
│   ├── admin/
│   │   ├── admin-audit-fixes.spec.ts
│   │   ├── admin-commission.spec.ts
│   │   ├── admin-country-control-plane.spec.ts
│   │   ├── admin-country-enhanced.spec.ts
│   │   ├── admin-communication-hub.spec.ts
│   │   ├── admin-data-ops.spec.ts
│   │   ├── admin-logistics-workspace.spec.ts
│   │   ├── admin-hr-permissions.spec.ts
│   │   ├── admin-modules-reconciliation.spec.ts
│   │   ├── admin-payment-gateways.spec.ts
│   │   ├── admin-supplier-logistics-sanity.spec.ts
│   │   ├── admin-treasury-payout.spec.ts
│   │   ├── finance-e2e.spec.ts
│   │   ├── finance-cod-proof-live.spec.ts
│   │   ├── rbac-enforcement.spec.ts
│   │   ├── csrf-protection.spec.ts
│   │   ├── xss-protection.spec.ts
│   │   ├── rate-limiting.spec.ts
│   │   ├── rls-cross-tenant.spec.ts
│   │   └── input-validation.spec.ts
│   ├── customer/
│   │   ├── customer-core-flow.spec.ts
│   │   ├── cross-border-checkout.spec.ts
│   │   ├── customer-search.spec.ts
│   │   ├── customer-cart.spec.ts             ← stub, needs implementation
│   │   └── customer-wishlist.spec.ts         ← stub, needs implementation
│   ├── supplier/
│   │   ├── supplier-smoke.spec.ts
│   │   ├── supplier-search.spec.ts
│   │   ├── supplier-product-upload.spec.ts
│   │   ├── supplier-kyc.spec.ts
│   │   ├── supplier-bulk-upload.spec.ts
│   │   ├── supplier-voice-to-catalog.spec.ts
│   │   └── supplier-orders-payouts.spec.ts   ← stub, needs implementation
│   ├── logistics/
│   │   ├── shipping-quote.spec.ts
│   │   ├── logistics-country-switching.spec.ts
│   │   ├── fulfillment-role-flow.spec.ts
│   │   ├── parcel-verification.spec.ts
│   │   └── logistics-dashboard.spec.ts       ← stub, needs implementation
│   └── employee/
│       ├── employee-login.spec.ts
│       ├── employee-dashboard.spec.ts
│       ├── employee-orders.spec.ts
│       ├── employee-customers.spec.ts
│       └── employee-hr.spec.ts
└── cross-cutting/
    ├── panel-slider-audit.spec.ts
    ├── mobile-panel-audit.spec.ts
    ├── verify-all-panels.spec.ts
    ├── products-visual-shell.spec.ts
    ├── design-system-tokens.spec.ts
    ├── design-system-comprehensive.spec.ts
    ├── collapse-poll.spec.ts
    ├── bg-comparison-visual.spec.ts
    ├── chatbot-shopping-assistant.spec.ts
    ├── command-center.spec.ts
    ├── amendment-verify.spec.ts
    ├── country-research-all-modules.spec.ts
    ├── country-integration-rls.spec.ts
    ├── country-auto-populate.spec.ts
    ├── countries-search.spec.ts
    └── scaling_audit.spec.ts
```

### Helper / config files

```
_browser_test/src/auth.ts          complete (159 lines)
_browser_test/src/api.ts           complete (355 lines)
_browser_test/src/ui.ts            complete (65 lines)
_browser_test/playwright.config.ts complete
_browser_test/global-setup.ts      exists
_browser_test/global-teardown.ts   exists
_browser_test/scripts/run-pipeline.ps1 exists
config/stack.env.ps1               exists
```

### Files that must NOT be modified (scope boundary)

```
frontend/web_app/e2e/**/*.spec.ts      # source of truth, do not edit
frontend/web_app/e2e/helpers/**/*.ts   # source of truth, do not edit
backend/                                 # out of scope for browser tests
```

---

## 14 · Execution Command

```powershell
# 1. Install browsers (once)
cd _browser_test
npx playwright install chromium

# 2. Configure environment
copy config\stack.env.ps1.example config\stack.env.ps1
# Edit config/stack.env.ps1 with real secrets

# 3. Start services (in separate terminals)
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

cd frontend/web_app
npx next dev --port 3100

# 4. Run pipeline
cd _browser_test
.\scripts\run-pipeline.ps1
```

---

## 15 · Benchmark Compliance Matrix

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

---

*Prompt version: 1.0 — 2026-10-01*
*Authority: `_most_imp_docx/ARCHITECTURE_STACK.md`, `_most_imp_docx/TECHNOLOGY_STACK.md`*
