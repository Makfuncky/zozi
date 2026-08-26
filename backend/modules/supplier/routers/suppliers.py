"""Supplier suppliers router — canonical."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status


router = APIRouter(prefix="/api/v1/supplier/suppliers", tags=["supplier", "suppliers"])

