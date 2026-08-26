"""Governance audit services."""
from domains.audit.services.retention_service import *  # Re-export from audit domain
from domains.audit.services.compliance_engine import *  # Re-export from audit domain

__all__ = ['run_operational_retention_cycle', 'GCCComplianceEngine', 'get_compliance_engine', 'DataResidencyService']


def run_operational_retention_cycle(*args, **kwargs):
    """Stub for operational retention cycle."""
    pass


class GCCComplianceEngine:
    """Stub for GCC compliance engine."""
    pass


def get_compliance_engine(*args, **kwargs):
    """Stub for compliance engine."""
    return GCCComplianceEngine()


class DataResidencyService:
    """Stub for data residency service."""
    pass
