"""Test suite for the backend/providers/media subpackage.

Tests public functions, classes, and constants across the current media
provider modules:
- __init__.py
- ai/ (ai_research_jobs, ai_variant_config, free_image_tools,
       image_ai_service, visual_voice_search_service)
- bg_removal/ (bg_removal_service)
- ocr/ocr_parser.py
- qr/parcel_verification_service.py
- storage/storage.py

Some modules have known import/syntax issues and are marked with @pytest.mark.skip.
Those tests are retained so they can be un-skipped once the underlying files
are repaired.

Run with: pytest tests/providers/test_media_providers.py -v
"""

import io
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import numpy as np
import pytest

from PIL import Image

from backend.providers.image import HAS_CV2, HAS_GUIDED_FILTER, cv2, ximgproc


# ─────────────────────────────────────────────────────────────────────────────
# Module-level import tests
# ─────────────────────────────────────────────────────────────────────────────

class TestMediaInit:
    """Verify media package exports."""

    def test_has_cv2_export(self):
        assert isinstance(HAS_CV2, bool)

    def test_has_guided_filter_export(self):
        assert isinstance(HAS_GUIDED_FILTER, bool)

    def test_cv2_export(self):
        assert cv2 is None or hasattr(cv2, 'imread')

    def test_ximgproc_export(self):
        assert ximgproc is None or hasattr(ximgproc, 'guidedFilter')

    def test_all_exports(self):
        from backend.providers.image import __all__
        assert "cv2" in __all__
        assert "ximgproc" in __all__
        assert "HAS_CV2" in __all__
        assert "HAS_GUIDED_FILTER" in __all__


# ─────────────────────────────────────────────────────────────────────────────
# AI Variant Config tests (ai_variant_config.py)
# ─────────────────────────────────────────────────────────────────────────────

class TestNormalizeCategory:
    """Tests for normalize_category function."""

    def test_empty_returns_other(self):
        from backend.providers.ai.ai_variant_config import normalize_category
        assert normalize_category("") == "Other"

    def test_none_returns_other(self):
        from backend.providers.ai.ai_variant_config import normalize_category
        assert normalize_category(None) == "Other"

    def test_general_returns_other(self):
        from backend.providers.ai.ai_variant_config import normalize_category
        assert normalize_category("general") == "Other"

    def test_service_returns_other(self):
        from backend.providers.ai.ai_variant_config import normalize_category
        assert normalize_category("service") == "Other"

    def test_canonical_exact_match(self):
        from backend.providers.ai.ai_variant_config import normalize_category
        assert normalize_category("Electronics") == "Electronics"

    def test_canonical_case_insensitive(self):
        from backend.providers.ai.ai_variant_config import normalize_category
        assert normalize_category("electronics") == "Electronics"

    def test_alias_clothing(self):
        from backend.providers.ai.ai_variant_config import normalize_category
        assert normalize_category("shirt") == "Clothing"

    def test_alias_beauty(self):
        from backend.providers.ai.ai_variant_config import normalize_category
        assert normalize_category("makeup") == "Beauty & Personal Care"

    def test_alias_home(self):
        from backend.providers.ai.ai_variant_config import normalize_category
        assert normalize_category("furniture") == "Home & Garden"

    def test_alias_sports(self):
        from backend.providers.ai.ai_variant_config import normalize_category
        assert normalize_category("fitness") == "Sports & Outdoors"

    def test_alias_books(self):
        from backend.providers.ai.ai_variant_config import normalize_category
        assert normalize_category("novel") == "Books"

    def test_alias_toys(self):
        from backend.providers.ai.ai_variant_config import normalize_category
        assert normalize_category("puzzle") == "Toys & Games"

    def test_alias_automotive(self):
        from backend.providers.ai.ai_variant_config import normalize_category
        assert normalize_category("car") == "Automotive"

    def test_alias_health(self):
        from backend.providers.ai.ai_variant_config import normalize_category
        assert normalize_category("vitamin") == "Health & Household"

    def test_alias_industrial(self):
        from backend.providers.ai.ai_variant_config import normalize_category
        assert normalize_category("machinery") == "Industrial & Scientific"

    def test_unknown_returns_other(self):
        from backend.providers.ai.ai_variant_config import normalize_category
        assert normalize_category("xyzqwerty") == "Other"


class TestSuggestPrice:
    """Tests for suggest_price function."""

    def test_electronic_price(self):
        from backend.providers.ai.ai_variant_config import suggest_price
        result = suggest_price("electronic", "Laptop")
        assert "ai_suggested_price" in result
        assert "price_min" in result
        assert "price_max" in result
        assert result["ai_suggested_price"] > 0

    def test_clothing_price(self):
        from backend.providers.ai.ai_variant_config import suggest_price
        result = suggest_price("clothing", "T-Shirt")
        assert result["ai_suggested_price"] > 0

    def test_furniture_price(self):
        from backend.providers.ai.ai_variant_config import suggest_price
        result = suggest_price("furniture", "Sofa")
        assert result["ai_suggested_price"] > 0

    def test_general_fallback(self):
        from backend.providers.ai.ai_variant_config import suggest_price
        result = suggest_price("unknown", "Item")
        assert result["ai_suggested_price"] > 0

    def test_price_range_ordering(self):
        from backend.providers.ai.ai_variant_config import suggest_price
        result = suggest_price("electronic", "Phone")
        assert result["price_min"] <= result["ai_suggested_price"] <= result["price_max"]

    def test_deterministic_jitter(self):
        from backend.providers.ai.ai_variant_config import suggest_price
        result1 = suggest_price("electronic", "Same Name")
        result2 = suggest_price("electronic", "Same Name")
        assert result1["ai_suggested_price"] == result2["ai_suggested_price"]

    def test_category_fallback(self):
        from backend.providers.ai.ai_variant_config import suggest_price
        result = suggest_price("", "", "Electronics")
        assert result["ai_suggested_price"] > 0


