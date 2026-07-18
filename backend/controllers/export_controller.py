"""
Admin Data Export Controller.

Streams CSV data for admin download.  All PII fields (phone, address) are
redacted as ``[ENCRYPTED]`` so exported CSVs are safe for analysis without
revealing raw personal data.

Endpoints are expected to be admin-only and audit-logged by the router.
"""
import csv
import io
import logging
from pathlib import Path
from uuid import uuid4
from typing import Any, Callable, Generator, Iterable

from fastapi import HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from controllers.audit_controller import audit_log, AuditAction
from db.database import SessionLocal
from models import AuditLog, Coupon, Order, Product, User
from services.finance_transfer_service import build_transfer_export_payload
from utils.background_jobs import enqueue_job, get_job
from utils.constants import MAX_EXPORT_ROWS

logger = logging.getLogger(__name__)

_ADMIN_ROLES = {"admin", "superadmin"}
_EXPORTS_DIR = Path(__file__).resolve().parents[2] / "artifacts" / "exports"


def _redacted_if_present(value: Any) -> str:
    return "[ENCRYPTED]" if value is not None else ""


def _to_iso(value: Any) -> str:
    return value.isoformat() if value is not None else ""


def _to_float(value: Any) -> float:
    return float(value) if value is not None else 0.0


def _require_admin(current_user: dict) -> None:
    if current_user.get("role") not in _ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Admin access required")


def _csv_streaming_response(generator: Generator, filename: str) -> StreamingResponse:
    return StreamingResponse(
        generator,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _csv_stream(rows: Iterable[dict], fieldnames: list[str]) -> Generator:
    """Yield a CSV stream (header + data rows) from an iterable of dicts.

    ``rows`` may be a list *or* a lazy generator — when combined with
    ``yield_per`` the memory footprint stays constant regardless of table
    size.
    """
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    yield buf.getvalue()
    buf.seek(0)
    buf.truncate(0)

    for row in rows:
        writer.writerow(row)
        yield buf.getvalue()
        buf.seek(0)
        buf.truncate(0)


def _write_csv_file(rows: list[dict], fieldnames: list[str], filename: str) -> str:
    _EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = _EXPORTS_DIR / filename
    with file_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return str(file_path)


def _iter_rows(db: Session, query, mapper: Callable, batch_size: int = 500) -> Generator[dict, None, None]:
    """Lazily yield mapped dicts from a SQLAlchemy query using ``yield_per``."""
    for obj in query.yield_per(batch_size):
        yield mapper(obj)


# ── Row mappers & fieldnames for streaming exports ────────────────────────────

_USER_FIELDS = [
    "id", "username", "email", "role", "is_active", "email_verified",
    "preferred_language", "preferred_currency", "phone", "created_at", "updated_at",
]

def _map_user(u: User) -> dict:
    return {
        "id": u.id, "username": u.username, "email": u.email, "role": u.role,
        "is_active": u.is_active, "email_verified": u.email_verified,
        "preferred_language": u.preferred_language, "preferred_currency": u.preferred_currency,
        "phone": _redacted_if_present(u.phone),
        "created_at": _to_iso(u.created_at), "updated_at": _to_iso(u.updated_at),
    }

_ORDER_FIELDS = [
    "id", "user_id", "status", "subtotal_amount", "discount_amount",
    "vat_amount", "shipping_amount", "total_amount", "coupon_code",
    "shipping_address", "customer_phone", "tracking_number", "paid_at", "created_at",
]

def _map_order(o: Order) -> dict:
    return {
        "id": o.id, "user_id": o.user_id, "status": o.status,
        "subtotal_amount": _to_float(o.subtotal_amount), "discount_amount": _to_float(o.discount_amount),
        "vat_amount": _to_float(o.vat_amount), "shipping_amount": _to_float(o.shipping_amount),
        "total_amount": _to_float(o.total_amount), "coupon_code": o.coupon_code or "",
        "shipping_address": _redacted_if_present(o.shipping_address),
        "customer_phone": _redacted_if_present(o.customer_phone),
        "tracking_number": o.tracking_number or "", "paid_at": _to_iso(o.paid_at),
        "created_at": _to_iso(o.created_at),
    }

_PRODUCT_FIELDS = [
    "id", "name", "category", "brand", "price", "compare_price", "stock",
    "sales_count", "rating", "supplier_id", "is_active", "is_approved",
    "is_deleted", "tags", "created_at",
]

def _map_product(p: Product) -> dict:
    return {
        "id": p.id, "name": p.name, "category": p.category, "brand": p.brand or "",
        "price": _to_float(p.price),
        "compare_price": _to_float(p.compare_price) if p.compare_price is not None else "",
        "stock": p.stock, "sales_count": p.sales_count, "rating": p.rating,
        "supplier_id": p.supplier_id, "is_active": p.is_active, "is_approved": p.is_approved,
        "is_deleted": p.is_deleted, "tags": p.tags or "", "created_at": _to_iso(p.created_at),
    }

_COUPON_FIELDS = [
    "id", "code", "discount_type", "value", "min_order", "max_uses",
    "uses_count", "is_active", "expires_at", "created_at",
]

def _map_coupon(c: Coupon) -> dict:
    return {
        "id": c.id, "code": c.code, "discount_type": c.discount_type,
        "value": _to_float(c.value), "min_order": _to_float(c.min_order),
        "max_uses": c.max_uses if c.max_uses is not None else "",
        "uses_count": c.uses_count, "is_active": c.is_active,
        "expires_at": _to_iso(c.expires_at), "created_at": _to_iso(c.created_at),
    }

_AUDIT_FIELDS = [
    "id", "user_id", "username", "user_role", "action", "resource_type",
    "resource_id", "status", "ip_address", "occurred_at",
]

def _map_audit_log(lg: AuditLog) -> dict:
    return {
        "id": lg.id, "user_id": lg.user_id if lg.user_id is not None else "",
        "username": lg.username or "", "user_role": lg.user_role or "",
        "action": lg.action, "resource_type": lg.resource_type or "",
        "resource_id": lg.resource_id or "", "status": lg.status,
        "ip_address": lg.ip_address or "", "occurred_at": _to_iso(lg.occurred_at),
    }


def _build_users_export(db: Session) -> tuple[list[dict], list[str], str, dict[str, Any]]:
    users = db.query(User).order_by(User.id).limit(MAX_EXPORT_ROWS).all()
    rows = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "email_verified": u.email_verified,
            "preferred_language": u.preferred_language,
            "preferred_currency": u.preferred_currency,
            "phone": _redacted_if_present(u.phone),
            "created_at": _to_iso(u.created_at),
            "updated_at": _to_iso(u.updated_at),
        }
        for u in users
    ]
    fieldnames = [
        "id", "username", "email", "role", "is_active", "email_verified",
        "preferred_language", "preferred_currency", "phone", "created_at", "updated_at",
    ]
    return rows, fieldnames, "users_export.csv", {"resource_type": "users", "details": {"count": len(rows), "capped": len(rows) >= MAX_EXPORT_ROWS}}


