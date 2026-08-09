-- ============================================================================
-- ZOZI Row-Level Security policies (DBA05)
-- ============================================================================
--
-- Country-scoped (multi-tenant) data access is enforced at the database level
-- using the per-request session GUC 'app.current_country_code', which is set
-- transaction-locally by middleware/CountryContextMiddleware.set_session_rls
-- (fail-closed: if the GUC is unset, access to country-aware rows is denied
-- for non-privileged roles).
--
-- This file is the authoritative DB-level RLS definition. It is generated to
-- cover EVERY ORM model that declares a 'country_code' column (238 tables), so
-- no country-scoped table is left unprotected. The app-level enforcer
-- (utils.rls_interceptor.COUNTRY_AWARE_TABLES) is the curated country-scoped
-- subset used by the before_execute hook; global GL master tables
-- (accounts/account_groups/account_balances/accruals/budgets/cost_centers/
-- fixed_assets) are intentionally excluded from the app-level filter but are
-- still covered here with a NULL-safe policy (rows with country_code IS NULL
-- are always permitted).
--
-- Regenerate from the models; keep in sync with COUNTRY_AWARE_TABLES.
-- ============================================================================

CREATE OR REPLACE FUNCTION zozi_rls_check(p_country_code TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    v_role TEXT;
BEGIN
    SELECT current_user INTO v_role;
    IF v_role IN ('admin', 'postgres', 'service_role') THEN
        RETURN TRUE;
    END IF;
    IF current_setting('app.current_country_code', true) IS NULL THEN
        RETURN FALSE;
    END IF;
    RETURN p_country_code = ANY(string_to_array(current_setting('app.current_country_code', true), ','));
END;
$$ LANGUAGE plpgsql STABLE;
-- account_balances.country_code
ALTER TABLE account_balances ENABLE ROW LEVEL SECURITY;
ALTER TABLE account_balances FORCE ROW LEVEL SECURITY;
CREATE POLICY account_balances_country_rls ON account_balances FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- account_groups.country_code
ALTER TABLE account_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE account_groups FORCE ROW LEVEL SECURITY;
CREATE POLICY account_groups_country_rls ON account_groups FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- accounts.country_code
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts FORCE ROW LEVEL SECURITY;
CREATE POLICY accounts_country_rls ON accounts FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- accruals.country_code
ALTER TABLE accruals ENABLE ROW LEVEL SECURITY;
ALTER TABLE accruals FORCE ROW LEVEL SECURITY;
CREATE POLICY accruals_country_rls ON accruals FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- addresses.country_code
ALTER TABLE addresses ENABLE ROW LEVEL SECURITY;
ALTER TABLE addresses FORCE ROW LEVEL SECURITY;
CREATE POLICY addresses_country_rls ON addresses FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- admin_activity_logs.country_code
ALTER TABLE admin_activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_activity_logs FORCE ROW LEVEL SECURITY;
CREATE POLICY admin_activity_logs_country_rls ON admin_activity_logs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- admin_analytics_snapshots.country_code
ALTER TABLE admin_analytics_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_analytics_snapshots FORCE ROW LEVEL SECURITY;
CREATE POLICY admin_analytics_snapshots_country_rls ON admin_analytics_snapshots FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- admin_change_audit_logs.country_code
ALTER TABLE admin_change_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_change_audit_logs FORCE ROW LEVEL SECURITY;
CREATE POLICY admin_change_audit_logs_country_rls ON admin_change_audit_logs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- ai_generation_logs.country_code
ALTER TABLE ai_generation_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_generation_logs FORCE ROW LEVEL SECURITY;
CREATE POLICY ai_generation_logs_country_rls ON ai_generation_logs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- ai_staging_products.country_code
ALTER TABLE ai_staging_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_staging_products FORCE ROW LEVEL SECURITY;
CREATE POLICY ai_staging_products_country_rls ON ai_staging_products FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- ai_staging_variants.country_code
ALTER TABLE ai_staging_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_staging_variants FORCE ROW LEVEL SECURITY;
CREATE POLICY ai_staging_variants_country_rls ON ai_staging_variants FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- ai_upload_jobs.country_code
ALTER TABLE ai_upload_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_upload_jobs FORCE ROW LEVEL SECURITY;
CREATE POLICY ai_upload_jobs_country_rls ON ai_upload_jobs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- alumni_network.country_code
ALTER TABLE alumni_network ENABLE ROW LEVEL SECURITY;
ALTER TABLE alumni_network FORCE ROW LEVEL SECURITY;
CREATE POLICY alumni_network_country_rls ON alumni_network FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- ap_bills.country_code
ALTER TABLE ap_bills ENABLE ROW LEVEL SECURITY;
ALTER TABLE ap_bills FORCE ROW LEVEL SECURITY;
CREATE POLICY ap_bills_country_rls ON ap_bills FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- ap_ledger_entries.country_code
ALTER TABLE ap_ledger_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE ap_ledger_entries FORCE ROW LEVEL SECURITY;
CREATE POLICY ap_ledger_entries_country_rls ON ap_ledger_entries FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- api_keys.country_code
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys FORCE ROW LEVEL SECURITY;
CREATE POLICY api_keys_country_rls ON api_keys FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- ar_invoices.country_code
ALTER TABLE ar_invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE ar_invoices FORCE ROW LEVEL SECURITY;
CREATE POLICY ar_invoices_country_rls ON ar_invoices FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- ar_ledger_entries.country_code
ALTER TABLE ar_ledger_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE ar_ledger_entries FORCE ROW LEVEL SECURITY;
CREATE POLICY ar_ledger_entries_country_rls ON ar_ledger_entries FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- audit_logs.country_code
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs FORCE ROW LEVEL SECURITY;
CREATE POLICY audit_logs_country_rls ON audit_logs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- automation_logs.country_code
ALTER TABLE automation_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation_logs FORCE ROW LEVEL SECURITY;
CREATE POLICY automation_logs_country_rls ON automation_logs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- automation_rules.country_code
ALTER TABLE automation_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation_rules FORCE ROW LEVEL SECURITY;
CREATE POLICY automation_rules_country_rls ON automation_rules FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- badge_billing_records.country_code
ALTER TABLE badge_billing_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE badge_billing_records FORCE ROW LEVEL SECURITY;
CREATE POLICY badge_billing_records_country_rls ON badge_billing_records FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- badge_tiers.country_code
ALTER TABLE badge_tiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE badge_tiers FORCE ROW LEVEL SECURITY;
CREATE POLICY badge_tiers_country_rls ON badge_tiers FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- badge_transactions.country_code
ALTER TABLE badge_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE badge_transactions FORCE ROW LEVEL SECURITY;
CREATE POLICY badge_transactions_country_rls ON badge_transactions FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- bank_accounts.country_code
ALTER TABLE bank_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE bank_accounts FORCE ROW LEVEL SECURITY;
CREATE POLICY bank_accounts_country_rls ON bank_accounts FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- bank_mapping_rules.country_code
ALTER TABLE bank_mapping_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE bank_mapping_rules FORCE ROW LEVEL SECURITY;
CREATE POLICY bank_mapping_rules_country_rls ON bank_mapping_rules FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- bank_reconciliations.country_code
ALTER TABLE bank_reconciliations ENABLE ROW LEVEL SECURITY;
ALTER TABLE bank_reconciliations FORCE ROW LEVEL SECURITY;
CREATE POLICY bank_reconciliations_country_rls ON bank_reconciliations FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- bank_statement_imports.country_code
ALTER TABLE bank_statement_imports ENABLE ROW LEVEL SECURITY;
ALTER TABLE bank_statement_imports FORCE ROW LEVEL SECURITY;
CREATE POLICY bank_statement_imports_country_rls ON bank_statement_imports FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- bank_statement_lines.country_code
ALTER TABLE bank_statement_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE bank_statement_lines FORCE ROW LEVEL SECURITY;
CREATE POLICY bank_statement_lines_country_rls ON bank_statement_lines FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- bank_transactions.country_code
ALTER TABLE bank_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE bank_transactions FORCE ROW LEVEL SECURITY;
CREATE POLICY bank_transactions_country_rls ON bank_transactions FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- banners.country_code
ALTER TABLE banners ENABLE ROW LEVEL SECURITY;
ALTER TABLE banners FORCE ROW LEVEL SECURITY;
CREATE POLICY banners_country_rls ON banners FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- budgets.country_code
ALTER TABLE budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE budgets FORCE ROW LEVEL SECURITY;
CREATE POLICY budgets_country_rls ON budgets FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- cart_items.country_code
ALTER TABLE cart_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE cart_items FORCE ROW LEVEL SECURITY;
CREATE POLICY cart_items_country_rls ON cart_items FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- carts.country_code
ALTER TABLE carts ENABLE ROW LEVEL SECURITY;
ALTER TABLE carts FORCE ROW LEVEL SECURITY;
CREATE POLICY carts_country_rls ON carts FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- cash_accounts.country_code
ALTER TABLE cash_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE cash_accounts FORCE ROW LEVEL SECURITY;
CREATE POLICY cash_accounts_country_rls ON cash_accounts FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- cash_flow_forecasts.country_code
ALTER TABLE cash_flow_forecasts ENABLE ROW LEVEL SECURITY;
ALTER TABLE cash_flow_forecasts FORCE ROW LEVEL SECURITY;
CREATE POLICY cash_flow_forecasts_country_rls ON cash_flow_forecasts FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- cash_position_snapshots.country_code
ALTER TABLE cash_position_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE cash_position_snapshots FORCE ROW LEVEL SECURITY;
CREATE POLICY cash_position_snapshots_country_rls ON cash_position_snapshots FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- cash_transactions.country_code
ALTER TABLE cash_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE cash_transactions FORCE ROW LEVEL SECURITY;
CREATE POLICY cash_transactions_country_rls ON cash_transactions FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- categories.country_code
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories FORCE ROW LEVEL SECURITY;
CREATE POLICY categories_country_rls ON categories FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- chatbot_query_events.country_code
ALTER TABLE chatbot_query_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE chatbot_query_events FORCE ROW LEVEL SECURITY;
CREATE POLICY chatbot_query_events_country_rls ON chatbot_query_events FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- coi_reports.country_code
ALTER TABLE coi_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE coi_reports FORCE ROW LEVEL SECURITY;
CREATE POLICY coi_reports_country_rls ON coi_reports FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- commission_agreements.country_code
ALTER TABLE commission_agreements ENABLE ROW LEVEL SECURITY;
ALTER TABLE commission_agreements FORCE ROW LEVEL SECURITY;
CREATE POLICY commission_agreements_country_rls ON commission_agreements FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- commission_badge_tiers.country_code
ALTER TABLE commission_badge_tiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE commission_badge_tiers FORCE ROW LEVEL SECURITY;
CREATE POLICY commission_badge_tiers_country_rls ON commission_badge_tiers FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- commission_category_rates.country_code
ALTER TABLE commission_category_rates ENABLE ROW LEVEL SECURITY;
ALTER TABLE commission_category_rates FORCE ROW LEVEL SECURITY;
CREATE POLICY commission_category_rates_country_rls ON commission_category_rates FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- commission_global_configs.country_code
ALTER TABLE commission_global_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE commission_global_configs FORCE ROW LEVEL SECURITY;
CREATE POLICY commission_global_configs_country_rls ON commission_global_configs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- commission_ledger_entries.country_code
ALTER TABLE commission_ledger_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE commission_ledger_entries FORCE ROW LEVEL SECURITY;
CREATE POLICY commission_ledger_entries_country_rls ON commission_ledger_entries FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- cost_centers.country_code
ALTER TABLE cost_centers ENABLE ROW LEVEL SECURITY;
ALTER TABLE cost_centers FORCE ROW LEVEL SECURITY;
CREATE POLICY cost_centers_country_rls ON cost_centers FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_category_tax_rates.country_code
ALTER TABLE country_category_tax_rates ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_category_tax_rates FORCE ROW LEVEL SECURITY;
CREATE POLICY country_category_tax_rates_country_rls ON country_category_tax_rates FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_cities.country_code
ALTER TABLE country_cities ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_cities FORCE ROW LEVEL SECURITY;
CREATE POLICY country_cities_country_rls ON country_cities FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_commission_rate_history.country_code
ALTER TABLE country_commission_rate_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_commission_rate_history FORCE ROW LEVEL SECURITY;
CREATE POLICY country_commission_rate_history_country_rls ON country_commission_rate_history FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_commission_rates.country_code
ALTER TABLE country_commission_rates ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_commission_rates FORCE ROW LEVEL SECURITY;
CREATE POLICY country_commission_rates_country_rls ON country_commission_rates FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_communication_threads.country_code
ALTER TABLE country_communication_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_communication_threads FORCE ROW LEVEL SECURITY;
CREATE POLICY country_communication_threads_country_rls ON country_communication_threads FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_communications.country_code
ALTER TABLE country_communications ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_communications FORCE ROW LEVEL SECURITY;
CREATE POLICY country_communications_country_rls ON country_communications FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_config_versions.country_code
ALTER TABLE country_config_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_config_versions FORCE ROW LEVEL SECURITY;
CREATE POLICY country_config_versions_country_rls ON country_config_versions FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_configs.country_code
ALTER TABLE country_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_configs FORCE ROW LEVEL SECURITY;
CREATE POLICY country_configs_country_rls ON country_configs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_economics.country_code
ALTER TABLE country_economics ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_economics FORCE ROW LEVEL SECURITY;
CREATE POLICY country_economics_country_rls ON country_economics FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_feature_flags.country_code
ALTER TABLE country_feature_flags ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_feature_flags FORCE ROW LEVEL SECURITY;
CREATE POLICY country_feature_flags_country_rls ON country_feature_flags FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_gateway_configs.country_code
ALTER TABLE country_gateway_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_gateway_configs FORCE ROW LEVEL SECURITY;
CREATE POLICY country_gateway_configs_country_rls ON country_gateway_configs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_gateway_credentials.country_code
ALTER TABLE country_gateway_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_gateway_credentials FORCE ROW LEVEL SECURITY;
CREATE POLICY country_gateway_credentials_country_rls ON country_gateway_credentials FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_holiday_calendars.country_code
ALTER TABLE country_holiday_calendars ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_holiday_calendars FORCE ROW LEVEL SECURITY;
CREATE POLICY country_holiday_calendars_country_rls ON country_holiday_calendars FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_legal.country_code
ALTER TABLE country_legal ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_legal FORCE ROW LEVEL SECURITY;
CREATE POLICY country_legal_country_rls ON country_legal FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_legal_contracts.country_code
ALTER TABLE country_legal_contracts ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_legal_contracts FORCE ROW LEVEL SECURITY;
CREATE POLICY country_legal_contracts_country_rls ON country_legal_contracts FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_localization.country_code
ALTER TABLE country_localization ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_localization FORCE ROW LEVEL SECURITY;
CREATE POLICY country_localization_country_rls ON country_localization FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_logistics_zones.country_code
ALTER TABLE country_logistics_zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_logistics_zones FORCE ROW LEVEL SECURITY;
CREATE POLICY country_logistics_zones_country_rls ON country_logistics_zones FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_map_configs.country_code
ALTER TABLE country_map_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_map_configs FORCE ROW LEVEL SECURITY;
CREATE POLICY country_map_configs_country_rls ON country_map_configs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_payment_aliases.country_code
ALTER TABLE country_payment_aliases ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_payment_aliases FORCE ROW LEVEL SECURITY;
CREATE POLICY country_payment_aliases_country_rls ON country_payment_aliases FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_payout_rules.country_code
ALTER TABLE country_payout_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_payout_rules FORCE ROW LEVEL SECURITY;
CREATE POLICY country_payout_rules_country_rls ON country_payout_rules FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_staff_assignments.country_code
ALTER TABLE country_staff_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_staff_assignments FORCE ROW LEVEL SECURITY;
CREATE POLICY country_staff_assignments_country_rls ON country_staff_assignments FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- country_tax.country_code
ALTER TABLE country_tax ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_tax FORCE ROW LEVEL SECURITY;
CREATE POLICY country_tax_country_rls ON country_tax FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- coupon_usage.country_code
ALTER TABLE coupon_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE coupon_usage FORCE ROW LEVEL SECURITY;
CREATE POLICY coupon_usage_country_rls ON coupon_usage FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- coupons.country_code
ALTER TABLE coupons ENABLE ROW LEVEL SECURITY;
ALTER TABLE coupons FORCE ROW LEVEL SECURITY;
CREATE POLICY coupons_country_rls ON coupons FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- customers.country_code
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers FORCE ROW LEVEL SECURITY;
CREATE POLICY customers_country_rls ON customers FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- data_residency_records.country_code
ALTER TABLE data_residency_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_residency_records FORCE ROW LEVEL SECURITY;
CREATE POLICY data_residency_records_country_rls ON data_residency_records FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- direct_chat_rooms.country_code
ALTER TABLE direct_chat_rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE direct_chat_rooms FORCE ROW LEVEL SECURITY;
CREATE POLICY direct_chat_rooms_country_rls ON direct_chat_rooms FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- disciplinary_cases.country_code
ALTER TABLE disciplinary_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE disciplinary_cases FORCE ROW LEVEL SECURITY;
CREATE POLICY disciplinary_cases_country_rls ON disciplinary_cases FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- dynamic_qr_sessions.country_code
ALTER TABLE dynamic_qr_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE dynamic_qr_sessions FORCE ROW LEVEL SECURITY;
CREATE POLICY dynamic_qr_sessions_country_rls ON dynamic_qr_sessions FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- email_campaigns.country_code
ALTER TABLE email_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_campaigns FORCE ROW LEVEL SECURITY;
CREATE POLICY email_campaigns_country_rls ON email_campaigns FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- email_provider_configs.country_code
ALTER TABLE email_provider_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_provider_configs FORCE ROW LEVEL SECURITY;
CREATE POLICY email_provider_configs_country_rls ON email_provider_configs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- email_verification_tokens.country_code
ALTER TABLE email_verification_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_verification_tokens FORCE ROW LEVEL SECURITY;
CREATE POLICY email_verification_tokens_country_rls ON email_verification_tokens FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- employee_addresses.country_code
ALTER TABLE employee_addresses ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_addresses FORCE ROW LEVEL SECURITY;
CREATE POLICY employee_addresses_country_rls ON employee_addresses FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- employee_assets.country_code
ALTER TABLE employee_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_assets FORCE ROW LEVEL SECURITY;
CREATE POLICY employee_assets_country_rls ON employee_assets FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- employee_attendance.country_code
ALTER TABLE employee_attendance ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_attendance FORCE ROW LEVEL SECURITY;
CREATE POLICY employee_attendance_country_rls ON employee_attendance FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- employee_biometrics.country_code
ALTER TABLE employee_biometrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_biometrics FORCE ROW LEVEL SECURITY;
CREATE POLICY employee_biometrics_country_rls ON employee_biometrics FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- employee_certifications.country_code
ALTER TABLE employee_certifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_certifications FORCE ROW LEVEL SECURITY;
CREATE POLICY employee_certifications_country_rls ON employee_certifications FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- employee_communication_threads.country_code
ALTER TABLE employee_communication_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_communication_threads FORCE ROW LEVEL SECURITY;
CREATE POLICY employee_communication_threads_country_rls ON employee_communication_threads FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- employee_dependents.country_code
ALTER TABLE employee_dependents ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_dependents FORCE ROW LEVEL SECURITY;
CREATE POLICY employee_dependents_country_rls ON employee_dependents FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- employee_documents.country_code
ALTER TABLE employee_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_documents FORCE ROW LEVEL SECURITY;
CREATE POLICY employee_documents_country_rls ON employee_documents FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- employee_expenses.country_code
ALTER TABLE employee_expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_expenses FORCE ROW LEVEL SECURITY;
CREATE POLICY employee_expenses_country_rls ON employee_expenses FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- employee_leave_ledgers.country_code
ALTER TABLE employee_leave_ledgers ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_leave_ledgers FORCE ROW LEVEL SECURITY;
CREATE POLICY employee_leave_ledgers_country_rls ON employee_leave_ledgers FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- employee_leave_requests.country_code
ALTER TABLE employee_leave_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_leave_requests FORCE ROW LEVEL SECURITY;
CREATE POLICY employee_leave_requests_country_rls ON employee_leave_requests FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- employee_relations.country_code
ALTER TABLE employee_relations ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_relations FORCE ROW LEVEL SECURITY;
CREATE POLICY employee_relations_country_rls ON employee_relations FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- employee_risk_scores.country_code
ALTER TABLE employee_risk_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_risk_scores FORCE ROW LEVEL SECURITY;
CREATE POLICY employee_risk_scores_country_rls ON employee_risk_scores FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- employee_roles.country_code
ALTER TABLE employee_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_roles FORCE ROW LEVEL SECURITY;
CREATE POLICY employee_roles_country_rls ON employee_roles FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- employee_shift_rosters.country_code
ALTER TABLE employee_shift_rosters ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_shift_rosters FORCE ROW LEVEL SECURITY;
CREATE POLICY employee_shift_rosters_country_rls ON employee_shift_rosters FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- employee_travel_requests.country_code
ALTER TABLE employee_travel_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_travel_requests FORCE ROW LEVEL SECURITY;
CREATE POLICY employee_travel_requests_country_rls ON employee_travel_requests FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- employee_work_logs.country_code
ALTER TABLE employee_work_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_work_logs FORCE ROW LEVEL SECURITY;
CREATE POLICY employee_work_logs_country_rls ON employee_work_logs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- employees.country_code
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE employees FORCE ROW LEVEL SECURITY;
CREATE POLICY employees_country_rls ON employees FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- escalation_sla_rules.country_code
ALTER TABLE escalation_sla_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE escalation_sla_rules FORCE ROW LEVEL SECURITY;
CREATE POLICY escalation_sla_rules_country_rls ON escalation_sla_rules FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- executive_news.country_code
ALTER TABLE executive_news ENABLE ROW LEVEL SECURITY;
ALTER TABLE executive_news FORCE ROW LEVEL SECURITY;
CREATE POLICY executive_news_country_rls ON executive_news FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- faqs.country_code
ALTER TABLE faqs ENABLE ROW LEVEL SECURITY;
ALTER TABLE faqs FORCE ROW LEVEL SECURITY;
CREATE POLICY faqs_country_rls ON faqs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- finance_audit_logs.country_code
ALTER TABLE finance_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance_audit_logs FORCE ROW LEVEL SECURITY;
CREATE POLICY finance_audit_logs_country_rls ON finance_audit_logs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- finance_automation_logs.country_code
ALTER TABLE finance_automation_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance_automation_logs FORCE ROW LEVEL SECURITY;
CREATE POLICY finance_automation_logs_country_rls ON finance_automation_logs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- finance_bank_accounts.country_code
ALTER TABLE finance_bank_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance_bank_accounts FORCE ROW LEVEL SECURITY;
CREATE POLICY finance_bank_accounts_country_rls ON finance_bank_accounts FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- financial_reports.country_code
ALTER TABLE financial_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE financial_reports FORCE ROW LEVEL SECURITY;
CREATE POLICY financial_reports_country_rls ON financial_reports FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- fiscal_periods.country_code
ALTER TABLE fiscal_periods ENABLE ROW LEVEL SECURITY;
ALTER TABLE fiscal_periods FORCE ROW LEVEL SECURITY;
CREATE POLICY fiscal_periods_country_rls ON fiscal_periods FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- fixed_assets.country_code
ALTER TABLE fixed_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE fixed_assets FORCE ROW LEVEL SECURITY;
CREATE POLICY fixed_assets_country_rls ON fixed_assets FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- flash_sale_items.country_code
ALTER TABLE flash_sale_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE flash_sale_items FORCE ROW LEVEL SECURITY;
CREATE POLICY flash_sale_items_country_rls ON flash_sale_items FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- flash_sales.country_code
ALTER TABLE flash_sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE flash_sales FORCE ROW LEVEL SECURITY;
CREATE POLICY flash_sales_country_rls ON flash_sales FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- fraud_alerts.country_code
ALTER TABLE fraud_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE fraud_alerts FORCE ROW LEVEL SECURITY;
CREATE POLICY fraud_alerts_country_rls ON fraud_alerts FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- fraud_cases.country_code
ALTER TABLE fraud_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE fraud_cases FORCE ROW LEVEL SECURITY;
CREATE POLICY fraud_cases_country_rls ON fraud_cases FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- fraud_events.country_code
ALTER TABLE fraud_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE fraud_events FORCE ROW LEVEL SECURITY;
CREATE POLICY fraud_events_country_rls ON fraud_events FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- fraud_rules.country_code
ALTER TABLE fraud_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE fraud_rules FORCE ROW LEVEL SECURITY;
CREATE POLICY fraud_rules_country_rls ON fraud_rules FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- fraud_scoring_logs.country_code
ALTER TABLE fraud_scoring_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE fraud_scoring_logs FORCE ROW LEVEL SECURITY;
CREATE POLICY fraud_scoring_logs_country_rls ON fraud_scoring_logs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- gateway_settlement_schedules.country_code
ALTER TABLE gateway_settlement_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE gateway_settlement_schedules FORCE ROW LEVEL SECURITY;
CREATE POLICY gateway_settlement_schedules_country_rls ON gateway_settlement_schedules FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- geo_fence_logs.country_code
ALTER TABLE geo_fence_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE geo_fence_logs FORCE ROW LEVEL SECURITY;
CREATE POLICY geo_fence_logs_country_rls ON geo_fence_logs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- group_chat_rooms.country_code
ALTER TABLE group_chat_rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE group_chat_rooms FORCE ROW LEVEL SECURITY;
CREATE POLICY group_chat_rooms_country_rls ON group_chat_rooms FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- internal_channels.country_code
ALTER TABLE internal_channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE internal_channels FORCE ROW LEVEL SECURITY;
CREATE POLICY internal_channels_country_rls ON internal_channels FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- internal_emails.country_code
ALTER TABLE internal_emails ENABLE ROW LEVEL SECURITY;
ALTER TABLE internal_emails FORCE ROW LEVEL SECURITY;
CREATE POLICY internal_emails_country_rls ON internal_emails FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- invoice_items.country_code
ALTER TABLE invoice_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoice_items FORCE ROW LEVEL SECURITY;
CREATE POLICY invoice_items_country_rls ON invoice_items FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- invoices.country_code
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices FORCE ROW LEVEL SECURITY;
CREATE POLICY invoices_country_rls ON invoices FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- ip_reputations.country_code
ALTER TABLE ip_reputations ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_reputations FORCE ROW LEVEL SECURITY;
CREATE POLICY ip_reputations_country_rls ON ip_reputations FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- journal_entries.country_code
ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE journal_entries FORCE ROW LEVEL SECURITY;
CREATE POLICY journal_entries_country_rls ON journal_entries FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- journal_entry_lines.country_code
ALTER TABLE journal_entry_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE journal_entry_lines FORCE ROW LEVEL SECURITY;
CREATE POLICY journal_entry_lines_country_rls ON journal_entry_lines FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- legal_contract_templates.country_code
ALTER TABLE legal_contract_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE legal_contract_templates FORCE ROW LEVEL SECURITY;
CREATE POLICY legal_contract_templates_country_rls ON legal_contract_templates FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- logistics_category_pricing_rules.country_code
ALTER TABLE logistics_category_pricing_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics_category_pricing_rules FORCE ROW LEVEL SECURITY;
CREATE POLICY logistics_category_pricing_rules_country_rls ON logistics_category_pricing_rules FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- logistics_cod_remittance_receipts.country_code
ALTER TABLE logistics_cod_remittance_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics_cod_remittance_receipts FORCE ROW LEVEL SECURITY;
CREATE POLICY logistics_cod_remittance_receipts_country_rls ON logistics_cod_remittance_receipts FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- logistics_fraud_indicators.country_code
ALTER TABLE logistics_fraud_indicators ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics_fraud_indicators FORCE ROW LEVEL SECURITY;
CREATE POLICY logistics_fraud_indicators_country_rls ON logistics_fraud_indicators FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- logistics_partner_bank_accounts.country_code
ALTER TABLE logistics_partner_bank_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics_partner_bank_accounts FORCE ROW LEVEL SECURITY;
CREATE POLICY logistics_partner_bank_accounts_country_rls ON logistics_partner_bank_accounts FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- logistics_partner_documents.country_code
ALTER TABLE logistics_partner_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics_partner_documents FORCE ROW LEVEL SECURITY;
CREATE POLICY logistics_partner_documents_country_rls ON logistics_partner_documents FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- logistics_partner_kyc_requirements.country_code
ALTER TABLE logistics_partner_kyc_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics_partner_kyc_requirements FORCE ROW LEVEL SECURITY;
CREATE POLICY logistics_partner_kyc_requirements_country_rls ON logistics_partner_kyc_requirements FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- logistics_partner_locations.country_code
ALTER TABLE logistics_partner_locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics_partner_locations FORCE ROW LEVEL SECURITY;
CREATE POLICY logistics_partner_locations_country_rls ON logistics_partner_locations FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- logistics_partner_payouts.country_code
ALTER TABLE logistics_partner_payouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics_partner_payouts FORCE ROW LEVEL SECURITY;
CREATE POLICY logistics_partner_payouts_country_rls ON logistics_partner_payouts FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- logistics_partner_profiles.country_code
ALTER TABLE logistics_partner_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics_partner_profiles FORCE ROW LEVEL SECURITY;
CREATE POLICY logistics_partner_profiles_country_rls ON logistics_partner_profiles FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- logistics_partner_service_areas.country_code
ALTER TABLE logistics_partner_service_areas ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics_partner_service_areas FORCE ROW LEVEL SECURITY;
CREATE POLICY logistics_partner_service_areas_country_rls ON logistics_partner_service_areas FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- logistics_partners.country_code
ALTER TABLE logistics_partners ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics_partners FORCE ROW LEVEL SECURITY;
CREATE POLICY logistics_partners_country_rls ON logistics_partners FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- logistics_pricing_profiles.country_code
ALTER TABLE logistics_pricing_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics_pricing_profiles FORCE ROW LEVEL SECURITY;
CREATE POLICY logistics_pricing_profiles_country_rls ON logistics_pricing_profiles FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- logistics_settlements.country_code
ALTER TABLE logistics_settlements ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics_settlements FORCE ROW LEVEL SECURITY;
CREATE POLICY logistics_settlements_country_rls ON logistics_settlements FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- logistics_vehicle_rules.country_code
ALTER TABLE logistics_vehicle_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE logistics_vehicle_rules FORCE ROW LEVEL SECURITY;
CREATE POLICY logistics_vehicle_rules_country_rls ON logistics_vehicle_rules FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- masked_messages.country_code
ALTER TABLE masked_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE masked_messages FORCE ROW LEVEL SECURITY;
CREATE POLICY masked_messages_country_rls ON masked_messages FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- media_assets.country_code
ALTER TABLE media_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE media_assets FORCE ROW LEVEL SECURITY;
CREATE POLICY media_assets_country_rls ON media_assets FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- media_upload_sessions.country_code
ALTER TABLE media_upload_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE media_upload_sessions FORCE ROW LEVEL SECURITY;
CREATE POLICY media_upload_sessions_country_rls ON media_upload_sessions FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- messages.country_code
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages FORCE ROW LEVEL SECURITY;
CREATE POLICY messages_country_rls ON messages FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- news_articles.country_code
ALTER TABLE news_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_articles FORCE ROW LEVEL SECURITY;
CREATE POLICY news_articles_country_rls ON news_articles FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- normalized_webhook_events.country_code
ALTER TABLE normalized_webhook_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE normalized_webhook_events FORCE ROW LEVEL SECURITY;
CREATE POLICY normalized_webhook_events_country_rls ON normalized_webhook_events FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- notifications.country_code
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications FORCE ROW LEVEL SECURITY;
CREATE POLICY notifications_country_rls ON notifications FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- offboarding_cases.country_code
ALTER TABLE offboarding_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE offboarding_cases FORCE ROW LEVEL SECURITY;
CREATE POLICY offboarding_cases_country_rls ON offboarding_cases FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- offices.country_code
ALTER TABLE offices ENABLE ROW LEVEL SECURITY;
ALTER TABLE offices FORCE ROW LEVEL SECURITY;
CREATE POLICY offices_country_rls ON offices FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- order_items.country_code
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items FORCE ROW LEVEL SECURITY;
CREATE POLICY order_items_country_rls ON order_items FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- order_logistics_allocations.country_code
ALTER TABLE order_logistics_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_logistics_allocations FORCE ROW LEVEL SECURITY;
CREATE POLICY order_logistics_allocations_country_rls ON order_logistics_allocations FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- orders.country_code
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders FORCE ROW LEVEL SECURITY;
CREATE POLICY orders_country_rls ON orders FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- org_units.country_code
ALTER TABLE org_units ENABLE ROW LEVEL SECURITY;
ALTER TABLE org_units FORCE ROW LEVEL SECURITY;
CREATE POLICY org_units_country_rls ON org_units FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- parcel_location_trackers.country_code
ALTER TABLE parcel_location_trackers ENABLE ROW LEVEL SECURITY;
ALTER TABLE parcel_location_trackers FORCE ROW LEVEL SECURITY;
CREATE POLICY parcel_location_trackers_country_rls ON parcel_location_trackers FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- password_reset_tokens.country_code
ALTER TABLE password_reset_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE password_reset_tokens FORCE ROW LEVEL SECURITY;
CREATE POLICY password_reset_tokens_country_rls ON password_reset_tokens FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- payment_gateway_connections.country_code
ALTER TABLE payment_gateway_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_gateway_connections FORCE ROW LEVEL SECURITY;
CREATE POLICY payment_gateway_connections_country_rls ON payment_gateway_connections FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- payment_orchestrator_sync.country_code
ALTER TABLE payment_orchestrator_sync ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_orchestrator_sync FORCE ROW LEVEL SECURITY;
CREATE POLICY payment_orchestrator_sync_country_rls ON payment_orchestrator_sync FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- payment_provider_configs.country_code
ALTER TABLE payment_provider_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_provider_configs FORCE ROW LEVEL SECURITY;
CREATE POLICY payment_provider_configs_country_rls ON payment_provider_configs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- payment_reconciliation_runs.country_code
ALTER TABLE payment_reconciliation_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_reconciliation_runs FORCE ROW LEVEL SECURITY;
CREATE POLICY payment_reconciliation_runs_country_rls ON payment_reconciliation_runs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- payments.country_code
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments FORCE ROW LEVEL SECURITY;
CREATE POLICY payments_country_rls ON payments FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- payout_batch_items.country_code
ALTER TABLE payout_batch_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE payout_batch_items FORCE ROW LEVEL SECURITY;
CREATE POLICY payout_batch_items_country_rls ON payout_batch_items FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- payout_batches.country_code
ALTER TABLE payout_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE payout_batches FORCE ROW LEVEL SECURITY;
CREATE POLICY payout_batches_country_rls ON payout_batches FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- payout_rule_categories.country_code
ALTER TABLE payout_rule_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE payout_rule_categories FORCE ROW LEVEL SECURITY;
CREATE POLICY payout_rule_categories_country_rls ON payout_rule_categories FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- payout_rule_products.country_code
ALTER TABLE payout_rule_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE payout_rule_products FORCE ROW LEVEL SECURITY;
CREATE POLICY payout_rule_products_country_rls ON payout_rule_products FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- payout_rules.country_code
ALTER TABLE payout_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE payout_rules FORCE ROW LEVEL SECURITY;
CREATE POLICY payout_rules_country_rls ON payout_rules FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- payouts.country_code
ALTER TABLE payouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE payouts FORCE ROW LEVEL SECURITY;
CREATE POLICY payouts_country_rls ON payouts FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- payroll_records.country_code
ALTER TABLE payroll_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE payroll_records FORCE ROW LEVEL SECURITY;
CREATE POLICY payroll_records_country_rls ON payroll_records FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- pending_journal_entries.country_code
ALTER TABLE pending_journal_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE pending_journal_entries FORCE ROW LEVEL SECURITY;
CREATE POLICY pending_journal_entries_country_rls ON pending_journal_entries FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- permission_audit_log.country_code
ALTER TABLE permission_audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE permission_audit_log FORCE ROW LEVEL SECURITY;
CREATE POLICY permission_audit_log_country_rls ON permission_audit_log FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- permission_categories.country_code
ALTER TABLE permission_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE permission_categories FORCE ROW LEVEL SECURITY;
CREATE POLICY permission_categories_country_rls ON permission_categories FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- permissions.country_code
ALTER TABLE permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE permissions FORCE ROW LEVEL SECURITY;
CREATE POLICY permissions_country_rls ON permissions FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- physical_id_cards.country_code
ALTER TABLE physical_id_cards ENABLE ROW LEVEL SECURITY;
ALTER TABLE physical_id_cards FORCE ROW LEVEL SECURITY;
CREATE POLICY physical_id_cards_country_rls ON physical_id_cards FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- processed_webhook_events.country_code
ALTER TABLE processed_webhook_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE processed_webhook_events FORCE ROW LEVEL SECURITY;
CREATE POLICY processed_webhook_events_country_rls ON processed_webhook_events FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- product_commission_overrides.country_code
ALTER TABLE product_commission_overrides ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_commission_overrides FORCE ROW LEVEL SECURITY;
CREATE POLICY product_commission_overrides_country_rls ON product_commission_overrides FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- product_filter_metadata.country_code
ALTER TABLE product_filter_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_filter_metadata FORCE ROW LEVEL SECURITY;
CREATE POLICY product_filter_metadata_country_rls ON product_filter_metadata FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- product_filter_options.country_code
ALTER TABLE product_filter_options ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_filter_options FORCE ROW LEVEL SECURITY;
CREATE POLICY product_filter_options_country_rls ON product_filter_options FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- product_variants.country_code
ALTER TABLE product_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_variants FORCE ROW LEVEL SECURITY;
CREATE POLICY product_variants_country_rls ON product_variants FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- product_verifications.country_code
ALTER TABLE product_verifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_verifications FORCE ROW LEVEL SECURITY;
CREATE POLICY product_verifications_country_rls ON product_verifications FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- product_videos.country_code
ALTER TABLE product_videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_videos FORCE ROW LEVEL SECURITY;
CREATE POLICY product_videos_country_rls ON product_videos FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- products.country_code
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE products FORCE ROW LEVEL SECURITY;
CREATE POLICY products_country_rls ON products FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- promotion_engine_configs.country_code
ALTER TABLE promotion_engine_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE promotion_engine_configs FORCE ROW LEVEL SECURITY;
CREATE POLICY promotion_engine_configs_country_rls ON promotion_engine_configs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- promotion_ledger_entries.country_code
ALTER TABLE promotion_ledger_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE promotion_ledger_entries FORCE ROW LEVEL SECURITY;
CREATE POLICY promotion_ledger_entries_country_rls ON promotion_ledger_entries FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- promotion_order_tiers.country_code
ALTER TABLE promotion_order_tiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE promotion_order_tiers FORCE ROW LEVEL SECURITY;
CREATE POLICY promotion_order_tiers_country_rls ON promotion_order_tiers FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- push_notification_tokens.country_code
ALTER TABLE push_notification_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE push_notification_tokens FORCE ROW LEVEL SECURITY;
CREATE POLICY push_notification_tokens_country_rls ON push_notification_tokens FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- recurring_templates.country_code
ALTER TABLE recurring_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE recurring_templates FORCE ROW LEVEL SECURITY;
CREATE POLICY recurring_templates_country_rls ON recurring_templates FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- referral_point_events.country_code
ALTER TABLE referral_point_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE referral_point_events FORCE ROW LEVEL SECURITY;
CREATE POLICY referral_point_events_country_rls ON referral_point_events FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- referrals.country_code
ALTER TABLE referrals ENABLE ROW LEVEL SECURITY;
ALTER TABLE referrals FORCE ROW LEVEL SECURITY;
CREATE POLICY referrals_country_rls ON referrals FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- refund_ledger.country_code
ALTER TABLE refund_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE refund_ledger FORCE ROW LEVEL SECURITY;
CREATE POLICY refund_ledger_country_rls ON refund_ledger FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- retention_job_runs.country_code
ALTER TABLE retention_job_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE retention_job_runs FORCE ROW LEVEL SECURITY;
CREATE POLICY retention_job_runs_country_rls ON retention_job_runs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- return_requests.country_code
ALTER TABLE return_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE return_requests FORCE ROW LEVEL SECURITY;
CREATE POLICY return_requests_country_rls ON return_requests FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- reviews.country_code
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews FORCE ROW LEVEL SECURITY;
CREATE POLICY reviews_country_rls ON reviews FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- revoked_tokens.country_code
ALTER TABLE revoked_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE revoked_tokens FORCE ROW LEVEL SECURITY;
CREATE POLICY revoked_tokens_country_rls ON revoked_tokens FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- role_permission_assignments.country_code
ALTER TABLE role_permission_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE role_permission_assignments FORCE ROW LEVEL SECURITY;
CREATE POLICY role_permission_assignments_country_rls ON role_permission_assignments FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- role_permission_settings.country_code
ALTER TABLE role_permission_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE role_permission_settings FORCE ROW LEVEL SECURITY;
CREATE POLICY role_permission_settings_country_rls ON role_permission_settings FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- scanned_expenses.country_code
ALTER TABLE scanned_expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE scanned_expenses FORCE ROW LEVEL SECURITY;
CREATE POLICY scanned_expenses_country_rls ON scanned_expenses FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- shift_handover_logs.country_code
ALTER TABLE shift_handover_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE shift_handover_logs FORCE ROW LEVEL SECURITY;
CREATE POLICY shift_handover_logs_country_rls ON shift_handover_logs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- shift_handover_sessions.country_code
ALTER TABLE shift_handover_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE shift_handover_sessions FORCE ROW LEVEL SECURITY;
CREATE POLICY shift_handover_sessions_country_rls ON shift_handover_sessions FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- shipment_confirmations.country_code
ALTER TABLE shipment_confirmations ENABLE ROW LEVEL SECURITY;
ALTER TABLE shipment_confirmations FORCE ROW LEVEL SECURITY;
CREATE POLICY shipment_confirmations_country_rls ON shipment_confirmations FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- shipment_events.country_code
ALTER TABLE shipment_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE shipment_events FORCE ROW LEVEL SECURITY;
CREATE POLICY shipment_events_country_rls ON shipment_events FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- shipments.country_code
ALTER TABLE shipments ENABLE ROW LEVEL SECURITY;
ALTER TABLE shipments FORCE ROW LEVEL SECURITY;
CREATE POLICY shipments_country_rls ON shipments FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- shipping_carriers.country_code
ALTER TABLE shipping_carriers ENABLE ROW LEVEL SECURITY;
ALTER TABLE shipping_carriers FORCE ROW LEVEL SECURITY;
CREATE POLICY shipping_carriers_country_rls ON shipping_carriers FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- shipping_rules.country_code
ALTER TABLE shipping_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE shipping_rules FORCE ROW LEVEL SECURITY;
CREATE POLICY shipping_rules_country_rls ON shipping_rules FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- shipping_zones.country_code
ALTER TABLE shipping_zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE shipping_zones FORCE ROW LEVEL SECURITY;
CREATE POLICY shipping_zones_country_rls ON shipping_zones FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- shop_warehouse_locations.country_code
ALTER TABLE shop_warehouse_locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE shop_warehouse_locations FORCE ROW LEVEL SECURITY;
CREATE POLICY shop_warehouse_locations_country_rls ON shop_warehouse_locations FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- supplier_badge_billing_history.country_code
ALTER TABLE supplier_badge_billing_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_badge_billing_history FORCE ROW LEVEL SECURITY;
CREATE POLICY supplier_badge_billing_history_country_rls ON supplier_badge_billing_history FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- supplier_badge_catalog.country_code
ALTER TABLE supplier_badge_catalog ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_badge_catalog FORCE ROW LEVEL SECURITY;
CREATE POLICY supplier_badge_catalog_country_rls ON supplier_badge_catalog FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- supplier_badges.country_code
ALTER TABLE supplier_badges ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_badges FORCE ROW LEVEL SECURITY;
CREATE POLICY supplier_badges_country_rls ON supplier_badges FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- supplier_bank_accounts.country_code
ALTER TABLE supplier_bank_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_bank_accounts FORCE ROW LEVEL SECURITY;
CREATE POLICY supplier_bank_accounts_country_rls ON supplier_bank_accounts FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- supplier_country_commissions.country_code
ALTER TABLE supplier_country_commissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_country_commissions FORCE ROW LEVEL SECURITY;
CREATE POLICY supplier_country_commissions_country_rls ON supplier_country_commissions FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- supplier_disputes.country_code
ALTER TABLE supplier_disputes ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_disputes FORCE ROW LEVEL SECURITY;
CREATE POLICY supplier_disputes_country_rls ON supplier_disputes FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- supplier_documents.country_code
ALTER TABLE supplier_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_documents FORCE ROW LEVEL SECURITY;
CREATE POLICY supplier_documents_country_rls ON supplier_documents FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- supplier_fraud_indicators.country_code
ALTER TABLE supplier_fraud_indicators ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_fraud_indicators FORCE ROW LEVEL SECURITY;
CREATE POLICY supplier_fraud_indicators_country_rls ON supplier_fraud_indicators FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- supplier_kyc_requirements.country_code
ALTER TABLE supplier_kyc_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_kyc_requirements FORCE ROW LEVEL SECURITY;
CREATE POLICY supplier_kyc_requirements_country_rls ON supplier_kyc_requirements FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- supplier_notification_preferences.country_code
ALTER TABLE supplier_notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_notification_preferences FORCE ROW LEVEL SECURITY;
CREATE POLICY supplier_notification_preferences_country_rls ON supplier_notification_preferences FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- supplier_onboarding_sync.country_code
ALTER TABLE supplier_onboarding_sync ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_onboarding_sync FORCE ROW LEVEL SECURITY;
CREATE POLICY supplier_onboarding_sync_country_rls ON supplier_onboarding_sync FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- supplier_profiles.country_code
ALTER TABLE supplier_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_profiles FORCE ROW LEVEL SECURITY;
CREATE POLICY supplier_profiles_country_rls ON supplier_profiles FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- supplier_settlements.country_code
ALTER TABLE supplier_settlements ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_settlements FORCE ROW LEVEL SECURITY;
CREATE POLICY supplier_settlements_country_rls ON supplier_settlements FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- support_ticket_replies.country_code
ALTER TABLE support_ticket_replies ENABLE ROW LEVEL SECURITY;
ALTER TABLE support_ticket_replies FORCE ROW LEVEL SECURITY;
CREATE POLICY support_ticket_replies_country_rls ON support_ticket_replies FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- support_tickets.country_code
ALTER TABLE support_tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE support_tickets FORCE ROW LEVEL SECURITY;
CREATE POLICY support_tickets_country_rls ON support_tickets FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- system_alerts.country_code
ALTER TABLE system_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_alerts FORCE ROW LEVEL SECURITY;
CREATE POLICY system_alerts_country_rls ON system_alerts FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- system_settings.country_code
ALTER TABLE system_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_settings FORCE ROW LEVEL SECURITY;
CREATE POLICY system_settings_country_rls ON system_settings FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- tax_rules.country_code
ALTER TABLE tax_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_rules FORCE ROW LEVEL SECURITY;
CREATE POLICY tax_rules_country_rls ON tax_rules FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- ticket_attachments.country_code
ALTER TABLE ticket_attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE ticket_attachments FORCE ROW LEVEL SECURITY;
CREATE POLICY ticket_attachments_country_rls ON ticket_attachments FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- ticket_messages.country_code
ALTER TABLE ticket_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE ticket_messages FORCE ROW LEVEL SECURITY;
CREATE POLICY ticket_messages_country_rls ON ticket_messages FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- ticket_replies.country_code
ALTER TABLE ticket_replies ENABLE ROW LEVEL SECURITY;
ALTER TABLE ticket_replies FORCE ROW LEVEL SECURITY;
CREATE POLICY ticket_replies_country_rls ON ticket_replies FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- transaction_ledgers.country_code
ALTER TABLE transaction_ledgers ENABLE ROW LEVEL SECURITY;
ALTER TABLE transaction_ledgers FORCE ROW LEVEL SECURITY;
CREATE POLICY transaction_ledgers_country_rls ON transaction_ledgers FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- treasury_accounts.country_code
ALTER TABLE treasury_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury_accounts FORCE ROW LEVEL SECURITY;
CREATE POLICY treasury_accounts_country_rls ON treasury_accounts FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- treasury_transactions.country_code
ALTER TABLE treasury_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury_transactions FORCE ROW LEVEL SECURITY;
CREATE POLICY treasury_transactions_country_rls ON treasury_transactions FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- upload_jobs.country_code
ALTER TABLE upload_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE upload_jobs FORCE ROW LEVEL SECURITY;
CREATE POLICY upload_jobs_country_rls ON upload_jobs FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- user_devices.country_code
ALTER TABLE user_devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_devices FORCE ROW LEVEL SECURITY;
CREATE POLICY user_devices_country_rls ON user_devices FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- user_login_history.country_code
ALTER TABLE user_login_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_login_history FORCE ROW LEVEL SECURITY;
CREATE POLICY user_login_history_country_rls ON user_login_history FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- user_permission_overrides.country_code
ALTER TABLE user_permission_overrides ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_permission_overrides FORCE ROW LEVEL SECURITY;
CREATE POLICY user_permission_overrides_country_rls ON user_permission_overrides FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- user_sessions.country_code
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions FORCE ROW LEVEL SECURITY;
CREATE POLICY user_sessions_country_rls ON user_sessions FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- users.country_code
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE users FORCE ROW LEVEL SECURITY;
CREATE POLICY users_country_rls ON users FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- vat_remittances.country_code
ALTER TABLE vat_remittances ENABLE ROW LEVEL SECURITY;
ALTER TABLE vat_remittances FORCE ROW LEVEL SECURITY;
CREATE POLICY vat_remittances_country_rls ON vat_remittances FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- vendors.country_code
ALTER TABLE vendors ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendors FORCE ROW LEVEL SECURITY;
CREATE POLICY vendors_country_rls ON vendors FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- video_analytics.country_code
ALTER TABLE video_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_analytics FORCE ROW LEVEL SECURITY;
CREATE POLICY video_analytics_country_rls ON video_analytics FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- video_rooms.country_code
ALTER TABLE video_rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_rooms FORCE ROW LEVEL SECURITY;
CREATE POLICY video_rooms_country_rls ON video_rooms FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- wishlist_items.country_code
ALTER TABLE wishlist_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE wishlist_items FORCE ROW LEVEL SECURITY;
CREATE POLICY wishlist_items_country_rls ON wishlist_items FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

-- wishlists.country_code
ALTER TABLE wishlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE wishlists FORCE ROW LEVEL SECURITY;
CREATE POLICY wishlists_country_rls ON wishlists FOR ALL
    USING (country_code IS NULL OR zozi_rls_check(country_code));

