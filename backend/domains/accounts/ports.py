"""accounts domain - sanctioned cross-domain READ surface (ports).

Per NEW_STRUCTURE.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these functions instead
of importing ``domains.accounts.models`` or ``domains.accounts.services`` directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via ``rbac``).

A3 / RESOLVER §26 ACC-01 cleanup: this file previously imported 30+ models
spanning security, hr, and the god-module ``core`` hub. Per Law 3, only
accounts-owned models live here. Cross-domain helpers were moved:

  * security.DocumentVerification / KYCVerification / AlertEscalationRule
      -> ``domains.security.ports``
  * hr.OnboardingPipeline / OnboardingStep
      -> ``domains.hr.ports``
  * The ``core`` models that were actually hr-shift / security composites
    (ShiftHandoverSession, ShiftHandoverTask, EscalationSLARule, EscalationSLALog)
    remain here ONLY because they are owned by accounts (see
    ``domains.accounts.models.core``); they are NOT re-homed.

Keyset (cursor) pagination: ``list_*`` returns a plain ``List`` (back-compat);
``*_page`` companions return a ``CursorPage`` for scale-ready cursor paging
(100Ks-concurrent-user path, no OFFSET on hot lists).
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from infrastructure.utils.pagination import (
    CursorPage,
    MAX_PAGE_SIZE,
    cursor_paginate_asc,
)

from domains.accounts.models.core import (
    Address,
    Cart,
    CartItem,
    CityDistanceMatrix,
    CommandCenterView,
    DirectChatMessage,
    DirectChatRoom,
    EntityChatMessage,
    EntityChatThread,
    EscalationSLALog,
    EscalationSLARule,
    ExecutiveNews,
    GroupChatMember,
    GroupChatMessage,
    GroupChatRoom,
    InternalNotice,
    NewsArticle,
    NewsSource,
    PredictiveSimulation,
    ShiftHandoverSession,
    ShiftHandoverTask,
    SupportTicket,
    SupportTicketReply,
    SystemHealthEvent,
    TicketAttachment,
    UserBrowsingHistory,
    UserSession,
    VideoRoom,
    VideoRoomParticipant,
    VideoRoomRecording,
    AuditLog,
)
from domains.accounts.models.mfa_factor import MfaFactor
from domains.accounts.models.onboarding import OCRResult
from domains.accounts.models.otp import OtpCode
from domains.accounts.models.social import SocialIdentity
from domains.accounts.models.user import (
    EmailVerificationToken,
    PasswordResetToken,
    RevokedToken,
    User,
    UserDevice,
    UserLoginHistory,
)

# Referral / ReferralPointEvent: owned by customers domain; re-exported via
# the accounts.models.core lazy __getattr__ so ports.py stays free of
# cross-domain imports at module load time (Law 3).
from domains.accounts.models import core as _accounts_core
Referral = _accounts_core.Referral
ReferralPointEvent = _accounts_core.ReferralPointEvent
del _accounts_core


# --- Keyset (cursor) pagination helpers (diagram §6: NEVER OFFSET on hot lists) ---

def _keyset_list(model, db: Session, limit: int = 100) -> list:
    """Backward-compatible plain list sourced via keyset (no OFFSET)."""
    return cursor_paginate_asc(db.query(model), page_size=limit).items


def _keyset_page(model, db: Session, cursor: Optional[str] = None,
                 page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page over ``model`` (scale-ready, no OFFSET)."""
    return cursor_paginate_asc(db.query(model), cursor=cursor, page_size=page_size)


# --- Address ---

def get_address_by_id(db: Session, id_: int) -> Optional[Address]:
    """Return Address by primary key (or None)."""
    return db.get(Address, id_)

def list_addresses(db: Session, limit: int = 100) -> List[Address]:
    """Return up to ``limit`` Address rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Address, db, limit)

def list_addresses_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of addresses (scale-ready)."""
    return _keyset_page(Address, db, cursor, page_size)


# --- Cart ---

def get_cart_by_id(db: Session, id_: int) -> Optional[Cart]:
    """Return Cart by primary key (or None)."""
    return db.get(Cart, id_)

def list_carts(db: Session, limit: int = 100) -> List[Cart]:
    """Return up to ``limit`` Cart rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Cart, db, limit)

def list_carts_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of carts (scale-ready)."""
    return _keyset_page(Cart, db, cursor, page_size)


# --- CartItem ---

