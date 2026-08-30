# ZOZI Frontend CSS Architecture — Design Handoff Document

**Date**: 2026-08-29
**Prepared for**: Design Handling Agent
**Source**: `frontend/web_app/`

---

## 1. File Inventory

### 1.1 Source CSS Files (`src/styles/`)

| File | Lines | Size | Purpose |
|---|---|---|---|
| `globals.css` | 5 | ~120 B | **Stub** — only `@import "tailwindcss"` + `.test-tailwind`. Real content is in `public/globals.css`. |
| `tokens.css` | 422 | ~12 KB | **Canonical design tokens** — all CSS custom properties for dark (`:root`) and light (`.light`) themes. |
| `glow.css` | 43 | ~1.2 KB | Gradient/solid utilities (partner hero, footer glow, tracking glow, label gradient). |
| `fonts.css` | 11 | ~350 B | Arabic `@font-face` using system fonts. |
| `comm.css` | 292 | ~8.5 KB | Communication workspace structural & motion CSS (5-zone grid, rail, composer, animations). |
| `panel-modern.css` | 74 | ~2.1 KB | Collapsible panel styles for admin/supplier panels. |
| `test.css` | 1 | ~20 B | Test file — only imports Tailwind. |

### 1.2 Component CSS Files

| File | Lines | Purpose |
|---|---|---|
| `src/components/ticker-bar.css` | 10 | TickerBar marquee animation. |
| `src/components/supplier/editor-buttons.css` | 28 | Shared editor toolbar button styles. |
| `src/components/banner-effects.module.css` | 13 | CSS Module — celebration/season effect keyframes. |
| `src/components/admin/commandCenter/hud.css` | 21 | HUD command-center keyframes (scan, pulse, shimmer, marquee). |
| `src/app/supplier/labels/[id]/print.css` | 33 | Print stylesheet for supplier parcel-label sheet. |

### 1.3 Public CSS Files (`public/`)

Served as static files via `<link>` tags (Next.js 16 workaround):

| File | Lines | Notes |
|---|---|---|
| `globals.css` | 3,626 | **Real compiled globals** — all design utilities, glass effects, buttons, cards, animations, light/dark overrides. |
| `tokens.css` | 422 | Verbatim copy of `src/styles/tokens.css`. |
| `glow.css` | 43 | Verbatim copy of `src/styles/glow.css`. |
| `fonts.css` | 11 | Verbatim copy of `src/styles/fonts.css`. |

### 1.4 Prototype/Regeneration Files (`_extra_files/gcss_proto/`)

**NOT imported** — work-in-progress artifacts for CSS rebuild:

| File | Lines | Notes |
|---|---|---|
| `globals.css` | 9,601 | Full Tailwind v3 compiled output. |
| `globals_regen.css` | 5,286 | Regenerated compact version. |
| `input.css` | 3 | `@tailwind base; @tailwind components; @tailwind utilities;` |
| `regen_all.css` | 1,897 | Full regenerated Tailwind base + utilities. |

---

## 2. CSS Configuration

### 2.1 `postcss.config.js`
```js
module.exports = {
  plugins: {
    "@tailwindcss/postcss": {},  // Tailwind v4 PostCSS plugin
    autoprefixer: {},
  },
};
```

### 2.2 `tailwind.config.js` (271 lines)
- **Content paths**: `src/components/**`, `src/app/**`, `src/lib/**`, `src/hooks/**`, `src/services/**`, `../shared/src/**`
- **Dark mode**: `"class"` (toggle via `html.dark` / `html.light`)
- **Plugins**: None (`plugins: []`)
- **Safelist**: ~250+ utility patterns for dynamic class preservation

### 2.3 Tailwind Version
| Package | Version |
|---|---|
| `next` | ^16.3.3 |
| `@tailwindcss/postcss` | ^4.3.3 |
| `tailwind-merge` | ^3.5.0 |
| `class-variance-authority` | ^0.7.1 |
| `clsx` | ^2.1.1 |

**Note**: Project uses Tailwind v4 (`@tailwindcss/postcss`) but config is v3 format. `public/globals.css` header says `tailwindcss v3.4.19`.

---

## 3. CSS Loading Architecture

### 3.1 Root Layout (`src/app/layout.tsx`)

**Webpack imports (processed by Next.js):**
```tsx
import "@/styles/tokens.css";    // Design tokens (CSS custom properties)
import "@/styles/test.css";      // Tailwind import test
import "@/styles/globals.css";   // Stub (only @import "tailwindcss" + .test-tailwind)
import "@/styles/glow.css";      // Gradient/glow utilities
```

**`<link>` tags in `<head>` (static files, bypasses webpack):**
```html
<link rel="stylesheet" href="/fonts.css" />
```

