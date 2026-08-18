"""Admin settings router."""
from fastapi import APIRouter, Depends
from infrastructure.utils.dependencies import require_admin
from infrastructure.utils.config import settings
from domains.accounts.models.user import User

router = APIRouter(prefix="/api/v1/admin")

@router.get("/")
def get_settings(_: User = Depends(require_admin)):
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "cors_origins": settings.cors_origins_list,
    }

