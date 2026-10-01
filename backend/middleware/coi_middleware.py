from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

# TODO: COI detection logic has been moved to middleware/dependencies/coi_dependency.py
# which itself is a no-op stub until the COI service can be relocated out of domains/.
# This middleware now short-circuits to keep the pipeline safe.


def coi_check_dependency(
    request: Request,
    db: Optional[Session] = None,
):
    """FastAPI dependency placeholder for the COI check.

    The real implementation lives in :mod:`middleware.dependencies.coi_dependency`.
    Kept here as a thin shim so existing router imports keep resolving.
    """
    if db is None:
        with get_db() as db_session:
            try:
                return _coi_check_internal(request, db_session)
            finally:
                db_session.close()
    return _coi_check_internal(request, db)


def _coi_check_internal(request: Request, db: Session) -> None:
    """No-op COI check pending relocation of the service out of ``domains/``."""
    return None
