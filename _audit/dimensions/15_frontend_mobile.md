# DIMENSION: Frontend Mobile

## Summary
- Confirmation: ❌
- Files inspected: 34
- Files compliant: 18
- Files with findings: 16
- Laws implicated: [L-13, L-16, L-187, L-188, L-189, L-190, L-191, L-192, L-193, L-194, L-195, L-196, L-243, L-244, L-245, L-246, L-247, L-248, L-249, L-250, L-251, L-252, L-253, L-254, L-255, L-256, L-257, L-258, L-259, L-260]
- Findings: 15
- P0: 3  P1: 3  P2: 5  P3: 4
- Clusters: 3
- Average confidence: 4.3/5
- Average evidence strength: multiple
- Status: NEW: 12 · COMPILED: 0 · RESOLVED: 3 · DEFERRED: 0 · INVALID: 0
- Completion blockers: 2 yes · 3 partial · 9 no

## Findings

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Evidence strength | Truth level | Claim state | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker |
|----|-------|--------|---------|-----------|---------|--------|-------|-----|--------|----------|------------|-------------------|-------------|-------------|---------|--------|------|----------|--------------|------------|--------|-------------------|
| MOB-001 | mobile | NEW | CLUSTER-missing-mobile-deps | frontend/mobile_app/app/_layout.tsx:43 | `require("expo-notifications")` used for push token registration | `expo-notifications` declared in `package.json` dependencies | Push notification SDK is used but not declared as a dependency | Add `expo-notifications` to `frontend/mobile_app/package.json` dependencies | S (1h) | P0 | 5 | multiple | L0 | VERIFIED | frontend/mobile_app/app/push_notifications.tsx:12 | `grep "expo-notifications" frontend/mobile_app/package.json` | `frontend/mobile_app/lib/__tests__/notificationsScreen.test.ts` | `git revert <commit>` | Push notifications, auth flow | none | MOB-005 | yes |
| MOB-002 | mobile | NEW | CLUSTER-missing-mobile-deps | frontend/mobile_app/app/barcode-scan.tsx:21 | `require("expo-camera")` used for barcode scanning | `expo-camera` declared in `package.json` dependencies | Camera SDK is used but not declared as a dependency | Add `expo-camera` to `frontend/mobile_app/package.json` dependencies | S (1h) | P0 | 5 | multiple | L0 | VERIFIED | frontend/mobile_app/app/admin/barcode.tsx:26 | `grep "expo-camera" frontend/mobile_app/package.json` | `frontend/mobile_app/lib/__tests__/barcodeScan.test.tsx` | `git revert <commit>` | Barcode scanning, logistics scanning, admin scanning | none | MOB-005 | yes |
| MOB-003 | mobile | NEW | | frontend/mobile_app/package.json:22 | `expo: ~57.0.9` | `expo: 57.0.20+` per TECHNOLOGY_STACK.md §16 | Expo SDK version is 11 patch versions behind target | Bump `expo` to `~57.0.20` in `frontend/mobile_app/package.json` | S (1h) | P2 | 5 | single | L0 | VERIFIED | | `grep '"expo": "~57.0.9"' frontend/mobile_app/package.json` | `cd frontend/mobile_app && pnpm install` | `git revert <commit>` | Expo ecosystem compatibility | none | none | no |
| MOB-004 | mobile | NEW | | frontend/mobile_app/package.json:27 | `react-native: 0.81.4` | `react-native: 0.86.3` per TECHNOLOGY_STACK.md §16 | React Native version is 0.5 versions behind target | Bump `react-native` to `0.86.3` in `frontend/mobile_app/package.json` | S (1h) | P2 | 5 | single | L0 | VERIFIED | | `grep '"react-native": "0.81.4"' frontend/mobile_app/package.json` | `cd frontend/mobile_app && pnpm install` | `git revert <commit>` | RN core compatibility | none | none | no |
| MOB-005 | mobile | NEW | CLUSTER-missing-mobile-deps | frontend/mobile_app/app.json:30-43 | No `expo-updates` plugin and no `eas.json` | `expo-updates` for OTA JS bundle updates per TECHNOLOGY_STACK.md §16 | OTA update capability is not configured | Add `expo-updates` plugin to `app.json`, create `eas.json`, add `expo-updates` to dependencies | M (3h) | P1 | 4 | multiple | L0 | VERIFIED | | `test -f frontend/mobile_app/eas.json && grep "expo-updates" frontend/mobile_app/package.json` | `frontend/mobile_app/e2e/mobile-smoke.spec.ts` | `git revert <commit>` | OTA hotfixes, app store compliance | none | MOB-001 | partial |
| MOB-006 | mobile | NEW | | frontend/mobile_app/app/_layout.tsx:153-214 | Push token registered on login, unregistered on logout | Token lifecycle tied to auth state with best-effort persistence | Push token sync is implemented but lacks retry on failure | Add retry logic with exponential backoff for `registerPushToken` and `unregisterPushToken` | M (2h) | P2 | 4 | single | L0 | VERIFIED | frontend/mobile_app/lib/api.ts:2264-2280 | `grep -A5 "registerPushToken" frontend/mobile_app/app/_layout.tsx` | `frontend/mobile_app/lib/__tests__/pushNotifications.test.ts` | `git revert <commit>` | Push notification delivery | none | none | no |
| MOB-007 | mobile | NEW | | frontend/mobile_app/app.json:15-44 | No `privacyPolicy` URL, no `ios.infoPlist.NSUserTrackingUsageDescription` | App store compliance requires privacy policy URL and tracking permission description | Store metadata is incomplete for app store submission | Add `privacyPolicy` URL, `ios.infoPlist.NSUserTrackingUsageDescription`, and `android.permissions` to `app.json` | M (3h) | P1 | 4 | single | L0 | VERIFIED | | `grep "privacyPolicy" frontend/mobile_app/app.json` | Manual App Store Connect / Google Play Console upload | `git revert <commit>` | App store submission | none | none | partial |
| MOB-008 | mobile | NEW | | frontend/mobile_app/lib/paymentService.ts:121-149 | Dynamic `require("@tap-as/sdk-react-native")` with try/catch fallback | Payment SDKs installed or hosted checkout used consistently | Tap SDK is referenced but not installed; falls back to error | Remove dynamic SDK imports or install `@tap-as/sdk-react-native` and `@paytabs/react-native-paytabs` | M (3h) | P2 | 3 | single | L0 | VERIFIED | frontend/mobile_app/app/checkout.tsx:830-874 | `grep "TapSDK" frontend/mobile_app/lib/paymentService.ts` | `frontend/mobile_app/lib/__tests__/paymentService.test.ts` | `git revert <commit>` | Alternative payment methods (Tap, PayTabs, Thawani) | none | none | no |
| MOB-009 | mobile | NEW | | frontend/mobile_app/lib/socialAuth.ts:55-76 | Google GSI script loaded dynamically for web | Social login implemented for Google; Facebook and Apple stubbed | Partial social login implementation | Implement Facebook and Apple social login or document as deferred | M (4h) | P3 | 3 | single | L0 | VERIFIED | frontend/mobile_app/lib/api.ts:2301-2311 | `grep "signInWith" frontend/mobile_app/lib/socialAuth.ts` | `frontend/mobile_app/lib/__tests__/socialAuth.test.ts` | `git revert <commit>` | Social login conversion rate | none | none | no |
| MOB-010 | mobile | NEW | | frontend/mobile_app/lib/api.ts:226-304 | In-memory GET cache with TTL and deduplication | Persistent cache or offline queue for API responses | Cache is volatile and lost on app background | Add persistent cache layer using `expo-secure-store` or implement offline queue with `NetInfo` | L (8h) | P2 | 3 | single | L0 | VERIFIED | frontend/mobile_app/lib/api.ts:226-304 | `grep "GET_CACHE_TTL" frontend/mobile_app/lib/api.ts` | `frontend/mobile_app/lib/__tests__/apiCache.test.ts` | `git revert <commit>` | Offline user experience | none | none | partial |
| MOB-011 | mobile | NEW | CLUSTER-employee-route-gap | frontend/mobile_app/app:1 | No `employee/` route directory exists | `employee` module routes required per ARCHITECTURE_STACK.md §2 and §13 | Employee actor has no mobile UI; role type exists in types but no screens | Create `app/employee/` route group with login, dashboard, and module-specific screens | L (8h) | P1 | 5 | multiple | L0 | VERIFIED | frontend/mobile_app/lib/authStore.ts:19 | `ls frontend/mobile_app/app/employee` | `frontend/mobile_app/lib/__tests__/employeeScreens.test.tsx` | `git revert <commit>` | Employee self-service, HR, attendance, payroll | none | none | partial |
| MOB-012 | mobile | NEW | CLUSTER-stripe-sdk-orphan | frontend/mobile_app/package.json:20 | `@stripe/stripe-react-native: ^0.50.0` installed | Stripe SDK used for native card checkout or removed if unused | Stripe SDK is installed but not imported anywhere in mobile source code | Either integrate `@stripe/stripe-react-native` in checkout flow or remove from dependencies | M (3h) | P2 | 4 | multiple | L0 | VERIFIED | frontend/mobile_app/app/checkout.tsx:831 | `grep -r "stripe-react-native" frontend/mobile_app/app frontend/mobile_app/lib` | `frontend/mobile_app/lib/__tests__/checkoutScreen.test.tsx` | `git revert <commit>` | Card payment UX, bundle size | none | none | no |
| MOB-013 | mobile | NEW | | frontend/mobile_app/app.json:15-44 | No `android.permissions` array in app.json | Android permissions should be declared for camera, notifications, location per actual usage | Permissions are only requested at runtime but not pre-declared in Android manifest | Add `android.permissions` to `app.json` with `CAMERA`, `POST_NOTIFICATIONS`, `ACCESS_FINE_LOCATION` | S (1h) | P1 | 4 | single | L0 | VERIFIED | | `grep "permissions" frontend/mobile_app/app.json` | `cd frontend/mobile_app && pnpm expo prebuild --clean` | `git revert <commit>` | Android runtime permission crashes | none | MOB-002 | partial |
| MOB-014 | mobile | NEW | | frontend/mobile_app/lib/api.ts:199-212 | Hardcoded `DEFAULT_API_BASE` with emulator IPs (`10.0.2.2`, `localhost`) | API base URL from environment variable with no hardcoded fallbacks | Emulator IPs leak into production if `EXPO_PUBLIC_API_URL` is unset | Remove hardcoded fallbacks; require `EXPO_PUBLIC_API_URL` in all environments | S (0.5h) | P2 | 4 | single | L0 | VERIFIED | frontend/mobile_app/lib/api.ts:199-206 | `grep "DEFAULT_API_BASE" frontend/mobile_app/lib/api.ts` | `frontend/mobile_app/lib/__tests__/api.test.ts` | `git revert <commit>` | Production API connectivity | none | none | no |
| MOB-015 | mobile | RESOLVED | CLUSTER-missing-mobile-deps | frontend/mobile_app/lib/api.ts:5 | Static import of `expo-secure-store` for secure token persistence | `expo-secure-store` declared in `package.json` dependencies | Core auth token storage SDK is imported but not declared as a dependency | AUDIT_CLAIM_WRONG — expo-secure-store IS declared via `app.json` plugins array (line 32), the canonical Expo SDK 57 pattern; present in pnpm-lock.yaml and node_modules | S (1h) | P0 | 5 | multiple | L0 | VERIFIED | frontend/mobile_app/app/_layout.tsx:25, frontend/mobile_app/app/push_notifications.tsx:12 | `grep "expo-secure-store" frontend/mobile_app/package.json` | `frontend/mobile_app/lib/__tests__/api.test.ts` | `git revert <commit>` | Auth flow, token storage, push notification preferences | none | none | yes |

