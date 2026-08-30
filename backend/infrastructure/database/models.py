"""Central model registry.

SQLAlchemy mapper registration (importing every ``domains/*/models`` package)
is performed by the lifespan preloader (``_preload_all_models``) so that the
downward-only import rule is preserved: ``infrastructure`` must never import
``domains``. This module therefore only clears any stale mappers at import
time; the actual mapper configuration happens lazily once every model module
has been registered by the lifespan preloader.
"""
from sqlalchemy.orm import clear_mappers

# Clear stale mappers so registration starts from a clean state. Mappers are
# configured lazily by SQLAlchemy when first accessed, after the lifespan
# preloader has imported every domain model module.
clear_mappers()
