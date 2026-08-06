# Panel Design System

Last updated: April 6, 2026
Scope: admin, supplier, logistics-partner panels in `frontend/web_app`

## Principles
- Prioritize information density over decorative padding.
- Keep interaction patterns identical across panel types.
- Use semantic theme tokens, not page-specific colors.
- Prefer one shared control over multiple page-local implementations.
- Optimize desktop operator workflows first, then mobile fallback.

## Typography

| Token | Size | Typical Use |
| --- | --- | --- |
| `xs` | `text-xs` | dense tables, chips, metadata |
| `sm` | `text-sm` | default body text |
| `base` | `text-base` | expanded density rows, modal body |
| `lg` | `text-lg` | page titles |
| `xl` | `text-xl` | dashboard hero metrics |

### Weights
- `font-medium`: table body emphasis, inline labels
- `font-semibold`: buttons, section headings, chips
- `font-bold`: metrics, modal titles, primary counts

### Line Height
- Dense data rows: `leading-tight`
- Body content: default Tailwind line height
- Section labels: uppercase tracking for scanability

## Spacing Scale

| Token | Utility |
| --- | --- |
| `1` | `0.25rem` |
| `2` | `0.5rem` |
| `3` | `0.75rem` |
| `4` | `1rem` |
| `5` | `1.25rem` |
| `6` | `1.5rem` |
| `8` | `2rem` |

### Layout Rules
- Toolbar controls: `gap-2` default
- Card grids: `gap-3` default, `gap-2` compact
- Heavy data sections: avoid `p-6` unless modal content requires it
- Panel pages: `p-3 sm:p-4 xl:p-5`

## Color System

Use semantic theme classes already present in the codebase:
- surfaces: `bg-surface`, `bg-surface-1`, `bg-surface-2`, `bg-surface-base`
- borders: `border-border`
- text: `text-text`, `text-text-muted`, `text-text-faint`, `text-on-brand`
- actions: `bg-primary`, `bg-danger`, `bg-success`, `bg-warning`, `bg-info`
- chips: `theme-chip-success`, `theme-chip-warning`, `theme-chip-danger`, `theme-chip-info`, `theme-chip-muted`, `theme-chip-brand`

### Light And Dark Themes
- Light theme should remain glossy but restrained: surface layering, border contrast, subtle shadows.
- Dark theme should avoid neon accents; keep semantic contrast driven by tokens, not ad hoc color literals.

## Buttons

### Standard Sizes
| Token | Height | Use |
| --- | --- | --- |
| `xs` | `h-7` | dense table actions |
| `sm` | `h-8` | toolbar controls |
| `md` | `h-10` | form actions |
| `lg` | `h-11` | primary standalone actions |

### Variants
- Primary: `theme-btn-primary`
- Secondary: `theme-btn-secondary border`
- Ghost: text-only with hover surface
- Danger: semantic destructive styling only

### Rules
- Prefer `xs` and `sm` inside operations pages.
- Avoid `lg` buttons inside tables and dashboards.
- Mobile action groups may stack vertically, but desktop should stay inline.

## Inputs
- Default height: `h-10`
- Compact mode input height: `h-8`
- Labels: uppercase, `text-[11px]`, `font-semibold`, `tracking-wider`
- Validation feedback below the field with icon + concise message

## Cards
- Use `theme-card rounded-xl border`
- Compact dashboards: `p-2.5`
- Normal dashboards: `p-3`
- Expanded cards or modal sections: `p-4`

## Modals
- Container: rounded 2xl, bordered surface, max height ~`80vh`
- Header: title + subtitle + close button
- Footer: fixed action zone when actions are present
- Escape key closes the modal
- Scrolling should stay inside the modal body, not the page

## Density Modes

| Mode | Text | Row Padding | Typical Page Size |
| --- | --- | --- | --- |
| Compact | `text-xs` | `py-1` to `py-2` | 50 |
| Normal | `text-sm` | `py-2` to `py-3` | 25 |
| Expanded | `text-base` | `py-4` | 10 |

### Density Rules
- Every table/list page should read density from `densityContext`.
- Card grids may collapse spacing in compact mode.
- Row action buttons should stay icon-first in compact mode.

## Data Grids
- Use a shared table abstraction where possible.
- Required features for enterprise pages:
  - global search
  - sortable columns
  - column visibility
  - bulk selection
  - page-size selector
  - CSV export
  - mobile card fallback

## Notifications And Alerts
- Toasts: top-right, auto-dismiss after ~3 seconds for success/info
- Alerts inside dashboards should use semantic chip or card treatments, not raw colored text
- Priority should be signaled through existing theme tones only

## Accessibility Rules
- Every icon-only button needs `aria-label`
- Switches must use `role="switch"` and `aria-checked`
- Table controls must remain keyboard reachable
- Modal close must support Escape

## Adoption Targets
- Immediate: orders, users, tickets, shipments, payouts
- Medium term: promotions, moderation, supplier products, returns queues
- Long term: standardize all panel forms on shared field wrappers 

### MERGED FROM COMPONENT_LIBRARY.md ###
 
# Component Library

Last updated: April 6, 2026

## Reusable Components

### EnterpriseDataTable
- Path: `frontend/shared/src/components/EnterpriseDataTable.tsx`
- Purpose: shared enterprise-oriented grid for large operational lists
- Current capabilities:
  - global search across visible columns
  - sortable columns
  - bulk page selection
  - CSV export
  - density modes
  - mobile card fallback
  - pagination with 10 / 25 / 50 / 100 page sizes
- Intended migration targets:
  - admin orders
  - admin users
  - admin tickets
  - logistics shipments

### DataDensityToggle
- Path: `frontend/web_app/src/components/DataDensityToggle.tsx`
- Purpose: compact / normal / expanded workspace control
- Depends on: `frontend/web_app/src/lib/densityContext.tsx`
- Used in: admin, supplier, logistics panel headers

### ColumnVisibilityPanel
- Path: `frontend/web_app/src/components/ColumnVisibilityPanel.tsx`
- Purpose: show/hide optional columns on list pages
- Used in: admin orders, admin users

### AdvancedFilterPanel
- Path: `frontend/web_app/src/components/AdvancedFilterPanel.tsx`
- Purpose: reusable dropdown container for advanced filters with reset and presets
- Used in: admin orders

### BulkActionBar
- Path: `frontend/web_app/src/components/BulkActionBar.tsx`
- Purpose: sticky multi-select action bar for high-volume workflows
- Used in: admin orders, admin users, tickets, logistics shipments

### InlineActionButtons
- Path: `frontend/web_app/src/components/InlineActionButtons.tsx`
- Purpose: compact icon-first row actions for dense tables
- Used in: admin orders, admin users

### QuickDetailModal
- Path: `frontend/web_app/src/components/QuickDetailModal.tsx`
- Purpose: standard compact detail modal with keyboard close support
- Used in: admin orders, supplier orders, other quick-view flows

### AdminLayout
- Path: `frontend/web_app/src/components/AdminLayout.tsx`
- Purpose: admin shell with permission-aware sidebar, density toggle, theme toggle, widened main content

### SupplierLayout
- Path: `frontend/web_app/src/components/SupplierLayout.tsx`
- Purpose: supplier shell with shared panel controls and wider main content area

### LogisticsPartnerLayout
- Path: `frontend/web_app/src/components/LogisticsPartnerLayout.tsx`
- Purpose: logistics shell with shared panel controls and wider main content area

### Button
- Path: `frontend/web_app/src/components/Button.tsx`
- Sizes: `xs`, `sm`, `md`, `lg`, `xl`
- Variants: `default`, `primary`, `secondary`, `ghost`, `danger`

### Input
- Path: `frontend/web_app/src/components/Input.tsx`
- Variants: text, password, icon-leading, error state, helper text

## Migration Guidance
- Prefer shared table/filter/modal components over page-local duplicates.
- Keep enterprise interactions icon-first and keyboard reachable.
- Avoid introducing new ad hoc color schemes; use semantic theme tokens already defined in the app.
 

### MERGED FROM STORYBOOK_COMPONENT_DOCS.md ###
 
# Shared Component Storybook Docs

Last updated: 2026-04-21

## Scope

This file is the Storybook-style documentation index for the shared component library in `frontend/shared/src/components`.
It documents the 39 canonical shared component modules (web/native variants included, alias wrappers excluded).

## How To Use This Doc

- Use this as the source of truth for component purpose, prop contract, and basic usage examples.
- For exact field-level types, open the referenced file and inspect the listed props interface/type.
- For platform behavior, always check both web/native variants when both exist.

## Component Catalog (39)

