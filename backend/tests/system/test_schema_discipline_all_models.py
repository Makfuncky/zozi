"""Law 6/23/55/152 — schema discipline + FK ondelete guard for the WHOLE DB layer.

Imports every domain's models package, iterates Base.__subclasses__(), and for
EACH model asserts:
  * schema discipline via ``laws.assert_schema_discipline``
  * FK ondelete via ``laws.assert_foreign_keys_have_ondelete``

This is the single cross-cutting gate that guards the entire ORM surface.
Failures are real violations — report them, do not weaken the test.
"""
from __future__ import annotations

import pytest

from tests._support import laws


# All 16 domains' model packages (Law 12).
_DOMAIN_MODEL_PACKAGES: tuple[str, ...] = tuple(
    f"domains.{d}.models" for d in laws.ALL_DOMAINS
)


@pytest.fixture(scope="module", autouse=True)
def _import_all_models():
    """Ensure every domain's models are imported so Base.metadata is populated."""
    for pkg in _DOMAIN_MODEL_PACKAGES:
        try:
            laws.import_module(pkg)
        except Exception:
            pass  # domain may have no models package; individual tests below catch gaps


class TestEveryModelHasSchemaDiscipline:
    """Law 6/55: every ORM model declares a domain Postgres schema."""

    def test_all_models_declare_schema(self, _import_all_models):
        from infrastructure.database.base import Base

        models = [m for m in Base.__subclasses__() if getattr(m, "__table__", None)]
        assert models, "No ORM models found — models failed to import"

        offenders: list[str] = []
        for model in models:
            try:
                laws.assert_schema_discipline(model)
            except AssertionError as exc:
                offenders.append(f"{model.__module__}.{model.__name__}: {exc}")

        assert not offenders, (
            "Law 6/55 violation: model(s) fail schema discipline:\n  "
            + "\n  ".join(offenders)
        )


class TestEveryForeignKeyHasOndelete:
    """Law 22/52: every ForeignKey declares explicit ondelete."""

    def test_all_foreign_keys_have_ondelete(self, _import_all_models):
        from infrastructure.database.base import Base

        models = [m for m in Base.__subclasses__() if getattr(m, "__table__", None)]
        assert models, "No ORM models found"

        offenders: list[str] = []
        for model in models:
            try:
                laws.assert_foreign_keys_have_ondelete(model)
            except AssertionError as exc:
                offenders.append(f"{model.__module__}.{model.__name__}: {exc}")

        assert not offenders, (
            "Law 22/52 violation: FK(s) missing ondelete:\n  "
            + "\n  ".join(offenders)
        )


class TestEveryDomainHasModels:
    """Law 12/150: every domain package should expose a models package with at least one model."""

    @pytest.mark.parametrize("domain", laws.ALL_DOMAINS)
    def test_domain_has_models(self, domain):
        pkg = f"domains.{domain}.models"
        try:
            laws.import_module(pkg)
        except ImportError:
            pytest.fail(f"Domain {domain} has no importable models package ({pkg})")

        from infrastructure.database.base import Base

        domain_models = [
            m for m in Base.__subclasses__()
            if getattr(m, "__module__", "").startswith(f"domains.{domain}.")
            and getattr(m, "__table__", None)
        ]
        assert domain_models, (
            f"Domain {domain} has no ORM models registered in Base.metadata"
        )
