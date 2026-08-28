"""security domain - sanctioned cross-domain READ surface (ports).

Per NEW_STRUCTURE.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these functions instead
of importing ``domains.security.models`` directly.

A3 / RESOLVER §26 ACC-01 — re-export the security-schema ORM classes the
accounts god-module hub used to own, so cross-domain readers resolve them via
this sanctioned ports surface (Law 3) instead of ``domains.governance.models``.

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

from domains.security.models.security_schema_models import (
    AlertEscalationRule,
    DocumentVerification,
    KYCVerification,
)


def _keyset_list(model, db: Session, limit: int = 100) -> list:
    """Backward-compatible plain list sourced via keyset (no OFFSET)."""
    return cursor_paginate_asc(db.query(model), page_size=limit).items


def _keyset_page(model, db: Session, cursor: Optional[str] = None,
                 page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page over ``model`` (scale-ready, no OFFSET)."""
    return cursor_paginate_asc(db.query(model), cursor=cursor, page_size=page_size)


# --- DocumentVerification ---

def get_document_verification_by_id(db: Session, id_: int) -> Optional[DocumentVerification]:
    """Return DocumentVerification by primary key (or None)."""
    return db.get(DocumentVerification, id_)

def list_document_verifications(db: Session, limit: int = 100) -> List[DocumentVerification]:
    """Return up to ``limit`` DocumentVerification rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(DocumentVerification, db, limit)

def list_document_verifications_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of document verifications (scale-ready)."""
    return _keyset_page(DocumentVerification, db, cursor, page_size)


# --- KYCVerification ---

def get_k_y_c_verification_by_id(db: Session, id_: int) -> Optional[KYCVerification]:
    """Return KYCVerification by primary key (or None)."""
    return db.get(KYCVerification, id_)

def list_k_y_c_verifications(db: Session, limit: int = 100) -> List[KYCVerification]:
    """Return up to ``limit`` KYCVerification rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(KYCVerification, db, limit)

def list_k_y_c_verifications_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of KYC verifications (scale-ready)."""
    return _keyset_page(KYCVerification, db, cursor, page_size)


# --- AlertEscalationRule ---

def get_alert_escalation_rule_by_id(db: Session, id_: int) -> Optional[AlertEscalationRule]:
    """Return AlertEscalationRule by primary key (or None)."""
    return db.get(AlertEscalationRule, id_)

def list_alert_escalation_rules(db: Session, limit: int = 100) -> List[AlertEscalationRule]:
    """Return up to ``limit`` AlertEscalationRule rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(AlertEscalationRule, db, limit)

def list_alert_escalation_rules_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of alert escalation rules (scale-ready)."""
    return _keyset_page(AlertEscalationRule, db, cursor, page_size)


__all__ = [
    "AlertEscalationRule",
    "DocumentVerification",
    "KYCVerification",
    "get_document_verification_by_id",
    "list_document_verifications",
    "list_document_verifications_page",
    "get_k_y_c_verification_by_id",
    "list_k_y_c_verifications",
    "list_k_y_c_verifications_page",
    "get_alert_escalation_rule_by_id",
    "list_alert_escalation_rules",
    "list_alert_escalation_rules_page",
]

# --- Lazy service exports (Law 3 sanctioned cross-domain surface) ---
# Cross-domain consumers import these from ports instead of reaching
# into the services tree directly.
_LAZY_SERVICE_EXPORTS: dict[str, tuple[str, str]] = {
    "require_roles": ("domains.security.services.iam.security_dependencies", "require_roles"),
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

