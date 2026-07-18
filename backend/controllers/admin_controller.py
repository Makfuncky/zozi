"""
Admin Controller â€” admin-only business logic for user, product, order management,
staff account creation, audit log review, and platform analytics.
"""
from collections import Counter
from decimal import Decimal
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
from typing import Any, List, Optional, cast

import stripe
from fastapi import Depends, HTTPException
from sqlalchemy import String, desc, exists, func, inspect, or_, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from db.database import Base
from models import (
    AdminAnalyticsSnapshot,
    Address, AuditLog, BadgeBillingRecord, Banner, CampaignRecipient, CartItem,
    ChatbotQueryEvent, CommissionAgreement, CommissionBadgeTier,
    CommissionCategoryRate, CommissionGlobalConfig, CommissionLedgerEntry, Coupon,
    CouponUsage, EmailCampaign, EmailProviderConfig, EmailTemplate,
    EmailVerificationToken, FinanceBankAccount, Invoice, InvoiceItem,
    LogisticsCategoryPricingRule, LogisticsCODRemittanceReceipt, LogisticsPartner,
    LogisticsPartnerBankAccount, LogisticsPartnerDocument, LogisticsPartnerServiceArea,
    LogisticsPricingProfile, LogisticsSettlement, LogisticsVehicleRule, Notification,
    Order, OrderItem, OrderLogisticsAllocation, PasswordResetToken, PaymentGatewayConnection,
    PaymentProviderConfig, Payout, Product, ProductCommissionOverride, ProductVerification,
    PromotionEngineConfig, PromotionLedgerEntry, PromotionOrderTier, PushNotificationToken,
    ReferralPointEvent, RefundLedger, ReturnRequest, Review, RevokedToken,
    RolePermissionSetting, Shipment, ShipmentConfirmation, ShipmentEvent, ShippingCarrier,
    ShippingZone, SupplierBankAccount, SupplierDocument, SupplierProfile, SupplierSettlement,
    SupportTicket, TicketAttachment, TicketMessage, TicketReply, TransactionLedger, User, VATRemittance,
    Wishlist, CountryConfig, FlashSale, Category,
    BankTransaction,
)
from db.schemas import CreateStaffAccount, UpdateStaffAccount, _normalize_image_path
from controllers.cache_utils import build_versioned_cache_key, cache_get_json, cache_set_json
from controllers.audit_controller import AuditAction, audit_log, get_audit_logs, get_unique_actions
from controllers.soft_delete import soft_delete, restore, hard_delete, bulk_soft_delete, bulk_restore
from utils.dependencies import get_current_user as _orm_get_current_user
# Import the dict-returning get_current_user for role-based dependencies
from controllers.auth_controller import get_current_user as _dict_get_current_user
from controllers.payments_controller import apply_order_status_change
from services.finance_transfer_service import build_transfer_reference
from utils.auth import get_password_hash, get_redis_health_status
from utils.backup import get_backup_manager
from utils.config import settings
from utils.constants import STAFF_ROLES
from utils.order_tracking import order_status_label, reconcile_order_status
from utils.staff_permissions import (
    DEFAULT_ROLE_PERMISSION_MAP,
    KNOWN_ROLE_PERMISSIONS,
    STAFF_PERMISSION_GROUPS,
    default_permissions_for_role,
    sanitize_staff_permissions,
)

logger = logging.getLogger(__name__)
_ADMIN_DEFAULT_PAGE_SIZE = 50
_ADMIN_MAX_PAGE_SIZE = 100
_ANALYTICS_CACHE_TTL_SECONDS = 300
_ANALYTICS_SNAPSHOT_TTL = timedelta(minutes=15)
_PERIOD_DAYS = {"7d": 7, "30d": 30, "90d": 90, "365d": 365}

# Expose the ORM version as get_current_user for backwards compatibility
get_current_user = _orm_get_current_user


def _build_list_page_payload(items: list[Any], total: int, *, offset: int = 0, page_size: Optional[int] = None) -> dict[str, Any]:
    resolved_page_size = page_size if page_size is not None else len(items)
    if resolved_page_size <= 0:
        resolved_page_size = max(total, 1)
    return {
        "data": items,
        "total": total,
        "page": (offset // resolved_page_size) + 1,
        "pageSize": resolved_page_size,
    }


def _load_admin_analytics_snapshot(snapshot_key: str, db: Session) -> dict[str, Any] | None:
    snapshot = db.query(AdminAnalyticsSnapshot).filter(AdminAnalyticsSnapshot.snapshot_key == snapshot_key).first()
    if snapshot is None:
        return None
    expires_at = cast(datetime | None, getattr(snapshot, "expires_at", None))
    if expires_at is not None and expires_at <= datetime.now(timezone.utc).replace(tzinfo=None):
        return None
    try:
        payload = json.loads(cast(str, getattr(snapshot, "payload_json")))
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _store_admin_analytics_snapshot(
    snapshot_key: str,
    snapshot_group: str,
    payload: dict[str, Any],
    db: Session,
    *,
    period: str | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_at = now + _ANALYTICS_SNAPSHOT_TTL
    snapshot = db.query(AdminAnalyticsSnapshot).filter(AdminAnalyticsSnapshot.snapshot_key == snapshot_key).first()
    serialized_payload = json.dumps(payload, default=str)
    if snapshot is None:
        snapshot = AdminAnalyticsSnapshot(
            snapshot_key=snapshot_key,
            snapshot_group=snapshot_group,
            period=period,
            payload_json=serialized_payload,
            computed_at=now,
            expires_at=expires_at,
        )
        db.add(snapshot)
    else:
        setattr(snapshot, "snapshot_group", snapshot_group)
        setattr(snapshot, "period", period)
        setattr(snapshot, "payload_json", serialized_payload)
        setattr(snapshot, "computed_at", now)
        setattr(snapshot, "expires_at", expires_at)
    db.flush()
    return payload


def _get_admin_analytics_payload(
    snapshot_key: str,
    snapshot_group: str,
    compute: callable,
    db: Session,
    *,
    cache_payload: dict[str, Any] | None = None,
    period: str | None = None,
) -> dict[str, Any]:
    cache_key = build_versioned_cache_key(
        "admin_analytics",
        snapshot_key,
        cache_payload or {"period": period or ""},
    )
    cached_payload = cache_get_json(cache_key)
    if isinstance(cached_payload, dict):
        return cached_payload

    persisted_payload = _load_admin_analytics_snapshot(snapshot_key, db)
    if persisted_payload is not None:
        cache_set_json(cache_key, persisted_payload, _ANALYTICS_CACHE_TTL_SECONDS)
        return persisted_payload

    payload = compute()
    payload = _store_admin_analytics_snapshot(snapshot_key, snapshot_group, payload, db, period=period)
    cache_set_json(cache_key, payload, _ANALYTICS_CACHE_TTL_SECONDS)
    return payload


def refresh_admin_analytics_snapshots(db: Session) -> dict[str, Any]:
    snapshots = {
        "overview": _compute_analytics_overview(db),
        "timeseries:7d": _compute_analytics_timeseries_payload("7d", db),
        "timeseries:30d": _compute_analytics_timeseries_payload("30d", db),
        "timeseries:90d": _compute_analytics_timeseries_payload("90d", db),
        "top-products:10": _compute_top_products_payload(10, db),
        "user-growth:30d": _compute_user_growth_payload("30d", db),
    }
    for snapshot_key, payload in snapshots.items():
        if snapshot_key.startswith("timeseries:"):
            period = snapshot_key.split(":", 1)[1]
            snapshot_group = "timeseries"
        elif snapshot_key.startswith("top-products:"):
            period = snapshot_key.split(":", 1)[1]
            snapshot_group = "top-products"
        elif snapshot_key.startswith("user-growth:"):
            period = snapshot_key.split(":", 1)[1]
            snapshot_group = "user-growth"
        else:
            period = None
            snapshot_group = snapshot_key
        _store_admin_analytics_snapshot(snapshot_key, snapshot_group, payload, db, period=period)
    return {"refreshed": len(snapshots), "keys": sorted(snapshots.keys())}

ROLE_PERMISSION_MAP: dict[str, set[str]] = {
    role: set(permissions)
    for role, permissions in DEFAULT_ROLE_PERMISSION_MAP.items()
}

VALID_USER_ROLES = {"customer", "supplier", "admin", "sub_admin", "moderator", "support"}


def _effective_staff_permissions(user: User) -> list[str]:
    assigned_permissions = sanitize_staff_permissions(getattr(user, "staff_permissions", None))
    if assigned_permissions:
        return assigned_permissions
    return default_permissions_for_role(cast(str | None, getattr(user, "role", None)))


def _serialize_staff_user(user: User) -> dict[str, Any]:
    return {
        "id": cast(int, getattr(user, "id")),
        "username": cast(str, getattr(user, "username")),
        "full_name": cast(str | None, getattr(user, "full_name", None)) or cast(str, getattr(user, "username")),
        "email": cast(str, getattr(user, "email")),
        "phone": cast(str | None, getattr(user, "phone", None)),
        "role": cast(str, getattr(user, "role")),
        "is_active": bool(cast(Any, getattr(user, "is_active", False))),
        "staff_role_label": cast(str | None, getattr(user, "staff_role_label", None)),
        "staff_title": cast(str | None, getattr(user, "staff_title", None)),
        "staff_department": cast(str | None, getattr(user, "staff_department", None)),
        "staff_area_of_operation": cast(str | None, getattr(user, "staff_area_of_operation", None)),
        "staff_hire_date": getattr(user, "staff_hire_date", None),
        "staff_experience_level": cast(str | None, getattr(user, "staff_experience_level", None)),
        "staff_performance_summary": cast(str | None, getattr(user, "staff_performance_summary", None)),
        "staff_assigned_tasks": list(getattr(user, "staff_assigned_tasks", None) or []),
        "staff_assigned_projects": list(getattr(user, "staff_assigned_projects", None) or []),
        "permissions": _effective_staff_permissions(user),
        "staff_notes": cast(str | None, getattr(user, "staff_notes", None)),
        "created_at": cast(datetime, getattr(user, "created_at")),
    }


def get_staff_permission_catalog() -> dict[str, Any]:
    return {
        "groups": [
            {
                "key": cast(str, group["key"]),
                "label": cast(str, group["label"]),
                "permissions": list(cast(tuple[str, ...], group["permissions"])),
            }
            for group in STAFF_PERMISSION_GROUPS
        ],
        "defaults": {
            role: default_permissions_for_role(role)
            for role in sorted(DEFAULT_ROLE_PERMISSION_MAP.keys())
        },
    }


def list_staff_accounts(db: Session) -> list[dict[str, Any]]:
    staff_users = (
        db.query(User)
        .filter(User.role.in_(tuple(STAFF_ROLES)))
        .order_by(User.created_at.desc())
        .all()
    )
    return [_serialize_staff_user(user) for user in staff_users]


def get_current_admin(current_user: dict = Depends(_dict_get_current_user)):
    """Allow any staff-level role to access the admin dashboard."""
    if current_user["role"] not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Staff access required")
    return current_user


def require_admin(current_user: dict = Depends(_dict_get_current_user)):
    """Require full admin role for sensitive operations."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin-only access required")
    return current_user


def require_admin_2fa_enabled(current_user: dict = Depends(_dict_get_current_user)):
    """Require that the admin user has TOTP 2FA enabled."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin-only access required")
    if not current_user.get("totp_enabled"):
        raise HTTPException(
            status_code=403,
            detail="Two-factor authentication must be enabled for admin accounts. "
            "Please set up 2FA in your account security settings before proceeding.",
        )
    return current_user


ADMIN_2FA_VERIFY_TTL = 900  # 15 minutes


def require_admin_2fa_verified(current_user: dict = Depends(_dict_get_current_user)):
    """Require admin or sub_admin role AND a recent 2FA verification for sensitive operations."""
    if current_user["role"] not in {"admin", "sub_admin"}:
        raise HTTPException(status_code=403, detail="Admin-only access required")
    if os.getenv("APP_ENV", "").lower() == "test":
        return current_user
    if not current_user.get("totp_enabled"):
        raise HTTPException(
            status_code=403,
            detail="Two-factor authentication must be enabled for admin accounts.",
        )
    admin_2fa_ts = current_user.get("admin_2fa_verified")
    if not admin_2fa_ts:
        raise HTTPException(
            status_code=403,
            detail="2FA verification required for this action. "
            "Please call POST /auth/2fa/admin-verify with a TOTP code.",
        )
    now = datetime.now(timezone.utc).timestamp()
    if now - float(admin_2fa_ts) > ADMIN_2FA_VERIFY_TTL:
        raise HTTPException(
            status_code=403,
            detail="2FA verification expired. Please call POST /auth/2fa/admin-verify again.",
        )
    return current_user


def require_roles(*allowed_roles: str):
    """Build a FastAPI dependency that restricts access to one or more roles."""
    allowed = tuple(dict.fromkeys(allowed_roles))
    if not allowed:
        raise ValueError("require_roles requires at least one role")

    def dependency(current_user: dict = Depends(_dict_get_current_user)):
        role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, "role", None)
        if role not in allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Access restricted to roles: {', '.join(allowed)}",
            )
        return current_user

    return dependency


def require_permission(permission: str, current_user) -> None:
    role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, "role", None)
    if role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Staff access required")
    explicit_permissions = current_user.get("permissions") if isinstance(current_user, dict) else getattr(current_user, "permissions", None)
    if isinstance(explicit_permissions, (list, tuple, set)):
        allowed = {str(item).strip() for item in explicit_permissions if str(item).strip()}
    else:
        allowed = ROLE_PERMISSION_MAP.get(role, set())
    if permission not in allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Role '{role}' is not allowed to perform this action",
        )


def require_country_access(country_code: str, current_user) -> None:
    """Ensure the current user can manage the given country.

    Full admins can access any country. Country-heads and country-managers
    are restricted to their ``staff_country_codes`` list.
    """
    role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, "role", None)
    if role == "admin":
        return
    if role not in ("country_head", "country_manager"):
        raise HTTPException(status_code=403, detail="Country-level access required")
    allowed_codes = current_user.get("staff_country_codes") if isinstance(current_user, dict) else getattr(current_user, "staff_country_codes", None)
    if not allowed_codes or not isinstance(allowed_codes, (list, tuple)):
        raise HTTPException(status_code=403, detail="You are not assigned to any country")
    if country_code not in [str(c).strip().upper() for c in allowed_codes]:
        raise HTTPException(
            status_code=403,
            detail=f"You do not have access to country '{country_code}'",
        )


def _database_health_snapshot(db: Session) -> tuple[bool, str]:
    try:
        db.execute(text("SELECT 1"))
        return True, "ok"
    except Exception:
        return False, "connection_failed"


def _safe_database_location() -> str:
    if settings.database_url == "sqlite:///:memory:":
        return ":memory:"
    if settings.database_url.startswith("sqlite:///"):
        return settings.database_url.removeprefix("sqlite:///")
    return "managed server"


def _table_row_count(db: Session, table_name: str) -> int | None:
    bind = cast(Any, db.get_bind())
    try:
        quoted_table_name = bind.dialect.identifier_preparer.quote_identifier(table_name)
        count_value = db.execute(text(f"SELECT COUNT(*) FROM {quoted_table_name}")).scalar()
        return 0 if count_value is None else int(count_value)
    except Exception:
        return None


def _table_column_details(columns: list[dict[str, Any]], primary_key: list[str]) -> list[dict[str, Any]]:
    primary_key_set = {str(column) for column in primary_key}
    details: list[dict[str, Any]] = []
    for column in columns:
        column_name = column.get("name")
        if not column_name:
            continue
        details.append(
            {
                "name": str(column_name),
                "type": str(column.get("type")),
                "nullable": bool(column.get("nullable", True)),
                "default": None if column.get("default") is None else str(column.get("default")),
                "primary_key": str(column_name) in primary_key_set,
            }
        )
    return details


def _sqlite_service_snapshot(active_engine: str) -> dict[str, Any]:
    active = active_engine == "sqlite"
    location = _safe_database_location() if active else None
    exists: bool | None = None
    if active and location not in {None, ":memory:", "managed server"}:
        exists = Path(location).exists()
    return {
        "label": "SQLite",
        "status": "active" if active else "supported",
        "active": active,
        "configured": active,
        "role": "Primary relational database for local file-backed runtime when DATABASE_URL uses sqlite:///.",
        "detail": "This runtime is currently backed by a local SQLite database file." if active else "SQLite support is built in for local development, but this runtime is not pointed at SQLite.",
        "location": location,
        "exists": exists,
        "backup_format": ".sqlite",
        "backup_strategy": "sqlite online backup API",
        "handles": ["canonical relational data", "schema introspection", "local file backups"],
    }


def _postgres_service_snapshot(active_engine: str) -> dict[str, Any]:
    active = active_engine == "postgresql"
    configured = settings.database_url.startswith("postgresql")
    parsed_url = make_url(settings.database_url)
    toolchain_ready = bool(shutil.which("pg_dump") and shutil.which("pg_restore")) if (active or configured) else None
    return {
        "label": "PostgreSQL",
        "status": "active" if active else "configured" if configured else "supported",
        "active": active,
        "configured": configured,
        "role": "Server-grade relational database option for production and multi-instance deployments.",
        "detail": "This runtime is currently backed by PostgreSQL." if active else "PostgreSQL is supported as the primary relational database when DATABASE_URL uses postgresql://.",
        "host": parsed_url.host if (active or configured) else None,
        "database": parsed_url.database if (active or configured) else None,
        "driver": parsed_url.drivername if (active or configured) else None,
        "toolchain_ready": toolchain_ready,
        "backup_format": ".pgdump",
        "backup_strategy": "pg_dump -Fc",
        "handles": ["canonical relational data", "multi-instance production persistence", "compressed logical backups"],
    }


def _redis_service_snapshot() -> dict[str, Any]:
    redis_status = get_redis_health_status()
    configured = bool(redis_status.get("configured", False))
    available = bool(redis_status.get("available", False))
    backend = str(redis_status.get("backend", "memory_fallback"))
    return {
        "label": "Redis",
        "status": "ready" if available else "degraded" if configured else "not_configured",
        "active": available,
        "configured": configured,
        "available": available,
        "role": "Optional cache and shared ephemeral state store; it does not replace the primary relational database.",
        "detail": "Redis is connected and serving shared cache/state." if available else "Redis is not connected; the app falls back to in-memory state for cache-like behavior in this runtime." if configured else "Redis is not configured for this runtime.",
        "backend": backend,
        "fallback_mode": "memory" if configured and not available else None,
        "shared_state": bool(redis_status.get("shared_state", False)),
        "handles": ["token blacklist", "shared cache", "background job coordination"],
    }