| # | Module Path | Export | Props Contract | Usage Example |
|---|---|---|---|---|
| 1 | `frontend/shared/src/components/logo/Logo.native.tsx` | `Logo` | `LogoNativeProps` | `<Logo size={40} label="ZOZI" />` |
| 2 | `frontend/shared/src/components/logo/Logo.web.tsx` | `Logo` | `LogoWebProps` | `<Logo size="md" className="text-primary" />` |
| 3 | `frontend/shared/src/components/logo/LogoAnimation.tsx` | `LogoAnimation` | `LogoAnimationProps` | `<LogoAnimation durationMs={1200} loop />` |
| 4 | `frontend/shared/src/components/logo/ZoziLogo.tsx` | `ZoziLogo` | `ZoziLogoProps` | `<ZoziLogo width={120} height={36} />` |
| 5 | `frontend/shared/src/components/ui/Button.native.tsx` | `Button` | `ButtonProps` | `<Button label="Save" onPress={onSave} />` |
| 6 | `frontend/shared/src/components/ui/Button.tsx` | `Button` | `ButtonProps` (re-export) | `<Button variant="primary">Submit</Button>` |
| 7 | `frontend/shared/src/components/ui/Button.web.tsx` | `Button` | `ButtonProps` | `<Button variant="secondary" size="sm">Cancel</Button>` |
| 8 | `frontend/shared/src/components/ui/CurrencyInit.native.tsx` | `CurrencyInit` | none (store bootstrap component) | `<CurrencyInit />` |
| 9 | `frontend/shared/src/components/ui/CurrencyInit.tsx` | `CurrencyInit` | none (platform proxy) | `<CurrencyInit />` |
| 10 | `frontend/shared/src/components/ui/CurrencyInit.web.tsx` | `CurrencyInit` | none (store bootstrap component) | `<CurrencyInit />` |
| 11 | `frontend/shared/src/components/ui/ErrorAlert.native.tsx` | `ErrorAlert` | `ErrorAlertProps` | `<ErrorAlert message={errorText} />` |
| 12 | `frontend/shared/src/components/ui/ErrorAlert.web.tsx` | `ErrorAlert` | `ErrorAlertProps` | `<ErrorAlert title="Request failed" message={detail} />` |
| 13 | `frontend/shared/src/components/ui/ErrorBoundary.tsx` | `ErrorBoundary` | `Props` | `<ErrorBoundary><AppSection /></ErrorBoundary>` |
| 14 | `frontend/shared/src/components/ui/ErrorHandlerInit.native.tsx` | `ErrorHandlerInit` | none (side-effect bootstrap) | `<ErrorHandlerInit />` |
| 15 | `frontend/shared/src/components/ui/ErrorHandlerInit.tsx` | `ErrorHandlerInit` | none (platform proxy) | `<ErrorHandlerInit />` |
| 16 | `frontend/shared/src/components/ui/ErrorHandlerInit.web.tsx` | `ErrorHandlerInit` | none (side-effect bootstrap) | `<ErrorHandlerInit />` |
| 17 | `frontend/shared/src/components/ui/GlassCard.native.tsx` | `GlassCard` | `GlassCardProps` | `<GlassCard><Content /></GlassCard>` |
| 18 | `frontend/shared/src/components/ui/Input.native.tsx` | `Input` | `InputProps` (`TextInputProps` extension) | `<Input value={email} onChangeText={setEmail} />` |
| 19 | `frontend/shared/src/components/ui/Input.tsx` | `Input` | `InputProps` (re-export) | `<Input label="Email" value={email} onChange={onChange} />` |
| 20 | `frontend/shared/src/components/ui/Input.web.tsx` | `Input` | `InputProps` (`InputHTMLAttributes` extension) | `<Input label="Password" type="password" />` |
| 21 | `frontend/shared/src/components/ui/LoadingSkeleton.native.tsx` | `LoadingSkeleton` | `SkeletonProps` | `<LoadingSkeleton lines={3} />` |
| 22 | `frontend/shared/src/components/ui/LoadingSkeleton.web.tsx` | `LoadingSkeleton` | `SkeletonProps` | `<LoadingSkeleton className="h-10 w-full" />` |
| 23 | `frontend/shared/src/components/ui/ProductCard.native.tsx` | `ProductCard` | `ProductCardProps` | `<ProductCard product={product} onPress={open} />` |
| 24 | `frontend/shared/src/components/ui/ProductCard.tsx` | `ProductCard` | `ProductCardProps` (platform bridge) | `<ProductCard product={product} />` |
| 25 | `frontend/shared/src/components/ui/ProductCard.web.tsx` | `ProductCard` | `ProductCardProps` | `<ProductCard product={product} href={`/products/${product.id}`} />` |
| 26 | `frontend/shared/src/components/ui/ProductGrid.native.tsx` | `ProductGrid` | `ProductGridProps` | `<ProductGrid products={items} />` |
| 27 | `frontend/shared/src/components/ui/ProductGrid.tsx` | `ProductGrid` | `ProductGridProps` | `<ProductGrid products={items} loading={isLoading} />` |
| 28 | `frontend/shared/src/components/ui/QuickFilters.native.tsx` | `QuickFilters` | `QuickFiltersProps` | `<QuickFilters filters={filters} value={value} onChange={setValue} />` |
| 29 | `frontend/shared/src/components/ui/QuickFilters.tsx` | `QuickFilters` | inferred props from implementation | `<QuickFilters filters={filters} value={value} onChange={setValue} />` |
| 30 | `frontend/shared/src/components/ui/SearchBar.native.tsx` | `SearchBar` | `SearchBarProps` | `<SearchBar value={query} onChangeText={setQuery} />` |
| 31 | `frontend/shared/src/components/ui/SearchBar.tsx` | `SearchBar` | inferred props from implementation | `<SearchBar value={query} onChange={setQuery} onSubmit={runSearch} />` |
| 32 | `frontend/shared/src/components/ui/SearchBar.web.tsx` | `SearchBar` | `SearchBarProps` | `<SearchBar query={query} onQueryChange={setQuery} />` |
| 33 | `frontend/shared/src/components/ui/SupplierBadge.native.tsx` | `SupplierBadge` | `SupplierBadgeProps` | `<SupplierBadge level="verified" score={88} />` |
| 34 | `frontend/shared/src/components/ui/SupplierBadge.web.tsx` | `SupplierBadge` | `SupplierBadgeProps` | `<SupplierBadge level="trusted" />` |
| 35 | `frontend/shared/src/components/ui/ThemeToggle.native.tsx` | `ThemeToggle` | `ThemeToggleProps` | `<ThemeToggle theme={theme} onToggle={toggleTheme} />` |
| 36 | `frontend/shared/src/components/ui/ThemeToggle.web.tsx` | `ThemeToggle` | `ThemeToggleProps` | `<ThemeToggle mode={mode} onToggle={toggleTheme} />` |
| 37 | `frontend/shared/src/components/ui/TranslatedText.native.tsx` | `TranslatedText` | `TranslatedTextProps` (`TextProps` extension) | `<TranslatedText tKey="checkout.total" />` |
| 38 | `frontend/shared/src/components/ui/TranslatedText.web.tsx` | `TranslatedText` | `TranslatedTextProps` | `<TranslatedText tKey="orders.title" />` |
| 39 | `frontend/shared/src/components/EnterpriseDataTable.tsx` | `EnterpriseDataTable` | `EnterpriseDataTableProps<T>` | `<EnterpriseDataTable columns={cols} rows={rows} />` |

## Notes

- Alias-only modules in `frontend/shared/src/components/ui/Logo.*` and `frontend/shared/src/components/ui/LogoAnimation.tsx` are intentionally excluded from canonical count to avoid duplicating logo contracts already documented in `frontend/shared/src/components/logo/*`.
- This document is intended to be consumed by Storybook docs pages or MDX pages during the next Storybook runtime bootstrap.
 

### MERGED FROM UIUX.md ###
 



- Check the Pasted Image properly for Implementation of UI and UX for `web_app` and `mobile_app` both.
- Investigate in detail all the UI and UX of `web_app` and `mobile_app` files to be make changes.
- List Down all the files to make changes in `web_app` and `mobile_app` for UI and UX changes.
- Remember `frontend/shared/**` files are shared between both `web_app` and `mobile_app`, so changes in these files will affect both platforms. so you can keep in `frontend/shared/**` any similar components/elements/styles/theme which can be shared for both platforms, make sure to update them accordingly to maintain consistency across both platforms. Make sure to test thoroughly after making changes in these shared files.
- Start making changes in the files one by one for UI and UX changes in both `web_app` and `mobile_app` as per the requirements and design guidelines.
- Remember to maintain the consistency of UI and UX across both `web_app` and `mobile_app` while making changes.
- After making changes in all the files, test the UI and UX on both `web_app` and `mobile_app` to ensure everything is working as expected and looks good.
- Remember to maintain the overall theme and design and responsiveness of the application while making changes to the UI and UX.
- Do not make change `Search Bar System` of `web_app` and replicate the same in `mobile_app` as it is working fine.
- Product Cart also need changes in both `web_app` and `mobile_app` as per the new design guidelines.
- After testing, if any issues are found, fix them.

---

# 🎨 E-Commerce UI Design Prompt

