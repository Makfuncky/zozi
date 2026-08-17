# Multi-Country Admin Onboarding & Management System

Status: In Progress / Partially Implemented
Scope: The operating "control plane" that lets any country be launched and run as a configuration package through admin-managed workflows — with full isolation and country-scoped management of employees, country heads, suppliers, customers, accounts, finance, banners, promotions, commissions, auto-tax detection, treasury, logistics, payment gateways, and reconciliation. Works hand-in-hand with the Country Intelligence feature (see companion document `COUNTRY_INTELLIGENCE_AUTO_RESEARCH.md`), which supplies the research data used to seed each new country.

---

## 1) The Two Sides of One Coin

| | Country Intelligence (companion doc) | Country Admin System (this doc) |
|---|---|---|
| Question | "Should we enter this country, and what does it look like?" | "How do we launch and operate this country safely?" |
| Output | Read-only research profile (20 modules) | Live, configurable country in the platform |
| Owner | Strategy / expansion team | Admin + Country Head + country staff |
| Data flow | Research → JSON → seeds onboarding | Config package → publish → runtime |

This document is the operating side. The goal is to make launching a new country a **configuration-and-approval action**, not a code deployment.

---

## 2) Universal Architecture

### 2.1 Shared Runtime (single code path)
- Country context middleware with validated fallback (resolves country from JWT → staff assignment → IP → header).
- Tax service using country config rows (type, rate, inclusivity, category overrides).
- Logistics service using country logistics mode and rules.
- Commission resolution with country-category overrides.
- Product listing filtered by request country context.

### 2.2 Admin Control Plane (single control surface)
- Country config CRUD with validation guardrails.
- Draft → Approve → Publish → Rollback lifecycle.
- Version history and immutable audit logs.
- Preview endpoints (before publish) for tax/logistics/commission outcomes.

### 2.3 Country Configuration Package (data only)
- Identity: country code, name, timezone, currency.
- Tax: type/rate/name, inclusivity, reduced/exempt category maps.
- Logistics: model + rates/zone payloads.
- Commissions: category defaults and optional overrides.
- Payments + feature flags + emergency toggles.

### 2.4 Admin-First Principle
Daily country operations (tax, logistics rules, payment methods, feature toggles, commission defaults, visibility) are admin-managed. Code changes are required only for new platform capabilities, not for normal market updates.

---

## 3) Unified Data Model

### 3.1 Core Entity: `country_configs` (Master Table)
Implemented in `backend/models/countries.py`. Key fields:
- **Identity:** `code`, `name`, `official_name`, `alpha3`, `capital`, `region`, `subregion`, `flag_url`, `phone_code`, `language`, `timezone`, `date_format`, `status`, `is_active`, `is_deleted`, `is_default`.
- **Economy:** `population`, `internet_penetration_pct`, `gdp_per_capita_usd`, `urbanization_pct`, `mobile_subs_per_100`, `exchange_rate_to_usd`.
- **Currency:** `currency`, `currency_symbol`, `currency_name`.
- **Tax:** `tax_type` (VAT/GST/etc.), `tax_rate`, `tax_name`, `tax_inclusive`.
- **Payments/Logistics:** `payment_methods_json`, `payment_gateways_json`, `logistics_providers_json`.
- **Fraud/Compliance:** `fraud_risk_tier`, `data_residency_tier`.
- **COD:** `cod_enabled`, `cod_max_amount`, `cod_verification_required`, `cod_remittance_days`.
- Relationships: `CountryCommunication`, `CountryGatewayCredentials`, `TaxRule`, `ShippingRule`, `PayoutRule`, `CountryCity`.

### 3.2 Normalized Supporting Tables (in `country_enhancements.py`)
- `CountryCity` — normalized cities with `country_code` FK, `population`, `is_capital`, lat/lng, postal prefix.
- `CountryCategoryTaxRate` — per-category tax rates.
- `CountryStaffAssignment` — links user ↔ country ↔ role.
- `CountryCommunicationThread` — internal/external comms linked to a country.
- `CrossCountryCustomerSession` — tracks customers shopping across countries (model exists; table not yet created).

