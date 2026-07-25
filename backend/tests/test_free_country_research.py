"""
Tests for free_country_ecommerce_research.py
==============================================
Tests cover: JSON parsing, prompt building, meta generation, and placeholder module logic.
Avoids external API calls and Ollama by mocking.
"""

import json
import os
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def researcher():
    from free_country_ecommerce_research import FreeEcommerceCountryResearch
    r = FreeEcommerceCountryResearch(
        country="India",
        use_ollama=False,
        enable_web_search=False,
    )
    r.basic = {
        "official_name": "Republic of India",
        "common_name": "India",
        "country_code_alpha2": "IN",
        "country_code_alpha3": "IND",
        "numeric_code": "356",
        "capital": "New Delhi",
        "flag": "\U0001f1ee\U0001f1f3",
        "region": "Asia",
        "subregion": "Southern Asia",
        "area_km2": 3287263,
        "population": 1400000000,
        "timezones": ["UTC+05:30"],
        "calling_codes": ["+91"],
        "google_maps": "https://maps.google.com/?q=India",
        "languages": ["Hindi", "English"],
        "currency_code": "INR",
        "currency_name": "Indian Rupee",
        "currency_symbol": "\u20b9",
        "independent": True,
        "un_member": True,
        "latlng": [20.0, 77.0],
    }
    r.query_name = "India"
    return r


class TestParseJsonText:
    def test_parse_valid_json(self, researcher):
        assert researcher.parse_json_text('{"key": "value"}') == {"key": "value"}

    def test_parse_invalid_with_braces(self, researcher):
        text = 'Some text {"key": "value"} trailing'
        assert researcher.parse_json_text(text) == {"key": "value"}

    def test_parse_no_json(self, researcher):
        assert researcher.parse_json_text("no json here") is None

    def test_parse_nested(self, researcher):
        text = '{"outer": {"inner": [1, 2, 3]}}'
        result = researcher.parse_json_text(text)
        assert result == {"outer": {"inner": [1, 2, 3]}}

    def test_parse_with_newlines(self, researcher):
        text = '{\n  "key": "value"\n}'
        assert researcher.parse_json_text(text) == {"key": "value"}


class TestBuildMeta:
    def test_meta_structure(self, researcher):
        demographics = {"population": {"value": "1400000000", "year": 2023}}
        economy = {
            "gdp_usd": {"value": "3940000000000", "year": 2023},
            "currency": {"code": "INR"},
            "exchange_rate_usd": {"rate": 83.2, "date": "2026-07-25", "source": "Frankfurter ECB"},
        }
        news = [{"title": "India GDP grows 6.5%"}]
        evidence = {"module_04_tax_duties": [{"title": "GST India"}]}

        meta = researcher.build_meta(demographics, economy, news, evidence)
        assert meta["country_input"] == "India"
        assert meta["resolved_country_name"] == "India"
        assert meta["report_date"] is not None
        assert "data_sources" in meta
        assert len(meta["data_sources"]) >= 3
        assert "REST Countries API" in meta["data_sources"]
        assert "World Bank Open Data API" in meta["data_sources"]
        assert meta["ai_backend"] == "none"
        assert meta["freshness"]["news_count"] == 1
        assert meta["freshness"]["web_evidence_modules_count"] == 1
        assert "disclaimer" in meta

    def test_meta_exchange_missing(self, researcher):
        demographics = {}
        economy = {"currency": {"code": "INR"}}
        news = []
        evidence = {}
        meta = researcher.build_meta(demographics, economy, news, evidence)
        assert meta["freshness"]["exchange_rate_date"] is None

    def test_meta_news_count(self, researcher):
        demographics = {}
        economy = {"currency": {"code": "INR"}}
        news = [{"title": "A"}, {"title": "B"}, {"title": "C"}]
        evidence = {}
        meta = researcher.build_meta(demographics, economy, news, evidence)
        assert meta["freshness"]["news_count"] == 3


class TestPlaceholderModules:
    def test_placeholder_structure(self, researcher):
        evidence = {"module_04_tax_duties": [{"title": "GST India", "href": "https://example.com"}]}
        placeholders = researcher.placeholder_modules(evidence)
        assert "module_04_tax_duties" in placeholders
        assert placeholders["module_04_tax_duties"]["status"] == "raw_evidence_only"
        assert placeholders["module_04_tax_duties"]["confidence"] == "low"

    def test_placeholder_no_evidence(self, researcher):
        placeholders = researcher.placeholder_modules({})
        for module in placeholders.values():
            assert module["status"] == "needs_local_ai_or_manual_research"

    def test_placeholder_has_evidence_field(self, researcher):
        evidence = {"module_04_tax_duties": [{"title": "test"}]}
        placeholders = researcher.placeholder_modules(evidence)
        assert placeholders["module_04_tax_duties"]["evidence"] == evidence["module_04_tax_duties"]


