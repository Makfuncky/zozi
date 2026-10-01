# ZOZI Frontend Design — Comprehensive Implementation Plan

> **Document purpose:** The single authoritative, copy-paste-ready plan that merges the best of all three prior analyses (DESIGN_MIGRATION_REPORT.md, DESIGN_PLAN_FINAL.md, DESIGN_IMPLEMENTATION_PLAN.md). Every action states exact file path, exact line numbers, exact old text, exact new text, and exact validation command.
>
> **Scope:** 12,500+ lines across `frontend/web_app` and `frontend/shared`. Covers CSS restoration, undefined-class fixes, token reconciliation, component consolidation, motion modernization, and visual polish.
>
> **Execution order:** Phase 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9. Phases 0, 1, 2 are low-risk and can ship quickly. Phase 3 is the long pole (migrate per-PR). Phases 7-9 complete the design system infrastructure.
>
> **Unique additions from this merged plan vs prior documents:**
> - Ground truth table + complete broken/undefined class catalog with file:line (from Migration Report)
> - `--zozi-ext-*` + `bcu-*` keyframe fixes (from Migration Report)
> - Gradient reconciliation restoring real multi-stop gradients (from Migration Report)
> - Motion tokens `--zozi-ease-*` + entrance utilities (from Migration Report)
> - Reduced-motion `prefers-reduced-motion: reduce` media query (from Migration Report)
> - Visual QA checklist + commit hygiene (from Migration Report)
> - All component primitives with full code (from V2)
> - Modal drawer variant + MotionConfig + Reveal/Stagger (from V2)
> - **NEW** Phase 7: Data & Feedback components (Table, StatCard, Progress, Tooltip, Popover)
> - **NEW** Phase 8: Navigation & Form systems (Tabs, Breadcrumbs, Stepper, Pagination, Form patterns)
> - **NEW** Phase 9: Infrastructure & Polish (ErrorBoundary, Print styles, Composition patterns, Token docs, Visual testing)

---

## Ground truth about TODAY'S app

| Fact | Detail |
|------|--------|
| CSS entry point | `layout.tsx:4 → import "@/styles/globals.css"`. Only global stylesheet |
| Tailwind | v4 engine (`@import "tailwindcss"`) + v3 `module.exports` config. **No `@theme` block** |
| Theming | `.light`/`.dark` on `<html>` via ThemeProvider + anti-flash script |
| Glass system | `backdrop-filter blur()+saturate()` across 25+ classes; `color-mix()` used 230× |
| Gradients | `--gradient-*` are ALL flat aliases to `var(--color-brand)` except `--gradient-hero` |
| Keyframes in globals | 18 total. `fadeIn`/`slideUp` are **dead** (framer-motion owns entrance) |
| Failing test | `designSystemTokens.test.ts` throws `ENOENT tokens.css` |
| Comms | `comm.css` deleted → 5-zone comms grid unstyled |
| Panels | `panel-modern.css` deleted → collapsible panels unstyled |
| Glow | `glow.css` deleted + layout import removed → 5 glow pages blank |
| Motion | `framer-motion` in 100+ files, `MotionConfig`/`useReducedMotion` in **ZERO** |

### Broken / undefined classes found in live JSX (verified damage)

| Undefined class/token | Used where (file:line) | Consequence |
|---|---|---|
| `theme-btn-danger` | `ui/Button.tsx:36`, `AccountingPanels.tsx:176,194`, `EmailSuppressionManager.tsx:178` | Delete/reject buttons unstyled |
| `theme-btn-danger-outline` | `ui/Button.tsx:37` | Outline danger unstyled |
| `theme-btn-outline` | `admin/payouts/page.tsx:250,589`, `background-jobs/page.tsx:279,362` | Payout outline buttons unstyled |
| `bg-background` (+ `--color-background`) | **49 files** | `--color-background` never defined → utility inert |
| `bg-gradient-brand-to-success` | `admin/suppliers/page.tsx:1074,1436` | Config has no such key → inert credibility bar |
| `hero-display`, `btn btn-primary`, `btn btn-secondary` | `components/Hero.tsx:56,73,86` | Landing hero CTA + headline unstyled |
| `max-w-450` | `components/PanelShell.tsx:394` | Inert max-width |
| `--zozi-ext-*` | `BackgroundEffect.tsx`, `hud.tsx:16-24`, `BannerCanvasEditor.tsx` | `var()` undefined → declarations dropped |
| `bcu-*` keyframes | `BannerCanvasEditor.tsx:492-571` + `banner-effects.module.css` | Referenced but never defined |

### Dead CSS in `globals.css` (defined, 0 JSX uses) — candidates to defrag

`glass-card` (1531), `glass-input` (434), `glass-strong` (1350), `trust-badge` (454), `status-pill`+`status-*` (1775–1816), `priority-*` (1819–1835), `card-base` (1980), `theme-empty-state` (1525), `page-wrapper` (1327), `text-gradient` (1766), `btn-buy-now` (496), `theme-bg-banner-gradient-*` (742–775), `products-hero-*` (820–870), `products-search-shell` (1457), `seasonal-banner-*` (1674–1764), `float-orb-slow/drift` (2103,2107), `crescent-float` (2122), `pendulum-swing` (2140), `lantern-hang` (2145).

---

## Phase 0 — Crash fixes (restore the 4 deleted files + re-wire)

These files exist verbatim at `HEAD` but are deleted from the working tree. The red test requires them.

### 0.1 Restore files verbatim from HEAD

PowerShell, from `frontend/web_app`:
```powershell
git show HEAD:src/styles/tokens.css        | Set-Content src/styles/tokens.css        -Encoding utf8
git show HEAD:src/styles/comm.css          | Set-Content src/styles/comm.css          -Encoding utf8
git show HEAD:src/styles/panel-modern.css  | Set-Content src/styles/panel-modern.css  -Encoding utf8
git show HEAD:src/styles/glow.css          | Set-Content src/styles/glow.css          -Encoding utf8
```

**Verify:** `tokens.css` 246 lines, `comm.css` 292 lines, `panel-modern.css` 74 lines, `glow.css` 43 lines.

### 0.2 Re-wire imports

**File:** `src/styles/globals.css` — line 1
```css
# Search:
@import "tailwindcss";

# Replace:
@import "./tokens.css";
@import "tailwindcss";
```

**File:** `src/app/layout.tsx` — line 4
```tsx
# Search:
import "@/styles/globals.css";

# Replace:
import "@/styles/tokens.css";
import "@/styles/globals.css";
import "@/styles/glow.css";
```

### 0.3 Map tokens into `tailwind.config.js` (test assertions 8–9)

**File:** `tailwind.config.js` — `borderRadius` (lines 100–109)
```js
# Search:
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

# Replace:
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

**File:** `tailwind.config.js` — `transitionDuration` (lines 144–148)
```js
# Search:
      transitionDuration: {
        250: "250ms",
        350: "350ms",
        400: "400ms",
      },

# Replace:
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

### 0.4 Add `max-w-450` (used at `PanelShell.tsx:394`)

**File:** `tailwind.config.js` — `maxWidth` (line 210)
```js
# Search:
        "11xl": "140rem",

# Replace:
        "11xl": "140rem",
        450: "28rem",
```

### 0.5 Delete orphan `variables.css`

```powershell
Remove-Item src/styles/variables.css
```
> Orange `#f97316`/purple `#a855f7` palette conflicts with brand lime/gold. Imported nowhere.

### 0.6 Validate Phase 0

```powershell
npx jest src/__tests__/designSystemTokens.test.ts --runInBand   # must be GREEN
npx tsc --noEmit --skipLibCheck
```

---

## Phase 1 — Fix every undefined class found in live JSX

Append one block to the **end of `globals.css`** (after the RTL helpers at line 2311).

### 1.1 Background token (fixes 49 `bg-background` uses)

**File:** `src/styles/globals.css` — `:root` block, after `--color-surface-0` (line 49)
```css
# Insert after line 49:
  --color-background: var(--color-surface-0);
```

### 1.2 Missing button/danger/hero classes + gradient utilities

Append to the **end of `globals.css`** (after line 2311):
```css
/* ============================================================
   Undefined classes referenced by live JSX — restored
   ============================================================ */

/* theme-btn-danger (Button variant="danger") */
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

/* theme-btn-danger-outline (Button variant="danger-outline") */
.theme-btn-danger-outline {
  background: transparent;
  color: var(--color-danger);
  border: 1px solid color-mix(in srgb, var(--color-danger) 45%, transparent);
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease, transform 0.12s var(--zozi-ease-spring, cubic-bezier(0.22,1,0.36,1));
}
.theme-btn-danger-outline:hover { background-color: color-mix(in srgb, var(--color-danger) 10%, transparent); border-color: var(--color-danger); transform: translateY(-1px); }
.theme-btn-danger-outline:focus-visible { outline: none; box-shadow: var(--zozi-ring); }
.theme-btn-danger-outline:active { transform: translateY(0) scale(0.98); }

/* theme-btn-outline (admin payout/background-jobs) */
.theme-btn-outline {
  background: transparent;
  color: var(--color-brand);
  border: 1px solid color-mix(in srgb, var(--color-brand) 40%, transparent);
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease, transform 0.12s var(--zozi-ease-spring, cubic-bezier(0.22,1,0.36,1));
}
.theme-btn-outline:hover { background-color: color-mix(in srgb, var(--color-brand) 10%, transparent); border-color: var(--color-brand); transform: translateY(-1px); }
.theme-btn-outline:focus-visible { outline: none; box-shadow: var(--zozi-ring); }
.theme-btn-outline:active { transform: translateY(0) scale(0.98); }

/* Hero display + buttons (Hero.tsx) */
.hero-display { font-family: var(--font-display, Fraunces, serif); font-weight: 800; letter-spacing: -0.03em; line-height: 0.95; }
.btn { display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem; border-radius: 0.9rem; font-weight: 700; transition: transform 0.15s var(--zozi-ease-spring, cubic-bezier(0.22,1,0.36,1)), box-shadow 0.2s ease, opacity 0.2s ease; }
.btn:active { transform: translateY(0) scale(0.98); }
.btn-primary { background: linear-gradient(135deg, var(--color-brand-light), var(--color-brand-dark)); color: var(--color-on-brand); box-shadow: 0 20px 40px -18px color-mix(in srgb, var(--color-brand) 60%, transparent); }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 28px 48px -18px color-mix(in srgb, var(--color-brand) 70%, transparent); }
.btn-secondary { background: rgba(255,255,255,0.08); color: #fff; border: 1px solid rgba(255,255,255,0.18); backdrop-filter: blur(12px); }
.btn-secondary:hover { background: rgba(255,255,255,0.14); transform: translateY(-2px); }

/* bg-gradient-brand-to-success (admin/suppliers credibility bars) */
.bg-gradient-brand-to-success { background: linear-gradient(90deg, var(--color-brand), var(--color-success)); }

/* text-gradient (generic clipped gradient text) */
.text-gradient { background: linear-gradient(135deg, var(--color-brand-light), var(--color-accent)); -webkit-background-clip: text; background-clip: text; color: transparent; }
```

### 1.3 `--zozi-ext-*` runtime tokens (used but undefined)

**File:** `src/styles/globals.css` — append after the block above:
```css
/* External effect tokens consumed by BackgroundEffect / hud / BannerCanvas */
:root {
  --zozi-ext-glow: 0 0 24px color-mix(in srgb, var(--color-brand) 40%, transparent);
  --zozi-ext-orbit: 480px;
  --zozi-ext-scanline: rgba(255,255,255,0.06);
  --zozi-ext-scanline-soft: rgba(255,255,255,0.03);
  --zozi-ext-hud-border: color-mix(in srgb, var(--color-brand) 35%, transparent);
}
```

### 1.4 `bcu-*` keyframes (BannerCanvasEditor decorative effects)

Append the missing definitions:
```css
/* banner-canvas-unified keyframes (referenced, never defined) */
@keyframes bcu-confetti { 0% { transform: translateY(-10%) rotate(0); opacity: 1; } 100% { transform: translateY(110vh) rotate(720deg); opacity: 0; } }
@keyframes bcu-snow { 0% { transform: translateY(-10%); opacity: 1; } 100% { transform: translateY(110vh); opacity: 0; } }
@keyframes bcu-spark { 0%, 100% { opacity: 0.2; transform: scale(0.8); } 50% { opacity: 1; transform: scale(1.2); } }
@keyframes bcu-balloon { 0% { transform: translateY(110vh); opacity: 0; } 10% { opacity: 1; } 100% { transform: translateY(-20%); opacity: 0; } }
@keyframes bcu-aurora { 0%,100% { transform: translateX(0) scale(1); opacity: 0.5; } 50% { transform: translateX(4%) scale(1.05); opacity: 0.8; } }
@keyframes bcu-lantern { 0%,100% { transform: translateY(0) rotate(0deg); } 50% { transform: translateY(-8px) rotate(2deg); } }
@keyframes bcu-crescent { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
```

### 1.5 Focus-visible ring (accessibility + polish)

**File:** `src/styles/globals.css` — lines 2255–2271
```css
# Search:
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

# Replace:
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

### 1.6 Harden reduced-motion

**File:** `src/styles/globals.css` — after the existing reduced-motion block (after line 2217, before the focus block):
```css
# Search:
  .aurora-bg {
    animation: none;
  }
}

# Replace:
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

### 1.7 Manual z-index fixes for `z-[200]` / `z-200` usages

**File:** `src/components/ToastContainer.tsx` — line 37
```tsx
# Search:
    <div className="fixed top-4 right-4 flex flex-col gap-1.5 z-200">

# Replace:
    <div className="fixed top-4 right-4 flex flex-col gap-1.5 z-toast">
```

**File:** `src/components/AuthRequiredModal.tsx` — line 165
```tsx
# Search:
          className="fixed inset-0 z-[200] flex items-center justify-center p-4"

# Replace:
          className="fixed inset-0 z-modal flex items-center justify-center p-4"
```

**File:** `src/components/MobileSearchOverlay.tsx` — line 322
```tsx
# Search:
            className="fixed inset-0 z-[200] bg-black/40 backdrop-blur-sm"

# Replace:
            className="fixed inset-0 z-overlay bg-black/40 backdrop-blur-sm"
```

**File:** `src/components/SizeGuide.tsx` — line 57
```tsx
# Search:
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">

# Replace:
        <div className="fixed inset-0 z-modal flex items-center justify-center p-4">
```

### 1.8 Validate Phase 1

```powershell
npx tsc --noEmit --skipLibCheck
npm run lint
npx jest src/__tests__/designSystemTokens.test.ts
```

---

## Phase 2 — Token & gradient reconciliation

Make `theme.ts`, `globals.css`, and `tailwind.config.js` share one source of truth.

### 2.1 Make status/semantic/glass vars theme-aware

**File:** `shared/src/theme.ts` — extend `applyCssTheme()` after line 199:
```ts
  // Status + semantic (currently theme-inert in globals.css)
  root.style.setProperty("--color-success", status.success);
  root.style.setProperty("--color-danger", status.danger);
  root.style.setProperty("--color-warning", status.warning);
  root.style.setProperty("--color-info", status.info);
  root.style.setProperty("--color-accent-dark", brand.accentDark ?? "#C09000");

  // Glass layer re-derived from surface so panels re-theme cleanly
  root.style.setProperty("--color-glass-base", "color-mix(in srgb, " + colors.surface0 + " 60%, transparent)");
  root.style.setProperty("--color-glass-panel", "color-mix(in srgb, " + colors.surface1 + " 84%, transparent)");
  root.style.setProperty("--color-glass-border", colors.borderLight);
```

### 2.2 Restore real gradients (remove flat aliases from globals `:root`)

**File:** `src/styles/globals.css` — lines 51–68 (delete the flat aliases)
```css
# Search:
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

# Replace with (empty — real values now come from tokens.css)
```

> Color drift check: `tokens.css` defines `--color-brand: #2ecc4f` while globals defines `#32CD32`. Because globals' `:root` comes later, globals **wins** → brand stays lime. Gradient *shape* upgrades, brand *color* untouched.

### 2.3 Align radius/shadow tokens

**File:** `src/styles/globals.css` — lines 114–117
```css
# Search:
  --radius-card: 1rem;
  --shadow-card: 0 18px 40px rgb(8 12 24 / 0.35);
  --shadow-card-hover: 0 24px 48px rgb(8 12 24 / 0.45);
  --gradient-hero: linear-gradient(135deg, var(--color-brand-light), var(--color-accent));

# Replace:
  --radius-card: var(--zozi-radius-xl);
  --shadow-card: var(--zozi-elevation-lg);
  --shadow-card-hover: var(--zozi-elevation-xl);
  --gradient-hero: var(--gradient-banner-alt);
```

### 2.4 Add motion tokens

**File:** `src/styles/globals.css` — append:
```css
:root {
  --zozi-ease-out: cubic-bezier(0, 0, 0.2, 1);
  --zozi-ease-spring: cubic-bezier(0.22, 1, 0.36, 1);
}
```

### 2.5 Add font-size tokens (kills `text-[10px]` arbitrarys)

**File:** `tailwind.config.js` — `fontSize` (lines 72–85)
```js
# Replace the fontSize block with:
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "1rem" }],
        "3xs": ["0.5625rem", { lineHeight: "0.875rem" }],
        "4xs": ["0.5rem", { lineHeight: "0.75rem" }],
        "5xs": ["0.4375rem", { lineHeight: "0.625rem" }],
        xs: ["0.75rem", { lineHeight: "1.125rem" }],
        sm: ["0.875rem", { lineHeight: "1.375rem" }],
        base: ["1rem", { lineHeight: "1.625rem" }],
        lg: ["1.125rem", { lineHeight: "1.75rem" }],
        xl: ["1.25rem", { lineHeight: "1.875rem" }],
        "2xl": ["1.5rem", { lineHeight: "2rem" }],
        "3xl": ["1.875rem", { lineHeight: "2.25rem" }],
        "4xl": ["2.25rem", { lineHeight: "2.5rem" }],
        "5xl": ["3rem", { lineHeight: "1.15" }],
        "6xl": ["3.75rem", { lineHeight: "1.1" }],
        display: ["clamp(2.5rem,6vw,4.5rem)", { lineHeight: "1.1" }],
      },
```

### 2.6 Add named z-index scale

**File:** `tailwind.config.js` — `zIndex` (lines 194–202)
```js
# Search:
      zIndex: {
        60: "60",
        70: "70",
        80: "80",
        90: "90",
        100: "100",
        1200: "1200",
        1201: "1201",
      },

# Replace:
      zIndex: {
        header: "50",
        dropdown: "1000",
        sticky: "1020",
        overlay: "1040",
        modal: "1050",
        popover: "1060",
        tooltip: "1070",
        toast: "1080",
      },
```

### 2.7 Add `gradient-brand-to-*` background images

**File:** `tailwind.config.js` — `backgroundImage` (lines 135–136)
```js
# Search:
        "gradient-text": "var(--gradient-brand-text)",
        "gradient-logo-text": "var(--gradient-logo-text)",

# Replace:
        "gradient-text": "var(--gradient-brand-text)",
        "gradient-logo-text": "var(--gradient-logo-text)",
        "gradient-brand-to-success": "var(--gradient-brand-to-success)",
        "gradient-brand-to-brand-dark": "var(--gradient-brand-to-brand-dark)",
        "gradient-brand-to-brand-light": "var(--gradient-brand-to-brand-light)",
```

### 2.8 Kill dead keyframes

**File:** `src/styles/globals.css` — lines 2004–2012 (delete `fadeIn` and `slideUp`)
```css
# Search:
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(12px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

# Replace with (empty)
```

### 2.9 Add `@keyframes scaleIn` (config references it; globals lacks it)

**File:** `src/styles/globals.css` — insert after the `shimmer` keyframe (after line 2002):
```css
@keyframes scaleIn { from { transform: scale(0.95); opacity: 0; } to { transform: scale(1); opacity: 1; } }
```

### 2.10 Validate Phase 2

```powershell
npx tsc --noEmit --skipLibCheck
npm run lint
npx jest src/__tests__/designSystemTokens.test.ts
```
> Visual: toggle light/dark on a product page → status chips and glass panels re-theme.

---

## Phase 3 — Component system consolidation

Goal: make `components/ui/` the **only** way to render buttons, modals, toasts, cards, inputs.

### 3.1 Create `components/ui/index.ts` barrel export

**New file:** `src/components/ui/index.ts`
```ts
export { Button, type ButtonProps, type ButtonVariant, type ButtonSize } from "./Button";
export { Card, CardHeader, CardContent, CardFooter } from "./Card";
export { GlassCard, GlassCardHeader, GlassCardContent, GlassCardFooter } from "./GlassCard";
export { Dropdown } from "./Dropdown";
export { FormLayout, FormInput, FormSelect, FormTextarea, FormCheckbox } from "./FormLayout";
export { StatCard } from "./StatCard";
export { Modal, ModalFooter } from "./shared/Modal";
export { Table, TableHeader, TableBody, TableRow, TableCell, TableHead } from "./shared/Table";
export { Badge, StatusBadge } from "./shared/Badge";
export { LoadingSkeleton, LoadingCard, LoadingTable } from "./shared/LoadingSkeleton";
export { EmptyState } from "./shared/EmptyState";
```

### 3.2 Extend `Modal.tsx` with Drawer variant + a11y props

**File:** `src/components/ui/shared/Modal.tsx`

