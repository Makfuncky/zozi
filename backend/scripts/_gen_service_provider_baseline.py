"""Baseline generator for the service -> provider leakage gate (P3).

Scans ``services/**`` for direct external-SDK imports (httpx, requests, openai,
stripe, twilio, ...) and freezes the current offenders so the architecture
gate only fails on *new* leakage. This mirrors the router-logic baseline
(``_router_logic_baseline.txt``): legacy debt is frozen and must only
decrease, migrating per-feature with verification.

Regenerate after an intentional relocation:
    python scripts/_gen_service_provider_baseline.py
"""
from __future__ import annotations

import os
import re

def _find_backend_root() -> str:
    d = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.exists(os.path.join(d, "main.py")) and os.path.isdir(os.path.join(d, "modules")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


BACKEND = _find_backend_root()
SERVICES_DIR = os.path.join(BACKEND, "services")
BASELINE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_service_provider_baseline.txt")

# Third-party vendor SDKs that belong behind a ``providers/**`` wrapper, not
# imported directly by a service. Internal/framework deps (mcp, fastapi,
# sqlalchemy, pydantic, structlog, ...) are intentionally NOT listed.
EXTERNAL_SDKS = {
    "httpx", "requests", "openai", "stripe", "twilio", "ollama", "sendgrid",
    "google", "slack", "shopify", "paypal", "boto3", "azure", "groq",
    "anthropic", "cohere", "telebot", "telegram", "facebook", "synapse",
}

_IMPORT_RE = re.compile(
    r"^\s*(?:import\s+([a-zA-Z_][\w.]*)|from\s+([a-zA-Z_][\w.]*)\s+import)"
)


def _top_module(name: str) -> str:
    return name.split(".")[0]


def scan_service_sdk_files():
    """Yield (rel_path, sdk) for service modules that import an external SDK."""
    out = []
    for dirpath, _, files in os.walk(SERVICES_DIR):
        for fn in files:
            if not fn.endswith(".py") or fn == "__init__.py":
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, BACKEND).replace(os.sep, "/")
            try:
                src = open(fp, encoding="utf-8").read()
            except Exception:
                continue
            for line in src.splitlines():
                m = _IMPORT_RE.match(line)
                if not m:
                    continue
                mod = m.group(1) or m.group(2)
                top = _top_module(mod)
                if top in EXTERNAL_SDKS:
                    out.append((rel, top))
    return out


def load_baseline():
    if not os.path.isfile(BASELINE_FILE):
        return set()
    out = set()
    for line in open(BASELINE_FILE, encoding="utf-8"):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.add(s)
    return out


if __name__ == "__main__":
    offenders = sorted(set(rel for rel, _ in scan_service_sdk_files()))
    with open(BASELINE_FILE, "w", encoding="utf-8") as fh:
        fh.write(
            "# Frozen list of services that currently import an external\n"
            "# third-party SDK directly (provider concern that belongs in\n"
            "# providers/**). Count must only DECREASE. Regenerate after an\n"
            "# intentional relocation: python scripts/_gen_service_provider_baseline.py\n"
            "# Format: one repo-root-relative path per line.\n"
        )
        for rel in offenders:
            fh.write(rel + "\n")
    print(f"WROTE baseline: {len(offenders)} service(s) with external-SDK imports")
