#!/usr/bin/env python3
"""
Free E-commerce Country Research Script

Uses only free sources:
- REST Countries API
- World Bank API
- Frankfurter ECB exchange rates
- open.er-api fallback
- CountriesNow API
- Optional GeoNames free API
- Wikipedia API
- Google News RSS
- Optional DuckDuckGo search evidence
- Optional local Ollama LLM for deep qualitative research

Output:
- JSON report for e-commerce system integration
- Markdown report for human reading
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from urllib.parse import quote
from xml.etree import ElementTree as ET

import requests

try:
    from duckduckgo_search import DDGS
except Exception:
    DDGS = None

CURRENT_YEAR = datetime.now().year
TODAY = datetime.now().strftime("%Y-%m-%d")

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


def safe_int(value):
    try:
        return int(value)
    except Exception:
        return 0


class FreeEcommerceCountryResearch:
    def __init__(
        self,
        country,
        use_ollama=True,
        ollama_model="llama3.1",
        enable_web_search=True,
        geonames_username=None,
        max_cities=20,
        max_news=12,
    ):
        self.country = country.strip()
        self.query_name = self.country
        self.use_ollama = use_ollama
        self.ollama_model = ollama_model
        self.web_search_requested = enable_web_search
        self.enable_web_search = enable_web_search and DDGS is not None
        self.geonames_username = geonames_username or os.getenv("GEONAMES_USERNAME")
        self.max_cities = max_cities
        self.max_news = max_news
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (compatible; FreeEcomResearch/1.0; +https://github.com/zozi)"}
        )
        self.basic = None
        self.ai_backend = "none"

    def log(self, message):
        print(message, flush=True)

    def fetch_basic(self):
        url = f"https://restcountries.com/v3.1/name/{quote(self.country)}?fullText=true"
        response = self.session.get(url, timeout=30)

        if not response.ok:
            url = f"https://restcountries.com/v3.1/name/{quote(self.country)}"
            response = self.session.get(url, timeout=30)

        if not response.ok:
            raise Exception(
                f"Country not found: {self.country}. Try the English official country name."
            )

        data = response.json()
        if not data:
            raise Exception("Empty response from REST Countries API.")

        d = data[0]

        currencies = d.get("currencies", {}) or {}
        currency_code = next(iter(currencies), None)
        currency_info = currencies.get(currency_code, {}) if currency_code else {}

        idd = d.get("idd") or {}
        calling_codes = []
        if idd.get("root"):
            suffixes = idd.get("suffixes") or [""]
            calling_codes = [f"{idd.get('root')}{suffix}" for suffix in suffixes]

        self.basic = {
            "official_name": d.get("name", {}).get("official"),
            "common_name": d.get("name", {}).get("common"),
            "country_code_alpha2": d.get("cca2"),
            "country_code_alpha3": d.get("cca3"),
            "numeric_code": d.get("ccn3"),
            "capital": (d.get("capital") or [None])[0],
            "flag_emoji": d.get("flag"),
            "flag_png": (d.get("flags") or {}).get("png"),
            "flag_svg": (d.get("flags") or {}).get("svg"),
            "region": d.get("region"),
            "subregion": d.get("subregion"),
            "continents": d.get("continents"),
            "area_km2": d.get("area"),
            "landlocked": d.get("landlocked"),
            "population": d.get("population"),
            "timezones": d.get("timezones"),
            "calling_codes": calling_codes,
            "google_maps": d.get("maps", {}).get("googleMaps"),
            "open_street_maps": d.get("maps", {}).get("openStreetMaps"),
            "languages": list((d.get("languages") or {}).values()),
            "currency_code": currency_code,
            "currency_name": currency_info.get("name"),
            "currency_symbol": currency_info.get("symbol"),
            "independent": d.get("independent"),
            "un_member": d.get("unMember"),
            "latlng": d.get("latlng"),
            "driving_side": (d.get("car") or {}).get("side"),
            "start_of_week": d.get("startOfWeek"),
            "postal_code_format": (d.get("postalCode") or {}).get("format") if isinstance(d.get("postalCode"), dict) else None,
            "coat_of_arms_url": (d.get("coatOfArms") or {}).get("svg"),
        }

        self.query_name = self.basic.get("common_name") or self.country
        return self.basic

    def worldbank_latest(self, indicator):
        country_code = self.basic.get("country_code_alpha2")
        if not country_code:
            return None

        url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}"
        params = {"format": "json", "per_page": 1000, "date": f"1960:{CURRENT_YEAR}"}

        try:
            response = self.session.get(url, params=params, timeout=45)
            payload = response.json()

            rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []

            best = None
            best_year = 0

            for row in rows:
                value = row.get("value")
                if value is None:
                    continue
                try:
                    year = int(row.get("date", "0"))
                except Exception:
                    year = 0
                if year >= best_year:
                    best_year = year
                    best = {
                        "value": value,
                        "year": year,
                        "indicator": row.get("indicator", {}).get("value"),
                        "unit": row.get("unit"),
                    }

            return best
        except Exception as e:
            return {"error": str(e)}

    def fetch_economy(self):
        indicators = {
            "population": "SP.POP.TOTL",
            "urban_population_pct": "SP.URB.TOTL.IN.ZS",
            "literacy_rate_pct": "SE.ADT.LITR.ZS",
            "internet_users_pct": "IT.NET.USER.ZS",
            "gdp_usd": "NY.GDP.MKTP.CD",
            "gdp_per_capita_ppp_usd": "NY.GDP.PCAP.PP.CD",
            "gdp_growth_pct": "NY.GDP.MKTP.KD.ZG",
            "inflation_pct": "FP.CPI.TOTL.ZG",
            "unemployment_pct": "SL.UEM.TOTL.ZS",
            "gini_index": "SI.POV.GINI",
            "government_debt_pct_gdp": "GC.DOD.TOTL.GD.ZS",
            "current_account_balance_pct_gdp": "BN.CAB.XOKA.GD.ZS",
            "mobile_subscriptions_per_100": "IT.CEL.SETS.P2",
            "age_dependency_ratio": "SP.POP.DPND",
            "exports_pct_gdp": "NE.EXP.GNFS.ZS",
            "foreign_direct_investment_pct_gdp": "BX.KLT.DINV.WD.GD.ZS",
            "gdp_per_capita_growth_pct": "NY.GDP.PCAP.KD.ZG",
            "poverty_rate_pct": "SI.POV.DDAY",
        }

        economy = {}
        for key, indicator in indicators.items():
            self.log(f"World Bank: fetching {key}")
            economy[key] = self.worldbank_latest(indicator)
            time.sleep(0.25)

        economy["currency"] = {
            "code": self.basic.get("currency_code"),
            "name": self.basic.get("currency_name"),
            "symbol": self.basic.get("currency_symbol"),
        }
        economy["exchange_rate_usd"] = self.fetch_exchange(self.basic.get("currency_code"))
        return economy

    def fetch_exchange(self, currency_code):
        if not currency_code:
            return None
        if currency_code == "USD":
            return {"base": "USD", "target": "USD", "rate": 1.0, "date": TODAY, "source": "fixed"}

        try:
            response = self.session.get(
                "https://api.frankfurter.app/latest",
                params={"from": "USD", "to": currency_code},
                timeout=25,
            )
            if response.ok:
                data = response.json()
                rate = data.get("rates", {}).get(currency_code)
                if rate is not None:
                    return {
                        "base": "USD",
                        "target": currency_code,
                        "rate": rate,
                        "date": data.get("date"),
                        "source": "Frankfurter ECB",
                    }
        except Exception:
            pass

        try:
            response = self.session.get("https://open.er-api.com/v6/latest/USD", timeout=25)
            if response.ok:
                data = response.json()
                rate = data.get("rates", {}).get(currency_code)
                if rate is not None:
                    return {
                        "base": "USD",
                        "target": currency_code,
                        "rate": rate,
                        "date": data.get("time_last_update_utc"),
                        "source": "open.er-api.com",
                    }
        except Exception:
            pass

        return None

    def fetch_cities(self):
        cities = []

        if self.geonames_username and self.basic.get("country_code_alpha2"):
            try:
                response = self.session.get(
                    "https://secure.geonames.org/searchJSON",
                    params={
                        "country": self.basic.get("country_code_alpha2"),
                        "featureClass": "P",
                        "maxRows": 50,
                        "username": self.geonames_username,
                        "style": "full",
                    },
                    timeout=35,
                )
                if response.ok:
                    items = response.json().get("geonames", []) or []
                    items.sort(key=lambda x: safe_int(x.get("population")), reverse=True)
                    for item in items[: self.max_cities]:
                        cities.append(
                            {
                                "city": item.get("name"),
                                "admin1": item.get("adminName1"),
                                "population": safe_int(item.get("population")),
                                "lat": item.get("lat"),
                                "lng": item.get("lng"),
                                "source": "GeoNames",
                            }
                        )
            except Exception:
                pass

        if not cities:
            names = []
            for name in [self.query_name, self.basic.get("official_name"), self.country]:
                if name and name not in names:
                    names.append(name)

            for name in names:
                for payload_name in [name, name.lower()]:
                    try:
                        response = self.session.post(
                            "https://countriesnow.space/api/v0.1/countries/cities",
                            json={"country": payload_name},
                            timeout=35,
                        )
                        if response.ok:
                            data = response.json()
                            if not data.get("error") and isinstance(data.get("data"), list):
                                cities = [
                                    {"city": city, "source": "CountriesNow"}
                                    for city in data.get("data", [])[: self.max_cities]
                                ]
                                break
                    except Exception:
                        pass
                if cities:
                    break

        if not cities and self.basic.get("capital"):
            cities = [
                {
                    "city": self.basic.get("capital"),
                    "note": "capital city",
                    "source": "REST Countries",
                }
            ]

        return cities

    def fetch_wikipedia(self):
        title = quote(self.query_name.replace(" ", "_"))
        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"

        try:
            response = self.session.get(summary_url, timeout=25)
            if not response.ok:
                search_response = self.session.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "list": "search",
                        "srsearch": self.query_name,
                        "format": "json",
                        "srlimit": 1,
                    },
                    timeout=25,
                )
                if search_response.ok:
                    results = search_response.json().get("query", {}).get("search", [])
                    if results:
                        title = quote(results[0].get("title", "").replace(" ", "_"))
                        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
                        response = self.session.get(summary_url, timeout=25)

            if response.ok:
                data = response.json()
                return {
                    "title": data.get("title"),
                    "description": data.get("description"),
                    "extract": data.get("extract"),
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
                }
        except Exception:
            pass
        return None

    def fetch_news(self):
        base_query = f"{self.query_name} economy OR ecommerce OR tax OR consumer OR payments"
        items = self._google_news_rss(f"{base_query} when:1d")
        if not items:
            items = self._google_news_rss(base_query)
        return items[: self.max_news]

    def _google_news_rss(self, query):
        url = f"https://news.google.com/rss/search?q={quote(query)}&hl=en-US&gl=US&ceid=US:en"
        try:
            response = self.session.get(url, timeout=30)
            root = ET.fromstring(response.content)
            items = []
            for item in root.findall(".//item"):
                title_el = item.find("title")
                link_el = item.find("link")
                pub_el = item.find("pubDate")
                source_el = item.find("source")
                items.append(
                    {
                        "title": title_el.text.strip() if title_el is not None and title_el.text else None,
                        "link": link_el.text.strip() if link_el is not None and link_el.text else None,
                        "published": pub_el.text.strip() if pub_el is not None and pub_el.text else None,
                        "source": source_el.text.strip() if source_el is not None and source_el.text else None,
                    }
                )
            return items
        except Exception:
            return []

    def fetch_web_evidence(self):
        evidence = {}
        if not self.web_search_requested:
            return evidence
        if DDGS is None:
            self.log("DuckDuckGo search package is missing. Install with: pip install duckduckgo-search")
            return evidence

        queries = [
            ("module_04_tax_duties", f"{self.query_name} ecommerce tax VAT GST rate {CURRENT_YEAR}"),
            ("module_04_tax_duties", f"{self.query_name} import duty de minimis threshold ecommerce {CURRENT_YEAR}"),
            ("module_05_consumer_psychology", f"{self.query_name} online shopping consumer behavior {CURRENT_YEAR}"),
            ("module_06_consumption_preferences", f"{self.query_name} top ecommerce product categories {CURRENT_YEAR}"),
            ("module_07_shopping_seasonality", f"{self.query_name} biggest shopping festivals ecommerce {CURRENT_YEAR}"),
            ("module_08_digital_landscape", f"{self.query_name} internet social media ecommerce usage {CURRENT_YEAR}"),
            ("module_09_payment_infrastructure", f"{self.query_name} popular payment gateways digital wallets COD {CURRENT_YEAR}"),
            ("module_10_logistics_shipping", f"{self.query_name} ecommerce courier delivery companies shipping times {CURRENT_YEAR}"),
            ("module_11_legal_regulations", f"{self.query_name} ecommerce consumer protection data privacy law {CURRENT_YEAR}"),
            ("module_12_language_communication", f"{self.query_name} official languages ecommerce localization {CURRENT_YEAR}"),
            ("module_13_community_social", f"{self.query_name} family community influence buying decisions {CURRENT_YEAR}"),
            ("module_14_marketing_advertising", f"{self.query_name} digital marketing channels influencer ecommerce {CURRENT_YEAR}"),
            ("module_15_competition", f"{self.query_name} top ecommerce marketplaces market share {CURRENT_YEAR}"),
            ("module_16_customer_service", f"{self.query_name} ecommerce customer service returns expectations {CURRENT_YEAR}"),
            ("module_17_technology_infrastructure", f"{self.query_name} mobile android app ecommerce technology {CURRENT_YEAR}"),
            ("module_19_risk_compliance", f"{self.query_name} ecommerce fraud chargeback regulatory risk {CURRENT_YEAR}"),
            ("module_20_strategic_recommendations", f"{self.query_name} ecommerce market entry strategy {CURRENT_YEAR}"),
        ]

        try:
            ddgs = DDGS()
        except Exception as e:
            self.log(f"DuckDuckGo initialization failed: {e}")
            return evidence

        for module, query_text in queries:
            results = []
            try:
                results = list(ddgs.text(query_text, max_results=3, timelimit="m"))
            except Exception:
                try:
                    results = list(ddgs.text(query_text, max_results=3))
                except Exception as e2:
                    evidence.setdefault(module, []).append({"query": query_text, "error": str(e2)})

            for result in results[:3]:
                evidence.setdefault(module, []).append(
                    {
                        "query": query_text,
                        "title": result.get("title"),
                        "href": result.get("href"),
                        "snippet": (result.get("body") or "")[:500],
                    }
                )
            time.sleep(1.2)

        return evidence

    def compact_evidence(self, evidence):
        compact = {}
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

    def build_ai_input(self, demographics, economy, news, evidence):
        demo = dict(demographics)
        cities = demo.get("major_cities") or []
        demo["major_cities"] = [
            city.get("city") if isinstance(city, dict) else city for city in cities[:10]
        ]
        econ = {key: value for key, value in economy.items() if value not in (None, "", [], {})}

        # Compute derived insights for the AI
        gdp_pc = None
        if isinstance(economy.get("gdp_per_capita_ppp_usd"), dict):
            try:
                gdp_pc = float(economy["gdp_per_capita_ppp_usd"].get("value", 0))
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

        return {
            "country": self.query_name,
            "today": TODAY,
            "basic_facts": self.basic,
            "income_tier": income_tier,
            "demographics": demo,
            "economy": econ,
            "latest_news_titles": [item.get("title") for item in news[:10]],
            "web_evidence": self.compact_evidence(evidence),
        }

    def build_prompt(self, ai_input):
        facts_json = json.dumps(ai_input, ensure_ascii=False, indent=2)
        if len(facts_json) > 90000:
            facts_json = facts_json[:90000] + "\n... truncated"

        prompt = f"""You are an expert e-commerce country research analyst.

