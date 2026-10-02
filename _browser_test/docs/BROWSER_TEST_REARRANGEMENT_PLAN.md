# Browser Test Rearrangement Plan

> **Authority:** `_most_imp_docx/ARCHITECTURE_STACK.md`, `_most_imp_docx/TECHNOLOGY_STACK.md`, `_browser_test/docs/PROMPT_BROWSER_TEST.md`
> **Date:** 2026-10-02
> **Status:** ACTIVE — pending execution

---

## 1 · Current State Summary

`_browser_test/tests/` contains **68 spec files** distributed across 4 top-level folders. The benchmark (`PROMPT_BROWSER_TEST.md`) requires exactly **62 files** in specific module-aligned locations. The current layout has:

- **12 extra files** not in the benchmark
- **4 mislocated files** in wrong directories
- **2 misnamed files** with incorrect filenames
- **6 missing files** that must be created

---

## 2 · Files to DELETE (12 extra files)

These files exist in `_browser_test/tests/` but are **not** in the benchmark. Delete them entirely.

| # | File | Reason |
|---|---|---|
| 1 | `tests/auth/auth-e2e-journey.spec.ts` | Extra — not in benchmark |
| 2 | `tests/modules/admin/admin-dashboard-journey.spec.ts` | Extra — not in benchmark |
| 3 | `tests/modules/admin/admin-logistics-pricing-insights-live.spec.ts` | Extra — not in benchmark |
| 4 | `tests/modules/admin/temp-import-test.spec.ts` | Extra — not in benchmark |
| 5 | `tests/modules/customer/cart-checkout-journey.spec.ts` | Extra — not in benchmark |
| 6 | `tests/modules/supplier/supplier-upload-journey.spec.ts` | Extra — not in benchmark |
| 7 | `tests/modules/employee/hr-dashboard-visual.spec.ts` | Extra — not in benchmark |
| 8 | `tests/modules/employee/hr-dashboard.spec.ts` | Extra — not in benchmark |
| 9 | `tests/modules/employee/hr-router-prefix.spec.ts` | Extra — not in benchmark |
| 10 | `tests/modules/logistics/shipping-quote-checkout.spec.ts` | Extra/duplicate — benchmark has `shipping-quote.spec.ts` |
| 11 | `tests/cross-cutting/consistency-audit.spec.ts` | Extra — not in benchmark |
| 12 | `tests/cross-cutting/comprehensive-test.spec.ts` | Extra — not in benchmark |

---

## 3 · Files to MOVE (4 mislocated files)

These files exist but are in the wrong directory per benchmark module alignment.

| # | Current Path | Target Path | Rationale |
|---|---|---|---|
| 1 | `tests/cross-cutting/search-bar-header.spec.ts` | `tests/modules/customer/customer-search.spec.ts` | Customer search/header UI belongs to customer module |
| 2 | `tests/cross-cutting/voice-to-catalog.spec.ts` | `tests/modules/supplier/supplier-voice-to-catalog.spec.ts` | Voice-to-catalog is a supplier catalog feature |
| 3 | `tests/cross-cutting/verify-8-fixes.spec.ts` | `tests/modules/admin/admin-verify-fixes.spec.ts` | Security verification belongs to admin module |
| 4 | `tests/cross-cutting/security.spec.ts` | `tests/modules/admin/admin-security.spec.ts` | Security tests belong to admin module |

---

## 4 · Files to RENAME (2 misnamed files)

These files exist in the correct directory but have wrong filenames per benchmark.

| # | Current Path | Target Path | Rationale |
|---|---|---|---|
| 1 | `tests/modules/supplier/supplier-product-upload-complete.spec.ts` | `tests/modules/supplier/supplier-product-upload.spec.ts` | Benchmark name is `supplier-product-upload` |
| 2 | `tests/modules/supplier/supplier-kyc-form.spec.ts` | `tests/modules/supplier/supplier-kyc.spec.ts` | Benchmark name is `supplier-kyc` |

---

## 5 · Files to CREATE (6 missing files)

These files are required by the benchmark but do not exist yet. Create as stubs.

| # | Path | Description |
|---|---|---|
| 1 | `tests/auth/auth-session-refresh.spec.ts` | Session refresh, token rotation, device binding, logout |
| 2 | `tests/auth/auth-rbac-gates.spec.ts` | RBAC 403 enforcement, cross-tenant isolation |
| 3 | `tests/modules/customer/customer-cart.spec.ts` | Cart persistence, quantity updates, empty cart, cross-border tax |
| 4 | `tests/modules/customer/customer-wishlist.spec.ts` | Wishlist add, persist across sessions |
| 5 | `tests/modules/supplier/supplier-orders-payouts.spec.ts` | Orders list, parcel sheet, payouts, support tickets |
| 6 | `tests/modules/logistics/logistics-dashboard.spec.ts` | Dashboard stats, scan page, status updates |

