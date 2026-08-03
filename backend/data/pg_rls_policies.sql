-- backend/data/pg_rls_policies.sql
-- Row Level Security (RLS) policies for country-scoped tables.
-- Every table with a country_code column must have RLS enabled so
-- that the session variable app.current_country_code (set by
-- backend/middleware/country_context.py) restricts rows per country.

BEGIN;

ALTER TABLE ai.ai_generation_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.ai_staging_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.ai_staging_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.ai_upload_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.executive_news ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.financial_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.normalized_webhook_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.processed_webhook_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit.admin_activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit.admin_analytics_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit.admin_change_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit.chatbot_query_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit.retention_job_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit.worm_audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.badge_billing_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.badge_tiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.badge_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.banners ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.cart_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.carts ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.commission_agreements ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.commission_badge_tiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.commission_category_rates ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.commission_global_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.commission_ledger_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.commission_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.coupon_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.coupons ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.flash_sale_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.flash_sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.order_logistics_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.product_commission_overrides ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.product_filter_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.product_filter_options ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.product_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.product_verifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.promotion_engine_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.promotion_ledger_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.promotion_order_tiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.return_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.email_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.employee_communication_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.escalation_sla_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.faqs ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.group_chat_rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.internal_channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.internal_emails ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.push_notification_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.support_ticket_replies ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.support_tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.ticket_attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.ticket_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.ticket_replies ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_category_tax_rates ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_commission_rate_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_commission_rates ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_communication_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_config_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_feature_flags ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_gateway_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_holiday_calendars ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_legal_contracts ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_localization ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_logistics_zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_payment_aliases ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_payout_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_staff_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.email_provider_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.event_dead_letter ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.event_retry_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.feature_flags ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.inbox_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.outbox_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.system_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.system_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.email_verification_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.password_reset_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.permission_audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.permission_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.revoked_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.role_permission_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.role_permission_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.user_devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.user_login_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.user_permission_overrides ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.country_cities ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.country_communications ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.country_economics ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.country_gateway_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.country_legal ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.country_tax ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.logistics_partner_kyc_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.payout_rule_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.payout_rule_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.supplier_kyc_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.tax_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer.addresses ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer.direct_chat_rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer.news_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer.referral_point_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer.referrals ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer.shift_handover_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer.user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer.video_rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer.wishlist_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer.wishlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.account_balances ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.account_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.accruals ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.ap_bills ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.ap_ledger_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.ar_invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.ar_ledger_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.bank_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.bank_mapping_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.bank_reconciliations ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.bank_statement_imports ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.bank_statement_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.bank_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.cost_centers ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.finance_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.finance_automation_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.finance_dashboard_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.finance_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.fiscal_periods ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.fixed_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.invoice_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.journal_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.journal_entry_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.pending_journal_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.recurring_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.refund_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.scanned_expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.supplier_settlements ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.trade_deal_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.trade_deals ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.trade_settlements ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.trading_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.transaction_ledgers ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.vat_remittances ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.vendors ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.alumni_network ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.coi_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.country_map_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.data_residency_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.disciplinary_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_addresses ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_biometrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_certifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_dependents ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_leave_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_relations ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_travel_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_work_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.legal_contract_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.logistics_partner_locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.offboarding_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.org_units ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.parcel_location_trackers ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.payment_orchestrator_sync ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.physical_id_cards ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.shift_handover_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.shop_warehouse_locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.supplier_onboarding_sync ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.customs_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.dynamic_qr_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.employee_attendance ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.employee_leave_ledgers ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.employee_shift_rosters ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.geo_fence_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.import_cost_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.import_shipment_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.import_shipments ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.landed_cost_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_category_pricing_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_cod_remittance_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_fraud_indicators ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_partner_bank_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_partner_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_partner_payouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_partner_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_partner_service_areas ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_partners ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_pricing_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_rates ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_settlements ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_vehicle_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.offices ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.shipment_confirmations ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.shipment_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.shipments ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.shipping_carriers ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.shipping_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.shipping_zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.stock_movements ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.warehouses ENABLE ROW LEVEL SECURITY;
ALTER TABLE media.media_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE media.media_upload_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE media.product_videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE media.video_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE kpi_conversion ENABLE ROW LEVEL SECURITY;
ALTER TABLE kpi_country ENABLE ROW LEVEL SECURITY;
ALTER TABLE kpi_customer ENABLE ROW LEVEL SECURITY;
ALTER TABLE kpi_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE kpi_retention ENABLE ROW LEVEL SECURITY;
ALTER TABLE kpi_revenue ENABLE ROW LEVEL SECURITY;
ALTER TABLE kpi_supplier ENABLE ROW LEVEL SECURITY;
ALTER TABLE mv_cash_position ENABLE ROW LEVEL SECURITY;
ALTER TABLE mv_daily_sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE mv_facet_counts ENABLE ROW LEVEL SECURITY;
ALTER TABLE mv_monthly_sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_gateway_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE security.fraud_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE security.fraud_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE security.fraud_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE security.fraud_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE security.fraud_scoring_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE security.ip_reputations ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier.supplier_bank_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier.supplier_country_commissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier.supplier_disputes ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier.supplier_fraud_indicators ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier.supplier_notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier.supplier_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading.goods_receipt_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading.goods_receipt_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading.purchase_order_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading.purchase_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading.sales_order_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading.sales_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.cash_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.cash_flow_forecasts ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.cash_position_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.cash_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.finance_bank_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.gateway_settlement_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.payment_provider_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.payment_reconciliation_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.payout_batch_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.payout_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.payout_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.payouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.treasury_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.treasury_transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY country_isolation ON ai.ai_generation_logs FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON ai.ai_staging_products FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON ai.ai_staging_variants FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON ai.ai_upload_jobs FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON analytics.executive_news FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON analytics.financial_reports FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON analytics.normalized_webhook_events FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON analytics.processed_webhook_events FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON audit.admin_activity_logs FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON audit.admin_analytics_snapshots FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON audit.admin_change_audit_logs FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON audit.chatbot_query_events FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON audit.retention_job_runs FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON audit.worm_audit FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.badge_billing_records FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.badge_tiers FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.badge_transactions FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.banners FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.cart_items FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.carts FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.categories FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.commission_agreements FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.commission_badge_tiers FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.commission_category_rates FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.commission_global_configs FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.commission_ledger_entries FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.commission_rules FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.coupon_usage FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.coupons FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.flash_sale_items FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.flash_sales FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.order_items FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.order_logistics_allocations FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.orders FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.product_commission_overrides FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.product_filter_metadata FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.product_filter_options FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.product_variants FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.product_verifications FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.products FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.promotion_engine_configs FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.promotion_ledger_entries FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.promotion_order_tiers FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.return_requests FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON commerce.reviews FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON communication.email_campaigns FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON communication.employee_communication_threads FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON communication.escalation_sla_rules FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON communication.faqs FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON communication.group_chat_rooms FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON communication.internal_channels FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON communication.internal_emails FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON communication.notifications FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON communication.push_notification_tokens FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON communication.support_ticket_replies FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON communication.support_tickets FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON communication.ticket_attachments FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON communication.ticket_messages FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON communication.ticket_replies FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.country_category_tax_rates FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.country_commission_rate_history FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.country_commission_rates FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.country_communication_threads FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.country_config_versions FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.country_feature_flags FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.country_gateway_configs FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.country_holiday_calendars FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.country_legal_contracts FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.country_localization FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.country_logistics_zones FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.country_payment_aliases FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.country_payout_rules FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.country_staff_assignments FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.email_provider_configs FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.event_dead_letter FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.event_retry_queue FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.feature_flags FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.inbox_events FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.outbox_events FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.system_alerts FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON configuration.system_settings FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON core.api_keys FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON core.email_verification_tokens FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON core.password_reset_tokens FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON core.permission_audit_log FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON core.permission_categories FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON core.permissions FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON core.revoked_tokens FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON core.role_permission_assignments FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON core.role_permission_settings FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON core.user_devices FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON core.user_login_history FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON core.user_permission_overrides FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON core.users FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON country.country_cities FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON country.country_communications FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON country.country_economics FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON country.country_gateway_credentials FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON country.country_legal FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON country.country_tax FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON country.logistics_partner_kyc_requirements FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON country.messages FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON country.payout_rule_categories FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON country.payout_rule_products FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON country.supplier_kyc_requirements FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON country.tax_rules FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON customer.addresses FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON customer.direct_chat_rooms FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON customer.news_articles FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON customer.referral_point_events FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON customer.referrals FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON customer.shift_handover_sessions FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON customer.user_sessions FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON customer.video_rooms FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON customer.wishlist_items FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON customer.wishlists FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.account_balances FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.account_groups FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.accounts FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.accruals FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.ap_bills FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.ap_ledger_entries FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.ar_invoices FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.ar_ledger_entries FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.bank_accounts FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.bank_mapping_rules FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.bank_reconciliations FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.bank_statement_imports FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.bank_statement_lines FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.bank_transactions FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.budgets FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.cost_centers FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.customers FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.finance_audit_logs FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.finance_automation_logs FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.finance_dashboard_metrics FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.finance_reports FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.fiscal_periods FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.fixed_assets FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.invoice_items FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.invoices FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.journal_entries FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.journal_entry_lines FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.payments FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.pending_journal_entries FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.recurring_templates FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.refund_ledger FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.scanned_expenses FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.supplier_settlements FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.trade_deal_items FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.trade_deals FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.trade_settlements FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.trading_configs FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.transaction_ledgers FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.vat_remittances FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON finance.vendors FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.alumni_network FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.coi_reports FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.country_map_configs FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.data_residency_records FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.disciplinary_cases FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.employee_addresses FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.employee_assets FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.employee_biometrics FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.employee_certifications FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.employee_dependents FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.employee_documents FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.employee_expenses FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.employee_leave_requests FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.employee_relations FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.employee_roles FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.employee_travel_requests FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.employee_work_logs FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.legal_contract_templates FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.logistics_partner_locations FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.offboarding_cases FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.org_units FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.parcel_location_trackers FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.payment_orchestrator_sync FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.physical_id_cards FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.shift_handover_logs FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.shop_warehouse_locations FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON hr.supplier_onboarding_sync FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.customs_entries FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.dynamic_qr_sessions FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.employee_attendance FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.employee_leave_ledgers FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.employee_shift_rosters FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.employees FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.geo_fence_logs FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.import_cost_templates FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.import_shipment_lines FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.import_shipments FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.landed_cost_allocations FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.logistics_category_pricing_rules FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.logistics_cod_remittance_receipts FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.logistics_fraud_indicators FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.logistics_partner_bank_accounts FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.logistics_partner_documents FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.logistics_partner_payouts FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.logistics_partner_profiles FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.logistics_partner_service_areas FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.logistics_partners FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.logistics_pricing_profiles FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.logistics_rates FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.logistics_settlements FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.logistics_vehicle_rules FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.offices FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.shipment_confirmations FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.shipment_events FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.shipments FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.shipping_carriers FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.shipping_rules FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.shipping_zones FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.stock_movements FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON logistics.warehouses FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON media.media_assets FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON media.media_upload_sessions FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON media.product_videos FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON media.video_analytics FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON kpi_conversion FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON kpi_country FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON kpi_customer FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON kpi_orders FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON kpi_retention FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON kpi_revenue FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON kpi_supplier FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON mv_cash_position FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON mv_daily_sales FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON mv_facet_counts FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON mv_monthly_sales FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON payment_gateway_connections FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON security.fraud_alerts FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON security.fraud_cases FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON security.fraud_events FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON security.fraud_rules FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON security.fraud_scoring_logs FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON security.ip_reputations FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON supplier.supplier_bank_accounts FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON supplier.supplier_country_commissions FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON supplier.supplier_disputes FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON supplier.supplier_fraud_indicators FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON supplier.supplier_notification_preferences FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON supplier.supplier_profiles FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON trading.goods_receipt_lines FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON trading.goods_receipt_notes FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON trading.purchase_order_lines FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON trading.purchase_orders FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON trading.sales_order_lines FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON trading.sales_orders FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON treasury.cash_accounts FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON treasury.cash_flow_forecasts FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON treasury.cash_position_snapshots FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON treasury.cash_transactions FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON treasury.finance_bank_accounts FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON treasury.gateway_settlement_schedules FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON treasury.payment_provider_configs FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON treasury.payment_reconciliation_runs FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON treasury.payout_batch_items FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON treasury.payout_batches FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON treasury.payout_rules FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON treasury.payouts FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON treasury.treasury_accounts FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);
CREATE POLICY country_isolation ON treasury.treasury_transactions FOR ALL TO public
    USING (country_code = current_setting('app.current_country_code', true)::text);

COMMIT;