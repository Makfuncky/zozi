"""comms domain - sanctioned cross-domain READ surface (ports).

Per NEW_STRUCTURE.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these functions instead
of importing ``domains.comms.models`` or ``domains.comms.services`` directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via ``rbac``).
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from infrastructure.utils.pagination import (
    CursorPage,
    MAX_PAGE_SIZE,
    cursor_paginate_asc,
)

# --- Keyset (cursor) pagination helpers (diagram §6: NEVER OFFSET on hot lists) ---
# The existing ``list_*`` functions keep their public contract (a plain ``List``)
# so cross-domain consumers are unaffected, but they are now sourced via keyset
# (stable ``id`` order, no OFFSET). The ``*_page`` companions return a ``CursorPage``
# for scale-ready cursor paging (the 100Ks-concurrent-user path).

def _keyset_list(model, db: Session, limit: int = 100) -> list:
    """Backward-compatible plain list sourced via keyset (no OFFSET)."""
    return cursor_paginate_asc(db.query(model), page_size=limit).items


def _keyset_page(model, db: Session, cursor: Optional[str] = None,
                 page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page over ``model`` (scale-ready, no OFFSET)."""
    return cursor_paginate_asc(db.query(model), cursor=cursor, page_size=page_size)

from domains.comms.models.chat import (
    DirectChatRoom, DirectChatMessage, EntityChatThread, EntityChatMessage,
    EscalationSLALog, GroupChatMember, GroupChatRoom, GroupChatMessage,
    VideoRoom, VideoRoomParticipant,
)
from domains.comms.models.communication_schema_models import (
    SupportTicket, TicketAttachment, NewsSource, InternalNotice, EscalationSLARule,
)
from domains.comms.models.news import NewsArticle
from domains.comms.models.communication import Announcement, ChatAttachment, ChatReadReceipt, CommunicationAuditTrail, EmailFolder, EmployeeCommunicationThread, ExternalContactMasking, FAQ, HelpCategory, InternalChannel, InternalChannelMember, InternalEmail, InternalMessage, MaskedMessage, Notification, ProxyCallLog, ProxyChannel, ProxyMessage, ProxySession, TicketMessage
from domains.comms.models.marketing import CampaignRecipient, EmailCampaign, EmailCampaignLog, EmailDeliveryEvent, EmailRuntimeConfig, EmailSuppression, EmailTemplate, FlashSaleItem, NewsletterSubscriber
from domains.promotions.models.promotions import FlashSale
from domains.promotions.models.loyalty_points import UserPoints, PointsTransaction
from domains.comms.models.chat import (
    DirectChatRoom, DirectChatMessage, EntityChatThread, EntityChatMessage,
    EscalationSLALog, GroupChatMember, GroupChatRoom, GroupChatMessage,
    VideoRoom, VideoRoomParticipant,
)
from domains.comms.models.suppliers import SupplierBadge, SupplierBadgeBillingHistory, SupplierBadgeCatalog, SupplierDocument, SupplierNotificationPreference, SupplierProfile
from domains.comms.models.communication_schema_models import SupportTicketReply  # A3: sanctioned ports surface for accounts hub


def get_notification_by_id(db: Session, id_: int) -> Optional[Notification]:
    """Return Notification by primary key (or None)."""
    return db.get(Notification, id_)

def list_notifications(db: Session, limit: int = 100) -> List[Notification]:
    """Return up to ``limit`` Notification rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Notification, db, limit)

def list_notifications_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of Notification rows (scale-ready)."""
    return _keyset_page(Notification, db, cursor, page_size)

def get_ticket_message_by_id(db: Session, id_: int) -> Optional[TicketMessage]:
    """Return TicketMessage by primary key (or None)."""
    return db.get(TicketMessage, id_)

def list_ticket_messages(db: Session, limit: int = 100) -> List[TicketMessage]:
    """Return up to ``limit`` TicketMessage rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(TicketMessage, db, limit)

def list_ticket_messages_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of TicketMessage rows (scale-ready)."""
    return _keyset_page(TicketMessage, db, cursor, page_size)

