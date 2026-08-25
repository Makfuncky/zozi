
# -------------------------------------------------------------------
# FROM: banner_write_service.py
# -------------------------------------------------------------------

"""Backward-compatible re-export shim for banner write operations.

This module intentionally performs NO imports at module-load time. It used to
re-export handler functions from `controllers.banner_controller`, which created
an import-time circular-import cycle (`banner_controller` ->
`banner_write_service` -> `banner_controller`). Resolving names lazily via
module-level `__getattr__` breaks that cycle: the underlying controller module
is only imported on first attribute access, by which point the importing module
is fully initialised.
"""
from __future__ import annotations

import importlib
from typing import Any

_REEXPORTS: dict[str, tuple[str, str]] = {
    "create_banner": ("controllers.banner_controller", "create_banner"),
    "delete_banner": ("controllers.banner_controller", "delete_banner"),
    "reorder_banners": ("controllers.banner_controller", "reorder_banners"),
    "update_banner": ("controllers.banner_controller", "update_banner"),
}


def __getattr__(name: str) -> Any:
    if name in _REEXPORTS:
        module_path, attr = _REEXPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


from typing import Optional

from sqlalchemy.orm import Session

from domains.catalog.models.promotions import Banner
import structlog
logger = structlog.get_logger(__name__)


def _is_orm(obj, Model) -> bool:
    return isinstance(obj, Model)


def add_banner_if_missing(db: Session, banner=None, **kw) -> Banner:
    """Insert a banner only when no banner with the same (title, country_code) exists.

    ``banner`` may be a dict (legacy controller form) or omitted in favour of
    keyword arguments (spec form ``title``/``country_code``/``**kw``).
    """
    if isinstance(banner, dict):
        title = banner.get("title")
        country_code = banner.get("country_code")
        fields = dict(banner)
    else:
        title = kw.get("title")
        country_code = kw.get("country_code")
        fields = dict(kw)

    if not title:
        raise ValueError("title is required to add a banner")

    existing = db.query(Banner).filter(
        Banner.title == title,
        Banner.is_deleted.is_(False),
        Banner.country_code == country_code,
    ).first()
    if existing is not None:
        return existing

    record = Banner(**fields)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def bulk_add_banners(db: Session, banners: list) -> list:
    """Insert many banners, de-duplicating against existing titles per country."""
    created = []
    for item in banners or []:
        if not isinstance(item, dict):
            continue
        record = add_banner_if_missing(db, item)
        created.append(record)
    return created


def update_banner_image(db: Session, banner_or_id, image_url: str, filename: Optional[str] = None, **kw) -> Banner:
    """Update a banner's image (legacy controller form passes a banner object)."""
    if _is_orm(banner_or_id, Banner):
        record = banner_or_id
    else:
        record = db.get(Banner, int(banner_or_id))
        if record is None:
            raise ValueError(f"Banner {banner_or_id} not found")
    record.image_url = image_url
    if filename is not None and hasattr(record, "image_filename"):
        record.image_filename = filename
    if kw:
        for k, v in kw.items():
            if hasattr(record, k) and v is not None:
                setattr(record, k, v)
    db.commit()
    db.refresh(record)
    return record


# -------------------------------------------------------------------
# FROM: categories_service.py
# -------------------------------------------------------------------

"""Auto-migrated service logic from routers/categories.py."""
from __future__ import annotations

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Query

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from infrastructure.database.schemas import CategoryCreate, CategoryOut, CategoryUpdate, MessageResponse

from domains.governance.models.user import User
from domains.catalog.models.products import Category

from infrastructure.utils.dependencies import require_admin

from infrastructure.utils.slug import generate_slug

async def list_categories(active_only: bool, parent_id: Optional[int], page: int, page_size: int, db: Session):
    query = db.query(Category)
    if active_only:
        query = query.filter(Category.is_active == True)
    if parent_id is not None:
        query = query.filter(Category.parent_id == parent_id)
    total = query.count()
    items = query.order_by(Category.sort_order, Category.name).offset((page - 1) * page_size).limit(page_size).all()
    return {"data": items, "total": total, "page": page, "page_size": page_size}

