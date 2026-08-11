"""controllers.geography.country_versioning_controller controller (CONTROLLERS layer).

Coordinates the country-config-version HTTP contract and delegates ALL
persistence to services.geography.country_versioning_service. It must not
issue db.query directly. The HTTP contract is declared with
routers.generated.auto_router decorators so the auto-router emits the surface
router that main._load_routers auto-discovers.

Both the /api/v1/admin and /api/v1 mount points are preserved (the legacy
hand-written routers included the versioning router under each prefix).
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from routers.generated.auto_router import get, post

from services.geography.country_versioning_service import (
    VersionDraftBody, approve_version, create_version, get_version, list_versions,
    publish_version, rollback_version,
)
import structlog
logger = structlog.get_logger(__name__)


@get("/api/v1/admin/config-versions/{country_code}", deps=["db", "user"], query=["config_type"], tags=["country-versioning"])
def list_config_versions(country_code: str, config_type: Optional[str] = None, current_user: dict = None, db: Session = None) -> list:
    return list_versions(country_code, config_type, current_user, db)


@get("/api/v1/config-versions/{country_code}", deps=["db", "user"], query=["config_type"], tags=["country-versioning"])
def list_config_versions_public(country_code: str, config_type: Optional[str] = None, current_user: dict = None, db: Session = None) -> list:
    return list_versions(country_code, config_type, current_user, db)


@get("/api/v1/admin/config-versions/{country_code}/{version_id}", deps=["db", "user"], tags=["country-versioning"])
def get_config_version(country_code: str, version_id: int, current_user: dict = None, db: Session = None) -> dict:
    return get_version(country_code, version_id, current_user, db)


@get("/api/v1/config-versions/{country_code}/{version_id}", deps=["db", "user"], tags=["country-versioning"])
def get_config_version_public(country_code: str, version_id: int, current_user: dict = None, db: Session = None) -> dict:
    return get_version(country_code, version_id, current_user, db)


@post("/api/v1/admin/config-versions/{country_code}", deps=["db", "user"], body=VersionDraftBody, tags=["country-versioning"])
def create_config_version(country_code: str, body: VersionDraftBody, current_user: dict = None, db: Session = None) -> dict:
    return create_version(country_code, body, current_user, db)


@post("/api/v1/config-versions/{country_code}", deps=["db", "user"], body=VersionDraftBody, tags=["country-versioning"])
def create_config_version_public(country_code: str, body: VersionDraftBody, current_user: dict = None, db: Session = None) -> dict:
    return create_version(country_code, body, current_user, db)


@post("/api/v1/admin/config-versions/{country_code}/{version_id}/approve", deps=["db", "user"], tags=["country-versioning"])
def approve_config_version(country_code: str, version_id: int, current_user: dict = None, db: Session = None) -> dict:
    return approve_version(country_code, version_id, current_user, db)


@post("/api/v1/config-versions/{country_code}/{version_id}/approve", deps=["db", "user"], tags=["country-versioning"])
def approve_config_version_public(country_code: str, version_id: int, current_user: dict = None, db: Session = None) -> dict:
    return approve_version(country_code, version_id, current_user, db)


@post("/api/v1/admin/config-versions/{country_code}/{version_id}/publish", deps=["db", "user"], tags=["country-versioning"])
def publish_config_version(country_code: str, version_id: int, current_user: dict = None, db: Session = None) -> dict:
    return publish_version(country_code, version_id, current_user, db)


@post("/api/v1/config-versions/{country_code}/{version_id}/publish", deps=["db", "user"], tags=["country-versioning"])
def publish_config_version_public(country_code: str, version_id: int, current_user: dict = None, db: Session = None) -> dict:
    return publish_version(country_code, version_id, current_user, db)


@post("/api/v1/admin/config-versions/{country_code}/{version_id}/rollback", deps=["db", "user"], tags=["country-versioning"])
def rollback_config_version(country_code: str, version_id: int, current_user: dict = None, db: Session = None) -> dict:
    return rollback_version(country_code, version_id, current_user, db)


@post("/api/v1/config-versions/{country_code}/{version_id}/rollback", deps=["db", "user"], tags=["country-versioning"])
def rollback_config_version_public(country_code: str, version_id: int, current_user: dict = None, db: Session = None) -> dict:
    return rollback_version(country_code, version_id, current_user, db)