def _database_architecture_snapshot(active_engine: str) -> dict[str, Any]:
    return {
        "mode": "single_primary_relational_with_optional_cache",
        "primary_database_engine": active_engine,
        "summary": "SQLite or PostgreSQL is the single source of truth for business data at runtime, selected by DATABASE_URL. Redis only accelerates cache and shared ephemeral state.",
        "write_path": "All canonical reads and writes go to the active relational database engine.",
        "cache_path": "Redis supplements the relational database for cache, token blacklist, and shared runtime state when available.",
    }


def get_database_overview(db: Session) -> dict[str, Any]:
    cache_key = "admin:db:overview"
    cached = cache_get_json(cache_key)
    if isinstance(cached, dict):
        return cached
    bind = cast(Any, db.get_bind())
    inspector = inspect(bind)
    table_names = sorted(inspector.get_table_names())
    orm_table_names = set(Base.metadata.tables.keys())
    tables: list[dict[str, Any]] = []

    for table_name in table_names:
        columns = inspector.get_columns(table_name)
        primary_key = inspector.get_pk_constraint(table_name).get("constrained_columns") or []
        indexes = inspector.get_indexes(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)
        tables.append(
            {
                "name": table_name,
                "row_count": _table_row_count(db, table_name),
                "column_count": len(columns),
                "columns": [str(column.get("name")) for column in columns if column.get("name")],
                "column_details": _table_column_details(columns, [str(column) for column in primary_key]),
                "primary_key": [str(column) for column in primary_key],
                "indexes": [str(index.get("name")) for index in indexes if index.get("name")],
                "index_count": len(indexes),
                "foreign_keys": [
                    {
                        "constrained_columns": [str(column) for column in (foreign_key.get("constrained_columns") or [])],
                        "referred_table": str(foreign_key.get("referred_table")) if foreign_key.get("referred_table") else None,
                        "referred_columns": [str(column) for column in (foreign_key.get("referred_columns") or [])],
                    }
                    for foreign_key in foreign_keys
                ],
                "foreign_key_count": len(foreign_keys),
                "orm_managed": table_name in orm_table_names,
            }
        )

    healthy, db_health = _database_health_snapshot(db)
    alembic_version: str | None = None
    if "alembic_version" in table_names:
        try:
            version_value = db.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar()
            alembic_version = str(version_value) if version_value else None
        except Exception:
            alembic_version = None

    backups = get_backup_manager().list_backups()
    latest_backup = backups[0] if backups else None
    missing_model_tables = sorted(orm_table_names.difference(table_names))
    managed_table_count = sum(1 for table in tables if bool(table.get("orm_managed")))
    inspected_at = datetime.now(timezone.utc).isoformat()
    active_engine = str(bind.dialect.name)

    payload = {
        "status": "healthy" if healthy else "unhealthy",
        "inspected_at": inspected_at,
        "refresh_interval_seconds": 20,
        "database": {
            "engine": bind.dialect.name,
            "driver": bind.dialect.driver,
            "location": _safe_database_location(),
            "connected": healthy,
            "health": db_health,
            "app_env": settings.app_env,
            "runtime_profile": settings.runtime_profile,
            "alembic_version": alembic_version,
            "backup_strategy": "sqlite online backup API" if active_engine == "sqlite" else "pg_dump -Fc" if active_engine == "postgresql" else "engine-specific",
        },
        "architecture": _database_architecture_snapshot(active_engine),
        "services": {
            "sqlite": _sqlite_service_snapshot(active_engine),
            "postgresql": _postgres_service_snapshot(active_engine),
            "redis": _redis_service_snapshot(),
        },
        "backup": {
            "enabled": settings.backup_enabled,
            "artifact_count": len(backups),
            "latest_filename": latest_backup.get("filename") if latest_backup else None,
            "latest_created_at": latest_backup.get("created_at") if latest_backup else None,
            "latest_verified": latest_backup.get("verified") if latest_backup else None,
            "latest_size_bytes": latest_backup.get("size_bytes") if latest_backup else None,
        },
        "totals": {
            "table_count": len(table_names),
            "orm_model_table_count": len(orm_table_names),
            "managed_table_count": managed_table_count,
            "extra_table_count": max(len(table_names) - managed_table_count, 0),
            "missing_model_table_count": len(missing_model_tables),
        },
        "tables_missing_from_database": missing_model_tables,
        "tables": tables,
    }
    cache_set_json(cache_key, payload, 30)
    return payload


def load_role_permission_settings(db: Session) -> dict[str, set[str]]:
    """Reload the runtime role-permission matrix from persisted DB overrides."""
    next_map = {
        role: set(permissions)
        for role, permissions in DEFAULT_ROLE_PERMISSION_MAP.items()
    }
    rows = db.query(RolePermissionSetting).all()
    for row in rows:
        role = cast(str | None, getattr(row, "role", None))
        if role not in next_map:
            continue

        raw_permissions = getattr(row, "permissions", None)
        if isinstance(raw_permissions, str):
            serialized_permissions = raw_permissions.strip()
            if serialized_permissions:
                try:
                    raw_permissions = json.loads(serialized_permissions)
                except (TypeError, ValueError, json.JSONDecodeError):
                    raw_permissions = [item.strip() for item in serialized_permissions.split(",")]
            else:
                raw_permissions = []
        if isinstance(raw_permissions, dict):
            raw_permissions = raw_permissions.get("permissions", [])
        if isinstance(raw_permissions, (list, tuple, set)):
            next_map[role] = {
                str(permission).strip()
                for permission in raw_permissions
                if str(permission).strip() in KNOWN_ROLE_PERMISSIONS
            }
            continue

        permission_name = str(getattr(row, "permission", "") or "").strip()
        if permission_name not in KNOWN_ROLE_PERMISSIONS:
            continue
        is_granted = bool(getattr(row, "is_granted", True))
        if is_granted:
            next_map[role].add(permission_name)
        else:
            next_map[role].discard(permission_name)

    ROLE_PERMISSION_MAP.clear()
    ROLE_PERMISSION_MAP.update(next_map)
    return ROLE_PERMISSION_MAP


def get_all_users(db: Session, limit: Optional[int] = None, offset: int = 0) -> dict[str, Any]:
    resolved_limit = _ADMIN_DEFAULT_PAGE_SIZE if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))
    query = db.query(User).order_by(User.created_at.desc())
    total = query.count()
    if offset:
        query = query.offset(offset)
    query = query.limit(resolved_limit)
    users = query.all()
    if not users:
        return _build_list_page_payload([], total, offset=offset, page_size=resolved_limit)

    user_ids = [cast(int, getattr(user, "id")) for user in users]
    profiles = {
        cast(int, getattr(profile, "user_id")): profile
        for profile in db.query(SupplierProfile).filter(SupplierProfile.user_id.in_(user_ids)).all()
    }

    items = []
    for user in users:
        profile = profiles.get(cast(int, getattr(user, "id")))
        verification_status = cast(str | None, getattr(profile, "verification_status", None)) if profile else None
        if not verification_status:
            if bool(cast(Any, getattr(user, "is_verified", False))):
                verification_status = "verified"
            elif bool(cast(Any, getattr(user, "email_verified", False))):
                verification_status = "email_verified"
            else:
                verification_status = "pending"

        items.append({
            "id": cast(int, getattr(user, "id")),
            "email": getattr(user, "email"),
            "username": getattr(user, "username"),
            "full_name": getattr(user, "full_name", None),
            "phone": getattr(user, "phone", None),
            "role": getattr(user, "role"),
            "is_active": bool(getattr(user, "is_active", False)),
            "is_verified": bool(getattr(user, "is_verified", False)),
            "email_verified": bool(getattr(user, "email_verified", False)),
            "verification_status": verification_status,
            "verified_at": getattr(profile, "verified_at", None) if profile else None,
            "created_at": getattr(user, "created_at"),
            "last_login": getattr(user, "last_login", None),
            "preferred_country": getattr(user, "preferred_country", None),
            "preferred_currency": getattr(user, "preferred_currency", None),
            "country_code": getattr(user, "country_code", None),
        })

    return _build_list_page_payload(items, total, offset=offset, page_size=resolved_limit)


def update_user_role(user_id: int, role: str, acting_user: dict, db: Session) -> dict:
    if role not in VALID_USER_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(sorted(VALID_USER_ROLES))}")

    if role in STAFF_ROLES and acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can assign staff roles")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = cast(str, getattr(user, "role"))
    setattr(user, "role", role)
    db.commit()

    audit_log(
        db=db,
        action=AuditAction.ROLE_CHANGED,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="user",
        resource_id=user_id,
        details={"old_role": old_role, "new_role": role, "target_user": user.username},
        status="success",
    )
    return {"message": "User role updated", "old_role": old_role, "new_role": role}


def toggle_user_active(user_id: int, acting_user: dict, db: Session) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    current_active = bool(cast(Any, getattr(user, "is_active")))
    setattr(user, "is_active", 0 if current_active else 1)
    db.commit()
    audit_log(
        db=db,
        action="USER_ACTIVE_TOGGLED",
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="user",
        resource_id=user_id,
        details={"is_active": bool(cast(Any, getattr(user, "is_active")))},
        status="success",
    )
    return {"id": cast(int, getattr(user, "id")), "is_active": cast(Any, getattr(user, "is_active"))}


# Protected demo accounts that cannot be deleted
_PROTECTED_EMAILS: set[str] = {"admin@zozi.com"}

_DELETE_BLOCKING_SUPPLIER_MODELS: list[tuple[Any, Any, str]] = [
    (Shipment, Shipment.supplier_id, "shipment(s) as supplier"),
    (
        OrderLogisticsAllocation,
        getattr(OrderLogisticsAllocation, "supplier_id", OrderLogisticsAllocation.partner_id),
        "logistics allocation record(s)",
    ),
    (Invoice, Invoice.supplier_id, "invoice record(s)"),
    (TransactionLedger, TransactionLedger.supplier_id, "financial ledger record(s)"),
    (SupplierSettlement, SupplierSettlement.supplier_id, "supplier settlement record(s)"),
    (CommissionLedgerEntry, CommissionLedgerEntry.supplier_id, "commission ledger record(s)"),
    (BadgeBillingRecord, BadgeBillingRecord.supplier_id, "badge billing record(s)"),
]

_NULLABLE_USER_REFERENCE_UPDATES: list[tuple[Any, Any, str]] = [
    (User, User.referred_by_user_id, "referred_by_user_id"),
    (AuditLog, AuditLog.user_id, "user_id"),
    (ReferralPointEvent, ReferralPointEvent.referred_user_id, "referred_user_id"),
    (ChatbotQueryEvent, ChatbotQueryEvent.user_id, "user_id"),
    (CampaignRecipient, CampaignRecipient.user_id, "user_id"),
    (EmailTemplate, EmailTemplate.created_by, "created_by"),
    (EmailCampaign, EmailCampaign.created_by, "created_by"),
    (ShippingCarrier, ShippingCarrier.supplier_id, "supplier_id"),
    (Shipment, Shipment.packaged_by_user_id, "packaged_by_user_id"),
    (ShipmentEvent, ShipmentEvent.actor_user_id, "actor_user_id"),
    (Banner, Banner.created_by, "created_by"),
    (SupplierDocument, SupplierDocument.reviewed_by, "reviewed_by"),
    (ProductVerification, ProductVerification.verified_by, "verified_by"),
    (LogisticsPartner, LogisticsPartner.user_id, "user_id"),
    (LogisticsPartner, LogisticsPartner.verified_by, "verified_by"),
    (LogisticsPartnerDocument, LogisticsPartnerDocument.reviewed_by, "reviewed_by"),
    (LogisticsPartnerServiceArea, LogisticsPartnerServiceArea.reviewed_by, "reviewed_by"),
    (LogisticsPricingProfile, LogisticsPricingProfile.reviewed_by, "reviewed_by"),
    (LogisticsCategoryPricingRule, LogisticsCategoryPricingRule.reviewed_by, "reviewed_by"),
    (LogisticsVehicleRule, LogisticsVehicleRule.reviewed_by, "reviewed_by"),
    (PromotionEngineConfig, PromotionEngineConfig.updated_by, "updated_by"),
    (PromotionOrderTier, PromotionOrderTier.updated_by, "updated_by"),
    (PromotionLedgerEntry, PromotionLedgerEntry.user_id, "user_id"),
    (PaymentGatewayConnection, PaymentGatewayConnection.gateway_name, "gateway_name"),
    (PaymentProviderConfig, PaymentProviderConfig.updated_by, "updated_by"),
    (EmailProviderConfig, EmailProviderConfig.updated_by, "updated_by"),
    (LogisticsCODRemittanceReceipt, LogisticsCODRemittanceReceipt.reviewed_by, "reviewed_by"),
    (BankTransaction, BankTransaction.linked_supplier_id, "linked_supplier_id"),
    (BankTransaction, BankTransaction.reconciled_by, "reconciled_by"),
    (VATRemittance, VATRemittance.remitted_by, "remitted_by"),
    (SupplierBankAccount, SupplierBankAccount.verified_by, "verified_by"),
    (LogisticsPartnerBankAccount, LogisticsPartnerBankAccount.verified_by, "verified_by"),
    (FinanceBankAccount, FinanceBankAccount.created_by, "created_by"),
    (FinanceBankAccount, FinanceBankAccount.updated_by, "updated_by"),
    (RolePermissionSetting, RolePermissionSetting.role, "role"),
    (TicketReply, TicketReply.sender_id, "sender_id"),
    (SupportTicket, SupportTicket.user_id, "user_id"),
    (CommissionAgreement, CommissionAgreement.set_by_admin_id, "set_by_admin_id"),
    (ProductCommissionOverride, ProductCommissionOverride.set_by_admin_id, "set_by_admin_id"),
    (CommissionGlobalConfig, CommissionGlobalConfig.updated_by, "updated_by"),
    (CommissionCategoryRate, CommissionCategoryRate.category_id, "category_id"),
    (CommissionBadgeTier, CommissionBadgeTier.name, "name"),
    (CommissionLedgerEntry, CommissionLedgerEntry.adjusted_by, "adjusted_by"),
    (BadgeBillingRecord, BadgeBillingRecord.user_id, "user_id"),
]

_DELETABLE_USER_OWNED_MODELS: list[tuple[Any, Any]] = [
    (ReferralPointEvent, ReferralPointEvent.user_id),
    (Wishlist, Wishlist.user_id),
    (Address, Address.user_id),
    (Review, Review.user_id),
    (Notification, Notification.user_id),
    (CouponUsage, CouponUsage.user_id),
    (PasswordResetToken, PasswordResetToken.user_id),
    (EmailVerificationToken, EmailVerificationToken.user_id),
    (ReturnRequest, ReturnRequest.customer_id),
    (Payout, Payout.supplier_id),
    (CartItem, CartItem.user_id),
    (PushNotificationToken, PushNotificationToken.user_id),
    (RevokedToken, RevokedToken.user_id),
    (ShippingZone, ShippingZone.supplier_id),
    (SupplierDocument, SupplierDocument.supplier_id),
    (SupplierProfile, SupplierProfile.user_id),
    (SupplierBankAccount, SupplierBankAccount.supplier_id),
    (CommissionAgreement, CommissionAgreement.supplier_id),
    (ProductCommissionOverride, ProductCommissionOverride.supplier_id),
]


def _build_user_delete_blocker(
    user: User,
    acting_user: dict[str, Any],
    db: Session,
    *,
    delete_orders: bool,
    order_count: int | None = None,
) -> tuple[int, str] | None:
    user_id = cast(int, getattr(user, "id"))
    user_email = cast(str, getattr(user, "email", ""))
    user_role = cast(str, getattr(user, "role", ""))

    if user_id == acting_user["id"]:
        return 400, "Cannot delete your own account"

    if user_email in _PROTECTED_EMAILS:
        return 400, "Cannot delete a protected admin account"

    if user_role == "admin":
        return 400, "Cannot delete other admin accounts"

    if order_count is None:
        order_count = db.query(func.count(Order.id)).filter(Order.user_id == user_id).scalar() or 0
    if order_count > 0 and not delete_orders:
        return 409, f"User has {order_count} order(s). Deactivate the account instead of deleting."

    for model, column, label in _DELETE_BLOCKING_SUPPLIER_MODELS:
        related_count = db.query(func.count()).select_from(model).filter(column == user_id).scalar() or 0
        if related_count > 0:
            return 409, f"User has {related_count} {label}. Deactivate the account instead of deleting."

    return None


def _delete_user_ticket_records(user_id: int, db: Session) -> None:
    ticket_ids = [
        ticket_id for (ticket_id,) in db.query(SupportTicket.id).filter(SupportTicket.user_id == user_id).all()
    ]
    reply_ids = [
        reply_id for (reply_id,) in db.query(TicketReply.id).filter(TicketReply.sender_id == user_id).all()
    ]
    if ticket_ids:
        reply_ids.extend(
            reply_id
            for (reply_id,) in db.query(TicketReply.id).filter(TicketReply.ticket_id.in_(ticket_ids)).all()
        )

    unique_reply_ids = sorted(set(reply_ids))
    if ticket_ids:
        db.query(TicketAttachment).filter(TicketAttachment.ticket_id.in_(ticket_ids)).delete(
            synchronize_session=False
        )
    if unique_reply_ids:
        db.query(TicketAttachment).filter(TicketAttachment.ticket_reply_id.in_(unique_reply_ids)).delete(
            synchronize_session=False
        )

    if unique_reply_ids:
        db.query(TicketReply).filter(TicketReply.id.in_(unique_reply_ids)).delete(
            synchronize_session=False
        )
    if ticket_ids:
        db.query(SupportTicket).filter(SupportTicket.id.in_(ticket_ids)).delete(
            synchronize_session=False
        )


