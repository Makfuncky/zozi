"""
        def _is_restricted(category_slug: str) -> bool:
            return restriction_cache.get((category_slug or "").strip().lower(), False)

        filtered_products = [prod for prod in serialized_products if not _is_restricted(prod.get("category", ""))]
        serialized_products = filtered_products

    return serialized_products, total


def get_products(
    db: Session,
    response: Optional[Response],
    q: Optional[str] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    brand: Optional[str] = None,
    brands: Optional[str] = None,
    color: Optional[str] = None,
    region: Optional[str] = None,
    supplier: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    new_arrivals: bool = False,
    best_sellers: bool = False,
    trending: bool = False,
    in_stock: bool = False,
    min_discount: Optional[int] = None,
    deals: bool = False,
    sort: Optional[str] = None,
    sale_id: Optional[int] = None,
    limit: int = 24,
    offset: int = 0,
    country_code: Optional[str] = None,
    has_video: bool = False,
    attributes: Optional[str] = None,
) -> List[Product]:
    resolved_country = country_code or region

    cache_payload = {
        "q": q,
        "category": category,
        "subcategory": subcategory,
        "brand": brand,
        "brands": brands,
        "color": color,
        "region": region,
        "supplier": supplier,
        "min_price": min_price,
        "max_price": max_price,
        "min_rating": min_rating,
        "max_rating": max_rating,
        "new_arrivals": new_arrivals,
        "best_sellers": best_sellers,
        "trending": trending,
        "in_stock": in_stock,
        "min_discount": min_discount,
        "deals": deals,
        "sort": sort,
        "sale_id": sale_id,
        "limit": limit,
        "offset": offset,
        "country_code": country_code,
        "has_video": has_video,
        "attributes": attributes,
    }
    cache_key = build_versioned_cache_key("products:listing", "list", cache_payload)

    def _compute() -> tuple[list[dict[str, Any]], int]:
        return _list_products_cached(
            db=db,
            resolved_country=resolved_country,
            q=q,
            category=category,
            subcategory=subcategory,
            brand=brand,
            brands=brands,
            color=color,
            region=region,
            supplier=supplier,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
            max_rating=max_rating,
            new_arrivals=new_arrivals,
            best_sellers=best_sellers,
            trending=trending,
            in_stock=in_stock,
            min_discount=min_discount,
            deals=deals,
            sort=sort,
            sale_id=sale_id,
            limit=limit,
            offset=offset,
            country_code=country_code,
            has_video=has_video,
            attributes=attributes,
        )

    serialized_products, total = cache_or_compute(
        key=cache_key,
        compute=_compute,
        ttl=300,
        namespace="products:listing",
    )

    if response is not None:
        response.headers["X-Total-Count"] = str(total)
        response.headers["Cache-Control"] = _PUBLIC_PRODUCTS_CACHE_CONTROL

    return cast(List[Product], serialized_products)


def create_product(product: ProductCreate, db: Session) -> Product:
    try:
        with db_query_timer("insert_product"):
            data = _prepare_product_write_payload(product.model_dump())
            data = _resolve_product_category_fields(data, db)
            data["name"] = html.escape(data["name"].strip()) if data.get("name") else data.get("name")
            if data.get("description"):
                data["description"] = html.escape(data["description"])
            db_product = Product(**data)
            db.add(db_product)
            db.commit()
        _bump_product_cache_version()
        invalidate_product_listings()
        db.refresh(db_product)
        log_service_call("products_service", "create_product", level="info", product_id=db_product.id)
        return db_product
    except Exception as exc:
        log_service_error("products_service", "create_product", exc)
        db.rollback()
        raise


def get_product(product_id: int, db: Session) -> Product:
    cache_key = _build_product_cache_key("detail", {"product_id": product_id})
    cached_payload = _cache_get_json(cache_key)
    if isinstance(cached_payload, dict):
        return cached_payload

    try:
        with db_query_timer("select_product_detail"):
            product = db.query(Product).options(selectinload(Product.variants)).filter(
                Product.id == product_id,
                Product.is_deleted == False,  # noqa: E712
            ).first()
    except Exception as exc:
        log_service_error("products_service", "get_product", exc, product_id=product_id)
        raise
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    active_sales = _get_active_flash_sales(db)
    active_sale = next((sale for sale in active_sales if product_id in _parse_flash_sale_product_ids(sale.product_ids)), None)
    global_sale = next((sale for sale in active_sales if not _parse_flash_sale_product_ids(sale.product_ids)), None)
    hydrated_product = _apply_live_offer_metadata(product, active_sale or global_sale)
    serialized_product = _serialize_product(hydrated_product)
    _cache_set_json(cache_key, serialized_product, _PRODUCT_DETAIL_CACHE_TTL)
    return serialized_product


def update_product(product_id: int, product: ProductCreate, current_user: dict, db: Session) -> Product:
    db_product = db.query(Product).filter(
        Product.id == product_id,
        Product.supplier_id == current_user["id"],
    ).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found or not authorized")
    data = _prepare_product_write_payload(product.model_dump())
    data = _resolve_product_category_fields(data, db)
    if data.get("name"):
        data["name"] = html.escape(data["name"].strip())
    if data.get("description"):
        data["description"] = html.escape(data["description"])
    for key, value in data.items():
        setattr(db_product, key, value)
    db.commit()
    _bump_product_cache_version()
    db.refresh(db_product)
    audit_log(
        db,
        action=AuditAction.PRODUCT_UPDATE,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="product",
        resource_id=product_id,
        details={"name": db_product.name},
    )
    return db_product


def delete_product(product_id: int, current_user: dict, db: Session) -> dict:
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,  # noqa: E712
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not authorized")

    product_name = str(product.name)

    # Cascade: remove from carts and wishlists
    db.query(CartItem).filter(CartItem.product_id == product_id).delete(synchronize_session=False)
    db.query(Wishlist).filter(Wishlist.product_id == product_id).delete(synchronize_session=False)

    # Cascade: soft-delete reviews
    db.query(Review).filter(
        Review.product_id == product_id,
        Review.is_deleted == False,  # noqa: E712
    ).update({"is_deleted": True}, synchronize_session=False)

    # Cascade: notify users with in-flight orders
    affected_orders = (
        db.query(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(
            OrderItem.product_id == product_id,
            Order.status.in_(["pending", "processing", "confirmed"]),
        )
        .all()
    )
    for order in affected_orders:
        db.add(Notification(
            user_id=order.user_id,
            type="system",
            title="Product Unavailable",
            message=(
                f"A product ('{product_name}') in your order #{order.id} "
                "is no longer available. Our support team will contact you."
            ),
            link=f"/orders/{order.id}",
        ))

    setattr(product, "is_deleted", True)
    db.commit()
    _bump_product_cache_version()
    audit_log(
        db,
        action=AuditAction.PRODUCT_DELETE,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="product",
        resource_id=product_id,
        details={"product_name": product_name, "orders_notified": len(affected_orders)},
    )
    return {"message": "Product deleted", "orders_notified": len(affected_orders)}


def update_product_return_window(
    product_id: int,
    days: int,
    current_user: dict,
    db: Session,
) -> dict:
    """
    Supplier sets the return window (days) for a specific product.

    Constraints:
      - Minimum: 10 days (platform minimum)
      - Maximum: supplier's max_return_days (default 30) from SupplierProfile
    """
    if days < 10:
        raise HTTPException(status_code=422, detail="Return window must be at least 10 days")

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,  # noqa: E712
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not authorized")

    # Check against supplier's configured maximum
    supplier_profile = db.query(SupplierProfile).filter(
        SupplierProfile.user_id == current_user["id"]
    ).first()
    max_days = int(supplier_profile.max_return_days) if supplier_profile and supplier_profile.max_return_days else 30
    if days > max_days:
        raise HTTPException(
            status_code=422,
            detail=f"Return window cannot exceed your configured maximum of {max_days} days",
        )

    setattr(product, "return_window_days", days)
    db.commit()
    return {"message": "Return window updated", "return_window_days": days}


_LOW_STOCK_THRESHOLD = 5


def patch_product_stock(
    product_id: int,
    delta: int,
    current_user: dict,
    db: Session,
) -> dict:
    """Adjust product stock by delta (+/-). Suppliers own their products; admins can adjust any."""
    role = current_user.get("role")

    q = db.query(Product).filter(
        Product.id == product_id,
        Product.is_deleted == False,  # noqa: E712
    )
    if role not in ("admin", "sub_admin"):
        q = q.filter(Product.supplier_id == current_user["id"])

    product = q.first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not authorized")

    current_stock = int(cast(Any, getattr(product, "stock")) or 0)
    new_stock = current_stock + delta
    if new_stock < 0:
        raise HTTPException(status_code=400, detail="Stock cannot go below 0")

    setattr(product, "stock", new_stock)
    db.commit()
    _bump_product_cache_version()

    audit_log(
        db,
        action=getattr(AuditAction, "PRODUCT_STOCK_UPDATED", AuditAction.PRODUCT_UPDATE),
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=role,
        resource_type="product",
        resource_id=product_id,
        details={"delta": delta, "new_stock": new_stock},
    )

    # Low-stock email alert to supplier (non-blocking)
    supplier_id = cast(int | None, getattr(product, "supplier_id"))
    if new_stock <= _LOW_STOCK_THRESHOLD and supplier_id:
        try:
            from domains.governance.ports import User as UserModel
            from infrastructure.utils.email_service import send_email
            supplier = db.query(UserModel).filter(UserModel.id == supplier_id).first()
            supplier_email = cast(str | None, getattr(supplier, "email")) if supplier else None
            if supplier and supplier_email:
                html_body = f"""
                <h2 style="font-family:Arial,sans-serif;color:#dc2626">Low Stock Alert</h2>
                <p style="font-family:Arial,sans-serif;color:#374151">
                  Product <strong>{product.name}</strong> (ID: {product.id}) 
                  has only <strong>{new_stock}</strong> unit(s) remaining.
                </p>
                <p style="font-family:Arial,sans-serif;color:#6b7280">
                  Please restock soon to avoid losing sales.
                </p>"""
                send_email(
                    to=supplier_email,
                    subject=f"ZOZI Low Stock Alert: {product.name}",
                    html=html_body,
                )
        except Exception as exc:
            logger.warning("Low-stock email failed (non-fatal): %s", exc)

    return {"product_id": product_id, "new_stock": new_stock, "delta": delta}


def atomic_stock_decrement(db: Session, product_id: int, quantity: int) -> bool:
    """Atomically decrement product stock if sufficient quantity exists.

    Uses a single ``UPDATE ... WHERE stock >= quantity`` statement to prevent
    oversell under concurrent requests. The database's row-level locking ensures
    that concurrent decrements are serialized — only transactions where stock is
    sufficient will succeed.

    Args:
        db: Database session.
        product_id: Product whose stock to decrement.
        quantity: Number of units to remove from stock.

    Returns:
        True if the stock was successfully decremented.

    Raises:
        HTTPException: 409 if insufficient stock (oversell prevented).
        HTTPException: 404 if product not found.
    """
    if quantity <= 0:
        return True

    result = db.execute(
        text(
            "UPDATE commerce.products SET stock = stock - :qty, updated_at = NOW() "
            "WHERE id = :pid AND is_deleted = FALSE AND stock >= :qty"
        ),
        {"pid": product_id, "qty": quantity},
    )

    if result.rowcount == 0:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product is None:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        available = int(getattr(product, "stock", 0) or 0)
        raise HTTPException(
            status_code=409,
            detail=f"Insufficient stock for product {product_id}. Available: {available}, Requested: {quantity}",
        )

    return True


