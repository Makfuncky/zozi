# Admin Panel Audit And Optimization

## Executive Summary

The admin surface has now converged on a clearer model:

1. Canonical workspaces own real management flows.
2. The dashboard owns overview, launch points, and a small number of native tabs.
3. Legacy routes remain in place as compatibility redirects so existing deep links do not break.

The main risk is no longer missing functionality. It is architecture drift between documentation, navigation metadata, and the actual route tree. This document reflects the current route ownership implemented in the frontend.

## Current Canonical Model

### Canonical workspaces

| Canonical route | Ownership | Notes |
| --- | --- | --- |
| `/admin/dashboard` | Overview, workspace launcher, `insights`, `exports` | `overview` is the default dashboard view; legacy duplicated tabs redirect out. |
| `/admin/analytics` | Analytics and KPI exploration | Primary analytics workspace. |
| `/admin/users` | Customer account management | Primary user-management workspace. |
| `/admin/suppliers` | Supplier onboarding, verification, documents, comparison | Owns supplier-specific specialist sections. |
| `/admin/orders` | Order operations, returns, barcode workflows | Canonical order operations workspace. |
| `/admin/products` | Catalog moderation and verification | Owns verification deep links. |
| `/admin/promotions` | Banners, coupons, flash sales | Canonical promotions hub. |
| `/admin/logistics` | Shipment operations and partner governance | Canonical logistics hub. |
| `/admin/invoices` | Invoice review | Standalone operational page. |
| `/admin/payments` | Payment gateway runtime control | Standalone settings page. |
| `/admin/finance` | Cash management, payouts, bank-account review | Canonical finance hub. |
| `/admin/email` | Lifecycle email and campaign operations | Standalone messaging workspace. |
| `/admin/tickets` | Support queue management | Standalone governance workspace. |
| `/admin/audit-logs` | Audit and security visibility | Standalone governance workspace. |
| `/admin/moderation` | Product moderation queue | Standalone governance workspace. |
| `/admin/staff` | Staff accounts, permissions, org access | Standalone governance workspace. |
| `/admin/barcode` | Dedicated scan workflow | Still has a real page implementation, but navigation now prefers `/admin/orders?section=barcode`. |
| `/admin/login` | Admin authentication | Not part of workspace navigation. |

### Canonical section ownership

| Parent workspace | Sections it owns |
| --- | --- |
| `/admin/dashboard` | `overview`, `insights`, `exports` |
| `/admin/suppliers` | `documents`, `compare` |
| `/admin/orders` | `returns`, `barcode` |
| `/admin/products` | `verification` |
| `/admin/promotions` | `banners`, `coupons`, `flash-sales` |
| `/admin/logistics` | `shipments`, `partners` |
| `/admin/finance` | `finance`, `payouts`, `bank-accounts` |
| `/admin/staff` | `permissions` |

## Compatibility Redirect Routes

These routes remain in the tree to preserve bookmarks, links, and older navigation paths, but they are no longer the canonical homes for the domain.

| Legacy route | Redirect target | Status |
| --- | --- | --- |
| `/admin/banners` | `/admin/promotions?section=banners` | Compatibility wrapper |
| `/admin/coupons` | `/admin/promotions?section=coupons` | Compatibility wrapper |
| `/admin/flash-sales` | `/admin/promotions?section=flash-sales` | Compatibility wrapper |
| `/admin/logistics-partners` | `/admin/logistics?section=partners` | Compatibility wrapper |
| `/admin/bank-accounts` | `/admin/finance?section=bank-accounts` | Compatibility wrapper |
| `/admin/payouts` | `/admin/finance?section=payouts` | Compatibility wrapper |
| `/admin/returns` | `/admin/orders?section=returns` | Compatibility wrapper |
| `/admin/product-verification` | `/admin/products?section=verification` | Compatibility wrapper |
| `/admin/supplier-documents` | `/admin/suppliers?section=documents` | Compatibility wrapper |
| `/admin/exports` | `/admin/dashboard?tab=exports` | Compatibility wrapper |

