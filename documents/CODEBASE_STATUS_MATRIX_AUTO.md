# ZOZI Codebase Status Matrix — SPEC-DRIVEN (v5.3 Ollama semantic mode)

**Generated:** 2026-08-07 05:43:30 · **Engine:** v5.3
**Matching mode:** 🦙 Ollama semantic embeddings
**LLM verification:** llama3.2:latest

## 🔬 Scan Summary

| Layer | Files |
|---|---|
| Backend Routers | 149 |
| Backend Controllers | 67 |
| Backend Services | 270 |
| Backend Models | 27 |
| Backend Schemas (Pydantic) | 3 |
| Backend Middleware | 22 |
| Backend Utils | 61 |
| Backend Providers | 38 |
| Backend Core | 38 |
| Backend Data/Seed | 19 |
| Web Pages | 130 |
| Web Components | 263 |
| Web Lib/Hooks | 120 |
| Web App Files | 60 |
| Frontend Scripts | 7 |
| Mobile Screens | 116 |
| Mobile Components | 71 |
| Mobile Lib/Hooks | 48 |
| Backend Tests | 63 |
| Web Tests | 77 |
| Mobile Tests | 65 |
| E2E Tests | 65 |
| Migrations | 29 |
| Backend Scripts | 4 |
| Backend Other | 29 |
| **Total** | **1841** |

---

## 📊 Executive Summary

| # | System | Scope | Files | Dead | DB | API | State | Caps | Sections | Tests | Steps | **Overall** | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Unified Communication Workspace (Chat · Email · Video · Contacts · Files)** | Admin · Employee · Supplier | 1061 | 147 | n/a | n/a | n/a | n/a | 79.6% | 75.0% | n/a | **58.1%** | 🟡 |
| 2 | **Product & Catalog System** | Customer · Supplier · Admin | 1183 | 172 | 0.0% | n/a | n/a | n/a | 76.7% | 25.0% | n/a | **15.7%** | ❌ |
| 3 | **Cash Management / Finance / Treasury System** | Admin · Supplier · Logistor | 963 | 168 | n/a | n/a | n/a | n/a | 91.1% | 75.0% | n/a | **65.8%** | 🟡 |
| 4 | **Order Tracker & Order Management** | Customer · Supplier · Logistor · Admin | 1704 | 313 | 62.5% | 100.0% | 81.0% | 78.0% | 77.0% | 100.0% | 91.3% | **62.0%** | 🟡 |

**Weighted overall: 49.6%**

- 🌐 Section I — System & Infrastructure Features: 1 feature(s) · **58.1%**
- 👤 Section II — Customer Features & Systems Status: 2 feature(s) · **38.9%**
- 🏭 Section III — Supplier Panel Features & Systems Status: 4 feature(s) · **49.6%**
- 🚚 Section IV — Logistor (Logistics Partner) Panel Features & Systems Status: 2 feature(s) · **63.8%**
- 👨‍💼 Section V — Admin Panel Features & Systems Status: 4 feature(s) · **49.6%**

---

## 🌐 Section I — System & Infrastructure Features

| Feature | TODO Ref | Backend: Controllers | Backend: Services | Backend: Router | Web App Pages | Mobile Screens | Shared / Utils | API Routes | DB Model(s) | Backend Tests | Web Tests | Mobile Tests | Completion % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 🟡 **Unified Communication Workspace (Chat · Email · Video · Contacts · Files)** | — | ✅ `ai_controller.py`<br>`banner_controller.py`<br>`cart_controller.py`<br>`chatbot_controller.py`<br>`comm_controller.py`<br>`commerce/reviews.py`<br>`comms/comm_controller.py`<br>`coupons_controller.py`<br>`employees_controller.py`<br>`iam_controller.py`<br>`invoice_controller.py`<br>`payments_controller.py`<br>`product_verification_controller.py`<br>`promotion_controller.py`<br>`search_controller.py`<br>`sub_ledger_controller.py` | ✅ `_registry.py`<br>`advanced_filter_service.py`<br>`advanced_search_engine.py`<br>`ai_automation_service.py`<br>`ai_copy_jobs.py`<br>`ai_service.py`<br>`ai_variant_config.py`<br>`audit/audit_trail_service.py`<br>`auth_service.py`<br>`background_check.py`<br>`bg_removal_presets.py`<br>`bg_removal_service.py`<br>`cash_flow_forecast_service.py`<br>`chat_enrichment.py`<br>`chat_system.py`<br>`comms/chat_enrichment.py`<br>`comms/chat_read_service.py`<br>`comms/command_center_query_service.py`<br>`comms/communication_audit.py`<br>`comms/communication_read_service.py`<br>`comms/communication_write_service.py`<br>`comms/content_service.py`<br>`comms/email_enrichment.py`<br>`comms/email_event_service.py`<br>`comms/email_gateway.py`<br>`comms/email_management_service.py`<br>`comms/email_reputation.py`<br>`comms/email_write_service.py`<br>`comms/entity_chat_service.py`<br>`comms/entity_messaging.py`<br>`comms/escalation_sla.py`<br>`comms/external_contact.py`<br>`comms/internal_communication.py`<br>`comms/notification_engine.py`<br>`comms/notification_worker.py`<br>`comms/translation_service.py`<br>`comms/video_conferencing.py`<br>`comms/video_service.py`<br>`comms/websocket_chat.py`<br>`comms/websocket_manager.py`<br>`communication_audit.py`<br>`communication_write_service.py`<br>`content_service.py`<br>`country_ai_research.py`<br>`country_read_service.py`<br>`country_research.py`<br>`country_write_service.py`<br>`cross_border_detection.py`<br>`data_residency.py`<br>`disputes_write_service.py`<br>… +58 more (full list in appendix) | ✅ `accounting.py`<br>`ai_upload.py`<br>`audit.py`<br>`auth.py`<br>`batch_upload.py`<br>`chat.py`<br>`chat_api.py`<br>`chat_enrichment.py`<br>`chatbot.py`<br>`comm.py`<br>`comms_unified.py`<br>`contact.py`<br>`country_auto_populate.py`<br>`country_staff.py`<br>`email.py`<br>`email_controller.py`<br>`email_enrichment.py`<br>`entity_chat.py`<br>`entity_communication.py`<br>`ess.py`<br>`export.py`<br>`finance_erp.py`<br>`frontend_errors.py`<br>`hierarchy.py`<br>`hr_dashboard.py`<br>`imports.py`<br>`internal_channels.py`<br>`invoices.py`<br>`location_api.py`<br>`messaging.py`<br>`notifications.py`<br>`orders.py`<br>`performance.py`<br>`permissions.py`<br>`product_videos.py`<br>`returns.py`<br>`search.py`<br>`tickets.py`<br>`trading.py`<br>`upload_jobs.py`<br>`video.py`<br>`video_controller.py`<br>`geography/country_router_service.py`<br>`utils/middleware_helpers.py` | ❌ — | ✅ `theme.native.ts` | ✅ `utils/analytics_service.py`<br>`utils/api_docs.py`<br>`utils/audit.py`<br>`utils/auth.py`<br>`utils/background_jobs.py`<br>`utils/backup.py`<br>`utils/config.py`<br>`utils/constants.py`<br>`utils/email_service.py`<br>`utils/entity_messaging.py`<br>`utils/error_handler.py`<br>`utils/file_validation.py`<br>`utils/invoice_html.py`<br>`utils/key_rotation.py`<br>`utils/logging_config.py`<br>`utils/ml_worker.py`<br>`utils/multi_secret_webhook.py`<br>`utils/order_tracking.py`<br>`utils/redis_client.py`<br>`utils/rls_interceptor.py`<br>`utils/security_audit.py`<br>`utils/security_metrics.py`<br>`utils/soft_delete.py`<br>`utils/staff_permissions.py`<br>`utils/websocket_manager.py`<br>`HomeClient.tsx`<br>`auth/callback/SocialAuthCallbackClient.tsx`<br>`global-error.tsx`<br>`hooks/useApprovalCheck.ts`<br>`hooks/useChatHistory.ts`<br>`hooks/useChatWebSocket.ts`<br>`hooks/useCommState.ts`<br>`hooks/useCountryAccess.ts`<br>`hooks/useCountryAutoPopulate.ts`<br>`hooks/useCrossBorder.ts`<br>`hooks/useSendMessage.ts`<br>`hooks/useThreadMessages.ts`<br>`hooks/useUnifiedInbox.ts`<br>`hooks/useWebSocket.ts`<br>`lib/api/client.ts`<br>`lib/api/country.ts`<br>`lib/api/errors.ts`<br>`lib/api/index.ts`<br>`lib/approvalMatrixApi.ts`<br>`lib/authCapabilities.ts`<br>`lib/authRedirects.ts`<br>`lib/authVerification.ts`<br>`lib/backgroundJobRealtime.ts`<br>`lib/backgroundJobs.ts`<br>`lib/categoryVariantBridge.ts`<br>… +18 more (full list in appendix) | ❌ — | ❌ — | ✅ `playwright/e2e/auth.spec.ts`<br>`playwright/e2e/finance-automation.spec.ts`<br>`playwright/helpers/auth.ts`<br>`test_auto_payout_sweep.py`<br>`test_background_jobs.py`<br>`test_cart.py`<br>`test_circuit_breaker.py`<br>`test_communication_services.py`<br>`test_country_research.py`<br>`test_ems_edge_cases.py`<br>`test_ems_lifecycle.py`<br>`test_error_handling.py`<br>`test_export_read_service.py`<br>`test_finance_audit.py`<br>`test_health.py`<br>`test_middleware_helpers.py`<br>`test_models.py`<br>`test_versioning.py` | ✅ `__tests__/chatbot.test.ts`<br>`__tests__/checkoutHelpers.test.ts`<br>`chatbot.test.ts`<br>`checkoutHelpers.test.ts`<br>`web_app/__tests__/browser.spec.ts`<br>`Chatbot.test.tsx`<br>`components/ApprovalActionModal.test.tsx`<br>`components/CountryDetailWorkspace.test.tsx`<br>`components/CountryResearchPanel.test.tsx`<br>`components/Header.test.tsx`<br>`components/QuickViewModal.test.tsx`<br>`components/emailComponents.test.tsx`<br>`lib/adminPermissions.test.ts`<br>`lib/api.test.ts`<br>`lib/currencyStore.test.ts`<br>`lib/requestCache.test.ts`<br>`lib/useApprovalCheck.test.tsx`<br>`lib/useAuth.preferences.test.tsx`<br>`lib/userRealtime.test.ts`<br>`pages/adminCommunicationHub.test.tsx`<br>`pages/adminDashboardNavigation.test.tsx`<br>`pages/adminExportsPanel.test.tsx`<br>`pages/adminFinanceCodVerification.test.tsx`<br>`pages/adminLogisticsPages.test.tsx`<br>`pages/adminManagementPages.test.tsx`<br>`pages/adminPaymentsPage.test.tsx`<br>`pages/adminStaffPage.test.tsx`<br>`pages/adminStandalonePages.test.tsx`<br>`pages/bulkOperations.test.tsx`<br>`pages/cart.test.tsx`<br>`pages/checkout.test.tsx`<br>`pages/commissionPolicySync.test.tsx`<br>`pages/countryAdmin.spec.ts`<br>`pages/forgotPassword.test.tsx`<br>`pages/help.test.tsx`<br>`pages/login.test.tsx`<br>`pages/productDetail.test.tsx`<br>`pages/products.test.tsx`<br>`pages/profile.test.tsx`<br>`pages/promotionBuilderPanel.test.tsx`<br>`pages/realtimeRefreshPages.test.tsx`<br>`pages/supplierOrdersPage.test.tsx`<br>`pages/supplierPayoutsPage.test.tsx`<br>`pages/supplierProductsPage.test.tsx`<br>`pages/supplierProfilePage.test.tsx`<br>`pages/supplierRegister.test.tsx`<br>`pages/supplierStorefront.test.tsx`<br>`pages/supplierSupportPage.test.tsx`<br>`pages/trackingPage.test.tsx` | ❌ — | **58.1%** |

---

## 👤 Section II — Customer Features & Systems Status

| Feature | TODO Ref | Backend: Controllers | Backend: Services | Backend: Router | Web App Pages | Mobile Screens | Shared / Utils | API Routes | DB Model(s) | Backend Tests | Web Tests | Mobile Tests | Completion % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ❌ **Product & Catalog System** | — | ❌ — | ✅ `customer_health_engine.py` | ✅ `customer_health.py` | ✅ `web_app/archive/page.tsx`<br>`web_app/barcode-scan/page.tsx`<br>`web_app/brand/page.tsx`<br>`web_app/cart/page.tsx`<br>`web_app/chatbot/page.tsx`<br>`web_app/checkout/page.tsx`<br>`web_app/contact/page.tsx`<br>`web_app/invoice/page.tsx`<br>`web_app/meet/[room]/page.tsx`<br>`web_app/newsletter/preferences/page.tsx`<br>`web_app/newsletter/unsubscribe/page.tsx`<br>`web_app/notifications/page.tsx`<br>`web_app/orders/[id]/page.tsx`<br>`web_app/orders/page.tsx`<br>`web_app/page.tsx`<br>`web_app/products/[id]/page.tsx`<br>`web_app/products/page.tsx`<br>`web_app/profile/page.tsx`<br>`web_app/profile/referrals/page.tsx`<br>`web_app/reset-password/page.tsx`<br>`web_app/returns/[id]/page.tsx`<br>`web_app/returns/page.tsx`<br>`web_app/tickets/[id]/page.tsx`<br>`web_app/tracking/[id]/page.tsx`<br>`web_app/verify-email/page.tsx`<br>`web_app/wishlist/page.tsx`<br>`PanelPage.tsx` | ✅ `(auth)/login.tsx`<br>`(auth)/register.tsx`<br>`(auth)/reset-password.tsx`<br>`(auth)/verify-email.tsx`<br>`(tabs)/_layout.tsx`<br>`(tabs)/cart.tsx`<br>`(tabs)/orders/[id].tsx`<br>`(tabs)/products/[id].tsx`<br>`(tabs)/products/index.tsx`<br>`(tabs)/profile.tsx`<br>`_layout.tsx`<br>`archive.tsx`<br>`barcode-scan.tsx`<br>`change-password.tsx`<br>`chatbot.tsx`<br>`checkout.tsx`<br>`coupons.tsx`<br>`edit-profile.tsx`<br>`flash-sales.tsx`<br>`help.tsx`<br>`index.tsx`<br>`invoice.tsx`<br>`newsletter.tsx`<br>`newsletter/preferences.tsx`<br>`newsletter/unsubscribe.tsx`<br>`notification-preferences.tsx`<br>`notifications.tsx`<br>`offers.tsx`<br>`orders.tsx`<br>`products/[id].tsx`<br>`products/index.tsx`<br>`push_notifications.tsx`<br>`referrals.tsx`<br>`returns.tsx`<br>`returns/[id].tsx`<br>`ticket-detail.tsx`<br>`tickets.tsx`<br>`tracking/[id].tsx`<br>`wishlist.tsx`<br>`write-review.tsx`<br>`sentry.config.ts` | ✅ `login/LoginClient.tsx`<br>`register/RegisterClient.tsx` | ❌ — | 🔍 1 tables | ✅ `test_chat.py`<br>`test_orders.py`<br>`test_reviews.py`<br>`test_wishlist.py` | ❌ — | ✅ `addressesScreen.test.ts`<br>`adminAnalyticsScreen.test.tsx`<br>`adminBankAccountsScreen.test.tsx`<br>`adminDashboardScreen.test.ts`<br>`adminMobileAudit.test.tsx`<br>`adminPromotionsHub.test.tsx`<br>`api.test.ts`<br>`authRecoveryScreens.test.tsx`<br>`authStore.test.ts`<br>`backgroundJobs.test.ts`<br>`cartScreen.test.tsx`<br>`cartStore.test.ts`<br>`chatbotScreen.test.tsx`<br>`checkoutFlow.test.ts`<br>`checkoutScreen.test.tsx`<br>`couponsScreen.test.ts`<br>`currencyStore.test.ts`<br>`customerAccountScreens.test.tsx`<br>`flashSalesScreen.test.ts`<br>`homeInsights.test.ts`<br>`loginScreen.test.ts`<br>`loginScreenRouting.test.tsx`<br>`mobileApiRouteHelpers.test.ts`<br>`newsletterPreferencesScreen.test.tsx`<br>`notificationsScreen.test.ts`<br>`ordersScreen.test.ts`<br>`partnerDashboardScreens.test.tsx`<br>`productDetailScreen.test.ts`<br>`productDetailScreenRender.test.tsx`<br>`productRouteFilters.test.ts`<br>`registerScreen.test.ts`<br>`returnsScreen.test.tsx`<br>`searchScreen.test.ts`<br>`supplierBulkScreen.test.tsx`<br>`supplierDocumentsApi.test.ts`<br>`supplierDocumentsScreen.test.tsx`<br>`supplierNotificationPreferencesScreen.test.tsx`<br>`supplierOrdersScreen.test.ts`<br>`supplierPayoutsScreen.test.tsx`<br>`supplierProductAi.test.ts`<br>`supplierProductCreateScreen.test.tsx`<br>`supplierProductForm.test.ts`<br>`supplierSupportScreen.test.tsx`<br>`themeStore.test.ts`<br>`ticketsScreen.test.ts`<br>`toastStore.test.ts`<br>`trackingScreen.test.tsx`<br>`trackingScreenRender.test.tsx`<br>`wishlistStore.test.ts` | **15.7%** |
| 🟡 **Order Tracker & Order Management** | — | ❌ — | ✅ `customer_health_engine.py` | ✅ `customer_health.py` | ✅ `web_app/archive/page.tsx`<br>`web_app/auth/callback/page.tsx`<br>`web_app/barcode-scan/page.tsx`<br>`web_app/brand/page.tsx`<br>`web_app/cart/page.tsx`<br>`web_app/chatbot/page.tsx`<br>`web_app/checkout/page.tsx`<br>`web_app/contact/page.tsx`<br>`web_app/invoice/page.tsx`<br>`web_app/login/page.tsx`<br>`web_app/logo-animation/page.tsx`<br>`web_app/meet/[room]/page.tsx`<br>`web_app/newsletter/preferences/page.tsx`<br>`web_app/newsletter/unsubscribe/page.tsx`<br>`web_app/notifications/page.tsx`<br>`web_app/orders/[id]/page.tsx`<br>`web_app/orders/page.tsx`<br>`web_app/products/[id]/page.tsx`<br>`web_app/products/page.tsx`<br>`web_app/profile/page.tsx`<br>`web_app/profile/referrals/page.tsx`<br>`web_app/r/[code]/page.tsx`<br>`web_app/register/page.tsx`<br>`web_app/reset-password/page.tsx`<br>`web_app/returns/[id]/page.tsx`<br>`web_app/returns/page.tsx`<br>`web_app/tickets/[id]/page.tsx`<br>`web_app/tracking/[id]/page.tsx`<br>`web_app/verify-email/page.tsx`<br>`web_app/wishlist/page.tsx`<br>`PanelPage.tsx` | ✅ `(auth)/forgot-password.tsx`<br>`(auth)/login.tsx`<br>`(auth)/register.tsx`<br>`(auth)/reset-password.tsx`<br>`(auth)/verify-email.tsx`<br>`(tabs)/_layout.tsx`<br>`(tabs)/cart.tsx`<br>`(tabs)/orders/[id].tsx`<br>`(tabs)/orders/index.tsx`<br>`(tabs)/products/[id].tsx`<br>`(tabs)/products/index.tsx`<br>`(tabs)/profile.tsx`<br>`_layout.tsx`<br>`archive.tsx`<br>`barcode-scan.tsx`<br>`change-password.tsx`<br>`chatbot-history.tsx`<br>`chatbot.tsx`<br>`checkout.tsx`<br>`coupons.tsx`<br>`edit-profile.tsx`<br>`flash-sales.tsx`<br>`help.tsx`<br>`invoice.tsx`<br>`newsletter.tsx`<br>`newsletter/preferences.tsx`<br>`newsletter/unsubscribe.tsx`<br>`notification-preferences.tsx`<br>`notifications.tsx`<br>`offers.tsx`<br>`orders.tsx`<br>`orders/[id].tsx`<br>`products/[id].tsx`<br>`push_notifications.tsx`<br>`r/[code].tsx`<br>`referrals.tsx`<br>`returns.tsx`<br>`returns/[id].tsx`<br>`settings.tsx`<br>`ticket-detail.tsx`<br>`tickets.tsx`<br>`tracking/[id].tsx`<br>`wishlist.tsx`<br>`write-review.tsx`<br>`playwright.config.ts` | ✅ `login/LoginClient.tsx`<br>`register/RegisterClient.tsx` | 🔍 1 found | 🔍 8 tables | ✅ `test_chat.py`<br>`test_orders.py`<br>`test_reviews.py`<br>`test_wishlist.py` | ❌ — | ✅ `addressesScreen.test.ts`<br>`adminAnalyticsScreen.test.tsx`<br>`adminBankAccountsScreen.test.tsx`<br>`adminDashboardScreen.test.ts`<br>`adminListUtils.test.ts`<br>`adminManagementUtils.test.ts`<br>`adminMobileAudit.test.tsx`<br>`adminPromotionsHub.test.tsx`<br>`api.test.ts`<br>`authRecoveryScreens.test.tsx`<br>`authStore.test.ts`<br>`backgroundJobStore.test.ts`<br>`backgroundJobs.test.ts`<br>`cartScreen.test.tsx`<br>`cartStore.test.ts`<br>`chatbotScreen.test.tsx`<br>`checkoutFlow.test.ts`<br>`checkoutScreen.test.tsx`<br>`countryContext.test.tsx`<br>`couponsScreen.test.ts`<br>`currencyStore.test.ts`<br>`customerAccountScreens.test.tsx`<br>`flashSalesScreen.test.ts`<br>`jest.setup.ts`<br>`localeStore.test.ts`<br>`loginScreen.test.ts`<br>`loginScreenRouting.test.tsx`<br>`mobileApiRouteHelpers.test.ts`<br>`newsletterPreferencesScreen.test.tsx`<br>`notificationsScreen.test.ts`<br>`ordersScreen.test.ts`<br>`partnerDashboardScreens.test.tsx`<br>`productDetailScreen.test.ts`<br>`productDetailScreenRender.test.tsx`<br>`productRouteFilters.test.ts`<br>`registerScreen.test.ts`<br>`returnsScreen.test.tsx`<br>`rootLayout.test.tsx`<br>`searchScreen.test.ts`<br>`supplierBulkScreen.test.tsx`<br>`supplierDocumentsApi.test.ts`<br>`supplierDocumentsScreen.test.tsx`<br>`supplierNotificationPreferencesScreen.test.tsx`<br>`supplierOrdersScreen.test.ts`<br>`supplierPayoutsScreen.test.tsx`<br>`supplierProductAi.test.ts`<br>`supplierProductCreateScreen.test.tsx`<br>`supplierShipmentWorkspace.test.ts`<br>`supplierSupportScreen.test.tsx`<br>`themeStore.test.ts`<br>… +6 more (full list in appendix) | **62.0%** |

---

## 🏭 Section III — Supplier Panel Features & Systems Status

