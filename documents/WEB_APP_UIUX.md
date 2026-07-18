# Web App UI/UX Inventory (Canonical)

Last updated: 2026-05-08

## Purpose

This inventory documents the canonical UI/UX architecture for `frontend/web_app` and its shared dependencies.

It is implementation-oriented and avoids speculative design notes.

## 1) Theme and Design Token Sources

### Primary web theme files

- `frontend/web_app/src/styles/globals.css`
  - CSS variables for surface/text/brand tokens, glass layers, button utilities, and shell styles.
- `frontend/web_app/tailwind.config.js`
  - Tailwind token bindings to CSS variables and semantic colors.
- `frontend/web_app/src/app/layout.tsx`
  - Global font registration, anti-flash scripts, app shell, and providers.
- `frontend/web_app/src/components/ThemeProvider.tsx`
- `frontend/web_app/src/components/ThemeToggle.tsx`

### Shared token source (web + mobile)

- `frontend/shared/src/theme.ts`
  - Brand colors, light/dark palettes, gradients, spacing, radius, and typography tokens.

## 2) Canonical Visual Direction

Current implemented direction:

- Brand-primary: lime spectrum (`#32CD32`, `#7CFC00`)
- Accent: yellow spectrum (`#FFD700`, `#FFEA00`)
- Dark-mode base: black and charcoal surfaces
- Light-mode base: white and neutral light surfaces
- Frosted glass panel utilities available in global CSS

## 3) Core Reusable UI Layers

### Layout and shell components

- `frontend/web_app/src/components/Header.tsx`
- `frontend/web_app/src/components/Footer.tsx`
- `frontend/web_app/src/components/AdminLayout.tsx`
- `frontend/web_app/src/components/SupplierLayout.tsx`
- `frontend/web_app/src/components/LogisticsPartnerLayout.tsx`

### Foundation components

- `frontend/web_app/src/components/Button.tsx`
- `frontend/web_app/src/components/Input.tsx`
- `frontend/web_app/src/components/FilterSearchBar.tsx`
- `frontend/web_app/src/components/BulkActionBar.tsx`
- `frontend/web_app/src/components/LoadingSkeleton.tsx`
- `frontend/web_app/src/components/ErrorAlert.tsx`

### Catalog and conversion components

- `frontend/web_app/src/components/ProductCard.tsx`
- `frontend/web_app/src/components/ProductGrid.tsx`
- `frontend/web_app/src/components/QuickViewModal.tsx`

## 4) High-Impact Route Surfaces

### Customer

- `frontend/web_app/src/app/page.tsx`
- `frontend/web_app/src/app/products/page.tsx`
- `frontend/web_app/src/app/products/[id]/page.tsx`
- `frontend/web_app/src/app/cart/page.tsx`
- `frontend/web_app/src/app/checkout/page.tsx`
- `frontend/web_app/src/app/tracking/[id]/page.tsx`

### Admin

- `frontend/web_app/src/app/admin/dashboard/page.tsx`
- `frontend/web_app/src/app/admin/staff/page.tsx`
- `frontend/web_app/src/app/admin/logistics/page.tsx`
- `frontend/web_app/src/app/admin/logistics-partners/page.tsx`

### Supplier and logistics partner

- `frontend/web_app/src/app/supplier/dashboard/page.tsx`
- `frontend/web_app/src/app/logistics-partner/dashboard/page.tsx`
- `frontend/web_app/src/app/logistics-partner/shipments/page.tsx`

## 5) UX Guardrails

- Keep search bar behavior unchanged unless there is a functional bug.
- Prefer shared token classes/utilities over page-specific color literals.
- Keep cart and checkout styling and interaction patterns aligned with theme tokens.
- Reuse shared status-chip helpers from `frontend/shared/src/statusColors.ts`.
- Maintain parity with shared components and `.web.tsx` fallbacks when using shared UI in Next.js.

## 6) Test Coverage Anchors

