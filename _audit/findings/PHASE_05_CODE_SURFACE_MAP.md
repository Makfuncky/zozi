```
=== AGENT LOG ===
PHASE: 05 — Application Code Surface Map
STATUS: COMPLETED (sampled — see Coverage & Sampling)
REPORT_FILE: _audit/findings/PHASE_05_CODE_SURFACE_MAP.md
SCOPE_COVERED: backend entry point + wiring (main.py, lifespan, routers); highest-value domains
  (orders, payments, finance/ledger/payouts, catalog, cart, promotions, logistics partners,
  accounts/auth, security/fraud), plus rbac/, providers/payments/, infrastructure/events,
  jobs/, kernel/. API-handler + background-job surface quantified across all modules.
FILES_EXAMINED: ~55 opened/greped in depth; structural line/route/task census over ~1272 backend .py files
EVIDENCE_ITEMS: ~120 file:line citations
FINDINGS_TOTAL: 31  (VERIFIED: 24 / INFERRED: 6 / UNKNOWN: 1)
SEVERITY_BREAKDOWN: BLOCKER: 0 / HIGH: 4 / MEDIUM: 9 / LOW: 6 / INFO: 12
TOP_FINDINGS:
  1. RBAC DB grants never enforced — resolver hardcodes db_grants=[] — backend/rbac/dependencies.py:47-53 vs backend/rbac/resolution.py:20-27 & backend/rbac/service.py:24-125
  2. Unbound `ctrl` in logistics_partner_service.py (import commented at line 13) — every ctrl.* delegator would fail — backend/domains/logistics/services/partners/logistics_partner_service.py:13
  3. Finance ledger god-module: 7113 lines / 260 symbols mixing CoA, journals, AR/AP, bank transfer providers, commissions — backend/domains/finance/services/ledger/general_ledger_service.py
  4. Duplicate stub `is_checkout_payment_method_allowed` always returns True (no country gate) shadows real gating impl — backend/domains/finance/services/payouts/payout_batch_service.py:1670 vs backend/domains/finance/services/payments/payment_engine.py:1119
  5. Double `__init__` on PaymentEngine class (second silently overrides first) — backend/domains/finance/services/payouts/payout_batch_service.py:489,496
GAPS / NOT DETERMINABLE: Full runtime call-graph (Called By) not traced for every symbol — marked
  INFERRED/UNKNOWN where not verified. hr/comms/country/analytics/audit/governance domains sampled
  only at census level. No dynamic execution performed.
SELF_SKEPTICISM_RATING: 4
=== END AGENT LOG ===
```

# PHASE 05 — APPLICATION CODE SURFACE MAP (Zozi backend)

> Forensic, evidence-based. Every claim is labelled **VERIFIED** (read from source at
> cited line), **INFERRED** (strongly implied by cited evidence but not fully traced), or
> **UNKNOWN**. No codebase file was modified. No secret values are reproduced.

---

## 0. Coverage & Sampling (read this first)

**VERIFIED census (whole backend):**
- Python files (excl. `__pycache__`, `tests/`, `alembic/versions/`): **1,272**
- Total Python LOC (same exclusions): **~189,268**
- HTTP route decorators under `backend/modules/**`: **981** (admin 233, customer 128, employee 402, logistics 128, supplier 90)
- Celery/background task decorators under `backend/jobs/`: **~31** across 11 job modules
- Domain file counts: logistics 77, suppliers 65, comms 57, finance 57, orders 54, hr 54, catalog 48, country 47, governance 46, customers 46, promotions 45, accounts 41, security 38, audit 35, analytics 19, payments 12
  - Evidence: terminal census over `backend/` (Get-ChildItem + Select-String).

**Sampling policy.** The executable surface is far larger than any single phase can fully
enumerate. Per the task, I prioritized the **highest-value domains** — orders, payments,
finance, catalog/products, cart/checkout, promotions, logistics, accounts/auth, and
rbac/security — and read those files at symbol + line level. Lower-value domains
(hr, comms, country, analytics, audit, governance, suppliers) are covered at **census
level** (file/line/route counts) with spot symbol maps. Where I did not trace a caller,
I say so rather than guessing. **Depth over false completeness.**

---

## 1. Runtime entry point & wiring (VERIFIED)