### 3.3 Required Data-Model Changes (backfill existing global tables)
| Table | Add Column | Purpose |
|-------|------------|---------|
| `suppliers` | `country_code` FK | Country isolation |
| `products` | `country_code` FK | Country catalog |
| `orders` | `country_code` FK | Order segregation |
| `banners` | `country_code` FK | Banner per country |
| `promotions` | `country_code` FK | Promo per country |
| `logistics_partners` | `country_code` FK | Partner per country |
| `payouts` | `country_code` FK | Payout per country |
| `employees` | ✅ exists | Already has `country_code` |
| `users` | `default_country_code` | Default context |
| `country_staff_assignments` | ✅ exists | Link staff ↔ country ↔ role |

---

## 4) Country-Scoped Sub-Systems (the "everything separated by country" requirement)

Each of the following must operate per-country with isolated data and its own admin surface:

### 4.1 Employees & Staff Management
- Refactor `/employees` → `/admin/{countryCode}/employees`; remove hardcoded `/countries/OM/` paths.
- Link `Employee.country_code` → `CountryStaffAssignment`.
- Geo-fenced check-in using `Employee.geo_check_in` + `Office.geo_fence_radius_meters` per country.
- Country head, sub-admin, manager, finance, moderator roles scoped to assigned countries.

### 4.2 Country Head & Hierarchy
- A Country Head owns one or more assigned countries and can configure, manage suppliers/products/orders/banners, but not cross-country.
- Hierarchy: Global Admin → Sub-Admin → Country Head → Country Manager / Country Finance / Country Moderator.
- Staff transfer/reassignment between countries with audit trail.

### 4.3 Supplier Management
- `GET/POST/PUT/DELETE /admin/{cc}/suppliers`, `/suppliers/{id}/verify`, `/suppliers/{id}/kyc`.
- KYC tiers via `SupplierKYCRequirement` per country (heuristic engine estimates documents by GDP tier).
- Supplier scorecards, FastPay conditional payouts, chargebacks for avoidable returns.

### 4.4 Customer Management
- `GET /admin/{cc}/customers`, `/customers/{id}/orders`, `/customers/reconcile`.
- Order history, delivery reconciliation, cross-country session tracking via `CrossCountryCustomerSession`.

### 4.5 Banner & Promotion Management
- `GET/POST/PUT/DELETE /admin/{cc}/banners`, `/admin/{cc}/promotions` with country-scoped scheduling.
- Use `CountryFeatureFlag` for promo types; festival calendars drive automated campaigns.

### 4.6 Product & Supplier Management
- `GET/POST/PUT/DELETE /admin/{cc}/products`, `/products/{id}/supplier-link`.
- Supplier assignment, category commissions per country, prohibited-item filters from research.

### 4.7 Logistic Partner Management
- `GET/POST/PUT/DELETE /admin/{cc}/logistics-partners`, `/logistics-partners/{id}/zones`, `/logistics-partners/{id}/payouts`.
- Uses `CountryLogisticsZone`, `LogisticsPartnerKYCRequirement`, shared logistics service (per-km, fixed, zone modes).

### 4.8 Payment Gateway System
- `GET/POST/PUT/DELETE /admin/{cc}/payment-gateways`, `/payment-gateways/test`.
- Credentials vault via `CountryGatewayCredentials` + `CountryGatewayConfig`.
- Gateway Registry service (currently missing) ranks feasible gateways.

### 4.9 Accounts, Finance & Treasury
- `CountryPayoutRule`, `settlement_hold_days`, minimum payout, schedule, batch size.
- COD reconciliation: `GET /admin/{cc}/cod-reconciliation`, `POST /admin/{cc}/cod-reconciliation/settle`.
- Order reconciliation & customer/delivery reconciliation: cross-reference logistics + orders.
- Multi-currency settlement and treasury per country.

### 4.10 Auto-Tax Detection
- Universal tax service computes tax from `country_configs` + `CountryCategoryTaxRate` + `CountryTaxRule`.
- Standard/reduced/exempt/inclusive handling; auto-applied at checkout; preview before publish.

### 4.11 Commission System
- Category defaults by country; country-category overrides checked before global rates.
- Value commissions (tier-based) and category commissions managed per country.

### 4.12 Feature Flags & Safety Switches
- Per-country and per-audience rollout toggles.
- Per-country checkout/order/payment kill switches (emergency).

