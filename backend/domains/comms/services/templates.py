"""Locale-aware template resolver for the comms domain.

Resolves a template_id + country_code to a localized message body.

- AE (United Arab Emirates) -> templates/<id>.ae.txt
- SA (Saudi Arabia)        -> templates/<id>.sa.txt
- Anything else / missing  -> fall back to the default English body
  shipped by ``infrastructure.utils.message_templates``.

This module does NOT import from ``domains/*`` or ``modules/*`` (Law 1)
and does NOT contain business logic — only template lookup + format.

Usage::

    from domains.comms.services.templates import render

    body = render("order_confirmed_sms", country_code="AE", order_id="X", total="100 AED")
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from infrastructure.utils.message_templates import (
    TEMPLATES,
    render_template as render_default,
)

logger = logging.getLogger(__name__)


_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


# Country codes we ship native locale variants for (Phase G).
# Anything outside this set falls back to the English default body.
SUPPORTED_LOCALES: frozenset[str] = frozenset({"AE", "SA"})


@lru_cache(maxsize=512)
def _load_locale_file(template_id: str, country_code: str) -> str | None:
    """Read a locale variant body from disk.

    Returns ``None`` when no variant file exists. The result is cached
    because template files never change during the lifetime of a
    process.
    """
    cc = country_code.upper()
    if cc not in SUPPORTED_LOCALES:
        return None
    path = _TEMPLATES_DIR / f"{template_id}.{cc.lower()}.txt"
    if not path.is_file():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("template locale read failed: %s (%s)", path, exc)
        return None

    # File format (see _locale.txt files):
    #   <template_id>
    #   <human description line>
    #   Subject: <subject line>
    #   Body: <body lines>
    # We extract only the body, which is the part the existing
    # notification pipeline substitutes variables into.
    lines = raw.splitlines()
    body_lines: list[str] = []
    in_body = False
    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("body:"):
            body_lines.append(stripped.split(":", 1)[1].strip())
            in_body = True
            continue
        if in_body:
            body_lines.append(line)
    if not body_lines:
        return None
    return "\n".join(body_lines).rstrip()


def _format(body: str, ctx: dict[str, Any]) -> str:
    """Safe ``str.format`` — missing keys become ``<missing:KEY>``."""
    class _SafeDict(dict):
        def __missing__(self, key: str) -> str:  # type: ignore[override]
            return "<missing:" + str(key) + ">"

    try:
        return body.format_map(_SafeDict(ctx))
    except (KeyError, IndexError, ValueError) as exc:
        raise ValueError(f"template format error: {exc}") from exc


def render(template_id: str, country_code: str | None = None, **ctx: Any) -> str:
    """Render a template, choosing the AE/SA variant when available.

    Args:
        template_id: Identifier from ``infrastructure.utils.message_templates``.
        country_code: ISO 3166-1 alpha-2 country code (e.g. ``"AE"``, ``"SA"``).
            ``None`` and unsupported values fall back to the default English.
        **ctx: Template variables used by ``str.format``.

    Returns:
        The rendered body string.

    Raises:
        ValueError: when ``template_id`` is unknown or formatting fails
            irrecoverably.
    """
    if template_id not in TEMPLATES:
        raise ValueError(f"Template not found: {template_id}")

    if country_code:
        localized = _load_locale_file(template_id, country_code)
        if localized:
            return _format(localized, ctx)

    # Fall back to the default English body shipped in code.
    return render_default(template_id, **ctx)


def has_locale_variant(template_id: str, country_code: str) -> bool:
    """Whether a localized variant exists for this template+country."""
    if country_code.upper() not in SUPPORTED_LOCALES:
        return False
    path = _TEMPLATES_DIR / f"{template_id}.{country_code.lower()}.txt"
    return path.is_file()


def clear_cache() -> None:
    """Reset the in-process template file cache (for tests)."""
    _load_locale_file.cache_clear()
