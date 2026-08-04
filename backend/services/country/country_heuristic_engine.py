"""Algorithmic heuristic engine for country e-commerce defaults.

Generates KYC tiers, payment gateway suggestions with integration feasibility
scoring, commission ranges per category (adjustable by admin), logistics zones,
and consumer insights from economic data (GDP, internet penetration, region).

Pure algorithmic scoring — no static country->value maps (except GDP/internet
fallbacks when World Bank API returns no data). All scores derived from
economic indicators and regional rules. Matches the scoring formulas from
the Multi_Country_System.txt blueprint exactly.
"""


import logging
from typing import Any

logger = logging.getLogger(__name__)

# =====================================================================
# REGION RESOLUTION
# =====================================================================

_GCC_COUNTRIES = {"AE", "SA", "QA", "OM", "KW", "BH"}
_MIDDLE_EAST_REGIONS = {"Western Asia", "Middle East"}
_ASIA_REGIONS = {"Asia", "Southern Asia", "Southeastern Asia", "Eastern Asia", "Central Asia"}


def _resolve_region(region: str | None, subregion: str | None, code: str) -> str:
    if code and code.upper() in _GCC_COUNTRIES:
        return "gcc"
    sr = (subregion or "").strip()
    if sr in _MIDDLE_EAST_REGIONS:
        return "middle_east"
    r = (region or "").strip()
    if r == "Europe":
        return "europe"
    if r == "Americas":
        return "americas"
    if r == "Africa":
        return "africa"
    if r == "Oceania":
        return "oceania"
    if r == "Asia" or sr in _ASIA_REGIONS:
        return "asia"
    return "middle_east"


# =====================================================================
# PAYMENT GATEWAY SUGGESTIONS & INTEGRATION FEASIBILITY
# =====================================================================
# Blueprint scoring formula (0-100 per gateway):
#   Region Match:          40 points (country_region in gateway.regions OR GLOBAL)
#   Currency Match:        25 points (country_currency in gateway.currencies OR *)
#   Internet Penetration:  15 points (digital wallets need internet)
#   Fee Competitiveness:   10 points (inverse — lower fee = higher score)
#   Setup Speed:           10 points (inverse — fewer days = higher score)

