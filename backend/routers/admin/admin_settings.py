"""Admin settings router."""
from fastapi import APIRouter, Depends
from utils.dependencies import require_admin
from utils.config import settings
from models import User

router = APIRouter()

@router.get("/")
def get_settings(_: User = Depends(require_admin)):
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "cors_origins": settings.cors_origins_list,
    }