**Anti-flash inline scripts:**
1. Theme class applied from localStorage or `prefers-color-scheme`
2. Locale/dir applied from localStorage or `navigator.language`

### 3.2 Component-Level CSS Imports

| Component | CSS Import |
|---|---|
| `hud.tsx` | `import "./hud.css"` |
| `BannerCanvasEditor.tsx` | `import styles from "./banner-effects.module.css"` (CSS Module) |
| `CommShell.tsx` | `import "@/styles/comm.css"` |
| `TickerBar.tsx` | `import "./ticker-bar.css"` |
| `MapView.tsx` / `LocationPicker.tsx` | `import "leaflet/dist/leaflet.css"` (third-party) |
| `PanelPage.tsx` | `import "@/styles/panel-modern.css"` |
| `ProductImageCanvas.tsx` / `PhotoEditorModal.tsx` | `import "./editor-buttons.css"` |
| `supplier/labels/[id]/page.tsx` | `import "./print.css"` |

---

## 4. Design Tokens (CSS Custom Properties)

### 4.1 Color Tokens — Dark Theme (`:root`)

| Token | Value |
|---|---|
| `--color-brand` | `#32CD32` (lime green) |
| `--color-brand-rgb` | `50 205 50` |
| `--color-brand-light` | `#7CFC00` |
| `--color-brand-dark` | `#228B22` |
| `--color-accent` | `#FFD700` (gold) |
| `--color-accent-rgb` | `255 215 0` |
| `--color-surface-0` | `#0f1419` |
| `--color-surface-1` | `#1a1f26` |
| `--color-surface-2` | `#252b33` |
| `--color-surface-3` | `#353c45` |
| `--color-border` | `#353c45` |
| `--color-text` | `#FFFFFF` |
| `--color-text-muted` | `#cbd5e1` |
| `--color-text-faint` | `#9CA3AF` |
| `--color-success` | `#22c55e` |
| `--color-danger` | `#ef4444` |
| `--color-warning` | `#FFD700` |
| `--color-info` | `#2f9be0` |
| `--color-on-brand` | `#000000` |

### 4.2 Color Tokens — Light Theme (`.light`)

| Token | Value |
|---|---|
| `--color-brand` | `#2f9440` |
| `--color-surface-0` | `#f8fafc` |
| `--color-surface-1` | `#ffffff` |
| `--color-text` | `#111111` |
| `--color-border` | `#e2e8d9` |

### 4.3 Glass/Frosted Tokens
`--color-glass-base`, `--color-glass-mid`, `--color-glass-hi`, `--color-glass-solid`, `--color-glass-panel`, `--color-glass-faint`, `--color-glass-border`, `--color-glass-border-mid`, `--color-glass-border-soft`

### 4.4 Gradient Tokens
`--gradient-logo`, `--gradient-brand-text`, `--gradient-banner`, `--gradient-banner-alt`, `--gradient-hero`, `--gradient-card`, `--gradient-logo-text`, `--gradient-brand-to-success`, `--bg-texture`, `--overlay-bg`

### 5.5 Radius Scale
`--zozi-radius-sm` (4px), `--zozi-radius-md` (8px), `--zozi-radius-lg` (12px), `--zozi-radius-xl` (16px), `--zozi-radius-2xl` (24px), `--zozi-radius-pill` (9999px)

### 5.6 Elevation Scale
`--zozi-elevation-sm`, `--zozi-elevation-md`, `--zozi-elevation-lg`, `--zozi-elevation-xl`

### 5.7 Motion Duration
`--zozi-duration-fast` (120ms), `--zozi-duration-base` (180ms), `--zozi-duration-normal` (200ms), `--zozi-duration-slow` (300ms), `--zozi-duration-slower` (500ms), `--zozi-duration-slowest` (700ms)

---

## 5. Tailwind Theme Extensions

### 5.1 Colors
All mapped to CSS custom properties: `primary`, `primary-light`, `primary-dark`, `accent`, `accent-light`, `success`, `danger`, `error`, `warning`, `info`, `on-brand`, `primary-foreground`, `on-accent`, `on-warning`, `surface` (with scale), `background`, `muted`, `muted-foreground`, `text`, `text-muted`, `text-faint`, `border`, `border-light`, plus legacy aliases (`charcoal`, `zozi-primary`, etc.).

### 5.2 Typography
- `fontFamily`: `heading`/`display` (Fraunces), `body`/`sans` (Sora)
- `fontSize`: Extended scale from `2xs` through `6xl` plus `display` (clamp)

### 5.3 Spacing
Extended with `4.5`, `13`, `15`, `18`, `22`, `30`, `88`, `128`

### 5.4 Border Radius
`sm` through `4xl` + `pill` + `token` scale