async def get_category(category_ref: str, db: Session):
    cat = db.query(Category).filter(Category.slug == category_ref).first()
    if not cat and category_ref.isdigit():
        cat = db.query(Category).filter(Category.id == int(category_ref)).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat

async def create_category(payload: CategoryCreate, _admin: User, db: Session):
    slug = generate_slug(payload.slug or payload.name)
    if db.query(Category).filter(Category.slug == slug).first():
        raise HTTPException(status_code=409, detail="Category slug already exists")

    payload_data = payload.model_dump(exclude_none=True, exclude={"slug"})
    cat = Category(name=payload.name, slug=slug)
    for field_name, value in payload_data.items():
        if field_name == "name":
            continue
        setattr(cat, field_name, value)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

async def update_category(category_id: int, payload: CategoryUpdate, _admin: User, db: Session):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    updates = payload.model_dump(exclude_none=True)
    requested_slug = updates.pop("slug", None)
    if requested_slug is not None:
        slug = generate_slug(requested_slug)
        existing = db.query(Category).filter(Category.slug == slug, Category.id != category_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Category slug already exists")
        cat.slug = slug
    for k, v in updates.items():
        setattr(cat, k, v)
    db.commit()
    db.refresh(cat)
    return cat

async def list_categories_flat(_admin: User, db: Session, page: int, page_size: int):
    """Return all active categories with id, slug, name, parent_id, commission_rate for admin commission config."""
    query = db.query(Category).filter(Category.is_active == True)
    total = query.count()
    rows = query.order_by(Category.sort_order, Category.name).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "data": [
            {
                "id": c.id,
                "slug": c.slug,
                "name": c.name,
                "parent_id": c.parent_id,
                "commission_rate": float(c.commission_rate) if c.commission_rate is not None else None,
                "sort_order": c.sort_order,
            }
            for c in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }

async def delete_category(category_id: int, _admin: User, db: Session):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    cat.is_active = False
    db.commit()
    return MessageResponse(message="Category deactivated")




# -------------------------------------------------------------------
# FROM: customer_router_service.py
# -------------------------------------------------------------------

"""Customer router service - DB operations for address and customer health routers."""
from __future__ import annotations
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from domains.governance.models.core import Address
import structlog
logger = structlog.get_logger(__name__)


def _normalize_address_payload(payload: dict, *, partial: bool = False) -> dict:
    street = payload.get("street", payload.get("address_line1"))
    state = payload.get("state", payload.get("region"))
    postal_code = payload.get("postal_code", payload.get("zip"))
    normalized = {
        "label": payload.get("label"),
        "street": street,
        "city": payload.get("city"),
        "state": state,
        "postal_code": postal_code,
        "country": payload.get("country"),
        "is_default": payload.get("is_default"),
    }
    if partial:
        return {key: value for key, value in normalized.items() if value is not None}
    required = {"street": street, "city": payload.get("city"), "country": payload.get("country")}
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Missing required fields: {', '.join(missing)}")
    return normalized


def _serialize_address(address: Address) -> dict:
    return {
        "id": address.id,
        "user_id": address.user_id,
        "label": getattr(address, "label", None),
        "street": address.address_line1,
        "address_line1": address.address_line1,
        "address_line2": address.address_line2,
        "city": address.city,
        "state": address.state,
        "postal_code": address.postal_code,
        "country": address.country,
        "is_default": address.is_default,
        "full_name": address.full_name,
        "phone": address.phone,
        "created_at": address.created_at,
    }


def _get_user_address(address_id: int, user_id: int, db: Session) -> Address:
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == user_id).first()
    if address is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found.")
    return address


def list_addresses(db: Session, user_id: int, limit: int = 100, offset: int = 0) -> List[dict]:
    rows = (
        db.query(Address)
        .filter(Address.user_id == user_id)
        .order_by(Address.is_default.desc(), Address.created_at.asc())
        .offset(max(0, offset))
        .limit(min(max(1, limit), 100))
        .all()
    )
    return [_serialize_address(row) for row in rows]


