"""
Strict Row-Level Security (RLS) middleware for database queries.

Automatically injects country_code filters for non-global admins.
"""
from typing import Optional, List, Callable
from functools import wraps
from sqlalchemy.orm import Query
from fastapi import HTTPException, Depends
import logging

logger = logging.getLogger(__name__)


class RLSMiddleware:
    """Enforces row-level security based on user's country assignments."""
    
    def __init__(self):
        self.country_filter_key = "country_code"
    
    def get_user_countries(self, user_id: int, session_factory: Callable | None = None) -> List[str]:
        """Get list of countries the user is assigned to manage."""
        if session_factory is None:
            from data.db import get_service_session
            session_factory = get_service_session
        
        from data.models import CountryStaffAssignment
        with session_factory() as db:
            assignments = db.query(CountryStaffAssignment).filter(
                CountryStaffAssignment.user_id == user_id,
                CountryStaffAssignment.is_active == True
            ).all()
            return [a.country_code for a in assignments]
    
    def filter_query_by_country(self, query: Query, user_id: Optional[int], is_global_admin: bool = False, session_factory: Callable | None = None) -> Query:
        """Apply country filter to a query based on user's assignments."""
        if is_global_admin or user_id is None:
            return query
        
        countries = self.get_user_countries(user_id, session_factory)
        if not countries:
            raise HTTPException(status_code=403, detail="User not assigned to any country")
        
        model = query.column_descriptions[0]['entity'] if query.column_descriptions else None
        if model and hasattr(model, '__tablename__'):
            if hasattr(model, 'country_code'):
                return query.filter(model.country_code.in_(countries))
        
        return query
    
    def inject_country_context(self, user_id: int, is_global_admin: bool = False, session_factory: Callable | None = None) -> dict:
        """Get country context for the current user."""
        if is_global_admin:
            return {"country_filter": None, "assigned_countries": ["ALL"]}
        
        countries = self.get_user_countries(user_id, session_factory)
        return {
            "country_filter": countries,
            "assigned_countries": countries,
        }


def rls_filter(model_class, country_field='country_code'):
    """
    Decorator to apply RLS filtering to repository methods.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from fastapi import Request
            request = kwargs.get('request') or (args[0].request if args and hasattr(args[0], 'request') else None)
            
            if request and hasattr(request.state, 'user_id'):
                user_id = request.state.user_id
                is_admin = getattr(request.state, 'is_global_admin', False)
                rls = RLSMiddleware()
                countries = rls.get_user_countries(user_id) if not is_admin else []
                kwargs['country_filter'] = countries
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


class CountryScopedRepository:
    """Base repository class with built-in RLS support."""
    
    def __init__(self, model_class, country_field='country_code', session_factory: Callable | None = None):
        self.model_class = model_class
        self.country_field = country_field
        self.rls = RLSMiddleware()
        self._session_factory = session_factory
    
    def _get_session_factory(self) -> Callable:
        if self._session_factory is not None:
            return self._session_factory
        from data.db import get_service_session
        return get_service_session
    
    def find_all(self, user_id: int, is_global_admin: bool = False, **filters):
        """Find all records with RLS filtering."""
        session_factory = self._get_session_factory()
        with session_factory() as db:
            query = db.query(self.model_class)
            
            if not is_global_admin:
                countries = self.rls.get_user_countries(user_id, session_factory)
                if not countries:
                    return []
                query = query.filter(getattr(self.model_class, self.country_field).in_(countries))
            
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)
            
            return query.all()
    
    def find_by_id(self, entity_id: int, user_id: int, is_global_admin: bool = False):
        """Find by ID with RLS check."""
        session_factory = self._get_session_factory()
        with session_factory() as db:
            query = db.query(self.model_class).filter(self.model_class.id == entity_id)
            
            if not is_global_admin:
                countries = self.rls.get_user_countries(user_id, session_factory)
                if not countries:
                    return None
                query = query.filter(getattr(self.model_class, self.country_field).in_(countries))
            
            return query.first()
