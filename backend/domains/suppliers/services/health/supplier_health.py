"""Supplier sub-module — imports shared helpers from supplier_shared."""

from domains.suppliers.services.supplier_shared import *
from domains.suppliers.services.supplier_shared import _build_public_supplier_cache_key
from infrastructure.utils.cache import cache_get_json

def get_supplier_analytics(period: str, current_user: dict, db: Session) -> dict:
    day_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days = day_map.get(period, 30)

    start_date = utcnow() - timedelta(days=days)
    previous_start_date = start_date - timedelta(days=days)
    sid = current_user["id"]

    total_revenue = db.query(
        func.sum(OrderItem.price * OrderItem.quantity)
    ).join(Order).join(Product).filter(
        Product.supplier_id == sid,
        Order.created_at >= start_date,
    ).scalar() or 0

    total_orders = db.query(Order).join(OrderItem).join(Product).filter(
        Product.supplier_id == sid,
        Order.created_at >= start_date,
    ).distinct().count()

    total_products = db.query(Product).filter(Product.supplier_id == sid).count()
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

    prev_revenue = db.query(
        func.sum(OrderItem.price * OrderItem.quantity)
    ).join(Order).join(Product).filter(
        Product.supplier_id == sid,
        Order.created_at >= previous_start_date,
        Order.created_at < start_date,
    ).scalar() or 0

    prev_orders = db.query(Order).join(OrderItem).join(Product).filter(
        Product.supplier_id == sid,
        Order.created_at >= previous_start_date,
        Order.created_at < start_date,
    ).distinct().count()

    revenue_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
    order_growth = ((total_orders - prev_orders) / prev_orders * 100) if prev_orders > 0 else 0

    # Single grouped query replaces N+1 per-day queries
    daily_rows = db.query(
        func.date(Order.created_at).label("date"),
        func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
    ).join(OrderItem, OrderItem.order_id == Order.id).join(Product, Product.id == OrderItem.product_id).filter(
        Product.supplier_id == sid,
        Order.created_at >= start_date,
    ).group_by(func.date(Order.created_at)).limit(1000).all()
    revenue_by_date = {str(row.date): float(row.revenue) for row in daily_rows}
    daily_revenue = [
        {
            "date": (start_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "revenue": revenue_by_date.get(
                (start_date + timedelta(days=i)).strftime("%Y-%m-%d"), 0.0
            ),
        }
        for i in range(days)
    ]

    top_selling = db.query(
        Product.id,
        Product.name,
        Product.image_url,
        func.count(OrderItem.id).label("sales"),
        func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
    ).join(OrderItem).join(Order).filter(
        Product.supplier_id == sid,
        Order.created_at >= start_date,
    ).group_by(Product.id, Product.name, Product.image_url).order_by(
        func.sum(OrderItem.price * OrderItem.quantity).desc()
    ).limit(10).all()

    product_performance = []
    for product in db.query(Product).filter(Product.supplier_id == sid).limit(10).all():
        sales_data = db.query(
            func.count(OrderItem.id),
            func.sum(OrderItem.price * OrderItem.quantity),
        ).filter(OrderItem.product_id == product.id).first()
        views = (sales_data[0] or 0) * 10 + 50
        purchases = sales_data[0] or 0
        conversion = (purchases / views * 100) if views > 0 else 0
        product_performance.append({
            "id": product.id,
            "name": product.name,
            "views": views,
            "purchases": purchases,
            "conversion": conversion,
        })

    total_views = sum(p["views"] for p in product_performance)
    conversion_rate = (total_orders / total_views * 100) if total_views > 0 else 0

    return {
        "overview": {
            "totalRevenue": float(total_revenue),
            "totalOrders": total_orders,
            "totalProducts": total_products,
            "averageOrderValue": float(avg_order_value),
            "conversionRate": conversion_rate,
        },
        "revenue": {"daily": daily_revenue, "monthly": [], "yearly": []},
        "products": {
            "topSelling": [
                {
                    "id": p.id,
                    "name": p.name,
                    "sales": p.sales,
                    "revenue": float(p.revenue),
                    "image_url": p.image_url,
                }
                for p in top_selling
            ],
            "performance": product_performance,
        },
        "trends": {
            "revenueGrowth": revenue_growth,
            "orderGrowth": order_growth,
            "customerGrowth": 0,
            "period": period,
        },
    }


# ── Inventory ─────────────────────────────────────────────────────────────────

def get_supplier_inventory(current_user: dict, db: Session) -> list:
    products = db.query(Product).filter(
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,  # noqa: E712
    ).limit(1000).all()
    result = []
    for product in products:
        thirty_days_ago = utcnow() - timedelta(days=30)
        sales_data = db.query(
            func.sum(OrderItem.quantity).label("total_sold"),
            func.count(OrderItem.id).label("order_count"),
        ).join(Order).filter(
            OrderItem.product_id == product.id,
            Order.created_at >= thirty_days_ago,
        ).first()

        total_sold = sales_data.total_sold or 0
        sales_velocity = total_sold / 30.0
        reorder_point = int(sales_velocity * 7)

        result.append({
            "id": product.id,
            "name": product.name,
            "current_stock": product.stock,
            "minimum_stock": max(reorder_point, 5),
            "maximum_stock": max(reorder_point * 3, 50),
            "category": product.category or "General",
            "supplier_price": product.price,
            "last_updated": (product.updated_at or product.created_at).isoformat(),
            "sales_velocity": sales_velocity,
            "reorder_point": reorder_point,
        })
    return result


def update_product_stock(product_id: int, stock_update: dict, current_user: dict, db: Session) -> dict:
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.supplier_id == current_user["id"],
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or doesn't belong to this supplier")
    new_stock = stock_update.get("stock_quantity", product.stock)
    if new_stock is None or new_stock < 0:
        raise HTTPException(status_code=400, detail="Stock quantity cannot be negative")
    product.stock = int(new_stock)
    db.commit()
    _bump_product_cache_version()
    db.refresh(product)
    return {"message": "Stock updated successfully", "product": {"id": product.id, "name": product.name, "stock": product.stock}}


def update_inventory_levels(product_id: int, levels_update: dict, current_user: dict, db: Session) -> dict:
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.supplier_id == current_user["id"],
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or doesn't belong to this supplier")
    min_stock = levels_update.get("minimum_stock")
    max_stock = levels_update.get("maximum_stock")
    if min_stock is not None and min_stock < 0:
        raise HTTPException(status_code=400, detail="Minimum stock cannot be negative")
    if max_stock is not None and max_stock < 0:
        raise HTTPException(status_code=400, detail="Maximum stock cannot be negative")
    if min_stock is not None and max_stock is not None and min_stock > max_stock:
        raise HTTPException(status_code=400, detail="Minimum stock cannot be greater than maximum stock")
    if min_stock is not None:
        product.minimum_stock = int(min_stock)
    if max_stock is not None:
        product.maximum_stock = int(max_stock)
    if min_stock is not None or max_stock is not None:
        db.commit()
        _bump_product_cache_version()
        db.refresh(product)
    return {"message": "Inventory levels updated successfully", "minimum_stock": product.minimum_stock, "maximum_stock": product.maximum_stock}


def get_inventory_alerts(current_user: dict, db: Session) -> dict:
    products = db.query(Product).filter(
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,  # noqa: E712
    ).limit(1000).all()
    alerts = []
    for product in products:
        thirty_days_ago = utcnow() - timedelta(days=30)
        sales_data = db.query(func.sum(OrderItem.quantity)).join(Order).filter(
            OrderItem.product_id == product.id,
            Order.created_at >= thirty_days_ago,
        ).scalar() or 0

        sales_velocity = sales_data / 30.0
        reorder_point = int(sales_velocity * 7)

        if product.stock <= reorder_point and product.stock > 0:
            alerts.append({
                "type": "low_stock",
                "product_id": product.id,
                "product_name": product.name,
                "current_stock": product.stock,
                "reorder_point": reorder_point,
                "sales_velocity": sales_velocity,
                "message": f"Low stock alert: {product.name} has {product.stock} units remaining",
            })
        elif product.stock == 0:
            alerts.append({
                "type": "out_of_stock",
                "product_id": product.id,
                "product_name": product.name,
                "current_stock": 0,
                "reorder_point": reorder_point,
                "sales_velocity": sales_velocity,
                "message": f"Out of stock: {product.name} needs restocking",
            })
        elif product.stock > reorder_point * 3:
            alerts.append({
                "type": "overstock",
                "product_id": product.id,
                "product_name": product.name,
                "current_stock": product.stock,
                "reorder_point": reorder_point,
                "sales_velocity": sales_velocity,
                "message": f"Overstock alert: {product.name} has excess inventory ({product.stock} units)",
            })

    return {"alerts": alerts, "total_alerts": len(alerts)}


# ── Profile ───────────────────────────────────────────────────────────────────

def get_supplier_profile(current_user: dict, db: Session) -> dict:
    supplier = db.query(User).filter(User.id == current_user["id"]).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    from domains.comms.ports import SupplierProfile as SP
    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()

    total_products = db.query(Product).filter(Product.supplier_id == current_user["id"]).count()
    total_orders = (
        db.query(Order).join(OrderItem).join(Product)
        .filter(Product.supplier_id == current_user["id"])
        .distinct()
        .count()
    )
    total_revenue = db.query(
        func.sum(OrderItem.price * OrderItem.quantity)
    ).join(Order).join(Product).filter(
        Product.supplier_id == current_user["id"],
        Order.status == "completed",
    ).scalar() or 0

    return {
        "id": supplier.id,
        "username": supplier.username,
        "email": supplier.email,
        "phone": supplier.phone,
        "business_name": profile.business_name if profile else None,
        "business_address": profile.address if profile else None,
        "website": profile.website if profile else None,
        "bio": profile.bio if profile else None,
        "about_us": getattr(profile, "about_us", None) if profile else None,
        "verification_status": profile.verification_status if profile else "pending",
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": float(total_revenue),
        "created_at": supplier.created_at.isoformat(),
    }


def update_supplier_profile(profile_update: dict, current_user: dict, db: Session) -> dict:
    supplier = db.query(User).filter(User.id == current_user["id"]).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    from domains.comms.ports import SupplierProfile as SP
    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    if not profile:
        profile = SP(user_id=current_user["id"], verification_status="pending")
        db.add(profile)

    if "phone" in profile_update:
        supplier.phone = _sanitize_profile_string(profile_update.get("phone"))

    profile_field_map = {
        "business_name": "business_name",
        "business_address": "address",
        "website": "website",
        "bio": "bio",
        "about_us": "about_us",
        "business_type": "business_type",
    }
    for source_field, target_field in profile_field_map.items():
        if source_field not in profile_update:
            continue
        value = profile_update.get(source_field)
        if target_field == "website" and isinstance(value, str) and value.strip() and not value.startswith(("http://", "https://")):
            value = f"https://{value.strip()}"
        setattr(profile, target_field, _sanitize_profile_string(value))

    if "established_year" in profile_update:
        raw_year = profile_update.get("established_year")
        if raw_year in (None, ""):
            profile.established_year = None
        else:
            try:
                profile.established_year = int(raw_year)
            except (TypeError, ValueError) as exc:
                raise HTTPException(status_code=400, detail="Established year must be a number") from exc

    db.commit()
    db.refresh(supplier)
    return get_supplier_profile(current_user, db)


def request_verification(current_user: dict, db: Session) -> dict:
    supplier = db.query(User).filter(User.id == current_user["id"]).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    from domains.comms.ports import SupplierProfile as SP
    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    if not profile:
        profile = SP(user_id=current_user["id"], verification_status="pending")
        db.add(profile)

    if profile.verification_status in (None, "pending"):
        profile.verification_status = "under_review"
    db.commit()
    return {"message": "Verification request submitted successfully", "status": profile.verification_status or "pending"}


# ── Payouts ───────────────────────────────────────────────────────────────────

def get_payout_history(current_user: dict, db: Session) -> list:
    payouts = (
        db.query(Payout)
        .filter(Payout.supplier_id == current_user["id"])
        .order_by(Payout.created_at.desc())
        .limit(1000)
        .all()
    )
    return [
        {
            "id": p.id,
            "amount": p.amount,
            "status": p.status,
            "method": p.method,
            "reference": p.reference_id,
            "notes": p.notes,
            "created_at": p.created_at.isoformat(),
            "processed_at": p.processed_at.isoformat() if p.processed_at else None,
        }
        for p in payouts
    ]


def get_supplier_shipments(current_user: dict, db: Session) -> list:
    """Compatibility endpoint for mobile supplier logistics list."""
    supplier_id = current_user["id"]
    shipments = (
        db.query(Shipment)
        .filter(Shipment.supplier_id == supplier_id)
        .order_by(Shipment.created_at.desc())
        .limit(1000)
        .all()
    )
    return [
        {
            "id": s.id,
            "order_id": s.order_id,
            "tracking_number": s.tracking_number,
            "carrier": s.carrier_name or (s.carrier.name if s.carrier else None),
            "status": s.status,
            "distribution_channel": s.distribution_channel,
            "current_hub": s.current_hub,
            "scan_code": s.scan_code,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in shipments
    ]


def request_payout(body: dict, current_user: dict, db: Session) -> dict:
    amount = body.get("amount")
    method = body.get("method", "bank")
    notes = body.get("notes")
    if not amount or float(amount) <= 0:
        raise HTTPException(status_code=422, detail="Amount must be positive")
    payout = Payout(
        supplier_id=current_user["id"],
        amount=float(amount),
        method=method,
        notes=notes,
        country_code=current_user.get("country_code") or current_user.get("preferred_country") or None,
    )
    db.add(payout)
    db.flush()
    payout.reference_id = build_transfer_reference(
        db,
        kind="supplier_payout",
        entity_id=int(current_user["id"]),
        record_id=int(payout.id),
    )
    db.add(
        Notification(
            user_id=current_user["id"],
            type="payout",
            title="Payout Request Received",
            message=f"Your payout request of {amount} AED has been submitted and is under review.",
            link="/supplier/payouts",
        )
    )
    db.commit()
    db.refresh(payout)
    audit_log(
        db=db,
        action=AuditAction.PAYOUT_REQUESTED,
        user_id=current_user["id"],
        username=current_user["username"],
        user_role=current_user["role"],
        resource_type="payout",
        resource_id=payout.id,
        details={"amount": float(amount), "method": method},
    )
    return {
        "id": payout.id,
        "status": payout.status,
        "amount": payout.amount,
        "method": payout.method,
        "reference": payout.reference_id,
        "notes": payout.notes,
        "created_at": payout.created_at.isoformat() if payout.created_at else None,
        "processed_at": payout.processed_at.isoformat() if payout.processed_at else None,
    }


# ── Bulk Operations ───────────────────────────────────────────────────────────

def execute_bulk_operation(operation: dict, current_user: dict, db: Session) -> dict:
    operation_type = operation.get("type")
    product_ids = operation.get("productIds", [])
    value = operation.get("value")

    if not product_ids:
        raise HTTPException(status_code=400, detail="No products selected")

    products = db.query(Product).filter(
        Product.id.in_(product_ids),
        Product.supplier_id == current_user["id"],
    ).limit(1000).all()
    if len(products) != len(product_ids):
        raise HTTPException(status_code=404, detail="Some products not found or don't belong to this supplier")

    updated_count = 0
    if operation_type == "price_update":
        if value is None or value < 0:
            raise HTTPException(status_code=400, detail="Invalid price value")
        for product in products:
            product.price = float(value)
        updated_count = len(products)
    elif operation_type == "category_change":
        if not value or not isinstance(value, str):
            raise HTTPException(status_code=400, detail="Invalid category value")
        for product in products:
            product.category = value
        updated_count = len(products)
    elif operation_type == "stock_update":
        if value is None or value < 0:
            raise HTTPException(status_code=400, detail="Invalid stock value")
        for product in products:
            product.stock = int(value)
        updated_count = len(products)
    elif operation_type == "status_change":
        # value may be bool, 0/1, "active"/"inactive"
        if value is None:
            raise HTTPException(status_code=400, detail="value is required for status_change (true/false or 'active'/'inactive')")
        if isinstance(value, bool):
            target_active = value
        elif isinstance(value, (int, float)):
            target_active = bool(value)
        elif isinstance(value, str):
            if value.lower() in ("true", "active", "1"):
                target_active = True
            elif value.lower() in ("false", "inactive", "0"):
                target_active = False
            else:
                raise HTTPException(status_code=400, detail="value must be true/false or 'active'/'inactive'")
        else:
            raise HTTPException(status_code=400, detail="Invalid value for status_change")
        for product in products:
            product.is_active = target_active
        updated_count = len(products)
    elif operation_type == "delete":
        for product in products:
            product.is_deleted = True
        updated_count = len(products)
    else:
        raise HTTPException(status_code=400, detail="Invalid operation type")

    db.commit()
    _bump_product_cache_version()
    return {
        "message": f"Bulk {operation_type.replace('_', ' ')} completed successfully",
        "updated_count": updated_count,
        "operation_type": operation_type,
    }


def bulk_inventory_adjust(adjustments: list, current_user: dict, db: Session) -> dict:
    """Bulk adjust stock for multiple products in one request.

    Each entry in `adjustments` must be:
        {"product_id": int, "mode": "set" | "adjust", "value": int}

    ``mode="set"``    → set stock to exactly `value` (must be >= 0).
    ``mode="adjust"`` → add/subtract `value` from current stock (result clamped to 0).
    """
    if current_user["role"] not in ("supplier", "admin", "sub_admin"):
        raise HTTPException(status_code=403, detail="Supplier access required")
    if not adjustments:
        raise HTTPException(status_code=400, detail="No adjustments provided")
    if len(adjustments) > 200:
        raise HTTPException(status_code=400, detail="Cannot adjust more than 200 products at once")

    product_ids = []
    for entry in adjustments:
        pid = entry.get("product_id")
        if not isinstance(pid, int) or pid <= 0:
            raise HTTPException(status_code=422, detail=f"Invalid product_id: {pid}")
        product_ids.append(pid)

    products_map: dict[int, Product] = {
        cast(int, p.id): p
        for p in db.query(Product).filter(
            Product.id.in_(product_ids),
            Product.supplier_id == current_user["id"],
            Product.is_deleted == False,  # noqa: E712
        ).limit(1000).all()
    }

    updated: list[dict] = []
    skipped: list[dict] = []

    for entry in adjustments:
        pid = int(entry["product_id"])
        mode = str(entry.get("mode", "set")).lower()
        raw_value = entry.get("value")

        product = products_map.get(pid)
        if not product:
            skipped.append({"product_id": pid, "reason": "Not found or not owned by this supplier"})
            continue

        try:
            delta = int(raw_value)
        except (TypeError, ValueError):
            skipped.append({"product_id": pid, "reason": f"Invalid value: {raw_value}"})
            continue

        if mode == "set":
            if delta < 0:
                skipped.append({"product_id": pid, "reason": "Stock cannot be set to a negative value"})
                continue
            old_stock = int(product.stock or 0)
            product.stock = delta
        elif mode == "adjust":
            old_stock = int(product.stock or 0)
            new_stock = max(0, old_stock + delta)
            product.stock = new_stock
        else:
            skipped.append({"product_id": pid, "reason": f"Unknown mode '{mode}'. Use 'set' or 'adjust'"})
            continue

        updated.append({
            "product_id": pid,
            "product_name": product.name,
            "old_stock": old_stock,
            "new_stock": product.stock,
            "mode": mode,
        })

    if updated:
        db.commit()
        _bump_product_cache_version()
        audit_log(
            db=db,
            action=AuditAction.PRODUCT_UPDATE,
            user_id=current_user["id"],
            username=current_user["username"],
            user_role=current_user["role"],
            resource_type="product",
            resource_id=0,
            details={"bulk_stock_adjust": True, "count": len(updated), "adjustments": updated},
        )
    return {
        "updated": len(updated),
        "skipped": len(skipped),
        "details": updated,
        "skipped_details": skipped,
    }


def export_products_csv(current_user: dict, db: Session) -> StreamingResponse:
    products = db.query(Product).filter(
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,  # noqa: E712
    ).limit(1000).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Description", "Price", "Stock Quantity", "Category", "Status", "Image URL", "Created At"])
    for product in products:
        writer.writerow([
            product.id,
            product.name,
            product.description or "",
            product.price,
            product.stock,
            product.category or "",
            "active",
            product.image_url or "",
            product.created_at.isoformat() if product.created_at else "",
        ])
    csv_content = output.getvalue()
    output.close()

    def iter_csv():
        yield csv_content

    return StreamingResponse(
        iter_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=products_export.csv"},
    )


async def import_products_csv(file: UploadFile, current_user: dict, db: Session) -> dict:
    if not (file.filename or "").endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV file")

    content = await file.read()
    from infrastructure.utils.file_validation import validate_csv_bytes
    validate_csv_bytes(content, file.filename or "")
    csv_content = content.decode("utf-8")
    csv_reader = csv.DictReader(io.StringIO(csv_content))

    imported_count = 0
    errors = []

    for row_num, row in enumerate(csv_reader, start=2):
        try:
            if not row.get("Name"):
                errors.append(f"Row {row_num}: Missing product name")
                continue
            if not row.get("Price"):
                errors.append(f"Row {row_num}: Missing price")
                continue
            raw_name = row["Name"].strip()
            raw_desc = row.get("Description", "").strip()
            raw_cat = row.get("Category", "").strip()
            # Generate unique slug for the product
            slug_base = re.sub(r"[^a-z0-9]+", "-", raw_name.lower()).strip("-") or "product"
            product_slug = slug_base
            attempt = 0
            while db.query(Product).filter(Product.slug == product_slug).first():
                attempt += 1
                product_slug = f"{slug_base}-{attempt}"
            new_product = Product(
                name=html.escape(raw_name),
                slug=product_slug,
                description=html.escape(raw_desc) if raw_desc else None,
                price=float(row["Price"]),
                stock=int(row.get("Stock Quantity", 0)),
                category=html.escape(raw_cat) if raw_cat else None,
                image_url=None,  # never accept image_url from CSV (SSRF risk)
                supplier_id=current_user["id"],
            )
            db.add(new_product)
            imported_count += 1
        except ValueError as e:
            errors.append(f"Row {row_num}: Invalid data - {str(e)}")
        except Exception as e:
            errors.append(f"Row {row_num}: Error - {str(e)}")

    db.commit()
    if imported_count:
        _bump_product_cache_version()
    return {
        "message": f"Import completed. {imported_count} products imported successfully.",
        "imported_count": imported_count,
        "errors": errors,
    }


# ── Reports ───────────────────────────────────────────────────────────────────

def get_supplier_reports(period: str, current_user: dict, db: Session) -> dict:
    now = utcnow()
    day_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days = day_map.get(period, 30)
    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days)

    supplier_products = db.query(Product).filter(Product.supplier_id == current_user["id"]).limit(1000).all()
    product_ids = [p.id for p in supplier_products]

    total_revenue = db.query(
        func.sum(OrderItem.price * OrderItem.quantity)
    ).join(Order).filter(
        OrderItem.product_id.in_(product_ids),
        Order.created_at >= start_date,
        Order.status.in_(["completed", "shipped", "delivered"]),
    ).scalar() or 0

    total_orders = db.query(func.count(func.distinct(Order.id))).join(OrderItem).filter(
        OrderItem.product_id.in_(product_ids),
        Order.created_at >= start_date,
        Order.status.in_(["completed", "shipped", "delivered"]),
    ).scalar() or 0

    total_products = len(supplier_products)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    conversion_rate = (total_orders / total_products * 100) if total_products > 0 else 0

    revenue_trends = db.query(
        func.date(Order.created_at).label("date"),
        func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
    ).join(Order).filter(
        OrderItem.product_id.in_(product_ids),
        Order.created_at >= start_date,
        Order.status.in_(["completed", "shipped", "delivered"]),
    ).group_by(func.date(Order.created_at)).order_by(func.date(Order.created_at)).all()

    top_products = db.query(
        Product.name,
        Product.id,
        Product.image_url,
        func.sum(OrderItem.quantity).label("sales"),
        func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
    ).join(OrderItem).join(Order).filter(
        Product.supplier_id == current_user["id"],
        Order.created_at >= start_date,
        Order.status.in_(["completed", "shipped", "delivered"]),
    ).group_by(Product.id, Product.name, Product.image_url).order_by(
        func.sum(OrderItem.price * OrderItem.quantity).desc()
    ).limit(10).all()

    product_performance = []
    for product in supplier_products[:10]:
        purchases = db.query(func.sum(OrderItem.quantity)).join(Order).filter(
            OrderItem.product_id == product.id,
            Order.created_at >= start_date,
            Order.status.in_(["completed", "shipped", "delivered"]),
        ).scalar() or 0
        views = purchases * 2
        conversion = (purchases / views * 100) if views > 0 else 0
        product_performance.append({
            "id": product.id,
            "name": product.name,
            "views": views,
            "purchases": purchases,
            "conversion": conversion,
        })

    prev_period_start = start_date - (now - start_date)
    prev_revenue = db.query(
        func.sum(OrderItem.price * OrderItem.quantity)
    ).join(Order).filter(
        OrderItem.product_id.in_(product_ids),
        Order.created_at >= prev_period_start,
        Order.created_at < start_date,
        Order.status.in_(["completed", "shipped", "delivered"]),
    ).scalar() or 0

    prev_orders = db.query(func.count(func.distinct(Order.id))).join(OrderItem).filter(
        OrderItem.product_id.in_(product_ids),
        Order.created_at >= prev_period_start,
        Order.created_at < start_date,
        Order.status.in_(["completed", "shipped", "delivered"]),
    ).scalar() or 0

    revenue_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
    order_growth = ((total_orders - prev_orders) / prev_orders * 100) if prev_orders > 0 else 0

    current_customers = db.query(func.count(func.distinct(Order.user_id))).join(OrderItem).filter(
        OrderItem.product_id.in_(product_ids),
        Order.created_at >= start_date,
        Order.status.in_(["completed", "shipped", "delivered"]),
    ).scalar() or 0

    prev_customers = db.query(func.count(func.distinct(Order.user_id))).join(OrderItem).filter(
        OrderItem.product_id.in_(product_ids),
        Order.created_at >= prev_period_start,
        Order.created_at < start_date,
        Order.status.in_(["completed", "shipped", "delivered"]),
    ).scalar() or 0

    customer_growth = ((current_customers - prev_customers) / prev_customers * 100) if prev_customers > 0 else 0

    return {
        "overview": {
            "totalRevenue": float(total_revenue),
            "totalOrders": total_orders,
            "totalProducts": total_products,
            "averageOrderValue": float(avg_order_value),
            "conversionRate": float(conversion_rate),
        },
        "revenue": {
            "daily": [{"date": str(r.date), "revenue": float(r.revenue)} for r in revenue_trends],
            "monthly": [],
            "yearly": [],
        },
        "products": {
            "topSelling": [
                {"id": p.id, "name": p.name, "sales": p.sales, "revenue": float(p.revenue), "image_url": p.image_url}
                for p in top_products
            ],
            "performance": product_performance,
        },
        "trends": {
            "revenueGrowth": float(revenue_growth),
            "orderGrowth": float(order_growth),
            "customerGrowth": float(customer_growth),
            "period": period,
        },
        "aiAudit": _load_supplier_ai_audit_summary(),
    }


# ── Bulk Image/Details Upload ─────────────────────────────────────────────────

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_BULK_PRODUCTS = 50
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


async def bulk_upload_products(
    products_json: str,
    images: List[UploadFile],
    use_ai: bool,
    current_user: dict,
    db: Session,
) -> dict:
    """
    Bulk-create multiple products at once, with optional AI enrichment.

    products_json: JSON array string of product objects.
      Each object: { name, price, stock, category?, description?, brand?, color? }
    images: list of UploadFile — matched to products by filename or index
      (filename should match product name or be indexed p0.jpg, p1.jpg …)
    use_ai: if True, call AI service to suggest category, tags, and description
            for each product that does not already have them.
    """
    # ── parse product list ──
    try:
        raw_products: list = json.loads(products_json)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="products_json must be a valid JSON array")

    if not isinstance(raw_products, list) or not raw_products:
        raise HTTPException(status_code=400, detail="products_json must be a non-empty JSON array")

    if len(raw_products) > MAX_BULK_PRODUCTS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_BULK_PRODUCTS} products per bulk upload",
        )

    # ── build upload map (filename → content metadata) ──
    from infrastructure.utils.file_validation import VIDEO_EXTENSIONS, _sniff_image_type, validate_upload_video

    upload_map: dict[str, dict[str, object]] = {}
    primary_image_keys: list[str] = []
    for img in images:
        if not img or not img.filename:
            continue
        ext = os.path.splitext(img.filename)[1].lower()
        is_video = ext in VIDEO_EXTENSIONS or (img.content_type or "").startswith("video/")
        if ext not in ALLOWED_IMAGE_EXTS and not is_video:
            continue
        content = img.file.read()
        if len(content) > (25 * 1024 * 1024 if is_video else MAX_IMAGE_SIZE):
            continue  # skip oversized images silently; will log
        if is_video:
            try:
                normalized_ext = validate_upload_video(content, img.filename or "bulk-media.mp4")
            except HTTPException:
                continue
        else:
            # Reject files that don't match a known image magic signature
            if _sniff_image_type(content) is None:
                continue
            normalized_ext = ext or ".jpg"
        key = img.filename.lower()
        upload_map[key] = {"content": content, "ext": normalized_ext, "is_video": is_video}
        if not is_video:
            primary_image_keys.append(key)

    created: list[dict] = []
    errors: list[dict] = []

    for idx, item in enumerate(raw_products):
        if not isinstance(item, dict):
            errors.append(_build_bulk_upload_error(idx, "Item must be an object"))
            continue

        name = str(item.get("name", "")).strip()
        if not name:
            errors.append(_build_bulk_upload_error(idx, "name is required"))
            continue

        try:
            price = float(item.get("price", 0))
        except (TypeError, ValueError):
            errors.append(_build_bulk_upload_error(idx, "price must be a number", name=name))
            continue

        if price <= 0:
            errors.append(_build_bulk_upload_error(idx, "price must be > 0", name=name))
            continue

        try:
            stock = int(item.get("stock", 0))
        except (TypeError, ValueError):
            stock = 0

        description = html.escape(str(item.get("description", "")).strip())
        category = str(item.get("category", "")).strip()
        subcategory = _normalize_optional_product_text(item.get("subcategory", item.get("sub_category")))
        brand = str(item.get("brand", "")).strip() or None
        color = str(item.get("color", "")).strip() or None
        raw_tags = item.get("tags", "")
        tags_str = (", ".join(raw_tags) if isinstance(raw_tags, list) else str(raw_tags)).strip() or None
        # Variant / spec fields
        sizes_val = item.get("sizes")
        sizes_str: Optional[str] = json.dumps(sizes_val) if isinstance(sizes_val, list) else (str(sizes_val) if sizes_val else None)
        materials_str: Optional[str] = str(item.get("materials", "")).strip() or None
        weight_val = item.get("weight")
        try:
            weight_float: Optional[float] = float(weight_val) if weight_val else None
        except (TypeError, ValueError):
            weight_float = None
        dimensions_str: Optional[str] = str(item.get("dimensions", "")).strip() or None
        normalized_visibility_regions = _normalize_product_visibility_regions(item.get("visibility_regions"))
        compare_price_value = item.get("compare_price", item.get("discount_price"))
        try:
            compare_price_float: Optional[float] = float(compare_price_value) if compare_price_value not in (None, "") else None
        except (TypeError, ValueError):
            errors.append(_build_bulk_upload_error(idx, "compare_price must be a number", name=name))
            continue
        try:
            discount_starts_at_value = _parse_optional_datetime(item.get("discount_starts_at"))
            discount_ends_at_value = _parse_optional_datetime(item.get("discount_ends_at"))
            return_window_days_value = _parse_supplier_return_window_days(
                item.get("return_window_days"),
                supplier_id=current_user["id"],
                db=db,
            )
            video_url_value = _normalize_product_video_reference(item.get("video_url"))
            parsed_variants = _parse_product_variants_payload(item.get("variants"))
        except HTTPException as exc:
            errors.append(_build_bulk_upload_error(idx, exc.detail, name=name))
            continue
        is_active = _coerce_optional_bool(item.get("is_active"), True)
        # Web URL or server-relative path for main image (alternative to file upload)
        item_image_url: Optional[str] = str(item.get("image_url", "")).strip() or None
        if item_image_url and not item_image_url.startswith(("http://", "https://", "uploads/")):
            item_image_url = None
        # Additional image URLs — accept full http(s) URLs or server-relative "uploads/" paths
        extra_urls_raw = item.get("additional_image_urls", [])
        extra_url_list: list = [
            u for u in (extra_urls_raw if isinstance(extra_urls_raw, list) else [])
            if isinstance(u, str) and (u.startswith(("http://", "https://")) or u.startswith("uploads/"))
        ]

        from infrastructure.utils.storage import storage as _storage

        # Extra image files uploaded with naming convention p{idx}_e{i}.ext
        for extra_i in range(19):
            for ext_try in [".jpg", ".jpeg", ".png", ".webp", ".mp4", ".webm"]:
                ekey = f"p{idx}_e{extra_i}{ext_try}"
                entry = upload_map.get(ekey)
                if entry:
                    try:
                        saved_ext = str(entry["ext"])
                        efname = f"{uuid.uuid4().hex}{saved_ext}"
                        extra_url = _storage.save(efname, entry["content"])
                        extra_url_list.append(extra_url)
                    except Exception as exc:
                        logger.warning("Failed to save extra image %s: %s", ekey, exc)
                    break  # found this slot, move to next index

        for video_ext in [".mp4", ".webm"]:
            video_key = f"p{idx}_video{video_ext}"
            video_entry = upload_map.get(video_key)
            if not video_entry:
                continue
            try:
                saved_ext = str(video_entry["ext"])
                video_filename = f"{uuid.uuid4().hex}{saved_ext}"
                video_url_value = _storage.save(video_filename, video_entry["content"])
            except Exception as exc:
                logger.warning("Failed to save product video %s: %s", video_key, exc)
            break

        for variant_index, variant_payload in enumerate(parsed_variants):
            if variant_payload.get("media_url"):
                continue
            for media_ext in [".jpg", ".jpeg", ".png", ".webp", ".mp4", ".webm"]:
                media_key = f"p{idx}_v{variant_index}{media_ext}"
                media_entry = upload_map.get(media_key)
                if not media_entry:
                    continue
                try:
                    saved_ext = str(media_entry["ext"])
                    variant_filename = f"{uuid.uuid4().hex}{saved_ext}"
                    variant_payload["media_url"] = _storage.save(variant_filename, media_entry["content"])
                except Exception as exc:
                    logger.warning("Failed to save variant media %s: %s", media_key, exc)
                break

        # ── resolve image for this product ──
        img_bytes: Optional[bytes] = None
        matched_image_key: Optional[str] = None
        # Try: index key p0.jpg/p1.jpg, then name-based match, then position
        for key in [f"p{idx}.jpg", f"p{idx}.jpeg", f"p{idx}.png", f"p{idx}.webp",
                    f"{name.lower().replace(' ', '_')}.jpg",
                    f"{name.lower().replace(' ', '_')}.jpeg",
                    f"{name.lower().replace(' ', '_')}.png",
                    f"{name.lower().replace(' ', '_')}.webp"]:
            entry = upload_map.get(key)
            if entry and not bool(entry["is_video"]):
                img_bytes = entry["content"]
                matched_image_key = key
                break
        # positional fallback — only when no URL was supplied for this product
        if img_bytes is None and item_image_url is None and idx < len(primary_image_keys):
            matched_image_key = primary_image_keys[idx]
            img_bytes = upload_map[matched_image_key]["content"]

        # ── AI enrichment ──
        ai_description: Optional[str] = None
        if use_ai:
            try:
                from providers.ai import ai_service

                suggested_cat = ai_service.suggest_category(name, description)
                if not category:
                    category = suggested_cat
                suggested_tags = ai_service.suggest_tags(name, category, description)
                if not tags_str:
                    tags_str = ", ".join(suggested_tags)
                ai_description = ai_service.generate_product_description(
                    name=name, category=category, image_bytes=img_bytes
                )
                if not description:
                    description = ai_description
            except Exception as exc:
                logger.warning("AI enrichment failed for product %r: %s", name, exc)

        # ── save image file ──
        image_url: Optional[str] = None
        if img_bytes:
            try:
                ext = ".jpg"
                if matched_image_key:
                    ext = str(upload_map[matched_image_key]["ext"])
                filename = f"{uuid.uuid4().hex}{ext}"
                image_url = _storage.save(filename, img_bytes)
            except Exception as exc:
                logger.warning("Failed to save image for %r: %s", name, exc)
        # Fall back to web URL if no file image was saved
        if not image_url and item_image_url:
            image_url = item_image_url

        # Merge file-uploaded extra images from image_map with extra URL list
        additional_images_combined: list = list(extra_url_list)

        # ── create product ──
        try:
            product = _persist_supplier_product(
                name=name,
                description=description or "",
                price=round(price, 2),
                stock_quantity=max(0, stock),
                category=category or "General",
                subcategory=subcategory,
                color=color,
                brand=brand,
                tags=tags_str,
                sizes=sizes_str,
                materials=materials_str,
                visibility_regions=normalized_visibility_regions,
                weight=weight_float,
                dimensions=dimensions_str,
                compare_price=compare_price_float,
                discount_starts_at=discount_starts_at_value,
                discount_ends_at=discount_ends_at_value,
                return_window_days=return_window_days_value,
                is_active=is_active,
                image_url=image_url,
                video_url=video_url_value,
                additional_media=additional_images_combined,
                ai_description=ai_description,
                variants_payload=parsed_variants,
                current_user=current_user,
                db=db,
            )
            created.append({
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "stock": product.stock,
                "category": product.category,
                "subcategory": product.subcategory,
                "tags": product.tags,
                "ai_description": product.ai_description,
                "image_url": product.image_url,
                "video_url": product.videos[0].video_url if product.videos else None,
                "visibility_regions": _serialize_product_visibility_regions(product.visibility_regions),
                "variants": [_serialize_product_variant(variant, product.price) for variant in (product.variants or [])],
            })
        except HTTPException as exc:
            logger.warning("Bulk upload validation failed for %r: %s", name, exc.detail)
            errors.append(_build_bulk_upload_error(idx, exc.detail, name=name))
        except Exception as exc:
            logger.error("Failed to create product %r: %s", name, exc)
            errors.append(_build_bulk_upload_error(idx, str(exc), name=name))

    db.commit()
    if created:
        _bump_product_cache_version()

    return {
        "created_count": len(created),
        "error_count": len(errors),
        "products": created,
        "errors": errors,
        "ai_used": use_ai and bool(ai_service.HF_API_TOKEN),
    }


