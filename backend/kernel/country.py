"""Shared kernel - country primitives (spec: kernel/country.py).

CountryCode typing and helpers for the country (4th) axis.
"""
from typing import NewType

CountryCode = NewType("CountryCode", str)

def normalize_country(code: str) -> CountryCode:
    return CountryCode(str(code).strip().upper())
