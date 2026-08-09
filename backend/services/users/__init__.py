"""User write-operations subpackage.

Canonical DB-write logic for user/staff entities lives in `user_write_ops`.
Re-exports are wired through `services.users_write_service` for backward
compatibility with legacy imports.
"""
import structlog
logger = structlog.get_logger(__name__)