**Current lines 7–17 (ModalProps interface):**
```tsx
export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: "sm" | "md" | "lg" | "xl";
  showCloseButton?: boolean;
  className?: string;
  bodyClassName?: string;
  overlayClassName?: string;
}
```
**Replace with:**
```tsx
export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: "sm" | "md" | "lg" | "xl";
  showCloseButton?: boolean;
  className?: string;
  bodyClassName?: string;
  overlayClassName?: string;
  variant?: "modal" | "drawer";
  closeOnEscape?: boolean;
  lockScroll?: boolean;
  initialFocusRef?: React.RefObject<HTMLElement>;
}
```

**Current lines 19–44 (Modal function signature + useEffect):** Replace with:
```tsx
export const Modal = forwardRef<HTMLDivElement, ModalProps>(
  ({ 
    isOpen, onClose, title, children, size = "md", showCloseButton = true,
    className, bodyClassName, overlayClassName,
    variant = "modal", closeOnEscape = true, lockScroll = true, initialFocusRef,
  }, ref) => {
    useEffect(() => {
      if (!isOpen) return;
      if (closeOnEscape) {
        const onKey = (event: KeyboardEvent) => {
          if (event.key === "Escape") onClose();
        };
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
      }
    }, [isOpen, onClose, closeOnEscape]);

    useEffect(() => {
      if (!isOpen || !lockScroll) return;
      const prevOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => { document.body.style.overflow = prevOverflow; };
    }, [isOpen, lockScroll]);

    useEffect(() => {
      if (!isOpen || !initialFocusRef?.current) return;
      initialFocusRef.current.focus();
    }, [isOpen, initialFocusRef]);
```

**Current lines 48–53 (`sizeClasses`):** Replace with:
```tsx
    const isDrawer = variant === "drawer";
    const sizeClasses = {
      sm: isDrawer ? "w-80" : "max-w-sm",
      md: isDrawer ? "w-96" : "max-w-md",
      lg: isDrawer ? "w-[28rem]" : "max-w-lg",
      xl: isDrawer ? "w-[32rem]" : "max-w-2xl",
    };
```

**Current lines 55–76 (overlay + panel markup):** Replace with:
```tsx
    return (
      <div 
        className={cn(
          "fixed inset-0 z-modal flex items-center justify-center theme-overlay p-4",
          "animate-fade-in", isDrawer && "items-end sm:items-center",
          overlayClassName
        )}
        onClick={onClose} role="dialog" aria-modal="true"
        aria-labelledby={title ? "modal-title" : undefined}
      >
        <div 
          ref={ref}
          className={cn(
            "glass-panel border rounded-xl shadow-2xl max-h-[80vh] overflow-y-auto",
            "animate-scale-in", sizeClasses[size],
            isDrawer && "rounded-b-none sm:rounded-b-xl sm:rounded-t-none",
            className
          )}
          onClick={(e) => e.stopPropagation()}
        >
```

### 3.3 Delete dead `ToastSystem.tsx`

```powershell
Remove-Item src/components/ToastSystem.tsx
```
> 85 lines, imported nowhere, exports a component named `ToastContainer` (name collision with the real one).

### 3.4 Unify LoadingSkeleton

**Keep:** `src/components/ui/shared/LoadingSkeleton.tsx` (canonical)
**Delete:** `src/components/LoadingSkeleton.tsx` (root duplicate, if it exists)

### 3.5 New primitives to add (file-per-component under `src/components/ui/`)

**`Container.tsx`** — kills width drift:
```tsx
"use client";
import { cn } from "@/lib/utils";
type ContainerWidth = "wide" | "default" | "narrow" | "full";
interface ContainerProps {
  children: React.ReactNode; width?: ContainerWidth; className?: string;
  as?: "div" | "section" | "main";
}
const widthClasses: Record<ContainerWidth, string> = {
  wide: "max-w-[1400px]", default: "max-w-[1200px]", narrow: "max-w-[880px]", full: "max-w-none",
};
export function Container({ children, width = "default", className, as = "div" }: ContainerProps) {
  const Component = as;
  return <Component className={cn("mx-auto w-full px-4 sm:px-6 lg:px-8", widthClasses[width], className)}>{children}</Component>;
}
```

**`PageHeader.tsx`**:
```tsx
"use client";
import { cn } from "@/lib/utils";
interface PageHeaderProps { title: string; description?: string; action?: React.ReactNode; className?: string; }
export function PageHeader({ title, description, action, className }: PageHeaderProps) {
  return (
    <div className={cn("flex items-start justify-between gap-4 mb-6", className)}>
      <div>
        <h1 className="text-2xl font-bold text-text">{title}</h1>
        {description && <p className="mt-1 text-sm text-text-muted">{description}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}
```

**`Section.tsx`**:
```tsx
"use client";
import { cn } from "@/lib/utils";
interface SectionProps { children: React.ReactNode; title?: string; description?: string; className?: string; contentClassName?: string; }
export function Section({ children, title, description, className, contentClassName }: SectionProps) {
  return (
    <section className={cn("mb-8", className)}>
      {(title || description) && (
        <div className="mb-4">
          {title && <h2 className="text-lg font-semibold text-text">{title}</h2>}
          {description && <p className="mt-1 text-sm text-text-muted">{description}</p>}
        </div>
      )}
      <div className={cn(contentClassName)}>{children}</div>
    </section>
  );
}
```

**`Heading.tsx`**:
```tsx
"use client";
import { cn } from "@/lib/utils";
type HeadingLevel = 1 | 2 | 3 | 4;
const levelClasses: Record<HeadingLevel, string> = {
  1: "text-4xl font-extrabold tracking-tight text-text",
  2: "text-2xl font-bold text-text",
  3: "text-xl font-semibold text-text",
  4: "text-lg font-medium text-text",
};
interface HeadingProps { level: HeadingLevel; children: React.ReactNode; className?: string; id?: string; }
export function Heading({ level, children, className, id }: HeadingProps) {
  const Tag = `h${level}` as keyof JSX.IntrinsicElements;
  return <Tag className={cn(levelClasses[level], className)} id={id}>{children}</Tag>;
}
```

**`Alert.tsx`**:
```tsx
"use client";
import { cn } from "@/lib/utils";
import { AlertCircle, CheckCircle, Info, AlertTriangle } from "lucide-react";
type AlertTone = "success" | "danger" | "warning" | "info";
const toneConfig: Record<AlertTone, { bg: string; border: string; text: string; Icon: React.ComponentType<{ className?: string }> }> = {
  success: { bg: "bg-success/10", border: "border-success/30", text: "text-success", Icon: CheckCircle },
  danger: { bg: "bg-danger/10", border: "border-danger/30", text: "text-danger", Icon: AlertCircle },
  warning: { bg: "bg-warning/10", border: "border-warning/30", text: "text-warning", Icon: AlertTriangle },
  info: { bg: "bg-info/10", border: "border-info/30", text: "text-info", Icon: Info },
};
interface AlertProps { tone: AlertTone; title?: string; children: React.ReactNode; className?: string; }
export function Alert({ tone, title, children, className }: AlertProps) {
  const config = toneConfig[tone]; const Icon = config.Icon;
  return (
    <div className={cn("flex items-start gap-3 rounded-xl border p-4", config.bg, config.border, className)}>
      <Icon className={cn("h-5 w-5 shrink-0 mt-0.5", config.text)} />
      <div className="flex-1">
        {title && <p className={cn("text-sm font-semibold", config.text)}>{title}</p>}
        <p className="text-sm text-text-muted">{children}</p>
      </div>
    </div>
  );
}
```

**`StatusBadge.tsx`**:
```tsx
"use client";
import { cn } from "@/lib/utils";
import { status } from "@zozi/shared";
type StatusKey = keyof typeof status;
const dotColors: Record<StatusKey, string> = { success: "bg-success", danger: "bg-danger", warning: "bg-warning", info: "bg-info" };
interface StatusBadgeProps { status: StatusKey; label: string; className?: string; }
export function StatusBadge({ status: statusKey, label, className }: StatusBadgeProps) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium border border-glass-border-mid bg-glass-base", className)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", dotColors[statusKey])} />
      {label}
    </span>
  );
}
```

**`Spinner.tsx`**:
```tsx
"use client";
import { cn } from "@/lib/utils";
interface SpinnerProps { size?: "sm" | "md" | "lg"; className?: string; }
const sizeClasses = { sm: "h-4 w-4 border-2", md: "h-6 w-6 border-2", lg: "h-8 w-8 border-3" };
export function Spinner({ size = "md", className }: SpinnerProps) {
  return <div role="status" aria-label="Loading" className={cn("animate-spin rounded-full border-current border-t-transparent text-brand", sizeClasses[size], className)} />;
}
```

**`Drawer.tsx`** (promoted from PanelPage):
```tsx
"use client";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { X } from "@/lib/icons";
interface DrawerProps { isOpen: boolean; onClose: () => void; title?: string; children: React.ReactNode; side?: "left" | "right"; size?: "sm" | "md" | "lg"; }
const sideClasses = { left: "left-0 border-l", right: "right-0 border-r" };
const sizeClasses = { sm: "w-80", md: "w-96", lg: "w-[28rem]" };
export function Drawer({ isOpen, onClose, title, children, side = "right", size = "md" }: DrawerProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-modal theme-overlay" onClick={onClose} />
          <motion.div initial={{ x: side === "right" ? "100%" : "-100%" }} animate={{ x: 0 }}
            exit={{ x: side === "right" ? "100%" : "-100%" }}
            transition={{ type: "spring", damping: 24, stiffness: 200 }}
            className={cn("fixed top-0 bottom-0 glass-panel border shadow-2xl flex flex-col", sideClasses[side], sizeClasses[size])}
          >
            {title && (
              <div className="flex items-center justify-between p-4 border-b border-glass-border-mid">
                <h3 className="text-sm font-bold text-text">{title}</h3>
                <button onClick={onClose} className="text-text-muted hover:text-text rounded-lg p-1" aria-label="Close drawer">
                  <X className="h-4 w-4" />
                </button>
              </div>
            )}
            <div className="flex-1 overflow-y-auto p-4">{children}</div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
```

### 3.6 Validate Phase 3

```powershell
npx tsc --noEmit --skipLibCheck
npm run lint
npx jest
```

---

## Phase 4 — Motion system modernization

### 4.1 Global reduced-motion (single change fixes 100+ files)

**File:** `src/app/layout.tsx`

**Add import after line 3:**
```tsx
# Search:
import { Suspense } from "react";

# Replace:
import { Suspense } from "react";
import { MotionConfig } from "framer-motion";
```

**Wrap the app-frame div (lines 97–118):**
```tsx
# Search:
            <div className="relative" data-app-frame style={{ isolation: "isolate", zIndex: 10 }}>

# Replace:
            <MotionConfig reducedMotion="user">
            <div className="relative" data-app-frame style={{ isolation: "isolate", zIndex: 10 }}>
```

**And close the wrapper after `</div>` at line 118:**
```tsx
# Search:
              </div>
            </div>
          </AuthProvider>

# Replace:
              </div>
            </div>
            </MotionConfig>
          </AuthProvider>
```

### 4.2 App-level page transitions

**New file:** `src/app/template.tsx`
```tsx
"use client";
import { motion } from "framer-motion";
export default function Template({ children }: { children: React.ReactNode }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}>
      {children}
    </motion.div>
  );
}
```

### 4.3 Promote `PanelPage.tsx` motion variants to `Reveal` + `Stagger`

**New file:** `src/components/ui/Reveal.tsx`
```tsx
"use client";
import { motion, type Variants } from "framer-motion";
export const ENTER_VARIANTS: Variants = {
  hidden: { opacity: 0, y: 12 },
  visible: (i: number = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.28, delay: i * 0.04, ease: [0.22, 1, 0.36, 1] } }),
};
export const FADE_SCALE: Variants = {
  hidden: { opacity: 0, scale: 0.96 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.2, ease: "easeOut" } },
  exit: { opacity: 0, scale: 0.96, transition: { duration: 0.15, ease: "easeIn" } },
};
export function Reveal({ children, variant = ENTER_VARIANTS, custom, className }: {
  children: React.ReactNode; variant?: Variants; custom?: number; className?: string;
}) {
  return (
    <motion.div initial="hidden" animate="visible" exit="exit" variants={variant} custom={custom} className={className}>
      {children}
    </motion.div>
  );
}
```

**New file:** `src/components/ui/Stagger.tsx`
```tsx
"use client";
import { motion, type Variants } from "framer-motion";
export function staggerItems(delay: number = 0.04): Variants {
  return { hidden: {}, visible: { transition: { staggerChildren: delay } } };
}
export function Stagger({ children, stagger = 0.04, className }: {
  children: React.ReactNode; stagger?: number; className?: string;
}) {
  return (
    <motion.div initial="hidden" animate="visible" variants={staggerItems(stagger)} className={className}>
      {children}
    </motion.div>
  );
}
```

### 4.4 Validate Phase 4

```powershell
npx playwright test e2e/smoke.spec.ts
```
> Manual: OS "Reduce motion" ON → no entrance/hover/modal animation. OFF → smooth.

---

## Phase 5 — Modern look & polish

### 5.1 Entrance utilities

**File:** `src/styles/globals.css` — append:
```css
.anim-fade-up  { animation: slideUp 0.5s var(--zozi-ease-out, cubic-bezier(0,0,0.2,1)) both; }
.anim-fade-in  { animation: fadeIn 0.4s ease-out both; }
.anim-scale-in { animation: scaleIn 0.3s var(--zozi-ease-out, cubic-bezier(0,0,0.2,1)) both; }
.anim-rise     { animation: comm-rise 0.28s var(--zozi-ease-spring, cubic-bezier(0.22,1,0.36,1)) both; }
```

### 5.2 Card hover lift (dark parity)

**File:** `src/styles/globals.css` — append:
```css
.theme-card:hover, .theme-panel:hover, .theme-elevated:hover { transform: translateY(-2px); }
```

### 5.3 Spring transitions on primary brand actions

**File:** `src/styles/globals.css` — append:
```css
.theme-btn-primary, .theme-btn-accent, .theme-btn-secondary,
.btn-place-order, .btn-buy-now { transition: transform 0.12s var(--zozi-ease-spring, cubic-bezier(0.22,1,0.36,1)), box-shadow 0.2s ease, background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease; }
.theme-btn-primary:active, .theme-btn-accent:active, .theme-btn-secondary:active,
.btn-place-order:active, .btn-buy-now:active { transform: translateY(0) scale(0.98); }
```

### 5.4 Glass cross-browser `-webkit-backdrop-filter` twins

**File:** `src/styles/globals.css` — append:
```css
.glass, .glass-strong, .theme-card, .glass-product-card, .glass-dropdown, .theme-panel, .theme-elevated {
  -webkit-backdrop-filter: blur(14px) saturate(140%);
  backdrop-filter: blur(14px) saturate(140%);
}
```

### 5.5 Hero gradient utility

**File:** `src/styles/globals.css` — append:
```css
.hero-gradient {
  background:
    radial-gradient(60% 80% at 15% 0%, color-mix(in srgb, var(--color-brand) 16%, transparent), transparent 60%),
    radial-gradient(50% 70% at 100% 10%, color-mix(in srgb, var(--color-accent) 14%, transparent), transparent 55%),
    linear-gradient(160deg, var(--color-surface-0), var(--color-surface-1) 60%, var(--color-surface-2));
}
```

### 5.6 View Transitions (progressive)

**File:** `src/styles/globals.css` — append:
```css
@media (prefers-reduced-motion: no-preference) {
  ::view-transition-old(root), ::view-transition-new(root) {
    animation-duration: 220ms;
    animation-timing-function: cubic-bezier(0.22, 1, 0.36, 1);
  }
}
```

### 5.7 Delete `!important` panel overrides (after Phase 3 migration complete)

**File:** `src/styles/globals.css` — delete lines 908–976 (the entire `:where(.supplier, .logistics-partner, .admin)` block).

### 5.8 Validate Phase 5

```powershell
npm run lint
npx jest
```
> Manual QA: Tab through form → focus-visible ring. Safari/Chrome → glass renders. Toggle light/dark → re-theme. Page navigation → smooth transition.

---

## Phase 6 — Rollout, verification & gates

### 6.1 Per-phase gate checklist

```powershell
cd frontend/web_app
npx jest src/__tests__/designSystemTokens.test.ts   # must pass after Phase 0
npx tsc --noEmit --skipLibCheck                      # after 1,2,3
npm run lint                                          # after 1,2,3,5
npx jest                                              # after 3
npx playwright test e2e/smoke.spec.ts               # after 4,5
```

### 6.2 Migration priority order for Phase 3

Migrate per-PR in this order (highest traffic first):
1. **Product card buttons** → `ui/Button` (BannerCanvasEditor.tsx has 40+ raw `theme-btn-secondary`)
2. **Cart / checkout buttons** → `ui/Button`
3. **Auth modals** (AuthRequiredModal, QuickViewModal) → `ui/Modal`
4. **Admin panel modals** → `ui/Modal`
5. **Supplier panel modals** → `ui/Modal`
6. **Remaining modals** → `ui/Modal`

### 6.3 Codemod scripts (run once, review, then commit)

**`scripts/codemod-fontsize.mjs`:**
```js
import { readdirSync, readFileSync, writeFileSync } from "fs";
import { join } from "path";
const root = join(process.cwd(), "src");
const map = [
  [/text-\[10px\]/g, "text-xs"],
  [/text-\[9px\]/g,  "text-3xs"],
  [/text-\[8px\]/g,  "text-4xs"],
  [/text-\[7px\]/g,  "text-5xs"],
];
function walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) walk(full);
    else if (entry.name.endsWith(".tsx") || entry.name.endsWith(".ts")) {
      let src = readFileSync(full, "utf8");
      let changed = false;
      for (const [re, replacement] of map) {
        if (re.test(src)) { src = src.replace(re, replacement); changed = true; }
      }
      if (changed) writeFileSync(full, src);
    }
  }
}
walk(root);
console.log("Font-size codemod complete.");
```

**`scripts/codemod-zindex.mjs`:**
```js
import { readdirSync, readFileSync, writeFileSync } from "fs";
import { join } from "path";
const root = join(process.cwd(), "src");
const map = [
  [/z-\[200\]/g,  "z-modal"],
  [/z-200/g,      "z-toast"],
  [/z-\[999\]/g,  "z-modal"],
  [/z-\[300\]/g,  "z-dropdown"],
];
function walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) walk(full);
    else if (entry.name.endsWith(".tsx") || entry.name.endsWith(".ts")) {
      let src = readFileSync(full, "utf8");
      let changed = false;
      for (const [re, replacement] of map) {
        if (re.test(src)) { src = src.replace(re, replacement); changed = true; }
      }
      if (changed) writeFileSync(full, src);
    }
  }
}
walk(root);
console.log("Z-index codemod complete.");
```

Run with:
```powershell
node scripts/codemod-fontsize.mjs
node scripts/codemod-zindex.mjs
git diff  # review before committing
```

### 6.4 Visual QA checklist (browser — `npm run dev`; both themes + OS reduce-motion)

1. **Comms** (`/comms`): rail collapse, ctx drawer, typing dots, presence pulse, msg rise
2. **Panel pages** (admin/supplier): collapsible panels expand, `.panel-compact-stat` hover
3. **Glow pages** (logistics-partners, tracking, supplier labels, logo-animation): backgrounds render
4. **Danger actions** (`<Button variant="danger">`, reject/delete): red gradient + haptic press
5. **Payouts** outline buttons, **suppliers credibility bars** gradient fill
6. **Hero** (home): `hero-display` headline + `btn btn-primary`/`btn btn-secondary` styled
7. **Loading.tsx pages**: `bg-background` resolves to page background
8. **Banner editor**: confetti/spark/snow effect layers animate
9. **Banner gradients** (seasonal banners, brand pages): real multi-stop, not flat brand
10. **Tab through UI**: brand halo focus ring on keyboard, clean on mouse
11. **Reduced-motion**: no decorative motion

### 6.5 Commit hygiene

```powershell
git add src/styles/tokens.css src/styles/comm.css src/styles/panel-modern.css src/styles/glow.css
git rm src/styles/variables.css
git add src/styles/globals.css tailwind.config.js src/app/layout.tsx
```
> Keep `*.bak` until browser QA passes. Do **not** commit `_design_investigation/` scratch.

---

## Complete File Change Summary

