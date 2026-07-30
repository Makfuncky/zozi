# Frontend Audit & Remediation Plan

## Context

The ZOZI frontend (`frontend/web_app`) is a Next.js 15.4.5 + React 19.2.3 app with manual error handling, logging, and Sentry instrumentation layered on top of `@sentry/nextjs` (v8) build-time integration via `withSentryConfig`. The monitoring team needs the frontend to reliably correlate crashes with backend errors, but the current instrumentation has conflicts, runtime bugs, and blind spots.

## Verified Current State

- **Next.js config**: `next.config.ts` wraps the build with `withSentryConfig` from `@sentry/nextjs`. Disables webpack plugins in dev/preview, uploads sourcemaps in production.
- **Client-side error handling**: `src/lib/globalErrorHandler.ts` (Singleton) initializes Sentry manually, listens to `unhandledrejection` and `window.onerror`. `ErrorBoundary.tsx` (from `@shared`) wraps components in a class-based boundary.
- **Logging**: `src/lib/logger.ts` provides leveled logging with optional remote forwarding. `src/lib/errorLogging.ts` provides an in-memory ring buffer.
- **Error shipping**: `src/lib/errorReporter.ts` queues to `localStorage` and flushes `/api/frontend-errors` → Next.js API route → backend.
- **API client**: `src/lib/api.ts` handles auth, CSRF, trace propagation, retries, and auto-refresh.
- **Observability files**: `next.config.ts`, `src/components/ErrorHandlerInit.tsx`, `src/app/api/frontend-errors/route.ts`.

## Issues Identified

### Critical (Broken)

1. **Double Sentry Initialization** (`src/lib/globalErrorHandler.ts`, `src/components/ui/ErrorBoundary.tsx`, `next.config.ts`)
   - In `globalErrorHandler.ts`, `_initSentry()` calls `Sentry.init()` with different options (`tracesSampleRate: 0.2`, custom `beforeSend`, `replayIntegration()`). In `next.config.ts`, `withSentryConfig` has `disableClientWebpackPlugin: process.env.NODE_ENV !== "production"`.
   - **Dev**: client webpack plugin is disabled → only `globalErrorHandler` init runs. No collision in dev.
   - **Production**: client webpack plugin enabled → `@sentry/nextjs` injects `sentry.client.config.ts` which calls `Sentry.init({ dsn, tracesSampleRate: 1.0, replaysSessionSampleRate: 0.1, ... })` at bundle load time. Then `globalErrorHandler._initSentry()` runs later and overwrites the config with its own `tracesSampleRate: 0.2`, custom `beforeSend`, and `replayIntegration()`.
   - **Effect in production**: second `init()` overwrites `beforeSend`, drops/re-adds integrations, changes sampling. This is not a visible crash but silently breaks the build-time source map correlation and can cause duplicate sessions/replays. The bundle also carries the Next.js server SDK code even on the client because `require("@sentry/nextjs")` resolves the full package.

2. **Logger args mutation bug** (`src/lib/logger.ts`)
   - Each log method (`debug/info/warn/error`) calls `args.shift()` inside `formatLogEntry` (the result is unused) and then calls `args.shift()` **again** when building the remote queue payload.
   - **Effect**: message becomes an object (the second arg) instead of the message string. Once an arguments array reference is reused, subsequent logs in the same call site produce garbage.

### High (Broken / Unreliable)

3. **Collision-prone error IDs** (`src/lib/errorLogging.ts`)
   - IDs are generated as `${Date.now()}-${entries.length + 1}`. If `entries` is cleared and re-populated rapidly, IDs repeat. Date.now() granularity in timers can also collide.
   - **Effect**: deduplication, correlation, and Loki aggregation break.

4. **Off-by-one in queue overflow** (`src/lib/errorReporter.ts`)
   - `if (queue.length > MAX_QUEUE_SIZE)` allows `MAX_QUEUE_SIZE + 1` items before capping. The `shift()` only happens after the `>` check, so the cap is effectively `MAX_QUEUE_SIZE + 1`.
   - **Effect**: localStorage overflow protection is weaker than intended.