## 🧱 Base Theme Structure
- **Light Mode**
  - Background: `#FFFFFF` (white)
  - Text: `#111111` (near black)
  - Glass Panels: `rgba(255,255,255,0.3)` with `backdrop-filter: blur(10px)`
  - Neutral UI: `#F5F5F5` (light gray)

- **Dark Mode**
  - Background: `#000000` (black)
  - Text: `#FFFFFF` (white)
  - Glass Panels: `rgba(0,0,0,0.4)` with `backdrop-filter: blur(10px)`
  - Neutral UI: `#1A1A1A` (dark gray)

## 🌈 Accent Colors
- **Primary CTA (e.g. Add to Cart, Shop Now)**: Lime Green `#32CD32` or `#7CFC00`
- **Secondary CTA (e.g. Buy Now, View Deals)**: Yellow `#FFD700` or `#FFEA00`
- **Highlight Badges (e.g. Hot Deal, Discount)**: Yellow with bold text
- **Hover States**: Slightly darker lime or yellow with shadow

---

## 🖼️ Layout Guidelines

### 1. Homepage
- **Header**: Frosted glass nav bar with logo, links, cart/profile icons
- **Hero Banner**: Large product image + “Spring Collection” + lime “Shop Now” button
- **Product Grid**: Glass cards with product image, price, lime “Add to Cart” button
- **Sections**: “Best Sellers”, “New Arrivals”, “Hot Deals” with yellow badges

### 2. Product Page
- **Main Section**: Large product image on glass card
- **Details**: Price, star ratings, color/quantity selectors
- **CTA Buttons**: Lime “Add to Cart”, yellow “Buy Now”
- **Tabs**: Description, Specifications, Reviews on glass panels
- **Recommendations**: Glass cards for related products

### 3. Checkout Page
- **Order Summary**: Glass panel listing items, subtotal, shipping, total
- **Shipping Form**: Glass container with input fields
- **Payment Options**: Glass panel with icons (Credit Card, PayPal, Apple Pay)
- **CTA Button**: Lime “Place Order” with lock icon
- **Trust Badges**: Yellow/green icons for “SSL Protected”, “Secure Payment”

---

## 🧠 UX Enhancements
- **Responsive Design**: Works seamlessly across desktop, tablet, mobile
- **Accessibility**: High contrast, readable fonts, keyboard navigation
- **Animations**: Subtle hover effects, button transitions, glass fade-ins
- **Dark Mode Toggle**: Top-right switch with smooth transition

---

## 🔐 Security & Trust
- **SSL Badges**: Displayed on checkout and footer
- **Verified Supplier Badges**: Glass-style icons with green/yellow glow
- **Return Policy & Guarantee**: Clearly shown in product and checkout pages

---


 

### MERGED FROM WEB_APP_UI_UX_INVENTORY.md ###
 
# Web App UI/UX Inventory

Last updated: 2026-04-03

## Purpose

This document is the implementation baseline for `frontend/web_app` UI and UX work. The web app is already structurally mature, so future work should prefer shared tokens, shared components, and low-risk consistency fixes over page redesigns.

## Canonical Theme And UX Layer

### Core theme files

- `frontend/web_app/src/styles/globals.css`
  - Source of CSS variables, light and dark theme overrides, glass/gloss utilities, semantic panel/button/chip classes.
  - Main utilities: `theme-card`, `theme-panel`, `theme-elevated`, `theme-chip-*`, `theme-btn-*`, `glass-*`, `theme-topbar`, `theme-sidebar-shell`, `theme-main-content`.
- `frontend/web_app/tailwind.config.js`
  - Maps CSS variables to Tailwind tokens such as `primary`, `accent`, `surface`, `text`, `warning`, `success`, `danger`, `info`, `on-brand`, and `on-accent`.
- `frontend/web_app/src/app/layout.tsx`
  - Global app shell and SSR anti-flash theme bootstrap.
- `frontend/web_app/src/lib/themeStore.ts`
  - Theme persistence and runtime theme switching.

### Shared UI components

- `frontend/web_app/src/components/AdminLayout.tsx`
- `frontend/web_app/src/components/SupplierLayout.tsx`
- `frontend/web_app/src/components/LogisticsPartnerLayout.tsx`
- `frontend/web_app/src/components/Header.tsx`
- `frontend/web_app/src/components/Footer.tsx`
- `frontend/web_app/src/components/ThemeProvider.tsx`
- `frontend/web_app/src/components/ThemeToggle.tsx`
- `frontend/web_app/src/components/Button.tsx`
- `frontend/web_app/src/components/Input.tsx`
- `frontend/web_app/src/components/FilterSearchBar.tsx`
- `frontend/web_app/src/components/BulkActionBar.tsx`
- `frontend/web_app/src/components/ProductCard.tsx`
- `frontend/web_app/src/components/ProductGrid.tsx`
- `frontend/web_app/src/components/QuickViewModal.tsx`
- `frontend/web_app/src/components/HeroBanner.tsx`
- `frontend/web_app/src/components/SeasonalBanner.tsx`
- `frontend/web_app/src/components/LimitedTimeOffer.tsx`
- `frontend/web_app/src/components/HomeProductShowcase.tsx`
- `frontend/web_app/src/components/Recommendations.tsx`
- `frontend/web_app/src/components/RecentlyViewed.tsx`
- `frontend/web_app/src/components/NewsletterSignup.tsx`
- `frontend/web_app/src/components/Chatbot.tsx`
- `frontend/web_app/src/components/LoadingSkeleton.tsx`
- `frontend/web_app/src/components/BrandLoading.tsx`
- `frontend/web_app/src/components/ErrorBoundary.tsx`
- `frontend/web_app/src/components/ErrorAlert.tsx`
- `frontend/web_app/src/components/TranslatedText.tsx`
- `frontend/web_app/src/components/ToastContainer.tsx`
- `frontend/web_app/src/components/Breadcrumbs.tsx`
- `frontend/web_app/src/components/Logo.tsx`
- `frontend/web_app/src/components/AuthRequiredModal.tsx`
- `frontend/web_app/src/components/BackgroundEffect.tsx`
- `frontend/web_app/src/components/BackgroundJobCenter.tsx`
- `frontend/web_app/src/components/SignaturePad.tsx`

### Shared admin email UI

- `frontend/web_app/src/components/admin/EmailCampaignManager.tsx`
- `frontend/web_app/src/components/admin/EmailTemplateManager.tsx`
- `frontend/web_app/src/components/admin/CreateCampaignForm.tsx`

### Shared UI helper functions and hooks

- `frontend/web_app/src/lib/themeStore.ts`
  - `useThemeStore()`
- `frontend/web_app/src/lib/useAuth.ts`
  - `useAuth()`
- `frontend/web_app/src/lib/localeStore.ts`
  - `useLocaleStore()`
- `frontend/web_app/src/lib/useTranslate.ts`
  - `useTranslate()`
  - `useTranslateText()`
  - `useTranslateTexts()`
- `frontend/web_app/src/lib/utils.ts`
  - `resolveImage()`
  - `supplierStorefrontPath()`
  - `cn()`
- `frontend/shared/src/statusColors.ts`
  - `ORDER_STATUS_CHIP`
  - `PRODUCT_STATUS_CHIP`
  - `RETURN_STATUS_CHIP`
  - `PARTNER_BADGE_STYLE`
  - `getStatusChip()`
  - `getPartnerBadgeStyle()`
- `frontend/shared/src/productHelpers.ts`
  - `calculateDiscountPercent()`
  - `getProductDiscountPercent()`
  - `getProductBadges()`
- `frontend/shared/src/localization.ts`
  - `formatLocalizedDate()`
  - `formatLocalizedDateTime()`
  - `isRtlLocale()`
- `frontend/shared/src/productQuery.ts`
  - `buildProductQueryParams()`

## Route Inventory

Main rule: every route file below is a UI surface and usually exports a default page component.

### Customer pages

