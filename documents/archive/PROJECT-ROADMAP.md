# Project Roadmap

## 1. Codebase audit summary

### 1.1 frontend/web_app
- Full Next.js app implementation with routes:
  - /products, /cart, /checkout, /orders, /profile, /auth, /newsletter, /notifications, /offers, /supplier, /admin, /wishlist
- UI components in `src/components`.
- API integration in `src/lib/api.ts` and shared helper modules.
- Tailwind + framer-motion + lucide-react.
- Tests in `__tests__` and Jest setup.
- Error handling docs in `ERROR_HANDLING.md`.

### 1.2 frontend/mobile_app
- Expo React Native app with base components:
  - `CartItem.tsx`, `OrderCard.tsx`, `ProductCard.tsx`, `ToastContainer.tsx`, and `ui/` subcomponents.
- Basic app-level structure: `app/`, `lib/`, `theme/`.
- Missing many page-level screens currently present in web.

### 1.3 frontend/shared
- Shared logic and helpers (non-UI): `cartHelpers`, `checkoutHelpers`, `productHelpers`, `productQuery`, `money`, `i18n`, `api-core`, `chatbot`, `theme`, `types`, `utils`.
- No UI component library yet.

### 1.4 backend
- FastAPI with folders:
  - `routers` (addresses, admin, ai, auth, cart, categories, coupons, currency, email, logistics, notifications, orders, payments, products, reviews, search, supplier, tickets, translate, wishlist)
  - `controllers` (business logic, e.g., `ai_controller`)
  - `db/models.py` (User, Product, Order, OrderItem, Review, Wishlist, Coupon, Notification, Category, PasswordResetToken, SupplierProfile)
- Payment with Stripe and Tap endpoints + webhooks.
- Role support in `User.role` (customer supplier admin).
- Utilities for auth, currency, email, file_validation, money.

## 2. Feature mapping

### 2.1 Frontend
- Existing: core web e-commerce flows, cart, checkout, orders, auth, supplier/admin base, wishlist.
- Required:
  1. responsive UI across screen sizes
  2. shared component library plus porting to mobile
  3. complete web-to-mobile parity
  4. chatbot integration on both
  5. payment gateway UI + errors
  6. global error boundaries + fallback UI
  7. complete admin analytics
  8. hierarchy roles, supplier panel, logistics, invoice management, QR scanning, recommendations, email management, product verification badges
  9. unit/integration tests for frontend

### 2.2 backend
- Existing: full router+controller coverage for core e-commerce tasks, AI suggestions, basic supplier profile.
- Required:
  1. finalize schema with invoice/returns/payout/hierarchy/QR
  2. add incomplete routers (invoices, returns, hierarchy, QR)
  3. chatbot backend if conversational or product AI already partial
  4. payment gateway robust retry & logging exists; verify and add gaps
  5. error handling utility (+ middleware)
  6. supplier/logistics/invoices/payout/return/paper verification/credibility
  7. RBAC and security hardening (auth, encryption, CSRF, auditing)
  8. tests

### 2.3 cross-platform
- Ensure shared API/logic with `frontend/shared`, i18n, currency.
- Add live locale/currency update system.
- implement e2e across both platforms.

## 3. Implementation details (per-step)

### 3.1 frontend shared componentization
- Build reusable components in `frontend/shared`:
  - `Button`, `Input`, `Card`, `Modal`, `Toast`, `Loader`, `Badge`, `ScreenLayout`
- Align with design tokens in `shared/theme.ts`.
- Platform adaptors for web/mobile UI (React Native, CSS-in-JS/Tailwind).

### 3.2 mobile_app per-page porting
- Add route screens mapping:
  - Products (listing + filters + detail), Cart, Checkout, Orders, Profile, Auth, Wishlist, Notifications, Supplier, Admin.
- A `ProductCard` that matches web visual / API expectation.
- create `app/(main)` group and use `shared` utilities.

### 3.3 ai/chatbot feature
- Web: add `ChatbotPanel` page/component.
- Mobile: include screen + persistent button.
- Backend call to `/ai/suggest` and `/ai/generate-angles`.

### 3.4 Payments
- Web checkout form improvements + 3D-secure handling and retry path.
- Mobile same flow with shared API wrapper.

