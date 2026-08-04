from __future__ import annotations
from typing import List

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from data.db import get_db
from data.controllers_admin_controller import require_admin
from services import import_service as svc
from services.logistics.logistics_router_service import get_import_shipment

router = APIRouter()


# â”€â”€ Schemas â”€â”€


class ShipmentLineInput(BaseModel):
    po_line_id: Optional[int] = None
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    sku: Optional[str] = None
    hs_code: Optional[str] = None
    quantity: float
    unit_cost_fx: float
    weight_kg: Optional[float] = None
    volume_cbm: Optional[float] = None


class ShipmentCreate(BaseModel):
    po_id: Optional[int] = None
    supplier_id: Optional[int] = None
    origin_country: Optional[str] = None
    port_of_loading: Optional[str] = None
    port_of_discharge: Optional[str] = None
    vessel_name: Optional[str] = None
    bill_of_lading: Optional[str] = None
    container_number: Optional[str] = None
    shipment_date: Optional[datetime] = None
    estimated_arrival: Optional[datetime] = None
    currency: str = "OMR"
    exchange_rate: float = 1.0
    warehouse_id: Optional[int] = None
    country_code: Optional[str] = None
    notes: Optional[str] = None
    lines: list[ShipmentLineInput] = []


class CostAllocateInput(BaseModel):
    freight_cost: Optional[float] = None
    insurance_cost: Optional[float] = None
    port_charges: Optional[float] = None
    inland_freight: Optional[float] = None
    bank_charges: Optional[float] = None
    other_costs: Optional[float] = None
    allocation_method: str = "by_value"


class CustomsInput(BaseModel):
    customs_declaration_number: Optional[str] = None
    customs_broker: Optional[str] = None
    entry_date: Optional[datetime] = None
    duty_rate: Optional[float] = None
    duty_amount: Optional[float] = None
    vat_on_duty: Optional[float] = None
    penalties: Optional[float] = None
    notes: Optional[str] = None


class FinalizeInput(BaseModel):
    warehouse_id: Optional[int] = None


class TemplateCreate(BaseModel):
    name: str
    default_duty_rate: Optional[float] = None
    default_freight_percent: Optional[float] = None
    default_insurance_percent: Optional[float] = None
    default_port_charges_percent: Optional[float] = None
    default_bank_charges_percent: Optional[float] = None
    allocation_method: str = "by_value"
    country_code: Optional[str] = None


class AutoAllocateInput(BaseModel):
    template_id: Optional[int] = None
    country_code: Optional[str] = None


# â”€â”€ Shipments â”€â”€


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
    return get_import_shipment(db, shipment_id)


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


@router.post("/shipments/{shipment_id}/finalize", summary="Finalize landed cost â†’ Inventory")
def finalize_cost(shipment_id: int, payload: FinalizeInput = FinalizeInput(),
                   db: Session = Depends(get_db),
                   _admin: dict = Depends(require_admin)):
    try:
        s = svc.finalize_landed_cost(db, shipment_id, warehouse_id=payload.warehouse_id,
                                      created_by=_admin.get("id"))
    except ValueError as e:
        raise HTTPException(400, str(e))
    return s


# â”€â”€ FX Revaluation â”€â”€


@router.post("/fx-revaluation", summary="Run FX revaluation on open shipments")
def fx_revaluation(as_of: date = None, country_code: str = None,
                    db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    return svc.run_fx_revaluation(db, as_of=as_of, country_code=country_code,
                                   created_by=_admin.get("id"))


# â”€â”€ Cost Templates â”€â”€


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