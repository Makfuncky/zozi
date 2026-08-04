"""Country admin DB operations extracted from ``routers/supplier/countries.py``.

Routers must not perform ``db.query`` / session writes directly (layering:
LC1/W1); they delegate to this module.  Every function takes the SQLAlchemy
``Session`` as its first argument and preserves the exact business logic,
validation and ``HTTPException`` status codes/messages of the original router
handlers.

Auth guards (``_require_admin`` / ``_require_full_admin`` /
``_require_country_access``) intentionally stay in the router: they are pure
in-memory checks on ``current_user`` and moving them here would introduce an
upward ``services -> controllers`` import.
"""

from decimal import Decimal
from typing import Any, Optional
import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from data.models import (
    CountryCity, CountryCommissionRate, CountryConfig,
    CountryCommunication, CountryStaffAssignment, CountryCategoryTaxRate,
    CrossCountryCustomerSession, OmanDeliveryZone, User,
    CountryConfigVersion, PayoutRuleCategory, PayoutRuleProduct,
)
from data.models_country_enhancements import CountryFeatureFlag
from data.services_logistics_partner_pricing import normalize_country_code
from services.country_write_service import record_admin_change, commit_country_changes
from data.services_write_helpers import (
    add_and_flush,
    commit_and_refresh,
    commit_only,
    delete_only,
)

from utils.datetime_utils import utcnow as _utcnow


# ── Internal helpers ─────────────────────────────────────────────────────────

def _actor_id(current_user: Any) -> Optional[int]:
    """Extract the acting admin's id from the ``current_user`` payload."""
    if isinstance(current_user, dict):
        return current_user.get("id")
    return getattr(current_user, "id", None)


def _to_json(value: Any) -> str:
    return json.dumps(value, default=str)


def _from_json(raw: str | None, *, default: Any) -> Any:
    if not raw:
        return default
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return default
    return parsed


def _get_country_or_404(db: Session, code: str) -> CountryConfig:
    """Mirror of ``country_controller._get_country_or_404`` (404 detail preserved)."""
    normalized = normalize_country_code(code)
    country = db.query(CountryConfig).filter(CountryConfig.code == normalized).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country config not found")
    return country


def _get_feature_flag_or_404(db: Session, code: str, key: str) -> CountryFeatureFlag:
    flag = (
        db.query(CountryFeatureFlag)
        .filter(CountryFeatureFlag.country_code == code.upper(), CountryFeatureFlag.feature_key == key)
        .first()
    )
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    return flag


def _get_city_or_404(db: Session, code: str, city_id: int) -> CountryCity:
    city = (
        db.query(CountryCity)
        .filter(CountryCity.id == city_id, CountryCity.country_code == code.upper())
        .first()
    )
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    return city