| Symbol | File | Type | Called By | Calls | Purpose | Evidence |
|---|---|---|---|---|---|---|
| `app` (FastAPI) | backend/main.py:74 | module global (singleton app) | uvicorn `main:app` | `build_lifespan()`, `setup_middleware`, `setup_prometheus`, `_load_routers` | Root ASGI application | main.py:74-91 |
| `_load_routers()` | backend/main.py:250-289 | function | module load (`_load_routers()` at :291) | `importlib.import_module("modules.<m>.routers")`, `app.include_router` | Dynamically imports & mounts routers for customer/supplier/logistics/admin/employee | main.py:250-291 |
| `build_lifespan()` | backend/lifespan.py | factory | `FastAPI(lifespan=...)` | startup/shutdown hooks | App lifecycle hooks | main.py:71,79 |
| `setup_middleware(app)` | backend/middleware/orchestrator.py | function | main.py:93 | registers middleware stack | Wires 20+ middleware | main.py:24,93 |
| `health_check` / `health_deps` / `health_ready` | backend/main.py:118-183 | API handlers | k8s/infra probes | `_get_redis`, `check_connection_health`, `_payment_provider_runtime_status` | Liveness/readiness | main.py:118-183 |
| `websocket_background_jobs` | backend/main.py:208-244 | WS port handler | `/ws/admin/background-jobs` | `decode_token`, `manager.*` | Admin realtime job push; **inline JWT+role auth** | main.py:208-244 |
| `general_exception_handler` | backend/main.py:302-305 | exception handler | FastAPI | `global_exception_handler` | Catch-all error funnel | main.py:302 |

**INFERRED (INFO):** Routers are **discovered dynamically** via `importlib` (main.py:262).
A router that raises on import is logged and **skipped** (main.py:270-283), so a broken
router silently drops its endpoints rather than failing boot. Impact: endpoint set is
partly determined at runtime; static enumeration (981) is an upper bound of *declared*
routes, not a guarantee all mount.

**Model-registry import-ordering side effect (VERIFIED, INFO):** `main.py:13` imports
`infrastructure.database.models` *first* "to ensure SQLAlchemy class registry is
populated." RLS is wired via `instrument_rls(engine)` and `install_rls_policies(engine)`
(main.py:44-56), skipped when `app_env == "test"`. This is a load-time global side effect.

---

## 2. Authorization surface — rbac/ (SECURITY-CRITICAL)

| Symbol | File | Type | Called By | Calls | Purpose | Evidence |
|---|---|---|---|---|---|---|
| `require_feature(feature)` | backend/rbac/dependencies.py:106-133 | dependency factory / dual-mode guard | module routers (`Depends(...)`) & direct calls | `_resolve_effective_features` | Feature gate → HTTP 403 | dependencies.py:106 |
| `require_module(module)` | backend/rbac/dependencies.py:136-169 | dependency factory | routers | `_ROLE_MODULES` lookup | Module gate | dependencies.py:136 |
| `require_roles(*roles)` | backend/rbac/dependencies.py:172-191 | dependency factory | routers | role compare | Role gate | dependencies.py:172 |
| `require_admin(user)` | backend/rbac/dependencies.py:193+ | guard | handlers | `_get_current_user` | Admin gate | dependencies.py:193 |
| `_resolve_effective_features(user)` | backend/rbac/dependencies.py:39-53 | function | all three gates above | `effective_features(...)` | Compute user feature set | dependencies.py:39-53 |
| `effective_features(...)` | backend/rbac/resolution.py:20-27 | pure function | `_resolve_effective_features` | `expand_wildcards` | Merge role+db+overrides, expand `*` | resolution.py:20 |
| `expand_wildcards(features, catalog)` | backend/rbac/resolution.py:8-18 | pure function | `effective_features` | — | Expand `*` / `x.*` against catalog | resolution.py:8 |
| `RBACService.grant/revoke/check_permission` | backend/rbac/service.py:24-125 | class methods | admin permission routers (INFERRED) | writes `RolePermissionAssignment`, `_audit_log` | **DB-backed** grant/revoke | service.py:18-125 |
| `_ROLE_FEATURES`, `_ROLE_MODULES`, `_PUBLIC_FEATURES` | backend/rbac/dependencies.py:32-104 | module dicts (global config state) | resolver/guards | — | Hardcoded role→feature/module map | dependencies.py:32-104 |
| `_current_user_ctx` | backend/rbac/dependencies.py:15 | `ContextVar` (global) | `require_*` direct-call path | — | Ambient current user | dependencies.py:15 |

**HIGH — RBAC DB grants are never enforced (VERIFIED, contradiction).**
`effective_features()` accepts a `db_grants` argument and unions it into the result
(resolution.py:25), and its docstring claims it "Merges role defaults + **DB grants** +
per-user overrides + **country scope**" (resolution.py:1-5). But the **only** request-path
caller, `_resolve_effective_features()`, invokes it with **`db_grants=[]` hardcoded**
(dependencies.py:50) and passes **no country scope**. Meanwhile `RBACService.grant()`/
`revoke()` persist `RolePermissionAssignment` rows and audit logs (service.py:24-125).
Net effect: **admin-managed DB permission grants have no runtime effect**; authorization is
driven solely by the static `_ROLE_FEATURES` dict + per-user `feature_overrides`.
Impact: privilege management UI/API may appear to work while changing nothing; also a
documentation-vs-code contradiction. (Deep auth verification deferred to Phase 09.)

