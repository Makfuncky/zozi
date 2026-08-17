
-----------------------------------------------------------------------------------
-----------------------------------------------------------------------------------

## The key insight: you have **three orthogonal axes**, not one tree

A folder tree can only physically express **one** axis. The other two must live in **naming + registration + configuration**. Your three axes map cleanly to three different mechanisms:

| Axis | What it is | Where it lives | Mechanism |
|---|---|---|---|
| **Module** (Customer, Supplier, Logistics, Admin, Employee) | *Who* is acting — login, session, route prefix, UI shell | `modules/{module}/` | Separate auth tables + thin API surface |
| **Domain** (Finance, Accounts, Country, HR, Orders, Catalog…) | *What* the business does — logic + data | `domains/{domain}/` | Services, models, schemas, policies, events |
| **Feature** (`finance.reporting`, `finance.ledger`…) | *What may be done* — permission atoms | `domains/{domain}/features.py` aggregated into `rbac/` | Data/config, enforced by `require_feature()` |

The rule that makes it coherent: **Modules compose. Domains own. Features gate.**

---

## The scaffolding hierarchy

```
backend/
├── modules/                            # AXIS 1 — MODULE (who)
│   ├── customer/
│   │   ├── auth/                       # login/OTP/social → customer.accounts; sessions, device binding
│   │   ├── routers/                    # thin /customer/* routers (one service call each)
│   │   └── serializers/                # customer-facing view models (optional)
│   ├── supplier/                       # auth → supplier.supplier_accounts
│   ├── logistics/                      # auth → logistics.logistics_partners
│   ├── admin/                          # auth → admin.admin_accounts
│   └── employee/                       # auth → employee.employees
│
├── domains/                            # AXIS 2 — DOMAIN (what)
│   ├── finance/
│   │   ├── services/                   # treasury_engine, ledger, reporting, payouts
│   │   ├── models/  schemas/  policies/
│   │   ├── events.py  subscribers.py
│   │   └── features.py                 # AXIS 3 seed — this domain's permission atoms
│   ├── accounts/                       # AR/AP sub-ledgers (or fold into finance — team's call)
│   ├── country/  hr/  orders/  catalog/  payments/
│   ├── logistics/  suppliers/  customers/  comms/  media/  risk/
│
├── rbac/                               # AXIS 3 — FEATURE (may)
│   ├── catalog.py                      # aggregates domains/*/features.py → single source of truth
│   ├── roles.py                        # (module, role) → feature sets
│   ├── resolution.py                   # actor × role × country → effective feature set (Redis-cached)
│   └── dependencies.py                 # require_feature("finance.ledger.post")
│
├── infrastructure/                     # platform: database, redis, storage, messaging, security, observability
├── jobs/                               # background consumers; may call domain services
└── main.py
```

> Note on the previous P1 draft: I had placed actor routers *inside* domains (`domains/orders/api/customer_*.py`). Both placements work while routers stay thin — but since **you treat Module as a first-class axis with its own login/session/nav**, `modules/` is the cleaner home. It also gives cross-domain *read composition* (dashboards) a natural place without polluting domains.

---

## The circuit (one request through all three axes)

```
Client
 → modules/admin/auth            (login → JWT with module claim; RLS country set)
 → modules/admin/routers/finance_ledger_router.py
      Depends(require_feature("finance.reporting"))      ← AXIS 3 gate
 → domains/finance/services/reporting_service.py         ← AXIS 2 logic
 → domains/finance/models → infrastructure/database      ← PostgreSQL (RLS-scoped)
```

### Feature atoms: defined once, in the domain

```python
# domains/finance/features.py
FEATURES = {
    "finance.ledger":       {"label": "General Ledger",  "risk": "high",
                             "actions": ["read", "post", "approve"]},
    "finance.reporting":    {"label": "Financial Reports", "risk": "medium",
                             "actions": ["read", "export"]},
    "finance.payouts":      {"label": "Supplier Payouts", "risk": "high",
                             "actions": ["view", "batch", "release"]},
}
```

`rbac/catalog.py` merges every domain's `features.py`; `rbac/roles.py` grants per **(module, role)**:

```python
# rbac/roles.py
ROLE_FEATURES = {
    ("admin",    "admin"):            {"finance.*", "hr.payroll.release", ...},
    ("admin",    "country_finance"):  {"finance.reporting.read", "finance.ledger.read", ...},
    ("employee", "finance_manager"):  {"finance.ledger.post", "finance.reporting.*"},
    ("employee", "employee"):         {"hr.payslip.view", "finance.expenses.submit"},
    ("supplier", "supplier"):         {"finance.payouts.view"},   # own payouts only (scoped in service)
}
```

### The same domain, five modules — the proof it works

```python
# modules/admin/routers/finance_router.py
@router.post("/ledger/journals")          # admin posts journals
async def post_journal(body, ctx=Depends(require_feature("finance.ledger.post")), db=Depends(get_db)):
    return LedgerService(db).post(body, actor=ctx)

# modules/employee/routers/finance_router.py
@router.post("/expenses")                 # employee submits an expense
async def submit_expense(body, ctx=Depends(require_feature("finance.expenses.submit")), db=Depends(get_db)):
    return ExpensesService(db).submit(body, actor=ctx)

# modules/supplier/routers/finance_router.py
@router.get("/payouts")                   # supplier sees OWN payouts
async def my_payouts(ctx=Depends(require_feature("finance.payouts.view")), db=Depends(get_db)):
    return PayoutsService(db).for_supplier(ctx.actor_id)
```

Three logins, three surfaces, **one** `domains/finance`. That is exactly your model.

---

## Migration mapping (from your current tree)

| Today | Becomes |
|---|---|
| `routers/admin_finance.py` (flat) | `modules/admin/routers/finance_router.py` |
| `controllers/finance/admin_cash_controller.py` | thin part → module router; logic → `domains/finance/services/cash_service.py` |
| `services/finance/treasury_engine.py` | `domains/finance/services/treasury_engine.py` |
| `models/finance.py` | `domains/finance/models/*` |
| `db/schemas.py` (finance slice) | `domains/finance/schemas/*` |
| `ADMIN_PERMISSION_MAP` / `shared/adminPermissions.ts` | **deleted** — replaced by the served `rbac` catalog (frontend nav + backend gates consume the same source) |
| login/session code | `modules/{m}/auth/` + primitives in `infrastructure/security/` |

---

## The five laws that keep it sane