| Feature | TODO Ref | Backend: Controllers | Backend: Services | Backend: Router | Web App Pages | Mobile Screens | Shared / Utils | API Routes | DB Model(s) | Backend Tests | Web Tests | Mobile Tests | Completion % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 🟡 **Unified Communication Workspace (Chat · Email · Video · Contacts · Files)** | — | ✅ `orders_controller.py`<br>`products_controller.py`<br>`returns_controller.py`<br>`supplier/badge.py`<br>`supplier/profile.py`<br>`supplier_controller.py`<br>`supplier_document_controller.py` | ✅ `auth_write_service.py`<br>`automation_scheduler.py`<br>`cash_management_service.py`<br>`commission_engine.py`<br>`comms/payout_notification_service.py`<br>`comms/proxy_communication.py`<br>`comms/transactional_email_service.py`<br>`downstream_wiring.py`<br>`finance/supplier_finance_service.py`<br>`finance_transfer_service.py`<br>`general_ledger_service.py`<br>`geography/legal_contract_service.py`<br>`legal_contract_service.py`<br>`media_service.py`<br>`payout_batch_service.py`<br>`payout_engine.py`<br>`payout_notification_service.py`<br>`proxy_communication.py`<br>`refund_posting_service.py`<br>`supplier_badge_service.py`<br>`supplier_health_engine.py`<br>`supplier_onboarding_service.py`<br>`suppliers_write_service.py`<br>`transactional_email_service.py`<br>`upload_job_service.py` | ✅ `admin.py`<br>`automation.py`<br>`commission.py`<br>`countries.py`<br>`finance.py`<br>`payout_approval.py`<br>`products.py`<br>`supplier.py`<br>`supplier_bg_ab_test.py`<br>`supplier_documents.py`<br>`supplier_finance.py`<br>`supplier_health.py`<br>`supplier_orders.py`<br>`supplier_products.py` | ✅ `web_app/supplier/(auth)/login/page.tsx`<br>`web_app/supplier/(auth)/register/page.tsx`<br>`web_app/supplier/analytics/page.tsx`<br>`web_app/supplier/batch-upload/page.tsx`<br>`web_app/supplier/bulk/page.tsx`<br>`web_app/supplier/credibility/page.tsx`<br>`web_app/supplier/labels/[id]/page.tsx`<br>`web_app/supplier/labels/page.tsx`<br>`web_app/supplier/notification-preferences/page.tsx`<br>`web_app/supplier/orders/[id]/page.tsx`<br>`web_app/supplier/orders/page.tsx`<br>`web_app/supplier/payouts/page.tsx`<br>`web_app/supplier/products/[id]/page.tsx`<br>`web_app/supplier/products/add/page.tsx`<br>`web_app/supplier/products/page.tsx`<br>`web_app/supplier/profile/page.tsx`<br>`web_app/supplier/regions/page.tsx`<br>`web_app/supplier/reports/page.tsx`<br>`web_app/supplier/support/page.tsx`<br>`web_app/supplier/terms/page.tsx`<br>`web_app/supplier/upload/bg-compare/page.tsx`<br>`web_app/supplier/videos/upload/page.tsx`<br>`web_app/suppliers/[id]/page.tsx` | ✅ `supplier/bulk.tsx`<br>`supplier/credibility.tsx`<br>`supplier/dashboard.tsx`<br>`supplier/documents.tsx`<br>`supplier/guide.tsx`<br>`supplier/invoices.tsx`<br>`supplier/label.tsx`<br>`supplier/login.tsx`<br>`supplier/logistics.tsx`<br>`supplier/notification-preferences.tsx`<br>`supplier/orders.tsx`<br>`supplier/payouts.tsx`<br>`supplier/products/[id].tsx`<br>`supplier/products/index.tsx`<br>`supplier/products/new.tsx`<br>`supplier/profile.tsx`<br>`supplier/regions.tsx`<br>`supplier/register.tsx`<br>`supplier/support.tsx`<br>`supplier/terms.tsx`<br>`suppliers/[id].tsx` | ✅ `lib/utils.ts` | ❌ — | ❌ — | ✅ `test_api_endpoints.py`<br>`test_orders_audit.py`<br>`test_orders_controller_audit.py`<br>`test_search_endpoints.py`<br>`test_shipping_quote.py`<br>`test_suppliers.py` | ✅ `pages/supplierBulkAi.test.tsx` | ❌ — | **58.1%** |
| ❌ **Product & Catalog System** | — | ✅ `orders_controller.py`<br>`products_controller.py`<br>`returns_controller.py`<br>`supplier/badge.py`<br>`supplier/inventory.py`<br>`supplier/orders.py`<br>`supplier/products.py`<br>`supplier/profile.py`<br>`supplier_controller.py`<br>`supplier_document_controller.py` | ✅ `auth_write_service.py`<br>`automation_scheduler.py`<br>`cash_management_service.py`<br>`commission_engine.py`<br>`comms/payout_notification_service.py`<br>`comms/proxy_communication.py`<br>`comms/transactional_email_service.py`<br>`country_rls_service.py`<br>`downstream_hooks.py`<br>`downstream_wiring.py`<br>`finance/supplier_finance_service.py`<br>`finance_transfer_service.py`<br>`general_ledger_service.py`<br>`geography/country_rls_service.py`<br>`geography/downstream_hooks.py`<br>`geography/legal_contract_service.py`<br>`legal_contract_service.py`<br>`media_service.py`<br>`payout_batch_service.py`<br>`payout_engine.py`<br>`payout_notification_service.py`<br>`proxy_communication.py`<br>`refund_posting_service.py`<br>`supplier_badge_service.py`<br>`supplier_health_engine.py`<br>`supplier_onboarding_service.py`<br>`suppliers_write_service.py`<br>`transactional_email_service.py`<br>`treasury/treasury_query_service.py`<br>`upload_job_service.py` | ✅ `admin.py`<br>`automation.py`<br>`commission.py`<br>`countries.py`<br>`finance.py`<br>`payout_approval.py`<br>`products.py`<br>`public_suppliers.py`<br>`supplier.py`<br>`supplier_analytics.py`<br>`supplier_bg_ab_test.py`<br>`supplier_documents.py`<br>`supplier_finance.py`<br>`supplier_health.py`<br>`supplier_orders.py`<br>`supplier_products.py`<br>`treasury.py` | ✅ `web_app/supplier/(auth)/login/page.tsx`<br>`web_app/supplier/(auth)/register/page.tsx`<br>`web_app/supplier/analytics/page.tsx`<br>`web_app/supplier/batch-upload/page.tsx`<br>`web_app/supplier/bulk/page.tsx`<br>`web_app/supplier/credibility/page.tsx`<br>`web_app/supplier/dashboard/page.tsx`<br>`web_app/supplier/inventory/page.tsx`<br>`web_app/supplier/labels/[id]/page.tsx`<br>`web_app/supplier/labels/page.tsx`<br>`web_app/supplier/notification-preferences/page.tsx`<br>`web_app/supplier/orders/[id]/page.tsx`<br>`web_app/supplier/orders/page.tsx`<br>`web_app/supplier/page.tsx`<br>`web_app/supplier/payouts/page.tsx`<br>`web_app/supplier/products/[id]/page.tsx`<br>`web_app/supplier/products/add/page.tsx`<br>`web_app/supplier/products/page.tsx`<br>`web_app/supplier/profile/page.tsx`<br>`web_app/supplier/regions/page.tsx`<br>`web_app/supplier/reports/page.tsx`<br>`web_app/supplier/support/page.tsx`<br>`web_app/supplier/terms/page.tsx`<br>`web_app/supplier/upload/bg-compare/page.tsx`<br>`web_app/supplier/upload/page.tsx`<br>`web_app/supplier/videos/upload/page.tsx`<br>`web_app/suppliers/[id]/page.tsx` | ✅ `supplier-storefront/[slug].tsx`<br>`supplier/analytics.tsx`<br>`supplier/bulk.tsx`<br>`supplier/credibility.tsx`<br>`supplier/dashboard.tsx`<br>`supplier/documents.tsx`<br>`supplier/guide.tsx`<br>`supplier/inventory.tsx`<br>`supplier/invoices.tsx`<br>`supplier/label.tsx`<br>`supplier/labels/[id].tsx`<br>`supplier/login.tsx`<br>`supplier/logistics.tsx`<br>`supplier/notification-preferences.tsx`<br>`supplier/orders.tsx`<br>`supplier/payouts.tsx`<br>`supplier/products/[id].tsx`<br>`supplier/products/index.tsx`<br>`supplier/products/new.tsx`<br>`supplier/profile.tsx`<br>`supplier/regions.tsx`<br>`supplier/register.tsx`<br>`supplier/reports.tsx`<br>`supplier/returns.tsx`<br>`supplier/support.tsx`<br>`supplier/terms.tsx`<br>`supplier/upload.tsx`<br>`suppliers/[id].tsx` | ✅ `lib/utils.ts` | ❌ — | 🔍 1 tables | ✅ `test_api_endpoints.py`<br>`test_orders_audit.py`<br>`test_orders_controller_audit.py`<br>`test_search_endpoints.py`<br>`test_shipping_quote.py`<br>`test_suppliers.py` | ✅ `pages/supplierBulkAi.test.tsx` | ❌ — | **15.7%** |
| 🟡 **Cash Management / Finance / Treasury System** | — | ✅ `orders_controller.py`<br>`products_controller.py`<br>`returns_controller.py`<br>`supplier/badge.py`<br>`supplier/orders.py`<br>`supplier/profile.py`<br>`supplier_controller.py`<br>`supplier_document_controller.py` | ✅ `auth_write_service.py`<br>`automation_scheduler.py`<br>`cash_management_service.py`<br>`commission_engine.py`<br>`comms/payout_notification_service.py`<br>`comms/proxy_communication.py`<br>`comms/transactional_email_service.py`<br>`country_rls_service.py`<br>`downstream_hooks.py`<br>`downstream_wiring.py`<br>`finance/supplier_finance_service.py`<br>`finance_transfer_service.py`<br>`general_ledger_service.py`<br>`geography/country_rls_service.py`<br>`geography/downstream_hooks.py`<br>`geography/legal_contract_service.py`<br>`legal_contract_service.py`<br>`media_service.py`<br>`payout_batch_service.py`<br>`payout_notification_service.py`<br>`proxy_communication.py`<br>`refund_posting_service.py`<br>`supplier_badge_service.py`<br>`supplier_health_engine.py`<br>`supplier_onboarding_service.py`<br>`suppliers_write_service.py`<br>`transactional_email_service.py`<br>`treasury/treasury_query_service.py`<br>`upload_job_service.py` | ✅ `admin.py`<br>`automation.py`<br>`commission.py`<br>`countries.py`<br>`finance.py`<br>`payout_approval.py`<br>`products.py`<br>`supplier.py`<br>`supplier_bg_ab_test.py`<br>`supplier_documents.py`<br>`supplier_finance.py`<br>`supplier_health.py`<br>`supplier_orders.py`<br>`supplier_payouts.py`<br>`supplier_products.py`<br>`supplier_profile.py`<br>`treasury.py` | ✅ `web_app/supplier/(auth)/login/page.tsx`<br>`web_app/supplier/(auth)/register/page.tsx`<br>`web_app/supplier/batch-upload/page.tsx`<br>`web_app/supplier/credibility/page.tsx`<br>`web_app/supplier/labels/[id]/page.tsx`<br>`web_app/supplier/labels/page.tsx`<br>`web_app/supplier/logistics/page.tsx`<br>`web_app/supplier/notification-preferences/page.tsx`<br>`web_app/supplier/orders/[id]/page.tsx`<br>`web_app/supplier/orders/page.tsx`<br>`web_app/supplier/page.tsx`<br>`web_app/supplier/payouts/page.tsx`<br>`web_app/supplier/products/[id]/page.tsx`<br>`web_app/supplier/products/add/page.tsx`<br>`web_app/supplier/products/page.tsx`<br>`web_app/supplier/profile/page.tsx`<br>`web_app/supplier/regions/page.tsx`<br>`web_app/supplier/reports/page.tsx`<br>`web_app/supplier/support/page.tsx`<br>`web_app/supplier/terms/page.tsx`<br>`web_app/supplier/upload/bg-compare/page.tsx`<br>`web_app/suppliers/[id]/page.tsx` | ✅ `supplier/bulk.tsx`<br>`supplier/credibility.tsx`<br>`supplier/dashboard.tsx`<br>`supplier/documents.tsx`<br>`supplier/guide.tsx`<br>`supplier/invoices.tsx`<br>`supplier/label.tsx`<br>`supplier/login.tsx`<br>`supplier/logistics.tsx`<br>`supplier/notification-preferences.tsx`<br>`supplier/orders.tsx`<br>`supplier/payouts.tsx`<br>`supplier/products/index.tsx`<br>`supplier/products/new.tsx`<br>`supplier/profile.tsx`<br>`supplier/register.tsx`<br>`supplier/reports.tsx`<br>`supplier/support.tsx`<br>`supplier/terms.tsx`<br>`suppliers/[id].tsx` | ✅ `lib/utils.ts` | ❌ — | ❌ — | ✅ `test_api_endpoints.py`<br>`test_orders_audit.py`<br>`test_search_endpoints.py`<br>`test_shipping_quote.py`<br>`test_suppliers.py` | ❌ — | ❌ — | **65.8%** |
| 🟡 **Order Tracker & Order Management** | — | ✅ `orders_controller.py`<br>`products_controller.py`<br>`returns_controller.py`<br>`supplier/analytics.py`<br>`supplier/badge.py`<br>`supplier/inventory.py`<br>`supplier/orders.py`<br>`supplier/products.py`<br>`supplier/profile.py`<br>`supplier_controller.py`<br>`supplier_document_controller.py` | ✅ `auth_write_service.py`<br>`automation_scheduler.py`<br>`cash_management_service.py`<br>`commission_engine.py`<br>`comms/payout_notification_service.py`<br>`comms/proxy_communication.py`<br>`comms/transactional_email_service.py`<br>`country_rls_service.py`<br>`downstream_hooks.py`<br>`downstream_wiring.py`<br>`finance/supplier_finance_service.py`<br>`finance_transfer_service.py`<br>`general_ledger_service.py`<br>`geography/country_rls_service.py`<br>`geography/downstream_hooks.py`<br>`geography/legal_contract_service.py`<br>`legal_contract_service.py`<br>`media_service.py`<br>`payout_batch_service.py`<br>`payout_engine.py`<br>`payout_notification_service.py`<br>`proxy_communication.py`<br>`refund_posting_service.py`<br>`supplier_badge_service.py`<br>`supplier_health_engine.py`<br>`supplier_onboarding_service.py`<br>`suppliers_write_service.py`<br>`transactional_email_service.py`<br>`treasury/treasury_query_service.py`<br>`upload_job_service.py` | ✅ `admin.py`<br>`automation.py`<br>`commission.py`<br>`countries.py`<br>`finance.py`<br>`payout_approval.py`<br>`products.py`<br>`public_suppliers.py`<br>`supplier.py`<br>`supplier_analytics.py`<br>`supplier_bg_ab_test.py`<br>`supplier_documents.py`<br>`supplier_finance.py`<br>`supplier_health.py`<br>`supplier_orders.py`<br>`supplier_payouts.py`<br>`supplier_products.py`<br>`supplier_profile.py`<br>`treasury.py` | ✅ `web_app/supplier-storefront/[slug]/page.tsx`<br>`web_app/supplier/(auth)/login/page.tsx`<br>`web_app/supplier/(auth)/register/page.tsx`<br>`web_app/supplier/analytics/page.tsx`<br>`web_app/supplier/batch-upload/page.tsx`<br>`web_app/supplier/bulk/page.tsx`<br>`web_app/supplier/credibility/page.tsx`<br>`web_app/supplier/dashboard/page.tsx`<br>`web_app/supplier/disputes/page.tsx`<br>`web_app/supplier/documents/page.tsx`<br>`web_app/supplier/guide/page.tsx`<br>`web_app/supplier/inventory/page.tsx`<br>`web_app/supplier/invoices/page.tsx`<br>`web_app/supplier/labels/[id]/page.tsx`<br>`web_app/supplier/labels/page.tsx`<br>`web_app/supplier/logistics/page.tsx`<br>`web_app/supplier/notification-preferences/page.tsx`<br>`web_app/supplier/orders/[id]/page.tsx`<br>`web_app/supplier/orders/page.tsx`<br>`web_app/supplier/page.tsx`<br>`web_app/supplier/payouts/page.tsx`<br>`web_app/supplier/products/[id]/page.tsx`<br>`web_app/supplier/products/add/page.tsx`<br>`web_app/supplier/products/page.tsx`<br>`web_app/supplier/profile/page.tsx`<br>`web_app/supplier/regions/page.tsx`<br>`web_app/supplier/reports/page.tsx`<br>`web_app/supplier/returns/page.tsx`<br>`web_app/supplier/support/page.tsx`<br>`web_app/supplier/terms/page.tsx`<br>`web_app/supplier/upload/bg-compare/page.tsx`<br>`web_app/supplier/upload/page.tsx`<br>`web_app/supplier/videos/upload/page.tsx`<br>`web_app/suppliers/[id]/page.tsx` | ✅ `supplier-storefront/[slug].tsx`<br>`supplier/_layout.tsx`<br>`supplier/analytics.tsx`<br>`supplier/bulk.tsx`<br>`supplier/credibility.tsx`<br>`supplier/dashboard.tsx`<br>`supplier/disputes.tsx`<br>`supplier/documents.tsx`<br>`supplier/guide.tsx`<br>`supplier/invoices.tsx`<br>`supplier/label.tsx`<br>`supplier/labels/[id].tsx`<br>`supplier/login.tsx`<br>`supplier/logistics.tsx`<br>`supplier/notification-preferences.tsx`<br>`supplier/orders.tsx`<br>`supplier/payouts.tsx`<br>`supplier/products/[id].tsx`<br>`supplier/products/index.tsx`<br>`supplier/products/new.tsx`<br>`supplier/profile.tsx`<br>`supplier/regions.tsx`<br>`supplier/register.tsx`<br>`supplier/reports.tsx`<br>`supplier/returns.tsx`<br>`supplier/support.tsx`<br>`supplier/terms.tsx`<br>`supplier/upload.tsx`<br>`suppliers/[id].tsx` | ✅ `lib/utils.ts` | 🔍 1 found | 🔍 8 tables | ✅ `test_api_endpoints.py`<br>`test_orders_audit.py`<br>`test_orders_controller_audit.py`<br>`test_search_endpoints.py`<br>`test_shipping_quote.py`<br>`test_suppliers.py` | ✅ `pages/supplierBulkAi.test.tsx` | ❌ — | **62.0%** |

---

## 🚚 Section IV — Logistor (Logistics Partner) Panel Features & Systems Status

| Feature | TODO Ref | Backend: Controllers | Backend: Services | Backend: Router | Web App Pages | Mobile Screens | Shared / Utils | API Routes | DB Model(s) | Backend Tests | Web Tests | Mobile Tests | Completion % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 🟡 **Cash Management / Finance / Treasury System** | — | ✅ `logistics_controller.py`<br>`logistics_partner_controller.py` | ✅ `auto_payout_scheduler.py`<br>`command_center_service.py`<br>`country_auto_populate.py`<br>`country_data_orchestrator.py`<br>`country_heuristic_engine.py`<br>`fraud_detection_service.py`<br>`geography/country_auto_populate.py`<br>`geography/country_data_orchestrator.py`<br>`geography/country_heuristic_engine.py`<br>`logistics/logistics_analytics_service.py`<br>`logistics/partner_blocker_service.py`<br>`logistics_engine.py`<br>`logistics_health_engine.py`<br>`logistics_partner_pricing.py`<br>`logistics_partner_write_service.py`<br>`logistics_sla_service.py`<br>`logistics_write_service.py` | ✅ `fraud_detection.py`<br>`logistics.py`<br>`logistics_health.py`<br>`logistics_locations.py`<br>`logistics_orders.py`<br>`logistics_orders_v2.py`<br>`logistics_partner.py` | ✅ `web_app/logistics-partner/(auth)/login/page.tsx`<br>`web_app/logistics-partner/(auth)/register/page.tsx`<br>`web_app/logistics-partner/analytics/page.tsx`<br>`web_app/logistics-partner/dashboard/page.tsx`<br>`web_app/logistics-partner/payouts/page.tsx`<br>`web_app/logistics-partner/profile/page.tsx`<br>`web_app/logistics-partner/routes/page.tsx`<br>`web_app/logistics-partner/scan/page.tsx`<br>`web_app/logistics-partner/shipments/page.tsx`<br>`web_app/logistics-partners/[id]/page.tsx`<br>`web_app/logistics-partners/page.tsx` | ✅ `logistics-partner/_layout.tsx`<br>`logistics-partner/analytics.tsx`<br>`logistics-partner/dashboard.tsx`<br>`logistics-partner/login.tsx`<br>`logistics-partner/payouts.tsx`<br>`logistics-partner/profile.tsx`<br>`logistics-partner/register.tsx`<br>`logistics-partner/scan.tsx`<br>`logistics-partner/shipments.tsx`<br>`logistics-partners/[id].tsx`<br>`logistics-partners/index.tsx` | ✅ `logistics-partner/payouts/FinanceSection.tsx` | ❌ — | ❌ — | ✅ `test_country_auto_populate.py`<br>`test_logistics_audit.py` | ✅ `pages/logisticsPartnerPages.test.tsx`<br>`pages/logisticsPartnerPayoutsReceipt.test.tsx` | ✅ `logisticsPartnerApi.test.ts`<br>`logisticsPartnerProfileScreen.test.tsx`<br>`logisticsPartnerScanScreen.test.tsx`<br>`logisticsPayoutInsights.test.ts`<br>`logisticsScreen.test.ts`<br>`logisticsShipmentsScreen.test.tsx` | **65.8%** |
| 🟡 **Order Tracker & Order Management** | — | ✅ `logistics_controller.py`<br>`logistics_partner_controller.py` | ✅ `auto_payout_scheduler.py`<br>`command_center_service.py`<br>`country_auto_populate.py`<br>`country_data_orchestrator.py`<br>`country_heuristic_engine.py`<br>`fraud_detection_service.py`<br>`geography/country_auto_populate.py`<br>`geography/country_data_orchestrator.py`<br>`geography/country_heuristic_engine.py`<br>`logistics/logistics_analytics_service.py`<br>`logistics/partner_blocker_service.py`<br>`logistics_engine.py`<br>`logistics_health_engine.py`<br>`logistics_partner_pricing.py`<br>`logistics_partner_write_service.py`<br>`logistics_sla_service.py`<br>`logistics_write_service.py` | ✅ `fraud_detection.py`<br>`logistics.py`<br>`logistics_health.py`<br>`logistics_locations.py`<br>`logistics_orders.py`<br>`logistics_orders_v2.py`<br>`logistics_partner.py` | ✅ `web_app/logistics-partner/(auth)/login/page.tsx`<br>`web_app/logistics-partner/(auth)/register/page.tsx`<br>`web_app/logistics-partner/analytics/page.tsx`<br>`web_app/logistics-partner/dashboard/page.tsx`<br>`web_app/logistics-partner/payouts/page.tsx`<br>`web_app/logistics-partner/profile/page.tsx`<br>`web_app/logistics-partner/routes/page.tsx`<br>`web_app/logistics-partner/scan/page.tsx`<br>`web_app/logistics-partner/shipments/page.tsx`<br>`web_app/logistics-partners/[id]/page.tsx`<br>`web_app/logistics-partners/page.tsx` | ✅ `logistics-partner/_layout.tsx`<br>`logistics-partner/analytics.tsx`<br>`logistics-partner/dashboard.tsx`<br>`logistics-partner/login.tsx`<br>`logistics-partner/payouts.tsx`<br>`logistics-partner/profile.tsx`<br>`logistics-partner/register.tsx`<br>`logistics-partner/scan.tsx`<br>`logistics-partner/shipments.tsx`<br>`logistics-partners/[id].tsx`<br>`logistics-partners/index.tsx` | ✅ `logistics-partner/payouts/FinanceSection.tsx` | 🔍 1 found | 🔍 8 tables | ✅ `test_country_auto_populate.py`<br>`test_logistics_audit.py` | ✅ `pages/logisticsPartnerAuth.test.tsx`<br>`pages/logisticsPartnerPages.test.tsx`<br>`pages/logisticsPartnerPayoutsReceipt.test.tsx` | ✅ `logisticsPartnerApi.test.ts`<br>`logisticsPartnerProfileScreen.test.tsx`<br>`logisticsPartnerScanScreen.test.tsx`<br>`logisticsPayoutInsights.test.ts`<br>`logisticsScreen.test.ts`<br>`logisticsShipmentsScreen.test.tsx` | **62.0%** |

---

## 👨‍💼 Section V — Admin Panel Features & Systems Status