def _cleanup_user_references(user_id: int, db: Session) -> None:
    for model, column, field_name in _NULLABLE_USER_REFERENCE_UPDATES:
        db.query(model).filter(column == user_id).update({field_name: None}, synchronize_session=False)

    _delete_user_ticket_records(user_id, db)

    for model, column in _DELETABLE_USER_OWNED_MODELS:
        db.query(model).filter(column == user_id).delete(synchronize_session=False)

    db.query(Product).filter(Product.supplier_id == user_id).update(
        {"supplier_id": None, "is_deleted": True, "is_active": False},
        synchronize_session=False,
    )


def _hard_delete_user_record(user: User, db: Session) -> None:
    user_id = cast(int, getattr(user, "id"))
    _cleanup_user_references(user_id, db)
    db.delete(user)
    db.flush()


def _delete_order_records(order: Order, db: Session) -> dict:
    order_id = cast(int, getattr(order, "id"))
    order_status = cast(str, getattr(order, "status", "pending"))
    user_id = cast(int, getattr(order, "user_id"))

    if order_status not in {"cancelled", "refunded", "failed"}:
        apply_order_status_change(order, "cancelled", db)

    shipment_ids = [
        shipment_id for (shipment_id,) in db.query(Shipment.id).filter(Shipment.order_id == order_id).all()
    ]
    invoice_ids = [
        invoice_id for (invoice_id,) in db.query(Invoice.id).filter(Invoice.order_id == order_id).all()
    ]
    return_request_ids = [
        return_request_id
        for (return_request_id,) in db.query(ReturnRequest.id).filter(ReturnRequest.order_id == order_id).all()
    ]
    bank_transaction_ids = set()
    if return_request_ids:
        bank_transaction_ids.update(
            bank_transaction_id
            for (bank_transaction_id,) in db.query(BankTransaction.id)
            .filter(BankTransaction.linked_refund_id.in_(return_request_ids))
            .all()
            if bank_transaction_id is not None
        )

    db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.link == f"/orders/{order_id}",
    ).delete(synchronize_session=False)
    if shipment_ids:
        db.query(ShipmentConfirmation).filter(ShipmentConfirmation.shipment_id.in_(shipment_ids)).delete(
            synchronize_session=False
        )
        db.query(ShipmentEvent).filter(ShipmentEvent.shipment_id.in_(shipment_ids)).delete(
            synchronize_session=False
        )
    db.query(ShipmentConfirmation).filter(ShipmentConfirmation.order_id == order_id).delete(
        synchronize_session=False
    )
    db.query(ShipmentEvent).filter(ShipmentEvent.order_id == order_id).delete(
        synchronize_session=False
    )
    db.query(SupplierSettlement).filter(SupplierSettlement.order_id == order_id).delete(
        synchronize_session=False
    )
    db.query(LogisticsSettlement).filter(LogisticsSettlement.order_id == order_id).delete(
        synchronize_session=False
    )
    db.query(RefundLedger).filter(RefundLedger.order_id == order_id).delete(
        synchronize_session=False
    )
    db.query(CommissionLedgerEntry).filter(CommissionLedgerEntry.order_id == order_id).delete(
        synchronize_session=False
    )
    db.query(TransactionLedger).filter(TransactionLedger.order_id == order_id).delete(
        synchronize_session=False
    )
    db.query(OrderLogisticsAllocation).filter(OrderLogisticsAllocation.order_id == order_id).delete(
        synchronize_session=False
    )
    if bank_transaction_ids:
        db.query(BankTransaction).filter(BankTransaction.id.in_(bank_transaction_ids)).delete(
            synchronize_session=False
        )
    db.query(ReturnRequest).filter(ReturnRequest.order_id == order_id).delete(
        synchronize_session=False
    )
    if invoice_ids:
        db.query(InvoiceItem).filter(InvoiceItem.invoice_id.in_(invoice_ids)).delete(
            synchronize_session=False
        )
    db.query(Invoice).filter(Invoice.order_id == order_id).delete(synchronize_session=False)
    db.query(Shipment).filter(Shipment.order_id == order_id).delete(synchronize_session=False)
    db.query(OrderItem).filter(OrderItem.order_id == order_id).delete(synchronize_session=False)
    db.delete(order)
    db.flush()

    return {"id": order_id, "status": order_status}


def delete_user_admin(user_id: int, acting_user: dict, db: Session, delete_orders: bool = False) -> dict:
    """Hard-delete a user and their non-order data. Blocked if user has orders."""
    if acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete users")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_orders = db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
    blocker = _build_user_delete_blocker(
        user,
        acting_user,
        db,
        delete_orders=delete_orders,
        order_count=len(user_orders),
    )
    if blocker is not None:
        raise HTTPException(status_code=blocker[0], detail=blocker[1])

    deleted_orders: list[dict] = []
    if delete_orders:
        for order in user_orders:
            deleted_orders.append(_delete_order_records(order, db))

    username = cast(str, getattr(user, "username"))
    email = cast(str, getattr(user, "email"))

    try:
        _hard_delete_user_record(user, db)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.warning("admin delete blocked by remaining related records", extra={"user_id": user_id, "error": str(e)})
        raise HTTPException(
            status_code=409,
            detail="User has related records that must be archived or removed before deletion.",
        )
    except Exception as e:
        db.rollback()
        logger.exception("admin delete user failed", extra={"user_id": user_id, "error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")

    audit_log(
        db=db,
        action=AuditAction.USER_DELETE,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="user",
        resource_id=user_id,
        details={
            "deleted_username": username,
            "deleted_email": email,
            "deleted_order_count": len(deleted_orders),
            "deleted_orders": deleted_orders,
        },
        status="success",
    )
    return {"message": f"User '{username}' deleted successfully"}


def bulk_delete_users_admin(user_ids: List[int], acting_user: dict, db: Session) -> dict:
    """Bulk hard-delete multiple users. Admin-only. Skips protected/order-holding accounts."""
    if acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete users")

    if not user_ids:
        raise HTTPException(status_code=400, detail="No user IDs provided")
    if len(user_ids) > 100:
        raise HTTPException(status_code=400, detail="Cannot delete more than 100 users at once")

    deleted: List[dict] = []
    skipped: List[dict] = []

    for uid in user_ids:
        if uid == acting_user["id"]:
            skipped.append({"id": uid, "reason": "Cannot delete own account"})
            continue

        user = db.query(User).filter(User.id == uid).first()
        if not user:
            skipped.append({"id": uid, "reason": "Not found"})
            continue

        blocker = _build_user_delete_blocker(user, acting_user, db, delete_orders=False)
        if blocker is not None:
            skipped.append({"id": uid, "reason": blocker[1]})
            continue

        username = cast(str, getattr(user, "username"))
        try:
            with db.begin_nested():
                _hard_delete_user_record(user, db)
            deleted.append({"id": uid, "username": username})
        except IntegrityError:
            db.rollback()
            skipped.append(
                {
                    "id": uid,
                    "reason": "Has related records that must be archived or removed before deletion",
                }
            )

    if deleted:
        db.commit()
        audit_log(
            db=db,
            action=AuditAction.USER_DELETE,
            user_id=acting_user["id"],
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type="user",
            resource_id=0,
            details={"bulk": True, "deleted_count": len(deleted), "deleted_users": deleted},
            status="success",
        )
    else:
        db.rollback()

    return {
        "deleted": len(deleted),
        "skipped": len(skipped),
        "details": deleted,
        "skipped_details": skipped,
    }


def force_reset_password_admin(user_id: int, new_password: str, acting_user: dict, db: Session) -> dict:
    """Force-set any user's password without requiring the old one (admin only)."""
    if acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can force-reset passwords")

    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent resetting another admin's password
    if cast(str, getattr(user, "role")) == "admin" and user_id != acting_user["id"]:
        raise HTTPException(status_code=403, detail="Cannot reset another admin's password")

    setattr(user, "hashed_password", get_password_hash(new_password))
    db.commit()

    audit_log(
        db=db,
        action=AuditAction.PASSWORD_FORCE_RESET,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="user",
        resource_id=user_id,
        details={"target_username": cast(str, getattr(user, "username"))},
        status="success",
    )
    return {"message": f"Password reset for user '{cast(str, getattr(user, 'username'))}'"}


# â”€â”€ Bulk Order Operations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def bulk_update_order_status_admin(
    order_ids: List[int], status: str, acting_user: dict, db: Session
) -> dict:
    """Bulk update status of multiple orders (admin / sub_admin). Skips invalid transitions."""
    require_permission("orders.manage", acting_user)
    if not order_ids:
        raise HTTPException(status_code=400, detail="No order IDs provided")
    if len(order_ids) > 200:
        raise HTTPException(status_code=400, detail="Cannot update more than 200 orders at once")

    valid_statuses = (
        "pending", "confirmed", "processing", "prepared", "picking_up",
        "shipped", "delivered", "cancelled", "failed",
    )
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    if status == "refunded":
        raise HTTPException(status_code=409, detail="Use the refund action instead of the status endpoint")

    updated: List[dict] = []
    skipped: List[dict] = []

    for oid in order_ids:
        order = db.query(Order).filter(Order.id == oid).first()
        if not order:
            skipped.append({"id": oid, "reason": "Not found"})
            continue
        old_status = cast(str, getattr(order, "status"))
        if old_status == status:
            skipped.append({"id": oid, "reason": "Status unchanged"})
            continue
        if not _can_staff_override_order_status(old_status, status):
            skipped.append({"id": oid, "reason": f"Cannot transition from '{old_status}' to '{status}'"})
            continue
        apply_order_status_change(order, status, db)
        updated.append({"id": oid, "old_status": old_status, "new_status": status})

    if updated:
        db.commit()
        audit_log(
            db=db,
            action=AuditAction.ORDER_STATUS_CHANGED,
            user_id=acting_user["id"],
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type="order",
            resource_id=0,
            details={"bulk": True, "updated_count": len(updated), "new_status": status, "orders": updated},
            status="success",
        )
    return {
        "updated": len(updated),
        "skipped": len(skipped),
        "details": updated,
        "skipped_details": skipped,
    }


def bulk_delete_orders_admin(order_ids: List[int], acting_user: dict, db: Session) -> dict:
    """Bulk delete multiple orders (admin only)."""
    if acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete orders")
    if not order_ids:
        raise HTTPException(status_code=400, detail="No order IDs provided")
    if len(order_ids) > 100:
        raise HTTPException(status_code=400, detail="Cannot delete more than 100 orders at once")

    deleted: List[dict] = []
    skipped: List[dict] = []

    for oid in order_ids:
        order = db.query(Order).filter(Order.id == oid).first()
        if not order:
            skipped.append({"id": oid, "reason": "Not found"})
            continue
        try:
            with db.begin_nested():
                info = _delete_order_records(order, db)
            deleted.append(info)
        except IntegrityError:
            logger.warning("admin bulk order delete blocked by remaining related records", extra={"order_id": oid})
            skipped.append(
                {
                    "id": oid,
                    "reason": "Order has related records that must be archived or removed before deletion.",
                }
            )

    if deleted:
        db.commit()
        audit_log(
            db=db,
            action=AuditAction.ORDER_DELETE,
            user_id=acting_user["id"],
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type="order",
            resource_id=0,
            details={"bulk": True, "deleted_count": len(deleted), "orders": deleted},
            status="success",
        )
    else:
        db.rollback()
    return {
        "deleted": len(deleted),
        "skipped": len(skipped),
        "details": deleted,
        "skipped_details": skipped,
    }


# â”€â”€ Bulk Product Operations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def bulk_delete_products_admin(product_ids: List[int], acting_user: dict, db: Session) -> dict:
    """Bulk soft-delete multiple products (admin / moderator)."""
    require_permission("products.manage", acting_user)
    if not product_ids:
        raise HTTPException(status_code=400, detail="No product IDs provided")
    if len(product_ids) > 200:
        raise HTTPException(status_code=400, detail="Cannot delete more than 200 products at once")

    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    found_ids = {cast(int, p.id) for p in products}
    deleted: List[dict] = []
    skipped: List[dict] = []

    for product in products:
        if bool(cast(Any, getattr(product, "is_deleted"))):
            skipped.append({"id": product.id, "reason": "Already deleted"})
            continue
        setattr(product, "is_deleted", True)
        deleted.append({"id": product.id, "name": product.name})

    for pid in product_ids:
        if pid not in found_ids:
            skipped.append({"id": pid, "reason": "Not found"})

    if deleted:
        db.commit()
        audit_log(
            db=db,
            action=AuditAction.PRODUCT_DELETE,
            user_id=acting_user["id"],
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type="product",
            resource_id=0,
            details={"bulk": True, "deleted_count": len(deleted), "products": deleted},
            status="success",
        )
    return {
        "deleted": len(deleted),
        "skipped": len(skipped),
        "details": deleted,
        "skipped_details": skipped,
    }


def bulk_product_moderation(
    product_ids: List[int], action: str, note: Optional[str], acting_user: dict, db: Session
) -> dict:
    """Bulk approve or reject multiple products in one call (admin / moderator)."""
    require_permission("moderation.products", acting_user)
    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action must be 'approve' or 'reject'")
    if not product_ids:
        raise HTTPException(status_code=400, detail="No product IDs provided")
    if len(product_ids) > 200:
        raise HTTPException(status_code=400, detail="Cannot moderate more than 200 products at once")

    products = db.query(Product).filter(
        Product.id.in_(product_ids),
        Product.is_deleted.is_(False),
    ).all()
    found_ids = {cast(int, p.id) for p in products}
    processed: List[dict] = []
    skipped: List[dict] = []

    for product in products:
        if action == "approve":
            setattr(product, "is_approved", True)
            setattr(product, "is_active", True)
            db.add(
                Notification(
                    user_id=product.supplier_id,
                    type="product",
                    title="Product Approved",
                    message=f'Your product "{product.name}" has been approved and is now live.',
                    link=f"/products/{product.id}",
                )
            )
        else:
            setattr(product, "is_approved", False)
            setattr(product, "is_active", False)
            db.add(
                Notification(
                    user_id=product.supplier_id,
                    type="product",
                    title="Product Rejected",
                    message=f'Your product "{product.name}" was not approved. Reason: {note or "Does not meet listing standards."}',
                    link="/supplier/products",
                )
            )
        processed.append({"id": product.id, "name": product.name})

    for pid in product_ids:
        if pid not in found_ids:
            skipped.append({"id": pid, "reason": "Not found or deleted"})

    if processed:
        db.commit()
        audit_log(
            db=db,
            action="PRODUCT_APPROVED" if action == "approve" else "PRODUCT_REJECTED",
            user_id=acting_user["id"],
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type="product",
            resource_id=0,
            details={"bulk": True, "action": action, "count": len(processed), "note": note, "products": processed},
            status="success",
        )
    return {
        "action": action,
        "processed": len(processed),
        "skipped": len(skipped),
        "details": processed,
        "skipped_details": skipped,
    }


# â”€â”€ Bulk Supplier Verification â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def bulk_supplier_verification(
    supplier_ids: List[int], action: str, note: Optional[str], acting_user: dict, db: Session
) -> dict:
    """Bulk verify or reject multiple suppliers in one call (admin / sub_admin)."""
    require_permission("moderation.suppliers", acting_user)
    if action not in ("verify", "reject"):
        raise HTTPException(status_code=400, detail="action must be 'verify' or 'reject'")
    if not supplier_ids:
        raise HTTPException(status_code=400, detail="No supplier IDs provided")
    if len(supplier_ids) > 100:
        raise HTTPException(status_code=400, detail="Cannot process more than 100 suppliers at once")

    from models import SupplierProfile as SP

    processed: List[dict] = []
    skipped: List[dict] = []

    for sid in supplier_ids:
        user = db.query(User).filter(User.id == sid, User.role == "supplier").first()
        if not user:
            skipped.append({"id": sid, "reason": "Supplier not found"})
            continue

        profile = db.query(SP).filter(SP.user_id == sid).first()
        if profile is None:
            profile = SP(user_id=sid)
            db.add(profile)
            db.flush()

        if action == "verify":
            if bool(cast(Any, getattr(user, "is_verified"))) and cast(str | None, getattr(profile, "verification_status")) == "approved":
                skipped.append({"id": sid, "reason": "Already verified"})
                continue
            setattr(user, "is_verified", True)
            setattr(user, "verification_note", note or "Approved")
            setattr(profile, "verification_status", "approved")
            setattr(profile, "verified_at", datetime.now(timezone.utc).replace(tzinfo=None))
            db.add(
                Notification(
                    user_id=user.id,
                    type="account",
                    title="Account Verified",
                    message="Congratulations! Your supplier account has been verified. You can now list products.",
                    link="/supplier/dashboard",
                )
            )
        else:
            setattr(user, "is_verified", False)
            setattr(user, "verification_note", note or "Rejected")
            setattr(profile, "verification_status", "rejected")
            setattr(profile, "verified_at", None)
            db.add(
                Notification(
                    user_id=user.id,
                    type="account",
                    title="Verification Declined",
                    message=f"Your supplier account verification was declined. Reason: {note or 'Please contact support.'}",
                    link="/supplier/dashboard",
                )
            )
        processed.append({"id": sid, "username": user.username})

    if processed:
        db.commit()
        audit_log(
            db=db,
            action=AuditAction.SUPPLIER_VERIFIED if action == "verify" else AuditAction.SUPPLIER_REJECTED,
            user_id=acting_user["id"],
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type="user",
            resource_id=0,
            details={"bulk": True, "action": action, "count": len(processed), "note": note, "suppliers": processed},
            status="success",
        )
    return {
        "action": action,
        "processed": len(processed),
        "skipped": len(skipped),
        "details": processed,
        "skipped_details": skipped,
    }


