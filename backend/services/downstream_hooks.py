"""
Downstream Integration Hooks
Connects Country Config to Payment, Supplier, and Logistics systems
"""
from typing import List, Dict, Any
from functools import lru_cache
from db.database import get_db_context
from models import CountryConfig


def invalidate_country_cache(country_code: str):
    """Invalidate all caches for a country"""
    get_country_payment_gateways.cache_clear()
    get_country_supplier_requirements.cache_clear()
    get_country_restricted_categories.cache_clear()


@lru_cache(maxsize=100)
def get_country_payment_gateways(country_code: str) -> List[Dict[str, Any]]:
    """Get enabled payment gateways for a country"""
    with get_db_context() as db:
        config = db.query(CountryConfig).filter(CountryConfig.code == country_code.upper()).first()
        if not config or not config.payment_gateways_json:
            return []
        
        gateways = config.payment_gateways_json
        return [g for g in gateways if g.get('enabled', True)]


@lru_cache(maxsize=100)
def get_country_supplier_requirements(country_code: str) -> Dict[str, Any]:
    """Get supplier requirements for a country"""
    with get_db_context() as db:
        config = db.query(CountryConfig).filter(CountryConfig.code == country_code.upper()).first()
        if not config or not config.supplier_requirements_json:
            return {"kyc_level": "standard", "required_documents": []}
        
        return config.supplier_requirements_json


@lru_cache(maxsize=100)
def get_country_restricted_categories(country_code: str) -> List[str]:
    """Get restricted categories for a country"""
    with get_db_context() as db:
        config = db.query(CountryConfig).filter(CountryConfig.code == country_code.upper()).first()
        if not config or not config.product_restrictions_json:
            return []
        
        return config.product_restrictions_json
