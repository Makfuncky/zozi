# ZOZI Frontend — Build Problem & Solution

> Status: **RESOLVED** · Date: 2026-08-27
> Scope: `frontend/web_app` (Next.js 16.3.1, App Router)
> This document explains why the frontend would not build, the root cause, the
> fix that was applied, and why your CSS work is safe (nothing was rewritten).

---

## 1 · The symptom

Running the production build from `frontend/web_app`:

```bash
npm run build
```

failed with:

```
Error occurred prerendering page "/admin/communication". Read more: https://nextjs.org/docs/messages/prerender-error
ReferenceError: window is not defined
    at 2992 (...\.next\server\app\admin\communication\page.js)
```

`next build` first **compiled and type-checked fine** — it only failed at the
**"Generating static pages"** step. This is the important clue: the error was
not a syntax error or a missing file. It was a **runtime error thrown while the
server tried to render static HTML for the `/admin/communication` page**.

---

## 2 · Why this is confusing

1. **The page itself looked fine.** `src/app/admin/communication/page.tsx` is a
   normal `"use client"` component. Nothing obviously wrong.
2. **TypeScript passes.** `npx tsc --noEmit` reported no errors.
3. **`npm run dev` also masked it.** The dev server compiles lazily per page and
   often swallows or delays prerender-time errors, so the app *appeared* to run
   while `next build` (which prerenders all static pages) did not.

The failure lived **deep in the import tree** of that page — not in the page
itself. `./admin/communication/page.tsx` imports a large chain of admin-Comms
components, which pull in several WebSocket hooks. One of those hooks broke
**module-scope evaluation** during server-side prerendering.

---

## 3 · Root cause

### The file

`frontend/web_app/src/hooks/useWebSocket.ts` (imported by the Comm Stage via
`src/components/comms/Stage/Stage.tsx`, which `/admin/communication` uses).

### The buggy code (before the fix)

```ts
// src/hooks/useWebSocket.ts  (top-level / module scope)
const WS_BASE =
  typeof window !== "undefined" &&
  (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
    ? "ws://127.0.0.1:8000"
    : `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.hostname}:8000`;
```

### Why it breaks on the server

`WS_BASE` is a **module-scope constant**. It runs the moment the file is
imported. Next.js prerenders `"use client"` components **on the server** to emit
static HTML, so this module *is* imported server-side… where `window` does not exist.

Trace the ternary:

1. Server: `typeof window` → `"undefined"` → `typeof window !== "undefined"` → `false`
2. `false && (anything)` → `false`
3. Ternary picks the **false branch**:
   ```ts
   `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.hostname}:8000`
   ```
4. That branch **unconditionally reads `window.location`** → `ReferenceError: window is not defined`.

The `typeof window !== "undefined"` guard was placed **inside the ternary
condition**, not on the ternary itself, so the guard protected the *condition*
but not the *false branch* that still references `window`.

> For comparison, `src/lib/api/client.ts:29` does it correctly:
> ```ts
> export const API_URL =
>   typeof window !== "undefined"
>     ? (/* safe branch using window only */)
>     : _API_URL;   // ← server branch never touches window → safe
> ```

The same faulty pattern existed in a **second** file,
`src/hooks/useUnifiedInbox.ts`, but there the `window.location` read was inside
a `useEffect` (client-only), so it did not throw at module scope.

---

## 4 · The fix

`frontend/web_app/src/hooks/useWebSocket.ts` — rewrote the top-level constant so
it returns a safe string when running on the server and never touches `window`
in the server path:

```ts
const WS_BASE = (() => {
  if (typeof window === "undefined") return "";
  const isLocal =
    window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
  if (isLocal) return "ws://127.0.0.1:8000";
  return `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.hostname}:8000`;
})();
```

Behavior is **identical in the browser** (local → `ws://127.0.0.1:8000`,
otherwise wss/ws to the current host). On the server it is an empty string,
which is never used because the hook only opens sockets inside `useEffect`
(which never runs server-side).

After the fix, `npm run build` completed: compiled + type-checked + generated
**all 128 static pages** with zero errors.

---

## 5 · Why your CSS is safe (months of work preserved)

No CSS was touched, deleted, or rewritten. The styling layer is fully intact:

| File | Size | Wired in via |
|---|---|---|
| `src/styles/globals.css` | ~207 KB (themed design system, tokens, components) | `GlobalStyles.tsx` (`@/styles/globals.css`) |
| `src/styles/glow.css` | 1.4 KB | `GlobalStyles.tsx` (`@/styles/glow.css`) |
| `src/styles/comm.css` | 10 KB (Comms workspace) | `Components/comms/CommShell.tsx` |
| `src/styles/panel-modern.css` | 1.4 KB | `Components/PanelPage.tsx` |
| `src/styles/tokens.css` | 5.8 KB (orphaned token system, guarded by `__tests__/designSystemTokens.test.ts`) | kept for reference |

- The build failure was **purely a JavaScript runtime error in one hook** — it
  never reached the CSS pipeline.
- Tailwind 3.4 + PostCSS + `tailwind.config.js` (theme tokens, safelist) are
  unchanged and processed normally — the generated pages render with the full
  themed styles (`theme-btn-*`, `--color-brand`, surfaces, etc.) as before.

---

## 6 · How to reproduce / verify

```bash
# 1) Clean and build (fastest proof the project runs)
cd frontend/web_app
rm -rf .next
npm run build        # → completes, 128/128 pages, no "window is not defined"

# 2) Dev server
npm run dev          # → http://localhost:3000
# open http://localhost:3000/admin/communication
```

If you ever see `ReferenceError: window is not defined` during `next build`
prerendering again, search for module-scope browser globals:

```bash
rg -n "\b(window|document|localStorage|navigator)\." src --type ts --type tsx
```

and verify each match is **inside a function/useEffect/event handler** — never a
bare top-level `const … = window…` whose alternate ternary branch is unguarded.
The safe pattern is:

```ts
const value = typeof window !== "undefined" ? window.something : SAFE_FALLBACK;
```

---

## 7 · Key takeaways

1. **Root cause:** module-scope `const WS_BASE` in `useWebSocket.ts` read
   `window.location` in an unguarded ternary branch during server-side
   prerender of `/admin/communication`.
2. **One-line-area fix**, no architecture change, no CSS change.
3. **CSS (months of work) is intact** — verified file sizes, wiring, and a fully
   successful production build.
