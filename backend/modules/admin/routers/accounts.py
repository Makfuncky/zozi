"""Admin accounts router — canonical."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Body, Request, status
from sqlalchemy.orm import Session
from typing import Optional

from domains.accounts.services.users.user_management_service import (
    list_pending_bank_accounts,
    verify_bank_account,
    delete_bank_account_record,
    list_staff_accounts,
    create_staff_account,
    update_staff_account,
    delete_staff_account,
    update_user_role,
    toggle_user_active,
    force_reset_password_admin,
    bulk_update_users_role,
    bulk_toggle_users_active,
    bulk_update_staff_accounts,
    bulk_delete_users_admin,
)
from domains.accounts.services.identity.identity_admin_service import (
    list_users_by_country,
    get_user_in_country,
    update_user_in_country,
    list_all_users,
    get_user_by_id_or_404,
    update_user_by_id,
    archive_user,
    restore_user,
    bulk_archive_users,
    bulk_toggle_active,
    bulk_restore_users,
    hard_delete_user,
    set_user_role,
    set_user_active,
    force_reset_password,
    delete_user_admin,
)
from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_admin
from domains.accounts.services.auth.auth_service import (
    SocialLoginRequest,
    sign_in_social,
    verify_social_identity,
)
from infrastructure.database.schemas import (
    CreateStaffAccount,
    UpdateStaffAccount,
    BulkUpdateStaffBody,
)
from rbac.dependencies import require_feature
from infrastructure.security.rate_limiter import limiter, RL_SENSITIVE

router = APIRouter(tags=["admin", "accounts"])


@router.get("/api/v1/admin/accounts/bank-accounts/{country_code}/pending", status_code=200, tags=["admin-bank-accounts"])
def list_pending_bank_accounts_route(
    country_code: str,
    kind: str = Query("supplier"),
    page: int = Query(1),
    page_size: int = Query(50),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List bank accounts awaiting verification."""
    require_feature("accounts.permissions.manage")
    return list_pending_bank_accounts(
        kind=kind,
        db=db,
        current_user=current_user,
        limit=page_size,
        offset=(page - 1) * page_size,
    )


@router.post("/api/v1/admin/accounts/bank-accounts/{country_code}/{kind}/{account_id}/verify", status_code=201, tags=["admin-bank-accounts"])
def verify_bank_account_route(
    country_code: str,
    kind: str,
    account_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    action: str = Body("approve", embed=True),
    note: Optional[str] = Body(None, embed=True),
):
    """Approve or reject a bank account."""
    require_feature("accounts.permissions.manage")
    return verify_bank_account(
        kind=kind,
        account_id=account_id,
        action=action,
        note=note,
        current_user=current_user,
        db=db,
    )


