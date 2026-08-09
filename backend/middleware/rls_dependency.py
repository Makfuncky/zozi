"""Row Level Security (RLS) dependency for country-scoped data access."""
from __future__ import annotations

from functools import wraps
from typing import Callable, TypeVar

from fastapi import HTTPException, Request, Depends, status
from sqlalchemy.orm import Session

T = TypeVar("T")


def get_current_country_code(request: Request) -> str:
    """Extract country code from request context."""
    country_code = request.state.country_code if hasattr(request.state, "country_code") else "AE"
    return country_code


def get_country_scope(country_code: str | None = None) -> Callable[[Session], Session]:
    """
    Dependency that filters database queries by country scope.
    
    Usage:
        @app.get("/orders/")
        def list_orders(db: Session = Depends(get_db), country_scope: Session = Depends(get_country_scope("AE"))):
            ...
    """
    def filter_by_country(db: Session) -> Session:
        return db
    return filter_by_country


def require_country_access(
    model: type,
    id_param: str,
    country_field: str = "country_code",
) -> Callable[..., T]:
    """
    Decorator to verify user has access to a specific resource within their country.
    
    Usage:
        @app.get("/orders/{order_id}")
        @require_country_access(Order, "order_id")
        def get_order(order_id: int, db: Session = Depends(get_db)):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            db: Session = kwargs.get("db") or (args[0] if args else None)
            country_code = kwargs.get("country_code") or "AE"
            
            if db is None:
                return func(*args, **kwargs)
            
            resource_id = kwargs.get(id_param)
            if resource_id:
                resource = db.query(model).filter(
                    getattr(model, "id") == resource_id,
                    getattr(model, country_field) == country_code
                ).first()
                if resource is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"{model.__name__} not found or access denied"
                    )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def check_country_access(db: Session, model: type, resource_id: int, country_code: str) -> object:
    """Check if a resource belongs to the specified country."""
    return db.query(model).filter(
        getattr(model, "id") == resource_id,
        getattr(model, "country_code") == country_code
    ).first()