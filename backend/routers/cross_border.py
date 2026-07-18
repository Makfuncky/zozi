"""
API endpoints for cross-border, localization, and legal contract features.
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Query
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