def bulk_manage_suppliers(
    supplier_ids: List[int], action: str, note: Optional[str], acting_user: dict, db: Session, badge_level: Optional[str] = None
) -> dict:
    """Bulk supplier lifecycle actions: verify, reject, activate/reactivate, suspend, archive, badge."""
    require_permission("moderation.suppliers", acting_user)
    if not supplier_ids:
        raise HTTPException(status_code=400, detail="No supplier IDs provided")

    normalized_action = str(action or "").strip().lower()
    if normalized_action == "reactivate":
        normalized_action = "activate"
    if normalized_action not in {"verify", "reject", "activate", "suspend", "delete", "badge"}:
        raise HTTPException(
            status_code=400,
            detail="action must be one of: verify, reject, activate, reactivate, suspend, delete, badge",
        )
    if normalized_action in {"delete", "badge"} and acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail=f"Only admins can bulk-{normalized_action} suppliers")

    normalized_badge = str(badge_level or "").strip().lower() or None
    valid_badges = {"none", "bronze", "silver", "gold", "membership", "verified"}
    if normalized_action == "badge" and normalized_badge not in valid_badges:
        raise HTTPException(status_code=422, detail=f"badge_level must be one of: {', '.join(sorted(valid_badges))}")

    processed: List[dict] = []
    skipped: List[dict] = []
    note_text = note.strip() if isinstance(note, str) and note.strip() else None

    for supplier_id in list(dict.fromkeys(supplier_ids)):
        user = db.query(User).filter(User.id == supplier_id, User.role == "supplier").first()
        if not user:
            skipped.append({"id": supplier_id, "reason": "Supplier not found"})
            continue

        profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == supplier_id).first()
        if profile is None:
            profile = SupplierProfile(user_id=supplier_id)
            db.add(profile)
            db.flush()

        if normalized_action == "verify":
            setattr(user, "is_verified", True)
            setattr(user, "is_active", True)
            setattr(user, "verification_note", note_text or "Approved")
            setattr(profile, "verification_status", "approved")
            setattr(profile, "verified_at", datetime.now(timezone.utc).replace(tzinfo=None))
        elif normalized_action == "reject":
            setattr(user, "is_verified", False)
            setattr(user, "verification_note", note_text or "Rejected")
            setattr(profile, "verification_status", "rejected")
            setattr(profile, "verified_at", None)
        elif normalized_action == "activate":
            setattr(user, "is_active", True)
            if cast(str | None, getattr(profile, "verification_status", None)) == "archived":
                setattr(profile, "verification_status", "approved" if bool(cast(Any, getattr(user, "is_verified", False))) else "pending")
            if note_text:
                setattr(user, "verification_note", note_text)
        elif normalized_action == "suspend":
            setattr(user, "is_active", False)
            setattr(user, "verification_note", note_text or "Suspended by admin")
        elif normalized_action == "delete":
            setattr(user, "is_active", False)
            setattr(user, "verification_note", note_text or "Archived by admin")
            setattr(profile, "verification_status", "archived")
        elif normalized_action == "badge":
            setattr(profile, "badge_level", normalized_badge)
            setattr(profile, "badge_granted_at", datetime.now(timezone.utc).replace(tzinfo=None))

        processed.append(
            {
                "id": supplier_id,
                "username": user.username,
                "is_active": bool(cast(Any, getattr(user, "is_active", False))),
                "is_verified": bool(cast(Any, getattr(user, "is_verified", False))),
                "verification_status": cast(str | None, getattr(profile, "verification_status", None)),
                "badge_level": cast(str | None, getattr(profile, "badge_level", None)),
                "archived": normalized_action == "delete",
            }
        )

    if processed:
        db.commit()
        audit_action = (
            AuditAction.SUPPLIER_VERIFIED
            if normalized_action == "verify"
            else AuditAction.SUPPLIER_REJECTED
            if normalized_action == "reject"
            else "SUPPLIER_BADGE_ASSIGNED"
            if normalized_action == "badge"
            else f"SUPPLIER_{normalized_action.upper()}"
        )
        for supplier_entry in processed:
            audit_log(
                db=db,
                action=audit_action,
                user_id=acting_user["id"],
                username=acting_user.get("username"),
                user_role=acting_user.get("role"),
                resource_type="user",
                resource_id=supplier_entry["id"],
                details={
                    "bulk": True,
                    "action": normalized_action,
                    "note": note_text,
                    "badge_level": normalized_badge,
                    "supplier": supplier_entry,
                },
                status="success",
            )

    return {
        "action": normalized_action,
        "processed": len(processed),
        "skipped": len(skipped),
        "details": processed,
        "skipped_details": skipped,
    }


def bulk_update_users_role(
    user_ids: List[int], role: str, acting_user: dict, db: Session
) -> dict:
    """Bulk assign the same role to multiple users (admin-only for staff roles)."""
    require_permission("users.role.update", acting_user)

    normalized_role = str(role or "").strip()
    if normalized_role not in VALID_USER_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(sorted(VALID_USER_ROLES))}",
        )

    if normalized_role in STAFF_ROLES and acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can assign staff roles")

    if not user_ids:
        raise HTTPException(status_code=400, detail="No user IDs provided")
    if len(user_ids) > 200:
        raise HTTPException(status_code=400, detail="Cannot update more than 200 users at once")

    updated: List[dict] = []
    skipped: List[dict] = []

    for uid in list(dict.fromkeys(user_ids)):
        if uid == acting_user["id"]:
            skipped.append({"id": uid, "reason": "Cannot change own account role in bulk"})
            continue

        user = db.query(User).filter(User.id == uid).first()
        if not user:
            skipped.append({"id": uid, "reason": "Not found"})
            continue

        old_role = cast(str, getattr(user, "role"))
        if old_role == normalized_role:
            skipped.append({"id": uid, "reason": "Role unchanged"})
            continue

        if old_role == "admin" and acting_user.get("role") != "admin":
            skipped.append({"id": uid, "reason": "Only admins can change admin roles"})
            continue

        setattr(user, "role", normalized_role)
        updated.append(
            {
                "id": uid,
                "username": getattr(user, "username", f"user-{uid}"),
                "old_role": old_role,
                "new_role": normalized_role,
            }
        )

    if updated:
        db.commit()
        audit_log(
            db=db,
            action=AuditAction.ROLE_CHANGED,
            user_id=acting_user["id"],
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type="user",
            resource_id=0,
            details={"bulk": True, "new_role": normalized_role, "count": len(updated), "users": updated},
            status="success",
        )

    return {
        "role": normalized_role,
        "updated": len(updated),
        "skipped": len(skipped),
        "details": updated,
        "skipped_details": skipped,
    }


# â”€â”€ Bulk User Toggle Active â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def bulk_toggle_users_active(
    user_ids: List[int], is_active: bool, acting_user: dict, db: Session
) -> dict:
    """Bulk enable or disable multiple user accounts (admin / sub_admin)."""
    require_permission("users.toggle_active", acting_user)
    if not user_ids:
        raise HTTPException(status_code=400, detail="No user IDs provided")
    if len(user_ids) > 200:
        raise HTTPException(status_code=400, detail="Cannot update more than 200 users at once")

    updated: List[dict] = []
    skipped: List[dict] = []

    for uid in user_ids:
        if uid == acting_user["id"]:
            skipped.append({"id": uid, "reason": "Cannot change own account status"})
            continue
        user = db.query(User).filter(User.id == uid).first()
        if not user:
            skipped.append({"id": uid, "reason": "Not found"})
            continue
        if cast(str, getattr(user, "email", "")) in _PROTECTED_EMAILS:
            skipped.append({"id": uid, "reason": "Protected account"})
            continue
        current_active = bool(cast(Any, getattr(user, "is_active")))
        if current_active == is_active:
            skipped.append({"id": uid, "reason": "Status unchanged"})
            continue
        setattr(user, "is_active", int(is_active))
        updated.append({"id": uid, "username": user.username, "is_active": is_active})

    if updated:
        db.commit()
        audit_log(
            db=db,
            action="USER_BULK_TOGGLE_ACTIVE",
            user_id=acting_user["id"],
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type="user",
            resource_id=0,
            details={"bulk": True, "is_active": is_active, "count": len(updated), "users": updated},
            status="success",
        )
    return {
        "is_active": is_active,
        "updated": len(updated),
        "skipped": len(skipped),
        "details": updated,
        "skipped_details": skipped,
    }


def delete_order_admin(order_id: int, acting_user: dict, db: Session) -> dict:
    if acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete orders")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        deleted_order = _delete_order_records(order, db)
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.warning("admin order delete blocked by remaining related records", extra={"order_id": order_id})
        raise HTTPException(
            status_code=409,
            detail="Order has related records that must be archived or removed before deletion.",
        )

    audit_log(
        db=db,
        action=AuditAction.ORDER_DELETE,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="order",
        resource_id=order_id,
        details=deleted_order,
        status="success",
    )
    return {"message": f"Order #{order_id} deleted successfully"}


def create_staff_account(payload: CreateStaffAccount, acting_user: dict, db: Session) -> dict:
    if acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create staff accounts")

    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    assigned_permissions = sanitize_staff_permissions(payload.permissions)
    if not assigned_permissions:
        assigned_permissions = default_permissions_for_role(payload.role)

    new_user = User(
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
        country_code=acting_user.get("country_code") or "OM",
        is_active=1,
        phone=payload.phone,
        email_verified=True,
        staff_role_label=payload.staff_role_label,
        staff_title=payload.staff_title,
        staff_department=payload.staff_department,
        staff_area_of_operation=payload.staff_area_of_operation,
        staff_hire_date=payload.staff_hire_date,
        staff_experience_level=payload.staff_experience_level,
        staff_performance_summary=payload.staff_performance_summary,
        staff_assigned_tasks=payload.staff_assigned_tasks,
        staff_assigned_projects=payload.staff_assigned_projects,
        staff_permissions=assigned_permissions,
        staff_notes=payload.staff_notes,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    audit_log(
        db=db,
        action=AuditAction.STAFF_CREATED,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="user",
        resource_id=cast(int, getattr(new_user, "id")),
        details={
            "created_username": new_user.username,
            "role": new_user.role,
            "staff_role_label": new_user.staff_role_label,
            "staff_title": new_user.staff_title,
            "staff_area_of_operation": new_user.staff_area_of_operation,
            "staff_hire_date": getattr(new_user, "staff_hire_date", None),
            "permissions": assigned_permissions,
        },
        status="success",
    )
    return _serialize_staff_user(new_user)


def update_staff_account(user_id: int, payload: UpdateStaffAccount, acting_user: dict, db: Session) -> dict[str, Any]:
    if acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update staff accounts")

    user = db.query(User).filter(User.id == user_id, User.role.in_(tuple(STAFF_ROLES))).first()
    if not user:
        raise HTTPException(status_code=404, detail="Staff user not found")

    updates = payload.model_dump(exclude_unset=True)
    next_role = cast(str, updates.get("role", getattr(user, "role")))
    explicit_permissions = updates.get("permissions")

    if user_id == acting_user["id"]:
        if "role" in updates or "permissions" in updates or updates.get("is_active") is False:
            raise HTTPException(status_code=400, detail="Cannot change your own role, permissions, or active status")

    next_email = cast(str | None, updates.get("email"))
    if next_email and next_email != getattr(user, "email"):
        existing = db.query(User).filter(User.email == next_email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

    if "full_name" in updates:
        setattr(user, "full_name", updates["full_name"])
    if "email" in updates:
        setattr(user, "email", updates["email"])
    if "phone" in updates:
        setattr(user, "phone", updates["phone"])
    if "role" in updates:
        setattr(user, "role", next_role)
    if "staff_role_label" in updates:
        setattr(user, "staff_role_label", updates["staff_role_label"])
    if "staff_title" in updates:
        setattr(user, "staff_title", updates["staff_title"])
    if "staff_department" in updates:
        setattr(user, "staff_department", updates["staff_department"])
    if "staff_area_of_operation" in updates:
        setattr(user, "staff_area_of_operation", updates["staff_area_of_operation"])
    if "staff_hire_date" in updates:
        setattr(user, "staff_hire_date", updates["staff_hire_date"])
    if "staff_experience_level" in updates:
        setattr(user, "staff_experience_level", updates["staff_experience_level"])
    if "staff_performance_summary" in updates:
        setattr(user, "staff_performance_summary", updates["staff_performance_summary"])
    if "staff_assigned_tasks" in updates:
        setattr(user, "staff_assigned_tasks", updates["staff_assigned_tasks"])
    if "staff_assigned_projects" in updates:
        setattr(user, "staff_assigned_projects", updates["staff_assigned_projects"])
    if "staff_notes" in updates:
        setattr(user, "staff_notes", updates["staff_notes"])
    if "is_active" in updates:
        setattr(user, "is_active", int(bool(updates["is_active"])))

    if explicit_permissions is not None:
        sanitized_permissions = sanitize_staff_permissions(cast(list[str], explicit_permissions))
        if not sanitized_permissions:
            raise HTTPException(status_code=400, detail="Assign at least one valid permission")
        setattr(user, "staff_permissions", sanitized_permissions)
    elif "role" in updates:
        setattr(user, "staff_permissions", default_permissions_for_role(next_role))

    db.commit()
    db.refresh(user)

    audit_log(
        db=db,
        action="STAFF_UPDATED",
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="user",
        resource_id=user_id,
        details={
            "updated_fields": sorted(updates.keys()),
            "role": getattr(user, "role"),
            "permissions": _effective_staff_permissions(user),
        },
        status="success",
    )
    return _serialize_staff_user(user)


def delete_staff_account(user_id: int, acting_user: dict, db: Session) -> dict[str, Any]:
    staff_user = db.query(User).filter(User.id == user_id, User.role.in_(tuple(STAFF_ROLES))).first()
    if not staff_user:
        raise HTTPException(status_code=404, detail="Staff user not found")

    username = cast(str, getattr(staff_user, "username", ""))
    role = cast(str, getattr(staff_user, "role", ""))
    result = delete_user_admin(user_id, acting_user, db)
    audit_log(
        db=db,
        action="STAFF_DELETED",
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="user",
        resource_id=user_id,
        details={"deleted_username": username, "deleted_role": role},
        status="success",
    )
    return result


def bulk_update_staff_accounts(user_ids: List[int], updates: UpdateStaffAccount, acting_user: dict, db: Session) -> dict[str, Any]:
    if acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can bulk update staff accounts")

    if not user_ids:
        raise HTTPException(status_code=400, detail="No user IDs provided")

    # Fetch all staff users at once
    staff_users = (
        db.query(User)
        .filter(User.id.in_(user_ids), User.role.in_(tuple(STAFF_ROLES)))
        .all()
    )

    found_ids = {cast(int, getattr(u, "id")) for u in staff_users}
    missing_ids = set(user_ids) - found_ids
    if missing_ids:
        raise HTTPException(status_code=404, detail=f"Staff users not found: {sorted(missing_ids)}")

    # Prevent self-update of sensitive fields
    acting_user_id = acting_user["id"]
    if acting_user_id in user_ids:
        sensitive_fields = {"role", "permissions", "is_active"}
        update_fields = updates.model_dump(exclude_unset=True).keys()
        if any(field in sensitive_fields for field in update_fields):
            raise HTTPException(status_code=400, detail="Cannot bulk update your own role, permissions, or active status")

    update_data = updates.model_dump(exclude_unset=True)
    next_role = cast(str | None, update_data.get("role"))
    explicit_permissions = update_data.get("permissions")

    # Validate role if provided
    if next_role and next_role not in STAFF_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(sorted(STAFF_ROLES))}")

    # Validate email uniqueness if provided
    next_email = cast(str | None, update_data.get("email"))
    if next_email:
        existing = db.query(User).filter(User.email == next_email, User.id.not_in_(user_ids)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

    updated_users = []
    for user in staff_users:
        user_id = cast(int, getattr(user, "id"))

        # Apply updates
        if "full_name" in update_data:
            setattr(user, "full_name", update_data["full_name"])
        if "email" in update_data:
            setattr(user, "email", update_data["email"])
        if "phone" in update_data:
            setattr(user, "phone", update_data["phone"])
        if "role" in update_data:
            setattr(user, "role", next_role)
        if "staff_role_label" in update_data:
            setattr(user, "staff_role_label", update_data["staff_role_label"])
        if "staff_title" in update_data:
            setattr(user, "staff_title", update_data["staff_title"])
        if "staff_department" in update_data:
            setattr(user, "staff_department", update_data["staff_department"])
        if "staff_area_of_operation" in update_data:
            setattr(user, "staff_area_of_operation", update_data["staff_area_of_operation"])
        if "staff_experience_level" in update_data:
            setattr(user, "staff_experience_level", update_data["staff_experience_level"])
        if "staff_performance_summary" in update_data:
            setattr(user, "staff_performance_summary", update_data["staff_performance_summary"])
        if "staff_assigned_tasks" in update_data:
            setattr(user, "staff_assigned_tasks", update_data["staff_assigned_tasks"])
        if "staff_assigned_projects" in update_data:
            setattr(user, "staff_assigned_projects", update_data["staff_assigned_projects"])
        if "staff_notes" in update_data:
            setattr(user, "staff_notes", update_data["staff_notes"])
        if "is_active" in update_data:
            setattr(user, "is_active", int(bool(update_data["is_active"])))

        # Handle permissions
        if explicit_permissions is not None:
            sanitized_permissions = sanitize_staff_permissions(cast(list[str], explicit_permissions))
            if not sanitized_permissions:
                raise HTTPException(status_code=400, detail="Assign at least one valid permission")
            setattr(user, "staff_permissions", sanitized_permissions)
        elif next_role:
            setattr(user, "staff_permissions", default_permissions_for_role(next_role))

        updated_users.append(_serialize_staff_user(user))

    db.commit()

    audit_log(
        db=db,
        action="STAFF_BULK_UPDATED",
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="user",
        resource_id=None,  # Bulk operation
        details={
            "user_ids": user_ids,
            "updated_fields": sorted(update_data.keys()),
            "count": len(user_ids),
        },
        status="success",
    )

    return {
        "message": f"Successfully updated {len(user_ids)} staff account(s)",
        "updated_users": updated_users,
        "updated_fields": sorted(update_data.keys()),
    }


def get_all_orders(
    db: Session,
    limit: Optional[int] = None,
    offset: int = 0,
    search: Optional[str] = None,
    status: Optional[str] = None,
    date_range: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    missing_tracking_only: bool = False,
) -> dict[str, Any]:
    resolved_limit = _ADMIN_DEFAULT_PAGE_SIZE if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))
    query = db.query(Order).options(selectinload(Order.items).selectinload(OrderItem.product))
    if status and status != "all":
        query = query.filter(Order.status == status)
    if min_amount is not None:
        query = query.filter(Order.total_amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Order.total_amount <= max_amount)
    if date_range and date_range != "all":
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if date_range == "7d":
            query = query.filter(Order.created_at >= now - timedelta(days=7))
        elif date_range == "30d":
            query = query.filter(Order.created_at >= now - timedelta(days=30))
        elif date_range == "month":
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Order.created_at >= month_start)
    if missing_tracking_only:
        query = query.filter(
            Order.status.in_(["shipped", "delivered"]),
            ~exists().where(Shipment.order_id == Order.id),
        )
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.outerjoin(User, User.id == Order.user_id).filter(
            or_(
                func.cast(Order.id, String).ilike(term),
                func.cast(Order.user_id, String).ilike(term),
                User.username.ilike(term),
                User.email.ilike(term),
            )
        )
    query = query.order_by(Order.created_at.desc(), Order.id.desc())
    total = query.count()
    if offset:
        query = query.offset(offset)
    query = query.limit(resolved_limit)
    orders = query.all()
    if not orders:
        return _build_list_page_payload([], total, offset=offset, page_size=resolved_limit)

    order_ids = [cast(int, o.id) for o in orders]

    # Batch-load customer usernames (avoid N+1 queries)
    user_ids = list({cast(int, o.user_id) for o in orders if o.user_id is not None})
    username_map: dict[int, str] = {}
    if user_ids:
        user_rows = db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()
        username_map = {r.id: r.username for r in user_rows}

    # Batch-load shipments for all orders at once (avoid N+1)
    all_shipments = (
        db.query(Shipment)
        .filter(Shipment.order_id.in_(order_ids))
        .order_by(Shipment.order_id.asc(), Shipment.created_at.asc(), Shipment.id.asc())
        .all()
    )
    shipments_by_order: dict[int, list] = {}
    for s in all_shipments:
        shipments_by_order.setdefault(cast(int, s.order_id), []).append(s)

    # Batch-load events for all shipments at once
    all_shipment_ids = [cast(int, s.id) for s in all_shipments]
    events_by_shipment: dict[int, list] = {}
    if all_shipment_ids:
        all_events = (
            db.query(ShipmentEvent)
            .filter(ShipmentEvent.shipment_id.in_(all_shipment_ids))
            .order_by(ShipmentEvent.created_at.asc())
            .all()
        )
        for e in all_events:
            events_by_shipment.setdefault(cast(int, e.shipment_id), []).append(e)

    for order in orders:
        for item in cast(list[Any], getattr(order, "items", []) or []):
            product = getattr(item, "product", None)
            if not getattr(item, "product_name", None):
                fallback_product_name = getattr(product, "name", None) or f"Product #{getattr(item, 'product_id', 'unknown')}"
                setattr(item, "product_name", str(fallback_product_name))

            unit_price_raw = getattr(item, "unit_price", None)
            if unit_price_raw is None:
                unit_price_raw = getattr(item, "price", 0) or 0
                setattr(item, "unit_price", unit_price_raw)

            total_price_raw = getattr(item, "total_price", None)
            if total_price_raw is None:
                quantity_value = int(getattr(item, "quantity", 0) or 0)
                safe_unit_price = float(unit_price_raw or 0)
                setattr(item, "total_price", round(safe_unit_price * max(quantity_value, 0), 2))

        shipments = shipments_by_order.get(cast(int, order.id), [])
        events: list = []
        for s in shipments:
            events.extend(events_by_shipment.get(cast(int, s.id), []))
        reconciled_status = reconcile_order_status(order, shipments)
        if order.status != reconciled_status:
            order.status = reconciled_status
        setattr(order, "status_label", order_status_label(reconciled_status, shipments, events))
        setattr(order, "customer_username", username_map.get(cast(int, order.user_id)) if order.user_id is not None else None)
    return _build_list_page_payload([_order_to_dict(o, include_items=False) for o in orders], total, offset=offset, page_size=resolved_limit)


