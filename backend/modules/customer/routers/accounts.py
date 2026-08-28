"""Customer accounts router — consolidated from 3 source files."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, Request, Response, UploadFile, File, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from infrastructure.security.dependencies import get_current_user
from infrastructure.database.database import get_db
from domains.accounts.services.addresses.addresses_service import create_address as create_address_model
from domains.accounts.services.addresses.addresses_service import update_address as update_address_model
from domains.accounts.services.addresses.addresses_service import delete_address as delete_address_model
from domains.accounts.services.addresses.addresses_service import set_default_address as set_default_address_model
from domains.accounts.services.auth.auth_service import (
    ForgotPasswordRequest,
    LoginRequest,
    PublicResendVerificationRequest,
    RefreshTokenBody,
    ResetPasswordRequest,
    SocialLoginRequest,
    change_password,
    complete_totp_login,
    disable_totp,
    enable_totp,
    forgot_password,
    get_facebook_oauth_start,
    get_google_oauth_start,
    get_totp_status,
    handle_facebook_oauth_callback,
    handle_google_oauth_callback,
    json_login_user,
    json_register_user,
    logout_user,
    refresh_access_token,
    register_user,
    resend_verification,
    resend_verification_public,
    reset_password,
    setup_totp,
    update_profile,
    upload_avatar,
    verify_email_token,
)
from domains.accounts.services.gdpr_service import delete_user_data, export_user_data
from domains.accounts.services.sessions.session_service import list_sessions, revoke_session
from domains.customers.ports import unset_other_default_addresses
from domains.customers.ports import list_user_addresses
from domains.customers.ports import get_user_address
from domains.customers.ports import get_coin_summary, redeem_coins
from domains.customers.ports import get_may_you_like, get_last_seen
from infrastructure.database.schemas import UserCreate
from rbac.dependencies import require_feature


router = APIRouter(tags=["customer", "accounts"])


# === Pydantic schemas for address endpoints ===

class AddressBase(BaseModel):
    label: Optional[str] = None
    street: Optional[str] = Field(None, description="Primary street line (alias for address_line1)")
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    is_default: Optional[bool] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None


class AddressCreate(AddressBase):
    street: str = Field(..., description="Primary street line (required)")
    city: str = Field(..., description="City (required)")
    country: str = Field(..., description="Country (required)")


class AddressUpdate(AddressBase):
    pass


# === From addresses.py ===
"""Address routes with compatibility for the recovered customer address contract."""


def _normalize_address_payload(payload: dict, *, partial: bool = False) -> dict:
    street = payload.get("street", payload.get("address_line1"))
    state = payload.get("state", payload.get("region"))
    postal_code = payload.get("postal_code", payload.get("zip"))
    normalized = {
        "label": payload.get("label"),
        "street": street,
        "city": payload.get("city"),
        "state": state,
        "postal_code": postal_code,
        "country": payload.get("country"),
        "is_default": payload.get("is_default"),
    }
    if partial:
        return {key: value for key, value in normalized.items() if value is not None}
    required = {"street": street, "city": payload.get("city"), "country": payload.get("country")}
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Missing required fields: {', '.join(missing)}")
    return normalized


def _serialize_address(address) -> dict:
    return {
        "id": address.id,
        "user_id": address.user_id,
        "label": getattr(address, "label", None),
        "street": address.address_line1,
        "address_line1": address.address_line1,
        "address_line2": address.address_line2,
        "city": address.city,
        "state": address.state,
        "postal_code": address.postal_code,
        "country": address.country,
        "is_default": address.is_default,
        "full_name": address.full_name,
        "phone": address.phone,
        "created_at": address.created_at,
    }


def _get_user_address(address_id: int, user_id: int, db: Session):
    return get_user_address(db, address_id, user_id)


def _payload_to_dict(payload) -> dict:
    return payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else dict(payload)


@router.get("/api/v1/customer/accounts")
def list_addresses(limit: int = 100, offset: int = 0, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.address.read"))
):
    rows = list_user_addresses(db, current_user.id, limit, offset)
    return [_serialize_address(row) for row in rows]


@router.post("/api/v1/customer/accounts", status_code=status.HTTP_201_CREATED)
def create_address(payload: AddressCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.address.create"))
):
    normalized = _normalize_address_payload(_payload_to_dict(payload))
    user_id = int(current_user.id)
    if normalized.get("is_default"):
        unset_other_default_addresses(db, user_id)
    address_data = {
        "user_id": user_id,
        "full_name": "Customer",
        "address_line1": normalized.get("street", ""),
        "city": normalized.get("city", ""),
        "state": normalized.get("state"),
        "postal_code": normalized.get("postal_code"),
        "country": normalized.get("country", "US"),
        "is_default": normalized.get("is_default", False),
    }
    if normalized.get("label"):
        address_data["label"] = normalized["label"]
    if normalized.get("phone"):
        address_data["phone"] = normalized["phone"]
    address = create_address_model(db, **address_data)
    return _serialize_address(address)


@router.put("/api/v1/customer/accounts/{address_id}")
def update_address(address_id: int, payload: AddressUpdate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.address.update"))
):
    address = _get_user_address(address_id, int(current_user.id), db)
    updates = _normalize_address_payload(_payload_to_dict(payload), partial=True)
    if updates.get("is_default") is True:
        unset_other_default_addresses(db, int(current_user.id), address_id)
    if "street" in updates:
        updates.pop("street")
    address = update_address_model(db, address, updates)
    return _serialize_address(address)


@router.delete("/api/v1/customer/accounts/{address_id}")
def delete_address(address_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.address.delete"))
):
    address = _get_user_address(address_id, int(current_user.id), db)
    delete_address_model(db, address)
    return {"detail": "Deleted"}


@router.post("/api/v1/customer/accounts/{address_id}/set-default")
def set_default_address(address_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.address.update"))
):
    user_id = int(current_user.id)
    unset_other_default_addresses(db, user_id, address_id)
    address = _get_user_address(address_id, user_id, db)
    address = set_default_address_model(db, address)
    return _serialize_address(address)


# === From auth.py ===
"""Auth router — login, refresh, me, logout."""


@router.post("/api/v1/auth/login", tags=["auth"])
def login(
    response: Response,
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.session.manage")),
):
    return json_login_user(response=response, login_data=login_data, db=db, request=request)


@router.post("/api/v1/auth/refresh", tags=["auth"])
def refresh(
    request: Request,
    response: Response,
    body: RefreshTokenBody = None,
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.session.manage")),
):
    body_refresh_token = body.refresh_token if body else None
    return refresh_access_token(
        request=request,
        response=response,
        db=db,
        body_refresh_token=body_refresh_token,
    )


@router.get("/api/v1/auth/me", tags=["auth"])
def me(current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("accounts.user.read"))
):
    return current_user


@router.post("/api/v1/auth/logout", tags=["auth"])
def logout(
    request: Request,
    response: Response,
    body: RefreshTokenBody = None,
    _rf_gate: None = Depends(require_feature("accounts.session.manage")),
):
    body_refresh_token = body.refresh_token if body else None
    return logout_user(request=request, response=response, body_refresh_token=body_refresh_token)


# === From customer.py ===
"""Customer profile router — coins and recommendations."""

# ── Zozi Coins ─────────────────────────────────────────────────────────────────

@router.get("/api/v1/customer/accounts/coins")
def customer_get_coins(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.coins.read")),
):
    """Get the authenticated customer's coin balance and history."""
    return get_coin_summary(db, current_user.id)