def get_announcement_by_id(db: Session, id_: int) -> Optional[Announcement]:
    """Return Announcement by primary key (or None)."""
    return db.get(Announcement, id_)

def list_announcements(db: Session, limit: int = 100) -> List[Announcement]:
    """Return up to ``limit`` Announcement rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Announcement, db, limit)

def list_announcements_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of Announcement rows (scale-ready)."""
    return _keyset_page(Announcement, db, cursor, page_size)

def get_f_a_q_by_id(db: Session, id_: int) -> Optional[FAQ]:
    """Return FAQ by primary key (or None)."""
    return db.get(FAQ, id_)

def list_f_a_qs(db: Session, limit: int = 100) -> List[FAQ]:
    """Return up to ``limit`` FAQ rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(FAQ, db, limit)

def list_f_a_qs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of FAQ rows (scale-ready)."""
    return _keyset_page(FAQ, db, cursor, page_size)

def get_help_category_by_id(db: Session, id_: int) -> Optional[HelpCategory]:
    """Return HelpCategory by primary key (or None)."""
    return db.get(HelpCategory, id_)

def list_help_categorys(db: Session, limit: int = 100) -> List[HelpCategory]:
    """Return up to ``limit`` HelpCategory rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(HelpCategory, db, limit)

def list_help_categorys_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of HelpCategory rows (scale-ready)."""
    return _keyset_page(HelpCategory, db, cursor, page_size)

def get_proxy_channel_by_id(db: Session, id_: int) -> Optional[ProxyChannel]:
    """Return ProxyChannel by primary key (or None)."""
    return db.get(ProxyChannel, id_)

def list_proxy_channels(db: Session, limit: int = 100) -> List[ProxyChannel]:
    """Return up to ``limit`` ProxyChannel rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ProxyChannel, db, limit)

def list_proxy_channels_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ProxyChannel rows (scale-ready)."""
    return _keyset_page(ProxyChannel, db, cursor, page_size)

def get_proxy_session_by_id(db: Session, id_: int) -> Optional[ProxySession]:
    """Return ProxySession by primary key (or None)."""
    return db.get(ProxySession, id_)

def list_proxy_sessions(db: Session, limit: int = 100) -> List[ProxySession]:
    """Return up to ``limit`` ProxySession rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ProxySession, db, limit)

def list_proxy_sessions_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ProxySession rows (scale-ready)."""
    return _keyset_page(ProxySession, db, cursor, page_size)

def get_proxy_message_by_id(db: Session, id_: int) -> Optional[ProxyMessage]:
    """Return ProxyMessage by primary key (or None)."""
    return db.get(ProxyMessage, id_)

def list_proxy_messages(db: Session, limit: int = 100) -> List[ProxyMessage]:
    """Return up to ``limit`` ProxyMessage rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ProxyMessage, db, limit)

def list_proxy_messages_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ProxyMessage rows (scale-ready)."""
    return _keyset_page(ProxyMessage, db, cursor, page_size)

def get_proxy_call_log_by_id(db: Session, id_: int) -> Optional[ProxyCallLog]:
    """Return ProxyCallLog by primary key (or None)."""
    return db.get(ProxyCallLog, id_)

def list_proxy_call_logs(db: Session, limit: int = 100) -> List[ProxyCallLog]:
    """Return up to ``limit`` ProxyCallLog rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ProxyCallLog, db, limit)

def list_proxy_call_logs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ProxyCallLog rows (scale-ready)."""
    return _keyset_page(ProxyCallLog, db, cursor, page_size)

def get_employee_communication_thread_by_id(db: Session, id_: int) -> Optional[EmployeeCommunicationThread]:
    """Return EmployeeCommunicationThread by primary key (or None)."""
    return db.get(EmployeeCommunicationThread, id_)

def list_employee_communication_threads(db: Session, limit: int = 100) -> List[EmployeeCommunicationThread]:
    """Return up to ``limit`` EmployeeCommunicationThread rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmployeeCommunicationThread, db, limit)

def list_employee_communication_threads_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmployeeCommunicationThread rows (scale-ready)."""
    return _keyset_page(EmployeeCommunicationThread, db, cursor, page_size)