def _order_to_dict(order: Order, include_items: bool = False) -> dict[str, Any]:
    cols = [c.name for c in Order.__table__.columns]
    d = {}
    for col in cols:
        val = getattr(order, col, None)
        if isinstance(val, Decimal):
            val = float(val)
        d[col] = val
    for attr in ("status_label", "customer_username"):
        if hasattr(order, attr):
            d[attr] = getattr(order, attr)
    if include_items and hasattr(order, "items") and order.items:
        d["items"] = []
        for item in order.items:
            item_dict = {c.name: getattr(item, c.name, None) for c in item.__table__.columns}
            for k, v in item_dict.items():
                if isinstance(v, Decimal):
                    item_dict[k] = float(v)
            if hasattr(item, "product_name"):
                item_dict["product_name"] = getattr(item, "product_name")
            d["items"].append(item_dict)
    return d


def _can_staff_override_order_status(current_status: str, target_status: str) -> bool:
    if target_status == "refunded":
        return False
    if current_status in {"cancelled", "failed", "refunded"}:
        return False
    return True


def update_order_status(order_id: int, status: str, acting_user: dict, db: Session) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    valid_statuses = (
        "pending", "confirmed", "processing", "prepared", "picking_up", "shipped",
        "delivered", "cancelled", "failed", "refunded",
    )
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
    if status == "refunded":
        raise HTTPException(
            status_code=409,
            detail="Use the refund action for this order instead of the status endpoint",
        )

    old_status = order.status
    if status == old_status:
        return {"message": "Order status unchanged", "old_status": old_status, "new_status": status}

    allowed_transitions = {
        "pending": {"confirmed", "cancelled", "failed"},
        "confirmed": {"processing", "prepared", "shipped", "delivered", "cancelled"},
        "processing": {"prepared", "shipped", "delivered", "cancelled"},
        "prepared": {"picking_up", "shipped", "delivered", "cancelled"},
        "picking_up": {"prepared", "shipped", "delivered", "cancelled"},
        "shipped": {"delivered"},
        "delivered": set(),
        "cancelled": set(),
        "failed": set(),
        "refunded": set(),
    }
    order_status = cast(str, getattr(order, "status"))
    order_paid_at = cast(datetime | None, getattr(order, "paid_at"))
    if order_status == "confirmed" and order_paid_at is None:
        allowed_transitions["confirmed"].add("failed")

    is_admin_override = False
    if status not in allowed_transitions.get(order_status, set()):
        if acting_user.get("role") in STAFF_ROLES and _can_staff_override_order_status(order_status, status):
            is_admin_override = True
        else:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot change order status from '{order_status}' to '{status}'",
            )

    if is_admin_override and order_status == "delivered" and status == "cancelled":
        raise HTTPException(
            status_code=409,
            detail="Delivered orders cannot be cancelled through status override",
        )

    apply_order_status_change(order, status, db)
    db.commit()
    try:
        from services.transactional_email_service import enqueue_order_status_email

        enqueue_order_status_email(cast(int, order.id), status=status)
    except Exception:
        logger.exception("Failed to enqueue order-status email for order %s", order.id)

    audit_log(
        db=db,
        action=AuditAction.ORDER_STATUS_CHANGED,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="order",
        resource_id=order_id,
        details={"old_status": old_status, "new_status": status, "forced_override": is_admin_override},
        status="success",
    )
    return {
        "message": "Order status updated",
        "old_status": old_status,
        "new_status": status,
        "forced_override": is_admin_override,
    }


def refund_order(order_id: int, acting_user: dict, db: Session) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    payment_intent_id = cast(str | None, getattr(order, "payment_intent_id"))
    order_status = cast(str, getattr(order, "status"))
    order_paid_at = cast(datetime | None, getattr(order, "paid_at"))
    if not payment_intent_id:
        raise HTTPException(status_code=422, detail="Order has no associated payment â€” cannot refund")

    allowed_statuses = {"confirmed", "processing", "prepared", "picking_up", "delivered", "shipped", "cancelled"}
    if order_status == "failed" and order_paid_at is not None:
        allowed_statuses.add("failed")
    if order_status not in allowed_statuses:
        raise HTTPException(status_code=409, detail=f"Cannot refund order in '{order_status}' status")

    from controllers.payments_controller import _apply_stripe_runtime_key

    stripe.api_key = _apply_stripe_runtime_key(db) or os.getenv("STRIPE_SECRET_KEY", "")
    if not stripe.api_key:
        raise HTTPException(status_code=503, detail="Payment service not configured")

    try:
        refund = stripe.Refund.create(payment_intent=payment_intent_id)
        apply_order_status_change(order, "refunded", db)
        try:
            from services.cash_management_service import log_refund_bank_transaction

            log_refund_bank_transaction(
                order,
                db,
                source="stripe_refund",
                transaction_ref=refund.id,
                description=f"Admin-issued Stripe refund for order #{order.id}",
                refund_amount=cast(Any, getattr(order, "total_amount", 0)),
            )
        except Exception:
            logger.exception("Failed to log refund bank transaction for order %s", order.id)
        db.add(
            Notification(
                user_id=order.user_id,
                type="order_update",
                title="Refund Issued",
                message=f"A full refund for Order #{order.id} has been issued by admin.",
                link=f"/orders/{order.id}",
            )
        )
        db.commit()
        try:
            from services.transactional_email_service import enqueue_refund_processed_email

            enqueue_refund_processed_email(cast(int, order.id), source="admin")
        except Exception:
            logger.exception("Failed to enqueue admin refund email for order %s", order.id)
        audit_log(
            db=db,
            action=AuditAction.ORDER_REFUNDED,
            user_id=acting_user["id"],
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type="order",
            resource_id=order_id,
            details={"refund_id": refund.id, "amount": order.total_amount},
            status="success",
        )
        logger.info("Admin refund issued: order %s refund %s", order.id, refund.id)
        return {"detail": "Refund issued", "refund_id": refund.id, "status": refund.status}
    except Exception as exc:
        if exc.__class__.__module__.startswith("stripe"):
            raise HTTPException(status_code=400, detail=str(getattr(exc, "user_message", str(exc))))
        logger.error("Refund error: %s", exc)
        raise HTTPException(status_code=500, detail="Refund service error")


def update_order_tracking(order_id: int, tracking_number: str, acting_user: dict, db: Session) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order_status = cast(str, getattr(order, "status"))
    if order_status not in ("confirmed", "processing", "prepared", "picking_up", "shipped"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot add tracking to order in '{order_status}' status",
        )

    setattr(order, "tracking_number", tracking_number)
    setattr(order, "status", "shipped")
    db.add(
        Notification(
            user_id=order.user_id,
            type="order_update",
            title="Order Shipped",
            message=f"Order #{order.id} has been shipped. Tracking: {tracking_number}",
            link=f"/orders/{order.id}",
        )
    )
    db.commit()
    audit_log(
        db=db,
        action=AuditAction.ORDER_STATUS_CHANGED,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="order",
        resource_id=order_id,
        details={"new_status": "shipped", "tracking_number": tracking_number},
        status="success",
    )
    return {"detail": "Tracking updated", "status": "shipped", "tracking_number": tracking_number}


def _product_to_dict(product: Product) -> dict[str, Any]:
    cols = [c.name for c in Product.__table__.columns]
    d = {}
    for col in cols:
        val = getattr(product, col, None)
        if isinstance(val, Decimal):
            val = float(val)
        d[col] = val
    # Handle relationships
    if hasattr(product, "variants") and product.variants:
        d["variants"] = [_variant_to_dict(v) for v in product.variants]
    return d


def _variant_to_dict(variant: Any) -> dict[str, Any]:
    cols = [c.name for c in variant.__table__.columns] if hasattr(variant, "__table__") else []
    d = {}
    for col in cols:
        val = getattr(variant, col, None)
        if isinstance(val, Decimal):
            val = float(val)
        d[col] = val
    return d


def get_all_products(
    db: Session,
    limit: Optional[int] = None,
    offset: int = 0,
    search: Optional[str] = None,
    filter_value: Optional[str] = None,
) -> dict[str, Any]:
    resolved_limit = _ADMIN_DEFAULT_PAGE_SIZE if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))
    query = db.query(Product).options(selectinload(Product.variants))
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Product.name.ilike(term),
                Product.category.ilike(term),
                Product.brand.ilike(term),
                func.cast(Product.id, String).ilike(term),
            )
        )
    if filter_value == "deleted":
        query = query.filter(Product.is_deleted.is_(True))
    else:
        query = query.filter(Product.is_deleted.is_(False))
        if filter_value == "pending":
            query = query.filter(Product.is_approved.is_(False))
        elif filter_value == "approved":
            query = query.filter(Product.is_approved.is_(True))
        elif filter_value == "rejected":
            query = query.filter(Product.is_approved.is_(False))
    query = query.order_by(Product.created_at.desc(), Product.id.desc())
    total = query.count()
    if offset:
        query = query.offset(offset)
    query = query.limit(resolved_limit)
    products = query.all()
    # Serialize ORM objects to dicts for Pydantic response model
    items = [_product_to_dict(p) for p in products]
    return _build_list_page_payload(items, total, offset=offset, page_size=resolved_limit)


def delete_product_admin(product_id: int, acting_user: dict, db: Session) -> dict:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product_name = str(product.name)

    # --- Cascade 1: Remove from all carts ---
    db.query(CartItem).filter(CartItem.product_id == product_id).delete(synchronize_session=False)

    # --- Cascade 2: Remove from all wishlists ---
    db.query(Wishlist).filter(Wishlist.product_id == product_id).delete(synchronize_session=False)

    # --- Cascade 3: Soft-delete reviews (preserve data history) ---
    db.query(Review).filter(
        Review.product_id == product_id,
        Review.is_deleted == False,  # noqa: E712
    ).update({"is_deleted": True}, synchronize_session=False)

    # --- Cascade 4: Notify users with pending/processing orders that include this product ---
    affected_orders = (
        db.query(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(
            OrderItem.product_id == product_id,
            Order.status.in_(["pending", "processing", "confirmed"]),
        )
        .all()
    )
    for order in affected_orders:
        db.add(Notification(
            user_id=order.user_id,
            type="system",
            title="Product Unavailable",
            message=(
                f"A product ('{product_name}') in your order #{order.id} "
                "is no longer available. Our support team will contact you."
            ),
            link=f"/orders/{order.id}",
        ))

    # --- Soft-delete the product itself ---
    setattr(product, "is_deleted", True)
    db.commit()

    audit_log(
        db=db,
        action=AuditAction.PRODUCT_DELETE,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="product",
        resource_id=product_id,
        details={
            "product_name": product_name,
            "carts_cleared": True,
            "wishlists_cleared": True,
            "reviews_archived": True,
            "orders_notified": len(affected_orders),
        },
        status="success",
    )
    return {"message": "Product deleted", "orders_notified": len(affected_orders)}


def restore_product_admin(product_id: int, acting_user: dict, db: Session) -> dict:
    """Restore a soft-deleted product (admin only)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if not bool(cast(Any, getattr(product, "is_deleted"))):
        raise HTTPException(status_code=400, detail="Product is not archived")
    setattr(product, "is_deleted", False)
    db.commit()
    audit_log(
        db=db,
        action=AuditAction.PRODUCT_UPDATE,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="product",
        resource_id=product_id,
        details={"product_name": product.name, "action": "restore"},
        status="success",
    )
    return {"message": "Product restored"}


# ── Soft-delete / Archive / Restore entity wrappers ─────────────────────────

def archive_entity(
    model_name: str,
    record_id: int,
    acting_user: dict,
    db: Session,
    reason: Optional[str] = None,
    check_relations: Optional[list] = None,
) -> dict:
    """Generic archive for any entity. Optionally checks for dependent records."""
    model_map = {
        "product": Product, "user": User, "order": Order, "category": Category,
        "coupon": Coupon, "banner": Banner, "flash_sale": FlashSale,
        "supplier_profile": SupplierProfile, "logistics_partner": LogisticsPartner,
        "country_config": CountryConfig, "payout": Payout, "shipment": Shipment,
        "invoice": Invoice, "support_ticket": SupportTicket, "return_request": ReturnRequest,
        "supplier_document": SupplierDocument, "review": Review,
    }
    model = model_map.get(model_name)
    if not model:
        raise HTTPException(status_code=400, detail=f"Unknown entity type: {model_name}")

    if check_relations:
        record = db.query(model).filter(model.id == record_id).first()
        if record:
            for rel_name in check_relations:
                rel = getattr(record, rel_name, None)
                if rel is not None:
                    count = rel.count() if hasattr(rel, "count") else (len(rel) if isinstance(rel, list) else 0)
                    if count > 0:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Cannot archive: {record_id} has {count} related {rel_name}",
                        )

    soft_delete(db, model, record_id, acting_user, reason)
    return {"message": f"{model_name} archived", "id": record_id}


def restore_entity(
    model_name: str,
    record_id: int,
    acting_user: dict,
    db: Session,
) -> dict:
    """Generic restore for any entity."""
    model_map = {
        "product": Product, "user": User, "order": Order, "category": Category,
        "coupon": Coupon, "banner": Banner, "flash_sale": FlashSale,
        "supplier_profile": SupplierProfile, "logistics_partner": LogisticsPartner,
        "country_config": CountryConfig, "payout": Payout, "shipment": Shipment,
        "invoice": Invoice, "support_ticket": SupportTicket, "return_request": ReturnRequest,
        "supplier_document": SupplierDocument, "review": Review,
    }
    model = model_map.get(model_name)
    if not model:
        raise HTTPException(status_code=400, detail=f"Unknown entity type: {model_name}")
    restore(db, model, record_id, acting_user)
    return {"message": f"{model_name} restored", "id": record_id}


def bulk_archive_entities(
    model_name: str,
    record_ids: List[int],
    acting_user: dict,
    db: Session,
    reason: Optional[str] = None,
) -> dict:
    """Bulk archive for any entity."""
    model_map = {
        "product": Product, "user": User, "order": Order, "category": Category,
        "coupon": Coupon, "banner": Banner, "flash_sale": FlashSale,
        "supplier_profile": SupplierProfile, "logistics_partner": LogisticsPartner,
        "country_config": CountryConfig, "payout": Payout, "shipment": Shipment,
        "invoice": Invoice, "support_ticket": SupportTicket, "return_request": ReturnRequest,
        "supplier_document": SupplierDocument, "review": Review,
    }
    model = model_map.get(model_name)
    if not model:
        raise HTTPException(status_code=400, detail=f"Unknown entity type: {model_name}")
    result = bulk_soft_delete(db, model, record_ids, acting_user, reason)
    return {"message": f"{len(record_ids)} {model_name}(s) archived", **result}


def bulk_restore_entities(
    model_name: str,
    record_ids: List[int],
    acting_user: dict,
    db: Session,
) -> dict:
    """Bulk restore for any entity."""
    model_map = {
        "product": Product, "user": User, "order": Order, "category": Category,
        "coupon": Coupon, "banner": Banner, "flash_sale": FlashSale,
        "supplier_profile": SupplierProfile, "logistics_partner": LogisticsPartner,
        "country_config": CountryConfig, "payout": Payout, "shipment": Shipment,
        "invoice": Invoice, "support_ticket": SupportTicket, "return_request": ReturnRequest,
        "supplier_document": SupplierDocument, "review": Review,
    }
    model = model_map.get(model_name)
    if not model:
        raise HTTPException(status_code=400, detail=f"Unknown entity type: {model_name}")
    result = bulk_restore(db, model, record_ids, acting_user)
    return {"message": f"{len(record_ids)} {model_name}(s) restored", **result}


def hard_delete_entity(
    model_name: str,
    record_id: int,
    acting_user: dict,
    db: Session,
    reason: Optional[str] = None,
) -> dict:
    """Permanent delete (super admin only) for any entity."""
    model_map = {
        "product": Product, "user": User, "order": Order, "category": Category,
        "coupon": Coupon, "banner": Banner, "flash_sale": FlashSale,
        "supplier_profile": SupplierProfile, "logistics_partner": LogisticsPartner,
        "country_config": CountryConfig, "payout": Payout, "shipment": Shipment,
        "invoice": Invoice, "support_ticket": SupportTicket, "return_request": ReturnRequest,
        "supplier_document": SupplierDocument, "review": Review,
    }
    model = model_map.get(model_name)
    if not model:
        raise HTTPException(status_code=400, detail=f"Unknown entity type: {model_name}")
    hard_delete(db, model, record_id, acting_user, reason)
    return {"message": f"{model_name} permanently deleted", "id": record_id}


def bulk_category_change(
    product_ids: List[int],
    category_id: int,
    acting_user: dict,
    db: Session,
    reason: Optional[str] = None,
) -> dict:
    """Change category for multiple products at once."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    updated = 0
    for pid in product_ids:
        product = db.query(Product).filter(Product.id == pid).first()
        if product and not product.is_deleted:
            product.category_id = category_id
            product.category = category.name
            updated += 1
    db.commit()
    audit_log(
        db=db,
        action=AuditAction.PRODUCT_UPDATE,
        user_id=acting_user.get("id"),
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="product",
        resource_id=None,
        details={"action": "bulk_category_change", "product_ids": product_ids, "category_id": category_id, "reason": reason},
        status="success",
    )
    return {"message": f"Category changed for {updated} products", "updated": updated}


def _compute_analytics_overview(db: Session) -> dict[str, Any]:
    total_users = db.query(User).count()
    total_products = db.query(Product).count()
    total_orders = db.query(Order).count()
    total_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.status.in_(["delivered", "confirmed"])
    ).scalar() or 0.0

    thirty_days_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
    daily_rows = (
        db.query(
            func.date(Order.created_at).label("day"),
            func.sum(Order.total_amount).label("revenue"),
            func.count(Order.id).label("orders"),
        )
        .filter(Order.created_at >= thirty_days_ago)
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
        .all()
    )
    daily_data = [
        {"date": str(row.day), "revenue": float(row.revenue or 0), "orders": row.orders}
        for row in daily_rows
    ]

    cat_rows = (
        db.query(Product.category, func.count(Product.id).label("count"))
        .group_by(Product.category)
        .order_by(desc(func.count(Product.id)))
        .limit(8)
        .all()
    )
    top_categories = [{"category": row.category or "Uncategorized", "count": row.count} for row in cat_rows]

    return {
        "total_users": total_users,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": float(total_revenue),
        "daily_data": daily_data,
        "top_categories": top_categories,
    }


