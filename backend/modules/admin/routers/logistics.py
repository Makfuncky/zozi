from __future__ import annotations

"""Admin logistics router — canonical."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status

from domains.comms.models.marketing import NewsletterSubscriber, EmailCampaign, CampaignRecipient
from domains.finance.models.payments import Payout
from domains.logistics.models.logistics import Shipment, ShippingCarrier, ShippingZone
from domains.accounts.models.user import User
from modules.admin.routers.governance import (
from modules.admin.routers.governance import archive_entity, restore_entity, bulk_archive_entities, bulk_restore_entities, hard_delete_entity
from modules.admin.routers.governance import require_admin
from modules.admin.routers.catalog import (
from modules.admin.routers.catalog import get_banners_page
from modules.admin.routers.promotions import (
from modules.admin.routers.promotions import (
from modules.admin.routers.governance import (
from modules.admin.routers.orders import disputes_controller
from datetime import date, datetime
from datetime import datetime
from datetime import datetime, timezone
from infrastructure.database.database import get_db
from infrastructure.database.schemas import (
from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest
from infrastructure.database.schemas import FlashSaleCreate, FlashSaleOut
from decimal import Decimal
from infrastructure.database.database import get_db
from infrastructure.utils import import_service as svc
from infrastructure.utils.dependencies import require_admin
from domains.audit.services.logs.audit_trail_service import AuditTrailService
from domains.catalog.services import import_service as svc
from domains.hr.services.hierarchy.hierarchy_service import (
from domains.logistics.services.partners.service import (
from domains.suppliers.services.legal_contract_service import LegalContractService
from domains.governance.services.approval_matrix_service import (
from sqlalchemy import func as sqlfunc
from sqlalchemy import func as sqlfunc, case as sql_case
from sqlalchemy import text
from sqlalchemy.orm import Session
from the UI without SSH or terminal access.
from typing import List, Optional
from typing import Optional
from infrastructure.utils.analytics_service import get_country_dashboard_stats
from infrastructure.utils.backup import get_backup_manager
from infrastructure.utils.constants import MAX_BULK_ITEMS
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.dependencies import require_admin, require_super_admin
from infrastructure.utils.key_rotation import rotate_encryption_key
from infrastructure.database.rls_interceptor import set_rls_context, clear_rls_context
import modules.admin.routers.finance as _ic
import modules.admin.routers.orders.logistics_controller as _ctrl
import modules.admin.routers.orders.logistics_partner_controller as _lpc
import modules.admin.routers.suppliers as _sc
import modules.admin.routers.suppliers as _sdc
import domains.orders.services.logistics_controller as _ctrl
import logging as _l; _l.getLogger(__name__).warning("skip partners_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip shipping_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip tracking_router: %s", _e)

router = APIRouter(prefix="/api/v1/admin/logistics", tags=["admin", "logistics"])

@router.post("/shipments", summary="Create an import shipment")
def create_shipment(payload: ShipmentCreate, db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    try:
        s = svc.create_import_shipment(
            db, po_id=payload.po_id, supplier_id=payload.supplier_id,
            origin_country=payload.origin_country,
            port_of_loading=payload.port_of_loading,
            port_of_discharge=payload.port_of_discharge,
            vessel_name=payload.vessel_name,
            bill_of_lading=payload.bill_of_lading,
            container_number=payload.container_number,
            shipment_date=payload.shipment_date,
            estimated_arrival=payload.estimated_arrival,
            currency=payload.currency, exchange_rate=Decimal(str(payload.exchange_rate)),
            warehouse_id=payload.warehouse_id, country_code=payload.country_code,
            notes=payload.notes, created_by=_admin.get("id"),
            lines=[l.model_dump() for l in payload.lines],
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return s




@router.get("/shipments", summary="List import shipments")
def list_shipments(status: str = None, po_id: int = None,
                   country_code: str = None, limit: int = 50, offset: int = 0,
                   db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    return svc.list_shipments(db, status=status, po_id=po_id,
                               country_code=country_code, limit=limit, offset=offset)




@router.get("/shipments/{shipment_id}", summary="Get an import shipment")
def get_shipment(shipment_id: int, db: Session = Depends(get_db),
                 _admin: dict = Depends(require_admin)):
    s = db.query(svc.ImportShipment).filter(
        svc.ImportShipment.id == shipment_id
    ).first()
    if not s:
        raise HTTPException(404, "Shipment not found")
    return s




@router.post("/shipments/{shipment_id}/confirm", summary="Confirm & post goods in transit")
def confirm_shipment(shipment_id: int, db: Session = Depends(get_db),
                     _admin: dict = Depends(require_admin)):
    try:
        s = svc.confirm_shipment(db, shipment_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return s




@router.post("/shipments/{shipment_id}/allocate", summary="Allocate landed costs")
def allocate_costs(shipment_id: int, payload: CostAllocateInput,
                    db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    try:
        s = svc.allocate_landed_costs(
            db, shipment_id,
            freight_cost=Decimal(str(payload.freight_cost)) if payload.freight_cost else None,
            insurance_cost=Decimal(str(payload.insurance_cost)) if payload.insurance_cost else None,
            port_charges=Decimal(str(payload.port_charges)) if payload.port_charges else None,
            inland_freight=Decimal(str(payload.inland_freight)) if payload.inland_freight else None,
            bank_charges=Decimal(str(payload.bank_charges)) if payload.bank_charges else None,
            other_costs=Decimal(str(payload.other_costs)) if payload.other_costs else None,
            allocation_method=payload.allocation_method,
            created_by=_admin.get("id"),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return s




@router.post("/shipments/{shipment_id}/auto-allocate", summary="Auto-allocate costs from template")
def auto_allocate(shipment_id: int, payload: AutoAllocateInput = AutoAllocateInput(),
                   db: Session = Depends(get_db),
                   _admin: dict = Depends(require_admin)):
    try:
        s = svc.auto_allocate_from_template(
            db, shipment_id, template_id=payload.template_id,
            country_code=payload.country_code, created_by=_admin.get("id"),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return s




@router.post("/shipments/{shipment_id}/customs", summary="Record customs entry")
def record_customs(shipment_id: int, payload: CustomsInput,
                    db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    try:
        c = svc.record_customs_entry(
            db, shipment_id,
            customs_declaration_number=payload.customs_declaration_number,
            customs_broker=payload.customs_broker,
            entry_date=payload.entry_date,
            duty_rate=Decimal(str(payload.duty_rate)) if payload.duty_rate else None,
            duty_amount=Decimal(str(payload.duty_amount)) if payload.duty_amount else None,
            vat_on_duty=Decimal(str(payload.vat_on_duty)) if payload.vat_on_duty else None,
            penalties=Decimal(str(payload.penalties)) if payload.penalties else None,
            notes=payload.notes, created_by=_admin.get("id"),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return c




@router.post("/shipments/{shipment_id}/finalize", summary="Finalize landed cost → Inventory")
def finalize_cost(shipment_id: int, payload: FinalizeInput = FinalizeInput(),
                   db: Session = Depends(get_db),
                   _admin: dict = Depends(require_admin)):
    try:
        s = svc.finalize_landed_cost(db, shipment_id, warehouse_id=payload.warehouse_id,
                                      created_by=_admin.get("id"))
    except ValueError as e:
        raise HTTPException(400, str(e))
    return s




@router.post("/fx-revaluation", summary="Run FX revaluation on open shipments")
def fx_revaluation(as_of: date = None, country_code: str = None,
                    db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    return svc.run_fx_revaluation(db, as_of=as_of, country_code=country_code,
                                   created_by=_admin.get("id"))




@router.post("/cost-templates", summary="Create a cost template")
def create_template(payload: TemplateCreate, db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    try:
        t = svc.create_cost_template(
            db, name=payload.name,
            default_duty_rate=Decimal(str(payload.default_duty_rate)) if payload.default_duty_rate else None,
            default_freight_percent=Decimal(str(payload.default_freight_percent)) if payload.default_freight_percent else None,
            default_insurance_percent=Decimal(str(payload.default_insurance_percent)) if payload.default_insurance_percent else None,
            default_port_charges_percent=Decimal(str(payload.default_port_charges_percent)) if payload.default_port_charges_percent else None,
            default_bank_charges_percent=Decimal(str(payload.default_bank_charges_percent)) if payload.default_bank_charges_percent else None,
            allocation_method=payload.allocation_method,
            country_code=payload.country_code,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return t




@router.get("/cost-templates", summary="List cost templates")
def list_templates(country_code: str = None,
                    db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    return svc.list_templates(db, country_code=country_code)


@router.get("/admin_logistics_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "admin_logistics_routes", "prefix": "/api/v1/admin"}




@router.get("/admin_logistics_routes/status")
def status():
    """Report whether a backing controller is importable."""
    return {"router": "admin_logistics_routes", "controller": "controllers.orders.logistics_controller" if _HAS_CTRL else None,
            "public_functions": _CTRL_PUBLIC}



@router.get("/{country_code}/partners")
def list_partners_route(country_code: str = Path(..., description="ISO country code"), include_deleted: bool = False, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return list_partners(db, country_code, include_deleted, page, page_size)
    finally:
        clear_rls_context()




@router.put("/{country_code}/partners/{partner_id}/approve")
def approve_partner_route(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return approve_partner(db, partner_id, country_code)
    finally:
        clear_rls_context()




@router.put("/{country_code}/partners/{partner_id}/reject")
def reject_partner_route(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return reject_partner(db, partner_id, country_code)
    finally:
        clear_rls_context()




@router.post("/{country_code}/partners/{partner_id}/toggle-active")
def toggle_partner_active_route(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return toggle_partner_active(db, partner_id, country_code)
    finally:
        clear_rls_context()




@router.post("/{country_code}/partners/{partner_id}/archive")
def archive_partner(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), payload: ArchiveRequest = None, _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return archive_entity("logistics_partner", partner_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason if payload else None)
    finally:
        clear_rls_context()




@router.post("/{country_code}/partners/{partner_id}/restore")
def restore_partner(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return restore_entity("logistics_partner", partner_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()




@router.post("/{country_code}/partners/bulk/archive")
def bulk_archive_partners(country_code: str = Path(..., description="ISO country code"), payload: BulkActionRequest = None, _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_archive_entities("logistics_partner", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason)
    finally:
        clear_rls_context()




@router.post("/{country_code}/partners/bulk/restore")
def bulk_restore_partners(country_code: str = Path(..., description="ISO country code"), payload: BulkActionRequest = None, _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_restore_entities("logistics_partner", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()




@router.delete("/{country_code}/partners/{partner_id}")
def delete_partner_permanent(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), _: User = Depends(require_super_admin), db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return hard_delete_entity("logistics_partner", partner_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()



@router.post("/shipments", summary="Create an import shipment")
def create_shipment(payload: ShipmentCreate, db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    try:
        s = svc.create_import_shipment(
            db, po_id=payload.po_id, supplier_id=payload.supplier_id,
            origin_country=payload.origin_country,
            port_of_loading=payload.port_of_loading,
            port_of_discharge=payload.port_of_discharge,
            vessel_name=payload.vessel_name,
            bill_of_lading=payload.bill_of_lading,
            container_number=payload.container_number,
            shipment_date=payload.shipment_date,
            estimated_arrival=payload.estimated_arrival,
            currency=payload.currency, exchange_rate=Decimal(str(payload.exchange_rate)),
            warehouse_id=payload.warehouse_id, country_code=payload.country_code,
            notes=payload.notes, created_by=_admin.get("id"),
            lines=[l.model_dump() for l in payload.lines],
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return s




@router.get("/shipments", summary="List import shipments")
def list_shipments(status: str = None, po_id: int = None,
                   country_code: str = None, limit: int = 50, offset: int = 0,
                   db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    return svc.list_shipments(db, status=status, po_id=po_id,
                               country_code=country_code, limit=limit, offset=offset)




@router.get("/shipments/{shipment_id}", summary="Get an import shipment")
def get_shipment(shipment_id: int, db: Session = Depends(get_db),
                 _admin: dict = Depends(require_admin)):
    s = db.query(svc.ImportShipment).filter(
        svc.ImportShipment.id == shipment_id
    ).first()
    if not s:
        raise HTTPException(404, "Shipment not found")
    return s




@router.post("/shipments/{shipment_id}/confirm", summary="Confirm & post goods in transit")
def confirm_shipment(shipment_id: int, db: Session = Depends(get_db),
                     _admin: dict = Depends(require_admin)):
    try:
        s = svc.confirm_shipment(db, shipment_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return s




@router.post("/shipments/{shipment_id}/allocate", summary="Allocate landed costs")
def allocate_costs(shipment_id: int, payload: CostAllocateInput,
                    db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    try:
        s = svc.allocate_landed_costs(
            db, shipment_id,
            freight_cost=Decimal(str(payload.freight_cost)) if payload.freight_cost else None,
            insurance_cost=Decimal(str(payload.insurance_cost)) if payload.insurance_cost else None,
            port_charges=Decimal(str(payload.port_charges)) if payload.port_charges else None,
            inland_freight=Decimal(str(payload.inland_freight)) if payload.inland_freight else None,
            bank_charges=Decimal(str(payload.bank_charges)) if payload.bank_charges else None,
            other_costs=Decimal(str(payload.other_costs)) if payload.other_costs else None,
            allocation_method=payload.allocation_method,
            created_by=_admin.get("id"),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return s




@router.post("/shipments/{shipment_id}/auto-allocate", summary="Auto-allocate costs from template")
def auto_allocate(shipment_id: int, payload: AutoAllocateInput = AutoAllocateInput(),
                   db: Session = Depends(get_db),
                   _admin: dict = Depends(require_admin)):
    try:
        s = svc.auto_allocate_from_template(
            db, shipment_id, template_id=payload.template_id,
            country_code=payload.country_code, created_by=_admin.get("id"),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return s




@router.post("/shipments/{shipment_id}/customs", summary="Record customs entry")
def record_customs(shipment_id: int, payload: CustomsInput,
                    db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    try:
        c = svc.record_customs_entry(
            db, shipment_id,
            customs_declaration_number=payload.customs_declaration_number,
            customs_broker=payload.customs_broker,
            entry_date=payload.entry_date,
            duty_rate=Decimal(str(payload.duty_rate)) if payload.duty_rate else None,
            duty_amount=Decimal(str(payload.duty_amount)) if payload.duty_amount else None,
            vat_on_duty=Decimal(str(payload.vat_on_duty)) if payload.vat_on_duty else None,
            penalties=Decimal(str(payload.penalties)) if payload.penalties else None,
            notes=payload.notes, created_by=_admin.get("id"),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return c




@router.post("/shipments/{shipment_id}/finalize", summary="Finalize landed cost → Inventory")
def finalize_cost(shipment_id: int, payload: FinalizeInput = FinalizeInput(),
                   db: Session = Depends(get_db),
                   _admin: dict = Depends(require_admin)):
    try:
        s = svc.finalize_landed_cost(db, shipment_id, warehouse_id=payload.warehouse_id,
                                      created_by=_admin.get("id"))
    except ValueError as e:
        raise HTTPException(400, str(e))
    return s




@router.post("/fx-revaluation", summary="Run FX revaluation on open shipments")
def fx_revaluation(as_of: date = None, country_code: str = None,
                    db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    return svc.run_fx_revaluation(db, as_of=as_of, country_code=country_code,
                                   created_by=_admin.get("id"))




@router.post("/cost-templates", summary="Create a cost template")
def create_template(payload: TemplateCreate, db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    try:
        t = svc.create_cost_template(
            db, name=payload.name,
            default_duty_rate=Decimal(str(payload.default_duty_rate)) if payload.default_duty_rate else None,
            default_freight_percent=Decimal(str(payload.default_freight_percent)) if payload.default_freight_percent else None,
            default_insurance_percent=Decimal(str(payload.default_insurance_percent)) if payload.default_insurance_percent else None,
            default_port_charges_percent=Decimal(str(payload.default_port_charges_percent)) if payload.default_port_charges_percent else None,
            default_bank_charges_percent=Decimal(str(payload.default_bank_charges_percent)) if payload.default_bank_charges_percent else None,
            allocation_method=payload.allocation_method,
            country_code=payload.country_code,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return t




@router.get("/cost-templates", summary="List cost templates")
def list_templates(country_code: str = None,
                    db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    return svc.list_templates(db, country_code=country_code)


@router.get("/users", response_model=ListPage[dict])
def list_users(
    limit: Optional[int] = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.put("/users/{user_id}/role")
def set_user_role(
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),


@router.post("/users/{user_id}/toggle-active")
def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),


@router.delete("/users/bulk")
def bulk_delete_users(
    body: BulkDeleteUsersBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),


@router.post("/users/bulk-toggle-active")
def bulk_toggle_users_active_route(
    body: BulkToggleActiveBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),


@router.post("/users/bulk-role")
def bulk_update_users_role_route(
    body: BulkUserRoleBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    delete_orders: bool = Query(False),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.post("/users/{user_id}/reset-password")
def admin_reset_password(
    user_id: int,
    body: ResetPasswordBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),


@router.post("/staff", status_code=201)
def create_staff(
    payload: CreateStaffAccount,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),


@router.get("/staff")
def list_staff(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),


@router.get("/staff/permission-catalog")
def staff_permission_catalog(
    current_admin: dict = Depends(require_admin),


@router.put("/staff/bulk")
def bulk_update_staff(
    body: BulkUpdateStaffBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),


@router.put("/staff/{user_id}")
def update_staff(
    user_id: int,
    payload: UpdateStaffAccount,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),


@router.delete("/staff/{user_id}")
def delete_staff(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),


@router.get("/orders", response_model=ListPage[OrderSchema])
def list_orders(
    limit: Optional[int] = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_range: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    missing_tracking_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.post("/orders/bulk-status")
def bulk_update_orders_status(
    body: BulkOrderStatusBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.delete("/orders/bulk")
def bulk_delete_orders(
    body: BulkOrderDeleteBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),


@router.delete("/orders/{order_id}")
def delete_order_route(
    order_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),


@router.put("/orders/{order_id}/status")
def set_order_status(
    order_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.post("/orders/{order_id}/refund")
def refund_order_route(
    order_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),


@router.put("/orders/{order_id}/tracking")
def set_order_tracking(
    order_id: int,
    tracking_number: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/products", response_model=ListPage[ProductSchema])
def list_products(
    limit: Optional[int] = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    filter_value: Optional[str] = Query(None, alias="filter"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.delete("/products/bulk")
def bulk_delete_products(
    body: BulkProductDeleteBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.post("/products/bulk-moderate")
def bulk_moderate_products(
    body: BulkProductModerationBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.post("/suppliers/bulk-verify")
def bulk_verify_suppliers(
    body: BulkSupplierVerifyBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.post("/suppliers/v1/bulk")
def bulk_manage_supplier_lifecycle(
    body: BulkSupplierLifecycleBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.post("/products/{product_id}/restore")
def restore_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),


@router.get("/analytics")
def analytics(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/{country_code}/dashboard")
def admin_country_dashboard(
    country_code: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/suppliers/v1/comparison", response_model=ListPage[dict])
def supplier_comparison(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/customers/insights")
def customer_insights(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/suppliers/pending", response_model=ListPage[dict])
def list_pending_suppliers(
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.post("/suppliers/{user_id}/verify")
def approve_supplier(
    user_id: int,
    note: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.post("/suppliers/{user_id}/reject")
def decline_supplier(
    user_id: int,
    note: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.put("/suppliers/{user_id}/badge")
def set_supplier_badge(
    user_id: int,
    badge_level: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.post("/suppliers/{user_id}/refresh-badge")
def refresh_supplier_badge(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/audit-logs", response_model=AuditLogPage)
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/audit-logs/actions")
def audit_log_actions(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/products/pending", response_model=ListPage[dict])
def list_pending_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.patch("/products/{product_id}/badge")
def set_product_badge(
    product_id: int,
    field: str = Query(..., description="is_hot | is_featured | is_new"),
    value: bool = Query(...),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.post("/products/{product_id}/approve")
def approve_product_route(
    product_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.post("/products/{product_id}/reject")
def reject_product_route(
    product_id: int,
    note: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/coupons", response_model=ListPage[CouponSchema])
def list_all_coupons(
    skip: int = 0,
    limit: int | None = None,
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.post("/coupons", status_code=201)
def create_coupon_route(
    data: dict,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.put("/coupons/{coupon_id}")
def update_coupon_route(
    coupon_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.delete("/coupons/{coupon_id}")
def delete_coupon_route(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),


@router.get("/promotions/config")
def get_promotion_config_route(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.put("/promotions/config")
def update_promotion_config_route(
    body: PromotionConfigBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/promotions/tiers")
def list_promotion_tiers_route(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.post("/promotions/tiers", status_code=201)
def create_promotion_tier_route(
    body: PromotionTierBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.put("/promotions/tiers/{tier_id}")
def update_promotion_tier_route(
    tier_id: int,
    body: PromotionTierUpdateBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.delete("/promotions/tiers/{tier_id}")
def delete_promotion_tier_route(
    tier_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),


@router.post("/promotions/preview")
def preview_promotion_route(
    body: PromotionPreviewBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/tickets", response_model=ListPage[dict])
def list_all_tickets(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/tickets/{ticket_id}")
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.post("/tickets/{ticket_id}/reply")
def reply_ticket(
    ticket_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.put("/tickets/{ticket_id}/status")
def set_ticket_status(
    ticket_id: int,
    status: Optional[str] = Query(None),
    body: dict | None = Body(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/disputes", response_model=ListPage[dict])
def list_admin_disputes(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    supplier_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/disputes/{dispute_id}")
def get_admin_dispute(
    dispute_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.patch("/disputes/{dispute_id}")
def patch_admin_dispute(
    dispute_id: int,
    payload: dict = Body(default_factory=dict),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.post("/disputes/bulk")
def bulk_admin_dispute_action(
    body: AdminDisputeBulkActionBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/flash-sales", response_model=ListPage[FlashSaleOut])
def list_flash_sales(
    limit: Optional[int] = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.post("/flash-sales", response_model=FlashSaleOut, status_code=201)
def create_flash_sale_route(
    body: FlashSaleCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),


@router.put("/flash-sales/{sale_id}", response_model=FlashSaleOut)
def update_flash_sale_route(
    sale_id: int,
    body: FlashSaleCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),


@router.delete("/flash-sales/{sale_id}")
def delete_flash_sale_route(
    sale_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),


@router.get("/hierarchy/permissions")
def get_hierarchy_permissions_route(
    current_admin: dict = Depends(get_current_admin),


@router.put("/hierarchy/permissions/{role}")
def update_role_permissions_route(
    role: str,
    body: UpdateRolePermissionsIn,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),


@router.get("/hierarchy/authority-level")
def hierarchy_authority_level(
    user_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_user),


@router.get("/hierarchy/chain/{user_id}")
def hierarchy_chain(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_user),


@router.get("/hierarchy/subordinates/{user_id}")
def hierarchy_subordinates(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_user),


@router.get("/hierarchy/can-manage")
def hierarchy_can_manage(
    manager_id: int = Query(..., gt=0),
    target_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_user),


@router.get("/hierarchy/org-chart")
def hierarchy_org_chart(
    org_unit_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_user),


@router.get("/hierarchy/team-members/{user_id}")
def hierarchy_team_members(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_user),


@router.get("/hierarchy/in-chain")
def hierarchy_in_chain(
    upper_user_id: int = Query(..., gt=0),
    lower_user_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_user),


@router.post("/hierarchy/reassign-manager")
def hierarchy_reassign_manager(
    body: ReassignManagerBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),


@router.post("/hierarchy/backfill-authority-levels")
def hierarchy_backfill_authority_levels(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),


@router.get("/hierarchy/approval-matrix/rules")
def get_approval_matrix_rules(
    current_admin: dict = Depends(get_current_user),


@router.post("/hierarchy/approval-matrix/check")
def check_approval_eligibility(
    body: ResourceApprovalCheckIn,
    user_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_user),


@router.get("/hierarchy/approvers/{resource_type}")
def get_resource_approvers(
    resource_type: str,
    org_unit_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_user),


@router.get("/hierarchy/approval-chain/{user_id}/{resource_type}")
def get_user_approval_chain(
    user_id: int,
    resource_type: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_user),


@router.get("/payouts/pending")
def get_pending_payouts_route(
    limit: int = 200,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.post("/payouts/{payout_id}/verify")
def verify_payout_route(
    payout_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),


@router.get("/email/stats")
def admin_email_stats(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/logistics/overview")
def admin_logistics_overview(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/suppliers/v1/documents", response_model=ListPage[dict])
def admin_supplier_documents(
    supplier_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    doc_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.put("/suppliers/v1/documents/{doc_id}/review")
def admin_review_document(
    doc_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/invoices/overview")
def admin_invoices_overview(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/logistics/partners")
def admin_logistics_partners(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.post("/logistics/partners", status_code=201)
def admin_create_logistics_partner(
    data: dict,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),


@router.put("/logistics/partners/{partner_id}")
def admin_update_logistics_partner(
    partner_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/analytics/timeseries")
def analytics_timeseries(
    period: str = Query("30d", pattern=r"^(7d|30d|90d|1y)$"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/analytics/top-products")
def analytics_top_products(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/analytics/user-growth")
def analytics_user_growth(
    period: str = Query("30d", pattern=r"^(7d|30d|90d|1y)$"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/analytics/chatbot")
def analytics_chatbot(
    period: str = Query("30d", pattern=r"^(7d|30d|90d|1y)$"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),


@router.get("/suppliers/v1/all")
def list_all_suppliers(
    page: int = Query(1, ge=1),
    page_size: Optional[int] = Query(None, ge=1, le=200),
    skip: int = 0,
    limit: int | None = None,
    q: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    badge: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/banners", response_model=ListPage[dict])
def admin_list_banners(
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),


@router.get("/banners/{banner_id:int}")
def admin_get_banner(
    banner_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),


@router.post("/banners", status_code=201)
def admin_create_banner(
    payload: BannerCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),


@router.put("/banners/{banner_id}")
def admin_update_banner(
    banner_id: int,
    payload: BannerUpdate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),


@router.delete("/banners/{banner_id}")
def admin_delete_banner(
    banner_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),


@router.get("/export/users")
def admin_export_users(
    background: bool = Query(False),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/export/orders")
def admin_export_orders(
    background: bool = Query(False),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/export/products")
def admin_export_products(
    background: bool = Query(False),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/export/coupons")
def admin_export_coupons(
    background: bool = Query(False),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/export/audit-logs")
def admin_export_audit_logs(
    days: int = Query(30, ge=1, le=365),
    background: bool = Query(False),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/export/supplier-payout-transfers")
def admin_export_supplier_payout_transfers(
    background: bool = Query(False),
    provider: str = Query("manual_csv"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/export/logistics-payout-transfers")
def admin_export_logistics_payout_transfers(
    background: bool = Query(False),
    provider: str = Query("manual_csv"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/export/cod-remittance-transfers")
def admin_export_cod_remittance_transfers(
    background: bool = Query(False),
    provider: str = Query("manual_csv"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/export/jobs/{job_id}/download")
def admin_download_export_job(
    job_id: str,
    current_admin: dict = Depends(get_current_admin),


@router.get("/database/overview")
def admin_database_overview(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.post("/backup/trigger", status_code=201)
def admin_trigger_backup(
    current_admin: dict = Depends(get_current_admin),


@router.get("/backup/list")
def admin_list_backups(
    current_admin: dict = Depends(get_current_admin),


@router.get("/backup/download/{filename}")
def admin_download_backup(
    filename: str,
    current_admin: dict = Depends(get_current_admin),


@router.post("/backup/restore-drill")
def admin_run_backup_restore_drill(
    filename: str | None = None,
    current_admin: dict = Depends(get_current_admin),


@router.post("/security/rotate-key")
def admin_rotate_encryption_key(
    payload: dict,
    current_admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),


@router.get("/bank-accounts/pending")
def admin_list_pending_bank_accounts(
    kind: str = Query(..., description="supplier or logistics_partner"),
    limit: int = 200,
    offset: int = 0,
    current_admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),


@router.post("/bank-accounts/{account_id}/approve")
def admin_approve_bank_account(
    account_id: int,
    kind: str = Query(..., description="supplier or logistics_partner"),
    body: Optional[dict] = None,
    current_admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),


@router.post("/bank-accounts/{account_id}/reject")
def admin_reject_bank_account(
    account_id: int,
    kind: str = Query(..., description="supplier or logistics_partner"),
    body: Optional[dict] = None,
    current_admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),


@router.delete("/bank-accounts/{account_id}")
def admin_delete_bank_account(
    account_id: int,
    kind: str = Query(..., description="supplier or logistics_partner"),
    current_admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),


@router.get("/config/checkout")
def get_checkout_config():
    """
    Public checkout configuration endpoint.
    Returns VAT rate, shipping flat rate, and free shipping threshold.
    """
    return {
        "vat_rate": 0.05,
        "shipping_flat_rate": 2.0,
        "free_shipping_threshold": 0.0,
    }




@router.post("/countries/{country_code}/legal-contracts/generate")
def generate_legal_contract(
    country_code: str = Path(...),
    payload: Optional[dict] = Body(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/countries/{country_code}/audit-trail")
def get_country_audit_trail(
    country_code: str = Path(...),
    table_name: Optional[str] = Query(None),
    record_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/reset", status_code=200)
def admin_reset_demo_data(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),


@router.get("/admin_logistics_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "admin_logistics_routes", "prefix": "/api/v1/admin"}




@router.get("/admin_logistics_routes/status")
def status():
    """Report whether a backing controller is importable."""
    return {"router": "admin_logistics_routes", "controller": "controllers.orders.logistics_controller" if _HAS_CTRL else None,
            "public_functions": _CTRL_PUBLIC}


