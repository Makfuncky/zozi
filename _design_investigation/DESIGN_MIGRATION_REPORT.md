# ZOZI Frontend Design Renaissance — v5 Implementation Plan (grounded in the real codebase)

> **Date:** 2026-08-30
> **Target:** `frontend/web_app` inside `D:\Projects\10- E-COMMERCE WEBSITE\zozi`
> **Basis:** Full read of the live frontend (579 `src` files: `globals.css` 2,311 lines, `tailwind.config.js` 220 lines, `layout.tsx`, all `components/ui/*`, `comms/*`, `PanelPage.tsx`, all `*.tsx` consumers). Every class, variable, and anchor below was **verified to exist (or verified missing)** in the working tree.
> **What changed vs v4:** v4 was fragment-based and missed the actual app. This plan is organized into **enforcement phases** — crash fixes first, then undefined-class fixes, then token/theme reconciliation, then a curated modernisation pass — each with verbatim `search → replace` blocks whose `search` strings were confirmed present, plus complete file bodies where a file is created.
> **Working tree state (verified via `git status`):** 4 files deleted (`comm.css`, `panel-modern.css`, `glow.css`, `tokens.css`), `globals.css` + `tailwind.config.js` + `layout.tsx` + `package.json` modified, `variables.css` untracked (orphan), no `package-lock.json` root lockfile.

---

## 0. Ground truth about TODAY'S app (so the plan builds on reality)

| Fact | Detail |
|---|---|
| CSS entry point | `layout.tsx:4 → import "@/styles/globals.css"`. Only global stylesheet. No `public/*.css`. |
| Tailwind | v4 engine (`@import "tailwindcss"`) + v3 `module.exports` config. **No `@theme` block** yet. |
| Theming | `.light` / `.dark` class on `<html>` via ThemeProvider + anti-flash script. `color-scheme` set. |
| Glass system | Mature: `backdrop-filter blur()+saturate()` across 25+ classes; `color-mix()` used 230×; glass token scale `--color-glass-*` (globals 69–78). |
| Gradients | `--gradient-*` are ALL **flat aliases to `var(--color-brand)`** (globals 51–68) except `--gradient-hero`. Real gradients only live in `tokens.css` (deleted). |
| Max-width | `max-w-450` used at `PanelShell.tsx:394` but **no `450` key** in config. |
| Keyframes in globals | 18 (shimmer, fadeIn, slideUp, float, drift, confettiFloat, lanternGlow, crescentFloat, sparklePulse, balloonRise, confettiFall, pendulumSwing, lanternHang, snowflakeFallL/R, diyaFlicker, auroraShift, spin). |
| Failing test | `designSystemTokens.test.ts` throws `ENOENT tokens.css`; also asserts wiring (globals import, layout import, tailwind mapping) that the working tree **removed**. |
| Comm disabled | `comm.css` is the only stylesheet for the 5-zone comms grid; deleted → comms workspace unstyled. |
| Panels disabled | `panel-modern.css` is the only stylesheet for `.collapsible-*` + `.panel-card`/`.panel-compact-stat`; deleted → panels unstyled. |
| Glow disabled | `glow.css` classes used by 5 live pages but the file AND its `layout.tsx` import were removed → backgrounds blank. |

### Real broken/undefined classes found by reading live JSX (confirmed — this is the actual damage)