def get_external_contact_masking_by_id(db: Session, id_: int) -> Optional[ExternalContactMasking]:
    """Return ExternalContactMasking by primary key (or None)."""
    return db.get(ExternalContactMasking, id_)

def list_external_contact_maskings(db: Session, limit: int = 100) -> List[ExternalContactMasking]:
    """Return up to ``limit`` ExternalContactMasking rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ExternalContactMasking, db, limit)

def list_external_contact_maskings_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ExternalContactMasking rows (scale-ready)."""
    return _keyset_page(ExternalContactMasking, db, cursor, page_size)

def get_communication_audit_trail_by_id(db: Session, id_: int) -> Optional[CommunicationAuditTrail]:
    """Return CommunicationAuditTrail by primary key (or None)."""
    return db.get(CommunicationAuditTrail, id_)

def list_communication_audit_trails(db: Session, limit: int = 100) -> List[CommunicationAuditTrail]:
    """Return up to ``limit`` CommunicationAuditTrail rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CommunicationAuditTrail, db, limit)

def list_communication_audit_trails_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of CommunicationAuditTrail rows (scale-ready)."""
    return _keyset_page(CommunicationAuditTrail, db, cursor, page_size)

def get_internal_channel_by_id(db: Session, id_: int) -> Optional[InternalChannel]:
    """Return InternalChannel by primary key (or None)."""
    return db.get(InternalChannel, id_)

def list_internal_channels(db: Session, limit: int = 100) -> List[InternalChannel]:
    """Return up to ``limit`` InternalChannel rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(InternalChannel, db, limit)

def list_internal_channels_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of InternalChannel rows (scale-ready)."""
    return _keyset_page(InternalChannel, db, cursor, page_size)

def get_internal_channel_member_by_id(db: Session, id_: int) -> Optional[InternalChannelMember]:
    """Return InternalChannelMember by primary key (or None)."""
    return db.get(InternalChannelMember, id_)

def list_internal_channel_members(db: Session, limit: int = 100) -> List[InternalChannelMember]:
    """Return up to ``limit`` InternalChannelMember rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(InternalChannelMember, db, limit)

def list_internal_channel_members_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of InternalChannelMember rows (scale-ready)."""
    return _keyset_page(InternalChannelMember, db, cursor, page_size)

def get_internal_message_by_id(db: Session, id_: int) -> Optional[InternalMessage]:
    """Return InternalMessage by primary key (or None)."""
    return db.get(InternalMessage, id_)

def list_internal_messages(db: Session, limit: int = 100) -> List[InternalMessage]:
    """Return up to ``limit`` InternalMessage rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(InternalMessage, db, limit)

def list_internal_messages_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of InternalMessage rows (scale-ready)."""
    return _keyset_page(InternalMessage, db, cursor, page_size)

def get_chat_read_receipt_by_id(db: Session, id_: int) -> Optional[ChatReadReceipt]:
    """Return ChatReadReceipt by primary key (or None)."""
    return db.get(ChatReadReceipt, id_)

def list_chat_read_receipts(db: Session, limit: int = 100) -> List[ChatReadReceipt]:
    """Return up to ``limit`` ChatReadReceipt rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ChatReadReceipt, db, limit)

def list_chat_read_receipts_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ChatReadReceipt rows (scale-ready)."""
    return _keyset_page(ChatReadReceipt, db, cursor, page_size)

def get_chat_attachment_by_id(db: Session, id_: int) -> Optional[ChatAttachment]:
    """Return ChatAttachment by primary key (or None)."""
    return db.get(ChatAttachment, id_)

def list_chat_attachments(db: Session, limit: int = 100) -> List[ChatAttachment]:
    """Return up to ``limit`` ChatAttachment rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ChatAttachment, db, limit)

def list_chat_attachments_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ChatAttachment rows (scale-ready)."""
    return _keyset_page(ChatAttachment, db, cursor, page_size)

def get_internal_email_by_id(db: Session, id_: int) -> Optional[InternalEmail]:
    """Return InternalEmail by primary key (or None)."""
    return db.get(InternalEmail, id_)

