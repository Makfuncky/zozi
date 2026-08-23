"""accounts domain - sanctioned cross-domain READ surface (ports).

Per NEW_STRUCTURE.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these functions instead
of importing ``domains.accounts.models`` or ``domains.accounts.services`` directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via ``rbac``).

Keyset (cursor) pagination: the existing ``list_*`` functions keep their public
contract (a plain ``List``) so cross-domain consumers are unaffected, but they
are now sourced via keyset (stable ``id`` order, no OFFSET). The ``*_page``
companions return a ``CursorPage`` for scale-ready cursor paging (the
100Ks-concurrent-user path).
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from infrastructure.utils.pagination import (
    CursorPage,
    MAX_PAGE_SIZE,
    cursor_paginate_asc,
)

from domains.accounts.models.core import Address, AlertEscalationRule, AuditLog, Cart, CartItem, CityDistanceMatrix, CommandCenterView, DirectChatMessage, DirectChatRoom, EntityChatMessage, EntityChatThread, EscalationSLALog, EscalationSLARule, ExecutiveNews, GroupChatMember, GroupChatMessage, GroupChatRoom, InternalNotice, NewsArticle, NewsSource, PredictiveSimulation, ShiftHandoverSession, ShiftHandoverTask, SupportTicket, SupportTicketReply, SystemHealthEvent, TicketAttachment, UserBrowsingHistory, UserSession, VideoRoom, VideoRoomParticipant, VideoRoomRecording
from domains.hr.ports import OnboardingPipeline, OnboardingStep  # A3: canonical read via hr.ports (Law 3)
from domains.accounts.models.onboarding import DocumentVerification, KYCVerification, OCRResult
from domains.accounts.models.otp import OtpCode
from domains.accounts.models.social import SocialIdentity
from domains.accounts.models.user import EmailVerificationToken, PasswordResetToken, Referral, ReferralPointEvent, RevokedToken, User, UserDevice, UserLoginHistory


# --- Keyset (cursor) pagination helpers (diagram §6: NEVER OFFSET on hot lists) ---
# The existing ``list_*`` functions keep their public contract (a plain ``List``)
# so the many cross-domain consumers are unaffected, but they are now sourced
# via keyset (stable ``id`` order, no OFFSET). The ``*_page`` companions return a
# ``CursorPage`` for scale-ready cursor paging (the 100Ks-concurrent-user path).

def _keyset_list(model, db: Session, limit: int = 100) -> list:
    """Backward-compatible plain list sourced via keyset (no OFFSET)."""
    return cursor_paginate_asc(db.query(model), page_size=limit).items


def _keyset_page(model, db: Session, cursor: Optional[str] = None,
                 page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page over ``model`` (scale-ready, no OFFSET)."""
    return cursor_paginate_asc(db.query(model), cursor=cursor, page_size=page_size)


def get_address_by_id(db: Session, id_: int) -> Optional[Address]:
    """Return Address by primary key (or None)."""
    return db.get(Address, id_)

def list_addresss(db: Session, limit: int = 100) -> List[Address]:
    """Return up to ``limit`` Address rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Address, db, limit)

def list_addresss_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of addresses (scale-ready)."""
    return _keyset_page(Address, db, cursor, page_size)

def get_cart_by_id(db: Session, id_: int) -> Optional[Cart]:
    """Return Cart by primary key (or None)."""
    return db.get(Cart, id_)

def list_carts(db: Session, limit: int = 100) -> List[Cart]:
    """Return up to ``limit`` Cart rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Cart, db, limit)

def list_carts_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of carts (scale-ready)."""
    return _keyset_page(Cart, db, cursor, page_size)

def get_cart_item_by_id(db: Session, id_: int) -> Optional[CartItem]:
    """Return CartItem by primary key (or None)."""
    return db.get(CartItem, id_)

def list_cart_items(db: Session, limit: int = 100) -> List[CartItem]:
    """Return up to ``limit`` CartItem rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CartItem, db, limit)

def list_cart_items_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of cart items (scale-ready)."""
    return _keyset_page(CartItem, db, cursor, page_size)