- `frontend/web_app/src/app/page.tsx` — home page
- `frontend/web_app/src/app/products/page.tsx` — catalog, search, filters, supplier spotlight
- `frontend/web_app/src/app/products/[id]/page.tsx` — product detail
- `frontend/web_app/src/app/cart/page.tsx` — cart
- `frontend/web_app/src/app/checkout/page.tsx` — checkout
- `frontend/web_app/src/app/orders/page.tsx` — customer orders list
- `frontend/web_app/src/app/orders/[id]/page.tsx` — customer order detail
- `frontend/web_app/src/app/returns/page.tsx` — customer returns list
- `frontend/web_app/src/app/returns/[id]/page.tsx` — return detail
- `frontend/web_app/src/app/wishlist/page.tsx` — wishlist
- `frontend/web_app/src/app/notifications/page.tsx` — notifications
- `frontend/web_app/src/app/profile/page.tsx` — profile
- `frontend/web_app/src/app/profile/referrals/page.tsx` — referral center
- `frontend/web_app/src/app/offers/page.tsx` — offers and promotions
- `frontend/web_app/src/app/help/page.tsx` — help center
- `frontend/web_app/src/app/tickets/page.tsx` — support tickets
- `frontend/web_app/src/app/tickets/[id]/page.tsx` — support ticket detail
- `frontend/web_app/src/app/invoice/page.tsx` — invoice view
- `frontend/web_app/src/app/tracking/[id]/page.tsx` — tracking detail
- `frontend/web_app/src/app/archive/page.tsx` — archive or historical content
- `frontend/web_app/src/app/logo-animation/page.tsx` — brand animation page
- `frontend/web_app/src/app/chatbot/page.tsx` — chatbot page shell
- `frontend/web_app/src/app/newsletter/page.tsx` — newsletter landing
- `frontend/web_app/src/app/newsletter/preferences/page.tsx` — newsletter preferences
- `frontend/web_app/src/app/newsletter/unsubscribe/page.tsx` — newsletter unsubscribe
- `frontend/web_app/src/app/r/[code]/page.tsx` — redirect or referral code page

### Auth and account pages

- `frontend/web_app/src/app/login/page.tsx` — customer login
- `frontend/web_app/src/app/register/page.tsx` — customer registration
- `frontend/web_app/src/app/forgot-password/page.tsx` — password recovery
- `frontend/web_app/src/app/reset-password/page.tsx` — reset password
- `frontend/web_app/src/app/verify-email/page.tsx` — email verification
- `frontend/web_app/src/app/auth/callback/page.tsx` — auth callback UI

### Supplier public pages

- `frontend/web_app/src/app/suppliers/[id]/page.tsx` — supplier public profile and storefront overview
- `frontend/web_app/src/app/supplier-storefront/[slug]/page.tsx` — supplier storefront route

### Admin pages

- `frontend/web_app/src/app/admin/login/page.tsx` — admin login
- `frontend/web_app/src/app/admin/dashboard/page.tsx` — admin dashboard shell
- `frontend/web_app/src/app/admin/analytics/page.tsx` — analytics page
- `frontend/web_app/src/app/admin/users/page.tsx` — user management
- `frontend/web_app/src/app/admin/suppliers/page.tsx` — supplier management
- `frontend/web_app/src/app/admin/products/page.tsx` — product moderation and badge toggles
- `frontend/web_app/src/app/admin/product-verification/page.tsx` — product verification workflows
- `frontend/web_app/src/app/admin/orders/page.tsx` — order management
- `frontend/web_app/src/app/admin/returns/page.tsx` — returns management
- `frontend/web_app/src/app/admin/invoices/page.tsx` — invoice management
- `frontend/web_app/src/app/admin/exports/page.tsx` — export tools
- `frontend/web_app/src/app/admin/banners/page.tsx` — banner management
- `frontend/web_app/src/app/admin/coupons/page.tsx` — coupon management
- `frontend/web_app/src/app/admin/flash-sales/page.tsx` — flash sale management
- `frontend/web_app/src/app/admin/logistics-partners/page.tsx` — logistics partner management
- `frontend/web_app/src/app/admin/audit-logs/page.tsx` — audit logs
- `frontend/web_app/src/app/admin/email/page.tsx` — email marketing dashboard
- `frontend/web_app/src/app/admin/barcode/page.tsx` — admin barcode tools

### Supplier portal pages

- `frontend/web_app/src/app/supplier/page.tsx` — supplier root shell or redirect
- `frontend/web_app/src/app/supplier/login/page.tsx` — supplier login
- `frontend/web_app/src/app/supplier/register/page.tsx` — supplier registration
- `frontend/web_app/src/app/supplier/dashboard/page.tsx` — supplier dashboard
- `frontend/web_app/src/app/supplier/products/page.tsx` — supplier product management
- `frontend/web_app/src/app/supplier/orders/page.tsx` — supplier orders
- `frontend/web_app/src/app/supplier/returns/page.tsx` — supplier returns
- `frontend/web_app/src/app/supplier/reports/page.tsx` — supplier reports
- `frontend/web_app/src/app/supplier/analytics/page.tsx` — supplier analytics
- `frontend/web_app/src/app/supplier/payouts/page.tsx` — supplier payouts
- `frontend/web_app/src/app/supplier/profile/page.tsx` — supplier profile
- `frontend/web_app/src/app/supplier/credibility/page.tsx` — supplier credibility and badge scoring
- `frontend/web_app/src/app/supplier/guide/page.tsx` — supplier guide
- `frontend/web_app/src/app/supplier/terms/page.tsx` — supplier terms and acceptance flow
- `frontend/web_app/src/app/supplier/logistics/page.tsx` — supplier logistics
- `frontend/web_app/src/app/supplier/invoices/page.tsx` — supplier invoices
- `frontend/web_app/src/app/supplier/inventory/page.tsx` — supplier inventory
- `frontend/web_app/src/app/supplier/regions/page.tsx` — supplier region settings
- `frontend/web_app/src/app/supplier/documents/page.tsx` — supplier documents
- `frontend/web_app/src/app/supplier/bulk/page.tsx` — bulk upload or import
- `frontend/web_app/src/app/supplier/upload/page.tsx` — upload route alias
- `frontend/web_app/src/app/supplier/labels/[id]/page.tsx` — supplier shipping or label print detail

### Logistics portal pages

- `frontend/web_app/src/app/logistics-partner/login/page.tsx` — logistics login
- `frontend/web_app/src/app/logistics-partner/register/page.tsx` — logistics registration
- `frontend/web_app/src/app/logistics-partner/dashboard/page.tsx` — logistics dashboard
- `frontend/web_app/src/app/logistics-partner/shipments/page.tsx` — shipment management
- `frontend/web_app/src/app/logistics-partner/scan/page.tsx` — scan workflows
- `frontend/web_app/src/app/logistics-partner/payouts/page.tsx` — payouts
- `frontend/web_app/src/app/logistics-partner/profile/page.tsx` — profile

### Utility and specialized pages

- `frontend/web_app/src/app/barcode-scan/page.tsx` — barcode scan UI

## High-Value Reusable Patterns

### Panels, cards, shells

- Prefer `theme-card`, `theme-panel`, and `theme-elevated` before creating new card backgrounds.
- Prefer `AdminLayout`, `SupplierLayout`, and `LogisticsPartnerLayout` for portal shells.
- Prefer `Header` and `Footer` for customer shell consistency.

### Buttons and inputs

- Prefer `theme-btn-primary`, `theme-btn-accent`, `theme-btn-danger`, and `theme-btn-ghost`.
- Prefer `Button` and `Input` wrappers where possible.
- Prefer `text-on-brand` and `text-on-accent` for solid primary and accent button text.

### Status, badge, and trust styling

- Prefer `ORDER_STATUS_CHIP`, `PRODUCT_STATUS_CHIP`, `RETURN_STATUS_CHIP`, and `getStatusChip()`.
- Prefer `getPartnerBadgeStyle()` for supplier badge levels.
- Prefer `getProductBadges()` for offer, hot, featured, and new product badges.

### Search and list toolbars

- Prefer `FilterSearchBar` for advanced catalog filtering.
- Prefer `BulkActionBar` for admin multi-select workflows.
- Prefer the admin toolbar pattern: count line, search, filters, refresh, then list or grid.

### Localization and RTL

- Prefer `useLocaleStore()`, `useTranslateText()`, `useTranslateTexts()`, and `isRtlLocale()`.
- Prefer localized date formatting through `formatLocalizedDate()` and `formatLocalizedDateTime()`.

## Implementation Notes

- The light theme should continue to be improved through shared tokens in `globals.css`, not through page-specific color forks.
- The app is already about 80% complete, so future UI work should avoid structural churn.
- Admin email is a regression-sensitive page because it has recent edits and depends on the admin email component set.
- Remaining debt should be addressed first in shared helpers and then in repeated page call sites.
 

### MERGED FROM ICON_INVENTORY.md ###
 
# ZOZI Icon & Symbol Inventory

> Auto-generated inventory of all icons and symbols used across `frontend/web_app` and `frontend/mobile_app`.
> Last updated: April 3, 2026.

---

## Table of Contents

