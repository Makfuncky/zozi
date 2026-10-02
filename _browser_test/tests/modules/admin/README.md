# Admin Tests

Administrative functions: user management, configuration, monitoring, billing, finance, commissions, countries, logistics, HR, permissions, security.

## Files

- `admin-commission.spec.ts` — global config, category rates, badge tiers.
- `admin-audit-fixes.spec.ts` — audit logs chrome, command center WebSocket, promotions prefix.
- `admin-country-control-plane.spec.ts` — ledger table, create country, 12-tab workspace, version history.
- `admin-country-enhanced.spec.ts` — inline form, auto-populate, ledger columns, bulk commission.
- `admin-communication-hub.spec.ts` — video rooms, email campaigns, chat threads.
- `admin-data-ops.spec.ts` — DB health, backup, restore, user export.
- `admin-logistics-workspace.spec.ts` — logistics config, carriers, service areas.
- `admin-hr-permissions.spec.ts` — employee management, permissions matrix.
- `admin-modules-reconciliation.spec.ts` — module route inventory vs actual routes.
- `admin-payment-gateways.spec.ts` — gateway attach, config, country assignment.
- `admin-supplier-logistics-sanity.spec.ts` — supplier and logistics sanity checks.
- `admin-treasury-payout.spec.ts` — treasury overview, payout sweep.
- `finance-e2e.spec.ts` — all 12 finance tabs: COA, FX, Deferred Revenue, Email-to-Ledger, Bank Mapping, AR/AP, Journal, Budgets, Audit Log.
- `finance-cod-proof-live.spec.ts` — logistics COD proof upload, admin verify.
- `employee-login.spec.ts` — employee UI and API bootstrap login.
- `employee-dashboard.spec.ts` — assigned orders, support tickets.
- `employee-orders.spec.ts` — order detail, internal notes.
- `employee-customers.spec.ts` — customer search, order history.
- `employee-hr.spec.ts` — onboarding pipeline, HSE tab.
- `rbac-enforcement.spec.ts` — 403 on unauthorized access, cross-tenant isolation.
- `csrf-protection.spec.ts` — POST without CSRF token returns 403.
- `xss-protection.spec.ts` — user-generated content sanitized, CSP header present.
- `rate-limiting.spec.ts` — 15 rapid logins return 429.
- `rls-cross-tenant.spec.ts` — country_code blocks cross-country reads.
- `input-validation.spec.ts` — oversized passwords, SQL injection, XSS in address fields.
