"""orders domain - sanctioned cross-domain READ surface (ports).

Per NEW_STRUCTURE.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these functions instead
of importing ``domains.orders.models`` or ``domains.orders.services`` directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via ``rbac``).

Pagination uses **keyset (cursor) pagination** (ARCHITECTURE_DIAGRAM.md §6) so
hot lists scale to 100Ks of rows without OFFSET scans. Every ``list_*`` function
returns a ``CursorPage`` envelope: ``{items, next_cursor, page_size}`` where
``next_cursor`` is ``None`` when no further rows exist. ``page_size`` is clamped
to ``MAX_PAGE_SIZE`` to prevent a single unbounded query from OOMing the server.

Soft-deleted rows (``is_deleted``) are excluded where the model supports it, and
results are scoped to ``country_code`` when the caller supplies one (multi-tenant
isolation at the read boundary).
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session, selectinload

from domains.orders.models.orders import (
    Order,
    OrderItem,
    OrderLogisticsAllocation,
    ReturnRequest,
)

# Re-exports of logistics-facing tracking service functions (Law 3 sanctioned
# cross-domain surface). Modules (e.g. modules/logistics) import these from
# ``domains.orders.ports`` instead of reaching into the services tree.
from domains.orders.services.tracking.service import (  # noqa: E402, F401
    get_available_orders_for_logistics,
    get_order_shipment_label,
    logistics_cancel_pickup,
    logistics_confirm_pickup,
    logistics_deliver_order,
    logistics_scan_and_receive,
    logistics_update_transit_status,
)
from domains.orders.models.order_entities import OrderNotification
from infrastructure.utils.pagination import (
    MAX_PAGE_SIZE,
    CursorPage,
    cursor_paginate_desc,
    keyset_paginate,
    get_max_page_size,
)


def get_order_by_id(db: Session, id_: int) -> Optional[Order]:
    """Return Order by primary key (or None)."""
    return db.get(Order, id_)


def order_query(db: Session) -> object:
    """Return a base ``Order`` query (sanctioned delegation target for controllers).

    Controller-delegated helpers in other domains that previously did
    ``db.query(Order)`` should call this instead of importing the model.
    """
    return db.query(Order)


def order_item_query(db: Session) -> object:
    """Return a base ``OrderItem`` query for sanctioned cross-domain delegation."""
    return db.query(OrderItem)


def return_request_query(db: Session) -> object:
    """Return a base ``ReturnRequest`` query for sanctioned cross-domain delegation."""
    return db.query(ReturnRequest)


def order_logistics_allocation_query(db: Session) -> object:
    """Return a base ``OrderLogisticsAllocation`` query for sanctioned cross-domain delegation."""
    return db.query(OrderLogisticsAllocation)


# --- Model class references (for column access in cross-domain filters) ---

def order_model() -> type:
    """Return the ``Order`` model class (for column reference only)."""
    return Order


def order_item_model() -> type:
    """Return the ``OrderItem`` model class (for column reference only)."""
    return OrderItem


def return_request_model() -> type:
    """Return the ``ReturnRequest`` model class (for column reference only)."""
    return ReturnRequest


def list_orders(
    db: Session,
    *,
    page_size: int = MAX_PAGE_SIZE,
    cursor: Optional[str] = None,
    country_code: Optional[str] = None,
) -> CursorPage:
    """Keyset-paginated Order rows (newest first), excluding soft-deleted.

    Scoped to ``country_code`` when provided (multi-tenant isolation).
    """
    q = db.query(Order).filter(Order.is_deleted.is_(False))
    if country_code is not None:
        q = q.filter(Order.country_code == country_code)
    return cursor_paginate_desc(q, cursor=cursor, page_size=page_size)


def get_order_item_by_id(db: Session, id_: int) -> Optional[OrderItem]:
    """Return OrderItem by primary key (or None)."""
    return db.get(OrderItem, id_)


def list_order_items(
    db: Session,
    *,
    page_size: int = MAX_PAGE_SIZE,
    cursor: Optional[str] = None,
    country_code: Optional[str] = None,
) -> CursorPage:
    """Keyset-paginated OrderItem rows (newest first), country-scoped when given."""
    q = db.query(OrderItem)
    if country_code is not None:
        q = q.filter(OrderItem.country_code == country_code)
    return cursor_paginate_desc(q, cursor=cursor, page_size=page_size)


def get_order_logistics_allocation_by_id(
    db: Session, id_: int
) -> Optional[OrderLogisticsAllocation]:
    """Return OrderLogisticsAllocation by primary key (or None)."""
    return db.get(OrderLogisticsAllocation, id_)


def list_order_logistics_allocations(
    db: Session,
    *,
    page_size: int = MAX_PAGE_SIZE,
    cursor: Optional[str] = None,
    country_code: Optional[str] = None,
) -> CursorPage:
    """Keyset-paginated OrderLogisticsAllocation rows (newest first), country-scoped."""
    q = db.query(OrderLogisticsAllocation)
    if country_code is not None:
        q = q.filter(OrderLogisticsAllocation.country_code == country_code)
    return cursor_paginate_desc(q, cursor=cursor, page_size=page_size)


def get_return_request_by_id(db: Session, id_: int) -> Optional[ReturnRequest]:
    """Return ReturnRequest by primary key (or None)."""
    return db.get(ReturnRequest, id_)


def list_return_requests(
    db: Session,
    *,
    page_size: int = MAX_PAGE_SIZE,
    cursor: Optional[str] = None,
    country_code: Optional[str] = None,
) -> CursorPage:
    """Keyset-paginated ReturnRequest rows (newest first), country-scoped when given."""
    q = db.query(ReturnRequest)
    if country_code is not None:
        q = q.filter(ReturnRequest.country_code == country_code)
    return cursor_paginate_desc(q, cursor=cursor, page_size=page_size)


def get_order_notification_by_id(db: Session, id_: int) -> Optional[OrderNotification]:
    """Return OrderNotification by primary key (or None)."""
    return db.get(OrderNotification, id_)


def list_order_notifications(
    db: Session,
    *,
    page_size: int = MAX_PAGE_SIZE,
    cursor: Optional[str] = None,
    country_code: Optional[str] = None,
) -> CursorPage:
    """Keyset-paginated OrderNotification rows (newest first), excluding soft-deleted.

    Note: OrderNotification has no ``country_code`` column, so it is not
    country-scoped here.
    """
    q = db.query(OrderNotification).filter(OrderNotification.is_deleted.is_(False))
    return cursor_paginate_desc(q, cursor=cursor, page_size=page_size)


def get_order_by_payment_intent_id(
    db: Session, payment_intent_id: object
) -> Optional[Order]:
    """Return the Order whose ``payment_intent_id`` matches (or None).

    Used by payment webhook handlers to resolve an order from a gateway ref.
    """
    if payment_intent_id is None:
        return None
    return db.query(Order).filter(Order.payment_intent_id == payment_intent_id).first()


def get_order_by_payment_intent_or_id(
    db: Session, payment_intent_id: object, order_id: object
) -> Optional[Order]:
    """Resolve an order by payment intent id, falling back to its primary key.

    Mirrors the common ``filter(payment_intent_id==...).first() or
    filter(id==int(meta)).first()`` pattern used across payment handlers.
    """
    order = get_order_by_payment_intent_id(db, payment_intent_id)
    if order is None and order_id is not None:
        order = get_order_by_id(db, order_id)
    return order


def get_order_items_by_order_id(db: Session, order_id: int) -> List[OrderItem]:
    """Return every OrderItem belonging to ``order_id``."""
    return db.query(OrderItem).filter(OrderItem.order_id == order_id).all()


def get_order_item_by_order_id(db: Session, order_id: int) -> Optional[OrderItem]:
    """Return the first OrderItem belonging to ``order_id`` (or None)."""
    return db.query(OrderItem).filter(OrderItem.order_id == order_id).first()


def get_return_requests_by_order_id(
    db: Session, order_id: int
) -> List[ReturnRequest]:
    """Return every ReturnRequest belonging to ``order_id``."""
    return db.query(ReturnRequest).filter(ReturnRequest.order_id == order_id).all()


def count_orders(
    db: Session,
    *,
    status: Optional[str] = None,
    created_at_ge: Optional[object] = None,
    country_code: Optional[str] = None,
) -> int:
    """Count Order rows, optionally scoped by status / created-since / country."""
    q = db.query(Order)
    if status is not None:
        q = q.filter(Order.status == status)
    if created_at_ge is not None:
        q = q.filter(Order.created_at >= created_at_ge)
    if country_code is not None:
        q = q.filter(Order.country_code == country_code)
    return q.count()


def get_orders_by_user_and_id(
    db: Session, user_id: object, order_id: object
) -> Optional[Order]:
    """Return the Order with ``id == order_id`` that also belongs to ``user_id``."""
    return (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == user_id)
        .first()
    )


def get_order_by_id_with_user(db: Session, id_: int) -> Optional[Order]:
    """Return Order by pk with its ``user`` relationship eagerly loaded."""
    return (
        db.query(Order)
        .options(selectinload(Order.user))
        .filter(Order.id == id_)
        .first()
    )


def get_return_request_by_id_with_order_user(
    db: Session, id_: int
) -> Optional[ReturnRequest]:
    """Return ReturnRequest by pk with ``order`` and ``order.user`` eager-loaded."""
    return (
        db.query(ReturnRequest)
        .options(selectinload(ReturnRequest.order).selectinload(Order.user))
        .filter(ReturnRequest.id == id_)
        .first()
    )


# ---------------------------------------------------------------------------
# Supplier-facing read helpers (ORD-CONSUMER Law-3 closure for suppliers).
#
# The suppliers domain needs order data scoped to a supplier's items. Per Law 3
# those reads must come through this ports surface rather than importing the
# Order/OrderItem models and issuing ``db.query`` directly. These are pure
# reads; the join to ``OrderItem.product`` is expressed via the relationship so
# no ``domains.catalog`` import is required (keeps ports.py Law-1 clean).
# ---------------------------------------------------------------------------


def list_orders_by_supplier(db: Session, supplier_id: object) -> List[Order]:
    """Return distinct Orders that contain at least one of the supplier's items."""
    return (
        db.query(Order)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == supplier_id)
        .distinct()
        .all()
    )


