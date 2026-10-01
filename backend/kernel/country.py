"""Shared kernel - country primitives (spec: kernel/country.py).

CountryCode typing and helpers for the country (4th) axis.
"""
from typing import NewType

CountryCode = NewType("CountryCode", str)

# Gulf Cooperation Council member states (ISO 3166-1 alpha-2).
GCC_COUNTRIES = frozenset({"AE", "SA", "QA", "OM", "KW", "BH"})


def normalize_country(code: str) -> CountryCode:
    return CountryCode(str(code).strip().upper())
