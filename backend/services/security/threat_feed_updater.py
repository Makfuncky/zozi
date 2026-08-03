"""Background job to update threat feeds from open sources."""
import logging
from datetime import datetime, timezone
from typing import Set

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


def fetch_ip_list(url: str) -> Set[str]:
    """Fetch IP list from URL."""
    try:
        import requests
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            content = response.text
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


def update_threat_feeds():
    """Update all threat feeds and return counts."""
    results = {}
    
    for feed_name, feed_config in THREAT_FEEDS.items():
        ips = fetch_ip_list(feed_config["url"])
        results[feed_name] = len(ips)
        logger.info(f"Refreshed {feed_name}: {len(ips)} entries")
    
    return results


if __name__ == "__main__":
    results = update_threat_feeds()
    logger.info("Threat feed refresh complete: %s", results)