@router.post("/api/v1/customer/accounts/coins/redeem")
def customer_redeem_coins(
    points: int = Query(..., gt=0, description="Number of coins to redeem"),
    reason: str = Query("redemption", description="Reason for redemption"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.coins.redeem")),
):
    """Redeem coins from the authenticated customer's balance."""
    return redeem_coins(db, current_user.id, points, reason=reason)


# ── Recommendations ────────────────────────────────────────────────────────────

@router.get("/api/v1/customer/accounts/recommendations")
def customer_get_recommendations(
    limit: int = Query(8, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("catalog.read")),
):
    """Get personalized product recommendations for the authenticated customer."""
    return get_may_you_like(db, current_user.id, limit=limit)


@router.get("/api/v1/customer/accounts/last-seen")
def customer_get_last_seen(
    limit: int = Query(12, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("catalog.read")),
):
    """Get recently viewed products for the authenticated customer."""
    return get_last_seen(db, current_user.id, limit=limit)


# === From auth_accounts.py — Registration & Email Verification ===

@router.post("/api/v1/auth/register", status_code=status.HTTP_201_CREATED, tags=["auth"])
def auth_register(
    response: Response,
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.user.create")),
):
    """Register a new customer and immediately issue tokens.

    Public endpoint — no authentication required. Wraps the mobile-friendly
    ``json_register_user`` helper which also issues a refresh cookie.
    """
    return json_register_user(response=response, user_data=user_data, db=db, request=request)


@router.post("/api/v1/auth/register-form", status_code=status.HTTP_201_CREATED, tags=["auth"])
def auth_register_form(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.user.create")),
):
    """Plain registration that returns the persisted user (no auto-login).

    Public endpoint — no authentication required. Used by admin / support
    flows that only need the created user record.
    """
    return register_user(user=user_data, db=db)


@router.get("/api/v1/auth/verify-email/{token}", tags=["auth"])
def auth_verify_email(
    token: str = Path(..., description="Email verification token sent to the user"),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.email.verify")),
):
    """Verify a user's email address using a token from their inbox.

    Public endpoint — no authentication required.
    """
    return verify_email_token(token=token, db=db)


@router.post("/api/v1/auth/resend-verification", tags=["auth"])
def auth_resend_verification(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.email.verify")),
):
    """Resend the email verification link to the authenticated user."""
    return resend_verification(current_user=current_user, db=db)


@router.post("/api/v1/auth/resend-verification-public", tags=["auth"])
def auth_resend_verification_public(
    payload: PublicResendVerificationRequest,
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.email.verify")),
):
    """Resend the email verification link by email/username (no auth required).

    Always returns a generic response to avoid leaking account existence.
    """
    return resend_verification_public(payload=payload, db=db)


# === Password Management ===

@router.post("/api/v1/auth/forgot-password", tags=["auth"])
def auth_forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.password.reset")),
):
    """Request a password-reset email. Always returns a generic response.

    Public endpoint — no authentication required.
    """
    return forgot_password(body=payload, db=db)


