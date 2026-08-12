# Controllers -> Services Map

> Auto-generated map of the ZOZI backend's HTTP layer (`controllers/`) to the service modules (`services/`) it imports directly.
>
> - **152** controller modules, **403** service modules (excluding `__init__.py`).
> - Mapping is by *direct Python import*. Many services are also reached transitively (service->service), at runtime (schedulers, webhooks, event bus), or via the central `services/_registry.py`. Those are not shown here by design.
> - Controllers marked **[FACADE]** do not import services directly; they re-export sibling controllers/routers via `from controllers.<pkg> import *`.
> - Controllers marked **(review manually)** delegate to other controllers (not services) and have no direct service import.

## admin

- **controllers.admin.admin_controller**
    - `services.admin.analytics_service`
    - `services.admin.bulk_ops_service`
    - `services.admin.coupons_service`
    - `services.admin.database_service`
    - `services.admin.misc_service`
    - `services.admin.orders_service`
    - `services.admin.payouts_service`
    - `services.admin.permissions_service`
    - `services.admin.products_service`
    - `services.admin.suppliers_service`
    - `services.admin.tickets_service`
    - `services.admin.users_service`
- **controllers.admin.analytics_controller**
    - `services.admin.analytics_service`
- **controllers.admin.audit_controller**
    - `services.admin.misc_service`
- **controllers.admin.auth**  _(review manually)_
- **controllers.admin.bank_accounts_controller**
    - `services.admin.users_service`
- **controllers.admin.coupons_controller**
    - `services.admin.coupons_service`
- **controllers.admin.misc_controller**
    - `services.admin.database_service`
- **controllers.admin.orders_controller**
    - `services.admin.orders_service`
- **controllers.admin.payouts_controller**
    - `services.admin.payouts_service`
- **controllers.admin.permissions_controller**
    - `services.admin.permissions_service`
- **controllers.admin.products_controller**
    - `services.admin.products_service`
- **controllers.admin.suppliers_controller**
    - `services.admin.suppliers_service`
- **controllers.admin.tickets_controller**
    - `services.admin.tickets_service`
- **controllers.admin.users_admin_controller**
    - `services.admin.users_service`

## catalog

- **controllers.catalog.banner_controller**
    - `services.catalog.banner_service`
- **controllers.catalog.categories_controller**  _[FACADE]_ -> re-exports: `controllers.commerce`
- **controllers.catalog.category_admin_controller**
    - `services.catalog.category_admin_read_service`
    - `services.catalog.category_admin_write_service`

## commerce

- **controllers.commerce.cart_controller**
    - `services.commerce.cart_controller_service`
- **controllers.commerce.coupons_controller**
    - `services.commerce.coupons_service`
- **controllers.commerce.flash_sale_controller**
    - `services.commerce.flash_sale_controller_service`
- **controllers.commerce.promotion_admin_controller**
    - `services.promotions.promotion_admin_write_service`
- **controllers.commerce.promotion_controller**
    - `services.commerce.promotion_service`
- **controllers.commerce.referrals_controller**
    - `services.commerce.referrals_service`
- **controllers.commerce.reviews_controller**
    - `services.commerce.reviews_service`
- **controllers.commerce.wishlist_controller**
    - `services.commerce.wishlist_read_service`
    - `services.commerce.wishlist_write_service`

## comms

- **controllers.comms.chat_write_controller**
    - `services.comms.chat_write_service`
    - `services.core.user_read_service`
- **controllers.comms.chatbot_controller**
    - `services.comms.chatbot_service`
- **controllers.comms.comm_controller**
    - `services.comms.comm_service`

## core

- **controllers.core.ai_controller**
    - `services.ai.ai_service`
- **controllers.core.ai_upload_controller**
    - `services.ai.ai_upload_write_service`
- **controllers.core.export_controller**
    - `services.core.export_service`

## customer

- **controllers.customer.users**
    - `services.common.db_read`
    - `services.users.users_write_service`

## delegators