# ── Business Profile ──────────────────────────────────────────────────────────

CURRENT_TERMS_VERSION = "1.0"

_ALLOWED_PROFILE_FIELDS = {
    "business_name", "business_type", "country", "region", "city",
    "address", "postal_code", "phone_business", "website", "tax_id", "bio",
    # Customer-facing page fields
    "about_us", "logo_url", "banner_url", "video_url",
    "certifications", "social_links", "established_year",
}
_VALID_BUSINESS_TYPES = {"retailer", "wholesaler", "manufacturer", "distributor", "service_provider", "individual"}


def _serialize_supplier_profile(profile) -> dict:
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "business_name": profile.business_name,
        "business_type": profile.business_type or "individual",
        "country": profile.country_code,
        "region": profile.region,
        "city": profile.city,
        "address": profile.address,
        "postal_code": profile.postal_code,
        "phone_business": profile.phone_business,
        "website": profile.website,
        "tax_id": profile.tax_id,
        # Customer-facing page fields
        "about_us": getattr(profile, "about_us", None),
        "logo_url": getattr(profile, "logo_url", None),
        "banner_url": getattr(profile, "banner_url", None),
        "video_url": getattr(profile, "video_url", None),
        "certifications": _deserialize_profile_json(getattr(profile, "certifications", None), []),
        "social_links": _deserialize_profile_json(getattr(profile, "social_links", None), {}),
        "established_year": getattr(profile, "established_year", None),
        "bio": profile.bio,
        "is_terms_accepted": bool(profile.is_terms_accepted),
        "terms_version": profile.terms_version,
        "terms_accepted_at": profile.terms_accepted_at.isoformat() if profile.terms_accepted_at else None,
        "verification_status": profile.verification_status or "pending",
        "verified_at": profile.verified_at.isoformat() if profile.verified_at else None,
        "created_at": profile.created_at.isoformat(),
    }


