
# -------------------------------------------------------------------
# FROM: admin_categories_service.py
# -------------------------------------------------------------------

"""Auto-migrated service logic from routers/admin_categories.py."""
from __future__ import annotations

from fastapi import Depends, HTTPException, Path, Query

from sqlalchemy.orm import Session

from modules.admin.routers.admin_controller import (
    archive_entity,
    bulk_archive_entities,
    bulk_restore_entities,
    restore_entity,
)

from infrastructure.database.database import get_db

from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest

from domains.governance.models.user import User
from domains.catalog.models.products import Category

from domains.catalog.services.categories.category_service import (
    create_category as create_category_model,
    update_category as update_category_model,
    delete_category as delete_category_model,
    reorder_categories as reorder_categories_model,
)

from domains.catalog.utils.category_tree import rebuild_category_paths

from domains.country.utils.country_rls import get_country_or_404

from infrastructure.utils.dependencies import require_admin

from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context

def list_categories(country_code: str, include_deleted: bool, page: int, page_size: int, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Category).filter(Category.country_code == country_code.upper())
        if not include_deleted: q = q.filter(Category.is_active == True)
        total = q.count()
        rows = q.order_by(Category.sort_order).offset((page - 1) * page_size).limit(page_size).all()
        return {"data": rows, "total": total, "page": page, "page_size": page_size}
    finally:
        clear_rls_context()

