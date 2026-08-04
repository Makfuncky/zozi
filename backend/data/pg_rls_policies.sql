<<<<<<< Updated upstream
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
=======
-- RLS Policies for ZOZI Multi-Country Platform
-- AUTO-GENERATED from COUNTRY_AWARE_TABLES registry
-- Date: 2026-08-01 02:50:07
-- DO NOT EDIT MANUALLY — regenerate after schema changes
--
-- This file enables Row-Level Security on all country-scoped tables.
-- Each policy ensures data isolation between countries.
-- Run this after applying migrations to enforce RLS.

-- Enable RLS extension and auth function
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION auth.country_access_check(p_country_code TEXT)
RETURNS BOOLEAN AS \$\$
DECLARE
    v_role TEXT;
BEGIN
    SELECT current_user INTO v_role;

    IF v_role = \'admin\' OR v_role = \'postgres\' OR v_role = \'service_role\' THEN
        RETURN TRUE;
    END IF;

    RETURN EXISTS (
        SELECT 1
        FROM configuration.country_staff_assignments csa
        WHERE csa.country_code = p_country_code
          AND csa.is_active = TRUE
          AND csa.user_id = (
              SELECT u.id FROM core.users u WHERE u.email = current_user LIMIT 1
          )
    );
END;
\$\$ LANGUAGE plpgsql SECURITY DEFINER;

-- RLS Policies for schema: ai\n
CREATE POLICY ai_generation_logs_rls_policy
    ON ai.ai_generation_logs
    FOR ALL
    USING (
        ai.ai_generation_logs.country_code IS NULL
        OR auth.country_access_check(ai.ai_generation_logs.country_code)
    );

CREATE POLICY ai_staging_products_rls_policy
    ON ai.ai_staging_products
    FOR ALL
    USING (
        ai.ai_staging_products.country_code IS NULL
        OR auth.country_access_check(ai.ai_staging_products.country_code)
    );

CREATE POLICY ai_staging_variants_rls_policy
    ON ai.ai_staging_variants
    FOR ALL
    USING (
        ai.ai_staging_variants.country_code IS NULL
        OR auth.country_access_check(ai.ai_staging_variants.country_code)
    );

CREATE POLICY ai_upload_jobs_rls_policy
    ON ai.ai_upload_jobs
    FOR ALL
    USING (
        ai.ai_upload_jobs.country_code IS NULL
        OR auth.country_access_check(ai.ai_upload_jobs.country_code)
    );
-- RLS Policies for schema: analytics\n
CREATE POLICY event_dead_letter_rls_policy
    ON analytics.event_dead_letter
    FOR ALL
    USING (
        analytics.event_dead_letter.country_code IS NULL
        OR auth.country_access_check(analytics.event_dead_letter.country_code)
    );

CREATE POLICY event_retry_queue_rls_policy
    ON analytics.event_retry_queue
    FOR ALL
    USING (
        analytics.event_retry_queue.country_code IS NULL
        OR auth.country_access_check(analytics.event_retry_queue.country_code)
    );

CREATE POLICY executive_news_rls_policy
    ON analytics.executive_news
    FOR ALL
    USING (
        analytics.executive_news.country_code IS NULL
        OR auth.country_access_check(analytics.executive_news.country_code)
    );

CREATE POLICY financial_reports_rls_policy
    ON analytics.financial_reports
    FOR ALL
    USING (
        analytics.financial_reports.country_code IS NULL
        OR auth.country_access_check(analytics.financial_reports.country_code)
    );

CREATE POLICY inbox_events_rls_policy
    ON analytics.inbox_events
    FOR ALL
    USING (
        analytics.inbox_events.country_code IS NULL
        OR auth.country_access_check(analytics.inbox_events.country_code)
    );

CREATE POLICY kpi_conversion_rls_policy
    ON analytics.kpi_conversion
    FOR ALL
    USING (
        analytics.kpi_conversion.country_code IS NULL
        OR auth.country_access_check(analytics.kpi_conversion.country_code)
    );

CREATE POLICY kpi_country_rls_policy
    ON analytics.kpi_country
    FOR ALL
    USING (
        analytics.kpi_country.country_code IS NULL
        OR auth.country_access_check(analytics.kpi_country.country_code)
    );

CREATE POLICY kpi_customer_rls_policy
    ON analytics.kpi_customer
    FOR ALL
    USING (
        analytics.kpi_customer.country_code IS NULL
        OR auth.country_access_check(analytics.kpi_customer.country_code)
    );

CREATE POLICY kpi_orders_rls_policy
    ON analytics.kpi_orders
    FOR ALL
    USING (
        analytics.kpi_orders.country_code IS NULL
        OR auth.country_access_check(analytics.kpi_orders.country_code)
    );

CREATE POLICY kpi_retention_rls_policy
    ON analytics.kpi_retention
    FOR ALL
    USING (
        analytics.kpi_retention.country_code IS NULL
        OR auth.country_access_check(analytics.kpi_retention.country_code)
    );

CREATE POLICY kpi_revenue_rls_policy
    ON analytics.kpi_revenue
    FOR ALL
    USING (
        analytics.kpi_revenue.country_code IS NULL
        OR auth.country_access_check(analytics.kpi_revenue.country_code)
    );

CREATE POLICY kpi_supplier_rls_policy
    ON analytics.kpi_supplier
    FOR ALL
    USING (
        analytics.kpi_supplier.country_code IS NULL
        OR auth.country_access_check(analytics.kpi_supplier.country_code)
    );

CREATE POLICY mv_cash_position_rls_policy
    ON analytics.mv_cash_position
    FOR ALL
    USING (
        analytics.mv_cash_position.country_code IS NULL
        OR auth.country_access_check(analytics.mv_cash_position.country_code)
    );

CREATE POLICY mv_daily_sales_rls_policy
    ON analytics.mv_daily_sales
    FOR ALL
    USING (
        analytics.mv_daily_sales.country_code IS NULL
        OR auth.country_access_check(analytics.mv_daily_sales.country_code)
    );

CREATE POLICY mv_facet_counts_rls_policy
    ON analytics.mv_facet_counts
    FOR ALL
    USING (
        analytics.mv_facet_counts.country_code IS NULL
        OR auth.country_access_check(analytics.mv_facet_counts.country_code)
    );

CREATE POLICY mv_monthly_sales_rls_policy
    ON analytics.mv_monthly_sales
    FOR ALL
    USING (
        analytics.mv_monthly_sales.country_code IS NULL
        OR auth.country_access_check(analytics.mv_monthly_sales.country_code)
    );

CREATE POLICY normalized_webhook_events_rls_policy
    ON analytics.normalized_webhook_events
    FOR ALL
    USING (
        analytics.normalized_webhook_events.country_code IS NULL
        OR auth.country_access_check(analytics.normalized_webhook_events.country_code)
    );

CREATE POLICY outbox_events_rls_policy
    ON analytics.outbox_events
    FOR ALL
    USING (
        analytics.outbox_events.country_code IS NULL
        OR auth.country_access_check(analytics.outbox_events.country_code)
    );

CREATE POLICY processed_webhook_events_rls_policy
    ON analytics.processed_webhook_events
    FOR ALL
    USING (
        analytics.processed_webhook_events.country_code IS NULL
        OR auth.country_access_check(analytics.processed_webhook_events.country_code)
    );
-- RLS Policies for schema: audit\n
CREATE POLICY admin_activity_logs_rls_policy
    ON audit.admin_activity_logs
    FOR ALL
    USING (
        audit.admin_activity_logs.country_code IS NULL
        OR auth.country_access_check(audit.admin_activity_logs.country_code)
    );

CREATE POLICY admin_analytics_snapshots_rls_policy
    ON audit.admin_analytics_snapshots
    FOR ALL
    USING (
        audit.admin_analytics_snapshots.country_code IS NULL
        OR auth.country_access_check(audit.admin_analytics_snapshots.country_code)
    );

CREATE POLICY admin_change_audit_logs_rls_policy
    ON audit.admin_change_audit_logs
    FOR ALL
    USING (
        audit.admin_change_audit_logs.country_code IS NULL
        OR auth.country_access_check(audit.admin_change_audit_logs.country_code)
    );

CREATE POLICY chatbot_query_events_rls_policy
    ON audit.chatbot_query_events
    FOR ALL
    USING (
        audit.chatbot_query_events.country_code IS NULL
        OR auth.country_access_check(audit.chatbot_query_events.country_code)
    );

CREATE POLICY retention_job_runs_rls_policy
    ON audit.retention_job_runs
    FOR ALL
    USING (
        audit.retention_job_runs.country_code IS NULL
        OR auth.country_access_check(audit.retention_job_runs.country_code)
    );

CREATE POLICY worm_audit_rls_policy
    ON audit.worm_audit
    FOR ALL
    USING (
        audit.worm_audit.country_code IS NULL
        OR auth.country_access_check(audit.worm_audit.country_code)
    );
-- RLS Policies for schema: commerce\n
CREATE POLICY badge_billing_records_rls_policy
    ON commerce.badge_billing_records
    FOR ALL
    USING (
        commerce.badge_billing_records.country_code IS NULL
        OR auth.country_access_check(commerce.badge_billing_records.country_code)
    );

CREATE POLICY badge_tiers_rls_policy
    ON commerce.badge_tiers
    FOR ALL
    USING (
        commerce.badge_tiers.country_code IS NULL
        OR auth.country_access_check(commerce.badge_tiers.country_code)
    );

CREATE POLICY badge_transactions_rls_policy
    ON commerce.badge_transactions
    FOR ALL
    USING (
        commerce.badge_transactions.country_code IS NULL
        OR auth.country_access_check(commerce.badge_transactions.country_code)
    );

CREATE POLICY banners_rls_policy
    ON commerce.banners
    FOR ALL
    USING (
        commerce.banners.country_code IS NULL
        OR auth.country_access_check(commerce.banners.country_code)
    );

CREATE POLICY cart_items_rls_policy
    ON commerce.cart_items
    FOR ALL
    USING (
        commerce.cart_items.country_code IS NULL
        OR auth.country_access_check(commerce.cart_items.country_code)
    );

CREATE POLICY carts_rls_policy
    ON commerce.carts
    FOR ALL
    USING (
        commerce.carts.country_code IS NULL
        OR auth.country_access_check(commerce.carts.country_code)
    );

CREATE POLICY categories_rls_policy
    ON commerce.categories
    FOR ALL
    USING (
        commerce.categories.country_code IS NULL
        OR auth.country_access_check(commerce.categories.country_code)
    );

CREATE POLICY commission_agreements_rls_policy
    ON commerce.commission_agreements
    FOR ALL
    USING (
        commerce.commission_agreements.country_code IS NULL
        OR auth.country_access_check(commerce.commission_agreements.country_code)
    );