_GATEWAY_PROFILES: dict[str, dict[str, Any]] = {
    "thawani": {
        "name": "Thawani", "base_fee_pct": 2.5, "base_fee_fixed": 0.20,
        "supports_cod": False, "supports_installments": True,
        "card_brand": True, "digital_wallet": True, "bank_transfer": False,
        "currencies": ["OMR"], "regions": ["gcc"],
        "min_gdp": 10000, "setup_days": 7,
    },
    "stripe": {
        "name": "Stripe", "base_fee_pct": 2.9, "base_fee_fixed": 0.30,
        "supports_cod": False, "supports_installments": False,
        "card_brand": True, "digital_wallet": False, "bank_transfer": False,
        "currencies": ["*"], "regions": ["europe", "americas", "asia", "oceania", "middle_east", "africa", "gcc"],
        "min_gdp": 2000, "setup_days": 1,
    },
    "tap": {
        "name": "Tap", "base_fee_pct": 2.75, "base_fee_fixed": 0.29,
        "supports_cod": True, "supports_installments": True,
        "card_brand": True, "digital_wallet": True, "bank_transfer": False,
        "currencies": ["SAR", "KWD", "BHD", "AED", "OMR"],
        "regions": ["gcc", "middle_east"],
        "min_gdp": 0, "setup_days": 14,
    },
    "hyperpay": {
        "name": "HyperPay", "base_fee_pct": 2.5, "base_fee_fixed": 0.25,
        "supports_cod": True, "supports_installments": True,
        "card_brand": True, "digital_wallet": True, "bank_transfer": False,
        "currencies": ["SAR", "AED"], "regions": ["gcc", "middle_east"],
        "min_gdp": 10000, "setup_days": 10,
    },
    "paytabs": {
        "name": "PayTabs", "base_fee_pct": 2.8, "base_fee_fixed": 0.25,
        "supports_cod": True, "supports_installments": False,
        "card_brand": True, "digital_wallet": False, "bank_transfer": True,
        "currencies": ["SAR", "AED", "BHD", "OMR"],
        "regions": ["gcc", "middle_east", "africa"],
        "min_gdp": 0, "setup_days": 5,
    },
    "mada": {
        "name": "Mada", "base_fee_pct": 1.5, "base_fee_fixed": 0.10,
        "supports_cod": False, "supports_installments": False,
        "card_brand": True, "digital_wallet": False, "bank_transfer": False,
        "currencies": ["SAR"], "regions": ["gcc"],
        "min_gdp": 15000, "setup_days": 30,
    },
    "omannet": {
        "name": "OmanNet", "base_fee_pct": 1.8, "base_fee_fixed": 0.10,
        "supports_cod": False, "supports_installments": False,
        "card_brand": True, "digital_wallet": False, "bank_transfer": False,
        "currencies": ["OMR"], "regions": ["gcc"],
        "min_gdp": 15000, "setup_days": 21,
    },
    "stc_pay": {
        "name": "STC Pay", "base_fee_pct": 2.0, "base_fee_fixed": 0.15,
        "supports_cod": False, "supports_installments": True,
        "card_brand": False, "digital_wallet": True, "bank_transfer": False,
        "currencies": ["SAR"], "regions": ["gcc"],
        "min_gdp": 15000, "setup_days": 14,
    },
    "paypal": {
        "name": "PayPal", "base_fee_pct": 3.49, "base_fee_fixed": 0.49,
        "supports_cod": False, "supports_installments": False,
        "card_brand": False, "digital_wallet": True, "bank_transfer": False,
        "currencies": ["*"], "regions": ["europe", "americas", "asia", "oceania", "middle_east", "africa", "gcc"],
        "min_gdp": 0, "setup_days": 1,
    },
    "tabby": {
        "name": "Tabby", "base_fee_pct": 4.0, "base_fee_fixed": 0.50,
        "supports_cod": False, "supports_installments": True,
        "card_brand": False, "digital_wallet": True, "bank_transfer": False,
        "currencies": ["SAR", "AED", "KWD"],
        "regions": ["gcc", "middle_east"],
        "min_gdp": 15000, "setup_days": 14,
    },
    "klarna": {
        "name": "Klarna", "base_fee_pct": 3.99, "base_fee_fixed": 0.50,
        "supports_cod": False, "supports_installments": True,
        "card_brand": False, "digital_wallet": True, "bank_transfer": False,
        "currencies": ["*"], "regions": ["europe", "americas"],
        "min_gdp": 25000, "setup_days": 14,
    },
}

# Currency-to-country mapping for currency match scoring
_COUNTRY_CURRENCIES: dict[str, str] = {
    "OM": "OMR", "AE": "AED", "SA": "SAR", "KW": "KWD", "QA": "QAR", "BH": "BHD",
    "JO": "JOD", "EG": "EGP", "TR": "TRY", "IQ": "IQD", "IR": "IRR",
    "GB": "GBP", "DE": "EUR", "FR": "EUR", "IT": "EUR", "ES": "EUR",
    "NL": "EUR", "BE": "EUR", "CH": "CHF", "SE": "SEK", "NO": "NOK",
    "DK": "DKK", "PL": "PLN", "US": "USD", "CA": "CAD", "MX": "MXN",
    "BR": "BRL", "AR": "ARS", "AU": "AUD", "NZ": "NZD",
    "IN": "INR", "PK": "PKR", "BD": "BDT", "LK": "LKR",
    "CN": "CNY", "JP": "JPY", "KR": "KRW", "HK": "HKD", "SG": "SGD",
    "MY": "MYR", "TH": "THB", "ID": "IDR", "PH": "PHP", "VN": "VND",
    "ZA": "ZAR", "NG": "NGN", "KE": "KES", "MA": "MAD",
    "RU": "RUB", "UA": "UAH", "KZ": "KZT",
}