| Feature | TODO Ref | Backend: Controllers | Backend: Services | Backend: Router | Web App Pages | Mobile Screens | Shared / Utils | API Routes | DB Model(s) | Backend Tests | Web Tests | Mobile Tests | Completion % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 🟡 **Unified Communication Workspace (Chat · Email · Video · Contacts · Files)** | — | ✅ `admin/admin_auth.py`<br>`admin/analytics.py`<br>`admin/bulk_ops.py`<br>`admin/coupons.py`<br>`admin/misc.py`<br>`admin/orders.py`<br>`admin/payouts.py`<br>`admin/permissions.py`<br>`admin/products.py`<br>`admin/suppliers.py`<br>`admin/tickets.py`<br>`admin/users.py`<br>`auth_controller.py`<br>`cash_management_controller.py`<br>`commission_controller.py`<br>`comms/admin_tickets_controller.py`<br>`country_controller.py`<br>`disputes_controller.py`<br>`export_controller.py`<br>`geography/country_controller.py` | ✅ `admin_analytics_service.py`<br>`comms/tickets_write_service.py`<br>`geography/country_write_service.py`<br>`order_tracking_service.py` | ✅ `admin_categories.py`<br>`admin_chat.py`<br>`admin_email.py`<br>`admin_fallback.py`<br>`admin_logistics.py`<br>`admin_orders.py`<br>`admin_payouts.py`<br>`admin_products.py`<br>`admin_promotions.py`<br>`admin_suppliers.py`<br>`admin_treasury.py`<br>`admin_users.py`<br>`admin_video.py`<br>`cash_management.py`<br>`categories.py`<br>`country_admin.py`<br>`country_payouts.py`<br>`coupons.py`<br>`employees.py`<br>`proxy_communication.py`<br>`ws_chat.py` | ✅ `web_app/admin/accounting/page.tsx`<br>`web_app/admin/audit-logs/page.tsx`<br>`web_app/admin/barcode/page.tsx`<br>`web_app/admin/categories/page.tsx`<br>`web_app/admin/chat/page.tsx`<br>`web_app/admin/command-center/alerts/page.tsx`<br>`web_app/admin/command-center/headlines/create/page.tsx`<br>`web_app/admin/command-center/headlines/page.tsx`<br>`web_app/admin/command-center/page.tsx`<br>`web_app/admin/commission/page.tsx`<br>`web_app/admin/communication/page.tsx`<br>`web_app/admin/countries/[code]/staff/page.tsx`<br>`web_app/admin/countries/page.tsx`<br>`web_app/admin/dashboard/page.tsx`<br>`web_app/admin/email/page.tsx`<br>`web_app/admin/ess/page.tsx`<br>`web_app/admin/finance/page.tsx`<br>`web_app/admin/hr/page.tsx`<br>`web_app/admin/inventory-alerts/page.tsx`<br>`web_app/admin/invoices/page.tsx`<br>`web_app/admin/login/page.tsx`<br>`web_app/admin/logistics/page.tsx`<br>`web_app/admin/orders/page.tsx`<br>`web_app/admin/payments/page.tsx`<br>`web_app/admin/payouts/background-jobs/page.tsx`<br>`web_app/admin/payouts/page.tsx`<br>`web_app/admin/products/page.tsx`<br>`web_app/admin/resolution/page.tsx`<br>`web_app/admin/supplier-documents/page.tsx`<br>`web_app/admin/suppliers/page.tsx`<br>`web_app/admin/tickets/[id]/page.tsx`<br>`web_app/admin/users/page.tsx`<br>`web_app/admin/video/page.tsx` | ✅ `admin/analytics.tsx`<br>`admin/bank-accounts.tsx`<br>`admin/banners.tsx`<br>`admin/barcode.tsx`<br>`admin/coupons.tsx`<br>`admin/dashboard.tsx`<br>`admin/email.tsx`<br>`admin/exports.tsx`<br>`admin/flash-sales.tsx`<br>`admin/invoices.tsx`<br>`admin/login.tsx`<br>`admin/logistics-partners.tsx`<br>`admin/orders.tsx`<br>`admin/product-verification.tsx`<br>`admin/products.tsx`<br>`admin/promotions.tsx`<br>`admin/returns.tsx`<br>`admin/suppliers.tsx`<br>`admin/users.tsx` | ✅ `utils/dependencies.py`<br>`utils/realtime.py`<br>`utils/rls_context.py`<br>`admin/countries/CountryLedgerTable.tsx`<br>`admin/dashboard/_components/ExportsPanel.tsx`<br>`admin/dashboard/_tabs/AnalyticsTab.tsx`<br>`admin/dashboard/_tabs/ApprovalMatrixTab.tsx`<br>`admin/dashboard/_tabs/BannerTab.tsx`<br>`admin/dashboard/_tabs/CouponsTab.tsx`<br>`admin/dashboard/_tabs/FinanceTab.tsx`<br>`admin/dashboard/_tabs/HierarchyTab.tsx`<br>`admin/dashboard/_tabs/InsightsTab.tsx`<br>`admin/dashboard/_tabs/ModerationTab.tsx`<br>`admin/dashboard/_tabs/PayoutsTab.tsx`<br>`admin/dashboard/_tabs/ProductsTab.tsx`<br>`admin/dashboard/_tabs/SupplierDocumentsTab.tsx`<br>`admin/dashboard/_tabs/TicketsTab.tsx`<br>`admin/disputes/_components/DisputesPanel.tsx`<br>`admin/employees/_components/employees-content.tsx`<br>`admin/employees/_tabs/AddressMatrixTab.tsx`<br>`admin/employees/_tabs/AlumniContractorTab.tsx`<br>`admin/employees/_tabs/CommunicationsTab.tsx`<br>`admin/employees/_tabs/DEITab.tsx`<br>`admin/employees/_tabs/DisciplinaryOffboardingTab.tsx`<br>`admin/employees/_tabs/HseTab.tsx`<br>`admin/employees/_tabs/InsuranceBenefitsTab.tsx`<br>`admin/employees/_tabs/PerformanceTab.tsx`<br>`admin/finance/_components/BankAccountsPanel.tsx`<br>`admin/finance/_components/CashFlowCycleTab.tsx`<br>`admin/finance/_components/ErpPanels.tsx`<br>`admin/logistics/_components/LogisticsPartnersPanel.tsx`<br>`admin/orders/_components/ReturnsPanel.tsx`<br>`admin/permissions/_components/permissions-content.tsx`<br>`admin/promotions/_components/BannersPanel.tsx`<br>`admin/promotions/_components/CouponsPanel.tsx`<br>`admin/promotions/_components/FlashSalesPanel.tsx`<br>`admin/promotions/_components/PromotionBuilderPanel.tsx`<br>`admin/staff/_components/staff-content.tsx`<br>`admin/treasury/_components/treasury-content.tsx`<br>`lib/adminPanelConfig.ts`<br>`lib/useAdminApi.ts`<br>`lib/useAuth.tsx`<br>`lib/userRealtime.ts` | ❌ — | ❌ — | ✅ `conftest.py`<br>`test_admin.py`<br>`test_api_pagination.py`<br>`test_auth.py`<br>`test_banners.py`<br>`test_categories.py`<br>`test_comprehensive_system.py`<br>`test_controller_subpackages.py`<br>`test_countries.py`<br>`test_coupons.py`<br>`test_internal_communication.py`<br>`test_logistics.py`<br>`test_notifications.py`<br>`test_payments.py`<br>`test_products.py`<br>`test_security_module.py`<br>`test_treasury.py`<br>`test_users.py` | ❌ — | ✅ `adminGuardedScreens.test.tsx` | **58.1%** |
| ❌ **Product & Catalog System** | — | ✅ `admin/admin_auth.py`<br>`admin/analytics.py`<br>`admin/bulk_ops.py`<br>`admin/coupons.py`<br>`admin/misc.py`<br>`admin/orders.py`<br>`admin/payouts.py`<br>`admin/permissions.py`<br>`admin/products.py`<br>`admin/suppliers.py`<br>`admin/tickets.py`<br>`admin/users.py`<br>`auth_controller.py`<br>`cash_management_controller.py`<br>`commission_controller.py`<br>`comms/admin_tickets_controller.py`<br>`country_controller.py`<br>`disputes_controller.py`<br>`export_controller.py`<br>`geography/country_controller.py` | ✅ `admin_analytics_service.py`<br>`comms/tickets_write_service.py`<br>`geography/country_write_service.py`<br>`order_tracking_service.py` | ✅ `admin_banners.py`<br>`admin_categories.py`<br>`admin_chat.py`<br>`admin_commission.py`<br>`admin_fallback.py`<br>`admin_payouts.py`<br>`admin_products.py`<br>`admin_promotions.py`<br>`admin_suppliers.py`<br>`admin_treasury.py`<br>`admin_users.py`<br>`admin_video.py`<br>`banners.py`<br>`cash_management.py`<br>`categories.py`<br>`country_admin.py`<br>`country_payouts.py`<br>`coupons.py`<br>`cross_border.py`<br>`finance_automation.py`<br>`payments.py`<br>`proxy_communication.py`<br>`users.py`<br>`ws_chat.py` | ✅ `web_app/admin/accounting/page.tsx`<br>`web_app/admin/audit-logs/page.tsx`<br>`web_app/admin/barcode/page.tsx`<br>`web_app/admin/categories/page.tsx`<br>`web_app/admin/command-center/alerts/page.tsx`<br>`web_app/admin/command-center/headlines/create/page.tsx`<br>`web_app/admin/command-center/headlines/page.tsx`<br>`web_app/admin/command-center/page.tsx`<br>`web_app/admin/commission/page.tsx`<br>`web_app/admin/countries/[code]/staff/page.tsx`<br>`web_app/admin/countries/page.tsx`<br>`web_app/admin/dashboard/page.tsx`<br>`web_app/admin/ess/page.tsx`<br>`web_app/admin/finance/page.tsx`<br>`web_app/admin/flash-sales/page.tsx`<br>`web_app/admin/hr/page.tsx`<br>`web_app/admin/inventory-alerts/page.tsx`<br>`web_app/admin/invoices/page.tsx`<br>`web_app/admin/login/page.tsx`<br>`web_app/admin/logistics/page.tsx`<br>`web_app/admin/orders/page.tsx`<br>`web_app/admin/organization/page.tsx`<br>`web_app/admin/page.tsx`<br>`web_app/admin/payments/page.tsx`<br>`web_app/admin/payouts/background-jobs/page.tsx`<br>`web_app/admin/payouts/page.tsx`<br>`web_app/admin/product-verification/page.tsx`<br>`web_app/admin/products/page.tsx`<br>`web_app/admin/promotions/page.tsx`<br>`web_app/admin/resolution/page.tsx`<br>`web_app/admin/supplier-documents/page.tsx`<br>`web_app/admin/suppliers/page.tsx`<br>`web_app/admin/tickets/[id]/page.tsx`<br>`web_app/admin/users/page.tsx` | ✅ `admin/analytics.tsx`<br>`admin/audit-logs.tsx`<br>`admin/bank-accounts.tsx`<br>`admin/banners.tsx`<br>`admin/barcode.tsx`<br>`admin/coupons.tsx`<br>`admin/dashboard.tsx`<br>`admin/email.tsx`<br>`admin/exports.tsx`<br>`admin/flash-sales.tsx`<br>`admin/invoices.tsx`<br>`admin/login.tsx`<br>`admin/logistics-partners.tsx`<br>`admin/orders.tsx`<br>`admin/product-verification.tsx`<br>`admin/products.tsx`<br>`admin/promotions.tsx`<br>`admin/returns.tsx`<br>`admin/suppliers.tsx`<br>`admin/users.tsx` | ✅ `utils/dependencies.py`<br>`utils/realtime.py`<br>`utils/rls_context.py`<br>`admin/countries/CountryLedgerTable.tsx`<br>`admin/dashboard/_components/ExportsPanel.tsx`<br>`admin/dashboard/_tabs/AnalyticsTab.tsx`<br>`admin/dashboard/_tabs/ApprovalMatrixTab.tsx`<br>`admin/dashboard/_tabs/BannerTab.tsx`<br>`admin/dashboard/_tabs/CouponsTab.tsx`<br>`admin/dashboard/_tabs/FinanceTab.tsx`<br>`admin/dashboard/_tabs/HierarchyTab.tsx`<br>`admin/dashboard/_tabs/InsightsTab.tsx`<br>`admin/dashboard/_tabs/ModerationTab.tsx`<br>`admin/dashboard/_tabs/OrdersTab.tsx`<br>`admin/dashboard/_tabs/PayoutsTab.tsx`<br>`admin/dashboard/_tabs/ProductsTab.tsx`<br>`admin/dashboard/_tabs/SupplierDocumentsTab.tsx`<br>`admin/dashboard/_tabs/TicketsTab.tsx`<br>`admin/disputes/_components/DisputesPanel.tsx`<br>`admin/employees/_components/employees-content.tsx`<br>`admin/employees/_tabs/AddressMatrixTab.tsx`<br>`admin/employees/_tabs/CommunicationsTab.tsx`<br>`admin/employees/_tabs/DEITab.tsx`<br>`admin/employees/_tabs/PerformanceTab.tsx`<br>`admin/finance/_components/BankAccountsPanel.tsx`<br>`admin/finance/_components/CashFlowCycleTab.tsx`<br>`admin/finance/_components/ErpPanels.tsx`<br>`admin/logistics/_components/LogisticsPartnersPanel.tsx`<br>`admin/orders/_components/ReturnsPanel.tsx`<br>`admin/permissions/_components/permissions-content.tsx`<br>`admin/promotions/_components/BannersPanel.tsx`<br>`admin/promotions/_components/CouponsPanel.tsx`<br>`admin/promotions/_components/FlashSalesPanel.tsx`<br>`admin/promotions/_components/PromotionBuilderPanel.tsx`<br>`admin/staff/_components/staff-content.tsx`<br>`admin/treasury/_components/treasury-content.tsx`<br>`lib/adminPanelConfig.ts`<br>`lib/useAdminApi.ts`<br>`lib/useAuth.tsx` | ❌ — | 🔍 1 tables | ✅ `conftest.py`<br>`test_admin.py`<br>`test_api_pagination.py`<br>`test_auth.py`<br>`test_banners.py`<br>`test_categories.py`<br>`test_comprehensive_system.py`<br>`test_controller_subpackages.py`<br>`test_countries.py`<br>`test_coupons.py`<br>`test_internal_communication.py`<br>`test_logistics.py`<br>`test_notifications.py`<br>`test_payments.py`<br>`test_products.py`<br>`test_security_module.py`<br>`test_treasury.py`<br>`test_users.py` | ❌ — | ✅ `adminGuardedScreens.test.tsx` | **15.7%** |
| 🟡 **Cash Management / Finance / Treasury System** | — | ✅ `admin/admin_auth.py`<br>`admin/analytics.py`<br>`admin/bulk_ops.py`<br>`admin/coupons.py`<br>`admin/misc.py`<br>`admin/orders.py`<br>`admin/payouts.py`<br>`admin/permissions.py`<br>`admin/products.py`<br>`admin/suppliers.py`<br>`admin/tickets.py`<br>`admin/users.py`<br>`auth_controller.py`<br>`cash_management_controller.py`<br>`commission_controller.py`<br>`comms/admin_tickets_controller.py`<br>`country_controller.py`<br>`disputes_controller.py`<br>`export_controller.py`<br>`geography/country_controller.py` | ✅ `admin_analytics_service.py`<br>`comms/tickets_write_service.py`<br>`geography/country_write_service.py`<br>`order_tracking_service.py` | ✅ `admin_cash.py`<br>`admin_categories.py`<br>`admin_chat.py`<br>`admin_commission.py`<br>`admin_email.py`<br>`admin_fallback.py`<br>`admin_logistics.py`<br>`admin_orders.py`<br>`admin_payouts.py`<br>`admin_products.py`<br>`admin_suppliers.py`<br>`admin_treasury.py`<br>`admin_video.py`<br>`banners.py`<br>`cash_management.py`<br>`categories.py`<br>`country_admin.py`<br>`country_payouts.py`<br>`coupons.py`<br>`cross_border.py`<br>`employees.py`<br>`finance_automation.py`<br>`payments.py`<br>`proxy_communication.py`<br>`users.py`<br>`ws_chat.py` | ✅ `web_app/admin/accounting/page.tsx`<br>`web_app/admin/audit-logs/page.tsx`<br>`web_app/admin/bank-accounts/page.tsx`<br>`web_app/admin/barcode/page.tsx`<br>`web_app/admin/command-center/headlines/create/page.tsx`<br>`web_app/admin/command-center/page.tsx`<br>`web_app/admin/commission/page.tsx`<br>`web_app/admin/communication/page.tsx`<br>`web_app/admin/countries/[code]/staff/page.tsx`<br>`web_app/admin/countries/page.tsx`<br>`web_app/admin/dashboard/page.tsx`<br>`web_app/admin/email/page.tsx`<br>`web_app/admin/employees/page.tsx`<br>`web_app/admin/ess/page.tsx`<br>`web_app/admin/finance/page.tsx`<br>`web_app/admin/hr/page.tsx`<br>`web_app/admin/inventory-alerts/page.tsx`<br>`web_app/admin/invoices/page.tsx`<br>`web_app/admin/logistics-partners/page.tsx`<br>`web_app/admin/logistics/page.tsx`<br>`web_app/admin/orders/page.tsx`<br>`web_app/admin/organization/page.tsx`<br>`web_app/admin/payments/page.tsx`<br>`web_app/admin/payouts/background-jobs/page.tsx`<br>`web_app/admin/payouts/page.tsx`<br>`web_app/admin/products/page.tsx`<br>`web_app/admin/promotions/page.tsx`<br>`web_app/admin/supplier-documents/page.tsx`<br>`web_app/admin/suppliers/page.tsx`<br>`web_app/admin/tickets/[id]/page.tsx`<br>`web_app/admin/treasury/page.tsx`<br>`web_app/admin/users/page.tsx` | ✅ `admin/analytics.tsx`<br>`admin/audit-logs.tsx`<br>`admin/bank-accounts.tsx`<br>`admin/banners.tsx`<br>`admin/barcode.tsx`<br>`admin/dashboard.tsx`<br>`admin/email.tsx`<br>`admin/exports.tsx`<br>`admin/invoices.tsx`<br>`admin/login.tsx`<br>`admin/logistics-partners.tsx`<br>`admin/orders.tsx`<br>`admin/product-verification.tsx`<br>`admin/products.tsx`<br>`admin/promotions.tsx`<br>`admin/returns.tsx`<br>`admin/suppliers.tsx`<br>`admin/users.tsx` | ✅ `utils/dependencies.py`<br>`utils/realtime.py`<br>`utils/rls_context.py`<br>`admin/countries/CountryLedgerTable.tsx`<br>`admin/dashboard/_components/ExportsPanel.tsx`<br>`admin/dashboard/_tabs/AnalyticsTab.tsx`<br>`admin/dashboard/_tabs/ApprovalMatrixTab.tsx`<br>`admin/dashboard/_tabs/BannerTab.tsx`<br>`admin/dashboard/_tabs/CouponsTab.tsx`<br>`admin/dashboard/_tabs/FinanceTab.tsx`<br>`admin/dashboard/_tabs/HierarchyTab.tsx`<br>`admin/dashboard/_tabs/InsightsTab.tsx`<br>`admin/dashboard/_tabs/ModerationTab.tsx`<br>`admin/dashboard/_tabs/OrdersTab.tsx`<br>`admin/dashboard/_tabs/PayoutsTab.tsx`<br>`admin/dashboard/_tabs/ProductsTab.tsx`<br>`admin/dashboard/_tabs/SupplierDocumentsTab.tsx`<br>`admin/dashboard/_tabs/TicketsTab.tsx`<br>`admin/disputes/_components/DisputesPanel.tsx`<br>`admin/employees/_components/employees-content.tsx`<br>`admin/employees/_tabs/AlumniContractorTab.tsx`<br>`admin/employees/_tabs/CommunicationsTab.tsx`<br>`admin/employees/_tabs/DEITab.tsx`<br>`admin/employees/_tabs/PerformanceTab.tsx`<br>`admin/finance/_components/AccountingPanels.tsx`<br>`admin/finance/_components/BankAccountsPanel.tsx`<br>`admin/finance/_components/CashFlowCycleTab.tsx`<br>`admin/finance/_components/ErpPanels.tsx`<br>`admin/logistics/_components/LogisticsPartnersPanel.tsx`<br>`admin/orders/_components/BarcodePanel.tsx`<br>`admin/orders/_components/ReturnsPanel.tsx`<br>`admin/permissions/_components/permissions-content.tsx`<br>`admin/promotions/_components/BannersPanel.tsx`<br>`admin/promotions/_components/CouponsPanel.tsx`<br>`admin/promotions/_components/FlashSalesPanel.tsx`<br>`admin/promotions/_components/PromotionBuilderPanel.tsx`<br>`admin/staff/_components/staff-content.tsx`<br>`admin/treasury/_components/treasury-content.tsx`<br>`lib/adminPanelConfig.ts`<br>`lib/useAdminApi.ts`<br>`lib/useAuth.tsx`<br>`lib/userRealtime.ts` | ❌ — | ❌ — | ✅ `conftest.py`<br>`test_admin.py`<br>`test_api_pagination.py`<br>`test_auth.py`<br>`test_banners.py`<br>`test_categories.py`<br>`test_comprehensive_system.py`<br>`test_controller_subpackages.py`<br>`test_countries.py`<br>`test_coupons.py`<br>`test_internal_communication.py`<br>`test_logistics.py`<br>`test_notifications.py`<br>`test_payments.py`<br>`test_products.py`<br>`test_security_module.py`<br>`test_treasury.py`<br>`test_users.py` | ❌ — | ✅ `adminGuardedScreens.test.tsx` | **65.8%** |
| 🟡 **Order Tracker & Order Management** | — | ✅ `admin/admin_auth.py`<br>`admin/analytics.py`<br>`admin/bulk_ops.py`<br>`admin/coupons.py`<br>`admin/misc.py`<br>`admin/orders.py`<br>`admin/payouts.py`<br>`admin/permissions.py`<br>`admin/products.py`<br>`admin/suppliers.py`<br>`admin/tickets.py`<br>`admin/users.py`<br>`auth_controller.py`<br>`cash_management_controller.py`<br>`commission_controller.py`<br>`comms/admin_tickets_controller.py`<br>`country_controller.py`<br>`disputes_controller.py`<br>`export_controller.py`<br>`geography/country_controller.py` | ✅ `admin_analytics_service.py`<br>`comms/tickets_write_service.py`<br>`geography/country_write_service.py`<br>`order_tracking_service.py` | ✅ `admin_banners.py`<br>`admin_cash.py`<br>`admin_categories.py`<br>`admin_chat.py`<br>`admin_commission.py`<br>`admin_email.py`<br>`admin_fallback.py`<br>`admin_logistics.py`<br>`admin_orders.py`<br>`admin_payouts.py`<br>`admin_products.py`<br>`admin_promotions.py`<br>`admin_settings.py`<br>`admin_suppliers.py`<br>`admin_treasury.py`<br>`admin_users.py`<br>`admin_video.py`<br>`banners.py`<br>`cash_management.py`<br>`categories.py`<br>`country_admin.py`<br>`country_payouts.py`<br>`coupons.py`<br>`cross_border.py`<br>`employees.py`<br>`finance_automation.py`<br>`payments.py`<br>`proxy_communication.py`<br>`users.py`<br>`ws_chat.py` | ✅ `web_app/admin/accounting/page.tsx`<br>`web_app/admin/audit-logs/page.tsx`<br>`web_app/admin/bank-accounts/page.tsx`<br>`web_app/admin/banners/page.tsx`<br>`web_app/admin/barcode/page.tsx`<br>`web_app/admin/categories/page.tsx`<br>`web_app/admin/chat/page.tsx`<br>`web_app/admin/command-center/alerts/page.tsx`<br>`web_app/admin/command-center/fraud/page.tsx`<br>`web_app/admin/command-center/headlines/create/page.tsx`<br>`web_app/admin/command-center/headlines/page.tsx`<br>`web_app/admin/command-center/page.tsx`<br>`web_app/admin/commission/page.tsx`<br>`web_app/admin/communication/page.tsx`<br>`web_app/admin/countries/[code]/staff/page.tsx`<br>`web_app/admin/countries/page.tsx`<br>`web_app/admin/coupons/page.tsx`<br>`web_app/admin/dashboard/page.tsx`<br>`web_app/admin/disputes/page.tsx`<br>`web_app/admin/email/page.tsx`<br>`web_app/admin/employees/page.tsx`<br>`web_app/admin/ess/page.tsx`<br>`web_app/admin/exports/page.tsx`<br>`web_app/admin/finance/page.tsx`<br>`web_app/admin/flash-sales/page.tsx`<br>`web_app/admin/hr/page.tsx`<br>`web_app/admin/inventory-alerts/page.tsx`<br>`web_app/admin/invoices/page.tsx`<br>`web_app/admin/login/page.tsx`<br>`web_app/admin/logistics-partners/page.tsx`<br>`web_app/admin/logistics/page.tsx`<br>`web_app/admin/moderation/page.tsx`<br>`web_app/admin/orders/page.tsx`<br>`web_app/admin/organization/page.tsx`<br>`web_app/admin/page.tsx`<br>`web_app/admin/payments/page.tsx`<br>`web_app/admin/payouts/background-jobs/page.tsx`<br>`web_app/admin/payouts/page.tsx`<br>`web_app/admin/payroll/page.tsx`<br>`web_app/admin/permissions/page.tsx`<br>`web_app/admin/product-verification/page.tsx`<br>`web_app/admin/products/page.tsx`<br>`web_app/admin/promotions/page.tsx`<br>`web_app/admin/resolution/page.tsx`<br>`web_app/admin/returns/page.tsx`<br>`web_app/admin/staff/page.tsx`<br>`web_app/admin/supplier-documents/page.tsx`<br>`web_app/admin/suppliers/page.tsx`<br>`web_app/admin/tickets/[id]/page.tsx`<br>`web_app/admin/tickets/page.tsx`<br>… +3 more (full list in appendix) | ✅ `admin/analytics.tsx`<br>`admin/audit-logs.tsx`<br>`admin/bank-accounts.tsx`<br>`admin/banners.tsx`<br>`admin/barcode.tsx`<br>`admin/coupons.tsx`<br>`admin/dashboard.tsx`<br>`admin/email.tsx`<br>`admin/exports.tsx`<br>`admin/flash-sales.tsx`<br>`admin/invoices.tsx`<br>`admin/login.tsx`<br>`admin/logistics-partners.tsx`<br>`admin/orders.tsx`<br>`admin/product-verification.tsx`<br>`admin/products.tsx`<br>`admin/promotions.tsx`<br>`admin/returns.tsx`<br>`admin/suppliers.tsx`<br>`admin/users.tsx` | ✅ `utils/dependencies.py`<br>`utils/realtime.py`<br>`utils/rls_context.py`<br>`admin/countries/CountryLedgerTable.tsx`<br>`admin/dashboard/_components/ExportsPanel.tsx`<br>`admin/dashboard/_tabs/AnalyticsTab.tsx`<br>`admin/dashboard/_tabs/ApprovalMatrixTab.tsx`<br>`admin/dashboard/_tabs/BannerTab.tsx`<br>`admin/dashboard/_tabs/CouponsTab.tsx`<br>`admin/dashboard/_tabs/FinanceTab.tsx`<br>`admin/dashboard/_tabs/HierarchyTab.tsx`<br>`admin/dashboard/_tabs/InsightsTab.tsx`<br>`admin/dashboard/_tabs/ModerationTab.tsx`<br>`admin/dashboard/_tabs/OrdersTab.tsx`<br>`admin/dashboard/_tabs/PayoutsTab.tsx`<br>`admin/dashboard/_tabs/ProductsTab.tsx`<br>`admin/dashboard/_tabs/SupplierDocumentsTab.tsx`<br>`admin/dashboard/_tabs/TicketsTab.tsx`<br>`admin/disputes/_components/DisputesPanel.tsx`<br>`admin/employees/_components/employees-content.tsx`<br>`admin/employees/_tabs/AddressMatrixTab.tsx`<br>`admin/employees/_tabs/AlumniContractorTab.tsx`<br>`admin/employees/_tabs/CommunicationsTab.tsx`<br>`admin/employees/_tabs/DEITab.tsx`<br>`admin/employees/_tabs/DisciplinaryOffboardingTab.tsx`<br>`admin/employees/_tabs/HseTab.tsx`<br>`admin/employees/_tabs/InsuranceBenefitsTab.tsx`<br>`admin/employees/_tabs/PerformanceTab.tsx`<br>`admin/finance/_components/AccountingPanels.tsx`<br>`admin/finance/_components/BankAccountsPanel.tsx`<br>`admin/finance/_components/CashFlowCycleTab.tsx`<br>`admin/finance/_components/ErpPanels.tsx`<br>`admin/logistics/_components/LogisticsPartnersPanel.tsx`<br>`admin/orders/_components/BarcodePanel.tsx`<br>`admin/orders/_components/ReturnsPanel.tsx`<br>`admin/permissions/_components/permissions-content.tsx`<br>`admin/promotions/_components/BannersPanel.tsx`<br>`admin/promotions/_components/CouponsPanel.tsx`<br>`admin/promotions/_components/FlashSalesPanel.tsx`<br>`admin/promotions/_components/PromotionBuilderPanel.tsx`<br>`admin/staff/_components/staff-content.tsx`<br>`admin/treasury/_components/treasury-content.tsx`<br>`lib/adminPanelConfig.ts`<br>`lib/useAdminApi.ts`<br>`lib/useAdminCountry.tsx`<br>`lib/useAuth.tsx`<br>`lib/userRealtime.ts` | 🔍 1 found | 🔍 8 tables | ✅ `conftest.py`<br>`test_admin.py`<br>`test_api_pagination.py`<br>`test_auth.py`<br>`test_banners.py`<br>`test_categories.py`<br>`test_comprehensive_system.py`<br>`test_controller_subpackages.py`<br>`test_countries.py`<br>`test_coupons.py`<br>`test_internal_communication.py`<br>`test_logistics.py`<br>`test_notifications.py`<br>`test_payments.py`<br>`test_products.py`<br>`test_security_module.py`<br>`test_treasury.py`<br>`test_users.py` | ❌ — | ✅ `adminGuardedScreens.test.tsx` | **62.0%** |

---

### SYS_001 — Unified Communication Workspace (Chat · Email · Video · Contacts · Files)  (58.1%)

**Checkpoints:** 0 tables · 0 routes · 0 statuses · 10 fields · 0 capabilities · 0 steps · 18 search terms
**Matched files:** 1061 / 1841 (57.6%)

**Completion Breakdown:**

| Component | Score | Weight |
|---|---|---|
| 🗄️ DB tables | n/a | 20% |
| 🔌 API routes | n/a | 15% |
| 🚦 Status machine | n/a | 15% |
| 💪 Capabilities | n/a | 10% |
| 🖥️ Panel sections | 79.6% | 20% |
| 🧪 Tests | 75.0% | 10% |
| 🧱 Steps | n/a | 10% |
| Dead-file penalty (147 unwired) | -20.0% | — |
| **Overall** | **58.1%** | 100% |

**🖥️ Panel sections (79.6%):**

- **§I** — 75.0% (terms 100.0%, web ❌, mobile ✅) — Realtime infrastructure: WebSocket chat delivery, channel masking, unified inbox aggregation, seed data.
- **§III** — 83.3% (terms 66.7%, web ✅, mobile ✅) — Supplier support inbox page handling customer conversations.
- **§V** — 80.6% (terms 61.1%, web ✅, mobile ✅) — Admin communication hub, video monitoring panel, employee communications tab, moderation.

**🧪 Tests (75.0%):**

- ✅ Backend: 1 file(s) — `test_communication_services.py`
- ✅ Web: 4 file(s) — `pages/adminCommunicationHub.test.tsx`, `pages/adminLogisticsPages.test.tsx`, `pages/logisticsPartnerPages.test.tsx`
- ❌ Mobile: 0 file(s)
- ✅ E2E: 4 file(s) — `web_app/e2e/admin-communication-hub.spec.ts`, `web_app/e2e/admin-logistics-workspace.spec.ts`, `web_app/e2e/admin-modules-reconciliation.spec.ts`

**📁 Files by Layer (top entries):**

**Backend Routers (85):**
- `accounting.py` — generic×2; semantic=0.496
- `admin.py` — specific×4; generic×10; semantic=0.551
- `admin_categories.py` — generic×2; semantic=0.494
- `admin_chat.py` — specific×3; generic×5; semantic=0.660
- `admin_email.py` — specific×1; generic×3; semantic=0.564
- `admin_fallback.py` — generic×2; semantic=0.499
- `admin_logistics.py` — generic×2; semantic=0.501
- `admin_orders.py` — generic×2; semantic=0.462
- `admin_payouts.py` — generic×5; semantic=0.479
- `admin_products.py` — generic×2; semantic=0.517
- `admin_promotions.py` — specific×1; generic×3; semantic=0.500
- `admin_suppliers.py` — generic×3; semantic=0.479
- `admin_treasury.py` — generic×2; semantic=0.502
- `admin_users.py` — specific×1; generic×3; semantic=0.498
- `admin_video.py` — specific×4; generic×3; semantic=0.609
- `ai_upload.py` — generic×5; semantic=0.514
- `audit.py` — specific×1; semantic=0.504
- `auth.py` — specific×1; generic×5; semantic=0.474
- `automation.py` — specific×1; generic×3; semantic=0.462
- `batch_upload.py` — specific×1; generic×6; semantic=0.503
- … +65 more

**Backend Controllers (45):**
- `admin/admin_auth.py` — generic×2; semantic=0.469
- `admin/analytics.py` — specific×2; generic×5; semantic=0.466
- `admin/bulk_ops.py` — generic×3; semantic=0.521
- `admin/coupons.py` — generic×3; semantic=0.460
- `admin/misc.py` — generic×3; semantic=0.493
- `admin/orders.py` — specific×1; generic×4; semantic=0.466
- `admin/payouts.py` — generic×3; semantic=0.472
- `admin/permissions.py` — generic×2; semantic=0.481
- `admin/products.py` — generic×3; semantic=0.506
- `admin/suppliers.py` — specific×2; generic×7; semantic=0.505
- `admin/tickets.py` — generic×3; semantic=0.506
- `admin/users.py` — specific×3; generic×7; semantic=0.520
- `ai_controller.py` — generic×2; semantic=0.498
- `auth_controller.py` — specific×2; generic×7; semantic=0.494
- `banner_controller.py` — specific×1; generic×3; semantic=0.495
- `cart_controller.py` — generic×3; semantic=0.433
- `cash_management_controller.py` — specific×1; generic×5; semantic=0.520
- `chatbot_controller.py` — specific×1; generic×7; semantic=0.576
- `comm_controller.py` — specific×4; generic×4; semantic=0.665
- `commerce/reviews.py` — generic×2; semantic=0.480
- … +25 more

**Backend Services (152):**
- `_registry.py` — specific×4; generic×7; semantic=0.507
- `admin_analytics_service.py` — generic×2; semantic=0.450
- `advanced_filter_service.py` — specific×1; generic×2; semantic=0.458
- `advanced_search_engine.py` — specific×1; generic×2; semantic=0.465
- `ai_automation_service.py` — specific×2; generic×4; semantic=0.426
- `ai_copy_jobs.py` — generic×2; semantic=0.504
- `ai_service.py` — specific×2; generic×6; semantic=0.509
- `ai_variant_config.py` — specific×1; generic×7; semantic=0.485
- `audit/audit_trail_service.py` — specific×1; generic×1; semantic=0.475
- `auth_service.py` — specific×2; generic×5; semantic=0.552
- `auth_write_service.py` — specific×1; generic×2; semantic=0.510
- `auto_payout_scheduler.py` — generic×5; semantic=0.430
- `automation_scheduler.py` — specific×1; generic×5; semantic=0.415
- `background_check.py` — generic×2; semantic=0.472
- `bg_removal_presets.py` — generic×3; semantic=0.490
- `bg_removal_service.py` — specific×1; generic×4; semantic=0.533
- `cash_flow_forecast_service.py` — generic×2; semantic=0.447
- `cash_management_service.py` — specific×1; generic×7; semantic=0.519
- `chat_enrichment.py` — specific×3; generic×6; semantic=0.588
- `chat_system.py` — specific×7; generic×8; semantic=0.610
- … +132 more