CREATE POLICY commission_badge_tiers_rls_policy
    ON commerce.commission_badge_tiers
    FOR ALL
    USING (
        commerce.commission_badge_tiers.country_code IS NULL
        OR auth.country_access_check(commerce.commission_badge_tiers.country_code)
    );

CREATE POLICY commission_category_rates_rls_policy
    ON commerce.commission_category_rates
    FOR ALL
    USING (
        commerce.commission_category_rates.country_code IS NULL
        OR auth.country_access_check(commerce.commission_category_rates.country_code)
    );

CREATE POLICY commission_global_configs_rls_policy
    ON commerce.commission_global_configs
    FOR ALL
    USING (
        commerce.commission_global_configs.country_code IS NULL
        OR auth.country_access_check(commerce.commission_global_configs.country_code)
    );

CREATE POLICY commission_ledger_entries_rls_policy
    ON commerce.commission_ledger_entries
    FOR ALL
    USING (
        commerce.commission_ledger_entries.country_code IS NULL
        OR auth.country_access_check(commerce.commission_ledger_entries.country_code)
    );

CREATE POLICY commission_rules_rls_policy
    ON commerce.commission_rules
    FOR ALL
    USING (
        commerce.commission_rules.country_code IS NULL
        OR auth.country_access_check(commerce.commission_rules.country_code)
    );

CREATE POLICY coupon_usage_rls_policy
    ON commerce.coupon_usage
    FOR ALL
    USING (
        commerce.coupon_usage.country_code IS NULL
        OR auth.country_access_check(commerce.coupon_usage.country_code)
    );

CREATE POLICY coupons_rls_policy
    ON commerce.coupons
    FOR ALL
    USING (
        commerce.coupons.country_code IS NULL
        OR auth.country_access_check(commerce.coupons.country_code)
    );

CREATE POLICY flash_sale_items_rls_policy
    ON commerce.flash_sale_items
    FOR ALL
    USING (
        commerce.flash_sale_items.country_code IS NULL
        OR auth.country_access_check(commerce.flash_sale_items.country_code)
    );

CREATE POLICY flash_sales_rls_policy
    ON commerce.flash_sales
    FOR ALL
    USING (
        commerce.flash_sales.country_code IS NULL
        OR auth.country_access_check(commerce.flash_sales.country_code)
    );

CREATE POLICY order_items_rls_policy
    ON commerce.order_items
    FOR ALL
    USING (
        commerce.order_items.country_code IS NULL
        OR auth.country_access_check(commerce.order_items.country_code)
    );

CREATE POLICY order_logistics_allocations_rls_policy
    ON commerce.order_logistics_allocations
    FOR ALL
    USING (
        commerce.order_logistics_allocations.country_code IS NULL
        OR auth.country_access_check(commerce.order_logistics_allocations.country_code)
    );

CREATE POLICY orders_rls_policy
    ON commerce.orders
    FOR ALL
    USING (
        commerce.orders.country_code IS NULL
        OR auth.country_access_check(commerce.orders.country_code)
    );

CREATE POLICY product_commission_overrides_rls_policy
    ON commerce.product_commission_overrides
    FOR ALL
    USING (
        commerce.product_commission_overrides.country_code IS NULL
        OR auth.country_access_check(commerce.product_commission_overrides.country_code)
    );

CREATE POLICY product_filter_metadata_rls_policy
    ON commerce.product_filter_metadata
    FOR ALL
    USING (
        commerce.product_filter_metadata.country_code IS NULL
        OR auth.country_access_check(commerce.product_filter_metadata.country_code)
    );

CREATE POLICY product_filter_options_rls_policy
    ON commerce.product_filter_options
    FOR ALL
    USING (
        commerce.product_filter_options.country_code IS NULL
        OR auth.country_access_check(commerce.product_filter_options.country_code)
    );

CREATE POLICY product_variants_rls_policy
    ON commerce.product_variants
    FOR ALL
    USING (
        commerce.product_variants.country_code IS NULL
        OR auth.country_access_check(commerce.product_variants.country_code)
    );

CREATE POLICY product_verifications_rls_policy
    ON commerce.product_verifications
    FOR ALL
    USING (
        commerce.product_verifications.country_code IS NULL
        OR auth.country_access_check(commerce.product_verifications.country_code)
    );

CREATE POLICY products_rls_policy
    ON commerce.products
    FOR ALL
    USING (
        commerce.products.country_code IS NULL
        OR auth.country_access_check(commerce.products.country_code)
    );

CREATE POLICY promotion_engine_configs_rls_policy
    ON commerce.promotion_engine_configs
    FOR ALL
    USING (
        commerce.promotion_engine_configs.country_code IS NULL
        OR auth.country_access_check(commerce.promotion_engine_configs.country_code)
    );

CREATE POLICY promotion_ledger_entries_rls_policy
    ON commerce.promotion_ledger_entries
    FOR ALL
    USING (
        commerce.promotion_ledger_entries.country_code IS NULL
        OR auth.country_access_check(commerce.promotion_ledger_entries.country_code)
    );

CREATE POLICY promotion_order_tiers_rls_policy
    ON commerce.promotion_order_tiers
    FOR ALL
    USING (
        commerce.promotion_order_tiers.country_code IS NULL
        OR auth.country_access_check(commerce.promotion_order_tiers.country_code)
    );

CREATE POLICY return_requests_rls_policy
    ON commerce.return_requests
    FOR ALL
    USING (
        commerce.return_requests.country_code IS NULL
        OR auth.country_access_check(commerce.return_requests.country_code)
    );

CREATE POLICY reviews_rls_policy
    ON commerce.reviews
    FOR ALL
    USING (
        commerce.reviews.country_code IS NULL
        OR auth.country_access_check(commerce.reviews.country_code)
    );
-- RLS Policies for schema: communication\n
CREATE POLICY email_campaigns_rls_policy
    ON communication.email_campaigns
    FOR ALL
    USING (
        communication.email_campaigns.country_code IS NULL
        OR auth.country_access_check(communication.email_campaigns.country_code)
    );

CREATE POLICY employee_communication_threads_rls_policy
    ON communication.employee_communication_threads
    FOR ALL
    USING (
        communication.employee_communication_threads.country_code IS NULL
        OR auth.country_access_check(communication.employee_communication_threads.country_code)
    );

CREATE POLICY escalation_sla_rules_rls_policy
    ON communication.escalation_sla_rules
    FOR ALL
    USING (
        communication.escalation_sla_rules.country_code IS NULL
        OR auth.country_access_check(communication.escalation_sla_rules.country_code)
    );

CREATE POLICY faqs_rls_policy
    ON communication.faqs
    FOR ALL
    USING (
        communication.faqs.country_code IS NULL
        OR auth.country_access_check(communication.faqs.country_code)
    );

CREATE POLICY group_chat_rooms_rls_policy
    ON communication.group_chat_rooms
    FOR ALL
    USING (
        communication.group_chat_rooms.country_code IS NULL
        OR auth.country_access_check(communication.group_chat_rooms.country_code)
    );

CREATE POLICY internal_channels_rls_policy
    ON communication.internal_channels
    FOR ALL
    USING (
        communication.internal_channels.country_code IS NULL
        OR auth.country_access_check(communication.internal_channels.country_code)
    );

CREATE POLICY internal_emails_rls_policy
    ON communication.internal_emails
    FOR ALL
    USING (
        communication.internal_emails.country_code IS NULL
        OR auth.country_access_check(communication.internal_emails.country_code)
    );

CREATE POLICY notifications_rls_policy
    ON communication.notifications
    FOR ALL
    USING (
        communication.notifications.country_code IS NULL
        OR auth.country_access_check(communication.notifications.country_code)
    );

CREATE POLICY push_notification_tokens_rls_policy
    ON communication.push_notification_tokens
    FOR ALL
    USING (
        communication.push_notification_tokens.country_code IS NULL
        OR auth.country_access_check(communication.push_notification_tokens.country_code)
    );

CREATE POLICY support_ticket_replies_rls_policy
    ON communication.support_ticket_replies
    FOR ALL
    USING (
        communication.support_ticket_replies.country_code IS NULL
        OR auth.country_access_check(communication.support_ticket_replies.country_code)
    );

CREATE POLICY support_tickets_rls_policy
    ON communication.support_tickets
    FOR ALL
    USING (
        communication.support_tickets.country_code IS NULL
        OR auth.country_access_check(communication.support_tickets.country_code)
    );

CREATE POLICY ticket_attachments_rls_policy
    ON communication.ticket_attachments
    FOR ALL
    USING (
        communication.ticket_attachments.country_code IS NULL
        OR auth.country_access_check(communication.ticket_attachments.country_code)
    );

CREATE POLICY ticket_messages_rls_policy
    ON communication.ticket_messages
    FOR ALL
    USING (
        communication.ticket_messages.country_code IS NULL
        OR auth.country_access_check(communication.ticket_messages.country_code)
    );

CREATE POLICY ticket_replies_rls_policy
    ON communication.ticket_replies
    FOR ALL
    USING (
        communication.ticket_replies.country_code IS NULL
        OR auth.country_access_check(communication.ticket_replies.country_code)
    );
-- RLS Policies for schema: configuration\n
CREATE POLICY country_category_tax_rates_rls_policy
    ON configuration.country_category_tax_rates
    FOR ALL
    USING (
        configuration.country_category_tax_rates.country_code IS NULL
        OR auth.country_access_check(configuration.country_category_tax_rates.country_code)
    );

CREATE POLICY country_commission_rate_history_rls_policy
    ON configuration.country_commission_rate_history
    FOR ALL
    USING (
        configuration.country_commission_rate_history.country_code IS NULL
        OR auth.country_access_check(configuration.country_commission_rate_history.country_code)
    );

CREATE POLICY country_commission_rates_rls_policy
    ON configuration.country_commission_rates
    FOR ALL
    USING (
        configuration.country_commission_rates.country_code IS NULL
        OR auth.country_access_check(configuration.country_commission_rates.country_code)
    );

CREATE POLICY country_communication_threads_rls_policy
    ON configuration.country_communication_threads
    FOR ALL
    USING (
        configuration.country_communication_threads.country_code IS NULL
        OR auth.country_access_check(configuration.country_communication_threads.country_code)
    );

CREATE POLICY country_config_versions_rls_policy
    ON configuration.country_config_versions
    FOR ALL
    USING (
        configuration.country_config_versions.country_code IS NULL
        OR auth.country_access_check(configuration.country_config_versions.country_code)
    );

CREATE POLICY country_feature_flags_rls_policy
    ON configuration.country_feature_flags
    FOR ALL
    USING (
        configuration.country_feature_flags.country_code IS NULL
        OR auth.country_access_check(configuration.country_feature_flags.country_code)
    );