def _public_supplier_slug(profile, user: User) -> str:
    preferred_name = getattr(profile, "business_name", None) or getattr(user, "username", None)
    return _slugify_supplier_storefront(preferred_name) or _slugify_supplier_storefront(getattr(user, "username", None))


def get_supplier_profile_business(current_user: dict, db: Session) -> dict:
    from domains.comms.ports import SupplierProfile as SP
    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    if not profile:
        profile = SP(user_id=current_user["id"], verification_status="pending")
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return _serialize_supplier_profile(profile)


def update_supplier_profile_business(body: dict, current_user: dict, db: Session) -> dict:
    from domains.comms.ports import SupplierProfile as SP
    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    if not profile:
        profile = SP(user_id=current_user["id"], verification_status="pending")
        db.add(profile)
    for field in _ALLOWED_PROFILE_FIELDS:
        if field not in body:
            continue
        value = body[field]
        if field == "business_type" and value not in _VALID_BUSINESS_TYPES:
            continue
        if field in _PROFILE_JSON_ARRAY_FIELDS:
            value = _serialize_profile_json(value, "array")
        elif field in _PROFILE_JSON_OBJECT_FIELDS:
            value = _serialize_profile_json(value, "object")
        elif field == "established_year":
            if value in (None, ""):
                value = None
            else:
                try:
                    value = int(value)
                except (TypeError, ValueError) as exc:
                    raise HTTPException(status_code=400, detail="Established year must be a number") from exc
        else:
            value = _sanitize_profile_string(value)
        if field == "website" and isinstance(value, str) and value and not value.startswith(("http://", "https://")):
            value = "https://" + value
        setattr(profile, "country_code" if field == "country" else field, value)
    db.commit()
    bump_cache_version("public_suppliers")
    db.refresh(profile)
    return _serialize_supplier_profile(profile)