def list_internal_emails(db: Session, limit: int = 100) -> List[InternalEmail]:
    """Return up to ``limit`` InternalEmail rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(InternalEmail, db, limit)

def list_internal_emails_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of InternalEmail rows (scale-ready)."""
    return _keyset_page(InternalEmail, db, cursor, page_size)

def get_email_folder_by_id(db: Session, id_: int) -> Optional[EmailFolder]:
    """Return EmailFolder by primary key (or None)."""
    return db.get(EmailFolder, id_)

def list_email_folders(db: Session, limit: int = 100) -> List[EmailFolder]:
    """Return up to ``limit`` EmailFolder rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmailFolder, db, limit)

def list_email_folders_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmailFolder rows (scale-ready)."""
    return _keyset_page(EmailFolder, db, cursor, page_size)

def get_masked_message_by_id(db: Session, id_: int) -> Optional[MaskedMessage]:
    """Return MaskedMessage by primary key (or None)."""
    return db.get(MaskedMessage, id_)

def list_masked_messages(db: Session, limit: int = 100) -> List[MaskedMessage]:
    """Return up to ``limit`` MaskedMessage rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(MaskedMessage, db, limit)

def list_masked_messages_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of MaskedMessage rows (scale-ready)."""
    return _keyset_page(MaskedMessage, db, cursor, page_size)

def get_flash_sale_by_id(db: Session, id_: int) -> Optional[FlashSale]:
    """Return FlashSale by primary key (or None)."""
    return db.get(FlashSale, id_)

def list_flash_sales(db: Session, limit: int = 100) -> List[FlashSale]:
    """Return up to ``limit`` FlashSale rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(FlashSale, db, limit)

def list_flash_sales_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of FlashSale rows (scale-ready)."""
    return _keyset_page(FlashSale, db, cursor, page_size)

def get_flash_sale_item_by_id(db: Session, id_: int) -> Optional[FlashSaleItem]:
    """Return FlashSaleItem by primary key (or None)."""
    return db.get(FlashSaleItem, id_)

def list_flash_sale_items(db: Session, limit: int = 100) -> List[FlashSaleItem]:
    """Return up to ``limit`` FlashSaleItem rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(FlashSaleItem, db, limit)

def list_flash_sale_items_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of FlashSaleItem rows (scale-ready)."""
    return _keyset_page(FlashSaleItem, db, cursor, page_size)

def get_email_campaign_by_id(db: Session, id_: int) -> Optional[EmailCampaign]:
    """Return EmailCampaign by primary key (or None)."""
    return db.get(EmailCampaign, id_)

def list_email_campaigns(db: Session, limit: int = 100) -> List[EmailCampaign]:
    """Return up to ``limit`` EmailCampaign rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmailCampaign, db, limit)

def list_email_campaigns_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmailCampaign rows (scale-ready)."""
    return _keyset_page(EmailCampaign, db, cursor, page_size)

def get_email_template_by_id(db: Session, id_: int) -> Optional[EmailTemplate]:
    """Return EmailTemplate by primary key (or None)."""
    return db.get(EmailTemplate, id_)

def list_email_templates(db: Session, limit: int = 100) -> List[EmailTemplate]:
    """Return up to ``limit`` EmailTemplate rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmailTemplate, db, limit)

def list_email_templates_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmailTemplate rows (scale-ready)."""
    return _keyset_page(EmailTemplate, db, cursor, page_size)

def get_newsletter_subscriber_by_id(db: Session, id_: int) -> Optional[NewsletterSubscriber]:
    """Return NewsletterSubscriber by primary key (or None)."""
    return db.get(NewsletterSubscriber, id_)

def list_newsletter_subscribers(db: Session, limit: int = 100) -> List[NewsletterSubscriber]:
    """Return up to ``limit`` NewsletterSubscriber rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(NewsletterSubscriber, db, limit)

def list_newsletter_subscribers_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of NewsletterSubscriber rows (scale-ready)."""
    return _keyset_page(NewsletterSubscriber, db, cursor, page_size)