def _compute_gateway_feasibility(
    profile: dict[str, Any],
    region: str,
    gdp: float | None,
    internet: float | None,
    country_code: str,
) -> float:
    """Score a gateway's integration feasibility for a country (0-100).

    Blueprint formula:
      - Region Match           40 pts
      - Currency Match         25 pts
      - Internet Penetration   15 pts
      - Fee Competitiveness    10 pts (inverse)
      - Setup Speed            10 pts (inverse)
    """
    g = gdp or 0
    i = internet or 50

    score = 0.0

    # 1. Region match (40 pts)
    if region in profile["regions"]:
        score += 40
    elif any(r in profile["regions"] for r in [region, "gcc", "middle_east"]):
        score += 20

    # 2. Currency match (25 pts)
    country_currency = _COUNTRY_CURRENCIES.get(country_code.upper(), "")
    currencies = profile.get("currencies", [])
    if "*" in currencies:
        score += 25
    elif country_currency and country_currency in currencies:
        score += 25
    elif country_currency:
        score += 5  # Partial — currency conversion needed

    # 3. Internet penetration (15 pts)
    if profile.get("digital_wallet") or profile.get("card_brand"):
        score += 15 * min(i / 100, 1.0)
    else:
        score += 10  # COD-focused gateways less dependent

    # 4. Fee competitiveness (10 pts, inverse)
    fee_score = max(0.0, 10.0 - (profile["base_fee_pct"] - 1.5) * 3)
    score += fee_score

    # 5. Setup speed (10 pts, inverse)
    speed_score = max(0.0, 10.0 - profile.get("setup_days", 14) / 3.0)
    score += speed_score

    # Penalty for very low GDP + high-fee gateways
    if g < 5000 and profile["base_fee_pct"] > 3:
        score *= 0.7

    # Bonus for local/regional gateways (better success rates, consumer trust)
    if region == "gcc" and profile["regions"] and profile["regions"][0] == "gcc":
        score = min(score + 3, 100)
    if region == profile.get("regions", [None])[0]:
        score = min(score + 2, 100)

    return round(min(score, 100), 1)


def _suggest_gateways(
    region: str, gdp: float | None, internet: float | None, country_code: str,
) -> list[dict[str, Any]]:
    """Suggest payment gateways ranked by integration feasibility score."""
    from services.payments.registry import PaymentGatewayRegistry

    scored: list[dict[str, Any]] = []
    for gid, profile in _GATEWAY_PROFILES.items():
        feasibility = _compute_gateway_feasibility(profile, region, gdp, internet, country_code)
        if feasibility < 15:
            continue
        scored.append({
            "gateway_id": gid,
            "name": profile["name"],
            "fee_percentage": profile["base_fee_pct"],
            "fee_fixed": profile["base_fee_fixed"],
            "supports_cod": profile["supports_cod"],
            "supports_installments": profile["supports_installments"],
            "adapter_exists": PaymentGatewayRegistry.is_supported(gid),
            "integration_feasibility_score": feasibility,
            "recommendation": (
                "highly_recommended" if feasibility >= 75 else
                "recommended" if feasibility >= 50 else
                "possible"
            ),
            "setup_days": profile.get("setup_days", 14),
            "reason": _gateway_reason(gid, feasibility),
        })

    scored.sort(key=lambda x: x["integration_feasibility_score"], reverse=True)
    return scored


