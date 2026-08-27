"""Re-export shim for logistics_partner_controller."""
from domains.logistics.services.partners.service import *

__all__ = ['review_logistics_partner_service_area', 'create_logistics_partner_service_area', 
           'update_logistics_partner_service_area', 'delete_logistics_partner_service_area']
