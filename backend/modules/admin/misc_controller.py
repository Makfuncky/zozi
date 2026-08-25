"""Backward-compat stub for legacy `modules.admin.misc_controller` imports."""
from domains.governance.services.settings.misc_service import *  # noqa: F401,F403


def database_overview(db=None, **kwargs) -> dict:
    """Return a high-level database overview (table counts, health, size)."""
    from domains.governance.services.settings.database_service import get_database_overview
    if db is None:
        return {"error": "no database session"}
    return get_database_overview(db)
