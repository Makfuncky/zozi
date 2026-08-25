# ARCHIVED MODULE - DO NOT IMPORT FROM `domains/_parked`.
# Historical leftover from the ORD-SLICE god-domain decomposition.
# Resolution / live owner documented in RESOLVER.md PART 5 (Sec 37) and _parked_report.txt.
# Retained for reference only; this file is NOT part of the running application.
from __future__ import annotations
"""Auto-migrated service logic from routers/admin_categories.py."""

from fastapi import Depends, HTTPException, Path, Query

from sqlalchemy.orm import Session

from domains.governance.events import (
    publish_gov_bulk_archive_requested,
    publish_gov_bulk_restore_requested,
    publish_gov_entity_archive_requested,
    publish_gov_entity_restore_requested,
)

from infrastructure.database.database import get_db

from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest

from domains.governance.ports import User
from domains.catalog.ports import Category

from domains.catalog.services.products.products_write_service import create_category as create_category_model, update_category as update_category_model, delete_category as delete_category_model, reorder_categories as reorder_categories_model

from domains.catalog.utils.category_tree import rebuild_category_paths

from domains.country.ports import get_country_or_404

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
        return publish_gov_entity_archive_requested("category", category_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, payload.reason if payload else None, db=db)
    finally:
        clear_rls_context()

def restore_category(country_code: str, category_id: int, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return publish_gov_entity_restore_requested("category", category_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db=db)
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
        return publish_gov_bulk_archive_requested("category", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, payload.reason, db=db)
    finally:
        clear_rls_context()

def bulk_restore_categories(country_code: str, payload: BulkActionRequest, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return publish_gov_bulk_restore_requested("category", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db=db)
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

