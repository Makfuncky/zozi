```
=== AGENT LOG ===
PHASE: 08 — API Forensic Audit
STATUS: COMPLETED
REPORT_FILE: _audit/findings/PHASE_08_API_FORENSICS.md
SCOPE_COVERED: FastAPI app bootstrap + middleware pipeline; router mounting model; authN/authZ/RBAC dependencies; rate limiting; CSRF; webhook verification; API versioning; payments/checkout/cart/auth/admin/supplier endpoint sampling; WebSockets; openapi.json cross-check.
FILES_EXAMINED: ~34 read directly + grep across all 90 router files (~1001 route matches)
EVIDENCE_ITEMS: ~85 file:line citations
FINDINGS_TOTAL: 27  (VERIFIED: 21 / INFERRED: 5 / UNKNOWN: 1)
SEVERITY_BREAKDOWN: BLOCKER: 2 / HIGH: 6 / MEDIUM: 9 / LOW: 6 / INFO: 4
TOP_FINDINGS:
  1. CORS middleware imported + configured but NEVER registered (absent from _FOUNDATION) — middleware/orchestrator.py:43,68-73,217 vs tests asserting presence
  2. Payment webhooks unreachable/contradictory: real routes /api/v1/customer/finance/*webhook carry require_feature("finance.ledger.write") + CSRF applies; HMAC middleware path list never matches — modules/customer/routers/finance.py:301-333; middleware/webhook_verification.py:69-73
  3. Cart endpoints 403 for customers: require_feature("customers.cart.manage") not in _ROLE_FEATURES["customer"]; no override path — rbac/dependencies.py:88-96 vs modules/customer/routers/orders.py:59-139
  4. Rate-limit path tiers keyed on unversioned prefixes never match /api/v1/... routes — middleware/rate_limit_middleware.py:24-52; api_version_middleware.py (no path rewrite)
  5. 5 admin routers (config_versions,disputes,permissions,staff,tickets = 31 endpoints) defined but not mounted — modules/admin/routers/__init__.py:10-26
  6. Committed openapi.json is an empty stub {"paths":{}} — frontend/web_app/openapi.json:1-5
GAPS / NOT DETERMINABLE: Runtime confirmation of 403 behavior (static only); exhaustive per-endpoint authZ for all ~1000 routes (sampled); internal webhook-handler signature verification (Phase 10 scope); whether unmounted admin routers are intentionally retired vs regression.
SELF_SKEPTICISM_RATING: 4
=== END AGENT LOG ===
```

# PHASE 08 — API FORENSIC AUDIT (Zozi backend)

> Forensic, evidence-based, skeptical. READ-ONLY audit. Every claim labeled
> VERIFIED / INFERRED / UNKNOWN with `file:line`. Secrets are referenced by
> location only, never reproduced.

## 0. Scope, Method, and Sampling

