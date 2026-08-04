"""Localization Service for Dynamic Country Integration.

Supports:
- RTL (Right-to-Left) languages (Arabic, Hebrew)
- Eastern Arabic numerals (Arabic-Indic digits)
- Hijri calendar conversion
- Deep localization for Middle East markets
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

RTL_LANGUAGES = {"ar", "he", "fa", "ur", "ps", "sd", "ug", "prs"}

EASTERN_ARABIC_NUMERALS = {
    "0": "٠", "1": "١", "2": "٢", "3": "٣", "4": "٤",
    "5": "٥", "6": "٦", "7": "٧", "8": "٨", "9": "٩",
}

GREGORIAN_MONTHS_EN = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

GREGORIAN_MONTHS_AR = [
    "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
    "يوليوز", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
]

HIJRI_MONTHS_AR = [
    "محرم", "صفر", "ربيع الأول", "ربيع الثاني", "جمادى الأولى", "جمادى الثانية",
    "رجب", "شعبان", "Ramadan", "Shawwal", "ذي القعدة", "ذي الحجة"
]


def is_rtl_language(language_code: str) -> bool:
    """Check if the language is RTL."""
    return language_code.lower() in RTL_LANGUAGES


def to_eastern_arabic_numerals(number: str | int | float, language_code: str) -> str:
    """Convert number to Eastern Arabic numerals for RTL languages."""
    if not is_rtl_language(language_code):
        return str(number)
    return "".join(EASTERN_ARABIC_NUMERALS.get(d, d) for d in str(number))


def format_date_rtl(date: datetime, language_code: str, format_type: str = "short") -> str:
    """Format date for RTL languages."""
    if not is_rtl_language(language_code):
        return date.strftime("%Y-%m-%d")
    
    if language_code == "ar":
        hijri_year, hijri_month, hijri_day = gregorian_to_hijri(date.year, date.month, date.day)
        month_name = HIJRI_MONTHS_AR[hijri_month - 1] if hijri_month <= len(HIJRI_MONTHS_AR) else str(hijri_month)
        if format_type == "full":
            return f"{hijri_day} {month_name} {hijri_year} ه"
        return f"{hijri_year}-{hijri_month:02d}-{hijri_day:02d}"
    
    return date.strftime("%Y-%m-%d")


def gregorian_to_hijri(year: int, month: int, day: int) -> tuple[int, int, int]:
    """Convert Gregorian date to Hijri date (approximate)."""
    hijri_epoch = 227014
    abs_month_day = (year - 1) * 354 + (month - 1) * 29.5 + day - 1
    hijri_day = int(abs_month_day % 30) + 1
    hijri_month = int((abs_month_day / 30) % 12) + 1
    hijri_year = int(abs_month_day / 354) + 1
    
    if hijri_year < 1:
        hijri_year = 1
    if hijri_month < 1:
        hijri_month = 1
    if hijri_day < 1:
        hijri_day = 1
    
    return hijri_year, hijri_month, hijri_day


def hijri_to_gregorian(hijri_year: int, hijri_month: int, hijri_day: int) -> tuple[int, int, int]:
    """Convert Hijri date to Gregorian date (approximate)."""
    abs_month_day = (hijri_year - 1) * 354 + (hijri_month - 1) * 29.5 + hijri_day - 1
    gregorian_year = int(abs_month_day / 354) + 1
    gregorian_month = int((abs_month_day / 29.5) % 12) + 1
    gregorian_day = int(abs_month_day % 30) + 1
    
    return gregorian_year, gregorian_month, gregorian_day


def get_number_format(language_code: str) -> dict:
    """Get number formatting rules for a language."""
    base = {
        "decimal_separator": ".",
        "thousands_separator": ",",
        "currency_symbol_position": "before",
        "currency_symbol": "$",
    }
    
    if language_code == "ar":
        return {
            **base,
            "decimal_separator": "٫",
            "thousands_separator": "٬",
            "currency_symbol": "ر.س",
        }
    
    if language_code == "fa":
        return {
            **base,
            "decimal_separator": "٫",
            "thousands_separator": "٬",
        }
    
    return base


def get_currency_symbol(currency_code: str, language_code: str) -> str:
    """Get localized currency symbol."""
    symbols = {
        "USD": {"default": "$", "ar": "د.س"},
        "EUR": {"default": "€", "ar": "€"},
        "GBP": {"default": "£", "ar": "£"},
        "SAR": {"default": "SR", "ar": "ر.س"},
        "AED": {"default": "DH", "ar": "د.إ"},
        "OMR": {"default": "R. Omani", "ar": "ر.ع"},
        "KWD": {"default": "KD", "ar": "د.ك"},
        "BHD": {"default": "BD", "ar": "د.ب"},
    }
    
    return symbols.get(currency_code, {}).get(language_code, currency_code)
