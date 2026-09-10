"""Locale-aware template resolver tests (Phase G).

Validates the AE/SA variants in ``backend/templates/`` are picked up by
``domains.comms.services.templates.render`` and that the resolver falls
back to the default English body for everything else.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make tests._support importable (matches existing comms test convention).
_TESTS_DIR = Path(__file__).resolve().parent.parent.parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

from domains.comms.services.templates import (  # noqa: E402
    SUPPORTED_LOCALES,
    has_locale_variant,
    render,
)
from infrastructure.utils.message_templates import (  # noqa: E402
    TEMPLATES,
    render_template,
)


# Every template shipped today must have both AE and SA variants.
ALL_TEMPLATE_IDS = sorted(TEMPLATES.keys())


@pytest.fixture(autouse=True)
def _reset_template_cache():
    """Make sure the resolver cache is fresh per test."""
    from domains.comms.services import templates as _tpl

    _tpl.clear_cache()
    yield
    _tpl.clear_cache()


class TestResolverFallsBack:
    """Default behaviour when no locale is requested must not change."""

    def test_no_country_uses_english_default(self):
        body = render("order_confirmed_sms", order_id="X1", total="100")
        assert body == render_template("order_confirmed_sms", order_id="X1", total="100")

    def test_unknown_country_uses_english_default(self):
        body = render("order_confirmed_sms", country_code="US", order_id="X1", total="100")
        assert body == render_template("order_confirmed_sms", order_id="X1", total="100")

    def test_unknown_template_raises(self):
        with pytest.raises(ValueError, match="Template not found"):
            render("nope_does_not_exist", country_code="AE")


class TestLocaleResolution:
    """AE / SA must resolve to their locale files."""

    @pytest.mark.parametrize("cc", ["AE", "SA"])
    def test_supported_locales_contains_target(self, cc: str):
        assert cc in SUPPORTED_LOCALES

    @pytest.mark.parametrize("tid", ALL_TEMPLATE_IDS)
    @pytest.mark.parametrize("cc", ["ae", "sa", "AE", "SA"])
    def test_all_templates_have_ae_and_sa_variants(self, tid: str, cc: str):
        assert has_locale_variant(tid, cc), f"missing locale file for {tid} / {cc}"

    def test_ae_renders_arabic_body_with_variables(self):
        body = render(
            "order_confirmed_sms",
            country_code="AE",
            order_id="12345",
            total="250 AED",
        )
        assert "12345" in body
        assert "250 AED" in body
        # Arabic script U+0600..U+06FF — confirms localized body
        assert any("\u0600" <= ch <= "\u06FF" for ch in body), body

    def test_sa_renders_arabic_body_with_variables(self):
        body = render(
            "order_confirmed_sms",
            country_code="SA",
            order_id="98765",
            total="300 SAR",
        )
        assert "98765" in body
        assert "300 SAR" in body
        assert any("\u0600" <= ch <= "\u06FF" for ch in body), body

    def test_ae_and_sa_differ_for_same_template(self):
        ae = render(
            "welcome_sms",
            country_code="AE",
        )
        sa = render(
            "welcome_sms",
            country_code="SA",
        )
        assert ae != sa, "AE and SA welcome copy must be distinct"


class TestMissingKeysAreTolerant:
    """Locale renderer should not crash on missing variables."""

    def test_missing_var_uses_safe_placeholder(self):
        body = render("order_confirmed_sms", country_code="AE")
        # No variables supplied — at least one must surface the placeholder
        # token for the substituted keys.
        assert "<missing:" in body


class TestEveryTemplateHasLocaleFile:
    """Filesystem-level guarantee that no template is left behind."""

    def _expected_files(self, suffix: str) -> list[Path]:
        # backend/tests/domains/comms -> backend/domains/comms/templates (Phase 4D)
        tpl_dir = Path(__file__).resolve().parents[3] / "domains" / "comms" / "templates"
        return [tpl_dir / f"{tid}.{suffix}.txt" for tid in ALL_TEMPLATE_IDS]

    def test_ae_files_present(self):
        missing = [p for p in self._expected_files("ae") if not p.is_file()]
        assert not missing, f"missing AE files: {missing}"

    def test_sa_files_present(self):
        missing = [p for p in self._expected_files("sa") if not p.is_file()]
        assert not missing, f"missing SA files: {missing}"
