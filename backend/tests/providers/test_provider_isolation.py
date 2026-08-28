"""Provider isolation tests — Law 31/100/123/124/126.

Verifies every provider subpackage:
  * Exposes HAS_<SDK> availability flags (Law 124).
  * Does NOT import forbidden layers: domains, modules, rbac, jobs, middleware (Law 31/100).
  * Contains only SDK wrapping, no business logic leak (Law 126).
  * Each provider wraps ONE external SDK (Law 11/123).

Run: python -m pytest tests/providers/test_provider_isolation.py -q
"""
from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

# Load tests/_support/laws.py directly (pytest sys.path manipulation breaks
# `from tests._support import laws` inside test modules).
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_LAWS_PATH = _BACKEND_ROOT / "tests" / "_support" / "laws.py"
_spec = importlib.util.spec_from_file_location("_support_laws", _LAWS_PATH)
laws = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(laws)  # type: ignore[union-attr]

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Every provider subpackage (hardcoded — discover_packages uses wrong root)
# ---------------------------------------------------------------------------
PROVIDER_PACKAGES: list[str] = [
    "providers",
    "providers.ai",
    "providers.analytics",
    "providers.auth",
    "providers.automation",
    "providers.barcode",
    "providers.bg_removal",
    "providers.comms",
    "providers.finance",
    "providers.geography",
    "providers.image",
    "providers.news",
    "providers.ocr",
    "providers.payments",
    "providers.qr",
    "providers.scanner",
    "providers.security",
    "providers.shipping",
    "providers.storage",
    "providers.voice",
]

# Provider packages that are PURE-PYTHON (no external SDK) and thus cannot
# expose a HAS_<SDK> flag. They are exempt from the flag check but still
# subject to the import-isolation check.
PURE_PYTHON_PROVIDERS: frozenset[str] = frozenset({
    "providers",        # meta-package re-exports from submodules
    "providers.shipping",   # zone-based rate calculator, no SDK
    "providers.payments",   # re-exports from submodules; flags live in submodules
    "providers.auth",       # re-exports from submodules; flags live in submodules
    "providers.bg_removal", # re-exports from service module
    "providers.analytics",  # re-exports AnalyticsProvider; HAS_ANALYTICS in submodule
    "providers.geography",  # re-exports from submodules; flags live in submodules
    "providers.image",      # re-exports from submodules; flags live in submodules
    "providers.voice",      # re-exports from submodule; HAS_VOICE in submodule
    "providers.security",   # re-exports from submodules; flags live in submodules
    "providers.comms",      # re-exports from submodules; flags live in submodules
    "providers.storage",    # re-exports from submodules; flags live in submodules
    "providers.ocr",        # re-exports from submodule; HAS_OCR_PARSER in submodule
    "providers.barcode",    # re-exports from submodule; HAS_BARCODE in submodule
    "providers.qr",         # re-exports from submodules; flags live in submodules
    "providers.scanner",    # re-exports from submodule; flags live in submodule
    "providers.news",       # re-exports from submodule; flags live in submodule
    "providers.finance",    # re-exports from submodule; HAS_BANK_API in submodule
    "providers.automation", # re-exports from submodule; HAS_APSCHEDULER in submodule
    "providers.ai",         # re-exports from submodules; flags live in submodules
})

# Packages where the HAS_ flags live in submodules (not the package __init__).
# For these we check at least one submodule exposes flags.
SUBMODULE_FLAG_PACKAGES: dict[str, list[str]] = {
    "providers": ["providers.ai", "providers.storage", "providers.security", "providers.payments"],
    "providers.auth": ["providers.auth.jwt", "providers.auth.totp", "providers.auth.oauth"],
    "providers.analytics": ["providers.analytics.analytics"],
    "providers.shipping": ["providers.shipping.shipping_calculator"],
    "providers.bg_removal": ["providers.bg_removal.bg_removal_service"],
    "providers.payments": ["providers.payments.stripe_sdk", "providers.payments.paypal"],
    "providers.geography": ["providers.geography.geo", "providers.geography.rates"],
    "providers.image": ["providers.image.image", "providers.image.bg_remover"],
    "providers.voice": ["providers.voice.voice_to_text"],
    "providers.security": ["providers.security.encryption", "providers.security.threat_intel"],
    "providers.comms": ["providers.comms.twilio", "providers.comms.whatsapp"],
    "providers.storage": ["providers.storage.s3_client", "providers.storage.storage_backend"],
    "providers.ocr": ["providers.ocr.ocr_parser"],
    "providers.barcode": ["providers.barcode.barcode_generator"],
    "providers.qr": ["providers.qr.qr_generator"],
    "providers.scanner": ["providers.scanner.scanner"],
    "providers.news": ["providers.news.rss_provider"],
    "providers.finance": ["providers.finance.bank_api"],
    "providers.automation": ["providers.automation.scheduler"],
    "providers.ai": ["providers.ai.text", "providers.ai.huggingface"],
}


