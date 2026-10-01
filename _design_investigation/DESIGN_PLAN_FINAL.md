# ZOZI Frontend Design System — Complete Implementation Plan

> **Scope:** A real, phased, line-to-line plan to (1) close the concrete CSS gap breaking `designSystemTokens.test.ts`, (2) reconcile the token foundation, (3) consolidate the bypassed component system, (4) modernize motion, and (5) unify the modern look — for a large GCC e-commerce app (162 components, 460 tsx files, framer-motion in 70+ files).

**Audited reality (verified 2026-08-30):**
- `components/ui/` already exists (12 primitives: Button, Card, GlassCard, Dropdown, FormLayout, StatCard, shared/{Modal,Table,Badge,LoadingSkeleton,EmptyState}) — **but is bypassed everywhere**: 80+ raw `theme-btn-*` buttons, **20+ hand-rolled modals**, two toast systems (`ToastContainer` wired in `layout.tsx:9`, `ToastSystem.tsx` imported nowhere), two skeletons, two card systems (Card vs GlassCard), two inputs (root `Input.tsx` vs `FormLayout.FormInput`).
- `framer-motion` is the sole animation runtime (70+ files) — **but `MotionConfig` and `useReducedMotion` are used in ZERO files** → accessibility gap across all motion.
- `theme.ts` (`applyCssTheme`) sets **17** CSS vars; `globals.css` defines **70+**. Status colors (`--color-success/danger/warning/info`), 18 semantic colors, glass vars, gradients, shadows are **theme-inert** (hardcoded/computed, never switched by JS).
- Arbitrary `text-[10px]…[7px]` appear in **50+ files** because no font-size token exists. Color arbitrary values (`bg-[#…]`) are **zero** — color theming is actually good.
- No `app/template.tsx` → **no page transitions**. No shared `Container`/`PageHeader`/`Section` → storefront widths drift (`max-w-11xl` / `max-w-[1400px]` / `max-w-7xl` / `max-w-6xl`).
- Panel pages use `!important` global overrides (`globals.css:911-976`) that fight any component-level iteration.

**Execution principle:** Phase 0 first (unblocks the red test + restores genuine CSS), then Phases 1-4 in dependency order. Each phase lists exact files, actions, and code. Phases are independently shippable (additive) except where noted.

## Phase 0 — Close the concrete gap (restore 4 deleted files + wire)

These files are **deleted from the working tree** but exist at `HEAD`. Restoring them is byte-identical and is what the red test expects.

```
# 0.1 restore verbatim from HEAD
git show HEAD:frontend/web_app/src/styles/comm.css         > frontend/web_app/src/styles/comm.css
git show HEAD:frontend/web_app/src/styles/panel-modern.css > frontend/web_app/src/styles/panel-modern.css
git show HEAD:frontend/web_app/src/styles/glow.css         > frontend/web_app/src/styles/glow.css
git show HEAD:frontend/web_app/src/styles/tokens.css       > frontend/web_app/src/styles/tokens.css
```

**0.2 Wire `tokens.css`** — `designSystemTokens.test.ts:17-23` requires `@import "./tokens.css"` inside `globals.css` AND `layout.tsx` importing `@/styles/tokens.css`. Edit `frontend/web_app/src/styles/globals.css` line 2:

```css
1: @import "tailwindcss";
2: @import "./tokens.css";
```

Edit `frontend/web_app/src/app/layout.tsx` after line 4:

```tsx
4: import "@/styles/globals.css";
5: import "@/styles/tokens.css";
6: import "@/styles/glow.css";
```

**0.3 Delete the stray `variables.css`** (orange `#f97316`/purple `#a855f7`, conflicts with brand; it is untracked):

```
rm frontend/web_app/src/styles/variables.css
```

> `comm.css` (imported by `CommShell.tsx:33`) and `panel-modern.css` (imported by `PanelPage.tsx:10`) need no further wiring. `glow.css` needs the layout import above (it has 0 importers today). `tokens.css` adds the canonical `zozi-*` scale + `--color-*-rgb` + overlay channels; where `globals.css :root` re-declares a var, the later `:root` wins → current lime/gold brand is preserved.