class TestVariantConfig:
    """Tests for VariantConfig class."""

    def test_default_init(self):
        from backend.providers.ai.ai_variant_config import VariantConfig
        config = VariantConfig()
        assert config.config is not None

    def test_custom_config(self):
        from backend.providers.ai.ai_variant_config import VariantConfig
        custom = {"variants": {"color": {"name": "Color"}}}
        config = VariantConfig(custom)
        assert config.config == custom

    def test_get_variants(self):
        from backend.providers.ai.ai_variant_config import VariantConfig
        config = VariantConfig({"variants": {"color": {}, "size": {}}})
        variants = config.get_variants()
        assert "color" in variants
        assert "size" in variants

    def test_get_product_type_keywords(self):
        from backend.providers.ai.ai_variant_config import VariantConfig
        config = VariantConfig({"product_type_keywords": {"clothing": ["shirt", "dress"]}})
        keywords = config.get_product_type_keywords()
        assert "clothing" in keywords
        assert "shirt" in keywords["clothing"]

    def test_get_product_type_keywords_adds_lingerie(self):
        from backend.providers.ai.ai_variant_config import VariantConfig
        config = VariantConfig({"product_type_keywords": {"clothing": ["shirt"]}})
        keywords = config.get_product_type_keywords()
        assert "lingerie" in keywords["clothing"]
        assert "bra" in keywords["clothing"]

    def test_get_category_fallbacks(self):
        from backend.providers.ai.ai_variant_config import VariantConfig
        config = VariantConfig({"category_fallbacks": {"apparel_keywords": ["dress"]}})
        fallbacks = config.get_category_fallbacks()
        assert "apparel_keywords" in fallbacks

    def test_get_ai_rules(self):
        from backend.providers.ai.ai_variant_config import VariantConfig
        config = VariantConfig({"ai_rules": {"liquid_rules": {"exclude": ["weight"]}}})
        rules = config.get_ai_rules()
        assert "liquid_rules" in rules

    def test_get_rules_for_product_type(self):
        from backend.providers.ai.ai_variant_config import VariantConfig
        config = VariantConfig({"ai_rules": {"liquid_rules": {"exclude": ["weight"]}}})
        rules = config.get_rules_for_product_type("liquid")
        assert "exclude" in rules

    def test_get_variant_info(self):
        from backend.providers.ai.ai_variant_config import VariantConfig
        config = VariantConfig({"variants": {"color": {"name": "Color", "type": "select"}}})
        info = config.get_variant_info("color")
        assert info["name"] == "Color"

    def test_get_mutually_exclusive(self):
        from backend.providers.ai.ai_variant_config import VariantConfig
        config = VariantConfig({"variants": {"color": {"mutually_exclusive_with": ["pattern"]}}})
        exclusive = config.get_mutually_exclusive("color")
        assert "pattern" in exclusive

    def test_classify_product_type_clothing(self):
        from backend.providers.ai.ai_variant_config import VariantConfig
        config = VariantConfig({"product_type_keywords": {"clothing": ["shirt", "dress"]}})
        result = config.classify_product_type("Cotton Shirt", "Fashion", "Tops")
        assert result == "clothing"

    def test_classify_product_type_electronic(self):
        from backend.providers.ai.ai_variant_config import VariantConfig
        config = VariantConfig({"product_type_keywords": {"electronic": ["phone", "laptop"]}})
        result = config.classify_product_type("iPhone", "Tech", "Phone")
        assert result == "electronic"

    def test_classify_product_type_general_fallback(self):
        from backend.providers.ai.ai_variant_config import VariantConfig
        config = VariantConfig({"product_type_keywords": {}})
        result = config.classify_product_type("Unknown", "Misc", "Other")
        assert result == "general"

    def test_get_allowed_variants(self):
        from backend.providers.ai.ai_variant_config import VariantConfig
        config = VariantConfig({
            "variants": {
                "color": {"categories": ["clothing", "fashion"]},
                "size": {"categories": ["clothing"]},
            }
        })
        result = config.get_allowed_variants("Clothing", "")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_allowed_variants_other_default(self):
        from backend.providers.ai.ai_variant_config import VariantConfig
        config = VariantConfig({"variants": {}})
        result = config.get_allowed_variants("Other", "")
        assert "color" in result
        assert "size" in result
        assert "material" in result

    def test_extract_variant_options(self):
        from backend.providers.ai.ai_variant_config import VariantConfig
        config = VariantConfig({
            "variants": {
                "color": {"prompt": "Choose color (Red, Blue, Green)"}
            }
        })
        result = config.extract_variant_options("color")
        assert "Red" in result
        assert "Blue" in result
        assert "Green" in result


class TestIsJunkFilename:
    """Tests for _is_junk_filename function."""

    def test_img_pattern(self):
        from backend.providers.ai.ai_variant_config import _is_junk_filename
        assert _is_junk_filename("IMG_1234.jpg") is True

    def test_dsc_pattern(self):
        from backend.providers.ai.ai_variant_config import _is_junk_filename
        assert _is_junk_filename("DSC_001.jpg") is True

    def test_whatsapp_pattern(self):
        from backend.providers.ai.ai_variant_config import _is_junk_filename
        assert _is_junk_filename("WhatsApp Image 2024.jpg") is True

    def test_screenshot_pattern(self):
        from backend.providers.ai.ai_variant_config import _is_junk_filename
        assert _is_junk_filename("Screenshot 2024.png") is True

    def test_pure_numeric(self):
        from backend.providers.ai.ai_variant_config import _is_junk_filename
        assert _is_junk_filename("12345.jpg") is True

    def test_short_name(self):
        from backend.providers.ai.ai_variant_config import _is_junk_filename
        assert _is_junk_filename("a.jpg") is True

    def test_valid_product_name(self):
        from backend.providers.ai.ai_variant_config import _is_junk_filename
        assert _is_junk_filename("red_leather_shoes.jpg") is False

    def test_valid_descriptive_name(self):
        from backend.providers.ai.ai_variant_config import _is_junk_filename
        assert _is_junk_filename("blue_cotton_tshirt.png") is False