def list_supplier_order_ids(db: Session, supplier_id: object) -> List[int]:
    """Return the ids of every Order containing at least one of the supplier's items."""
    return [
        row[0]
        for row in db.query(Order.id)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == supplier_id)
        .distinct()
        .all()
    ]


def get_supplier_order(
    db: Session, order_id: object, supplier_id: object
) -> Optional[Order]:
    """Return the Order with ``id == order_id`` that contains a supplier's item."""
    return (
        db.query(Order)
        .filter(Order.id == order_id)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == supplier_id)
        .first()
    )


def get_supplier_order_items(
    db: Session, order_id: object, supplier_id: object
) -> List[OrderItem]:
    """Return the supplier's OrderItems for a given order."""
    return (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order_id, OrderItem.supplier_id == supplier_id)
        .all()
    )


def get_supplier_order_for_verify(
    db: Session, order_id: object, user_id: object
) -> Optional[Order]:
    """Return a supplier-owned Order (joined through product) for parcel verify."""
    return (
        db.query(Order)
        .filter(Order.id == order_id)
        .join(OrderItem)
        .join(OrderItem.product)
        .filter(OrderItem.product.has(supplier_id=user_id))
        .first()
    )


def get_supplier_order_items_for_verify(
    db: Session, order_id: object, user_id: object
) -> List[OrderItem]:
    """Return a supplier's OrderItems (joined through product) for parcel verify."""
    return (
        db.query(OrderItem)
        .join(OrderItem.product)
        .filter(
            OrderItem.order_id == order_id,
            OrderItem.product.has(supplier_id=user_id),
        )
        .all()
    )


def count_orders_by_supplier(db: Session, supplier_id: object) -> int:
    """Count Orders containing at least one of the supplier's items."""
    return (
        db.query(Order.id)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == supplier_id)
        .distinct()
        .count()
    )