5. **Case-sensitive error matching** (`src/lib/api.ts::categorizeError`)
   - `error.message.includes("timeout")` misses `"Timeout"`, `"The operation was aborted"`, and other abort/timeout variants.
   - **Effect**: AbortController timeouts are mis-routed to `unknown_error` instead of `timeout_error`, suppressing retry logic.

6. **Module-level mutable state in `api.ts`** (`_accessToken`, `_refreshPromise`, `_traceId`)
   - These are plain module-scoped variables. In React 19 / Next.js strict mode, HMR can re-evaluate modules while preserving React component state, leaving stale or missing access tokens.
   - **Effect**: auth state becomes inconsistent during development; in production, long-lived tabs / service workers do not see HMR, but the pattern is still fragile.

### Medium (Improvable)

7. **No Sentry / logger integration in Next.js error boundaries**
   - `src/app/global-error.tsx` and `src/app/error.tsx` only `console.error` in dev. Production users see a retry UI with zero telemetry.
   - `ErrorBoundary.tsx` tries to `require("@sentry/nextjs")`, which only works because the bundle already loaded Sentry. If DSN is unset, the boundary falls back to clipboard copy with **no logger call**.

8. **Inconsistent instrumentation path**
   - Browser errors can travel: `globalErrorHandler` → `logFrontendError` → `errorReporter` → Next.js API route → backend.
   - Sentry errors travel: build-time config → Sentry cloud (if DSN is set).
   - Loki never receives frontend error logs directly; they pass through the backend `/api/frontend-errors` endpoint.

9. **`ErrorBoundary.tsx` reports to backend with raw `fetch`** inside a class component lifecycle. This call is not gated by `use client` and runs in any renderer context. It also does not apply the `resolveRequestUrl` / proxy logic from `api.ts`.

10. **Missing root `loading.tsx`** — root layout has no skeleton, causing layout shift on first load.

 11. **`categorizeError` missing abort/timeout signals** — `error.message.includes("timeout")` only matches lowercase `TypeError` with "timeout". AbortController aborts surface as `DOMException` with `name === "AbortError"`, message `"The operation was aborted."`, which falls through to `unknown_error` with `retryable: false`. Browser autoplay blocks or `"Network request failed"` also slip through.

12. **Remote logger messages are untyped objects** — When the logger `args.shift()` is called, the remaining `args` map in `formatLogEntry` serializes `undefined` values poorly, and the remote queue stores the **second** `args.shift()` result as the message. Remote log payloads are structurally malformed even when they don't crash.

### Watchlist (Low)

13. `next.config.ts` rewrites hardcode `/api`, `/auth`, `/admin`, `/hr`, `/__api`. Any new API route group needs a manual rewrite entry, otherwise Next.js returns 200 with an empty body (not a CORS error).
14. `resolveRequestUrl` in `api.ts` bypasses the proxy for `/api/*`, `/auth/*`, and `/admin/*` routes — correct today, but any new cross-origin route would need explicit listing.
15. `localStorage` error queue has no quota detection beyond the catch-and-clear block; `QuotaExceededError` is swallowed completely.
16. `globalErrorHandler.ts` stores breadcrumbs in memory. If the user navigates for hours, 50 breadcrumbs remain. No size-based eviction beyond the hard cap.
17. ` routes-manifest.json` error from stale `.next` cache — not a code bug, but indicates hot reload / disk-watch fragility.

## Execution Plan

### Phase 1: Stabilize Observability (Critical)

**1.1 Remove double Sentry init**
- Delete the entire `_initSentry` method and the `sentryInitialized` flag from `globalErrorHandler.ts`.
- Remove all `_reportToSentry` calls. `withSentryConfig` already instruments `unhandledrejection`, `window.onerror`, and React error boundaries at build time.
- Update `globalErrorHandler.ts` to only manage breadcrumbs and call `logFrontendError()` + `handleApiError()`.

**1.2 Fix ErrorBoundary.tsx Sentry fallback**
- Remove the `require("@sentry/nextjs")` from `tryReportToSentry` and `tryReportToBackend`.
- For Sentry presence, rely on the build-time initialized client. For absent DSN, fall back to `logFrontendError()` + `navigator.sendBeacon` to `/api/frontend-errors`.
- Add an `errorId` param to `tryReportToBackend` (already partially there) so backend can correlate.

