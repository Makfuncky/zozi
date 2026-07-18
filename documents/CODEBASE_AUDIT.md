# Panel UI/UX Codebase Audit

Last updated: April 6, 2026
Scope: `frontend/web_app/src/app/admin`, `frontend/web_app/src/app/supplier`, `frontend/web_app/src/app/logistics-partner`, `frontend/web_app/src/components`, `frontend/shared/src`

## Component Hierarchy Tree

### Admin
- `admin/layout.tsx`
- `admin/dashboard/page.tsx`
  - `AdminLayout`
  - `InsightsTab`
  - `ExportsPanel`
- `admin/orders/page.tsx`
  - `AdminLayout`
  - `ColumnVisibilityPanel`
  - `AdvancedFilterPanel`
  - `InlineActionButtons`
  - `BulkActionBar`
  - `QuickDetailModal`
- `admin/users/page.tsx`
  - `AdminLayout`
  - `ColumnVisibilityPanel`
  - `InlineActionButtons`
  - `BulkActionBar`
- `admin/tickets/page.tsx`
  - `AdminLayout`
  - `dashboard/tabs/TicketsTab`
  - `BulkActionBar`
- Additional enterprise-relevant roots:
  - `admin/finance/page.tsx`
  - `admin/logistics/page.tsx`
  - `admin/logistics-partners/page.tsx`
  - `admin/payouts/page.tsx`
  - `admin/products/page.tsx`
  - `admin/suppliers/page.tsx`

### Supplier
- `supplier/layout.tsx`
  - `DensityProvider`
- `supplier/dashboard/page.tsx`
  - `SupplierLayout`
  - onboarding, credibility badge, alert widgets
- `supplier/orders/page.tsx`
  - `SupplierLayout`
  - `QuickDetailModal`
  - density-aware list/table patterns
- `supplier/products/page.tsx`
- `supplier/returns/page.tsx`
- `supplier/payouts/page.tsx`
  - `FinanceSection`
- `supplier/profile/page.tsx`

### Logistics Partner
- `logistics-partner/layout.tsx`
  - `DensityProvider`
- `logistics-partner/dashboard/page.tsx`
  - `LogisticsPartnerLayout`
  - live shipment analytics widgets
- `logistics-partner/shipments/page.tsx`
  - `LogisticsPartnerLayout`
  - `BulkActionBar`
  - density-aware shipment table
- `logistics-partner/scan/page.tsx`
- `logistics-partner/payouts/page.tsx`
- `logistics-partner/profile/page.tsx`

### Shared UI Surface In Use
- `frontend/web_app/src/components/AdminLayout.tsx`
- `frontend/web_app/src/components/SupplierLayout.tsx`
- `frontend/web_app/src/components/LogisticsPartnerLayout.tsx`
- `frontend/web_app/src/components/DataDensityToggle.tsx`
- `frontend/web_app/src/components/ColumnVisibilityPanel.tsx`
- `frontend/web_app/src/components/AdvancedFilterPanel.tsx`
- `frontend/web_app/src/components/BulkActionBar.tsx`
- `frontend/web_app/src/components/InlineActionButtons.tsx`
- `frontend/web_app/src/components/QuickDetailModal.tsx`
- `frontend/web_app/src/components/Button.tsx`
- `frontend/web_app/src/components/Input.tsx`

### Shared Package Inventory
- `frontend/shared/src` currently contains shared utilities, status colors, permissions, localization, realtime, helpers, and tests.
- Before this pass, `frontend/shared` had no shared React component layer.
- New migration target added in this pass: `frontend/shared/src/components/EnterpriseDataTable.tsx`

## Styling Frameworks And Patterns
- Next.js 16 App Router
- React 19
- Tailwind CSS tooling (`@tailwindcss/postcss`, utility-first classes)
- Framer Motion for animated cards, modals, and sidebars
- Zustand stores for theme, density, auth-adjacent preferences, toasts, notifications
- Theme token classes from `globals.css`:
  - `theme-layout-shell`
  - `theme-sidebar-shell`
  - `theme-topbar`
  - `theme-main-content`
  - `theme-card`
  - semantic chip classes from `@shared/statusColors`

## Reusable Hooks And Utilities

### Web app hooks/stores
- `src/lib/densityContext.tsx`
- `src/lib/themeStore.ts`
- `src/lib/useAuth.tsx`
- `src/lib/toastStore.ts`
- `src/lib/notificationStore.ts`
- `src/lib/localeStore.ts`
- `src/lib/currencyStore.ts`
- `src/lib/api.ts`

### Shared helpers
- `frontend/shared/src/adminPermissions.ts`
- `frontend/shared/src/statusColors.ts`
- `frontend/shared/src/localization.ts`
- `frontend/shared/src/realtime.ts`
- `frontend/shared/src/trackingMap.ts`
- `frontend/shared/src/requestCache.ts`

## Current Styling Inconsistencies
- Panel shells were mostly aligned, but theme switching was not exposed in the admin/supplier/logistics headers consistently before this pass.
- Main content widths differed by panel (`max-w-screen-2xl` vs `max-w-7xl`), which reduced usable density on large operations pages.
- Table-heavy pages repeat bespoke implementations for:
  - search bars
  - pagination controls
  - bulk selection
  - column toggles
  - action button groups
- The app has both shared `Button` / `Input` components and many page-local raw button/input implementations.
- Density support exists, but adoption is uneven. Orders, users, tickets, shipments use it; many other pages still hardcode spacing.
- Theme toggle exists as a component but was not wired into the major panel headers before this pass.

## Performance Bottlenecks
- Large admin and logistics pages still render page-local tables instead of a unified optimized grid.
- Repeated bespoke table code increases render-path complexity and maintenance cost.
- Most large tables paginate correctly, but virtualization is not broadly adopted yet.
- Several dashboards fetch multiple resources client-side in parallel on mount; acceptable today, but this should be monitored for 1000+ operator workflows.
- Many action clusters still render multiple inline buttons per row; compact action menus may be warranted on the heaviest pages.

## Missing Test Coverage
- No dedicated visual regression suite exists for admin, supplier, or logistics dashboards.
- No Lighthouse or performance budget automation is checked into the repo for panel pages.
- No targeted test coverage currently exists for:
  - `DataDensityToggle` behavior across panel pages
  - `ColumnVisibilityPanel`
  - `AdvancedFilterPanel`
  - `QuickDetailModal`
  - shared enterprise table migration target
- Current frontend Jest coverage is strongest for page smoke tests and auth flows, but weaker for reusable enterprise UI primitives.

## Audit Summary
- The codebase is already past the “basic admin panel” stage; it has solid shells, density controls, chips, and bulk actions in key pages.
- The main remaining gap is consistency, not raw capability.
- Highest-value next migration path:
  1. move orders, users, shipments, and tickets onto `EnterpriseDataTable` or a shared table abstraction
  2. standardize form layout and validation feedback wrappers
  3. add visual + interaction tests for density, filters, and bulk actions