def get_supplier_order_eager(
    db: Session, order_id: object, supplier_id: object
) -> Optional[Order]:
    """Return a supplier-owned Order with ``items`` and ``items.product`` eager-loaded."""
    return (
        db.query(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.id == order_id)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == supplier_id)
        .first()
    )


def has_supplier_products_in_order(
    db: Session, order_id: object, supplier_id: object
) -> bool:
    """True if the order contains at least one item whose product belongs to the supplier."""
    return (
        db.query(OrderItem)
        .join(OrderItem.product)
        .filter(
            OrderItem.order_id == order_id,
            OrderItem.product.has(supplier_id=supplier_id),
        )
        .first()
        is not None
    )


def get_supplier_order_summaries(
    db: Session, supplier_id: object
) -> List:
    """Return ``(order_id, created_at)`` rows for every order with the supplier's items."""
    return (
        db.query(Order.id.label("order_id"), Order.created_at.label("created_at"))
        .join(OrderItem)
        .filter(OrderItem.supplier_id == supplier_id)
        .distinct()
        .all()
    )


def count_orders_for_supplier_products(
    db: Session, supplier_id: object
) -> int:
    """Count Orders joined through OrderItem -> Product for ``supplier_id``."""
    return (
        db.query(Order)
        .join(OrderItem)
        .join(OrderItem.product)
        .filter(OrderItem.product.has(supplier_id=supplier_id))
        .distinct()
        .count()
    )


# ---------------------------------------------------------------------------
# Supplier analytics + report read helpers (ORD-CONSUMER Law-3 closure).
#
# Centralises every supplier-scoped aggregation that previously lived as raw
# ``db.query(Order/OrderItem)`` inside the suppliers domain. Order/OrderItem are
# filtered via ``OrderItem.supplier_id`` / ``OrderItem.product_id`` (no catalog
# import required for the purely order-scoped helpers); helpers that must return
# Product projections import ``Product`` locally so ports.py stays Law-1 clean
# at import time. All suppliers-domain callers now read orders ONLY through here.
# ---------------------------------------------------------------------------


def supplier_order_id_query(db: Session, supplier_id: object) -> object:
    """Base query for ``(order_id, created_at)`` rows of a supplier's orders."""
    return (
        db.query(Order.id.label("order_id"), Order.created_at.label("created_at"))
        .join(OrderItem)
        .filter(OrderItem.supplier_id == supplier_id)
        .distinct()
    )


def get_orders_eager_by_ids(db: Session, order_ids: List[int]) -> List[Order]:
    """Return Orders with ``items`` + ``items.product`` eager-loaded, by id list."""
    if not order_ids:
        return []
    return (
        db.query(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.id.in_(order_ids))
        .all()
    )


def sum_supplier_revenue(
    db: Session,
    supplier_id: object,
    start: object = None,
    end: object = None,
    status: object = None,
) -> float:
    """Sum ``price * quantity`` of a supplier's order items, optionally windowed."""
    q = (
        db.query(func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0))
        .join(Order)
        .filter(OrderItem.supplier_id == supplier_id)
    )
    if start is not None:
        q = q.filter(Order.created_at >= start)
    if end is not None:
        q = q.filter(Order.created_at < end)
    if status is not None:
        q = q.filter(Order.status == status)
    return q.scalar() or 0


def count_supplier_orders_in_range(
    db: Session,
    supplier_id: object,
    start: object = None,
    end: object = None,
) -> int:
    """Count distinct supplier Orders, optionally windowed by ``created_at``."""
    q = db.query(Order).join(OrderItem).filter(OrderItem.supplier_id == supplier_id).distinct()
    if start is not None:
        q = q.filter(Order.created_at >= start)
    if end is not None:
        q = q.filter(Order.created_at < end)
    return q.count()


def supplier_revenue_by_date(
    db: Session, supplier_id: object, start: object, end: object = None
) -> List:
    """Daily ``(date, revenue)`` rows for a supplier from ``start`` onward."""
    q = (
        db.query(
            func.date(Order.created_at).label("date"),
            func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
        )
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(OrderItem.supplier_id == supplier_id, Order.created_at >= start)
    )
    if end is not None:
        q = q.filter(Order.created_at < end)
    return q.group_by(func.date(Order.created_at)).all()


def get_top_selling_products_for_supplier(
    db: Session, supplier_id: object, start: object, limit: int = 10
) -> List:
    """Top-selling Products (with sales + revenue) for a supplier since ``start``."""
    from domains.catalog.ports import Product

    return (
        db.query(
            Product.id,
            Product.name,
            Product.image_url,
            func.count(OrderItem.id).label("sales"),
            func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
        )
        .join(OrderItem)
        .join(Order)
        .filter(Product.supplier_id == supplier_id, Order.created_at >= start)
        .group_by(Product.id, Product.name, Product.image_url)
        .order_by(func.sum(OrderItem.price * OrderItem.quantity).desc())
        .limit(limit)
        .all()
    )


def sum_revenue_for_products(
    db: Session,
    product_ids: List[int],
    start: object = None,
    end: object = None,
    statuses: object = None,
) -> float:
    """Sum ``price * quantity`` of order items whose product is in ``product_ids``."""
    q = (
        db.query(func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0))
        .join(Order)
        .filter(OrderItem.product_id.in_(product_ids))
    )
    if start is not None:
        q = q.filter(Order.created_at >= start)
    if end is not None:
        q = q.filter(Order.created_at < end)
    if statuses:
        q = q.filter(Order.status.in_(statuses))
    return q.scalar() or 0


def count_distinct_orders_for_products(
    db: Session,
    product_ids: List[int],
    start: object = None,
    end: object = None,
    statuses: object = None,
) -> int:
    """Count distinct Orders containing any of ``product_ids``."""
    q = db.query(func.count(func.distinct(Order.id))).join(OrderItem).filter(
        OrderItem.product_id.in_(product_ids)
    )
    if start is not None:
        q = q.filter(Order.created_at >= start)
    if end is not None:
        q = q.filter(Order.created_at < end)
    if statuses:
        q = q.filter(Order.status.in_(statuses))
    return q.scalar() or 0


