"""Auto-migrated service logic from routers/auth.py."""
from __future__ import annotations

import domains.country.services as auth_svc

from domains.governance.services.auth.auth_service_accounts import LoginRequest
from domains.governance.services.auth.auth_service_accounts import RefreshRequest
from domains.governance.services.auth.auth_service_accounts import _find_user
from domains.governance.services.auth.auth_service_accounts import _record_login_history
from domains.governance.services.auth.auth_service_accounts import bearer_scheme
from domains.governance.services.auth.auth_service_accounts import csrf_token
from domains.governance.services.auth.auth_service_accounts import logger
from domains.governance.services.auth.auth_service_accounts import login
from domains.governance.services.auth.auth_service_accounts import logout
from domains.governance.services.auth.auth_service_accounts import me
from domains.governance.services.auth.auth_service_accounts import refresh
from domains.governance.services.auth.auth_service_accounts import register

import logging

import uuid

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status

from fastapi.encoders import jsonable_encoder

from fastapi.responses import JSONResponse

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from pydantic import BaseModel

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from infrastructure.database.schemas import RegisterRequest, TokenResponse, UserOut

from middleware.csrf_middleware import generate_csrf_token

from domains.governance.models.user import User
from domains.governance.models.user import UserLoginHistory

from infrastructure.utils.audit import AuditAction, audit_log

from infrastructure.utils.auth import (
    blacklist_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)

from infrastructure.utils.config import settings

from infrastructure.utils.dependencies import get_current_user

from infrastructure.utils.ip_utils import get_request_ip

def login(payload: LoginRequest, db: Session, request: Request):
    return auth_svc.login(payload=payload, db=db, request=request)

def register(payload: RegisterRequest, db: Session):
    return auth_svc.register(payload=payload, db=db)

def refresh(payload: RefreshRequest | None, request: Request, db: Session):
    return auth_svc.refresh(payload=payload, request=request, db=db)

def me(current_user: User):
    return auth_svc.me(current_user=current_user)

def csrf_token(request: Request):
    return auth_svc.csrf_token(request=request)

def logout(credentials: HTTPAuthorizationCredentials | None, current_user: User):
    return auth_svc.logout(credentials=credentials, current_user=current_user)


