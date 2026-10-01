import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BACKEND_ROOT = _REPO_ROOT / "backend"
CONFIG_PATH = _BACKEND_ROOT / "config.py"

_SYSPATH_LINE = (
    f"import sys; sys.path.insert(0, r'{_REPO_ROOT}'); "
)


def _run_python(code: str) -> subprocess.CompletedProcess:
    full_code = _SYSPATH_LINE + code
    return subprocess.run(
        [sys.executable, "-c", full_code],
        capture_output=True,
        text=True,
        cwd=_BACKEND_ROOT,
    )


class TestNumericFieldConstraints:
    """CFG-012: every numeric Settings field must carry ge/le bounds."""

    def test_all_int_fields_have_ge_or_le(self):
        code = (
            "from backend.config import Settings\n"
            "from pydantic import Field\n"
            "missing = []\n"
            "for name, info in Settings.model_fields.items():\n"
            "    if info.annotation is int:\n"
            "        has_constraint = any(\n"
            "            type(m).__name__ in ('Ge', 'Le', 'Gt', 'MultipleOf')\n"
            "            for m in info.metadata\n"
            "        )\n"
            "        if not has_constraint:\n"
            "            missing.append(name)\n"
            "assert not missing, f'int fields missing ge/le: {missing}'\n"
        )
        result = _run_python(code)
        assert result.returncode == 0, (
            f"int field constraint check failed:\n{result.stderr}"
        )

    def test_all_float_fields_have_ge_or_le(self):
        code = (
            "from backend.config import Settings\n"
            "missing = []\n"
            "for name, info in Settings.model_fields.items():\n"
            "    if info.annotation is float:\n"
            "        has_constraint = any(\n"
            "            type(m).__name__ in ('Ge', 'Le', 'Gt', 'MultipleOf')\n"
            "            for m in info.metadata\n"
            "        )\n"
            "        if not has_constraint:\n"
            "            missing.append(name)\n"
            "assert not missing, f'float fields missing ge/le: {missing}'\n"
        )
        result = _run_python(code)
        assert result.returncode == 0, (
            f"float field constraint check failed:\n{result.stderr}"
        )

    def test_db_pool_size_bounds_match_validator(self):
        code = (
            "from backend.config import Settings\n"
            "info = Settings.model_fields['db_pool_size']\n"
            "le = next((m.le for m in info.metadata if type(m).__name__ == 'Le'), None)\n"
            "assert le is not None and le >= 50, f'db_pool_size le ({le}) must be >= default 50'\n"
        )
        result = _run_python(code)
        assert result.returncode == 0, (
            f"db_pool_size bounds check failed:\n{result.stderr}"
        )

    def test_db_max_overflow_bounds_cover_default(self):
        code = (
            "from backend.config import Settings\n"
            "info = Settings.model_fields['db_max_overflow']\n"
            "le = next((m.le for m in info.metadata if type(m).__name__ == 'Le'), None)\n"
            "assert le is not None and le >= 100, f'db_max_overflow le ({le}) must be >= default 100'\n"
        )
        result = _run_python(code)
        assert result.returncode == 0, (
            f"db_max_overflow bounds check failed:\n{result.stderr}"
        )


class TestNoRawOsGetenvInConfigModule:
    """ENV-11-026: raw os.getenv in config.py must be documented."""

    def test_raw_os_getenv_calls_have_documentation(self):
        source = CONFIG_PATH.read_text(encoding="utf-8")
        lines = source.splitlines()
        raw_calls = []
        for i, line in enumerate(lines, 1):
            if "os.getenv(" in line or "os.environ" in line:
                raw_calls.append((i, line.strip()))

        assert raw_calls, "expected raw os.getenv calls to exist and be documented"

        undocumented = []
        for lineno, line in raw_calls:
            window_before = max(0, lineno - 15)
            window_after = min(len(lines), lineno + 8)
            window = "\n".join(lines[window_before:window_after])
            has_note = "NOTE:" in window
            if not has_note:
                undocumented.append(f"  line {lineno}: {line}")

        assert not undocumented, (
            f"Not all raw os.getenv calls are documented (NOTE: must appear within 15 lines before or 7 lines after):\n"
            + "\n".join(undocumented)
        )