CREATE POLICY country_gateway_configs_rls_policy
    ON configuration.country_gateway_configs
    FOR ALL
    USING (
        configuration.country_gateway_configs.country_code IS NULL
        OR auth.country_access_check(configuration.country_gateway_configs.country_code)
    );

CREATE POLICY country_holiday_calendars_rls_policy
    ON configuration.country_holiday_calendars
    FOR ALL
    USING (
        configuration.country_holiday_calendars.country_code IS NULL
        OR auth.country_access_check(configuration.country_holiday_calendars.country_code)
    );

CREATE POLICY country_legal_contracts_rls_policy
    ON configuration.country_legal_contracts
    FOR ALL
    USING (
        configuration.country_legal_contracts.country_code IS NULL
        OR auth.country_access_check(configuration.country_legal_contracts.country_code)
    );

CREATE POLICY country_localization_rls_policy
    ON configuration.country_localization
    FOR ALL
    USING (
        configuration.country_localization.country_code IS NULL
        OR auth.country_access_check(configuration.country_localization.country_code)
    );

CREATE POLICY country_logistics_zones_rls_policy
    ON configuration.country_logistics_zones
    FOR ALL
    USING (
        configuration.country_logistics_zones.country_code IS NULL
        OR auth.country_access_check(configuration.country_logistics_zones.country_code)
    );

CREATE POLICY country_payment_aliases_rls_policy
    ON configuration.country_payment_aliases
    FOR ALL
    USING (
        configuration.country_payment_aliases.country_code IS NULL
        OR auth.country_access_check(configuration.country_payment_aliases.country_code)
    );

CREATE POLICY country_payout_rules_rls_policy
    ON configuration.country_payout_rules
    FOR ALL
    USING (
        configuration.country_payout_rules.country_code IS NULL
        OR auth.country_access_check(configuration.country_payout_rules.country_code)
    );

CREATE POLICY country_staff_assignments_rls_policy
    ON configuration.country_staff_assignments
    FOR ALL
    USING (
        configuration.country_staff_assignments.country_code IS NULL
        OR auth.country_access_check(configuration.country_staff_assignments.country_code)
    );

CREATE POLICY email_provider_configs_rls_policy
    ON configuration.email_provider_configs
    FOR ALL
    USING (
        configuration.email_provider_configs.country_code IS NULL
        OR auth.country_access_check(configuration.email_provider_configs.country_code)
    );

CREATE POLICY feature_flags_rls_policy
    ON configuration.feature_flags
    FOR ALL
    USING (
        configuration.feature_flags.country_code IS NULL
        OR auth.country_access_check(configuration.feature_flags.country_code)
    );

CREATE POLICY system_alerts_rls_policy
    ON configuration.system_alerts
    FOR ALL
    USING (
        configuration.system_alerts.country_code IS NULL
        OR auth.country_access_check(configuration.system_alerts.country_code)
    );

CREATE POLICY system_settings_rls_policy
    ON configuration.system_settings
    FOR ALL
    USING (
        configuration.system_settings.country_code IS NULL
        OR auth.country_access_check(configuration.system_settings.country_code)
    );
-- RLS Policies for schema: core\n
CREATE POLICY api_keys_rls_policy
    ON core.api_keys
    FOR ALL
    USING (
        core.api_keys.country_code IS NULL
        OR auth.country_access_check(core.api_keys.country_code)
    );

CREATE POLICY email_verification_tokens_rls_policy
    ON core.email_verification_tokens
    FOR ALL
    USING (
        core.email_verification_tokens.country_code IS NULL
        OR auth.country_access_check(core.email_verification_tokens.country_code)
    );

CREATE POLICY password_reset_tokens_rls_policy
    ON core.password_reset_tokens
    FOR ALL
    USING (
        core.password_reset_tokens.country_code IS NULL
        OR auth.country_access_check(core.password_reset_tokens.country_code)
    );

CREATE POLICY permission_audit_log_rls_policy
    ON core.permission_audit_log
    FOR ALL
    USING (
        core.permission_audit_log.country_code IS NULL
        OR auth.country_access_check(core.permission_audit_log.country_code)
    );

CREATE POLICY permission_categories_rls_policy
    ON core.permission_categories
    FOR ALL
    USING (
        core.permission_categories.country_code IS NULL
        OR auth.country_access_check(core.permission_categories.country_code)
    );

CREATE POLICY permissions_rls_policy
    ON core.permissions
    FOR ALL
    USING (
        core.permissions.country_code IS NULL
        OR auth.country_access_check(core.permissions.country_code)
    );

CREATE POLICY revoked_tokens_rls_policy
    ON core.revoked_tokens
    FOR ALL
    USING (
        core.revoked_tokens.country_code IS NULL
        OR auth.country_access_check(core.revoked_tokens.country_code)
    );

CREATE POLICY role_permission_assignments_rls_policy
    ON core.role_permission_assignments
    FOR ALL
    USING (
        core.role_permission_assignments.country_code IS NULL
        OR auth.country_access_check(core.role_permission_assignments.country_code)
    );

CREATE POLICY role_permission_settings_rls_policy
    ON core.role_permission_settings
    FOR ALL
    USING (
        core.role_permission_settings.country_code IS NULL
        OR auth.country_access_check(core.role_permission_settings.country_code)
    );

CREATE POLICY user_devices_rls_policy
    ON core.user_devices
    FOR ALL
    USING (
        core.user_devices.country_code IS NULL
        OR auth.country_access_check(core.user_devices.country_code)
    );

CREATE POLICY user_login_history_rls_policy
    ON core.user_login_history
    FOR ALL
    USING (
        core.user_login_history.country_code IS NULL
        OR auth.country_access_check(core.user_login_history.country_code)
    );

CREATE POLICY user_permission_overrides_rls_policy
    ON core.user_permission_overrides
    FOR ALL
    USING (
        core.user_permission_overrides.country_code IS NULL
        OR auth.country_access_check(core.user_permission_overrides.country_code)
    );

CREATE POLICY users_rls_policy
    ON core.users
    FOR ALL
    USING (
        core.users.country_code IS NULL
        OR auth.country_access_check(core.users.country_code)
    );
-- RLS Policies for schema: country\n
CREATE POLICY country_cities_rls_policy
    ON country.country_cities
    FOR ALL
    USING (
        country.country_cities.country_code IS NULL
        OR auth.country_access_check(country.country_cities.country_code)
    );

CREATE POLICY country_communications_rls_policy
    ON country.country_communications
    FOR ALL
    USING (
        country.country_communications.country_code IS NULL
        OR auth.country_access_check(country.country_communications.country_code)
    );

CREATE POLICY country_configs_rls_policy
    ON country.country_configs
    FOR ALL
    USING (
        country.country_configs.code IS NULL
        OR auth.country_access_check(country.country_configs.code)
    );

CREATE POLICY country_economics_rls_policy
    ON country.country_economics
    FOR ALL
    USING (
        country.country_economics.country_code IS NULL
        OR auth.country_access_check(country.country_economics.country_code)
    );

CREATE POLICY country_gateway_credentials_rls_policy
    ON country.country_gateway_credentials
    FOR ALL
    USING (
        country.country_gateway_credentials.country_code IS NULL
        OR auth.country_access_check(country.country_gateway_credentials.country_code)
    );

CREATE POLICY country_legal_rls_policy
    ON country.country_legal
    FOR ALL
    USING (
        country.country_legal.country_code IS NULL
        OR auth.country_access_check(country.country_legal.country_code)
    );

CREATE POLICY country_tax_rls_policy
    ON country.country_tax
    FOR ALL
    USING (
        country.country_tax.country_code IS NULL
        OR auth.country_access_check(country.country_tax.country_code)
    );

CREATE POLICY logistics_partner_kyc_requirements_rls_policy
    ON country.logistics_partner_kyc_requirements
    FOR ALL
    USING (
        country.logistics_partner_kyc_requirements.country_code IS NULL
        OR auth.country_access_check(country.logistics_partner_kyc_requirements.country_code)
    );

CREATE POLICY messages_rls_policy
    ON country.messages
    FOR ALL
    USING (
        country.messages.country_code IS NULL
        OR auth.country_access_check(country.messages.country_code)
    );

CREATE POLICY payout_rule_categories_rls_policy
    ON country.payout_rule_categories
    FOR ALL
    USING (
        country.payout_rule_categories.country_code IS NULL
        OR auth.country_access_check(country.payout_rule_categories.country_code)
    );

CREATE POLICY payout_rule_products_rls_policy
    ON country.payout_rule_products
    FOR ALL
    USING (
        country.payout_rule_products.country_code IS NULL
        OR auth.country_access_check(country.payout_rule_products.country_code)
    );

CREATE POLICY supplier_kyc_requirements_rls_policy
    ON country.supplier_kyc_requirements
    FOR ALL
    USING (
        country.supplier_kyc_requirements.country_code IS NULL
        OR auth.country_access_check(country.supplier_kyc_requirements.country_code)
    );

CREATE POLICY tax_rules_rls_policy
    ON country.tax_rules
    FOR ALL
    USING (
        country.tax_rules.country_code IS NULL
        OR auth.country_access_check(country.tax_rules.country_code)
    );
-- RLS Policies for schema: customer\n
CREATE POLICY addresses_rls_policy
    ON customer.addresses
    FOR ALL
    USING (
        customer.addresses.country_code IS NULL
        OR auth.country_access_check(customer.addresses.country_code)
    );

CREATE POLICY direct_chat_rooms_rls_policy
    ON customer.direct_chat_rooms
    FOR ALL
    USING (
        customer.direct_chat_rooms.country_code IS NULL
        OR auth.country_access_check(customer.direct_chat_rooms.country_code)
    );

CREATE POLICY news_articles_rls_policy
    ON customer.news_articles
    FOR ALL
    USING (
        customer.news_articles.country_code IS NULL
        OR auth.country_access_check(customer.news_articles.country_code)
    );

CREATE POLICY referral_point_events_rls_policy
    ON customer.referral_point_events
    FOR ALL
    USING (
        customer.referral_point_events.country_code IS NULL
        OR auth.country_access_check(customer.referral_point_events.country_code)
    );

CREATE POLICY referrals_rls_policy
    ON customer.referrals
    FOR ALL
    USING (
        customer.referrals.country_code IS NULL
        OR auth.country_access_check(customer.referrals.country_code)
    );

CREATE POLICY shift_handover_sessions_rls_policy
    ON customer.shift_handover_sessions
    FOR ALL
    USING (
        customer.shift_handover_sessions.country_code IS NULL
        OR auth.country_access_check(customer.shift_handover_sessions.country_code)
    );