def _to_decimal(value: Any, *, field: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid decimal for {field}") from exc


# ── Public Endpoints (read-only) ─────────────────────────────────────────────

def list_public_countries(db: Session) -> list[dict[str, Any]]:
    rows = (
        db.query(CountryConfig)
        .filter(CountryConfig.is_active == True)
        .order_by(CountryConfig.code.asc())
        .all()
    )
    return [{"code": row.code, "name": row.name, "currency": row.currency} for row in rows]


def get_public_country_config(code: str, db: Session) -> dict[str, Any]:
    country = _get_country_or_404_by_code(db, normalize_country_code(code))
    if not country.is_active:
        raise HTTPException(status_code=404, detail="Country is inactive")
    return _country_public_payload(db, country)


def _get_country_or_404_by_code(db: Session, code: str) -> CountryConfig:
    country = db.query(CountryConfig).filter(CountryConfig.code == code).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country config not found")
    return country


def list_employees(code: str, db: Session, department: Optional[str] = None,
                   status: Optional[str] = None, query: Optional[str] = None, limit: int = 100) -> list[dict]:
    from data.models import Employee
    q = db.query(Employee).filter(Employee.country_code == code)
    if department and department != "all":
        q = q.filter(Employee.department == department)
    if status and status != "all":
        q = q.filter(Employee.employment_status == status)
    if query:
        q = q.join(Employee.user).filter(
            Employee.employee_code.ilike(f"%{query}%") |
            Employee.position.ilike(f"%{query}%") |
            Employee.department.ilike(f"%{query}%")
        )
    employees = q.order_by(Employee.created_at.desc()).limit(limit).all()
    return [_employee_payload(e) for e in employees]


def _employee_payload(emp) -> dict:
    return {
        "id": emp.id,
        "employee_code": emp.employee_code,
        "department": emp.department,
        "position": emp.position,
        "employment_status": emp.employment_status,
        "salary": float(emp.salary) if emp.salary else None,
        "currency": emp.currency,
        "country_code": emp.country_code,
        "hire_date": emp.hire_date.isoformat() if emp.hire_date else None,
        "user": {"id": emp.user_id, "full_name": emp.user.full_name if emp.user else None} if emp.user else None,
    }


def _country_public_payload(db: Session, country: CountryConfig) -> dict[str, Any]:
    city_count = 0
    try:
        city_count = db.query(CountryCity).filter(
            CountryCity.country_code == country.code,
            CountryCity.is_active == True,
        ).count()
    except Exception:
        city_count = 0

    return {
        "code": country.code,
        "name": country.name,
        "currency": country.currency,
        "currency_symbol": country.currency_symbol,
        "phone_code": country.phone_code,
        "language": country.language or "en",
        "timezone": country.timezone,
        "tax_type": country.tax_type,
        "tax_rate": float(country.tax_rate) if country.tax_rate is not None else 0.0,
        "tax_name": country.tax_name,
        "tax_inclusive": bool(country.tax_inclusive),
        "tax_exempt_categories": _from_json(country.tax_exempt_categories_json, default=[]),
        "tax_reduced_rates": _from_json(country.tax_reduced_rates_json, default={}),
        "logistics_model": country.logistics_model,
        "default_vehicle_type": country.default_vehicle_type,
        "base_rate": float(country.base_rate) if country.base_rate is not None else None,
        "per_km_rate": float(country.per_km_rate) if country.per_km_rate is not None else None,
        "minimum_charge": float(country.minimum_charge) if country.minimum_charge is not None else None,
        "weight_surcharge_rate": float(country.weight_surcharge_rate) if country.weight_surcharge_rate is not None else None,
        "weight_surcharge_threshold_kg": float(country.weight_surcharge_threshold_kg) if country.weight_surcharge_threshold_kg is not None else None,
        "payment_methods": _from_json(country.payment_methods_json, default=[]),
        "payment_gateways": _from_json(country.payment_gateways_json, default=[]),
        "logistics_providers": _from_json(country.logistics_providers_json, default=[]),
        "date_format": country.date_format or "DD/MM/YYYY",
        "address_format": _from_json(country.address_format_json, default={}),
        "legal_rules": _from_json(country.legal_rules_json, default={}),
        "product_restrictions": _from_json(country.product_restrictions_json, default=[]),
        "regions": _from_json(country.regions_json, default=[]),
        "supplier_requirements": _from_json(country.supplier_requirements_json, default={}),
        "payout_settings": _from_json(country.payout_settings_json, default={}),
        "commission_tiers": _from_json(country.commission_tiers_json, default=[]),
        "is_active": bool(country.is_active),
        "city_count": city_count,
        # Phase 1: Heuristic / algorithmic fields
        "economic_tier": country.economic_tier,
        "fraud_risk_tier": country.fraud_risk_tier,
        "suggested_logistics_model": country.suggested_logistics_model,
        "suggested_commission_ranges": _from_json(country.suggested_commission_ranges_json, default={}),
        "suggested_gateway_rankings": _from_json(country.suggested_gateway_rankings_json, default=[]),
        "consumer_behavior_profile": _from_json(country.consumer_behavior_profile_json, default={}),
        # Phase 1: Expanded identity
        "official_name": country.official_name,
        "alpha3": country.alpha3,
        "flag_url": country.flag_url,
        "currency_name": country.currency_name,
        "exchange_rate_to_usd": float(country.exchange_rate_to_usd) if country.exchange_rate_to_usd is not None else None,
        # Phase 1: COD / settlement
        "cod_enabled": bool(country.cod_enabled) if country.cod_enabled is not None else True,
        "cod_max_amount": float(country.cod_max_amount) if country.cod_max_amount is not None else None,
        "cod_verification_required": bool(country.cod_verification_required) if country.cod_verification_required is not None else False,
        "cod_remittance_days": country.cod_remittance_days,
        "settlement_hold_days": country.settlement_hold_days,
        "minimum_payout_amount": float(country.minimum_payout_amount) if country.minimum_payout_amount is not None else None,
        "payout_currency": country.payout_currency,
        # Phase 1: Supplier defaults
        "supplier_kyc_tier": country.supplier_kyc_tier,
        "supplier_onboarding_fee": float(country.supplier_onboarding_fee) if country.supplier_onboarding_fee is not None else None,
        "supplier_monthly_fee": float(country.supplier_monthly_fee) if country.supplier_monthly_fee is not None else None,
        "supplier_rating_threshold": float(country.supplier_rating_threshold) if country.supplier_rating_threshold is not None else None,
        # Phase 1: Legal / consumer
        "legal_entity_required": bool(country.legal_entity_required) if country.legal_entity_required is not None else False,
        "consumer_protection_days": country.consumer_protection_days,
        "data_privacy_framework": country.data_privacy_framework,
        # Phase 1: Logistics expansion
        "max_package_weight_kg": float(country.max_package_weight_kg) if country.max_package_weight_kg is not None else None,
        "max_package_dimensions_cm": country.max_package_dimensions_cm,
        "signature_required_threshold": float(country.signature_required_threshold) if country.signature_required_threshold is not None else None,
        # Phase 1: Locale
        "measurement_system": country.measurement_system or "metric",
        "working_days": _from_json(country.working_days_json, default=[]),
    }


def get_admin_country(code: str, current_user: dict, db: Session) -> dict[str, Any]:
    return _country_public_payload(db, _get_country_or_404(db, code))


def create_admin_country(payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    normalized_code = normalize_country_code(str(payload.get("code") or ""))
    if not normalized_code:
        raise HTTPException(status_code=422, detail="Invalid country code")

    existing = db.query(CountryConfig).filter(CountryConfig.code == normalized_code).first()
    if existing:
        raise HTTPException(status_code=409, detail="Country already exists")

    name = str(payload.get("name") or "").strip()
    currency = str(payload.get("currency") or "").strip().upper()
    timezone = str(payload.get("timezone") or "").strip()
    is_active = bool(payload.get("is_active", True))

    if not name or not currency or not timezone:
        raise HTTPException(status_code=422, detail="Name, currency, and timezone are required")

    logistics_defaults = payload.get("logistics_defaults") or {}
    legal_rules = payload.get("legal_rules") or {}

    country = CountryConfig(
        code=normalized_code,
        name=name,
        currency=currency,
        currency_symbol=str(payload.get("currency_symbol") or "").strip() or None,
        phone_code=str(payload.get("phone_code") or "").strip() or None,
        language=str(payload.get("language") or "en").strip().lower() or "en",
        timezone=timezone,
        tax_type=str(payload.get("tax_type") or "VAT"),
        tax_rate=Decimal(str(payload["tax_rate"])) if payload.get("tax_rate") is not None else Decimal("0.0000"),
        tax_name=str(payload.get("tax_name") or "Tax"),
        tax_inclusive=False,
        tax_exempt_categories_json="[]",
        tax_reduced_rates_json="{}",
        logistics_model=str(logistics_defaults.get("logistics_model") or "fixed"),
        default_vehicle_type=logistics_defaults.get("default_vehicle_type"),
        base_rate=logistics_defaults.get("base_rate"),
        per_km_rate=logistics_defaults.get("per_km_rate"),
        minimum_charge=logistics_defaults.get("minimum_charge"),
        weight_surcharge_rate=logistics_defaults.get("weight_surcharge_rate"),
        weight_surcharge_threshold_kg=logistics_defaults.get("weight_surcharge_threshold_kg"),
        payment_methods_json="[]",
        payment_gateways_json=_to_json(payload.get("payment_gateways")),
        logistics_providers_json=_to_json(payload.get("logistics_providers")),
        legal_rules_json=_to_json(legal_rules),
        product_restrictions_json=_to_json(payload.get("product_restrictions")),
        address_format_json='{"fields":["street","city","postal_code"],"required":["street","city"]}',
        date_format=str(payload.get("date_format") or "DD/MM/YYYY").strip(),
        regions_json="[]",
        supplier_requirements_json=_to_json(payload.get("supplier_requirements")),
        payout_settings_json=_to_json(payload.get("payout_settings")),
        commission_tiers_json=_to_json(payload.get("commission_tiers")),
        is_active=is_active,
        population=payload.get("population"),
        internet_penetration_pct=payload.get("internet_penetration_pct"),
        gdp_per_capita_usd=payload.get("gdp_per_capita_usd"),
        urbanization_pct=payload.get("urbanization_pct"),
        mobile_subs_per_100=payload.get("mobile_subs_per_100"),
        public_holidays_json=_to_json(payload.get("public_holidays")),
        macro_indicators_json=_to_json(payload.get("macro_indicators")),
        economic_tier=str(payload.get("economic_tier") or "").strip() or None,
        fraud_risk_tier=str(payload.get("fraud_risk_tier") or "").strip() or None,
        suggested_logistics_model=str(payload.get("suggested_logistics_model") or "").strip() or None,
        suggested_commission_ranges_json=_to_json(payload.get("suggested_commission_ranges")),
        suggested_gateway_rankings_json=_to_json(payload.get("suggested_gateway_rankings")),
        consumer_behavior_profile_json=_to_json(payload.get("consumer_behavior_profile")),
        official_name=str(payload.get("official_name") or "").strip() or None,
        alpha3=str(payload.get("alpha3") or "").strip().upper() or None,
        flag_url=str(payload.get("flag_url") or "").strip() or None,
        currency_name=str(payload.get("currency_name") or "").strip() or None,
        exchange_rate_to_usd=payload.get("exchange_rate_to_usd"),
        cod_enabled=payload.get("cod_enabled"),
        cod_max_amount=payload.get("cod_max_amount"),
        cod_verification_required=payload.get("cod_verification_required"),
        cod_remittance_days=payload.get("cod_remittance_days"),
        settlement_hold_days=payload.get("settlement_hold_days") or 3,
        minimum_payout_amount=payload.get("minimum_payout_amount"),
        payout_currency=str(payload.get("payout_currency") or "").strip().upper() or None,
        supplier_kyc_tier=str(payload.get("supplier_kyc_tier") or "").strip() or None,
        supplier_onboarding_fee=payload.get("supplier_onboarding_fee"),
        supplier_monthly_fee=payload.get("supplier_monthly_fee"),
        supplier_rating_threshold=payload.get("supplier_rating_threshold"),
        legal_entity_required=payload.get("legal_entity_required"),
        consumer_protection_days=payload.get("consumer_protection_days") or 14,
        data_privacy_framework=str(payload.get("data_privacy_framework") or "").strip() or None,
        max_package_weight_kg=payload.get("max_package_weight_kg"),
        max_package_dimensions_cm=str(payload.get("max_package_dimensions_cm") or "").strip() or None,
        signature_required_threshold=payload.get("signature_required_threshold"),
        measurement_system=str(payload.get("measurement_system") or "metric").strip().lower(),
        working_days_json=_to_json(payload.get("working_days")),
    )
    db.add(country)
    record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="create",
        entity="country",
        entity_key=country.code,
        before=None,
        after=_country_public_payload(db, country),
    )
    commit_and_refresh(db, country)

    cities_data = payload.get("cities") or []
    for c in cities_data:
        city = CountryCity(
            country_code=normalized_code,
            name=str(c.get("name", "")).strip(),
            region=str(c.get("region", "")).strip() or None,
            latitude=float(c["lat"]) if c.get("lat") is not None else None,
            longitude=float(c["lng"]) if c.get("lng") is not None else None,
            population=int(c["population"]) if c.get("population") is not None else None,
            source=str(c.get("source", "openmeteo")),
        )
        db.add(city)

    tax_rates_data = payload.get("category_tax_rates") or []
    for tr in tax_rates_data:
        tax_entry = CountryCategoryTaxRate(
            country_code=normalized_code,
            category_slug=str(tr.get("category_slug", "")).strip(),
            rate=Decimal(str(round(float(tr.get("rate", 0.0)), 4))),
            is_exempt=bool(tr.get("is_exempt", False)),
            is_reduced=bool(tr.get("is_reduced", False)),
            notes=str(tr.get("notes", "")) or None,
            source=str(tr.get("source", "curated")),
        )
        db.add(tax_entry)

    if payload.get("population") is not None:
        country.population = int(payload["population"])
    if payload.get("internet_penetration_pct") is not None:
        country.internet_penetration_pct = Decimal(str(payload["internet_penetration_pct"]))
    if payload.get("gdp_per_capita_usd") is not None:
        country.gdp_per_capita_usd = Decimal(str(payload["gdp_per_capita_usd"]))
    if payload.get("urbanization_pct") is not None:
        country.urbanization_pct = Decimal(str(payload["urbanization_pct"]))
    if payload.get("mobile_subs_per_100") is not None:
        country.mobile_subs_per_100 = Decimal(str(payload["mobile_subs_per_100"]))

    if payload.get("suggested_gateways"):
        country.suggested_gateway_rankings_json = _to_json(payload["suggested_gateways"])
    if payload.get("suggested_commission_tiers"):
        country.suggested_commission_ranges_json = _to_json(payload["suggested_commission_tiers"])
    if payload.get("suggested_supplier_requirements"):
        country.supplier_requirements_json = _to_json(payload["suggested_supplier_requirements"])
    if payload.get("suggested_payout_settings"):
        country.payout_settings_json = _to_json(payload["suggested_payout_settings"])
    if payload.get("consumer_profile"):
        country.consumer_behavior_profile_json = _to_json(payload["consumer_profile"])
    if payload.get("cod_reliance_estimate"):
        cod_est = payload["cod_reliance_estimate"]
        if cod_est.get("cod_pct") is not None:
            country.cod_enabled = True

    db.commit()
    db.refresh(country)
    db.commit()
    return _country_public_payload(db, country)


def update_country_identity(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    country = _get_country_or_404(db, code)
    before = _country_public_payload(db, country)

    if "name" in payload and payload["name"]:
        country.name = str(payload["name"]).strip()
    if "currency_symbol" in payload:
        country.currency_symbol = str(payload["currency_symbol"] or "").strip() or None
    if "phone_code" in payload:
        country.phone_code = str(payload["phone_code"] or "").strip() or None
    if "language" in payload:
        country.language = str(payload["language"] or "en").strip().lower() or "en"
    if "date_format" in payload:
        country.date_format = str(payload["date_format"] or "DD/MM/YYYY").strip()
    if "is_active" in payload:
        country.is_active = bool(payload["is_active"])

    if "official_name" in payload:
        country.official_name = str(payload["official_name"] or "").strip() or None
    if "alpha3" in payload:
        country.alpha3 = str(payload["alpha3"] or "").strip().upper() or None
    if "flag_url" in payload:
        country.flag_url = str(payload["flag_url"] or "").strip() or None
    if "currency_name" in payload:
        country.currency_name = str(payload["currency_name"] or "").strip() or None
    if "exchange_rate_to_usd" in payload:
        country.exchange_rate_to_usd = payload["exchange_rate_to_usd"]

    if "cod_enabled" in payload:
        country.cod_enabled = bool(payload["cod_enabled"])
    if "cod_max_amount" in payload:
        country.cod_max_amount = payload["cod_max_amount"]
    if "cod_verification_required" in payload:
        country.cod_verification_required = bool(payload["cod_verification_required"])
    if "cod_remittance_days" in payload:
        country.cod_remittance_days = int(payload["cod_remittance_days"])
    if "settlement_hold_days" in payload:
        country.settlement_hold_days = int(payload["settlement_hold_days"])
    if "minimum_payout_amount" in payload:
        country.minimum_payout_amount = payload["minimum_payout_amount"]
    if "payout_currency" in payload:
        country.payout_currency = str(payload["payout_currency"] or "").strip().upper() or None

    if "measurement_system" in payload:
        country.measurement_system = str(payload["measurement_system"] or "metric").strip().lower()
    if "working_days" in payload:
        country.working_days_json = _to_json(payload["working_days"])
    if "data_privacy_framework" in payload:
        country.data_privacy_framework = str(payload["data_privacy_framework"] or "").strip() or None

    if "supplier_kyc_tier" in payload:
        country.supplier_kyc_tier = str(payload["supplier_kyc_tier"] or "").strip() or None
    if "supplier_onboarding_fee" in payload:
        country.supplier_onboarding_fee = payload["supplier_onboarding_fee"]
    if "supplier_monthly_fee" in payload:
        country.supplier_monthly_fee = payload["supplier_monthly_fee"]
    if "supplier_rating_threshold" in payload:
        country.supplier_rating_threshold = payload["supplier_rating_threshold"]

    if "legal_entity_required" in payload:
        country.legal_entity_required = bool(payload["legal_entity_required"])
    if "consumer_protection_days" in payload:
        country.consumer_protection_days = int(payload["consumer_protection_days"])

    if "max_package_weight_kg" in payload:
        country.max_package_weight_kg = payload["max_package_weight_kg"]
    if "max_package_dimensions_cm" in payload:
        country.max_package_dimensions_cm = str(payload["max_package_dimensions_cm"] or "").strip() or None
    if "signature_required_threshold" in payload:
        country.signature_required_threshold = payload["signature_required_threshold"]

    if "economic_tier" in payload:
        country.economic_tier = str(payload["economic_tier"] or "").strip() or None
    if "fraud_risk_tier" in payload:
        country.fraud_risk_tier = str(payload["fraud_risk_tier"] or "").strip() or None
    if "suggested_logistics_model" in payload:
        country.suggested_logistics_model = str(payload["suggested_logistics_model"] or "").strip() or None

    country.updated_at = _utcnow()
    record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="update",
        entity="country_identity",
        entity_key=country.code,
        before=before,
        after=_country_public_payload(db, country),
    )
    db.commit()
    db.refresh(country)
    return _country_public_payload(db, country)


def create_tax_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    country = _get_country_or_404(db, code)

    draft_payload = {
        "tax_type": str(payload.get("tax_type") or country.tax_type).strip().upper(),
        "tax_rate": str(_to_decimal(payload.get("tax_rate", country.tax_rate), field="tax_rate")),
        "tax_name": str(payload.get("tax_name") or country.tax_name).strip() or country.tax_name,
        "tax_inclusive": bool(payload.get("tax_inclusive", country.tax_inclusive)),
        "tax_exempt_categories": payload.get("tax_exempt_categories", _from_json(country.tax_exempt_categories_json, default=[])),
        "tax_reduced_rates": payload.get("tax_reduced_rates", _from_json(country.tax_reduced_rates_json, default={})),
    }

    version = CountryConfigVersion(
        country_code=country.code,
        config_type="tax",
        version=_next_version(db, country.code, "tax"),
        payload_json=_to_json(draft_payload),
        status="draft",
        draft_by=current_user.get("id"),
        created_at=_utcnow(),
    )
    db.add(version)
    record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="create_draft",
        entity="country_tax",
        entity_key=f"{country.code}:v{version.version}",
        before=_country_public_payload(db, country),
        after=draft_payload,
    )
    db.commit()
    db.refresh(version)
    return {"message": "Tax draft created", "version_id": version.id, "version": version.version}


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
    return int(getattr(latest, "version", 0) or 0) + 1


