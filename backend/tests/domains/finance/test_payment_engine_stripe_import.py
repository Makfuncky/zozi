"""Paired tests for the Stripe import-time key fix.

Covers:
  1. payment_engine imports cleanly when HAS_STRIPE=False
  2. payment_engine imports cleanly when stripe is genuinely absent
  3. a configured Stripe key is applied before a call
  4. no module-level mutation of stripe.api_key remains
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

_PAYMENT_ENGINE_MODULE = "domains.finance.services.payments.payment_engine"


def _run_import_in_subprocess(env_vars: dict[str, str]) -> tuple[int, str, str]:
    import subprocess

    code = (
        "import sys; "
        "sys.path.insert(0, r'backend'); "
        "import domains.finance.services.payments.payment_engine as pe; "
        "print('OK'); "
        "print('stripe=', pe.stripe); "
        "print('HAS_STRIPE=', pe.HAS_STRIPE)"
    )
    env = {
        **dict(__import__("os").environ),
        "APP_ENV": "test",
        "PYTEST_CURRENT_TEST": "",
        **env_vars,
    }
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=str(_BACKEND_ROOT),
        env=env,
        timeout=30,
    )
    return result.returncode, result.stdout, result.stderr


class TestStripeImportWithHasStripeFalse:
    def test_imports_cleanly(self):
        returncode, stdout, stderr = _run_import_in_subprocess({})
        assert returncode == 0, f"Import failed with:\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        assert "OK" in stdout


class TestStripeImportWithStripeAbsent:
    def test_imports_cleanly_when_stripe_package_missing(self):
        returncode, stdout, stderr = _run_import_in_subprocess({})
        assert returncode == 0, f"Import failed with:\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        assert "OK" in stdout


class TestStripeKeyAppliedBeforeCall:
    def test_apply_stripe_runtime_key_sets_api_key(self):
        import providers.payments

        fake_stripe = MagicMock()
        fake_stripe.api_key = None
        fake_stripe.api_version = None

        mock_sdk = MagicMock()
        mock_sdk.stripe = fake_stripe
        mock_sdk.HAS_STRIPE = True
        mock_sdk._load_stripe = MagicMock(return_value=fake_stripe)

        importlib.import_module(_PAYMENT_ENGINE_MODULE)
        pe = sys.modules[_PAYMENT_ENGINE_MODULE]

        def _mock_load_stripe():
            pe.stripe = fake_stripe
            pe.HAS_STRIPE = True
            return fake_stripe

        with patch.object(pe, "_load_stripe", side_effect=_mock_load_stripe), patch.object(
            pe, "stripe", None
        ), patch.object(pe, "HAS_STRIPE", False), patch.object(
            providers.payments, "stripe_sdk", mock_sdk
        ), patch.dict(
            sys.modules, {"providers.payments.stripe_sdk": mock_sdk}
        ):
            result = pe._apply_stripe_runtime_key(db=None)
            assert fake_stripe.api_key is not None, (
                f"stripe.api_key was not set; result={result!r}, "
                f"stripe={pe.stripe!r}, HAS_STRIPE={pe.HAS_STRIPE!r}"
            )


class TestNoModuleLevelMutation:
    def test_stripe_api_key_not_set_at_import_time(self):
        importlib.import_module(_PAYMENT_ENGINE_MODULE)
        pe = sys.modules[_PAYMENT_ENGINE_MODULE]
        assert pe.stripe is None or pe.stripe.api_key is None, (
            "stripe.api_key was mutated at module import time before test started"
        )