**Validate 0:** `cd frontend/web_app && npx jest src/__tests__/designSystemTokens.test.ts` must pass.

---

## Phase 1 — Token foundation reconciliation

Make the design tokens a single source of truth across `theme.ts`, `globals.css`, and `tailwind.config.js`.

### 1.1 Make status/semantic/glass/gradient vars theme-aware
**File:** `frontend/shared/src/theme.ts` — extend `applyCssTheme()` to set the vars `globals.css` defines but JS never sets. Append inside the function (after line 200):

```ts
  // Status + semantic (currently theme-inert in globals.css)
  root.style.setProperty("--color-success", status.success);
  root.style.setProperty("--color-danger", status.danger);
  root.style.setProperty("--color-warning", status.warning);
  root.style.setProperty("--color-info", status.info);
  root.style.setProperty("--color-accent-dark", brand.accentDark ?? "#C09000");
  root.style.setProperty("--color-on-brand", colors.onBrand ?? "#ffffff");
  root.style.setProperty("--color-on-accent", colors.onAccent ?? "#000000");
  // Glass layer re-derived from surface so panels re-theme cleanly
  root.style.setProperty("--color-glass-base", "color-mix(in srgb, " + colors.surface0 + " 60%, transparent)");
  root.style.setProperty("--color-glass-panel", "color-mix(in srgb, " + colors.surface1 + " 84%, transparent)");
  root.style.setProperty("--color-glass-border", colors.borderLight);
```

This single change makes `BULK_COLOR_HEX_MAP` (draftUtils.ts) the only remaining hardcoded color map → replace it to read from these tokens in 1.4.

### 1.2 Add a font-size token scale (kills `text-[10px]` arbitrarys)
**File:** `frontend/web_app/tailwind.config.js` — extend `fontSize` (lines 72-85) with dense sizes used across admin/command-center:

```js
fontSize: {
  "2xs": ["0.625rem", { lineHeight: "1rem" }],
  "3xs": ["0.5625rem", { lineHeight: "0.875rem" }],   // ~9px
  "4xs": ["0.5rem", { lineHeight: "0.75rem" }],        // ~8px
  "5xs": ["0.4375rem", { lineHeight: "0.625rem" }],    // ~7px
  // ... keep existing xs..display
}
```
Then migrate `text-[10px]→text-xs`, `text-[9px]→text-3xs`, `text-[8px]→text-4xs`, `text-[7px]→text-5xs` via a codemod (1.9).

### 1.3 Add a z-index scale
**File:** `frontend/web_app/tailwind.config.js` — extend `zIndex` (lines 194-202) to a named scale:

```js
zIndex: { header: "50", dropdown: "1000", sticky: "1020", overlay: "1040", modal: "1050", popover: "1060", tooltip: "1070", toast: "1080" }
```
Migrate raw `z-[200]`/`z-[999]`/`z-[300]` to these names (codemod 1.9). `Modal.tsx` and `ToastContainer` must use `z-modal`/`z-toast`.

### 1.4 De-duplicate the product color map
**File:** `frontend/web_app/src/app/supplier/bulk/draftUtils.ts` — replace `BULK_COLOR_HEX_MAP` (24 hardcoded hexes) with references to the token vars (read via `getComputedStyle(document.documentElement)` or import the `status`/semantic map from `@shared`). Eliminates a parallel color system.

### 1.5 Remove panel `!important` overrides
**File:** `frontend/web_app/src/styles/globals.css:911-976` — these `:where(.supplier/.admin/.logistics-partner) button/card/input { … !important }` rules fight component iteration. Delete this block **after** Phase 2 panels are migrated.

### 1.6 Token map to `tailwind.config.js` colors
Confirm `success/danger/warning/info` map to the now-JS-set vars (lines 18-21 already do this — they were inert until 1.1). No change needed.

### 1.7 Kill dead keyframes
`globals.css:2004 fadeIn` and `:2009 slideUp` have **no consumers**. Delete them (framer-motion owns entrance). Low risk.

### 1.8 `tokens.css` alignment
`tokens.css` (restored in 0.1) already defines the `zozi-*` scale the test checks. Keep it imported (0.2).