def get_audit_log_by_id(db: Session, id_: int) -> Optional[AuditLog]:
    """Return AuditLog by primary key (or None)."""
    return db.get(AuditLog, id_)

def list_audit_logs(db: Session, limit: int = 100) -> List[AuditLog]:
    """Return up to ``limit`` AuditLog rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(AuditLog, db, limit)

def list_audit_logs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of audit logs (scale-ready)."""
    return _keyset_page(AuditLog, db, cursor, page_size)

def get_support_ticket_by_id(db: Session, id_: int) -> Optional[SupportTicket]:
    """Return SupportTicket by primary key (or None)."""
    return db.get(SupportTicket, id_)

def list_support_tickets(db: Session, limit: int = 100) -> List[SupportTicket]:
    """Return up to ``limit`` SupportTicket rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SupportTicket, db, limit)

def list_support_tickets_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of support tickets (scale-ready)."""
    return _keyset_page(SupportTicket, db, cursor, page_size)

def get_support_ticket_reply_by_id(db: Session, id_: int) -> Optional[SupportTicketReply]:
    """Return SupportTicketReply by primary key (or None)."""
    return db.get(SupportTicketReply, id_)

def list_support_ticket_replys(db: Session, limit: int = 100) -> List[SupportTicketReply]:
    """Return up to ``limit`` SupportTicketReply rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SupportTicketReply, db, limit)

def list_support_ticket_replys_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of support ticket replies (scale-ready)."""
    return _keyset_page(SupportTicketReply, db, cursor, page_size)

def get_ticket_attachment_by_id(db: Session, id_: int) -> Optional[TicketAttachment]:
    """Return TicketAttachment by primary key (or None)."""
    return db.get(TicketAttachment, id_)

def list_ticket_attachments(db: Session, limit: int = 100) -> List[TicketAttachment]:
    """Return up to ``limit`` TicketAttachment rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(TicketAttachment, db, limit)

def list_ticket_attachments_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ticket attachments (scale-ready)."""
    return _keyset_page(TicketAttachment, db, cursor, page_size)

def get_city_distance_matrix_by_id(db: Session, id_: int) -> Optional[CityDistanceMatrix]:
    """Return CityDistanceMatrix by primary key (or None)."""
    return db.get(CityDistanceMatrix, id_)

def list_city_distance_matrixs(db: Session, limit: int = 100) -> List[CityDistanceMatrix]:
    """Return up to ``limit`` CityDistanceMatrix rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CityDistanceMatrix, db, limit)

def list_city_distance_matrixs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of city distance matrices (scale-ready)."""
    return _keyset_page(CityDistanceMatrix, db, cursor, page_size)

def get_executive_news_by_id(db: Session, id_: int) -> Optional[ExecutiveNews]:
    """Return ExecutiveNews by primary key (or None)."""
    return db.get(ExecutiveNews, id_)

def list_executive_newss(db: Session, limit: int = 100) -> List[ExecutiveNews]:
    """Return up to ``limit`` ExecutiveNews rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ExecutiveNews, db, limit)

def list_executive_newss_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of executive news (scale-ready)."""
    return _keyset_page(ExecutiveNews, db, cursor, page_size)

def get_user_browsing_history_by_id(db: Session, id_: int) -> Optional[UserBrowsingHistory]:
    """Return UserBrowsingHistory by primary key (or None)."""
    return db.get(UserBrowsingHistory, id_)

def list_user_browsing_historys(db: Session, limit: int = 100) -> List[UserBrowsingHistory]:
    """Return up to ``limit`` UserBrowsingHistory rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(UserBrowsingHistory, db, limit)

def list_user_browsing_historys_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of user browsing history (scale-ready)."""
    return _keyset_page(UserBrowsingHistory, db, cursor, page_size)

def get_system_health_event_by_id(db: Session, id_: int) -> Optional[SystemHealthEvent]:
    """Return SystemHealthEvent by primary key (or None)."""
    return db.get(SystemHealthEvent, id_)

