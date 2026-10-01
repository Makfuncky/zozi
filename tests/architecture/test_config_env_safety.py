"""ENV safety tests for backend/config.py (FILE-8 contract).

Paired test: tests/architecture/test_config_env_safety.py
Contract  : _audit/_audit/resolver/contracts/file-8.md
"""

from __future__ import annotations

import copy
import os
import subprocess
import sys
from pathlib import Path

import pytest

_BACKEND_ROOT = Path(__file__).resolve().parents[2] / "backend"
_REPO_ROOT = _BACKEND_ROOT.parent
_SYSPATH_LINE = (
    f"import sys; sys.path.insert(0, r'{_REPO_ROOT}'); "
)


def _run_python(code: str) -> subprocess.CompletedProcess:
    full_code = _SYSPATH_LINE + code
    return subprocess.run(
        [sys.executable, "-c", full_code],
        capture_output=True,
        text=True,
        cwd=str(_BACKEND_ROOT),
    )


class TestNoEnvironmentMutation:
    """Settings.__init__ must not permanently mutate os.environ.

    dotenv loading happens at module import time (outside Settings.__init__),
    so env_before is captured after import but before Settings() instantiation.
    """

    def test_no_environment_mutation_on_init(self):
        from backend.config import Settings
        env_before = copy.deepcopy(dict(os.environ))
        Settings()
        env_after = dict(os.environ)
        assert env_before == env_after, (
            "os.environ was mutated by Settings() init. "
            f"Added: {sorted(set(env_after) - set(env_before))}, "
            f"Removed: {sorted(set(env_before) - set(env_after))}"
        )

    def test_no_environment_mutation_with_kwargs(self):
        from backend.config import Settings
        env_before = copy.deepcopy(dict(os.environ))
        Settings(secret_key="a" * 40, app_env="development")
        env_after = dict(os.environ)
        assert env_before == env_after, (
            "os.environ was mutated by Settings() init with kwargs. "
            f"Added: {sorted(set(env_after) - set(env_before))}, "
            f"Removed: {sorted(set(env_before) - set(env_after))}"
        )

    def test_explicit_kwargs_take_precedence_over_env(self):
        from backend.config import Settings
        s = Settings(secret_key="explicit_secret_key_12345678901234567890", app_env="development")
        assert s.secret_key == "explicit_secret_key_12345678901234567890", (
            "Explicit kwargs must not be shadowed by env values"
        )


class TestAlgorithmSync:
    """jwt_algorithm must follow ALGORITHM env var."""

    def test_jwt_algorithm_defaults_to_algorithm_field(self):
        code = (
            "import os; os.environ['ALGORITHM'] = 'HS512'\n"
            "import sys; sys.path.insert(0, r'" + str(_REPO_ROOT) + "')\n"
            "from backend.config import Settings\n"
            "s = Settings()\n"
            "assert s.algorithm == 'HS512', f'algorithm={s.algorithm}'\n"
            "assert s.jwt_algorithm == 'HS512', f'jwt_algorithm={s.jwt_algorithm}'\n"
        )
        result = _run_python(code)
        assert result.returncode == 0, f"algorithm sync test failed:\n{result.stderr}"

    def test_jwt_algorithm_does_not_diverge_from_algorithm(self):
        from backend.config import Settings
        s = Settings()
        assert s.jwt_algorithm == s.algorithm, (
            f"jwt_algorithm ({s.jwt_algorithm}) must equal algorithm ({s.algorithm})"
        )


class TestBackendDotenvLoaded:
    """backend/.env must be loaded so its SECRET_KEY is available."""

    def test_backend_env_secret_key_loaded(self):
        code = (
            "import sys; sys.path.insert(0, r'" + str(_REPO_ROOT) + "')\n"
            "from backend.config import Settings\n"
            "s = Settings()\n"
            "assert s.secret_key, 'SECRET_KEY from backend/.env was not loaded'\n"
        )
        result = _run_python(code)
        assert result.returncode == 0, f"backend/.env loading test failed:\n{result.stderr}"
        assert "SECRET_KEY from backend/.env was not loaded" not in (result.stdout + result.stderr)