- **controllers.delegators.admin**
    - `services.admin.admin_fallback_service`
- **controllers.delegators.admin_admin_fallback_service**
    - `services.admin.admin_fallback_service`
- **controllers.delegators.admin_admin_write_service**
    - `services.admin.admin_write_service`
- **controllers.delegators.ai**
    - `services.ai.automation_scheduler`
- **controllers.delegators.ai_ai_automation_service**
    - `services.ai.ai_automation_service`
- **controllers.delegators.ai_ai_copy_jobs**
    - `services.ai.ai_copy_jobs`
- **controllers.delegators.ai_ai_research_jobs**
    - `services.ai.ai_research_jobs`
- **controllers.delegators.ai_ai_variant_config**
    - `services.ai.ai_variant_config`
- **controllers.delegators.ai_bg_removal_service**
    - `services.ai.bg_removal_service`
- **controllers.delegators.ai_country_ai_research**
    - `services.ai.country_ai_research`
- **controllers.delegators.ai_parcel_verification_service**
    - `services.ai.parcel_verification_service`
- **controllers.delegators.audit_audit_trail_service**
    - `services.audit.audit_trail_service`
- **controllers.delegators.audit_compliance_engine**
    - `services.audit.compliance_engine`
- **controllers.delegators.catalog_product_admin_read_service**
    - `services.catalog.product_admin_read_service`
- **controllers.delegators.catalog_product_admin_write_service**
    - `services.catalog.product_admin_write_service`
- **controllers.delegators.catalog_variant_config_service**
    - `services.catalog.variant_config_service`
- **controllers.delegators.commerce**
    - `services.commerce.admin_promotion_service`
- **controllers.delegators.commerce_coupons_read_service**
    - `services.commerce.coupons_read_service`
- **controllers.delegators.commerce_coupons_write_service**
    - `services.commerce.coupons_write_service`
- **controllers.delegators.common**
    - `services.common.import_service`
- **controllers.delegators.common_asset_tracking**
    - `services.common.asset_tracking`
- **controllers.delegators.common_storage**
    - `services.common.storage`
- **controllers.delegators.comms_campaign_geography_service**
    - `services.comms.campaign_geography_service`
- **controllers.delegators.comms_chat_system**
    - `services.comms.chat_system`
- **controllers.delegators.comms_content_service**
    - `services.comms.content_service`
- **controllers.delegators.comms_entity_chat_service**
    - `services.comms.entity_chat_service`
- **controllers.delegators.comms_internal_communication**
    - `services.comms.internal_communication`
- **controllers.delegators.comms_realtime_chat_service**
    - `services.comms.realtime_chat_service`
- **controllers.delegators.comms_unified_inbox_service**
    - `services.comms.unified_inbox_service`
- **controllers.delegators.comms_video_conferencing**
    - `services.comms.video_conferencing`
- **controllers.delegators.comms_video_room_service**
    - `services.comms.video_room_service`
- **controllers.delegators.communication_package_service**
    - `services.communication.package_service`
- **controllers.delegators.country_country_communications_read_service**
    - `services.country.country_communications_read_service`
- **controllers.delegators.customer_customer_health_engine**
    - `services.customer.customer_health_engine`
- **controllers.delegators.finance**
    - `services.finance.trading_service`
- **controllers.delegators.finance_commission_geography_service**
    - `services.finance.commission_geography_service`
- **controllers.delegators.finance_contractor_milestone_read_service**
    - `services.finance.contractor_milestone_read_service`
- **controllers.delegators.finance_credit_control_service**
    - `services.finance.credit_control_service`
- **controllers.delegators.finance_expense_processing**
    - `services.finance.expense_processing`
- **controllers.delegators.finance_expense_routing**
    - `services.finance.expense_routing`
- **controllers.delegators.finance_financial_reporting**
    - `services.finance.financial_reporting`
- **controllers.delegators.finance_je_reversal_service**
    - `services.finance.je_reversal_service`
- **controllers.delegators.finance_period_close_service**
    - `services.finance.period_close_service`