| Phase | File | Lines | Action |
|-------|------|-------|--------|
| 0 | `src/styles/globals.css` | 1 | Insert `@import "./tokens.css"` |
| 0 | `src/app/layout.tsx` | 4 | Insert `import "@/styles/tokens.css"` + `import "@/styles/glow.css"` |
| 0 | `src/styles/variables.css` | 90 | DELETE |
| 0 | `src/styles/comm.css` | 292 | RESTORE from HEAD |
| 0 | `src/styles/panel-modern.css` | 74 | RESTORE from HEAD |
| 0 | `src/styles/glow.css` | 43 | RESTORE from HEAD |
| 0 | `src/styles/tokens.css` | 246 | RESTORE from HEAD |
| 0 | `tailwind.config.js` | 100-109 | Map borderRadius to `--zozi-radius-*` |
| 0 | `tailwind.config.js` | 144-154 | Map transitionDuration to `--zozi-duration-*` |
| 0 | `tailwind.config.js` | 210 | Add `max-w-450` |
| 1 | `src/styles/globals.css` | 49 | Insert `--color-background` |
| 1 | `src/styles/globals.css` | end | Append undefined-class block (~110L) |
| 1 | `src/styles/globals.css` | end | Append `--zozi-ext-*` tokens |
| 1 | `src/styles/globals.css` | end | Append `bcu-*` keyframes |
| 1 | `src/styles/globals.css` | 2255-2271 | Replace focus-kill with focus-visible ring |
| 1 | `src/styles/globals.css` | 2217 | Append reduced-motion media query |
| 1 | `src/components/ToastContainer.tsx` | 37 | `z-200` → `z-toast` |
| 1 | `src/components/AuthRequiredModal.tsx` | 165 | `z-[200]` → `z-modal` |
| 1 | `src/components/MobileSearchOverlay.tsx` | 322 | `z-[200]` → `z-overlay` |
| 1 | `src/components/SizeGuide.tsx` | 57 | `z-[200]` → `z-modal` |
| 2 | `shared/src/theme.ts` | 199-213 | Extend `applyCssTheme` with status/glass vars |
| 2 | `src/styles/globals.css` | 51-68 | Delete flat gradient aliases |
| 2 | `src/styles/globals.css` | 114-117 | Align radius/shadow tokens |
| 2 | `src/styles/globals.css` | end | Append motion tokens |
| 2 | `tailwind.config.js` | 72-88 | Add 3xs-5xs font sizes |
| 2 | `tailwind.config.js` | 194-203 | Replace z-index with named scale |
| 2 | `tailwind.config.js` | 135-139 | Add gradient-brand-to-* keys |
| 2 | `src/styles/globals.css` | 2004-2012 | Delete dead fadeIn/slideUp keyframes |
| 2 | `src/styles/globals.css` | ~2002 | Insert `@keyframes scaleIn` |
| 3 | `src/components/ui/index.ts` | NEW | Barrel export all primitives |
| 3 | `src/components/ui/shared/Modal.tsx` | 7-76 | Add drawer variant + a11y props |
| 3 | `src/components/ToastSystem.tsx` | 85 | DELETE |
| 3 | `src/components/LoadingSkeleton.tsx` | — | DELETE (root duplicate) |
| 3 | `src/components/ui/Container.tsx` | NEW | Container primitive |
| 3 | `src/components/ui/PageHeader.tsx` | NEW | PageHeader primitive |
| 3 | `src/components/ui/Section.tsx` | NEW | Section primitive |
| 3 | `src/components/ui/Heading.tsx` | NEW | Heading primitive |
| 3 | `src/components/ui/Alert.tsx` | NEW | Alert primitive |
| 3 | `src/components/ui/StatusBadge.tsx` | NEW | StatusBadge primitive |
| 3 | `src/components/ui/Spinner.tsx` | NEW | Spinner primitive |
| 3 | `src/components/ui/Drawer.tsx` | NEW | Drawer primitive |
| 3 | 20+ modal files | — | Migrate to `<Modal>` (per-PR) |
| 3 | 80+ button files | — | Migrate to `<Button>` (per-PR) |
| 4 | `src/app/layout.tsx` | 3, 97-120 | Import `MotionConfig` + wrap app |
| 4 | `src/app/template.tsx` | NEW | Page transition wrapper |
| 4 | `src/components/ui/Reveal.tsx` | NEW | Promote ENTER_VARIANTS + FADE_SCALE |
| 4 | `src/components/ui/Stagger.tsx` | NEW | Promote staggerItems |
| 5 | `src/styles/globals.css` | end | Append entrance utilities |
| 5 | `src/styles/globals.css` | end | Append card hover lift |
| 5 | `src/styles/globals.css` | end | Append spring transitions |
| 5 | `src/styles/globals.css` | end | Append webkit backdrop-filter twins |
| 5 | `src/styles/globals.css` | end | Append hero gradient |
| 5 | `src/styles/globals.css` | end | Append view-transition utilities |
| 5 | `src/styles/globals.css` | 908-976 | Delete `!important` panel overrides |
| 6 | `scripts/codemod-fontsize.mjs` | NEW | Font-size codemod |
| 6 | `scripts/codemod-zindex.mjs` | NEW | Z-index codemod |

---

## What we keep (do NOT change)

- Current lime/gold brand: `--color-brand: #32CD32`, `--color-accent: #FFD700`
- `globals.css` existing vocabulary (glass, theme-card, theme-panel, shimmer, seasonal-banner-*, etc.)
- `tailwind.config.js` `scaleIn`/`spring`/`expo-out`/`smooth` easing tokens
- Rich `BackgroundEffect.tsx` seasonal engine
- `BannerCanvasEditor.tsx` (legitimate canvas/SVG colors)
- Chart color palettes

## What we drop

- `src/styles/variables.css` (orphan, orange/purple, conflicts with brand)
- `src/components/ToastSystem.tsx` (dead code, imported nowhere)
- `src/components/LoadingSkeleton.tsx` (root duplicate — keep `ui/shared/LoadingSkeleton.tsx`)
- `globals.css:2004–2012` dead `fadeIn`/`slideUp` keyframes
- `globals.css:2255–2271` focus-kill block (replaced by Phase 1.5)
- `globals.css:908–976` `!important` panel overrides (replaced by component system)
- All raw `theme-btn-*` usages outside `ui/Button.tsx` (migrated in Phase 3)
- All raw `glass-panel` modal markup outside `ui/Modal.tsx` (migrated in Phase 3)
- All `text-[10px]…[7px]` arbitrarys (migrated in Phase 2.5 + codemod)

---

## Phase 7 — Data & Feedback components

This phase adds the data visualization and feedback components needed for admin/supplier/logistics panels.

### 7.1 Enhanced Table primitive

**New file:** `src/components/ui/Table.tsx`
```tsx
"use client";
import { cn } from "@/lib/utils";

interface TableProps {
  children: React.ReactNode;
  className?: string;
  striped?: boolean;
  compact?: boolean;
  bordered?: boolean;
}

export function Table({ children, className, striped = false, compact = false, bordered = false }: TableProps) {
  return (
    <div className={cn("w-full overflow-x-auto rounded-xl border border-glass-border-mid")}>
      <table className={cn("w-full text-sm text-left", className)}>
        {children}
      </table>
    </div>
  );
}

export function TableHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return <thead className={cn("text-xs text-text-muted uppercase bg-glass-panel border-b border-glass-border-mid", className)}>{children}</thead>;
}

export function TableBody({ children, className, striped }: { children: React.ReactNode; className?: string; striped?: boolean }) {
  return <tbody className={cn(stripped && "[&>tr:nth-child(even)]:bg-glass-faint", className)}>{children}</tbody>;
}

export function TableRow({ children, className, onClick }: { children: React.ReactNode; className?: string; onClick?: () => void }) {
  return <tr className={cn("border-b border-glass-border-soft last:border-b-0", onClick && "cursor-pointer hover:bg-glass-panel transition-colors", className)} onClick={onClick}>{children}</tr>;
}

export function TableHead({ children, className, sortable, sorted, onSort }: {
  children: React.ReactNode; className?: string; sortable?: boolean; sorted?: "asc" | "desc" | null; onSort?: () => void;
}) {
  return (
    <th className={cn("px-4 py-3 font-semibold text-text-muted", sortable && "cursor-pointer select-none hover:text-text", className)} onClick={onSort}>
      <span className="inline-flex items-center gap-1">
        {children}
        {sortable && <span className={cn("text-xs", sorted ? "text-brand" : "text-text-faint")}>{sorted === "asc" ? "▲" : sorted === "desc" ? "▼" : "⇅"}</span>}
      </span>
    </th>
  );
}

export function TableCell({ children, className }: { children: React.ReactNode; className?: string }) {
  return <td className={cn("px-4 py-3 text-text", className)}>{children}</td>;
}
```

### 7.2 StatCard primitive (data visualization)

**New file:** `src/components/ui/StatCard.tsx`
```tsx
"use client";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

type TrendDirection = "up" | "down" | "neutral";

interface StatCardProps {
  label: string;
  value: string | number;
  change?: string;
  trend?: TrendDirection;
  icon?: React.ReactNode;
  className?: string;
}

const trendConfig: Record<TrendDirection, { icon: React.ComponentType<{ className?: string }>; color: string }> = {
  up: { icon: TrendingUp, color: "text-success" },
  down: { icon: TrendingDown, color: "text-danger" },
  neutral: { icon: Minus, color: "text-text-muted" },
};

export function StatCard({ label, value, change, trend, icon, className }: StatCardProps) {
  const trendInfo = trend ? trendConfig[trend] : null;
  const TrendIcon = trendInfo?.icon;

  return (
    <div className={cn("glass-panel rounded-xl border p-4 transition-all hover:shadow-card-hover", className)}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-xs font-medium text-text-muted uppercase tracking-wide">{label}</p>
          <p className="mt-1 text-2xl font-bold text-text">{value}</p>
          {change && (
            <div className="mt-1 flex items-center gap-1">
              {TrendIcon && <TrendIcon className={cn("h-3 w-3", trendInfo?.color)} />}
              <span className={cn("text-xs font-medium", trendInfo?.color)}>{change}</span>
            </div>
          )}
        </div>
        {icon && <div className="shrink-0 text-text-faint">{icon}</div>}
      </div>
    </div>
  );
}
```

### 7.3 Progress bar primitive

**New file:** `src/components/ui/Progress.tsx`
```tsx
"use client";
import { cn } from "@/lib/utils";

type ProgressVariant = "default" | "success" | "warning" | "danger";

interface ProgressProps {
  value: number;
  max?: number;
  variant?: ProgressVariant;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  className?: string;
}

const variantColors: Record<ProgressVariant, string> = {
  default: "bg-brand",
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
};

const sizeClasses = { sm: "h-1", md: "h-2", lg: "h-3" };

export function Progress({ value, max = 100, variant = "default", size = "md", showLabel = false, className }: ProgressProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div className={cn("w-full", className)}>
      {showLabel && (
        <div className="flex justify-between mb-1">
          <span className="text-xs text-text-muted">Progress</span>
          <span className="text-xs font-medium text-text">{Math.round(percentage)}%</span>
        </div>
      )}
      <div className={cn("w-full rounded-full bg-surface-2 overflow-hidden", sizeClasses[size])}>
        <div
          className={cn("h-full rounded-full transition-all duration-300", variantColors[variant])}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
        />
      </div>
    </div>
  );
}
```

### 7.4 Tooltip primitive

**New file:** `src/components/ui/Tooltip.tsx`
```tsx
"use client";
import { useState, useRef, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

type TooltipPosition = "top" | "bottom" | "left" | "right";

interface TooltipProps {
  content: ReactNode;
  children: ReactNode;
  position?: TooltipPosition;
  delay?: number;
  className?: string;
}

const positionClasses: Record<TooltipPosition, string> = {
  top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
  bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
  left: "right-full top-1/2 -translate-y-1/2 mr-2",
  right: "left-full top-1/2 -translate-y-1/2 ml-2",
};

export function Tooltip({ content, children, position = "top", delay = 200, className }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();

  const show = () => {
    timeoutRef.current = setTimeout(() => setIsVisible(true), delay);
  };

  const hide = () => {
    clearTimeout(timeoutRef.current);
    setIsVisible(false);
  };

  return (
    <span className={cn("relative inline-flex", className)} onMouseEnter={show} onMouseLeave={hide} onFocus={show} onBlur={hide}>
      {children}
      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className={cn("absolute z-tooltip px-2.5 py-1.5 text-xs font-medium text-text bg-glass-strong border border-glass-border-mid rounded-lg shadow-lg whitespace-nowrap pointer-events-none", positionClasses[position])}
            role="tooltip"
          >
            {content}
          </motion.div>
        )}
      </AnimatePresence>
    </span>
  );
}
```

### 7.5 Popover primitive

**New file:** `src/components/ui/Popover.tsx`
```tsx
"use client";
import { useState, useRef, useEffect, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

interface PopoverProps {
  trigger: ReactNode;
  children: ReactNode;
  align?: "left" | "right" | "center";
  side?: "bottom" | "top";
  className?: string;
}

export function Popover({ trigger, children, align = "left", side = "bottom", className }: PopoverProps) {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setIsOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const alignClasses = { left: "left-0", right: "right-0", center: "left-1/2 -translate-x-1/2" };
  const sideClasses = { bottom: "top-full mt-2", top: "bottom-full mb-2" };

  return (
    <div className={cn("relative inline-flex", className)} ref={ref}>
      <div onClick={() => setIsOpen(!isOpen)}>{trigger}</div>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: side === "bottom" ? -4 : 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: side === "bottom" ? -4 : 4 }}
            transition={{ duration: 0.15 }}
            className={cn("absolute z-popover w-72 rounded-xl border border-glass-border-mid bg-glass-strong shadow-xl p-4", alignClasses[align], sideClasses[side])}
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
```

### 7.6 Validate Phase 7

```powershell
npx tsc --noEmit --skipLibCheck
npm run lint
npx jest
```

---

## Phase 8 — Navigation & Form systems

This phase adds navigation components and comprehensive form patterns.

### 8.1 Tabs primitive

**New file:** `src/components/ui/Tabs.tsx`
```tsx
"use client";
import { createContext, useContext, useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface TabsContextValue {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const TabsContext = createContext<TabsContextValue | null>(null);

interface TabsProps {
  children: ReactNode;
  defaultTab: string;
  className?: string;
}

export function Tabs({ children, defaultTab, className }: TabsProps) {
  const [activeTab, setActiveTab] = useState(defaultTab);
  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className={cn("w-full", className)}>{children}</div>
    </TabsContext.Provider>
  );
}

export function TabList({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("flex border-b border-glass-border-mid", className)} role="tablist">{children}</div>;
}

export function Tab({ id, children, className }: { id: string; children: ReactNode; className?: string }) {
  const ctx = useContext(TabsContext);
  if (!ctx) throw new Error("Tab must be used within Tabs");
  const isActive = ctx.activeTab === id;
  return (
    <button
      role="tab"
      aria-selected={isActive}
      className={cn("px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px", isActive ? "text-brand border-brand" : "text-text-muted border-transparent hover:text-text", className)}
      onClick={() => ctx.setActiveTab(id)}
    >
      {children}
    </button>
  );
}

export function TabPanel({ id, children, className }: { id: string; children: ReactNode; className?: string }) {
  const ctx = useContext(TabsContext);
  if (!ctx) throw new Error("TabPanel must be used within Tabs");
  if (ctx.activeTab !== id) return null;
  return <div className={cn("py-4", className)} role="tabpanel">{children}</div>;
}
```

### 8.2 Breadcrumbs primitive

**New file:** `src/components/ui/Breadcrumbs.tsx`
```tsx
"use client";
import { cn } from "@/lib/utils";
import { ChevronRight } from "@/lib/icons";

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  className?: string;
}

export function Breadcrumbs({ items, className }: BreadcrumbsProps) {
  return (
    <nav aria-label="Breadcrumb" className={cn("flex items-center gap-1.5 text-sm", className)}>
      {items.map((item, i) => (
        <span key={i} className="flex items-center gap-1.5">
          {i > 0 && <ChevronRight className="h-3 w-3 text-text-faint" />}
          {item.href && i < items.length - 1 ? (
            <a href={item.href} className="text-text-muted hover:text-text transition-colors">{item.label}</a>
          ) : (
            <span className={cn(i === items.length - 1 ? "text-text font-medium" : "text-text-muted")}>{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
```

### 8.3 Pagination primitive

**New file:** `src/components/ui/Pagination.tsx`
```tsx
"use client";
import { cn } from "@/lib/utils";
import { ChevronLeft, ChevronRight } from "@/lib/icons";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
}

export function Pagination({ currentPage, totalPages, onPageChange, className }: PaginationProps) {
  const pages = getPageNumbers(currentPage, totalPages);

  return (
    <nav className={cn("flex items-center gap-1", className)} aria-label="Pagination">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage <= 1}
        className="flex items-center justify-center w-8 h-8 rounded-lg text-text-muted hover:text-text hover:bg-glass-panel disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        aria-label="Previous page"
      >
        <ChevronLeft className="h-4 w-4" />
      </button>
      {pages.map((page, i) => (
        <button
          key={i}
          onClick={() => typeof page === "number" && onPageChange(page)}
          disabled={page === "..."}
          className={cn("flex items-center justify-center w-8 h-8 rounded-lg text-sm font-medium transition-colors", page === currentPage ? "bg-brand text-on-brand" : "text-text-muted hover:text-text hover:bg-glass-panel", page === "..." && "cursor-default")}
          aria-current={page === currentPage ? "page" : undefined}
        >
          {page}
        </button>
      ))}
      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage >= totalPages}
        className="flex items-center justify-center w-8 h-8 rounded-lg text-text-muted hover:text-text hover:bg-glass-panel disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        aria-label="Next page"
      >
        <ChevronRight className="h-4 w-4" />
      </button>
    </nav>
  );
}

function getPageNumbers(current: number, total: number): (number | string)[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  if (current <= 3) return [1, 2, 3, 4, "...", total];
  if (current >= total - 2) return [1, "...", total - 3, total - 2, total - 1, total];
  return [1, "...", current - 1, current, current + 1, "...", total];
}
```

### 8.4 Stepper primitive

**New file:** `src/components/ui/Stepper.tsx`
```tsx
"use client";
import { cn } from "@/lib/utils";
import { Check } from "@/lib/icons";

interface Step {
  label: string;
  description?: string;
}

interface StepperProps {
  steps: Step[];
  currentStep: number;
  className?: string;
}

export function Stepper({ steps, currentStep, className }: StepperProps) {
  return (
    <div className={cn("flex items-start w-full", className)}>
      {steps.map((step, i) => (
        <div key={i} className="flex-1 flex flex-col items-center relative">
          {i > 0 && (
            <div className={cn("absolute top-4 right-1/2 w-full h-0.5 -translate-y-1/2", i <= currentStep ? "bg-brand" : "bg-surface-2")} />
          )}
          <div className={cn("relative z-10 flex items-center justify-center w-8 h-8 rounded-full border-2 text-xs font-bold transition-colors", i < currentStep ? "bg-brand border-brand text-on-brand" : i === currentStep ? "border-brand text-brand bg-surface-0" : "border-surface-2 text-text-muted bg-surface-0")}>
            {i < currentStep ? <Check className="h-4 w-4" /> : i + 1}
          </div>
          <div className="mt-2 text-center">
            <p className={cn("text-xs font-medium", i <= currentStep ? "text-text" : "text-text-muted")}>{step.label}</p>
            {step.description && <p className="text-xs text-text-faint mt-0.5">{step.description}</p>}
          </div>
        </div>
      ))}
    </div>
  );
}
```

### 8.5 Form validation patterns

**New file:** `src/components/ui/FormGroup.tsx`
```tsx
"use client";
import { createContext, useContext, type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface FormGroupContextValue {
  error?: string;
  required?: boolean;
}

const FormGroupContext = createContext<FormGroupContextValue>({});

interface FormGroupProps {
  children: ReactNode;
  label?: string;
  error?: string;
  required?: boolean;
  hint?: string;
  className?: string;
}

export function FormGroup({ children, label, error, required, hint, className }: FormGroupProps) {
  return (
    <FormGroupContext.Provider value={{ error, required }}>
      <div className={cn("mb-4", className)}>
        {label && (
          <label className="block text-sm font-medium text-text mb-1.5">
            {label}
            {required && <span className="text-danger ml-0.5">*</span>}
          </label>
        )}
        {children}
        {error && <p className="mt-1.5 text-xs text-danger flex items-center gap-1">{error}</p>}
        {hint && !error && <p className="mt-1.5 text-xs text-text-faint">{hint}</p>}
      </div>
    </FormGroupContext.Provider>
  );
}

export function useFormGroup() {
  return useContext(FormGroupContext);
}
```

### 8.6 Enhanced Input with validation

**New file:** `src/components/ui/Input.tsx`
```tsx
"use client";
import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import { useFormGroup } from "./FormGroup";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(({ className, error, ...props }, ref) => {
  const formGroup = useFormGroup();
  const hasError = error || formGroup.error;

  return (
    <input
      ref={ref}
      className={cn(
        "w-full rounded-lg border bg-surface-1 px-3 py-2 text-sm text-text placeholder:text-text-faint transition-colors",
        "focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand",
        hasError && "border-danger focus:ring-danger/30 focus:border-danger",
        className
      )}
      aria-invalid={hasError ? "true" : undefined}
      {...props}
    />
  );
});

Input.displayName = "Input";
```

### 8.7 Enhanced Textarea

**New file:** `src/components/ui/Textarea.tsx`
```tsx
"use client";
import { forwardRef, type TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import { useFormGroup } from "./FormGroup";

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(({ className, error, ...props }, ref) => {
  const formGroup = useFormGroup();
  const hasError = error || formGroup.error;

  return (
    <textarea
      ref={ref}
      className={cn(
        "w-full rounded-lg border bg-surface-1 px-3 py-2 text-sm text-text placeholder:text-text-faint transition-colors resize-y min-h-[80px]",
        "focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand",
        hasError && "border-danger focus:ring-danger/30 focus:border-danger",
        className
      )}
      aria-invalid={hasError ? "true" : undefined}
      {...props}
    />
  );
});

Textarea.displayName = "Textarea";
```

### 8.8 Enhanced Select

**New file:** `src/components/ui/Select.tsx`
```tsx
"use client";
import { forwardRef, type SelectHTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import { ChevronDown } from "@/lib/icons";
import { useFormGroup } from "./FormGroup";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  error?: boolean;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(({ className, children, error, ...props }, ref) => {
  const formGroup = useFormGroup();
  const hasError = error || formGroup.error;

  return (
    <div className="relative">
      <select
        ref={ref}
        className={cn(
          "w-full appearance-none rounded-lg border bg-surface-1 px-3 py-2 pr-8 text-sm text-text transition-colors",
          "focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand",
          hasError && "border-danger focus:ring-danger/30 focus:border-danger",
          className
        )}
        aria-invalid={hasError ? "true" : undefined}
        {...props}
      >
        {children}
      </select>
      <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted pointer-events-none" />
    </div>
  );
});

Select.displayName = "Select";
```

