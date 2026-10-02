# Cross-Cutting Tests

Tests spanning multiple roles: design system, visual regression, panel navigation, mobile overflow, WebSocket, chatbot, scaling.

## Files

- `panel-slider-audit.spec.ts` — mobile drawer + desktop sidebar collapse for admin/supplier/logistics.
- `mobile-panel-audit.spec.ts` — iPhone 13 viewport overflow across 18 routes.
- `verify-all-panels.spec.ts` — no global header, sidebar collapses for all 3 roles.
- `products-visual-shell.spec.ts` — background effects, glass cards, no opaque white shell.
- `design-system-tokens.spec.ts` — CSS custom properties wired correctly.
- `design-system-comprehensive.spec.ts` — token wiring, glass system, z-index scale, theme switching.
- `collapse-poll.spec.ts` — sidebar collapse does not trigger infinite re-render.
- `bg-comparison-visual.spec.ts` — background removal visual quality.
- `chatbot-shopping-assistant.spec.ts` — chatbot flow: intent → product suggestion → add to cart.
- `command-center.spec.ts` — WebSocket real-time telemetry, SYNC/INITIALISING states.
- `amendment-verify.spec.ts` — order amendment request + admin verify flow.
- `country-research-all-modules.spec.ts` — country AI research across all modules.
- `country-integration-rls.spec.ts` — country RLS integration across domains.
- `country-auto-populate.spec.ts` — auto-populate "Saudi Arabia" returns SA/SAR/Asia-Riyadh.
- `countries-search.spec.ts` — countries search and selection.
- `scaling_audit.spec.ts` — API health, auth, product search, pagination, storage, Dockerfiles, Alembic.