@router.delete("/api/v1/admin/accounts/bank-accounts/{country_code}/{kind}/{account_id}", status_code=200, tags=["admin-bank-accounts"])
def delete_bank_account_route(
    country_code: str,
    kind: str,
    account_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a bank account record."""
    require_feature("accounts.permissions.manage")
    return delete_bank_account_record(
        kind=kind,
        account_id=account_id,
        current_user=current_user,
        db=db,
    )


# ── User lifecycle (identity_admin_service) ──


@router.get("/api/v1/admin/accounts/users/{country_code}", status_code=200)
def list_users_by_country_route(
    country_code: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    include_deleted: bool = Query(False),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List users in a specific country."""
    require_feature("accounts.user.list")
    return list_users_by_country(
        db=db,
        country_code=country_code,
        page=page,
        size=page_size,
        role=role,
        search=search,
        include_deleted=include_deleted,
    )


@router.get("/api/v1/admin/accounts/users/{country_code}/{user_id}", status_code=200)
def get_user_in_country_route(
    country_code: str,
    user_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get a single user within a specific country."""
    require_feature("accounts.user.read")
    return get_user_in_country(db, country_code, user_id)


@router.get("/api/v1/admin/accounts/users", status_code=200)
def list_all_users_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List users across all countries (admin console, no RLS scoping)."""
    require_feature("accounts.user.list")
    return list_all_users(
        db=db,
        skip=(page - 1) * page_size,
        limit=page_size,
    )


@router.get("/api/v1/admin/accounts/users/{user_id}", status_code=200)
def get_user_by_id_route(
    user_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Fetch a user by primary key."""
    require_feature("accounts.user.read")
    return get_user_by_id_or_404(db, user_id)


@router.patch("/api/v1/admin/accounts/users/{user_id}", status_code=200)
def update_user_by_id_route(
    user_id: int,
    payload: dict = Body(...),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update a user's profile fields (no country scoping)."""
    require_feature("accounts.user.update")
    return update_user_by_id(db, user_id, payload)


@router.post("/api/v1/admin/accounts/users/{country_code}/{user_id}/archive", status_code=200)
def archive_user_route(
    country_code: str,
    user_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    reason: Optional[str] = Body(None, embed=True),
):
    """Soft-archive (soft-delete) a user within a country."""
    require_feature("accounts.user.delete")
    return archive_user(db, country_code, user_id, reason=reason)


@router.post("/api/v1/admin/accounts/users/{country_code}/{user_id}/restore", status_code=200)
def restore_user_route(
    country_code: str,
    user_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Restore a previously archived user."""
    require_feature("accounts.user.delete")
    return restore_user(db, country_code, user_id)


@router.post("/api/v1/admin/accounts/users/bulk/archive", status_code=200)
def bulk_archive_users_route(
    country_code: str = Query(...),
    ids: list[int] = Body(..., embed=True),
    reason: Optional[str] = Body(None, embed=True),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Bulk soft-archive users in a country."""
    require_feature("accounts.user.delete")

    class _Payload:
        pass

    payload = _Payload()
    payload.ids = ids
    return bulk_archive_users(db, country_code, payload, reason=reason)


@router.post("/api/v1/admin/accounts/users/bulk/toggle-active", status_code=200)
def bulk_toggle_active_route(
    country_code: str = Query(...),
    user_ids: list[int] = Body(..., embed=True),
    is_active: bool = Body(True, embed=True),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Bulk enable or disable users in a country."""
    require_feature("accounts.user.update")
    return bulk_toggle_active(db, country_code, user_ids, is_active=is_active)


@router.post("/api/v1/admin/accounts/users/bulk/restore", status_code=200)
def bulk_restore_users_route(
    country_code: str = Query(...),
    ids: list[int] = Body(..., embed=True),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Bulk restore archived users in a country."""
    require_feature("accounts.user.delete")

    class _Payload:
        pass

    payload = _Payload()
    payload.ids = ids
    return bulk_restore_users(db, country_code, payload)


@router.delete("/api/v1/admin/accounts/users/{country_code}/{user_id}", status_code=200)
def hard_delete_user_route(
    country_code: str,
    user_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    delete_orders: bool = Query(False),
):
    """Hard-delete a user within a country."""
    require_feature("accounts.user.delete")
    return hard_delete_user(db, country_code, user_id, current_user, delete_orders=delete_orders)


@router.patch("/api/v1/admin/accounts/users/{country_code}/{user_id}/role", status_code=200)
def set_user_role_route(
    country_code: str,
    user_id: int,
    role: str = Body(..., embed=True),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Set a user's role (country-scoped)."""
    require_feature("accounts.role.assign")
    return set_user_role(db, country_code, user_id, role, current_user)


@router.post("/api/v1/admin/accounts/users/{country_code}/{user_id}/toggle-active", status_code=200)
def set_user_active_route(
    country_code: str,
    user_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Toggle a user's active status (country-scoped)."""
    require_feature("accounts.user.update")
    return set_user_active(db, country_code, user_id, current_user)


@router.post("/api/v1/admin/accounts/users/{country_code}/{user_id}/reset-password", status_code=200)
def force_reset_password_route(
    country_code: str,
    user_id: int,
    new_password: str = Body(..., embed=True),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Force-reset a user's password (country-scoped)."""
    require_feature("accounts.password.reset")
    return force_reset_password(db, country_code, user_id, new_password, current_user)


@router.delete("/api/v1/admin/accounts/users/{country_code}/{user_id}/hard", status_code=200)
def delete_user_admin_route(
    country_code: str,
    user_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    delete_orders: bool = Body(False, embed=True),
):
    """Hard-delete a user within a country (admin variant)."""
    require_feature("accounts.user.delete")
    return delete_user_admin(db, country_code, user_id, current_user, delete_orders=delete_orders)


# ── Staff accounts & user_management_service ──


@router.get("/api/v1/admin/accounts/staff", status_code=200)
def list_staff_accounts_route(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all staff accounts."""
    require_feature("accounts.user.list")
    return list_staff_accounts(db)


@router.patch("/api/v1/admin/accounts/users/{user_id}/role", status_code=200)
def update_user_role_route(
    user_id: int,
    role: str = Body(..., embed=True),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update a user's role (admin console)."""
    require_feature("accounts.role.assign")
    return update_user_role(user_id, role, current_user, db)


@router.post("/api/v1/admin/accounts/users/{user_id}/toggle-active", status_code=200)
def toggle_user_active_route(
    user_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Toggle a user's active flag."""
    require_feature("accounts.user.update")
    return toggle_user_active(user_id, current_user, db)


@router.post("/api/v1/admin/accounts/users/{user_id}/reset-password", status_code=200)
def force_reset_password_admin_route(
    user_id: int,
    password_hash: str = Body(..., embed=True),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Force-reset a user's password using a pre-hashed password (admin)."""
    require_feature("accounts.password.reset")
    return force_reset_password_admin(user_id, password_hash, current_user, db)


@router.post("/api/v1/admin/accounts/staff", status_code=201)
def create_staff_account_route(
    payload: CreateStaffAccount,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new staff account."""
    require_feature("accounts.user.create")
    return create_staff_account(payload, current_user, db)


@router.put("/api/v1/admin/accounts/staff/{user_id}", status_code=200)
def update_staff_account_route(
    user_id: int,
    payload: UpdateStaffAccount,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update an existing staff account."""
    require_feature("accounts.user.update")
    return update_staff_account(user_id, payload, current_user, db)


@router.delete("/api/v1/admin/accounts/staff/{user_id}", status_code=200)
def delete_staff_account_route(
    user_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a staff account."""
    require_feature("accounts.user.delete")
    return delete_staff_account(user_id, current_user, db)


@router.post("/api/v1/admin/accounts/users/bulk/role", status_code=200)
def bulk_update_users_role_route(
    user_ids: list[int] = Body(..., embed=True),
    role: str = Body(..., embed=True),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Bulk assign the same role to multiple users."""
    require_feature("accounts.role.assign")
    return bulk_update_users_role(user_ids, role, current_user, db)


@router.post("/api/v1/admin/accounts/users/bulk/toggle-active-global", status_code=200)
def bulk_toggle_users_active_route(
    user_ids: list[int] = Body(..., embed=True),
    is_active: bool = Body(..., embed=True),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Bulk enable or disable users (cross-country)."""
    require_feature("accounts.user.update")
    return bulk_toggle_users_active(user_ids, is_active, current_user, db)


@router.post("/api/v1/admin/accounts/staff/bulk", status_code=200)
def bulk_update_staff_accounts_route(
    body: BulkUpdateStaffBody,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Bulk update multiple staff accounts."""
    require_feature("accounts.user.update")
    return bulk_update_staff_accounts(body.user_ids, body.updates, current_user, db)


@router.post("/api/v1/admin/accounts/users/bulk/delete", status_code=200)
def bulk_delete_users_admin_route(
    user_ids: list[int] = Body(..., embed=True),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Bulk hard-delete multiple users (admin-only)."""
    require_feature("accounts.user.delete")
    return bulk_delete_users_admin(user_ids, current_user, db)


# ── Social (OAuth/OIDC) sign-in endpoints (moved from modules/admin/routers/auth_social.py) ──


@router.post(
    "/social/login",
    tags=["auth", "social"],
    status_code=status.HTTP_200_OK,
    summary="Sign in with a social identity provider (Google / Apple / etc.)",
    description=(
        "Public, unauthenticated endpoint that exchanges a verified social identity "
        "(ID token, access token, or provider-issued user id) for a ZOZI session. "
        "Rate-limited per client IP to deter credential-stuffing and token replay; "
        "the `accounts.session.manage` feature gate is enforced via the dependency "
        "to keep RBAC checks uniform with the rest of the accounts surface."
    ),
    responses={
        200: {"description": "Signed in; returns session token + user payload."},
        400: {"description": "Invalid social identity payload."},
        401: {"description": "Social identity could not be verified."},
        429: {"description": "Too many social login attempts; slow down."},
    },
)
@limiter.limit(RL_SENSITIVE)
def social_login(
    request: Request,
    payload: SocialLoginRequest,
    db: Session = Depends(get_db),
    _feature: None = Depends(require_feature("accounts.session.manage")),
):
    require_feature("accounts.session.manage")
    identity = verify_social_identity(
        payload.provider,
        id_token=payload.id_token,
        access_token=payload.access_token,
        provider_user_id=payload.provider_user_id,
        email=payload.email,
        full_name=payload.full_name,
    )
    return sign_in_social(
        payload.provider,
        identity["provider_user_id"],
        email=identity.get("email"),
        full_name=identity.get("full_name"),
        db=db,
    )