### 1.9 Codemod scripts (run once, then `git diff` review)
- `scripts/codemod-fontsize.mjs` — `text-[10px]→text-xs`, `text-[9px]→text-3xs`, `text-[8px]→text-4xs`, `text-[7px]→text-5xs` across `src/**/*.tsx`.
- `scripts/codemod-zindex.mjs` — `z-[200]/z-[999]/z-[300]…` → named scale.

**Validate 1:** `npx tsc --noEmit --skipLibCheck` + `npm run lint` + `npx jest src/__tests__/designSystemTokens.test.ts` + visual: toggle light/dark on a product page → status chips and glass panels re-theme.

## Phase 2 — Component system consolidation (the architectural win)

Goal: make `components/ui/` the **only** way to render buttons, modals, toasts, cards, inputs, and add the missing primitives. This is what makes the app maintainable at 100K-user scale.

### 2.1 Single barrel + folder rules
- Add `frontend/web_app/src/components/ui/index.ts` re-exporting all primitives (currently only `shared/index.ts` exists).
- Add a check (`scripts/check-ui-imports.mjs` or eslint) that **forbids** raw `theme-btn-*` class usage outside `ui/Button.tsx` and raw `theme-overlay`/`glass-panel` modal markup outside `ui/shared/Modal.tsx`. This enforces the system going forward.

### 2.2 Unify Modal → one primitive + Drawer variant
- **Keep & extend** `components/ui/shared/Modal.tsx` (already framer-motion + `animate-fade-in`/`animate-scale-in` + `theme-overlay`/`glass-panel`). Add:
  - `variant: "modal" | "drawer"` (drawer = side sheet reusing `PanelDrawer` CSS pattern from `PanelPage.tsx:732-758`, but via framer-motion for consistency).
  - `closeOnEscape` (default true), `lockScroll` (default true), `role="dialog"` + `aria-modal` (verify present), `initialFocus` prop.
- **Migration targets (replace hand-rolled overlays with `<Modal>`)** — verified list of 20+ files:
  `ApprovalActionModal.tsx:158`, `AuthRequiredModal.tsx:165`, `AdminChatPanel.tsx:753`, `AdminVideoPanel.tsx:309/354/395`, `EmailCampaignManager.tsx:170`, `CommandPalette.tsx:116`, `CountryStaffAssignmentModal.tsx:77`, `ImageZoom.tsx:59`, `ShiftHandoverModal.tsx:67`, `QuickDetailModal.tsx:36`, `QuickViewModal.tsx:31`, `AIResultsModal.tsx:43`, `BgStrategyOnboardingTooltip.tsx:109`, `PhotoEditorModal.tsx:202`, `ProductImageCanvas.tsx:198`, `ProcessingModal.tsx:27`, `ProductPublishSuccess.tsx:26`, `QuantityModal.tsx:61`, `SmartMediaUpload.tsx:28`, `VerificationPopup.tsx:34`, `UploadModal.tsx:81`, `VoiceProductInput.tsx:236`, `VerifyPublishModal.tsx:48`, `SizeGuide.tsx:57`, `MobileSearchOverlay.tsx:322`.
  Migrate a **few per PR** (highest-traffic first: product/cart/checkout flows).

### 2.3 Unify Toast → delete `ToastSystem.tsx`
- `ToastContainer.tsx` is already wired in `layout.tsx`. Make it the single system. Delete `components/ToastSystem.tsx` (imported nowhere). Ensure it uses `z-toast` (1.3) and `useReducedMotion`-aware animation (Phase 3).

### 2.4 Unify LoadingSkeleton
- Keep `components/ui/shared/LoadingSkeleton.tsx` as the source; delete root `components/LoadingSkeleton.tsx`. Add shimmer variant (use existing `.animate-shimmer` from `globals.css:1333`/keyframe `:1999`) to the 15+ hand-rolled `loading.tsx` route files by replacing raw `animate-pulse` blocks with `<LoadingSkeleton variant="…">`.

