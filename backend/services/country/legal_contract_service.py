"""Legal Contract Generation Service.

Generates country-specific legal documents:
- Terms of Service
- Privacy Policy
- Return/Refund Policy
- Supplier Agreement
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from data.models import CountryConfig
from services.localization_service import is_rtl_language

logger = logging.getLogger(__name__)


class LegalContractService:
    """Service for generating legal contracts."""
    
    @staticmethod
    def generate_contract(country_code: str, template_type: str, db: Session = None) -> dict[str, Any]:
        """Generate a legal contract for a country."""
        if template_type == "terms":
            return generate_terms_of_service(country_code, "en")
        elif template_type == "privacy":
            return generate_privacy_policy(country_code, "en")
        elif template_type == "refund":
            return generate_supplier_agreement(country_code, "en")
        else:
            return generate_terms_of_service(country_code, "en")

logger = logging.getLogger(__name__)


LEGAL_TEMPLATE_GCC = {
    "terms": {
        "minimum_order_age": 18,
        "max_returns_allowed": 3,
        "return_window_days": 14,
        "refund_processing_days": 7,
        "requires_commercial_license": True,
        "requires_vat_registration": True,
        "product_restrictions": ["alcohol", "pork", "gambling"],
    },
    "privacy": {
        "data_residency": "strict",
        "cookie_consent_required": True,
        "data_retention_years": 3,
        "user_rights": ["access", "rectification", "deletion", "portability"],
    },
}

LEGAL_TEMPLATE_DEFAULT = {
    "terms": {
        "minimum_order_age": 18,
        "max_returns_allowed": 3,
        "return_window_days": 14,
        "refund_processing_days": 7,
        "requires_commercial_license": False,
        "requires_vat_registration": False,
        "product_restrictions": [],
    },
    "privacy": {
        "data_residency": "standard",
        "cookie_consent_required": True,
        "data_retention_years": 2,
        "user_rights": ["access", "rectification"],
    },
}


def get_legal_template(country_code: str) -> dict:
    """Get legal template for a country."""
    gcc_countries = {"SA", "AE", "OM", "BH", "KW", "QA", "PK"}
    if country_code.upper() in gcc_countries:
        return LEGAL_TEMPLATE_GCC
    return LEGAL_TEMPLATE_DEFAULT


def generate_terms_of_service(country_code: str, language_code: str = "en") -> dict[str, Any]:
    """Generate Terms of Service document."""
    template = get_legal_template(country_code)
    terms = template.get("terms", {})
    
    return {
        "document_type": "terms_of_service",
        "country_code": country_code,
        "language": language_code,
        "generated_at": datetime.utcnow().isoformat(),
        "content": {
            "title": "Terms of Service" if language_code != "ar" else "شروط الخدمة",
            "minimum_order_age": terms.get("minimum_order_age", 18),
            "return_policy": {
                "max_returns": terms.get("max_returns_allowed", 3),
                "window_days": terms.get("return_window_days", 14),
                "processing_days": terms.get("refund_processing_days", 7),
            },
            "commercial_registration_required": terms.get("requires_commercial_license", False),
            "vat_registration_required": terms.get("requires_vat_registration", False),
            "restricted_products": terms.get("product_restrictions", []),
        },
    }


def generate_privacy_policy(country_code: str, language_code: str = "en") -> dict[str, Any]:
    """Generate Privacy Policy document."""
    template = get_legal_template(country_code)
    privacy = template.get("privacy", {})
    
    return {
        "document_type": "privacy_policy",
        "country_code": country_code,
        "language": language_code,
        "generated_at": datetime.utcnow().isoformat(),
        "content": {
            "title": "Privacy Policy" if language_code != "ar" else "سياسة الخصوصية",
            "data_residency_tier": privacy.get("data_residency", "standard"),
            "cookie_consent_required": privacy.get("cookie_consent_required", True),
            "data_retention_years": privacy.get("data_retention_years", 2),
            "user_rights": privacy.get("user_rights", ["access", "rectification"]),
        },
    }


def generate_supplier_agreement(country_code: str, language_code: str = "en") -> dict[str, Any]:
    """Generate Supplier Agreement document."""
    template = get_legal_template(country_code)
    terms = template.get("terms", {})
    
    return {
        "document_type": "supplier_agreement",
        "country_code": country_code,
        "language": language_code,
        "generated_at": datetime.utcnow().isoformat(),
        "content": {
            "title": "Supplier Agreement" if language_code != "ar" else "اتفاقية المورد",
            "commercial_registration_required": terms.get("requires_commercial_license", False),
            "kyc_requirements": {
                "documents_required": ["commercial_register", "tax_certificate", "bank_statement"],
                "verification_days": 7,
            },
        },
    }


def generate_all_legal_documents(country_code: str, language_code: str = "en") -> dict[str, dict]:
    """Generate all legal documents for a country."""
    return {
        "terms_of_service": generate_terms_of_service(country_code, language_code),
        "privacy_policy": generate_privacy_policy(country_code, language_code),
        "supplier_agreement": generate_supplier_agreement(country_code, language_code),
    }


def get_legal_rules_for_checkout(db: Session, country_code: str) -> dict[str, Any]:
    """Get legal rules applicable at checkout."""
    config = db.query(CountryConfig).filter(
        CountryConfig.code == country_code.upper(),
        CountryConfig.is_active == True,
    ).first()
    
    if not config or not config.legal_rules_json:
        template = get_legal_template(country_code)
        return template.get("terms", {})
    
    try:
        rules = json.loads(config.legal_rules_json) if isinstance(config.legal_rules_json, str) else config.legal_rules_json
        return rules or {}
    except (json.JSONDecodeError, TypeError):
        return {}
