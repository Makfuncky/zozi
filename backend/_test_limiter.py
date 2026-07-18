"""Test that __future__ annotations + limiter work together."""
from __future__ import annotations

from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from db.schemas import UserCreate
from utils.rate_limiter import limiter

router = APIRouter()

@router.post("/register", status_code=201)
@limiter.limit("10/minute")
async def register(request: Request, payload: UserCreate, db: Session = Depends(get_db)):
    return {"ok": True}

print("SUCCESS: __future__ annotations + limiter coexist fine")

