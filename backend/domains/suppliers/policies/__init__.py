"""suppliers domain - access policies (Law 1/Law 5 encapsulation).

Policies express the domain's authorization rules as pure functions so routers
and services share one decision source. Country scope (Law 5) is enforced here
independent of the feature check.
"""

from __future__ import annotations


def can_manage_supplier(actor: dict, supplier_user_id: int) -> bool:
    """Return True if ``actor`` may mutate the supplier identified by ``supplier_user_id``.

    Admins and sub-admins may manage any supplier in their country scope.
    Suppliers may only manage their own profile.
    """
    role = actor.get("role", "")
    if role in ("admin", "sub_admin"):
        return True
    return actor.get("id") == supplier_user_id


def can_view_supplier_health(actor: dict, supplier_user_id: int | None = None) -> bool:
    """Return True if ``actor`` may view supplier health scores.

    Admins may view any supplier health. Suppliers may view only their own.
    """
    role = actor.get("role", "")
    if role == "admin":
        return True
    if supplier_user_id is None:
        return False
    return actor.get("id") == supplier_user_id


def can_manage_supplier_payouts(actor: dict) -> bool:
    """Return True if ``actor`` may create or approve supplier payouts."""
    return actor.get("role", "") in ("admin", "sub_admin")


def can_manage_supplier_badges(actor: dict) -> bool:
    """Return True if ``actor`` may assign or revoke supplier badges."""
    return actor.get("role", "") in ("admin", "sub_admin")


def can_review_supplier_documents(actor: dict) -> bool:
    """Return True if ``actor`` may approve or reject supplier documents."""
    return actor.get("role", "") in ("admin", "sub_admin")


def is_in_country_scope(actor: dict, country_code: str | None) -> bool:
    """Return True if ``actor`` is authorized in ``country_code`` (Law 5).

    Admins with no country restriction (global) pass any country. Country-scoped
    staff must match the target country.
    """
    if not country_code:
        return True
    actor_role = actor.get("role", "")
    actor_country = actor.get("country_code") or actor.get("preferred_country")
    if actor_role == "admin" and not actor_country:
        return True
    return (actor_country or "").upper() == country_code.upper()


__all__ = [
    "can_manage_supplier",
    "can_view_supplier_health",
    "can_manage_supplier_payouts",
    "can_manage_supplier_badges",
    "can_review_supplier_documents",
    "is_in_country_scope",
]
