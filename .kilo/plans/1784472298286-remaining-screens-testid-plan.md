# Plan: Add `testID` roots to remaining mobile_app screens

## Context
We are building a comprehensive Playwright e2e suite against the Expo **web** build (SPA on `http://127.0.0.1:19006`) for an e-commerce mobile app with customer, supplier, logistics-partner, and admin roles. Playwright can only select stable hooks via `testID` (web renders RN `testID` as `data-testid`). Many screens already have a root `testID` (e.g. `chatbot-screen`, `cart-screen`, `supplier-dashboard-screen`). This plan closes the remaining gaps so the e2e specs can assert on a screen root instead of brittle text/role selectors.

**Note:** An earlier progress summary was stale. The following top-level screens *already* have root `testID`s and need **no change**: `chatbot`, `archive`, `coupons`, `wishlist`, `offers`, `flash-sales`, `returns`, `orders`, `profile` (tabs), `write-review`, `change-password`, `edit-profile`, `referrals`, `invoice`, `tickets`, `help`, `cart` (logged-out + main), `notifications`, `settings`, plus all of `supplier/dashboard`, `supplier/products/index`, `supplier/products/new`, `supplier/orders`, `supplier/support`, `logistics-partner/dashboard`, `logistics-partner/shipments`, `logistics-partner/scan`, `logistics-partner/analytics`, `admin/dashboard`, and `checkout`.

## Rule for every change
- Add exactly **one** `testID` on the screen's **outer container** (the `<View>`/`<ScrollView>`/`<SafeAreaView>` immediately inside the top `return (`), using the kebab id `<area>-<screen>-screen` or the existing convention.
- Do **not** add comments. Do **not** change behavior, styles, or layout.
- Preserve existing `style`/`contentContainerStyle` props; just add `testID="..."` as the first attribute.
- Keep the existing `tsc --noEmit` green; `testID` is already a valid RN prop everywhere.
- For files with bracket names (`[id]`, `[slug]`, `[code]`), edit with a **literal path** (PowerShell escaping), not glob.

## A. Genuinely-UI screens missing a root `testID` — ADD one

### Auth / customer modals
- `app/(auth)/verify-email.tsx` — outer `<ScrollView contentContainerStyle={[s.container, styles.scroll]}>` (line ~57): add `testID="verify-email-screen"`.
- `app/notification-preferences.tsx` — outer `<View style={[styles.container, { justifyContent: "center", alignItems: "center" }]}>` (line ~145): add `testID="notification-preferences-screen"`.
- `app/push_notifications.tsx` — outer `<View style={{ flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: theme.colors.surface0 }}>` (line ~280): add `testID="push-notifications-screen"`.
- `app/barcode-scan.tsx` — outer `<View style={[s.container, { paddingTop: 0 }]}>` (line ~182): add `testID="barcode-scan-screen"`.
- `app/chatbot-history.tsx` — outer container (line ~164, `styles.sessionInfo` View): add `testID="chatbot-history-screen"`.
- `app/ticket-detail.tsx` — outer container (the `return (` after line ~99): add `testID="ticket-detail-screen"`.
- `app/tracking/[id].tsx` — outer container (line ~278/289 region; it already has child `tracking-live-status`, but no root): add `testID="tracking-screen"` on the screen root.
- `app/returns/[id].tsx` — outer container (line ~85 `<ScrollView>` / line ~63 loading View): add `testID="return-detail-screen"` on the main content container.
- `app/orders/[id].tsx` — outer container (top `return (`): add `testID="order-detail-screen"`.
- `app/r/[code].tsx` — outer container (line ~39 `return (`): add `testID="referral-landing-screen"`.

### Products (tabs)
- `app/(tabs)/products/index.tsx` — already has `testID="products-screen"` inside the card wrapper at line ~446; add root `testID="products-screen"` is already present — **no change needed** (verified). Skip.
- `app/(tabs)/products/[id].tsx` — already has `testID="product-detail-screen"` (line ~415) — **no change needed**. Skip.

