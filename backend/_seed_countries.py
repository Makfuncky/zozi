"""Seed script: auto-populate one or more countries and persist to DB.

Usage:
    python -m _seed_countries OM PK AE SA
    python -m _seed_countries --all               # all 57 curated countries
    python -m _seed_countries OM                  # single country

Runs auto_populate() for each country, then calls create_admin_country()
with a mock admin user to persist everything (config, cities, tax rates, etc).
"""
from __future__ import annotations

import asyncio
import sys
import traceback

from db.database import SessionLocal
from db.models import CountryConfig

MOCK_ADMIN = {"role": "admin", "id": None}

COUNTRIES_TO_SEED = [
    "AE", "SA", "QA", "OM", "KW", "BH",
    "JO", "EG", "TR", "IR", "IQ",
    "GB", "DE", "FR", "IT", "ES",
    "NL", "BE", "CH", "SE", "NO",
    "DK", "PL",
    "US", "CA", "MX", "BR", "AR",
    "AU", "NZ",
    "IN", "PK", "BD", "LK",
    "CN", "JP", "KR", "HK", "SG",
    "MY", "TH", "ID", "PH", "VN", "TW",
    "ZA", "NG", "KE", "MA", "TN", "DZ",
    "RU", "UA", "KZ",
]


def _country_exists(code: str, db) -> bool:
    return db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first() is not None


async def seed_country(code: str, db) -> dict:
    """Auto-populate and persist a single country. Returns result dict."""
    code = code.upper().strip()
    print(f"\n{'='*60}")
    print(f"  Seeding {code}...")
    print(f"{'='*60}")

    # 1. Auto-populate
    from services.country_auto_populate import auto_populate
    result = await auto_populate(code)

    if result.get("error"):
        print(f"  ERROR: {result['error']}")
        return result

    name = result.get("name", code)
    print(f"  Name: {name}")
    print(f"  GDP: {result.get('gdp_per_capita_usd')}")
    print(f"  Internet: {result.get('internet_penetration_pct')}%")
    print(f"  Cities: {len(result.get('cities', []))}")
    print(f"  Warnings: {result.get('warnings', [])}")
    print(f"  Source: {result.get('source', '')}")

    # 2. Persist via controller
    from controllers.country_controller import create_admin_country

    payload = {
        "code": result.get("code", code),
        "name": result.get("name", name),
        "currency": result.get("currency", ""),
        "currency_symbol": result.get("currency_symbol"),
        "phone_code": result.get("phone_code"),
        "language": result.get("language", "en"),
        "timezone": result.get("timezone", "UTC"),
        "tax_type": result.get("tax_type", "VAT"),
        "tax_rate": result.get("tax_rate", 0.0),
        "tax_name": result.get("tax_name", "VAT"),
        "date_format": "DD/MM/YYYY",
        "is_active": True,
        "population": result.get("population"),
        "internet_penetration_pct": result.get("internet_penetration_pct"),
        "gdp_per_capita_usd": result.get("gdp_per_capita_usd"),
        "urbanization_pct": result.get("urbanization_pct"),
        "mobile_subs_per_100": result.get("mobile_subs_per_100"),
        "public_holidays": result.get("public_holidays", []),
        "macro_indicators": result.get("macro_indicators", {}),
        "cities": result.get("cities", []),
        "category_tax_rates": result.get("category_tax_rates", []),
        "legal_rules": result.get("legal_rules", {}),
        "logistics_defaults": result.get("logistics_defaults", {}),
        "payment_gateways": result.get("suggested_gateways", []),
        "logistics_providers": [],
        "supplier_requirements": result.get("suggested_supplier_requirements", {}),
        "payout_settings": result.get("suggested_payout_settings", {}),
        "commission_tiers": result.get("suggested_commission_tiers", []),
        "product_restrictions": result.get("product_restrictions", []),
        "economic_tier": result.get("economic_tier"),
        "fraud_risk_tier": result.get("fraud_risk_tier"),
        "suggested_logistics_model": result.get("suggested_logistics_model"),
        "suggested_gateways": result.get("suggested_gateways", []),
        "suggested_commission_tiers": result.get("suggested_commission_tiers", []),
        "suggested_supplier_requirements": result.get("suggested_supplier_requirements", {}),
        "suggested_payout_settings": result.get("suggested_payout_settings", {}),
        "consumer_profile": result.get("consumer_profile", {}),
        "cod_reliance_estimate": result.get("cod_reliance_estimate", {}),
        "heuristic_region": result.get("heuristic_region"),
        "official_name": result.get("official_name"),
        "alpha3": result.get("alpha3"),
        "flag_url": result.get("flag_url"),
        "currency_name": result.get("currency_name"),
        "supplier_kyc_tier": (result.get("suggested_supplier_requirements") or {}).get("kyc_level"),
        "consumer_protection_days": (result.get("consumer_profile") or {}).get("return_window_days", 14),
        "minimum_payout_amount": (result.get("suggested_payout_settings") or {}).get("minimum_payout_amount"),
        "payout_currency": result.get("currency"),
        "measurement_system": "metric",
        "working_days": None,
    }

    try:
        saved = create_admin_country(payload, MOCK_ADMIN, db)
        print(f"  [+] Created: {saved.get('code')} - {saved.get('name')}")
        return saved
    except Exception as e:
        print(f"  [X] Failed: {e}")
        traceback.print_exc()
        return {"error": str(e)}


