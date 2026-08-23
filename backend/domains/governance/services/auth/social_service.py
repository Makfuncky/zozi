"""Social (OAuth/OIDC) sign-in logic for the accounts domain.

Find-or-create a local ``User`` from an external provider identity and issue the
standard auth response. Provider token *verification* is stubbed for now (no
provider SDK configured in dev); the real OIDC verification hook is marked
TODO and will populate the identity claims before this service runs.
"""
from __future__ import annotations

import secrets
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from domains.governance.models.social import SocialIdentity
from domains.governance.models.user import User
from domains.governance.services.auth_service import issue_auth_response
from infrastructure.security.auth import get_password_hash


def verify_social_identity(
    provider: str,
    id_token: Optional[str] = None,
    access_token: Optional[str] = None,
    provider_user_id: Optional[str] = None,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
) -> dict:
    """Return verified identity claims for a provider login.

    TODO(zozi): replace the dev path with real OIDC/id_token verification
    (google/apple) so the provider asserts ``provider_user_id``/``email``.
    Until then, callers may pass the claims directly (dev/test only).
    """
    if provider_user_id:
        return {
            "provider_user_id": provider_user_id,
            "email": email,
            "full_name": full_name,
        }
    # Real verification path requires provider SDKs / JWKS; not wired in dev.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Social token verification is not configured; pass provider_user_id in dev.",
    )


def find_or_create_user(
    provider: str,
    provider_user_id: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    db: Session | None = None,
) -> User:
    existing = (
        db.query(SocialIdentity)
        .filter(
            SocialIdentity.provider == provider,
            SocialIdentity.provider_user_id == provider_user_id,
        )
        .first()
    )
    if existing is not None:
        return db.query(User).filter(User.id == existing.user_id).first()

    user = None
    if email:
        user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(
            email=email,
            full_name=full_name,
            role="customer",
            hashed_password=get_password_hash(secrets.token_hex(16)),
            is_active=True,
            email_verified=bool(email),
        )
        db.add(user)
        db.flush()

    db.add(
        SocialIdentity(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
            full_name=full_name,
        )
    )
    db.commit()
    db.refresh(user)
    return user


def sign_in_social(
    provider: str,
    provider_user_id: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    db: Session | None = None,
):
    user = find_or_create_user(provider, provider_user_id, email=email, full_name=full_name, db=db)
    return issue_auth_response(user)