**Backend Models (23):**
- `__init__.py` — specific×11; generic×9; semantic=0.499
- `admin.py` — specific×3; generic×8; semantic=0.482
- `ai_upload.py` — generic×4; semantic=0.507
- `commission.py` — generic×2; semantic=0.462
- `comms/communication.py` — specific×8; generic×5; semantic=0.577
- `comms/core.py` — specific×7; generic×7; semantic=0.540
- `comms/marketing.py` — specific×2; generic×2; semantic=0.516
- `comms/suppliers.py` — specific×3; generic×5; semantic=0.489
- `country_control.py` — generic×2; semantic=0.439
- `employee_models.py` — specific×1; generic×2; semantic=0.492
- `finance.py` — specific×1; generic×3; semantic=0.448
- `fraud.py` — specific×2; generic×4; semantic=0.459
- `geography/countries.py` — specific×1; generic×4; semantic=0.428
- `geography/country_economics.py` — generic×2; semantic=0.413
- `geography/country_enhancements.py` — specific×1; generic×3; semantic=0.406
- `incident.py` — specific×1; generic×1; semantic=0.487
- `logistics.py` — specific×2; generic×4; semantic=0.467
- `media_models.py` — specific×1; generic×5; semantic=0.519
- `onboarding.py` — generic×2; semantic=0.481
- `orders.py` — generic×4; semantic=0.440
- … +3 more

**Backend Schemas (Pydantic) (3):**
- `schemas.py` — specific×1; generic×9; semantic=0.502
- `schemas.py` — specific×1; generic×4; semantic=0.435
- `utils/schema_audit.py` — specific×1; generic×2; semantic=0.481

**Backend Middleware (10):**
- `middleware/__init__.py` — specific×1; generic×1; semantic=0.556
- `middleware/country_context.py` — generic×3; semantic=0.547
- `middleware/csrf_middleware.py` — specific×1; generic×1; semantic=0.536
- `middleware/impossible_travel_middleware.py` — generic×3; semantic=0.535
- `middleware/orchestrator.py` — specific×1; generic×1; semantic=0.523
- `middleware/rate_limit_middleware.py` — generic×2; semantic=0.518
- `middleware/security_headers.py` — generic×2; semantic=0.548
- `middleware/siem_engine.py` — generic×2; semantic=0.543
- `middleware/webhook_ip_whitelist.py` — specific×1; generic×2; semantic=0.495
- `middleware/webhook_verification.py` — specific×1; generic×2; semantic=0.502

**Backend Utils (28):**
- `utils/analytics_service.py` — specific×1; generic×3; semantic=0.450
- `utils/api_docs.py` — specific×3; generic×3; semantic=0.501
- `utils/audit.py` — generic×2; semantic=0.509
- `utils/auth.py` — generic×2; semantic=0.445
- `utils/background_jobs.py` — specific×1; generic×3; semantic=0.520
- `utils/backup.py` — specific×1; generic×2; semantic=0.494
- `utils/config.py` — specific×2; generic×4; semantic=0.483
- `utils/constants.py` — generic×2; semantic=0.524
- `utils/dependencies.py` — generic×3; semantic=0.469
- `utils/email_service.py` — specific×1; generic×5; semantic=0.604
- `utils/entity_messaging.py` — specific×1; generic×3; semantic=0.620
- `utils/error_handler.py` — generic×2; semantic=0.533
- `utils/file_validation.py` — specific×2; generic×3; semantic=0.497
- `utils/invoice_html.py` — specific×1; generic×4; semantic=0.504
- `utils/key_rotation.py` — specific×1; generic×3; semantic=0.437
- `utils/logging_config.py` — specific×1; generic×2; semantic=0.456
- `utils/ml_worker.py` — generic×2; semantic=0.497
- `utils/multi_secret_webhook.py` — generic×2; semantic=0.501
- `utils/order_tracking.py` — generic×3; semantic=0.468
- `utils/realtime.py` — specific×1; generic×8; semantic=0.508
- … +8 more

**Backend Providers (27):**
- `providers/__init__.py` — specific×2; generic×2; semantic=0.495
- `providers/ai/__init__.py` — specific×1; generic×1; semantic=0.478
- `providers/ai/text.py` — specific×1; generic×1; semantic=0.504
- `providers/analytics.py` — specific×1; generic×4; semantic=0.483
- `providers/async_workers.py` — specific×1; generic×3; semantic=0.537
- `providers/bg_remover.py` — specific×2; generic×4; semantic=0.471
- `providers/chatbot.py` — specific×1; generic×3; semantic=0.550
- `providers/config.py` — specific×1; generic×1; semantic=0.506
- `providers/finance_ai.py` — specific×1; generic×3; semantic=0.486
- `providers/hr/br_05.py` — specific×1; generic×3; semantic=0.438
- `providers/hr/br_06.py` — specific×1; generic×3; semantic=0.433
- `providers/hr/br_08.py` — specific×1; generic×5; semantic=0.465
- `providers/hr/br_11.py` — specific×1; generic×3; semantic=0.427
- `providers/hr/br_12.py` — specific×1; generic×3; semantic=0.489
- `providers/hr/br_13.py` — specific×1; generic×3; semantic=0.430
- `providers/image.py` — generic×2; semantic=0.460
- `providers/legacy/br_05.py` — specific×1; generic×3; semantic=0.441
- `providers/legacy/br_06.py` — specific×1; generic×3; semantic=0.433
- `providers/legacy/br_08.py` — specific×1; generic×5; semantic=0.465
- `providers/legacy/br_11.py` — specific×1; generic×3; semantic=0.431
- … +7 more

**Backend Core (5):**
- `admin/__init__.py` — generic×2; semantic=0.517
- `database.py` — specific×1; generic×4; semantic=0.494
- `main.py` — specific×6; generic×11; semantic=0.491
- `_exports.py` — specific×1; generic×4; semantic=0.458
- `comms/__init__.py` — specific×1; generic×2; semantic=0.491

**Backend Data/Seed (6):**
- `data/category_tax_profiles.py` — specific×1; generic×2; semantic=0.441
- `data/country_curated.py` — specific×1; generic×1; semantic=0.445
- `data/geography_read.py` — specific×1; semantic=0.501
- `data/models_communication.py` — specific×2; generic×1; semantic=0.588
- `seed.py` — specific×1; generic×5; semantic=0.493
- `treasury_seeder.py` — generic×2; semantic=0.443

**Web Pages (91):**
- `web_app/admin/accounting/page.tsx` — specific×1; generic×1; semantic=0.506
- `web_app/admin/audit-logs/page.tsx` — generic×2; semantic=0.482
- `web_app/admin/barcode/page.tsx` — specific×1; generic×5; semantic=0.497
- `web_app/admin/categories/page.tsx` — generic×3; semantic=0.475
- `web_app/admin/chat/page.tsx` — specific×2; generic×2; semantic=0.550
- `web_app/admin/command-center/alerts/page.tsx` — generic×3; semantic=0.494
- `web_app/admin/command-center/headlines/create/page.tsx` — generic×2; semantic=0.480
- `web_app/admin/command-center/headlines/page.tsx` — generic×2; semantic=0.494
- `web_app/admin/command-center/page.tsx` — generic×6; semantic=0.511
- `web_app/admin/commission/page.tsx` — generic×3; semantic=0.474
- `web_app/admin/communication/page.tsx` — specific×2; generic×1; semantic=0.543
- `web_app/admin/countries/[code]/staff/page.tsx` — specific×1; generic×4; semantic=0.486
- `web_app/admin/countries/page.tsx` — specific×3; generic×6; semantic=0.478
- `web_app/admin/dashboard/page.tsx` — specific×1; generic×2; semantic=0.483
- `web_app/admin/email/page.tsx` — specific×2; generic×2; semantic=0.525
- `web_app/admin/ess/page.tsx` — specific×1; generic×4; semantic=0.505
- `web_app/admin/finance/page.tsx` — generic×2; semantic=0.480
- `web_app/admin/hr/page.tsx` — specific×2; generic×8; semantic=0.517
- `web_app/admin/inventory-alerts/page.tsx` — generic×3; semantic=0.477
- `web_app/admin/invoices/page.tsx` — generic×3; semantic=0.488
- … +71 more

**Web Components (114):**
- `components/ui/ErrorAlert.web.tsx` — generic×2; semantic=0.448
- `components/ui/ErrorBoundary.tsx` — generic×2; semantic=0.444
- `admin/countries/components/CommunicationsTab.tsx` — specific×1; generic×1; semantic=0.545
- `admin/countries/components/CountriesTabProps.ts` — specific×1; generic×5; semantic=0.445
- `admin/countries/components/FeatureFlagsTab.tsx` — specific×1; generic×4; semantic=0.427
- `admin/countries/components/LocalizationTab.tsx` — generic×3; semantic=0.426
- `admin/countries/components/LogisticsModelTab.tsx` — generic×2; semantic=0.447
- `admin/countries/components/MapTab.tsx` — generic×3; semantic=0.426
- `admin/countries/components/PayoutSettingsTab.tsx` — generic×4; semantic=0.458
- `admin/countries/components/PromotionsTab.tsx` — generic×3; semantic=0.454
- `admin/countries/components/StaffTab.tsx` — specific×1; generic×4; semantic=0.485
- `admin/countries/components/VersionsTab.tsx` — generic×4; semantic=0.457
- `admin/error.tsx` — generic×3; semantic=0.495
- `api/z-rmbg/route.ts` — generic×2; semantic=0.445
- `barcode-scan/error.tsx` — generic×2; semantic=0.469
- `cart/error.tsx` — generic×2; semantic=0.475
- `checkout/error.tsx` — generic×2; semantic=0.470
- `help/error.tsx` — generic×2; semantic=0.482
- `invoice/error.tsx` — generic×2; semantic=0.495
- `layout.tsx` — specific×1; generic×5; semantic=0.452
- … +94 more

**Web Lib/Hooks (87):**
- `HomeClient.tsx` — specific×1; generic×3; semantic=0.474
- `admin/countries/CountryLedgerTable.tsx` — specific×1; generic×4; semantic=0.451
- `admin/dashboard/_components/ExportsPanel.tsx` — specific×3; generic×5; semantic=0.504
- `admin/dashboard/_tabs/AnalyticsTab.tsx` — specific×1; generic×3; semantic=0.461
- `admin/dashboard/_tabs/ApprovalMatrixTab.tsx` — generic×4; semantic=0.466
- `admin/dashboard/_tabs/BannerTab.tsx` — specific×2; generic×3; semantic=0.430
- `admin/dashboard/_tabs/CouponsTab.tsx` — generic×2; semantic=0.430
- `admin/dashboard/_tabs/FinanceTab.tsx` — generic×2; semantic=0.436
- `admin/dashboard/_tabs/HierarchyTab.tsx` — generic×3; semantic=0.495
- `admin/dashboard/_tabs/InsightsTab.tsx` — specific×1; generic×2; semantic=0.485
- `admin/dashboard/_tabs/ModerationTab.tsx` — specific×1; generic×5; semantic=0.450
- `admin/dashboard/_tabs/PayoutsTab.tsx` — generic×4; semantic=0.455
- `admin/dashboard/_tabs/ProductsTab.tsx` — specific×1; generic×4; semantic=0.455
- `admin/dashboard/_tabs/SupplierDocumentsTab.tsx` — generic×2; semantic=0.454
- `admin/dashboard/_tabs/TicketsTab.tsx` — generic×3; semantic=0.439
- `admin/disputes/_components/DisputesPanel.tsx` — generic×4; semantic=0.511
- `admin/employees/_components/employees-content.tsx` — specific×3; generic×5; semantic=0.559
- `admin/employees/_tabs/AddressMatrixTab.tsx` — generic×3; semantic=0.483
- `admin/employees/_tabs/AlumniContractorTab.tsx` — generic×2; semantic=0.480
- `admin/employees/_tabs/CommunicationsTab.tsx` — specific×7; generic×8; semantic=0.597
- … +67 more

**Web App Files (27):**
- `adminPermissions.ts` — specific×1; generic×3; semantic=0.512
- `api-core.ts` — generic×3; semantic=0.517
- `chatbot.ts` — specific×1; generic×3; semantic=0.613
- `checkoutHelpers.ts` — generic×2; semantic=0.407
- `errorLogging.ts` — generic×2; semantic=0.510
- `i18n.ts` — specific×2; generic×7; semantic=0.482
- `index.ts` — specific×1; generic×3; semantic=0.463
- `notificationHelpers.ts` — generic×2; semantic=0.508
- `notificationStore.ts` — generic×5; semantic=0.520
- `productQuery.ts` — specific×1; generic×2; semantic=0.414
- `realtime.ts` — generic×4; semantic=0.515
- `requestCache.ts` — specific×1; generic×2; semantic=0.468
- `ticketHelpers.ts` — generic×2; semantic=0.456
- `types.ts` — specific×2; generic×8; semantic=0.457
- `userRealtimeAlerts.ts` — generic×5; semantic=0.534
- `web_app/jest.setup.ts` — generic×2; semantic=0.421
- `web_app/middleware.ts` — generic×2; semantic=0.485
- `admin/countries/constants.ts` — specific×1; generic×4; semantic=0.468
- `admin/countries/types.ts` — specific×2; generic×3; semantic=0.472
- `admin/employees/_components/employee-types.ts` — specific×2; generic×1; semantic=0.494
- … +7 more

**Frontend Scripts (6):**
- `web_app/scripts/check_pages.py` — generic×2; semantic=0.465
- `web_app/scripts/extract_tabs.py` — specific×2; generic×2; semantic=0.413
- `web_app/scripts/extract_tabs_v2.py` — specific×2; generic×4; semantic=0.438
- `web_app/scripts/final_fixes.py` — specific×1; generic×5; semantic=0.422
- `web_app/scripts/fix_components.py` — specific×2; generic×6; semantic=0.448
- `web_app/scripts/update_page_imports.py` — specific×2; generic×5; semantic=0.426

**Mobile Screens (87):**
- `(auth)/forgot-password.tsx` — specific×1; generic×3; semantic=0.440
- `(auth)/login.tsx` — specific×1; generic×5; semantic=0.409
- `(auth)/register.tsx` — specific×1; generic×3; semantic=0.392
- `(auth)/reset-password.tsx` — generic×2; semantic=0.436
- `(auth)/verify-email.tsx` — specific×1; generic×3; semantic=0.441
- `(tabs)/_layout.tsx` — specific×2; generic×2; semantic=0.417
- `(tabs)/cart.tsx` — generic×2; semantic=0.425
- `(tabs)/orders/[id].tsx` — generic×3; semantic=0.424
- `(tabs)/products/[id].tsx` — specific×1; generic×5; semantic=0.459
- `(tabs)/products/index.tsx` — specific×1; generic×5; semantic=0.438
- `(tabs)/profile.tsx` — specific×3; generic×8; semantic=0.429
- `_layout.tsx` — specific×1; generic×4; semantic=0.458
- `admin/analytics.tsx` — specific×1; generic×2; semantic=0.465
- `admin/bank-accounts.tsx` — generic×4; semantic=0.460
- `admin/banners.tsx` — specific×1; generic×2; semantic=0.472
- `admin/barcode.tsx` — generic×2; semantic=0.498
- `admin/coupons.tsx` — specific×1; generic×3; semantic=0.454
- `admin/dashboard.tsx` — specific×1; generic×7; semantic=0.489
- `admin/email.tsx` — specific×1; generic×5; semantic=0.557
- `admin/exports.tsx` — specific×1; generic×5; semantic=0.477
- … +67 more

**Mobile Components (14):**
- `components/AddressesScreen.tsx` — generic×2; semantic=0.459
- `components/AuthRequiredModal.tsx` — specific×1; generic×3; semantic=0.509
- `components/MobileSeasonalBanner.tsx` — specific×1; generic×4; semantic=0.462
- `components/NewsletterSignup.tsx` — specific×1; generic×2; semantic=0.500
- `components/ProductCard.tsx` — generic×2; semantic=0.451
- `components/ToastContainer.tsx` — generic×2; semantic=0.414
- `components/UserRealtimeBridge.tsx` — generic×3; semantic=0.527
- `components/ui/AppHeader.tsx` — specific×1; generic×1; semantic=0.452
- `components/ui/ErrorAlert.tsx` — generic×2; semantic=0.402
- `components/ui/ErrorBanner.tsx` — generic×2; semantic=0.410
- `components/ui/ErrorBoundary.tsx` — generic×2; semantic=0.438
- `components/ui/Footer.tsx` — specific×1; generic×1; semantic=0.455
- `components/ui/StatusBadge.tsx` — generic×3; semantic=0.473
- `components/ui/ErrorAlert.native.tsx` — generic×2; semantic=0.362

**Mobile Lib/Hooks (20):**
- `lib/adminManagementUtils.ts` — specific×1; generic×2; semantic=0.503
- `lib/api.ts` — specific×1; generic×6; semantic=0.477
- `lib/authPrompt.tsx` — specific×1; generic×3; semantic=0.490
- `lib/authStore.ts` — specific×1; generic×4; semantic=0.449
- `lib/backgroundJobs.ts` — specific×1; generic×4; semantic=0.454
- `lib/chatbotStore.ts` — specific×1; generic×3; semantic=0.550
- `lib/documentPicker.ts` — specific×1; generic×1; semantic=0.442
- `lib/errorReporter.ts` — generic×2; semantic=0.430
- `lib/fileSystem.ts` — specific×1; generic×1; semantic=0.501
- `lib/globalErrorHandler.ts` — generic×2; semantic=0.431
- `lib/icons.ts` — specific×2; generic×2; semantic=0.425
- `lib/imagePicker.ts` — specific×1; generic×2; semantic=0.442
- `lib/invoiceService.ts` — specific×1; generic×3; semantic=0.439
- `lib/paymentService.ts` — generic×2; semantic=0.504
- `lib/socialAuth.ts` — specific×1; generic×3; semantic=0.499
- `lib/supplierProductAi.ts` — specific×1; generic×1; semantic=0.455
- `lib/supplierShipmentWorkspace.ts` — specific×1; generic×1; semantic=0.536
- `lib/toastStore.ts` — generic×2; semantic=0.450
- `lib/userRealtime.ts` — generic×3; semantic=0.501
- `theme/index.ts` — specific×1; generic×2; semantic=0.429

**Backend Tests (47):**
- `conftest.py` — specific×2; generic×6; semantic=0.520
- `playwright/e2e/auth.spec.ts` — specific×1; generic×4; semantic=0.443
- `playwright/e2e/finance-automation.spec.ts` — specific×1; generic×4; semantic=0.482
- `playwright/helpers/auth.ts` — specific×1; generic×1; semantic=0.486
- `test_admin.py` — specific×1; generic×2; semantic=0.462
- `test_api_endpoints.py` — specific×1; generic×4; semantic=0.437
- `test_api_pagination.py` — generic×2; semantic=0.515
- `test_auth.py` — specific×1; generic×3; semantic=0.439
- `test_auto_payout_sweep.py` — specific×1; generic×3; semantic=0.452
- `test_background_jobs.py` — specific×1; generic×3; semantic=0.445
- `test_banners.py` — specific×1; generic×2; semantic=0.479
- `test_cart.py` — specific×1; generic×3; semantic=0.470
- `test_categories.py` — specific×1; generic×2; semantic=0.477
- `test_chat.py` — specific×2; generic×5; semantic=0.587
- `test_circuit_breaker.py` — generic×2; semantic=0.380
- `test_communication_services.py` — specific×3; generic×4; semantic=0.613
- `test_comprehensive_system.py` — specific×2; generic×3; semantic=0.546
- `test_controller_subpackages.py` — specific×1; generic×4; semantic=0.457
- `test_countries.py` — specific×1; generic×2; semantic=0.477
- `test_country_auto_populate.py` — generic×5; semantic=0.444
- … +27 more

**Web Tests (53):**
- `__tests__/chatbot.test.ts` — specific×1; generic×2; semantic=0.518
- `__tests__/checkoutHelpers.test.ts` — generic×2; semantic=0.417
- `chatbot.test.ts` — specific×1; generic×2; semantic=0.509
- `checkoutHelpers.test.ts` — generic×2; semantic=0.424
- `web_app/__tests__/browser.spec.ts` — specific×1; generic×3; semantic=0.449
- `Chatbot.test.tsx` — specific×1; generic×5; semantic=0.489
- `components/ApprovalActionModal.test.tsx` — generic×2; semantic=0.477
- `components/CountryDetailWorkspace.test.tsx` — specific×1; generic×1; semantic=0.458
- `components/CountryResearchPanel.test.tsx` — generic×2; semantic=0.423
- `components/Header.test.tsx` — specific×1; generic×4; semantic=0.446
- `components/QuickViewModal.test.tsx` — specific×1; generic×3; semantic=0.428
- `components/emailComponents.test.tsx` — specific×1; generic×4; semantic=0.526
- `lib/adminPermissions.test.ts` — specific×1; generic×2; semantic=0.467
- `lib/api.test.ts` — generic×3; semantic=0.450
- `lib/currencyStore.test.ts` — generic×2; semantic=0.425
- `lib/requestCache.test.ts` — specific×1; generic×2; semantic=0.473
- `lib/useApprovalCheck.test.tsx` — generic×3; semantic=0.434
- `lib/useAuth.preferences.test.tsx` — specific×1; generic×2; semantic=0.407
- `lib/userRealtime.test.ts` — generic×4; semantic=0.493
- `pages/adminCommunicationHub.test.tsx` — specific×6; generic×4; semantic=0.508
- … +33 more

**Mobile Tests (45):**
- `adminAnalyticsScreen.test.tsx` — specific×1; generic×4; semantic=0.398
- `adminBankAccountsScreen.test.tsx` — generic×2; semantic=0.416
- `adminDashboardScreen.test.ts` — specific×1; generic×4; semantic=0.476
- `adminGuardedScreens.test.tsx` — specific×1; generic×4; semantic=0.399
- `adminManagementUtils.test.ts` — specific×1; generic×2; semantic=0.441
- `adminMobileAudit.test.tsx` — specific×1; generic×4; semantic=0.409
- `adminPromotionsHub.test.tsx` — specific×1; generic×1; semantic=0.408
- `authRecoveryScreens.test.tsx` — specific×1; generic×2; semantic=0.391
- `authStore.test.ts` — specific×1; generic×3; semantic=0.425
- `backgroundJobStore.test.ts` — specific×1; generic×2; semantic=0.425
- `backgroundJobs.test.ts` — specific×1; generic×3; semantic=0.434
- `cartScreen.test.tsx` — generic×3; semantic=0.433
- `chatbotScreen.test.tsx` — specific×1; generic×3; semantic=0.453
- `checkoutFlow.test.ts` — generic×2; semantic=0.431
- `checkoutScreen.test.tsx` — generic×4; semantic=0.396
- `customerAccountScreens.test.tsx` — specific×2; generic×4; semantic=0.427
- `flashSalesScreen.test.ts` — generic×3; semantic=0.424
- `loginScreen.test.ts` — specific×1; generic×4; semantic=0.444
- `loginScreenRouting.test.tsx` — specific×1; generic×3; semantic=0.411
- `logisticsPartnerApi.test.ts` — generic×3; semantic=0.472
- … +25 more

**E2E Tests (62):**
- `e2e/auth.spec.ts` — specific×1; generic×1; semantic=0.444
- `e2e/mobile-smoke.spec.ts` — generic×2; semantic=0.451
- `web_app/e2e/admin-audit-fixes.spec.ts` — generic×3; semantic=0.463
- `web_app/e2e/admin-commission.spec.ts` — generic×2; semantic=0.473
- `web_app/e2e/admin-communication-hub.spec.ts` — specific×5; generic×6; semantic=0.619
- `web_app/e2e/admin-country-control-plane.spec.ts` — specific×2; generic×6; semantic=0.429
- `web_app/e2e/admin-country-enhanced.spec.ts` — specific×2; generic×6; semantic=0.420
- `web_app/e2e/admin-data-ops.spec.ts` — specific×2; generic×3; semantic=0.439
- `web_app/e2e/admin-hr-permissions.spec.ts` — specific×1; generic×2; semantic=0.521
- `web_app/e2e/admin-logistics-pricing-insights-live.spec.ts` — specific×2; generic×4; semantic=0.441
- `web_app/e2e/admin-logistics-workspace.spec.ts` — specific×3; generic×6; semantic=0.503
- `web_app/e2e/admin-modules-reconciliation.spec.ts` — specific×5; generic×4; semantic=0.490
- `web_app/e2e/admin-payment-gateways.spec.ts` — specific×1; generic×5; semantic=0.495
- `web_app/e2e/admin-supplier-logistics-sanity.spec.ts` — specific×1; generic×6; semantic=0.468
- `web_app/e2e/admin-treasury-payout.spec.ts` — generic×2; semantic=0.470
- `web_app/e2e/amendment-verify.spec.ts` — generic×3; semantic=0.405
- `web_app/e2e/auth-registration-login.spec.ts` — specific×2; generic×4; semantic=0.472
- `web_app/e2e/auth-role-login.spec.ts` — generic×2; semantic=0.455
- `web_app/e2e/bg-comparison-visual.spec.ts` — specific×1; generic×2; semantic=0.450
- `web_app/e2e/chatbot-shopping-assistant.spec.ts` — specific×1; generic×1; semantic=0.508
- … +42 more

**Migrations (15):**
- `alembic/_analyze_graph.py` — specific×1; generic×2; semantic=0.427
- `alembic/_diagnose_tree.py` — specific×1; generic×2; semantic=0.423
- `alembic/_graph_analysis.py` — specific×1; generic×2; semantic=0.424
- `alembic/versions/2026_07_26_16_09-b81bfc888610_baseline_canonical_orm_schema_clean.py` — generic×2; semantic=0.432
- `alembic/versions/2026_07_26_21_30_c9e8f7d6a5b4_add_communication_gap_tables.py` — specific×4; generic×4; semantic=0.657
- `alembic/versions/2026_07_27_00_32-c0f3f1817791_add_production_postgres_indexes.py` — specific×2; generic×3; semantic=0.449
- `alembic/versions/2026_07_27_09_08-20260727_0908_add_check_constraints_to_status_enum_columns.py` — generic×2; semantic=0.423
- `alembic/versions/2026_07_28_0000_employee_hr_tables.py` — specific×2; generic×5; semantic=0.453
- `alembic/versions/2026_07_28_19_30-e8efae30fc29_add_missing_indexes_and_constraints.py` — specific×2; generic×4; semantic=0.407
- `alembic/versions/2026_07_28_21_14-87146598d2c3_add_missing_fk_constraints_for_.py` — specific×1; generic×2; semantic=0.415
- `alembic/versions/2026_07_29_10_28-9ff24a0683dd_schema_drift_check.py` — specific×1; generic×2; semantic=0.409
- `alembic/versions/2026_07_30_0003-20260730_0003_create_upload_jobs_table.py` — generic×4; semantic=0.452
- `alembic/versions/2026_07_30_0005-20260730_0005_bounded_context_schema_migration.py` — specific×5; generic×11; semantic=0.486
- `alembic/versions/2026_08_06_0001_add_analytics_audit_columns.py` — specific×1; generic×4; semantic=0.488
- `alembic/versions/2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py` — specific×6; generic×12; semantic=0.457

**Backend Scripts (2):**
- `seed_all.py` — specific×7; generic×10; semantic=0.539
- `fix_chat.py` — specific×1; generic×1; semantic=0.568

**Backend Other (7):**
- `models_country_enhancements.py` — specific×1; semantic=0.489
- `lifespan.py` — specific×1; generic×3; semantic=0.478
- `communication.py` — specific×1; semantic=0.616
- `settings/notification_worker.py` — specific×2; generic×4; semantic=0.511
- `tasks/background_tasks.py` — generic×2; semantic=0.460
- `tools/mcp/mcp_server.py` — specific×2; generic×6; semantic=0.552
- `zozi_mcp/zozi_mcp.py` — specific×1; generic×3; semantic=0.557

---

### SYS_002 — Product & Catalog System  (15.7%)

**Checkpoints:** 1 tables · 0 routes · 0 statuses · 7 fields · 0 capabilities · 0 steps · 10 search terms
**Matched files:** 1183 / 1841 (64.3%)

**Completion Breakdown:**

