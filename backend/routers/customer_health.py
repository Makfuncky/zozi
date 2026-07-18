"""
Customer Health API Endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from controllers.auth_controller import get_current_user
from services.customer_health_engine import get_customer_health_engine

router = APIRouter()


@router.get("/health/customers/{user_id}")
def get_customer_health(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    engine = get_customer_health_engine(db)
    return engine.calculate_health_score(user_id)


@router.get("/health/customers")
def list_customer_health(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from models import User
    from models import UserRole
    users = db.query(User).all()
    results = []
    for u in users:
        engine = get_customer_health_engine(db)
        health = engine.calculate_health_score(u.id)
        health["profile"] = {
            "email": u.email,
            "role": u.role,
        }
        results.append(health)
    results.sort(key=lambda x: x.get("trust_score", 0), reverse=True)
    return {"customers": results[:100]}
