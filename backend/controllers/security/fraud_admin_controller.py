"""controllers.security.fraud_admin_controller controller.

Business logic is delegated to services.security.fraud_admin_controller_service (routers -> controllers -> services)."""

from services.security.fraud_admin_controller_service import (
    _q, add_to_blacklist, assign_review, create_rule, list_blacklist, list_device_fingerprints,
    list_fraud_events, list_ip_reputation, list_review_queue, list_rules, logger, remove_from_blacklist,
    resolve_review, threat_feed_status
)

__all__ = [
    "_q", "add_to_blacklist", "assign_review", "create_rule", "list_blacklist", "list_device_fingerprints",
    "list_fraud_events", "list_ip_reputation", "list_review_queue", "list_rules", "logger", "remove_from_blacklist",
    "resolve_review", "threat_feed_status"
]