def get_email_campaign_log_by_id(db: Session, id_: int) -> Optional[EmailCampaignLog]:
    """Return EmailCampaignLog by primary key (or None)."""
    return db.get(EmailCampaignLog, id_)

def list_email_campaign_logs(db: Session, limit: int = 100) -> List[EmailCampaignLog]:
    """Return up to ``limit`` EmailCampaignLog rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmailCampaignLog, db, limit)

def list_email_campaign_logs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmailCampaignLog rows (scale-ready)."""
    return _keyset_page(EmailCampaignLog, db, cursor, page_size)

def get_campaign_recipient_by_id(db: Session, id_: int) -> Optional[CampaignRecipient]:
    """Return CampaignRecipient by primary key (or None)."""
    return db.get(CampaignRecipient, id_)

def list_campaign_recipients(db: Session, limit: int = 100) -> List[CampaignRecipient]:
    """Return up to ``limit`` CampaignRecipient rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CampaignRecipient, db, limit)

def list_campaign_recipients_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of CampaignRecipient rows (scale-ready)."""
    return _keyset_page(CampaignRecipient, db, cursor, page_size)


def campaign_recipient_query(db: Session) -> object:
    """Return a base ``CampaignRecipient`` query for sanctioned cross-domain delegation."""
    return db.query(CampaignRecipient)


def direct_chat_message_query(db: Session) -> object:
    """Return a base ``DirectChatMessage`` query for sanctioned cross-domain delegation."""
    return db.query(DirectChatMessage)


def group_chat_message_query(db: Session) -> object:
    """Return a base ``GroupChatMessage`` query for sanctioned cross-domain delegation."""
    return db.query(GroupChatMessage)


def entity_chat_message_query(db: Session) -> object:
    """Return a base ``EntityChatMessage`` query for sanctioned cross-domain delegation."""
    return db.query(EntityChatMessage)


def video_room_query(db: Session) -> object:
    """Return a base ``VideoRoom`` query for sanctioned cross-domain delegation."""
    return db.query(VideoRoom)

def get_email_delivery_event_by_id(db: Session, id_: int) -> Optional[EmailDeliveryEvent]:
    """Return EmailDeliveryEvent by primary key (or None)."""
    return db.get(EmailDeliveryEvent, id_)

def list_email_delivery_events(db: Session, limit: int = 100) -> List[EmailDeliveryEvent]:
    """Return up to ``limit`` EmailDeliveryEvent rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmailDeliveryEvent, db, limit)

def list_email_delivery_events_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmailDeliveryEvent rows (scale-ready)."""
    return _keyset_page(EmailDeliveryEvent, db, cursor, page_size)

def get_email_suppression_by_id(db: Session, id_: int) -> Optional[EmailSuppression]:
    """Return EmailSuppression by primary key (or None)."""
    return db.get(EmailSuppression, id_)

def list_email_suppressions(db: Session, limit: int = 100) -> List[EmailSuppression]:
    """Return up to ``limit`` EmailSuppression rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmailSuppression, db, limit)

def list_email_suppressions_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmailSuppression rows (scale-ready)."""
    return _keyset_page(EmailSuppression, db, cursor, page_size)

def get_email_runtime_config_by_id(db: Session, id_: int) -> Optional[EmailRuntimeConfig]:
    """Return EmailRuntimeConfig by primary key (or None)."""
    return db.get(EmailRuntimeConfig, id_)

def list_email_runtime_configs(db: Session, limit: int = 100) -> List[EmailRuntimeConfig]:
    """Return up to ``limit`` EmailRuntimeConfig rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmailRuntimeConfig, db, limit)

def list_email_runtime_configs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmailRuntimeConfig rows (scale-ready)."""
    return _keyset_page(EmailRuntimeConfig, db, cursor, page_size)

def get_points_transaction_by_id(db: Session, id_: int) -> Optional[PointsTransaction]:
    """Return PointsTransaction by primary key (or None)."""
    return db.get(PointsTransaction, id_)

def list_points_transactions(db: Session, limit: int = 100) -> List[PointsTransaction]:
    """Return up to ``limit`` PointsTransaction rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PointsTransaction, db, limit)

def list_points_transactions_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of PointsTransaction rows (scale-ready)."""
    return _keyset_page(PointsTransaction, db, cursor, page_size)

