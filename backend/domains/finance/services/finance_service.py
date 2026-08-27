"""Auto-migrated service logic from routers/cash_management.py."""
from __future__ import annotations

from typing import Optional

from fastapi import Body, Depends, Query

ALLOWED_BANK_ACCOUNT_KINDS = {"supplier", "logistics_partner"}

from providers.finance.bank_api import BankApiError, dispatch_batch, test_connection

from providers.geography.rates import fetch_rates
from providers.automation.scheduler import add_interval_job, create_scheduler
from providers.payments.connect import create_connect_account

from pydantic import BaseModel

from sqlalchemy.orm import Session

from infrastructure.utils.auth import require_permission
from infrastructure.security.dependencies import require_admin
from infrastructure.database.database import get_db

from infrastructure.database.schemas import (
    BadgeBillingOut,
    BankTransactionCreate,
    BankTransactionImportItem,
    BankTransactionOut,
    BankTransactionResolutionIn,
    FinanceBankConnectionTestOut,
    FinanceBankSettingsOut,
    FinanceBankSettingsUpdate,
    FinancialSummaryOut,
    LedgerEntryOut,
    LogisticsCODRemittanceReceiptOut,
    LogisticsFinancialSummaryOut,
    LogisticsSettlementOut,
    ReconciliationSummaryOut,
    RefundLedgerOut,
    SupplierFinancialSummaryOut,
    SupplierSettlementOut,
    VATRemittanceCreate,
    VATRemittanceOut,
)

from infrastructure.utils.dependencies import get_current_user
from infrastructure.utils.config import settings

from domains.finance.services.treasury.cash_management_service import CashManagementService

ctrl = CashManagementService(None)


def _get_general_ledger_service():
    """Lazy import to avoid circular dependency."""
    from domains.finance.services.ledger.general_ledger_service import (
        delete_supplier_commission_override as _delete_supplier_commission_override,
        get_product_commission_override as _get_product_commission_override,
        list_product_commission_overrides as _list_product_commission_overrides,
        set_product_commission_override as _set_product_commission_override,
    )
    return _delete_supplier_commission_override, _get_product_commission_override, _list_product_commission_overrides, _set_product_commission_override

class FlagRequest(BaseModel):
    reason: str

class CodRemittanceRequest(BaseModel):
    amount: float

class BadgeBillingPaymentRequest(BaseModel):
    payment_method: str
    transaction_ref: Optional[str] = None
    notes: Optional[str] = None

class PayoutProcessRequest(BaseModel):
    settlement_ids: list[int] = []

class ReceiptReviewRequest(BaseModel):
    note: Optional[str] = None