### 3.5 admin/supplier/logistics/invoice
- Web admin dashboards (metrics: total sales, supplier approvals, payouts, returns, shipments).
- Supplier panel for product approvals, KYC status.
- Logistics panel for route select, delivery status, tracking.
- Invoice model + endpoints + UI.

### 3.6 security + RBAC
- Centralize role checks with dependency `get_current_user`.
- Add `is_admin`, `is_supplier`, `is_logistics` decorators.
- Add `AuditLog` model + `db/controllers/audit_controller`.

### 3.7 testing
- unit tests in shared web/mobile.
- integration tests using Jest + react-testing-library + pytest.
- e2e scripts with Playwright and Detox.

## 4. Schedule
- Stage 1: Audit + core shared system (1 week)
- Stage 2: Full web/mobile parity + logistics/invoices (2 weeks)
- Stage 3: Hardening + tests + deployment (2 weeks)

## 5. Next actions
- Prioritize which scope first (payments vs admin vs mobile parity)
- Keep shared focused on logic/contracts/brand modules (`frontend/shared/src` + `frontend/shared/src/logo`) and implement UI in app-owned folders.
- Add `backend/db/models` entries for missing features
- Add security middleware and test harness

## 6. Repository file location of this plan
- `PROJECT-ROADMAP.md` (this file)

## 7. Master Job List - Detailed To Do and How
> ⚡ Codebase audit confirmed: core web/mobile features implemented, partial cross-platform UI library, missing returns/recommendations. See 7.1-7.4 status markers.

### 7.1 🎨 Frontend
- 1. Make all UI responsive across devices. (Status: implemented for current pages; ongoing maintenance)
  - To do: audit each page in `frontend/web_app/src/app/*` for mobile viewport. Add Tailwind responsive classes and/or CSS breakpoints. Use Browser DevTools and Expo device simulator.
  - How: create a `frontend/shared/src/theme.ts` responsive token map; apply to web and mobile via layout components.

- 2. Keep strict boundary between shared logic and app-owned UI. (Status: now aligned; continue enforcing)
  - To do: compare directories and keep only cross-app logic/contracts in `frontend/shared/src`; keep render/UI wrappers in `frontend/web_app/src/components` and `frontend/mobile_app/components`.
  - How: centralize non-visual logic in `frontend/shared/src` (+ brand assets in `frontend/shared/src/logo`), and keep UI rendering in each app.

- 3. Ensure consistent design and functionality across web and mobile.
  - To do: define design tokens and branding in `frontend/shared/src/theme.ts`; use on both projects.
  - How: enforce through style checks and cross-platform component contracts.

- 4. Complete mobile app UI and feature parity with web.
  - To do: implement pages from web (`products`, `cart`, `checkout`, `orders`, `profile`, `wishlist`, `notifications`, `offers`, `supplier`, `admin`) in mobile app.
  - How: set up `mobile_app/app` navigator, copy web routes as Expo screens, reuse `shared` helpers.

- 5. Integrate chatbot feature into both web and mobile.
  - To do: add chatbot UI in web (component + route) and mobile (screen + action button). Hook to backend `/ai` routes.
  - How: use `frontend/shared/src/chatbot.ts` and implement front-end state + sending logic in platform components.

- 6. Implement payment gateway UI and error handling.
  - To do: complete checkout forms in both apps with payment method selection (card, Tap, Stripe). Add success/failure states.
  - How: use shared API wrappers and an error boundary component.

- 7. Add global error boundaries and fallback UI.
  - To do: implement React `ErrorBoundary` in web and RN equivalent in mobile.
  - How: wrap root layout with boundary and provide a fallback screen.

- 8. Complete admin panel UI with analytics dashboard.
  - To do: add admin dashboards in web and mobile for sales, orders, suppliers, complaints.
  - How: reuse API analytics endpoints in `backend/routers/admin.py`.

- 9. Implement hierarchy system for admin control.
  - To do: in UI allow assignment of roles, permissions, zones.
  - How: use a role management page with calls to backend RBAC endpoints.

- 10. Add supplier panel UI integration.
  - To do: supplier product updates, KYC status, payout views.
  - How: wire to `backend/routers/supplier.py` endpoints and use shared model.

- 11. Add logistics and distribution channel UI.
  - To do: implement order tracking page and channel assignment.
  - How: connect to `backend/routers/logistics.py`.