### Supplier area
- `app/supplier/login.tsx` — outer `<View>` at top `return (` (line ~49): add `testID="supplier-login-screen"`.
- `app/supplier/register.tsx` — outer `<View>` (line ~45): add `testID="supplier-register-screen"`.
- `app/supplier/profile.tsx` — outer container (line ~727 `return (`): add `testID="supplier-profile-screen"`.
- `app/supplier/analytics.tsx` — outer `<View>` (line ~88/115): add `testID="supplier-analytics-screen"`.
- `app/supplier/payouts.tsx` — outer `<View>` (line ~123): add `testID="supplier-payouts-screen"`.
- `app/supplier/inventory.tsx` — outer container (top `return (`): add `testID="supplier-inventory-screen"`.
- `app/supplier/bulk.tsx` — outer `<View>` (line ~168): add `testID="supplier-bulk-screen"`.
- `app/supplier/credibility.tsx` — outer `<View>` (line ~104): add `testID="supplier-credibility-screen"`.
- `app/supplier/disputes.tsx` — outer `<View>` (line ~17): add `testID="supplier-disputes-screen"`.
- `app/supplier/documents.tsx` — outer `<View>` (line ~147): add `testID="supplier-documents-screen"`.
- `app/supplier/guide.tsx` — outer `<ScrollView>` (line ~96): add `testID="supplier-guide-screen"`.
- `app/supplier/label.tsx` — outer `<View>` (line ~95): add `testID="supplier-label-screen"`.
- `app/supplier/logistics.tsx` — outer `<View style={s.container}>` (line ~267): add `testID="supplier-logistics-screen"`.
- `app/supplier/regions.tsx` — outer `<View>` (line ~132): add `testID="supplier-regions-screen"`.
- `app/supplier/reports.tsx` — outer `<View>` (line ~142): add `testID="supplier-reports-screen"`.
- `app/supplier/returns.tsx` — outer container (line ~91 `return (`): add `testID="supplier-returns-screen"`.
- `app/supplier/terms.tsx` — outer `<View>` (line ~117): add `testID="supplier-terms-screen"`.
- `app/supplier/upload.tsx` — outer container (top `return (`): add `testID="supplier-upload-screen"`.
- `app/supplier/products/[id].tsx` — outer container (line ~352/459 region): add `testID="supplier-product-edit-screen"`.
- `app/supplier/labels/[id].tsx` — outer container (top `return (`): add `testID="supplier-label-detail-screen"`.

### Logistics-partner area
- `app/logistics-partner/login.tsx` — outer `<View>` (line ~56): add `testID="logistics-login-screen"`.
- `app/logistics-partner/register.tsx` — outer container (top `return (`): add `testID="logistics-register-screen"`.
- `app/logistics-partner/payouts.tsx` — outer `<View>` (line ~167): add `testID="logistics-payouts-screen"`.
- `app/logistics-partner/profile.tsx` — outer `<View>` (line ~345): add `testID="logistics-profile-screen"`.
- `app/logistics-partners/index.tsx` — outer container (top `return (`): add `testID="logistics-partners-screen"`.
- `app/logistics-partners/[id].tsx` — outer `<View>` (line ~80): add `testID="logistics-partner-detail-screen"`.

