"""Users router — profile CRUD, admin user management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from models import User
from db.schemas import UserOut, UserUpdate, UserAdminUpdate, MessageResponse
from utils.dependencies import get_current_user, require_admin

router = APIRouter()

@router.get("/me", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserOut)
def update_profile(payload: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, k, v)
    db.commit(); db.refresh(current_user)
    return current_user

@router.get("", response_model=list[UserOut])
def list_users(skip: int = 0, limit: int = 50, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(User).offset(skip).limit(limit).all()

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u: raise HTTPException(404, "User not found")
    return u

@router.put("/{user_id}", response_model=UserOut)
def admin_update_user(user_id: int, payload: UserAdminUpdate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u: raise HTTPException(404, "User not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(u, k, v)
    db.commit(); db.refresh(u)
    return u