## Dashboard Tab Inventory

Only three dashboard tabs are still native to the dashboard page.

| Dashboard tab | Current owner | Behavior |
| --- | --- | --- |
| `overview` | Dashboard | Native dashboard view with KPIs, workspace cards, and operational shortcuts. |
| `insights` | Dashboard | Native dashboard analysis tab. |
| `exports` | Dashboard | Native dashboard export panel. |

The following legacy dashboard tabs now redirect to canonical workspaces through `ADMIN_LEGACY_DASHBOARD_REDIRECTS`:

- `analytics`
- `users`
- `suppliers`
- `orders`
- `products`
- `audit`
- `banner`
- `coupons`
- `flash-sales`
- `logistics-partners`
- `logistics`
- `finance`
- `staff`
- `moderation`
- `tickets`
- `payouts`
- `supplier-documents`
- `hierarchy`
- `returns`
- `barcode`
- `product-verification`
- `compare`

## Navigation Alignment

`frontend/web_app/src/lib/adminPanelConfig.ts` is now the source of truth for primary navigation.

- Primary nav points to canonical workspaces or canonical section URLs.
- Redirect wrappers exist only for compatibility, not as preferred destinations.
- Dashboard shortcut cards are derived from the same metadata so titles and descriptions stay aligned.
- Dashboard shortcut cards now reuse the same permission/role access helper as the sidebar, so restricted roles do not see launchers for admin-only workspaces they cannot open.

Examples of this alignment:

- `Returns` points to `/admin/orders?section=returns`, not `/admin/returns`.
- `Barcode / QR` points to `/admin/orders?section=barcode`, even though `/admin/barcode` still exists.
- `Verifications` points to `/admin/products?section=verification`, not `/admin/product-verification`.
- `Exports` points to `/admin/dashboard?tab=exports`, not `/admin/exports`.

## Current Findings

### What has been consolidated successfully

- Promotions is a real hub and owns banners, coupons, and flash sales.
- Logistics is a real hub and owns shipment operations plus partner management.
- Finance is a real hub and owns payouts and bank-account review.
- Orders and products now serve as the canonical homes for returns, barcode, and verification entry points.
- Dashboard duplication has been reduced to overview plus two native specialist tabs.

### Remaining partial duplication

- `/admin/barcode` still has a dedicated implementation while navigation prefers the orders hub entry point.
- Some specialist experiences are still represented both as section deep links and as retained compatibility pages to avoid breaking old links.
- Mobile admin still deserves a follow-up IA pass because its dashboard shell is not yet as consolidated as the web canonical workspace model.

### Mobile-vs-web parity findings

- Mobile `app/admin/dashboard.tsx` still behaves like an all-in-one legacy admin shell with tabs for `analytics`, `users`, `suppliers`, `orders`, `products`, `moderation`, `coupons`, `tickets`, `flash-sales`, `audit`, `hierarchy`, `staff`, `compare`, `insights`, and `tools`.
- Web canonical navigation no longer uses the dashboard as that kind of omnibus control surface; it treats `/admin/dashboard` as overview plus launcher while domain work happens in dedicated workspaces from `adminPanelConfig.ts`.
- Mobile still keeps several specialist top-level routes that web now treats as compatibility or section entry points, including `banners`, `coupons`, `flash-sales`, `logistics-partners`, `returns`, `product-verification`, and `barcode`.
- Mobile currently has dedicated screens for `email`, `invoices`, `exports`, `bank-accounts`, and the specialist pages above, but it does not expose the same canonical hub structure the web admin now uses for `promotions`, `logistics`, `finance`, `payments`, `commission`, or `staff`.
- The most visible parity gap is that web admin leads users into a smaller set of domain hubs with section deep links, while mobile admin still asks staff to navigate a mixed model of dashboard tabs plus legacy one-off pages.

## Recommended Next Optimizations

### Short term

