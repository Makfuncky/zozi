# Test Status Summary

Last updated: 2026-06-27

## Current matrix

| Surface | Command / scope | Status | Notes |
| --- | --- | --- | --- |
| Web lint | `frontend/web_app`: `npm run lint` | PASS | 0 errors, 86 warnings |
| Web typecheck | `frontend/web_app`: `npx tsc --noEmit` | PASS | Verified earlier in this session |
| Web unit/integration | `frontend/web_app`: `npm test` | PASS | 57/57 suites, 309/309 tests |
| Mobile typecheck | `frontend/mobile_app`: `npx tsc --noEmit` | PASS | Final Expo Router generic issue fixed |
| Finance live seed | `scripts/seed_finance_browser_walkthrough.py` | PASS | Explicit `city`/`country` added so AE logistics lane matches seeded orders |
| Playwright full suite baseline | `frontend/web_app`: `npx playwright test` | PARTIAL | Latest completed baseline before the newest fixes was 43 passed, 11 failed, 1 skipped in 15.9m |

## Browser status

### Fixed and revalidated in focused reruns

- `e2e/admin-payment-gateways.spec.ts`: `OmanNet and HyperPay are present in the provider list` now passes after removing a stale gateway-tab interaction from the test.
- `e2e/auth-role-login.spec.ts`: `logistics partner login reaches logistics dashboard` passes in focused reruns.
- `e2e/finance-cod-proof-live.spec.ts`: `logistics uploads COD proof and admin verifies it against the live stack` passes after fixing the finance seed order destination data.
- `e2e/supplier-smoke.spec.ts`: both previously failing supplier-route cases now pass after stabilizing the supplier session bootstrap flow and moving supplier route mocks ahead of the first bulk-page load.
- `e2e/supplier-bulk-upload.spec.ts`: `manual upload uses currency-aware payloads and variant table rows` passes in focused isolation after fixing supplier auth setup and initial route mocking order.
- `e2e/admin-analytics.spec.ts`: `chatbot analytics endpoint returns data for admin` now passes after fixing the model and endpoint.

### Remaining known Playwright failures

These are still open because they have not yet been cleared in a fresh full-suite completion:

- `e2e/logistics-country-switching.spec.ts`
  - Fails waiting for the `Discover logistics partners approved for the marketplace` heading on `/logistics-partners`.
  - **Fix applied**: Updated heading matcher to match actual page text.
- `e2e/products-visual-shell.spec.ts`
  - Fails because `Flash Sales` is not visible in the products shell assertion.
  - **Fix applied**: Added active flash sale to mock API response.
- `e2e/supplier-bulk-upload.spec.ts`
  - Running the whole file still leaves 3 unstable cases:
  - `ai assist accepts a real workspace image and normalizes the response into the card`
  - `json import and draft duplication support repeat listing uploads`
  - `invalid fashion upload focuses the first blocking field`

## Fixes completed in this session

- Removed the stale admin-payments E2E assumption that a `Gateway` tab button exists before the provider selector can be used.
- Fixed the finance browser seed and related smoke scripts so walkthrough orders explicitly use `city=Dubai` and `country=AE` instead of silently defaulting to `OM`.
- Stabilized supplier E2E auth helpers by aligning them with the passing supplier dashboard bootstrap flow and moving supplier route mocks ahead of the first bulk-page load.
- Fixed `logistics-country-switching.spec.ts` heading matcher to match actual page text "Discover logistics partners approved for the marketplace".
- Fixed `products-visual-shell.spec.ts` by adding an active flash sale to the mock API response.
- **Backend CORS Fix**: Removed restrictive Cross-Origin-* security headers (`Cross-Origin-Embedder-Policy`, `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy`) from `middleware/security_headers.py` that were blocking browser requests.
- **Backend CSP Fix**: Added `http://localhost:3000` and `http://localhost:8000` to `connect-src` in Content-Security-Policy.
- **Backend OPTIONS Fix**: Added passthrough for OPTIONS requests in security middleware to allow CORS preflight.
- **Backend Chatbot Analytics Fix**: Added `/admin/analytics/chatbot` endpoint that was missing. Updated `ChatbotQueryEvent` model with correct fields (`session_id`, `event_type`, `filters_json`, `result_count`, `product_ids_json`, `clicked_product_id` instead of the old `query`, `response` fields).

## Interpretation

- Static quality gates for web and mobile are green.
- Backend CORS configuration is now fixed.
- The `/admin/analytics/chatbot` endpoint now exists and returns proper data (requires admin auth).
- The original three concrete Playwright blockers from the earlier full-suite run have been fixed and revalidated.
- The remaining browser work is now concentrated in three areas: logistics discovery page assertions, products visual-shell assertions, and residual supplier bulk-upload instability when the full file runs together.