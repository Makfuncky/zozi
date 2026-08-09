"""Facade exposing logistics pricing helpers to non-logistics domains.

Cash management depends on ``build_service_area_pricing_breakdown`` for COD
settlement math. Importing it through ``data`` (an exempt, cross-cutting
layer) keeps the domain dependency graph acyclic and avoids the
``cash_management -> logistics`` bounded-context violation.
"""
from __future__ import annotations

from services.logistics.logistics_partner_pricing import (
    build_service_area_pricing_breakdown,
)

__all__ = ["build_service_area_pricing_breakdown"]
