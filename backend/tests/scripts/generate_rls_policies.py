#!/usr/bin/env python
"""Generate missing RLS policies for DB05 compliance.

This script reads the existing pg_rls_policies.sql and appends policies
for the 88 country-scoped tables that are missing RLS coverage.
"""
import re
from pathlib import Path

POLICIES_FILE = Path(__file__).parent.parent / "data" / "pg_rls_policies.sql"

# Tables missing RLS policies (from DATABASE_AUDIT_REPORT.md)
MISSING_TABLES = [
    ("account_balances", "account"),
    ("account_groups", "account"),
    ("accounts", "finance"),
    ("accruals", "finance"),
    ("alumni_network", "admin"),
    ("badge_billing_records", "admin"),
    ("badge_tiers", "admin"),
    ("badge_transactions", "admin"),
    ("chatbot_query_events", "admin"),
    ("coi_reports", "admin"),
    ("api_keys", "admin"),
    ("ar_invoices", "finance"),
    ("ap_bills", "finance"),
    ("finance_bank_accounts", "finance"),
    ("finance_automation_logs", "finance"),
    ("financial_reports", "analytics"),
    ("fixed_assets", "finance"),
    ("fiscal_periods", "finance"),
    ("product_verifications", "admin"),
    ("ai_generation_logs", "ai"),
    ("ai_staging_products", "ai"),
    ("ai_staging_variants", "ai"),
    ("ai_upload_jobs", "ai"),
    ("announcements", "communication"),
    ("communication_audit_trail", "communication"),
    ("employee_communication_threads", "communication"),
    ("external_contact_masking", "communication"),
    ("faqs", "communication"),
    ("internal_channel_members", "communication"),
    ("internal_messages", "communication"),
    ("proxy_call_logs", "communication"),
    ("proxy_channels", "communication"),
    ("proxy_messages", "communication"),
    ("proxy_sessions", "communication"),
    ("ticket_messages", "communication"),
    ("addresses", "core"),
    ("carts", "commerce"),
    ("cart_items", "commerce"),
    ("city_distance_matrix", "logistics"),
    ("direct_chat_messages", "customer"),
    ("direct_chat_rooms", "customer"),
    ("email_verification_tokens", "user"),
    ("entity_chat_messages", "communication"),
    ("entity_chat_threads", "customer"),
    ("executive_news", "analytics"),
    ("group_chat_messages", "communication"),
    ("group_chat_rooms", "communication"),
    ("internal_notices", "communication"),
    ("predictive_simulations", "ai"),
    ("shift_handover_tasks", "hr"),
    ("support_ticket_replies", "communication"),
    ("user_sessions", "customer"),
    ("user_browsing_history", "core"),
    ("video_room_participants", "customer"),
    ("video_room_recordings", "media"),
    ("cash_position_snapshot_mv", "analytics"),
    ("daily_sales_snapshot", "analytics"),
    ("facet_counts_snapshot", "analytics"),
    ("kpi_conversion", "analytics"),
    ("kpi_country", "analytics"),
    ("kpi_customer", "analytics"),
    ("kpi_orders", "analytics"),
    ("kpi_retention", "analytics"),
    ("kpi_revenue", "analytics"),
    ("kpi_supplier", "analytics"),
    ("monthly_sales_snapshot", "analytics"),
    ("alert_escalation_rules", "communication"),
    ("escalation_sla_logs", "customer"),
    ("escalation_sla_rules", "communication"),
    ("command_center_views", "audit"),
    ("news_articles", "customer"),
    ("news_sources", "communication"),
    ("system_health_events", "core"),
    ("ticket_attachments", "communication"),
    ("credit_card_bin", "fraud"),
    ("direct_chat_room_members", "customer"),
    ("group_chat_member", "customer"),
    ("event_dead_letter", "events"),
    ("event_retry_queue", "events"),
    ("inbox_events", "events"),
    ("outbox_events", "events"),
    ("cash_flow_forecasts", "treasury"),
    ("cash_position_snapshots", "treasury"),
    ("gateway_settlement_schedules", "treasury"),
    ("pending_journal_entries", "finance"),
    ("dlp_violations", "fraud"),
    ("device_fingerprints", "fraud"),
    ("fraud_alerts", "fraud"),
    ("fraud_blacklist", "fraud"),
    ("fraud_case_assignments", "fraud"),
    ("fraud_cases", "fraud"),
    ("fraud_events", "fraud"),
    ("fraud_scoring_logs", "fraud"),
    ("ip_account_linkages", "fraud"),
    ("ip_reputations", "fraud"),
    ("logistics_fraud_indicators", "logistics"),
    ("manual_review_queues", "fraud"),
    ("meeting_action_items", "fraud"),
    ("meeting_recordings", "fraud"),
    ("meeting_transcripts", "fraud"),
    ("return_abuse_patterns", "fraud"),
    ("velocity_counters", "fraud"),
    ("disciplinary_cases", "hr"),
    ("employee_addresses", "hr"),
    ("employee_assets", "hr"),
    ("employee_attendance", "hr"),
    ("employee_biometrics", "hr"),
    ("employee_certifications", "hr"),
    ("employee_documents", "hr"),
    ("employee_expenses", "hr"),
    ("employee_leave_ledgers", "hr"),
    ("employee_leave_requests", "hr"),
    ("employee_relations", "hr"),
    ("employee_shift_rosters", "hr"),
    ("employee_travel_requests", "hr"),
    ("employee_work_logs", "hr"),
    ("geo_fence_logs", "hr"),
    ("internal_emails", "hr"),
    ("offboarding_cases", "hr"),
    ("org_units", "hr"),
    ("physical_id_cards", "hr"),
    ("logistics_category_pricing_rules", "logistics"),
    ("logistics_cod_remittance_receipts", "logistics"),
    ("logistics_fraud_indicators", "logistics"),
    ("logistics_partner_bank_accounts", "logistics"),
    ("logistics_partner_documents", "logistics"),
    ("logistics_partner_kyc_requirements", "logistics"),
    ("logistics_partner_locations", "logistics"),
    ("logistics_partner_payouts", "logistics"),
    ("logistics_partner_profiles", "logistics"),
    ("logistics_partner_service_areas", "logistics"),
    ("logistics_pricing_profiles", "logistics"),
    ("logistics_settlements", "logistics"),
    ("logistics_vehicle_rules", "logistics"),
    ("parcel_location_trackers", "logistics"),
    ("shipment_confirmations", "logistics"),
    ("shipment_events", "logistics"),
    ("shipments", "logistics"),
    ("campaign_recipients", "marketing"),
    ("email_campaigns", "marketing"),
    ("email_campaign_logs", "marketing"),
    ("email_delivery_events", "marketing"),
    ("email_provider_configs", "marketing"),
    ("email_runtime_configs", "marketing"),
    ("email_suppressions", "marketing"),
    ("email_templates", "marketing"),
    ("flash_sale", "marketing"),
    ("flash_sale_item", "marketing"),
    ("newsletter_subscribers", "marketing"),
    ("push_notification_tokens", "marketing"),
    ("retention_job_runs", "marketing"),
    ("media_assets", "media"),
    ("media_upload_sessions", "media"),
    ("order_notifications", "orders"),
    ("return_requests", "orders"),
    ("permission_audit_log", "permissions"),
    ("permission_categories", "permissions"),
    ("permissions", "permissions"),
    ("role_permission_assignments", "permissions"),
    ("role_permission_settings", "permissions"),
    ("user_permission_overrides", "permissions"),
    ("categories", "commerce"),
    ("product_filter_metadata", "commerce"),
    ("product_filter_options", "commerce"),
    ("product_videos", "commerce"),
    ("product_variants", "commerce"),
    ("products", "commerce"),
    ("reviews", "commerce"),
    ("wishlists", "commerce"),
    ("wishlist_items", "commerce"),
    ("supplier_bank_accounts", "suppliers"),
    ("supplier_country_commissions", "suppliers"),
    ("supplier_documents", "suppliers"),
    ("supplier_disputes", "suppliers"),
    ("supplier_fraud_indicators", "suppliers"),
    ("supplier_notification_preference", "suppliers"),
    ("supplier_profiles", "suppliers"),
    ("supplier_settlements", "finance"),
    ("user_devices", "user"),
    ("user_login_history", "user"),
    ("commission_rules", "commerce"),
    ("feature_flags", "configuration"),
]