def get_cart_item_by_id(db: Session, id_: int) -> Optional[CartItem]:
    """Return CartItem by primary key (or None)."""
    return db.get(CartItem, id_)

def list_cart_items(db: Session, limit: int = 100) -> List[CartItem]:
    """Return up to ``limit`` CartItem rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CartItem, db, limit)

def list_cart_items_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of cart items (scale-ready)."""
    return _keyset_page(CartItem, db, cursor, page_size)


# --- AuditLog ---

def get_audit_log_by_id(db: Session, id_: int) -> Optional[AuditLog]:
    """Return AuditLog by primary key (or None)."""
    return db.get(AuditLog, id_)

def list_audit_logs(db: Session, limit: int = 100) -> List[AuditLog]:
    """Return up to ``limit`` AuditLog rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(AuditLog, db, limit)

def list_audit_logs_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of audit logs (scale-ready)."""
    return _keyset_page(AuditLog, db, cursor, page_size)


# --- SupportTicket / Reply / Attachment ---

def get_support_ticket_by_id(db: Session, id_: int) -> Optional[SupportTicket]:
    """Return SupportTicket by primary key (or None)."""
    return db.get(SupportTicket, id_)

def list_support_tickets(db: Session, limit: int = 100) -> List[SupportTicket]:
    """Return up to ``limit`` SupportTicket rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SupportTicket, db, limit)

def list_support_tickets_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of support tickets (scale-ready)."""
    return _keyset_page(SupportTicket, db, cursor, page_size)


def get_support_ticket_reply_by_id(db: Session, id_: int) -> Optional[SupportTicketReply]:
    """Return SupportTicketReply by primary key (or None)."""
    return db.get(SupportTicketReply, id_)

def list_support_ticket_replies(db: Session, limit: int = 100) -> List[SupportTicketReply]:
    """Return up to ``limit`` SupportTicketReply rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SupportTicketReply, db, limit)

def list_support_ticket_replies_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of support ticket replies (scale-ready)."""
    return _keyset_page(SupportTicketReply, db, cursor, page_size)


def get_ticket_attachment_by_id(db: Session, id_: int) -> Optional[TicketAttachment]:
    """Return TicketAttachment by primary key (or None)."""
    return db.get(TicketAttachment, id_)

def list_ticket_attachments(db: Session, limit: int = 100) -> List[TicketAttachment]:
    """Return up to ``limit`` TicketAttachment rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(TicketAttachment, db, limit)

def list_ticket_attachments_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of ticket attachments (scale-ready)."""
    return _keyset_page(TicketAttachment, db, cursor, page_size)


# --- CityDistanceMatrix ---

def get_city_distance_matrix_by_id(db: Session, id_: int) -> Optional[CityDistanceMatrix]:
    """Return CityDistanceMatrix by primary key (or None)."""
    return db.get(CityDistanceMatrix, id_)

def list_city_distance_matrixs(db: Session, limit: int = 100) -> List[CityDistanceMatrix]:
    """Return up to ``limit`` CityDistanceMatrix rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CityDistanceMatrix, db, limit)

def list_city_distance_matrixs_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of city distance matrices (scale-ready)."""
    return _keyset_page(CityDistanceMatrix, db, cursor, page_size)


# --- ExecutiveNews ---

def get_executive_news_by_id(db: Session, id_: int) -> Optional[ExecutiveNews]:
    """Return ExecutiveNews by primary key (or None)."""
    return db.get(ExecutiveNews, id_)

def list_executive_newss(db: Session, limit: int = 100) -> List[ExecutiveNews]:
    """Return up to ``limit`` ExecutiveNews rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ExecutiveNews, db, limit)

def list_executive_newss_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of executive news (scale-ready)."""
    return _keyset_page(ExecutiveNews, db, cursor, page_size)


# --- UserBrowsingHistory ---

def get_user_browsing_history_by_id(db: Session, id_: int) -> Optional[UserBrowsingHistory]:
    """Return UserBrowsingHistory by primary key (or None)."""
    return db.get(UserBrowsingHistory, id_)

def list_user_browsing_historys(db: Session, limit: int = 100) -> List[UserBrowsingHistory]:
    """Return up to ``limit`` UserBrowsingHistory rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(UserBrowsingHistory, db, limit)

def list_user_browsing_historys_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of user browsing history (scale-ready)."""
    return _keyset_page(UserBrowsingHistory, db, cursor, page_size)