CREATE POLICY user_sessions_rls_policy
    ON customer.user_sessions
    FOR ALL
    USING (
        customer.user_sessions.country_code IS NULL
        OR auth.country_access_check(customer.user_sessions.country_code)
    );

CREATE POLICY video_rooms_rls_policy
    ON customer.video_rooms
    FOR ALL
    USING (
        customer.video_rooms.country_code IS NULL
        OR auth.country_access_check(customer.video_rooms.country_code)
    );

CREATE POLICY wishlist_items_rls_policy
    ON customer.wishlist_items
    FOR ALL
    USING (
        customer.wishlist_items.country_code IS NULL
        OR auth.country_access_check(customer.wishlist_items.country_code)
    );

CREATE POLICY wishlists_rls_policy
    ON customer.wishlists
    FOR ALL
    USING (
        customer.wishlists.country_code IS NULL
        OR auth.country_access_check(customer.wishlists.country_code)
    );
-- RLS Policies for schema: finance\n
CREATE POLICY account_balances_rls_policy
    ON finance.account_balances
    FOR ALL
    USING (
        finance.account_balances.country_code IS NULL
        OR auth.country_access_check(finance.account_balances.country_code)
    );

CREATE POLICY account_groups_rls_policy
    ON finance.account_groups
    FOR ALL
    USING (
        finance.account_groups.country_code IS NULL
        OR auth.country_access_check(finance.account_groups.country_code)
    );

CREATE POLICY accounts_rls_policy
    ON finance.accounts
    FOR ALL
    USING (
        finance.accounts.country_code IS NULL
        OR auth.country_access_check(finance.accounts.country_code)
    );

CREATE POLICY accruals_rls_policy
    ON finance.accruals
    FOR ALL
    USING (
        finance.accruals.country_code IS NULL
        OR auth.country_access_check(finance.accruals.country_code)
    );

CREATE POLICY ap_bills_rls_policy
    ON finance.ap_bills
    FOR ALL
    USING (
        finance.ap_bills.country_code IS NULL
        OR auth.country_access_check(finance.ap_bills.country_code)
    );

CREATE POLICY ap_ledger_entries_rls_policy
    ON finance.ap_ledger_entries
    FOR ALL
    USING (
        finance.ap_ledger_entries.country_code IS NULL
        OR auth.country_access_check(finance.ap_ledger_entries.country_code)
    );

CREATE POLICY ar_invoices_rls_policy
    ON finance.ar_invoices
    FOR ALL
    USING (
        finance.ar_invoices.country_code IS NULL
        OR auth.country_access_check(finance.ar_invoices.country_code)
    );

CREATE POLICY ar_ledger_entries_rls_policy
    ON finance.ar_ledger_entries
    FOR ALL
    USING (
        finance.ar_ledger_entries.country_code IS NULL
        OR auth.country_access_check(finance.ar_ledger_entries.country_code)
    );

CREATE POLICY bank_accounts_rls_policy
    ON finance.bank_accounts
    FOR ALL
    USING (
        finance.bank_accounts.country_code IS NULL
        OR auth.country_access_check(finance.bank_accounts.country_code)
    );

CREATE POLICY bank_mapping_rules_rls_policy
    ON finance.bank_mapping_rules
    FOR ALL
    USING (
        finance.bank_mapping_rules.country_code IS NULL
        OR auth.country_access_check(finance.bank_mapping_rules.country_code)
    );

CREATE POLICY bank_reconciliations_rls_policy
    ON finance.bank_reconciliations
    FOR ALL
    USING (
        finance.bank_reconciliations.country_code IS NULL
        OR auth.country_access_check(finance.bank_reconciliations.country_code)
    );

CREATE POLICY bank_statement_imports_rls_policy
    ON finance.bank_statement_imports
    FOR ALL
    USING (
        finance.bank_statement_imports.country_code IS NULL
        OR auth.country_access_check(finance.bank_statement_imports.country_code)
    );

CREATE POLICY bank_statement_lines_rls_policy
    ON finance.bank_statement_lines
    FOR ALL
    USING (
        finance.bank_statement_lines.country_code IS NULL
        OR auth.country_access_check(finance.bank_statement_lines.country_code)
    );

CREATE POLICY bank_transactions_rls_policy
    ON finance.bank_transactions
    FOR ALL
    USING (
        finance.bank_transactions.country_code IS NULL
        OR auth.country_access_check(finance.bank_transactions.country_code)
    );

CREATE POLICY budgets_rls_policy
    ON finance.budgets
    FOR ALL
    USING (
        finance.budgets.country_code IS NULL
        OR auth.country_access_check(finance.budgets.country_code)
    );

CREATE POLICY cost_centers_rls_policy
    ON finance.cost_centers
    FOR ALL
    USING (
        finance.cost_centers.country_code IS NULL
        OR auth.country_access_check(finance.cost_centers.country_code)
    );

CREATE POLICY customers_rls_policy
    ON finance.customers
    FOR ALL
    USING (
        finance.customers.country_code IS NULL
        OR auth.country_access_check(finance.customers.country_code)
    );

CREATE POLICY finance_audit_logs_rls_policy
    ON finance.finance_audit_logs
    FOR ALL
    USING (
        finance.finance_audit_logs.country_code IS NULL
        OR auth.country_access_check(finance.finance_audit_logs.country_code)
    );

CREATE POLICY finance_automation_logs_rls_policy
    ON finance.finance_automation_logs
    FOR ALL
    USING (
        finance.finance_automation_logs.country_code IS NULL
        OR auth.country_access_check(finance.finance_automation_logs.country_code)
    );

CREATE POLICY finance_dashboard_metrics_rls_policy
    ON finance.finance_dashboard_metrics
    FOR ALL
    USING (
        finance.finance_dashboard_metrics.country_code IS NULL
        OR auth.country_access_check(finance.finance_dashboard_metrics.country_code)
    );

CREATE POLICY finance_reports_rls_policy
    ON finance.finance_reports
    FOR ALL
    USING (
        finance.finance_reports.country_code IS NULL
        OR auth.country_access_check(finance.finance_reports.country_code)
    );

CREATE POLICY fiscal_periods_rls_policy
    ON finance.fiscal_periods
    FOR ALL
    USING (
        finance.fiscal_periods.country_code IS NULL
        OR auth.country_access_check(finance.fiscal_periods.country_code)
    );

CREATE POLICY fixed_assets_rls_policy
    ON finance.fixed_assets
    FOR ALL
    USING (
        finance.fixed_assets.country_code IS NULL
        OR auth.country_access_check(finance.fixed_assets.country_code)
    );

CREATE POLICY invoice_items_rls_policy
    ON finance.invoice_items
    FOR ALL
    USING (
        finance.invoice_items.country_code IS NULL
        OR auth.country_access_check(finance.invoice_items.country_code)
    );

CREATE POLICY invoices_rls_policy
    ON finance.invoices
    FOR ALL
    USING (
        finance.invoices.country_code IS NULL
        OR auth.country_access_check(finance.invoices.country_code)
    );

CREATE POLICY journal_entries_rls_policy
    ON finance.journal_entries
    FOR ALL
    USING (
        finance.journal_entries.country_code IS NULL
        OR auth.country_access_check(finance.journal_entries.country_code)
    );

CREATE POLICY journal_entry_lines_rls_policy
    ON finance.journal_entry_lines
    FOR ALL
    USING (
        finance.journal_entry_lines.country_code IS NULL
        OR auth.country_access_check(finance.journal_entry_lines.country_code)
    );

CREATE POLICY payments_rls_policy
    ON finance.payments
    FOR ALL
    USING (
        finance.payments.country_code IS NULL
        OR auth.country_access_check(finance.payments.country_code)
    );

CREATE POLICY pending_journal_entries_rls_policy
    ON finance.pending_journal_entries
    FOR ALL
    USING (
        finance.pending_journal_entries.country_code IS NULL
        OR auth.country_access_check(finance.pending_journal_entries.country_code)
    );

CREATE POLICY recurring_templates_rls_policy
    ON finance.recurring_templates
    FOR ALL
    USING (
        finance.recurring_templates.country_code IS NULL
        OR auth.country_access_check(finance.recurring_templates.country_code)
    );

CREATE POLICY refund_ledger_rls_policy
    ON finance.refund_ledger
    FOR ALL
    USING (
        finance.refund_ledger.country_code IS NULL
        OR auth.country_access_check(finance.refund_ledger.country_code)
    );

CREATE POLICY scanned_expenses_rls_policy
    ON finance.scanned_expenses
    FOR ALL
    USING (
        finance.scanned_expenses.country_code IS NULL
        OR auth.country_access_check(finance.scanned_expenses.country_code)
    );

CREATE POLICY supplier_settlements_rls_policy
    ON finance.supplier_settlements
    FOR ALL
    USING (
        finance.supplier_settlements.country_code IS NULL
        OR auth.country_access_check(finance.supplier_settlements.country_code)
    );

CREATE POLICY trade_deal_items_rls_policy
    ON finance.trade_deal_items
    FOR ALL
    USING (
        finance.trade_deal_items.country_code IS NULL
        OR auth.country_access_check(finance.trade_deal_items.country_code)
    );

CREATE POLICY trade_deals_rls_policy
    ON finance.trade_deals
    FOR ALL
    USING (
        finance.trade_deals.country_code IS NULL
        OR auth.country_access_check(finance.trade_deals.country_code)
    );

CREATE POLICY trade_settlements_rls_policy
    ON finance.trade_settlements
    FOR ALL
    USING (
        finance.trade_settlements.country_code IS NULL
        OR auth.country_access_check(finance.trade_settlements.country_code)
    );

CREATE POLICY trading_configs_rls_policy
    ON finance.trading_configs
    FOR ALL
    USING (
        finance.trading_configs.country_code IS NULL
        OR auth.country_access_check(finance.trading_configs.country_code)
    );

CREATE POLICY transaction_ledgers_rls_policy
    ON finance.transaction_ledgers
    FOR ALL
    USING (
        finance.transaction_ledgers.country_code IS NULL
        OR auth.country_access_check(finance.transaction_ledgers.country_code)
    );

CREATE POLICY vat_remittances_rls_policy
    ON finance.vat_remittances
    FOR ALL
    USING (
        finance.vat_remittances.country_code IS NULL
        OR auth.country_access_check(finance.vat_remittances.country_code)
    );

CREATE POLICY vendors_rls_policy
    ON finance.vendors
    FOR ALL
    USING (
        finance.vendors.country_code IS NULL
        OR auth.country_access_check(finance.vendors.country_code)
    );
-- RLS Policies for schema: hr\n
CREATE POLICY alumni_network_rls_policy
    ON hr.alumni_network
    FOR ALL
    USING (
        hr.alumni_network.country_code IS NULL
        OR auth.country_access_check(hr.alumni_network.country_code)
    );

