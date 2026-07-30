"""
API endpoints for cross-border, localization, and legal contract features.
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from controllers.auth_controller import get_current_user


router = APIRouter()


class TaxCalculationBody(BaseModel):
    amount: float
    category: Optional[str] = None


@router.get("/admin/countries/{code}/localization")
def get_localization_settings(code: str, current_user: dict = Depends(get_current_user)):
    from services.cross_border_service import LocalizationService, AddressFormatService
    
    language = current_user.get("language", "en") if current_user else "en"
    
    return {
        "numeral_system": LocalizationService.get_numeral_system(language, code),
        "calendar_system": LocalizationService.get_calendar_system(code),
        "rtl_enabled": LocalizationService.get_rtl_enabled(language, code),
        "is_rtl": LocalizationService.get_rtl_enabled(language, code),
        "address_format": AddressFormatService.get_address_format(code),
    }


@router.get("/admin/countries/{code}/geo-detect")
def detect_country_from_ip(
    code: str,
    ip_address: str = Query(..., description="Client IP address"),
):
    from services.cross_border_service import GeoDetectionService
    
    detected_code = GeoDetectionService.detect_country_from_ip(ip_address)
    
    return {
        "detected_country": detected_code,
        "currency": code.upper() if detected_code is None else detected_code,
        "language": "ar" if detected_code in ["SA", "AE", "OM"] else "en",
    }


@router.get("/admin/countries/{code}/legal-documents")
def get_legal_documents(code: str):
    from services.legal_contract_service import LegalContractService
    
    return {
        "terms_of_service": LegalContractService.generate_contract(code, "terms"),
        "privacy_policy": LegalContractService.generate_contract(code, "privacy"),
    }


@router.get("/admin/countries/{code}/data-residency")
def get_data_residency_info(code: str):
    from services.data_residency import DataResidencyService, DataResidencyTier

    tier = DataResidencyService.get_residency_tier(code)
    pii_fields = DataResidencyService.get_pii_fields()

    return {
        "residency_tier": tier.value,
        "kms_key_alias": DataResidencyService.get_kms_key_alias(code),
        "should_encrypt": DataResidencyService.should_encrypt_with_local_kms(code),
        "pii_fields": pii_fields,
        "should_redact_in_export": DataResidencyService.should_redact_in_export(code),
    }


@router.get("/session/{customer_id}")
def get_cross_border_session(customer_id: int):
    from models import Order, User
    from db.database import get_db_context

    with get_db_context() as db:
        user = db.query(User).filter(User.id == customer_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Customer not found")
        current_country = user.country_code or "AE"
        orders = (
            db.query(Order.currency, Order.shipping_country)
            .filter(Order.customer_id == customer_id)
            .filter(Order.shipping_country != None)
            .all()
        )
        buckets: dict[tuple[str, str], dict] = {}
        for currency, country in orders:
            key = (currency or "USD", country or "US")
            if key not in buckets:
                buckets[key] = {
                    "countryCode": country or "US",
                    "currency": currency or "USD",
                    "totalSpent": 0.0,
                    "orderCount": 0,
                }
            buckets[key]["orderCount"] += 1
        shopping_history = list(buckets.values())

    return {
        "sessionId": f"session-{customer_id}",
        "customerId": customer_id,
        "originalCountryCode": current_country,
        "currentCountryCode": current_country,
        "shoppingHistory": shopping_history,
    }


@router.get("/convert")
def convert_currency(
    from_currency: str = Query(..., alias="from", min_length=3, max_length=5),
    to_currency: str = Query(..., alias="to", min_length=3, max_length=5),
    amount: float = Query(..., gt=0),
):
    from utils.currency import convert_between_currencies

    converted, rate, source = convert_between_currencies(amount, from_currency, to_currency)
    return {
        "fromCurrency": from_currency.upper(),
        "toCurrency": to_currency.upper(),
        "amount": amount,
        "convertedAmount": float(converted),
        "rate": float(rate),
    }


@router.get("/tax/calculate")
def calculate_tax(
    country_code: str = Query(..., min_length=2, max_length=3),
    amount: float = Query(..., gt=0),
    category_id: int | None = Query(None),
):
    from services.cross_border_service import CurrencyTaxService

    config = CurrencyTaxService.get_country_tax_config(country_code)
    tax_amount = round(float(amount) * float(config.get("tax_rate", 0.0)), 2)
    return {
        "taxAmount": tax_amount,
        "taxRate": float(config.get("tax_rate", 0.0)),
        "taxName": config.get("tax_name", "VAT"),
    }