| Component | Score | Weight |
|---|---|---|
| 🗄️ DB tables | 0.0% | 20% |
| 🔌 API routes | n/a | 15% |
| 🚦 Status machine | n/a | 15% |
| 💪 Capabilities | n/a | 10% |
| 🖥️ Panel sections | 76.7% | 20% |
| 🧪 Tests | 25.0% | 10% |
| 🧱 Steps | n/a | 10% |
| Dead-file penalty (172 unwired) | -20.0% | — |
| **Overall** | **15.7%** | 100% |

**🗄️ Database tables (0.0%):**

- ❌ `fts_products`

**🖥️ Panel sections (76.7%):**

- **§II** — 75.0% (terms 50.0%, web ✅, mobile ✅) — Customer storefront: browse products, product detail, search/filter, wishlist, barcode scan, checkout entry.
- **§III** — 75.0% (terms 50.0%, web ✅, mobile ✅) — Supplier: create/edit products, bulk & batch upload, AI assist, product pages, analytics.
- **§V** — 80.0% (terms 60.0%, web ✅, mobile ✅) — Admin: categories, product verification, promotions, flash sales, suppliers list, command center.

**🧪 Tests (25.0%):**

- ❌ Backend: 0 file(s)
- ❌ Web: 0 file(s)
- ✅ Mobile: 1 file(s) — `flashSalesScreen.test.ts`
- ❌ E2E: 0 file(s)

**⛔ Gap summary (what to build next):**

- **Tables:** `fts_products`
- **Fields:** `products_controller.py`, `test_categories.py`, `test_products.py`

**📁 Files by Layer (top entries):**

**Backend Routers (94):**
- `accounting.py` — generic×4; semantic=0.540
- `addresses.py` — generic×2; semantic=0.512
- `admin.py` — specific×3; generic×12; semantic=0.595
- `admin_banners.py` — generic×2; semantic=0.523
- `admin_categories.py` — specific×1; generic×6; semantic=0.589
- `admin_chat.py` — specific×1; generic×3; semantic=0.500
- `admin_commission.py` — generic×4; semantic=0.537
- `admin_fallback.py` — specific×1; generic×8; semantic=0.563
- `admin_payouts.py` — generic×4; semantic=0.509
- `admin_products.py` — specific×1; generic×5; semantic=0.617
- `admin_promotions.py` — specific×1; generic×2; semantic=0.573
- `admin_suppliers.py` — specific×1; generic×6; semantic=0.546
- `admin_treasury.py` — specific×1; generic×7; semantic=0.525
- `admin_users.py` — generic×3; semantic=0.484
- `admin_video.py` — generic×2; semantic=0.536
- `ai.py` — specific×1; generic×6; semantic=0.581
- `ai_image.py` — specific×1; generic×6; semantic=0.517
- `ai_research.py` — generic×3; semantic=0.491
- `ai_upload.py` — specific×1; generic×10; semantic=0.606
- `auth.py` — specific×1; generic×7; semantic=0.499
- … +74 more

**Backend Controllers (52):**
- `admin/admin_auth.py` — generic×3; semantic=0.475
- `admin/analytics.py` — specific×1; generic×11; semantic=0.536
- `admin/bulk_ops.py` — specific×2; generic×7; semantic=0.583
- `admin/coupons.py` — generic×4; semantic=0.587
- `admin/misc.py` — specific×3; generic×8; semantic=0.557
- `admin/orders.py` — specific×1; generic×7; semantic=0.584
- `admin/payouts.py` — generic×3; semantic=0.520
- `admin/permissions.py` — specific×2; generic×5; semantic=0.531
- `admin/products.py` — specific×2; generic×9; semantic=0.682
- `admin/suppliers.py` — specific×1; generic×7; semantic=0.583
- `admin/tickets.py` — generic×6; semantic=0.541
- `admin/users.py` — specific×1; generic×10; semantic=0.574
- `ai_controller.py` — specific×1; generic×7; semantic=0.558
- `auth_controller.py` — specific×1; generic×9; semantic=0.511
- `banner_controller.py` — specific×1; generic×8; semantic=0.582
- `cart_controller.py` — specific×1; generic×6; semantic=0.624
- `cash_management_controller.py` — specific×1; generic×9; semantic=0.572
- `catalog/category_admin_controller.py` — specific×1; generic×3; semantic=0.637
- `chatbot_controller.py` — specific×2; generic×13; semantic=0.570
- `commerce/package.py` — specific×1; generic×8; semantic=0.640
- … +32 more

**Backend Services (170):**
- `_registry.py` — specific×2; generic×6; semantic=0.579
- `admin_analytics_service.py` — specific×1; generic×4; semantic=0.512
- `advanced_filter_service.py` — specific×1; generic×6; semantic=0.608
- `advanced_search_engine.py` — specific×1; generic×6; semantic=0.634
- `ai/automation_read_service.py` — specific×1; semantic=0.554
- `ai_automation_service.py` — generic×6; semantic=0.557
- `ai_copy_jobs.py` — specific×1; generic×5; semantic=0.584
- `ai_research_jobs.py` — generic×2; semantic=0.501
- `ai_search_service.py` — specific×2; generic×6; semantic=0.666
- `ai_service.py` — specific×2; generic×11; semantic=0.588
- `ai_variant_config.py` — specific×2; generic×13; semantic=0.595
- `approval_matrix_service.py` — specific×1; generic×4; semantic=0.528
- `audit/audit_trail_service.py` — generic×2; semantic=0.500
- `auth_service.py` — specific×1; generic×6; semantic=0.509
- `auth_write_service.py` — generic×3; semantic=0.550
- `auto_payout_scheduler.py` — generic×5; semantic=0.517
- `automation_scheduler.py` — specific×1; generic×6; semantic=0.527
- `background_check.py` — specific×1; generic×7; semantic=0.556
- `bg_removal_presets.py` — specific×1; generic×5; semantic=0.514
- `bg_removal_service.py` — specific×1; generic×10; semantic=0.545
- … +150 more

**Backend Models (25):**
- `__init__.py` — specific×4; generic×10; semantic=0.573
- `admin.py` — specific×2; generic×11; semantic=0.566
- `ai_upload.py` — specific×1; generic×9; semantic=0.589
- `commission.py` — specific×1; generic×8; semantic=0.574
- `comms/communication.py` — specific×1; generic×5; semantic=0.537
- `comms/core.py` — specific×2; generic×8; semantic=0.550
- `comms/marketing.py` — specific×3; generic×4; semantic=0.620
- `comms/suppliers.py` — generic×3; semantic=0.578
- `country_control.py` — generic×3; semantic=0.518
- `employee_models.py` — specific×1; generic×2; semantic=0.535
- `finance.py` — specific×1; generic×9; semantic=0.549
- `fraud.py` — generic×5; semantic=0.531
- `geography/countries.py` — specific×2; generic×8; semantic=0.524
- `geography/country_economics.py` — specific×1; generic×3; semantic=0.518
- `geography/country_enhancements.py` — specific×1; generic×5; semantic=0.525
- `geography/country_legal.py` — generic×2; semantic=0.523
- `geography/country_tax.py` — generic×2; semantic=0.506
- `logistics.py` — generic×4; semantic=0.552
- `media_models.py` — specific×1; generic×6; semantic=0.601
- `onboarding.py` — generic×2; semantic=0.546
- … +5 more

**Backend Schemas (Pydantic) (3):**
- `schemas.py` — specific×3; generic×13; semantic=0.572
- `schemas.py` — specific×1; generic×8; semantic=0.552
- `utils/schema_audit.py` — specific×1; generic×6; semantic=0.509

**Backend Middleware (13):**
- `middleware/coi_middleware.py` — generic×2; semantic=0.516
- `middleware/country_context.py` — generic×4; semantic=0.541
- `middleware/csrf_middleware.py` — specific×1; generic×3; semantic=0.538
- `middleware/database_security.py` — generic×2; semantic=0.475
- `middleware/impossible_travel_middleware.py` — generic×3; semantic=0.491
- `middleware/orchestrator.py` — specific×1; generic×3; semantic=0.571
- `middleware/pci_dss_compliance.py` — specific×1; generic×3; semantic=0.551
- `middleware/rate_limit_middleware.py` — generic×3; semantic=0.570
- `middleware/security_headers.py` — specific×1; generic×4; semantic=0.479
- `middleware/siem_engine.py` — generic×3; semantic=0.537
- `middleware/webhook_ip_whitelist.py` — generic×2; semantic=0.544
- `middleware/webhook_verification.py` — generic×2; semantic=0.522
- `utils/rls_middleware.py` — generic×2; semantic=0.480

**Backend Utils (31):**
- `utils/analytics_service.py` — specific×1; generic×4; semantic=0.576
- `utils/api_docs.py` — specific×1; generic×4; semantic=0.580
- `utils/audit.py` — generic×3; semantic=0.524
- `utils/auth.py` — specific×1; generic×5; semantic=0.485
- `utils/background_jobs.py` — specific×2; generic×3; semantic=0.536
- `utils/backup.py` — generic×2; semantic=0.501
- `utils/cache.py` — generic×2; semantic=0.527
- `utils/category_tree.py` — specific×1; generic×3; semantic=0.573
- `utils/config.py` — specific×1; generic×7; semantic=0.491
- `utils/constants.py` — specific×1; generic×5; semantic=0.554
- `utils/country_rls.py` — generic×2; semantic=0.507
- `utils/dependencies.py` — generic×4; semantic=0.465
- `utils/email_service.py` — specific×1; generic×5; semantic=0.544
- `utils/entity_messaging.py` — specific×1; generic×3; semantic=0.542
- `utils/error_handler.py` — specific×1; generic×4; semantic=0.524
- `utils/file_validation.py` — generic×3; semantic=0.489
- `utils/invoice_html.py` — generic×4; semantic=0.527
- `utils/key_rotation.py` — generic×3; semantic=0.501
- `utils/ml_worker.py` — specific×1; generic×2; semantic=0.524
- `utils/order_tracking.py` — specific×1; generic×6; semantic=0.573
- … +11 more

**Backend Providers (32):**
- `providers/__init__.py` — specific×1; generic×5; semantic=0.532
- `providers/ai/__init__.py` — specific×1; generic×4; semantic=0.565
- `providers/ai/vision.py` — specific×1; generic×4; semantic=0.585
- `providers/analytics.py` — specific×1; generic×6; semantic=0.546
- `providers/async_workers.py` — specific×2; generic×9; semantic=0.560
- `providers/bg_remover.py` — specific×1; generic×9; semantic=0.499
- `providers/chatbot.py` — specific×1; generic×6; semantic=0.544
- `providers/config.py` — specific×1; generic×4; semantic=0.535
- `providers/country.py` — specific×1; generic×3; semantic=0.556
- `providers/finance_ai.py` — generic×7; semantic=0.568
- `providers/geo.py` — generic×4; semantic=0.464
- `providers/geography/country.py` — specific×1; generic×3; semantic=0.542
- `providers/geography/geo.py` — generic×4; semantic=0.471
- `providers/hr/br_06.py` — specific×1; generic×3; semantic=0.520
- `providers/hr/br_08.py` — specific×2; generic×7; semantic=0.537
- `providers/hr/br_11.py` — specific×1; generic×3; semantic=0.509
- `providers/hr/br_12.py` — specific×1; generic×3; semantic=0.586
- `providers/image.py` — specific×2; generic×10; semantic=0.551
- `providers/legacy/__init__.py` — specific×1; generic×2; semantic=0.503
- `providers/legacy/br_05.py` — specific×1; generic×3; semantic=0.504
- … +12 more

**Backend Core (9):**
- `admin/__init__.py` — specific×1; generic×4; semantic=0.549
- `admin/database.py` — specific×1; generic×5; semantic=0.519
- `data/__init__.py` — specific×1; semantic=0.556
- `database.py` — specific×1; generic×7; semantic=0.527
- `init_db.py` — specific×1; generic×2; semantic=0.496
- `main.py` — specific×1; generic×10; semantic=0.556
- `_exports.py` — specific×2; generic×6; semantic=0.540
- `comms/__init__.py` — generic×2; semantic=0.508
- `catalog/__init__.py` — specific×1; semantic=0.584

**Backend Data/Seed (4):**
- `data/category_tax_profiles.py` — specific×1; generic×6; semantic=0.605
- `data/vat_rates.py` — specific×1; generic×3; semantic=0.578
- `seed.py` — specific×1; generic×9; semantic=0.524
- `treasury_seeder.py` — specific×2; generic×7; semantic=0.486

**Web Pages (96):**
- `web_app/admin/accounting/page.tsx` — generic×2; semantic=0.509
- `web_app/admin/audit-logs/page.tsx` — specific×1; generic×8; semantic=0.494
- `web_app/admin/barcode/page.tsx` — generic×3; semantic=0.539
- `web_app/admin/categories/page.tsx` — specific×1; generic×10; semantic=0.589
- `web_app/admin/command-center/alerts/page.tsx` — generic×2; semantic=0.481
- `web_app/admin/command-center/headlines/create/page.tsx` — generic×6; semantic=0.541
- `web_app/admin/command-center/headlines/page.tsx` — generic×4; semantic=0.530
- `web_app/admin/command-center/page.tsx` — specific×2; generic×11; semantic=0.528
- `web_app/admin/commission/page.tsx` — generic×6; semantic=0.564
- `web_app/admin/countries/[code]/staff/page.tsx` — generic×6; semantic=0.501
- `web_app/admin/countries/page.tsx` — specific×2; generic×11; semantic=0.514
- `web_app/admin/dashboard/page.tsx` — specific×1; generic×5; semantic=0.541
- `web_app/admin/ess/page.tsx` — generic×5; semantic=0.490
- `web_app/admin/finance/page.tsx` — generic×4; semantic=0.519
- `web_app/admin/flash-sales/page.tsx` — specific×1; generic×1; semantic=0.616
- `web_app/admin/hr/page.tsx` — generic×4; semantic=0.509
- `web_app/admin/inventory-alerts/page.tsx` — specific×1; generic×5; semantic=0.582
- `web_app/admin/invoices/page.tsx` — generic×4; semantic=0.535
- `web_app/admin/login/page.tsx` — generic×2; semantic=0.483
- `web_app/admin/logistics/page.tsx` — generic×3; semantic=0.530
- … +76 more

**Web Components (130):**
- `components/EnterpriseDataTable.tsx` — generic×3; semantic=0.545
- `components/ProductCard.ts` — specific×1; generic×2; semantic=0.644
- `components/logo/Logo.web.tsx` — specific×1; semantic=0.492
- `components/logo/LogoAnimation.tsx` — specific×1; semantic=0.476
- `components/ui/ErrorBoundary.tsx` — specific×1; generic×2; semantic=0.471
- `components/ui/LoadingSkeleton.web.tsx` — specific×1; generic×3; semantic=0.491
- `components/ui/SearchBar.web.tsx` — specific×1; generic×3; semantic=0.535
- `components/ui/TranslatedText.web.tsx` — specific×1; generic×3; semantic=0.443
- `components/ui/index.ts` — generic×2; semantic=0.540
- `logo/Logo.web.tsx` — specific×1; semantic=0.484
- `admin/countries/components/AnalyticsTab.tsx` — generic×4; semantic=0.551
- `admin/countries/components/CategoryCommissionsTab.tsx` — generic×4; semantic=0.621
- `admin/countries/components/CommissionTiersTab.tsx` — generic×4; semantic=0.595
- `admin/countries/components/CommunicationsTab.tsx` — specific×1; generic×2; semantic=0.533
- `admin/countries/components/CountriesTabProps.ts` — specific×1; generic×7; semantic=0.530
- `admin/countries/components/FeatureFlagsTab.tsx` — generic×3; semantic=0.561
- `admin/countries/components/KycTab.tsx` — specific×1; generic×4; semantic=0.607
- `admin/countries/components/LegalRulesTab.tsx` — specific×1; generic×5; semantic=0.608
- `admin/countries/components/LocalizationTab.tsx` — generic×3; semantic=0.517
- `admin/countries/components/LogisticsModelTab.tsx` — generic×2; semantic=0.559
- … +110 more

**Web Lib/Hooks (83):**
- `logo/LogoAnimation.tsx` — specific×1; semantic=0.473
- `HomeClient.tsx` — specific×1; generic×7; semantic=0.583
- `admin/countries/CountryLedgerTable.tsx` — generic×7; semantic=0.522
- `admin/dashboard/_components/ExportsPanel.tsx` — specific×2; generic×10; semantic=0.554
- `admin/dashboard/_tabs/AnalyticsTab.tsx` — specific×1; generic×8; semantic=0.524
- `admin/dashboard/_tabs/ApprovalMatrixTab.tsx` — specific×1; generic×7; semantic=0.525
- `admin/dashboard/_tabs/BannerTab.tsx` — specific×1; generic×6; semantic=0.536
- `admin/dashboard/_tabs/CouponsTab.tsx` — generic×3; semantic=0.548
- `admin/dashboard/_tabs/FinanceTab.tsx` — generic×3; semantic=0.512
- `admin/dashboard/_tabs/HierarchyTab.tsx` — generic×4; semantic=0.483
- `admin/dashboard/_tabs/InsightsTab.tsx` — generic×5; semantic=0.515
- `admin/dashboard/_tabs/ModerationTab.tsx` — generic×6; semantic=0.515
- `admin/dashboard/_tabs/OrdersTab.tsx` — generic×2; semantic=0.602
- `admin/dashboard/_tabs/PayoutsTab.tsx` — generic×5; semantic=0.506
- `admin/dashboard/_tabs/ProductsTab.tsx` — specific×2; generic×10; semantic=0.573
- `admin/dashboard/_tabs/SupplierDocumentsTab.tsx` — generic×2; semantic=0.556
- `admin/dashboard/_tabs/TicketsTab.tsx` — generic×4; semantic=0.514
- `admin/disputes/_components/DisputesPanel.tsx` — generic×5; semantic=0.541
- `admin/employees/_components/employees-content.tsx` — generic×6; semantic=0.541
- `admin/employees/_tabs/AddressMatrixTab.tsx` — generic×2; semantic=0.504
- … +63 more

**Web App Files (28):**
- `adminPermissions.ts` — specific×2; generic×4; semantic=0.518
- `api-core.ts` — generic×3; semantic=0.504
- `chatbot.ts` — specific×1; generic×7; semantic=0.563
- `checkoutHelpers.ts` — specific×1; generic×5; semantic=0.572
- `i18n.ts` — specific×1; generic×14; semantic=0.596
- `index.ts` — specific×1; generic×5; semantic=0.560
- `notificationHelpers.ts` — specific×1; generic×2; semantic=0.549
- `notificationStore.ts` — specific×1; generic×5; semantic=0.568
- `productCardModel.ts` — specific×1; generic×2; semantic=0.645
- `productHelpers.ts` — specific×2; generic×3; semantic=0.643
- `productQuery.ts` — specific×1; generic×7; semantic=0.655
- `requestCache.ts` — generic×2; semantic=0.508
- `returnsApi.ts` — specific×1; generic×4; semantic=0.532
- `statusColors.ts` — specific×1; generic×3; semantic=0.563
- `supplierProductOptions.ts` — specific×1; generic×5; semantic=0.588
- `theme.ts` — specific×1; semantic=0.501
- `types.ts` — specific×1; generic×10; semantic=0.576
- `userRealtimeAlerts.ts` — specific×1; generic×5; semantic=0.547
- `web_app/middleware.ts` — specific×1; generic×5; semantic=0.515
- `web_app/next.config.ts` — generic×2; semantic=0.446
- … +8 more

**Frontend Scripts (7):**
- `web_app/scripts/check_pages.py` — specific×1; generic×4; semantic=0.509
- `web_app/scripts/extract_tabs.py` — generic×5; semantic=0.445
- `web_app/scripts/extract_tabs_v2.py` — specific×1; generic×7; semantic=0.470
- `web_app/scripts/final_fixes.py` — specific×1; generic×8; semantic=0.492
- `web_app/scripts/fix_components.py` — specific×1; generic×8; semantic=0.500
- `web_app/scripts/insert_dark_css.py` — specific×1; semantic=0.387
- `web_app/scripts/update_page_imports.py` — specific×1; generic×7; semantic=0.503

**Mobile Screens (97):**
- `(auth)/login.tsx` — specific×1; generic×5; semantic=0.508
- `(auth)/register.tsx` — specific×1; generic×6; semantic=0.489
- `(auth)/reset-password.tsx` — generic×2; semantic=0.495
- `(auth)/verify-email.tsx` — generic×2; semantic=0.498
- `(tabs)/_layout.tsx` — specific×1; generic×4; semantic=0.544
- `(tabs)/cart.tsx` — specific×1; generic×4; semantic=0.567
- `(tabs)/orders/[id].tsx` — specific×1; generic×7; semantic=0.537
- `(tabs)/products/[id].tsx` — specific×1; generic×11; semantic=0.577
- `(tabs)/products/index.tsx` — specific×3; generic×11; semantic=0.615
- `(tabs)/profile.tsx` — specific×1; generic×9; semantic=0.501
- `_layout.tsx` — specific×1; generic×8; semantic=0.548
- `admin/analytics.tsx` — specific×1; generic×6; semantic=0.565
- `admin/audit-logs.tsx` — generic×3; semantic=0.536
- `admin/bank-accounts.tsx` — generic×5; semantic=0.524
- `admin/banners.tsx` — specific×1; generic×6; semantic=0.525
- `admin/barcode.tsx` — generic×3; semantic=0.602
- `admin/coupons.tsx` — generic×3; semantic=0.571
- `admin/dashboard.tsx` — specific×3; generic×10; semantic=0.561
- `admin/email.tsx` — generic×3; semantic=0.532
- `admin/exports.tsx` — specific×2; generic×6; semantic=0.546
- … +77 more

**Mobile Components (28):**
- `components/AddressesScreen.tsx` — generic×3; semantic=0.512
- `components/AuthRequiredModal.tsx` — generic×3; semantic=0.557
- `components/BackgroundJobCenter.tsx` — generic×2; semantic=0.513
- `components/CartItem.tsx` — specific×1; generic×4; semantic=0.537
- `components/HeroBanner.tsx` — specific×1; generic×4; semantic=0.572
- `components/HomeProductShowcase.tsx` — specific×2; generic×6; semantic=0.614
- `components/MobileBackgroundEffect.tsx` — generic×2; semantic=0.493
- `components/MobileSeasonalBanner.tsx` — specific×2; generic×8; semantic=0.564
- `components/OrderCard.tsx` — specific×1; generic×3; semantic=0.580
- `components/ProductCard.tsx` — specific×1; generic×5; semantic=0.620
- `components/QuickViewModal.tsx` — specific×1; generic×6; semantic=0.581
- `components/RecentlyViewed.tsx` — specific×1; generic×2; semantic=0.566
- `components/Recommendations.tsx` — specific×2; generic×6; semantic=0.569
- `components/ToastContainer.tsx` — generic×2; semantic=0.530
- `components/ui/AppHeader.tsx` — specific×1; generic×7; semantic=0.550
- `components/ui/Footer.tsx` — specific×1; generic×4; semantic=0.524
- `components/ui/HeaderBar.tsx` — specific×1; generic×3; semantic=0.510
- `components/ui/LoadingSkeleton.tsx` — specific×1; generic×2; semantic=0.482
- `components/ui/ProductGrid.tsx` — specific×1; generic×3; semantic=0.574
- `components/ui/ProductSearchFilterBar.tsx` — specific×1; generic×7; semantic=0.600
- … +8 more

**Mobile Lib/Hooks (18):**
- `lib/adminManagementUtils.ts` — generic×4; semantic=0.553
- `lib/api.ts` — specific×1; generic×12; semantic=0.537
- `lib/authPrompt.tsx` — generic×2; semantic=0.519
- `lib/authStore.ts` — generic×4; semantic=0.520
- `lib/backgroundJobs.ts` — specific×1; generic×3; semantic=0.523
- `lib/cartStore.ts` — specific×1; generic×2; semantic=0.602
- `lib/chatbotStore.ts` — specific×1; generic×2; semantic=0.532
- `lib/fileSystem.ts` — specific×1; generic×1; semantic=0.536
- `lib/homeInsights.ts` — specific×1; generic×4; semantic=0.520
- `lib/invoiceService.ts` — specific×1; generic×5; semantic=0.547
- `lib/paymentService.ts` — specific×1; generic×3; semantic=0.531
- `lib/productDraft.ts` — specific×1; generic×4; semantic=0.572
- `lib/productRouteFilters.ts` — specific×1; generic×6; semantic=0.636
- `lib/recentlyViewedStore.ts` — specific×1; generic×4; semantic=0.630
- `lib/supplierProductForm.ts` — generic×4; semantic=0.658
- `lib/themeStore.ts` — specific×1; generic×1; semantic=0.514
- `lib/wishlistStore.ts` — specific×1; generic×3; semantic=0.594
- `theme/index.ts` — specific×2; generic×2; semantic=0.541

**Backend Tests (57):**
- `conftest.py` — generic×6; semantic=0.529
- `playwright/e2e/auth.spec.ts` — generic×4; semantic=0.454
- `playwright/e2e/cart.spec.ts` — generic×2; semantic=0.511
- `playwright/e2e/finance-automation.spec.ts` — generic×5; semantic=0.507
- `playwright/e2e/products.spec.ts` — specific×1; generic×7; semantic=0.577
- `playwright/e2e/user-profile.spec.ts` — generic×2; semantic=0.470
- `test_admin.py` — specific×1; generic×5; semantic=0.477
- `test_ai_research_jobs.py` — generic×3; semantic=0.500
- `test_ai_research_router.py` — generic×3; semantic=0.521
- `test_api_endpoints.py` — specific×1; generic×8; semantic=0.411
- `test_api_pagination.py` — specific×1; generic×6; semantic=0.554
- `test_auth.py` — generic×4; semantic=0.437
- `test_auto_payout_sweep.py` — generic×2; semantic=0.544
- `test_background_jobs.py` — generic×3; semantic=0.483
- `test_banners.py` — specific×1; generic×4; semantic=0.499
- `test_cart.py` — specific×1; generic×8; semantic=0.565
- `test_categories.py` — generic×5; semantic=0.553
- `test_chat.py` — specific×2; generic×5; semantic=0.476
- `test_circuit_breaker.py` — generic×2; semantic=0.476
- `test_comprehensive_system.py` — specific×2; generic×12; semantic=0.562
- … +37 more

**Web Tests (63):**
- `__tests__/chatbot.test.ts` — specific×1; generic×4; semantic=0.497
- `__tests__/checkoutHelpers.test.ts` — specific×1; generic×5; semantic=0.512
- `chatbot.test.ts` — specific×1; generic×4; semantic=0.492
- `checkoutHelpers.test.ts` — specific×1; generic×5; semantic=0.522
- `components/ProductCard.test.ts` — specific×1; generic×5; semantic=0.626
- `web_app/__tests__/browser.spec.ts` — specific×1; generic×5; semantic=0.496
- `Chatbot.test.tsx` — specific×1; generic×8; semantic=0.483
- `components/ApprovalActionModal.test.tsx` — generic×2; semantic=0.548
- `components/CountryDetailWorkspace.test.tsx` — generic×6; semantic=0.537
- `components/CountryResearchPanel.test.tsx` — specific×1; generic×4; semantic=0.538
- `components/Footer.test.tsx` — specific×1; generic×3; semantic=0.519
- `components/GhostRowForm.test.tsx` — generic×4; semantic=0.528
- `components/Header.test.tsx` — generic×4; semantic=0.496
- `components/ProductCard.test.tsx` — specific×1; generic×5; semantic=0.600
- `components/QuickViewModal.test.tsx` — specific×1; generic×7; semantic=0.557
- `components/Recommendations.test.tsx` — specific×1; generic×6; semantic=0.542
- `components/emailComponents.test.tsx` — generic×4; semantic=0.523
- `lib/adminPermissions.test.ts` — specific×2; generic×4; semantic=0.487
- `lib/api.test.ts` — specific×1; generic×6; semantic=0.482
- `lib/cartStore.test.ts` — specific×1; generic×7; semantic=0.580
- … +43 more