def create_address(db: Session, user_id: int, payload: dict) -> dict:
    from domains.customers.services.commerce_write_service import create_address as create_address_db
    from domains.customers.services.commerce_write_service import unset_other_default_addresses
    
    normalized = _normalize_address_payload(payload)
    if normalized.get("is_default"):
        unset_other_default_addresses(db, user_id)
    address = Address(
        user_id=user_id,
        full_name="Customer",
        address_line1=normalized.get("street", ""),
        city=normalized.get("city", ""),
        state=normalized.get("state"),
        postal_code=normalized.get("postal_code"),
        country=normalized.get("country", "US"),
        is_default=normalized.get("is_default", False),
    )
    if normalized.get("label"):
        address.label = normalized["label"]
    if normalized.get("phone"):
        address.phone = normalized["phone"]
    return _serialize_address(create_address_db(db, **{
        "user_id": user_id,
        "full_name": "Customer",
        "address_line1": normalized.get("street", ""),
        "city": normalized.get("city", ""),
        "state": normalized.get("state"),
        "postal_code": normalized.get("postal_code"),
        "country": normalized.get("country", "US"),
        "is_default": normalized.get("is_default", False),
        "label": normalized.get("label"),
        "phone": normalized.get("phone"),
    }))


def update_address(db: Session, address_id: int, user_id: int, payload: dict) -> dict:
    from domains.customers.services.commerce_write_service import update_address as update_address_db
    from domains.customers.services.commerce_write_service import unset_other_default_addresses
    
    address = _get_user_address(address_id, user_id, db)
    updates = _normalize_address_payload(payload, partial=True)
    if updates.get("is_default") is True:
        unset_other_default_addresses(db, address.user_id, address_id)
    if "street" in updates:
        street_value = updates.pop("street")
        address.address_line1 = street_value
    return _serialize_address(update_address_db(db, address, updates))


def delete_address(db: Session, address_id: int, user_id: int) -> dict:
    from domains.customers.services.commerce_write_service import delete_address
    
    address = _get_user_address(address_id, user_id, db)
    delete_address(db, address)
    return {"detail": "Deleted"}


def set_default_address(db: Session, address_id: int, user_id: int) -> dict:
    from domains.customers.services.commerce_write_service import unset_other_default_addresses
    from domains.customers.services.commerce_write_service import set_default_address as set_default_address_db
    
    unset_other_default_addresses(db, user_id, address_id)
    address = _get_user_address(address_id, user_id, db)
    return _serialize_address(set_default_address_db(db, address))

# -------------------------------------------------------------------
# FROM: ghost_watchdog.py
# -------------------------------------------------------------------

