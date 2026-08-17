"""Supplier write operations.



Assembled during the service-layer recovery: handlers that previously

lived inline in routers/controllers are centralized here so

``services.supplier.suppliers_write_service`` is a concrete module (no cycles).

Symbols without a prior implementation are stubbed explicitly.

"""

from __future__ import annotations



from typing import Any, Dict, Optional



from sqlalchemy.orm import Session



from models import (

    Notification,

    Payout,

    Shipment,

    ShipmentEvent,

    SupplierBankAccount,

    SupplierDocument,

    SupplierProfile,

    SupplierSettlement,

    User,

)

from services.common.write_helpers import add_and_flush, commit_only  # noqa: F401

from utils.datetime_utils import utcnow as _utcnow

import structlog

logger = structlog.get_logger(__name__)





def _filter_kwargs(model: Any, data: Dict[str, Any]) -> Dict[str, Any]:

    cols = {c.name for c in model.__table__.columns}

    return {k: v for k, v in data.items() if k in cols}





def _apply_updates(db: Session, obj: Any, updates: Optional[Dict[str, Any]] = None) -> Any:

    for key, value in (updates or {}).items():

        if hasattr(obj, key):

            setattr(obj, key, value)

    db.flush()

    return obj



# origin: services/suppliers_write_service.py

def add_and_flush(db: Session, obj: _M) -> _M:

    """Add ``obj`` to the session and flush so its generated columns (ids,

    defaults) become available without a full commit."""

    db.add(obj)

    db.flush()

    return obj



# origin: services/suppliers_write_service.py

def add_notification(

    db: Session,

    *,

    user_id: Optional[int] = None,

    type: Optional[str] = None,

    title: Optional[str] = None,

    message: Optional[str] = None,

    link: Optional[str] = None,

    **_kwargs: Any,

) -> Any:

    note = Notification(user_id=user_id, type=type, title=title, message=message, link=link)

    db.add(note)

    db.flush()

    return note





def _shipment_event_columns() -> set:

    return {c.name for c in ShipmentEvent.__table__.columns}



# origin: services/suppliers_write_service.py

def add_to_session(db: Session, model: Any) -> None:

    """Stage a model in the session without committing (caller commits later)."""

    db.add(model)



# origin: services/suppliers_write_service.py

def commit_only(db: Session) -> None:

    """Commit the current transaction without refreshing any specific object."""

    db.commit()



def create_payout(db: Session, **kwargs: Any) -> Any:

    payout = Payout(**_filter_kwargs(Payout, kwargs))

    db.add(payout)

    db.flush()

    return payout





# origin: controllers/logistics_controller.py