def upload_supplier_profile_business_media(
    field: str,
    file: UploadFile,
    current_user: dict,
    db: Session,
    index: Optional[int] = None,
) -> dict:
    from domains.comms.ports import SupplierProfile as SP

    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    if not profile:
        profile = SP(user_id=current_user["id"], verification_status="pending")
        db.add(profile)

    field_config = _SUPPLIER_PROFILE_MEDIA_FIELDS.get(field)
    if not field_config:
        raise HTTPException(status_code=400, detail="Unsupported supplier storefront media field")

    media_url = _save_supplier_profile_media_upload(file, current_user["id"], field, db=db)

    response_payload: dict[str, Any] = {
        "detail": f"Supplier {field_config['label']} uploaded successfully",
        "field": field,
        "media_url": media_url,
    }

    if field == "certification_image":
        certifications = _deserialize_profile_json(getattr(profile, "certifications", None), [])
        if index is None or index < 0:
            raise HTTPException(status_code=400, detail="Certification index is required")
        if index > len(certifications):
            raise HTTPException(status_code=400, detail="Certification index out of range")

        if index == len(certifications):
            certifications.append({})

        existing_cert = certifications[index] if isinstance(certifications[index], dict) else {}
        updated_cert = {
            **existing_cert,
            "image_url": media_url,
        }
        certifications[index] = _sanitize_profile_json(updated_cert)
        profile.certifications = json.dumps(_sanitize_profile_json(certifications))
        response_payload["index"] = index
    else:
        setattr(profile, field, media_url)

    db.commit()
    db.refresh(profile)
    response_payload["profile"] = _serialize_supplier_profile(profile)
    return response_payload


def accept_supplier_terms(current_user: dict, db: Session) -> dict:
    from domains.comms.ports import SupplierProfile as SP
    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    if not profile:
        profile = SP(user_id=current_user["id"])
        db.add(profile)
    profile.is_terms_accepted = True
    profile.terms_version = CURRENT_TERMS_VERSION
    profile.terms_accepted_at = utcnow()
    db.commit()
    return {"detail": "Terms accepted", "terms_version": CURRENT_TERMS_VERSION}


def get_supplier_onboarding_status(current_user: dict, db: Session) -> dict:
    from domains.comms.ports import SupplierProfile as SP
    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    products_count = db.query(Product).filter(
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,  # noqa: E712
    ).count()
    return {
        "profile_complete": bool(profile and profile.business_name and profile.country_code),
        "terms_accepted": bool(profile and profile.is_terms_accepted),
        "first_product_uploaded": products_count > 0,
        "products_count": products_count,
        "verification_status": profile.verification_status if profile else "pending",
    }


# ── Regions / Countries of Operation ─────────────────────────────────────────