def create_category(country_code: str, name: str, slug: str, parent_id: int, sort_order: int, description: str, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        cat_data = {
            "name": name,
            "slug": slug,
            "parent_id": parent_id,
            "sort_order": sort_order,
            "description": description,
            "country_code": country_code.upper(),
        }
        cat = create_category_model(db, **cat_data)
        rebuild_category_paths(db)
        return cat
    finally:
        clear_rls_context()

def update_category(country_code: str, category_id: int, name: str, slug: str, parent_id: int, sort_order: int, description: str, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        cat = db.query(Category).filter(Category.id == category_id, Category.country_code == country_code.upper()).first()
        if not cat: raise HTTPException(404)
        updates = {}
        if name is not None: updates["name"] = name
        if slug is not None: updates["slug"] = slug
        if parent_id is not None: updates["parent_id"] = parent_id
        if sort_order is not None: updates["sort_order"] = sort_order
        if description is not None: updates["description"] = description
        cat = update_category_model(db, cat, updates)
        rebuild_category_paths(db)
        return cat
    finally:
        clear_rls_context()

def archive_category(country_code: str, category_id: int, payload: ArchiveRequest, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return archive_entity("category", category_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason if payload else None)
    finally:
        clear_rls_context()

def restore_category(country_code: str, category_id: int, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return restore_entity("category", category_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()

def reorder_categories(country_code: str, order: dict, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        reorder_categories_model(db, {int(k): v for k, v in order.items()})
        return {"message": "Categories reordered"}
    finally:
        clear_rls_context()

def bulk_archive_categories(country_code: str, payload: BulkActionRequest, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_archive_entities("category", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason)
    finally:
        clear_rls_context()

def bulk_restore_categories(country_code: str, payload: BulkActionRequest, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_restore_entities("category", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()

def delete_category(country_code: str, category_id: int, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        cat = db.query(Category).filter(Category.id == category_id, Category.country_code == country_code.upper()).first()
        if not cat: raise HTTPException(404)
        delete_category_model(db, cat)
        return {"message": "Category deleted"}
    finally:
        clear_rls_context()




# -------------------------------------------------------------------
# FROM: admin_email_service.py
# -------------------------------------------------------------------

"""Admin email management service."""
from __future__ import annotations

from sqlalchemy import case as sql_case
from sqlalchemy import func as sqlfunc
from sqlalchemy.orm import Session

from infrastructure.database.schemas import EmailCampaignCreate
from domains.comms.models.marketing import CampaignRecipient
from domains.comms.models.marketing import EmailCampaign
from domains.comms.models.marketing import NewsletterSubscriber

from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context


def list_all_campaigns(db: Session) -> list:
    """List all email campaigns across all countries (consolidated view)."""
    return db.query(EmailCampaign).order_by(EmailCampaign.created_at.desc()).limit(200).all()


def admin_email_metrics(db: Session) -> dict:
    """Consolidated email metrics across all countries."""
    total_subscribers = db.query(sqlfunc.count(NewsletterSubscriber.id)).filter(NewsletterSubscriber.is_active == True).scalar() or 0
    campaign_stats = db.query(
        sqlfunc.count(EmailCampaign.id).label("total"),
        sqlfunc.sum(sql_case((EmailCampaign.status == "sending", 1), else_=0)).label("active"),
        sqlfunc.count(CampaignRecipient.id).label("total_sent"),
    ).first()
    total_sent = int(campaign_stats.total_sent or 0)
    return {
        "total_subscribers": total_subscribers,
        "active_campaigns": int(campaign_stats.active or 0),
        "total_campaigns": int(campaign_stats.total or 0),
        "total_sent": total_sent,
    }


def list_campaigns(country_code: str, page: int, page_size: int, db: Session) -> dict:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(EmailCampaign).filter(EmailCampaign.country_code == country_code.upper())
        total = q.count()
        rows = q.order_by(EmailCampaign.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"data": rows, "total": total, "page": page, "page_size": page_size}
    finally:
        clear_rls_context()


def create_campaign(country_code: str, payload: EmailCampaignCreate, db: Session) -> EmailCampaign:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        allowed = {"name", "subject", "status", "send_at", "created_by", "country_code"}
        data = {k: v for k, v in payload.model_dump().items() if k in allowed and v is not None}
        data["country_code"] = country_code.upper()
        c = EmailCampaign(**data)
        db.add(c)
        db.commit()
        db.refresh(c)
        return c
    finally:
        clear_rls_context()


def delete_campaign(country_code: str, campaign_id: int, db: Session) -> dict:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        c = db.query(EmailCampaign).filter(EmailCampaign.id == campaign_id, EmailCampaign.country_code == country_code.upper()).first()
        if not c:
            raise ValueError("Campaign not found")
        db.delete(c)
        db.commit()
        return {"message": "Deleted"}
    finally:
        clear_rls_context()




# -------------------------------------------------------------------
# FROM: addresses_service.py
# -------------------------------------------------------------------

"""Auto-migrated service logic from routers/addresses.py."""
from __future__ import annotations
from domains.customers.services.customer_router_service import _serialize_address
from domains.customers.services.customer_router_service import _normalize_address_payload

from fastapi import Depends, HTTPException, status

from sqlalchemy.orm import Session

from infrastructure.utils.dependencies import get_current_user

from infrastructure.database.database import get_db

from domains.governance.models.core import Address

from domains.customers.services.commerce_write_service import create_address as create_address_model
from domains.customers.services.commerce_write_service import update_address as update_address_model
from domains.customers.services.commerce_write_service import delete_address as delete_address_model
from domains.customers.services.commerce_write_service import set_default_address as set_default_address_model
from domains.customers.services.commerce_write_service import unset_other_default_addresses

from domains.customers.services.commerce_read_service import list_user_addresses
from domains.customers.services.commerce_read_service import get_user_address



def _get_user_address(address_id: int, user_id: int, db: Session) -> Address:
    return get_user_address(db, address_id, user_id)

def list_addresses(limit: int, offset: int, current_user: dict, db: Session):
    rows = list_user_addresses(db, current_user["id"], limit, offset)
    return [_serialize_address(row) for row in rows]

def create_address(payload: dict, current_user: dict, db: Session):
    normalized = _normalize_address_payload(payload)
    user_id = int(current_user["id"])
    if normalized.get("is_default"):
        unset_other_default_addresses(db, user_id)
    address_data = {
        "user_id": user_id,
        "full_name": "Customer",
        "address_line1": normalized.get("street", ""),
        "city": normalized.get("city", ""),
        "state": normalized.get("state"),
        "postal_code": normalized.get("postal_code"),
        "country": normalized.get("country", "US"),
        "is_default": normalized.get("is_default", False),
    }
    if normalized.get("label"):
        address_data["label"] = normalized["label"]
    if normalized.get("phone"):
        address_data["phone"] = normalized["phone"]
    address = create_address_model(db, **address_data)
    return _serialize_address(address)

def update_address(address_id: int, payload: dict, current_user: dict, db: Session):
    address = _get_user_address(address_id, int(current_user["id"]), db)
    updates = _normalize_address_payload(payload, partial=True)
    if updates.get("is_default") is True:
        unset_other_default_addresses(db, int(current_user["id"]), address_id)
    if "street" in updates:
        updates.pop("street")
    address = update_address_model(db, address, updates)
    return _serialize_address(address)

def delete_address(address_id: int, current_user: dict, db: Session):
    address = _get_user_address(address_id, int(current_user["id"]), db)
    delete_address_model(db, address)
    return {"detail": "Deleted"}

def set_default_address(address_id: int, current_user: dict, db: Session):
    user_id = int(current_user["id"])
    unset_other_default_addresses(db, user_id, address_id)
    address = _get_user_address(address_id, user_id, db)
    address = set_default_address_model(db, address)
    return _serialize_address(address)



