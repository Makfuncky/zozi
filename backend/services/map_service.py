"""Map service for interactive country maps and geographic visualization.

Provides map rendering, city markers, zone management, and geographic data.
"""
from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from models import CountryConfig, CountryCity
from models.country_control import CountryMapConfig, ShopWarehouseLocation

logger = logging.getLogger(__name__)


class MapService:
    """Service for interactive map rendering and geographic data."""

    def __init__(self, db: Session):
        self.db = db

    def get_country_map_config(self, country_code: str) -> Optional[Dict[str, Any]]:
        """Get map configuration for a country."""
        config = (
            self.db.query(CountryMapConfig)
            .filter(CountryMapConfig.country_code == country_code.upper())
            .first()
        )

        if not config:
            country = (
                self.db.query(CountryConfig)
                .filter(CountryConfig.code == country_code.upper())
                .first()
            )
            if country and country.latitude and country.longitude:
                return {
                    "country_code": country_code.upper(),
                    "map_provider": "google",
                    "api_key_ref": None,
                    "default_zoom": 5,
                    "show_regions": True,
                    "show_cities": True,
                    "center_lat": float(country.latitude),
                    "center_lng": float(country.longitude),
                }
            return None

        return {
            "country_code": country_code.upper(),
            "map_provider": config.map_provider,
            "api_key_ref": config.api_key_ref,
            "default_zoom": config.default_zoom,
            "show_regions": config.show_regions,
            "show_cities": config.show_cities,
        }

    def get_cities_for_map(
        self,
        country_code: str,
        region: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get cities with coordinates for map markers."""
        query = (
            self.db.query(CountryCity)
            .filter(
                CountryCity.country_code == country_code.upper(),
                CountryCity.is_active == True,
            )
            .limit(limit)
        )

        if region:
            query = query.filter(CountryCity.region == region)

        cities = query.all()
        return [
            {
                "id": c.id,
                "name": c.name,
                "region": c.region,
                "latitude": float(c.latitude) if c.latitude else None,
                "longitude": float(c.longitude) if c.longitude else None,
                "population": c.population,
                "is_active": c.is_active,
            }
            for c in cities
        ]

    def get_warehouses_for_map(
        self, country_code: str, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """Get warehouse locations for map."""
        query = self.db.query(ShopWarehouseLocation).filter(
            ShopWarehouseLocation.country_code == country_code.upper()
        )

        if not include_inactive:
            query = query.filter(ShopWarehouseLocation.is_active == True)

        warehouses = query.all()
        return [
            {
                "id": w.id,
                "name": w.name,
                "warehouse_code": w.warehouse_code,
                "latitude": w.latitude,
                "longitude": w.longitude,
                "address": w.address,
                "is_active": w.is_active,
            }
            for w in warehouses
        ]

    def get_delivery_zones(
        self, country_code: str, zone_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get delivery zones for a country."""
        from models.country_enhancements import OmanDeliveryZone

        query = self.db.query(OmanDeliveryZone).filter(
            OmanDeliveryZone.is_active == True
        )

        zones = query.all()
        return [
            {
                "zone_code": z.zone_code,
                "zone_name": z.zone_name,
                "description": z.description,
                "car_rate": float(z.car_rate) if z.car_rate else 0,
                "van_rate": float(z.van_rate) if z.van_rate else 0,
                "truck_rate": float(z.truck_rate) if z.truck_rate else 0,
                "weight_surcharge_rate": float(z.weight_surcharge_rate) if z.weight_surcharge_rate else 0,
                "cities": z.cities_json,
                "sort_order": z.sort_order,
            }
            for z in zones
        ]

    def generate_map_markers(
        self, country_code: str, include_parcels: bool = False
    ) -> Dict[str, Any]:
        """Generate complete marker data for map visualization."""
        cities = self.get_cities_for_map(country_code)
        warehouses = self.get_warehouses_for_map(country_code)

        markers = {
            "cities": [
                {
                    "type": "city",
                    "id": f"city_{c['id']}",
                    "name": c["name"],
                    "lat": c["latitude"],
                    "lng": c["longitude"],
                    "popup": f"<strong>{c['name']}</strong><br/>Population: {c['population'] or 'N/A'}",
                }
                for c in cities
                if c["latitude"] and c["longitude"]
            ],
            "warehouses": [
                {
                    "type": "warehouse",
                    "id": f"wh_{w['id']}",
                    "name": w["name"],
                    "lat": w["latitude"],
                    "lng": w["longitude"],
                    "popup": f"<strong>{w['name']}</strong><br/>{w['warehouse_code']}",
                }
                for w in warehouses
                if w["latitude"] and w["longitude"]
            ],
        }

        if include_parcels:
            from models import Shipment
            from models.country_control import ParcelLocationTracker

            shipments = (
                self.db.query(Shipment)
                .filter(Shipment.country_code == country_code.upper())
                .all()
            )

            parcel_trackers = (
                self.db.query(ParcelLocationTracker)
                .filter(ParcelLocationTracker.country_code == country_code.upper())
                .all()
            )

            latest_locations = {}
            for pt in parcel_trackers:
                if pt.parcel_id not in latest_locations or pt.timestamp > latest_locations[pt.parcel_id].timestamp:
                    latest_locations[pt.parcel_id] = pt

            markers["parcels"] = [
                {
                    "type": "parcel",
                    "id": f"parcel_{pid}",
                    "lat": loc.latitude,
                    "lng": loc.longitude,
                    "popup": f"Parcel {pid}",
                }
                for pid, loc in latest_locations.items()
                if loc.latitude and loc.longitude
            ]

        return markers

    def get_region_bounds(
        self, country_code: str, region_name: str
    ) -> Optional[Dict[str, float]]:
        """Calculate bounding box for a region."""
        cities = (
            self.db.query(CountryCity)
            .filter(
                CountryCity.country_code == country_code.upper(),
                CountryCity.region == region_name,
                CountryCity.latitude.isnot(None),
                CountryCity.longitude.isnot(None),
            )
            .all()
        )

        if not cities:
            return None

        lats = [float(c.latitude) for c in cities]
        lons = [float(c.longitude) for c in cities]

        padding = 0.1
        return {
            "north": max(lats) + padding,
            "south": min(lats) - padding,
            "east": max(lons) + padding,
            "west": min(lons) - padding,
        }
