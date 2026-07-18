from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from controllers.treasury_controller import (
    get_treasury_metrics,
    get_cash_position,
    get_vat_liability,
    get_supplier_payables,
)
from controllers.auth_controller import get_current_user
from controllers.audit_controller import AuditAction, audit_log

router = APIRouter()


@router.get("/metrics")
def treasury_metrics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = get_treasury_metrics(db)
    audit_log(
        db=db,
        action=AuditAction.TRIAL_BALANCE_VIEWED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="treasury_metrics",
    )
    return result


@router.get("/cash-position")
def cash_position(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = get_cash_position(db)
    audit_log(
        db=db,
        action=AuditAction.FINANCIAL_REPORT_GENERATED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="cash_position",
    )
    return result


@router.get("/vat-liability")
def vat_liability(
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = get_vat_liability(db, country_code)
    audit_log(
        db=db,
        action=AuditAction.FINANCIAL_REPORT_GENERATED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="vat_liability",
        details={"country_code": country_code},
    )
    return result


@router.get("/supplier-payables")
def supplier_payables(
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = get_supplier_payables(db, country_code)
    audit_log(
        db=db,
        action=AuditAction.FINANCIAL_REPORT_GENERATED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="supplier_payables",
        details={"country_code": country_code},
    )
    return result

