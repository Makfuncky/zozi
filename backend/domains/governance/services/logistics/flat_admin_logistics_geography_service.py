"""Auto-migrated service logic from routers/admin_logistics_geography.py."""
from __future__ import annotations

from fastapi import Depends, HTTPException, Query, Path

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from domains.governance.models.user import User

from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest

from infrastructure.utils.dependencies import require_admin, require_super_admin

from domains.country.utils.country_rls import get_country_or_404

from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context

from modules.admin.routers.admin_controller import archive_entity, restore_entity, bulk_archive_entities, bulk_restore_entities, hard_delete_entity

from domains.logistics.services.partner_geography_service import approve_partner
from domains.logistics.services.partner_geography_service import list_partners
from domains.logistics.services.partner_geography_service import reject_partner
from domains.logistics.services.partner_geography_service import toggle_partner_active

def list_partners_route(country_code: str, include_deleted: bool, page: int, page_size: int, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return list_partners(db, country_code, include_deleted, page, page_size)
    finally:
        clear_rls_context()

def approve_partner_route(country_code: str, partner_id: int, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return approve_partner(db, partner_id, country_code)
    finally:
        clear_rls_context()

def reject_partner_route(country_code: str, partner_id: int, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return reject_partner(db, partner_id, country_code)
    finally:
        clear_rls_context()

def toggle_partner_active_route(country_code: str, partner_id: int, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return toggle_partner_active(db, partner_id, country_code)
    finally:
        clear_rls_context()

def archive_partner(country_code: str, partner_id: int, payload: ArchiveRequest, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return archive_entity("logistics_partner", partner_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason if payload else None)
    finally:
        clear_rls_context()

def restore_partner(country_code: str, partner_id: int, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return restore_entity("logistics_partner", partner_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()

def bulk_archive_partners(country_code: str, payload: BulkActionRequest, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_archive_entities("logistics_partner", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason)
    finally:
        clear_rls_context()

def bulk_restore_partners(country_code: str, payload: BulkActionRequest, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_restore_entities("logistics_partner", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()

def delete_partner_permanent(country_code: str, partner_id: int, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return hard_delete_entity("logistics_partner", partner_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()


