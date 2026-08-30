"""Supplier sub-module — imports shared helpers from supplier_shared."""

from domains.suppliers.services.supplier_shared import *

def get_supplier_orders(
    current_user: dict,
    db: Session,
    limit: Optional[int] = None,
    offset: int = 0,
    search: Optional[str] = None,
    status: Optional[str] = None,
) -> dict[str, Any]:
    supplier_id = current_user["id"]
    order_id_query = (
        db.query(Order.id.label("order_id"), Order.created_at.label("created_at"))
        .join(OrderItem)
        .join(Product)
        .filter(Product.supplier_id == supplier_id)
        .distinct()
    )
    if status and status != "all":
        order_id_query = order_id_query.filter(Order.status == status)
    if search and search.strip():
        term = f"%{search.strip()}%"
        order_id_query = order_id_query.outerjoin(User, User.id == Order.user_id).filter(
            or_(
                func.cast(Order.id, String).ilike(term),
                User.email.ilike(term),
                User.email.ilike(term),
            )
        )
    total = order_id_query.count()
    query = order_id_query.order_by(Order.created_at.desc(), Order.id.desc())
    if offset:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    paged_order_ids = [cast(int, row.order_id) for row in query.all()]
    if not paged_order_ids:
        resolved_page_size = limit if limit is not None else 0
        return _build_list_page_payload([], total, offset=offset, page_size=resolved_page_size)

    supplier_orders = (
        db.query(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.id.in_(paged_order_ids))
        .all()
    )
    order_positions = {order_id: index for index, order_id in enumerate(paged_order_ids)}
    supplier_orders.sort(key=lambda order: order_positions.get(cast(int, order.id), len(order_positions)))
    shipments_by_order = _load_shipments_for_orders([cast(int, order.id) for order in supplier_orders], db)
    shipment_ids = [cast(int, shipment.id) for shipments in shipments_by_order.values() for shipment in shipments]
    shipment_events_by_shipment: dict[int, list[ShipmentEvent]] = {}
    if shipment_ids:
        shipment_events = (
            db.query(ShipmentEvent)
            .filter(ShipmentEvent.shipment_id.in_(shipment_ids))
            .order_by(ShipmentEvent.created_at.asc(), ShipmentEvent.id.asc())
            .all()
        )
        for event in shipment_events:
            shipment_events_by_shipment.setdefault(cast(int, event.shipment_id), []).append(event)
    customers_by_id = _load_users_by_ids([cast(int, order.user_id) for order in supplier_orders], db)

    # Batch-load supplier settlements for payment/settlement status enrichment
    all_order_ids = [cast(int, order.id) for order in supplier_orders]
    settlements_by_order: dict[int, SupplierSettlement] = {}
    if all_order_ids:
        settlements_by_order = {
            cast(int, s.order_id): s
            for s in db.query(SupplierSettlement).filter(
                SupplierSettlement.supplier_id == supplier_id,
                SupplierSettlement.order_id.in_(all_order_ids),
            ).all()
        }

    result = []
    orders_updated = False
    for order in supplier_orders:
        shipments = shipments_by_order.get(cast(int, order.id), [])
        reconciled_status = reconcile_order_status(order, shipments)
        if order.status != reconciled_status:
            order.status = reconciled_status
            orders_updated = True

        supplier_shipments = [
            shipment
            for shipment in shipments
            if cast(Optional[int], getattr(shipment, "supplier_id", None)) == supplier_id
        ]
        preferred_shipment = supplier_shipments[-1] if supplier_shipments else None
        shipment_status = cast(Optional[str], getattr(preferred_shipment, "status", None)) if preferred_shipment else None
        shipment_events = []
        for shipment in shipments:
            shipment_events.extend(shipment_events_by_shipment.get(cast(int, shipment.id), []))

        status_label_value = order_status_label(reconciled_status, shipments, shipment_events)
        shipment_status_label_value = (
            shipment_status_label(shipment_status, shipment=preferred_shipment)
            if preferred_shipment and shipment_status
            else None
        )
        tracking_number = (
            cast(Optional[str], getattr(preferred_shipment, "tracking_number", None))
            or canonical_scan_code(preferred_shipment)
            if preferred_shipment
            else None
        )

        customer = customers_by_id.get(cast(int, order.user_id))
        order_financials = derive_order_financials(order)
        settlement = settlements_by_order.get(cast(int, order.id))
        supplier_items = [
            {
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": item.price,
                "product_name": item.product.name,
                "product_image": _normalize_media_path(item.product.image_url),
            }
            for item in order.items
            if item.product.supplier_id == supplier_id
        ]
        result.append({
            "id": order.id,
            "user_id": order.user_id,
            "total_amount": order_financials["total"],
            "status": order.status,
            "status_label": status_label_value,
            "tracking_number": tracking_number,
            "shipment_status": shipment_status,
            "shipment_status_label": shipment_status_label_value,
            "payment_status": "paid" if getattr(order, "paid_at", None) else "unpaid",
            "paid_at": order.paid_at.isoformat() if getattr(order, "paid_at", None) else None,
            "payment_method": getattr(order, "payment_method", None),
            "settlement_status": cast(str, getattr(settlement, "status", None)) if settlement else None,
            "settlement_id": cast(int, getattr(settlement, "id", None)) if settlement else None,
            "settlement_net_amount": float(cast(object, getattr(settlement, "net_amount", None)) or 0) if settlement else None,
            "created_at": order.created_at.isoformat(),
            "customer_name": customer.username if customer else "Unknown",
            "customer_email": customer.email if customer else "",
            "customer_phone": order.customer_phone,
            "shipping_address": order.shipping_address,
            "delivery_location": order.delivery_location,
            "delivery_note": order.delivery_note,
            "items": supplier_items,
        })
    if orders_updated:
        db.commit()
    resolved_page_size = limit if limit is not None else len(result)
    return _build_list_page_payload(result, total, offset=offset, page_size=resolved_page_size)