def _build_orders_export(db: Session) -> tuple[list[dict], list[str], str, dict[str, Any]]:
    orders = db.query(Order).order_by(Order.id).limit(MAX_EXPORT_ROWS).all()
    rows = [
        {
            "id": o.id,
            "user_id": o.user_id,
            "status": o.status,
            "subtotal_amount": _to_float(o.subtotal_amount),
            "discount_amount": _to_float(o.discount_amount),
            "vat_amount": _to_float(o.vat_amount),
            "shipping_amount": _to_float(o.shipping_amount),
            "total_amount": _to_float(o.total_amount),
            "coupon_code": o.coupon_code or "",
            "shipping_address": _redacted_if_present(o.shipping_address),
            "customer_phone": _redacted_if_present(o.customer_phone),
            "tracking_number": o.tracking_number or "",
            "paid_at": _to_iso(o.paid_at),
            "created_at": _to_iso(o.created_at),
        }
        for o in orders
    ]
    fieldnames = [
        "id", "user_id", "status", "subtotal_amount", "discount_amount",
        "vat_amount", "shipping_amount", "total_amount", "coupon_code",
        "shipping_address", "customer_phone", "tracking_number", "paid_at", "created_at",
    ]
    return rows, fieldnames, "orders_export.csv", {"resource_type": "orders", "details": {"count": len(rows), "capped": len(rows) >= MAX_EXPORT_ROWS}}


def _build_products_export(db: Session) -> tuple[list[dict], list[str], str, dict[str, Any]]:
    products = db.query(Product).order_by(Product.id).limit(MAX_EXPORT_ROWS).all()
    rows = [
        {
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "brand": p.brand or "",
            "price": _to_float(p.price),
            "compare_price": _to_float(p.compare_price) if p.compare_price is not None else "",
            "stock": p.stock,
            "sales_count": p.sales_count,
            "rating": p.rating,
            "supplier_id": p.supplier_id,
            "is_active": p.is_active,
            "is_approved": p.is_approved,
            "is_deleted": p.is_deleted,
            "tags": p.tags or "",
            "created_at": _to_iso(p.created_at),
        }
        for p in products
    ]
    fieldnames = [
        "id", "name", "category", "brand", "price", "compare_price", "stock",
        "sales_count", "rating", "supplier_id", "is_active", "is_approved",
        "is_deleted", "tags", "created_at",
    ]
    return rows, fieldnames, "products_export.csv", {"resource_type": "products", "details": {"count": len(rows), "capped": len(rows) >= MAX_EXPORT_ROWS}}


