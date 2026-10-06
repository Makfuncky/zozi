"""Regression guard: ``alembic upgrade head --sql`` must complete end-to-end.

This defect has returned three times; without a test it returns again.
"""
from __future__ import annotations

import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", "..", "backend"))
_ALEMBIC_INI = os.path.join(_BACKEND_ROOT, "alembic", "alembic.ini")


def test_alembic_upgrade_head_sql_completes():
    """``upgrade head --sql`` must exit 0 and emit a COMMIT;."""
    result = subprocess.run(
        ["alembic", "-c", _ALEMBIC_INI, "upgrade", "head", "--sql"],
        capture_output=True,
        text=True,
        cwd=_BACKEND_ROOT,
        timeout=300,
    )
    assert result.returncode == 0, (
        "alembic upgrade head --sql must exit 0.\n"
        f"STDOUT:\n{result.stdout[-4000:]}\n"
        f"STDERR:\n{result.stderr[-4000:]}"
    )
    assert "COMMIT;" in result.stdout, (
        "Static SQL output must contain COMMIT; to confirm transactional DDL rendering."
    )
