#!python
"""
Database Security - Encryption and Query Logging
Implements data protection and query audit logging
"""

import time
import logging
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime
from functools import wraps

from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from utils.redis_client import redis_client
from utils.security_audit import log_security_event

logger = logging.getLogger(__name__)


class QueryLogger:
    """Logs database queries for security audit."""

    def __init__(self):
        self.redis = redis_client()
        self.sensitive_tables = {
            "users", "orders", "payments", "financial_transactions",
            "employee_records", "payouts", "audit_logs"
        }

    def log_query(
        self,
        query: str,
        params: Dict[str, Any],
        user_id: Optional[int] = None,
        duration_ms: float = 0,
    ):
        """Log query for security audit."""
        query_lower = query.lower()

        for table in self.sensitive_tables:
            if table in query_lower:
                log_security_event(
                    action="SENSITIVE_QUERY",
                    user_id=user_id,
                    details={
                        "table": table,
                        "query_type": self._classify_query(query),
                        "duration_ms": duration_ms,
                        "params_hash": self._hash_params(params),
                    },
                )
                break

    def _classify_query(self, query: str) -> str:
        """Classify query type."""
        query_lower = query.lower().strip()
        if query_lower.startswith("select"):
            return "SELECT"
        elif query_lower.startswith("insert"):
            return "INSERT"
        elif query_lower.startswith("update"):
            return "UPDATE"
        elif query_lower.startswith("delete"):
            return "DELETE"
        return "OTHER"

    def _hash_params(self, params: Dict[str, Any]) -> str:
        """Hash parameters for logging."""
        param_str = str(sorted(params.items()))
        return hashlib.sha256(param_str.encode()).hexdigest()[:16]


class EncryptionHelper:
    """Helper for field-level encryption."""

    def __init__(self):
        self.redis = redis_client()

    def encrypt_field(self, value: str, key: str) -> str:
        """Encrypt a field value."""
        if not value:
            return ""

        encryption_key = self._get_encryption_key(key)
        if not encryption_key:
            return value

        import hashlib
        from cryptography.fernet import Fernet
        import base64

        key_bytes = hashlib.sha256(encryption_key.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        f = Fernet(fernet_key)
        return f.encrypt(value.encode()).decode()

    def decrypt_field(self, encrypted_value: str, key: str) -> str:
        """Decrypt a field value."""
        if not encrypted_value:
            return ""

        encryption_key = self._get_encryption_key(key)
        if not encryption_key:
            return encrypted_value

        import base64
        from cryptography.fernet import Fernet

        key_bytes = hashlib.sha256(encryption_key.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        f = Fernet(fernet_key)
        return f.decrypt(encrypted_value.encode()).decode()

    def _get_encryption_key(self, key_name: str) -> Optional[str]:
        """Get encryption key from Redis or config."""
        if self.redis:
            stored_key = self.redis.get(f"encryption_key:{key_name}")
            if stored_key:
                return stored_key

        import os
        return os.environ.get(f"DB_ENCRYPTION_KEY_{key_name}")


def register_query_logging(engine: Engine):
    """Register query logging event listeners."""
    query_logger = QueryLogger()

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        context["query_start_time"] = time.time()
        context["query_statement"] = statement
        context["query_parameters"] = parameters
        context["user_id"] = getattr(conn, "user_id", None)

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        if context.get("query_start_time"):
            duration_ms = (time.time() - context["query_start_time"]) * 1000
            user_id = context.get("user_id")
            query_logger.log_query(
                statement,
                parameters,
                user_id=user_id,
                duration_ms=duration_ms,
            )


class DatabaseSecurityManager:
    """Manages database security configurations."""

    def __init__(self):
        self.redis = redis_client()
        self.encryption_helper = EncryptionHelper()

    def create_encrypted_column(
        self,
        table_name: str,
        column_name: str,
        value: str,
    ) -> str:
        """Create encrypted column value."""
        key = f"{table_name}_{column_name}"
        return self.encryption_helper.encrypt_field(value, key)

    def decrypt_column(
        self,
        table_name: str,
        column_name: str,
        encrypted_value: str,
    ) -> str:
        """Decrypt column value."""
        key = f"{table_name}_{column_name}"
        return self.encryption_helper.decrypt_field(encrypted_value, key)

    def audit_table_access(
        self,
        table_name: str,
        user_id: int,
        action: str,
        record_id: Optional[int] = None,
    ):
        """Audit table access."""
        log_security_event(
            action="TABLE_ACCESS",
            user_id=user_id,
            details={
                "table": table_name,
                "action": action,
                "record_id": record_id,
            },
        )


def secure_execute(session: Session, query, user_id: Optional[int] = None):
    """Execute query with security logging."""
    start_time = time.time()
    try:
        result = query.all()
        duration_ms = (time.time() - start_time) * 1000

        QueryLogger().log_query(
            str(query),
            {},
            user_id=user_id,
            duration_ms=duration_ms,
        )

        return result
    except Exception as e:
        logger.error(f"Query execution error: {e}")
        raise