def list_system_health_events(db: Session, limit: int = 100) -> List[SystemHealthEvent]:
    """Return up to ``limit`` SystemHealthEvent rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SystemHealthEvent, db, limit)

def list_system_health_events_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of system health events (scale-ready)."""
    return _keyset_page(SystemHealthEvent, db, cursor, page_size)

def get_user_session_by_id(db: Session, id_: int) -> Optional[UserSession]:
    """Return UserSession by primary key (or None)."""
    return db.get(UserSession, id_)

def list_user_sessions(db: Session, limit: int = 100) -> List[UserSession]:
    """Return up to ``limit`` UserSession rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(UserSession, db, limit)

def list_user_sessions_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of user sessions (scale-ready)."""
    return _keyset_page(UserSession, db, cursor, page_size)

def get_command_center_view_by_id(db: Session, id_: int) -> Optional[CommandCenterView]:
    """Return CommandCenterView by primary key (or None)."""
    return db.get(CommandCenterView, id_)

def list_command_center_views(db: Session, limit: int = 100) -> List[CommandCenterView]:
    """Return up to ``limit`` CommandCenterView rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CommandCenterView, db, limit)

def list_command_center_views_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of command center views (scale-ready)."""
    return _keyset_page(CommandCenterView, db, cursor, page_size)

def get_news_source_by_id(db: Session, id_: int) -> Optional[NewsSource]:
    """Return NewsSource by primary key (or None)."""
    return db.get(NewsSource, id_)

def list_news_sources(db: Session, limit: int = 100) -> List[NewsSource]:
    """Return up to ``limit`` NewsSource rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(NewsSource, db, limit)

def list_news_sources_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of news sources (scale-ready)."""
    return _keyset_page(NewsSource, db, cursor, page_size)

def get_news_article_by_id(db: Session, id_: int) -> Optional[NewsArticle]:
    """Return NewsArticle by primary key (or None)."""
    return db.get(NewsArticle, id_)

def list_news_articles(db: Session, limit: int = 100) -> List[NewsArticle]:
    """Return up to ``limit`` NewsArticle rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(NewsArticle, db, limit)

def list_news_articles_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of news articles (scale-ready)."""
    return _keyset_page(NewsArticle, db, cursor, page_size)

def get_internal_notice_by_id(db: Session, id_: int) -> Optional[InternalNotice]:
    """Return InternalNotice by primary key (or None)."""
    return db.get(InternalNotice, id_)

def list_internal_notices(db: Session, limit: int = 100) -> List[InternalNotice]:
    """Return up to ``limit`` InternalNotice rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(InternalNotice, db, limit)

def list_internal_notices_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of internal notices (scale-ready)."""
    return _keyset_page(InternalNotice, db, cursor, page_size)

def get_predictive_simulation_by_id(db: Session, id_: int) -> Optional[PredictiveSimulation]:
    """Return PredictiveSimulation by primary key (or None)."""
    return db.get(PredictiveSimulation, id_)

def list_predictive_simulations(db: Session, limit: int = 100) -> List[PredictiveSimulation]:
    """Return up to ``limit`` PredictiveSimulation rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PredictiveSimulation, db, limit)

def list_predictive_simulations_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of predictive simulations (scale-ready)."""
    return _keyset_page(PredictiveSimulation, db, cursor, page_size)

def get_alert_escalation_rule_by_id(db: Session, id_: int) -> Optional[AlertEscalationRule]:
    """Return AlertEscalationRule by primary key (or None)."""
    return db.get(AlertEscalationRule, id_)

def list_alert_escalation_rules(db: Session, limit: int = 100) -> List[AlertEscalationRule]:
    """Return up to ``limit`` AlertEscalationRule rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(AlertEscalationRule, db, limit)

def list_alert_escalation_rules_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of alert escalation rules (scale-ready)."""
    return _keyset_page(AlertEscalationRule, db, cursor, page_size)