class TestApplyAIModules:
    def test_apply_modules_with_valid_ai(self, researcher):
        final = {"module_01_country_identity": {}, "module_02_demographics": {}}
        ai_modules = {
            "module_04_tax_duties": {"standard_tax_percentage": "18%", "confidence": "medium"},
        }
        evidence = {}

        researcher.apply_ai_modules(final, ai_modules, evidence)
        assert final["module_04_tax_duties"]["standard_tax_percentage"] == "18%"

    def test_apply_modules_fallback_to_placeholder(self, researcher):
        final = {"module_01_country_identity": {}}
        evidence = {}

        researcher.apply_ai_modules(final, None, evidence)
        # Should use placeholder for QUAL_MODULES
        for m in ["module_04_tax_duties", "module_05_consumer_psychology"]:
            assert m in final
            assert final[m]["status"] == "needs_local_ai_or_manual_research"

    def test_apply_modules_news_special_handling(self, researcher):
        final = {"module_01_country_identity": {}}
        ai_modules = {"module_18_news_current_context": {"consumer_sentiment": "Cautious"}}
        evidence = {}

        researcher.apply_ai_modules(final, ai_modules, evidence)
        assert final["module_18_news_current_context"]["consumer_sentiment"] == "Cautious"

    def test_apply_modules_extra_keys(self, researcher):
        final = {"module_01_country_identity": {}}
        ai_modules = {"extra_module": {"key": "value"}}
        evidence = {}

        researcher.apply_ai_modules(final, ai_modules, evidence)
        assert "additional_ai_modules" in final
        assert final["additional_ai_modules"]["extra_module"]["key"] == "value"

    def test_apply_modules_with_evidence(self, researcher):
        final = {"module_01_country_identity": {}}
        ai_modules = {"module_04_tax_duties": {"standard_tax_percentage": "18%"}}
        evidence = {"module_04_tax_duties": [{"title": "test"}]}

        researcher.apply_ai_modules(final, ai_modules, evidence)
        assert "evidence" in final["module_04_tax_duties"]


class TestCompactEvidence:
    def test_compact_evidence_truncation(self, researcher):
        evidence = {
            "module_04_tax_duties": [
                {"title": "A", "href": "https://a.com", "snippet": "x" * 500},
                {"title": "B", "href": "https://b.com", "snippet": "short"},
            ]
        }
        compact = researcher.compact_evidence(evidence)
        assert len(compact["module_04_tax_duties"]) == 2
        assert len(compact["module_04_tax_duties"][0]["snippet"]) <= 300

    def test_compact_evidence_limits(self, researcher):
        evidence = {
            "test": [{"title": str(i), "href": f"https://example.com/{i}", "snippet": "test"} for i in range(10)]
        }
        compact = researcher.compact_evidence(evidence)
        assert len(compact["test"]) == 3  # max 3 items

    def test_compact_evidence_skips_non_lists(self, researcher):
        evidence = {"test": "not a list"}
        compact = researcher.compact_evidence(evidence)
        assert "test" not in compact

    def test_compact_evidence_skips_non_dicts(self, researcher):
        evidence = {"test": [1, 2, 3]}
        compact = researcher.compact_evidence(evidence)
        assert compact["test"] == []


class TestBuildAIInput:
    def test_build_ai_input_structure(self, researcher):
        demographics = {
            "population": {"value": "1400000000"},
            "major_cities": [{"city": "Mumbai"}, {"city": "Delhi"}],
        }
        economy = {"gdp_usd": {"value": "3940000000000"}}
        news = [{"title": "News 1"}, {"title": "News 2"}]
        evidence = {"module_04_tax_duties": [{"title": "GST"}]}

        ai_input = researcher.build_ai_input(demographics, economy, news, evidence)
        assert ai_input["country"] == "India"
        assert ai_input["basic_facts"] == researcher.basic
        assert "Mumbai" in ai_input["demographics"]["major_cities"]
        assert len(ai_input["latest_news_titles"]) == 2
        assert "web_evidence" in ai_input

    def test_build_ai_input_city_strings(self, researcher):
        demographics = {"major_cities": ["Mumbai", "Delhi"]}
        economy = {}
        news = []
        evidence = {}
        ai_input = researcher.build_ai_input(demographics, economy, news, evidence)
        assert ai_input["demographics"]["major_cities"] == ["Mumbai", "Delhi"]


