"""customers domain — request/response schemas (Pydantic v2).

Single-sourced here (diagram §3). Add the customer-facing schemas
(Create/Update/List/DTO) so routers serialize through a single contract.
"""
from __future__ import annotations

# Customer-domain Pydantic schemas live here. Imported by services and
# routers; kept free of ORM imports.

__all__: list[str] = []
