"""Authentication router: login, refresh, logout, current user, register."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from data.db import get_db
from data.models import User, UserLoginHistory
from data.schemas import RegisterRequest, TokenResponse, UserOut
from utils.auth import (
    blacklist_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from utils.audit_log import audit_log, AuditAction
from utils.config import settings
from utils.dependencies import get_current_user
from utils.ip_utils import get_request_ip
from data.middleware_csrf_middleware import generate_csrf_token

from services.write_helpers import add_and_flush, commit_and_refresh, commit_only, rollback_only
router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    email: str | None = None
    username: str | None = None
    password: str


def _find_user(db: Session, email: str | None, username: str | None) -> User | None:
    q = db.query(User)
    if email:
        q = q.filter(User.email == email)
    elif username:
        q = q.filter(User.username == username)
    else:
        return None
    user = q.first()
    if user:
        return user
    if username and "@" in username and not email:
        return db.query(User).filter(User.email == username).first()
    return None


def _record_login_history(db: Session, user: User, request: Request | None = None, success: bool = True) -> None:
    """Write a UserLoginHistory record for a login attempt."""
    try:
        ip = get_request_ip(request) if request else None
        ua = (request.headers.get("user-agent") or "")[:500] if request else None
        history = UserLoginHistory(
            user_id=user.id,
            ip_address=ip or "unknown",
            user_agent=ua,
            timestamp=datetime.now(timezone.utc),
            success=success,
            country_code=user.country_code,
        )
        add_and_flush(db, history)
        commit_only(db)
    except Exception as exc:
        logger.warning("Failed to record login history for %s: %s", user.username, exc)
        try:
            rollback_only(db)
        except Exception:
            pass


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db), request: Request = None):
    ip = get_request_ip(request) if request else None
    ua = (request.headers.get("user-agent") or "")[:500] if request else None

    user = _find_user(db, payload.email, payload.username)
    if not user or not verify_password(payload.password, user.hashed_password):
        if user:
            audit_log(
                db=db,
                action=AuditAction.LOGIN_FAILED,
                user_id=user.id,
                username=user.username,
                user_role=user.role,
                ip_address=ip,
                user_agent=ua,
                status="failure",
                details={"reason": "invalid_credentials"},
            )
            _record_login_history(db, user, request=request, success=False)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        audit_log(
            db=db,
            action=AuditAction.LOGIN_FAILED,
            user_id=user.id,
            username=user.username,
            user_role=user.role,
            ip_address=ip,
            user_agent=ua,
            status="failure",
            details={"reason": "account_inactive"},
        )
        _record_login_history(db, user, request=request, success=False)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    user.last_login = datetime.now(timezone.utc)
    commit_only(db)

    # Record login history
    _record_login_history(db, user, request=request, success=True)

    family_id = uuid.uuid4().hex
    access = create_access_token({"sub": str(user.id), "role": user.role})
    refresh = create_refresh_token({"sub": str(user.id), "role": user.role}, family_id=family_id)
    resp = JSONResponse(
        jsonable_encoder(
            TokenResponse(
                access_token=access,
                refresh_token=refresh,
                token_type="bearer",
                user=UserOut.model_validate(user),
            )
        ),
    )
    resp.set_cookie(
        key="access_token",
        value=access,
        httponly=True,
        samesite="lax" if str(settings.app_env).lower() != "production" else "none",
        secure=str(settings.app_env).lower() == "production",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    resp.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        samesite="lax" if str(settings.app_env).lower() != "production" else "none",
        secure=str(settings.app_env).lower() == "production",
        max_age=settings.refresh_token_expire_days * 86400,
        path="/auth/refresh",
    )
    return resp


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        if db.query(User).filter(User.email == payload.email).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        if payload.username and db.query(User).filter(User.username == payload.username).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

        # Validate role is one of the allowed values
        valid_roles = {"customer", "supplier", "admin", "employee", "logistics_partner"}
        if payload.role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid role '{payload.role}'. Allowed roles: {', '.join(sorted(valid_roles))}",
            )

        from data.schemas import _validate_password_complexity
        try:
            _validate_password_complexity(payload.password)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )

        if len(payload.password) > 72:
            import logging as _logging
            _logging.getLogger(__name__).warning(
                "Password truncated to 72 characters due to bcrypt limit for user %s",
                payload.email,
            )

        user = User(
            email=payload.email,
            username=payload.username,
            full_name=payload.full_name or payload.username,
            phone=payload.phone,
            role=payload.role,
            hashed_password=get_password_hash(payload.password),
        )
        add_and_flush(db, user)
        commit_and_refresh(db, user)
        family_id = uuid.uuid4().hex
        access = create_access_token({"sub": str(user.id), "role": user.role})
        refresh = create_refresh_token({"sub": str(user.id), "role": user.role}, family_id=family_id)
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            token_type="bearer",
            user=UserOut.model_validate(user),
        )
    except HTTPException:
        raise
    except Exception as exc:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Registration failed for %s", getattr(payload, "email", "unknown"))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration could not be completed. If this persists, contact support. (Reference: {getattr(payload, 'email', 'unknown')})",
        )


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest | None = None, request: Request = None, db: Session = Depends(get_db)):
    token = payload.refresh_token if payload else None
    if not token and request:
        token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token provided")
    try:
        decoded = decode_token(token)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    user = db.query(User).filter(User.id == int(decoded.get("sub"))).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    family_id = decoded.get("family_id") or uuid.uuid4().hex
    access = create_access_token({"sub": str(user.id), "role": user.role})
    refresh = create_refresh_token({"sub": str(user.id), "role": user.role}, family_id=family_id)
    resp = JSONResponse(
        jsonable_encoder(
            TokenResponse(
                access_token=access,
                refresh_token=refresh,
                token_type="bearer",
                user=UserOut.model_validate(user),
            )
        ),
    )
    resp.set_cookie(
        key="access_token",
        value=access,
        httponly=True,
        samesite="lax" if str(settings.app_env).lower() != "production" else "none",
        secure=str(settings.app_env).lower() == "production",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    resp.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        samesite="lax" if str(settings.app_env).lower() != "production" else "none",
        secure=str(settings.app_env).lower() == "production",
        max_age=settings.refresh_token_expire_days * 86400,
        path="/auth/refresh",
    )
    return resp


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/csrf")
def csrf_token(request: Request):
    token = generate_csrf_token()
    is_production = str(settings.app_env).lower() == "production"
    resp = JSONResponse({"csrf_token": token})
    resp.set_cookie(
        key="csrf_token",
        value=token,
        httponly=False,
        secure=is_production,
        samesite="strict",
        max_age=3600,
        path="/",
    )
    return resp


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
):
    if credentials:
        try:
            payload = decode_token(credentials.credentials)
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                import time
                ttl = int(exp) - int(time.time())
                if ttl > 0:
                    blacklist_token(jti, ttl)
        except Exception:
            pass
    resp = JSONResponse({"message": "Logged out"})
    resp.delete_cookie(key="refresh_token", path="/auth/refresh")
    return resp

