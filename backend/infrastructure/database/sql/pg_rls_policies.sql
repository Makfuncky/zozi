-- ============================================================================
-- ZOZI Platform — Row Level Security (RLS) Policies
-- ============================================================================
-- This file creates PostgreSQL RLS policies for country isolation.
-- Run this AFTER the bounded context schema migration.
--
-- Usage:
--   psql -U <user> -d <dbname> -f pg_rls_policies.sql
-- ============================================================================

-- Enable RLS on all country-scoped tables
-- NOTE: This is a template. Tables are listed by schema.

-- ============================================================================
-- CORE SCHEMA
-- ============================================================================
ALTER TABLE IF EXISTS "core"."users" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "core"."user_sessions" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "core"."user_devices" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "core"."user_login_history" ENABLE ROW LEVEL SECURITY;

-- Core policies
CREATE POLICY country_isolation_users ON "core"."users"
    FOR ALL
    USING (country_code = current_setting('app.current_country_code', true))
    WITH CHECK (country_code = current_setting('app.current_country_code', true));

CREATE POLICY admin_bypass_users ON "core"."users"
    FOR ALL
    USING (current_setting('app.current_role', true) = 'admin')
    WITH CHECK (current_setting('app.current_role', true) = 'admin');

-- ============================================================================
-- COMMERCE SCHEMA
-- ============================================================================
ALTER TABLE IF EXISTS "commerce"."products" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "commerce"."product_variants" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "commerce"."categories" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "commerce"."carts" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "commerce"."cart_items" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "commerce"."orders" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "commerce"."order_items" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "commerce"."banners" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "commerce"."coupons" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "commerce"."flash_sales" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "commerce"."flash_sale_items" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "commerce"."reviews" ENABLE ROW LEVEL SECURITY;

-- Commerce policies
CREATE POLICY country_isolation_products ON "commerce"."products"
    USING (country_code = current_setting('app.current_country_code', true));
CREATE POLICY admin_bypass_products ON "commerce"."products"
    USING (current_setting('app.current_role', true) = 'admin');

CREATE POLICY country_isolation_orders ON "commerce"."orders"
    USING (country_code = current_setting('app.current_country_code', true));
CREATE POLICY admin_bypass_orders ON "commerce"."orders"
    USING (current_setting('app.current_role', true) = 'admin');

-- ============================================================================
-- CUSTOMER SCHEMA
-- ============================================================================
ALTER TABLE IF EXISTS "customer"."customers" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "customer"."addresses" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "customer"."wishlists" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "customer"."wishlist_items" ENABLE ROW LEVEL SECURITY;

-- Customer policies
CREATE POLICY country_isolation_customers ON "customer"."customers"
    USING (country_code = current_setting('app.current_country_code', true));
CREATE POLICY admin_bypass_customers ON "customer"."customers"
    USING (current_setting('app.current_role', true) = 'admin');

-- ============================================================================
-- SUPPLIER SCHEMA
-- ============================================================================
ALTER TABLE IF EXISTS "supplier"."supplier_profiles" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "supplier"."supplier_documents" ENABLE ROW LEVEL SECURITY;

-- Supplier policies
CREATE POLICY country_isolation_supplier_profiles ON "supplier"."supplier_profiles"
    USING (country_code = current_setting('app.current_country_code', true));
CREATE POLICY admin_bypass_supplier_profiles ON "supplier"."supplier_profiles"
    USING (current_setting('app.current_role', true) = 'admin');

-- ============================================================================
-- LOGISTICS SCHEMA
-- ============================================================================
ALTER TABLE IF EXISTS "logistics"."logistics_partners" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "logistics"."logistics_partner_documents" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "logistics"."logistics_partner_service_areas" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "logistics"."logistics_pricing_profiles" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "logistics"."logistics_vehicle_rules" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "logistics"."shipments" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "logistics"."shipment_events" ENABLE ROW LEVEL SECURITY;

-- Logistics policies
CREATE POLICY country_isolation_logistics_partners ON "logistics"."logistics_partners"
    USING (country_code = current_setting('app.current_country_code', true));
CREATE POLICY admin_bypass_logistics_partners ON "logistics"."logistics_partners"
    USING (current_setting('app.current_role', true) = 'admin');

CREATE POLICY country_isolation_shipments ON "logistics"."shipments"
    USING (country_code = current_setting('app.current_country_code', true));
