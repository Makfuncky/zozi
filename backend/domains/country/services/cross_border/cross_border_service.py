"""
Cross-Border Customer Detection & Localization Service.

Handles IP detection, geo-detection, currency/tax swapping, and localization.
"""
from typing import Optional, Dict, Any
import logging
import json

from infrastructure.database.database import get_db_context
from domains.country.models.countries import CountryConfig
from providers.geography.ip import detect_country_from_ip

logger = logging.getLogger(__name__)


class GeoDetectionService:
    """Detects customer location from IP and determines locale preferences."""
    
    @staticmethod
    def detect_country_from_ip(ip_address: str) -> Optional[str]:
        """Detect country code from IP address using IP geolocation providers."""
        return detect_country_from_ip(ip_address)


class LocalizationService:
    """Handles deep localization including numerals, calendars, and RTL."""
    
    @staticmethod
    def get_numeral_system(language: str, country: str) -> str:
        """Determine numeral system (Western/Arabic)."""
        arabic_countries = ["SA", "AE", "OM", "BH", "KW", "QA", "JO", "LB", "EG", "IQ", "PS", "SY", "YE"]
        if country.upper() in arabic_countries or language.lower() == "ar":
            return "eastern"
        return "western"
    
    @staticmethod
    def get_calendar_system(country: str) -> str:
        """Determine calendar system (Gregorian/Hijri)."""
        gcc_countries = ["SA", "AE", "OM", "BH", "KW", "QA"]
        if country.upper() in gcc_countries:
            return "hijri_gregorian"
        return "gregorian"
    
    @staticmethod
    def get_rtl_enabled(language: str, country: str) -> bool:
        """Check if RTL layout should be enabled."""
        arabic_countries = ["SA", "AE", "OM", "BH", "KW", "QA", "JO", "LB", "EG", "IQ", "PS", "SY", "YE"]
        return language.lower() == "ar" or country.upper() in arabic_countries
    
    @staticmethod
    def format_arabic_numerals(number: int) -> str:
        """Convert Western numerals to Eastern Arabic numerals."""
        eastern_numerals = "٠١٢٣٤٥٦٧٨٩"
        return "".join(eastern_numerals[int(d)] if d.isdigit() else d for d in str(number))


class AddressFormatService:
    """Dynamic address form builder based on region."""
    
    @staticmethod
    def get_address_format(country_code: str) -> Dict[str, Any]:
        """Get address format for a country from CountryConfig or defaults."""
        with get_db_context() as db:
            config = db.query(CountryConfig).filter(CountryConfig.code == country_code.upper()).first()
            if config and config.address_format_json:
                try:
                    return json.loads(config.address_format_json)
                except (json.JSONDecodeError, TypeError):
                    pass
        
        return AddressFormatService._get_default_format(country_code)
    
    @staticmethod
    def _get_default_format(country_code: str) -> Dict[str, Any]:
        """Fallback default address formats."""
        arabic_countries = ["SA", "AE", "OM", "BH", "KW", "QA", "JO", "LB", "EG", "IQ", "PS", "SY", "YE"]
        eu_countries = ["GB", "DE", "FR", "IT", "ES", "NL", "AT", "BE", "CH"]
        us_ca = ["US", "CA"]
        
        if country_code.upper() in arabic_countries:
            return {
                "fields": ["street", "building", "floor", "apartment", "city", "governorate", "postal_code"],
                "required": ["street", "city", "governorate"],
                "rtl": True
            }
        elif country_code.upper() in eu_countries:
            return {
                "fields": ["street", "house_number", "city", "postal_code", "country"],
                "required": ["street", "house_number", "city", "postal_code"],
            }
        elif country_code.upper() in us_ca:
            return {
                "fields": ["street", "city", "state", "zip_code"],
                "required": ["street", "city", "zip_code"],
            }
        
        return {
            "fields": ["street", "city", "postal_code", "country"],
            "required": ["street", "city", "postal_code"],
        }


class CurrencyTaxService:
    """Handles dynamic currency and tax swapping for cross-border operations."""
    
    @staticmethod
    def get_country_tax_config(country_code: str) -> Dict[str, Any]:
        """Get tax configuration for a country."""
        with get_db_context() as db:
            config = db.query(CountryConfig).filter(CountryConfig.code == country_code.upper()).first()
            if config:
                return {
                    "tax_type": config.tax_type or "VAT",
                    "tax_rate": float(config.tax_rate) if config.tax_rate else 0.0,
                    "tax_name": config.tax_name or "VAT",
                    "tax_inclusive": config.tax_inclusive or False,
                    "tax_exempt_categories": json.loads(config.tax_exempt_categories_json) if config.tax_exempt_categories_json else [],
                    "tax_reduced_rates": json.loads(config.tax_reduced_rates_json) if config.tax_reduced_rates_json else {},
                }
        return {"tax_type": "VAT", "tax_rate": 0.0, "tax_name": "VAT", "tax_inclusive": False, "tax_exempt_categories": [], "tax_reduced_rates": {}}
    
    @staticmethod
    def get_country_currency(country_code: str) -> Dict[str, Any]:
        """Get currency configuration for a country."""
        with get_db_context() as db:
            config = db.query(CountryConfig).filter(CountryConfig.code == country_code.upper()).first()
            if config:
                return {
                    "currency": config.currency or "USD",
                    "currency_symbol": config.currency_symbol or "$",
                    "exchange_rate_to_usd": float(config.exchange_rate_to_usd) if config.exchange_rate_to_usd else 1.0,
                }
        return {"currency": "USD", "currency_symbol": "$", "exchange_rate_to_usd": 1.0}


class CrossBorderTracker:
    """Tracks customers shopping in different countries."""
    
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
    
    def track_country_change(self, session_id: str, ip_address: str, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Track when a customer switches countries."""
        country_code = GeoDetectionService.detect_country_from_ip(ip_address)
        if not country_code:
            return None
        
        previous = self._sessions.get(session_id)
        change_info = {
            "session_id": session_id,
            "previous_country": previous.get("country_code") if previous else None,
            "new_country": country_code,
            "ip_address": ip_address,
            "user_id": user_id,
            "timestamp": __import__("datetime").datetime.now(timezone.utc).isoformat(),
            "is_new_session": previous is None,
        }
        
        self._sessions[session_id] = {
            "country_code": country_code,
            "ip_address": ip_address,
            "user_id": user_id,
            "first_seen": previous.get("first_seen", change_info["timestamp"]) if previous else change_info["timestamp"],
            "last_seen": change_info["timestamp"],
        }
        
        return change_info
    
    def get_session_country(self, session_id: str) -> Optional[str]:
        """Get the current country for a session."""
        session = self._sessions.get(session_id)
        return session.get("country_code") if session else None
    
    def clear_session(self, session_id: str):
        """Clear a session."""
        self._sessions.pop(session_id, None)