1. **Arrows point down:** `modules → domains → infrastructure`. Domains never import modules. `rbac` is imported by modules and middleware only — domains enforce *policies*, not permissions.
2. **Module routers stay thin:** auth context + `require_feature(...)` + one domain-service call. No DB writes, no business rules.
3. **Cross-domain writes only via events** (`events.py`/`subscribers.py`). Cross-domain *reads* allowed only in designated read services (e.g., `domains/governance/services/command_center_read_service.py`).
4. **Feature strings are single-sourced** in `domains/*/features.py`; a CI test fails on any `require_feature("...")` literal not present in the catalog.
5. **Country is the fourth, orthogonal axis:** feature check (may) × RLS country (where) are independent gates — `country_staff_assignments` scopes *which* features a role holds *in which* country.

This gives every concept you named exactly one home: **Module = folder, Domain = folder, Feature = data** — and the three never bleed into each other.

-----------------------------------------------------------------------------------
-----------------------------------------------------------------------------------

## RBAC = **Role-Based Access Control**

In plain words: instead of giving permissions to *people*, you give permissions to **roles** (`admin`, `country_finance`, `finance_manager`, `supplier`…), and people *inherit* whatever their role holds. Grant/revoke then becomes "change the role," not "edit 500 users."

In your 3-axis model, `rbac/` is the home of the **Feature axis** — it owns the permission catalog, the role→feature mappings, and the "can this user do this?" decision logic. It is **configuration + decision logic**, not business logic.

> Your system is already RBAC in practice — `role_permission_assignments`, `user_permission_overrides`, `employee_roles`, `DEFAULT_ROLE_PERMISSION_MAP`, `require_finance_permission` — it's just scattered. `rbac/` gives those pieces one first-class home.

---

## What goes inside `rbac/`

```
backend/rbac/
├── __init__.py
├── catalog.py        # THE feature registry — single source of truth
├── roles.py          # (module, role) → default feature sets
├── resolution.py     # actor × role × country → effective feature set (cached)
├── dependencies.py   # FastAPI gates: require_feature(...), require_module(...)
├── service.py        # admin CRUD: grant/revoke, delegation, maker-checker
└── models.py         # (optional) ORM for permission tables*
```

### 1. `catalog.py` — the feature atoms
Aggregates every domain's `features.py` so a feature string can never be invented in a router:
```python
from domains.finance.features import FEATURES as FINANCE
from domains.hr.features       import FEATURES as HR
# ...
FEATURE_CATALOG = {**FINANCE, **HR}          # {"finance.ledger": {...}, "hr.payroll": {...}}

def is_known(feature: str) -> bool: ...
def all_features() -> list[str]: ...
```

### 2. `roles.py` — role → features per module
Replaces `DEFAULT_ROLE_PERMISSION_MAP` / `ADMIN_PERMISSION_MAP`:
```python
ROLE_FEATURES: dict[tuple[str, str], set[str]] = {
    ("admin",    "admin"):           {"*"},
    ("admin",    "country_finance"): {"finance.reporting.read", "finance.ledger.read"},
    ("employee", "finance_manager"): {"finance.ledger.post", "finance.reporting.*"},
    ("employee", "employee"):        {"hr.payslip.view", "finance.expenses.submit"},
    ("supplier", "supplier"):        {"finance.payouts.view"},   # own payouts only
}
```

### 3. `resolution.py` — the actual decision
Merges defaults + DB grants + per-user overrides + country scope, cached in Redis:
```python
def effective_features(user, module: str, country: str, db) -> set[str]:
    feats  = set(ROLE_FEATURES.get((module, user.role), set()))
    feats |= role_db_grants(user.role, country, db)      # role_permission_assignments
    feats  = apply_overrides(feats, user.id, country, db) # user_permission_overrides
    return expand_wildcards(feats, FEATURE_CATALOG)
```

### 4. `dependencies.py` — the gates routers use
```python
def require_feature(feature: str):
    def dep(ctx=Depends(get_auth_context), db=Depends(get_db)):
        if feature not in effective_features(ctx.user, ctx.module, ctx.country, db):
            raise HTTPException(403, f"Missing feature: {feature}")
        return ctx
    return dep
```

### 5. `service.py` — admin-facing RBAC operations
Your existing `RBACService` (delegation workflows, approval chains) moves here: grant/revoke, temporary grants with `expires_at`, maker-checker for sensitive grants, audit logging.

### 6. `models.py`* — the permission tables
`permission_categories`, `role_permission_assignments`, `user_permission_overrides` can live here (self-contained) **or** in `domains/governance/models/` if you prefer every ORM model inside a domain. Either is fine — pick one and document it.

---

## What does **NOT** go in `rbac/`

| Thing | Correct home |
|---|---|
| HTTP endpoints for managing roles | `modules/admin/routers/rbac_router.py` (calls `rbac/service.py`) |
| Login / sessions / JWT | `modules/{m}/auth/` + `infrastructure/security/` |
| Business rules (e.g., "payout needs 2 approvals") | `domains/*/policies/` |
| Feature definitions themselves | `domains/*/features.py` (rbac only aggregates) |

---

## Migration mapping (your current code → rbac/)

| Today | Becomes |
|---|---|
| `utils/staff_permissions.py` (`DEFAULT_ROLE_PERMISSION_MAP`) | `rbac/roles.py` |
| `services/rbac_service.py` (`RBACService`) | `rbac/service.py` |
| `require_finance_permission`, `require_admin`, `hasAdminPermission` | `rbac/dependencies.py` |
| `shared/adminPermissions.ts` (hardcoded frontend map) | deleted → frontend fetches `GET /rbac/catalog` so **UI gating and backend gating share one source** |

One-line summary: **`rbac/` answers exactly one question — "may this actor, in this module, in this country, perform this feature?" — and nothing else.**

-----------------------------------------------------------------------------------
-----------------------------------------------------------------------------------


# Zozi Platform — Final Scaffolding Hierarchy

This is the definitive tree. It encodes all three axes (**Module** = `modules/`, **Domain** = `domains/`, **Feature** = `rbac/` + `domains/*/features.py`), the platform layer, the strangler shims for legacy code, and the full monorepo (backend + web + mobile + shared).

---

## 1 · Backend (the core decision)