### 4.13 Localization
- Language, currency, date/number format, RTL, calendar, numerals, branding per country (`CountryLocalization`).
- Missing tab — needs implementation.

### 4.14 Analytics
- Per-country performance dashboard; cross-country comparison (`/admin/analytics/cross-country`).
- Missing tab — needs implementation.

---

## 5) The Algorithmic Heuristic Engine

Implemented in `backend/services/country_heuristic_engine.py` (`generate_ecommerce_defaults()`). It proposes sensible defaults for a new country so onboarding is near one-click.

### 5.1 Payment Gateway Ranking (0-100)
| Component | Points |
|-----------|--------|
| Region Match | 40 |
| Currency Match | 25 |
| Internet Penetration | 15 |
| Fee Competitiveness (inverse) | 10 |
| Setup Speed (inverse) | 10 |

Supported gateways include Thawani, Stripe, Tap, HyperPay, PayTabs, Mada, OmanNet, STC Pay, PayPal, Tabby, Klarna (12 profiles).

### 5.2 Commission Tiers (by category, adjusted by GDP/region)
| Category | Min% | Max% | Suggested% |
|----------|------|------|------------|
| electronics | 4 | 8 | 6.0 |
| fashion | 12 | 22 | 17.0 |
| groceries | 2 | 6 | 4.0 |
| beauty | 10 | 18 | 14.0 |
| automotive | 5 | 10 | 7.0 |

Adjustments: Emerging (GDP < $10K) ×0.85; Developing ($10K-$40K) ×1.0; Developed (>$40K) ×1.10; GCC/Middle East +5%.

### 5.3 KYC Rules by GDP Tier
- Basic (<$10K): National ID, Phone OTP.
- Standard ($10K-$40K): ID, Commercial Reg, Bank Letter.
- Strict (>$40K or GCC/EU/NA): + VAT Cert, Trade License, Passport.

### 5.4 COD Reliance by Internet Penetration
<40% → 80%; 40-60% → 60%; 60-80% → 35%; >80% → 15%.

### 5.5 Payout Settings
>$30K → min $50, weekly, batch 100; >$10K → min $20, weekly, batch 50; ≤$10K → min $10, biweekly, batch 25.

### 5.6 Logistics Model
>$30K & >10M pop → hub_and_spoke; >$10K & >5M → hybrid; ≤$10K & ≤5M → point_to_point.

### 5.7 Fraud Risk Scoring
>$30K & >80% & GCC/EU/NA → low; >$10K & >50% → medium; ≤$10K & ≤50% → high.

> Gateway Registry service and the Redis-cached auto-populate API endpoint are referenced but not yet implemented.

---

## 6) Admin Workflow & Lifecycle

### 6.1 States
Draft → Approve → Publish → Rollback, with version history and immutable audit logs.

### 6.2 Approval Policy
- Tax and commission publish requires finance/compliance approver roles.
- Logistics and payments publish requires operations approver role.
- All publish/rollback actions are audited.

### 6.3 Safety
- Preview endpoints let admins validate tax/logistics/commission outcomes before publishing.
- Rollback target: under 5 minutes.
- `CountryConfigVersion` records each published configuration for audit and cloning.

### 6.4 Admin Ownership Matrix
Admin-manageable controls (no code deploy required):
- **Tax profile:** type, rate, inclusivity, exemptions, reduced rates.
- **Logistics profile:** base/per-km/min charge/surcharge and delivery zones (where zone model is used).
- **Commission profile:** category defaults by country.
- **Payments profile:** enabled methods and fallback order.
- **Feature flags:** rollout toggles by country and audience.
- **Safety switches:** per-country checkout/order/payment kill switches.

Approval policy:
- Tax and commission publish requires finance/compliance approver roles.
- Logistics and payments publish requires operations approver role.
- All publish/rollback actions are audited.

This is the concrete control list behind the 3-layer RBAC in section 8 and the "admin-first" principle in section 2.4.

### 6.5 Current Implementation Scope
**Completed foundation:**
- Country control-plane tables and seeded baseline data.
- Universal tax service and country context middleware.
- Admin countries API workflow (draft, approve, publish, rollback).
- Country-aware order tax/currency logic and commission-country overrides.
- Product region fallback from resolved request country.

