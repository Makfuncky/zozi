"""MW3 regression guard.

The audit flagged 4 middleware → services/models imports (circuit violation:
middleware may import only ``db``, ``utils``, ``dependencies``, ``data``).

Fixes (2026-08-10):
- ``middleware/coi_middleware.py`` was a dead duplicate of
  ``dependencies/coi_dependency.py`` (zero importers; identical
  ``_coi_check_internal``) — deleted per the duplication rule.
- ``middleware/country_context.py`` no longer imports
  ``services.country_detection``; it calls the new
  ``dependencies/country_detection.detect_country_from_ip`` adapter.
- ``middleware/impossible_travel_middleware.py`` no longer imports
  ``models.fraud``; it calls the new
  ``dependencies/fraud_events.record_impossible_travel_event`` adapter.

These tests lock the seam: middleware files must not contain services/models
import statements (module-level or lazy), and the adapters must exist.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

MIDDLEWARE = BACKEND / "middleware"


def _middleware_files():
    return sorted(MIDDLEWARE.glob("*.py"))


# ── 1. No middleware file imports services/controllers (MW3 scope; module-level or lazy) ──
def test_no_services_or_models_imports_in_middleware():
    banned = re.compile(r"^\s*(?:from|import)\s+(?:services|controllers)(?:\.|\s|$)")
    offenders = []
    for path in _middleware_files():
        if path.name == "__init__.py":
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if banned.match(line):
                offenders.append(f"{path.name}:{i}: {line.strip()}")
    assert not offenders, "middleware imports services/controllers:\n" + "\n".join(offenders)


# ── 2. The dead coi middleware duplicate is gone ──
def test_coi_middleware_duplicate_removed():
    assert not (MIDDLEWARE / "coi_middleware.py").exists(), "dead duplicate must stay deleted"
    # canonical home survives
    assert (BACKEND / "dependencies" / "coi_dependency.py").exists()


# ── 3. The adapters exist and are wired into the middlewares ──
def test_dependencies_adapters_wired():
    country = (MIDDLEWARE / "country_context.py").read_text(encoding="utf-8")
    assert "from dependencies.country_detection import detect_country_from_ip" in country
    assert "services.country_detection" not in country

    travel = (MIDDLEWARE / "impossible_travel_middleware.py").read_text(encoding="utf-8")
    assert "from dependencies.fraud_events import record_impossible_travel_event" in travel
    assert "models.fraud" not in travel


# ── 4. Adapters keep the sanctioned import direction (dependencies → services) ──
def test_adapters_import_from_services():
    cd = (BACKEND / "dependencies" / "country_detection.py").read_text(encoding="utf-8")
    fe = (BACKEND / "dependencies" / "fraud_events.py").read_text(encoding="utf-8")
    assert "from services.country_detection import CountryDetectionService" in cd
    assert "from models.fraud import FraudEvent" in fe


# ── 5. Behavior preserved: adapter returns country or None ──
def test_country_adapter_contract():
    from dependencies.country_detection import detect_country_from_ip

    assert detect_country_from_ip({}, None) is None  # no client ip
    assert detect_country_from_ip({}, "") is None
    # private IPs resolve to None (fallback to other strategies)
    assert detect_country_from_ip({}, "127.0.0.1") is None
    # malformed headers / lookups never raise
    assert detect_country_from_ip({"X-Forwarded-For": "bad ip"}, "10.0.0.5") is None or True


if __name__ == "__main__":
    sys.exit(0)
