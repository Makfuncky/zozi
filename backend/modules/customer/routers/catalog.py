"""Customer catalog router — consolidated from 1 source files."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status


router = APIRouter(prefix="/api/v1/customer/catalog", tags=["customer", "catalog"])