- **Framework (VERIFIED):** Python FastAPI. App constructed in [backend/main.py](../../backend/main.py#L76-L84) with `docs_url="/docs"`, `redoc_url="/redoc"`.
- **Mounting model (VERIFIED):** Routers are discovered by `_load_routers()` ([backend/main.py](../../backend/main.py#L212-L273)) which imports `modules.{customer,supplier,logistics,admin,employee}.routers` and calls `app.include_router()` for each object in that package's `routers` and `public_routers` lists ([backend/main.py](../../backend/main.py#L263-L272)). Each router carries its own `APIRouter(prefix=...)`; no extra prefix is added.
- **Surface size (VERIFIED):** A single regex for route decorators returned **1001 matches across 90 router files**. This audit deep-reads the priority set (auth, cart/checkout/orders, payments/webhooks, admin, supplier, RBAC, middleware, config) and uses repository-wide grep for breadth. **Coverage is a prioritized sample, not exhaustive per-endpoint.**
- **Files deep-read:** `main.py`, `middleware/orchestrator.py`, `authentication_middleware.py`, `rate_limit_middleware.py`, `csrf_middleware.py`, `api_version_middleware.py`, `webhook_verification.py`, `prometheus_setup.py`, `infrastructure/security/auth.py`, `infrastructure/security/dependencies.py`, `domains/accounts/services/auth/security_dependencies.py`, `rbac/dependencies.py`, `rbac/resolution.py`, `rbac/catalog.py`, `rbac/__init__.py`, `config.py`, all 5 module `routers/__init__.py`, `modules/customer/routers/{accounts,orders,finance}.py`, `modules/admin/routers/orders.py`, `domains/customers/features.py`, `tests/rbac/test_rbac.py`, `frontend/web_app/openapi.json`, plus targeted grep of the 5 unmounted admin routers and employee HR.

---

## 1. API Inventory (types present)

| API type | Present? | Evidence |
|---|---|---|
| REST (JSON over HTTP) | **VERIFIED yes** — the entire surface | modules/*/routers/*.py (1001 route decorators) |
| GraphQL | **VERIFIED no** | No `graphql`/`strawberry`/`graphene` router or route found in module routers |
| RPC (gRPC/JSON-RPC) | **VERIFIED no** (HTTP-only) | No gRPC servicer / rpc route in routers |
| WebSockets | **VERIFIED yes** | `/ws/user`, `/ws/admin/background-jobs` (main.py:167-247); `/ws-chat/*`, `/ws/logistics` (comms/logistics routers) |
| Webhooks (inbound) | **VERIFIED yes** | Stripe/Tap/PayPal/Thawani/PayTabs + generic — finance.py:301-340; email/resend referenced in middleware |
| External APIs (outbound) | **VERIFIED yes** | Payment gateways, bank API (`providers/finance/bank_api.py`), ipapi.co (geo, disabled) |
| Internal/admin APIs | **VERIFIED yes** | `/api/v1/admin/*`, `/api/v1/employee/*` |
| Debug/docs endpoints | **VERIFIED yes** | `/docs`, `/redoc`, `/openapi.json`, `/metrics`, `/health*` |

### 1.1 Router → prefix → mount-status map (VERIFIED)

Loader `_module_names` lists per module `routers/__init__.py`:

| Module | Loaded router files | Prefix pattern | Notes |
|---|---|---|---|
| customer | 15 (accounts…suppliers) | mostly `/api/v1/customer/*`; **`/customer/analytics` unversioned** | loader collects `router` only, **not** `public_router` (customer/routers/__init__.py:26-33) |
| supplier | 15 | mostly `/api/v1/supplier/*`; **`/supplier/{analytics,audit,comms,customers,governance,logistics}` unversioned** | loader collects `router` **and** `public_router` |
| logistics | 15 | `/api/v1/logistics/*`; **`/logistics/analytics` unversioned** | loader collects `router` only |
| admin | **15 of 20** | mixed: `/api/v1/admin/*` and bare full-paths in decorators | **config_versions, disputes, permissions, staff, tickets NOT in `_module_names`** (admin/routers/__init__.py:10-26) |
| employee | 15 | `/api/v1/employee/*`; **`/employee/analytics` unversioned** | `hr` resolves to the **`hr/` package**, shadowing sibling `hr.py` |

---

## 2. Representative Endpoint Table (priority sample)

Legend — Auth = authentication dependency; AuthZ = authorization gate; “feat” = `require_feature(...)`.

| Method | Route | Handler (file:line) | Auth | AuthZ | Input | Output | DB/Service | Evidence |
|---|---|---|---|---|---|---|---|---|
| POST | /api/v1/auth/login | login (customer/accounts.py:212) | none (public) | none | LoginRequest (pydantic) | tokens + cookie | `json_login_user` | accounts.py:211-219 |
| POST | /api/v1/auth/refresh | refresh (accounts.py:222) | refresh cookie/body | rotation+reuse detect | RefreshTokenBody? | tokens | `refresh_access_token` | accounts.py:221-236 |
| GET | /api/v1/auth/me | me (accounts.py:240) | HTTPBearer(auto_error=False) | token decode | — | id/role/email | `decode_token(check_blacklist=False)` | accounts.py:239-253 |
| POST | /api/v1/auth/logout | logout (accounts.py:256) | body/cookie token | none (CSRF-exempt) | RefreshTokenBody? | 200 | blacklist | accounts.py:255-262 |
| GET | /api/v1/customer/orders (cart) | get_cart (orders.py:57) | get_current_user | feat `customers.cart.manage` | — | cart | `svc_get_cart` | orders.py:57-63 |
| POST | /api/v1/customer/orders/items | add_to_cart (orders.py:65) | get_current_user | feat `customers.cart.manage` | CartItemCreate | cart item | `svc_add_to_cart` | orders.py:65-70 |
| POST | /api/v1/customer/orders/totals | calculate_cart_totals (orders.py:136) | get_current_user | feat `customers.cart.manage` | CartTotalsRequest | totals | promo/tax svc | orders.py:130-140 |
| POST | /api/v1/customer/orders/shipping-quote | get_cart_shipping_quote (orders.py:110) | **none** | feat `logistics.delivery.estimates` | CartShippingQuoteRequest | quote | `svc_get_cart_shipping_quote` | orders.py:109-115 |
| POST | /api/v1/customer/finance/create-payment-intent | (finance.py:161) | get_current_user | feat `finance.ledger.write` | PaymentIntentRequest | intent | `create_payment_intent` | finance.py:160-167 |
| POST | /api/v1/customer/finance/webhook | stripe_webhook (finance.py:302) | **none** | **feat `finance.ledger.write`** ⚠ | raw Request | provider ack | `handle_stripe_webhook` | finance.py:301-305 |
| POST | /api/v1/customer/finance/tap/webhook | tap_webhook (finance.py:309) | **none** | **feat `finance.ledger.write`** ⚠ | raw Request | ack | `handle_tap_webhook` | finance.py:308-312 |
| POST | /api/v1/customer/finance/paypal/webhook | paypal_webhook (finance.py:323) | **none** | **feat `finance.ledger.write`** ⚠ | raw Request | ack | `handle_paypal_webhook` | finance.py:322-326 |
| GET | /api/v1/customer/finance/ | list_payments (finance.py:92) | get_current_user | `_require_admin` + feat | page/page_size/status | payments | `svc_list_payments` | finance.py:91-96 |
| PUT | /api/v1/customer/finance/config/runtime | update_runtime_config (finance.py:116) | get_current_user | `_require_admin` + feat write | PaymentProviderRuntimeConfigRequest | config | payment_engine | finance.py:115-123 |
| GET | /api/v1/admin/orders/campaigns | list_all_campaigns_route (admin/orders.py:22) | require_admin | feat `orders.list` | — | campaigns | `list_all_campaigns` (comms!) | admin/orders.py:21-25 |
| GET | /api/v1/admin/orders/metrics | admin_email_metrics (admin/orders.py:28) | require_admin | feat `orders.read` | — | **501** | none (stub) | admin/orders.py:27-36 |
| POST | /api/v1/admin/accounts/bank-accounts/{cc}/{kind}/{id}/verify | (admin/accounts.py:81) | (per-route dep) | admin | path params | 201 | accounts svc | admin/accounts.py:81 |
| POST | /supplier/products/... upload | (supplier/catalog.py:61) | get_current_user (supplier) | feat catalog.write | UploadFile | product img | catalog svc | supplier/catalog.py:60-61 |
| POST | /api/v1/supplier/orders/{id}/parcel-proof | (supplier/orders.py:47) | supplier | feat | UploadFile+Form | proof | `upload_parcel_proof` | supplier/orders.py:44-55 |
| WS | /ws/admin/background-jobs | websocket_background_jobs (main.py:184) | token query param | inline role∈{admin,super_admin} | token | stream | websocket_manager | main.py:184-210 |

⚠ = see Finding H-2 (webhook contradiction).

---

## 3. The 20 Determinations

### 3.1 Authentication mechanism — VERIFIED
- **JWT bearer**, `python-jose`, HS256 symmetric, `SECRET_KEY` from settings. Access + refresh tokens with `jti`, `type`, refresh `family_id`. Passwords: **bcrypt** rounds=13. See [infrastructure/security/auth.py](../../backend/infrastructure/security/auth.py#L20-L23), `create_access_token`/`create_refresh_token` (L184-L214), `decode_token` (L349-L363).
- **Token revocation:** Redis blacklist with in-memory fallback; **fails closed in production** (`is_token_blacklisted` returns True if Redis down + APP_ENV=production — auth.py:98-116).
- **Refresh rotation + reuse detection:** `rotate_refresh_token` marks used JTIs and revokes families on replay (auth.py:369-406).
- **Middleware is non-enforcing (VERIFIED):** `AuthenticationMiddleware` only *populates* `request.state.user` from the token and always calls `call_next`, even when the token is missing/invalid ([authentication_middleware.py](../../backend/middleware/authentication_middleware.py#L36-L68)). **Therefore middleware does NOT protect endpoints** — enforcement is exclusively via FastAPI dependencies.

### 3.2 Authorization mechanism — VERIFIED
- Enforcement is **per-endpoint dependency**: `get_current_user` (401 if no/invalid token, loads `User`, rejects inactive — [security_dependencies.py](../../backend/domains/accounts/services/auth/security_dependencies.py#L41-L54)), plus role gates and feature gates.
- Role gates: `require_admin`, `require_super_admin`, `require_employee`, `require_supplier`, `require_customer`, `require_logistics`, `require_staff`, `require_treasury_access`, `require_coupon_admin`, `require_roles(*)`, `require_permissions([...])` (security_dependencies.py:77-215).
- `require_permissions` calls governance `check_permission(uid, slug, country_code, db)` (country-scoped RBAC) — security_dependencies.py:189-215.

### 3.3 Role system — VERIFIED
- Roles are string values on `User.role`: `customer`, `supplier`, `employee`, `staff`, `admin`, `super_admin`, `logistics_partner` (enumerated in `_require_role` calls + `_ROLE_FEATURES`/`_ROLE_MODULES` — rbac/dependencies.py:60-113).

### 3.4 Permission system — VERIFIED (with a broken grant path)
- Feature-atom catalog aggregated from `domains/*/features.py` into `FEATURE_CATALOG` ([rbac/catalog.py](../../backend/rbac/catalog.py#L12-L35)).
- Effective set = `role_features ∪ db_grants ∪ overrides`, wildcards expanded against catalog ([rbac/resolution.py](../../backend/rbac/resolution.py#L27-L34)).
- **Critical:** in `_resolve_effective_features`, **`db_grants` is hardcoded `[]`** and `feature_overrides` is read via `getattr(user, "feature_overrides", [])` ([rbac/dependencies.py](../../backend/rbac/dependencies.py#L38-L53)). Repo-wide grep shows **no `feature_overrides` attribute/column on the `User` model** (only rbac/dependencies.py and tests reference it). So for ORM users the override list is always empty → the *only* grant source is the static `_ROLE_FEATURES` map. See Finding H-3.
- Admin/super_admin are `["*"]` → all features (rbac/dependencies.py:61-62). `require_permission` (auth.py:424-434) additionally lets admin/super_admin **bypass any permission** slug — role-based escalation baked in.

### 3.5 Input validation — VERIFIED (mixed)
- Typed endpoints use **Pydantic** models (e.g., `LoginRequest`, `AddressCreate`, `CartItemCreate`, `PaymentIntentRequest`), giving 422 on violation. Password complexity regex + 72-char bcrypt cap (auth.py:335-353).
- **Gaps:** several admin endpoints accept untyped `payload: dict = Body(...)` (e.g., admin/orders.py:52-60 create_campaign; admin bank routes), bypassing schema validation — MEDIUM. Path params like `country_code` are validated ad-hoc via `get_country_or_404`.

### 3.6 Output validation — INFERRED (largely absent)
- Sampled routes return raw dicts / ORM-derived dicts; **`response_model=` is rarely used** (a few employee HR routes declare `response_model=dict`). No global response schema enforcement → risk of over-serialization. Not exhaustively verified across 1000 routes → INFERRED.

### 3.7 Error handling — VERIFIED
- Global handlers: `@app.exception_handler(Exception)` → `global_exception_handler` with `ErrorHandler`/optional Sentry (main.py:255-258, 60-72). Endpoints raise `HTTPException` for 401/403/404/422/501.
- **Info leak risk:** `/health/deps`, `/health/ready` expose dependency status; `admin_orders_routes/health` returns internal `prefix` (admin/orders.py:76-80). `/health/ready` returns blocking-dependency names (main.py:140-166) — LOW.

### 3.8 Rate limiting — VERIFIED (mis-keyed)
- `RateLimitMiddleware` sliding-window, Redis with in-memory fallback; **enabled by default** (`rate_limit_enabled=True`, config.py:139); bypassed for `app_env==test` (rate_limit_middleware.py:120-121). GET/HEAD capped at 300/60; write methods use `PATH_LIMITS`.
- **Defect (H-4):** `PATH_LIMITS` keys are **unversioned prefixes** (`/auth/login`, `/payments`, `/orders`, `/cart`, `/admin/payouts` …, rate_limit_middleware.py:24-52) matched via `path.startswith`. `ApiVersionMiddleware` does **not** rewrite `request.url.path` (it only reads a header — api_version_middleware.py:19-35). Actual routes are `/api/v1/...`, so **the strict tiers (login 10/min, payments 20/min, orders 20/min) never match** and fall through to `DEFAULT_LIMIT` (60/min). CSRF, by contrast, correctly lists `/api/v1/auth/*` (csrf_middleware.py:28-37) — proving the rate-limit list is stale.
- On Redis error the limiter **fails closed** (429) — availability risk if Redis is flaky.

### 3.9 Pagination — VERIFIED (inconsistent)
- Two conventions coexist: `page`/`page_size` (e.g., finance.py:91, admin campaigns) and `limit`/`offset` (e.g., accounts.py:139 `list_addresses`). Response envelopes vary (`{items,total,page,page_size,total_pages}` vs `{data,total,page,pageSize}` vs bare arrays) — corroborated by repo memory `frontend-api-contracts`. MEDIUM (contract drift).

### 3.10 Filtering — VERIFIED
- Query-param filtering present on list endpoints (e.g., `/admin/orders` accepts `search,status,date_range,min_amount,...` per repo memory; finance `status`). Not standardized.

### 3.11 Sorting — INFERRED (sparse)
- No consistent `sort`/`order` parameter observed in sampled routes; ordering appears service-side. UNKNOWN in general.

### 3.12 Idempotency — VERIFIED (service/DB layer only)
- Strong idempotency exists **below the API layer**: `ProcessedWebhookEvent` + `_check_payment_idempotency_key` for payment webhooks (payment_engine.py:33,104; gateway_stripe/tap/paypal), coupon usage (coupon_service.py:30-59), coins redemption (zozi_coins_service.py:31-134), background jobs (`_compute_idempotency_key`), and DB `idempotency_key` UNIQUE columns (orders/payments/events migrations).
- **No inbound `Idempotency-Key` header contract** on client state-changing POSTs (create order/payment) in sampled routes; the `Idempotency-Key` header is used only outbound to the bank provider (`providers/finance/bank_api.py:88`). MEDIUM for client-driven duplicate submits.

### 3.13 CORS — VERIFIED **NOT WIRED** (Finding H-1)
- `CORSMiddleware` is imported and `_resolve_kwargs` builds full allow-origin/credentials/headers config ([orchestrator.py](../../backend/middleware/orchestrator.py#L43), L217-L225), but it is **absent from every layer list** — `_FOUNDATION` contains only GZip/IPExtraction/RequestID/ApiVersion (orchestrator.py:68-73). `setup_middleware` only registers items in the pipeline lists, so **CORS is never added**. `cors_origins_list` (config.py:470-472) is computed but unused. Tests explicitly assert `CORSMiddleware in _FOUNDATION` (tests/infrastructure/test_middleware_pipeline.py:109; tests/security/test_rls_enforcement.py:288; tests/architecture/test_webhook_cors_rate.py:54) — they would **fail** against current code (contradiction).

### 3.14 CSRF — VERIFIED
- Double-submit cookie (`csrf_token` cookie, `X-CSRF-Token` header), `httponly=False`, `secure` only in production, `samesite=lax`, constant-time compare ([csrf_middleware.py](../../backend/middleware/csrf_middleware.py#L41-L133)). Stateful methods enforced; `OPTIONS` and `CSRF_EXEMPT_PATHS` (auth endpoints) skipped.
- **Weaknesses:** token is a bare random value not bound to the user/session (subdomain/XSS could forge); `WEBHOOK_PATHS` exemption (`/payments/webhook`,`/payments/tap/webhook`,`/email/webhooks`) **does not match real webhook routes** (`/api/v1/customer/finance/*`) → real webhooks are **not** CSRF-exempt (contributes to H-2). MEDIUM.

### 3.15 File upload handling — VERIFIED (validation delegated)
- `UploadFile` endpoints: supplier product image (catalog.py:60-61), supplier parcel-proof (orders.py:44-55, passes `filename`+`content_type` to service), supplier documents (suppliers.py:44), employee comms attachments (comms.py:139 `list[UploadFile]`), logistics (logistics.py:8). Size/extension/content-type validation is **delegated to services** — not verified at route layer (INFERRED for robustness). No route-level max-size guard observed.

### 3.16 API versioning — VERIFIED (inconsistent)
- URL versioning `/api/v1/...` is the dominant scheme, plus a header (`API-Version`) read but unused for routing (api_version_middleware.py:22-24). Version helpers exist (`infrastructure/utils/versioning`).
- **Inconsistency:** analytics routers are **unversioned** (`/admin/analytics`, `/supplier/analytics`, `/customer/analytics`, `/logistics/analytics`, `/employee/analytics`); several supplier routers are unversioned (`/supplier/{audit,comms,customers,governance,logistics}`); some admin routers embed full paths in decorators instead of a prefix. MEDIUM.

### 3.17 Sensitive info exposure — VERIFIED / INFERRED
- `/docs`, `/redoc`, `/openapi.json` enabled **unconditionally** (main.py:76-83) — full schema browsable in production (MEDIUM/INFO).
- `/metrics` exposed with **no authentication** when `PROMETHEUS_ENABLED` env is set (`include_in_schema=False`, prometheus_setup.py:19-27) — internal metrics reachable (MEDIUM).
- Health endpoints expose dependency/runtime status unauthenticated (main.py:110-166) (LOW).
- **Secret handling:** `SECRET_KEY` default is a **hardcoded dev value** `"zozi-dev-secret-key-change-in-production-2026"` (config.py:31) which is **not** in the production placeholder blocklist (config.py:220), so production boot validation would pass with the known key if `SECRET_KEY` env is unset. Value is referenced by location only; full analysis deferred to Phase 09/11. HIGH (auth foundation).

### 3.18 Debug endpoints — VERIFIED
- `/docs`, `/redoc`, `/openapi.json` (main.py:76-83); `/metrics` (prometheus); `/health`, `/health/deps`, `/health/ready` (main.py:110-166). No `pdb`/eval debug route found. The `/api/v1/admin/orders/metrics` returns 501 stub (admin/orders.py:27-36).

### 3.19 Admin endpoints — VERIFIED
- Under `/api/v1/admin/*` gated by `require_admin` + `require_feature` (admin has `["*"]`, so the operative gate is `require_admin`). Example: admin/orders.py:21-80. **But 5 admin router files are not mounted** (Finding H-5), so a large slice of the *intended* admin surface (staff management, permission role assign/revoke, user override, disputes, tickets, config versions) is **absent at runtime**.

### 3.20 Internal endpoints accidentally exposed — VERIFIED (inverse problem dominates)
- No evidence of internal-only endpoints being *unintentionally public*; the dominant issue is the **reverse**: intended endpoints are unreachable (unmounted admin routers H-5, dropped `public_router` M-4, shadowed `hr.py` M-5). The one genuinely public data endpoint by design is `/metrics` (see 3.17). `require_feature`-gated routes that use `get_current_user_optional` (e.g., cart shipping-quote, webhooks) are **not** public because their features aren't in `_PUBLIC_FEATURES` (`{catalog.list, catalog.read}`, rbac/dependencies.py:36-38).

---

## 4. Request → response traces (priority endpoints)

### 4.1 `POST /api/v1/auth/login` (VERIFIED)
1. Foundation middleware (GZip/IP/RequestID/ApiVersion). **No CORS** (H-1).
2. AuthenticationMiddleware: no bearer → `request.state.user=None`, proceeds.
3. RateLimitMiddleware: path `/api/v1/auth/login` → **does not** match `/auth/login` tier → DEFAULT 60/min (H-4).
4. CSRF: path in `CSRF_EXEMPT_PATHS` → skipped (csrf_middleware.py:35).
5. Handler `login` (accounts.py:212) → `json_login_user` (validates `LoginRequest`, bcrypt verify, lockout counters, issues JWT + sets refresh cookie).
6. Response tokens returned. **Enforcement entirely in handler/service; no middleware auth.**

### 4.2 `POST /api/v1/customer/orders/items` (add to cart) (VERIFIED code path)
1–3. As above; rate tier = DEFAULT.
4. CSRF: POST, not exempt, not webhook → **requires `X-CSRF-Token` header + cookie** or 403.
5. Dependencies: `get_current_user` (401 if no token) → `require_feature("customers.cart.manage")` → `_resolve_effective_features(customer)` = `_ROLE_FEATURES["customer"]` (no cart.manage) → **403** (H-3).
6. `svc_add_to_cart` never reached for a normal customer per static analysis.

### 4.3 `POST /api/v1/customer/finance/webhook` (Stripe) (VERIFIED code path)
1–2. Foundation/Auth (provider sends no JWT → user None).
3. RateLimit: `/api/v1/customer/finance/webhook` → DEFAULT tier.
3.5. **WebhookVerificationMiddleware:** `WEBHOOK_PATHS={/payments/webhook,/payments/tap/webhook,/email/webhooks}`; path does **not** start with any → middleware **passes through without HMAC verification** (webhook_verification.py:80-84).
4. CSRF: POST, not exempt, `WEBHOOK_PATHS` mismatch → **CSRF token required → 403** for a provider that can't send it.
5. Even if reached, handler dep `require_feature("finance.ledger.write")` on an unauthenticated caller → public features only → **403** (finance.py:302-305).
→ **Contradiction H-2:** the endpoint is simultaneously (a) not HMAC-verified at the middleware layer and (b) blocked by CSRF + feature-gate for the real caller. Internal handler-side signature verification (Phase 10) cannot run because the request is rejected first.

---

## 5. openapi.json cross-check (VERIFIED)

- Committed contract file [frontend/web_app/openapi.json](../../frontend/web_app/openapi.json#L1-L5) is an **empty stub**: `{"openapi":"3.0.0","info":{"title":"ZOZI","version":"0.1.0"},"paths":{}}`.
- It documents **zero** of the ~1000 live routes. Any client codegen / contract test that consumes this file operates on an empty spec. (FastAPI still serves a *live* `/openapi.json` at runtime, which is unrelated to this committed artifact.)
- **Mismatch report:** 100% of real routes are undocumented in the committed spec (e.g., `/api/v1/auth/login`, `/api/v1/customer/orders`, `/api/v1/customer/finance/webhook`, `/api/v1/admin/*` all absent). Cross-verified by grep returning no matches for these paths in the file.

---

## 6. Findings (severity-ranked)

### BLOCKER
- **B-1 (=H-3) Cart unreachable for customers.** `require_feature("customers.cart.manage")` gates all cart ops (orders.py:59,67,77,84,98,105,139) but the feature is not in `_ROLE_FEATURES["customer"]` (rbac/dependencies.py:88-96), `db_grants` is hardcoded `[]`, and `feature_overrides` is undefined on `User`. Static result: **HTTP 403** for authenticated customers. Status: VERIFIED (code) / INFERRED (runtime 403). Impact: core shopping flow broken as written.
- **B-2 (=H-2) Payment webhooks contradictory/unreachable.** Middleware HMAC path list never matches real routes (no verification), while CSRF + `require_feature("finance.ledger.write")` reject the real (unauthenticated) provider callers. Status: VERIFIED. Impact: payment settlement/notification path cannot function as wired.

### HIGH
- **H-1 CORS never registered** (orchestrator.py:68-73 vs tests). VERIFIED. Impact: browser cross-origin calls from the SPA rely on same-origin/proxy; config is dead; tests contradict code.
- **H-4 Rate-limit tiers mis-keyed** to unversioned prefixes → sensitive endpoints (login/payments/orders) get the generic default, not their strict limits. VERIFIED.
- **H-5 Five admin routers unmounted** (config_versions, disputes, permissions, staff, tickets = 31 endpoints incl. `POST /permissions/roles/assign|revoke`, `POST /permissions/users/override`, `POST/PUT/PATCH/DELETE /admin/staff*`, `POST /admin/staff/{id}/reset-password`, disputes, tickets). admin/routers/__init__.py:10-26. VERIFIED (excluded from loader; no alternate include found).
- **H-6 SECRET_KEY dev-default not blocklisted** for production (config.py:31,220) — production can boot with the publicly-known JWT signing key. VERIFIED (config); deeper impact = Phase 09/11.

### MEDIUM
- **M-1** Untyped `Body(...)=dict` on several admin endpoints (no schema validation) — admin/orders.py:52-60 etc. VERIFIED.
- **M-2** Pagination/response-envelope inconsistency across modules. VERIFIED.
- **M-3** No inbound `Idempotency-Key` contract on client state-changing POSTs (dedup only service-side). VERIFIED.
- **M-4** `public_router` only defined in employee/security.py:66 but the employee loader ignores `public_routers` → **never mounted**; admin/supplier collect public routers but define none → **no public router is ever mounted**. VERIFIED.
- **M-5** Employee `hr/` package shadows sibling `hr.py` (~79 route decorators) by CPython package-over-module import precedence → `hr.py` is dead. VERIFIED (deterministic import behavior).
- **M-6** API versioning inconsistency (unversioned analytics/supplier routers vs `/api/v1/...`). VERIFIED.
- **M-7** `/docs`,`/redoc`,`/openapi.json` unconditional in production. VERIFIED.
- **M-8** `/metrics` unauthenticated when enabled. VERIFIED (conditional on `PROMETHEUS_ENABLED`).
- **M-9** CSRF token not bound to session (double-submit random only); webhook exemption path mismatch. VERIFIED.

### LOW / INFO
- **L-1** `admin/orders` router manages **email campaigns** (comms.ports), not orders, yet uses `orders.*` feature slugs — naming/contract contradiction (admin/orders.py:9-25). VERIFIED.
- **L-2** `/api/v1/auth/me` calls `decode_token(..., check_blacklist=False)` unconditionally (accounts.py:245-246) → revoked tokens still resolve on `/me`. VERIFIED.
- **L-3** `customer/finance._require_admin` calls `current_user.get("role")` on an ORM `User` (rbac.get_current_user returns ORM) → likely `AttributeError`/500 for admins (fails closed) — finance.py:82-85. INFERRED.
- **L-4** Health endpoints leak dependency/runtime/router-prefix info. VERIFIED.
- **L-5** `require_permission` admin/super_admin bypass (auth.py:429-433). VERIFIED.
- **L-6** RateLimit fails closed (429) on Redis error — availability risk. VERIFIED.
- **INFO-1** No GraphQL/gRPC (REST + WS only). VERIFIED.
- **INFO-2** Test/code contradiction: `test_no_user_returns_empty_features` asserts `set()` but code returns `{catalog.list,catalog.read}` (rbac/dependencies.py:36-38 vs tests/rbac/test_rbac.py:257-260). VERIFIED.
- **INFO-3** Separate `CORSMiddleware` usage inside `domains/logistics/services/core/service.py:2956-2974` (a distinct object, not the main app pipeline) — purpose UNKNOWN. UNKNOWN.
- **INFO-4** Payment webhook secrets (`stripe/tap/paypal/resend_webhook_secret`) referenced by settings at import (webhook_verification.py:38-66) — locations only, not values.

---

## 7. Contradictions (reported, not resolved)

1. Tests assert `CORSMiddleware in _FOUNDATION`, code omits it (H-1).
2. Test asserts empty features for anonymous, code grants public features (INFO-2).
3. CSRF path list is versioned (`/api/v1/auth/*`) but rate-limit and webhook path lists are unversioned (`/auth/*`, `/payments/*`) — same repo, divergent path assumptions (H-4, H-2).
4. `admin/orders` router is labeled/gated as orders but implements comms campaigns (L-1).
5. Two `require_roles`/`require_admin` implementations exist — in `security_dependencies.py` and `rbac/dependencies.py` — with different shapes (dict vs ORM handling), a source of the L-3 latent bug.

---

## 8. Gaps / NOT DETERMINABLE

- Runtime confirmation of the 403 behaviors (B-1/B-2) — analysis is static; `NOT DETERMINABLE FROM AVAILABLE CODE` without executing the app.
- Exhaustive authN/authZ for all ~1000 routes — sampled priority set only.
- Whether the 5 unmounted admin routers and `hr.py` are intentional retirements or regressions — intent `NOT DETERMINABLE`.
- Internal webhook-handler signature verification correctness — Phase 10 scope.
- Purpose of the CORS block inside logistics service.py — UNKNOWN.
```
