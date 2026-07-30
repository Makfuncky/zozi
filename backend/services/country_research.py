from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ── Default data for modules 4–20 when AI research is not available ──────────

DEFAULT_MODULES: dict[str, dict] = {
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
        "confidence": "low",
        "verification_notes": "Derived from basic country data. Verify with local tax authority.",
        "sources": ["Auto-populate heuristic"],
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
        "confidence": "low",
        "verification_notes": "Requires local AI or market research.",
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
        "confidence": "low",
        "verification_notes": "Requires local AI or market research.",
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
        "confidence": "low",
        "verification_notes": "Requires local AI or market research.",
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
        "confidence": "low",
        "verification_notes": "Requires local AI or market research.",
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
        "confidence": "low",
        "verification_notes": "Requires local AI or market research.",
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
        "confidence": "low",
        "verification_notes": "Requires local AI or market research.",
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
        "confidence": "low",
        "verification_notes": "Requires local AI or market research.",
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
        "confidence": "low",
        "verification_notes": "Requires local AI or market research.",
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
        "confidence": "low",
        "verification_notes": "Requires local AI or market research.",
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
        "confidence": "low",
        "verification_notes": "Requires local AI or market research.",
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
        "confidence": "low",
        "verification_notes": "Requires local AI or market research.",
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
        "confidence": "low",
        "verification_notes": "Requires local AI or market research.",
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
        "confidence": "low",
        "verification_notes": "Requires local AI or market research.",
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
        "confidence": "low",
        "verification_notes": "Derived from basic country data. Verify with compliance team.",
        "sources": ["Auto-populate heuristic"],
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
        "confidence": "low",
        "verification_notes": "Requires AI-generated strategic analysis.",
        "sources": [],
    },
}


def _safe_val(val: Any, default: Any = "") -> Any:
    if val is None:
        return default
    return val


def _pop_val(data: dict, key: str, default: Any = "") -> Any:
    return _safe_val(data.get(key), default)


