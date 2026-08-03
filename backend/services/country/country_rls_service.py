"""
Country RLS Service
Provides per-country pricing, logistics, and supplier rule calculations
"""
from typing import Dict, Any, Optional
from decimal import Decimal
from functools import lru_cache

from data.db import get_db
from data.models import CountryConfig


class CountryRLSService:
    """Revenue, Logistics, and Supplier service per country."""

    @staticmethod
    def get_country_config(country_code: str) -> Optional[Dict[str, Any]]:
        with get_db() as db:
            config = db.query(CountryConfig).filter(
                CountryConfig.code == country_code.upper()
            ).first()
            if not config:
                return None
            return {
                "code": config.code,
                "name": config.name,
                "currency": config.currency,
                "tax_rate": float(config.tax_rate) if config.tax_rate else 0,
                "logistics_model": config.logistics_model,
                "base_rate": float(config.base_rate) if config.base_rate else 0,
                "per_km_rate": float(config.per_km_rate) if config.per_km_rate else 0,
                "minimum_charge": float(config.minimum_charge) if config.minimum_charge else 0,
                "default_vehicle_type": config.default_vehicle_type,
                "tax_name": config.tax_name,
                "tax_inclusive": config.tax_inclusive,
                "commission_tiers_json": config.commission_tiers_json,
                "supplier_requirements_json": config.supplier_requirements_json,
                "payout_settings_json": config.payout_settings_json,
            }

    @staticmethod
    def calculate_tax(country_code: str, amount: Decimal, category: str = None) -> Dict[str, Any]:
        config = CountryRLSService.get_country_config(country_code)
        if not config:
            return {"tax_amount": Decimal("0"), "tax_rate": Decimal("0")}
        
        tax_rate = Decimal(str(config["tax_rate"])) if config["tax_rate"] else Decimal("0")
        tax_amount = amount * tax_rate
        
        return {
            "tax_amount": tax_amount,
            "tax_rate": tax_rate,
            "tax_name": config.get("tax_name", "Tax") or "Tax",
            "tax_inclusive": config.get("tax_inclusive") or False,
        }

    @staticmethod
    def calculate_commission(country_code: str, order_amount: Decimal) -> Dict[str, Any]:
        config = CountryRLSService.get_country_config(country_code)
        if not config:
            return {"commission_amount": Decimal("0"), "commission_rate": Decimal("0")}
        
        commission_tiers = config.get("commission_tiers_json") or []
        commission_rate = Decimal("0")
        
        for tier in commission_tiers:
            min_val = Decimal(str(tier.get("min_order_value", 0)))
            max_val = Decimal(str(tier.get("max_order_value", 0) or "999999999"))
            rate = Decimal(str(tier.get("commission_percentage", 0)))
            
            if min_val <= order_amount <= max_val:
                commission_rate = rate
                break
        
        commission_amount = order_amount * commission_rate
        return {
            "commission_amount": commission_amount,
            "commission_rate": commission_rate,
        }

    @staticmethod
    def get_supplier_requirements(country_code: str) -> Dict[str, Any]:
        config = CountryRLSService.get_country_config(country_code)
        if not config or not config.get("supplier_requirements_json"):
            return {"kyc_level": "standard", "required_documents": [], "approval_required": False}
        return config["supplier_requirements_json"]

    @staticmethod
    def get_payout_settings(country_code: str) -> Dict[str, Any]:
        config = CountryRLSService.get_country_config(country_code)
        if not config or not config.get("payout_settings_json"):
            return {"minimum_payout_amount": Decimal("0"), "payout_schedule": "weekly"}
        return config["payout_settings_json"]

    @staticmethod
    def get_logistics_settings(country_code: str) -> Dict[str, Any]:
        config = CountryRLSService.get_country_config(country_code)
        if not config:
            return {"model": "fixed", "base_rate": Decimal("0")}
        
        return {
            "model": config.get("logistics_model") or "fixed",
            "base_rate": Decimal(str(config.get("base_rate", 0) or 0)),
            "per_km_rate": Decimal(str(config.get("per_km_rate", 0) or 0)),
            "minimum_charge": Decimal(str(config.get("minimum_charge", 0) or 0)),
            "vehicle_type": config.get("default_vehicle_type"),
        }


@lru_cache(maxsize=100)
def get_country_config_cached(country_code: str) -> Optional[Dict[str, Any]]:
    return CountryRLSService.get_country_config(country_code)
