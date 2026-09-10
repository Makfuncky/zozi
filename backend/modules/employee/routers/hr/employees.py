"""Employee lifecycle sub-router — thin delegators to HR services (Law 2)."""
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from infrastructure.security.dependencies import get_current_user
from infrastructure.database.database import get_db
from infrastructure.utils.country_rls import enforce_country_access
from domains.hr.services.hr_employee_service import get_hr_employee_service
from rbac.dependencies import require_feature

router = APIRouter()


@router.get("/admin/{code}/employees")
def list_employees(
    code: str, department: Optional[str] = Query(None),
    status: Optional[str] = Query(None, alias="employment_status"),
    q: Optional[str] = Query(None), limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.delete")),
    _feature_gate: None = Depends(require_feature("hr.update")),
    _perm_gate: None = Depends(require_feature("hr.create")),
    _gate: None = Depends(require_feature("hr.read")),
):
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).list_employees(code, db, department=department, status=status, query=q, limit=limit)


@router.post("/admin/{code}/employees")
def create_employee(code: str, body: dict = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).create_employee(code, body or {}, current_user, db)


@router.get("/employees/{employee_id}")
def get_employee(employee_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return get_hr_employee_service(db).get_employee(employee_id, db)


@router.patch("/admin/{code}/employees/{employee_id}")
def update_employee(code: str, employee_id: int, body: dict = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.update"))
):
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).update_employee(employee_id, body or {}, current_user, db)


@router.delete("/admin/{code}/employees/{employee_id}")
def delete_employee(code: str, employee_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.delete"))
):
    enforce_country_access(code, db=db)
    get_hr_employee_service(db).delete_employee(employee_id, current_user, db)
    return {"message": "Employee deleted"}


@router.get("/admin/{code}/employees/{employee_id}/documents")
def list_employee_documents(code: str, employee_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).list_employee_documents(employee_id, db)


@router.post("/admin/{code}/employees/{employee_id}/documents")
def create_employee_document(code: str, employee_id: int, body: dict = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).create_employee_document(employee_id, body or {}, db)


@router.patch("/admin/{code}/employees/documents/{doc_id}")
def update_employee_document_status(code: str, doc_id: int, body: dict = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.update"))
):
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).update_employee_document_status(doc_id, body or {}, db)


@router.get("/employees/{employee_id}/addresses")
def list_employee_addresses(
    employee_id: int = Path(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.read")),
):
    return get_hr_employee_service(db).list_employee_addresses(employee_id)


@router.get("/employees/{employee_id}/dependents")
def list_employee_dependents(
    employee_id: int = Path(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.read")),
):
    return get_hr_employee_service(db).list_employee_dependents(employee_id)


@router.post("/admin/{code}/employees/{employee_id}/kill-switch")
def kill_switch_employee(employee_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    return get_hr_employee_service(db).kill_switch(employee_id, current_user, db)


@router.get("/admin/{code}/employee-roles")
def list_employee_roles(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).list_employee_roles(code, db)


@router.post("/admin/{code}/employee-roles")
def create_employee_role(code: str, body: dict = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).create_employee_role(code, body or {}, db)


@router.get("/public")
def list_employees_public(db: Session = Depends(get_db)):
    from fastapi import HTTPException
    try:
        return get_hr_employee_service(db).list_employees_public()
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")