def create_logistics_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    country = _get_country_or_404(db, code)
    delivery_zones = payload.get("delivery_zones")
    if delivery_zones is None:
        delivery_zones = payload.get("oman_zones")

    draft_payload = {
        "logistics_model": str(payload.get("logistics_model") or country.logistics_model).strip().lower(),
        "default_vehicle_type": str(payload.get("default_vehicle_type") or country.default_vehicle_type or "").strip() or None,
        "base_rate": payload.get("base_rate", float(country.base_rate) if country.base_rate is not None else None),
        "per_km_rate": payload.get("per_km_rate", float(country.per_km_rate) if country.per_km_rate is not None else None),
        "minimum_charge": payload.get("minimum_charge", float(country.minimum_charge) if country.minimum_charge is not None else None),
        "weight_surcharge_rate": payload.get("weight_surcharge_rate", float(country.weight_surcharge_rate) if country.weight_surcharge_rate is not None else None),
        "weight_surcharge_threshold_kg": payload.get("weight_surcharge_threshold_kg", float(country.weight_surcharge_threshold_kg) if country.weight_surcharge_threshold_kg is not None else None),
        "delivery_zones": delivery_zones if isinstance(delivery_zones, list) else [],
    }

    version = CountryConfigVersion(
        country_code=country.code,
        config_type="logistics",
        version=_next_version(db, country.code, "logistics"),
        payload_json=_to_json(draft_payload),
        status="draft",
        draft_by=current_user.get("id"),
        created_at=_utcnow(),
    )
    db.add(version)
    record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="create_draft",
        entity="country_logistics",
        entity_key=f"{country.code}:v{version.version}",
        before=_country_public_payload(db, country),
        after=draft_payload,
    )
    db.commit()
    db.refresh(version)
    return {"message": "Logistics draft created", "version_id": version.id, "version": version.version}


def create_commission_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    country = _get_country_or_404(db, code)
    rates = payload.get("rates")
    if not isinstance(rates, list):
        raise HTTPException(status_code=422, detail="rates must be a list")

    normalized_rates: list[dict[str, Any]] = []
    for row in rates:
        if not isinstance(row, dict):
            continue
        slug = str(row.get("category_slug") or "").strip().lower()
        if not slug:
            continue
        normalized_rates.append({
            "category_slug": slug,
            "commission_rate": str(_to_decimal(row.get("commission_rate", 0), field=f"commission_rate[{slug}]")),
            "notes": str(row.get("notes") or "").strip() or None,
            "is_active": bool(row.get("is_active", True)),
        })

    version = CountryConfigVersion(
        country_code=country.code,
        config_type="commission",
        version=_next_version(db, country.code, "commission"),
        payload_json=_to_json({"rates": normalized_rates}),
        status="draft",
        draft_by=current_user.get("id"),
        created_at=_utcnow(),
    )
    db.add(version)
    record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="create_draft",
        entity="country_commission",
        entity_key=f"{country.code}:v{version.version}",
        before=None,
        after=normalized_rates,
    )
    db.commit()
    db.refresh(version)
    return {"message": "Commission draft created", "version_id": version.id, "version": version.version}


def create_payment_and_flags_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    country = _get_country_or_404(db, code)

    draft_payload = {
        "payment_methods": payload.get("payment_methods", _from_json(country.payment_methods_json, default=[])),
        "feature_flags": payload.get("feature_flags", {}),
    }
    version = CountryConfigVersion(
        country_code=country.code,
        config_type="ops",
        version=_next_version(db, country.code, "ops"),
        payload_json=_to_json(draft_payload),
        status="draft",
        draft_by=current_user.get("id"),
        created_at=_utcnow(),
    )
    db.add(version)
    record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="create_draft",
        entity="country_ops",
        entity_key=f"{country.code}:v{version.version}",
        before=None,
        after=draft_payload,
    )
    db.commit()
    db.refresh(version)
    return {"message": "Ops draft created", "version_id": version.id, "version": version.version}


