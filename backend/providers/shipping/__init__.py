from __future__ import annotations

"""
Shipping Provider
==================
Shipping rate calculation, carrier comparison, and delivery estimation.
Pure Python — zone-based pricing model.
"""
from typing import Any, Dict, List, Optional

__all__ = [
    "calculate_shipping_rate",
    "get_available_carriers",
    "estimate_delivery_days",
    "compare_shipping_options",
]

from .shipping_calculator import (
    calculate_shipping_rate,
    get_available_carriers,
    estimate_delivery_days,
    compare_shipping_options,
)