def get_entity_chat_thread_by_id(db: Session, id_: int) -> Optional[EntityChatThread]:
    """Return EntityChatThread by primary key (or None)."""
    return db.get(EntityChatThread, id_)

def list_entity_chat_threads(db: Session, limit: int = 100) -> List[EntityChatThread]:
    """Return up to ``limit`` EntityChatThread rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EntityChatThread, db, limit)

def list_entity_chat_threads_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of entity chat threads (scale-ready)."""
    return _keyset_page(EntityChatThread, db, cursor, page_size)

def get_entity_chat_message_by_id(db: Session, id_: int) -> Optional[EntityChatMessage]:
    """Return EntityChatMessage by primary key (or None)."""
    return db.get(EntityChatMessage, id_)

def list_entity_chat_messages(db: Session, limit: int = 100) -> List[EntityChatMessage]:
    """Return up to ``limit`` EntityChatMessage rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EntityChatMessage, db, limit)

def list_entity_chat_messages_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of entity chat messages (scale-ready)."""
    return _keyset_page(EntityChatMessage, db, cursor, page_size)

def get_video_room_by_id(db: Session, id_: int) -> Optional[VideoRoom]:
    """Return VideoRoom by primary key (or None)."""
    return db.get(VideoRoom, id_)

def list_video_rooms(db: Session, limit: int = 100) -> List[VideoRoom]:
    """Return up to ``limit`` VideoRoom rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(VideoRoom, db, limit)

def list_video_rooms_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of video rooms (scale-ready)."""
    return _keyset_page(VideoRoom, db, cursor, page_size)

def get_video_room_participant_by_id(db: Session, id_: int) -> Optional[VideoRoomParticipant]:
    """Return VideoRoomParticipant by primary key (or None)."""
    return db.get(VideoRoomParticipant, id_)

def list_video_room_participants(db: Session, limit: int = 100) -> List[VideoRoomParticipant]:
    """Return up to ``limit`` VideoRoomParticipant rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(VideoRoomParticipant, db, limit)

def list_video_room_participants_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of video room participants (scale-ready)."""
    return _keyset_page(VideoRoomParticipant, db, cursor, page_size)

def get_video_room_recording_by_id(db: Session, id_: int) -> Optional[VideoRoomRecording]:
    """Return VideoRoomRecording by primary key (or None)."""
    return db.get(VideoRoomRecording, id_)

def list_video_room_recordings(db: Session, limit: int = 100) -> List[VideoRoomRecording]:
    """Return up to ``limit`` VideoRoomRecording rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(VideoRoomRecording, db, limit)

def list_video_room_recordings_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of video room recordings (scale-ready)."""
    return _keyset_page(VideoRoomRecording, db, cursor, page_size)

def get_direct_chat_room_by_id(db: Session, id_: int) -> Optional[DirectChatRoom]:
    """Return DirectChatRoom by primary key (or None)."""
    return db.get(DirectChatRoom, id_)

def list_direct_chat_rooms(db: Session, limit: int = 100) -> List[DirectChatRoom]:
    """Return up to ``limit`` DirectChatRoom rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(DirectChatRoom, db, limit)

def list_direct_chat_rooms_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of direct chat rooms (scale-ready)."""
    return _keyset_page(DirectChatRoom, db, cursor, page_size)

def get_direct_chat_message_by_id(db: Session, id_: int) -> Optional[DirectChatMessage]:
    """Return DirectChatMessage by primary key (or None)."""
    return db.get(DirectChatMessage, id_)

def list_direct_chat_messages(db: Session, limit: int = 100) -> List[DirectChatMessage]:
    """Return up to ``limit`` DirectChatMessage rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(DirectChatMessage, db, limit)

def list_direct_chat_messages_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of direct chat messages (scale-ready)."""
    return _keyset_page(DirectChatMessage, db, cursor, page_size)

def get_group_chat_room_by_id(db: Session, id_: int) -> Optional[GroupChatRoom]:
    """Return GroupChatRoom by primary key (or None)."""
    return db.get(GroupChatRoom, id_)

