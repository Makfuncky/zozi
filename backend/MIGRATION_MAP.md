# Auto-Router Migration Map (hand-written routers -> decorated controllers)

Generated analysis of 315 hand-written routers.

## Legend
- **Handlers**: inline `@router.*`/`@app.*` route decorators in the file.
- **Backing controller(s)**: `from controllers.X import` targets (the logic owner to decorate).
- **Risk**: `HIGH` if name or backing controller touches auth/identity/permission/security; else `LOW`.
- **Deco?**: `yes` if already covered by a `core.route_contract` decorated controller (skip).

## Ranked candidates (by handler count, descending)

| Router | Handlers | Risk | Backing controller(s) | Deco? |
|---|---:|---|---|---|
| `admin.py` | 124 | LOW | controllers.admin.admin_controller, controllers.catalog.banner_controller, controllers.commerce.flash_sale_controller, controllers.commerce.promotion_controller, controllers.core.export_controller, controllers.finance.invoice_controller, controllers.orders, controllers.orders.logistics_partner_controller, controllers.supplier.supplier_controller, controllers.supplier_document_controller |  |
| `admin_logistics_operations.py` | 124 | LOW | controllers.admin.admin_controller, controllers.catalog.banner_controller, controllers.commerce.flash_sale_controller, controllers.commerce.promotion_controller, controllers.core.export_controller, controllers.finance.invoice_controller, controllers.orders, controllers.orders.logistics_partner_controller, controllers.supplier.supplier_controller, controllers.supplier.supplier_document_controller |  |
| `admin_geography_configuration.py` | 69 | HIGH | controllers.geography, controllers.geography.country_controller, controllers.hr, controllers.security.auth_controller |  |
| `countries.py` | 69 | HIGH | controllers.country_controller, controllers.geography, controllers.hr, controllers.security.auth_controller |  |
| `public_geography_configuration.py` | 69 | HIGH | controllers.geography, controllers.geography.country_controller, controllers.hr, controllers.security.auth_controller |  |
| `admin_treasury.py` | 60 | HIGH | controllers.security.auth_controller |  |
| `admin_treasury_reporting.py` | 60 | HIGH | controllers.security.auth_controller |  |
| `logistics_partner.py` | 57 | LOW | controllers.orders.logistics_partner_controller |  |
| `logistics_partner_verify.py` | 57 | LOW | controllers.orders.logistics_partner_controller |  |
| `employees.py` | 36 | HIGH | controllers.hr, controllers.security.auth_controller |  |
| `cash_management.py` | 34 | LOW | controllers.admin.admin_controller, controllers.treasury.cash_management_controller |  |
| `admin_commerce_configuration.py` | 31 | LOW | controllers.admin.admin_controller |  |
| `admin_promotions.py` | 31 | LOW | controllers.admin.admin_controller |  |
| `payments.py` | 28 | HIGH | controllers.payments_controller, controllers.security.auth_controller |  |
| `accounting.py` | 25 | LOW | controllers.admin.admin_controller, controllers.finance, controllers.finance.sub_ledger_controller | yes |
| `admin_finance_creation.py` | 25 | LOW | controllers.admin.admin_controller, controllers.finance, controllers.finance.sub_ledger_controller | yes |
| `public_finance_creation.py` | 25 | LOW | controllers.admin.admin_controller, controllers.finance, controllers.finance.sub_ledger_controller | yes |
| `automation.py` | 24 | LOW | controllers.admin.admin_controller |  |
| `system_ai_reporting.py` | 24 | LOW | controllers.admin.admin_controller |  |
| `hierarchy.py` | 23 | HIGH | controllers.security.auth_controller |  |
| `admin_security_detection.py` | 21 | HIGH | *(inline-only)* |  |
| `admin_supplier_reviews.py` | 21 | LOW | controllers.admin.admin_controller, controllers.supplier.supplier_document_controller |  |
| `admin_suppliers.py` | 21 | LOW | controllers.admin.admin_controller, controllers.supplier_document_controller |  |
| `public_security_detection.py` | 21 | HIGH | *(inline-only)* |  |
| `admin_supplier_trading.py` | 19 | LOW | controllers.admin.admin_controller |  |
| `email.py` | 19 | LOW | controllers.admin.admin_controller |  |
| `finance.py` | 19 | HIGH | controllers.security.auth_controller |  |
| `logistics.py` | 19 | LOW | controllers.orders.logistics_controller |  |
| `logistics_logistics_status.py` | 19 | LOW | controllers.orders.logistics_controller |  |
| `trading.py` | 19 | LOW | controllers.admin.admin_controller |  |
| `admin_permissions_validation.py` | 18 | HIGH | controllers.admin.admin_controller, controllers.security.auth_controller |  |
| `commission.py` | 18 | LOW | controllers.admin.admin_controller, controllers.finance |  |
| `permissions.py` | 18 | HIGH | controllers.admin.admin_controller, controllers.security.auth_controller |  |
| `public_permissions_validation.py` | 18 | HIGH | controllers.admin.admin_controller, controllers.security.auth_controller |  |
| `admin_geography_audit.py` | 16 | HIGH | controllers.security.auth_controller |  |
| `admin_treasury_cash_management_write.py` | 16 | LOW | controllers.treasury.cash_management_write_controller | yes |
| `country_admin.py` | 16 | HIGH | controllers.security.auth_controller |  |
| `admin_governance_command_center.py` | 15 | LOW | controllers.governance.command_center_controller | yes |
| `search.py` | 15 | HIGH | controllers.search_controller, controllers.security.auth_controller |  |
| `hr.py` | 13 | LOW | controllers.hr_controller |  |
| `admin_analytics_fallback_dashboard.py` | 12 | LOW | controllers.admin.admin_controller |  |
| `admin_chat.py` | 12 | LOW | *(inline-only)* |  |
| `admin_comms_messaging.py` | 12 | LOW | *(inline-only)* |  |
| `admin_fallback.py` | 12 | LOW | controllers.admin.admin_controller |  |
| `admin_geography_country_versioning.py` | 12 | LOW | controllers.geography.country_versioning_controller | yes |
| `admin_identity_operations.py` | 12 | HIGH | controllers.admin.admin_controller |  |
| `admin_logistics_fallback.py` | 12 | LOW | controllers.admin.admin_controller |  |
| `admin_payouts.py` | 12 | LOW | *(inline-only)* |  |
| `admin_treasury_status.py` | 12 | LOW | *(inline-only)* |  |
| `admin_users.py` | 12 | HIGH | controllers.admin.admin_controller |  |
| `admin_catalog_operations.py` | 11 | LOW | controllers.admin.admin_controller, controllers.products.products_controller |  |
| `admin_commerce_promotion_admin.py` | 11 | LOW | controllers.commerce.promotion_admin_controller | yes |
| `admin_logistics_imports.py` | 11 | LOW | controllers.admin.admin_controller |  |
| `admin_products.py` | 11 | LOW | controllers.admin.admin_controller, controllers.products.products_controller |  |
| `imports.py` | 11 | LOW | controllers.admin.admin_controller |  |
| `performance.py` | 11 | HIGH | controllers.security.auth_controller |  |
| `chat_enrichment.py` | 10 | HIGH | controllers.security.auth_controller |  |
| `comms_chat.py` | 10 | LOW | *(inline-only)* |  |
| `products.py` | 10 | HIGH | controllers.products.products_controller, controllers.security.auth_controller |  |
| `admin_admin_users_admin.py` | 9 | HIGH | controllers.admin.users_admin_controller | yes |
| `admin_catalog_orders.py` | 9 | LOW | controllers.admin.admin_controller |  |
| `admin_categories.py` | 9 | LOW | controllers.admin.admin_controller |  |
| `admin_logistics.py` | 9 | LOW | controllers.admin.admin_controller |  |
| `admin_logistics_geography.py` | 9 | LOW | controllers.admin.admin_controller |  |
| `ess.py` | 9 | HIGH | controllers.security.auth_controller |  |
| `orders.py` | 9 | HIGH | controllers.orders_controller, controllers.security.auth_controller |  |
| `video_controller.py` | 9 | LOW | *(inline-only)* |  |
| `admin_orders.py` | 8 | LOW | controllers.admin.admin_controller |  |
| `admin_orders_status.py` | 8 | LOW | controllers.admin.admin_controller |  |
| `finance_package.py` | 8 | HIGH | controllers.security.auth_controller |  |
| `logistics_orders_v2.py` | 8 | LOW | *(inline-only)* |  |
| `proxy_communication.py` | 8 | HIGH | controllers.admin.admin_controller, controllers.security.auth_controller |  |
| `admin_admin_suppliers.py` | 7 | LOW | controllers.admin.suppliers_controller | yes |
| `banners.py` | 7 | LOW | controllers.catalog.banner_controller |  |
| `cart.py` | 7 | LOW | controllers.commerce.cart_controller, controllers.products.products_controller |  |
| `iam.py` | 7 | HIGH | controllers.identity.iam_controller |  |
| `internal_channels.py` | 7 | LOW | *(inline-only)* |  |
| `internal_comms_channels.py` | 7 | LOW | *(inline-only)* |  |
| `invoices.py` | 7 | LOW | controllers.finance.invoice_controller |  |
| `payroll.py` | 7 | HIGH | controllers.security.auth_controller |  |
| `public_hr_hierarchy.py` | 7 | LOW | controllers.hr.hierarchy_controller | yes |
| `supplier_orders.py` | 7 | LOW | *(inline-only)* |  |
| `supplier_orders_verify.py` | 7 | LOW | *(inline-only)* |  |
| `admin_admin_analytics.py` | 6 | LOW | controllers.admin.analytics_controller | yes |
| `admin_admin_products.py` | 6 | LOW | controllers.admin.products_controller | yes |
| `admin_banners.py` | 6 | LOW | controllers.catalog.banner_controller |  |
| `admin_commerce_geography.py` | 6 | LOW | controllers.catalog.banner_controller |  |
| `admin_commission.py` | 6 | LOW | *(inline-only)* |  |
| `admin_finance_geography.py` | 6 | LOW | *(inline-only)* |  |
| `admin_media_geography.py` | 6 | LOW | *(inline-only)* |  |
| `admin_promotions_routes.py` | 6 | LOW | controllers.commerce.promotion_admin_controller | yes |
| `admin_security_health.py` | 6 | HIGH | controllers.security.risk_controller | yes |
| `admin_security_registration.py` | 6 | HIGH | *(inline-only)* |  |
| `admin_treasury_payments.py` | 6 | LOW | controllers.treasury.payout_approval_controller | yes |
| `admin_video.py` | 6 | LOW | *(inline-only)* |  |
| `ai.py` | 6 | LOW | controllers.core.ai_controller | yes |
| `auth.py` | 6 | HIGH | *(inline-only)* |  |
| `categories.py` | 6 | LOW | *(inline-only)* |  |
| `comms_video.py` | 6 | LOW | *(inline-only)* |  |
| `compliance.py` | 6 | LOW | *(inline-only)* |  |
| `country_payouts.py` | 6 | LOW | controllers.admin.admin_controller |  |
| `country_staff.py` | 6 | HIGH | controllers.admin.admin_controller, controllers.security.auth_controller |  |
| `governance_package.py` | 6 | HIGH | controllers.security.auth_controller |  |
| `public_commerce_reviews.py` | 6 | LOW | controllers.commerce.reviews_controller | yes |
| `public_security_health.py` | 6 | HIGH | controllers.security.risk_controller | yes |
| `public_security_registration.py` | 6 | HIGH | *(inline-only)* |  |
| `public_treasury_payments.py` | 6 | LOW | *(inline-only)* |  |
| `returns.py` | 6 | LOW | controllers.orders.returns_controller |  |
| `risk.py` | 6 | HIGH | controllers.security.risk_controller | yes |
| `supplier_products.py` | 6 | LOW | *(inline-only)* |  |
| `supplier_products_upload.py` | 6 | LOW | *(inline-only)* |  |
| `system_ai_sync.py` | 6 | LOW | controllers.core.ai_controller | yes |
| `video.py` | 6 | LOW | *(inline-only)* |  |
| `addresses.py` | 5 | LOW | *(inline-only)* |  |
| `admin_comms_geography.py` | 5 | LOW | *(inline-only)* |  |
| `admin_email.py` | 5 | LOW | *(inline-only)* |  |
| `admin_identity_operations_api.py` | 5 | HIGH | *(inline-only)* |  |
| `comm.py` | 5 | LOW | controllers.comms.comm_controller |  |
| `customer_coupons_create.py` | 5 | LOW | controllers.commerce.coupons_controller |  |
| `lms.py` | 5 | LOW | controllers.hr.lms_controller |  |
| `onboarding.py` | 5 | HIGH | controllers.security.auth_controller |  |
| `public_identity_operations.py` | 5 | HIGH | *(inline-only)* |  |
| `reviews.py` | 5 | LOW | *(inline-only)* |  |
| `shipments.py` | 5 | LOW | *(inline-only)* |  |
| `supplier_finance.py` | 5 | LOW | *(inline-only)* |  |
| `supplier_finance_status.py` | 5 | LOW | *(inline-only)* |  |
| `tickets.py` | 5 | LOW | *(inline-only)* |  |
| `users.py` | 5 | LOW | *(inline-only)* |  |
| `admin_admin_coupons.py` | 4 | LOW | controllers.admin.coupons_controller | yes |
| `admin_admin_tickets.py` | 4 | LOW | controllers.admin.tickets_controller | yes |
| `admin_security_operations.py` | 4 | HIGH | controllers.security.auth_controller |  |
| `admin_treasury_cash_position.py` | 4 | HIGH | controllers.security.auth_controller |  |
| `ai_upload.py` | 4 | LOW | controllers.admin.admin_controller |  |
| `api_geography_location.py` | 4 | LOW | *(inline-only)* |  |
| `country_communications.py` | 4 | LOW | *(inline-only)* |  |
| `coupons.py` | 4 | HIGH | controllers.security.auth_controller |  |
| `customer_coupons_mgmt.py` | 4 | HIGH | controllers.security.auth_controller |  |
| `email_enrichment.py` | 4 | HIGH | controllers.security.auth_controller |  |
| `entity_chat.py` | 4 | HIGH | controllers.security.auth_controller |  |
| `entity_communication.py` | 4 | HIGH | controllers.security.auth_controller |  |
| `incident.py` | 4 | HIGH | controllers.security.auth_controller |  |
| `location_api.py` | 4 | LOW | *(inline-only)* |  |
| `notifications.py` | 4 | HIGH | controllers.security.auth_controller |  |
| `public_commerce_validation.py` | 4 | HIGH | controllers.security.auth_controller |  |
| `public_commerce_wishlist.py` | 4 | LOW | controllers.commerce.wishlist_controller | yes |
| `public_core_ai_upload.py` | 4 | LOW | controllers.core.ai_upload_controller | yes |
| `public_security_operations.py` | 4 | HIGH | controllers.security.auth_controller |  |
| `public_suppliers.py` | 4 | LOW | controllers.supplier.supplier_controller |  |
| `public_treasury_cash_position.py` | 4 | HIGH | controllers.security.auth_controller |  |
| `succession.py` | 4 | HIGH | controllers.security.auth_controller |  |
| `system_ai_upload.py` | 4 | LOW | controllers.admin.admin_controller |  |
| `treasury.py` | 4 | HIGH | controllers.security.auth_controller |  |
| `admin_admin_bank_accounts.py` | 3 | LOW | controllers.admin.bank_accounts_controller | yes |
| `admin_admin_orders.py` | 3 | LOW | controllers.admin.orders_controller | yes |
| `admin_admin_permissions.py` | 3 | HIGH | controllers.admin.permissions_controller | yes |
| `admin_cash.py` | 3 | LOW | *(inline-only)* |  |
| `admin_treasury_identity.py` | 3 | HIGH | *(inline-only)* |  |
| `chatbot.py` | 3 | LOW | controllers.comms.chatbot_controller |  |
| `country_dropdown.py` | 3 | HIGH | controllers.security.auth_controller |  |
| `currency.py` | 3 | LOW | *(inline-only)* |  |
| `ediscovery.py` | 3 | LOW | controllers.admin.admin_controller |  |
| `escalation.py` | 3 | HIGH | controllers.security.auth_controller |  |
| `okr.py` | 3 | HIGH | controllers.security.auth_controller |  |
| `supplier_documents_review.py` | 3 | LOW | *(inline-only)* |  |
| `supplier_profile.py` | 3 | LOW | *(inline-only)* |  |
| `supplier_profile_create.py` | 3 | LOW | *(inline-only)* |  |
| `supplier_supplier_upload.py` | 3 | LOW | controllers.admin.admin_controller |  |
| `system_ai_messaging.py` | 3 | LOW | controllers.comms.chatbot_controller |  |
| `travel.py` | 3 | HIGH | controllers.security.auth_controller |  |
| `wishlist.py` | 3 | LOW | controllers.products.products_controller |  |
| `admin_admin_audit.py` | 2 | LOW | controllers.admin.audit_controller | yes |
| `admin_categories_routes.py` | 2 | LOW | controllers.catalog.categories_controller |  |
| `admin_chat_routes.py` | 2 | LOW | *(inline-only)* |  |
| `admin_commission_routes.py` | 2 | LOW | controllers.finance.commission_controller |  |
| `admin_comms_unified.py` | 2 | LOW | *(inline-only)* |  |
| `admin_logistics_routes.py` | 2 | LOW | controllers.orders.logistics_controller |  |
| `admin_orders_routes.py` | 2 | LOW | controllers.orders.orders_controller |  |
| `admin_products_routes.py` | 2 | LOW | controllers.products.products_controller |  |
| `admin_video_routes.py` | 2 | LOW | *(inline-only)* |  |
| `audit.py` | 2 | LOW | *(inline-only)* |  |
| `comms_unified.py` | 2 | LOW | *(inline-only)* |  |
| `core_accounting_routes.py` | 2 | LOW | controllers.finance.accounting_controller | yes |
| `core_ai_routes.py` | 2 | LOW | controllers.core.ai_controller | yes |
| `core_chatbot_routes.py` | 2 | LOW | controllers.comms.chatbot_controller |  |
| `core_comm_routes.py` | 2 | LOW | controllers.comms.comm_controller |  |
| `core_commission_routes.py` | 2 | LOW | controllers.finance.commission_controller |  |
| `core_compliance_routes.py` | 2 | LOW | controllers.governance.compliance_controller |  |
| `core_export_routes.py` | 2 | LOW | controllers.core.export_controller |  |
| `core_hierarchy_routes.py` | 2 | LOW | controllers.hr.hierarchy_controller | yes |
| `core_iam_routes.py` | 2 | HIGH | controllers.identity.iam_controller |  |
| `core_lms_routes.py` | 2 | LOW | controllers.hr.lms_controller |  |
| `core_risk_routes.py` | 2 | HIGH | controllers.security.risk_controller | yes |
| `core_video_routes.py` | 2 | LOW | *(inline-only)* |  |
| `country_admin_routes.py` | 2 | LOW | controllers.admin.admin_controller |  |
| `country_maps.py` | 2 | LOW | *(inline-only)* |  |
| `customer_health.py` | 2 | HIGH | controllers.security.auth_controller |  |
| `customer_health_list.py` | 2 | HIGH | controllers.security.auth_controller |  |
| `geo.py` | 2 | HIGH | controllers.security.auth_controller |  |
| `logistics_health.py` | 2 | HIGH | controllers.security.auth_controller |  |
| `logistics_health_list.py` | 2 | HIGH | controllers.security.auth_controller |  |
| `logistics_locations.py` | 2 | HIGH | controllers.security.auth_controller |  |
| `logistics_locations_create.py` | 2 | HIGH | controllers.security.auth_controller |  |
| `public_commerce_referrals.py` | 2 | LOW | controllers.commerce.referrals_controller | yes |
| `public_comms_status.py` | 2 | LOW | *(inline-only)* |  |
| `public_comms_unified.py` | 2 | LOW | *(inline-only)* |  |
| `referrals.py` | 2 | LOW | controllers.commerce.promotion_controller |  |
| `store_cart_routes.py` | 2 | LOW | controllers.commerce.cart_controller |  |
| `store_orders_routes.py` | 2 | LOW | controllers.orders.orders_controller |  |
| `store_payments_routes.py` | 2 | LOW | *(inline-only)* |  |
| `store_products_routes.py` | 2 | LOW | controllers.products.products_controller |  |
| `store_referrals_routes.py` | 2 | LOW | controllers.commerce.referrals_controller | yes |
| `store_returns_routes.py` | 2 | LOW | controllers.orders.returns_controller |  |
| `supplier_documents.py` | 2 | LOW | *(inline-only)* |  |
| `supplier_health.py` | 2 | HIGH | controllers.security.auth_controller |  |
| `supplier_health_list.py` | 2 | HIGH | controllers.security.auth_controller |  |
| `supplier_payouts_pay.py` | 2 | LOW | *(inline-only)* |  |
| `system_ai_country_research.py` | 2 | LOW | *(inline-only)* |  |
| `system_comms_status.py` | 2 | LOW | controllers.comms.chat_write_controller |  |
| `upload.py` | 2 | LOW | *(inline-only)* |  |
| `workflows.py` | 2 | HIGH | controllers.security.auth_controller |  |
| `admin_admin_misc.py` | 1 | LOW | controllers.admin.misc_controller | yes |
| `admin_analytics_routes.py` | 1 | LOW | *(inline-only)* |  |
| `admin_banners_routes.py` | 1 | LOW | *(inline-only)* |  |
| `admin_cash_routes.py` | 1 | LOW | *(inline-only)* |  |
| `admin_configuration_operations.py` | 1 | LOW | *(inline-only)* |  |
| `admin_core_routes.py` | 1 | LOW | *(inline-only)* |  |
| `admin_email_routes.py` | 1 | LOW | *(inline-only)* |  |
| `admin_fallback_routes.py` | 1 | LOW | *(inline-only)* |  |
| `admin_payouts_routes.py` | 1 | LOW | *(inline-only)* |  |
| `admin_settings.py` | 1 | LOW | *(inline-only)* |  |
| `admin_settings_routes.py` | 1 | LOW | *(inline-only)* |  |
| `admin_suppliers_routes.py` | 1 | LOW | *(inline-only)* |  |
| `admin_treasury_routes.py` | 1 | LOW | *(inline-only)* |  |
| `admin_users_routes.py` | 1 | HIGH | *(inline-only)* |  |
| `ai_image.py` | 1 | LOW | *(inline-only)* |  |
| `ai_research.py` | 1 | LOW | *(inline-only)* |  |
| `batch_upload.py` | 1 | LOW | *(inline-only)* |  |
| `contact.py` | 1 | HIGH | controllers.security.auth_controller |  |
| `core_addresses_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_automation_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_countries_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_ediscovery_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_email_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_ess_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_imports_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_incident_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_invoices_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_jobs_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_messaging_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_okr_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_onboarding_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_payroll_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_performance_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_permissions_routes.py` | 1 | HIGH | *(inline-only)* |  |
| `core_succession_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_tickets_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_trading_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_travel_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_treasury_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_upload_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_users_routes.py` | 1 | LOW | *(inline-only)* |  |
| `core_workflows_routes.py` | 1 | LOW | *(inline-only)* |  |
| `country_auto_populate.py` | 1 | LOW | *(inline-only)* |  |
| `country_payouts_routes.py` | 1 | LOW | *(inline-only)* |  |
| `country_research.py` | 1 | LOW | *(inline-only)* |  |
| `country_staff_routes.py` | 1 | LOW | *(inline-only)* |  |
| `cross_border.py` | 1 | LOW | *(inline-only)* |  |
| `csp_reporting.py` | 1 | LOW | *(inline-only)* |  |
| `email_controller.py` | 1 | LOW | *(inline-only)* |  |
| `finance_automation.py` | 1 | LOW | *(inline-only)* |  |
| `finance_erp.py` | 1 | LOW | *(inline-only)* |  |
| `flash_sales.py` | 1 | LOW | *(inline-only)* |  |
| `fraud_detection.py` | 1 | LOW | *(inline-only)* |  |
| `frontend_errors.py` | 1 | LOW | *(inline-only)* |  |
| `hr_dashboard.py` | 1 | LOW | *(inline-only)* |  |
| `jobs.py` | 1 | LOW | *(inline-only)* |  |
| `logistics_orders_list.py` | 1 | LOW | *(inline-only)* |  |
| `parcel_tracking.py` | 1 | LOW | *(inline-only)* |  |
| `payout_approval.py` | 1 | LOW | *(inline-only)* |  |
| `product_moderation.py` | 1 | LOW | *(inline-only)* |  |
| `product_verification.py` | 1 | LOW | *(inline-only)* |  |
| `product_videos.py` | 1 | LOW | *(inline-only)* |  |
| `public_auth_access.py` | 1 | HIGH | *(inline-only)* |  |
| `public_core_translate.py` | 1 | LOW | controllers.core.translate_controller | yes |
| `public_effective_permissions_access.py` | 1 | HIGH | *(inline-only)* |  |
| `public_permission_primitives_access.py` | 1 | HIGH | *(inline-only)* |  |
| `public_suppliers_routes.py` | 1 | LOW | *(inline-only)* |  |
| `public_treasury_api_access.py` | 1 | LOW | *(inline-only)* |  |
| `push_notifications.py` | 1 | LOW | *(inline-only)* |  |
| `shift_handover.py` | 1 | LOW | *(inline-only)* |  |
| `shop_locations.py` | 1 | LOW | *(inline-only)* |  |
| `store_banners_routes.py` | 1 | LOW | *(inline-only)* |  |
| `store_currency_routes.py` | 1 | LOW | *(inline-only)* |  |
| `store_shipments_routes.py` | 1 | LOW | *(inline-only)* |  |
| `supplier_analytics.py` | 1 | LOW | *(inline-only)* |  |
| `supplier_analytics_analytics.py` | 1 | LOW | *(inline-only)* |  |
| `supplier_bg_ab_test.py` | 1 | LOW | *(inline-only)* |  |
| `supplier_core_routes.py` | 1 | LOW | *(inline-only)* |  |
| `supplier_payouts.py` | 1 | LOW | *(inline-only)* |  |
| `system_ai_media.py` | 1 | LOW | *(inline-only)* |  |
| `upload_jobs.py` | 1 | LOW | *(inline-only)* |  |
| `ws_chat.py` | 1 | LOW | *(inline-only)* |  |
| `chat.py` | 0 | LOW | *(inline-only)* |  |
| `chat_api.py` | 0 | LOW | *(inline-only)* |  |
| `command_center.py` | 0 | LOW | *(inline-only)* |  |
| `command_center_api.py` | 0 | LOW | *(inline-only)* |  |
| `core_auth_routes.py` | 0 | HIGH | controllers.security.auth_controller |  |
| `country_versioning.py` | 0 | LOW | *(inline-only)* |  |
| `expense_controller.py` | 0 | LOW | *(inline-only)* |  |
| `expenses.py` | 0 | LOW | *(inline-only)* |  |
| `messaging.py` | 0 | LOW | *(inline-only)* |  |
| `mobile_controller.py` | 0 | LOW | *(inline-only)* |  |
| `operational_controller.py` | 0 | LOW | *(inline-only)* |  |
| `public_country_auto_populate_access.py` | 0 | LOW | *(inline-only)* |  |
| `treasury_api.py` | 0 | LOW | *(inline-only)* |  |