def _build_coupons_export(db: Session) -> tuple[list[dict], list[str], str, dict[str, Any]]:
    coupons = db.query(Coupon).order_by(Coupon.id).limit(MAX_EXPORT_ROWS).all()
    rows = [
        {
            "id": c.id,
            "code": c.code,
            "discount_type": c.discount_type,
            "value": _to_float(c.value),
            "min_order": _to_float(c.min_order),
            "max_uses": c.max_uses if c.max_uses is not None else "",
            "uses_count": c.uses_count,
            "is_active": c.is_active,
            "expires_at": _to_iso(c.expires_at),
            "created_at": _to_iso(c.created_at),
        }
        for c in coupons
    ]
    fieldnames = [
        "id", "code", "discount_type", "value", "min_order", "max_uses",
        "uses_count", "is_active", "expires_at", "created_at",
    ]
    return rows, fieldnames, "coupons_export.csv", {"resource_type": "coupons", "details": {"count": len(rows), "capped": len(rows) >= MAX_EXPORT_ROWS}}


def _build_audit_logs_export(db: Session, days: int) -> tuple[list[dict], list[str], str, dict[str, Any]]:
    if days < 1 or days > 365:
        raise HTTPException(status_code=422, detail="days must be between 1 and 365")

    from utils.datetime_utils import utcnow
    from datetime import timedelta

    since = utcnow() - timedelta(days=days)
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.occurred_at >= since)
        .order_by(AuditLog.id)
        .all()
    )
    rows = [
        {
            "id": lg.id,
            "user_id": lg.user_id if lg.user_id is not None else "",
            "username": lg.username or "",
            "user_role": lg.user_role or "",
            "action": lg.action,
            "resource_type": lg.resource_type or "",
            "resource_id": lg.resource_id or "",
            "status": lg.status,
            "ip_address": lg.ip_address or "",
            "occurred_at": _to_iso(lg.occurred_at),
        }
        for lg in logs
    ]
    fieldnames = [
        "id", "user_id", "username", "user_role", "action", "resource_type",
        "resource_id", "status", "ip_address", "occurred_at",
    ]
    return rows, fieldnames, f"audit_logs_{days}d_export.csv", {
        "resource_type": "audit_logs",
        "details": {"count": len(rows), "days": days},
    }


def _build_export_payload(
    export_type: str,
    db: Session,
    days: int = 30,
    provider: str = "manual_csv",
) -> tuple[list[dict], list[str], str, dict[str, Any]]:
    if export_type == "users":
        return _build_users_export(db)
    if export_type == "orders":
        return _build_orders_export(db)
    if export_type == "products":
        return _build_products_export(db)
    if export_type == "coupons":
        return _build_coupons_export(db)
    if export_type == "audit-logs":
        return _build_audit_logs_export(db, days)
    if export_type in {"supplier-payout-transfers", "logistics-payout-transfers", "cod-remittance-transfers"}:
        return build_transfer_export_payload(export_type, db=db, provider=provider)
    raise HTTPException(status_code=404, detail="Unknown export type")


# ── Export functions ──────────────────────────────────────────────────────────

def export_users_csv(current_user: dict, db: Session) -> StreamingResponse:
    _require_admin(current_user)
    count = db.query(func.count(User.id)).scalar()
    audit_log(
        db=db,
        action=AuditAction.DATA_EXPORTED,
        user_id=current_user["id"],
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="users",
        details={"count": count},
    )
    query = db.query(User).order_by(User.id)
    return _csv_streaming_response(
        _csv_stream(_iter_rows(db, query, _map_user), _USER_FIELDS),
        "users_export.csv",
    )


def export_orders_csv(current_user: dict, db: Session) -> StreamingResponse:
    _require_admin(current_user)
    count = db.query(func.count(Order.id)).scalar()
    audit_log(
        db=db,
        action=AuditAction.DATA_EXPORTED,
        user_id=current_user["id"],
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="orders",
        details={"count": count},
    )
    query = db.query(Order).order_by(Order.id)
    return _csv_streaming_response(
        _csv_stream(_iter_rows(db, query, _map_order), _ORDER_FIELDS),
        "orders_export.csv",
    )