- `frontend/web_app/src/__tests__/pages/products.test.tsx`
- `frontend/web_app/src/__tests__/pages/checkout.test.tsx`
- `frontend/web_app/src/__tests__/pages/adminLogisticsPages.test.tsx`
- `frontend/web_app/src/__tests__/pages/adminStaffPage.test.tsx`
- `frontend/web_app/src/__tests__/pages/logisticsPartnerPages.test.tsx`

## 7) Change Workflow for UI Work

1. Update shared tokens first when change is cross-platform.
2. Update web global styles and component-level classes.
3. Update target route surfaces.
4. Re-run route and component tests.
5. Re-run visual smoke checks in light and dark mode.
6. Update migration notes/report docs.

## 8) Design System Governance

This section defines the shared UI/UX direction and implementation governance for web and mobile applications.

### Platform Scope

- Web: `frontend/web_app`
- Mobile: `frontend/mobile_app`
- Shared: `frontend/shared`

### Design System Direction

- Light mode foundation: white/neutral surfaces, dark text, glass overlays
- Dark mode foundation: black/charcoal surfaces, light text, glass overlays
- Primary CTA color family: lime (`#32CD32`, `#7CFC00`)
- Secondary accent family: yellow (`#FFD700`, `#FFEA00`)

### Cross-Platform Consistency Rules

1. Shared tokens in `frontend/shared/src/theme.ts` are the cross-platform baseline.
2. Any change in shared tokens requires validation on both web and mobile.
3. Shared UI components must keep platform-specific fallbacks where native APIs are unavailable on web.
4. Keep interaction semantics aligned for cart, checkout, logistics tracking, and admin data workflows.

### Functional Guardrails

- Keep the existing search bar system behavior stable unless there is a bug.
- Prioritize cart and checkout UX consistency improvements across web and mobile.
- Preserve accessibility fundamentals: contrast, focus visibility, readable typography, and keyboard navigation where applicable.

### Route Priority Matrix

**Priority A (conversion-critical):**
- Home
- Product list and product detail
- Cart
- Checkout

**Priority B (operations-critical):**
- Admin dashboard and staff workspace
- Admin logistics workspace
- Logistics-partner dashboard and shipments

**Priority C (supporting):**
- Profile, help, tickets, archive, and secondary content routes

### Implementation Workflow

1. Update shared tokens/components first when change is cross-platform.
2. Update web and mobile route surfaces.
3. Update or add platform fallbacks (`*.web.tsx` / native variants) as needed.
4. Run impacted test suites.
5. Run visual QA in light and dark modes on desktop and mobile breakpoints.
6. Update migration notes/report docs.

### Testing and QA Expectations

- Validate component-level tests for changed shared modules.
- Validate route-level tests for changed screens.
- Validate no regressions in admin workflows (staff/logistics) and customer flows (cart/checkout).
- Confirm no build/type failures after token or shared component changes.

## 9) Migration Status & Tracking

### Completed Foundations

- Shared theme tokens exist in `frontend/shared/src/theme.ts`.
- Web global theme variables and glass utilities are centralized in `frontend/web_app/src/styles/globals.css`.
- Web layout loads brand typography and theme bootstrap in `frontend/web_app/src/app/layout.tsx`.
- Shared web fallbacks for native components exist (for example `*.web.tsx` in `frontend/shared/src/components/ui/`).
- Admin and logistics web surfaces are actively wired to themed component system.

### Migration Guardrails

- Do not change search bar interaction model unless a bug requires it.
- Keep cart and checkout visual language aligned across web and mobile.
- Keep shared token changes synchronized between web and mobile consumers.
- Avoid hardcoded one-off color literals in route pages where utility tokens already exist.

### Active Focus Areas

1. Keep high-traffic routes visually consistent:
   - Products, product detail, cart, checkout
2. Keep admin consistency:
   - Staff workspace, logistics workspace, dashboard tabs
3. Keep logistics-partner views consistent:
   - Dashboard, shipments, payouts, profile

### Known Risks

- Shared component changes can break either web or mobile when platform fallbacks are incomplete.
- Route pages with mixed legacy classes may drift from token-driven style.
- Test fixtures may still assert outdated color semantics.