**1.3 Fix logger mutation bug**
- Replace `args.shift()` with `const message = args[0] ?? ""; console.debug(...)` style logging.
- Build the remote queue entry from the **full** args array without mutation.

### Phase 2: Harden Error Data Paths (High)

**2.1 Upgrade errorLogging.ts IDs**
- Replace `Date.now() - entries.length + 1` with `crypto.randomUUID()` (browser-native) or `nanoid` (if shared lib has it). Export the ID generation so `errorReporter` and `ErrorBoundary` can use the same scheme.

**2.2 Fix errorReporter.ts overflow and identity**
- Change `if (queue.length > MAX_QUEUE_SIZE)` → `if (queue.length >= MAX_QUEUE_SIZE)`.
- Generate `id` per queued error using the same ID generator as `errorLogging.ts`.
- Add a `fingerprint` field (already computed) to each queued item so backend can dedup.

**2.3 Fix categorizeError matching**
- Normalize `error.message` to lowercase before matching.
- Add `error instanceof DOMException` / `error.name === "AbortError"` branch → `timeout_error` / `retryable: true`.
- Add `"networkrequestfailed"`, `"failed to fetch"` as case-insensitive timeout/network signals.
- Note: 503 already maps to `server_error` / `retryable: true` via `error.status >= 500`. Keep it but add explicit 503 branch for clarity in retry UI.
- In `handleApiError`, surface 503 as `warning` toast instead of generic `error` so it aligns with the retry-will-happen UX.

**2.4 Protect module-level state in api.ts**
- Replace plain module variables (`_accessToken`, `_refreshPromise`, `_traceId`) with a small runtime store object that survives HMR re-evaluation (e.g., `const _store = (() => { ... })()` with try/catch that only resets if truly absent).
- Alternatively, move access token to `sessionStorage` and read it lazily. This is slower but survives HMR and hard reloads. Given the security requirement (never write to localStorage), `sessionStorage` is acceptable since it doesn't persist across sessions and isn't accessible from cross-origin iframes in modern browsers.

### Phase 3: Close Observability Gaps (Medium)

**3.1 Report Next.js errors to centralized logger**
- Update `src/app/error.tsx` and `src/app/global-error.tsx` to call `logFrontendError(error, "nextjs-app-error", { digest })` and show a Retry button that still resets.
- In production, send a beacon to `/api/frontend-errors` so Loki receives the event even when Sentry DSN is unset.

**3.2 Instrument ErrorBoundary to use logger**
- In `componentDidCatch`, call `logFrontendError(error, "react-error-boundary", ...)` regardless of Sentry availability.
- Add `this.props.showReportButton` hook that copies the error to clipboard with the `errorId` and component stack, not just Sentry's dialog.

**3.3 Align logger API with structured output**
- Remove the unused `formatted` variable from log methods.
- Ensure `remoteQueue.push({ level, message, args: serializedArgs, timestamp })` uses the **original** message string, not a mutated second-shift value.
- Only serialize `args` once using the same logic as `formatLogEntry`, but do NOT mutate `args`.

### Phase 4: Structure & DX (Low / Optional)

**4.1 Add root loading.tsx**
- Minimal `loading.tsx` at `src/app/` with a brand-consistent skeleton.

**4.2 Add `error_id` propagation**
- When `globalErrorHandler` or `ErrorBoundary` captures an error, generate an `error_id` with `crypto.randomUUID()` and store it in `logFrontendError` context.
- Pass `error_id` through `errorReporter` to backend so the backend `/api/frontend-errors` handler can tag it.

**4.3 Test coverage**
- Add unit tests for `logger.ts` (verify no mutation, verify remote queue shape).
- Add unit tests for `errorLogging.ts` (verify ID uniqueness under concurrency).
- Add unit tests for `errorReporter.ts` (verify overflow ===, verify dedup window).
- Add unit tests for `api.ts::categorizeError` (case-insensitive timeout, AbortError → retryable, 503 → server_error/retryable).

