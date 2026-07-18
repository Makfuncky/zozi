"""Test external API connectivity."""
import httpx, asyncio, json

async def test():
    async with httpx.AsyncClient(timeout=10, verify=False) as c:
        # World Bank
        try:
            r = await c.get("https://api.worldbank.org/v2/country/OM/indicator/NY.GDP.PCAP.CD?format=json&date=latest")
            print(f"World Bank status: {r.status_code}")
            print(f"Response: {r.text[:300]}")
        except Exception as e:
            print(f"World Bank Error: {type(e).__name__}: {e}")

        # Open-meteo by country name
        try:
            r = await c.get("https://geocoding-api.open-meteo.com/v1/search?name=Oman&count=10&format=json")
            print(f"\nOpen-Meteo Oman: {r.status_code}")
            if r.is_success:
                data = r.json()
                results = data.get("results", [])
                print(f"  Results: {len(results)}")
                for res in results[:5]:
                    print(f"  - {res.get('name')}, cc={res.get('country_code')}, pop={res.get('population')}")
        except Exception as e:
            print(f"Open-Meteo Error: {e}")

        # Open-meteo by capital name
        try:
            r = await c.get("https://geocoding-api.open-meteo.com/v1/search?name=Muscat&count=10&format=json")
            print(f"\nOpen-Meteo Muscat: {r.status_code}")
            if r.is_success:
                data = r.json()
                results = data.get("results", [])
                print(f"  Results: {len(results)}")
                for res in results[:5]:
                    print(f"  - {res.get('name')}, cc={res.get('country_code')}, pop={res.get('population')}")
        except Exception as e:
            print(f"Open-Meteo Error: {e}")

asyncio.run(test())