### 8.9 Checkbox & Radio primitives

**New file:** `src/components/ui/Checkbox.tsx`
```tsx
"use client";
import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import { Check, Minus } from "@/lib/icons";

interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  indeterminate?: boolean;
  label?: string;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(({ className, indeterminate, label, checked, ...props }, ref) => {
  return (
    <label className={cn("inline-flex items-center gap-2 cursor-pointer text-sm text-text", className)}>
      <span className={cn("relative flex items-center justify-center w-4 h-4 rounded border transition-colors", checked || indeterminate ? "bg-brand border-brand" : "border-border bg-surface-1")}>
        <input ref={ref} type="checkbox" className="sr-only" checked={checked} {...props} />
        {indeterminate ? <Minus className="h-3 w-3 text-on-brand" /> : checked ? <Check className="h-3 w-3 text-on-brand" /> : null}
      </span>
      {label && <span>{label}</span>}
    </label>
  );
});

Checkbox.displayName = "Checkbox";
```

**New file:** `src/components/ui/Radio.tsx`
```tsx
"use client";
import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface RadioProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label?: string;
}

export const Radio = forwardRef<HTMLInputElement, RadioProps>(({ className, label, checked, ...props }, ref) => {
  return (
    <label className={cn("inline-flex items-center gap-2 cursor-pointer text-sm text-text", className)}>
      <span className={cn("relative flex items-center justify-center w-4 h-4 rounded-full border transition-colors", checked ? "border-brand" : "border-border bg-surface-1")}>
        <input ref={ref} type="radio" className="sr-only" checked={checked} {...props} />
        {checked && <span className="w-2 h-2 rounded-full bg-brand" />}
      </span>
      {label && <span>{label}</span>}
    </label>
  );
});

Radio.displayName = "Radio";
```

### 8.10 Switch primitive

**New file:** `src/components/ui/Switch.tsx`
```tsx
"use client";
import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface SwitchProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label?: string;
}

export const Switch = forwardRef<HTMLInputElement, SwitchProps>(({ className, label, checked, ...props }, ref) => {
  return (
    <label className={cn("inline-flex items-center gap-2 cursor-pointer text-sm text-text", className)}>
      <span className={cn("relative w-9 h-5 rounded-full transition-colors", checked ? "bg-brand" : "bg-surface-2")}>
        <input ref={ref} type="checkbox" role="switch" className="sr-only" checked={checked} {...props} />
        <span className={cn("absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform", checked && "translate-x-4")} />
      </span>
      {label && <span>{label}</span>}
    </label>
  );
});

Switch.displayName = "Switch";
```

### 8.11 Enhanced LoadingSkeleton with variants

**File:** `src/components/ui/shared/LoadingSkeleton.tsx` — extend with:
```tsx
# Add to existing file after LoadingTable:

interface LoadingAvatarProps { size?: "sm" | "md" | "lg"; className?: string; }
export function LoadingAvatar({ size = "md", className }: LoadingAvatarProps) {
  const sizeClasses = { sm: "h-8 w-8", md: "h-10 w-10", lg: "h-12 w-12" };
  return <div className={cn("rounded-full bg-glass-mid animate-pulse", sizeClasses[size], className)} />;
}

interface LoadingButtonProps { className?: string; }
export function LoadingButton({ className }: LoadingButtonProps) {
  return <div className={cn("h-10 w-24 rounded-lg bg-glass-mid animate-pulse", className)} />;
}

interface LoadingImageProps { className?: string; aspectRatio?: "square" | "video" | "wide"; }
export function LoadingImage({ className, aspectRatio = "video" }: LoadingImageProps) {
  const aspectClasses = { square: "aspect-square", video: "aspect-video", wide: "aspect-[21/9]" };
  return <div className={cn("rounded-xl bg-glass-mid animate-pulse", aspectClasses[aspectRatio], className)} />;
}
```

### 8.12 Enhanced EmptyState with contextual variants

**File:** `src/components/ui/shared/EmptyState.tsx` — extend with:
```tsx
# Add to existing file:

interface EmptyStateActionProps {
  icon?: React.ReactNode; title: string; description?: string; action?: React.ReactNode; className?: string;
}
export function EmptyStateAction({ icon, title, description, action, className }: EmptyStateActionProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-12 px-4 text-center", className)}>
      {icon && <div className="mb-4 text-text-faint">{icon}</div>}
      <h3 className="text-lg font-semibold text-text mb-1">{title}</h3>
      {description && <p className="text-sm text-text-muted mb-4 max-w-sm">{description}</p>}
      {action}
    </div>
  );
}
```

### 8.13 Validate Phase 8

```powershell
npx tsc --noEmit --skipLibCheck
npm run lint
npx jest
```

---

## Phase 9 — Infrastructure & Polish

This phase adds error handling, print styles, composition patterns, and developer tooling.

### 9.1 Error Boundary UI component

**New file:** `src/components/ui/ErrorState.tsx`
```tsx
"use client";
import { cn } from "@/lib/utils";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({ title = "Something went wrong", message, onRetry, className }: ErrorStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-12 px-4 text-center", className)}>
      <div className="flex items-center justify-center w-12 h-12 rounded-full bg-danger/10 mb-4">
        <AlertTriangle className="h-6 w-6 text-danger" />
      </div>
      <h3 className="text-lg font-semibold text-text mb-1">{title}</h3>
      {message && <p className="text-sm text-text-muted mb-4 max-w-sm">{message}</p>}
      {onRetry && (
        <button onClick={onRetry} className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand text-on-brand text-sm font-medium hover:bg-brand-dark transition-colors">
          <RefreshCw className="h-4 w-4" />
          Try Again
        </button>
      )}
    </div>
  );
}
```

### 9.2 Print styles

**File:** `src/styles/globals.css` — append:
```css
/* -- Print styles (invoices, shipping labels, reports) ------------------------ */
@media print {
  *, *::before, *::after {
    background: transparent !important;
    color: #000 !important;
    box-shadow: none !important;
    text-shadow: none !important;
  }

  body { font-size: 12pt; line-height: 1.5; }

  .no-print, [data-no-print], nav, aside, footer,
  .theme-sidebar-shell, .theme-topbar { display: none !important; }

  .print-only { display: block !important; }

  .glass-panel, .theme-card, .theme-panel {
    border: 1px solid #ccc !important;
    break-inside: avoid;
  }

  a[href]::after {
    content: " (" attr(href) ")";
    font-size: 10pt;
    color: #666;
  }

  @page { margin: 1.5cm; }
}
```

### 9.3 Component composition patterns

**New file:** `src/components/ui/Group.tsx`
```tsx
"use client";
import { cn } from "@/lib/utils";

interface GroupProps {
  children: React.ReactNode; className?: string;
  gap?: "none" | "sm" | "md" | "lg";
  align?: "start" | "center" | "end" | "stretch";
  justify?: "start" | "center" | "end" | "between" | "around";
  wrap?: boolean;
}

const gapClasses = { none: "gap-0", sm: "gap-1", md: "gap-2", lg: "gap-4" };
const alignClasses = { start: "items-start", center: "items-center", end: "items-end", stretch: "items-stretch" };
const justifyClasses = { start: "justify-start", center: "justify-center", end: "justify-end", between: "justify-between", around: "justify-around" };

export function Group({ children, className, gap = "md", align = "center", justify = "start", wrap = true }: GroupProps) {
  return (
    <div className={cn("flex", gapClasses[gap], alignClasses[align], justifyClasses[justify], wrap && "flex-wrap", className)}>
      {children}
    </div>
  );
}

interface StackProps {
  children: React.ReactNode; className?: string;
  gap?: "none" | "sm" | "md" | "lg";
  align?: "start" | "center" | "end" | "stretch";
}

export function Stack({ children, className, gap = "md", align = "stretch" }: StackProps) {
  return (
    <div className={cn("flex flex-col", gapClasses[gap], alignClasses[align], className)}>
      {children}
    </div>
  );
}
```

### 9.4 Design token documentation

**New file:** `src/components/ui/tokens.ts`
```ts
/**
 * ZOZI Design Tokens — reference for component development.
 * 
 * CSS Variables (from globals.css + tokens.css):
 *   --color-brand, --color-brand-light, --color-brand-dark
 *   --color-accent, --color-accent-light, --color-accent-dark
 *   --color-surface-0..3, --color-border, --color-border-light
 *   --color-text, --color-text-muted, --color-text-faint
 *   --color-success, --color-danger, --color-warning, --color-info
 *   --color-on-brand, --color-on-accent, --color-on-warning
 *   --color-glass-base/mid/hi/solid/panel/faint
 *   --color-glass-border/border-mid/border-soft
 *   --zozi-radius-sm/md/lg/xl/2xl/pill
 *   --zozi-elevation-sm/md/lg/xl, --zozi-ring
 *   --zozi-duration-fast/base/normal/slow/slower/slowest
 *   --zozi-ease-out, --zozi-ease-spring
 *   --gradient-banner, --gradient-banner-alt, --gradient-hero, --gradient-card
 * 
 * Tailwind Utilities:
 *   bg-{color}, text-{color}, border-{color}
 *   rounded-{sm..pill}
 *   shadow-{card/card-sm/card-lg/glow-primary/glass}
 *   animate-{fade-in/slide-up/scale-in/shimmer/float/ticker}
 *   z-{header/dropdown/sticky/overlay/modal/popover/tooltip/toast}
 */

export const tokens = {
  colors: {
    brand: "var(--color-brand)",
    brandLight: "var(--color-brand-light)",
    brandDark: "var(--color-brand-dark)",
    accent: "var(--color-accent)",
    surface0: "var(--color-surface-0)",
    surface1: "var(--color-surface-1)",
    surface2: "var(--color-surface-2)",
    surface3: "var(--color-surface-3)",
    border: "var(--color-border)",
    text: "var(--color-text)",
    textMuted: "var(--color-text-muted)",
    success: "var(--color-success)",
    danger: "var(--color-danger)",
    warning: "var(--color-warning)",
    info: "var(--color-info)",
  },
  radius: {
    sm: "var(--zozi-radius-sm)",
    md: "var(--zozi-radius-md)",
    lg: "var(--zozi-radius-lg)",
    xl: "var(--zozi-radius-xl)",
    "2xl": "var(--zozi-radius-2xl)",
    pill: "var(--zozi-radius-pill)",
  },
  elevation: {
    sm: "var(--zozi-elevation-sm)",
    md: "var(--zozi-elevation-md)",
    lg: "var(--zozi-elevation-lg)",
    xl: "var(--zozi-elevation-xl)",
  },
  duration: {
    fast: "var(--zozi-duration-fast)",
    base: "var(--zozi-duration-base)",
    normal: "var(--zozi-duration-normal)",
    slow: "var(--zozi-duration-slow)",
    slower: "var(--zozi-duration-slower)",
    slowest: "var(--zozi-duration-slowest)",
  },
} as const;
```

### 9.5 Visual regression testing setup

**New file:** `.storybook/main.ts`
```ts
import type { StorybookConfig } from "@storybook/nextjs";
const config: StorybookConfig = {
  stories: ["../src/components/**/*.stories.@(js|jsx|ts|tsx)"],
  addons: ["@storybook/addon-links", "@storybook/addon-essentials", "@storybook/addon-interactions", "@storybook/addon-a11y"],
  framework: { name: "@storybook/nextjs", options: {} },
  docs: { autodocs: "tag" },
};
export default config;
```

**New file:** `.storybook/preview.ts`
```ts
import type { StorybookConfig } from "@storybook/nextjs";
import "../src/styles/globals.css";
import "../src/styles/tokens.css";

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: "^on[A-Z].*" },
    controls: { matchers: { color: /(background|color)$/i, date: /Date$/ } },
    backgrounds: {
      default: "dark",
      values: [
        { name: "dark", value: "#000000" },
        { name: "light", value: "#fbfcf8" },
      ],
    },
  },
};

export default preview;
```

**New file:** `src/components/ui/Button.stories.tsx`
```ts
import type { Meta, StoryObj } from "@storybook/react";
import { Button } from "./Button";

const meta: Meta<typeof Button> = {
  title: "UI/Button",
  component: Button,
  tags: ["autodocs"],
  argTypes: {
    variant: { control: "select", options: ["primary", "secondary", "ghost", "danger", "danger-outline", "accent", "admin", "warning", "info"] },
    size: { control: "select", options: ["sm", "md", "lg"] },
  },
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = { args: { variant: "primary", children: "Button" } };
export const Secondary: Story = { args: { variant: "secondary", children: "Button" } };
export const Danger: Story = { args: { variant: "danger", children: "Delete" } };
export const Loading: Story = { args: { variant: "primary", isLoading: true, children: "Loading" } };
```

### 9.6 Update barrel export

**File:** `src/components/ui/index.ts` — add new exports:
```ts
# Add to existing barrel:
export { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "./Table";
export { StatCard } from "./StatCard";
export { Progress } from "./Progress";
export { Tooltip } from "./Tooltip";
export { Popover } from "./Popover";
export { Tabs, TabList, Tab, TabPanel } from "./Tabs";
export { Breadcrumbs } from "./Breadcrumbs";
export { Pagination } from "./Pagination";
export { Stepper } from "./Stepper";
export { FormGroup, useFormGroup } from "./FormGroup";
export { Input } from "./Input";
export { Textarea } from "./Textarea";
export { Select } from "./Select";
export { Checkbox } from "./Checkbox";
export { Radio } from "./Radio";
export { Switch } from "./Switch";
export { ErrorState } from "./ErrorState";
export { Group, Stack } from "./Group";
export { tokens } from "./tokens";
```

### 9.7 Validate Phase 9

```powershell
npx tsc --noEmit --skipLibCheck
npm run lint
npx jest
```

---

## Complete File Change Summary (All Phases)

| Phase | File | Lines | Action |
|-------|------|-------|--------|
| 0 | `src/styles/globals.css` | 1 | Insert `@import "./tokens.css"` |
| 0 | `src/app/layout.tsx` | 4 | Insert `import "@/styles/tokens.css"` + `import "@/styles/glow.css"` |
| 0 | `src/styles/variables.css` | 90 | DELETE |
| 0 | `src/styles/comm.css` | 292 | RESTORE from HEAD |
| 0 | `src/styles/panel-modern.css` | 74 | RESTORE from HEAD |
| 0 | `src/styles/glow.css` | 43 | RESTORE from HEAD |
| 0 | `src/styles/tokens.css` | 246 | RESTORE from HEAD |
| 0 | `tailwind.config.js` | 100-109 | Map borderRadius to `--zozi-radius-*` |
| 0 | `tailwind.config.js` | 144-154 | Map transitionDuration to `--zozi-duration-*` |
| 0 | `tailwind.config.js` | 210 | Add `max-w-450` |
| 1 | `src/styles/globals.css` | 49 | Insert `--color-background` |
| 1 | `src/styles/globals.css` | end | Append undefined-class block (~110L) |
| 1 | `src/styles/globals.css` | end | Append `--zozi-ext-*` tokens |
| 1 | `src/styles/globals.css` | end | Append `bcu-*` keyframes |
| 1 | `src/styles/globals.css` | 2255-2271 | Replace focus-kill with focus-visible ring |
| 1 | `src/styles/globals.css` | 2217 | Append reduced-motion media query |
| 1 | `src/components/ToastContainer.tsx` | 37 | `z-200` → `z-toast` |
| 1 | `src/components/AuthRequiredModal.tsx` | 165 | `z-[200]` → `z-modal` |
| 1 | `src/components/MobileSearchOverlay.tsx` | 322 | `z-[200]` → `z-overlay` |
| 1 | `src/components/SizeGuide.tsx` | 57 | `z-[200]` → `z-modal` |
| 2 | `shared/src/theme.ts` | 199-213 | Extend `applyCssTheme` with status/glass vars |
| 2 | `src/styles/globals.css` | 51-68 | Delete flat gradient aliases |
| 2 | `src/styles/globals.css` | 114-117 | Align radius/shadow tokens |
| 2 | `src/styles/globals.css` | end | Append motion tokens |
| 2 | `tailwind.config.js` | 72-88 | Add 3xs-5xs font sizes |
| 2 | `tailwind.config.js` | 194-203 | Replace z-index with named scale |
| 2 | `tailwind.config.js` | 135-139 | Add gradient-brand-to-* keys |
| 2 | `src/styles/globals.css` | 2004-2012 | Delete dead fadeIn/slideUp keyframes |
| 2 | `src/styles/globals.css` | ~2002 | Insert `@keyframes scaleIn` |
| 3 | `src/components/ui/index.ts` | NEW | Barrel export all primitives |
| 3 | `src/components/ui/shared/Modal.tsx` | 7-76 | Add drawer variant + a11y props |
| 3 | `src/components/ToastSystem.tsx` | 85 | DELETE |
| 3 | `src/components/LoadingSkeleton.tsx` | — | DELETE (root duplicate) |
| 3 | `src/components/ui/Container.tsx` | NEW | Container primitive |
| 3 | `src/components/ui/PageHeader.tsx` | NEW | PageHeader primitive |
| 3 | `src/components/ui/Section.tsx` | NEW | Section primitive |
| 3 | `src/components/ui/Heading.tsx` | NEW | Heading primitive |
| 3 | `src/components/ui/Alert.tsx` | NEW | Alert primitive |
| 3 | `src/components/ui/StatusBadge.tsx` | NEW | StatusBadge primitive |
| 3 | `src/components/ui/Spinner.tsx` | NEW | Spinner primitive |
| 3 | `src/components/ui/Drawer.tsx` | NEW | Drawer primitive |
| 3 | 20+ modal files | — | Migrate to `<Modal>` (per-PR) |
| 3 | 80+ button files | — | Migrate to `<Button>` (per-PR) |
| 4 | `src/app/layout.tsx` | 3, 97-120 | Import `MotionConfig` + wrap app |
| 4 | `src/app/template.tsx` | NEW | Page transition wrapper |
| 4 | `src/components/ui/Reveal.tsx` | NEW | Promote ENTER_VARIANTS + FADE_SCALE |
| 4 | `src/components/ui/Stagger.tsx` | NEW | Promote staggerItems |
| 5 | `src/styles/globals.css` | end | Append entrance utilities |
| 5 | `src/styles/globals.css` | end | Append card hover lift |
| 5 | `src/styles/globals.css` | end | Append spring transitions |
| 5 | `src/styles/globals.css` | end | Append webkit backdrop-filter twins |
| 5 | `src/styles/globals.css` | end | Append hero gradient |
| 5 | `src/styles/globals.css` | end | Append view-transition utilities |
| 5 | `src/styles/globals.css` | 908-976 | Delete `!important` panel overrides |
| 6 | `scripts/codemod-fontsize.mjs` | NEW | Font-size codemod |
| 6 | `scripts/codemod-zindex.mjs` | NEW | Z-index codemod |
| 7 | `src/components/ui/Table.tsx` | NEW | Enhanced Table primitive |
| 7 | `src/components/ui/StatCard.tsx` | NEW | StatCard primitive |
| 7 | `src/components/ui/Progress.tsx` | NEW | Progress bar primitive |
| 7 | `src/components/ui/Tooltip.tsx` | NEW | Tooltip primitive |
| 7 | `src/components/ui/Popover.tsx` | NEW | Popover primitive |
| 8 | `src/components/ui/Tabs.tsx` | NEW | Tabs primitive |
| 8 | `src/components/ui/Breadcrumbs.tsx` | NEW | Breadcrumbs primitive |
| 8 | `src/components/ui/Pagination.tsx` | NEW | Pagination primitive |
| 8 | `src/components/ui/Stepper.tsx` | NEW | Stepper primitive |
| 8 | `src/components/ui/FormGroup.tsx` | NEW | FormGroup primitive |
| 8 | `src/components/ui/Input.tsx` | NEW | Enhanced Input primitive |
| 8 | `src/components/ui/Textarea.tsx` | NEW | Enhanced Textarea primitive |
| 8 | `src/components/ui/Select.tsx` | NEW | Enhanced Select primitive |
| 8 | `src/components/ui/Checkbox.tsx` | NEW | Checkbox primitive |
| 8 | `src/components/ui/Radio.tsx` | NEW | Radio primitive |
| 8 | `src/components/ui/Switch.tsx` | NEW | Switch primitive |
| 8 | `src/components/ui/shared/LoadingSkeleton.tsx` | — | Extend with new variants |
| 8 | `src/components/ui/shared/EmptyState.tsx` | — | Extend with contextual variants |
| 9 | `src/components/ui/ErrorState.tsx` | NEW | Error state component |
| 9 | `src/styles/globals.css` | end | Append print styles |
| 9 | `src/components/ui/Group.tsx` | NEW | Group + Stack layout primitives |
| 9 | `src/components/ui/tokens.ts` | NEW | Token reference export |
| 9 | `.storybook/main.ts` | NEW | Storybook config |
| 9 | `.storybook/preview.ts` | NEW | Storybook preview |
| 9 | `src/components/ui/Button.stories.tsx` | NEW | Button stories |
| 9 | `src/components/ui/index.ts` | — | Update barrel with new exports |

---

## What we keep (do NOT change)