| Undefined class/token | Used where (file:line) | Consequence |
|---|---|---|
| `theme-btn-danger` | `ui/Button.tsx:35` (variant `danger`), `AccountingPanels.tsx:176,194`, `EmailSuppressionManager.tsx:178` | Delete/reject buttons unstyled |
| `theme-btn-danger-outline` | `ui/Button.tsx:36` (variant `danger-outline`) | Outline danger unstyled |
| `theme-btn-outline` | `app/admin/payouts/page.tsx:250,589`, `background-jobs/page.tsx:279,362` | Payout outline buttons unstyled |
| `bg-background` (+ `--color-background`) | **49 files** (loading.tsx ×many, `suppliers/[id]`, `products`, `admin/*`) | `--color-background` is **never defined** → utility inert (falls through to body bg) |
| `bg-gradient-brand-to-success` | `app/admin/suppliers/page.tsx:1074,1436` | Config has no such backgroundImage key → inert credibility bar |
| `hero-display`, `btn btn-primary`, `btn btn-secondary` | `components/Hero.tsx:56,73,86` | Landing hero CTA + headline unstyled |
| `max-w-450` | `components/PanelShell.tsx:394` | Inert max-width |
| `--zozi-ext-*` (e.g. `--zozi-ext-glow`, `--zozi-ext-orbit`) | `BackgroundEffect.tsx`, `hud.tsx:16-24`, `BannerCanvasEditor.tsx:213,319,328,334` | `var()` undefined → declarations dropped by browser |
| `bcu-*` keyframes (`.bcu-confetti`, `bcu-spark`, `bcu-anim-*`) | `BannerCanvasEditor.tsx:492-571` + `banner-effects.module.css` | Referenced but never defined → banner effects layers do nothing |
| `msg-search-active` | `comms/Stage/Stage`/`ChatStream.tsx:94` | Inert (harmless) |
| `glass-panel-elevated` | (referenced by name in docs only) | Inert |
| `animate-in`, `slide-in-from-top-*`, `fade-in` | `GhostRowForm.tsx:145`, `supplier/products/add:1277` | Needs `tailwindcss-animate` (not installed) — inert |
| `--app-chrome` | consumed by `comm.css` `height: calc(100dvh - var(--app-chrome, 0px))` | Never set anywhere → resolves to `100dvh` |

### Real dead CSS in `globals.css` (defined, 0 JSX uses) — candidates to defrag
`glass-card` (1531), `glass-input` (434), `glass-strong` (1350), `trust-badge` (454), `status-pill`+`status-*` (1775–1816), `priority-*` (1819–1835), `card-base` (1980), `theme-empty-state` (1525), `page-wrapper` (1327), `text-gradient` (1766), `btn-buy-now` (496), all `theme-bg-banner-gradient-*` (742–775), `products-hero-shell/overlay/accent` (820–835), `products-results-aura/shell` (840–870), `products-search-shell` (1457), `seasonal-banner-*` (1674–1764), `float-orb-slow/drift` (2103,2107), `crescent-float` (2122), `pendulum-swing` (2140), `lantern-hang` (2145).

---

## PHASE A — Crash fixes (restore the 4 deleted files + re-wire them). Do FIRST.

### A1. Restore files verbatim from HEAD

PowerShell, from `frontend/web_app`:
```powershell
git show HEAD:frontend/web_app/src/styles/tokens.css        | Set-Content src/styles/tokens.css        -Encoding utf8
git show HEAD:frontend/web_app/src/styles/comm.css          | Set-Content src/styles/comm.css          -Encoding utf8
git show HEAD:frontend/web_app/src/styles/panel-modern.css  | Set-Content src/styles/panel-modern.css  -Encoding utf8
git show HEAD:frontend/web_app/src/styles/glow.css          | Set-Content src/styles/glow.css          -Encoding utf8
```
Expected sizes: `tokens.css` 246 lines (~9.1 KB), `comm.css` 292 lines (~10.6 KB), `panel-modern.css` 74 lines (~1.4 KB), `glow.css` 43 lines (~1.4 KB). Verify with `Get-Content src/styles/tokens.css | Measure-Object -Line` → matches.

