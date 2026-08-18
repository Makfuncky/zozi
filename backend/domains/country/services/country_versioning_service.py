from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from domains.country.models.country_enhancements import CountryConfigVersion
from domains.logistics.services.logistics_partner_pricing import normalize_country_code


class VersionDraftBody(BaseModel):
    config_type: str
    payload: dict[str, Any] = {}


def _require_staff(current_user: dict) -> None:
    role = str(current_user.get('role') or '').lower()
    if role not in {'admin', 'country_head', 'country_manager', 'sub_admin'}:
        raise HTTPException(status_code=403, detail='Staff access required')


def _next_version(db: Session, country_code: str, config_type: str) -> int:
    latest = (
        db.query(CountryConfigVersion)
        .filter(
            CountryConfigVersion.country_code == country_code,
            CountryConfigVersion.config_type == config_type,
        )
        .order_by(CountryConfigVersion.version.desc())
        .first()
    )
    return int(getattr(latest, 'version', 0) or 0) + 1


def _safe_json(value):
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return value
    return value


def _serialize(row: CountryConfigVersion) -> dict:
    return {
        'id': row.id,
        'uuid': str(getattr(row, 'uuid', '')) or None,
        'country_code': row.country_code,
        'config_type': row.config_type,
        'version': row.version,
        'status': row.status,
        'payload': _safe_json(row.payload_json),
        'created_at': str(getattr(row, 'created_at', '') or ''),
    }


def list_versions(country_code: str, config_type: Optional[str], current_user: dict, db: Session) -> list:
    _require_staff(current_user)
    code = normalize_country_code(country_code)
    query = db.query(CountryConfigVersion).filter(CountryConfigVersion.country_code == code)
    if config_type:
        query = query.filter(CountryConfigVersion.config_type == config_type)
    rows = query.order_by(
        CountryConfigVersion.created_at.desc(), CountryConfigVersion.version.desc()
    ).all()
    return [_serialize(r) for r in rows]


def get_version(country_code: str, version_id: int, current_user: dict, db: Session) -> dict:
    _require_staff(current_user)
    code = normalize_country_code(country_code)
    row = (
        db.query(CountryConfigVersion)
        .filter(CountryConfigVersion.id == version_id, CountryConfigVersion.country_code == code)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail='Config version not found')
    return _serialize(row)


def create_version(country_code: str, body: "VersionDraftBody", current_user: dict, db: Session) -> dict:
    _require_staff(current_user)
    code = normalize_country_code(country_code)
    row = CountryConfigVersion(
        country_code=code,
        config_type=body.config_type,
        version=_next_version(db, code, body.config_type),
        payload_json=json.dumps(body.payload),
        status='draft',
        created_by=current_user.get('id'),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize(row)


def approve_version(country_code: str, version_id: int, current_user: dict, db: Session) -> dict:
    _require_staff(current_user)
    code = normalize_country_code(country_code)
    row = (
        db.query(CountryConfigVersion)
        .filter(CountryConfigVersion.id == version_id, CountryConfigVersion.country_code == code)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail='Config version not found')
    if row.status != 'draft':
        raise HTTPException(status_code=400, detail='Only draft versions can be approved')
    row.status = 'approved'
    db.commit()
    return _serialize(row)


def publish_version(country_code: str, version_id: int, current_user: dict, db: Session) -> dict:
    _require_staff(current_user)
    code = normalize_country_code(country_code)
    row = (
        db.query(CountryConfigVersion)
        .filter(CountryConfigVersion.id == version_id, CountryConfigVersion.country_code == code)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail='Config version not found')
    if row.status not in {'approved', 'draft'}:
        raise HTTPException(status_code=400, detail='Version must be approved before publishing')
    row.status = 'published'
    db.commit()
    return _serialize(row)


def rollback_version(country_code: str, version_id: int, current_user: dict, db: Session) -> dict:
    _require_staff(current_user)
    code = normalize_country_code(country_code)
    row = (
        db.query(CountryConfigVersion)
        .filter(CountryConfigVersion.id == version_id, CountryConfigVersion.country_code == code)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail='Config version not found')
    if row.status != 'published':
        raise HTTPException(status_code=400, detail='Only published versions can be rolled back')
    new_row = CountryConfigVersion(
        country_code=code,
        config_type=row.config_type,
        version=_next_version(db, code, row.config_type),
        payload_json=row.payload_json,
        status='draft',
        created_by=current_user.get('id'),
    )
    db.add(new_row)
    db.commit()
    db.refresh(new_row)
    return _serialize(new_row)
