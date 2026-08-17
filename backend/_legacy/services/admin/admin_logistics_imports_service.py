from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from db.database import get_db
from controllers.admin.admin_controller import require_admin
from services.common import import_service as svc

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
    currency: str = 'OMR'
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
    allocation_method: str = 'by_value'

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
    allocation_method: str = 'by_value'
    country_code: Optional[str] = None

class AutoAllocateInput(BaseModel):
    template_id: Optional[int] = None
    country_code: Optional[str] = None

def get_shipment(shipment_id: int, db: Session=Depends(get_db), _admin: dict=Depends(require_admin)):
    s = db.query(svc.ImportShipment).filter(svc.ImportShipment.id == shipment_id).first()
    if not s:
        raise HTTPException(404, 'Shipment not found')
    return s
