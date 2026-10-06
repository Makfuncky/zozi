"""Re-export shim for logistics_partner_service."""
from domains.logistics.ports import review_logistics_partner_service_area, create_logistics_partner_service_area, update_logistics_partner_service_area, delete_logistics_partner_service_area

__all__ = ['review_logistics_partner_service_area', 'create_logistics_partner_service_area',
           'update_logistics_partner_service_area', 'delete_logistics_partner_service_area']


def get_partner_shipments(current_user: dict, db, *, status: str | None = None,
                          page: int = 1, page_size: int = 30) -> dict:
    """Shipments visible to the calling logistics partner, newest first.

    modules/logistics/routers/logistics.py calls this, but only the service-area
    CRUD helpers were re-exported, so GET /api/v1/logistics/logistics/shipments
    raised AttributeError: ... has no attribute 'get_partner_shipments'.
    """
    from sqlalchemy import func, select

    from domains.logistics.models.logistics_entities import Shipment

    query = select(Shipment)
    count_q = select(func.count()).select_from(Shipment)
    partner_id = _partner_id_for(current_user)
    if partner_id is not None:
        query = query.where(Shipment.assigned_partner_id == partner_id)
        count_q = count_q.where(Shipment.assigned_partner_id == partner_id)
    if status:
        query = query.where(Shipment.status_code == status)
        count_q = count_q.where(Shipment.status_code == status)
    total = db.execute(count_q).scalar() or 0
    rows = (db.execute(query.order_by(Shipment.created_at.desc())
                      .offset(max(page - 1, 0) * page_size).limit(page_size))
            .scalars().all())
    return {"items": [_shipment_dict(r) for r in rows], "total": total, "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if page_size else 0}


def _partner_id_for(current_user) -> int | None:
    if not isinstance(current_user, dict):
        return None
    if current_user.get("role") in ("admin", "staff", "super_admin"):
        return None
    raw = current_user.get("logistics_partner_id") or current_user.get("partner_id")
    if raw in (None, ""):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _shipment_dict(row) -> dict:
    return {"id": row.id, "order_id": row.order_id, "supplier_id": row.supplier_id,
            "assigned_partner_id": row.assigned_partner_id,
            "tracking_number": row.tracking_number, "carrier_name": row.carrier_name,
            "status": row.status_code, "status_code": row.status_code,
            "package_count": row.package_count, "package_weight_kg": row.package_weight_kg,
            "current_hub": row.current_hub, "country_code": row.country_code,
            "created_at": row.created_at, "updated_at": row.updated_at}