@router.post("/api/v1/auth/reset-password", tags=["auth"])
def auth_reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.password.reset")),
):
    """Reset a password using a valid reset token.

    Public endpoint — no authentication required.
    """
    return reset_password(body=payload, db=db)


@router.post("/api/v1/customer/accounts/change-password", tags=["customer", "accounts"])
def customer_change_password(
    payload: dict = Body(..., description="JSON body with current_password and new_password"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.password.change")),
):
    """Change the authenticated customer's password."""
    current_password = payload.get("current_password") or payload.get("currentPassword")
    new_password = payload.get("new_password") or payload.get("newPassword")
    if not current_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="current_password and new_password are required",
        )
    from infrastructure.database.schemas import ChangePasswordRequest
    body = ChangePasswordRequest(current_password=current_password, new_password=new_password)
    return change_password(body=body, current_user=current_user, db=db)


# === Profile & Avatar ===

@router.put("/api/v1/customer/accounts/profile", tags=["customer", "accounts"])
def customer_update_profile(
    payload: dict = Body(..., description="Profile fields to update (any of username, email, full_name, phone, address_book, profile_image, preferred_*)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.user.update")),
):
    """Update the authenticated customer's profile fields."""
    from infrastructure.database.schemas import ProfileUpdate
    body = ProfileUpdate(**payload)
    updated = update_profile(body=body, current_user=current_user, db=db)
    return {
        "id": updated.id,
        "email": updated.email,
        "username": updated.username,
        "full_name": getattr(updated, "full_name", None),
        "phone": getattr(updated, "phone", None),
        "profile_image": getattr(updated, "profile_image", None),
        "preferred_language": getattr(updated, "preferred_language", None),
        "preferred_currency": getattr(updated, "preferred_currency", None),
        "preferred_country": getattr(updated, "preferred_country", None),
    }


@router.post("/api/v1/customer/accounts/avatar", tags=["customer", "accounts"])
async def customer_upload_avatar(
    file: UploadFile = File(..., description="Avatar image file (JPEG/PNG/WebP)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.user.update")),
):
    """Upload and set the authenticated customer's profile avatar."""
    return await upload_avatar(file=file, current_user=current_user, db=db)


# === 2FA / TOTP ===

@router.get("/api/v1/customer/accounts/totp/status", tags=["customer", "accounts"])
def customer_totp_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.mfa.enable")),
):
    """Return whether TOTP 2FA is enabled for the authenticated customer."""
    return get_totp_status(current_user=current_user, db=db)


@router.post("/api/v1/customer/accounts/totp/setup", tags=["customer", "accounts"])
def customer_totp_setup(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.mfa.enable")),
):
    """Begin TOTP 2FA setup — returns a secret and provisioning URI for QR scanning."""
    return setup_totp(current_user=current_user, db=db)


class _TotpEnableBody(BaseModel):
    code: str = Field(..., min_length=6, max_length=10, description="6-digit TOTP code from authenticator app")


class _TotpDisableBody(BaseModel):
    password: str = Field(..., description="Current account password to confirm disabling 2FA")


@router.post("/api/v1/customer/accounts/totp/enable", tags=["customer", "accounts"])
def customer_totp_enable(
    body: _TotpEnableBody,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.mfa.enable")),
):
    """Confirm a TOTP code and enable 2FA (returns one-time recovery codes)."""
    return enable_totp(current_user=current_user, db=db, code=body.code)