- 12. Implement invoices management UI (supplier → logistics → customer). (Status: partial; endpoint exists, UI is being finalized)
  - To do: create invoice screens in customer and supplier dashboards.
  - How: add API endpoints + UI forms for invoice creation/approval.

- 13. Add barcode/QR code scanning UI for transactions. (Status: implemented) 
  - To do: mobile: use Expo BarCodeScanner. Web: use `jsQR` or `zxing` with getUserMedia.
  - How: implement scanner component and verify codes with backend endpoint.

- 14. Implement customer preference algorithm UI (recommendations, browsing history). (Status: not implemented; priority gap)
  - To do: display recommended products, history sidebar in UI.
  - How: call new endpoint `/preferences` and match with user actions.

- 15. Add email management UI (newsletter, notifications, verification). (Status: implemented)
  - To do: panel for campaigns, templates, logs.
  - How: use backend `email` router and share components.

- 16. Implement product verification UI for specifications.
  - To do: show product spec checklist and verified badge.
  - How: from `Product.is_verified` and admin validation flow.

- 17. Add supplier credibility badge system UI.
  - To do: show supplier score, verified status, rating stars.
  - How: include `SupplierProfile.verification_status` and product vendor info.

- 18. Write unit and integration tests for all frontend components.
  - To do: for each shared/web/mobile component add Jest tests and integration flow tests.
  - How: run `npm test` + CI steps.

### 7.2 ⚙️ Backend
- 1. Finalize database schema and management in `backend/db`. (Status: mostly done; `ReturnRequest` and `HierarchyRole` pending)
  - To do: add models `Invoice`, `InvoiceItem`, `Shipment`, `ReturnRequest`, `SupplierPayout`, `HierarchyRole`, `QRScan`, `AuditLog`.
  - How: update `models.py`, migration scripts in `alembic/versions`, and seed data.

- 2. Complete API routers in `backend/routers`. (Status: major coverage exists; add `returns` + `recommendations`)
  - To do: confirm all operations on User, Product, Cart, Orders, Admin, Supplier, Logistics.
  - How: add missing endpoints and include in `main.py`.

- 3. Implement chatbot backend service.
  - To do: extend `services/ai_service.py` to include conversational endpoints and safeguard.
  - How: add controllers for chat history, user context.

- 4. Integrate payment gateway backend service with retry and logging.
  - To do: test Pay/Gap flows (Stripe/Tap), add retries for timeout/failure.
  - How: use `retry` logic in `controllers/payments_controller.py`.

- 5. Add error handling utilities in `backend/utils`.
  - To do: add `error.py` with `APIError`, `audit_error`, `log_exception`.
  - How: include middleware in `main.py` for `HTTPException` and `ValidationError`.

- 6. Complete supplier panel backend integration and testing.
  - To do: endpoints to approve products, payouts, profile updates.
  - How: add tests to `backend/tests/test_supplier.py`.

- 7. Implement logistics integration (location‑wise, distribution channels).
  - To do: add `LogisticsHub`, `Route`, `Shipment` model and API.
  - How: make syncing with orders and supplier hub.

- 8. Complete invoices management backend (supplier → logistics → customer).
  - To do: endpoints for invoice create/retrieve/update, link with orders.
  - How: use generated PDFs maybe optional, store `invoice_url`.

- 9. Add barcode/QR code scanning backend support.
  - To do: endpoint to validate scan token and unlock order.
  - How: decode payload, check order status.

- 10. Implement customer preference algorithm backend.
  - To do: keep `user_activity` table and recommendation endpoints.
  - How: run daily job in `services` to compute `top_products`.

- 11. Add email management backend service.
  - To do: `utils/email_service.py` has basics; add newsletter schedulers and templates.
  - How: integrate SMTP/Ethereal and webhooks.

- 12. Implement papers verification system for suppliers.
  - To do: upload docs, admin review API, status updates.
  - How: use `SupplierProfile` fields and new endpoint.

- 13. Add supplier payout verification system.
  - To do: track payout requests, statuses, bank details.
  - How: new model + route + admin approval.

- 14. Implement customer return policy management.
  - To do: model policies + create return request flow.
  - How: connect with orders and product states.

- 15. Add product specification verification backend.
  - To do: save verified specs, manage flags by admin.
  - How: in `products` model include `spec_checked` metadata.

- 16. Implement supplier credibility badge system backend.
  - To do: compute score via ratings, fulfillment, KYC status.
  - How: use worker or query, expose in endpoints.