# --- SystemHealthEvent ---

def get_system_health_event_by_id(db: Session, id_: int) -> Optional[SystemHealthEvent]:
    """Return SystemHealthEvent by primary key (or None)."""
    return db.get(SystemHealthEvent, id_)

def list_system_health_events(db: Session, limit: int = 100) -> List[SystemHealthEvent]:
    """Return up to ``limit`` SystemHealthEvent rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SystemHealthEvent, db, limit)

def list_system_health_events_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of system health events (scale-ready)."""
    return _keyset_page(SystemHealthEvent, db, cursor, page_size)


# --- UserSession ---

def get_user_session_by_id(db: Session, id_: int) -> Optional[UserSession]:
    """Return UserSession by primary key (or None)."""
    return db.get(UserSession, id_)

def list_user_sessions(db: Session, limit: int = 100) -> List[UserSession]:
    """Return up to ``limit`` UserSession rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(UserSession, db, limit)

def list_user_sessions_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of user sessions (scale-ready)."""
    return _keyset_page(UserSession, db, cursor, page_size)


# --- CommandCenterView ---

def get_command_center_view_by_id(db: Session, id_: int) -> Optional[CommandCenterView]:
    """Return CommandCenterView by primary key (or None)."""
    return db.get(CommandCenterView, id_)

def list_command_center_views(db: Session, limit: int = 100) -> List[CommandCenterView]:
    """Return up to ``limit`` CommandCenterView rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CommandCenterView, db, limit)

def list_command_center_views_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of command center views (scale-ready)."""
    return _keyset_page(CommandCenterView, db, cursor, page_size)


# --- NewsSource / NewsArticle / InternalNotice ---

def get_news_source_by_id(db: Session, id_: int) -> Optional[NewsSource]:
    """Return NewsSource by primary key (or None)."""
    return db.get(NewsSource, id_)

def list_news_sources(db: Session, limit: int = 100) -> List[NewsSource]:
    """Return up to ``limit`` NewsSource rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(NewsSource, db, limit)

def list_news_sources_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of news sources (scale-ready)."""
    return _keyset_page(NewsSource, db, cursor, page_size)


def get_news_article_by_id(db: Session, id_: int) -> Optional[NewsArticle]:
    """Return NewsArticle by primary key (or None)."""
    return db.get(NewsArticle, id_)

def list_news_articles(db: Session, limit: int = 100) -> List[NewsArticle]:
    """Return up to ``limit`` NewsArticle rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(NewsArticle, db, limit)

def list_news_articles_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of news articles (scale-ready)."""
    return _keyset_page(NewsArticle, db, cursor, page_size)


def get_internal_notice_by_id(db: Session, id_: int) -> Optional[InternalNotice]:
    """Return InternalNotice by primary key (or None)."""
    return db.get(InternalNotice, id_)

def list_internal_notices(db: Session, limit: int = 100) -> List[InternalNotice]:
    """Return up to ``limit`` InternalNotice rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(InternalNotice, db, limit)

def list_internal_notices_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of internal notices (scale-ready)."""
    return _keyset_page(InternalNotice, db, cursor, page_size)


# --- PredictiveSimulation ---

def get_predictive_simulation_by_id(db: Session, id_: int) -> Optional[PredictiveSimulation]:
    """Return PredictiveSimulation by primary key (or None)."""
    return db.get(PredictiveSimulation, id_)

def list_predictive_simulations(db: Session, limit: int = 100) -> List[PredictiveSimulation]:
    """Return up to ``limit`` PredictiveSimulation rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PredictiveSimulation, db, limit)

def list_predictive_simulations_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of predictive simulations (scale-ready)."""
    return _keyset_page(PredictiveSimulation, db, cursor, page_size)


# --- EntityChat ---

def get_entity_chat_thread_by_id(db: Session, id_: int) -> Optional[EntityChatThread]:
    """Return EntityChatThread by primary key (or None)."""
    return db.get(EntityChatThread, id_)

def list_entity_chat_threads(db: Session, limit: int = 100) -> List[EntityChatThread]:
    """Return up to ``limit`` EntityChatThread rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EntityChatThread, db, limit)

def list_entity_chat_threads_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of entity chat threads (scale-ready)."""
    return _keyset_page(EntityChatThread, db, cursor, page_size)


