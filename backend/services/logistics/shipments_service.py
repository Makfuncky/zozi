"""Shipments router logic, extracted behind the service layer (clears LC1/W1).

Each function owns its database session via ``data.db.get_db_context`` so the
router layer never injects or touches a SQLAlchemy session directly.
"""
from typing import List, Optional

from fastapi import HTTPException


def get_shipment(shipment_id: int):
    from data.db import get_db_context
    from data.models import Shipment

    with get_db_context() as db:
        s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not s:
            raise HTTPException(404, "Not found")
        return s


def track_shipment(tracking_number: str):
    from data.db import get_db_context
    from data.models import Shipment

    with get_db_context() as db:
        s = db.query(Shipment).filter(Shipment.tracking_number == tracking_number).first()
        if not s:
            raise HTTPException(404, "Tracking number not found")
        return s


def create_shipment(payload):
    from data.db import get_db_context
    from data.models import Shipment
    from data.services_write_helpers import add_and_flush, commit_only, refresh_only

    with get_db_context() as db:
        s = Shipment(**payload.model_dump())
        add_and_flush(db, s)
        commit_only(db)
        refresh_only(db, s)
        return s


def update_shipment(shipment_id: int, payload):
    from data.db import get_db_context
    from data.models import Shipment
    from data.services_write_helpers import commit_only, refresh_only

    with get_db_context() as db:
        s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not s:
            raise HTTPException(404, "Not found")
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(s, k, v)
        commit_only(db)
        refresh_only(db, s)
        return s


def add_event(shipment_id: int, payload, current_user_id: int):
    from data.db import get_db_context
    from data.models import Shipment, ShipmentEvent
    from data.services_write_helpers import add_and_flush, commit_only, refresh_only

    with get_db_context() as db:
        s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not s:
            raise HTTPException(404, "Not found")
        event = ShipmentEvent(shipment_id=shipment_id, created_by=current_user_id, **payload.model_dump())
        add_and_flush(db, event)
        commit_only(db)
        refresh_only(db, event)
        return event
