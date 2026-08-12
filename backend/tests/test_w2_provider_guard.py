"""Architecture guard: Layer-2 (W2) forbids provider / vendor SDK code in
``services/``.

The contract: ``providers`` own ALL vendor integration code (Stripe, OpenAI,
Ollama, HuggingFace, Twilio, Resend, rembg, boto3, ...). ``services`` must call
through a provider module, never import and drive the SDK directly.

This test counts each known vendor token inside ``services/`` and fails the build
only when a count *exceeds* the recorded baseline. The baseline is the current
(pre-refactor) number of direct usages; as we migrate services to delegate to
``providers/*`` these counts should drop. Any NEW direct usage (a count above
baseline) is an immediate regression and fails CI, so the cleanup cannot silently
leak new vendor code back into the service layer.
"""
from __future__ import annotations

import re

import pytest

_BACKEND_ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent
_SERVICES = _BACKEND_ROOT / "services"

# (token, regex) -> current direct-usage count across services/.
# Bump a baseline DOWN only after the corresponding migration lands; never set it
# higher to silence a failure.
_BASELINE = {
    "stripe.": 29,
    "resend": 47,
    "rembg": 69,
    "ollama": 56,
    "huggingface": 14,
    "openai": 6,
    "twilio": 14,
    "boto3": 1,
}

_COMPILED = {tok: re.compile(re.escape(tok), re.IGNORECASE) for tok in _BASELINE}


def _count_token(tok: str) -> int:
    rx = _COMPILED[tok]
    total = 0
    for path in sorted(_SERVICES.rglob("*.py")):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        total += len(rx.findall(text))
    return total


_RESULTS = {tok: _count_token(tok) for tok in _BASELINE}


def test_no_new_provider_sdk_in_services() -> None:
    regressions = {
        tok: (got, _BASELINE[tok])
        for tok, got in _RESULTS.items()
        if got > _BASELINE[tok]
    }
    if regressions:
        lines = "\n".join(
            f"  {tok}: {got} direct usages (baseline {base}) — NEW vendor code in services/"
            for tok, (got, base) in regressions.items()
        )
        raise AssertionError(
            "W2 violation: provider SDK leaked into services/ beyond baseline:\n" + lines
        )


def test_provider_baseline_recorded() -> None:
    # Documents the current migration debt so it cannot be zeroed out by accident.
    assert _RESULTS == _BASELINE, (
        "W2 baseline drift — update _BASELINE only after a migration lands:\n"
        + "\n".join(f"  {tok}: now {got}, baseline {_BASELINE[tok]}" for tok, got in _RESULTS.items())
    )


def test_services_dir_exists() -> None:
    assert _SERVICES.exists(), "expected services/ layer directory"
