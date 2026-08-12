"""Generated re-export shim.



This module was missing after a refactor that relocated handlers into

subpackage service modules. It re-exports the symbols from their

canonical locations so legacy imports (e.g. `from services.common.misc_write_service import ...`)

keep resolving. Prefer importing from the canonical module directly

in new code.

"""

from __future__ import annotations



import structlog

from typing import Optional



from sqlalchemy.orm import Session



from models import Banner, RolePermissionSetting, SupplierDispute

from db.seed import _ensure_demo_user, _seed_password

from services.treasury.cash_write_service import (

    create_cash_account,

    create_cash_transaction,

)

from utils.config import settings

from utils.soft_delete import (

    _has_soft_delete as has_soft_delete,

    _now as _soft_now,

    hard_delete as _soft_delete_hard_delete,

    restore as _soft_delete_restore,

    soft_delete as _soft_delete_soft_delete,

)



logger = structlog.get_logger(__name__)





def soft_delete_record(db, record, acting_user, reason=None):

    """Delegate generic soft-delete to the canonical ``utils.soft_delete`` impl."""

    _soft_delete_soft_delete(db, type(record), record.id, acting_user, reason)





def restore_record(db, record, acting_user):

    """Delegate generic restore to the canonical ``utils.soft_delete`` impl."""

    _soft_delete_restore(db, type(record), record.id, acting_user)





def hard_delete_record(db, record, acting_user, reason=None):

    """Delegate generic hard-delete to the canonical ``utils.soft_delete`` impl."""

    _soft_delete_hard_delete(db, type(record), record.id, acting_user, reason)





def reset_demo_data(db: Session, *, country_code: Optional[str] = None) -> dict:

    """Reset demo data for ``country_code`` and re-seed the three demo users.



    Soft-deletable demo tables are soft-deleted (not hard-dropped) and the demo

    admin/supplier/customer accounts are ensured to exist. Each step is guarded so

    a missing table never aborts the whole reset.

    """

    if str(getattr(settings, "app_env", "")).strip().lower() == "production":

        raise RuntimeError(

            "reset_demo_data is disabled in production; it seeds hardcoded demo accounts."

        )



    deleted: dict = {}



    def _safe_clear(Model, label):

        try:

            rows = db.query(Model)

            if country_code is not None and hasattr(Model, "country_code"):

                rows = rows.filter(Model.country_code == country_code)

            count = rows.count()

            if count and _has_soft_delete(Model):

                rows.update(

                    {Model.is_deleted: True, Model.deleted_at: _soft_now()},

                    synchronize_session=False,

                )

            elif count:

                rows.delete(synchronize_session=False)

            db.commit()

            deleted[label] = count

        except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:  # pragma: no cover - defensive

            db.rollback()

            logger.warning("reset_demo_data_clear_failed", label=label, error=str(exc))

            deleted[label] = "error"



    _safe_clear(Banner, "banners")

    _safe_clear(SupplierDispute, "supplier_disputes")

    _safe_clear(RolePermissionSetting, "role_permission_settings")



    reseeded = 0

    try:

        _ensure_demo_user(db, email="admin@zozi.om", username="admin", password=_seed_password("SEED_ADMIN_PASSWORD"), role="admin", log_label="admin")

        _ensure_demo_user(db, email="supplier@zozi.om", username="supplier", password=_seed_password("SEED_SUPPLIER_PASSWORD"), role="supplier", log_label="supplier")

        _ensure_demo_user(db, email="customer@zozi.om", username="customer", password=_seed_password("SEED_CUSTOMER_PASSWORD"), role="customer", log_label="customer")

        reseeded = 3

    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:  # pragma: no cover - defensive

        db.rollback()

        logger.warning("reset_demo_data_reseed_failed", error=str(exc))



    return {"deleted": deleted, "reseeded": reseeded}



