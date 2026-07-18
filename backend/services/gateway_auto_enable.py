"""Gateway auto-enable service for country-specific payment routing.

Automatically enables payment gateways based on country configuration
from the auto-populate service.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from models import CountryConfig, CountryGatewayCredentials
from services.gateways.registry import PaymentGatewayRegistry
from services.country_auto_populate import GATEWAY_REGISTRY

logger = logging.getLogger(__name__)


class GatewayAutoEnableService:
    """Service for automatically enabling gateways based on country config."""

    def __init__(self, db: Session):
        self.db = db

    def get_eligible_gateways(self, country_code: str) -> List[Dict[str, Any]]:
        """Get gateways eligible for a country based on config."""
        country = (
            self.db.query(CountryConfig)
            .filter(CountryConfig.code == country_code.upper())
            .first()
        )

        if not country:
            return []

        currencies = []
        if country.currencies:
            currencies = country.currencies if isinstance(country.currencies, list) else []
        elif country.currency:
            currencies = [country.currency]

        region = country.region or ""
        internet_pen = float(country.internet_penetration_pct) if country.internet_penetration_pct else 50

        gateway_rankings = self.calculate_gateway_rankings(
            country_code, currencies, region, internet_pen
        )

        return [
            {
                "gateway_id": gw["gateway_id"],
                "name": gw["name"],
                "type": gw["type"],
                "enabled": True,
                "credential_ref": None,
                "supports_cod": gw["gateway_id"] in ["tap", "thawani", "omannet"],
                "supports_installments": gw["gateway_id"] in ["stripe", "tap", "hyperpay"],
                "fee_percentage": gw["avg_fee"],
                "fee_fixed": 0.30,
                "integration_feasibility_score": gw["score"],
                "recommendation": "highly_recommended" if gw["score"] >= 75 else "recommended" if gw["score"] >= 50 else "consider",
            }
            for gw in gateway_rankings
        ]

    def calculate_gateway_rankings(
        self,
        country_code: str,
        currencies: List[str],
        region: str = None,
        internet_pen: float = 50,
    ) -> List[Dict[str, Any]]:
        """Calculate gateway rankings for a country."""
        scores = []
        for gw_id, gw in GATEWAY_REGISTRY.items():
            score = 0
            if country_code.upper() in gw["regions"] or "GLOBAL" in gw["regions"]:
                score += 40
            for curr in currencies:
                if curr in gw["currencies"] or "*" in gw["currencies"]:
                    score += 25
                    break
            if internet_pen > 80:
                score += 15
            elif internet_pen > 50:
                score += 10
            else:
                score += 5
            score += max(0, 10 - (gw["avg_fee"] - 1.5))
            score += max(0, 10 - (gw["setup_days"] / 3))
            if score > 50:
                scores.append({
                    "gateway_id": gw_id,
                    "score": score,
                    "name": gw["name"],
                    "type": gw["type"],
                    "avg_fee": gw["avg_fee"],
                    "setup_days": gw["setup_days"],
                })
        return sorted(scores, key=lambda x: x["score"], reverse=True)

    def enable_gateways_for_country(
        self, country_code: str, user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Enable eligible gateways for a country."""
        gateways = self.get_eligible_gateways(country_code)

        for gw in gateways:
            existing = (
                self.db.query(CountryGatewayCredentials)
                .filter(
                    CountryGatewayCredentials.country_code == country_code.upper(),
                    CountryGatewayCredentials.gateway_name == gw["gateway_id"],
                )
                .first()
            )

            if not existing:
                cred = CountryGatewayCredentials(
                    country_code=country_code.upper(),
                    gateway_name=gw["gateway_id"],
                    environment="test",
                    credentials={},
                    is_active=True,
                )
                self.db.add(cred)

        self.db.commit()
        return gateways

    def get_enabled_gateways(self, country_code: str) -> List[Dict[str, Any]]:
        """Get list of enabled gateways for a country."""
        credentials = (
            self.db.query(CountryGatewayCredentials)
            .filter(
                CountryGatewayCredentials.country_code == country_code.upper(),
                CountryGatewayCredentials.is_active == True,
            )
            .all()
        )

        return [
            {
                "gateway_id": c.gateway_name,
                "gateway_name": c.gateway_name,
                "environment": c.environment,
                "is_active": c.is_active,
            }
            for c in credentials
        ]


def auto_enable_gateways(db: Session, country_code: str, user_id: Optional[int] = None) -> List[str]:
    """Convenience function to auto-enable gateways for a country."""
    service = GatewayAutoEnableService(db)
    gateways = service.enable_gateways_for_country(country_code, user_id)
    return [g["gateway_id"] for g in gateways]