### 2.5 Unify Card
- Define **one** `Card` with `variant: "glass" | "glass-solid" | "elevated" | "product"` subsuming `Card.tsx`, `GlassCard.tsx`, `theme-card`, `glass-product-card`, and the raw `rounded-2xl border bg-surface-*` divs in product detail/home. Keep `theme-card` as the CSS implementation behind the component (no CSS rewrite needed).
- Migration: `StatCard.tsx` (currently opaque `bg-surface`, visual outlier) → use `Card variant="glass"`.

### 2.6 Unify Input
- `components/Input.tsx` becomes the single input (label/error/helperText). `FormLayout.FormInput` should re-export it to avoid two code paths. Drop `focus:ring-primary/20` vs `focus:ring-primary` divergence.

### 2.7 New primitives to add (file-per-component under `components/ui/`)
| Primitive | Why | Notes |
|---|---|---|
| `Container.tsx` | Kill width drift (4.2) | `max-w` prop: `wide(1400)/default(1200)/narrow(880)` |
| `PageHeader.tsx` / `Section.tsx` | Consistent section headings + rhythm | Uses type scale (4.1) |
| `Heading.tsx` | Type scale enforcement | `level` 1-4 → token sizes |
| `Avatar.tsx` | Replace ad-hoc initials in `PresenceIndicator` | initial/icon/status dot |
| `Tabs.tsx` | No shared tabs (only feature-specific) | ARIA tablist |
| `Tooltip.tsx` | Replace `title=`/group-hover popups | framer-motion pop |
| `Accordion.tsx` | None exists | |
| `Drawer.tsx` | None (PanelDrawer is CSS-only) | fold into Modal variant or standalone |
| `Pagination.tsx` | None | |
| `Alert.tsx` | Unify `theme-alert-*` vs inline `rounded-lg p-2 text-[10px]` (profile page) | `tone` success/danger/warning/info |
| `Spinner.tsx` | Replace 30+ `animate-spin` icon usages | uses `--zozi-ring`/brand |
| `Checkbox/Radio/Switch.tsx` | None | |
| `StatusBadge.tsx` | Promote `Badge.StatusBadge` to first-class | maps status strings → tone |

### 2.8 Enforce shared Button
- `ui/Button.tsx` already maps `primary/secondary/ghost/danger/danger-outline/accent/admin/warning/info`. Add a **codemod** `scripts/codemod-button.mjs` that rewrites `<button className="theme-btn-primary …">…</button>` → `<Button variant="primary" …>…</Button>` for the 80+ raw usages, starting with `BannerCanvasEditor.tsx` (40+), `EmailTemplateManager.tsx`, `ProductCard.tsx`, `NewsletterSignup.tsx`, `AccountingPanels.tsx`. Run per-PR with review.

### 2.9 Validate 2
`npm run lint` (new ui-import rule passes) + `npx jest` (no regressions) + manual: open 3 migrated modals → consistent fade+scale, Escape closes, scroll locked.

## Phase 3 — Motion system modernization

Highest-leverage, lowest-risk phase: one wrapper fixes 70+ files.

### 3.1 Global reduced-motion (single change)
**File:** `frontend/web_app/src/app/layout.tsx` — wrap children in framer-motion `MotionConfig reducedMotion="user"` (auto-disables all `motion`/`AnimatePresence` animations for users who prefer reduced motion):

```tsx
import { MotionConfig } from "framer-motion";
// inside body, around the app-frame div:
<MotionConfig reducedMotion="user">
  <div className="relative" data-app-frame style={{ isolation: "isolate", zIndex: 10 }}>
    {/* existing children */}
  </div>
</MotionConfig>
```
This satisfies the accessibility gap the audit flagged across `Hero`, `ProductCard`, `QuickDetailModal`, `ToastSystem`, `Dropdown`, `BannerCarousel`, etc. **No per-file edits needed.**

### 3.2 App-level page transitions
**New file:** `frontend/web_app/src/app/template.tsx` (Next.js App Router re-mounts this on every navigation):

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
Respects `reducedMotion="user"` automatically (3.1). Add to storefront + panel layouts.