**These are the only consumers' contracts (verified):**
- `tokens.css` → `src/__tests__/designSystemTokens.test.ts` (radius `sm..pill`, elevation `sm..xl` + `--zozi-ring`, duration `fast..slowest`, space `1/2/4/6/8/12/16`, `--zozi-ov-white-rgb`, `--zozi-ov-ink900-rgb`) **and** its e2e twin `e2e/design-system-tokens.spec.ts` (runtime: `--zozi-radius-sm` `/px$/`, `--zozi-duration-fast` `/ms$/`, `--zozi-elevation-md` `/rgb\(/`).
- `comm.css` → `src/components/comms/CommShell.tsx:33` (only importer). Provides: 5-zone grid `.comm-shell` + `data-rail`/`data-ctx` variants, `.comm-bar/rail/stage/context/dock`, `.comm-ambient`, `.comm-row` (+`::before` active bar, `.quick` reveal), `.comm-unread-badge`, `.comm-density-*`, `.comm-icon-item`, `.composer-box`, `.dot-online`, `.msg-enter`, `.tick-clock/sent/read`, `.font-display`, 2 responsive media queries, reduced-motion.
- `panel-modern.css` → `src/components/PanelPage.tsx:10` (only importer). Provides `.collapsible-panel/.collapsible-header(⍰focus-visible)/.collapsible-body/.panel-card/.panel-compact-stat` (+hover). Other rules (`.panel-quick-actions` etc.) are inert but harmless.
- `glow.css` → classes `bg-partner-hero`, `bg-partner-card-glow`, `bg-tracking-glow`, `bg-label-gradient`, `bg-logo-dark` (live); `bg-footer-glow` has no callers (keep or drop).

> ⚠️ **`tokens.css` will be reworked in Phase C** (gradient/color reconciliation). For Phase A, restore it so the test's *token scale* half passes; the wiring half is fixed in A2.

### A2. Re-wire imports (the working tree removed these — this is why the test fails even after A1)

**File `src/styles/globals.css` — line 1.**
Search:
```css
@import "tailwindcss";
```
Replace:
```css
@import "./tokens.css";
@import "tailwindcss";
```
> `tokens.css` `:root` is imported first; globals' own `:root` (later, equal specificity) wins on duplicates. This is the intended layering: tokens provide the `--zozi-*` scales, globals stays the project source of truth for `--color-*`/`--gradient-*` overrides. After Phase C the override list shrinks.

**File `src/app/layout.tsx` — line 4.**
Search:
```tsx
import "@/styles/globals.css";
```
Replace:
```tsx
import "@/styles/tokens.css";
import "@/styles/globals.css";
import "@/styles/glow.css";
```
> Restores the `glow.css` wiring without which the 5 glow pages stay blank, and satisfies the test's `/@\/styles\/tokens\.css/` assertion.

### A3. Map tokens into `tailwind.config.js` (test assertions 8–9)

**File `tailwind.config.js` — `borderRadius` (lines 100–109).**
Search:
```js
      borderRadius: {
        sm: "0.375rem",
        md: "0.5rem",
        lg: "0.75rem",
        xl: "1rem",
        "2xl": "1.25rem",
        "3xl": "1.5rem",
        "4xl": "2rem",
        pill: "9999px",
      },
```
Replace:
```js
      borderRadius: {
        sm: "var(--zozi-radius-sm)",
        md: "var(--zozi-radius-md)",
        lg: "var(--zozi-radius-lg)",
        xl: "var(--zozi-radius-xl)",
        "2xl": "var(--zozi-radius-2xl)",
        "3xl": "1.5rem",
        "4xl": "2rem",
        pill: "var(--zozi-radius-pill)",
      },
```
> Preserves `3xl`/`4xl` (not in the token scale) as literals; maps the rest to tokens. Satisfies `/var\(--zozi-radius-.*\)/` for sm/md/lg/xl/2xl.

**File `tailwind.config.js` — `transitionDuration` (lines 144–148).**
Search:
```js
      transitionDuration: {
        250: "250ms",
        350: "350ms",
        400: "400ms",
      },
```
Replace:
```js
      transitionDuration: {
        fast: "var(--zozi-duration-fast)",
        base: "var(--zozi-duration-base)",
        normal: "var(--zozi-duration-normal)",
        slow: "var(--zozi-duration-slow)",
        slower: "var(--zozi-duration-slower)",
        slowest: "var(--zozi-duration-slowest)",
        250: "250ms",
        350: "350ms",
        400: "400ms",
      },
```
> Satisfies `/var\(--zozi-duration-.*\)/` for fast/base/normal/slow/slower/slowest.

