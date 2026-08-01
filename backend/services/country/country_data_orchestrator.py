"""
Autonomous Data Orchestrator & Heuristic Engine.

Fetches external data and generates e-commerce rules without manual admin input.
"""
import asyncio
import aiohttp
from typing import Optional, Dict, Any
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# External API endpoints
REST_COUNTRIES_URL = "https://restcountries.com/v3.1/alpha/{country_code}"
WORLD_BANK_URL = "https://api.worldbank.org/v2/country/{country_code}?format=json"
GEODB_CITIES_URL = "https://api.geodb-cities.com/v1/cities?country={country_code}&limit=1000"
NAGER_DATE_URL = "https://date.nager.at/v3/PublicHolidays/{year}/{country_code}"

# Redis TTL for cached data (48 hours)
CACHE_TTL_SECONDS = 48 * 60 * 60


class ExternalAPIFetcher:
    """Concurrent async fetcher for external country data APIs."""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _fetch_with_cache(self, key: str, fetch_fn) -> Any:
        """Fetch data with Redis caching."""
        if self.redis:
            cached = await self.redis.get(key)
            if cached:
                logger.info(f"Cache hit for {key}")
                return cached
        
        data = await fetch_fn()
        
        if self.redis and data:
            await self.redis.setex(key, CACHE_TTL_SECONDS, data)
        
        return data
    
    async def fetch_country_identity(self, country_code: str) -> Dict[str, Any]:
        """Fetch country identity data from RestCountries."""
        async def _fetch():
            url = REST_COUNTRIES_URL.format(country_code=country_code)
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data[0] if data else {}
                return {}
        return await self._fetch_with_cache(f"country:identity:{country_code}", lambda: _fetch())
    
    async def fetch_economic_data(self, country_code: str) -> Dict[str, Any]:
        """Fetch economic data from World Bank."""
        async def _fetch():
            url = WORLD_BANK_URL.format(country_code=country_code)
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # World Bank returns array with metadata and data
                    if isinstance(data, list) and len(data) > 1:
                        return data[1] if data[1] else []
                    return {}
                return {}
        return await self._fetch_with_cache(f"country:economics:{country_code}", lambda: _fetch())
    
    async def fetch_cities(self, country_code: str) -> list:
        """Fetch cities from GeoDB."""
        async def _fetch():
            url = GEODB_CITIES_URL.format(country_code=country_code)
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('data', [])
                return []
        return await self._fetch_with_cache(f"country:cities:{country_code}", lambda: _fetch())
    
    async def fetch_public_holidays(self, country_code: str, year: int = 2024) -> list:
        """Fetch public holidays from Nager.Date."""
        async def _fetch():
            url = NAGER_DATE_URL.format(year=year, country_code=country_code)
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                return []
        return await self._fetch_with_cache(f"country:holidays:{country_code}:{year}", lambda: _fetch())