**MEDIUM — `require_feature` dual-mode returns a no-op closure when context is unset
(VERIFIED, latent risk).** When called **directly** (not via `Depends`), the function reads
`_get_current_user()` from a `ContextVar`; if that is `None` it falls through and **returns
the `_check` function object** (dependencies.py:129-133) instead of performing a check. If a
route handler calls `require_feature("x")` inline without the context var being populated,
the guard silently becomes a no-op (returns a function, no exception). Whether any handler
does this is **UNKNOWN** here (defer to Phase 09/11). Impact: potential silent auth bypass
depending on call convention.

**INFO — super_admin/admin = `["*"]` wildcard (VERIFIED).** dependencies.py:60-61 grant all
features/modules via `"*"`, expanded against `FEATURE_CATALOG`.

---

## 3. Orders domain (VERIFIED symbol map)

### 3.1 Order engine — `backend/domains/orders/services/core/order_engine.py` (1,132 LOC, 27 symbols)

| Symbol | Type | Called By | Calls | Purpose | Evidence |
|---|---|---|---|---|---|
| `create_order(order, current_user, db, request)` | function (**large, ~193 LOC**) | customer orders router (INFERRED) | `_load_products_for_order`, `_calculate_shipping`, `_quote_supplier_groups`, `_calculate_order_amounts`, `_rollback_order_creation` | Core checkout: validate, price, persist order | order_engine.py:726-918 |
| `preview_order(...)` | function | checkout preview handler (INFERRED) | pricing helpers | Dry-run price/shipping | order_engine.py:919-998 |
| `_calculate_order_amounts(...)` | function | `create_order`, `preview_order` | money kernel | Totals/discount/VAT math | order_engine.py:601-725 |
| `_quote_supplier_groups(...)` | function | pricing path | `_calculate_supplier_zone_shipping`, `_calculate_fallback_shipping` | Per-supplier shipment quotes | order_engine.py:389-553 |
| `validate_order_transition(cur, target)` | pure function | status-change flows (INFERRED) | — | State-machine guard | order_engine.py:92 |
| `_generate_order_number()` | function | `create_order` | — | Order number minting | order_engine.py:122 |

### 3.2 Cross-domain READ facade — `backend/domains/orders/ports.py` (1,361 LOC, 98 fns) (VERIFIED)
- Pure read helpers with **keyset/cursor pagination** returning `CursorPage` envelopes
  (ports.py:1-18, `list_orders_keyset`:1262). Explicitly a **Law-3 sanctioned** cross-domain
  read boundary — other domains import these instead of `domains.orders.models`.
- Re-exports logistics tracking functions (`logistics_confirm_pickup`, `logistics_deliver_order`,
  etc.) from `services.tracking.service` (ports.py:39-47).
- **Hidden dynamic surface:** module-level `__getattr__` (ports.py:1587-1595) lazily resolves
  names from `_LAZY_SERVICE_EXPORTS` via `importlib`, and a top-level `try/except ImportError`
  aliases promotions functions (`list_flash_sales as get_all_flash_sales`) (ports.py:1598-1616).
  Impact: some importable names do not exist statically; import failures are swallowed.

### 3.3 Fulfillment + mis-homed logistics — `backend/domains/orders/services/core/logistics.py` (4,527 LOC, 145 symbols)
| Symbol | Type | Purpose | Evidence |
|---|---|---|---|
| `FulfillmentService` | class | Reacts to `PaymentConfirmedEvent`; drives inventory fulfillment | logistics.py:27-260 |
| `FulfillmentService.handle_payment_confirmed` | event handler | `_process_inventory_fulfillment`, `_complete_successful_fulfillment` | logistics.py:35 |
| `list_partners`, `create_partner`, `update_partner`, `delete_partner`, `get_partner_dashboard`, `get_partner_analytics`, `request_partner_payout`, `verify_partner_payout`, `get_partner_shipments`, `update_shipment_status_partner`, `get_partner_pricing_insights`, `upsert_my_partner_*` | functions (full bodies) | **Canonical logistics-partner implementation living in the orders domain** | logistics.py:2172, 2193, 2273, 2324, 2442, 2517, 2541, 2610, 2834, 3258, 3091, 1020-1256 |

**MEDIUM — logistics-partner business logic is physically located in the `orders` domain
(VERIFIED).** The real partner CRUD/analytics/payout implementations are in
`orders/services/core/logistics.py`, not in the `logistics` domain. See §7 for the
delegation chain that reaches them. This is a domain-boundary/cohesion concern.