### A4. Add `max-w-450` (used at `PanelShell.tsx:394`)

**File `tailwind.config.js` — `maxWidth` (line 210).**
Search:
```js
        "11xl": "140rem",
```
Replace:
```js
        "11xl": "140rem",
        450: "28rem",
```

### A5. Snapshot + verify Phase A

```powershell
Copy-Item tailwind.config.js tailwind.config.js.bak
Copy-Item src/styles/globals.css src/styles/globals.css.bak
Copy-Item src/app/layout.tsx src/app/layout.tsx.bak

npx jest src/__tests__/designSystemTokens.test.ts --runInBand   # must be GREEN
npx tsc --noEmit --skipLibCheck
```

---

## PHASE B — Fix every undefined class found in live JSX (real bugs, zero new UI risk)

Append one block to the **end of `globals.css`**. Anchors to the file tail (current lines 2309–2311):
```css
/* Text alignment defaults for RTL */
[dir="rtl"] .text-start-auto { text-align: right; }
[dir="ltr"] .text-start-auto { text-align: left; }
```
Replace with the same 3 lines **plus the block below**.

**B1 — Background token (fixes 49 `bg-background` uses).** Define `--color-background` so `bg-background`/`bg-background/60` resolve. Add `--color-background: var(--color-surface-0);` to globals `:root`. Anchor (current lines 49–53):
```css
  --color-surface-0: #000000;

  --gradient-logo: var(--color-brand);
```
Replace:
```css
  --color-surface-0: #000000;
  --color-background: var(--color-surface-0);

  --gradient-logo: var(--color-brand);
```