### Migration Validation Checklist

**Web:**
- Type check: `frontend/web_app -> npx tsc --noEmit`
- Unit tests: targeted page suites and full suite as needed
- Visual check: light and dark themes on desktop and mobile widths

**Mobile:**
- Unit tests: `frontend/mobile_app/lib/__tests__/`
- Navigation/route smoke checks on core commerce and logistics screens

## 10) Migration Report

**Report date:** 2026-05-08

### Executive Summary

The codebase has an established shared design-token foundation and active glass/lime/yellow theming across web and mobile surfaces.

Migration status:
- Foundation: complete
- Broad rollout: active
- Final polish and parity checks: ongoing

### High-Impact Surfaces Covered

**Customer:**
- Products and product detail
- Cart and checkout
- Tracking and order-facing status surfaces

**Admin:**
- Staff management workspace
- Logistics management workspace

**Logistics partner:**
- Dashboard, shipments, payouts, profile workflows

### Remaining Work Categories

1. Visual parity tuning between route-level legacy styles and token-driven styles.
2. Continued cleanup of route-specific color literals in favor of semantic utilities.
3. Ongoing responsive and accessibility verification for mobile breakpoints and keyboard flows.
4. Regression coverage updates when UI behavior contracts change.

### Validation Guidance

Use these checks for each migration batch:

- Web type check: `frontend/web_app -> npx tsc --noEmit`
- Web tests: targeted route suites plus full run when shared components are modified
- Mobile tests: affected screen suites in `frontend/mobile_app/lib/__tests__/`
- Visual QA: desktop and mobile viewport checks in both light and dark themes



# ____________________________________________________________________________
# New Detail
# ____________________________________________________________________________



I have all the evidence needed. The shared `ui/shared` primitives (`Modal`, `Table`, `Badge`, `StatusBadge`, `LoadingSkeleton`, `EmptyState`) exist and are well-built, but the three panels barely use them. Here is the detailed audit.

---

# Admin / Supplier / Logistics Panels — Frontend Inconsistency & Improvement Audit

## Architecture context (the good foundation)
All three panels already share one shell (`PanelShell.tsx`) and a primitive library (`PanelPage.tsx` + `components/ui/shared/`: `Modal`, `Table`, `Badge`, `StatusBadge`, `LoadingSkeleton`, `EmptyState`). The infrastructure for consistency **already exists** — the problem is that individual pages ignore it and hand-roll their own versions. That is the root cause of nearly every inconsistency below.

| Shared asset | Used by | Ignored by |
|---|---|---|
| `PanelHero` | products/add, reports, credibility, labels, profile (logi) | **all three dashboards**, supplier products/analytics/support, logistics shipments/scan/analytics |
| `PanelLoadingState` | few pages (labels, credibility, admin payments/finance) | most pages hand-roll `animate-pulse` |
| `ui/shared/Modal` | admin permissions, employees (partially) | admin suppliers/staff/promotions, supplier products/add (6 dialogs), logistics ScanModal |
| `ui/shared/Table` | admin promotions/employees | every other table (≈40 raw `<table>`) |
| `ui/shared/Badge` / `StatusBadge` | payouts | most pages hand-roll status pills |
| `ui/shared/EmptyState` | admin promotions/employees | treasury, countries, payouts, support |

---

## 1. Design tokens — `danger` vs `error` (cross-cutting, highest severity)
The canonical token is **`danger`** (`--color-danger`, `.text-danger` at globals.css:4297; `Badge`/`StatusBadge` use `danger`; `PanelShell` logout uses `text-danger`). A parallel **`error`** alias also exists, but `text-error` is **not in the Tailwind safelist** (tailwind.config.js:275 safelists only `text-danger/*`). So `text-error` works only via fragile JIT string-scanning.

- Logistics dashboard `dashboard/page.tsx:149,264` → `bg-error/10 text-error`
- `shipments/page.tsx:409`, `scan/page.tsx:122`, `payouts/FinanceSection.tsx:71` → `text-error`
- Meanwhile the SAME panel uses `text-danger` at `shipments/page.tsx:137`, `payouts/page.tsx:196`, `profile/page.tsx:236`, and `error.tsx`.