### 3.3 Shared Reveal/Stagger
Promote `PanelPage.tsx` `PanelAnimate`/`PanelStagger`/`ENTER_VARIANTS` into `components/ui/Reveal.tsx` + `components/ui/Stagger.tsx`. Use across storefront: product grid, category sections, offers, footer. Example:
```tsx
<Stagger stagger={0.06}><ProductCard/>…</Stagger>
```

### 3.4 Unify modal/drawer transitions
Once 2.2 lands, all modals use `Modal.tsx` transitions (fade+scale for modal, slide for drawer) — no more abrupt pops or mismatched CSS/JS animation.

### 3.5 Loading Spinner component
`components/ui/Spinner.tsx` (2.7) used by `Button isLoading` and standalone; consistent brand-colored ring, reduced-motion aware.

### 3.6 Validate 3
OS "reduce motion" ON → no entrance/hover/modal animation anywhere; OFF → smooth. `npx playwright test` smoke on home + a product page.

---

## Phase 4 — Modern look & consistency

### 4.1 Type scale + `Heading`
Define one scale (already partially in `tailwind.config.js fontSize` + `theme.ts fontSize`). Add `components/ui/Heading.tsx` enforcing `level→size` mapping. Migrate section headings (home `text-xl`, product detail `text-2xl`, cart `text-xl`, admin `text-xs uppercase`) to `Heading`.

### 4.2 Single `Container`
`components/ui/Container.tsx` (2.7). Migrate the 6+ drifting max-w usages: `HomeClient.tsx`, `products/page.tsx` (`max-w-[1400px]`), `products/[id]/page.tsx` (`max-w-7xl`), `cart/page.tsx`/`checkout/page.tsx` (`max-w-6xl`), `profile/page.tsx` (`max-w-11xl`). Footer already `max-w-11xl` → align to Container.

### 4.3 Focus-visible ring (accessibility + polish)
`globals.css:2255-2271` currently does `outline:none; box-shadow:none` for all interactive controls (no visible focus). Replace with keyboard-only ring (uses `--zozi-ring` from `tokens.css`):
```css
button:focus, a:focus, input:focus, select:focus, textarea:focus, [tabindex]:focus { outline: none; }
button:focus-visible, a:focus-visible, input:focus-visible, select:focus-visible,
textarea:focus-visible, [tabindex]:focus-visible {
  outline: 2px solid var(--color-brand);
  outline-offset: 2px;
  box-shadow: var(--zozi-ring, 0 0 0 3px rgb(50 205 50 / 0.5));
}
```

### 4.4 Alert unification
`components/ui/Alert.tsx` (2.7). Replace `theme-alert-*` usages and the inline `rounded-lg p-2 text-[10px]` alerts in `profile/page.tsx` with `<Alert tone="…">`.

### 4.5 Stat card unification
`StatCard` (currently `bg-surface`, outlier) + `PanelStatCard`/`PanelCompactStatCard` + admin inline stat cards → one `StatCard` variant on `Card`. Used by admin dashboard, supplier/logistics dashboards.

### 4.6 Consistent card treatment
After 2.5, product cards (`glass-product-card`), supplier store cards (inline), home value-prop cards (`bg-surface`), detail sections (`bg-surface-1`) all use `<Card variant="…">`.

### 4.7 Glass cross-browser
`globals.css` — add `-webkit-backdrop-filter` twins to `.glass*`, `.theme-card`, `.glass-product-card` (Safari/Chrome support). One global rule is enough:
```css
.glass, .glass-strong, .theme-card, .glass-product-card {
  -webkit-backdrop-filter: blur(14px) saturate(140%);
  backdrop-filter: blur(14px) saturate(140%);
}
```

### 4.8 Hero gradient (multi-stop, token-driven)
```css
.hero-gradient {
  background:
    radial-gradient(60% 80% at 15% 0%, color-mix(in srgb, var(--color-brand) 16%, transparent), transparent 60%),
    radial-gradient(50% 70% at 100% 10%, color-mix(in srgb, var(--color-accent) 14%, transparent), transparent 55%),
    linear-gradient(160deg, var(--color-surface-0), var(--color-surface-1) 60%, var(--color-surface-2));
}
```