def get_user_points_by_id(db: Session, id_: int) -> Optional[UserPoints]:
    """Return UserPoints by primary key (or None)."""
    return db.get(UserPoints, id_)

def list_user_points(db: Session, limit: int = 100) -> List[UserPoints]:
    """Return up to ``limit`` UserPoints rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(UserPoints, db, limit)

def list_user_points_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of UserPoints rows (scale-ready)."""
    return _keyset_page(UserPoints, db, cursor, page_size)

def get_supplier_profile_by_id(db: Session, id_: int) -> Optional[SupplierProfile]:
    """Return SupplierProfile by primary key (or None)."""
    return db.get(SupplierProfile, id_)

def list_supplier_profiles(db: Session, limit: int = 100) -> List[SupplierProfile]:
    """Return up to ``limit`` SupplierProfile rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SupplierProfile, db, limit)

def list_supplier_profiles_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of SupplierProfile rows (scale-ready)."""
    return _keyset_page(SupplierProfile, db, cursor, page_size)

def get_supplier_document_by_id(db: Session, id_: int) -> Optional[SupplierDocument]:
    """Return SupplierDocument by primary key (or None)."""
    return db.get(SupplierDocument, id_)

def list_supplier_documents(db: Session, limit: int = 100) -> List[SupplierDocument]:
    """Return up to ``limit`` SupplierDocument rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SupplierDocument, db, limit)

def list_supplier_documents_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of SupplierDocument rows (scale-ready)."""
    return _keyset_page(SupplierDocument, db, cursor, page_size)

def get_supplier_notification_preference_by_id(db: Session, id_: int) -> Optional[SupplierNotificationPreference]:
    """Return SupplierNotificationPreference by primary key (or None)."""
    return db.get(SupplierNotificationPreference, id_)

def list_supplier_notification_preferences(db: Session, limit: int = 100) -> List[SupplierNotificationPreference]:
    """Return up to ``limit`` SupplierNotificationPreference rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SupplierNotificationPreference, db, limit)

def list_supplier_notification_preferences_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of SupplierNotificationPreference rows (scale-ready)."""
    return _keyset_page(SupplierNotificationPreference, db, cursor, page_size)

def get_supplier_badge_catalog_by_id(db: Session, id_: int) -> Optional[SupplierBadgeCatalog]:
    """Return SupplierBadgeCatalog by primary key (or None)."""
    return db.get(SupplierBadgeCatalog, id_)

def list_supplier_badge_catalogs(db: Session, limit: int = 100) -> List[SupplierBadgeCatalog]:
    """Return up to ``limit`` SupplierBadgeCatalog rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SupplierBadgeCatalog, db, limit)

def list_supplier_badge_catalogs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of SupplierBadgeCatalog rows (scale-ready)."""
    return _keyset_page(SupplierBadgeCatalog, db, cursor, page_size)

def get_supplier_badge_by_id(db: Session, id_: int) -> Optional[SupplierBadge]:
    """Return SupplierBadge by primary key (or None)."""
    return db.get(SupplierBadge, id_)

def list_supplier_badges(db: Session, limit: int = 100) -> List[SupplierBadge]:
    """Return up to ``limit`` SupplierBadge rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SupplierBadge, db, limit)

def list_supplier_badges_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of SupplierBadge rows (scale-ready)."""
    return _keyset_page(SupplierBadge, db, cursor, page_size)

def get_supplier_badge_billing_history_by_id(db: Session, id_: int) -> Optional[SupplierBadgeBillingHistory]:
    """Return SupplierBadgeBillingHistory by primary key (or None)."""
    return db.get(SupplierBadgeBillingHistory, id_)

def list_supplier_badge_billing_historys(db: Session, limit: int = 100) -> List[SupplierBadgeBillingHistory]:
    """Return up to ``limit`` SupplierBadgeBillingHistory rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SupplierBadgeBillingHistory, db, limit)

def list_supplier_badge_billing_historys_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of SupplierBadgeBillingHistory rows (scale-ready)."""
    return _keyset_page(SupplierBadgeBillingHistory, db, cursor, page_size)


