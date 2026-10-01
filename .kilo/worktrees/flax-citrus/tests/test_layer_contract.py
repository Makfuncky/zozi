"""Regression test for the controller layer contract (LC1 / W1).

Controllers orchestrate request handling; per the circuit plan they must not
open sessions or perform DB writes (add/commit/delete/merge/flush). Those
belong in ``services/``. This test fails if any controller acquires a session
or commits a transaction, catching regressions like the one fixed in
``controllers/cash_management_controller.py`` (LC1: session.commit() at :870).
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONTROLLERS = REPO / "backend" / "controllers"

_WRITE_RE = re.compile(r"\b(?:session|db|conn)\.(add|commit|delete|merge|flush)\(")


def _controller_files():
    return sorted(CONTROLLERS.rglob("*.py"))


def test_controllers_perform_no_db_writes():
    offenders: list[tuple[str, int, str]] = []
    for f in _controller_files():
        text = f.read_text(encoding="utf-8")
        for m in _WRITE_RE.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            offenders.append((f.name, line_no, m.group(0)))
    assert not offenders, f"DB writes found in controllers/ (LC1/W1): {offenders}"
