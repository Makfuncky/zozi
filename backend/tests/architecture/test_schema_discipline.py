"""Schema discipline gate (ARCHTEST-001): ORM models live in a ``models`` package.

Run: ``pytest tests/architecture/test_schema_discipline.py -q``

Why this exists
---------------
Schema tooling (alembic autogenerate, ``iter_domain_models``, RLS audits and the
``domains/<domain>/models`` import contract) discovers ORM tables by scanning
``models`` packages. A model declared next to a router, service or utility
silently escapes those checks, which is how tables were duplicated and later
relocated. This gate keeps new ORM table definitions inside a ``models``
package so the tooling can always find them by path.

This module is deliberately stdlib + pytest only: architecture tests are
collected *before* ``tests/config`` installs a valid ``SECRET_KEY``, so
importing application code here would abort the whole collection run.
"""
from __future__ import annotations

import pathlib
import re

import pytest

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

_SKIP_DIRS = {
    ".venv",
    "__pycache__",
    ".hypothesis",
    ".pytest_cache",
    ".ruff_cache",
    "logs",
    "var",
    "node_modules",
    "_audit",
    "tests",
}

_TABNAME_RE = re.compile(r"__tablename__\s*=")

# Model packages sanctioned outside ``domains/`` (legacy RBAC permission tables).
NON_DOMAIN_MODEL_PACKAGES = frozenset({"rbac/models"})


def _iter_python_files():
    """Yield every first-party Python file (tests/ and tooling caches skipped)."""
    for entry in sorted(_BACKEND_ROOT.iterdir()):
        if entry.name in _SKIP_DIRS:
            continue
        if entry.is_file():
            if entry.suffix == ".py":
                yield entry
            continue
        if not entry.is_dir():
            continue
        for path in sorted(entry.rglob("*.py")):
            rel_parts = path.relative_to(_BACKEND_ROOT).parts
            if any(part in _SKIP_DIRS for part in rel_parts):
                continue
            yield path


def _rel(path: pathlib.Path) -> str:
    return path.relative_to(_BACKEND_ROOT).as_posix()


def _model_files() -> list[pathlib.Path]:
    """First-party files that declare an ORM table (``__tablename__ = ...``)."""
    found: list[pathlib.Path] = []
    for path in _iter_python_files():
        try:
            source = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if _TABNAME_RE.search(source):
            found.append(path)
    return found


def _is_in_models_package(path: pathlib.Path) -> bool:
    return "/models/" in f"/{_rel(path)}"


class TestScanIntegrity:
    """Guard the scanner itself so a broken scan cannot fake a green gate."""

    def test_scan_finds_model_files(self):
        files = _model_files()
        assert files, (
            "no ORM model files were discovered - the scanner is broken or "
            "every model was moved out of the backend tree"
        )

    def test_scan_finds_domain_models(self):
        domain_models = [p for p in _model_files() if _rel(p).startswith("domains/")]
        assert domain_models, "no models discovered under domains/"


class TestORMModelsLiveInModelsPackages:
    """Every ``__tablename__`` definition must sit inside a ``models`` package."""

    def test_model_files_live_in_a_models_package(self):
        offenders = sorted(_rel(p) for p in _model_files() if not _is_in_models_package(p))
        assert not offenders, (
            "ORM model(s) declared outside a `models` package:\n  "
            + "\n  ".join(offenders)
        )

    def test_model_packages_are_python_packages(self):
        missing = sorted(
            _rel(model_dir)
            for model_dir in {p.parent for p in _model_files()}
            if not (model_dir / "__init__.py").exists()
        )
        assert not missing, (
            "model directory without `__init__.py`:\n  " + "\n  ".join(missing)
        )

    def test_no_models_under_domain_services(self):
        offenders = sorted(
            _rel(p)
            for p in _model_files()
            if _rel(p).startswith("domains/") and "/services/" in _rel(p)
        )
        assert not offenders, (
            "ORM model(s) re-introduced under a domain service layer:\n  "
            + "\n  ".join(offenders)
        )

    def test_no_models_under_module_routers(self):
        offenders = sorted(
            _rel(p) for p in _model_files() if _rel(p).startswith("modules/")
        )
        assert not offenders, (
            "ORM model(s) declared under HTTP routers:\n  " + "\n  ".join(offenders)
        )


class TestNonDomainModelPackages:
    """Only the legacy RBAC package may hold models outside ``domains/``."""

    def test_no_new_model_packages_outside_domains(self):
        outside = {
            "/".join(_rel(p).split("/")[:2])
            for p in _model_files()
            if not _rel(p).startswith("domains/")
        }
        unexpected = sorted(outside - NON_DOMAIN_MODEL_PACKAGES)
        assert not unexpected, (
            "model package(s) outside domains/ are not on the allowlist:\n  "
            + "\n  ".join(unexpected)
            + "\n  (move the model into domains/<domain>/models/ or extend "
            "NON_DOMAIN_MODEL_PACKAGES after review)"
        )
