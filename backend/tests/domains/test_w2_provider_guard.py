"""Architecture guard: Layer-2 (W2) forbids provider / vendor SDK code in the
domain **service** layer.

The contract: ``providers`` own ALL vendor integration code (Stripe, OpenAI,
Ollama, HuggingFace, Twilio, Resend, rembg, boto3, ...). Service modules
(``domains/<x>/*_service.py``) must call through a provider module, never import
and drive the SDK directly.

After the NEW_STRUCTURE migration the flat ``backend/services`` package was
retired; service logic now lives inside each domain package
(``domains/<x>/.../*_service.py``). This test counts each known vendor token
inside that service layer and fails the build only when a count *exceeds* the
recorded baseline. The baseline is the current (pre-refactor) number of direct
usages; as we migrate services to delegate to ``providers/*`` these counts
should drop. Any NEW direct usage (a count above baseline) is an immediate
regression and fails CI, so the cleanup cannot silently leak new vendor code
back into the service layer.
"""
from __future__ import annotations

import pathlib
import re

import pytest

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent
_DOMAINS = _BACKEND_ROOT / "domains"


def _service_files():
    if not _DOMAINS.exists():
        return
    for path in sorted(_DOMAINS.rglob("*_service.py")):
        if path.name == "__init__.py":
            continue
        yield path


def _read_source(path: pathlib.Path) -> str:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):  # strip UTF-8 BOM
        data = data[3:]
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="replace")


# (token, regex) -> current direct-usage count across the domains/ service layer.
# Bump a baseline DOWN only after the corresponding migration lands; never set it
# higher to silence a failure.
_BASELINE = {
    "stripe.": 2,
    "resend": 79,
    "rembg": 73,
    "ollama": 8,
    "huggingface": 27,
    "openai": 0,
    "twilio": 3,
    "boto3": 0,
}

_COMPILED = {tok: re.compile(re.escape(tok), re.IGNORECASE) for tok in _BASELINE}


def _count_token(tok: str) -> int:
    rx = _COMPILED[tok]
    total = 0
    for path in _service_files():
        total += len(rx.findall(_read_source(path)))
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
            f"  {tok}: {got} direct usages (baseline {base}) — NEW vendor code in domains/ service layer"
            for tok, (got, base) in regressions.items()
        )
        raise AssertionError(
            "W2 violation: provider SDK leaked into domains/ service layer beyond baseline:\n" + lines
        )


def test_provider_baseline_recorded() -> None:
    # Documents the current migration debt so it cannot be zeroed out by accident.
    assert _RESULTS == _BASELINE, (
        "W2 baseline drift — update _BASELINE only after a migration lands:\n"
        + "\n".join(f"  {tok}: now {got}, baseline {_BASELINE[tok]}" for tok, got in _RESULTS.items())
    )


def test_services_dir_exists() -> None:
    assert _DOMAINS.exists(), "expected domains/ package directory"
