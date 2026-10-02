# DIMENSION: 15 Frontend Mobile

## Summary
- Confirmation: ❌
- Files inspected: 18 (app/*.tsx screens + layouts, lib/*.ts stores, components/*.tsx, e2e/*, package.json, app.json, AndroidManifest.xml)
- Files compliant: 9
- Files with findings: 9
- Laws implicated: [L-40, L-85, L-228, L-229, L-230, L-246, L-247, L-248, L-249, L-250, L-251, L-252, L-253]
- Findings: 9
- P0: 0  P1: 2  P2: 4  P3: 3
- Clusters: 2
- Average confidence: 4/5
- Average evidence strength: single
- Status: NEW: 9 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0
- Completion blockers: 1 yes · 0 partial · 8 no

## Findings

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Evidence strength | Truth level | Claim state | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MOB-001 | mobile | COMPILED | CLUSTER-ota-disabled | android/app/src/main/AndroidManifest.xml:17 | `expo.modules.updates.ENABLED=false` | `expo-updates` installed and ENABLED=true per TECHNOLOGY_STACK.md §16 | OTA updates are explicitly disabled in the Android manifest; no `expo-updates` package in package.json | Set ENABLED=true; add `expo-updates` to dependencies; configure `runtimeVersion` policy | M (2h) | P1 | 5 | single | L0 | VERIFIED | _most_imp_docx/TECHNOLOGY_STACK.md:248 | `expo-updates` present in `npm ls` | Add unit test asserting `Updates.checkForUpdateAsync()` does not throw | Revert manifest meta-data and remove package | All hotfix delivery, crash recovery without store review | none | MOB-002 | yes |
| MOB-002 | mobile | INVALID | CLUSTER-ota-disabled | _most_imp_docx/TECHNOLOGY_STACK.md:248 | `expo-updates` listed as "Always" for OTA JS bundle updates | `expo-updates` absent from `frontend/mobile_app/package.json` dependencies | Declared in TECHNOLOGY_STACK.md but not installed; contradicts the "Always" recommendation | Install `expo-updates`; wire `Updates.checkForUpdateAsync()` in `_layout.tsx` | M (2h) | P1 | 5 | single | L0 | VERIFIED | frontend/mobile_app/package.json:16 | `npm ls expo-updates` returns version | Add `expo-updates` to package.json dependencies | Remove from package.json | OTA hotfix capability, crash recovery | none | MOB-001 | yes |
| MOB-003 | mobile | COMPILED | CLUSTER-offline-gap | frontend/mobile_app/lib/api.ts:238 | In-memory GET cache with 60 s TTL for deduplication | `@react-native-community/netinfo` for connectivity detection; persistent offline queue per ARCHITECTURE_STACK.md §3 mobile_app/lib | No offline connectivity detection; mutations fail silently when network is unavailable; no queue-and-retry | Add `@react-native-community/netinfo`; gate mutations on connectivity; implement queue-and-retry | M (3h) | P2 | 4 | single | L0 | VERIFIED | frontend/mobile_app/lib/api.ts:294 | Toggle airplane mode; verify mutation shows user-facing error | Add test mocking NetInfo.disconnect | Remove netinfo dependency and queue code | Order submission, cart mutations, checkout | none | MOB-004 | no |
| MOB-004 | mobile | COMPILED | CLUSTER-offline-gap | frontend/mobile_app/app/_layout.tsx:153 | `PushTokenSync` registers token on login only | Offline-aware push registration with retry; token re-registration on connectivity restore | No offline detection; push token registration silently dropped when device is offline at login | Wrap `registerPushToken` in retry triggered by NetInfo connectivity event | S (1h) | P3 | 4 | single | L0 | VERIFIED | frontend/mobile_app/app/_layout.tsx:181 | Airplane mode on first launch; observe no token registered after restoring connectivity | Add test with NetInfo mock | Remove NetInfo listener | Push notification delivery | MOB-003 | none | no |
| MOB-005 | mobile | COMPILED | CLUSTER-social-stubs | frontend/mobile_app/lib/authStore.ts:107 | `loginWithGoogle` throws "Google sign-in not configured" error | Functional Google Sign-In with `expo-auth-session` + `@react-native-google-signin/google-signin` | Native Google and Facebook sign-in are placeholder stubs; calling them raises a runtime error | Install and wire Google and Facebook native SDKs; remove throw stubs | L (6h) | P2 | 5 | single | L0 | VERIFIED | frontend/mobile_app/lib/socialAuth.ts:141 | Tap "Sign in with Google" in app; verify Google account picker appears | Add Detox test for Google sign-in flow | Revert to stubs; disable social buttons in UI | Social login conversion rate | none | MOB-006 | no |
| MOB-006 | mobile | COMPILED | CLUSTER-social-stubs | frontend/mobile_app/lib/socialAuth.ts:139 | Facebook and Apple throw "not available in this environment yet" | Functional Facebook Sign-In with `@react-native-fbsdk-next`; Apple Sign-In with `expo-apple-authentication` | All three social providers (Google, Facebook, Apple) are non-functional on native; only Google GSI works on web | Install and wire Facebook and Apple native SDKs | L (8h) | P3 | 4 | single | L0 | VERIFIED | frontend/mobile_app/lib/socialAuth.ts:141 | Attempt Facebook/Apple sign-in on device; verify provider screen appears | Add test per provider | Revert to stubs | Social login coverage | MOB-005 | none | no |
| MOB-007 | mobile | COMPILED | none | frontend/mobile_app/package.json:20 | `@stripe/stripe-react-native: ^0.50.0` listed in dependencies | TECHNOLOGY_STACK.md §15 declares `@stripe/react-stripe-js` 6.9.0 (web) + Stripe Elements; mobile uses web redirect per checkout.tsx:94 | Mobile has the native Stripe SDK installed but checkout.tsx uses a web redirect for card payment ("Redirects to the web app for secure card checkout") — contradictory strategy | Choose one strategy: either wire native Stripe SDK (remove web redirect) or remove native SDK dependency | M (3h) | P2 | 4 | single | L0 | VERIFIED | frontend/mobile_app/app/checkout.tsx:94 | Verify card payment opens in-app webview vs native SDK flow | Test checkout with card method | Revert to prior strategy | Card payment UX, PCI scope | none | none | no |
| MOB-008 | mobile | COMPILED | none | frontend/mobile_app/lib/paymentService.ts:121 | `processTapPayment` uses `require("@tap-as/sdk-react-native")` dynamic require | `@tap-as/sdk-react-native`, `@paytabs/react-native-paytabs`, `@thawani/rn-sdk` listed in package.json | Three payment SDK packages are dynamically required but not listed in package.json; they will crash with "module not found" at runtime if invoked | Either install the SDKs and register them, or remove the native SDK wrappers and use hosted redirect only | M (3h) | P2 | 4 | single | L0 | VERIFIED | frontend/mobile_app/lib/paymentService.ts:121 | Trigger Tap payment on device; observe module-not-found error | Add test mocking each SDK require | Remove SDK wrapper functions | Regional payment (Tap, PayTabs, Thawani) | none | none | no |
| MOB-009 | mobile | INVALID | none | frontend/mobile_app/e2e/ | Playwright `.spec.ts` and `.e2e.js` files; `.detoxrc.js` present but no Detox test specs | TECHNOLOGY_STACK.md §16 declares `Detox 20.0.0+` for "all mobile critical paths" | Detox is configured (`.detoxrc.js` present) but zero Detox test specs exist; only Playwright web-viewport tests exercise the mobile web build | Write Detox specs for login, browse, add-to-cart, checkout critical paths; configure CI to run `detox test` | L (8h) | P2 | 4 | single | L0 | VERIFIED | frontend/mobile_app/e2e/ | `ls e2e/*.test.ts` — no Detox specs; only `.spec.ts` (Playwright) | Add `e2e/auth.test.ts` (Detox format) | None needed | Mobile E2E regression safety net | none | none | no |

## Over all

### Problem(s)
1. OTA updates are fully disabled (ENABLED=false in AndroidManifest) and `expo-updates` is absent from package.json — the app cannot receive hotfixes without a full store review cycle (MOB-001, MOB-002).
2. No offline connectivity detection exists; the app silently fails mutations when the network is unavailable and has no queue-and-retry mechanism (MOB-003, MOB-004).
3. Social sign-in (Google, Facebook, Apple) is non-functional on native — two of three providers are throw stubs, and Google requires native SDK packages that are not installed (MOB-005, MOB-006).
4. Payment strategy is contradictory: the native Stripe SDK is installed but card checkout redirects to web; three regional SDKs (Tap, PayTabs, Thawani) are dynamically required but not installed in package.json (MOB-007, MOB-008).
5. Detox E2E tests do not exist despite the technology stack mandating them; only Playwright web-viewport tests are present (MOB-009).
6. `expo-secure-store` web fallback uses `localStorage` (unencrypted) for tokens — consistent with the in-code comment but a security downgrade on web vs. native Keychain/Keystore.

### Solution(s)
1. Re-enable `expo-updates` in AndroidManifest (`ENABLED=true`), add the `expo-updates` package, and wire `checkForUpdateAsync()` in `_layout.tsx`.
2. Add `@react-native-community/netinfo`; gate mutations on connectivity; implement a queue-and-retry pattern for failed mutations.
3. Install `@react-native-google-signin/google-signin`, `@react-native-fbsdk-next`, and `expo-apple-authentication`; wire each provider end-to-end.
4. Choose one payment strategy: either commit to native Stripe SDK (remove web redirect) or remove `@stripe/stripe-react-native` and rely on hosted redirect; install or remove the Tap/PayTabs/Thawani wrappers.
5. Write at least three Detox specs (auth, browse-to-cart, checkout) matching the Playwright critical-path coverage.
6. Document the `localStorage` web fallback as accepted risk for non-native platforms; ensure `expo-secure-store` is used on native.

### Suggestion(s)
1. Add a `NETWORK_STATUS` Zustand store (or reuse `@react-native-community/netinfo` slice) so screens can show an offline banner and queue mutations.
2. Wrap `registerPushToken` in a connectivity-aware retry so push registration survives offline first-launch.
3. Add `expo-updates` to the `detox` build configuration so OTA runtime is exercised in E2E.
4. Audit the `web-dist/` build artifact — it is checked into the repo and should be `.gitignore`d.
5. Pin all `^` version ranges in package.json to exact versions matching the lockfile to prevent accidental drift.

### Corrections required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
|---|---|---|---|---|---|
| P1 | Re-enable `expo-updates` and add package | `AndroidManifest.xml`, `package.json`, `_layout.tsx` | yes | M | 5 |
| P1 | Resolve Stripe SDK vs web redirect contradiction | `checkout.tsx`, `paymentService.ts` | no | M | 4 |
| P2 | Add offline detection and mutation queue | `lib/api.ts`, new `lib/netInfo.ts` | no | M | 4 |
| P2 | Write Detox E2E specs for critical paths | `e2e/auth.test.ts`, `e2e/checkout.test.ts` | no | L | 4 |
| P2 | Wire or remove regional payment SDK wrappers | `paymentService.ts`, `package.json` | no | M | 4 |
| P2 | Implement functional native social sign-in | `authStore.ts`, `socialAuth.ts` | no | L | 4 |
| P3 | Add push notification retry on connectivity restore | `_layout.tsx` | no | S | 4 |
| P3 | Remove `web-dist/` from repo or add to `.gitignore` | `.gitignore` | no | S | 5 |
| P3 | Pin `^` ranges in package.json to exact lockfile versions | `package.json` | no | S | 5 |