def get_analytics(db: Session) -> dict:
    return _get_admin_analytics_payload("overview", "overview", lambda: _compute_analytics_overview(db), db)


def get_supplier_comparison(db: Session, limit: Optional[int] = None, offset: int = 0) -> dict[str, Any]:
    resolved_limit = _ADMIN_DEFAULT_PAGE_SIZE if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))
    supplier_query = db.query(User).filter(User.role == "supplier")
    total = supplier_query.count()
    suppliers = (
        supplier_query
        .order_by(User.created_at.desc(), User.id.desc())
        .offset(max(0, offset))
        .limit(resolved_limit)
        .all()
    )
    if not suppliers:
        return _build_list_page_payload([], total, offset=offset, page_size=resolved_limit)

    supplier_ids = [s.id for s in suppliers]
    comparison_since = datetime.now(timezone.utc).replace(tzinfo=None)
    recent_since = comparison_since - timedelta(days=30)
    previous_since = comparison_since - timedelta(days=60)

    # Batch: product counts per supplier
    product_count_rows = (
        db.query(Product.supplier_id, func.count(Product.id).label("product_count"))
        .filter(Product.supplier_id.in_(supplier_ids), Product.is_deleted.is_(False))
        .group_by(Product.supplier_id)
        .all()
    )
    product_counts = {
        cast(int, row.supplier_id): int(row.product_count or 0)
        for row in product_count_rows
    }

    # Batch: avg price per supplier
    avg_price_rows = (
        db.query(Product.supplier_id, func.avg(Product.price).label("avg_price"))
        .filter(Product.supplier_id.in_(supplier_ids), Product.is_deleted.is_(False))
        .group_by(Product.supplier_id)
        .all()
    )
    avg_prices = {
        cast(int, row.supplier_id): round(float(row.avg_price or 0), 2)
        for row in avg_price_rows
    }

    # Batch: revenue and order counts per supplier via OrderItem join
    revenue_data: dict[int, float] = {}
    order_count_data: dict[int, int] = {}
    rev_rows = (
        db.query(
            Product.supplier_id,
            func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
            func.count(func.distinct(OrderItem.order_id)).label("order_count"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .filter(Product.supplier_id.in_(supplier_ids), Product.is_deleted.is_(False))
        .group_by(Product.supplier_id)
        .all()
    )
    for row in rev_rows:
        supplier_id = cast(int, row.supplier_id)
        revenue_data[supplier_id] = float(row.revenue or 0)
        order_count_data[supplier_id] = int(row.order_count or 0)

    recent_rows = (
        db.query(
            Product.supplier_id,
            func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0).label("revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Product.supplier_id.in_(supplier_ids),
            Product.is_deleted.is_(False),
            Order.created_at >= recent_since,
        )
        .group_by(Product.supplier_id)
        .all()
    )
    previous_rows = (
        db.query(
            Product.supplier_id,
            func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0).label("revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Product.supplier_id.in_(supplier_ids),
            Product.is_deleted.is_(False),
            Order.created_at >= previous_since,
            Order.created_at < recent_since,
        )
        .group_by(Product.supplier_id)
        .all()
    )
    recent_revenue = {cast(int, row.supplier_id): float(row.revenue or 0) for row in recent_rows}
    previous_revenue = {cast(int, row.supplier_id): float(row.revenue or 0) for row in previous_rows}
    total_revenue = sum(revenue_data.values()) or 0.0

    results = []
    for supplier in suppliers:
        sid = cast(int, supplier.id)
        joined_at = cast(datetime | None, getattr(supplier, "created_at"))
        supplier_revenue = round(revenue_data.get(sid, 0.0), 2)
        current_window = recent_revenue.get(sid, 0.0)
        previous_window = previous_revenue.get(sid, 0.0)
        if previous_window <= 0:
            growth_rate = 100.0 if current_window > 0 else 0.0
        else:
            growth_rate = round(((current_window - previous_window) / previous_window) * 100, 2)
        results.append({
            "id": sid,
            "username": supplier.username,
            "email": supplier.email,
            "product_count": product_counts.get(sid, 0),
            "order_count": order_count_data.get(sid, 0),
            "revenue": supplier_revenue,
            "avg_price": avg_prices.get(sid, 0.0),
            "growth_rate": growth_rate,
            "revenue_share": round((supplier_revenue / total_revenue) * 100, 2) if total_revenue else 0.0,
            "joined": joined_at.isoformat() if joined_at else None,
        })

    results.sort(key=lambda item: item["revenue"], reverse=True)
    return _build_list_page_payload(results, total, offset=offset, page_size=resolved_limit)


def get_customer_insights(db: Session) -> dict:
    top_cust_rows = (
        db.query(
            Order.user_id,
            User.username,
            User.email,
            func.count(Order.id).label("order_count"),
            func.sum(Order.total_amount).label("total_spent"),
        )
        .join(User, User.id == Order.user_id)
        .group_by(Order.user_id, User.username, User.email)
        .order_by(desc(func.sum(Order.total_amount)))
        .limit(10)
        .all()
    )
    top_customers = [
        {
            "user_id": row.user_id,
            "username": row.username,
            "email": row.email,
            "order_count": row.order_count,
            "total_spent": round(float(row.total_spent or 0), 2),
        }
        for row in top_cust_rows
    ]

    cat_rows = (
        db.query(Product.category, func.sum(OrderItem.quantity).label("units_sold"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.category)
        .order_by(desc(func.sum(OrderItem.quantity)))
        .limit(10)
        .all()
    )
    top_categories = [
        {"category": row.category or "Uncategorized", "units_sold": int(row.units_sold or 0)}
        for row in cat_rows
    ]

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)

    new_this_month = db.query(User).filter(
        User.role == "customer",
        User.created_at >= this_month_start,
    ).count()
    new_last_month = db.query(User).filter(
        User.role == "customer",
        User.created_at >= last_month_start,
        User.created_at < this_month_start,
    ).count()

    return {
        "top_customers": top_customers,
        "top_categories": top_categories,
        "new_customers_this_month": new_this_month,
        "new_customers_last_month": new_last_month,
    }


def get_audit_log_page(
    db: Session,
    page: int = 1,
    page_size: int = 50,
    action_filter: Optional[str] = None,
    user_id_filter: Optional[int] = None,
    resource_type_filter: Optional[str] = None,
    resource_id_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
) -> dict:
    return get_audit_logs(
        db=db,
        page=page,
        page_size=page_size,
        action_filter=action_filter,
        user_id_filter=user_id_filter,
        resource_type_filter=resource_type_filter,
        resource_id_filter=resource_id_filter,
        status_filter=status_filter,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )


def get_available_audit_actions(db: Session) -> list:
    return get_unique_actions(db)


# â”€â”€ Supplier Verification â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_pending_suppliers(db: Session, limit: Optional[int] = None, offset: int = 0) -> dict[str, Any]:
    """Return suppliers who have not yet been verified."""
    resolved_limit = _ADMIN_DEFAULT_PAGE_SIZE if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))
    supplier_query = db.query(User).filter(User.role == "supplier", User.is_verified.is_(False))
    total = supplier_query.count()
    suppliers = (
        supplier_query
        .order_by(User.created_at.asc(), User.id.asc())
        .offset(max(0, offset))
        .limit(resolved_limit)
        .all()
    )
    return _build_list_page_payload([
        {
            "id": s.id,
            "username": s.username,
            "email": s.email,
            "phone": s.phone,
            "created_at": s.created_at,
            "is_active": s.is_active,
            "verification_note": s.verification_note,
        }
        for s in suppliers
    ], total, offset=offset, page_size=resolved_limit)


def verify_supplier(user_id: int, note: Optional[str], acting_user: dict, db: Session) -> dict:
    from models import SupplierProfile, CountryConfig

    user = db.query(User).filter(User.id == user_id, User.role == "supplier").first()
    if not user:
        raise HTTPException(status_code=404, detail="Supplier not found")

    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
    if profile is None:
        profile = SupplierProfile(user_id=user_id)
        db.add(profile)
        db.flush()

    if bool(cast(Any, getattr(user, "is_verified"))) and cast(str | None, getattr(profile, "verification_status", None)) == "approved":
        return {"message": "Supplier already verified"}

    # ── Country-specific KYC enforcement ───────────────────────────────────
    supplier_country = str(getattr(user, "preferred_country", "") or "").strip()
    if supplier_country:
        country_config = db.query(CountryConfig).filter(
            CountryConfig.code == supplier_country.upper(),
            CountryConfig.is_active == True,
        ).first()
        if country_config:
            req_raw = country_config.supplier_requirements_json
            if req_raw:
                try:
                    import json
                    requirements = json.loads(req_raw) if isinstance(req_raw, str) else req_raw
                except (json.JSONDecodeError, TypeError):
                    requirements = {}
                if isinstance(requirements, dict):
                    required_docs = requirements.get("required_documents", [])
                    if required_docs and isinstance(required_docs, list):
                        from models import SupplierDocument
                        approved_types = set()
                        for doc in db.query(SupplierDocument).filter(
                            SupplierDocument.supplier_id == user_id,
                            SupplierDocument.status == "approved",
                        ).all():
                            approved_types.add(str(getattr(doc, "document_type", "")).strip().lower())

                        missing = [
                            d for d in required_docs
                            if str(d).strip().lower() not in approved_types
                        ]
                        if missing:
                            raise HTTPException(
                                status_code=422,
                                detail=f"Supplier missing required documents for country '{supplier_country}': {', '.join(missing)}. Required: {required_docs}",
                            )

    setattr(user, "is_verified", True)
    setattr(user, "verification_note", note or "Approved")
    setattr(profile, "verification_status", "approved")
    setattr(profile, "verified_at", datetime.now(timezone.utc).replace(tzinfo=None))
    db.add(
        Notification(
            user_id=user.id,
            type="account",
            title="Account Verified",
            message="Congratulations! Your supplier account has been verified. You can now list products.",
            link="/supplier/dashboard",
        )
    )
    db.commit()
    audit_log(
        db=db,
        action=AuditAction.SUPPLIER_VERIFIED,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="user",
        resource_id=user_id,
        details={"supplier_username": user.username, "note": note},
        status="success",
    )
    return {"message": "Supplier verified", "supplier_id": user_id, "username": user.username}


def reject_supplier(user_id: int, note: Optional[str], acting_user: dict, db: Session) -> dict:
    from models import SupplierProfile

    user = db.query(User).filter(User.id == user_id, User.role == "supplier").first()
    if not user:
        raise HTTPException(status_code=404, detail="Supplier not found")

    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
    if profile is None:
        profile = SupplierProfile(user_id=user_id)
        db.add(profile)
        db.flush()

    setattr(user, "is_verified", False)
    setattr(user, "verification_note", note or "Rejected")
    setattr(profile, "verification_status", "rejected")
    setattr(profile, "verified_at", None)
    db.add(
        Notification(
            user_id=user.id,
            type="account",
            title="Verification Declined",
            message=f"Your supplier account verification was declined. Reason: {note or 'Please contact support.'}",
            link="/supplier/dashboard",
        )
    )
    db.commit()
    audit_log(
        db=db,
        action=AuditAction.SUPPLIER_REJECTED,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="user",
        resource_id=user_id,
        details={"supplier_username": user.username, "note": note},
        status="success",
    )
    return {"message": "Supplier verification rejected", "supplier_id": user_id, "username": user.username}


# â”€â”€ Product Moderation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_pending_products(db: Session, limit: Optional[int] = None, offset: int = 0) -> dict[str, Any]:
    """Return products pending admin approval."""
    resolved_limit = _ADMIN_DEFAULT_PAGE_SIZE if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))
    product_query = db.query(Product).filter(Product.is_approved.is_(False), Product.is_deleted.is_(False))
    total = product_query.count()
    products = (
        product_query
        .order_by(Product.created_at.asc(), Product.id.asc())
        .offset(max(0, offset))
        .limit(resolved_limit)
        .all()
    )
    return _build_list_page_payload([
        {
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "price": p.price,
            "supplier_id": p.supplier_id,
            "image_url": _normalize_image_path(cast(str | None, getattr(p, "image_url"))),
            "created_at": p.created_at,
        }
        for p in products
    ], total, offset=offset, page_size=resolved_limit)


