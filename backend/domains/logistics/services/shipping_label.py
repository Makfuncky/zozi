"""Shipping label helper for the logistics domain.

Wraps the shipping, QR, and barcode providers into a single high-level
``create_shipment_label`` operation. Lives in the services layer so the
``features`` module remains a pure feature-atom catalog.
"""
from __future__ import annotations

import logging

from pydantic import ValidationError

from domains.logistics.schemas.shipping_label_schemas import (
    ShipmentLabelData,
    ShipmentLabelDestination,
    validate_destination,
    validate_shipment_data,
)
from providers.barcode.barcode_generator import generate_code128
from providers.qr.qr_generator import generate_tracking_qr
from providers.shipping.shipping_calculator import (
    calculate_shipping_rate,
    compare_shipping_options,
    estimate_delivery_days,
    get_available_carriers,
)

logger = logging.getLogger(__name__)


def _coerce_to_dict(model_or_dict, validator):
    """Accept a Pydantic model or raw dict, validate, and return a plain dict."""
    if hasattr(model_or_dict, "model_dump"):
        model_or_dict = model_or_dict.model_dump()
    return validator(model_or_dict)


def create_shipment_label(shipment_data, destination):
    """Generate a shipping label with QR + barcode using shipping/QR/barcode providers."""
    shipment_data = _coerce_to_dict(shipment_data, validate_shipment_data)
    destination = _coerce_to_dict(destination, validate_destination)

    origin = {"country": shipment_data["origin_country"], "city": shipment_data["origin_city"]}
    package = {
        "weight_kg": shipment_data["weight_kg"],
        "length_cm": shipment_data.get("length_cm", 30),
        "width_cm": shipment_data.get("width_cm", 20),
        "height_cm": shipment_data.get("height_cm", 10),
    }
    try:
        rate = calculate_shipping_rate(origin, destination, package)
    except (ValueError, TypeError, RuntimeError) as exc:
        logger.exception("calculate_shipping_rate failed")
        rate = {"error": str(exc)}
    try:
        qr_code = generate_tracking_qr(shipment_data["tracking_number"])
    except (ValueError, TypeError, RuntimeError) as exc:
        logger.exception("generate_tracking_qr failed")
        qr_code = None
    try:
        barcode = generate_code128(shipment_data["tracking_number"])
    except (ValueError, TypeError, RuntimeError) as exc:
        logger.exception("generate_code128 failed")
        barcode = None
    return {"rate": rate, "qr_code": qr_code, "barcode": barcode}


__all__ = [
    "create_shipment_label",
    "ShipmentLabelData",
    "ShipmentLabelDestination",
    "validate_shipment_data",
    "validate_destination",
    "calculate_shipping_rate",
    "compare_shipping_options",
    "estimate_delivery_days",
    "get_available_carriers",
    "generate_tracking_qr",
    "generate_code128",
]