def build_country_research(auto_populate_result: dict) -> dict:
    """Build the full 20-module country research report from auto-populate data.

    Args:
        auto_populate_result: The dict returned by auto_populate_country().

    Returns:
        A dict with all 20 modules + meta information.
    """
    ap = auto_populate_result

    # ── Module 01: Country Identity & Basics ──────────────────────────────
    module_01 = {
        "official_name": _pop_val(ap, "official_name"),
        "common_name": _pop_val(ap, "name"),
        "country_code_alpha2": _pop_val(ap, "code"),
        "country_code_alpha3": _pop_val(ap, "alpha3"),
        "numeric_code": _pop_val(ap, "numeric_code"),
        "capital": _pop_val(ap, "capital"),
        "flag_url": _pop_val(ap, "flag_url"),
        "region": _pop_val(ap, "region"),
        "subregion": _pop_val(ap, "", "subregion"),
        "area_km2": _pop_val(ap, "area_km2"),
        "population": _pop_val(ap, "population"),
        "timezone": _pop_val(ap, "timezone"),
        "language": _pop_val(ap, "language"),
        "languages": _pop_val(ap, "languages", []),
        "currencies": _pop_val(ap, "currencies", []),
        "currency_code": _pop_val(ap, "currency"),
        "currency_symbol": _pop_val(ap, "currency_symbol"),
        "currency_name": _pop_val(ap, "currency_name"),
        "phone_code": _pop_val(ap, "phone_code"),
        "latitude": _pop_val(ap, "latitude"),
        "longitude": _pop_val(ap, "longitude"),
        "google_maps": _pop_val(ap, "google_maps"),
        "confidence": "high",
        "sources": ["REST Countries API"],
    }

    # ── Module 02: Demographics & Population ──────────────────────────────
    module_02 = {
        "total_population": _pop_val(ap, "population"),
        "internet_penetration_pct": _pop_val(ap, "internet_penetration_pct"),
        "economic_tier": _pop_val(ap, "economic_tier"),
        "gdp_per_capita_usd": _pop_val(ap, "gdp_per_capita_usd"),
        "urban_population_pct": _pop_val(ap, "urban_population_pct"),
        "literacy_rate_pct": _pop_val(ap, "literacy_rate_pct"),
        "cities_count": len(_pop_val(ap, "cities", [])),
        "top_cities": [
            {
                "name": c.get("name"),
                "population": c.get("population"),
                "is_capital": c.get("is_capital", False),
            }
            for c in _pop_val(ap, "cities", [])[:10]
        ],
        "public_holidays_count": len(_pop_val(ap, "public_holidays", [])),
        "languages": _pop_val(ap, "languages", []),
        "confidence": "high",
        "sources": ["REST Countries API", "World Bank API"],
    }

    # ── Module 03: Economy & Wealth ───────────────────────────────────────
    module_03 = {
        "currency_code": _pop_val(ap, "currency"),
        "currency_symbol": _pop_val(ap, "currency_symbol"),
        "currency_name": _pop_val(ap, "currency_name"),
        "gdp_usd": _pop_val(ap, "gdp_usd"),
        "gdp_per_capita_usd": _pop_val(ap, "gdp_per_capita_usd"),
        "gdp_per_capita_ppp_usd": _pop_val(ap, "gdp_per_capita_ppp_usd"),
        "gdp_growth_pct": _pop_val(ap, "gdp_growth_pct"),
        "inflation_pct": _pop_val(ap, "inflation_pct"),
        "unemployment_pct": _pop_val(ap, "unemployment_pct"),
        "gini_index": _pop_val(ap, "gini_index"),
        "government_debt_pct_gdp": _pop_val(ap, "government_debt_pct_gdp"),
        "current_account_balance_pct_gdp": _pop_val(ap, "current_account_balance_pct_gdp"),
        "population": _pop_val(ap, "population"),
        "internet_penetration_pct": _pop_val(ap, "internet_penetration_pct"),
        "urban_population_pct": _pop_val(ap, "urban_population_pct"),
        "literacy_rate_pct": _pop_val(ap, "literacy_rate_pct"),
        "economic_tier": _pop_val(ap, "economic_tier"),
        "tax_type": _pop_val(ap, "tax_type"),
        "tax_rate": _pop_val(ap, "tax_rate"),
        "tax_name": _pop_val(ap, "tax_name"),
        "confidence_score": _pop_val(ap, "confidence_score"),
        "confidence": "medium",
        "sources": ["World Bank API", "Auto-populate heuristic"],
    }

    # ── Module 18: News & Current Context ────────────────────────────────
    module_18 = {
        "current_context_summary": "",
        "political_stability": "",
        "recent_regulatory_changes": [],
        "natural_disasters_disruptions": [],
        "consumer_sentiment_index": "",
        "trending_products_viral_items": [],
        "exchange_rate_volatility_current": "",
        "confidence": "low",
        "verification_notes": "Requires live news fetch or AI analysis.",
        "sources": [],
    }

    # ── Assemble final report ─────────────────────────────────────────────
    modules = {
        "module_01_country_identity": module_01,
        "module_02_demographics": module_02,
        "module_03_economy_wealth": module_03,
        **{k: dict(v) for k, v in DEFAULT_MODULES.items()},
        "module_18_news_current_context": module_18,
    }

    # Override module_07 seasonality with public holidays if available
    holidays = _pop_val(ap, "public_holidays", [])
    if holidays:
        modules["module_07_shopping_seasonality"]["major_shopping_festivals"] = [
            {"name": h.get("name"), "date": h.get("date"), "local_name": h.get("local_name")}
            for h in holidays[:10]
        ]
        modules["module_07_shopping_seasonality"]["confidence"] = "medium"
        modules["module_07_shopping_seasonality"]["sources"] = ["Nager.Date public holidays API"]

    # Override module_11 legal with existing legal rules from auto-populate
    legal_rules = _pop_val(ap, "legal_rules", {})
    if legal_rules:
        modules["module_11_legal_regulations"]["mandatory_return_refund_window"] = str(_pop_val(legal_rules, "return_window_days", ""))
        modules["module_11_legal_regulations"]["consumer_protection_law"] = f"Return window: {legal_rules.get('return_window_days')} days"
        modules["module_11_legal_regulations"]["prohibited_restricted_items_for_sale"] = _pop_val(legal_rules, "product_restrictions", [])
        modules["module_11_legal_regulations"]["age_verification_requirements"] = f"Minimum order age: {legal_rules.get('minimum_order_age')}"
        modules["module_11_legal_regulations"]["confidence"] = "medium"
        modules["module_11_legal_regulations"]["sources"] = ["Auto-populate legal rules"]

    # Override module_09 payment with auto-populate payment data
    payment_gateways = _pop_val(ap, "payment_gateways", [])
    if payment_gateways:
        modules["module_09_payment_infrastructure"]["top_5_payment_gateways"] = [
            {"name": gw.get("name"), "type": gw.get("type"), "fee_percentage": gw.get("fee_percentage")}
            for gw in payment_gateways[:5]
        ]
        modules["module_09_payment_infrastructure"]["confidence"] = "medium"
        modules["module_09_payment_infrastructure"]["sources"] = ["Auto-populate gateway registry"]

    # Override module_19 risk with auto-populate data
    fraud_tier = _pop_val(ap, "fraud_risk_tier")
    if fraud_tier:
        modules["module_19_risk_compliance"]["fraud_chargeback_rate"] = str(fraud_tier)
        modules["module_19_risk_compliance"]["confidence"] = "medium"
        modules["module_19_risk_compliance"]["sources"] = ["Auto-populate heuristic"]

    # Override module_10 logistics with auto-populate data
    logistics_model = _pop_val(ap, "logistics_model")
    if logistics_model:
        modules["module_10_logistics_shipping"]["last_mile_delivery_quality"] = logistics_model
        modules["module_10_logistics_shipping"]["package_tracking_expectation"] = "Standard tracking expected"
        modules["module_10_logistics_shipping"]["confidence"] = "medium"
        modules["module_10_logistics_shipping"]["sources"] = ["Auto-populate heuristic"]

    # Override module_17 technology with data privacy info
    data_privacy = _pop_val(ap, "data_privacy_framework")
    data_residency = _pop_val(ap, "data_residency_tier")
    if data_privacy:
        modules["module_17_technology_infrastructure"]["cloud_hosting_regulations"] = f"Data privacy framework: {data_privacy}, Residency tier: {data_residency}"
        modules["module_17_technology_infrastructure"]["confidence"] = "medium"
        modules["module_17_technology_infrastructure"]["sources"] = ["Auto-populate heuristic"]

    # Build meta
    meta = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "country_code": _pop_val(ap, "code"),
        "country_name": _pop_val(ap, "name"),
        "source": "auto-populate",
        "data_sources": [
            "REST Countries API",
            "World Bank API",
            "Nager.Date public holidays API",
            "Auto-populate heuristic engine",
        ],
        "overall_confidence": _calculate_overall_confidence(modules),
        "modules_available": len([k for k in modules if modules[k].get("confidence") in ("medium", "high")]),
        "modules_total": len(modules),
    }

    return {
        "meta": meta,
        **modules,
    }


def _calculate_overall_confidence(modules: dict[str, dict]) -> str:
    confidences = [m.get("confidence", "low") for m in modules.values()]
    if all(c == "high" for c in confidences):
        return "high"
    if any(c == "high" for c in confidences):
        return "medium"
    return "low"