class TestExtractJson:
    """Tests for _extract_json function."""

    def test_valid_json(self):
        from backend.providers.ai.ai_variant_config import _extract_json
        result = _extract_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_with_surrounding_text(self):
        from backend.providers.ai.ai_variant_config import _extract_json
        result = _extract_json('Here is the result: {"status": "ok"} Done')
        assert result == {"status": "ok"}

    def test_json_with_markdown_fences(self):
        from backend.providers.ai.ai_variant_config import _extract_json
        result = _extract_json('```json\n{"key": "val"}\n```')
        assert result == {"key": "val"}

    def test_empty_string(self):
        from backend.providers.ai.ai_variant_config import _extract_json
        assert _extract_json("") is None

    def test_no_json(self):
        from backend.providers.ai.ai_variant_config import _extract_json
        assert _extract_json("no json here") is None

    def test_single_quotes_fixed(self):
        from backend.providers.ai.ai_variant_config import _extract_json
        result = _extract_json("{'key': 'value'}")
        assert result == {"key": "value"}

    def test_trailing_comma_fixed(self):
        from backend.providers.ai.ai_variant_config import _extract_json
        result = _extract_json('{"a": 1, "b": 2,}')
        assert result == {"a": 1, "b": 2}

    def test_none_replaced(self):
        from backend.providers.ai.ai_variant_config import _extract_json
        result = _extract_json('{"value": None}')
        assert result == {"value": None}


# ─────────────────────────────────────────────────────────────────────────────
# AI Research Jobs tests (ai_research_jobs.py)
# ─────────────────────────────────────────────────────────────────────────────

class TestAIResearchJobs:
    """Tests for ai_research_jobs module."""

    def test_enqueue_job(self):
        from backend.providers.ai.ai_research_jobs import enqueue_job, _in_memory_store
        _in_memory_store.clear()
        result = enqueue_job("US", {"key": "value"})
        assert "job_id" in result
        assert result["country_code"] == "US"
        assert result["status"] == "queued"
        assert "created_at_utc" in result

    def test_get_job(self):
        from backend.providers.ai.ai_research_jobs import enqueue_job, get_job, _in_memory_store
        _in_memory_store.clear()
        job = enqueue_job("US", {})
        fetched = get_job(job["job_id"])
        assert fetched is not None
        assert fetched["job_id"] == job["job_id"]

    def test_get_job_unknown(self):
        from backend.providers.ai.ai_research_jobs import get_job
        assert get_job("nonexistent") is None

    def test_mark_job_running(self):
        from backend.providers.ai.ai_research_jobs import enqueue_job, mark_job_running, get_job, _in_memory_store
        _in_memory_store.clear()
        job = enqueue_job("US", {})
        result = mark_job_running(job["job_id"])
        assert result is True
        assert get_job(job["job_id"])["status"] == "running"

    def test_mark_job_running_unknown(self):
        from backend.providers.ai.ai_research_jobs import mark_job_running
        assert mark_job_running("nonexistent") is False

    def test_mark_job_completed(self):
        from backend.providers.ai.ai_research_jobs import enqueue_job, mark_job_completed, get_job, get_completed_result, _in_memory_store
        _in_memory_store.clear()
        job = enqueue_job("US", {})
        result_data = {"key": "value"}
        result = mark_job_completed(job["job_id"], result_data)
        assert result is True
        assert get_job(job["job_id"])["status"] == "completed"
        assert get_completed_result(job["job_id"]) == result_data

    def test_mark_job_completed_unknown(self):
        from backend.providers.ai.ai_research_jobs import mark_job_completed
        assert mark_job_completed("nonexistent", {}) is False

    def test_mark_job_failed(self):
        from backend.providers.ai.ai_research_jobs import enqueue_job, mark_job_failed, get_job, _in_memory_store
        _in_memory_store.clear()
        job = enqueue_job("US", {})
        result = mark_job_failed(job["job_id"], "error message")
        assert result is True
        fetched = get_job(job["job_id"])
        assert fetched["status"] == "failed"
        assert fetched["error"] == "error message"

    def test_mark_job_failed_unknown(self):
        from backend.providers.ai.ai_research_jobs import mark_job_failed
        assert mark_job_failed("nonexistent", "error") is False

    def test_get_completed_result_not_completed(self):
        from backend.providers.ai.ai_research_jobs import enqueue_job, get_completed_result, _in_memory_store
        _in_memory_store.clear()
        job = enqueue_job("US", {})
        assert get_completed_result(job["job_id"]) is None

    def test_get_completed_result_unknown(self):
        from backend.providers.ai.ai_research_jobs import get_completed_result
        assert get_completed_result("nonexistent") is None

    def test_count_running_jobs(self):
        from backend.providers.ai.ai_research_jobs import count_running_jobs, increment_running_jobs, decrement_running_jobs
        import backend.providers.ai.ai_research_jobs as mod
        mod._running_jobs_counter = 0
        assert count_running_jobs() == 0
        increment_running_jobs()
        assert count_running_jobs() == 1
        decrement_running_jobs()
        assert count_running_jobs() == 0

    def test_decrement_not_below_zero(self):
        from backend.providers.ai.ai_research_jobs import decrement_running_jobs, count_running_jobs
        import backend.providers.ai.ai_research_jobs as mod
        mod._running_jobs_counter = 0
        decrement_running_jobs()
        assert count_running_jobs() == 0

    def test_country_code_uppercased(self):
        from backend.providers.ai.ai_research_jobs import enqueue_job, _in_memory_store
        _in_memory_store.clear()
        job = enqueue_job("us", {})
        assert job["country_code"] == "US"