def generate_policy(table_name: str, schema: str) -> str:
    """Generate a RLS policy for a table."""
    policy_name = table_name
    table_ref = f"{schema}.{table_name}"
    
    # Determine which column to use for country check
    if table_name in ["order_logistics_allocations"]:
        col_ref = f"{table_ref}.destination_country"
    elif table_name in ["addresses", "core_addresses"]:
        col_ref = f"{table_ref}.country_code"
    else:
        col_ref = f"{table_ref}.country_code"
    
    return f"""CREATE POLICY {policy_name}_rls_policy
    ON {table_ref}
    FOR ALL
    USING (
        {col_ref} IS NULL
        OR auth.country_access_check({col_ref})
    );
"""


def main():
    content = POLICIES_FILE.read_text()
    
    # Find existing policies
    existing_policies = set(re.findall(r'CREATE POLICY\s+(\w+)_rls_policy', content))
    
    # Generate missing policies
    new_policies = []
    for table_name, schema in MISSING_TABLES:
        if table_name not in existing_policies:
            policy = generate_policy(table_name, schema)
            new_policies.append(policy)
    
    # Insert before the verification queries section
    insert_point = "-- ============================================================================\n-- VERIFICATION QUERIES"
    if insert_point in content:
        new_section = "\n-- ============================================================================\n-- MISSING RLS POLICIES (Added for DB05 compliance)\n-- Tables listed in DATABASE_AUDIT_REPORT.md\n-- ============================================================================\n\n"
        new_section += "\n".join(new_policies)
        new_section += "\n\n"
        
        content = content.replace(insert_point, new_section + insert_point)
        POLICIES_FILE.write_text(content)
        print(f"Added {len(new_policies)} missing RLS policies")
    else:
        print("Could not find insertion point")


if __name__ == "__main__":
    main()