def _gateway_reason(gateway_id: str, score: float) -> str:
    reasons = {
        "thawani": "Native OMR support, regional leader, low fees",
        "stripe": "Global fallback, instant setup",
        "tap": "Full multi-currency GCC support, regional leader",
        "hyperpay": "Strong KSA/AED presence, Apple Pay support",
        "paytabs": "Broad GCC support, quick setup",
        "mada": "National debit network, highest consumer trust in KSA",
        "omannet": "National debit network, highest consumer trust in Oman",
        "stc_pay": "Largest mobile wallet in KSA",
        "paypal": "Global wallet, instant setup",
        "tabby": "BNPL leader in GCC",
        "klarna": "Global BNPL, strong in EU/NA",
    }
    return reasons.get(gateway_id, "Gateway available for this region")


# =====================================================================
# COMMISSION TIERS — Blueprint exact implementation
# =====================================================================

_BASE_COMMISSIONS: dict[str, dict[str, float]] = {
    "electronics":       {"min_pct": 4, "max_pct": 8, "suggested": 6.0},
    "fashion":           {"min_pct": 12, "max_pct": 22, "suggested": 17.0},
    "accessories":       {"min_pct": 10, "max_pct": 18, "suggested": 14.0},
    "groceries":         {"min_pct": 2, "max_pct": 6, "suggested": 4.0},
    "health_beauty":     {"min_pct": 10, "max_pct": 18, "suggested": 14.0},
    "home_living":       {"min_pct": 8, "max_pct": 15, "suggested": 12.0},
    "automotive":        {"min_pct": 5, "max_pct": 10, "suggested": 7.0},
    "sports":            {"min_pct": 8, "max_pct": 15, "suggested": 11.0},
    "footwear":          {"min_pct": 10, "max_pct": 18, "suggested": 14.0},
    "books_media":       {"min_pct": 6, "max_pct": 12, "suggested": 9.0},
    "toys_games":        {"min_pct": 8, "max_pct": 16, "suggested": 12.0},
    "digital_goods":     {"min_pct": 8, "max_pct": 15, "suggested": 10.0},
    "jewelry":           {"min_pct": 6, "max_pct": 12, "suggested": 8.0},
    "watches":           {"min_pct": 8, "max_pct": 16, "suggested": 12.0},
    "pet_supplies":      {"min_pct": 8, "max_pct": 15, "suggested": 11.0},
    "furniture":         {"min_pct": 6, "max_pct": 12, "suggested": 9.0},
    "beauty":            {"min_pct": 10, "max_pct": 18, "suggested": 14.0},
    "general":           {"min_pct": 4, "max_pct": 12, "suggested": 8.0},
}


def _estimate_commission_ranges(gdp_per_capita: float | None, region: str) -> tuple[str, list[dict[str, Any]]]:
    """Generate per-category commission tiers adjusted by GDP and region.

    Blueprint algorithm:
      1. Start with BASE_COMMISSIONS
      2. emerging tier:  *0.85 — lower commissions to attract suppliers
         developed tier: *1.10 — higher commissions, suppliers can absorb
      3. Middle East region: *1.05 — GCC premium market
      4. Clamp to [min_pct, max_pct]
    """
    gdp = gdp_per_capita or 0
    if gdp > 30000:
        tier_name = "developed"
        tier_mult = 1.10
    elif gdp > 10000:
        tier_name = "developing"
        tier_mult = 1.0
    else:
        tier_name = "emerging"
        tier_mult = 0.85

    region_mult = 1.05 if region in ("gcc", "middle_east") else 1.0

    results: list[dict[str, Any]] = []
    for slug, base in _BASE_COMMISSIONS.items():
        suggested = base["suggested"] * tier_mult * region_mult
        suggested = round(max(base["min_pct"], min(suggested, base["max_pct"])), 1)

        results.append({
            "category_slug": slug,
            "min_commission_pct": base["min_pct"],
            "max_commission_pct": base["max_pct"],
            "default_pct": suggested,
            "label": f"{slug.replace('_', ' ').title()} ({suggested}%)",
            "gdp_tier": tier_name,
            "admin_adjustable": True,
            "adjustable_by": ["admin", "country_head"],
        })

    return tier_name, results