def get_payment_gateways(code: str, current_user: dict, db: Session) -> list[dict[str, Any]]:
    country = _get_country_or_404(db, code)
    return _from_json(country.payment_gateways_json, default=[])


def create_payment_gateways_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    country = _get_country_or_404(db, code)
    gateways = payload.get("gateways") if isinstance(payload, dict) else payload
    if not isinstance(gateways, list):
        raise HTTPException(status_code=422, detail="gateways must be a list")

    normalized: list[dict[str, Any]] = []
    for gw in gateways:
        if not isinstance(gw, dict):
            continue
        normalized.append({
            "gateway_id": str(gw.get("gateway_id") or "").strip().lower(),
            "name": str(gw.get("name") or "").strip(),
            "type": str(gw.get("type") or "card").strip().lower(),
            "enabled": bool(gw.get("enabled", True)),
            "credential_ref": str(gw.get("credential_ref") or "").strip() or None,
            "supports_cod": bool(gw.get("supports_cod", False)),
            "supports_installments": bool(gw.get("supports_installments", False)),
            "fee_percentage": float(gw.get("fee_percentage") or 0),
            "fee_fixed": float(gw.get("fee_fixed") or 0),
        })

    version = CountryConfigVersion(
        country_code=country.code,
        config_type="payment_gateways",
        version=_next_version(db, country.code, "payment_gateways"),
        payload_json=_to_json({"gateways": normalized}),
        status="draft",
        draft_by=current_user.get("id"),
        created_at=_utcnow(),
    )
    db.add(version)
    record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="create_draft",
        entity="country_payment_gateways",
        entity_key=f"{country.code}:v{version.version}",
        before=None,
        after={"gateways": normalized},
    )
    db.commit()
    db.refresh(version)
    return {"message": "Payment gateways draft created", "version_id": version.id, "version": version.version}


def get_logistics_providers(code: str, current_user: dict, db: Session) -> list[dict[str, Any]]:
    country = _get_country_or_404(db, code)
    return _from_json(country.logistics_providers_json, default=[])


def create_logistics_providers_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    country = _get_country_or_404(db, code)
    providers = payload.get("providers") if isinstance(payload, dict) else payload
    if not isinstance(providers, list):
        raise HTTPException(status_code=422, detail="providers must be a list")

    normalized: list[dict[str, Any]] = []
    for prov in providers:
        if not isinstance(prov, dict):
            continue
        normalized.append({
            "provider_id": str(prov.get("provider_id") or "").strip().lower(),
            "name": str(prov.get("name") or "").strip(),
            "enabled": bool(prov.get("enabled", True)),
            "service_areas": prov.get("service_areas") if isinstance(prov.get("service_areas"), list) else ["all_regions"],
            "sla_standard_days": str(prov.get("sla_standard_days") or "3-5").strip(),
            "sla_express_days": str(prov.get("sla_express_days") or "1-2").strip(),
            "base_rate": float(prov.get("base_rate") or 0),
            "per_kg_rate": float(prov.get("per_kg_rate") or 0),
            "currency": str(prov.get("currency") or "").strip().upper() or None,
        })

    version = CountryConfigVersion(
        country_code=country.code,
        config_type="logistics_providers",
        version=_next_version(db, country.code, "logistics_providers"),
        payload_json=_to_json({"providers": normalized}),
        status="draft",
        draft_by=current_user.get("id"),
        created_at=_utcnow(),
    )
    db.add(version)
    record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="create_draft",
        entity="country_logistics_providers",
        entity_key=f"{country.code}:v{version.version}",
        before=None,
        after={"providers": normalized},
    )
    db.commit()
    db.refresh(version)
    return {"message": "Logistics providers draft created", "version_id": version.id, "version": version.version}


def get_legal_rules(code: str, current_user: dict, db: Session) -> dict[str, Any]:
    country = _get_country_or_404(db, code)
    return _from_json(country.legal_rules_json, default={})


def create_legal_rules_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    country = _get_country_or_404(db, code)
    existing = _from_json(country.legal_rules_json, default={})

    draft_payload: dict[str, Any] = {
        "minimum_order_age": int(payload.get("minimum_order_age", existing.get("minimum_order_age", 18)) or 18),
        "max_returns_allowed": int(payload.get("max_returns_allowed", existing.get("max_returns_allowed", 3)) or 3),
        "return_window_days": int(payload.get("return_window_days", existing.get("return_window_days", 14)) or 14),
        "refund_processing_days": int(payload.get("refund_processing_days", existing.get("refund_processing_days", 7)) or 7),
        "requires_commercial_license": bool(payload.get("requires_commercial_license", existing.get("requires_commercial_license", False))),
        "requires_vat_registration": bool(payload.get("requires_vat_registration", existing.get("requires_vat_registration", False))),
        "product_restrictions": payload.get("product_restrictions", existing.get("product_restrictions", [])) if isinstance(payload.get("product_restrictions", existing.get("product_restrictions", [])), list) else [],
    }

    version = CountryConfigVersion(
        country_code=country.code,
        config_type="legal_rules",
        version=_next_version(db, country.code, "legal_rules"),
        payload_json=_to_json(draft_payload),
        status="draft",
        draft_by=current_user.get("id"),
        created_at=_utcnow(),
    )
    db.add(version)
    record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="create_draft",
        entity="country_legal_rules",
        entity_key=f"{country.code}:v{version.version}",
        before=existing,
        after=draft_payload,
    )
    db.commit()
    db.refresh(version)
    return {"message": "Legal rules draft created", "version_id": version.id, "version": version.version}


def get_regions(code: str, current_user: dict, db: Session) -> list[dict[str, Any]]:
    country = _get_country_or_404(db, code)
    return _from_json(country.regions_json, default=[])


def create_regions_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    country = _get_country_or_404(db, code)
    regions = payload.get("regions") if isinstance(payload, dict) else payload
    if not isinstance(regions, list):
        raise HTTPException(status_code=422, detail="regions must be a list")

    normalized: list[dict[str, Any]] = []
    for region in regions:
        if not isinstance(region, dict):
            continue
        region_id = str(region.get("region_id") or region.get("name") or "").strip().lower().replace(" ", "_")
        cities = region.get("cities") if isinstance(region.get("cities"), list) else []
        normalized.append({
            "region_id": region_id,
            "name": str(region.get("name") or region_id).strip(),
            "cities": [str(c).strip() for c in cities if str(c).strip()],
        })

    version = CountryConfigVersion(
        country_code=country.code,
        config_type="regions",
        version=_next_version(db, country.code, "regions"),
        payload_json=_to_json({"regions": normalized}),
        status="draft",
        draft_by=current_user.get("id"),
        created_at=_utcnow(),
    )
    db.add(version)
    record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="create_draft",
        entity="country_regions",
        entity_key=f"{country.code}:v{version.version}",
        before=None,
        after={"regions": normalized},
    )
    db.commit()
    db.refresh(version)
    return {"message": "Regions draft created", "version_id": version.id, "version": version.version}


def get_supplier_requirements(code: str, current_user: dict, db: Session) -> dict[str, Any]:
    country = _get_country_or_404(db, code)
    return _from_json(country.supplier_requirements_json, default={})


def create_supplier_requirements_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    country = _get_country_or_404(db, code)
    existing = _from_json(country.supplier_requirements_json, default={})

    required_docs = payload.get("required_documents", existing.get("required_documents", []))
    draft_payload: dict[str, Any] = {
        "kyc_level": str(payload.get("kyc_level", existing.get("kyc_level", "standard")) or "standard").strip().lower(),
        "required_documents": required_docs if isinstance(required_docs, list) else [],
        "approval_required": bool(payload.get("approval_required", existing.get("approval_required", True))),
    }

    version = CountryConfigVersion(
        country_code=country.code,
        config_type="supplier_requirements",
        version=_next_version(db, country.code, "supplier_requirements"),
        payload_json=_to_json(draft_payload),
        status="draft",
        draft_by=current_user.get("id"),
        created_at=_utcnow(),
    )
    db.add(version)
    record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="create_draft",
        entity="country_supplier_requirements",
        entity_key=f"{country.code}:v{version.version}",
        before=existing,
        after=draft_payload,
    )
    db.commit()
    db.refresh(version)
    return {"message": "Supplier requirements draft created", "version_id": version.id, "version": version.version}


def get_payout_settings(code: str, current_user: dict, db: Session) -> dict[str, Any]:
    country = _get_country_or_404(db, code)
    return _from_json(country.payout_settings_json, default={})


def create_payout_settings_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    country = _get_country_or_404(db, code)
    existing = _from_json(country.payout_settings_json, default={})

    draft_payload: dict[str, Any] = {
        "minimum_payout_amount": float(payload.get("minimum_payout_amount", existing.get("minimum_payout_amount", 10)) or 10),
        "payout_schedule": str(payload.get("payout_schedule", existing.get("payout_schedule", "weekly")) or "weekly").strip().lower(),
        "payout_day": str(payload.get("payout_day", existing.get("payout_day", "sunday")) or "sunday").strip().lower(),
        "batch_size": int(payload.get("batch_size", existing.get("batch_size", 50)) or 50),
        "currency": str(payload.get("currency", existing.get("currency", "")) or "").strip().upper() or None,
    }

    version = CountryConfigVersion(
        country_code=country.code,
        config_type="payout_settings",
        version=_next_version(db, country.code, "payout_settings"),
        payload_json=_to_json(draft_payload),
        status="draft",
        draft_by=current_user.get("id"),
        created_at=_utcnow(),
    )
    db.add(version)
    record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="create_draft",
        entity="country_payout_settings",
        entity_key=f"{country.code}:v{version.version}",
        before=existing,
        after=draft_payload,
    )
    db.commit()
    db.refresh(version)
    return {"message": "Payout settings draft created", "version_id": version.id, "version": version.version}


