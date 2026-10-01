"""Add missing indexes and constraints for production readiness

Revision ID: e8efae30fc29
Revises: 20260728_0000
Create Date: 2026-07-28 19:30:00.000000+00:00

Adds:
- Indexes on ForeignKey columns missing from ORM
- Composite indexes for common filter/sort patterns
- Unique constraints for business-logic uniqueness
- Connection pool defaults updated in config (no migration needed)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e8efae30fc29"
down_revision: Union[str, None] = "20260728_0000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- orders -------------------------------------------------------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_order_logistics_allocations_order_id ON order_logistics_allocations (order_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_order_logistics_allocations_supplier_id ON order_logistics_allocations (supplier_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_order_logistics_allocations_partner_id ON order_logistics_allocations (partner_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_order_logistics_allocations_service_area_id ON order_logistics_allocations (service_area_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_order_logistics_allocations_shipment_id ON order_logistics_allocations (shipment_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_orders_status_created ON orders (status, created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_orders_user_deleted_created ON orders (user_id, is_deleted, created_at)")

    # -- logistics ----------------------------------------------------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_shipments_supplier_id ON shipments (supplier_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_shipments_assigned_partner_id ON shipments (assigned_partner_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_shipments_carrier_id ON shipments (carrier_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_shipment_events_supplier_id ON shipment_events (supplier_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_shipment_events_actor_user_id ON shipment_events (actor_user_id)")

    # -- commission ---------------------------------------------------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_commission_agreements_supplier_id ON commission_agreements (supplier_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_commission_agreements_set_by_admin_id ON commission_agreements (set_by_admin_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_commission_agreement_active ON commission_agreements (supplier_id, country_code, is_active, effective_from)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_commission_agreement ON commission_agreements (supplier_id, country_code, tier)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_product_commission_overrides_product_id ON product_commission_overrides (product_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_product_commission_overrides_supplier_id ON product_commission_overrides (supplier_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_product_commission_overrides_set_by_admin_id ON product_commission_overrides (set_by_admin_id)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_product_commission_override ON product_commission_overrides (product_id, supplier_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_commission_ledger_entries_supplier_id ON commission_ledger_entries (supplier_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_commission_ledger_entries_order_id ON commission_ledger_entries (order_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_commission_ledger_entries_order_item_id ON commission_ledger_entries (order_item_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_commission_ledger_entries_product_id ON commission_ledger_entries (product_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_commission_ledger_entries_adjusted_by ON commission_ledger_entries (adjusted_by)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_commission_ledger_supplier_created ON commission_ledger_entries (supplier_id, created_at)")

    # -- finance ------------------------------------------------------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_transaction_ledgers_user_id ON transaction_ledgers (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_transaction_ledgers_supplier_id ON transaction_ledgers (supplier_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_transaction_ledgers_logistics_partner_id ON transaction_ledgers (logistics_partner_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_transaction_ledgers_order_id ON transaction_ledgers (order_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_transaction_ledgers_order_item_id ON transaction_ledgers (order_item_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_transaction_ledgers_shipment_id ON transaction_ledgers (shipment_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_supplier_settlements_supplier_id ON supplier_settlements (supplier_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_supplier_settlements_order_id ON supplier_settlements (order_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_supplier_settlements_ledger_id ON supplier_settlements (ledger_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_supplier_settlements_payout_id ON supplier_settlements (payout_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_supplier_settlements_shipment_id ON supplier_settlements (shipment_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_supplier_settlements_bank_transaction_id ON supplier_settlements (bank_transaction_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_supplier_settlements_deleted_by ON supplier_settlements (deleted_by)")

    # -- admin --------------------------------------------------------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_system_alerts_acknowledged_by ON system_alerts (acknowledged_by)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_admin_change_audit_logs_admin_id ON admin_change_audit_logs (admin_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_admin_activity_logs_admin_id ON admin_activity_logs (admin_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_api_keys_created_by ON api_keys (created_by)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_payment_provider_configs_updated_by ON payment_provider_configs (updated_by)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_email_provider_configs_updated_by ON email_provider_configs (updated_by)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_finance_bank_accounts_created_by ON finance_bank_accounts (created_by)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_finance_bank_accounts_updated_by ON finance_bank_accounts (updated_by)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_promotion_engine_configs_updated_by ON promotion_engine_configs (updated_by)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_promotion_order_tiers_updated_by ON promotion_order_tiers (updated_by)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_logistics_cod_remittance_receipts_partner_id ON logistics_cod_remittance_receipts (partner_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_logistics_cod_remittance_receipts_shipment_id ON logistics_cod_remittance_receipts (shipment_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_logistics_cod_remittance_receipts_settlement_id ON logistics_cod_remittance_receipts (settlement_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_logistics_cod_remittance_receipts_reviewed_by ON logistics_cod_remittance_receipts (reviewed_by)")

    # -- suppliers ----------------------------------------------------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_supplier_profiles_user_id ON supplier_profiles (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_supplier_documents_supplier_id ON supplier_documents (supplier_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_supplier_documents_reviewed_by ON supplier_documents (reviewed_by)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_supplier_documents_verified_by ON supplier_documents (verified_by)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_supplier_notification_preferences_supplier_id ON supplier_notification_preferences (supplier_id)")

    # -- marketing ----------------------------------------------------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_flash_sale_items_flash_sale_id ON flash_sale_items (flash_sale_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_flash_sale_items_product_id ON flash_sale_items (product_id)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_flash_sale_item ON flash_sale_items (flash_sale_id, product_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_email_campaign_logs_campaign_id ON email_campaign_logs (campaign_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_email_campaign_logs_recipient_email ON email_campaign_logs (recipient_email)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_email_campaign_log ON email_campaign_logs (campaign_id, recipient_email)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_campaign_recipients_campaign_id ON campaign_recipients (campaign_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_campaign_recipients_user_id ON campaign_recipients (user_id)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_campaign_recipient ON campaign_recipients (campaign_id, user_id)")

    # -- countries ----------------------------------------------------------
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_payout_rule ON payout_rules (country_code, min_amount, max_amount)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_tax_rule ON tax_rules (country_code, tax_name)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_shipping_rule ON shipping_rules (country_code, method)")

    # -- products -----------------------------------------------------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_products_category_active_deleted ON products (category_id, is_active, is_deleted)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_products_supplier_active_deleted ON products (supplier_id, is_active, is_deleted)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_products_created_at ON products (created_at)")

    # -- refund_ledger (additional FK indexes) ------------------------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_refund_ledger_bank_transaction_id ON refund_ledger (bank_transaction_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_refund_ledger_deleted_by ON refund_ledger (deleted_by)")

    # -- invoices (additional FK indexes) -----------------------------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_invoices_deleted_by ON invoices (deleted_by)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_invoices_shipment_id ON invoices (shipment_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_invoices_supplier_id ON invoices (supplier_id)")

    # -- return_requests (missing order_id index) ---------------------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_return_requests_order_id ON return_requests (order_id)")

    # -- supplier_disputes (missing created_by index) -----------------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_supplier_disputes_created_by ON supplier_disputes (created_by)")

    # -- logistics_settlements (missing shipment_id index) ------------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_logistics_settlements_shipment_id ON logistics_settlements (shipment_id)")

    # -- product_verifications (missing shipment_id index) ------------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_product_verifications_shipment_id ON product_verifications (shipment_id)")

    # -- bank_transactions (additional indexes) -----------------------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_bank_transactions_linked_order_id ON bank_transactions (linked_order_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_bank_transactions_linked_supplier_id ON bank_transactions (linked_supplier_id)")

    # -- vat_remittances (additional FK index) ------------------------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_vat_remittances_bank_transaction_id ON vat_remittances (bank_transaction_id)")

    # -- ar_ledger_entries / ap_ledger_entries ------------------------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_ar_ledger_entries_order_id ON ar_ledger_entries (order_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ap_ledger_entries_order_id ON ap_ledger_entries (order_id)")


    # -- account_balances (missing user_id index) ---------------------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_account_balances_user_id ON account_balances (user_id)")

    # -- commission_badge_tiers / commission_global_configs -----------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_commission_badge_tiers_updated_by ON commission_badge_tiers (updated_by)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_commission_global_configs_updated_by ON commission_global_configs (updated_by)")

    # -- pgc_provider_country (ensure present) ------------------------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_pgc_provider_country ON payment_gateway_connections (provider_code, country_code)")



def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_pgc_provider_country")
    op.execute("DROP INDEX IF EXISTS ix_commission_global_configs_updated_by")
    op.execute("DROP INDEX IF EXISTS ix_commission_badge_tiers_updated_by")
    op.execute("DROP INDEX IF EXISTS ix_account_balances_user_id")
    op.execute("DROP INDEX IF EXISTS uq_campaign_recipient")
    op.execute("DROP INDEX IF EXISTS ix_campaign_recipients_user_id")
    op.execute("DROP INDEX IF EXISTS ix_campaign_recipients_campaign_id")
    op.execute("DROP INDEX IF EXISTS uq_email_campaign_log")
    op.execute("DROP INDEX IF EXISTS ix_email_campaign_logs_recipient_email")
    op.execute("DROP INDEX IF EXISTS ix_email_campaign_logs_campaign_id")
    op.execute("DROP INDEX IF EXISTS uq_flash_sale_item")
    op.execute("DROP INDEX IF EXISTS ix_flash_sale_items_product_id")
    op.execute("DROP INDEX IF EXISTS ix_flash_sale_items_flash_sale_id")
    op.execute("DROP INDEX IF EXISTS ix_email_provider_configs_updated_by")
    op.execute("DROP INDEX IF EXISTS ix_finance_bank_accounts_updated_by")
    op.execute("DROP INDEX IF EXISTS ix_finance_bank_accounts_created_by")
    op.execute("DROP INDEX IF EXISTS ix_promotion_order_tiers_updated_by")
    op.execute("DROP INDEX IF EXISTS ix_promotion_engine_configs_updated_by")
    op.execute("DROP INDEX IF EXISTS ix_products_created_at")
    op.execute("DROP INDEX IF EXISTS ix_products_supplier_active_deleted")
    op.execute("DROP INDEX IF EXISTS ix_products_category_active_deleted")
    op.execute("DROP INDEX IF EXISTS uq_shipping_rule")
    op.execute("DROP INDEX IF EXISTS uq_tax_rule")
    op.execute("DROP INDEX IF EXISTS uq_payout_rule")
    op.execute("DROP INDEX IF EXISTS ix_supplier_notification_preferences_supplier_id")
    op.execute("DROP INDEX IF EXISTS ix_supplier_documents_verified_by")
    op.execute("DROP INDEX IF EXISTS ix_supplier_documents_reviewed_by")
    op.execute("DROP INDEX IF EXISTS ix_supplier_documents_supplier_id")
    op.execute("DROP INDEX IF EXISTS ix_supplier_profiles_user_id")
    op.execute("DROP INDEX IF EXISTS ix_logistics_cod_remittance_receipts_reviewed_by")
    op.execute("DROP INDEX IF EXISTS ix_logistics_cod_remittance_receipts_settlement_id")
    op.execute("DROP INDEX IF EXISTS ix_logistics_cod_remittance_receipts_shipment_id")
    op.execute("DROP INDEX IF EXISTS ix_logistics_cod_remittance_receipts_partner_id")
    op.execute("DROP INDEX IF EXISTS ix_payment_provider_configs_updated_by")
    op.execute("DROP INDEX IF EXISTS ix_api_keys_created_by")
    op.execute("DROP INDEX IF EXISTS ix_admin_activity_logs_admin_id")
    op.execute("DROP INDEX IF EXISTS ix_admin_change_audit_logs_admin_id")
    op.execute("DROP INDEX IF EXISTS ix_system_alerts_acknowledged_by")
    op.execute("DROP INDEX IF EXISTS ix_supplier_settlements_deleted_by")
    op.execute("DROP INDEX IF EXISTS ix_supplier_settlements_bank_transaction_id")
    op.execute("DROP INDEX IF EXISTS ix_supplier_settlements_shipment_id")
    op.execute("DROP INDEX IF EXISTS ix_supplier_settlements_payout_id")
    op.execute("DROP INDEX IF EXISTS ix_supplier_settlements_ledger_id")
    op.execute("DROP INDEX IF EXISTS ix_supplier_settlements_order_id")
    op.execute("DROP INDEX IF EXISTS ix_supplier_settlements_supplier_id")
    op.execute("DROP INDEX IF EXISTS ix_transaction_ledgers_shipment_id")
    op.execute("DROP INDEX IF EXISTS ix_transaction_ledgers_order_item_id")
    op.execute("DROP INDEX IF EXISTS ix_transaction_ledgers_order_id")
    op.execute("DROP INDEX IF EXISTS ix_transaction_ledgers_supplier_id")
    op.execute("DROP INDEX IF EXISTS ix_transaction_ledgers_logistics_partner_id")
    op.execute("DROP INDEX IF EXISTS ix_transaction_ledgers_user_id")
    op.execute("DROP INDEX IF EXISTS uq_commission_agreement")
    op.execute("DROP INDEX IF EXISTS ix_commission_ledger_supplier_created")
    op.execute("DROP INDEX IF EXISTS ix_commission_ledger_entries_adjusted_by")
    op.execute("DROP INDEX IF EXISTS ix_commission_ledger_entries_product_id")
    op.execute("DROP INDEX IF EXISTS ix_commission_ledger_entries_order_item_id")
    op.execute("DROP INDEX IF EXISTS ix_commission_ledger_entries_order_id")
    op.execute("DROP INDEX IF EXISTS ix_commission_ledger_entries_supplier_id")
    op.execute("DROP INDEX IF EXISTS uq_product_commission_override")
    op.execute("DROP INDEX IF EXISTS ix_product_commission_overrides_set_by_admin_id")
    op.execute("DROP INDEX IF EXISTS ix_product_commission_overrides_supplier_id")
    op.execute("DROP INDEX IF EXISTS ix_product_commission_overrides_product_id")
    op.execute("DROP INDEX IF EXISTS ix_commission_agreement_active")
    op.execute("DROP INDEX IF EXISTS ix_commission_agreements_set_by_admin_id")
    op.execute("DROP INDEX IF EXISTS ix_commission_agreements_supplier_id")
    op.execute("DROP INDEX IF EXISTS ix_orders_user_deleted_created")
    op.execute("DROP INDEX IF EXISTS ix_orders_status_created")
    op.execute("DROP INDEX IF EXISTS ix_order_logistics_allocations_shipment_id")
    op.execute("DROP INDEX IF EXISTS ix_order_logistics_allocations_service_area_id")
    op.execute("DROP INDEX IF EXISTS ix_order_logistics_allocations_partner_id")
    op.execute("DROP INDEX IF EXISTS ix_order_logistics_allocations_supplier_id")
    op.execute("DROP INDEX IF EXISTS ix_order_logistics_allocations_order_id")
    op.execute("DROP INDEX IF EXISTS ix_shipment_events_actor_user_id")
    op.execute("DROP INDEX IF EXISTS ix_shipment_events_supplier_id")
    op.execute("DROP INDEX IF EXISTS ix_shipments_carrier_id")
    op.execute("DROP INDEX IF EXISTS ix_shipments_assigned_partner_id")
    op.execute("DROP INDEX IF EXISTS ix_shipments_supplier_id")
    op.execute("DROP INDEX IF EXISTS ix_vat_remittances_bank_transaction_id")
    op.execute("DROP INDEX IF EXISTS ix_product_verifications_shipment_id")
    op.execute("DROP INDEX IF EXISTS ix_logistics_settlements_shipment_id")
    op.execute("DROP INDEX IF EXISTS ix_supplier_disputes_created_by")
    op.execute("DROP INDEX IF EXISTS ix_return_requests_order_id")
    op.execute("DROP INDEX IF EXISTS ix_invoices_supplier_id")
    op.execute("DROP INDEX IF EXISTS ix_invoices_shipment_id")
    op.execute("DROP INDEX IF EXISTS ix_invoices_deleted_by")
    op.execute("DROP INDEX IF EXISTS ix_bank_transactions_linked_supplier_id")