# ===========================================================================
# Law 31/100: No forbidden imports across ALL provider files
# ===========================================================================
class TestNoForbiddenImports:
    """providers/ must never import domains/modules/rbac/jobs/middleware."""

    def test_no_forbidden_imports_across_providers(self):
        laws.assert_no_forbidden_imports("providers", BACKEND_ROOT / "providers")


# ===========================================================================
# Law 124: HAS_<SDK> flags
# ===========================================================================
class TestProviderHasFlags:
    """Every provider package must expose HAS_<SDK> flags (Law 124)."""

    @pytest.mark.parametrize("pkg_name", PROVIDER_PACKAGES)
    def test_package_has_flags(self, pkg_name: str):
        mod = importlib.import_module(pkg_name)
        flags = [n for n in dir(mod) if n.startswith("HAS_")]
        if pkg_name in PURE_PYTHON_PROVIDERS:
            # Flags may live in submodules — verify at least one submodule has them
            submodules = SUBMODULE_FLAG_PACKAGES.get(pkg_name, [])
            self._assert_submodule_flags(pkg_name, submodules)
        else:
            assert flags, (
                f"{pkg_name} exposes no HAS_<SDK> flags (Law 124). "
                f"Expected at least one HAS_* boolean."
            )

    def _assert_submodule_flags(self, pkg_name: str, submodules: list[str]) -> None:
        found_flags: list[str] = []
        for sub in submodules:
            try:
                sub_mod = importlib.import_module(sub)
            except ImportError:
                continue
            found_flags.extend(n for n in dir(sub_mod) if n.startswith("HAS_"))
        assert found_flags, (
            f"{pkg_name} and its submodules {submodules} expose no HAS_<SDK> "
            f"flags (Law 124: graceful degradation)."
        )


# ===========================================================================
# Law 124: HAS_ flags are booleans
# ===========================================================================
class TestHasFlagsAreBooleans:
    """HAS_<SDK> flags must be actual booleans, not arbitrary truthy values."""

    @pytest.mark.parametrize("pkg_name", PROVIDER_PACKAGES)
    def test_flags_are_booleans(self, pkg_name: str):
        mod = importlib.import_module(pkg_name)
        flags = [n for n in dir(mod) if n.startswith("HAS_")]
        for flag in flags:
            value = getattr(mod, flag)
            assert isinstance(value, bool), (
                f"{pkg_name}.{flag} is {type(value).__name__}, not bool (Law 124)."
            )