def get_commission_tiers(code: str, current_user: dict, db: Session) -> list[dict[str, Any]]:
    country = _get_country_or_404(db, code)
    return _from_json(country.commission_tiers_json, default=[])


def create_commission_tiers_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    country = _get_country_or_404(db, code)
    tiers = payload.get("tiers") if isinstance(payload, dict) else payload
    if not isinstance(tiers, list):
        raise HTTPException(status_code=422, detail="tiers must be a list")

    normalized: list[dict[str, Any]] = []
    for tier in tiers:
        if not isinstance(tier, dict):
            continue
        normalized.append({
            "min_order_value": float(tier.get("min_order_value") or 0),
            "max_order_value": float(tier.get("max_order_value") or 0) if tier.get("max_order_value") is not None else None,
            "commission_percentage": float(tier.get("commission_percentage") or 0),
            "fixed_fee": float(tier.get("fixed_fee") or 0),
        })

    version = CountryConfigVersion(
        country_code=country.code,
        config_type="commission_tiers",
        version=_next_version(db, country.code, "commission_tiers"),
        payload_json=_to_json({"tiers": normalized}),
        status="draft",
        draft_by=current_user.get("id"),
        created_at=_utcnow(),
    )
    db.add(version)
    record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="create_draft",
        entity="country_commission_tiers",
        entity_key=f"{country.code}:v{version.version}",
        before=None,
        after={"tiers": normalized},
    )
    db.commit()
    db.refresh(version)
    return {"message": "Commission tiers draft created", "version_id": version.id, "version": version.version}


def list_country_versions(code: str, current_user: dict, db: Session, config_type: str | None = None) -> list[dict[str, Any]]:
    normalized_code = normalize_country_code(code)
    query = db.query(CountryConfigVersion).filter(CountryConfigVersion.country_code == normalized_code)
    if config_type:
        query = query.filter(CountryConfigVersion.config_type == config_type)
    rows = query.order_by(CountryConfigVersion.created_at.desc(), CountryConfigVersion.version.desc()).all()
    return [
        {
            "id": row.id,
            "country_code": row.country_code,
            "config_type": row.config_type,
            "version": row.version,
            "status": row.status,
            "draft_by": row.draft_by,
            "approved_by": row.approved_by,
            "published_at": row.published_at,
            "effective_from": row.effective_from,
            "created_at": row.created_at,
            "payload": _from_json(row.payload_json, default={}),
        }
        for row in rows
    ]


def approve_country_version(code: str, version_id: int, current_user: dict, db: Session) -> dict[str, Any]:
    version = db.query(CountryConfigVersion).filter(
        CountryConfigVersion.id == version_id,
        CountryConfigVersion.country_code == normalize_country_code(code),
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="Config version not found")

    if version.status != "draft":
        raise HTTPException(status_code=409, detail="Only draft versions can be approved")

    version.status = "approved"
    version.approved_by = current_user.get("id")
    record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="approve",
        entity="country_config_version",
        entity_key=f"{version.country_code}:{version.config_type}:v{version.version}",
        before={"status": "draft"},
        after={"status": "approved"},
    )
    db.commit()
    db.refresh(version)
    return {"message": "Version approved", "version_id": version.id, "status": version.status}


def publish_country_version(code: str, version_id: int, current_user: dict, db: Session) -> dict[str, Any]:
    version = db.query(CountryConfigVersion).filter(
        CountryConfigVersion.id == version_id,
        CountryConfigVersion.country_code == normalize_country_code(code),
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="Config version not found")

    if version.status not in {"approved", "draft"}:
        raise HTTPException(status_code=409, detail="Version cannot be published")

    row = _apply_version_payload(version, db)
    version.status = "published"
    version.approved_by = version.approved_by or current_user.get("id")
    version.published_at = _utcnow()
    record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="publish",
        entity="country_config_version",
        entity_key=f"{version.country_code}:{version.config_type}:v{version.version}",
        before={"status": "approved" if version.approved_by else "draft"},
        after={"status": "published"},
    )
    db.commit()
    db.refresh(version)
    return {"message": "Version published", "version_id": version.id, "status": version.status, "published_at": version.published_at}


def _apply_version_payload(row: CountryConfigVersion, db: Session) -> None:
    country = _get_country_or_404(db, row.country_code)
    payload = _from_json(row.payload_json, default={})

    if row.config_type == "tax":
        country.tax_type = str(payload.get("tax_type") or country.tax_type).upper()
        country.tax_rate = _to_decimal(payload.get("tax_rate", country.tax_rate), field="tax_rate")
        country.tax_name = str(payload.get("tax_name") or country.tax_name)
        country.tax_inclusive = bool(payload.get("tax_inclusive", country.tax_inclusive))
        country.tax_exempt_categories_json = _to_json(payload.get("tax_exempt_categories", []))
        country.tax_reduced_rates_json = _to_json(payload.get("tax_reduced_rates", {}))
    elif row.config_type == "logistics":
        country.logistics_model = str(payload.get("logistics_model") or country.logistics_model).lower()
        country.default_vehicle_type = payload.get("default_vehicle_type")
        country.base_rate = _to_decimal(payload["base_rate"], field="base_rate") if payload.get("base_rate") is not None else None
        country.per_km_rate = _to_decimal(payload["per_km_rate"], field="per_km_rate") if payload.get("per_km_rate") is not None else None
        country.minimum_charge = _to_decimal(payload["minimum_charge"], field="minimum_charge") if payload.get("minimum_charge") is not None else None
        country.weight_surcharge_rate = _to_decimal(payload["weight_surcharge_rate"], field="weight_surcharge_rate") if payload.get("weight_surcharge_rate") is not None else None
        country.weight_surcharge_threshold_kg = (
            _to_decimal(payload["weight_surcharge_threshold_kg"], field="weight_surcharge_threshold_kg")
            if payload.get("weight_surcharge_threshold_kg") is not None
            else None
        )
        zones = payload.get("delivery_zones")
        if zones is None:
            zones = payload.get("oman_zones")
        if isinstance(zones, list) and country.logistics_model == "zone":
            existing = {zone.zone_code: zone for zone in db.query(OmanDeliveryZone).all()}
            for zone_payload in zones:
                if not isinstance(zone_payload, dict):
                    continue
                zone_code = str(zone_payload.get("zone_code") or "").strip().upper()
                if not zone_code:
                    continue
                zone = existing.get(zone_code) or OmanDeliveryZone(zone_code=zone_code, zone_name=zone_code)
                zone.zone_name = str(zone_payload.get("zone_name") or zone.zone_name)
                zone.description = str(zone_payload.get("description") or "").strip() or None
                zone.car_rate = _to_decimal(zone_payload.get("car_rate", zone.car_rate), field=f"{zone_code}.car_rate")
                zone.van_rate = _to_decimal(zone_payload.get("van_rate", zone.van_rate), field=f"{zone_code}.van_rate")
                zone.truck_rate = _to_decimal(zone_payload.get("truck_rate", zone.truck_rate), field=f"{zone_code}.truck_rate")
                zone.weight_surcharge_rate = _to_decimal(zone_payload.get("weight_surcharge_rate", zone.weight_surcharge_rate), field=f"{zone_code}.weight_surcharge_rate") if zone_payload.get("weight_surcharge_rate") is not None else None
                zone.weight_surcharge_threshold_kg = _to_decimal(zone_payload.get("weight_surcharge_threshold_kg", zone.weight_surcharge_threshold_kg), field=f"{zone_code}.weight_surcharge_threshold_kg") if zone_payload.get("weight_surcharge_threshold_kg") is not None else None
                zone.cities_json = _to_json(zone_payload.get("cities", []))
                zone.is_active = bool(zone_payload.get("is_active", True))
                zone.sort_order = int(zone_payload.get("sort_order", 0) or 0)
                if zone.id is None:
                    db.add(zone)
    elif row.config_type == "commission":
        rates = payload.get("rates") or []
        if isinstance(rates, list):
            existing_rows = {
                (entry.country_code, entry.category_slug): entry
                for entry in db.query(PayoutRuleCategory)
                .filter(PayoutRuleCategory.country_code == row.country_code)
                .all()
            }
            for item in rates:
                if not isinstance(item, dict):
                    continue
                slug = str(item.get("category_slug") or "").strip().lower()
                if not slug:
                    continue
                key = (row.country_code, slug)
                entry = existing_rows.get(key)
                if entry is None:
                    entry = PayoutRuleCategory(country_code=row.country_code, category_slug=slug)
                    db.add(entry)
                entry.commission_rate = _to_decimal(item.get("commission_rate", entry.commission_rate or 0), field=f"commission_rate[{slug}]")
                entry.notes = str(item.get("notes") or "").strip() or None
                entry.is_active = bool(item.get("is_active", True))
    elif row.config_type == "ops":
        payment_methods = payload.get("payment_methods", [])
        country.payment_methods_json = _to_json(payment_methods if isinstance(payment_methods, list) else [])

        feature_flags = payload.get("feature_flags", {})
        if isinstance(feature_flags, dict):
            existing_flags = {
                flag.feature_key: flag
                for flag in db.query(CountryFeatureFlag)
                .filter(CountryFeatureFlag.country_code == row.country_code)
                .all()
            }
            for feature_key, value in feature_flags.items():
                key = str(feature_key).strip()
                if not key:
                    continue
                flag = existing_flags.get(key)
                if flag is None:
                    flag = CountryFeatureFlag(country_code=row.country_code, feature_key=key)
                    db.add(flag)
                if isinstance(value, dict):
                    flag.is_enabled = bool(value.get("is_enabled", False))
                    flag.rollout_audience = str(value.get("rollout_audience") or "").strip() or None
                    flag.notes = str(value.get("notes") or "").strip() or None
                else:
                    flag.is_enabled = bool(value)
                flag.updated_at = _utcnow()
    elif row.config_type == "payment_gateways":
        gateways = payload.get("gateways") if isinstance(payload, dict) else payload
        if isinstance(gateways, list):
            country.payment_gateways_json = _to_json(gateways)

        country.updated_at = _utcnow()
    elif row.config_type == "logistics_providers":
        providers = payload.get("providers") if isinstance(payload, dict) else payload
        if isinstance(providers, list):
            country.logistics_providers_json = _to_json(providers)

        country.updated_at = _utcnow()
    elif row.config_type == "legal_rules":
        if isinstance(payload, dict):
            country.legal_rules_json = _to_json(payload)

        country.updated_at = _utcnow()
    elif row.config_type == "regions":
        regions = payload.get("regions") if isinstance(payload, dict) else payload
        if isinstance(regions, list):
            country.regions_json = _to_json(regions)

        country.updated_at = _utcnow()
    elif row.config_type == "supplier_requirements":
        if isinstance(payload, dict):
            country.supplier_requirements_json = _to_json(payload)

        country.updated_at = _utcnow()
    elif row.config_type == "payout_settings":
        if isinstance(payload, dict):
            country.payout_settings_json = _to_json(payload)

        country.updated_at = _utcnow()
    elif row.config_type == "commission_tiers":
        tiers = payload.get("tiers") if isinstance(payload, dict) else payload
        if isinstance(tiers, list):
            country.commission_tiers_json = _to_json(tiers)

        country.updated_at = _utcnow()
    elif row.config_type == "product_restrictions":
        restrictions = payload.get("restrictions") if isinstance(payload, dict) else payload
        if isinstance(restrictions, list):
            country.product_restrictions_json = _to_json(restrictions)

        country.updated_at = _utcnow()
    elif row.config_type == "address_format":
        if isinstance(payload, dict):
            fmt = payload.get("address_format", payload)
            if isinstance(fmt, dict):
                country.address_format_json = _to_json(fmt)
    elif row.config_type == "date_format":
        if isinstance(payload, dict):
            fmt = str(payload.get("date_format", country.date_format) or "DD/MM/YYYY").strip()
            country.date_format = fmt

    country.updated_at = _utcnow()


