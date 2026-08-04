"""Misc write service — DB write operations for admin misc utilities."""
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def soft_delete_record(db: Session, record: object, reason: Optional[str] = None) -> object:
    if hasattr(record, "is_deleted"):
        setattr(record, "is_deleted", True)
    if hasattr(record, "deleted_at"):
        setattr(record, "deleted_at", datetime.now())
    if hasattr(record, "deleted_reason"):
        setattr(record, "deleted_reason", reason)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def restore_record(db: Session, record: object) -> object:
    if hasattr(record, "is_deleted"):
        setattr(record, "is_deleted", False)
    if hasattr(record, "deleted_at"):
        setattr(record, "deleted_at", None)
    if hasattr(record, "deleted_reason"):
        setattr(record, "deleted_reason", None)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def hard_delete_record(db: Session, record: object) -> None:
    db.delete(record)
    db.commit()


def reset_demo_data(db: Session) -> dict[str, int]:
    tables_to_clear = [
        "entity_chat_messages",
        "entity_chat_threads",
        "group_chat_messages",
        "group_chat_members",
        "group_chat_rooms",
        "direct_chat_messages",
        "direct_chat_rooms",
        "internal_emails",
        "email_folders",
        "order_items",
        "orders",
        "reviews",
        "order_logistics_allocations",
        "shipments",
        "wishlist_items",
        "cart_items",
        "coupon_usages",
        "coupons",
        "promotion_ledger_entries",
        "promotion_order_tiers",
        "product_variants",
        "products",
        "categories",
        "audit_logs",
        "notifications",
    ]
    _ALLOWED_TABLES = set(tables_to_clear)
    deleted_counts: dict[str, int] = {}
    for table in tables_to_clear:
        if table not in _ALLOWED_TABLES:
            continue
        try:
            delete_stmt = text("DELETE FROM " + table)
            result = db.execute(delete_stmt)
            deleted_counts[table] = result.rowcount or 0
        except Exception:
            deleted_counts[table] = -1

    deleted_counts["users_(non_admin)"] = 0
    db.execute(text("DELETE FROM users WHERE role != 'admin'"))

    try:
        db.execute(text("DELETE FROM sqlite_sequence"))
    except Exception:
        pass

    db.commit()

    total = sum(v for v in deleted_counts.values() if v >= 0)
    return {
        "detail": "Demo data reset complete",
        "tables_cleared": len(tables_to_clear) + 1,
        "total_rows_deleted": total,
        "counts": deleted_counts,
        "note": "Admin accounts preserved. Run seed_all.py to re-seed.",
    }