CREATE POLICY admin_bypass_shipments ON "logistics"."shipments"
    USING (current_setting('app.current_role', true) = 'admin');

-- ============================================================================
-- FINANCE SCHEMA
-- ============================================================================
ALTER TABLE IF EXISTS "finance"."accounts" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "finance"."account_groups" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "finance"."journal_entries" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "finance"."journal_entry_lines" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "finance"."ap_ledger_entries" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "finance"."ar_ledger_entries" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "finance"."invoices" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "finance"."invoice_items" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "finance"."payments" ENABLE ROW LEVEL SECURITY;

-- Finance policies
CREATE POLICY country_isolation_accounts ON "finance"."accounts"
    USING (country_code = current_setting('app.current_country_code', true));
CREATE POLICY admin_bypass_accounts ON "finance"."accounts"
    USING (current_setting('app.current_role', true) = 'admin');

CREATE POLICY country_isolation_journal_entries ON "finance"."journal_entries"
    USING (country_code = current_setting('app.current_country_code', true));
CREATE POLICY admin_bypass_journal_entries ON "finance"."journal_entries"
    USING (current_setting('app.current_role', true) = 'admin');

-- ============================================================================
-- TREASURY SCHEMA
-- ============================================================================
ALTER TABLE IF EXISTS "treasury"."treasury_accounts" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "treasury"."treasury_transactions" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "treasury"."cash_accounts" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "treasury"."bank_accounts" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "treasury"."payout_batches" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "treasury"."payouts" ENABLE ROW LEVEL SECURITY;

-- Treasury policies
CREATE POLICY country_isolation_treasury_accounts ON "treasury"."treasury_accounts"
    USING (country_code = current_setting('app.current_country_code', true));
CREATE POLICY admin_bypass_treasury_accounts ON "treasury"."treasury_accounts"
    USING (current_setting('app.current_role', true) = 'admin');

-- ============================================================================
-- HR SCHEMA
-- ============================================================================
ALTER TABLE IF EXISTS "hr"."employees" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "hr"."employee_addresses" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "hr"."employee_attendance" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "hr"."employee_leave_requests" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "hr"."employee_shift_rosters" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "hr"."offices" ENABLE ROW LEVEL SECURITY;

-- HR policies
CREATE POLICY country_isolation_employees ON "hr"."employees"
    USING (country_code = current_setting('app.current_country_code', true));
CREATE POLICY admin_bypass_employees ON "hr"."employees"
    USING (current_setting('app.current_role', true) = 'admin');

-- ============================================================================
-- COUNTRY SCHEMA
-- ============================================================================
ALTER TABLE IF EXISTS "country"."country_configs" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "country"."country_cities" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "country"."country_commission_rates" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "country"."country_staff_assignments" ENABLE ROW LEVEL SECURITY;

-- Country policies
CREATE POLICY country_isolation_country_configs ON "country"."country_configs"
    USING (country_code = current_setting('app.current_country_code', true));
CREATE POLICY admin_bypass_country_configs ON "country"."country_configs"
    USING (current_setting('app.current_role', true) = 'admin');

-- ============================================================================
-- COMMUNICATION SCHEMA
-- ============================================================================
ALTER TABLE IF EXISTS "comms"."notifications" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "comms"."messages" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "comms"."email_campaigns" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "comms"."email_templates" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "comms"."chat_threads" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "comms"."chat_messages" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "comms"."chat_attachments" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "comms"."support_tickets" ENABLE ROW LEVEL SECURITY;

-- Communication policies
CREATE POLICY country_isolation_notifications ON "comms"."notifications"
    USING (country_code = current_setting('app.current_country_code', true));
CREATE POLICY admin_bypass_notifications ON "comms"."notifications"
    USING (current_setting('app.current_role', true) = 'admin');

-- ============================================================================
-- SECURITY SCHEMA
-- ============================================================================
ALTER TABLE IF EXISTS "security"."api_keys" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "security"."fraud_alerts" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "security"."fraud_cases" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "security"."fraud_rules" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "security"."fraud_blacklist" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "security"."ip_reputations" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "security"."device_fingerprints" ENABLE ROW LEVEL SECURITY;

-- Security policies
CREATE POLICY country_isolation_fraud_alerts ON "security"."fraud_alerts"
    USING (country_code = current_setting('app.current_country_code', true));
CREATE POLICY admin_bypass_fraud_alerts ON "security"."fraud_alerts"
    USING (current_setting('app.current_role', true) = 'admin');

