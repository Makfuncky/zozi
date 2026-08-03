#!/usr/bin/env python
"""Script to update COUNTRY_AWARE_TABLES in rls_interceptor.py."""
import re

with open("utils/rls_interceptor.py", "r") as f:
    content = f.read()

tables = [
    "account_balances", "account_groups", "accounts", "accruals", "addresses",
    "admin_activity_logs", "admin_analytics_snapshots", "admin_change_audit_logs",
    "ai_generation_logs", "ai_staging_products", "ai_staging_variants", "ai_upload_jobs",
    "alumni_network", "ap_bills", "ap_ledger_entries", "api_keys", "ar_invoices",
    "ar_ledger_entries", "badge_billing_records", "badge_tiers", "badge_transactions",
    "bank_accounts", "bank_mapping_rules", "bank_reconciliations",
    "bank_statement_imports", "bank_statement_lines", "bank_transactions", "banners",
    "budgets", "cart_items", "carts", "cash_accounts", "cash_flow_forecasts",
    "cash_position_snapshots", "cash_transactions", "categories", "chatbot_query_events",
    "coi_reports", "commission_agreements", "commission_badge_tiers",
    "commission_category_rates", "commission_global_configs", "commission_ledger_entries",
    "commission_rules", "cost_centers", "country_category_tax_rates", "country_cities",
    "country_commission_rate_history", "country_commission_rates", "country_communication_threads",
    "country_communications", "country_config_versions", "country_economics", "country_feature_flags",
    "country_gateway_configs", "country_gateway_credentials", "country_holiday_calendars",
    "country_legal", "country_legal_contracts", "country_localization", "country_logistics_zones",
    "country_map_configs", "country_payment_aliases", "country_payout_rules",
    "country_staff_assignments", "country_tax", "coupon_usage", "coupons", "customers",
    "customs_entries", "data_residency_records", "direct_chat_rooms", "disciplinary_cases",
    "dynamic_qr_sessions", "email_campaigns", "email_provider_configs",
    "email_verification_tokens", "employee_addresses", "employee_assets", "employee_attendance",
    "employee_biometrics", "employee_certifications", "employee_communication_threads",
    "employee_dependents", "employee_documents", "employee_expenses", "employee_leave_ledgers",
    "employee_leave_requests", "employee_relations", "employee_roles", "employee_shift_rosters",
    "employee_travel_requests", "employee_work_logs", "employees", "escalation_sla_rules",
    "event_dead_letter", "event_retry_queue", "executive_news", "faqs", "feature_flags",
    "finance_audit_logs", "finance_automation_logs", "finance_bank_accounts",
    "finance_dashboard_metrics", "finance_reports", "financial_reports", "fiscal_periods",
    "fixed_assets", "flash_sale_items", "flash_sales", "fraud_alerts", "fraud_cases",
    "fraud_events", "fraud_rules", "fraud_scoring_logs", "gateway_settlement_schedules",
    "geo_fence_logs", "goods_receipt_lines", "goods_receipt_notes", "group_chat_rooms",
    "import_cost_templates", "import_shipment_lines", "import_shipments", "inbox_events",
    "internal_channels", "internal_emails", "invoice_items", "invoices", "ip_reputations",
    "journal_entries", "journal_entry_lines", "kpi_conversion", "kpi_country", "kpi_customer",
    "kpi_orders", "kpi_retention", "kpi_revenue", "kpi_supplier", "landed_cost_allocations",
    "legal_contract_templates", "logistics_category_pricing_rules",
    "logistics_cod_remittance_receipts", "logistics_fraud_indicators",
    "logistics_partner_bank_accounts", "logistics_partner_documents",
    "logistics_partner_kyc_requirements", "logistics_partner_locations",
    "logistics_partner_payouts", "logistics_partner_profiles",
    "logistics_partner_service_areas", "logistics_partners", "logistics_pricing_profiles",
    "logistics_rates", "logistics_settlements", "logistics_vehicle_rules", "media_assets",
    "media_upload_sessions", "messages", "mv_cash_position", "mv_daily_sales", "mv_facet_counts",
    "mv_monthly_sales", "news_articles", "normalized_webhook_events", "notifications",
    "offboarding_cases", "offices", "order_items", "order_logistics_allocations", "orders",
    "org_units", "outbox_events", "parcel_location_trackers", "password_reset_tokens",
    "payment_gateway_connections", "payment_orchestrator_sync", "payment_provider_configs",
    "payment_reconciliation_runs", "payments", "payout_batch_items", "payout_batches",
    "payout_rule_categories", "payout_rule_products", "payout_rules", "payouts",
    "logistics_partner_payouts", "cash_flow_forecasts", "cash_position_snapshots",
    "gateway_settlement_schedules", "vat_remittances", "refund_ledger", "transaction_ledgers",
    "supplier_settlements", "budgets", "fixed_assets", "accruals", "scanned_expenses",
    "recurring_templates", "finance_audit_logs", "finance_automation_logs",
    "financial_reports", "fiscal_periods", "permission_audit_log", "customers", "addresses",
    "employee_addresses", "employees", "employee_roles", "employee_attendance",
    "employee_leave_requests", "employee_leave_ledgers", "employee_assets", "employee_biometrics",
    "employee_dependents", "employee_certifications", "employee_documents", "employee_expenses",
    "employee_relations", "employee_shift_rosters", "employee_travel_requests",
    "employee_work_logs", "coi_reports", "offboarding_cases", "disciplinary_cases", "org_units",
    "country_configs", "country_basics", "country_economics", "country_tax", "country_legal",
    "country_cities", "country_communications", "country_gateway_credentials",
    "country_gateway_configs", "country_holiday_calendars", "country_localization",
    "country_logistics_zones", "country_map_configs", "country_payment_aliases",
    "country_payout_rules", "country_category_tax_rates", "country_feature_flags",
    "country_config_versions", "country_commission_rates", "country_commission_rate_history",
    "feature_flags", "system_settings", "tax_rules", "shipping_rules", "fraud_rules",
    "api_keys", "fraud_cases", "fraud_alerts", "fraud_events", "fraud_scoring_logs",
    "ip_reputations", "logistics_fraud_indicators", "device_fingerprints", "manual_review_queues",
    "meeting_action_items", "meeting_recordings", "meeting_transcripts", "return_abuse_patterns",
    "velocity_counters", "mv_daily_sales", "mv_monthly_sales", "mv_cash_position",
    "mv_facet_counts", "kpi_revenue", "kpi_orders", "kpi_customer", "kpi_supplier",
    "kpi_country", "kpi_conversion", "daily_sales_snapshot", "monthly_sales_snapshot",
    "cash_position_snapshot_mv", "facet_counts_snapshot", "financial_reports",
    "finance_dashboard_metrics", "outbox_events", "inbox_events", "event_dead_letter",
    "event_retry_queue", "normalized_webhook_events", "processed_webhook_events", "messages",
    "chatbot_query_events", "news_articles", "internal_emails", "email_campaigns",
    "ticket_messages", "support_tickets", "support_ticket_replies",
    "employee_communication_threads", "communication_audit_trail", "ai_upload_jobs",
    "ai_staging_products", "ai_staging_variants", "ai_generation_logs", "media_assets",
    "media_upload_sessions", "video_rooms", "video_analytics", "video_room_participants",
    "video_room_recordings", "admin_activity_logs", "admin_analytics_snapshots",
    "admin_change_audit_logs", "system_alerts", "system_settings", "tax_rules",
    "shipping_rules", "fraud_rules", "promotion_ledger_entries", "permission_audit_log",
    "communication_audit_trail", "worm_audit"
]

unique_tables = list(dict.fromkeys(tables))

lines = [
    'COUNTRY_AWARE_TABLES: dict[str, str] = {',
]
for name in sorted(unique_tables):
    lines.append(f'    "{name}": "country_code",')
lines.append("}")

new_dict_content = "\n".join(lines)

pattern = r'COUNTRY_AWARE_TABLES: dict\[str, str\] = \{[^}]+\}'
match = re.search(pattern, content, re.DOTALL)
if match:
    new_content = content[:match.start()] + new_dict_content + content[match.end():]
    with open("utils/rls_interceptor.py", "w") as f:
        f.write(new_content)
    print(f"Processed {len(unique_tables)} tables")
else:
    print("Pattern not found")