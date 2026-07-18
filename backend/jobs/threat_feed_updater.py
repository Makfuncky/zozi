"""Background job to update threat feeds from open sources."""
import asyncio
import logging
import aiohttp
from datetime import datetime, timezone
from typing import Set

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

THREAT_FEEDS = {
    "tor": {
        "url": "https://check.torproject.org/torbulkexitlist",
        "type": "ip_list",
    },
    "open_proxies": {
        "url": "https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/proxylists.org/domains_proxies.txt",
        "type": "ip_list",
    },
    "spamhaus_drop": {
        "url": "https://www.spamhaus.org/drop/drop.txt",
        "type": "ip_list",
    },
}

async def fetch_ip_list(session: aiohttp.ClientSession, url: str) -> Set[str]:
    """Fetch IP list from URL."""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                content = await response.text()
                ips = set()
                for line in content.strip().split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#") and not line.startswith(";"):
                        parts = line.split("|") if "|" in line else line.split(",")
                        if parts:
                            ips.add(parts[0].strip())
                return ips
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
    return set()

async def update_threat_feeds():
    """Update all threat feeds and return counts."""
    results = {}
    
    async with aiohttp.ClientSession() as session:
        for feed_name, feed_config in THREAT_FEEDS.items():
            ips = await fetch_ip_list(session, feed_config["url"])
            results[feed_name] = len(ips)
            logger.info(f"Updated {feed_name}: {len(ips)} entries")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(update_threat_feeds())
    print(f"Threat feed update complete: {results}")