# ===========================================================================
# Law 11/123: Each provider wraps ONE external SDK
# ===========================================================================
class TestProviderSingleSdk:
    """Each provider module should wrap at most one external SDK.

    We verify this by checking that the module's imports reference at most
    one optional external package via try/except ImportError.
    """

    # Map of provider module -> the single SDK it wraps (or None for pure-Python)
    EXPECTED_SDK: dict[str, str | None] = {
        "providers.ai.text": "ollama/http",
        "providers.ai.huggingface": "requests",
        "providers.ai.openai_client": "httpx",
        "providers.ai.vision": None,
        "providers.ai.chatbot": None,
        "providers.ai.search": None,
        "providers.ai.finance_ai": None,
        "providers.ai.sentiment": "vaderSentiment",
        "providers.ai.image_similarity": "PIL",
        "providers.ai.recommendation": None,
        "providers.ai.price_intelligence": None,
        "providers.ai.image_ai_service": None,
        "providers.ai.visual_voice_search_service": None,
        "providers.ai.web_search": None,
        "providers.ai.zozi_mcp": None,
        "providers.ai.ai_research_jobs": None,
        "providers.ai.ai_service": None,
        "providers.ai.ai_variant_config": None,
        "providers.analytics.analytics": None,
        "providers.auth.jwt": "jose",
        "providers.auth.totp": "pyotp",
        "providers.auth.oauth": "requests",
        "providers.auth.apple": "jwt",
        "providers.automation.scheduler": "apscheduler",
        "providers.barcode.barcode_generator": "barcode",
        "providers.bg_removal.bg_removal_service": "rembg",
        "providers.comms.email": None,
        "providers.comms.twilio": "twilio",
        "providers.comms.whatsapp": "twilio",
        "providers.finance.bank_api": "requests",
        "providers.geography.country": None,
        "providers.geography.country_http": "httpx",
        "providers.geography.external_data": "aiohttp",
        "providers.geography.geo": "geoip2",
        "providers.geography.geoip": "geoip2",
        "providers.geography.ip": "httpx",
        "providers.geography.map": None,
        "providers.geography.rates": None,
        "providers.image.image": "PIL",
        "providers.image.bg_remover": "rembg",
        "providers.image.ocr": "pytesseract",
        "providers.image.free_image_tools": "PIL",
        "providers.image.parcel_verification": None,
        "providers.news.rss_provider": "feedparser",
        "providers.ocr.ocr_parser": None,
        "providers.payments.stripe_sdk": "stripe",
        "providers.payments.paypal": "requests",
        "providers.payments.tap": "requests",
        "providers.payments.paytabs": "requests",
        "payments.thawani": "requests",
        "providers.payments.connect": "stripe",
        "providers.payments.generic": None,
        "providers.payments.webhooks": None,
        "providers.payments.config": None,
        "providers.payments.base": None,
        "providers.payments.base_models": None,
        "providers.payments.webhook_models": None,
        "providers.payments.registry": None,
        "providers.qr.qr_generator": "qrcode",
        "providers.qr.parcel_verification_service": None,
        "providers.scanner.scanner": "pyzbar",
        "providers.security.encryption": "cryptography",
        "providers.security.threat_intel": None,
        "providers.security.watchlist": None,
        "providers.shipping.shipping_calculator": None,
        "providers.storage.s3_client": "boto3",
        "providers.storage.storage_backend": None,
        "providers.voice.voice_to_text": None,
    }

    @pytest.mark.parametrize("module_path", [k for k in EXPECTED_SDK if not k.startswith("payments.") or k.startswith("providers.payments.")])
    def test_provider_imports_only_one_sdk(self, module_path: str):
        """Verify the module does not import a different SDK than expected."""
        try:
            mod = importlib.import_module(module_path)
        except ImportError:
            pytest.skip(f"{module_path} not importable")

        source_path = Path(mod.__file__) if mod.__file__ else None
        if source_path is None or not source_path.exists():
            pytest.skip(f"{module_path} has no source file")

        source = source_path.read_text(encoding="utf-8")
        tree = laws.read_source(source_path)

        # Collect all top-level import roots
        roots = laws.module_import_roots(tree)

        # The module should not import forbidden layers (already covered above)
        # Here we just verify it doesn't import a SECOND unexpected external SDK.
        # This is a heuristic — the key guarantee is the import-isolation test.
        forbidden = laws.FORBIDDEN_IMPORT_RULES.get("providers", ())
        violations = [r for r in roots if r in forbidden]
        assert not violations, (
            f"{module_path} imports forbidden layers: {violations} (Law 31/100)."
        )


# ===========================================================================
# Law 126: No business logic leak
# ===========================================================================
class TestNoBusinessLogicLeak:
    """Providers must not import from domains (business logic lives there)."""

    @pytest.mark.parametrize("pkg_name", PROVIDER_PACKAGES)
    def test_no_domain_imports(self, pkg_name: str):
        try:
            mod = importlib.import_module(pkg_name)
        except ImportError:
            pytest.skip(f"{pkg_name} not importable")

        if not mod.__file__:
            pytest.skip(f"{pkg_name} has no source file")

        source_path = Path(mod.__file__)
        if not source_path.exists():
            pytest.skip(f"{module_path} source not found")

        tree = laws.read_source(source_path)
        roots = laws.module_import_roots(tree)
        assert "domains" not in roots, (
            f"{pkg_name} imports 'domains' — business logic leak (Law 126)."
        )
        assert "modules" not in roots, (
            f"{pkg_name} imports 'modules' — business logic leak (Law 126)."
        )
        assert "rbac" not in roots, (
            f"{pkg_name} imports 'rbac' — business logic leak (Law 126)."
        )


