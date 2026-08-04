"""Async AI enrichment service for country research qualitative modules."""

import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

from utils.config import settings

logger = logging.getLogger(__name__)

QUAL_MODULES = [
    "module_04_tax_duties",
    "module_05_consumer_psychology",
    "module_06_consumption_preferences",
    "module_07_shopping_seasonality",
    "module_08_digital_landscape",
    "module_09_payment_infrastructure",
    "module_10_logistics_shipping",
    "module_11_legal_regulations",
    "module_12_language_communication",
    "module_13_community_social",
    "module_14_marketing_advertising",
    "module_15_competition",
    "module_16_customer_service",
    "module_17_technology_infrastructure",
    "module_18_news_current_context",
    "module_19_risk_compliance",
    "module_20_strategic_recommendations",
]

AI_SCHEMA = {
    "module_04_tax_duties": {
        "tax_system_type": "",
        "standard_tax_rate": "",
        "tax_slabs_tiers": [],
        "digital_goods_tax": "",
        "physical_goods_tax": "",
        "import_customs_duty": "",
        "customs_threshold_de_minimis": "",
        "who_pays_duty_ddp_vs_ddu": "",
        "tax_registration_requirement": "",
        "foreign_company_tax_obligation": "",
        "withholding_tax_on_cross_border": "",
        "tax_filing_frequency": "",
        "tax_authority_name": "",
        "free_trade_agreements": [],
        "confidence": "high|medium|low",
        "verification_notes": "",
        "sources": [],
    },
    "module_05_consumer_psychology": {
        "general_mindset_toward_online_shopping": "",
        "price_sensitivity_level_1_to_10": "",
        "brand_loyalty_level_1_to_10": "",
        "status_prestige_buying": "",
        "family_influence_on_purchases_1_to_10": "",
        "peer_social_proof_influence_1_to_10": "",
        "fomo_factor_during_sales_1_to_10": "",
        "trust_in_foreign_brands": "",
        "trust_in_new_unknown_brands": "",
        "bargaining_discount_expectation": "",
        "impulse_vs_planned_buying_ratio": "",
        "research_before_purchase": "",
        "emotional_vs_rational_buying": "",
        "attitude_toward_made_in_country": "",
        "generational_differences": "",
        "confidence": "high|medium|low",
        "verification_notes": "",
        "sources": [],
    },
    "module_06_consumption_preferences": {
        "top_10_product_categories_by_demand": [],
        "average_order_value": "",
        "quality_vs_price_priority": "",
        "sustainability_eco_consciousness": "",
        "preference_for_local_vs_international": "",
        "size_fit_preferences": "",
        "color_design_preferences": "",
        "packaging_expectations": "",
        "subscription_repeat_purchase_rate": "",
        "bulk_wholesale_buying_culture": "",
        "seasonal_product_demand": "",
        "halal_kosher_vegetarian_requirements": [],
        "prohibited_restricted_products": [],
        "confidence": "high|medium|low",
        "verification_notes": "",
        "sources": [],
    },
    "module_07_shopping_seasonality": {
        "major_shopping_festivals": [],
        "ecommerce_specific_sales_events": [],
        "global_sales_events_participation": [],
        "payday_shopping_cycles": "",
        "wedding_season_impact": "",
        "back_to_school_season": "",
        "religious_fasting_periods": [],
        "monsoon_weather_impact": "",
        "peak_shopping_hours": "",
        "peak_shopping_days": "",
        "confidence": "high|medium|low",
        "verification_notes": "",
        "sources": [],
    },
    "module_08_digital_landscape": {
        "internet_penetration_percent": "",
        "mobile_vs_desktop_split": "",
        "average_internet_speed": "",
        "smartphone_penetration": "",
        "dominant_os_android_vs_ios": "",
        "top_social_media_platforms": [],
        "social_media_hours_per_day": "",
        "top_ecommerce_apps": [],
        "search_engine_preference": "",
        "email_open_engagement_rate": "",
        "video_commerce_live_shopping": "",
        "ai_chatbot_acceptance": "",
        "confidence": "high|medium|low",
        "verification_notes": "",
        "sources": [],
    },
    "module_09_payment_infrastructure": {
        "most_popular_payment_method": "",
        "top_5_payment_gateways": [],
        "credit_debit_card_penetration": "",
        "digital_wallet_usage": [],
        "cash_on_delivery_percentage": "",
        "bank_transfer_net_banking_percentage": "",
        "buy_now_pay_later_bnpl": "",
        "emi_installment_culture": "",
        "international_card_acceptance": [],
        "cryptocurrency_status": "",
        "average_transaction_value": "",
        "payment_failure_rate": "",
        "refund_processing_time": "",
        "currency_conversion_fees": "",
        "confidence": "high|medium|low",
        "verification_notes": "",
        "sources": [],
    },
    "module_10_logistics_shipping": {
        "top_courier_logistics_companies": [],
        "average_delivery_time_metro": "",
        "average_delivery_time_rural": "",
        "shipping_cost_expectation": "",
        "free_shipping_threshold": "",
        "same_day_next_day_availability": "",
        "last_mile_delivery_quality": "",
        "package_tracking_expectation": "",
        "cod_availability_by_region": "",
        "return_pickup_service": "",
        "customs_clearance_time_imports": "",
        "warehousing_hubs": [],
        "packaging_regulations": [],
        "confidence": "high|medium|low",
        "verification_notes": "",
        "sources": [],
    },
    "module_11_legal_regulations": {
        "ecommerce_registration_requirement": "",
        "consumer_protection_law": "",
        "mandatory_return_refund_window": "",
        "data_privacy_law": "",
        "data_localization_requirement": "",
        "cookie_tracking_consent_rules": "",
        "advertising_standards_restrictions": [],
        "product_labeling_requirements": [],
        "prohibited_restricted_items_for_sale": [],
        "intellectual_property_trademark_laws": "",
        "antitrust_competition_law": "",
        "gst_invoice_requirements": "",
        "foreign_exchange_regulations": "",
        "age_verification_requirements": "",
        "environmental_e_waste_regulations": "",
        "confidence": "high|medium|low",
        "verification_notes": "",
        "sources": [],
    },
    "module_12_language_communication": {
        "official_languages": [],
        "regional_state_languages": [],
        "primary_ecommerce_language": "",
        "localization_requirement_languages": [],
        "script_writing_systems": [],
        "date_number_format": "",
        "measurement_system": "",
        "customer_support_language_expectation": "",
        "rtl_right_to_left_requirement": "",
        "tone_formality_in_communication": "",
        "confidence": "high|medium|low",
        "verification_notes": "",
        "sources": [],
    },
    "module_13_community_social": {
        "family_structure": "",
        "decision_making_unit": "",
        "caste_class_sensitivity": "",
        "gender_roles_in_purchasing": "",
        "community_group_buying_culture": "",
        "influencer_celebrity_impact": "",
        "religious_cultural_sensitivities": [],
        "festival_gifting_culture": "",
        "trust_in_word_of_mouth": "",
        "review_rating_culture": "",
        "confidence": "high|medium|low",
        "verification_notes": "",
        "sources": [],
    },
    "module_14_marketing_advertising": {
        "most_effective_ad_channels": [],
        "influencer_marketing_effectiveness": "",
        "email_marketing_effectiveness": "",
        "whatsapp_marketing_effectiveness": "",
        "sms_marketing_effectiveness": "",
        "tv_traditional_media_impact": "",
        "affiliate_marketing_maturity": [],
        "seo_organic_search_behavior": "",
        "ad_spend_per_capita": "",
        "best_time_to_run_ads": "",
        "content_format_preference": [],
        "loyalty_rewards_program_response": "",
        "confidence": "high|medium|low",
        "verification_notes": "",
        "sources": [],
    },
    "module_15_competition": {
        "top_5_ecommerce_platforms": [],
        "market_share_breakdown": "",
        "niche_vertical_players": [],
        "social_commerce_platforms": [],
        "d2c_brand_ecosystem": "",
        "price_comparison_behavior": "",
        "market_entry_barriers": [],
        "white_space_untapped_niches": [],
        "confidence": "high|medium|low",
        "verification_notes": "",
        "sources": [],
    },
    "module_16_customer_service": {
        "preferred_support_channels": [],
        "expected_response_time": "",
        "support_language": "",
        "return_refund_expectation": "",
        "compensation_culture": "",
        "social_media_complaint_behavior": "",
        "warranty_guarantee_expectation": "",
        "after_sales_service_importance": "",
        "confidence": "high|medium|low",
        "verification_notes": "",
        "sources": [],
    },
    "module_17_technology_infrastructure": {
        "cloud_hosting_regulations": "",
        "cdn_server_location_recommendation": [],
        "app_store_preferences": "",
        "pwa_vs_native_app_preference": "",
        "browser_usage": "",
        "common_screen_sizes": "",
        "low_bandwidth_optimization_needed": "",
        "upi_api_integration_standards": "",
        "confidence": "high|medium|low",
        "verification_notes": "",
        "sources": [],
    },
    "module_18_news_current_context": {
        "current_context_summary": "",
        "political_stability": "",
        "recent_regulatory_changes": [],
        "natural_disasters_disruptions": [],
        "consumer_sentiment_index": "",
        "trending_products_viral_items": [],
        "exchange_rate_volatility_current": "",
        "confidence": "high|medium|low",
        "verification_notes": "",
        "sources": [],
    },
    "module_19_risk_compliance": {
        "fraud_chargeback_rate": "",
        "cod_rejection_risk": "",
        "counterfeit_product_prevalence": "",
        "cybersecurity_threat_level": "",
        "sanctions_trade_restrictions": "",
        "political_risk_to_business": "",
        "currency_repatriation_risk": "",
        "legal_dispute_resolution": "",
        "overall_risk_score_1_to_10": "",
        "confidence": "high|medium|low",
        "verification_notes": "",
        "sources": [],
    },
    "module_20_strategic_recommendations": {
        "market_entry_strategy": "",
        "pricing_strategy": "",
        "recommended_product_mix": [],
        "recommended_payment_stack": [],
        "recommended_marketing_mix": [],
        "localization_priority": [],
        "key_success_factors": [],
        "key_risks_to_mitigate": [],
        "estimated_time_to_profitability": "",
        "recommended_budget_allocation": {},
        "confidence": "high|medium|low",
        "verification_notes": "",
        "sources": [],
    },
}