Today is {TODAY}.

Use only the provided facts, latest news titles, and web evidence.
If evidence is missing, do not invent exact legal or tax numbers.
Use "unknown" for missing fields.
If you provide a number, mention uncertainty in verification_notes unless evidence clearly supports it.
Use sources arrays when evidence URLs are available.
Return ONLY valid JSON.
Do not include markdown.
Do not include comments.
Do not include trailing commas.

PROVIDED DATA:
{facts_json}

Return JSON matching this schema:
{json.dumps(AI_SCHEMA, indent=2)}
"""
        return prompt

    def ollama_tags(self):
        try:
            response = self.session.get("http://localhost:11434/api/tags", timeout=5)
            if response.ok:
                return response.json().get("models", [])
        except Exception:
            pass
        return None

    def select_ollama_model(self):
        models = self.ollama_tags()
        if not models:
            return None
        names = [model.get("name") for model in models if model.get("name")]
        if not names:
            return None
        if self.ollama_model in names:
            return self.ollama_model
        base_requested = self.ollama_model.split(":")[0]
        for name in names:
            if name.split(":")[0] == base_requested:
                return name
        return names[0]

    def parse_json_text(self, text):
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

    def generate_ai_modules(self, ai_input):
        if not self.use_ollama:
            self.log("Ollama disabled by configuration.")
            return None

        model = self.select_ollama_model()
        if not model:
            self.log("Ollama is not running or no local model is installed. Install Ollama and run: ollama pull llama3.1")
            return None

        self.ai_backend = f"ollama:{model}"
        self.log(f"Using local Ollama model: {model}")

        prompt = self.build_prompt(ai_input)
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2, "num_ctx": 8192},
        }

        try:
            response = self.session.post("http://localhost:11434/api/chat", json=payload, timeout=900)
            response.raise_for_status()
            data = response.json()
            if data.get("error"):
                raise Exception(data.get("error"))
            content = data.get("message", {}).get("content", "")
            parsed = self.parse_json_text(content)
            if parsed is None:
                self.log("Ollama returned invalid JSON.")
            return parsed
        except Exception as e:
            self.log(f"Ollama generation failed: {e}")
            return None

    def placeholder_modules(self, evidence):
        placeholders = {}
        for module in QUAL_MODULES:
            has_evidence = bool(evidence.get(module))
            placeholders[module] = {
                "status": "raw_evidence_only" if has_evidence else "needs_local_ai_or_manual_research",
                "message": "Install Ollama and a local model to auto-generate this module, or review evidence below.",
                "confidence": "low",
                "evidence": evidence.get(module, []),
            }
        return placeholders

    def apply_ai_modules(self, final, ai_modules, evidence):
        placeholders = self.placeholder_modules(evidence)
        if not isinstance(ai_modules, dict):
            ai_modules = {}

        for module in QUAL_MODULES:
            ai_part = ai_modules.get(module)
            if module == "module_18_news_current_context":
                final.setdefault(module, {})
                if isinstance(ai_part, dict):
                    final[module].update(ai_part)
                else:
                    final[module].update(placeholders[module])
                if evidence.get(module):
                    final[module].setdefault("evidence", evidence.get(module, []))
            else:
                if isinstance(ai_part, dict):
                    final[module] = ai_part
                else:
                    final[module] = placeholders[module]
                if evidence.get(module):
                    final[module].setdefault("evidence", evidence.get(module, []))

        extra = {key: value for key, value in ai_modules.items() if key not in QUAL_MODULES}
        if extra:
            final["additional_ai_modules"] = extra

    def build_meta(self, demographics, economy, news, evidence):
        world_bank_years = {}
        for section_name, section in (("demographics", demographics), ("economy", economy)):
            for key, value in section.items():
                if isinstance(value, dict) and value.get("year"):
                    world_bank_years[f"{section_name}.{key}"] = value.get("year")

        exchange = economy.get("exchange_rate_usd") or {}
        exchange_date = exchange.get("date") or exchange.get("time") or exchange.get("source")

        data_sources = [
            "REST Countries API",
            "World Bank Open Data API",
            "Frankfurter ECB exchange rates",
            "open.er-api.com exchange rates fallback",
            "CountriesNow API",
            "Wikipedia REST API",
            "Google News RSS",
        ]
        if self.geonames_username:
            data_sources.append("GeoNames API")
        if self.enable_web_search:
            data_sources.append("DuckDuckGo search evidence")
        if self.ai_backend != "none":
            data_sources.append("Local Ollama LLM")

        return {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "country_input": self.country,
            "resolved_country_name": self.query_name,
            "report_date": TODAY,
            "data_sources": data_sources,
            "ai_backend": self.ai_backend,
            "freshness": {
                "exchange_rate_date": exchange_date,
                "world_bank_latest_years": world_bank_years,
                "news_count": len(news),
                "web_evidence_enabled": self.enable_web_search,
                "web_evidence_modules_count": len(
                    [key for key, value in evidence.items() if isinstance(value, list) and value]
                ),
            },
            "disclaimer": (
                "This report combines free public APIs, latest news, web evidence, "
                "and optional local AI analysis. Tax, legal, payment, and compliance "
                "fields can change frequently. Verify critical fields with official "
                "government, tax authority, payment gateway, and legal sources before "
                "using them in production commerce logic."
            ),
        }

    def write_markdown(self, report, md_file):
        title = report.get("module_01_country_identity", {}).get("official_name") or self.country
        lines = []
        lines.append(f"# {title} — E-commerce Country Research")
        lines.append("")
        meta = report.get("meta", {})
        lines.append(f"Generated: {meta.get('generated_at_utc')} | "
                      f"Data confidence: {meta.get('overall_confidence', 'N/A')}")
        lines.append("")

        def section_heading(name, level=2):
            return f"{'#' * level} {name.replace('_', ' ').title()}"

        def as_table(data, cols=3):
            if isinstance(data, dict):
                items = list(data.items())
            else:
                return ""
            rows = []
            for i in range(0, len(items), cols):
                row = []
                for j in range(cols):
                    if i + j < len(items):
                        k, v = items[i + j]
                        val = str(v) if v is not None else ""
                        if isinstance(val, str) and len(val) > 60:
                            val = val[:60] + "..."
                        row.append(f"{k}: {val}")
                rows.append("| " + " | ".join(row) + " |")
            if rows:
                return "\n".join(rows)
            return ""

        def fmt_module(module_data):
            if not isinstance(module_data, dict):
                return str(module_data)
            out = []
            confidence = module_data.pop("confidence", None)
            notes = module_data.pop("verification_notes", None)
            sources = module_data.pop("sources", [])
            list_keys = {k for k, v in module_data.items() if isinstance(v, list)}
            simple = {k: v for k, v in module_data.items() if k not in list_keys}
            if simple:
                out.append(as_table(simple, cols=2))
            for key in sorted(list_keys):
                vals = module_data.get(key, [])
                if vals:
                    out.append(f"\n**{key.replace('_', ' ').title()}:**")
                    for item in vals:
                        if isinstance(item, dict):
                            out.append(f"- _{json.dumps(item, ensure_ascii=False)}_")
                        else:
                            out.append(f"- {item}")
            if notes:
                out.append(f"\n*Verification: {notes}*")
            if confidence:
                out.append(f"\n**Confidence:** {confidence}")
            if sources:
                out.append(f"\n**Sources:** {', '.join(sources[:5])}")
                if len(sources) > 5:
                    out.append(f"... and {len(sources) - 5} more")
            if confidence:
                module_data["confidence"] = confidence
            if notes:
                module_data["verification_notes"] = notes
            if sources:
                module_data["sources"] = sources
            return "\n".join(out)

        module_order = [
            "meta",
            "module_01_country_identity",
            "module_02_demographics",
            "module_03_economy_wealth",
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
            "appendix_web_evidence",
        ]

        for key in module_order:
            value = report.get(key)
            if value is None:
                continue
            if key == "meta":
                lines.append("## Report Metadata")
                lines.append("")
                lines.append(as_table(meta, cols=2))
                lines.append("")
                continue
            if key == "appendix_web_evidence":
                lines.append(section_heading(key))
                lines.append("")
                ev_count = sum(len(v) for v in value.values() if isinstance(v, list))
                lines.append(f"*{ev_count} evidence items collected from web search.*")
                lines.append("")
                if isinstance(value, dict):
                    for src, items in value.items():
                        if items and isinstance(items, list):
                            lines.append(f"**{src}:** {len(items)} items")
                            for it in items[:3]:
                                if isinstance(it, dict):
                                    snippet = it.get("snippet", it.get("text", ""))
                                    link = it.get("link", "")
                                    if snippet:
                                        lines.append(f"- {snippet[:200]}")
                                    if link:
                                        lines.append(f"  [{link}]({link})")
                            if len(items) > 3:
                                lines.append(f"  ... and {len(items) - 3} more items")
                lines.append("")
                continue
            lines.append(section_heading(key))
            lines.append("")
            if key == "module_01_country_identity":
                identity = dict(value)
                identity.pop("wikipedia_summary", None)
                lines.append(as_table(identity, cols=2))
                lines.append("")
                wiki = value.get("wikipedia_summary")
                if wiki:
                    lines.append("**Wikipedia Summary:**")
                    lines.append("")
                    lines.append(wiki[:2000])
                    lines.append("")
            elif key == "module_02_demographics":
                lines.append(as_table(value, cols=2))
                lines.append("")
            elif key == "module_03_economy_wealth":
                lines.append(as_table(value, cols=2))
                lines.append("")
            else:
                lines.append(fmt_module(value))
                lines.append("")

        with open(md_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def run(self):
        self.log("=" * 70)
        self.log(f"Free E-commerce Country Research: {self.country}")
        self.log("=" * 70)

        self.fetch_basic()
        self.log("Basic country facts fetched.")

        economy = self.fetch_economy()
        self.log("Economic indicators fetched.")

        demographic_keys = ["population", "urban_population_pct", "literacy_rate_pct", "internet_users_pct"]
        demographics = {key: economy.pop(key, None) for key in demographic_keys}
        demographics["population_restcountries"] = self.basic.get("population")
        demographics["major_cities"] = self.fetch_cities()
        self.log("Cities fetched.")

        wiki = self.fetch_wikipedia()
        self.log("Wikipedia summary fetched.")

        news = self.fetch_news()
        self.log(f"News fetched: {len(news)} items.")

        evidence = self.fetch_web_evidence()
        evidence_count = sum(len(value) for value in evidence.values() if isinstance(value, list))
        self.log(f"Web evidence fetched: {evidence_count} items.")

        ai_input = self.build_ai_input(demographics, economy, news, evidence)
        ai_modules = self.generate_ai_modules(ai_input)

        final = {
            "module_01_country_identity": {**self.basic, "wikipedia_summary": wiki},
            "module_02_demographics": demographics,
            "module_03_economy_wealth": economy,
            "module_18_news_current_context": {
                "latest_news_rss": news,
                "query_note": "Google News RSS latest available items",
            },
        }

        self.apply_ai_modules(final, ai_modules, evidence)

        final = {
            "meta": self.build_meta(demographics, economy, news, evidence),
            **final,
            "appendix_web_evidence": evidence,
        }

        base = re.sub(r"[^A-Za-z0-9_-]+", "_", self.country.strip()).strip("_")
        if not base:
            base = "country"

        json_file = f"{base}_free_ecommerce_report.json"
        md_file = f"{base}_free_ecommerce_report.md"

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(final, f, indent=2, ensure_ascii=False)

        self.write_markdown(final, md_file)

        self.log("")
        self.log("Research completed.")
        self.log(f"JSON report saved: {json_file}")
        self.log(f"Markdown report saved: {md_file}")

        return final


def main():
    country = sys.argv[1].strip() if len(sys.argv) > 1 else input("Enter country name for e-commerce research: ").strip()
    if not country:
        print("Country name is required.")
        sys.exit(1)

    researcher = FreeEcommerceCountryResearch(
        country=country,
        use_ollama=os.getenv("USE_OLLAMA", "1") != "0",
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1"),
        enable_web_search=os.getenv("ENABLE_WEB_SEARCH", "1") != "0",
        geonames_username=os.getenv("GEONAMES_USERNAME"),
    )
    researcher.run()


if __name__ == "__main__":
    main()