@router.post("/api/v1/customer/accounts/totp/disable", tags=["customer", "accounts"])
def customer_totp_disable(
    body: _TotpDisableBody,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.mfa.disable")),
):
    """Disable TOTP 2FA after verifying the current password."""
    return disable_totp(current_user=current_user, db=db, password=body.password)


class _TotpCompleteBody(BaseModel):
    temp_token: str = Field(..., description="Short-lived temp token returned by the login challenge")
    code: str = Field(..., min_length=6, max_length=20, description="TOTP code or recovery code")


@router.post("/api/v1/auth/totp/complete", tags=["auth"])
def auth_totp_complete(
    response: Response,
    body: _TotpCompleteBody,
    request: Request,
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.mfa.enable")),
):
    """Complete a 2FA login by submitting a TOTP code against a temp challenge token.

    Public endpoint — the temp_token itself is the proof of partial authentication.
    """
    return complete_totp_login(
        temp_token=body.temp_token,
        code=body.code,
        db=db,
        response=response,
        request=request,
    )


# === Social Login ===

@router.get("/api/v1/auth/social/google/start", tags=["auth"])
def auth_social_google_start(    _rf_gate: None = Depends(require_feature("accounts.social.link"))):
    """Begin the Google OAuth flow — returns a 302 redirect to Google's consent screen."""
    return get_google_oauth_start()


@router.get("/api/v1/auth/social/google/callback", tags=["auth"])
def auth_social_google_callback(
    code: str = Query(..., description="Authorization code returned by Google"),
    state: Optional[str] = Query(None, description="OAuth state value to validate"),
    request: Request = None,
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.social.link")),
):
    """Handle the Google OAuth callback and issue a session via redirect."""
    return handle_google_oauth_callback(code=code, state=state, request=request, db=db)


@router.get("/api/v1/auth/social/facebook/start", tags=["auth"])
def auth_social_facebook_start(    _rf_gate: None = Depends(require_feature("accounts.social.link"))):
    """Begin the Facebook OAuth flow — returns a 302 redirect to Facebook's consent screen."""
    return get_facebook_oauth_start()


@router.get("/api/v1/auth/social/facebook/callback", tags=["auth"])
def auth_social_facebook_callback(
    code: str = Query(..., description="Authorization code returned by Facebook"),
    state: Optional[str] = Query(None, description="OAuth state value to validate"),
    request: Request = None,
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.social.link")),
):
    """Handle the Facebook OAuth callback and issue a session via redirect."""
    return handle_facebook_oauth_callback(code=code, state=state, request=request, db=db)


@router.post("/api/v1/auth/social/google/id-token", tags=["auth"])
def auth_social_google_id_token(
    response: Response,
    payload: SocialLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.social.link")),
):
    """Google One Tap / GSI login — exchange a Google ID token for a ZOZI session.

    Public endpoint — the Google ID token is the credential.
    """
    from domains.accounts.services.auth.auth_service import handle_google_id_token_login
    return handle_google_id_token_login(payload=payload, response=response, db=db, request=request)


# === Sessions ===

@router.get("/api/v1/customer/accounts/sessions", tags=["customer", "accounts"])
def customer_list_sessions(
    page: int = Query(1, ge=1, description="1-based page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.session.manage")),
):
    """List the authenticated customer's active sessions (paginated)."""
    sessions = list_sessions(user_id=current_user.id, db=db)
    total = len(sessions)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = sessions[start:end]
    return {
        "items": [
            {
                "id": s.id,
                "user_id": s.user_id,
                "is_active": getattr(s, "is_active", True),
                "last_activity": getattr(s, "last_activity", None),
                "ip_address": getattr(s, "ip_address", None),
                "user_agent": getattr(s, "user_agent", None),
                "country_code": getattr(s, "country_code", None),
            }
            for s in page_items
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }


@router.delete("/api/v1/customer/accounts/sessions/{session_id}", tags=["customer", "accounts"])
def customer_revoke_session(
    session_id: int = Path(..., description="Session ID to revoke"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.session.revoke")),
):
    """Revoke a specific active session belonging to the authenticated customer."""
    revoked = revoke_session(user_id=current_user.id, session_id=session_id, db=db)
    if not revoked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {"detail": "Session revoked"}


# === GDPR ===

@router.post("/api/v1/customer/accounts/data-export", tags=["customer", "accounts"])
def customer_data_export(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.user.export")),
):
    """Export all personal data held about the authenticated customer (GDPR Art. 15)."""
    return export_user_data(user_id=current_user.id, db=db)


@router.post("/api/v1/customer/accounts/delete-request", tags=["customer", "accounts"])
def customer_delete_request(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.user.delete")),
):
    """Submit a personal-data deletion request (GDPR Art. 17)."""
    result = delete_user_data(user_id=current_user.id, db=db)
    return {"detail": "Deletion request processed", "result": result}