**In-progress universalization:**
- Consolidate country logistics formulas into shared logistics service.
- Remove Oman-only naming from router/controller payloads.
- Ensure middleware defaults and API payloads are not hardcoded to any specific country.

### 6.6 Country Onboarding Wizard (advanced)
`/admin/countries/new` → auto-populate from research (Country Intelligence JSON or `country_curated.py`) → create all default configs (tax, logistics, KYC, gateways) → route through draft/approve/publish. Supports country cloning (A → B with modifications).

---

## 7) Data Isolation & Security (RLS)

### 7.1 Current Gap
`country_rls.py` / `rls_interceptor.py` set only thread-local context — no enforced PostgreSQL RLS policies. Country managers can currently see ALL countries' suppliers, orders, products, banners, employees. This must be fixed.

### 7.2 Required Implementation
- Enable RLS on `suppliers`, `products`, `orders`, `banners`, `promotions`, `employees`, `logistics_partners`, `payouts`:
  ```sql
  ALTER TABLE suppliers ENABLE ROW LEVEL SECURITY;
  CREATE POLICY supplier_country_isolation ON suppliers
    USING (country_code = current_setting('app.current_country_code'));
  ```
- `CountryContextMiddleware` sets `request.state.country_code` from: JWT claim → staff assignment → IP detection → header.
- All `/admin/*` routers accept `country_code` path param and call `enforce_country_access(code, request, db)`.
- Frontend `apiFetchWithCountry()` injects `X-Country-Code` header from React context.
- `AuditTrailService` tags every change with `country_code` and enforces it in RLS.
- Super-admin global view via `/admin/global/...` or `?country=all`.

---

## 8) Role-Based Access Control (3-Layer Permissions)

Permissions must be open and in the Admin's hand: Admin creates categories and grants permission to Sub-Admin, who grants permission to Employees. Three layers.

### 8.1 Roles
Global: `admin`, `sub_admin`. Country-scoped: `country_head`, `country_manager`, `country_finance`, `country_moderator`, `country_operations`.

### 8.2 Target Permission Matrix
| Permission | Admin | Sub-Admin | Country Head | Country Manager | Country Finance | Country Moderator |
|------------|-------|-----------|--------------|-----------------|-----------------|-------------------|
| All Countries | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Assigned Countries Only | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Configure Country | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Manage Suppliers | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Manage Products | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Manage Orders | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Manage Banners/Promos | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Manage Logistics | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Payment Gateways | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| COD/Finance Recon | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| Staff Assignment | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| View Analytics | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Audit Trail | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |

### 8.3 Implementation
- Extend `ADMIN_PERMISSION_MAP` to include `country_code` dimension: `{ role: { country_code: [permissions] } }`.
- On `CountryStaffAssignment` create/update, auto-sync permissions into the user's JWT claims.
- Frontend `useCountryPermission(permission, countryCode)` hook wraps admin components.
- Country selector in `AdminLayout` shows only assigned countries.

---

## 9) Frontend Tab Matrix (Country Ledger UI)

| Tab | Route | Component | API Endpoint | Status |
|-----|-------|-----------|--------------|--------|
| Overview | `/admin/countries/:code` | CountryOverview | `GET /country/{code}` | ✅ |
| Tax & VAT | `/admin/countries/:code/tax` | TaxConfig | `GET /country/{code}/tax` | ✅ |
| Logistics | `/admin/countries/:code/logistics` | LogisticsConfig | `GET /country/{code}/logistics` | ✅ |
| Gateways | `/admin/countries/:code/gateways` | GatewayList | `GET /country/{code}/gateways` | ✅ |
| KYC | `/admin/countries/:code/kyc` | KYCRequirements | `GET /country/{code}/kyc` | ✅ |
| Payouts | `/admin/countries/:code/payouts` | PayoutConfig | `GET /country/{code}/payouts` | ✅ |
| Commissions | `/admin/countries/:code/commissions` | CommissionConfig | `GET /country/{code}/commissions` | ✅ |
| Analytics | `/admin/countries/:code/analytics` | CountryAnalytics | `GET /country/{code}/analytics` | ❌ Missing |
| Localization | `/admin/countries/:code/localization` | LocalizationConfig | `GET /country/{code}/localization` | ❌ Missing |
| Regions & Cities | — | — | — | ⚠️ Partial (JSON blob) |
| Interactive Map | — | CountryMapView | — | ✅ |
| Supplier KYC | — | — | — | ✅ |
| Staff Assignments | — | — | — | ✅ |
| Communications | — | — | — | ⚠️ Partial |
| Promotions | — | — | — | ✅ |
| Feature Flags | — | — | — | ✅ |
| Version History | — | — | — | ✅ |

