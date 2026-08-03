"""Flash sales router."""
from fastapi import APIRouter, Depends, Query

from utils.dependencies import require_admin
from data.schemas import FlashSaleCreate
from data.services_commerce_flash_sales_service import (
    list_flash_sales,
    get_flash_sale,
    create_flash_sale,
)

router = APIRouter()


@router.get("")
def list_flash_sales_endpoint(
    active_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    return list_flash_sales(active_only, skip, limit)


@router.get("/{sale_id}")
def get_flash_sale_endpoint(sale_id: int):
    return get_flash_sale(sale_id)


@router.post("")
def create_flash_sale_endpoint(payload: FlashSaleCreate, _=Depends(require_admin)):
    return create_flash_sale(payload)