def update_supplier_order_status(order_id: int, status_update: dict, current_user: dict, db: Session) -> dict:
    order_has_supplier_products = (
        db.query(OrderItem)
        .join(Product)
        .filter(
            OrderItem.order_id == order_id,
            Product.supplier_id == current_user["id"],
        )
        .first()
    )
    if not order_has_supplier_products:
        raise HTTPException(status_code=404, detail="Order not found or no products from this supplier")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    shipments = (
        db.query(Shipment)
        .filter(Shipment.order_id == order_id, Shipment.supplier_id == current_user["id"])
        .order_by(Shipment.created_at.desc())
        .all()
    )
    current_reconciled = reconcile_order_status(order, shipments)
    new_status = (status_update or {}).get("status", "").strip().lower()

    ALLOWED_SUPPLIER_TRANSITIONS = {
        "confirmed": ["processing"],
        "processing": ["prepared"],
        "prepared": ["processing"],
    }

    if new_status in ALLOWED_SUPPLIER_TRANSITIONS.get(current_reconciled, []):
        order.status = new_status
        db.commit()
        db.refresh(order)
        return {
            "message": f"Order status updated to '{new_status}'",
            "order_id": order.id,
            "status": order.status,
        }

    raise HTTPException(
        status_code=409,
        detail=(
            f"Cannot transition order status from '{current_reconciled}' to '{new_status}'. "
            "Supplier can only transition: confirmed -> processing -> shipped. "
            "Other status transitions (picking_up, in_transit, delivered) are derived "
            "automatically from logistics partner scan events."
        ),
    )


