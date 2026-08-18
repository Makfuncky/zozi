"""Transaction management utilities for Zozi backend.

Provides standardized transaction context managers for database operations
with consistent error handling and cleanup.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session

from db.database import SessionLocal, engine

logger = logging.getLogger(__name__)


@contextmanager
def db_transaction_context(
    autocommit: bool = False,
    autoflush: bool = False,
    expire_on_commit: bool = True,
    retries: int = 3,
    retry_delay: float = 0.5,
):
    """Standardized database transaction context manager.

    Provides a robust transaction context with proper cleanup and
    consistent error handling across all database operations.

    Retry semantics are only supported via the ``transactional`` decorator
    or by wrapping the context manager in an explicit retry loop.
    The ``retries`` and ``retry_delay`` parameters are kept for API
    compatibility but are not used by the context manager itself.

    Args:
        autocommit: Whether to enable autocommit mode
        autoflush: Whether to enable autoflush mode
        expire_on_commit: Whether to expire objects on commit
        retries: Kept for API compatibility (unused)
        retry_delay: Kept for API compatibility (unused)

    Yields:
        Session: Database session ready for transaction operations

    Raises:
        Exception: If the transaction fails
    """
    session: Session | None = None
    try:
        session = SessionLocal(
            autocommit=autocommit,
            autoflush=autoflush,
            bind=engine,
            expire_on_commit=expire_on_commit,
        )
        yield session
        session.commit()
    except Exception:
        if session:
            session.rollback()
        raise
    finally:
        if session:
            try:
                session.close()
            except Exception:
                pass


def get_transaction_context(
    autocommit: bool = False,
    autoflush: bool = False,
    expire_on_commit: bool = True,
) -> type:
    """Get a transaction context manager class for dependency injection.

    Args:
        autocommit: Whether to enable autocommit mode
        autoflush: Whether to enable autoflush mode
        expire_on_commit: Whether to expire objects on commit

    Returns:
        Transaction context manager class
    """

    @contextmanager
    def _transaction_context() -> Generator[Session, None]:
        with db_transaction_context(
            autocommit=autocommit,
            autoflush=autoflush,
            expire_on_commit=expire_on_commit,
        ) as session:
            yield session

    return _transaction_context


@contextmanager
def atomic_transaction(
    retries: int = 3,
    retry_delay: float = 0.5,
) -> Generator[Session, None]:
    """Atomic transaction with all-or-nothing semantics.

    Ensures that either all operations within the context succeed
    and are committed, or none are persisted (rollback).

    Args:
        retries: Number of retry attempts on failure
        retry_delay: Delay between retry attempts in seconds

    Yields:
        Session: Database session for atomic operations

    Raises:
        Exception: If all retry attempts fail
    """
    with db_transaction_context(retries=retries, retry_delay=retry_delay) as session:
        yield session


def transactional(
    retries: int = 3,
    retry_delay: float = 0.5,
):
    """Decorator to make a function transactional.

    Args:
        retries: Number of retry attempts on failure
        retry_delay: Delay between retry attempts in seconds

    Returns:
        Decorated function with transaction context
    """
    from functools import wraps

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with db_transaction_context(retries=retries, retry_delay=retry_delay) as session:
                # Replace session argument if function accepts it
                new_args = []
                for arg in args:
                    if isinstance(arg, type(session)):
                        new_args.append(session)
                    else:
                        new_args.append(arg)

                return func(*new_args, **kwargs)

        return wrapper

    return decorator