# ─────────────────────────────────────────────────────────────────────────────
# OCR Parser tests (ocr_parser.py)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.skip(reason="ocr_parser.py has syntax error (IndentationError on import)")
class TestParseBillText:
    """Tests for parse_bill_text function."""

    def test_empty_text(self):
        from backend.providers.ocr.ocr_parser import parse_bill_text
        result = parse_bill_text("")
        assert result["vendor_name"] is None
        assert result["amount"] is None
        assert result["confidence"] == 0.0

    def test_empty_text_with_filename(self):
        from backend.providers.ocr.ocr_parser import parse_bill_text
        result = parse_bill_text("", filename="invoice_12345.pdf")
        assert result["invoice_number"] == "12345"
        assert result["confidence"] == 0.15

    def test_vendor_extraction(self):
        from backend.providers.ocr.ocr_parser import parse_bill_text
        text = "ACME Supplies Ltd\nTotal: $49.99\nDate: 2024-01-15"
        result = parse_bill_text(text)
        assert result["vendor_name"] is not None
        assert "ACME" in result["vendor_name"]

    def test_amount_extraction(self):
        from backend.providers.ocr.ocr_parser import parse_bill_text
        text = "Coffee Shop\nTotal: $25.50\nThank you!"
        result = parse_bill_text(text)
        assert result["amount"] is not None
        assert float(result["amount"]) == 25.50

    def test_vat_extraction(self):
        from backend.providers.ocr.ocr_parser import parse_bill_text
        text = "Store Name\nAmount: $100\nVAT: $5\nTotal: $105"
        result = parse_bill_text(text)
        assert result["tax_amount"] is not None

    def test_date_extraction(self):
        from backend.providers.ocr.ocr_parser import parse_bill_text
        text = "Store\nDate: 2024-03-15\nTotal: $50"
        result = parse_bill_text(text)
        assert result["expense_date"] is not None

    def test_invoice_number_extraction(self):
        from backend.providers.ocr.ocr_parser import parse_bill_text
        text = "Store\nInvoice# INV-2024-001\nTotal: $75"
        result = parse_bill_text(text)
        assert result["invoice_number"] is not None

    def test_confidence_calculation(self):
        from backend.providers.ocr.ocr_parser import parse_bill_text
        text = "ACME Corp\nTotal: $100\nVAT: $5\nDate: 2024-01-15\nInvoice# INV-001"
        result = parse_bill_text(text)
        assert result["confidence"] > 0.5

    def test_raw_text_preserved(self):
        from backend.providers.ocr.ocr_parser import parse_bill_text
        text = "Test receipt text"
        result = parse_bill_text(text)
        assert result["raw_text"] == text

    def test_year_like_amounts_excluded(self):
        from backend.providers.ocr.ocr_parser import parse_bill_text
        text = "Store\nAmount: $50\nYear: 2024"
        result = parse_bill_text(text)
        assert float(result["amount"]) == 50.0

    def test_labelled_amount_preferred(self):
        from backend.providers.ocr.ocr_parser import parse_bill_text
        text = "Store\nSubtotal: $30\nTotal: $50\nTax: $5"
        result = parse_bill_text(text)
        assert float(result["amount"]) == 50.0


@pytest.mark.skip(reason="ocr_parser.py has syntax error (IndentationError on import)")
class TestParseStatementCSV:
    """Tests for parse_statement_csv function."""

    def test_empty_csv(self):
        from backend.providers.ocr.ocr_parser import parse_statement_csv
        assert parse_statement_csv("") == []

    def test_csv_with_header(self):
        from backend.providers.ocr.ocr_parser import parse_statement_csv
        csv_text = "Date,Description,Amount\n2024-01-15,Coffee Shop,25.50\n2024-01-16,Gas Station,45.00"
        result = parse_statement_csv(csv_text)
        assert len(result) == 2
        assert result[0]["description"] == "Coffee Shop"
        assert result[0]["amount"] == 25.50

    def test_csv_without_header(self):
        from backend.providers.ocr.ocr_parser import parse_statement_csv
        csv_text = "2024-01-15,Coffee Shop,25.50\n2024-01-16,Gas Station,45.00"
        result = parse_statement_csv(csv_text)
        assert len(result) >= 1

    def test_csv_with_reference(self):
        from backend.providers.ocr.ocr_parser import parse_statement_csv
        csv_text = "Date,Description,Reference,Amount\n2024-01-15,Shop,REF001,100.00"
        result = parse_statement_csv(csv_text)
        assert len(result) == 1
        assert result[0]["reference"] == "REF001"

    def test_csv_skips_empty_rows(self):
        from backend.providers.ocr.ocr_parser import parse_statement_csv
        csv_text = "Date,Description,Amount\n2024-01-15,Shop,25.50\n\n2024-01-16,Other,10.00"
        result = parse_statement_csv(csv_text)
        assert len(result) == 2

    def test_csv_negative_amount(self):
        from backend.providers.ocr.ocr_parser import parse_statement_csv
        csv_text = "Date,Description,Amount\n2024-01-15,Refund,(50.00)"
        result = parse_statement_csv(csv_text)
        assert len(result) == 1
        assert result[0]["amount"] == -50.0


# ─────────────────────────────────────────────────────────────────────────────
# Parcel Verification Service tests (qr/parcel_verification_service.py)
# ─────────────────────────────────────────────────────────────────────────────

class TestParcelVerificationService:
    """Tests for parcel_verification_service module."""

    def test_verify_parcel_photo_import(self):
        from backend.providers.qr.parcel_verification_service import verify_parcel_photo
        assert callable(verify_parcel_photo)

    def test_verify_parcel_fast_import(self):
        from backend.providers.qr.parcel_verification_service import verify_parcel_fast
        assert callable(verify_parcel_fast)

    @patch("backend.providers.qr.parcel_verification_service._provider_verify_parcel_photo")
    def test_verify_parcel_photo_delegates(self, mock_provider):
        from backend.providers.qr.parcel_verification_service import verify_parcel_photo
        mock_provider.return_value = {"match": True, "score": 0.95}
        result = verify_parcel_photo(
            image_bytes=b"image",
            item_descriptions=["box"],
            run_ssim=True,
        )
        mock_provider.assert_called_once()
        assert result["match"] is True

    @patch("backend.providers.qr.parcel_verification_service._provider_verify_parcel_fast")
    def test_verify_parcel_fast_delegates(self, mock_provider):
        from backend.providers.qr.parcel_verification_service import verify_parcel_fast
        mock_provider.return_value = {"match": True, "score": 0.9}
        result = verify_parcel_fast(
            image_bytes=b"image",
            item_descriptions=["box"],
        )
        mock_provider.assert_called_once()
        assert result["match"] is True


