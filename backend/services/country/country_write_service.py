"""Country write service — DB write operations for country-related entities."""
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from models import (
    AdminChangeAuditLog,
    CountryCity,
    CountryConfig,
    CountryConfigVersion,
    CountryCommunication,
    CountryFeatureFlag,
    CountryStaffAssignment,
    EmailVerificationToken,
    OmanDeliveryZone,
    PasswordResetToken,
    ProcessedWebhookEvent,
    SupplierCountryCommission,
)

try:
    from models import Country, CountryTranslation
except ImportError:
    Country = None
    CountryTranslation = None
from utils.datetime_utils import utcnow as _utcnow


def _to_json(value: Any) -> str:
    import json
    return json.dumps(value, default=str)


def record_admin_change(
    db: Session,
    *,
    actor_id: int | None,
    action: str,
    entity: str,
    entity_key: str | None,
    before: Any,
    after: Any,
    notes: str | None = None,
) -> AdminChangeAuditLog:
    audit = AdminChangeAuditLog(
        admin_id=actor_id,
        action=action,
        entity=entity,
        entity_key=entity_key,
        before_json=_to_json(before) if before is not None else None,
        after_json=_to_json(after) if after is not None else None,
        notes=notes,
        created_at=_utcnow(),
    )
    db.add(audit)
    return audit


def create_country(db: Session, code: str, name: str, **kwargs) -> Country:
    country = Country(code=code, name=name, **kwargs)
    db.add(country)
    db.commit()
    db.refresh(country)
    return country


def update_country(db: Session, country: Country, updates: dict) -> Country:
    for key, value in updates.items():
        setattr(country, key, value)
    db.commit()
    db.refresh(country)
    return country


def delete_country(db: Session, country: Country) -> None:
    db.delete(country)
    db.commit()


def commit_and_refresh(db: Session) -> None:
    db.commit()


def refresh(db: Session, obj: Any) -> Any:
    db.refresh(obj)
    return obj


def create_country_config(db: Session, country_code: str, **config_data) -> CountryConfig:
    config = CountryConfig(country_code=country_code, **config_data)
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def update_country_config(db: Session, config: CountryConfig, updates: dict) -> CountryConfig:
    for key, value in updates.items():
        setattr(config, key, value)
    db.commit()
    db.refresh(config)
    return config


def create_country_translation(
    db: Session, country_code: str, language_code: str, **translation_data
) -> CountryTranslation:
    translation = CountryTranslation(
        country_code=country_code, language_code=language_code, **translation_data
    )
    db.add(translation)
    db.commit()
    db.refresh(translation)
    return translation


def delete_country_translation(db: Session, translation: CountryTranslation) -> None:
    db.delete(translation)
    db.commit()