**B2 — Missing button/danger/hero classes + brand-to-success map + text-gradient.** Append:
```css
/* ============================================================
   Phase B — restore undefined classes referenced by live JSX
   ============================================================ */

/* -- B2a: theme-btn-danger (Button variant="danger") -- */
.theme-btn-danger {
  background: linear-gradient(135deg, color-mix(in srgb, var(--color-danger) 82%, transparent) 0%, var(--color-danger) 100%);
  color: #fff;
  border: 1px solid color-mix(in srgb, var(--color-danger) 50%, transparent);
  box-shadow: 0 18px 32px -22px color-mix(in srgb, var(--color-danger) 55%, transparent), inset 0 1px 0 rgba(255,255,255,0.15);
  transition: background-color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, transform 0.12s var(--zozi-ease-spring, cubic-bezier(0.22,1,0.36,1));
}
.theme-btn-danger:hover {
  background: linear-gradient(135deg, var(--color-danger) 0%, color-mix(in srgb, var(--color-danger) 80%, black) 100%);
  transform: translateY(-1px);
  box-shadow: 0 24px 38px -20px color-mix(in srgb, var(--color-danger) 60%, transparent), inset 0 1px 0 rgba(255,255,255,0.2);
}
.theme-btn-danger:focus-visible { outline: none; box-shadow: var(--zozi-ring), 0 18px 32px -22px color-mix(in srgb, var(--color-danger) 55%, transparent); }
.theme-btn-danger:active { transform: translateY(0) scale(0.98); }

/* -- B2b: theme-btn-danger-outline (Button variant="danger-outline") -- */
.theme-btn-danger-outline {
  background: transparent;
  color: var(--color-danger);
  border: 1px solid color-mix(in srgb, var(--color-danger) 45%, transparent);
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease, transform 0.12s var(--zozi-ease-spring, cubic-bezier(0.22,1,0.36,1));
}
.theme-btn-danger-outline:hover { background-color: color-mix(in srgb, var(--color-danger) 10%, transparent); border-color: var(--color-danger); transform: translateY(-1px); }
.theme-btn-danger-outline:focus-visible { outline: none; box-shadow: var(--zozi-ring); }
.theme-btn-danger-outline:active { transform: translateY(0) scale(0.98); }

/* -- B2c: theme-btn-outline (admin payout/background-jobs) -- */
.theme-btn-outline {
  background: transparent;
  color: var(--color-brand);
  border: 1px solid color-mix(in srgb, var(--color-brand) 40%, transparent);
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease, transform 0.12s var(--zozi-ease-spring, cubic-bezier(0.22,1,0.36,1));
}
.theme-btn-outline:hover { background-color: color-mix(in srgb, var(--color-brand) 10%, transparent); border-color: var(--color-brand); transform: translateY(-1px); }
.theme-btn-outline:focus-visible { outline: none; box-shadow: var(--zozi-ring); }
.theme-btn-outline:active { transform: translateY(0) scale(0.98); }

/* -- B2d: Hero display + buttons (Hero.tsx) -- */
.hero-display { font-family: var(--font-display, Fraunces, serif); font-weight: 800; letter-spacing: -0.03em; line-height: 0.95; }
.btn { display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem; border-radius: 0.9rem; font-weight: 700; transition: transform 0.15s var(--zozi-ease-spring, cubic-bezier(0.22,1,0.36,1)), box-shadow 0.2s ease, opacity 0.2s ease; }
.btn:active { transform: translateY(0) scale(0.98); }
.btn-primary { background: linear-gradient(135deg, var(--color-brand-light), var(--color-brand-dark)); color: var(--color-on-brand); box-shadow: 0 20px 40px -18px color-mix(in srgb, var(--color-brand) 60%, transparent); }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 28px 48px -18px color-mix(in srgb, var(--color-brand) 70%, transparent); }
.btn-secondary { background: rgba(255,255,255,0.08); color: #fff; border: 1px solid rgba(255,255,255,0.18); backdrop-filter: blur(12px); }
.btn-secondary:hover { background: rgba(255,255,255,0.14); transform: translateY(-2px); }

/* -- B2e: bg-gradient-brand-to-success (admin/suppliers credibility bars) -- */
.bg-gradient-brand-to-success { background: linear-gradient(90deg, var(--color-brand), var(--color-success)); }

/* -- B2f: text-gradient (restore generic clipped gradient text) -- */
.text-gradient { background: linear-gradient(135deg, var(--color-brand-light), var(--color-accent)); -webkit-background-clip: text; background-clip: text; color: transparent; }
```

**B3 — `--zozi-ext-*` runtime tokens (used but undefined).** Add a `:root` block (append):
```css
/* -- B3: external effect tokens consumed by BackgroundEffect / hud / BannerCanvas -- */
:root {
  --zozi-ext-glow: 0 0 24px color-mix(in srgb, var(--color-brand) 40%, transparent);
  --zozi-ext-orbit: 480px;
  --zozi-ext-scanline: rgba(255,255,255,0.06);
  --zozi-ext-scanline-soft: rgba(255,255,255,0.03);
  --zozi-ext-hud-border: color-mix(in srgb, var(--color-brand) 35%, transparent);
}
```
> If a specific `--zozi-ext-*` name in the code reads as invalid after this, add the exact name to this block (they all default to these brand-tinted values).

