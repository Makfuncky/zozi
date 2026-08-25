"""Admin partners router — split from logistics.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_logistics_geography import router as admin_logistics_geography_router
    router.include_router(admin_logistics_geography_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_logistics_geography: %s", _e)

try:
    from .logistics_geography import router as logistics_geography_router
    router.include_router(logistics_geography_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip logistics_geography: %s", _e)

try:
    from .admin_logistics_imports import router as admin_logistics_imports_router
    router.include_router(admin_logistics_imports_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_logistics_imports: %s", _e)

try:
    from .logistics_imports import router as logistics_imports_router
    router.include_router(logistics_imports_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip logistics_imports: %s", _e)

