"""
Auto logistics tier resolver (Step 8).

Maps a product's weight (kg) and optional dimensions ("LxWxH" in cm) to a
shipping tier used for downstream fulfilment/rate selection. Uses volumetric
weight (L*W*H / 5000) when it exceeds the actual weight, matching common GCC
courier conventions (Aramex, SMSA, etc.).
"""

from __future__ import annotations

import re
from typing import Optional, Dict

# Tier thresholds by chargeable weight (kg).
_TIERS = [
    (1.0, "light", "Small parcel / envelope"),
    (5.0, "standard", "Standard box"),
    (20.0, "heavy", "Large box / multi-piece"),
    (float("inf"), "freight", "Freight / pallet"),
]


def _parse_dimensions(dimensions: Optional[str]) -> Optional[float]:
    """Return volumetric weight (kg) from an 'LxWxH' (cm) string, else None."""
    if not dimensions:
        return None
    nums = re.findall(r"[\d.]+", dimensions)
    if len(nums) < 3:
        return None
    try:
        length, width, height = (float(nums[0]), float(nums[1]), float(nums[2]))
    except ValueError:
        return None
    if length <= 0 or width <= 0 or height <= 0:
        return None
    return (length * width * height) / 5000.0


def resolve_shipping_tier(
    weight_kg: Optional[float] = None,
    dimensions: Optional[str] = None,
) -> Dict[str, object]:
    """
    Resolve the chargeable weight and shipping tier.

    Returns ``{"tier": str, "label": str, "chargeable_weight_kg": float}``.
    Defaults to the ``standard`` tier when no data is provided.
    """
    actual = float(weight_kg) if weight_kg and weight_kg > 0 else 0.0
    volumetric = _parse_dimensions(dimensions) or 0.0
    chargeable = max(actual, volumetric)

    if chargeable <= 0:
        return {"tier": "standard", "label": "Standard box", "chargeable_weight_kg": 0.0}

    for threshold, tier, label in _TIERS:
        if chargeable <= threshold:
            return {
                "tier": tier,
                "label": label,
                "chargeable_weight_kg": round(chargeable, 3),
            }
    return {"tier": "freight", "label": "Freight / pallet", "chargeable_weight_kg": round(chargeable, 3)}

