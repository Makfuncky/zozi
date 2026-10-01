"""Infrastructure geography wrapper.

Delegates to ``providers.geography`` so that middleware and other
infrastructure consumers never import directly from providers.
"""
from __future__ import annotations

from providers.geography.geoip import lookup_coordinates
from providers.geography.ip import detect_country_from_ip

__all__ = ["detect_country_from_ip", "lookup_coordinates"]
