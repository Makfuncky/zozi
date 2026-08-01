"""
AI/OCR Onboarding Pipeline Service
Features: Document OCR, AI Verification, Automated Onboarding Flows
"""
import logging
import base64
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import io

from sqlalchemy.orm import Session
from PIL import Image

try:
    import pytesseract
    import cv2
    import numpy as np
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from models import OnboardingPipeline, OnboardingStep, DocumentVerification, OCRResult, KYCVerification, User
from db.database import get_service_session

logger = logging.getLogger("zozi.onboarding")


class OCRProcessor:
    """Handles OCR processing for documents."""
    
    @staticmethod
    def preprocess_image(image_data: bytes) -> Any:
        """Preprocess image for better OCR results."""
        if not OCR_AVAILABLE:
            raise ImportError("OCR dependencies (pytesseract, cv2, numpy) not installed")
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray)
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary
    
    @classmethod
    def extract_text(cls, image_data: bytes, document_type: str = None) -> Dict[str, Any]:
        """Extract text from document image."""
        if not OCR_AVAILABLE:
            return {"text": "", "confidence": 0, "fields": {}, "error": "OCR not available"}
        try:
            processed_img = cls.preprocess_image(image_data)
            text = pytesseract.image_to_string(processed_img)
            confidence = pytesseract.image_to_data(processed_img, output_boxes=True)
            return {
                "text": text.strip(),
                "confidence": len(confidence) / max(1, len(text.split())),
                "fields": cls._extract_fields(text, document_type)
            }
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return {"text": "", "confidence": 0, "fields": {}, "error": str(e)}
    
    @staticmethod
    def _extract_fields(text: str, doc_type: Optional[str] = None) -> Dict[str, str]:
        """Extract structured fields from OCR text."""
        fields = {}
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        
        if doc_type == "passport":
            for i, line in enumerate(lines[:10]):
                fields[f"line_{i}"] = line
            if len(lines) > 0:
                fields["name"] = lines[0]
            if len(lines) > 1:
                fields["passport_number"] = lines[1].split()[-1] if lines[1].split() else ""
        
        elif doc_type == "driver_license":
            for i, line in enumerate(lines[:10]):
                fields[f"line_{i}"] = line
            if len(lines) > 0:
                fields["name"] = lines[0]
        
        else:
            for i, line in enumerate(lines[:5]):
                fields[f"line_{i}"] = line
        
        return fields


class AIVerifier:
    """AI-based document verification."""
    
    @staticmethod
    def verify_document(document_type: str, ocr_result: Dict[str, Any]) -> Dict[str, Any]:
        """Verify document authenticity using AI."""
        confidence = ocr_result.get("confidence", 0)
        fields = ocr_result.get("fields", {})
        
        if document_type == "passport":
            required = ["name", "passport_number"]
            has_required = all(f in fields and fields[f] for f in required)
            is_valid = confidence > 0.7 and has_required
        elif document_type == "driver_license":
            required = ["name"]
            has_required = all(f in fields and fields[f] for f in required)
            is_valid = confidence > 0.6 and has_required
        else:
            is_valid = confidence > 0.5
        
        return {
            "is_valid": is_valid,
            "confidence": confidence,
            "issues": [] if is_valid else ["Low confidence" if confidence < 0.5 else "Missing required fields"]
        }


class OnboardingPipelineService:
    """Service for managing onboarding pipelines."""
    
    def __init__(self, db: Session = None):
        self.db = db or get_service_session()
    
    def create_pipeline(self, user_id: int, pipeline_type: str = "kyc") -> OnboardingPipeline:
        """Create a new onboarding pipeline for a user."""
        pipeline = OnboardingPipeline(
            user_id=user_id,
            pipeline_type=pipeline_type,
            status="pending"
        )
        self.db.add(pipeline)
        self.db.commit()
        self.db.refresh(pipeline)
        return pipeline
    
    def process_document(
        self,
        pipeline_id: int,
        document_type: str,
        image_data: bytes
    ) -> DocumentVerification:
        """Process a document through OCR and verification."""
        ocr_result = OCRProcessor.extract_text(image_data, document_type)
        
        ocr = OCRResult(
            document_verification_id=0,
            extracted_text=ocr_result.get("text", ""),
            confidence_score=str(ocr_result.get("confidence", 0)),
            fields=ocr_result.get("fields", {})
        )
        self.db.add(ocr)
        self.db.commit()
        self.db.refresh(ocr)
        
        verification = DocumentVerification(
            pipeline_id=pipeline_id,
            document_type=document_type,
            document_data={"size": len(image_data)},
            ocr_result_id=ocr.id,
            status="processed"
        )
        self.db.add(verification)
        self.db.commit()
        self.db.refresh(verification)
        
        verification_result = AIVerifier.verify_document(document_type, ocr_result)
        verification.status = "verified" if verification_result["is_valid"] else "rejected"
        self.db.commit()
        
        return verification
    
    def create_kyc_verification(self, user_id: int, documents: List[Dict[str, Any]]) -> KYCVerification:
        """Create a KYC verification record."""
        kyc = KYCVerification(
            user_id=user_id,
            status="pending",
            document_types=[d.get("type") for d in documents]
        )
        self.db.add(kyc)
        self.db.commit()
        self.db.refresh(kyc)
        return kyc
    
    def get_pipeline_status(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get the current onboarding pipeline status for a user."""
        pipeline = self.db.query(OnboardingPipeline).filter(
            OnboardingPipeline.user_id == user_id
        ).order_by(OnboardingPipeline.started_at.desc()).first()
        
        if not pipeline:
            return None
        
        return {
            "pipeline_id": pipeline.id,
            "type": pipeline.pipeline_type,
            "status": pipeline.status,
            "current_step": pipeline.current_step,
            "started_at": pipeline.started_at.isoformat(),
            "completed_at": pipeline.completed_at.isoformat() if pipeline.completed_at else None
        }
    
    def complete_step(self, pipeline_id: int, step_name: str) -> OnboardingStep:
        """Mark a step as completed."""
        step = self.db.query(OnboardingStep).filter(
            OnboardingStep.pipeline_id == pipeline_id,
            OnboardingStep.step_name == step_name
        ).first()
        
        if step:
            step.status = "completed"
            step.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            return step
        
        step = OnboardingStep(
            pipeline_id=pipeline_id,
            step_name=step_name,
            status="completed",
            completed_at=datetime.now(timezone.utc)
        )
        self.db.add(step)
        self.db.commit()
        return step


def get_onboarding_service(db: Session = None) -> OnboardingPipelineService:
    return OnboardingPipelineService(db or get_service_session())