- Current lime/gold brand: `--color-brand: #32CD32`, `--color-accent: #FFD700`
- `globals.css` existing vocabulary (glass, theme-card, theme-panel, shimmer, seasonal-banner-*, etc.)
- `tailwind.config.js` `scaleIn`/`spring`/`expo-out`/`smooth` easing tokens
- Rich `BackgroundEffect.tsx` seasonal engine
- `BannerCanvasEditor.tsx` (legitimate canvas/SVG colors)
- Chart color palettes

## What we drop

- `src/styles/variables.css` (orphan, orange/purple, conflicts with brand)
- `src/components/ToastSystem.tsx` (dead code, imported nowhere)
- `src/components/LoadingSkeleton.tsx` (root duplicate — keep `ui/shared/LoadingSkeleton.tsx`)
- `globals.css:2004–2012` dead `fadeIn`/`slideUp` keyframes
- `globals.css:2255–2271` focus-kill block (replaced by Phase 1.5)
- `globals.css:908–976` `!important` panel overrides (replaced by component system)
- All raw `theme-btn-*` usages outside `ui/Button.tsx` (migrated in Phase 3)
- All raw `glass-panel` modal markup outside `ui/Modal.tsx` (migrated in Phase 3)
- All `text-[10px]…[7px]` arbitrarys (migrated in Phase 2.5 + codemod)

---

## Phase 10 — Specialized components & infrastructure

This final phase adds the remaining specialized components, responsive patterns, and operational infrastructure needed for a truly production-ready system.

### 10.1 Accordion/Collapse primitive

**New file:** `src/components/ui/Accordion.tsx`
```tsx
"use client";
import { createContext, useContext, useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { ChevronDown } from "@/lib/icons";

interface AccordionContextValue {
  openItems: Set<string>;
  toggle: (id: string) => void;
}

const AccordionContext = createContext<AccordionContextValue | null>(null);

interface AccordionProps {
  children: ReactNode;
  allowMultiple?: boolean;
  className?: string;
}

export function Accordion({ children, allowMultiple = false, className }: AccordionProps) {
  const [openItems, setOpenItems] = useState<Set<string>>(new Set());

  const toggle = (id: string) => {
    setOpenItems((prev) => {
      const next = new Set(prev);
      if (next.has(id)) { next.delete(id); } else {
        if (!allowMultiple) next.clear();
        next.add(id);
      }
      return next;
    });
  };

  return (
    <AccordionContext.Provider value={{ openItems, toggle }}>
      <div className={cn("divide-y divide-glass-border-mid", className)}>{children}</div>
    </AccordionContext.Provider>
  );
}

interface AccordionItemProps {
  id: string; title: string; children: ReactNode; icon?: ReactNode; className?: string;
}

export function AccordionItem({ id, title, children, icon, className }: AccordionItemProps) {
  const ctx = useContext(AccordionContext);
  if (!ctx) throw new Error("AccordionItem must be used within Accordion");
  const isOpen = ctx.openItems.has(id);

  return (
    <div className={cn("py-2", className)}>
      <button className="flex items-center justify-between w-full py-2 text-left text-sm font-medium text-text hover:text-brand transition-colors" onClick={() => ctx.toggle(id)} aria-expanded={isOpen}>
        <span className="flex items-center gap-2">{icon}{title}</span>
        <ChevronDown className={cn("h-4 w-4 text-text-muted transition-transform", isOpen && "rotate-180")} />
      </button>
      <div className={cn("overflow-hidden transition-all", isOpen ? "max-h-96 opacity-100" : "max-h-0 opacity-0")}>
        <div className="py-2 text-sm text-text-muted">{children}</div>
      </div>
    </div>
  );
}
```

### 10.2 Divider/Separator primitive

**New file:** `src/components/ui/Divider.tsx`
```tsx
"use client";
import { cn } from "@/lib/utils";

type DividerOrientation = "horizontal" | "vertical";
type DividerVariant = "solid" | "dashed" | "dotted";

interface DividerProps {
  orientation?: DividerOrientation; variant?: DividerVariant; className?: string; label?: string;
}

const orientationClasses: Record<DividerOrientation, string> = {
  horizontal: "w-full border-t", vertical: "h-full border-l",
};
const variantClasses: Record<DividerVariant, string> = {
  solid: "border-solid", dashed: "border-dashed", dotted: "border-dotted",
};

export function Divider({ orientation = "horizontal", variant = "solid", className, label }: DividerProps) {
  if (label) {
    return (
      <div className={cn("flex items-center w-full", className)}>
        <div className={cn("flex-1 border-t border-glass-border-mid", variantClasses[variant])} />
        <span className="px-3 text-xs text-text-muted">{label}</span>
        <div className={cn("flex-1 border-t border-glass-border-mid", variantClasses[variant])} />
      </div>
    );
  }
  return <div className={cn("border-glass-border-mid", orientationClasses[orientation], variantClasses[variant], className)} role="separator" />;
}
```

### 10.3 Avatar + AvatarGroup primitives

**New file:** `src/components/ui/Avatar.tsx`
```tsx
"use client";
import { cn } from "@/lib/utils";

type AvatarSize = "xs" | "sm" | "md" | "lg" | "xl";

interface AvatarProps {
  src?: string; alt?: string; initials?: string; size?: AvatarSize;
  status?: "online" | "offline" | "away" | "busy"; className?: string;
}

const sizeClasses: Record<AvatarSize, string> = {
  xs: "h-6 w-6 text-xs", sm: "h-8 w-8 text-xs", md: "h-10 w-10 text-sm", lg: "h-12 w-12 text-base", xl: "h-16 w-16 text-lg",
};
const statusSizeClasses: Record<AvatarSize, string> = {
  xs: "h-1.5 w-1.5 bottom-0 right-0", sm: "h-2 w-2 bottom-0 right-0", md: "h-2.5 w-2.5 bottom-0 right-0", lg: "h-3 w-3 bottom-0 right-0", xl: "h-3.5 w-3.5 bottom-0.5 right-0.5",
};
const statusColors = { online: "bg-success", offline: "bg-text-faint", away: "bg-warning", busy: "bg-danger" };

export function Avatar({ src, alt, initials, size = "md", status, className }: AvatarProps) {
  return (
    <span className={cn("relative inline-flex", className)}>
      <span className={cn("inline-flex items-center justify-center rounded-full bg-glass-panel border border-glass-border-mid overflow-hidden", sizeClasses[size])}>
        {src ? <img src={src} alt={alt || "Avatar"} className="h-full w-full object-cover" /> : <span className="font-medium text-text-muted">{initials || "?"}</span>}
      </span>
      {status && <span className={cn("absolute rounded-full border-2 ring-2 ring-surface-0", statusSizeClasses[size], statusColors[status])} />}
    </span>
  );
}

interface AvatarGroupProps {
  children: React.ReactNode; max?: number; size?: AvatarSize; className?: string;
}

export function AvatarGroup({ children, max = 4, size = "md", className }: AvatarGroupProps) {
  const childArray = Array.isArray(children) ? children : [children];
  const visible = childArray.slice(0, max);
  const remaining = childArray.length - max;
  return (
    <div className={cn("flex -space-x-2", className)}>
      {visible.map((child, i) => <div key={i} className="ring-2 ring-surface-0 rounded-full">{child}</div>)}
      {remaining > 0 && <span className={cn("inline-flex items-center justify-center rounded-full bg-glass-panel border border-glass-border-mid font-medium text-text-muted", sizeClasses[size])}>+{remaining}</span>}
    </div>
  );
}
```

### 10.4 Toast queue/positioning improvements

**File:** `src/components/ToastContainer.tsx` — replace with enhanced version:
```tsx
"use client";
import { useToastStore } from "@/lib/toastStore";
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

type ToastPosition = "top-right" | "top-left" | "bottom-right" | "bottom-left" | "top-center" | "bottom-center";

const STYLES = {
  error: { bg: "bg-danger/15 border-danger/30", text: "text-danger", Icon: AlertCircle },
  success: { bg: "bg-success/15 border-success/30", text: "text-success", Icon: CheckCircle },
  info: { bg: "bg-info/15 border-info/30", text: "text-info", Icon: Info },
  warning: { bg: "bg-warning/15 border-warning/30", text: "text-warning", Icon: AlertTriangle },
} as const;

const positionClasses: Record<ToastPosition, string> = {
  "top-right": "top-4 right-4", "top-left": "top-4 left-4", "bottom-right": "bottom-4 right-4",
  "bottom-left": "bottom-4 left-4", "top-center": "top-4 left-1/2 -translate-x-1/2", "bottom-center": "bottom-4 left-1/2 -translate-x-1/2",
};

interface ToastContainerProps { position?: ToastPosition; maxVisible?: number; }

export default function ToastContainer({ position = "top-right", maxVisible = 5 }: ToastContainerProps) {
  const toasts = useToastStore((s) => s.toasts);
  const remove = useToastStore((s) => s.removeToast);
  const visibleToasts = toasts.slice(0, maxVisible);

  if (visibleToasts.length === 0) return null;

  return (
    <div className={cn("fixed flex flex-col gap-2 z-toast max-w-sm w-full pointer-events-none", positionClasses[position])}>
      <AnimatePresence mode="popLayout">
        {visibleToasts.map((t) => {
          const style = STYLES[t.type as keyof typeof STYLES] || STYLES.info;
          const IconComp = style.Icon;
          return (
            <motion.div key={t.id} layout initial={{ opacity: 0, y: -20, scale: 0.95 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} transition={{ duration: 0.2 }}
              className={cn("pointer-events-auto max-w-sm w-full rounded-xl border p-3 shadow-lg backdrop-blur-sm flex items-start gap-2.5 bg-glass-strong", style.bg)}>
              <IconComp className={cn("h-4 w-4 shrink-0 mt-0.5", style.text)} />
              <p className={cn("text-xs font-medium flex-1", style.text)}>{t.message}</p>
              <button onClick={() => remove(t.id)} className="shrink-0 text-text-faint hover:text-text transition-colors"><X className="h-3 w-3" /></button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
```

### 10.5 Command palette primitive

**New file:** `src/components/ui/CommandPalette.tsx`
```tsx
"use client";
import { useState, useEffect, useCallback, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { Search } from "@/lib/icons";

interface CommandItem { id: string; label: string; icon?: ReactNode; shortcut?: string; onSelect: () => void; }

interface CommandPaletteProps { isOpen: boolean; onClose: () => void; items: CommandItem[]; placeholder?: string; className?: string; }

export function CommandPalette({ isOpen, onClose, items, placeholder = "Type a command...", className }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const filtered = items.filter((item) => item.label.toLowerCase().includes(query.toLowerCase()));

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (!isOpen) return;
    if (e.key === "Escape") onClose();
    if (e.key === "ArrowDown") { e.preventDefault(); setSelectedIndex((i) => Math.min(i + 1, filtered.length - 1)); }
    if (e.key === "ArrowUp") { e.preventDefault(); setSelectedIndex((i) => Math.max(i - 1, 0)); }
    if (e.key === "Enter" && filtered[selectedIndex]) { filtered[selectedIndex].onSelect(); onClose(); }
  }, [isOpen, filtered, selectedIndex, onClose]);

  useEffect(() => { document.addEventListener("keydown", handleKeyDown); return () => document.removeEventListener("keydown", handleKeyDown); }, [handleKeyDown]);
  useEffect(() => { if (isOpen) { setQuery(""); setSelectedIndex(0); } }, [isOpen]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-modal theme-overlay" onClick={onClose} />
          <motion.div initial={{ opacity: 0, scale: 0.95, y: -20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: -20 }} transition={{ duration: 0.15 }}
            className={cn("fixed top-[20%] left-1/2 -translate-x-1/2 z-modal w-full max-w-lg rounded-xl border border-glass-border-mid bg-glass-strong shadow-2xl overflow-hidden", className)}>
            <div className="flex items-center gap-2 px-3 py-2 border-b border-glass-border-mid">
              <Search className="h-4 w-4 text-text-muted" />
              <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder={placeholder} className="flex-1 bg-transparent text-sm text-text placeholder:text-text-faint outline-none" autoFocus />
            </div>
            <div className="max-h-80 overflow-y-auto py-1">
              {filtered.length === 0 ? <p className="px-3 py-6 text-center text-sm text-text-muted">No results found</p> : filtered.map((item, i) => (
                <button key={item.id} className={cn("flex items-center justify-between w-full px-3 py-2 text-sm transition-colors", i === selectedIndex ? "bg-glass-panel text-text" : "text-text-muted hover:bg-glass-faint")}
                  onClick={() => { item.onSelect(); onClose(); }} onMouseEnter={() => setSelectedIndex(i)}>
                  <span className="flex items-center gap-2">{item.icon}{item.label}</span>
                  {item.shortcut && <span className="text-xs text-text-faint">{item.shortcut}</span>}
                </button>
              ))}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
```

### 10.6 File upload with drag-and-drop

**New file:** `src/components/ui/FileUpload.tsx`
```tsx
"use client";
import { useState, useRef, type ChangeEvent, type DragEvent } from "react";
import { cn } from "@/lib/utils";
import { Upload, X, FileText } from "lucide-react";

interface FileUploadProps { accept?: string; multiple?: boolean; maxSize?: number; onFilesSelected: (files: File[]) => void; className?: string; }

export function FileUpload({ accept, multiple = false, maxSize = 10, onFilesSelected, className }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: DragEvent) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = () => setIsDragging(false);
  const handleDrop = (e: DragEvent) => {
    e.preventDefault(); setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    const validFiles = maxSize ? droppedFiles.filter((f) => f.size <= maxSize * 1024 * 1024) : droppedFiles;
    setFiles(validFiles); onFilesSelected(validFiles);
  };
  const handleChange = (e: ChangeEvent<HTMLInputElement>) => { const selectedFiles = Array.from(e.target.files || []); setFiles(selectedFiles); onFilesSelected(selectedFiles); };
  const removeFile = (index: number) => { const updated = files.filter((_, i) => i !== index); setFiles(updated); onFilesSelected(updated); };

  return (
    <div className={cn("w-full", className)}>
      <div onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop} onClick={() => inputRef.current?.click()}
        className={cn("flex flex-col items-center justify-center w-full py-8 px-4 rounded-xl border-2 border-dashed cursor-pointer transition-colors", isDragging ? "border-brand bg-brand/5" : "border-glass-border-mid hover:border-brand/50 hover:bg-glass-faint")}>
        <Upload className={cn("h-8 w-8 mb-2", isDragging ? "text-brand" : "text-text-muted")} />
        <p className="text-sm text-text-muted"><span className="text-brand font-medium">Click to upload</span> or drag and drop</p>
        <p className="text-xs text-text-faint mt-1">{accept ? `${accept} • ` : ""}Max {maxSize}MB{multiple ? " per file" : ""}</p>
        <input ref={inputRef} type="file" accept={accept} multiple={multiple} onChange={handleChange} className="hidden" />
      </div>
      {files.length > 0 && (
        <div className="mt-3 space-y-2">
          {files.map((file, i) => (
            <div key={i} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-glass-panel border border-glass-border-mid">
              <FileText className="h-4 w-4 text-text-muted shrink-0" />
              <span className="flex-1 text-sm text-text truncate">{file.name}</span>
              <span className="text-xs text-text-faint">{(file.size / 1024).toFixed(1)} KB</span>
              <button onClick={() => removeFile(i)} className="text-text-faint hover:text-danger transition-colors"><X className="h-3.5 w-3.5" /></button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### 10.7 Date picker primitive

**New file:** `src/components/ui/DatePicker.tsx`
```tsx
"use client";
import { useState, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import { Calendar, ChevronLeft, ChevronRight } from "lucide-react";

interface DatePickerProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type" | "value" | "onChange"> {
  value?: string; onChange?: (date: string) => void; className?: string;
}

const DAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

