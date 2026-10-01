"""Supplier finance router — thin wrappers over finance domain services."""

from typing import Optional

from fastapi import APIRouter, Depends, Body, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_supplier, require_admin
from infrastructure.database.schemas import ListPage
from rbac.dependencies import require_feature

from domains.finance.services.ledger.general_ledger_service import (
    delete_supplier_commission_override,
    get_effective_rate,
    get_global_config,
    get_product_commission_override,
    get_supplier_commission,
    list_all_supplier_commissions,
    list_badge_tiers,
    list_category_rates,
    list_ledger_entries,
    preview_commission,
    update_category_rate,
    update_global_config,
)
from domains.finance.services.country.supplier_finance_service import (
    get_order_payment_status,
    get_supplier_bank_account,
    get_supplier_payout_summary,
    list_supplier_orders_with_payout_status,
    upsert_supplier_bank_account,
)
from domains.suppliers.ports import (
    list_payouts,
    request_payout,
)

router = APIRouter(prefix="/api/v1/supplier/finance", tags=["supplier", "finance"])


class GlobalConfigRequest(BaseModel):
    default_rate: float = Field(..., ge=0, le=100)
    min_payout_amount: float = Field(0, ge=0)
    max_commission_rate: float = Field(100, ge=0, le=100)
    currency: str = Field(default="OMR", max_length=3)


class CategoryRateRequest(BaseModel):
    rate: float = Field(..., ge=0, le=100)
    category_slug: str = Field(..., min_length=1, max_length=100)


class PreviewCommissionRequest(BaseModel):
    supplier_id: int = Field(..., gt=0)
    order_value: float = Field(..., gt=0)
    category_slug: str | None = Field(None, max_length=100)


class BankAccountRequest(BaseModel):
    bank_name: str = Field(..., min_length=1, max_length=200)
    account_holder: str = Field(..., min_length=1, max_length=200)
    account_number: str = Field(..., min_length=1, max_length=50)
    iban: str | None = Field(None, max_length=50)
    swift_code: str | None = Field(None, max_length=20)


class PayoutRequest(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = Field(default="OMR", max_length=3)
    notes: str | None = Field(None, max_length=500)


# ── Commission (admin) ────────────────────────────────────────────────────────

@router.get("/global")
def get_global_config_route(
    db: Session = Depends(get_db), _: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.commission.read")),
):
    return get_global_config(db)


@router.put("/global")
def update_global_config_route(
    body: GlobalConfigRequest, db: Session = Depends(get_db), _: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.commission.write")),
):
    return update_global_config(body.model_dump(exclude_unset=True), _, db)


@router.get("/categories", response_model=ListPage[dict])
def list_category_rates_route(
    page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=500),
    search: Optional[str] = None, db: Session = Depends(get_db), _: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.commission.read")),
):
    return list_category_rates(db, limit=page_size, offset=(page - 1) * page_size, search=search)


@router.put("/categories/{category_slug}")
def update_category_rate_route(
    category_slug: str, body: CategoryRateRequest, db: Session = Depends(get_db), _: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.commission.write")),
):
    return update_category_rate(category_slug, body.model_dump(exclude_unset=True), _, db)


@router.get("/badge-tiers", response_model=ListPage[dict])
def list_badge_tiers_route(
    page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=500),
    search: Optional[str] = None, db: Session = Depends(get_db), _: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.commission.read")),
):
    return list_badge_tiers(db, limit=page_size, offset=(page - 1) * page_size, search=search)


@router.get("/ledger")
def list_ledger_entries_route(
    supplier_id: Optional[int] = None, order_id: Optional[int] = None,
    skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db), _: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.ledger.read")),
):
    return list_ledger_entries(db, supplier_id=supplier_id, order_id=order_id, skip=skip, limit=limit)


@router.post("/preview")
def preview_commission_route(
    body: PreviewCommissionRequest, db: Session = Depends(get_db), _: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.commission.read")),
):
    return preview_commission(
        supplier_id=body.supplier_id, order_value=body.order_value,
        category_slug=body.category_slug, db=db,
    )


@router.get("/suppliers", response_model=ListPage[dict])
def list_supplier_commissions_route(
    page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=500),
    search: Optional[str] = None, db: Session = Depends(get_db), _: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.commission.read")),
):
    return list_all_supplier_commissions(db, limit=page_size, offset=(page - 1) * page_size, search=search)


@router.get("/suppliers/{supplier_id}")
def get_supplier_commission_route(
    supplier_id: int, db: Session = Depends(get_db), _: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.commission.read")),
):
    return get_supplier_commission(supplier_id, db)


@router.delete("/suppliers/{supplier_id}")
def delete_supplier_commission_override_route(
    supplier_id: int, db: Session = Depends(get_db), _: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.commission.write")),
):
    return delete_supplier_commission_override(supplier_id=supplier_id, acting_user=_, db=db)


@router.get("/products/{product_id}")
def get_product_commission_override_route(
    product_id: int, db: Session = Depends(get_db), _: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.commission.read")),
):
    return get_product_commission_override(product_id, db)


@router.get("/effective-rate")
def get_effective_rate_route(
    supplier_id: int, product_id: Optional[int] = None, category_slug: Optional[str] = None,
    db: Session = Depends(get_db), _: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.commission.read")),
):
    rate = get_effective_rate(supplier_id=supplier_id, product_id=product_id, db=db)
    return {"rate": float(rate), "method": "effective"}


# ── Payout status (supplier) ─────────────────────────────────────────────────

@router.get("/payout-status/summary")
def get_supplier_payout_summary_route(
    current_user=Depends(require_supplier), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.payout.read")),
):
    return get_supplier_payout_summary(db, current_user.id)


@router.get("/orders/{order_id}/payment-status")
def get_order_payment_status_route(
    order_id: int, current_user=Depends(require_supplier), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.payout.read")),
):
    return get_order_payment_status(db, order_id, current_user.id)


@router.get("/payout-status/orders")
def list_supplier_orders_with_payout_status_route(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = None, current_user=Depends(require_supplier), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.payout.read")),
):
    return list_supplier_orders_with_payout_status(db, current_user.id, page, page_size, status_filter)


@router.get("/bank-account")
def get_supplier_bank_account_route(
    current_user=Depends(require_supplier), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.bank.read")),
):
    return get_supplier_bank_account(db, current_user.id)


@router.put("/bank-account")
def upsert_supplier_bank_account_route(
    body: BankAccountRequest, current_user=Depends(require_supplier), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.bank.write")),
):
    return upsert_supplier_bank_account(db, current_user.id, body.model_dump())


# ── Payouts ───────────────────────────────────────────────────────────────────

@router.get("/payouts")
def list_payouts_route(current_user=Depends(require_supplier), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.payout.read")),
):
    return list_payouts(current_user=current_user, db=db, page=page, page_size=page_size)


@router.post("/payouts/request")
def request_payout_route(
    body: PayoutRequest, current_user=Depends(require_supplier), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.payout.write")),
):
    return request_payout(body.model_dump(), current_user, db)
