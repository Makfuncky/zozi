"""Admin user-management operations (security / identity surface).

These are privileged, admin-only operations (hard-delete, bulk-delete,
force password reset). They live in the security bounded context rather than
the customer surface so the customer domain stays free of admin-only tokens.

Implementation helper: these functions are reached through the decorated routes
in ``controllers.admin.users_admin_controller`` (``delete_user_route``,
``force_reset_password_route``) and the hand-written ``admin_identity_operations``
router, so they are intentionally NOT decorated with their own HTTP contract.
"""
from __future__ import annotations

from core.route_contract import delete, post

from typing import List, cast

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from domains.media.services.db_read import all_rows, first

from models import Order, OrderItem, User

from modules.customer.routers.users import (
    _build_user_delete_blocker,
    _delete_order_records,
    _hard_delete_user_record,
    audit_log,
    AuditAction,
    force_reset_password_service,
    get_password_hash,
    logger,
)

@delete("/api/v1/admin/py/user_admin", skip=True)
def delete_user_admin(user_id: int, current_user: dict, db: Session, delete_orders: bool = False) -> dict:
    """Hard-delete a user and their non-order data. Blocked if user has orders."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete users")

    user = first(db, User, [User.id == user_id])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_orders = all_rows(
        db,
        Order,
        [Order.user_id == user_id],
        options=[
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.shipments),
        ],
        order_by=[Order.created_at.desc()],
    )

    blocker = _build_user_delete_blocker(
        user,
        current_user,
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
    except IntegrityError as e:
        logger.warning("admin delete blocked by remaining related records", extra={"user_id": user_id, "error": str(e)})
        raise HTTPException(
            status_code=409,
            detail="User has related records that must be archived or removed before deletion.",
        )
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("admin delete user failed", extra={"user_id": user_id, "error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to remove user: {str(e)}")

    audit_log(
        db=db,
        action=AuditAction.USER_DELETE,
        user_id=current_user["id"],
        username=current_user.get("username"),
        user_role=current_user.get("role"),
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

@post("/api/v1/admin/py/delete_users_admin", skip=True)
def bulk_delete_users_admin(user_ids: List[int], current_user: dict, db: Session) -> dict:
    """Bulk hard-delete multiple users. Admin-only. Skips protected/order-holding accounts."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete users")

    if not user_ids:
        raise HTTPException(status_code=400, detail="No user IDs provided")
    if len(user_ids) > 100:
        raise HTTPException(status_code=400, detail="Cannot delete more than 100 users at once")

    deleted: List[dict] = []
    skipped: List[dict] = []

    for uid in user_ids:
        if uid == current_user["id"]:
            skipped.append({"id": uid, "reason": "Cannot delete own account"})
            continue

        user = first(db, User, [User.id == uid])
        if not user:
            skipped.append({"id": uid, "reason": "Not found"})
            continue

        blocker = _build_user_delete_blocker(user, current_user, db, delete_orders=False)
        if blocker is not None:
            skipped.append({"id": uid, "reason": blocker[1]})
            continue

        username = cast(str, getattr(user, "username"))
        try:
            _hard_delete_user_record(user, db)
            deleted.append({"id": uid, "username": username})
        except IntegrityError as e:
            logger.exception("bulk_delete_users_admin_failed", error=str(e))
            skipped.append(
                {
                    "id": uid,
                    "reason": "Has related records that must be archived or removed before deletion",
                }
            )

    if deleted:
        audit_log(
            db=db,
            action=AuditAction.USER_DELETE,
            user_id=current_user["id"],
            username=current_user.get("username"),
            user_role=current_user.get("role"),
            resource_type="user",
            resource_id=0,
            details={"bulk": True, "deleted_count": len(deleted), "deleted_users": deleted},
            status="success",
        )
    else:
        pass

    return {
        "deleted": len(deleted),
        "skipped": len(skipped),
        "details": deleted,
        "skipped_details": skipped,
    }

@post("/api/v1/admin/py/force_reset_password_admin", skip=True)
def force_reset_password_admin(user_id: int, new_password: str, current_user: dict, db: Session) -> dict:
    """Force-set any user's password without requiring the old one (admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can force-reset passwords")

    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")

    user = first(db, User, [User.id == user_id])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if cast(str, getattr(user, "role")) == "admin" and user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Cannot reset another admin's password")

    force_reset_password_service(db, user, get_password_hash(new_password))

    audit_log(
        db=db,
        action=AuditAction.PASSWORD_FORCE_RESET,
        user_id=current_user["id"],
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="user",
        resource_id=user_id,
        details={"target_username": cast(str, getattr(user, "username"))},
        status="success",
    )
    return {"message": f"Password reset for user '{cast(str, getattr(user, 'username'))}'"}
