from __future__ import annotations

"""Logistics services — re-exports from focused service modules.

This module provides a single import point for all logistics service functions.
Each focused service owns its own domain logic:
- services/core/carrier_service.py: Carrier CRUD operations
- services/core/shipment_service.py: Shipment operations
- services/core/zone_service.py: Zone management
- services/core/location_service.py: Location management
- services/core/admin_service.py: Admin operations
- services/partners/partner_service.py: Partner CRUD
- services/partners/logistics_pricing_service.py: Pricing engine
- services/partners/settlement_service.py: Settlements
- services/partners/contract_service.py: Contracts
- services/geo/routing_service.py: Routing
- services/geo/distance_service.py: Distance calculations
"""

from domains.logistics.services.core.carrier_service import (
    get_carriers,
    create_carrier,
    delete_carrier,
)
from domains.logistics.services.core.shipment_service import (
    get_orders_to_fulfil,
    create_shipment,
    get_active_shipments,
    get_shipment_history,
    get_shipment_events,
    scan_shipment_event,
    update_shipment_status,
    get_logistics_summary,
    get_distribution_channels,
    update_event_gps,
)
from domains.logistics.services.core.zone_service import (
    get_shipping_zones,
    upsert_shipping_zone,
    delete_shipping_zone,
)
from domains.logistics.services.core.location_service import (
    list_city_distances,
    create_city_distance,
    update_city_distance,
    delete_city_distance,
)
from domains.logistics.services.core.admin_service import (
    list_partners,
    create_partner,
    update_partner,
    delete_partner,
    bulk_manage_partners,
    review_partner_profile,
    review_partner_service_area,
    review_partner_pricing_profile,
    review_partner_category_rule,
    review_partner_vehicle_rule,
    admin_review_lp_document,
)
from domains.logistics.services.partners.partner_service import (
    get_my_partner_profile,
    update_my_partner_profile,
    accept_partner_terms,
    submit_partner_profile_for_review,
    list_public_partners,
    get_public_partner,
)
from domains.logistics.services.partners.logistics_pricing_service import (
    list_my_partner_service_areas,
    list_my_partner_pricing_profiles,
    list_my_partner_category_rules,
    list_my_partner_vehicle_rules,
    upsert_my_partner_service_area,
    upsert_my_partner_pricing_profile,
    upsert_my_partner_category_rule,
    upsert_my_partner_vehicle_rule,
    delete_my_partner_pricing_profile,
    delete_my_partner_category_rule,
    delete_my_partner_vehicle_rule,
    delete_my_partner_service_area,
)
from domains.logistics.services.partners.settlement_service import (
    get_partner_payouts,
    request_partner_payout,
    list_pending_partner_payouts,
    verify_partner_payout,
    list_partner_cod_remittance_receipts,
    upload_partner_cod_remittance_receipt,
)
from domains.logistics.services.partners.contract_service import (
    get_partner_bank_account,
    upsert_partner_bank_account,
    list_partner_documents,
    upload_partner_document,
    delete_partner_document,
)
from domains.logistics.services.geo.routing_service import build_route_plan
from domains.logistics.services.geo.distance_service import (
    haversine_km,
    lookup_city_distance_km,
)