# ─────────────────────────────────────────────────────────────────────────────
# Storage tests (storage.py)
# ─────────────────────────────────────────────────────────────────────────────

class TestLocalStorage:
    """Tests for LocalStorage class."""

    @pytest.fixture
    def tmp_dir(self):
        with tempfile.TemporaryDirectory() as d:
            yield d

    def test_init_creates_directory(self, tmp_dir):
        from providers.storage.storage_backend import LocalStorage
        storage = LocalStorage(base_dir=tmp_dir)
        assert os.path.isdir(tmp_dir)

    def test_save_and_read(self, tmp_dir):
        from providers.storage.storage_backend import LocalStorage
        storage = LocalStorage(base_dir=tmp_dir)
        url = storage.save("test/file.txt", b"hello world")
        assert "/uploads/test/file.txt" in url
        data = storage.read("test/file.txt")
        assert data == b"hello world"

    def test_url_generation(self, tmp_dir):
        from providers.storage.storage_backend import LocalStorage
        storage = LocalStorage(base_dir=tmp_dir)
        url = storage.url("path/to/file.png")
        assert url == "/uploads/path/to/file.png"

    def test_delete(self, tmp_dir):
        from providers.storage.storage_backend import LocalStorage
        storage = LocalStorage(base_dir=tmp_dir)
        storage.save("to_delete.txt", b"data")
        storage.delete("to_delete.txt")
        storage.delete("nonexistent.txt")

    def test_list(self, tmp_dir):
        from providers.storage.storage_backend import LocalStorage
        storage = LocalStorage(base_dir=tmp_dir)
        storage.save("dir/a.txt", b"a")
        storage.save("dir/b.txt", b"b")
        storage.save("other/c.txt", b"c")
        result = storage.list(prefix="dir/")
        assert len(result) == 2

    def test_list_empty_prefix(self, tmp_dir):
        from providers.storage.storage_backend import LocalStorage
        storage = LocalStorage(base_dir=tmp_dir)
        storage.save("a.txt", b"a")
        storage.save("b.txt", b"b")
        result = storage.list()
        assert len(result) == 2

    def test_path_traversal_prevention(self, tmp_dir):
        from providers.storage.storage_backend import LocalStorage
        storage = LocalStorage(base_dir=tmp_dir)
        with pytest.raises(ValueError, match="Unsafe"):
            storage.read("../../etc/passwd")

    def test_save_creates_subdirectories(self, tmp_dir):
        from providers.storage.storage_backend import LocalStorage
        storage = LocalStorage(base_dir=tmp_dir)
        storage.save("a/b/c/file.txt", b"data")
        assert os.path.isfile(os.path.join(tmp_dir, "a", "b", "c", "file.txt"))

    def test_presign_put_returns_none(self, tmp_dir):
        from providers.storage.storage_backend import LocalStorage
        storage = LocalStorage(base_dir=tmp_dir)
        assert storage.presign_put("key") is None


class TestS3Storage:
    """Tests for S3Storage class."""

    @patch("providers.storage.s3_client.create_s3_client")
    def test_init_with_params(self, mock_create):
        from providers.storage.storage_backend import S3Storage
        storage = S3Storage(
            bucket="test-bucket",
            region="us-east-1",
            access_key="key",
            secret_key="secret",
        )
        assert storage.bucket == "test-bucket"
        assert storage.region == "us-east-1"

    @patch("providers.storage.storage_backend.create_s3_client")
    def test_save(self, mock_create):
        from providers.storage.storage_backend import S3Storage
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        storage = S3Storage(
            bucket="test-bucket",
            region="us-east-1",
            access_key="key",
            secret_key="secret",
        )
        storage._client = mock_client
        url = storage.save("key", b"data", content_type="image/png")
        mock_client.put_object.assert_called_once()
        assert "test-bucket" in url

    @patch("providers.storage.storage_backend.create_s3_client")
    def test_read(self, mock_create):
        from providers.storage.storage_backend import S3Storage
        mock_client = MagicMock()
        mock_body = MagicMock()
        mock_body.read.return_value = b"file_data"
        mock_client.get_object.return_value = {"Body": mock_body}
        mock_create.return_value = mock_client
        storage = S3Storage(
            bucket="test-bucket",
            region="us-east-1",
            access_key="key",
            secret_key="secret",
        )
        storage._client = mock_client
        data = storage.read("key")
        assert data == b"file_data"

    @patch("providers.storage.storage_backend.create_s3_client")
    def test_delete(self, mock_create):
        from providers.storage.storage_backend import S3Storage
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        storage = S3Storage(
            bucket="test-bucket",
            region="us-east-1",
            access_key="key",
            secret_key="secret",
        )
        storage._client = mock_client
        storage.delete("key")
        mock_client.delete_object.assert_called_once()

    @patch("providers.storage.storage_backend.create_s3_client")
    def test_url_with_cdn(self, mock_create):
        from providers.storage.storage_backend import S3Storage
        storage = S3Storage(
            bucket="test-bucket",
            region="us-east-1",
            cdn_base="https://cdn.example.com",
            access_key="key",
            secret_key="secret",
        )
        url = storage.url("path/to/file.png")
        assert url == "https://cdn.example.com/path/to/file.png"

    @patch("providers.storage.storage_backend.create_s3_client")
    def test_url_without_cdn(self, mock_create):
        from providers.storage.storage_backend import S3Storage
        storage = S3Storage(
            bucket="test-bucket",
            region="us-east-1",
            access_key="key",
            secret_key="secret",
        )
        url = storage.url("path/to/file.png")
        assert "test-bucket" in url

    @patch("providers.storage.storage_backend.create_s3_client")
    def test_presign_put(self, mock_create):
        from providers.storage.storage_backend import S3Storage
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://presigned.url"
        mock_create.return_value = mock_client
        storage = S3Storage(
            bucket="test-bucket",
            region="us-east-1",
            access_key="key",
            secret_key="secret",
        )
        storage._client = mock_client
        url = storage.presign_put("key", content_type="image/png")
        assert url == "https://presigned.url"

    @patch("providers.storage.storage_backend.create_s3_client")
    def test_presign_put_no_credentials(self, mock_create):
        from providers.storage.storage_backend import S3Storage
        storage = S3Storage(bucket="", region="us-east-1")
        assert storage.presign_put("key") is None


