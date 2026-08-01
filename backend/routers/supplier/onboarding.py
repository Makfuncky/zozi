"""
Onboarding Pipeline API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from models import OnboardingPipeline, User
from services.onboarding_pipeline import get_onboarding_service, OnboardingPipelineService
from db.database import get_db
from dependencies.auth import get_current_user

router = APIRouter()


@router.post("/pipelines", response_model=dict)
async def create_pipeline(
    pipeline_type: str = "kyc",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == int(current_user["sub"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    service = get_onboarding_service(db)
    pipeline = service.create_pipeline(user.id, pipeline_type)
    
    return {
        "pipeline_id": pipeline.id,
        "type": pipeline.pipeline_type,
        "status": pipeline.status
    }


@router.post("/pipelines/{pipeline_id}/documents", response_model=dict)
async def upload_document(
    pipeline_id: int,
    document_type: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    content = await file.read()
    
    service = get_onboarding_service(db)
    verification = service.process_document(pipeline_id, document_type, content)
    
    return {
        "verification_id": verification.id,
        "document_type": verification.document_type,
        "status": verification.status,
        "ocr_confidence": verification.ocr_result.confidence_score if verification.ocr_result else None
    }


@router.post("/kyc", response_model=dict)
async def create_kyc_verification(
    documents: List[dict],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == int(current_user["sub"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    service = get_onboarding_service(db)
    kyc = service.create_kyc_verification(user.id, documents)
    
    return {
        "kyc_id": kyc.id,
        "status": kyc.status,
        "document_types": kyc.document_types
    }


@router.get("/status", response_model=dict)
async def get_onboarding_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == int(current_user["sub"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    service = get_onboarding_service(db)
    status = service.get_pipeline_status(user.id)
    
    if not status:
        return {"status": "not_started"}
    
    return status


@router.post("/pipelines/{pipeline_id}/steps/{step_name}/complete", response_model=dict)
async def complete_step(
    pipeline_id: int,
    step_name: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_onboarding_service(db)
    step = service.complete_step(pipeline_id, step_name)
    
    return {
        "step": step.step_name,
        "status": step.status,
        "completed_at": step.completed_at.isoformat() if step.completed_at else None
    }
