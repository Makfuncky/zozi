"""controllers.treasury.reporting_controller controller.

Business logic is delegated to services.treasury.reporting_service (routers -> controllers -> services)."""

from services.treasury.reporting_service import (
    _resolve_stage, admin_approve_payout_batch, admin_approve_pending, admin_approve_settlement, admin_cash_forecasts, admin_cash_position,
    admin_cod_remittances, admin_detect_orphans, admin_dispatch_payout_batch, admin_gateway_exceptions, admin_gateway_summary, admin_generate_payout_batch,
    admin_liabilities_exposure, admin_logistics_payouts, admin_manual_adjustment, admin_payment_transactions, admin_payout_batches, admin_pending_entries,
    admin_reconciliation_pipeline, admin_record_cod_remittance, admin_reject_pending, admin_settle_supplier, admin_snapshot_cash_position, admin_supplier_earnings,
    admin_supplier_payouts, admin_treasury_ledger, admin_treasury_metrics, admin_treasury_root, admin_trial_balance, admin_vat_liability,
    consolidated_cash_forecasts, consolidated_cash_position, consolidated_cod_remittances, consolidated_gateway_summary, consolidated_payout_batches, consolidated_reconciliation_pipeline,
    consolidated_treasury_ledger, consolidated_treasury_metrics, consolidated_trial_balance, consolidated_vat_liability, country_approve_pending, country_cash_position,
    country_cod_remittances, country_detect_orphans, country_gateway_exceptions, country_gateway_summary, country_liabilities_exposure, country_logistics_payouts,
    country_manual_adjustment, country_payment_transactions, country_payout_batches, country_payroll, country_pending_entries, country_reject_pending,
    country_supplier_earnings, country_supplier_payouts, country_treasury_ledger, country_treasury_metrics, country_trial_balance, country_vat_liability,
    logger, payroll_equity
)

__all__ = [
    "_resolve_stage", "admin_approve_payout_batch", "admin_approve_pending", "admin_approve_settlement", "admin_cash_forecasts", "admin_cash_position",
    "admin_cod_remittances", "admin_detect_orphans", "admin_dispatch_payout_batch", "admin_gateway_exceptions", "admin_gateway_summary", "admin_generate_payout_batch",
    "admin_liabilities_exposure", "admin_logistics_payouts", "admin_manual_adjustment", "admin_payment_transactions", "admin_payout_batches", "admin_pending_entries",
    "admin_reconciliation_pipeline", "admin_record_cod_remittance", "admin_reject_pending", "admin_settle_supplier", "admin_snapshot_cash_position", "admin_supplier_earnings",
    "admin_supplier_payouts", "admin_treasury_ledger", "admin_treasury_metrics", "admin_treasury_root", "admin_trial_balance", "admin_vat_liability",
    "consolidated_cash_forecasts", "consolidated_cash_position", "consolidated_cod_remittances", "consolidated_gateway_summary", "consolidated_payout_batches", "consolidated_reconciliation_pipeline",
    "consolidated_treasury_ledger", "consolidated_treasury_metrics", "consolidated_trial_balance", "consolidated_vat_liability", "country_approve_pending", "country_cash_position",
    "country_cod_remittances", "country_detect_orphans", "country_gateway_exceptions", "country_gateway_summary", "country_liabilities_exposure", "country_logistics_payouts",
    "country_manual_adjustment", "country_payment_transactions", "country_payout_batches", "country_payroll", "country_pending_entries", "country_reject_pending",
    "country_supplier_earnings", "country_supplier_payouts", "country_treasury_ledger", "country_treasury_metrics", "country_trial_balance", "country_vat_liability",
    "logger", "payroll_equity"
]