**Fix:** standardize on `text-danger`/`bg-danger/*` everywhere; remove `text-error` usage (or add to safelist and deprecate). Add a lint rule / grep gate.

## 2. Raw palette classes instead of tokens
- Admin: `countries/CountryLedgerTable.tsx:100-119` → `bg-purple-500/10 text-purple-400`, `bg-amber-500/10`, `bg-cyan-500`, `bg-orange-500`; `logistics/LogisticsPartnersPanel.tsx:1419` → `bg-amber-500/10 text-amber-700`; chart palettes `countries/page.tsx:3258` → `colors={["#22c55e","#6366f1","#f59e0b"]}`, `color="#3b82f6"`, `bg_color || "#0f172a"`.
- Supplier: `payouts/page.tsx:442-443` → **malformed classes** `… /20 text-success hover:/30` (missing `bg-` prefix) — these are no-ops, so Paid/Overdue buttons render with no background; `profile/page.tsx:1132` hard-coded `from-primary via-brand to-accent` gradient; `routes/page.tsx` (logi) `:89` → `text-brand` while rest of app uses `text-primary`.
- `markerColor="#3b82f6"` hard-coded in `logistics-partner/shipments/page.tsx:536` and `supplier/orders/[id]/page.tsx:424` (maps — arguably acceptable, but should come from a token map).

Pure hex is acceptable only for canvas/print/maps (`products/add` canvas fills, `labels` print).

## 3. Page-header divergence (the three dashboards)
`PanelShell` already renders the `<h1>` title in the topbar (PanelShell.tsx:281). Yet:
- **All three dashboards hand-roll a second `<h1>` + custom Refresh button** inside content (admin `dashboard/page.tsx:158`, supplier `dashboard/page.tsx:111`, logistics `dashboard/page.tsx:123`) → stacked duplicate titles.
- Supplier `products`, `analytics`, `support`, `payouts`, `profile`, and logistics `shipments`/`scan`/`analytics` also hand-roll headers.
- Only ~5 admin pages use `PanelHero`; logistics `profile` uses it correctly.

**Fix:** delete the in-page `<h1>` from dashboards (topbar already shows it) OR adopt `PanelHero` consistently and pass `headerMode="compact"` so the shell doesn't double-render. Add a `PanelSection` component for the repeated hand-rolled `<h2 className="text-sm font-bold text-text">` (treasury has 25+, countries 20+).

## 4. Loading states — three patterns
- Hand-rolled `<div className="h-28 animate-pulse">` with **arbitrary heights** (`h-16`/`h-24`/`h-28`/`h-48`) — admin command-center tabs, supplier dashboard/analytics/reports/payouts, logistics dashboard/shipments (shipments has **no skeleton at all**, just absent table), logistics analytics uses a bare `Loader2` spinner, logistics payouts uses plain text "Loading…".
- Shared `PanelLoadingState` used only in a minority.

**Fix:** route every page through `PanelLoadingState` (or `LoadingSkeleton`); one skeleton block size.

## 5. Modals — three patterns, shared `Modal` ignored
- Hand-rolled `fixed inset-0 z-50 … theme-overlay` inline with `motion.div` (admin suppliers/staff/promotions/payments/products).
- `theme-modal-card` token (admin treasury/promotions).
- Shared `ui/shared/Modal` (admin permissions/employees).
- Inconsistent: `rounded-2xl` (suppliers) vs `rounded-xl` (promotions); only some set `role="dialog" aria-modal`; supplier `products/add` hand-rolls **6 separate dialogs** (lines 1624+); logistics `ScanModal` is a one-off.

**Fix:** adopt `ui/shared/Modal` + `ModalFooter` everywhere; delete the hand-rolled wrappers.