```
backend/
├── main.py                          # boots app; registers module routers per actor prefix;
│                                    #   imports domains (models) + subscribers (event bus)
├── config.py                        # settings, env, feature gates
├── DOMAIN_ALLOWLIST.yaml            # strangler debt: temporary cross-domain imports (may only shrink)
│
├── modules/                         # AXIS 1 — MODULE (who acts: login + thin API surface)
│   ├── customer/
│   │   ├── auth/                    # login/OTP/social → customer.accounts; sessions; device binding
│   │   ├── routers/                 # thin /customer/* : catalog_router, checkout_router, tracking_router, wishlist_router
│   │   └── serializers/             # customer-facing view models (optional)
│   ├── supplier/
│   │   ├── auth/                    # → supplier.supplier_accounts
│   │   └── routers/                 # onboarding_router, products_router, orders_router, payouts_router, finance_router
│   ├── logistics/
│   │   ├── auth/                    # → logistics.logistics_partners
│   │   └── routers/                 # pickups_router, shipments_router, settlements_router, cod_remittance_router
│   ├── admin/
│   │   ├── auth/                    # → admin.admin_accounts; MFA/TOTP
│   │   └── routers/                 # finance_ledger_router, finance_reports_router, orders_router,
│   │                                #   hierarchy_router, rbac_router, command_center_router, country_router, moderation_router
│   └── employee/
│       ├── auth/                    # → employee.employees; QR-kiosk + biometric login
│       └── routers/                 # ess_router (payslip/leave/expenses), comms_router, attendance_router
│
├── domains/                         # AXIS 2 — DOMAIN (what the business does; owns logic + data)
│   ├── finance/                     # ← shown FULLY expanded; every domain has this internal layout
│   │   ├── services/                # treasury_engine.py, ledger_service.py, reporting_service.py,
│   │   │                            #   payouts_service.py, vat_service.py, cash_forecast_service.py
│   │   ├── models/                  # accounts.py, journal_entries.py, pending_journal_entries.py,
│   │   │                            #   payout_batches.py, vat_remittances.py, cash_position_snapshots.py,
│   │   │                            #   partner_bank_accounts.py   # unified supplier/logistics/employee banking
│   │   ├── schemas/                 # Pydantic DTOs (finance slice of legacy db/schemas.py)
│   │   ├── repositories/            # (optional) hot-path data access: keyset cursors, replica reads
│   │   ├── policies/                # pure rules: approval thresholds, period-close lock, maker-checker
│   │   ├── events.py                # PayoutReleased, JournalPosted, FxRevalued …
│   │   ├── subscribers.py           # consumes OrderSettled, RefundApproved …
│   │   ├── features.py              # AXIS 3 seed: finance.ledger, finance.reporting, finance.treasury, finance.payouts …
│   │   └── __init__.py
│   ├── accounts/                    # invoices.py, invoice_items.py, ap_ledger_entries.py, ar_ledger_entries.py,
│   │                                #   bank_transactions.py, transaction_ledgers.py; reconciliation_service.py
│   ├── catalog/                     # products.py, product_variants.py, categories.py, coupons.py, reviews.py,
│   │                                #   product_filter_metadata.py; product_upload_service.py, moderation_service.py
│   ├── orders/                      # orders.py, order_items.py, carts.py, return_requests.py, supplier_disputes.py;
│   │                                #   checkout_service.py, order_lifecycle_service.py, returns_service.py
│   ├── payments/                    # payment_webhook_events.py, gateway_settlement_schedules.py,
│   │                                #   payment_gateway_connections.py, credit_card_bins.py; payment_orchestrator.py
│   ├── logistics/                   # logistics_partners.py, shipments.py, shipment_confirmations.py,
│   │                                #   parcel_location_trackers.py, logistics_settlements.py, city_distance_matrix.py;
│   │                                #   allocation_service.py, tracking_service.py, sla_service.py
│   ├── suppliers/                   # supplier_profiles.py, supplier_documents.py, supplier_kyc_requirements.py;
│   │                                #   onboarding_service.py, kyc_service.py
│   ├── customers/                   # addresses.py, referrals.py, badge_tiers.py, wishlists.py; profile_service.py
│   ├── hr/                          # employees.py, org_units.py, employee_attendance.py, employee_shift_rosters.py,
│   │                                #   employee_leave_requests.py, employee_biometrics.py, physical_id_cards.py;
│   │                                #   payroll_service.py, hierarchy_service.py, performance_service.py
│   ├── comms/                       # internal_channels.py, direct_chat_rooms.py, group_chat_rooms.py,
│   │                                #   country_communications.py, notifications.py, escalation_sla_rules.py;
│   │                                #   chat_service.py, internal_email_service.py, escalation_service.py
│   ├── media/                       # media_assets.py, product_videos.py, video_rooms.py, video_room_recordings.py,
│   │                                #   video_analytics.py, ai_upload_jobs.py; image_pipeline_service.py (rembg/BiRefNet)
│   ├── country/                     # country_configs.py, country_config_versions.py, country_cities.py,
│   │                                #   country_category_tax_rates.py, country_staff_assignments.py; country_sync_service.py
│   └── governance/                  # audit_logs.py, fraud_events.py, fraud_scoring_logs.py, manual_review_queue.py,
│                                    #   executive_news.py, system_health_events.py; command_center_service.py, fraud_service.py
│
├── rbac/                            # AXIS 3 — FEATURE (what may be done)
│   ├── catalog.py                   # aggregates domains/*/features.py → single source of truth
│   ├── roles.py                     # (module, role) → feature sets  [replaces DEFAULT_ROLE_PERMISSION_MAP]
│   ├── resolution.py                # actor × role × country → effective set (Redis-cached)
│   ├── dependencies.py              # require_feature(...), require_module(...)
│   ├── service.py                   # grant/revoke, delegation, maker-checker  [was services/rbac_service.py]
│   └── models.py                    # permission_categories, role_permission_assignments, user_permission_overrides
│
├── infrastructure/                  # PLATFORM — zero business logic; imports nothing above it
│   ├── database/                    # base.py, database.py (get_db/get_read_db), session.py, transaction.py,
│   │                                #   security.py  ← ONE canonical RLS enforcer, seeds/, create_tables.py (dev-only)
│   ├── redis/                       # client.py, cache, token blacklist, pub/sub
│   ├── storage/                     # S3/R2 adapters, presigned URLs (media blobs never in Postgres)
│   ├── messaging/                   # event_bus.py (in-proc → Redis/Celery later), ws_manager.py, webhook ingress
│   ├── observability/               # structlog, OTEL, Prometheus, Sentry
│   ├── security/                    # JWT, hashing, field encryption (KMS), zero-trust primitives
│   └── utils/                       # money.py, pagination.py, datetime_utils.py, variant_key.py (pure helpers only)
│
├── providers/                       # 3rd-party/AI adapters; called ONLY by services/ and jobs/
│   ├── ai/  analytics/  auth/  automation/  comms/  finance/  geography/
│   ├── image/  media/  news/  payments/  security/  voice/  legacy/
│   └── _base.py                     # BaseProvider / BaseAIProvider + health_check()
│
├── jobs/                            # background workers/consumers (heavy/AI/off-request only)
│   ├── fraud_monitoring.py  ghost_order_detector.py  data_retention.py
│   ├── payroll_run.py  payout_sweep.py  reconciliation_cron.py  bank_statement_importer.py
│   ├── fx_revaluation.py  accrual_reversal.py  threat_feed_updater.py  mcp_server.py
│   └── background_tasks.py
│
├── middleware/                      # flat; orchestrator.py orders the pipeline BEFORE module routers
│   ├── orchestrator.py
│   └── api_version · country_context · csrf · database_security · device_binding · impossible_travel ·
│       ip_extraction · logging · pci_dss_compliance · rate_limit · request_id · rls_dependency ·
│       security_headers · webhook_ip_whitelist · webhook_verification · zero_trust_auth
│
├── alembic/                         # SINGLE schema source of truth (env.py, versions/, alembic.ini)
├── scripts/                         # analyze_tables.py, rewrite_imports.py, seed helpers (dev)
├── tests/
│   ├── architecture/                # test_import_laws.py (layer direction + cross-domain ban), test_feature_catalog.py
│   └── domains/                     # per-domain unit/integration tests
│
└── _legacy/                         # DEPRECATED strangler shims (re-export only; delete when domain slice is 100% ready)
    ├── routers/  controllers/  services/  models/  db/  utils/
```