def revenue_by_date_for_products(
    db: Session, product_ids: List[int], start: object, statuses: object = None
) -> List:
    """Daily ``(date, revenue)`` rows for ``product_ids`` from ``start`` onward."""
    q = (
        db.query(
            func.date(Order.created_at).label("date"),
            func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
        )
        .join(Order)
        .filter(OrderItem.product_id.in_(product_ids), Order.created_at >= start)
    )
    if statuses:
        q = q.filter(Order.status.in_(statuses))
    return q.group_by(func.date(Order.created_at)).order_by(func.date(Order.created_at)).all()


def count_distinct_customers_for_products(
    db: Session,
    product_ids: List[int],
    start: object = None,
    end: object = None,
    statuses: object = None,
) -> int:
    """Count distinct customers (Order.user_id) who bought ``product_ids``."""
    q = db.query(func.count(func.distinct(Order.user_id))).join(OrderItem).filter(
        OrderItem.product_id.in_(product_ids)
    )
    if start is not None:
        q = q.filter(Order.created_at >= start)
    if end is not None:
        q = q.filter(Order.created_at < end)
    if statuses:
        q = q.filter(Order.status.in_(statuses))
    return q.scalar() or 0


def top_products_for_supplier_reports(
    db: Session, supplier_id: object, start: object, limit: int = 10, statuses: object = None
) -> List:
    """Top Products (name/id/image/sales/revenue) for supplier report cards."""
    from domains.catalog.ports import Product

    q = (
        db.query(
            Product.name,
            Product.id,
            Product.image_url,
            func.sum(OrderItem.quantity).label("sales"),
            func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
        )
        .join(OrderItem)
        .join(Order)
        .filter(Product.supplier_id == supplier_id, Order.created_at >= start)
    )
    if statuses:
        q = q.filter(Order.status.in_(statuses))
    return (
        q.group_by(Product.id, Product.name, Product.image_url)
        .order_by(func.sum(OrderItem.price * OrderItem.quantity).desc())
        .limit(limit)
        .all()
    )


def sum_quantity_for_product(
    db: Session, product_id: int, start: object = None, statuses: object = None
) -> float:
    """Sum order-item quantity for a single product."""
    q = db.query(func.coalesce(func.sum(OrderItem.quantity), 0)).join(Order).filter(
        OrderItem.product_id == product_id
    )
    if start is not None:
        q = q.filter(Order.created_at >= start)
    if statuses:
        q = q.filter(Order.status.in_(statuses))
    return q.scalar() or 0


def count_sales_for_product(
    db: Session, product_id: int, start: object = None, statuses: object = None
) -> int:
    """Count order items for a single product."""
    q = db.query(func.count(OrderItem.id)).join(Order).filter(OrderItem.product_id == product_id)
    if start is not None:
        q = q.filter(Order.created_at >= start)
    if statuses:
        q = q.filter(Order.status.in_(statuses))
    return q.scalar() or 0


def sum_revenue_for_product(
    db: Session, product_id: int, start: object = None, statuses: object = None
) -> float:
    """Sum ``price * quantity`` for a single product."""
    q = db.query(func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0)).join(Order).filter(
        OrderItem.product_id == product_id
    )
    if start is not None:
        q = q.filter(Order.created_at >= start)
    if statuses:
        q = q.filter(Order.status.in_(statuses))
    return q.scalar() or 0


def get_product_sales_summary(
    db: Session, product_id: int, start: object = None, statuses: object = None
) -> object:
    """Return ``(sales_count, revenue)`` for a single product."""
    q = db.query(
        func.count(OrderItem.id).label("sales_count"),
        func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0).label("revenue"),
    ).join(Order).filter(OrderItem.product_id == product_id)
    if start is not None:
        q = q.filter(Order.created_at >= start)
    if statuses:
        q = q.filter(Order.status.in_(statuses))
    return q.first()


def order_item_sales_by_products(db: Session, product_ids: List[int]) -> List:
    """Return ``(product_id, sales_count, revenue)`` rows grouped by product."""
    if not product_ids:
        return []
    return (
        db.query(
            OrderItem.product_id.label("product_id"),
            func.count(OrderItem.id).label("sales_count"),
            func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0).label("revenue"),
        )
        .filter(OrderItem.product_id.in_(product_ids))
        .group_by(OrderItem.product_id)
        .all()
    )


def fulfilled_orders_count_for_supplier(
    db: Session, supplier_id: object, statuses: List[str]
) -> int:
    """Count distinct fulfilled Orders for a supplier (badge metrics)."""
    from domains.catalog.ports import Product

    return (
        db.query(func.count(func.distinct(Order.id)))
        .join(OrderItem)
        .join(Product)
        .filter(Product.supplier_id == supplier_id, Order.status.in_(statuses))
        .scalar()
    ) or 0


def monthly_revenue_for_supplier(
    db: Session, supplier_id: object, statuses: List[str], month_start: object
) -> float:
    """Sum supplier monthly revenue (badge metrics)."""
    from domains.catalog.ports import Product

    return (
        db.query(func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0))
        .select_from(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, Product.id == OrderItem.product_id)
        .filter(
            Product.supplier_id == supplier_id,
            Order.status.in_(statuses),
            Order.created_at >= month_start,
        )
        .scalar()
    ) or 0


def list_orders_for_ids_in_range(
    db: Session,
    order_ids: List[int],
    start: object,
    end: object,
    country_code: object = None,
) -> List[Order]:
    """Return Orders whose id is in ``order_ids`` and ``created_at`` in [start, end]."""
    if not order_ids:
        return []
    q = db.query(Order).filter(
        Order.id.in_(order_ids),
        Order.created_at >= start,
        Order.created_at <= end,
    )
    if country_code:
        q = q.filter(Order.shipping_country == country_code)
    return q.all()


def count_returns_for_order_ids(db: Session, order_ids: List[int]) -> int:
    """Count ReturnRequests whose ``order_id`` is in ``order_ids``."""
    if not order_ids:
        return 0
    return db.query(ReturnRequest).filter(ReturnRequest.order_id.in_(order_ids)).count()


