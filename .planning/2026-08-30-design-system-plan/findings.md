# Design System Plan Findings

## Architecture Benchmark
- `ARCHITECTURE_DIAGRAM.md` is the authoritative architecture source and ends with 325 laws.
- Frontend laws visible in the benchmark: Tailwind + CVA + `tailwind-merge` + `clsx`, route groups by actor, App Router conventions (`page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`), design tokens in Tailwind/global CSS, frontend knows backend through API only, errors should flow to toasts/boundaries.
- Architecture constraints for the design plan: keep design-system work in `frontend/web_app/src/components/ui`, `frontend/web_app/src/styles`, `frontend/web_app/src/theme`, `frontend/web_app/tailwind.config.*`, and actor-specific shells/components; do not recommend backend/domain violations for visual-only work.
- Completed chunked top-to-bottom read of `ARCHITECTURE_DIAGRAM.md`.
- Key law anchors for final document:
  - Lines 32-44: frontend stack is Next.js 16.3.1, React 18.3.1, TS strict, Tailwind 3.4.19, CVA, `clsx`, `tailwind-merge`, lucide-react, framer-motion.
  - Lines 252-276: frontend layout: `web_app/src/app`, `src/components`, `src/hooks`, `src/lib`, `src/services`, `src/theme`, `src/styles`, plus `mobile_app` and `shared`.
  - Lines 536-570: frontend action flow goes through Zustand/API client, backend module router, auth/RBAC, domain service, DB.
  - Laws 168-186: monorepo structure, RSC/client component split, API proxy, Tailwind/CVA styling, error handling, actor route groups, component/hook/lib/service/theme/type/utils locations, and build requirement.
  - Laws 195-200: shared package must stay cross-platform; `permissions.ts` is generated; money/i18n/theme helpers belong in shared only when platform agnostic.

## Design Investigation
- `_design_investigation` exists and contains 19 files: current/old global CSS, Tailwind snapshots, old/current glow/banner/ticker styles, supplier editor buttons, HUD/glow/print snippets, migration reports, and an existing final design plan.
- `DESIGN_PLAN_FINAL.md` recommends a phased plan: restore deleted style contracts (`comm.css`, `panel-modern.css`, `glow.css`, `tokens.css`), reconcile tokens, consolidate component primitives, add global reduced motion, create app transitions, and modernize with glass/focus/gradient polish.
- `DESIGN_MIGRATION_REPORT.md` is more bug-focused: it identifies deleted CSS contracts, undefined utilities/classes, missing token wiring, missing `--color-background`, missing `max-w-450`, disabled comm/panel/glow styling, and flat gradient aliases in the current globals.
- Old/current Tailwind snapshots show the current direction is already token-based: brand lime/gold, surface tokens, glass tokens, Fraunces display + Sora body, Tailwind colors mapped to CSS vars, and safelisted alpha utility variants. `tailwind_full_push.js` adds RGB alpha-variable mappings and a large safelist; `tailwind_current.js` is leaner but lacks some modern repairs.
- `tokens_old.css` is not the desired full token file; it flattens gradients to brand-only aliases and should not be copied as-is. Its useful parts are logo/color anchors and the reminder that gradients need real multi-stop definitions.
- `comm_old.css` contains a strong communication workspace interaction model: five-zone grid, collapsible rail/context widths, ambient dotted drift layer, active row marker, unread badge pop, hover quick actions, composer expansion on focus/drag, presence pulse, stage/message enters, responsive sheet behavior, and reduced-motion handling.
- `panel_modern_old.css` contains reusable panel polish: collapsible-panel hover/focus treatment, panel-card and compact stat transitions, elevated glass panel, density transitions, quick-action reveal, brand divider, icon glow, live dot pulse, subtle ambient panel background, mobile radius adjustments, and reduced-motion handling.
- `glow_current.css` and `glow_from_git.css` match. They define token-friendly backgrounds for partner hero/card glow, footer glow, tracking glow, label gradient with print fallback, and dark logo background.
- `hud_from_git.css`, `editor_buttons_from_git.css`, and `ticker_bar_current.css` preserve small moved style contracts for command-center HUD keyframes, supplier editor buttons, and marquee ticker animation.
- `banner_effects_current.css` and `print_css_from_git.css` are empty; do not plan to preserve content from them unless current frontend imports prove otherwise.
- `fence_lines.txt` is an index of code-fence line numbers from a prior generated document, not a design source.
- `globals_current.css` findings:
  - Line 1 imports only Tailwind; `tokens.css` is not imported.
  - Lines 28-122 define dark-first root tokens: ZOZI logo colors, brand `#32CD32`, accent `#FFD700`, black surfaces, glass variables, status colors, semantic colors, card radius/shadows, hero gradient, and background texture.
  - Lines 51-68 flatten most named gradients to `var(--color-brand)`, so the app has gradient names but not real multi-stop gradient depth at the token level.
  - Lines 130-217 define light mode with brand `#2f9440`, accent `#f2c94c`, tinted green surfaces, white glass variables, refined shadows, and light background texture. This is worth keeping as the default modern direction for light theme.
  - Lines 267-333, 423-451, 524-1142, and 1327-1987 hold the app's real design vocabulary: glass, theme-card, theme-panel, theme-elevated, theme-input, theme buttons, chips, alerts, overlays, product/search shells, nav, modal shell, empty state, glass-product-card, dropdown, seasonal banner elements, status/priority pills, light-mode polish.
  - Lines 879-1011 duplicate and override earlier button definitions, which makes future styling fragile.
  - Lines 911-976 apply broad admin/supplier/logistics button/form/card fallbacks; these are useful for emergency consistency but should be replaced by shared primitives and then removed.
  - Lines 1998-2253 define shimmer, fadeIn, slideUp, float/drift, seasonal/celebration keyframes, aurora, reduced-motion for decorative classes, button spinner, and spin.
  - Lines 2255-2271 remove focus outlines/shadows/border color from focus and focus-visible. This is an accessibility and polish bug; replace with keyboard-only focus visible using `--zozi-ring`.
  - Lines 2273-2311 contain helpful border and RTL helper rules to keep.

## Frontend Audit
- `frontend` contains web, shared, and mobile apps. The design plan should focus first on `frontend/web_app`, then mention shared/mobile only where design tokens or shared UI primitives cross app boundaries.
- The web app includes screenshots/test artifacts plus source under `frontend/web_app/src/app`, `src/components`, `src/components/ui`, `src/theme`, and `src/styles`.

## Synthesis Notes
Pending.