**Mobile Tests (54):**
- `addressesScreen.test.ts` — generic×2; semantic=0.478
- `adminAnalyticsScreen.test.tsx` — specific×1; generic×5; semantic=0.498
- `adminBankAccountsScreen.test.tsx` — generic×3; semantic=0.497
- `adminDashboardScreen.test.ts` — specific×1; generic×8; semantic=0.543
- `adminGuardedScreens.test.tsx` — specific×2; generic×6; semantic=0.495
- `adminMobileAudit.test.tsx` — specific×1; generic×10; semantic=0.491
- `adminPromotionsHub.test.tsx` — specific×1; generic×2; semantic=0.481
- `api.test.ts` — specific×1; generic×2; semantic=0.486
- `authRecoveryScreens.test.tsx` — generic×3; semantic=0.489
- `authStore.test.ts` — generic×2; semantic=0.490
- `backgroundJobs.test.ts` — specific×1; generic×1; semantic=0.480
- `cartScreen.test.tsx` — specific×1; generic×5; semantic=0.553
- `cartStore.test.ts` — specific×1; generic×6; semantic=0.547
- `chatbotScreen.test.tsx` — specific×1; generic×7; semantic=0.481
- `checkoutFlow.test.ts` — specific×1; generic×6; semantic=0.566
- `checkoutScreen.test.tsx` — specific×1; generic×8; semantic=0.511
- `couponsScreen.test.ts` — generic×3; semantic=0.569
- `currencyStore.test.ts` — generic×2; semantic=0.543
- `customerAccountScreens.test.tsx` — specific×1; generic×7; semantic=0.499
- `flashSalesScreen.test.ts` — specific×3; generic×6; semantic=0.609
- … +34 more

**E2E Tests (60):**
- `e2e/mobile-smoke.spec.ts` — specific×1; generic×4; semantic=0.500
- `web_app/e2e/admin-audit-fixes.spec.ts` — generic×2; semantic=0.457
- `web_app/e2e/admin-commission.spec.ts` — generic×5; semantic=0.527
- `web_app/e2e/admin-communication-hub.spec.ts` — generic×3; semantic=0.480
- `web_app/e2e/admin-country-control-plane.spec.ts` — generic×6; semantic=0.458
- `web_app/e2e/admin-country-enhanced.spec.ts` — specific×1; generic×10; semantic=0.467
- `web_app/e2e/admin-data-ops.spec.ts` — generic×3; semantic=0.454
- `web_app/e2e/admin-hr-permissions.spec.ts` — specific×1; generic×6; semantic=0.475
- `web_app/e2e/admin-logistics-pricing-insights-live.spec.ts` — generic×3; semantic=0.495
- `web_app/e2e/admin-logistics-workspace.spec.ts` — generic×7; semantic=0.491
- `web_app/e2e/admin-modules-reconciliation.spec.ts` — specific×1; generic×4; semantic=0.510
- `web_app/e2e/admin-payment-gateways.spec.ts` — specific×1; generic×7; semantic=0.488
- `web_app/e2e/admin-supplier-logistics-sanity.spec.ts` — specific×1; generic×7; semantic=0.544
- `web_app/e2e/admin-treasury-payout.spec.ts` — generic×3; semantic=0.490
- `web_app/e2e/amendment-verify.spec.ts` — generic×3; semantic=0.464
- `web_app/e2e/auth-registration-login.spec.ts` — specific×1; generic×7; semantic=0.520
- `web_app/e2e/auth-role-login.spec.ts` — specific×1; generic×5; semantic=0.488
- `web_app/e2e/bg-comparison-visual.spec.ts` — specific×1; generic×8; semantic=0.522
- `web_app/e2e/chatbot-shopping-assistant.spec.ts` — specific×1; generic×2; semantic=0.493
- `web_app/e2e/collapse-poll.spec.ts` — generic×2; semantic=0.489
- … +40 more

**Migrations (20):**
- `alembic/_analyze_graph.py` — generic×2; semantic=0.461
- `alembic/_graph_analysis.py` — generic×2; semantic=0.468
- `alembic/versions/2026_07_26_21_30_c9e8f7d6a5b4_add_communication_gap_tables.py` — generic×4; semantic=0.498
- `alembic/versions/2026_07_27_00_32-c0f3f1817791_add_production_postgres_indexes.py` — specific×1; generic×8; semantic=0.570
- `alembic/versions/2026_07_27_09_08-20260727_0908_add_check_constraints_to_status_enum_columns.py` — generic×3; semantic=0.511
- `alembic/versions/2026_07_28_0000_employee_hr_tables.py` — specific×1; generic×2; semantic=0.525
- `alembic/versions/2026_07_28_19_30-e8efae30fc29_add_missing_indexes_and_constraints.py` — specific×2; generic×7; semantic=0.548
- `alembic/versions/2026_07_28_21_14-87146598d2c3_add_missing_fk_constraints_for_.py` — specific×1; generic×2; semantic=0.494
- `alembic/versions/2026_07_29_10_17-e281faa0c087_add_orm_models_for_orphaned_employee_.py` — generic×3; semantic=0.521
- `alembic/versions/2026_07_29_10_28-9ff24a0683dd_schema_drift_check.py` — specific×1; generic×5; semantic=0.520
- `alembic/versions/2026_07_29_19_14-20260729_1914_add_products_search_vector_trigger.py` — specific×1; generic×6; semantic=0.605
- `alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py` — specific×1; generic×2; semantic=0.537
- `alembic/versions/2026_07_30_0002-20260730_0002_create_points_transactions_table.py` — generic×2; semantic=0.505
- `alembic/versions/2026_07_30_0003-20260730_0003_create_upload_jobs_table.py` — specific×1; generic×7; semantic=0.521
- `alembic/versions/2026_07_30_0004-20260730_0004_create_event_tables.py` — generic×2; semantic=0.508
- `alembic/versions/2026_07_30_0005-20260730_0005_bounded_context_schema_migration.py` — specific×2; generic×11; semantic=0.491
- `alembic/versions/2026_08_06_0001_add_analytics_audit_columns.py` — generic×3; semantic=0.546
- `alembic/versions/2026_08_06_0001_media_add_audit_softdelete_mixins_and_rename_ai_result.py` — generic×2; semantic=0.577
- `alembic/versions/2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py` — specific×2; generic×15; semantic=0.502
- `alembic/versions/2026_08_06_0004-catalog_categories_dba03_audit_softdelete.py` — specific×1; generic×2; semantic=0.617

**Backend Scripts (2):**
- `seed_all.py` — specific×2; generic×11; semantic=0.509
- `fix_chat.py` — specific×1; semantic=0.466

**Backend Other (7):**
- `dependencies/country_rls.py` — generic×2; semantic=0.491
- `events/event_publisher.py` — specific×1; generic×2; semantic=0.573
- `lifespan.py` — specific×2; generic×3; semantic=0.594
- `marketing.py` — specific×1; semantic=0.658
- `upload_job.py` — generic×2; semantic=0.498
- `tools/mcp/mcp_server.py` — specific×2; generic×11; semantic=0.558
- `zozi_mcp/zozi_mcp.py` — specific×2; generic×9; semantic=0.588

---

### SYS_031 — Cash Management / Finance / Treasury System  (65.8%)

**Checkpoints:** 0 tables · 0 routes · 0 statuses · 10 fields · 0 capabilities · 0 steps · 15 search terms
**Matched files:** 963 / 1841 (52.3%)

**Completion Breakdown:**

| Component | Score | Weight |
|---|---|---|
| 🗄️ DB tables | n/a | 20% |
| 🔌 API routes | n/a | 15% |
| 🚦 Status machine | n/a | 15% |
| 💪 Capabilities | n/a | 10% |
| 🖥️ Panel sections | 91.1% | 20% |
| 🧪 Tests | 75.0% | 10% |
| 🧱 Steps | n/a | 10% |
| Dead-file penalty (168 unwired) | -20.0% | — |
| **Overall** | **65.8%** | 100% |

**🖥️ Panel sections (91.1%):**

- **§III** — 96.7% (terms 93.3%, web ✅, mobile ✅) — Supplier finance: payout status, bank account self-service, settlement visibility.
- **§IV** — 80.0% (terms 60.0%, web ✅, mobile ✅) — Logistics partner: COD remittance receipts, settlement and payout visibility.
- **§V** — 96.7% (terms 93.3%, web ✅, mobile ✅) — Admin: payouts console, treasury dashboard, cash-flow cycle, finance automation, background jobs.

**🧪 Tests (75.0%):**

- ✅ Backend: 3 file(s) — `test_auto_payout_sweep.py`, `test_finance_audit.py`, `test_treasury.py`
- ✅ Web: 2 file(s) — `pages/adminFinanceCodVerification.test.tsx`, `pages/adminStandalonePages.test.tsx`
- ❌ Mobile: 0 file(s)
- ✅ E2E: 2 file(s) — `web_app/e2e/admin-treasury-payout.spec.ts`, `web_app/e2e/supplier-smoke.spec.ts`

**📁 Files by Layer (top entries):**

**Backend Routers (102):**
- `accounting.py` — specific×3; generic×5; semantic=0.665
- `addresses.py` — generic×2; semantic=0.483
- `admin.py` — specific×2; generic×7; semantic=0.571
- `admin_cash.py` — specific×2; generic×4; semantic=0.630
- `admin_categories.py` — generic×2; semantic=0.507
- `admin_chat.py` — specific×1; generic×4; semantic=0.517
- `admin_commission.py` — generic×2; semantic=0.491
- `admin_email.py` — generic×2; semantic=0.512
- `admin_fallback.py` — specific×2; generic×5; semantic=0.556
- `admin_logistics.py` — generic×3; semantic=0.525
- `admin_orders.py` — generic×2; semantic=0.524
- `admin_payouts.py` — specific×4; generic×5; semantic=0.632
- `admin_products.py` — generic×2; semantic=0.515
- `admin_suppliers.py` — generic×3; semantic=0.499
- `admin_treasury.py` — specific×8; generic×6; semantic=0.661
- `admin_video.py` — generic×4; semantic=0.520
- `ai.py` — specific×1; generic×1; semantic=0.478
- `ai_image.py` — generic×2; semantic=0.428
- `ai_research.py` — generic×2; semantic=0.444
- `ai_upload.py` — generic×5; semantic=0.547
- … +82 more

**Backend Controllers (59):**
- `accounting_controller.py` — specific×1; generic×3; semantic=0.634
- `admin/admin_auth.py` — generic×3; semantic=0.468
- `admin/analytics.py` — generic×5; semantic=0.514
- `admin/bulk_ops.py` — generic×5; semantic=0.581
- `admin/coupons.py` — specific×1; generic×3; semantic=0.609
- `admin/misc.py` — specific×1; generic×5; semantic=0.559
- `admin/orders.py` — specific×2; generic×3; semantic=0.566
- `admin/payouts.py` — specific×4; generic×5; semantic=0.681
- `admin/permissions.py` — specific×1; generic×3; semantic=0.503
- `admin/products.py` — specific×2; generic×4; semantic=0.541
- `admin/suppliers.py` — specific×1; generic×6; semantic=0.550
- `admin/tickets.py` — specific×1; generic×3; semantic=0.536
- `admin/users.py` — specific×5; generic×6; semantic=0.592
- `ai_controller.py` — generic×2; semantic=0.498
- `auth_controller.py` — specific×1; generic×6; semantic=0.523
- `banner_controller.py` — specific×1; generic×4; semantic=0.555
- `cart_controller.py` — generic×4; semantic=0.528
- `cash_management_controller.py` — specific×7; generic×6; semantic=0.741
- `catalog/category_admin_controller.py` — specific×1; generic×2; semantic=0.498
- `chatbot_controller.py` — generic×5; semantic=0.547
- … +39 more

**Backend Services (198):**
- `_registry.py` — specific×3; generic×4; semantic=0.549
- `admin_analytics_service.py` — generic×2; semantic=0.534
- `ai/automation_read_service.py` — specific×2; generic×2; semantic=0.563
- `ai_automation_service.py` — specific×3; generic×4; semantic=0.616
- `ai_copy_jobs.py` — generic×3; semantic=0.524
- `ai_service.py` — generic×3; semantic=0.491
- `ai_variant_config.py` — specific×1; generic×4; semantic=0.552
- `approval_matrix_service.py` — specific×1; generic×3; semantic=0.516
- `asset_tracking.py` — specific×1; generic×2; semantic=0.570
- `attendance_service.py` — generic×2; semantic=0.546
- `audit_service.py` — generic×2; semantic=0.562
- `auth_service.py` — generic×5; semantic=0.564
- `auth_write_service.py` — generic×5; semantic=0.553
- `auto_payout_scheduler.py` — specific×4; generic×7; semantic=0.659
- `automation_scheduler.py` — specific×8; generic×5; semantic=0.555
- `background_check.py` — generic×3; semantic=0.494
- `bg_removal_presets.py` — generic×2; semantic=0.482
- `bg_removal_service.py` — generic×3; semantic=0.573
- `cash_flow_forecast_service.py` — specific×4; generic×3; semantic=0.676
- `cash_management_service.py` — specific×7; generic×7; semantic=0.825
- … +178 more

**Backend Models (21):**
- `__init__.py` — specific×12; generic×6; semantic=0.565
- `admin.py` — specific×4; generic×6; semantic=0.571
- `ai_upload.py` — generic×3; semantic=0.561
- `commission.py` — generic×3; semantic=0.543
- `comms/communication.py` — specific×1; generic×2; semantic=0.522
- `comms/core.py` — specific×1; generic×4; semantic=0.538
- `comms/suppliers.py` — generic×4; semantic=0.542
- `country_control.py` — generic×4; semantic=0.559
- `employee_models.py` — specific×1; generic×3; semantic=0.539
- `finance.py` — specific×12; generic×4; semantic=0.626
- `fraud.py` — generic×6; semantic=0.558
- `geography/countries.py` — specific×2; generic×4; semantic=0.534
- `geography/country_economics.py` — specific×1; generic×3; semantic=0.538
- `geography/country_enhancements.py` — specific×1; generic×3; semantic=0.507
- `logistics.py` — generic×4; semantic=0.555
- `media_models.py` — generic×2; semantic=0.549
- `onboarding.py` — generic×2; semantic=0.568
- `orders.py` — generic×5; semantic=0.554
- `payments.py` — specific×2; generic×4; semantic=0.590
- `products.py` — generic×2; semantic=0.545
- … +1 more

**Backend Schemas (Pydantic) (2):**
- `schemas.py` — specific×9; generic×7; semantic=0.562
- `schemas.py` — generic×2; semantic=0.508

**Backend Middleware (8):**
- `middleware/behavioral_analytics.py` — generic×2; semantic=0.491
- `middleware/coi_middleware.py` — generic×4; semantic=0.559
- `middleware/country_context.py` — generic×3; semantic=0.529
- `middleware/impossible_travel_middleware.py` — generic×3; semantic=0.499
- `middleware/pci_dss_compliance.py` — specific×2; generic×3; semantic=0.569
- `middleware/rate_limit_middleware.py` — generic×3; semantic=0.518
- `middleware/siem_engine.py` — specific×1; generic×2; semantic=0.592
- `utils/rls_middleware.py` — generic×3; semantic=0.466

**Backend Utils (27):**
- `write_helpers.py` — specific×1; generic×1; semantic=0.582
- `utils/analytics_service.py` — generic×3; semantic=0.525
- `utils/auth.py` — generic×3; semantic=0.537
- `utils/background_jobs.py` — specific×1; generic×1; semantic=0.541
- `utils/config.py` — specific×1; generic×1; semantic=0.524
- `utils/constants.py` — specific×3; generic×5; semantic=0.566
- `utils/country_rls.py` — generic×4; semantic=0.491
- `utils/dependencies.py` — generic×5; semantic=0.486
- `utils/email_service.py` — generic×4; semantic=0.587
- `utils/entity_messaging.py` — specific×1; generic×3; semantic=0.521
- `utils/error_handler.py` — specific×1; generic×2; semantic=0.590
- `utils/file_validation.py` — generic×2; semantic=0.462
- `utils/invoice_html.py` — generic×3; semantic=0.475
- `utils/key_rotation.py` — generic×4; semantic=0.486
- `utils/kms_encryption.py` — specific×1; generic×1; semantic=0.472
- `utils/ml_worker.py` — specific×1; generic×2; semantic=0.493
- `utils/order_tracking.py` — specific×2; generic×4; semantic=0.546
- `utils/realtime.py` — generic×4; semantic=0.532
- `utils/redis_client.py` — generic×2; semantic=0.479
- `utils/rls_context.py` — specific×1; generic×2; semantic=0.457
- … +7 more

**Backend Providers (17):**
- `providers/__init__.py` — specific×1; semantic=0.522
- `providers/analytics.py` — generic×2; semantic=0.495
- `providers/async_workers.py` — specific×1; generic×1; semantic=0.514
- `providers/bg_remover.py` — specific×1; generic×1; semantic=0.475
- `providers/chatbot.py` — generic×2; semantic=0.479
- `providers/config.py` — specific×1; semantic=0.513
- `providers/country.py` — specific×1; semantic=0.477
- `providers/finance_ai.py` — specific×1; generic×1; semantic=0.590
- `providers/geography/country.py` — specific×1; semantic=0.468
- `providers/hr/br_08.py` — specific×1; generic×1; semantic=0.543
- `providers/image.py` — specific×1; generic×1; semantic=0.501
- `providers/legacy/br_08.py` — specific×1; generic×1; semantic=0.599
- `providers/map.py` — specific×1; generic×1; semantic=0.488
- `providers/ocr.py` — specific×1; semantic=0.479
- `providers/parcel_verification.py` — generic×2; semantic=0.509
- `providers/text.py` — specific×3; generic×1; semantic=0.522
- `providers/voice_to_text.py` — specific×2; generic×1; semantic=0.476

**Backend Core (10):**
- `admin/__init__.py` — generic×2; semantic=0.590
- `admin/database.py` — specific×1; generic×3; semantic=0.537
- `treasury/__init__.py` — specific×2; generic×1; semantic=0.618
- `data/__init__.py` — specific×1; generic×1; semantic=0.513
- `database.py` — specific×2; generic×4; semantic=0.514
- `main.py` — specific×5; generic×6; semantic=0.596
- `_exports.py` — specific×2; generic×4; semantic=0.500
- `comms/__init__.py` — generic×2; semantic=0.442
- `orders/__init__.py` — specific×2; generic×2; semantic=0.596
- `treasury/__init__.py` — specific×2; generic×1; semantic=0.658

**Backend Data/Seed (5):**
- `data/ledger_facade.py` — specific×4; generic×2; semantic=0.638
- `data/ledger_impl_bridge.py` — specific×2; generic×2; semantic=0.604
- `data/logistics_pricing_facade.py` — specific×2; generic×2; semantic=0.585
- `seed.py` — specific×1; generic×5; semantic=0.544
- `treasury_seeder.py` — specific×3; generic×5; semantic=0.660

**Web Pages (79):**
- `web_app/admin/accounting/page.tsx` — specific×2; generic×2; semantic=0.561
- `web_app/admin/audit-logs/page.tsx` — generic×2; semantic=0.491
- `web_app/admin/bank-accounts/page.tsx` — specific×1; generic×2; semantic=0.575
- `web_app/admin/barcode/page.tsx` — generic×3; semantic=0.458
- `web_app/admin/command-center/headlines/create/page.tsx` — specific×1; generic×1; semantic=0.418
- `web_app/admin/command-center/page.tsx` — specific×3; generic×5; semantic=0.485
- `web_app/admin/commission/page.tsx` — specific×1; generic×3; semantic=0.456
- `web_app/admin/communication/page.tsx` — generic×2; semantic=0.386
- `web_app/admin/countries/[code]/staff/page.tsx` — specific×1; generic×2; semantic=0.421
- `web_app/admin/countries/page.tsx` — specific×2; generic×5; semantic=0.442
- `web_app/admin/dashboard/page.tsx` — specific×1; generic×4; semantic=0.420
- `web_app/admin/email/page.tsx` — specific×1; generic×1; semantic=0.457
- `web_app/admin/employees/page.tsx` — specific×1; generic×1; semantic=0.458
- `web_app/admin/ess/page.tsx` — generic×3; semantic=0.442
- `web_app/admin/finance/page.tsx` — specific×4; generic×3; semantic=0.557
- `web_app/admin/hr/page.tsx` — generic×2; semantic=0.459
- `web_app/admin/inventory-alerts/page.tsx` — generic×2; semantic=0.479
- `web_app/admin/invoices/page.tsx` — specific×1; generic×3; semantic=0.488
- `web_app/admin/logistics-partners/page.tsx` — generic×2; semantic=0.511
- `web_app/admin/logistics/page.tsx` — generic×3; semantic=0.475
- … +59 more

**Web Components (70):**
- `components/logo/Logo.web.tsx` — specific×1; semantic=0.450
- `components/logo/LogoAnimation.tsx` — specific×1; semantic=0.450
- `components/ui/ErrorBoundary.tsx` — specific×1; semantic=0.431
- `logo/Logo.web.tsx` — specific×1; semantic=0.454
- `admin/countries/components/AnalyticsTab.tsx` — generic×2; semantic=0.483
- `admin/countries/components/CommunicationsTab.tsx` — specific×1; generic×1; semantic=0.462
- `admin/countries/components/CountriesTabProps.ts` — specific×1; generic×3; semantic=0.483
- `admin/countries/components/KycTab.tsx` — generic×2; semantic=0.527
- `admin/countries/components/LogisticsModelTab.tsx` — specific×1; generic×2; semantic=0.528
- `admin/countries/components/LogisticsProvidersTab.tsx` — generic×2; semantic=0.514
- `admin/countries/components/MapTab.tsx` — specific×1; generic×2; semantic=0.428
- `admin/countries/components/PaymentGatewaysTab.tsx` — specific×1; semantic=0.586
- `admin/countries/components/PayoutSettingsTab.tsx` — generic×2; semantic=0.596
- `admin/countries/components/PromotionsTab.tsx` — generic×2; semantic=0.473
- `admin/countries/components/StaffTab.tsx` — specific×2; generic×1; semantic=0.455
- `admin/countries/components/VersionsTab.tsx` — generic×3; semantic=0.494
- `admin/layout.tsx` — specific×1; generic×1; semantic=0.516
- `api/auth/login/route.ts` — generic×2; semantic=0.444
- `api/auth/logout/route.ts` — generic×2; semantic=0.440
- `api/auth/me/route.ts` — generic×2; semantic=0.438
- … +50 more

**Web Lib/Hooks (64):**
- `logo/LogoAnimation.tsx` — specific×1; semantic=0.451
- `HomeClient.tsx` — generic×2; semantic=0.428
- `admin/countries/CountryLedgerTable.tsx` — generic×5; semantic=0.457
- `admin/dashboard/_components/ExportsPanel.tsx` — specific×1; generic×6; semantic=0.482
- `admin/dashboard/_tabs/AnalyticsTab.tsx` — generic×3; semantic=0.525
- `admin/dashboard/_tabs/ApprovalMatrixTab.tsx` — generic×2; semantic=0.464
- `admin/dashboard/_tabs/BannerTab.tsx` — generic×2; semantic=0.454
- `admin/dashboard/_tabs/CouponsTab.tsx` — specific×1; generic×2; semantic=0.511
- `admin/dashboard/_tabs/FinanceTab.tsx` — specific×2; generic×2; semantic=0.559
- `admin/dashboard/_tabs/HierarchyTab.tsx` — specific×1; generic×1; semantic=0.459
- `admin/dashboard/_tabs/InsightsTab.tsx` — generic×2; semantic=0.496
- `admin/dashboard/_tabs/ModerationTab.tsx` — generic×3; semantic=0.451
- `admin/dashboard/_tabs/OrdersTab.tsx` — generic×2; semantic=0.552
- `admin/dashboard/_tabs/PayoutsTab.tsx` — specific×1; generic×3; semantic=0.539
- `admin/dashboard/_tabs/ProductsTab.tsx` — generic×3; semantic=0.455
- `admin/dashboard/_tabs/SupplierDocumentsTab.tsx` — generic×3; semantic=0.491
- `admin/dashboard/_tabs/TicketsTab.tsx` — generic×2; semantic=0.460
- `admin/disputes/_components/DisputesPanel.tsx` — generic×3; semantic=0.462
- `admin/employees/_components/employees-content.tsx` — specific×2; generic×2; semantic=0.460
- `admin/employees/_tabs/AlumniContractorTab.tsx` — generic×2; semantic=0.473
- … +44 more

**Web App Files (18):**
- `addressHelpers.ts` — specific×1; semantic=0.462
- `adminPermissions.ts` — specific×2; generic×3; semantic=0.483
- `api-core.ts` — generic×2; semantic=0.497
- `i18n.ts` — generic×5; semantic=0.506
- `notificationHelpers.ts` — specific×1; generic×1; semantic=0.464
- `notificationStore.ts` — generic×3; semantic=0.490
- `requestCache.ts` — generic×2; semantic=0.425
- `statusColors.ts` — generic×2; semantic=0.487
- `theme.ts` — specific×1; generic×1; semantic=0.459
- `ticketHelpers.ts` — generic×2; semantic=0.462
- `types.ts` — specific×1; generic×6; semantic=0.463
- `userRealtimeAlerts.ts` — generic×2; semantic=0.475
- `web_app/middleware.ts` — generic×3; semantic=0.463
- `admin/countries/constants.ts` — generic×3; semantic=0.461
- `admin/countries/types.ts` — specific×1; generic×4; semantic=0.550
- `supplier/batch-upload/types.ts` — generic×2; semantic=0.504
- `services/addressFormatService.ts` — generic×2; semantic=0.430
- `services/localizationService.ts` — generic×2; semantic=0.441

**Frontend Scripts (7):**
- `web_app/scripts/check_pages.py` — generic×2; semantic=0.430
- `web_app/scripts/extract_tabs.py` — generic×2; semantic=0.425
- `web_app/scripts/extract_tabs_v2.py` — specific×1; generic×2; semantic=0.444
- `web_app/scripts/final_fixes.py` — generic×4; semantic=0.441
- `web_app/scripts/fix_components.py` — generic×4; semantic=0.469
- `web_app/scripts/insert_dark_css.py` — specific×1; semantic=0.354
- `web_app/scripts/update_page_imports.py` — generic×4; semantic=0.446

**Mobile Screens (66):**
- `(auth)/login.tsx` — generic×5; semantic=0.428
- `(tabs)/orders/[id].tsx` — specific×2; generic×3; semantic=0.450
- `(tabs)/products/index.tsx` — generic×3; semantic=0.442
- `(tabs)/profile.tsx` — generic×4; semantic=0.400
- `_layout.tsx` — generic×3; semantic=0.442
- `admin/analytics.tsx` — specific×1; generic×1; semantic=0.489
- `admin/audit-logs.tsx` — specific×1; generic×2; semantic=0.507
- `admin/bank-accounts.tsx` — generic×5; semantic=0.588
- `admin/banners.tsx` — specific×1; generic×2; semantic=0.461
- `admin/barcode.tsx` — generic×3; semantic=0.476
- `admin/dashboard.tsx` — specific×2; generic×5; semantic=0.478
- `admin/email.tsx` — specific×1; generic×2; semantic=0.493
- `admin/exports.tsx` — specific×1; generic×4; semantic=0.485
- `admin/invoices.tsx` — specific×1; generic×2; semantic=0.540
- `admin/login.tsx` — generic×2; semantic=0.482
- `admin/logistics-partners.tsx` — specific×1; generic×4; semantic=0.523
- `admin/orders.tsx` — generic×2; semantic=0.500
- `admin/product-verification.tsx` — specific×1; generic×3; semantic=0.503
- `admin/products.tsx` — generic×2; semantic=0.493
- `admin/promotions.tsx` — specific×1; generic×1; semantic=0.482
- … +46 more

**Mobile Components (7):**
- `components/HeroBanner.tsx` — generic×2; semantic=0.451
- `components/HomeProductShowcase.tsx` — specific×1; semantic=0.448
- `components/MobileSeasonalBanner.tsx` — generic×2; semantic=0.447
- `components/Recommendations.tsx` — specific×1; semantic=0.434
- `components/ui/AppHeader.tsx` — generic×2; semantic=0.441
- `components/ui/StatCard.tsx` — generic×2; semantic=0.427
- `components/ui/StatusBadge.tsx` — generic×4; semantic=0.506

