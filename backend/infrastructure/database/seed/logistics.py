from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from infrastructure.database.seed.models import get_model


def quote_shipping_for_destination(
    db: Session,
    *,
    country: str | None,
    city: str | None = None,
    partner_id: int | None = None,
    supplier_city: str | None = None,
    total_weight_kg: Decimal | float | int | None = None,
    categories: list[str] | None = None,
    pickup_count: int | None = None,
    dropoff_count: int | None = None,
) -> dict[str, Any] | None:
    """Seed-only shipping quote resolver.

    Finds the active service area for the given partner + destination and
    computes a flat pricing breakdown from the seeded rate columns.
    """
    LogisticsPartnerServiceArea = get_model("LogisticsPartnerServiceArea")

    query = db.query(LogisticsPartnerServiceArea).filter(
        LogisticsPartnerServiceArea.partner_id == partner_id,
        LogisticsPartnerServiceArea.country_code == country,
        LogisticsPartnerServiceArea.is_active.is_(True),
    )
    if city:
        query = query.filter(LogisticsPartnerServiceArea.city_name == city)

    area = query.first()
    if area is None:
        return None

    weight = Decimal(str(total_weight_kg)) if total_weight_kg else Decimal("0")
    base_fee = Decimal(str(getattr(area, "charge_amount", 0) or 0))
    per_kg = Decimal(str(getattr(area, "per_kg_rate", 0) or 0))
    minimum = Decimal(str(getattr(area, "minimum_charge", 0) or 0))

    shipping_amount = base_fee + (per_kg * weight)
    if shipping_amount < minimum:
        shipping_amount = minimum

    pickup_charge = Decimal(str(getattr(area, "pickup_charge", 0) or 0))
    dropoff_charge = Decimal(str(getattr(area, "dropoff_charge", 0) or 0))

    return {
        "shipping_amount": shipping_amount,
        "currency": getattr(area, "currency", "AED") or "AED",
        "partner_id": area.partner_id,
        "service_area": {"id": area.id},
        "pricing_profile": None,
        "category_rules": [],
        "vehicle_rule": None,
        "pricing_breakdown": {
            "shipping_amount": shipping_amount,
            "pickup_charge": pickup_charge,
            "dropoff_charge": dropoff_charge,
        },
        "destination": {
            "country": country,
            "city": city,
            "country_code": country,
        },
    }
