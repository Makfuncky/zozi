"""
Onboarding Pipeline API

All DB work is delegated to ``services/supplier/supplier_onboarding_service.py``
so this router stays a thin delegator (layering: LC1/W1).
"""
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File

from data.dependencies_auth import get_current_user
from data.services_supplier_onboarding_service import (
    complete_pipeline_step,
    create_kyc_verification_record,
    create_onboarding_pipeline,
    get_onboarding_status_for_user,
    process_pipeline_document,
)

router = APIRouter()


@router.post("/pipelines", response_model=dict)
async def create_pipeline(
    pipeline_type: str = "kyc",
    current_user: dict = Depends(get_current_user),
):
    return create_onboarding_pipeline(current_user, pipeline_type)


@router.post("/pipelines/{pipeline_id}/documents", response_model=dict)
async def upload_document(
    pipeline_id: int,
    document_type: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    content = await file.read()

    return process_pipeline_document(pipeline_id, document_type, content)


@router.post("/kyc", response_model=dict)
async def create_kyc_verification(
    documents: List[dict],
    current_user: dict = Depends(get_current_user),
):
    return create_kyc_verification_record(current_user, documents)


@router.get("/status", response_model=dict)
async def get_onboarding_status(
    current_user: dict = Depends(get_current_user),
):
    return get_onboarding_status_for_user(current_user)


@router.post("/pipelines/{pipeline_id}/steps/{step_name}/complete", response_model=dict)
async def complete_step(
    pipeline_id: int,
    step_name: str,
    current_user: dict = Depends(get_current_user),
):
    return complete_pipeline_step(pipeline_id, step_name)
