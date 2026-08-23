"""accounts domain - onboarding models.

Canonical definitions of onboarding models live in their respective domains.
This module re-exports them for backwards compatibility.
"""
from __future__ import annotations

# Re-export from canonical domains (were duplicate definitions)
from domains.hr.models.hr_schema_models import (  # noqa: F401
    OnboardingPipeline, OnboardingStep,
)
from domains.security.models.security_schema_models import (  # noqa: F401
    DocumentVerification, KYCVerification,
)
from domains.media.models.media_schema_models import OCRResult  # noqa: F401

__all__ = [
    "OnboardingPipeline",
    "OnboardingStep",
    "DocumentVerification",
    "KYCVerification",
    "OCRResult",
]