export function DatePicker({ value, onChange, className, ...props }: DatePickerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [viewDate, setViewDate] = useState(() => (value ? new Date(value) : new Date()));
  const year = viewDate.getFullYear(); const month = viewDate.getMonth();
  const firstDay = new Date(year, month, 1).getDay(); const daysInMonth = new Date(year, month + 1, 0).getDate();

  const handleSelect = (day: number) => { const date = new Date(year, month, day); onChange?.(date.toISOString().split("T")[0]); setIsOpen(false); };
  const prevMonth = () => setViewDate(new Date(year, month - 1, 1));
  const nextMonth = () => setViewDate(new Date(year, month + 1, 1));

  return (
    <div className={cn("relative", className)}>
      <div className="flex items-center gap-2 w-full rounded-lg border border-glass-border bg-surface-1 px-3 py-2 cursor-pointer" onClick={() => setIsOpen(!isOpen)}>
        <Calendar className="h-4 w-4 text-text-muted" />
        <input type="text" readOnly value={value || ""} placeholder="Select date" className="flex-1 bg-transparent text-sm text-text outline-none cursor-pointer" {...props} />
      </div>
      {isOpen && (
        <div className="absolute top-full left-0 mt-1 z-popover w-72 rounded-xl border border-glass-border-mid bg-glass-strong shadow-xl p-3">
          <div className="flex items-center justify-between mb-3">
            <button onClick={prevMonth} className="p-1 rounded hover:bg-glass-panel text-text-muted hover:text-text"><ChevronLeft className="h-4 w-4" /></button>
            <span className="text-sm font-medium text-text">{MONTHS[month]} {year}</span>
            <button onClick={nextMonth} className="p-1 rounded hover:bg-glass-panel text-text-muted hover:text-text"><ChevronRight className="h-4 w-4" /></button>
          </div>
          <div className="grid grid-cols-7 gap-1 mb-2">{DAYS.map((d) => <div key={d} className="text-center text-xs text-text-muted py-1">{d}</div>)}</div>
          <div className="grid grid-cols-7 gap-1">
            {Array.from({ length: firstDay }).map((_, i) => <div key={`empty-${i}`} />)}
            {Array.from({ length: daysInMonth }).map((_, i) => {
              const day = i + 1; const isSelected = value === new Date(year, month, day).toISOString().split("T")[0];
              return <button key={day} onClick={() => handleSelect(day)} className={cn("h-7 w-7 rounded-full text-xs transition-colors", isSelected ? "bg-brand text-on-brand" : "text-text-muted hover:bg-glass-panel hover:text-text")}>{day}</button>;
            })}
          </div>
        </div>
      )}
    </div>
  );
}
```

### 10.8 Search with autocomplete

**New file:** `src/components/ui/SearchInput.tsx`
```tsx
"use client";
import { useState, useRef, useEffect, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import { Search, X } from "@/lib/icons";

interface SearchInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "onChange"> {
  value?: string; onChange?: (value: string) => void; onSearch?: (value: string) => void; suggestions?: string[]; className?: string;
}

export function SearchInput({ value, onChange, onSearch, suggestions = [], className, ...props }: SearchInputProps) {
  const [query, setQuery] = useState(value || "");
  const [isFocused, setIsFocused] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const ref = useRef<HTMLDivElement>(null);
  const filtered = suggestions.filter((s) => s.toLowerCase().includes(query.toLowerCase())).slice(0, 6);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setIsFocused(false); };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => { setQuery(e.target.value); onChange?.(e.target.value); setSelectedIndex(-1); };
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setSelectedIndex((i) => Math.min(i + 1, filtered.length - 1)); }
    if (e.key === "ArrowUp") { e.preventDefault(); setSelectedIndex((i) => Math.max(i - 1, -1)); }
    if (e.key === "Enter") { if (selectedIndex >= 0 && filtered[selectedIndex]) { setQuery(filtered[selectedIndex]); onChange?.(filtered[selectedIndex]); } onSearch?.(query); setIsFocused(false); }
    if (e.key === "Escape") setIsFocused(false);
  };
  const clear = () => { setQuery(""); onChange?.(""); };

  return (
    <div className={cn("relative", className)} ref={ref}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
        <input value={query} onChange={handleChange} onFocus={() => setIsFocused(true)} onKeyDown={handleKeyDown}
          className="w-full rounded-lg border border-glass-border bg-surface-1 pl-9 pr-8 py-2 text-sm text-text placeholder:text-text-faint focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand transition-colors" {...props} />
        {query && <button onClick={clear} className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text"><X className="h-3.5 w-3.5" /></button>}
      </div>
      {isFocused && filtered.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 z-dropdown rounded-xl border border-glass-border-mid bg-glass-strong shadow-xl overflow-hidden">
          {filtered.map((item, i) => (
            <button key={item} className={cn("w-full px-3 py-2 text-sm text-left transition-colors", i === selectedIndex ? "bg-glass-panel text-text" : "text-text-muted hover:bg-glass-faint")}
              onClick={() => { setQuery(item); onChange?.(item); setIsFocused(false); }} onMouseEnter={() => setSelectedIndex(i)}>
              {item}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
```

### 10.9 Responsive design patterns

**File:** `src/styles/globals.css` — append:
```css
/* -- Responsive utilities ---------------------------------------------------- */
@media (max-width: 640px) {
  .hide-mobile { display: none !important; }
  .show-mobile { display: block !important; }
  .mobile-full { width: 100% !important; }
  .mobile-stack { flex-direction: column !important; }
  .mobile-no-gap { gap: 0 !important; }
  .mobile-text-center { text-align: center !important; }
  .mobile-text-left { text-align: left !important; }
  .mobile-p-2 { padding: 0.5rem !important; }
  .mobile-p-4 { padding: 1rem !important; }
  .mobile-px-2 { padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
  .mobile-py-2 { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; }
}

@media (min-width: 641px) { .hide-desktop { display: none !important; } }

@media (pointer: coarse) {
  button, a, [role="button"] { min-height: 44px; min-width: 44px; }
}
```

### 10.10 Performance optimization

**File:** `src/styles/globals.css` — append:
```css
/* -- Performance optimizations ----------------------------------------------- */
.section-defer { content-visibility: auto; contain-intrinsic-size: 0 500px; }
.gpu-accelerated { transform: translateZ(0); will-change: transform; }
.fixed-gpu { transform: translateZ(0); backface-visibility: hidden; }
.contain-paint { contain: paint; }
.contain-layout { contain: layout style; }
```

### 10.11 Migration playbook

**New file:** `MIGRATION_PLAYBOOK.md`
```markdown
# ZOZI Design System — Migration Playbook

## Priority Order

### 1. Buttons (highest impact)
**Target:** 80+ files using raw `theme-btn-*` classes
**Approach:** Codemod + manual review
**Steps:**
1. Run `scripts/codemod-button.mjs` (to be created)
2. Review BannerCanvasEditor.tsx (40+ buttons)
3. Review admin panel pages
4. Review supplier panel pages
5. Review auth pages (login, register)

### 2. Modals (high impact)
**Target:** 20+ hand-rolled modals
**Approach:** Migrate per-PR, highest traffic first
**Steps:**
1. AuthRequiredModal.tsx
2. QuickViewModal.tsx
3. Admin panel modals
4. Supplier panel modals
5. Remaining modals

### 3. Forms (medium impact)
**Target:** All form-heavy pages
**Approach:** Incremental, page by page
**Steps:**
1. Replace raw inputs with `Input` + `FormGroup`
2. Add validation patterns
3. Add error states

### 4. Tables (medium impact)
**Target:** All data tables
**Approach:** Replace raw `<table>` with `Table` component
**Steps:**
1. Admin data tables
2. Supplier data tables
3. Logistics data tables

### 5. Navigation (low-medium impact)
**Target:** All tab/breadcrumb/pagination usages
**Approach:** Incremental
**Steps:**
1. Replace raw tabs with `Tabs` component
2. Add `Breadcrumbs` to panel pages
3. Replace raw pagination with `Pagination`

## Per-PR Checklist

- [ ] Component renders correctly in both themes
- [ ] Responsive on mobile (320px) and desktop (1440px)
- [ ] Keyboard accessible (Tab, Enter, Escape)
- [ ] Reduced-motion respected
- [ ] No console errors
- [ ] Visual QA passed
```

### 10.12 Component testing patterns

**New file:** `src/components/ui/__tests__/Button.test.tsx`
```tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { Button } from "../Button";

describe("Button", () => {
  it("renders with correct text", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText("Click me")).toBeInTheDocument();
  });

  it("calls onClick when clicked", () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click</Button>);
    fireEvent.click(screen.getByText("Click"));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("shows loading state", () => {
    render(<Button isLoading>Submit</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("applies variant classes correctly", () => {
    const { container } = render(<Button variant="primary">Primary</Button>);
    expect(container.firstChild).toHaveClass("theme-btn-primary");
  });

  it("is disabled when disabled prop is true", () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });
});
```

### 10.13 Update barrel export

**File:** `src/components/ui/index.ts` — add:
```ts
# Add to existing barrel:
export { Accordion, AccordionItem } from "./Accordion";
export { Divider } from "./Divider";
export { Avatar, AvatarGroup } from "./Avatar";
export { CommandPalette } from "./CommandPalette";
export { FileUpload } from "./FileUpload";
export { DatePicker } from "./DatePicker";
export { SearchInput } from "./SearchInput";
```

### 10.14 Validate Phase 10

```powershell
npx tsc --noEmit --skipLibCheck
npm run lint
npx jest
npx jest --testPathPattern "components/ui/__tests__"
```

---

## Complete File Change Summary (All 10 Phases)

| Phase | File | Action |
|-------|------|--------|
| 0 | `src/styles/globals.css` | Insert `@import "./tokens.css"` |
| 0 | `src/app/layout.tsx` | Insert `import "@/styles/tokens.css"` + `import "@/styles/glow.css"` |
| 0 | `src/styles/variables.css` | DELETE |
| 0 | `src/styles/comm.css` | RESTORE from HEAD |
| 0 | `src/styles/panel-modern.css` | RESTORE from HEAD |
| 0 | `src/styles/glow.css` | RESTORE from HEAD |
| 0 | `src/styles/tokens.css` | RESTORE from HEAD |
| 0 | `tailwind.config.js` | Map borderRadius + transitionDuration + add max-w-450 |
| 1 | `src/styles/globals.css` | Insert `--color-background` + undefined-class block + `--zozi-ext-*` + `bcu-*` keyframes |
| 1 | `src/styles/globals.css` | Replace focus-kill with focus-visible ring + reduced-motion media query |
| 1 | 4 component files | Fix `z-[200]` / `z-200` usages |
| 2 | `shared/src/theme.ts` | Extend `applyCssTheme` with status/glass vars |
| 2 | `src/styles/globals.css` | Delete flat gradient aliases + align radius/shadow tokens + motion tokens |
| 2 | `tailwind.config.js` | Add 3xs-5xs font sizes + named z-index scale + gradient-brand-to-* keys |
| 2 | `src/styles/globals.css` | Delete dead fadeIn/slideUp + insert `@keyframes scaleIn` |
| 3 | `src/components/ui/index.ts` | Barrel export all primitives |
| 3 | `src/components/ui/shared/Modal.tsx` | Add drawer variant + a11y props |
| 3 | `src/components/ToastSystem.tsx` | DELETE |
| 3 | `src/components/LoadingSkeleton.tsx` | DELETE (root duplicate) |
| 3 | 8 new files | Container, PageHeader, Section, Heading, Alert, StatusBadge, Spinner, Drawer |
| 4 | `src/app/layout.tsx` | Import `MotionConfig` + wrap app |
| 4 | `src/app/template.tsx` | Page transition wrapper |
| 4 | 2 new files | Reveal, Stagger |
| 5 | `src/styles/globals.css` | Entrance utilities + card hover lift + spring transitions + webkit backdrop-filter + hero gradient + view-transition |
| 5 | `src/styles/globals.css` | Delete `!important` panel overrides |
| 6 | 2 new files | codemod-fontsize.mjs, codemod-zindex.mjs |
| 7 | 5 new files | Table, StatCard, Progress, Tooltip, Popover |
| 8 | 10 new files | Tabs, Breadcrumbs, Pagination, Stepper, FormGroup, Input, Textarea, Select, Checkbox, Radio, Switch |
| 8 | 2 existing files | Extend LoadingSkeleton + EmptyState |
| 9 | 4 new files | ErrorState, Group, tokens.ts, Storybook config |
| 9 | `src/styles/globals.css` | Print styles |
| 9 | `src/components/ui/index.ts` | Update barrel with new exports |
| 10 | 8 new files | Accordion, Divider, Avatar, CommandPalette, FileUpload, DatePicker, SearchInput, Button.test |
| 10 | `src/components/ToastContainer.tsx` | Enhanced with queue + positioning |
| 10 | `src/styles/globals.css` | Responsive utilities + performance optimizations |
| 10 | `MIGRATION_PLAYBOOK.md` | Migration guide |
| 10 | `src/components/ui/index.ts` | Update barrel with Phase 10 exports |

---

## What we keep (do NOT change)

- Current lime/gold brand: `--color-brand: #32CD32`, `--color-accent: #FFD700`
- `globals.css` existing vocabulary (glass, theme-card, theme-panel, shimmer, seasonal-banner-*, etc.)
- `tailwind.config.js` `scaleIn`/`spring`/`expo-out`/`smooth` easing tokens
- Rich `BackgroundEffect.tsx` seasonal engine
- `BannerCanvasEditor.tsx` (legitimate canvas/SVG colors)
- Chart color palettes

## What we drop

- `src/styles/variables.css` (orphan, orange/purple, conflicts with brand)
- `src/components/ToastSystem.tsx` (dead code, imported nowhere)
- `src/components/LoadingSkeleton.tsx` (root duplicate — keep `ui/shared/LoadingSkeleton.tsx`)
- `globals.css:2004–2012` dead `fadeIn`/`slideUp` keyframes
- `globals.css:2255–2271` focus-kill block (replaced by Phase 1.5)
- `globals.css:908–976` `!important` panel overrides (replaced by component system)
- All raw `theme-btn-*` usages outside `ui/Button.tsx` (migrated in Phase 3)
- All raw `glass-panel` modal markup outside `ui/Modal.tsx` (migrated in Phase 3)
- All `text-[10px]…[7px]` arbitrarys (migrated in Phase 2.5 + codemod)

---

## Phase 11 — E-commerce specialized components

This final phase adds the specialized components needed for a complete e-commerce application.

### 11.1 Confirm dialog

**New file:** `src/components/ui/ConfirmDialog.tsx`
```tsx
"use client";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Info, HelpCircle, Trash2 } from "lucide-react";

type ConfirmVariant = "danger" | "warning" | "info" | "question";

interface ConfirmDialogProps {
  isOpen: boolean; onClose: () => void; onConfirm: () => void;
  title: string; message?: string; confirmLabel?: string; cancelLabel?: string;
  variant?: ConfirmVariant; isLoading?: boolean; className?: string;
}

const variantConfig: Record<ConfirmVariant, { icon: React.ComponentType<{ className?: string }>; iconColor: string; buttonClass: string }> = {
  danger: { icon: Trash2, iconColor: "text-danger", buttonClass: "bg-danger hover:bg-danger/90" },
  warning: { icon: AlertTriangle, iconColor: "text-warning", buttonClass: "bg-warning hover:bg-warning/90" },
  info: { icon: Info, iconColor: "text-info", buttonClass: "bg-info hover:bg-info/90" },
  question: { icon: HelpCircle, iconColor: "text-brand", buttonClass: "bg-brand hover:bg-brand-dark" },
};

export function ConfirmDialog({ isOpen, onClose, onConfirm, title, message, confirmLabel = "Confirm", cancelLabel = "Cancel", variant = "danger", isLoading = false, className }: ConfirmDialogProps) {
  const config = variantConfig[variant]; const Icon = config.icon;
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-modal theme-overlay" onClick={onClose} />
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} transition={{ duration: 0.15 }}
            className={cn("fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-modal w-full max-w-sm rounded-xl border border-glass-border-mid bg-glass-strong shadow-2xl p-6", className)} role="alertdialog" aria-modal="true">
            <div className="flex flex-col items-center text-center">
              <div className={cn("flex items-center justify-center w-12 h-12 rounded-full mb-4", variant === "danger" ? "bg-danger/10" : variant === "warning" ? "bg-warning/10" : variant === "info" ? "bg-info/10" : "bg-brand/10")}>
                <Icon className={cn("h-6 w-6", config.iconColor)} />
              </div>
              <h3 className="text-lg font-semibold text-text mb-2">{title}</h3>
              {message && <p className="text-sm text-text-muted mb-6">{message}</p>}
              <div className="flex items-center gap-3 w-full">
                <button onClick={onClose} disabled={isLoading} className="flex-1 px-4 py-2 rounded-lg border border-glass-border-mid text-text-muted text-sm font-medium hover:bg-glass-panel transition-colors disabled:opacity-50">{cancelLabel}</button>
                <button onClick={onConfirm} disabled={isLoading} className={cn("flex-1 px-4 py-2 rounded-lg text-white text-sm font-medium transition-colors disabled:opacity-50", config.buttonClass)}>{isLoading ? "Loading..." : confirmLabel}</button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
```

### 11.2 Notification center

**New file:** `src/components/ui/NotificationCenter.tsx`
```tsx
"use client";
import { useState, createContext, useContext, useCallback, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { Bell, Check, CheckCheck, X, Package, Truck, CreditCard, AlertCircle } from "lucide-react";

type NotificationType = "order" | "shipping" | "payment" | "alert" | "info";
interface Notification { id: string; type: NotificationType; title: string; message: string; time: string; read: boolean; }
interface NotificationContextValue { notifications: Notification[]; unreadCount: number; addNotification: (n: Omit<Notification, "id" | "read">) => void; markAsRead: (id: string) => void; markAllAsRead: () => void; removeNotification: (id: string) => void; }
const NotificationContext = createContext<NotificationContextValue | null>(null);
export function useNotifications() { const ctx = useContext(NotificationContext); if (!ctx) throw new Error("useNotifications must be used within NotificationProvider"); return ctx; }

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const addNotification = useCallback((n: Omit<Notification, "id" | "read">) => { setNotifications((prev) => [{ ...n, id: Date.now().toString(), read: false }, ...prev]); }, []);
  const markAsRead = useCallback((id: string) => { setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n))); }, []);
  const markAllAsRead = useCallback(() => { setNotifications((prev) => prev.map((n) => ({ ...n, read: true }))); }, []);
  const removeNotification = useCallback((id: string) => { setNotifications((prev) => prev.filter((n) => n.id !== id)); }, []);
  const unreadCount = notifications.filter((n) => !n.read).length;
  return <NotificationContext.Provider value={{ notifications, unreadCount, addNotification, markAsRead, markAllAsRead, removeNotification }}>{children}</NotificationContext.Provider>;
}

const typeIcons: Record<NotificationType, React.ComponentType<{ className?: string }>> = { order: Package, shipping: Truck, payment: CreditCard, alert: AlertCircle, info: Bell };
const typeColors: Record<NotificationType, string> = { order: "text-brand", shipping: "text-info", payment: "text-success", alert: "text-danger", info: "text-text-muted" };

interface NotificationCenterProps { isOpen: boolean; onClose: () => void; className?: string; }
export function NotificationCenter({ isOpen, onClose, className }: NotificationCenterProps) {
  const { notifications, unreadCount, markAsRead, markAllAsRead, removeNotification } = useNotifications();
  return (
    <AnimatePresence>
      {isOpen && (<>
        <div className="fixed inset-0 z-modal" onClick={onClose} />
        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} transition={{ duration: 0.2 }}
          className={cn("fixed top-0 right-0 z-modal h-full w-full max-w-sm border-l border-glass-border-mid bg-glass-strong shadow-2xl flex flex-col", className)}>
          <div className="flex items-center justify-between px-4 py-3 border-b border-glass-border-mid">
            <div className="flex items-center gap-2"><Bell className="h-4 w-4 text-text-muted" /><h2 className="text-sm font-semibold text-text">Notifications</h2>{unreadCount > 0 && <span className="px-1.5 py-0.5 text-xs font-bold text-on-brand bg-brand rounded-full">{unreadCount}</span>}</div>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && <button onClick={markAllAsRead} className="text-xs text-brand hover:text-brand-light transition-colors flex items-center gap-1"><CheckCheck className="h-3 w-3" /> Mark all read</button>}
              <button onClick={onClose} className="text-text-muted hover:text-text transition-colors"><X className="h-4 w-4" /></button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto">
            {notifications.length === 0 ? (<div className="flex flex-col items-center justify-center py-12 px-4 text-center"><Bell className="h-8 w-8 text-text-faint mb-2" /><p className="text-sm text-text-muted">No notifications yet</p></div>) : (
              <div className="divide-y divide-glass-border-soft">
                {notifications.map((n) => { const Icon = typeIcons[n.type]; return (
                  <div key={n.id} className={cn("flex items-start gap-3 px-4 py-3 transition-colors", !n.read && "bg-brand/5")} onClick={() => markAsRead(n.id)}>
                    <div className={cn("shrink-0 mt-0.5", typeColors[n.type])}><Icon className="h-4 w-4" /></div>
                    <div className="flex-1 min-w-0"><p className={cn("text-sm", !n.read ? "font-medium text-text" : "text-text-muted")}>{n.title}</p><p className="text-xs text-text-faint truncate">{n.message}</p><p className="text-xs text-text-faint mt-0.5">{n.time}</p></div>
                    <div className="flex items-center gap-1 shrink-0">{!n.read && <span className="h-2 w-2 rounded-full bg-brand" />}<button onClick={(e) => { e.stopPropagation(); removeNotification(n.id); }} className="text-text-faint hover:text-danger transition-colors"><X className="h-3 w-3" /></button></div>
                  </div>
                ); })}
              </div>
            )}
          </div>
        </motion.div>
      </>)}
    </AnimatePresence>
  );
}
```

### 11.3 Timeline

**New file:** `src/components/ui/Timeline.tsx`
```tsx
"use client";
import { cn } from "@/lib/utils";
import { Check } from "@/lib/icons";

type TimelineItemStatus = "completed" | "current" | "pending" | "cancelled";
interface TimelineItem { id: string; title: string; description?: string; time?: string; status: TimelineItemStatus; icon?: React.ReactNode; }
interface TimelineProps { items: TimelineItem[]; className?: string; }

const statusColors: Record<TimelineItemStatus, string> = { completed: "bg-brand text-on-brand", current: "bg-brand text-on-brand ring-4 ring-brand/20", pending: "bg-surface-2 text-text-muted border border-glass-border-mid", cancelled: "bg-danger text-white" };

export function Timeline({ items, className }: TimelineProps) {
  return (
    <div className={cn("relative", className)}>
      {items.map((item, i) => (
        <div key={item.id} className="flex gap-3 pb-6 last:pb-0">
          <div className="flex flex-col items-center">
            <div className={cn("flex items-center justify-center w-8 h-8 rounded-full shrink-0 text-xs font-bold", statusColors[item.status])}>{item.icon || (item.status === "completed" ? <Check className="h-4 w-4" /> : i + 1)}</div>
            {i < items.length - 1 && <div className={cn("w-0.5 flex-1 mt-1", item.status === "completed" ? "bg-brand" : "bg-surface-2")} />}
          </div>
          <div className="flex-1 pt-1">
            <p className={cn("text-sm font-medium", item.status === "pending" ? "text-text-muted" : "text-text")}>{item.title}</p>
            {item.description && <p className="text-xs text-text-faint mt-0.5">{item.description}</p>}
            {item.time && <p className="text-xs text-text-faint mt-0.5">{item.time}</p>}
          </div>
        </div>
      ))}
    </div>
  );
}
```

### 11.4 Rating/Stars

**New file:** `src/components/ui/Rating.tsx`
```tsx
"use client";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { Star } from "lucide-react";

interface RatingProps { value: number; max?: number; size?: "sm" | "md" | "lg"; interactive?: boolean; onChange?: (value: number) => void; showValue?: boolean; className?: string; }
const sizeClasses = { sm: "h-3.5 w-3.5", md: "h-5 w-5", lg: "h-6 w-6" };

export function Rating({ value, max = 5, size = "md", interactive = false, onChange, showValue = false, className }: RatingProps) {
  const [hoverValue, setHoverValue] = useState(0);
  const displayValue = hoverValue || value;
  return (
    <div className={cn("inline-flex items-center gap-1", className)}>
      <div className="flex items-center gap-0.5">
        {Array.from({ length: max }).map((_, i) => {
          const starValue = i + 1; const isFilled = starValue <= displayValue; const isHalf = !isFilled && starValue - 0.5 <= displayValue;
          return (<button key={i} type="button" disabled={!interactive} className={cn("transition-colors", interactive && "cursor-pointer hover:scale-110", !interactive && "cursor-default")}
            onClick={() => interactive && onChange?.(starValue)} onMouseEnter={() => interactive && setHoverValue(starValue)} onMouseLeave={() => interactive && setHoverValue(0)}>
            <Star className={cn(sizeClasses[size], isFilled ? "fill-warning text-warning" : isHalf ? "fill-warning/50 text-warning" : "text-text-faint")} />
          </button>);
        })}
      </div>
      {showValue && <span className="text-sm font-medium text-text ml-1">{value.toFixed(1)}</span>}
    </div>
  );
}
```

### 11.5 Image Carousel/Gallery

**New file:** `src/components/ui/Carousel.tsx`
```tsx
"use client";
import { useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { ChevronLeft, ChevronRight } from "@/lib/icons";
import { motion, AnimatePresence } from "framer-motion";

interface CarouselProps { children: ReactNode[]; showDots?: boolean; showArrows?: boolean; className?: string; }
interface ImageGalleryProps { images: string[]; thumbnailsPerRow?: number; className?: string; }

export function Carousel({ children, showDots = true, showArrows = true, className }: CarouselProps) {
  const [current, setCurrent] = useState(0); const total = children.length;
  const next = () => setCurrent((c) => (c + 1) % total); const prev = () => setCurrent((c) => (c - 1 + total) % total);
  return (
    <div className={cn("relative w-full overflow-hidden rounded-xl", className)}>
      <div className="relative aspect-video"><AnimatePresence mode="wait"><motion.div key={current} initial={{ opacity: 0, x: 50 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -50 }} transition={{ duration: 0.3 }} className="absolute inset-0">{children[current]}</motion.div></AnimatePresence></div>
      {showArrows && (<><button onClick={prev} className="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/50 text-white flex items-center justify-center hover:bg-black/70"><ChevronLeft className="h-4 w-4" /></button><button onClick={next} className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/50 text-white flex items-center justify-center hover:bg-black/70"><ChevronRight className="h-4 w-4" /></button></>)}
      {showDots && (<div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex items-center gap-1.5">{Array.from({ length: total }).map((_, i) => <button key={i} onClick={() => setCurrent(i)} className={cn("w-2 h-2 rounded-full transition-all", i === current ? "bg-white w-4" : "bg-white/50 hover:bg-white/70")} />)}</div>)}
    </div>
  );
}

export function ImageGallery({ images, thumbnailsPerRow = 4, className }: ImageGalleryProps) {
  const [selected, setSelected] = useState(0);
  return (
    <div className={cn("space-y-3", className)}>
      <div className="relative aspect-square overflow-hidden rounded-xl border border-glass-border-mid"><img src={images[selected]} alt={`Product ${selected + 1}`} className="h-full w-full object-cover" /></div>
      <div className={cn("grid gap-2", `grid-cols-${thumbnailsPerRow}`)}>{images.map((img, i) => <button key={i} onClick={() => setSelected(i)} className={cn("aspect-square overflow-hidden rounded-lg border-2 transition-all", i === selected ? "border-brand" : "border-transparent hover:border-glass-border-mid")}><img src={img} alt={`Thumbnail ${i + 1}`} className="h-full w-full object-cover" /></button>)}</div>
    </div>
  );
}
```

### 11.6 Infinite scroll

**New file:** `src/components/ui/InfiniteScroll.tsx`
```tsx
"use client";
import { useEffect, useRef, type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface InfiniteScrollProps { children: ReactNode; hasMore: boolean; isLoading: boolean; onLoadMore: () => void; threshold?: number; loader?: ReactNode; className?: string; }

export function InfiniteScroll({ children, hasMore, isLoading, onLoadMore, threshold = 0.8, loader, className }: InfiniteScrollProps) {
  const sentinelRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const sentinel = sentinelRef.current; if (!sentinel) return;
    const observer = new IntersectionObserver((entries) => { if (entries[0].isIntersecting && hasMore && !isLoading) onLoadMore(); }, { threshold });
    observer.observe(sentinel); return () => observer.disconnect();
  }, [hasMore, isLoading, onLoadMore, threshold]);
  return (<div className={cn("w-full", className)}>{children}<div ref={sentinelRef} className="w-full py-4 flex justify-center">{isLoading && (loader || <div className="flex items-center gap-2 text-sm text-text-muted"><div className="h-4 w-4 border-2 border-brand border-t-transparent rounded-full animate-spin" /> Loading more...</div>)}{!hasMore && <p className="text-sm text-text-faint">No more items</p>}</div></div>);
}
```

### 11.7 Multi-step wizard

**New file:** `src/components/ui/Wizard.tsx`
```tsx
"use client";
import { useState, createContext, useContext, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Check } from "@/lib/icons";

interface WizardContextValue { currentStep: number; totalSteps: number; next: () => void; prev: () => void; goTo: (step: number) => void; }
const WizardContext = createContext<WizardContextValue | null>(null);
export function useWizard() { const ctx = useContext(WizardContext); if (!ctx) throw new Error("useWizard must be used within Wizard"); return ctx; }

interface WizardProps { children: ReactNode; onComplete: () => void; className?: string; }
export function Wizard({ children, onComplete, className }: WizardProps) {
  const childArray = Array.isArray(children) ? children : [children]; const [currentStep, setCurrentStep] = useState(0); const totalSteps = childArray.length;
  const next = () => { if (currentStep < totalSteps - 1) setCurrentStep((s) => s + 1); else onComplete(); };
  const prev = () => setCurrentStep((s) => Math.max(0, s - 1)); const goTo = (step: number) => setCurrentStep(step);
  return <WizardContext.Provider value={{ currentStep, totalSteps, next, prev, goTo }}><div className={cn("w-full", className)}>{childArray[currentStep]}</div></WizardContext.Provider>;
}

export function WizardSteps({ children, className }: { children: ReactNode; className?: string }) {
  const { currentStep, totalSteps } = useWizard(); const childArray = Array.isArray(children) ? children : [children];
  return (<div className={cn("flex items-center gap-2 mb-6", className)}>{childArray.map((_, i) => (<div key={i} className="flex items-center gap-2 flex-1"><div className={cn("flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold shrink-0", i < currentStep ? "bg-brand text-on-brand" : i === currentStep ? "bg-brand text-on-brand ring-4 ring-brand/20" : "bg-surface-2 text-text-muted")}>{i < currentStep ? <Check className="h-3.5 w-3.5" /> : i + 1}</div>{i < totalSteps - 1 && <div className={cn("flex-1 h-0.5 rounded", i < currentStep ? "bg-brand" : "bg-surface-2")} />}</div>))}</div>);
}

export function WizardContent({ children, step }: { children: ReactNode; step: number }) { const { currentStep } = useWizard(); if (currentStep !== step) return null; return <div>{children}</div>; }

export function WizardNavigation({ onNext, onPrev, nextLabel = "Next", prevLabel = "Back", className }: { onNext?: () => void; onPrev?: () => void; nextLabel?: string; prevLabel?: string; className?: string; }) {
  const { next, prev, currentStep } = useWizard();
  return (<div className={cn("flex items-center justify-between mt-6 pt-4 border-t border-glass-border-mid", className)}>{currentStep > 0 ? <button onClick={onPrev || prev} className="px-4 py-2 rounded-lg border border-glass-border-mid text-text-muted text-sm font-medium hover:bg-glass-panel transition-colors">{prevLabel}</button> : <div />}<button onClick={onNext || next} className="px-4 py-2 rounded-lg bg-brand text-on-brand text-sm font-medium hover:bg-brand-dark transition-colors">{nextLabel}</button></div>);
}
```

### 11.8 Tag/Chip input

**New file:** `src/components/ui/TagInput.tsx`
```tsx
"use client";
import { useState, type KeyboardEvent } from "react";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";

interface TagInputProps { value: string[]; onChange: (tags: string[]) => void; placeholder?: string; maxTags?: number; className?: string; }

export function TagInput({ value, onChange, placeholder = "Type and press enter...", maxTags, className }: TagInputProps) {
  const [input, setInput] = useState("");
  const addTag = (tag: string) => { const trimmed = tag.trim(); if (trimmed && !value.includes(trimmed) && (!maxTags || value.length < maxTags)) onChange([...value, trimmed]); setInput(""); };
  const removeTag = (tag: string) => { onChange(value.filter((t) => t !== tag)); };
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => { if (e.key === "Enter" || e.key === ",") { e.preventDefault(); addTag(input); } if (e.key === "Backspace" && !input && value.length > 0) removeTag(value[value.length - 1]); };
  return (
    <div className={cn("flex flex-wrap items-center gap-1.5 w-full rounded-lg border border-glass-border bg-surface-1 px-2 py-1.5 focus-within:ring-2 focus-within:ring-brand/30 focus-within:border-brand transition-colors", className)}>
      {value.map((tag) => (<span key={tag} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-brand/10 text-brand text-xs font-medium">{tag}<button onClick={() => removeTag(tag)} className="hover:text-brand-dark transition-colors"><X className="h-3 w-3" /></button></span>))}
      {(!maxTags || value.length < maxTags) && (<input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown} onBlur={() => input && addTag(input)} placeholder={value.length === 0 ? placeholder : ""} className="flex-1 min-w-[120px] bg-transparent text-sm text-text outline-none py-0.5" />)}
    </div>
  );
}
```

### 11.9 Skeleton page layouts

**New file:** `src/components/ui/SkeletonPage.tsx`
```tsx
"use client";
import { cn } from "@/lib/utils";

interface SkeletonPageProps { type?: "dashboard" | "list" | "detail" | "form"; className?: string; }

export function SkeletonPage({ type = "dashboard", className }: SkeletonPageProps) {
  switch (type) {
    case "dashboard": return (<div className={cn("space-y-6", className)}><div className="flex items-center justify-between"><div className="h-8 w-48 rounded-lg bg-glass-mid animate-pulse" /><div className="h-10 w-32 rounded-lg bg-glass-mid animate-pulse" /></div><div className="grid grid-cols-1 md:grid-cols-4 gap-4">{Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-24 rounded-xl bg-glass-mid animate-pulse" />)}</div><div className="grid grid-cols-1 lg:grid-cols-3 gap-6"><div className="lg:col-span-2 h-80 rounded-xl bg-glass-mid animate-pulse" /><div className="h-80 rounded-xl bg-glass-mid animate-pulse" /></div></div>);
    case "list": return (<div className={cn("space-y-4", className)}><div className="flex items-center justify-between"><div className="h-8 w-48 rounded-lg bg-glass-mid animate-pulse" /><div className="h-10 w-32 rounded-lg bg-glass-mid animate-pulse" /></div><div className="h-10 w-full rounded-lg bg-glass-mid animate-pulse" /><div className="space-y-2">{Array.from({ length: 8 }).map((_, i) => <div key={i} className="h-14 w-full rounded-lg bg-glass-mid animate-pulse" />)}</div></div>);
    case "detail": return (<div className={cn("space-y-6", className)}><div className="h-8 w-64 rounded-lg bg-glass-mid animate-pulse" /><div className="grid grid-cols-1 lg:grid-cols-2 gap-6"><div className="aspect-square rounded-xl bg-glass-mid animate-pulse" /><div className="space-y-4"><div className="h-6 w-3/4 rounded bg-glass-mid animate-pulse" /><div className="h-4 w-1/2 rounded bg-glass-mid animate-pulse" /><div className="h-4 w-2/3 rounded bg-glass-mid animate-pulse" /><div className="h-24 w-full rounded-lg bg-glass-mid animate-pulse" /><div className="h-12 w-full rounded-lg bg-glass-mid animate-pulse" /></div></div></div>);
    case "form": return (<div className={cn("max-w-2xl space-y-6", className)}><div className="h-8 w-48 rounded-lg bg-glass-mid animate-pulse" /><div className="space-y-4">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="space-y-1.5"><div className="h-4 w-24 rounded bg-glass-mid animate-pulse" /><div className="h-10 w-full rounded-lg bg-glass-mid animate-pulse" /></div>)}<div className="h-10 w-32 rounded-lg bg-glass-mid animate-pulse" /></div></div>);
  }
}
```

### 11.10 Chart/Graph wrapper

**New file:** `src/components/ui/Chart.tsx`
```tsx
"use client";
import { cn } from "@/lib/utils";

interface ChartContainerProps { children: React.ReactNode; title?: string; subtitle?: string; action?: React.ReactNode; height?: number; className?: string; }
interface ChartTooltipProps { active?: boolean; payload?: Array<{ name: string; value: number; color: string }>; label?: string; }
interface ChartLegendProps { items: Array<{ label: string; color: string }>; className?: string; }

export function ChartContainer({ children, title, subtitle, action, height = 300, className }: ChartContainerProps) {
  return (<div className={cn("glass-panel rounded-xl border p-4", className)}>{(title || action) && (<div className="flex items-start justify-between mb-4"><div>{title && <h3 className="text-sm font-semibold text-text">{title}</h3>}{subtitle && <p className="text-xs text-text-muted mt-0.5">{subtitle}</p>}</div>{action && <div className="shrink-0">{action}</div>}</div>)}<div style={{ height }}>{children}</div></div>);
}

export function ChartTooltip({ active, payload, label }: ChartTooltipProps) {
  if (!active || !payload?.length) return null;
  return (<div className="glass-strong rounded-lg border border-glass-border-mid shadow-lg p-2 text-xs">{label && <p className="font-medium text-text mb-1">{label}</p>}{payload.map((entry, i) => (<div key={i} className="flex items-center gap-2 text-text-muted"><span className="h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} /><span>{entry.name}: <span className="font-medium text-text">{entry.value}</span></span></div>))}</div>);
}

export function ChartLegend({ items, className }: ChartLegendProps) {
  return (<div className={cn("flex flex-wrap items-center gap-4", className)}>{items.map((item, i) => (<div key={i} className="flex items-center gap-1.5 text-xs text-text-muted"><span className="h-2.5 w-2.5 rounded-full shrink-0" style={{ backgroundColor: item.color }} />{item.label}</div>))}</div>);
}
```

### 11.11 Update barrel export

**File:** `src/components/ui/index.ts` — add:
```ts
# Add to existing barrel:
export { ConfirmDialog } from "./ConfirmDialog";
export { NotificationProvider, NotificationCenter, useNotifications } from "./NotificationCenter";
export { Timeline } from "./Timeline";
export { Rating } from "./Rating";
export { Carousel, ImageGallery } from "./Carousel";
export { InfiniteScroll } from "./InfiniteScroll";
export { Wizard, WizardSteps, WizardContent, WizardNavigation, useWizard } from "./Wizard";
export { TagInput } from "./TagInput";
export { SkeletonPage } from "./SkeletonPage";
export { ChartContainer, ChartTooltip, ChartLegend } from "./Chart";
```

### 11.12 Validate Phase 11

```powershell
npx tsc --noEmit --skipLibCheck
npm run lint
npx jest
npx jest --testPathPattern "components/ui/__tests__"
```

---

## Complete File Change Summary (All 11 Phases)

| Phase | File | Action |
|-------|------|--------|
| 0 | `src/styles/globals.css` | Insert `@import "./tokens.css"` |
| 0 | `src/app/layout.tsx` | Insert `import "@/styles/tokens.css"` + `import "@/styles/glow.css"` |
| 0 | `src/styles/variables.css` | DELETE |
| 0 | `src/styles/comm.css` | RESTORE from HEAD |
| 0 | `src/styles/panel-modern.css` | RESTORE from HEAD |
| 0 | `src/styles/glow.css` | RESTORE from HEAD |
| 0 | `src/styles/tokens.css` | RESTORE from HEAD |
| 0 | `tailwind.config.js` | Map borderRadius + transitionDuration + add max-w-450 |
| 1 | `src/styles/globals.css` | Insert `--color-background` + undefined-class block + `--zozi-ext-*` + `bcu-*` keyframes |
| 1 | `src/styles/globals.css` | Replace focus-kill with focus-visible ring + reduced-motion media query |
| 1 | 4 component files | Fix `z-[200]` / `z-200` usages |
| 2 | `shared/src/theme.ts` | Extend `applyCssTheme` with status/glass vars |
| 2 | `src/styles/globals.css` | Delete flat gradient aliases + align radius/shadow tokens + motion tokens |
| 2 | `tailwind.config.js` | Add 3xs-5xs font sizes + named z-index scale + gradient-brand-to-* keys |
| 2 | `src/styles/globals.css` | Delete dead fadeIn/slideUp + insert `@keyframes scaleIn` |
| 3 | `src/components/ui/index.ts` | Barrel export all primitives |
| 3 | `src/components/ui/shared/Modal.tsx` | Add drawer variant + a11y props |
| 3 | `src/components/ToastSystem.tsx` | DELETE |
| 3 | `src/components/LoadingSkeleton.tsx` | DELETE (root duplicate) |
| 3 | 8 new files | Container, PageHeader, Section, Heading, Alert, StatusBadge, Spinner, Drawer |
| 4 | `src/app/layout.tsx` | Import `MotionConfig` + wrap app |
| 4 | `src/app/template.tsx` | Page transition wrapper |
| 4 | 2 new files | Reveal, Stagger |
| 5 | `src/styles/globals.css` | Entrance utilities + card hover lift + spring transitions + webkit backdrop-filter + hero gradient + view-transition |
| 5 | `src/styles/globals.css` | Delete `!important` panel overrides |
| 6 | 2 new files | codemod-fontsize.mjs, codemod-zindex.mjs |
| 7 | 5 new files | Table, StatCard, Progress, Tooltip, Popover |
| 8 | 10 new files | Tabs, Breadcrumbs, Pagination, Stepper, FormGroup, Input, Textarea, Select, Checkbox, Radio, Switch |
| 8 | 2 existing files | Extend LoadingSkeleton + EmptyState |
| 9 | 4 new files | ErrorState, Group, tokens.ts, Storybook config |
| 9 | `src/styles/globals.css` | Print styles |
| 9 | `src/components/ui/index.ts` | Update barrel with new exports |
| 10 | 8 new files | Accordion, Divider, Avatar, CommandPalette, FileUpload, DatePicker, SearchInput, Button.test |
| 10 | `src/components/ToastContainer.tsx` | Enhanced with queue + positioning |
| 10 | `src/styles/globals.css` | Responsive utilities + performance optimizations |
| 10 | `MIGRATION_PLAYBOOK.md` | Migration guide |
| 10 | `src/components/ui/index.ts` | Update barrel with Phase 10 exports |
| 11 | 10 new files | ConfirmDialog, NotificationCenter, Timeline, Rating, Carousel, InfiniteScroll, Wizard, TagInput, SkeletonPage, Chart |
| 11 | `src/components/ui/index.ts` | Update barrel with Phase 11 exports |

---

## What we keep (do NOT change)

- Current lime/gold brand: `--color-brand: #32CD32`, `--color-accent: #FFD700`
- `globals.css` existing vocabulary (glass, theme-card, theme-panel, shimmer, seasonal-banner-*, etc.)
- `tailwind.config.js` `scaleIn`/`spring`/`expo-out`/`smooth` easing tokens
- Rich `BackgroundEffect.tsx` seasonal engine
- `BannerCanvasEditor.tsx` (legitimate canvas/SVG colors)
- Chart color palettes

## What we drop

- `src/styles/variables.css` (orphan, orange/purple, conflicts with brand)
- `src/components/ToastSystem.tsx` (dead code, imported nowhere)
- `src/components/LoadingSkeleton.tsx` (root duplicate — keep `ui/shared/LoadingSkeleton.tsx`)
- `globals.css:2004–2012` dead `fadeIn`/`slideUp` keyframes
- `globals.css:2255–2271` focus-kill block (replaced by Phase 1.5)
- `globals.css:908–976` `!important` panel overrides (replaced by component system)
- All raw `theme-btn-*` usages outside `ui/Button.tsx` (migrated in Phase 3)
- All raw `glass-panel` modal markup outside `ui/Modal.tsx` (migrated in Phase 3)
- All `text-[10px]…[7px]` arbitrarys (migrated in Phase 2.5 + codemod)

---

## Phase 12 — Edge-case components (remaining 2%)

This phase adds the remaining edge-case components that are needed for specific scenarios but not part of the core system. These components complete the design system to 100%.

### 12.1 Color picker primitive

**New file:** `src/components/ui/ColorPicker.tsx`
```tsx
"use client";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

interface ColorPickerProps {
  value?: string;
  onChange?: (color: string) => void;
  colors?: string[];
  className?: string;
}

const defaultColors = [
  "#ef4444", "#f97316", "#eab308", "#22c55e", "#14b8a6",
  "#3b82f6", "#6366f1", "#a855f7", "#ec4899", "#f43f5e",
  "#0f172a", "#334155", "#64748b", "#94a3b8", "#cbd5e1",
];

export function ColorPicker({ value, onChange, colors = defaultColors, className }: ColorPickerProps) {
  return (
    <div className={cn("flex flex-wrap gap-2", className)}>
      {colors.map((color) => (
        <button
          key={color}
          onClick={() => onChange?.(color)}
          className={cn("w-7 h-7 rounded-full border-2 transition-all flex items-center justify-center", value === color ? "border-text scale-110" : "border-transparent hover:scale-110")}
          style={{ backgroundColor: color }}
          aria-label={`Select color ${color}`}
        >
          {value === color && <Check className="h-3 w-3 text-white drop-shadow" />}
        </button>
      ))}
    </div>
  );
}
```

### 12.2 Rich text editor primitive

**New file:** `src/components/ui/RichTextEditor.tsx`
```tsx
"use client";
import { useState, useCallback, type KeyboardEvent } from "react";
import { cn } from "@/lib/utils";
import { Bold, Italic, Underline, List, ListOrdered, Link, Image, Undo, Redo, Code } from "lucide-react";

interface RichTextEditorProps {
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  minHeight?: number;
  className?: string;
}

interface ToolbarButton {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  command: string;
  value?: string;
}

const toolbarButtons: ToolbarButton[] = [
  { icon: Bold, label: "Bold", command: "bold" },
  { icon: Italic, label: "Italic", command: "italic" },
  { icon: Underline, label: "Underline", command: "underline" },
  { icon: Code, label: "Code", command: "code" },
  { icon: List, label: "Bullet List", command: "insertUnorderedList" },
  { icon: ListOrdered, label: "Numbered List", command: "insertOrderedList" },
  { icon: Link, label: "Link", command: "createLink" },
  { icon: Image, label: "Image", command: "insertImage" },
  { icon: Undo, label: "Undo", command: "undo" },
  { icon: Redo, label: "Redo", command: "redo" },
];

export function RichTextEditor({ value = "", onChange, placeholder = "Write something...", minHeight = 150, className }: RichTextEditorProps) {
  const [isActive, setIsActive] = useState<Record<string, boolean>>({});

  const execCommand = useCallback((command: string, value?: string) => {
    document.execCommand(command, false, value);
    setIsActive((prev) => ({ ...prev, [command]: document.queryCommandState(command) }));
  }, []);

  const handleInput = useCallback((e: React.FormEvent<HTMLDivElement>) => {
    onChange?.(e.currentTarget.innerHTML);
  }, [onChange]);

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === "Tab") {
      e.preventDefault();
      document.execCommand("insertText", false, "  ");
    }
  };

  return (
    <div className={cn("w-full rounded-lg border border-glass-border-mid overflow-hidden focus-within:ring-2 focus-within:ring-brand/30 focus-within:border-brand transition-colors", className)}>
      <div className="flex flex-wrap items-center gap-0.5 px-2 py-1.5 border-b border-glass-border-mid bg-glass-panel">
        {toolbarButtons.map((btn) => {
          const Icon = btn.icon;
          return (
            <button
              key={btn.command}
              type="button"
              onMouseDown={(e) => { e.preventDefault(); execCommand(btn.command); }}
              className={cn("p-1.5 rounded transition-colors", isActive[btn.command] ? "bg-brand/20 text-brand" : "text-text-muted hover:text-text hover:bg-glass-faint")}
              title={btn.label}
              aria-label={btn.label}
            >
              <Icon className="h-3.5 w-3.5" />
            </button>
          );
        })}
      </div>
      <div
        contentEditable
        onInput={handleInput}
        onKeyDown={handleKeyDown}
        onFocus={() => toolbarButtons.forEach((btn) => setIsActive((prev) => ({ ...prev, [btn.command]: document.queryCommandState(btn.command) })))}
        dangerouslySetInnerHTML={{ __html: value }}
        data-placeholder={placeholder}
        className={cn("w-full px-3 py-2 text-sm text-text outline-none overflow-y-auto prose prose-sm max-w-none", "[&:empty]:before:content-[attr(data-placeholder)] [&:empty]:before:text-text-faint")}
        style={{ minHeight }}
      />
    </div>
  );
}
```

### 12.3 Tag/Chip display primitive

**New file:** `src/components/ui/Tag.tsx`
```tsx
"use client";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";

type TagSize = "sm" | "md" | "lg";
type TagVariant = "default" | "primary" | "success" | "warning" | "danger" | "info" | "outline";

interface TagProps {
  children: React.ReactNode;
  size?: TagSize;
  variant?: TagVariant;
  removable?: boolean;
  onRemove?: () => void;
  icon?: React.ReactNode;
  className?: string;
}

const sizeClasses: Record<TagSize, string> = {
  sm: "px-1.5 py-0 text-xs", md: "px-2 py-0.5 text-xs", lg: "px-2.5 py-1 text-sm",
};

const variantClasses: Record<TagVariant, string> = {
  default: "bg-glass-panel text-text border-glass-border-mid",
  primary: "bg-brand/10 text-brand border-brand/20",
  success: "bg-success/10 text-success border-success/20",
  warning: "bg-warning/10 text-warning border-warning/20",
  danger: "bg-danger/10 text-danger border-danger/20",
  info: "bg-info/10 text-info border-info/20",
  outline: "bg-transparent text-text border-glass-border-mid",
};

export function Tag({ children, size = "md", variant = "default", removable = false, onRemove, icon, className }: TagProps) {
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-md border font-medium", sizeClasses[size], variantClasses[variant], className)}>
      {icon && <span className="shrink-0">{icon}</span>}
      {children}
      {removable && (
        <button onClick={onRemove} className="shrink-0 hover:opacity-70 transition-opacity" aria-label="Remove tag">
          <X className="h-3 w-3" />
        </button>
      )}
    </span>
  );
}
```

### 12.4 Tree view primitive

**New file:** `src/components/ui/Tree.tsx`
```tsx
"use client";
import { useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { ChevronRight, ChevronDown, Folder, FolderOpen, File } from "lucide-react";

interface TreeNode {
  id: string;
  label: string;
  icon?: ReactNode;
  children?: TreeNode[];
  selectable?: boolean;
}

interface TreeProps {
  nodes: TreeNode[];
  selectedId?: string;
  onSelect?: (id: string) => void;
  defaultExpanded?: string[];
  className?: string;
}

export function Tree({ nodes, selectedId, onSelect, defaultExpanded = [], className }: TreeProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set(defaultExpanded));

  const toggle = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const renderNode = (node: TreeNode, depth: number = 0) => {
    const hasChildren = node.children && node.children.length > 0;
    const isExpanded = expanded.has(node.id);
    const isSelected = selectedId === node.id;

    return (
      <div key={node.id}>
        <div
          className={cn("flex items-center gap-1.5 px-2 py-1 rounded-lg text-sm cursor-pointer transition-colors", isSelected ? "bg-brand/10 text-brand" : "text-text-muted hover:bg-glass-faint hover:text-text")}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
          onClick={() => { if (hasChildren) toggle(node.id); if (node.selectable !== false) onSelect?.(node.id); }}
        >
          {hasChildren ? (isExpanded ? <ChevronDown className="h-3.5 w-3.5 shrink-0" /> : <ChevronRight className="h-3.5 w-3.5 shrink-0" />) : <span className="w-3.5 shrink-0" />}
          {node.icon || (hasChildren ? (isExpanded ? <FolderOpen className="h-4 w-4 shrink-0 text-brand" /> : <Folder className="h-4 w-4 shrink-0 text-brand" />) : <File className="h-4 w-4 shrink-0 text-text-faint" />)}
          <span className="truncate">{node.label}</span>
        </div>
        {hasChildren && isExpanded && node.children!.map((child) => renderNode(child, depth + 1))}
      </div>
    );
  };

  return <div className={cn("w-full", className)}>{nodes.map((node) => renderNode(node))}</div>;
}
```

### 12.5 Code/Syntax display primitive

**New file:** `src/components/ui/CodeBlock.tsx`
```tsx
"use client";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { Copy, Check } from "lucide-react";

interface CodeBlockProps {
  code: string;
  language?: string;
  showLineNumbers?: boolean;
  copyable?: boolean;
  className?: string;
}

export function CodeBlock({ code, language, showLineNumbers = false, copyable = true, className }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);
  const lines = code.split("\n");

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={cn("relative w-full rounded-lg border border-glass-border-mid overflow-hidden", className)}>
      {(language || copyable) && (
        <div className="flex items-center justify-between px-3 py-2 border-b border-glass-border-mid bg-glass-panel">
          {language && <span className="text-xs font-medium text-text-muted uppercase">{language}</span>}
          {copyable && (
            <button onClick={handleCopy} className="flex items-center gap-1 text-xs text-text-muted hover:text-text transition-colors">
              {copied ? <><Check className="h-3 w-3 text-success" /> Copied!</> : <><Copy className="h-3 w-3" /> Copy</>}
            </button>
          )}
        </div>
      )}
      <div className="overflow-x-auto">
        <pre className="p-3 text-xs text-text font-mono leading-relaxed">
          {lines.map((line, i) => (
            <div key={i} className="flex">
              {showLineNumbers && <span className="inline-block w-8 text-right mr-3 text-text-faint select-none shrink-0">{i + 1}</span>}
              <span className="flex-1">{line || " "}</span>
            </div>
          ))}
        </pre>
      </div>
    </div>
  );
}
```

### 12.6 Mention/Tag people primitive

**New file:** `src/components/ui/MentionInput.tsx`
```tsx
"use client";
import { useState, useRef, useEffect, type KeyboardEvent } from "react";
import { cn } from "@/lib/utils";

interface Mention {
  id: string;
  name: string;
  avatar?: string;
}

interface MentionInputProps {
  value: string;
  onChange: (value: string) => void;
  mentions: Mention[];
  onMentionSelect?: (mention: Mention) => void;
  placeholder?: string;
  className?: string;
}

export function MentionInput({ value, onChange, mentions, onMentionSelect, placeholder = "Type @ to mention...", className }: MentionInputProps) {
  const [showMentions, setShowMentions] = useState(false);
  const [query, setQuery] = useState("");
  const [cursorPosition, setCursorPosition] = useState(0);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const filteredMentions = mentions.filter((m) => m.name.toLowerCase().includes(query.toLowerCase()));

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (inputRef.current && !inputRef.current.parentElement?.contains(e.target as Node)) setShowMentions(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    const cursor = e.target.selectionStart;
    onChange(newValue);
    setCursorPosition(cursor);

    const textBeforeCursor = newValue.slice(0, cursor);
    const lastAtIndex = textBeforeCursor.lastIndexOf("@");

    if (lastAtIndex !== -1 && cursor - lastAtIndex > 0) {
      const queryText = textBeforeCursor.slice(lastAtIndex + 1);
      if (!queryText.includes(" ")) {
        setQuery(queryText);
        setShowMentions(true);
        return;
      }
    }
    setShowMentions(false);
  };

  const selectMention = (mention: Mention) => {
    const textBeforeCursor = value.slice(0, cursorPosition);
    const lastAtIndex = textBeforeCursor.lastIndexOf("@");
    const newValue = value.slice(0, lastAtIndex) + `@${mention.name} ` + value.slice(cursorPosition);
    onChange(newValue);
    setShowMentions(false);
    onMentionSelect?.(mention);
  };

  return (
    <div className={cn("relative", className)}>
      <textarea
        ref={inputRef}
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        className="w-full rounded-lg border border-glass-border bg-surface-1 px-3 py-2 text-sm text-text placeholder:text-text-faint resize-y min-h-[80px] focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand transition-colors"
      />
      {showMentions && filteredMentions.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 z-dropdown max-h-48 overflow-y-auto rounded-xl border border-glass-border-mid bg-glass-strong shadow-xl">
          {filteredMentions.map((mention) => (
            <button key={mention.id} className="flex items-center gap-2 w-full px-3 py-2 text-sm text-left text-text-muted hover:bg-glass-panel hover:text-text transition-colors" onClick={() => selectMention(mention)}>
              {mention.avatar ? <img src={mention.avatar} alt="" className="h-5 w-5 rounded-full" /> : <span className="h-5 w-5 rounded-full bg-brand/20 text-brand text-xs flex items-center justify-center font-medium">{mention.name[0]}</span>}
              <span>{mention.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
```

### 12.7 Back to top button

**New file:** `src/components/ui/BackToTop.tsx`
```tsx
"use client";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { ArrowUp } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface BackToTopProps {
  threshold?: number;
  className?: string;
}

export function BackToTop({ threshold = 300, className }: BackToTopProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsVisible(window.scrollY > threshold);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [threshold]);

  const scrollToTop = () => window.scrollTo({ top: 0, behavior: "smooth" });

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.button
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          onClick={scrollToTop}
          className={cn("fixed bottom-6 right-6 z-sticky w-10 h-10 rounded-full bg-brand text-on-brand shadow-lg flex items-center justify-center hover:bg-brand-dark transition-colors", className)}
          aria-label="Back to top"
        >
          <ArrowUp className="h-4 w-4" />
        </motion.button>
      )}
    </AnimatePresence>
  );
}
```

### 12.8 Copy to clipboard primitive

**New file:** `src/components/ui/CopyButton.tsx`
```tsx
"use client";
import { useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import { Copy, Check } from "lucide-react";

interface CopyButtonProps {
  text: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeClasses = { sm: "h-6 w-6", md: "h-8 w-8", lg: "h-10 w-10" };

export function CopyButton({ text, size = "md", className }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [text]);

  return (
    <button
      onClick={handleCopy}
      className={cn("inline-flex items-center justify-center rounded-lg border border-glass-border-mid bg-glass-panel text-text-muted hover:text-text hover:bg-glass-faint transition-all", sizeClasses[size], className)}
      aria-label={copied ? "Copied!" : "Copy to clipboard"}
    >
      {copied ? <Check className="h-3.5 w-3.5 text-success" /> : <Copy className="h-3.5 w-3.5" />}
    </button>
  );
}
```

### 12.9 Keyboard shortcut display

**New file:** `src/components/ui/Kbd.tsx`
```tsx
"use client";
import { cn } from "@/lib/utils";

interface KbdProps {
  children: React.ReactNode;
  className?: string;
}

export function Kbd({ children, className }: KbdProps) {
  return (
    <kbd className={cn("inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-md border border-glass-border-mid bg-glass-panel text-xs font-mono text-text-muted shadow-sm", className)}>
      {children}
    </kbd>
  );
}

interface ShortcutProps {
  keys: string[];
  className?: string;
}

export function Shortcut({ keys, className }: ShortcutProps) {
  return (
    <span className={cn("inline-flex items-center gap-1", className)}>
      {keys.map((key, i) => (
        <span key={i} className="flex items-center gap-1">
          {i > 0 && <span className="text-text-faint text-xs">+</span>}
          <Kbd>{key}</Kbd>
        </span>
      ))}
    </span>
  );
}
```

### 12.10 QR code display

**New file:** `src/components/ui/QRCode.tsx`
```tsx
"use client";
import { cn } from "@/lib/utils";

interface QRCodeProps {
  value: string;
  size?: number;
  className?: string;
}

export function QRCode({ value, size = 128, className }: QRCodeProps) {
  // Uses Google Charts API for simplicity - replace with a library like qrcode.react for production
  const src = `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(value)}`;

  return (
    <div className={cn("inline-flex p-2 rounded-lg border border-glass-border-mid bg-white", className)}>
      <img src={src} alt={`QR Code for ${value}`} width={size} height={size} className="block" />
    </div>
  );
}
```

### 12.11 Breadcrumb with dropdown

**New file:** `src/components/ui/BreadcrumbDropdown.tsx`
```tsx
"use client";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { ChevronRight, ChevronDown } from "@/lib/icons";

interface BreadcrumbItem {
  label: string;
  href?: string;
  children?: BreadcrumbItem[];
}

interface BreadcrumbDropdownProps {
  items: BreadcrumbItem[];
  className?: string;
}

export function BreadcrumbDropdown({ items, className }: BreadcrumbDropdownProps) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <nav aria-label="Breadcrumb" className={cn("flex items-center gap-1.5 text-sm", className)}>
      {items.map((item, i) => (
        <span key={i} className="flex items-center gap-1.5">
          {i > 0 && <ChevronRight className="h-3 w-3 text-text-faint" />}
          {item.children && item.children.length > 0 ? (
            <span className="relative">
              <button
                onClick={() => setOpenIndex(openIndex === i ? null : i)}
                className="flex items-center gap-1 text-text-muted hover:text-text transition-colors"
              >
                {item.label}
                <ChevronDown className={cn("h-3 w-3 transition-transform", openIndex === i && "rotate-180")} />
              </button>
              {openIndex === i && (
                <div className="absolute top-full left-0 mt-1 z-dropdown min-w-[160px] rounded-xl border border-glass-border-mid bg-glass-strong shadow-xl py-1">
                  {item.children.map((child, j) => (
                    <a key={j} href={child.href || "#"} className="block px-3 py-1.5 text-sm text-text-muted hover:text-text hover:bg-glass-panel transition-colors">
                      {child.label}
                    </a>
                  ))}
                </div>
              )}
            </span>
          ) : (
            item.href && i < items.length - 1 ? (
              <a href={item.href} className="text-text-muted hover:text-text transition-colors">{item.label}</a>
            ) : (
              <span className={cn(i === items.length - 1 ? "text-text font-medium" : "text-text-muted")}>{item.label}</span>
            )
          )}
        </span>
      ))}
    </nav>
  );
}
```

### 12.12 Table of contents

**New file:** `src/components/ui/TableOfContents.tsx`
```tsx
"use client";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";

interface TocItem {
  id: string;
  label: string;
  level: number;
}

interface TableOfContentsProps {
  items: TocItem[];
  className?: string;
}

export function TableOfContents({ items, className }: TableOfContentsProps) {
  const [activeId, setActiveId] = useState("");

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((e) => e.isIntersecting);
        if (visible.length > 0) setActiveId(visible[0].target.id);
      },
      { rootMargin: "-20% 0px -60% 0px" }
    );

    items.forEach((item) => {
      const el = document.getElementById(item.id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, [items]);

  return (
    <nav aria-label="Table of contents" className={cn("w-full", className)}>
      <p className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-2">On this page</p>
      <ul className="space-y-1 border-l border-glass-border-mid">
        {items.map((item) => (
          <li key={item.id}>
            <a
              href={`#${item.id}`}
              className={cn("block pl-3 py-1 text-xs transition-colors border-l -ml-px", activeId === item.id ? "text-brand border-brand font-medium" : "text-text-faint hover:text-text border-transparent")}
              style={{ paddingLeft: `${item.level * 12 + 12}px` }}
            >
              {item.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}
```

### 12.13 Update barrel export

**File:** `src/components/ui/index.ts` — add:
```ts
# Add to existing barrel:
export { ColorPicker } from "./ColorPicker";
export { RichTextEditor } from "./RichTextEditor";
export { Tag } from "./Tag";
export { Tree } from "./Tree";
export { CodeBlock } from "./CodeBlock";
export { MentionInput } from "./MentionInput";
export { BackToTop } from "./BackToTop";
export { CopyButton } from "./CopyButton";
export { Kbd, Shortcut } from "./Kbd";
export { QRCode } from "./QRCode";
export { BreadcrumbDropdown } from "./BreadcrumbDropdown";
export { TableOfContents } from "./TableOfContents";
```

### 12.14 Validate Phase 12

```powershell
npx tsc --noEmit --skipLibCheck
npm run lint
npx jest
npx jest --testPathPattern "components/ui/__tests__"
```

---

## Complete File Change Summary (All 12 Phases)

| Phase | File | Action |
|-------|------|--------|
| 0 | `src/styles/globals.css` | Insert `@import "./tokens.css"` |
| 0 | `src/app/layout.tsx` | Insert `import "@/styles/tokens.css"` + `import "@/styles/glow.css"` |
| 0 | `src/styles/variables.css` | DELETE |
| 0 | `src/styles/comm.css` | RESTORE from HEAD |
| 0 | `src/styles/panel-modern.css` | RESTORE from HEAD |
| 0 | `src/styles/glow.css` | RESTORE from HEAD |
| 0 | `src/styles/tokens.css` | RESTORE from HEAD |
| 0 | `tailwind.config.js` | Map borderRadius + transitionDuration + add max-w-450 |
| 1 | `src/styles/globals.css` | Insert `--color-background` + undefined-class block + `--zozi-ext-*` + `bcu-*` keyframes |
| 1 | `src/styles/globals.css` | Replace focus-kill with focus-visible ring + reduced-motion media query |
| 1 | 4 component files | Fix `z-[200]` / `z-200` usages |
| 2 | `shared/src/theme.ts` | Extend `applyCssTheme` with status/glass vars |
| 2 | `src/styles/globals.css` | Delete flat gradient aliases + align radius/shadow tokens + motion tokens |
| 2 | `tailwind.config.js` | Add 3xs-5xs font sizes + named z-index scale + gradient-brand-to-* keys |
| 2 | `src/styles/globals.css` | Delete dead fadeIn/slideUp + insert `@keyframes scaleIn` |
| 3 | `src/components/ui/index.ts` | Barrel export all primitives |
| 3 | `src/components/ui/shared/Modal.tsx` | Add drawer variant + a11y props |
| 3 | `src/components/ToastSystem.tsx` | DELETE |
| 3 | `src/components/LoadingSkeleton.tsx` | DELETE (root duplicate) |
| 3 | 8 new files | Container, PageHeader, Section, Heading, Alert, StatusBadge, Spinner, Drawer |
| 4 | `src/app/layout.tsx` | Import `MotionConfig` + wrap app |
| 4 | `src/app/template.tsx` | Page transition wrapper |
| 4 | 2 new files | Reveal, Stagger |
| 5 | `src/styles/globals.css` | Entrance utilities + card hover lift + spring transitions + webkit backdrop-filter + hero gradient + view-transition |
| 5 | `src/styles/globals.css` | Delete `!important` panel overrides |
| 6 | 2 new files | codemod-fontsize.mjs, codemod-zindex.mjs |
| 7 | 5 new files | Table, StatCard, Progress, Tooltip, Popover |
| 8 | 10 new files | Tabs, Breadcrumbs, Pagination, Stepper, FormGroup, Input, Textarea, Select, Checkbox, Radio, Switch |
| 8 | 2 existing files | Extend LoadingSkeleton + EmptyState |
| 9 | 4 new files | ErrorState, Group, tokens.ts, Storybook config |
| 9 | `src/styles/globals.css` | Print styles |
| 9 | `src/components/ui/index.ts` | Update barrel with new exports |
| 10 | 8 new files | Accordion, Divider, Avatar, CommandPalette, FileUpload, DatePicker, SearchInput, Button.test |
| 10 | `src/components/ToastContainer.tsx` | Enhanced with queue + positioning |
| 10 | `src/styles/globals.css` | Responsive utilities + performance optimizations |
| 10 | `MIGRATION_PLAYBOOK.md` | Migration guide |
| 10 | `src/components/ui/index.ts` | Update barrel with Phase 10 exports |
| 11 | 10 new files | ConfirmDialog, NotificationCenter, Timeline, Rating, Carousel, InfiniteScroll, Wizard, TagInput, SkeletonPage, Chart |
| 12 | 12 new files | ColorPicker, RichTextEditor, Tag, Tree, CodeBlock, MentionInput, BackToTop, CopyButton, Kbd, QRCode, BreadcrumbDropdown, TableOfContents |

---

## What we keep (do NOT change)

- Current lime/gold brand: `--color-brand: #32CD32`, `--color-accent: #FFD700`
- `globals.css` existing vocabulary (glass, theme-card, theme-panel, shimmer, seasonal-banner-*, etc.)
- `tailwind.config.js` `scaleIn`/`spring`/`expo-out`/`smooth` easing tokens
- Rich `BackgroundEffect.tsx` seasonal engine
- `BannerCanvasEditor.tsx` (legitimate canvas/SVG colors)
- Chart color palettes

## What we drop

- `src/styles/variables.css` (orphan, orange/purple, conflicts with brand)
- `src/components/ToastSystem.tsx` (dead code, imported nowhere)
- `src/components/LoadingSkeleton.tsx` (root duplicate — keep `ui/shared/LoadingSkeleton.tsx`)
- `globals.css:2004–2012` dead `fadeIn`/`slideUp` keyframes
- `globals.css:2255–2271` focus-kill block (replaced by Phase 1.5)
- `globals.css:908–976` `!important` panel overrides (replaced by component system)
- All raw `theme-btn-*` usages outside `ui/Button.tsx` (migrated in Phase 3)
- All raw `glass-panel` modal markup outside `ui/Modal.tsx` (migrated in Phase 3)
- All `text-[10px]…[7px]` arbitrarys (migrated in Phase 2.5 + codemod)
