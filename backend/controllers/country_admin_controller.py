from __future__ import annotations

from typing import Any

from fastapi import Response

from controllers.country_controller import (
    _get_country_or_404,
    _require_admin,
    _require_country_access,
    _require_full_admin,
)
from services.geography.country_config_write_service import (
    add_country_city,
    archive_country,
    bulk_archive_countries,
    bulk_restore_countries,
    create_country_commission_rate,
    create_country_feature_flag,
    delete_country_city,
    delete_country_commission_rate,
    delete_country_feature_flag,
    hard_delete_country,
    patch_country_city,
    restore_country,
    toggle_country_active,
    update_country_feature_flag,
)
import structlog
logger = structlog.get_logger(__name__)


def create_feature_flag(code: str, body: dict, current_user: dict, db) -> dict:
    return create_country_feature_flag(db, code, body)


def update_feature_flag(code: str, key: str, body: dict, current_user: dict, db) -> dict:
    return update_country_feature_flag(db, code, key, body)


def delete_feature_flag(code: str, key: str, current_user: dict, db) -> Response:
    delete_country_feature_flag(db, code, key)
    return Response(status_code=204)


def add_city(code: str, body: dict, current_user: dict, db) -> dict:
    _require_admin(current_user)
    return add_country_city(db, code, body)


def patch_city(code: str, city_id: int, body: dict, current_user: dict, db) -> dict:
    _require_admin(current_user)
    return patch_country_city(db, code, city_id, body)


def delete_city(code: str, city_id: int, current_user: dict, db) -> Response:
    _require_admin(current_user)
    delete_country_city(db, code, city_id)
    return Response(status_code=204)


def toggle_active(code: str, current_user: dict, db) -> dict:
    _require_admin(current_user)
    return toggle_country_active(db, code)


def archive(code: str, current_user: dict, db) -> dict:
    _require_full_admin(current_user)
    _get_country_or_404(code, db)
    return archive_country(db, code, current_user.get("id"))


def restore(code: str, current_user: dict, db) -> dict:
    _require_full_admin(current_user)
    _get_country_or_404(code, db)
    return restore_country(db, code, current_user.get("id"))


def bulk_archive(payload: Any, current_user: dict, db) -> dict:
    _require_full_admin(current_user)
    return bulk_archive_countries(db, payload.ids, current_user.get("id"))


def bulk_restore(payload: Any, current_user: dict, db) -> dict:
    _require_full_admin(current_user)
    return bulk_restore_countries(db, payload.ids, current_user.get("id"))


def hard_delete(code: str, current_user: dict, db) -> Response:
    _require_full_admin(current_user)
    hard_delete_country(db, code)
    return Response(status_code=204)


def create_commission_rate(code: str, body: Any, current_user: dict, db) -> dict:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    _get_country_or_404(code, db)
    return create_country_commission_rate(db, code, body, current_user.get("id"))


def delete_commission_rate(code: str, tier: str, name: str, current_user: dict, db) -> dict:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    return delete_country_commission_rate(db, code, tier, name, current_user.get("id"))