def rollback_country_to_version(code: str, version_id: int, current_user: dict, db: Session) -> dict[str, Any]:
    version = db.query(CountryConfigVersion).filter(
        CountryConfigVersion.id == version_id,
        CountryConfigVersion.country_code == normalize_country_code(code),
        CountryConfigVersion.status == "published",
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="Published version not found")

    _apply_version_payload(version, db)
    rollback_row = CountryConfigVersion(
        country_code=version.country_code,
        config_type=version.config_type,
        version=_next_version(db, version.country_code, version.config_type),
        payload_json=version.payload_json,
        status="rolled_back",
        draft_by=current_user.get("id"),
        approved_by=current_user.get("id"),
        published_at=_utcnow(),
        created_at=_utcnow(),
    )
    db.add(rollback_row)
    record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="rollback",
        entity="country_config_version",
        entity_key=f"{version.country_code}:{version.config_type}:v{version.version}",
        before=None,
        after={"rollback_to_version": version.version},
    )
    db.commit()
    db.refresh(rollback_row)
    return {
        "message": "Rollback applied",
        "rolled_back_to": version.version,
        "new_version": rollback_row.version,
        "status": rollback_row.status,
    }


def list_country_commissions(code: str, current_user: dict, db: Session) -> list[dict[str, Any]]:
    normalized_code = normalize_country_code(code)
    rows = (
        db.query(PayoutRuleCategory)
        .filter(PayoutRuleCategory.country_code == normalized_code)
        .order_by(PayoutRuleCategory.category_slug.asc())
        .all()
    )
    return [
        {
            "id": row.id,
            "country_code": row.country_code,
            "category_slug": row.category_slug,
            "commission_rate": float(row.commission_rate),
            "notes": row.notes,
            "is_active": bool(row.is_active),
            "updated_at": row.updated_at,
        }
        for row in rows
    ]


def preview_country_tax(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    from services.tax_service import calculate_tax
    amount = _to_decimal(payload.get("amount", "0"), field="amount")
    category = str(payload.get("category") or "").strip() or None
    inclusive = payload.get("inclusive")
    if inclusive is not None:
        inclusive = bool(inclusive)

    result = calculate_tax(amount, code, db, category=category, inclusive=inclusive)
    result["tax_rate"] = float(result["tax_rate"])
    result["tax_amount"] = float(result["tax_amount"])
    result["net_amount"] = float(result["net_amount"])
    result["total_amount"] = float(result["total_amount"])
    return result


def get_country_feature_flags(code: str, current_user: dict, db: Session) -> list[dict[str, Any]]:
    normalized_code = normalize_country_code(code)
    rows = (
        db.query(CountryFeatureFlag)
        .filter(CountryFeatureFlag.country_code == normalized_code)
        .order_by(CountryFeatureFlag.feature_key.asc())
        .all()
    )
    return [
        {
            "id": row.id,
            "country_code": row.country_code,
            "feature_key": row.feature_key,
            "is_enabled": bool(row.is_enabled),
            "rollout_audience": row.rollout_audience,
            "notes": row.notes,
            "updated_at": row.updated_at,
        }
        for row in rows
    ]


def list_country_delivery_zones(code: str, current_user: dict, db: Session) -> list[dict[str, Any]]:
    country = _get_country_or_404(db, code)
    if str(country.logistics_model or "").lower() != "zone":
        return []

    rows = db.query(OmanDeliveryZone).order_by(OmanDeliveryZone.sort_order.asc(), OmanDeliveryZone.zone_code.asc()).all()
    return [
        {
            "zone_code": row.zone_code,
            "zone_name": row.zone_name,
            "description": row.description,
            "car_rate": float(row.car_rate),
            "van_rate": float(row.van_rate),
            "truck_rate": float(row.truck_rate),
            "weight_surcharge_rate": float(row.weight_surcharge_rate) if row.weight_surcharge_rate is not None else None,
            "weight_surcharge_threshold_kg": float(row.weight_surcharge_threshold_kg) if row.weight_surcharge_threshold_kg is not None else None,
            "cities": _from_json(row.cities_json, default=[]),
            "is_active": bool(row.is_active),
            "sort_order": row.sort_order,
        }
        for row in rows
    ]


def list_country_cities(
    code: str,
    current_user: dict,
    db: Session,
    *,
    query: str | None = None,
    limit: int = 50,
    include_inactive: bool = False,
) -> dict[str, Any]:
    cc = code.upper()

    q = db.query(CountryCity).filter(CountryCity.country_code == cc)
    if not include_inactive:
        q = q.filter(CountryCity.is_active == True)
    if query:
        like = f"%{query.strip()}%"
        q = q.filter(CountryCity.name.ilike(like))
    q = q.order_by(CountryCity.population.desc().nullslast(), CountryCity.name.asc())
    q = q.limit(limit)

    db_cities = q.all()
    return {
        "code": cc,
        "cities": [
            {
                "id": c.id,
                "name": c.name,
                "region": c.region or "",
                "latitude": float(c.latitude) if c.latitude is not None else None,
                "longitude": float(c.longitude) if c.longitude is not None else None,
                "population": c.population,
                "is_active": bool(c.is_active),
            }
            for c in db_cities
        ],
        "source": "database",
    }


def list_country_staff(country_code: str, current_user: dict, db: Session) -> list[dict]:
    rows = db.query(CountryStaffAssignment).filter(
        CountryStaffAssignment.country_code == country_code.upper(),
        CountryStaffAssignment.is_active == True,
    ).order_by(CountryStaffAssignment.created_at.desc()).all()
    user_ids = [r.user_id for r in rows]
    users = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "country_code": r.country_code,
            "role_in_country": r.role_in_country,
            "user_name": users.get(r.user_id, {}).username if isinstance(users.get(r.user_id, {}), User) else getattr(users.get(r.user_id), "username", ""),
            "user_email": users.get(r.user_id, {}).email if isinstance(users.get(r.user_id, {}), User) else getattr(users.get(r.user_id), "email", ""),
            "is_active": r.is_active,
            "assigned_by": r.assigned_by,
            "created_at": r.created_at,
        }
        for r in rows
        if r.user_id in users
    ]


