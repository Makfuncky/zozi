from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from utils.datetime_utils import utcnow as _utcnow

from . import Base


class UploadJob(Base):
    __tablename__ = "upload_jobs"
    __table_args__ = ({"schema": "ai"},)

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("core.users.id"), nullable=False, index=True)
    filename = Column(String(512), nullable=False)
    status = Column(String(32), nullable=False, index=True)
    progress = Column(Float, nullable=False, default=0.0)
    strategy_winner = Column(String(64), nullable=True)
    strategy_score = Column(Float, nullable=True)
    ai_result = Column(JSON, nullable=True)
    product_id = Column(Integer, ForeignKey("commerce.products.id"), nullable=True)
    error_message = Column(Text, nullable=True)
    image_url = Column(String(1024), nullable=True)
    processed_image_url = Column(String(1024), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
    stt_duration_ms = Column(Float, nullable=True)
    nlp_duration_ms = Column(Float, nullable=True)
    bg_duration_ms = Column(Float, nullable=True)
    ai_duration_ms = Column(Float, nullable=True)
    total_duration_ms = Column(Float, nullable=True)

    supplier = relationship("User", foreign_keys=[supplier_id])
    product = relationship("Product", foreign_keys=[product_id])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "supplier_id": self.supplier_id,
            "filename": self.filename,
            "status": self.status,
            "progress": self.progress,
            "strategy_winner": self.strategy_winner,
            "strategy_score": self.strategy_score,
            "ai_result": self.ai_result,
            "product_id": self.product_id,
            "error_message": self.error_message,
            "image_url": self.image_url,
            "processed_image_url": self.processed_image_url,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "stt_duration_ms": self.stt_duration_ms,
            "nlp_duration_ms": self.nlp_duration_ms,
            "bg_duration_ms": self.bg_duration_ms,
            "ai_duration_ms": self.ai_duration_ms,
            "total_duration_ms": self.total_duration_ms,
        }
