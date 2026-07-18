"""Test auto-populate with unicode-safe output."""
import asyncio, sys, json
from services.country_auto_populate import auto_populate

async def test():
    result = await auto_populate("Oman")
    # Print as JSON to avoid unicode issues in console
    safe = {
        "name": result.get("name"),
        "code": result.get("code"),
        "currency": result.get("currency"),
        "currency_symbol": result.get("currency_symbol"),
        "tax_rate": result.get("tax_rate"),
        "economic_tier": result.get("economic_tier"),
        "population": result.get("population"),
        "internet_penetration_pct": result.get("internet_penetration_pct"),
        "cities_count": len(result.get("suggested_cities", [])),
        "gateways_count": len(result.get("suggested_gateways", [])),
        "commissions_count": len(result.get("suggested_commissions", {})),
        "degraded": result.get("degraded"),
        "warnings": result.get("warnings"),
        "source": result.get("source"),
        "first_cities": [{"name": c.get("name"), "pop": c.get("population"), "capital": c.get("is_capital")}
                        for c in (result.get("suggested_cities") or [])[:3]],
        "first_gateways": [{"id": g.get("gateway_id"), "score": g.get("score")}
                          for g in (result.get("suggested_gateways") or [])[:3]],
    }
    print(json.dumps(safe, indent=2))

asyncio.run(test())