# ── sanctioned READ surface re-exports (Law 3) ─────────────────────────────
# Cross-domain consumers import these from ``domains.comms.ports`` instead of
# from the model modules directly.  Read-only; no service logic re-exported.

from domains.comms.models.chat import (
    DirectChatRoom, DirectChatMessage, EntityChatThread, EntityChatMessage,
    EscalationSLALog, GroupChatMember, GroupChatRoom, GroupChatMessage,
    VideoRoom, VideoRoomParticipant,
)
from domains.comms.models.communication_schema_models import (
    SupportTicket, TicketAttachment, NewsSource, InternalNotice, EscalationSLARule,
)
from domains.comms.models.news import NewsArticle
from domains.comms.models.communication import Notification
from domains.comms.models.marketing import (
    CampaignRecipient,
    EmailCampaign,
    FlashSale,
    FlashSaleItem,
    NewsletterSubscriber,
    PointsTransaction,
    UserPoints,
)


# Sanctioned cross-domain READ surface
__all__ = [
    # Models from communication.py
    "Announcement", "ChatAttachment", "ChatReadReceipt", "CommunicationAuditTrail",
    "EmailFolder", "EmployeeCommunicationThread", "ExternalContactMasking", "FAQ",
    "HelpCategory", "InternalChannel", "InternalChannelMember", "InternalEmail",
    "InternalMessage", "MaskedMessage", "Notification", "ProxyCallLog", "ProxyChannel",
    "ProxyMessage", "ProxySession", "TicketMessage",
    # Models from marketing.py
    "CampaignRecipient", "EmailCampaign", "EmailCampaignLog", "EmailDeliveryEvent",
    "EmailRuntimeConfig", "EmailSuppression", "EmailTemplate", "FlashSale",
    "FlashSaleItem", "NewsletterSubscriber", "PointsTransaction", "UserPoints",
    # Models from suppliers.py
    "SupplierBadge", "SupplierBadgeBillingHistory", "SupplierBadgeCatalog",
    "SupplierDocument", "SupplierNotificationPreference", "SupplierProfile",
    # Models from communication_schema_models.py
    "SupportTicket", "SupportTicketReply", "TicketAttachment", "NewsSource",
    "InternalNotice", "EscalationSLARule",
    # Models from chat.py
    "DirectChatRoom", "DirectChatMessage", "EntityChatThread", "EntityChatMessage",
    "EscalationSLALog", "GroupChatMember", "GroupChatRoom", "GroupChatMessage",
    "VideoRoom", "VideoRoomParticipant",
    # Models from news.py
    "NewsArticle",
    # Functions
    "get_notification_by_id", "list_notifications", "list_notifications_page",
    "get_ticket_message_by_id", "list_ticket_messages",
    "get_announcement_by_id", "list_announcements",
]


# --- Lazy model re-exports for infrastructure/kernel Law 1 compliance ---
# Infrastructure and kernel layers must not import directly from domains/*/models.
# These lazy exports let infrastructure access domain models via the sanctioned
# ports surface without circular imports (resolved on first access at runtime).
_LAZY_MODEL_EXPORTS: dict[str, tuple[str, str]] = {
    "Notification": ("domains.comms.models.communication", "Notification"),
    "InternalEmail": ("domains.comms.models.communication", "InternalEmail"),
    "SupplierProfile": ("domains.comms.models.suppliers", "SupplierProfile"),
}

import importlib as _importlib


