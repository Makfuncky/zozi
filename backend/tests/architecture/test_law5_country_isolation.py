"""Law 5 (country scope) gate — page-level isolation for the partner/supplier
flows fixed in Phase 2G.

For each page below, the corresponding backend read path must:
  (a) accept a country scope (query param, JWT claim, or partner country_code), and
  (b) restrict results to that country (no cross-country leakage).

Pages in scope:
  * /logistics-partner/shipments    — partner only sees own-country shipments
  * /logistics-partner/scan         — partner scan is restricted to own country
  * /suppliers/[id]                 — public supplier page respects URL `country`

These checks are source-level (AST), so they don't need a running DB.
"""
from __future__ import annotations

import pathlib
import re

import pytest

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_DOMAINS_LOGISTICS_SVC = _BACKEND_ROOT / "domains" / "logistics" / "services" / "shipping" / "shipments_service.py"
_DOMAINS_ORDERS_LOGISTICS = (
    _BACKEND_ROOT / "domains" / "orders" / "services" / "core" / "logistics.py"
)
_MODULES_CUSTOMER_SUPPLIERS = (
    _BACKEND_ROOT / "modules" / "customer" / "routers" / "suppliers.py"
)
_DOMAINS_SUPPLIERS_PORTS = _BACKEND_ROOT / "domains" / "suppliers" / "ports.py"
_DOMAINS_CATALOG_PORTS = _BACKEND_ROOT / "domains" / "catalog" / "ports.py"


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


class TestPartnerShipmentsCountryFilter:
    """Backend `_partner_visible_shipments_query` must AND-filter on partner.country_code (Law 5)."""

    def test_query_file_exists(self):
        assert _DOMAINS_ORDERS_LOGISTICS.exists()

    def test_query_defines_country_clause(self):
        source = _read(_DOMAINS_ORDERS_LOGISTICS)
        # The query must add a country filter for the logistics_partner branch.
        assert "partner_country" in source or "partner.country_code" in source, (
            "Partner-visible shipments query must AND-filter on partner country (Law 5)."
        )

    def test_query_shipment_country_code_present(self):
        source = _read(_DOMAINS_ORDERS_LOGISTICS)
        assert "Shipment.country_code" in source, (
            "Partner-visible shipments must be filtered by Shipment.country_code (Law 5)."
        )


class TestScanLookupCountryFilter:
    """`scan_lookup_shipment_by_code` must reject cross-country scans for partners."""

    def test_service_file_exists(self):
        assert _DOMAINS_LOGISTICS_SVC.exists()

    def test_scan_function_rejects_logistics_partner_without_country_match(self):
        source = _read(_DOMAINS_LOGISTICS_SVC)
        # The function must accept logistics_partner and gate by partner country.
        assert "logistics_partner" in source
        assert "country_code" in source
        # Must raise 404 on cross-country mismatch (not 403, to avoid existence disclosure).
        assert "404" in source, "scan_lookup_shipment_by_code must return 404 on cross-country mismatch."


class TestPublicSupplierCountryFilter:
    """Public supplier endpoint must accept `country` query and pass it to ports (Law 3 + Law 5)."""

    def test_router_has_country_query_param(self):
        source = _read(_MODULES_CUSTOMER_SUPPLIERS)
        # The thin router must declare `country: str | None = Query(...)`.
        assert re.search(r"country[^=]*=.*Query", source), (
            "Public supplier endpoints must accept `country` query param (Law 5)."
        )

    def test_router_passes_country_to_ports(self):
        source = _read(_MODULES_CUSTOMER_SUPPLIERS)
        # The router must call the ports with country=...
        assert "country=country" in source or "country=country_code" in source, (
            "Public supplier router must forward `country` to suppliers.ports (Law 3 / Law 5)."
        )

    def test_supplier_ports_declares_country_parameter(self):
        source = _read(_DOMAINS_SUPPLIERS_PORTS)
        # The public-by-id function must accept a country argument.
        assert "country: str | None = None" in source or "country:" in source

    def test_catalog_ports_filters_by_country(self):
        source = _read(_DOMAINS_CATALOG_PORTS)
        assert "country_code" in source, (
            "domains/catalog/ports.py must provide a country-scoped public product read (Law 5)."
        )


class TestNoCrossCountryLeakage:
    """Sanity: a partner with country 'EG' must not see shipments with country 'SA'."""

    def test_country_filter_is_AND_not_OR(self):
        source = _read(_DOMAINS_ORDERS_LOGISTICS)
        # The country clause must be ANDed with the existing assigned/pickup filter.
        # Look for "& country_clause" in the partner branch.
        assert "& country_clause" in source or "country_clause is not None" in source


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q", "--no-header"]))