1. [Web App Icons (Lucide React)](#1-web-app-icons--lucide-react)
2. [Mobile App Icons (Expo Vector Icons — Ionicons)](#2-mobile-app-icons--ionicons)
3. [Mobile App Icons (Expo Vector Icons — Feather)](#3-mobile-app-icons--feather)
4. [Icon Usage by Page — Web App](#4-icon-usage-by-page--web-app)
5. [Icon Usage by Page — Mobile App](#5-icon-usage-by-page--mobile-app)
6. [Centralized Registry Files](#6-centralized-registry-files)

---

## 1. Web App Icons — Lucide React

Library: `lucide-react`  
Import source: `frontend/web_app/src/lib/icons.ts` (centralized)

| # | Icon Name | Symbol / Purpose |
|---|-----------|-----------------|
| 1 | `Activity` | Live activity / jobs indicator |
| 2 | `AlertCircle` | Warning / error alert |
| 3 | `AlertTriangle` | Caution / warning triangle |
| 4 | `ArrowDownRight` | Down-right directional arrow |
| 5 | `ArrowLeft` | Back navigation arrow |
| 6 | `ArrowRight` | Forward / proceed arrow |
| 7 | `ArrowUp` | Upward direction / scroll up |
| 8 | `ArrowUpRight` | Up-right directional arrow |
| 9 | `Award` | Achievement / award badge |
| 10 | `BadgeCheck` | Verified / credibility badge |
| 11 | `Banknote` | Cash / banknote payment |
| 12 | `BarChart3` | Analytics / bar chart |
| 13 | `Bell` | Notifications |
| 14 | `BookOpen` | Guide / documentation |
| 15 | `Building` | Business / organisation |
| 16 | `Building2` | Company / headquarters |
| 17 | `Calendar` | Calendar / scheduled date |
| 18 | `CalendarDays` | Calendar with days view |
| 19 | `Camera` | Camera / photo upload |
| 20 | `Check` | Checkmark / selected state |
| 21 | `CheckCheck` | Double-check / all read |
| 22 | `CheckCircle` | Success / verified |
| 23 | `CheckCircle2` | Alternate success circle |
| 24 | `CheckSquare` | Checked checkbox |
| 25 | `ChevronDown` | Dropdown / expand |
| 26 | `ChevronLeft` | Previous / back chevron |
| 27 | `ChevronRight` | Next / forward chevron |
| 28 | `ChevronUp` | Collapse / minimize |
| 29 | `Circle` | Empty circle / neutral state |
| 30 | `CircleEllipsis` | More options / pending |
| 31 | `ClipboardList` | Audit logs / clipboard |
| 32 | `Clock` | Time / pending status |
| 33 | `Clock3` | Time (alternate) |
| 34 | `Code` | Code / template editor |
| 35 | `Copy` | Copy to clipboard |
| 36 | `CreditCard` | Card payment |
| 37 | `Crown` | Admin / premium role |
| 38 | `DollarSign` | Currency / payout |
| 39 | `Download` | Download file |
| 40 | `Edit` | Edit item |
| 41 | `Edit2` | Edit (alternate style) |
| 42 | `ExternalLink` | Open in new tab |
| 43 | `Eye` | View / preview |
| 44 | `EyeOff` | Hide / password toggle |
| 45 | `FileCheck` | Document verified |
| 46 | `FileCheck2` | Document verified (alternate) |
| 47 | `FileDown` | Download file |
| 48 | `FileJson` | JSON file / bulk import |
| 49 | `FileText` | Document / text file |
| 50 | `Filter` | Filter results |
| 51 | `Flame` | Hot / trending product |
| 52 | `Gem` | Jewellery category |
| 53 | `Gift` | Referral reward / gift |
| 54 | `Globe` | Global / region setting |
| 55 | `Hash` | Order / tracking number |
| 56 | `Headphones` | Electronics / audio category |
| 57 | `Heart` | Wishlist / favourite |
| 58 | `Image` *(as `ImageIcon`)* | Image / banner placeholder |
| 59 | `Info` | Information / tooltip |
| 60 | `Instagram` | Instagram social link |
| 61 | `Keyboard` | Keyboard / manual input |
| 62 | `KeyRound` | Password / security key |
| 63 | `Lamp` | Home & lighting category |
| 64 | `LayoutDashboard` | Dashboard layout |
| 65 | `Layers` | Product variants / layers |
| 66 | `Lightbulb` | Tips / suggestions |
| 67 | `Link2` | Copy link / URL |
| 68 | `List` | List view toggle |
| 69 | `Loader2` | Loading spinner |
| 70 | `Lock` | Security / locked state |
| 71 | `LocateFixed` | Locate / GPS |
| 72 | `LogIn` | Login / sign in |
| 73 | `LogOut` | Logout / sign out |
| 74 | `Mail` | Email / newsletter |
| 75 | `MapPin` | Location / address pin |
| 76 | `MapPinned` | Pinned location (filled) |
| 77 | `Maximize2` | Expand / full screen |
| 78 | `Megaphone` | Promotions / announcements |
| 79 | `Menu` | Hamburger menu |
| 80 | `MessageCircle` | Chat message bubble |
| 81 | `MessageCircleQuestion` | FAQ / help chat |
| 82 | `MessageSquare` | Support ticket / chat |
| 83 | `Minus` | Decrease quantity |
| 84 | `Moon` | Dark mode / night theme |
| 85 | `MoreVertical` | Options / context menu |
| 86 | `MousePointer` | Click / interaction tracking |
| 87 | `Network` | Network / integrations |
| 88 | `Package` | Order package |
| 89 | `Package2` | Alternate package icon |
| 90 | `PackageCheck` | Package verified / accepted |
| 91 | `PackageX` | Package rejected / returned |
| 92 | `Pencil` | Edit / pencil |
| 93 | `Percent` | Discount / percentage |
| 94 | `Phone` | Phone number |
| 95 | `Plus` | Add / create new |
| 96 | `Printer` | Print invoice |
| 97 | `QrCode` | QR code / barcode scan |
| 98 | `Radio` | Live / real-time status |
| 99 | `RefreshCw` | Reload / refresh |
| 100 | `RotateCcw` | Restore / undo |
| 101 | `Route` | Delivery route |
| 102 | `Ruler` | Product dimensions |
| 103 | `Save` | Save / submit |
| 104 | `ScanLine` | Barcode scan line |
| 105 | `ScrollText` | Terms & conditions |
| 106 | `Search` | Search / find |
| 107 | `Send` | Send message / payout |
| 108 | `Settings` | Settings / preferences |
| 109 | `Share2` | Share / referral link |
| 110 | `Shield` | Security / privacy |
| 111 | `ShieldCheck` | Verified / secure |
| 112 | `ShieldOff` | Unverified / revoke |
| 113 | `Shirt` | Fashion category |
| 114 | `ShoppingBag` | Shopping bag |
| 115 | `ShoppingCart` | Cart |
| 116 | `Smartphone` | Mobile / smartphone |
| 117 | `Sofa` | Furniture category |
| 118 | `Sparkles` | AI / recommendations / special |
| 119 | `Star` | Rating / review |
| 120 | `Stars` | Multiple stars / seasonal |
| 121 | `Store` | Supplier store |
| 122 | `Tag` | Coupon / price tag |
| 123 | `Ticket` | Support ticket |
| 124 | `ToggleLeft` | Toggle off |
| 125 | `ToggleRight` | Toggle on |
| 126 | `Trash2` | Delete / remove |
| 127 | `TrendingUp` | Trending / sales growth |
| 128 | `TriangleAlert` | Jobs / critical alert |
| 129 | `Truck` | Delivery / logistics |
| 130 | `Upload` | Upload file / image |
| 131 | `User` | User profile |
| 132 | `UserCircle2` | User avatar circle |
| 133 | `UserPlus` | Register / add user |
| 134 | `Users` | User management |
| 135 | `Wallet` | Wallet / payouts |
| 136 | `Watch` | Watches & accessories category |
| 137 | `X` | Close / dismiss / clear |
| 138 | `XCircle` | Error / rejected state |
| 139 | `Zap` | Flash sale / fast action |

**Total: 139 unique Lucide icons**

---

## 2. Mobile App Icons — Ionicons

Library: `@expo/vector-icons` → `Ionicons`  
Import source: `frontend/mobile_app/lib/icons.ts` (centralized)

| # | Icon Name | Symbol / Purpose |
|---|-----------|-----------------|
| 1 | `add` | Add / plus |
| 2 | `add-circle-outline` | Add with circle outline |
| 3 | `alert-circle` | Warning / error alert |
| 4 | `arrow-forward` | Forward / proceed arrow |
| 5 | `barcode-outline` | Barcode scan |
| 6 | `camera` | Camera |
| 7 | `camera-outline` | Camera (outline) |
| 8 | `car` | Car / delivery |
| 9 | `car-outline` | Car (outline) / delivery |
| 10 | `cart` | Cart (filled) |
| 11 | `cart-outline` | Cart (outline) |
| 12 | `chatbubble-ellipses` | Chat / chatbot |
| 13 | `checkmark` | Checkmark / confirm |
| 14 | `checkmark-circle` | Success / verified |
| 15 | `checkmark-circle-outline` | Verified (outline) |
| 16 | `checkmark-outline` | Mark all read |
| 17 | `chevron-forward` | Next / forward |
| 18 | `close` | Close / dismiss |
| 19 | `close-circle` | Close with circle / error |
| 20 | `close-outline` | Dismiss (outline) |
| 21 | `copy-outline` | Copy referral code |
| 22 | `cube-outline` | Empty product / placeholder |
| 23 | `expand-outline` | Quick view expand |
| 24 | `eye` | Show password |
| 25 | `eye-off` | Hide password |
| 26 | `filter-outline` | Filter orders |
| 27 | `flash` | Flash sale (filled) |
| 28 | `flash-outline` | Flash sale (outline) |
| 29 | `gift-outline` | Referral gift |
| 30 | `grid` | Grid view (filled) |
| 31 | `grid-outline` | Grid view (outline) |
| 32 | `heart` | Wishlist (filled) |
| 33 | `heart-outline` | Wishlist (outline) |
| 34 | `home` | Home tab (focused) |
| 35 | `home-outline` | Home tab (unfocused) |
| 36 | `image-outline` | Image placeholder |
| 37 | `list` | List view |
| 38 | `locate-outline` | Track order location |
| 39 | `location-outline` | Address / location |
| 40 | `lock-closed` | Secure checkout / locked |
| 41 | `lock-open` | Unlock / auth |
| 42 | `log-in-outline` | Login (guest state) |
| 43 | `mail` | Email |
| 44 | `mail-unread` | Unread email |
| 45 | `moon-outline` | Dark mode |
| 46 | `notifications` | Notifications (filled) |
| 47 | `notifications-outline` | Notifications (outline) |
| 48 | `person` | Profile (filled) |
| 49 | `person-circle-outline` | Profile avatar |
| 50 | `person-outline` | Profile (outline) |
| 51 | `pricetag` | Coupon / price tag |
| 52 | `receipt-outline` | Order receipt |
| 53 | `refresh-circle` | Refresh (filled) |
| 54 | `refresh-outline` | Refresh / returns |
| 55 | `remove` | Decrease quantity |
| 56 | `search` | Search (filled) |
| 57 | `search-outline` | Search (outline) |
| 58 | `share-outline` | Share product |
| 59 | `share-social-outline` | Share referral (social) |
| 60 | `shield-checkmark` | Buyer protection (filled) |
| 61 | `shield-checkmark-outline` | Buyer protection (outline) |
| 62 | `sparkles` | AI / recommendations |
| 63 | `sparkles-outline` | AI suggestions (outline) |
| 64 | `star` | Rating / review |
| 65 | `sunny-outline` | Light mode |
| 66 | `time-outline` | Recent / pending time |
| 67 | `trash-outline` | Delete / remove |
| 68 | `trending-up` | Trending / top sellers |

**Total: 68 unique Ionicons**

---

## 3. Mobile App Icons — Feather

Library: `@expo/vector-icons` → `Feather`  
Import source: `frontend/mobile_app/lib/icons.ts` (centralized)

| # | Icon Name | Symbol / Purpose |
|---|-----------|-----------------|
| 1 | `check` | Approve / verified action |
| 2 | `check-circle` | Confirmed (empty state) |
| 3 | `edit-3` | Manual barcode input |
| 4 | `maximize-2` | Expand product quick view |
| 5 | `package` | Empty returns state |
| 6 | `rotate-ccw` | Restore / undo product |
| 7 | `search` | Search bar |
| 8 | `trash-2` | Delete product |
| 9 | `x` | Clear / dismiss |
| 10 | `zap` | Flash sale tag |

**Total: 10 unique Feather icons**

---

## 4. Icon Usage by Page — Web App

### Components (Shared)

| Component | Icons Used |
|-----------|-----------|
| `Header.tsx` | `ShoppingBag`, `Heart`, `User`, `Menu`, `X`, `LogOut`, `Package`, `ClipboardList`, `Settings`, `Store`, `LayoutDashboard`, `Bell`, `ChevronDown` |
| `Footer.tsx` | `Sparkles`, `Crown` |
| `AdminLayout.tsx` | `Crown`, `Users`, `Package`, `ShoppingCart`, `BarChart3`, `Store`, `Shield`, `ClipboardList`, `Tag`, `MessageSquare`, `Megaphone`, `Mail`, `Truck`, `FileText`, `FileDown`, `QrCode`, `CheckSquare`, `Menu`, `X`, `ChevronLeft`, `ChevronRight`, `LogOut`, `Zap`, `Wallet`, `Network`, `FileCheck2`, `TrendingUp`, `DollarSign` |
| `SupplierLayout.tsx` | `LayoutDashboard`, `Package`, `ShoppingCart`, `FileText`, `User`, `Menu`, `X`, `ChevronLeft`, `ChevronRight`, `LogOut`, `Wallet`, `BadgeCheck` |
| `LogisticsPartnerLayout.tsx` | `LayoutDashboard`, `Package`, `Menu`, `X`, `ChevronLeft`, `ChevronRight`, `LogOut`, `Truck`, `Wallet`, `User`, `ScanLine` |
| `HeroBanner.tsx` | `TrendingUp`, `ShoppingBag`, `Percent` |
| `HomeProductShowcase.tsx` | `Search`, `Sofa`, `Headphones`, `Shirt`, `Watch`, `Lamp`, `Gem` |
| `ProductCard.tsx` | `Heart`, `Star`, `Tag`, `Maximize2`, `ShoppingCart` |
| `QuickViewModal.tsx` | `X`, `ShoppingCart`, `Heart`, `Star`, `ArrowRight`, `Package`, `Check` |
| `FilterSearchBar.tsx` | `Search`, `Tag`, `Percent`, `Store`, `Sparkles`, `TrendingUp`, `Star`, `ShoppingBag`, `X`, `ChevronDown`, `Camera`, `Zap`, `CheckCircle`, `Bell`, `Filter`, `Package2` |
| `SeasonalBanner.tsx` | `ArrowRight`, `BadgeCheck`, `ChevronLeft`, `ChevronRight`, `Megaphone`, `ShieldCheck`, `Sparkles`, `Tag`, `Truck`, `Flame`, `Moon`, `Stars` |
| `NewsletterSignup.tsx` | `Mail`, `CheckCircle`, `AlertCircle`, `Loader2` |
| `RecentlyViewed.tsx` | `Clock` |
| `Recommendations.tsx` | `Sparkles` |
| `LimitedTimeOffer.tsx` | `X`, `Clock`, `Percent` |
| `AuthRequiredModal.tsx` | `AlertCircle`, `Eye`, `EyeOff`, `LogIn`, `UserPlus`, `X` |
| `ToastContainer.tsx` | `X`, `CheckCircle`, `AlertCircle`, `Info` |
| `BackgroundJobCenter.tsx` | `Activity`, `CheckCircle2`, `ChevronDown`, `ChevronUp`, `ExternalLink`, `Loader2`, `TriangleAlert`, `X` |
| `BulkActionBar.tsx` | `X` |

### Auth Pages

| Page | Icons Used |
|------|-----------|
| `login/LoginClient.tsx` | `LogIn`, `Eye`, `EyeOff`, `AlertCircle` |
| `register/RegisterClient.tsx` | `UserPlus`, `AlertCircle` |
| `forgot-password/page.tsx` | `Mail`, `ArrowLeft`, `CheckCircle` |
| `reset-password/page.tsx` | `Lock`, `CheckCircle`, `Eye`, `EyeOff` |
| `verify-email/page.tsx` | `CheckCircle`, `XCircle` |

### Customer Pages

| Page | Icons Used |
|------|-----------|
| `cart/page.tsx` | `ShoppingCart`, `Trash2`, `Minus`, `Plus`, `ArrowRight`, `Package`, `Tag`, `LocateFixed`, `MapPin`, `FileText`, `Phone`, `Lock`, `Shield`, `CheckCircle` |
| `checkout/page.tsx` | `CreditCard`, `Banknote`, `Lock`, `CheckCircle`, `Shield`, `AlertCircle`, `MapPin`, `ShoppingBag`, `ChevronRight`, `ChevronLeft`, `Tag`, `Smartphone` |
| `products/page.tsx` | `Search`, `Loader2`, `Tag`, `Percent`, `Store`, `MapPin`, `Sparkles`, `TrendingUp`, `Star`, `ShoppingBag`, `X`, `ChevronDown`, `Flame`, `Award`, `Package2`, `Filter`, `ArrowUp`, `CheckCircle` |
| `products/[id]/page.tsx` | *(large set — see filtering & product detail icons)* |
| `orders/page.tsx` | `Package`, `Clock`, `CheckCircle`, `Truck`, `XCircle`, `MapPin`, `CircleEllipsis`, `RotateCcw`, `CreditCard` |
| `orders/[id]/page.tsx` | *(invoice, timeline, and tracking icons)* |
| `wishlist/page.tsx` | `Heart`, `ShoppingCart`, `Trash2` |
| `tracking/[id]/page.tsx` | `ArrowLeft`, `Clock`, `Package`, `Truck`, `CheckCircle`, `ExternalLink`, `MapPin`, `Hash` |
| `returns/page.tsx` | `PackageX`, `Clock`, `CheckCircle`, `XCircle`, `RotateCcw`, `RefreshCw` |
| `returns/[id]/page.tsx` | `ArrowLeft`, `PackageX` |
| `profile/page.tsx` | `User`, `Lock`, `Mail`, `Shield`, `Save`, `AlertCircle`, `Phone`, `Camera`, `CheckCircle`, `XCircle`, `MapPin`, `FileText`, `Gift`, `Copy`, `Share2`, `Users` |
| `profile/referrals/page.tsx` | `ArrowLeft`, `Gift`, `Share2`, `Copy`, `RefreshCw` |
| `notifications/page.tsx` | `Bell`, `CheckCheck`, `Trash2`, `Package`, `AlertTriangle`, `Info` |
| `tickets/page.tsx` | `Ticket`, `Plus`, `MessageCircle`, `ChevronRight` |
| `tickets/[id]/page.tsx` | `ArrowLeft`, `Send`, `User`, `ShieldCheck` |
| `help/page.tsx` | `MessageSquare`, `Send`, `ChevronDown`, `CheckCircle`, `Clock`, `AlertCircle` |
| `offers/page.tsx` | `Zap`, `Tag`, `ChevronRight`, `Store`, `Megaphone` |
| `newsletter/page.tsx` | `Mail`, `CheckCircle`, `Bell`, `Tag`, `Zap`, `Gift` |
| `newsletter/preferences/page.tsx` | `Mail`, `CheckCircle`, `XCircle` |
| `newsletter/unsubscribe/page.tsx` | `CheckCircle`, `XCircle`, `Mail`, `AlertCircle` |
| `suppliers/[id]/page.tsx` | *(supplier storefront icons)* |

### Supplier Pages

| Page | Icons Used |
|------|-----------|
| `supplier/page.tsx` | `TrendingUp`, `BarChart3`, `Shield`, `Truck`, `ArrowRight`, `Sparkles`, `Users`, `DollarSign` |
| `supplier/dashboard/page.tsx` | `DollarSign`, `Package`, `ShoppingCart`, `TrendingUp`, `ArrowUpRight`, `ArrowDownRight`, `AlertTriangle`, `CheckCircle`, `Circle`, `ChevronRight`, `Star` |
| `supplier/login/page.tsx` | `LogIn`, `AlertCircle`, `Store` |
| `supplier/register/page.tsx` | `UserPlus`, `AlertCircle`, `Building2`, `FileCheck`, `ChevronRight`, `ChevronLeft`, `Check`, `ShieldCheck`, `Globe`, `Instagram`, `ExternalLink` |
| `supplier/products/page.tsx` | `Search`, `Plus`, `Edit`, `Trash2`, `Package`, `ToggleLeft`, `ToggleRight`, `X`, `Save` |
| `supplier/bulk/page.tsx` | `Upload`, `Trash2`, `Plus`, `Sparkles`, `X`, `CheckCircle`, `AlertCircle`, `ImageIcon`, `Tag`, `Package`, `ChevronDown`, `ChevronUp`, `Loader2`, `FileJson`, `Download`, `Link2`, `Ruler`, `Layers`, `FileText` |
| `supplier/orders/page.tsx` | `FileText`, `RefreshCw`, `CheckCircle`, `Clock`, `Truck`, `AlertCircle`, `Plus`, `ChevronLeft`, `ChevronRight`, `X` |
| `supplier/analytics/page.tsx` | `DollarSign`, `TrendingUp`, `BarChart3`, `ShoppingCart`, `ArrowUpRight`, `ArrowDownRight`, `RefreshCw` |
| `supplier/reports/page.tsx` | `BarChart3`, `Download`, `FileText`, `TrendingUp`, `DollarSign`, `ShoppingCart` |
| `supplier/invoices/page.tsx` | `FileCheck2`, `Upload`, `Trash2`, `RefreshCw`, `AlertCircle`, `CheckCircle`, `XCircle`, `Clock`, `FileText` |
| `supplier/payouts/page.tsx` | `DollarSign`, `Clock`, `CheckCircle`, `ArrowDownRight`, `Send` |
| `supplier/payouts/FinanceSection.tsx` | `TrendingUp`, `ChevronDown`, `ChevronUp` |
| `supplier/profile/page.tsx` | `User`, `Mail`, `Building`, `Save`, `Shield`, `Lock`, `AlertCircle`, `Package`, `DollarSign`, `TrendingUp`, `Globe`, `MapPin`, `Phone`, `FileText`, `CheckCircle`, `Clock`, `XCircle`, `Star`, `ExternalLink`, `Eye`, `Plus`, `Trash2`, `ImageIcon`, `BadgeCheck`, `Upload`, `Link2`, `RefreshCw`, `Search`, `Loader2`, `Info` |
| `supplier/credibility/page.tsx` | `BadgeCheck`, `RefreshCw`, `Package`, `Star`, `FileCheck`, `ChevronRight` |
| `supplier/documents/page.tsx` | `FileCheck2`, `Upload`, `Trash2`, `RefreshCw`, `AlertCircle`, `CheckCircle`, `XCircle` |
| `supplier/regions/page.tsx` | `Globe`, `MapPin`, `Plus`, `X`, `Check`, `Search`, `Loader2`, `Info` |
| `supplier/returns/page.tsx` | `CheckCircle`, `Loader2`, `Package`, `PackageCheck`, `RefreshCw`, `Search`, `XCircle` |
| `supplier/terms/page.tsx` | `ScrollText`, `CheckCircle`, `Clock`, `AlertCircle` |
| `supplier/guide/page.tsx` | `BookOpen`, `CheckCircle2`, `Circle`, `ChevronDown`, `ChevronUp`, `UserCircle2`, `Package`, `FileText`, `BarChart3`, `ScrollText`, `Lightbulb`, `MessageCircleQuestion`, `Mail`, `ExternalLink`, `ShieldCheck`, `Star`, `MapPin`, `Wallet` |

### Admin Pages

| Page | Icons Used |
|------|-----------|
| `admin/dashboard/page.tsx` | `Users`, `Package`, `ShoppingCart`, `TrendingUp`, `Store`, `Search`, `Shield`, `UserPlus`, `AlertCircle`, `CheckCircle`, `XCircle`, `RefreshCw`, `ShieldCheck`, `Clock`, `Star` |
| `admin/login/page.tsx` | `Crown`, `LogIn`, `AlertCircle` |
| `admin/analytics/page.tsx` | `TrendingUp`, `DollarSign`, `ShoppingCart`, `Users`, `RefreshCw` |
| `admin/products/page.tsx` | `CheckCircle`, `XCircle`, `RefreshCw`, `Search`, `Flame`, `Star`, `Trash2`, `RotateCcw` |
| `admin/suppliers/page.tsx` | `CheckCircle`, `XCircle`, `RefreshCw`, `Search`, `Store`, `Star` |
| `admin/orders/page.tsx` | `Search`, `RefreshCw`, `ChevronLeft`, `ChevronRight`, `Trash2` |
| `admin/users/page.tsx` | `Search`, `Shield`, `ShieldOff`, `RefreshCw`, `Users`, `Trash2`, `KeyRound` |
| `admin/coupons/page.tsx` | `Plus`, `Pencil`, `Trash2`, `RefreshCw`, `Tag`, `X`, `Search` |
| `admin/flash-sales/page.tsx` | `Plus`, `Pencil`, `Trash2`, `RefreshCw`, `Zap`, `X`, `ToggleLeft`, `ToggleRight`, `Search` |
| `admin/banners/page.tsx` | `Plus`, `Pencil`, `Trash2`, `RefreshCw`, `Megaphone`, `X`, `Upload`, `ToggleLeft`, `ToggleRight`, `Eye`, `Search` |
| `admin/barcode/page.tsx` | `Camera`, `ScanLine`, `Keyboard`, `RefreshCw`, `CheckCircle`, `XCircle`, `Package`, `Truck`, `MapPin`, `AlertCircle` |
| `admin/returns/page.tsx` | `Search`, `RefreshCw`, `CheckCircle`, `XCircle`, `PackageCheck` |
| `admin/invoices/page.tsx` | `FileText`, `RefreshCw`, `AlertCircle`, `CheckCircle`, `Package`, `Truck`, `MapPin`, `Clock`, `Plus` |
| `admin/exports/page.tsx` | `AlertCircle`, `CheckCircle2`, `Clock3`, `Download`, `FileDown`, `Loader2` |
| `admin/email/page.tsx` | `Mail`, `BarChart3`, `FileText`, `Users`, `Send`, `Eye`, `MousePointer` |
| `admin/audit-logs/page.tsx` | `Search`, `RefreshCw`, `ChevronLeft`, `ChevronRight`, `ClipboardList` |
| `admin/product-verification/page.tsx` | `ShieldCheck`, `RefreshCw`, `Plus`, `CheckCircle`, `XCircle`, `AlertCircle`, `Package`, `Truck`, `MapPin` |
| `admin/logistics-partners/page.tsx` | `AlertCircle`, `CheckCircle`, `Globe`, `MapPin`, `Plus`, `RefreshCw`, `ShieldCheck`, `Truck`, `XCircle` |

### Admin Dashboard Tabs

| Tab | Icons Used |
|-----|-----------|
| `AuditTab.tsx` | `Search`, `RefreshCw`, `ChevronLeft`, `ChevronRight` |
| `BannerTab.tsx` | `RefreshCw`, `Sparkles`, `Save`, `Upload`, `Image` *(ImageIcon)* |
| `CouponsTab.tsx` | `Plus`, `Tag`, `RefreshCw`, `Trash2` |
| `FinanceTab.tsx` | `RefreshCw`, `DollarSign`, `TrendingUp`, `CreditCard`, `Truck`, `AlertTriangle`, `CheckCircle`, `XCircle`, `ArrowDownRight`, `ArrowUpRight`, `Banknote`, `FileText` |
| `FlashSalesTab.tsx` | `Sparkles` |
| `LogisticsPartnersTab.tsx` | `AlertCircle`, `Plus`, `RefreshCw`, `ShieldCheck`, `Trash2` |
| `LogisticsTab.tsx` | `RefreshCw` |
| `ModerationTab.tsx` | `CheckCircle`, `XCircle`, `RefreshCw` |
| `PayoutsTab.tsx` | `RefreshCw`, `CheckCircle`, `XCircle` |
| `SupplierDocumentsTab.tsx` | `FileCheck2`, `CheckCircle`, `XCircle`, `RefreshCw` |
| `TicketsTab.tsx` | `MessageSquare` |

### Logistics Partner Pages

| Page | Icons Used |
|------|-----------|
| `logistics-partner/dashboard/page.tsx` | `AlertTriangle`, `BarChart3`, `CheckCircle`, `Clock`, `ExternalLink`, `MapPinned`, `Package`, `Radio`, `RefreshCw`, `Route`, `Truck`, `Wallet`, `XCircle` |
| `logistics-partner/login/page.tsx` | `LogIn`, `AlertCircle`, `Truck` |
| `logistics-partner/register/page.tsx` | `AlertCircle`, `Truck`, `UserPlus` |
| `logistics-partner/scan/page.tsx` | `Camera`, `ScanLine`, `Keyboard`, `RefreshCw`, `CheckCircle`, `XCircle`, `Package`, `Truck`, `MapPin`, `AlertCircle` |
| `logistics-partner/shipments/page.tsx` | `AlertCircle`, `BadgeCheck`, `Building2`, `CheckCircle`, `Clock3`, `Globe`, `Info`, `Link2`, `MapPin`, `MapPinned`, `PackageCheck`, `Phone`, `Plus`, `RefreshCw`, `Save`, `Search`, `ShieldCheck`, `Trash2`, `Truck`, `User` |
| `logistics-partner/payouts/page.tsx` | `RefreshCw`, `Send`, `Wallet` |
| `logistics-partner/payouts/FinanceSection.tsx` | `TrendingUp`, `ChevronDown`, `ChevronUp`, `AlertTriangle` |
| `logistics-partner/profile/page.tsx` | `RefreshCw`, `CheckCircle`, `ChevronLeft`, `ChevronRight`, `X` |

### Email Admin Components

| Component | Icons Used |
|-----------|-----------|
| `admin/EmailTemplateManager.tsx` | `Plus`, `Edit2`, `Trash2`, `Eye`, `Code`, `Save`, `X` |
| `admin/EmailCampaignManager.tsx` | `Mail`, `Plus`, `BarChart3`, `Users`, `Eye`, `MousePointer`, `Calendar`, `MoreVertical`, `CheckCircle`, `Clock`, `AlertCircle`, `Loader2` |
| `admin/CreateCampaignForm.tsx` | `X`, `Save` |

---

## 5. Icon Usage by Page — Mobile App

### Bottom Tab Navigation

| Tab | Ionicons Used |
|-----|--------------|
| Home | `home` / `home-outline` |
| Products | `grid` / `grid-outline` |
| Search | `search` / `search-outline` |
| Cart | `cart` / `cart-outline` |
| Profile | `person` / `person-outline` |

### Auth Screens

| Screen | Icons Used |
|--------|-----------|
| `(auth)/login.tsx` | `alert-circle`, `shield-checkmark`, `car`, `refresh-circle`, `pricetag`, `eye`, `eye-off` |
| `(auth)/register.tsx` | `alert-circle`, `flash`, `notifications`, `heart`, `star` |

### Customer Screens

| Screen | Icons Used |
|--------|-----------|
| `(tabs)/home.tsx` | `trending-up`, `chevron-forward`, `cube-outline`, `flash` |
| `(tabs)/products/index.tsx` | `heart-outline`, `notifications-outline`, `cart-outline`, `person-outline`, `log-in-outline`, `cube-outline`, `grid`, `list`, `chatbubble-ellipses`, `sunny-outline`, `moon-outline` |
| `(tabs)/products/[id].tsx` | `share-outline`, `heart`/`heart-outline`, `car-outline`, `shield-checkmark-outline`, `refresh-outline`, `checkmark-circle-outline` |
| `(tabs)/cart.tsx` | `sparkles-outline`, `image-outline`, `add-circle-outline`, `pricetag`, `shield-checkmark-outline`, `car-outline`, `refresh-outline`, `lock-closed` |
| `(tabs)/profile.tsx` | `person-circle-outline`, `camera`, `person`, `alert-circle`, `checkmark-circle`, `gift-outline`, `share-social-outline`, `time-outline`, `chevron-forward` |
| `checkout.tsx` | `checkmark-circle`, `time-outline`, `checkmark`, `cart`, `location`, `card`, `car-outline` |
| `orders.tsx` | `filter-outline` |
| `wishlist.tsx` | `heart`, `share-outline`, `cart-outline` |
| `search.tsx` | `time-outline`, `search-outline`, `close` |
| `notifications.tsx` | `chevron-forward`, `checkmark-outline`, `close-outline` |
| `referrals.tsx` | `gift-outline`, `share-social-outline`, `copy-outline`, `flash-outline`, `refresh-outline` |

### Components

| Component | Icons Used |
|-----------|-----------|
| `CartItem.tsx` | `heart-outline`, `heart`, `trash-outline`, `remove`, `add` |
| `ProductCard.tsx` | `image-outline`, `sparkles`, `expand-outline`, `star`, `checkmark-circle`, `cart-outline` |
| `QuickViewModal.tsx` | `close`, `image-outline`, `star`, `checkmark`, `cart`, `maximize-2` *(Feather)* |
| `HeroBanner.tsx` | `sparkles`, `arrow-forward` |
| `HomeProductShowcase.tsx` | `grid`, `arrow-forward` |
| `LimitedTimeOfferBanner.tsx` | `flash`, `close` |
| `MobileSeasonalBanner.tsx` | `search` *(Feather)*, `x` *(Feather)* |
| `NewsletterSignup.tsx` | `checkmark-circle`, `mail`, `arrow-forward`, `mail-unread`, `alert-circle` |
| `OrderCard.tsx` | `cube-outline`, `locate-outline`, `chevron-forward` |
| `RecentlyViewed.tsx` | `time-outline`, `cube-outline` |
| `Recommendations.tsx` | `sparkles`, `cube-outline` |
| `AuthRequiredModal.tsx` | `close`, `lock-open`, `alert-circle`, `eye`/`eye-off` |

### Admin Screens

| Screen | Icons Used |
|--------|-----------|
| `admin/barcode.tsx` | `lock-closed`, `camera`, `camera-outline`, `search`, `close-circle`, `receipt-outline`, `barcode-outline`, `car-outline`, `location-outline`, `home-outline`, `checkmark-circle`, `edit-3` *(Feather)* |
| `admin/products.tsx` | `rotate-ccw`, `trash-2` *(Feather)* |
| `admin/suppliers.tsx` | `check-circle`, `check`, `x` *(Feather)* |
| `admin/returns.tsx` | `package` *(Feather)* |

### Supplier Screens

| Screen | Icons Used |
|--------|-----------|
| `supplier/products/new.tsx` | `zap` *(Feather)* |
| `supplier/products/[id].tsx` | `zap` *(Feather)* |

---

## 6. Centralized Registry Files

### Web App

**File:** `frontend/web_app/src/lib/icons.ts`  
Re-exports all Lucide icons used across the entire web app. Import from this file instead of directly from `lucide-react`.

```ts
// Usage example
import { Heart, ShoppingCart, Star } from "@/lib/icons";
```

### Mobile App

**File:** `frontend/mobile_app/lib/icons.ts`  
Exports `Ionicons` and `Feather` components plus typed name constants for all icons used.

```ts
// Usage example
import { Ionicons, Feather, IONICON, FEATHER } from "@/lib/icons";
// <Ionicons name={IONICON.CART} size={24} color={...} />
```

---

*To export this document as DOCX, open in VS Code and use the "Markdown PDF" or "Pandoc" extension to convert, or paste into Word and save.*
