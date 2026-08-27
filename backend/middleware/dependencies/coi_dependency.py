from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

logger = logging.getLogger(__name__)

# TODO: Conflict-of-interest detection is owned by
# ``domains.hr.services.employees.coi_service.COIService`` but the
# middleware/dependencies layer must not import from ``domains/``
# (Law 1). The active implementation will be moved to
# ``infrastructure/security/coi`` so the dependency can stay inside the
# circuit. Until that lands, the dependency is a no-op shim that keeps
# the request pipeline safe and the public signature stable.


def coi_check_dependency(
    request: Request,
    db: Optional[Session] = None,
):
    """FastAPI dependency placeholder for the COI check.

    Lives in the dependencies layer (which is permitted to reach
    services), but the real COI service lives in ``domains/`` and is
    currently not reachable from the middleware circuit. This shim
    short-circuits to keep the request pipeline safe.
    """
    if db is None:
        with get_db() as db_session:
            try:
                return _coi_check_internal(request, db_session)
            finally:
                db_session.close()
    return _coi_check_internal(request, db)


def _coi_check_internal(request: Request, db: Session) -> None:
    """No-op COI check pending relocation of the service."""
    return None