def get_entity_chat_message_by_id(db: Session, id_: int) -> Optional[EntityChatMessage]:
    """Return EntityChatMessage by primary key (or None)."""
    return db.get(EntityChatMessage, id_)

def list_entity_chat_messages(db: Session, limit: int = 100) -> List[EntityChatMessage]:
    """Return up to ``limit`` EntityChatMessage rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EntityChatMessage, db, limit)

def list_entity_chat_messages_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of entity chat messages (scale-ready)."""
    return _keyset_page(EntityChatMessage, db, cursor, page_size)


# --- VideoRoom ---

def get_video_room_by_id(db: Session, id_: int) -> Optional[VideoRoom]:
    """Return VideoRoom by primary key (or None)."""
    return db.get(VideoRoom, id_)

def list_video_rooms(db: Session, limit: int = 100) -> List[VideoRoom]:
    """Return up to ``limit`` VideoRoom rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(VideoRoom, db, limit)

def list_video_rooms_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of video rooms (scale-ready)."""
    return _keyset_page(VideoRoom, db, cursor, page_size)


def get_video_room_participant_by_id(db: Session, id_: int) -> Optional[VideoRoomParticipant]:
    """Return VideoRoomParticipant by primary key (or None)."""
    return db.get(VideoRoomParticipant, id_)

def list_video_room_participants(db: Session, limit: int = 100) -> List[VideoRoomParticipant]:
    """Return up to ``limit`` VideoRoomParticipant rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(VideoRoomParticipant, db, limit)

def list_video_room_participants_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of video room participants (scale-ready)."""
    return _keyset_page(VideoRoomParticipant, db, cursor, page_size)


def get_video_room_recording_by_id(db: Session, id_: int) -> Optional[VideoRoomRecording]:
    """Return VideoRoomRecording by primary key (or None)."""
    return db.get(VideoRoomRecording, id_)

def list_video_room_recordings(db: Session, limit: int = 100) -> List[VideoRoomRecording]:
    """Return up to ``limit`` VideoRoomRecording rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(VideoRoomRecording, db, limit)

def list_video_room_recordings_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of video room recordings (scale-ready)."""
    return _keyset_page(VideoRoomRecording, db, cursor, page_size)


# --- DirectChat ---

def get_direct_chat_room_by_id(db: Session, id_: int) -> Optional[DirectChatRoom]:
    """Return DirectChatRoom by primary key (or None)."""
    return db.get(DirectChatRoom, id_)

def list_direct_chat_rooms(db: Session, limit: int = 100) -> List[DirectChatRoom]:
    """Return up to ``limit`` DirectChatRoom rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(DirectChatRoom, db, limit)

def list_direct_chat_rooms_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of direct chat rooms (scale-ready)."""
    return _keyset_page(DirectChatRoom, db, cursor, page_size)


def get_direct_chat_message_by_id(db: Session, id_: int) -> Optional[DirectChatMessage]:
    """Return DirectChatMessage by primary key (or None)."""
    return db.get(DirectChatMessage, id_)

def list_direct_chat_messages(db: Session, limit: int = 100) -> List[DirectChatMessage]:
    """Return up to ``limit`` DirectChatMessage rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(DirectChatMessage, db, limit)

def list_direct_chat_messages_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of direct chat messages (scale-ready)."""
    return _keyset_page(DirectChatMessage, db, cursor, page_size)


# --- GroupChat ---

def get_group_chat_room_by_id(db: Session, id_: int) -> Optional[GroupChatRoom]:
    """Return GroupChatRoom by primary key (or None)."""
    return db.get(GroupChatRoom, id_)

def list_group_chat_rooms(db: Session, limit: int = 100) -> List[GroupChatRoom]:
    """Return up to ``limit`` GroupChatRoom rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(GroupChatRoom, db, limit)

def list_group_chat_rooms_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of group chat rooms (scale-ready)."""
    return _keyset_page(GroupChatRoom, db, cursor, page_size)


def get_group_chat_member_by_id(db: Session, id_: int) -> Optional[GroupChatMember]:
    """Return GroupChatMember by primary key (or None)."""
    return db.get(GroupChatMember, id_)

def list_group_chat_members(db: Session, limit: int = 100) -> List[GroupChatMember]:
    """Return up to ``limit`` GroupChatMember rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(GroupChatMember, db, limit)

def list_group_chat_members_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of group chat members (scale-ready)."""
    return _keyset_page(GroupChatMember, db, cursor, page_size)


