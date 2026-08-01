"""
Country Config Draft-to-Publish Workflow Router
Implements versioning and safe configuration management
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dependencies.auth import get_current_user
from models import CountryConfig, CountryConfigVersion
from services.country_write_service import (
    create_country_config_version as create_draft_version,
    update_country_config_version_status as update_version_status,
    create_rollback_version as create_rollback_row,
)
from services.downstream_hooks import invalidate_country_cache
from utils.audit import AuditAction, audit_log
from utils.dependencies import get_db

router = APIRouter()


def _require_admin(current_user: dict):
    if current_user.get("role") not in {"admin", "super_admin"}:
        raise HTTPException(status_code=403, detail="Admin access required")


def _get_country_or_404(code: str, db: Session):
    country = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country


@router.post("/admin/countries/{code}/draft")
def create_draft(
    code: str,
    draft_data: dict,
    config_type: str = "general",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _require_admin(current_user)
    country = _get_country_or_404(code, db)
    
    existing_versions = db.query(CountryConfigVersion).filter(
        CountryConfigVersion.country_code == code.upper(),
        CountryConfigVersion.config_type == config_type
    ).all()
    version_number = len(existing_versions) + 1
    
    version = create_draft_version(
        db,
        country_code=code.upper(),
        config_type=config_type,
        version=version_number,
        payload_json=draft_data,
        status='draft',
        draft_by=current_user.get('id'),
    )
    
    audit_log(
        db,
        actor_id=current_user.get('id'),
        action=AuditAction.CREATE_DRAFT,
        entity='country_config',
        entity_key=code.upper(),
        details={'version_id': version.id, 'config_type': config_type}
    )
    
    return {"version_id": version.id, "status": "draft", "version": version_number}


@router.post("/admin/countries/{code}/approve")
def approve_draft(
    code: str,
    version_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _require_admin(current_user)
    country = _get_country_or_404(code, db)
    
    version = db.query(CountryConfigVersion).filter(
        CountryConfigVersion.id == version_id,
        CountryConfigVersion.country_code == code.upper()
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    if version.status != 'draft':
        raise HTTPException(status_code=400, detail="Version must be in draft status")
    
    update_version_status(db, version, {'status': 'approved', 'approved_by': current_user.get('id')})
    
    audit_log(
        db,
        actor_id=current_user.get('id'),
        action=AuditAction.APPROVE,
        entity='country_config',
        entity_key=code.upper(),
        details={'version_id': version.id}
    )
    
    return {"status": "approved", "version_id": version.id}


@router.post("/admin/countries/{code}/publish")
def publish_version(
    code: str,
    version_id: int,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _require_admin(current_user)
    country = _get_country_or_404(code, db)
    
    version = db.query(CountryConfigVersion).filter(
        CountryConfigVersion.id == version_id,
        CountryConfigVersion.country_code == code.upper()
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    if version.status != 'approved':
        raise HTTPException(status_code=400, detail="Version must be approved first")
    
    update_version_status(db, version, {
        'status': 'published',
        'published_at': datetime.utcnow(),
        'approved_by': current_user.get('id')
    })
    
    invalidate_country_cache(code.upper())
    
    audit_log(
        db,
        actor_id=current_user.get('id'),
        action=AuditAction.PUBLISH,
        entity='country_config',
        entity_key=code.upper(),
        details={'version_id': version.id, 'config_type': version.config_type, 'reason': reason}
    )
    
    return {"status": "published", "version_id": version.id}


@router.post("/admin/countries/{code}/rollback")
def rollback_to_version(
    code: str,
    version_id: int,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _require_admin(current_user)
    country = _get_country_or_404(code, db)
    
    version = db.query(CountryConfigVersion).filter(
        CountryConfigVersion.id == version_id,
        CountryConfigVersion.country_code == code.upper()
    ).first()
    
    if not version or version.status != 'published':
        raise HTTPException(status_code=404, detail="Published version not found")
    
    rollback_version = create_rollback_row(
        db,
        country_code=code.upper(),
        config_type=version.config_type,
        version=1,
        payload_json=version.payload_json,
        draft_by=current_user.get('id'),
        approved_by=current_user.get('id'),
    )
    
    invalidate_country_cache(code.upper())
    
    audit_log(
        db,
        actor_id=current_user.get('id'),
        action=AuditAction.ROLLBACK,
        entity='country_config',
        entity_key=code.upper(),
        details={'from_version': version.id, 'to_version': rollback_version.id, 'reason': reason}
    )
    
    return {"status": "rolled_back", "new_version_id": rollback_version.id}
