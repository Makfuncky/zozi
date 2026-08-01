"""Database dependency injection layer — proper abstraction from db.database.

This module provides the database session dependency to the application layer,
ensuring controllers/routers never import directly from db.database.

Architecture invariant: Controllers → Services → db.database
"""
from __future__ import annotations

from typing import Generator
from sqlalchemy.orm import Session

from db.database import get_db as _get_db_impl


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session with proper cleanup.
    
    This is a service-layer wrapper around db.database.get_db to maintain
    proper layer separation. Controllers import this function instead of
    importing directly from db.database.
    
    Usage:
        from services.database import get_db
        from fastapi import Depends
        
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    return _get_db_impl()