## Over all

### Problem(s)
1. Critical mobile dependencies (`expo-notifications`, `expo-camera`) are used in source code but missing from `package.json`, causing runtime failures in production builds.
2. OTA update infrastructure (`expo-updates`, `eas.json`) is entirely absent, preventing hotfixes without app store review.
3. App store compliance metadata (privacy policy, tracking usage description, Android permissions) is missing from `app.json`, blocking submission.
4. No offline behavior strategy exists: no `NetInfo` monitoring, no persistent queue, no sync mechanism — the app is online-only.
5. Alternative payment SDKs (Tap, PayTabs, Thawani) are referenced in code but not installed, relying solely on hosted checkout fallbacks.
6. Employee module has no mobile route group or screens, despite being a first-class actor in the architecture.
7. `@stripe/stripe-react-native` is installed but unused in source code, adding bundle weight without value.
8. API base URL has hardcoded emulator fallbacks that could leak into production.
9. `expo-secure-store` is statically imported for secure token persistence but missing from `package.json` dependencies.

### Solution(s)
1. Add missing dependencies (`expo-notifications`, `expo-camera`, `expo-updates`) to `package.json` and run `pnpm install`.
2. Configure EAS Update with `eas.json` and add `expo-updates` plugin to `app.json`.
3. Add required app store metadata to `app.json` (privacy policy URL, permission descriptions, Android permissions array).
4. Implement offline queue using `@react-native-community/netinfo` and persistent storage.
5. Either install payment SDKs or remove dynamic import stubs to avoid runtime errors.
6. Create `app/employee/` route group with login, dashboard, and role-guarded screens.
7. Remove `@stripe/stripe-react-native` or integrate it into the checkout flow.
8. Remove hardcoded API base fallbacks and require `EXPO_PUBLIC_API_URL` in all environments.
9. Add `expo-secure-store` to `frontend/mobile_app/package.json` dependencies.

