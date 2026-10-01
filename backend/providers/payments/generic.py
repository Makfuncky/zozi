from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)

__all__ = [
    "parse_generic_payload",
    "fill_gateway_template",
    "normalize_generic_status",
]


def parse_generic_payload(raw_body: bytes, query_params: dict | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if raw_body:
        try:
            payload = json.loads(raw_body)
            if not isinstance(payload, dict):
                payload = {}
        except (json.JSONDecodeError, ValueError, TypeError):
            try:
                parsed = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
                payload = {k: v[-1] for k, v in parsed.items() if v}
            except (UnicodeDecodeError, ValueError, TypeError):
                payload = {}
    if query_params:
        for key, value in query_params.items():
            if key not in payload:
                payload[key] = value
    return payload


def fill_gateway_template(template: str, ctx: dict[str, Any]) -> str:
    def repl(match: "re.Match[str]") -> str:
        key = match.group(1)
        value = ctx.get(key, "")
        return str(value if value is not None else "")

    return re.sub(r"\{([a-zA-Z0-9_]+)\}", repl, template)


def normalize_generic_status(
    raw_status: str,
    success_values: list[str] | None = None,
    failure_values: list[str] | None = None,
) -> str:
    status = str(raw_status or "").strip().lower()
    if not status:
        return "unknown"
    if success_values and status in [s.lower() for s in success_values]:
        return "success"
    if failure_values and status in [f.lower() for f in failure_values]:
        return "failed"
    return status
