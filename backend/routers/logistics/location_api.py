"""In-app location API mounted at /location (same-origin for the web/mobile apps).

This reuses the shared geo_resolver so the frontend can resolve the customer's
current coordinates without standing up the separate location server. The
standalone ``location_service`` remains available for direct IP geolocation.

No coordinates are ever fabricated: a failed lookup returns 502 with a clear
message so the UI can fall back to the browser Geolocation API.
"""

from __future__ import annotations

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.location.geo_resolver import resolve_ip_location, reverse_geocode

router = APIRouter()


class ReverseRequest(BaseModel):
    lat: float
    lon: float


class ResolveRequest(BaseModel):
    ip: str | None = None


def _client_meta(request: Request, x_forwarded_for: str | None, x_real_ip: str | None):
    client_host = request.client.host if request.client else "127.0.0.1"
    return client_host, x_forwarded_for, x_real_ip


@router.get("/api/geo/from-ip")
def geo_from_ip(request: Request, ip: str | None = None, x_forwarded_for: str | None = Header(None), x_real_ip: str | None = Header(None)):
    client_host, fwd, real = _client_meta(request, x_forwarded_for, x_real_ip)
    try:
        return resolve_ip_location(ip=ip, client_host=client_host, forwarded_for=fwd, real_ip=real).to_dict()
    except RuntimeError as exc:
        return JSONResponse(status_code=502, content={"error": str(exc), "source": "location_api"})


@router.get("/api/geo/locate")
def geo_locate(request: Request, x_forwarded_for: str | None = Header(None), x_real_ip: str | None = Header(None)):
    client_host, fwd, real = _client_meta(request, x_forwarded_for, x_real_ip)
    try:
        return resolve_ip_location(client_host=client_host, forwarded_for=fwd, real_ip=real).to_dict()
    except RuntimeError as exc:
        return JSONResponse(status_code=502, content={"error": str(exc), "source": "location_api"})


@router.post("/api/geo/reverse")
def geo_reverse(payload: ReverseRequest):
    try:
        return reverse_geocode(payload.lat, payload.lon).to_dict()
    except RuntimeError as exc:
        return JSONResponse(status_code=502, content={"error": str(exc), "source": "location_api"})


@router.post("/api/geo/resolve")
def geo_resolve(payload: ResolveRequest, request: Request, x_forwarded_for: str | None = Header(None), x_real_ip: str | None = Header(None)):
    client_host, fwd, real = _client_meta(request, x_forwarded_for, x_real_ip)
    try:
        return resolve_ip_location(ip=payload.ip, client_host=client_host, forwarded_for=fwd, real_ip=real).to_dict()
    except RuntimeError as exc:
        return JSONResponse(status_code=502, content={"error": str(exc), "source": "location_api"})

