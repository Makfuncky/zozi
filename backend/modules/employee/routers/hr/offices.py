"""Office CRUD sub-router — thin delegator to HR employee service (Law 2)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from infrastructure.security.dependencies import get_current_user
from infrastructure.database.database import get_db
from infrastructure.utils.country_rls import enforce_country_access
from domains.hr.services.hr_employee_service import get_hr_employee_service
from rbac.dependencies import require_feature

router = APIRouter()


@router.get("/admin/{code}/offices")
def list_offices(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).list_offices(code, db)


@router.post("/admin/{code}/offices")
def create_office(code: str, body: dict = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).create_office(code, body or {}, db)


@router.put("/admin/{code}/offices/{office_id}")
def update_office(code: str, office_id: int, body: dict = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.update"))
):
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).update_office(office_id, body or {}, db)


@router.delete("/admin/{code}/offices/{office_id}")
def delete_office(code: str, office_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.delete"))
):
    enforce_country_access(code, db=db)
    get_hr_employee_service(db).delete_office(office_id, db)
    return {"message": "Office deleted"}