class TestGetStorage:
    """Tests for get_storage function."""

    @patch("providers.storage.storage_backend.os.getenv")
    def test_local_backend(self, mock_getenv):
        from providers.storage.storage_backend import get_storage, LocalStorage
        mock_getenv.return_value = "local"
        result = get_storage()
        assert isinstance(result, LocalStorage)

    @patch("providers.storage.s3_client.create_s3_client")
    @patch("providers.storage.storage_backend.os.getenv")
    def test_s3_backend(self, mock_getenv, mock_create):
        from providers.storage.storage_backend import get_storage, S3Storage
        mock_getenv.side_effect = lambda key, default="": {
            "STORAGE_BACKEND": "s3",
            "S3_BUCKET": "test-bucket",
            "S3_REGION": "us-east-1",
            "S3_ACCESS_KEY_ID": "key",
            "S3_SECRET_ACCESS_KEY": "secret",
        }.get(key, default)
        result = get_storage()
        assert isinstance(result, S3Storage)


# ─────────────────────────────────────────────────────────────────────────────
# Free Image Tests (ai/free_image_tools.py)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.skip(reason="free_image_tools.py has syntax error (malformed import)")
class TestFreeImageTools:
    """Tests for free_image_tools module."""

    @pytest.fixture
    def sample_image(self):
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def test_auto_process_image_default(self, sample_image):
        from backend.providers.image.free_image_tools import auto_process_image
        result = auto_process_image(sample_image)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_auto_process_image_empty_tools(self, sample_image):
        from backend.providers.image.free_image_tools import auto_process_image
        result = auto_process_image(sample_image, tools=[])
        assert result == sample_image

    def test_auto_process_image_unknown_tool_ignored(self, sample_image):
        from backend.providers.image.free_image_tools import auto_process_image
        result = auto_process_image(sample_image, tools=["nonexistent_tool"])
        assert result == sample_image

    def test_tool_registry_has_all_tools(self):
        from backend.providers.image.free_image_tools import TOOL_REGISTRY
        expected_tools = [
            "magic_erase", "smart_crop", "rotate", "auto_light", "upscale",
            "white_balance", "denoise", "sharpen", "compress", "webp_convert",
            "color_enhance", "auto_levels",
        ]
        for tool in expected_tools:
            assert tool in TOOL_REGISTRY
            assert callable(TOOL_REGISTRY[tool])

    def test_auto_rotate_no_exif(self, sample_image):
        from backend.providers.image.free_image_tools import auto_rotate
        result = auto_rotate(sample_image)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_auto_rotate_with_angle(self, sample_image):
        from backend.providers.image.free_image_tools import auto_rotate
        result = auto_rotate(sample_image, angle=90)
        assert isinstance(result, bytes)

    def test_sharpen(self, sample_image):
        from backend.providers.image.free_image_tools import sharpen
        result = sharpen(sample_image, strength=1.0)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_compress(self, sample_image):
        from backend.providers.image.free_image_tools import compress
        result = compress(sample_image, quality=80)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_webp_convert(self, sample_image):
        from backend.providers.image.free_image_tools import webp_convert
        result = webp_convert(sample_image, quality=85)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_webp_convert_lossless(self, sample_image):
        from backend.providers.image.free_image_tools import webp_convert
        result = webp_convert(sample_image, quality=85, lossless=True)
        assert isinstance(result, bytes)

    def test_color_enhance(self, sample_image):
        from backend.providers.image.free_image_tools import color_enhance
        result = color_enhance(sample_image, saturation=1.15)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_auto_levels(self, sample_image):
        from backend.providers.image.free_image_tools import auto_levels
        result = auto_levels(sample_image, clip_hist=0.5)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_upscale_lanczos(self, sample_image):
        from backend.providers.image.free_image_tools import upscale
        result = upscale(sample_image, scale=1.5, method="lanczos")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_smart_crop(self, sample_image):
        from backend.providers.image.free_image_tools import smart_crop
        result = smart_crop(sample_image, target_ratio=1.0)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_auto_white_balance(self, sample_image):
        from backend.providers.image.free_image_tools import auto_white_balance
        result = auto_white_balance(sample_image, strength=0.5)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_batch_result_dataclass(self):
        from backend.providers.image.free_image_tools import BatchResult
        result = BatchResult(
            filename="test.png",
            success=True,
            input_size=1000,
            output_size=800,
            processing_time=1.5,
            tools_applied=["compress"],
        )
        assert result.filename == "test.png"
        assert result.success is True
        assert result.error is None


# ─────────────────────────────────────────────────────────────────────────────
# Visual Voice Search Service tests (visual_voice_search_service.py)
# ─────────────────────────────────────────────────────────────────────────────

class TestVisualVoiceSearchService:
    """Tests for visual_voice_search_service module."""

    def test_process_visual_search_import(self):
        from backend.providers.ai.visual_voice_search_service import process_visual_search
        assert callable(process_visual_search)

    def test_transcribe_voice_search_import(self):
        from backend.providers.ai.visual_voice_search_service import transcribe_voice_search
        assert callable(transcribe_voice_search)

    @patch("backend.providers.ai.visual_voice_search_service.process_image_search")
    @pytest.mark.asyncio
    async def test_process_visual_search_delegates(self, mock_search):
        from backend.providers.ai.visual_voice_search_service import process_visual_search
        mock_search.return_value = {"results": []}
        result = await process_visual_search(b"image_data")
        mock_search.assert_called_once()

    @patch("backend.providers.ai.visual_voice_search_service.transcribe_audio")
    def test_transcribe_voice_search_delegates(self, mock_transcribe):
        from backend.providers.ai.visual_voice_search_service import transcribe_voice_search
        mock_transcribe.return_value = "hello world"
        result = transcribe_voice_search(b"audio_data")
        mock_transcribe.assert_called_once_with(b"audio_data")
        assert result == "hello world"