### Suggestion(s)
1. Consider deferring offline behavior to a post-launch phase if mobile is not launch-critical.
2. Add Maestro flows for mobile critical paths to complement Playwright tests.
3. Implement `HAS_<SDK>` pattern for optional native modules to match backend provider availability flags.
4. Align mobile route structure with web actor grouping: `(customer)/`, `auth/`, `admin/*`, `supplier/*`, `logistics-partner/*`, `employee/*`.

### Corrections required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
|---|---|---|---|---|---|
| P0 | Add `expo-notifications` to dependencies | `frontend/mobile_app/package.json` | yes | S | 5 |
| P0 | Add `expo-camera` to dependencies | `frontend/mobile_app/package.json` | yes | S | 5 |
| P1 | Configure OTA updates with expo-updates and eas.json | `app.json`, `eas.json` | partial | M | 4 |
| P1 | Add app store compliance metadata to app.json | `app.json` | partial | M | 4 |
| P1 | Create employee route group with screens | `frontend/mobile_app/app/employee/` | partial | L | 5 |
| P2 | Bump expo and react-native to target versions | `package.json` | no | S | 5 |
| P2 | Add persistent offline queue or document deferral | `lib/offlineQueue.ts` | partial | L | 3 |
| P2 | Install or remove alternative payment SDK stubs | `lib/paymentService.ts` | no | M | 3 |
| P2 | Remove hardcoded API base fallbacks | `lib/api.ts` | no | S | 4 |
| P0 | Add `expo-secure-store` to dependencies | `frontend/mobile_app/package.json` | yes | S | 5 |
| P2 | Remove unused Stripe SDK or integrate it | `package.json`, `app/checkout.tsx` | no | M | 4 |
| P3 | Complete social login for Facebook and Apple | `lib/socialAuth.ts` | no | M | 3 |
| P3 | Add retry logic for push token registration | `app/_layout.tsx` | no | M | 4 |
| P3 | Add Maestro mobile test flows | `e2e/maestro/` | no | M | 3 |

## Clusters

| Cluster ID | Phase | Depends on phase | Root cause | Members | Recommended fix | Recommended test | Completion blocker |
|---|---|---|---|---|---|---|---|
| CLUSTER-missing-mobile-deps | mobile | tech | Native SDKs used via dynamic require but not declared in package.json | MOB-001, MOB-002, MOB-005, MOB-015 | Add all missing Expo SDKs to package.json and run pnpm install | `grep` for each SDK in package.json | yes |
| CLUSTER-employee-route-gap | mobile | architecture | Employee module defined in architecture but no mobile route group or screens exist | MOB-011 | Create `app/employee/` with login, dashboard, and role-guarded screens | `ls frontend/mobile_app/app/employee` | partial |
| CLUSTER-stripe-sdk-orphan | mobile | tech | Stripe SDK installed as dependency but never imported in mobile source code | MOB-012 | Remove unused dependency or integrate into checkout flow | `grep -r "stripe-react-native" frontend/mobile_app/app frontend/mobile_app/lib` | no |
