from __future__ import annotations

"""
Shipping Rate Calculator
=========================
Calculate shipping costs based on weight, dimensions, distance, and carrier.
Includes major carriers: FedEx, UPS, DHL, Aramex, local post.
Pure Python — zone-based pricing model.
"""
import logging
import math
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Carrier definitions
# ---------------------------------------------------------------------------
# Each carrier has:
#   - base_rate: flat fee per shipment
#   - per_kg: cost per kg
#   - per_cbm: cost per cubic meter (dimensional weight)
#   - zones: dict mapping country/region code to zone multiplier
#   - max_weight_kg: maximum weight allowed
#   - delivery_days: dict mapping zone to (min_days, max_days)

_CARRIERS: Dict[str, Dict[str, Any]] = {
    "fedex": {
        "name": "FedEx",
        "base_rate": 8.50,
        "per_kg": 2.80,
        "per_cbm": 180.0,
        "max_weight_kg": 150.0,
        "zones": {
            "US": 1.0, "CA": 1.1, "GB": 1.3, "DE": 1.3, "FR": 1.3,
            "AE": 1.5, "SA": 1.5, "QA": 1.5, "KW": 1.5, "BH": 1.5,
            "OM": 1.6, "JO": 1.6, "EG": 1.6, "IN": 1.7, "CN": 1.4,
            "JP": 1.4, "AU": 1.6, "BR": 1.8, "DEFAULT": 2.0,
        },
        "delivery_days": {
            1: (1, 2), 2: (2, 3), 3: (3, 5), 4: (4, 7),
            5: (5, 9), 6: (7, 12), 7: (10, 20),
        },
    },
    "ups": {
        "name": "UPS",
        "base_rate": 7.95,
        "per_kg": 2.65,
        "per_cbm": 175.0,
        "max_weight_kg": 150.0,
        "zones": {
            "US": 1.0, "CA": 1.1, "GB": 1.25, "DE": 1.25, "FR": 1.25,
            "AE": 1.45, "SA": 1.45, "QA": 1.45, "KW": 1.45, "BH": 1.45,
            "OM": 1.55, "JO": 1.55, "EG": 1.55, "IN": 1.65, "CN": 1.35,
            "JP": 1.35, "AU": 1.55, "BR": 1.75, "DEFAULT": 1.9,
        },
        "delivery_days": {
            1: (1, 2), 2: (2, 3), 3: (3, 5), 4: (4, 7),
            5: (5, 9), 6: (7, 12), 7: (10, 20),
        },
    },
    "dhl": {
        "name": "DHL",
        "base_rate": 9.25,
        "per_kg": 3.10,
        "per_cbm": 190.0,
        "max_weight_kg": 150.0,
        "zones": {
            "US": 1.05, "CA": 1.1, "GB": 1.2, "DE": 1.2, "FR": 1.2,
            "AE": 1.4, "SA": 1.4, "QA": 1.4, "KW": 1.4, "BH": 1.4,
            "OM": 1.5, "JO": 1.5, "EG": 1.5, "IN": 1.6, "CN": 1.3,
            "JP": 1.3, "AU": 1.5, "BR": 1.7, "DEFAULT": 1.85,
        },
        "delivery_days": {
            1: (1, 2), 2: (2, 3), 3: (2, 4), 4: (3, 6),
            5: (4, 8), 6: (6, 10), 7: (8, 18),
        },
    },
    "aramex": {
        "name": "Aramex",
        "base_rate": 6.50,
        "per_kg": 2.20,
        "per_cbm": 160.0,
        "max_weight_kg": 100.0,
        "zones": {
            "US": 1.2, "CA": 1.2, "GB": 1.2, "DE": 1.2, "FR": 1.2,
            "AE": 1.05, "SA": 1.05, "QA": 1.05, "KW": 1.05, "BH": 1.05,
            "OM": 1.1, "JO": 1.1, "EG": 1.1, "IN": 1.3, "CN": 1.25,
            "JP": 1.25, "AU": 1.3, "BR": 1.5, "DEFAULT": 1.6,
        },
        "delivery_days": {
            1: (2, 3), 2: (2, 4), 3: (3, 5), 4: (4, 7),
            5: (5, 9), 6: (7, 14), 7: (10, 21),
        },
    },
    "local_post": {
        "name": "Local Post",
        "base_rate": 3.50,
        "per_kg": 1.20,
        "per_cbm": 120.0,
        "max_weight_kg": 30.0,
        "zones": {
            "US": 1.0, "CA": 1.15, "GB": 1.3, "DE": 1.3, "FR": 1.3,
            "AE": 1.6, "SA": 1.6, "QA": 1.6, "KW": 1.6, "BH": 1.6,
            "OM": 1.7, "JO": 1.7, "EG": 1.7, "IN": 1.8, "CN": 1.5,
            "JP": 1.5, "AU": 1.7, "BR": 1.9, "DEFAULT": 2.2,
        },
        "delivery_days": {
            1: (2, 4), 2: (3, 6), 3: (5, 9), 4: (7, 14),
            5: (10, 21), 6: (14, 30), 7: (21, 45),
        },
    },
}

