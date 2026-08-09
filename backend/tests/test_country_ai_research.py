"""Tests for country_ai_research.py — async AI enrichment service."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from services.country_ai_research import (
    CountryAIResearchService,
    AI_SCHEMA,
    QUAL_MODULES,
)


@pytest.fixture
def base_report():
    return {
        "module_01_country_identity": {
            "official_name": "Republic of India",
            "common_name": "India",
            "country_code_alpha2": "IN",
        },
        "module_02_demographics": {
            "total_population": 1400000000,
            "internet_penetration_pct": 52.0,
        },
        "module_03_economy_wealth": {
            "gdp_usd": 3940000000000.0,
            "gdp_per_capita_usd": 2400.0,
        },
    }


@pytest.fixture
def demographics():
    return {
        "population": 1400000000,
        "urban_population_pct": 35.0,
        "literacy_rate_pct": 77.7,
        "major_cities": [{"city": "Mumbai", "population": 12480000}],
    }


@pytest.fixture
def economy():
    return {
        "gdp_usd": 3940000000000.0,
        "gdp_per_capita_ppp_usd": {"value": 9183.0, "year": 2024},
        "gdp_growth_pct": 6.5,
        "inflation_pct": 5.1,
        "currency_code": "INR",
    }


@pytest.fixture
def empty_evidence():
    return {}


class TestCountryAIResearchServiceInit:
    def test_init_stores_parameters(self, base_report, demographics, economy):
        service = CountryAIResearchService(
            country_name="India",
            base_report=base_report,
            demographics=demographics,
            economy=economy,
            news=[],
            evidence={},
        )
        assert service.country_name == "India"
        assert service.base_report == base_report
        assert service.demographics == demographics
        assert service.economy == economy
        assert service.ai_backend == "none"


class TestBuildAIInput:
    def test_build_ai_input_returns_dict_with_expected_keys(self, base_report, demographics, economy, empty_evidence):
        service = CountryAIResearchService(
            country_name="India",
            base_report=base_report,
            demographics=demographics,
            economy=economy,
            news=[],
            evidence=empty_evidence,
        )
        result = service._build_ai_input(empty_evidence)
        assert "country" in result
        assert result["country"] == "India"
        assert "today" in result
        assert "basic_facts" in result
        assert "income_tier" in result
        assert "demographics" in result
        assert "economy" in result
        assert "latest_news_titles" in result
        assert "web_evidence" in result

    def test_build_ai_input_filters_empty_economy_values(self, base_report, demographics, economy, empty_evidence):
        service = CountryAIResearchService(
            country_name="India",
            base_report=base_report,
            demographics=demographics,
            economy=economy,
            news=[],
            evidence=empty_evidence,
        )
        result = service._build_ai_input(empty_evidence)
        assert "gdp_usd" in result["economy"]

    def test_build_ai_input_income_tier_lower_middle(self, base_report, demographics, economy, empty_evidence):
        service = CountryAIResearchService(
            country_name="India",
            base_report=base_report,
            demographics=demographics,
            economy=economy,
            news=[],
            evidence=empty_evidence,
        )
        result = service._build_ai_input(empty_evidence)
        assert result["income_tier"] == "lower_middle"

    def test_build_ai_input_income_tier_high(self, base_report, demographics, economy, empty_evidence):
        economy_high = dict(economy)
        economy_high["gdp_per_capita_ppp_usd"] = {"value": 35000.0, "year": 2024}
        service = CountryAIResearchService(
            country_name="Singapore",
            base_report=base_report,
            demographics=demographics,
            economy=economy_high,
            news=[],
            evidence=empty_evidence,
        )
        result = service._build_ai_input(empty_evidence)
        assert result["income_tier"] == "high"


class TestCompactEvidence:
    def test_compact_evidence_limits_to_three_items(self, base_report, demographics, economy, empty_evidence):
        service = CountryAIResearchService(
            country_name="India",
            base_report=base_report,
            demographics=demographics,
            economy=economy,
            news=[],
            evidence=empty_evidence,
        )
        evidence = {
            "module_04_tax_duties": [
                {"title": "Tax info 1", "href": "https://example.com/1", "snippet": "snippet 1"},
                {"title": "Tax info 2", "href": "https://example.com/2", "snippet": "snippet 2"},
                {"title": "Tax info 3", "href": "https://example.com/3", "snippet": "snippet 3"},
                {"title": "Tax info 4", "href": "https://example.com/4", "snippet": "snippet 4"},
            ]
        }
        result = service._compact_evidence(evidence)
        assert len(result["module_04_tax_duties"]) == 3

    def test_compact_evidence_empty_input(self, base_report, demographics, economy, empty_evidence):
        service = CountryAIResearchService(
            country_name="India",
            base_report=base_report,
            demographics=demographics,
            economy=economy,
            news=[],
            evidence=empty_evidence,
        )
        result = service._compact_evidence({})
        assert result == {}


class TestParseJsonText:
    def test_parse_valid_json(self, base_report, demographics, economy, empty_evidence):
        service = CountryAIResearchService(
            country_name="India",
            base_report=base_report,
            demographics=demographics,
            economy=economy,
            news=[],
            evidence=empty_evidence,
        )
        result = service._parse_json_text('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_json_with_surrounding_text(self, base_report, demographics, economy, empty_evidence):
        service = CountryAIResearchService(
            country_name="India",
            base_report=base_report,
            demographics=demographics,
            economy=economy,
            news=[],
            evidence=empty_evidence,
        )
        text = 'Some preamble {"key": "value"} trailing text'
        result = service._parse_json_text(text)
        assert result == {"key": "value"}

    def test_parse_invalid_json_returns_none(self, base_report, demographics, economy, empty_evidence):
        service = CountryAIResearchService(
            country_name="India",
            base_report=base_report,
            demographics=demographics,
            economy=economy,
            news=[],
            evidence=empty_evidence,
        )
        result = service._parse_json_text("not json at all")
        assert result is None

    def test_parse_empty_string_returns_none(self, base_report, demographics, economy, empty_evidence):
        service = CountryAIResearchService(
            country_name="India",
            base_report=base_report,
            demographics=demographics,
            economy=economy,
            news=[],
            evidence=empty_evidence,
        )
        result = service._parse_json_text("")
        assert result is None


class TestMergeAIOutput:
    def test_merge_preserves_base_report(self, base_report, demographics, economy, empty_evidence):
        service = CountryAIResearchService(
            country_name="India",
            base_report=base_report,
            demographics=demographics,
            economy=economy,
            news=[],
            evidence=empty_evidence,
        )
        ai_modules = {
            "module_04_tax_duties": {
                "tax_system_type": "GST",
                "standard_tax_rate": "18%",
                "confidence": "medium",
                "verification_notes": "AI-generated",
                "sources": ["DuckDuckGo"],
            }
        }
        result = service._merge_ai_output(ai_modules, empty_evidence)
        assert "module_01_country_identity" in result
        assert result["module_01_country_identity"]["official_name"] == "Republic of India"

    def test_merge_adds_ai_module_data(self, base_report, demographics, economy, empty_evidence):
        service = CountryAIResearchService(
            country_name="India",
            base_report=base_report,
            demographics=demographics,
            economy=economy,
            news=[],
            evidence=empty_evidence,
        )
        ai_modules = {
            "module_04_tax_duties": {
                "tax_system_type": "GST",
                "standard_tax_rate": "18%",
                "confidence": "medium",
                "verification_notes": "",
                "sources": [],
            }
        }
        result = service._merge_ai_output(ai_modules, empty_evidence)
        assert result["module_04_tax_duties"]["tax_system_type"] == "GST"
        assert result["module_04_tax_duties"]["standard_tax_rate"] == "18%"

    def test_merge_preserves_base_module_when_ai_has_no_data(self, base_report, demographics, economy, empty_evidence):
        service = CountryAIResearchService(
            country_name="India",
            base_report=base_report,
            demographics=demographics,
            economy=economy,
            news=[],
            evidence=empty_evidence,
        )
        ai_modules = {}
        result = service._merge_ai_output(ai_modules, empty_evidence)
        assert result["module_01_country_identity"]["official_name"] == "Republic of India"

    def test_merge_sets_low_confidence_when_ai_module_has_no_confidence(self, base_report, demographics, economy, empty_evidence):
        service = CountryAIResearchService(
            country_name="India",
            base_report=base_report,
            demographics=demographics,
            economy=economy,
            news=[],
            evidence=empty_evidence,
        )
        ai_modules = {
            "module_04_tax_duties": {
                "tax_system_type": "GST",
                "standard_tax_rate": "18%",
            }
        }
        result = service._merge_ai_output(ai_modules, empty_evidence)
        assert result["module_04_tax_duties"]["confidence"] == "low"

    def test_merge_adds_evidence_to_module_18(self, base_report, demographics, economy, empty_evidence):
        service = CountryAIResearchService(
            country_name="India",
            base_report=base_report,
            demographics=demographics,
            economy=economy,
            news=[],
            evidence=empty_evidence,
        )
        ai_modules = {
            "module_18_news_current_context": {
                "current_context_summary": "Stable economy",
                "confidence": "medium",
            }
        }
        evidence_18 = [{"title": "News item", "href": "https://example.com"}]
        result = service._merge_ai_output(ai_modules, {"module_18_news_current_context": evidence_18})
        assert "evidence" in result["module_18_news_current_context"]
        assert result["module_18_news_current_context"]["evidence"] == evidence_18


class TestFallback:
    def test_fallback_returns_base_report_copy(self, base_report, demographics, economy, empty_evidence):
        service = CountryAIResearchService(
            country_name="India",
            base_report=base_report,
            demographics=demographics,
            economy=economy,
            news=[],
            evidence=empty_evidence,
        )
        result = service._fallback("AI disabled")
        assert result["module_01_country_identity"]["official_name"] == "Republic of India"


class TestAI_SCHEMA:
    def test_all_qual_modules_have_schema_entries(self):
        for module in QUAL_MODULES:
            assert module in AI_SCHEMA, f"Missing schema for {module}"

    def test_schema_entries_have_required_keys(self):
        for module, schema in AI_SCHEMA.items():
            assert "confidence" in schema
            assert "verification_notes" in schema
            assert "sources" in schema


class TestEnrichDisabled:
    def test_enrich_returns_base_report_when_disabled(self, base_report, demographics, economy, empty_evidence):
        with patch("services.country_ai_research.settings") as mock_settings:
            mock_settings.country_ai_enabled = False
            service = CountryAIResearchService(
                country_name="India",
                base_report=base_report,
                demographics=demographics,
                economy=economy,
                news=[],
                evidence=empty_evidence,
            )
            import asyncio
            result = asyncio.run(service.enrich())
            assert result["module_01_country_identity"]["official_name"] == "Republic of India"