def get_supplier_regions(current_user: dict, db: Session) -> dict:
    """Return the supplier's configured operating regions."""
    from domains.comms.ports import SupplierProfile as SP
    if current_user["role"] not in ("supplier", "admin"):
        raise HTTPException(status_code=403, detail="Supplier access required")
    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    raw = (profile.operating_regions if profile else None) or "[]"
    try:
        regions = json.loads(raw)
    except Exception:
        regions = []
    return {
        "operating_regions": regions,
        "origin_country": profile.country_code if profile else None,
        "city": profile.city if profile else None,
    }


def update_supplier_regions(body: dict, current_user: dict, db: Session) -> dict:
    """Save the supplier's list of operating countries/regions."""
    from domains.comms.ports import SupplierProfile as SP
    if current_user["role"] not in ("supplier", "admin"):
        raise HTTPException(status_code=403, detail="Supplier access required")
    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    if not profile:
        profile = SP(user_id=current_user["id"])
        db.add(profile)
    regions = body.get("operating_regions", [])
    if not isinstance(regions, list):
        raise HTTPException(status_code=422, detail="operating_regions must be a list")
    # sanitize — keep plain strings only, max 200 entries
    sanitized = [str(r).strip()[:100] for r in regions if r][:200]
    profile.operating_regions = json.dumps(sanitized)
    if "origin_country" in body and isinstance(body["origin_country"], str):
        profile.country_code = body["origin_country"].strip()[:100] or profile.country_code
    if "city" in body and isinstance(body["city"], str):
        profile.city = body["city"].strip()[:100] or profile.city
    db.commit()
    return {"operating_regions": sanitized, "origin_country": profile.country_code, "city": profile.city}


# ── Credibility Badge & Document Verification ─────────────────────────────────

_BADGE_THRESHOLDS = {
    # (min_credibility_score, label)
    "gold": 85,
    "silver": 65,
    "bronze": 40,
    "none": 0,
}
_FULFILLED_ORDER_STATUSES = ("completed", "delivered", "shipped")
_MANUAL_BADGE_LEVELS = {"membership", "verified"}
_BADGE_AMOUNT_QUANT = Decimal("0.001")


def _round_badge_amount(value: object) -> Decimal:
    return to_decimal(value).quantize(_BADGE_AMOUNT_QUANT, rounding=ROUND_HALF_UP)


def _ensure_supplier_profile_record(supplier_id: int, db: Session) -> SupplierProfile:
    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == supplier_id).first()
    if not profile:
        profile = SupplierProfile(user_id=supplier_id, verification_status="pending")
        db.add(profile)
        db.flush()
    return profile


def _start_of_month(value: datetime) -> datetime:
    return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _start_of_next_month(value: datetime) -> datetime:
    if value.month == 12:
        return value.replace(year=value.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return value.replace(month=value.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)


def _start_of_year(value: datetime) -> datetime:
    return value.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)


def _start_of_next_year(value: datetime) -> datetime:
    return value.replace(year=value.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)


def _badge_period_bounds(interval: Optional[str], reference_time: datetime) -> tuple[Optional[datetime], Optional[datetime]]:
    normalized = str(interval or "").strip().lower()
    if normalized == "monthly":
        return _start_of_month(reference_time), _start_of_next_month(reference_time)
    if normalized in {"annual", "yearly"}:
        return _start_of_year(reference_time), _start_of_next_year(reference_time)
    return None, None


def _load_active_badge_tiers(db: Session) -> list[CommissionBadgeTier]:
    rows = (
        db.query(CommissionBadgeTier)
        .filter(CommissionBadgeTier.is_active == True)  # noqa: E712
        .order_by(CommissionBadgeTier.sort_order.asc(), CommissionBadgeTier.id.asc())
        .limit(1000)
        .all()
    )
    if rows:
        return rows

    from domains.finance.ports import commission_engine, log_bank_transaction

    _commission_engine.seed_defaults(db)
    return (
        db.query(CommissionBadgeTier)
        .filter(CommissionBadgeTier.is_active == True)  # noqa: E712
        .order_by(CommissionBadgeTier.sort_order.asc(), CommissionBadgeTier.id.asc())
        .limit(1000)
        .all()
    )


def _badge_tier_meets_metrics(tier: CommissionBadgeTier, metrics: dict[str, Any]) -> bool:
    required_orders = int(getattr(tier, "min_fulfilled_orders", None) or 0)
    required_revenue = to_decimal(getattr(tier, "min_monthly_revenue", None) or 0)
    return int(metrics["fulfilled_orders"]) >= required_orders and to_decimal(metrics["monthly_revenue"]) >= required_revenue


def _compute_badge_threshold_metrics(supplier_id: int, db: Session, reference_time: Optional[datetime] = None) -> dict[str, Any]:
    now = reference_time or utcnow()
    month_start = _start_of_month(now)

    fulfilled_orders = (
        db.query(func.count(func.distinct(Order.id)))
        .join(OrderItem)
        .join(Product)
        .filter(
            Product.supplier_id == supplier_id,
            Order.status.in_(_FULFILLED_ORDER_STATUSES),
        )
        .scalar()
    ) or 0

    monthly_revenue = (
        db.query(func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0))
        .select_from(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, Product.id == OrderItem.product_id)
        .filter(
            Product.supplier_id == supplier_id,
            Order.status.in_(_FULFILLED_ORDER_STATUSES),
            Order.created_at >= month_start,
        )
        .scalar()
    ) or 0

    return {
        "fulfilled_orders": int(fulfilled_orders),
        "monthly_revenue": _round_badge_amount(monthly_revenue),
        "month_start": month_start,
        "month_label": month_start.strftime("%Y-%m"),
    }


def _select_eligible_badge_tier(metrics: dict[str, Any], db: Session) -> Optional[CommissionBadgeTier]:
    tiers = _load_active_badge_tiers(db)
    fallback = next((tier for tier in tiers if str(tier.badge_level or "").lower() == "none"), None)
    selected = fallback
    for tier in tiers:
        level = str(tier.badge_level or "").lower()
        if level in _MANUAL_BADGE_LEVELS:
            continue
        if level == "none":
            continue
        if _badge_tier_meets_metrics(tier, metrics):
            selected = tier
    return selected