def assign_staff_to_country(country_code: str, user_id: int, role_in_country: str, current_user: dict, db: Session) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.query(CountryConfig).filter(CountryConfig.code == country_code.upper()).first()
    existing = db.query(CountryStaffAssignment).filter(
        CountryStaffAssignment.user_id == user_id,
        CountryStaffAssignment.country_code == country_code.upper(),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Staff already assigned to this country")
    assignment = CountryStaffAssignment(
        user_id=user_id,
        country_code=country_code.upper(),
        role_in_country=role_in_country,
        assigned_by=current_user.get("id"),
    )
    db.add(assignment)
    record_admin_change(db, actor_id=current_user.get("id"), action="assign_staff", entity="country_staff", entity_key=f"{country_code}:{user_id}", before=None, after={"user_id": user_id, "role": role_in_country})
    db.commit()
    db.refresh(assignment)
    return {"id": assignment.id, "user_id": user_id, "country_code": country_code.upper(), "role_in_country": role_in_country}


def unassign_staff_from_country(country_code: str, user_id: int, current_user: dict, db: Session) -> dict:
    assignment = db.query(CountryStaffAssignment).filter(
        CountryStaffAssignment.user_id == user_id,
        CountryStaffAssignment.country_code == country_code.upper(),
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    assignment.is_active = False
    record_admin_change(db, actor_id=current_user.get("id"), action="unassign_staff", entity="country_staff", entity_key=f"{country_code}:{assignment.user_id}", before={"active": True}, after={"active": False})
    db.commit()
    return {"message": "Staff unassigned"}


def list_country_communications(country_code: str, current_user: dict, db: Session, category: str | None = None) -> list[dict]:
    q = db.query(CountryCommunication).filter(CountryCommunication.country_code == country_code.upper())
    if category:
        q = q.filter(CountryCommunication.category == category)
    rows = q.order_by(CountryCommunication.created_at.desc()).limit(100).all()
    return [
        {
            "id": r.id,
            "from_user_id": r.from_user_id,
            "to_user_id": r.to_user_id,
            "subject": r.subject,
            "body": r.body,
            "priority": r.priority,
            "status": r.status,
            "category": r.category,
            "created_at": r.created_at,
            "read_at": r.read_at,
        }
        for r in rows
    ]


def send_country_communication(country_code: str, payload: dict, current_user: dict, db: Session) -> dict:
    comm = CountryCommunication(
        country_code=country_code.upper(),
        from_user_id=current_user.get("id"),
        to_user_id=payload.get("to_user_id"),
        subject=str(payload.get("subject", "")).strip(),
        body=str(payload.get("body", "")).strip(),
        priority=str(payload.get("priority", "normal")).lower(),
        category=str(payload.get("category", "")).strip() or None,
    )
    if not comm.subject or not comm.body:
        raise HTTPException(status_code=422, detail="Subject and body are required")
    db.add(comm)
    db.commit()
    db.refresh(comm)
    return {"id": comm.id, "status": comm.status, "created_at": comm.created_at}


def mark_communication_read(comm_id: int, current_user: dict, db: Session) -> dict:
    comm = db.query(CountryCommunication).filter(CountryCommunication.id == comm_id).first()
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")
    if comm.to_user_id and comm.to_user_id != current_user.get("id"):
        role = str(current_user.get("role") or "").lower()
        if role != "admin":
            raise HTTPException(status_code=403, detail="Only recipient or admin can mark as read")
    comm.status = "read"
    comm.read_at = _utcnow()
    db.commit()
    return {"message": "Marked as read"}


def list_cross_country_sessions(country_code: str, current_user: dict, db: Session) -> list[dict]:
    q = db.query(CrossCountryCustomerSession).filter(
        CrossCountryCustomerSession.target_country_code == country_code.upper(),
    ).order_by(CrossCountryCustomerSession.created_at.desc()).limit(50).all()
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "source_country_code": r.source_country_code,
            "target_country_code": r.target_country_code,
            "conversion": r.conversion,
            "order_id": r.order_id,
            "created_at": r.created_at,
        }
        for r in q
    ]


def list_payout_rules_categories(country_code: str, current_user: dict, db: Session) -> list[dict]:
    normalized_code = normalize_country_code(country_code)
    country = db.query(CountryConfig).filter(CountryConfig.code == normalized_code).first()
    if not country:
        return []
    payout_rules_raw = _from_json(country.payout_settings_json, default=[])
    return payout_rules_raw if isinstance(payout_rules_raw, list) else []


def create_payout_rule_category(country_code: str, payload: dict, current_user: dict, db: Session) -> dict:
    country = _get_country_or_404(db, country_code)
    rule_id = str(payload.get("rule_id") or payload.get("category_slug") or "")
    if not rule_id:
        raise HTTPException(status_code=422, detail="rule_id or category_slug is required")
    rule = {
        "rule_id": rule_id,
        "name": payload.get("name") or rule_id,
        "type": payload.get("type") or "category",
        "threshold_min": payload.get("threshold_min"),
        "threshold_max": payload.get("threshold_max"),
        "payout_rate": float(payload.get("payout_rate", 0)),
        "fixed_fee": float(payload.get("fixed_fee", 0)),
        "currency": payload.get("currency"),
    }
    existing = _from_json(country.payout_settings_json, default=[])
    if not isinstance(existing, list):
        existing = []
    existing = [r for r in existing if r.get("rule_id") != rule_id]
    existing.append(rule)
    country.payout_settings_json = _to_json(existing)
    country.updated_at = _utcnow()
    db.commit()
    return {"message": "Payout rule created", "rule": rule}


def list_payout_rules_products(country_code: str, current_user: dict, db: Session) -> list[dict]:
    return list_payout_rules_categories(country_code, current_user, db)


def create_payout_rule_product(country_code: str, payload: dict, current_user: dict, db: Session) -> dict:
    payload_copy = payload.copy()
    payload_copy["type"] = "product"
    return create_payout_rule_category(country_code, payload_copy, current_user, db)


def delete_payout_rule(country_code: str, rule_id: str, current_user: dict, db: Session) -> dict:
    country = _get_country_or_404(db, country_code)
    existing = _from_json(country.payout_settings_json, default=[])
    if not isinstance(existing, list):
        existing = []
    remaining = [r for r in existing if str(r.get("rule_id")) != str(rule_id)]
    if len(remaining) == len(existing):
        raise HTTPException(status_code=404, detail="Payout rule not found")
    country.payout_settings_json = _to_json(remaining)
    country.updated_at = _utcnow()
    db.commit()
    return {"message": "Payout rule deleted", "rule_id": rule_id}


def list_country_delivery_zones_legacy(db: Session) -> list[dict]:
    rows = db.query(OmanDeliveryZone).order_by(OmanDeliveryZone.sort_order.asc(), OmanDeliveryZone.zone_code.asc()).all()
    return [
        {
            "zone_code": row.zone_code,
            "zone_name": row.zone_name,
            "description": row.description,
            "car_rate": float(row.car_rate),
            "van_rate": float(row.van_rate),
            "truck_rate": float(row.truck_rate),
            "weight_surcharge_rate": float(row.weight_surcharge_rate) if row.weight_surcharge_rate is not None else None,
            "weight_surcharge_threshold_kg": float(row.weight_surcharge_threshold_kg) if row.weight_surcharge_threshold_kg is not None else None,
            "cities": _from_json(row.cities_json, default=[]),
            "is_active": bool(row.is_active),
            "sort_order": row.sort_order,
        }
        for row in rows
    ]


def test_gateway_connection(code: str, gateway_id: str, environment: str, current_user: dict, db: Session) -> dict[str, Any]:
    from services.payment_engine import PaymentEngine
    engine = PaymentEngine(db)
    result = engine.test_gateway_connection(country_code=code, gateway_id=gateway_id, environment=environment)
    return {
        "success": result.success,
        "message": result.message,
        "latency_ms": result.latency_ms,
        "country_code": code,
        "gateway_id": gateway_id,
        "environment": environment,
    }


# ── Payout rules model aliases ───────────────────────────────────────────────

# For backward compatibility, use PayoutRuleCategory and PayoutRuleProduct
# as they serve as the commission and product payout rules respectively

# ── Archive / Restore / Toggle functions ─────────────────────────────────────────

def archive_country(db: Session, code: str, current_user: dict) -> dict[str, Any]:
    country = _get_country_or_404(db, code)
    if bool(country.is_active):
        country.is_active = False
        record_admin_change(
            db,
            actor_id=current_user.get("id"),
            action="archive",
            entity="country",
            entity_key=country.code,
            before={"is_active": True},
            after={"is_active": False},
        )
        db.commit()
    return {"message": "Country archived", "code": country.code}


def restore_country(db: Session, code: str, current_user: dict) -> dict[str, Any]:
    country = _get_country_or_404(db, code)
    if not bool(country.is_active):
        country.is_active = True
        record_admin_change(
            db,
            actor_id=current_user.get("id"),
            action="restore",
            entity="country",
            entity_key=country.code,
            before={"is_active": False},
            after={"is_active": True},
        )
        db.commit()
    return {"message": "Country restored", "code": country.code}