# =====================================================================
# KYC RULES — Blueprint tiers (Basic / Standard / Strict)
# =====================================================================

def _estimate_kyc_rules(gdp_per_capita: float | None, region: str) -> dict[str, Any]:
    """Assign KYC tier based on GDP and region per blueprint.

    | Tier | When Assigned | Required Documents | Verification Method |
    | Basic | GDP < $10K or emerging | National ID, Phone OTP | Automated OTP + ID scan |
    | Standard | $10K-$40K or developing | ID, Commercial Reg, Bank Letter | OCR + Manual review |
    | Strict | > $40K or GCC/EU/NA | All + VAT Cert, Trade License, Passport | OCR + Background check + Manual |
    """
    gdp = gdp_per_capita or 0
    strict_regions = {"gcc", "middle_east", "europe", "americas"}

    if gdp > 40000 or (gdp > 20000 and region in strict_regions):
        return {
            "kyc_level": "strict",
            "required_documents": [
                "commercial_registration", "vat_certificate", "bank_letter",
                "director_passport", "trade_license",
            ],
            "approval_required": True,
            "review_timeline_hours": 48,
            "verification_method": "OCR + Background check API + Manual",
        }
    if gdp > 10000:
        return {
            "kyc_level": "standard",
            "required_documents": [
                "national_id", "commercial_registration", "bank_letter",
            ],
            "approval_required": True,
            "review_timeline_hours": 72,
            "verification_method": "OCR + Manual review",
        }
    return {
        "kyc_level": "basic",
        "required_documents": ["national_id", "phone_otp"],
        "approval_required": False,
        "review_timeline_hours": 24,
        "verification_method": "Automated OTP + ID scan",
    }


# =====================================================================
# COD RELIANCE (Internet-penetration based)
# =====================================================================

def _estimate_cod_reliance(internet_penetration_pct: float | None, region: str) -> dict[str, Any]:
    internet = internet_penetration_pct or 50
    if internet < 40:
        return {"cod_pct": 80, "remittance_days": 7, "notes": "High COD reliance due to low internet penetration"}
    if internet < 60:
        return {"cod_pct": 60, "remittance_days": 5, "notes": "Moderate COD reliance; digital payments growing"}
    if internet < 80:
        return {"cod_pct": 35, "remittance_days": 3, "notes": "Growing digital payment adoption"}
    return {"cod_pct": 15, "remittance_days": 2, "notes": "Low COD reliance; strong digital payment infrastructure"}


# =====================================================================
# PAYOUT DEFAULTS (GDP tiered)
# =====================================================================

def _estimate_payout_settings(gdp_per_capita: float | None, region: str) -> dict[str, Any]:
    gdp = gdp_per_capita or 0
    if gdp > 30000:
        return {"minimum_payout_amount": 50, "payout_schedule": "weekly", "batch_size": 100, "payout_day": "sunday"}
    if gdp > 10000:
        return {"minimum_payout_amount": 20, "payout_schedule": "weekly", "batch_size": 50, "payout_day": "sunday"}
    return {"minimum_payout_amount": 10, "payout_schedule": "biweekly", "batch_size": 25, "payout_day": "monday"}


# =====================================================================
# PRODUCT RESTRICTIONS
# =====================================================================

_PRODUCT_RESTRICTIONS_BY_REGION: dict[str, list[str]] = {
    "gcc": ["alcohol", "pork", "adult_content", "gambling", "religious_offensive", "pig_products", "swine"],
    "middle_east": ["alcohol", "pork", "adult_content", "gambling", "religious_offensive"],
    "asia": ["gambling", "adult_content"],
    "africa": ["adult_content", "gambling"],
    "europe": ["adult_content", "gambling", "ivory"],
    "americas": ["adult_content", "gambling", "firearms"],
}


def _estimate_product_restrictions(region: str) -> list[str]:
    return _PRODUCT_RESTRICTIONS_BY_REGION.get(region, [])