def _serialize_badge_billing_record(record: BadgeBillingRecord) -> dict[str, Any]:
    supplier = getattr(record, "supplier", None)
    txn = getattr(record, "bank_transaction", None)
    return {
        "id": record.id,
        "billing_reference": record.billing_reference,
        "supplier_id": record.supplier_id,
        "supplier_name": getattr(supplier, "username", None),
        "badge_level": record.badge_level,
        "charge_type": record.charge_type,
        "charge_source": record.charge_source,
        "status": record.status,
        "amount": float(_round_badge_amount(record.amount)),
        "currency": record.currency,
        "period_start": record.period_start,
        "period_end": record.period_end,
        "due_at": record.due_at,
        "billed_at": record.billed_at,
        "paid_at": record.paid_at,
        "payment_method": record.payment_method,
        "bank_transaction_id": record.bank_transaction_id,
        "transaction_ref": getattr(txn, "transaction_ref", None),
        "notes": record.notes,
        "created_by": record.created_by,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def _find_existing_badge_billing(
    supplier_id: int,
    badge_level: str,
    charge_type: str,
    db: Session,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
) -> Optional[BadgeBillingRecord]:
    q = db.query(BadgeBillingRecord).filter(
        BadgeBillingRecord.supplier_id == supplier_id,
        BadgeBillingRecord.badge_level == badge_level,
        BadgeBillingRecord.charge_type == charge_type,
        BadgeBillingRecord.status.in_(("draft", "invoiced", "paid")),
    )
    if charge_type == "setup":
        return q.order_by(BadgeBillingRecord.created_at.desc()).first()
    if period_start is not None:
        q = q.filter(BadgeBillingRecord.period_start == period_start)
    if period_end is not None:
        q = q.filter(BadgeBillingRecord.period_end == period_end)
    return q.order_by(BadgeBillingRecord.created_at.desc()).first()


def _create_badge_billing_record(
    supplier_id: int,
    badge_level: str,
    charge_type: str,
    amount: Decimal,
    db: Session,
    *,
    charge_source: str,
    created_by: Optional[int],
    notes: Optional[str] = None,
    payment_method: Optional[str] = None,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    due_at: Optional[datetime] = None,
) -> tuple[BadgeBillingRecord, bool]:
    existing = _find_existing_badge_billing(
        supplier_id=supplier_id,
        badge_level=badge_level,
        charge_type=charge_type,
        db=db,
        period_start=period_start,
        period_end=period_end,
    )
    if existing:
        return existing, False

    now = utcnow()
    normalized_amount = _round_badge_amount(amount)
    status = "paid" if normalized_amount <= 0 else "invoiced"
    record = BadgeBillingRecord(
        billing_reference=f"BDG-{uuid.uuid4().hex[:10].upper()}",
        supplier_id=supplier_id,
        badge_level=badge_level,
        charge_type=charge_type,
        charge_source=charge_source,
        status=status,
        amount=normalized_amount,
        currency=settings.default_currency,
        period_start=period_start,
        period_end=period_end,
        due_at=due_at,
        billed_at=now,
        paid_at=now if status == "paid" else None,
        payment_method=payment_method,
        notes=notes,
        created_by=created_by,
    )
    db.add(record)
    db.flush()
    return record, True


def _maybe_create_recurring_badge_billing(
    supplier_id: int,
    badge_level: str,
    badge_granted_at: Optional[datetime],
    db: Session,
    *,
    charge_source: str,
    created_by: Optional[int],
) -> Optional[BadgeBillingRecord]:
    tier = (
        db.query(CommissionBadgeTier)
        .filter(
            CommissionBadgeTier.badge_level == badge_level,
            CommissionBadgeTier.is_active == True,  # noqa: E712
        )
        .first()
    )
    if not tier:
        return None

    recurring_fee = _round_badge_amount(getattr(tier, "recurring_fee", 0) or 0)
    if recurring_fee <= 0:
        return None

    period_start, period_end = _badge_period_bounds(getattr(tier, "recurring_interval", None), utcnow())
    if period_start is None or period_end is None:
        return None

    if badge_granted_at and badge_granted_at >= period_start:
        return None

    record, created = _create_badge_billing_record(
        supplier_id=supplier_id,
        badge_level=badge_level,
        charge_type="recurring",
        amount=recurring_fee,
        db=db,
        charge_source=charge_source,
        created_by=created_by,
        notes=f"Recurring {badge_level} badge fee for {period_start.strftime('%Y-%m')}",
        period_start=period_start,
        period_end=period_end,
        due_at=period_end,
    )
    return record if created else None


def list_supplier_badge_catalog(current_user: dict, db: Session) -> dict[str, Any]:
    supplier_id = int(current_user["id"])
    profile = _ensure_supplier_profile_record(supplier_id, db)
    metrics = _compute_badge_threshold_metrics(supplier_id, db)
    eligible_tier = _select_eligible_badge_tier(metrics, db)
    current_badge = str(profile.badge_level or "none").lower()

    tiers = []
    for tier in _load_active_badge_tiers(db):
        badge_level = str(tier.badge_level or "none").lower()
        tiers.append({
            "badge_level": badge_level,
            "commission_rate": float(tier.commission_rate),
            "setup_fee": float(_round_badge_amount(tier.setup_fee)),
            "recurring_fee": float(_round_badge_amount(tier.recurring_fee)),
            "recurring_interval": tier.recurring_interval,
            "min_fulfilled_orders": tier.min_fulfilled_orders,
            "min_monthly_revenue": float(_round_badge_amount(tier.min_monthly_revenue or 0)),
            "is_active": bool(tier.is_active),
            "is_current": badge_level == current_badge,
            "is_eligible": _badge_tier_meets_metrics(tier, metrics) if badge_level not in _MANUAL_BADGE_LEVELS else False,
            "is_recommended": badge_level == str(getattr(eligible_tier, "badge_level", "none") or "none").lower(),
        })

    return {
        "supplier_id": supplier_id,
        "current_badge_level": current_badge,
        "eligible_badge_level": str(getattr(eligible_tier, "badge_level", "none") or "none").lower(),
        "fulfilled_orders": metrics["fulfilled_orders"],
        "monthly_revenue": float(metrics["monthly_revenue"]),
        "month_label": metrics["month_label"],
        "tiers": tiers,
    }


def list_supplier_badge_billing_history(current_user: dict, db: Session) -> list[dict[str, Any]]:
    supplier_id = int(current_user["id"])
    rows = (
        db.query(BadgeBillingRecord)
        .options(selectinload(BadgeBillingRecord.bank_transaction), selectinload(BadgeBillingRecord.supplier))
        .filter(BadgeBillingRecord.supplier_id == supplier_id)
        .order_by(BadgeBillingRecord.created_at.desc())
        .limit(100)
        .all()
    )
    return [_serialize_badge_billing_record(row) for row in rows]


def record_badge_billing_payment(
    billing_id: int,
    payment_method: str,
    current_user: dict,
    db: Session,
    transaction_ref: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    record = (
        db.query(BadgeBillingRecord)
        .options(selectinload(BadgeBillingRecord.bank_transaction), selectinload(BadgeBillingRecord.supplier))
        .filter(BadgeBillingRecord.id == billing_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Badge billing record not found")
    if record.status == "paid":
        return _serialize_badge_billing_record(record)
    if record.status in {"waived", "cancelled"}:
        raise HTTPException(status_code=409, detail=f"Cannot record payment for {record.status} badge billing")

    paid_at = utcnow()
    if _round_badge_amount(record.amount) > 0 and not record.bank_transaction_id:

        txn = log_bank_transaction(
            source="badge_billing",
            transaction_type="inflow",
            category="badge_fee",
            amount=_round_badge_amount(record.amount),
            db=db,
            currency=record.currency,
            supplier_id=record.supplier_id,
            description=f"{record.charge_type.title()} badge fee collected for {record.badge_level} tier",
            transaction_ref=transaction_ref,
            transaction_date=paid_at,
        )
        record.bank_transaction_id = txn.id
        record.bank_transaction = txn

    record.status = "paid"
    record.payment_method = payment_method.strip().lower() or "manual"
    record.paid_at = paid_at
    if notes:
        record.notes = notes if not record.notes else f"{record.notes}\n{notes}"

    db.flush()
    audit_log(
        db=db,
        action=AuditAction.PAYOUT_PROCESSED,
        user_id=current_user["id"],
        username=current_user["username"],
        user_role=current_user["role"],
        resource_type="badge_billing",
        resource_id=record.id,
        details={"status": record.status, "payment_method": record.payment_method, "badge_level": record.badge_level},
    )
    db.commit()
    db.refresh(record)
    return _serialize_badge_billing_record(record)


def purchase_supplier_badge(body: dict, current_user: dict, db: Session) -> dict[str, Any]:
    supplier_id = int(current_user["id"])
    badge_level = str(body.get("badge_level") or "").strip().lower()
    notes = str(body.get("notes") or "").strip() or None
    if current_user["role"] != "supplier":
        raise HTTPException(status_code=403, detail="Supplier access required")
    if not badge_level or badge_level in {"none", *sorted(_MANUAL_BADGE_LEVELS)}:
        raise HTTPException(status_code=422, detail="Select a purchasable badge tier")

    tier = (
        db.query(CommissionBadgeTier)
        .filter(
            CommissionBadgeTier.badge_level == badge_level,
            CommissionBadgeTier.is_active == True,  # noqa: E712
        )
        .first()
    )
    if not tier:
        raise HTTPException(status_code=404, detail="Badge tier not found")

    metrics = _compute_badge_threshold_metrics(supplier_id, db)
    if not _badge_tier_meets_metrics(tier, metrics):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Supplier is not yet eligible for {badge_level}. "
                f"Requires {int(getattr(tier, 'min_fulfilled_orders', None) or 0)} fulfilled orders and "
                f"{float(_round_badge_amount(getattr(tier, 'min_monthly_revenue', None) or 0))} monthly revenue."
            ),
        )

    profile = _ensure_supplier_profile_record(supplier_id, db)
    previous_badge = str(profile.badge_level or "none").lower()
    charge_type = "recurring" if previous_badge == badge_level else "setup"
    amount = _round_badge_amount(tier.recurring_fee if charge_type == "recurring" else tier.setup_fee)
    period_start, period_end = (None, None)
    due_at = utcnow() + timedelta(days=7)

    if charge_type == "recurring":
        period_start, period_end = _badge_period_bounds(getattr(tier, "recurring_interval", None), utcnow())
        if period_start is None or period_end is None:
            raise HTTPException(status_code=422, detail="This badge tier does not have a recurring billing interval")
        due_at = period_end

    record, created = _create_badge_billing_record(
        supplier_id=supplier_id,
        badge_level=badge_level,
        charge_type=charge_type,
        amount=amount,
        db=db,
        charge_source="manual_purchase",
        created_by=supplier_id,
        notes=notes,
        payment_method="manual" if amount <= 0 else None,
        period_start=period_start,
        period_end=period_end,
        due_at=due_at,
    )

    if charge_type == "setup" and previous_badge != badge_level:
        profile.badge_level = badge_level
        profile.badge_granted_at = utcnow()

    profile.credibility_score = compute_credibility_score(supplier_id, db)
    db.flush()

    audit_log(
        db=db,
        action=AuditAction.PROFILE_UPDATED,
        user_id=supplier_id,
        username=current_user["username"],
        user_role=current_user["role"],
        resource_type="badge_purchase",
        resource_id=record.id,
        details={
            "badge_level": badge_level,
            "charge_type": charge_type,
            "amount": float(_round_badge_amount(record.amount)),
            "created": created,
        },
    )

    db.commit()
    db.refresh(record)
    return {
        "badge_level": str(profile.badge_level or "none").lower(),
        "billing": _serialize_badge_billing_record(record),
        "created": created,
        "fulfilled_orders": metrics["fulfilled_orders"],
        "monthly_revenue": float(metrics["monthly_revenue"]),
    }


def compute_credibility_score(supplier_id: int, db: Session) -> int:
    """
    Compute a 0-100 credibility score based on:
      - Order fulfilment rate        (max 35 pts)
      - Average product review score (max 25 pts)
      - Document verification status (max 20 pts)
      - Account age in days          (max 10 pts)
      - Number of approved products  (max 10 pts)
    """
    from domains.catalog.ports import Product
    from domains.catalog.ports import Review
    from domains.comms.ports import SupplierProfile as SP
    from domains.orders.ports import Order
    from domains.orders.ports import OrderItem

    # 1. Fulfilment rate
    total_orders = (
        db.query(func.count(func.distinct(Order.id)))
        .join(OrderItem)
        .join(Product)
        .filter(Product.supplier_id == supplier_id)
        .scalar()
    ) or 0
    fulfilled_orders = (
        db.query(func.count(func.distinct(Order.id)))
        .join(OrderItem)
        .join(Product)
        .filter(
            Product.supplier_id == supplier_id,
            Order.status.in_(["completed", "delivered", "shipped"]),
        )
        .scalar()
    ) or 0
    fulfilment_rate = (fulfilled_orders / total_orders) if total_orders > 0 else 0
    pts_fulfilment = round(fulfilment_rate * 35)

    # 2. Average review
    avg_review = (
        db.query(func.avg(Review.rating))
        .join(Product, Review.product_id == Product.id)
        .filter(Product.supplier_id == supplier_id)
        .scalar()
    ) or 0
    pts_review = round((float(avg_review) / 5.0) * 25)

    # 3. Document verification
    profile = db.query(SP).filter(SP.user_id == supplier_id).first()
    docs = {}
    if profile and profile.verified_documents:
        try:
            docs = json.loads(profile.verified_documents)
        except Exception:
            docs = {}
    pts_docs = 0
    if profile and profile.verification_status in ("approved", "verified"):
        pts_docs = 20
    elif docs:
        pts_docs = min(15, len(docs) * 5)

    # 4. Account age
    user = db.query(User).filter(User.id == supplier_id).first()
    age_days = 0
    if user and user.created_at:
        age_days = max(0, (utcnow() - user.created_at).days)
    pts_age = min(10, age_days // 30)  # 1pt per month, max 10

    # 5. Approved products
    approved_count = (
        db.query(func.count(Product.id))
        .filter(
            Product.supplier_id == supplier_id,
            Product.is_approved == True,  # noqa: E712
            Product.is_deleted == False,  # noqa: E712
        )
        .scalar()
    ) or 0
    pts_products = min(10, approved_count)

    return int(pts_fulfilment + pts_review + pts_docs + pts_age + pts_products)


def _badge_for_score(score: int) -> str:
    if score >= _BADGE_THRESHOLDS["gold"]:
        return "gold"
    if score >= _BADGE_THRESHOLDS["silver"]:
        return "silver"
    if score >= _BADGE_THRESHOLDS["bronze"]:
        return "bronze"
    return "none"


def refresh_supplier_badge(supplier_id: int, db: Session) -> dict:
    """Recompute credibility score and align badge assignment to tier thresholds."""
    profile = _ensure_supplier_profile_record(supplier_id, db)
    score = compute_credibility_score(supplier_id, db)
    metrics = _compute_badge_threshold_metrics(supplier_id, db)
    eligible_tier = _select_eligible_badge_tier(metrics, db)
    previous_badge = str(profile.badge_level or "none").lower()

    if previous_badge in _MANUAL_BADGE_LEVELS:
        resolved_badge = previous_badge
    else:
        resolved_badge = str(getattr(eligible_tier, "badge_level", None) or _badge_for_score(score)).lower()

    profile.credibility_score = score
    created_billings: list[dict[str, Any]] = []
    if previous_badge != resolved_badge:
        profile.badge_level = resolved_badge
        profile.badge_granted_at = utcnow()
        if eligible_tier is not None and resolved_badge not in {"none", *sorted(_MANUAL_BADGE_LEVELS)}:
            record, created = _create_badge_billing_record(
                supplier_id=supplier_id,
                badge_level=resolved_badge,
                charge_type="setup",
                amount=_round_badge_amount(getattr(eligible_tier, "setup_fee", 0) or 0),
                db=db,
                charge_source="automatic_recalculation",
                created_by=None,
                notes=f"Automatic badge recalculation promoted supplier to {resolved_badge}",
                due_at=utcnow() + timedelta(days=7),
            )
            if created:
                created_billings.append(_serialize_badge_billing_record(record))
        audit_log(
            db=db,
            action=AuditAction.PROFILE_UPDATED,
            user_id=None,
            username="system",
            user_role="system",
            resource_type="supplier_badge",
            resource_id=supplier_id,
            details={"previous_badge": previous_badge, "badge_level": resolved_badge, "source": "automatic_recalculation"},
        )

    recurring_billing = None
    if resolved_badge not in {"none", *sorted(_MANUAL_BADGE_LEVELS)}:
        recurring_record = _maybe_create_recurring_badge_billing(
            supplier_id=supplier_id,
            badge_level=resolved_badge,
            badge_granted_at=profile.badge_granted_at,
            db=db,
            charge_source="scheduled_recurring",
            created_by=None,
        )
        if recurring_record is not None:
            recurring_billing = _serialize_badge_billing_record(recurring_record)

    db.commit()
    bump_cache_version("public_suppliers")
    return {
        "supplier_id": supplier_id,
        "credibility_score": score,
        "badge_level": str(profile.badge_level or "none").lower(),
        "previous_badge_level": previous_badge,
        "eligible_badge_level": str(getattr(eligible_tier, "badge_level", "none") or "none").lower(),
        "fulfilled_orders": metrics["fulfilled_orders"],
        "monthly_revenue": float(metrics["monthly_revenue"]),
        "month_label": metrics["month_label"],
        "billing_records_created": created_billings,
        "recurring_billing": recurring_billing,
    }


def run_badge_recalculation_cycle(db: Session) -> dict[str, Any]:
    supplier_ids = [supplier_id for supplier_id, in db.query(User.id).filter(User.role == "supplier").limit(1000).all()]
    changed = 0
    invoiced = 0
    recurring = 0
    snapshots: list[dict[str, Any]] = []
    for supplier_id in supplier_ids:
        snapshot = refresh_supplier_badge(int(supplier_id), db)
        snapshots.append(snapshot)
        if snapshot.get("previous_badge_level") != snapshot.get("badge_level"):
            changed += 1
        invoiced += len(snapshot.get("billing_records_created") or [])
        recurring += 1 if snapshot.get("recurring_billing") else 0
    return {
        "suppliers_processed": len(supplier_ids),
        "badges_changed": changed,
        "billings_created": invoiced,
        "recurring_billings_created": recurring,
        "snapshots": snapshots,
    }


async def upload_verification_documents(
    files: list,
    doc_types: list[str],
    current_user: dict,
    db: Session,
) -> dict:
    """
    Upload KYC/verification documents for the supplier.
    Stores file paths in SupplierProfile.verified_documents (JSON).
    """
    from domains.comms.ports import SupplierProfile as SP
    from infrastructure.utils.file_validation import validate_upload_image
    from infrastructure.utils.config import settings as _settings

    _VALID_DOC_TYPES = {"trade_license", "tax_certificate", "id_front", "id_back", "bank_statement", "other"}

    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    if not profile:
        profile = SP(user_id=current_user["id"], verification_status="pending")
        db.add(profile)

    existing_docs = {}
    if profile.verified_documents:
        try:
            existing_docs = json.loads(profile.verified_documents)
        except Exception:
            existing_docs = {}

    from infrastructure.utils.storage import storage as _storage

    saved = {}
    for file, doc_type in zip(files, doc_types):
        if doc_type not in _VALID_DOC_TYPES:
            continue
        content = await file.read()
        try:
            ext = validate_upload_image(content, file.filename or "doc")
        except Exception:
            fname_lower = (file.filename or "").lower()
            if not fname_lower.endswith(".pdf"):
                continue
            ext = ".pdf"
        filename = f"doc_{current_user['id']}_{doc_type}_{uuid.uuid4().hex[:6]}{ext}"
        key = f"supplier_documents/{filename}"
        mime_type = file.content_type or "application/octet-stream"
        saved[doc_type] = _storage.save(key, content, content_type=mime_type)

    existing_docs.update(saved)
    profile.verified_documents = json.dumps(existing_docs)
    profile.document_expires_at = None  # admin sets expiry after review
    db.commit()

    # auto-refresh badge score after upload
    refresh_supplier_badge(current_user["id"], db)

    return {
        "uploaded": list(saved.keys()),
        "all_documents": existing_docs,
    }


_PERIOD_DAYS = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}


def get_supplier_analytics_timeseries(
    current_user: dict,
    period: str,
    db: Session,
) -> dict:
    """Return daily revenue and order counts for the authenticated supplier."""
    supplier_id = current_user["id"]
    if current_user["role"] not in ("supplier", "admin"):
        raise HTTPException(status_code=403, detail="Supplier access required")

    days = _PERIOD_DAYS.get(period, 30)
    since = utcnow() - timedelta(days=days)

    rows = (
        db.query(
            func.date(Order.created_at).label("day"),
            func.count(Order.id.distinct()).label("orders"),
            func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0).label("revenue"),
        )
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, Product.id == OrderItem.product_id)
        .filter(
            Product.supplier_id == supplier_id,
            Order.created_at >= since,
            Order.status != "cancelled",
        )
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
    )

    return {
        "period": period,
        "data": [
            {"date": str(r.day), "orders": r.orders, "revenue": float(r.revenue)}
            for r in rows
        ],
    }