### 5.5 Box Shadow
`card-sm`, `card`, `card-lg`, `card-xl`, `glow-primary`, `glow-accent`, `glow-primary-lg`, `glass`, `btn-primary`, `btn-primary-hover`, `focus`

### 5.6 Background Image
`gradient-primary`, `gradient-accent`, `gradient-hero`, `gradient-logo`, `gradient-card`, `gradient-radial`, `gradient-text`, `gradient-logo-text`, `gradient-brand-to-success`

### 5.7 Animations
`ticker` (60s), `float` (6s), `spin-slow` (8s)

---

## 6. Key Design Utility Classes

| Class | Source | Purpose |
|---|---|---|
| `.glass` | `public/globals.css` | Frosted card surface |
| `.glass-panel` | `public/globals.css` | Panel container |
| `.glass-card` | `public/globals.css` | Card with glossy pseudo-elements |
| `.glass-product-card` | `public/globals.css` | Product card surface |
| `.glass-search` | `public/globals.css` | Search bar surface |
| `.glass-dropdown` | `public/globals.css` | Dropdown panel |
| `.glass-input` | `public/globals.css` | Input field in glass panels |
| `.glass-strong` | `public/globals.css` | Heavy backdrop panel |
| `.theme-card` | `public/globals.css` | Themed card with elevation |
| `.theme-btn-primary` | `public/globals.css` | Brand CTA button |
| `.theme-btn-accent` | `public/globals.css` | Yellow accent button |
| `.theme-btn-secondary` | `public/globals.css` | Neutral surface button |
| `.theme-btn-danger` | `public/globals.css` | Destructive CTA |
| `.theme-btn-admin` | `public/globals.css` | Blue admin CTA |
| `.theme-modal-shell` | `public/globals.css` | Modal container |
| `.theme-layout-shell` | `public/globals.css` | Layout wrapper |
| `.theme-sidebar-shell` | `public/globals.css` | Sidebar panel |
| `.theme-topbar` | `public/globals.css` | Top navigation bar |
| `.theme-nav-item` | `public/globals.css` | Navigation item |
| `.theme-nav-item-active` | `public/globals.css` | Active nav item |
| `.theme-main-content` | `public/globals.css` | Main content area |
| `.btn-place-order` | `public/globals.css` | Place order CTA |
| `.btn-buy-now` | `public/globals.css` | Buy now yellow CTA |
| `.status-pill` | `public/globals.css` | Status badge |
| `.aurora-bg` | `public/globals.css` | Animated gradient background |
| `.animate-shimmer` | `public/globals.css` | Skeleton loading animation |
| `.text-gradient` | `public/globals.css` | Gradient text effect |
| `.scrollbar-none` | `public/globals.css` | Hide scrollbar |
| `.page-wrapper` | `public/globals.css` | Max-width container |

---

## 7. Critical Issues Requiring Design Agent Attention

### 7.1 CRITICAL: Undefined Token References

The following CSS variables are **referenced throughout the codebase but NEVER defined**:

**`--zozi-ov-*` overlay RGB tokens** (36 tokens):
- `--zozi-ov-black-rgb`, `--zozi-ov-white-rgb`, `--zozi-ov-olive-rgb`, `--zozi-ov-slate900-rgb`, `--zozi-ov-pine-rgb`, `--zozi-ov-sprout-rgb`, `--zozi-ov-gold-rgb`, `--zozi-ov-gunmetal-rgb`, `--zozi-ov-cream-rgb`, `--zozi-ov-fern-rgb`, `--zozi-ov-blue900-rgb`, `--zozi-ov-azure-rgb`, `--zozi-ov-teal-rgb`, `--zozi-ov-lilac-rgb`, `--zozi-ov-brass-rgb`, `--zozi-ov-ink900-rgb`, `--zozi-ov-void-rgb`, `--zozi-ov-foam-rgb`, `--zozi-ov-milk-rgb`, `--zozi-ov-pearl-rgb`, `--zozi-ov-lime-rgb`, `--zozi-ov-mist-rgb`, `--zozi-ov-snow-rgb`, `--zozi-ov-frostmint-rgb`, `--zozi-ov-butter-rgb`, `--zozi-ov-seafoam-rgb`, `--zozi-ov-ivory-rgb`, `--zozi-ov-chiffon-rgb`, `--zozi-ov-linen-rgb`, `--zozi-ov-meadow-rgb`, `--zozi-ov-ochre-rgb`, `--zozi-ov-forest-rgb`, `--zozi-ov-olivedrab-rgb`, `--zozi-ov-bark-rgb`, `--zozi-ov-brand-rgb`, `--zozi-ov-leaf-rgb`

**`--zozi-space-*` spacing tokens** (20+ tokens):
- `--zozi-space-px`, `--zozi-space-050`, `--zozi-space-075`, `--zozi-space-1` through `--zozi-space-150`, `--zozi-space-250`, `--zozi-space-350`, `--zozi-space-450`, `--zozi-space-6`

