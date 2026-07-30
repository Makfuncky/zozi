import logging
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from db.database import get_db_session
from services.country_detection import CountryDetectionService
from utils.ip_utils import get_request_ip

logger = logging.getLogger(__name__)

COUNTRY_HEADER = "X-Country-Code"
COUNTRY_SOURCE_HEADER = "X-Country-Source"


class CountryDetectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        country_code, source = await self._detect_country(request)
        
        response = await call_next(request)
        
        if country_code:
            response.headers[COUNTRY_HEADER] = country_code
            response.headers[COUNTRY_SOURCE_HEADER] = source
        
        return response
    
    async def _detect_country(self, request: Request) -> tuple[Optional[str], str]:
        db = None
        try:
            client_host = get_request_ip(request)

            db = get_db_session()
            service = CountryDetectionService(db)
            country_code, source = service.detect_country_from_ip({}, client_host)
            return country_code, source
        except Exception as e:
            logger.debug("Country detection failed: %s", e)
            return None, "error"
        finally:
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass


def get_country_from_request(request: Request) -> Optional[str]:
    return request.headers.get(COUNTRY_HEADER)


def get_country_source_from_request(request: Request) -> str:
    return request.headers.get(COUNTRY_SOURCE_HEADER, "unknown")
