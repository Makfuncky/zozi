"""
Logistics Partner Router — partner management and partner dashboard.
All business logic in controllers/logistics_partner_controller.py.
"""
from typing import List, Optional
from fastapi import Depends, File, Form, Query, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from modules.admin.routers import get_current_user
import domains.orders.services.logistics_partner_controller as ctrl

class BulkPartnerAdminActionRequest(BaseModel):
    partner_ids: List[int]
    action: str
    note: str | None = None

class BulkShipmentStatusRequest(BaseModel):
    shipment_ids: List[int]
    status: str
    notes: str | None = None
