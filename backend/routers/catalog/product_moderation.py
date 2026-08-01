"""
Product Moderation Router
Checks product_restrictions_json to auto-block prohibited items.
"""
import json
import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from db.database import get_db
from models import CountryConfig
from utils.dependencies import get_current_user

router = APIRouter(tags=["product-moderation"])

logger = logging.getLogger(__name__)


class ProductModerationService:
    """Moderates products based on country restrictions."""
    
    @staticmethod
    def get_restrictions(country_code: str, db) -> Dict[str, Any]:
        """Get product restrictions for a country."""
        config = db.query(CountryConfig).filter(
            CountryConfig.code == country_code.upper()
        ).first()
        
        if not config:
            return {"restricted_categories": [], "restricted_keywords": [], "age_restrictions": {}}
        
        try:
            restrictions = json.loads(config.product_restrictions_json) if isinstance(config.product_restrictions_json, str) else config.product_restrictions_json
        except (json.JSONDecodeError, TypeError):
            return {"restricted_categories": [], "restricted_keywords": [], "age_restrictions": {}}
        
        return restrictions
    
    @staticmethod
    def is_product_allowed(country_code: str, product_data: Dict[str, Any], db) -> Dict[str, Any]:
        """Check if a product is allowed in a country."""
        restrictions = ProductModerationService.get_restrictions(country_code, db)
        
        errors = []
        
        categories = product_data.get("categories", [])
        restricted_categories = restrictions.get("restricted_categories", [])
        for cat in categories:
            if cat in restricted_categories:
                errors.append(f"Category '{cat}' is restricted in {country_code}")
        
        title = product_data.get("title", "").lower()
        description = product_data.get("description", "").lower()
        restricted_keywords = restrictions.get("restricted_keywords", [])
        for keyword in restricted_keywords:
            if keyword.lower() in title or keyword.lower() in description:
                errors.append(f"Keyword '{keyword}' is restricted")
        
        return {
            "allowed": len(errors) == 0,
            "errors": errors,
            "restrictions": restrictions
        }


@router.get("/{country_code}/product-restrictions")
def get_product_restrictions(
    country_code: str = Path(..., description="Country code"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get product restrictions for a country."""
    return ProductModerationService.get_restrictions(country_code, db)


@router.post("/{country_code}/products/{product_id}/moderate")
def moderate_product(
    country_code: str = Path(..., description="Country code"),
    product_id: int = Path(..., description="Product ID"),
    product_data: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Check if a product is allowed in a country."""
    if product_data is None:
        product_data = {}
    
    result = ProductModerationService.is_product_allowed(country_code, product_data, db)
    result["product_id"] = product_id
    return result
