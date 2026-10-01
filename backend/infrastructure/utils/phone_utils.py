"""Phone number utilities for GCC markets."""
from __future__ import annotations

from typing import Optional

import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberType, region_code_for_number


def normalize_phone_number(phone: Optional[str], country_code: Optional[str] = None) -> Optional[str]:
    if not phone:
        return None
    try:
        parsed = phonenumbers.parse(phone, country_code)
        if not phonenumbers.is_valid_number(parsed):
            return None
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except NumberParseException:
        return None


def validate_phone_number(phone: Optional[str], country_code: Optional[str] = None) -> dict:
    result: dict = {"valid": False, "country": "unknown", "error": None}
    if not phone:
        result["error"] = "empty_phone"
        return result
    try:
        parsed = phonenumbers.parse(phone, country_code)
        if not phonenumbers.is_valid_number(parsed):
            result["error"] = "invalid_number"
            return result
        result["valid"] = True
        result["country"] = region_code_for_number(parsed) or country_code or "unknown"
        return result
    except NumberParseException as exc:
        result["error"] = str(exc)
        return result


def format_phone_display(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    try:
        parsed = phonenumbers.parse(phone, None)
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    except NumberParseException:
        return phone


def is_mobile_number(phone: Optional[str], country_code: Optional[str] = None) -> bool:
    if not phone:
        return False
    try:
        parsed = phonenumbers.parse(phone, country_code)
        return phonenumbers.number_type(parsed) == PhoneNumberType.MOBILE
    except NumberParseException:
        return False