def admin_set_supplier_badge(
    supplier_user_id: int,
    badge_level: str,
    current_user: dict,
    db: Session,
) -> dict:
    """Admin: manually override badge level for a supplier."""
    from domains.comms.ports import SupplierProfile as SP
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    normalized_badge_level = str(badge_level or "").strip().lower()
    valid_badges = {"none", "bronze", "silver", "gold", "membership", "verified"}
    if normalized_badge_level not in valid_badges:
        raise HTTPException(status_code=422, detail=f"badge_level must be one of: {', '.join(sorted(valid_badges))}")
    profile = db.query(SP).filter(SP.user_id == supplier_user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Supplier profile not found")
    profile.badge_level = normalized_badge_level
    profile.badge_granted_at = utcnow()
    db.commit()
    bump_cache_version("public_suppliers")
    audit_log(
        db=db,
        action=AuditAction.PROFILE_UPDATED,
        user_id=current_user["id"],
        username=current_user["username"],
        user_role=current_user["role"],
        resource_type="supplier_badge",
        resource_id=supplier_user_id,
        details={"badge_level": normalized_badge_level},
    )
    return {
        "supplier_id": supplier_user_id,
        "badge_level": profile.badge_level,
        "badge_granted_at": profile.badge_granted_at.isoformat(),
    }


# ── Public (Customer-Facing) Supplier Endpoints ───────────────────────────────

def _public_storefront_visibility_clause(profile_model, user_model=None):
    visibility_clauses = [
        profile_model.verification_status.in_(["approved", "verified"]),
    ]
    return or_(*visibility_clauses)


def _get_public_supplier_aggregates(supplier_ids: list[int], db: Session) -> dict[int, dict[str, float | int]]:
    if not supplier_ids:
        return {}

    from domains.catalog.ports import Review as ReviewModel

    aggregates: dict[int, dict[str, float | int]] = {
        supplier_id: {
            "product_count": 0,
            "avg_rating": 0.0,
            "total_reviews": 0,
            "total_sales": 0,
        }
        for supplier_id in supplier_ids
    }

    product_rows = (
        db.query(
            Product.supplier_id,
            func.count(Product.id),
            func.avg(Product.rating),
            func.sum(Product.sales_count),
        )
        .filter(
            Product.supplier_id.in_(supplier_ids),
            Product.is_deleted == False,  # noqa: E712
            Product.is_active == True,  # noqa: E712
        )
        .group_by(Product.supplier_id)
        .limit(1000)
        .all()
    )

    for supplier_id, product_count, avg_rating, total_sales in product_rows:
        aggregates[int(supplier_id)] = {
            **aggregates.get(int(supplier_id), {}),
            "product_count": int(product_count or 0),
            "avg_rating": float(avg_rating or 0.0),
            "total_sales": int(total_sales or 0),
        }

    review_rows = (
        db.query(Product.supplier_id, func.count(ReviewModel.id))
        .join(Product, ReviewModel.product_id == Product.id)
        .filter(
            Product.supplier_id.in_(supplier_ids),
            Product.is_deleted == False,  # noqa: E712
            Product.is_active == True,  # noqa: E712
            ReviewModel.is_deleted == False,  # noqa: E712
        )
        .group_by(Product.supplier_id)
        .limit(1000)
        .all()
    )

    for supplier_id, total_reviews in review_rows:
        current = aggregates.get(int(supplier_id), {
            "product_count": 0,
            "avg_rating": 0.0,
            "total_reviews": 0,
            "total_sales": 0,
        })
        current["total_reviews"] = int(total_reviews or 0)
        aggregates[int(supplier_id)] = current

    return aggregates


def _normalize_supplier_lookup_token(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _supplier_lookup_sql_expression(column):
    return func.lower(
        func.replace(
            func.replace(
                func.replace(
                    func.replace(func.coalesce(column, ""), " ", ""),
                    "-",
                    "",
                ),
                "_",
                "",
            ),
            ".",
            "",
        )
    )

def _get_public_supplier_record(supplier_id: int, db: Session):
    from domains.comms.ports import SupplierProfile as SP

    row = (
        db.query(User, SP)
        .join(SP, SP.user_id == User.id)
        .filter(
            User.id == supplier_id,
            User.is_active == 1,
            User.role == "supplier",
            _public_storefront_visibility_clause(SP, User),
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return row

def list_public_suppliers(
    q: Optional[str],
    names: Optional[str],
    country: Optional[str],
    limit: int,
    offset: int,
    db: Session,
) -> dict:
    """
    Return active suppliers for the customer discovery page.
    No PII is exposed — only business-facing fields.
    """
    region_code = normalize_country_code(country)
    cache_key = _build_public_supplier_cache_key(
        "list",
        {
            "q": (q or "").strip().lower(),
            "names": names or "",
            "country": region_code,
            "limit": limit,
            "offset": offset,
        },
    )
    cached_payload = cache_get_json(cache_key)
    if isinstance(cached_payload, dict):
        return cached_payload

    from domains.comms.ports import SupplierProfile as SP

    base_query = db.query(SP, User).join(User, User.id == SP.user_id).filter(
        User.is_active == 1,
        User.role == "supplier",
        _public_storefront_visibility_clause(SP, User),
    )

    if q:
        term = f"%{q.strip()}%"
        base_query = base_query.filter(
            or_(
                User.email.ilike(term),
                SP.business_name.ilike(term),
                SP.bio.ilike(term),
                SP.city.ilike(term),
                SP.region.ilike(term),
                SP.country_code.ilike(term),
            )
        )

    supplier_names = [value.strip() for value in (names or "").split(",") if value.strip()]
    if supplier_names:
        if len(supplier_names) == 1:
            exact_name = supplier_names[0]
            base_query = base_query.filter(
                or_(
                    User.email.ilike(exact_name),
                    SP.business_name.ilike(exact_name),
                )
            )
        else:
            base_query = base_query.filter(
                or_(
                    User.email.in_(supplier_names),
                    SP.business_name.in_(supplier_names),
                )
            )

    profiles = base_query.order_by(User.created_at.desc(), User.id.desc()).limit(1000).all()

    if region_code:
        profiles = [
            (profile, user)
            for profile, user in profiles
            if not normalize_country_code(getattr(profile, "country_code", None))
            or normalize_country_code(getattr(profile, "country_code", None)) == region_code
        ]

    total = len(profiles)
    profiles = profiles[offset : offset + limit]

    aggregates = _get_public_supplier_aggregates([user.id for profile, user in profiles], db)
    items = [
        _build_public_supplier_summary(profile, user, aggregates.get(user.id, {}))
        for profile, user in profiles
    ]

    payload = {"total": total, "items": items}
    cache_set_json(cache_key, payload, _PUBLIC_SUPPLIER_CACHE_TTL)
    return payload


def resolve_public_supplier_slug(slug: str, db: Session) -> dict:
    cache_key = _build_public_supplier_cache_key("slug", {"slug": slug.strip().lower()})
    cached_payload = cache_get_json(cache_key)
    if isinstance(cached_payload, dict):
        return cached_payload

    from domains.comms.ports import SupplierProfile as SP

    normalized_slug = _normalize_supplier_lookup_token(slug)
    if not normalized_slug:
        raise HTTPException(status_code=404, detail="Supplier not found")

    base_query = db.query(User, SP).join(SP, SP.user_id == User.id).filter(
        User.is_active == 1,
        User.role == "supplier",
        _public_storefront_visibility_clause(SP, User),
    )

    row = base_query.filter(
        or_(
            _supplier_lookup_sql_expression(User.email) == normalized_slug,
            _supplier_lookup_sql_expression(SP.business_name) == normalized_slug,
        )
    ).first()

    if not row:
        for user, profile in base_query.limit(1000).all():
            if _normalize_supplier_lookup_token(user.username) == normalized_slug:
                row = (user, profile)
                break
            if _normalize_supplier_lookup_token(getattr(profile, "business_name", None)) == normalized_slug:
                row = (user, profile)
                break

    if not row:
        raise HTTPException(status_code=404, detail="Supplier not found")

    user, profile = row
    aggregates = _get_public_supplier_aggregates([user.id], db)
    storefront_slug = _public_supplier_slug(profile, user)

    payload = {
        **_build_public_supplier_summary(profile, user, aggregates.get(user.id, {})),
        "canonical_path": f"/supplier={storefront_slug}",
    }
    cache_set_json(cache_key, payload, _PUBLIC_SUPPLIER_CACHE_TTL)
    return payload


def get_public_supplier_profile(supplier_id: int, db: Session) -> dict:
    """
    Return the full customer-facing profile for one supplier.
    Sensitive fields (phone, address, tax_id, email) are excluded.
    """
    cache_key = _build_public_supplier_cache_key("profile", {"supplier_id": supplier_id})
    cached_payload = cache_get_json(cache_key)
    if isinstance(cached_payload, dict):
        return cached_payload

    user, profile = _get_public_supplier_record(supplier_id, db)

    aggregates = _get_public_supplier_aggregates([supplier_id], db).get(
        supplier_id,
        {"product_count": 0, "avg_rating": 0.0, "total_reviews": 0, "total_sales": 0},
    )

    from domains.catalog.ports import Review as ReviewModel

    recent_reviews = [
        {
            "id": review.id,
            "rating": float(review.rating),
            "comment": review.comment,
            "username": reviewer_name,
            "customer_name": reviewer_name,
            "product_name": product_name,
            "created_at": review.created_at.isoformat(),
            "is_verified_purchase": bool(review.is_verified_purchase),
        }
        for review, product_name, reviewer_name in (
            db.query(ReviewModel, Product.name, User.email)
            .join(Product, ReviewModel.product_id == Product.id)
            .join(User, ReviewModel.user_id == User.id)
            .filter(
                Product.supplier_id == supplier_id,
                Product.is_deleted == False,  # noqa: E712
                Product.is_active == True,  # noqa: E712
                ReviewModel.is_deleted == False,  # noqa: E712
            )
            .order_by(ReviewModel.created_at.desc())
            .limit(5)
            .all()
        )
    ]

    certifications_raw = getattr(profile, "certifications", None) if profile else None
    certifications: list = []
    if certifications_raw:
        try:
            certifications = json.loads(certifications_raw)
        except Exception:
            certifications = []

    social_links_raw = getattr(profile, "social_links", None) if profile else None
    social_links: dict = {}
    if social_links_raw:
        try:
            social_links = json.loads(social_links_raw)
        except Exception:
            social_links = {}

    payload = {
        "id": user.id,
        "username": user.username,
        "slug": _public_supplier_slug(profile, user),
        "business_name": getattr(profile, "business_name", None) if profile else None,
        "business_type": (getattr(profile, "business_type", None) or "individual") if profile else "individual",
        # Model uses `country_code`; the `country` relationship returns the full config object,
        # so expose the ISO code string for the UI.
        "country": getattr(profile, "country_code", None) if profile else None,
        "country_code": getattr(profile, "country_code", None) if profile else None,
        "region": getattr(profile, "region", None) if profile else None,
        "city": getattr(profile, "city", None) if profile else None,
        "website": getattr(profile, "website", None) if profile else None,
        "bio": getattr(profile, "bio", None) if profile else None,
        "about_us": getattr(profile, "about_us", None) if profile else None,
        "logo_url": getattr(profile, "logo_url", None) if profile else None,
        "banner_url": getattr(profile, "banner_url", None) if profile else None,
        "video_url": getattr(profile, "video_url", None) if profile else None,
        "certifications": certifications,
        "social_links": social_links,
        "established_year": getattr(profile, "established_year", None) if profile else None,
        "verification_status": (getattr(profile, "verification_status", None) or "pending") if profile else "pending",
        "badge_level": (getattr(profile, "badge_level", None) or "none") if profile else "none",
        "credibility_score": (getattr(profile, "credibility_score", None) or 0) if profile else 0,
        "member_since": user.created_at.isoformat(),
        "is_verified": bool(user.is_verified),
        # Aggregated metrics
        "product_count": int(aggregates.get("product_count", 0)),
        "avg_rating": round(float(aggregates.get("avg_rating", 0.0)), 1),
        "total_reviews": int(aggregates.get("total_reviews", 0)),
        "total_sales": int(aggregates.get("total_sales", 0)),
        "recent_reviews": recent_reviews,
    }
    cache_set_json(cache_key, payload, _PUBLIC_SUPPLIER_CACHE_TTL)
    return payload


def get_public_supplier_products(
    supplier_id: int, limit: int, offset: int, db: Session
) -> dict:
    """Return paginated active products for the customer-facing supplier page."""
    cache_key = _build_public_supplier_cache_key(
        "products",
        {"supplier_id": supplier_id, "limit": limit, "offset": offset},
    )
    cached_payload = cache_get_json(cache_key)
    if isinstance(cached_payload, dict):
        return cached_payload

    _get_public_supplier_record(supplier_id, db)

    total = db.query(func.count(Product.id)).filter(
        Product.supplier_id == supplier_id,
        Product.is_deleted == False,  # noqa: E712
        Product.is_active == True,  # noqa: E712
    ).scalar() or 0

    products = db.query(Product).filter(
        Product.supplier_id == supplier_id,
        Product.is_deleted == False,  # noqa: E712
        Product.is_active == True,  # noqa: E712
    ).order_by(Product.created_at.desc()).offset(offset).limit(limit).all()

    items = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": str(p.price),
            "compare_price": str(p.compare_price) if p.compare_price else None,
            "image_url": p.image_url,
            "additional_images": p.images,
            "stock": p.stock,
            "category": p.category,
            "brand": p.brand,
            "rating": p.rating,
            "color": p.color,
            "tags": p.tags,
            "sizes": p.sizes,
            "materials": p.materials,
            "weight": p.weight,
            "dimensions": p.dimensions,
            "is_new": bool(getattr(p, "is_new", False)),
            "is_hot": bool(getattr(p, "is_hot", False)),
            "is_featured": bool(getattr(p, "is_featured", False)),
            "sales_count": p.sales_count,
            "created_at": p.created_at.isoformat(),
        }
        for p in products
    ]
    payload = {"total": total, "items": items}
    cache_set_json(cache_key, payload, _PUBLIC_SUPPLIER_CACHE_TTL)
    return payload


def _build_public_supplier_summary(profile, user: User, aggregates: dict[str, float | int]) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "slug": _public_supplier_slug(profile, user),
        "business_name": getattr(profile, "business_name", None),
        "country": getattr(profile, "country_code", None),
        "city": getattr(profile, "city", None),
        "logo_url": getattr(profile, "logo_url", None),
        "bio": getattr(profile, "bio", None),
        "badge_level": getattr(profile, "badge_level", None) or "none",
        "verification_status": getattr(profile, "verification_status", None) or "pending",
        "credibility_score": int(aggregates.get("credibility_score", getattr(profile, "credibility_score", 0) or 0)),
        "is_verified": bool(user.is_verified),
        "product_count": int(aggregates.get("product_count", 0)),
        "avg_rating": round(float(aggregates.get("avg_rating", 0.0)), 1),
        "total_reviews": int(aggregates.get("total_reviews", 0)),
        "total_sales": int(aggregates.get("total_sales", 0)),
        "member_since": user.created_at.isoformat(),
    }


# ── Supplier Bank Account (Payout Beneficiary) ───────────────────────────────

def get_supplier_bank_account(current_user: dict, db: Session) -> dict:
    """Return the supplier's own bank account details."""
    supplier_id = int(current_user["id"])
    if current_user["role"] != "supplier":
        raise HTTPException(status_code=403, detail="Supplier access required.")
    record = db.query(SupplierBankAccount).filter(SupplierBankAccount.supplier_id == supplier_id).first()
    if record is None:
        return {"configured": False}
    return {
        "configured": True,
        "id": record.id,
        "beneficiary_name": record.beneficiary_name,
        "bank_name": record.bank_name,
        "branch_name": record.branch_name,
        "account_number": record.account_number,
        "iban": record.iban,
        "swift_code": record.swift_code,
        "routing_number": record.routing_number,
        "currency": record.currency,
        "bank_country": record.bank_country,
        "verification_status": record.verification_status,
        "verification_note": record.verification_note,
        "provider": record.provider,
        "provider_recipient_id": record.provider_recipient_id,
        "provider_status": record.provider_status,
        "provider_last_synced_at": record.provider_last_synced_at.isoformat() if record.provider_last_synced_at else None,
        "verified_at": record.verified_at.isoformat() if record.verified_at else None,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


def upsert_supplier_bank_account(body: dict, current_user: dict, db: Session) -> dict:
    """Supplier submits or updates their payout bank account. Triggers re-verification."""
    supplier_id = int(current_user["id"])
    if current_user["role"] != "supplier":
        raise HTTPException(status_code=403, detail="Supplier access required.")

    record = db.query(SupplierBankAccount).filter(SupplierBankAccount.supplier_id == supplier_id).first()
    is_new = record is None
    if is_new:
        record = SupplierBankAccount(supplier_id=supplier_id)
        db.add(record)

    for field in ("beneficiary_name", "bank_name", "branch_name", "account_number",
                  "iban", "swift_code", "routing_number", "currency", "bank_country"):
        value = body.get(field)
        if value is not None:
            setattr(record, field, value)

    # Any update resets verification (only if previously verified/rejected)
    if not is_new and getattr(record, "verification_status", "pending") != "pending":
        setattr(record, "verification_status", "pending")
        setattr(record, "verification_note", "Resubmitted by supplier — awaiting re-verification.")
        setattr(record, "provider", None)
        setattr(record, "provider_recipient_id", None)
        setattr(record, "provider_status", None)
        setattr(record, "provider_last_synced_at", None)
        setattr(record, "verified_at", None)
        setattr(record, "verified_by", None)

    db.commit()
    db.refresh(record)
    return {
        "ok": True,
        "id": record.id,
        "verification_status": record.verification_status,
        "message": "Bank account saved. Awaiting admin verification." if is_new else "Bank account updated. Awaiting re-verification.",
    }


