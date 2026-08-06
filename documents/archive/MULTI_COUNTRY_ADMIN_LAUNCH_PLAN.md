# Universal Multi-Country Admin Launch Plan

Status: In Progress
Scope: Enable any current/future country to launch through admin-managed configuration without routine code deployments.

---

## 1) Executive Summary

This plan shifts country rollout from country-specific code branches to one universal control plane.

Execution model:
1. Implement a shared country runtime once (context, tax, logistics strategy, commissions, product visibility).
2. Keep country behavior in admin-managed data and approval workflows.
3. Launch any country as a configuration package with publish/rollback and audit trace.

Admin-first principle:
- Daily country operations (tax, logistics rules, payment methods, feature toggles, commission defaults, visibility) are admin-managed.
- Code changes are required only for new platform capabilities, not for normal market updates.

---

## 2) Universal Architecture

### Shared Runtime (single code path)
- Country context middleware with validated fallback.
- Tax service using country config rows (type, rate, inclusivity, category overrides).
- Logistics service using country logistics mode and rules.
- Commission resolution with country-category overrides.
- Product listing filtered by request country context.

### Admin Control Plane (single control surface)
- Country config CRUD with validation guardrails.
- Draft -> Approve -> Publish -> Rollback lifecycle.
- Version history and immutable audit logs.
- Preview endpoints before publish for tax/logistics/commission outcomes.

### Country Configuration Package (data only)
- Identity: country code, name, timezone, currency.
- Tax: type/rate/name, inclusivity, reduced/exempt category maps.
- Logistics: model + rates/zone payloads.
- Commissions: category defaults and optional overrides.
- Payments + feature flags + emergency toggles.

---

## 3) Current Implementation Scope

### Completed foundation
- Country control-plane tables and seeded baseline data.
- Universal tax service and country context middleware.
- Admin countries API workflow (draft, approve, publish, rollback).
- Country-aware order tax/currency logic and commission-country overrides.
- Product region fallback from resolved request country.

### In-progress universalization
- Consolidate country logistics formulas into shared logistics service.
- Remove Oman-only naming from router/controller payloads.
- Ensure middleware defaults and API payloads are not hardcoded to any specific country.

---

## 4) Admin Ownership Matrix

Admin-manageable controls (no code deploy required):
- Tax profile: type, rate, inclusivity, exemptions, reduced rates.
- Logistics profile: base/per-km/min charge/surcharge and delivery zones (where zone model is used).
- Commission profile: category defaults by country.
- Payments profile: enabled methods and fallback order.
- Feature flags: rollout toggles by country and audience.
- Safety switches: per-country checkout/order/payment kill switches.

Approval policy:
- Tax and commission publish requires finance/compliance approver roles.
- Logistics and payments publish requires operations approver role.
- All publish and rollback actions are audited.

---

## 5) Detailed Implementation Stages

### Stage A: Runtime Unification
Tasks:
1. Keep all country logistics formulas in `backend/services/logistics_partner_pricing.py`.
2. Keep tax logic centralized in `backend/services/tax_service.py`.
3. Ensure middleware resolves country generically from active configs.
4. Remove hardcoded country-only route naming from countries APIs.

Stage tests:
- Unit tests for country resolution and delivery calculation helpers.
- API tests for country workflow endpoints using non-OM/PK country codes.

Exit criteria:
- New country code works without service-layer code changes.

### Stage B: Order + Product + Commission Runtime
Tasks:
1. Orders use universal country tax resolution and currency from country config/user preference.
2. Product listing defaults to request country context when explicit region filter is absent.
3. Commission engine checks country-category overrides before global category rates.

Stage tests:
- Regression tests for orders/products/commission.
- Targeted test for country-specific commission override behavior.

Exit criteria:
- Country-aware totals and listing isolation are deterministic.

### Stage C: Admin Workflow Safety
Tasks:
1. Keep draft/approve/publish/rollback flow universal for all countries.
2. Keep payload schema country-neutral (`delivery_zones` vs country-specific naming).
3. Keep preview endpoints for publish confidence.

Stage tests:
- Admin flow tests: create draft, approve, publish, rollback.
- Audit log assertions for each lifecycle action.

Exit criteria:
- Admin can safely control country behavior with rollback under 5 minutes.

### Stage D: Browser Assurance
Tasks:
1. Run role login and admin browser flows using Playwright.
2. Validate API+UI behavior after backend universalization.

Stage tests:
- Playwright auth role smoke.
- Playwright admin data operations/workspace smoke.

Exit criteria:
- Browser validation passes for critical role flows.

---

## 6) Universal Test Matrix

### Backend
- Country middleware:
  - header/query/user-preference fallback order
  - configurable default-country behavior
- Tax service:
  - standard/reduced/exempt/inclusive cases
  - arbitrary active country code support
- Logistics service:
  - generic per-km country quote
  - legacy Pakistan helper compatibility in shared service
- Country admin workflow:
  - tax/logistics/commission/ops draft->approve->publish
  - version listing and rollback behavior

### Browser (Playwright)
- Auth role login smoke.
- Core customer/admin smoke for runtime sanity.
- Admin operations smoke for configuration UX health.

---

## 7) Launch Gates (Universal)

Gate 1: Data readiness
- country configs exist for target launch countries.

Gate 2: Functional correctness
- tax/logistics/commission outputs match approved examples.

Gate 3: Security and isolation
- server-side country resolution prevents cross-country leakage.

Gate 4: Operational readiness
- admin publish/rollback and audits verified.

Gate 5: Browser confidence
- critical role-based browser smoke tests pass.

---

## 8) Backlog Priorities

P0:
- Universal runtime services and middleware defaults.
- Admin country APIs with universal payload names.
- Country-aware orders/products/commission integration.

P1:
- Admin UI controls and full role-based approvals.
- Expanded country analytics and workflow telemetry.

P2:
- Advanced country routing and subdomain auto-selection.
- Deeper per-country alerting and anomaly controls.

---

## 9) Operating Rule

Any new country must launch by configuration package through admin workflows.
No branch-specific runtime logic should be introduced for a single country when a shared service extension can satisfy the requirement.
