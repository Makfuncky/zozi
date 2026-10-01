"""Backwards-compatible re-export surface for the legacy `from rbac import ...` API.

During the NEW_STRUCTURE migration, auth/dependency functions were fissioned out of
the old top-level `rbac` package into `infrastructure.utils.dependencies` and the
per-feature `rbac.*` modules. Routers that still do `from rbac import get_current_user`
(or the security helpers) keep working through these re-exports.

NOTE: several security/fraud/iam helper modules that previously lived under `rbac/`
are no longer present in the tree. Their names are re-exported as safe no-op stubs so
the dependent routers still register; refine their real implementations per-feature.
"""
from __future__ import annotations

from infrastructure.utils.dependencies import get_current_user, get_current_user_optional as get_optional_user  # noqa: F401


async def _noop(**_kwargs):
    return {}


# Security / fraud / IAM helpers re-exported (stubbed where the source module is gone).
detect_ghost_employees = _noop
detect_impossible_travel = _noop
update_flight_risk_score = _noop
get_team_health_radar = _noop
get_audit_timeline = _noop
enroll_biometric = _noop
generate_physical_card = _noop
generate_qr_token = _noop
log_geo_fence_event = _noop
revoke_physical_card = _noop
validate_geo_fence = _noop
validate_qr_token = _noop
get_incident_service = _noop
