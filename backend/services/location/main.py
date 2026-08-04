"""Standalone IP/location tracking server for the Zozi order/delivery system.

Run with the backend virtual environment:

    cd backend
    python run_location_server.py
    # or:
    uvicorn location_service.main:app --port 8005 --reload

Endpoints
---------
GET  /api/health                              liveness probe
GET  /api/geo/from-ip?ip=1.2.3.4             geolocate an arbitrary IP (omit ip for caller)
GET  /api/geo/locate                          geolocate the calling client
POST /api/geo/reverse  {lat, lon}            reverse geocode coordinates -> address
POST /api/geo/resolve   {ip?}                IP -> coords + (best-effort) address

No coordinates are ever fabricated. When a lookup is impossible a 502 with a clear
message is returned so the frontend can rely on the browser Geolocation API.
"""


import logging
import os

from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.location.geo_resolver import resolve_ip_location, reverse_geocode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("location_service")

app = FastAPI(title="Zozi Location Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("LOCATION_CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ReverseRequest(BaseModel):
    lat: float
    lon: float


class ResolveRequest(BaseModel):
    ip: str | None = None


def _client_meta(request: Request, x_forwarded_for: str | None, x_real_ip: str | None):
    client_host = request.client.host if request.client else "127.0.0.1"
    return client_host, x_forwarded_for, x_real_ip


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "location", "version": "1.0.0"}


@app.get("/api/geo/from-ip")
def geo_from_ip(
    request: Request,
    ip: str | None = None,
    x_forwarded_for: str | None = Header(None),
    x_real_ip: str | None = Header(None),
):
    client_host, fwd, real = _client_meta(request, x_forwarded_for, x_real_ip)
    try:
        location = resolve_ip_location(ip=ip, client_host=client_host, forwarded_for=fwd, real_ip=real)
    except RuntimeError as exc:
        return JSONResponse(status_code=502, content={"error": str(exc), "source": "location_service"})
    return location.to_dict()


@app.get("/api/geo/locate")
def geo_locate(
    request: Request,
    x_forwarded_for: str | None = Header(None),
    x_real_ip: str | None = Header(None),
):
    client_host, fwd, real = _client_meta(request, x_forwarded_for, x_real_ip)
    try:
        location = resolve_ip_location(client_host=client_host, forwarded_for=fwd, real_ip=real)
    except RuntimeError as exc:
        return JSONResponse(status_code=502, content={"error": str(exc), "source": "location_service"})
    return location.to_dict()


@app.post("/api/geo/reverse")
def geo_reverse(payload: ReverseRequest):
    try:
        result = reverse_geocode(payload.lat, payload.lon)
    except RuntimeError as exc:
        return JSONResponse(status_code=502, content={"error": str(exc), "source": "location_service"})
    return result.to_dict()


@app.post("/api/geo/resolve")
def geo_resolve(
    payload: ResolveRequest,
    request: Request,
    x_forwarded_for: str | None = Header(None),
    x_real_ip: str | None = Header(None),
):
    client_host, fwd, real = _client_meta(request, x_forwarded_for, x_real_ip)
    try:
        location = resolve_ip_location(ip=payload.ip, client_host=client_host, forwarded_for=fwd, real_ip=real)
    except RuntimeError as exc:
        return JSONResponse(status_code=502, content={"error": str(exc), "source": "location_service"})
    return location.to_dict()