DDG_QUERIES = [
    ("module_04_tax_duties", "{country} ecommerce tax VAT GST rate {year}"),
    ("module_04_tax_duties", "{country} import duty de minimis threshold ecommerce {year}"),
    ("module_05_consumer_psychology", "{country} online shopping consumer behavior {year}"),
    ("module_06_consumption_preferences", "{country} top ecommerce product categories {year}"),
    ("module_07_shopping_seasonality", "{country} biggest shopping festivals ecommerce {year}"),
    ("module_08_digital_landscape", "{country} internet social media ecommerce usage {year}"),
    ("module_09_payment_infrastructure", "{country} popular payment gateways digital wallets COD {year}"),
    ("module_10_logistics_shipping", "{country} ecommerce courier delivery companies shipping times {year}"),
    ("module_11_legal_regulations", "{country} ecommerce consumer protection data privacy law {year}"),
    ("module_12_language_communication", "{country} official languages ecommerce localization {year}"),
    ("module_13_community_social", "{country} family community influence buying decisions {year}"),
    ("module_14_marketing_advertising", "{country} digital marketing channels influencer ecommerce {year}"),
    ("module_15_competition", "{country} top ecommerce marketplaces market share {year}"),
    ("module_16_customer_service", "{country} ecommerce customer service returns expectations {year}"),
    ("module_17_technology_infrastructure", "{country} mobile android app ecommerce technology {year}"),
    ("module_19_risk_compliance", "{country} ecommerce fraud chargeback regulatory risk {year}"),
    ("module_20_strategic_recommendations", "{country} ecommerce market entry strategy {year}"),
]


