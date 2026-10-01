"""comms domain — Message model previously housed under country.

This table was originally defined in ``domains/country/models/countries.py``.
It is a comms-domain concept (user-to-user message) and has been relocated here to
remove cross-domain pollution.

The ``__tablename__`` is preserved unchanged. The schema has been corrected to
``comms`` (was ``country``) to comply with Law 6 (schema discipline).
"""
from __future__ import annotations
from uuid import uuid4
from sqlalchemy import func, UUID
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from infrastructure.database.types import GUID
from . import Base
from domains.country.models.countries import CountryConfig  # noqa: F401
from infrastructure.utils.datetime_utils import utcnow as utcnow

__all__ = ["Message"]


class Message(Base):
    __tablename__ = 'messages'
    uuid = Column(GUID(), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = (Index('ix_message_recipient', 'to_user_id', 'created_at'), Index('ix_message_sender', 'from_user_id', 'created_at'), Index('ix_messages_country_created', 'country_code', 'created_at'), {'schema': 'comms'})
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(2), ForeignKey('country.country_configs.code', ondelete='RESTRICT'), nullable=True, index=True)
    from_user_id = Column(Integer, nullable=False)
    to_user_id = Column(Integer, nullable=False)
    subject = Column(String(200), nullable=False)
    body = Column(Text, nullable=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    priority = Column(String(20), default='normal')
    category = Column(String(50), nullable=True)
    status = Column(String(20), default='sent')
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    country = relationship('CountryConfig')
    from_user = relationship('User', primaryjoin='foreign(Message.from_user_id) == User.id')
    to_user = relationship('User', primaryjoin='foreign(Message.to_user_id) == User.id')