-- ============================================================================
-- AUDIT SCHEMA
-- ============================================================================
ALTER TABLE IF EXISTS "audit"."audit_logs" ENABLE ROW LEVEL SECURITY;

-- Audit policies
CREATE POLICY country_isolation_audit_logs ON "audit"."audit_logs"
    USING (country_code = current_setting('app.current_country_code', true));
CREATE POLICY admin_bypass_audit_logs ON "audit"."audit_logs"
    USING (current_setting('app.current_role', true) = 'admin');

-- ============================================================================
-- AI SCHEMA
-- ============================================================================
ALTER TABLE IF EXISTS "ai"."ai_staging_products" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "ai"."ai_upload_jobs" ENABLE ROW LEVEL SECURITY;

-- AI policies
CREATE POLICY country_isolation_ai_staging ON "ai"."ai_staging_products"
    USING (country_code = current_setting('app.current_country_code', true));
CREATE POLICY admin_bypass_ai_staging ON "ai"."ai_staging_products"
    USING (current_setting('app.current_role', true) = 'admin');

-- ============================================================================
-- MEDIA SCHEMA
-- ============================================================================
ALTER TABLE IF EXISTS "media"."media_assets" ENABLE ROW LEVEL SECURITY;

-- Media policies
CREATE POLICY country_isolation_media_assets ON "media"."media_assets"
    USING (country_code = current_setting('app.current_country_code', true));
CREATE POLICY admin_bypass_media_assets ON "media"."media_assets"
    USING (current_setting('app.current_role', true) = 'admin');

-- ============================================================================
-- CONFIGURATION SCHEMA
-- ============================================================================
ALTER TABLE IF EXISTS "configuration"."system_settings" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "configuration"."country_feature_flags" ENABLE ROW LEVEL SECURITY;

-- Configuration policies
CREATE POLICY country_isolation_system_settings ON "configuration"."system_settings"
    USING (country_code = current_setting('app.current_country_code', true));
CREATE POLICY admin_bypass_system_settings ON "configuration"."system_settings"
    USING (current_setting('app.current_role', true) = 'admin');

-- ============================================================================
-- GOVERNANCE SCHEMA
-- ============================================================================
ALTER TABLE IF EXISTS "governance"."admin_activity_logs" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "governance"."admin_analytics_snapshots" ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS "governance"."admin_change_audit_logs" ENABLE ROW LEVEL SECURITY;

-- Governance policies
CREATE POLICY country_isolation_admin_activity ON "governance"."admin_activity_logs"
    USING (country_code = current_setting('app.current_country_code', true));
CREATE POLICY admin_bypass_admin_activity ON "governance"."admin_activity_logs"
    USING (current_setting('app.current_role', true) = 'admin');

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================
-- Grant usage on schemas to application role
GRANT USAGE ON SCHEMA core TO zozi_app;
GRANT USAGE ON SCHEMA commerce TO zozi_app;
GRANT USAGE ON SCHEMA supplier TO zozi_app;
GRANT USAGE ON SCHEMA customer TO zozi_app;
GRANT USAGE ON SCHEMA logistics TO zozi_app;
GRANT USAGE ON SCHEMA finance TO zozi_app;
GRANT USAGE ON SCHEMA treasury TO zozi_app;
GRANT USAGE ON SCHEMA hr TO zozi_app;
GRANT USAGE ON SCHEMA country TO zozi_app;
GRANT USAGE ON SCHEMA media TO zozi_app;
GRANT USAGE ON SCHEMA ai TO zozi_app;
GRANT USAGE ON SCHEMA communication TO zozi_app;
GRANT USAGE ON SCHEMA audit TO zozi_app;
GRANT USAGE ON SCHEMA security TO zozi_app;
GRANT USAGE ON SCHEMA analytics TO zozi_app;
GRANT USAGE ON SCHEMA configuration TO zozi_app;
GRANT USAGE ON SCHEMA governance TO zozi_app;

-- Grant SELECT/INSERT/UPDATE on all tables to application role
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA core TO zozi_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA commerce TO zozi_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA supplier TO zozi_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA customer TO zozi_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA logistics TO zozi_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA finance TO zozi_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA treasury TO zozi_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA hr TO zozi_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA country TO zozi_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA media TO zozi_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA ai TO zozi_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA communication TO zozi_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA audit TO zozi_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA security TO zozi_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA analytics TO zozi_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA configuration TO zozi_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA governance TO zozi_app;
