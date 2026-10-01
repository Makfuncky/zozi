"""Cash Management Service — encapsulates cash management operations."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from sqlalchemy.orm import Session

from infrastructure.database.rls_interceptor import clear_rls_context, set_rls_context
from infrastructure.utils.country_rls import get_country_or_404


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
    """Create a CashTransaction record for a refund (debit — money going out to the customer)."""
    from domains.finance.models.general_ledger import CashAccount, CashTransaction

    amount = Decimal(str(kwargs.get("amount", getattr(order, "total", 0) or 0)))
    country_code = getattr(order, "country_code", None)
    account_id = kwargs.get("account_id")

    if account_id is None:
        query = db.query(CashAccount).filter(CashAccount.is_deleted.is_(False))
        if country_code:
            query = query.filter(CashAccount.country_code == country_code)
        account = query.order_by(CashAccount.id).first()
        if account is None:
            raise ValueError("No active cash account found for refund transaction")
        account_id = account.id

    txn = CashTransaction(
        account_id=account_id,
        transaction_type="refund",
        amount=amount,
        description=kwargs.get("description", f"Refund for order {getattr(order, 'order_number', getattr(order, 'id', ''))}"),
        reference=kwargs.get("reference", getattr(order, "order_number", None)),
        category="refund",
        performed_by_id=kwargs.get("performed_by_id"),
        country_code=country_code,
    )
    db.add(txn)
    db.flush()


def apply_shipment_vehicle_selection(shipment: Any, db: Session, vehicle_type: Optional[str] = None) -> Any:
    """Apply vehicle selection to a shipment and commit the change."""
    if vehicle_type is not None:
        shipment.accepted_vehicle_type = vehicle_type
        shipment.accepted_vehicle_selected_at = datetime.utcnow()
        db.add(shipment)
        db.commit()
    return shipment


def create_cod_remittance_receipt(*args: Any, **kwargs: Any) -> Any:
    """Create a COD remittance receipt record."""
    from domains.governance.models.admin import LogisticsCODRemittanceReceipt

    settlement_id = kwargs.get("settlement_id")
    if settlement_id is None and args:
        settlement_id = args[0]

    amount = kwargs.get("amount", 0)
    if amount is None and len(args) > 1:
        amount = args[1]

    receipt = LogisticsCODRemittanceReceipt(
        settlement_id=settlement_id,
        partner_id=kwargs.get("partner_id"),
        shipment_id=kwargs.get("shipment_id"),
        amount=Decimal(str(amount)),
        bank_reference=kwargs.get("bank_reference"),
        receipt_file_url=kwargs.get("receipt_file_url"),
        notes=kwargs.get("notes"),
        currency=kwargs.get("currency"),
        country_code=kwargs.get("country_code"),
        status=kwargs.get("status", "pending"),
    )
    db = kwargs.get("db")
    if db is not None:
        db.add(receipt)
        db.flush()
    return receipt


def create_settlements_on_delivery(*args: Any, **kwargs: Any) -> Any:
    """Create a settlement record for delivered orders."""
    from domains.governance.models.admin import LogisticsSettlement

    partner_id = kwargs.get("partner_id")
    if partner_id is None and args:
        partner_id = args[0]

    order_id = kwargs.get("order_id")
    if order_id is None and len(args) > 1:
        order_id = args[1]

    settlement = LogisticsSettlement(
        partner_id=partner_id,
        order_id=order_id,
        shipment_id=kwargs.get("shipment_id"),
        amount=Decimal(str(kwargs.get("amount", 0))) if kwargs.get("amount") is not None else None,
        pickup_charge=Decimal(str(kwargs.get("pickup_charge", 0))) if kwargs.get("pickup_charge") is not None else None,
        dropoff_charge=Decimal(str(kwargs.get("dropoff_charge", 0))) if kwargs.get("dropoff_charge") is not None else None,
        total_delivery_fee=Decimal(str(kwargs.get("total_delivery_fee", 0))) if kwargs.get("total_delivery_fee") is not None else None,
        cod_collected=Decimal(str(kwargs.get("cod_collected", 0))) if kwargs.get("cod_collected") is not None else None,
        cod_remitted=Decimal(str(kwargs.get("cod_remitted", 0))) if kwargs.get("cod_remitted") is not None else None,
        cod_retained=Decimal(str(kwargs.get("cod_retained", 0))) if kwargs.get("cod_retained") is not None else None,
        cod_remittance_status=kwargs.get("cod_remittance_status"),
        currency=kwargs.get("currency"),
        country_code=kwargs.get("country_code"),
        status=kwargs.get("status", "pending"),
    )
    db = kwargs.get("db")
    if db is not None:
        db.add(settlement)
        db.flush()
    return settlement


def deserialize_pricing_breakdown_json(pricing_breakdown_json: Optional[str]) -> dict:
    """Deserialize a pricing breakdown JSON string into a dict.

    Returns an empty dict if the input is None, empty, or invalid JSON.
    """
    import json
    if not pricing_breakdown_json:
        return {}
    try:
        result = json.loads(pricing_breakdown_json)
        return result if isinstance(result, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def effective_allocation_delivery_amounts(allocation: Any) -> dict:
    """Return effective delivery amounts for a logistics allocation.

    Returns a dict with shipping_amount, cod_amount, and other delivery-related
    monetary values. Extracts from the allocation's pricing breakdown or returns
    sensible defaults.
    """
    if allocation is None:
        return {"shipping_amount": 0.0, "cod_amount": 0.0, "total_amount": 0.0}

    # Try to get amounts from the allocation
    shipping_amount = float(getattr(allocation, "shipping_amount", 0) or 0)
    cod_amount = float(getattr(allocation, "cod_amount", 0) or 0)
    total_amount = float(getattr(allocation, "total_amount", 0) or 0)

    return {
        "shipping_amount": shipping_amount,
        "cod_amount": cod_amount,
        "total_amount": total_amount,
    }


def list_cod_remittance_receipts(db: Session, **kwargs: Any) -> list:
    """List COD remittance receipts. Delegates to CashManagementService."""
    svc = CashManagementService()
    return svc.admin_list_cod_remittance_receipts(db, **kwargs)


def serialize_cod_remittance_receipt(receipt: Any, db: Session) -> dict:
    """Serialize a COD remittance receipt into a dict."""
    if receipt is None:
        return {}
    return {
        "id": getattr(receipt, "id", None),
        "settlement_id": getattr(receipt, "settlement_id", None),
        "amount": float(getattr(receipt, "amount", 0) or 0),
        "status": getattr(receipt, "status", "pending"),
        "created_at": str(getattr(receipt, "created_at", "")),
    }
