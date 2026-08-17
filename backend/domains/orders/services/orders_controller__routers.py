"""Customer-facing orders controller.

Delegates to ``services.orders.orders_service`` which holds the real order
creation, preview, lookup, tracking, invoice, cancellation and
shipment-confirmation logic. The controller is the stable boundary the router
imports; the service owns the business rules.

Routes are declared with the metadata-only decorators from ``core.route_contract``
so ``routers/generated/auto_router.py`` can auto-generate the FastAPI surface.
A controller never imports FastAPI directly.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from core.route_contract import get, post
from infrastructure.database.schemas import OrderCreate, OrderPreviewOut

from domains.orders.services.orders_service import (
    cancel_order as _cancel_order,
)
from domains.orders.services.orders_service import (
    confirm_order_scan_receipt as _confirm_order_scan_receipt,
)
from domains.orders.services.orders_service import (
    create_order as _create_order,
)
from domains.orders.services.orders_service import (
    get_order as _get_order,
)
from domains.orders.services.orders_service import (
    get_order_invoice as _get_order_invoice,
)
from domains.orders.services.orders_service import (
    get_order_tracking as _get_order_tracking,
)
from domains.orders.services.orders_service import (
    get_orders as _get_orders,
)
from domains.orders.services.orders_service import (
    preview_order as _preview_order,
)
from domains.orders.services.orders_service import (
    respond_to_shipment_confirmation as _respond_to_shipment_confirmation,
)

@post("/api/v1/customer/orders", deps=["user", "db"], body=OrderCreate, tags=["orders"])
def create_order(order: OrderCreate, current_user: dict, db: Session):
    """Create an order from the customer checkout payload."""
    return _create_order(order, current_user, db)

@post(
    "/api/v1/customer/orders/preview",
    deps=["user", "db"],
    body=OrderCreate,
    response_model=OrderPreviewOut,
    tags=["orders"],
)
def preview_order(order: OrderCreate, current_user: dict, db: Session):
    """Compute order totals/taxes/fees without persisting."""
    return _preview_order(order, current_user, db)

@get("/api/v1/customer/orders", deps=["user", "db"], query=["skip", "limit"], tags=["orders"])
def get_orders(current_user: dict, db: Session, *, skip: int = 0, limit: int = 50):
    """List the current customer's orders."""
    return _get_orders(current_user, db, skip=skip, limit=limit)

@get("/api/v1/customer/orders/{order_id}", deps=["user", "db"], tags=["orders"])
def get_order(order_id: int, current_user: dict, db: Session):
    """Fetch a single order owned by the current customer."""
    return _get_order(order_id, current_user, db)

@get("/api/v1/customer/orders/{order_id}/invoice", deps=["user", "db"], tags=["orders"])
def get_order_invoice(order_id: int, current_user: dict, db: Session):
    """Build the invoice payload for an order."""
    return _get_order_invoice(order_id, current_user, db)

@get("/api/v1/customer/orders/{order_id}/tracking", deps=["user", "db"], tags=["orders"])
def get_order_tracking(order_id: int, current_user: dict, db: Session):
    """Return shipment tracking details for an order."""
    return _get_order_tracking(order_id, current_user, db)

@post(
    "/api/v1/customer/orders/{order_id}/scan-receipt",
    deps=["user", "db"],
    body=dict,
    tags=["orders"],
)
def confirm_order_scan_receipt(order_id: int, data: dict, current_user: dict, db: Session):
    """Record a scanned receipt confirmation for an order."""
    return _confirm_order_scan_receipt(order_id, data, current_user, db)

@post("/api/v1/customer/orders/{order_id}/cancel", deps=["user", "db"], tags=["orders"])
def cancel_order(order_id: int, current_user: dict, db: Session):
    """Cancel an order owned by the current customer."""
    return _cancel_order(order_id, current_user, db)

@post(
    "/api/v1/customer/orders/{order_id}/confirmation-requests/{confirmation_id}/respond",
    deps=["user", "db"],
    body=dict,
    tags=["orders"],
)
def respond_to_shipment_confirmation(
    order_id: int, confirmation_id: int, data: dict, current_user: dict, db: Session
):
    """Accept/reject a delivery shipment-confirmation request."""
    return _respond_to_shipment_confirmation(
        order_id, confirmation_id, data, current_user, db
    )

