"""Debug World Bank API."""
import httpx, asyncio

async def test():
    async with httpx.AsyncClient(timeout=10) as c:
        # Try different formats
        urls = [
            "https://api.worldbank.org/v2/country/OM/indicator/NY.GDP.PCAP.CD?format=json",
            "https://api.worldbank.org/v2/country/OM/indicator/NY.GDP.PCAP.CD?format=json&per_page=1",
            "https://api.worldbank.org/v2/country/om/indicator/NY.GDP.PCAP.CD?format=json&per_page=1",
            "https://api.worldbank.org/v2/country/OMN/indicator/NY.GDP.PCAP.CD?format=json&per_page=1",
            "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.CD?format=json&per_page=3",
        ]
        for url in urls:
            try:
                r = await c.get(url)
                data = r.json()
                if r.is_success and len(data) > 1 and data[1]:
                    entry = data[1][0]
                    print(f"OK: {url.split('?')[0][:60]}... value={entry.get('value')} year={entry.get('date')}")
                else:
                    msg = data[0].get("message", [{}])[0].get("value", "?") if len(data) > 0 else "?"
                    print(f"FAIL: {url.split('?')[0][:60]}... msg={msg}")
            except Exception as e:
                print(f"ERR: {url.split('?')[0][:60]}... {e}")

asyncio.run(test())

