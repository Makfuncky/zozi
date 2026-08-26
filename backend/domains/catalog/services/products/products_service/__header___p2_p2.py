"""
def finalize_inventory_atomic(db: Session, order_id: int) -> list[str]:
    """Atomically finalize inventory for a paid order with oversell prevention.

    Iterates over order items and uses atomic ``UPDATE ... WHERE stock >= quantity``
    for each product. If any item has insufficient stock, collects the issues
    and returns them without modifying any rows.

    Args:
        db: Database session.
        order_id: Order whose inventory to finalize.

    Returns:
        List of issue strings (empty if all items were decremented successfully).
    """
    order_items = (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order_id)
        .all()
    )

    if not order_items:
        return []

    requested_quantities: dict[int, int] = {}
    for item in order_items:
        product_id = int(getattr(item, "product_id"))
        quantity = int(getattr(item, "quantity"))
        requested_quantities[product_id] = requested_quantities.get(product_id, 0) + quantity

    issues: list[str] = []
    insufficient_product_ids: list[int] = []

    for product_id, requested_quantity in requested_quantities.items():
        result = db.execute(
            text(
                "UPDATE commerce.products SET stock = stock - :qty, updated_at = NOW() "
                "WHERE id = :pid AND is_deleted = FALSE AND stock >= :qty"
            ),
            {"pid": product_id, "qty": requested_quantity},
        )

        if result.rowcount == 0:
            insufficient_product_ids.append(product_id)

    if insufficient_product_ids:
        # Batch-load all insufficient-stock products in a single query (avoids N+1)
        insufficient_products = {
            p.id: p
            for p in db.query(Product).filter(Product.id.in_(insufficient_product_ids)).all()
        }
        for product_id in insufficient_product_ids:
            product = insufficient_products.get(product_id)
            if product is None:
                issues.append(f"missing_product:{product_id}")
            else:
                available = int(getattr(product, "stock", 0) or 0)
                requested_qty = requested_quantities[product_id]
                issues.append(
                    f"insufficient_stock:{product.id}:available={available}:requested={requested_qty}"
                )

    if not issues:
        _bump_product_cache_version()

    return issues


