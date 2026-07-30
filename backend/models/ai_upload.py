"""AI upload pipeline models (Phase 4).

The old flow ran AI enrichment **inline** inside the per-item bulk loop
(``supplier_controller.py``), blocking the request, with no job/cost/audit
record and no idempotency. These tables move enrichment to a durable,
resumable, audited flow:

    supplier upload -> ai_upload_jobs(pending)
        -> worker enriches + writes ai_staging_products / ai_staging_variants
           (+ ai_generation_logs per field)
        -> supplier reviews staging
        -> publish -> upsert into products / product_variants (committed)

All four tables are country-scoped (``country_code VARCHAR(10)``) and are
registered in the RLS registry (``utils/rls_interceptor.py``).

PG note (Phase 6): these belong to the ``supplier`` schema. The schema is
applied via a Postgres-only migration (``ALTER TABLE ... SET SCHEMA``); it is
NOT set here because SQLite interprets ``__table_args__["schema"]`` as an
attached database and would fail to find the table.
"""
from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from . import Base
from utils.datetime_utils import utcnow as _utcnow

__all__ = [
    "AIUploadJob",
    "AIStagingProduct",
    "AIStagingVariant",
    "AIGenerationLog",
]


class AIUploadJob(Base):
    __tablename__ = "ai_upload_jobs"

    __table_args__ = ({"schema": "ai"},)

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(20), default="pending", nullable=False, index=True)
    model_used = Column(String(100), nullable=True)
    prompt_hash = Column(String(64), nullable=True, index=True)
    tokens_used = Column(Numeric(12, 2), nullable=True)
    source_media_json = Column(Text, nullable=True)
    created_product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    error_log = Column(Text, nullable=True)
    country_code = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    staging_products = relationship(
        "AIStagingProduct", back_populates="job",
        order_by="AIStagingProduct.id", cascade="all, delete-orphan",
    )


class AIStagingProduct(Base):
    __tablename__ = "ai_staging_products"

    __table_args__ = ({"schema": "ai"},)

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("ai_upload_jobs.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=True)
    stock = Column(Integer, default=0)
    category = Column(String, nullable=True)
    subcategory = Column(String, nullable=True)
    color = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)
    sizes = Column(JSON, nullable=True)
    materials = Column(JSON, nullable=True)
    image_url = Column(String, nullable=True)
    additional_media = Column(JSON, nullable=True)
    ai_description = Column(Text, nullable=True)
    variant_axes = Column(JSON, nullable=True)
    attributes = Column(JSON, nullable=True)
    confidence_score = Column(Numeric(5, 4), nullable=True)
    requires_human_review = Column(Boolean, default=False)
    country_code = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)

    job = relationship("AIUploadJob", back_populates="staging_products")
    staging_variants = relationship(
        "AIStagingVariant", back_populates="staging_product",
        order_by="AIStagingVariant.id", cascade="all, delete-orphan",
    )


class AIStagingVariant(Base):
    __tablename__ = "ai_staging_variants"

    __table_args__ = ({"schema": "ai"},)

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("ai_upload_jobs.id"), nullable=False, index=True)
    staging_product_id = Column(Integer, ForeignKey("ai_staging_products.id"), nullable=False, index=True)
    variant_key = Column(String(64), nullable=True, index=True)
    size = Column(String, nullable=True)
    color = Column(String, nullable=True)
    material = Column(String, nullable=True)
    pattern = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    sku = Column(String, nullable=True)
    barcode = Column(String, nullable=True)
    product_code = Column(String, nullable=True)
    price = Column(Numeric(10, 2), nullable=True)
    stock = Column(Integer, default=0)
    media_url = Column(String, nullable=True)
    attributes_json = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    confidence_score = Column(Numeric(5, 4), nullable=True)
    requires_human_review = Column(Boolean, default=False)
    country_code = Column(String(10), nullable=True, index=True)

    staging_product = relationship("AIStagingProduct", back_populates="staging_variants")


class AIGenerationLog(Base):
    __tablename__ = "ai_generation_logs"

    __table_args__ = ({"schema": "ai"},)

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("ai_upload_jobs.id"), nullable=False, index=True)
    field = Column(String(40), nullable=False)
    model_used = Column(String(100), nullable=True)
    prompt_hash = Column(String(64), nullable=True, index=True)
    tokens_used = Column(Numeric(12, 2), nullable=True)
    cost = Column(Numeric(12, 6), nullable=True)
    confidence = Column(Numeric(5, 4), nullable=True)
    country_code = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)


Index("ix_ai_staging_variants_job_staging", AIStagingVariant.job_id, AIStagingVariant.staging_product_id)

