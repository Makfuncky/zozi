"""
Product Moderation Router
Checks product_restrictions_json to auto-block prohibited items.
"""
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, Path

from utils.dependencies import get_current_user
from data.services_catalog_product_moderation_service import (
    get_restrictions,
    is_product_allowed,
)

router = APIRouter(tags=["product-moderation"])
logger = logging.getLogger(__name__)


@router.get("/{country_code}/product-restrictions")
def get_product_restrictions(
    country_code: str = Path(..., description="Country code"),
    current_user=Depends(get_current_user),
):
    """Get product restrictions for a country."""
    return get_restrictions(country_code)


@router.post("/{country_code}/products/{product_id}/moderate")
def moderate_product(
    country_code: str = Path(..., description="Country code"),
    product_id: int = Path(..., description="Product ID"),
    product_data: Optional[Dict[str, Any]] = None,
    current_user=Depends(get_current_user),
):
    """Check if a product is allowed in a country."""
    if product_data is None:
        product_data = {}

    result = is_product_allowed(country_code, product_data)
    result["product_id"] = product_id
    return result