## 6. Status badges / tables — fragmented
- Two badge systems: `theme-chip-*` (admin suppliers/users/dashboard) vs raw `bg-success/10 text-success` spans (admin products/categories/orders, supplier products/payouts, logistics dashboard).
- **Mapping conflict:** logistics dashboard treats `in_transit`/`shipped` as **info** (`bg-info/10`), but `shipments/page.tsx:126` treats the same statuses as **warning** (`bg-warning/10`). The same shipment shows different colors on two pages.
- Pill shape split: `rounded-full` (dashboard, shipments) vs `rounded` (logistics `routes/page.tsx:133`) vs `rounded-lg` (payouts `theme-chip-*`).
- Table styling: header bg/font-size/border vary (`text-xs`+`font-mono` dashboard vs `text-sm`+`bg-surface-2` shipments vs `bg-surface-2/40` payouts).

**Fix:** one `StatusBadge` with a canonical status→variant map (reconcile `in_transit` = info); wrap tables in `ui/shared/Table`.

## 7. Responsiveness / shell gaps
- **`logistics-partner/routes/page.tsx:67` does NOT use `LogisticsPartnerLayout`** — wraps content in a bare `<div className="min-h-screen bg-surface-base">`, so it has no sidebar, topbar, mobile drawer, or `max-w-450` wrapper. It's a desktop-only orphan page. Confirmed unused imports (`Plus`, `Map`, `Loader2`, `AlertCircle`).
- Fixed widths: logistics `scan/page.tsx:106` `w-64` input; `min-w-[800px]`/`min-w-[860px]` in admin countries.
- Supplier `Header.tsx` currency/Country/Locale were already wrapped `hidden md:inline-flex` (mobile overflow fixed in prior session).

## 8. Dead / duplicated code
- Admin `dashboard/page.tsx:19` — large commented-out import block; `AdminLayout.tsx` computes `currentTab` (useSearchParams) but **never uses it** for render (dead).
- `payouts/page.tsx` (logi) defines a redundant local `Fragment` wrapper; `payouts/page.tsx` + `FinanceSection.tsx` duplicate `titleCase`/`normalizeStatus` helpers.
- Supplier `StatCard` duplicated verbatim in `dashboard/page.tsx:49` and `reports/page.tsx:71`.
- Icon import inconsistency: `videos/upload/page.tsx`, logistics `login`/`register`, import `lucide-react` directly instead of `@/lib/icons`; `profile` pages carry many unused icon imports.
- `orders/page.tsx:69` typo'd state setter `setUpdateingShipmentId`.
- `promotions/FlashSalesPanel.tsx:188` passes `title=` to `PanelContent`, which has **no `title` prop** (silently ignored).

## 9. Nav-group structure divergence (minor)
Admin uses 5 groups (Overview/Commerce/Operations/Growth/Governance); Supplier & Logistics use 4 (Overview/Operations/Finance/Account). Not a bug, but means the "Finance" vs "Operations" grouping differs between panels — worth aligning if a unified look is the goal.

---

## Prioritized improvement plan
1. **Token sweep**: replace `text-error`→`text-danger`, `bg-error/*`→`bg-danger/*`; replace raw `*-500/*` palette classes with `theme-chip-*` / token classes; fix the malformed `payouts/page.tsx:442-443`.
2. **Adopt shared `Modal`** across all three panels (start with the 6 supplier `products/add` dialogs + logistics `ScanModal` + admin suppliers/staff).
3. **Adopt `StatusBadge`** with one canonical status map; reconcile `in_transit` coloring.
4. **Adopt `PanelHero` + `PanelLoadingState`** in all dashboards and list pages; delete duplicate in-page `<h1>`.
5. **Wrap orphan `routes/page.tsx`** in `LogisticsPartnerLayout`.
6. **Extract shared `StatCard`** to `components/ui`; delete duplicate in dashboard/reports.
7. **Cleanup**: remove dead `currentTab`/`commented import`, redundant `Fragment`, duplicate helpers, unused imports, fix typo; normalize icon imports to `@/lib/icons`.

No code was changed — this is a research/audit report. The shared component library already covers every gap; the work is mostly migration + a token-usage lint gate.


