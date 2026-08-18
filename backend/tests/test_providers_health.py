"""Provider-layer health gates (P3 / P4).

Validates that ``providers/`` is import-clean (no BOM / syntax defects such as the
one remediated in ``infrastructure.routing.route_contract``) and that the WhatsApp message provider is
correctly wired through ``services.comms.whatsapp_service`` and degrades safely when
its optional SDK (``twilio``) is absent.
"""
from __future__ import annotations

import ast
import glob
import os
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

ROOT = BACKEND


def _provider_files():
    out = []
    for f in glob.glob(os.path.join(ROOT, "providers", "**", "*.py"), recursive=True):
        if os.path.basename(f).startswith("__init__") or "__pycache__" in f:
            continue
        out.append(f)
    return sorted(out)


def test_providers_parse_clean():
    bad = []
    for f in _provider_files():
        raw = open(f, "rb").read()
        if raw[:3] == b"\xef\xbb\xbf":
            bad.append((os.path.relpath(f, ROOT), "UTF-8 BOM"))
            continue
        try:
            ast.parse(raw.decode("utf-8"))
        except SyntaxError as e:
            bad.append((os.path.relpath(f, ROOT), str(e).splitlines()[0]))
    assert not bad, f"provider layer defects: {bad}"


def test_whatsapp_provider_degraded_send():
    from providers.comms.whatsapp import send_whatsapp_message

    result = send_whatsapp_message(
        "15551234567", "hello", from_number="15557654321", preview=True
    )
    assert result["channel"] == "whatsapp"
    assert result["delivered"] is False
    assert result["preview"] is True


def test_whatsapp_service_wires_provider():
    import domains.comms.services.whatsapp_service as svc
    from providers.comms.whatsapp import send_whatsapp_message as provider_fn

    assert svc.send_whatsapp_message is provider_fn
