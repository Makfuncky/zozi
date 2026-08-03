from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from data.models import CountryConfig
from data.services_logistics_partner_pricing import normalize_country_code
from utils.config import settings
from utils.money import round_money, to_decimal


def _safe_json_list(raw: str | None) -> set[str]:
    if not raw:
        return set()
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return set()
    if not isinstance(parsed, list):
        return set()
    return {str(item).strip().lower() for item in parsed if str(item).strip()}


def _safe_json_map(raw: str | None) -> dict[str, Decimal]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    if not isinstance(parsed, dict):
        return {}

    normalized: dict[str, Decimal] = {}
    for key, value in parsed.items():
        k = str(key).strip().lower()
        if not k:
            continue
        normalized[k] = to_decimal(value)
    return normalized


def get_country_config(db: Session, country_code: str) -> CountryConfig:
    code = normalize_country_code(country_code)
    if not code:
        raise ValueError("Unknown country: empty code")

    config = (
        db.query(CountryConfig)
        .filter(CountryConfig.code == code, CountryConfig.is_active == True)  # noqa: E712
        .first()
    )
    if not config:
        raise ValueError(f"Unknown country: {code}")
    return config


def resolve_tax_rate(config: CountryConfig, category: str | None = None) -> Decimal:
    category_key = (category or "").strip().lower()

    exempt = _safe_json_list(getattr(config, "tax_exempt_categories_json", None))
    if category_key and category_key in exempt:
        return Decimal("0.0000")

    reduced = _safe_json_map(getattr(config, "tax_reduced_rates_json", None))
    if category_key and category_key in reduced:
        return reduced[category_key]

    return to_decimal(getattr(config, "tax_rate", 0) or 0)


def calculate_tax(
    amount: Decimal,
    country_code: str,
    db: Session,
    *,
    category: str | None = None,
    inclusive: bool | None = None,
) -> dict[str, Any]:
    config = get_country_config(db, country_code)
    amount_decimal = round_money(to_decimal(amount))
    rate = resolve_tax_rate(config, category)

    if inclusive is None:
        inclusive_mode = bool(getattr(config, "tax_inclusive", False))
    else:
        inclusive_mode = bool(inclusive)

    if inclusive_mode and rate > 0:
        net_amount = round_money(amount_decimal / (Decimal("1.0") + rate))
        tax_amount = round_money(amount_decimal - net_amount)
        total_amount = amount_decimal
    else:
        tax_amount = round_money(amount_decimal * rate)
        net_amount = amount_decimal
        total_amount = round_money(amount_decimal + tax_amount)

    return {
        "country_code": normalize_country_code(country_code),
        "tax_type": str(getattr(config, "tax_type", "TAX") or "TAX"),
        "tax_name": str(getattr(config, "tax_name", "Tax") or "Tax"),
        "tax_rate": rate,
        "tax_amount": tax_amount,
        "net_amount": net_amount,
        "total_amount": total_amount,
        "is_inclusive": inclusive_mode,
        "currency": str(getattr(config, "currency", settings.default_currency) or settings.default_currency),
    }

