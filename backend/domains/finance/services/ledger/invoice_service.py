"""Finance domain — invoice service (stub for development)."""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session


def create_invoice_from_order(db: Session, order_id: int, **kwargs: Any) -> dict:
    """Create an invoice from an order. Stub for development."""
    return {"order_id": order_id, "status": "pending"}