**Mobile Lib/Hooks (13):**
- `lib/adminManagementUtils.ts` — generic×2; semantic=0.499
- `lib/api.ts` — specific×3; generic×7; semantic=0.448
- `lib/authPrompt.tsx` — generic×2; semantic=0.442
- `lib/authStore.ts` — generic×3; semantic=0.459
- `lib/backgroundJobs.ts` — specific×1; generic×2; semantic=0.455
- `lib/fileSystem.ts` — specific×1; generic×1; semantic=0.460
- `lib/icons.ts` — generic×2; semantic=0.480
- `lib/invoiceService.ts` — generic×3; semantic=0.487
- `lib/logisticsPayoutInsights.ts` — specific×1; generic×3; semantic=0.573
- `lib/paymentService.ts` — generic×2; semantic=0.570
- `lib/themeStore.ts` — specific×1; semantic=0.409
- `lib/userRealtime.ts` — generic×2; semantic=0.426
- `theme/index.ts` — specific×2; generic×1; semantic=0.421

**Backend Tests (49):**
- `conftest.py` — specific×2; generic×7; semantic=0.549
- `playwright/e2e/auth.spec.ts` — generic×2; semantic=0.464
- `playwright/e2e/finance-automation.spec.ts` — specific×2; generic×5; semantic=0.570
- `test_admin.py` — specific×2; generic×2; semantic=0.458
- `test_ai_research_jobs.py` — generic×2; semantic=0.490
- `test_ai_research_router.py` — generic×2; semantic=0.478
- `test_api_endpoints.py` — generic×2; semantic=0.369
- `test_api_pagination.py` — generic×3; semantic=0.482
- `test_auth.py` — generic×3; semantic=0.442
- `test_auto_payout_sweep.py` — specific×3; generic×4; semantic=0.628
- `test_background_jobs.py` — generic×2; semantic=0.483
- `test_banners.py` — specific×1; generic×2; semantic=0.470
- `test_cart.py` — generic×2; semantic=0.487
- `test_categories.py` — specific×1; generic×2; semantic=0.467
- `test_chat.py` — specific×1; generic×1; semantic=0.447
- `test_communication_services.py` — generic×2; semantic=0.516
- `test_comprehensive_system.py` — specific×2; generic×5; semantic=0.520
- `test_controller_subpackages.py` — generic×4; semantic=0.497
- `test_countries.py` — generic×2; semantic=0.474
- `test_country_ai_research.py` — specific×1; generic×1; semantic=0.477
- … +29 more

**Web Tests (39):**
- `web_app/__tests__/browser.spec.ts` — generic×4; semantic=0.405
- `components/ApprovalActionModal.test.tsx` — specific×1; generic×2; semantic=0.440
- `components/CountryDetailWorkspace.test.tsx` — generic×2; semantic=0.456
- `components/CountryResearchPanel.test.tsx` — specific×1; generic×1; semantic=0.458
- `components/Footer.test.tsx` — generic×2; semantic=0.434
- `components/emailComponents.test.tsx` — specific×1; generic×2; semantic=0.439
- `lib/adminPermissions.test.ts` — specific×1; generic×2; semantic=0.444
- `lib/api.test.ts` — generic×2; semantic=0.390
- `lib/requestCache.test.ts` — specific×1; generic×2; semantic=0.393
- `lib/useApprovalCheck.test.tsx` — generic×3; semantic=0.423
- `lib/useAuth.preferences.test.tsx` — generic×2; semantic=0.381
- `pages/adminCommunicationHub.test.tsx` — specific×1; generic×2; semantic=0.411
- `pages/adminDashboardNavigation.test.tsx` — specific×1; generic×3; semantic=0.402
- `pages/adminExportsPanel.test.tsx` — generic×3; semantic=0.413
- `pages/adminFinanceCodVerification.test.tsx` — specific×3; generic×4; semantic=0.476
- `pages/adminLogisticsPages.test.tsx` — specific×1; generic×5; semantic=0.413
- `pages/adminManagementPages.test.tsx` — specific×1; generic×2; semantic=0.434
- `pages/adminPaymentsPage.test.tsx` — specific×2; generic×4; semantic=0.447
- `pages/adminStaffPage.test.tsx` — generic×3; semantic=0.447
- `pages/adminStandalonePages.test.tsx` — specific×3; generic×2; semantic=0.454
- … +19 more

**Mobile Tests (32):**
- `adminAnalyticsScreen.test.tsx` — generic×2; semantic=0.375
- `adminBankAccountsScreen.test.tsx` — generic×5; semantic=0.419
- `adminDashboardScreen.test.ts` — generic×2; semantic=0.477
- `adminGuardedScreens.test.tsx` — specific×2; generic×2; semantic=0.362
- `adminManagementUtils.test.ts` — specific×1; generic×2; semantic=0.450
- `adminMobileAudit.test.tsx` — specific×1; generic×3; semantic=0.367
- `backgroundJobStore.test.ts` — generic×2; semantic=0.432
- `backgroundJobs.test.ts` — specific×1; generic×1; semantic=0.412
- `checkoutScreen.test.tsx` — specific×1; generic×2; semantic=0.404
- `customerAccountScreens.test.tsx` — generic×2; semantic=0.407
- `flashSalesScreen.test.ts` — specific×1; generic×2; semantic=0.460
- `loginScreen.test.ts` — generic×3; semantic=0.485
- `loginScreenRouting.test.tsx` — generic×3; semantic=0.389
- `logisticsPartnerApi.test.ts` — generic×3; semantic=0.498
- `logisticsPartnerProfileScreen.test.tsx` — specific×1; generic×4; semantic=0.413
- `logisticsPartnerScanScreen.test.tsx` — generic×3; semantic=0.413
- `logisticsPayoutInsights.test.ts` — generic×3; semantic=0.517
- `logisticsScreen.test.ts` — generic×3; semantic=0.486
- `logisticsShipmentsScreen.test.tsx` — generic×3; semantic=0.441
- `mobileApiRouteHelpers.test.ts` — generic×5; semantic=0.428
- … +12 more

**E2E Tests (52):**
- `web_app/e2e/admin-audit-fixes.spec.ts` — generic×2; semantic=0.477
- `web_app/e2e/admin-commission.spec.ts` — specific×1; generic×3; semantic=0.501
- `web_app/e2e/admin-communication-hub.spec.ts` — generic×2; semantic=0.495
- `web_app/e2e/admin-country-control-plane.spec.ts` — generic×4; semantic=0.445
- `web_app/e2e/admin-country-enhanced.spec.ts` — generic×4; semantic=0.456
- `web_app/e2e/admin-data-ops.spec.ts` — specific×1; generic×2; semantic=0.473
- `web_app/e2e/admin-hr-permissions.spec.ts` — specific×1; generic×2; semantic=0.481
- `web_app/e2e/admin-logistics-pricing-insights-live.spec.ts` — generic×3; semantic=0.493
- `web_app/e2e/admin-logistics-workspace.spec.ts` — generic×5; semantic=0.485
- `web_app/e2e/admin-modules-reconciliation.spec.ts` — specific×2; generic×2; semantic=0.542
- `web_app/e2e/admin-payment-gateways.spec.ts` — specific×2; generic×3; semantic=0.516
- `web_app/e2e/admin-supplier-logistics-sanity.spec.ts` — generic×5; semantic=0.497
- `web_app/e2e/admin-treasury-payout.spec.ts` — specific×4; generic×4; semantic=0.653
- `web_app/e2e/amendment-verify.spec.ts` — generic×3; semantic=0.449
- `web_app/e2e/auth-registration-login.spec.ts` — generic×5; semantic=0.510
- `web_app/e2e/auth-role-login.spec.ts` — generic×3; semantic=0.507
- `web_app/e2e/collapse-poll.spec.ts` — generic×3; semantic=0.448
- `web_app/e2e/command-center.spec.ts` — specific×1; generic×2; semantic=0.462
- `web_app/e2e/comprehensive-test.spec.ts` — specific×1; generic×4; semantic=0.408
- `web_app/e2e/consistency-audit.spec.ts` — generic×3; semantic=0.498
- … +32 more

**Migrations (8):**
- `alembic/versions/2026_07_27_09_08-20260727_0908_add_check_constraints_to_status_enum_columns.py` — generic×4; semantic=0.501
- `alembic/versions/2026_07_28_0000_employee_hr_tables.py` — specific×2; generic×3; semantic=0.510
- `alembic/versions/2026_07_28_19_30-e8efae30fc29_add_missing_indexes_and_constraints.py` — specific×2; generic×6; semantic=0.492
- `alembic/versions/2026_07_29_10_28-9ff24a0683dd_schema_drift_check.py` — generic×2; semantic=0.524
- `alembic/versions/2026_07_30_0003-20260730_0003_create_upload_jobs_table.py` — generic×3; semantic=0.528
- `alembic/versions/2026_07_30_0005-20260730_0005_bounded_context_schema_migration.py` — specific×5; generic×6; semantic=0.525
- `alembic/versions/2026_08_06_0001_add_analytics_audit_columns.py` — specific×1; generic×2; semantic=0.542
- `alembic/versions/2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py` — specific×5; generic×7; semantic=0.526

**Backend Scripts (2):**
- `seed_all.py` — specific×3; generic×7; semantic=0.538
- `fix_chat.py` — specific×1; semantic=0.416

**Backend Other (8):**
- `transaction.py` — specific×1; semantic=0.673
- `dependencies/country_rls.py` — generic×4; semantic=0.490
- `events/event_publisher.py` — specific×1; semantic=0.468
- `lifespan.py` — specific×2; generic×3; semantic=0.535
- `settings/notification_worker.py` — generic×2; semantic=0.450
- `tasks/background_tasks.py` — specific×1; generic×2; semantic=0.525
- `tools/mcp/mcp_server.py` — specific×1; generic×4; semantic=0.559
- `zozi_mcp/zozi_mcp.py` — generic×3; semantic=0.644

---

### SYS_007 — Order Tracker & Order Management  (62.0%)

**Checkpoints:** 8 tables · 1 routes · 21 statuses · 13 fields · 50 capabilities · 9 steps · 43 search terms
**Matched files:** 1704 / 1841 (92.6%)

**Completion Breakdown:**

| Component | Score | Weight |
|---|---|---|
| 🗄️ DB tables | 62.5% | 20% |
| 🔌 API routes | 100.0% | 15% |
| 🚦 Status machine | 81.0% | 15% |
| 💪 Capabilities | 78.0% | 10% |
| 🖥️ Panel sections | 77.0% | 20% |
| 🧪 Tests | 100.0% | 10% |
| 🧱 Steps | 91.3% | 10% |
| Dead-file penalty (313 unwired) | -20.0% | — |
| **Overall** | **62.0%** | 100% |

**🗄️ Database tables (62.5%):**

- ✅ `media_assets` — `alembic/versions/2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py`
- ❌ `order_status_rules`
- ✅ `outbox_events` — `alembic/versions/2026_07_30_0004-20260730_0004_create_event_tables.py`, `alembic/versions/2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py`
- ❌ `packages` (commerce)
- ❌ `proof_of_delivery` (logistics)
- ✅ `return_requests` — `alembic/versions/2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py`
- ✅ `shipment_events` — `alembic/versions/2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py`
- ✅ `shipments` (logistics) — `alembic/versions/2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py`, `logistics.py`

**🔌 API routes (100.0%):**

- ✅ `ANY /orders/{id}/label` — `supplier.py`

**🚦 Status machine (81.0%):** 17/21 present

- ❌ Missing: `RETURNED_TO_SUPPLIER`, `RETURN_APPROVED`, `RETURN_IN_TRANSIT`, `RETURN_REQUESTED`
- ✅ Present: `CANCELLED`, `DELAYED`, `DELIVERED`, `DISTRIBUTION_CHECKPOINT`, `FAILED`, `LOGISTIC_RECEIVED`, `PENDING`, `PICKED`, `PICKING_UP`, `PREPARED`, `PROCESSING`, `RESCHEDULED`, `SHIPMENT_CANCELLED`, `SHIPMENT_DELAYED`, `SHIPMENT_FAILED`, `SHIPMENT_RESCHEDULED`, `SHIPMENT_RETURNED`

**💪 Capabilities (78.0%):**

- ❌ constitution-compliant
- ❌ no silent/hardcoded fallbacks
- ✅ One order, one identity: — `auth_controller.py`
- ✅ Single source of truth for status: — `admin/database.py` 🦙✓
- ❌ No hardcoded fallbacks:
- ✅ Universal visibility: — `supplier/bulk/components/ProductDraftCard.tsx` 🦙✗
- ✅ Customer, Supplier, Logistic Partner, Admin — `alembic/versions/2026_07_27_09_08-20260727_0908_add_check_constraints_to_status_enum_columns.py` 🦙✓
- ❌ Proof at every handover:
- ✅ Admin is the referee: — `alembic/versions/2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py` 🦙✗
- ✅ uploads photo of the packed parcel — `supplier_controller.py` 🦙✗
- ❌ flashes on ALL logistic partner pages
- ✅ removed from every other logistic partner's page — `admin/users.py` 🦙✗
- ✅ may cancel the pick-up — `alembic/versions/2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py` 🦙✗
- ✅ PICKED FROM SUPPLIER — `alembic/versions/2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py` 🦙✗
- ✅ scans the parcel QR — `supplier_orders.py` 🦙✗
- ✅ Transit (logistic-only sub-statuses, allowed only between `PICKED` and `DELIVERED`): — `invoice_controller.py` 🦙✗
- ✅ return parcel to supplier — `alembic/versions/2026_07_30_0005-20260730_0005_bounded_context_schema_migration.py` 🦙✗
- ✅ Post-delivery: — `alembic/versions/2026_07_28_21_14-87146598d2c3_add_missing_fk_constraints_for_.py` 🦙✓
- ✅ Logistic partner: — `alembic/versions/2026_07_27_09_08-20260727_0908_add_check_constraints_to_status_enum_columns.py` 🦙✓
- ✅ override/correct any status — `payments_controller.py` 🦙✗
- ✅ cancel any order — `alembic/versions/2026_07_27_09_08-20260727_0908_add_check_constraints_to_status_enum_columns.py` 🦙✓
- ✅ configuration.order_status_rules — `alembic/versions/2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py` 🦙✗
- ✅ Supplier packages by default — `order_tracking_service.py` 🦙✗
- ✅ Packaging Manager — `alembic/versions/2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py` 🦙✓
- ✅ "Print Parcel Sheet" button on the Supplier order page — `supplier/guide.tsx` 🦙✗
- ✅ + Latitude/Longitude — `alembic/versions/2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py` 🦙✗
- ✅ COD amount to collect — `alembic/versions/2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py` 🦙✗
- ✅ first-class endpoint — `admin/orders.py` 🦙✗
- ✅ reverse shipment — `alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py` 🦙✓
- ✅ ledger service — `alembic/versions/2026_07_28_19_30-e8efae30fc29_add_missing_indexes_and_constraints.py` 🦙✓
- ❌ flashing pick-up board
- ✅ monthly range-partitioned — `alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py` 🦙✓
- ✅ media bytes in R2 — `alembic/versions/2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py` 🦙✗
- ❌ Reconciliation engine (restored, country-aware):
- ❌ Logistic remits → ZOZI Treasury → Supplier payout (− commission)
- ✅ Treasury → Supplier payout (− commission) — `alembic/versions/2026_07_30_0005-20260730_0005_bounded_context_schema_migration.py` 🦙✗
- ✅ Treasury → Logistic delivery fee — `alembic/versions/2026_07_30_0005-20260730_0005_bounded_context_schema_migration.py` 🦙✗
- ✅ Location service: — `alembic/versions/2026_07_28_19_30-e8efae30fc29_add_missing_indexes_and_constraints.py` 🦙✓
- ❌ Admin ecosystem wiring:
- ✅ E2E test matrix: — `alembic/versions/2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py` 🦙✗
- ✅ Step 1 — Schema & state machine. — `finance.py` 🦙✗
- ✅ Step 2 — Placement, location & QR. — `(tabs)/orders/[id].tsx` 🦙✓
- ✅ Step 3 — Supplier workflow. — `disputes_controller.py` 🦙✗
- ✅ Print Parcel Sheet — `logistics-partner/scan.tsx` 🦙✗
- ❌ Step 4 — Logistic claim & handover.
- ✅ Step 5 — Transit & exceptions. — `utils/circuit_breaker.py` 🦙✓
- ✅ Step 6 — Delivery proof. — `supplier_controller.py` 🦙✗
- ❌ Step 7 — Returns/replacements & money.
- ✅ Step 8 — Admin controls & panels. — `web_app/e2e/verify-all-panels.spec.ts` 🦙✗
- ✅ Step 9 — E2E test & close-out. — `alembic/versions/2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py` 🦙✗

**🧱 Steps (91.3%):**

| Step | Title | Done when | Score |
|---|---|---|---|
| 1 | Schema & state machine | illegal transition rejected in test; drift gate green. | 🟡 **71.4%** |
| 2 | Placement, location & QR | label renders with QR + COD amount; scan token resolves server-side with role/status checks. | ✅ **100.0%** |
| 3 | Supplier workflow | photo missing blocks `PREPARED` with explicit error. | ✅ **100.0%** |
| 4 | Logistic claim & handover | visibility assertions pass. | ✅ **100.0%** |
| 5 | Transit & exceptions | each exception path leaves a full audited trail. | ✅ **100.0%** |
| 6 | Delivery proof | both paths produce POD record. | 🟡 **50.0%** |
| 7 | Returns/replacements & money | COD run reconciles Order→Logistic→Treasury→Supplier with zero variance. | ✅ **100.0%** |
| 8 | Admin controls & panels | parity check web vs mobile passes. | ✅ **100.0%** |
| 9 | E2E test & close-out | every row green and matrix committed. | ✅ **100.0%** |

**🖥️ Panel sections (77.0%):**

- **§II** — 73.3% (terms 46.5%, web ✅, mobile ✅) — Customer: place order (COD/Card) with GPS capture; My Orders live timeline; cancel early; confirm delivery request; e-signature; reject at door; request return/
- **§III** — 74.4% (terms 48.8%, web ✅, mobile ✅) — Supplier: new-order queue + alerts; accept to PROCESSING; pack with tamper seal + QR label + weight/dims; print parcel sheet; upload packed photo to reach PREPA
- **§IV** — 81.4% (terms 62.8%, web ✅, mobile ✅) — Logistic partner: flashing pick-up board of PREPARED orders; claim pick-up; cancel claim; QR-scan handover; transit sub-statuses with GPS; delayed/rescheduled/f
- **§V** — 79.1% (terms 58.1%, web ✅, mobile ✅) — Admin: full visibility of all orders; override/correct any status with mandatory reason + audit; cancel wrong orders; resolve disputes; approve returns; monitor

**🧪 Tests (100.0%):**

- ✅ Backend: 4 file(s) — `conftest.py`, `test_comprehensive_system.py`, `test_country_research.py`
- ✅ Web: 6 file(s) — `orderHelpers.test.ts`, `__tests__/orderHelpers.test.ts`, `pages/adminLogisticsPages.test.tsx`
- ✅ Mobile: 8 file(s) — `checkoutScreen.test.tsx`, `logisticsPartnerApi.test.ts`, `logisticsPartnerScanScreen.test.tsx`
- ✅ E2E: 3 file(s) — `web_app/e2e/admin-supplier-logistics-sanity.spec.ts`, `web_app/e2e/fulfillment-role-flow.spec.ts`, `web_app/e2e/supplier-smoke.spec.ts`

**⛔ Gap summary (what to build next):**

- **Tables:** `order_status_rules`, `packages`, `proof_of_delivery`
- **Statuses:** `RETURNED_TO_SUPPLIER`, `RETURN_APPROVED`, `RETURN_IN_TRANSIT`, `RETURN_REQUESTED`
- **Capabilities:** `constitution-compliant`, `no silent/hardcoded fallbacks`, `No hardcoded fallbacks:`, `Proof at every handover:`, `flashes on ALL logistic partner pages`, `flashing pick-up board`, `Reconciliation engine (restored, country-aware):`, `Logistic remits → ZOZI Treasury → Supplier payout (− commission)`, `Admin ecosystem wiring:`, `Step 4 — Logistic claim & handover.`, `Step 7 — Returns/replacements & money.`
- **Fields:** `media_ref`, `order_uuid`, `original_order_uuid`, `packed_photo_media_id`, `proof_of_delivery`, `qr_token_hash`, `signature_media_id`, `tamper_seal_id`

**📁 Files by Layer (top entries):**

**Backend Routers (143):**
- `_permission_primitives.py` — generic×5; semantic=0.562
- `accounting.py` — specific×2; generic×18; semantic=0.607
- `addresses.py` — specific×1; generic×16; semantic=0.597
- `admin.py` — specific×4; generic×37; semantic=0.679
- `admin_banners.py` — specific×1; generic×11; semantic=0.572
- `admin_cash.py` — specific×2; generic×11; semantic=0.595
- `admin_categories.py` — specific×2; generic×15; semantic=0.599
- `admin_chat.py` — specific×1; generic×12; semantic=0.603
- `admin_commission.py` — specific×2; generic×14; semantic=0.594
- `admin_email.py` — specific×2; generic×17; semantic=0.604
- `admin_fallback.py` — specific×3; generic×23; semantic=0.627
- `admin_logistics.py` — specific×1; generic×13; semantic=0.636
- `admin_orders.py` — specific×2; generic×16; semantic=0.703
- `admin_payouts.py` — specific×2; generic×26; semantic=0.607
- `admin_products.py` — specific×1; generic×13; semantic=0.632
- `admin_promotions.py` — specific×2; generic×18; semantic=0.603
- `admin_settings.py` — generic×4; semantic=0.549
- `admin_suppliers.py` — specific×2; generic×21; semantic=0.649
- `admin_treasury.py` — specific×4; generic×30; semantic=0.602
- `admin_users.py` — specific×2; generic×16; semantic=0.580
- … +123 more

**Backend Controllers (62):**
- `accounting_controller.py` — specific×1; generic×8; semantic=0.573
- `admin/admin_auth.py` — specific×1; generic×9; semantic=0.499
- `admin/analytics.py` — specific×1; generic×21; semantic=0.579
- `admin/bulk_ops.py` — specific×1; generic×16; semantic=0.611
- `admin/coupons.py` — specific×2; generic×15; semantic=0.589
- `admin/misc.py` — specific×1; generic×17; semantic=0.557
- `admin/orders.py` — specific×7; generic×33; semantic=0.710
- `admin/payouts.py` — specific×3; generic×18; semantic=0.603
- `admin/permissions.py` — specific×2; generic×12; semantic=0.557
- `admin/products.py` — specific×3; generic×24; semantic=0.624
- `admin/suppliers.py` — specific×3; generic×25; semantic=0.638
- `admin/tickets.py` — specific×2; generic×17; semantic=0.572
- `admin/users.py` — specific×3; generic×37; semantic=0.629
- `ai_controller.py` — generic×12; semantic=0.565
- `auth_controller.py` — specific×3; generic×38; semantic=0.587
- `banner_controller.py` — specific×4; generic×24; semantic=0.569
- `cart_controller.py` — specific×2; generic×21; semantic=0.627
- `cash_management_controller.py` — specific×3; generic×30; semantic=0.651
- `catalog/category_admin_controller.py` — specific×1; generic×3; semantic=0.547
- `chatbot_controller.py` — specific×1; generic×29; semantic=0.604
- … +42 more

**Backend Services (262):**
- `location_service.py` — generic×3; semantic=0.578
- `_registry.py` — specific×3; generic×25; semantic=0.585
- `admin_analytics_service.py` — generic×7; semantic=0.536
- `advanced_filter_service.py` — specific×1; generic×12; semantic=0.553
- `advanced_search_engine.py` — specific×1; generic×9; semantic=0.585
- `ai/automation_read_service.py` — specific×2; generic×8; semantic=0.570
- `ai_automation_service.py` — specific×2; generic×23; semantic=0.556
- `ai_copy_jobs.py` — generic×13; semantic=0.557
- `ai_research_jobs.py` — specific×2; generic×7; semantic=0.513
- `ai_search_service.py` — specific×1; generic×7; semantic=0.588
- `ai_service.py` — specific×1; generic×24; semantic=0.557
- `ai_variant_config.py` — specific×1; generic×26; semantic=0.644
- `approval_matrix_service.py` — specific×1; generic×10; semantic=0.572
- `asset_tracking.py` — specific×1; generic×10; semantic=0.599
- `attendance_service.py` — generic×6; semantic=0.604
- `audit/audit_trail_service.py` — specific×1; generic×11; semantic=0.582
- `audit/worm_audit.py` — specific×1; generic×9; semantic=0.600
- `audit_service.py` — specific×1; generic×6; semantic=0.570
- `auth_service.py` — specific×1; generic×21; semantic=0.589
- `auth_write_service.py` — specific×1; generic×19; semantic=0.577
- … +242 more

**Backend Models (27):**
- `__init__.py` — specific×2; generic×33; semantic=0.592
- `admin.py` — specific×4; generic×35; semantic=0.601
- `ai_upload.py` — specific×2; generic×16; semantic=0.621
- `commission.py` — specific×2; generic×14; semantic=0.597
- `comms/communication.py` — specific×3; generic×19; semantic=0.589
- `comms/core.py` — specific×1; generic×25; semantic=0.587
- `comms/marketing.py` — specific×2; generic×18; semantic=0.608
- `comms/suppliers.py` — specific×2; generic×20; semantic=0.638
- `country_control.py` — specific×4; generic×18; semantic=0.611
- `employee_models.py` — specific×1; generic×19; semantic=0.581
- `finance.py` — specific×7; generic×33; semantic=0.578
- `fraud.py` — specific×2; generic×24; semantic=0.590
- `geography/countries.py` — specific×1; generic×16; semantic=0.580
- `geography/country_basics.py` — generic×8; semantic=0.578
- `geography/country_economics.py` — specific×1; generic×11; semantic=0.576
- `geography/country_enhancements.py` — specific×2; generic×18; semantic=0.563
- `geography/country_legal.py` — specific×1; generic×8; semantic=0.598
- `geography/country_tax.py` — specific×1; generic×7; semantic=0.543
- `incident.py` — generic×8; semantic=0.581
- `logistics.py` — specific×6; generic×30; semantic=0.637
- … +7 more

**Backend Schemas (Pydantic) (3):**
- `schemas.py` — specific×6; generic×46; semantic=0.624
- `schemas.py` — specific×1; generic×23; semantic=0.548
- `utils/schema_audit.py` — specific×1; generic×16; semantic=0.569

**Backend Middleware (22):**
- `middleware/__init__.py` — generic×3; semantic=0.590
- `middleware/api_version_middleware.py` — generic×3; semantic=0.533
- `middleware/behavioral_analytics.py` — generic×10; semantic=0.576
- `middleware/coi_middleware.py` — specific×1; generic×9; semantic=0.579
- `middleware/country_context.py` — specific×1; generic×18; semantic=0.607
- `middleware/csrf_middleware.py` — generic×12; semantic=0.552
- `middleware/database_security.py` — specific×1; generic×15; semantic=0.580
- `middleware/device_binding_middleware.py` — generic×5; semantic=0.525
- `middleware/impossible_travel_middleware.py` — specific×1; generic×18; semantic=0.536
- `middleware/ip_extraction_middleware.py` — generic×2; semantic=0.493
- `middleware/logging_middleware.py` — specific×1; generic×9; semantic=0.596
- `middleware/orchestrator.py` — specific×1; generic×17; semantic=0.634
- `middleware/pci_dss_compliance.py` — generic×19; semantic=0.621
- `middleware/rate_limit_middleware.py` — specific×1; generic×17; semantic=0.542
- `middleware/request_id_middleware.py` — generic×3; semantic=0.596
- `middleware/rls_dependency.py` — specific×2; generic×11; semantic=0.575
- `middleware/security_headers.py` — generic×14; semantic=0.618
- `middleware/siem_engine.py` — specific×2; generic×11; semantic=0.650
- `middleware/webhook_ip_whitelist.py` — generic×10; semantic=0.540
- `middleware/webhook_verification.py` — generic×13; semantic=0.519
- … +2 more

