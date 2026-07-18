"""Test auto-populate service."""
import asyncio
from services.country_auto_populate import auto_populate

async def test():
    result = await auto_populate("Oman")
    print("=== AUTO-POPULATE RESULT ===")
    print(f"Name: {result.get('name')}")
    print(f"Code: {result.get('code')}")
    print(f"Currency: {result.get('currency')} / {result.get('currency_symbol')}")
    print(f"Tax rate: {result.get('tax_rate')}")
    print(f"Economic tier: {result.get('economic_tier')}")
    print(f"Population: {result.get('population')}")
    print(f"Internet penetration: {result.get('internet_penetration_pct')}")
    cities = result.get('suggested_cities', [])
    print(f"Cities count: {len(cities)}")
    for c in cities[:5]:
        print(f"  City: {c.get('name')} (pop={c.get('population')}, capital={c.get('is_capital')})")
    gateways = result.get('suggested_gateways', [])
    print(f"Gateways: {len(gateways)}")
    for g in gateways[:3]:
        print(f"  Gateway: {g.get('gateway_id')} score={g.get('score')} fee={g.get('avg_fee')}")
    commissions = result.get('suggested_commissions', {})
    print(f"Commissions categories: {len(commissions)}")
    for k, v in list(commissions.items())[:3]:
        print(f"  {k}: min={v.get('min_rate')} max={v.get('max_rate')} suggested={v.get('suggested_rate')}")
    print(f"Degraded: {result.get('degraded')}")
    print(f"Warnings: {result.get('warnings', [])}")
    print(f"Source: {result.get('source')}")

asyncio.run(test())

