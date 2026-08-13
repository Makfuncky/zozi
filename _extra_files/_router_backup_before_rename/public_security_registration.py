"""Authentication router: login, refresh, logout, current user, register.

This router is a thin HTTP layer. All business logic (user lookup, password
verification, token issuance, login-history recording, user creation) is
delegated to ``controllers.auth_controller`` so the circuit stays clean:
routers -> controllers/schemas/auth-deps only (no direct db/query/model use).
"""
from __future__ import annotations
import logging
import uuid
from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from db.session import get_db
from db.schemas import RegisterRequest, TokenResponse, UserOut
from controllers.auth_controller import _find_user_for_login, _record_login_history, create_access_token, create_refresh_token, decode_token, register_user, _resolve_user_from_subject, UserCreate, verify_password
from utils.audit import audit_log, AuditAction
from utils.config import settings
from utils.dependencies import get_current_user
from utils.ip_utils import get_request_ip
from utils.csrf_utils import generate_csrf_token
import services.db_write as db_write
logger = logging.getLogger(__name__)
router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)

class LoginRequest(BaseModel):
    email: str | None = None
    username: str | None = None
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

def _issue_tokens(user) -> dict:
    """Build the token payload via controller primitives (no direct model use)."""
    family_id = uuid.uuid4().hex
    access = create_access_token({'sub': str(user.id), 'role': user.role})
    refresh = create_refresh_token({'sub': str(user.id), 'role': user.role}, family_id=family_id)
    return {'access_token': access, 'refresh_token': refresh, 'token_type': 'bearer', 'user': UserOut.model_validate(user)}

def _set_auth_cookies(resp: JSONResponse, access_token: str, refresh_token: str) -> None:
    is_prod = str(settings.app_env).lower() == 'production'
    samesite = 'none' if is_prod else 'lax'
    resp.set_cookie(key='access_token', value=access_token, httponly=True, samesite=samesite, secure=is_prod, max_age=settings.access_token_expire_minutes * 60, path='/')
    resp.set_cookie(key='refresh_token', value=refresh_token, httponly=True, samesite=samesite, secure=is_prod, max_age=settings.refresh_token_expire_days * 86400, path='/auth/refresh')

@router.post('/login', response_model=TokenResponse)
def login(payload: LoginRequest, db=Depends(get_db), request: Request=None):
    ip = get_request_ip(request) if request else None
    ua = (request.headers.get('user-agent') or '')[:500] if request else None
    user = _find_user_for_login(payload.email or payload.username or '', db)
    if not user or not verify_password(payload.password, user.hashed_password):
        if user:
            audit_log(db=db, action=AuditAction.LOGIN_FAILED, user_id=user.id, username=user.username, user_role=user.role, ip_address=ip, user_agent=ua, status='failure', details={'reason': 'invalid_credentials'})
            _record_login_history(db, user, request=request, success=False)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
    if not user.is_active:
        audit_log(db=db, action=AuditAction.LOGIN_FAILED, user_id=user.id, username=user.username, user_role=user.role, ip_address=ip, user_agent=ua, status='failure', details={'reason': 'account_inactive'})
        _record_login_history(db, user, request=request, success=False)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Account is inactive')
    user.last_login = timezone.utc.now() if hasattr(timezone, 'utc') else timezone.now()
    db_write.add(db, user)
    db_write.commit(db)
    _record_login_history(db, user, request=request, success=True)
    tokens = _issue_tokens(user)
    resp = JSONResponse(jsonable_encoder(TokenResponse(**tokens)))
    _set_auth_cookies(resp, tokens['access_token'], tokens['refresh_token'])
    return resp

@router.post('/register', response_model=TokenResponse)
def register(payload: RegisterRequest, db=Depends(get_db)):
    user_create = UserCreate(email=payload.email, username=payload.username, password=payload.password, full_name=getattr(payload, 'full_name', None), phone=getattr(payload, 'phone', None), role=payload.role)
    try:
        created = register_user(user_create, db)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception('Registration failed for %s', getattr(payload, 'email', 'unknown'))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Registration could not be completed. If this persists, contact support.') from exc
    tokens = _issue_tokens(created)
    resp = JSONResponse(jsonable_encoder(TokenResponse(**tokens)))
    _set_auth_cookies(resp, tokens['access_token'], tokens['refresh_token'])
    return resp

@router.post('/refresh', response_model=TokenResponse)
def refresh(payload: RefreshRequest | None=None, request: Request=None, db=Depends(get_db)):
    token = payload.refresh_token if payload else None
    if not token and request:
        token = request.cookies.get('refresh_token')
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='No refresh token provided')
    try:
        decoded = decode_token(token)
    except HTTPException as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token') from exc
    if decoded.get('type') != 'refresh':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token type')
    user = _resolve_user_from_subject(str(decoded.get('sub')), db)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')
    family_id = decoded.get('family_id') or uuid.uuid4().hex
    tokens = _issue_tokens(user)
    resp = JSONResponse(jsonable_encoder(TokenResponse(**tokens)))
    _set_auth_cookies(resp, tokens['access_token'], tokens['refresh_token'])
    return resp

@router.get('/me', response_model=UserOut)
def me(current_user: dict=Depends(get_current_user)):
    return current_user

@router.get('/csrf')
def csrf_token(request: Request):
    token = generate_csrf_token()
    is_production = str(settings.app_env).lower() == 'production'
    resp = JSONResponse({'csrf_token': token})
    resp.set_cookie(key='csrf_token', value=token, httponly=False, secure=is_production, samesite='strict', max_age=3600, path='/')
    return resp

@router.post('/logout')
def logout(credentials: HTTPAuthorizationCredentials | None=Depends(bearer_scheme), current_user: dict=Depends(get_current_user)):
    if credentials:
        try:
            from utils.auth import blacklist_token
            import time
            payload = decode_token(credentials.credentials)
            jti = payload.get('jti')
            exp = payload.get('exp')
            if jti and exp:
                ttl = int(exp) - int(time.time())
                if ttl > 0:
                    blacklist_token(jti, ttl)
        except Exception:
            pass
    resp = JSONResponse({'message': 'Logged out'})
    resp.delete_cookie(key='refresh_token', path='/auth/refresh')
    return resp
