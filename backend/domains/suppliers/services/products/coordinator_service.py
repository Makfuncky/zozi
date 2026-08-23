"""Supplier product coordinator service.

Wraps multi-domain-service calls for product creation endpoints.
This allows the module router to stay thin (single service call).
"""
from __future__ import annotations

from typing import Any, Optional
from sqlalchemy.orm import Session


def create_product_with_extras(
    db: Session,
    name: str,
    description: str,
    price: float,
    stock_quantity: int,
    category: str,
    **kwargs: Any,
) -> Any:
    """Create a product with content moderation and logistics setup.
    
    Wraps calls to:
    - domains.comms.services.admin.content_service.moderate_content
    - domains.logistics.services.shipments.shipping_tier.resolve_shipping_tier
    """
    from domains.comms.services.admin.content_service import moderate_content
    from domains.logistics.services.shipments.shipping_tier import resolve_shipping_tier
    from domains.suppliers.services.supplier_service import create_supplier_product
    
    # Moderate content
    moderate_content(description)
    
    # Resolve shipping tier
    shipping_tier = resolve_shipping_tier(weight=kwargs.get("weight"), country_code=kwargs.get("country_code"))
    
    # Create the product
    return create_supplier_product(
        db=db,
        name=name,
        description=description,
        price=price,
        stock_quantity=stock_quantity,
        category=category,
        shipping_tier=shipping_tier,
        **kwargs,
    )
