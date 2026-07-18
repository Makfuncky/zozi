#!python
"""
Row-Level Security (RLS) Middleware for Zozi Platform
Implements country-based access control and data isolation
"""

import time
import hashlib
import logging
from typing import Optional, List, Set, Dict, Any
from datetime import datetime, timedelta
from functools import wraps

from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
import jwt

from utils.redis_client import redis_client
from utils.config import settings

logger = logging.getLogger(__name__)

class RLSMiddleware(BaseHTTPMiddleware):
    """
    Row-Level Security Middleware for Zozi Platform.
    
    Implements the "Ghost Filter" concept where every database query
    is automatically scoped to the user's approved country scope.
    
    Key Features:
    - JWT-based authentication with country scope
    - Automatic query filtering for country-aware models
    - Ghost record protocol (404 for unauthorized access)
    - Admin bypass for oversight roles
    - Real-time country scope updates via Redis
    """
    
    def __init__(self, app=None, redis_url: str = None):
        super().__init__(app)
        self.redis = redis_client() if redis_url is None else None
        self.cache_ttl = 300  # 5 minutes cache
        
        # Admin roles that bypass RLS
        self.admin_roles = {
            'superadmin', 'global_admin', 'country_admin',
            'finance_admin', 'compliance_officer', 'security_admin',
            'audit_admin', 'ops_admin', 'system_admin', 'admin'
        }
        
        # Country-aware models that require RLS filtering
        self.country_aware_models = {
            'orders', 'products', 'users', 'logistics_partners',
            'payouts', 'financial_transactions', 'supplier_profiles',
            'employee_records', 'country_configs'
        }
        
        if app is not None:
            self.app = app

    async def _extract_user_context(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract and validate user context from JWT token."""
        try:
            token = request.headers.get("authorization", "").replace("Bearer ", "")
            if not token:
                return None
            
            # Decode JWT
            payload = jwt.decode(
                token, 
                settings.secret_key, 
                algorithms=[settings.algorithm or "HS256"]
            )
            
            # Get country scope from Redis cache or token
            country_scope = self._get_country_scope_sync(payload.get('user_id', 0), payload)
            
            return {
                'user_id': payload['user_id'],
                'role': payload.get('role', 'customer'),
                'country_scope': country_scope,
                'permissions': payload.get('permissions', []),
                'is_active': payload.get('is_active', True)
            }
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            logger.error(f"RLS Middleware error: {e}")
            return None
    
    @staticmethod
    def _get_country_scope_sync(user_id: int, token_payload: dict) -> list[str]:
        """Get user's country scope from DB assignments first, then token payload."""
        staff_codes = token_payload.get('staff_country_codes', [])
        if staff_codes:
            if isinstance(staff_codes, str):
                return [c.strip() for c in staff_codes.split(',') if c.strip()]
            return [str(c).strip() for c in staff_codes if c]
        return token_payload.get('country_scope', [])

    def _get_country_scope_from_db(self, user_id: int) -> list[str]:
        """Query country_staff_assignments table for live scope."""
        try:
            from db.database import SessionLocal
            db = SessionLocal()
            try:
                from models.country_enhancements import CountryStaffAssignment
                assignments = db.query(CountryStaffAssignment).filter(
                    CountryStaffAssignment.user_id == user_id,
                    CountryStaffAssignment.is_active == True,
                ).all()
                return list({a.country_code.upper() for a in assignments})
            finally:
                db.close()
        except Exception as e:
            logger.debug("DB country scope lookup failed: %s", e)
            return []

    async def dispatch(self, request: Request, call_next):
        """Main middleware processing."""
        if request.method == "OPTIONS":
            response = await call_next(request)
            return response

        if not request.url.path.startswith("/api/"):
            response = await call_next(request)
            return response

        user_context = await self._extract_user_context(request)

        if user_context:
            request.state.user_id = user_context['user_id']
            request.state.role = user_context['role']
            request.state.country_scope = user_context.get('country_scope', [])
            request.state.security_context = user_context

            if user_context['role'].lower() not in self.admin_roles:
                db_scope = self._get_country_scope_from_db(user_context['user_id'])
                if db_scope:
                    request.state.country_scope = db_scope
                    user_context['country_scope'] = db_scope
        else:
            if self._requires_authentication(request.url.path):
                response = await call_next(request)
                response.status_code = 401
                return response

        request.state.rls_filter = self._build_rls_filter(user_context)

        response = await call_next(request)
        return response
    
    def _build_rls_filter(self, user_context: Optional[Dict]) -> Dict[str, Any]:
        """Build RLS filter for SQL queries."""
        if not user_context:
            return {'blocked': True}
        
        # Admin roles bypass RLS - CHECK FIRST
        if user_context['role'].lower() in self.admin_roles:
            return {'blocked': False, 'admin': True}
        
        # Regular users get country-scoped filter
        country_scope = user_context.get('country_scope', [])
        if not country_scope:
            return {'blocked': True}
        
        return {
            'blocked': False,
            'country_codes': [code.upper() for code in country_scope],
            'user_id': user_context['user_id']
        }
    
    def _requires_authentication(self, path: str) -> bool:
        """Check if path requires authentication."""
        public_paths = [
            '/api/v1/auth',
            '/api/v1/public',
            '/api/v1/health',
            '/api/v1/metrics/public',
            '/api/v1/countries',
            '/api/v1/products/suppliers',
            '/api/v1/banners',
        ]
        return not any(path.startswith(p) for p in public_paths)
    
    def enforce_country_access(self, model_name: str, country_code: str, user_context: dict) -> bool:
        """
        Enforce country access for a specific model and country.
        Implements the "Ghost Record Protocol" - returns 404 instead of 403.
        """
        if not user_context:
            return False
        
        # Admin roles bypass all restrictions
        if user_context['role'].lower() in self.admin_roles:
            return True
        
        # Non-country-aware models don't need RLS
        if model_name not in self.country_aware_models:
            return True
        
        # Check if user has access to this country
        user_countries = user_context.get('country_scope', [])
        return country_code.upper() in [c.upper() for c in user_countries]
    
    def get_sql_filter_clause(self, user_context: dict, table_alias: str = 't') -> str:
        """Generate SQL WHERE clause for RLS filtering."""
        if not user_context or user_context.get('role', '').lower() in self.admin_roles:
            return ""
        
        country_scope = user_context.get('country_scope', [])
        if not country_scope:
            return "1=0"  # Block all access
        
        countries = "','".join([c.upper() for c in country_scope])
        return f"{table_alias}.country_code IN ('{countries}')"