---

## 2 · Frontend + Shared + Root (unchanged circuits, aligned naming)

```
frontend/
├── web_app/                         # Next.js 15
│   ├── src/app/                     # route tree: (customer), auth/, admin/*, supplier/*, logistics-partner/*,
│   │                                #   employee/*, wishlist/, profile/, chatbot/, tracking/; app/api/ = Next server routes
│   ├── src/components/              # ui/ (design system), admin/, auth/, chat/, comms/, country/, ems/, map/, supplier/
│   ├── src/hooks/                   # useApi, useAuth, WebSocket hooks
│   ├── src/lib/                     # api/ (client.ts, auth.ts, country.ts, errors.ts), rbac.ts (fetches /rbac/catalog)
│   ├── src/services/                # localizationService, crossBorderService, addressFormatService
│   ├── src/theme/  src/styles/      # design tokens → Tailwind (NO inline <style>)
│   ├── src/types/  src/utils/
│   ├── tests/  e2e/                 # mocks + Playwright
│   └── root/                        # next.config.ts (rewrites), middleware.ts, tailwind.config, playwright.config
│
├── mobile_app/                      # Expo RN
│   ├── app/                         # Expo Router: (auth)/(tabs) + admin/ supplier/ logistics/ employee/ tracking/ returns/
│   ├── components/ui/               # design-system
│   ├── lib/                         # api.ts, Zustand stores, authPrompt, countryContext, geo, paymentService,
│   │                                #   expoSecureStorage, errorReporter
│   ├── theme/  assets/  android/  mocks/  e2e/  scripts/
│   └── root/                        # app.config.js, metro.config, babel.config, sentry, pnpm-workspace
│
└── shared/                          # cross-platform TS, imported by BOTH apps
    └── src/                         # api-core.ts (apiFetch), money.ts, i18n.ts, cart/checkout/order/product/returns/
                                     #   wishlist/notification helpers, statusColors.ts, requestCache.ts, realtime.ts,
                                     #   chatbot.ts, types.ts, theme.ts + theme.native.ts,
                                     #   permissions.ts  ← GENERATED from backend /rbac/catalog (replaces adminPermissions.ts)

root/
├── docker-compose.yml  Makefile  pnpm-workspace.yaml
├── .github/workflows/               # ci.yml · import-lint.yml · schema-drift.yml (alembic check) · e2e.yml
└── _extra_files/                    # temporary audit/migration working files
```

---

## 3 · The laws that keep it final

1. **Arrows point down only:** `modules → domains → infrastructure`; `jobs → domains → infrastructure`; `providers ← services/jobs`; `middleware → infrastructure`. Domains never import modules; infrastructure imports nothing above it.
2. **Module routers stay thin:** auth context + `require_feature(...)` + one domain-service call. No DB writes, no business rules.
3. **Cross-domain writes only via events** (`events.py`/`subscribers.py`). Cross-domain reads only in designated read services (e.g., `governance/services/command_center_service.py`).
4. **Features single-sourced:** defined only in `domains/*/features.py`; aggregated by `rbac/catalog.py`; CI fails on any `require_feature("…")` literal not in the catalog; frontend gating consumes the same catalog.
5. **Country is the orthogonal scope axis:** RLS session context + `country_staff_assignments` — independent of the feature check.
6. **Schema discipline:** every table in a domain Postgres schema; Alembic is the only schema source (`create_all` dev-only); naming lint (`snake_case`, plural, `<thing>_id`, `created_at/updated_at`, `country_code`, `is_deleted`).
7. **Strangler rule:** `_legacy/` shims re-export only; a shim is deleted when its domain slice is auto-generation-ready and tests green; `DOMAIN_ALLOWLIST.yaml` may only shrink.

---

## 4 · Legacy → final mapping (one glance)

| Legacy | Final home |
|---|---|
| `routers/admin_finance.py` | `modules/admin/routers/finance_*_router.py` |
| `controllers/finance/admin_cash_controller.py` | thin → module router; logic → `domains/finance/services/` |
| `services/finance/treasury_engine.py` | `domains/finance/services/treasury_engine.py` |
| `models/finance.py` | `domains/finance/models/*` |
| `db/schemas.py` | split → `domains/*/schemas/` |
| `db/database.py` | `infrastructure/database/database.py` (+ `security.py` = single RLS enforcer) |
| `services/rbac_service.py`, `utils/staff_permissions.py` | `rbac/service.py`, `rbac/roles.py` |
| `shared/adminPermissions.ts` | `shared/src/permissions.ts` (generated from `/rbac/catalog`) |

This is the end state: **Module = folder, Domain = folder, Feature = data** — every concept has exactly one home, and the dependency laws make the structure enforce itself.


-----------------------------------------------------------------------------------
-----------------------------------------------------------------------------------

Good questions — these are exactly the seams where a restructure either holds or collapses. Here's the precise answer for each.

---

## 1 · Controllers: not "merged into services" — **split by what they actually do**

The `controllers/` layer is **abolished**, but its code goes to two different homes depending on its nature:

| What the controller code does | New home |
|---|---|
| Route declaration, request validation, auth wiring, response shaping | `modules/{module}/routers/{domain}_router.py` (thin) |
| Orchestration / business logic / (the illegal DB writes you have in `core/ai_controller.py`, `treasury/cash_management_write_controller.py`) | `domains/{domain}/services/` |

Why no controller layer at all? Because once you have:
- **thin module routers** (auth via `require_feature(...)` deps), and
- **rich domain services** (orchestration + transactions),

…a middle "controller" layer is pure indirection with no resident logic. Your own P1 doc already admitted the target was "controllers orchestrate only, never import FastAPI" — and half of them violated it. Absorbing them removes the ambiguity permanently.