class CountryAIResearchService:
    def __init__(
        self,
        country_name: str,
        base_report: Dict[str, Any],
        demographics: Dict[str, Any],
        economy: Dict[str, Any],
        news: List[Dict[str, Any]],
        evidence: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        self.country_name = country_name
        self.base_report = base_report
        self.demographics = demographics
        self.economy = economy
        self.news = news
        self.evidence = evidence
        self.ai_backend = "none"

    async def enrich(self) -> Dict[str, Any]:
        if not getattr(settings, "country_ai_enabled", True):
            logger.info("Country AI enrichment disabled by settings.")
            return self._fallback("AI enrichment disabled by configuration.")

        web_evidence = await self._fetch_web_evidence()
        ai_modules = await self._generate_ai_modules(web_evidence)
        merged = self._merge_ai_output(ai_modules, web_evidence)
        return merged

    async def _fetch_web_evidence(self) -> Dict[str, List[Dict[str, Any]]]:
        evidence: Dict[str, List[Dict[str, Any]]] = {}
        if not getattr(settings, "country_ai_web_search_enabled", True):
            return evidence

        year = datetime.now().year
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            for module, template in DDG_QUERIES:
                query_text = template.replace("{country}", self.country_name).replace("{year}", str(year))
                evidence.setdefault(module, [])
                try:
                    response = await client.get(
                        "https://duckduckgo.com/html/",
                        params={"q": query_text},
                        headers={"User-Agent": "Mozilla/5.0 (compatible; ZoziCountryAI/1.0)"},
                    )
                    if response.status_code == 200:
                        evidence[module].append(
                            {
                                "query": query_text,
                                "title": f"Web search: {query_text}",
                                "href": f"https://duckduckgo.com/?q={quote(query_text)}",
                                "snippet": (response.text or "")[:500],
                                "source": "DuckDuckGo",
                            }
                        )
                except Exception as exc:
                    logger.warning("Web evidence fetch failed for %s: %s", module, exc)
                await asyncio_sleep(1.2)
        return evidence

    async def _generate_ai_modules(self, evidence: Dict[str, List[Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
        model = getattr(settings, "country_ai_ollama_model", "llama3.1")
        base_url = getattr(settings, "ollama_base_url", "http://localhost:11434")
        ai_url = f"{base_url}/api/chat"
        payload = self._build_ai_payload(evidence)

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(900.0)) as client:
                response = await client.post(
                    ai_url,
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": payload["prompt"]}],
                        "stream": False,
                        "format": "json",
                        "options": {"temperature": 0.2, "num_ctx": 8192},
                    },
                )
                response.raise_for_status()
                data = response.json()
                if data.get("error"):
                    raise RuntimeError(data["error"])
                content = data.get("message", {}).get("content", "")
                parsed = self._parse_json_text(content)
                if parsed is None:
                    raise RuntimeError("Ollama returned invalid JSON.")
                self.ai_backend = f"ollama:{model}"
                return parsed
        except Exception as exc:
            logger.warning("AI module generation failed: %s", exc)
            self.ai_backend = "none"
            return None

    def _build_ai_payload(self, evidence: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        ai_input = self._build_ai_input(evidence)
        facts_json = json.dumps(ai_input, ensure_ascii=False, indent=2)
        if len(facts_json) > 90000:
            facts_json = facts_json[:90000] + "\n... truncated"
        prompt = "\n".join(
            [
                "You are an expert e-commerce country research analyst.",
                f"Today is {datetime.now(timezone.utc).strftime('%Y-%m-%d')}.",
                "Use only the provided facts, latest news titles, and web evidence.",
                "If evidence is missing, do not invent exact legal or tax numbers.",
                "Use \"unknown\" for missing fields.",
                "If you provide a number, mention uncertainty in verification_notes unless evidence clearly supports it.",
                "Use sources arrays when evidence URLs are available.",
                "Return ONLY valid JSON.",
                "Do not include markdown.",
                "Do not include comments.",
                "Do not include trailing commas.",
                "",
                "PROVIDED DATA:",
                facts_json,
                "",
                "Return JSON matching this schema:",
                json.dumps(AI_SCHEMA, indent=2),
            ]
        )
        return {"prompt": prompt, "ai_input": ai_input}

    def _build_ai_input(self, evidence: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        demo = dict(self.demographics)
        cities = demo.get("major_cities") or []
        demo["major_cities"] = [
            city.get("city") if isinstance(city, dict) else city for city in cities[:10]
        ]
        econ = {key: value for key, value in self.economy.items() if value not in (None, "", [], {})}
        gdp_pc = None
        gdp_per_capita = self.economy.get("gdp_per_capita_ppp_usd")
        if isinstance(gdp_per_capita, dict):
            try:
                gdp_pc = float(gdp_per_capita.get("value", 0))
            except Exception:
                pass
        income_tier = "low"
        if gdp_pc:
            if gdp_pc > 30000:
                income_tier = "high"
            elif gdp_pc > 10000:
                income_tier = "upper_middle"
            elif gdp_pc > 4000:
                income_tier = "lower_middle"

        compact_evidence = self._compact_evidence(evidence)
        return {
            "country": self.country_name,
            "today": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "basic_facts": self.base_report.get("module_01_country_identity", {}),
            "income_tier": income_tier,
            "demographics": demo,
            "economy": econ,
            "latest_news_titles": [item.get("title") for item in (self.news or [])[:10] if isinstance(item, dict)],
            "web_evidence": compact_evidence,
        }

    def _compact_evidence(self, evidence: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        compact: Dict[str, List[Dict[str, Any]]] = {}
        for module, items in evidence.items():
            if not isinstance(items, list):
                continue
            compact[module] = []
            for item in items[:3]:
                if not isinstance(item, dict):
                    continue
                compact[module].append(
                    {
                        "title": item.get("title"),
                        "href": item.get("href"),
                        "snippet": (item.get("snippet") or "")[:300],
                    }
                )
        return compact

    def _parse_json_text(self, text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        try:
            return json.loads(text)
        except Exception:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    return None
        return None

    def _merge_ai_output(
        self, ai_modules: Optional[Dict[str, Any]], evidence: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        merged = dict(self.base_report)
        if not isinstance(ai_modules, dict):
            ai_modules = {}

        for module in QUAL_MODULES:
            ai_part = ai_modules.get(module)
            base_module = merged.get(module) or {}
            if module == "module_18_news_current_context":
                merged.setdefault(module, {})
                if isinstance(ai_part, dict):
                    merged[module].update({k: v for k, v in ai_part.items() if v not in (None, "", [], {})})
                current_evidence = evidence.get(module) or []
                if current_evidence:
                    merged[module]["evidence"] = current_evidence
                continue

            if isinstance(ai_part, dict):
                merged[module] = {**base_module, **ai_part}
            else:
                merged[module] = base_module
            current_evidence = evidence.get(module) or []
            if current_evidence:
                merged[module]["evidence"] = current_evidence
            if not merged[module].get("confidence"):
                merged[module]["confidence"] = "low"
            if not merged[module].get("sources"):
                merged[module]["sources"] = ["Auto-populate heuristic"] + [
                    item.get("href") or item.get("source") for item in current_evidence if isinstance(item, dict)
                ]

        extra = {key: value for key, value in ai_modules.items() if key not in QUAL_MODULES}
        if extra:
            merged["additional_ai_modules"] = extra
        return merged

    def _fallback(self, message: str) -> Dict[str, Any]:
        logger.warning("AI research fallback: %s", message)
        return dict(self.base_report)


async def asyncio_sleep(seconds: float) -> None:
    import asyncio
    await asyncio.sleep(seconds)
