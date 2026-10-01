"""Admin country config-versioning router - thin HTTP layer delegating to the country domain service."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_admin
from rbac.dependencies import require_feature
from domains.country.services.core.country_config_version_service import (
    list_config_versions,
    get_config_version,
    create_config_version,
    update_config_version,
    approve_config_version,
    publish_config_version,
    archive_config_version,
)

router = APIRouter(prefix="/api/v1/admin/config-versions", tags=["admin", "country", "config-versions"])


@router.get("/{country_code}")
def list_config_versions_route(
    country_code: str = Path(...),
    config_type: str | None = Query(None),
    status: str | None = Query(None),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.versioning.approve")),
):
    return list_config_versions(country_code, config_type=config_type, status=status, db=db)


@router.post("/{country_code}")
def create_config_version_route(
    country_code: str = Path(...),
    body: dict = Body(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.versioning.approve")),
):
    return create_config_version(country_code, body, _, db)


@router.get("/{country_code}/{version_id}")
def get_config_version_route(
    country_code: str = Path(...),
    version_id: int = Path(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.versioning.approve")),
):
    return get_config_version(country_code, version_id, db)


@router.patch("/{country_code}/{version_id}")
def update_config_version_route(
    country_code: str = Path(...),
    version_id: int = Path(...),
    body: dict = Body(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.versioning.approve")),
):
    return update_config_version(country_code, version_id, body, _, db)


@router.post("/{country_code}/{version_id}/approve")
def approve_config_version_route(
    country_code: str = Path(...),
    version_id: int = Path(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.versioning.approve")),
):
    return approve_config_version(country_code, version_id, _, db)


@router.post("/{country_code}/{version_id}/publish")
def publish_config_version_route(
    country_code: str = Path(...),
    version_id: int = Path(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.versioning.approve")),
):
    return publish_config_version(country_code, version_id, _, db)


@router.post("/{country_code}/{version_id}/archive")
def archive_config_version_route(
    country_code: str = Path(...),
    version_id: int = Path(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.versioning.approve")),
):
    return archive_config_version(country_code, version_id, _, db)