class TestSafeInt:
    def test_safe_int_valid(self):
        from free_country_ecommerce_research import safe_int
        assert safe_int("123") == 123

    def test_safe_int_invalid(self):
        from free_country_ecommerce_research import safe_int
        assert safe_int("abc") == 0

    def test_safe_int_none(self):
        from free_country_ecommerce_research import safe_int
        assert safe_int(None) == 0

    def test_safe_int_float(self):
        from free_country_ecommerce_research import safe_int
        assert safe_int(45.7) == 45


class TestBuildPrompt:
    def test_prompt_contains_schema(self, researcher):
        ai_input = {
            "country": "India",
            "today": "2026-07-25",
            "basic_facts": {"name": "India"},
            "demographics": {},
            "economy": {},
            "latest_news_titles": [],
            "web_evidence": {},
        }
        prompt = researcher.build_prompt(ai_input)
        assert "India" in prompt
        assert "tax" in prompt.lower() or "Tax" in prompt or "TAX" in prompt
        assert "e-commerce" in prompt.lower()

    def test_prompt_truncation(self, researcher):
        # Create a large input to test truncation
        large_data = {"data": "x" * 100000}
        ai_input = {
            "country": "India",
            "today": "2026-07-25",
            "basic_facts": large_data,
            "demographics": large_data,
            "economy": large_data,
            "latest_news_titles": [],
            "web_evidence": {},
        }
        prompt = researcher.build_prompt(ai_input)
        # The prompt is truncated at 90000 chars for the facts_json + schema overhead
        assert len(prompt) < 100000  # Should be truncated to ~90k + overhead


class TestOllamaTags:
    def test_ollama_tags_connection_refused(self, researcher):
        tags = researcher.ollama_tags()
        # If Ollama is not running, returns None. If running, returns list of models.
        assert tags is None or isinstance(tags, list)

    def test_select_ollama_model_no_models(self, researcher):
        with patch.object(researcher, "ollama_tags", return_value=None):
            model = researcher.select_ollama_model()
            assert model is None

    def test_select_ollama_model_with_matching(self, researcher):
        models = [{"name": "llama3.1"}, {"name": "mistral"}]
        with patch.object(researcher, "ollama_tags", return_value=models):
            model = researcher.select_ollama_model()
            assert model == "llama3.1"

    def test_select_ollama_model_fallback(self, researcher):
        models = [{"name": "llama3.2:3b"}, {"name": "mistral"}]
        with patch.object(researcher, "ollama_tags", return_value=models):
            model = researcher.select_ollama_model()
            assert model is not None


class TestGenerateAIModules:
    def test_generate_disabled(self, researcher):
        researcher.use_ollama = False
        result = researcher.generate_ai_modules({})
        assert result is None

    def test_generate_no_model(self, researcher):
        with patch.object(researcher, "select_ollama_model", return_value=None):
            result = researcher.generate_ai_modules({})
            assert result is None


class TestWriteMarkdown:
    def test_write_markdown_creates_file(self, researcher, tmp_path):
        report = {
            "meta": {"generated_at_utc": "2026-07-25T00:00:00Z"},
            "module_01_country_identity": {"official_name": "Republic of India", "common_name": "India"},
        }
        md_path = tmp_path / "test_report.md"
        researcher.write_markdown(report, str(md_path))
        assert md_path.exists()
        content = md_path.read_text(encoding="utf-8")
        assert "Republic of India" in content
        assert "E-commerce Country Research" in content

    def test_write_markdown_truncates_large_sections(self, researcher, tmp_path):
        report = {
            "meta": {"generated_at_utc": "2026-07-25T00:00:00Z"},
            "module_01_country_identity": {"large_field": "x" * 50000},
        }
        md_path = tmp_path / "test_truncated.md"
        researcher.write_markdown(report, str(md_path))
        content = md_path.read_text(encoding="utf-8")
        # Value truncated to 60 chars + "..." by as_table
        assert "..." in content
        assert "large_field" in content