def toggle_product_badge(
    product_id: int,
    field: str,
    value: bool,
    acting_user: dict,
    db: Session,
) -> dict:
    """Set is_hot, is_featured, or is_new on a product."""
    allowed = {"is_hot", "is_featured", "is_new"}
    if field not in allowed:
        raise HTTPException(status_code=400, detail=f"field must be one of {allowed}")
    product = db.query(Product).filter(Product.id == product_id, Product.is_deleted.is_(False)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    setattr(product, field, value)
    db.commit()
    audit_log(
        db=db,
        action=f"PRODUCT_BADGE_{field.upper()}_{'ON' if value else 'OFF'}",
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="product",
        resource_id=product_id,
        details={"product_name": product.name, "field": field, "value": value},
        status="success",
    )
    return {"message": f"{field} set to {value}", "product_id": product_id}


def approve_product(product_id: int, acting_user: dict, db: Session) -> dict:
    product = db.query(Product).filter(Product.id == product_id, Product.is_deleted.is_(False)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    from controllers.country_controller import is_product_restricted_for_country
    supplier = db.query(User).filter(User.id == product.supplier_id).first()
    if supplier:
        supplier_country = str(getattr(supplier, "preferred_country", "") or "").strip()
        if supplier_country:
            product_category = str(getattr(product, "category", "") or "").strip().lower()
            if is_product_restricted_for_country(product_category, supplier_country, db):
                raise HTTPException(
                    status_code=422,
                    detail=f"Product category '{product_category}' is restricted in the supplier's country ({supplier_country}).",
                )

    setattr(product, "is_approved", True)
    setattr(product, "is_active", True)
    db.add(
        Notification(
            user_id=product.supplier_id,
            type="product",
            title="Product Approved",
            message=f'Your product "{product.name}" has been approved and is now live.',
            link=f"/products/{product.id}",
        )
    )
    db.commit()
    audit_log(
        db=db,
        action="PRODUCT_APPROVED",
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="product",
        resource_id=product_id,
        details={"product_name": product.name},
        status="success",
    )
    return {"message": "Product approved", "product_id": product_id}


def reject_product(product_id: int, note: Optional[str], acting_user: dict, db: Session) -> dict:
    product = db.query(Product).filter(Product.id == product_id, Product.is_deleted.is_(False)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    setattr(product, "is_approved", False)
    setattr(product, "is_active", False)
    db.add(
        Notification(
            user_id=product.supplier_id,
            type="product",
            title="Product Rejected",
            message=f'Your product "{product.name}" was not approved. Reason: {note or "Does not meet listing standards."}',
            link="/supplier/products",
        )
    )
    db.commit()
    audit_log(
        db=db,
        action="PRODUCT_REJECTED",
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="product",
        resource_id=product_id,
        details={"product_name": product.name, "note": note},
        status="success",
    )
    return {"message": "Product rejected", "product_id": product_id}


# â”€â”€ Coupon Management â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def list_coupons(db: Session, *, skip: int = 0, limit: int | None = None, search: Optional[str] = None) -> dict:
    resolved_limit = _ADMIN_DEFAULT_PAGE_SIZE if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))
    query = db.query(Coupon)
    if search and search.strip():
        query = query.filter(Coupon.code.ilike(f"%{search.strip()}%"))
    total = query.with_entities(func.count(Coupon.id)).scalar() or 0
    coupons = (
        query.order_by(Coupon.created_at.desc(), Coupon.id.desc())
        .offset(skip)
        .limit(resolved_limit)
        .all()
    )
    return _build_list_page_payload([
            {
                "id": c.id,
                "code": c.code,
                "discount_type": c.discount_type,
                "value": c.value,
                "discount_value": c.value,
                "min_order": c.min_order,
                "min_order_amount": c.min_order,
                "max_uses": c.max_uses,
                "uses_count": c.uses_count,
                "used_count": c.uses_count,
                "expires_at": c.expires_at,
                "is_active": c.is_active,
                "created_at": c.created_at,
            }
            for c in coupons
        ], total, offset=skip, page_size=resolved_limit)


def create_coupon(data: dict, acting_user: dict, db: Session) -> dict:
    code = (data.get("code") or "").strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Coupon code is required")
    if db.query(Coupon).filter(Coupon.code == code).first():
        raise HTTPException(status_code=409, detail="Coupon code already exists")

    from datetime import datetime as _dt
    expires_raw = data.get("expires_at")
    expires_at = None
    if expires_raw:
        try:
            expires_at = _dt.fromisoformat(str(expires_raw).replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            expires_at = None

    coupon = Coupon(
        code=code,
        discount_type=data.get("discount_type", "percent"),
        value=float(data.get("value", 10)),
        min_order=float(data.get("min_order", 0)),
        max_uses=int(data["max_uses"]) if data.get("max_uses") else None,
        expires_at=expires_at,
        is_active=bool(data.get("is_active", True)),
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    audit_log(
        db=db,
        action="COUPON_CREATED",
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="coupon",
        resource_id=cast(int, getattr(coupon, "id")),
        details={"code": coupon.code, "value": coupon.value},
        status="success",
    )
    return {"message": "Coupon created", "id": coupon.id, "code": coupon.code}


def update_coupon(coupon_id: int, data: dict, acting_user: dict, db: Session) -> dict:
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    for field in ("discount_type", "value", "min_order", "max_uses", "is_active"):
        if field in data:
            setattr(coupon, field, data[field])
    if "expires_at" in data and data["expires_at"]:
        from datetime import datetime as _dt
        try:
            setattr(coupon, "expires_at", _dt.fromisoformat(str(data["expires_at"]).replace("Z", "+00:00")).replace(tzinfo=None))
        except ValueError:
            pass
    db.commit()
    return {"message": "Coupon updated", "id": coupon_id}


def delete_coupon(coupon_id: int, acting_user: dict, db: Session) -> dict:
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    usage_count = db.query(func.count(CouponUsage.id)).filter(CouponUsage.coupon_id == coupon_id).scalar() or 0
    if usage_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Coupon has {usage_count} recorded usage(s). Archive or disable it instead of deleting.",
        )

    try:
        db.delete(coupon)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Coupon has related records that must be archived or removed before deletion.",
        )
    return {"message": "Coupon deleted"}


# â”€â”€ Support Tickets â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _serialize_ticket_attachment(attachment: TicketAttachment) -> dict[str, Any]:
    return {
        "id": cast(int, getattr(attachment, "id")),
        "original_name": cast(str, getattr(attachment, "original_name")),
        "mime_type": cast(str | None, getattr(attachment, "mime_type", None)),
        "file_size_bytes": cast(int | None, getattr(attachment, "file_size_bytes", None)),
        "file_path": cast(str, getattr(attachment, "file_path")),
        "created_at": cast(datetime, getattr(attachment, "created_at")),
    }


def _serialize_ticket_message(reply: TicketMessage) -> dict[str, Any]:
    user = cast(User | None, getattr(reply, "sender", None))
    return {
        "id": cast(int, getattr(reply, "id")),
        "user_id": cast(int | None, getattr(reply, "sender_id", None)),
        "username": cast(str | None, getattr(user, "username", None)) if user else ("Admin" if getattr(reply, "is_admin", False) else "User"),
        "message": cast(str, getattr(reply, "message")),
        "is_admin": bool(cast(Any, getattr(reply, "is_admin", False))),
        "created_at": cast(datetime, getattr(reply, "created_at")),
        "attachments": [],
    }


def _serialize_support_ticket(ticket: SupportTicket, *, include_message: bool = False, include_replies: bool = False) -> dict[str, Any]:
    user = cast(User | None, getattr(ticket, "user", None))
    payload: dict[str, Any] = {
        "id": cast(int, getattr(ticket, "id")),
        "user_id": cast(int | None, getattr(ticket, "user_id", None)),
        "username": cast(str | None, getattr(user, "username", None)) if user else "Unknown",
        "subject": cast(str, getattr(ticket, "subject")),
        "status": cast(str, getattr(ticket, "status")),
        "priority": cast(str | None, getattr(ticket, "priority", None)) or "normal",
        "ticket_category": cast(str | None, getattr(ticket, "ticket_category", None)) or "customer",
        "raised_by_role": cast(str | None, getattr(ticket, "raised_by_role", None)),
        "related_entity_type": cast(str | None, getattr(ticket, "related_entity_type", None)),
        "related_entity_id": cast(int | None, getattr(ticket, "related_entity_id", None)),
        "created_at": cast(datetime, getattr(ticket, "created_at")),
        "updated_at": cast(datetime, getattr(ticket, "updated_at")),
        "reply_count": len(list(getattr(ticket, "messages", []) or [])),
        "attachments": [_serialize_ticket_attachment(attachment) for attachment in list(getattr(ticket, "attachments", []) or [])],
    }
    if include_message:
        msgs = list(getattr(ticket, "messages", []) or [])
        payload["message"] = cast(str, msgs[0].message) if msgs else ""
    if include_replies:
        payload["replies"] = [_serialize_ticket_message(reply) for reply in list(getattr(ticket, "messages", []) or [])]
    return payload

def list_tickets(db: Session, status: Optional[str] = None, limit: Optional[int] = None, offset: int = 0) -> dict[str, Any]:
    resolved_limit = 200 if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))
    q = db.query(SupportTicket)
    if status:
        q = q.filter(SupportTicket.status == status)
    total = q.count()
    tickets = (
        q.options(
            selectinload(SupportTicket.attachments),
            selectinload(SupportTicket.messages),
        )
        .order_by(SupportTicket.created_at.desc(), SupportTicket.id.desc())
        .offset(max(0, offset))
        .limit(resolved_limit)
        .all()
    )
    serialized = [_serialize_support_ticket(ticket) for ticket in tickets]
    return _build_list_page_payload(serialized, total, offset=offset, page_size=resolved_limit)


def get_ticket_detail(ticket_id: int, db: Session) -> dict:
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return _serialize_support_ticket(ticket, include_message=True, include_replies=True)


def reply_to_ticket(ticket_id: int, message: str, acting_user: dict, db: Session) -> dict:
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="Reply message cannot be empty")
    reply = TicketMessage(
        ticket_id=ticket_id,
        sender_id=acting_user["id"],
        message=message.strip(),
        is_admin=True,
    )
    db.add(reply)
    if cast(str, getattr(ticket, "status")) in {"open", "pending", "resolved", "closed"}:
        setattr(ticket, "status", "in_progress")
    db.add(
        Notification(
            user_id=ticket.user_id,
            type="support",
            title="Support Reply Received",
            message=f'Admin replied to your ticket: "{ticket.subject}"',
            link=f"/tickets/{ticket.id}",
        )
    )
    db.commit()
    db.refresh(ticket)
    return _serialize_support_ticket(ticket, include_message=True, include_replies=True)


def update_ticket_status(ticket_id: int, status: str, acting_user: dict, db: Session) -> dict:
    allowed = {"open", "pending", "in_progress", "resolved", "closed"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(allowed)}")
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    setattr(ticket, "status", status)
    db.commit()
    db.refresh(ticket)
    return _serialize_support_ticket(ticket, include_message=True, include_replies=True)


def list_pending_payouts(db: Session) -> list:
    payouts = (
        db.query(Payout)
        .filter(Payout.status.in_(["pending", "processing"]))
        .order_by(Payout.created_at.asc())
        .all()
    )
    return [
        {
            "id": payout.id,
            "supplier_id": payout.supplier_id,
            "supplier_username": payout.supplier.username if payout.supplier else None,
            "amount": float(cast(Any, getattr(payout, "amount")) or 0),
            "status": payout.status,
            "method": payout.method,
            "reference": payout.reference_id,
            "notes": payout.notes,
            "created_at": payout.created_at,
            "processed_at": payout.processed_at,
        }
        for payout in payouts
    ]


def _refresh_order_finance_settlement_status(order_id: int, db: Session) -> None:
    entries = db.query(TransactionLedger).filter(TransactionLedger.order_id == order_id).all()
    if not entries:
        return

    for entry in entries:
        if str(getattr(entry, "settlement_status", "") or "") == "refunded":
            continue

        supplier_settlement = (
            db.query(SupplierSettlement)
            .filter(
                SupplierSettlement.order_id == order_id,
                SupplierSettlement.supplier_id == entry.supplier_id,
            )
            .first()
        )
        logistics_settlement = None
        if entry.logistics_partner_id:
            logistics_settlement = (
                db.query(LogisticsSettlement)
                .filter(
                    LogisticsSettlement.order_id == order_id,
                    LogisticsSettlement.partner_id == entry.logistics_partner_id,
                )
                .first()
            )

        supplier_done = bool(supplier_settlement and supplier_settlement.status == "settled")
        logistics_done = True if entry.logistics_partner_id is None else bool(
            logistics_settlement and logistics_settlement.status == "settled"
        )

        if supplier_done and logistics_done:
            entry.settlement_status = "fully_settled"
        elif supplier_done:
            entry.settlement_status = "supplier_settled"
        elif logistics_done:
            entry.settlement_status = "logistics_settled"
        else:
            entry.settlement_status = "pending"


def _sync_supplier_settlements_for_payout(
    payout_id: int,
    new_status: str,
    processed_at: datetime | None,
    db: Session,
) -> None:
    settlements = db.query(SupplierSettlement).filter(SupplierSettlement.payout_id == payout_id).all()
    if not settlements:
        return

    touched_order_ids: set[int] = set()
    now = processed_at or datetime.now(timezone.utc).replace(tzinfo=None)

    for settlement in settlements:
        touched_order_ids.add(cast(int, settlement.order_id))

        if new_status == "completed":
            settlement.status = "settled"
            settlement.settled_at = now
        elif new_status == "rejected":
            settlement.status = "eligible" if settlement.eligible_at and settlement.eligible_at <= now else "pending"
            settlement.payout_id = None
            settlement.settled_at = None
            settlement.bank_transaction_id = None
        else:
            settlement.status = "processing"
            settlement.settled_at = None

    for order_id in touched_order_ids:
        _refresh_order_finance_settlement_status(order_id, db)


def verify_payout(
    payout_id: int,
    data: dict,
    acting_user: dict,
    db: Session,
) -> dict:
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")

    new_status = str(data.get("status", "")).strip().lower()
    if new_status not in {"processing", "completed", "rejected"}:
        raise HTTPException(status_code=422, detail="status must be one of: processing, completed, rejected")

    setattr(payout, "status", new_status)
    setattr(
        payout,
        "reference_id",
        str(data.get("reference", "")).strip()
        or cast(str | None, getattr(payout, "reference_id"))
        or build_transfer_reference(
            db,
            kind="supplier_payout",
            entity_id=int(cast(int, getattr(payout, "supplier_id"))),
            record_id=int(cast(int, getattr(payout, "id"))),
        ),
    )
    setattr(payout, "notes", str(data.get("notes", "")).strip() or cast(str | None, getattr(payout, "notes")))
    processed_at: datetime | None = None
    if new_status in {"completed", "rejected"}:
        processed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        setattr(payout, "processed_at", processed_at)
    else:
        setattr(payout, "processed_at", None)

    _sync_supplier_settlements_for_payout(payout_id, new_status, processed_at, db)

    supplier_id = cast(int | None, getattr(payout, "supplier_id"))
    if supplier_id:
        message = (
            f"Your payout request #{payout.id} is now {new_status}."
            if new_status != "completed"
            else f"Your payout request #{payout.id} has been completed."
        )
        db.add(
            Notification(
                user_id=supplier_id,
                type="payout",
                title="Payout Update",
                message=message,
                link="/supplier/payouts",
            )
        )

    db.commit()
    audit_log(
        db=db,
        action=AuditAction.PAYOUT_PROCESSED,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="payout",
        resource_id=cast(int, getattr(payout, "id")),
        details={"status": new_status, "reference": cast(str | None, getattr(payout, "reference_id"))},
        status="success",
    )
    return {
        "id": payout.id,
        "status": payout.status,
        "reference": payout.reference_id,
        "notes": payout.notes,
        "processed_at": payout.processed_at,
    }


def get_hierarchy_permissions(current_user: dict) -> dict:
    role = cast(str | None, current_user["role"])
    return {
        "role": role,
        "permissions": sorted(ROLE_PERMISSION_MAP.get(role, set())) if role else [],
        "matrix": {k: sorted(v) for k, v in ROLE_PERMISSION_MAP.items()},
    }


def update_role_permissions(role: str, new_permissions: list[str], db: Session, current_user: dict) -> dict:
    """Persist a new permission set for *role* and update the in-memory map.

    Only admin users may call this endpoint.  The supplied permissions are
    validated against the full set of known permission strings so that typos
    are caught early.
    """
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin-only access required")

    if role not in ROLE_PERMISSION_MAP:
        raise HTTPException(status_code=404, detail=f"Unknown role: {role}")

    unknown = [p for p in new_permissions if p not in KNOWN_ROLE_PERMISSIONS]
    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown permission(s): {', '.join(sorted(unknown))}",
        )

    # Upsert the DB row
    row = db.query(RolePermissionSetting).filter(RolePermissionSetting.role == role).first()
    if row is None:
        row = RolePermissionSetting(
            role=role,
            permissions=new_permissions,
            updated_by_id=current_user["id"],
        )
        db.add(row)
    else:
        row.permissions = new_permissions
        row.updated_by_id = current_user["id"]
    db.commit()

    load_role_permission_settings(db)

    return {
        "role": role,
        "permissions": sorted(new_permissions),
        "matrix": {k: sorted(v) for k, v in ROLE_PERMISSION_MAP.items()},
    }


# â”€â”€ Advanced Analytics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_PERIOD_DAYS = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}


def _compute_analytics_timeseries_payload(period: str, db: Session) -> dict[str, Any]:
    days = _PERIOD_DAYS.get(period, 30)
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)

    rows = (
        db.query(
            func.date(Order.created_at).label("day"),
            func.sum(Order.total_amount).label("revenue"),
            func.count(Order.id).label("orders"),
        )
        .filter(Order.created_at >= since)
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
        .all()
    )

    total_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.status.in_(["delivered", "confirmed", "processing", "shipped"]),
        Order.created_at >= since,
    ).scalar() or 0.0

    return {
        "period": period,
        "days": days,
        "total_revenue": round(float(total_revenue), 2),
        "data": [
            {"date": str(r.day), "revenue": round(float(r.revenue or 0), 2), "orders": r.orders}
            for r in rows
        ],
    }


def get_analytics_timeseries(period: str, db: Session) -> dict:
    return _get_admin_analytics_payload(
        f"timeseries:{period}",
        "timeseries",
        lambda: _compute_analytics_timeseries_payload(period, db),
        db,
        cache_payload={"period": period},
        period=period,
    )