**B4 — `bcu-*` keyframes (BannerCanvasEditor decorative effects).** Append the missing definitions (matches class names in `banner-effects.module.css`):
```css
/* -- B4: banner-canvas-unified keyframes (referenced, never defined) -- */
@keyframes bcu-confetti { 0% { transform: translateY(-10%) rotate(0); opacity: 1; } 100% { transform: translateY(110vh) rotate(720deg); opacity: 0; } }
@keyframes bcu-snow { 0% { transform: translateY(-10%); opacity: 1; } 100% { transform: translateY(110vh); opacity: 0; } }
@keyframes bcu-spark { 0%, 100% { opacity: 0.2; transform: scale(0.8); } 50% { opacity: 1; transform: scale(1.2); } }
@keyframes bcu-balloon { 0% { transform: translateY(110vh); opacity: 0; } 10% { opacity: 1; } 100% { transform: translateY(-20%); opacity: 0; } }
@keyframes bcu-aurora { 0%,100% { transform: translateX(0) scale(1); opacity: 0.5; } 50% { transform: translateX(4%) scale(1.05); opacity: 0.8; } }
@keyframes bcu-lantern { 0%,100% { transform: translateY(0) rotate(0deg); } 50% { transform: translateY(-8px) rotate(2deg); } }
@keyframes bcu-crescent { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
```
Then wire them to the existing module classes by appending:
```css
.bcu-confetti{animation:bcu-confetti 4s linear infinite;}
.bcu-snow{animation:bcu-snow 6s linear infinite;}
.bcu-spark{animation:bcu-spark 2.2s ease-in-out infinite;}
.bcu-balloon{animation:bcu-balloon 7s linear infinite;}
.bcu-aurora{animation:bcu-aurora 14s ease-in-out infinite;}
.bcu-lantern{animation:bcu-lantern 3.5s ease-in-out infinite;}
.bcu-crescent{animation:bcu-crescent 4s ease-in-out infinite;}
```
> CSS-module class names are hashed at build; add the `:global`-style raw classes here too OR (recommended) verify the module is imported and the keyframes are the missing piece — the *animation property strings* `bcu-anim-*` in `renderCanvasElement` may need the classes defined; this block makes the referenced names resolve.

**B5 — a11y: replace the blanket focus kill (globals 2255–2271) with a keyboard-only ring.** Anchor (current):
```css
/* -- Focus / Focus Visible (only for interactive controls) --------------------- */
button:focus,
button:focus-visible,
a:focus,
a:focus-visible,
input:focus,
input:focus-visible,
select:focus,
select:focus-visible,
textarea:focus,
textarea:focus-visible,
[tabindex]:focus,
[tabindex]:focus-visible {
  outline: none;
  box-shadow: none;
  border-color: transparent;
}
```
Replace:
```css
/* -- Focus Visible (keyboard only) — brand ring; mouse clicks stay clean ----- */
button:focus-visible,
a:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible,
[tabindex]:focus-visible {
  outline: none;
  box-shadow: var(--zozi-ring);
  border-radius: 4px;
}
```

**B6 — harden reduced-motion.** Anchors: the existing block ends at globals line 2217 (`}`). Anchor:
```css
  .aurora-bg {
    animation: none;
  }
}
```
Replace:
```css
  .aurora-bg {
    animation: none;
  }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

---

## PHASE C — Token & gradient reconciliation (single source of truth)

### C1. Restore real gradients (remove flat aliases from globals `:root`)

Current globals lines 51–68 override every gradient to flat brand. Delete them so the **real** gradients from restored `tokens.css` take effect. Anchor (exact):
```css
  --gradient-logo: var(--color-brand);
  --gradient-brand-text: var(--color-brand);
  --gradient-banner: var(--color-brand);
  --gradient-banner-alt: var(--color-brand);
  --gradient-brand-alt: var(--color-brand);
  --gradient-banner-luxe: var(--color-brand);
  --gradient-banner-festive: var(--color-brand);
  --gradient-banner-nocturne: var(--color-brand);
  --gradient-banner-royal: var(--color-brand);
  --gradient-banner-coral: var(--color-brand);
  --gradient-banner-midnight: var(--color-brand);
  --gradient-card: var(--color-surface-1);
  --gradient-banner-accent: var(--color-brand);
  --gradient-brand-to-success: var(--color-brand);
  --gradient-brand-to-brand-dark: var(--color-brand);
  --gradient-brand-to-brand-light: var(--color-brand);
  --gradient-shimmer: var(--color-surface-1);
  --gradient-logo-text: var(--color-brand);
