# ZOZI Marketplace — Codebase Map

> **Purpose:** Single reference for every major folder and file in the ZOZI e-commerce platform, grouped by domain and feature, with short descriptions of what each area does and how it fits into the overall system.

---

## Table of Contents

1. [Top-Level Structure](#top-level-structure)
2. [Domain: Core Platform](#domain-core-platform)
3. [Domain: Authentication & Identity](#domain-authentication--identity)
4. [Domain: Products & Catalog](#domain-products--catalog)
5. [Domain: Cart & Checkout](#domain-cart--checkout)
6. [Domain: Orders & Fulfillment](#domain-orders--fulfillment)
7. [Domain: Payments & Finance](#domain-payments--finance)
8. [Domain: Logistics](#domain-logistics)
9. [Domain: Suppliers](#domain-suppliers)
10. [Domain: Customers](#domain-customers)
11. [Domain: Communications](#domain-communications)
12. [Domain: Admin & Governance](#domain-admin--governance)
13. [Domain: HR & Employees](#domain-hr--employees)
14. [Domain: Geography & Country](#domain-geography--country)
15. [Domain: AI & Automation](#domain-ai--automation)
16. [Domain: Media & Uploads](#domain-media--uploads)
17. [Domain: Security & Compliance](#domain-security--compliance)
18. [Domain: Notifications & Realtime](#domain-notifications--realtime)
19. [Domain: Reviews & Ratings](#domain-reviews--ratings)
20. [Domain: Tickets & Support](#domain-tickets--support)
21. [Domain: Returns & Disputes](#domain-returns--disputes)
22. [Domain: Treasury & Payouts](#domain-treasury--payouts)
23. [Domain: Search & Discovery](#domain-search--discovery)
24. [Domain: Promotions & Marketing](#domain-promotions--marketing)
25. [Domain: Infrastructure & Observability](#domain-infrastructure--observability)
26. [Additional Backend Structure](#additional-backend-structure)
27. [Domain: Frontend (Web App)](#domain-frontend-web-app)
28. [Domain: Frontend (Mobile App)](#domain-frontend-mobile-app)
29. [Domain: Shared Packages](#domain-shared-packages)
29. [Feature: E-Commerce Flow](#feature-e-commerce-flow)
30. [Feature: Admin Operations](#feature-admin-operations)
31. [Feature: Supplier Operations](#feature-supplier-operations)
32. [Feature: Logistics Partner Flow](#feature-logistics-partner-flow)
33. [Feature: Chat & Messaging](#feature-chat--messaging)
34. [Feature: Real-Time Features](#feature-real-time-features)
35. [Appendix: Router Auto-Discovery](#appendix-router-auto-discovery)
36. [Appendix: Key Patterns](#appendix-key-patterns)

---

## Top-Level Structure

```
zozi/
├── backend/                  # FastAPI + Python backend
│   ├── main.py               # App entry, router auto-discovery, health checks
│   ├── lifespan.py           # Startup/shutdown hooks (Alembic, services, listeners)
│   ├── middleware/           # HTTP middleware pipeline (CORS, CSRF, rate limit, geo, etc.)
│   ├── routers/              # API route definitions (auto-discovered)
│   ├── controllers/          # Thin delegators — validate input, call services
│   ├── services/             # Business logic layer
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas.py            # Legacy Pydantic schemas
│   ├── db/                   # Database engine, session, migrations, seed data
│   ├── utils/                # Cross-cutting utilities (auth, crypto, RLS, logging, etc.)
│   ├── providers/            # External integrations (payments, storage, media, AI, etc.)
│   ├── events/               # Domain events (payment confirmed, etc.)
│   ├── jobs/                 # Background tasks (fraud monitoring, AI, threat feeds)
│   ├── dependencies/         # FastAPI Depends helpers (COI, country, fraud)
│   ├── core/                 # Core route contracts / base modules
│   └── uploads/              # Local file upload storage
│
├── frontend/
│   ├── web_app/              # Next.js 15 web application
│   ├── mobile_app/           # React Native / Expo mobile app
│   └── shared/               # @zozi/shared — platform-agnostic code
│
├── docs/                     # Documentation
├── scripts/                  # Operational scripts
├── monitoring/               # Monitoring configs
├── nginx/                    # Reverse proxy configs
├── tests/                    # Top-level tests
├── docker-compose.yml        # Local Docker orchestration
├── railway.toml              # Railway deployment config
└── vercel.json               # Vercel deployment config
```

---

## Domain: Core Platform

**Feature:** Application bootstrap, configuration, health, middleware pipeline, database, and shared utilities.

### `backend/main.py`
- FastAPI app factory, router auto-discovery, health endpoints (`/health`, `/health/deps`, `/health/ready`), global exception handler, static uploads mount, WebSocket routes for user chat and admin background jobs.

### `backend/lifespan.py`
- Modular startup/shutdown hooks: ensures DB tables exist, runs Alembic migrations in dev/test, loads role permissions, registers service side-effects, wires event listeners.

### `backend/middleware/orchestrator.py`
- Single entry point that layers all middleware in order: Foundation (GZip, CORS, IP extraction, request ID, API versioning) → Security (headers, impossible travel, fraud detection/scoring, CSRF) → Rate Limiting → Geo & Country → Observability (logging) → PCI Compliance.

### `backend/utils/config.py`
- Central settings management (env vars, BASE_DIR, database URL, app env, debug flags, feature flags).

### `backend/utils/logging_config.py`
- Structured logging setup via `structlog`, request-scoped log context.

### `backend/utils/error_handler.py`
- Global error handler wrapping Sentry, standardized error response formatting.

### `backend/utils/versioning.py`
- API version prefix management (`VERSION_PREFIX`, `get_version_path`, `get_active_versions`).

### `backend/utils/tracing.py`
- OpenTelemetry distributed tracing setup.

### `backend/utils/prometheus_setup.py`
- Prometheus metrics exporter initialization.

### `backend/db/database.py`
- SQLAlchemy engine creation, SQLite/PostgreSQL config, connection pooling, schema translation map, performance pragmas for SQLite.

### `backend/db/base.py`
- Declarative base class for all ORM models.

### `backend/db/session.py`
- Session factory and `get_db` dependency for FastAPI.

### `backend/db/transaction.py`
- Transaction management helpers.

### `backend/db/init_db.py`
- Database initialization logic.

### `backend/db/create_tables.py`
- Table creation helper (called from lifespan if DB is fresh).

### `backend/db/seed.py`
- Seed data insertion (countries, categories, etc.).

### `backend/db/models.py`
- Central model registry (imports all models so Alembic can detect them).

### `backend/db/migrations/`
- Alembic migration scripts and config.

### `backend/schemas.py`
- Legacy Pydantic schemas for products, users, orders (being superseded by per-domain schemas in controllers).

---

## Domain: Authentication & Identity

**Feature:** User registration, login, JWT/OAuth2, TOTP, password reset, email verification, token revocation, device tracking.

### `backend/models/user.py`
- `User` model (core.users): email, username, hashed_password, role, staff fields, referral_code, TOTP, address_book, relationships to products, cart, orders, reviews, wishlist, devices, referrals.
- `UserDevice`, `Referral`, `ReferralPointEvent`, `PasswordResetToken`, `EmailVerificationToken`, `RevokedToken`, `UserLoginHistory`.

### `backend/routers/auth.py`
- Login, logout, token refresh, registration, password reset, email verification endpoints.

### `backend/controllers/admin/auth.py`
- Admin authentication controller.

### `backend/services/security/auth_service.py`
- Core auth logic: password hashing, token creation/validation, session management.

### `backend/services/security/auth_write_service.py`
- Write-side auth operations: password changes, TOTP enable/disable.

### `backend/services/security/triple_auth.py`
- Multi-factor authentication orchestration.

### `backend/services/security/mobile_auth_service.py`
- Mobile-specific auth flows.

### `backend/services/security/biometric_auth.py`
- Biometric authentication support.

### `backend/services/security/qr_auth.py`
- QR code-based authentication.

### `backend/services/identity/iam_service.py`
- Identity & Access Management: role assignment, permission checks.

### `backend/services/identity/identity_admin_service.py`
- Admin identity operations.

### `backend/providers/auth/`
- Authentication provider implementations (OAuth, LDAP, etc.).

### `backend/utils/auth.py`
- JWT utilities, password hashing, token revocation, Redis-backed session store, `_get_redis`.

### `backend/utils/encryption.py`
- Encryption utilities (at-rest data, address book).

### `backend/utils/kms_encryption.py`
- AWS KMS integration for envelope encryption.

### `backend/utils/secrets_manager.py`
- Secrets management (AWS SSM, env vars).

### `backend/utils/csrf.py` / `csrf_utils.py`
- CSRF token generation and validation.

### `backend/middleware/csrf_middleware.py`
- CSRF protection middleware.

### `backend/middleware/device_binding_middleware.py`
- Device fingerprint binding for sessions.

### `backend/middleware/zero_trust_auth.py`
- Zero-trust auth enforcement.

### `backend/middleware/webhook_verification.py`
- Webhook signature verification.

### `backend/middleware/webhook_ip_whitelist.py`
- Webhook IP allowlisting.

### `frontend/web_app/src/lib/api/auth.ts`
- Frontend auth client: token storage, silent refresh, session state.

### `frontend/web_app/src/hooks/`
- `useAuth.tsx`, `useAuthModal.ts`, `useSendMessage.ts`, etc.

### `frontend/web_app/src/app/login/`, `register/`, `reset-password/`, `verify-email/`
- Authentication page routes.

---

## Domain: Products & Catalog

**Feature:** Product CRUD, categories, variants, search, moderation, verification, banners, pricing, inventory, AI descriptions.

### `backend/models/products.py`
- `Category` (commerce.categories): name, slug, parent_id, path (materialized path), depth, commission_rate, country_code.
- `Product` (commerce.products): name, slug, description, ai_description, sku, barcode, price, compare_price, cost_price, stock, low_stock_threshold, weight, dimensions, materials, images, category_id, tags, attributes, supplier_id, country_code, is_active, is_featured, is_verified, moderation_status, brand, color, sizes, rating, sales_count, discount dates.
- `ProductVariant`, `Review`, `WishlistItem`, `Wishlist`, `ProductVideo`, `VideoAnalytics`, `ProductFilterMetadata`, `ProductFilterOption`.

### `backend/routers/products.py.bak` → migrated to `routers/admin_products_routes.py`, `core_products_routes.py.bak`, `supplier_products_upload.py`, `supplier_products.py`
- Product API routes (admin, public, supplier).

### `backend/controllers/products/products_controller.py`
- Product CRUD controller.

### `backend/controllers/admin/products_controller.py`
- Admin product management controller.

### `backend/controllers/supplier/supplier_products_upload_controller.py`
- Supplier product upload and management controller.

### `backend/services/products/products_service.py`
- Product business logic: listing, filtering, detail, stock checks.

### `backend/services/products/product_verification_service.py`
- Product verification workflow.

### `backend/services/catalog/`
- `product_service.py`, `products_write_service.py`, `product_admin_read_service.py`, `product_admin_write_service.py`, `product_moderation_service.py`, `product_verification_write_service.py`, `category_service.py`, `category_admin_read_service.py`, `category_admin_write_service.py`, `advanced_filter_service.py`, `advanced_search_engine.py`, `banner_service.py`, `banner_write_service.py`, `variant_config_service.py`, `visual_search_service.py`, `bulk_ops_write_service.py`.

### `backend/controllers/catalog/`
- Catalog-specific controllers (delegators to services).

### `backend/models/catalog/`
- Catalog-specific model extensions.

### `backend/routers/admin_products_routes.py`
- Admin product routes.

### `backend/routers/admin_banners_routes.py`
- Banner management routes.

### `backend/routers/store_products_routes.py.bak`
- Store-level product routes.

### `backend/providers/media/`
- Media processing providers (image optimization, background removal).

### `backend/providers/image/`
- Image manipulation providers.

### `backend/providers/voice/`
- Voice-to-product AI providers.

### `frontend/web_app/src/app/products/`
- Product catalog page.

### `frontend/web_app/src/components/ProductCard.tsx`, `ProductGrid.tsx`, `CategoryGrid.tsx`, `CategorySidebar.tsx`
- Product display components.

### `frontend/web_app/src/components/QuickViewModal.tsx`, `QuickDetailModal.tsx`
- Quick product view modals.

### `frontend/web_app/src/components/supplier/`
- Supplier product upload components: `SmartMediaUpload`, `SmartPricingPanel`, `SmartVariantMatrix`, `PhotoEditorModal`, `VoiceProductInput`, `VoiceToCatalogPipeline`, `AIResultsModal`, `ProductPublishSuccess`, `ProductSpecsSelector`.

### `frontend/web_app/src/lib/productCardModel.ts`
- Product card data model.

### `frontend/web_app/src/lib/variantConfig.ts`
- Variant configuration utilities.

---

## Domain: Cart & Checkout

**Feature:** Shopping cart, cart items, checkout flow, delivery options, order creation.

### `backend/models/orders.py`
- `Cart`, `CartItem` (commerce schema): user_id, product_id, quantity, selected_variant, added_at.

### `backend/routers/core_cart_routes.py.bak`
- Cart routes (migrating).

### `backend/controllers/commerce/`
- Commerce controllers including cart.

### `backend/services/orders/cart_service.py`
- Cart read operations: get cart, calculate totals, validate stock.

### `backend/services/orders/cart_write_service.py`
- Cart mutations: add item, update quantity, remove item, clear cart.

### `backend/services/commerce/cart_service.py`, `cart_controller_service.py`
- Commerce-level cart services.

### `backend/services/core/cart_service.py`
- Core cart service (legacy/delegator).

### `backend/services/commerce/coupons_read_service.py`, `coupons_write_service.py`, `coupons_service.py`
- Coupon validation and application in cart.

### `backend/services/commerce/referrals_service.py`
- Referral code application in cart/checkout.

### `backend/services/commerce/flash_sale_service.py`, `flash_sale_controller_service.py`, `flash_sale_write_service.py`
- Flash sale pricing in cart.

### `backend/services/commerce/promotion_engine_service.py`, `promotion_service.py`, `promotion_points_service.py`, `promotion_bogo_service.py`
- Promotion engine: BOGO, points, stackable discounts.

### `frontend/web_app/src/app/cart/`
- Cart page route.

### `frontend/web_app/src/lib/cartStore.ts`
- Zustand cart state store.

### `frontend/web_app/src/lib/cartUtils.ts`
- Cart calculation utilities.

### `frontend/web_app/src/app/checkout/`
- Checkout flow page.

### `frontend/web_app/src/lib/checkoutConfig.ts`, `checkoutHelpers.ts` (shared)
- Checkout configuration and helpers.

### `frontend/web_app/src/lib/deliveryStore.ts`
- Delivery option state.

---

## Domain: Orders & Fulfillment

**Feature:** Order creation, status transitions, order items, shipments, tracking, delivery, returns, disputes.

### `backend/models/orders.py`
- `Order` (commerce.orders): order_number, customer_id, user_id, status, payment_status, payment_method, provider, intent_id, subtotal, shipping_fee, tax, vat, discount, total, coupon_code, fraud_score, currency, shipping_address/city/country/postal, tracking_number, selected_partner_id, estimated_delivery, paid_at, country_code, is_deleted.
- `OrderItem` (commerce.order_items): order_id, product_id, variant_id, quantity, price, total.
- `OrderLogisticsAllocation`, `ReturnRequest`.

### `backend/models/logistics.py`
- `LogisticsPartner`, `LogisticsPartnerProfile`, `LogisticsPartnerServiceArea`, `LogisticsPricingProfile`, `LogisticsVehicleRule`, `Shipment`, `ShipmentEvent`, `LogisticsCategoryPricingRule`.

### `backend/routers/orders.py.bak` → migrated to `routers/core_orders_routes.py.bak`, `admin_orders_routes.py`, `supplier_orders.py`, etc.
- Order API routes.

### `backend/controllers/orders/orders_controller.py`
- Order CRUD controller.

### `backend/controllers/orders/logistics_controller.py`
- Order logistics controller.

### `backend/controllers/orders/disputes_controller.py`
- Dispute management.

### `backend/controllers/orders/returns_controller.py`
- Return request management.

### `backend/controllers/orders/logistics_partner_controller.py`
- Logistics partner order operations.

### `backend/services/orders/orders_service.py`
- Order read logic: listing, detail, status history, customer/order lookup.

### `backend/services/orders/orders_write_service.py`
- Order mutations: create, update status, cancel, fulfill.

### `backend/services/orders/fulfillment_service.py`
- Fulfillment orchestration: payment confirmation → allocate logistics → create shipment → notify.

### `backend/services/orders/bulk_order_service.py`
- Bulk order operations.

### `backend/services/orders/order_tracking_service.py`
- Tracking number generation and tracking event streaming.

### `backend/services/orders/returns_service.py`, `returns_write_service.py`
- Return processing: approval, refund, restock.

### `backend/services/orders/disputes_service.py`, `disputes_write_service.py`
- Dispute lifecycle.

### `backend/services/orders/logistics_service.py`
- Order-to-logistics allocation.

### `backend/services/orders/logistics_partner_service.py`
- Logistics partner order operations.

### `backend/services/orders/admin_orders_read_service.py`, `admin_orders_write_service.py`
- Admin order oversight.

### `backend/services/orders/ghost_watchdog.py`
- Ghost order detection (suspicious/fraudulent orders).

### `backend/services/orders/returns_controller_service.py`
- Legacy returns controller service.

### `frontend/web_app/src/app/orders/`, `orders/[id]/`
- Customer orders list and detail pages.

### `frontend/web_app/src/app/returns/`, `returns/[id]/`
- Returns management pages.

### `frontend/web_app/src/app/tracking/[id]/`
- Order tracking page.

### `frontend/web_app/src/lib/orderHelpers.ts` (shared)
- Order formatting and status helpers.

---

## Domain: Payments & Finance

**Feature:** Payment processing, gateways, refunds, reconciliation, invoices, commissions, financial ledger.

### `backend/models/payments.py`
- `Payment` (finance.payments): order_id, amount, payment_method, provider, status, intent_id, country_code, layout_json.
- `Coupon` (commerce.coupons): code, discount_type, discount_value, minimum_order, usage_limit, starts_at, expires_at.
- `Banner` (commerce.banners): free-form canvas layout for admin banner editor.
- `PaymentGatewayConnection`, `Payout`, `LogisticsPartnerPayout`, `PaymentReconciliationRun`.

### `backend/models/finance.py`
- `FiscalPeriod`, `TransactionLedger`, `SupplierSettlement`, `JournalEntry`, `JournalEntryLine`, `Account`, `AccountGroup`, `AccountBalance`, `FinancialReport`, `Invoice`, `InvoiceItem`, `RefundLedger`, `BankTransaction`, `VATRemittance`, `CashAccount`, `CashTransaction`, `TreasuryAccount`, `TreasuryTransaction`, `CashFlowForecast`, `CashPositionSnapshot`, `GatewaySettlementSchedule`, `PendingJournalEntry`, `PayoutBatch`, `PayoutBatchItem`, `ARLedgerEntry`, `APLedger`, `BankStatementImport`, `BankStatementLine`, `BankMappingRule`, `FixedAsset`, `Accrual`, `ScannedExpense`, `FinanceAutomationLog`, `Vendor`, `Customer`, `CostCenter`, `APBill`, `ARInvoice`, `BankAccount`, `Budget`, `BankReconciliation`, `RecurringTemplate`, `FinanceAuditLog`.

### `backend/routers/payments.py.bak` → migrated to `routers/core_payments_routes.py.bak`, `admin_payouts_routes.py`, `admin_cash_routes.py`, etc.
- Payment and finance routes.

### `backend/controllers/finance/`
- `accounting_controller.py`, `commission_controller.py`, `finance_controller.py`, `invoice_controller.py`, `sub_ledger_controller.py`.

### `backend/services/finance/`
- `payments_gateway_service.py`, `order_payment_functions.py`, `refund_posting_service.py`, `invoice_service.py`, `invoice_write_service.py`, `commission_engine.py`, `commission_service.py`, `commission_write_service.py`, `commission_admin_write_service.py`, `commission_geography_service.py`, `finance_read_service.py`, `finance_automation.py`, `finance_automation_write_service.py`, `finance_erp_write_service.py`, `finance_package_service.py`, `finance_transfer_service.py`, `financial_reporting.py`, `financial_reports_service.py`, `general_ledger_service.py`, `sub_ledger_service.py`, `tax_service.py`, `badge_billing_payment.py`, `expense_processing.py`, `expense_routing.py`, `credit_control_service.py`, `period_close_service.py`, `je_reversal_service.py`, `trading_service.py`, `trading_read_service.py`, `contractor_milestone_read_service.py`, `auto_payout_scheduler.py`, `erp_finance_service.py`, `erp_read_service.py`.

### `backend/providers/payments/`
- Payment gateway providers: Stripe (`stripe.py`, `stripe_sdk.py`), PayPal (`paypal.py`), PayTabs (`paytabs.py`), Tap (`tap.py`), Thawani (`thawani.py`), generic fallback (`generic.py`), webhook processors (`webhooks.py`), payment persistence (`payment_persistence.py`), order-level payment orchestration (`_order.py`), connection management (`connect.py`, `config.py`).

### `backend/services/gateways/`
- `payments.py`, `payments_write_service.py`, `gateway_auto_enable.py`, `gateway_reconciliation_service.py`, `payment_event_handlers.py`, `registry.py`, `webhook_processor.py`, `webhook_models.py`, `base.py`, `base_models.py`.

### `backend/services/treasury/`
- Treasury operations: `payment_engine.py`, `payment_orchestrator.py`, `payout_engine.py`, `payout_batch_service.py`, `payout_dispatch_service.py`, `payout_read_service.py`, `payout_status_service.py`, `payout_admin_service.py`, `payout_approval_read_service.py`, `payout_approval_write_service.py`, `cash_management_controller_service.py`, `cash_read_service.py`, `cash_write_service.py`, `cash_flow_forecast_service.py`, `bank_transaction_service.py`, `treasury_service.py`, `treasury_engine.py`, `treasury_query_service.py`, `treasury_router_service.py`, `treasury_adapter.py`, `treasurer.py`, `reporting_service.py`, `admin_treasury_read_service.py`, `admin_treasury_write_service.py`, `admin_reporting_service.py`, `admin_treasury_reporting_service/`.

### `frontend/web_app/src/app/invoice/`
- Invoice display page.

### `frontend/web_app/src/app/admin/*`
- Admin finance pages (payouts, invoices, treasury, bank accounts).

---

## Domain: Logistics

**Feature:** Logistics partners, service areas, pricing, shipments, tracking, partner onboarding, geo-fencing, SLA.

### `backend/models/logistics.py`
- `LogisticsPartner` (logistics.logistics_partners): user_id, name, code, contact info, coverage_regions, service_types, status, verification_status, country_code, business_type, region, city, address, tax_id, latitude, longitude, social_links, terms.
- `LogisticsPartnerProfile`, `LogisticsPartnerServiceArea`, `LogisticsPricingProfile`, `LogisticsVehicleRule`, `Shipment`, `ShipmentEvent`, `LogisticsCategoryPricingRule`.

### `backend/routers/logistics_partner_verify.py`
- Logistics partner verification routes.

### `backend/routers/admin_logistics_routes.py`, `admin_logistics_imports.py`
- Admin logistics routes.

### `backend/controllers/orders/logistics_controller.py`
- Order logistics controller.

### `backend/controllers/orders/logistics_partner_controller.py`
- Partner-specific order controller.

### `backend/services/logistics/`
- `logistics_engine.py`, `logistics_write_service.py`, `logistics_service.py`, `shipment_service.py`, `logistics_partner_verify_service.py`, `logistics_partner_write_service.py`, `logistics_partner_pricing.py`, `logistics_partner_admin_write_service.py`, `logistics_orders_v2_service.py`, `logistics_orders_list_service.py`, `logistics_logistics_status_service.py`, `logistics_locations_create_service.py`, `logistics_locations_service.py`, `logistics_health_service.py`, `logistics_health_engine.py`, `logistics_health_list_service.py`, `logistics_analytics_service.py`, `logistics_sla_service.py`, `live_tracking_service.py`, `geo_fence_service.py`, `map_service.py`, `location_service.py`, `partner_blocker_service.py`, `partner_geography_service.py`, `partner_shipments_service.py`, `shipping_tier.py`, `admin_operations_service.py`.

### `backend/services/core/logistics_service.py`, `logistics_partner_service.py`, `logistics_locations_service.py`, `logistics_health_service.py`, `shipments_service.py`
- Core logistics services (delegators).

### `backend/controllers/admin/admin_logistics_operations_controller.py`, `admin_logistics_geography_controller.py`
- Admin logistics controllers.

### `backend/services/admin/admin_logistics_operations_service.py`, `admin_logistics_geography_service.py`, `admin_logistics_imports_service.py`
- Admin logistics services.

### `frontend/web_app/src/app/logistics-partner/`, `logistics-partners/`
- Logistics partner portal routes.

### `frontend/web_app/src/components/LogisticsPartnerLayout.tsx`
- Logistics partner layout shell.

### `frontend/web_app/src/lib/trackingRealtime.ts`
- Real-time tracking WebSocket bridge.

---

## Domain: Suppliers

**Feature:** Supplier registration, onboarding, profile, products, documents, health scoring, payouts, analytics, disputes, storefronts.

### `backend/models/comms/suppliers.py`
- `SupplierProfile` (communication.supplier_profiles): user_id, business_name, tax_id, business_type, years_in_business, insurance, verification_status, country_code, bio, logo, banner, social_links, terms.

### `backend/models/suppliers.py`
- Re-export shim pointing to `models.comms.suppliers`.

### `backend/routers/supplier_products.py`, `supplier_products_upload.py`, `supplier_orders.py`, `supplier_payouts.py.bak`, `supplier_documents.py.bak`, etc.
- Supplier-specific routes.

### `backend/controllers/supplier/`
- `supplier_controller.py`, `supplier_analytics_controller.py`, `supplier_document_controller.py`, `supplier_health_controller.py`, `supplier_orders_verify_controller.py`, `supplier_products_upload_controller.py`, `supplier_profile_create_controller.py`.

### `backend/services/supplier/`
- `supplier_service.py`, `suppliers_service.py`, `suppliers_write_service.py`, `supplier_profile_create_service.py`, `supplier_profile_write_service.py`, `supplier_products_upload_service.py`, `supplier_supplier_upload_service.py`, `supplier_batch_write_service.py`, `supplier_order_service.py`, `supplier_orders_verify_service.py`, `supplier_payout_service.py`, `supplier_finance_service.py`, `supplier_document_service.py`, `supplier_document_controller_service.py`, `supplier_health_service.py`, `supplier_health_engine.py`, `supplier_badge_service.py`, `supplier_badge_write_service.py`, `supplier_analytics_service.py`, `supplier_bank_account_service.py`, `supplier_onboarding_service.py`, `onboarding_pipeline.py`, `legal_contract_service.py`, `supplier_supplier_sync_service.py`, `admin_supplier_review_service.py`, `admin_supplier_write_service.py`.

### `backend/services/admin/`
- `suppliers_service.py`, `admin_supplier_trading_service.py`, `admin_supplier_reviews_service.py`.

### `backend/controllers/admin/suppliers_controller.py`
- Admin supplier management.

### `frontend/web_app/src/app/supplier/`
- Supplier portal: dashboard, inventory, orders, payouts, analytics, products, documents, disputes, regions, returns, support, terms, logistics, videos, bulk upload.

### `frontend/web_app/src/app/supplier-storefront/[slug]/`
- Public supplier storefront.

### `frontend/web_app/src/app/suppliers/[id]/`
- Public supplier directory page.

### `frontend/web_app/src/components/SupplierLayout.tsx`, `SupplierRouteRedirect.tsx`
- Supplier portal layout and auth guard.

### `frontend/web_app/src/components/supplier/`
- Supplier-specific UI: upload, pricing, verification, AI, voice input, commission summary, parcel audit.

---

## Domain: Customers

**Feature:** Customer profiles, addresses, wishlist, reviews, referrals, health scoring, retention, coupons.

### `backend/models/user.py`
- `User` model (also serves as customer profile), `UserDevice`, `Referral`, `ReferralPointEvent`.

### `backend/models/orders.py`
- `WishlistItem`, `Wishlist`, `Review`.

### `backend/routers/wishlist.py.bak`
- Wishlist routes.

### `backend/routers/reviews.py.bak`
- Review routes.

### `backend/routers/referrals.py.bak`
- Referral routes.

### `backend/routers/customer_coupons_create.py.bak`, `customer_coupons_mgmt.py.bak`, `customer_health.py.bak`, `customer_health_list.py.bak`
- Customer-specific routes.

### `backend/controllers/customer/`
- `(empty)` — customer controllers may be in `controllers/public/` or `controllers/commerce/`.

### `backend/services/commerce/reviews_service.py`, `wishlist_read_service.py`, `wishlist_write_service.py`, `referrals_service.py`, `coupons_service.py`, `coupons_read_service.py`, `coupons_write_service.py`, `coupons_legacy_write_service.py`, `flash_sale_service.py`, `flash_sale_write_service.py`, `flash_sale_controller_service.py`, `promotion_service.py`, `promotion_engine_service.py`, `promotion_bogo_service.py`, `promotion_points_service.py`, `promotions_write_service.py`, `admin_promotion_service.py`.

### `backend/services/customer/`
- `customer_coupons_create_service.py`, `customer_health_engine.py`, `customer_health_list_service.py`, `retention_service.py`.

### `backend/services/core/reviews_service.py`, `wishlist_service.py`, `referrals_service.py`
- Core customer feature services.

### `backend/services/public/`
- `customer_coupons_create_service.py`, `customer_health_list_service.py`, `public_commerce_validation_service.py`.

### `frontend/web_app/src/app/wishlist/`
- Wishlist page.

### `frontend/web_app/src/lib/wishlistStore.ts`, `wishlistHelpers.ts` (shared)
- Wishlist state and helpers.

### `frontend/web_app/src/app/profile/`
- User profile page.

### `frontend/web_app/src/app/profile/referrals/`
- Referrals sub-page.

### `frontend/web_app/src/components/RecentlyViewed.tsx`, `Recommendations.tsx`
- Customer discovery components.

---

## Domain: Communications

**Feature:** Email, chat, video conferencing, unified inbox, notifications, push notifications, WhatsApp, internal comms, escalation, SLA.

### `backend/models/comms/`
- Communication models: conversations, messages, participants, email threads, video rooms, notifications.

### `backend/models/comms/suppliers.py`
- Supplier profile model (also part of comms domain).

### `backend/routers/chat.py`, `chat_api.py`, `chat_enrichment.py`, `chatbot.py`, `comms_chat.py`, `comms_unified.py`, `comms_video.py`, `ws_chat.py.bak`, `comm_ws.py`
- Communication routes: chat, chatbot, unified comms, video.

### `backend/routers/public_comms_status.py`, `public_comms_unified.py.bak`, `public_comms_comm.py.bak`, `public_comms_notification.py.bak`
- Public communication routes.

### `backend/routers/core_messaging_routes.py`, `core_video_routes.py.bak`, `core_chatbot_routes.py`
- Core communication routes.

### `backend/controllers/comms/`
- `chat_write_controller.py`, `chatbot_controller.py`, `comm_controller.py`, `communication_audit_controller.py`, `notification_controller.py` — comms controllers for chat, chatbot, unified comms, audit, notifications.

### `backend/controllers/admin/admin_comms_messaging_controller.py`, `admin_comms_unified_controller.py`, `admin_comms_geography_controller.py`
- Admin communication controllers.

### `backend/services/comms/`
- `chat_system.py`, `chat_read_service.py`, `chat_write_service.py`, `chat_enrichment.py`, `chatbot_service.py`, `comm_service.py`, `communication_read_service.py`, `communication_write_service.py`, `communication_audit.py`, `connection_manager_base.py`, `content_service.py`, `email_gateway.py`, `email_write_service.py`, `email_management_service.py`, `email_event_service.py`, `email_enrichment.py`, `email_reputation.py`, `entity_chat_service.py`, `entity_messaging.py`, `escalation_sla.py`, `external_contact.py`, `internal_communication.py`, `notification_engine.py`, `notification_service.py`, `notification_worker.py`, `proxy_communication.py`, `push_notifications_service.py`, `realtime_chat_service.py`, `transactional_email_service.py`, `translation_service.py`, `unified_inbox_service.py`, `video_conferencing.py`, `video_room_service.py`, `video_room_write_service.py`, `video_service.py`, `websocket_chat.py`, `websocket_manager.py`, `whatsapp_service.py`, `package_service.py`, `payout_notification_service.py`, `campaign_geography_service.py`.

### `backend/services/core/comms_unified_service.py`, `email_service.py`, `chat_enrichment_service.py`
- Core comms services.

### `backend/services/admin/admin_comms_messaging_service.py`, `admin_comms_unified_service.py`, `admin_comms_geography_service.py`
- Admin comms services.

### `backend/services/public/public_comms_status_service.py`, `public_comms_unified_service.py`
- Public comms services.

### `backend/events/event_publisher.py`
- Event publishing infrastructure.

### `backend/providers/comms/`
- Communication providers (email, SMS, push).

### `backend/providers/voice/`
- Voice/transcription providers.

### `frontend/web_app/src/app/chatbot/`
- Chatbot interface.

### `frontend/web_app/src/components/chat/`
- Chat UI: `PresenceIndicator.tsx`, `TypingIndicator.tsx`.

### `frontend/web_app/src/components/comms/`
- Unified inbox: `CommandPalette`, `CommShell`, `Composer`, `StatusDock`, `UnifiedInboxBridge`, `DragProvider`, `LensChips`, `Context/Context.tsx`, `Rail/`, `Stage/` (B2BMasked, ChatStream, ContactTimeline, EmailView, IncidentRoom, VideoRoom).

### `frontend/web_app/src/hooks/useSendMessage.ts`, `useChatHistory.ts`, `useWebSocket.ts`, `useThreadMessages.ts`
- Chat and messaging hooks.

### `frontend/web_app/src/app/notifications/`
- Notifications page.

### `frontend/web_app/src/lib/notificationStore.ts`, `notificationHelpers.ts` (shared)
- Notification state and helpers.

### `frontend/web_app/src/app/meet/[room]/`
- Real-time meeting/video room page.

---

## Domain: Admin & Governance

**Feature:** Admin dashboard, user management, product moderation, order oversight, finance oversight, permissions, audit logs, command center, governance, incident management.

### `backend/routers/admin.py`
- Admin router aggregator.

### `backend/routers/admin_analytics_routes.py`, `admin_banners_routes.py`, `admin_cash_routes.py`, `admin_chat_routes.py`, `admin_core_routes.py`, `admin_email_routes.py`, `admin_fallback_routes.py`, `admin_logistics_routes.py`, `admin_orders_routes.py`, `admin_payouts_routes.py`, `admin_products_routes.py`, `admin_settings_routes.py`, `admin_suppliers_routes.py`, `admin_treasury_routes.py`, `admin_users_routes.py`, `admin_video_routes.py`
- Admin API routes.

### `backend/controllers/admin/`
- `admin_controller.py`, `admin_dashboard_controller.py`, `admin_catalog_operations_controller.py`, `admin_catalog_orders_controller.py`, `admin_commerce_configuration_controller.py`, `admin_commerce_geography_controller.py`, `admin_comms_geography_controller.py`, `admin_comms_messaging_controller.py`, `admin_comms_unified_controller.py`, `admin_finance_geography_controller.py`, `admin_geography_audit_controller.py`, `admin_geography_configuration_controller.py`, `admin_identity_operations_api_controller.py`, `admin_identity_operations_controller.py`, `admin_logistics_geography_controller.py`, `admin_logistics_operations_controller.py`, `admin_media_geography_controller.py`, `admin_orders_status_controller.py`, `admin_permissions_validation_controller.py`, `admin_security_detection_controller.py`, `admin_security_operations_controller.py`, `admin_security_registration_controller.py`, `admin_supplier_reviews_controller.py`, `admin_supplier_trading_controller.py`, `admin_treasury_identity_controller.py`, `admin_treasury_payments_controller.py`, `admin_treasury_reporting_controller.py`, `admin_treasury_status_controller.py`, `analytics_controller.py`, `analytics_dashboard_controller.py`, `audit_controller.py`, `bank_accounts_controller.py`, `coupons_controller.py`, `misc_controller.py`, `orders_controller.py`, `payouts_controller.py`, `permissions_controller.py`, `products_controller.py`, `suppliers_controller.py`, `tickets_controller.py`, `users_admin_controller.py`.

### `backend/services/admin/`
- 46 service files covering all admin operations: dashboard, catalog, commerce, comms, finance, geography, identity, logistics, media, orders, permissions, security, suppliers, treasury, users, analytics, bulk ops, coupons, database, misc, payouts, tickets.

### `backend/services/governance/`
- `command_center_service.py`, `governance_package_service.py`, `incident_admin_read_service.py`.

### `backend/routers/command_center_api.py`, `command_center.py`
- Command center API routes.

### `backend/controllers/audit/`
- Audit controllers.

### `backend/services/audit/`
- Audit services.

### `backend/utils/audit.py`
- Audit logging utilities.

### `backend/utils/security_audit.py`
- Security audit utilities.

### `backend/utils/schema_audit.py`
- Schema audit utilities.

### `frontend/web_app/src/app/admin/`
- Admin panel with 47+ subdirectories: dashboard, products, orders, users, suppliers, finance, payouts, bank-accounts, commission, invoices, treasury, coupons, promotions, flash-sales, communication, email, video, command-center, HR, staff, payroll, returns, disputes, countries, audit-logs, inventory-alerts, product-verification, exports, tickets, moderation, payments, permissions, resolution, etc.

### `frontend/web_app/src/components/AdminLayout.tsx`, `AdminRouteRedirect.tsx`
- Admin layout and route guard.

### `frontend/web_app/src/components/admin/`
- Admin-specific components: `AdminChatPanel`, `AdminEmailPanel`, `AdminVideoPanel`, `EmailCampaignManager`, `CreateCampaignForm`, `EmailProviderConfigManager`, `EmailSuppressionManager`, `EmailTemplateManager`, `commandCenter/` (HUD).

### `frontend/web_app/src/components/FraudDetectionDashboard.tsx`
- Fraud detection admin dashboard.

---

## Domain: HR & Employees

**Feature:** Employee management, attendance, payroll, performance, leave, LMS, OKR, succession planning, shift scheduling, background checks, DEI, HSE.

### `backend/models/employee_models.py`
- Employee-specific models.

### `backend/models/hr/`
- HR domain models.

### `backend/routers/employees.py.bak`, `core_payroll_routes.py`, `core_performance_routes.py`, `core_okr_routes.py`, `core_succession_routes.py`
- HR routes.

### `backend/controllers/hr/`
- HR controllers (directory exists).

### `backend/services/hr/`
- 34 service files: `attendance_service.py`, `background_check.py`, `coi_engine.py`, `coi_service.py`, `dei_auditor.py`, `employee_activity_logger.py`, `employee_communication_service.py`, `employee_lifecycle_service.py`, `employee_write_service.py`, `employees_controller_service.py`, `employees_service.py`, `ess_write_service.py`, `hr_dashboard_service.py`, `hr_service.py`, `hr_write_service.py`, `hse_manager.py`, `learning_write_service.py`, `leave_accrual.py`, `lms_permission_lock.py`, `lms_service.py`, `lms_write_service.py`, `lms.py`, `offboarding.py`, `okr_engine.py`, `payroll_engine.py`, `payroll_read_service.py`, `payroll_service.py`, `performance_service.py`, `shift_handover.py`, `shift_roster_service.py`, `shift_scheduling.py`, `succession_service.py`.

### `backend/services/employee/`
- `attendance_service.py`, `background_check.py`.

### `backend/services/core/hr_service.py`, `payroll_service.py`, `performance_service.py`, `ess_service.py`, `employees_service.py`
- Core HR services.

### `frontend/web_app/src/app/admin/`
- Admin HR pages.

### `frontend/web_app/src/components/ems/`
- Enterprise management system components: `ActivityTimeline`, `ChatEnrichment`, `OrgChartTree`, `PayrollWorkflow`.

---

## Domain: Geography & Country

**Feature:** Country config, RLS, cross-border detection, currency, localization, maps, staff assignment, auto-populate, tax, restriction, versioning.

### `backend/models/countries.py`
- `CountryConfig` (country.country_configs): code, name, currency, phone_code, timezone, is_active, is_featured, commission_rate, tax_rate, tax_id, address_format, meta, logo, flag.

### `backend/models/country_control.py`
- Country control models.

### `backend/models/country_enhancements.py`
- Country enhancement models.

### `backend/routers/core_countries_routes.py`, `api_geography_location.py`, `country_communications.py`, `core_travel_routes.py.bak`, etc.
- Country and geography routes.

### `backend/controllers/geography/`
- Geography controllers.

### `backend/services/geography/`
- 38 service files: `country_service.py`, `country_read_service.py`, `country_write_service.py`, `country_admin_write_service.py`, `country_audit_admin_service.py`, `country_auto_populate.py`, `country_auto_populate_write_service.py`, `country_communication_service.py`, `country_config_admin_service.py`, `country_config_write_service.py`, `country_curated.py`, `country_data_orchestrator.py`, `country_detection.py`, `country_dropdown_service.py`, `country_heuristic_engine.py`, `country_maps_service.py`, `country_payout_write_service.py`, `country_research.py`, `country_restriction_service.py`, `country_rls_service.py`, `country_router_service.py`, `country_staff_service.py`, `country_staff_write_service.py`, `country_tax_service.py`, `country_versioning_service.py`, `cross_border_base.py`, `cross_border_detection.py`, `cross_border_service.py`, `cross_border_tracker.py`, `curated_cities.py`, `geo_service.py`, `localization_service.py`, `travel_detector.py`, `travel_service.py`, `vat_rates.py`, `category_tax_profiles.py`.

### `backend/services/country/`
- `country_communications_read_service.py`, `country_communications_service.py`.

### `backend/services/core/countries_service.py`, `country_admin_service.py`, `country_dropdown_service.py`, `country_maps_service.py`, `country_payouts_service.py`, `country_staff_service.py`, `geo_service.py`
- Core country services.

### `backend/services/admin/admin_commerce_geography_controller.py`, `admin_geography_audit_controller.py`, `admin_geography_configuration_controller.py`, `admin_finance_geography_controller.py`, `admin_logistics_geography_controller.py`, `admin_media_geography_controller.py`
- Admin geography controllers.

### `backend/services/admin/admin_commerce_geography_service.py`, `admin_geography_audit_service.py`, `admin_geography_configuration_service.py`, `admin_finance_geography_service.py`, `admin_logistics_geography_service.py`, `admin_media_geography_service.py`
- Admin geography services.

### `backend/utils/country_access.py`, `country_detection_middleware.py`, `country_rls.py`, `geo.py`
- Country access control, detection, RLS helpers.

### `backend/middleware/country_context.py`
- Country context middleware.

### `backend/dependencies/country_detection.py`, `country_rls.py`
- Country detection and RLS dependencies.

### `backend/providers/geography/`
- Geography providers (maps, geo data).

### `backend/services/location_service/`
- `geo_resolver.py`, `main.py` — location resolution service.

### `frontend/web_app/src/app/api/geo/`
- Geo API route.

### `frontend/web_app/src/hooks/useCountryAutoPopulate.ts`, `useCrossBorder.ts`
- Country and cross-border hooks.

### `frontend/web_app/src/services/crossBorderService.ts`, `localizationService.ts`
- Cross-border and localization services.

### `frontend/web_app/src/components/country/`
- Country workbench: `CountryDetailWorkspace`, `CountryMapView`, `CountryLedgerTable`, `CountryResearchPanel`, `CountryStaffAssignmentModal`, `DynamicAddressForm`, `ParcelTracker`, `LegalContractGenerator`, `ShiftHandoverModal`, `tabs/OverviewTab.tsx`.

---

## Domain: AI & Automation

**Feature:** AI product descriptions, background removal, OCR, research, automation, parcel verification, search, copy jobs.

### `backend/models/ai_upload.py`
- AI upload models.

### `backend/models/ai/`
- AI domain models.

### `backend/routers/ai.py`, `ai_image.py`, `ai_research.py`, `ai_upload.py`, `core_ai_routes.py`, `system_ai_country_research.py.bak`, `system_ai_media.py`, `system_ai_messaging.py.bak`, `system_ai_reporting.py.bak`, `system_ai_sync.py`
- AI routes.

### `backend/controllers/ai/`
- AI controllers.

### `backend/services/ai/`
- `ai_service.py`, `ai_automation_service.py`, `ai_copy_jobs.py`, `ai_research_jobs.py`, `ai_search_service.py`, `ai_upload_write_service.py`, `ai_variant_config.py`, `automation_read_service.py`, `automation_scheduler.py`, `bg_removal_presets.py`, `bg_removal_service.py`, `country_ai_research.py`, `ocr_parser.py`, `parcel_verification_service.py`.

### `backend/services/system/system_ai_country_research.py.bak`, `system_ai_media.py`, `system_ai_messaging.py.bak`, `system_ai_reporting.py.bak`, `system_ai_sync.py`
- System AI services.

### `backend/providers/ai/`
- AI provider integrations (OpenAI, etc.).

### `backend/providers/image/`
- Image processing providers (background removal).

### `backend/jobs/ai/`
- AI background jobs.

### `backend/utils/ml_worker.py`
- ML worker utilities.

### `frontend/web_app/src/app/admin/`
- Admin AI pages.

### `frontend/web_app/src/components/supplier/`
- Supplier AI components: `VoiceProductInput`, `VoiceToCatalogPipeline`, `AIResultsModal`, `ProcessingModal`.

---

## Domain: Media & Uploads

**Feature:** Image uploads, video, media management, storage backends (local/S3), bulk upload.

### `backend/models/media_models.py`
- Media models.

### `backend/models/media/`
- Media domain models.

### `backend/routers/upload.py`, `batch_upload.py`, `ai_upload.py`, `core_upload_routes.py.bak`, `upload_jobs.py.bak`
- Upload routes.

### `backend/controllers/media/`
- Media controllers.

### `backend/services/media/`
- (directory exists, empty __init__).

### `backend/services/uploads/`
- (directory exists, empty __init__).

### `backend/services/system/system_ai_media.py`
- System AI media service.

### `backend/providers/media/`
- Media processing providers.

### `backend/providers/storage.py`
- S3/boto3 client factory.

### `backend/services/ai/bg_removal_service.py`
- Background removal service.

### `backend/services/ai/ocr_parser.py`
- OCR parsing service.

### `backend/services/supplier/supplier_products_upload_service.py`, `supplier_supplier_upload_service.py`
- Supplier upload services.

### `backend/services/admin/admin_media_geography_service.py`
- Admin media geography service.

### `backend/services/core/admin_media_service.py` (implied)
- Core media service.

### `frontend/web_app/src/components/supplier/SmartMediaUpload.tsx`
- Supplier media upload component.

### `frontend/web_app/src/components/ProductImageCanvas.tsx`
- Product image canvas editor.

### `frontend/web_app/src/components/PhotoEditorModal.tsx`
- Photo editor modal.

---

## Domain: Security & Compliance

**Feature:** Fraud detection, impossible travel, behavioral analytics, risk scoring, PCI-DSS, security headers, KMS encryption, SIEM, incident management, approval matrix.

### `backend/models/security/`
- Security domain models.

### `backend/models/fraud.py`
- Fraud detection models.

### `backend/routers/compliance.py`, `admin_security_health.py`, `admin_security_operations.py.bak`, `core_compliance_routes.py`, `core_risk_routes.py`
- Security and compliance routes.

### `backend/controllers/security/`
- Security controllers.

### `backend/controllers/admin/admin_security_detection_controller.py`, `admin_security_operations_controller.py`, `admin_security_registration_controller.py`
- Admin security controllers.

### `backend/services/security/`
- 32 service files: `auth_controller_service.py`, `auth_service.py`, `auth_write_service.py`, `behavioral_analytics.py`, `biometric_auth.py`, `country_context_service.py`, `data_residency.py`, `data_residency_service.py`, `effective_permissions.py`, `fraud_admin_controller_service.py`, `fraud_admin_service.py`, `fraud_detection_service.py`, `fraud_detection.py`, `fraud_engine.py`, `fraud_service.py`, `iam_service.py`, `iam_write_service.py`, `impossible_travel_write_service.py`, `incident_service.py`, `kms_encryption.py`, `mobile_auth_service.py`, `permission_primitive_write_service.py`, `permission_service.py`, `permissions_write_service.py`, `risk_service.py`, `risk_write_service.py`, `siem_engine.py`, `triple_auth.py`, `admin_security_operations_service.py`, `approval_matrix_service.py`.

### `backend/services/admin/admin_security_detection_service.py`, `admin_security_health_service.py`, `admin_security_operations_service.py`, `admin_security_registration_service.py`
- Admin security services.

### `backend/services/public/public_security_detection_service.py`, `public_security_operations_service.py`, `public_security_registration_service.py`
- Public security services.

### `backend/middleware/impossible_travel_middleware.py`
- Impossible travel detection middleware.

### `backend/middleware/pci_dss_compliance.py`
- PCI-DSS compliance middleware.

### `backend/middleware/security_headers.py`
- Security headers middleware.

### `backend/middleware/coi_middleware.py`
- Conflict of interest middleware.

### `backend/utils/security_metrics.py`
- Security metrics utilities.

### `backend/services/orders/ghost_watchdog.py`
- Ghost order detection.

### `backend/services/orders/fraud_monitoring.py` (in jobs/)
- Fraud monitoring background job.

### `frontend/web_app/src/components/FraudDetectionDashboard.tsx`
- Fraud detection admin dashboard.

---

## Domain: Notifications & Realtime

**Feature:** Push notifications, email notifications, in-app notifications, WebSocket real-time updates, notification worker.

### `backend/models/comms/`
- Notification models.

### `backend/routers/notifications.py.bak`
- Notification routes.

### `backend/services/comms/notification_engine.py`, `notification_service.py`, `notification_worker.py`, `push_notifications_service.py`, `payout_notification_service.py`, `email_event_service.py`
- Notification services.

### `backend/services/core/notification_service.py` (implied)
- Core notification service.

### `backend/utils/websocket_manager.py`
- WebSocket connection manager.

### `backend/utils/realtime.py`
- Realtime utilities.

### `backend/utils/email_service.py`
- Email sending utilities.

### `backend/providers/comms/`
- Communication providers (email, push, SMS).

### `backend/events/event_publisher.py`
- Event publishing (triggers notifications).

### `frontend/web_app/src/app/notifications/`
- Notifications page.

### `frontend/web_app/src/lib/notificationStore.ts`, `notificationHelpers.ts` (shared)
- Notification state.

### `frontend/web_app/src/components/UserRealtimeBridge.tsx`
- Realtime updates bridge component.

### `frontend/web_app/src/hooks/`
- Various realtime hooks.

---

## Domain: Reviews & Ratings

**Feature:** Product reviews, ratings, review moderation.

### `backend/models/products.py`
- `Review` model.

### `backend/routers/reviews.py.bak`
- Review routes.

### `backend/services/commerce/reviews_service.py`
- Commerce review service.

### `backend/services/core/reviews_service.py`
- Core review service.

### `backend/services/reviews/`
- (directory exists, empty __init__).

### `backend/controllers/reviews/`
- Review controllers.

### `backend/controllers/admin/admin_supplier_reviews_controller.py`
- Admin supplier review controller.

### `backend/services/admin/admin_supplier_reviews_service.py`
- Admin supplier review service.

### `frontend/web_app/src/app/products/`
- Product pages with reviews.

---

## Domain: Tickets & Support

**Feature:** Support tickets, ticket lifecycle, escalation, SLA.

### `backend/routers/tickets.py.bak`, `core_tickets_routes.py`
- Ticket routes.

### `backend/controllers/admin/tickets_controller.py`
- Admin ticket controller.

### `backend/services/comms/tickets_write_service.py`
- Ticket write service.

### `backend/services/core/tickets_service.py`
- Core ticket service.

### `backend/services/admin/tickets_service.py`
- Admin ticket service.

### `backend/services/comms/escalation_sla.py`
- Escalation SLA service.

### `frontend/web_app/src/app/tickets/`, `tickets/[id]/`
- Ticket pages.

---

## Domain: Returns & Disputes

**Feature:** Return requests, return processing, dispute management, refunds.

### `backend/models/orders.py`
- `ReturnRequest` model.

### `backend/routers/returns.py.bak`, `public_core_returns.py.bak`
- Return routes.

### `backend/controllers/orders/returns_controller.py`
- Returns controller.

### `backend/services/orders/returns_service.py`, `returns_write_service.py`, `returns_controller_service.py`
- Return services.

### `backend/services/commerce/`
- Commerce-level return services.

### `backend/services/core/returns_service.py`
- Core returns service.

### `backend/controllers/orders/disputes_controller.py`
- Disputes controller.

### `backend/services/orders/disputes_service.py`, `disputes_write_service.py`
- Dispute services.

### `frontend/web_app/src/app/returns/`, `returns/[id]/`
- Returns pages.

---

## Domain: Treasury & Payouts

**Feature:** Supplier payouts, treasury management, cash flow, bank transactions, reconciliation, payout batches, approval workflows.

### `backend/models/finance.py`
- Treasury models: `TreasuryAccount`, `TreasuryTransaction`, `CashAccount`, `CashTransaction`, `CashFlowForecast`, `CashPositionSnapshot`, `PayoutBatch`, `PayoutBatchItem`.

### `backend/routers/admin_payouts_routes.py`, `admin_treasury_routes.py`, `admin_cash_routes.py`, `core_treasury_routes.py.bak`
- Treasury and payout routes.

### `backend/controllers/treasury/`
- Treasury controllers.

### `backend/services/treasury/`
- 28 service files: `payment_engine.py`, `payment_orchestrator.py`, `payout_engine.py`, `payout_batch_service.py`, `payout_dispatch_service.py`, `payout_read_service.py`, `payout_status_service.py`, `payout_admin_service.py`, `payout_approval_read_service.py`, `payout_approval_write_service.py`, `cash_management_controller_service.py`, `cash_read_service.py`, `cash_write_service.py`, `cash_flow_forecast_service.py`, `bank_transaction_service.py`, `treasury_service.py`, `treasury_engine.py`, `treasury_query_service.py`, `treasury_router_service.py`, `treasury_adapter.py`, `treasurer.py`, `reporting_service.py`, `admin_treasury_read_service.py`, `admin_treasury_write_service.py`, `admin_reporting_service.py`, `admin_treasury_reporting_service/`, `auto_payout_scheduler.py`.

### `backend/services/finance/auto_payout_scheduler.py`
- Auto payout scheduler.

### `backend/services/supplier/supplier_payout_service.py`
- Supplier payout service.

### `backend/services/core/supplier_payouts_service.py`
- Core supplier payouts service.

### `backend/services/admin/payouts_service.py`
- Admin payouts service.

### `frontend/web_app/src/app/admin/`
- Admin treasury and payouts pages.

---

## Domain: Search & Discovery

**Feature:** Product search, advanced filtering, visual search, recommendations, category tree, search ranking.

### `backend/routers/search.py`
- Search routes.

### `backend/services/search/`
- Search service directory.

### `backend/services/catalog/advanced_search_engine.py`, `advanced_filter_service.py`, `visual_search_service.py`
- Search and discovery services.

### `backend/services/core/search_service.py`
- Core search service.

### `backend/utils/category_tree.py`
- Category tree utilities.

### `frontend/web_app/src/components/UnifiedSearchBar.tsx`, `FilterSearchBar.tsx`, `AdvancedFilter.tsx`, `AdvancedFilterPanel.tsx`
- Search UI components.

### `frontend/web_app/src/components/Recommendations.tsx`
- Recommendations component.

### `frontend/web_app/src/lib/useBgRecommendations.ts`
- Background recommendations hook.

---

## Domain: Promotions & Marketing

**Feature:** Coupons, flash sales, promotions, BOGO, points, banners, email campaigns, referral rewards.

### `backend/models/payments.py`
- `Coupon`, `Banner` models.

### `backend/routers/coupons.py.bak`, `flash_sales.py.bak`, `admin_promotions.py`, `store_banners_routes.py.bak`
- Promotion routes.

### `backend/services/commerce/coupons_service.py`, `coupons_read_service.py`, `coupons_write_service.py`, `coupons_legacy_write_service.py`, `promotion_service.py`, `promotion_engine_service.py`, `promotion_bogo_service.py`, `promotion_points_service.py`, `promotions_write_service.py`, `flash_sale_service.py`, `flash_sale_write_service.py`, `flash_sale_controller_service.py`, `referrals_service.py`, `wishlist_read_service.py`, `wishlist_write_service.py`, `reviews_service.py`, `admin_promotion_service.py`.

### `backend/services/catalog/banner_service.py`, `banner_write_service.py`
- Banner services.

### `backend/services/core/banners_service.py`, `coupons_service.py`
- Core banner/coupon services.

### `backend/services/admin/coupons_service.py`
- Admin coupon service.

### `backend/services/comms/email_gateway.py`, `email_write_service.py`, `email_management_service.py`, `transactional_email_service.py`, `campaign_geography_service.py`
- Email campaign services.

### `backend/controllers/admin/coupons_controller.py`
- Admin coupons controller.

### `frontend/web_app/src/components/BannerCarousel.tsx`, `SeasonalBanner.tsx`, `LimitedTimeOffer.tsx`
- Marketing UI components.

---

## Domain: Infrastructure & Observability

**Feature:** Database, migrations, logging, metrics, tracing, health checks, background jobs, configuration, Redis, caching, RLS, soft delete, encryption.

### `backend/db/`
- Database engine, session, base, migrations, seed data, create_tables, init_db.

### `backend/utils/config.py`
- Settings management.

### `backend/utils/logging_config.py`
- Structured logging.

### `backend/utils/prometheus_setup.py`
- Prometheus metrics.

### `backend/utils/tracing.py`
- OpenTelemetry tracing.

### `backend/utils/redis_client.py`
- Redis client.

### `backend/utils/cache.py`
- Caching utilities.

### `backend/utils/metrics.py`
- Metrics utilities.

### `backend/utils/background_jobs.py`
- Background job framework.

### `backend/utils/migrations.py`
- Migration utilities (Alembic wrapper).

### `backend/utils/rls_interceptor.py`, `rls_middleware.py`, `rls_dependency.py`, `rls_context.py`, `country_rls.py`
- Row-Level Security (RLS) implementation.

### `backend/utils/soft_delete.py`
- Soft delete utilities.

### `backend/utils/ghost_record.py`
- Ghost record (tombstone) handling.

### `backend/utils/encryption.py`, `kms_encryption.py`, `kms_integration.py`
- Encryption utilities.

### `backend/utils/secrets_manager.py`
- Secrets management.

### `backend/utils/key_rotation.py`
- Key rotation utilities.

### `backend/utils/datetime_utils.py`
- Timezone-aware datetime utilities.

### `backend/utils/money.py`
- Money/currency utilities.

### `backend/utils/slug.py`
- URL slug generation.

### `backend/utils/pagination.py`
- Pagination helpers.

### `backend/utils/rate_limiter.py`
- Rate limiting logic.

### `backend/utils/ip_utils.py`
- IP address utilities.

### `backend/utils/geo.py`
- Geo utilities.

### `backend/utils/constant_time.py`
- Constant-time comparison for security.

### `backend/utils/file_validation.py`
- File upload validation.

### `backend/utils/websocket_manager.py`
- WebSocket connection manager.

### `backend/utils/realtime.py`
- Realtime utilities.

### `backend/utils/entity_messaging.py`
- Entity messaging utilities.

### `backend/utils/order_tracking.py`
- Order tracking utilities.

### `backend/utils/invoice_html.py`
- Invoice HTML generation.

### `backend/utils/vault.py`
- Vault integration.

### `backend/utils/multi_secret_webhook.py`
- Multi-secret webhook verification.

### `backend/utils/url_security.py`
- URL security utilities.

### `backend/utils/variant_key.py`
- Variant key utilities.

### `backend/utils/staff_permissions.py`
- Staff permission utilities.

### `backend/utils/analytics_service.py`
- Analytics service utilities.

### `backend/utils/admin_shared.py`
- Admin shared utilities.

### `backend/utils/api_docs.py`
- API documentation utilities.

### `backend/utils/response_wrapper.py`
- Response wrapper utilities.

### `backend/utils/lazy_imports.py`
- Lazy import utilities.

### `backend/utils/circuit_breaker.py`
- Circuit breaker pattern.

### `backend/utils/backup.py`, `db_backup.py`
- Backup utilities.

### `backend/utils/middleware_helpers.py`
- Middleware helper utilities.

### `backend/utils/versioning.py`
- API versioning utilities.

### `backend/utils/csrf.py`, `csrf_utils.py`
- CSRF utilities.

### `backend/utils/error_handler.py`
- Error handling utilities.

### `backend/utils/dependencies.py`
- Dependency injection helpers.

### `backend/middleware/`
- 18 middleware files: orchestrator, IP extraction, security headers, impossible travel, fraud detection, fraud scoring, CSRF, rate limiting, country context, request ID, API versioning, logging, PCI-DSS, device binding, COI, database security, webhook IP whitelist, webhook verification, zero-trust auth, RLS dependency. Note: CORS and GZip are FastAPI built-ins wired in `orchestrator.py`, not separate middleware files.

### `backend/jobs/`
- Background tasks: `background_tasks.py`, `fraud_monitoring.py`, `ghost_order_detector.py`, `threat_feed_updater.py`, `seed_all.py`, `mcp_server.py`, `ai/` (AI jobs).

### `backend/events/`
- Domain events: `event_publisher.py`, `payment_events.py`.

### `backend/providers/`
- External integrations: `ai/`, `analytics/`, `auth/`, `automation/`, `comms/`, `config.py`, `finance/`, `geography/`, `http.py`, `image/`, `legacy/`, `media/`, `news/`, `observability.py`, `parcel_verification.py`, `payments/`, `security/`, `storage.py`, `voice/`, `async_workers.py`.

### `backend/dependencies/`
- FastAPI dependencies: `coi_dependency.py`, `country_detection.py`, `country_rls.py`, `fraud_events.py`.

---

## Additional Backend Structure

### `backend/scripts/`
- 42+ operational and migration scripts: `add_schema_declarations_*.py`, `check_db_models.py`, `comprehensive_schema_check.py`, `debug_*.py` (6 files), `fix_table_args_*.py` (7 files), `generate_data_dictionary.py`, `migrate_media_to_s3.py`, `validate_migrations.py`, `verify_syntax.py`, `partition_maintenance.sql`, and others for schema validation, model analysis, and data migration.

### `backend/controllers/delegators/`
- 96 delegator files that re-export routers from service modules. Examples: `ai.py`, `admin.py`, `commerce.py`, `comms_chat_system.py`, `finance.py`, `logistics_shipment_service.py`, `orders_admin_orders_read_service.py`, `security_fraud_engine.py`, `supplier_supplier_upload_service.py`, `treasury_treasury_service.py`, `users_approval_matrix_service.py`. These form the thin controller layer that FastAPI router auto-discovery imports.

### `backend/controllers/core/`
- 67 core controller files: `admin_orders_controller.py`, `admin_products_controller.py`, `admin_users_controller.py`, `ai_controller.py`, `auth_controller.py`, `cart_controller.py`, `coupons_controller.py`, `countries_controller.py`, `logistics_controller.py`, `orders_controller.py`, `payments.py` (router bridge), `shipments_controller.py`, `supplier_products_controller.py`, `tickets_controller.py`, `users_controller.py`, and more. These handle core platform routes.

### `backend/controllers/router_bridges/`
- Router bridge modules that connect legacy routers to the new controller/service architecture.

### `backend/controllers/gateway/`
- Gateway-related controllers.

### `backend/controllers/unknown/`
- Controllers with undetermined domain classification.

### `backend/services/common/`
- 18 shared service utilities: `asset_tracking.py`, `command_center_background.py`, `command_center_service.py`, `db_read.py`, `db_write.py`, `downstream_hooks.py`, `downstream_wiring.py`, `event_bus.py`, `free_image_tools.py`, `image_ai_service.py`, `import_service.py`, `media_service.py`, `media_storage.py`, `misc_write_service.py`, `qr_service.py`, `storage.py`, `upload_job_service.py`, `write_helpers.py`.

### `backend/services/api/`
- `api_geography_location_service.py` — geo location API service.

### `backend/services/hierarchy/`
- `hierarchy_service.py`, `org_hierarchy_write_service.py` — organizational hierarchy management.

### `backend/services/mcp/`
- `zozi_mcp.py` — Model Context Protocol server integration.

### `backend/services/reporting/`
- Empty directory (just `__init__.py`) — placeholder for reporting services.

### `backend/services/unknown/`
- `_registry.py` — service side-effect registry imported at startup to register schedulers, webhook handlers, event consumers.

### `backend/services/users/`
- 7 files: `approval_matrix_service.py`, `identity_admin_service.py`, `identity_service.py`, `rbac_service.py`, `user_write_ops.py`, `users_write_service.py`, `workflow_engine.py`.

### `backend/services/core/` (additional files not covered in domain sections)
- 47 additional core service files: `addresses_service.py`, `admin_banners_service.py`, `admin_cash_service.py`, `admin_categories_service.py`, `admin_chat_service.py`, `admin_commission_service.py`, `admin_email_service.py`, `admin_logistics_service.py`, `admin_orders_service.py`, `admin_payouts_service.py`, `admin_products_service.py`, `admin_promotions_service.py`, `admin_service.py`, `admin_suppliers_service.py`, `admin_treasury_service.py`, `admin_users_service.py`, `admin_video_service.py`, `auth_service.py`, `categories_service.py`, `cash_management_service.py`, `chat_enrichment_service.py`, `commission_service.py`, `comms_unified_service.py`, `customer_health_service.py`, `email_service.py`, `employees_service.py`, `ess_service.py`, `export_read_service.py`, `export_service.py`, `hierarchy_service.py`, `hr_service.py`, `incident_service.py`, `internal_channels_service.py`, `payroll_service.py`, `performance_service.py`, `permissions_service.py`, `supplier_documents_service.py`, `supplier_finance_service.py`, `supplier_health_service.py`, `supplier_orders_service.py`, `supplier_payouts_service.py`, `supplier_products_service.py`, `supplier_profile_service.py`, `tickets_service.py`, `translation_service.py`, `user_read_service.py`, `users_service.py`.

### `backend/services/public/` (additional files)
- 11 additional public service files: `admin_promotions_routes_service.py`, `admin_treasury_service.py`, `auth_service.py`, `customer_coupons_mgmt_service.py`, `internal_comms_channels_service.py`, `public_geography_configuration_service.py`, `public_identity_operations_service.py`, `public_permissions_validation_service.py`, `public_treasury_payments_service.py`, `system_ai_upload_service.py`, `system_comms_status_service.py`.

### `backend/services/finance/` (additional files not listed in main Finance section)
- `cash_management_service.py`, `cash_management_write_service.py`, `payout_admin_write_service.py`, `supplier_finance_service.py`, `events/` directory.

### `backend/services/comms/` (additional files)
- `command_center_query_service.py`.

### `backend/services/users/`
- Entirely undocumented directory with 7 user-related service files: `approval_matrix_service.py`, `identity_admin_service.py`, `identity_service.py`, `rbac_service.py`, `user_write_ops.py`, `users_write_service.py`, `workflow_engine.py`.

### `backend/models/admin.py`
- Admin domain models.

### `backend/models/commission.py`
- Commission model.

### `backend/models/communication.py`
- Communication domain models.

### `backend/models/configuration/`
- Configuration models directory.

### `backend/models/core.py`
- Core model definitions.

### `backend/models/core/user.py`
- Core user model (subdirectory).

### `backend/models/erp.py`
- ERP model definitions.

### `backend/models/finance/general_ledger.py`
- General ledger model (subdirectory).

### `backend/models/geography/`
- 7 geography model files.

### `backend/models/gateway/`
- Gateway models directory.

### `backend/models/identity/`
- Identity models directory.

### `backend/models/incident.py`
- Incident model.

### `backend/models/logistics/logistics_entities.py`
- Logistics entity models (subdirectory).

### `backend/models/marketing.py`
- Marketing model definitions.

### `backend/models/onboarding.py`
- Onboarding model definitions.

### `backend/models/orders/order_entities.py`
- Order entity models (subdirectory).

### `backend/models/permissions.py`
- Permissions model definitions.

### `backend/models/permissions/permission_entities.py`
- Permission entity models (subdirectory).

### `backend/models/promotions.py`
- Promotions model definitions.

### `backend/models/supplier/suppliers.py`
- Supplier models (subdirectory).

### `backend/models/upload_job.py`
- Upload job model definitions.

### `backend/db/schemas.py`
- Database schema definitions.

### `backend/db/treasury_seeder.py`
- Treasury seed data.

### `backend/db/database_logging.py`
- Database query logging instrumentation.

### `backend/db/migrations/`
- Alembic migration environment: `env.py`, `script.py.mako`, `versions/` directory with migration scripts, `new_tables.py`.

### `backend/providers/_base.py`
- Base provider class.

### `backend/providers/payments/_common.py`
- Shared payment provider utilities.

### `backend/providers/payments/base.py`
- Base payment provider class.

### `backend/routers/generated/auto_router.py`
- Auto-generated router (Design 3) emitted by `routers/generated/auto_router.py` directly into the routers surface folder.

### `backend/alembic/`
- Alembic migration environment directory.

### `backend/alembic.ini`
- Alembic configuration file.

### `backend/audit_controllers.py`
- Root-level audit controllers module.

### `backend/_analyze_controllers.py`
- Controller analysis script.

### `backend/_analyze_routers_for_migration.py`
- Router migration analysis script.

### `backend/_migration_trash/`
- Migration trash directory with 14+ files.

### `backend/migration_helpers.py`
- Migration helper utilities.

### `backend/tools/`
- Tools directory.

### `backend/var/`
- Variable data directory.

---

## Domain: Frontend (Web App)

**Feature:** Next.js 15 web application with React 19, TypeScript, Tailwind CSS, Zustand state management, App Router, role-based layouts.

### `frontend/web_app/`
- Next.js web application root.

### `frontend/web_app/src/app/`
- App Router routes: `layout.tsx` (root layout), `page.tsx` (redirects to /products), `error.tsx`, `loading.tsx`, `not-found.tsx`, plus 40+ route directories.

### `frontend/web_app/src/components/`
- 83+ React components: layout shells (`AdminLayout`, `SupplierLayout`, `LogisticsPartnerLayout`), product display (`ProductCard`, `ProductGrid`, `QuickViewModal`), search (`UnifiedSearchBar`, `FilterSearchBar`, `AdvancedFilter`), admin (`AdminChatPanel`, `EmailCampaignManager`, `FraudDetectionDashboard`), supplier (`SmartMediaUpload`, `SmartPricingPanel`, `VoiceProductInput`), comms (`CommandPalette`, `CommShell`, `Composer`, `UnifiedInboxBridge`), country workbench (`CountryDetailWorkspace`, `CountryMapView`), EMS (`ActivityTimeline`, `OrgChartTree`, `PayrollWorkflow`), UI primitives (`Button`, `Card`, `GlassCard`, `Modal`, `Table`).

### `frontend/web_app/src/lib/`
- 53 library files: API client (`api/client.ts`, `api/auth.ts`, `api/errors.ts`), state stores (`cartStore.ts`, `wishlistStore.ts`, `notificationStore.ts`, `currencyStore.ts`, `localeStore.ts`, `themeStore.ts`, `authModalStore.ts`, `backgroundJobStore.ts`, `effectStore.ts`, `densityContext.tsx`), configs (`checkoutConfig.ts`, `adminPanelConfig.ts`, `productCardModel.ts`, `variantConfig.ts`), hooks (`useAdminApi.ts`, `useAdminCountry.tsx`, `useApi.ts`, `useAuth.tsx`, `useRequireAuthAction.ts`, `useTranslate.ts`, `useBgABTest.ts`, `useBgRecommendations.ts`, `userRealtime.ts`, `trackingRealtime.ts`, `backgroundJobRealtime.ts`), utilities (`utils.ts`, `logger.ts`, `errorLogging.ts`, `errorReporter.ts`, `listResponse.ts`, `approvalMatrixApi.ts`, `authCapabilities.ts`, `authVerification.ts`, `authRedirects.ts`, `serverAuth.ts`, `hierarchyApi.ts`, `payoutsApi.ts`, `productQrBundle.ts`, `recentlyViewedStore.ts`, `uploadOrchestrator.ts`, `i18n.ts`, `icons.ts`, `panelNavigation.ts`, `categoryVariantBridge.ts`, `crossBorderService.ts`, `addressBook.ts`, `deliveryStore.ts`, `toastStore.ts`).

### `frontend/web_app/src/hooks/`
- Custom React hooks: auth, chat, comms, country, cross-border, websocket, etc.

### `frontend/web_app/src/services/`
- `addressFormatService.ts`, `crossBorderService.ts`, `localizationService.ts`.

### `frontend/web_app/src/styles/`
- `globals.css`, `glow.css`, `comm.css`, `panel-modern.css`, `tokens.css`, `_vars.txt`.

### `frontend/web_app/src/theme/`
- `animations.ts`.

### `frontend/web_app/src/types/`
- `framer-motion.d.ts`.

### `frontend/web_app/src/__tests__/`
- Jest tests: Chatbot, designSystemTokens, ErrorBoundary, plus component/lib/page test suites.

### `frontend/web_app/e2e/`
- Playwright E2E test specs.

### `frontend/web_app/public/`
- Static assets: images, fonts, icons, favicon, robots.txt, etc.

### `frontend/web_app/next.config.ts`
- Next.js config with rewrites to FastAPI backend.

### `frontend/web_app/middleware.ts`
- Middleware: auth guard, role-based redirects, slugification.

### `frontend/web_app/src/app/` (additional routes)
- `archive/` — archived content page
- `auth/` — OAuth callback handler
- `barcode-scan/` — barcode scanning page
- `brand/` — brand landing pages
- `contact/` — contact page
- `document.tsx` — custom document
- `global-error.tsx` — global error boundary
- `help/` — help center
- `HomeClient.tsx` — home client component
- `logo-animation/` — logo animation showcase
- `newsletter/` — newsletter unsubscribe/preferences
- `r/[code]/` — referral code dynamic route

### `frontend/web_app/src/app/admin/` (additional subdirectories)
- `accounting/`, `banners/`, `barcode/`, `categories/`, `chat/`, `ess/`, `logistics/`, `logistics-partners/`, `organization/`, `supplier-documents/` — additional admin sub-pages.

### `frontend/web_app/src/components/` (additional components)
- `AppFooter.tsx`, `AuthRequiredModal.tsx`, `BackgroundEffect.tsx`, `BackgroundJobCenter.tsx`, `BannerCanvasEditor.tsx`, `BrandLoading.tsx`, `Breadcrumbs.tsx`, `BulkActionBar.tsx`, `Carousel.tsx`, `ChartComponents.tsx`, `ClientDeferred.tsx`, `ColumnVisibilityPanel.tsx`, `CurrencyInit.tsx`, `DataDensityToggle.tsx`, `DirectorySection.tsx`, `EcosystemWidget.tsx`, `ErrorBoundary.tsx`, `ErrorHandlerInit.tsx`, `Footer.tsx`, `Header.tsx`, `HeaderSearchBar.tsx`, `Hero.tsx`, `HomeProductShowcase.tsx`, `InlineActionButtons.tsx`, `Input.tsx`, `KeyboardShortcutsHelp.tsx`, `LoadingSkeleton.tsx`, `LocaleInit.tsx`, `Logo.tsx`, `MobileNav.tsx`, `MobileSearchOverlay.tsx`, `NewsletterSignup.tsx`, `PanelPage.tsx`, `PanelShell.tsx`, `PillTag.tsx`, `ProductCard.test.tsx`, `SearchParamsReader.tsx`, `SignaturePad.tsx`, `StatsGrid.tsx`, `TestimonialsWidget.tsx`, `ThemeProvider.tsx`, `ThemeToggle.tsx`, `TickerBar.tsx`, `ToastContainer.tsx`, `TopCategoriesWidget.tsx`, `TranslatedText.tsx`, `VideoScrollingRow.tsx`.

### `frontend/web_app/src/components/` (additional subdirectories)
- `map/` — `LocationPicker.tsx`, `MapView.tsx`, `mapMarker.ts`, `parseLocation.ts`
- `auth/` — `GoogleSignInButton.tsx`
- `ui/shared/` — `Badge.tsx`, `EmptyState.tsx`, `index.ts`, `LoadingSkeleton.tsx`, `Modal.tsx`, `Table.tsx`
- `ui/` additional: `Dropdown.tsx`, `FormLayout.tsx`, `StatCard.tsx`
- `supplier/upload/` — supplier upload subcomponents
- `country/` additional: `AuditTrailTimeline.tsx`, `GhostRowForm.tsx`, `InternalCommunicationsSystem.tsx`, `LocationTrackerMap.tsx`
- `ems/` additional: `ChatEnrichment.tsx`

### `frontend/web_app/src/lib/` (additional files)
- `api/country.ts` — country API client
- `api/index.ts` — API barrel export
- `backgroundJobs.ts` — background job utilities
- `globalErrorHandler.ts` — global error handler setup
- `types.ts` — TypeScript type definitions

### `frontend/web_app/src/hooks/` (additional hooks)
- `useApprovalCheck.ts`, `useChatWebSocket.ts`, `useCommState.ts`, `useCountryAccess.ts`, `usePanelLayout.ts`, `useSearchHistory.ts`, `useUnifiedInbox.ts`.

### `frontend/web_app/src/__mocks__/`
- Jest mocks: `nanoid.ts`, `styleMock.js`.

### `frontend/web_app/src/logo/`
- Web-specific logo components (6 files).

### `frontend/web_app/src/utils/`
- `test.ts` utility.

### `frontend/web_app/` (root config/build files)
- `package.json`, `package-lock.json`, `tsconfig.json`, `next-env.d.ts`, `tailwind.config.js`, `postcss.config.js`, `eslint.config.js`, `jest.config.js`, `jest.setup.ts`, `playwright.config.ts`, `playwright.__tests__.config.ts`, `playwright.config.ts.bak`, `tsconfig.tsbuildinfo`, `.env.example`, `.env.local`, `.gitignore`, `Dockerfile`, `README.md`, `ERROR_HANDLING.md`.

---

## Domain: Frontend (Mobile App)

**Feature:** React Native / Expo mobile application mirroring web_app routes with platform-specific adapters.

### `frontend/mobile_app/`
- React Native / Expo app with `app/`, `components/` (17+ components), `e2e/` (7+ test files), `theme/`, `scripts/`, `assets/`, `android/` directories. Uses `.native.tsx` / `.web.tsx` file extensions for cross-platform components.

### `frontend/shared/`
- `@zozi/shared` — platform-agnostic package built via `tsc`, provides: `api-core.ts` (TokenAdapter interface), `cartHelpers`, `checkoutHelpers`, `orderHelpers`, `wishlistHelpers`, `notificationHelpers`, `productQuery`, `theme`, `realtime`, `requestCache`, `i18n`, `returnsApi`, `statusColors`, `addressHelpers`, `adminListUtils`, `adminPermissions`, `chatbot.ts`, `errorLogging.ts`, `money.ts`, `productHelpers.ts`, `supplierProductOptions.ts`, `theme.native.ts`, `ticketHelpers.ts`, `trackingMap.ts`, `types.ts`, `userRealtimeAlerts.ts`, `utils.ts`. Includes `components/`, `logo/`, `__tests__/` subdirectories.

---

## Domain: Shared Packages

**Feature:** Platform-agnostic code shared between web and mobile.

### `frontend/shared/`
- `@zozi/shared` — built via `tsc`, provides: `api-core.ts` (TokenAdapter interface), `cartHelpers`, `checkoutHelpers`, `orderHelpers`, `wishlistHelpers`, `notificationHelpers`, `productQuery`, `theme`, `realtime`, `requestCache`, `i18n`, `returnsApi`, `statusColors`, `addressHelpers`, `adminListUtils`, `adminPermissions`, `chatbot.ts`, `errorLogging.ts`, `money.ts`, `productHelpers.ts`, `supplierProductOptions.ts`, `theme.native.ts`, `ticketHelpers.ts`, `trackingMap.ts`, `types.ts`, `userRealtimeAlerts.ts`, `utils.ts`. Includes `components/`, `logo/`, `__tests__/` subdirectories. Platform-specific adapters: web adapter (httpOnly cookies + in-memory token) in `src/lib/api/`; mobile adapter in `mobile_app/lib/`.

---

## Feature: E-Commerce Flow

**How it works end-to-end:**

1. **Product Discovery:** Customer browses `/products` → `ProductGrid`/`ProductCard` components fetch from `services/catalog/product_service.py` → SQLAlchemy `Product` model in `commerce.products` schema.
2. **Cart:** Customer adds to cart → `cart_write_service.py` creates/updates `CartItem` → Zustand `cartStore.ts` syncs UI.
3. **Checkout:** Customer proceeds to `/checkout` → `checkoutConfig.ts` orchestrates address, delivery, payment method selection → `commerce_write_service.py` or `orders_write_service.py` creates `Order`.
4. **Payment:** Payment intent created via `services/gateways/payments.py` → provider-specific implementation in `providers/payments/` (Stripe, PayPal, etc.) → `Payment` model updated → webhook processed by `webhook_processor.py`.
5. **Fulfillment:** `fulfillment_service.py` listens for `PaymentConfirmedEvent` → allocates logistics partner → creates `Shipment` → `order_tracking_service.py` generates tracking events.
6. **Delivery:** Logistics partner updates `ShipmentEvent` → customer sees tracking in `/tracking/[id]`.
7. **Post-Purchase:** Customer can review (`reviews_service.py`), return (`returns_service.py`), or create dispute (`disputes_service.py`).
8. **Financials:** `TransactionLedger` records all amounts → `SupplierSettlement` tracks supplier payouts → `PayoutBatch` batches payouts → `treasury_service.py` orchestrates cash movement.

---

## Feature: Admin Operations

**How it works:**

1. Admin logs into `/admin` → `AdminLayout` enforces `admin`/`super_admin` role via `middleware.ts`.
2. Dashboard (`admin_dashboard_controller.py` + `admin_dashboard_service.py`) shows KPIs from `TransactionLedger`, `Order`, `Shipment`.
3. Admin manages products via `admin_products_controller.py` → `catalog/product_admin_write_service.py` → `Product` model CRUD.
4. Admin oversees orders via `admin_orders_controller.py` → `orders/admin_orders_read_service.py` → status updates via `admin_orders_write_service.py`.
5. Admin manages suppliers via `suppliers_controller.py` → `admin/suppliers_service.py` → verification, health scoring, trading.
6. Admin manages finance via `finance/` controllers → `finance_read_service.py`, `finance_automation.py`, `invoice_service.py`.
7. Admin manages payouts via `payouts_controller.py` → `admin/payouts_service.py` → `treasury/payout_approval_write_service.py`.
8. Admin manages communications via `comms` controllers → `email_management_service.py`, `unified_inbox_service.py`, `campaign_geography_service.py`.
9. Admin manages HR via `hr/` controllers → `employees_service.py`, `payroll_service.py`, `performance_service.py`.

---

## Feature: Supplier Operations

**How it works:**

1. Supplier registers → `supplier_profile_create_controller.py` → `supplier_profile_create_service.py` → `SupplierProfile` model created.
2. Supplier onboards → `onboarding_pipeline.py` → document upload, verification, health scoring (`supplier_health_engine.py`).
3. Supplier uploads products → `supplier_products_upload_controller.py` → `supplier_products_upload_service.py` → AI description generation (`ai_service.py`), background removal (`bg_removal_service.py`), variant config.
4. Supplier manages orders → `supplier_orders.py` → `supplier_order_service.py` → fulfillment via `fulfillment_service.py`.
5. Supplier views payouts → `supplier_payouts.py.bak` → `supplier_payout_service.py` → `treasury/payout_read_service.py`.
6. Supplier views analytics → `supplier_analytics_controller.py` → `supplier_analytics_service.py`.
7. Public storefront: `/supplier-storefront/[slug]` → `supplier_service.py` → `Product` queries filtered by supplier.

---

## Feature: Logistics Partner Flow

**How it works:**

1. Logistics partner registers → `logistics_partner_verify.py` → `logistics_partner_verify_service.py` → `LogisticsPartner` model.
2. Partner configures service areas → `logistics_partner_write_service.py` → `LogisticsPartnerServiceArea`.
3. Partner sets pricing → `logistics_partner_pricing.py` → `LogisticsPricingProfile`, `LogisticsCategoryPricingRule`.
4. Orders allocated to partner → `fulfillment_service.py` → `logistics_service.py` → `Shipment` created.
5. Partner scans/updates status → `logistics_partner_verify_service.py` → `ShipmentEvent` created.
6. Partner views shipments → `logistics_orders_v2_service.py`, `partner_shipments_service.py`.
7. Customer tracks → `/tracking/[id]` → `order_tracking_service.py` → `ShipmentEvent` stream.

---

## Feature: Chat & Messaging

**How it works:**

1. User opens `/chatbot` → `Chatbot.tsx` component connects to WebSocket → `chat_write_service.py` / `chat_read_service.py`.
2. Unified inbox (`comms/` components) aggregates email, chat, video, incident rooms → `unified_inbox_service.py`.
3. Admin comms center → `admin_comms_unified_controller.py` → `admin_comms_unified_service.py`.
4. Real-time chat → `websocket_chat.py` / `realtime_chat_service.py` → `websocket_manager.py`.
5. Video conferencing → `video_room_service.py` / `video_room_write_service.py` → `/meet/[room]`.
6. Email campaigns → `email_management_service.py` → `email_gateway.py` → provider integration.
7. Push notifications → `push_notifications_service.py` → provider integration (Firebase, etc.).

---

## Feature: Real-Time Features

**How it works:**

1. WebSocket routes mounted in `main.py`: `/ws/user` (user chat), `/ws/admin/background-jobs` (admin job status).
2. `websocket_manager.py` manages connection pools, rooms, message broadcasting.
3. `realtime.ts` utility provides pub/sub helpers.
4. Frontend hooks (`userRealtime.ts`, `trackingRealtime.ts`, `backgroundJobRealtime.ts`) bridge WebSocket to React state.
5. `UserRealtimeBridge.tsx` component mounts WebSocket listeners and updates Zustand stores.

---

## Appendix: Router Auto-Discovery

`backend/main.py` uses `_load_routers()` which:
1. Scans `backend/routers/**/*.py` recursively.
2. Imports each module via `importlib`.
3. Extracts `router` (APIRouter) and optional `__router_prefix__`.
4. Includes router in FastAPI app with prefix.
5. Also includes `public_router` if present.
6. Fails fast in production if any router fails to load.

This means new routers are automatically registered without touching `main.py`.

---

## Appendix: Key Patterns

### Controller-Delegator Pattern
- **Controllers** (`backend/controllers/`): Thin FastAPI route handlers. Validate input, call services, return responses. Often re-export a router from a service module.
- **Services** (`backend/services/`): Business logic, database access, external calls. Organized by domain (orders, products, supplier, etc.).
- **Delegators**: Some controllers simply import and re-export a router from a service module (e.g., `controllers/orders/orders_controller.py` → `services/orders/orders_service.py`).

### Service Layer Organization
- `services/<domain>/` — domain-specific services (e.g., `services/orders/`, `services/supplier/`).
- `services/core/` — shared core services used by multiple domains.
- `services/admin/` — admin-specific service implementations.
- `services/public/` — public-facing service implementations.

### Multi-Schema Database
- PostgreSQL uses schemas: `core`, `commerce`, `logistics`, `finance`, `treasury`, `hr`, `country`, `media`, `ai`, `communication`, `audit`, `security`, `analytics`, `configuration`, `supplier`, `customer`.
- SQLite maps all schemas to default schema via `schema_translate_map`.

### Row-Level Security (RLS)
- Country-based RLS: `country_rls.py`, `rls_interceptor.py`, `rls_middleware.py`, `rls_dependency.py`.
- Enforced at database level via SQLAlchemy events and FastAPI dependencies.

### Role-Based Access
- Roles: `customer`, `supplier`, `logistics_partner`, `admin`, `super_admin`.
- Frontend middleware enforces route access.
- Backend permissions via `services/permissions/`, `services/security/permission_service.py`.

### Event-Driven Architecture
- Domain events defined in `events/` (e.g., `PaymentConfirmedEvent`).
- `event_publisher.py` publishes events.
- Services subscribe to events (e.g., `fulfillment_service.py` listens for payment events).

### Provider Pattern
- External integrations abstracted behind providers (`providers/payments/`, `providers/storage.py`, `providers/media/`, `providers/ai/`).
- Base classes define contracts; concrete implementations handle specifics.
- Registry pattern for dynamic provider selection.

---

*This file was auto-generated by exploring the codebase structure. For line-by-line details, read the individual source files.*
