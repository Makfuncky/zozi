"""Diagnostics: check country data state."""
import asyncio
from sqlalchemy import text
from db.database import SessionLocal

# === DB Check ===
db = SessionLocal()

# Check regions_json in country_configs
rows = db.execute(text("SELECT code, name, regions_json, economic_tier, population, internet_penetration_pct, currency, currency_symbol, tax_rate FROM country_configs")).fetchall()
print("=== COUNTRY CONFIGS (with regions_json) ===")
for r in rows:
    d = dict(r._mapping)
    print(f"  {d['code']}: {d['name']}")
    print(f"    economic_tier={d['economic_tier']}, population={d['population']}, internet={d['internet_penetration_pct']}")
    print(f"    currency={d['currency']} {d['currency_symbol']}, tax_rate={d['tax_rate']}")
    has_regions = d['regions_json'] is not None and len(str(d['regions_json'])) > 0
    print(f"    has_regions_json={has_regions}")

# Check country_cities
count = db.execute(text("SELECT COUNT(*) FROM country_cities")).scalar()
print(f"\n=== COUNTRY CITIES TOTAL: {count} ===")

# Check commission_category_rates
ccr = db.execute(text("SELECT country_code, category_slug FROM commission_category_rates LIMIT 10")).fetchall()
print(f"\n=== COMMISSION CATEGORY RATES ===")
for r in ccr:
    print(f"  {r[0]}: {r[1]}")

# Check country_category_tax_rates
tax = db.execute(text("SELECT country_code, category_slug, rate FROM country_category_tax_rates LIMIT 10")).fetchall()
print(f"\n=== COUNTRY CATEGORY TAX RATES ===")
for r in tax:
    print(f"  {r[0]}: {r[1]} = {r[2]}")

# Check feature flags
ff = db.execute(text("SELECT country_code, feature_key, is_enabled FROM country_feature_flags LIMIT 10")).fetchall()
print(f"\n=== FEATURE FLAGS ===")
for r in ff:
    print(f"  {r[0]}: {r[1]} = {r[2]}")

# Check versions
vers = db.execute(text("SELECT country_code, config_type, status FROM country_config_versions LIMIT 10")).fetchall()
print(f"\n=== VERSIONS ===")
for r in vers:
    print(f"  {r[0]}: {r[1]} = {r[2]}")

db.close()

# === Auto-populate test ===
print("\n\n=== TESTING AUTO-POPULATE ===")
from services.country_auto_populate import auto_populate

async def test():
    result = await auto_populate("Oman")
    print(f"Name: {result.get('name')}")
    print(f"Code: {result.get('code')}")
    print(f"Currency: {result.get('currency_code')} / {result.get('currency_symbol')}")
    print(f"Tax rate: {result.get('default_tax_rate')}")
    print(f"Cities count: {len(result.get('suggested_cities', []))}")
    print(f"Gateways: {len(result.get('suggested_gateways', []))}")
    print(f"Commissions categories: {len(result.get('suggested_commissions', {}))}")
    print(f"Degraded: {result.get('degraded')}")
    print(f"Warnings: {result.get('warnings', [])}")
    print(f"Source: {result.get('source')}")
    # Print first 3 cities
    for c in result.get('suggested_cities', [])[:3]:
        print(f"  City: {c.get('name')} (pop={c.get('population')}, capital={c.get('is_capital')})")
    # Print first 3 gateways
    for g in result.get('suggested_gateways', [])[:3]:
        print(f"  Gateway: {g.get('gateway_id')} score={g.get('score')} fee={g.get('avg_fee')}")

asyncio.run(test())