def __getattr__(name: str):
    if name in _LAZY_MODEL_EXPORTS:
        module_path, symbol = _LAZY_MODEL_EXPORTS[name]
        mod = _importlib.import_module(module_path)
        value = getattr(mod, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# ── Campaign functions (sanctioned cross-domain delegation) ─────────────────
# Thin wrappers so module routers import from comms.ports instead of
# directly from domains.comms.services.email.email_management.

def create_campaign(db: Session, payload: dict, country_code: str) -> dict:
    """Sanctioned cross-domain write: create an email campaign."""
    from domains.comms.services.email.email_management import create_campaign as _svc
    return _svc(db, payload, country_code)


def delete_campaign(db: Session, campaign_id: int, country_code: str) -> dict:
    """Sanctioned cross-domain write: delete an email campaign."""
    from domains.comms.services.email.email_management import delete_campaign as _svc
    return _svc(db, campaign_id, country_code)


def list_campaigns(db: Session, country_code: str, page: int, page_size: int) -> dict:
    """Sanctioned cross-domain read: list email campaigns by country."""
    from domains.comms.services.email.email_management import list_campaigns as _svc
    return _svc(db, country_code, page, page_size)


def list_all_campaigns(db: Session) -> list:
    """Sanctioned cross-domain read: list all email campaigns."""
    from domains.comms.services.email.email_management import list_all_campaigns as _svc
    return _svc(db)


# ── Notification enums and support-ticket helpers (module-router use only) ─
# Re-exported here so module routers import from comms.ports instead of
# reaching into ``domains.comms.services.comms_service`` directly.

_LAZY_COMMS_EXPORTS: dict[str, tuple[str, str]] = {
    "NotificationChannel": ("domains.comms.services.comms_service", "NotificationChannel"),
    "NotificationPriority": ("domains.comms.services.comms_service", "NotificationPriority"),
    "list_support_tickets": ("domains.comms.services.comms_service", "list_support_tickets"),
    "create_support_ticket": ("domains.comms.services.comms_service", "create_support_ticket"),
    "get_support_ticket": ("domains.comms.services.comms_service", "get_support_ticket"),
    "reply_to_support_ticket": ("domains.comms.services.comms_service", "reply_to_support_ticket"),
    "enqueue_refund_processed_email": ("domains.comms.services.email.transactional_email_service", "enqueue_refund_processed_email"),
    "auto_process_image": ("domains.comms.services.free_image_tools", "auto_process_image"),
    "save_product_media": ("domains.comms.services.media_service", "save_product_media"),
    "save_supplier_media": ("domains.comms.services.media_service", "save_supplier_media"),
    "notify_logistics_partners_of_payout": ("domains.comms.services.shared.notification.notification_engine", "notify_logistics_partners_of_payout"),
    "notify_suppliers_of_payout": ("domains.comms.services.shared.notification.notification_engine", "notify_suppliers_of_payout"),
    "NotificationEngine": ("domains.comms.services.shared.notification.notification_engine", "NotificationEngine"),
    "NotificationChannel": ("domains.comms.services.shared.notification.notification_models", "NotificationChannel"),
    "NotificationPriority": ("domains.comms.services.shared.notification.notification_models", "NotificationPriority"),
    "create_notification": ("domains.comms.services.tickets.tickets_service", "create_notification"),
    "enqueue_invoice_email": ("domains.comms.services.transactional_email_service", "enqueue_invoice_email"),
    "enqueue_payment_confirmed_email": ("domains.comms.services.transactional_email_service", "enqueue_payment_confirmed_email"),
    "enqueue_payment_failed_email": ("domains.comms.services.transactional_email_service", "enqueue_payment_failed_email"),
    "enqueue_supplier_approval_email": ("domains.comms.services.shared.notification.notification_engine", "enqueue_supplier_approval_email"),
    "enqueue_shipment_status_email": ("domains.comms.services.transactional_email_service", "enqueue_shipment_status_email"),
    "enqueue_order_status_email": ("domains.comms.services.transactional_email_service", "enqueue_order_status_email"),
    "enqueue_return_created_email": ("domains.comms.services.transactional_email_service", "enqueue_return_created_email"),
    "enqueue_return_status_email": ("domains.comms.services.transactional_email_service", "enqueue_return_status_email"),
}


_orig_comms_getattr = __getattr__


def __getattr__(name: str):  # type: ignore[no-redef]
    if name in _LAZY_COMMS_EXPORTS:
        import importlib as _il
        module_path, symbol = _LAZY_COMMS_EXPORTS[name]
        mod = _il.import_module(module_path)
        value = getattr(mod, symbol)
        globals()[name] = value
        return value
    return _orig_comms_getattr(name)