# Regional zone mapping (country code -> zone number)
_ZONE_MAP: Dict[str, int] = {
    "US": 1, "CA": 2, "GB": 3, "DE": 3, "FR": 3, "IT": 3, "ES": 3,
    "NL": 3, "BE": 3, "SE": 3, "NO": 3, "DK": 3, "FI": 3, "PL": 3,
    "AE": 4, "SA": 4, "QA": 4, "KW": 4, "BH": 4,
    "OM": 5, "JO": 5, "EG": 5, "IN": 5, "PK": 5,
    "CN": 4, "JP": 4, "KR": 4,
    "AU": 5, "NZ": 5, "BR": 5, "AR": 5, "ZA": 5,
}


def _get_zone(country_code: str) -> int:
    """Map a country code to a shipping zone (1-7)."""
    if not country_code:
        return 7
    return _ZONE_MAP.get(country_code.upper().strip(), 7)


def _get_zone_multiplier(carrier: Dict[str, Any], country_code: str) -> float:
    """Get the zone multiplier for a carrier and destination country."""
    zones = carrier["zones"]
    if not country_code:
        return zones.get("DEFAULT", 2.0)
    return zones.get(country_code.upper().strip(), zones.get("DEFAULT", 2.0))


def _dimensional_weight_kg(length_cm: float, width_cm: float, height_cm: float) -> float:
    """Compute dimensional (volumetric) weight in kg.

    Uses the standard divisor of 5000 (cm³ per kg).
    """
    volume_cm3 = length_cm * width_cm * height_cm
    return volume_cm3 / 5000.0


def get_available_carriers(destination_country: str) -> List[Dict[str, Any]]:
    """List available shipping carriers for a destination country.

    Args:
        destination_country: ISO country code (e.g., "US", "AE").

    Returns:
        List of carrier dicts with 'id', 'name', and 'available' keys.
    """
    results: List[Dict[str, Any]] = []
    for cid, carrier in _CARRIERS.items():
        zone = _get_zone(destination_country)
        multiplier = _get_zone_multiplier(carrier, destination_country)
        min_days, max_days = carrier["delivery_days"].get(zone, (14, 45))

        results.append({
            "id": cid,
            "name": carrier["name"],
            "available": True,
            "zone": zone,
            "zone_multiplier": multiplier,
            "max_weight_kg": carrier["max_weight_kg"],
            "estimated_delivery_days": {"min": min_days, "max": max_days},
        })
    return results


def calculate_shipping_rate(
    origin: Dict[str, str],
    destination: Dict[str, str],
    package: Dict[str, Any],
    carrier: Optional[str] = None,
) -> Dict[str, Any]:
    """Calculate shipping cost based on weight, dimensions, distance, and carrier.

    Args:
        origin: {"country": "US", "city": "NY", "postal": "10001"}
        destination: {"country": "US", "city": "LA", "postal": "90001"}
        package: {"weight_kg": 1.5, "length_cm": 30, "width_cm": 20, "height_cm": 10}
        carrier: Optional carrier ID (fedex, ups, dhl, aramex, local_post).
                 If None, uses the cheapest available carrier.

    Returns:
        Dict with carrier, rate breakdown, total cost, and currency.
    """
    weight_kg = float(package.get("weight_kg", 0))
    length_cm = float(package.get("length_cm", 0))
    width_cm = float(package.get("width_cm", 0))
    height_cm = float(package.get("height_cm", 0))
    dest_country = destination.get("country", "")

    if weight_kg <= 0:
        return {
            "error": "Package weight must be greater than zero.",
            "carrier": carrier or "unknown",
            "total": 0.0,
            "currency": "USD",
        }

    # Dimensional weight
    dim_weight = 0.0
    if length_cm > 0 and width_cm > 0 and height_cm > 0:
        dim_weight = _dimensional_weight_kg(length_cm, width_cm, height_cm)

    # Chargeable weight is the greater of actual and dimensional weight
    chargeable_weight = max(weight_kg, dim_weight)

    # Find carrier(s) to use
    carriers_to_check: List[str] = []
    if carrier:
        cid = carrier.lower().strip()
        if cid not in _CARRIERS:
            return {
                "error": f"Unknown carrier: {carrier}. Available: {list(_CARRIERS.keys())}",
                "carrier": carrier,
                "total": 0.0,
                "currency": "USD",
            }
        carriers_to_check = [cid]
    else:
        carriers_to_check = list(_CARRIERS.keys())

    best_rate: Optional[Dict[str, Any]] = None

    for cid in carriers_to_check:
        c = _CARRIERS[cid]

        # Weight limit check
        if weight_kg > c["max_weight_kg"]:
            continue

        zone = _get_zone(dest_country)
        multiplier = _get_zone_multiplier(c, dest_country)

        # Rate components
        base_fee = c["base_rate"]
        weight_fee = chargeable_weight * c["per_kg"]
        dim_fee = 0.0
        if dim_weight > weight_kg and length_cm > 0:
            dim_fee = dim_weight * c["per_cbm"] / 1000  # per_cbm is per cubic meter

        subtotal = base_fee + weight_fee + dim_fee
        total = round(subtotal * multiplier, 2)

        rate_info = {
            "carrier_id": cid,
            "carrier_name": c["name"],
            "base_fee": round(base_fee, 2),
            "weight_fee": round(weight_fee, 2),
            "dimensional_fee": round(dim_fee, 2),
            "zone_multiplier": multiplier,
            "chargeable_weight_kg": round(chargeable_weight, 3),
            "actual_weight_kg": round(weight_kg, 3),
            "dimensional_weight_kg": round(dim_weight, 3),
            "zone": zone,
            "total": total,
            "currency": "USD",
        }

        if best_rate is None or total < best_rate["total"]:
            best_rate = rate_info

    if best_rate is None:
        return {
            "error": "No carrier available for the given weight/destination.",
            "carrier": carrier or "unknown",
            "total": 0.0,
            "currency": "USD",
        }

    # Add origin/destination to result
    best_rate["origin"] = origin
    best_rate["destination"] = destination
    best_rate["package"] = package

    return best_rate


