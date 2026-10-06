"""Paired test: verify that SQLAlchemy mappers configure without InvalidRequestError."""
from __future__ import annotations

import sys

_BACKEND_ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))


def test_configure_mappers_succeeds() -> None:
    from infrastructure.database.base import Base
    print("DEBUG: Tables before import:", list(Base.metadata.tables.keys())[:10])
    print("DEBUG: logistics_entities in sys.modules:", "domains.logistics.models.logistics_entities" in sys.modules)
    
    from domains.logistics.models.logistics_entities import Shipment  # noqa: F401
    
    print("DEBUG: Tables after import:", list(Base.metadata.tables.keys())[:10])
    from domains.country.models.country_control import (  # noqa: F401
        LogisticsPartnerLocation,
        ParcelLocationTracker,
    )
    from sqlalchemy.orm import configure_mappers
    configure_mappers()
