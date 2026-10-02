# Auth Tests

Login, logout, session management, token refresh, and RBAC gate enforcement for all 5 modules.

## Files

- `auth-role-login.spec.ts` — UI login smoke for admin, customer, supplier, logistics, employee.
- `auth-registration-login.spec.ts` — registration page renders and submission flows.
- `auth-session-refresh.spec.ts` — silent refresh, token rotation, device binding, logout.
- `auth-rbac-gates.spec.ts` — 403 on unauthorized features, cross-tenant data isolation.
