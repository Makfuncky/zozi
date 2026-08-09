# ZOZI Web App — Design Token & Theme Reference

Codified from the `tailwind-design-system` principles (brand → semantic →
component token hierarchy, class-based dark variant, CVA-style component
conventions), adapted to the **Tailwind CSS v3.4.19** system already live in
`frontend/web_app`.

> Companion to `documents/DESIGN_SYSTEM.md` (panel conventions, component
> library, icon inventory). This file is the **token/theme** layer reference.
>
> **Version note**: the project runs Tailwind **v3.4.19** (config-based), not
> v4 (CSS-first). All rules below describe the *live* v3 system. The v4
> migration path is documented at the end so tokens map 1:1 when upgrading.

---

## 1. Token Hierarchy

```
Brand tokens (abstract values)
    └── Semantic tokens (purpose)        — surfaces, text, borders, status
        └── Component tokens (specific)  — theme-btn-*, card shadows, glass-*
```

**Single source of truth**: ALL semantic/component tokens live in
`src/styles/globals.css` under three theme blocks (`:root` dark-first,
`.light`, `.dark`). `tailwind.config.js` maps the CSS variables to utility
names (`primary`, `accent`, `surface`, `text`, `danger`, …).

> **History**: the old `src/styles/tokens.css` brand-token file was **deleted**
> (dead code — never imported anywhere, and its `--color-brand: #2ecc4f`
> conflicted with the live theme values `#2f9440` light / `#2ecc4f` dark).
> Do NOT reintroduce a parallel token file.

### 1.1 Brand tokens

Defined per-theme in `globals.css`; consumed by semantic tokens.

| Token | Light | Dark |
|---|---|---|
| `--color-brand` | `#2f9440` | `#2ecc4f` |
| `--color-brand-light` | `#59bc61` | `#5fe57a` |
| `--color-brand-dark` | `#256f33` | `#1f9e3c` |
| `--color-accent` | `#f2c94c` | `#FFD700` |
| `--color-accent-light` | `#f7d96c` | `#FFEA00` |
| `--color-accent-dark` | `#c89020` | `#C09000` |
| `--color-surface-0` | `#fbfcf8` | `#000000` |

Brand colors are also exposed as RGB triplets (`--color-brand-rgb: 47 148 64`)
so utilities support alpha: `bg-primary/20`, `border-accent/50`.

### 1.2 Semantic tokens

Exposed to Tailwind via `tailwind.config.js` `theme.extend.colors` using the
pattern `rgb(var(--color-X-rgb) / <alpha-value>)` so every color supports
`/opacity` modifiers.

| Utility prefix | Purpose |
|---|---|
| `primary`, `primary-light/dark` | Brand actions, links, active states |
| `accent`, `accent-light/dark` | Highlights, badges, CTAs |
| `success`, `danger`, `warning`, `info` | Status semantics (with `on-*` text colors) |
| `surface`, `surface-base`, `surface-1/2/3` | Elevation ladder — card bg, hover bg |
| `background` | Page background (`--color-background-rgb`) |
| `text`, `text-muted`, `text-faint` | Text emphasis ladder |
| `border`, `border-light` | Hairlines and dividers |
| `on-brand`, `on-accent`, `on-warning` | Contrast-safe text on filled surfaces |
| `glass-*` (`glass-base/mid/hi/solid/panel/faint`, `glass-border*`) | Frosted panel surfaces |

**Convention**: status colors use Tailwind names that already carry meaning
(`danger`, `warning`, `info`). Do not add `destructive`/`card` aliases until a
v4 migration makes them worth it.

### 1.3 Component tokens

- **Button themes** (`theme-btn-primary/secondary/danger/danger-outline/accent/admin`)
  — plain CSS classes in `globals.css`, consumed by the `Button.tsx` variant map.
  Extend the Button component; do not inline button styles in pages.
- **Shadows** (`card-sm/card/card-lg/card-xl`, `glass`, `glow-primary`,
  `btn-primary`, `focus`) — the card/shadow ladder.
- **Gradients** (`gradient-banner`, `gradient-card`, `gradient-logo`, …) —
  theme-driven banner/card treatments.
- **Chips** (`theme-chip-*`) — status chips for tables/dashboards.

---

## 2. Theme Strategy (dark-first, class-based)

- `darkMode: "class"` in `tailwind.config.js`; `dark:` variants compile to
  `.dark …` selectors.