- 17. Complete admin panel backend support with analytics dashboard.
  - To do: endpoints with summaries (`/admin/stats`).
  - How: aggregate orders, revenue, user growth, overdue tasks.

- 18. Implement role‑based access control for hierarchy system.
  - To do: middleware and API guards utilizing `User.role` and new `roles` table.
  - How: dependency in routers and tests.

- 19. Add security measures.
  - To do: JWT auth, password hashing, CSRF (for web), audit logging.
  - How: integrate `python-jose`, `passlib`, secure headers, logger.

- 20. Write unit and integration tests for backend components.
  - To do: each router + controller.
  - How: `pytest --cov`, test data fixtures.

### 7.3 🔗 Cross‑Platform / General
- 1. Ensure seamless integration between web and mobile platforms.
  - To do: shared API contract in `frontend/shared/src/api-core.ts` and `types.ts`.
  - How: enforce same request/response shape in both apps.

- 2. Implement language, country, and currency JSON file.
  - To do: add `shared/locales`, and `currency.json`.
  - How: dynamic load by user locale.

- 3. Add live update system for multilingual and multi‑currency support.
  - To do: endpoints for labels/values, `useSWR` with stale-while-revalidate.
  - How: update UI instantly at runtime.

- 4. Sync frontend and backend features for consistent behavior.
  - To do: one source of truth feature matrix.
  - How: tests and documentation.

- 5. Conduct end‑to‑end testing across web and mobile.
  - To do: Playwright for web, Detox for mobile.
  - How: workflows: login, cart, checkout, order tracking.

- 6. Ensure chatbot, payment gateway, and admin panel work identically across platforms.
  - To do: cross-platform test scenarios.
  - How: E2E and performance checks.

### 7.4 🛠️ Additional Recommendations
- Performance Optimization:
  - Add caching layer (Redis) and query indexing.
- Monitoring & Logging:
  - central log collector + dashboards.
- CI/CD Pipeline:
  - GitHub Actions with build/test/deploy.
- Documentation:
  - API and UX docs.
- Scalability & Cloud Readiness:
  - Docker + deployment scripts.

## 8. Detailed comparison: frontend/web_app vs frontend/mobile_app vs frontend/shared

### 8.1 common coverage
- `web_app`: full-featured product discovery and checkout web experience.
- `mobile_app`: core e-commerce components exist (product cards, cart, orders) but pages are sparse.
- `shared`: non-UI logic and helpers only; no complete UI component set yet.

### 8.2 UI components
- `web_app/src/components`: complete card, listing, filter, nav, forms, modals, skeletons, pages.
- `mobile_app/components`: limited templates (CartItem, ProductCard, OrderCard), lacks pages and admin/supplier layouts.
- `shared/src/components`: intentionally removed; shared now hosts logic/contracts + `shared/src/logo` brand module only.

### 8.3 data/logic utility
- `shared/src`: strong foundation for cart, checkout, products, money, i18n, API core, chatbot logic.
- `web_app` uses these in `src/lib` + 3rd-party hooks; mostly UI glue.
- `mobile_app` should ingest `shared` and implement navigation/presentation.

### 8.4 navigation and routing
- `web_app/src/app`: fully routed with nested sections and filters screens.
- `mobile_app/app`: only basic structure; needs complete tab/stack for web features.
- `shared`: no routing (platform-specific), but route Semantics should align.

### 8.5 feature parity gaps (high priority)
- Missing mobile screens: admin, supplier portal, notifications settings, analytics, lifestyle pages, full checkout details, search facets.
- Shared UI wrappers are intentionally out of scope; keep shared focused on logic/contracts while maintaining common theme tokens and logo assets.
- Shared backend integration: all API endpoints used by web should be invoked from mobile too.

### 8.6 improvement tasks
1. keep `frontend/shared/src` focused on cross-app logic/contracts and shared `frontend/shared/src/logo` assets.
2. maintain app-owned UI in `frontend/web_app/src/components` and `frontend/mobile_app/components`.
3. implement missing mobile screens using shared logic modules (not shared UI wrappers).
4. port and validate `web_app` route behavior (search, filter, product detail, cart, checkout, orders, profile, admin, supplier) into `mobile_app` flows.
5. test consistency for chatbot, payment, notifications, and admin operations across devices.



