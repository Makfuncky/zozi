"""Admin country router — imports from split sub-modules."""

from fastapi import APIRouter

from .countries import router as countries_router
from .localization import router as localization_router
from .tax import router as tax_router

router = APIRouter()

try:
    router.include_router(countries_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip countries_router: %s", _e)

try:
    router.include_router(localization_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip localization_router: %s", _e)

try:
    router.include_router(tax_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip tax_router: %s", _e)

