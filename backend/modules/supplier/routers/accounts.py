"""Supplier accounts router — self-service account, security, sessions, bank accounts.

Auth (login/refresh/logout/me) is shared and exposed by the platform auth router.
This router is a thin wrapper over the accounts and finance domains.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import get_current_user, require_supplier
from infrastructure.database.schemas import ChangePasswordRequest
from rbac.dependencies import require_feature

from domains.accounts.services.auth.auth_service import (
    change_password,
    disable_totp,
    enable_totp,
    get_totp_status,
    setup_totp,
)
from domains.accounts.services.sessions.session_service import (
    list_sessions,
    revoke_session,
)
from domains.suppliers.ports import (
    get_supplier_bank_account,
    upsert_supplier_bank_account,
    get_supplier_profile,
    update_supplier_profile,
)

router = APIRouter(prefix="/api/v1/supplier/accounts", tags=["supplier", "accounts"])


# ── Schemas ───────────────────────────────────────────────────────────────────


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    phone: Optional[str] = Field(None, max_length=32)
    profile_image: Optional[str] = Field(None, max_length=500)
    company_name: Optional[str] = Field(None, min_length=1, max_length=200)
    business_email: Optional[str] = Field(None, max_length=200)
    business_phone: Optional[str] = Field(None, max_length=32)
    address_line1: Optional[str] = Field(None, max_length=300)
    address_line2: Optional[str] = Field(None, max_length=300)
    city: Optional[str] = Field(None, max_length=120)
    state: Optional[str] = Field(None, max_length=120)
    postal_code: Optional[str] = Field(None, max_length=32)
    country_code: Optional[str] = Field(None, min_length=2, max_length=2)


class TotpEnableRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=10)


class TotpDisableRequest(BaseModel):
    password: str = Field(..., min_length=1)


class BankAccountRequest(BaseModel):
    bank_name: str = Field(..., min_length=1, max_length=200)
    beneficiary_name: Optional[str] = Field(None, min_length=1, max_length=200)
    account_number: Optional[str] = Field(None, min_length=1, max_length=50)
    iban: Optional[str] = Field(None, max_length=50)
    swift_code: Optional[str] = Field(None, max_length=20)
    routing_number: Optional[str] = Field(None, max_length=50)
    branch_name: Optional[str] = Field(None, max_length=200)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    bank_country: Optional[str] = Field(None, min_length=2, max_length=3)


# ── Profile ───────────────────────────────────────────────────────────────────


@router.get("/profile")
def get_profile_route(
    current_user: Any = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    require_feature("suppliers.profile.read")
    return get_supplier_profile(db, current_user.id)


@router.put("/profile")
def update_profile_route(
    body: ProfileUpdateRequest,
    current_user: Any = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    require_feature("suppliers.profile.write")
    profile = update_supplier_profile(body.model_dump(exclude_unset=True), current_user, db)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


# ── Password & Security ───────────────────────────────────────────────────────


@router.post("/change-password")
def change_password_route(
    body: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature("accounts.password.change")
    return change_password(body, current_user, db)


@router.get("/totp/status")
def totp_status_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature("accounts.mfa.enable")
    return get_totp_status(current_user, db)


@router.post("/totp/setup")
def totp_setup_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature("accounts.mfa.enable")
    return setup_totp(current_user, db)


@router.post("/totp/enable")
def totp_enable_route(
    body: TotpEnableRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature("accounts.mfa.enable")
    return enable_totp(current_user, db, body.code)


@router.post("/totp/disable")
def totp_disable_route(
    body: TotpDisableRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature("accounts.mfa.disable")
    return disable_totp(current_user, db, body.password)


# ── Sessions ──────────────────────────────────────────────────────────────────


@router.get("/sessions")
def list_sessions_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature("accounts.session.manage")
    sessions = list_sessions(int(current_user["sub"]), db)
    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "device_info": getattr(s, "device_info", None),
            "ip_address": getattr(s, "ip_address", None),
            "country_code": getattr(s, "country_code", None),
            "last_activity": s.last_activity.isoformat() if s.last_activity else None,
            "created_at": s.created_at.isoformat() if getattr(s, "created_at", None) else None,
            "is_active": s.is_active,
        }
        for s in sessions
    ]


@router.delete("/sessions/{session_id}")
def revoke_session_route(
    session_id: int = Path(..., ge=1),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature("accounts.session.revoke")
    revoked = revoke_session(int(current_user["sub"]), session_id, db)
    if not revoked:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"detail": "Session revoked", "session_id": session_id}


# ── Bank Accounts (supplier-facing) ───────────────────────────────────────────


@router.get("/bank-accounts")
def get_bank_account_route(
    current_user: Any = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    require_feature("finance.bank.read")
    return get_supplier_bank_account(current_user, db)


@router.post("/bank-accounts")
def create_bank_account_route(
    body: BankAccountRequest,
    current_user: Any = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    require_feature("finance.bank.write")
    return upsert_supplier_bank_account(body.model_dump(exclude_unset=True), current_user, db)


@router.put("/bank-accounts/{account_id}")
def update_bank_account_route(
    body: BankAccountRequest,
    account_id: int = Path(..., ge=1),
    current_user: Any = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    require_feature("finance.bank.write")
    payload = body.model_dump(exclude_unset=True)
    payload["account_id"] = account_id
    return upsert_supplier_bank_account(payload, current_user, db)


@router.delete("/bank-accounts/{account_id}")
def delete_bank_account_route(
    account_id: int = Path(..., ge=1),
    current_user: Any = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    require_feature("finance.bank.write")
    from domains.governance.models.admin import SupplierBankAccount

    account = (
        db.query(SupplierBankAccount)
        .filter(
            SupplierBankAccount.id == account_id,
            SupplierBankAccount.supplier_id == current_user.id,
        )
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    account.is_active = False
    db.commit()
    return {"detail": "Bank account deactivated", "account_id": account_id}
