"""Invoices router stub."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from data.db import get_db
from utils.dependencies import require_admin

router = APIRouter()


@router.get("/")
def list_invoices(current_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    return {"message": "Invoices endpoint - stub"}