async def create_shipment(data: dict, current_user: dict, db: Session) -> dict:

    """Create a shipment record and move the order into the prepared handoff stage."""

    supplier_id = _require_supplier(current_user)



    order_id = data.get("order_id")

    if not order_id:

        raise HTTPException(status_code=422, detail="order_id is required")



    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:

        raise HTTPException(status_code=404, detail="Order not found")



    # Verify the order contains this supplier's products

    supplier_product_ids = {

        row[0] for row in db.query(Product.id).filter(

            Product.supplier_id == supplier_id,

        ).all()

    }

    has_supplier_item = any(i.product_id in supplier_product_ids for i in order.items)

    if not has_supplier_item and current_user.get("role") != "admin":

        raise HTTPException(status_code=403, detail="This order does not contain your products")



    # Prevent duplicate shipments

    existing = db.query(Shipment).filter(

        Shipment.order_id == order_id,

        Shipment.supplier_id == supplier_id,

        Shipment.status.notin_(["failed", "returned"]),

    ).first()

    if existing:

        raise HTTPException(

            status_code=409,

            detail=f"Shipment already exists for this order (ID: {existing.id}, status: {existing.status})",

        )



    current_hub = str(data.get("current_hub", "")).strip() or None

    if not current_hub:

        supplier_profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == supplier_id).first()

        current_hub = next(

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



    shipment = Shipment(

        order_id=order_id,

        supplier_id=supplier_id,

        assigned_partner_id=None,

        carrier_id=None,

        carrier_name=None,

        tracking_number=None,

        status="processing",

        distribution_channel=None,

        current_hub=current_hub,

        estimated_delivery=None,

        notes=str(data.get("notes", "")).strip() or None,

        created_at=_utcnow(),

    )

    _apply_package_metadata(shipment, cast(dict[str, Any], data), current_user.get("id"))

    add_and_flush(db, shipment)



    tracking_number, shipment_scan_code = ensure_shipment_identifiers(shipment)



    # Update order tracking_number if provided

    order_tracking_number = cast(Optional[str], getattr(order, "tracking_number", None))

    if tracking_number and not order_tracking_number:

        setattr(order, "tracking_number", tracking_number)

    setattr(order, "status", "processing")



    shipment_status = cast(str, getattr(shipment, "status"))

    shipment_notes = cast(Optional[str], getattr(shipment, "notes", None))



    event = ShipmentEvent(

        shipment_id=shipment.id,

        order_id=order_id,

        supplier_id=supplier_id,

        actor_user_id=current_user.get("id"),

        actor_role=current_user.get("role", "supplier"),

        event_type="packaging_started",

        status_after=shipment_status,

        distribution_channel=None,

        location=current_hub,

        scan_code=shipment_scan_code,

        notes=shipment_notes,

        created_at=_utcnow(),

    )

    add_and_flush(db, event)



    audit_log(

        db=db,

        action=AuditAction.ORDER_STATUS_CHANGED,

        user_id=current_user.get("id"),

        username=current_user.get("username"),

        user_role=current_user.get("role"),

        resource_type="shipment",

        resource_id=cast(int, getattr(shipment, "id")),

        details={

            "event": "shipment_created",

            "order_id": order_id,

            "status": shipment_status,

            "distribution_channel": None,

            "hub": current_hub,

            "assigned_partner_id": shipment.assigned_partner_id,

            "package_count": shipment.package_count,

            "package_weight_kg": shipment.package_weight_kg,

            "tracking_number": tracking_number,

            "scan_code": shipment_scan_code,

        },

        status="success",

    )



    commit_only(db)

    refresh_model(db, shipment)

    refresh_model(db, event)

    _publish_supplier_shipment_update(shipment, event_type="shipment.packaging_started")

    logger.info("Shipment created: order %d by supplier %d → tracking %s", order_id, supplier_id, tracking_number)



    # Auto-create invoice for this shipment if one doesn't exist yet (non-blocking)

    try:

        from services.finance.invoice_service import create_invoice_from_order

        from models import Invoice

        has_invoice = db.query(Invoice).filter(

            Invoice.order_id == order_id,

            Invoice.supplier_id == supplier_id,

            Invoice.invoice_type == "sale",

        ).first()

        if not has_invoice:

            create_invoice_from_order(

                data={"order_id": order_id, "shipment_id": shipment.id},

                current_user=current_user,

                db=db,

            )

            logger.info("Auto-invoice created for order %d supplier %d", order_id, supplier_id)

    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:

        logger.warning("Auto-invoice creation failed (non-fatal): %s", exc)



    return _serialize_shipment(shipment)



# origin: services/suppliers_write_service.py

def create_shipment_event(db: Session, **kwargs: Any) -> Any:

    cols = _shipment_event_columns()

    data = {k: v for k, v in kwargs.items() if k in cols}

    event = ShipmentEvent(**data)

    db.add(event)

    db.flush()

    return event



# origin: services/suppliers_write_service.py

def create_supplier_bank_account(db: Session, **kwargs: Any) -> Any:

    account = SupplierBankAccount(**_filter_kwargs(SupplierBankAccount, kwargs))

    db.add(account)

    db.flush()

    return account



# origin: services/suppliers_write_service.py

def create_supplier_document(

    db: Session,

    *,

    supplier_id: int,

    doc_type: str,

    document_name: Optional[str] = None,

    file_url: str,

    status: str = "pending",

    expires_at: Optional[Any] = None,

) -> Any:

    doc = SupplierDocument(

        supplier_id=supplier_id,

        doc_type=doc_type,

        document_name=document_name,

        file_url=file_url,

        status=status,

        expires_at=expires_at,

    )

    db.add(doc)

    db.flush()

    return doc



def create_supplier_profile(db: Session, *, user_id: int, **kwargs: Any) -> Any:

    profile = SupplierProfile(user_id=user_id, **_filter_kwargs(SupplierProfile, kwargs))

    db.add(profile)

    db.flush()

    return profile





# origin: services/suppliers_write_service.py

def create_supplier_settlement(db: Session, **kwargs: Any) -> Any:

    settlement = SupplierSettlement(**_filter_kwargs(SupplierSettlement, kwargs))

    db.add(settlement)

    db.flush()

    return settlement



# origin: services/suppliers_write_service.py

def delete_payout(db: Session, payout: Any) -> Any:

    payout.is_deleted = True

    payout.deleted_at = _utcnow()

    db.flush()

    return payout



# origin: services/suppliers_write_service.py

def delete_shipment(db: Session, shipment: Any) -> Any:

    shipment.is_deleted = True

    shipment.deleted_at = _utcnow()

    db.flush()

    return shipment





# origin: services/suppliers_write_service.py

def delete_shipment_event(db: Session, event: Any) -> Any:

    event.is_deleted = True

    event.deleted_at = _utcnow()

    db.flush()

    return event



# origin: services/suppliers_write_service.py

def delete_supplier_bank_account(db: Session, account: Any) -> Any:

    account.is_deleted = True

    account.deleted_at = _utcnow()

    db.flush()

    return account



# origin: services/suppliers_write_service.py

def delete_supplier_document(db: Session, doc: Any) -> Any:

    doc.is_deleted = True

    doc.deleted_at = _utcnow()

    db.flush()

    return doc



# origin: services/suppliers_write_service.py

def delete_supplier_profile(db: Session, profile: Any) -> Any:

    profile.is_deleted = True

    profile.deleted_at = _utcnow()

    db.flush()

    return profile



# origin: services/suppliers_write_service.py

def delete_supplier_settlement(db: Session, settlement: Any) -> Any:

    settlement.is_deleted = True

    settlement.deleted_at = _utcnow()

    db.flush()

    return settlement



# origin: services/suppliers_write_service.py

def flush_session(db: Session) -> None:

    db.flush()





# origin: services/suppliers_write_service.py

def refresh_model(db: Session, obj: Any) -> Any:

    db.refresh(obj)

    return obj



# origin: services/suppliers_write_service.py

def update_payout(db: Session, payout: Any, updates: Optional[Dict[str, Any]] = None) -> Any:

    return _apply_updates(db, payout, updates)



def update_shipment(db: Session, shipment: Any, updates: Optional[Dict[str, Any]] = None) -> Any:

    return _apply_updates(db, shipment, updates)





# origin: services/suppliers_write_service.py

def update_shipment_event(db: Session, event: Any, updates: Optional[Dict[str, Any]] = None) -> Any:

    return _apply_updates(db, event, updates)



# origin: services/suppliers_write_service.py

def update_supplier_bank_account(db: Session, account: Any, updates: Optional[Dict[str, Any]] = None) -> Any:

    return _apply_updates(db, account, updates)



# origin: services/suppliers_write_service.py

def update_supplier_document(db: Session, doc: Any, updates: Optional[Dict[str, Any]] = None) -> Any:

    return _apply_updates(db, doc, updates)



# origin: controllers/supplier_controller.py

def update_supplier_profile(profile_update: dict, current_user: dict, db: Session) -> dict:

    supplier = db.query(User).filter(User.id == current_user["id"]).first()

    if not supplier:

        raise HTTPException(status_code=404, detail="Supplier not found")



    from models import SupplierProfile as SP

    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()

    if not profile:

        profile = create_supplier_profile(db=db, user_id=current_user["id"], verification_status="pending")



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

                logger.exception("update_supplier_profile_failed", error=str(exc))

                raise HTTPException(status_code=400, detail="Established year must be a number") from exc



    commit_only(db)

    refresh_model(db, supplier)

    return get_supplier_profile(current_user, db)



# origin: services/suppliers_write_service.py

def update_supplier_settlement(db: Session, settlement: Any, updates: Optional[Dict[str, Any]] = None) -> Any:

    return _apply_updates(db, settlement, updates)