"""Geo location and country detection endpoints."""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from db.database import get_db
from controllers.auth_controller import get_current_user
from services.country_detection import CountryDetectionService
from utils.ip_utils import get_request_ip

router = APIRouter()


def get_country_from_ip(ip: str, db: Session) -> Optional[str]:
    """Fallback function for geo detection."""
    service = CountryDetectionService(db)
    country_code, _ = service._lookup_country_by_ip(ip)
    return country_code


@router.get("/geo")
def get_geo_info(
    request: Request,
    ip_address: Optional[str] = Query(None, description="Client IP for geo detection"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get geo information based on IP or user location."""
    country_code = None
    if ip_address:
        country_code = get_country_from_ip(ip_address, db)
    elif hasattr(request.state, "client_ip") and request.state.client_ip != "unknown":
        country_code = get_country_from_ip(request.state.client_ip, db)
    elif current_user.get("preferred_country"):
        country_code = current_user.get("preferred_country")
    
    from models import CountryConfig
    country = db.query(CountryConfig).filter(CountryConfig.code == country_code).first() if country_code else None
    
    return {
        "country_code": country_code,
        "country_name": country.name if country else None,
        "currency": country.currency if country else None,
        "currency_symbol": country.currency_symbol if country else None,
        "timezone": country.timezone if country else None,
        "language": country.language if country else None,
    }


@router.get("/geo/countries")
def list_geo_countries(db: Session = Depends(get_db)):
    """List all countries with geo information."""
    from models import CountryConfig
    countries = db.query(CountryConfig).filter(CountryConfig.is_active == True).all()
    return [
        {
            "code": c.code,
            "name": c.name,
            "currency": c.currency,
            "currency_symbol": c.currency_symbol,
            "phone_code": c.phone_code,
            "language": c.language,
            "timezone": c.timezone,
        }
        for c in countries
    ]