Plus per-country operational pages under `/admin/{cc}/...`: suppliers, customers, banners, promotions, products, logistics-partners, employees, payment-gateways, finance/cod-reconciliation, finance/reconciliation.

---

## 10) Cross-System Integration Points
- **Fraud Detection:** `fraud_risk_tier` feeds `calculate_score()`; high-risk countries get higher base scores.
- **Chat/Video/Email:** `CountryCommunicationThread` links comms to countries; internal channels per country; audit service logs country-specific events.
- **Employee Management:** `CountryStaffAssignment` enforces country-level access via RLS; shift handover can be country-specific.
- **Treasury/Finance:** payout rules, COD settlement, reconciliation all country-scoped.

---

## 11) Implementation Roadmap

### PHASE 1: Foundation — Multi-Country Architecture (Week 1-2)
1.1 RLS policies on all isolated tables keyed by `country_code`.
1.2 `CountryContextMiddleware` (JWT → staff → IP → header).
1.3 Scope all `/admin/*` routers with `enforce_country_access()`.
1.4 Frontend `apiFetchWithCountry()` injecting `X-Country-Code`.
1.5 Country selector in `AdminLayout` (assigned countries only).

### PHASE 2: Country Admin Dashboard — Full Segregation (Week 2-4)
2.1 Supplier Management (KYC, verification, tiers).
2.2 Customer Management (orders, delivery recon).
2.3 Banner & Promotion Management (country-scoped scheduling).
2.4 Product & Supplier Management (supplier linking, category commissions).
2.5 Logistic Partner Management (zones, payouts).
2.6 Employee Management (country-scoped CRUD).
2.7 Payment Gateway System (credentials vault).
2.8 COD & Order Reconciliation.
2.9 Customer/Delivery Reconciliation.
2.10 Move remaining config tabs to per-country pages.

### PHASE 3: RBAC & Permissions (Country-Dimensional) (Week 3-4)
3.1 Permission matrix with `country_code` dimension.
3.2 Staff assignment → JWT permission sync.
3.3 Country-specific roles.
3.4 Frontend `useCountryPermission` guards.
3.5 Per-country audit trail.

### PHASE 4: IP/Geo Intelligence & Automation (Week 4-5)
4.1 IP → country auto-routing for sessions.
4.2 Geo-fenced employee check-in.
4.3 Country-specific compliance (data residency, PDPL/GDPR).
4.4 Multi-currency & auto-tax at checkout.

### PHASE 5: Advanced Features (Week 5-6)
5.1 Country Onboarding Wizard (research → auto-populate → publish).
5.2 Cross-Country Analytics.
5.3 Staff transfer/reassignment.
5.4 Country cloning.
5.5 White-label theming (RTL, numerals, branding).

### Phase Backlog Priorities
- **P0:** RLS + context middleware + API client + selector; Analytics tab; Supplier/Product/Banner per-country.
- **P1:** Cross-country customer table; Auto-populate API; Internal channels; Audit trail API; Localization tab.
- **P2:** Gateway Registry; Alembic migrations; Enhanced city management.

### Implementation Priority Matrix (effort vs impact)
| Priority | Component | Effort | Impact |
|----------|-----------|--------|--------|
| P0 | Analytics Tab UI | Medium | High |
| P0 | Localization Tab UI | Low | Medium |
| P1 | Cross-Country Customer Records table | Low | Medium |
| P1 | Auto-populate API endpoint | Medium | High |
| P1 | Internal Channels API | Low | High |
| P1 | Audit Trail API | Low | High |
| P2 | Gateway Registry service | Medium | High |
| P2 | Alembic migrations | Low | High |
| P3 | Enhanced city management | Medium | Medium |

---