- **controllers.delegators.finance_refund_posting_service**
    - `services.finance.refund_posting_service`
- **controllers.delegators.gateways_gateway_reconciliation_service**
    - `services.gateways.gateway_reconciliation_service`
- **controllers.delegators.gateways_payments**
    - `services.gateways.payments`
- **controllers.delegators.geography_country_audit_admin_service**
    - `services.geography.country_admin_write_service`
    - `services.geography.country_audit_admin_service`
- **controllers.delegators.geography_country_config_admin_service**
    - `services.geography.country_config_admin_service`
- **controllers.delegators.governance_command_center_service**
    - `services.governance.command_center_service`
- **controllers.delegators.hierarchy_hierarchy_service**
    - `services.hierarchy.hierarchy_service`
- **controllers.delegators.hr_leave_accrual**
    - `services.hr.leave_accrual`
- **controllers.delegators.hr_payroll_engine**
    - `services.hr.payroll_engine`
- **controllers.delegators.location_service_geo_resolver**
    - `services.location_service.geo_resolver`
- **controllers.delegators.logistics_admin_operations_service**
    - `services.logistics.admin_operations_service`
- **controllers.delegators.logistics_logistics_health_service**
    - `services.logistics.logistics_health_service`
- **controllers.delegators.logistics_logistics_partner_write_service**
    - `services.logistics.logistics_partner_write_service`
- **controllers.delegators.logistics_partner_geography_service**
    - `services.logistics.partner_geography_service`
- **controllers.delegators.logistics_partner_shipments_service**
    - `services.logistics.partner_shipments_service`
- **controllers.delegators.logistics_shipment_service**
    - `services.logistics.shipment_service`
- **controllers.delegators.logistics_shipping_tier**
    - `services.logistics.shipping_tier`
- **controllers.delegators.orders_admin_orders_read_service**
    - `services.orders.admin_orders_read_service`
- **controllers.delegators.orders_admin_orders_write_service**
    - `services.orders.admin_orders_write_service`
- **controllers.delegators.orders_order_tracking_service**
    - `services.orders.order_tracking_service`
- **controllers.delegators.security**
    - `services.security.permission_service`
- **controllers.delegators.security_auth_write_service**
    - `services.security.auth_write_service`
- **controllers.delegators.security_effective_permissions**
    - `services.security.effective_permissions`
- **controllers.delegators.security_fraud_admin_service**
    - `services.security.fraud_admin_service`
- **controllers.delegators.security_fraud_detection_service**
    - `services.security.fraud_detection_service`
- **controllers.delegators.security_incident_service**
    - `services.security.incident_service`
- **controllers.delegators.security_risk_service**
    - `services.security.risk_service`
- **controllers.delegators.supplier_legal_contract_service**
    - `services.supplier.legal_contract_service`
- **controllers.delegators.supplier_supplier_analytics_service**
    - `services.supplier.supplier_analytics_service`
- **controllers.delegators.supplier_supplier_document_service**
    - `services.supplier.supplier_document_service`
- **controllers.delegators.supplier_supplier_finance_service**
    - `services.supplier.supplier_finance_service`
- **controllers.delegators.supplier_supplier_health_service**
    - `services.supplier.supplier_health_service`
- **controllers.delegators.supplier_supplier_order_service**
    - `services.supplier.supplier_order_service`
- **controllers.delegators.supplier_supplier_payout_service**
    - `services.supplier.supplier_payout_service`
- **controllers.delegators.supplier_supplier_products_upload_service**
    - `services.supplier.supplier_products_upload_service`
- **controllers.delegators.supplier_supplier_profile_write_service**
    - `services.supplier.supplier_profile_write_service`
- **controllers.delegators.suppliers**
    - `services.suppliers.admin_supplier_review_service`
- **controllers.delegators.system_ai_upload_service**
    - `services.system.ai_upload_service`
- **controllers.delegators.treasury**
    - `services.treasury.admin_reporting_service`
