"""Authentication router: login, refresh, logout, current user, register."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import User
from db.schemas import RegisterRequest, TokenResponse, UserOut
from utils.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from utils.config import settings
from utils.dependencies import get_current_user

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
    return q.first()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = _find_user(db, payload.email, payload.username)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    family_id = uuid.uuid4().hex
    access = create_access_token({"sub": str(user.id), "role": user.role})
    refresh = create_refresh_token({"sub": str(user.id), "role": user.role}, family_id=family_id)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        user=UserOut.model_validate(user),
    )


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    if payload.username and db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
    from db.schemas import _validate_password_complexity

    _validate_password_complexity(payload.password)
    user = User(
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name,
        phone=payload.phone,
        role=payload.role,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    family_id = uuid.uuid4().hex
    access = create_access_token({"sub": str(user.id), "role": user.role})
    refresh = create_refresh_token({"sub": str(user.id), "role": user.role}, family_id=family_id)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        user=UserOut.model_validate(user),
    )


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token)
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
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
):
    return {"message": "Logged out"}
