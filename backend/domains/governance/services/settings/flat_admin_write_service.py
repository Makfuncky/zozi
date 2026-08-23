"""Admin write service — miscellaneous privileged data operations.

Owns destructive admin-only transactions (e.g. demo-data reset) so the routers
never call ``db.execute`` / ``db.commit`` directly (audit rule W1).
"""
from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import text
from sqlalchemy.orm import Session


def reset_demo_data(db: Session) -> Dict[str, Any]:
    """Clear all non-essential seed data, preserving admin accounts.

    Behaviour-preserving extraction of the inline body of
    ``routers.admin_logistics_operations.admin_reset_demo_data``: child tables are
    deleted first (FK order), non-admin users are removed, sqlite sequences are
    reset, and the transaction commits once. Returns the same counts payload.
    """
    # Tables ordered with children first to respect FK constraints
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
    deleted_counts: Dict[str, int] = {}
    for table in tables_to_clear:
        try:
            result = db.execute(text(f"DELETE FROM {table}"))
            deleted_counts[table] = result.rowcount or 0
        except Exception:
            # Table may not exist in this schema version
            deleted_counts[table] = -1

    # Delete all non-admin users (preserve admin accounts)
    non_admin_count = db.execute(
        text("DELETE FROM users WHERE role != 'admin'")
    ).rowcount or 0
    deleted_counts["users_(non_admin)"] = non_admin_count

    # Reset auto-increment sequences where possible
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