# ─────────────────────────────────────────────────────────────────────────────
# Image AI Service tests (ai/image_ai_service.py)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.skip(reason="image_ai_service.py has syntax error (malformed imports)")
class TestImageAIService:
    """Tests for image_ai_service module."""

    @pytest.fixture
    def sample_image(self):
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()

    def test_resize_if_needed_small_image(self, sample_image):
        from backend.providers.ai.image_ai_service import _resize_if_needed
        result = _resize_if_needed(sample_image)
        assert result == sample_image

    def test_resize_if_needed_large_image(self):
        from backend.providers.ai.image_ai_service import _resize_if_needed
        img = Image.new("RGB", (2000, 2000), color=(128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        result = _resize_if_needed(buf.getvalue())
        result_img = Image.open(io.BytesIO(result))
        assert max(result_img.size) <= 1024

    def test_composite_white(self, sample_image):
        from backend.providers.ai.image_ai_service import _composite_white
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        result = _composite_white(buf.getvalue())
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_split_grid_landscape(self):
        from backend.providers.ai.image_ai_service import _split_grid
        img = Image.new("RGB", (300, 200), color=(128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        result = _split_grid(buf.getvalue(), count=4)
        assert isinstance(result, list)
        assert len(result) == 4

    def test_split_grid_portrait(self):
        from backend.providers.ai.image_ai_service import _split_grid
        img = Image.new("RGB", (200, 300), color=(128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        result = _split_grid(buf.getvalue(), count=4)
        assert isinstance(result, list)
        assert len(result) == 4

    @patch("backend.providers.ai.image_ai_service._remove_with_rembg")
    def test_remove_background_rembg_success(self, mock_rembg, sample_image):
        from backend.providers.ai.image_ai_service import remove_background
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        mock_rembg.return_value = buf.getvalue()
        result = remove_background(sample_image)
        assert isinstance(result, bytes)
        assert len(result) > 0

    @patch("backend.providers.ai.image_ai_service._remove_with_rembg")
    def test_remove_background_fallback(self, mock_rembg, sample_image):
        from backend.providers.ai.image_ai_service import remove_background
        mock_rembg.side_effect = ImportError("rembg not installed")
        result = remove_background(sample_image)
        assert isinstance(result, bytes)


# ─────────────────────────────────────────────────────────────────────────────
# BG Removal Service tests (bg_removal/bg_removal_service.py)
# ─────────────────────────────────────────────────────────────────────────────

class TestBGRemovalService:
    """Tests for bg_removal_service module."""

    @pytest.fixture
    def sample_image(self):
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()

    def test_valid_strategies(self):
        from backend.providers.bg_removal.bg_removal_service import VALID_STRATEGIES
        assert "auto" in VALID_STRATEGIES
        assert "clean_commercial" in VALID_STRATEGIES
        assert "precision_geometry" in VALID_STRATEGIES
        assert "birefnet_production" in VALID_STRATEGIES
        assert "ultimate_gaps" in VALID_STRATEGIES
        assert "marketing_variants" in VALID_STRATEGIES
        assert "lite_variants" in VALID_STRATEGIES

    def test_preset_aliases(self):
        from backend.providers.bg_removal.bg_removal_service import PRESET_ALIASES
        assert PRESET_ALIASES["general"] == "clean_commercial"
        assert PRESET_ALIASES["handheld"] == "precision_geometry"

    def test_available_models(self):
        from backend.providers.bg_removal.bg_removal_service import AVAILABLE_MODELS
        assert isinstance(AVAILABLE_MODELS, list)
        assert len(AVAILABLE_MODELS) > 0

    def test_session_manager_clear_all(self):
        from backend.providers.bg_removal.bg_removal_service import _SessionManager
        _SessionManager.clear_all()

    def test_session_manager_release_sessions(self):
        from backend.providers.bg_removal.bg_removal_service import _SessionManager
        _SessionManager.release_sessions()

    def test_concurrency_gate_acquire_release(self):
        from backend.providers.bg_removal.bg_removal_service import _ConcurrencyGate
        result = _ConcurrencyGate.acquire(timeout=1.0)
        assert result is True
        _ConcurrencyGate.release()

    def test_resolution_cap_lite(self):
        from backend.providers.bg_removal.bg_removal_service import _resolution_cap
        result = _resolution_cap("birefnet-general-lite", 2048)
        assert result <= 1024

    def test_resolution_cap_heavy(self):
        from backend.providers.bg_removal.bg_removal_service import _resolution_cap
        result = _resolution_cap("birefnet-massive", 2048)
        assert result <= 512

    def test_maybe_downscale_small_image(self, sample_image):
        from backend.providers.bg_removal.bg_removal_service import _maybe_downscale
        result, orig_size = _maybe_downscale(sample_image, 1024)
        assert result == sample_image

    def test_maybe_downscale_large_image(self):
        from backend.providers.bg_removal.bg_removal_service import _maybe_downscale
        img = Image.new("RGB", (2000, 2000), color=(128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        result, orig_size = _maybe_downscale(buf.getvalue(), 1024)
        result_img = Image.open(io.BytesIO(result))
        assert max(result_img.size) <= 1024

    def test_compose_rgba(self):
        from backend.providers.bg_removal.bg_removal_service import _compose_rgba
        arr = np.zeros((100, 100, 3), dtype=np.uint8)
        alpha = np.ones((100, 100), dtype=np.float32) * 0.5
        result = _compose_rgba(arr, alpha)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_compute_quality_score(self):
        from backend.providers.bg_removal.bg_removal_service import _compute_quality_score
        arr = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        alpha = np.ones((100, 100), dtype=np.float32) * 0.8
        result = _compute_quality_score(arr, alpha)
        assert "edge_clarity" in result
        assert "alpha_confidence" in result
        assert "coverage" in result
        assert "overall" in result

    def test_model_file_present(self):
        from backend.providers.bg_removal.bg_removal_service import _model_file_present
        result = _model_file_present("nonexistent-model-xyz")
        assert isinstance(result, bool)

    def test_remove_background_invalid_strategy(self, sample_image):
        from backend.providers.bg_removal.bg_removal_service import remove_background
        result = remove_background(sample_image, strategy="invalid_strategy")
        assert isinstance(result, bytes)

    def test_magic_erase(self, sample_image):
        from backend.providers.bg_removal.bg_removal_service import magic_erase
        result = magic_erase(sample_image)
        assert isinstance(result, bytes)

    def test_remove_background_preset(self, sample_image):
        from backend.providers.bg_removal.bg_removal_service import remove_background_preset
        result = remove_background_preset(sample_image, preset="general")
        assert isinstance(result, bytes)


# ─────────────────────────────────────────────────────────────────────────────
# AI Variant Config constants tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAIVariantConfigConstants:
    """Tests for ai_variant_config module constants."""

    def test_canonical_categories(self):
        from backend.providers.ai.ai_variant_config import CANONICAL_CATEGORIES
        assert "Electronics" in CANONICAL_CATEGORIES
        assert "Clothing" in CANONICAL_CATEGORIES
        assert "Other" in CANONICAL_CATEGORIES

    def test_price_by_type(self):
        from backend.providers.ai.ai_variant_config import _PRICE_BY_TYPE
        assert "electronic" in _PRICE_BY_TYPE
        assert "clothing" in _PRICE_BY_TYPE
        assert _PRICE_BY_TYPE["electronic"] > 0

    def test_category_to_type(self):
        from backend.providers.ai.ai_variant_config import _CATEGORY_TO_TYPE
        assert _CATEGORY_TO_TYPE["Electronics"] == "electronic"
        assert _CATEGORY_TO_TYPE["Clothing"] == "clothing"

    def test_category_aliases(self):
        from backend.providers.ai.ai_variant_config import _CATEGORY_ALIASES
        assert _CATEGORY_ALIASES["phone"] == "Electronics"
        assert _CATEGORY_ALIASES["shirt"] == "Clothing"

    def test_color_names(self):
        from backend.providers.ai.ai_variant_config import _COLOR_NAMES
        assert "red" in _COLOR_NAMES
        assert "blue" in _COLOR_NAMES
        assert isinstance(_COLOR_NAMES["red"], tuple)


# ─────────────────────────────────────────────────────────────────────────────
# BG Removal Service constants tests
# ─────────────────────────────────────────────────────────────────────────────

class TestBGRemovalConstants:
    """Tests for bg_removal module constants."""

    def test_heavy_models(self):
        from backend.providers.bg_removal.bg_removal_service import HEAVY_MODELS
        assert isinstance(HEAVY_MODELS, set)
        assert len(HEAVY_MODELS) > 0

    def test_strategy_models(self):
        from backend.providers.bg_removal.bg_removal_service import STRATEGY_MODELS
        assert "clean_commercial" in STRATEGY_MODELS
        assert "lite_variants" in STRATEGY_MODELS

    def test_light_models(self):
        from backend.providers.bg_removal.bg_removal_service import LIGHT_MODELS
        assert "u2net" in LIGHT_MODELS
        assert "isnet-general-use" in LIGHT_MODELS


# ─────────────────────────────────────────────────────────────────────────────
# Free Image Tools constants tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.skip(reason="free_image_tools.py has syntax error (malformed import)")
class TestFreeImageToolsConstants:
    """Tests for free_image_tools module constants."""

    def test_max_dimension(self):
        from backend.providers.image.free_image_tools import MAX_DIMENSION
        assert MAX_DIMENSION == 2048

    def test_allowed_formats(self):
        from backend.providers.image.free_image_tools import ALLOWED_FORMATS
        assert "PNG" in ALLOWED_FORMATS
        assert "JPEG" in ALLOWED_FORMATS
        assert "WEBP" in ALLOWED_FORMATS


# ─────────────────────────────────────────────────────────────────────────────
# Edge case and integration-style tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEdgeCases:
    """Edge case tests across the media providers."""

    def test_normalize_category_with_mixed_case(self):
        from backend.providers.ai.ai_variant_config import normalize_category
        assert normalize_category("eLeCtRoNiCs") == "Electronics"

    def test_suggest_price_with_empty_name(self):
        from backend.providers.ai.ai_variant_config import suggest_price
        result = suggest_price("electronic", "")
        assert result["ai_suggested_price"] > 0

    def test_parse_bill_text_with_unicode(self):
        pytest.skip("ocr_parser.py has syntax error (IndentationError on import)")

    def test_parse_bill_text_with_multiple_currencies(self):
        pytest.skip("ocr_parser.py has syntax error (IndentationError on import)")

    def test_local_storage_with_binary_data(self, tmp_path):
        from providers.storage.storage_backend import LocalStorage
        storage = LocalStorage(base_dir=str(tmp_path))
        binary_data = bytes(range(256))
        storage.save("binary.bin", binary_data)
        result = storage.read("binary.bin")
        assert result == binary_data

    def test_auto_process_image_with_all_tools(self, sample_image):
        pytest.skip("free_image_tools.py has syntax error (malformed import)")

    @pytest.fixture
    def sample_image(self):
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def test_variant_config_with_empty_config(self):
        from backend.providers.ai.ai_variant_config import VariantConfig
        config = VariantConfig({})
        assert config.get_variants() == {}
        assert config.get_product_type_keywords() == {}

    def test_variant_config_get_allowed_variants_unknown_category(self):
        from backend.providers.ai.ai_variant_config import VariantConfig
        config = VariantConfig({"variants": {}})
        result = config.get_allowed_variants("UnknownCategory", "")
        assert "color" in result

    def test_country_research_service_with_empty_data(self):
        pytest.skip("country_ai_research.py has been removed")