def get_group_chat_message_by_id(db: Session, id_: int) -> Optional[GroupChatMessage]:
    """Return GroupChatMessage by primary key (or None)."""
    return db.get(GroupChatMessage, id_)

def list_group_chat_messages(db: Session, limit: int = 100) -> List[GroupChatMessage]:
    """Return up to ``limit`` GroupChatMessage rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(GroupChatMessage, db, limit)

def list_group_chat_messages_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of group chat messages (scale-ready)."""
    return _keyset_page(GroupChatMessage, db, cursor, page_size)


# --- ShiftHandover ---

def get_shift_handover_session_by_id(db: Session, id_: int) -> Optional[ShiftHandoverSession]:
    """Return ShiftHandoverSession by primary key (or None)."""
    return db.get(ShiftHandoverSession, id_)

def list_shift_handover_sessions(db: Session, limit: int = 100) -> List[ShiftHandoverSession]:
    """Return up to ``limit`` ShiftHandoverSession rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ShiftHandoverSession, db, limit)

def list_shift_handover_sessions_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of shift handover sessions (scale-ready)."""
    return _keyset_page(ShiftHandoverSession, db, cursor, page_size)


def get_shift_handover_task_by_id(db: Session, id_: int) -> Optional[ShiftHandoverTask]:
    """Return ShiftHandoverTask by primary key (or None)."""
    return db.get(ShiftHandoverTask, id_)

def list_shift_handover_tasks(db: Session, limit: int = 100) -> List[ShiftHandoverTask]:
    """Return up to ``limit`` ShiftHandoverTask rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ShiftHandoverTask, db, limit)

def list_shift_handover_tasks_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of shift handover tasks (scale-ready)."""
    return _keyset_page(ShiftHandoverTask, db, cursor, page_size)


# --- EscalationSLA ---

def get_escalation_s_l_a_rule_by_id(db: Session, id_: int) -> Optional[EscalationSLARule]:
    """Return EscalationSLARule by primary key (or None)."""
    return db.get(EscalationSLARule, id_)

def list_escalation_s_l_a_rules(db: Session, limit: int = 100) -> List[EscalationSLARule]:
    """Return up to ``limit`` EscalationSLARule rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EscalationSLARule, db, limit)

def list_escalation_s_l_a_rules_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of escalation SLA rules (scale-ready)."""
    return _keyset_page(EscalationSLARule, db, cursor, page_size)


def get_escalation_s_l_a_log_by_id(db: Session, id_: int) -> Optional[EscalationSLALog]:
    """Return EscalationSLALog by primary key (or None)."""
    return db.get(EscalationSLALog, id_)

def list_escalation_s_l_a_logs(db: Session, limit: int = 100) -> List[EscalationSLALog]:
    """Return up to ``limit`` EscalationSLALog rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EscalationSLALog, db, limit)

def list_escalation_s_l_a_logs_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of escalation SLA logs (scale-ready)."""
    return _keyset_page(EscalationSLALog, db, cursor, page_size)


# --- OCRResult ---

def get_o_c_r_result_by_id(db: Session, id_: int) -> Optional[OCRResult]:
    """Return OCRResult by primary key (or None)."""
    return db.get(OCRResult, id_)

def list_o_c_r_results(db: Session, limit: int = 100) -> List[OCRResult]:
    """Return up to ``limit`` OCRResult rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(OCRResult, db, limit)

def list_o_c_r_results_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of OCR results (scale-ready)."""
    return _keyset_page(OCRResult, db, cursor, page_size)


# --- OtpCode ---

def get_otp_code_by_id(db: Session, id_: int) -> Optional[OtpCode]:
    """Return OtpCode by primary key (or None)."""
    return db.get(OtpCode, id_)

def list_otp_codes(db: Session, limit: int = 100) -> List[OtpCode]:
    """Return up to ``limit`` OtpCode rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(OtpCode, db, limit)

def list_otp_codes_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of OTP codes (scale-ready)."""
    return _keyset_page(OtpCode, db, cursor, page_size)


# --- SocialIdentity ---

def get_social_identity_by_id(db: Session, id_: int) -> Optional[SocialIdentity]:
    """Return SocialIdentity by primary key (or None)."""
    return db.get(SocialIdentity, id_)