**Backend Utils (57):**
- `write_helpers.py` — generic×3; semantic=0.539
- `utils/analytics_service.py` — specific×2; generic×12; semantic=0.641
- `utils/api_docs.py` — specific×1; generic×10; semantic=0.602
- `utils/audit.py` — generic×10; semantic=0.591
- `utils/auth.py` — generic×14; semantic=0.544
- `utils/background_jobs.py` — specific×2; generic×19; semantic=0.540
- `utils/backup.py` — generic×16; semantic=0.535
- `utils/cache.py` — generic×5; semantic=0.532
- `utils/category_tree.py` — generic×5; semantic=0.516
- `utils/circuit_breaker.py` — generic×10; semantic=0.601
- `utils/config.py` — generic×19; semantic=0.539
- `utils/constant_time.py` — generic×5; semantic=0.528
- `utils/constants.py` — specific×5; generic×24; semantic=0.614
- `utils/country_rls.py` — specific×1; generic×12; semantic=0.577
- `utils/currency.py` — generic×12; semantic=0.535
- `utils/db_backup.py` — generic×4; semantic=0.556
- `utils/dependencies.py` — generic×9; semantic=0.523
- `utils/email_service.py` — specific×1; generic×22; semantic=0.682
- `utils/encryption.py` — generic×4; semantic=0.540
- `utils/entity_messaging.py` — specific×2; generic×14; semantic=0.586
- … +37 more

**Backend Providers (35):**
- `providers/__init__.py` — generic×6; semantic=0.565
- `providers/_base.py` — generic×4; semantic=0.558
- `providers/ai/__init__.py` — generic×2; semantic=0.538
- `providers/analytics.py` — specific×2; generic×12; semantic=0.595
- `providers/async_workers.py` — specific×2; generic×18; semantic=0.558
- `providers/bg_remover.py` — specific×3; generic×24; semantic=0.502
- `providers/chatbot.py` — specific×1; generic×14; semantic=0.550
- `providers/config.py` — generic×6; semantic=0.577
- `providers/country.py` — specific×1; generic×7; semantic=0.573
- `providers/finance_ai.py` — generic×10; semantic=0.574
- `providers/geo.py` — specific×1; generic×14; semantic=0.550
- `providers/geography/country.py` — specific×1; generic×7; semantic=0.562
- `providers/geography/geo.py` — specific×1; generic×13; semantic=0.543
- `providers/hr/br_05.py` — specific×1; generic×13; semantic=0.550
- `providers/hr/br_06.py` — specific×1; generic×14; semantic=0.556
- `providers/hr/br_08.py` — specific×1; generic×15; semantic=0.571
- `providers/hr/br_11.py` — specific×2; generic×12; semantic=0.551
- `providers/hr/br_12.py` — specific×2; generic×13; semantic=0.611
- `providers/hr/br_13.py` — specific×2; generic×14; semantic=0.573
- `providers/image.py` — specific×2; generic×13; semantic=0.538
- … +15 more

**Backend Core (14):**
- `admin/__init__.py` — specific×1; generic×7; semantic=0.604
- `admin/database.py` — specific×1; generic×16; semantic=0.583
- `supplier/__init__.py` — generic×3; semantic=0.590
- `data/__init__.py` — generic×4; semantic=0.547
- `database.py` — generic×3; semantic=0.526
- `database.py` — generic×18; semantic=0.553
- `init_db.py` — generic×6; semantic=0.555
- `events/__init__.py` — generic×3; semantic=0.631
- `main.py` — specific×4; generic×36; semantic=0.679
- `_exports.py` — specific×1; generic×13; semantic=0.515
- `finance/events/__init__.py` — generic×3; semantic=0.597
- `hr/__init__.py` — generic×2; semantic=0.539
- `location_service/__init__.py` — generic×3; semantic=0.525
- `orders/__init__.py` — specific×1; generic×8; semantic=0.672

**Backend Data/Seed (14):**
- `data/category_tax_profiles.py` — specific×1; generic×9; semantic=0.521
- `data/commerce_read.py` — specific×1; generic×6; semantic=0.616
- `data/comms_read.py` — specific×1; generic×4; semantic=0.577
- `data/country_curated.py` — generic×5; semantic=0.540
- `data/curated_cities.py` — specific×1; generic×5; semantic=0.495
- `data/geography_read.py` — specific×2; generic×9; semantic=0.587
- `data/ledger_facade.py` — specific×2; generic×5; semantic=0.568
- `data/ledger_impl_bridge.py` — generic×5; semantic=0.507
- `data/logistics_pricing_facade.py` — specific×1; generic×3; semantic=0.613
- `data/models_communication.py` — generic×2; semantic=0.492
- `data/orm_models.py` — generic×4; semantic=0.564
- `data/vat_rates.py` — specific×3; generic×6; semantic=0.552
- `seed.py` — specific×5; generic×35; semantic=0.601
- `treasury_seeder.py` — specific×2; generic×12; semantic=0.587

**Web Pages (129):**
- `web_app/admin/accounting/page.tsx` — generic×7; semantic=0.519
- `web_app/admin/audit-logs/page.tsx` — specific×1; generic×20; semantic=0.584
- `web_app/admin/bank-accounts/page.tsx` — generic×2; semantic=0.522
- `web_app/admin/banners/page.tsx` — generic×2; semantic=0.516
- `web_app/admin/barcode/page.tsx` — specific×3; generic×30; semantic=0.580
- `web_app/admin/categories/page.tsx` — specific×1; generic×19; semantic=0.552
- `web_app/admin/chat/page.tsx` — generic×4; semantic=0.525
- `web_app/admin/command-center/alerts/page.tsx` — specific×2; generic×17; semantic=0.534
- `web_app/admin/command-center/fraud/page.tsx` — generic×5; semantic=0.535
- `web_app/admin/command-center/headlines/create/page.tsx` — specific×2; generic×18; semantic=0.525
- `web_app/admin/command-center/headlines/page.tsx` — specific×2; generic×18; semantic=0.536
- `web_app/admin/command-center/page.tsx` — specific×3; generic×34; semantic=0.578
- `web_app/admin/commission/page.tsx` — specific×3; generic×25; semantic=0.545
- `web_app/admin/communication/page.tsx` — generic×9; semantic=0.488
- `web_app/admin/countries/[code]/staff/page.tsx` — specific×2; generic×23; semantic=0.553
- `web_app/admin/countries/page.tsx` — specific×4; generic×30; semantic=0.564
- `web_app/admin/coupons/page.tsx` — generic×2; semantic=0.555
- `web_app/admin/dashboard/page.tsx` — specific×1; generic×23; semantic=0.544
- `web_app/admin/disputes/page.tsx` — generic×2; semantic=0.553
- `web_app/admin/email/page.tsx` — specific×1; generic×3; semantic=0.544
- … +109 more

**Web Components (234):**
- `components/EnterpriseDataTable.tsx` — specific×1; generic×16; semantic=0.551
- `components/ProductCard.ts` — generic×5; semantic=0.540
- `components/logo/Logo.web.tsx` — generic×3; semantic=0.504
- `components/logo/LogoAnimation.tsx` — generic×6; semantic=0.483
- `components/logo/ZoziLogo.tsx` — generic×6; semantic=0.529
- `components/logo/logoArt.ts` — specific×1; generic×4; semantic=0.506
- `components/ui/Button.tsx` — generic×2; semantic=0.476
- `components/ui/Button.web.tsx` — specific×1; generic×8; semantic=0.452
- `components/ui/ErrorAlert.web.tsx` — specific×1; generic×4; semantic=0.485
- `components/ui/ErrorBoundary.tsx` — specific×1; generic×7; semantic=0.516
- `components/ui/GlassCard.web.tsx` — specific×1; generic×3; semantic=0.481
- `components/ui/Input.web.tsx` — specific×1; generic×9; semantic=0.472
- `components/ui/LoadingSkeleton.web.tsx` — specific×1; generic×7; semantic=0.449
- `components/ui/QuickFilters.tsx` — generic×2; semantic=0.524
- `components/ui/SearchBar.web.tsx` — specific×1; generic×3; semantic=0.485
- `components/ui/SupplierBadge.web.tsx` — specific×1; generic×6; semantic=0.567
- `components/ui/ThemeToggle.web.tsx` — specific×1; generic×4; semantic=0.418
- `components/ui/TranslatedText.web.tsx` — generic×3; semantic=0.488
- `components/ui/index.ts` — generic×4; semantic=0.494
- `logo/Logo.web.tsx` — generic×3; semantic=0.508
- … +214 more

**Web Lib/Hooks (115):**
- `logo/LogoAnimation.tsx` — generic×6; semantic=0.498
- `logo/ZoziLogo.tsx` — generic×6; semantic=0.555
- `HomeClient.tsx` — specific×2; generic×16; semantic=0.554
- `admin/countries/CountryLedgerTable.tsx` — specific×1; generic×23; semantic=0.555
- `admin/dashboard/_components/ExportsPanel.tsx` — specific×2; generic×39; semantic=0.567
- `admin/dashboard/_tabs/AnalyticsTab.tsx` — specific×4; generic×19; semantic=0.566
- `admin/dashboard/_tabs/ApprovalMatrixTab.tsx` — specific×1; generic×21; semantic=0.567
- `admin/dashboard/_tabs/BannerTab.tsx` — specific×2; generic×20; semantic=0.515
- `admin/dashboard/_tabs/CouponsTab.tsx` — specific×2; generic×21; semantic=0.560
- `admin/dashboard/_tabs/FinanceTab.tsx` — specific×2; generic×16; semantic=0.527
- `admin/dashboard/_tabs/HierarchyTab.tsx` — specific×2; generic×18; semantic=0.537
- `admin/dashboard/_tabs/InsightsTab.tsx` — specific×1; generic×14; semantic=0.563
- `admin/dashboard/_tabs/ModerationTab.tsx` — specific×1; generic×24; semantic=0.556
- `admin/dashboard/_tabs/OrdersTab.tsx` — specific×4; generic×15; semantic=0.659
- `admin/dashboard/_tabs/PayoutsTab.tsx` — specific×2; generic×30; semantic=0.549
- `admin/dashboard/_tabs/ProductsTab.tsx` — specific×1; generic×24; semantic=0.562
- `admin/dashboard/_tabs/SupplierDocumentsTab.tsx` — specific×1; generic×15; semantic=0.630
- `admin/dashboard/_tabs/TicketsTab.tsx` — specific×1; generic×21; semantic=0.552
- `admin/disputes/_components/DisputesPanel.tsx` — specific×1; generic×21; semantic=0.533
- `admin/employees/_components/employees-content.tsx` — specific×3; generic×34; semantic=0.538
- … +95 more

**Web App Files (49):**
- `shared/jest.setup.ts` — generic×3; semantic=0.459
- `addressHelpers.ts` — specific×1; generic×6; semantic=0.543
- `adminListUtils.ts` — generic×4; semantic=0.543
- `adminPermissions.ts` — specific×2; generic×16; semantic=0.558
- `api-core.ts` — generic×8; semantic=0.586
- `cartHelpers.ts` — specific×1; generic×3; semantic=0.546
- `chatbot.ts` — specific×1; generic×8; semantic=0.560
- `checkoutHelpers.ts` — specific×1; generic×13; semantic=0.636
- `errorLogging.ts` — generic×4; semantic=0.570
- `i18n.ts` — specific×4; generic×41; semantic=0.607
- `index.ts` — specific×1; generic×9; semantic=0.498
- `localization.ts` — generic×5; semantic=0.489
- `money.ts` — generic×5; semantic=0.487
- `notificationHelpers.ts` — specific×1; generic×12; semantic=0.573
- `notificationStore.ts` — generic×12; semantic=0.582
- `orderHelpers.ts` — specific×5; generic×13; semantic=0.618
- `productCardModel.ts` — generic×5; semantic=0.548
- `productHelpers.ts` — generic×2; semantic=0.522
- `productQuery.ts` — specific×1; generic×5; semantic=0.569
- `realtime.ts` — generic×7; semantic=0.505
- … +29 more

**Frontend Scripts (7):**
- `web_app/scripts/check_pages.py` — specific×1; generic×9; semantic=0.520
- `web_app/scripts/extract_tabs.py` — generic×11; semantic=0.477
- `web_app/scripts/extract_tabs_v2.py` — generic×13; semantic=0.495
- `web_app/scripts/final_fixes.py` — specific×2; generic×19; semantic=0.493
- `web_app/scripts/fix_components.py` — specific×2; generic×21; semantic=0.525
- `web_app/scripts/insert_dark_css.py` — specific×1; generic×3; semantic=0.394
- `web_app/scripts/update_page_imports.py` — specific×2; generic×18; semantic=0.524

**Mobile Screens (107):**
- `(auth)/forgot-password.tsx` — specific×1; generic×12; semantic=0.484
- `(auth)/login.tsx` — specific×2; generic×22; semantic=0.487
- `(auth)/register.tsx` — specific×2; generic×22; semantic=0.454
- `(auth)/reset-password.tsx` — specific×1; generic×12; semantic=0.480
- `(auth)/verify-email.tsx` — generic×13; semantic=0.512
- `(tabs)/_layout.tsx` — specific×1; generic×16; semantic=0.498
- `(tabs)/cart.tsx` — specific×1; generic×17; semantic=0.516
- `(tabs)/orders/[id].tsx` — specific×5; generic×33; semantic=0.609
- `(tabs)/orders/index.tsx` — specific×1; generic×2; semantic=0.593
- `(tabs)/products/[id].tsx` — specific×2; generic×24; semantic=0.558
- `(tabs)/products/index.tsx` — specific×1; generic×23; semantic=0.565
- `(tabs)/profile.tsx` — specific×4; generic×40; semantic=0.473
- `_layout.tsx` — specific×1; generic×24; semantic=0.548
- `admin/analytics.tsx` — specific×1; generic×15; semantic=0.601
- `admin/audit-logs.tsx` — specific×2; generic×18; semantic=0.609
- `admin/bank-accounts.tsx` — specific×1; generic×22; semantic=0.568
- `admin/banners.tsx` — specific×2; generic×20; semantic=0.521
- `admin/barcode.tsx` — specific×3; generic×26; semantic=0.633
- `admin/coupons.tsx` — specific×1; generic×20; semantic=0.556
- `admin/dashboard.tsx` — specific×5; generic×36; semantic=0.580
- … +87 more

**Mobile Components (64):**
- `components/AddressesScreen.tsx` — specific×1; generic×21; semantic=0.510
- `components/AuthRequiredModal.tsx` — specific×1; generic×13; semantic=0.551
- `components/BackgroundJobCenter.tsx` — specific×1; generic×15; semantic=0.522
- `components/CartItem.tsx` — specific×1; generic×11; semantic=0.479
- `components/HeroBanner.tsx` — specific×1; generic×16; semantic=0.517
- `components/HomeProductShowcase.tsx` — specific×1; generic×12; semantic=0.534
- `components/LimitedTimeOfferBanner.tsx` — specific×1; generic×6; semantic=0.515
- `components/LocationPicker.tsx` — specific×1; generic×15; semantic=0.526
- `components/Logo.tsx` — specific×1; generic×3; semantic=0.480
- `components/MobileBackgroundEffect.tsx` — specific×1; generic×6; semantic=0.467
- `components/MobileSeasonalBanner.tsx` — specific×1; generic×18; semantic=0.514
- `components/NewsletterSignup.tsx` — specific×1; generic×13; semantic=0.557
- `components/OrderCard.tsx` — specific×5; generic×20; semantic=0.649
- `components/ProductCard.tsx` — specific×1; generic×14; semantic=0.541
- `components/QuickViewModal.tsx` — specific×1; generic×12; semantic=0.541
- `components/RecentlyViewed.tsx` — specific×1; generic×8; semantic=0.550
- `components/Recommendations.tsx` — specific×1; generic×10; semantic=0.547
- `components/SignaturePad.tsx` — specific×1; generic×10; semantic=0.495
- `components/ToastContainer.tsx` — specific×1; generic×7; semantic=0.475
- `components/UserRealtimeBridge.tsx` — generic×5; semantic=0.520
- … +44 more

**Mobile Lib/Hooks (42):**
- `lib/__mocks__/react-native.ts` — generic×9; semantic=0.509
- `lib/adminManagementUtils.ts` — specific×1; generic×12; semantic=0.565
- `lib/api.ts` — specific×10; generic×46; semantic=0.539
- `lib/authPrompt.tsx` — specific×1; generic×18; semantic=0.503
- `lib/authStore.ts` — specific×2; generic×13; semantic=0.535
- `lib/backgroundJobStore.ts` — generic×8; semantic=0.558
- `lib/backgroundJobs.ts` — generic×12; semantic=0.513
- `lib/cartStore.ts` — generic×8; semantic=0.541
- `lib/chatbotStore.ts` — generic×6; semantic=0.480
- `lib/countryContext.tsx` — generic×4; semantic=0.527
- `lib/countrySelection.ts` — generic×4; semantic=0.536
- `lib/currencyStore.ts` — specific×1; generic×6; semantic=0.528
- `lib/documentPicker.ts` — generic×2; semantic=0.488
- `lib/errorReporter.ts` — generic×3; semantic=0.548
- `lib/expoSecureStorage.ts` — generic×2; semantic=0.506
- `lib/fileSystem.ts` — generic×7; semantic=0.508
- `lib/geo.ts` — generic×2; semantic=0.497
- `lib/globalErrorHandler.ts` — generic×2; semantic=0.507
- `lib/homeInsights.ts` — generic×2; semantic=0.485
- `lib/icons.ts` — specific×1; generic×16; semantic=0.554
- … +22 more

**Backend Tests (63):**
- `conftest.py` — specific×3; generic×30; semantic=0.627
- `playwright/e2e/auth.spec.ts` — generic×9; semantic=0.517
- `playwright/e2e/cart.spec.ts` — generic×9; semantic=0.543
- `playwright/e2e/checkout.spec.ts` — specific×1; generic×9; semantic=0.555
- `playwright/e2e/finance-automation.spec.ts` — specific×1; generic×19; semantic=0.573
- `playwright/e2e/products.spec.ts` — generic×8; semantic=0.559
- `playwright/e2e/user-profile.spec.ts` — specific×1; generic×9; semantic=0.525
- `playwright/helpers/auth.ts` — generic×7; semantic=0.512
- `playwright/playwright.config.ts` — generic×4; semantic=0.481
- `test_admin.py` — specific×1; generic×11; semantic=0.550
- `test_ai_research_jobs.py` — specific×2; generic×11; semantic=0.522
- `test_ai_research_router.py` — specific×1; generic×9; semantic=0.549
- `test_api_endpoints.py` — specific×1; generic×11; semantic=0.454
- `test_api_pagination.py` — specific×1; generic×10; semantic=0.561
- `test_auth.py` — generic×9; semantic=0.527
- `test_auto_payout_sweep.py` — specific×1; generic×16; semantic=0.569
- `test_background_jobs.py` — generic×8; semantic=0.487
- `test_banners.py` — specific×2; generic×11; semantic=0.528
- `test_cart.py` — generic×11; semantic=0.578
- `test_categories.py` — specific×1; generic×10; semantic=0.536
- … +43 more

**Web Tests (77):**
- `__tests__/cartHelpers.test.ts` — specific×1; generic×6; semantic=0.505
- `__tests__/chatbot.test.ts` — specific×1; generic×3; semantic=0.496
- `__tests__/checkoutHelpers.test.ts` — specific×1; generic×11; semantic=0.573
- `__tests__/localization.test.ts` — generic×2; semantic=0.507
- `__tests__/money.test.ts` — generic×5; semantic=0.469
- `__tests__/orderHelpers.test.ts` — specific×5; generic×13; semantic=0.610
- `cartHelpers.test.ts` — specific×1; generic×6; semantic=0.502
- `chatbot.test.ts` — specific×1; generic×3; semantic=0.488
- `checkoutHelpers.test.ts` — specific×1; generic×11; semantic=0.579
- `components/ProductCard.test.ts` — generic×5; semantic=0.568
- `localization.test.ts` — generic×2; semantic=0.503
- `money.test.ts` — generic×5; semantic=0.478
- `orderHelpers.test.ts` — specific×5; generic×13; semantic=0.611
- `web_app/__tests__/browser.spec.ts` — generic×8; semantic=0.512
- `web_app/playwright.__tests__.config.ts` — generic×3; semantic=0.482
- `Chatbot.test.tsx` — specific×1; generic×20; semantic=0.486
- `ErrorBoundary.test.tsx` — generic×4; semantic=0.486
- `components/ApprovalActionModal.test.tsx` — specific×1; generic×13; semantic=0.530
- `components/CountryDetailWorkspace.test.tsx` — specific×1; generic×14; semantic=0.540
- `components/CountryResearchPanel.test.tsx` — specific×1; generic×11; semantic=0.541
- … +57 more

**Mobile Tests (63):**
- `addressesScreen.test.ts` — generic×11; semantic=0.504
- `adminAnalyticsScreen.test.tsx` — specific×1; generic×12; semantic=0.467
- `adminBankAccountsScreen.test.tsx` — specific×1; generic×13; semantic=0.489
- `adminDashboardScreen.test.ts` — specific×1; generic×13; semantic=0.542
- `adminGuardedScreens.test.tsx` — specific×2; generic×15; semantic=0.457
- `adminListUtils.test.ts` — generic×7; semantic=0.556
- `adminManagementUtils.test.ts` — specific×2; generic×10; semantic=0.562
- `adminMobileAudit.test.tsx` — specific×2; generic×21; semantic=0.460
- `adminPromotionsHub.test.tsx` — specific×1; generic×5; semantic=0.462
- `api.test.ts` — generic×5; semantic=0.496
- `authRecoveryScreens.test.tsx` — specific×1; generic×9; semantic=0.462
- `authStore.test.ts` — generic×7; semantic=0.503
- `backgroundJobStore.test.ts` — specific×1; generic×8; semantic=0.492
- `backgroundJobs.test.ts` — specific×1; generic×8; semantic=0.471
- `cartScreen.test.tsx` — specific×1; generic×10; semantic=0.505
- `cartStore.test.ts` — generic×9; semantic=0.501
- `chatbotScreen.test.tsx` — specific×1; generic×17; semantic=0.457
- `checkoutFlow.test.ts` — specific×1; generic×21; semantic=0.602
- `checkoutScreen.test.tsx` — specific×3; generic×31; semantic=0.492
- `countryContext.test.tsx` — generic×4; semantic=0.498
- … +43 more

**E2E Tests (65):**
- `e2e/auth.spec.ts` — generic×7; semantic=0.497
- `e2e/mobile-smoke.spec.ts` — generic×5; semantic=0.502
- `e2e/navigation.spec.ts` — generic×5; semantic=0.527
- `web_app/e2e/admin-audit-fixes.spec.ts` — generic×9; semantic=0.512
- `web_app/e2e/admin-commission.spec.ts` — specific×2; generic×19; semantic=0.566
- `web_app/e2e/admin-communication-hub.spec.ts` — specific×2; generic×19; semantic=0.543
- `web_app/e2e/admin-country-control-plane.spec.ts` — specific×1; generic×26; semantic=0.536
- `web_app/e2e/admin-country-enhanced.spec.ts` — generic×20; semantic=0.530
- `web_app/e2e/admin-data-ops.spec.ts` — generic×13; semantic=0.541
- `web_app/e2e/admin-hr-permissions.spec.ts` — specific×2; generic×18; semantic=0.554
- `web_app/e2e/admin-logistics-pricing-insights-live.spec.ts` — generic×15; semantic=0.573
- `web_app/e2e/admin-logistics-workspace.spec.ts` — specific×2; generic×37; semantic=0.594
- `web_app/e2e/admin-modules-reconciliation.spec.ts` — specific×1; generic×16; semantic=0.545
- `web_app/e2e/admin-payment-gateways.spec.ts` — specific×1; generic×25; semantic=0.552
- `web_app/e2e/admin-supplier-logistics-sanity.spec.ts` — specific×3; generic×30; semantic=0.683
- `web_app/e2e/admin-treasury-payout.spec.ts` — specific×1; generic×19; semantic=0.584
- `web_app/e2e/amendment-verify.spec.ts` — generic×11; semantic=0.550
- `web_app/e2e/auth-registration-login.spec.ts` — specific×1; generic×18; semantic=0.579
- `web_app/e2e/auth-role-login.spec.ts` — specific×1; generic×9; semantic=0.584
- `web_app/e2e/bg-comparison-visual.spec.ts` — specific×1; generic×14; semantic=0.496
- … +45 more

**Migrations (27):**
- `alembic/_analyze_graph.py` — generic×7; semantic=0.507
- `alembic/_diagnose_tree.py` — generic×6; semantic=0.509
- `alembic/_graph_analysis.py` — generic×8; semantic=0.498
- `alembic/env.py` — generic×4; semantic=0.509
- `alembic/versions/2026_07_26_16_09-b81bfc888610_baseline_canonical_orm_schema_clean.py` — specific×1; generic×7; semantic=0.534
- `alembic/versions/2026_07_26_21_30_c9e8f7d6a5b4_add_communication_gap_tables.py` — specific×3; generic×19; semantic=0.522
- `alembic/versions/2026_07_27_00_32-c0f3f1817791_add_production_postgres_indexes.py` — specific×2; generic×13; semantic=0.529
- `alembic/versions/2026_07_27_09_08-20260727_0908_add_check_constraints_to_status_enum_columns.py` — specific×6; generic×20; semantic=0.558
- `alembic/versions/2026_07_28_0000_employee_hr_tables.py` — specific×1; generic×13; semantic=0.559
- `alembic/versions/2026_07_28_19_30-e8efae30fc29_add_missing_indexes_and_constraints.py` — specific×5; generic×28; semantic=0.574
- `alembic/versions/2026_07_28_21_14-87146598d2c3_add_missing_fk_constraints_for_.py` — generic×7; semantic=0.538
- `alembic/versions/2026_07_29_10_17-e281faa0c087_add_orm_models_for_orphaned_employee_.py` — generic×5; semantic=0.545
- `alembic/versions/2026_07_29_10_28-9ff24a0683dd_schema_drift_check.py` — specific×2; generic×18; semantic=0.553
- `alembic/versions/2026_07_29_19_14-20260729_1914_add_products_search_vector_trigger.py` — generic×4; semantic=0.544
- `alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py` — specific×1; generic×10; semantic=0.534
- `alembic/versions/2026_07_30_0001-20260730_0001_create_user_points_table.py` — generic×3; semantic=0.529
- `alembic/versions/2026_07_30_0002-20260730_0002_create_points_transactions_table.py` — specific×1; generic×5; semantic=0.549
- `alembic/versions/2026_07_30_0003-20260730_0003_create_upload_jobs_table.py` — generic×7; semantic=0.562
- `alembic/versions/2026_07_30_0004-20260730_0004_create_event_tables.py` — specific×2; generic×14; semantic=0.569
- `alembic/versions/2026_07_30_0005-20260730_0005_bounded_context_schema_migration.py` — specific×7; generic×41; semantic=0.541
- … +7 more

**Backend Scripts (4):**
- `providers/hr/check_BiRefNet.py` — generic×3; semantic=0.547
- `providers/legacy/check_BiRefNet.py` — generic×3; semantic=0.505
- `seed_all.py` — specific×6; generic×39; semantic=0.575
- `fix_chat.py` — generic×2; semantic=0.428

**Backend Other (19):**
- `_import_test.py` — specific×1; generic×8; semantic=0.511
- `database_logging.py` — generic×6; semantic=0.608
- `create_tables.py` — generic×3; semantic=0.487
- `mixins.py` — specific×1; generic×5; semantic=0.594
- `transaction.py` — specific×1; generic×3; semantic=0.686
- `dependencies/country_rls.py` — specific×1; generic×12; semantic=0.577
- `events/event_publisher.py` — generic×7; semantic=0.565
- `events/payment_events.py` — specific×2; generic×10; semantic=0.599
- `lifespan.py` — generic×18; semantic=0.602
- `countries.py` — generic×2; semantic=0.541
- `mixins.py` — generic×2; semantic=0.578
- `upload_job.py` — generic×6; semantic=0.491
- `run_server.py` — generic×2; semantic=0.555
- `settings/notification_worker.py` — specific×3; generic×20; semantic=0.581
- `tasks/background_tasks.py` — generic×7; semantic=0.523
- `tasks/fraud_monitoring.py` — generic×6; semantic=0.562
- `tools/mcp/mcp_client_example.py` — generic×6; semantic=0.565
- `tools/mcp/mcp_server.py` — specific×3; generic×26; semantic=0.582
- `zozi_mcp/zozi_mcp.py` — specific×4; generic×27; semantic=0.714

---
