"""Social (OAuth/OIDC) sign-in endpoints for the admin auth surface.

Router is thin: identity verification + user resolution live in
``domains.accounts.services.social_service``.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from domains.accounts.services import social_service
from infrastructure.database.database import get_db
from modules.admin.auth.schemas import SocialLoginRequest

router = APIRouter(prefix="/social", tags=["auth", "social"])


@router.post("/login")
def social_login(payload: SocialLoginRequest, db: Session = Depends(get_db)):
    identity = social_service.verify_social_identity(
        payload.provider,
        id_token=payload.id_token,
        access_token=payload.access_token,
        provider_user_id=payload.provider_user_id,
        email=payload.email,
        full_name=payload.full_name,
    )
    return social_service.sign_in_social(
        payload.provider,
        identity["provider_user_id"],
        email=identity.get("email"),
        full_name=identity.get("full_name"),
        db=db,
    )