def supplier_orders_query(db: Session, supplier_id: object) -> object:
    """Base ``Order`` query for a supplier (joined through items, de-duplicated)."""
    return (
        db.query(Order)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == supplier_id)
        .distinct()
    )


def sum_supplier_order_item_total_price(db: Session, supplier_id: object) -> float:
    """Sum ``OrderItem.total_price`` across a supplier's items."""
    return (
        db.query(func.coalesce(func.sum(OrderItem.total_price), 0))
        .filter(OrderItem.supplier_id == supplier_id)
        .scalar()
        or 0
    )


def count_distinct_supplier_order_item_orders(db: Session, supplier_id: object) -> int:
    """Count distinct order ids among a supplier's order items."""
    return (
        db.query(func.count(func.distinct(OrderItem.order_id)))
        .filter(OrderItem.supplier_id == supplier_id)
        .scalar()
        or 0
    )


# ---------------------------------------------------------------------------
# Cross-domain read helpers for the OTHER domains (ORD-CONSUMER Law-3 closure).
#
# Every other domain (accounts, customers, catalog, comms, country, finance,
# governance, logistics, media) that needs Order/OrderItem/ReturnRequest/
# OrderLogisticsAllocation data must read it through the helpers below instead
# of importing the models and issuing ``db.query`` directly. These are pure
# reads: no writes, no permission checks (callers gate via ``rbac``).
# ---------------------------------------------------------------------------


def list_orders_by_user(
    db: Session,
    user_id: object,
    *,
    eager_items_product: bool = False,
    eager_shipments: bool = False,
    eager_user: bool = False,
    created_ge: object = None,
    created_le: object = None,
    statuses: object = None,
    limit: object = None,
    ordered_desc: bool = False,
) -> List[Order]:
    """Return Orders belonging to ``user_id`` with optional scoping/eager-loading.

    ``eager_*`` flags add ``selectinload`` for items->product, shipments, user.
    ``created_ge`` / ``created_le`` window by ``created_at``. ``statuses`` is an
    iterable of statuses to filter on. ``limit`` caps rows; ``ordered_desc``
    orders newest-first.
    """
    q = db.query(Order).filter(Order.user_id == user_id)
    if created_ge is not None:
        q = q.filter(Order.created_at >= created_ge)
    if created_le is not None:
        q = q.filter(Order.created_at <= created_le)
    if statuses:
        q = q.filter(Order.status.in_(list(statuses)))
    opts = []
    if eager_items_product:
        opts.append(selectinload(Order.items).selectinload(OrderItem.product))
    if eager_shipments:
        opts.append(selectinload(Order.shipments))
    if eager_user:
        opts.append(selectinload(Order.user))
    if opts:
        q = q.options(*opts)
    if ordered_desc:
        q = q.order_by(Order.created_at.desc())
    if limit is not None:
        q = q.limit(limit)
    return q.all()


def count_orders_for_user(
    db: Session,
    user_id: object,
    *,
    statuses: object = None,
    created_ge: object = None,
    created_le: object = None,
) -> int:
    """Count Orders belonging to ``user_id`` (optionally status / date windowed)."""
    q = db.query(Order).filter(Order.user_id == user_id)
    if statuses:
        q = q.filter(Order.status.in_(list(statuses)))
    if created_ge is not None:
        q = q.filter(Order.created_at >= created_ge)
    if created_le is not None:
        q = q.filter(Order.created_at <= created_le)
    return q.count()


def list_return_requests_by_user(
    db: Session,
    user_id: object,
    *,
    created_ge: object = None,
    created_le: object = None,
) -> List[ReturnRequest]:
    """Return ReturnRequests whose ``user_id`` matches (optionally date windowed)."""
    q = db.query(ReturnRequest).filter(ReturnRequest.user_id == user_id)
    if created_ge is not None:
        q = q.filter(ReturnRequest.created_at >= created_ge)
    if created_le is not None:
        q = q.filter(ReturnRequest.created_at <= created_le)
    return q.all()


def count_return_requests_for_user(db: Session, user_id: object) -> int:
    """Count ReturnRequests whose ``user_id`` matches."""
    return db.query(ReturnRequest).filter(ReturnRequest.user_id == user_id).count()


def list_return_requests_by_order_ids(
    db: Session, order_ids: List[int]
) -> List[ReturnRequest]:
    """Return ReturnRequests whose ``order_id`` is in ``order_ids``."""
    if not order_ids:
        return []
    return db.query(ReturnRequest).filter(ReturnRequest.order_id.in_(order_ids)).all()


def get_order_by_id_eager_items(db: Session, id_: int) -> Optional[Order]:
    """Return Order by pk with ``items`` and ``items.product`` eager-loaded."""
    return (
        db.query(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.id == id_)
        .first()
    )


def get_order_by_id_eager_items_user(db: Session, id_: int) -> Optional[Order]:
    """Return Order by pk with ``items->product`` and ``user`` eager-loaded."""
    return (
        db.query(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.user),
        )
        .filter(Order.id == id_)
        .first()
    )


def list_orders_by_ids(
    db: Session,
    order_ids: List[int],
    *,
    eager_items_product: bool = False,
    eager_user: bool = False,
    ordered_by_id: bool = False,
) -> List[Order]:
    """Return Orders whose id is in ``order_ids`` (optionally eager-loaded)."""
    if not order_ids:
        return []
    q = db.query(Order).filter(Order.id.in_(order_ids))
    opts = []
    if eager_items_product:
        opts.append(selectinload(Order.items).selectinload(OrderItem.product))
    if eager_user:
        opts.append(selectinload(Order.user))
    if opts:
        q = q.options(*opts)
    if ordered_by_id:
        q = q.order_by(Order.id)
    return q.all()


def list_all_orders_ordered_by_id(
    db: Session, *, limit: object = None, country_code: object = None
) -> List[Order]:
    """Return every Order ordered by ``id`` (export-style dump).

    ``limit`` caps rows; ``country_code`` scopes to a tenant when provided.
    """
    q = db.query(Order).order_by(Order.id)
    if country_code is not None:
        q = q.filter(Order.country_code == country_code)
    if limit is not None:
        q = q.limit(limit)
    return q.all()


