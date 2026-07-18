from __future__ import annotations

from typing import Optional, Set, Any

from fastapi import Depends, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session, Query
from sqlalchemy import event, text

from db.database import get_db
from models import User, CountryStaffAssignment, CountryConfig
from utils.auth import verify_token
from utils.config import settings


class RLSContext:
    """Request context for RLS enforcement"""
    def __init__(self):
        self.country_scope: Optional[Set[str]] = None
        self.is_restricted: bool = False
        self.user_id: Optional[int] = None
        self.role: Optional[str] = None


rls_context = RLSContext()


def get_rls_context() -> RLSContext:
    return rls_context


def clear_rls_context() -> None:
    rls_context.country_scope = None
    rls_context.is_restricted = False
    rls_context.user_id = None
    rls_context.role = None


def resolve_user_country_scope(user: User, db: Session) -> Set[str]:
    """Resolve allowed country codes for a user"""
    if user.role in {"admin", "super_admin"}:
        return set()
    
    assignments = (
        db.query(CountryStaffAssignment.country_code)
        .filter(
            CountryStaffAssignment.user_id == user.id,
            CountryStaffAssignment.is_active == True,
        )
        .all()
    )
    
    codes = {str(row[0]).upper().strip() for row in assignments if row[0]}
    return codes


class RowLevelSecurityMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce RLS at request level"""
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            clear_rls_context()
            return await call_next(request)
        
        try:
            payload = verify_token(token)
            user_id = int(payload.get("sub"))
            role = payload.get("role", "customer")
            
            rls_context.user_id = user_id
            rls_context.role = role
            
            if role in {"admin", "super_admin"}:
                clear_rls_context()
                return await call_next(request)
            
            with get_db() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    scope = resolve_user_country_scope(user, db)
                    rls_context.country_scope = scope
                    rls_context.is_restricted = bool(scope)
        except Exception:
            clear_rls_context()
        
        response = await call_next(request)
        clear_rls_context()
        return response


def apply_rls_filter(query: Query, country_code: Optional[str] = None) -> Query:
    """Apply RLS filter to SQLAlchemy query"""
    if rls_context.is_restricted:
        if rls_context.country_scope:
            return query.filter(CountryConfig.code.in_(rls_context.country_scope))
    return query


@event.listens_for(Session, "after_begin")
def set_session_rls(session: Session, transaction: Any, *args: Any, **kwargs: Any) -> None:
    """Set RLS context at database session level"""
    if rls_context.is_restricted and rls_context.country_scope:
        country_list = list(rls_context.country_scope)
        session.execute(
            text(f"SET LOCAL app.country_scope = '{','.join(country_list)}'")
        )


# PostgreSQL function for RLS
"""
CREATE OR REPLACE FUNCTION rls_check_country()
RETURNS BOOLEAN AS $$
BEGIN
    IF current_setting('app.country_scope', true) = '' THEN
        RETURN TRUE;
    END IF;
    RETURN country_code::text = ANY(string_to_array(current_setting('app.country_scope'), ','));
END;
$$ LANGUAGE plpgsql;
"""

