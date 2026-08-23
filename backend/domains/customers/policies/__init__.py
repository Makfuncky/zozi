"""customers domain — authorization policies (OPA/rego bindings, ABAC gates).

Single-sourced here (diagram §3). Populate as customer-domain authorization
decisions are extracted from inline router checks.
"""
from __future__ import annotations

# Policy entry points for the customers domain. Add policy functions here as
# authorization logic is extracted from routers/controllers.

__all__: list[str] = []