def create_email_verification_token(
    db: Session, user_id: int, raw_token: str, expires_at: datetime
) -> EmailVerificationToken:
    token = EmailVerificationToken(
        user_id=user_id, token=raw_token, expires_at=expires_at
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def expire_token(db: Session, token: Any) -> None:
    setattr(token, "expires_at", datetime.now(timezone.utc).replace(tzinfo=None))
    db.commit()


def verify_email_record(db: Session, ev: EmailVerificationToken, user: Any) -> None:
    setattr(user, "email_verified", True)
    setattr(ev, "used", True)
    db.commit()
    db.refresh(user)


def create_reset_token(
    db: Session, user_id: int, raw_token: str, expires_at: datetime
) -> PasswordResetToken:
    token = PasswordResetToken(user_id=user_id, token=raw_token, expires_at=expires_at)
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def execute_password_reset(
    db: Session, user: Any, db_token: PasswordResetToken, new_password: str
) -> None:
    from utils.auth import get_password_hash
    setattr(user, "hashed_password", get_password_hash(new_password))
    setattr(db_token, "used", True)
    db.commit()
    db.refresh(user)


def record_processed_webhook_event(
    db: Session, event_id: str, processor: str, payload_hash: Optional[str] = None
) -> ProcessedWebhookEvent:
    event = ProcessedWebhookEvent(
        event_id=event_id, processor=processor, payload_hash=payload_hash
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def create_country_city(
    db: Session,
    country_code: str,
    name: str,
    region: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    population: int | None = None,
    is_active: bool = True,
    sort_order: int = 0,
    source: str = "manual",
) -> CountryCity:
    city = CountryCity(
        country_code=country_code,
        name=name,
        region=region,
        latitude=latitude,
        longitude=longitude,
        population=population,
        is_active=is_active,
        sort_order=sort_order,
        source=source,
    )
    db.add(city)
    db.commit()
    db.refresh(city)
    return city


def delete_country_cities(db: Session, country_code: str) -> None:
    db.query(CountryCity).filter(CountryCity.country_code == country_code).delete(synchronize_session=False)
    db.commit()


def create_country_config_version(
    db: Session,
    country_code: str,
    config_type: str,
    version: int,
    payload_json: str,
    status: str = "draft",
    draft_by: int | None = None,
) -> CountryConfigVersion:
    version_obj = CountryConfigVersion(
        country_code=country_code,
        config_type=config_type,
        version=version,
        payload_json=payload_json,
        status=status,
        draft_by=draft_by,
        created_at=_utcnow(),
    )
    db.add(version_obj)
    db.commit()
    db.refresh(version_obj)
    return version_obj


def update_country_config_version(db: Session, version: CountryConfigVersion, updates: dict) -> CountryConfigVersion:
    for key, value in updates.items():
        setattr(version, key, value)
    db.commit()
    db.refresh(version)
    return version


def create_delivery_zone(
    db: Session,
    zone_code: str,
    zone_name: str,
    description: str | None = None,
    car_rate: float | None = None,
    van_rate: float | None = None,
    truck_rate: float | None = None,
    weight_surcharge_rate: float | None = None,
    weight_surcharge_threshold_kg: float | None = None,
    cities: list = None,
    is_active: bool = True,
    sort_order: int = 0,
) -> OmanDeliveryZone:
    zone = OmanDeliveryZone(
        zone_code=zone_code,
        zone_name=zone_name,
        description=description,
        car_rate=car_rate,
        van_rate=van_rate,
        truck_rate=truck_rate,
        weight_surcharge_rate=weight_surcharge_rate,
        weight_surcharge_threshold_kg=weight_surcharge_threshold_kg,
        cities_json=_to_json(cities or []),
        is_active=is_active,
        sort_order=sort_order,
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


def create_supplier_country_commission(
    db: Session,
    country_code: str,
    category_slug: str,
    commission_rate: float,
    notes: str | None = None,
    is_active: bool = True,
) -> SupplierCountryCommission:
    entry = SupplierCountryCommission(
        country_code=country_code,
        category_slug=category_slug,
        commission_rate=commission_rate,
        notes=notes,
        is_active=is_active,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def update_supplier_country_commission(
    db: Session, entry: SupplierCountryCommission, updates: dict
) -> SupplierCountryCommission:
    for key, value in updates.items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return entry


def create_country_feature_flag(
    db: Session,
    country_code: str,
    feature_key: str,
    is_enabled: bool = False,
    rollout_audience: str | None = None,
    notes: str | None = None,
) -> "CountryFeatureFlag":
    from models import CountryFeatureFlag
    flag = CountryFeatureFlag(
        country_code=country_code,
        feature_key=feature_key,
        is_enabled=is_enabled,
        rollout_audience=rollout_audience,
        notes=notes,
    )
    db.add(flag)
    db.commit()
    db.refresh(flag)
    return flag


def update_country_feature_flag(
    db: Session, flag: "CountryFeatureFlag", updates: dict
) -> "CountryFeatureFlag":
    from models import CountryFeatureFlag
    for key, value in updates.items():
        setattr(flag, key, value)
    db.commit()
    db.refresh(flag)
    return flag


def create_country_communication(
    db: Session,
    country_code: str,
    from_user_id: int,
    to_user_id: int | None,
    subject: str,
    body: str,
    priority: str = "normal",
    category: str | None = None,
) -> "CountryCommunication":
    from models import CountryCommunication
    comm = CountryCommunication(
        country_code=country_code.upper(),
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        subject=subject,
        body=body,
        priority=priority.lower(),
        category=category,
    )
    db.add(comm)
    db.commit()
    db.refresh(comm)
    return comm


def mark_communication_read(db: Session, comm: "CountryCommunication") -> None:
    from utils.datetime_utils import utcnow
    comm.status = "read"
    comm.read_at = utcnow()
    db.commit()


def create_country_staff_assignment(
    db: Session,
    user_id: int,
    country_code: str,
    role_in_country: str,
    assigned_by: int,
) -> "CountryStaffAssignment":
    from models import CountryStaffAssignment
    assignment = CountryStaffAssignment(
        user_id=user_id,
        country_code=country_code.upper(),
        role_in_country=role_in_country,
        assigned_by=assigned_by,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def deactivate_country_staff_assignment(db: Session, assignment: "CountryStaffAssignment") -> None:
    from models import CountryStaffAssignment
    assignment.is_active = False
    db.commit()


def commit_country_config(db: Session) -> None:
    db.commit()


def refresh_country_config(db: Session, config: CountryConfig) -> CountryConfig:
    db.refresh(config)
    return config


def add_country_city(db: Session, city: CountryCity) -> None:
    db.add(city)


def add_to_session(db: Session, model: Any) -> None:
    """Stage a model in the session without committing (caller commits later)."""
    db.add(model)


def bulk_replace_country_cities(db: Session, country_code: str, cities: list) -> None:
    """Delete all cities for a country and insert new ones in a single transaction."""
    db.query(CountryCity).filter(CountryCity.country_code == country_code).delete(synchronize_session=False)
    for city in cities:
        db.add(city)
    db.commit()


def delete_country_cities_by_country(db: Session, country_code: str) -> None:
    db.query(CountryCity).filter(CountryCity.country_code == country_code).delete(synchronize_session=False)
    db.commit()


def update_country_config_json(db: Session, country: CountryConfig, key: str, value: str) -> None:
    setattr(country, key, value)
    db.commit()


def add_delivery_zone(db: Session, zone: OmanDeliveryZone) -> None:
    db.add(zone)


def add_supplier_commission(db: Session, entry: SupplierCountryCommission) -> None:
    db.add(entry)


def add_feature_flag(db: Session, flag: CountryFeatureFlag) -> None:
    db.add(flag)


def add_country_communication(db: Session, comm: "CountryCommunication") -> "CountryCommunication":
    db.add(comm)
    db.commit()
    db.refresh(comm)
    return comm


def mark_communication_read_at(db: Session, comm: "CountryCommunication") -> None:
    from utils.datetime_utils import utcnow
    comm.status = "read"
    comm.read_at = utcnow()
    db.commit()


def add_country_staff_assignment(db: Session, assignment: "CountryStaffAssignment") -> "CountryStaffAssignment":
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def create_country_config_version_and_commit(
    db: Session,
    country_code: str,
    config_type: str,
    version: int,
    payload_json: str,
    status: str = "draft",
    draft_by: int | None = None,
) -> CountryConfigVersion:
    version_obj = CountryConfigVersion(
        country_code=country_code,
        config_type=config_type,
        version=version,
        payload_json=payload_json,
        status=status,
        draft_by=draft_by,
        created_at=_utcnow(),
    )
    db.add(version_obj)
    db.commit()
    db.refresh(version_obj)
    return version_obj


def update_country_config_version_status(db: Session, version: CountryConfigVersion, updates: dict) -> CountryConfigVersion:
    for key, value in updates.items():
        setattr(version, key, value)
    db.commit()
    db.refresh(version)
    return version


def add_country_city_and_commit(db: Session, city: CountryCity) -> CountryCity:
    db.add(city)
    db.commit()
    db.refresh(city)
    return city


def add_tax_entry(db: Session, entry: Any) -> None:
    db.add(entry)


def commit_and_refresh_obj(db: Session, obj: Any) -> Any:
    db.commit()
    db.refresh(obj)
    return obj


def add_oman_delivery_zone(db: Session, zone: OmanDeliveryZone) -> None:
    db.add(zone)


def add_supplier_commission_entry(db: Session, entry: SupplierCountryCommission) -> None:
    db.add(entry)


def add_country_feature_flag(db: Session, flag: "CountryFeatureFlag") -> None:
    db.add(flag)


def commit_country_changes(db: Session) -> None:
    db.commit()


def create_rollback_version(
    db: Session,
    country_code: str,
    config_type: str,
    version: int,
    payload_json: str,
    draft_by: int | None = None,
    approved_by: int | None = None,
) -> CountryConfigVersion:
    from models import CountryConfigVersion
    from utils.datetime_utils import utcnow
    rollback_row = CountryConfigVersion(
        country_code=country_code,
        config_type=config_type,
        version=version,
        payload_json=payload_json,
        status="rolled_back",
        draft_by=draft_by,
        approved_by=approved_by,
        published_at=utcnow(),
        created_at=utcnow(),
    )
    db.add(rollback_row)
    db.commit()
    db.refresh(rollback_row)
    return rollback_row