def _compute_top_products_payload(limit: int, db: Session) -> dict[str, Any]:
    rows = (
        db.query(
            Product.id,
            Product.name,
            Product.category,
            Product.price,
            Product.image_url,
            func.sum(OrderItem.quantity).label("units_sold"),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label("revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .filter(Product.is_deleted.is_(False))
        .group_by(Product.id, Product.name, Product.category, Product.price, Product.image_url)
        .order_by(desc(func.sum(OrderItem.quantity)))
        .limit(limit)
        .all()
    )
    return {
        "products": [
            {
                "id": r.id,
                "name": r.name,
                "category": r.category,
                "price": float(r.price or 0),
                "image_url": r.image_url,
                "units_sold": int(r.units_sold or 0),
                "revenue": round(float(r.revenue or 0), 2),
            }
            for r in rows
        ]
    }


def get_top_products_analytics(limit: int, db: Session) -> dict:
    return _get_admin_analytics_payload(
        f"top-products:{limit}",
        "top-products",
        lambda: _compute_top_products_payload(limit, db),
        db,
        cache_payload={"limit": limit},
        period=str(limit),
    )


def _compute_user_growth_payload(period: str, db: Session) -> dict[str, Any]:
    days = _PERIOD_DAYS.get(period, 30)
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)

    rows = (
        db.query(
            func.date(User.created_at).label("day"),
            User.role,
            func.count(User.id).label("count"),
        )
        .filter(User.created_at >= since)
        .group_by(func.date(User.created_at), User.role)
        .order_by(func.date(User.created_at))
        .all()
    )

    # Aggregate by date
    by_date: dict[str, dict] = {}
    for r in rows:
        day = str(r.day)
        entry = by_date.setdefault(day, {"date": day, "customers": 0, "suppliers": 0, "total": 0})
        if r.role == "customer":
            entry["customers"] += r.count
        elif r.role == "supplier":
            entry["suppliers"] += r.count
        entry["total"] += r.count

    return {
        "period": period,
        "data": sorted(by_date.values(), key=lambda x: x["date"]),
    }


def get_user_growth_analytics(period: str, db: Session) -> dict:
    return _get_admin_analytics_payload(
        f"user-growth:{period}",
        "user-growth",
        lambda: _compute_user_growth_payload(period, db),
        db,
        cache_payload={"period": period},
        period=period,
    )


def get_all_suppliers(
    db: Session,
    *,
    skip: int = 0,
    limit: int | None = None,
    q: Optional[str] = None,
    status: Optional[str] = None,
    badge: Optional[str] = None,
) -> dict:
    """Return suppliers with summary profile, activity metrics, and server-side filters."""
    resolved_limit = _ADMIN_DEFAULT_PAGE_SIZE if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))

    query = (
        db.query(User)
        .outerjoin(SupplierProfile, SupplierProfile.user_id == User.id)
        .filter(User.role == "supplier")
    )

    normalized_query = (q or "").strip()
    if normalized_query:
        like = f"%{normalized_query}%"
        query = query.filter(
            or_(
                User.username.ilike(like),
                User.email.ilike(like),
                SupplierProfile.business_name.ilike(like),
            )
        )

    normalized_status = (status or "").strip().lower()
    if normalized_status and normalized_status != "all":
        if normalized_status == "pending":
            query = query.filter(User.is_active.in_([True, 1])).filter(
                or_(
                    SupplierProfile.verification_status.is_(None),
                    SupplierProfile.verification_status.in_(["pending", "under_review", "documents_submitted"]),
                )
            )
        elif normalized_status in {"approved", "verified"}:
            query = query.filter(User.is_active.in_([True, 1])).filter(
                or_(
                    SupplierProfile.verification_status.in_(["approved", "verified"]),
                    User.is_verified.is_(True),
                )
            )
        elif normalized_status == "rejected":
            query = query.filter(SupplierProfile.verification_status == "rejected")
        elif normalized_status in {"suspended", "archived"}:
            query = query.filter(User.is_active.in_([False, 0]))
        elif normalized_status == "active":
            query = query.filter(User.is_active.in_([True, 1]))

    normalized_badge = (badge or "").strip().lower()
    if normalized_badge and normalized_badge != "all":
        query = query.filter(SupplierProfile.badge_level == normalized_badge)

    total = query.count()
    suppliers = (
        query
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(resolved_limit)
        .all()
    )

    supplier_ids = [cast(int, supplier.id) for supplier in suppliers]
    profiles = {
        cast(int, profile.user_id): profile
        for profile in db.query(SupplierProfile).filter(SupplierProfile.user_id.in_(supplier_ids)).all()
    } if supplier_ids else {}

    product_metric_rows = (
        db.query(
            Product.supplier_id,
            func.count(Product.id).label("product_count"),
            func.avg(Product.price).label("avg_price"),
        )
        .filter(Product.supplier_id.in_(supplier_ids), Product.is_deleted.is_(False))
        .group_by(Product.supplier_id)
        .all()
    ) if supplier_ids else []
    product_metrics = {
        cast(int, row.supplier_id): {
            "product_count": int(row.product_count or 0),
            "avg_price": round(float(row.avg_price or 0), 2),
        }
        for row in product_metric_rows
    }

    revenue_rows = (
        db.query(
            Product.supplier_id,
            func.count(func.distinct(OrderItem.order_id)).label("order_count"),
            func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0).label("revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .filter(Product.supplier_id.in_(supplier_ids), Product.is_deleted.is_(False))
        .group_by(Product.supplier_id)
        .all()
    ) if supplier_ids else []
    revenue_metrics = {
        cast(int, row.supplier_id): {
            "order_count": int(row.order_count or 0),
            "revenue": round(float(row.revenue or 0), 2),
        }
        for row in revenue_rows
    }

    top_product_rows = (
        db.query(Product.supplier_id, Product.name, Product.sales_count)
        .filter(Product.supplier_id.in_(supplier_ids), Product.is_deleted.is_(False))
        .order_by(Product.supplier_id.asc(), Product.sales_count.desc(), Product.created_at.desc())
        .all()
    ) if supplier_ids else []
    top_products: dict[int, str | None] = {}
    for row in top_product_rows:
        supplier_id = cast(int, row.supplier_id)
        if supplier_id not in top_products:
            top_products[supplier_id] = cast(str | None, row.name)

    summary = {
        "pending_suppliers": int(
            (
                db.query(func.count(User.id))
                .outerjoin(SupplierProfile, SupplierProfile.user_id == User.id)
                .filter(
                    User.role == "supplier",
                    User.is_active.in_([True, 1]),
                    or_(
                        SupplierProfile.verification_status.is_(None),
                        SupplierProfile.verification_status.in_(["pending", "under_review", "documents_submitted"]),
                    ),
                )
                .scalar()
            ) or 0
        ),
        "active_suppliers": int((db.query(func.count(User.id)).filter(User.role == "supplier", User.is_active.in_([True, 1])).scalar()) or 0),
        "suspended_suppliers": int((db.query(func.count(User.id)).filter(User.role == "supplier", User.is_active.in_([False, 0])).scalar()) or 0),
        "total_revenue": round(
            float(
                (
                    db.query(func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0))
                    .join(Product, Product.id == OrderItem.product_id)
                    .join(User, User.id == Product.supplier_id)
                    .filter(User.role == "supplier", Product.is_deleted.is_(False))
                    .scalar()
                ) or 0
            ),
            2,
        ),
    }

    items = []
    for supplier in suppliers:
        profile = profiles.get(cast(int, supplier.id))
        metrics = product_metrics.get(cast(int, supplier.id), {})
        revenue = revenue_metrics.get(cast(int, supplier.id), {})
        verified_at = cast(datetime | None, getattr(profile, "verified_at", None)) if profile else None
        items.append(
            {
                "id": supplier.id,
                "username": supplier.username,
                "email": supplier.email,
                "phone": supplier.phone,
                "is_active": supplier.is_active,
                "is_verified": supplier.is_verified,
                "verification_note": supplier.verification_note,
                "created_at": supplier.created_at,
                "product_count": int(metrics.get("product_count", 0)),
                "order_count": int(revenue.get("order_count", 0)),
                "revenue": float(revenue.get("revenue", 0)),
                "avg_price": float(metrics.get("avg_price", 0)),
                "top_product_name": top_products.get(cast(int, supplier.id)),
                "profile": {
                    "business_name": profile.business_name if profile else None,
                    "business_type": profile.business_type if profile else None,
                    "country": profile.country_code if profile else None,
                    "region": profile.region if profile else None,
                    "city": profile.city if profile else None,
                    "website": profile.website if profile else None,
                    "phone_business": profile.phone_business if profile else None,
                    "tax_id": profile.tax_id if profile else None,
                    "verification_status": profile.verification_status if profile else "pending",
                    "badge_level": profile.badge_level if profile else None,
                    "credibility_score": profile.credibility_score if profile else 0,
                    "verified_at": verified_at.isoformat() if verified_at else None,
                } if profile else None,
            }
        )

    page = (skip // resolved_limit) + 1 if resolved_limit else 1
    total_pages = max(1, ((total - 1) // resolved_limit) + 1) if resolved_limit else 1

    return {
        "items": items,
        "summary": summary,
        "total": total,
        "page": page,
        "page_size": resolved_limit,
        "total_pages": total_pages,
        "skip": skip,
        "limit": resolved_limit,
        "filters": {
            "q": normalized_query or None,
            "status": normalized_status or "all",
            "badge": normalized_badge or "all",
        },
    }


def _safe_load_chatbot_filters(raw_filters: Optional[str]) -> dict[str, Any]:
    if not raw_filters:
        return {}
    try:
        loaded = json.loads(raw_filters)
        return loaded if isinstance(loaded, dict) else {}
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}


def get_chatbot_analytics(period: str, db: Session) -> dict:
    """Return assistant query trends, shopper behavior signals, and click engagement."""
    days = _PERIOD_DAYS.get(period, 30)
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)

    events = (
        db.query(ChatbotQueryEvent)
        .filter(ChatbotQueryEvent.created_at >= since)
        .order_by(ChatbotQueryEvent.created_at.asc())
        .all()
    )
    query_events = [event for event in events if cast(str | None, getattr(event, "event_type", None)) == "query"]
    click_events = [event for event in events if cast(str | None, getattr(event, "event_type", None)) == "product_click"]

    top_queries: Counter[str] = Counter()
    top_intents: Counter[str] = Counter()
    top_categories: Counter[str] = Counter()
    top_brands: Counter[str] = Counter()
    top_colors: Counter[str] = Counter()
    top_sizes: Counter[str] = Counter()
    no_result_queries: Counter[str] = Counter()
    daily_data: dict[str, dict[str, Any]] = {}
    budget_focused = 0
    quality_focused = 0
    brand_specific = 0

    for event in query_events:
        normalized_query = str(getattr(event, "normalized_query", "") or "").strip()
        intent = str(getattr(event, "intent", "") or "unknown")
        result_count = int(cast(Any, getattr(event, "result_count", 0)) or 0)
        filters = _safe_load_chatbot_filters(cast(str | None, getattr(event, "filters_json", None)))
        day = str(cast(datetime, getattr(event, "created_at")).date()) if getattr(event, "created_at", None) else "unknown"
        bucket = daily_data.setdefault(day, {"date": day, "queries": 0, "clicks": 0, "product_searches": 0})
        bucket["queries"] += 1
        if intent == "product_search":
            bucket["product_searches"] += 1

        if normalized_query:
            top_queries[normalized_query] += 1
            if result_count == 0:
                no_result_queries[normalized_query] += 1
        top_intents[intent] += 1

        category = str(filters.get("category") or "").strip()
        brand = str(filters.get("brand") or "").strip()
        color = str(filters.get("color") or "").strip()
        size = str(filters.get("size") or "").strip()
        if category:
            top_categories[category] += 1
        if brand:
            top_brands[brand] += 1
            brand_specific += 1
        if color:
            top_colors[color] += 1
        if size:
            top_sizes[size] += 1
        if filters.get("max_price") is not None or filters.get("min_price") is not None:
            budget_focused += 1
        if filters.get("quality") or filters.get("min_rating") is not None:
            quality_focused += 1

    for event in click_events:
        day = str(cast(datetime, getattr(event, "created_at")).date()) if getattr(event, "created_at", None) else "unknown"
        bucket = daily_data.setdefault(day, {"date": day, "queries": 0, "clicks": 0, "product_searches": 0})
        bucket["clicks"] += 1

    top_clicked_rows = (
        db.query(
            Product.id,
            Product.name,
            func.count(ChatbotQueryEvent.id).label("clicks"),
        )
        .join(Product, Product.id == ChatbotQueryEvent.clicked_product_id)
        .filter(
            ChatbotQueryEvent.created_at >= since,
            ChatbotQueryEvent.event_type == "product_click",
        )
        .group_by(Product.id, Product.name)
        .order_by(desc(func.count(ChatbotQueryEvent.id)))
        .limit(10)
        .all()
    )

    query_count = len(query_events)
    click_count = len(click_events)
    clicked_sessions = {getattr(event, "session_id", None) for event in click_events if getattr(event, "session_id", None)}
    clicked_session_count = len(clicked_sessions)

    return {
        "period": period,
        "days": days,
        "total_queries": query_count,
        "total_clicks": click_count,
        "unique_sessions": len({getattr(event, "session_id", None) for event in query_events if getattr(event, "session_id", None)}),
        "unique_users": len({getattr(event, "user_id", None) for event in query_events if getattr(event, "user_id", None)}),
        "product_search_queries": top_intents.get("product_search", 0),
        "avg_results_per_query": round(sum(int(cast(Any, getattr(event, "result_count", 0)) or 0) for event in query_events) / query_count, 2) if query_count else 0.0,
        "click_through_rate": round((clicked_session_count / query_count) * 100, 1) if query_count else 0.0,
        "top_queries": [{"query": query, "count": count} for query, count in top_queries.most_common(10)],
        "top_intents": [{"intent": intent, "count": count} for intent, count in top_intents.most_common(8)],
        "top_filters": {
            "categories": [{"value": value, "count": count} for value, count in top_categories.most_common(8)],
            "brands": [{"value": value, "count": count} for value, count in top_brands.most_common(8)],
            "colors": [{"value": value, "count": count} for value, count in top_colors.most_common(8)],
            "sizes": [{"value": value, "count": count} for value, count in top_sizes.most_common(8)],
        },
        "behavior_summary": {
            "budget_focused_queries": budget_focused,
            "quality_focused_queries": quality_focused,
            "brand_specific_queries": brand_specific,
        },
        "top_clicked_products": [
            {"id": row.id, "name": row.name, "clicks": int(row.clicks or 0)}
            for row in top_clicked_rows
        ],
        "no_result_queries": [{"query": query, "count": count} for query, count in no_result_queries.most_common(10)],
        "daily_data": sorted(daily_data.values(), key=lambda item: item["date"]),
    }


# â”€â”€ Admin: Recipient Bank Account Verification â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_ALLOWED_BANK_ACCOUNT_KINDS = {"supplier", "logistics_partner"}


def _require_admin(current_user: dict) -> None:
    role = current_user["role"]
    if role not in {"admin", "sub_admin"}:
        raise HTTPException(status_code=403, detail="Admin access required.")


def list_pending_bank_accounts(kind: str, db: Session, current_user: dict) -> list[dict]:
    """List bank accounts awaiting verification for a given kind (supplier|logistics_partner)."""
    _require_admin(current_user)
    if kind not in _ALLOWED_BANK_ACCOUNT_KINDS:
        raise HTTPException(status_code=400, detail=f"kind must be one of {list(_ALLOWED_BANK_ACCOUNT_KINDS)}")

    if kind == "supplier":
        rows = (
            db.query(SupplierBankAccount, User.username, SupplierProfile.business_name)
            .join(User, SupplierBankAccount.supplier_id == User.id)
            .outerjoin(SupplierProfile, SupplierProfile.user_id == User.id)
            .filter(SupplierBankAccount.verification_status == "pending")
            .order_by(SupplierBankAccount.created_at.asc())
            .all()
        )
        return [
            {
                "id": r.id,
                "supplier_id": r.supplier_id,
                "entity_name": business_name or username or str(r.supplier_id),
                "beneficiary_name": r.beneficiary_name,
                "bank_name": r.bank_name,
                "branch_name": r.branch_name,
                "account_number": r.account_number,
                "iban": r.iban,
                "swift_code": r.swift_code,
                "routing_number": r.routing_number,
                "currency": r.currency,
                "bank_country": r.bank_country,
                "verification_status": r.verification_status,
                "provider": r.provider,
                "provider_recipient_id": r.provider_recipient_id,
                "provider_status": r.provider_status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r, username, business_name in rows
        ]
    else:
        rows = (
            db.query(LogisticsPartnerBankAccount, LogisticsPartner.name)
            .join(LogisticsPartner, LogisticsPartnerBankAccount.partner_id == LogisticsPartner.id)
            .filter(LogisticsPartnerBankAccount.verification_status == "pending")
            .order_by(LogisticsPartnerBankAccount.created_at.asc())
            .all()
        )
        return [
            {
                "id": r.id,
                "partner_id": r.partner_id,
                "entity_name": partner_name or str(r.partner_id),
                "beneficiary_name": r.beneficiary_name,
                "bank_name": r.bank_name,
                "branch_name": r.branch_name,
                "account_number": r.account_number,
                "iban": r.iban,
                "swift_code": r.swift_code,
                "routing_number": r.routing_number,
                "currency": r.currency,
                "bank_country": r.bank_country,
                "verification_status": r.verification_status,
                "provider": r.provider,
                "provider_recipient_id": r.provider_recipient_id,
                "provider_status": r.provider_status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r, partner_name in rows
        ]


def verify_bank_account(
    kind: str,
    account_id: int,
    action: str,
    note: Optional[str],
    current_user: dict,
    db: Session,
) -> dict:
    """Approve or reject a supplier or logistics partner bank account."""
    _require_admin(current_user)
    if kind not in _ALLOWED_BANK_ACCOUNT_KINDS:
        raise HTTPException(status_code=400, detail=f"kind must be one of {list(_ALLOWED_BANK_ACCOUNT_KINDS)}")
    if action not in {"approve", "reject"}:
        raise HTTPException(status_code=400, detail="action must be approve or reject")

    if kind == "supplier":
        record = db.query(SupplierBankAccount).filter(SupplierBankAccount.id == account_id).first()
    else:
        record = db.query(LogisticsPartnerBankAccount).filter(LogisticsPartnerBankAccount.id == account_id).first()

    if record is None:
        raise HTTPException(status_code=404, detail="Bank account record not found.")

    new_status = "verified" if action == "approve" else "rejected"
    setattr(record, "verification_status", new_status)
    setattr(record, "verification_note", note or ("Approved." if action == "approve" else "Rejected by admin."))
    if action == "reject":
        setattr(record, "provider", None)
        setattr(record, "provider_recipient_id", None)
        setattr(record, "provider_status", None)
        setattr(record, "provider_last_synced_at", None)
    setattr(record, "verified_at", datetime.now(timezone.utc))
    setattr(record, "verified_by", int(current_user["id"]))
    db.commit()

    audit_log(
        db,
        user_id=int(current_user["id"]),
        username=current_user["username"],
        user_role=current_user["role"],
        action=f"BANK_ACCOUNT_{action.upper()}",
        resource_type=f"{kind}_bank_account",
        resource_id=account_id,
        details={"status": new_status, "note": note},
    )
    return {
        "ok": True,
        "id": account_id,
        "verification_status": new_status,
        "verification_note": note or ("Approved." if action == "approve" else "Rejected by admin."),
    }


def delete_bank_account_record(
    kind: str,
    account_id: int,
    current_user: dict,
    db: Session,
) -> dict:
    """Delete a supplier or logistics partner bank account record."""
    _require_admin(current_user)
    if kind not in _ALLOWED_BANK_ACCOUNT_KINDS:
        raise HTTPException(status_code=400, detail=f"kind must be one of {list(_ALLOWED_BANK_ACCOUNT_KINDS)}")

    if kind == "supplier":
        record = db.query(SupplierBankAccount).filter(SupplierBankAccount.id == account_id).first()
    else:
        record = db.query(LogisticsPartnerBankAccount).filter(LogisticsPartnerBankAccount.id == account_id).first()

    if record is None:
        raise HTTPException(status_code=404, detail="Bank account record not found.")

    verification_status = cast(str | None, getattr(record, "verification_status", None))
    db.delete(record)
    db.commit()

    audit_log(
        db,
        user_id=int(current_user["id"]),
        username=current_user["username"],
        user_role=current_user["role"],
        action="BANK_ACCOUNT_DELETE",
        resource_type=f"{kind}_bank_account",
        resource_id=account_id,
        details={"status": verification_status},
    )
    return {"ok": True, "id": account_id, "deleted": True}

