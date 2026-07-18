"""
Country Config Draft-to-Publish Workflow Controller
Implements versioning and safe configuration management
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from db.database import get_db
from models import CountryConfig, CountryConfigVersion
from controllers.auth_controller import get_current_user
from utils.audit import audit_log, AuditAction
from services.downstream_hooks import invalidate_country_cache


router = APIRouter()


def _require_admin(current_user: dict):
    if current_user.get("role") not in {"admin", "super_admin"}:
        raise HTTPException(status_code=403, detail="Admin access required")


def _get_country_or_404(code: str, db: Session):
    from models import CountryConfig
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
    
    version = CountryConfigVersion(
        country_code=code.upper(),
        config_type=config_type,
        version=version_number,
        status='draft',
        payload_json=draft_data,
        draft_by=current_user.get('id'),
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    
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
    
    version.status = 'approved'
    version.approved_by = current_user.get('id')
    
    db.commit()
    
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
    
    version.status = 'published'
    version.published_at = datetime.utcnow()
    version.approved_by = current_user.get('id')
    
    db.commit()
    
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
    
    rollback_version = CountryConfigVersion(
        country_code=code.upper(),
        config_type=version.config_type,
        version=1,
        status='rolled_back',
        payload_json=version.payload_json,
        draft_by=current_user.get('id'),
        approved_by=current_user.get('id'),
    )
    db.add(rollback_version)
    db.commit()
    
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

