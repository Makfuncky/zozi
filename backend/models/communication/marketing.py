from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, UniqueConstraint, Index, JSON
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as _utcnow

__all__ = ["FlashSale", "FlashSaleItem", "EmailCampaign", "EmailTemplate", "NewsletterSubscriber", "EmailCampaignLog", "CampaignRecipient", "EmailDeliveryEvent", "EmailSuppression", "EmailRuntimeConfig"]


class FlashSale(Base):
    __tablename__ = "flash_sales"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    discount_pct = Column(Numeric(5, 2), default=0)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    product_ids = Column(JSON, nullable=True)
    country_code = Column(String(3), ForeignKey("country.country_configs.code"), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    country = relationship("CountryConfig", foreign_keys=[country_code])


class FlashSaleItem(Base):
    __tablename__ = "flash_sale_items"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    flash_sale_id = Column(Integer, ForeignKey("commerce.flash_sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("commerce.products.id"), nullable=False)
    original_price = Column(Numeric(10, 2), nullable=False)
    discounted_price = Column(Numeric(10, 2), nullable=False)
    quantity_limit = Column(Integer, nullable=True)
    country_code = Column(String(3), ForeignKey("country.country_configs.code"), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    
    flash_sale = relationship("FlashSale", back_populates="items")
    product = relationship("Product")
    country = relationship("CountryConfig", foreign_keys=[country_code])


FlashSale.items = relationship("FlashSaleItem", back_populates="flash_sale", cascade="all, delete-orphan")


class EmailCampaign(Base):
    __tablename__ = "email_campaigns"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    status = Column(String, default="draft")
    send_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(3), ForeignKey("country.country_configs.code"), nullable=True, index=True)
    from_email = Column(String(200), nullable=True)
    from_name = Column(String(200), nullable=True)
    target_audience = Column(Text, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    sent_count = Column(Integer, default=0)
    open_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)


class EmailTemplate(Base):
    __tablename__ = "email_templates"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, index=True, nullable=False)
    subject = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    template_type = Column(String(50), default="marketing")
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    subscribed_at = Column(DateTime, default=_utcnow)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class EmailCampaignLog(Base):
    __tablename__ = "email_campaign_logs"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("communication.email_campaigns.id"), nullable=False)
    recipient_email = Column(String, nullable=False)
    status = Column(String, default="sent")
    sent_at = Column(DateTime, default=_utcnow)
    delivered_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class CampaignRecipient(Base):
    __tablename__ = "campaign_recipients"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("communication.email_campaigns.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    email = Column(String, nullable=False)
    status = Column(String, default="pending")
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    bounced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    
    campaign = relationship("EmailCampaign", back_populates="recipients")
    user = relationship("User")


EmailCampaign.recipients = relationship("CampaignRecipient", back_populates="campaign", cascade="all, delete-orphan")


class EmailDeliveryEvent(Base):
    __tablename__ = "email_delivery_events"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False)
    recipient_email = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    status = Column(String, default="sent")
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class EmailSuppression(Base):
    __tablename__ = "email_suppressions"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, index=True)
    reason = Column(String, nullable=False)
    source = Column(String, nullable=False)
    provider = Column(String, nullable=True)
    status = Column(String, default="active")
    notes = Column(Text, nullable=True)
    suppressed_at = Column(DateTime, nullable=True)
    last_event_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class EmailRuntimeConfig(Base):
    __tablename__ = "email_runtime_config"
    __table_args__ = ({"schema": "configuration"},)
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(50), default="environment")
    resend_api_key = Column(String, nullable=True)
    resend_webhook_secret = Column(String, nullable=True)
    smtp_host = Column(String, nullable=True)
    smtp_port = Column(Integer, default=587)
    smtp_username = Column(String, nullable=True)
    smtp_password = Column(String, nullable=True)
    smtp_use_tls = Column(Boolean, default=True)
    smtp_use_ssl = Column(Boolean, default=False)
    smtp_timeout_seconds = Column(Integer, default=15)
    email_from_default = Column(String, nullable=True)
    email_from_promotional = Column(String, nullable=True)
    email_from_transactional = Column(String, nullable=True)
    email_from_notification = Column(String, nullable=True)
    email_from_alert = Column(String, nullable=True)
    email_from_verification = Column(String, nullable=True)
    email_from_login_verification = Column(String, nullable=True)
    email_from_password_reset = Column(String, nullable=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
