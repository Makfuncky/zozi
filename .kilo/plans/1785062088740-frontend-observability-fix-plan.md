# Frontend Observability Fix — Backend-Primary Error Reporting

## Goal
Make `/api/frontend-errors` → Loki the guaranteed frontend crash pipeline. Remove all manual runtime Sentry init/calls from the client bundle to eliminate double-init collisions and the `sentry_sdk is not installed` warning. Keep `withSentryConfig` only for source-map upload if desired, or remove it entirely.

## Rationale
- `/api/frontend-errors` already exists and routes to backend logging + Loki via Promtail.
- Production emits `sentry_sdk is not installed; skipping Sentry init`.
- `globalErrorHandler.ts`, `ErrorBoundary.tsx`, `sentry.client.config.ts`, `sentry.server.config.ts`, and `instrumentation.ts` each independently initialize or call Sentry — any subset can collide.
- Removing runtime Sentry calls eliminates the double-init category entirely and shrinks the client bundle.

## Changes

### 1. Strip all manual Sentry from the client bundle

**Files: `src/lib/globalErrorHandler.ts`, `src/components/ErrorBoundary.tsx`, `src/app/error.tsx`, `src/app/global-error.tsx`**

- Delete `_initSentry()`, `_reportToSentry()`, and `sentryInitialized` from `globalErrorHandler.ts`.
- `initialize()` should only register `unhandledrejection` / `window.onerror`, call `logFrontendError()` + `handleApiError()`, and maintain breadcrumbs in memory.
- Remove `require("@sentry/nextjs")` from `ErrorBoundary.tsx::tryReportToSentry` and `handleReport`.
- `componentDidCatch` must always call `logFrontendError()` + `tryReportToBackend()` regardless of DSN.
- `handleReport` fallback: copy error details (message + stack + componentStack + errorId) to clipboard. Remove Sentry `showReportDialog`.
- Update `src/app/error.tsx` and `src/app/global-error.tsx` to call `logFrontendError(error, "nextjs-app-error", { digest })` and optionally `navigator.sendBeacon("/api/frontend-errors", ...)` in production.

### 2. Remove runtime-only Sentry config files

**Files: `sentry.client.config.ts`, `sentry.server.config.ts`, `instrumentation.ts`**

- Delete all three. They are no longer needed once `globalErrorHandler` and `ErrorBoundary` no longer call `Sentry.init()` or import `@sentry/nextjs`.
- If the team still wants source-map uploads in CI, keep `withSentryConfig` in `next.config.ts` with `sourcemapUpload: process.env.NODE_ENV === "production"` and both `disableClientWebpackPlugin` / `disableServerWebpackPlugin` set to `true`. This keeps the SDK out of the runtime bundle while preserving build-time source maps.

### 3. Expedite `next.config.ts`

- Either remove `withSentryConfig` entirely, or keep it with both webpack plugins disabled and only `sourcemapUpload` enabled.
- No runtime client SDK should be injected.

### 4. Fix logger args mutation (`src/lib/logger.ts`)

- Replace `args.shift()` with `const message = Array.isArray(args) && args.length > 0 ? args[0] : "";` and use the rest of the args array only for serialization.
- The `formatLogEntry` function is unused dead code; remove it or keep it as the single serialization helper used by all methods.
- Ensure `remoteQueue.push({ level, message: String(message), args: serializedArgs, timestamp })` never mutates the caller's `args`.

### 5. Fix `errorLogging.ts` ID generation (shared package)

- Replace `${Date.now()}-${entries.length + 1}` with `crypto.randomUUID()` (browser-native, supported by all target browsers per the existing plan).
- Keep the existing `MAX_ERROR_LOGS = 50` and `sessionStorage` persistence; the shared package already trims to `MAX_ERROR_LOGS`.

### 6. Fix `errorReporter.ts` overflow

- Change `if (queue.length > MAX_QUEUE_SIZE)` to `if (queue.length >= MAX_QUEUE_SIZE)`.
- Assign a UUID `id` to each queued entry (align with `errorLogging.ts`).
- Add `fingerprint: `${source}:${message}`` to each queued item before dedup check.

### 7. Fix `categorizeError` (`src/lib/api.ts`)

- Lowercase `error.message` before matching.
- Add explicit `error instanceof DOMException && error.name === "AbortError"` branch → `timeout_error` / `retryable: true`.
- Add `"networkrequestfailed"` as a case-insensitive match.
- Keep existing `Response` status-code branches intact.

### 8. Harden module-level state in `api.ts`

- Wrap `_accessToken`, `_refreshPromise`, and `_traceId` in a single shared mutable store object: `const _store = { accessToken: null as string | null, refreshPromise: null, traceId: null as string | null }`.
- This doesn't fully survive HMR, but it makes the state footprint explicit. Full persistence is out of scope (the existing `zozi_has_session` flag already gates silent refresh).

### 9. Add root `loading.tsx`

- Minimal skeleton at `src/app/loading.tsx` to prevent layout shift on first load.

## Validation

1. **Smoke test**: `npm run build` and `npm run start`. Verify zero `@sentry/nextjs re-initialized` warnings and no `[@sentry/nextjs]` runtime warnings in console.
2. **Error path test**: Throw inside a client component wrapped in `<ErrorBoundary>`. Verify Loki receives the event via `/api/frontend-errors` and `logFrontendError` captures breadcrumbs.
3. **Logger smoke test**: `logger.debug("msg", {a:1}, {b:2})` — confirm the remote queue payload has `message: "msg"` and the original `args` are preserved without mutation.
4. **ID uniqueness test**: Fire 1000 `logFrontendError` calls in a tight loop. Assert no duplicate IDs.
5. **Overflow test**: Fill the `errorReporter` queue to `MAX_QUEUE_SIZE + 5` and assert length === `MAX_QUEUE_SIZE`.
6. **Case-insensitive categorize test**: Pass `new Error("Connection Timeout")` and `new DOMException("The operation was aborted.", "AbortError")` and assert `{ category: "timeout_error", retryable: true }`.
7. **Next.js error boundary test**: Throw inside a page component. Verify `global-error.tsx` renders and a `sendBeacon` call is made.
8. **Build artifact check**: Confirm `node_modules/.cache` / `.next` output does not contain `sentry.client.config.ts` artifacts or a second `Sentry.init()` call.

## Scope / Out of Scope

| Item | Decision |
|------|----------|
| Keep Sentry as optional build-time source-map upload | In scope (`withSentryConfig` optionally kept, both webpack plugins disabled) |
| Remove `@sentry/nextjs` from `package.json` | Out of scope — `withSentryConfig` may still need it at build time |
| Persist `_accessToken` across HMR via `sessionStorage` | Out of scope — current `_store` wrapper is sufficient |
| Add `loki_push` endpoint to `logger.ts` remote forwarding | Out of scope — existing backend `/api/frontend-errors` is the primary path |
| Add quota-detection to `localStorage` queue | Watchlist — not required for the break/fix |

## Open Question

**Should `withSentryConfig` be removed entirely, or kept for CI source-map uploads?**

- **Remove** if the team has no plan to use Sentry releases. Simplest, zero runtime footprint.
- **Keep** with both webpack plugins disabled if the team wants Sentry release tracking + source maps without runtime integration. Source maps still upload; no client SDK is injected.