def admin_financial_summary(db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_get_financial_summary(db)

def admin_reconciliation_summary(db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_get_reconciliation_summary(db)

def admin_list_ledger(skip: int, limit: int, order_id: Optional[int], supplier_id: Optional[int], settlement_status: Optional[str], payment_method: Optional[str], category_slug: Optional[str], badge_level: Optional[str], calculation_method: Optional[str], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_ledger_entries(
        db, skip=skip, limit=limit,
        order_id=order_id, supplier_id=supplier_id,
        settlement_status=settlement_status, payment_method=payment_method,
        category_slug=category_slug, badge_level=badge_level, calculation_method=calculation_method,
    )

def admin_list_badge_billings(skip: int, limit: int, supplier_id: Optional[int], status: Optional[str], badge_level: Optional[str], charge_type: Optional[str], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_badge_billing_records(
        db,
        skip=skip,
        limit=limit,
        supplier_id=supplier_id,
        status=status,
        badge_level=badge_level,
        charge_type=charge_type,
    )

def admin_record_badge_billing_payment(billing_id: int, body: BadgeBillingPaymentRequest, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_record_badge_billing_payment(
        billing_id=billing_id,
        payment_method=body.payment_method,
        current_admin=current_admin,
        db=db,
        transaction_ref=body.transaction_ref,
        notes=body.notes,
    )
    db.commit()
    return result

def admin_list_supplier_settlements(skip: int, limit: int, supplier_id: Optional[int], status: Optional[str], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_supplier_settlements(db, skip=skip, limit=limit, supplier_id=supplier_id, status=status)

def admin_list_logistics_settlements(skip: int, limit: int, partner_id: Optional[int], status: Optional[str], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_logistics_settlements(db, skip=skip, limit=limit, partner_id=partner_id, status=status)

def admin_list_bank_transactions(skip: int, limit: int, source: Optional[str], category: Optional[str], reconciled: Optional[bool], flagged: Optional[bool], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_bank_transactions(
        db, skip=skip, limit=limit,
        source=source, category=category,
        reconciled=reconciled, flagged=flagged,
    )

def admin_list_refunds(skip: int, limit: int, status: Optional[str], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_refunds(db, skip=skip, limit=limit, status=status)

def admin_list_vat_remittances(skip: int, limit: int, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_vat_remittance_records(db, skip=skip, limit=limit)

def admin_get_bank_settings(db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_get_finance_bank_settings(db)

def admin_list_transfer_providers(db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_transfer_providers(db)

def admin_test_bank_settings_connection(db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_test_finance_bank_connection(db)

def admin_upsert_bank_settings(body: FinanceBankSettingsUpdate, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_upsert_finance_bank_settings(body.model_dump(), current_admin, db)
    db.commit()
    return result

def admin_record_vat_remittance(body: VATRemittanceCreate, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_record_vat_remittance(body.model_dump(), current_admin, db)
    db.commit()
    return result

def admin_create_bank_transaction(data: BankTransactionCreate, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_create_bank_transaction(data.model_dump(), db)
    db.commit()
    return result

def admin_import_bank_transactions(items: list[BankTransactionImportItem], auto_reconcile: bool, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_import_bank_transactions(
        [item.model_dump() for item in items],
        current_admin,
        db,
        auto_reconcile=auto_reconcile,
    )
    db.commit()
    return result

def admin_reconcile_transaction(txn_id: int, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_reconcile_transaction(txn_id, current_admin, db)
    db.commit()
    return result

def admin_flag_transaction(txn_id: int, body: FlagRequest, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_flag_transaction(txn_id, body.reason, db)
    db.commit()
    return result

def admin_resolve_transaction(txn_id: int, body: BankTransactionResolutionIn, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_resolve_transaction_exception(txn_id, body.model_dump(), current_admin, db)
    db.commit()
    return result

def admin_auto_reconcile_transactions(limit: int, source: Optional[str], category: Optional[str], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_auto_reconcile_transactions(
        current_admin,
        db,
        limit=limit,
        source=source,
        category=category,
    )
    db.commit()
    return result

def admin_trigger_supplier_payouts(body: Optional[PayoutProcessRequest], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    results = ctrl.admin_trigger_supplier_payouts(db, settlement_ids=(body.settlement_ids if body else None))
    db.commit()
    return {"processed": len(results), "payouts": results}

def admin_trigger_logistics_payouts(body: Optional[PayoutProcessRequest], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    results = ctrl.admin_trigger_logistics_payouts(db, settlement_ids=(body.settlement_ids if body else None))
    db.commit()
    return {"processed": len(results), "payouts": results}

def admin_dispatch_payouts(kind: str, provider: Optional[str], dry_run: bool, background: bool, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    if background:
        return ctrl.admin_queue_dispatch_transfer_batch(
            kind,
            current_admin,
            provider=provider,
            dry_run=dry_run,
        )

    result = ctrl.admin_dispatch_transfer_batch(
        kind,
        current_admin,
        db,
        provider=provider,
        dry_run=dry_run,
    )
    db.commit()
    return result

def admin_record_cod_remittance(settlement_id: int, body: CodRemittanceRequest, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_record_cod_remittance(settlement_id, body.amount, current_admin, db)
    db.commit()
    return {"status": "ok", "settlement_id": result.id, "cod_remittance_status": result.cod_remittance_status}

def admin_list_cod_remittance_receipts(skip: int, limit: int, partner_id: Optional[int], status: Optional[str], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_cod_remittance_receipts(db, skip=skip, limit=limit, partner_id=partner_id, status=status)

def admin_verify_cod_remittance_receipt(receipt_id: int, body: Optional[ReceiptReviewRequest], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_verify_cod_remittance_receipt(receipt_id, current_admin, db, note=body.note if body else None)
    db.commit()
    return result

def admin_reject_cod_remittance_receipt(receipt_id: int, body: ReceiptReviewRequest, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_reject_cod_remittance_receipt(receipt_id, current_admin, db, note=body.note or "")
    db.commit()
    return result

def supplier_financial_summary(db: Session, current_user: dict):
    if current_user.get("role") not in ("supplier", "admin"):
        return {"error": "Supplier access required"}, 403
    return ctrl.supplier_get_financial_summary(current_user["id"], db)

def supplier_list_settlements(skip: int, limit: int, status: Optional[str], db: Session, current_user: dict):
    if current_user.get("role") not in ("supplier", "admin"):
        return []
    return ctrl.supplier_list_settlements(current_user["id"], db, skip=skip, limit=limit, status=status)

def supplier_list_ledger(skip: int, limit: int, db: Session, current_user: dict):
    if current_user.get("role") not in ("supplier", "admin"):
        return []
    return ctrl.supplier_list_ledger_entries(current_user["id"], db, skip=skip, limit=limit)

def logistics_financial_summary(db: Session, current_user: dict):
    from domains.logistics.models.logistics import LogisticsPartner
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == current_user["id"]).first()
    if not partner:
        return {"error": "Logistics partner not found"}, 404
    return ctrl.logistics_get_financial_summary(partner.id, db)

def logistics_list_settlements(skip: int, limit: int, status: Optional[str], db: Session, current_user: dict):
    from domains.logistics.models.logistics import LogisticsPartner
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == current_user["id"]).first()
    if not partner:
        return []
    return ctrl.logistics_list_settlements(partner.id, db, skip=skip, limit=limit, status=status)

def logistics_list_ledger(skip: int, limit: int, db: Session, current_user: dict):
    from domains.logistics.models.logistics import LogisticsPartner
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == current_user["id"]).first()
    if not partner:
        return []
    return ctrl.logistics_list_ledger_entries(partner.id, db, skip=skip, limit=limit)




# === Merged from commission_service.py ===


from typing import Optional

from fastapi import Depends, Query

from pydantic import BaseModel, Field

from sqlalchemy.orm import Session

from domains.finance.services.ledger.general_ledger_service import (
    get_global_config, update_global_config, list_category_rates, update_category_rate,
    list_badge_tiers, update_badge_tier, list_ledger_entries, create_ledger_adjustment,
    preview_commission, list_all_supplier_commissions, get_supplier_commission,
    set_supplier_commission, delete_supplier_commission_override,
    get_product_commission_override, list_product_commission_overrides,
    set_product_commission_override, delete_product_commission_override,
)
from infrastructure.database.database import get_db

from infrastructure.database.schemas import ListPage

class CommissionRateBody(BaseModel):
    rate: float = Field(..., ge=0.0, le=1.0, description="Commission rate as decimal, e.g. 0.12 for 12%")
    note: Optional[str] = Field(None, max_length=500)

class GlobalConfigBody(BaseModel):
    default_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    low_value_threshold: Optional[float] = Field(None, ge=0.0)
    fixed_cap_amount: Optional[float] = Field(None, ge=0.0)
    fixed_cap_enabled: Optional[bool] = None
    margin_protection_enabled: Optional[bool] = None
    margin_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)

class CategoryRateBody(BaseModel):
    rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)
    category_display_name: Optional[str] = Field(None, max_length=150)

class BadgeTierBody(BaseModel):
    commission_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    setup_fee: Optional[float] = Field(None, ge=0.0)
    recurring_fee: Optional[float] = Field(None, ge=0.0)
    recurring_interval: Optional[str] = Field(None, max_length=20)
    benefits_json: Optional[str] = None
    min_fulfilled_orders: Optional[int] = None
    min_monthly_revenue: Optional[float] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class LedgerAdjustmentBody(BaseModel):
    new_amount: float = Field(..., ge=0.0)
    reason: str = Field(..., min_length=5, max_length=1000)

class PreviewBody(BaseModel):
    supplier_id: int
    order_value: float = Field(..., gt=0.0)
    category_slug: Optional[str] = None

def get_global_config(db: Session, current_user: dict):
    return get_global_config(db)

def update_global_config(body: GlobalConfigBody, db: Session, current_user: dict):
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    return update_global_config(payload, current_user, db)

def list_category_rates(page: int, page_size: int, search: Optional[str], db: Session, current_user: dict):
    return list_category_rates(db, limit=page_size, offset=(page - 1) * page_size, search=search)

def update_category_rate(category_slug: str, body: CategoryRateBody, db: Session, current_user: dict):
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    return update_category_rate(category_slug, payload, current_user, db)

def list_badge_tiers(page: int, page_size: int, search: Optional[str], db: Session, current_user: dict):
    return list_badge_tiers(db, limit=page_size, offset=(page - 1) * page_size, search=search)

def update_badge_tier(badge_level: str, body: BadgeTierBody, db: Session, current_user: dict):
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    return update_badge_tier(badge_level, payload, current_user, db)

def list_ledger_entries(supplier_id: Optional[int], order_id: Optional[int], skip: int, limit: int, db: Session, current_user: dict):
    return list_ledger_entries(db, supplier_id, order_id, skip, limit)

def adjust_ledger_entry(ledger_id: int, body: LedgerAdjustmentBody, db: Session, current_user: dict):
    return create_ledger_adjustment(
        ledger_id=ledger_id,
        new_amount=body.new_amount,
        reason=body.reason,
        acting_user=current_user,
        db=db,
    )

def preview_commission(body: PreviewBody, db: Session, current_user: dict):
    return preview_commission(
        supplier_id=body.supplier_id,
        order_value=body.order_value,
        category_slug=body.category_slug,
        db=db,
    )

def list_supplier_commissions(page: int, page_size: int, search: Optional[str], db: Session, current_user: dict):
    return list_all_supplier_commissions(db, limit=page_size, offset=(page - 1) * page_size, search=search)

def get_supplier_commission(supplier_id: int, db: Session, current_user: dict):
    return get_supplier_commission(supplier_id, db)

def set_supplier_commission(supplier_id: int, body: CommissionRateBody, db: Session, current_user: dict):
    return set_supplier_commission(
        supplier_id=supplier_id,
        rate=body.rate,
        note=body.note,
        acting_user=current_user,
        db=db,
    )

def delete_supplier_commission_override(supplier_id: int, db: Session, current_user: dict):
    _delete_supplier_commission_override, _, _, _ = _get_general_ledger_service()
    return _delete_supplier_commission_override(
        supplier_id=supplier_id,
        acting_user=current_user,
        db=db,
    )

def get_product_commission_override(product_id: int, db: Session, current_user: dict):
    _, _get_product_commission_override, _, _ = _get_general_ledger_service()
    result = _get_product_commission_override(product_id, db)
    if result is None:
        return {"override": None, "message": "No override - using category/badge/default rate"}
    return result

def list_product_commission_overrides(search: Optional[str], supplier_id: Optional[int], limit: int, db: Session, current_user: dict):
    _, _, _list_product_commission_overrides, _ = _get_general_ledger_service()
    return _list_product_commission_overrides(
        db,
        search=search,
        supplier_id=supplier_id,
        limit=limit,
    )

def set_product_commission_override(product_id: int, body: CommissionRateBody, db: Session, current_user: dict):
    _, _, _, _set_product_commission_override = _get_general_ledger_service()
    return _set_product_commission_override(
        product_id=product_id,
        rate=body.rate,
        note=body.note,
        acting_user=current_user,
        db=db,
    )

def delete_product_commission_override(product_id: int, db: Session, current_user: dict):
    return delete_product_commission_override(
        product_id=product_id,
        acting_user=current_user,
        db=db,
    )

def get_effective_rate(supplier_id: int, product_id: Optional[int], category_slug: Optional[str], db: Session, current_user: dict):
    from domains.finance.services.commission_engine import get_effective_rate as _engine_rate
    result = _engine_rate(supplier_id=supplier_id, product_id=product_id,
                          category_slug=category_slug, db=db)
    return {
        "rate": float(result.applied_rate),
        "percentage": f"{float(result.applied_rate) * 100:.2f}%",
        "calculation_method": result.calculation_method,
        "supplier_rate": float(result.supplier_rate),
        "supplier_rate_source": result.supplier_rate_source,
        "base_rate": float(result.base_rate),
        "base_rate_source": result.base_rate_source,
        "product_override_rate": float(result.product_override_rate) if result.product_override_rate else None,
        "badge_level": result.badge_level,
        "category_slug": result.category_slug,
        "override_flag": result.override_flag,
    }



# === Merged from flat_admin_finance_geography_service.py ===

"""Auto-migrated service logic from routers/admin_finance_geography.py."""


from fastapi import Depends, Path, Query

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from domains.governance.models.user import User

from infrastructure.database.schemas import CommissionCategoryRateCreate, CommissionCategoryRateOut, CommissionBadgeTierCreate, CommissionBadgeTierOut

from infrastructure.utils.dependencies import require_admin

from domains.country.utils.country_rls import get_country_or_404

from infrastructure.database.rls_interceptor import set_rls_context, clear_rls_context

# TODO: Module not yet created
# from domains.finance.services.commission.commission_geography_service import create_badge_tier
# TODO: Module not yet created
# from domains.finance.services.commission.commission_geography_service import create_category_rate
# TODO: Module not yet created
# from domains.finance.services.commission.commission_geography_service import list_badge_tiers
# TODO: Module not yet created
# from domains.finance.services.commission.commission_geography_service import list_category_rates
# TODO: Module not yet created
# from domains.finance.services.commission.commission_geography_service import update_badge_tier
# TODO: Module not yet created
# from domains.finance.services.commission.commission_geography_service import update_category_rate

def list_rates(country_code: str, _: User, db: Session, page: int, page_size: int):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return list_category_rates(db, country_code, page, page_size)
    finally:
        clear_rls_context()

def create_rate(country_code: str, payload: CommissionCategoryRateCreate, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return create_category_rate(db, payload, country_code)
    finally:
        clear_rls_context()

def update_rate(country_code: str, rate_id: int, payload: CommissionCategoryRateCreate, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    return update_category_rate(db, rate_id, country_code, payload)

def list_badge_tiers_route(country_code: str, _: User, db: Session, page: int, page_size: int):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return list_badge_tiers(db, country_code, page, page_size)
    finally:
        clear_rls_context()

def create_badge_tier_route(country_code: str, payload: CommissionBadgeTierCreate, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return create_badge_tier(db, payload, country_code)
    finally:
        clear_rls_context()

def update_badge_tier_route(country_code: str, tier_id: int, payload: CommissionBadgeTierCreate, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    return update_badge_tier(db, tier_id, country_code, payload)


# ?? Provider-wired helpers ??


def verify_bank_connection(base_url: str, api_key: str):
    """Probe the bank API for connectivity using the finance provider."""
    try:
        result = test_connection(
            base_url,
            batch_path=settings.bank_api_batch_path,
            auth_token=api_key,
            timeout=float(settings.bank_api_timeout_seconds),
        )
        return {"connected": result.get("ok", False), "message": result.get("detail", "")}
    except BankApiError as exc:
        return {"connected": False, "message": str(exc)}


def reconcile_in_multi_currency(amount: float, from_currency: str, to_currency: str = "USD"):
    """Convert an amount between currencies using live FX rates from the geography provider."""
    try:
        rates, _source = fetch_rates()
        from_key = from_currency.upper()
        to_key = to_currency.upper()
        if from_key == to_key:
            return {"original": amount, "converted": amount, "rate": 1.0}
        base_rate = rates.get(from_key)
        target_rate = rates.get(to_key)
        if base_rate is None or target_rate is None:
            return {"original": amount, "converted": None, "rate": None, "error": f"Rate unavailable for {from_currency}/{to_currency}"}
        rate = float(target_rate) / float(base_rate)
        converted = round(amount * rate, 2)
        return {"original": amount, "converted": converted, "rate": rate}
    except Exception as exc:
        return {"original": amount, "converted": None, "rate": None, "error": str(exc)}


def create_stripe_connect_account(**kwargs):
    """Create a Stripe Connect account via the payments provider."""
    return create_connect_account(**kwargs)


def general_ledger_service():
    """Access the general ledger service."""
    from domains.finance.services.ledger.general_ledger_service import GeneralLedgerService
    return GeneralLedgerService


