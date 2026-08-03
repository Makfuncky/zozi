"""
Customer Health API Endpoints
"""
from fastapi import APIRouter, Depends

from data.dependencies_auth import get_current_user
from data.services_customer_health_service import get_customer_health, list_customer_health

router = APIRouter()


@router.get("/health/customers/{user_id}")
def get_customer_health_endpoint(
    user_id: int,
    current_user: dict = Depends(get_current_user),
):
    return get_customer_health(user_id)


@router.get("/health/customers")
def list_customer_health_endpoint(
    current_user: dict = Depends(get_current_user),
    page: int = 1,
    size: int = 100,
):
    return list_customer_health(page=page, size=size)
