"""
Pure helper functions for country code normalization.

This module provides country code utilities without any DB or service dependencies.
"""

from __future__ import annotations


_COUNTRY_CODE_ALIASES: dict[str, str] = {
    "AE": "AE",
    "UAE": "AE",
    "UNITEDARABEMIRATES": "AE",
    "EMIRATES": "AE",
    "PK": "PK",
    "PAKISTAN": "PK",
    "OM": "OM",
    "OMAN": "OM",
    "SA": "SA",
    "SAUDIARABIA": "SA",
    "KSA": "SA",
    "IN": "IN",
    "INDIA": "IN",
    "US": "US",
    "USA": "US",
    "UNITEDSTATES": "US",
    "UNITEDSTATESOFAMERICA": "US",
    "GB": "GB",
    "UK": "GB",
    "UNITEDKINGDOM": "GB",
    "KW": "KW",
    "KUWAIT": "KW",
    "QA": "QA",
    "QATAR": "QA",
    "BH": "BH",
    "BAHRAIN": "BH",
}


def normalize_country_code(value: str | None) -> str:
    """Normalize a country name or code to a 2-letter ISO code.

    This is a pure helper with no DB or service dependencies.
    """
    if not value:
        return ""

    letters = "".join(ch for ch in str(value).upper() if ch.isalpha())
    if not letters:
        return ""

    aliased = _COUNTRY_CODE_ALIASES.get(letters)
    if aliased:
        return aliased

    if len(letters) == 2:
        return letters

    return letters[:2]
