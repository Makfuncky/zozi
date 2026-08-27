"""Supplier suppliers router — thin wrappers over supplier domain services."""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status, File, UploadFile, Form
from sqlalchemy.orm import Session

from infrastructure.security.dependencies import get_current_user, require_admin, require_supplier
from infrastructure.database.database import get_db
from rbac.dependencies import require_feature

from domains.suppliers.services.health.supplier_health_service import get_supplier_health, list_supplier_health
from domains.suppliers.services.documents.supplier_document_service import list_all_supplier_documents, review_supplier_document
from domains.suppliers.services.orders.supplier_orders_service import get_supplier_profile_by_user_id, list_supplier_orders
from domains.suppliers.services.profile.supplier_profile_service import get_supplier_profile
from domains.suppliers.services.health.supplier_health import update_supplier_profile
from infrastructure.database.schemas import (
    SupplierDocumentOut,
    SupplierProfileOut,
    SupplierProfileCreate,
    SupplierProfileUpdate,
)

router = APIRouter(prefix="/api/v1/supplier/suppliers", tags=["supplier", "suppliers"])


# ── Onboarding ────────────────────────────────────────────────────────────────

@router.post("/pipelines")
async def create_pipeline(
    pipeline_type: str = "kyc",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature("suppliers.onboarding.write")
    from domains.suppliers.services.onboarding.supplier_onboarding_service import create_pipeline as _create_pipeline
    return _create_pipeline(int(current_user["sub"]), pipeline_type, db)


@router.post("/pipelines/{pipeline_id}/documents")
async def upload_document(
    pipeline_id: int,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature("suppliers.onboarding.write")
    from domains.suppliers.services.onboarding.supplier_onboarding_service import upload_document as _upload_document
    content = await file.read()
    return _upload_document(pipeline_id, document_type, content, db)


@router.post("/kyc")
async def create_kyc_verification(
    documents: list[dict] = Body(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature("suppliers.onboarding.write")
    from domains.suppliers.services.onboarding.supplier_onboarding_service import create_kyc_verification as _create_kyc
    return _create_kyc(int(current_user["sub"]), documents, db)


@router.get("/status")
async def get_onboarding_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature("suppliers.onboarding.read")
    from domains.suppliers.services.onboarding.supplier_onboarding_service import get_onboarding_status as _get_status
    return _get_status(int(current_user["sub"]), db)


@router.post("/pipelines/{pipeline_id}/steps/{step_name}/complete")
async def complete_step(
    pipeline_id: int,
    step_name: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature("suppliers.onboarding.write")
    from domains.suppliers.services.onboarding.supplier_onboarding_service import complete_step as _complete_step
    return _complete_step(pipeline_id, step_name, db)


# ── Documents ─────────────────────────────────────────────────────────────────

@router.get("/documents", response_model=list[SupplierDocumentOut])
def list_all_documents(
    status_filter: Optional[str] = Query(None),
    _: Any = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("suppliers.documents.read")
    return list_all_supplier_documents(db, status_filter)


@router.put("/documents/{document_id}/review")
def review_document(
    document_id: int,
    new_status: str = Body(...),
    note: Optional[str] = Body(None),
    admin_user: Any = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("suppliers.documents.write")
    return review_supplier_document(db, document_id, new_status, note, admin_user.id)


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health/suppliers/{supplier_id}")
def get_supplier_health_route(
    supplier_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    country_code: Optional[str] = Query(None),
):
    require_feature("suppliers.health.read")
    return get_supplier_health(supplier_id=supplier_id, country_code=country_code, current_user=current_user, db=db)


@router.get("/health/suppliers")
def list_supplier_health_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    country_code: Optional[str] = Query(None),
):
    require_feature("suppliers.health.read")
    return list_supplier_health(country_code=country_code, current_user=current_user, db=db)


# ── Orders ────────────────────────────────────────────────────────────────────

@router.get("/orders")
def list_supplier_orders_route(
    current_user: Any = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    require_feature("orders.list")
    supplier = get_supplier_profile_by_user_id(db, current_user.id)
    return list_supplier_orders(db, supplier.id)


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get("/profile")
def get_supplier_profile_route(
    current_user: Any = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    require_feature("suppliers.profile.read")
    return get_supplier_profile(db, current_user.id)


@router.post("/profile", response_model=SupplierProfileOut, status_code=201)
def create_supplier_profile_route(
    payload: SupplierProfileCreate,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature("suppliers.profile.write")
    from domains.accounts.ports import create_supplier_profile
    return create_supplier_profile(current_user, payload, db)


@router.put("/profile", response_model=SupplierProfileOut)
def update_supplier_profile_route(
    payload: SupplierProfileUpdate,
    current_user: Any = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    require_feature("suppliers.profile.write")
    profile = update_supplier_profile(payload.dict(), current_user, db)
    if profile is None:
        raise HTTPException(404, "Profile not found")
    return profile
