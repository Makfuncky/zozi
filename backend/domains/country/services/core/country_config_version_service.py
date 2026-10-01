"""Service layer for country config version management."""
from __future__ import annotations

import json
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.country.models.country_enhancements import CountryConfigVersion


def list_config_versions(
    code: str,
    config_type: str | None = None,
    status: str | None = None,
    db: Session = None,
) -> list[dict]:
    query = db.query(CountryConfigVersion).filter(
        CountryConfigVersion.country_code == code.upper(),
        not CountryConfigVersion.is_deleted,
    )
    if config_type:
        query = query.filter(CountryConfigVersion.config_type == config_type)
    if status:
        query = query.filter(CountryConfigVersion.status == status)
    versions = query.order_by(CountryConfigVersion.version.desc()).all()
    return [_serialize_version(v) for v in versions]


def get_config_version(code: str, version_id: int, db: Session = None) -> dict:
    version = (
        db.query(CountryConfigVersion)
        .filter(
            CountryConfigVersion.id == version_id,
            CountryConfigVersion.country_code == code.upper(),
            not CountryConfigVersion.is_deleted,
        )
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Config version not found")
    return _serialize_version(version)


def create_config_version(
    code: str,
    body: dict,
    current_user: dict | None,
    db: Session = None,
) -> dict:
    config_type = str(body.get("config_type", "")).strip()
    if not config_type:
        raise HTTPException(status_code=400, detail="config_type is required")

    payload = body.get("payload_json")
    if payload is None:
        raise HTTPException(status_code=400, detail="payload_json is required")

    if isinstance(payload, dict):
        payload = json.dumps(payload)

    max_ver = (
        db.query(CountryConfigVersion.version)
        .filter(
            CountryConfigVersion.country_code == code.upper(),
            CountryConfigVersion.config_type == config_type,
            not CountryConfigVersion.is_deleted,
        )
        .order_by(CountryConfigVersion.version.desc())
        .first()
    )
    next_version = (max_ver[0] + 1) if max_ver else 1

    version = CountryConfigVersion(
        country_code=code.upper(),
        config_type=config_type,
        version=next_version,
        payload_json=payload,
        status="draft",
        draft_by=current_user.get("id") if current_user else None,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return _serialize_version(version)


def update_config_version(
    code: str,
    version_id: int,
    body: dict,
    current_user: dict | None,
    db: Session = None,
) -> dict:
    version = (
        db.query(CountryConfigVersion)
        .filter(
            CountryConfigVersion.id == version_id,
            CountryConfigVersion.country_code == code.upper(),
            not CountryConfigVersion.is_deleted,
        )
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Config version not found")

    if version.status not in ("draft",):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot update version in '{version.status}' status",
        )

    if "payload_json" in body:
        payload = body["payload_json"]
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        version.payload_json = payload
    if "config_type" in body:
        version.config_type = str(body["config_type"]).strip()
    if "effective_from" in body:
        version.effective_from = body["effective_from"]

    if current_user:
        version.updated_by = current_user.get("id")
    db.commit()
    db.refresh(version)
    return _serialize_version(version)


def approve_config_version(
    code: str,
    version_id: int,
    current_user: dict | None,
    db: Session = None,
) -> dict:
    version = (
        db.query(CountryConfigVersion)
        .filter(
            CountryConfigVersion.id == version_id,
            CountryConfigVersion.country_code == code.upper(),
            not CountryConfigVersion.is_deleted,
        )
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Config version not found")
    if version.status != "draft":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve version in '{version.status}' status",
        )
    version.status = "approved"
    version.approved_by = current_user.get("id") if current_user else None
    db.commit()
    db.refresh(version)
    return _serialize_version(version)


def publish_config_version(
    code: str,
    version_id: int,
    current_user: dict | None,
    db: Session = None,
) -> dict:
    version = (
        db.query(CountryConfigVersion)
        .filter(
            CountryConfigVersion.id == version_id,
            CountryConfigVersion.country_code == code.upper(),
            not CountryConfigVersion.is_deleted,
        )
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Config version not found")
    if version.status not in ("draft", "approved"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot publish version in '{version.status}' status",
        )
    version.status = "published"
    version.published_at = datetime.utcnow()
    if not version.approved_by and current_user:
        version.approved_by = current_user.get("id")
    db.commit()
    db.refresh(version)
    return _serialize_version(version)


def archive_config_version(
    code: str,
    version_id: int,
    current_user: dict | None,
    db: Session = None,
) -> dict:
    version = (
        db.query(CountryConfigVersion)
        .filter(
            CountryConfigVersion.id == version_id,
            CountryConfigVersion.country_code == code.upper(),
            not CountryConfigVersion.is_deleted,
        )
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Config version not found")
    version.status = "archived"
    version.updated_by = current_user.get("id") if current_user else None
    db.commit()
    db.refresh(version)
    return _serialize_version(version)


def _serialize_version(v: CountryConfigVersion) -> dict:
    try:
        payload = json.loads(v.payload_json) if v.payload_json else {}
    except (json.JSONDecodeError, TypeError):
        payload = {}
    return {
        "id": v.id,
        "country_code": v.country_code,
        "config_type": v.config_type,
        "version": v.version,
        "payload_json": payload,
        "status": v.status,
        "draft_by": v.draft_by,
        "approved_by": v.approved_by,
        "published_at": v.published_at.isoformat() if v.published_at else None,
        "effective_from": v.effective_from.isoformat() if v.effective_from else None,
        "created_at": v.created_at.isoformat() if v.created_at else None,
        "updated_at": v.updated_at.isoformat() if v.updated_at else None,
    }