def toggle_country_active(db: Session, code: str, current_user: dict) -> dict[str, Any]:
    country = _get_country_or_404(db, code)
    country.is_active = not bool(country.is_active)
    record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="toggle_active",
        entity="country",
        entity_key=country.code,
        before={"is_active": not bool(country.is_active)},
        after={"is_active": bool(country.is_active)},
    )
    db.commit()
    return {"message": "Country activated" if country.is_active else "Country deactivated", "is_active": bool(country.is_active)}


def hard_delete_country(db: Session, code: str) -> None:
    country = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if country:
        db.delete(country)
        db.commit()


def bulk_archive_countries(db: Session, ids: list[str], current_user: dict) -> dict[str, Any]:
    codes = [c.upper() for c in ids if c]
    countries = db.query(CountryConfig).filter(CountryConfig.code.in_(codes)).all()
    for c in countries:
        if bool(c.is_active):
            c.is_active = False
    record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="bulk_archive",
        entity="countries",
        entity_key=",".join(codes),
        before=None,
        after={"codes": codes, "count": len(countries)},
    )
    db.commit()
    return {"message": f"{len(countries)} countries archived", "codes": codes}


def bulk_restore_countries(db: Session, ids: list[str], current_user: dict) -> dict[str, Any]:
    codes = [c.upper() for c in ids if c]
    countries = db.query(CountryConfig).filter(CountryConfig.code.in_(codes)).all()
    for c in countries:
        if not bool(c.is_active):
            c.is_active = True
    record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="bulk_restore",
        entity="countries",
        entity_key=",".join(codes),
        before=None,
        after={"codes": codes, "count": len(countries)},
    )
    db.commit()
    return {"message": f"{len(countries)} countries restored", "codes": codes}


# ── City management functions ─────────────────────────────────────────────────

def create_city(db: Session, code: str, body: dict[str, Any]) -> dict[str, Any]:
    country = _get_country_or_404(db, code)
    city = CountryCity(
        country_code=code.upper(),
        name=str(body.get("name", "")).strip(),
        region=str(body.get("region", "")).strip() or None,
        latitude=float(body["lat"]) if body.get("lat") is not None else None,
        longitude=float(body["lng"]) if body.get("lng") is not None else None,
        population=int(body.get("population")) if body.get("population") is not None else None,
        source=str(body.get("source", "openmeteo")),
        is_active=bool(body.get("is_active", True)),
        sort_order=int(body.get("sort_order", 0) or 0),
    )
    db.add(city)
    db.commit()
    db.refresh(city)
    return {"message": "City created", "id": city.id, "name": city.name}


def update_city(db: Session, code: str, city_id: int, body: dict[str, Any]) -> dict[str, Any]:
    city = _get_city_or_404(db, code, city_id)
    if "name" in body:
        city.name = str(body["name"]).strip()
    if "region" in body:
        city.region = str(body.get("region", "")).strip() or None
    if "latitude" in body:
        city.latitude = float(body["latitude"]) if body.get("latitude") is not None else None
    if "longitude" in body:
        city.longitude = float(body["longitude"]) if body.get("longitude") is not None else None
    if "population" in body:
        city.population = int(body.get("population")) if body.get("population") is not None else None
    if "is_active" in body:
        city.is_active = bool(body["is_active"])
    if "sort_order" in body:
        city.sort_order = int(body.get("sort_order", 0) or 0)
    db.commit()
    db.refresh(city)
    return {"message": "City updated", "id": city.id}


def delete_city(db: Session, code: str, city_id: int) -> None:
    city = _get_city_or_404(db, code, city_id)
    db.delete(city)
    db.commit()


# ── Feature flag management functions ───────────────────────────────────────────

def create_feature_flag(db: Session, code: str, body: dict[str, Any], current_user: dict = None) -> dict[str, Any]:
    normalized_code = normalize_country_code(code)
    existing_country = db.query(CountryConfig).filter(CountryConfig.code == normalized_code).first()
    if existing_country:
        for key, value in body.items():
            if key == "is_enabled":
                continue
            flag = CountryFeatureFlag(
                country_code=normalized_code,
                feature_key=str(key).strip(),
                is_enabled=bool(value.get("is_enabled", False)) if isinstance(value, dict) else bool(value),
                rollout_audience=str(value.get("rollout_audience", "")).strip() or None if isinstance(value, dict) else None,
                notes=str(value.get("notes", "")).strip() or None if isinstance(value, dict) else None,
            )
            db.add(flag)
        db.commit()
        return {"message": "Feature flag created", "country_code": normalized_code}
    raise HTTPException(status_code=404, detail="Country not found")


def update_feature_flag(db: Session, code: str, key: str, body: dict[str, Any], current_user: dict = None) -> dict[str, Any]:
    flag = _get_feature_flag_or_404(db, code, key)
    if "is_enabled" in body:
        flag.is_enabled = bool(body["is_enabled"])
    if "rollout_audience" in body:
        flag.rollout_audience = str(body.get("rollout_audience", "")).strip() or None
    if "notes" in body:
        flag.notes = str(body.get("notes", "")).strip() or None
    db.commit()
    db.refresh(flag)
    return {"message": "Feature flag updated", "feature_key": flag.feature_key}


def delete_feature_flag(db: Session, code: str, key: str) -> None:
    flag = _get_feature_flag_or_404(db, code, key)
    db.delete(flag)
    db.commit()


# ── Commission rate management functions ───────────────────────────────────────

def create_commission_rate(db: Session, code: str, payload: dict[str, Any], current_user: dict = None) -> dict[str, Any]:
    country = _get_country_or_404(db, code)
    rate = PayoutRuleCategory(
        country_code=code.upper(),
        category_slug=str(payload.get("supplier_tier", "standard").strip().lower()),
        commission_rate=_to_decimal(payload.get("commission_percentage", 0), field="commission_rate"),
        notes=str(payload.get("notes", "")).strip() or None,
        is_active=bool(payload.get("is_active", True)),
        fixed_fee=_to_decimal(payload.get("fixed_fee", 0), field="fixed_fee"),
    )
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return {"message": "Commission rate created", "id": rate.id, "category_slug": rate.category_slug}


def delete_commission_rate(db: Session, code: str, tier: str, name: str, current_user: dict = None) -> dict[str, Any]:
    row = (
        db.query(PayoutRuleCategory)
        .filter(
            PayoutRuleCategory.country_code == code.upper(),
            PayoutRuleCategory.category_slug == tier.lower(),
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Commission rate not found")
    db.delete(row)
    db.commit()
    return {"message": "Commission rate deleted", "tier": tier}


def list_commission_rates(db: Session, code: str, skip: int = 0, limit: int = 20) -> list[dict[str, Any]]:
    rows = (
        db.query(PayoutRuleCategory)
        .filter(PayoutRuleCategory.country_code == code.upper())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": row.id,
            "country_code": row.country_code,
            "tier": row.category_slug,
            "name": row.name or row.category_slug,
            "commission_percentage": float(row.commission_rate),
            "fixed_fee": float(row.fixed_fee) if row.fixed_fee else 0,
            "is_active": bool(row.is_active),
        }
        for row in rows
    ]


# ── Bulk city update ─────────────────────────────────────────────────────────────

def update_country_cities_bulk(
    code: str,
    payload: dict[str, Any],
    current_user: dict,
    db: Session,
) -> dict[str, Any]:
    country = _get_country_or_404(db, code)
    cities_data = payload.get("cities", [])
    if not isinstance(cities_data, list):
        cities_data = []

    for c in cities_data:
        if not isinstance(c, dict):
            continue
        city_id = c.get("id")
        if city_id:
            city = db.query(CountryCity).filter(CountryCity.id == city_id, CountryCity.country_code == code.upper()).first()
            if city:
                if "name" in c:
                    city.name = str(c["name"]).strip()
                if "region" in c:
                    city.region = str(c.get("region", "")).strip() or None
                if "latitude" in c:
                    city.latitude = float(c["latitude"]) if c.get("latitude") is not None else None
                if "longitude" in c:
                    city.longitude = float(c["longitude"]) if c.get("longitude") is not None else None
                if "population" in c:
                    city.population = int(c.get("population")) if c.get("population") is not None else None
                if "is_active" in c:
                    city.is_active = bool(c["is_active"])
                if "sort_order" in c:
                    city.sort_order = int(c.get("sort_order", 0) or 0)
        else:
            city = CountryCity(
                country_code=code.upper(),
                name=str(c.get("name", "")).strip(),
                region=str(c.get("region", "")).strip() or None,
                latitude=float(c.get("latitude")) if c.get("latitude") is not None else None,
                longitude=float(c.get("longitude")) if c.get("longitude") is not None else None,
                population=int(c.get("population")) if c.get("population") is not None else None,
                is_active=bool(c.get("is_active", True)),
                sort_order=int(c.get("sort_order", 0) or 0),
            )
            db.add(city)

    db.commit()
    cities = db.query(CountryCity).filter(CountryCity.country_code == code.upper()).all()
    return {"message": "Cities updated", "count": len(cities), "country_code": code.upper()}
