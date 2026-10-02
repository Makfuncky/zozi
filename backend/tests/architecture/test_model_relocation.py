"""Model relocation discipline (ARCHTEST-002): domain models live in
``domains/<domain>/models/``.

Run: ``pytest tests/architecture/test_model_relocation.py -q``

Why this exists
---------------
Domain ORM models were historically scattered across services, routers and
stray ``models.py`` modules, then relocated into per-domain ``models``
packages. Relocation only stays complete if a gate fails when a model is
re-introduced outside that package: the schema scanners, the cross-domain
import laws (Law 3) and alembic autogenerate all key off the
``domains/<domain>/models`` location.

Stdlib + pytest only on purpose - see the module docstring of
``test_schema_discipline.py`` for the collection-order constraint.
"""
from __future__ import annotations

import pathlib
import re

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_DOMAINS_DIR = _BACKEND_ROOT / "domains"

_SKIP_DIRS = {".venv", "__pycache__", ".hypothesis", ".pytest_cache", ".ruff_cache"}
_TABNAME_RE = re.compile(r"__tablename__\s*=")


def _rel(path: pathlib.Path) -> str:
    return path.relative_to(_BACKEND_ROOT).as_posix()


def _domain_dirs() -> list[pathlib.Path]:
    if not _DOMAINS_DIR.exists():
        return []
    return sorted(
        entry
        for entry in _DOMAINS_DIR.iterdir()
        if entry.is_dir() and entry.name not in _SKIP_DIRS
    )


def _domain_python_files() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for domain in _domain_dirs():
        for path in sorted(domain.rglob("*.py")):
            if any(part in _SKIP_DIRS for part in path.parts):
                continue
            files.append(path)
    return files


def _domain_model_files() -> list[pathlib.Path]:
    found: list[pathlib.Path] = []
    for path in _domain_python_files():
        try:
            source = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if _TABNAME_RE.search(source):
            found.append(path)
    return found


class TestEveryDomainHasAModelsPackage:
    """Each domain ships a real ``models`` package that tooling can import."""

    def test_domains_exist(self):
        assert _domain_dirs(), "no domain packages discovered under domains/"

    def test_every_domain_has_a_models_package(self):
        missing = [
            domain.name for domain in _domain_dirs() if not (domain / "models").is_dir()
        ]
        assert not missing, (
            "domain(s) without a models/ package:\n  " + "\n  ".join(missing)
        )

    def test_models_packages_are_importable(self):
        missing = sorted(
            _rel(domain / "models")
            for domain in _domain_dirs()
            if (domain / "models").is_dir()
            and not (domain / "models" / "__init__.py").exists()
        )
        assert not missing, (
            "models package without __init__.py:\n  " + "\n  ".join(missing)
        )

    def test_no_stray_models_module_in_domains(self):
        strays = sorted(
            _rel(path)
            for path in _domain_python_files()
            if path.name == "models.py"
        )
        assert not strays, (
            "stray `models.py` module(s) found - relocate the definitions into "
            "the domain's models/ package:\n  " + "\n  ".join(strays)
        )


class TestDomainModelsStayRelocated:
    """Relocated models must not creep back out of ``domains/<d>/models/``."""

    def test_scan_finds_domain_models(self):
        assert _domain_model_files(), (
            "no ORM models discovered under domains/ - scanner or layout broken"
        )

    def test_domain_models_only_under_models_package(self):
        offenders = sorted(
            _rel(path)
            for path in _domain_model_files()
            if path.relative_to(_DOMAINS_DIR).parts[1] != "models"
        )
        assert not offenders, (
            "domain ORM model(s) outside domains/<domain>/models/:\n  "
            + "\n  ".join(offenders)
            + "\n  relocate the model - schema discovery and Law 3 import "
            "checks only scan the models packages"
        )

    def test_model_directories_are_python_packages(self):
        missing = sorted(
            _rel(model_dir)
            for model_dir in {path.parent for path in _domain_model_files()}
            if not (model_dir / "__init__.py").exists()
        )
        assert not missing, (
            "directory holding domain ORM model(s) without an __init__.py:\n  "
            + "\n  ".join(missing)
        )

    def test_model_module_paths_are_domain_scoped(self):
        """Every model module resolves below ``domains.<domain>.models``."""
        offenders = sorted(
            _rel(path)
            for path in _domain_model_files()
            if len(path.relative_to(_DOMAINS_DIR).parts) < 3
        )
        assert not offenders, (
            "domain ORM model module(s) not importable as "
            "`domains.<domain>.models...`:\n  " + "\n  ".join(offenders)
        )
