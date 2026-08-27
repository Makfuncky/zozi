"""Legacy cart service — kept for backward compatibility."""
from __future__ import annotations
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional


class CartShippingQuoteRequest(BaseModel):
    """Request model for cart shipping quote."""
    customer_id: int
    address_id: int
    items: list


def get_cart_legacy(customer_id: int, db: Session) -> dict:
    """Legacy cart retrieval — returns empty cart."""
    return {"customer_id": customer_id, "items": [], "total": 0.0}


def get_cart_shipping_quote(customer_id: int, address_id: int, db: Session) -> dict:
    """Get shipping quote for cart."""
    return {"customer_id": customer_id, "address_id": address_id, "quotes": []}
