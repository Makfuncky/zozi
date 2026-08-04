import logging
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from models import CountryConfig, PayoutRule, PayoutRuleCategory, PayoutRuleProduct, CountryCommissionRate

logger = logging.getLogger(__name__)


class PayoutEngine:
    def __init__(self, db: Session):
        self.db = db

    def get_payout_rate(
        self,
        country_code: str,
        supplier_id: int,
        product_id: Optional[int] = None,
        category_slug: Optional[str] = None,
    ) -> Decimal:
        country = self._get_country(country_code)
        if not country:
            logger.warning("Country %s not found", country_code)
            return Decimal("0")

        if product_id is not None:
            rate = self._get_product_payout_rate(country_code, product_id)
            if rate is not None:
                return rate

        if category_slug is not None:
            rate = self._get_category_payout_rate(country_code, category_slug)
            if rate is not None:
                return rate

        return self._get_default_payout_rate(country_code)

    def _get_country(self, country_code: str) -> Optional[CountryConfig]:
        return self.db.query(CountryConfig).filter(
            CountryConfig.code == country_code.upper(),
            CountryConfig.is_active == True,
        ).first()

    def _get_product_payout_rate(self, country_code: str, product_id: int) -> Optional[Decimal]:
        rule = (
            self.db.query(PayoutRuleProduct)
            .filter(
                PayoutRuleProduct.country_code == country_code.upper(),
                PayoutRuleProduct.product_id == product_id,
                PayoutRuleProduct.is_active == True,
            )
            .first()
        )
        if rule:
            return Decimal(str(rule.payout_rate))
        return None

    def _get_category_payout_rate(self, country_code: str, category_slug: str) -> Optional[Decimal]:
        rule = (
            self.db.query(PayoutRuleCategory)
            .filter(
                PayoutRuleCategory.country_code == country_code.upper(),
                PayoutRuleCategory.category_slug == category_slug.lower(),
                PayoutRuleCategory.is_active == True,
            )
            .first()
        )
        if rule:
            return Decimal(str(rule.payout_rate))
        return None

    def _get_default_payout_rate(self, country_code: str) -> Decimal:
        country = self._get_country(country_code)
        if country and country.payout_settings_json:
            import json
            try:
                settings = json.loads(country.payout_settings_json)
                if settings and "default_payout_rate" in settings:
                    return Decimal(str(settings["default_payout_rate"]))
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        return Decimal("0.10")

    def get_minimum_payout(self, country_code: str) -> Decimal:
        country = self._get_country(country_code)
        if country and country.minimum_payout_amount:
            return Decimal(str(country.minimum_payout_amount))
        return Decimal("10.00")

    def get_payout_currency(self, country_code: str) -> str:
        country = self._get_country(country_code)
        if country and country.payout_currency:
            return country.payout_currency
        if country:
            return country.currency
        return "USD"

    def get_payout_schedule(self, country_code: str) -> dict:
        country = self._get_country(country_code)
        if country and country.payout_settings_json:
            import json
            try:
                settings = json.loads(country.payout_settings_json)
                return {
                    "schedule": settings.get("payout_schedule", "weekly"),
                    "day": settings.get("payout_day", "sunday"),
                    "batch_size": settings.get("batch_size", 50),
                }
            except (json.JSONDecodeError, TypeError):
                pass
        return {"schedule": "weekly", "day": "sunday", "batch_size": 50}

    def calculate_supplier_payout(
        self,
        country_code: str,
        supplier_id: int,
        order_amount: Decimal,
        product_id: Optional[int] = None,
        category_slug: Optional[str] = None,
    ) -> dict:
        rate = self.get_payout_rate(country_code, supplier_id, product_id, category_slug)
        minimum = self.get_minimum_payout(country_code)
        currency = self.get_payout_currency(country_code)

        payout_amount = (order_amount * rate).quantize(Decimal("0.01"))
        is_below_minimum = payout_amount < minimum

        return {
            "rate": float(rate),
            "payout_amount": float(payout_amount),
            "minimum_payout": float(minimum),
            "currency": currency,
            "is_below_minimum": is_below_minimum,
        }
