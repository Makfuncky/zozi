from __future__ import annotations

"""
Country Provider
================
Country details search AI work and system.
Test file: backend/tests/_test_provider/test_country.py
"""
import logging
from typing import Any, Dict, List, Optional

from .config import settings

logger = logging.getLogger(__name__)


class CountrySearchProvider:
    """AI-powered country details search system."""

    def __init__(self):
        self._default_country = settings.geo_default_country
        self._country_cache: Dict[str, Dict] = {}

    def search_country(self, query: str) -> List[Dict[str, Any]]:
        """Search for countries matching a query string.

        Args:
            query: Search query (country name, code, region, etc.).

        Returns:
            List of matching country dicts.
        """
        query_lower = query.lower().strip()
        results = []

        known_countries = self._get_known_countries()
        for country in known_countries:
            if (
                query_lower in country.get("name", "").lower()
                or query_lower in country.get("code", "").lower()
                or query_lower in country.get("region", "").lower()
                or query_lower in country.get("capital", "").lower()
            ):
                results.append(country)

        return results[:20]

    def get_country_details(self, country_code: str) -> Dict[str, Any]:
        """Get detailed information about a country by code.

        Args:
            country_code: ISO 3166-1 alpha-2 country code.

        Returns:
            Dict with country details.
        """
        code = country_code.upper().strip()

        if code in self._country_cache:
            return self._country_cache[code]

        details = self._fetch_country_details(code)
        self._country_cache[code] = details
        return details

    def get_country_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get country details by full name."""
        results = self.search_country(name)
        if results:
            return results[0]
        return None

    def get_countries_by_region(self, region: str) -> List[Dict[str, Any]]:
        """Get all countries in a region."""
        region_lower = region.lower().strip()
        all_countries = self._get_known_countries()
        return [
            c for c in all_countries
            if c.get("region", "").lower() == region_lower
        ]

    def get_currencies(self) -> Dict[str, List[str]]:
        """Get a mapping of currencies to countries."""
        currencies: Dict[str, List[str]] = {}
        for country in self._get_known_countries():
            for currency in country.get("currencies", []):
                if currency not in currencies:
                    currencies[currency] = []
                currencies[currency].append(country.get("code", ""))
        return currencies

    def _get_known_countries(self) -> List[Dict[str, Any]]:
        return [
            {"code": "US", "name": "United States", "region": "Americas", "capital": "Washington, D.C.", "currencies": ["USD"], "phone_code": "+1", "languages": ["English"]},
            {"code": "GB", "name": "United Kingdom", "region": "Europe", "capital": "London", "currencies": ["GBP"], "phone_code": "+44", "languages": ["English"]},
            {"code": "DE", "name": "Germany", "region": "Europe", "capital": "Berlin", "currencies": ["EUR"], "phone_code": "+49", "languages": ["German"]},
            {"code": "FR", "name": "France", "region": "Europe", "capital": "Paris", "currencies": ["EUR"], "phone_code": "+33", "languages": ["French"]},
            {"code": "JP", "name": "Japan", "region": "Asia", "capital": "Tokyo", "currencies": ["JPY"], "phone_code": "+81", "languages": ["Japanese"]},
            {"code": "CN", "name": "China", "region": "Asia", "capital": "Beijing", "currencies": ["CNY"], "phone_code": "+86", "languages": ["Chinese"]},
            {"code": "IN", "name": "India", "region": "Asia", "capital": "New Delhi", "currencies": ["INR"], "phone_code": "+91", "languages": ["Hindi", "English"]},
            {"code": "BR", "name": "Brazil", "region": "Americas", "capital": "Brasilia", "currencies": ["BRL"], "phone_code": "+55", "languages": ["Portuguese"]},
            {"code": "AU", "name": "Australia", "region": "Oceania", "capital": "Canberra", "currencies": ["AUD"], "phone_code": "+61", "languages": ["English"]},
            {"code": "CA", "name": "Canada", "region": "Americas", "capital": "Ottawa", "currencies": ["CAD"], "phone_code": "+1", "languages": ["English", "French"]},
            {"code": "KR", "name": "South Korea", "region": "Asia", "capital": "Seoul", "currencies": ["KRW"], "phone_code": "+82", "languages": ["Korean"]},
            {"code": "MX", "name": "Mexico", "region": "Americas", "capital": "Mexico City", "currencies": ["MXN"], "phone_code": "+52", "languages": ["Spanish"]},
            {"code": "IT", "name": "Italy", "region": "Europe", "capital": "Rome", "currencies": ["EUR"], "phone_code": "+39", "languages": ["Italian"]},
            {"code": "ES", "name": "Spain", "region": "Europe", "capital": "Madrid", "currencies": ["EUR"], "phone_code": "+34", "languages": ["Spanish"]},
            {"code": "NL", "name": "Netherlands", "region": "Europe", "capital": "Amsterdam", "currencies": ["EUR"], "phone_code": "+31", "languages": ["Dutch"]},
            {"code": "SA", "name": "Saudi Arabia", "region": "Middle East", "capital": "Riyadh", "currencies": ["SAR"], "phone_code": "+966", "languages": ["Arabic"]},
            {"code": "AE", "name": "United Arab Emirates", "region": "Middle East", "capital": "Abu Dhabi", "currencies": ["AED"], "phone_code": "+971", "languages": ["Arabic"]},
            {"code": "EG", "name": "Egypt", "region": "Africa", "capital": "Cairo", "currencies": ["EGP"], "phone_code": "+20", "languages": ["Arabic"]},
            {"code": "NG", "name": "Nigeria", "region": "Africa", "capital": "Abuja", "currencies": ["NGN"], "phone_code": "+234", "languages": ["English"]},
            {"code": "ZA", "name": "South Africa", "region": "Africa", "capital": "Pretoria", "currencies": ["ZAR"], "phone_code": "+27", "languages": ["English", "Afrikaans"]},
        ]

    def _fetch_country_details(self, code: str) -> Dict[str, Any]:
        for country in self._get_known_countries():
            if country.get("code") == code:
                return country
        return {
            "code": code,
            "name": code,
            "region": "Unknown",
            "capital": "",
            "currencies": [],
            "phone_code": "",
            "languages": [],
        }