### Admin area
- `app/admin/login.tsx` — outer `<View>` (line ~61): add `testID="admin-login-screen"`.
- `app/admin/users.tsx` — outer `<View>` (line ~153): add `testID="admin-users-screen"`.
- `app/admin/products.tsx` — outer `<View>` (line ~154): add `testID="admin-products-screen"`.
- `app/admin/analytics.tsx` — outer `<ScrollView>` (line ~118): add `testID="admin-analytics-screen"`.
- `app/admin/suppliers.tsx` — outer container (line ~118 `return (`): add `testID="admin-suppliers-screen"`.
- `app/admin/returns.tsx` — outer `<View>` (line ~115): add `testID="admin-returns-screen"`.
- `app/admin/invoices.tsx` — outer `<View>` (line ~153): add `testID="admin-invoices-screen"`.
- `app/admin/exports.tsx` — outer `<View>` (line ~126): add `testID="admin-exports-screen"`.
- `app/admin/email.tsx` — outer `<View>` (line ~160): add `testID="admin-email-screen"`.
- `app/admin/barcode.tsx` — outer `<View>` (line ~263): add `testID="admin-barcode-screen"`.
- `app/admin/audit-logs.tsx` — outer container (line ~129 `return (`): add `testID="admin-audit-logs-screen"`.
- `app/admin/logistics-partners.tsx` — outer `<View>` (line ~135): add `testID="admin-logistics-partners-screen"`.
- `app/admin/product-verification.tsx` — outer `<View>` (line ~133): add `testID="admin-product-verification-screen"`.

### Suppliers public / misc
- `app/suppliers/[id].tsx` — outer `<View>` (line ~58): add `testID="supplier-public-profile-screen"`.
- `app/supplier-storefront/[slug].tsx` — **REDIRECT** (renders `null`, pushes `/suppliers/${slug}`). No UI → **no change**. Skip.
- `app/newsletter/preferences.tsx` — outer container (line ~158 `return (`): add `testID="newsletter-preferences-screen"`.
- `app/newsletter/unsubscribe.tsx` — outer container (line ~55 `return (`): add `testID="newsletter-unsubscribe-screen"`.

## B. Redirect / re-export screens — NO CHANGE (no UI to test)
- `app/index.tsx` (root redirect)
- `app/products/index.tsx` → redirects to `/(tabs)/products`
- `app/products/[id].tsx` → redirects to `/(tabs)/products/[id]`
- `app/(tabs)/orders/index.tsx` → re-exports `../../orders`
- `app/supplier-storefront/[slug].tsx` → pushes `/suppliers/${slug}`
- `app/_layout.tsx`, `app/(auth)/_layout.tsx`, `app/(tabs)/_layout.tsx`, `app/supplier/_layout.tsx`, `app/logistics-partner/_layout.tsx` — layout wrappers, not screens (they render `<Slot/>`/children). No root testID needed; the child screen provides it. **Skip.**

## C. Validation
1. `cd D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\mobile_app`
2. `npx tsc --noEmit -p tsconfig.json` must exit 0 (regression guard).
3. Rebuild web SPA if the running server serves a stale bundle: `npx expo export --platform web` (or `expo export -p web`) into `web-dist/`, then restart `scripts/serve-spa.py --port 19006`.
4. Quick Playwright smoke (reuse running 19006): for a sample of the new ids, `await page.goto('/<route>'); await expect(page.getByTestId('<id>')).toBeVisible();` — e.g. `verify-email-screen`, `supplier-login-screen`, `admin-users-screen`, `logistics-payouts-screen`, `tracking-screen`, `order-detail-screen`, `return-detail-screen`.
5. Confirm `inventory.tsx`, `upload.tsx`, `logistics-partner/register.tsx`, `supplier/products/[id].tsx`, `supplier/labels/[id].tsx`, `logistics-partners/[id].tsx`, `suppliers/[id].tsx`, `r/[code].tsx`, `ticket-detail.tsx`, `tracking/[id].tsx` outer containers were located correctly (they had no `testID` and non-obvious `return (` lines) — verify the chosen container is the one actually rendered.

## D. Out of scope (this plan)
- Writing the Playwright `globalSetup`/`specs` — tracked as the next task after this lands.
- Updating `documents/MOBILE_APP_SCREEN_LIST.md` — tracked separately.
- Fixing the 17 Jest `react-test-renderer` failures (React 19.2 `act` tooling issue, not app bugs).

## Open question (non-blocking)
- `app/supplier/products/[id].tsx` has multiple `return (` branches (loading/error/main). Confirm the **main edit** branch is the one receiving `testID` (the others can keep none, or receive the same id — either is fine for e2e since only one renders at a time). Recommend: add `testID="supplier-product-edit-screen"` on the main content container only.