**`--zozi-pal-*` palette tokens** (8 tokens):
- `--zozi-pal-slate100`, `--zozi-pal-slate300`, `--zozi-pal-slate600`, `--zozi-pal-sky100`, `--zozi-pal-green50`, `--zozi-pal-green100`, `--zozi-pal-green800`, `--zozi-pal-emerald100`

**Impact**: Glass effect colors fall back to `rgb(undefined / 0.X)` → **invisible/broken**. Spacing tokens fall back to `undefined` → **0 or invalid**. Light mode polish classes don't render correctly.

### 7.2 Next.js 16 CSS Loader Workaround

**Issue**: `next-flight-css-loader` doesn't process `@tailwind` directives in Next.js 16.

**Workaround**: CSS files loaded via `<link>` tags in `layout.tsx` instead of webpack imports. `src/styles/globals.css` is a 5-line stub; the real 3,626-line file is in `public/globals.css`.

**Action Required**: When migrating to proper Tailwind v4, remove the `<link>` workaround and restore webpack imports.

### 7.3 Tailwind Version Mismatch

- **Package**: `@tailwindcss/postcss` ^4.3.3 (Tailwind v4)
- **Config format**: v3-style CommonJS (`module.exports` with `content`, `theme.extend`)
- **Static CSS**: `public/globals.css` header says `tailwindcss v3.4.19`

**Action Required**: Regenerate `public/globals.css` from Tailwind v4 or migrate config to v4 format.

### 7.4 Duplicate CSS Definitions

- `.glass-panel` defined twice in `public/globals.css` (lines 409, 3543) with different values
- `.glass-card > *` pseudo-elements duplicated (lines 781-784, 786-789)
- Many `.hover:*` and `.focus:*` classes duplicated (lines 2175-2390 duplicate 2200-2370)

### 7.5 Test Expectations vs Reality

Test `designSystemTokens.test.ts` expects `tokens.css` to import from `globals.css`, but `src/styles/globals.css` doesn't import `tokens.css`. Test may fail.

---

## 8. Build & Dev Commands

```bash
# Development
npm run dev          # next dev --webpack

# Production build
npm run build        # next build --webpack

# Lint
npm run lint         # ESLint

# Type check
npx tsc --noEmit --skipLibCheck

# Unit tests
npx jest --runInBand

# E2E tests
npx playwright test
```

---

## 9. File Reference Quick Map

```
frontend/web_app/
├── postcss.config.js          # Tailwind v4 + Autoprefixer
├── tailwind.config.js         # v3-format config (content, theme, safelist)
├── src/
│   ├── app/
│   │   ├── layout.tsx         # CSS imports + <link> tags + anti-flash scripts
│   │   ├── globals.css        # 5-line stub (real content in public/)
│   │   └── supplier/labels/[id]/print.css
│   ├── styles/
│   │   ├── tokens.css         # 422 lines — design tokens (dark + light)
│   │   ├── glow.css           # 43 lines — gradient/glow utilities
│   │   ├── fonts.css          # 11 lines — Arabic @font-face
│   │   ├── comm.css           # 292 lines — communication workspace
│   │   ├── panel-modern.css   # 74 lines — collapsible panels
│   │   └── test.css           # 1 line — Tailwind test
│   └── components/
│       ├── ticker-bar.css     # 10 lines — marquee animation
│       ├── supplier/editor-buttons.css  # 28 lines
│       ├── banner-effects.module.css    # 13 lines (CSS Module)
│       └── admin/commandCenter/hud.css  # 21 lines
├── public/
│   ├── globals.css            # 3,626 lines — REAL compiled globals
│   ├── tokens.css             # 422 lines — copy of src/styles/tokens.css
│   ├── glow.css               # 43 lines — copy of src/styles/glow.css
│   └── fonts.css              # 11 lines — copy of src/styles/fonts.css
└── _extra_files/gcss_proto/   # Prototype regeneration artifacts (NOT imported)
```

---

## 10. Recommendations for Design Agent

1. **Define missing tokens**: Add `--zozi-ov-*`, `--zozi-space-*`, `--zozi-pal-*` to `tokens.css`
2. **Deduplicate CSS**: Remove duplicate `.glass-panel`, `.glass-card > *`, `.hover:*`, `.focus:*` definitions
3. **Unify Tailwind version**: Either migrate config to v4 format or downgrade `@tailwindcss/postcss` to v3
4. **Remove `<link>` workaround**: Once Tailwind v4 is properly configured, restore webpack CSS imports
5. **Regenerate globals.css**: Run Tailwind build to generate fresh `public/globals.css` from current config
6. **Fix test expectations**: Update `designSystemTokens.test.ts` to match actual file structure