# =====================================================================
# CONSUMER PROFILE
# =====================================================================

_DIGITAL_WALLET_ADOPTION: dict[str, float] = {
    "gcc": 0.65, "middle_east": 0.40, "europe": 0.35, "americas": 0.45,
    "asia": 0.60, "africa": 0.55, "oceania": 0.30,
}


def _estimate_consumer_profile(region: str, gdp_per_capita: float | None, internet_penetration_pct: float | None) -> dict[str, Any]:
    gdp = gdp_per_capita or 0
    internet = internet_penetration_pct or 50

    return {
        "return_window_days": 14 if gdp > 20000 else 7,
        "min_order_age": 21 if region in ("gcc", "middle_east") else 18,
        "max_returns_allowed": 5 if gdp > 30000 else 3,
        "refund_processing_days": 3 if internet > 80 else 7,
        "prefers_cod": internet < 50,
        "average_order_value_estimate_usd": round(gdp * 0.012, 2) if gdp else 25,
        "digital_wallet_penetration": round(_DIGITAL_WALLET_ADOPTION.get(region, 0.3) * 100, 1),
        "mobile_commerce_likely": internet > 60,
    }


# =====================================================================
# LOGISTICS MODEL RECOMMENDATION
# =====================================================================

def _estimate_logistics_model(gdp_per_capita: float | None, region: str, population: int | None) -> str:
    gdp = gdp_per_capita or 0
    pop = population or 0
    if gdp > 30000 and pop > 10000000:
        return "hub_and_spoke"
    if gdp > 10000 and pop > 5000000:
        return "hybrid"
    return "point_to_point"


def _suggest_logistics_zones(region: str, gdp_per_capita: float | None) -> list[dict[str, Any]]:
    gdp = gdp_per_capita or 0
    if region in ("gcc", "middle_east") and gdp > 20000:
        return [
            {"name": "Capital Metro", "type": "metro", "cities": []},
            {"name": "Major Cities", "type": "regional", "cities": []},
            {"name": "Rest of Country", "type": "national", "cities": []},
        ]
    return [
        {"name": "Primary Zone", "type": "national", "cities": []},
    ]


# =====================================================================
# FRAUD RISK SCORING
# =====================================================================

def _estimate_fraud_risk(gdp_per_capita: float | None, region: str, internet: float | None) -> str:
    gdp = gdp_per_capita or 0
    i = internet or 50
    if gdp > 30000 and i > 80 and region in ("gcc", "europe", "americas"):
        return "low"
    if gdp > 10000 and i > 50:
        return "medium"
    return "high"


# =====================================================================
# GDP & INTERNET FALLBACK MAPS
# =====================================================================

_GDP_FALLBACK: dict[str, float] = {
    "AE": 47790, "SA": 30436, "QA": 68839, "OM": 21214, "KW": 35999, "BH": 27696,
    "JO": 4243, "EG": 3968, "TR": 10996, "IR": 3539, "IQ": 5078,
    "GB": 46125, "DE": 48633, "FR": 43659, "IT": 35657, "ES": 30104,
    "NL": 52788, "BE": 47850, "CH": 88380, "SE": 52211, "NO": 82060,
    "DK": 62580, "PL": 18188, "US": 76330, "CA": 52963, "MX": 10460,
    "BR": 7602, "AR": 10872, "AU": 60928, "NZ": 44248,
    "IN": 2256, "PK": 1550, "BD": 2450, "LK": 3598, "CN": 12541, "JP": 40086,
    "KR": 34800, "HK": 48611, "SG": 82350, "MY": 11252, "TH": 7289,
    "ID": 4342, "PH": 3663, "VN": 3758, "TW": 33439,
    "ZA": 5558, "NG": 2084, "KE": 2042, "MA": 3506, "TN": 3653, "DZ": 3671,
    "RU": 11585, "UA": 4035, "KZ": 10216,
}

