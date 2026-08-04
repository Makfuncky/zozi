"""Service methods for user read operations."""
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc
from data.models import User


def get_all_users(db: Session, skip: int = 0, limit: int = 20) -> list[User]:
    """Get all users with pagination."""
    return db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()


def get_user_by_username(db: Session, username: str) -> User | None:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_stats(db: Session) -> dict:
    """Get user statistics."""
    total = db.query(sqlfunc.count(User.id)).scalar() or 0
    active = db.query(sqlfunc.count(User.id)).filter(User.is_active == True).scalar() or 0
    inactive = db.query(sqlfunc.count(User.id)).filter(User.is_active == False).scalar() or 0
    return {"total": total, "active": active, "inactive": inactive}