def list_social_identitys(db: Session, limit: int = 100) -> List[SocialIdentity]:
    """Return up to ``limit`` SocialIdentity rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SocialIdentity, db, limit)

def list_social_identitys_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of social identities (scale-ready)."""
    return _keyset_page(SocialIdentity, db, cursor, page_size)


# --- User (the global user hub) ---

def get_user_by_id(db: Session, id_: int) -> Optional[User]:
    """Return User by primary key (or None)."""
    return db.get(User, id_)

def list_users(db: Session, limit: int = 100) -> List[User]:
    """Return up to ``limit`` User rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(User, db, limit)

def list_users_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of users (scale-ready, the global user hub)."""
    return _keyset_page(User, db, cursor, page_size)


def get_user_login_history_by_id(db: Session, id_: int) -> Optional[UserLoginHistory]:
    """Return UserLoginHistory by primary key (or None)."""
    return db.get(UserLoginHistory, id_)

def list_user_login_historys(db: Session, limit: int = 100) -> List[UserLoginHistory]:
    """Return up to ``limit`` UserLoginHistory rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(UserLoginHistory, db, limit)

def list_user_login_historys_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of user login history (scale-ready)."""
    return _keyset_page(UserLoginHistory, db, cursor, page_size)


def get_user_device_by_id(db: Session, id_: int) -> Optional[UserDevice]:
    """Return UserDevice by primary key (or None)."""
    return db.get(UserDevice, id_)

def list_user_devices(db: Session, limit: int = 100) -> List[UserDevice]:
    """Return up to ``limit`` UserDevice rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(UserDevice, db, limit)

def list_user_devices_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of user devices (scale-ready)."""
    return _keyset_page(UserDevice, db, cursor, page_size)


# --- Referral / ReferralPointEvent ---

def get_referral_by_id(db: Session, id_: int) -> Optional[Referral]:
    """Return Referral by primary key (or None)."""
    return db.get(Referral, id_)

def list_referrals(db: Session, limit: int = 100) -> List[Referral]:
    """Return up to ``limit`` Referral rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Referral, db, limit)

def list_referrals_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of referrals (scale-ready)."""
    return _keyset_page(Referral, db, cursor, page_size)


def get_referral_point_event_by_id(db: Session, id_: int) -> Optional[ReferralPointEvent]:
    """Return ReferralPointEvent by primary key (or None)."""
    return db.get(ReferralPointEvent, id_)

def list_referral_point_events(db: Session, limit: int = 100) -> List[ReferralPointEvent]:
    """Return up to ``limit`` ReferralPointEvent rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ReferralPointEvent, db, limit)

def list_referral_point_events_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of referral point events (scale-ready)."""
    return _keyset_page(ReferralPointEvent, db, cursor, page_size)


# --- Password / Email / Revoked tokens ---

def get_password_reset_token_by_id(db: Session, id_: int) -> Optional[PasswordResetToken]:
    """Return PasswordResetToken by primary key (or None)."""
    return db.get(PasswordResetToken, id_)

def list_password_reset_tokens(db: Session, limit: int = 100) -> List[PasswordResetToken]:
    """Return up to ``limit`` PasswordResetToken rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PasswordResetToken, db, limit)

def list_password_reset_tokens_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of password reset tokens (scale-ready)."""
    return _keyset_page(PasswordResetToken, db, cursor, page_size)


def get_email_verification_token_by_id(db: Session, id_: int) -> Optional[EmailVerificationToken]:
    """Return EmailVerificationToken by primary key (or None)."""
    return db.get(EmailVerificationToken, id_)

def list_email_verification_tokens(db: Session, limit: int = 100) -> List[EmailVerificationToken]:
    """Return up to ``limit`` EmailVerificationToken rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmailVerificationToken, db, limit)

def list_email_verification_tokens_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of email verification tokens (scale-ready)."""
    return _keyset_page(EmailVerificationToken, db, cursor, page_size)


def get_revoked_token_by_id(db: Session, id_: int) -> Optional[RevokedToken]:
    """Return RevokedToken by primary key (or None)."""
    return db.get(RevokedToken, id_)

def list_revoked_tokens(db: Session, limit: int = 100) -> List[RevokedToken]:
    """Return up to ``limit`` RevokedToken rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(RevokedToken, db, limit)

def list_revoked_tokens_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of revoked tokens (scale-ready)."""
    return _keyset_page(RevokedToken, db, cursor, page_size)