def estimate_delivery_days(
    origin: Dict[str, str],
    destination: Dict[str, str],
    carrier: str,
) -> Dict[str, Any]:
    """Estimate delivery days for a given carrier and route.

    Args:
        origin: {"country": "US", "city": "NY", "postal": "10001"}
        destination: {"country": "US", "city": "LA", "postal": "90001"}
        carrier: Carrier ID (fedex, ups, dhl, aramex, local_post).

    Returns:
        Dict with carrier, zone, min_days, max_days, and estimated_range.
    """
    cid = carrier.lower().strip()
    if cid not in _CARRIERS:
        return {
            "error": f"Unknown carrier: {carrier}. Available: {list(_CARRIERS.keys())}",
            "carrier": carrier,
            "min_days": 0,
            "max_days": 0,
        }

    c = _CARRIERS[cid]
    dest_country = destination.get("country", "")
    zone = _get_zone(dest_country)
    min_days, max_days = c["delivery_days"].get(zone, (14, 45))

    return {
        "carrier_id": cid,
        "carrier_name": c["name"],
        "origin": origin,
        "destination": destination,
        "zone": zone,
        "min_days": min_days,
        "max_days": max_days,
        "estimated_range": f"{min_days}-{max_days} business days",
    }


def compare_shipping_options(
    origin: Dict[str, str],
    destination: Dict[str, str],
    package: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Compare shipping rates across all available carriers.

    Args:
        origin: {"country": "US", "city": "NY", "postal": "10001"}
        destination: {"country": "US", "city": "LA", "postal": "90001"}
        package: {"weight_kg": 1.5, "length_cm": 30, "width_cm": 20, "height_cm": 10}

    Returns:
        List of rate dicts sorted by total cost ascending.
    """
    dest_country = destination.get("country", "")
    results: List[Dict[str, Any]] = []

    for cid, c in _CARRIERS.items():
        weight_kg = float(package.get("weight_kg", 0))

        # Skip carriers that can't handle the weight
        if weight_kg > c["max_weight_kg"]:
            results.append({
                "carrier_id": cid,
                "carrier_name": c["name"],
                "available": False,
                "reason": f"Exceeds max weight ({c['max_weight_kg']} kg)",
                "total": 0.0,
                "currency": "USD",
            })
            continue

        zone = _get_zone(dest_country)
        multiplier = _get_zone_multiplier(c, dest_country)

        # Calculate rate
        length_cm = float(package.get("length_cm", 0))
        width_cm = float(package.get("width_cm", 0))
        height_cm = float(package.get("height_cm", 0))
        dim_weight = 0.0
        if length_cm > 0 and width_cm > 0 and height_cm > 0:
            dim_weight = _dimensional_weight_kg(length_cm, width_cm, height_cm)

        chargeable_weight = max(weight_kg, dim_weight)
        base_fee = c["base_rate"]
        weight_fee = chargeable_weight * c["per_kg"]
        dim_fee = 0.0
        if dim_weight > weight_kg and length_cm > 0:
            dim_fee = dim_weight * c["per_cbm"] / 1000

        subtotal = base_fee + weight_fee + dim_fee
        total = round(subtotal * multiplier, 2)

        min_days, max_days = c["delivery_days"].get(zone, (14, 45))

        results.append({
            "carrier_id": cid,
            "carrier_name": c["name"],
            "available": True,
            "total": total,
            "currency": "USD",
            "zone": zone,
            "chargeable_weight_kg": round(chargeable_weight, 3),
            "base_fee": round(base_fee, 2),
            "weight_fee": round(weight_fee, 2),
            "dimensional_fee": round(dim_fee, 2),
            "zone_multiplier": multiplier,
            "estimated_delivery_days": {"min": min_days, "max": max_days},
        })

    # Sort: available first (by cost), then unavailable
    results.sort(
        key=lambda x: (not x.get("available", False), x.get("total", float("inf")))
    )

    return results