CREATE POLICY coi_reports_rls_policy
    ON hr.coi_reports
    FOR ALL
    USING (
        hr.coi_reports.country_code IS NULL
        OR auth.country_access_check(hr.coi_reports.country_code)
    );

CREATE POLICY country_map_configs_rls_policy
    ON hr.country_map_configs
    FOR ALL
    USING (
        hr.country_map_configs.country_code IS NULL
        OR auth.country_access_check(hr.country_map_configs.country_code)
    );

CREATE POLICY data_residency_records_rls_policy
    ON hr.data_residency_records
    FOR ALL
    USING (
        hr.data_residency_records.country_code IS NULL
        OR auth.country_access_check(hr.data_residency_records.country_code)
    );

CREATE POLICY disciplinary_cases_rls_policy
    ON hr.disciplinary_cases
    FOR ALL
    USING (
        hr.disciplinary_cases.country_code IS NULL
        OR auth.country_access_check(hr.disciplinary_cases.country_code)
    );

CREATE POLICY employee_addresses_rls_policy
    ON hr.employee_addresses
    FOR ALL
    USING (
        hr.employee_addresses.country_code IS NULL
        OR auth.country_access_check(hr.employee_addresses.country_code)
    );

CREATE POLICY employee_assets_rls_policy
    ON hr.employee_assets
    FOR ALL
    USING (
        hr.employee_assets.country_code IS NULL
        OR auth.country_access_check(hr.employee_assets.country_code)
    );

CREATE POLICY employee_biometrics_rls_policy
    ON hr.employee_biometrics
    FOR ALL
    USING (
        hr.employee_biometrics.country_code IS NULL
        OR auth.country_access_check(hr.employee_biometrics.country_code)
    );

CREATE POLICY employee_certifications_rls_policy
    ON hr.employee_certifications
    FOR ALL
    USING (
        hr.employee_certifications.country_code IS NULL
        OR auth.country_access_check(hr.employee_certifications.country_code)
    );

CREATE POLICY employee_dependents_rls_policy
    ON hr.employee_dependents
    FOR ALL
    USING (
        hr.employee_dependents.country_code IS NULL
        OR auth.country_access_check(hr.employee_dependents.country_code)
    );

CREATE POLICY employee_documents_rls_policy
    ON hr.employee_documents
    FOR ALL
    USING (
        hr.employee_documents.country_code IS NULL
        OR auth.country_access_check(hr.employee_documents.country_code)
    );

CREATE POLICY employee_expenses_rls_policy
    ON hr.employee_expenses
    FOR ALL
    USING (
        hr.employee_expenses.country_code IS NULL
        OR auth.country_access_check(hr.employee_expenses.country_code)
    );

CREATE POLICY employee_leave_requests_rls_policy
    ON hr.employee_leave_requests
    FOR ALL
    USING (
        hr.employee_leave_requests.country_code IS NULL
        OR auth.country_access_check(hr.employee_leave_requests.country_code)
    );

CREATE POLICY employee_relations_rls_policy
    ON hr.employee_relations
    FOR ALL
    USING (
        hr.employee_relations.country_code IS NULL
        OR auth.country_access_check(hr.employee_relations.country_code)
    );

CREATE POLICY employee_roles_rls_policy
    ON hr.employee_roles
    FOR ALL
    USING (
        hr.employee_roles.country_code IS NULL
        OR auth.country_access_check(hr.employee_roles.country_code)
    );

CREATE POLICY employee_travel_requests_rls_policy
    ON hr.employee_travel_requests
    FOR ALL
    USING (
        hr.employee_travel_requests.country_code IS NULL
        OR auth.country_access_check(hr.employee_travel_requests.country_code)
    );

CREATE POLICY employee_work_logs_rls_policy
    ON hr.employee_work_logs
    FOR ALL
    USING (
        hr.employee_work_logs.country_code IS NULL
        OR auth.country_access_check(hr.employee_work_logs.country_code)
    );

CREATE POLICY legal_contract_templates_rls_policy
    ON hr.legal_contract_templates
    FOR ALL
    USING (
        hr.legal_contract_templates.country_code IS NULL
        OR auth.country_access_check(hr.legal_contract_templates.country_code)
    );

CREATE POLICY logistics_partner_locations_rls_policy
    ON hr.logistics_partner_locations
    FOR ALL
    USING (
        hr.logistics_partner_locations.country_code IS NULL
        OR auth.country_access_check(hr.logistics_partner_locations.country_code)
    );

CREATE POLICY offboarding_cases_rls_policy
    ON hr.offboarding_cases
    FOR ALL
    USING (
        hr.offboarding_cases.country_code IS NULL
        OR auth.country_access_check(hr.offboarding_cases.country_code)
    );

CREATE POLICY org_units_rls_policy
    ON hr.org_units
    FOR ALL
    USING (
        hr.org_units.country_code IS NULL
        OR auth.country_access_check(hr.org_units.country_code)
    );

CREATE POLICY parcel_location_trackers_rls_policy
    ON hr.parcel_location_trackers
    FOR ALL
    USING (
        hr.parcel_location_trackers.country_code IS NULL
        OR auth.country_access_check(hr.parcel_location_trackers.country_code)
    );

CREATE POLICY payment_orchestrator_sync_rls_policy
    ON hr.payment_orchestrator_sync
    FOR ALL
    USING (
        hr.payment_orchestrator_sync.country_code IS NULL
        OR auth.country_access_check(hr.payment_orchestrator_sync.country_code)
    );

CREATE POLICY physical_id_cards_rls_policy
    ON hr.physical_id_cards
    FOR ALL
    USING (
        hr.physical_id_cards.country_code IS NULL
        OR auth.country_access_check(hr.physical_id_cards.country_code)
    );

CREATE POLICY shift_handover_logs_rls_policy
    ON hr.shift_handover_logs
    FOR ALL
    USING (
        hr.shift_handover_logs.country_code IS NULL
        OR auth.country_access_check(hr.shift_handover_logs.country_code)
    );

CREATE POLICY shop_warehouse_locations_rls_policy
    ON hr.shop_warehouse_locations
    FOR ALL
    USING (
        hr.shop_warehouse_locations.country_code IS NULL
        OR auth.country_access_check(hr.shop_warehouse_locations.country_code)
    );

CREATE POLICY supplier_onboarding_sync_rls_policy
    ON hr.supplier_onboarding_sync
    FOR ALL
    USING (
        hr.supplier_onboarding_sync.country_code IS NULL
        OR auth.country_access_check(hr.supplier_onboarding_sync.country_code)
    );
-- RLS Policies for schema: logistics\n
CREATE POLICY dynamic_qr_sessions_rls_policy
    ON logistics.dynamic_qr_sessions
    FOR ALL
    USING (
        logistics.dynamic_qr_sessions.country_code IS NULL
        OR auth.country_access_check(logistics.dynamic_qr_sessions.country_code)
    );

CREATE POLICY employee_attendance_rls_policy
    ON logistics.employee_attendance
    FOR ALL
    USING (
        logistics.employee_attendance.country_code IS NULL
        OR auth.country_access_check(logistics.employee_attendance.country_code)
    );

CREATE POLICY employee_leave_ledgers_rls_policy
    ON logistics.employee_leave_ledgers
    FOR ALL
    USING (
        logistics.employee_leave_ledgers.country_code IS NULL
        OR auth.country_access_check(logistics.employee_leave_ledgers.country_code)
    );

CREATE POLICY employee_shift_rosters_rls_policy
    ON logistics.employee_shift_rosters
    FOR ALL
    USING (
        logistics.employee_shift_rosters.country_code IS NULL
        OR auth.country_access_check(logistics.employee_shift_rosters.country_code)
    );

CREATE POLICY employees_rls_policy
    ON logistics.employees
    FOR ALL
    USING (
        logistics.employees.country_code IS NULL
        OR auth.country_access_check(logistics.employees.country_code)
    );

CREATE POLICY geo_fence_logs_rls_policy
    ON logistics.geo_fence_logs
    FOR ALL
    USING (
        logistics.geo_fence_logs.country_code IS NULL
        OR auth.country_access_check(logistics.geo_fence_logs.country_code)
    );

CREATE POLICY logistics_category_pricing_rules_rls_policy
    ON logistics.logistics_category_pricing_rules
    FOR ALL
    USING (
        logistics.logistics_category_pricing_rules.country_code IS NULL
        OR auth.country_access_check(logistics.logistics_category_pricing_rules.country_code)
    );

CREATE POLICY logistics_cod_remittance_receipts_rls_policy
    ON logistics.logistics_cod_remittance_receipts
    FOR ALL
    USING (
        logistics.logistics_cod_remittance_receipts.country_code IS NULL
        OR auth.country_access_check(logistics.logistics_cod_remittance_receipts.country_code)
    );

CREATE POLICY logistics_fraud_indicators_rls_policy
    ON logistics.logistics_fraud_indicators
    FOR ALL
    USING (
        logistics.logistics_fraud_indicators.country_code IS NULL
        OR auth.country_access_check(logistics.logistics_fraud_indicators.country_code)
    );

CREATE POLICY logistics_partner_bank_accounts_rls_policy
    ON logistics.logistics_partner_bank_accounts
    FOR ALL
    USING (
        logistics.logistics_partner_bank_accounts.country_code IS NULL
        OR auth.country_access_check(logistics.logistics_partner_bank_accounts.country_code)
    );

CREATE POLICY logistics_partner_documents_rls_policy
    ON logistics.logistics_partner_documents
    FOR ALL
    USING (
        logistics.logistics_partner_documents.country_code IS NULL
        OR auth.country_access_check(logistics.logistics_partner_documents.country_code)
    );

CREATE POLICY logistics_partner_payouts_rls_policy
    ON logistics.logistics_partner_payouts
    FOR ALL
    USING (
        logistics.logistics_partner_payouts.country_code IS NULL
        OR auth.country_access_check(logistics.logistics_partner_payouts.country_code)
    );

CREATE POLICY logistics_partner_profiles_rls_policy
    ON logistics.logistics_partner_profiles
    FOR ALL
    USING (
        logistics.logistics_partner_profiles.country_code IS NULL
        OR auth.country_access_check(logistics.logistics_partner_profiles.country_code)
    );

CREATE POLICY logistics_partner_service_areas_rls_policy
    ON logistics.logistics_partner_service_areas
    FOR ALL
    USING (
        logistics.logistics_partner_service_areas.country_code IS NULL
        OR auth.country_access_check(logistics.logistics_partner_service_areas.country_code)
    );

