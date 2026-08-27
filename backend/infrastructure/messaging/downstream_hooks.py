"""
Downstream Integration Hooks
Connects Country Config to Payment, Supplier, and Logistics systems.

Law 1 compliance: all country-config lookups use raw SQL on the
``country_configs`` table. No domain models are imported — the column
names are part of the schema contract documented in
``domains/country/models/country.py``.
"""
from typing import List, Dict, Any
from functools import lru_cache
from infrastructure.database.database import get_db_context
from sqlalchemy import text


def invalidate_country_cache(country_code: str):
    """Invalidate all caches for a country"""
    get_country_payment_gateways.cache_clear()
    get_country_supplier_requirements.cache_clear()
    get_country_restricted_categories.cache_clear()


@lru_cache(maxsize=100)
def get_country_payment_gateways(country_code: str) -> List[Dict[str, Any]]:
    """Get enabled payment gateways for a country"""
    cc_upper = country_code.upper()
    with get_db_context() as db:
        row = db.execute(
            text("SELECT payment_gateways_json FROM country_configs WHERE code = :code"),
            {"code": cc_upper},
        ).first()
        if not row or not row[0]:
            return []
        import json
        try:
            gateways = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        except (json.JSONDecodeError, TypeError):
            return []
        return [g for g in (gateways or []) if g.get('enabled', True)]


@lru_cache(maxsize=100)
def get_country_supplier_requirements(country_code: str) -> Dict[str, Any]:
    """Get supplier requirements for a country"""
    cc_upper = country_code.upper()
    with get_db_context() as db:
        row = db.execute(
            text("SELECT supplier_requirements_json FROM country_configs WHERE code = :code"),
            {"code": cc_upper},
        ).first()
        if not row or not row[0]:
            return {"kyc_level": "standard", "required_documents": []}
        import json
        try:
            data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
            return data or {"kyc_level": "standard", "required_documents": []}
        except (json.JSONDecodeError, TypeError):
            return {"kyc_level": "standard", "required_documents": []}


@lru_cache(maxsize=100)
def get_country_restricted_categories(country_code: str) -> List[str]:
    """Get restricted categories for a country"""
    cc_upper = country_code.upper()
    with get_db_context() as db:
        row = db.execute(
            text("SELECT product_restrictions_json FROM country_configs WHERE code = :code"),
            {"code": cc_upper},
        ).first()
        if not row or not row[0]:
            return []
        import json
        try:
            data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
            return data or []
        except (json.JSONDecodeError, TypeError):
            return []

