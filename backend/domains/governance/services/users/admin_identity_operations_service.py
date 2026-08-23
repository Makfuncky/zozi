"""Admin users router."""
from fastapi import Depends, HTTPException, Query, Body, Path
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from infrastructure.database.schemas import UserOut, UserAdminUpdate, ArchiveRequest, BulkActionRequest
from infrastructure.utils.dependencies import require_admin
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context
from infrastructure.utils.pagination import paginated_response
from domains.governance.services.settings.misc_service import archive_entity
from domains.governance.services.settings.misc_service import restore_entity
from domains.catalog.ports import bulk_archive_entities
from domains.catalog.ports import bulk_restore_entities
from domains.governance.services.settings.misc_service import hard_delete_entity
from domains.governance.services.users.users_service_accounts import update_user_role
from domains.governance.services.users.users_service_accounts import toggle_user_active
from domains.governance.services.users.admin_users import force_reset_password_admin
from domains.governance.ports import delete_user_admin

def list_users(country_code: str=Path(..., description='ISO country code'), page: int=Query(1, ge=1), size: int=Query(50), role: str=None, search: str=None, include_deleted: bool=False, _=Depends(require_admin), db: Session=Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(User).filter(User.country_code == country_code.upper())
        if role:
            q = q.filter(User.role == role)
        if search:
            q = q.filter(User.email.ilike(f'%{search}%') | User.full_name.ilike(f'%{search}%'))
        if not include_deleted:
            q = q.filter(User.is_deleted == False)
        return paginated_response(q, page, size)
    finally:
        clear_rls_context()

def update_user(country_code: str=Path(..., description='ISO country code'), user_id: int=Path(...), payload: UserAdminUpdate=None, _: User=Depends(require_admin), db: Session=Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        u = db.query(User).filter(User.id == user_id, User.country_code == country_code.upper()).first()
        if not u:
            raise HTTPException(404)
        for (k, v) in payload.model_dump(exclude_unset=True).items():
            setattr(u, k, v)
        db.commit()
        db.refresh(u)
        return u
    finally:
        clear_rls_context()

def bulk_toggle_user_active(country_code: str=Path(..., description='ISO country code'), payload: dict=Body(...), _: User=Depends(require_admin), db: Session=Depends(get_db), current_user: User=Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        user_ids = payload.get('user_ids', [])
        is_active = payload.get('is_active', True)
        if not user_ids:
            raise HTTPException(400, 'user_ids is required')
        updated = 0
        for uid in user_ids:
            u = db.query(User).filter(User.id == uid, User.country_code == country_code.upper()).first()
            if u:
                u.is_active = is_active
                updated += 1
        db.commit()
        return {'message': f'Updated {updated} users', 'updated': updated}
    finally:
        clear_rls_context()
