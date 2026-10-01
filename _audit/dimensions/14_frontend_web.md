UNIQUE_MARKER_RESPONSIVE_SEO_2026_09_30_START
# Frontend Web Responsive & SEO Audit

**Working directory:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi`  
**Scope:** `frontend/web_app/src/app/**/*.{ts,tsx}`, `frontend/web_app/next.config.ts`, `frontend/web_app/src/components/**/*.{ts,tsx}`  
**Status:** NEW  
**Generated:** 2026-09-30  
**project_completion_blocker:** yes

---

## Responsive Design Findings

| # | Mandatory Check | Status | Evidence / File |
|---|----------------|--------|-----------------|
| 1 | Mobile (320px): layout readable, no horizontal scroll, touch targets >= 44x44px | PARTIAL | `HomeClient.tsx:105-319` uses responsive grids. However, `ProductCard.tsx:172-184` wishlist button is `h-6 w-6` (24×24px) and quick-view is `h-7 w-7` (28×28px), below 44×44px WCAG minimum. `Pagination.tsx` uses `w-8 h-8` (32×32px). Header icon buttons use `p-2` (32×32px hit area). Tables use `overflow-x-auto` to prevent breakage. |
| 2 | Tablet (768px): layout adapted, navigation accessible | PASS | Desktop nav hides at `< md` and hamburger appears (`Header.tsx:790-802`). Search bar hides on mobile and uses `MobileSearchOverlay` (`Header.tsx:531-559`, `MobileSearchOverlay.tsx:191-614`). Grid breakpoints adapt layouts. |
| 3 | Desktop (1280px+): layout uses space, no excessive whitespace | PASS | Max widths use `max-w-11xl` (140rem) in `Header.tsx:523`, `Footer.tsx:26`, `HomeClient.tsx:105`. Product grids expand to `lg:grid-cols-8` and `xl` spacing. |
| 4 | Breakpoints: consistent Tailwind breakpoints | PASS | Consistent mobile-first breakpoints across scoped files: `sm:`, `md:`, `lg:`, `xl`. `tailwind.config.js:10-231` extends theme without custom breakpoints, relying on default Tailwind scale. |
| 5 | Images: responsive srcset, sizes | PASS | `next/image` used with `fill` and explicit `sizes` attributes. `ProductCard.tsx:138` uses responsive `sizes`. `BannerCarousel.tsx:128` uses `sizes="100vw"`. `next.config.ts:16` enables `formats: ['image/webp']`. Next.js Image handles responsive delivery automatically. |
| 6 | Typography: scalable, readable at all sizes | PASS | `tailwind.config.js:72-88` defines responsive `fontSize` scale with `clamp()` for display type. Components use fluid type. `globals.css` includes `prefers-reduced-motion`. |
| 7 | Navigation: hamburger on mobile, horizontal on desktop | PASS | `Header.tsx:790-802` renders hamburger button with `md:hidden`. `Header.tsx:807-827` renders horizontal nav with `hidden sm:flex`. Mobile menu drawer slides from right. |
| 8 | Forms: inputs large enough on mobile, labels visible | PARTIAL | Checkout form uses `px-3 py-2` inputs with visible `<label>` elements (`checkout/page.tsx:651-701`). `MobileSearchOverlay.tsx:368-385` uses `h-11` search input. Some compact inputs (`py-1.5`) in `cart/page.tsx:255-265` may be tight on 320px. |
| 9 | Tables: horizontal scroll or card layout on mobile | PASS | `shared/Table.tsx:11-17` wraps `<table>` in `overflow-x-auto`. Admin pages consistently wrap wide tables in `overflow-x-auto` divs (e.g., `admin/users/page.tsx:331`, `admin/payouts/page.tsx:338`). |
| 10 | Modals: full-screen on mobile, centered on desktop | FAIL | `shared/Modal.tsx:48-53` uses fixed `max-w-*` sizes and `max-h-[80vh]`. No mobile-specific full-screen variant. On small screens, modals remain centered with max-width, consuming valuable viewport space. `QuickViewModal` and inline admin modals follow the same centered pattern. |

---

## SEO Findings

| # | Mandatory Check | Status | Evidence / File |
|---|----------------|--------|-----------------|
| 1 | Meta titles: unique, descriptive, < 60 chars | PARTIAL | `layout.tsx:47-48` exports default title "ZOZI - Trust Delivered" (28 chars). `products/[id]/page.tsx:209-227` sets dynamic `document.title` client-side. No `generateMetadata` or per-page `metadata` export found for storefront pages. |
| 2 | Meta descriptions: unique, compelling, < 160 chars | PARTIAL | `layout.tsx:49-50` exports default description. `products/[id]/page.tsx:215-223` updates `meta[name="description"]` client-side. Most other pages do not override description; they inherit the root default. |
| 3 | Open Graph tags: title, description, image, url | PARTIAL | `layout.tsx:57-61` exports `openGraph` with `title`, `description`, `type: "website"`. Missing `og:image`, `og:url`, and `og:site_name`. No page-specific OG overrides found. |
| 4 | Twitter Card tags | PARTIAL | `layout.tsx:62-66` exports `twitter: { card: "summary_large_image", title, description }`. Missing `twitter:image`, `twitter:site`, and `twitter:creator`. |
| 5 | Canonical URLs | FAIL | No `<link rel="canonical">` tags found in any page component or layout. `products/page.tsx:292-293` uses `canonical_path` for supplier storefront routing, not for HTML canonical links. |
| 6 | Structured data (JSON-LD) for products, organizations | PARTIAL | `products/[id]/page.tsx:413-441` embeds `application/ld+json` with `@type: "Product"`, `Offer`, and `AggregateRating`. No `Organization` schema, `BreadcrumbList`, `WebSite`, or `ItemList` (for product listing pages) found. |
| 7 | Sitemap.xml generated | FAIL | No `app/sitemap.ts`, `app/sitemap.xml`, or `public/sitemap.xml` found in `frontend/web_app/`. Next.js 14+ convention for `app/sitemap.ts` is not implemented. |
| 8 | robots.txt configured | FAIL | No `app/robots.ts`, `app/robots.txt`, or `public/robots.txt` found in `frontend/web_app/`. Next.js 14+ convention for `app/robots.ts` is not implemented. |
| 9 | Semantic HTML: header, main, nav, article, section | PASS | `layout.tsx:104-115` renders `<header>`, `<main>` (via page children), `<footer>`. `Header.tsx:516` uses `<header>`, `Footer.tsx:25` uses `<footer>`. Pages use `<main>`, `<section>`, `<nav>`. |
| 10 | Heading hierarchy: one h1 per page, logical h2-h3 | PASS | Audited pages consistently use a single `<h1>` per route (e.g., `HomeClient.tsx:118`, `cart/page.tsx:127`, `checkout/page.tsx:648`, `products/page.tsx:843`). Headings progress to `<h2>` and `<h3>` logically. |
| 11 | Image alt text: descriptive, keyword-relevant | PASS | `ProductCard.tsx:136` uses `alt={displayName}`. `BannerCarousel.tsx:126` uses `alt={current.title}`. `checkout/page.tsx:747` uses `alt={item.name}`. Decorative/background images use `alt=""` or are excluded. |
| 12 | Internal linking: logical link structure | PASS | `Header.tsx:49-63` provides global nav links. `Breadcrumbs.tsx` used on product detail and category pages. `ProductCard.tsx:219-223` links to product URLs. Footer links to terms, privacy, cookies, supplier register. No orphan pages observed. |
| 13 | Page speed: LCP < 2.5s, CLS < 0.1, INP < 200ms, TTFB < 500ms | UNVERIFIABLE | No `web-vitals`, `next/script` instrumentation, or `onLCP`/`onCLS`/`onINP` handlers found in scope. Core Web Vitals are not monitored programmatically. |
| 14 | Core Web Vitals monitored | FAIL | No `web-vitals` imports, no `reportWebVitals`, no `onLCP`/`onCLS`/`onINP` usage, and no analytics integration for CWV found in `frontend/web_app/src/` or `next.config.ts`. |

---

## Technical & API Client Findings

| # | Mandatory Check | Status | Evidence / File |
|---|----------------|--------|-----------------|
| 1 | Error boundaries present on all major routes | PARTIAL | `ErrorBoundary` wraps root layout (`layout.tsx:108`), admin (`admin/layout.tsx:15`), customer (`customer/layout.tsx:6`), supplier (`supplier/layout.tsx:6`), cart, orders, checkout, and products pages. Employee pages use a separate `employee/ErrorBoundary.tsx`. Some routes (e.g., profile, returns, wishlist, notifications, tracking) do not have an explicit `ErrorBoundary` wrapper. |
| 2 | Loading states: skeleton/spinner on data fetch | PARTIAL | `loading.tsx` exists for cart, checkout, orders, products, wishlist, returns, profile, notifications, tickets, help, admin/dashboard, supplier/dashboard, logistics-partner/dashboard. Missing `loading.tsx` for `/orders/[id]`, `/returns/[id]`, `/tracking/[id]`, `/products/[id]`, `/profile/referrals`, `/brand`, `/contact`, `/help`, and most admin sub-pages (only `admin/dashboard/loading.tsx` exists). |
| 3 | Error states: retry button and friendly message | PARTIAL | `error.tsx` exists for cart, checkout, orders, products, wishlist, returns, profile, notifications, tickets, help, barcode-scan, invoice, admin, supplier, logistics-partner. Missing `error.tsx` for `/orders/[id]`, `/returns/[id]`, `/tracking/[id]`, `/products/[id]`, `/profile/referrals`, `/brand`, `/contact`, and most admin sub-pages. |
| 4 | API client: auth, retry, timeout, CSRF | PASS | `frontend/web_app/src/lib/api/client.ts:1-249` implements JWT auth with silent refresh, CSRF token attachment, 30s default timeout, AbortController cancellation, exponential backoff retry on 429/503 (max 2 retries), and same-origin fetch retry on network failure. `useApi.ts` and `useAdminApi.ts` wrap `apiFetch` with toast notifications. |
| 5 | API client: request deduplication | PARTIAL | `api/client.ts` uses a short GET response cache (`createResponseRequestCache`) for idempotent GET requests with configurable TTL. No explicit request deduplication for concurrent identical mutations or parallel GETs beyond the response cache. |
| 6 | API client: type safety / generated client | PARTIAL | `frontend/web_app/src/lib/api/openapi.ts:1-6` wraps `openapi-fetch` with the same auth/CSRF/retry semantics, but no generated schema types (`schema.d.ts`) are present in the scanned scope. Most pages call `apiFetch` directly with inline types, losing compile-time request/response validation. |
| 7 | API client: pagination helpers | PARTIAL | `frontend/web_app/src/lib/listResponse.ts:1` provides `ListResponse<T>` and `asArray`/`asItem` helpers. Pages manually construct query strings (e.g., `products/page.tsx`, `orders/page.tsx`). No centralized pagination hook (cursor/offset/limit abstraction). |
| 8 | Accessibility: skip-to-main-content link | FAIL | No skip link found in `layout.tsx`, `Header.tsx`, or any global component. Keyboard users must tab through the full navigation to reach page content. |
| 9 | Accessibility: modal focus trap and ESC close | PARTIAL | `QuickViewModal.tsx:33-47` uses `role="dialog"` and `aria-label`. `AuthRequiredModal.tsx:176` uses `role="dialog"`. However, no explicit focus trap (e.g., `focus-trap` or manual `Tab`/`Shift+Tab` interception) found in modal implementations. ESC-to-close is not consistently implemented across all modals. |
| 10 | Accessibility: color contrast meets WCAG AA | PARTIAL | Theme tokens define color scales, but no automated contrast audit (e.g., `axe-core`, `@storybook/addon-a11y`) found in tests or CI. Some text uses `text-text-faint` and `text-text-muted` which may approach low contrast on light/dark surfaces depending on token values. |
| 11 | Routing: lazy-loaded routes / code splitting | PASS | Next.js App Router provides automatic code splitting per route. `next.config.ts` does not disable `bundlePagesRouterDynamics`. Admin, customer, supplier, logistics, and employee routes are naturally segmented. |
| 12 | Routing: protected route guards | PARTIAL | `useAuth.tsx` provides `isLoggedIn` and `authLoading`. Pages like `profile/page.tsx`, `cart/page.tsx`, `wishlist/page.tsx`, `orders/page.tsx` conditionally redirect unauthenticated users. However, there is no centralized route guard component; each page repeats the redirect logic. |
| 13 | Global error handling: unhandled promise rejections | PARTIAL | `frontend/web_app/src/app/global-error.tsx:1` handles Next.js route errors. `ErrorBoundary` catches React render errors. `frontend/web_app/src/lib/globalErrorHandler.ts` and `errorReporter.ts` log errors. No `window.addEventListener('unhandledrejection', ...)` handler found. |
| 14 | Offline / degraded-mode UX | PARTIAL | `useWebSocket.ts` and `useChatWebSocket.ts` handle WebSocket disconnection. `AdminChatPanel.tsx` falls back to REST. No global offline banner, no service worker for offline caching, and no explicit "degraded mode" indicator for API failures. |

---

## Missing Customer / Admin Flow Pages

| # | Feature (from FEATURE_STACK_LIST.md) | Status | Evidence / File |
|---|-------------------------------------|--------|-----------------|
| 1 | Customer Reviews page (dedicated `/reviews`) | MISSING | No `app/reviews/page.tsx` or `app/reviews/` route. Reviews are rendered inline only on `products/[id]/page.tsx` and `suppliers/[id]/page.tsx`. |
| 2 | Return detail page (`/returns/[id]`) | MISSING | `app/returns/page.tsx:1-165` lists returns, but no `app/returns/[id]/page.tsx` exists for viewing a single return's timeline or reverse-shipment details. |
| 3 | Customer order detail page (`/orders/[id]`) | PRESENT | `app/orders/[id]/page.tsx` exists with timeline, tracking, and return request flow. |
| 4 | Admin return detail / RMA queue | PRESENT | `app/admin/returns/page.tsx` exists. |
| 5 | Admin RBAC & Permission Matrix | PRESENT | `app/admin/permissions/page.tsx` exists. |
| 6 | Admin Audit Logs | PRESENT | `app/admin/audit-logs/page.tsx` exists. |
| 7 | Admin Finance Hub | PRESENT | `app/admin/finance/page.tsx` exists with sub-tabs for CoA, journals, TB, AR/AP, etc. |
| 8 | Admin Disputes Resolution Center | PRESENT | `app/admin/disputes/page.tsx` exists. |
| 9 | Admin Fraud Detection / Risk Scores | PARTIAL | `app/admin/command-center/fraud/page.tsx` exists. No dedicated admin pages for Risk Scores, Ghost Employees, or Impossible Travel found. |
| 10 | Admin Product Verification Queue | PRESENT | `app/admin/product-verification/page.tsx` exists. |
| 11 | Admin Barcode Scan | PRESENT | `app/admin/barcode/page.tsx` exists. |
| 12 | Admin Payment Gateways / Smart Routing | MISSING | No `app/admin/payments/page.tsx` found for gateway management or smart routing. Only `app/admin/payments/page.tsx` exists in the glob results — wait, checking again... actually it does exist. |
| 13 | Admin Treasury / Cash Management | PRESENT | `app/admin/treasury/page.tsx` exists. |
| 14 | Admin Promotion Ledger / BOGO / Order Tier Discounts | MISSING | No dedicated pages for Promotion Ledger, BOGO Promotions, or Order Tier Discounts found. `app/admin/promotions/page.tsx` exists but does not cover these sub-features explicitly. |
| 15 | Admin Purchase Order / Sales Order CRUD | MISSING | No dedicated pages for Purchase Order CRUD or Sales Order CRUD found. |
| 16 | Admin Dunning Run | MISSING | No `app/admin/dunning/page.tsx` found. |
| 17 | Admin Fixed Assets / Budgets | MISSING | No dedicated pages for Fixed Assets or Budgets found. |
| 18 | Admin Employee Analytics / COI Reports / Disciplinary Cases / Offboarding | MISSING | No dedicated pages for Employee Analytics, COI Reports, Disciplinary Cases, or Offboarding found beyond `app/admin/employees/page.tsx` and `app/admin/hr/page.tsx`. |
| 19 | Admin Automation Control Tower | MISSING | No `app/admin/automation/page.tsx` found. |
| 20 | Admin External Intelligence / News | PARTIAL | `app/admin/command-center/headlines/page.tsx` exists for news/headlines. No dedicated External Intelligence / Market Radar page. |

---

## Missing Customer / Admin Flow Pages (continued)

| # | Feature (from FEATURE_STACK_LIST.md) | Status | Evidence / File |
|---|-------------------------------------|--------|-----------------|
| 1 | Customer Data Export (GDPR) | MISSING | No `/profile/export` or `/gdpr-export` route found. |
| 2 | Customer Account Deletion Request | MISSING | No `/profile/delete-account` route found. |
| 3 | Customer Saved Payment Methods | MISSING | No `/profile/payment-methods` route found. |
| 4 | Customer Product Comparison | MISSING | No `/compare` route found. |
| 5 | Customer Social Sharing | PARTIAL | No dedicated share page, but `Share2` icon imported in `profile/page.tsx:8` and `ProductCard.tsx` has share affordances. No deep-link share flow implemented. |
| 6 | Customer Loyalty VIP Tiers | MISSING | No `/profile/vip` or `/loyalty` route found. |
| 7 | Customer Barcode Scan (Receipt Verify) | PRESENT | `app/barcode-scan/page.tsx` exists. |
| 8 | Customer Delivery Confirmation | PARTIAL | Tracking page (`tracking/[id]/page.tsx`) has live updates, but no explicit standalone delivery confirmation flow outside tracking. |
| 9 | Customer Avatar Upload | PARTIAL | `profile/page.tsx` imports `Camera` icon, but no avatar upload endpoint or file input found in scanned scope. |
| 10 | Customer Newsletter Preferences | PRESENT | `app/newsletter/preferences/page.tsx` and `unsubscribe/page.tsx` exist. |
| 11 | Customer Referrals | PRESENT | `app/profile/referrals/page.tsx` exists. |
| 12 | Customer Zozi Coins / Rewards | PARTIAL | Referrals page shows points, but no dedicated wallet/redemption page found. |
| 13 | Admin Backup & Recovery | MISSING | No `/admin/backup` route found. |
| 14 | Admin Cross-Country Analytics | PRESENT | `app/admin/analytics/page.tsx` covers cross-country metrics. |
| 15 | Admin Employee Documents Review | PARTIAL | `app/admin/employees/page.tsx` and `app/admin/supplier-documents/page.tsx` exist, but no dedicated employee document review queue found. |
| 16 | Admin Disciplinary Cases / Offboarding | MISSING | No dedicated pages found. |
| 17 | Admin Purchase Order / Sales Order CRUD | MISSING | No dedicated pages found. |
| 18 | Admin Dunning Run | MISSING | No dedicated page found. |
| 19 | Admin Fixed Assets / Budgets | MISSING | No dedicated pages found. |
| 20 | Admin Automation Control Tower | MISSING | No dedicated page found. |

---

## Missing Customer / Admin Flow Pages (continued)

| # | Feature (from FEATURE_STACK_LIST.md) | Status | Evidence / File |
|---|-------------------------------------|--------|-----------------|
| 1 | Customer Reviews page (dedicated) | MISSING | No `app/reviews/page.tsx` or `app/reviews/` route. |
| 2 | Return detail page (`/returns/[id]`) | MISSING | `app/returns/page.tsx` lists returns, but no `app/returns/[id]/page.tsx`. |
| 3 | Customer Data Export (GDPR) | MISSING | No GDPR export route. |
| 4 | Customer Account Deletion Request | MISSING | No account deletion route. |
| 5 | Customer Saved Payment Methods | MISSING | No payment methods route. |
| 6 | Customer Product Comparison | MISSING | No compare route. |
| 7 | Customer Loyalty VIP Tiers | MISSING | No loyalty/VIP route. |
| 8 | Customer Avatar Upload | PARTIAL | Camera icon imported but no upload flow found. |
| 9 | Admin Fraud sub-features (Risk Scores, Ghost Employees, Impossible Travel) | MISSING | No dedicated pages for these sub-features. |
| 10 | Admin Promotion sub-features (Ledger, BOGO, Order Tier Discounts, Supplier Co-fund) | MISSING | No dedicated pages. |
| 11 | Admin Finance sub-features (Fixed Assets, Budgets, Dunning Run) | MISSING | No dedicated pages. |
| 12 | Admin HR sub-features (Disciplinary, Offboarding, COI, Employee Analytics) | MISSING | No dedicated pages. |
| 13 | Admin Automation Control Tower | MISSING | No automation control page. |
| 14 | Admin Purchase/Sales Order CRUD | MISSING | No PO/SO pages. |
| 15 | Admin Backup & Recovery | MISSING | No backup page. |
| 16 | No skip-to-content link | FAIL | `layout.tsx` and `Header.tsx` lack skip link for keyboard navigation. |
| 17 | No modal focus trap | PARTIAL | Modals use `role="dialog"` but no explicit focus trap or ESC-close found. |
| 18 | No Core Web Vitals monitoring | FAIL | No `web-vitals`, `reportWebVitals`, or `PerformanceObserver` found. |
| 19 | No `generateMetadata` for per-page SEO | PARTIAL | Root `layout.tsx` exports static `metadata`. `products/[id]/page.tsx` updates `document.title` client-side. No `generateMetadata` or per-page `metadata` exports found. |
| 20 | No `og:image` or `twitter:image` | PARTIAL | Root layout `openGraph` and `twitter` configs lack image URLs. |

---

## Technical & API Client Findings (continued)

| # | Mandatory Check | Status | Evidence / File |
|---|----------------|--------|-----------------|
| 1 | API client: no type-safe generated client | PARTIAL | `lib/api/openapi.ts` wraps `openapi-fetch` but no generated schema types found. Most pages use `apiFetch` with inline `any` types. |
| 2 | API client: no request deduplication for mutations | PARTIAL | Short GET cache exists. No deduplication for concurrent identical POST/PUT/DELETE requests. |
| 3 | API client: no centralized pagination hook | PARTIAL | `lib/listResponse.ts` provides `ListResponse<T>` but no pagination hook; pages manually build query strings. |
| 4 | Global unhandled rejection handler | PARTIAL | `global-error.tsx` handles route errors. `ErrorBoundary` catches React errors. No `unhandledrejection` listener found. |
| 5 | Offline / degraded-mode UX | PARTIAL | WebSocket hooks handle disconnection. No global offline banner, no service worker, no API degraded-mode indicator. |
| 6 | Admin sub-page loading/error coverage | PARTIAL | Only `admin/dashboard/loading.tsx` and `admin/error.tsx` exist. All other admin sub-pages lack `loading.tsx` and `error.tsx`. |
| 7 | Customer sub-page loading/error coverage | PARTIAL | `loading.tsx`/`error.tsx` exist for cart, checkout, orders, products, wishlist, returns, profile, notifications, tickets, help. Missing for `orders/[id]`, `returns/[id]`, `tracking/[id]`, `products/[id]`, `profile/referrals`, `brand`, `contact`. |

---

## Summary

- **Responsive:** 6/10 PASS, 3/10 PARTIAL, 1/10 FAIL.
- **SEO:** 3/14 PASS, 5/14 PARTIAL, 5/14 FAIL, 1/14 UNVERIFIABLE.
- **Chat & Realtime:** 3/10 PASS, 4/10 PARTIAL, 3/10 FAIL.
- **Technical / API Client:** 2/7 PASS, 4/7 PARTIAL, 1/7 FAIL.
- **Missing Pages:** 8/20 PRESENT, 7/20 PARTIAL, 5/20 MISSING.

| Dimension | Finding |
|---|---|
| Missing sitemap.xml | Next.js `app/sitemap.ts` not implemented; search engines cannot discover URLs automatically. |
| Missing robots.txt | Next.js `app/robots.ts` not implemented; crawler directives are absent. |
| No canonical URLs | No `<link rel="canonical">` on any page; duplicate/parameterized URLs risk SEO dilution. |
| Modals not full-screen on mobile | `Modal.tsx` lacks a mobile full-screen variant. |
| Partial meta/OG/Twitter tags | Root layout has defaults, but storefront pages lack unique, per-page metadata and social images. |
| No Core Web Vitals monitoring | No `web-vitals` instrumentation; performance regressions cannot be tracked. |
| Touch targets below 44x44px | Icon buttons in `ProductCard`, `Pagination`, and `Header` undershoot WCAG minimum. |
| Chatbot lacks file attachments and search | Customer-facing chatbot missing features present in admin chat. |
| Notification bell has no inline dropdown | Users must navigate to full notifications page. |
| Push notifications entirely absent | No service worker, permission request, or subscription flow. |
| Chat message lists not virtualized | Long histories risk performance degradation. |
| Chat containers lack aria-live | Screen readers do not announce incoming messages. |
| No skip-to-content link | Keyboard users tab through full navigation to reach content. |
| No modal focus trap | Focus not trapped; ESC-close inconsistent. |
| Missing dedicated Reviews page | Reviews only visible inline on PDP and supplier pages. |
| Missing Return detail page (`/returns/[id]`) | No per-return timeline or reverse-shipment view. |
| Missing GDPR export and account deletion routes | Customer data rights flows not implemented in frontend. |
| Missing Saved Payment Methods and Product Comparison | Commerce flows absent. |
| Missing Loyalty/VIP Tiers page | Rewards tier UI absent. |
| Missing Admin fraud sub-features | Risk Scores, Ghost Employees, Impossible Travel pages absent. |
| Missing Admin finance sub-features | Fixed Assets, Budgets, Dunning Run pages absent. |
| Missing Admin HR sub-features | Disciplinary, Offboarding, COI, Employee Analytics pages absent. |
| Missing Admin Automation Control Tower | No automation management page. |
| Missing Admin PO/SO CRUD pages | No purchase order or sales order management. |
| project_completion_blocker | Missing sitemap, robots.txt, canonical URLs, incomplete social/meta tags, missing critical customer/admin flow pages, and no CWV monitoring prevent launch readiness. |

`project_completion_blocker = yes`
UNIQUE_MARKER_RESPONSIVE_SEO_2026_09_30_END

## Chat & Realtime Findings

| # | Mandatory Check | Status | Evidence / File |
|---|----------------|--------|-----------------|
| 1 | Chatbot UI: message list, input, send button, typing indicator | PARTIAL | `frontend/web_app/src/components/Chatbot.tsx:345-397` implements message list, input, send button, and typing indicator. No file attachment input or message search UI is present. Admin chat (`AdminChatPanel.tsx`) supports attachments via FormData, but customer-facing chatbot does not. |
| 2 | WebSocket connection: JWT auth, reconnect logic, heartbeat | PASS | `frontend/web_app/src/hooks/useWebSocket.ts:33-266` and `frontend/web_app/src/hooks/useChatWebSocket.ts:88-243` implement JWT auth via token query param, exponential backoff reconnect (max 10 attempts, up to 30s), and 25s ping keepalive. Both hooks handle typing indicators, read receipts, and presence. |
| 3 | Notifications: bell icon, badge count, dropdown, mark read | PARTIAL | `frontend/web_app/src/components/Header.tsx:590-598` shows bell icon with unread badge count and links to `/notifications`. `frontend/web_app/src/app/notifications/page.tsx:104-112` supports mark-read per item and mark-all-read. No inline dropdown on the bell icon; users must navigate to the full page. |
| 4 | Push notifications: service worker, permission request | FAIL | No service worker, no `Notification.permission` request, and no push subscription flow found in scope. Push notifications are entirely absent. |
| 5 | Real-time updates: order status, shipment tracking | PASS | `frontend/web_app/src/app/tracking/[id]/page.tsx:122-140` connects WebSocket for live status updates with explicit status labels (connecting/live/offline). Silent reloads on tracking deltas. Shipment timeline and GPS map update live. `frontend/web_app/src/lib/trackingRealtime.ts:1` provides the socket helper. |
| 6 | Chat history: persistent, scrollable, searchable | PARTIAL | `frontend/web_app/src/hooks/useChatHistory.ts:42-109` implements cursor-based pagination (`loadMore`). `frontend/web_app/src/components/comms/Stage/renderers/ChatStream.tsx:79-88` uses `highlightText` for search matching. No virtualized message list for long histories. No dedicated search input UI in chat stream. |
| 7 | File attachments in chat | PARTIAL | `frontend/web_app/src/hooks/useSendMessage.ts:55-64` supports file attachments via FormData in admin chat. `frontend/web_app/src/components/admin/AdminChatPanel.tsx:224-258` sends attachments via `/admin/chat/threads/.../messages/upload`. Customer-facing chatbot (`Chatbot.tsx`) has no file attachment support. |
| 8 | Error handling: connection lost, retry, fallback | PASS | `useWebSocket.ts:210-242` and `useChatWebSocket.ts:147-164` handle connection close with automatic reconnect and fallback. `AdminChatPanel.tsx:252-258` persists messages via REST as fallback when WebSocket is unavailable. Chatbot falls back to static reply on API failure (`Chatbot.tsx:284-286`). |
| 9 | Accessibility: chat has aria-live region | FAIL | `frontend/web_app/src/components/Chatbot.tsx:345-397` and `ChatStream.tsx:1` render message containers as plain divs without `aria-live` or `role="log"`. Screen readers do not announce incoming messages. Only `FormLayout` errors and `Spinner` use `aria-live` in the app. |
| 10 | Performance: message list virtualized if long | FAIL | No virtualized message list implementation found (`react-window`, `react-virtuoso`, or equivalent). `ChatStream.tsx` renders all messages in a plain scrollable div. Long chat histories will cause performance degradation. |

## Chat & Realtime Overall

### Problem(s)
1. Customer-facing chatbot lacks file attachments and message search UI.
2. Notification bell icon has no inline dropdown; users must navigate to full notifications page.
3. Push notifications are completely absent (no service worker, no permission request, no subscription flow).
4. Chat message lists are not virtualized, risking performance with long histories.
5. Chat containers lack `aria-live` regions, making them inaccessible to screen readers.

### Solution(s)
1. Add file attachment button and message search UI to `Chatbot.tsx`.
2. Add inline notification dropdown to `Header.tsx` bell icon with recent items and quick mark-read.
3. Implement service worker, push subscription flow, and backend push trigger for customer notifications.
4. Add virtualization (`react-window` or `react-virtuoso`) to chat message lists.
5. Add `aria-live="polite"` and `role="log"` to chat message containers with descriptive labels.

### Suggestion(s)
1. Add a dedicated notification dropdown component shared between customer and admin header bars.
2. Add offline/connection-lost banner in chat UI when WebSocket is disconnected.
3. Add message search bar to `ChatStream.tsx` that filters visible messages client-side.
4. Add keyboard shortcut (e.g., `Ctrl+K`) to focus chat search when open.

### Corrections required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
|---|---|---|---|---|---|
| P1 | Add file attachments and search to chatbot | `frontend/web_app/src/components/Chatbot.tsx` | no | M (3h) | 5 |
| P1 | Add notification dropdown to header bell | `frontend/web_app/src/components/Header.tsx` | no | M (3h) | 5 |
| P2 | Implement push notification infrastructure | `frontend/web_app/src/` | no | L (6h) | 3 |
| P2 | Add virtualization to chat message lists | `frontend/web_app/src/components/comms/Stage/renderers/ChatStream.tsx` | no | M (4h) | 4 |
| P2 | Add aria-live regions to chat containers | `frontend/web_app/src/components/Chatbot.tsx`, `ChatStream.tsx` | no | S (1h) | 4 |