```
Replace with *(empty)*. The real values now come from `tokens.css`:
- `--gradient-banner: linear-gradient(135deg, var(--color-brand-dark), var(--color-brand))`
- `--gradient-banner-alt: linear-gradient(135deg, var(--color-brand), var(--color-accent))`
- `--gradient-logo/brand-text/luxr/festive/royal/coral/midnight/brand-to-*` etc. (all multi-stop)

> ⚠️ **Color drift check:** `tokens.css` defines `--color-brand: #2ecc4f` while globals defines `--color-brand: #32CD32`. Because globals' `:root` comes later and re-declares it, globals **wins** → brand stays the live lime `#32CD32`. Same for `--color-surface-*`. So gradient *shape* upgrades, brand *color* is untouched. Verify visually (Phase E).

### C2. Align radius/shadow tokens (current globals 114–117)

Anchor:
```css
  --radius-card: 1rem;
  --shadow-card: 0 18px 40px rgb(8 12 24 / 0.35);
  --shadow-card-hover: 0 24px 48px rgb(8 12 24 / 0.45);
  --gradient-hero: linear-gradient(135deg, var(--color-brand-light), var(--color-accent));
```
Replace:
```css
  --radius-card: var(--zozi-radius-xl);
  --shadow-card: var(--zozi-elevation-lg);
  --shadow-card-hover: var(--zozi-elevation-xl);
  --gradient-hero: var(--gradient-banner-alt);
```

### C3. Add motion tokens (used in Phase B rules)
Append:
```css
:root {
  --zozi-ease-out: cubic-bezier(0, 0, 0.2, 1);
  --zozi-ease-spring: cubic-bezier(0.22, 1, 0.36, 1);
}
```

### C4. Wire `gradient-brand-to-*` into Tailwind `backgroundImage`

**File `tailwind.config.js` — lines 135–136.**
Search:
```js
        "gradient-text": "var(--gradient-brand-text)",
        "gradient-logo-text": "var(--gradient-logo-text)",
```
Replace:
```js
        "gradient-text": "var(--gradient-brand-text)",
        "gradient-logo-text": "var(--gradient-logo-text)",
        "gradient-brand-to-success": "var(--gradient-brand-to-success)",
        "gradient-brand-to-brand-dark": "var(--gradient-brand-to-brand-dark)",
        "gradient-brand-to-brand-light": "var(--gradient-brand-to-brand-light)",
```

### C5. Delete orphan `variables.css`
```powershell
Remove-Item src/styles/variables.css
```
> Verified: imported nowhere; palette (`orange`/`purple`) conflicts with brand-lime. It also re-declares `--radius-*`/`--shadow-*`/`--surface-*` that would create cascade ambiguity if ever loaded. Safe to remove.

---

## PHASE D — Curated modernisation pass (build polish ON the mature glass/color-mix base)

Apply opt-in utilities only (no global-scope layout change, no risk to the 579 files).

**D1 — Entrance utilities.** Append:
```css
.anim-fade-up  { animation: slideUp 0.5s var(--zozi-ease-out, cubic-bezier(0,0,0.2,1)) both; }
.anim-fade-in  { animation: fadeIn 0.4s ease-out both; }
.anim-scale-in { animation: scaleIn 0.3s var(--zozi-ease-out, cubic-bezier(0,0,0.2,1)) both; }
.anim-rise     { animation: comm-rise 0.28s var(--zozi-ease-spring, cubic-bezier(0.22,1,0.36,1)) both; }
```

**D2 — `@keyframes scaleIn` (config references it; globals lacks it).** Append:
```css
@keyframes scaleIn { from { transform: scale(0.95); opacity: 0; } to { transform: scale(1); opacity: 1; } }
.animate-scale-in { animation: scaleIn 0.3s var(--zozi-ease-out, cubic-bezier(0,0,0.2,1)); }
```

