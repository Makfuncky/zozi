"""Locale resolution for GCC transactional email / SMS templates.

Phase 2.1 MASTER Item 5: the codebase had no locale-aware template
resolution. Every template was rendered in English, ignoring the
recipient's country. This module is the single source of truth for
mapping a recipient country code (OM/AE/SA/BH/KW/QA) to a template
locale string used to look up ``*.{locale}.html`` files.

The expected lookup convention is::

    comms/templates/order_created.en.html
    comms/templates/order_created.ar.html          # pan-Arabic
    comms/templates/order_created.ar-ae.html       # AE-specific dialect
    comms/templates/order_created.ar-sa.html       # SA-specific dialect

Resolver order:
1. ``<country_code>`` (e.g. ``ar-ae``, ``ar-sa``) — explicit dialect match
2. ``ar`` (pan-Arabic fallback for any Arabic country)
3. ``en`` (English fallback)

The mapping below is a Phase-2 baseline. Add more countries as the
template corpus grows.
"""
from __future__ import annotations

from typing import Final


# GCC + Yemen country -> locale suffix (None = English-only)
COUNTRY_LOCALE: Final[dict[str, str]] = {
    "AE": "ar-ae",
    "SA": "ar-sa",
    "OM": "ar",
    "BH": "ar",
    "KW": "ar",
    "QA": "ar",
    "YE": "ar",
}


def resolve_locale(country_code: str | None, fallback: str = "en") -> str:
    """Return the locale string for ``country_code``.

    Falls back to ``fallback`` (default ``en``) for unknown codes or
    when ``country_code`` is falsy.
    """
    if not country_code:
        return fallback
    return COUNTRY_LOCALE.get(country_code.upper(), fallback)


def template_candidates(
    template_name: str, country_code: str | None
) -> tuple[str, ...]:
    """Return the ordered tuple of template filenames to try.

    Example::

        >>> template_candidates("order_created", "AE")
        ('order_created.ar-ae.html', 'order_created.ar.html', 'order_created.en.html')
    """
    locale = resolve_locale(country_code)
    primary = f"{template_name}.{locale}.html"
    pan_arabic = f"{template_name}.ar.html"
    english = f"{template_name}.en.html"
    if locale == "ar":
        return (pan_arabic, english)
    if locale.startswith("ar-"):
        return (primary, pan_arabic, english)
    return (primary, english)


__all__ = [
    "COUNTRY_LOCALE",
    "resolve_locale",
    "template_candidates",
]