- Extract a shared `AdminDataTableShell` for search, filter, table, and bulk-action pages.
- Extract a shared `AdminApprovalQueue` for review-heavy flows such as supplier verification, bank accounts, and product verification.
- Decide whether `/admin/barcode` should remain a real page or become a pure compatibility redirect to the orders workspace.
- Start collapsing the mobile dashboard tabs into the same canonical hub model used on web, beginning with promotions/logistics and the finance stack.

### Mid term

- Standardize section navigation patterns across hub pages so each canonical workspace exposes the same deep-link semantics.
- Add route-level instrumentation for the heaviest admin workspaces.
- Reduce remaining duplicated fetch and table state patterns across admin pages.

### Long term

- Move from many top-level routes toward fewer durable domain workspaces with stable section URLs.
- Keep compatibility redirects in place until analytics confirm old routes are no longer used.

## Files Updated As Part Of This Consolidation Pass

- `frontend/web_app/src/lib/adminPanelConfig.ts` — canonical navigation metadata and legacy dashboard tab redirects.
- `frontend/web_app/src/app/admin/dashboard/page.tsx` — dashboard reduced to overview plus native tabs.
- `frontend/web_app/src/components/AdminRouteRedirect.tsx` — shared redirect wrapper for compatibility routes.
- `frontend/web_app/src/app/admin/banners/page.tsx` — compatibility redirect.
- `frontend/web_app/src/app/admin/coupons/page.tsx` — compatibility redirect.
- `frontend/web_app/src/app/admin/flash-sales/page.tsx` — compatibility redirect.
- `frontend/web_app/src/app/admin/logistics-partners/page.tsx` — compatibility redirect.
- `frontend/web_app/src/app/admin/bank-accounts/page.tsx` — compatibility redirect.
- `frontend/web_app/src/app/admin/payouts/page.tsx` — compatibility redirect.
- `frontend/web_app/src/app/admin/returns/page.tsx` — compatibility redirect.
- `frontend/web_app/src/app/admin/product-verification/page.tsx` — compatibility redirect.
- `frontend/web_app/src/app/admin/supplier-documents/page.tsx` — compatibility redirect.
- `frontend/web_app/src/app/admin/exports/page.tsx` — compatibility redirect.

## Admin Shell Pattern & Convention Checklist

Apply these rules whenever adding or editing a page under `frontend/web_app/src/app/admin/`.

### Page Shell

| Before | After |
|---|---|
| `<PanelHero title="..." />` inside `PanelContent` | Removed — `AdminLayout title="..."` is the single page heading |
| Duplicate `<h1>` / `<h2>` eyebrow heading inside the content body | Removed — only section sub-headings (`text-sm font-bold`) inside cards are kept |
| `"Admin Workspace"` eyebrow label above staff/finance titles | Removed |
| `<PanelContent className="space-y-8 ...">` large spacing | `space-y-4` or `space-y-6` — no more than `space-y-6` |

### Tabs

| Before | After |
|---|---|
| Bespoke tab arrays with per-page styles | Shared `<PanelTabs items={SECTIONS} value={section} onChange={...} />` |
| Tabs floated inside the content | Wrapped in `<div className="theme-card rounded-xl border p-2">` control band |

### Stats / KPI Cards

| Before | After |
|---|---|
| `<motion.div>` framer-motion wrappers on stat cards | Plain `<div>` — no entrance animations |
| `p-6` padding on stat cards | `px-3 py-2.5` (compact) |
| `text-3xl` numbers | `text-lg` or `text-2xl` max |
| Hard `w-full` grid always split into 4 columns | `grid gap-2 sm:grid-cols-2 xl:grid-cols-4` — mobile-first |

### Tables