def list_group_chat_rooms(db: Session, limit: int = 100) -> List[GroupChatRoom]:
    """Return up to ``limit`` GroupChatRoom rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(GroupChatRoom, db, limit)

def list_group_chat_rooms_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of group chat rooms (scale-ready)."""
    return _keyset_page(GroupChatRoom, db, cursor, page_size)

def get_group_chat_member_by_id(db: Session, id_: int) -> Optional[GroupChatMember]:
    """Return GroupChatMember by primary key (or None)."""
    return db.get(GroupChatMember, id_)

def list_group_chat_members(db: Session, limit: int = 100) -> List[GroupChatMember]:
    """Return up to ``limit`` GroupChatMember rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(GroupChatMember, db, limit)

def list_group_chat_members_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of group chat members (scale-ready)."""
    return _keyset_page(GroupChatMember, db, cursor, page_size)

def get_group_chat_message_by_id(db: Session, id_: int) -> Optional[GroupChatMessage]:
    """Return GroupChatMessage by primary key (or None)."""
    return db.get(GroupChatMessage, id_)

def list_group_chat_messages(db: Session, limit: int = 100) -> List[GroupChatMessage]:
    """Return up to ``limit`` GroupChatMessage rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(GroupChatMessage, db, limit)

def list_group_chat_messages_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of group chat messages (scale-ready)."""
    return _keyset_page(GroupChatMessage, db, cursor, page_size)

def get_shift_handover_session_by_id(db: Session, id_: int) -> Optional[ShiftHandoverSession]:
    """Return ShiftHandoverSession by primary key (or None)."""
    return db.get(ShiftHandoverSession, id_)

def list_shift_handover_sessions(db: Session, limit: int = 100) -> List[ShiftHandoverSession]:
    """Return up to ``limit`` ShiftHandoverSession rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ShiftHandoverSession, db, limit)

def list_shift_handover_sessions_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of shift handover sessions (scale-ready)."""
    return _keyset_page(ShiftHandoverSession, db, cursor, page_size)

def get_shift_handover_task_by_id(db: Session, id_: int) -> Optional[ShiftHandoverTask]:
    """Return ShiftHandoverTask by primary key (or None)."""
    return db.get(ShiftHandoverTask, id_)

def list_shift_handover_tasks(db: Session, limit: int = 100) -> List[ShiftHandoverTask]:
    """Return up to ``limit`` ShiftHandoverTask rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ShiftHandoverTask, db, limit)

def list_shift_handover_tasks_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of shift handover tasks (scale-ready)."""
    return _keyset_page(ShiftHandoverTask, db, cursor, page_size)

def get_escalation_s_l_a_rule_by_id(db: Session, id_: int) -> Optional[EscalationSLARule]:
    """Return EscalationSLARule by primary key (or None)."""
    return db.get(EscalationSLARule, id_)

def list_escalation_s_l_a_rules(db: Session, limit: int = 100) -> List[EscalationSLARule]:
    """Return up to ``limit`` EscalationSLARule rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EscalationSLARule, db, limit)

def list_escalation_s_l_a_rules_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of escalation SLA rules (scale-ready)."""
    return _keyset_page(EscalationSLARule, db, cursor, page_size)

def get_escalation_s_l_a_log_by_id(db: Session, id_: int) -> Optional[EscalationSLALog]:
    """Return EscalationSLALog by primary key (or None)."""
    return db.get(EscalationSLALog, id_)

def list_escalation_s_l_a_logs(db: Session, limit: int = 100) -> List[EscalationSLALog]:
    """Return up to ``limit`` EscalationSLALog rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EscalationSLALog, db, limit)

def list_escalation_s_l_a_logs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of escalation SLA logs (scale-ready)."""
    return _keyset_page(EscalationSLALog, db, cursor, page_size)

def get_onboarding_pipeline_by_id(db: Session, id_: int) -> Optional[OnboardingPipeline]:
    """Return OnboardingPipeline by primary key (or None)."""
    return db.get(OnboardingPipeline, id_)