## 12) Implementation Stages & Universal Test Matrix

### 12.1 Detailed Implementation Stages
These stages operationalize the roadmap (section 11) with explicit tasks, tests, and exit criteria.

**Stage A: Runtime Unification**
- Tasks: keep all country logistics formulas in `backend/services/logistics_partner_pricing.py`; keep tax logic centralized in `backend/services/tax_service.py`; ensure middleware resolves country generically from active configs; remove hardcoded country-only route naming from countries APIs.
- Stage tests: unit tests for country resolution and delivery calculation helpers; API tests for country workflow endpoints using non-OM/PK country codes.
- Exit criteria: a new country code works without service-layer code changes.

**Stage B: Order + Product + Commission Runtime**
- Tasks: orders use universal country tax resolution and currency from country config/user preference; product listing defaults to request country context when explicit region filter is absent; commission engine checks country-category overrides before global category rates.
- Stage tests: regression tests for orders/products/commission; targeted test for country-specific commission override behavior.
- Exit criteria: country-aware totals and listing isolation are deterministic.

**Stage C: Admin Workflow Safety**
- Tasks: keep draft/approve/publish/rollback flow universal for all countries; keep payload schema country-neutral (`delivery_zones` vs country-specific naming); keep preview endpoints for publish confidence.
- Stage tests: admin flow tests (create draft, approve, publish, rollback); audit log assertions for each lifecycle action.
- Exit criteria: admin can safely control country behavior with rollback under 5 minutes.

**Stage D: Browser Assurance**
- Tasks: run role login and admin browser flows using Playwright; validate API+UI behavior after backend universalization.
- Stage tests: Playwright auth role smoke; Playwright admin data operations/workspace smoke.
- Exit criteria: browser validation passes for critical role flows.

### 12.2 Universal Test Matrix
**Backend**
- Country middleware: header/query/user-preference fallback order; configurable default-country behavior.
- Tax service: standard/reduced/exempt/inclusive cases; arbitrary active country code support.
- Logistics service: generic per-km country quote; legacy Pakistan helper compatibility in shared service.
- Country admin workflow: tax/logistics/commission/ops draft→approve→publish; version listing and rollback behavior.

**Browser (Playwright)**
- Auth role login smoke.
- Core customer/admin smoke for runtime sanity.
- Admin operations smoke for configuration UX health.

---

## 13) Key Metrics & Monitoring

| Metric | Target | Description |
|--------|--------|-------------|
| Gateway Success Rate | > 95% | Payment gateway integration success |
| KYC Approval Rate | > 80% | Percentage of suppliers approved |
| COD Conversion | Variable | By country internet penetration |
| Country Coverage | > 90% | Countries with complete config |

---

## 14) Launch Gates (Universal)
1. **Data readiness** — country configs exist for target launch countries.
2. **Functional correctness** — tax/logistics/commission outputs match approved examples.
3. **Security & isolation** — server-side country resolution prevents cross-country leakage (RLS enforced).
4. **Operational readiness** — admin publish/rollback and audits verified.
5. **Browser confidence** — critical role-based browser smoke tests pass (Playwright).

---

## 15) Critical Problems To Resolve (Current State)
1. No enforced RLS — country managers see all countries' data.
2. Employee system not country-aware (hardcoded `/countries/OM/` paths).
3. Incomplete country admin dashboard (tabs are config-only; missing Supplier/Customer/Product/Banner management).
4. Banner/Promotion/Supplier systems not country-segregated.
5. IP/country detection not integrated with RBAC.
6. Fragmented role system (no country dimension in permission evaluation).
7. No enforced country-level feature flags.
8. Payment gateway / logistics / COD not country-scoped with management APIs.

---

## 16) Operating Rule
Any new country must launch by configuration package through admin workflows. No branch-specific runtime logic should be introduced for a single country when a shared service extension can satisfy the requirement.

---

## 17) Connection to Companion Feature
The Country Intelligence auto-research feature (`COUNTRY_INTELLIGENCE_AUTO_RESEARCH.md`) supplies the 20-module JSON that seeds `country_configs` during onboarding — currency, tax, payments, logistics, legal KYC, and risk feed directly into the heuristic engine and the draft configuration package. Research confidence flags tell compliance which values must be verified before publish.
