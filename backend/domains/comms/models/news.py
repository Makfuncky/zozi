from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow


class NewsArticle(Base):
    __tablename__ = "news_articles"
    __table_args__ = (Index("ix_news_articles_published", "published_at"), {"schema": "comms"})

    id = Column(Integer, primary_key=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("comms.news_sources.id", ondelete="SET NULL"), nullable=True, index=True)
    external_id = Column(String(255), nullable=True)
    content_hash = Column(String(64), nullable=True, index=True)
    title = Column(String(300), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    published_at = Column(DateTime, nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    ai_sentiment = Column(String(20), default="neutral")
    ai_tags = Column(JSON, nullable=True)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=True)


__all__ = ["NewsArticle"]