def get_supplier_order_detail(order_id: int, current_user: dict, db: Session) -> dict:
    order_has_supplier_products = (
        db.query(OrderItem)
        .join(Product)
        .filter(
            OrderItem.order_id == order_id,
            Product.supplier_id == current_user["id"],
        )
        .first()
    )
    if not order_has_supplier_products:
        raise HTTPException(status_code=404, detail="Order not found or no products from this supplier")

    order = (
        db.query(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    shipments = _load_shipments_for_orders([cast(int, order.id)], db).get(cast(int, order.id), [])
    reconciled_status = reconcile_order_status(order, shipments)
    if order.status != reconciled_status:
        order.status = reconciled_status
        db.commit()
        db.refresh(order)

    customer = _load_users_by_ids([cast(int, order.user_id)], db).get(cast(int, order.user_id))
    order_financials = derive_order_financials(order)
    supplier_items = [
        {
            "id": item.id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "price": item.price,
            "product_name": item.product.name,
            "product_image": _normalize_media_path(item.product.image_url),
        }
        for item in order.items
        if item.product.supplier_id == current_user["id"]
    ]

    return {
        "id": order.id,
        "user_id": order.user_id,
        "total_amount": order_financials["total"],
        "status": order.status,
        "created_at": order.created_at.isoformat(),
        "customer_name": customer.username if customer else "Unknown",
        "customer_email": customer.email if customer else "",
        "customer_phone": order.customer_phone,
        "shipping_address": order.shipping_address,
        "delivery_location": order.delivery_location,
        "delivery_note": order.delivery_note,
        "items": supplier_items,
    }


def get_supplier_label_payload(order_id: int, current_user: dict, db: Session) -> dict:
    supplier_id = current_user["id"]
    order_has_supplier_products = (
        db.query(OrderItem)
        .join(Product)
        .filter(
            OrderItem.order_id == order_id,
            Product.supplier_id == supplier_id,
        )
        .first()
    )
    if not order_has_supplier_products:
        raise HTTPException(status_code=404, detail="Order not found or no products from this supplier")

    order = (
        db.query(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    supplier_user = db.query(User).filter(User.id == supplier_id).first()
    supplier_profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == supplier_id).first()

    shipment = (
        db.query(Shipment)
        .filter(Shipment.order_id == order_id, Shipment.supplier_id == supplier_id)
        .order_by(Shipment.created_at.desc())
        .first()
    )

    customer = db.query(User).filter(User.id == order.user_id).first()
    supplier_items = []
    supplier_subtotal = 0.0
    for item in order.items:
        if not item.product or item.product.supplier_id != supplier_id:
            continue
        unit_price = float(item.price or 0)
        quantity = int(item.quantity or 0)
        line_total = unit_price * quantity
        supplier_subtotal += line_total
        supplier_items.append(
            {
                "order_item_id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name,
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )

    has_shipment = shipment is not None
    shipment_id = shipment.id if shipment else None
    shipment_status = shipment.status if shipment else "awaiting_shipment"
    shipment_status_label_value = shipment_status_label(shipment_status, shipment=shipment) if shipment else "Awaiting Shipment"
    scan_code = (
        shipment.scan_code or f"SHIP-{shipment.id}"
        if shipment
        else f"ORDER-{order.id}"
    )
    tracking_number = shipment.tracking_number if shipment else None
    shipment_carrier = getattr(shipment, "carrier", None) if shipment else None
    carrier_name = cast(Any, getattr(shipment, "carrier_name", None)) if shipment else None
    if not carrier_name and shipment_carrier is not None:
        carrier_name = getattr(shipment_carrier, "name", None)
    packaged_at = cast(Any, getattr(shipment, "packaged_at", None)) if shipment else None
    order_created_at = cast(Any, getattr(order, "created_at", None))
    order_paid_at = cast(Any, getattr(order, "paid_at", None))
    order_financials = derive_order_financials(order)
    vat_amount = order_financials["vat"]
    shipping_amount = order_financials["shipping"]
    discount_amount = order_financials["discount"]
    total_amount = order_financials["total"]
    order_subtotal = order_financials["subtotal"]
    allocation_ratio = supplier_subtotal / order_subtotal if order_subtotal > 0 and supplier_subtotal > 0 else (1.0 if supplier_subtotal > 0 else 0.0)
    supplier_discount = round(discount_amount * allocation_ratio, 2)
    supplier_vat = round(vat_amount * allocation_ratio, 2)
    supplier_shipping = round(shipping_amount * allocation_ratio, 2)
    supplier_total = round(supplier_subtotal - supplier_discount + supplier_vat + supplier_shipping, 2)
    if supplier_total <= 0 and supplier_subtotal > 0:
        supplier_total = round(total_amount if allocation_ratio >= 0.999 else supplier_subtotal, 2)

    supplier_name = None
    if supplier_profile and supplier_profile.business_name:
        supplier_name = supplier_profile.business_name
    elif supplier_user and supplier_user.username:
        supplier_name = supplier_user.username
    else:
        supplier_name = f"Supplier #{supplier_id}"

    supplier_address_parts = [
        cast(Optional[str], getattr(supplier_profile, "address", None)) if supplier_profile else None,
        cast(Optional[str], getattr(supplier_profile, "city", None)) if supplier_profile else None,
        cast(Optional[str], getattr(supplier_profile, "region", None)) if supplier_profile else None,
        cast(Optional[str], getattr(supplier_profile, "country", None)) if supplier_profile else None,
        cast(Optional[str], getattr(supplier_profile, "postal_code", None)) if supplier_profile else None,
    ]
    supplier_address = ", ".join(str(part).strip() for part in supplier_address_parts if part and str(part).strip()) or None

    return {
        "order_id": order.id,
        "shipment_id": shipment_id,
        "has_shipment": has_shipment,
        "sheet_mode": "shipment" if has_shipment else "packing",
        "invoice_number": f"INV-{order.id:06d}",
        "order_status": order.status,
        "shipment_status": shipment_status,
        "shipment_status_label": shipment_status_label_value,
        "ordered_at": order_created_at.isoformat() if order_created_at else None,
        "paid_at": order_paid_at.isoformat() if order_paid_at else None,
        "payment_method": cast(Optional[str], getattr(order, "payment_method", None)),
        "supplier_name": supplier_name,
        "supplier_email": cast(Optional[str], getattr(supplier_user, "email", None)) if supplier_user else None,
        "supplier_phone": cast(Optional[str], getattr(supplier_profile, "phone_business", None)) if supplier_profile else None,
        "supplier_address": supplier_address,
        "supplier_website": cast(Optional[str], getattr(supplier_profile, "website", None)) if supplier_profile else None,
        "supplier_tax_id": cast(Optional[str], getattr(supplier_profile, "tax_id", None)) if supplier_profile else None,
        "supplier_logo_url": cast(Optional[str], getattr(supplier_profile, "logo_url", None)) if supplier_profile else None,
        "customer_name": customer.username if customer else f"Customer #{order.user_id}",
        "customer_email": customer.email if customer else None,
        "customer_phone": order.customer_phone,
        "shipping_address": order.shipping_address,
        "delivery_location": order.delivery_location,
        "delivery_note": order.delivery_note,
        "carrier_name": carrier_name,
        "tracking_number": tracking_number or (scan_code if shipment else None),
        "scan_code": scan_code,
        "current_hub": shipment.current_hub if shipment else None,
        "package_count": shipment.package_count if shipment else None,
        "package_weight_kg": shipment.package_weight_kg if shipment else None,
        "package_dimensions": shipment.package_dimensions if shipment else None,
        "packaged_at": packaged_at.isoformat() if packaged_at else None,
        "packaging_notes": shipment.packaging_notes if shipment else None,
        "subtotal": supplier_subtotal,
        "discount": supplier_discount,
        "vat": supplier_vat,
        "shipping": supplier_shipping,
        "total": supplier_total,
        "items": supplier_items,
    }


def upload_supplier_parcel_proof(
    order_id: int,
    file: UploadFile,
    notes: Optional[str],
    current_user: dict,
    db: Session,
) -> dict:
    supplier_id = current_user["id"]
    supplier_items = (
        db.query(OrderItem)
        .join(Product)
        .filter(
            OrderItem.order_id == order_id,
            Product.supplier_id == supplier_id,
        )
        .all()
    )
    if not supplier_items:
        raise HTTPException(status_code=404, detail="Order not found or no products from this supplier")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order_status = str(getattr(order, "status", "pending"))
    if order_status not in {"processing", "prepared"}:
        raise HTTPException(
            status_code=409,
            detail="Packed parcel proof can only be uploaded while the order is being prepared for dispatch",
        )

    shipment = (
        db.query(Shipment)
        .filter(Shipment.order_id == order_id, Shipment.supplier_id == supplier_id)
        .order_by(Shipment.created_at.desc())
        .first()
    )
    supplier_profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == supplier_id).first()
    pickup_location = next(
        (
            value for value in [
                getattr(supplier_profile, "address", None),
                getattr(supplier_profile, "city", None),
                getattr(supplier_profile, "region", None),
                getattr(supplier_profile, "country", None),
            ]
            if value
        ),
        None,
    )

    if shipment is None:
        shipment = Shipment(
            order_id=order.id,
            supplier_id=supplier_id,
            assigned_partner_id=None,
            status="processing",
            current_hub=pickup_location,
            packaged_at=utcnow(),
            packaged_by_user_id=supplier_id,
            packaging_notes=(notes or "").strip() or None,
            notes=(notes or "").strip() or None,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        db.add(shipment)
        db.flush()
        ensure_shipment_identifiers(shipment)
    else:
        if pickup_location and not getattr(shipment, "current_hub", None):
            shipment.current_hub = pickup_location
        shipment.status = "processing"
        shipment.packaged_at = getattr(shipment, "packaged_at", None) or utcnow()
        shipment.packaged_by_user_id = supplier_id
        shipment.packaging_notes = (notes or "").strip() or getattr(shipment, "packaging_notes", None)
        shipment.updated_at = utcnow()
        ensure_shipment_identifiers(shipment)

    if not db.query(ShipmentEvent).filter(
        ShipmentEvent.shipment_id == shipment.id,
        ShipmentEvent.event_type.in_(["supplier_prepared", "picked_from_supplier"]),
    ).first():
        db.add(
            ShipmentEvent(
                shipment_id=shipment.id,
                order_id=shipment.order_id,
                supplier_id=shipment.supplier_id,
                actor_user_id=current_user["id"],
                actor_role=current_user.get("role", "supplier"),
                event_type="supplier_prepared",
                status_after="processing",
                distribution_channel=getattr(shipment, "distribution_channel", None),
                location=shipment.current_hub,
                scan_code=shipment.scan_code,
                notes=(notes or "").strip() or "Packed parcel proof uploaded by supplier",
                created_at=utcnow(),
            )
        )

    order.status = "prepared"
    order_shipments = db.query(Shipment).filter(Shipment.order_id == order.id).all()
    order.status = reconcile_order_status(order, order_shipments)

    partner_for_notification = getattr(shipment, "assigned_partner", None)
    if partner_for_notification and getattr(partner_for_notification, "user_id", None):
        db.add(
            Notification(
                user_id=partner_for_notification.user_id,
                type="shipment_update",
                title="Pickup Ready",
                message=f"Order #{order.id} is prepared for pickup{f' from {shipment.current_hub}' if shipment.current_hub else ''}.",
                link="/logistics-partner/shipments",
            )
        )

    primary_item = supplier_items[0]
    image_url = _save_upload(file, supplier_id, db=db)
    media_base = os.path.basename(os.getenv("MEDIA_STORAGE_PATH", "uploads"))
    if image_url and not image_url.startswith(f"{media_base}/"):
        image_url = f"{media_base}/{image_url}"
    scan_code = shipment.scan_code if shipment and shipment.scan_code else f"ORDER-{order.id}"
    note_text = (notes or "").strip() or "Packed parcel proof uploaded by supplier"

    from domains.catalog.ports import create_verification

    verification = create_verification(
        {
            "product_id": primary_item.product_id,
            "order_id": order.id,
            "shipment_id": shipment.id if shipment else None,
            "verification_type": "supplier_dispatch",
            "result": "passed",
            "scan_code": scan_code,
            "image_urls": [image_url],
            "notes": note_text,
        },
        current_user,
        db,
    )
    db.commit()
    logistics_realtime_hub.publish(
        order_id=cast(int, getattr(shipment, "order_id")),
        payload={
            "type": "shipment.prepared",
            "shipment_id": cast(int, getattr(shipment, "id")),
            "order_id": cast(int, getattr(shipment, "order_id")),
            "assigned_partner_id": cast(Optional[int], getattr(shipment, "assigned_partner_id", None)),
            "status": "prepared",
            "tracking_number": cast(Optional[str], getattr(shipment, "tracking_number", None)),
            "current_hub": cast(Optional[str], getattr(shipment, "current_hub", None)),
            "scan_code": canonical_scan_code(shipment),
        },
        broadcast_all_partners=True,
    )
    return {
        **verification,
        "order_status": order.status,
        "shipment_status": "prepared" if shipment else None,
        "shipment_id": shipment.id if shipment else None,
        "assigned_partner_id": shipment.assigned_partner_id if shipment else None,
    }


# ── Products ──────────────────────────────────────────────────────────────────

