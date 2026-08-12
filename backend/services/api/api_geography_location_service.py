"""In-app location API mounted at /location (same-origin for the web/mobile apps).

This reuses the shared geo_resolver so the frontend can resolve the customer's
current coordinates without standing up the separate location server. The
standalone ``location_service`` remains available for direct IP geolocation.

No coordinates are ever fabricated: a failed lookup returns 502 with a clear
message so the UI can fall back to the browser Geolocation API.
"""
from __future__ import annotations
from fastapi import Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services.location_service.geo_resolver import resolve_ip_location, reverse_geocode

class ReverseRequest(BaseModel):
    lat: float
    lon: float

class ResolveRequest(BaseModel):
    ip: str | None = None