async def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python -m _seed_countries OM PK AE SA")
        print("       python -m _seed_countries --all")
        print("       python -m _seed_countries --overwrite OM PK  # re-seed existing")
        sys.exit(1)

    overwrite = "--overwrite" in args
    codes = [c.upper() for c in args if not c.startswith("--") and len(c) == 2]
    if "--all" in args:
        codes = COUNTRIES_TO_SEED

    db = SessionLocal()
    try:
        results = []
        for code in codes:
            exists = _country_exists(code, db)
            if exists and not overwrite:
                print(f"  Skipping {code}: already exists (use --overwrite to re-seed)")
                results.append({"code": code, "status": "skipped"})
                continue
            if exists and overwrite:
                print(f"  Deleting existing data for {code}...")
                from db.models import (
                    AdminChangeAuditLog, CountryCity, CountryCategoryTaxRate,
                    CountryFeatureFlag, CountryStaffAssignment, CountryCommunication,
                    CountryConfigVersion, CrossCountryCustomerSession,
                    SupplierCountryCommission, CountryGatewayCredentials,
                )
                child_tables = [
                    CountryCity, CountryCategoryTaxRate,
                    CountryGatewayCredentials, SupplierCountryCommission,
                    CountryFeatureFlag, CountryStaffAssignment,
                    CountryCommunication, CountryConfigVersion,
                    CrossCountryCustomerSession, AdminChangeAuditLog,
                ]
                for tbl in child_tables:
                    if hasattr(tbl, "country_code"):
                        db.query(tbl).filter(tbl.country_code == code).delete(synchronize_session=False)
                    elif hasattr(tbl, "source_country_code"):
                        db.query(tbl).filter(
                            (tbl.source_country_code == code) | (tbl.target_country_code == code)
                        ).delete(synchronize_session=False)
                db.query(CountryConfig).filter(CountryConfig.code == code).delete(synchronize_session=False)
                db.commit()
                print(f"  Deleted {code}")

            r = await seed_country(code, db)
            results.append({"code": code, "status": "ok" if "error" not in r else "failed"})

        ok_count = sum(1 for r in results if r['status'] == 'ok')
        skipped = sum(1 for r in results if r['status'] == 'skipped')
        failed = sum(1 for r in results if r['status'] == 'failed')
        print(f"\n{'='*60}")
        print(f"  Summary: {ok_count} created, {skipped} skipped, {failed} failed")
        print(f"{'='*60}")
        if failed:
            sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())

