"""
Transaction Service — Centralized transaction management for services.

This module provides a pattern for services to handle database transactions
properly, keeping commit/rollback logic out of controllers and routers.

Usage:
    from services.core.transaction_service import transaction_context

    @transaction_context
    def my_service_method(db: Session) -> Result:
        # business logic
        db.add(entity)
        return result
    # commit/rollback handled by decorator

    # Or for more control:
    with transaction_context() as db:
        # business logic
        db.add(entity)
    # auto-commits on success, rolls back on exception
"""
from __future__ import annotations

import functools
import logging
from contextlib import contextmanager
from typing import Callable, Generator, TypeVar

from sqlalchemy.orm import Session

from dependencies.db import SessionLocal

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable)


@contextmanager
def transaction_context() -> Generator[Session, None, None]:
    """
    Context manager for database transactions with automatic commit/rollback.
    
    Usage:
        with transaction_context() as db:
            db.add(entity)
            # auto-commit on exit, rollback on exception
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def with_transaction(func: F) -> F:
    """
    Decorator to wrap service functions with automatic transaction management.
    
    Usage:
        @with_transaction
        def create_item(db: Session, data: dict) -> Item:
            item = Item(**data)
            db.add(item)
            return item
    """
    @functools.wraps(func)
    def wrapper(*args: list, **kwargs: dict):
        # Find db in args or kwargs
        db = None
        db_arg_index = None
        
        for i, arg in enumerate(args):
            if isinstance(arg, Session):
                db = arg
                db_arg_index = i
                break
        
        if db is None and 'db' in kwargs:
            db = kwargs['db']
        
        if db is not None:
            # db provided externally - let caller manage transaction
            return func(*args, **kwargs)
        
        # No db provided - create one with transaction management
        with transaction_context() as new_db:
            if db_arg_index is not None:
                args = list(args)
                args[db_arg_index] = new_db
            kwargs['db'] = new_db
            result = func(*args, **kwargs)
            return result
    
    return wrapper  # type: ignore


class TransactionService:
    """
    Service class for transaction management.
    
    Provides methods for services that need to coordinate multiple operations
    within a single transaction boundary.
    """
    
    def __init__(self, db: Session | None = None):
        self._db = db
        self._external_transaction = db is not None
    
    @property
    def db(self) -> Session:
        if self._db is None:
            raise RuntimeError("Session not initialized. Call __enter__ first.")
        return self._db
    
    def __enter__(self) -> TransactionService:
        if not self._external_transaction:
            self._db = SessionLocal()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is None:
            self._db.commit()
        else:
            self._db.rollback()
        if not self._external_transaction:
            self._db.close()


def transaction_service(db: Session | None = None) -> TransactionService:
    """
    Factory function to create a TransactionService.
    
    Usage:
        with transaction_service() as tx:
            tx.db.add(entity)
            tx.db.flush()
    """
    return TransactionService(db)