"""
Ghost Employee Watchdog
Detects employees with no activity but still active in payroll
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from domains.hr.models.employee_models import Employee
from domains.hr.models.employee_models import EmployeeWorkLog
from domains.hr.models.employee_models import EmployeeAttendance
from domains.governance.models.user import User
from domains.finance.models.finance import TreasuryAccount

logger = logging.getLogger("zozi.ghost_watchdog")


class GhostEmployeeWatchdog:
    def __init__(self, db: Session):
        self.db = db
    
    def find_ghost_employees(self, days_threshold: int = 90) -> List[dict]:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)
        
        recent_attendance = self.db.query(EmployeeAttendance.employee_id).filter(
            EmployeeAttendance.scan_in_time >= cutoff_date
        ).distinct().subquery()
        
        recent_work_logs = self.db.query(EmployeeWorkLog.employee_id).filter(
            EmployeeWorkLog.work_date >= cutoff_date
        ).distinct().subquery()
        
        ghosts = self.db.query(Employee).filter(
            Employee.employment_status == "active",
            and_(
                ~Employee.id.in_(recent_attendance),
                ~Employee.id.in_(recent_work_logs)
            )
        ).all()

        ghost_ids = [emp.id for emp in ghosts]

        treasury_map: dict[int, "TreasuryAccount"] = {}
        if ghost_ids:
            treasury_map = {
                t.employee_id: t for t in self.db.query(TreasuryAccount).filter(
                    TreasuryAccount.employee_id.in_(ghost_ids)
                ).all()
            }

        last_attendance_map: dict[int, datetime] = {}
        last_worklog_map: dict[int, datetime] = {}
        if ghost_ids:
            att_rows = (
                self.db.query(
                    EmployeeAttendance.employee_id,
                    func.max(EmployeeAttendance.scan_in_time).label("max_scan"),
                )
                .filter(
                    EmployeeAttendance.employee_id.in_(ghost_ids)
                )
                .group_by(EmployeeAttendance.employee_id)
                .all()
            )
            last_attendance_map = {row.employee_id: row.max_scan for row in att_rows}

            wl_rows = (
                self.db.query(
                    EmployeeWorkLog.employee_id,
                    func.max(EmployeeWorkLog.work_date).label("max_date"),
                )
                .filter(
                    EmployeeWorkLog.employee_id.in_(ghost_ids)
                )
                .group_by(EmployeeWorkLog.employee_id)
                .all()
            )
            last_worklog_map = {row.employee_id: row.max_date for row in wl_rows}

        results = []
        for emp in ghosts:
            treasury = treasury_map.get(emp.id)
            last_attendance = last_attendance_map.get(emp.id)
            last_worklog = last_worklog_map.get(emp.id)
            activities = [a for a in [last_attendance, last_worklog] if a]
            last_active = max(activities) if activities else None

            results.append({
                "employee_id": emp.id,
                "employee_code": emp.employee_code,
                "name": f"{emp.first_name} {emp.last_name}",
                "last_active": last_active,
                "payroll_active": treasury is not None,
                "risk_level": "high" if treasury else "medium"
            })

        return results

    def flag_for_review(self, employee_id: int, reason: str) -> dict:
        return {
            "employee_id": employee_id,
            "flagged": True,
            "reason": reason,
            "requires_review": True
        }
    
    def generate_ghost_report(self, days_threshold: int = 90) -> dict:
        ghosts = self.find_ghost_employees(days_threshold)
        return {
            "report_generated_at": datetime.now(timezone.utc).isoformat(),
            "threshold_days": days_threshold,
            "ghost_count": len(ghosts),
            "ghosts": ghosts
        }


def get_ghost_watchdog(db: Session) -> GhostEmployeeWatchdog:
    return GhostEmployeeWatchdog(db)



# -------------------------------------------------------------------
# FROM: supplier_documents_service.py
# -------------------------------------------------------------------

"""Auto-migrated service logic from routers/supplier_documents.py."""
from __future__ import annotations

from __future__ import annotations

from fastapi import Depends, HTTPException, Query

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from infrastructure.database.schemas import SupplierDocumentOut

from domains.governance.models.user import User
from domains.comms.models.suppliers import SupplierDocument
from domains.comms.models.suppliers import SupplierProfile

from infrastructure.utils.dependencies import require_admin, require_supplier

def list_my_documents(
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Supplier profile not found")
    return (
        db.query(SupplierDocument)
        .filter(SupplierDocument.supplier_id == profile.id, SupplierDocument.is_deleted == False)  # noqa: E712
        .order_by(SupplierDocument.id.desc())
        .all()
    )

def list_all_documents(status_filter: str | None, _: User, db: Session):
    q = db.query(SupplierDocument).filter(SupplierDocument.is_deleted == False)  # noqa: E712
    if status_filter:
        q = q.filter(SupplierDocument.status == status_filter)
    return q.order_by(SupplierDocument.id.desc()).all()

def review_document(document_id: int, new_status: str, note: str | None, admin_user: User, db: Session):
    doc = db.query(SupplierDocument).filter(SupplierDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.status = new_status
    doc.review_note = note
    doc.reviewed_by = admin_user.id
    db.commit()
    return {"message": "Reviewed", "status": new_status}