### 4.9 View Transitions (progressive)
```css
@media (prefers-reduced-motion: no-preference) {
  ::view-transition-old(root), ::view-transition-new(root) {
    animation-duration: 220ms;
    animation-timing-function: cubic-bezier(0.22, 1, 0.36, 1);
  }
}
```
Opt-in at router level later via `document.startViewTransition`.

### 4.10 Validate 4
`npx jest` (incl. any `jest-axe` a11y tests) + visual QA: focus ring visible on Tab, alerts/toasts/stat cards consistent, glass renders in Safari.

---

## Phase 5 — Rollout, validation & gates

**Order:** 0 → 1 → 2 → 3 → 4. Phases 0,1,3 are low-risk and can ship quickly; Phase 2 is the long pole (migrate modals/buttons per-PR).

**Per-phase gates:**
```
cd frontend/web_app
npx jest src/__tests__/designSystemTokens.test.ts   # must pass after Phase 0
npx tsc --noEmit --skipLibCheck                      # after 1,2
npm run lint                                          # after 1,2 (ui-import rule)
npx playwright test e2e/smoke.spec.ts               # after 3,4
npx jest --testPathPattern a11y                      # if jest-axe tests exist
```

**Keep (do NOT change):** current lime/gold brand (`--color-brand`/`--color-accent`), `globals.css` existing vocabulary, `tailwind.config.js` `scaleIn`/`spring` tokens, rich `BackgroundEffect.tsx` seasonal engine, `BannerCanvasEditor` (legit canvas/SVG colors), chart palettes.

**Drop:** stray `variables.css`; dead `ToastSystem.tsx` + root `LoadingSkeleton.tsx`; `globals.css` `!important` panel overrides (after 2); dead `fadeIn`/`slideUp` keyframes; orange/purple tokens; the 3,400 generated Tailwind v3 utilities from `globals_old.css` (already excluded).

---

## File change summary

| Phase | File | Action |
|---|---|---|
| 0 | styles/comm.css, panel-modern.css, glow.css, tokens.css | restore from HEAD |
| 0 | styles/globals.css:2 | `@import "./tokens.css"` |
| 0 | app/layout.tsx:4 | import tokens.css + glow.css |
| 0 | styles/variables.css | delete |
| 1 | shared/src/theme.ts:200 | set status/semantic/glass/accent-dark vars |
| 1 | tailwind.config.js | font-size 3xs-5xs, z-index scale |
| 1 | supplier/bulk/draftUtils.ts | use token colors |
| 1 | styles/globals.css:911-976 | delete panel !important (after 2) |
| 1 | styles/globals.css:2004,2009 | delete dead keyframes |
| 1 | scripts/codemod-*.mjs | font-size + z-index codemods |
| 2 | components/ui/index.ts | barrel |
| 2 | components/ui/shared/Modal.tsx | add drawer variant + a11y |
| 2 | components/ToastSystem.tsx | delete |
| 2 | components/LoadingSkeleton.tsx | delete (use ui/) |
| 2 | components/ui/Card.tsx, Input.tsx | unify |
| 2 | components/ui/{Container,PageHeader,Section,Heading,Avatar,Tabs,Tooltip,Accordion,Drawer,Pagination,Alert,Spinner,Checkbox,Radio,Switch,StatusBadge}.tsx | new |
| 2 | 20+ modal files (list 2.2) | migrate to <Modal> |
| 2 | 80+ raw button files (list 2.8) | migrate to <Button> |
| 2 | eslint/check script | forbid raw theme-btn-*/theme-overlay outside ui/ |
| 3 | app/layout.tsx | wrap in <MotionConfig reducedMotion="user"> |
| 3 | app/template.tsx | page transition |
| 3 | components/ui/{Reveal,Stagger,Spinner}.tsx | promote/extract |
| 4 | components/ui/Heading.tsx, Container.tsx | type scale + container |
| 4 | styles/globals.css:2255-2271 | focus-visible ring |
| 4 | styles/globals.css | glass -webkit twins, hero-gradient, view-transition |
| 4 | profile/page.tsx, admin dashboard, etc. | use Alert/StatCard/Container |
