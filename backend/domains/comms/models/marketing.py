from __future__ import annotations
from uuid import uuid4
from sqlalchemy import func, UUID
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, UniqueConstraint, Index, JSON, CheckConstraint, text
from sqlalchemy.orm import relationship
from infrastructure.database.types import GUID
from . import Base
from domains.country.models.countries import CountryConfig  # noqa: F401
from infrastructure.utils.datetime_utils import utcnow as utcnow
from infrastructure.database.mixins import TenantMixin, VersionMixin
__all__ = ['FlashSaleItem', 'EmailCampaign', 'EmailTemplate', 'NewsletterSubscriber', 'EmailCampaignLog', 'CampaignRecipient', 'EmailDeliveryEvent', 'EmailSuppression', 'EmailRuntimeConfig']

class FlashSaleItem(Base, TenantMixin):
    __tablename__ = 'flash_sale_items'
    __table_args__ = {"schema": "comms"}
    uuid = Column(GUID(), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = (
        Index('ix_flash_sale_items_country_created', 'country_code', 'created_at'),
        {'schema': 'comms'},
    )
    id = Column(Integer, primary_key=True, index=True)
    flash_sale_id = Column(Integer, ForeignKey('promotions.flash_sales.id', ondelete='RESTRICT'), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('catalog.products.id', ondelete='RESTRICT'), nullable=False, index=True)
    original_price = Column(Numeric(10, 2), nullable=False)
    discounted_price = Column(Numeric(10, 2), nullable=False)
    country_code = Column(String(2), nullable=True)
    quantity_limit = Column(Integer, nullable=True)
    flash_sale = relationship('FlashSale', back_populates='items')
    product = relationship('Product')
    country = relationship('CountryConfig', foreign_keys='FlashSaleItem.country_code', primaryjoin='foreign(FlashSaleItem.country_code) == CountryConfig.code')

class EmailCampaign(Base, TenantMixin):
    __tablename__ = 'email_campaigns'
    __table_args__ = {"schema": "comms"}
    uuid = Column(GUID(), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = (Index('ix_email_campaigns_country_created', 'country_code', 'created_at'), CheckConstraint("status_code IN ('draft', 'scheduled', 'sending', 'sent', 'paused', 'cancelled')", name='chk_email_campaigns_status_valid'), {'schema': 'comms'})
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    status_code = Column(String(50), default='draft')
    send_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    from_name = Column(String(200), nullable=True)
    target_audience = Column(Text, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    sent_count = Column(Integer, default=0)
    open_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    recipients = relationship('CampaignRecipient', back_populates='campaign', cascade='all, delete-orphan')

class EmailTemplate(Base):
    __tablename__ = 'email_templates'
    uuid = Column(GUID(), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = ({'schema': 'comms'},)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, index=True, nullable=False)
    subject = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    template_type = Column(String(50), default='marketing')
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

class NewsletterSubscriber(Base):
    __tablename__ = 'newsletter_subscribers'
    __table_args__ = {"schema": "comms"}
    uuid = Column(GUID(), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = ({'schema': 'comms'},)
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

class EmailCampaignLog(Base):
    __tablename__ = 'email_campaign_logs'
    __table_args__ = {"schema": "comms"}
    uuid = Column(GUID(), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = (CheckConstraint("status_code IN ('sent', 'delivered', 'bounced', 'failed')", name='chk_email_campaign_logs_status_valid'), {'schema': 'comms'})
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey('comms.email_campaigns.id', ondelete='RESTRICT'), nullable=False, index=True)
    recipient_email = Column(String(255), nullable=False)
    status_code = Column(String(50), default='sent')
    sent_at = Column(DateTime, default=utcnow)
    delivered_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

class CampaignRecipient(Base):
    __tablename__ = 'campaign_recipients'
    __table_args__ = {"schema": "comms"}
    uuid = Column(GUID(), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = (CheckConstraint("status_code IN ('pending', 'sent', 'delivered', 'bounced', 'failed', 'unsubscribed')", name='chk_campaign_recipients_status_valid'), {'schema': 'comms'})
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey('comms.email_campaigns.id', ondelete='RESTRICT'), nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    email = Column(String(255), nullable=False)
    status_code = Column(String(50), default='pending')
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    bounced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    campaign = relationship('EmailCampaign', back_populates='recipients')
    user = relationship('User', primaryjoin='foreign(CampaignRecipient.user_id) == User.id')

class EmailDeliveryEvent(Base):
    __tablename__ = 'email_delivery_events'
    __table_args__ = {"schema": "comms"}
    uuid = Column(GUID(), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = (Index('ix_email_delivery_events_details', 'details'), {'schema': 'comms'})
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=True)
    status_code = Column(String(50), default='sent')
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utcnow)

class EmailSuppression(Base):
    __tablename__ = 'email_suppressions'
    __table_args__ = {"schema": "comms"}
    uuid = Column(GUID(), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = (CheckConstraint("status_code IN ('active', 'inactive', 'expired')", name='chk_email_suppressions_status_valid'), {'schema': 'comms'})
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    reason = Column(String(255), nullable=False)
    source = Column(String(255), nullable=False)
    provider = Column(String(100), nullable=True)
    status_code = Column(String(50), default='active')
    notes = Column(Text, nullable=True)
    suppressed_at = Column(DateTime, nullable=True)
    last_event_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

class EmailRuntimeConfig(Base):
    __tablename__ = 'email_runtime_configs'
    __table_args__ = {"schema": "comms"}
    uuid = Column(GUID(), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = ({'schema': 'comms'},)
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(50), default='environment')
    resend_api_key = Column(String(255), nullable=True)
    resend_webhook_secret = Column(String(255), nullable=True)
    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(Integer, default=587)
    smtp_username = Column(String(255), nullable=True)
    smtp_password = Column(String(255), nullable=True)
    is_smtp_use_tls = Column(Boolean, default=True)
    is_smtp_use_ssl = Column(Boolean, default=False)
    smtp_timeout_seconds = Column(Integer, default=15)
    email_from_default = Column(String(255), nullable=True)
    email_from_promotional = Column(String(255), nullable=True)
    email_from_transactional = Column(String(255), nullable=True)
    email_from_notification = Column(String(255), nullable=True)
    email_from_alert = Column(String(255), nullable=True)
    email_from_verification = Column(String(255), nullable=True)
    email_from_login_verification = Column(String(255), nullable=True)
    email_from_password_reset = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


# Lazy re-export shims for models whose canonical home is the promotions domain.
# These are resolved on first access to avoid a direct cross-domain import at
# module load (Law 3: cross-domain reads resolve via the owning domain's exports).
_CANONICAL_PROMOTIONS_EXPORTS: dict[str, tuple[str, str]] = {
    "FlashSale": ("domains.promotions.models.promotions", "FlashSale"),
    "UserPoints": ("domains.promotions.models.loyalty_points", "UserPoints"),
    "PointsTransaction": ("domains.promotions.models.loyalty_points", "PointsTransaction"),
}


def __getattr__(name: str):
    """Lazily resolve promotions-owned re-exports."""
    if name in _CANONICAL_PROMOTIONS_EXPORTS:
        import importlib
        module_path, attr_name = _CANONICAL_PROMOTIONS_EXPORTS[name]
        mod = importlib.import_module(module_path)
        value = getattr(mod, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