CREATE POLICY logistics_partners_rls_policy
    ON logistics.logistics_partners
    FOR ALL
    USING (
        logistics.logistics_partners.country_code IS NULL
        OR auth.country_access_check(logistics.logistics_partners.country_code)
    );

CREATE POLICY logistics_pricing_profiles_rls_policy
    ON logistics.logistics_pricing_profiles
    FOR ALL
    USING (
        logistics.logistics_pricing_profiles.country_code IS NULL
        OR auth.country_access_check(logistics.logistics_pricing_profiles.country_code)
    );

CREATE POLICY logistics_rates_rls_policy
    ON logistics.logistics_rates
    FOR ALL
    USING (
        logistics.logistics_rates.country_code IS NULL
        OR auth.country_access_check(logistics.logistics_rates.country_code)
    );

CREATE POLICY logistics_settlements_rls_policy
    ON logistics.logistics_settlements
    FOR ALL
    USING (
        logistics.logistics_settlements.country_code IS NULL
        OR auth.country_access_check(logistics.logistics_settlements.country_code)
    );

CREATE POLICY logistics_vehicle_rules_rls_policy
    ON logistics.logistics_vehicle_rules
    FOR ALL
    USING (
        logistics.logistics_vehicle_rules.country_code IS NULL
        OR auth.country_access_check(logistics.logistics_vehicle_rules.country_code)
    );

CREATE POLICY offices_rls_policy
    ON logistics.offices
    FOR ALL
    USING (
        logistics.offices.country_code IS NULL
        OR auth.country_access_check(logistics.offices.country_code)
    );

CREATE POLICY shipment_confirmations_rls_policy
    ON logistics.shipment_confirmations
    FOR ALL
    USING (
        logistics.shipment_confirmations.country_code IS NULL
        OR auth.country_access_check(logistics.shipment_confirmations.country_code)
    );

CREATE POLICY shipment_events_rls_policy
    ON logistics.shipment_events
    FOR ALL
    USING (
        logistics.shipment_events.country_code IS NULL
        OR auth.country_access_check(logistics.shipment_events.country_code)
    );

CREATE POLICY shipments_rls_policy
    ON logistics.shipments
    FOR ALL
    USING (
        logistics.shipments.country_code IS NULL
        OR auth.country_access_check(logistics.shipments.country_code)
    );

CREATE POLICY shipping_carriers_rls_policy
    ON logistics.shipping_carriers
    FOR ALL
    USING (
        logistics.shipping_carriers.country_code IS NULL
        OR auth.country_access_check(logistics.shipping_carriers.country_code)
    );

CREATE POLICY shipping_rules_rls_policy
    ON logistics.shipping_rules
    FOR ALL
    USING (
        logistics.shipping_rules.country_code IS NULL
        OR auth.country_access_check(logistics.shipping_rules.country_code)
    );

CREATE POLICY shipping_zones_rls_policy
    ON logistics.shipping_zones
    FOR ALL
    USING (
        logistics.shipping_zones.country_code IS NULL
        OR auth.country_access_check(logistics.shipping_zones.country_code)
    );

CREATE POLICY stock_movements_rls_policy
    ON logistics.stock_movements
    FOR ALL
    USING (
        logistics.stock_movements.country_code IS NULL
        OR auth.country_access_check(logistics.stock_movements.country_code)
    );

CREATE POLICY warehouses_rls_policy
    ON logistics.warehouses
    FOR ALL
    USING (
        logistics.warehouses.country_code IS NULL
        OR auth.country_access_check(logistics.warehouses.country_code)
    );
-- RLS Policies for schema: media\n
CREATE POLICY media_assets_rls_policy
    ON media.media_assets
    FOR ALL
    USING (
        media.media_assets.country_code IS NULL
        OR auth.country_access_check(media.media_assets.country_code)
    );

CREATE POLICY media_upload_sessions_rls_policy
    ON media.media_upload_sessions
    FOR ALL
    USING (
        media.media_upload_sessions.country_code IS NULL
        OR auth.country_access_check(media.media_upload_sessions.country_code)
    );

CREATE POLICY product_videos_rls_policy
    ON media.product_videos
    FOR ALL
    USING (
        media.product_videos.country_code IS NULL
        OR auth.country_access_check(media.product_videos.country_code)
    );

CREATE POLICY video_analytics_rls_policy
    ON media.video_analytics
    FOR ALL
    USING (
        media.video_analytics.country_code IS NULL
        OR auth.country_access_check(media.video_analytics.country_code)
    );
-- RLS Policies for schema: security\n
CREATE POLICY fraud_alerts_rls_policy
    ON security.fraud_alerts
    FOR ALL
    USING (
        security.fraud_alerts.country_code IS NULL
        OR auth.country_access_check(security.fraud_alerts.country_code)
    );

CREATE POLICY fraud_cases_rls_policy
    ON security.fraud_cases
    FOR ALL
    USING (
        security.fraud_cases.country_code IS NULL
        OR auth.country_access_check(security.fraud_cases.country_code)
    );

CREATE POLICY fraud_events_rls_policy
    ON security.fraud_events
    FOR ALL
    USING (
        security.fraud_events.country_code IS NULL
        OR auth.country_access_check(security.fraud_events.country_code)
    );

CREATE POLICY fraud_rules_rls_policy
    ON security.fraud_rules
    FOR ALL
    USING (
        security.fraud_rules.country_code IS NULL
        OR auth.country_access_check(security.fraud_rules.country_code)
    );

CREATE POLICY fraud_scoring_logs_rls_policy
    ON security.fraud_scoring_logs
    FOR ALL
    USING (
        security.fraud_scoring_logs.country_code IS NULL
        OR auth.country_access_check(security.fraud_scoring_logs.country_code)
    );

CREATE POLICY ip_reputations_rls_policy
    ON security.ip_reputations
    FOR ALL
    USING (
        security.ip_reputations.country_code IS NULL
        OR auth.country_access_check(security.ip_reputations.country_code)
    );
-- RLS Policies for schema: supplier\n
CREATE POLICY supplier_bank_accounts_rls_policy
    ON supplier.supplier_bank_accounts
    FOR ALL
    USING (
        supplier.supplier_bank_accounts.country_code IS NULL
        OR auth.country_access_check(supplier.supplier_bank_accounts.country_code)
    );

CREATE POLICY supplier_country_commissions_rls_policy
    ON supplier.supplier_country_commissions
    FOR ALL
    USING (
        supplier.supplier_country_commissions.country_code IS NULL
        OR auth.country_access_check(supplier.supplier_country_commissions.country_code)
    );

CREATE POLICY supplier_disputes_rls_policy
    ON supplier.supplier_disputes
    FOR ALL
    USING (
        supplier.supplier_disputes.country_code IS NULL
        OR auth.country_access_check(supplier.supplier_disputes.country_code)
    );

CREATE POLICY supplier_fraud_indicators_rls_policy
    ON supplier.supplier_fraud_indicators
    FOR ALL
    USING (
        supplier.supplier_fraud_indicators.country_code IS NULL
        OR auth.country_access_check(supplier.supplier_fraud_indicators.country_code)
    );

CREATE POLICY supplier_notification_preferences_rls_policy
    ON supplier.supplier_notification_preferences
    FOR ALL
    USING (
        supplier.supplier_notification_preferences.country_code IS NULL
        OR auth.country_access_check(supplier.supplier_notification_preferences.country_code)
    );

CREATE POLICY supplier_profiles_rls_policy
    ON supplier.supplier_profiles
    FOR ALL
    USING (
        supplier.supplier_profiles.country_code IS NULL
        OR auth.country_access_check(supplier.supplier_profiles.country_code)
    );
-- RLS Policies for schema: trading\n
CREATE POLICY goods_receipt_lines_rls_policy
    ON trading.goods_receipt_lines
    FOR ALL
    USING (
        trading.goods_receipt_lines.country_code IS NULL
        OR auth.country_access_check(trading.goods_receipt_lines.country_code)
    );

CREATE POLICY goods_receipt_notes_rls_policy
    ON trading.goods_receipt_notes
    FOR ALL
    USING (
        trading.goods_receipt_notes.country_code IS NULL
        OR auth.country_access_check(trading.goods_receipt_notes.country_code)
    );

CREATE POLICY purchase_order_lines_rls_policy
    ON trading.purchase_order_lines
    FOR ALL
    USING (
        trading.purchase_order_lines.country_code IS NULL
        OR auth.country_access_check(trading.purchase_order_lines.country_code)
    );

CREATE POLICY purchase_orders_rls_policy
    ON trading.purchase_orders
    FOR ALL
    USING (
        trading.purchase_orders.country_code IS NULL
        OR auth.country_access_check(trading.purchase_orders.country_code)
    );

CREATE POLICY sales_order_lines_rls_policy
    ON trading.sales_order_lines
    FOR ALL
    USING (
        trading.sales_order_lines.country_code IS NULL
        OR auth.country_access_check(trading.sales_order_lines.country_code)
    );

CREATE POLICY sales_orders_rls_policy
    ON trading.sales_orders
    FOR ALL
    USING (
        trading.sales_orders.country_code IS NULL
        OR auth.country_access_check(trading.sales_orders.country_code)
    );
-- RLS Policies for schema: treasury\n
CREATE POLICY cash_accounts_rls_policy
    ON treasury.cash_accounts
    FOR ALL
    USING (
        treasury.cash_accounts.country_code IS NULL
        OR auth.country_access_check(treasury.cash_accounts.country_code)
    );

CREATE POLICY cash_flow_forecasts_rls_policy
    ON treasury.cash_flow_forecasts
    FOR ALL
    USING (
        treasury.cash_flow_forecasts.country_code IS NULL
        OR auth.country_access_check(treasury.cash_flow_forecasts.country_code)
    );

CREATE POLICY cash_position_snapshots_rls_policy
    ON treasury.cash_position_snapshots
    FOR ALL
    USING (
        treasury.cash_position_snapshots.country_code IS NULL
        OR auth.country_access_check(treasury.cash_position_snapshots.country_code)
    );

CREATE POLICY cash_transactions_rls_policy
    ON treasury.cash_transactions
    FOR ALL
    USING (
        treasury.cash_transactions.country_code IS NULL
        OR auth.country_access_check(treasury.cash_transactions.country_code)
    );

CREATE POLICY finance_bank_accounts_rls_policy
    ON treasury.finance_bank_accounts
    FOR ALL
    USING (
        treasury.finance_bank_accounts.country_code IS NULL
        OR auth.country_access_check(treasury.finance_bank_accounts.country_code)
    );

CREATE POLICY gateway_settlement_schedules_rls_policy
    ON treasury.gateway_settlement_schedules
    FOR ALL
    USING (
        treasury.gateway_settlement_schedules.country_code IS NULL
        OR auth.country_access_check(treasury.gateway_settlement_schedules.country_code)
    );