## Key Files to Touch

| File | Phase | What |
|------|-------|------|
| `frontend/web_app/src/lib/globalErrorHandler.ts` | 1.1 | Remove `_initSentry`, `_reportToSentry`, `sentryInitialized`. Keep breadcrumbs + local logging. |
| `frontend/web_app/src/components/ui/ErrorBoundary.tsx` | 1.2 / 3.2 | Replace `require("@sentry/nextjs")` with logger fallback; add error_id. |
| `frontend/web_app/src/lib/logger.ts` | 1.3 / 3.3 | Fix `args.shift()` mutation; align remote queue payload. |
| `frontend/web_app/src/lib/errorLogging.ts` | 2.1 | Replace ID generator with `crypto.randomUUID()`. |
| `frontend/web_app/src/lib/errorReporter.ts` | 2.2 | Fix overflow check (`>=`), add `id` field, dedup via `fingerprint`. |
| `frontend/web_app/src/lib/api.ts` | 2.3 / 2.4 | Lowercase error matching, protect module state. |
| `frontend/web_app/src/app/error.tsx` | 3.1 | Call `logFrontendError` + sendBeacon. |
| `frontend/web_app/src/app/global-error.tsx` | 3.1 | Call `logFrontendError` + sendBeacon. |
| `frontend/web_app/next.config.ts` | 1.1 / 1.2 | Keep `withSentryConfig`; document that runtime Sentry init is forbidden. |
| `frontend/web_app/src/app/loading.tsx` | 4.1 | Create root loading skeleton. |

## Validation

1. **Smoke test**: Run `npm run build` and `npm run start`. Verify zero `[@sentry/nextjs] re-initialized` warnings.
2. **Error path test**: Throw inside a client component wrapped in `<ErrorBoundary>`. Verify Loki receives the event via `/api/frontend-errors` and `logFrontendError` captures the breadcrumbs.
3. **Logger smoke test**: Call `logger.debug("msg", {a:1}, {b:2})` and inspect the remote queue payload. The `message` field must be `"msg"`.
4. **ID uniqueness test**: Fire 1000 `logFrontendError` calls in a tight loop. Assert no duplicate IDs.
5. **Overflow test**: Fill `errorReporter` queue to `MAX_QUEUE_SIZE + 5` and assert length == `MAX_QUEUE_SIZE`.
6. **Case-insensitive categorize test**: Pass `new Error("Connection Timeout")` and assert `{ category: "timeout_error", retryable: true }`.
7. **Next.js error boundary test**: Throw inside a page component. Verify `global-error.tsx` renders and a `sendBeacon` call is made.
8. **HMR resilience test**: In dev mode, edit `api.ts` and trigger HMR. Verify `_accessToken` and `_refreshPromise` are preserved (or gracefully re-initialized) without orphaned promises.

## Open Questions

1. **Sentry DSN policy**: Should `NEXT_PUBLIC_SENTRY_DSN` be mandatory in production, or should the fallback Loki+direct-shipping path be the primary (Sentry as optional enrichment)? Recommendation: Loki direct-shipping is primary; Sentry is optional.
2. **Remote logger endpoint**: Where should `logger.ts` ship to? Options: backend `/api/logs`, Loki push API (`/loki/api/v1/push`), or Grafana Agent. Recommendation: Loki push API directly to cut latency.
3. **`_refreshPromise` state persistence**: Should silent refresh state survive HMR and hard reloads? Recommendation: persist session flag in `sessionStorage` (already done via `zozi_has_session`), but keep the in-memory promise guard only for the current page lifecycle.
4. **Browser `crypto.randomUUID()` support**: All target browsers support it. If legacy support is needed, add `nanoid` to shared package. Recommendation: use native API and add `nanoid` to shared only as a polyfill fallback.
5. **`/api/frontend-errors` input size**: Should there be a max payload size (e.g., 64KB)? Untrusted user-agent strings and deeply nested context could bloat localStorage and Loki ingestion. Recommendation: cap at 32KB per entry, truncate stack traces >1KB.