def list_onboarding_pipelines(db: Session, limit: int = 100) -> List[OnboardingPipeline]:
    """Return up to ``limit`` OnboardingPipeline rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(OnboardingPipeline, db, limit)

def list_onboarding_pipelines_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of onboarding pipelines (scale-ready)."""
    return _keyset_page(OnboardingPipeline, db, cursor, page_size)

def get_onboarding_step_by_id(db: Session, id_: int) -> Optional[OnboardingStep]:
    """Return OnboardingStep by primary key (or None)."""
    return db.get(OnboardingStep, id_)

def list_onboarding_steps(db: Session, limit: int = 100) -> List[OnboardingStep]:
    """Return up to ``limit`` OnboardingStep rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(OnboardingStep, db, limit)

def list_onboarding_steps_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of onboarding steps (scale-ready)."""
    return _keyset_page(OnboardingStep, db, cursor, page_size)

def get_document_verification_by_id(db: Session, id_: int) -> Optional[DocumentVerification]:
    """Return DocumentVerification by primary key (or None)."""
    return db.get(DocumentVerification, id_)

def list_document_verifications(db: Session, limit: int = 100) -> List[DocumentVerification]:
    """Return up to ``limit`` DocumentVerification rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(DocumentVerification, db, limit)

def list_document_verifications_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of document verifications (scale-ready)."""
    return _keyset_page(DocumentVerification, db, cursor, page_size)

def get_o_c_r_result_by_id(db: Session, id_: int) -> Optional[OCRResult]:
    """Return OCRResult by primary key (or None)."""
    return db.get(OCRResult, id_)

def list_o_c_r_results(db: Session, limit: int = 100) -> List[OCRResult]:
    """Return up to ``limit`` OCRResult rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(OCRResult, db, limit)

def list_o_c_r_results_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of OCR results (scale-ready)."""
    return _keyset_page(OCRResult, db, cursor, page_size)

def get_k_y_c_verification_by_id(db: Session, id_: int) -> Optional[KYCVerification]:
    """Return KYCVerification by primary key (or None)."""
    return db.get(KYCVerification, id_)

def list_k_y_c_verifications(db: Session, limit: int = 100) -> List[KYCVerification]:
    """Return up to ``limit`` KYCVerification rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(KYCVerification, db, limit)

def list_k_y_c_verifications_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of KYC verifications (scale-ready)."""
    return _keyset_page(KYCVerification, db, cursor, page_size)

def get_otp_code_by_id(db: Session, id_: int) -> Optional[OtpCode]:
    """Return OtpCode by primary key (or None)."""
    return db.get(OtpCode, id_)

def list_otp_codes(db: Session, limit: int = 100) -> List[OtpCode]:
    """Return up to ``limit`` OtpCode rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(OtpCode, db, limit)

def list_otp_codes_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of OTP codes (scale-ready)."""
    return _keyset_page(OtpCode, db, cursor, page_size)

def get_social_identity_by_id(db: Session, id_: int) -> Optional[SocialIdentity]:
    """Return SocialIdentity by primary key (or None)."""
    return db.get(SocialIdentity, id_)

def list_social_identitys(db: Session, limit: int = 100) -> List[SocialIdentity]:
    """Return up to ``limit`` SocialIdentity rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SocialIdentity, db, limit)

def list_social_identitys_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of social identities (scale-ready)."""
    return _keyset_page(SocialIdentity, db, cursor, page_size)

def get_user_by_id(db: Session, id_: int) -> Optional[User]:
    """Return User by primary key (or None)."""
    return db.get(User, id_)

def list_users(db: Session, limit: int = 100) -> List[User]:
    """Return up to ``limit`` User rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(User, db, limit)

def list_users_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of users (scale-ready, the global user hub)."""
    return _keyset_page(User, db, cursor, page_size)

def get_user_login_history_by_id(db: Session, id_: int) -> Optional[UserLoginHistory]:
    """Return UserLoginHistory by primary key (or None)."""
    return db.get(UserLoginHistory, id_)

