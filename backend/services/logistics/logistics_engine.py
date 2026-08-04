import json
import logging
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from data.models import CountryConfig, LogisticsPartner, LogisticsPricingProfile
from data.services_logistics_partner_pricing import normalize_country_code

logger = logging.getLogger(__name__)


class LogisticsEngine:
    """Country-aware logistics provider orchestration.

    Reads provider config from ``CountryConfig.logistics_providers_json``
    and maps to ``LogisticsPartner`` models for shipment fulfilment.
    """

    def __init__(self, db: Session):
        self.db = db

    # ── Public API ─────────────────────────────────────────────────────────

    def get_enabled_providers(self, country_code: str) -> list[dict[str, Any]]:
        """Return enabled logistics providers configured for a country."""
        country = self._get_country(country_code)
        if not country:
            return []
        raw_providers = self._parse_providers(country)
        return [p for p in raw_providers if p.get("enabled", False)]

    def get_provider_rates(self, country_code: str) -> list[dict[str, Any]]:
        """Return all providers with their pricing for a country."""
        providers = self.get_enabled_providers(country_code)
        for prov in providers:
            partner = self._find_partner(prov["provider_id"])
            prov["partner_registered"] = partner is not None
            if partner:
                prov["partner_id"] = partner.id
                prov["verification_status"] = partner.verification_status
        return providers

    def calculate_shipping_cost(
        self,
        country_code: str,
        provider_id: str,
        *,
        weight_kg: float = 0.0,
        distance_km: float = 0.0,
        is_express: bool = False,
    ) -> dict[str, Any]:
        """Calculate shipping cost for a given provider and country."""
        country = self._get_country(country_code)
        if not country:
            return {"error": "Country not found", "cost": None}

        providers = self._parse_providers(country)
        provider_config = None
        for p in providers:
            if str(p.get("provider_id", "")).lower() == provider_id.lower():
                provider_config = p
                break

        if not provider_config:
            return {"error": f"Provider '{provider_id}' not configured for {country_code}", "cost": None}
        if not provider_config.get("enabled", False):
            return {"error": f"Provider '{provider_id}' is disabled for {country_code}", "cost": None}

        base_rate = Decimal(str(provider_config.get("base_rate", 0)))
        per_kg_rate = Decimal(str(provider_config.get("per_kg_rate", 0)))
        currency = provider_config.get("currency") or country.currency

        total = base_rate + (per_kg_rate * Decimal(str(weight_kg)))
        if distance_km > 0:
            total += base_rate * Decimal(str(distance_km)) / Decimal("10")

        sla_key = "sla_express_days" if is_express else "sla_standard_days"
        sla = provider_config.get(sla_key, "3-5")

        partner = self._find_partner(provider_id)

        return {
            "provider_id": provider_id,
            "provider_name": provider_config.get("name", provider_id),
            "country_code": country_code,
            "currency": currency,
            "base_rate": float(base_rate),
            "per_kg_rate": float(per_kg_rate),
            "weight_kg": weight_kg,
            "distance_km": distance_km,
            "total_cost": float(total),
            "sla_days": sla,
            "is_express": is_express,
            "partner_registered": partner is not None,
            "partner_id": partner.id if partner else None,
            "partner_verified": partner.verification_status == "approved" if partner else False,
        }

    def register_provider(
        self,
        country_code: str,
        provider_config: dict[str, Any],
        *,
        actor_id: int | None = None,
    ) -> dict[str, Any]:
        """Upsert a logistics provider into a country's config.

        ``provider_config`` must include at minimum ``provider_id`` and ``name``.
        """
        country = self._get_country(country_code)
        if not country:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Country not found")

        provider_id = str(provider_config.get("provider_id") or "").strip().lower()
        if not provider_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail="provider_id is required")

        raw = country.logistics_providers_json
        try:
            providers = json.loads(raw) if isinstance(raw, str) else (raw or [])
        except (json.JSONDecodeError, TypeError):
            providers = []
        if not isinstance(providers, list):
            providers = []

        existing = None
        for p in providers:
            if isinstance(p, dict) and str(p.get("provider_id", "")).lower() == provider_id:
                existing = p
                break

        normalized = {
            "provider_id": provider_id,
            "name": str(provider_config.get("name") or provider_id).strip(),
            "enabled": bool(provider_config.get("enabled", True)),
            "service_areas": provider_config.get("service_areas") if isinstance(provider_config.get("service_areas"), list) else ["all_regions"],
            "sla_standard_days": str(provider_config.get("sla_standard_days") or "3-5").strip(),
            "sla_express_days": str(provider_config.get("sla_express_days") or "1-2").strip(),
            "base_rate": float(provider_config.get("base_rate") or 0),
            "per_kg_rate": float(provider_config.get("per_kg_rate") or 0),
            "currency": str(provider_config.get("currency") or "").strip().upper() or None,
        }

        if existing:
            existing.update(normalized)
        else:
            providers.append(normalized)

        country.logistics_providers_json = json.dumps(providers, default=str)
        self.db.commit()
        self.db.refresh(country)

        return {
            "message": "Provider '" + str(provider_id) + "' " + ("updated" if existing else "created") + " for " + str(country_code),
            "provider": normalized,
        }

    # ── Internal helpers ───────────────────────────────────────────────────

    def _get_country(self, country_code: str) -> CountryConfig | None:
        return self.db.query(CountryConfig).filter(
            CountryConfig.code == normalize_country_code(country_code),
            CountryConfig.is_active == True,
        ).first()

    def _parse_providers(self, country: CountryConfig) -> list[dict[str, Any]]:
        raw = country.logistics_providers_json
        if not raw:
            return []
        try:
            providers = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            return []
        return providers if isinstance(providers, list) else []

    def _find_partner(self, provider_id: str) -> LogisticsPartner | None:
        return self.db.query(LogisticsPartner).filter(
            LogisticsPartner.code == provider_id.lower(),
        ).first()

