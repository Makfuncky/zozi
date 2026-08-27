"""Cash Management Service — encapsulates cash management operations."""

from typing import Any, Optional
from sqlalchemy.orm import Session

from infrastructure.database.rls_interceptor import clear_rls_context, set_rls_context
from domains.country.utils.country_rls import get_country_or_404


def commit_db(db: Session) -> None:
    """Commit the current database transaction."""
    db.commit()


def set_rls_context_service(db: Session, country_code: Optional[str]):
    """Set RLS context for a country. Returns cleanup function."""
    if country_code:
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
    def cleanup():
        if country_code:
            clear_rls_context()
    return cleanup


def generate_forecast(db: Session, days: int = 90, currency: str = "OMR", country_code: Optional[str] = None) -> dict:
    """Generate cash flow forecast."""
    return {"days": days, "currency": currency, "country_code": country_code, "forecast": []}


def list_contractor_milestones(db: Session) -> list:
    """Return contractor payment/delivery milestones."""
    return []


class CashManagementService:
    """Service for cash management operations."""

    def __init__(self, db: Session):
        self.db = db

    def admin_get_financial_summary(self) -> dict:
        return {}

    def admin_get_reconciliation_summary(self) -> dict:
        return {}

    def admin_list_ledger_entries(self, db: Session, **kwargs) -> list:
        return []

    def admin_list_supplier_settlements(self, db: Session, **kwargs) -> list:
        return []

    def admin_list_logistics_settlements(self, db: Session, **kwargs) -> list:
        return []

    def admin_list_bank_transactions(self, db: Session, **kwargs) -> list:
        return []

    def admin_list_refunds(self, db: Session, **kwargs) -> list:
        return []

    def admin_list_vat_remittance_records(self, db: Session, **kwargs) -> list:
        return []

    def admin_get_finance_bank_settings(self) -> dict:
        return {}

    def admin_test_finance_bank_connection(self) -> dict:
        return {}

    def admin_upsert_finance_bank_settings(self, body: dict, current_admin: dict) -> dict:
        return {}

    def admin_record_vat_remittance(self, body: dict, current_admin: dict) -> dict:
        return {}

    def admin_create_bank_transaction(self, data: dict) -> dict:
        return {}

    def admin_import_bank_transactions(self, items: list, current_admin: dict, **kwargs) -> dict:
        return {}

    def admin_reconcile_transaction(self, txn_id: int, current_admin: dict) -> dict:
        return {}

    def admin_flag_transaction(self, txn_id: int, reason: str) -> dict:
        return {}

    def admin_resolve_transaction_exception(self, txn_id: int, body: dict, current_admin: dict) -> dict:
        return {}

    def admin_auto_reconcile_transactions(self, current_admin: dict, **kwargs) -> dict:
        return {}

    def admin_trigger_supplier_payouts(self, db: Session, **kwargs) -> list:
        return []

    def admin_trigger_logistics_payouts(self, db: Session, **kwargs) -> list:
        return []

    def admin_record_cod_remittance(self, settlement_id: int, amount: float, current_admin: dict):
        from types import SimpleNamespace
        return SimpleNamespace(id=settlement_id, cod_remittance_status="recorded")

    def admin_list_cod_remittance_receipts(self, db: Session, **kwargs) -> list:
        return []

    def admin_verify_cod_remittance_receipt(self, receipt_id: int, current_admin: dict, **kwargs) -> dict:
        return {}

    def admin_reject_cod_remittance_receipt(self, receipt_id: int, current_admin: dict, **kwargs) -> dict:
        return {}

    def supplier_get_financial_summary(self, user_id: int, db: Session) -> dict:
        return {}

    def supplier_list_settlements(self, user_id: int, db: Session, **kwargs) -> list:
        return []

    def supplier_list_ledger_entries(self, user_id: int, db: Session, **kwargs) -> list:
        return []

    def logistics_get_financial_summary(self, user_id: int, db: Session) -> dict:
        return {}

    def logistics_list_settlements(self, user_id: int, db: Session, **kwargs) -> list:
        return []

    def logistics_list_ledger_entries(self, user_id: int, db: Session, **kwargs) -> list:
        return []


def log_refund_bank_transaction(order: Any, db: Session, **kwargs: Any) -> None:
    """Stub for logging refund bank transactions."""
    pass