# --- Filtered read helpers (router-layer consolidation) ---
# These express the exact filters the customer/employee routers previously ran
# inline so callers stay free of raw ``db.query`` in the module layer.

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Return the User whose ``email`` matches (or None)."""
    return db.query(User).filter(User.email == email).first()


def list_active_user_sessions(db: Session, user_id: int) -> List[UserSession]:
    """Return non-expired UserSession rows for a user, newest first."""
    return (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id, UserSession.expires_at > db.func.now())
        .order_by(UserSession.created_at.desc())
        .all()
    )


def list_open_support_tickets_for_user(db: Session, user_id: int) -> List[SupportTicket]:
    """Return open SupportTicket rows for a user, newest first."""
    return (
        db.query(SupportTicket)
        .filter(
            SupportTicket.user_id == user_id,
            SupportTicket.status.in_(("open", "in_progress", "pending")),
        )
        .order_by(SupportTicket.created_at.desc())
        .all()
    )


# --- Service delegation (sanctioned cross-domain wrappers) ---
# These expose service-level helpers so module routers can import from
# accounts.ports without crossing into domains.accounts.services directly.

def get_referral_dashboard(current_user: dict, db: Session):
    """Sanctioned cross-domain read: referral dashboard for the current user."""
    from domains.accounts.services.auth.auth_service import get_referral_dashboard as _svc
    return _svc(current_user, db)


__all__ = [
    "Address",
    "Cart",
    "CartItem",
    "CityDistanceMatrix",
    "CommandCenterView",
    "DirectChatMessage",
    "DirectChatRoom",
    "EntityChatMessage",
    "EntityChatThread",
    "EscalationSLALog",
    "EscalationSLARule",
    "ExecutiveNews",
    "GroupChatMember",
    "GroupChatMessage",
    "GroupChatRoom",
    "InternalNotice",
    "NewsArticle",
    "NewsSource",
    "OCRResult",
    "OtpCode",
    "PredictiveSimulation",
    "ShiftHandoverSession",
    "ShiftHandoverTask",
    "SocialIdentity",
    "SupportTicket",
    "SupportTicketReply",
    "SystemHealthEvent",
    "TicketAttachment",
    "User",
    "UserBrowsingHistory",
    "UserDevice",
    "UserLoginHistory",
    "UserSession",
    "VideoRoom",
    "VideoRoomParticipant",
    "VideoRoomRecording",
    "AuditLog",
    "EmailVerificationToken",
    "MfaFactor",
    "PasswordResetToken",
    "Referral",
    "ReferralPointEvent",
    "RevokedToken",
    "get_address_by_id",
    "list_addresses",
    "list_addresses_page",
    "get_cart_by_id",
    "list_carts",
    "list_carts_page",
    "get_cart_item_by_id",
    "list_cart_items",
    "list_cart_items_page",
    "get_audit_log_by_id",
    "list_audit_logs",
    "list_audit_logs_page",
    "get_support_ticket_by_id",
    "list_support_tickets",
    "list_support_tickets_page",
    "get_support_ticket_reply_by_id",
    "list_support_ticket_replies",
    "list_support_ticket_replies_page",
    "get_ticket_attachment_by_id",
    "list_ticket_attachments",
    "list_ticket_attachments_page",
    "get_city_distance_matrix_by_id",
    "list_city_distance_matrixs",
    "list_city_distance_matrixs_page",
    "get_executive_news_by_id",
    "list_executive_newss",
    "list_executive_newss_page",
    "get_user_browsing_history_by_id",
    "list_user_browsing_historys",
    "list_user_browsing_historys_page",
    "get_system_health_event_by_id",
    "list_system_health_events",
    "list_system_health_events_page",
    "get_user_session_by_id",
    "list_user_sessions",
    "list_user_sessions_page",
    "get_command_center_view_by_id",
    "list_command_center_views",
    "list_command_center_views_page",
    "get_news_source_by_id",
    "list_news_sources",
    "list_news_sources_page",
    "get_news_article_by_id",
    "list_news_articles",
    "list_news_articles_page",
    "get_internal_notice_by_id",
    "list_internal_notices",
    "list_internal_notices_page",
    "get_predictive_simulation_by_id",
    "list_predictive_simulations",
    "list_predictive_simulations_page",
    "get_entity_chat_thread_by_id",
    "list_entity_chat_threads",
    "list_entity_chat_threads_page",
    "get_entity_chat_message_by_id",
    "list_entity_chat_messages",
    "list_entity_chat_messages_page",
    "get_video_room_by_id",
    "list_video_rooms",
    "list_video_rooms_page",
    "get_video_room_participant_by_id",
    "list_video_room_participants",
    "list_video_room_participants_page",
    "get_video_room_recording_by_id",
    "list_video_room_recordings",
    "list_video_room_recordings_page",
    "get_direct_chat_room_by_id",
    "list_direct_chat_rooms",
    "list_direct_chat_rooms_page",
    "get_direct_chat_message_by_id",
    "list_direct_chat_messages",
    "list_direct_chat_messages_page",
    "get_group_chat_room_by_id",
    "list_group_chat_rooms",
    "list_group_chat_rooms_page",
    "get_group_chat_member_by_id",
    "list_group_chat_members",
    "list_group_chat_members_page",
    "get_group_chat_message_by_id",
    "list_group_chat_messages",
    "list_group_chat_messages_page",
    "get_shift_handover_session_by_id",
    "list_shift_handover_sessions",
    "list_shift_handover_sessions_page",
    "get_shift_handover_task_by_id",
    "list_shift_handover_tasks",
    "list_shift_handover_tasks_page",
    "get_escalation_s_l_a_rule_by_id",
    "list_escalation_s_l_a_rules",
    "list_escalation_s_l_a_rules_page",
    "get_escalation_s_l_a_log_by_id",
    "list_escalation_s_l_a_logs",
    "list_escalation_s_l_a_logs_page",
    "get_o_c_r_result_by_id",
    "list_o_c_r_results",
    "list_o_c_r_results_page",
    "get_otp_code_by_id",
    "list_otp_codes",
    "list_otp_codes_page",
    "get_social_identity_by_id",
    "list_social_identitys",
    "list_social_identitys_page",
    "get_user_by_id",
    "list_users",
    "list_users_page",
    "get_user_login_history_by_id",
    "list_user_login_historys",
    "list_user_login_historys_page",
    "get_user_device_by_id",
    "list_user_devices",
    "list_user_devices_page",
    "get_referral_by_id",
    "list_referrals",
    "list_referrals_page",
    "get_referral_point_event_by_id",
    "list_referral_point_events",
    "list_referral_point_events_page",
    "get_password_reset_token_by_id",
    "list_password_reset_tokens",
    "list_password_reset_tokens_page",
    "get_email_verification_token_by_id",
    "list_email_verification_tokens",
    "list_email_verification_tokens_page",
    "get_revoked_token_by_id",
    "list_revoked_tokens",
    "list_revoked_tokens_page",
    "get_user_by_email",
    "list_active_user_sessions",
    "list_open_support_tickets_for_user",
    "get_referral_dashboard",
]

# Service re-exports (Law 3 sanctioned cross-domain surface). Modules under
# modules/supplier import these from ``domains.accounts.ports`` instead of
# reaching into the services tree directly.
# Disabled: circular import issue
# from domains.accounts.services.auth.auth_service import (  # noqa: E402, F401
#     create_supplier_profile,
# )

# --- Lazy service exports (Law 3 sanctioned cross-domain surface) ---
# Cross-domain consumers import these from ports instead of reaching
# into the services tree directly.
_LAZY_SERVICE_EXPORTS: dict[str, tuple[str, str]] = {
    "get_current_user": ("domains.accounts.services.auth.security_dependencies", "get_current_user"),
    "start_otp": ("domains.accounts.services.auth.auth_service", "start_otp"),
    "verify_otp": ("domains.accounts.services.auth.auth_service", "verify_otp"),
    "RBACService": ("domains.accounts.services.permissions.permission_service", "RBACService"),
    "get_hierarchy_permissions": ("domains.accounts.services.permissions.permission_service", "get_hierarchy_permissions"),
    "get_staff_permission_catalog": ("domains.accounts.services.permissions.permission_service", "get_staff_permission_catalog"),
    "update_role_permissions": ("domains.accounts.services.permissions.permission_service", "update_role_permissions"),
    "force_reset_password_admin": ("domains.accounts.services.users.user_management_service", "force_reset_password_admin"),
}
import importlib

def __getattr__(name: str):
    if name in _LAZY_SERVICE_EXPORTS:
        module_path, symbol = _LAZY_SERVICE_EXPORTS[name]
        mod = importlib.import_module(module_path)
        value = getattr(mod, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