- **controllers.delegators.treasury_admin_treasury_write_service**
    - `services.admin.payouts_service`
    - `services.supplier.suppliers_write_service`
    - `services.treasury.admin_treasury_write_service`
- **controllers.delegators.treasury_auto_payout_scheduler**
    - `services.finance.auto_payout_scheduler`
    - `services.treasury.auto_payout_scheduler`
- **controllers.delegators.treasury_cash_flow_forecast_service**
    - `services.finance.cash_flow_forecast_service`
    - `services.treasury.cash_flow_forecast_service`
- **controllers.delegators.treasury_cash_read_service**
    - `services.treasury.cash_read_service`
- **controllers.delegators.treasury_cash_write_service**
    - `services.treasury.cash_write_service`
- **controllers.delegators.treasury_payout_approval_read_service**
    - `services.admin.payouts_service`
    - `services.treasury.payout_approval_read_service`
- **controllers.delegators.treasury_payout_approval_write_service**
    - `services.treasury.payout_approval_write_service`
- **controllers.delegators.treasury_payout_batch_service**
    - `services.treasury.payout_batch_service`
- **controllers.delegators.treasury_treasury_adapter**
    - `services.treasury.treasury_adapter`
- **controllers.delegators.treasury_treasury_service**
    - `services.treasury.treasury_service`
- **controllers.delegators.users_approval_matrix_service**
    - `services.users.approval_matrix_service`
- **controllers.delegators.users_identity_admin_service**
    - `services.users.identity_admin_service`

## finance

- **controllers.finance.accounting_controller**
    - `services.finance.general_ledger_service`
- **controllers.finance.commission_controller**
    - `services.finance.commission_service`
- **controllers.finance.expense_controller**  _(review manually)_
- **controllers.finance.invoice_controller**
    - `services.finance.invoice_service`
- **controllers.finance.sub_ledger_controller**
    - `services.finance.sub_ledger_service`

## geography

- **controllers.geography.country_controller**
    - `services.geography.country_service`
- **controllers.geography.country_versioning_controller**
    - `services.geography.country_versioning_service`

## governance

- **controllers.governance.compliance_controller**  _(review manually)_
- **controllers.governance.operational_controller**  _(review manually)_

## hr

- **controllers.hr.employees_controller**
    - `services.hr.employees_controller_service`
- **controllers.hr.hierarchy_controller**
    - `services.hierarchy.org_hierarchy_write_service`
- **controllers.hr.lms_controller**
    - `services.hr.lms_service`

## identity

- **controllers.identity.iam_controller**
    - `services.identity.iam_service`

## orders

- **controllers.orders.disputes_controller**
    - `services.orders.disputes_service`
- **controllers.orders.logistics_controller**
    - `services.orders.logistics_service`
- **controllers.orders.logistics_partner_controller**
    - `services.orders.logistics_partner_service`
- **controllers.orders.orders_controller**
    - `services.orders.orders_service`
- **controllers.orders.returns_controller**
    - `services.orders.returns_controller_service`

## security

- **controllers.security.admin_users**
    - `services.common.db_read`
- **controllers.security.auth_controller**
    - `services.security.auth_controller_service`
- **controllers.security.risk_controller**
    - `services.security.risk_service`

## supplier

- **controllers.supplier.supplier_controller**
    - `services.supplier.supplier_service`
- **controllers.supplier.supplier_document_controller**
    - `services.supplier.supplier_document_controller_service`

## treasury

- **controllers.treasury.cash_management_controller**
    - `services.treasury.cash_management_controller_service`
- **controllers.treasury.cash_management_write_controller**
    - `services.finance.cash_management_write_service`
- **controllers.treasury.payout_approval_controller**
    - `services.treasury.payout_approval_write_service`

---

- Controllers importing services directly: **147**
- Facade/re-export controllers: **1**
- Delegating controllers (review manually): **4** -> controllers.admin.auth, controllers.finance.expense_controller, controllers.governance.compliance_controller, controllers.governance.operational_controller
- Total controller modules mapped: **152**