CREATE POLICY payment_gateway_connections_rls_policy
    ON treasury.payment_gateway_connections
    FOR ALL
    USING (
        treasury.payment_gateway_connections.country_code IS NULL
        OR auth.country_access_check(treasury.payment_gateway_connections.country_code)
    );

CREATE POLICY payment_provider_configs_rls_policy
    ON treasury.payment_provider_configs
    FOR ALL
    USING (
        treasury.payment_provider_configs.country_code IS NULL
        OR auth.country_access_check(treasury.payment_provider_configs.country_code)
    );

CREATE POLICY payment_reconciliation_runs_rls_policy
    ON treasury.payment_reconciliation_runs
    FOR ALL
    USING (
        treasury.payment_reconciliation_runs.country_code IS NULL
        OR auth.country_access_check(treasury.payment_reconciliation_runs.country_code)
    );

CREATE POLICY payout_batch_items_rls_policy
    ON treasury.payout_batch_items
    FOR ALL
    USING (
        treasury.payout_batch_items.country_code IS NULL
        OR auth.country_access_check(treasury.payout_batch_items.country_code)
    );

CREATE POLICY payout_batches_rls_policy
    ON treasury.payout_batches
    FOR ALL
    USING (
        treasury.payout_batches.country_code IS NULL
        OR auth.country_access_check(treasury.payout_batches.country_code)
    );

CREATE POLICY payout_rules_rls_policy
    ON treasury.payout_rules
    FOR ALL
    USING (
        treasury.payout_rules.country_code IS NULL
        OR auth.country_access_check(treasury.payout_rules.country_code)
    );

CREATE POLICY payouts_rls_policy
    ON treasury.payouts
    FOR ALL
    USING (
        treasury.payouts.country_code IS NULL
        OR auth.country_access_check(treasury.payouts.country_code)
    );

CREATE POLICY treasury_accounts_rls_policy
    ON treasury.treasury_accounts
    FOR ALL
    USING (
        treasury.treasury_accounts.country_code IS NULL
        OR auth.country_access_check(treasury.treasury_accounts.country_code)
    );

CREATE POLICY treasury_transactions_rls_policy
    ON treasury.treasury_transactions
    FOR ALL
    USING (
        treasury.treasury_transactions.country_code IS NULL
        OR auth.country_access_check(treasury.treasury_transactions.country_code)
    );
