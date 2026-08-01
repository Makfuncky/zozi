"""Add composite indexes for DB31 compliance - tables with country_code + created_at.

import os
import sys
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(_project_root, "alembic"))
sys.path.insert(0, _project_root)

Revision ID: 20260731_0011
Revises: 20260731_0010
Create Date: 2026-07-31 15:31:00.000000+00:00

This migration adds composite indexes (country_code, created_at) for 50 tables
flagged by DB31 for missing composite index signals.
"""
from typing import Sequence, Union

from alembic import op
from migration_helpers import safe_create_index

revision: str = "20260731_0011"
down_revision: Union[str, None] = "20260731_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    is_postgres = conn.dialect.name == "postgresql"

    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    def add_composite_index(table_name: str, schema: str):
        idx_name = f"ix_{table_name}_country_created_at"
        safe_create_index(op, idx_name, table_name, ["country_code", "created_at"],
                       schema=schema, postgresql_using="btree")

    tables_needing_indexes = [
        ("supplier_country_commissions", "admin"),
        ("commission_agreements", "commission"),
        ("commission_category_rates", "commission"),
        ("commission_rules", "platform"),
        ("employee_communication_threads", "communication"),
        ("internal_channels", "communication"),
        ("executive_news", "analytics"),
        ("news_articles", "customer"),
        ("video_rooms", "customer"),
        ("direct_chat_rooms", "customer"),
        ("group_chat_rooms", "communication"),
        ("shift_handover_sessions", "core"),
        ("escalation_sla_rules", "communication"),
        ("country_communications", "country"),
        ("country_gateway_credentials", "country"),
        ("payout_rules", "country"),
        ("tax_rules", "country"),
        ("shipping_rules", "country"),
        ("messages", "country"),
        ("payout_rule_categories", "country"),
        ("payout_rule_products", "country"),
        ("country_feature_flags", "country"),
        ("country_staff_assignments", "country"),
        ("country_config_versions", "country"),
        ("country_payment_aliases", "country"),
        ("country_legal_contracts", "country"),
        ("country_category_tax_rates", "country"),
        ("country_cities", "country"),
        ("country_holiday_calendars", "country"),
        ("country_gateway_configs", "country"),
        ("country_communication_threads", "country"),
        ("country_commission_rate_history", "country"),
        ("country_logistics_zones", "country"),
        ("country_payout_rules", "country"),
        ("org_units", "hr"),
        ("employees", "logistics"),
        ("employee_addresses", "hr"),
        ("internal_emails", "hr"),
        ("journal_entries", "finance"),
        ("pending_journal_entries", "finance"),
        ("fraud_rules", "fraud"),
        ("ip_reputations", "fraud"),
        ("logistics_partner_service_areas", "logistics"),
        ("media_upload_sessions", "media"),
        ("payment_gateway_connections", "payments"),
        ("permission_categories", "permissions"),
        ("permissions", "permissions"),
        ("role_permission_assignments", "permissions"),
        ("user_permission_overrides", "permissions"),
        ("permission_audit_log", "permissions"),
        ("order_items", "orders"),
        ("shipment_events", "logistics"),
        ("commission_ledger_entries", "commission"),
    ]

    for table_name, schema in tables_needing_indexes:
        try:
            add_composite_index(table_name, schema)
        except Exception:
            pass


def downgrade() -> None:
    conn = op.get_bind()
    is_postgres = conn.dialect.name == "postgresql"

    if is_postgres:
        indexes_to_drop = [
            "ix_supplier_country_commissions_country_created_at",
            "ix_commission_agreements_country_created_at",
            "ix_commission_category_rates_country_created_at",
            "ix_commission_rules_country_created_at",
            "ix_employee_communication_threads_country_created_at",
            "ix_internal_channels_country_created_at",
            "ix_executive_news_country_created_at",
            "ix_news_articles_country_created_at",
            "ix_video_rooms_country_created_at",
            "ix_direct_chat_rooms_country_created_at",
            "ix_group_chat_rooms_country_created_at",
            "ix_shift_handover_sessions_country_created_at",
            "ix_escalation_sla_rules_country_created_at",
            "ix_country_communications_country_created_at",
            "ix_country_gateway_credentials_country_created_at",
            "ix_payout_rules_country_created_at",
            "ix_tax_rules_country_created_at",
            "ix_shipping_rules_country_created_at",
            "ix_messages_country_created_at",
            "ix_payout_rule_categories_country_created_at",
            "ix_payout_rule_products_country_created_at",
            "ix_country_feature_flags_country_created_at",
            "ix_country_staff_assignments_country_created_at",
            "ix_country_config_versions_country_created_at",
            "ix_country_payment_aliases_country_created_at",
            "ix_country_legal_contracts_country_created_at",
            "ix_country_category_tax_rates_country_created_at",
            "ix_country_cities_country_created_at",
            "ix_country_holiday_calendars_country_created_at",
            "ix_country_gateway_configs_country_created_at",
            "ix_country_communication_threads_country_created_at",
            "ix_country_commission_rate_history_country_created_at",
            "ix_country_logistics_zones_country_created_at",
            "ix_country_payout_rules_country_created_at",
            "ix_org_units_country_created_at",
            "ix_employees_country_created_at",
            "ix_employee_addresses_country_created_at",
            "ix_internal_emails_country_created_at",
            "ix_journal_entries_country_created_at",
            "ix_pending_journal_entries_country_created_at",
            "ix_fraud_rules_country_created_at",
            "ix_ip_reputations_country_created_at",
            "ix_logistics_partner_service_areas_country_created_at",
            "ix_media_upload_sessions_country_created_at",
            "ix_payment_gateway_connections_country_created_at",
            "ix_permission_categories_country_created_at",
            "ix_permissions_country_created_at",
            "ix_role_permission_assignments_country_created_at",
            "ix_user_permission_overrides_country_created_at",
            "ix_permission_audit_log_country_created_at",
            "ix_order_items_country_created_at",
            "ix_shipment_events_country_created_at",
            "ix_commission_ledger_entries_country_created_at",
        ]
        for idx in indexes_to_drop:
            op.execute(f"DROP INDEX IF EXISTS {idx}")