**The auto-router generator survives**, just retargeted: instead of controllers emitting thin routers into flat `routers/`, the generator now emits thin routers into `modules/{module}/routers/` from the domain's route contract (service method signatures), still carrying the `AUTO-GENERATED` marker. Legacy `controllers/` lives in `_legacy/` as re-export shims until each slice is migrated.

---

## 2 · Models: ORM-only, and **yes — flat inside each domain**

**What goes in `domains/{d}/models/`:**
- SQLAlchemy declarative classes (tables, columns, relationships, indexes, `__table_args__` with the Postgres schema)
- Shared mixins if domain-specific (otherwise mixins come from `infrastructure/database/base.py`)

**What must NOT go there:** Pydantic DTOs (→ `schemas/`), business rules (→ `policies/`/`services/`), serialization helpers (→ module `serializers/`), the `Base`/metadata (→ `infrastructure/database/base.py`).

**Flat or nested?** Flat *within the domain*, grouped by file, not by folder:

```
domains/finance/models/          # flat — 5 files, no subfolders
├── ledger.py        # Account, AccountGroup, JournalEntry, JournalEntryLine, PendingJournalEntry
├── payouts.py       # PayoutBatch, PayoutBatchItem, Payout
├── banking.py       # PartnerBankAccount
├── tax.py           # VatRemittance
└── snapshots.py     # CashPositionSnapshot
```

Rule of thumb: **one file per entity aggregate** (not one-per-table, not deep nesting). The domain folder already provides the grouping that the old top-level `models/{domain}/` subfolders used to give you — so inside a domain, subfolders are redundant. Only if a domain exceeds ~15 model files (finance/comms/hr could) may you add 2–3 subfolders; never a single global flat `models/` for everything — that recreates the 377-fan-in blob.

---

## 3 · Routers: they didn't vanish — they were **re-homed per actor (module)**

- The 224 flat files in `routers/` are **split by actor** into `modules/{customer,supplier,logistics,admin,employee}/routers/`.
- Each stays thin: accept → validate → `require_feature(...)` → one domain-service call → return.
- **Public/webhook routers keep the same pattern as today**: a router file may expose `router` (authed) and `public_router` (payment/email webhooks); `main.py` mounts both.
- The old `router_names` import list in `main.py` is replaced by per-module discovery:

```python
# main.py
for m in ["customer", "supplier", "logistics", "admin", "employee"]:
    pkg = importlib.import_module(f"modules.{m}.routers")
    for r in pkg.routers:          # each modules/{m}/routers/__init__.py lists its routers
        app.include_router(r, prefix=f"/api/{m}")
    for r in getattr(pkg, "public_routers", []):
        app.include_router(r, prefix=f"/api/{m}")
```

- Legacy `routers/` (with its `.bak` corpses) sits in `_legacy/` as shims; a shim is deleted when its slice is auto-generation-ready and tests green.

---

## 4 · Registering a new domain / feature: **deliberately trivial**

The design goal was: adding a domain or feature touches **2–3 files and zero central registries** (except role grants). Discovery is automatic.

**New feature in an existing domain** (e.g., `finance.budgets`):
1. Add the atom to `domains/finance/features.py`.
2. Use it: `Depends(require_feature("finance.budgets.read"))` in a module router.
3. Grant it: `rbac/roles.py` default, or DB `role_permission_assignments` via admin UI.

**New domain** (e.g., `loyalty`):
1. Create `domains/loyalty/` with the standard skeleton (`services/ models/ schemas/ policies/ events.py subscribers.py features.py`).
2. Add models → one Alembic migration.
3. Add module routers where the surface is needed (`modules/customer/routers/loyalty_router.py`) — picked up by the per-module `routers` list.
4. Done. No `main.py` edits (module discovery loops modules, not domains), no catalog edits.

**Why it's safe to be this automatic** — the catalog aggregates by package scan, and CI closes the gap:

```python
# rbac/catalog.py — auto-discovers every domain's features
import importlib, pkgutil
import domains

FEATURE_CATALOG = {}
for m in pkgutil.iter_modules(domains.__path__):
    try:
        feat = importlib.import_module(f"domains.{m.name}.features")
    except ModuleNotFoundError:
        continue
    FEATURE_CATALOG.update(getattr(feat, "FEATURES", {}))
```

plus a CI test that fails on any `require_feature("…")` literal not present in `FEATURE_CATALOG`. So forgetting to register a feature **fails the build**, never production.

---

**One-line summary:** controllers were split (shell → module routers, logic → domain services); models are ORM-only and flat per domain; routers were re-homed per actor with auto-discovery; and new domains/features register themselves via package scan + CI guard, so growth stays cheap and governed.

-----------------------------------------------------------------------------------
-----------------------------------------------------------------------------------

Yes. After looking at the current `PROJECT_SCAFFOLDING.md` and the architecture material around it, my recommendation is **not to split Admin, Employee, Supplier, Customer, and Logistic Partner into separate servers at this stage**.

The stronger architecture for ZOZI is:

> **Module-separated + domain-separated + independently deployable later, but initially deployed as a modular monolith.**

The scaffolding already contains a large domain ecosystem—finance/treasury, logistics, catalog, orders, supplier, HR, communications, AI, geography, etc.—and also explicitly has surface-oriented router organization. 

### Recommended structure

```text
ZOZI
│
├── modules/                    # WHO is accessing the system
│   ├── admin/
│   ├── employee/
│   ├── supplier/
│   ├── customer/
│   └── logistics/
│
├── domains/                    # WHAT business capability is being used
│   ├── identity/
│   ├── commerce/
│   ├── catalog/
│   ├── orders/
│   ├── finance/
│   ├── treasury/
│   ├── logistics/
│   ├── supplier/
│   ├── customer/
│   ├── hr/
│   ├── payments/
│   ├── communication/
│   ├── media/
│   └── ai/
│
├── infrastructure/
│   ├── database/
│   ├── redis/
│   ├── security/
│   ├── messaging/
│   └── observability/
│
└── gateway/
```

This matches the important distinction from the architecture discussion: **modules represent access surfaces/actors; domains represent business capabilities.** The same finance capability, for example, can legitimately be exposed through admin, employee, and supplier surfaces without duplicating the finance domain. 

### Why I prefer this

* **Admin ≠ business domain.**
* **Supplier ≠ business domain.**
* **Customer ≠ business domain.**
* **Employee ≠ business domain.**
* They are primarily **security/access/API surfaces**.
* Finance, Orders, Catalog, Logistics, Payments, etc. are the actual **business domains**.
* This avoids duplicating business logic.
* It allows one domain service to serve multiple modules.
* It makes RBAC/feature permissions much cleaner.
* It keeps the database model coherent.
* It makes future service extraction possible.

### Most importantly: don't confuse module separation with server separation

You can have:

```text
                  ┌───────────────┐
Admin ───────────►│               │
Employee ────────►│               │
Supplier ────────►│ ZOZI Backend  │
Customer ────────►│               │
Logistics ───────►│               │
                  └───────┬───────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
           Finance      Orders     Logistics
              │           │           │
              └───────────┼───────────┘
                          ▼
                      PostgreSQL
```

Then later, if actual traffic demonstrates a need:

```text
Gateway
   │
   ├── Customer API ───────► Customer service
   ├── Supplier API ───────► Supplier service
   ├── Logistics API ──────► Logistics service
   ├── Admin API ──────────► Admin service
   └── Employee API ───────► Employee service
```

You can extract them **without redesigning the business domains**, because the boundaries already exist.

### One thing I would change in the current project

Your audit report is already detecting files that cross multiple domains—for example services/providers containing signals from several domains. 

That is more important than creating five servers.

I would enforce:

```text
modules
   ↓
domains
   ↓
infrastructure
```

and **never**:

```text
domain → module
domain → another module
infrastructure → module
```

The existing architecture discussion already defines this direction as one of the core laws. 

### My final recommendation

**Do this now:**

* ✅ Separate `admin`, `employee`, `supplier`, `customer`, `logistics` as **modules**
* ✅ Separate Finance, Orders, Catalog, Logistics, Payments, etc. as **domains**
* ✅ Give each module its own routers/auth/RBAC/navigation
* ✅ Keep domain services/models independent of modules
* ✅ Keep one PostgreSQL ecosystem initially
* ✅ Keep Redis shared initially
* ✅ Deploy the backend as a modular monolith initially
* ✅ Make domains independently testable
* ✅ Enforce dependency boundaries automatically with your architecture auditor
* ✅ Design deployment boundaries so high-load domains can later become services
* ❌ Don't buy five servers just because there are five user types
* ❌ Don't duplicate finance/order/catalog logic into each module
* ❌ Don't create microservices before actual workload justifies them

**In short:** I would make ZOZI **modular now, microservice-capable later**. That gives you the scalability path without paying the operational complexity of five independent servers from day one.


-----------------------------------------------------------------------------------
-----------------------------------------------------------------------------------

Yes — but as **refinements inside the same skeleton**, not a new topology. The three-axis shape (Module / Domain / Feature) is right; what can be better is the *internal anatomy* of domains and the *seams* between them. Five targeted upgrades:

---

## 1 · Vertical slices inside **heavy** domains (layered inside small ones)

Layering *inside* a domain (`services/ models/ schemas/`) recreates the old problem at a smaller scale once a domain gets big (finance ≈ 35 tables, orders, logistics, hr, comms). Fix: **slice by sub-capability when a domain crosses a threshold; stay flat below it.**

Rule of thumb: **> ~8 services or > ~12 tables → slice. Otherwise flat.**

```
domains/finance/                     # HEAVY → vertical slices
├── ledger/                          # one sub-capability = one folder
│   ├── service.py  models.py  schemas.py  policies.py  features.py
├── payouts/
├── treasury/
├── reporting/
├── tax/
├── ports.py                         # (see #2)
├── events.py  subscribers.py
└── __init__.py

domains/country/                     # SMALL → keep flat
├── services/  models/  schemas/  features.py  events.py
```

The `rbac` catalog scanner just walks both depths (`domains/*/features.py` + `domains/*/*/features.py`). This keeps finance navigable without forcing 13 domains into a ceremony they don't need.

## 2 · `ports.py` — the sanctioned cross-domain read path

Sharpen the dependency law from "allowlist YAML" to a structural rule:

- **Writes across domains → events only** (unchanged).
- **Reads across domains → the publishing domain's `ports.py` only.**

```python
# domains/catalog/ports.py  — the ONLY thing orders/ may import from catalog
def get_price(db, product_id, country) -> Money: ...
def get_stock(db, variant_id) -> int: ...
```

CI rule: `from domains.X.(services|models|repositories)` outside `domains/X` = **build failure**; `from domains.X.ports` and `from domains.X.events` = allowed. The YAML allowlist then only tracks *legacy* debt and shrinks to zero.

## 3 · Read-model layer (CQRS-lite) for dashboards

Command Center, admin analytics, supplier comparisons all do cross-domain JOINs. Don't let them pollute domain services. Give each domain a `read_models/` for its own projections, and put cross-domain dashboards in `governance/read_models/`:

```
domains/finance/read_models/treasury_dashboard.py   # uses get_read_db(), materialized views
domains/governance/read_models/command_center.py    # composes other domains' read models
```

Domain services stay write-optimized and event-pure; dashboards stay read-optimized. This is the structural home for the "materialized views" rule you already adopted.

## 4 · A real **shared kernel**, separate from technical utils

`infrastructure/utils/` is for *technical* helpers (pagination, slugs). But Money, currency conversion, fiscal periods, country-code typing, and the **unified reference-numbering service** (ORD-/INV-/PAY-/BATCH-) are *business* primitives used by every domain. Give them a first-class home so they're not smuggled into utils or duplicated per domain:

```
backend/kernel/
├── money.py        # Decimal money, currency conversion (NEVER float)
├── numbering.py    # centralized, configurable reference numbering
├── country.py      # CountryCode type + RLS session-context helper
└── period.py       # fiscal period / date-range logic
```

Import direction: `domains → kernel → (nothing)`.

## 5 · Enforce domain ↔ Postgres schema 1:1

You already committed to bounded-context DB schemas. Make it structural and CI-checked:

- Every model declares `__table_args__ = {"schema": "<domain>"}` (slice tables use the parent domain's schema).
- CI test asserts schema name == owning domain name, `country_code` present on business tables, and naming conventions (plural snake_case, `<thing>_id`, `created_at/updated_at`).

---

## The refined anatomy at a glance

```
backend/
├── modules/        # unchanged (auth + thin actor routers)
├── domains/        # flat inside small domains, sliced inside heavy ones
│   └── {d}/[slice/] {service,models,schemas,policies,features}.py
│   └── {d}/ ports.py · events.py · subscribers.py · read_models/
├── rbac/           # unchanged (catalog auto-scans both depths)
├── kernel/         # NEW: money, numbering, country, period
├── infrastructure/ # unchanged (+ optional: fold middleware/ in here)
├── providers/  jobs/  alembic/  scripts/  tests/  _legacy/
```

**What I would NOT change:** the three axes, `modules/` as the composition layer, event-bus-first integration, the strangler `_legacy/` path, and no microservice extraction until a measured trigger appears. The skeleton was the hard decision — these five just make the inside of it age well.

-----------------------------------------------------------------------------------
-----------------------------------------------------------------------------------
I've now read the target spec (`documents/NEW_STRUCTURE.md`), the boot/router logic (`main.py`, `lifespan.py`, `auto_router.py`), the real backend tree, import patterns, the existing CI gates, the prior audit artifacts, and both frontend packages. Here is a grounded, step-by-step implementation plan.

---

# Implementation Plan — Converting the codebase to `documents/NEW_STRUCTURE.md`

## 0 · Reality check (what the spec says vs. what the code actually is)

**What the spec prescribes:** three orthogonal axes — `modules/` (who: customer/supplier/logistics/admin/employee), `domains/` (what: finance/accounts/catalog/orders/payments/logistics/suppliers/customers/hr/comms/media/country/governance), `rbac/` + `domains/*/features.py` (may). Plus refinements: `kernel/` (money/numbering/country/period), `ports.py` (sanctioned cross-domain reads), `read_models/`, vertical slices for heavy domains, and `_legacy/` shims. Seven laws enforce it (`modules → domains → infrastructure`, thin module routers, events-only cross-domain writes, single-sourced features, country as 4th axis, schema discipline, strangler rule).

**What the code actually is (verified):**
- `routers/` = **223 flat files at root + `generated/auto_router.py`**. These 223 are *generated thin delegators* (AUTO-GENERATED marker). They are NOT the source of truth.
- `controllers/` = **371 files**, named `{surface}_{domain}_{feature}_controller.py` (e.g. `customer_coupons_create_controller.py`, `admin_cash.py`). They declare routes via `@get/@post/...` imported from `routers.generated.auto_router` and call `services.{surface}.{feature}_service`. **Controllers are the real route source; routers are emitted from them.**
- `services/` = 575 files in domain subfolders (`admin` 45, `core` 68, `commerce` 25, `comms` 44, `finance` 39, `treasury` 28, `supplier` 28, `logistics` 26, `catalog` 17, `orders` 18, `hr` 33, `geography` 37, `security` 32, `ai` 16, `gateways` 11, `common` 19...).
- `models/` = **27 flat files** (`finance.py`, `orders.py`, `products.py`, `suppliers.py`, `countries.py`...) + a few subfolders.
- `db/` = `base.py`, `database.py`, `schemas.py` (**2227 lines of Pydantic DTOs to split**), `seed.py`, `treasury_seeder.py`, `session.py`, `transaction.py`, `create_tables.py`.
- `utils/` = 67 flat files (to split into `infrastructure/*` + `kernel/`).
- `providers/` 15 subfolders, `middleware/` 19, `jobs/` 7, `alembic/` 37, `tests/` 102.
- Import fan-in (the real risk): **`from models import` (flat) = 1027**, `from services.` = 1657, `from controllers.` = 399, `from models.` = 338.
- **Boot anchors that must keep working:** `import models` (registers ORM), `services.admin.permissions_service`, `services.unknown._registry`, `services.gateways.payments._event_publisher` + `events.PaymentConfirmedEvent` + `services.orders.fulfillment_service`, `db.treasury_seeder`, `db.seed`, and `main.py`'s imports of `middleware.orchestrator`, `utils.*`, `db.*`, `routers.public_comms_status`, `routers.logistics_partner_verify`, `routers.core_countries_routes`.
- **Already-built tooling to reuse, not rebuild:** `.github/workflows/architecture-gate.yml` (runs `scripts/coherence_gate.py --check`, `tests/test_architecture_gates.py`, `auto_router.py --verify`, forbidden-folder-scan), `router-generation.yml`, `schema-audit.yml`, `backend/pyproject.toml`. Prior audit artifacts exist: `MODELS_SERVICES_CONTROLLERS_MAP.md` (1475 lines: controller→service→model), `FEATURES.md` (7560 lines), `feature_definitions.md`, `ARCHITECTURE_MIGRATION_REPORT.md`. **Use these as the mapping source — don't re-derive.**
- Frontend: `web_app` (Next 16.3.1 / React 18.3.1) with route groups `admin/`, `supplier/`, `suppliers/`, `logistics-partner(s)/`, `cart/`, `checkout/`, `orders/`, `products/`, `profile/`, `wishlist/`, `tracking/`, `returns/`… `web_app/src/lib/api` = `auth/client/country/errors/index` (**no `rbac.ts` yet**). `shared/src/adminPermissions.ts` (300 lines, hardcoded) is the catalog to replace. `mobile_app/` (Expo) present.

**Honest correction to the 40/40/10/10 split you proposed:** copying files will **not** compile — 1027 flat `from models import` and 1657 `from services.` references break the moment files move. The import-rewrite engine is the actual hard part and must run *during* relocation, not "at the end." I recommend: **Phase 1 scaffold+shims (de-risks everything, ~0 behavior change)**, **Phase 2 relocate + AST import-rewrite per domain (the real ~60%)**, **Phase 3 consolidate per-feature (~15%)**, **Phase 4 adapt code to laws + RBAC + frontend (~25%)**.

---

## Phase 1 — Scaffold skeleton + shims + retargeted tooling  *(the "scaffolding pipeline")*

**Goal:** new folders exist; app still boots *exactly* as today via `_legacy/` re-export shims. Zero behavior change.

1. **Reconcile taxonomy (do this first).** `NEW_STRUCTURE.md` invents `customers/`, `suppliers/`, `accounts/`, `risk/`, `governance/` but the real tree has `customer`(5), `supplier`(28), `treasury`(28), `commerce`(25), `identity`(3), `security`(32), `permissions`(1), `governance`(4), `hierarchy`(3), `audit`(7). Build an **authoritative `current → NEW_STRUCTURE` mapping table** (real domain folder → target domain) using `MODELS_SERVICES_CONTROLLERS_MAP.md` + `FEATURES.md`. Resolve `core`(67 services), `delegators`(95), `router_bridges`(57) homes.
2. **Create the new tree** (empty packages with `__init__.py`):
   - `backend/modules/{customer,supplier,logistics,admin,employee}/{auth,routers,serializers}/` — each `routers/__init__.py` exposes `routers` / `public_routers` lists.
   - `backend/domains/{finance,accounts,catalog,orders,payments,logistics,suppliers,customers,hr,comms,media,country,governance}/` with `services/ models/ schemas/ policies/ events.py subscribers.py features.py __init__.py`.
   - `backend/rbac/{catalog,roles,resolution,dependencies,service,models}.py`, `backend/kernel/{money,numbering,country,period}.py`, `backend/infrastructure/{database,redis,storage,messaging,observability,security,utils}/`.
   - `backend/_legacy/{routers,controllers,services,models,db,utils}/` — **re-export shims** (`from services.finance.treasury_engine import *` style) so all 1657/`1027` imports still resolve.
3. **Retarget `auto_router.py`** `--out` to emit into `modules/{m}/routers/` keyed by the controller's surface token; keep `AUTO-GENERATED` marker.
4. **Rewrite `main.py` `_load_routers()`** to the per-module discovery loop from the spec (loop `modules/*/routers`, mount `routers` + `public_routers` under `/api/{m}`), while `_legacy/routers` still supplies the 223 until migrated. Rewrite `lifespan.py` boot anchors to import through `_legacy` shims.
5. **Move `db/` → `infrastructure/database/`** (`base.py`, `database.py`, `session.py`, `transaction.py`) and consolidate the scattered RLS enforcers (`rls_dependency`, `rls_middleware`, `rls_interceptor`, `rls_context`, `country_context`) into **one** `infrastructure/database/security.py`. Keep `db/` re-export shim.
6. **Update CI (`architecture-gate.yml`)** to import the new contract; add `DOMAIN_ALLOWLIST.yaml`.

**Gate:** `pytest` green, app boots, all 223 routers still registered, `coherence_gate.py --check` passes, `auto_router.py --verify` passes.

## Phase 2 — Relocate files with AST import-rewrite  *(your "copy from legacy", but as `git mv` + rewrite)*

**Goal:** move real logic into `modules/`+`domains/`, delete shim entries as each slice goes green.

- **Wave A — foundation (no dependents break):** `kernel/` (lift `money` from `utils`, numbering, `country_code` type), `infrastructure/security` + `redis` + `observability`, and `rbac/` (seed `catalog.py`/`roles.py`/`resolution.py`/`dependencies.py`/`service.py`/`models.py` from existing `utils/staff_permissions.py` `DEFAULT_ROLE_PERMISSION_MAP`, `services/rbac_service.py`, `require_finance_permission`/`hasAdminPermission`).
- **Wave B — per domain, smallest-first:** for `d` in `[country, comms, media, catalog, orders, payments, logistics, suppliers, customers, hr, finance, treasury, governance]`: `git mv services/<d>/* domains/<d>/services/`, `models/<d-file> → domains/<d>/models/`, split `db/schemas.py` slice → `domains/<d>/schemas/`. Run **`scripts/rewrite_imports.py`** for that domain (`services.<d>.` → `domains.<d>.services.`, `models` → `domains.<d>.models`, `db.` → `infrastructure.database.`, `utils.X` → `infrastructure.X`/`kernel.X`). Remove the corresponding `_legacy` shim lines. **Verify per wave.**
- **Wave C — controllers → split:** for each `controllers/{surface}/..._controller.py`, separate the **shell** (`@get/@post` contract) → `modules/<m>/routers/<d>_router.py`, and any inline **logic** → `domains/<d>/services/`. Run auto_router retargeted.
- **Wave D — retire the 223 flat routers:** once `modules/*/routers` are generated/regenerated and verified identical, delete `routers/*.py` and the `_legacy/routers` shim.

**Gate after each wave:** unit+integration tests, `coherence_gate`, `auto_router --verify`, boot check, **no new `_legacy` shim entries** (allowlist only shrinks).

## Phase 3 — Consolidate per feature  *(your "merge files per features")*

- Flatten/slice inside each domain: heavy domains (`finance`, `orders`, `logistics`, `hr`, `comms`) get **vertical slices** (`domains/finance/ledger/`, `payouts/`, `treasury/`); small ones stay flat.
- Add `domains/<d>/ports.py` (the **only** sanctioned cross-domain read surface) and `domains/governance/read_models/command_center.py` for cross-domain dashboards.
- Move inline rules → `domains/<d>/policies/`; domain events → `events.py`/`subscribers.py`.
- Seed `domains/*/features.py` from `FEATURES.md` + `feature_definitions.md` (these are the existing atoms); `rbac/catalog.py` auto-scans both depths.
- Co-locate tests into `domains/<d>/tests/`; keep `tests/architecture/` for law checks.

## Phase 4 — Adapt code to the new structure  *(your "code changes")*

**Backend:**
- Enforce Laws 1–7 via `import-linter` (or extended `coherence_gate`): `modules→domains→infrastructure`, no `domain→module`, cross-domain reads only via `ports.py`/`events.py`; `DOMAIN_ALLOWLIST.yaml` → 0.
- Replace `require_finance_permission`/`hasAdminPermission`/`ADMIN_PERMISSION_MAP` with `require_feature("finance.ledger.post")` + `rbac/`. Add CI test failing on any `require_feature("…")` literal not in catalog.
- Country as 4th axis: RLS session context + `country_staff_assignments` independent of feature check (single enforcer from Phase 1.5).
- Delete `_legacy/` shims when each slice is 100% green.

**Frontend:**
- Add `web_app/src/lib/rbac.ts` fetching `GET /rbac/catalog`; generate `shared/src/permissions.ts` from it (CI), **delete `shared/src/adminPermissions.ts`**.
- Align `web_app/src/app` route groups to modules (`customer/`, `supplier/`, `logistics/`, `admin/`, `employee/`); match API prefixes `/api/{m}`. Update `next.config.ts` rewrites / `vercel.json` if prefixes change. `mobile_app` + `shared` follow the same catalog.

---

## WBS & effort (realistic)

| Phase | Work | Effort | Verification |
|---|---|---|---|
| 1 | Taxonomy map + skeleton + `_legacy` shims + retarget auto_router + `db→infrastructure` + CI | 20% | boot identical, gates green |
| 2 | Relocate + AST import-rewrite per wave (A→D) | 45% | per-wave tests + boot + coherence |
| 3 | Per-feature consolidation, `ports.py`, `policies/`, `features.py`, test co-location | 15% | catalog CI, slice navigation |
| 4 | Law enforcement, RBAC swap, country axis, frontend catalog + route alignment, shim deletion | 20% | import-lint 0 violations, allowlist 0 |

## Top risks to watch
1. **`from models import` (1027 flat refs)** — must be handled by shims in Phase 1 *before* any model moves, or boot breaks.
2. **Boot anchors** — `import models`, `services.unknown._registry`, event listeners: keep resolving via `_legacy` until their owning domain is migrated.
3. **Alembic drift** — moving models into per-domain packages must not change table names/schemas; add a `schema-audit.yml` check (already exists) to every migration PR.
4. **`auto_router` retargeting** — the 223 generated routers must stay byte-for-byte equivalent after re-emitting into `modules/`; `--verify` is your safety net.
5. **`controllers/core`(67)/`delegators`(95)/`router_bridges`(57)** — these are the ambiguous piles; the taxonomy map (Phase 1.1) must decide their homes before Wave C.

## Recommended pilot
Start with **`country`** (small, few models, touches RLS = the 4th axis) or **`finance`** (high-value, already has `treasury`/`accounts` siblings). Prove Phase 1→2→3→4 on one domain end-to-end, then repeat Waves B–D per domain. Do **not** touch the 5 modules' auth split (separate auth-store) until domains are settled.

---