def list_user_login_historys(db: Session, limit: int = 100) -> List[UserLoginHistory]:
    """Return up to ``limit`` UserLoginHistory rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(UserLoginHistory, db, limit)

def list_user_login_historys_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of user login history (scale-ready)."""
    return _keyset_page(UserLoginHistory, db, cursor, page_size)

def get_user_device_by_id(db: Session, id_: int) -> Optional[UserDevice]:
    """Return UserDevice by primary key (or None)."""
    return db.get(UserDevice, id_)

def list_user_devices(db: Session, limit: int = 100) -> List[UserDevice]:
    """Return up to ``limit`` UserDevice rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(UserDevice, db, limit)

def list_user_devices_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of user devices (scale-ready)."""
    return _keyset_page(UserDevice, db, cursor, page_size)

def get_referral_by_id(db: Session, id_: int) -> Optional[Referral]:
    """Return Referral by primary key (or None)."""
    return db.get(Referral, id_)

def list_referrals(db: Session, limit: int = 100) -> List[Referral]:
    """Return up to ``limit`` Referral rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Referral, db, limit)

def list_referrals_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of referrals (scale-ready)."""
    return _keyset_page(Referral, db, cursor, page_size)

def get_referral_point_event_by_id(db: Session, id_: int) -> Optional[ReferralPointEvent]:
    """Return ReferralPointEvent by primary key (or None)."""
    return db.get(ReferralPointEvent, id_)

def list_referral_point_events(db: Session, limit: int = 100) -> List[ReferralPointEvent]:
    """Return up to ``limit`` ReferralPointEvent rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ReferralPointEvent, db, limit)

def list_referral_point_events_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of referral point events (scale-ready)."""
    return _keyset_page(ReferralPointEvent, db, cursor, page_size)

def get_password_reset_token_by_id(db: Session, id_: int) -> Optional[PasswordResetToken]:
    """Return PasswordResetToken by primary key (or None)."""
    return db.get(PasswordResetToken, id_)

def list_password_reset_tokens(db: Session, limit: int = 100) -> List[PasswordResetToken]:
    """Return up to ``limit`` PasswordResetToken rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PasswordResetToken, db, limit)

def list_password_reset_tokens_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of password reset tokens (scale-ready)."""
    return _keyset_page(PasswordResetToken, db, cursor, page_size)

def get_email_verification_token_by_id(db: Session, id_: int) -> Optional[EmailVerificationToken]:
    """Return EmailVerificationToken by primary key (or None)."""
    return db.get(EmailVerificationToken, id_)

def list_email_verification_tokens(db: Session, limit: int = 100) -> List[EmailVerificationToken]:
    """Return up to ``limit`` EmailVerificationToken rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmailVerificationToken, db, limit)

def list_email_verification_tokens_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of email verification tokens (scale-ready)."""
    return _keyset_page(EmailVerificationToken, db, cursor, page_size)

def get_revoked_token_by_id(db: Session, id_: int) -> Optional[RevokedToken]:
    """Return RevokedToken by primary key (or None)."""
    return db.get(RevokedToken, id_)

def list_revoked_tokens(db: Session, limit: int = 100) -> List[RevokedToken]:
    """Return up to ``limit`` RevokedToken rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(RevokedToken, db, limit)

def list_revoked_tokens_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of revoked tokens (scale-ready)."""
    return _keyset_page(RevokedToken, db, cursor, page_size)

# --- P11 re-exports (Law 3 sanctioned read surface) ---
from domains.accounts.models.core import Address, CartItem, CityDistanceMatrix
from domains.accounts.models.user import Referral, User
# Read helpers re-exported from owning services (Law 3: cross-domain READ surface only;
# writes were removed — call the owning accounts service directly).
from domains.accounts.services.customer_coupons_create_service import list_coupons
# --- P11.5 re-exports (orders cross-domain repointing) ---
from domains.accounts.services.customer_coupons_mgmt_service import validate_coupon