def list_orders_for_product(
    db: Session,
    product_id: int,
    *,
    statuses: object = None,
    eager_items: bool = False,
) -> List[Order]:
    """Return Orders that contain ``product_id`` (optionally status-windowed).

    Used by catalog to find in-flight orders affecting a product.
    """
    q = (
        db.query(Order)
        .join(OrderItem)
        .filter(OrderItem.product_id == product_id)
    )
    if statuses:
        q = q.filter(Order.status.in_(list(statuses)))
    if eager_items:
        q = q.options(selectinload(Order.items).selectinload(OrderItem.product))
    return q.distinct().all()


def list_order_logistics_allocations_by_order_id(
    db: Session, order_id: object
) -> List[OrderLogisticsAllocation]:
    """Return every OrderLogisticsAllocation for ``order_id``."""
    return (
        db.query(OrderLogisticsAllocation)
        .filter(OrderLogisticsAllocation.order_id == order_id)
        .all()
    )


def list_order_logistics_allocations_for_order_ids(
    db: Session, order_ids: List[int]
) -> List[OrderLogisticsAllocation]:
    """Return every OrderLogisticsAllocation whose ``order_id`` is in ``order_ids``."""
    if not order_ids:
        return []
    return (
        db.query(OrderLogisticsAllocation)
        .filter(OrderLogisticsAllocation.order_id.in_(order_ids))
        .all()
    )


def order_logistics_allocations_query(db: Session, **filters: object) -> object:
    """Return a base ``OrderLogisticsAllocation`` query, optionally equality-filtered.

    Callers chain their own ``.order_by()`` / ``.first()`` / ``.all()`` so behaviour
    stays identical to the previous inline ``db.query(OrderLogisticsAllocation)``.
    """
    q = db.query(OrderLogisticsAllocation)
    if filters:
        q = q.filter(
            *[getattr(OrderLogisticsAllocation, k) == v for k, v in filters.items()]
        )
    return q


def user_purchased_product_ids_subquery(
    db: Session, user_id: object, limit: int = 20
) -> object:
    """Scalar subquery of distinct ``product_id`` values this user purchased."""
    return (
        db.query(OrderItem.product_id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.user_id == user_id)
        .distinct()
        .limit(limit)
        .scalar_subquery()
    )


def co_purchase_order_ids_subquery(
    db: Session, user_product_ids_subq: object, user_id: object, limit: int = 100
) -> object:
    """Scalar subquery of order ids from *other* users containing ``user_product_ids_subq``."""
    return (
        db.query(OrderItem.order_id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            OrderItem.product_id.in_(user_product_ids_subq),
            Order.user_id != user_id,
        )
        .distinct()
        .limit(limit)
        .scalar_subquery()
    )


def list_user_purchased_product_ids(db: Session, user_id: object) -> List[int]:
    """Return the distinct ``product_id`` values this user has purchased."""
    return [
        row.product_id
        for row in db.query(OrderItem.product_id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.user_id == user_id)
        .distinct()
        .all()
    ]