ALTER TABLE ai.ai_generation_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.ai_generation_logs FORCE ROW LEVEL SECURITY;
ALTER TABLE ai.ai_staging_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.ai_staging_products FORCE ROW LEVEL SECURITY;
ALTER TABLE ai.ai_staging_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.ai_staging_variants FORCE ROW LEVEL SECURITY;
ALTER TABLE ai.ai_upload_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.ai_upload_jobs FORCE ROW LEVEL SECURITY;
ALTER TABLE analytics.event_dead_letter ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.event_dead_letter FORCE ROW LEVEL SECURITY;
ALTER TABLE analytics.event_retry_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.event_retry_queue FORCE ROW LEVEL SECURITY;
ALTER TABLE analytics.executive_news ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.executive_news FORCE ROW LEVEL SECURITY;
ALTER TABLE analytics.financial_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.financial_reports FORCE ROW LEVEL SECURITY;
ALTER TABLE analytics.inbox_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.inbox_events FORCE ROW LEVEL SECURITY;
ALTER TABLE analytics.kpi_conversion ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.kpi_conversion FORCE ROW LEVEL SECURITY;
ALTER TABLE analytics.kpi_country ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.kpi_country FORCE ROW LEVEL SECURITY;
ALTER TABLE analytics.kpi_customer ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.kpi_customer FORCE ROW LEVEL SECURITY;
ALTER TABLE analytics.kpi_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.kpi_orders FORCE ROW LEVEL SECURITY;
ALTER TABLE analytics.kpi_retention ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.kpi_retention FORCE ROW LEVEL SECURITY;
ALTER TABLE analytics.kpi_revenue ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.kpi_revenue FORCE ROW LEVEL SECURITY;
ALTER TABLE analytics.kpi_supplier ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.kpi_supplier FORCE ROW LEVEL SECURITY;
ALTER TABLE analytics.mv_cash_position ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.mv_cash_position FORCE ROW LEVEL SECURITY;
ALTER TABLE analytics.mv_daily_sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.mv_daily_sales FORCE ROW LEVEL SECURITY;
ALTER TABLE analytics.mv_facet_counts ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.mv_facet_counts FORCE ROW LEVEL SECURITY;
ALTER TABLE analytics.mv_monthly_sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.mv_monthly_sales FORCE ROW LEVEL SECURITY;
ALTER TABLE analytics.normalized_webhook_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.normalized_webhook_events FORCE ROW LEVEL SECURITY;
ALTER TABLE analytics.outbox_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.outbox_events FORCE ROW LEVEL SECURITY;
ALTER TABLE analytics.processed_webhook_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.processed_webhook_events FORCE ROW LEVEL SECURITY;
ALTER TABLE audit.admin_activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit.admin_activity_logs FORCE ROW LEVEL SECURITY;
ALTER TABLE audit.admin_analytics_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit.admin_analytics_snapshots FORCE ROW LEVEL SECURITY;
ALTER TABLE audit.admin_change_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit.admin_change_audit_logs FORCE ROW LEVEL SECURITY;
ALTER TABLE audit.chatbot_query_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit.chatbot_query_events FORCE ROW LEVEL SECURITY;
ALTER TABLE audit.retention_job_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit.retention_job_runs FORCE ROW LEVEL SECURITY;
ALTER TABLE audit.worm_audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit.worm_audit FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.badge_billing_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.badge_billing_records FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.badge_tiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.badge_tiers FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.badge_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.badge_transactions FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.banners ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.banners FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.cart_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.cart_items FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.carts ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.carts FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.categories FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.commission_agreements ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.commission_agreements FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.commission_badge_tiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.commission_badge_tiers FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.commission_category_rates ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.commission_category_rates FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.commission_global_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.commission_global_configs FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.commission_ledger_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.commission_ledger_entries FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.commission_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.commission_rules FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.coupon_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.coupon_usage FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.coupons ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.coupons FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.flash_sale_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.flash_sale_items FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.flash_sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.flash_sales FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.order_items FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.order_logistics_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.order_logistics_allocations FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.orders FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.product_commission_overrides ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.product_commission_overrides FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.product_filter_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.product_filter_metadata FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.product_filter_options ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.product_filter_options FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.product_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.product_variants FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.product_verifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.product_verifications FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.products FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.promotion_engine_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.promotion_engine_configs FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.promotion_ledger_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.promotion_ledger_entries FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.promotion_order_tiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.promotion_order_tiers FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.return_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.return_requests FORCE ROW LEVEL SECURITY;
ALTER TABLE commerce.reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE commerce.reviews FORCE ROW LEVEL SECURITY;
ALTER TABLE communication.email_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.email_campaigns FORCE ROW LEVEL SECURITY;
ALTER TABLE communication.employee_communication_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.employee_communication_threads FORCE ROW LEVEL SECURITY;
ALTER TABLE communication.escalation_sla_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.escalation_sla_rules FORCE ROW LEVEL SECURITY;
ALTER TABLE communication.faqs ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.faqs FORCE ROW LEVEL SECURITY;
ALTER TABLE communication.group_chat_rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.group_chat_rooms FORCE ROW LEVEL SECURITY;
ALTER TABLE communication.internal_channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.internal_channels FORCE ROW LEVEL SECURITY;
ALTER TABLE communication.internal_emails ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.internal_emails FORCE ROW LEVEL SECURITY;
ALTER TABLE communication.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.notifications FORCE ROW LEVEL SECURITY;
ALTER TABLE communication.push_notification_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.push_notification_tokens FORCE ROW LEVEL SECURITY;
ALTER TABLE communication.support_ticket_replies ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.support_ticket_replies FORCE ROW LEVEL SECURITY;
ALTER TABLE communication.support_tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.support_tickets FORCE ROW LEVEL SECURITY;
ALTER TABLE communication.ticket_attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.ticket_attachments FORCE ROW LEVEL SECURITY;
ALTER TABLE communication.ticket_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.ticket_messages FORCE ROW LEVEL SECURITY;
ALTER TABLE communication.ticket_replies ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication.ticket_replies FORCE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_category_tax_rates ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_category_tax_rates FORCE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_commission_rate_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_commission_rate_history FORCE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_commission_rates ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_commission_rates FORCE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_communication_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_communication_threads FORCE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_config_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_config_versions FORCE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_feature_flags ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_feature_flags FORCE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_gateway_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_gateway_configs FORCE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_holiday_calendars ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_holiday_calendars FORCE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_legal_contracts ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_legal_contracts FORCE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_localization ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_localization FORCE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_logistics_zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_logistics_zones FORCE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_payment_aliases ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_payment_aliases FORCE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_payout_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_payout_rules FORCE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_staff_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.country_staff_assignments FORCE ROW LEVEL SECURITY;
ALTER TABLE configuration.email_provider_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.email_provider_configs FORCE ROW LEVEL SECURITY;
ALTER TABLE configuration.feature_flags ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.feature_flags FORCE ROW LEVEL SECURITY;
ALTER TABLE configuration.system_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.system_alerts FORCE ROW LEVEL SECURITY;
ALTER TABLE configuration.system_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration.system_settings FORCE ROW LEVEL SECURITY;
ALTER TABLE core.api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.api_keys FORCE ROW LEVEL SECURITY;
ALTER TABLE core.email_verification_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.email_verification_tokens FORCE ROW LEVEL SECURITY;
ALTER TABLE core.password_reset_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.password_reset_tokens FORCE ROW LEVEL SECURITY;
ALTER TABLE core.permission_audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.permission_audit_log FORCE ROW LEVEL SECURITY;
ALTER TABLE core.permission_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.permission_categories FORCE ROW LEVEL SECURITY;
ALTER TABLE core.permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.permissions FORCE ROW LEVEL SECURITY;
ALTER TABLE core.revoked_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.revoked_tokens FORCE ROW LEVEL SECURITY;
ALTER TABLE core.role_permission_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.role_permission_assignments FORCE ROW LEVEL SECURITY;
ALTER TABLE core.role_permission_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.role_permission_settings FORCE ROW LEVEL SECURITY;
ALTER TABLE core.user_devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.user_devices FORCE ROW LEVEL SECURITY;
ALTER TABLE core.user_login_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.user_login_history FORCE ROW LEVEL SECURITY;
ALTER TABLE core.user_permission_overrides ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.user_permission_overrides FORCE ROW LEVEL SECURITY;
ALTER TABLE core.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.users FORCE ROW LEVEL SECURITY;
ALTER TABLE country.country_cities ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.country_cities FORCE ROW LEVEL SECURITY;
ALTER TABLE country.country_communications ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.country_communications FORCE ROW LEVEL SECURITY;
ALTER TABLE country.country_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.country_configs FORCE ROW LEVEL SECURITY;
ALTER TABLE country.country_economics ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.country_economics FORCE ROW LEVEL SECURITY;
ALTER TABLE country.country_gateway_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.country_gateway_credentials FORCE ROW LEVEL SECURITY;
ALTER TABLE country.country_legal ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.country_legal FORCE ROW LEVEL SECURITY;
ALTER TABLE country.country_tax ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.country_tax FORCE ROW LEVEL SECURITY;
ALTER TABLE country.logistics_partner_kyc_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.logistics_partner_kyc_requirements FORCE ROW LEVEL SECURITY;
ALTER TABLE country.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.messages FORCE ROW LEVEL SECURITY;
ALTER TABLE country.payout_rule_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.payout_rule_categories FORCE ROW LEVEL SECURITY;
ALTER TABLE country.payout_rule_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.payout_rule_products FORCE ROW LEVEL SECURITY;
ALTER TABLE country.supplier_kyc_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.supplier_kyc_requirements FORCE ROW LEVEL SECURITY;
ALTER TABLE country.tax_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE country.tax_rules FORCE ROW LEVEL SECURITY;
ALTER TABLE customer.addresses ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer.addresses FORCE ROW LEVEL SECURITY;
ALTER TABLE customer.direct_chat_rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer.direct_chat_rooms FORCE ROW LEVEL SECURITY;
ALTER TABLE customer.news_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer.news_articles FORCE ROW LEVEL SECURITY;
ALTER TABLE customer.referral_point_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer.referral_point_events FORCE ROW LEVEL SECURITY;
ALTER TABLE customer.referrals ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer.referrals FORCE ROW LEVEL SECURITY;
ALTER TABLE customer.shift_handover_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer.shift_handover_sessions FORCE ROW LEVEL SECURITY;
ALTER TABLE customer.user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer.user_sessions FORCE ROW LEVEL SECURITY;
ALTER TABLE customer.video_rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer.video_rooms FORCE ROW LEVEL SECURITY;
ALTER TABLE customer.wishlist_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer.wishlist_items FORCE ROW LEVEL SECURITY;
ALTER TABLE customer.wishlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer.wishlists FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.account_balances ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.account_balances FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.account_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.account_groups FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.accounts FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.accruals ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.accruals FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.ap_bills ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.ap_bills FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.ap_ledger_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.ap_ledger_entries FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.ar_invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.ar_invoices FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.ar_ledger_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.ar_ledger_entries FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.bank_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.bank_accounts FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.bank_mapping_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.bank_mapping_rules FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.bank_reconciliations ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.bank_reconciliations FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.bank_statement_imports ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.bank_statement_imports FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.bank_statement_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.bank_statement_lines FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.bank_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.bank_transactions FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.budgets FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.cost_centers ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.cost_centers FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.customers FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.finance_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.finance_audit_logs FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.finance_automation_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.finance_automation_logs FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.finance_dashboard_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.finance_dashboard_metrics FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.finance_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.finance_reports FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.fiscal_periods ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.fiscal_periods FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.fixed_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.fixed_assets FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.invoice_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.invoice_items FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.invoices FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.journal_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.journal_entries FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.journal_entry_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.journal_entry_lines FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.payments FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.pending_journal_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.pending_journal_entries FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.recurring_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.recurring_templates FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.refund_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.refund_ledger FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.scanned_expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.scanned_expenses FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.supplier_settlements ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.supplier_settlements FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.trade_deal_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.trade_deal_items FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.trade_deals ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.trade_deals FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.trade_settlements ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.trade_settlements FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.trading_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.trading_configs FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.transaction_ledgers ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.transaction_ledgers FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.vat_remittances ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.vat_remittances FORCE ROW LEVEL SECURITY;
ALTER TABLE finance.vendors ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.vendors FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.alumni_network ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.alumni_network FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.coi_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.coi_reports FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.country_map_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.country_map_configs FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.data_residency_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.data_residency_records FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.disciplinary_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.disciplinary_cases FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_addresses ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_addresses FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_assets FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_biometrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_biometrics FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_certifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_certifications FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_dependents ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_dependents FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_documents FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_expenses FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_leave_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_leave_requests FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_relations ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_relations FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_roles FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_travel_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_travel_requests FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_work_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee_work_logs FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.legal_contract_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.legal_contract_templates FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.logistics_partner_locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.logistics_partner_locations FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.offboarding_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.offboarding_cases FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.org_units ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.org_units FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.parcel_location_trackers ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.parcel_location_trackers FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.payment_orchestrator_sync ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.payment_orchestrator_sync FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.physical_id_cards ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.physical_id_cards FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.shift_handover_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.shift_handover_logs FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.shop_warehouse_locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.shop_warehouse_locations FORCE ROW LEVEL SECURITY;
ALTER TABLE hr.supplier_onboarding_sync ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.supplier_onboarding_sync FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.dynamic_qr_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.dynamic_qr_sessions FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.employee_attendance ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.employee_attendance FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.employee_leave_ledgers ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.employee_leave_ledgers FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.employee_shift_rosters ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.employee_shift_rosters FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.employees FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.geo_fence_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.geo_fence_logs FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_category_pricing_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_category_pricing_rules FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_cod_remittance_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_cod_remittance_receipts FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_fraud_indicators ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_fraud_indicators FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_partner_bank_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_partner_bank_accounts FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_partner_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_partner_documents FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_partner_payouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_partner_payouts FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_partner_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_partner_profiles FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_partner_service_areas ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_partner_service_areas FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_partners ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_partners FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_pricing_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_pricing_profiles FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_rates ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_rates FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_settlements ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_settlements FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_vehicle_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.logistics_vehicle_rules FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.offices ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.offices FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.shipment_confirmations ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.shipment_confirmations FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.shipment_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.shipment_events FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.shipments ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.shipments FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.shipping_carriers ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.shipping_carriers FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.shipping_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.shipping_rules FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.shipping_zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.shipping_zones FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.stock_movements ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.stock_movements FORCE ROW LEVEL SECURITY;
ALTER TABLE logistics.warehouses ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics.warehouses FORCE ROW LEVEL SECURITY;
ALTER TABLE media.media_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE media.media_assets FORCE ROW LEVEL SECURITY;
ALTER TABLE media.media_upload_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE media.media_upload_sessions FORCE ROW LEVEL SECURITY;
ALTER TABLE media.product_videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE media.product_videos FORCE ROW LEVEL SECURITY;
ALTER TABLE media.video_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE media.video_analytics FORCE ROW LEVEL SECURITY;
ALTER TABLE security.fraud_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE security.fraud_alerts FORCE ROW LEVEL SECURITY;
ALTER TABLE security.fraud_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE security.fraud_cases FORCE ROW LEVEL SECURITY;
ALTER TABLE security.fraud_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE security.fraud_events FORCE ROW LEVEL SECURITY;
ALTER TABLE security.fraud_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE security.fraud_rules FORCE ROW LEVEL SECURITY;
ALTER TABLE security.fraud_scoring_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE security.fraud_scoring_logs FORCE ROW LEVEL SECURITY;
ALTER TABLE security.ip_reputations ENABLE ROW LEVEL SECURITY;
ALTER TABLE security.ip_reputations FORCE ROW LEVEL SECURITY;
ALTER TABLE supplier.supplier_bank_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier.supplier_bank_accounts FORCE ROW LEVEL SECURITY;
ALTER TABLE supplier.supplier_country_commissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier.supplier_country_commissions FORCE ROW LEVEL SECURITY;
ALTER TABLE supplier.supplier_disputes ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier.supplier_disputes FORCE ROW LEVEL SECURITY;
ALTER TABLE supplier.supplier_fraud_indicators ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier.supplier_fraud_indicators FORCE ROW LEVEL SECURITY;
ALTER TABLE supplier.supplier_notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier.supplier_notification_preferences FORCE ROW LEVEL SECURITY;
ALTER TABLE supplier.supplier_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier.supplier_profiles FORCE ROW LEVEL SECURITY;
ALTER TABLE trading.goods_receipt_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading.goods_receipt_lines FORCE ROW LEVEL SECURITY;
ALTER TABLE trading.goods_receipt_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading.goods_receipt_notes FORCE ROW LEVEL SECURITY;
ALTER TABLE trading.purchase_order_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading.purchase_order_lines FORCE ROW LEVEL SECURITY;
ALTER TABLE trading.purchase_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading.purchase_orders FORCE ROW LEVEL SECURITY;
ALTER TABLE trading.sales_order_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading.sales_order_lines FORCE ROW LEVEL SECURITY;
ALTER TABLE trading.sales_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading.sales_orders FORCE ROW LEVEL SECURITY;
ALTER TABLE treasury.cash_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.cash_accounts FORCE ROW LEVEL SECURITY;
ALTER TABLE treasury.cash_flow_forecasts ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.cash_flow_forecasts FORCE ROW LEVEL SECURITY;
ALTER TABLE treasury.cash_position_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.cash_position_snapshots FORCE ROW LEVEL SECURITY;
ALTER TABLE treasury.cash_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.cash_transactions FORCE ROW LEVEL SECURITY;
ALTER TABLE treasury.finance_bank_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.finance_bank_accounts FORCE ROW LEVEL SECURITY;
ALTER TABLE treasury.gateway_settlement_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.gateway_settlement_schedules FORCE ROW LEVEL SECURITY;
ALTER TABLE treasury.payment_gateway_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.payment_gateway_connections FORCE ROW LEVEL SECURITY;
ALTER TABLE treasury.payment_provider_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.payment_provider_configs FORCE ROW LEVEL SECURITY;
ALTER TABLE treasury.payment_reconciliation_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.payment_reconciliation_runs FORCE ROW LEVEL SECURITY;
ALTER TABLE treasury.payout_batch_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.payout_batch_items FORCE ROW LEVEL SECURITY;
ALTER TABLE treasury.payout_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.payout_batches FORCE ROW LEVEL SECURITY;
ALTER TABLE treasury.payout_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.payout_rules FORCE ROW LEVEL SECURITY;
ALTER TABLE treasury.payouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.payouts FORCE ROW LEVEL SECURITY;
ALTER TABLE treasury.treasury_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.treasury_accounts FORCE ROW LEVEL SECURITY;
ALTER TABLE treasury.treasury_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury.treasury_transactions FORCE ROW LEVEL SECURITY;
>>>>>>> Stashed changes