---

## 6 · Complete Target File Inventory (62 files)

After rearrangement, `_browser_test/tests/` must contain exactly these files:

```
_browser_test/tests/
├── preflight.spec.ts
├── database.spec.ts
├── fixtures.ts
├── auth/
│   ├── auth-role-login.spec.ts
│   ├── auth-registration-login.spec.ts
│   ├── auth-session-refresh.spec.ts          ← CREATE
│   └── auth-rbac-gates.spec.ts               ← CREATE
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
│   │   ├── admin-verify-fixes.spec.ts        ← MOVE from cross-cutting/verify-8-fixes.spec.ts
│   │   ├── admin-security.spec.ts            ← MOVE from cross-cutting/security.spec.ts
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
│   │   ├── customer-search.spec.ts           ← MOVE from cross-cutting/search-bar-header.spec.ts
│   │   ├── customer-cart.spec.ts             ← CREATE
│   │   └── customer-wishlist.spec.ts         ← CREATE
│   ├── supplier/
│   │   ├── supplier-smoke.spec.ts
│   │   ├── supplier-search.spec.ts
│   │   ├── supplier-product-upload.spec.ts   ← RENAME from supplier-product-upload-complete.spec.ts
│   │   ├── supplier-kyc.spec.ts             ← RENAME from supplier-kyc-form.spec.ts
│   │   ├── supplier-bulk-upload.spec.ts
│   │   ├── supplier-voice-to-catalog.spec.ts ← MOVE from cross-cutting/voice-to-catalog.spec.ts
│   │   └── supplier-orders-payouts.spec.ts   ← CREATE
│   ├── logistics/
│   │   ├── shipping-quote.spec.ts
│   │   ├── logistics-country-switching.spec.ts
│   │   ├── fulfillment-role-flow.spec.ts
│   │   ├── parcel-verification.spec.ts
│   │   └── logistics-dashboard.spec.ts       ← CREATE
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

**Total: 62 spec files** (matches benchmark requirement)

---

## 7 · Execution Order

1. **DELETE** 12 extra files
2. **RENAME** 2 files (supplier-product-upload-complete → supplier-product-upload, supplier-kyc-form → supplier-kyc)
3. **MOVE** 4 files from cross-cutting to correct module directories
4. **CREATE** 6 missing stub files
5. **VERIFY** final count = 62 files

---

## 8 · What Remains After Rearrangement

After the file system is correctly aligned, the remaining work to complete the browser test is:

### 8.1 Helper Files (already complete)

| File | Status |
|---|---|
| `_browser_test/src/auth.ts` | Complete — 159 lines, all bootstrap helpers |
| `_browser_test/src/api.ts` | Complete — 355 lines, all CRUD helpers |
| `_browser_test/src/ui.ts` | Complete — 65 lines, ZOZI selectors |
| `_browser_test/playwright.config.ts` | Complete — 30 lines, reporters, env vars |
| `_browser_test/global-setup.ts` | Exists |
| `_browser_test/global-teardown.ts` | Exists |
| `_browser_test/scripts/run-pipeline.ps1` | Exists |

### 8.2 Spec File Implementation Work

| Category | Action | Count |
|---|---|---|
| Port from `frontend/web_app/e2e/` | Copy existing specs, update imports to use `_browser_test/src/` | ~40 files |
| Write new from scratch | Per Section 5 of PROMPT_BROWSER_TEST.md | ~12 files |
| Fix imports | Replace `frontend/web_app/e2e/helpers/` with `_browser_test/src/` | All ported files |
| Update PROMPT_BROWSER_TEST.md | Section 2 (Current State), Section 13 (File Inventory) | 1 file |

### 8.3 Environment Setup

| Step | Status |
|---|---|
| `config/stack.env.ps1` exists | ✓ Already exists |
| Playwright browsers installed | Pending |
| Backend booted | Pending |
| Frontend dev server | Pending |
| Valkey running | Pending |
| Postgres running | Pending |

---

## 9 · Risks & Notes

1. **Moved files may need import updates** — `verify-8-fixes.spec.ts` and `security.spec.ts` currently in `cross-cutting/` may import from `../` paths; after moving to `admin/`, relative imports may break.
2. **Renamed files break references** — Any test importing `supplier-product-upload-complete` or `supplier-kyc-form` must be updated.
3. **New stub files are empty** — The 6 CREATE files must be populated with actual test implementations.
4. **Source of truth is `frontend/web_app/e2e/`** — Never modify files there; only port from them.

---

*Plan version: 1.0 — 2026-10-02*