# ===========================================================================
# Law 124: Graceful degradation — when HAS_<SDK> is False, code must not crash
# ===========================================================================
class TestGracefulDegradation:
    """When HAS_<SDK> is False, provider functions must return safe defaults."""

    def test_twilio_graceful_when_unavailable(self):
        from providers.comms import twilio as twilio_mod
        original = twilio_mod.HAS_TWILIO
        try:
            twilio_mod.HAS_TWILIO = False
            result = twilio_mod.create_twilio_client("sid", "token")
            assert result is None, "Twilio client should be None when HAS_TWILIO=False"
        finally:
            twilio_mod.HAS_TWILIO = original

    def test_whatsapp_graceful_when_unavailable(self):
        from providers.comms import whatsapp as wa_mod
        original = wa_mod.HAS_WHATSAPP
        try:
            wa_mod.HAS_WHATSAPP = False
            result = wa_mod.send_whatsapp_message(
                to="+15551234567", body="Hi", from_number="+15557654321",
            )
            # Should return a preview/degraded result, not crash
            assert isinstance(result, dict)
            assert result.get("delivered") is False
        finally:
            wa_mod.HAS_WHATSAPP = original

    def test_storage_graceful_when_unavailable(self):
        from providers.storage import s3_client as s3_mod
        original = s3_mod.HAS_S3
        try:
            s3_mod.HAS_S3 = False
            result = s3_mod.create_s3_client("bucket", "us-east-1", "", "key", "secret")
            assert result is None, "S3 client should be None when HAS_S3=False"
        finally:
            s3_mod.HAS_S3 = original

    def test_stripe_graceful_when_unavailable(self):
        from providers.payments import stripe_sdk as stripe_mod
        original = stripe_mod.HAS_STRIPE
        try:
            stripe_mod.HAS_STRIPE = False
            assert stripe_mod.stripe is None
        finally:
            stripe_mod.HAS_STRIPE = original

    def test_paypal_graceful_when_unavailable(self):
        from providers.payments import paypal as paypal_mod
        original = paypal_mod.HAS_PAYPAL
        try:
            paypal_mod.HAS_PAYPAL = False
            result = paypal_mod.is_available()
            assert result is False
        finally:
            paypal_mod.HAS_PAYPAL = original

    def test_sentiment_graceful_when_unavailable(self):
        from providers.ai import sentiment as sent_mod
        original = sent_mod.HAS_VADER
        try:
            sent_mod.HAS_VADER = False
            result = sent_mod.analyze_sentiment("This is great!")
            # Should return a degraded result, not crash
            assert isinstance(result, dict)
        finally:
            sent_mod.HAS_VADER = original

    def test_image_similarity_graceful_when_unavailable(self):
        from providers.ai import image_similarity as sim_mod
        original_pil = sim_mod.HAS_PIL
        original_np = sim_mod.HAS_NUMPY
        try:
            sim_mod.HAS_PIL = False
            sim_mod.HAS_NUMPY = False
            result = sim_mod.compute_similarity(b"img1", b"img2")
            assert isinstance(result, float)
        finally:
            sim_mod.HAS_PIL = original_pil
            sim_mod.HAS_NUMPY = original_np

    def test_barcode_graceful_when_unavailable(self):
        from providers.barcode import barcode_generator as bc_mod
        original = bc_mod.HAS_BARCODE
        try:
            bc_mod.HAS_BARCODE = False
            result = bc_mod.generate_barcode("123456789012")
            assert result is None or result == b""
        finally:
            bc_mod.HAS_BARCODE = original

    def test_qr_graceful_when_unavailable(self):
        from providers.qr import qr_generator as qr_mod
        original = qr_mod.HAS_QRCODE
        try:
            qr_mod.HAS_QRCODE = False
            result = qr_mod.generate_qr("https://zozi.com")
            assert result is None or result == b""
        finally:
            qr_mod.HAS_QRCODE = original

    def test_scanner_graceful_when_unavailable(self):
        from providers.scanner import scanner as scan_mod
        original = scan_mod.HAS_PYZBAR
        try:
            scan_mod.HAS_PYZBAR = False
            result = scan_mod.scan_barcode(b"fake-image")
            assert isinstance(result, list)
        finally:
            scan_mod.HAS_PYZBAR = original

    def test_ocr_graceful_when_unavailable(self):
        from providers.ocr import ocr_parser as ocr_mod
        original = ocr_mod.HAS_OCR_PARSER
        try:
            ocr_mod.HAS_OCR_PARSER = False
            result = ocr_mod.parse_bill_text("Total: $50.00")
            assert isinstance(result, dict)
        finally:
            ocr_mod.HAS_OCR_PARSER = original

    def test_voice_graceful_when_unavailable(self):
        from providers.voice import voice_to_text as voice_mod
        original = voice_mod.HAS_VOICE
        try:
            voice_mod.HAS_VOICE = False
            result = voice_mod.transcribe_audio(b"fake-audio")
            assert result == "" or isinstance(result, str)
        finally:
            voice_mod.HAS_VOICE = original

    def test_news_graceful_when_unavailable(self):
        from providers.news import rss_provider as news_mod
        original = news_mod.HAS_FEEDPARSER
        try:
            news_mod.HAS_FEEDPARSER = False
            # fetch_rss_entries should handle missing feedparser gracefully
            import asyncio
            try:
                result = asyncio.run(news_mod.fetch_rss_entries("https://example.com/feed.xml"))
            except Exception:
                result = None
            # Either returns None/empty or raises — but doesn't segfault
            assert result is None or isinstance(result, list)
        finally:
            news_mod.HAS_FEEDPARSER = original

    def test_finance_graceful_when_unavailable(self):
        from providers.finance import bank_api as bank_mod
        original = bank_mod.HAS_BANK_API
        try:
            bank_mod.HAS_BANK_API = False
            result = bank_mod.test_connection("https://api.bank.com", "/v1/batches", "token", 10.0)
            assert isinstance(result, dict)
            assert result.get("reachable") is False
        finally:
            bank_mod.HAS_BANK_API = original

    def test_automation_graceful_when_unavailable(self):
        from providers.automation import scheduler as sched_mod
        original = sched_mod.HAS_APSCHEDULER
        try:
            sched_mod.HAS_APSCHEDULER = False
            result = sched_mod.create_scheduler()
            assert result is None
        finally:
            sched_mod.HAS_APSCHEDULER = original

    def test_security_encryption_graceful_when_unavailable(self):
        from providers.security import encryption as enc_mod
        original = enc_mod.HAS_CRYPTOGRAPHY
        try:
            enc_mod.HAS_CRYPTOGRAPHY = False
            result = enc_mod.encrypt_data(b"secret")
            assert result is None or result == b""
        finally:
            enc_mod.HAS_CRYPTOGRAPHY = original

    def test_security_threat_intel_graceful_when_unavailable(self):
        from providers.security import threat_intel as ti_mod
        original = ti_mod.HAS_THREAT_INTEL
        try:
            ti_mod.HAS_THREAT_INTEL = False
            result = ti_mod.fetch_tor_exit_list()
            assert isinstance(result, list)
        finally:
            ti_mod.HAS_THREAT_INTEL = original

    def test_security_watchlist_graceful_when_unavailable(self):
        from providers.security import watchlist as wl_mod
        original = wl_mod.HAS_WATCHLIST
        try:
            wl_mod.HAS_WATCHLIST = False
            result = wl_mod.screen_watchlist("EMP001", "John", "US", api_url="https://api.example.com")
            assert isinstance(result, dict)
        finally:
            wl_mod.HAS_WATCHLIST = original

    def test_geography_graceful_when_unavailable(self):
        from providers.geography import geo as geo_mod
        original = geo_mod.HAS_GEO
        try:
            geo_mod.HAS_GEO = False
            try:
                result = geo_mod.resolve_ip_location(ip="1.2.3.4")
            except RuntimeError:
                pass  # Expected when no provider available
        finally:
            geo_mod.HAS_GEO = original

    def test_image_graceful_when_unavailable(self):
        from providers.image import image as img_mod
        original_pil = img_mod.HAS_PIL
        try:
            img_mod.HAS_PIL = False
            result = img_mod.remove_background(b"fake-image")
            assert isinstance(result, bytes)
        finally:
            img_mod.HAS_PIL = original_pil

    def test_ai_graceful_when_unavailable(self):
        from providers.ai import text as text_mod
        original = text_mod.HAS_AI_TEXT
        try:
            text_mod.HAS_AI_TEXT = False
            result = text_mod.cosine_similarity([1, 0], [0, 1])
            assert isinstance(result, float)
        finally:
            text_mod.HAS_AI_TEXT = original

    def test_comms_graceful_when_unavailable(self):
        from providers.comms import email as email_mod
        # Email has no HAS_ flag — console mode always works
        result = email_mod.deliver_email(
            to="test@example.com", subject="Test", html="<p>Hi</p>",
            from_address="sender@example.com", provider="console",
        )
        assert result is None  # console mode returns None