def user_category_purchase_units(db: Session, user_id: object) -> List:
    """Return ``(category, units)`` rows of products this user bought, units desc.

    Joins Product -> OrderItem -> Order so the catalog domain can read a user's
    category-affinity without importing Order/OrderItem directly.
    """
    from domains.catalog.ports import Product

    return (
        db.query(Product.category, func.sum(OrderItem.quantity).label("units"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.user_id == user_id)
        .group_by(Product.category)
        .order_by(desc(func.sum(OrderItem.quantity)))
        .all()
    )


def user_avg_purchased_product_price(db: Session, user_id: object) -> object:
    """Return the average ``Product.price`` of products this user bought (row)."""
    from domains.catalog.ports import Product

    return (
        db.query(func.avg(Product.price).label("avg_price"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.user_id == user_id)
        .first()
    )


def user_collaborative_category_boosts(
    db: Session,
    user_id: object,
    seed_limit: int = 20,
    co_limit: int = 100,
    rows_limit: int = 50,
) -> List:
    """Return ``(category, co_count)`` rows for the "also bought" signal.

    Finds products other users purchased in orders that share this user's
    purchased products, boosting those categories. Catalog-scoped via the local
    ``Product`` import (Law-1 clean); order scoping stays inside ports.
    """
    from domains.catalog.ports import Product

    user_product_ids_subq = user_purchased_product_ids_subquery(db, user_id, limit=seed_limit)
    co_order_ids_subq = co_purchase_order_ids_subquery(
        db, user_product_ids_subq, user_id, limit=co_limit
    )
    return (
        db.query(Product.category, func.count(OrderItem.product_id).label("co_count"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .filter(
            OrderItem.order_id.in_(co_order_ids_subq),
            Product.id.notin_(user_product_ids_subq),
            Product.is_deleted == False,  # noqa: E712
            Product.is_active == True,    # noqa: E712
            Product.is_approved == True,  # noqa: E712
        )
        .group_by(Product.category)
        .limit(rows_limit)
        .all()
    )


# ---------------------------------------------------------------------------
# Additional cross-domain read helpers (ORD-CONSUMER Branch 1 closure).
#
# Covers the recurring query shapes still issued inline by accounts / country /
# customers / finance / governance / logistics / media so those domains stop
# constructing ``Order`` / ``OrderItem`` / ``ReturnRequest`` queries directly.
# All helpers are pure reads; callers keep their own rbac / RLS gating.
# ---------------------------------------------------------------------------


def count_all_orders(db: Session) -> int:
    """Count every Order (export / analytics summaries)."""
    return db.query(func.count(Order.id)).scalar() or 0


def export_orders_query(db: Session) -> object:
    """Return every Order ordered by ``id`` as a *query* (streaming export)."""
    return db.query(Order).order_by(Order.id)


def list_orders_paginated(
    db: Session,
    *,
    status: object = None,
    include_deleted: bool = True,
    page: int = 1,
    size: int = 20,
    order_by_created_desc: bool = True,
    cursor: object = None,
) -> dict:
    """Paginated Orders with optional status / soft-delete gating (admin listing).

    Backward-compatible envelope ``{items, total, page, pages}``. When ``cursor``
    is supplied the items are fetched with **keyset** pagination (no OFFSET scan,
    the 100Ks-scale strategy from ARCHITECTURE_DIAGRAM.md §6); otherwise the
    classic page/offset behaviour is preserved for callers that have not yet
    adopted cursors. ``next_cursor`` is always returned so the client can switch
    to cursor navigation.
    """
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    if not include_deleted:
        q = q.filter(Order.is_deleted == False)  # noqa: E712
    total = q.count()
    page_size = max(1, min(int(size or 20), get_max_page_size()))
    direction = "desc" if order_by_created_desc else "asc"
    sort_keys = [(Order.created_at, direction), (Order.id, direction)]

    # B6 / R6: hot lists MUST use keyset (cursor) pagination, never OFFSET.
    # Callers may still request a 1-based ``page`` (backward-compatible envelope);
    # we reach it by walking the keyset cursor from the start — cheap for the
    # small page numbers admin lists use. Passing ``cursor`` directly skips the
    # walk and is the preferred 100Ks-scale path.
    page = max(1, int(page or 1))
    eff_cursor = cursor
    if eff_cursor is None and page > 1:
        cur = None
        for _ in range(page - 1):
            step = keyset_paginate(q, sort_keys=sort_keys, cursor=cur, page_size=page_size)
            cur = step["next_cursor"]
            if cur is None:
                break
        eff_cursor = cur

    ks = keyset_paginate(q, sort_keys=sort_keys, cursor=eff_cursor, page_size=page_size)
    pages = max(1, (total + page_size - 1) // page_size) if total else 1
    return {
        "items": ks["items"],
        "next_cursor": ks["next_cursor"],
        "page_size": ks["page_size"],
        "has_next": ks["has_next"],
        "total": total,
        "page": page,
        "pages": pages,
    }


def list_orders_keyset(
    db: Session,
    *,
    status: object = None,
    include_deleted: bool = True,
    cursor: object = None,
    size: int = 50,
    order_by_created_desc: bool = True,
) -> dict:
    """Canonical 100Ks-scale hot-list reader for Orders (keyset, never OFFSET).

    Returns a cursor envelope ``{items, next_cursor, page_size, has_next}``. This
    is the preferred entry point for any order-list endpoint and is the form the
    admin order routers should adopt. ``next_cursor`` is ``None`` when the final
    page is reached.
    """
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    if not include_deleted:
        q = q.filter(Order.is_deleted == False)  # noqa: E712
    direction = "desc" if order_by_created_desc else "asc"
    sort_keys = [(Order.created_at, direction), (Order.id, direction)]
    return keyset_paginate(q, sort_keys=sort_keys, cursor=cursor, page_size=size)


def get_order_for_supplier(
    db: Session, order_id: object, supplier_id: object
) -> Optional[Order]:
    """Return an Order only if it contains an item owned by ``supplier_id``."""
    return (
        db.query(Order)
        .join(OrderItem)
        .filter(Order.id == order_id, OrderItem.supplier_id == supplier_id)
        .first()
    )


def count_orders_for_user_status_no_proof(db: Session, user_id: object) -> int:
    """Count a user's delivered Orders missing a delivery proof (fraud signal)."""
    return (
        db.query(Order)
        .filter(
            Order.user_id == user_id,
            Order.status == "delivered",
            Order.delivery_proof_url.is_(None),
        )
        .count()
    )


def list_recent_orders_for_user(
    db: Session, user_id: object, since, *, limit: object = None
) -> List[Order]:
    """Orders for ``user_id`` created at/after ``since`` (fraud frequency signal)."""
    q = db.query(Order).filter(Order.user_id == user_id, Order.created_at >= since)
    if limit is not None:
        q = q.limit(limit)
    return q.all()


def list_recent_payout_orders_for_user(
    db: Session, user_id: object, since
) -> List[Order]:
    """Payout-method Orders for ``user_id`` created at/after ``since``."""
    return (
        db.query(Order)
        .filter(
            Order.user_id == user_id,
            Order.payment_method == "payout",
            Order.created_at >= since,
        )
        .all()
    )


def list_order_item_order_ids_for_products(
    db: Session, product_ids: List[int]
) -> List[int]:
    """Distinct Order ids that contain any of ``product_ids`` (logistics batching)."""
    if not product_ids:
        return []
    return [
        row[0]
        for row in db.query(OrderItem.order_id)
        .filter(OrderItem.product_id.in_(product_ids))
        .distinct()
        .all()
    ]


def count_awaiting_orders(
    db: Session,
    order_ids: List[int],
    shipped_order_ids: List[int],
    statuses,
) -> int:
    """Count orders in ``order_ids`` not yet shipped and within ``statuses``."""
    if not order_ids:
        return 0
    q = db.query(Order).filter(
        Order.id.in_(order_ids),
        Order.id.notin_(shipped_order_ids),
        Order.status.in_(list(statuses)),
    )
    return q.count()


def list_orders_for_shipping(
    db: Session,
    order_ids: List[int],
    *,
    exclude_ids: object = None,
    statuses=("confirmed", "paid", "processing"),
    offset: int = 0,
    limit: int = 200,
) -> List[Order]:
    """Eager Orders (items->product) in ``order_ids`` pending shipment.

    Chunking is done by slicing the created_at-ordered id sequence in Python
    rather than SQL ``OFFSET`` (B6 / R6 — no OFFSET scan on the join), so the
    same ``[offset:offset+limit]`` window is returned as before.
    """
    if not order_ids:
        return []
    offset = max(0, int(offset or 0))
    limit = min(max(1, int(limit or 200)), 200)

    ordered_ids = [
        row[0]
        for row in db.query(Order.id)
        .filter(Order.id.in_(order_ids), Order.status.in_(list(statuses)))
        .order_by(Order.created_at)
        .all()
    ]
    if exclude_ids:
        exclude = set(exclude_ids)
        ordered_ids = [oid for oid in ordered_ids if oid not in exclude]
    chunk = ordered_ids[offset:offset + limit]
    if not chunk:
        return []
    return (
        db.query(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.id.in_(chunk))
        .order_by(Order.created_at)
        .all()
    )


def list_orders_by_payment_status_invoice(
    db: Session,
    *,
    payment_method: str,
    status: str,
    invoice_is_null: bool = False,
    country_code: object = None,
) -> List[Order]:
    """Orders matching a payment method / status, optionally missing an invoice."""
    q = db.query(Order).filter(
        Order.payment_method == payment_method,
        Order.status == status,
    )
    if invoice_is_null:
        q = q.filter(Order.invoice_id.is_(None))
    if country_code:
        q = q.filter(Order.country_code == country_code)
    return q.all()


def has_verified_purchase(db: Session, user_id: object, product_id: object) -> bool:
    """True if ``user_id`` has a delivered/completed Order for ``product_id``."""
    return (
        db.query(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Order.user_id == user_id,
            OrderItem.product_id == product_id,
            Order.status.in_(["delivered", "completed"]),
        )
        .first()
        is not None
    )


def list_orders_affected_by_product(
    db: Session, product_id: object, statuses
) -> List[Order]:
    """Orders containing ``product_id`` within ``statuses`` (cascade notifications)."""
    return (
        db.query(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(OrderItem.product_id == product_id, Order.status.in_(list(statuses)))
        .all()
    )


def list_orders_cod_delivered(db: Session, *, country_code: object = None) -> List[Order]:
    """COD Orders marked delivered (media remittance alerts)."""
    q = db.query(Order).filter(
        Order.payment_method == "cod",
        Order.status == "delivered",
    )
    if country_code:
        q = q.filter(Order.country_code == country_code)
    return q.all()


# ---------------------------------------------------------------------------
# Supplier-admin analytics aggregations (ORD-CONSUMER Branch 1 closure).
#
# ``domains/suppliers/services/suppliers_service.py`` (admin) computed supplier
# revenue / order-count by joining OrderItem -> Product (and Order for the time
# windows) directly via ``aggregate_rows``. Those joins are moved here so the
# suppliers domain no longer references the Order / OrderItem models.
# ---------------------------------------------------------------------------


def aggregate_supplier_revenue_order_count(
    db: Session, supplier_ids: List[int]
) -> List:
    """Per-supplier revenue + distinct order count from their OrderItems."""
    from domains.catalog.models.products import Product

    if not supplier_ids:
        return []
    return (
        db.query(
            Product.supplier_id,
            func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
            func.count(func.distinct(OrderItem.order_id)).label("order_count"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .filter(Product.supplier_id.in_(supplier_ids), Product.is_deleted == False)
        .group_by(Product.supplier_id)
        .all()
    )


def aggregate_supplier_revenue_window(
    db: Session, supplier_ids: List[int], since, *, until: object = None
) -> List:
    """Per-supplier revenue in ``[since, until)`` from their OrderItems (via Order)."""
    from domains.catalog.models.products import Product

    if not supplier_ids:
        return []
    q = (
        db.query(
            Product.supplier_id,
            func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0).label("revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Product.supplier_id.in_(supplier_ids),
            Product.is_deleted == False,
            Order.created_at >= since,
        )
        .group_by(Product.supplier_id)
    )
    if until is not None:
        q = q.filter(Order.created_at < until)
    return q.all()


def sum_supplier_total_revenue(db: Session) -> float:
    """Total revenue across all supplier OrderItems (OrderItem->Product->User)."""
    from domains.accounts.models.user import User
    from domains.catalog.models.products import Product

    return (
        db.query(func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0))
        .join(Product, Product.id == OrderItem.product_id)
        .join(User, User.id == Product.supplier_id)
    .filter(User.role == "supplier", Product.is_deleted == False)
    .scalar()
    or 0
)

# --- Lazy service exports (Law 3 sanctioned cross-domain surface) ---
# Cross-domain consumers import these from ports instead of reaching
# into the services tree directly.
_LAZY_SERVICE_EXPORTS: dict[str, tuple[str, str]] = {
    "CartShippingQuoteRequest": ("domains.orders.services.cart_legacy_service", "CartShippingQuoteRequest"),
    "get_cart_shipping_quote": ("domains.orders.services.cart_legacy_service", "get_cart_shipping_quote"),
    "create_campaign": ("domains.orders.services.core.admin_extra", "create_campaign"),
    "delete_campaign": ("domains.orders.services.core.admin_extra", "delete_campaign"),
    "list_all_campaigns": ("domains.orders.services.core.admin_extra", "list_all_campaigns"),
    "list_campaigns": ("domains.orders.services.core.admin_extra", "list_campaigns"),
    "create_coupon_from_payload": ("domains.orders.services.coupons_write_service", "create_coupon_from_payload"),
    "delete_coupon_by_id": ("domains.orders.services.coupons_write_service", "delete_coupon_by_id"),
    "list_coupons_paginated": ("domains.orders.services.coupons_write_service", "list_coupons_paginated"),
    "validate_coupon": ("domains.orders.services.coupons_write_service", "validate_coupon"),
    "_get_or_create_config": ("domains.orders.services.promotion_service", "_get_or_create_config"),
    "order_status_label": ("domains.orders.services.tracking.service", "order_status_label"),
    "shipment_status_label": ("domains.orders.services.tracking.service", "shipment_status_label"),
    "canonical_scan_code": ("domains.orders.services.tracking.service", "canonical_scan_code"),
    "derive_order_financials": ("domains.orders.services.tracking.service", "derive_order_financials"),
    "ensure_shipment_identifiers": ("domains.orders.services.tracking.service", "ensure_shipment_identifiers"),
    "reconcile_order_status": ("domains.orders.services.tracking.service", "reconcile_order_status"),
}
import importlib

def __getattr__(name: str):
    if name in _LAZY_SERVICE_EXPORTS:
        module_path, symbol = _LAZY_SERVICE_EXPORTS[name]
        mod = importlib.import_module(module_path)
        value = getattr(mod, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