def export_products_csv(current_user: dict, db: Session) -> StreamingResponse:
    _require_admin(current_user)
    count = db.query(func.count(Product.id)).scalar()
    audit_log(
        db=db,
        action=AuditAction.DATA_EXPORTED,
        user_id=current_user["id"],
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="products",
        details={"count": count},
    )
    query = db.query(Product).order_by(Product.id)
    return _csv_streaming_response(
        _csv_stream(_iter_rows(db, query, _map_product), _PRODUCT_FIELDS),
        "products_export.csv",
    )


def export_coupons_csv(current_user: dict, db: Session) -> StreamingResponse:
    _require_admin(current_user)
    count = db.query(func.count(Coupon.id)).scalar()
    audit_log(
        db=db,
        action=AuditAction.DATA_EXPORTED,
        user_id=current_user["id"],
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="coupons",
        details={"count": count},
    )
    query = db.query(Coupon).order_by(Coupon.id)
    return _csv_streaming_response(
        _csv_stream(_iter_rows(db, query, _map_coupon), _COUPON_FIELDS),
        "coupons_export.csv",
    )


def export_audit_logs_csv(current_user: dict, db: Session, days: int = 30) -> StreamingResponse:
    _require_admin(current_user)
    if days < 1 or days > 365:
        raise HTTPException(status_code=422, detail="days must be between 1 and 365")
    from utils.datetime_utils import utcnow
    from datetime import timedelta
    since = utcnow() - timedelta(days=days)
    count = db.query(func.count(AuditLog.id)).filter(AuditLog.occurred_at >= since).scalar()
    audit_log(
        db=db,
        action=AuditAction.DATA_EXPORTED,
        user_id=current_user["id"],
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="audit_logs",
        details={"count": count, "days": days},
    )
    query = db.query(AuditLog).filter(AuditLog.occurred_at >= since).order_by(AuditLog.id)
    return _csv_streaming_response(
        _csv_stream(_iter_rows(db, query, _map_audit_log), _AUDIT_FIELDS),
        f"audit_logs_{days}d_export.csv",
    )


def export_transfer_csv(
    export_type: str,
    current_user: dict,
    db: Session,
    *,
    provider: str = "manual_csv",
) -> StreamingResponse:
    _require_admin(current_user)
    rows, fieldnames, filename, audit_meta = _build_export_payload(export_type, db, provider=provider)
    audit_log(
        db=db,
        action=AuditAction.DATA_EXPORTED,
        user_id=current_user["id"],
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type=audit_meta["resource_type"],
        details={**audit_meta["details"], "filename": filename, "background": False},
    )
    return _csv_streaming_response(_csv_stream(rows, fieldnames), filename)


def _run_export_job(export_type: str, current_user: dict, days: int = 30, provider: str = "manual_csv") -> dict:
    db = SessionLocal()
    try:
        _require_admin(current_user)
        rows, fieldnames, filename, audit_meta = _build_export_payload(export_type, db, days=days, provider=provider)
        stored_filename = f"{Path(filename).stem}_{uuid4().hex[:8]}.csv"
        file_path = _write_csv_file(rows, fieldnames, stored_filename)

        audit_log(
            db=db,
            action=AuditAction.DATA_EXPORTED,
            user_id=current_user["id"],
            username=current_user.get("username"),
            user_role=current_user.get("role"),
            resource_type=audit_meta["resource_type"],
            details={**audit_meta["details"], "filename": stored_filename, "background": True},
        )

        return {
            "export_type": export_type,
            "provider": provider,
            "filename": stored_filename,
            "file_path": file_path,
            "rows": len(rows),
        }
    finally:
        db.close()


def queue_export_job(export_type: str, current_user: dict, days: int = 30, provider: str = "manual_csv") -> dict:
    _require_admin(current_user)
    return enqueue_job(
        kind="admin-export",
        owner_user_id=current_user.get("id"),
        owner_role=current_user.get("role"),
        metadata={"export_type": export_type, "days": days, "provider": provider},
        func=lambda: _run_export_job(export_type, current_user, days, provider),
    )


def download_export_job_result(job_id: str, current_user: dict) -> FileResponse:
    _require_admin(current_user)
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("status") != "completed":
        raise HTTPException(status_code=409, detail="Export job is not finished yet")
    result = job.get("result") or {}
    file_path = result.get("file_path")
    filename = result.get("filename")
    if not file_path or not filename or not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="Export artifact not found")
    return FileResponse(file_path, media_type="text/csv", filename=filename)