---

## 4. Payments surface

### 4.1 `backend/domains/finance/services/payments/payment_engine.py` (2,141 LOC, 121 symbols) (VERIFIED)
Mixes: ~30 Pydantic request/response models (payment_engine.py:379-943); multi-gateway
secret/config resolvers for **Stripe, Tap, PayTabs, PayPal, Thawani**; idempotency;
signature verification; runtime status.

| Symbol | Type | Purpose | Evidence |
|---|---|---|---|
| `get_payment_methods_status(db, country)` | function (~188 LOC) | Aggregate enabled methods per country | payment_engine.py:2039-2226 |
| `get_customer_checkout_gateways(db, country)` | function | Checkout gateway list | payment_engine.py:2227 |
| `upsert_payment_gateway_connection(...)` | function | Persist gateway connection | payment_engine.py:3105 |
| `test_payment_gateway_connection(code, db)` | function | Live connectivity test | payment_engine.py:3231 |
| `is_checkout_payment_method_allowed(...)` | function | **Real** country/method gate | payment_engine.py:1119-1172 |
| `_resolve_stripe_secret_key`, `_resolve_tap_secret_key`, `_resolve_paytabs_server_key`, `_resolve_thawani_secret_key`, `_verify_paytabs_signature` | functions | **Secret resolution / webhook signature** (SECRETS: existence noted, values NOT read) | payment_engine.py:1239,1320,1398,1908,1430 |

### 4.2 `backend/domains/finance/services/payments/payment_orchestrator.py` (1,053 LOC, 41 symbols) (VERIFIED)
Gateway **wizard** (`gateway_wizard_step` + 5 step fns), generic gateway create/callback/confirm,
badge billing, **settlement reconciliation** (`match_gateway_settlement`, `reconcile_cod_deposit`,
`run_gateway_3way_reconciliation`, `reconcile_all_cod_deposits`), and `GatewayAutoEnableService`
(payment_orchestrator.py:1609-1744). Multiple unrelated responsibilities in one module.

