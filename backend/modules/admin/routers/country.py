"""Admin country router — thin HTTP layer delegating to country domain services."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Path, Body, HTTPException, status
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_admin
from rbac.dependencies import require_feature
from domains.country.services.core.country_service import (
    list_public_countries,
    get_public_country_config,
    create_admin_country,
    get_admin_country,
    update_country_identity,
)
from domains.country.services.core.country_config_admin_service import (
    list_cities as _list_cities,
    add_city as _add_city,
    update_city as _update_city,
    delete_city as _delete_city,
    list_staff as _list_staff,
    assign_staff as _assign_staff,
    remove_staff as _remove_staff,
    list_tax_rates as _list_tax_rates,
    set_tax_rate as _set_tax_rate,
    send_country_communication as _send_country_communication,
    list_communications as _list_communications,
    mark_communication_read as _mark_communication_read,
    toggle_country_active as _toggle_country_active,
    archive_country as _archive_country,
    restore_country as _restore_country,
    bulk_archive_countries as _bulk_archive_countries,
    bulk_restore_countries as _bulk_restore_countries,
    hard_delete_country as _hard_delete_country,
    list_country_commission_rates as _list_country_commission_rates,
    create_country_commission_rate as _create_country_commission_rate,
    delete_country_commission_rate as _delete_country_commission_rate,
)

router = APIRouter(prefix="/api/v1/admin/country", tags=["admin", "country"])


def _not_implemented(name: str):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"TODO: {name} not yet wired to a domain service",
    )


# Backwards-compatible aliases. The country service exposes both
# ``name(...)`` and ``svc_*(...)`` variants for some helpers, but the router
# historically called the ``svc_`` form. These thin aliases keep the URL
# surface stable while routing to the real implementations.
def svc_list_cities(country_code, active=True, limit=100, db=None):
    return _list_cities(country_code, active, limit, db, current_user=None)


def svc_add_city(
    country_code,
    name,
    name_local,
    population,
    is_capital,
    latitude,
    longitude,
    db,
):
    return _add_city(
        country_code,
        name,
        name_local,
        population,
        is_capital,
        latitude,
        longitude,
        db,
        current_user=None,
    )


def svc_update_city(
    country_code,
    city_id,
    name,
    name_local,
    population,
    is_capital,
    latitude,
    longitude,
    status,
    db,
):
    return _update_city(
        country_code,
        city_id,
        name,
        name_local,
        population,
        is_capital,
        latitude,
        longitude,
        status,
        db,
        current_user=None,
    )


def svc_delete_city(country_code, city_id, db):
    return _delete_city(country_code, city_id, db, current_user=None)


def svc_list_staff(country_code, db):
    return _list_staff(country_code, db, current_user=None)


def svc_assign_staff(country_code, user_id, role_in_country, db):
    return _assign_staff(country_code, user_id, role_in_country, db, current_user=None)


def svc_remove_staff(country_code, staff_id, db):
    return _remove_staff(country_code, staff_id, db, current_user=None)


def svc_list_tax_rates(country_code, db):
    return _list_tax_rates(country_code, db, current_user=None)


def svc_set_tax_rate(country_code, category_id, tax_rate, tax_name, db):
    return _set_tax_rate(country_code, category_id, tax_rate, tax_name, db, current_user=None)


def svc_send_country_communication(
    country_code,
    to_user_id,
    subject,
    body,
    priority,
    category,
    related_entity_type,
    related_entity_id,
    db,
):
    return _send_country_communication(
        country_code,
        to_user_id,
        subject,
        body,
        priority,
        category,
        related_entity_type,
        related_entity_id,
        db,
        current_user=None,
    )


def svc_list_communications(status, priority, limit, db):
    return _list_communications(status, priority, limit, db, current_user=None)


def svc_mark_communication_read(comm_id, db):
    return _mark_communication_read(comm_id, db, current_user=None)


def svc_toggle_country_active(code, current_user, db):
    return _toggle_country_active(code, current_user, db)


def svc_archive_country(code, current_user, db):
    return _archive_country(code, current_user, db)


def svc_restore_country(code, current_user, db):
    return _restore_country(code, current_user, db)


def svc_bulk_archive_countries(ids, current_user, db):
    return _bulk_archive_countries(ids, current_user, db)


def svc_bulk_restore_countries(ids, current_user, db):
    return _bulk_restore_countries(ids, current_user, db)


def svc_hard_delete_country(code, current_user, db):
    return _hard_delete_country(code, current_user, db)


def svc_list_country_commission_rates(code, current_user, db):
    return _list_country_commission_rates(code, current_user, db)


def svc_create_country_commission_rate(code, body, current_user, db):
    return _create_country_commission_rate(code, body, current_user, db)


def svc_delete_country_commission_rate(code, tier, name, current_user, db):
    return _delete_country_commission_rate(code, tier, name, current_user, db)


@router.get("")
def list_public_countries_route(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.configure")),
):
    return list_public_countries(db)


@router.get("/{code}/config")
def get_public_country_config_route(
    code: str,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.configure")),
):
    return get_public_country_config(code, db)


@router.post("")
def create_admin_country_route(
    body: dict = Body(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.configure")),
):
    return create_admin_country(body, _, db)


@router.get("/{code}")
def get_admin_country_route(
    code: str,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.configure")),
):
    return get_admin_country(code, _, db)


@router.patch("/{code}")
def update_admin_country_identity(
    code: str,
    body: dict = Body(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.configure")),
):
    return update_country_identity(code, body, _, db)


@router.get("/{country_code}/cities")
def list_cities(
    country_code: str = Path(...),
    active: bool = Query(True),
    limit: int = Query(100, le=500),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.localization.manage")),
):
    return svc_list_cities(country_code, active=active, limit=limit, db=db)


@router.post("/{country_code}/cities")
def add_city(
    country_code: str = Path(...),
    name: str = Body(...),
    name_local: str | None = Body(None),
    population: int = Body(0),
    is_capital: bool = Body(False),
    latitude: float | None = Body(None),
    longitude: float | None = Body(None),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.localization.manage")),
):
    return svc_add_city(
        country_code=country_code,
        name=name,
        name_local=name_local,
        population=population,
        is_capital=is_capital,
        latitude=latitude,
        longitude=longitude,
        db=db,
    )


@router.put("/{country_code}/cities/{city_id}")
def update_city(
    country_code: str = Path(...),
    city_id: int = Path(...),
    name: str | None = Body(None),
    name_local: str | None = Body(None),
    population: int | None = Body(None),
    is_capital: bool | None = Body(None),
    latitude: float | None = Body(None),
    longitude: float | None = Body(None),
    status: str | None = Body(None),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.localization.manage")),
):
    return svc_update_city(
        country_code=country_code,
        city_id=city_id,
        name=name,
        name_local=name_local,
        population=population,
        is_capital=is_capital,
        latitude=latitude,
        longitude=longitude,
        status=status,
        db=db,
    )


@router.delete("/{country_code}/cities/{city_id}")
def delete_city(
    country_code: str = Path(...),
    city_id: int = Path(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.localization.manage")),
):
    return svc_delete_city(country_code=country_code, city_id=city_id, db=db)


@router.get("/{country_code}/staff")
def list_staff(
    country_code: str = Path(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.staff.assign")),
):
    return svc_list_staff(country_code=country_code, db=db)


@router.post("/{country_code}/staff")
def assign_staff(
    country_code: str = Path(...),
    user_id: int = Body(...),
    role_in_country: str = Body(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.staff.assign")),
):
    return svc_assign_staff(country_code=country_code, user_id=user_id, role_in_country=role_in_country, db=db)


@router.delete("/{country_code}/staff/{staff_id}")
def remove_staff(
    country_code: str = Path(...),
    staff_id: int = Path(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.staff.assign")),
):
    return svc_remove_staff(country_code=country_code, staff_id=staff_id, db=db)


@router.get("/{country_code}/tax-rates")
def list_tax_rates(
    country_code: str = Path(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.tax.manage")),
):
    return svc_list_tax_rates(country_code=country_code, db=db)


@router.post("/{country_code}/tax-rates")
def set_tax_rate(
    country_code: str = Path(...),
    category_id: int = Body(...),
    tax_rate: float = Body(...),
    tax_name: str | None = Body(None),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.tax.manage")),
):
    return svc_set_tax_rate(
        country_code=country_code,
        category_id=category_id,
        tax_rate=tax_rate,
        tax_name=tax_name,
        db=db,
    )


@router.post("/{country_code}/communications")
def send_country_communication(
    country_code: str = Path(...),
    to_user_id: int = Body(...),
    subject: str = Body(...),
    body: str = Body(...),
    priority: str = Body("normal"),
    category: str | None = Body(None),
    related_entity_type: str | None = Body(None),
    related_entity_id: int | None = Body(None),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.communications.send")),
):
    return svc_send_country_communication(
        country_code=country_code,
        to_user_id=to_user_id,
        subject=subject,
        body=body,
        priority=priority,
        category=category,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        db=db,
    )


@router.get("/communications")
def list_communications(
    status: str | None = Query(None),
    priority: str | None = Query(None),
    limit: int = Query(50, le=200),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.communications.send")),
):
    return svc_list_communications(status=status, priority=priority, limit=limit, db=db)


@router.put("/communications/{comm_id}/read")
def mark_communication_read(
    comm_id: int,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.communications.send")),
):
    return svc_mark_communication_read(comm_id=comm_id, db=db)


@router.post("/{code}/toggle-active")
def toggle_country_active_route(
    code: str,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.configure")),
):
    return svc_toggle_country_active(code, _, db)


@router.post("/{code}/archive")
def archive_country_route(
    code: str,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.configure")),
):
    return svc_archive_country(code, _, db)


@router.post("/{code}/restore")
def restore_country_route(
    code: str,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.configure")),
):
    return svc_restore_country(code, _, db)


@router.post("/bulk/archive")
def bulk_archive_countries(
    payload: dict = Body(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.configure")),
):
    return svc_bulk_archive_countries(payload.get("ids", []), _, db)


@router.post("/bulk/restore")
def bulk_restore_countries(
    payload: dict = Body(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.configure")),
):
    return svc_bulk_restore_countries(payload.get("ids", []), _, db)


@router.delete("/{code}")
def hard_delete_country_route(
    code: str,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.configure")),
):
    svc_hard_delete_country(code, _, db)
    return {"message": "Deleted"}


@router.get("/countries/{code}/commission-rates")
def list_country_commission_rates_route(
    code: str,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.configure")),
):
    return svc_list_country_commission_rates(code, _, db)


@router.post("/countries/{code}/commission-rates")
def create_country_commission_rate_route(
    code: str,
    body: dict = Body(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.configure")),
):
    return svc_create_country_commission_rate(code, body, _, db)


@router.delete("/countries/{code}/commission-rates/{tier}/{name}")
def delete_country_commission_rate_route(
    code: str,
    tier: str,
    name: str,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("country.configure")),
):
    return svc_delete_country_commission_rate(code, tier, name, _, db)
