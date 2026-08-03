"""
OKR API Router
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.okr_engine import get_okr_engine, OKREngine
from data.db import get_db
from data.dependencies_auth import get_current_user

router = APIRouter()


class ObjectiveCreate(BaseModel):
    employee_id: int
    title: str
    description: str
    key_results: List[Dict[str, Any]] = []
    period_start: str
    period_end: str


class KpiEvaluate(BaseModel):
    employee_id: int
    metric_query_hash: str
    target_value: float
    current_value: float


@router.post("/objectives", response_model=dict)
async def create_objective(
    payload: ObjectiveCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    engine = get_okr_engine(db)
    result = engine.create_objective(
        employee_id=payload.employee_id,
        title=payload.title,
        description=payload.description,
        key_results=payload.key_results,
        period_start=payload.period_start,
        period_end=payload.period_end
    )
    return result


@router.post("/evaluate", response_model=dict)
async def evaluate_kpi(
    payload: KpiEvaluate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    engine = get_okr_engine(db)
    result = engine.evaluate_kpi(
        employee_id=payload.employee_id,
        metric_query_hash=payload.metric_query_hash,
        target_value=payload.target_value,
        current_value=payload.current_value
    )
    return result


@router.get("/employee/{employee_id}", response_model=List[dict])
async def get_employee_okrs(
    employee_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    engine = get_okr_engine(db)
    return engine.get_employee_okrs(employee_id)
