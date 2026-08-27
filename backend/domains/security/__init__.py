"""Security domain — public facade.

Exports the public API for the security domain. Uses lazy imports to avoid
circular dependency issues at module load time.
"""
from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # services
    "SecurityService": ("domains.security.services.core.security_service", "SecurityService"),
    "KMSEncryption": ("domains.security.services.core.kms_encryption", "KMSEncryption"),
    "SecurityMetrics": ("domains.security.services.core.security_metrics", "SecurityMetrics"),
    "FraudDetectionService": ("domains.security.services.fraud.fraud_detection_service", "FraudDetectionService"),
    "FraudEngine": ("domains.security.services.fraud.fraud_engine", "FraudEngine"),
    "FraudService": ("domains.security.services.fraud.fraud_service", "FraudService"),
    "IAMService": ("domains.security.services.iam.iam_service", "IAMService"),
    "PublicSecurityDetectionService": ("domains.security.services.detection.public_security_detection_service", "PublicSecurityDetectionService"),
    "PublicSecurityRegistrationService": ("domains.security.services.registration.public_security_registration_service", "PublicSecurityRegistrationService"),
    # models
    "Fraud": ("domains.security.models.fraud", "Fraud"),
    "SecuritySchema": ("domains.security.models.security_schema_models", "SecuritySchema"),
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'domains.security' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