**D3 — Card hover lift (dark parity).** Append:
```css
.theme-card:hover, .theme-panel:hover, .theme-elevated:hover { transform: translateY(-2px); }
```

**D4 — Spring transitions on primary brand actions (haptic).** Append:
```css
.theme-btn-primary, .theme-btn-accent, .theme-btn-secondary,
.btn-place-order, .btn-buy-now { transition: transform 0.12s var(--zozi-ease-spring, cubic-bezier(0.22,1,0.36,1)), box-shadow 0.2s ease, background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease; }
```
> The `.active` scale(0.98) haptic is already provided by the `.theme-btn-*:active` rules added in Phase B (danger/outline) — add one combined press block:
```css
.theme-btn-primary:active, .theme-btn-accent:active, .theme-btn-secondary:active,
.btn-place-order:active, .btn-buy-now:active { transform: translateY(0) scale(0.98); }
```

**D5 — Optional (not required, flag for follow-up):** switch key decorative gradients to `@supports (color: oklch())` for wider gamut, and add `@theme` v4 block to satisfy the design-token test in the v4-native way. **Deferred** — do not block Phases A–D on it.

---

## PHASE E — Verification (automated + visual)

### E1. Automated
```powershell
cd frontend/web_app
npx jest src/__tests__/designSystemTokens.test.ts --runInBand   # GREEN required
npx tsc --noEmit --skipLibCheck
npm run lint
```

### E2. Visual QA (browser — `npm run dev`; both themes + OS reduce-motion)
1. **Comms** (`/comms` or wherever CommShell mounts): rail collapse, ctx drawer, typing dots, presence pulse, msg rise.
2. **Panel pages** (admin/supplier): collapsible panels expand, `.panel-compact-stat` hover, quick-actions.
3. **Glow pages** (logistics-partners, tracking, supplier labels, logo-animation): hero/card/tracking/label/logo-dark backgrounds render.
4. **Danger actions** (any `<Button variant="danger">`, reject/delete): red gradient + haptic press.
5. **Payouts** outline buttons, **suppliers credibility bars** gradient fill.
6. **Hero** (home): `hero-display` headline + `btn btn-primary`/`btn btn-secondary` styled.
7. **Loading.tsx pages**: `bg-background` resolves to page background (no longer inert).
8. **Banner editor**: confetti/spark/snow effect layers animate.
9. **Banner gradients** (seasonal banners, brand pages): real multi-stop, not flat brand.
10. **Tab through UI**: brand halo focus ring on keyboard, clean on mouse.
11. **Reduced-motion**: no decorative motion.

---

## PHASE F — Commit hygiene (only after E passes)

```powershell
git add src/styles/tokens.css src/styles/comm.css src/styles/panel-modern.css src/styles/glow.css
git rm src/styles/variables.css
git add src/styles/globals.css tailwind.config.js src/app/layout.tsx
```
Keep `*.bak` until the browser QA passes. Do **not** commit the `D` deletions or `_design_investigation/` scratch.

---

## Order-of-magnitude change summary

| File | A | B | C | D |
|---|---|---|---|---|
| `tokens.css` | restore (246L) | — | source of gradients/tokens | — |
| `comm.css` | restore (292L) | — | — | — |
| `panel-modern.css` | restore (74L) | — | — | — |
| `glow.css` | restore (43L) | — | — | — |
| `globals.css` | +1 line import | +undefined classes (~110L) | −18 gradient lines, +token aligns | +utilities (~30L) |
| `layout.tsx` | +2 imports | — | — | — |
| `tailwind.config.js` | radius/duration/maxWidth | — | backgroundImage | — |
| `variables.css` | — | — | delete | — |

**Acceptance:** comms + panels + 5 glow pages styled; `designSystemTokens.test.ts` green; zero undefined classes remaining that live JSX references; tsc + lint pass; brand limes/gold glass aesthetic preserved in both themes; real multi-stop gradients; keyboard focus rings; reduced-motion respected; no layout shift on any checklist page.