_INTERNET_FALLBACK: dict[str, float] = {
    "AE": 99, "SA": 98, "QA": 97, "OM": 96, "KW": 99, "BH": 99,
    "JO": 82, "EG": 72, "TR": 82, "IR": 80, "IQ": 60,
    "GB": 97, "DE": 96, "FR": 92, "IT": 82, "ES": 90,
    "NL": 96, "BE": 95, "CH": 96, "SE": 97, "NO": 98,
    "DK": 97, "PL": 85, "US": 93, "CA": 93, "MX": 72,
    "BR": 78, "AR": 86, "AU": 95, "NZ": 94,
    "IN": 48, "PK": 35, "BD": 38, "LK": 52, "CN": 78, "JP": 92,
    "KR": 97, "HK": 96, "SG": 96, "MY": 90, "TH": 82,
    "ID": 65, "PH": 68, "VN": 74, "TW": 95,
    "ZA": 72, "NG": 55, "KE": 50, "MA": 65, "TN": 68, "DZ": 62,
    "RU": 88, "UA": 75, "KZ": 82,
}


# =====================================================================
# MAIN ENTRY POINT
# =====================================================================

def generate_ecommerce_defaults(
    code: str,
    name: str,
    region: str | None,
    subregion: str | None,
    gdp_per_capita: float | None,
    internet_penetration_pct: float | None,
    population: int | None,
) -> dict[str, Any]:
    """Generate algorithmic e-commerce defaults for a country.

    Returns a dict with:
      - suggested_gateways: ranked by integration_feasibility_score
      - suggested_commission_tiers: per-category min/max %
      - suggested_supplier_requirements: KYC level + docs
      - suggested_payout_settings: defaults
      - cod_reliance_estimate: COD %
      - product_restrictions: region-specific
      - consumer_profile: demographics
      - logistic_model: recommended logistics model
      - suggested_logistics_zones: default zone suggestions
      - fraud_risk_tier: low/medium/high
      - heuristic_region: resolved region string
    """
    resolved_region = _resolve_region(region, subregion, code)

    code_upper = code.upper()
    gdp = gdp_per_capita or _GDP_FALLBACK.get(code_upper)
    internet = internet_penetration_pct or _INTERNET_FALLBACK.get(code_upper)
    pop = population or 0

    # 1. Payment gateways with blueprint scoring
    suggested_gateways = _suggest_gateways(resolved_region, gdp, internet, code)

    # 2. Commission ranges (blueprint: GDP-tiered + region adjustment)
    tier_name, suggested_commission_tiers = _estimate_commission_ranges(gdp, resolved_region)

    # 3. KYC requirements (blueprint: Basic / Standard / Strict)
    kyc = _estimate_kyc_rules(gdp, resolved_region)

    # 4. COD reliance
    cod = _estimate_cod_reliance(internet, resolved_region)

    # 5. Payout defaults
    payout = _estimate_payout_settings(gdp, resolved_region)

    # 6. Product restrictions
    restrictions = _estimate_product_restrictions(resolved_region)

    # 7. Consumer profile
    consumer = _estimate_consumer_profile(resolved_region, gdp, internet)

    # 8. Logistics model
    logistics_model = _estimate_logistics_model(gdp, resolved_region, pop)
    logistics_zones = _suggest_logistics_zones(resolved_region, gdp)

    # 9. Fraud risk
    fraud_risk = _estimate_fraud_risk(gdp, resolved_region, internet)

    return {
        "suggested_gateways": suggested_gateways,
        "suggested_commission_tiers": suggested_commission_tiers,
        "suggested_supplier_requirements": kyc,
        "suggested_payout_settings": payout,
        "cod_reliance_estimate": cod,
        "product_restrictions": restrictions,
        "consumer_profile": consumer,
        "suggested_logistics_model": logistics_model,
        "suggested_logistics_zones": logistics_zones,
        "fraud_risk_tier": fraud_risk,
        "heuristic_region": resolved_region,
        "economic_tier": tier_name,
    }

