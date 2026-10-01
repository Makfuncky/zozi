"""accounts domain — feature flags (Law 4).

Feature atoms are single-sourced here and aggregated by ``rbac/catalog.py``
(automatic package scan, no manual wiring needed). CI fails on any
``require_feature(...)`` literal not present in this registry.
"""

FEATURES = {
    # --- User lifecycle ---
    "accounts.user.create": "Create new user accounts (registration, admin create).",
    "accounts.user.read": "Read user account details (self or admin).",
    "accounts.user.update": "Update user account profile fields.",
    "accounts.user.delete": "Soft-delete / hard-delete user accounts.",
    "accounts.user.list": "List users (admin / support only).",
    "accounts.user.export": "Export user data (GDPR / admin).",

    # --- Authentication / sessions ---
    "accounts.session.manage": "Manage user sessions and tokens (list, revoke, refresh).",
    "accounts.session.revoke": "Force-revoke an active session or refresh token.",
    "accounts.password.reset": "Issue / consume password-reset tokens.",
    "accounts.password.change": "Change password (authenticated user).",
    "accounts.email.verify": "Issue / consume email-verification tokens.",

    # --- MFA / OTP ---
    "accounts.otp.issue": "Issue OTP codes (email / SMS).",
    "accounts.otp.verify": "Verify OTP codes.",
    "accounts.mfa.enable": "Enable multi-factor authentication for a user.",
    "accounts.mfa.disable": "Disable multi-factor authentication for a user.",

    # --- Social login ---
    "accounts.social.link": "Link a social identity (Google / Apple / etc.) to a user.",
    "accounts.social.unlink": "Unlink a social identity from a user.",

    # --- Devices / login history ---
    "accounts.device.list": "List devices the user has logged in from.",
    "accounts.device.trust": "Mark a device as trusted.",
    "accounts.device.revoke": "Revoke a trusted device.",
    "accounts.login_history.read": "Read user login history.",

    # --- Address book ---
    "accounts.address.create": "Add a new address to a user's address book.",
    "accounts.address.read": "Read a user's address book.",
    "accounts.address.update": "Update an existing address.",
    "accounts.address.delete": "Delete an address from the address book.",
    "accounts.address.set_default": "Mark an address as the default for shipping / billing.",

    # --- Cart ---
    "accounts.cart.read": "Read the user's shopping cart.",
    "accounts.cart.write": "Add / update / remove cart items.",

    # --- Referrals ---
    "accounts.referral.create": "Create a referral (code, invite).",
    "accounts.referral.read": "Read referral / point-event history.",

    # --- Support tickets ---
    "accounts.support_ticket.create": "Open a customer support ticket.",
    "accounts.support_ticket.read": "Read a support ticket (own or all for staff).",
    "accounts.support_ticket.reply": "Reply to a support ticket.",
    "accounts.support_ticket.assign": "Assign a support ticket to a staff member.",
    "accounts.support_ticket.close": "Close / resolve a support ticket.",
    "accounts.support_ticket.attach": "Upload attachments to a support ticket.",

    # --- Chat (direct / group / entity / video) ---
    "accounts.chat.direct.send": "Send a direct message.",
    "accounts.chat.direct.read": "Read direct chat history.",
    "accounts.chat.group.create": "Create a group chat room.",
    "accounts.chat.group.manage": "Add / remove members of a group chat.",
    "accounts.chat.group.send": "Send a group chat message.",
    "accounts.chat.entity.read": "Read entity (business-customer) chat threads.",
    "accounts.video.room.create": "Create a video room (support, business calls).",
    "accounts.video.room.join": "Join a video room.",
    "accounts.video.recording.read": "Read / download video room recordings.",

    # --- Audit / observability ---
    "accounts.audit.read": "Read audit logs (admin / compliance).",
    "accounts.system_health.read": "Read system health events (admin ops).",
    "accounts.command_center.read": "Read command-center views (admin ops dashboard).",
    "accounts.shift_handover.read": "Read shift handover sessions / tasks (ops).",
    "accounts.shift_handover.write": "Create / update shift handover tasks.",

    # --- News / notices (publishing the accounts-owned feed) ---
    "accounts.news.read": "Read executive / internal news articles.",
    "accounts.news.publish": "Publish news articles (admin).",
    "accounts.news.source.manage": "Manage news sources (admin).",
    "accounts.internal_notice.read": "Read internal notices for staff.",
    "accounts.internal_notice.publish": "Publish internal notices (admin).",
    "accounts.predictive_simulation.read": "Read predictive simulation outputs.",

    # --- Escalation / SLA ---
    "accounts.escalation_sla.read": "Read escalation SLA rules and logs.",
    "accounts.escalation_sla.write": "Create / update escalation SLA rules.",

    # --- Permissions / RBAC delegation ---
    "accounts.permissions.manage": "Manage role and user permissions.",
    "accounts.role.assign": "Assign a role to a user (admin).",
    "accounts.role.revoke": "Revoke a role from a user (admin).",

    # --- Cross-domain delegation tokens ---
    "accounts.delegation_token.issue": "Issue short-lived delegation tokens to other domains.",
}


def all_features() -> list:
    """Return all accounts feature atoms (used by tests / docs)."""
    return list(FEATURES.keys())


__all__ = ["FEATURES", "all_features"]
