"""
Logistics Partner Router — partner management and partner dashboard.
All business logic in controllers/logistics_partner_controller.py.
"""
from typing import List, Optional
from fastapi import Depends, File, Form, Query, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db.database import get_db
from routers.core_auth_routes import get_current_user
import controllers.orders.logistics_partner_controller as ctrl

class BulkPartnerAdminActionRequest(BaseModel):
    partner_ids: List[int]
    action: str
    note: str | None = None

class BulkShipmentStatusRequest(BaseModel):
    shipment_ids: List[int]
    status: str
    notes: str | None = None