class HeuristicEngine:
    """Algorithmically generates e-commerce rules based on country data."""
    
    @staticmethod
    def calculate_gateway_score(gateway: Dict, country_data: Dict) -> int:
        """Score payment gateways 0-100 based on compatibility."""
        score = 100
        
        # Region match (25 points)
        supported_regions = gateway.get('supported_regions', [])
        country_code = country_data.get('code', '')
        if country_code not in supported_regions:
            score -= 25
        
        # Currency match (20 points)
        currencies = gateway.get('currencies', [])
        country_currency = country_data.get('currency', 'USD')
        if country_currency not in currencies:
            score -= 20
        
        # Internet penetration factor (15 points)
        internet_pct = country_data.get('internet_penetration', 50)
        if internet_pct < 50:
            score -= int(15 * internet_pct / 100)
        
        # Fee competitiveness (15 points)
        fee = gateway.get('fee_percent', 3.0)
        if fee > 3.0:
            score -= min(15, int((fee - 3.0) * 5))
        
        # Setup speed (10 points)
        setup_days = gateway.get('setup_days', 7)
        if setup_days > 7:
            score -= min(10, setup_days - 7)
        
        return max(0, score)
    
    @staticmethod
    def generate_commission_tiers(gdp_per_capita: Decimal, country_code: str) -> Dict[str, Any]:
        """Generate commission rates based on country's GDP tier."""
        gdp = float(gdp_per_capita)
        
        if gdp >= 50000:
            tier = "high_income"
            default_rate = 0.08
            min_payout = 5000
        elif gdp >= 15000:
            tier = "upper_middle"
            default_rate = 0.12
            min_payout = 1000
        elif gdp >= 5000:
            tier = "lower_middle"
            default_rate = 0.15
            min_payout = 500
        else:
            tier = "low_income"
            default_rate = 0.18
            min_payout = 100
        
        return {
            "tier": tier,
            "default_rate": default_rate,
            "min_payout_amount": min_payout,
            "min_order_value": 10,
        }
    
    @staticmethod
    def assign_kyc_tier(gdp_per_capita: Decimal, fraud_index: float) -> str:
        """Assign KYC tier based on economic and fraud risk factors."""
        gdp = float(gdp_per_capita)
        
        if gdp >= 30000 and fraud_index < 0.3:
            return "strict"
        elif gdp >= 10000 and fraud_index < 0.5:
            return "standard"
        else:
            return "basic"
    
    @staticmethod
    def recommend_logistics_model(urbanization_pct: Decimal) -> Dict[str, Any]:
        """Recommend logistics model based on urbanization."""
        urban_pct = float(urbanization_pct)
        
        if urban_pct >= 70:
            return {
                "model": "point_to_point",
                "delivery_zones": 1,
                "hub_count": 0,
            }
        elif urban_pct >= 40:
            return {
                "model": "hub_and_spoke",
                "delivery_zones": 3,
                "hub_count": 2,
            }
        else:
            return {
                "model": "regional_distribution",
                "delivery_zones": 5,
                "hub_count": 4,
            }


async def auto_populate_country_config(country_code: str, redis_client=None) -> Dict[str, Any]:
    """Main orchestrator that fetches and processes all country data."""
    async with ExternalAPIFetcher(redis_client) as fetcher:
        # Fetch all data concurrently
        results = await asyncio.gather(
            fetcher.fetch_country_identity(country_code),
            fetcher.fetch_economic_data(country_code),
            fetcher.fetch_cities(country_code),
            fetcher.fetch_public_holidays(country_code),
            return_exceptions=True,
        )
        
        identity, economics, cities, holidays = results
        
        if isinstance(identity, Exception):
            logger.error(f"Identity fetch failed: {identity}")
            identity = {}
        
        if isinstance(economics, Exception):
            logger.error(f"Economics fetch failed: {economics}")
            economics = []
        
        if isinstance(cities, Exception):
            logger.error(f"Cities fetch failed: {cities}")
            cities = []
        
        if isinstance(holidays, Exception):
            logger.error(f"Holidays fetch failed: {holidays}")
            holidays = []
        
        # Process economic data
        gdp_per_capita = Decimal("0")
        population = 0
        internet_penetration = 50.0
        
        if economics:
            for item in economics:
                if item.get('indicator', {}).get('id') == 'NY.GDP.PCAP.KD':
                    gdp_per_capita = Decimal(str(item.get('value', 0)))
                elif item.get('indicator', {}).get('id') == 'SP.POP.TOTL':
                    population = int(item.get('value', 0))
                elif item.get('indicator', {}).get('id') == 'IT.NET.USER.ZS':
                    internet_penetration = float(item.get('value', 50))
        
        # Generate heuristic data
        heuristic = HeuristicEngine()
        commission_tiers = heuristic.generate_commission_tiers(gdp_per_capita, country_code)
        kyc_tier = heuristic.assign_kyc_tier(gdp_per_capita, 0.3)
        logistics_model = heuristic.recommend_logistics_model(Decimal('50'))
        
        return {
            "identity": identity,
            "economics": economics,
            "cities": cities,
            "holidays": holidays,
            "heuristics": {
                "commission_tiers": commission_tiers,
                "kyc_tier": kyc_tier,
                "logistics_model": logistics_model,
            },
            "population": population,
            "gdp_per_capita": gdp_per_capita,
            "internet_penetration": internet_penetration,
        }