| Before | After |
|---|---|
| Bespoke `<table>` with custom pagination in each page | Shared `<EnterpriseDataTable>` from `@zozi/shared` |
| `rounded-3xl` on table wrapper | `rounded-xl` |
| `motion.tr` row animations | Plain `<tr>` |
| `border-b border-border bg-surface-1` header styles | `EnterpriseDataTable` handles header internally |
| Inline detail panel rendered **below the entire table** (external sibling `<div>`) | `expandedRowKey` + `expandedRowRenderer` prop on `EnterpriseDataTable` — renders inline below the clicked row |

**EnterpriseDataTable inline row expansion pattern:**
```tsx
<EnterpriseDataTable
  ...
  expandedRowKey={focusedKey ?? undefined}
  expandedRowRenderer={(row) => (
    <div className="p-4">
      {/* detail content */}
    </div>
  )}
/>
```
Remove any external `{focusedRow ? <div>...</div>}` sibling panel.

### Control Rows (filters, search, action buttons)

| Before | After |
|---|---|
| Search + filters stacked in `space-y-4` separate sections | Single `flex flex-wrap items-center gap-2` control row inside or above the table toolbar |
| Refresh button at the very top in its own row | Inline in the control band next to filters, or as `toolbarSlot` on `EnterpriseDataTable` |
| `focus:ring-2 focus:ring-primary/30` on inputs | `focus:border-primary focus:outline-none` — consistent with shared input style |

### Loading States

| Before | After |
|---|---|
| `<div className="p-12 text-center text-xs text-text-muted">Loading...</div>` | Use `<PanelLoadingState />` from `@/components/PanelPage` when a dedicated spinner is needed |

### Mobile Responsiveness Checklist

- [ ] Stats grids: `grid gap-2 sm:grid-cols-2 xl:grid-cols-4` (never fixed columns at all widths)
- [ ] Multi-column info grids: default 1 col, split at `lg:` or `xl:`
- [ ] Control rows: `flex flex-wrap gap-2` — never `flex` without `flex-wrap`
- [ ] Select inputs with long content: `min-w-0` on parent or `w-full sm:w-auto` on the select
- [ ] `EnterpriseDataTable` mobile: always provide `mobileCardRenderer` for data-dense tables

### Page Implementation Status

| Page | PanelHero removed | Shared tabs | EnterpriseDataTable | Motion removed |
|---|:---:|:---:|:---:|:---:|
| Orders | ✓ | — | partial | — |
| Products | ✓ | — | — | — |
| Users | ✓ | — | — | — |
| Suppliers | ✓ | ✓ | ✓ | — |
| Payments | ✓ | — | — | — |
| Email | ✓ | — | — | — |
| Commission | ✓ | — | — | — |
| Tickets | ✓ | — | — | — |
| Promotions | ✓ | — | — | — |
| Audit Logs | ✓ | — | — | — |
| Finance | ✓ | ✓ | ✓ | — |
| Logistics | ✓ | ✓ | ✓ | — |
| Staff | ✓ | ✓ | ✓ | — |
| Invoices | ✓ | — | bespoke* | ✓ |
| Returns | redirect only | — | — | — |
| Barcode | ✓ | — | n/a (scanner) | — |

*Invoices uses a bespoke table; migration to `EnterpriseDataTable` deferred.




-----------------------------

# Admin Shell Pattern → See ADMIN_PANEL_AUDIT_AND_OPTIMIZATION.md

**This document has been consolidated into [ADMIN_PANEL_AUDIT_AND_OPTIMIZATION.md](ADMIN_PANEL_AUDIT_AND_OPTIMIZATION.md).**

All admin page shell patterns, convention checklists, and implementation standards are now documented in the main admin panel reference guide.

For details, see:
- [Admin Shell Pattern & Convention Checklist](ADMIN_PANEL_AUDIT_AND_OPTIMIZATION.md#admin-shell-pattern--convention-checklist)
- [Page Shell](ADMIN_PANEL_AUDIT_AND_OPTIMIZATION.md#page-shell)
- [Mobile Responsiveness Checklist](ADMIN_PANEL_AUDIT_AND_OPTIMIZATION.md#mobile-responsiveness-checklist)
