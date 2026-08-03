"""Country versioning router."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from data.db import get_db
from utils.dependencies import require_admin
from controllers.country.country_controller import (
    list_country_versions,
    approve_country_version,
    publish_country_version,
    rollback_country_to_version,
)

router = APIRouter()


@router.get("/admin/{code}/versions")
def get_versions(
    code: str,
    config_type: str | None = Query(None),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return list_country_versions(code, _, db, config_type=config_type)


@router.post("/admin/{code}/versions/{version_id}/approve")
def approve_version(
    code: str,
    version_id: int,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return approve_country_version(code, version_id, _, db)


@router.post("/admin/{code}/versions/{version_id}/publish")
def publish_version(
    code: str,
    version_id: int,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return publish_country_version(code, version_id, _, db)


@router.post("/admin/{code}/versions/{version_id}/rollback")
def rollback_version(
    code: str,
    version_id: int,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return rollback_country_to_version(code, version_id, _, db)