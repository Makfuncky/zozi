"""Regression tests for infrastructure.utils.image_ai_service backward-compat shim.

Outcome test: the shim must re-export all public names from the canonical provider
module so that existing `from infrastructure.utils.image_ai_service import *` usage
continues to work after the Law-1 fix (lazy __getattr__ loader).

Error-path test: requesting a name that does not exist in the canonical module must
raise AttributeError, not silently return None or crash with an unexpected type.
"""

from __future__ import annotations

import sys

import pytest


SHIM_PATH = "infrastructure.utils.image_ai_service"


def _import_shim():
    import importlib

    return importlib.import_module(SHIM_PATH)


class TestBackwardCompatShim:
    def test_star_import_does_not_raise(self) -> None:
        """`from shim import *` must succeed without ImportError."""
        code = "from infrastructure.utils.image_ai_service import *\nprint('OK')"
        result = subprocess_runner(code)
        assert result.returncode == 0, result.stderr
        assert "OK" in result.stdout

    def test_public_names_reexported(self) -> None:
        """Public names from the canonical provider must be reachable via the shim."""
        shim = _import_shim()
        canonical = sys.modules.get("providers.ai.image_ai_service")
        if canonical is None:
            pytest.importorskip("providers.ai.image_ai_service")
            canonical = sys.modules["providers.ai.image_ai_service"]
        public_canonical = {
            name
            for name in dir(canonical)
            if not name.startswith("_")
        }
        # The shim must at least expose the names that exist in the canonical module.
        missing = public_canonical - set(dir(shim))
        assert not missing, f"shim is missing public names: {missing}"

    def test_missing_name_raises_attribute_error(self) -> None:
        """Accessing a nonexistent name must raise AttributeError (not ImportError)."""
        shim = _import_shim()
        with pytest.raises(AttributeError):
            shim.this_name_does_not_exist_anywhere_xyzzY


# ---------------------------------------------------------------------------
# Minimal subprocess runner so the star-import test executes in a clean
# Python process with the same PYTHONPATH as the parent.
# ---------------------------------------------------------------------------
import subprocess
import os
import sys as _sys
from io import StringIO


class _SubprocessResult:
    def __init__(self, returncode: int, stdout: str, stderr: str):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def subprocess_runner(code: str) -> _SubprocessResult:
    env = os.environ.copy()
    env["PYTHONPATH"] = "backend"
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
    proc = subprocess.run(
        [_sys.executable, "-c", code],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
    )
    return _SubprocessResult(proc.returncode, proc.stdout, proc.stderr)