### 4.3 Payment provider adapters — `backend/providers/payments/` (VERIFIED)
| Symbol | File | Type | Purpose | Evidence |
|---|---|---|---|---|
| `BasePaymentGateway(ABC)` | providers/payments/base.py:83 | abstract base | Adapter contract: `validate_credentials`, `process_payment`, `process_refund`, `test_connection`, `verify_webhook_signature`, `normalize_webhook_payload` | base.py:83-159 |
| `PaymentGatewayRegistry` | providers/payments/registry.py:16 | class w/ **class-level `_registry` dict (global/singleton state)** | `register`, `register_adapter` (decorator), `get_or_raise`, `build`, `clear` | registry.py:16-69 |
| `register_provider` / `get_provider` / `dispatch_provider_operation` + `GatewayDefinition` | providers/payments/base.py:26-80 | **second, parallel** registry | Provider definition + op dispatch | base.py:26-80 |
| adapters: stripe, tap, paytabs, paypal, thawani, connect, generic | providers/payments/*.py | concrete adapters | Per-gateway impls | dir listing (7 adapters + webhooks/registry/base) |

**LOW — two parallel gateway-registration mechanisms (VERIFIED).** `PaymentGatewayRegistry`
(registry.py) and `register_provider`/`GatewayDefinition` (base.py) coexist. Impact: two
ways to register/resolve a gateway; risk of divergence about which is authoritative.

---

## 5. Finance / ledger / payouts

### 5.1 God-module — `backend/domains/finance/services/ledger/general_ledger_service.py` (7,113 LOC, 260 symbols)
**HIGH (maintainability) — single largest module (VERIFIED).** Distinct responsibilities all
co-resident:
- Chart of accounts: `seed_chart_of_accounts`:65, `repair_chart_of_accounts`:201
- Journals: `create_journal_entry`:340, `post_order_payment_journal`:582, `post_refund_journal`:711, `post_payout_journal`:791, `post_gateway_fee_journal`:830, `post_vat_remittance_journal`:873, `post_supplier_settlement_journal`:998
- Trial balance / periods: `get_trial_balance`:1058, `close_period`:1215, `_transfer_pnl_to_retained_earnings`:1279
- **Bank transfer providers** (payment-egress): `TransferExportProvider` (Protocol):1629, `ManualCsvTransferProvider`:1652, `ConfiguredBankApiTransferProvider`:2150, `StripeConnectTransferProvider`:2262
- AR/AP: `post_ar_invoice`:2681, `post_ap_payable`:2843, `get_ap_summary`:2922
- **Commissions**: `get_effective_rate`:3059, `set_supplier_commission`:3119, `set_product_commission_override`:3235, `get_global_config`:3467
Impact: accounting, treasury egress, AR/AP, and commission policy share one namespace and
one edit-blast-radius; high coupling and review risk. (Not "bad because large" — bad because
**≥5 independent bounded concerns** are fused with no internal module boundary.)

### 5.2 Payouts — `backend/domains/finance/services/payouts/payout_batch_service.py` (3,647 LOC, 145 symbols)
| Symbol | Type | Purpose | Evidence |
|---|---|---|---|
| `PayoutEngine` | class | Country-aware payout-rate resolution, `calculate_supplier_payout` | payout_batch_service.py:336-472 |
| `PaymentEngine` | class | Gateway-abstracted payment/refund | payout_batch_service.py:474-680 |
| `PaymentOrchestratorService` | class (static methods) | enabled/sync/fees gateways | payout_batch_service.py:681-789 |
| `run_auto_payout_sweep` / `run_auto_logistics_payout_sweep` | functions (**large**, ~270 LOC each) | Automation sweeps | payout_batch_service.py:863-1136, 1137-1427 |
| `start_auto_payout_background_job` / `_loop` / `stop_...` | functions + thread loop | **Background thread** driving sweeps | payout_batch_service.py:1525-1571 |
| `approve_batch` / `reject_batch` / `dispatch_batch` | functions | Payout batch lifecycle | payout_batch_service.py:3084,3111,3136 |

**HIGH — trivial duplicate stubs shadow real payment logic (VERIFIED).** payout_batch_service.py:1650-1690
defines **leaf stubs** with names identical to real functions elsewhere:
- `is_checkout_payment_method_allowed(method, country)` → `return bool(method)` — **always True for any
  non-empty method; no country gating** (payout_batch_service.py:1670) — vs. the real gate at
  payment_engine.py:1119.
- `build_order_payment_snapshot(order, db)` → returns a 3-key dict (payout_batch_service.py:1658) — vs.
  the real snapshot builder at payment_engine.py:1714.
- also `apply_order_status_change`:1650, `normalize_checkout_payment_method`:1674, `order_holds_inventory`:1682.
The header calls these "leaf definitions so the import graph stays acyclic." Impact: any caller that
imports the *payouts* copies gets **no payment-method gating** and a **degraded snapshot**. Which
callers bind which copy is not fully traced here (defer to Phase 13/14), but the always-True gate is a
concrete correctness/security risk.

**MEDIUM — duplicate `__init__` on `PaymentEngine` (VERIFIED, code smell/latent bug).**
Two `def __init__(self, db)` at payout_batch_service.py:489 and :496 with a `_lazy_country_models`
method wedged between them; the second `__init__` silently overrides the first. Bodies are identical
today (harmless now) but the pattern indicates a botched merge and is fragile.

**LOW — duplicated function names within one module (VERIFIED).** `list_pending_payouts` is defined
twice (payout_batch_service.py:2578 and :2973) and `list_pending_payouts_by_country` similarly; the
later definition shadows the earlier. Impact: confusing surface; the earlier defs are dead.

### 5.3 Finance read facade — `backend/domains/finance/ports.py` (752 LOC, ~189 fns) (VERIFIED)
Mechanical `get_<X>_by_id` / `list_<X>s` / `list_<X>s_page` triplets per model (commission,
warehouse, PO/GRN, sales order, journals, accounts, AR/AP, invoices, VAT, bank txns…). Name
artifacts (`get_a_r_ledger_entry_by_id`:380, `get_v_a_t_remittance_by_id`:453) reveal
**code-generation** from class names (INFERRED). Not a defect; characterizes surface as generated boilerplate.

---

## 6. Catalog, cart, promotions

### 6.1 Products — `backend/domains/catalog/services/products/products_service.py` (729 LOC, 60 symbols) (VERIFIED)
| Symbol | Type | Purpose | Evidence |
|---|---|---|---|
| `get_products(...)` w/ inner `_compute()` | function + closure | Paginated listing (cache-wrapped) | products_service.py:195-289 |
| `create_product(...)` / `update_product` / `delete_product` | functions | Product CRUD | products_service.py:305,355,371 |
| `atomic_stock_decrement(db, product_id, qty)` | function | **Inventory** atomic decrement | products_service.py:444 |
| `finalize_inventory_atomic(db, order_id)` | function | Commit reserved stock | products_service.py:460 |
| `set_moderation_status` / `approve_product_by_id` / `reject_product_by_id` | functions | Moderation | products_service.py:659,641,650 |
| `_bump_product_cache_version()` | function (**hidden side effect**) | Invalidate product cache globally | products_service.py:881 |

### 6.2 Cart — `backend/domains/orders/services/cart/service.py` (551 LOC, 33 symbols) (VERIFIED)
`add_to_cart`:228, `update_cart_item`:252, `sync_cart`:307, `get_cart_shipping_quote`:411,
plus variant resolution (`_resolve_variant`:63) and low-level repo fns (`upsert_cart_item`:609).
Note **duplicate/legacy pairs**: `get_cart` vs `get_cart_legacy`:167/183; `upsert_cart_item` vs
`upsert_cart_item_legacy`:609/364 (LOW — parallel legacy surface).

### 6.3 Promotions (VERIFIED duplicate implementations)
**MEDIUM — BOGO logic duplicated across two files.** `calculate_bogo_discount` and
`validate_bogo_eligibility` exist with **near-identical bodies + identical docstring algorithm** in
both `promotions/services/bogo/bogo_service.py:66,111` and
`promotions/services/bogo/promotion_bogo_service.py:115,182`. Impact: two sources of truth for
discount math; they can silently diverge.
**LOW — coupon validation duplicated:** `validate_coupon_code` in `promotions/ports.py:36` and
`coupons/coupon_service.py:288`; `validate_coupon` in `ports.py:100` and
`coupons/customer_coupons_mgmt_service.py:18`.

---

## 7. Logistics partners — deep delegation chain (VERIFIED / INFERRED)

Three wrapper layers for one capability:
1. `modules/logistics/routers/logistics.py` (88 routes) → calls
2. `domains/logistics/services/partners/service.py` — imports `logistics_partner_service as ctrl`
   (service.py:17) and delegates every op (e.g. `list_partners → ctrl.list_partners`, service.py:154-158) → calls
3. `domains/logistics/services/partners/logistics_partner_service.py` — delegates again via `ctrl.*`
   (e.g. `list_partners → ctrl.list_partners(current_user, db)`, :157) → target names/sigs match
4. `domains/orders/services/core/logistics.py` (the canonical full implementation, §3.3).

**HIGH — `ctrl` is unbound in `logistics_partner_service.py` (VERIFIED).** The only `ctrl` binding
in that file is a **commented-out import** at line 13
(`# import domains.logistics.services.logistics_partner_service as ctrl`); no active `import ... as ctrl`
exists (verified by grep for `as ctrl` and `^from|^import`). Yet ~150 functions reference `ctrl.*`
(e.g. :157, :161). Therefore, if those functions are invoked, they raise `NameError: name 'ctrl' is
not defined`. Whether they are reachable at runtime is not executed/traced here (mark the runtime
failure **INFERRED**; the missing binding is **VERIFIED**). Impact: either dead code or a live break
in the logistics-partner path; strong cross-reference for Phase 13 (dead code) and Phase 14 (bugs).

**INFERRED** — `service.py` also references `ctrl.list_public_partners` (service.py:40) while the
`ctrl` module exposes `list_public_logistics_partners` (different name), suggesting further
name-mismatch fragility in this chain (needs Phase 14 confirmation).

---

## 8. Security / fraud — `backend/domains/security/services/fraud/fraud_detection_service.py` (1,095 LOC, 59 symbols) (VERIFIED)
| Symbol | Type | Purpose | Evidence |
|---|---|---|---|
| `IPIntelligenceService` | class | IP reputation/geo/ASN, `_calculate_ip_risk` | fraud_detection_service.py:76-200 |
| `DeviceFingerprintService` | class | Fingerprint compute, headless detection | :201-292 |
| `IPAccountLinkageService` | class | IP↔account linkage, `check_ip_multiple_accounts` | :293-365 |
| `GraphAnalysisService` | class | duplicate bank/device/return-abuse graph checks | :366-460 |
| `FraudScoringEngine` | class | `calculate_score` (**~150 LOC**), impossible-travel, velocity, BIN fraud | :461-842 |
| module `__getattr__(name)` | function (**hidden dynamic surface**) | lazy cross-domain model access | :68-74 |

**LOW — `check_ip_multiple_accounts` implemented in 3 classes** (IPAccountLinkageService:325,
GraphAnalysisService:372, FraudScoringEngine:825). Same method name, three implementations — verify
they are intentional overrides vs. accidental duplicates (Phase 13/14).

---

## 9. Accounts / auth — `backend/domains/accounts/services/auth/auth_service.py` (3,795 LOC, 188 symbols) (VERIFIED)
**MEDIUM (maintainability) — auth mega-module.** One file spans: password auth
(`authenticate_password`:390), phone OTP (`request_otp`:498, `authenticate_phone_otp`:515),
biometric (`_enroll_biometric`:570, `authenticate_biometric`:628, `_compare_face_encodings`:719),
kiosk QR (`generate_kiosk_qr`:746, `authenticate_kiosk_qr`:794), SSO/OAuth (`_verify_sso_token`:935,
`authenticate_sso`:1026, Google/Facebook callbacks :2223-2352), session mgmt
(`_issue_session`:1121, `refresh_session`:1245, `logout`:1275), registration
(`register_user`:2353, `verify_email_token`:2516), device fingerprinting/risk
(`_record_device`:292, `_compute_risk_score`:334), rate limiting (`_check_login_rate_limit`:97),
and referral logic. Also embeds ~8 Pydantic request models (:1605-1652). Impact: every auth
mechanism shares one edit surface; high review/security blast radius (deep review in Phase 09).

`backend/domains/accounts/ports.py` (812 LOC, 133 fns): **catch-all** generated read facade exposing
Address, Cart, AuditLog, SupportTicket, VideoRoom, News, chat, OCR, OTP, sessions, SLA (accounts/ports.py:110-640).
Name artifacts (`get_o_c_r_result_by_id`:613, `get_escalation_s_l_a_rule_by_id`:581) confirm generation.
INFO — low cohesion: the "accounts" port owns many unrelated models.

---

## 10. Background jobs & events (VERIFIED)

| Area | Symbol/File | Type | Purpose | Evidence |
|---|---|---|---|---|
| Celery app | backend/jobs/celery_app.py | module | Worker app | jobs listing |
| Periodic tasks | backend/jobs/periodic_tasks.py (9 tasks) | scheduled tasks | Cron-like jobs | census |
| Payout automation | backend/jobs/payout_tasks.py (4), payout_sweep.py (1) | tasks | Async payout sweeps | census |
| Finance crons | accrual_reversal.py, fx_revaluation.py, reconciliation_cron.py, bank_statement_importer.py | tasks | Ledger automation | census |
| Email/AI/ML | email_tasks.py (5), ai_tasks.py (5), ml_worker.py | tasks | Async side effects | census |
| Fraud/threat | fraud_monitoring.py, threat_feed_updater.py, ghost_order_detector.py | jobs | Security automation | census |

**MEDIUM — event subscriber is a no-op stub (VERIFIED).** `backend/infrastructure/events/subscriber.py`
declares `EventSubscriber` whose `start()` and `stop()` are empty (`subscriber.py:14-18`; docstring
"Event subscriber stubs for jobs module"). `create_subscriber(...)` returns this inert object. Impact:
any code relying on this class to consume an event stream does nothing; real event handling (if any)
must occur via other paths (e.g. `FulfillmentService.handle_payment_confirmed` §3.3, `jobs/event_workers.py`).
The working eventing path is **INFERRED**, not confirmed here.

**Money kernel — `backend/kernel/money.py` (VERIFIED, INFO):** 6 pure functions (`to_decimal`,
`round_money`, `to_cents`, `money_to_minor_units`, `from_cents`, `format_currency`, money.py:11-39).
Stateless shared primitive — a high fan-in hub but low risk (no shared mutable state).

---

## 11. Hotspot synthesis (the 9 requested categories)

### 11.1 Extremely large functions (WHY it matters, not just size)
- `create_order` (order_engine.py:726-918, ~193 LOC) — the checkout critical path; touches pricing,
  shipping, inventory, persistence, rollback in one body → hard to test each branch in isolation. **HIGH review value.**
- `get_payment_methods_status` (payment_engine.py:2039-2226, ~188 LOC) — per-country/per-gateway branching;
  correctness directly affects what customers can pay with. **MEDIUM.**
- `run_auto_payout_sweep` / `run_auto_logistics_payout_sweep` (payout_batch_service.py:863,1137, ~270 LOC each)
  — money-moving automation with retry/threading; failure = mispaid suppliers/partners. **HIGH.**
- `FraudScoringEngine.calculate_score` (fraud_detection_service.py:472-621, ~150 LOC) — single scoring
  monolith mixing many signals; a bug silently mis-scores fraud. **MEDIUM.**

### 11.2 Extremely large classes / modules
- `general_ledger_service.py` (7,113 LOC / 260 symbols) — see §5.1. **≥5 fused bounded concerns.** HIGH.
- `orders/services/core/logistics.py` (4,527 LOC / 145) — fulfillment + full logistics-partner suite mis-homed. MEDIUM.
- `auth_service.py` (3,795 / 188) — all auth mechanisms in one file. MEDIUM.
- `payout_batch_service.py` (3,647 / 145) — payouts + embedded PaymentEngine/PayoutEngine/Orchestrator + stubs. HIGH.
- `logistics/services/partners/service.py` (3,000 / 245, mostly thin delegators). MEDIUM.

### 11.3 Highly coupled modules (hubs)
- `orders/ports.py`, `finance/ports.py`, `accounts/ports.py` — sanctioned cross-domain read hubs; large
  fan-in by design (Law 3). Coupling is intentional but concentrates change-risk.
- `payment_engine.py` — imported by health/readiness (main.py:145) and checkout; fan-in hub. VERIFIED main.py:145.
- `kernel/money.py`, `middleware/orchestrator.py` — foundational hubs.

### 11.4 Deep call chains
- **Logistics partner ops: 4 hops** router → partners/service.py → logistics_partner_service.py → orders/core/logistics.py,
  with an **unbound `ctrl`** in hop 3 (§7). WHY it matters: indirection hides a latent NameError and obscures the real owner. HIGH.
- Readiness probe → `_payment_provider_runtime_status` → gateway config resolvers → DB (main.py:145, payment_engine.py:1550). MEDIUM.

### 11.5 Functions with many responsibilities
- `create_order` (validate+price+ship+inventory+persist+rollback), `run_auto_payout_sweep`
  (query+calculate+notify+journal+status), `register_user` (auth_service.py:2353: create+consent+verify+referral). All MEDIUM–HIGH.

### 11.6 Global state
- `rbac/dependencies.py`: `_ROLE_FEATURES`, `_ROLE_MODULES`, `_PUBLIC_FEATURES` dicts + `_current_user_ctx` ContextVar (:15,32-104).
- `providers/payments/registry.py`: `PaymentGatewayRegistry._registry` mutable class dict (:19).
- `main.py`: module-global `app`, lazy `_error_handler` (:57-68).
- `dump.rdb` at repo root + Redis usage imply external shared state (INFO).

### 11.7 Singleton-like state
- `PaymentGatewayRegistry` (class-method registry, mutable, `clear()`/`unregister()` exposed) — mutable global singleton; test isolation risk. registry.py:16-69.
- `websocket_manager.manager` + `BACKGROUND_JOBS_ROOM` (main.py:200) — process-wide connection registry.
- Payout background thread singleton via `start_auto_payout_background_job` (`_loop`, payout_batch_service.py:1525-1571).

### 11.8 Hidden side effects
- `products_service._bump_product_cache_version()` (:881) — global cache invalidation.
- `orders/ports.py.__getattr__` (:1587) & `fraud_detection_service.__getattr__` (:68) — dynamic import on attribute access.
- Import-time RLS install + model registry population (main.py:13,44-56).
- `auth_service` writes device/login-history/referral records as side effects of authentication (:292,2038,1828).

### 11.9 Duplicate implementations (VERIFIED unless noted)
- BOGO discount/eligibility duplicated in two files (§6.3). MEDIUM.
- Coupon `validate_coupon_code`/`validate_coupon` duplicated (§6.3). LOW.
- Payment helper **stubs** shadow real impls (`is_checkout_payment_method_allowed` always-True, etc., §5.2). HIGH.
- Two gateway-registration mechanisms (§4.3). LOW.
- Legacy cart pairs `get_cart`/`get_cart_legacy`, `upsert_cart_item`/`_legacy` (§6.2). LOW.
- `check_ip_multiple_accounts` ×3 classes (§8). LOW.
- Embedded `PaymentEngine`/`PayoutEngine`/`PaymentOrchestratorService` in payouts module duplicating the
  dedicated `payments/` services (§5.2). MEDIUM.

---

## 12. Contradictions register (per MASTER_RULES §10-11)
1. RBAC docstring "merges DB grants + country scope" vs. resolver passing `db_grants=[]`, no country (§2). VERIFIED.
2. `is_checkout_payment_method_allowed`: real country-gated impl vs. always-True stub (§5.2). VERIFIED.
3. Logistics-partner logic said to live in `logistics` domain vs. canonical impl in `orders` domain (§3.3/§7). VERIFIED.
4. `logistics_partner_service.py` calls `ctrl.*` with the import commented out (§7). VERIFIED (binding); runtime failure INFERRED.

## 13. Gaps / NOT DETERMINABLE
- Complete runtime **Called By** graph for each symbol — not exhaustively traced; entries marked INFERRED/UNKNOWN.
- Exact runtime binding/reachability of the unbound-`ctrl` functions — **NOT DETERMINABLE FROM STATIC READ ALONE** (no execution performed).
- hr/comms/country/analytics/audit/governance/suppliers internal symbol maps — census-level only this phase.
- Whether the no-op `EventSubscriber` is wired anywhere live — INFERRED not, not confirmed.

---

### Skepticism self-check
- [x] Opened files and cited real line numbers.
- [x] Separated declared/imported vs. actually used (e.g. commented `ctrl` import; `db_grants=[]`).
- [x] Labelled VERIFIED / INFERRED / UNKNOWN throughout.
- [x] Reported contradictions instead of resolving them (§12).
- [x] Did not infer behavior from names/docs alone (verified bodies for every HIGH finding).
- [x] No secret values reproduced — only names/locations of secret-resolution functions noted.