- Three blocks in `globals.css`:
  1. `:root` — **dark-first defaults** (dark is the base).
  2. `.light` — overrides for light theme.
  3. `.dark` — explicit dark overrides + `html.dark { color-scheme: dark }`.
- Toggling adds/removes the `light`/`dark` class on `<html>` (see the app's
  theme store / SSR anti-flash bootstrap). `html { background-color:
  var(--color-surface-0); color: var(--color-text) }` anchors the cascade.

**Rules**
- New tokens must be defined in **all three blocks** or theme switching breaks.
- Use semantic utilities (`bg-surface`, `text-text-muted`) not raw hex in
  components — they re-theme automatically.
- Alpha modifiers (`/20`, `/50`) are safelisted in `tailwind.config.js` for
  the common color set — add new alpha combos to the safelist if JIT purges them.

---

## 3. Component Conventions

### 3.1 Primitive kit (`src/components/ui/`)

| Component | Contract |
|---|---|
| `Button` | Variants `primary/secondary/ghost/danger/danger-outline/accent/admin/warning/info`; sizes `sm/md/lg`; `isLoading`, `icon`, `iconRight`; forwards `ref`; `aria-busy` when loading |
| `Card` / `GlassCard` | Glass-surface panels with the `card` shadow ladder |
| `StatCard` | KPI card — `bg-surface border-border`, status via `text-success`/`text-danger` |
| `FormLayout` | Label + input + error; error state via `border-danger text-danger` |
| `Dropdown` | Menu surface; danger items use `bg-danger text-danger` |
| `shared/` | Shared sub-pieces |

### 3.2 Conventions

- **`cn()`**: `import { cn } from "@/lib/utils"` (clsx + tailwind-merge).
  Always pass `className` through `cn(...)`.
- **Variant maps**: `Record<Variant, string>` (Button pattern) or CVA
  (`class-variance-authority` is installed) — pick one per component; do not mix.
- **Accessibility**: `focus-visible:ring-2 focus-visible:ring-primary
  focus-visible:ring-offset-2`; `aria-busy` on loading buttons; `aria-invalid`
  + `role="alert"` on form errors; Escape closes modals; icon-only buttons
  carry `aria-label`.
- **Dark-safe**: no hardcoded `#` colors in JSX — every color must come from a
  token utility (exception: SVG logo internals use `--zozi-logo-*` vars).
- **RTL**: `icon-gap` reverses icon order for Arabic; keep `dir`-sensitive
  layouts flexible.
- **Density**: table/list pages read density from `densityContext`
  (compact / normal / expanded).

---

## 4. Tailwind v4 Migration Path (when ready)

The v3 config is already token-complete, so migration is mechanical:

| v3 (current) | v4 target |
|---|---|
| `tailwind.config.js` `theme.extend.colors` | `@theme { --color-* }` in `globals.css` |
| `@tailwind base/components/utilities` | `@import "tailwindcss"` |
| `darkMode: "class"` | `@custom-variant dark (&:where(.dark, .dark *))` |
| `theme.extend.animation` + `keyframes` | `@theme` with `--animate-*` + inline `@keyframes` |
| RGB-triplet alpha trick | `color-mix()` / `--color-*` alpha natively |
| `safelist` for alpha combos | Usually unnecessary (v4 scans better) |
| CSS `theme-btn-*` classes | `@utility theme-btn-*` or CVA components |

Migration checklist:
1. Port color tokens (`brand`, `accent`, `status`, `surface*`, `text*`,
   `border*`, `glass*`) into `@theme` verbatim.
2. Move keyframes + `--animate-*` into `@theme`.
3. Replace the three theme blocks with `:root` defaults + `@custom-variant
   dark` overrides.
4. Delete `theme.extend` remnants and `safelist` after verifying JIT coverage.
5. Verify with the app's Playwright E2E suites (light + dark, Admin/Supplier/
   Logistics panels).

---

## 5. Do / Don't

- **Do** use semantic utilities (`bg-surface`, `text-text-muted`) everywhere.
- **Do** extend tokens in all three theme blocks simultaneously.
- **Do** route styling through the `Button`/`Card` primitives.
- **Don't** add raw hex colors in JSX.
- **Don't** create a second token file — `globals.css` is the single source.
- **Don't** hardcode Tailwind class strings outside `cn()` composition.
